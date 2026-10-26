"""P6 — session archives (OQ-7): one pin/digest set, k turns; ctx_mode 0
(reset per turn; assembled on CPU from P5's committed per-row scores) vs
ctx_mode 1 (shared history; scored on GPU in KV chunks).
Protocol: experiments/P6_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from amber.binformat import CTX_RESET, CTX_SHARED, fixed_overhead_bytes, unpack_session
from amber.rac_codec import FLAG_A, FLAG_C, FLAG_X, CoderParams
from amber.real.archive import (build_session_archive, decode_session_archive, encode_symbols,
                                make_hf_scorer_chunked, make_torch_stepper, payload_to_symbols,
                                session_symbol_count, symbols_to_payload)
from amber.real.capture import (Arm, _load_tokenizer, _snapshot_hash, atomic_write_bytes, atomic_write_json,
                                load_model, provenance)
from amber.real.divergence import DRAFT, load_generated

RESULTS = Path(__file__).resolve().parent.parent / "results"
FP32 = Arm("cuda_fp32", "cuda", "fp32", "none", 1)
KS = (2, 4, 8, 16)
DECODE_PLAN = {("m1", 8): None, ("m0", 8): 8}          # mode1 k=8: all sessions; mode0 k=8: first 8


def sdir(out: Path, k: int, mode: int) -> Path:
    return out / f"k{k}_m{mode}"


def groups(rows: list[int], k: int) -> list[list[int]]:
    return [rows[i:i + k] for i in range(0, len(rows) - len(rows) % k, k)]


def p5_symbols(p5dir: Path, row: int, ids: np.ndarray) -> tuple[list[tuple[int, int]], np.ndarray, np.ndarray]:
    with np.load(p5dir / "archives" / f"row_{row:04d}_symbols.npz") as z:
        flag, rank, gap = z["flag"], z["rank"], z["gap"]
    syms = [(int(f), int(rank[j]) if f == FLAG_C else int(ids[j + 1]) if f == FLAG_X else 0)
            for j, f in enumerate(flag)]
    return syms, rank, gap


def seg_bits(syms, p: CoderParams, coder: str) -> int:
    return symbols_to_payload(syms, coder, p)[1]


def turn_accounting(metas, syms, p, coder, ctx_mode) -> list[dict]:
    """Standalone gamma bits per (prompt segment, gen segment) per turn."""
    acc = []; pos = 0
    for i, m in enumerate(metas):
        n_p = m["prompt_len"] - (1 if (ctx_mode == CTX_RESET or i == 0) else 0)
        seg_p = syms[pos:pos + n_p]; seg_g = syms[pos + n_p:pos + n_p + m["gen_len"]]
        acc.append({"prompt_bits": seg_bits(seg_p, p, coder) if seg_p else 0, "prompt_syms": n_p,
                    "gen_bits": seg_bits(seg_g, p, coder), "gen_syms": m["gen_len"],
                    "gen_div": sum(1 for f, _ in seg_g if f != FLAG_A)})
        pos += n_p + m["gen_len"]
    return acc


def encode_stage(a, out: Path, seqs) -> None:
    seqd = {r: (ids, pl) for r, ids, pl in seqs}
    rows = sorted(seqd)
    vocab = 128256
    p = CoderParams(max_rank=a.max_rank, vocab_bits=max(1, (vocab - 1).bit_length()))
    model_desc = {"id": a.draft, "snapshot": _snapshot_hash(a.draft), "dtype": "fp32"}
    p5dir = Path("results/p5")
    if not (p5dir / "ENCODE_DONE").exists():
        raise RuntimeError("P6 mode-0 assembly needs results/p5 (run p5 encode first)")

    model = None; score = None
    for mode in (CTX_RESET, CTX_SHARED):
        for k in KS:
            d = sdir(out, k, mode); d.mkdir(parents=True, exist_ok=True)
            meta_path = d / "meta.json"
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"sessions": {}}
            gs = groups(rows, k)
            todo = [gi for gi in range(len(gs)) if str(gi) not in meta["sessions"]]
            if not todo:
                continue
            if mode == CTX_SHARED and model is None:
                t0 = time.perf_counter(); model = load_model(a.draft, FP32)
                score = make_hf_scorer_chunked(model, "cuda", chunk=a.chunk)
                print(f"[encode] {a.draft} fp32 loaded in {time.perf_counter()-t0:.1f}s")
            for gi in todo:
                g = gs[gi]
                metas = [{"prompt_len": seqd[r][1], "gen_len": len(seqd[r][0]) - seqd[r][1],
                          "first_token": int(seqd[r][0][0])} for r in g]
                all_ids = np.concatenate([seqd[r][0] for r in g])
                if mode == CTX_RESET:
                    syms = []
                    for r in g:
                        s, _, _ = p5_symbols(p5dir, r, seqd[r][0]); syms += s
                else:
                    t1 = time.perf_counter(); sc = score(all_ids); dt = time.perf_counter() - t1
                    syms = encode_symbols(sc["rank"], sc["gap"], sc["topm_idx"], all_ids[1:], p)
                blob = build_session_archive(model_desc, vocab, metas, all_ids, syms, a.coder, p, mode)
                h, payload, pp = unpack_session(blob)
                if payload_to_symbols(payload, h["payload_bits"], h["n_symbols"], h["n_corrections"], a.coder, pp) != syms:
                    raise RuntimeError(f"symbol self-check failed: k{k} m{mode} session {gi}")
                atomic_write_bytes(d / f"sess_{gi:04d}.ambr4", blob)
                meta["sessions"][str(gi)] = {
                    "rows": g, "bytes": len(blob), "payload_bits": h["payload_bits"],
                    "gen_tokens": int(sum(m["gen_len"] for m in metas)),
                    "all_tokens": int(len(all_ids)), "turns": turn_accounting(metas, syms, p, a.coder, mode),
                    **({"score_seconds": dt} if mode == CTX_SHARED else {})}
                atomic_write_json(meta_path, meta)
            meta.update({"draft": a.draft, "model": model_desc, "vocab_size": vocab, "coder": a.coder,
                         "max_rank": a.max_rank, "k": k, "ctx_mode": mode,
                         **({"provenance": provenance(a.draft, FP32)} if mode == CTX_SHARED else {"provenance_note": "assembled from results/p5 scores"})})
            atomic_write_json(meta_path, meta)
            print(f"[encode] k{k} m{mode}: {len(gs)} sessions done")
    (out / "ENCODE_DONE").write_text("{}")


def decode_stage(a, out: Path, seqs) -> None:
    seqd = {r: (ids, pl) for r, ids, pl in seqs}
    t0 = time.perf_counter(); model = load_model(a.draft, FP32)
    print(f"[decode] loaded in {time.perf_counter()-t0:.1f}s")
    factory = make_torch_stepper(model, "cuda", topk=a.topk)
    for (mtag, k), limit in DECODE_PLAN.items():
        mode = CTX_SHARED if mtag == "m1" else CTX_RESET
        d = sdir(out, k, mode)
        meta = json.loads((d / "meta.json").read_text())
        res_path = d / "decode_fp32.json"
        res = json.loads(res_path.read_text()) if res_path.exists() else {"sessions": {}}
        gis = sorted(int(x) for x in meta["sessions"])[:limit]
        for gi in gis:
            if str(gi) in res["sessions"]:
                continue
            g = meta["sessions"][str(gi)]["rows"]
            truth = np.concatenate([seqd[r][0] for r in g])
            blob = (d / f"sess_{gi:04d}.ambr4").read_bytes()
            t1 = time.perf_counter()
            toks, first, _ = decode_session_archive(blob, factory, truth=truth)
            dt = time.perf_counter() - t1
            res["sessions"][str(gi)] = {"first": int(first), "n_decoded": int(len(toks)), "seconds": dt}
            atomic_write_json(res_path, res)
            print(f"[decode k{k} m{mode}] session {gi}: {'EXACT' if first < 0 else f'desync at {first}'} ({len(toks)/dt:.0f} tok/s)")
        res["done"] = True; atomic_write_json(res_path, res)


def report_stage(a, out: Path, seqs) -> None:
    import zstandard
    seqd = {r: (ids, pl) for r, ids, pl in seqs}
    tok = _load_tokenizer(a.draft)
    p5 = json.loads(Path("results/p5/encode_meta.json").read_text())["per_row"]
    z = lambda s: 8 * len(zstandard.ZstdCompressor(level=19).compress(s.encode("utf-8")))  # noqa: E731
    fixed = fixed_overhead_bytes(a.draft, True)
    rep = {"fixed_header_bytes": fixed, "by_k_mode": {}, "per_turn_index_k8": {}, "decode": {}}
    for mode in (CTX_RESET, CTX_SHARED):
        for k in KS:
            d = sdir(out, k, mode)
            if not (d / "meta.json").exists():
                continue
            meta = json.loads((d / "meta.json").read_text()); ss = meta["sessions"]
            n_gen = sum(v["gen_tokens"] for v in ss.values()); n_all = sum(v["all_tokens"] for v in ss.values())
            bits = sum(8 * v["bytes"] for v in ss.values())
            v3_bits = sum(8 * p5[str(r)]["bytes"] for v in ss.values() for r in v["rows"])
            zs = sum(z("".join(tok.decode(seqd[r][0]) for r in v["rows"])) for v in ss.values())
            pb = sum(t["prompt_bits"] for v in ss.values() for t in v["turns"])
            gb = sum(t["gen_bits"] for v in ss.values() for t in v["turns"])
            rep["by_k_mode"][f"k{k}_m{mode}"] = {
                "sessions": len(ss), "gen_tokens": n_gen,
                "bits_per_gen_token": bits / n_gen, "bits_per_all_tokens": bits / n_all,
                "vs_k_separate_v3_files": bits / v3_bits,
                "zstd19_per_session_bits_per_gen_token": zs / n_gen,
                "breakdown_per_gen_token": {"fixed+table": (bits - sum(v["payload_bits"] for v in ss.values())) / n_gen,
                                            "prompt_payload": pb / n_gen, "content_payload": gb / n_gen}}
    for mode in (CTX_RESET, CTX_SHARED):
        d = sdir(out, 8, mode)
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text())
        by_turn = {}
        for v in meta["sessions"].values():
            for ti, t in enumerate(v["turns"]):
                b = by_turn.setdefault(ti, {"prompt_bits": 0, "prompt_syms": 0, "gen_bits": 0, "gen_syms": 0, "gen_div": 0})
                for key in b:
                    b[key] += t[key]
        rep["per_turn_index_k8"][f"m{mode}"] = {
            str(ti): {"prompt_bits_per_token": b["prompt_bits"] / max(1, b["prompt_syms"]),
                      "content_bits_per_token": b["gen_bits"] / b["gen_syms"],
                      "divergence": b["gen_div"] / b["gen_syms"]}
            for ti, b in sorted(by_turn.items())}
    for (mtag, k) in DECODE_PLAN:
        mode = CTX_SHARED if mtag == "m1" else CTX_RESET
        res_path = sdir(out, k, mode) / "decode_fp32.json"
        if res_path.exists():
            res = json.loads(res_path.read_text())["sessions"]
            firsts = [v["first"] for v in res.values()]
            rep["decode"][f"k{k}_m{mode}"] = {"sessions": len(res), "byte_exact": sum(1 for f in firsts if f < 0),
                                              "desync_positions": [f for f in firsts if f >= 0],
                                              "tok_per_s": sum(v["n_decoded"] for v in res.values()) / sum(v["seconds"] for v in res.values())}
    payload = {"_experiment": "p6_sessions", "_written_unix": int(time.time()), "protocol": "experiments/P6_PROTOCOL.md",
               "draft": a.draft, "coder": "gamma", "ks": KS, "report": rep,
               "regime": "P1 turns grouped in row order into k-turn sessions; ctx_mode 0 reset per turn (CPU repack of P5 fp32 scores), ctx_mode 1 shared history (fp32 KV-chunked rescoring); turns were generated INDEPENDENTLY by the target, so shared-context conditioning is biased against amber by construction; one 3080 Ti"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p6_sessions.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(rep, indent=1)[:5000]); print("[saved] results/p6_sessions.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["encode", "decode", "report"])
    ap.add_argument("--p1", default="results/p1"); ap.add_argument("--out", default="results/p6")
    ap.add_argument("--draft", default=DRAFT); ap.add_argument("--coder", default="gamma")
    ap.add_argument("--max-rank", type=int, default=64); ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--topk", type=int, default=128)
    a = ap.parse_args(argv); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    seqs = load_generated(Path(a.p1))
    if a.stage == "encode":
        encode_stage(a, out, seqs)
    elif a.stage == "decode":
        if not (out / "ENCODE_DONE").exists():
            print("encode first", file=sys.stderr); return 1
        decode_stage(a, out, seqs)
    else:
        report_stage(a, out, seqs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

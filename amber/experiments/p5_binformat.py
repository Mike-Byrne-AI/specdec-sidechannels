"""P5 — binary format v3 + prompt coded with the draft (OQ-7).
Protocol: experiments/P5_PROTOCOL.md. Stages: encode (cuda fp32, one
teacher-forced forward per prompt scoring positions 1..L), decode (cuda
fp32, prompt segment decoded not fed), report (sizes itemised, prompt-coding
cost, crossover curve, D-6 baselines per archive)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from amber.binformat import fixed_overhead_bytes, unpack
from amber.rac_codec import FLAG_A, FLAG_C, FLAG_X, CoderParams
from amber.real.archive import (build_binary_archive, decode_binary_archive, encode_symbols, make_hf_scorer,
                                make_torch_stepper, payload_to_symbols, symbols_to_payload)
from amber.real.capture import (Arm, _load_tokenizer, _snapshot_hash, atomic_savez, atomic_write_bytes,
                                atomic_write_json, load_model, provenance)
from amber.real.divergence import DRAFT, load_generated

RESULTS = Path(__file__).resolve().parent.parent / "results"
FP32 = Arm("cuda_fp32", "cuda", "fp32", "none", 1)


def apath(out: Path, row: int) -> Path:
    return out / "archives" / f"row_{row:04d}.ambr3"


def encode_stage(a, out: Path, seqs) -> None:
    (out / "archives").mkdir(parents=True, exist_ok=True)
    meta_path = out / "encode_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    todo = [(r, ids, pl) for r, ids, pl in seqs if not apath(out, r).exists()]
    if not todo:
        print("[encode] all v3 archives present"); return
    t0 = time.perf_counter(); model = load_model(a.draft, FP32)
    print(f"[encode] {a.draft} fp32 loaded in {time.perf_counter()-t0:.1f}s; {len(todo)} archives")
    vocab = int(model.config.vocab_size)
    model_desc = {"id": a.draft, "snapshot": _snapshot_hash(a.draft), "dtype": "fp32"}
    p = CoderParams(max_rank=a.max_rank, vocab_bits=max(1, (vocab - 1).bit_length()))
    score = make_hf_scorer(model, "cuda", topm=2)
    meta.update({"draft": a.draft, "model": model_desc, "vocab_size": vocab, "coder": a.coder,
                 "max_rank": a.max_rank, "provenance": provenance(a.draft, FP32), "per_row": meta.get("per_row", {})})
    t_pos = 0; t_sec = 0.0
    for r, ids, pl in todo:
        t1 = time.perf_counter(); s = score(ids, 1); dt = time.perf_counter() - t1   # score EVERY position after ids[0]
        syms = encode_symbols(s["rank"], s["gap"], s["topm_idx"], ids[1:], p)
        blob = build_binary_archive(model_desc, vocab, ids, pl, syms, a.coder, p)
        h, payload, pp = unpack(blob)
        if payload_to_symbols(payload, h["payload_bits"], len(syms), h["n_corrections"], a.coder, pp) != syms:
            raise RuntimeError(f"symbol self-check failed on row {r}")
        prompt_syms = syms[:pl - 1]
        prompt_bits = symbols_to_payload(prompt_syms, a.coder, p)[1] if pl > 1 else 0
        atomic_savez(out / "archives" / f"row_{r:04d}_symbols.npz", flag=np.array([f for f, _ in syms], np.int8),
                     rank=s["rank"], gap=s["gap"])
        atomic_write_bytes(apath(out, r), blob)
        meta["per_row"][str(r)] = {"bytes": len(blob), "payload_bits": h["payload_bits"],
                                   "prompt_bits_standalone": prompt_bits, "prompt_len": pl,
                                   "length": len(ids) - pl, "n_corrections": h["n_corrections"],
                                   "prompt_ranks": np.asarray(s["rank"][:pl - 1]).tolist(), "score_seconds": dt}
        t_pos += len(ids) - 1; t_sec += dt
        if len(meta["per_row"]) % 40 == 0:
            atomic_write_json(meta_path, meta); print(f"[encode] {len(meta['per_row'])} archives, {t_pos/t_sec:.0f} pos/s")
    atomic_write_json(meta_path, meta); (out / "ENCODE_DONE").write_text("{}")
    print(f"[encode] done: {len(meta['per_row'])} archives")


def decode_stage(a, out: Path, seqs) -> None:
    ddir = out / "decode_cuda_fp32"; ddir.mkdir(exist_ok=True)
    rows = [r for r, _, _ in seqs]
    n_shards = (len(rows) + a.shard_size - 1) // a.shard_size
    pending = [s for s in range(n_shards) if not (ddir / f"shard_{s:04d}.npz").exists()]
    if not pending:
        print("[decode] complete"); (ddir / "DONE").write_text("{}"); return
    t0 = time.perf_counter(); model = load_model(a.draft, FP32)
    print(f"[decode] loaded in {time.perf_counter()-t0:.1f}s; {len(pending)} shards")
    factory = make_torch_stepper(model, "cuda", topk=a.topk)
    truth = {r: ids for r, ids, _ in seqs}
    for s in pending:
        srows = rows[s * a.shard_size:(s + 1) * a.shard_size]; rec = []
        t1 = time.perf_counter(); n_dec = 0
        for r in srows:
            blob = apath(out, r).read_bytes()
            toks, first, _ = decode_binary_archive(blob, factory, truth=truth[r])
            n = len(truth[r]) - 1 if first < 0 else first + 1; n_dec += n
            rec.append((r, first, n))
        dt = time.perf_counter() - t1
        atomic_savez(ddir / f"shard_{s:04d}.npz", row=np.array([x[0] for x in rec]), first=np.array([x[1] for x in rec]),
                     n_decoded=np.array([x[2] for x in rec]), seconds=np.array([dt / len(rec)] * len(rec)))
        print(f"[decode] shard {s+1}/{n_shards}: exact {sum(1 for x in rec if x[1] < 0)}/{len(rec)}, {n_dec/dt:.0f} tok/s")
    (ddir / "DONE").write_text("{}")
    atomic_write_json(ddir / "meta.json", {"arm": FP32.__dict__, "provenance": provenance(a.draft, FP32), "topk": a.topk})


def report_stage(a, out: Path, seqs) -> None:
    import zstandard
    enc = json.loads((out / "encode_meta.json").read_text()); pr = enc["per_row"]
    rows = sorted(int(k) for k in pr)
    tok = _load_tokenizer(enc["draft"]); seqd = {r: (ids, pl) for r, ids, pl in seqs}
    n_gen = sum(pr[str(r)]["length"] for r in rows); n_all = sum(len(seqd[r][0]) for r in rows)
    n_prompt = n_all - n_gen
    total_bits = sum(8 * pr[str(r)]["bytes"] for r in rows)
    payload_bits = sum(pr[str(r)]["payload_bits"] for r in rows)
    prompt_bits = sum(pr[str(r)]["prompt_bits_standalone"] for r in rows)
    fixed = fixed_overhead_bytes(enc["draft"], True)
    v2_bits = None
    v2meta = Path("results/p4/encode_meta.json")
    if v2meta.exists():
        v2 = json.loads(v2meta.read_text())["per_row"]
        v2_bits = sum(8 * v2[str(r)]["bytes"] for r in rows if str(r) in v2)
    z = lambda s: 8 * len(zstandard.ZstdCompressor(level=19).compress(s.encode("utf-8")))  # noqa: E731
    z_per_archive = sum(z(tok.decode(seqd[r][0])) for r in rows)
    z_concat = z("".join(tok.decode(seqd[r][0]) for r in rows))
    pranks = np.concatenate([np.array(pr[str(r)]["prompt_ranks"]) for r in rows])
    # measured components for the crossover curve
    payload_gen_rate = (payload_bits - prompt_bits) / n_gen              # bits per generated token
    per_archive_const = fixed * 8 + prompt_bits / len(rows)              # bits per archive (mean prompt)
    curve = {}
    for L in (64, 128, 245, 512, 1024, 2048, 4096, 8192):
        amber_total = per_archive_const / L + payload_gen_rate
        curve[str(L)] = round(amber_total, 3)
    d = {}
    ddir = out / "decode_cuda_fp32"
    if (ddir / "DONE").exists():
        first, n_dec, secs = [], [], []
        for sp in sorted(ddir.glob("shard_*.npz")):
            with np.load(sp) as zz:
                first += zz["first"].tolist(); n_dec += zz["n_decoded"].tolist(); secs += zz["seconds"].tolist()
        first = np.array(first)
        d = {"archives": len(first), "byte_exact": int((first < 0).sum()),
             "first_desync_positions": first[first >= 0].tolist(),
             "decode_tok_per_s": float(sum(n_dec) / sum(secs))}
    rep = {
        "archives": len(rows), "generated_tokens": n_gen, "prompt_tokens_incl_first": n_prompt,
        "v3_total_bits_per_generated_token": total_bits / n_gen,
        "v3_total_bits_per_all_tokens": total_bits / n_all,
        "v2_json_total_bits_per_generated_token": (v2_bits / n_gen) if v2_bits else None,
        "v3_over_v2_size_ratio": (sum(8 * pr[str(r)]["bytes"] for r in rows) / v2_bits) if v2_bits else None,
        "breakdown_bits_per_generated_token": {
            "fixed_header": len(rows) * fixed * 8 / n_gen,
            "prompt_payload": prompt_bits / n_gen,
            "content_payload": (payload_bits - prompt_bits) / n_gen,
        },
        "fixed_header_bytes": fixed,
        "prompt_coding": {
            "bits_per_prompt_token": prompt_bits / max(1, n_prompt - len(rows)),
            "raw17_bits_per_prompt_token": 17.0,
            "varint_raw_bits_per_prompt_token": float(np.mean([8 * (1 + (int(x) >= 1 << 7) + (int(x) >= 1 << 14) + (int(x) >= 1 << 21))
                                                               for x in np.concatenate([seqd[r][0][1:seqd[r][1]] for r in rows])])),
            "prompt_rank_quantiles": {q: int(np.quantile(pranks, float(q))) for q in ("0.5", "0.9", "0.99")},
            "prompt_rank_gt_max_rank_rate": float((pranks > enc["max_rank"]).mean()),
        },
        "zstd19_full_text_per_archive_bits_per_generated_token": z_per_archive / n_gen,
        "zstd19_full_text_concatenated_bits_per_generated_token": z_concat / n_gen,
        "raw_bits_per_token": 16.97,
        "amber_v3_bits_per_generated_token_vs_L_curve": curve,
        "curve_model": {"per_archive_const_bits": per_archive_const, "payload_gen_rate": payload_gen_rate,
                        "note": "const/L + rate; assumes P1-like divergence and this prompt mix"},
        "decode_cuda_fp32": d,
    }
    payload = {"_experiment": "p5_binformat", "_written_unix": int(time.time()), "protocol": "experiments/P5_PROTOCOL.md",
               "draft": enc["draft"], "model": enc["model"], "coder": enc["coder"], "report": rep,
               "regime": "P1 content re-archived in v3 binary format (prompt coded with the draft from the first token on), Llama-3.2-1B cuda fp32; decode cuda fp32 incremental KV from first token; one 3080 Ti"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p5_binformat.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(rep, indent=1)[:4000]); print("[saved] results/p5_binformat.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["encode", "decode", "report"])
    ap.add_argument("--p1", default="results/p1"); ap.add_argument("--out", default="results/p5")
    ap.add_argument("--draft", default=DRAFT); ap.add_argument("--coder", default="gamma")
    ap.add_argument("--max-rank", type=int, default=64); ap.add_argument("--shard-size", type=int, default=8)
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

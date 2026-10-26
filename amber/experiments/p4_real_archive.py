"""P4 — real archives: encode the P1 content with the 1B draft (cuda fp32,
teacher-forced), decode with the draft alone (incremental KV replay) under
several dtype arms; byte-exactness per archive, first-desync attribution,
rate incl. header, throughput. Resumable per archive / per shard.
Protocol: experiments/P4_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from amber.rac_codec import FLAG_NAMES, CoderParams
from amber.real.archive import (build_archive, decode_archive, encode_symbols, make_hf_scorer, make_torch_stepper,
                                parse_archive, payload_to_symbols)
from amber.real.capture import Arm, _load_tokenizer, _snapshot_hash, atomic_savez, atomic_write_bytes, atomic_write_json, load_model, provenance
from amber.real.divergence import DRAFT, load_generated

RESULTS = Path(__file__).resolve().parent.parent / "results"
ARMS = {"cuda_fp32": Arm("cuda_fp32", "cuda", "fp32", "none", 1), "cuda_bf16": Arm("cuda_bf16", "cuda", "bf16", "none", 1),
        "cuda_fp16": Arm("cuda_fp16", "cuda", "fp16", "none", 1), "cpu_fp32": Arm("cpu_fp32", "cpu", "fp32", "none", 1)}
PREDICTED_FAIL_BAND = {"cuda_fp32": (0.0, 0.01), "cpu_fp32": (0.0, 0.01), "cuda_bf16": (0.5, 0.9), "cuda_fp16": (0.08, 0.35)}


def archive_path(out: Path, row: int) -> Path:
    return out / "archives" / f"row_{row:04d}.ambr"


def encode_stage(a, out: Path, seqs) -> None:
    (out / "archives").mkdir(parents=True, exist_ok=True)
    meta_path = out / "encode_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    todo = [(r, ids, pl) for r, ids, pl in seqs if not archive_path(out, r).exists()]
    if not todo:
        print("[encode] all archives present"); return
    arm = ARMS["cuda_fp32"]; t0 = time.perf_counter(); model = load_model(a.draft, arm)
    print(f"[encode] {a.draft} fp32 loaded in {time.perf_counter()-t0:.1f}s; {len(todo)} archives to write")
    vocab = int(model.config.vocab_size)
    model_desc = {"id": a.draft, "snapshot": _snapshot_hash(a.draft), "dtype": "fp32"}
    p = CoderParams(tie_margin=0.0, tie_topm=2, max_rank=a.max_rank, vocab_bits=max(1, (vocab - 1).bit_length()))
    score = make_hf_scorer(model, "cuda", topm=2)
    meta.update({"draft": a.draft, "model": model_desc, "vocab_size": vocab, "coder": a.coder, "max_rank": a.max_rank,
                 "provenance": provenance(a.draft, arm), "per_row": meta.get("per_row", {})})
    t_pos = 0; t_sec = 0.0
    for r, ids, pl in todo:
        toks = ids[pl:]; t1 = time.perf_counter(); s = score(ids, pl); dt = time.perf_counter() - t1
        syms = encode_symbols(s["rank"], s["gap"], s["topm_idx"], toks, p)
        blob = build_archive(model_desc, vocab, ids[:pl].tolist(), toks, syms, a.coder, p)
        h, payload, pp = parse_archive(blob)
        if payload_to_symbols(payload, h["payload_bits"], h["length"], h["n_corrections"], a.coder, pp) != syms:
            raise RuntimeError(f"symbol self-check failed on row {r}")
        atomic_savez(out / "archives" / f"row_{r:04d}_symbols.npz", flag=np.array([f for f, _ in syms], np.int8),
                     value=np.array([v for _, v in syms], np.int64), rank=s["rank"], gap=s["gap"], tokens=toks)
        atomic_write_bytes(archive_path(out, r), blob)
        meta["per_row"][str(r)] = {"bytes": len(blob), "payload_bits": h["payload_bits"], "length": h["length"],
                                   "n_corrections": h["n_corrections"], "score_seconds": dt}
        t_pos += len(toks); t_sec += dt
        if len(meta["per_row"]) % 20 == 0:
            atomic_write_json(meta_path, meta); print(f"[encode] {len(meta['per_row'])} archives, {t_pos/t_sec:.0f} pos/s")
    meta["encode_pos_per_s"] = t_pos / t_sec if t_sec else None
    atomic_write_json(meta_path, meta); (out / "ENCODE_DONE").write_text("{}")
    print(f"[encode] done: {len(meta['per_row'])} archives, teacher-forced fp32 {t_pos/t_sec:.0f} pos/s")


def decode_stage(a, out: Path, seqs) -> None:
    for arm_name in a.arm:
        arm = ARMS[arm_name]; ddir = out / f"decode_{arm_name}"; ddir.mkdir(exist_ok=True)
        rows = [r for r, _, _ in seqs][:a.n_prompts]
        n_shards = (len(rows) + a.shard_size - 1) // a.shard_size
        pending = [s for s in range(n_shards) if not (ddir / f"shard_{s:04d}.npz").exists()]
        if not pending:
            print(f"[decode {arm_name}] complete"); (ddir / "DONE").write_text("{}"); continue
        t0 = time.perf_counter(); model = load_model(a.draft, arm)
        print(f"[decode {arm_name}] loaded in {time.perf_counter()-t0:.1f}s; {len(pending)} shards to run")
        factory = make_torch_stepper(model, arm.device, topk=a.topk)
        truth = {r: ids[pl:] for r, ids, pl in seqs}
        for s in pending:
            srows = rows[s * a.shard_size:(s + 1) * a.shard_size]; rec = []
            t1 = time.perf_counter(); n_dec = 0
            for r in srows:
                blob = archive_path(out, r).read_bytes(); t2 = time.perf_counter()
                toks, first, _ = decode_archive(blob, factory, truth=truth[r])
                n = len(truth[r]) if first < 0 else first + 1; n_dec += n
                rec.append((r, first, n, time.perf_counter() - t2))
            dt = time.perf_counter() - t1
            atomic_savez(ddir / f"shard_{s:04d}.npz", row=np.array([x[0] for x in rec]), first=np.array([x[1] for x in rec]),
                         n_decoded=np.array([x[2] for x in rec]), seconds=np.array([x[3] for x in rec]))
            print(f"[decode {arm_name}] shard {s+1}/{n_shards}: exact {sum(1 for x in rec if x[1] < 0)}/{len(rec)}, {n_dec/dt:.0f} tok/s")
        (ddir / "DONE").write_text("{}")
        atomic_write_json(ddir / "meta.json", {"arm": arm.__dict__, "provenance": provenance(a.draft, arm), "topk": a.topk})
        del model
        import gc, torch; gc.collect(); torch.cuda.empty_cache()


def report_stage(a, out: Path, seqs) -> None:
    enc = json.loads((out / "encode_meta.json").read_text())
    rows = sorted(int(k) for k in enc["per_row"])
    n_tok = sum(enc["per_row"][str(r)]["length"] for r in rows)
    n_prompt_tok = sum(pl for r, _, pl in seqs if r in set(rows))
    payload_bits = sum(enc["per_row"][str(r)]["payload_bits"] for r in rows)
    total_bits = sum(8 * enc["per_row"][str(r)]["bytes"] for r in rows)
    # Header cost, honestly: the JSON header carries the prompt ids + 4 digests + model pin, and on
    # 245-token archives it dominates. Also a binary-header estimate (4x8 B digests, 16 B model pin,
    # 12 B ints, 2 B/varint prompt id) and zstd-19 on the FULL text (prompt + continuation).
    import zstandard
    tok = _load_tokenizer(enc["draft"]); seqd = {r: (ids, pl) for r, ids, pl in seqs}
    bin_hdr_bits = sum(8 * (60 + 2 * seqd[r][1]) for r in rows)
    full_text = "".join(tok.decode(seqd[r][0]) for r in rows); gen_text = "".join(tok.decode(seqd[r][0][seqd[r][1]:]) for r in rows)
    z = lambda s: 8 * len(zstandard.ZstdCompressor(level=19).compress(s.encode("utf-8")))  # noqa: E731
    z_per_archive = sum(z(tok.decode(seqd[r][0])) for r in rows)
    rep = {"archives": len(rows), "content_tokens": n_tok, "prompt_tokens": n_prompt_tok, "prompt_tokens_mean": n_prompt_tok / len(rows),
           "payload_bits_per_token": payload_bits / n_tok, "total_archive_bits_per_token_incl_header": total_bits / n_tok,
           "header_bytes_mean": (total_bits - payload_bits) / 8 / len(rows),
           "binary_header_estimate_bits_per_token": (payload_bits + bin_hdr_bits) / n_tok,
           "zstd19_generated_text_bits_per_token": z(gen_text) / n_tok,
           "zstd19_full_text_concatenated_bits_per_generated_token": z(full_text) / n_tok,
           "zstd19_full_text_per_archive_bits_per_generated_token": z_per_archive / n_tok,
           "encode_teacher_forced_fp32_pos_per_s": enc.get("encode_pos_per_s"), "arms": {}}
    for arm_name in ARMS:
        ddir = out / f"decode_{arm_name}"
        if not (ddir / "DONE").exists():
            continue
        first, n_dec, secs, rws = [], [], [], []
        for sp in sorted(ddir.glob("shard_*.npz")):
            with np.load(sp) as z:
                first += z["first"].tolist(); n_dec += z["n_decoded"].tolist(); secs += z["seconds"].tolist(); rws += z["row"].tolist()
        first = np.array(first); fails = first >= 0
        cls = {}
        for r, f in zip(rws, first):
            if f < 0:
                continue
            with np.load(out / "archives" / f"row_{r:04d}_symbols.npz") as z:
                fl = int(z["flag"][f]); rk = int(z["rank"][f]); gp = float(z["gap"][f])
            key = FLAG_NAMES[fl] if fl != 1 else f"C{rk}"
            cls.setdefault(key, []).append({"row": int(r), "pos": int(f), "gap": gp})
        n_arm_tok = sum(enc["per_row"][str(r)]["length"] for r in rws)
        fail_rate = float(fails.mean()) if len(first) else None
        band = PREDICTED_FAIL_BAND.get(arm_name)
        rep["arms"][arm_name] = {
            "archives": len(first), "byte_exact": int((~fails).sum()), "fail_rate": fail_rate,
            "predicted_fail_band": band, "in_band": (band[0] <= fail_rate <= band[1]) if (band and fail_rate is not None) else None,
            "first_desync_pos": {"p10": float(np.quantile(first[fails], .1)), "p50": float(np.median(first[fails])), "p90": float(np.quantile(first[fails], .9))} if fails.any() else None,
            "tokens_before_first_desync_mean": float(np.mean(np.where(fails, first, [enc["per_row"][str(r)]["length"] for r in rws]))),
            "desyncs_per_token": float(fails.sum() / sum(n_dec)) if sum(n_dec) else None,
            "first_desync_class_counts": {k: len(v) for k, v in cls.items()},
            "first_desync_examples": {k: v[:5] for k, v in cls.items()},
            "wide_gap_A_desyncs_gt_1e-3": sum(1 for x in cls.get("A", []) if x["gap"] > 1e-3),
            "decode_tok_per_s": float(sum(n_dec) / sum(secs)) if sum(secs) else None, "content_tokens": n_arm_tok}
    payload = {"_experiment": "p4_real_archive", "_written_unix": int(time.time()), "protocol": "experiments/P4_PROTOCOL.md",
               "draft": enc["draft"], "model": enc["model"], "coder": enc["coder"], "max_rank": enc["max_rank"],
               "encoder_provenance": enc.get("provenance"), "report": rep,
               "regime": "P1 content (Llama-3.2-3B greedy, 200 prompts) archived with Llama-3.2-1B base cuda fp32 teacher-forced; decoded draft-only, incremental KV, batch 1, per arm; one 3080 Ti"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p4_real_archive.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(rep, indent=1, default=str)[:6000]); print("[saved] results/p4_real_archive.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["encode", "decode", "report"])
    ap.add_argument("--p1", default="results/p1"); ap.add_argument("--out", default="results/p4")
    ap.add_argument("--draft", default=DRAFT); ap.add_argument("--coder", default="gamma"); ap.add_argument("--max-rank", type=int, default=64)
    ap.add_argument("--arm", action="append", default=[]); ap.add_argument("--n-prompts", type=int, default=10**9)
    ap.add_argument("--shard-size", type=int, default=8); ap.add_argument("--topk", type=int, default=128)
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

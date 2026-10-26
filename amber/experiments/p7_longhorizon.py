"""P7 — long-horizon archives + TRUE multi-turn sessions (P7_PROTOCOL.md).

generate  target bf16 greedy: Part A rows 0-31 at caps 2048/4096/8192
          (row-atomic); Part B rows 0-95 as 12 8-turn sessions, each turn
          generated WITH full session history (session-atomic)
encode    draft cuda fp32 (D-8): Part A v3 archives (chunked scorer, +log2q
          for the AC-under-draft baseline); Part B v4 sessions in BOTH ctx
          modes from the same content
decode    draft-only cuda fp32 incremental KV: 32 archives + 12x2 sessions;
          a desync halts that part (bug first, per protocol)
report    rate-vs-L with D-6 baselines and repetition diagnostics; the
          pre-registered m1/m0 sign test on true multi-turn content
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from amber.binformat import CTX_RESET, CTX_SHARED, fixed_overhead_bytes, unpack, unpack_session
from amber.rac_codec import FLAG_A, FLAG_C, FLAG_X, CoderParams
from amber.real.archive import (build_binary_archive, build_session_archive, decode_binary_archive,
                                decode_session_archive, encode_symbols, make_hf_scorer_chunked,
                                make_torch_stepper, payload_to_symbols, symbols_to_payload)
from amber.real.capture import (Arm, _load_tokenizer, _snapshot_hash, atomic_savez, atomic_write_bytes,
                                atomic_write_json, load_model, provenance)
from amber.real.divergence import DRAFT, PROMPTS, TARGET, load_prompts, make_generator
from amber.real.longhorizon import build_multiturn, distinct_ngram_ratio, loop_fraction

RESULTS = Path(__file__).resolve().parent.parent / "results"
FP32 = Arm("cuda_fp32", "cuda", "fp32", "none", 1)
GROUPS_A = {"L2048": (list(range(0, 16)), 2048),
            "L4096": (list(range(16, 28)), 4096),
            "L8192": (list(range(28, 32)), 8192)}
K_MT, N_SESS, N_ROWS = 8, 12, 96
RATE_LAW = (917.0, 0.455)          # F-12: bits/archive, bits/gen-token
BANDS = {"A1": {"L2048": (0.08, 0.35), "L4096": (0.05, 0.32), "L8192": (0.03, 0.30)},
         "A2": (0.35, 1.00), "A3": (0.01, 0.25),
         "B1": (0.40, 0.95), "B2": (1.3, 6.0), "B3": (0.6, 1.6), "B4": (0.6, 1.0), "B5": (0.55, 0.98)}


# ----------------------------------------------------------------------------
# loaders
# ----------------------------------------------------------------------------

def load_single(out: Path) -> list[tuple[int, np.ndarray, int, int, str]]:
    gdir = out / "gen_single"; res = []
    for name, (rows, cap) in GROUPS_A.items():
        for r in rows:
            f = gdir / f"row_{r:04d}.npz"
            if not f.exists():
                continue
            with np.load(f) as z:
                ids = z["ids"].astype(np.int64); pl = int(z["prompt_len"][0])
            res.append((r, ids, pl, cap, name))
    return res


def load_mt(out: Path) -> list[tuple[int, np.ndarray, list[dict], list[int]]]:
    mdir = out / "gen_mt"; res = []
    for s in range(N_SESS):
        f = mdir / f"sess_{s:02d}.npz"
        if not f.exists():
            continue
        with np.load(f) as z:
            all_ids = z["all_ids"].astype(np.int64)
            pls, gls, rows = z["prompt_len"].tolist(), z["gen_len"].tolist(), z["rows"].tolist()
        metas, pos = [], 0
        for pl, gl in zip(pls, gls):
            metas.append({"prompt_len": int(pl), "gen_len": int(gl), "first_token": int(all_ids[pos])})
            pos += pl + gl
        res.append((s, all_ids, metas, rows))
    return res


def turn_accounting(metas, syms, p: CoderParams, coder: str, ctx_mode: int) -> list[dict]:
    """Standalone bits per (prompt, gen) segment per turn — copied from
    experiments/p6_sessions.py (same repo) so P7 stands alone."""
    acc = []; pos = 0
    for i, m in enumerate(metas):
        n_p = m["prompt_len"] - (1 if (ctx_mode == CTX_RESET or i == 0) else 0)
        seg_p = syms[pos:pos + n_p]; seg_g = syms[pos + n_p:pos + n_p + m["gen_len"]]
        acc.append({"prompt_bits": symbols_to_payload(seg_p, coder, p)[1] if seg_p else 0, "prompt_syms": n_p,
                    "gen_bits": symbols_to_payload(seg_g, coder, p)[1], "gen_syms": m["gen_len"],
                    "gen_div": sum(1 for f, _ in seg_g if f != FLAG_A)})
        pos += n_p + m["gen_len"]
    return acc


# ----------------------------------------------------------------------------
# stages
# ----------------------------------------------------------------------------

def generate_stage(a, out: Path) -> None:
    prompts = load_prompts(Path(a.prompts), N_ROWS)
    atomic_write_json(out / "prompts.json", {"source": str(a.prompts), "n": N_ROWS,
                      "sha256": hashlib.sha256(json.dumps(prompts, sort_keys=True).encode()).hexdigest()})
    gdir = out / "gen_single"; mdir = out / "gen_mt"
    gdir.mkdir(parents=True, exist_ok=True); mdir.mkdir(parents=True, exist_ok=True)
    todo_a = [(name, r, cap) for name, (rows, cap) in GROUPS_A.items() for r in rows
              if not (gdir / f"row_{r:04d}.npz").exists()]
    todo_b = [s for s in range(N_SESS) if not (mdir / f"sess_{s:02d}.npz").exists()]
    if not todo_a and not todo_b:
        (out / "GEN_DONE").write_text("{}"); print("[generate] complete"); return
    tok = _load_tokenizer(a.target); bos = tok.bos_token_id
    enc_bos = lambda s2: [bos] + tok(s2, add_special_tokens=False)["input_ids"]  # noqa: E731
    enc_raw = lambda s2: tok(s2, add_special_tokens=False)["input_ids"]          # noqa: E731
    arm = Arm("gen", "cuda", a.gen_dtype, "none", 1)
    t0 = time.perf_counter(); model = load_model(a.target, arm)
    print(f"[generate] {a.target} {a.gen_dtype} loaded in {time.perf_counter() - t0:.1f}s; "
          f"{len(todo_a)} long rows + {len(todo_b)} sessions to go")
    caps = {cap for _, _, cap in todo_a} | {a.mt_max_new}
    gens = {cap: make_generator(model, tok, "cuda", cap) for cap in caps}
    for name, r, cap in todo_a:
        t1 = time.perf_counter()
        p_ids = enc_bos(prompts[r]["prompt"]); g_ids = gens[cap](p_ids)
        dt = time.perf_counter() - t1
        atomic_savez(gdir / f"row_{r:04d}.npz", ids=np.asarray(p_ids + g_ids, np.int32),
                     prompt_len=np.asarray([len(p_ids)], np.int32))
        print(f"[generate A {name}] row {r}: {len(g_ids)} tokens {dt:.0f}s ({len(g_ids) / dt:.1f} tok/s)"
              + ("" if len(g_ids) >= cap else " [EOS before cap]"))
    for s in todo_b:
        rows = list(range(s * K_MT, (s + 1) * K_MT))
        tp = [enc_bos(prompts[rows[0]]["prompt"])] + [enc_raw(prompts[r]["prompt"]) for r in rows[1:]]
        t1 = time.perf_counter()
        all_ids, metas_t = build_multiturn(tp, gens[a.mt_max_new])
        dt = time.perf_counter() - t1
        atomic_savez(mdir / f"sess_{s:02d}.npz", all_ids=all_ids.astype(np.int32),
                     prompt_len=np.asarray([m["prompt_len"] for m in metas_t], np.int32),
                     gen_len=np.asarray([m["gen_len"] for m in metas_t], np.int32),
                     rows=np.asarray(rows, np.int32))
        n_new = int(sum(m["gen_len"] for m in metas_t))
        print(f"[generate B] session {s}: {n_new} new tokens / {K_MT} turns {dt:.0f}s")
    atomic_write_json(out / "generate_meta.json", {
        "target": a.target, "dtype": a.gen_dtype,
        "groups": {k: {"rows": v[0], "max_new": v[1]} for k, v in GROUPS_A.items()},
        "mt": {"k": K_MT, "sessions": N_SESS, "max_new": a.mt_max_new},
        "provenance": provenance(a.target, arm)})
    (out / "GEN_DONE").write_text("{}")
    print("[generate] done")


def encode_stage(a, out: Path) -> None:
    if not (out / "GEN_DONE").exists():
        print("generate first", file=sys.stderr); raise SystemExit(1)
    singles = load_single(out); sessions = load_mt(out)
    adir = out / "archives"; adir.mkdir(exist_ok=True)
    meta_path = out / "encode_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.setdefault("per_row", {}); meta.setdefault("per_session", {})
    todo_a = [x for x in singles if str(x[0]) not in meta["per_row"]]
    todo_b = [x for x in sessions if str(x[0]) not in meta["per_session"]]
    if not todo_a and not todo_b:
        (out / "ENCODE_DONE").write_text("{}"); print("[encode] complete"); return
    t0 = time.perf_counter(); model = load_model(a.draft, FP32)
    print(f"[encode] {a.draft} fp32 loaded in {time.perf_counter() - t0:.1f}s; "
          f"{len(todo_a)} rows + {len(todo_b)} sessions")
    score = make_hf_scorer_chunked(model, "cuda", chunk=a.chunk, logq=True)
    vocab = int(model.config.vocab_size)
    p = CoderParams(max_rank=a.max_rank, vocab_bits=max(1, (vocab - 1).bit_length()))
    model_desc = {"id": a.draft, "snapshot": _snapshot_hash(a.draft), "dtype": "fp32"}
    meta.update({"draft": a.draft, "model": model_desc, "vocab_size": vocab, "coder": a.coder,
                 "max_rank": a.max_rank, "provenance": provenance(a.draft, FP32)})
    for r, ids, pl, cap, group in todo_a:
        t1 = time.perf_counter(); sc = score(ids); dt = time.perf_counter() - t1
        syms = encode_symbols(sc["rank"], sc["gap"], sc["topm_idx"], ids[1:], p)
        blob = build_binary_archive(model_desc, vocab, ids, pl, syms, a.coder, p)
        h, payload, pp = unpack(blob)
        if payload_to_symbols(payload, h["payload_bits"], len(syms), h["n_corrections"], a.coder, pp) != syms:
            raise RuntimeError(f"symbol self-check failed on row {r}")
        prompt_bits = symbols_to_payload(syms[:pl - 1], a.coder, p)[1] if pl > 1 else 0
        atomic_savez(adir / f"row_{r:04d}_symbols.npz", flag=np.array([f for f, _ in syms], np.int8),
                     rank=sc["rank"].astype(np.int32), gap=sc["gap"], log2q=sc["log2q"])
        atomic_write_bytes(adir / f"row_{r:04d}.ambr3", blob)
        meta["per_row"][str(r)] = {"group": group, "bytes": len(blob), "payload_bits": h["payload_bits"],
                                   "prompt_bits_standalone": prompt_bits, "prompt_len": int(pl),
                                   "length": int(len(ids) - pl), "n_corrections": h["n_corrections"],
                                   "ac_bits_gen": float(-sc["log2q"][pl - 1:].sum()), "score_seconds": dt}
        atomic_write_json(meta_path, meta)
        print(f"[encode A] row {r} ({group}): {len(ids) - pl} gen tokens, {len(blob)} B, "
              f"{(len(ids) - 1) / dt:.0f} pos/s")
    for s, all_ids, metas_t, rows in todo_b:
        t1 = time.perf_counter()
        sc1 = score(all_ids)
        syms1 = encode_symbols(sc1["rank"], sc1["gap"], sc1["topm_idx"], all_ids[1:], p)
        syms0: list[tuple[int, int]] = []; ac0 = 0.0; pos = 0
        for m in metas_t:
            n_here = m["prompt_len"] + m["gen_len"]; tids = all_ids[pos:pos + n_here]
            sct = score(tids)
            syms0 += encode_symbols(sct["rank"], sct["gap"], sct["topm_idx"], tids[1:], p)
            ac0 += float(-sct["log2q"][m["prompt_len"] - 1:].sum())
            pos += n_here
        ac1 = 0.0; pos = 0
        for m in metas_t:
            ac1 += float(-sc1["log2q"][pos + m["prompt_len"] - 1: pos + m["prompt_len"] + m["gen_len"] - 1].sum())
            pos += m["prompt_len"] + m["gen_len"]
        blobs = {}
        for mode, syms in ((CTX_SHARED, syms1), (CTX_RESET, syms0)):
            blob = build_session_archive(model_desc, vocab, metas_t, all_ids, syms, a.coder, p, mode)
            h, payload, pp = unpack_session(blob)
            if payload_to_symbols(payload, h["payload_bits"], h["n_symbols"], h["n_corrections"], a.coder, pp) != syms:
                raise RuntimeError(f"symbol self-check failed on session {s} mode {mode}")
            atomic_write_bytes(adir / f"sess_{s:02d}_m{mode}.ambr4", blob)
            blobs[mode] = (len(blob), h["payload_bits"])
        meta["per_session"][str(s)] = {
            "rows": rows, "gen_tokens": int(sum(m["gen_len"] for m in metas_t)),
            "all_tokens": int(len(all_ids)),
            "bytes_m0": blobs[CTX_RESET][0], "bytes_m1": blobs[CTX_SHARED][0],
            "payload_bits_m0": blobs[CTX_RESET][1], "payload_bits_m1": blobs[CTX_SHARED][1],
            "turns_m0": turn_accounting(metas_t, syms0, p, a.coder, CTX_RESET),
            "turns_m1": turn_accounting(metas_t, syms1, p, a.coder, CTX_SHARED),
            "ac_bits_gen_m0": ac0, "ac_bits_gen_m1": ac1,
            "score_seconds": time.perf_counter() - t1}
        atomic_write_json(meta_path, meta)
        print(f"[encode B] session {s}: m0 {blobs[CTX_RESET][0]} B / m1 {blobs[CTX_SHARED][0]} B")
    (out / "ENCODE_DONE").write_text("{}")
    print("[encode] done")


def decode_stage(a, out: Path) -> None:
    if not (out / "ENCODE_DONE").exists():
        print("encode first", file=sys.stderr); raise SystemExit(1)
    singles = load_single(out); sessions = load_mt(out)
    res_path = out / "decode_fp32.json"
    res = json.loads(res_path.read_text()) if res_path.exists() else {"rows": {}, "sessions": {}}
    todo_a = [x for x in singles if str(x[0]) not in res["rows"]]
    todo_b = [(s, all_ids, m) for s, all_ids, _, _ in sessions for m in (1, 0)
              if f"{s}_m{m}" not in res["sessions"]]
    if not todo_a and not todo_b:
        res["done"] = True; atomic_write_json(res_path, res); print("[decode] complete"); return
    t0 = time.perf_counter(); model = load_model(a.draft, FP32)
    print(f"[decode] {a.draft} fp32 loaded in {time.perf_counter() - t0:.1f}s")
    factory = make_torch_stepper(model, "cuda", topk=a.topk)
    for r, ids, pl, cap, group in singles:
        if str(r) in res["rows"]:
            continue
        blob = (out / "archives" / f"row_{r:04d}.ambr3").read_bytes()
        t1 = time.perf_counter()
        toks, first, _ = decode_binary_archive(blob, factory, truth=ids)
        dt = time.perf_counter() - t1
        res["rows"][str(r)] = {"first": int(first), "n": int(len(toks)), "seconds": dt}
        atomic_write_json(res_path, res)
        exact = "EXACT" if first < 0 else f"DESYNC at {first}"
        print(f"[decode A] row {r} ({group}): {exact} ({len(toks) / dt:.0f} tok/s)")
        if first >= 0:
            print("[decode A] HALTED on desync (bug first, per protocol A4)"); break
    for s, all_ids, m in todo_b:
        key = f"{s}_m{m}"
        if key in res["sessions"]:
            continue
        blob = (out / "archives" / f"sess_{s:02d}_m{m}.ambr4").read_bytes()
        t1 = time.perf_counter()
        toks, first, _ = decode_session_archive(blob, factory, truth=all_ids)
        dt = time.perf_counter() - t1
        res["sessions"][key] = {"first": int(first), "n": int(len(toks)), "seconds": dt}
        atomic_write_json(res_path, res)
        exact = "EXACT" if first < 0 else f"DESYNC at {first}"
        print(f"[decode B] sess {s} m{m}: {exact} ({len(toks) / dt:.0f} tok/s)")
        if first >= 0:
            print("[decode B] HALTED on desync (bug first, per protocol B6)"); break
    if len(res["rows"]) == len(singles) and len(res["sessions"]) == 2 * len(sessions):
        res["done"] = True; atomic_write_json(res_path, res)


def report_stage(a, out: Path) -> None:
    import zstandard
    meta = json.loads((out / "encode_meta.json").read_text())
    tok = _load_tokenizer(meta["draft"])
    V = meta["vocab_size"]; coder = meta["coder"]
    p = CoderParams(max_rank=meta["max_rank"], vocab_bits=max(1, (V - 1).bit_length()))
    z = lambda b: 8 * len(zstandard.ZstdCompressor(level=19).compress(b))  # noqa: E731
    singles = {r: (ids, pl) for r, ids, pl, cap, g in load_single(out)}

    partA = {}
    for gname, (rows, cap) in GROUPS_A.items():
        rs = [r for r in rows if str(r) in meta["per_row"]]
        if not rs:
            continue
        pr = [meta["per_row"][str(r)] for r in rs]
        gen_toks = sum(x["length"] for x in pr)
        total_bits = sum(8 * x["bytes"] for x in pr)
        prompt_bits = sum(x["prompt_bits_standalone"] for x in pr)
        payload_bits = sum(x["payload_bits"] for x in pr)
        content_rate = (payload_bits - prompt_bits) / gen_toks
        texts = [tok.decode(singles[r][0].tolist()) for r in rs]
        reps, bucket = [], {}
        for r in rs:
            ids, pl = singles[r]; gen_ids = ids[pl:]
            frac, per = loop_fraction(gen_ids)
            reps.append({"row": r, "gen_len": int(len(gen_ids)), "hit_cap": bool(len(gen_ids) >= cap),
                         "loop_fraction": round(frac, 4), "loop_period": per,
                         "distinct4": round(distinct_ngram_ratio(gen_ids), 4)})
            with np.load(out / "archives" / f"row_{r:04d}_symbols.npz") as zz:
                flag, rank = zz["flag"], zz["rank"]
            syms = [(int(f), int(rank[j]) if f == FLAG_C else int(ids[j + 1]) if f == FLAG_X else 0)
                    for j, f in enumerate(flag)]
            gsyms = syms[pl - 1:]; granks = rank[pl - 1:]
            for b0 in range(0, len(gsyms), 1024):
                bb = bucket.setdefault(b0, {"n": 0, "div": 0, "bits": 0})
                seg = gsyms[b0:b0 + 1024]
                bb["n"] += len(seg)
                bb["div"] += int((granks[b0:b0 + 1024] != 1).sum())
                bb["bits"] += symbols_to_payload(seg, coder, p)[1]
        mean_l = gen_toks / len(rs)
        law = RATE_LAW[0] / mean_l + RATE_LAW[1]
        total_rate = total_bits / gen_toks
        lo, hi = BANDS["A1"][gname]
        med_loop = float(np.median([x["loop_fraction"] for x in reps]))
        row = {
            "archives": len(rs), "cap": cap, "gen_tokens": gen_toks, "mean_realized_len": round(mean_l, 1),
            "hit_cap": sum(1 for x in reps if x["hit_cap"]),
            "bits_per_gen_token": round(total_rate, 4),
            "breakdown_per_gen_token": {"fixed+frame": round((total_bits - payload_bits) / gen_toks, 4),
                                        "prompt_payload": round(prompt_bits / gen_toks, 4),
                                        "content_payload": round(content_rate, 4)},
            "A1": {"band": [lo, hi], "value": round(content_rate, 4), "in_band": lo <= content_rate <= hi},
            "A2": {"band": list(BANDS["A2"]), "law_prediction": round(law, 4),
                   "value": round(total_rate / law, 4),
                   "in_band": BANDS["A2"][0] <= total_rate / law <= BANDS["A2"][1]},
            "ac_under_draft_bits_per_gen_token": round(sum(x["ac_bits_gen"] for x in pr) / gen_toks, 4),
            "zstd19_per_archive_bits_per_gen_token": round(sum(z(t.encode("utf-8")) for t in texts) / gen_toks, 4),
            "zstd19_concat_bits_per_gen_token": round(z("".join(texts).encode("utf-8")) / gen_toks, 4),
            "raw_bits_per_token": round(math.log2(V), 2),
            "by_1024_bucket_standalone": {
                str(b0): {"tokens": bb["n"], "divergence": round(bb["div"] / bb["n"], 4),
                          "content_bits_per_token": round(bb["bits"] / bb["n"], 4)}
                for b0, bb in sorted(bucket.items())},
            "repetition": reps, "median_loop_fraction": med_loop, "A5_degenerate": med_loop > 0.5,
        }
        deep = [(bb["bits"], bb["n"]) for b0, bb in bucket.items() if b0 >= 1024]
        if deep:
            dv = sum(b for b, _ in deep) / sum(n for _, n in deep)
            row["A3"] = {"band": list(BANDS["A3"]), "value": round(dv, 4),
                         "in_band": BANDS["A3"][0] <= dv <= BANDS["A3"][1]}
        ok_rows = [x["row"] for x in reps if x["loop_fraction"] < 0.3]
        if ok_rows:
            ab = sum(8 * meta["per_row"][str(r)]["bytes"] for r in ok_rows)
            zb = sum(z(tok.decode(singles[r][0].tolist()).encode("utf-8")) for r in ok_rows)
            row["A6_nondegenerate_amber_over_zstd"] = round(ab / zb, 4)
        partA[gname] = row
    vals = [partA[g]["A1"]["value"] for g in ("L2048", "L4096", "L8192") if g in partA]
    a1_monotone = all(vals[i + 1] <= vals[i] + 0.02 for i in range(len(vals) - 1)) if len(vals) > 1 else None

    ps = meta.get("per_session", {})
    partB = {}
    if ps:
        def agg(mtag):
            by = {}
            for v in ps.values():
                for ti, t in enumerate(v[f"turns_m{mtag}"]):
                    b = by.setdefault(ti, {"prompt_bits": 0, "prompt_syms": 0, "gen_bits": 0,
                                           "gen_syms": 0, "gen_div": 0})
                    for key in b:
                        b[key] += t[key]
            return by

        def crate(by, ts):
            return sum(by[t]["gen_bits"] for t in ts) / sum(by[t]["gen_syms"] for t in ts)

        def drate(by, t):
            return by[t]["gen_div"] / by[t]["gen_syms"]

        def band(k, v):
            lo, hi = BANDS[k]
            return {"band": [lo, hi], "value": round(v, 4), "in_band": lo <= v <= hi}

        def tbl(by):
            return {str(ti): {"prompt_bits_per_token": round(bb["prompt_bits"] / max(1, bb["prompt_syms"]), 3),
                              "content_bits_per_token": round(bb["gen_bits"] / bb["gen_syms"], 4),
                              "divergence": round(bb["gen_div"] / bb["gen_syms"], 4)}
                    for ti, bb in sorted(by.items())}

        b0, b1 = agg(0), agg(1)
        later = list(range(1, K_MT))
        gen_tokens = sum(v["gen_tokens"] for v in ps.values())
        mts = {s: all_ids for s, all_ids, _, _ in load_mt(out)}
        ztot = sum(z(tok.decode(mts[int(s)].tolist()).encode("utf-8")) for s in ps)
        bits0 = sum(8 * v["bytes_m0"] for v in ps.values())
        bits1 = sum(8 * v["bytes_m1"] for v in ps.values())
        r1 = crate(b1, later) / crate(b0, later)
        pr1 = (sum(b1[t]["prompt_bits"] for t in later) / sum(b1[t]["prompt_syms"] for t in later)) / \
              (b1[0]["prompt_bits"] / b1[0]["prompt_syms"])
        partB = {
            "sessions": len(ps), "gen_tokens": gen_tokens,
            "bits_per_gen_token": {"m0": round(bits0 / gen_tokens, 4), "m1": round(bits1 / gen_tokens, 4)},
            "ac_under_draft_bits_per_gen_token": {
                "m0": round(sum(v["ac_bits_gen_m0"] for v in ps.values()) / gen_tokens, 4),
                "m1": round(sum(v["ac_bits_gen_m1"] for v in ps.values()) / gen_tokens, 4)},
            "zstd19_per_session_bits_per_gen_token": round(ztot / gen_tokens, 4),
            "raw_bits_per_token": round(math.log2(V), 2),
            "per_turn_index": {"m0": tbl(b0), "m1": tbl(b1)},
            "B1_sign_test_content_m1_over_m0_turns2plus": band("B1", r1),
            "B2_m0_div_turn8_over_turn1": band("B2", drate(b0, K_MT - 1) / max(1e-9, drate(b0, 0))),
            "B3_m1_div_turn8_over_turn1": band("B3", drate(b1, K_MT - 1) / max(1e-9, drate(b1, 0))),
            "B4_m1_prompt_turns2plus_over_turn1": band("B4", pr1),
            "B5_total_m1_over_m0": band("B5", bits1 / bits0),
            "falsifies_F13_caveat_hypothesis": bool(r1 >= 1.0),
        }

    dec = {}
    dpath = out / "decode_fp32.json"
    if dpath.exists():
        d = json.loads(dpath.read_text())
        if d["rows"]:
            fa = [v["first"] for v in d["rows"].values()]
            dec["partA"] = {"archives": len(fa), "byte_exact": sum(1 for f in fa if f < 0),
                            "desyncs": [f for f in fa if f >= 0],
                            "tok_per_s": round(sum(v["n"] for v in d["rows"].values())
                                               / max(1e-9, sum(v["seconds"] for v in d["rows"].values())), 1)}
        for m in (0, 1):
            fs = [v["first"] for k2, v in d["sessions"].items() if k2.endswith(f"m{m}")]
            if fs:
                dec[f"partB_m{m}"] = {"sessions": len(fs), "byte_exact": sum(1 for f in fs if f < 0),
                                      "desyncs": [f for f in fs if f >= 0]}

    gm = json.loads((out / "generate_meta.json").read_text()) if (out / "generate_meta.json").exists() else {}
    payload = {"_experiment": "p7_longhorizon", "_written_unix": int(time.time()),
               "protocol": "experiments/P7_PROTOCOL.md",
               "target": gm.get("target"), "draft": meta["draft"], "coder": coder,
               "fixed_header_bytes": fixed_overhead_bytes(meta["draft"], True),
               "partA": partA, "A1_monotone_nonincreasing": a1_monotone,
               "partB": partB, "decode": dec,
               "regime": "Part A: rows 0-31 of sideband prompts, target Llama-3.2-3B base greedy bf16 at caps "
                         "2048/4096/8192, v3 archives encoded and decoded at cuda fp32 (D-8), gamma R=64, one "
                         "3080 Ti; Part B: rows 0-95 as 12 8-turn sessions generated WITH full session history "
                         "(true multi-turn), the same content coded in ctx modes 0 and 1; bands frozen in "
                         "P7_PROTOCOL.md before generation; per-bucket and per-turn bits are standalone-coded "
                         "accounting"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p7_longhorizon.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    brief = {"partA": {g: {k2: partA[g][k2] for k2 in ("bits_per_gen_token", "A1", "A2",
                                                       "median_loop_fraction") if k2 in partA[g]}
                       for g in partA},
             "A1_monotone": a1_monotone,
             "partB_B1": partB.get("B1_sign_test_content_m1_over_m0_turns2plus"),
             "partB_totals": partB.get("bits_per_gen_token"), "decode": dec}
    print(json.dumps(brief, indent=1))
    print("[saved] results/p7_longhorizon.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["generate", "encode", "decode", "report"])
    ap.add_argument("--out", default="results/p7")
    ap.add_argument("--target", default=TARGET); ap.add_argument("--draft", default=DRAFT)
    ap.add_argument("--prompts", default=str(PROMPTS))
    ap.add_argument("--gen-dtype", default="bf16", choices=["bf16", "fp16", "fp32"])
    ap.add_argument("--mt-max-new", type=int, default=256)
    ap.add_argument("--coder", default="gamma"); ap.add_argument("--max-rank", type=int, default=64)
    ap.add_argument("--chunk", type=int, default=512); ap.add_argument("--topk", type=int, default=128)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    {"generate": generate_stage, "encode": encode_stage,
     "decode": decode_stage, "report": report_stage}[a.stage](a, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

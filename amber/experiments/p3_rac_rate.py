"""P3 — coder upgrade and tie-escape price on the P1 stream (experiments/P3_PROTOCOL.md).

Reads results/p1 (draft ranks / log2q / gap per target-generated position and
the generated ids). Tuning set = prompt rows 0-99 (hyperparameters chosen
here only); held-out = rows 100-199 (every reported rate). Two stream modes:
`per_prompt` (independent archive per prompt; real byte counts incl. flush)
and `concatenated` (coder state persists; long-archive limit).

Variants: gamma (v0, exact bits), rac1 (theta=0), rac1 tie escapes at theta
in {0.142, 0.465, 0.93} x m in {2, 4}, and the research-only value-context
variant rac1_qctx (gain measured, not adopted — see protocol). D-6 baselines
on the same split. Symbol-level roundtrip is asserted for every variant.
"""

from __future__ import annotations

import argparse
import itertools
import json
import lzma
import time
import zlib
from pathlib import Path

import numpy as np

from amber.bits import BitWriter, gamma_encode
from amber.rac_codec import FLAG_A, FLAG_C, FLAG_T, FLAG_X, CoderParams, PayloadDecoder, PayloadEncoder, classify
from amber.real.divergence import load_generated, load_rank

RESULTS = Path(__file__).resolve().parent.parent / "results"
THETAS = (0.142, 0.465, 0.93)
MS = (2, 4)
R_MAX = 64
VOCAB_BITS = 17
TUNE_GRID = {"increment": (8, 16, 32, 64), "rescale_limit": (1 << 12, 1 << 14, 1 << 16)}


def gamma_bits(ranks: np.ndarray) -> int:
    w = BitWriter(); gap = 0
    for r in ranks:
        if r == 1:
            gap += 1; continue
        gamma_encode(w, gap + 1); gamma_encode(w, int(r) - 1); gap = 0
    return w.n_bits


def symbols_for(prompt: dict, ids: np.ndarray, p: CoderParams) -> list[tuple[int, int]]:
    """Encoder-side symbol stream for one prompt. T slots are uniform bits so
    the (unknown here) index-order slot costs the same as slot 0."""
    out = []
    for r, g, tok in zip(prompt["rank"].tolist(), prompt["gap"].tolist(), ids.tolist()):
        f = classify(r, g, p)
        out.append((f, r if f == FLAG_C else tok if f == FLAG_X else 0))
    return out


def qctx(prompt: dict) -> np.ndarray:
    """Research-only value context: q_max bucket x gap bucket (12 contexts)."""
    qmax = np.exp2(prompt["log2qmax"].astype(np.float64)); gap = prompt["gap"]
    qb = np.digitize(qmax, [0.5, 0.8, 0.95])          # 0..3
    gb = np.digitize(gap, [0.465, 2.0])               # 0..2
    return qb * 3 + gb


def code_split(prompts: list[dict], gen: dict, p: CoderParams, mode: str, use_qctx: bool = False) -> dict:
    """Returns real bits, ideal bits, per-prompt ideal bits and roundtrip status."""
    real = 0; ideal_pp = []; ok = True
    enc = PayloadEncoder(p) if mode == "concatenated" else None
    streams = []
    for pr in prompts:
        ids = gen[pr["row"]][0][gen[pr["row"]][1]:]
        syms = symbols_for(pr, ids, p)
        ctx = qctx(pr) if use_qctx else None
        if mode == "per_prompt":
            enc = PayloadEncoder(p)
        start = enc.ideal_bits
        for t, (f, v) in enumerate(syms):
            enc.step(t, f, v, 0 if ctx is None else int(ctx[t]))
        ideal_pp.append(enc.ideal_bits - start)
        streams.append((syms, ctx))
        if mode == "per_prompt":
            pay = enc.finish(); real += 8 * len(pay)
            ok &= _roundtrip(pay, [(syms, ctx)], p)
    if mode == "concatenated":
        pay = enc.finish(); real = 8 * len(pay)
        ok &= _roundtrip(pay, streams, p)
    return {"real_bits": real, "ideal_bits": float(sum(ideal_pp)), "ideal_bits_per_prompt": ideal_pp, "roundtrip_ok": bool(ok)}


def _roundtrip(pay: bytes, streams, p: CoderParams) -> bool:
    dec = PayloadDecoder(pay, p)
    for syms, ctx in streams:
        for t, (f, v) in enumerate(syms):
            got = dec.step(t, 0 if ctx is None else int(ctx[t]))
            if got != (f, v):
                return False
    return True


def content_bits(prompts, gen, tok) -> dict:
    text = "".join(tok.decode(gen[p["row"]][0][gen[p["row"]][1]:]) for p in prompts)
    b = text.encode("utf-8"); out = {"utf8": 8 * len(b), "zlib9": 8 * len(zlib.compress(b, 9)), "lzma": 8 * len(lzma.compress(b, preset=9))}
    try:
        import zstandard
        out["zstd19"] = 8 * len(zstandard.ZstdCompressor(level=19).compress(b))
    except ImportError:
        out["zstd19"] = None
    return out


def bootstrap_diff(a_pp: np.ndarray, b_pp: np.ndarray, n_pp: np.ndarray, n_boot=1000, seed=0) -> dict:
    """95% CI of (sum a / sum n) - (sum b / sum n) under prompt resampling."""
    g = np.random.default_rng(seed); k = len(n_pp); diffs = np.empty(n_boot)
    for i in range(n_boot):
        s = g.integers(0, k, k)
        diffs[i] = a_pp[s].sum() / n_pp[s].sum() - b_pp[s].sum() / n_pp[s].sum()
    return {"point": float(a_pp.sum() / n_pp.sum() - b_pp.sum() / n_pp.sum()),
            "ci95": [float(np.quantile(diffs, .025)), float(np.quantile(diffs, .975))], "n_boot": n_boot, "seed": seed}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/p1"); ap.add_argument("--split-at", type=int, default=100)
    a = ap.parse_args(argv); out = Path(a.out)
    gen = {r: (ids, plen) for r, ids, plen in load_generated(out)}
    draft = load_rank(out, "draft")
    tune = [p for p in draft["per_prompt"] if p["row"] < a.split_at]
    held = [p for p in draft["per_prompt"] if p["row"] >= a.split_at]
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(draft["meta"]["model"], local_files_only=True)
    V = len(tok)

    def n_tokens(ps): return int(sum(len(p["rank"]) for p in ps))
    def ac_pp(ps): return np.array([-float(p["log2q"].sum()) for p in ps])
    def npp(ps): return np.array([len(p["rank"]) for p in ps])

    # ---- tuning (tuning set only, concatenated, theta=0) ----------------------
    t0 = time.perf_counter(); tuning = []
    for inc, lim in itertools.product(TUNE_GRID["increment"], TUNE_GRID["rescale_limit"]):
        p = CoderParams(max_rank=R_MAX, vocab_bits=VOCAB_BITS, increment=inc, rescale_limit=lim)
        r = code_split(tune, gen, p, "concatenated")
        tuning.append({"increment": inc, "rescale_limit": lim, "bits_per_token": r["real_bits"] / n_tokens(tune), "roundtrip_ok": r["roundtrip_ok"]})
    best = min(tuning, key=lambda d: d["bits_per_token"])
    print(f"[tune] best on rows<{a.split_at}: inc={best['increment']} limit={best['rescale_limit']} {best['bits_per_token']:.4f} b/t ({time.perf_counter()-t0:.1f}s)")

    def params(theta=0.0, m=2, extra=1):
        return CoderParams(tie_margin=theta, tie_topm=m, max_rank=R_MAX, vocab_bits=VOCAB_BITS,
                           increment=best["increment"], rescale_limit=best["rescale_limit"], n_extra_ctx=extra)

    variants = {"rac1": (params(), False)}
    for th, m in itertools.product(THETAS, MS):
        variants[f"rac1_tie{th}_m{m}"] = (params(th, m), False)
    variants["rac1_qctx_UNSAFE"] = (params(extra=12), True)

    report = {}
    for split_name, ps in (("tuning", tune), ("held_out", held)):
        n = n_tokens(ps); cb = content_bits(ps, gen, tok)
        ranks = np.concatenate([p["rank"] for p in ps]); gaps = np.concatenate([p["gap"] for p in ps])
        row = {"n_prompts": len(ps), "positions": n, "divergence_rate": float((ranks != 1).mean()),
               "amber_v0_gamma_bits_per_token": gamma_bits(ranks) / n,
               "amber_v0_gamma_per_prompt_bytepadded_bits_per_token": sum(8 * ((gamma_bits(p["rank"]) + 7) // 8) for p in ps) / n,
               "ac_under_draft_bits_per_token": float(ac_pp(ps).sum() / n),
               "raw_bits_per_token": float(np.log2(V)),
               **{f"{k}_bits_per_token": (v / n if v is not None else None) for k, v in cb.items()},
               "escape_mass": {str(th): {str(m): float(((gaps < th) & (ranks <= m)).mean()) for m in MS} for th in THETAS},
               "rank_gt_R_rate": float((ranks > R_MAX).mean()), "modes": {}}
        for mode in ("concatenated", "per_prompt"):
            md = {}
            for name, (p, use_q) in variants.items():
                r = code_split(ps, gen, p, mode, use_q)
                if not r["roundtrip_ok"]:
                    raise RuntimeError(f"symbol roundtrip failed: {name} {mode} {split_name}")
                md[name] = {"bits_per_token": r["real_bits"] / n, "ideal_bits_per_token": r["ideal_bits"] / n}
                if mode == "concatenated" and name in ("rac1", "rac1_qctx_UNSAFE"):
                    md[name]["vs_ac_bootstrap"] = bootstrap_diff(np.array(r["ideal_bits_per_prompt"]), ac_pp(ps), npp(ps))
                md[name]["escape_price_vs_rac1"] = None
            base = md["rac1"]["bits_per_token"]
            for name in md:
                md[name]["escape_price_vs_rac1"] = md[name]["bits_per_token"] - base
            row["modes"][mode] = md
        report[split_name] = row
        print(f"\n== {split_name}: {len(ps)} prompts, {n} tokens, div {row['divergence_rate']:.4f}")
        print(f"  gamma {row['amber_v0_gamma_bits_per_token']:.4f}  AC {row['ac_under_draft_bits_per_token']:.4f}  zstd19 {row['zstd19_bits_per_token']}  raw {row['raw_bits_per_token']:.2f}")
        for mode, md in row["modes"].items():
            for name, d in md.items():
                extra = f"  CI {d['vs_ac_bootstrap']['ci95']}" if "vs_ac_bootstrap" in d else ""
                print(f"  {mode:13s} {name:22s} {d['bits_per_token']:.4f}  (+{d['escape_price_vs_rac1']:+.4f} vs rac1){extra}")

    ho = report["held_out"]; conc = ho["modes"]["concatenated"]["rac1"]
    ci = conc["vs_ac_bootstrap"]["ci95"]
    band = "PASS" if ci[1] < 0 else ("LOSE" if ci[0] > 0 else "TIE")
    fp32_penalty = 7360.866793607187 / 2014.6062444719903   # P2 llama32 census, cuda_bf16_b1 / cuda_fp32_b1 pos/s
    payload = {"_experiment": "p3_rac_rate", "_written_unix": int(time.time()), "protocol": "experiments/P3_PROTOCOL.md",
               "target": json.loads((out / "generate" / "meta.json").read_text()).get("target"), "draft": draft["meta"]["model"],
               "split_at_row": a.split_at, "tuning_grid": tuning, "chosen": {k: best[k] for k in ("increment", "rescale_limit")},
               "R_max": R_MAX, "thetas": THETAS, "ms": MS, "band_question1_heldout_concatenated": band,
               "fp32_decode_time_penalty_vs_bf16": fp32_penalty, "splits": report,
               "regime": f"P1 stream (Llama-3.2-3B->1B base, greedy, 256-token continuations of sideband prompts); held-out rows >= {a.split_at}; "
                         f"rates are real payload bytes x 8 per token, headers excluded; per_prompt includes range-coder flush/padding"}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "p3_rac_rate.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"\nBAND (held-out, concatenated, rac1 vs AC): {band}   CI {ci}")
    print("[saved] results/p3_rac_rate.json")


if __name__ == "__main__":
    main()

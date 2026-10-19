"""P2 — Rank-stability census of the ~1B Llama-architecture draft (BLUEPRINT Phase 2 / OQ-2).

Reads the top-k dumps written by `python -m amber.real.capture run ...` and
compares every arm against the CPU fp32 reference with amber.rankcensus.
Pre-registered (see experiments/P2_PROTOCOL.md; bands frozen before the run):

  tau per arm = 99.9th pct of that arm's OWN aligned |delta logit| vs the
  reference. A top-1 flip whose reference top-2 gap exceeds 2*tau cannot be
  explained by the perturbation the arm actually exhibits (XB-3 rule 3 with
  the arm's measured delta distribution as the calibration). Amended
  2026-08-29 before any real capture: the smoke run showed run-to-run and
  batch repeats are BIT-IDENTICAL on this box, so a tau calibrated from a
  repeat is 0 and would mark every flip a bug. Repeats are kept as explicit
  DETERMINISM checks instead (must be zero flips; nonzero => band c).

  Band (a) CONTRACT NEAR-FREE : every GPU arm has top-1 flip rate < 1e-3 AND
                                 flips_beyond_2tau == 0
  Band (b) NEAR-TIE ESCAPE    : some arm has top-1 flip rate >= 1e-3 but every
                                 flip is within 2*tau (all flips are near-ties)
  Band (c) PIPELINE BUG FIRST : any arm has flips_beyond_2tau > 0 — investigate
                                 before believing anything else
  Plus: batch invariance (cuda_bf16_b1 vs cuda_bf16_b8) reported as its own
  row; a batch-dependent delta beyond bf16's run-to-run tau is a mask/kernel
  bug (XB-3 rule 4). Burstiness reported; dispersion >> 1 => bursty
  corrections (lockstep E-006 stop condition), a wire-format question.

Spread: the census is reported per sequence-half as well as overall so a
single pathological sequence cannot carry a band.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from amber.rankcensus import calibrate_tau_topk, rank_census_topk
from amber.real.capture import ARMS, DEFAULT_OUT, REFERENCE_ARM, load_arm

RESULTS = Path(__file__).resolve().parent.parent / "results"
KS = (1, 2, 8, 64)
DETERMINISM_PAIRS = {  # name -> (a, b): expected bit-identical dumps
    "run_to_run:cpu_fp32": ("cpu_fp32", "cpu_fp32_rep"),
    "run_to_run:cuda_bf16_b1": ("cuda_bf16_b1", "cuda_bf16_b1_rep"),
    "batch_invariance:cuda_bf16_b1_vs_b8": ("cuda_bf16_b1", "cuda_bf16_b8"),
    "batch_invariance:cuda_fp32_b1_vs_b8": ("cuda_fp32_b1", "cuda_fp32_b8"),
}
DECIDING_ARMS = ("cuda_fp32_b1", "cuda_bf16_b1", "cuda_fp16_b1")  # int8/nf4 reported, not deciding


def census_row(name: str, ref, alt, tau: float | None, n_seqs: int, seq_len: int) -> dict:
    ri, rv = ref; ai, av = alt
    c = rank_census_topk(ri, rv, ai, av, ks=KS, tau=None if tau is None else 2 * tau, window=seq_len)
    row = {"arm": name, "tau": tau, **c.to_dict()}
    half = (n_seqs // 2) * seq_len
    halves = []
    for lo, hi in ((0, half), (half, ri.shape[0])):
        h = rank_census_topk(ri[lo:hi], rv[lo:hi], ai[lo:hi], av[lo:hi], ks=(1,),
                             tau=None if tau is None else 2 * tau, window=seq_len)
        halves.append({"top1_flip_rate": h.top1_flip_rate, "flips_beyond_2tau": h.flips_beyond_tau})
    row["halves"] = halves
    return row


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--topk", type=int, default=64)
    a = ap.parse_args(argv)
    out = Path(a.out)

    have = {n for n in ARMS if (out / n / "DONE").exists()}
    if REFERENCE_ARM not in have:
        raise SystemExit(f"reference arm {REFERENCE_ARM} not captured")
    dumps = {n: load_arm(out, n, a.topk) for n in have}
    meta_ref = dumps[REFERENCE_ARM][2]
    n_seqs, seq_len = meta_ref["n_seqs"], meta_ref["seq_len"]
    for n, (_, _, m) in dumps.items():
        if m["corpus_sha256"] != meta_ref["corpus_sha256"]:
            raise SystemExit(f"arm {n} was captured on a different corpus")

    ref = (dumps[REFERENCE_ARM][0], dumps[REFERENCE_ARM][1])
    rows, taus = [], {}
    for n in sorted(have):
        if n == REFERENCE_ARM or n.endswith("_rep"):
            continue
        tau = calibrate_tau_topk(ref[0], ref[1], dumps[n][0], dumps[n][1])
        taus[n] = tau
        rows.append(census_row(n, ref, (dumps[n][0], dumps[n][1]), tau, n_seqs, seq_len))
        r = rows[-1]
        print(f"{n:18s} tau={tau:.4g} top1 {r['top1_flip_rate']:.5f} ({r['top1_flips']}) beyond2tau={r['flips_beyond_tau']} "
              f"set8 {r['topk_set_flip_rate'].get('8', float('nan')):.4f} p99d={r['p99_abs_logit_delta']:.3g} "
              f"disp={r['dispersion_index']} halves={[h['top1_flip_rate'] for h in r['halves']]}")

    determinism = {}
    for name, (x, y) in DETERMINISM_PAIRS.items():
        if x in have and y in have:
            d = census_row(name, (dumps[x][0], dumps[x][1]), (dumps[y][0], dumps[y][1]), 0.0, n_seqs, seq_len)
            determinism[name] = {"top1_flips": d["top1_flips"], "top1_flip_rate": d["top1_flip_rate"],
                                 "max_abs_logit_delta": d["max_abs_logit_delta"],
                                 "bit_identical": d["max_abs_logit_delta"] == 0.0 and d["delta_coverage"] == 1.0
                                                  and d["topk_order_flip_rate"][str(max(d["ks"]))] == 0.0}
            print(f"determinism {name}: {determinism[name]}")

    # POST-HOC investigation block (added 2026-08-29 AFTER the first census; does
    # NOT alter the pre-registered band): judge each batch pair at the dtype's
    # own 2*tau and report in-batch-row / position signatures of the delta.
    investigation = {}
    for name, (x, y) in DETERMINISM_PAIRS.items():
        if not name.startswith("batch_invariance") or x not in have or y not in have:
            continue
        tau_x = taus.get(x)
        c = rank_census_topk(dumps[x][0], dumps[x][1], dumps[y][0], dumps[y][1], ks=(1, 8, 64),
                             tau=None if tau_x is None else 2 * tau_x, window=seq_len)
        dmax = np.abs(dumps[x][1] - dumps[y][1]).max(axis=1).reshape(n_seqs, seq_len)
        bsz = ARMS[y].batch
        by_row = dmax.max(axis=1)[: (n_seqs // bsz) * bsz].reshape(-1, bsz).mean(axis=0)
        investigation[name] = {
            "judged_at_2tau_of": x, "tau": tau_x, "top1_flips": c.top1_flips,
            "flips_beyond_2tau": c.flips_beyond_tau, "flip_gap_max": c.flip_gap_max,
            "max_abs_delta_by_in_batch_row": [float(v) for v in by_row],
            "max_abs_delta_by_position_quarter": [float(dmax[:, i:i + seq_len // 4].max()) for i in range(0, seq_len, seq_len // 4)],
        }
        print(f"investigation {name}: beyond2tau={c.flips_beyond_tau} gap_max={c.flip_gap_max} by_row={np.round(by_row, 3).tolist()}")

    # mechanical band evaluation over the deciding arms present
    deciding = [r for r in rows if r["arm"] in DECIDING_ARMS]
    band = None
    if deciding:
        if any(r["flips_beyond_tau"] > 0 for r in deciding) or any(not v["bit_identical"] and v["top1_flips"] > 0 for v in determinism.values()):
            band = "c:pipeline-bug-first"
        elif all(r["top1_flip_rate"] < 1e-3 for r in deciding):
            band = "a:contract-near-free"
        else:
            band = "b:near-tie-escape-needed"
    payload = {
        "_experiment": "p2_rank_census", "_written_unix": int(time.time()),
        "reference_arm": REFERENCE_ARM, "topk_used": a.topk, "ks": list(KS),
        "n_seqs": n_seqs, "seq_len": seq_len, "positions": n_seqs * seq_len,
        "corpus_sha256": meta_ref["corpus_sha256"],
        "provenance": {n: dumps[n][2].get("provenance") for n in sorted(have)},
        "throughput_pos_per_s": {n: float(np.mean([s["positions_per_s"] for s in dumps[n][2]["shards"].values()])) for n in sorted(have)},
        "calibrated_tau_per_arm": taus, "rows": rows, "determinism_checks": determinism,
        "deciding_arms": list(DECIDING_ARMS), "post_hoc_investigation": investigation,
        "band": band,
        "regime": f"{meta_ref.get('provenance', {}).get('model_id', '?')} draft, teacher-forced {n_seqs}x{seq_len} windows of a wiki/docs corpus, "
                  "top-k dumps, CPU fp32 reference, one 3080 Ti box; bands pre-registered in P2_PROTOCOL.md",
    }
    RESULTS.mkdir(exist_ok=True)
    fname = f"{out.name}_rank_census.json"
    (RESULTS / fname).write_text(json.dumps(payload, indent=2, sort_keys=True))
    print("band:", band)
    print(f"[saved] results/{fname}")


if __name__ == "__main__":
    main()

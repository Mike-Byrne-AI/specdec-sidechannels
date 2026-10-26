"""A03 — Rank-flip census on synthetic drafts: instrument shakedown + the
expected SHAPE before any GPU run (BLUEPRINT Phase 2 / OQ-2 pre-registration).

The sideband world's draft distributions q are perturbed in LOGIT space with
Gaussian noise of scale eps (the lockstep E-006 / PA-3 drift class). For each
eps we report top-1 / top-8 flip rates, the near-tie attribution of every
flip (reference top-2 gap), and burstiness. The pre-registered expectation:

  * top-1 flip rate follows the Gaussian near-tie law
    mean_t 0.5*erfc(gap_t / 2eps) (gaussian_flip_law) — i.e. flips are
    entirely explained by near-ties (flips_beyond_tau == 0 when tau is
    calibrated from an independent draw at the same eps);
  * flips are Poisson-scattered (dispersion index ~1) because the synthetic
    drift is i.i.d. — REAL drift may be bursty (E-006 stop condition), which
    is exactly what the GPU run must check and this world cannot.

This is instrument validation in a regime where the answer is known; nothing
here is a claim about real hardware.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
from sideband.synthetic import World, WorldConfig

from amber.rankcensus import calibrate_tau, rank_census, top2_gap

RESULTS = Path(__file__).resolve().parent.parent / "results"


def gaussian_flip_law(gaps: np.ndarray, eps: float) -> float:
    """Pre-registered predictor: under i.i.d. N(0, eps^2) logit noise the
    top-2 difference moves by N(0, 2 eps^2), so P(top-1 flip) ~= mean over
    positions of P(N(0, sqrt(2) eps) > gap) = 0.5 * erfc(gap / (2 eps)).
    Ignores flips from tokens ranked 3+ (a lower bound for small eps)."""
    z = gaps / (2.0 * eps)
    return float(np.mean(0.5 * np.array([math.erfc(v) for v in z])))


def draft_logits(cfg: WorldConfig, path_seed: int, draft_seed: int, length: int) -> np.ndarray:
    world = World(cfg)
    path = world.sample_concept_path(np.random.default_rng(path_seed), length)
    gen = np.random.default_rng(draft_seed)
    out = np.empty((length, cfg.vocab_size))
    for t in range(length):
        q = world.draft_dist(world.draft_concept(gen, int(path[t])))
        out[t] = np.log(np.maximum(q, 1e-300))
    return out


def main() -> None:
    T = 6000
    cfg = WorldConfig(draft_alpha=0.7, draft_temperature=1.6, seed=0)
    ref = draft_logits(cfg, 100, 200, T)
    gaps = top2_gap(ref)
    rows = []
    for eps in (1e-3, 1e-2, 3e-2, 5e-2, 1e-1, 2e-1, 3e-1):
        per_seed = []
        for s in (1, 2, 3):
            alt = ref + np.random.default_rng(1000 + s).normal(scale=eps, size=ref.shape)
            benign = ref + np.random.default_rng(2000 + s).normal(scale=eps, size=ref.shape)
            tau = calibrate_tau(ref, benign, 0.999)
            c = rank_census(ref, alt, ks=(1, 8, 64), tau=2 * tau, window=64)
            per_seed.append({
                "seed": s, "tau_calibrated": tau,
                "top1_flip_rate": c.top1_flip_rate,
                "top8_set_flip_rate": c.topk_set_flip_rate["8"],
                "top8_order_flip_rate": c.topk_order_flip_rate["8"],
                "flips_beyond_2tau": c.flips_beyond_tau,
                "flip_gap_median": c.flip_gap_median,
                "dispersion_index": c.dispersion_index,
                "longest_flip_run": c.longest_flip_run,
                "near_tie_law_prediction": gaussian_flip_law(gaps, eps),
            })
        rates = [r["top1_flip_rate"] for r in per_seed]
        row = {"eps": eps, "top1_flip_rate_mean": float(np.mean(rates)),
               "top1_flip_rate_spread": [float(min(rates)), float(max(rates))],
               "flips_beyond_2tau_total": int(sum(r["flips_beyond_2tau"] for r in per_seed)),
               "per_seed": per_seed}
        rows.append(row)
        print(f"eps={eps:.0e} top1 {row['top1_flip_rate_mean']:.4f} "
              f"[{row['top1_flip_rate_spread'][0]:.4f},{row['top1_flip_rate_spread'][1]:.4f}] "
              f"beyond2tau={row['flips_beyond_2tau_total']} "
              f"disp={per_seed[0]['dispersion_index']} "
              f"law={per_seed[0]['near_tie_law_prediction']:.4f}")

    payload = {
        "_experiment": "a03_rank_flip_synthetic", "_written_unix": int(time.time()),
        "T": T, "vocab": int(cfg.vocab_size),
        "gap_quantiles_reference": {q: float(np.quantile(gaps, float(q))) for q in ("0.001", "0.01", "0.1", "0.5")},
        "rows": rows,
        "regime": "sideband synthetic concept-HMM v0 world drafts (alpha 0.7, T=1.6), i.i.d. "
                  "Gaussian logit-space drift, T=6000 x 3 noise seeds; instrument shakedown, "
                  "not a hardware measurement",
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "a03_rank_flip_synthetic.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print("[saved] results/a03_rank_flip_synthetic.json")


if __name__ == "__main__":
    main()

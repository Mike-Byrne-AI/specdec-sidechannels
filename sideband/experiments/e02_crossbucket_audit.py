"""E02 — Cross-bucket rejection audit (Phase 0a; the kill-shot diagnostic).

Question: of all vanilla-specdec rejections, what fraction are CROSS-BUCKET
(draft proposed a token in a different bucket than the target emitted)?
Only that share is even addressable by bucket steering. If it's small, the
project dies here cheaply — which is the point of running this first.

Sweeps draft concept-accuracy (draft_alpha): a weaker draft should show a
larger addressable share, mapping where steering has room to matter.
"""

from __future__ import annotations

import argparse

from _util import mean_std, save_json, smoke_results
from sideband.pipeline import run_simulation
from sideband.synthetic import World, WorldConfig


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    n_positions = 3000 if smoke else 24000
    seeds = [0] if smoke else [0, 1, 2]
    alphas = [0.5, 0.7, 0.9]
    gamma = 4

    rows = []
    for alpha in alphas:
        accs, fracs, masses, rej = [], [], [], 0
        for seed in seeds:
            world = World(WorldConfig(draft_alpha=alpha, seed=seed))
            res = run_simulation(world, seed=seed + 100, n_positions=n_positions,
                                 gamma=gamma, policy="none")
            accs.append(res.metrics.acceptance_rate)
            fracs.append(res.cross_bucket_fraction())
            masses.append(res.cross_bucket_mass_fraction())
            rej += len(res.rejection_buckets)
        rows.append({
            "draft_alpha": alpha,
            "acceptance_rate": mean_std(accs),
            "cross_bucket_fraction_of_rejections": mean_std(fracs),
            "cross_bucket_residual_mass": mean_std(masses),
            "n_rejections_total": rej,
        })
        print(rows[-1])

    payload = {
        "gamma": gamma,
        "n_positions": n_positions,
        "seeds": seeds,
        "rows": rows,
        "regime": "synthetic concept-HMM v0, default WorldConfig except draft_alpha; "
                  "state-observed target; buckets = ground-truth blocks",
        "interpretation": "residual_mass is the variance-free estimator of the same estimand as the sampled fraction (F-8). cross_bucket_fraction is the ceiling on the SHARE of "
                          "rejections concept-steering can address, not on acceptance "
                          "itself (within-bucket token choice still has to match).",
    }
    save_json("e02_crossbucket_audit.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

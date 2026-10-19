"""E03 — Oracle steering ceilings + beta sweep (Phase 0b).

Policies compared at each bias strength beta:
  oracle_concept_now    non-causal ceiling (fresh true state every position)
  oracle_concept_stale  causal ceiling (perfect decoder of last-position state)
  free_lastp            free-information baseline (no telemetry at all)

Expected shape (and why it matters):
- acceptance vs beta is NON-monotone for concept policies: past some beta the
  boost starves the shared function tokens the target still wants — the
  function-word tax. The best beta is finite; hard masks are the beta->inf
  pathology.
- free_lastp ~= oracle_concept_stale in THIS world by construction (both are
  functions of the same latent state at the same position). The real-model
  question OQ-1 is whether telemetry beats free_lastp there.
"""

from __future__ import annotations

import argparse

from _util import save_json, smoke_results
from sideband.pipeline import run_simulation
from sideband.synthetic import World, WorldConfig


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    n_positions = 2500 if smoke else 16000
    betas = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0] if not smoke else [0.0, 1.5, 6.0]
    policies = ["oracle_concept_now", "oracle_concept_stale", "free_lastp"]
    gamma = 4
    world = World(WorldConfig())

    base = run_simulation(world, seed=100, n_positions=n_positions, gamma=gamma, policy="none")
    rows = {"none": {"beta": None, "analytic_acceptance": base.analytic_acceptance,
                     "empirical_acceptance": base.metrics.acceptance_rate,
                     "tokens_per_target_call": base.metrics.tokens_per_target_call}}

    for policy in policies:
        rows[policy] = {}
        for gate in ("always", "disagree"):
            curve = []
            for beta in betas:
                res = run_simulation(world, seed=100, n_positions=n_positions,
                                     gamma=gamma, policy=policy, beta=beta,
                                     steer_gate=gate)
                curve.append({
                    "beta": beta,
                    "analytic_acceptance": res.analytic_acceptance,
                    "empirical_acceptance": res.metrics.acceptance_rate,
                    "tokens_per_target_call": res.metrics.tokens_per_target_call,
                    "steered_positions": res.steered_positions,
                })
                print(policy, gate, curve[-1])
            best = max(curve, key=lambda r: r["analytic_acceptance"])
            rows[policy][gate] = {"curve": curve, "best": best}

    payload = {
        "gamma": gamma,
        "n_positions": n_positions,
        "betas": betas,
        "rows": rows,
        "regime": "synthetic concept-HMM v0, default WorldConfig (lambda_function=0.45, "
                  "rho=0.92, draft_alpha=0.70, draft_temperature=1.6)",
    }
    save_json("e03_oracle_ceiling.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

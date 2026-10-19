"""E04 — Staleness decay (the Hole-2 quantification).

Telemetry available for a block is from the LAST VERIFIED position; drafted
positions sit 1..gamma steps into the future. This experiment measures the
per-offset analytic acceptance of the stale-oracle policy against the fresh
oracle and vanilla, across concept persistence rho.

Reading: the (fresh - stale) gap at offset j is the pure staleness tax at
that offset; where stale drops to vanilla, held-bucket steering has aged out.
Expected: tax grows with offset and shrinks with rho (persistence ~ how long
one concept read stays actionable). This is the curve that decides how large
gamma can usefully be for a telemetry-steered draft.
"""

from __future__ import annotations

import argparse

from _util import save_json, smoke_results
from sideband.pipeline import run_simulation
from sideband.synthetic import World, WorldConfig


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    n_positions = 2500 if smoke else 14000
    rhos = [0.75, 0.92] if smoke else [0.6, 0.75, 0.9, 0.97]
    gamma = 6
    beta = 2.5

    rows = []
    for rho in rhos:
        world = World(WorldConfig(rho=rho))
        kw = dict(seed=200, n_positions=n_positions, gamma=gamma)
        base = run_simulation(world, policy="none", **kw)
        stale = run_simulation(world, policy="oracle_concept_stale", beta=beta, steer_gate="disagree", **kw)
        fresh = run_simulation(world, policy="oracle_concept_now", beta=beta, steer_gate="disagree", **kw)

        def by_offset(res):
            return {j: float(sum(v) / len(v)) for j, v in sorted(res.analytic_by_offset.items())}

        rows.append({
            "rho": rho,
            "expected_run_length": 1.0 / (1.0 - rho),
            "vanilla_by_offset": by_offset(base),
            "stale_by_offset": by_offset(stale),
            "fresh_by_offset": by_offset(fresh),
        })
        print(rows[-1])

    payload = {
        "gamma": gamma,
        "beta": beta,
        "n_positions": n_positions,
        "rows": rows,
        "regime": "synthetic concept-HMM v0, default WorldConfig except rho; disagreement-gated beta=2.5; "
                  "stale policy holds last-verified concept for the whole block",
    }
    save_json("e04_staleness_decay.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

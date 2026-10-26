"""E05 — Sidecar recovery vs sketch width (Phase 3 in miniature).

Train the sidecar on (slot multi-hot -> concept) at several slot counts K and
measure (a) holdout decode accuracy and (b) end-to-end analytic acceptance
when the sidecar drives steering, with and without confidence gating (tau), expressed as RECOVERY of the stale-oracle
gain:

    recovery = (sidecar - vanilla) / (stale_oracle - vanilla)

This answers 'how narrow can the physical sideband be before the decoder, and
therefore the steering, degrades' — the hardware-facing number. Collisions
(units per slot) rise as K falls; expected_collision_rate is logged.
"""

from __future__ import annotations

import argparse

from _util import save_json, smoke_results
from sideband.pipeline import run_simulation, train_sidecar
from sideband.synthetic import World, WorldConfig


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    n_positions = 2500 if smoke else 12000
    slot_counts = [16, 128] if smoke else [8, 16, 32, 64, 256, 1024]
    beta, gamma = 2.5, 4
    n_train = 4000 if smoke else 20000
    # Hardened telemetry (vs WorldConfig defaults) so decoder quality actually
    # varies with K: weaker support gain, more noise, narrower top-N.
    hard = dict(support_gain=0.5, support_noise=0.5, background_noise=0.25, top_n=16)

    rows = []
    for k in slot_counts:
        world = World(WorldConfig(n_slots=k, **hard))
        model, holdout = train_sidecar(world, seed=300, n_train=n_train,
                                       epochs=10 if smoke else 25)
        kw = dict(seed=301, n_positions=n_positions, gamma=gamma)
        base = run_simulation(world, policy="none", **kw).analytic_acceptance
        stale = run_simulation(world, policy="oracle_concept_stale", beta=beta, steer_gate="disagree", **kw).analytic_acceptance
        side0 = run_simulation(world, policy="sidecar", beta=beta, tau=0.0,
                               sidecar=model, steer_gate="disagree", **kw).analytic_acceptance
        side5 = run_simulation(world, policy="sidecar", beta=beta, tau=0.5,
                               sidecar=model, steer_gate="disagree", **kw).analytic_acceptance
        denom = stale - base
        rec = lambda x: (x - base) / denom if denom > 1e-9 else float("nan")
        rows.append({
            "n_slots": k,
            "mean_units_per_slot": world.cfg.n_units / k,
            "sidecar_holdout_acc": holdout,
            "vanilla": base,
            "stale_oracle": stale,
            "sidecar_tau0": side0,
            "recovery_tau0": rec(side0),
            "sidecar_tau05": side5,
            "recovery_tau05": rec(side5),
        })
        print(rows[-1])

    payload = {
        "gamma": gamma, "beta": beta, "tau_variants": [0.0, 0.5],
        "n_positions": n_positions, "n_train": n_train,
        "rows": rows,
        "regime": "synthetic concept-HMM v0, hardened telemetry (support_gain=0.5, support_noise=0.5, background_noise=0.25, top_n=16), n_slots swept; "
                  "sidecar = softmax regression on slot multi-hot at last verified position; disagreement-gated beta=2.5",
    }
    save_json("e05_sidecar_recovery.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

"""E06 — Posterior mechanism vs argmax (the F-7 experiment).

Part A (default world): for each policy, argmax(tau=0) vs posterior at the
same beta and gate, paired seeds. Shows the mechanism effect with real block
dynamics.

Part B (hardened telemetry, K swept): the F-5 table redone with BOTH
mechanisms and BOTH denominators. D-11 lesson made concrete: the posterior
sidecar can exceed 100% recovery against the ARGMAX oracle (wrong ceiling),
so recovery must be quoted against the mechanism-matched (posterior) oracle.

Free-baseline note (D-5 hygiene, discovered while building this): under the
posterior mechanism, free_lastp's SOFT bucket-mass posterior is flatter than
a one-hot, so it scores below the stale oracle even though both are functions
of the same latent. The fair free baseline includes the SHARPENED variant —
one-hot at argmax(p_last) — which in this world coincides exactly with
oracle_concept_stale (posterior). F-6 stands; on real models run BOTH free
variants.
"""

from __future__ import annotations

import argparse

import numpy as np

import _util
from _util import mean_std, save_json, smoke_results
from sideband.pipeline import run_simulation, train_sidecar
from sideband.synthetic import World, WorldConfig

HARD = dict(support_gain=0.5, support_noise=0.5, background_noise=0.25, top_n=16)


BETA, GAMMA = 2.5, 4
# partial files live beside the payload in _util.RESULTS, so they follow the smoke redirect (2026-10-16)
PARTIAL_A = "_e06_part_a.json"
PARTIAL_B = "_e06_part_b_%d.json"


def part_a(smoke: bool = False) -> dict:
    beta, gamma = BETA, GAMMA
    nA = 2500 if smoke else 12000
    seedsA = [400] if smoke else [400, 401]
    world = World(WorldConfig())
    base = [run_simulation(world, seed=s, n_positions=nA, gamma=gamma, policy="none").analytic_acceptance
            for s in seedsA]
    part_a = {"vanilla": mean_std(base)}
    for pol in ("oracle_concept_stale", "oracle_concept_now", "free_lastp"):
        part_a[pol] = {}
        for mech in ("argmax", "posterior"):
            vals = [run_simulation(world, seed=s, n_positions=nA, gamma=gamma, policy=pol,
                                   beta=beta, steer_gate="disagree", steer_mech=mech).analytic_acceptance
                    for s in seedsA]
            part_a[pol][mech] = {**mean_std(vals),
                                 "delta_vs_vanilla": float(np.mean(vals) - np.mean(base))}
            print("A", pol, mech, part_a[pol][mech])
    return {"data": part_a, "n": nA, "seeds": seedsA}


def part_b(smoke: bool = False, slot_counts=None) -> dict:
    beta, gamma = BETA, GAMMA
    nB = 2000 if smoke else 8000
    seedsB = [401] if smoke else [401, 402]
    if slot_counts is None:
        slot_counts = [64] if smoke else [16, 64, 256]
    n_train, epochs = (3000, 8) if smoke else (12000, 15)

    rows = []
    for k in slot_counts:
        wh = World(WorldConfig(n_slots=k, **HARD))
        model, holdout = train_sidecar(wh, seed=300, n_train=n_train, epochs=epochs)
        def run(**kw):
            return float(np.mean([
                run_simulation(wh, seed=s, n_positions=nB, gamma=gamma, **kw).analytic_acceptance
                for s in seedsB
            ]))
        vanilla = run(policy="none")
        or_am = run(policy="oracle_concept_stale", beta=beta, steer_gate="disagree", steer_mech="argmax")
        or_po = run(policy="oracle_concept_stale", beta=beta, steer_gate="disagree", steer_mech="posterior")
        sc_am0 = run(policy="sidecar", beta=beta, steer_gate="disagree", steer_mech="argmax", sidecar=model)
        sc_am5 = run(policy="sidecar", beta=beta, tau=0.5, steer_gate="disagree", steer_mech="argmax", sidecar=model)
        sc_po = run(policy="sidecar", beta=beta, steer_gate="disagree", steer_mech="posterior", sidecar=model)
        rec = lambda x, d: (x - vanilla) / d if d > 1e-9 else float("nan")
        rows.append({
            "n_slots": k, "sidecar_holdout_acc": holdout,
            "vanilla": vanilla, "oracle_argmax": or_am, "oracle_posterior": or_po,
            "sidecar_argmax_tau0": sc_am0, "sidecar_argmax_tau05": sc_am5, "sidecar_posterior": sc_po,
            "recovery_vs_argmax_oracle": {
                "argmax_tau0": rec(sc_am0, or_am - vanilla),
                "argmax_tau05": rec(sc_am5, or_am - vanilla),
                "posterior": rec(sc_po, or_am - vanilla),
            },
            "recovery_vs_posterior_oracle": {"posterior": rec(sc_po, or_po - vanilla)},
        })
        print("B", rows[-1])
    return {"rows": rows, "n": nB, "seeds": seedsB}


def _assemble(a: dict, b_rows: list[dict], nA, seedsA, nB, seedsB) -> dict:
    payload = {
        "beta": BETA, "gamma": GAMMA, "gate": "disagree",
        "part_a_default_world": a,
        "part_b_hardened": sorted(b_rows, key=lambda r: r["n_slots"]),
        "regime": "part A: synthetic concept-HMM v0, default WorldConfig, n=%d, seeds %s; "
                  "part B: hardened telemetry (support_gain=0.5, support_noise=0.5, "
                  "background_noise=0.25, top_n=16), n=%d, seeds %s" % (nA, seedsA, nB, seedsB),
    }
    save_json("e06_posterior_mechanism.json", payload)
    return payload


def main(smoke: bool = False, part: str = "all", slots: int | None = None) -> dict:
    """part='all' runs everything in-process (run_all/CI path). Long CPU
    sessions can chunk: --part a, then --part b --slots K per K, then
    --part merge (assembles the canonical json from partials, same code path,
    and removes them)."""
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    import json as _json

    if part == "all":
        a = part_a(smoke)
        b = part_b(smoke)
        return _assemble(a["data"], b["rows"], a["n"], a["seeds"], b["n"], b["seeds"])
    if part == "a":
        a = part_a(smoke)
        _util.RESULTS.mkdir(parents=True, exist_ok=True)
        (_util.RESULTS / PARTIAL_A).write_text(_json.dumps(a))
        return a
    if part == "b":
        assert slots is not None, "--part b needs --slots"
        b = part_b(smoke, slot_counts=[slots])
        _util.RESULTS.mkdir(parents=True, exist_ok=True)
        (_util.RESULTS / (PARTIAL_B % slots)).write_text(_json.dumps(b))
        return b
    if part == "merge":
        a = _json.loads((_util.RESULTS / PARTIAL_A).read_text())
        parts = sorted(_util.RESULTS.glob("_e06_part_b_*.json"))
        assert parts, "no part-b partials found"
        rows, nB, seedsB = [], None, None
        for f in parts:
            b = _json.loads(f.read_text())
            rows.extend(b["rows"]); nB, seedsB = b["n"], b["seeds"]
        payload = _assemble(a["data"], rows, a["n"], a["seeds"], nB, seedsB)
        for f in [_util.RESULTS / PARTIAL_A, *parts]:
            f.unlink()
        return payload
    raise ValueError(part)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--part", choices=["all", "a", "b", "merge"], default="all")
    ap.add_argument("--slots", type=int, default=None)
    main(**vars(ap.parse_args()))

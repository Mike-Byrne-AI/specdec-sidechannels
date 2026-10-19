"""E07 — Hint-rate accounting v0 (the verified-archives track, OQ-7).

At COMPRESS time the causality constraint drops: the encoder has the future
and can spend bits on a hint stream that raises the draft's acceptance,
buying back correction bits. This experiment does the v0 ledger in the
synthetic world:

  correction cost   = sum over rejections of -log2 r[emitted]   (ideal coding
                      under the residual — what the archive must store)
  hint cost (H1)    = log2(C) per DRAFTED position for the fresh oracle
                      (worst-case: pay for re-drafts too)
  net               = correction bits saved vs vanilla - hint bits spent

Deliberately conservative v0: omits the accept/reject indicator stream
(identical across arms to first order), assumes ideal entropy coding, and
prices the most expensive hint scheme. If H1 doesn't pay HERE, per-position
full-concept hints are dead and the archives track needs event-driven hints
(topic-shift flags, rejection-triggered hints) — that constraint is the
point of running this.
"""

from __future__ import annotations

import argparse

import numpy as np

from _util import mean_std, save_json, smoke_results
from sideband.pipeline import run_simulation
from sideband.synthetic import World, WorldConfig


def ledger(res, hint_bits_per_proposed: float) -> dict:
    n_emit = res.metrics.n_emitted
    corr_bits = float(np.sum(res.rejection_bits))
    hint_bits = hint_bits_per_proposed * res.metrics.n_proposed
    return {
        "acceptance": res.analytic_acceptance,
        "rejections_per_emitted": len(res.rejection_bits) / n_emit,
        "mean_bits_per_correction": res.mean_rejection_bits(),
        "correction_bits_per_emitted": corr_bits / n_emit,
        "hint_bits_per_emitted": hint_bits / n_emit,
        "total_bits_per_emitted": (corr_bits + hint_bits) / n_emit,
    }


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    n = 3000 if smoke else 16000
    seeds = [500] if smoke else [500, 501]
    beta, gamma = 2.5, 4
    world = World(WorldConfig())
    C = world.cfg.n_concepts
    hint_h1 = float(np.log2(C))

    arms = {
        "vanilla": dict(kw=dict(policy="none"), hint=0.0),
        "free_causal": dict(kw=dict(policy="free_lastp", beta=beta,
                                    steer_gate="disagree", steer_mech="posterior"), hint=0.0),
        "hint_h1_fresh": dict(kw=dict(policy="oracle_concept_now", beta=beta,
                                      steer_gate="disagree", steer_mech="posterior"), hint=hint_h1),
    }
    out = {}
    for name, arm in arms.items():
        ledgers = [ledger(run_simulation(world, seed=s, n_positions=n, gamma=gamma, **arm["kw"]),
                          arm["hint"]) for s in seeds]
        out[name] = {k: mean_std([l[k] for l in ledgers]) for k in ledgers[0]}
        print(name, {k: round(v["mean"], 4) for k, v in out[name].items()})

    base_corr = out["vanilla"]["correction_bits_per_emitted"]["mean"]
    for name in ("free_causal", "hint_h1_fresh"):
        saved = base_corr - out[name]["correction_bits_per_emitted"]["mean"]
        spent = out[name]["hint_bits_per_emitted"]["mean"]
        out[name]["_summary"] = {
            "correction_bits_saved_per_emitted": saved,
            "hint_bits_spent_per_emitted": spent,
            "net_bits_per_emitted": saved - spent,
            "breakeven_hint_budget_bits_per_emitted": saved,
        }
        print(name, "summary", {k: round(v, 4) for k, v in out[name]["_summary"].items()})

    payload = {
        "beta": beta, "gamma": gamma, "n_positions": n, "seeds": seeds,
        "hint_bits_per_proposed_h1": hint_h1,
        "arms": out,
        "regime": "synthetic concept-HMM v0, default WorldConfig; posterior mechanism, "
                  "disagreement gate; ideal-coding ledger, indicator stream omitted, "
                  "H1 priced per drafted position (conservative)",
    }
    save_json("e07_hint_rate.json", payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

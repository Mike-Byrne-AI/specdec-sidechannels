"""F-9's ledger with the bonus token and the accept/reject indicator priced (image audit 2026-10-15,
section B item 5; the S8 refuter's e07_ledger.py made tree-relative).

Wraps sideband.pipeline.run_block to log, per block, the ideal-coding cost of the bonus token the
verifier emits (-log2 p_target at the bonus position) and of the accept/reject indicator stream, with
no extra RNG draw, then runs e07's three arms (vanilla, free_causal, hint_h1_fresh) at seeds 500 and
501, n_positions 16000, gamma 4, beta 2.5, posterior mechanism, disagreement gate, exactly as
experiments/e07_hint_rate.py does.

Pinned 2026-10-16 before the lane-B rerun (the audit's figures), asserted by the script: correction bits
per emitted token 1.2704 / 1.1707 / 1.1083 must match the committed results/e07_hint_rate.json arms
within 5e-5; bonus tokens per emitted 0.0628 / 0.0654 / 0.0684; mean bonus cost 5.54 / 5.52 / 5.57 bits;
unpriced bonus bits per emitted 0.348 / 0.361 / 0.381; savings with the bonus term priced 0.0862 (free)
and 0.1291 (fresh) against the committed 0.0997 and 0.1621. The script exits non-zero on any mismatch
and writes e07_ledger_out.json next to itself only when every pin holds; the output records the numpy
version. About ten seconds on CPU.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]  # docs/audits/<folder>/ -> the repository root
sys.path.insert(0, str(REPO / "src"))
import sideband.pipeline as pl  # noqa: E402
from sideband.dists import normalize  # noqa: E402
from sideband.synthetic import World, WorldConfig  # noqa: E402

LOG: dict[str, list[float]] = {}
_real = pl.run_block
PINS = {"vanilla": (1.2704, 0.0628, 5.54, 0.348), "free_causal": (1.1707, 0.0654, 5.52, 0.361),
        "hint_h1_fresh": (1.1083, 0.0684, 5.57, 0.381)}
PIN_SAVED = {"free_causal": 0.0862, "hint_h1_fresh": 0.1291}


def wrapped(gen, target_dists, draft_dists):
    b = _real(gen, target_dists, draft_dists)
    if b.bonus is not None:
        p = normalize(target_dists[len(draft_dists)])
        LOG["bonus_bits"].append(-math.log2(max(p[b.bonus], 1e-300)))
    for st in b.steps:
        a = st.accept_prob
        if st.accepted:
            LOG["ind_bits"].append(0.0 if a >= 1.0 else -math.log2(a))
        else:
            LOG["ind_bits"].append(-math.log2(max(1.0 - a, 1e-300)))
    return b


def main() -> int:
    pl.run_block = wrapped
    world = World(WorldConfig()); C = world.cfg.n_concepts; h1 = math.log2(C)
    beta, gamma, n = 2.5, 4, 16000
    arms = {"vanilla": dict(policy="none"),
            "free_causal": dict(policy="free_lastp", beta=beta, steer_gate="disagree", steer_mech="posterior"),
            "hint_h1_fresh": dict(policy="oracle_concept_now", beta=beta, steer_gate="disagree", steer_mech="posterior")}
    agg = {}
    for name, kw in arms.items():
        rows = []
        for s in (500, 501):
            LOG["bonus_bits"] = []; LOG["ind_bits"] = []
            res = pl.run_simulation(world, seed=s, n_positions=n, gamma=gamma, **kw)
            m = res.metrics; ne = m.n_emitted
            n_bonus = ne - m.n_proposed
            assert n_bonus == len(LOG["bonus_bits"]), (n_bonus, len(LOG["bonus_bits"]))
            rows.append(dict(
                corr=float(np.sum(res.rejection_bits)) / ne,
                prop_per_emit=m.n_proposed / ne,
                drafted_per_emit=gamma * m.n_blocks / ne,
                analytic_drafted_per_emit=res.analytic_acc_n / ne,
                bonus_per_emit=n_bonus / ne,
                bonus_bits_per_emit=sum(LOG["bonus_bits"]) / ne,
                mean_bonus_bits=float(np.mean(LOG["bonus_bits"])),
                ind_per_emit=sum(LOG["ind_bits"]) / ne,
                hint_paid=h1 * m.n_proposed / ne if name == "hint_h1_fresh" else 0.0,
                hint_drafted=h1 * gamma * m.n_blocks / ne if name == "hint_h1_fresh" else 0.0))
        agg[name] = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
        print(name, {k: round(v, 4) for k, v in agg[name].items()})
    v = agg["vanilla"]
    committed = json.loads((REPO / "results" / "e07_hint_rate.json").read_text(encoding="utf-8"))
    derived = {}
    for name in ("free_causal", "hint_h1_fresh"):
        a = agg[name]
        derived[name] = dict(saved_corr=v["corr"] - a["corr"],
                             d_bonus=a["bonus_bits_per_emit"] - v["bonus_bits_per_emit"],
                             d_ind=a["ind_per_emit"] - v["ind_per_emit"],
                             saved_corr_plus_bonus=(v["corr"] + v["bonus_bits_per_emit"]) - (a["corr"] + a["bonus_bits_per_emit"]),
                             saved_full=(v["corr"] + v["bonus_bits_per_emit"] + v["ind_per_emit"]) - (a["corr"] + a["bonus_bits_per_emit"] + a["ind_per_emit"]),
                             hint_paid=a["hint_paid"], hint_drafted=a["hint_drafted"])
        print(f"{name}: saved_corr {derived[name]['saved_corr']:.4f} d_bonus {derived[name]['d_bonus']:+.4f} "
              f"saved_corr_plus_bonus {derived[name]['saved_corr_plus_bonus']:.4f}")
    failed = []
    for name, (corr, bpe, mbb, bbpe) in PINS.items():
        a = agg[name]
        if abs(a["corr"] - committed["arms"][name]["correction_bits_per_emitted"]["mean"]) >= 5e-5:
            failed.append((name, "corr vs committed", a["corr"]))
        if (round(a["corr"], 4), round(a["bonus_per_emit"], 4), round(a["mean_bonus_bits"], 2), round(a["bonus_bits_per_emit"], 3)) != (corr, bpe, mbb, bbpe):
            failed.append((name, "pins", round(a["corr"], 4), round(a["bonus_per_emit"], 4), round(a["mean_bonus_bits"], 2), round(a["bonus_bits_per_emit"], 3)))
    for name, want in PIN_SAVED.items():
        if round(derived[name]["saved_corr_plus_bonus"], 4) != want:
            failed.append((name, "saved_corr_plus_bonus", round(derived[name]["saved_corr_plus_bonus"], 4)))
    if failed:
        print("PIN MISMATCH:", failed, "| numpy", np.__version__)
        return 1
    out = dict(numpy=np.__version__, arms=agg, derived=derived, committed_arms=committed["arms"])
    (Path(__file__).with_name("e07_ledger_out.json")).write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print("all pins hold; wrote e07_ledger_out.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Recompute the registered E6 conversion gates from COMMITTED evidence (CPU,
seconds): the pairwise tokens-per-verify-call deltas with their bootstrap
CIs, the +0.062 point bar, and the pairwise drafted-per-emitted budget
guard, for every registered verdict population whose summaries are in
results/real/. This is the reproduction surface for the two conversion
nulls (F-19, F-21) and the Stage-A pairs as frozen (F-22's STAGE-A FREEZE;
struck by F-23 except O vs V under a future registration): a stranger with the repo and numpy can re-derive every
headline gate number without the gitignored raws or a GPU.

Estimand (stage-E clarification E6, docs/BLUEPRINT.md): tokens/call =
emitted tokens per verify call (n_blocks), pooled over prompts; delta =
sideband.stats.paired_ratio_delta_ci (joint prompt-cluster bootstrap,
n_boot 2000, seed 0, percentile CI95); budget = drafted / emitted, pooled.
WIN gate (all-hold form): for EVERY registered comparator, CI95 lower > 0
AND point >= BAR AND arm budget <= comparator budget + EPSILON.

  python tools/e6_gate.py                # every population whose files exist
  python tools/e6_gate.py --population k3_s1 --json out.json

Inputs are the per-prompt (n_emitted, n_blocks, n_drafted) rows of the
committed <stem>.summary.json files (their per_prompt_stats). Nothing is
written unless --json is given; results/ is never touched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sideband.stats import paired_ratio_delta_ci  # noqa: E402

REAL = Path(__file__).resolve().parents[1] / "results" / "real"
BAR = 0.062          # docs/ECONOMICS.md S5 materiality bar, tokens per verify call
EPSILON = 0.01       # pairwise budget guard allowance (K-3 arc registration)
N_BOOT, SEED = 2000, 0

# Registered populations: the test arm, its comparators (all must hold),
# and the finding the numbers belong to. Arm names per the arc registrations.
POPULATIONS = {
    "k3_s1": {
        "finding": "F-19 (K-3 Attempt #1, seed 1)",
        "stems": {1: "k3_verdict_s1_arm1", 2: "k3_verdict_s1_arm2",
                  3: "k3_verdict_s1_arm3", 4: "k3_verdict_s1_arm4",
                  5: "k3_verdict_s1_arm5"},
        "names": {1: "vanilla gamma-4", 2: "draft_conf", 3: "probe (a) free",
                  4: "probe (c) telemetry", 5: "fixed gamma-6 control"},
        "test_arm": 4, "comparators": (1, 3, 2),
    },
    "oq15c_s3": {
        "finding": "F-21 (OQ-15 Stage C, seed 3)",
        "stems": {1: "oq15c_verdict_s3_arm1", 2: "oq15c_verdict_s3_arm2",
                  6: "oq15c_verdict_s3_arm6", 7: "oq15c_verdict_s3_arm7"},
        "names": {1: "C1 vanilla gamma-4", 2: "C2 draft_conf",
                  6: "C3 head_free", 7: "C4 head_tel"},
        "test_arm": 7, "comparators": (1, 2, 6),
    },
    "oq16a_s4": {
        "finding": "STAGE-A FREEZE ladder as frozen (F-22 registration); STRUCK by F-23 except arm 8 vs arm 1, live only under a future FREE-ACTUATOR registration",
        "stems": {1: "oq16a_verdict_arm1", 8: "oq16a_verdict_arm8",
                  9: "oq16a_verdict_arm9", 10: "oq16a_verdict_arm10"},
        "names": {1: "V vanilla", 8: "O oracle_h", 9: "F free_inject",
                  10: "T tel_inject"},
        # A0: O vs V; A1: F vs V (free-actuator readout), T vs V and T vs F
        "test_arm": 10, "comparators": (1, 9),
        "extra_pairs": ((8, 1), (9, 1)),
    },
}


def per_prompt(stem: str, root: Path = REAL):
    path = root / f"{stem}.summary.json"
    if not path.exists():
        return None
    pp = sorted(json.load(open(path))["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    return {
        "emitted": np.array([p["n_emitted"] for p in pp], float),
        "blocks": np.array([p["n_blocks"] for p in pp], float),
        "drafted": np.array([p["n_drafted"] for p in pp], float),
        "prompt_idx": [int(p["prompt_idx"]) for p in pp],
        "n_prompts": len(pp),
    }


def pooled(a: dict) -> dict:
    return {"tokens_per_call": float(a["emitted"].sum() / a["blocks"].sum()),
            "drafted_per_emitted": float(a["drafted"].sum() / a["emitted"].sum()),
            "n_prompts": a["n_prompts"]}


def pair(a: dict, b: dict) -> dict:
    """arm a vs comparator b: tokens/call delta with CI, bar, guard."""
    if a["prompt_idx"] != b["prompt_idx"]:
        raise SystemExit("arms are not on the same prompt set — the pairing is void")
    d, lo, hi = paired_ratio_delta_ci(a["emitted"], a["blocks"], b["emitted"], b["blocks"],
                                      n_boot=N_BOOT, seed=SEED)
    pa, pb = pooled(a), pooled(b)
    guard_margin = pb["drafted_per_emitted"] + EPSILON - pa["drafted_per_emitted"]
    return {"delta": d, "ci_lower": lo, "ci_upper": hi,
            "ci_lower_positive": bool(lo > 0.0), "point_at_bar": bool(d >= BAR),
            "budget_guard_margin": guard_margin, "guard_holds": bool(guard_margin >= 0.0),
            "leg_holds": bool(lo > 0.0 and d >= BAR and guard_margin >= 0.0)}


def evaluate(pop_key: str, root: Path = REAL) -> dict | None:
    spec = POPULATIONS[pop_key]
    arms = {k: per_prompt(stem, root) for k, stem in spec["stems"].items()}
    if any(v is None for v in arms.values()):
        return None
    out = {"population": pop_key, "finding": spec["finding"], "bar": BAR,
           "epsilon": EPSILON, "n_boot": N_BOOT, "seed": SEED,
           "arms": {str(k): {"name": spec["names"][k], "stem": spec["stems"][k], **pooled(v)}
                    for k, v in arms.items()},
           "legs": {}}
    t = spec["test_arm"]
    for c in spec["comparators"]:
        out["legs"][f"arm{t}_vs_arm{c}"] = pair(arms[t], arms[c])
    for a, b in spec.get("extra_pairs", ()):
        out["legs"][f"arm{a}_vs_arm{b}"] = pair(arms[a], arms[b])
    gate_legs = [out["legs"][f"arm{t}_vs_arm{c}"] for c in spec["comparators"]]
    out["win"] = all(leg["leg_holds"] for leg in gate_legs)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", choices=sorted(POPULATIONS), default=None)
    ap.add_argument("--data-root", default=str(REAL))
    ap.add_argument("--json", default=None, help="write the readouts here (never results/)")
    args = ap.parse_args()
    root = Path(args.data_root)
    keys = [args.population] if args.population else sorted(POPULATIONS)
    report = {}
    for key in keys:
        res = evaluate(key, root)
        if res is None:
            print(f"[{key}] summaries not present — skipped ({POPULATIONS[key]['finding']})")
            continue
        report[key] = res
        print(f"\n[{key}] {res['finding']}  bar {BAR:+.3f} tokens/call, guard +{EPSILON}")
        for k, a in res["arms"].items():
            print(f"  arm {k:>2} {a['name']:<24} t/c {a['tokens_per_call']:.6f}  "
                  f"drafted/emitted {a['drafted_per_emitted']:.6f}  n={a['n_prompts']}")
        for name, leg in res["legs"].items():
            print(f"  {name:<14} delta {leg['delta']:+.6f} [{leg['ci_lower']:+.6f}, "
                  f"{leg['ci_upper']:+.6f}]  guard margin {leg['budget_guard_margin']:+.4f}  "
                  f"-> {'HOLDS' if leg['leg_holds'] else 'fails'}")
        print(f"  WIN (all-hold): {res['win']}")
    if args.json:
        out = Path(args.json)
        if out.resolve().is_relative_to(REAL.resolve()):
            raise SystemExit("--json must not point into results/ (committed evidence)")
        out.write_text(json.dumps(report, indent=2))
        print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

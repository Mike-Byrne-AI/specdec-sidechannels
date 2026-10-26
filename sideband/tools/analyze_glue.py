#!/usr/bin/env python3
"""OQ-4 validation: re-summarize the COMMITTED Phase 0a rejection records
with the glue exclusion, per the pre-registered K-7 addendum
(docs/WHY_THIS_DIES.md), and evaluate the F-10 reopen trigger.

For each k in {256, 512, 1024}:
  - load results/real/audit_k{k}.jsonl + results/real/glue_k{k}.json;
  - recompute summarize_audit WITH glue: the bucket-level fields must match
    the committed .summary.json exactly (same records, same pinned bootstrap
    seed — a mismatch means code drift and fails the run);
  - report the glue section: token-level concept_cross_fraction with CIs
    (the committed records carry buckets, not residual vectors, so only the
    SAMPLED estimand is recomputable here; the MASS-level decomposition
    comes from the Phase 0b vanilla arm's records via --vanilla-stem).

Trigger (pre-registered): F-10's "K-1 does not fire" is REOPENED iff the
concept-level estimand drops below the original K-1 bar — token-level CI
upper < 0.25 at EVERY k, or mass-level CI upper < 0.25 at k=512. The trigger
firing is a reported scientific outcome, exit code stays 0; only internal
consistency failures exit 1.

Run: python tools/analyze_glue.py [--vanilla-stem results/real/phase0b_vanilla_k512]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.real.hf_specdec import AuditRecord, summarize_audit  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
KS = (256, 512, 1024)
KILL_BAR = 0.25
CAUTION_BAND = (0.15, 0.35)


def _roundtrip(obj):
    """Normalize tuples->lists etc. so recomputed values compare to json."""
    return json.loads(json.dumps(obj))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla-stem", default="results/real/phase0b_vanilla_k512",
                    help="stem of the Phase 0b vanilla arm (its records carry "
                         "residual_mass_glue); skipped gracefully if absent")
    ap.add_argument("--out", default="results/real/glue_phase0a_analysis.json")
    args = ap.parse_args()

    out: dict = {"kill_bar": KILL_BAR, "caution_band": list(CAUTION_BAND), "per_k": {}}
    failures: list[str] = []
    token_upper_below_bar = []

    for k in KS:
        glue_path = REAL / f"glue_k{k}.json"
        if not glue_path.exists():
            failures.append(f"missing {glue_path.name}")
            continue
        glue = json.loads(glue_path.read_text())
        recs = [AuditRecord(**json.loads(l)) for l in (REAL / f"audit_k{k}.jsonl").open()]
        committed = json.loads((REAL / f"audit_k{k}.summary.json").read_text())["audit"]
        s = _roundtrip(summarize_audit(recs, glue_bucket_ids=glue["glue_bucket_ids"]))
        g = s.pop("glue")
        consistent = s == committed
        if not consistent:
            drift = sorted(set(s) ^ set(committed)) or [kk for kk in s if s[kk] != committed.get(kk)]
            failures.append(f"k={k} bucket-level summary drifted from committed: {drift}")
        ci = g["concept_cross_fraction_ci95_prompt_bootstrap"]
        token_upper_below_bar.append(ci is not None and ci[1] < KILL_BAR)
        # Robustness: the token-level estimand under every committed
        # ALTERNATIVE glue set (sensitivity covers + the count-rule set).
        # Token-level only — the stored residual_mass_glue field is specific
        # to the primary set and cannot be rescaled post hoc.
        alt_sets: dict[str, list[int]] = {
            f"cover_{cov}": ids for cov, ids in glue.get("sensitivity", {}).items()
        }
        alt_sets["count_rule_ge5"] = glue.get("diagnostics", {}).get("count_rule_ge5_buckets", [])
        alternatives = {}
        for name, ids in alt_sets.items():
            if not ids or sorted(ids) == sorted(glue["glue_bucket_ids"]):
                continue
            ga = _roundtrip(summarize_audit(recs, glue_bucket_ids=ids))["glue"]
            alternatives[name] = {
                "n_glue_buckets": len(ids),
                "concept_cross_fraction": ga["concept_cross_fraction"],
                "concept_cross_fraction_ci95_prompt_bootstrap":
                    ga["concept_cross_fraction_ci95_prompt_bootstrap"],
            }
        out["per_k"][str(k)] = {
            "alternative_glue_sets": alternatives,
            "n_glue_buckets": len(glue["glue_bucket_ids"]),
            "glue_rule": glue.get("rule"),
            "glue_concentration_flag": glue.get("diagnostics", {}).get("concentration_flag"),
            "bucket_level_matches_committed_summary": consistent,
            "bucket_level_cross_fraction": committed["cross_bucket_fraction"],
            "glue": g,
            "concept_cross_ci_in_caution_band": (
                ci is not None and not (ci[1] < CAUTION_BAND[0] or ci[0] > CAUTION_BAND[1])
            ),
        }

    # Mass-level confirmation from the Phase 0b vanilla arm, once it exists.
    van = Path(args.vanilla_stem + ".summary.json")
    if van.exists():
        vg = json.loads(van.read_text()).get("audit", {}).get("glue")
        out["mass_level_vanilla_k512"] = vg
        mass_ci = (vg or {}).get("residual_mass_concept_other_ci95_prompt_bootstrap")
    else:
        out["mass_level_vanilla_k512"] = None
        mass_ci = None
        out["mass_level_note"] = f"{van.name} not found yet; token-level only"

    # "at EVERY k" must mean every k in KS, not every k that happened to
    # have a glue file — a partial run may never fire the trigger.
    token_trigger = (len(token_upper_below_bar) == len(KS)
                     and all(token_upper_below_bar))
    mass_trigger = mass_ci is not None and mass_ci[1] < KILL_BAR
    out["f10_reopen_trigger"] = {
        "token_level_all_k_upper_below_bar": token_trigger,
        "mass_level_k512_upper_below_bar": mass_trigger if mass_ci is not None else None,
        "fires": token_trigger or mass_trigger,
    }
    out["internal_consistency"] = "PASS" if not failures else f"FAIL: {failures}"

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

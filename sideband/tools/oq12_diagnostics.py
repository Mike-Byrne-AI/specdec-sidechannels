#!/usr/bin/env python3
"""OQ-12 pre-GPU diagnostics: measure the coarse gating space on COMMITTED
evidence before any steered run exists.

For each coarse k (default 16/32/64), entirely from committed artifacts:
  - HEADROOM: re-bucketize the 11,287 committed Phase 0a rejections (token
    ids in audit_k512.jsonl are bucketization-independent) at coarse k and
    compute the concept-cross fraction with cluster CIs, coarse glue
    excluded — the sampled estimand only (residual vectors are not stored,
    so no mass estimand at new k).
  - PERSISTENCE: read the bucket_persistence_k{k}.json produced by
    tools/bucket_persistence.py (run it first for each k).
  - GLUE SHAPE: vocab share of glue, C_concept, concentration flag.

The pre-registered viability rule (docs/BLUEPRINT.md OQ-12 protocol) reads
this file: a coarse C is VIABLE iff the concept-cross CI lower bound >= 0.25
(K-1's bar applied to the coarse space). Persistence and gate expectations
are reported diagnostics, not gates.

Run: python tools/oq12_diagnostics.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.real.hf_specdec import AuditRecord, summarize_audit  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
VIABILITY_BAR = 0.25


def load_bot(k: int) -> np.ndarray:
    data = json.loads((REAL / f"buckets_k{k}.json").read_text())
    bot = np.full(int(data["n_tokens"]), -1, dtype=np.int64)
    for t, b in data["bucket_of_token"].items():
        bot[int(t)] = int(b)
    return bot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ks", type=int, nargs="*", default=[16, 32, 64])
    ap.add_argument("--out", default="results/real/oq12_diagnostics.json")
    args = ap.parse_args()

    base = [json.loads(l) for l in (REAL / "audit_k512.jsonl").open()]
    out: dict = {"viability_bar": VIABILITY_BAR, "n_rejections": len(base), "per_k": {}}
    failures: list[str] = []

    for k in args.ks:
        try:
            bot = load_bot(k)
            glue = json.loads((REAL / f"glue_k{k}.json").read_text())
        except FileNotFoundError as e:
            failures.append(f"k={k}: {e}")
            continue
        gids = glue["glue_bucket_ids"]
        recs = [AuditRecord(prompt_idx=r["prompt_idx"], position=r["position"],
                            offset=r["offset"], proposed=r["proposed"], emitted=r["emitted"],
                            proposed_bucket=int(bot[r["proposed"]]),
                            emitted_bucket=int(bot[r["emitted"]]))
                for r in base]
        s = summarize_audit(recs, glue_bucket_ids=gids)
        g = s["glue"]
        ci = g["concept_cross_fraction_ci95_prompt_bootstrap"]
        pers_path = REAL / f"bucket_persistence_k{k}.json"
        pers = json.loads(pers_path.read_text()) if pers_path.exists() else None
        glue_mask = np.isin(bot, np.array(gids, dtype=np.int64))
        out["per_k"][str(k)] = {
            "C_concept": int(k - len(gids)),
            "n_negative_bucket_records": s["n_negative_bucket_records"],
            "n_glue_buckets": len(gids),
            "glue_vocab_share": float(glue_mask.mean()),
            "glue_generated_share": (pers or {}).get("glue_token_share"),
            "glue_concentration_flag": glue.get("diagnostics", {}).get("concentration_flag"),
            "bucket_level_cross_fraction": s["cross_bucket_fraction"],
            "concept_cross_fraction": g["concept_cross_fraction"],
            "concept_cross_fraction_ci95_prompt_bootstrap": ci,
            "glue_involved_fraction": g["glue_involved_fraction"],
            "persistence_concept_concept": (pers or {}).get(
                "persistence_concept_concept", {}).get("p_same_bucket"),
            "concept_run_length_mean": (pers or {}).get("concept_run_length", {}).get("mean"),
            "VIABLE": bool(ci is not None and ci[0] >= VIABILITY_BAR),
        }

    out["internal"] = "PASS" if not failures else f"FAIL: {failures}"
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

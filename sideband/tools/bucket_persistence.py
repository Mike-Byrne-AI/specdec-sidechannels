#!/usr/bin/env python3
"""Concept-bucket persistence of real generated text (partial OQ-3 answer).

F-4's rule: hold a bucket prediction only while the expected concept run
length is >> gamma. This measures the real quantity at a given k from the
committed Phase 0b vanilla gen log (target-distributed text, F-0/F-1):

  - P(bucket_{t+1} == bucket_t) over consecutive CONCEPT-token pairs
    (both tokens in non-glue buckets; glue tokens break no runs on their
    own row but are also reported in the with-glue frame);
  - run-length distribution over the concept-bucket sequence (glue and
    unbucketed tokens treated as run breakers in the strict frame);
  - the F-4 verdict: expected run length vs gamma.

Run: python tools/bucket_persistence.py [--k 512]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REAL = Path(__file__).resolve().parent.parent / "results" / "real"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=512)
    ap.add_argument("--gen", default="phase0b_vanilla_k512.gen.jsonl")
    ap.add_argument("--gamma", type=int, default=4)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_path = Path(args.out or (REAL / f"bucket_persistence_k{args.k}.json"))

    bdata = json.loads((REAL / f"buckets_k{args.k}.json").read_text())
    n_tokens = int(bdata["n_tokens"])
    bot = np.full(n_tokens, -1, dtype=np.int64)
    for t, b in bdata["bucket_of_token"].items():
        bot[int(t)] = int(b)
    glue = set(json.loads((REAL / f"glue_k{args.k}.json").read_text())["glue_bucket_ids"])

    same_any = n_any = 0        # consecutive pairs, any bucket ids >= 0
    same_cc = n_cc = 0          # consecutive pairs, both in CONCEPT buckets
    runs: list[int] = []        # concept-run lengths (glue/unbucketed break)
    n_rows = n_tok = n_glue_tok = 0
    for line in (REAL / args.gen).open():
        ids = json.loads(line)["generated_ids"]
        n_rows += 1
        n_tok += len(ids)
        bs = bot[np.asarray(ids, dtype=np.int64)]
        is_glue = np.array([b in glue for b in bs.tolist()])
        n_glue_tok += int(is_glue.sum())
        for a, b in zip(bs[:-1], bs[1:]):
            if a >= 0 and b >= 0:
                n_any += 1
                same_any += int(a == b)
        concept = np.where(is_glue | (bs < 0), -1, bs)
        for a, b in zip(concept[:-1], concept[1:]):
            if a >= 0 and b >= 0:
                n_cc += 1
                same_cc += int(a == b)
        run = 0
        prev = -2
        for b in concept.tolist():
            if b >= 0 and b == prev:
                run += 1
            else:
                if run > 0:
                    runs.append(run)
                run = 1 if b >= 0 else 0
            prev = b
        if run > 0:
            runs.append(run)

    runs_arr = np.array(runs, dtype=float)
    exp_run = float(runs_arr.mean()) if len(runs) else float("nan")
    out = {
        "k": args.k,
        "gen_file": args.gen,
        "gamma": args.gamma,
        "n_prompts": n_rows,
        "n_generated_tokens": n_tok,
        "glue_token_share": n_glue_tok / max(1, n_tok),
        "persistence_with_glue_frame": {"n_pairs": n_any, "p_same_bucket": same_any / max(1, n_any)},
        "persistence_concept_concept": {"n_pairs": n_cc, "p_same_bucket": same_cc / max(1, n_cc)},
        "concept_run_length": {
            "n_runs": len(runs),
            "mean": exp_run,
            "p50": float(np.percentile(runs_arr, 50)) if len(runs) else None,
            "p90": float(np.percentile(runs_arr, 90)) if len(runs) else None,
            "max": int(runs_arr.max()) if len(runs) else None,
        },
        "f4_hold_rule": {
            "rule": "hold a bucket only while expected run length >> gamma",
            "expected_run_length": exp_run,
            "gamma": args.gamma,
            "verdict": ("FAILS — holding a fine-bucket prediction for a block is unjustified"
                        if exp_run < args.gamma else "passes"),
        },
    }
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

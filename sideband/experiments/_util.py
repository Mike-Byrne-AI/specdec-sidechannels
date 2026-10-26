"""Shared experiment plumbing: seeded runs, json results, tiny stats."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS_ROOT = RESULTS


def smoke_results() -> Path:
    """Route every save_json() of this process to results/smoke/ (gitignored) and return it.

    Dated note 2026-10-16 (lane C of the 2026-10-15 image audit, item S8-C-7): until this
    function existed only run_all.py redirected under --smoke, by reassigning RESULTS itself,
    and a script run on its own (python experiments/e04_staleness_decay.py --smoke) wrote its
    smoke-sized payload over the committed results/ file. Every script's main block now calls
    this under --smoke; run_all.py calls it too; the call is idempotent (the smoke directory
    never nests). tests/test_experiments_smoke.py holds the structural and the end-to-end check.
    """
    global RESULTS
    RESULTS = RESULTS_ROOT / "smoke"
    return RESULTS


def save_json(name: str, payload: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    payload = {"_experiment": name, "_written_unix": int(time.time()), **payload}
    # LF on every OS (2026-10-16): a text-mode write without newline= produced CRLF on Windows, so the
    # bytes depended on the writing box. e01 and e07 are stored CRLF today and flip when next regenerated
    # (none of the seven payloads is sha-cited; the evidence-bytes checks report the change)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(f"[saved] {path}")
    return path


def mean_std(xs) -> dict:
    a = np.asarray(list(xs), dtype=float)
    return {"mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0, "n": len(a)}


class Timer:
    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *_):
        self.seconds = time.time() - self.t0

"""Vector coverage of the adaptive model's rescale clause (cold read of 2026-10-18).

Replays the six lsp0 conformance vectors through AdaptiveByteModel and records the largest
row total any context reaches, against the model's RESCALE_LIMIT; then re-encodes each
adaptive-model vector with the rescale disabled (the limit raised beyond reach) and compares
the payload digest with the vector's committed one. If no vector reaches the limit, a coder
with no rescale clause passes the five adaptive-model vectors (the uniform sixth has no such
clause), and the vectors say nothing about that clause. Before the replay, a self-test feeds
the probe a synthetic row long enough to cross the limit and asserts that the probe sees the
rescale fire, so the pinned "no rescale fired" below rests on a probe that can detect one.

Reads: src/lockstep/data/vectors_v0.json through lockstep.conformance (load_vectors, materialize_input).
Writes nothing. Run from the repository root:
    python docs/audits/2026-10-18-image-audit/vector_coverage.py
Exit 0 when the printed figures equal EXPECTED (pinned after the first run of 2026-10-18 and
asserted on every run since); exit 1 otherwise.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from lockstep.codec import encode_bytes  # noqa: E402
from lockstep.conformance import load_vectors, materialize_input  # noqa: E402
from lockstep.models import AdaptiveByteModel, make_model  # noqa: E402

EXPECTED: dict | None = {   # pinned 2026-10-18 from the first run's print; see the module docstring
    "rescale_limit": 32768,
    "cases": {
        "empty": {"model": "adaptive-order1", "n_bytes": 0, "payload_matches": True, "max_total": 0,
                  "rescale_fired": False, "payload_matches_without_rescale": True},
        "hello": {"model": "adaptive-order1", "n_bytes": 744, "payload_matches": True, "max_total": 3712,
                  "rescale_fired": False, "payload_matches_without_rescale": True},
        "byte_ramp_x4": {"model": "adaptive-order1", "n_bytes": 1024, "payload_matches": True, "max_total": 376,
                         "rescale_fired": False, "payload_matches_without_rescale": True},
        "drbg_1k": {"model": "adaptive-order1", "n_bytes": 1024, "payload_matches": True, "max_total": 520,
                    "rescale_fired": False, "payload_matches_without_rescale": True},
        "drbg_4k": {"model": "adaptive-order1", "n_bytes": 4096, "payload_matches": True, "max_total": 952,
                    "rescale_fired": False, "payload_matches_without_rescale": True},
        "uniform_1k": {"model": "uniform", "n_bytes": 1024},
    },
    "max_total_over_adaptive_vectors": 3712,
    "any_rescale_fired": False,
    "all_adaptive_match_without_rescale": True,
}


class ProbeModel(AdaptiveByteModel):
    """AdaptiveByteModel that records the peak row total offered to the rescale test."""

    def __init__(self) -> None:
        super().__init__()
        self.max_total = 0
        self.rescales = 0

    def update(self, symbol: int) -> None:
        context = self._context
        before = self._row(context)[1]
        super().update(symbol)
        peak = before + self.INCREMENT          # the value `total > RESCALE_LIMIT` is tested against
        self.max_total = max(self.max_total, peak)
        if self._rows[context][1] < peak:       # the total dropped: the rescale fired
            self.rescales += 1


def _self_test() -> None:
    """A row of one repeated byte crosses RESCALE_LIMIT: the probe must see the peak and the rescale."""
    probe = ProbeModel()
    n = (AdaptiveByteModel.RESCALE_LIMIT // AdaptiveByteModel.INCREMENT) + 2
    for _ in range(n):
        probe.update(0)
    assert probe.max_total > AdaptiveByteModel.RESCALE_LIMIT, probe.max_total
    assert probe.rescales >= 1, probe.rescales


def main() -> int:
    _self_test()
    spec = load_vectors()
    cases = spec["cases"] if isinstance(spec, dict) else spec
    limit = AdaptiveByteModel.RESCALE_LIMIT
    out: dict = {"rescale_limit": limit, "cases": {}}
    for case in cases:
        data = materialize_input(case["input"])
        row: dict = {"model": case["model"], "n_bytes": len(data)}
        if case["model"] == "adaptive-order1":
            probe = ProbeModel()
            payload = encode_bytes(data, probe)
            row["payload_matches"] = hashlib.sha256(payload).hexdigest() == case["payload_sha256"]
            row["max_total"] = probe.max_total
            row["rescale_fired"] = probe.rescales > 0
            saved = AdaptiveByteModel.RESCALE_LIMIT
            try:
                AdaptiveByteModel.RESCALE_LIMIT = 1 << 62   # a coder with no rescale clause
                no_rescale = encode_bytes(data, make_model(case["model"]))
            finally:
                AdaptiveByteModel.RESCALE_LIMIT = saved
            row["payload_matches_without_rescale"] = hashlib.sha256(no_rescale).hexdigest() == case["payload_sha256"]
        out["cases"][case["name"]] = row
    adaptive = [r for r in out["cases"].values() if r["model"] == "adaptive-order1"]
    out["max_total_over_adaptive_vectors"] = max(r["max_total"] for r in adaptive)
    out["any_rescale_fired"] = any(r["rescale_fired"] for r in adaptive)
    out["all_adaptive_match_without_rescale"] = all(r["payload_matches_without_rescale"] for r in adaptive)
    for k, v in out.items():
        if k != "cases":
            print(f"{k}: {v}")
    for name, row in out["cases"].items():
        print(f"  {name}: {row}")
    if EXPECTED is not None and out != EXPECTED:
        print("MISMATCH against the pinned EXPECTED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

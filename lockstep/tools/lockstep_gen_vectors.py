#!/usr/bin/env python3
"""Generate or verify the mirrored ``lsp0`` conformance vector files.

Regenerating vectors is a profile-format event. ``--check`` is the safe CI
mode; ``--write`` updates both the repository-visible and packaged copies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lockstep.codec import encode_bytes  # noqa: E402
from lockstep.conformance import (  # noqa: E402
    VECTORS_V0_SHA256,
    materialize_input,
)
from lockstep.models import make_model  # noqa: E402

CASES = [
    {"name": "empty", "model": "adaptive-order1",
     "input": {"kind": "literal-utf8", "text": ""}},
    {"name": "hello", "model": "adaptive-order1",
     "input": {"kind": "literal-utf8", "text": "Deterministic decode, forever. " * 24}},
    {"name": "byte_ramp_x4", "model": "adaptive-order1",
     "input": {"kind": "byte-ramp", "repeat": 4}},
    {"name": "drbg_1k", "model": "adaptive-order1",
     "input": {"kind": "drbg", "seed": "lockstep-lsp0-1k", "n": 1024}},
    {"name": "drbg_4k", "model": "adaptive-order1",
     "input": {"kind": "drbg", "seed": "lockstep-lsp0-4k", "n": 4096}},
    {"name": "uniform_1k", "model": "uniform",
     "input": {"kind": "drbg", "seed": "lockstep-lsp0-uni", "n": 1024}},
]

TARGETS = [
    ROOT / "conformance" / "vectors_v0.json",
    ROOT / "src" / "lockstep" / "data" / "vectors_v0.json",
]


def generate_text() -> str:
    cases = []
    for case in CASES:
        data = materialize_input(case["input"])
        payload = encode_bytes(data, make_model(case["model"]))
        cases.append({
            **case,
            "n_bytes": len(data),
            "original_sha256": hashlib.sha256(data).hexdigest(),
            "payload_size": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
        })
    spec = {
        "format": "lockstep-conformance",
        "version": 0,
        "profile": "lsp0",
        "cases": cases,
    }
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="rewrite both vector copies")
    mode.add_argument("--check", action="store_true", help="fail if either copy differs")
    args = parser.parse_args(argv)

    text = generate_text()
    generated_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if generated_digest != VECTORS_V0_SHA256:
        print(
            "generated vector digest differs from the pin in "
            "lockstep.conformance.VECTORS_V0_SHA256; update it only as an explicit "
            "vector-governance change",
            file=sys.stderr,
        )
        return 1
    if args.write:
        for path in TARGETS:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path} ({len(CASES)} cases)")
        return 0
    if args.check:
        mismatches = []
        for path in TARGETS:
            try:
                actual = path.read_text(encoding="utf-8")
            except OSError:
                actual = None
            if actual != text:
                mismatches.append(path)
        if mismatches:
            for path in mismatches:
                print(f"vector mismatch: {path}", file=sys.stderr)
            return 1
        print(f"OK: {len(TARGETS)} vector copies match generated lsp0 data")
        return 0
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared fixtures for the landing tests (added 2026-10-15, lane A, CI portability).

phase3_data_root (session scope): a data root in which the committed reader-lens payloads' recorded Phase-3
paths resolve by the frozen tool's own rule. tools/run_reader_lens.py (frozen 2026-10-05, sha12 d1125670be05)
locates the Phase-3 state file and payload as ``data_root / Path(recorded).name`` (its lines 1050-1051 and
1067), where ``recorded`` is ``provenance.args.phase3_state`` / ``phase3_payload`` of a lens, readers or
readers_long payload. The committed payloads record the writing box's absolute Windows paths, so on POSIX
``Path(recorded).name`` is the whole recorded string and the lookup under results/real misses: the three F-28
landing tests were red on Linux (pre-publication audit, 2026-10-15). The fixture copies each referenced file
from results/real into a tmp root under the name the running OS computes from the recorded string (the
basename on Windows, the whole string on POSIX), after checking its sha256 against the one the payload's
provenance records (``phase3_state_sha256`` / ``phase3_payload_sha256``), so a copy can never stand in for
drifted bytes; the landing tests pass that root as ``conclude_from``'s ``data_root``. The frozen tool and the
committed evidence are not touched; nothing is written under results/; the payloads themselves, and the lens
payloads a readers conclusion admits against, stay the originals under results/real. Dated 2026-10-17: the S1 pair
(readers_s1.json, readers_s1_r.json) joined the list for tests/test_reader_s1_landing.py, and the two committed F-24
twin payloads are copied by basename because tools/run_reader_s1.pairing_checks reads them under data_root."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path, PureWindowsPath

import pytest

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "results" / "real"
READER_LENS_PAYLOADS = ("lens_s3.json", "lens_s3_r.json", "readers_s3.json", "readers_s3_r.json",
                        "readers_long_s3.json", "readers_long_s3_r.json",
                        "readers_s1.json", "readers_s1_r.json")            # the S1 pair, added 2026-10-17 (F-29's landing test)
S1_PAIRING_COMPANIONS = ("fullfree_s1_twin.json", "fullfree_s1_r_twin.json")   # read by tools/run_reader_s1.pairing_checks under data_root


@pytest.fixture(scope="session")
def phase3_data_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("phase3_data_root")
    for name in READER_LENS_PAYLOADS:
        payload = REAL / name
        if not payload.exists():
            continue                                              # an absent payload is the landing tests' own concern
        prov = json.loads(payload.read_text(encoding="utf-8"))["provenance"]
        for key in ("phase3_state", "phase3_payload"):
            recorded = str(prov["args"][key])
            src = REAL / PureWindowsPath(recorded).name          # the committed file, by its basename on any OS
            assert src.exists(), f"{name}: its recorded {key} {src.name} is not under results/real"
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            assert sha == prov[f"{key}_sha256"], f"{name}: {src.name} differs from the sha256 its provenance records"
            dst = root / Path(recorded).name                      # the name the frozen lookup computes on this OS
            if not dst.exists():
                shutil.copyfile(src, dst)
    for name in S1_PAIRING_COMPANIONS:                          # committed F-24 twin payloads; the check is descriptive
        src = REAL / name
        if src.exists() and not (root / name).exists():
            shutil.copyfile(src, root / name)
    return root

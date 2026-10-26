"""tests/test_frozen_imports_pinned.py — the two frozen modules that later instruments import by bare
name, tools/run_probes.py and tools/run_posthoc_topic.py, are byte-pinned here.

Written 2026-10-18 after the cold read of that date (docs/PUBLIC_CUT_PLAN.md 15.8): the harness  # [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
reviewer mutated both files and the evidence-bytes and doc-claims tests stayed green, because the
seventeen-file frozen closure (pyproject's ruff extend-exclude; tests/test_harness_doc_claims.py)
holds the LIST of frozen files and the fourteen payload-attested instruments hold their own bytes,
while these two sit in the closure only by import (CLAUDE.md, the frozen-instrument rule) and no
payload records their sha. tests/test_fullfree_landing.py pins tools/run_fullfree.py the same way.

What each pin attests. Both files last changed at 8542ef5 (2026-09-05, the release audit: the
provenance block's `args` passed through sideband.provenance.redact_args, one import and one line
each; `git log -1 -- <file>` prints that commit). Every frozen instrument that imports them and
was frozen on or after 2026-09-06 imported these bytes: run_fullfree.py (1d1a7f8), run_fullfree_twin.py
(675a8f6), run_fullfree_coarse.py (15c4e9c), run_oq18_rider_poscontrol.py (5ef3ccf),
run_fullfree_coarse_amended.py and run_oq18_rider_diag.py (0eb73d9), run_reader_lens.py (b128fda),
and run_posthoc_topic.py itself imports run_probes.py. The pins do NOT reach back before 8542ef5:
the Phase-3 probe payloads behind K-2 (F-15, F-17; 2026-08-30 to 2026-09-01) and the F-16 and F-18
posthoc-topic payloads were produced by the earlier blobs (9ca4308 to 3eb5efd; 1a54fb7 and 6cf7e1e), of which the
last before 8542ef5 (3eb5efd; 6cf7e1e) differs from these by that one provenance line and the
earlier ones by more (`git diff --stat 9ca4308 HEAD -- tools/run_probes.py`, and 1a54fb7 for
the other), and tools/export_probe_weights.py (last changed 69cb8f2,
2026-09-02, not a frozen instrument) imported an earlier blob too. The digests are the sha256 of
each file with CRLF folded to LF, pasted from `git show HEAD:<file>` hashed the same way on
2026-10-18; both blobs are stored LF, so the LF digest is the blob's content digest. Nothing here
imports torch."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# (file, last-change commit, sha256 of the LF-folded bytes)
PINNED = {
    "tools/run_probes.py": ("8542ef5", "14817bffbeaa8e1c4a5facbd8e3761dcb14daf4eaed727f2585513f56658f7e7"),
    "tools/run_posthoc_topic.py": ("8542ef5", "2f447eeca940b34177fd111792cd5a9a209f3a565fa88e98ed75e949a639dadb"),
}


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.mark.parametrize("rel", sorted(PINNED))
def test_frozen_import_on_disk_is_the_pinned_one(rel):
    _, digest = PINNED[rel]
    assert _sha_lf(ROOT / rel) == digest, f"{rel} differs from the bytes pinned on 2026-10-18 (last change 8542ef5)"


def test_both_pinned_files_are_in_the_frozen_closure():
    """The pin and the closure name the same two files: both sit in pyproject's ruff `extend-exclude`
    array, the frozen closure tests/test_harness_doc_claims.py derives from the payloads (the array is
    read with the same regular expression that test uses, so no TOML parser is needed)."""
    import re
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"extend-exclude\s*=\s*\[(.*?)\]", text, flags=re.S)
    assert block is not None, "pyproject.toml has no ruff extend-exclude array"
    excluded = set(re.findall(r'"([^"]+)"', block.group(1)))
    for rel in PINNED:
        assert rel in excluded, f"{rel} is not in pyproject's ruff extend-exclude (the frozen closure)"

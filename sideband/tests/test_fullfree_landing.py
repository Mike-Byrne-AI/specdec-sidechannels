"""tests/test_fullfree_landing.py — the committed OQ-17 full-free payloads (F-24) reproduce
their landed labels through the frozen instrument's own conclude(), their provenance is the
registered run's, and the instrument on disk is the frozen one.

Landing test written 2026-10-16 (lane C of the 2026-10-15 image audit, item S7a-C-1), forty days
after the runs were read on 2026-09-06: tests/test_fullfree.py accepted any label from the
committed payloads, and tools/run_fullfree.py's bytes were attested by no payload (the twin
payloads cite the fullfree payload and state shas, not the instrument's). The labels here are
pinned as F-24 landed them, with the cell counts and the one dirty stamp as the payloads record
them; the gate rows and D rows are read back from the payloads and held to the registered rule.
The payload's own rows are what conclude() reads; the state-to-payload leg is held by the twin
recompute in tests/test_fullfree_twin.py (the twin payloads cite the fullfree payload and state
digests) and by check 6 of tests/test_evidence_bytes.py. INSTRUMENT_SHA256 is the sha256 of
tools/run_fullfree.py with CRLF folded to LF, equal to the blob at the freeze commit 1d1a7f8
(`git show 1d1a7f8:tools/run_fullfree.py`, checked when this file was written); the file has not
changed since (`git log -1 -- tools/run_fullfree.py` prints that commit). Nothing here imports
torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_fullfree as rf  # noqa: E402

# the freeze commit (docs/BLUEPRINT.md, OQ-17 FULL-FREE EXISTENCE RE-TEST REGISTRATION) and the
# instrument it froze; every registered run records this commit, three with a clean tracked tree and
# the S3 replication with a -dirty stamp (DIRTY below)
FREEZE_COMMIT = "1d1a7f81219bdeb35cd0f2b3579489409a3625f1"
INSTRUMENT_SHA256 = "059892b4c064ac19c054f1d8203418858510766664906b9e65bd2f5a32ec202a"
# the labels read on 2026-09-06 (F-24): ABSORBED at both sources, OFF3-ABSORBED at the horizon,
# the gate not firing on either harvest, the reader valid, every D CI95 upper below the floor
LANDED = {
    ("fullfree_s1.json", "fullfree_s1_r.json"): {"harvest": "harvest_shadow", "n_cells": 27, "horizon": "OFF3-ABSORBED",
                                                 "space": "L1_concept_k16"},
    ("fullfree_s3.json", "fullfree_s3_r.json"): {"harvest": "harvest_moe", "n_cells": 18, "horizon": None,
                                                 "space": "L1_olmoe_k16"},
}
LANDED_LABEL = rf.LABEL_ABSORBED
# the one payload written from a tree with tracked modifications, as its provenance block records them:
# F-24 says the dirt was "the twin-diagnostic registration written while that run was in flight; tools/,
# src/ and tests/ unchanged against HEAD" (docs/BLUEPRINT.md's twin block says the same)
DIRTY = {"fullfree_s3_r.json": "-dirty"}
DIRTY_TRACKED = {"fullfree_s3_r.json": [" M .gitignore", " M OPEN_QUESTIONS.md", " M docs/BLUEPRINT.md"]}


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_instrument_on_disk_is_the_frozen_one():
    assert _sha_lf(ROOT / "tools" / "run_fullfree.py") == INSTRUMENT_SHA256


@pytest.mark.parametrize("pair", sorted(LANDED))
def test_committed_fullfree_payloads_reproduce_their_landed_label(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("registered OQ-17 payloads not present")
    pp, rp = (json.loads(p.read_text(encoding="utf-8")) for p in paths)
    want = LANDED[pair]
    for d, name in ((pp, pair[0]), (rp, pair[1])):
        prov = d["provenance"]
        # a registered run, never a smoke: the registered harvest, the full cell grid, the freeze commit.
        # Three payloads record a clean tracked tree; the S3 replication records the freeze commit with
        # a -dirty stamp and the three files F-24 names (the twin-diagnostic registration in flight;
        # .gitignore among them for the state file's negation line). Pinned as recorded.
        assert prov["git_commit"] == FREEZE_COMMIT + DIRTY.get(name, "")
        assert prov["git_status_tracked"] == DIRTY_TRACKED.get(name, [])
        assert prov["args"]["only"] is None and prov["args"]["conclude_from"] is None
        assert prov["args"]["harvest"].replace("\\", "/").endswith("results/real/" + want["harvest"] + ("_r" if name.endswith("_r.json") else ""))
        assert prov["args"]["out"].replace("\\", "/").endswith("results/real/" + name)
        assert d["partial"] is False and d["n_cells"] == want["n_cells"] and d["resumed_cells"] == 0
        assert d["registered"] and d["reader_valid"]["ok"] is True
        assert d["rider"]["pass"] and d["rider"]["leg1_pass"] and d["rider"]["leg2_pass"]
        # the gate row is the registered cell, read back from the payload and held to the rule
        gate = d["gate"]
        assert (gate["space"], gate["offset"], gate["capacity"]) == (want["space"], rf.GATE_OFFSET, rf.GATE_CAPACITY)
        assert gate["row"]["pair"] == rf.GATE_PAIR and gate["fires"] is False
        assert gate["fires"] == rf.gate_fires(gate["row"])
        # every D row (both harvests, every registered cell) has its CI95 upper below the materiality
        # floor; the cells are the registered grid: offset 2 at both capacities, offset 3 (the horizon,
        # concept tag only) at the gate capacity
        rows = d["d_fplus_b_vs_fplus_n"]
        assert d["offsets"] == list(rf.OFFSETS_OF_TAG[prov["args"]["space_tag"]])
        want_cells = {(off, cap) for off in d["offsets"] for cap in ("linear", rf.GATE_CAPACITY)
                      if not (off != rf.GATE_OFFSET and cap == "linear")}
        assert {(r["offset"], r["capacity"]) for r in rows} == want_cells and len(rows) == len(want_cells)
        for r in rows:
            assert r["n_seeds"] == len(rf.SEEDS) and r["n_clusters"] == 30
            assert r["ci95"][0] <= r["margin"] <= r["ci95"][1]
            assert r["ci95"][1] < rf.MATERIALITY, (name, r["offset"], r["ci95"])
    out = rf.conclude(pp, rp)
    assert out["label"] == LANDED_LABEL
    assert out["horizon_off3"] == LANDED[pair]["horizon"]
    assert out["gate_fires"] == {"primary": False, "replication": False}
    assert out["all_d_ci_uppers_below_floor"] is True
    assert out["reader_valid"] == {"primary": True, "replication": True}
    assert out["materiality_floor"] == rf.MATERIALITY
    assert out["space"] == LANDED[pair]["space"]

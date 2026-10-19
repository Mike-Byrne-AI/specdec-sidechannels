"""tests/test_prefetch_strat_landing.py — the committed stratified-coverage-read payloads (the
2026-10-01 amendment to the free-bigram twin; F-26's second dated status line) reproduce their
own conclusion through the instrument's exact recompute surface, incl. the REPRODUCE check
against the committed twin state files; the instrument on disk is the one both payloads
attest; the frozen twin and its parent are still frozen.

Landing test written 2026-10-02 after both registered runs were read; it pins the labels as
landed so that a changed payload, state file, twin file or instrument flags here. Missing
evidence FAILS, never skips. Nothing in this file imports torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import run_prefetch_strat as rs  # noqa: E402
import run_prefetch_bigram as rb  # noqa: E402
import run_prefetch_readouts as pr  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402

# the freeze commit and the instrument it froze (both payloads' provenance; the amendment block's OUTCOME)
FREEZE_COMMIT = "fea243157df63bb88c54f123d43c94d42d42765a"
INSTRUMENT_SHA256 = "39a6cd587492e13d66da47ce75df0ec17ffe2ab57c3ee0ae760f4c574e110e0c"
# the labels read on 2026-10-02 through --conclude-from on both harvests (F-26's second dated status line)
LANDED = {
    "prefetch_strat_s3.json": {"seeds": [0, 1, 2, 3, 4, 5, 6, 7], "harvest": "harvest_moe",
                               "twin": "prefetch_bigram_s3.json", "label": "FALLBACK-LOCATED / PT-SURVIVES", "q1": "FALLBACK-LOCATED", "q2": "PT-SURVIVES",
                               "encoding": "prev_table", "reproduce": "EXACT",
                               # covered, fallback, d_eq_pt, d_add_pt, q2 straddles; covered negative
                               "flags": (True, False, True, False, True, False)},
    "prefetch_strat_s3_r.json": {"seeds": [8, 9, 10, 11], "harvest": "harvest_moe_r",
                                 "twin": "prefetch_bigram_s3_r.json", "label": "FALLBACK-LOCATED / PT-SURVIVES", "q1": "FALLBACK-LOCATED", "q2": "PT-SURVIVES",
                                 "encoding": "prev_table", "reproduce": "EXACT",
                                 "flags": (True, False, True, False, True, False)},
}


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_instrument_on_disk_is_the_attested_one_and_its_parents_are_frozen():
    assert _sha_lf(ROOT / "tools" / "run_prefetch_strat.py") == INSTRUMENT_SHA256
    assert rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_strat_payloads_reproduce_their_conclusion(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    # committed evidence: absent is a failure, not a skip
    assert path.exists() and state.exists(), f"committed stratified-read evidence missing: {name}"
    want = LANDED[name]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == rs.REGISTERED
    prov = payload["provenance"]
    # a registered run, never a smoke: full seeds, the registered grid, a clean tree at the freeze commit
    assert prov["smoke"] is False and prov["smoke_split_val"] is False
    assert prov["args"]["only_seeds"] is None and prov["args"]["lambdas"] is None and prov["args"]["twin"] is None
    assert sorted(prov["seeds"]) == want["seeds"] and Path(prov["harvest_dir"]).name == want["harvest"]
    assert prov["git_commit"] == FREEZE_COMMIT and prov["git_status_tracked"] == []
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["frozen_twin"]["sha256_lf"] == rs.TWIN_INSTRUMENT_SHA256
    assert prov["frozen_instrument"]["sha256_lf"] == rb.FROZEN_INSTRUMENT_SHA256
    assert prov["n_test_prompts"] == 30 and prov["constants"]["lambdas"] == list(rs.LAMBDAS)
    assert prov["constants"]["n_boot"] == rs.N_BOOT and prov["constants"]["boot_seed"] == rs.BOOT_SEED
    assert prov["constants"]["strata"] == list(rs.STRATA) and prov["encoding_selected"] == want["encoding"]
    assert prov["encoding_source"] == "twin" and all(prov["lambda_source"][a] == "twin" for a in rs.ARMS_TWIN)
    # the committed twin this run took its encoding, lambdas and rows from is the committed twin as it stands
    tw = prov["twin"]
    tpath, tstate = ROOT / tw["path"], ROOT / tw["state_path"]
    assert tpath.name == want["twin"] and tw["instrument_sha256"] == rs.TWIN_INSTRUMENT_SHA256
    assert hashlib.sha256(tpath.read_bytes()).hexdigest() == tw["sha256"]
    assert hashlib.sha256(tstate.read_bytes()).hexdigest() == tw["state_sha256"]
    twin_payload = json.loads(tpath.read_text(encoding="utf-8"))
    assert twin_payload["provenance"]["encoding_selected"] == tw["encoding"] == want["encoding"]
    for arm in rs.ARMS_TWIN:
        assert float(twin_payload["provenance"]["lambda_selected"][arm]) == prov["lambda_selected"][arm]
    assert twin_payload["conclusion"]["deltas"][f"gate_eq|B={rs.LABEL_BUDGET}"] == tw["gate_eq"]
    # the state file is bound to the harvest, carries the twin record, and holds only TEST prompts in the six strata
    header, rows = pr.load_state(state)
    assert header["harvest_npz_sha256"] == prov["harvest_npz_sha256"] == tw["harvest_npz_sha256"]
    assert header["encoding"] == want["encoding"] and header["twin"] == tw and header["lambda_selected"] == prov["lambda_selected"]
    hdir = ROOT / "results" / "real" / want["harvest"]
    assert len(header["harvest_npz_sha256"]) == len(want["seeds"])
    for shard, sha in header["harvest_npz_sha256"].items():
        meta = json.loads((hdir / shard.replace(".npz", ".meta.json")).read_text(encoding="utf-8"))
        assert meta["npz_sha256"] == sha, shard
    assert len(rows) == payload["n_state_rows"]
    prompts = {int(r["prompt_idx"]) for r in rows}
    assert len(prompts) == 30 and all(split_of_prompt(p) == "test" for p in prompts)
    assert {r["arm"] for r in rows} == set(rs.ARMS_REQUIRED) and {r["stratum"] for r in rows} <= set(rs.STRATA)
    # REPRODUCE against the committed twin rows, re-derived here from the files, not read from the payload
    _, twin_rows = pr.load_state(tstate)
    rep = rs.reproduce_check(rows, twin_rows)
    assert rep["status"] == want["reproduce"] and rep["needed_mismatch_rows"] == 0
    # exact recompute under the numpy that ran the instrument; labels only under another numpy
    # (the bootstrap CIs come from numpy's Generator, whose streams are not version-stable)
    if np.__version__ == prov["numpy_version"]:
        got = rs.conclude_from(path)
    else:
        got = rs.conclude(rows, header["encoding"], twin_rows, tw["gate_eq"])
    lab = got["labels"]
    assert lab["label"] == want["label"] and lab["q1"] == want["q1"] and lab["q2"] == want["q2"]
    assert lab["reproduce_status"] == want["reproduce"] and lab["reproduce_ok"] is True and lab["void"] is False
    assert lab["all_gate_eq_matches_twin"] is True
    assert lab["missing_arms"] == [] and lab["missing_label_cells"] == []
    # the straddle flags as landed (both gates straddle the floor on both harvests; the branch readings do not)
    assert (lab["covered_floor_straddle"], lab["fallback_floor_straddle"], lab["d_eq_pt_floor_straddle"],
            lab["d_add_pt_floor_straddle"], lab["q2_floor_straddle"], lab["covered_negative"]) == want["flags"]
    assert lab["pt_inconsistent_cause"] is None
    # the sentence is the pinned composition for those flags
    expect_q1 = rs.SENTENCES_Q1[(want["q1"], lab["covered_floor_straddle"])]
    if lab["covered_negative"]:
        expect_q1 = f"the address block reads below the equal-dims free bigram block on {rs._COV} (NEGATIVE); " + expect_q1
    if lab["fallback_floor_straddle"]:
        expect_q1 += rs._FB_STRADDLE
    assert lab["sentence"] == expect_q1 + "; " + rs.SENTENCES_Q2[(want["q2"], lab["q2_floor_straddle"])]
    assert "not settled at this power" in lab["sentence"] and "indicated, not settled" in lab["sentence"]

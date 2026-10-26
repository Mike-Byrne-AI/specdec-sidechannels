"""tests/test_prefetch_r2_landing.py — the committed generalising-free-baseline (R2) payloads (the 2026-10-02
amendment to the stratified coverage read; F-26's third dated status line) reproduce their own conclusion through
the instrument's exact recompute surface, incl. the REPRODUCE check against the committed stratified state files;
the instrument on disk is the one both payloads attest; the frozen chain is still frozen; the replay source is the
pinned checkpoint, and where the Hugging Face cache holds it the eight probe vectors recompute to their recorded shas.

Landing test written 2026-10-03 after both registered runs were read; it pins the labels as landed so that a
changed payload, state file, stratified file, tool or instrument flags here. Missing committed evidence FAILS,
never skips; only the cache-dependent probe check skips, and says so. Nothing in this file imports torch."""
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
import run_prefetch_r2 as r2  # noqa: E402
import run_prefetch_strat as rs  # noqa: E402
import run_prefetch_bigram as rb  # noqa: E402
import run_prefetch_readouts as pr  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402

# the freeze commit and the instrument it froze (both payloads' provenance; the block's FINAL RE-READ paragraph)
FREEZE_COMMIT = "2fe5926ce054bac1bb5f812a406372dcc64b05f1"
INSTRUMENT_SHA256 = "eaf671fdb9d637624c012b5555a06d1a7ff82072d09829c1d31c3aa492231a84"
# the labels read on 2026-10-03 through --conclude-from on both harvests (F-26's third dated status line)
LANDED = {
    "prefetch_r2_s3.json": {"seeds": [0, 1, 2, 3, 4, 5, 6, 7], "harvest": "harvest_moe", "strat": "prefetch_strat_s3.json",
                            "label": "R2-FALLBACK-SURVIVES / H-ABSORBS", "q1": "R2-FALLBACK-SURVIVES", "q2": "H-ABSORBS",
                            "k": "128", "all_reading": "NOT-SHOWN"},
    "prefetch_r2_s3_r.json": {"seeds": [8, 9, 10, 11], "harvest": "harvest_moe_r", "strat": "prefetch_strat_s3_r.json",
                              "label": "R2-FALLBACK-SURVIVES / H-ABSORBS", "q1": "R2-FALLBACK-SURVIVES", "q2": "H-ABSORBS",
                              "k": "128", "all_reading": "SIGNAL"},
}
# flags as landed, the same on both harvests: fallback straddle, all straddle, d_eq_h straddle, d_add_h straddle, q2 straddle,
# fallback negative, all negative, h negative, reader guard, address handicap, k at the replay end
FLAGS = (False, True, False, False, False, False, False, False, False, False, False)


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_instrument_on_disk_is_the_attested_one_and_the_chain_is_frozen():
    assert _sha_lf(ROOT / "tools" / "run_prefetch_r2.py") == INSTRUMENT_SHA256
    assert r2.assert_frozen_strat() == r2.STRAT_INSTRUMENT_SHA256
    assert rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_r2_payloads_reproduce_their_conclusion(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed R2 evidence missing: {name}"       # absent is a failure, not a skip
    want = LANDED[name]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == r2.REGISTERED
    prov = payload["provenance"]
    # a registered run, never a smoke: full seeds, the registered grids, a clean tree at the freeze commit, the pinned source
    assert prov["smoke"] is False and prov["smoke_split_val"] is False
    assert prov["args"]["only_seeds"] is None and prov["args"]["lambdas"] is None and prov["args"]["k_grid"] is None
    assert prov["args"]["strat"] is None and prov["args"]["replay"] == "hf"
    assert sorted(prov["seeds"]) == want["seeds"] and Path(prov["harvest_dir"]).name == want["harvest"]
    assert prov["git_commit"] == FREEZE_COMMIT and prov["git_status_tracked"] == []
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["frozen_strat"]["sha256_lf"] == r2.STRAT_INSTRUMENT_SHA256
    assert prov["frozen_twin"]["sha256_lf"] == rs.TWIN_INSTRUMENT_SHA256
    assert prov["frozen_instrument"]["sha256_lf"] == rb.FROZEN_INSTRUMENT_SHA256
    assert prov["n_test_prompts"] == 30 and prov["constants"]["lambdas"] == list(r2.LAMBDAS)
    assert prov["constants"]["k_grid"] == [r2.k_tag(k) for k in r2.K_GRID] and prov["constants"]["n_boot"] == r2.N_BOOT
    assert prov["encoding_selected"] == "prev_table" and prov["encoding_source"] == "strat"
    assert all(prov["lambda_source"][a] == "strat" for a in r2.ARMS_TWIN)
    assert prov["k_selected"] == want["k"] and prov["k_grid_edge"] is False
    src = prov["replay_source"]
    assert src["kind"] == "hf" and src["sha256"] == r2.REPLAY_SOURCE_SHA256 and prov["replay_source_matches_pinned"] is True
    assert src["snapshot"] == r2.SNAPSHOT and src["model"] == r2.MODEL_ID and src["eps"] == 1e-5
    assert prov["hidden"]["width"] == 2048 and prov["hidden"]["dtype"] == "float16"
    # the committed stratified payload this run took its encoding, lambdas and rows from is the one on disk
    st = prov["strat"]
    spath, sstate = ROOT / st["path"], ROOT / st["state_path"]
    assert spath.name == want["strat"] and st["instrument_sha256"] == r2.STRAT_INSTRUMENT_SHA256
    assert hashlib.sha256(spath.read_bytes()).hexdigest() == st["sha256"]
    assert hashlib.sha256(sstate.read_bytes()).hexdigest() == st["state_sha256"]
    strat_payload = json.loads(spath.read_text(encoding="utf-8"))
    assert strat_payload["provenance"]["encoding_selected"] == st["encoding"] == "prev_table"
    for arm in r2.ARMS_TWIN:
        assert float(strat_payload["provenance"]["lambda_selected"][arm]) == prov["lambda_selected"][arm]
    for scope in r2.IDENTITY_SCOPES:
        assert strat_payload["conclusion"]["deltas"][f"gate_eq|B={r2.LABEL_BUDGET}|{scope}"] == st["gate_eq"][scope]
    # the state file is bound to the harvest, carries the records, and holds only TEST prompts in the six strata
    header, rows = pr.load_state(state)
    assert header["harvest_npz_sha256"] == prov["harvest_npz_sha256"] == st["harvest_npz_sha256"]
    assert header["encoding"] == "prev_table" and header["k_selected"] == want["k"] and header["strat"] == st
    assert header["lambda_selected"] == prov["lambda_selected"] and header["replay_source_sha256"] == src["sha256"]
    hdir = ROOT / "results" / "real" / want["harvest"]
    assert len(header["harvest_npz_sha256"]) == len(want["seeds"])
    for shard, sha in header["harvest_npz_sha256"].items():
        meta = json.loads((hdir / shard.replace(".npz", ".meta.json")).read_text(encoding="utf-8"))
        assert meta["npz_sha256"] == sha, shard
    assert len(rows) == payload["n_state_rows"]
    prompts = {int(r["prompt_idx"]) for r in rows}
    assert len(prompts) == 30 and all(split_of_prompt(p) == "test" for p in prompts)
    assert {r["arm"] for r in rows} == set(r2.ARMS_REQUIRED) and {r["stratum"] for r in rows} <= set(r2.STRATA)
    # REPRODUCE against the committed stratified rows, re-derived here from the files, not read from the payload
    _, strat_rows = pr.load_state(sstate)
    rep = r2.reproduce_check(rows, strat_rows)
    assert rep["status"] == "EXACT" and rep["needed_mismatch_rows"] == 0 and rep["hits_mismatch_rows"] == 0
    # exact recompute under the numpy that ran the instrument; labels only under another numpy
    if np.__version__ == prov["numpy_version"]:
        got = r2.conclude_from(path)
    else:
        got = r2.conclude(rows, header["encoding"], r2.k_of_tag(header["k_selected"]), strat_rows, st["gate_eq"])
    lab = got["labels"]
    assert lab["label"] == want["label"] and lab["q1"] == want["q1"] and lab["q2"] == want["q2"]
    assert lab["reproduce_status"] == "EXACT" and lab["reproduce_ok"] is True and lab["void"] is False
    assert lab["gate_eq_matches_strat"] is True and lab["missing_arms"] == [] and lab["missing_label_cells"] == []
    assert lab["k_selected"] == want["k"]
    assert (lab["fallback_floor_straddle"], lab["all_floor_straddle"], lab["d_eq_h_floor_straddle"], lab["d_add_h_floor_straddle"],
            lab["q2_floor_straddle"], lab["fallback_negative"], lab["all_negative"], lab["h_negative"], lab["q2_reader_guard"],
            lab["address_handicap"], lab["k_at_replay_end"]) == FLAGS
    assert lab["gate_eq_r2_fallback_reading"] == "SIGNAL" and lab["gate_eq_r2_all_reading"] == want["all_reading"]
    assert lab["d_eq_h_all_reading"] == "NOT-SHOWN" and lab["d_add_h_all_reading"] == "NOT-SHOWN"
    assert lab["shrinkage_readings"]["fallback"] == "SIGNAL" and lab["h_inconsistent_cause"] is None
    # the sentence is the pinned composition for those flags: the no-straddle Q1 branch + the pooled-straddle clause,
    # the no-straddle Q2 branch (the strike's sentence), no guard, no NEGATIVE prefix
    expect = r2.SENTENCES_Q1[(want["q1"], False)] + r2._ALL_STRADDLE + "; " + r2.SENTENCES_Q2[(want["q2"], False)]
    assert lab["sentence"] == expect
    assert "stage 2's address-beyond-free motivation is struck" not in lab["sentence"]   # the strike is the record's sentence, not the tool's


def test_both_harvests_agree_and_the_strike_condition_holds():
    labs = {}
    for name in LANDED:
        payload = json.loads((ROOT / "results" / "real" / name).read_text(encoding="utf-8"))
        labs[name] = payload["conclusion"]["labels"]
    a, b = labs["prefetch_r2_s3.json"], labs["prefetch_r2_s3_r.json"]
    assert a["q1"] == b["q1"] and a["q2"] == b["q2"] == "H-ABSORBS"
    # the pinned strike condition: no straddle on either Q2 reading on either harvest, the replication agreeing, no guard
    assert not a["q2_floor_straddle"] and not b["q2_floor_straddle"] and not a["q2_reader_guard"] and not b["q2_reader_guard"]


def _cache_present() -> bool:
    return r2.hf_snapshot_dir().exists()


@pytest.mark.skipif(not _cache_present(), reason="the pinned checkpoint is not in the Hugging Face cache on this machine")
@pytest.mark.parametrize("name", sorted(LANDED))
def test_replay_probe_vectors_recompute_from_the_cache(name):
    """The eight probe tokens' replay vectors, recomputed at the payload's replay_vocab with the tool's chunk, hash to the
    recorded shas; the source hashes to the pinned sha (skipped, and said, where the cache is absent)."""
    prov = json.loads((ROOT / "results" / "real" / name).read_text(encoding="utf-8"))["provenance"]
    src = r2.load_replay_source("hf")
    assert src["sha256"] == r2.REPLAY_SOURCE_SHA256 == prov["replay_source"]["sha256"]
    table = r2.replay_table(src, int(prov["replay_vocab"]))
    assert r2.replay_probe(table) == prov["replay_probe"]

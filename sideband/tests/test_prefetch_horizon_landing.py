"""tests/test_prefetch_horizon_landing.py — the committed horizon-read payloads (the 2026-10-04 amendment to the R2
block of docs/BLUEPRINT.md; F-26's fourth dated status line; the dated K-6 STATUS line) reproduce their own conclusion
through the instrument's exact recompute surface, incl. the REPRODUCE check against the committed R2 state files; the
instrument on disk is the one both payloads attest; the frozen chain is still frozen; the replay source is the pinned
checkpoint, and where the Hugging Face cache holds it the probe vectors recompute to their recorded shas.

Landing test written 2026-10-04 after both registered runs were read; it pins the labels as landed, the instrument sha
and both state files' shas, so a changed payload, state file, R2 file, tool or instrument flags here. Missing committed
evidence FAILS, never skips; only the cache-dependent probe check skips, and says so. Nothing in this file imports torch."""
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
import run_prefetch_horizon as hz  # noqa: E402
import run_prefetch_r2 as r2  # noqa: E402
import run_prefetch_strat as rs  # noqa: E402
import run_prefetch_bigram as rb  # noqa: E402
import run_prefetch_readouts as pr  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402

# the clean tree both runs attest: the memory-row commit right after the freeze commit b41d3f3 (the eight files hashed at
# the freeze unchanged between them); the instrument's raw-bytes sha (both payloads' provenance; the freeze record)
RUN_COMMIT = "5e0e2a94ecb8a5c07e6e2917ed5ed4deba825aab"
FREEZE_COMMIT_PREFIX = "b41d3f3"
INSTRUMENT_SHA256 = "cc6a7fb0bc505fe0f439e4dc6ba99366c7446d58b114a5636f12905d0df4db55"
LABEL = "LEAD-TIME-ABSORBED"
# the labels read on 2026-10-04 through --conclude-from on both harvests, and each state file's sha256 (raw bytes;
# results/** carries -text, so every checkout writes them as committed)
LANDED = {
    "prefetch_horizon_s3.json": {"seeds": [0, 1, 2, 3, 4, 5, 6, 7], "harvest": "harvest_moe", "r2": "prefetch_r2_s3.json",
                                 "state_sha256": "e768ca7a68db5ccecbd8013ce3c6e78a63e76a493e592b1b10c50d5bd1811759"},
    "prefetch_horizon_s3_r.json": {"seeds": [8, 9, 10, 11], "harvest": "harvest_moe_r", "r2": "prefetch_r2_s3_r.json",
                                   "state_sha256": "0bbe55e9941b9b9025e015519c1f34c61dc802bcef01c658767b1f84d137a836"},
}
N_STATE_ROWS = 161280          # both harvests: 30 test prompts x two scopes x every (arm, budget, gate) of the four horizons
K_SELECTED = "128"             # every horizon on both harvests


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_instrument_on_disk_is_the_attested_one_and_the_chain_is_frozen():
    # the payloads attest the RAW bytes (`-text` writes them LF on every checkout), so the raw sha is the faithful pin
    assert _sha_raw(ROOT / "tools" / "run_prefetch_horizon.py") == INSTRUMENT_SHA256
    assert hz.assert_frozen_r2() == hz.R2_INSTRUMENT_SHA256
    assert r2.assert_frozen_strat() == r2.STRAT_INSTRUMENT_SHA256
    assert rs.assert_frozen_twin() == rs.TWIN_INSTRUMENT_SHA256
    assert rb.assert_frozen_instrument() == rb.FROZEN_INSTRUMENT_SHA256


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_horizon_payloads_reproduce_their_conclusion(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed horizon-read evidence missing: {name}"   # absent is a failure, not a skip
    want = LANDED[name]
    assert _sha_raw(state) == want["state_sha256"], f"{state.name} is not the committed state file"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == hz.REGISTERED
    prov = payload["provenance"]
    # a registered run, never a smoke: full seeds, the registered grids and horizons, the clean tree, the pinned source
    assert prov["smoke"] is False and prov["smoke_split_val"] is False
    a = prov["args"]
    assert a["only_seeds"] is None and a["lambdas"] is None and a["k_grid"] is None and a["horizons"] is None
    assert a["r2"] is None and a["replay"] == "hf" and a["conclude_from"] is None
    assert sorted(prov["seeds"]) == want["seeds"] and Path(prov["harvest_dir"]).name == want["harvest"]
    assert prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == []
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["frozen_r2"]["sha256_lf"] == hz.R2_INSTRUMENT_SHA256
    assert prov["frozen_strat"]["sha256_lf"] == r2.STRAT_INSTRUMENT_SHA256
    assert prov["frozen_twin"]["sha256_lf"] == rs.TWIN_INSTRUMENT_SHA256
    assert prov["frozen_instrument"]["sha256_lf"] == rb.FROZEN_INSTRUMENT_SHA256
    c = prov["constants"]
    assert c["lambdas"] == list(hz.LAMBDAS) and c["k_grid"] == [r2.k_tag(k) for k in hz.K_GRID]
    assert c["horizons"] == list(hz.HORIZONS) and c["label_horizons"] == list(hz.LABEL_HORIZONS)
    assert c["reproduce_horizon"] == hz.REPRODUCE_HORIZON and c["label_budget"] == hz.LABEL_BUDGET
    assert c["material"] == hz.MATERIAL and c["n_boot"] == hz.N_BOOT and c["boot_seed"] == hz.BOOT_SEED
    assert prov["n_test_prompts"] == 30
    assert prov["encoding_selected"] == "prev_table" and prov["encoding_source"] == "r2"
    for j in hz.HORIZONS:
        sel = prov["selection"][str(j)]
        assert sel["k_selected"] == K_SELECTED and sel["k_grid_edge"] is False
    assert prov["selection"]["1"]["reselect"]["matches_r2"] is True
    src = prov["replay_source"]
    assert src["kind"] == "hf" and src["sha256"] == r2.REPLAY_SOURCE_SHA256 and prov["replay_source_matches_pinned"] is True
    assert src["snapshot"] == r2.SNAPSHOT and src["model"] == r2.MODEL_ID and src["eps"] == 1e-5
    assert prov["hidden"]["width"] == 2048 and prov["hidden"]["dtype"] == "float16"
    # the committed R2 payload this run took k, every horizon-1 lambda and the REPRODUCE rows from is the one on disk
    rr = prov["r2"]
    rpath = ROOT / rr["path"]
    assert rpath.name == want["r2"] and rr["instrument_sha256"] == hz.R2_INSTRUMENT_SHA256
    assert hashlib.sha256(rpath.read_bytes()).hexdigest() == rr["sha256"]
    assert hashlib.sha256((ROOT / rr["state_path"]).read_bytes()).hexdigest() == rr["state_sha256"]
    fresh = hz.read_r2(rpath)
    assert fresh["sha256"] == rr["sha256"] and fresh["state_sha256"] == rr["state_sha256"]
    assert hz._r2_header(fresh) == rr
    # the state file is bound to the harvest, carries the records, and holds only TEST prompts at the two scopes
    header, rows = pr.load_state(state)
    assert header["registered"] == hz.REGISTERED and header["smoke"] is False
    assert header["harvest_npz_sha256"] == prov["harvest_npz_sha256"] == rr["harvest_npz_sha256"]
    assert header["encoding"] == "prev_table" and header["horizons"] == list(hz.HORIZONS)
    assert header["k_of_horizon"] == {str(j): K_SELECTED for j in hz.HORIZONS}
    assert header["lambda_selected"] == {str(j): prov["selection"][str(j)]["lambda_selected"] for j in hz.HORIZONS}
    assert header["r2"] == rr and header["replay_source_sha256"] == src["sha256"]
    hdir = ROOT / "results" / "real" / want["harvest"]
    assert len(header["harvest_npz_sha256"]) == len(want["seeds"])
    for shard, sha in header["harvest_npz_sha256"].items():
        meta = json.loads((hdir / shard.replace(".npz", ".meta.json")).read_text(encoding="utf-8"))
        assert meta["npz_sha256"] == sha, shard
    assert len(rows) == payload["n_state_rows"] == N_STATE_ROWS
    prompts = {int(r["prompt_idx"]) for r in rows}
    assert len(prompts) == 30 and all(split_of_prompt(p) == "test" for p in prompts)
    assert {int(r["key"]) for r in rows} == set(hz.HORIZONS) and {r["scope"] for r in rows} == set(hz.STATE_SCOPES)
    assert {r["arm"] for r in rows if int(r["key"]) == 1} == set(hz.ARMS_J1)
    for j in hz.LABEL_HORIZONS:
        assert {r["arm"] for r in rows if int(r["key"]) == j} == set(hz.arms_h("prev_table"))
    # REPRODUCE against the committed R2 rows, re-derived here from the files, not read from the payload
    rep = hz.reproduce_check(rows, fresh["_rows"])
    assert rep["status"] == "EXACT" and rep["needed_mismatch_rows"] == 0 and rep["hits_mismatch_rows"] == 0
    assert rep["missing_here"] == 0 and rep["extra_here"] == 0 and rep["n_r2_union_rows"] == rep["n_compared"]
    # exact recompute under the numpy that ran the instrument; labels only under another numpy
    if np.__version__ == prov["numpy_version"]:
        got = hz.conclude_from(path)
    else:
        lam = header["lambda_selected"]
        fh_edge = {j: bool(float(lam[j]["free_h"]) in (hz.LAMBDAS[0], hz.LAMBDAS[-1])) for j in lam}
        got = hz.conclude(rows, header["encoding"], header["k_of_horizon"], fresh["_rows"], fresh["cells"],
                          horizons=tuple(hz.HORIZONS), free_h_edge=fh_edge)
    lab = got["labels"]
    assert lab["label"] == lab["stage"] == LABEL and lab["void"] is False
    assert lab["reproduce_status"] == "EXACT" and lab["reproduce_ok"] is True and lab["identity_matches_r2"] is True
    assert lab["k_of_horizon"] == {str(j): K_SELECTED for j in hz.HORIZONS}
    assert lab["missing_arms"] == {} and lab["missing_label_cells"] == [] and lab["label_horizons"] == list(hz.LABEL_HORIZONS)
    assert lab["first_horizon"] is None
    assert lab["straddle_horizons"] == [] and lab["guard_horizons"] == [] and lab["free_h_edge_horizons"] == []
    for j in hz.HORIZONS:
        h = lab["horizons"][str(j)]
        assert h["q"] == "H-ABSORBS"
        assert h["d_eq_h_reading"] == "NOT-SHOWN" and h["d_add_h_reading"] == "NOT-SHOWN"
        assert (h["d_eq_h_floor_straddle"], h["d_add_h_floor_straddle"], h["floor_straddle"], h["negative"],
                h["reader_guard"], h["inconsistent_cause"], h["b8_b32_disagree"]) == (False, False, False, False, False, None, [])
        assert h["sentence"] == hz.sentence_horizon("H-ABSORBS", False, j)
    said = lab["said_in_words"]
    assert said["b8_b32_disagree"] == [] and said["negative_horizons"] == [] and said["fallback_signal"] == []
    assert said["free_h_edge_horizons"] == [] and not any(said["h_only_above_history_tok"].values())
    # the stage sentence is the pinned template with no straddle, guard or edge suffix
    assert lab["sentence"] == hz.SENTENCE_STAGE[LABEL]
    assert "closes at this reader" in lab["sentence"]


def test_both_harvests_agree_and_the_closure_condition_holds():
    labs = {}
    for name in LANDED:
        payload = json.loads((ROOT / "results" / "real" / name).read_text(encoding="utf-8"))
        labs[name] = payload["conclusion"]["labels"]
    a, b = labs["prefetch_horizon_s3.json"], labs["prefetch_horizon_s3_r.json"]
    # the pinned cross-harvest closure condition: BOTH harvests LEAD-TIME-ABSORBED with no straddle and no guard at any
    # label horizon on either (and no free_h grid edge), the per-horizon labels agreeing
    assert a["stage"] == b["stage"] == LABEL and a["first_horizon"] is None and b["first_horizon"] is None
    assert a["straddle_horizons"] == b["straddle_horizons"] == [] and a["guard_horizons"] == b["guard_horizons"] == []
    assert a["free_h_edge_horizons"] == b["free_h_edge_horizons"] == []
    for j in hz.HORIZONS:
        assert a["horizons"][str(j)]["q"] == b["horizons"][str(j)]["q"] == "H-ABSORBS"


def _cache_present() -> bool:
    return r2.hf_snapshot_dir().exists()


@pytest.mark.skipif(not _cache_present(), reason="the pinned checkpoint is not in the Hugging Face cache on this machine")
@pytest.mark.parametrize("name", sorted(LANDED))
def test_replay_probe_vectors_recompute_from_the_cache(name):
    """The probe tokens' replay vectors, recomputed at the payload's replay_vocab, hash to the recorded shas; the source
    hashes to the pinned sha (skipped, and said, where the cache is absent)."""
    prov = json.loads((ROOT / "results" / "real" / name).read_text(encoding="utf-8"))["provenance"]
    src = r2.load_replay_source("hf")
    assert src["sha256"] == r2.REPLAY_SOURCE_SHA256 == prov["replay_source"]["sha256"]
    table = r2.replay_table(src, int(prov["replay_vocab"]))
    assert r2.replay_probe(table) == prov["replay_probe"]

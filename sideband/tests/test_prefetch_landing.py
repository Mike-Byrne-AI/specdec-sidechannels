"""tests/test_prefetch_landing.py — the committed OQ-9 stage-1 payloads (F-26)
reproduce their own conclusion through the frozen instrument's exact recompute
surface, and the instrument on disk is the frozen one.

Landing test written 2026-09-15 after both registered runs were read; it pins
the labels as landed so that a changed payload, state file or instrument flags
here. Nothing in this file imports torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_prefetch_readouts as pr  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402

# the freeze commit and the instrument it froze (docs/BLUEPRINT.md, PRE-FREEZE ROUND (h))
FREEZE_COMMIT = "c4c4511a5746969024077ee59d2413664c50a836"
INSTRUMENT_SHA256 = "8529532d4d787833cfa667a11d406ffa928c9c079836401e4930d43a6fb0e69a"
# the labels read on 2026-09-15 through --conclude-from on both harvests (F-26)
LANDED = {
    "prefetch_s3.json": {"seeds": [0, 1, 2, 3, 4, 5, 6, 7], "harvest": "harvest_moe"},
    "prefetch_s3_r.json": {"seeds": [8, 9, 10, 11], "harvest": "harvest_moe_r"},
}
LANDED_STAGE = "PREFETCH-HEADROOM"
LANDED_READINGS = {"history": "SIGNAL", "address_beyond_token": "SIGNAL",
                   "intra_forward": "SIGNAL", "draft": "SIGNAL"}


def _sha_lf(path: Path) -> str:
    """sha256 of the file with CRLF normalised to LF (the committed blob is LF;
    a CRLF checkout must still hash to the frozen instrument)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_instrument_on_disk_is_the_frozen_one():
    assert _sha_lf(ROOT / "tools" / "run_prefetch_readouts.py") == INSTRUMENT_SHA256


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_prefetch_payloads_reproduce_their_conclusion(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    if not (path.exists() and state.exists()):
        pytest.skip("OQ-9 stage-1 payloads not present")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == pr.REGISTERED
    prov = payload["provenance"]
    # a registered run, never a smoke: full seeds, pinned split, the registered grid, a clean tree
    assert prov["smoke"] is False and prov["smoke_split_val"] is False
    assert prov["args"]["only_seeds"] is None and prov["args"]["lambdas"] is None
    assert sorted(prov["seeds"]) == LANDED[name]["seeds"]
    # the payload records the writing box's separators (backslashes); PureWindowsPath takes the last
    # component under either separator on every OS, where POSIX Path().name would keep the whole string
    assert PureWindowsPath(prov["harvest_dir"]).name == LANDED[name]["harvest"]
    assert prov["git_commit"] == FREEZE_COMMIT and prov["git_status_tracked"] == []
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["n_test_prompts"] == 30
    assert prov["constants"]["n_boot"] == pr.N_BOOT and prov["constants"]["boot_seed"] == pr.BOOT_SEED
    assert prov["constants"]["lambdas"] == list(pr.LAMBDAS)
    # the state file is bound to the harvest and holds only TEST prompts
    header, rows = pr.load_state(state)
    assert header["harvest_npz_sha256"] == prov["harvest_npz_sha256"]
    # ... and equal to the COMMITTED shard metas (the .npz shards are gitignored)
    hdir = ROOT / "results" / "real" / LANDED[name]["harvest"]
    assert len(header["harvest_npz_sha256"]) == len(LANDED[name]["seeds"])
    for shard, sha in header["harvest_npz_sha256"].items():
        meta = json.loads((hdir / shard.replace(".npz", ".meta.json")).read_text(encoding="utf-8"))
        assert meta["npz_sha256"] == sha, shard
    assert len(rows) == payload["n_state_rows"]
    prompts = {int(r["prompt_idx"]) for r in rows}
    assert len(prompts) == 30 and all(split_of_prompt(p) == "test" for p in prompts)
    # exact recompute (raises SystemExit on any mismatch) under the numpy that ran the instrument;
    # the bootstrap CIs come from numpy's Generator, whose streams are not version-stable, so under
    # another numpy only the labels (points and integer counts) are pinned, not the CI bytes
    if np.__version__ == prov["numpy_version"]:
        got = pr.conclude_from(path)
    else:
        got = pr.conclude(rows)
    lab = got["labels"]
    assert lab["stage"] == LANDED_STAGE
    assert lab["cache_sufficient"] is False and lab["p1_window_kill_would_fire"] is False
    for reading, label in LANDED_READINGS.items():
        assert lab[reading] == label
        d = lab[f"{reading}_delta"]
        assert d["lo"] > 0 and d["delta"] >= pr.MATERIAL
    assert lab["sideband_sentence"] == (
        "the address stream adds a material margin over the free input token at this reader")
    assert lab["missing_arms"] == [] and lab["missing_label_cells"] == []

"""tests/test_prefetch_bigram_landing.py — the committed free-bigram twin payloads (the
2026-10-01 amendment to OQ-9 stage 1; F-26's dated status line) reproduce their own
conclusion through the instrument's exact recompute surface, the instrument on disk is
the one both payloads attest, and the frozen stage-1 parent is still frozen.

Landing test written 2026-10-01 after both registered runs were read; it pins the labels as
landed so that a changed payload, state file or instrument flags here. Nothing in this
file imports torch."""
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
import run_prefetch_bigram as bg  # noqa: E402
import run_prefetch_readouts as pr  # noqa: E402
from sideband.harvest import split_of_prompt  # noqa: E402

# the freeze commit and the instrument it froze (both payloads' provenance; the amendment block's OUTCOME)
FREEZE_COMMIT = "d55e62f15f610be6c9520a3555fe619b2291ddee"
INSTRUMENT_SHA256 = "10599fa98c276751f3296ecff6815aae07a701e35d13b5a2fb6ff8170ba7a11a"
# the labels read on 2026-10-01 through --conclude-from on both harvests (F-26's dated status line)
LANDED = {
    "prefetch_bigram_s3.json": {"seeds": [0, 1, 2, 3, 4, 5, 6, 7], "harvest": "harvest_moe",
                                "committed": "prefetch_s3.json", "label": "SURVIVES", "encoding": "prev_table",
                                "gate_eq": "SIGNAL", "address_beyond_bigram": "SIGNAL"},
    "prefetch_bigram_s3_r.json": {"seeds": [8, 9, 10, 11], "harvest": "harvest_moe_r",
                                  "committed": "prefetch_s3_r.json", "label": "SURVIVES", "encoding": "prev_table",
                                  "gate_eq": "SIGNAL", "address_beyond_bigram": "SIGNAL"},
}


def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_instrument_on_disk_is_the_attested_one_and_its_parent_is_frozen():
    assert _sha_lf(ROOT / "tools" / "run_prefetch_bigram.py") == INSTRUMENT_SHA256
    assert bg.assert_frozen_instrument() == bg.FROZEN_INSTRUMENT_SHA256


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_bigram_payloads_reproduce_their_conclusion(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    # committed evidence: absent is a failure, not a skip (the stage-1 landing test skips; this one does not)
    assert path.exists() and state.exists(), f"committed free-bigram twin evidence missing: {name}"
    want = LANDED[name]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == bg.REGISTERED
    prov = payload["provenance"]
    # a registered run, never a smoke: full seeds, the registered grid, a clean tree at the freeze commit
    assert prov["smoke"] is False and prov["smoke_split_val"] is False
    assert prov["args"]["only_seeds"] is None and prov["args"]["lambdas"] is None and prov["args"]["committed"] is None
    assert sorted(prov["seeds"]) == want["seeds"] and Path(prov["harvest_dir"]).name == want["harvest"]
    assert prov["git_commit"] == FREEZE_COMMIT and prov["git_status_tracked"] == []
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["frozen_instrument"]["sha256_lf"] == bg.FROZEN_INSTRUMENT_SHA256
    assert prov["n_test_prompts"] == 30 and prov["constants"]["lambdas"] == list(bg.LAMBDAS)
    assert prov["constants"]["n_boot"] == bg.N_BOOT and prov["constants"]["boot_seed"] == bg.BOOT_SEED
    assert prov["encoding_selected"] == want["encoding"]
    # the committed stage-1 cell this run read is the committed payload as it stands
    cell = prov["committed_cell"]
    cpath = ROOT / cell["path"]
    assert cpath.name == want["committed"] and cell["key"] == bg.COMMITTED_KEY
    assert hashlib.sha256(cpath.read_bytes()).hexdigest() == cell["sha256"]
    committed = json.loads(cpath.read_text(encoding="utf-8"))
    assert committed["conclusion"]["deltas"][bg.COMMITTED_KEY]["delta"] == cell["delta"]
    assert committed["provenance"]["instrument_sha256"] == cell["instrument_sha256"] == bg.FROZEN_INSTRUMENT_SHA256
    # the state file is bound to the harvest, carries the encoding and the cell, and holds only TEST prompts
    header, rows = pr.load_state(state)
    assert header["harvest_npz_sha256"] == prov["harvest_npz_sha256"]
    assert header["encoding"] == want["encoding"] and header["committed_cell"] == cell
    hdir = ROOT / "results" / "real" / want["harvest"]
    assert len(header["harvest_npz_sha256"]) == len(want["seeds"])
    for shard, sha in header["harvest_npz_sha256"].items():
        meta = json.loads((hdir / shard.replace(".npz", ".meta.json")).read_text(encoding="utf-8"))
        assert meta["npz_sha256"] == sha, shard
    assert len(rows) == payload["n_state_rows"]
    prompts = {int(r["prompt_idx"]) for r in rows}
    assert len(prompts) == 30 and all(split_of_prompt(p) == "test" for p in prompts)
    assert {r["arm"] for r in rows} == set(bg.ARMS_REQUIRED)
    # the encoding re-derives from the payload's own val table under every numpy (no RNG involved)
    assert bg.select_encoding(prov["val_table"], prov["lambda_selected"]) == want["encoding"]
    # exact recompute under the numpy that ran the instrument; labels only under another numpy
    # (the bootstrap CIs come from numpy's Generator, whose streams are not version-stable)
    if np.__version__ == prov["numpy_version"]:
        got = bg.conclude_from(path)
    else:
        got = bg.conclude(rows, header["encoding"], cell["delta"])
    lab = got["labels"]
    assert lab["label"] == want["label"] and lab["remeasure_ok"] is True
    assert lab["gate_eq_reading"] == want["gate_eq"] and lab["address_beyond_bigram_reading"] == want["address_beyond_bigram"]
    assert lab["largest_gain_gate"] == 0 and lab["driven_by_gate0"] is True
    assert abs(lab["remeasure_gap"]) <= bg.REMEASURE_TOL
    assert lab["sentence"] == bg.SENTENCES[want["label"]]
    assert lab["missing_arms"] == [] and lab["missing_label_cells"] == []

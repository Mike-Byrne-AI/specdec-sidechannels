"""tests/test_reader_s1_landing.py — the committed S1 READER RE-TEST payloads (docs/BLUEPRINT.md, "S1 READER RE-TEST
REGISTRATION", 2026-10-16; FINDINGS.md F-29) are registered runs of the frozen reader-lens instrument's s1 stage from the
launch commit, which is the freeze commit that holds the registration; the word payload was written by the frozen word
instrument at that HEAD; and the S1 word reproduces through tools/run_reader_s1.conclude on the pair (which verifies every
payload's stage, role, harvest, registry, row set, HEAD, n_boot, instrument sha and state sha first, recomputes every
readout from the state files and derives the labels through the frozen rules).

Landing test written 2026-10-17 after both registered runs were read; it pins both instruments' shas, the payloads' and
state files' shas, the labels, the licences, the word, the pairing checks, the R-N scale constants and the gate margins at
six decimals. Missing committed evidence FAILS, never skips."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_reader_lens as rl  # noqa: E402
import run_reader_s1 as rs1  # noqa: E402  (asserts the frozen chain at import)

PINS = {'C_HZ': {'primary': 0.173976, 'replication': 0.173982},
 'INSTRUMENT_SHA256': 'd1125670be056b4824ebfcd734379f40e44db994308c10accb731839d2a4a624',
 'LABELS': {'RL|L1_concept_k16': 'ABSORBED',
            'RN|L1_concept_k16': 'ABSORBED',
            'RT|L1_concept_k16': 'ABSORBED'},
 'LANDED': {'readers_s1.json': {'gate': {'RL|L1_concept_k16': 0.000382,
                                         'RN|L1_concept_k16': 0.002589,
                                         'RT|L1_concept_k16': 0.000339},
                                'harvest': 'harvest_shadow',
                                'mn_r': {'RL|L1_concept_k16': 0.002676,
                                         'RN|L1_concept_k16': -0.003747,
                                         'RT|L1_concept_k16': -0.000339},
                                'mt': {'RL|L1_concept_k16': 0.003059,
                                       'RN|L1_concept_k16': -0.001158,
                                       'RT|L1_concept_k16': 0.0},
                                'payload_sha256': '16c5b68c2854609d6aa8e793de42d26ac9cbdb8e4f3d3e0a5e851d286085b5cc',
                                'resumed_cells': 0,
                                'rn_rt_a_identical': True,
                                'role': 'primary',
                                'state_sha256': '0e89a857f6ce9e90f9e224ba3d9540498693deb74a7900fc140c34453a296938',
                                'twin_perm_equal': True},
            'readers_s1_r.json': {'gate': {'RL|L1_concept_k16': -4.4e-05,
                                           'RN|L1_concept_k16': 0.002209,
                                           'RT|L1_concept_k16': 0.001088},
                                  'harvest': 'harvest_shadow_r',
                                  'mn_r': {'RL|L1_concept_k16': 0.002319,
                                           'RN|L1_concept_k16': -0.005012,
                                           'RT|L1_concept_k16': 0.004847},
                                  'mt': {'RL|L1_concept_k16': 0.002275,
                                         'RN|L1_concept_k16': -0.002803,
                                         'RT|L1_concept_k16': 0.005936},
                                  'payload_sha256': '3a21e9469805615f9fb1b6746a8b00e183e3330929722241807fd4c98b692a18',
                                  'resumed_cells': 0,
                                  'rn_rt_a_identical': True,
                                  'role': 'replication',
                                  'state_sha256': '5aafc5c09d8c79c010bd58317c62ff0b502616db1ff1fd7917fa5bdd6592dd8e',
                                  'twin_perm_equal': True}},
 'LICENCES': {'RL|L1_concept_k16': None, 'RN|L1_concept_k16': None, 'RT|L1_concept_k16': None},
 'REOPENED': [],
 'RUN_COMMIT': '46a812fc309826c48e9e82ebe930ca9fce965075',
 'VOID': [],
 'WORD': 'K-2-NOT-OVERTURNED-AT-S1',
 'WORD_INSTRUMENT_SHA256': '94640a09cbebbadf9eff91dec5249be89880f1d298a3aa3819e2c51acc624c11',
 'WORD_PAYLOAD_SHA256': '7815547ef556ecf9a55221b2ffbf9488902d9894982a06c5e116e66e7bbce193'}
RUN_COMMIT = PINS["RUN_COMMIT"]
N_ROWS = 36
S1_SPACE = "L1_concept_k16"


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _r6(x: float) -> float:
    return round(x, 6)


def test_both_instruments_are_the_committed_ones():
    assert _sha_raw(ROOT / "tools" / "run_reader_lens.py") == PINS["INSTRUMENT_SHA256"] == rs1.FROZEN_READER_LENS_SHA256
    assert _sha_raw(ROOT / "tools" / "run_reader_s1.py") == PINS["WORD_INSTRUMENT_SHA256"]


def test_the_launch_commit_is_the_freeze_commit_that_holds_the_registration():
    """The registration pins the launch commit as the freeze commit. The record names it: the block's OUTCOME and the
    CHANGELOG's freeze line carry its short hash; where the history is present (not a shallow CI checkout) the commit's
    own tree holds the registration block and its subject is the freeze's."""
    import subprocess
    short = RUN_COMMIT[:7]
    bp = " ".join((ROOT / "docs" / "BLUEPRINT.md").read_text(encoding="utf-8").split())     # the record wraps at 76 columns
    assert f"- OUTCOME (2026-10-17; both registered runs from the clean tree at {short}, the freeze commit" in bp
    assert f"- {short} (2026-10-16) feat(registration): freeze the S1 reader re-test" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    have = subprocess.run(["git", "cat-file", "-e", f"{RUN_COMMIT}^{{commit}}"], cwd=ROOT, capture_output=True)
    if have.returncode == 0:
        body = subprocess.run(["git", "show", f"{RUN_COMMIT}:docs/BLUEPRINT.md"], cwd=ROOT, capture_output=True).stdout.decode("utf-8", "replace")
        assert "S1 READER RE-TEST REGISTRATION (2026-10-16, pre-run" in body     # the registration was in the tree the runs launched from
        msg = subprocess.run(["git", "log", "-1", "--format=%s", RUN_COMMIT], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        assert msg.startswith("feat(registration): freeze the S1 reader re-test")


@pytest.mark.parametrize("name", sorted(PINS["LANDED"]))
def test_committed_s1_payloads_are_registered_runs_with_the_landed_numbers(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed S1 READER RE-TEST evidence missing: {name}"   # absent FAILS, never skips
    want = PINS["LANDED"][name]
    assert _sha_raw(path) == want["payload_sha256"] and _sha_raw(state) == want["state_sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == rl.REGISTERED and payload["stage"] == "s1" and payload["role"] == want["role"]
    assert Path(payload["harvest"]).name == want["harvest"] and tuple(payload["readers"]) == rs1.S1_READERS and list(payload["spaces"]) == [S1_SPACE]
    prov = payload["provenance"]
    assert not payload["partial"] and payload["smoke_cell"] is None and payload["resumed_cells"] == want["resumed_cells"] == 0
    assert prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == [] and prov["instrument_sha256"] == PINS["INSTRUMENT_SHA256"]
    assert prov["threads"] == 6 and prov["cuda_visible_devices"] == "" and int(prov["args"]["n_boot"]) == rl.N_BOOT
    assert prov["torn_bytes_dropped_on_resume"] == 0
    assert len(payload["cells"]) == N_ROWS and payload["riders"] == {}
    for key in want["gate"]:
        rs = payload["per_reader_space"][key]
        if PINS["LABELS"][key] != rl.LABEL_READER_INVALID:
            assert rs["reader_valid"]["ok"]
        assert _r6(rs["gate"]["row"]["margin"]) == want["gate"][key]
        mt = next(m for m in rs["mt_fplus_b_vs_fplus"] if m["offset"] == rl.GATE_OFFSET and m["capacity"] == rl.GATE_CAPACITY)
        mn = next(m for m in rs["mn_r_fplus_r_vs_fplus"] if m["offset"] == rl.GATE_OFFSET and m["capacity"] == rl.GATE_CAPACITY)
        assert _r6(mt["margin"]) == want["mt"][key] and _r6(mn["margin"]) == want["mn_r"][key]
    c_hz = {v["c_hz"] for v in payload["per_reader_space"][f"RN|{S1_SPACE}"]["rescale"].values() if v.get("c_hz") is not None}
    assert len(c_hz) == 1 and _r6(c_hz.pop()) == PINS["C_HZ"][want["role"]]


def test_the_word_payload_is_the_registered_one_written_at_the_launch_head():
    path = ROOT / "results" / "real" / rs1.REGISTERED_OUT
    assert path.exists(), "committed S1 word payload missing"
    assert _sha_raw(path) == PINS["WORD_PAYLOAD_SHA256"]
    w = json.loads(path.read_text(encoding="utf-8"))
    assert w["registered"] and w["stage"] == "s1" and tuple(w["readers"]) == rs1.S1_READERS and w["space"] == S1_SPACE
    assert w["provenance"]["git_commit"] == RUN_COMMIT and w["provenance"]["git_status_tracked"] == []
    assert w["provenance"]["instrument_sha256"] == PINS["WORD_INSTRUMENT_SHA256"] and w["provenance"]["reader_lens_sha256"] == PINS["INSTRUMENT_SHA256"]
    for name, want in PINS["LANDED"].items():
        inp = w["inputs"][want["role"]]
        assert inp["payload"] == name and inp["payload_sha256"] == want["payload_sha256"] and inp["state_sha256"] == want["state_sha256"]
        assert inp["git_commit"] == RUN_COMMIT
        pc = w["pairing"][want["role"]]
        assert pc["twin_perm_sha256_equal_to_committed"] is want["twin_perm_equal"] is True
        assert pc["rn_rt_fresh_a_rows_all_identical"] is want["rn_rt_a_identical"] is True
    assert w["word"]["word"] == PINS["WORD"] and sorted(w["word"]["void_cells"]) == PINS["VOID"] and sorted(w["word"]["reopened"]) == PINS["REOPENED"]
    assert {k: v["label"] for k, v in w["labels"].items()} == PINS["LABELS"]
    assert {k: v["licence"] for k, v in w["labels"].items()} == PINS["LICENCES"]


def test_the_s1_word_reproduces_through_conclude_on_the_pair(phase3_data_root):
    real = ROOT / "results" / "real"
    out = rs1.conclude(real / "readers_s1.json", real / "readers_s1_r.json", data_root=phase3_data_root)   # refuses on any drift; data_root: tests/conftest.py
    assert {k: v["label"] for k, v in out["labels"].items()} == PINS["LABELS"]
    assert {k: v["licence"] for k, v in out["labels"].items()} == PINS["LICENCES"]
    assert out["word"]["word"] == PINS["WORD"] and sorted(out["word"]["void_cells"]) == PINS["VOID"]
    assert out["word"]["provisional"] is bool(PINS["REOPENED"])
    for name, want in PINS["LANDED"].items():
        for key, margin in want["gate"].items():
            assert _r6(out["labels"][key]["gate"][want["role"]]["margin"]) == margin
        pc = out["pairing"][want["role"]]                       # recomputed here, not the stored booleans
        assert pc["twin_perm_sha256_equal_to_committed"] is True and pc["rn_rt_fresh_a_rows_all_identical"] is True

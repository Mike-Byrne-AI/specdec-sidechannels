"""tests/test_reader_lens_readers_long_landing.py — the committed STAGE READERS-LONG payloads of the reader-and-lens
re-test (docs/BLUEPRINT.md, "READER-AND-LENS RE-TEST AT S3 REGISTRATION"; F-28's STAGE READERS-LONG line) are registered
runs of the frozen instrument from the launch commit, admitted on the committed lens payloads, and the ONE K-2 sentence
over both reader stages reproduces through --conclude-from on the readers pair with --lens and --long (which verifies
every payload's stage, role, harvest, registry, row set, HEAD, n_boot, riders, admission shas and location first).

Landing test written 2026-10-09 after both registered runs were read; it pins the labels, the licences, the final K-2
word, the instrument, payload and state shas and the gate margins at six decimals. Missing committed evidence FAILS,
never skips.
Dated amendment 2026-10-19 (the public cut's first CI run): the --conclude-from reproduction below skips under the
variable CI, by name and with its reason, because the lens instrument's byte-for-byte rider gate refused on GitHub's
ubuntu runner while passing on the registered box and in four Linux containers on its CPU, the last of them matching
the runner's numpy, scipy, OpenBLAS build, thread count and distribution; the runner's CPU is the leading candidate,
which operation moves is not measured; SIDEBAND_REQUIRE_CPU_BOUND=1 runs it anyway. Nothing else in this file changed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_reader_lens as rl  # noqa: E402

RUN_COMMIT = "f050574d7994254b707d5b14952a730c26721536"
INSTRUMENT_SHA256 = "d1125670be056b4824ebfcd734379f40e44db994308c10accb731839d2a4a624"
OTHER_SHA256 = {
    "lens_s3.json": "d98d5e6639a01047ad79d36d1fa68427b16b8118bc0c875f6f54a0b4b6b9831d",
    "lens_s3_r.json": "ae73d65495eb7263b5a0e2c42689f5e9c24d84b64afc446cd23c4109831b4366",
    "readers_s3.json": "4113851956e133bf47267573a73b6e0455065f54132d0aa549402623b40ccf4d",
    "readers_s3_r.json": "c970d84f1a00515a18eb3481c0dcb57d1acc490ffa8c2be8d55078e56d820b50"
}
K2_WORD = "K-2-ISOLATED"
S1_TRIGGER = []
LABELS = {
    "RL|L1_olmoe_k16": "ABSORBED",
    "RL|L3_olmoe_groups_v1": "SURVIVES-STRONGER",
    "RL|L3_olmoe_balanced_v1": "ABSORBED"
}
LICENCES = {
    "RL|L1_olmoe_k16": None,
    "RL|L3_olmoe_groups_v1": "equal-dims-only",
    "RL|L3_olmoe_balanced_v1": None
}
LANDED = {
    "readers_long_s3.json": {
        "role": "primary",
        "harvest": "harvest_moe",
        "payload_sha256": "400ab2ac94692b6471c3e1e8cb2a2c1081492d27fded7300abc191b4168ebfa0",
        "state_sha256": "b09741897f7a9055f56921a684859ea6a7e9937c56f227183db394d34296ee4c",
        "git": "f050574d7994254b707d5b14952a730c26721536",
        "gate": {
            "RL|L1_olmoe_k16": 0.00117,
            "RL|L3_olmoe_groups_v1": 0.005107,
            "RL|L3_olmoe_balanced_v1": 0.001546
        }
    },
    "readers_long_s3_r.json": {
        "role": "replication",
        "harvest": "harvest_moe_r",
        "payload_sha256": "b3c6defe8d1edaea0fb99cf065935e4830a924584574b0e0bd66f151b00c00ce",
        "state_sha256": "6c4c8de6d0f3870ef417ab57ead870d347c288f820c0b49e794869f8933e5bd1",
        "git": "f050574d7994254b707d5b14952a730c26721536",
        "gate": {
            "RL|L1_olmoe_k16": 0.001547,
            "RL|L3_olmoe_groups_v1": 0.00541,
            "RL|L3_olmoe_balanced_v1": 0.000545
        }
    }
}
N_ROWS = 39


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _r6(x: float) -> float:
    return round(x, 6)


def test_instrument_and_the_earlier_stages_payloads_are_the_committed_ones():
    assert _sha_raw(ROOT / "tools" / "run_reader_lens.py") == INSTRUMENT_SHA256
    for name, want in OTHER_SHA256.items():
        p = ROOT / "results" / "real" / name
        assert p.exists(), f"committed evidence missing: {name}"
        assert _sha_raw(p) == want


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_readers_long_payloads_are_registered_runs_with_the_landed_labels(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed STAGE READERS-LONG evidence missing: {name}"   # absent FAILS, never skips
    want = LANDED[name]
    assert _sha_raw(path) == want["payload_sha256"] and _sha_raw(state) == want["state_sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == rl.REGISTERED and payload["stage"] == "readers_long" and payload["role"] == want["role"]
    assert Path(payload["harvest"]).name == want["harvest"] and list(payload["readers"]) == ["RL"]
    prov = payload["provenance"]
    assert not payload["partial"] and payload["smoke_cell"] is None and payload["resumed_cells"] == 0
    assert prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == [] and prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["threads"] == 6 and prov["cuda_visible_devices"] == "" and int(prov["args"]["n_boot"]) == rl.N_BOOT
    assert len(payload["cells"]) == N_ROWS and payload["riders"] == {}
    adm = payload["balanced_admission"]
    assert adm["ok"] and {k: v["sha256"] for k, v in adm["payloads"].items()} == {k: v for k, v in OTHER_SHA256.items() if k.startswith("lens")}
    for key, margin in want["gate"].items():
        rs = payload["per_reader_space"][key]
        assert rs["reader_valid"]["ok"] and _r6(rs["gate"]["row"]["margin"]) == margin


@pytest.mark.skipif(
    bool(os.environ.get("CI")) and os.environ.get("SIDEBAND_REQUIRE_CPU_BOUND") != "1",   # the findings lint's CI idiom
    # (tools/lint_findings.py); unset on the registered box; the override runs the gate anywhere, as the section's
    # other REQUIRE switches do (tests/README.md, "Fail, not skip", 2026-10-19)
    reason="a bit-exact recompute gate that holds on the registered box and failed off it: the lens instrument's "
           "byte-for-byte rider check refused on GitHub's ubuntu runner on 2026-10-19 (Python 3.12, numpy 2.5.4, "
           "scipy-openblas 0.3.34.106.0, 2 threads), while four Linux containers on the registered box's CPU passed "
           "it under the runner's versions, OpenBLAS build and thread count, under ubuntu:24.04, and under the "
           "payloads' numpy 2.3.5 with scipy 1.17.1; the runner's CPU is the leading candidate and which operation "
           "moves is not measured (tests/README.md, Fail not skip, 2026-10-19)",
)
def test_the_one_k2_sentence_reproduces_through_conclude_from_with_lens_and_long(phase3_data_root):
    real = ROOT / "results" / "real"
    out = rl.conclude_from(real / "readers_s3.json", real / "readers_s3_r.json",
                           long_pair=(real / "readers_long_s3.json", real / "readers_long_s3_r.json"),
                           lens_pair=(real / "lens_s3.json", real / "lens_s3_r.json"),
                           data_root=phase3_data_root)   # refuses on any drift; data_root: tests/conftest.py
    assert {k: v["label"] for k, v in out["labels_readers_long"].items()} == LABELS
    assert {k: v["licence"] for k, v in out["labels_readers_long"].items()} == LICENCES
    assert out["k2"]["word"] == K2_WORD and out["k2"]["s1_trigger_readers"] == S1_TRIGGER
    assert out["readers_long_runs"] is True

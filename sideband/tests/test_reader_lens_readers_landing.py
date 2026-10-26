"""tests/test_reader_lens_readers_landing.py — the committed STAGE READERS payloads of the reader-and-lens re-test
(docs/BLUEPRINT.md, "READER-AND-LENS RE-TEST AT S3 REGISTRATION"; F-28's STAGE READERS line) are registered runs of the
frozen instrument from the launch commit, admitted on the committed lens payloads, and reproduce their own labels and
the K-2 word through --conclude-from with --lens (which verifies stage, role, harvest, registry, row set, HEAD, n_boot,
the absence of rider cells, the admission shas and the location before it labels anything).

Landing test written 2026-10-05 after both registered runs were read; it pins the labels, the K-2 word, the instrument,
payload and state shas and the gate margins at six decimals. Missing committed evidence FAILS, never skips.
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

RUN_COMMIT = "790b2fc65e5e2833fef96c4ab6511cc779217de8"
INSTRUMENT_SHA256 = "d1125670be056b4824ebfcd734379f40e44db994308c10accb731839d2a4a624"
LENS_SHA256 = {
    "lens_s3.json": "d98d5e6639a01047ad79d36d1fa68427b16b8118bc0c875f6f54a0b4b6b9831d",
    "lens_s3_r.json": "ae73d65495eb7263b5a0e2c42689f5e9c24d84b64afc446cd23c4109831b4366"
}
K2_WORD = "K-2-ISOLATED"
READERS_LONG_RUNS = True
S1_TRIGGER = []
LABELS = {
    "RN|L1_olmoe_k16": "ABSORBED",
    "RN|L3_olmoe_groups_v1": "SURVIVES-STRONGER",
    "RN|L3_olmoe_balanced_v1": "NOT-SHOWN",
    "RT|L1_olmoe_k16": "ABSORBED",
    "RT|L3_olmoe_groups_v1": "ABSORBED",
    "RT|L3_olmoe_balanced_v1": "ABSORBED"
}
LICENCES = {
    "RN|L1_olmoe_k16": None,
    "RN|L3_olmoe_groups_v1": "equal-dims-only",
    "RN|L3_olmoe_balanced_v1": None,
    "RT|L1_olmoe_k16": None,
    "RT|L3_olmoe_groups_v1": None,
    "RT|L3_olmoe_balanced_v1": None
}
LANDED = {
    "readers_s3.json": {
        "role": "primary",
        "harvest": "harvest_moe",
        "payload_sha256": "4113851956e133bf47267573a73b6e0455065f54132d0aa549402623b40ccf4d",
        "state_sha256": "89f060ed44830f4b153568be7e5b03459e151e0424aeea5819cf01bae794fcb0",
        "git": "790b2fc65e5e2833fef96c4ab6511cc779217de8",
        "gate": {
            "RN|L1_olmoe_k16": 0.003035,
            "RN|L3_olmoe_groups_v1": 0.008025,
            "RN|L3_olmoe_balanced_v1": 0.00397,
            "RT|L1_olmoe_k16": 0.00056,
            "RT|L3_olmoe_groups_v1": 0.001165,
            "RT|L3_olmoe_balanced_v1": 0.001501
        }
    },
    "readers_s3_r.json": {
        "role": "replication",
        "harvest": "harvest_moe_r",
        "payload_sha256": "c970d84f1a00515a18eb3481c0dcb57d1acc490ffa8c2be8d55078e56d820b50",
        "state_sha256": "fe63ab2c03652938acc85cd6ce7aa293796ff85876692a6bac39fe786827c8c6",
        "git": "790b2fc65e5e2833fef96c4ab6511cc779217de8",
        "gate": {
            "RN|L1_olmoe_k16": 0.003206,
            "RN|L3_olmoe_groups_v1": 0.012968,
            "RN|L3_olmoe_balanced_v1": 0.004453,
            "RT|L1_olmoe_k16": 0.000668,
            "RT|L3_olmoe_groups_v1": 0.000824,
            "RT|L3_olmoe_balanced_v1": 0.001314
        }
    }
}
N_ROWS = 75


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _r6(x: float) -> float:
    return round(x, 6)


def test_instrument_on_disk_is_the_attested_one_and_the_lens_payloads_are_the_committed_ones():
    assert _sha_raw(ROOT / "tools" / "run_reader_lens.py") == INSTRUMENT_SHA256
    for name, want in LENS_SHA256.items():
        p = ROOT / "results" / "real" / name
        assert p.exists(), f"committed STAGE LENS evidence missing: {name}"
        assert _sha_raw(p) == want


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_readers_payloads_are_registered_runs_with_the_landed_labels(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed STAGE READERS evidence missing: {name}"   # absent FAILS, never skips
    want = LANDED[name]
    assert _sha_raw(path) == want["payload_sha256"] and _sha_raw(state) == want["state_sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == rl.REGISTERED and payload["stage"] == "readers" and payload["role"] == want["role"]
    assert Path(payload["harvest"]).name == want["harvest"] and list(payload["readers"]) == ["RN", "RT"]
    assert payload["spaces"] == [rl.SPACE_L1["olmoe"], rl.SPACE_L3_LOP, rl.SPACE_L3_BAL]
    prov = payload["provenance"]
    assert not payload["partial"] and payload["smoke_cell"] is None and payload["resumed_cells"] == 0
    assert prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == [] and prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["threads"] == 6 and prov["cuda_visible_devices"] == "" and int(prov["args"]["n_boot"]) == rl.N_BOOT
    assert len(payload["cells"]) == N_ROWS and payload["riders"] == {}
    adm = payload["balanced_admission"]
    assert adm["ok"] and {k: v["sha256"] for k, v in adm["payloads"].items()} == LENS_SHA256
    assert sorted(payload["shared_committed_ids"]) == sorted(rl.cell_id(rl.SPACE_L1["olmoe"], 2, "a", "mlp256", s) for s in rl.SEEDS)
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
def test_committed_readers_payloads_reproduce_the_k2_word_through_conclude_from_with_lens(phase3_data_root):
    p = ROOT / "results" / "real" / "readers_s3.json"
    r = ROOT / "results" / "real" / "readers_s3_r.json"
    lens = (ROOT / "results" / "real" / "lens_s3.json", ROOT / "results" / "real" / "lens_s3_r.json")
    assert p.exists() and r.exists(), "committed STAGE READERS evidence missing"
    out = rl.conclude_from(p, r, lens_pair=lens, data_root=phase3_data_root)   # refuses on any drift (verify + recompute); data_root: tests/conftest.py
    assert {k: v["label"] for k, v in out["labels"].items()} == LABELS
    assert {k: v["licence"] for k, v in out["labels"].items()} == LICENCES
    assert out["k2"]["word"] == K2_WORD and out["readers_long_runs"] is READERS_LONG_RUNS
    assert out["k2"]["s1_trigger_readers"] == S1_TRIGGER
    assert all(v["all_identical"] for v in out["r0_linear_a_rerun"].values())

"""tests/test_noise_floor_landing.py — the committed seed-noise floor payloads (the 2026-10-04 registration block
"SEED-NOISE FLOOR READOUTS REGISTRATION" of docs/BLUEPRINT.md; F-27) reproduce their own conclusion through the
instrument's exact recompute surface from their state files and the committed summaries; the instrument on disk is the
one both payloads attest; the labels, readings and headline numbers are the ones that landed.

Landing test written 2026-10-04 after both registered runs were read; it pins the labels as landed, the instrument sha,
both state files' shas and the headline numbers at six decimals, so a changed payload, state file, summary, tool or
instrument flags here. Missing committed evidence FAILS, never skips. Nothing in this file imports torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_noise_floor as nf  # noqa: E402

# the clean tree both runs attest (the freeze commit itself: no commit fell between the freeze and the runs) and the
# instrument's raw-bytes sha (both payloads' provenance; the freeze record's 12-hex pin abb0bec95a22)
RUN_COMMIT = "906edfd41ac27b2fa54130634f48b6c72c7083dc"
INSTRUMENT_SHA256 = "abb0bec95a22f30c9a9e70c9592d335ee9f0a7ff0efa7e1d5d3c9a8b03e7522a"
LABEL, STAGE = "FLOOR-MATERIAL", "NOTE-STANDS"
READINGS = {"bar": "BAR-RESOLVED@210", "rule": "RULE-LEAKS@30"}
N_STATE_ROWS = 5000            # 1,000 subsets (or swap draws of the full set) at each of the five n
# the labels read on 2026-10-04 through --conclude-from on both populations, each state file's sha256 (raw bytes;
# results/** carries -text, so every checkout writes them as committed) and the headline numbers at six decimals
LANDED = {
    "noise_floor_k3.json": {
        "population": "k3", "role": "label", "seeds": [0, 1], "stage": STAGE,
        "state_sha256": "4032925543a3926f00cf90e5e30970548cd24183b63cc0210a1886958459aceb",
        "r": 0.42322, "f_one_30": 0.106, "f_one_30_se": 0.006463, "hw_210": 0.038538, "g_one_30": 0.0235,
        "f19_share": 0.116, "full_delta": 0.011597, "mom_seed_share": 0.527644,
    },
    "noise_floor_oq15.json": {
        "population": "oq15", "role": "replication", "seeds": [2, 3], "stage": None,
        "state_sha256": "d271650df468674ef6c4809abc65276068f7a87c1b3d7d73c16dd06070c470fe",
        "r": 0.417244, "f_one_30": 0.132, "f_one_30_se": 0.00697, "hw_210": 0.039796, "g_one_30": 0.0375,
        "f19_share": 0.141, "full_delta": 0.017473, "mom_seed_share": 0.545349,
    },
}


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _r6(x: float) -> float:
    return round(x, 6)


def test_instrument_on_disk_is_the_attested_one_and_stays_out_of_the_tools_chain():
    assert _sha_raw(ROOT / "tools" / "run_noise_floor.py") == INSTRUMENT_SHA256
    src = (ROOT / "tools" / "run_noise_floor.py").read_text(encoding="utf-8")
    assert "import torch" not in src and "from torch" not in src
    assert nf.registered_constants()["sizes"] == [30, 42, 84, 126, 210]


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_noise_floor_payloads_are_registered_runs_with_the_landed_labels(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed seed-noise floor evidence missing: {name}"   # absent FAILS, never skips
    want = LANDED[name]
    assert _sha_raw(state) == want["state_sha256"], f"{state.name} is not the committed state file"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == nf.REGISTERED
    assert payload["population"] == want["population"] and payload["role"] == want["role"] and payload["seeds"] == want["seeds"]
    prov = payload["provenance"]
    assert prov["smoke"] is False and prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == ""
    assert prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["constants"] == nf.registered_constants()
    assert prov["state_sha256"] == want["state_sha256"] and payload["n_state_rows"] == N_STATE_ROWS
    assert payload["precondition"]["holds"] and payload["precondition"]["n_checks"] == 19
    c = payload["conclusion"]
    assert c["label"] == LABEL and c["stage"] == want["stage"] and c["readings"] == READINGS and not c["void"]
    assert not c["within_two_se_of_threshold"]
    ro = payload["readouts"]
    assert _r6(ro["reliability"]["r"]) == want["r"]
    assert _r6(ro["per_n"]["30"]["f_one"]["rate"]) == want["f_one_30"]
    assert _r6(ro["per_n"]["30"]["f_one"]["se"]) == want["f_one_30_se"]
    assert _r6(ro["per_n"]["210"]["half_width"]["median"]) == want["hw_210"]
    assert _r6(ro["per_n"]["30"]["g_one"]["rate"]) == want["g_one_30"]
    assert ro["per_n"]["30"]["g_one_guard"]["rate"] == ro["per_n"]["30"]["g_one"]["rate"]   # the guard identity
    assert ro["guard_identity_holds_everywhere"]
    assert _r6(ro["f19"]["share_at_or_above"]) == want["f19_share"]
    assert _r6(ro["full_set_delta"]) == want["full_delta"]
    assert _r6(ro["decomposition"]["mom"]["share"]["seed_within_prompt"]) == want["mom_seed_share"]
    assert ro["decomposition"]["mom"]["all_nonnegative"] and ro["decomposition"]["identity_holds"]
    # the summaries, metas and prompt file the run read are the ones on disk (the recompute below re-checks them)
    for stem, info in prov["summaries"].items():
        assert _sha_raw(ROOT / info["path"]) == info["sha256"], f"{stem}.summary.json changed since the run"
    assert _sha_raw(ROOT / prov["prompts"]["path"]) == prov["prompts"]["sha256"]


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_noise_floor_payloads_reproduce_through_conclude_from(name):
    path = ROOT / "results" / "real" / name
    assert path.exists(), f"committed seed-noise floor evidence missing: {name}"
    out = nf.conclude_from(path)                      # refuses on any drift; ~25 s per population
    assert out["conclusion"]["label"] == LABEL and out["conclusion"]["readings"] == READINGS
    assert out["conclusion"]["stage"] == LANDED[name]["stage"]
    assert out["precondition"]["holds"]


def test_both_populations_agree_and_the_label_population_carries_the_stage():
    k = json.loads((ROOT / "results" / "real" / "noise_floor_k3.json").read_text(encoding="utf-8"))
    q = json.loads((ROOT / "results" / "real" / "noise_floor_oq15.json").read_text(encoding="utf-8"))
    assert k["conclusion"]["label"] == q["conclusion"]["label"] and k["conclusion"]["readings"] == q["conclusion"]["readings"]
    assert k["conclusion"]["stage"] == STAGE and q["conclusion"]["stage"] is None
    # the full-set deltas are the committed pooled differences the registration disclosed as known
    assert _r6(k["readouts"]["full_set_delta"]) == 0.011597 and _r6(q["readouts"]["full_set_delta"]) == 0.017473

"""tests/test_seed_replay_landing.py — the committed OQ-20 seed-replay payloads (docs/BLUEPRINT.md, "SEED-REPLAY OF THE
CONVERSION-VERDICT LEGS REGISTRATION", 2026-10-09; F-27's STAGE REPLAY line) are registered readouts of the frozen
instrument from the clean tree at the commit of the six seed-6 runs' sidecars, bound to the launch commit every seed-6
meta carries; their labels, readings and both stage words reproduce through --conclude-from and the tool's own stage-word
rule from the summaries on disk.

Landing test written 2026-10-10 after both readouts were read; it pins the labels, the readings, both stage words, the
launch and run commits, the instrument, payload, state and input-summary shas and the headline legs at six decimals, so
a changed payload, state file, summary or instrument flags here. Missing committed evidence FAILS, never skips. Nothing
in this file imports torch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import run_seed_replay as sr  # noqa: E402

LAUNCH_COMMIT = "b6d3701347e28373677f20dff5c4d36539549b05"          # the freeze commit the six seed-6 runs launched from (a clean clone)
RUN_COMMIT = "c62f03d6d366730eb863b2ee68735bcbb885b404"             # the clean tree the two readouts ran from (the sidecars' commit)
INSTRUMENT_SHA256 = "0b00f8dfd4cf2d879486ce289168ac7feb9c7879ee5b92fac1b427ef66c1adcb"
STAGE_WORD, FREE_STAGE_WORD = "SPREAD-COVERED", "FREE-SPREAD-COVERED"
N_STATE_ROWS = 8
LANDED = {
    "seed_replay_k3.json": {
        "population": "k3",
        "role": "label",
        "finding": "F-19",
        "seeds": {
            "new": 6,
            "vanilla_pairs": [
                [
                    0,
                    6
                ],
                [
                    1,
                    6
                ]
            ],
            "verdict": 1
        },
        "payload_sha256": "c0abad0de759b49ebeba47bedbccdc7c0b382687153652d90bc1c6ef6ff85f1d",
        "state_sha256": "562f1219ab5d2c19026f4cd479b46ae266932ec2d93cebeacae9c436d35bfe7c",
        "n_checks": 93,
        "labels": {
            "R2": "MUTUAL-COVERAGE",
            "R2_reading": "REPRODUCES",
            "R3": "BAR-NOT-CLEARED",
            "R4": "R-CONSISTENT",
            "R6": "MUTUAL-COVERAGE",
            "R6_reading": "REPRODUCES",
            "R7": "BAR-NOT-CLEARED-FREE",
            "R8": "NEAR-IDENTICAL-ARMS",
            "guard": "GUARD-HELD",
            "guard_free": "GUARD-FREE-HELD"
        },
        "r1": [
            0.01034,
            -0.009288,
            0.030521
        ],
        "r1_guard_margin": 0.017778,
        "r2_difference": [
            -0.003479,
            -0.033416,
            0.022758
        ],
        "r2_verdict_delta": 0.00686,
        "r5": [
            0.010109,
            -0.009724,
            0.030422
        ],
        "r6_difference": [
            -0.003135,
            -0.033327,
            0.023051
        ],
        "r6_verdict_delta": 0.006974,
        "r8_new": [
            0.000231,
            -0.000335,
            0.00104
        ],
        "r8_n_differing": {
            "new": 3,
            "verdict": 1
        },
        "r4_new_r": {
            "0_6": 0.41446,
            "1_6": 0.40355
        },
        "inputs": {
            "new_free": "9f5d5d07e92c5a9cec3b1244fd3fd505372280da759412f08037b92ee6adf8e2",
            "new_tel": "066d7c4e537001139c1182f4c837bf6c37fd31a6cbbd327b80bf4f035ee42bda",
            "new_vanilla": "8ed2d6529df863be86465a2f332d0474cbc8824f7251e88ce561722eb9d64ccd",
            "vanilla_seed0": "e1ffa17c1a88114460b6402a510dd23d3ee5c5a8e5dd1f524dc07e16859eeefa",
            "vanilla_seed1": "214944a5978f2519994bf1102977801c1d9d5033423551c2f61938e0ce45e99b",
            "verdict_free": "35d321acbbdd9b90d7c5f392d1d0838155169d80c8efbbc5bcae019e1550368e",
            "verdict_tel": "070c4614841fd0eb17f4950f1efb7d1177924b79eae8f347bfe3d650f83dd5c4",
            "verdict_vanilla": "214944a5978f2519994bf1102977801c1d9d5033423551c2f61938e0ce45e99b"
        }
    },
    "seed_replay_oq15.json": {
        "population": "oq15",
        "role": "replication",
        "finding": "F-21",
        "seeds": {
            "new": 6,
            "vanilla_pairs": [
                [
                    2,
                    6
                ],
                [
                    3,
                    6
                ]
            ],
            "verdict": 3
        },
        "payload_sha256": "a1ef30730baae4b53ca551b6c6a17f2f65f3730840b7e722adc35c0d45ab6b62",
        "state_sha256": "ca8c8a9285b6139e1f516220d21ad3c526056e7349301626eaa600671b3f03ac",
        "n_checks": 94,
        "labels": {
            "R2": "MUTUAL-COVERAGE",
            "R2_reading": "REPRODUCES",
            "R3": "BAR-NOT-CLEARED",
            "R4": "R-CONSISTENT",
            "R6": "MUTUAL-COVERAGE",
            "R6_reading": "REPRODUCES",
            "R7": "BAR-NOT-CLEARED-FREE",
            "R8": "DELTA-MOVES",
            "guard": "GUARD-HELD",
            "guard_free": "GUARD-FREE-HELD"
        },
        "r1": [
            -0.018029,
            -0.065168,
            0.028495
        ],
        "r1_guard_margin": 0.060652,
        "r2_difference": [
            0.020693,
            -0.04483,
            0.088277
        ],
        "r2_verdict_delta": 0.002664,
        "r5": [
            -0.053623,
            -0.107526,
            -0.002448
        ],
        "r6_difference": [
            -0.028223,
            -0.099002,
            0.042346
        ],
        "r6_verdict_delta": -0.081846,
        "r8_new": [
            0.035594,
            -0.009909,
            0.082906
        ],
        "r8_n_differing": {
            "new": 210,
            "verdict": 210
        },
        "r4_new_r": {
            "2_6": 0.469991,
            "3_6": 0.473553
        },
        "inputs": {
            "new_free": "d090183a85eb6ddb6da30aaf5385c0ceaa05402923f26f867a20a441521e1f3c",
            "new_tel": "b0282246c709cb446d27cf25305991353227651c253072865a61068b5bd2ce57",
            "new_vanilla": "25b9c94fc8af02b16d55101e2776d2e46280a1576fec9cf5edf971a309f1b798",
            "vanilla_seed2": "9277912939deb136699f235b84ef5e97bddb95aa6ee154fb87e9bbed47ccafa7",
            "vanilla_seed3": "e80d78ef1cd2f2c8a48d01e908dcddf20986475365c658258781d39b665a9613",
            "verdict_free": "272451b941ed480a5697cd8956d6f95a531ffe314226518a76ff47133d37d1b0",
            "verdict_tel": "c6d2dee548b5b5fc5e8c027ee7294ef65d0369798677bb5336fe9fe91c624871",
            "verdict_vanilla": "e80d78ef1cd2f2c8a48d01e908dcddf20986475365c658258781d39b665a9613"
        }
    }
}


def _sha_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _r6(x: float) -> float:
    return round(x, 6)


def test_instrument_on_disk_is_the_attested_one_and_imports_only_the_frozen_noise_floor_tool():
    assert _sha_raw(ROOT / "tools" / "run_seed_replay.py") == INSTRUMENT_SHA256
    src = (ROOT / "tools" / "run_seed_replay.py").read_text(encoding="utf-8")
    assert "import torch" not in src and "from torch" not in src
    assert "import e6_gate" not in src and "from e6_gate" not in src
    assert sr.NEW_SEED == 6 and sr.READOUT_NAMES == ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_seed_replay_payloads_are_registered_readouts_with_the_landed_labels(name):
    path = ROOT / "results" / "real" / name
    state = Path(str(path) + ".state.jsonl")
    assert path.exists() and state.exists(), f"committed OQ-20 evidence missing: {name}"   # absent FAILS, never skips
    want = LANDED[name]
    assert _sha_raw(path) == want["payload_sha256"] and _sha_raw(state) == want["state_sha256"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["registered"] == sr.REGISTERED and payload["smoke"] is False
    assert payload["population"] == want["population"] and payload["role"] == want["role"] and payload["finding"] == want["finding"]
    assert payload["seeds"] == want["seeds"] and payload["launch_commit"] == LAUNCH_COMMIT
    prov = payload["provenance"]
    assert prov["git_commit"] == RUN_COMMIT and prov["git_status_tracked"] == [] and prov["instrument_sha256"] == INSTRUMENT_SHA256
    assert prov["state_sha256"] == want["state_sha256"] and payload["n_state_rows"] == N_STATE_ROWS
    reg = sr.registered_constants()                   # the payload adds the draws actually used beside the registered ones
    assert {k: prov["constants"][k] for k in reg} == reg
    assert prov["constants"]["n_boot_used"] == reg["n_boot"] and prov["constants"]["reliability_draws_used"] == reg["reliability_draws"]
    assert payload["precondition"]["holds"] and payload["precondition"]["n_checks"] == want["n_checks"]
    assert payload["labels"] == want["labels"]
    ro = payload["readouts"]
    assert [_r6(ro["R1"][k]) for k in ("delta", "ci_lower", "ci_upper")] == want["r1"]
    assert _r6(ro["R1"]["budget_guard_margin"]) == want["r1_guard_margin"] and ro["R1"]["guard_holds"]
    assert [_r6(ro["R2"][k]) for k in ("difference", "ci_lower", "ci_upper")] == want["r2_difference"]
    assert _r6(ro["R2"]["delta_verdict"]) == want["r2_verdict_delta"]
    assert [_r6(ro["R5"][k]) for k in ("delta", "ci_lower", "ci_upper")] == want["r5"]
    assert [_r6(ro["R6"][k]) for k in ("difference", "ci_lower", "ci_upper")] == want["r6_difference"]
    assert _r6(ro["R6"]["delta_verdict"]) == want["r6_verdict_delta"]
    assert [_r6(ro["R8"]["new_leg"][k]) for k in ("delta", "ci_lower", "ci_upper")] == want["r8_new"]
    assert ro["R8"]["n_differing_prompts"] == want["r8_n_differing"]
    assert {k: _r6(v["reliability"]["r"]) for k, v in ro["R4"]["pairs"].items()} == want["r4_new_r"]
    assert all(v["committed_r_inside_ci"] for v in ro["R4"]["pairs"].values())
    # the summaries the readout read are the ones on disk (the recompute below re-checks them through the state header)
    for tag, info in prov["inputs"].items():
        assert info["summary_sha256"] == want["inputs"][tag]
        assert _sha_raw(ROOT / "results" / "real" / (info["stem"] + ".summary.json")) == info["summary_sha256"], f"{info['stem']} changed since the readout"
        assert _sha_raw(ROOT / "results" / "real" / (info["stem"] + ".meta.json")) == info["meta_sha256"], f"{info['stem']} meta changed since the readout"


@pytest.mark.parametrize("name", sorted(LANDED))
def test_committed_seed_replay_payloads_reproduce_through_conclude_from(name):
    path = ROOT / "results" / "real" / name
    assert path.exists(), f"committed OQ-20 evidence missing: {name}"
    out = sr.conclude_from(path)                      # refuses on any drift; seconds on CPU
    assert out["labels"] == LANDED[name]["labels"]


def test_both_stage_words_reproduce_through_the_tools_rule_from_the_committed_labels():
    k = json.loads((ROOT / "results" / "real" / "seed_replay_k3.json").read_text(encoding="utf-8"))
    q = json.loads((ROOT / "results" / "real" / "seed_replay_oq15.json").read_text(encoding="utf-8"))
    assert (k["role"], q["role"]) == ("label", "replication")
    assert sr.stage_word(k["labels"]["R2"], q["labels"]["R2"]) == STAGE_WORD
    assert sr.stage_word(k["labels"]["R6"], q["labels"]["R6"], "FREE-") == FREE_STAGE_WORD
    assert sr.stage_word_from(ROOT / "results" / "real" / "seed_replay_k3.json", ROOT / "results" / "real" / "seed_replay_oq15.json") == STAGE_WORD
    # K-3's R8 is fixed by the verdict seed's differing-prompt count, as the registration said before any run
    assert k["labels"]["R8"] == "NEAR-IDENTICAL-ARMS" and k["readouts"]["R8"]["n_differing_prompts"]["verdict"] < sr.R8_MIN_DIFFERING


def _table_rows(text: str):
    """Each Markdown table of `text` as (header_line_no, header_pipe_count, [(line_no, pipe_count), ...]). A table is a
    header line starting with a pipe followed by a delimiter row (cells of one or more dashes, optional colons); its body
    runs to the next blank line, as GitHub renders it. Only a backslash-escaped pipe is not a cell separator: GitHub splits
    on a pipe inside a backtick span too (the critic's second re-hash, 2026-10-10)."""
    import re
    lines = text.split("\n")
    tables, i = [], 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and re.fullmatch(r"\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?", lines[i + 1].strip()):
            def pipes(ln):
                return ln.replace("\\|", "").count("|")
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip():
                rows.append((j + 1, pipes(lines[j])))
                j += 1
            tables.append((i + 1, pipes(lines[i]), rows))
            i = j
        else:
            i += 1
    return tables


@pytest.mark.parametrize("rel", ["FINDINGS.md", "docs/FINDINGS_INDEX.md"])
def test_record_table_rows_carry_their_headers_pipe_count(rel):
    """An unescaped pipe inside a cell (the critic's re-hash round of 2026-10-10 found `|R5 - R1|` in two status cells) renders as
    an extra column and drops the cell's tail, so every row of every table in the two record files must count the header's pipes."""
    text = (ROOT / rel).read_bytes().decode("utf-8").replace("\r\n", "\n")
    tables = _table_rows(text)
    assert len(tables) == 1, f"{rel}: expected the one findings table, found {len(tables)}"   # a skipped or split table shows here
    bad = [(h, ln, n, hn) for h, hn, rows in tables for ln, n in rows if n != hn]
    assert bad == [], f"{rel}: rows whose pipe count differs from their header's (header line, row line, row pipes, header pipes): {bad}"

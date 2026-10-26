"""tools/e6_gate.py: the registered conversion gates recompute from the
committed summaries alone, bit-exact against the numbers FINDINGS.md
prints for F-19 and F-21 (the two conversion nulls)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import e6_gate  # noqa: E402

REAL = ROOT / "results" / "real"
needs_evidence = pytest.mark.skipif(
    not (REAL / "oq15c_verdict_s3_arm7.summary.json").exists(),
    reason="committed verdict summaries not present")


def _r6(x):
    return round(x, 6)


@needs_evidence
def test_f19_seed1_legs_reproduce_findings_text():
    res = e6_gate.evaluate("k3_s1")
    legs = res["legs"]
    # FINDINGS.md F-19: the three seed-1 gate legs at 6 dp
    assert [_r6(v) for v in (legs["arm4_vs_arm1"]["delta"], legs["arm4_vs_arm1"]["ci_lower"],
                             legs["arm4_vs_arm1"]["ci_upper"])] == [0.006860, -0.015024, 0.025572]
    assert [_r6(v) for v in (legs["arm4_vs_arm3"]["delta"], legs["arm4_vs_arm3"]["ci_lower"],
                             legs["arm4_vs_arm3"]["ci_upper"])] == [0.006974, -0.014909, 0.025690]
    assert [_r6(v) for v in (legs["arm4_vs_arm2"]["delta"], legs["arm4_vs_arm2"]["ci_lower"],
                             legs["arm4_vs_arm2"]["ci_upper"])] == [0.048863, -0.007393, 0.104327]
    # the arm-2 leg breaches the pairwise budget guard (dpe 1.317033 vs 1.275681 + 0.01)
    assert not legs["arm4_vs_arm2"]["guard_holds"]
    assert _r6(res["arms"]["4"]["drafted_per_emitted"]) == 1.317033
    assert res["win"] is False
    assert all(a["n_prompts"] == 210 for a in res["arms"].values())


@needs_evidence
def test_f21_seed3_legs_reproduce_findings_text():
    res = e6_gate.evaluate("oq15c_s3")
    legs = res["legs"]
    assert [_r6(v) for v in (legs["arm7_vs_arm1"]["delta"], legs["arm7_vs_arm1"]["ci_lower"],
                             legs["arm7_vs_arm1"]["ci_upper"])] == [0.002664, -0.044719, 0.046727]
    assert [_r6(v) for v in (legs["arm7_vs_arm2"]["delta"], legs["arm7_vs_arm2"]["ci_lower"],
                             legs["arm7_vs_arm2"]["ci_upper"])] == [-0.050425, -0.109388, 0.005772]
    assert [_r6(v) for v in (legs["arm7_vs_arm6"]["delta"], legs["arm7_vs_arm6"]["ci_lower"],
                             legs["arm7_vs_arm6"]["ci_upper"])] == [-0.081846, -0.132484, -0.035567]
    # full-precision pooled tokens/call as printed in F-21
    assert res["arms"]["1"]["tokens_per_call"] == 3.00827523663776
    assert res["arms"]["6"]["tokens_per_call"] == 3.0927852831273355
    assert res["arms"]["7"]["drafted_per_emitted"] == 1.2742347176420175
    # seed 3: every guard clears; every leg fails the point bar
    assert all(leg["guard_holds"] for leg in legs.values())
    assert res["win"] is False
    # and the pooled values equal the summaries' own fields bit-exactly
    for k, a in res["arms"].items():
        s = json.load(open(REAL / f"{a['stem']}.summary.json"))
        assert a["tokens_per_call"] == s["tokens_per_call"]
        assert a["drafted_per_emitted"] == s["drafted_per_emitted"]


def test_pairing_refusal_and_json_guard(tmp_path):
    a = {"emitted": np.ones(3), "blocks": np.ones(3), "drafted": np.ones(3),
         "prompt_idx": [0, 1, 2], "n_prompts": 3}
    b = dict(a, prompt_idx=[0, 1, 3])
    with pytest.raises(SystemExit, match="pairing is void"):
        e6_gate.pair(a, b)
    # a population whose summaries are absent is skipped, not fabricated
    assert e6_gate.evaluate("oq16a_s4", tmp_path) is None
    res = subprocess.run([sys.executable, str(ROOT / "tools" / "e6_gate.py"),
                          "--population", "k3_s1", "--json",
                          str(REAL / "e6_gate_should_refuse.json")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert res.returncode != 0 and "must not point into results/" in (res.stdout + res.stderr)
    assert not (REAL / "e6_gate_should_refuse.json").exists()

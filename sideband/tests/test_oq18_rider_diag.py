"""OQ-18 leak-rider diagnostic (tools/run_oq18_rider_diag.py): the registered
grid, the dependence-excess statistic (zero for a constant predictor, 1 -
sum p^2 for a perfect one), pairing refusals, bootstrap determinism, the
pinned branch rules, the wrap flags and histograms, and the out-path
refusals. No torch."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import run_oq18_rider_diag as rd  # noqa: E402


def _hist_cell(arm, seed, per_prompt, n_classes, maj=0, space=rd.SPACE_L3):
    """per_prompt: {prompt: (pred array, label array, wrap bool array)}"""
    h = {}
    for p, (pred, y, wrap) in per_prompt.items():
        h.update(rd.histograms(np.asarray(pred), np.asarray(y), np.full(len(pred), p),
                               np.asarray(wrap, dtype=bool), n_classes))
    acc = float(np.mean(np.concatenate([np.asarray(v[0]) == np.asarray(v[1]) for v in per_prompt.values()])))
    return {"cell": rd.cell_id(space, 2, arm, "linear", seed, True), "space": space, "offset": 2,
            "features": arm, "capacity": "linear", "seed": seed, "shuffled": True,
            "test_acc": acc, "best_epoch": 0, "majority_label": maj, "_hist": h}


def test_grid_is_the_registered_sixteen_cells():
    g = rd.build_grid()
    assert len(g) == 16
    assert g[:4] == [(rd.SPACE_L3, 2, a, "linear", 0, True) for a in rd.DIAG_ARMS]
    assert [c for c in g if c[0] == rd.SPACE_L3] == [(rd.SPACE_L3, 2, a, "linear", s, True)
                                                    for s in (0, 1, 2) for a in rd.DIAG_ARMS]
    assert [c for c in g if c[0] == rd.SPACE_L2] == [(rd.SPACE_L2, 2, a, "linear", 0, True)
                                                    for a in rd.DIAG_ARMS]
    assert all(c[5] and c[3] == "linear" and c[1] == 2 for c in g)


def test_wrap_flags_and_histograms():
    lengths = np.array([40, 25])
    rows = np.array([0, 0, 0, 1, 1])
    anchors = np.array([0, 20, 22, 0, 7])
    # label_index(a, 2) = a + 1; wraps where a + 1 + 17 >= length:
    # row 0 (40): anchor 22 -> 23 + 17 = 40 wraps, 20 -> 38 does not;
    # row 1 (25): anchor 7 -> 8 + 17 = 25 wraps
    w = rd.wrap_flags(anchors, rows, lengths, 2, 17)
    assert w.tolist() == [False, False, True, False, True]
    pred = np.array([0, 1, 1, 2, 0])
    y = np.array([0, 1, 2, 2, 2])
    prompts = np.array([7, 7, 7, 9, 9])
    h = rd.histograms(pred, y, prompts, w, 3)
    assert set(h) == {7, 9}
    assert h[7]["n"] == [2, 1] and h[7]["correct"] == [2, 0]
    assert h[7]["pred"] == [[1, 1, 0], [0, 1, 0]] and h[7]["label"] == [[1, 1, 0], [0, 0, 1]]
    assert h[9]["n"] == [1, 1] and h[9]["correct"] == [1, 0]


def _two_prompt_cells(n_classes=3):
    rng = np.random.default_rng(0)
    per = {}
    for p in range(30):
        y = rng.integers(0, n_classes, 50)
        wrap = np.zeros(50, dtype=bool)
        wrap[-3:] = True
        per[p] = (y, wrap)
    return per


def test_excess_is_zero_for_a_constant_predictor_and_one_minus_sum_p2_for_a_perfect_one():
    per = _two_prompt_cells()
    const = {p: (np.zeros(50, dtype=int), y, w) for p, (y, w) in per.items()}
    perfect = {p: (y.copy(), y, w) for p, (y, w) in per.items()}
    cells = {"a": [_hist_cell("a", 0, const, 3)], "fplus": [_hist_cell("fplus", 0, perfect, 3)]}
    st = rd.excess_stats(cells, 3, "all", n_boot=0)
    a = st["arms"]["a"]
    assert abs(a["E"]) < 1e-12 and abs(a["acc"] - a["chance"]) < 1e-12
    allY = np.concatenate([y for y, _ in per.values()])
    p = np.bincount(allY, minlength=3) / len(allY)
    f = st["arms"]["fplus"]
    assert abs(f["acc"] - 1.0) < 1e-12
    assert abs(f["E"] - (1.0 - float(p @ p))) < 1e-12
    pr = st["pairs"]["fplus-a"]
    assert abs(pr["d_E"] - (f["E"] - a["E"])) < 1e-12
    assert st["n_prompts"] == 30 and st["label_majority_rate"] == pytest.approx(float(p[0]))
    # the wrapped selection only sees the last three anchors of each prompt
    sw = rd.excess_stats(cells, 3, "wrapped", n_boot=0)
    assert sw["n_anchors"] == 90.0


def test_bootstrap_is_deterministic_and_pairing_is_refused_on_label_mismatch():
    per = _two_prompt_cells()
    rng = np.random.default_rng(1)
    noisy = {p: (np.where(rng.random(50) < 0.5, y, rng.integers(0, 3, 50)), y, w) for p, (y, w) in per.items()}
    const = {p: (np.zeros(50, dtype=int), y, w) for p, (y, w) in per.items()}
    cells = {"fplus": [_hist_cell("fplus", 0, const, 3)], "fplus_b": [_hist_cell("fplus_b", 0, noisy, 3)]}
    s1 = rd.excess_stats(cells, 3, "all", n_boot=200, seed=0)
    s2 = rd.excess_stats(cells, 3, "all", n_boot=200, seed=0)
    assert s1 == s2
    pr = s1["pairs"]["fplus_b-fplus"]
    assert pr["ci95_d_E"][0] <= pr["d_E"] <= pr["ci95_d_E"][1]
    assert pr["d_E"] > 0.2                      # half the predictions are the label
    # a seed mismatch between arms is refused, and so is a label mismatch
    with pytest.raises(SystemExit):
        rd.excess_stats({"fplus": [_hist_cell("fplus", 0, const, 3)],
                         "fplus_b": [_hist_cell("fplus_b", 1, noisy, 3)]}, 3, "all", n_boot=0)
    other = {p: (np.zeros(50, dtype=int), (y + 1) % 3, w) for p, (y, w) in per.items()}
    with pytest.raises(SystemExit):
        rd.excess_stats({"fplus": [_hist_cell("fplus", 0, const, 3)],
                         "fplus_b": [_hist_cell("fplus_b", 0, other, 3)]}, 3, "all", n_boot=0)
    # the expected cluster count is enforced
    with pytest.raises(SystemExit):
        rd.excess_stats(cells, 3, "all", n_boot=0, expected_clusters=29)


def _stats(d_acc_bf, d_e_bf, ci_bf, d_acc_br, d_e_br, ci_br, qb=0.9, qr=0.9):
    return {"pairs": {"fplus_b-fplus": {"d_acc": d_acc_bf, "d_E": d_e_bf, "ci95_d_E": ci_bf,
                                        "ci95_d_acc": [d_acc_bf - 0.01, d_acc_bf + 0.01]},
                      "fplus_b-fplus_r": {"d_acc": d_acc_br, "d_E": d_e_br, "ci95_d_E": ci_br,
                                          "ci95_d_acc": [d_acc_br - 0.01, d_acc_br + 0.01]}},
            "arms": {"fplus_b": {"q_majority": qb}, "fplus_r": {"q_majority": qr}}}


def test_amended_leg_is_coherent_with_branch_a():
    ok = rd.amended_leg({"d_E": 0.004, "ci95_d_E": [-0.002, 0.010]})
    assert not ok["fails"]
    assert rd.amended_leg({"d_E": 0.0101, "ci95_d_E": [-0.002, 0.020]})["fails"]        # band
    assert rd.amended_leg({"d_E": 0.006, "ci95_d_E": [0.001, 0.011]})["fails"]          # CI-clear, material
    assert not rd.amended_leg({"d_E": 0.004, "ci95_d_E": [0.001, 0.007]})["fails"]      # CI-clear, sub-material
    assert rd.amended_leg({"d_E": 0.010, "ci95_d_E": [-0.001, 0.021]})["fails"] is False  # exactly at the band passes
    assert rd.amended_leg({"d_E": 0.005, "ci95_d_E": [0.0001, 0.010]})["fails"]         # exactly material, CI-clear


def test_branch_rules_are_the_pinned_ones():
    pooled = _stats(0.012, 0.001, [-0.004, 0.006], 0.003, 0.001, [-0.004, 0.006])
    s0 = _stats(0.0132, 0.001, [-0.004, 0.006], 0.004, 0.002, [-0.004, 0.008])
    v = rd.branch(pooled, {0: s0, 1: _stats(0.004, 0, [-0.005, 0.005], 0, 0, [-0.005, 0.005])})
    assert v["branch"] == rd.BRANCH_B and v["mechanism"] == rd.MECH_DRIFT
    assert v["tie_reproduces"] and v["leg2_raw_per_seed"] == {0: 0.0132, 1: 0.004}
    assert v["x_raw_seed0"] == 0.004 and v["x_raw_sentence"].endswith("would also have passed")
    assert v["dE_br_seed0_half_width"] == pytest.approx(0.006)
    assert any(q.startswith("underpowered") for q in v["qualifiers"])      # half-width 0.006 > 0.005
    assert not any("EXPRESSED" in q for q in v["qualifiers"])
    # A: CI-clear and material twin excess; the wrap qualifier unless the non-wrapped selection fires too
    a_pooled = _stats(0.012, 0.008, [0.002, 0.014], 0.010, 0.006, [0.001, 0.011])
    v = rd.branch(a_pooled, {0: s0})
    assert v["branch"] == rd.BRANCH_A and v["mechanism"] == rd.MECH_TWIN
    assert v["qualifiers"] == ["concentrated on wrapped anchors (row-end / row-opening recall), not row-level content"]
    v = rd.branch(a_pooled, {0: s0}, _stats(0.012, 0.008, [0.002, 0.014], 0.010, 0.006, [0.001, 0.011]))
    assert v["branch"] == rd.BRANCH_A and v["qualifiers"] == []
    # a CI-clear but sub-material pooled twin excess is not A; within the band and passing at seed 0 it is B
    v = rd.branch(_stats(0.012, 0.008, [0.002, 0.014], 0.010, 0.004, [0.001, 0.009]), {0: s0})
    assert v["branch"] == rd.BRANCH_B and v["mechanism"] == rd.MECH_TWIN
    # C: pooled point above the band with a CI including zero
    v = rd.branch(_stats(0.012, 0.001, [-0.004, 0.006], 0.012, 0.011, [-0.002, 0.024]), {0: s0})
    assert v["branch"] == rd.BRANCH_C
    # C when the amended leg fails at seed 0 although the pooled is within the band (point above band)
    s0_hi = _stats(0.0132, 0.001, [-0.004, 0.006], 0.012, 0.011, [-0.004, 0.026])
    v = rd.branch(pooled, {0: s0_hi})
    assert v["branch"] == rd.BRANCH_C and "amended leg fails" in v["reason"]
    # C when the amended leg fails at seed 0 by the CI-clear-material clause
    s0_ci = _stats(0.0132, 0.001, [-0.004, 0.006], 0.009, 0.007, [0.001, 0.013])
    v = rd.branch(pooled, {0: s0_ci})
    assert v["branch"] == rd.BRANCH_C and "CI-clear and material" in v["reason"]
    # the X_raw sentence flips above the band
    s0_x = _stats(0.0132, 0.001, [-0.004, 0.006], 0.011, 0.002, [-0.004, 0.008])
    v = rd.branch(pooled, {0: s0_x})
    assert v["branch"] == rd.BRANCH_B and v["x_raw_sentence"].endswith("would still have fired")
    # compression and twin-anomaly qualifiers
    s0_q = _stats(0.0132, 0.001, [-0.004, 0.006], 0.004, 0.002, [-0.004, 0.008], qb=0.95, qr=0.90)
    neg_pooled = _stats(0.012, 0.001, [-0.004, 0.006], 0.003, -0.006, [-0.011, -0.001])
    v = rd.branch(neg_pooled, {0: s0_q})
    assert v["branch"] == rd.BRANCH_B
    assert any("EXPRESSED" in q for q in v["qualifiers"]) and any(q.startswith("twin anomaly") for q in v["qualifiers"])
    # T: the registered fire does not reproduce in-process
    v = rd.branch(pooled, {0: _stats(0.009, 0.001, [-0.004, 0.006], 0.003, 0.001, [-0.004, 0.006])})
    assert v["branch"] == rd.BRANCH_T
    # exactly at the band is not a fire (leg 2 is "<= band" passes)
    v = rd.branch(pooled, {0: _stats(0.010, 0.001, [-0.004, 0.006], 0.003, 0.001, [-0.004, 0.006])})
    assert v["branch"] == rd.BRANCH_T
    # DRIFT-DOMINANT: the raw fire's dependence excess is CI-clear negative
    v = rd.branch(_stats(0.012, -0.006, [-0.010, -0.001], 0.003, 0.001, [-0.004, 0.006]), {0: s0})
    assert v["mechanism"] == rd.MECH_DRIFT_DOM
    # INCOMPLETE without the twin
    v = rd.branch({"pairs": {"fplus_b-fplus": pooled["pairs"]["fplus_b-fplus"]}}, {0: s0})
    assert v["branch"] == rd.BRANCH_INCOMPLETE
    v = rd.branch(pooled, {})
    assert v["branch"] == rd.BRANCH_INCOMPLETE


def test_reproduction_tie():
    diag = [{"cell": "x|SHUFFLED", "test_acc": 0.5, "best_epoch": 3},
            {"cell": "y|SHUFFLED", "test_acc": 0.5 + 2e-9, "best_epoch": 3},
            {"cell": "z|SHUFFLED", "test_acc": 0.7, "best_epoch": 1}]
    committed = {"x|SHUFFLED": {"test_acc": 0.5, "best_epoch": 3},
                 "y|SHUFFLED": {"test_acc": 0.5, "best_epoch": 4}}
    r = rd.reproduction(diag, committed)
    assert set(r) == {"x|SHUFFLED", "y|SHUFFLED"}
    assert r["x|SHUFFLED"]["reproduced"] and not r["y|SHUFFLED"]["reproduced"]


def test_out_path_refusals_and_registration_document():
    with pytest.raises(SystemExit):
        rd.check_out("results/real/fullfree_coarse_s1.json", None)
    with pytest.raises(SystemExit):
        rd.check_out(rd.DIAG_OUT, "L3_concept_groups_v1|off2|a")
    p, reg = rd.check_out(rd.DIAG_OUT, None)
    assert reg and p.name == "oq18_rider_diag_s1.json"
    p, reg = rd.check_out("results/smoke/oq18_rider_diag_smoke.json", "L3")
    assert not reg
    assert rd.REGISTRATION_DOC.exists()
    text = rd.REGISTRATION_DOC.read_text(encoding="utf-8")
    for token in ("CONTENT-TRANSFER", "AMENDABLE", "INDETERMINATE-NOT-REPRODUCED", "MARGINAL-DRIFT",
                  "TWIN-MATCHED", "DRIFT-DOMINANT", "+0.005", "0.01", "post-hoc reroute around a fired kill",
                  rd.PRE_ROUND_REGISTRATION_SHA256):
        assert token in text
    assert rd.build_parser().parse_args([]).out == rd.DIAG_OUT
    assert rd.only_match("L3_concept_groups_v1|off2|a", "L3_concept_groups_v1|off2|a|linear|s0|SHUFFLED")
    assert not rd.only_match("L2", "L3_concept_groups_v1|off2|a|linear|s0|SHUFFLED")


@pytest.mark.skipif(not Path("results/real/oq18_rider_diag_s1.json").exists(),
                    reason="diagnostic payload not written yet")
def test_committed_diagnostic_payload_reproduces_its_verdict():
    import json
    payload = json.loads(Path("results/real/oq18_rider_diag_s1.json").read_text())
    assert payload["registration_sha256"] == rd._sha(rd.REGISTRATION_DOC)
    l3 = payload["per_space"][rd.SPACE_L3]
    v = rd.branch(l3["pooled"]["all"], {int(s): d["all"] for s, d in l3["per_seed"].items()},
                  l3["pooled"]["nonwrapped"])
    for k in ("branch", "mechanism", "qualifiers", "tie_reproduces", "dE_br_pooled", "dE_bf_pooled",
              "x_raw_seed0", "amended_leg_seed0"):
        assert v.get(k) == payload["verdict"].get(k)
    assert payload["pre_round_registration_sha256"] == rd.PRE_ROUND_REGISTRATION_SHA256
    assert not payload["partial"] and payload["n_cells"] == 16
    # pinned 2026-10-16 (lane C, image audit S7a-C-6) as the rider diagnostic landed on 2026-09-13
    # (OPEN_QUESTIONS.md OQ-18, docs/OQ18_RIDER_DIAGNOSTIC.md): the branch rules above reproduce
    # whatever the payload says; this line says what it says
    assert (payload["verdict"]["branch"], payload["verdict"]["mechanism"]) == ("AMENDABLE", "TWIN-MATCHED")
    assert payload["verdict"]["qualifiers"] == [] and payload["verdict"]["tie_reproduces"] is True

"""OQ-18 leak-rider POSITIVE CONTROL (tools/run_oq18_rider_poscontrol.py):
the leak block reads the slots at exactly the shuffled label's position;
the readout seats the leak cell in the aligned arm's seat and applies the
raw and amended legs; the pinned verdict rules; out-path refusals; the
registration document's tokens; the committed payload (when present)
reproduces its verdict. No torch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from sideband.probes import labels_for, slots_multi_hot  # noqa: E402
import run_oq18_rider_diag as rd  # noqa: E402
import run_oq18_rider_poscontrol as pc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_leak_anchors_are_the_shuffled_label_positions():
    lengths = np.array([40, 25, 18, 60])
    rows = np.array([0, 0, 1, 2, 3, 3])
    anchors = np.array([0, 30, 20, 0, 7, 58])
    la = pc.leak_anchors(anchors, rows, lengths, offset=2, shift=17)
    # (a + 2 - 1 + 17) mod length
    assert la.tolist() == [18, 8, 13, 0, 25, 16]
    # byte-for-byte the index labels_for reads: label = label_of_token[tokens[row, li]]
    T = 64
    tokens = np.arange(4 * T).reshape(4, T)
    label_of_token = np.arange(4 * T) * 3
    got = labels_for(tokens, rows, anchors, 2, label_of_token, shuffle_shift=17, lengths=lengths)
    assert np.array_equal(got, label_of_token[tokens[rows, la]])
    # wrapped anchors land in the row's first positions
    assert (la[(anchors + 18) >= lengths[rows]] < 17).all()


def test_leak_factory_reads_slots_at_the_leak_position_and_keeps_dims():
    rng = np.random.default_rng(0)
    n_rows, T, L, K, n_slots = 3, 30, 2, 3, 8   # (rows, T, layers, top_n) -1-padded ids, as the harvest
    slots = rng.integers(0, n_slots, (n_rows, T, L, K))
    slots[:, :, :, -1] = -1
    lengths = np.array([30, 22, 19])
    rows = np.array([0, 1, 2, 2])
    anchors = np.array([5, 20, 0, 17])

    class _Dummy:
        dim = 4

        def batch(self, idx):
            return np.zeros((len(idx), 4))

    def fplus_factory(r, a):
        return [_Dummy()]

    fac = pc.make_leak_factory(fplus_factory, slots, lengths, n_slots, offset=2, shift=17)
    blocks = fac(rows, anchors)
    assert len(blocks) == 2 and blocks[0].dim == 4 and blocks[1].dim == L * n_slots
    la = pc.leak_anchors(anchors, rows, lengths, 2, 17)
    idx = np.arange(len(rows))
    assert np.array_equal(blocks[1].batch(idx), slots_multi_hot(slots[rows, la], n_slots))
    # and NOT the aligned block's own position
    assert not np.array_equal(blocks[1].batch(idx), slots_multi_hot(slots[rows, anchors], n_slots))


def _cell(space, arm, per_prompt, n_classes, seed=0):
    h = {}
    for p, (pred, y, wrap) in per_prompt.items():
        h.update(rd.histograms(np.asarray(pred), np.asarray(y), np.full(len(pred), p),
                               np.asarray(wrap, dtype=bool), n_classes))
    acc = float(np.mean(np.concatenate([np.asarray(v[0]) == np.asarray(v[1]) for v in per_prompt.values()])))
    return {"cell": rd.cell_id(space, 2, arm, "linear", seed, True), "space": space, "offset": 2,
            "features": arm, "capacity": "linear", "seed": seed, "shuffled": True, "test_acc": acc,
            "best_epoch": 0, "majority_label": 0, "_hist": h}


def _prompts(n_classes=3, seed=0, n=60):
    rng = np.random.default_rng(seed)
    per = {}
    for p in range(30):
        y = rng.integers(0, n_classes, n)
        wrap = np.zeros(n, dtype=bool)
        wrap[-4:] = True
        per[p] = (y, wrap)
    return per


def test_space_readout_applies_both_legs_to_the_seated_leak():
    sp = rd.SPACE_L3
    per = _prompts()
    const = {p: (np.zeros(60, dtype=int), y, w) for p, (y, w) in per.items()}
    rng = np.random.default_rng(3)
    informed = {p: (np.where(rng.random(60) < 0.6, y, rng.integers(0, 3, 60)), y, w) for p, (y, w) in per.items()}
    ref = {"a": _cell(sp, "a", const, 3), "fplus": _cell(sp, "fplus", const, 3),
           "fplus_b": _cell(sp, "fplus_b", const, 3), "fplus_r": _cell(sp, "fplus_r", const, 3)}
    # a leak cell with real dependence: both legs fire
    leak = _cell(sp, "fplus_leak", informed, 3)
    out = pc.space_readout(ref, leak, 3, "all", n_boot=60, expected_clusters=30)
    assert out["amended_fires"] and out["raw_fires"]
    assert set(out["arms"]) == {"a", "fplus", "fplus_leak", "fplus_r"}
    assert out["dE_leak_r"] == pytest.approx(out["arms"]["fplus_leak"]["E"] - out["arms"]["fplus_r"]["E"])
    assert out["raw_leak"] == pytest.approx(out["arms"]["fplus_leak"]["acc"] - out["arms"]["fplus"]["acc"])
    assert out["amended_leg"]["fails"] is True
    # a constant leak cell: neither leg fires
    leak0 = _cell(sp, "fplus_leak", const, 3)
    out0 = pc.space_readout(ref, leak0, 3, "all", n_boot=60, expected_clusters=30)
    assert not out0["amended_fires"] and not out0["raw_fires"] and out0["dE_leak_r"] == pytest.approx(0.0)
    # the aligned reference reproduces the diagnostic's own pairing
    ar = pc.aligned_reference(ref, 3, "all", n_boot=60, expected_clusters=30)
    assert ar["dE_br"] == pytest.approx(0.0) and ar["leg2_raw"] == pytest.approx(0.0)
    # a wrongly labelled leak cell or a histogram-less reference is refused
    with pytest.raises(SystemExit):
        pc.space_readout(ref, _cell(sp, "fplus_b", informed, 3), 3, "all", n_boot=10, expected_clusters=30)
    bad = dict(ref)
    bad["fplus_r"] = {k: v for k, v in ref["fplus_r"].items() if k != "_hist"}
    with pytest.raises(SystemExit):
        pc.space_readout(bad, leak, 3, "all", n_boot=10, expected_clusters=30)


def test_verdict_rules_are_the_pinned_ones():
    L3, L2 = pc.CONTROL_SPACES
    f = lambda a, r: {"amended_fires": a, "raw_fires": r}  # noqa: E731
    assert pc.verdict({L3: f(True, True), L2: f(True, False)})["verdict"] == pc.V_CONFIRMED
    assert pc.verdict({L3: f(True, True), L2: f(False, False)})["verdict"] == pc.V_PARTIAL
    assert pc.verdict({L3: f(False, False), L2: f(False, False)})["verdict"] == pc.V_UNINFORMATIVE
    v = pc.verdict({L3: f(True, True), L2: f(False, True)})
    assert v["verdict"] == pc.V_FALSIFIED and "WITHDRAWN" in v["consequence"]
    # falsification outranks a confirmation at the other space
    assert pc.verdict({L3: f(False, True), L2: f(True, True)})["verdict"] == pc.V_FALSIFIED
    assert pc.verdict({L3: f(True, True)})["verdict"] == pc.V_INCOMPLETE


def test_out_path_refusals_and_parser():
    with pytest.raises(SystemExit):
        pc.check_out("results/real/fullfree_coarse_s1.json", None)
    with pytest.raises(SystemExit):
        pc.check_out(rd.DIAG_OUT, None)
    with pytest.raises(SystemExit):
        pc.check_out(pc.POS_OUT, "L3")
    assert pc.check_out(pc.POS_OUT, None)[1] is True
    assert pc.check_out("results/smoke/oq18_rider_poscontrol_smoke.json", "L3")[1] is False
    a = pc.build_parser().parse_args([])
    assert a.out == pc.POS_OUT and a.diag_payload == rd.DIAG_OUT and a.n_boot == rd.N_BOOT
    assert a.harvest == rd.DIAG_HARVEST


def test_registration_document_carries_the_pinned_tokens():
    t = (ROOT / "docs" / "OQ18_RIDER_POSCONTROL.md").read_text(encoding="utf-8")
    for tok in (pc.V_CONFIRMED, pc.V_FALSIFIED, pc.V_PARTIAL, pc.V_UNINFORMATIVE, pc.V_INCOMPLETE,
                "(a + off - 1 + 17) mod length[row]", "AMENDED-FIRES", "RAW-FIRES", "WITHDRAWN",
                "Honest prediction", "fplus_leak", "n_boot 2000", pc.POS_OUT):
        assert tok in t, tok


def test_committed_control_payload_reproduces_its_verdict():
    p = ROOT / pc.POS_OUT
    if not p.exists():
        pytest.skip("control payload not written yet")
    payload = json.loads(p.read_text())
    assert payload["registration_sha256"] == rd._sha(pc.REGISTRATION_DOC)
    assert not payload["partial"]
    flags = {sp: {"amended_fires": e["all"]["amended_fires"], "raw_fires": e["all"]["raw_fires"]}
             for sp, e in payload["per_space"].items()}
    v = pc.verdict(flags)
    assert v["verdict"] == payload["verdict"]["verdict"]
    # pinned 2026-10-16 (lane C, image audit S7a-C-6) as the control landed on 2026-09-13
    # (docs/OQ18_RIDER_POSCONTROL.md): the leak the amended leg was built to catch is caught at both spaces
    assert payload["verdict"]["verdict"] == "DOMINANCE-CONFIRMED-HERE"
    assert all(f["amended_fires"] and f["raw_fires"] for f in flags.values()) and len(flags) == 2
    for sp, e in payload["per_space"].items():
        leg = rd.amended_leg(e["all"]["pairs"]["fplus_leak-fplus_r"])
        assert leg["fails"] == e["all"]["amended_fires"]
        assert (e["all"]["raw_leak"] > rd.BAND) == e["all"]["raw_fires"]
    assert payload["provenance"]["arm_dims"]["fplus_leak"] == payload["provenance"]["arm_dims"]["fplus_b"]

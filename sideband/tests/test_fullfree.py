"""tools/run_fullfree.py (OQ-17 full-free existence re-test): the CI-safe
layer — the TOK block equals the committed DR-2 hashing rule, the new
blocks index the anchor coordinates exactly as the registered blocks do,
the h_a z-score uses TRAIN moments only (clip to train support), the twin
factories emit equal dims in the same block order, the grid is the
registered one bound to the source, the leak rider halts on either leg
(fresh or resumed cells), the reader-validity precondition and the pinned
labels are mechanical, --conclude-from refuses the wrong inputs, and (when
present) the committed payloads reproduce their own conclusion. No torch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_fullfree as rf  # noqa: E402
from run_probes import AnchorBlock, SlotsAnchorBlock, cell_id  # noqa: E402, F401  (SlotsAnchorBlock unused; cleanup owed)
from sideband.probes import slots_multi_hot  # noqa: E402


def test_tok_multi_hot_matches_recon_tok_block():
    from sideband.recon import FREETOK_BINS, tok_block

    rng = np.random.default_rng(0)
    ids = rng.integers(0, 128256, size=(40, 32)).astype(np.int64)
    ids[3, 5:] = -1              # padding
    ids[7, :] = -1               # empty row
    ids[9, :] = 17 + 2048 * np.arange(32)   # 32 ids that all hash to bin 17
    z = {"top_ids": ids, "gamma_used": np.zeros(40)}
    want = tok_block(z, FREETOK_BINS)
    got = rf.tok_multi_hot(ids, FREETOK_BINS)
    assert got.dtype == np.float32 and got.shape == (40, FREETOK_BINS)
    np.testing.assert_array_equal(got.astype(np.float64), want)
    assert got[7].sum() == 0 and got[9, 17] == 1.0 and got[9].sum() == 1.0
    assert got[3].sum() == len(np.unique(ids[3, :5] % FREETOK_BINS))


def test_new_blocks_read_the_anchor_coordinates_like_the_registered_blocks():
    rng = np.random.default_rng(1)
    N, T = 3, 10
    top_ids = rng.integers(0, 5000, size=(N, T, 32)).astype(np.int32)
    hidden = rng.normal(size=(N, T, 8)).astype(np.float16)
    rows = np.array([0, 1, 2, 2])
    anchors = np.array([0, 4, 9, 3])
    tok = rf.TokAnchorBlock(top_ids, rows, anchors, 64)
    hid = AnchorBlock(hidden, rows, anchors)
    idx = np.arange(4)
    np.testing.assert_array_equal(tok.batch(idx), rf.tok_multi_hot(top_ids[rows, anchors], 64))
    np.testing.assert_array_equal(hid.batch(idx), hidden[rows, anchors].astype(np.float32))
    # mutant: shifting the anchor by one changes what both blocks read
    tok2 = rf.TokAnchorBlock(top_ids, rows, (anchors + 1) % T, 64)
    assert not np.array_equal(tok2.batch(idx), tok.batch(idx))
    assert tok.dim == 64 and hid.dim == 8


def test_train_moments_use_train_rows_only_and_zscore_clips_to_train_support():
    rng = np.random.default_rng(3)
    N, T, d = 6, 12, 5
    hidden = rng.normal(size=(N, T, d)).astype(np.float16)
    hidden[:, :, 0] *= 40            # an outlier channel, the Llama pattern
    lengths = np.array([12, 7, 12, 3, 12, 12])
    split = np.array(["train", "train", "val", "train", "test", "train"])
    hidden[2, :, :] = 1e4            # a VAL row full of garbage must not leak in
    hidden[4, :, :] = -1e4           # nor a TEST row
    m = rf.train_moments(hidden, lengths, split)
    xs = np.concatenate([hidden[r, :lengths[r]].astype(np.float64)
                         for r in (0, 1, 3, 5)])
    np.testing.assert_allclose(m["mu"], xs.mean(0), rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(m["sd"], np.maximum(xs.std(0), rf.SD_FLOOR), rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(m["lo"], xs.min(0), rtol=1e-6)
    np.testing.assert_allclose(m["hi"], xs.max(0), rtol=1e-6)
    assert m["n_train_rows"] == 4 and m["n_train_positions"] == 12 + 7 + 3 + 12
    assert len(m["sha256"]) == 64 and m["mu"].dtype == np.float32
    # the block: the TEST garbage row is clipped to the train support first
    rows = np.array([0, 4])
    anchors = np.array([2, 5])
    hz = rf.HiddenZBlock(hidden, rows, anchors, m)
    out = hz.batch(np.arange(2))
    assert hz.dim == d and out.dtype == np.float32
    np.testing.assert_allclose(out[0], (hidden[0, 2].astype(np.float32) - m["mu"]) / m["sd"], rtol=1e-4)
    np.testing.assert_allclose(out[1], (m["lo"] - m["mu"]) / m["sd"], rtol=1e-4)  # clipped to lo
    # a constant channel gets the sd floor, not a division by zero
    hidden2 = hidden.copy()
    hidden2[:, :, 1] = 0.5
    m2 = rf.train_moments(hidden2, lengths, split)
    assert m2["sd"][1] == np.float32(rf.SD_FLOOR)
    assert np.isfinite(rf.HiddenZBlock(hidden2, rows, anchors, m2).batch(np.arange(2))).all()


def test_factories_equal_dims_same_order_and_shift_destroys_alignment():
    rng = np.random.default_rng(2)
    N, T, L, top, d = 4, 40, 4, 32, 6
    slots = rng.integers(0, 512, size=(N, T, L, top)).astype(np.int16)
    top_ids = rng.integers(0, 3000, size=(N, T, 32)).astype(np.int32)
    hidden = rng.normal(size=(N, T, d)).astype(np.float16)
    lengths = np.array([40, 40, 18, 30])
    split = np.array(["train", "train", "val", "test"])
    m = rf.train_moments(hidden, lengths, split)
    fac = rf.make_factories(top_ids, hidden, slots, lengths, 512, m, n_bins=64)
    rows = np.array([0, 1, 2, 3, 0])
    anchors = np.array([0, 39, 17, 4, 20])
    b_blocks = fac["fplus_b"](rows, anchors)
    n_blocks = fac["fplus_n"](rows, anchors)
    f_blocks = fac["fplus"](rows, anchors)
    assert [type(b).__name__ for b in b_blocks] == ["TokAnchorBlock", "HiddenZBlock", "SlotsAnchorBlock"]
    assert [type(b).__name__ for b in n_blocks] == [type(b).__name__ for b in b_blocks]
    assert [type(b).__name__ for b in f_blocks] == ["TokAnchorBlock", "HiddenZBlock"]
    assert sum(b.dim for b in b_blocks) == sum(b.dim for b in n_blocks) == 64 + d + L * 512
    idx = np.arange(len(rows))
    shifted = (anchors + rf.SLOT_SHIFT) % lengths[rows]
    assert np.all(shifted >= 0) and np.all(shifted < lengths[rows])
    assert np.all(shifted != anchors)  # every row here is longer than the shift
    # the twin's slots block is the aligned rule evaluated at the shifted anchors
    np.testing.assert_array_equal(n_blocks[2].batch(idx), slots_multi_hot(slots[rows, shifted], 512))
    np.testing.assert_array_equal(b_blocks[2].batch(idx), slots_multi_hot(slots[rows, anchors], 512))
    assert not np.array_equal(n_blocks[2].batch(idx), b_blocks[2].batch(idx))
    # the shared blocks are identical objects' worth of output in both twins
    np.testing.assert_array_equal(n_blocks[0].batch(idx), b_blocks[0].batch(idx))
    np.testing.assert_array_equal(n_blocks[1].batch(idx), b_blocks[1].batch(idx))


def test_grid_is_the_registered_one_and_offsets_bind_to_the_source():
    assert rf.offsets_for_tag("concept") == (2, 3) and rf.offsets_for_tag("olmoe") == (2,)
    with pytest.raises(SystemExit):
        rf.offsets_for_tag("other")
    g1 = rf.build_grid("L1_concept_k16", rf.offsets_for_tag("concept"))
    g3 = rf.build_grid("L1_olmoe_k16", rf.offsets_for_tag("olmoe"))
    assert g1[0][5] and g1[1][5] and g1[0][2] == "fplus" and g1[1][2] == "fplus_b"
    assert len([c for c in g1 if not c[5]]) == 27 and len(g1) == 29
    assert len([c for c in g3 if not c[5]]) == 18 and len(g3) == 20
    assert {c[3] for c in g1 if c[1] == 3} == {"mlp256"}
    assert {c[3] for c in g1 if c[1] == 2 and not c[5]} == {"linear", "mlp256"}
    assert {c[4] for c in g1 if not c[5]} == {0, 1, 2}
    with pytest.raises(SystemExit):
        rf.build_grid("L1_concept_k16", (1, 2))
    assert len({cell_id(*c) for c in g1}) == len(g1)


def _cell(space, off, feats, cap, seed, acc, maj=0.59, shuffled=False):
    return {"cell": cell_id(space, off, feats, cap, seed, shuffled), "space": space,
            "offset": off, "features": feats, "capacity": cap, "seed": seed,
            "shuffled": shuffled, "test_acc": acc, "majority_rate_test": maj}


def test_leak_rider_two_legs_halt_and_need_the_committed_cell():
    sp = "L1_concept_k16"
    committed = [_cell(sp, 2, "a", "linear", 0, 0.5889, shuffled=True)]
    sf = _cell(sp, 2, "fplus", "linear", 0, 0.585, shuffled=True)
    sb = _cell(sp, 2, "fplus_b", "linear", 0, 0.590, shuffled=True)
    r = rf.rider_check([sf], committed, sp)
    assert r["leg1_pass"] and "leg2_pass" not in r and r["pass"] is False
    r = rf.rider_check([sf, sb], committed, sp)
    assert r["pass"] and r["leg1_pass"] and r["leg2_pass"]
    with pytest.raises(SystemExit, match="leg 1"):
        rf.rider_check([_cell(sp, 2, "fplus", "linear", 0, 0.60, shuffled=True)], committed, sp)
    with pytest.raises(SystemExit, match="leg 2"):
        rf.rider_check([sf, _cell(sp, 2, "fplus_b", "linear", 0, 0.5961, shuffled=True)], committed, sp)
    with pytest.raises(SystemExit, match="committed"):
        rf.rider_check([sf], [], sp)
    with pytest.raises(SystemExit, match="partner"):
        rf.rider_check([sb], committed, sp)
    assert rf.committed_shuffled_a(committed, "L1_olmoe_k16") is None


def _row(space, off, cap, margin, lo, hi, seeds=(0.01, 0.01, 0.01), pair=rf.GATE_PAIR,
         n_seeds=3, n_clusters=30):
    return {"space": space, "offset": off, "capacity": cap, "margin": margin,
            "ci95": [lo, hi], "per_seed_margin": {i: s for i, s in enumerate(seeds)},
            "pair": pair, "n_seeds": n_seeds, "n_clusters": n_clusters}


def test_reader_validity_precondition():
    sp = "L1_concept_k16"
    good = [_cell(sp, 2, arm, "mlp256", s, 0.62) for arm in rf.ARMS for s in rf.SEEDS]
    mf_ok = [_row(sp, 2, "mlp256", 0.01, 0.005, 0.015, pair="fplus-a")]
    r = rf.reader_validity(good, mf_ok, sp)
    assert r["ok"] and r["complete"] and r["floor_ok"] and r["mf_ok"]
    assert r["min_acc_minus_floor"] == pytest.approx(0.03)
    bad_floor = good[:-1] + [_cell(sp, 2, "fplus_n", "mlp256", 2, 0.58)]
    assert not rf.reader_validity(bad_floor, mf_ok, sp)["ok"]
    assert rf.reader_validity(good[:-1] + [_cell(sp, 2, "fplus_n", "mlp256", 2, 0.5895)], mf_ok, sp)["ok"]
    mf_bad = [_row(sp, 2, "mlp256", -0.01, -0.02, -0.001, pair="fplus-a")]
    assert not rf.reader_validity(good, mf_bad, sp)["ok"]
    assert not rf.reader_validity(good[:5], mf_ok, sp)["complete"]
    assert not rf.reader_validity(good, [], sp)["ok"]


def test_gate_and_pinned_labels_are_mechanical():
    sp = "L1_concept_k16"
    fire = _row(sp, 2, "mlp256", 0.012, 0.006, 0.018)
    quiet = _row(sp, 2, "mlp256", 0.002, -0.003, 0.0049)
    straddle = _row(sp, 2, "mlp256", 0.004, -0.002, 0.009)
    assert rf.gate_fires(fire) and not rf.gate_fires(quiet) and not rf.gate_fires(straddle)
    assert not rf.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, seeds=(0.02, 0.02, -0.001)))
    assert not rf.gate_fires(_row(sp, 2, "mlp256", 0.004, 0.001, 0.007))       # immaterial
    assert not rf.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair="fplus_b-fplus"))
    assert not rf.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, n_seeds=1))
    assert not rf.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, n_clusters=29))
    assert not rf.gate_fires(None)
    lin_q = _row(sp, 2, "linear", 0.001, -0.002, 0.004)
    off3_q = _row(sp, 3, "mlp256", 0.0, -0.004, 0.0045)
    assert rf.source_label(fire, fire) == rf.LABEL_SURVIVES
    assert rf.source_label(fire, quiet) == rf.LABEL_SPLIT
    assert rf.source_label(quiet, fire) == rf.LABEL_SPLIT
    assert rf.source_label(None, fire) == rf.LABEL_INCOMPLETE
    assert rf.source_label(fire, fire, reader_ok=(True, False)) == rf.LABEL_READER_INVALID
    # ABSORBED needs EVERY D row's CI upper below the floor on both harvests
    rows_quiet = [quiet, lin_q, off3_q]
    assert rf.source_label(quiet, quiet, rows_quiet, rows_quiet) == rf.LABEL_ABSORBED
    assert rf.source_label(quiet, quiet, rows_quiet, [straddle, lin_q, off3_q]) == rf.LABEL_NOT_SHOWN
    assert rf.source_label(straddle, straddle, [straddle], [straddle]) == rf.LABEL_NOT_SHOWN
    assert rf.source_label(quiet, quiet) == rf.LABEL_NOT_SHOWN   # no rows given: never ABSORBED
    off3 = _row(sp, 3, "mlp256", 0.012, 0.006, 0.018)
    off3_straddle = _row(sp, 3, "mlp256", 0.004, -0.002, 0.010)
    assert rf.horizon_note(None, None) is None
    assert rf.horizon_note(off3, None) == "OFF3-INCOMPLETE"
    assert rf.horizon_note(off3, off3) == "OFF3-SURVIVES"
    assert rf.horizon_note(off3_q, off3_q) == "OFF3-ABSORBED"
    assert rf.horizon_note(off3_q, off3_straddle) == "OFF3-NOT-SHOWN"   # a straddle never narrows
    assert rf.horizon_note(off3_straddle, off3_straddle) == "OFF3-NOT-SHOWN"
    assert rf.horizon_note(off3, off3_q) == "OFF3-SPLIT"
    assert rf.expected_d_rows(sp) == 3 and rf.expected_d_rows("L1_olmoe_k16") == 2
    rows = [fire, _row(sp, 2, "linear", 0.03, 0.02, 0.04), off3]
    assert rf.gate_row(rows, sp) is fire
    assert rf.gate_row(rows, sp, capacity="linear")["margin"] == 0.03
    assert rf.gate_row(rows, sp, offset=3) is off3
    assert rf.gate_row(rows, "L1_olmoe_k16") is None


def _payload(space, harvest, sha, rows, mt=None, partial=False, rider_pass=True,
             reader_ok=True, offsets=None, out=None):
    tag = "concept" if space == "L1_concept_k16" else "olmoe"
    if out is None:
        out = ("fullfree_s1" if tag == "concept" else "fullfree_s3") + \
              ("_r" if harvest.endswith("_r") else "") + ".json"
    return {"gate": {"space": space}, "harvest": harvest, "partial": partial,
            "offsets": list(offsets if offsets is not None else rf.OFFSETS_OF_TAG[tag]),
            "rider": {"pass": rider_pass}, "reader_valid": {"ok": reader_ok},
            "d_fplus_b_vs_fplus_n": rows, "mt_fplus_b_vs_fplus": mt or [],
            "provenance": {"harvest_npz_sha256": {"x.npz": sha},
                           "args": {"out": "results/real/" + out}}}


def _s1_rows(space, gate):
    """A complete S1 D-row set: the gate row plus quiet linear off2 and off3 rows."""
    return [gate, _row(space, 2, "linear", 0.001, -0.002, 0.004),
            _row(space, 3, "mlp256", 0.0, -0.004, 0.0045)]


def test_conclude_refusals_and_license():
    sp = "L1_concept_k16"
    fire = _row(sp, 2, "mlp256", 0.012, 0.006, 0.018)
    rows = _s1_rows(sp, fire)
    mt_neg = [_row(sp, 2, "mlp256", -0.01, -0.02, -0.002, pair="fplus_b-fplus")]
    mt_pos = [_row(sp, 2, "mlp256", 0.01, 0.002, 0.02, pair="fplus_b-fplus")]
    p = _payload(sp, "results/real/harvest_shadow", "aa", rows, mt_pos)
    r = _payload(sp, "results/real/harvest_shadow_r", "bb", rows, mt_pos)
    out = rf.conclude(p, r)
    assert out["label"] == rf.LABEL_SURVIVES and out["survives_license"] == "full"
    assert out["horizon_off3"] == "OFF3-ABSORBED"
    assert out["gate_fires"] == {"primary": True, "replication": True}
    r_neg = _payload(sp, "results/real/harvest_shadow_r", "bb", rows, mt_neg)
    assert rf.conclude(p, r_neg)["survives_license"] == "equal-dims-only"
    r_no_mt = _payload(sp, "results/real/harvest_shadow_r", "bb", rows, [])
    assert rf.conclude(p, r_no_mt)["survives_license"] == "equal-dims-only"  # missing Mt is not >= 0
    with pytest.raises(SystemExit, match="SAME harvest"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow_r", "aa", rows))
    with pytest.raises(SystemExit, match="different sources"):
        rf.conclude(p, _payload("L1_olmoe_k16", "results/real/harvest_moe_r", "bb", rows[:2]))
    with pytest.raises(SystemExit, match="PARTIAL"):
        rf.conclude(_payload(sp, "results/real/harvest_shadow", "aa", rows, partial=True), r)
    with pytest.raises(SystemExit, match="rider"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow_r", "bb", rows, rider_pass=False))
    with pytest.raises(SystemExit, match="offsets"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow_r", "bb", rows, offsets=[2]))
    with pytest.raises(SystemExit, match="registered primary harvest"):
        rf.conclude(_payload(sp, "results/smoke/whatever", "aa", rows), r)
    with pytest.raises(SystemExit, match="registered replication harvest"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow", "bb", rows,
                                out="fullfree_s1_r.json"))
    with pytest.raises(SystemExit, match="not the registered"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow_r", "bb", rows,
                                out="fullfree_smoke.json"))
    with pytest.raises(SystemExit, match="INCOMPLETE"):
        rf.conclude(p, _payload(sp, "results/real/harvest_shadow_r", "bb", [fire]))
    inv = _payload(sp, "results/real/harvest_shadow_r", "bb", rows, reader_ok=False)
    assert rf.conclude(p, inv)["label"] == rf.LABEL_READER_INVALID
    # S3 pair with the registered offsets (two D rows)
    s3 = "L1_olmoe_k16"
    f3 = _row(s3, 2, "mlp256", 0.012, 0.006, 0.018)
    q3 = _row(s3, 2, "mlp256", 0.001, -0.003, 0.004)
    lin3 = _row(s3, 2, "linear", 0.001, -0.003, 0.004)
    out3 = rf.conclude(_payload(s3, "results/real/harvest_moe", "cc", [q3, lin3]),
                       _payload(s3, "results/real/harvest_moe_r", "dd", [q3, lin3]))
    assert out3["label"] == rf.LABEL_ABSORBED and out3["all_d_ci_uppers_below_floor"]
    out3b = rf.conclude(_payload(s3, "results/real/harvest_moe", "cc", [f3, lin3]),
                        _payload(s3, "results/real/harvest_moe_r", "dd", [q3, lin3]))
    assert out3b["label"] == rf.LABEL_SPLIT
    with pytest.raises(SystemExit, match="INCOMPLETE"):
        rf.conclude(_payload(s3, "results/real/harvest_moe", "cc", [q3]),
                    _payload(s3, "results/real/harvest_moe_r", "dd", [q3, lin3]))


def test_parser_defaults_are_the_s1_instrument():
    d = vars(rf.build_parser().parse_args([]))
    assert d["harvest"] == "results/real/harvest_shadow"
    assert d["out"] == "results/real/fullfree_s1.json"
    assert d["space_tag"] == "concept" and d["n_slots"] == 512
    assert d["parent_finding"] == "F-15" and "offsets" not in d
    assert d["phase3_state"] == "results/real/probes_s1.json.state.jsonl"
    assert d["conclude_from"] is None
    for arg, name in (("buckets16", "buckets_k16.json"), ("glue16", "glue_k16.json"),
                      ("buckets512", "buckets_k512.json"), ("glue512", "glue_k512.json"),
                      ("groups", "concept_groups_v1.json")):
        assert d[arg].endswith(name)
    assert rf.GATE_OFFSET == 2 and rf.GATE_CAPACITY == "mlp256" and rf.MATERIALITY == 0.005
    assert rf.R2_BAND == 0.01 and rf.READER_FLOOR_TOL == 0.001


@pytest.mark.parametrize("pair", [("fullfree_s1.json", "fullfree_s1_r.json"),
                                  ("fullfree_s3.json", "fullfree_s3_r.json")])
def test_committed_payloads_reproduce_their_conclusion(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("registered OQ-17 payloads not present")
    pp, rp = (json.loads(p.read_text()) for p in paths)
    n_cells = 27 if "s1" in pair[0] else 18
    for d in (pp, rp):
        assert d["partial"] is False and d["n_cells"] == n_cells
        assert d["rider"]["pass"] and d["rider"]["leg1_pass"] and d["rider"]["leg2_pass"]
        assert d["provenance"]["arm_dims_total"]["fplus_b"] == d["provenance"]["arm_dims_total"]["fplus_n"]
        assert d["gate"]["fires"] == (d["reader_valid"]["ok"] and rf.gate_fires(d["gate"]["row"]))
        assert all(m["n_clusters"] == 30 and m["n_seeds"] == 3 for m in d["d_fplus_b_vs_fplus_n"])
        assert len(d["standardization"]["moments_sha256"]) == 64
    out = rf.conclude(pp, rp)
    assert out["label"] in (rf.LABEL_SURVIVES, rf.LABEL_ABSORBED, rf.LABEL_NOT_SHOWN,
                            rf.LABEL_SPLIT, rf.LABEL_READER_INVALID)

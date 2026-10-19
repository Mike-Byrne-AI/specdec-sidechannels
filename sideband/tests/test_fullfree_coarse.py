"""tools/run_fullfree_coarse.py (OQ-18 coarse-label full-free re-test at
L2 / L3): the CI-safe layer — offsets bind per space to the F-15 / F-17
firing sets, the grid is the registered one (rider first with a FRESH
shuffled (a) reference, fresh (a) mlp256 cells, off2 at both capacities,
further offsets at mlp256), the grid is refused against committed cell ids
and missing committed bases, the per-seed factories emit equal dims in the
same block order with the corrected twin reading another prompt's row, the
leak rider halts on either leg, the three-leg precondition (including the
Mf_x collapse leg) and the per-space labels / horizons / licenses are
mechanical, --conclude-from refuses the wrong inputs, and (when present)
the committed payloads reproduce their own conclusion. No torch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_fullfree_coarse as rc  # noqa: E402
import run_fullfree as rf  # noqa: E402
from run_probes import cell_id  # noqa: E402
from sideband.probes import slots_multi_hot  # noqa: E402

S1 = ("L2_concept_k512", "L3_concept_groups_v1")
S3 = ("L2_olmoe_k512", "L3_olmoe_groups_v1")


def test_offsets_and_spaces_bind_to_the_firing_sets():
    assert rc.registered_spaces("concept") == S1 and rc.registered_spaces("olmoe") == S3
    assert rc.offsets_for_space(S1[0]) == (2, 3) and rc.offsets_for_space(S1[1]) == (2, 3)
    assert rc.offsets_for_space(S3[0]) == (2, 3) and rc.offsets_for_space(S3[1]) == (2, 3, 4)
    assert rc.tag_of_space(S1[1]) == "concept" and rc.tag_of_space(S3[0]) == "olmoe"
    with pytest.raises(SystemExit):
        rc.offsets_for_space("L1_concept_k16")           # L1 is OQ-17's, not this test's
    with pytest.raises(SystemExit):
        rc.offsets_for_space("L2_concept_k512", {"L2_concept_k512": (1, 2)})
    with pytest.raises(SystemExit):
        rc.offsets_for_space("L2_concept_k512", {"L2_concept_k512": (3,)})   # must start at the gate offset
    with pytest.raises(SystemExit):
        rc.tag_of_space("L2_other_k512")
    assert rc.expected_d_rows(S1[0]) == 3 and rc.expected_d_rows(S3[1]) == 4
    assert rc.GATE_PAIR == "fplus_b-fplus_r" and rc.TWIN_ARM == "fplus_r"
    assert rc.PAIR_MFX == "fplus-a_lin" and rc.LIN_BASE == "a_lin"


def test_grid_is_the_registered_one():
    g1 = rc.build_grid(rc.registered_spaces("concept"))
    g3 = rc.build_grid(rc.registered_spaces("olmoe"))
    assert len(g1) == 66 and len([c for c in g1 if not c[5]]) == 60
    assert len(g3) == 75 and len([c for c in g3 if not c[5]]) == 69
    # per space: rider first (fresh shuffled (a), shuffled fplus, shuffled fplus_b)
    for g, spaces in ((g1, S1), (g3, S3)):
        for sp in spaces:
            block = [c for c in g if c[0] == sp]
            assert [(c[2], c[3], c[4], c[5]) for c in block[:3]] == [
                ("a", "linear", 0, True), ("fplus", "linear", 0, True), ("fplus_b", "linear", 0, True)]
            fresh_a = [c for c in block if c[2] == "a" and not c[5]]
            assert [(c[1], c[3]) for c in fresh_a] == [(2, "mlp256")] * 3 and {c[4] for c in fresh_a} == {0, 1, 2}
            assert {c[3] for c in block if c[1] > 2} == {"mlp256"}
            assert {c[3] for c in block if c[1] == 2 and not c[5] and c[2] != "a"} == {"linear", "mlp256"}
            assert {c[2] for c in block if not c[5] and c[2] != "a"} == set(rc.ARMS)
            assert sorted({c[1] for c in block}) == list(rc.offsets_for_space(sp))
    assert [c[0] for c in g1][:33] == [S1[0]] * 33 and [c[0] for c in g1][33:] == [S1[1]] * 33
    assert len([c for c in g3 if c[0] == S3[1]]) == 42
    assert len({cell_id(*c) for c in g1}) == len(g1)
    with pytest.raises(SystemExit):
        rc.build_grid(("L2_concept_k512",), {"L2_concept_k512": (1, 2)})


def _committed_ids(spaces, offsets=(1, 2, 3, 4), seeds=(0, 1, 2)):
    ids = set()
    for sp in spaces:
        for off in offsets:
            for s in seeds:
                for f in ("a", "b", "c"):
                    ids.add(cell_id(sp, off, f, "linear", s))
    return ids


def test_grid_is_refused_against_committed_ids_and_missing_bases():
    spaces = rc.registered_spaces("olmoe")
    grid = rc.build_grid(spaces)
    ids = _committed_ids(spaces)
    rc.check_grid_against_committed(grid, ids, spaces)                     # the committed inventory
    with pytest.raises(SystemExit):                                         # a collision with a committed id
        rc.check_grid_against_committed(grid, ids | {cell_id(spaces[0], 2, "fplus", "linear", 0)}, spaces)
    with pytest.raises(SystemExit):                                         # a missing committed (c) at seed 2
        rc.check_grid_against_committed(grid, ids - {cell_id(spaces[1], 4, "c", "linear", 2)}, spaces)
    with pytest.raises(SystemExit):                                         # a missing committed (a) at off3
        rc.check_grid_against_committed(grid, ids - {cell_id(spaces[0], 3, "a", "linear", 1)}, spaces)


def _layout():
    """A tiny synthetic harvest: 4 prompts x 2 rows, all train, unequal lengths."""
    rng = np.random.default_rng(2)
    N, T, L, top, d = 8, 40, 4, 32, 6
    slots = rng.integers(0, 512, size=(N, T, L, top)).astype(np.int16)
    top_ids = rng.integers(0, 3000, size=(N, T, 32)).astype(np.int32)
    hidden = rng.normal(size=(N, T, d)).astype(np.float16)
    lengths = np.array([40, 40, 18, 30, 40, 25, 40, 33])
    prompt_idx = np.array([0, 0, 1, 1, 2, 2, 3, 3])
    split = np.array(["train"] * N)
    return slots, top_ids, hidden, lengths, prompt_idx, split, (L, d)


def test_factories_per_seed_equal_dims_same_order_and_twin_reads_another_prompt():
    slots, top_ids, hidden, lengths, prompt_idx, split, (L, d) = _layout()
    m = rf.train_moments(hidden, lengths, split)
    perms = {s: rc.derangement_by_prompt(prompt_idx, split, s) for s in rc.SEEDS}
    fac = rc.make_factories(top_ids, hidden, slots, lengths, 512, m, perms, n_bins=64)
    assert set(fac) == {(arm, s) for arm in rc.ARMS for s in rc.SEEDS}
    rows = np.array([0, 1, 2, 3, 0, 7])
    anchors = np.array([0, 39, 17, 4, 20, 32])
    idx = np.arange(len(rows))
    for seed in rc.SEEDS:
        b_blocks = fac[("fplus_b", seed)](rows, anchors)
        r_blocks = fac[("fplus_r", seed)](rows, anchors)
        f_blocks = fac[("fplus", seed)](rows, anchors)
        assert [type(b).__name__ for b in b_blocks] == ["TokAnchorBlock", "HiddenZBlock", "SlotsAnchorBlock"]
        assert [type(b).__name__ for b in r_blocks] == ["TokAnchorBlock", "HiddenZBlock", "OtherRowSlotsBlock"]
        assert [type(b).__name__ for b in f_blocks] == ["TokAnchorBlock", "HiddenZBlock"]
        assert sum(b.dim for b in b_blocks) == sum(b.dim for b in r_blocks) == 64 + d + L * 512
        np.testing.assert_array_equal(r_blocks[0].batch(idx), b_blocks[0].batch(idx))
        np.testing.assert_array_equal(r_blocks[1].batch(idx), b_blocks[1].batch(idx))
        np.testing.assert_array_equal(b_blocks[2].batch(idx), slots_multi_hot(slots[rows, anchors], 512))
        other = perms[seed][rows]
        assert np.all(prompt_idx[other] != prompt_idx[rows])          # another prompt, always
        oa = anchors % lengths[other]
        np.testing.assert_array_equal(r_blocks[2].batch(idx), slots_multi_hot(slots[other, oa], 512))
        assert not np.array_equal(r_blocks[2].batch(idx), b_blocks[2].batch(idx))
    # different train seeds -> different derangements (the diagnostic's rule)
    assert not np.array_equal(perms[0], perms[1])
    with pytest.raises(SystemExit):
        rc.make_factories(top_ids, hidden, slots, lengths, 512, m, {0: perms[0]}, n_bins=64)


def _cell(space, off, feats, cap, seed, acc, maj=0.41, shuffled=False, best_epoch=0, clusters=None):
    c = {"cell": cell_id(space, off, feats, cap, seed, shuffled), "space": space,
         "offset": off, "features": feats, "capacity": cap, "seed": seed,
         "shuffled": shuffled, "test_acc": acc, "majority_rate_test": maj,
         "best_epoch": best_epoch}
    if clusters is not None:
        c["_clusters"] = clusters
    return c


def test_relabel_committed_linear_a_copies_only_the_gate_offset_cells():
    sp, other = S1
    clusters = {"0": (3, 5), "1": (2, 5)}
    p3 = [_cell(sp, 2, "a", "linear", s, 0.42, clusters=clusters) for s in rc.SEEDS]
    p3 += [_cell(sp, 3, "a", "linear", 0, 0.41, clusters=clusters),          # wrong offset
           _cell(sp, 2, "c", "linear", 0, 0.44, clusters=clusters),          # wrong feats
           _cell(sp, 2, "a", "linear", 0, 0.41, shuffled=True, clusters=clusters),
           _cell(other, 2, "a", "linear", 0, 0.60, clusters=clusters)]       # wrong space
    got = rc.relabel_committed_linear_a(p3, sp)
    assert len(got) == 3 and {g["seed"] for g in got} == {0, 1, 2}
    for g in got:
        assert g["features"] == rc.LIN_BASE and g["capacity"] == "mlp256" and g["offset"] == 2
        assert g["cell"] == cell_id(sp, 2, rc.LIN_BASE, "mlp256", g["seed"])
        assert g["_clusters"] is clusters and g["test_acc"] == 0.42
    assert all(c["features"] == "a" or c["features"] == "c" for c in p3)  # the originals are untouched
    assert rc.relabel_committed_linear_a(p3, other)[0]["test_acc"] == 0.60


def test_leak_rider_two_legs_halt_and_need_the_fresh_reference():
    sp = S1[0]
    assert rc.rider_check([], sp) is None
    sa = _cell(sp, 2, "a", "linear", 0, 0.400, shuffled=True)
    sf = _cell(sp, 2, "fplus", "linear", 0, 0.405, shuffled=True)
    sb = _cell(sp, 2, "fplus_b", "linear", 0, 0.409, shuffled=True)
    out = rc.rider_check([sa, sf, sb], sp)
    assert out["pass"] and out["leg1_pass"] and out["leg2_pass"] and out["space"] == sp
    assert rc.rider_check([sa], sp)["pass"] is False           # legs pending, not failed
    with pytest.raises(SystemExit):
        rc.rider_check([sf], sp)                                # no fresh reference
    with pytest.raises(SystemExit):
        rc.rider_check([sa, sb], sp)                            # fplus_b without fplus
    with pytest.raises(SystemExit):
        rc.rider_check([sa, _cell(sp, 2, "fplus", "linear", 0, 0.4101, shuffled=True)], sp)
    with pytest.raises(SystemExit):
        rc.rider_check([sa, sf, _cell(sp, 2, "fplus_b", "linear", 0, 0.4151, shuffled=True)], sp)
    # another space's shuffled cells are invisible to this space's rider
    other = [_cell(S1[1], 2, "a", "linear", 0, 0.3, shuffled=True)]
    assert rc.rider_check(other, sp) is None


def _row(space, off, cap, margin, lo, hi, seeds=(0.01, 0.01, 0.01), pair=rc.GATE_PAIR,
         n_seeds=3, n_clusters=30):
    return {"space": space, "offset": off, "capacity": cap, "pair": pair, "margin": margin,
            "ci95": [lo, hi], "per_seed_margin": {str(i): s for i, s in enumerate(seeds)},
            "n_seeds": n_seeds, "n_clusters": n_clusters}


def test_reader_validity_three_legs_and_the_collapsed_reader():
    sp = S1[1]
    cells = [_cell(sp, 2, f, "mlp256", s, 0.45) for f in rc.ARMS + ("a",) for s in rc.SEEDS]
    mf = [_row(sp, 2, "mlp256", 0.02, 0.01, 0.03, pair=rc.PAIR_MF)]
    mfx = [_row(sp, 2, "mlp256", 0.01, 0.002, 0.02, pair=rc.PAIR_MFX)]
    ok = rc.reader_validity(cells, mf, mfx, sp)
    assert ok["ok"] and ok["complete"] and ok["n_gate_probes"] == 12
    assert ok["mfx_gate_margin"] == 0.01 and ok["acc_fplus_minus_floor_per_seed"] == [0.04] * 3
    assert rc.reader_validity(cells[:-1], mf, mfx, sp)["ok"] is False          # eleven probes
    assert rc.reader_validity(cells, [], mfx, sp)["ok"] is False                # no Mf row
    assert rc.reader_validity(cells, mf, [], sp)["ok"] is False                 # no Mf_x row
    assert rc.reader_validity(cells, mf, mf, sp)["ok"] is False                 # Mf_x must carry its own pair
    assert rc.reader_validity(cells, [_row(sp, 2, "mlp256", -0.02, -0.03, -0.001, pair=rc.PAIR_MF)], mfx, sp)["ok"] is False
    assert rc.reader_validity(cells, mf, [_row(sp, 2, "mlp256", -0.02, -0.03, -0.001, pair=rc.PAIR_MFX)], sp)["ok"] is False
    below = list(cells)
    below[4] = _cell(sp, 2, "fplus_b", "mlp256", 1, 0.4088)                     # 1.2 points under the floor
    assert rc.reader_validity(below, mf, mfx, sp)["ok"] is False
    near = list(cells)
    near[4] = _cell(sp, 2, "fplus_b", "mlp256", 1, 0.4095)                      # within tol
    assert rc.reader_validity(near, mf, mfx, sp)["ok"] is True
    coll = list(cells)
    coll[9] = _cell(sp, 2, "a", "mlp256", 0, 0.30)                              # a collapsed (a) counts too
    assert rc.reader_validity(coll, mf, mfx, sp)["ok"] is False
    assert rc.reader_validity(cells + [_cell(S1[0], 2, "fplus", "mlp256", 0, 0.1)], mf, mfx, sp)["ok"] is True
    # THE COLLAPSED READER (pre-run critic B2): every probe exactly at its
    # floor passes legs 1-2 with Mf = 0 exactly; only Mf_x, against the
    # committed LINEAR (a) that reads above the floor, refuses it
    flat = [_cell(sp, 2, f, "mlp256", s, 0.41) for f in rc.ARMS + ("a",) for s in rc.SEEDS]
    mf0 = [_row(sp, 2, "mlp256", 0.0, 0.0, 0.0, seeds=(0.0, 0.0, 0.0), pair=rc.PAIR_MF)]
    mfx_neg = [_row(sp, 2, "mlp256", -0.057, -0.06, -0.054, seeds=(-0.057,) * 3, pair=rc.PAIR_MFX)]
    r = rc.reader_validity(flat, mf0, mfx_neg, sp)
    assert r["floor_ok"] and r["mf_ok"] and not r["mfx_ok"] and r["ok"] is False
    assert r["acc_fplus_minus_floor_per_seed"] == [0.0] * 3


def test_gate_labels_horizons_and_the_boundary_are_mechanical():
    sp = S3[1]
    fire = _row(sp, 2, "mlp256", 0.012, 0.006, 0.018)
    quiet = _row(sp, 2, "mlp256", 0.002, -0.003, 0.0049)
    straddle = _row(sp, 2, "mlp256", 0.004, -0.002, 0.009)
    boundary = _row(sp, 2, "mlp256", 0.002, -0.001, 0.005)          # upper exactly at the floor
    assert rc.gate_fires(fire) and not rc.gate_fires(quiet) and not rc.gate_fires(straddle)
    assert not rc.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, seeds=(0.02, 0.02, -0.001)))
    assert not rc.gate_fires(_row(sp, 2, "mlp256", 0.004, 0.001, 0.007))
    assert not rc.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair="fplus_b-fplus_n"))  # OQ-17's pair
    assert not rc.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, n_seeds=1))
    assert not rc.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, n_clusters=29))
    assert not rc.gate_fires(None)
    assert rc.fires_triple(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair=rc.PAIR_MT), rc.PAIR_MT)
    assert not rc.fires_triple(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair=rc.PAIR_MT), rc.PAIR_MNR)
    lin_q = _row(sp, 2, "linear", 0.001, -0.002, 0.004)
    off3_q = _row(sp, 3, "mlp256", 0.0, -0.004, 0.0045)
    off4_q = _row(sp, 4, "mlp256", 0.0, -0.004, 0.0045)
    assert rc.source_label(fire, fire) == rc.LABEL_SURVIVES
    assert rc.source_label(fire, quiet) == rc.LABEL_SPLIT
    assert rc.source_label(None, fire) == rc.LABEL_INCOMPLETE
    assert rc.source_label(fire, fire, reader_ok=(True, False)) == rc.LABEL_READER_INVALID
    rows_quiet = [quiet, lin_q, off3_q, off4_q]
    assert rc.source_label(quiet, quiet, rows_quiet, rows_quiet) == rc.LABEL_ABSORBED
    assert rc.source_label(quiet, quiet, rows_quiet, [straddle, lin_q, off3_q, off4_q]) == rc.LABEL_NOT_SHOWN
    assert rc.source_label(boundary, boundary, [boundary], [boundary]) == rc.LABEL_NOT_SHOWN   # +0.005 is not below
    assert rc.source_label(quiet, quiet) == rc.LABEL_NOT_SHOWN
    off4 = _row(sp, 4, "mlp256", 0.012, 0.006, 0.018)
    off4_straddle = _row(sp, 4, "mlp256", 0.004, -0.002, 0.010)
    off4_boundary = _row(sp, 4, "mlp256", 0.001, -0.003, 0.005)
    assert rc.horizon_note(None, None, 4) is None
    assert rc.horizon_note(off4, None, 4) == "OFF4-INCOMPLETE"
    assert rc.horizon_note(off4, off4, 4) == "OFF4-SURVIVES"
    assert rc.horizon_note(off4_q, off4_q, 4) == "OFF4-ABSORBED"
    assert rc.horizon_note(off4_q, off4_straddle, 4) == "OFF4-NOT-SHOWN"
    assert rc.horizon_note(off4_q, off4_boundary, 4) == "OFF4-NOT-SHOWN"
    assert rc.horizon_note(off4, off4_q, 4) == "OFF4-SPLIT"
    assert rc.horizon_note(off3_q, off3_q, 3) == "OFF3-ABSORBED"
    rows = [fire, _row(sp, 2, "linear", 0.03, 0.02, 0.04), off4]
    assert rc.gate_row(rows, sp) is fire and rc.gate_row(rows, sp, offset=4) is off4
    assert rc.gate_row(rows, sp, capacity="linear")["margin"] == 0.03
    assert rc.gate_row(rows, S3[0]) is None
    assert rc.only_match(None, "x") and rc.only_match("L2_olmoe,fplus_r", "L3|fplus_r|s0")
    assert not rc.only_match("L2_olmoe,fplus_r", "L3|fplus_b|s0")


def _space_rows(space, gate):
    rows = [gate, _row(space, 2, "linear", 0.001, -0.002, 0.004)]
    rows += [_row(space, o, "mlp256", 0.0, -0.004, 0.0045) for o in rc.offsets_for_space(space) if o != 2]
    return rows


def _payload(tag, harvest, sha, rows_of, mt_of=None, mnr_of=None, partial=False, rider_pass=None,
             reader_ok=None, offsets_of=None, out=None, levels=None):
    spaces = rc.registered_spaces(tag)
    if out is None:
        out = rc.OUT_STEM_OF_TAG[tag] + ("_r" if harvest.endswith("_r") else "") + ".json"
    per = {}
    for sp in spaces:
        per[sp] = {"rider": {"pass": (rider_pass or {}).get(sp, True)},
                   "reader_valid": {"ok": (reader_ok or {}).get(sp, True),
                                    "mfx_gate_margin": 0.01, "mfx_gate_ci_upper": 0.02,
                                    "acc_fplus_minus_floor_per_seed": [0.03, 0.03, 0.03]},
                   "d_fplus_b_vs_fplus_r": rows_of.get(sp, []),
                   "mt_fplus_b_vs_fplus": (mt_of or {}).get(sp, []),
                   "mn_r_fplus_r_vs_fplus": (mnr_of or {}).get(sp, [])}
    return {"tag": tag, "levels": list(levels if levels is not None else rc.LEVELS),
            "spaces_registered": list(spaces), "harvest": harvest, "partial": partial,
            "offsets_of_space": {sp: list((offsets_of or {}).get(sp, rc.offsets_for_space(sp)))
                                 for sp in spaces},
            "per_space": per,
            "provenance": {"harvest_npz_sha256": {"x.npz": sha},
                           "args": {"out": "results/real/" + out}}}


def test_conclude_refusals_licenses_and_per_space_labels():
    tag = "olmoe"
    l2, l3 = rc.registered_spaces(tag)
    fire2 = _row(l2, 2, "mlp256", 0.012, 0.006, 0.018)
    fire3 = _row(l3, 2, "mlp256", 0.030, 0.020, 0.040)
    quiet3 = _row(l3, 2, "mlp256", 0.002, -0.003, 0.0049)
    rows_p = {l2: _space_rows(l2, fire2), l3: _space_rows(l3, fire3)}
    rows_r = {l2: _space_rows(l2, fire2), l3: _space_rows(l3, quiet3)}
    mt_pos = {l3: [_row(l3, 2, "mlp256", 0.02, 0.01, 0.03, pair=rc.PAIR_MT)],
              l2: [_row(l2, 2, "mlp256", 0.01, 0.002, 0.02, pair=rc.PAIR_MT)]}
    mnr_ok = {l3: [_row(l3, 2, "mlp256", 0.001, -0.004, 0.006, pair=rc.PAIR_MNR)],
              l2: [_row(l2, 2, "mlp256", 0.000, -0.005, 0.005, pair=rc.PAIR_MNR)]}
    pp = _payload(tag, "results/real/harvest_moe", "A", rows_p, mt_of=mt_pos, mnr_of=mnr_ok)
    rp = _payload(tag, "results/real/harvest_moe_r", "B", rows_r, mt_of=mt_pos, mnr_of=mnr_ok)
    out = rc.conclude(pp, rp)
    assert out["tag"] == tag and set(out["spaces"]) == {l2, l3}
    assert out["spaces"][l2]["label"] == rc.LABEL_SURVIVES and out["spaces"][l2]["survives_license"] == "full"
    assert out["spaces"][l2]["license_reason"] is None
    assert out["spaces"][l2]["mt_fires_triple_rule"] == {"primary": True, "replication": True}
    assert out["spaces"][l2]["mn_r_fires_triple_rule"] == {"primary": False, "replication": False}
    assert out["spaces"][l3]["label"] == rc.LABEL_SPLIT and out["spaces"][l3]["survives_license"] is None
    assert out["spaces"][l3]["horizons"] == {"off3": "OFF3-ABSORBED", "off4": "OFF4-ABSORBED"}
    assert out["spaces"][l2]["horizons"] == {"off3": "OFF3-ABSORBED"}
    assert out["spaces"][l2]["all_d_ci_uppers_below_floor"] is False
    assert out["spaces"][l2]["reader_valid_detail"]["primary"]["mfx_gate_margin"] == 0.01
    # equal-dims-only when an Mt upper is negative on either harvest ...
    mt_neg = dict(mt_pos)
    mt_neg[l2] = [_row(l2, 2, "mlp256", -0.01, -0.02, -0.002, pair=rc.PAIR_MT)]
    rp2 = _payload(tag, "results/real/harvest_moe_r", "B", rows_r, mt_of=mt_neg, mnr_of=mnr_ok)
    o2 = rc.conclude(pp, rp2)["spaces"][l2]
    assert o2["survives_license"] == "equal-dims-only" and "Mt" in o2["license_reason"]
    # ... or when the corrected twin is CI-clear HARMFUL (a fire bought by the twin's cost)
    mnr_neg = dict(mnr_ok)
    mnr_neg[l2] = [_row(l2, 2, "mlp256", -0.006, -0.010, -0.002, seeds=(-0.006,) * 3, pair=rc.PAIR_MNR)]
    rp3 = _payload(tag, "results/real/harvest_moe_r", "B", rows_r, mt_of=mt_pos, mnr_of=mnr_neg)
    o3 = rc.conclude(pp, rp3)["spaces"][l2]
    assert o3["label"] == rc.LABEL_SURVIVES and o3["survives_license"] == "equal-dims-only"
    assert "Mn_r" in o3["license_reason"]
    # a missing Mn_r row is not a non-negative row
    rp4 = _payload(tag, "results/real/harvest_moe_r", "B", rows_r, mt_of=mt_pos)
    assert rc.conclude(pp, rp4)["spaces"][l2]["survives_license"] == "equal-dims-only"
    # the strong null needs every D row of both harvests below the floor
    q2 = _row(l2, 2, "mlp256", 0.001, -0.003, 0.004)
    rows_q = {l2: _space_rows(l2, q2), l3: _space_rows(l3, quiet3)}
    pq = _payload(tag, "results/real/harvest_moe", "A", rows_q)
    rq = _payload(tag, "results/real/harvest_moe_r", "B", rows_q)
    oq = rc.conclude(pq, rq)
    assert oq["spaces"][l2]["label"] == rc.LABEL_ABSORBED and oq["spaces"][l3]["label"] == rc.LABEL_ABSORBED
    assert oq["spaces"][l2]["all_d_ci_uppers_below_floor"] is True
    # refusals
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", rows_p, partial=True), rp)
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", rows_p, rider_pass={l3: False}), rp)
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_shadow", "A", rows_p), rp)      # wrong source dir
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", rows_p, out="smoke.json"), rp)
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", rows_p, offsets_of={l3: (2, 3)}), rp)
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", rows_p, levels=("L1", "L2")), rp)
    short = dict(rows_p)
    short[l3] = rows_p[l3][:-1]
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", short), rp)         # missing off4 row
    thin = dict(rows_p)
    thin[l3] = rows_p[l3][:-1] + [_row(l3, 4, "mlp256", 0.0, -0.004, 0.0045, n_clusters=29)]
    with pytest.raises(SystemExit):
        rc.conclude(_payload(tag, "results/real/harvest_moe", "A", thin), rp)          # a structurally thin D row
    with pytest.raises(SystemExit):
        rc.conclude(pp, _payload(tag, "results/real/harvest_moe_r", "A", rows_r))       # same harvest
    with pytest.raises(SystemExit):
        rc.conclude(pp, _payload("concept", "results/real/harvest_shadow_r", "B",
                                 {s: _space_rows(s, _row(s, 2, "mlp256", 0, -0.001, 0.001))
                                  for s in rc.registered_spaces("concept")}))           # sources differ
    # READER-INVALID on either harvest at a space blocks that space only
    ri = _payload(tag, "results/real/harvest_moe_r", "B", rows_r, mt_of=mt_pos, mnr_of=mnr_ok,
                  reader_ok={l3: False})
    o = rc.conclude(pp, ri)
    assert o["spaces"][l3]["label"] == rc.LABEL_READER_INVALID and o["spaces"][l2]["label"] == rc.LABEL_SURVIVES


def test_parser_defaults_are_the_s1_instrument():
    a = rc.build_parser().parse_args([])
    assert a.harvest == "results/real/harvest_shadow" and a.space_tag == "concept"
    assert a.out == "results/real/fullfree_coarse_s1.json" and a.n_slots == 512
    assert a.phase3_state == "results/real/probes_s1.json.state.jsonl"
    assert a.parent_finding == "F-15" and a.only is None and a.resume is False
    assert rc.REGISTERED_OUTS == ("fullfree_coarse_s1.json", "fullfree_coarse_s1_r.json",
                                  "fullfree_coarse_s3.json", "fullfree_coarse_s3_r.json")
    assert rc.OUT_STEM_OF_TAG == {"concept": "fullfree_coarse_s1", "olmoe": "fullfree_coarse_s3"}
    assert set(rc.FULLFREE_OF_HARVEST.values()) == {"fullfree_s1.json", "fullfree_s1_r.json",
                                                    "fullfree_s3.json", "fullfree_s3_r.json"}
    assert rc.committed_moments_sha("results/real/some_other_harvest") is None


@pytest.mark.parametrize("pair", [("fullfree_coarse_s1.json", "fullfree_coarse_s1_r.json"),
                                  ("fullfree_coarse_s3.json", "fullfree_coarse_s3_r.json")])
def test_committed_payloads_reproduce_their_conclusion(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("registered OQ-18 payloads not present")
    pp, rp = (json.loads(p.read_text()) for p in paths)
    if pp.get("amendment") or rp.get("amendment"):
        # DATED NOTE (2026-09-14): the committed payloads were written under the 2026-09-07 rider
        # amendment (docs/BLUEPRINT.md dated amendment bullet): licensed resumes make resumed_cells
        # nonzero by plan and the rider block carries the amended leg; the frozen instrument never
        # concluded them. tests/test_fullfree_coarse_amended.py reproduces their conclusion instead.
        pytest.skip("committed OQ-18 payloads are amended (2026-09-07 rider amendment); "
                    "see tests/test_fullfree_coarse_amended.py")
    n_cells = 60 if "s1" in pair[0] else 69
    for d in (pp, rp):
        assert d["partial"] is False and d["n_cells"] == n_cells and d["resumed_cells"] == 0
        assert d["provenance"]["arm_dims_total"]["fplus_b"] == d["provenance"]["arm_dims_total"]["fplus_r"]
        assert d["twin"]["arm"] == rc.TWIN_ARM and d["twin"]["seed_base"] == rc.TWIN_SEED_BASE
        assert d["standardization"]["moments_sha_matches_committed_oq17"] is True
        for sp, ps in d["per_space"].items():
            assert ps["rider"]["pass"] and ps["rider"]["leg1_pass"] and ps["rider"]["leg2_pass"]
            assert ps["gate"]["fires"] == (ps["reader_valid"]["ok"] and rc.gate_fires(ps["gate"]["row"]))
            assert all(m["n_clusters"] == 30 and m["n_seeds"] == 3 for m in ps["d_fplus_b_vs_fplus_r"])
            assert ps["reader_valid"]["n_gate_probes"] == 12
            assert ps["reader_valid"]["mfx_gate_ci_upper"] is not None
        for seed, g in d["twin"]["geometry"].items():
            assert all(gg["corrected_twin_same_prompt_frac"] == 0.0 for gg in g.values())
        assert len(d["standardization"]["moments_sha256"]) == 64
    out = rc.conclude(pp, rp)
    for sp, o in out["spaces"].items():
        assert o["label"] in (rc.LABEL_SURVIVES, rc.LABEL_ABSORBED, rc.LABEL_NOT_SHOWN,
                              rc.LABEL_SPLIT, rc.LABEL_READER_INVALID)

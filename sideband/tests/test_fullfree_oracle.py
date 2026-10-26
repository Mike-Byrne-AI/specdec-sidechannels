"""DRAFT STATUS (2026-10-01): UNFROZEN. The OQ-19 instrument these tests cover
is committed as a DRAFT beside docs/OQ19_ORACLE_CEILING_DRAFT.md; no
registration block exists in docs/BLUEPRINT.md and nothing of OQ-19 has run.

tools/run_fullfree_oracle.py (OQ-19 oracle-intermediate ceiling) and the
pure-numpy layer of sideband.real.oracle_replay: registered spaces / offsets
/ arms, the grid (lead control at the gate offset only) and its refusal
against committed ids, the oracle / lead / subset-sketch blocks with their
corrected twins and their byte-identity to the OQ-17 free blocks, the
committed-cell selection per space, the rider against the committed
shuffled fplus, the oracle and four-leg reader preconditions (including
a reader that never opens the oracle block), the pinned labels / horizons,
the survival-fraction bootstrap and its undefined / READER-LIMITED forms,
--conclude-from refusals (counts, on-disk re-hash) and readings, and the
replay helpers (chunk bounds, set equality and overlap, the hygiene
finalizer, the fidelity summary, the side-file binding and the loader's
seed-order / row-alignment / fidelity-recompute refusals on real files).
No torch."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import run_fullfree_oracle as ro  # noqa: E402
import run_fullfree as rf  # noqa: E402
from sideband.real import oracle_replay as orp  # noqa: E402
from run_probes import cell_id  # noqa: E402
from sideband.probes import slots_multi_hot  # noqa: E402

S1 = ("L1_concept_k16", "L3_concept_groups_v1")
S3 = ("L1_olmoe_k16", "L3_olmoe_groups_v1")


def test_registered_spaces_offsets_arms_and_layers():
    assert ro.registered_spaces("concept") == S1 and ro.registered_spaces("olmoe") == S3
    assert ro.offsets_for_space(S1[0]) == (2, 3) and ro.offsets_for_space(S1[1]) == (2, 3)
    assert ro.offsets_for_space(S3[0]) == (2,) and ro.offsets_for_space(S3[1]) == (2, 3)
    with pytest.raises(SystemExit):
        ro.offsets_for_space("L2_concept_k512")                 # L2 is omitted by registration
    assert ro.arms_for_tag("concept") == ("fplus_o", "fplus_o_r", "fplus_o_lead")
    assert ro.arms_for_tag("olmoe") == ("fplus_o", "fplus_o_r", "fplus_o_lead", "fplus_b4", "fplus_r4")
    assert ro.arms_at_offset(ro.arms_for_tag("olmoe"), 3) == ("fplus_o", "fplus_o_r", "fplus_b4", "fplus_r4")
    assert ro.REGISTERED_LAYERS == {"shadow": (7, 15, 23, 31), "moe": (3, 7, 11, 15)}
    assert ro.SKETCH_LAYERS_OF_TAG == {"concept": None, "olmoe": (3, 7, 11, 15)}
    assert ro.committed_of_harvest("results/real/harvest_moe_r")["oracle_dir"] == "results/real/oracle_moe_r"
    with pytest.raises(SystemExit):
        ro.committed_of_harvest("results/real/harvest_other")
    assert ro.tag_of_space(S3[1]) == "olmoe" and ro.expected_d_rows(S3[0]) == 1 and ro.expected_d_rows(S1[1]) == 2
    assert ro.LEAD == 2 and ro.LEAD_MIN == 0.02 and ro.N_TRAINED_OF_TAG == {"concept": 30, "olmoe": 42}
    assert ro.PARENT_FINDING_OF_TAG == {"concept": "F-15", "olmoe": "F-17"}
    assert ro.ALPHABET_KEY_OF_TAG == {"concept": "n_slots", "olmoe": "n_experts"}


def test_grid_is_the_registered_one_and_refuses_committed_ids():
    g1 = ro.build_grid(ro.registered_spaces("concept"), ro.arms_for_tag("concept"))
    g3 = ro.build_grid(ro.registered_spaces("olmoe"), ro.arms_for_tag("olmoe"))
    assert len(g1) == 32 and len([c for c in g1 if not c[5]]) == 30
    assert len(g3) == 44 and len([c for c in g3 if not c[5]]) == 42
    for g, spaces, arms in ((g1, S1, ro.arms_for_tag("concept")), (g3, S3, ro.arms_for_tag("olmoe"))):
        for sp in spaces:
            block = [c for c in g if c[0] == sp]
            assert block[0] == (sp, 2, "fplus_o", "linear", 0, True)
            assert {c[3] for c in block[1:]} == {"mlp256"}
            assert {c[2] for c in block if c[1] == 2 and not c[5]} == set(arms)
            assert all(c[2] != "fplus_o_lead" for c in block if c[1] != 2)     # lead at the gate only
            assert sorted({c[1] for c in block}) == list(ro.offsets_for_space(sp))
    assert len({cell_id(*c) for c in g3}) == len(g3)
    with pytest.raises(SystemExit):
        ro.build_grid(("L1_concept_k16",), ro.arms_for_tag("concept"), {"L1_concept_k16": (1, 2)})
    ro.check_grid_against_committed(g1, {cell_id(S1[0], 2, "fplus", "mlp256", 0)})
    with pytest.raises(SystemExit):
        ro.check_grid_against_committed(g1, {cell_id(S1[0], 2, "fplus_o", "mlp256", 0)})


def _layout():
    rng = np.random.default_rng(5)
    N, T, L16, top, d_h, L_o, d_o = 8, 30, 16, 8, 6, 4, 5
    slots = rng.integers(0, 64, size=(N, T, L16, top)).astype(np.int16)
    top_ids = rng.integers(0, 3000, size=(N, T, 32)).astype(np.int32)
    hidden = rng.normal(size=(N, T, d_h)).astype(np.float16)
    oracle = rng.normal(size=(N, T, L_o * d_o)).astype(np.float16)
    lengths = np.array([30, 30, 18, 25, 30, 22, 30, 27])
    prompt_idx = np.array([0, 0, 1, 1, 2, 2, 3, 3])
    split = np.array(["train"] * N)
    return slots, top_ids, hidden, oracle, lengths, prompt_idx, split, (d_h, L_o * d_o)


def test_blocks_and_factories():
    slots, top_ids, hidden, oracle, lengths, prompt_idx, split, (d_h, d_of) = _layout()
    m_h = rf.train_moments(hidden, lengths, split)
    m_o = rf.train_moments(oracle, lengths, split)
    perms = {s: ro.derangement_by_prompt(prompt_idx, split, s) for s in ro.SEEDS}
    rows = np.array([0, 1, 2, 3, 7, 5])
    anchors = np.array([0, 29, 17, 4, 26, 21])
    idx = np.arange(len(rows))
    sub = ro.SubsetSlotsBlock(slots, rows, anchors, (3, 7, 11, 15), 64)
    assert sub.dim == 4 * 64
    np.testing.assert_array_equal(sub.batch(idx), slots_multi_hot(slots[rows, anchors][:, [3, 7, 11, 15], :], 64))
    with pytest.raises(SystemExit):
        ro.SubsetSlotsBlock(slots, rows, anchors, (3, 7, 11, 16), 64)
    with pytest.raises(SystemExit):
        ro.SubsetSlotsBlock(slots, rows, anchors, (3, 3, 11, 15), 64)
    tw = ro.OtherRowZBlock(oracle, rows, anchors, lengths, perms[1], m_o)
    other = perms[1][rows]
    assert np.all(prompt_idx[other] != prompt_idx[rows])
    np.testing.assert_array_equal(tw.batch(idx), rf.HiddenZBlock(oracle, other, anchors % lengths[other], m_o).batch(idx))
    lead = ro.LeadZBlock(oracle, rows, anchors, lengths, m_o)
    want = np.minimum(anchors + 2, lengths[rows] - 1)
    np.testing.assert_array_equal(lead.lead_anchors, want)
    assert want[1] == 29 and want[0] == 2 and want[3] == 6
    np.testing.assert_array_equal(lead.batch(idx), rf.HiddenZBlock(oracle, rows, want, m_o).batch(idx))
    assert not np.array_equal(lead.batch(idx), rf.HiddenZBlock(oracle, rows, anchors, m_o).batch(idx))
    for tag, sk in (("concept", None), ("olmoe", (3, 7, 11, 15))):
        fac = ro.make_factories(top_ids, hidden, oracle, slots, lengths, 64, m_h, m_o, perms, sk, n_bins=32)
        assert set(fac) == {(a, s) for a in ro.arms_for_tag(tag) for s in ro.SEEDS}
        ref = rf.make_factories(top_ids, hidden, slots, lengths, 64, m_h, n_bins=32)["fplus"](rows, anchors)
        for seed in ro.SEEDS:
            o_blocks = fac[("fplus_o", seed)](rows, anchors)
            r_blocks = fac[("fplus_o_r", seed)](rows, anchors)
            l_blocks = fac[("fplus_o_lead", seed)](rows, anchors)
            assert [type(b).__name__ for b in o_blocks] == ["TokAnchorBlock", "HiddenZBlock", "HiddenZBlock"]
            assert [type(b).__name__ for b in r_blocks] == ["TokAnchorBlock", "HiddenZBlock", "OtherRowZBlock"]
            assert [type(b).__name__ for b in l_blocks] == ["TokAnchorBlock", "HiddenZBlock", "LeadZBlock"]
            assert sum(b.dim for b in o_blocks) == sum(b.dim for b in r_blocks) == sum(b.dim for b in l_blocks) == 32 + d_h + d_of
            for k in (0, 1):
                np.testing.assert_array_equal(o_blocks[k].batch(idx), ref[k].batch(idx))
                np.testing.assert_array_equal(r_blocks[k].batch(idx), ref[k].batch(idx))
            assert not np.array_equal(o_blocks[2].batch(idx), r_blocks[2].batch(idx))
            if sk:
                b4 = fac[("fplus_b4", seed)](rows, anchors)
                r4 = fac[("fplus_r4", seed)](rows, anchors)
                assert [type(b).__name__ for b in b4] == ["TokAnchorBlock", "HiddenZBlock", "SubsetSlotsBlock"]
                assert [type(b).__name__ for b in r4] == ["TokAnchorBlock", "HiddenZBlock", "OtherRowSubsetSlotsBlock"]
                assert sum(b.dim for b in b4) == sum(b.dim for b in r4) == 32 + d_h + 4 * 64
    with pytest.raises(SystemExit):
        ro.make_factories(top_ids, hidden, oracle, slots, lengths, 64, m_h, m_o, {0: perms[0]}, None)


def _cell(space, off, feats, cap, seed, acc, maj=0.41, shuffled=False, best_epoch=0, clusters=None):
    c = {"cell": cell_id(space, off, feats, cap, seed, shuffled), "space": space, "offset": off,
         "features": feats, "capacity": cap, "seed": seed, "shuffled": shuffled, "test_acc": acc,
         "majority_rate_test": maj, "best_epoch": best_epoch}
    if clusters is not None:
        c["_clusters"] = clusters
    return c


def test_committed_cells_per_space_and_rider():
    l1, l3 = S1
    ff = [_cell(l1, 2, f, "mlp256", 0, 0.5) for f in ("fplus", "fplus_b", "fplus_n")] + \
         [_cell(l1, 2, "fplus", "linear", 0, 0.41, shuffled=True), _cell(l1, 2, "b", "mlp256", 0, 0.5)]
    tw = [_cell(l1, 2, "fplus_r", "mlp256", 0, 0.5)]
    co = [_cell(l3, 2, f, "mlp256", 0, 0.6) for f in ("fplus", "fplus_b", "fplus_r", "a")] + \
         [_cell(l3, 2, "fplus", "linear", 0, 0.56, shuffled=True)]
    c1 = ro.committed_cells_for(l1, ff, tw, co)
    assert {c["features"] for c in c1} == {"fplus", "fplus_b", "fplus_n", "fplus_r"} and all(c["space"] == l1 for c in c1)
    assert {c["features"] for c in ro.committed_cells_for(l3, ff, tw, co)} == {"fplus", "fplus_b", "fplus_r", "a"}
    with pytest.raises(SystemExit):
        ro.committed_cells_for(l3, ff, tw, [])
    assert ro.rider_check([], c1, l1) is None
    ok = ro.rider_check([_cell(l1, 2, "fplus_o", "linear", 0, 0.415, shuffled=True)], c1, l1)
    assert ok["pass"] and ok["committed_shuffled_fplus"] == 0.41
    with pytest.raises(SystemExit):
        ro.rider_check([_cell(l1, 2, "fplus_o", "linear", 0, 0.4201, shuffled=True)], c1, l1)
    with pytest.raises(SystemExit):
        ro.rider_check([_cell(l1, 2, "fplus_o", "linear", 0, 0.415, shuffled=True)],
                       [c for c in c1 if not c["shuffled"]], l1)


def _row(space, off, cap, margin, lo, hi, seeds=(0.01, 0.01, 0.01), pair=ro.GATE_PAIR, n_seeds=3, n_clusters=30):
    return {"space": space, "offset": off, "capacity": cap, "pair": pair, "margin": margin, "ci95": [lo, hi],
            "per_seed_margin": {str(i): s for i, s in enumerate(seeds)}, "n_seeds": n_seeds, "n_clusters": n_clusters}


def test_oracle_and_reader_preconditions():
    ok = dict(token_min=0.995, overlap_min=0.96, h_rel_median=0.005, h_rel_p99=0.02, exact_min=0.5)
    assert ro.oracle_validity(**ok)["ok"]
    assert not ro.oracle_validity(**{**ok, "token_min": 0.98})["ok"]
    assert not ro.oracle_validity(**{**ok, "overlap_min": 0.94})["ok"]
    assert not ro.oracle_validity(**{**ok, "h_rel_median": 0.02})["ok"]
    assert not ro.oracle_validity(**{**ok, "h_rel_p99": 0.06})["ok"]
    assert not ro.oracle_validity()["ok"]
    sp = S3[1]
    arms = ro.arms_for_tag("olmoe")
    cells = [_cell(sp, 2, a, "mlp256", s, 0.5) for a in arms for s in ro.SEEDS]
    mfx = [_row(sp, 2, "mlp256", 0.02, 0.01, 0.03, pair=ro.PAIR_MFX)]
    lead = [_row(sp, 2, "mlp256", 0.05, 0.03, 0.07, seeds=(0.05, 0.05, 0.05), pair=ro.PAIR_LEAD)]
    r = ro.reader_validity(cells, mfx, lead, sp, arms)
    assert r["ok"] and r["n_gate_probes"] == 15 and r["lead_ok"] and r["lead_gate_margin"] == 0.05
    assert not ro.reader_validity(cells[:-1], mfx, lead, sp, arms)["ok"]
    assert not ro.reader_validity(cells, [], lead, sp, arms)["ok"]
    assert not ro.reader_validity(cells, mfx, [], sp, arms)["ok"]
    assert not ro.reader_validity(cells, [_row(sp, 2, "mlp256", -0.02, -0.03, -0.001, pair=ro.PAIR_MFX)], lead, sp, arms)["ok"]
    # THE READER THAT NEVER OPENS THE ORACLE BLOCK: every probe at fplus's
    # level, Mf_x fine, D_o = 0 exactly — only the lead control refuses it
    lead_flat = [_row(sp, 2, "mlp256", 0.0, -0.002, 0.002, seeds=(0.0, 0.0, 0.0), pair=ro.PAIR_LEAD)]
    rr = ro.reader_validity(cells, mfx, lead_flat, sp, arms)
    assert rr["floor_ok"] and rr["mfx_ok"] and not rr["lead_ok"] and rr["ok"] is False
    lead_small = [_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair=ro.PAIR_LEAD)]
    assert not ro.reader_validity(cells, mfx, lead_small, sp, arms)["ok"]
    low = list(cells)
    low[0] = _cell(sp, 2, "fplus_o", "mlp256", 0, 0.4088)
    assert not ro.reader_validity(low, mfx, lead, sp, arms)["ok"]
    assert ro.reader_validity(cells, mfx, lead, sp, ro.arms_for_tag("concept"))["n_gate_probes"] == 9


def test_labels_and_horizons():
    sp = S1[1]
    fire = _row(sp, 2, "mlp256", 0.012, 0.006, 0.018)
    quiet = _row(sp, 2, "mlp256", 0.002, -0.003, 0.0049)
    straddle = _row(sp, 2, "mlp256", 0.004, -0.002, 0.009)
    assert ro.gate_fires(fire) and not ro.gate_fires(quiet) and not ro.gate_fires(straddle)
    assert not ro.gate_fires(_row(sp, 2, "mlp256", 0.012, 0.006, 0.018, pair="fplus_b-fplus_r"))
    assert ro.source_label(fire, fire) == ro.LABEL_HEADROOM
    assert ro.source_label(fire, quiet) == ro.LABEL_SPLIT
    assert ro.source_label(None, fire) == ro.LABEL_INCOMPLETE
    assert ro.source_label(fire, fire, reader_ok=(False, True)) == ro.LABEL_READER_INVALID
    assert ro.source_label(fire, fire, oracle_ok=(True, False)) == ro.LABEL_ORACLE_INVALID
    assert ro.source_label(None, None, oracle_ok=(False, False)) == ro.LABEL_ORACLE_INVALID
    off3_q = _row(sp, 3, "mlp256", 0.0, -0.004, 0.0045)
    assert ro.source_label(quiet, quiet, [quiet, off3_q], [quiet, off3_q]) == ro.LABEL_NO_HEADROOM
    assert ro.source_label(quiet, quiet, [quiet, off3_q], [straddle, off3_q]) == ro.LABEL_NOT_SHOWN
    assert ro.source_label(quiet, quiet) == ro.LABEL_NOT_SHOWN
    off3 = _row(sp, 3, "mlp256", 0.012, 0.006, 0.018)
    assert ro.horizon_note(off3, off3, 3) == "OFF3-HEADROOM"
    assert ro.horizon_note(off3_q, off3_q, 3) == "OFF3-NO-HEADROOM"
    assert ro.horizon_note(off3_q, _row(sp, 3, "mlp256", 0.002, -0.002, 0.006), 3) == "OFF3-NOT-SHOWN"
    assert ro.horizon_note(off3, off3_q, 3) == "OFF3-SPLIT"
    assert ro.horizon_note(off3, None, 3) == "OFF3-INCOMPLETE" and ro.horizon_note(None, None, 3) is None


def _clusters(succ, trials=10, n=30):
    return {str(p): (succ, trials) for p in range(n)}


def test_survival_fraction_bootstrap_and_readings():
    sp = S1[0]
    cells = []
    for s in ro.SEEDS:
        cells += [_cell(sp, 2, "fplus_b", "mlp256", s, 0.5, clusters=_clusters(6)),
                  _cell(sp, 2, "fplus_r", "mlp256", s, 0.5, clusters=_clusters(5)),      # sketch delta 1 / prompt
                  _cell(sp, 2, "fplus_o", "mlp256", s, 0.5, clusters=_clusters(7)),
                  _cell(sp, 2, "fplus_o_r", "mlp256", s, 0.5, clusters=_clusters(5))]    # oracle delta 2 / prompt
    sf = ro.survival_fraction(cells, sp, "fplus_b", "fplus_r")
    assert sf["defined"] and sf["point"] == 0.5 and sf["ci95"][0] <= 0.5 <= sf["ci95"][1] and sf["n_clusters"] == 30
    assert sf["n_boot"] == 2000 and sf["n_boot_undefined"] == 0 and sf["reading"].startswith("fraction")
    assert ro.survival_fraction(cells, sp, "fplus_b", "fplus_r")["ci95"] == sf["ci95"]      # deterministic
    # the house draw convention: one (n_boot, n) index matrix from default_rng(seed)
    idx = np.random.default_rng(0).integers(0, 30, size=(2000, 30))
    ratios = np.ones(30)[idx].sum(1) / (2 * np.ones(30))[idx].sum(1)
    assert sf["ci95"] == [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]
    assert ro.survival_fraction(cells[:-1], sp, "fplus_b", "fplus_r") is None
    bad = list(cells)
    bad[1] = _cell(sp, 2, "fplus_r", "mlp256", 0, 0.5, clusters=_clusters(5, trials=9))
    assert ro.survival_fraction(bad, sp, "fplus_b", "fplus_r") is None
    flat = [dict(c) for c in cells]
    for c in flat:
        if c["features"] == "fplus_o":
            c["_clusters"] = _clusters(5)
    assert ro.survival_fraction(flat, sp, "fplus_b", "fplus_r")["defined"] is False
    big = [dict(c) for c in cells]
    for c in big:
        if c["features"] == "fplus_b":
            c["_clusters"] = _clusters(9)                                              # sketch delta 4 vs oracle 2
    assert ro.survival_fraction(big, sp, "fplus_b", "fplus_r")["reading"].startswith("READER-LIMITED")
    neg = [dict(c) for c in cells]
    for c in neg:
        if c["features"] == "fplus_b":
            c["_clusters"] = _clusters(4)
    assert "negative" in ro.survival_fraction(neg, sp, "fplus_b", "fplus_r")["reading"]


def _payload(tag, harvest, sha, rows_of, sk_of=None, partial=False, rider_pass=None, reader_ok=None,
             oracle_ok=True, layers=None, out=None, offsets_of=None, n_cells=None, resumed=0):
    spaces = ro.registered_spaces(tag)
    if out is None:
        out = ro.OUT_STEM_OF_TAG[tag] + ("_r" if harvest.endswith("_r") else "") + ".json"
    sk_key = "d_4_fplus_b4_vs_fplus_r4" if ro.SKETCH_LAYERS_OF_TAG.get(tag) else "d_sk_fplus_b_vs_fplus_r"
    per = {}
    for sp in spaces:
        per[sp] = {"rider": {"pass": (rider_pass or {}).get(sp, True)},
                   "reader_valid": {"ok": (reader_ok or {}).get(sp, True), "lead_gate_margin": 0.05},
                   "d_o_fplus_o_vs_fplus_o_r": rows_of.get(sp, []),
                   "mt_o_fplus_o_vs_fplus": [], "mn_o_fplus_o_r_vs_fplus": [],
                   "d_sk_fplus_b_vs_fplus_r": (sk_of or {}).get(sp, []) if sk_key.startswith("d_sk") else [],
                   sk_key: (sk_of or {}).get(sp, []),
                   "survival_fraction": {"defined": True, "point": 0.3, "ci95": [0.1, 0.5]}}
    return {"tag": tag, "levels": list(ro.LEVELS), "spaces_registered": list(spaces), "harvest": harvest,
            "partial": partial, "n_cells": (ro.N_TRAINED_OF_TAG[tag] if n_cells is None else n_cells),
            "resumed_cells": resumed,
            "offsets_of_space": {sp: list((offsets_of or {}).get(sp, ro.offsets_for_space(sp))) for sp in spaces},
            "per_space": per,
            "oracle": {"layers": list(layers if layers is not None else ro.REGISTERED_LAYERS[ro.PREFIX_OF_TAG[tag]]),
                       "validity": {"ok": oracle_ok}, "side_file_sha256": {}, "side_file_meta_sha256": {}},
            "provenance": {"harvest_npz_sha256": {"x.npz": sha}, "args": {"out": "results/real/" + out}}}


def _space_rows(space, gate):
    return [gate] + [_row(space, o, "mlp256", 0.0, -0.004, 0.0045) for o in ro.offsets_for_space(space) if o != 2]


def test_conclude_readings_and_refusals():
    tag = "concept"
    l1, l3 = ro.registered_spaces(tag)
    fire1 = _row(l1, 2, "mlp256", 0.012, 0.006, 0.018)
    quiet3 = _row(l3, 2, "mlp256", 0.002, -0.003, 0.0049)
    rows = {l1: _space_rows(l1, fire1), l3: _space_rows(l3, quiet3)}
    sk_fire3 = _row(l3, 2, "mlp256", 0.030, 0.020, 0.040, pair=ro.PAIR_DSK)
    sk = {l1: [_row(l1, 2, "mlp256", 0.004, -0.001, 0.009, pair=ro.PAIR_DSK)], l3: [sk_fire3]}
    pp = _payload(tag, "results/real/harvest_shadow", "A", rows, sk_of=sk)
    rp = _payload(tag, "results/real/harvest_shadow_r", "B", rows, sk_of=sk)
    out = ro.conclude(pp, rp, verify_files=False)
    assert out["spaces"][l1]["label"] == ro.LABEL_HEADROOM
    assert out["spaces"][l1]["survival_fraction"]["primary"]["point"] == 0.3
    assert out["spaces"][l1]["reader_limited_reading"] is False
    assert out["spaces"][l1]["lead_control"] == {"primary": 0.05, "replication": 0.05}
    assert out["spaces"][l3]["label"] == ro.LABEL_NO_HEADROOM
    assert out["spaces"][l3]["reader_limited_reading"] is True                       # sketch fires under NO-HEADROOM
    assert out["spaces"][l3]["sketch_d_at_gate"]["pair"] == ro.PAIR_DSK
    assert out["spaces"][l3]["full_sketch_d_at_gate"]["like_for_like"] is True
    assert out["spaces"][l1]["horizons"] == {"off3": "OFF3-NO-HEADROOM"}
    assert out["resumed_cells"] == {"primary": 0, "replication": 0}
    # a one-harvest sketch fire is NOT reader-limited
    sk1 = {l1: sk[l1], l3: [sk_fire3]}
    rp1 = _payload(tag, "results/real/harvest_shadow_r", "B", rows,
                   sk_of={l1: sk[l1], l3: [_row(l3, 2, "mlp256", 0.002, -0.003, 0.006, pair=ro.PAIR_DSK)]})
    assert ro.conclude(_payload(tag, "results/real/harvest_shadow", "A", rows, sk_of=sk1), rp1,
                       verify_files=False)["spaces"][l3]["reader_limited_reading"] is False
    tag3 = "olmoe"
    m1, m3 = ro.registered_spaces(tag3)
    rows3 = {m1: _space_rows(m1, _row(m1, 2, "mlp256", 0.0, -0.003, 0.004)),
             m3: _space_rows(m3, _row(m3, 2, "mlp256", 0.02, 0.01, 0.03))}
    p3 = _payload(tag3, "results/real/harvest_moe", "A", rows3)
    r3 = _payload(tag3, "results/real/harvest_moe_r", "B", rows3)
    o3 = ro.conclude(p3, r3, verify_files=False)
    assert o3["spaces"][m1]["label"] == ro.LABEL_NO_HEADROOM and o3["spaces"][m3]["label"] == ro.LABEL_HEADROOM
    assert o3["spaces"][m3]["sketch_d_at_gate"]["pair"] == ro.PAIR_D4 and o3["spaces"][m1]["horizons"] == {}
    assert o3["spaces"][m1]["full_sketch_d_at_gate"]["like_for_like"] is False        # the 16-layer sketch is reported only
    # a resumed run is recorded, not refused
    assert ro.conclude(_payload(tag, "results/real/harvest_shadow", "A", rows, sk_of=sk, resumed=1), rp,
                       verify_files=False)["resumed_cells"]["primary"] == 1
    for bad in (_payload(tag, "results/real/harvest_shadow", "A", rows, partial=True),
                _payload(tag, "results/real/harvest_shadow", "A", rows, rider_pass={l3: False}),
                _payload(tag, "results/real/harvest_moe", "A", rows),
                _payload(tag, "results/real/harvest_shadow", "A", rows, out="smoke.json"),
                _payload(tag, "results/real/harvest_shadow", "A", rows, layers=(7, 15)),
                _payload(tag, "results/real/harvest_shadow", "A", {l1: rows[l1][:1], l3: rows[l3]}),
                _payload(tag, "results/real/harvest_shadow", "A", rows, n_cells=29)):
        with pytest.raises(SystemExit):
            ro.conclude(bad, rp, verify_files=False)
    thin = {l1: [_row(l1, 2, "mlp256", 0.012, 0.006, 0.018, n_clusters=29), rows[l1][1]], l3: rows[l3]}
    with pytest.raises(SystemExit):
        ro.conclude(_payload(tag, "results/real/harvest_shadow", "A", thin), rp, verify_files=False)
    with pytest.raises(SystemExit):
        ro.conclude(pp, _payload(tag, "results/real/harvest_shadow_r", "A", rows), verify_files=False)
    with pytest.raises(SystemExit):
        ro.conclude(pp, p3, verify_files=False)
    oi = ro.conclude(pp, _payload(tag, "results/real/harvest_shadow_r", "B", rows, sk_of=sk, oracle_ok=False), verify_files=False)
    assert {o["label"] for o in oi["spaces"].values()} == {ro.LABEL_ORACLE_INVALID}
    ri = ro.conclude(pp, _payload(tag, "results/real/harvest_shadow_r", "B", rows, sk_of=sk, reader_ok={l1: False}), verify_files=False)
    assert ri["spaces"][l1]["label"] == ro.LABEL_READER_INVALID and ri["spaces"][l3]["label"] == ro.LABEL_NO_HEADROOM
    # with verify_files the committed payload / state files and oracle metas must exist and match
    with pytest.raises(SystemExit):
        ro.conclude(pp, rp)


def test_replay_helpers():
    assert orp.chunk_bounds(210, 16)[-1] == (208, 210) and len(orp.chunk_bounds(210, 16)) == 14
    with pytest.raises(ValueError):
        orp.chunk_bounds(0, 16)
    a = np.array([[[1, 3, 5, -1], [2, 4, -1, -1]]], np.int16)
    b = a.copy()
    b[0, 1, 1] = 9
    np.testing.assert_array_equal(orp.sets_equal_rows(a, b), [[True, False]])
    np.testing.assert_allclose(orp.set_overlap_rows(a, b), [[1.0, 0.5]])           # {2,9} logged, {2,4} recomputed
    np.testing.assert_allclose(orp.set_overlap_rows(np.full_like(a, -1), a), [[0.0, 0.0]])
    np.testing.assert_allclose(orp.set_overlap_rows(a, np.full_like(a, -1)), [[1.0, 1.0]])
    with pytest.raises(ValueError):
        orp.sets_equal_rows(a, a[:, :1])
    assert orp.seed_of_npz("shadow_s10.npz") == 10 and orp.seed_of_npz("results/real/x/moe_s8.npz") == 8
    raw = {"oracle": np.ones((2, 5, 1, 3), np.float16), "drawn": np.full((2, 5), 7, np.int32),
           "token_match": np.ones((2, 5), bool), "argmax_match": np.ones((2, 5), bool),
           "topp_maxabs": np.ones((2, 5), np.float32), "slot_match": np.ones((2, 5, 2), bool),
           "slot_overlap": np.ones((2, 5, 2), np.float16), "h_maxabs": np.ones((2, 5), np.float32),
           "h_absmax_logged": np.ones((2, 5), np.float32)}
    fin = orp.finalize_replay(raw, np.array([5, 3]))
    assert fin["oracle"][1, 3:].sum() == 0 and fin["oracle"][1, :3].sum() == 9 and fin["oracle"][0].sum() == 15
    for k in ("token_match", "argmax_match", "slot_match"):
        assert not fin[k][1, 3:].any() and fin[k][1, :3].all() and fin[k][0].all()
    for k in ("topp_maxabs", "h_maxabs", "h_absmax_logged"):
        assert fin[k][1, 3:].sum() == 0 and fin[k][1, :3].sum() == 3
    assert fin["slot_overlap"][1, 3:].sum() == 0 and fin["slot_overlap"][1, :3].sum() == 6
    assert (fin["drawn"] == 7).all()                                                 # the draws are kept whole
    assert raw["oracle"][1, 3:].sum() == 6 and raw["token_match"][1, 3:].all()       # inputs are not mutated
    N, T, L = 3, 6, 2
    tm = np.ones((N, T), bool)
    tm[2, 1] = False                  # one valid draw mismatch
    am = np.ones((N, T), bool)
    am[0, 0] = False
    sm = np.ones((N, T, L), bool)
    sm[0, 2, 1] = False
    sm[1, 5, :] = False               # beyond row 1's length: must not count
    so = np.ones((N, T, L), np.float16)
    so[0, 2, 1] = 0.5
    lengths = np.array([6, 4, 6])
    hm = np.zeros((N, T), np.float32)
    hm[2, 3] = 0.5
    hl = np.full((N, T), 10.0, np.float32)
    tp = np.zeros((N, T), np.float32)
    tp[1, 1] = 0.02
    arrs = {"token_match": tm, "argmax_match": am, "topp_maxabs": tp, "slot_match": sm, "slot_overlap": so,
            "h_maxabs": hm, "h_absmax_logged": hl}
    f = orp.fidelity_summary(arrs, lengths, ["a", "b"])
    assert f["n_valid_positions"] == 16 and f["token_match_rate"] == 15 / 16 and f["argmax_match_rate"] == 15 / 16
    assert f["topp_maxabs_percentiles"]["100"] == np.float32(0.02) and f["topp_maxabs_percentiles"]["50"] == 0.0
    assert f["slot_per_layer"]["a"]["exact_match_rate"] == 1.0 and f["slot_per_layer"]["a"]["mean_overlap"] == 1.0
    assert abs(f["slot_per_layer"]["b"]["exact_match_rate"] - 15 / 16) < 1e-12
    assert abs(f["slot_per_layer"]["b"]["mean_overlap"] - (15 + 0.5) / 16) < 1e-6
    assert f["slot_exact_match_rate_min"] == 15 / 16 and abs(f["slot_overlap_mean_min"] - 15.5 / 16) < 1e-6
    assert f["h_relmax_percentiles"]["100"] == 0.05 and f["h_maxabs_percentiles"]["50"] == 0.0 and f["h_exact_rate"] == 15 / 16
    with pytest.raises(ValueError):
        orp.fidelity_summary(arrs, lengths, ["a"])                                   # a short layer list is refused
    assert orp._fidelity_close(f, json.loads(json.dumps(f)))
    g = json.loads(json.dumps(f))
    g["token_match_rate"] = 0.5
    assert not orp._fidelity_close(f, g)
    meta = {"npz_file": "oracle_s0.npz", "parent_npz_file": "shadow_s0.npz", "parent_npz_sha256": "abc", "layers": [7, 15, 23, 31]}
    orp.oracle_meta_check(meta, {"shadow_s0.npz": "abc"}, (7, 15, 23, 31))
    for bad_parents, bad_layers in (({"shadow_s0.npz": "abd"}, (7, 15, 23, 31)), ({"shadow_s0.npz": "abc"}, (7, 15)),
                                    ({"shadow_s1.npz": "abc"}, (7, 15, 23, 31))):
        with pytest.raises(SystemExit):
            orp.oracle_meta_check(meta, bad_parents, bad_layers)


class _FakeHarvest:
    """A replication-shaped harvest: seeds 8-11 whose npz_shas dict is in
    LEXICOGRAPHIC order (s10, s11, s8, s9), as verified_seed_files yields;
    lengths differ per seed so the row-alignment leg can see a seed swap."""

    def __init__(self, T=4, rows_per_seed=2):
        self.T = T
        order = ["shadow_s10.npz", "shadow_s11.npz", "shadow_s8.npz", "shadow_s9.npz"]
        self.npz_shas = {n: hashlib.sha256(n.encode()).hexdigest() for n in order}
        self.n_rows = rows_per_seed * len(order)
        self.tokens = np.zeros((self.n_rows, T), np.int32)
        self.lengths = np.array([T, T - 1, T, T - 2, T - 1, T, T - 2, T - 1], np.int64)
        self.prompt_idx = np.array([0, 1] * len(order), np.int64)


def _write_side_files(tmp: Path, harvest: _FakeHarvest, layers=(7, 15, 23, 31), d=2, bad=None):
    tmp.mkdir(parents=True, exist_ok=True)
    order = list(harvest.npz_shas)
    for k, pf in enumerate(order):
        seed = orp.seed_of_npz(pf)
        n = 2
        r0 = k * n
        o = np.full((n, harvest.T, len(layers), d), float(seed), np.float16)   # the seed number, so placement is checkable
        lengths = harvest.lengths[r0:r0 + n].astype(np.int32)
        pidx = harvest.prompt_idx[r0:r0 + n].astype(np.int32)
        if bad == "lengths" and seed == 9:
            lengths = lengths[::-1].copy()
        arrs = {"token_match": np.ones((n, harvest.T), bool), "argmax_match": np.ones((n, harvest.T), bool),
                "topp_maxabs": np.zeros((n, harvest.T), np.float32), "slot_match": np.ones((n, harvest.T, 4), bool),
                "slot_overlap": np.ones((n, harvest.T, 4), np.float16), "h_maxabs": np.zeros((n, harvest.T), np.float32),
                "h_absmax_logged": np.ones((n, harvest.T), np.float32)}
        npz = tmp / f"oracle_s{seed}.npz"
        np.savez(npz, oracle=o, drawn=np.full((n, harvest.T), seed, np.int32), lengths=lengths, prompt_idx=pidx, **arrs)
        fid = orp.fidelity_summary(arrs, lengths.astype(np.int64), ["a", "b", "c", "d"])
        if bad == "fidelity" and seed == 10:
            fid = dict(fid, token_match_rate=0.5)
        meta = {"npz_file": npz.name, "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest(),
                "parent_npz_file": pf, "parent_npz_sha256": harvest.npz_shas[pf],
                "layers": list(layers if not (bad == "layers" and seed == 8) else (7, 15)),
                "layer_names": [f"model.layers.{i}.post_attention_layernorm" for i in layers],
                "sketch_layer_names": ["a", "b", "c", "d"], "d": d, "seed": seed, "fidelity": fid}
        if bad == "sha" and seed == 11:
            meta["parent_npz_sha256"] = "0" * 64
        (tmp / f"oracle_s{seed}.meta.json").write_text(json.dumps(meta))
        if bad == "missing" and seed == 10:
            npz.unlink()
            (tmp / f"oracle_s{seed}.meta.json").unlink()


def test_oracle_data_loads_in_the_harvest_order_and_refuses_misbinding(tmp_path):
    h = _FakeHarvest()
    _write_side_files(tmp_path / "ok", h)
    od = orp.OracleData(tmp_path / "ok", h, (7, 15, 23, 31))
    assert od.oracle_flat.shape == (8, 4, 8) and od.d == 2
    expect = np.repeat([10, 11, 8, 9], 2).astype(np.float16)                  # the HARVEST's order
    np.testing.assert_array_equal(od.oracle_flat[:, 0, 0], expect)
    assert od.oracle_flat[1, 3].sum() == 0 and od.oracle_flat[3, 2:].sum() == 0  # zeroed beyond each row's length
    assert list(od.npz_shas) == ["oracle_s10.npz", "oracle_s11.npz", "oracle_s8.npz", "oracle_s9.npz"]
    assert list(od.meta_shas) == ["oracle_s10.meta.json", "oracle_s11.meta.json", "oracle_s8.meta.json", "oracle_s9.meta.json"]
    assert od.token_match_rate_min == 1.0 and od.slot_overlap_mean_min == 1.0 and od.h_relmax_median_max == 0.0
    assert od.metas[0]["fidelity"]["argmax_match_rate"] == 1.0
    assert od.nbytes == 8 * 4 * 8 * 2
    for bad in ("sha", "layers", "lengths", "missing", "fidelity"):
        _write_side_files(tmp_path / bad, h, bad=bad)
        with pytest.raises(SystemExit):
            orp.OracleData(tmp_path / bad, h, (7, 15, 23, 31))
    with pytest.raises(SystemExit):
        orp.OracleData(tmp_path / "ok", h, (7, 15))
    with pytest.raises(SystemExit):
        orp.check_out_dir(tmp_path / "ok", tmp_path / "ok")
    (tmp_path / "mixed").mkdir()
    (tmp_path / "mixed" / "shadow_s0.meta.json").write_text("{}")
    with pytest.raises(SystemExit):
        orp.check_out_dir(tmp_path / "mixed", tmp_path / "harvest")
    orp.check_out_dir(tmp_path / "ok", tmp_path / "harvest")


def test_parser_defaults_and_ram_check():
    a = ro.build_parser().parse_args([])
    assert a.harvest == "results/real/harvest_shadow" and a.out == "results/real/fullfree_oracle_s1.json"
    assert a.space_tag == "concept" and a.n_slots == 512 and a.parent_finding is None and not a.resume
    assert ro.REGISTERED_OUTS == ("fullfree_oracle_s1.json", "fullfree_oracle_s1_r.json",
                                  "fullfree_oracle_s3.json", "fullfree_oracle_s3_r.json")
    assert ro.FID_TOKEN_MIN == 0.99 and ro.FID_OVERLAP_MIN == 0.95
    assert ro.FID_H_REL_MEDIAN_MAX == 0.01 and ro.FID_H_REL_P99_MAX == 0.05
    psutil = pytest.importorskip("psutil")
    real = psutil.virtual_memory()
    assert isinstance(int(real.available), int)          # the guard reads the live value
    # the pass / fail rule is tested against a FIXED available figure so the
    # test does not depend on what else is running on the box
    fixed = 20 * 1024 ** 3

    class _VM:
        available = fixed

    monkeypatch_target = psutil.virtual_memory
    try:
        psutil.virtual_memory = lambda: _VM()
        r = ro.ram_check(1024)
        assert r["ok"] and r["needed_bytes"] == 1024 and r["margin_bytes"] == 8 * 1024 ** 3
        assert r["available_bytes"] == fixed
        assert not ro.ram_check(fixed - 8 * 1024 ** 3 + 1)["ok"]
        assert ro.ram_check(fixed - 8 * 1024 ** 3)["ok"]
        assert not ro.ram_check(10 ** 15)["ok"]
    finally:
        psutil.virtual_memory = monkeypatch_target


@pytest.mark.parametrize("pair", [("fullfree_oracle_s1.json", "fullfree_oracle_s1_r.json"),
                                  ("fullfree_oracle_s3.json", "fullfree_oracle_s3_r.json")])
def test_committed_payloads_reproduce_their_conclusion(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("OQ-19 draft payloads not present (OQ-19 is an unfrozen draft; nothing has run)")
    pp, rp = (json.loads(p.read_text()) for p in paths)
    for d in (pp, rp):
        assert d["partial"] is False and isinstance(d["resumed_cells"], int)
        assert d["n_cells"] == ro.N_TRAINED_OF_TAG[d["tag"]]
        assert d["oracle"]["validity"]["ok"] is True and d["twin"]["perm_sha256_equals_committed_twin"] is True
        for sp, ps in d["per_space"].items():
            assert ps["rider"]["pass"]
            assert ps["gate"]["fires"] == (ps["reader_valid"]["ok"] and ro.gate_fires(ps["gate"]["row"]))
    out = ro.conclude(pp, rp)      # re-hashes the committed metas; the npz only when present
    for o in out["spaces"].values():
        assert o["label"] in (ro.LABEL_HEADROOM, ro.LABEL_NO_HEADROOM, ro.LABEL_NOT_SHOWN, ro.LABEL_SPLIT,
                              ro.LABEL_READER_INVALID, ro.LABEL_ORACLE_INVALID)

# ---------------------------------------------------------------------------
# the DRAFT guard (added 2026-10-01 at the code-reviewer's WARN: the guard had no test)
# ---------------------------------------------------------------------------

def test_draft_guard_refuses_every_run_while_unfrozen(monkeypatch):
    """main() refuses before parsing anything heavy while DRAFT_UNFROZEN is set; the
    parser has no required arguments, so the defaults reach the refusal."""
    assert ro.DRAFT_UNFROZEN is True
    monkeypatch.setattr(sys, "argv", ["run_fullfree_oracle.py"])
    with pytest.raises(SystemExit, match="UNFROZEN DRAFT"):
        ro.main()


def test_draft_flag_is_tied_to_the_record():
    """The flag flips only in the freeze commit that inserts the registration block into
    docs/BLUEPRINT.md: the two must move together or this test goes red."""
    blueprint = (ROOT / "docs" / "BLUEPRINT.md").read_text(encoding="utf-8")
    registered = "OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION" in blueprint
    assert ro.DRAFT_UNFROZEN == (not registered)

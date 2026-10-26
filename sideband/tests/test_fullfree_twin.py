"""tools/run_fullfree_twin.py (OQ-17 post-hoc twin-inertness diagnostic):
the CI-safe layer — the within-split PROMPT-level derangement has no fixed
points, never maps a row to its own prompt, preserves the splits and the
generation index; the corrected-twin block reads ANOTHER prompt's row at a
valid (wrapped) anchor through the registered slots class, against rows
padded with -1 beyond their length; the twin factory keeps fplus_b's block
order and dims with byte-identical shared blocks; the reproduction gate
refuses a one-success perturbation and a wrong header; the branches
(incl. the clean-fire rule and the +0.005 boundary) and the T reading are
mechanical; --conclude-from refuses the wrong inputs; and (when present)
the committed twin payloads' three readouts recompute from the state files
at 1e-12. No torch."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_fullfree as rf  # noqa: E402
import run_fullfree_twin as rt  # noqa: E402
from run_probes import SlotsAnchorBlock, cell_id, margins, parse_state  # noqa: E402
from sideband.probes import anchor_table, slots_multi_hot  # noqa: E402

SPACE = "L1_concept_k16"


def _layout(n_prompts: int, n_gen: int, split_of_prompt) -> tuple[np.ndarray, np.ndarray]:
    """Seed-major rows like the harvests: row = k * n_prompts + p."""
    prompt_idx = np.tile(np.arange(n_prompts), n_gen)
    split = np.array([split_of_prompt(int(p)) for p in prompt_idx])
    return prompt_idx, split


def test_prompt_derangement_no_fixed_points_own_prompt_or_split_crossing():
    P, G = 14, 3
    prompt_idx, split = _layout(P, G, lambda p: ("train", "train", "val", "test")[p % 4])
    p0 = rt.derangement_by_prompt(prompt_idx, split, 0)
    p1 = rt.derangement_by_prompt(prompt_idx, split, 1)
    n = P * G
    assert sorted(p0.tolist()) == list(range(n))
    assert not np.any(p0 == np.arange(n))
    assert np.all(prompt_idx[p0] != prompt_idx)
    assert np.array_equal(split[p0], split)
    assert np.array_equal(p0 // P, np.arange(n) // P)        # same generation index
    assert not np.array_equal(p0, p1)
    assert np.array_equal(p0, rt.derangement_by_prompt(prompt_idx, split, 0))
    # every prompt's rows map to ONE other prompt's rows (a prompt-level map)
    for p in range(P):
        assert len(set(prompt_idx[p0[prompt_idx == p]].tolist())) == 1
    with pytest.raises(SystemExit):                          # a one-prompt split
        rt.derangement_by_prompt(*_layout(5, 2, lambda p: "test" if p == 0 else "train"), 0)
    with pytest.raises(SystemExit):                          # unequal row counts
        rt.derangement_by_prompt(np.array([0, 1, 1, 2, 2]), np.array(["train"] * 5), 0)
    with pytest.raises(SystemExit):                          # a prompt spanning splits
        rt.derangement_by_prompt(np.array([0, 1, 0, 1]), np.array(["train", "train", "test", "test"]), 0)


def test_other_row_block_reads_the_other_prompt_at_a_wrapped_anchor():
    n_rows, T, L, top, n_slots = 6, 12, 3, 4, 8
    lengths = np.array([12, 5, 9, 12, 7, 10])
    # every slot id of row r equals r inside the row's length, -1 (padding) beyond it
    slots = np.broadcast_to(np.arange(n_rows, dtype=np.int16)[:, None, None, None],
                            (n_rows, T, L, top)).copy()
    for r in range(n_rows):
        slots[r, lengths[r]:] = -1
    prompt_idx = np.arange(n_rows)                            # one row per prompt
    split = np.array(["train"] * 3 + ["test"] * 3)
    perm = rt.derangement_by_prompt(prompt_idx, split, 0)
    rows = np.array([0, 1, 2, 3, 4, 5, 0, 3])
    anchors = np.array([0, 4, 8, 11, 6, 9, 3, 2])
    blk = rt.OtherRowSlotsBlock(slots, rows, anchors, lengths, perm, n_slots)
    idx = np.arange(len(rows))
    other = perm[rows]
    oa = anchors % lengths[other]
    assert np.all(oa < lengths[other]) and np.all(other != rows)
    assert np.any(anchors >= lengths[other])                  # the wrap case is exercised
    got = blk.batch(idx)
    np.testing.assert_array_equal(got, slots_multi_hot(slots[other, oa], n_slots))
    assert blk.dim == L * n_slots
    for i in range(len(rows)):                                # one-hot at the OTHER row's id per layer
        assert np.nonzero(got[i])[0].tolist() == [layer * n_slots + other[i] for layer in range(L)]
    aligned = SlotsAnchorBlock(slots, rows, anchors, n_slots).batch(idx)
    assert not np.any(np.all(got == aligned, axis=1))
    assert blk.wrapped == int(np.sum(oa != anchors))


def test_twin_factory_keeps_fplus_b_order_dims_and_shared_blocks():
    rng = np.random.default_rng(3)
    n_rows, T, D, L, top = 6, 10, 6, 2, 3
    n_slots, n_bins = 8, 2048
    hidden = rng.normal(size=(n_rows, T, D)).astype(np.float16)
    top_ids = rng.integers(0, 50000, size=(n_rows, T, 32)).astype(np.int64)
    slots = rng.integers(0, n_slots, size=(n_rows, T, L, top)).astype(np.int16)
    lengths = np.array([10, 8, 10, 9, 7, 10])
    prompt_idx, split = _layout(3, 2, lambda p: "train")    # three prompts, two generations each
    moments = rf.train_moments(hidden, lengths, split)
    perm = rt.derangement_by_prompt(prompt_idx, split, 0)
    f_r = rt.make_twin_factory(top_ids, hidden, slots, lengths, n_slots, moments, perm, n_bins)
    reg = rf.make_factories(top_ids, hidden, slots, lengths, n_slots, moments, n_bins)
    rows = np.array([0, 1, 3, 4, 5])
    anchors = np.array([2, 5, 1, 6, 9])
    br, bb, bn = f_r(rows, anchors), reg["fplus_b"](rows, anchors), reg["fplus_n"](rows, anchors)
    assert [b.dim for b in br] == [b.dim for b in bb] == [b.dim for b in bn]
    assert [type(b).__name__ for b in br[:2]] == [type(b).__name__ for b in bb[:2]]
    idx = np.arange(len(rows))
    np.testing.assert_array_equal(br[0].batch(idx), bb[0].batch(idx))
    np.testing.assert_array_equal(br[1].batch(idx), bb[1].batch(idx))
    other = perm[rows]
    oa = anchors % lengths[other]
    np.testing.assert_array_equal(br[2].batch(idx), slots_multi_hot(slots[other, oa], n_slots))


def test_twin_geometry_counts_and_same_prompt_is_zero():
    prompt_idx, split = _layout(4, 2, lambda p: "train" if p < 2 else "test")
    lengths = np.array([30, 40, 50, 25, 33, 41, 52, 27])
    perm = rt.derangement_by_prompt(prompt_idx, split, 0)
    g = rt.twin_geometry(lengths, perm, 2, 64, prompt_idx)
    rows, anchors = anchor_table(lengths, 2, 64)
    other = perm[rows]
    assert g["n_anchors"] == len(rows) and g["shift"] == 17
    assert g["corrected_twin_wrapped_frac"] == pytest.approx(float(np.mean(anchors >= lengths[other])))
    assert g["shift_twin_future_frac"] == pytest.approx(float(np.mean(anchors + 17 < lengths[rows])))
    assert g["corrected_twin_same_prompt_frac"] == 0.0
    assert "corrected_twin_same_prompt_frac" not in rt.twin_geometry(lengths, perm, 2, 64)


# --- synthetic committed cells ---------------------------------------------

def _cell(feats, seed, succ, n=10, offset=2, cap="mlp256", shuffled=False):
    clusters = {p: [int(s), n] for p, s in enumerate(succ)}
    acc = sum(s for s, _ in clusters.values()) / (n * len(succ))
    return {"cell": cell_id(SPACE, offset, feats, cap, seed, shuffled), "space": SPACE,
            "offset": offset, "features": feats, "capacity": cap, "seed": seed,
            "shuffled": shuffled, "test_acc": acc, "majority_rate_test": 0.5, "best_epoch": 0,
            "_clusters": clusters}


def _committed(rng, n_clusters=30):
    cells = []
    for seed in (0, 1, 2):
        base = rng.integers(3, 8, size=n_clusters)
        cells.append(_cell("fplus", seed, base))
        cells.append(_cell("fplus_b", seed, np.clip(base + rng.integers(-1, 2, size=n_clusters), 0, 10)))
        cells.append(_cell("fplus_n", seed, np.clip(base + rng.integers(-1, 2, size=n_clusters), 0, 10)))
    return cells


def _payload_from(cells):
    return {"d_fplus_b_vs_fplus_n": margins(cells, "fplus_b", expected_clusters=30, base_feats="fplus_n"),
            "mt_fplus_b_vs_fplus": margins(cells, "fplus_b", expected_clusters=30, base_feats="fplus"),
            "mn_fplus_n_vs_fplus_dilution": margins(cells, "fplus_n", expected_clusters=30, base_feats="fplus")}


def test_reproduction_gate_refuses_a_one_success_perturbation(tmp_path):
    rng = np.random.default_rng(5)
    cells = _committed(rng)
    payload = _payload_from(cells)
    got = rt.reproduce_gate_rows(cells, payload, SPACE)
    assert set(got) == {"D", "Mt", "Mn"} and got["D"]["pair"] == "fplus_b-fplus_n"
    mutant = [json.loads(json.dumps(c)) for c in cells]
    mutant[4]["_clusters"]["7"][0] += 1                      # one more success in one cluster
    with pytest.raises(SystemExit):
        rt.reproduce_gate_rows(mutant, payload, SPACE)
    with pytest.raises(SystemExit):                          # a missing row
        rt.reproduce_gate_rows(cells, {**payload, "mn_fplus_n_vs_fplus_dilution": []}, SPACE)
    # the state loader binds the harvest through the header
    shas = {"a.npz": "1" * 64}
    good = tmp_path / "ok.state.jsonl"
    good.write_text("\n".join([json.dumps({"kind": "state_header", "harvest_npz_sha256": shas})]
                              + [json.dumps(c) for c in cells]) + "\n")
    loaded = rt.load_fullfree_cells(good, shas)
    assert len(loaded) == 9 and all(isinstance(k, int) for k in loaded[0]["_clusters"])
    with pytest.raises(SystemExit):
        rt.load_fullfree_cells(good, {"a.npz": "2" * 64})
    bad = tmp_path / "bad.state.jsonl"
    bad.write_text("\n".join(json.dumps(c) for c in cells) + "\n")
    with pytest.raises(SystemExit):
        rt.load_fullfree_cells(bad, shas)


def test_per_cluster_corr_is_the_pearson_of_seed_summed_deltas():
    rng = np.random.default_rng(6)
    cells = _committed(rng)
    out = rt.per_cluster_corr(cells, SPACE, "fplus_b", "fplus_n")
    assert out["n_clusters"] == 30 and out["pairs"] == ["fplus_b-fplus", "fplus_n-fplus"]
    same = rt.per_cluster_corr(cells, SPACE, "fplus_b", "fplus_b")
    assert same["pearson"] == pytest.approx(1.0)
    assert rt.per_cluster_corr(cells, SPACE, "fplus_b", "fplus_r") is None


# --- branches ----------------------------------------------------------------

def _row(margin, lo, hi, per_seed, pair=rt.PAIR_DR, n_seeds=3, n_clusters=30):
    return {"space": SPACE, "offset": 2, "capacity": "mlp256", "pair": pair,
            "margin": margin, "ci95": [lo, hi],
            "per_seed_margin": {str(i): v for i, v in enumerate(per_seed)},
            "n_seeds": n_seeds, "n_clusters": n_clusters}


FIRE = _row(0.006, 0.002, 0.010, (0.005, 0.006, 0.007))
BELOW = _row(0.001, -0.001, 0.003, (0.001, 0.001, 0.001))
STRADDLE = _row(0.003, 0.001, 0.0052, (0.004, 0.002, 0.003))
MNR_OK = _row(0.001, -0.001, 0.003, (0.001,) * 3, pair=rt.PAIR_MNR)
MNR_HARM = _row(-0.003, -0.005, -0.001, (-0.003,) * 3, pair=rt.PAIR_MNR)


def test_branches_clean_fire_rule_boundary_and_guards():
    assert rt.twin_branch(FIRE, FIRE, MNR_OK, MNR_OK) == "TWIN-MASKED"
    assert rt.twin_branch(FIRE, FIRE, MNR_OK, MNR_HARM) == "TWIN-SPLIT"       # one fire is dilution-bought
    assert rt.twin_branch(FIRE, FIRE, MNR_HARM, MNR_HARM) == "TWIN-DEPENDENT"  # both bought by dilution
    assert rt.twin_branch(FIRE, FIRE) == "TWIN-DEPENDENT"                      # no Mn_r rows: never MASKED
    assert rt.twin_branch(FIRE, BELOW, MNR_OK, MNR_OK) == "TWIN-SPLIT"
    assert rt.twin_branch(BELOW, FIRE, MNR_OK, MNR_OK) == "TWIN-SPLIT"
    assert rt.twin_branch(BELOW, BELOW, MNR_OK, MNR_OK) == "TWIN-ROBUST"
    assert rt.twin_branch(BELOW, BELOW) == "TWIN-ROBUST"
    assert rt.twin_branch(BELOW, STRADDLE, MNR_OK, MNR_OK) == "TWIN-DEPENDENT"
    assert rt.twin_branch(STRADDLE, STRADDLE, MNR_OK, MNR_OK) == "TWIN-DEPENDENT"
    assert rt.twin_branch(None, BELOW, MNR_OK, MNR_OK) == "TWIN-INCOMPLETE"
    two_seed = _row(0.001, -0.001, 0.003, (0.001, 0.001), n_seeds=2)
    assert rt.twin_branch(two_seed, BELOW) == "TWIN-INCOMPLETE"               # ROBUST needs the guards
    wrong_pair = _row(0.001, -0.001, 0.003, (0.001,) * 3, pair="fplus_b-fplus_n")
    assert rt.twin_branch(wrong_pair, BELOW) == "TWIN-INCOMPLETE"
    assert rt.fires(_row(0.005, 0.002, 0.010, (0.005, 0.005, 0.005)))         # the boundary fires
    assert not rt.fires(_row(0.0049999, 0.002, 0.010, (0.005, 0.005, 0.005)))
    assert not rt.fires(_row(0.006, 0.002, 0.010, (0.005, 0.006, 0.007), pair="fplus_b-fplus_n"))
    assert not rt.fires(_row(0.006, 0.002, 0.010, (0.005, 0.006, 0.007), n_seeds=2))
    assert not rt.fires(_row(0.006, 0.002, 0.010, (0.005, 0.006, 0.007), n_clusters=29))
    assert not rt.fires(_row(0.006, 0.002, 0.010, (0.005, -0.001, 0.007)))
    assert not rt.fires(_row(0.006, -0.001, 0.010, (0.005, 0.006, 0.007)))
    assert rt.fires_clean(FIRE, MNR_OK) and not rt.fires_clean(FIRE, MNR_HARM)
    assert not rt.fires_clean(FIRE, None)
    assert not rt.fires_clean(FIRE, _row(0.001, -0.001, 0.003, (0.001,) * 3, pair=rt.PAIR_T))
    tp = _row(0.003, 0.001, 0.005, (0.003,) * 3, pair=rt.PAIR_T)
    tz = _row(0.001, -0.001, 0.003, (0.001,) * 3, pair=rt.PAIR_T)
    assert rt.t_reading(tp, tp) == "TWIN-INFORMATIVE"
    assert rt.t_reading(tp, tz) == "TWIN-INFORMATION-NOT-SHOWN"
    assert rt.t_reading(tp, None) is None
    assert rt.t_reading(_row(0.003, 0.001, 0.005, (0.003,) * 3), tp) is None


# --- conclude -----------------------------------------------------------------

def _twin_payload(role, harvest, out, ff, dr=None, mnr=None, partial=False, shas=None,
                  n_cells=3, seed_base=rt.TWIN_SEED_BASE, ff_shas=("x", "y")):
    dr = dr or BELOW
    mnr = mnr or MNR_OK
    return {"space": "L1_concept_k16", "harvest": harvest, "partial": partial, "n_cells": n_cells,
            "reproduced_registered_gate_rows": True,
            "registered_gate_rows": {"D": dr, "Mt": dr, "Mn": dr},
            "d_r_fplus_b_vs_fplus_r": [dr], "mn_r_fplus_r_vs_fplus": [mnr],
            "t_fplus_n_vs_fplus_r": [_row(0.002, 0.001, 0.003, (0.002,) * 3, pair=rt.PAIR_T)],
            "twin": {"arm": "fplus_r", "seed_base": seed_base},
            "provenance": {"args": {"out": out, "fullfree_payload": ff},
                           "harvest_npz_sha256": shas or {"x": role},
                           "fullfree_payload_sha256": ff_shas[0], "fullfree_state_sha256": ff_shas[1]}}


P_ARGS = ("primary", "results/real/harvest_shadow", "results/real/fullfree_s1_twin.json",
          "results/real/fullfree_s1.json")
R_ARGS = ("replication", "results/real/harvest_shadow_r", "results/real/fullfree_s1_r_twin.json",
          "results/real/fullfree_s1_r.json")


def test_conclude_reading_and_refusals():
    p, r = _twin_payload(*P_ARGS), _twin_payload(*R_ARGS)
    out = rt.conclude(p, r, verify_files=False)
    assert out["branch"] == "TWIN-ROBUST" and out["t_reading"] == "TWIN-INFORMATIVE"
    assert out["d_r_fires_raw"] == {"primary": False, "replication": False}
    assert out["deciding_upper_minus_floor"]["primary"] == pytest.approx(0.003 - 0.005)
    masked = rt.conclude(_twin_payload(*P_ARGS, dr=FIRE), _twin_payload(*R_ARGS, dr=FIRE), verify_files=False)
    assert masked["branch"] == "TWIN-MASKED" and masked["d_r_fires_clean"] == {"primary": True, "replication": True}
    bought = rt.conclude(_twin_payload(*P_ARGS, dr=FIRE, mnr=MNR_HARM),
                         _twin_payload(*R_ARGS, dr=FIRE, mnr=MNR_HARM), verify_files=False)
    assert bought["branch"] == "TWIN-DEPENDENT" and bought["corrected_twin_ci_clear_harmful"] == {"primary": True, "replication": True}
    for bad in (_twin_payload(*P_ARGS, partial=True),
                _twin_payload("primary", "results/real/harvest_shadow", "results/smoke/x.json", P_ARGS[3]),
                _twin_payload("primary", "results/real/harvest_shadow_r", P_ARGS[2], P_ARGS[3]),
                _twin_payload(*P_ARGS, n_cells=2),
                _twin_payload(*P_ARGS, seed_base=7),
                _twin_payload("primary", "results/real/harvest_shadow", P_ARGS[2], "results/real/fullfree_s1_r.json")):
        with pytest.raises(SystemExit):
            rt.conclude(bad, r, verify_files=False)
    with pytest.raises(SystemExit):                          # same harvest twice
        rt.conclude(p, _twin_payload(*R_ARGS, shas={"x": "primary"}), verify_files=False)
    q = dict(p)
    q["reproduced_registered_gate_rows"] = False
    with pytest.raises(SystemExit):
        rt.conclude(q, r, verify_files=False)
    s3 = _twin_payload("primary", "results/real/harvest_moe", "results/real/fullfree_s3_twin.json",
                       "results/real/fullfree_s3.json")
    s3["space"] = "L1_olmoe_k16"
    with pytest.raises(SystemExit):
        rt.conclude(s3, r, verify_files=False)


def test_conclude_verifies_the_paired_fullfree_files_on_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results" / "real").mkdir(parents=True)
    ffp = tmp_path / "results" / "real" / "fullfree_s1.json"
    ffs = tmp_path / "results" / "real" / "fullfree_s1.json.state.jsonl"
    ffp.write_text("{}")
    ffs.write_text("header\n")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    p = _twin_payload(*P_ARGS, ff_shas=(sha(ffp), sha(ffs)))
    rt._check_payload(p, "primary", verify_files=True)
    ffs.write_text("header\nchanged\n")
    with pytest.raises(SystemExit):
        rt._check_payload(p, "primary", verify_files=True)
    ffs.unlink()
    with pytest.raises(SystemExit):
        rt._check_payload(p, "primary", verify_files=True)


def test_parser_defaults_and_registered_pairing():
    d = vars(rt.build_parser().parse_args([]))
    assert d["harvest"] == "results/real/harvest_shadow"
    assert d["out"] == "results/real/fullfree_s1_twin.json"
    assert d["fullfree_payload"] == "results/real/fullfree_s1.json"
    assert d["space_tag"] == "concept" and d["n_slots"] == 512 and d["only"] is None
    assert d["resume"] is False
    assert rt.FULLFREE_OF_OUT["fullfree_s3_r_twin.json"] == "fullfree_s3_r.json"
    assert rt.TWIN_SEED_BASE == 1000 and rt.ARM == "fplus_r"
    assert rt.PAIR_DR == "fplus_b-fplus_r" and rt.PAIR_T == "fplus_n-fplus_r" and rt.PAIR_MNR == "fplus_r-fplus"


@pytest.mark.parametrize("pair", [("fullfree_s1_twin.json", "fullfree_s1_r_twin.json"),
                                  ("fullfree_s3_twin.json", "fullfree_s3_r_twin.json")])
def test_committed_twin_payloads_recompute_from_the_state_files(pair):
    paths = [ROOT / "results" / "real" / n for n in pair]
    if not all(p.exists() for p in paths):
        pytest.skip("registered OQ-17 twin payloads not present")
    pp, rp = (json.loads(p.read_text()) for p in paths)
    for d, path in ((pp, paths[0]), (rp, paths[1])):
        assert d["partial"] is False and d["n_cells"] == 3 and d["resumed_cells"] == 0
        assert d["reproduced_registered_gate_rows"] and d["standardization"]["matches_registered"]
        assert d["provenance"]["arm_dims_total"]["fplus_r"] == d["provenance"]["arm_dims_total"]["fplus_b"]
        for seed in ("0", "1", "2"):
            g = d["twin"]["geometry_at_gate_offset"][seed]
            assert g["corrected_twin_same_prompt_frac"] == 0.0
            assert 0.0 <= g["corrected_twin_wrapped_frac"] < 0.2 and g["shift_twin_future_frac"] > 0.8
        # recompute the three readouts from the twin state file + the paired fullfree state file
        ff = ROOT / d["provenance"]["args"]["fullfree_payload"]
        space = d["space"]
        shas = d["provenance"]["harvest_npz_sha256"]
        ff_cells = rt.load_fullfree_cells(Path(str(ff) + ".state.jsonl"), shas)
        twin_cells = list(parse_state(Path(str(path) + ".state.jsonl").read_text(), shas).values())
        assert len(twin_cells) == 3
        pooled = twin_cells + ff_cells
        for key, top, base in (("d_r_fplus_b_vs_fplus_r", "fplus_b", "fplus_r"),
                               ("mn_r_fplus_r_vs_fplus", "fplus_r", "fplus"),
                               ("t_fplus_n_vs_fplus_r", "fplus_n", "fplus_r")):
            got = rf.gate_row(margins(pooled, top, expected_clusters=30, base_feats=base), space)
            want = rf.gate_row(d[key], space)
            assert len(d[key]) == 1 and want["n_seeds"] == 3 and want["n_clusters"] == 30
            assert abs(got["margin"] - want["margin"]) <= 1e-12
            assert max(abs(a - b) for a, b in zip(got["ci95"], want["ci95"])) <= 1e-12
        assert d["gate"]["d_r_fires_raw"] == rt.fires(d["gate"]["d_r_row"])
    out = rt.conclude(pp, rp)
    # pinned 2026-10-16 (lane C, image audit S7a-C-6) as F-24's twin reading landed them on 2026-09-06:
    # TWIN-ROBUST at both sources, T not informative; a changed payload or state file flags here
    assert out["branch"] == "TWIN-ROBUST" and out["t_reading"] == "TWIN-INFORMATION-NOT-SHOWN"

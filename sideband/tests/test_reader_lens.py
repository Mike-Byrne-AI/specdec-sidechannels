"""tools/run_reader_lens.py: the readers, grids, readouts, label rules, state loading, payload verification and
refusals on CPU fixtures. The registered-reader path is checked against run_probes.run_cell on a small fake
harvest object (same blocks, same trainer call, bit-exact output) for the (a), (c) and factory-extra arms; the
two-tower trainer is checked against sideband.probes.train_probe with no slots tower (bit-exact). Torch is
imported only inside the trainers, on CPU. No frozen file is imported by path; nothing under results/ is read.
Dated note 2026-10-15 (lane A, CI portability): the module-level torch import-or-skip that skipped all 26 tests
wherever torch is absent (the CI installs .[dev] only) is replaced by a per-test skip on the five that need torch
(measured with torch masked: 5 failed, 21 passed); the file's sha12 moves off the FILES AT THE FREEZE line of the
READER-AND-LENS RE-TEST AT S3 REGISTRATION in docs/BLUEPRINT.md, recorded there by a DATED AMENDMENT of the same date."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
import run_reader_lens as rl  # noqa: E402
import run_probes as rp  # noqa: E402
from run_fullfree import TokAnchorBlock, HiddenZBlock  # noqa: E402
from run_probes import SlotsAnchorBlock, cell_id  # noqa: E402
from sideband.probes import DenseBlock, train_probe  # noqa: E402


def _has(mod: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(mod) is not None


needs_torch = pytest.mark.skipif(not _has("torch"), reason="needs torch")   # the five tests that need torch (2026-10-15)

L1, LOP, BAL = rl.SPACE_L1["olmoe"], rl.SPACE_L3_LOP, rl.SPACE_L3_BAL
S3_SPACES = (L1, LOP, BAL)


# ---------------------------------------------------------------------------
# blocks and readers
# ---------------------------------------------------------------------------

def _dense(gen, n, d, scale=1.0):
    return DenseBlock((scale * gen.standard_normal((n, d))).astype(np.float32))


def test_hz_rescale_scales_the_hz_block_alone_to_the_aligned_slots_norm():
    gen = np.random.default_rng(0)
    n = 400
    a1, a2 = _dense(gen, n, 5, 0.1), _dense(gen, n, 3, 0.1)
    tok, hz, slots = _dense(gen, n, 7, 1.0), _dense(gen, n, 11, 30.0), _dense(gen, n, 4, 3.0)
    fams = [("A", [a1, a2]), ("TOK", [tok]), ("HZ", [hz]), ("SLOTS", [slots])]
    idx = np.arange(n)
    m = rl.mean_squared_norms([("HZ", [hz]), ("S", [slots])], idx, batch=64)
    assert abs(m["HZ"] - (hz.batch(idx).astype(np.float64) ** 2).sum(1).mean()) < 1e-6
    blocks, info = rl.hz_rescale(fams, slots, idx)
    assert abs(info["c_hz"] - np.sqrt(m["S"] / m["HZ"])) < 1e-9 and abs(info["m_hz"] - m["HZ"]) < 1e-9 * m["HZ"]
    assert [type(b).__name__ for b in blocks] == ["DenseBlock", "DenseBlock", "DenseBlock", "ScaledBlock", "DenseBlock"]
    assert blocks[0] is a1 and blocks[2] is tok and blocks[4] is slots           # unscaled families are the same objects
    scaled = blocks[3].batch(idx).astype(np.float64)
    assert abs((scaled ** 2).sum(1).mean() - m["S"]) < 1e-3 and blocks[3].dim == hz.dim
    plain, info2 = rl.hz_rescale([("A", [a1]), ("TOK", [tok]), ("SLOTS", [slots])], slots, idx)
    assert info2["c_hz"] is None and plain == [a1, tok, slots]


def test_family_of_blocks_classifies_the_real_block_classes_in_order():
    gen = np.random.default_rng(1)
    rows, anchors = np.array([0, 1]), np.array([0, 0])
    tok = TokAnchorBlock(gen.integers(0, 50, (2, 3, 4)), rows, anchors, n_bins=8)
    hz = HiddenZBlock(gen.standard_normal((2, 3, 6)).astype(np.float32), rows, anchors,
                      {"mu": np.zeros(6, np.float32), "sd": np.ones(6, np.float32), "lo": -np.ones(6, np.float32) * 9,
                       "hi": np.ones(6, np.float32) * 9})
    sl = SlotsAnchorBlock(gen.integers(0, 4, (2, 3, 2, 2)), rows, anchors, n_slots=4)
    fams = rl.family_of_blocks([DenseBlock(np.ones((2, 1), np.float32))], [tok, hz, sl])
    assert [f for f, _ in fams] == ["A", "TOK", "HZ", "SLOTS"]
    with pytest.raises(SystemExit, match="unknown extra block"):
        rl.family_of_blocks([], [DenseBlock(np.ones((2, 1), np.float32))])


def _toy_problem(seed=0, n=600, d_a=9, d_b=6, n_classes=4):
    gen = np.random.default_rng(seed)
    xa = gen.standard_normal((n, d_a)).astype(np.float32)
    xb = gen.standard_normal((n, d_b)).astype(np.float32)
    w = gen.standard_normal((d_a + d_b, n_classes))
    y = (np.concatenate([xa, xb], axis=1) @ w).argmax(1).astype(np.int64)
    split = np.array(["train"] * 400 + ["val"] * 100 + ["test"] * 100)
    return DenseBlock(xa), DenseBlock(xb), y, split, n_classes


@needs_torch
def test_two_tower_with_no_slots_tower_is_train_probe_mlp256_bit_exact():
    a, b, y, split, k = _toy_problem()
    ref = train_probe([a, b], y, split, k, "mlp256", seed=3, device="cpu", epochs=4, batch_size=128, lr=3e-3)
    got = rl.train_two_tower([a, b], [], y, split, k, seed=3, device="cpu", epochs=4, batch_size=128, lr=3e-3)
    assert got["test_acc"] == ref["test_acc"] and got["val_acc_best"] == ref["val_acc_best"]
    assert got["best_epoch"] == ref["best_epoch"] and np.array_equal(got["test_correct"], ref["test_correct"])
    assert got["towers"] == {"a_dim": 15, "b_dim": 0, "width_a": 256, "width_b": 0}


@needs_torch
def test_two_tower_with_a_slots_tower_trains_and_differs_from_the_single_tower():
    a, b, y, split, k = _toy_problem(seed=1)
    one = rl.train_two_tower([a, b], [], y, split, k, seed=0, device="cpu", epochs=3, batch_size=128)
    two = rl.train_two_tower([a], [b], y, split, k, seed=0, device="cpu", epochs=3, batch_size=128, width_b=8)
    assert two["towers"] == {"a_dim": 9, "b_dim": 6, "width_a": 256, "width_b": 8}
    assert 0.0 <= two["test_acc"] <= 1.0 and two["n_train"] == 400
    assert not (two["test_acc"] == one["test_acc"] and np.array_equal(two["test_correct"], one["test_correct"]))


def test_registered_reader_r0_is_train_probes_own_default_budget():
    sig = inspect.signature(train_probe).parameters
    assert sig["epochs"].default == rl.READERS["R0"]["epochs"] == 30 and sig["lr"].default == rl.READERS["R0"]["lr"] == 3e-3
    assert sig["batch_size"].default == 4096
    assert rl.READERS["RL"]["epochs"] == 60 and rl.READERS["RL"]["lr"] == 1e-3 and rl.READERS["RN"]["kind"] == "hz_rescaled"


# ---------------------------------------------------------------------------
# the R0 runner against run_cell on a fake harvest
# ---------------------------------------------------------------------------

class FakeData:
    """The HarvestData surface run_cell and run_cell_reader touch: lengths, tokens, prompt_idx, row_split(), array()."""

    def __init__(self, seed=0, n_rows=14, T=12, n_tok=40, n_slots=4, n_layers=2, top=2, hidden=5):
        gen = np.random.default_rng(seed)
        self.lengths = gen.integers(6, T + 1, n_rows).astype(np.int64)
        self.tokens = gen.integers(0, n_tok, (n_rows, T)).astype(np.int64)
        self.prompt_idx = np.arange(n_rows, dtype=np.int64)          # ids 5, 12 -> val and 6, 13 -> test (idx % 7)
        self._arrays = {
            "mass16": gen.random((n_rows, T, 16)).astype(np.float32), "mass32": gen.random((n_rows, T, 32)).astype(np.float32),
            "mass64": gen.random((n_rows, T, 64)).astype(np.float32), "mass512": gen.random((n_rows, T, 512)).astype(np.float32),
            "entropy": gen.random((n_rows, T)).astype(np.float32), "top_p": gen.random((n_rows, T, 32)).astype(np.float32),
            "slots": gen.integers(0, n_slots, (n_rows, T, n_layers, top)).astype(np.int64),
            "hidden": gen.standard_normal((n_rows, T, hidden)).astype(np.float32),
            "top_ids": gen.integers(0, n_tok, (n_rows, T, 32)).astype(np.int64),
        }

    def array(self, key):
        return self._arrays[key]

    def row_split(self):
        from sideband.harvest import split_of_prompt
        return np.array([split_of_prompt(int(i)) for i in self.prompt_idx])


def _spaces(n_tok=40, n_classes=3):
    gen = np.random.default_rng(5)
    return {"SP": {"label_map": gen.integers(0, n_classes, n_tok).astype(np.int64), "n_classes": n_classes}}


def _factory(data, arm, seed):
    moments = {"mu": np.zeros(5, np.float32), "sd": np.ones(5, np.float32), "lo": -np.ones(5, np.float32) * 9,
               "hi": np.ones(5, np.float32) * 9}

    def make(rows, anchors):
        blocks = [TokAnchorBlock(data.array("top_ids"), rows, anchors, n_bins=8), HiddenZBlock(data.array("hidden"), rows, anchors, moments)]
        if arm != "fplus":
            blocks.append(SlotsAnchorBlock(data.array("slots"), rows, anchors, 4))
        return blocks
    return {(arm, seed): make}


def _quick(real, epochs=2, batch_size=32):
    """train_probe at a tiny budget whatever epochs / batch_size the caller passes (the lr passes through)."""
    def quick(blocks, labels, split, n_classes, cap, seed, device="cpu", lr=3e-3, **kw):
        kw.pop("epochs", None)
        kw.pop("batch_size", None)
        return real(blocks, labels, split, n_classes, cap, seed, device=device, epochs=epochs, batch_size=batch_size, lr=lr, **kw)
    return quick


@needs_torch
def test_r0_runner_matches_run_cell_bit_exactly_on_a_fake_harvest(monkeypatch):
    data, spaces = FakeData(), _spaces()
    quick = _quick(train_probe)
    monkeypatch.setattr(rp, "train_probe", quick)
    monkeypatch.setattr(rl, "train_probe", quick)
    ref = rp.run_cell(data, spaces, "SP", 2, "a", "mlp256", 1, "cpu", n_slots=4)
    got = rl.run_cell_reader(data, spaces, "SP", 2, "a", "mlp256", 1, "R0", {}, 4, "cpu")
    for k in ("cell", "test_acc", "val_acc_best", "best_epoch", "n_train", "n_val", "n_test", "majority_rate_test", "_clusters"):
        assert got[k] == ref[k], k
    assert got["reader"] == "R0" and got["reader_params"]["kind"] == "plain"
    # the (c) proxy cell: (a) blocks plus the slots block, the registered feature_blocks(data, "c") order
    ref_c = rp.run_cell(data, spaces, "SP", 2, "c", "linear", 0, "cpu", n_slots=4)
    got_c = rl.run_cell_reader(data, spaces, "SP", 2, "c", "linear", 0, "R0", {}, 4, "cpu")
    assert got_c["test_acc"] == ref_c["test_acc"] and got_c["_clusters"] == ref_c["_clusters"]
    # an arm through the factory extras (the frozen chain's run_cell call: (a) blocks, then the arm's factory blocks)
    fac = _factory(data, "fplus_b", 1)
    ref_b = rp.run_cell(data, spaces, "SP", 2, "a", "mlp256", 1, "cpu", extra_factory=fac[("fplus_b", 1)], feats_label="fplus_b", n_slots=4)
    got_b = rl.run_cell_reader(data, spaces, "SP", 2, "fplus_b", "mlp256", 1, "R0", fac, 4, "cpu")
    for k in ("cell", "test_acc", "val_acc_best", "best_epoch", "_clusters", "majority_rate_test"):
        assert got_b[k] == ref_b[k], k


@needs_torch
def test_rn_records_the_hz_rescale_and_rt_records_towers_on_the_fake_harvest(monkeypatch):
    data, spaces = FakeData(seed=2), _spaces()
    monkeypatch.setattr(rl, "train_probe", _quick(train_probe, epochs=1))
    real_tt = rl.train_two_tower
    monkeypatch.setattr(rl, "train_two_tower", lambda *a, **kw: real_tt(*a, **{**kw, "epochs": 1, "batch_size": 32}))
    fac = {**_factory(data, "fplus_b", 0), **_factory(data, "fplus", 0)}
    rn = rl.run_cell_reader(data, spaces, "SP", 2, "fplus_b", "mlp256", 0, "RN", fac, 4, "cpu")
    rs = rn["reader_params"]["rescale"]
    assert rs["c_hz"] > 0 and rs["m_hz"] > 0 and rs["m_slots_aligned"] > 0 and "adam_equivalence" in rs
    rn_f = rl.run_cell_reader(data, spaces, "SP", 2, "fplus", "mlp256", 0, "RN", fac, 4, "cpu")
    assert rn_f["reader_params"]["rescale"]["c_hz"] == rs["c_hz"]          # the aligned slots reference, the same for every arm
    rn_a = rl.run_cell_reader(data, spaces, "SP", 2, "a", "mlp256", 0, "RN", fac, 4, "cpu")
    assert rn_a["reader_params"]["rescale"]["c_hz"] is None
    rt = rl.run_cell_reader(data, spaces, "SP", 2, "fplus_b", "mlp256", 0, "RT", fac, 4, "cpu")
    assert rt["reader_params"]["towers"]["b_dim"] == 8 and rt["reader_params"]["towers"]["width_b"] == 64
    with pytest.raises(SystemExit, match="not registered under it"):
        rl.run_cell_reader(data, spaces, "SP", 2, "fplus_b", "linear", 0, "RT", fac, 4, "cpu")


# ---------------------------------------------------------------------------
# grids
# ---------------------------------------------------------------------------

def test_grids_have_the_registered_counts_and_unique_keys():
    lens = rl.grid_lens()
    assert len(lens) == 49 and sum(1 for c in lens if c[5]) == 4
    assert sum(1 for c in lens if c[2] == "c") == 3 and all(c[6] == "R0" for c in lens)
    readers = rl.grid_readers(("RN", "RT"), S3_SPACES)
    assert len(readers) == 75 and {c[6] for c in readers} == {"RN", "RT", "R0"} and all(c[1] == 2 for c in readers)
    r0 = [c for c in readers if c[6] == "R0"]
    assert len(r0) == 3 and all(c[0] == BAL and c[2] == "a" and c[3] == "linear" for c in r0)
    assert all(c[3] == "mlp256" for c in readers if c[6] != "R0")
    g, rs, sps = rl.stage_grid("readers_long", "olmoe", None)
    assert len(g) == 39 and rs == ("RL",) and sps == S3_SPACES
    with pytest.raises(SystemExit, match="--readers is required"):
        rl.stage_grid("s1", "concept", None)
    with pytest.raises(SystemExit, match="unknown reader"):
        rl.stage_grid("s1", "concept", ("RN", "RX"))
    g1, _, sps1 = rl.stage_grid("s1", "concept", ("RN",))
    assert len(g1) == 12 and sps1 == ("L1_concept_k16",)
    with pytest.raises(SystemExit, match="unknown stage"):
        rl.stage_spaces("nope", "olmoe")
    assert rl.grid_keys(lens) == {(c[6], cell_id(*c[:6])) for c in lens}


def test_smoke_cell_grid_parses_and_refuses():
    g, rs, sps = rl.smoke_cell_grid("RN|L1_olmoe_k16|2|fplus_b|mlp256|0")
    assert g == [(L1, 2, "fplus_b", "mlp256", 0, False, "RN")] and rs == ("RN",) and sps == (L1,)
    with pytest.raises(SystemExit, match="unknown reader"):
        rl.smoke_cell_grid("RX|L1_olmoe_k16|2|fplus_b|mlp256|0")
    with pytest.raises(SystemExit, match="wants"):
        rl.smoke_cell_grid("RN|L1_olmoe_k16|2")


def test_grid_collision_check_names_the_shared_l1_a_cells_and_refuses_any_other():
    g = rl.grid_readers(("RN", "RT"), S3_SPACES)
    shared = {cell_id(L1, 2, "a", "mlp256", s) for s in rl.SEEDS}
    assert rl.check_grid_against_committed(g, shared) == sorted(shared)
    assert rl.check_grid_against_committed(g, set()) == []
    with pytest.raises(SystemExit, match="collide"):
        rl.check_grid_against_committed(g, {cell_id(L1, 2, "fplus", "mlp256", 0)})
    with pytest.raises(SystemExit, match="collide"):
        rl.check_grid_against_committed(g, {cell_id(BAL, 2, "a", "mlp256", 0)})


# ---------------------------------------------------------------------------
# readouts on synthetic cells (the B1 / B2 pairings)
# ---------------------------------------------------------------------------

def _cell(space, arm, cap, seed, acc, reader="R0", off=2, best_epoch=5, shuffled=False, n=100, prompts=7):
    correct = int(round(acc * n))
    return {"cell": cell_id(space, off, arm, cap, seed, shuffled), "reader": reader, "space": space, "offset": off,
            "features": arm, "capacity": cap, "seed": seed, "shuffled": shuffled, "test_acc": acc,
            "majority_rate_test": 0.2, "best_epoch": best_epoch, "runtime_s": 1.0,
            "_clusters": {p: [correct, n] for p in range(prompts)}}


def _reader_cells(space, reader, acc_a=0.3, acc_f=0.5, acc_b=0.52, acc_r=0.5):
    out = []
    for s in rl.SEEDS:
        out += [_cell(space, "a", "mlp256", s, acc_a, reader), _cell(space, "fplus", "mlp256", s, acc_f, reader),
                _cell(space, "fplus_b", "mlp256", s, acc_b, reader), _cell(space, "fplus_r", "mlp256", s, acc_r, reader)]
    return out


def test_readouts_pair_the_readers_own_fresh_a_and_never_the_committed_one_at_the_gate_capacity():
    cells = _reader_cells(L1, "RN")
    p3 = []
    for s in rl.SEEDS:
        p3 += [_cell(L1, "a", "mlp256", s, 0.9), _cell(L1, "a", "linear", s, 0.25),
               _cell(L1, "c", "linear", s, 0.4), _cell(L1, "c", "mlp256", s, 0.45)]
    assert {c["cell"] for c in p3 if c["capacity"] == "mlp256" and c["features"] == "a"} <= {c["cell"] for c in cells}
    rd = rl.readouts_for(cells, L1, "RN", p3, [], None)
    mf = rd["mf_fplus_vs_a"][0]
    assert abs(mf["margin"] - 0.2) < 1e-9, "Mf must pair the reader's fresh (a) (0.5 - 0.3), not the committed 0.9"
    assert abs(rd["mfx_fplus_vs_linear_a"][0]["margin"] - 0.25) < 1e-9
    assert abs(next(m for m in rd["mc_fplus_vs_c"] if m["capacity"] == "mlp256")["margin"] - 0.05) < 1e-9
    assert rd["reader_valid"]["complete"] and rd["reader_valid"]["ok"]
    assert abs(rd["d_fplus_b_vs_fplus_r"][0]["margin"] - 0.02) < 1e-9
    assert rd["best_epochs"]["a"] == [5, 5, 5] and "rescale" in rd


def test_readouts_at_the_balanced_lens_use_this_runs_r0_linear_a_for_mfx():
    cells = _reader_cells(BAL, "RT")
    lin = [_cell(BAL, "a", "linear", s, 0.28, "R0") for s in rl.SEEDS]
    rd = rl.readouts_for(cells + lin, BAL, "RT", [], lin, None)
    assert rd["reader_valid"]["complete"] and abs(rd["mfx_fplus_vs_linear_a"][0]["margin"] - 0.22) < 1e-9
    assert rd["mc_fplus_vs_c"] == []                                   # no (c) cell at the balanced lens in a readers stage
    without = rl.readouts_for(cells, BAL, "RT", [], [], None)
    assert not without["reader_valid"]["complete"] and not without["reader_valid"]["ok"]   # B1's failure mode
    proxy = rl.proxy_readout(lin + [_cell(BAL, "c", "linear", s, 0.4, "R0") for s in rl.SEEDS], BAL, None)
    assert abs(proxy["row"]["margin"] - 0.12) < 1e-9 and proxy["acc_minus_floor_per_seed"]["c"] == [0.2, 0.2, 0.2]
    assert rl.proxy_readout(lin, BAL, None) is None


# ---------------------------------------------------------------------------
# label rules
# ---------------------------------------------------------------------------

def _row(space, pair, m, lo, hi, per_seed=(0.01, 0.01, 0.01), cap="mlp256", off=2, n_clusters=30):
    return {"space": space, "offset": off, "capacity": cap, "pair": pair, "margin": m, "ci95": [lo, hi],
            "per_seed_margin": {s: v for s, v in zip(rl.SEEDS, per_seed)}, "n_seeds": 3, "n_clusters": n_clusters}


def _readouts(space, d=(0.01, 0.005, 0.015), mt=(0.004, 0.001, 0.008), mnr=(0.001, -0.002, 0.004), ok=True, d_offs=()):
    rows = [_row(space, "fplus_b-fplus_r", *d)] + [_row(space, "fplus_b-fplus_r", *dd, off=o) for o, dd in d_offs]
    return {"gate": {"row": rows[0], "fires": ok and rl.gate_fires(rows[0])}, "d_fplus_b_vs_fplus_r": rows,
            "mt_fplus_b_vs_fplus": [_row(space, "fplus_b-fplus", *mt)], "mn_r_fplus_r_vs_fplus": [_row(space, "fplus_r-fplus", *mnr)],
            "reader_valid": {"ok": ok}, "best_epochs": {"fplus": [1, 1, 1]}}


NULL_D = dict(d=(0.0005, -0.002, 0.003))


def test_pair_label_through_the_frozen_rules_with_the_stage_words():
    fire = _readouts(L1)
    v = rl.pair_label(fire, fire, (2,), stronger_word=True)
    assert v["label"] == rl.LABEL_STRONGER and v["licence"] == "full" and v["mt_fires_triple"] == {"primary": False, "replication": False}
    assert rl.pair_label(fire, fire, (2,), stronger_word=False)["label"] == rl.LABEL_SURVIVES
    mt_fire = _readouts(L1, mt=(0.006, 0.002, 0.01))
    assert rl.pair_label(mt_fire, mt_fire, (2,), True)["mt_fires_triple"] == {"primary": True, "replication": True}
    neg_twin = _readouts(L1, mnr=(-0.004, -0.007, -0.001))
    v2 = rl.pair_label(fire, neg_twin, (2,), True)
    assert v2["label"] == rl.LABEL_STRONGER and v2["licence"] == "equal-dims-only" and "twin" in v2["licence_reason"]
    null = _readouts(L1, **NULL_D)
    assert rl.pair_label(null, null, (2,), True)["label"] == rl.LABEL_ABSORBED
    straddle = _readouts(L1, d=(0.002, -0.002, 0.006))
    assert rl.pair_label(null, straddle, (2,), True)["label"] == rl.LABEL_NOT_SHOWN
    assert rl.pair_label(fire, null, (2,), True)["label"] == rl.LABEL_SPLIT
    invalid = rl.pair_label(fire, _readouts(L1, ok=False), (2,), True)
    assert invalid["label"] == rl.LABEL_READER_INVALID and invalid["licence"] is None
    horizons = rl.pair_label(_readouts(BAL, d_offs=[(3, (0.001, -0.001, 0.003))]),
                             _readouts(BAL, d_offs=[(3, (0.0, -0.002, 0.002))]), (2, 3, 4), False)["horizons"]
    assert horizons["off3"] == "OFF3-ABSORBED" and horizons["off4"] is None


def _p(fires, upper, lo=-0.01):
    return {"fires": fires, "row": {"ci95": [lo, upper], "margin": 0.0}}


def test_lens_label_growth_and_licence_rules():
    assert rl.lens_label(_p(True, 0.1), _p(True, 0.1)) == rl.LENS_SURVIVES
    assert rl.lens_label(_p(True, 0.1), _p(False, 0.1)) == rl.LENS_SPLIT
    assert rl.lens_label(_p(False, 0.001), _p(False, 0.004)) == rl.LENS_COLLAPSE
    assert rl.lens_label(_p(False, 0.001), _p(False, 0.006)) == rl.LENS_NOT_SHOWN
    assert rl.lens_label(None, _p(True, 0.1)) == rl.LABEL_INCOMPLETE
    assert rl.growth_reading(_p(True, 0.015, lo=0.005), 0.0206) == rl.GROWTH_LOST
    assert rl.growth_reading(_p(True, 0.06, lo=0.03), 0.0206) == rl.GROWTH_SURVIVES
    assert rl.growth_reading(_p(True, 0.03, lo=0.01), 0.0206) == rl.GROWTH_UNSETTLED
    assert rl.growth_reading(None, 0.02) is None and rl.growth_reading(_p(True, 0.03), None) is None
    G = rl
    assert G.growth_combined(G.GROWTH_LOST, G.GROWTH_LOST) == G.GROWTH_LOST
    assert G.growth_combined(G.GROWTH_SURVIVES, G.GROWTH_SURVIVES) == G.GROWTH_SURVIVES
    assert G.growth_combined(G.GROWTH_LOST, G.GROWTH_UNSETTLED) == G.GROWTH_SPLIT
    assert G.growth_combined(G.GROWTH_UNSETTLED, G.GROWTH_SURVIVES) == G.GROWTH_SPLIT
    assert G.growth_combined(G.GROWTH_LOST, G.GROWTH_SURVIVES) == G.GROWTH_SPLIT
    assert G.growth_combined(G.GROWTH_UNSETTLED, G.GROWTH_UNSETTLED) == G.GROWTH_UNSETTLED
    assert G.growth_combined(None, G.GROWTH_LOST) is None
    pos, neg = {"ci95": [0.0, 0.01]}, {"ci95": [-0.01, -0.001]}
    assert rl.licence_of(rl.LABEL_STRONGER, pos, pos, pos, pos) == ("full", None)
    lic, reason = rl.licence_of(rl.LABEL_SURVIVES, pos, pos, neg, pos)
    assert lic == "equal-dims-only" and "twin" in reason
    assert rl.licence_of(rl.LABEL_STRONGER, neg, pos, pos, pos)[1].startswith("Mt")
    assert rl.licence_of(rl.LABEL_ABSORBED, pos, pos, pos, pos) == (None, None)


def _lab(label, lic=None, mt=(False, False)):
    return {"label": label, "licence": lic, "mt_fires_triple": {"primary": mt[0], "replication": mt[1]}}


GRADE = dict(lic="full", mt=(True, True))


def test_k2_sentence_rules():
    allnull = {("RN", L1): _lab("ABSORBED"), ("RN", LOP): _lab("NOT-SHOWN"), ("RN", BAL): _lab("ABSORBED"),
               ("RT", L1): _lab("ABSORBED"), ("RT", LOP): _lab("ABSORBED"), ("RT", BAL): _lab("NOT-SHOWN")}
    k = rl.k2_sentence(allnull, None)
    assert k["word"] == rl.K2_STANDS == "K-2-NOT-OVERTURNED-AT-S3" and not k["over_valid_cells_only"] and not k["reopen_provisional"]
    assert k["narrowed_cells"] == sorted(["RN|" + L1, "RN|" + BAL, "RT|" + L1, "RT|" + LOP])
    assert k["not_narrowed_cells"] == sorted(["RN|" + LOP, "RT|" + BAL])
    assert rl.k2_sentence({**allnull, ("RT", LOP): _lab("SPLIT")}, None)["word"] == rl.K2_UNSETTLED
    iso = {**allnull, ("RN", L1): _lab(rl.LABEL_STRONGER, **GRADE)}
    k = rl.k2_sentence(iso, None)
    assert k["word"] == rl.K2_ISOLATED and k["s1_trigger_readers"] == ["RN"] and k["s1_pending"]
    k = rl.k2_sentence(iso, {"RN": _lab(rl.LABEL_STRONGER, **GRADE)})
    assert k["word"] == rl.K2_REOPENED and k["reopened"] == ["RN|" + L1] and k["reopen_provisional"] and k["reopen_rider_rule"]
    assert rl.k2_sentence(iso, {"RN": _lab(rl.LABEL_STRONGER, "equal-dims-only", (True, True))})["word"] == rl.K2_ISOLATED
    assert rl.k2_sentence(iso, {"RN": _lab(rl.LABEL_STRONGER, "full", (True, False))})["word"] == rl.K2_ISOLATED
    # a FULL licence without Mt firing the triple rule is not reopen-grade (the critic's A15)
    weak = {**allnull, ("RN", L1): _lab(rl.LABEL_STRONGER, "full", (False, False))}
    k = rl.k2_sentence(weak, {"RN": _lab(rl.LABEL_STRONGER, **GRADE)})
    assert k["word"] == rl.K2_ISOLATED and k["s1_trigger_readers"] == []
    # the lopsided lens never decides a reopen, whatever the balanced cell reads
    lop = {**allnull, ("RT", LOP): _lab(rl.LABEL_STRONGER, **GRADE), ("RT", BAL): _lab("READER-INVALID")}
    k = rl.k2_sentence(lop, {"RT": _lab(rl.LABEL_STRONGER, **GRADE)})
    assert k["word"] == rl.K2_ISOLATED and k["void_cells"] == ["RT|" + BAL] and k["over_valid_cells_only"]
    # the balanced lens can
    bal = {**allnull, ("RT", BAL): _lab(rl.LABEL_STRONGER, **GRADE)}
    assert rl.k2_sentence(bal, {"RT": _lab(rl.LABEL_STRONGER, **GRADE)})["word"] == rl.K2_REOPENED
    # a READER-INVALID cell is void and the word is read over the valid cells; no valid cell at all is INCOMPLETE
    k = rl.k2_sentence({**allnull, ("RN", BAL): _lab("READER-INVALID")}, None)
    assert k["word"] == rl.K2_STANDS and k["void_cells"] == ["RN|" + BAL] and k["over_valid_cells_only"]
    assert rl.k2_sentence({kk: _lab("READER-INVALID") for kk in allnull}, None)["word"] == rl.K2_INCOMPLETE


# ---------------------------------------------------------------------------
# state files, payload verification, conclude-from
# ---------------------------------------------------------------------------

NPZ = {"moe_s0.npz": "a" * 64}
NPZ_R = {"moe_s8.npz": "b" * 64}
RIDER = {"space": BAL, "pass": True, "leg1_pass": True, "leg2_pass": True, "band": 0.01}


def _header(npz=NPZ, head="h1", out="lens_s3.json", **extra):
    return {"kind": "state_header", "harvest_npz_sha256": npz, "git_head": head, "out": out, **extra}


def _write_state(path, header, rows, torn=None):
    text = json.dumps(header) + "\n" + "".join(json.dumps(r) + "\n" for r in rows)
    if torn is not None:
        text += torn
    path.write_text(text, encoding="utf-8", newline="\n")


def _rows_of(grid):
    rows = []
    for c in grid:
        r = {"cell": cell_id(*c[:6]), "reader": c[6], "space": c[0], "offset": c[1], "features": c[2], "capacity": c[3],
             "seed": c[4], "shuffled": c[5], "test_acc": 0.5, "best_epoch": 1, "runtime_s": 1.0,
             "_clusters": {p: [5, 10] for p in range(3)}}
        if c[5]:
            r["n_classes"] = 17
        rows.append(r)
    return rows


def _fake_rider(monkeypatch, value=RIDER, root=None):
    monkeypatch.setattr(rl.am, "rider_check_amended", lambda cells, sp, n_classes, n_boot, expected_clusters: value)
    if root is not None:
        monkeypatch.setattr(rl, "PAYLOAD_ROOT", root)                 # the test-only override of "payloads live under results/real"


def test_load_state_binds_the_harvest_and_follows_parse_state_semantics(tmp_path):
    st = tmp_path / "x.state.jsonl"
    rows = _rows_of(rl.grid_lens()[:3])
    _write_state(st, _header(), rows, torn='{"cell": "torn')
    header, got = rl.load_state(st, NPZ)
    assert header["git_head"] == "h1" and len(got) == 3 and ("R0", rows[0]["cell"]) in got
    assert list(got[("R0", rows[0]["cell"])]["_clusters"]) == [0, 1, 2]           # int keys restored
    with pytest.raises(SystemExit, match="different harvest"):
        rl.load_state(st, NPZ_R)
    # a torn final line is cut before the next row is appended, and the file then loads whole
    dropped = rl.truncate_torn(st)
    assert dropped == len('{"cell": "torn') and st.read_bytes().endswith(b"\n") and rl.truncate_torn(st) == 0
    with open(st, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"cell": "late", "reader": "R0"}) + "\n")
    assert ("R0", "late") in rl.load_state(st, NPZ)[1]
    _write_state(st, _header(), rows[:1] + [{"cell": "x", "reader": "R0"}])
    st.write_text(st.read_text(encoding="utf-8").replace('{"cell": "x", "reader": "R0"}\n', "not json\n" + json.dumps(rows[1]) + "\n"),
                  encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="corrupt row"):
        rl.load_state(st, NPZ)
    st.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="empty"):
        rl.load_state(st, NPZ)
    _write_state(st, {"nothing": 1}, rows)
    with pytest.raises(SystemExit, match="not a state header"):
        rl.load_state(st, NPZ)
    st.write_text("[1, 2]\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit, match="not a state header"):
        rl.load_state(st, NPZ)
    _write_state(st, _header(), [{"cell": "noreader"}])
    assert ("R0", "noreader") in rl.load_state(st, None)[1]


def _payload(tmp_path, name, stage, npz, per_rs, proxy=None, head="h1", rows=None, tag="olmoe", riders=None,
             admission=None, readers_list=(), n_boot=2000, **over):
    grid, readers, spaces = rl.stage_grid(stage, tag, tuple(readers_list) or None)
    rows = _rows_of(grid) if rows is None else rows
    st = tmp_path / (name + ".state.jsonl")
    _write_state(st, _header(npz, head, name), rows)
    harvest = "results/real/" + rl.HARVEST_OF_OUT[name]
    if riders is None:
        riders = {BAL: dict(RIDER)} if stage == "lens" else {}
    p = {"stage": stage, "role": rl.ROLE_OF_OUT[name], "harvest": harvest, "tag": tag,
         "readers": {r: rl.READERS[r] for r in readers}, "spaces": list(spaces), "partial": False, "smoke_cell": None,
         "per_reader_space": per_rs, "proxy": proxy, "riders": riders, "balanced_admission": admission,
         "provenance": {"git_commit": head, "git_status_tracked": [], "instrument_sha256": rl._sha(Path(rl.__file__)),
                        "state_file": st.name, "state_sha256": rl._sha(st), "harvest_npz_sha256": npz,
                        "args": {"phase3_state": "x.state.jsonl", "phase3_payload": "x.json", "n_boot": n_boot}}}
    for k, v in over.items():
        d, key = p, k
        if "." in k:
            parts = k.split(".")
            for part in parts[:-1]:
                d = d[part]
            key = parts[-1]
        d[key] = v
    path = tmp_path / name
    path.write_text(json.dumps(p), encoding="utf-8")
    return path


def _admission(lens_p, lens_r):
    return {"ok": True, "payloads": {lens_p.name: {"sha256": rl._sha(lens_p), "rider_pass": True, "ok": True},
                                    lens_r.name: {"sha256": rl._sha(lens_r), "rider_pass": True, "ok": True}}}


def test_verify_payload_refusals_and_acceptance(tmp_path, monkeypatch):
    _fake_rider(monkeypatch)
    per_rs = {"R0|" + BAL: _readouts(BAL)}
    ok_path = _payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs)
    with pytest.raises(SystemExit, match="lies outside"):                # a registered name elsewhere than results/real
        rl.verify_payload(ok_path, "primary")
    monkeypatch.setattr(rl, "PAYLOAD_ROOT", tmp_path)
    p, cells = rl.verify_payload(ok_path, "primary")
    assert len(cells) == 49 and p["stage"] == "lens"
    assert rl.verify_payload(ok_path, "primary", expect_stage="lens")[0]["stage"] == "lens"
    for over, role, msg in [
        ({}, "replication", "read as replication"),
        ({"role": "replication"}, "primary", "read as primary"),
        ({"harvest": "results/real/harvest_moe_r"}, "primary", "binds harvest"),
        ({"partial": True}, "primary", "partial"),
        ({"provenance.git_status_tracked": [" M x"]}, "primary", "dirty"),
        ({"provenance.instrument_sha256": "0" * 64}, "primary", "instrument's bytes"),
        ({"readers": {"RN": rl.READERS["RN"]}}, "primary", "registry"),
        ({"spaces": [L1]}, "primary", "registry"),
        ({"n_boot": 50}, "primary", "not the registered 2000"),
        ({"riders": {}}, "primary", "balanced rider alone"),
        ({"riders": {BAL: dict(RIDER), L1: dict(RIDER)}}, "primary", "balanced rider alone"),
        ({"provenance.state_sha256": "0" * 64}, "primary", "state file sha"),
        ({"provenance.git_commit": "h2"}, "primary", "HEAD or out name"),
    ]:
        bad = _payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs, **over)
        with pytest.raises(SystemExit, match=msg):
            rl.verify_payload(bad, role)
    with pytest.raises(SystemExit, match="where a readers_long payload is required"):
        rl.verify_payload(_payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs), "primary", expect_stage="readers_long")
    (tmp_path / "scratch.json").write_text(ok_path.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(SystemExit, match="not a registered out"):
        rl.verify_payload(tmp_path / "scratch.json", "primary")
    short = _payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs, rows=_rows_of(rl.grid_lens()[:-1]))
    with pytest.raises(SystemExit, match="not the stage's grid"):
        rl.verify_payload(short, "primary")
    wrong_stage = _payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs)
    d = json.loads(wrong_stage.read_text(encoding="utf-8"))
    d["stage"] = "readers"
    wrong_stage.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(SystemExit, match="not a registered out of stage"):
        rl.verify_payload(wrong_stage, "primary")
    # the rider must recompute from the shuffled rows and must have passed
    failed = _payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs, riders={BAL: {**RIDER, "pass": False}})
    _fake_rider(monkeypatch, {**RIDER, "pass": False})
    with pytest.raises(SystemExit, match="did not pass"):
        rl.verify_payload(failed, "primary")
    _fake_rider(monkeypatch, {**RIDER, "band": 0.02})
    with pytest.raises(SystemExit, match="does not recompute"):
        rl.verify_payload(_payload(tmp_path, "lens_s3.json", "lens", NPZ, per_rs), "primary")
    # a readers payload carries no rider
    rd = _payload(tmp_path, "readers_s3.json", "readers", NPZ, {}, riders={BAL: dict(RIDER)})
    with pytest.raises(SystemExit, match="carries no rider cells"):
        rl.verify_payload(rd, "primary")


def _stub_recompute(monkeypatch):
    monkeypatch.setattr(rl, "recompute_readouts", lambda p, cells, data_root=rl.REAL: p["per_reader_space"])
    monkeypatch.setattr(rl, "committed_l2_margin", lambda p, data_root=rl.REAL: 0.0206)


def _lens_pair(tmp_path, proxy_margin=0.03):
    proxy = {"row": _row(BAL, "c-a", proxy_margin, proxy_margin - 0.005, proxy_margin + 0.01, cap="linear"), "fires": True,
             "acc_minus_floor_per_seed": {"a": [0.1] * 3, "c": [0.13] * 3}}
    lens_p = _payload(tmp_path, "lens_s3.json", "lens", NPZ, {"R0|" + BAL: _readouts(BAL)}, proxy)
    lens_r = _payload(tmp_path, "lens_s3_r.json", "lens", NPZ_R, {"R0|" + BAL: _readouts(BAL, **NULL_D)}, proxy)
    return lens_p, lens_r


def test_conclude_from_lens_pair_labels_growth_and_refusals(tmp_path, monkeypatch):
    _fake_rider(monkeypatch, root=tmp_path)
    _stub_recompute(monkeypatch)
    lens_p, lens_r = _lens_pair(tmp_path)
    out = rl.conclude_from(lens_p, lens_r, data_root=tmp_path)
    assert out["stage"] == "lens" and out["labels"]["R0|" + BAL]["label"] == rl.LABEL_SPLIT
    g = out["lens"]["growth_over_l2"]
    assert out["lens"]["proxy_label"] == rl.LENS_SURVIVES and g["primary"] == rl.GROWTH_SURVIVES and g["combined"] == rl.GROWTH_SURVIVES
    assert abs(out["lens"]["ratio_to_f17"]["primary"] - 0.03 / rl.F17_L3_MARGIN["primary"]) < 1e-12
    assert "k2" not in out
    same = _payload(tmp_path, "lens_s3_r.json", "lens", NPZ, {"R0|" + BAL: _readouts(BAL)}, out["lens"]["proxy"]["primary"])
    with pytest.raises(SystemExit, match="SAME harvest"):
        rl.conclude_from(lens_p, same, data_root=tmp_path)


def test_conclude_from_refuses_when_the_readouts_do_not_reproduce(tmp_path, monkeypatch):
    _fake_rider(monkeypatch, root=tmp_path)
    monkeypatch.setattr(rl, "load_phase3_cells", lambda *a, **k: [])
    monkeypatch.setattr(rl, "readouts_for", lambda *a, **k: {"tampered": True})
    lens_p, lens_r = _lens_pair(tmp_path)
    with pytest.raises(SystemExit, match="does not reproduce"):
        rl.conclude_from(lens_p, lens_r, data_root=tmp_path)


def test_conclude_from_readers_pair_binds_every_extra_payload_to_its_stage(tmp_path, monkeypatch):
    _fake_rider(monkeypatch, root=tmp_path)
    _stub_recompute(monkeypatch)
    lens_p, lens_r = _lens_pair(tmp_path)
    adm = _admission(lens_p, lens_r)
    rs = {f"{r}|{sp}": _readouts(sp, **NULL_D) for r in ("RN", "RT") for sp in S3_SPACES}
    rs["RT|" + L1] = _readouts(L1, d=(0.002, -0.002, 0.006))
    rd_p = _payload(tmp_path, "readers_s3.json", "readers", NPZ, rs, admission=adm)
    rd_r = _payload(tmp_path, "readers_s3_r.json", "readers", NPZ_R, rs, admission=adm)
    with pytest.raises(SystemExit, match="requires --lens"):
        rl.conclude_from(rd_p, rd_r, data_root=tmp_path)
    with pytest.raises(SystemExit, match="differ in stage"):
        rl.conclude_from(rd_p, lens_r, lens_pair=(lens_p, lens_r), data_root=tmp_path)
    out = rl.conclude_from(rd_p, rd_r, lens_pair=(lens_p, lens_r), data_root=tmp_path)
    assert out["k2"]["word"] == rl.K2_STANDS and out["readers_long_runs"] is True
    assert out["labels"]["RT|" + L1]["label"] == rl.LABEL_NOT_SHOWN and out["labels"]["RN|" + L1]["label"] == rl.LABEL_ABSORBED
    ident = out["r0_linear_a_rerun"]["primary"]
    assert ident["all_identical"] and len(ident["cells"]) == 3
    # the s3-for-s1 typo: a readers payload where an S1 payload is required is refused, never a REOPEN
    with pytest.raises(SystemExit, match="where a s1 payload is required"):
        rl.conclude_from(rd_p, rd_r, lens_pair=(lens_p, lens_r), s1_pair=(rd_p, rd_r), data_root=tmp_path)
    with pytest.raises(SystemExit, match="where a readers_long payload is required"):
        rl.conclude_from(rd_p, rd_r, lens_pair=(lens_p, lens_r), long_pair=(lens_p, lens_r), data_root=tmp_path)
    with pytest.raises(SystemExit, match="where a lens payload is required"):
        rl.conclude_from(rd_p, rd_r, lens_pair=(rd_p, rd_r), data_root=tmp_path)
    # the lens payloads must be the ones the readers run admitted the balanced space on
    other_adm = _admission(lens_r, lens_p)
    rd_p2 = _payload(tmp_path, "readers_s3.json", "readers", NPZ, rs, admission={"ok": True, "payloads": {
        lens_p.name: {"sha256": "0" * 64}, lens_r.name: other_adm["payloads"][lens_r.name]}})
    with pytest.raises(SystemExit, match="admitted the balanced space on a different"):
        rl.conclude_from(rd_p2, rd_r, lens_pair=(lens_p, lens_r), data_root=tmp_path)
    # the rerun identity reports a changed R0 linear (a) row; runtime_s never counts
    rows = _rows_of(rl.stage_grid("readers", "olmoe", None)[0])
    for r in rows:
        if r["reader"] == "R0":
            r["test_acc"], r["runtime_s"] = 0.51, 9.0
    rd_p3 = _payload(tmp_path, "readers_s3.json", "readers", NPZ, rs, rows=rows, admission=adm)
    out2 = rl.conclude_from(rd_p3, rd_r, lens_pair=(lens_p, lens_r), data_root=tmp_path)
    cells = out2["r0_linear_a_rerun"]["primary"]["cells"]
    assert not out2["r0_linear_a_rerun"]["primary"]["all_identical"]
    assert all(v["differing_fields"] == ["test_acc"] for v in cells.values())
    # readers_long_runs reads the READERS labels only; the long labels join the K-2 word
    rs_long = {f"RL|{sp}": _readouts(sp, **NULL_D) for sp in S3_SPACES}
    rs_long["RL|" + L1] = _readouts(L1, d=(0.002, -0.002, 0.006))
    lg_p = _payload(tmp_path, "readers_long_s3.json", "readers_long", NPZ, rs_long, admission=adm)
    lg_r = _payload(tmp_path, "readers_long_s3_r.json", "readers_long", NPZ_R, {**rs_long, "RL|" + L1: _readouts(L1)}, admission=adm)
    out3 = rl.conclude_from(rd_p, rd_r, lens_pair=(lens_p, lens_r), long_pair=(lg_p, lg_r), data_root=tmp_path)
    assert out3["readers_long_runs"] is True and out3["k2"]["word"] == rl.K2_UNSETTLED and "RL|" + L1 in out3["k2"]["split"]
    # the long payloads' admission is cross-checked against the --lens pair too
    lg_bad = _payload(tmp_path, "readers_long_s3.json", "readers_long", NPZ, rs_long, admission=None)
    with pytest.raises(SystemExit, match="readers_long payload admitted the balanced space on a different"):
        rl.conclude_from(rd_p, rd_r, lens_pair=(lens_p, lens_r), long_pair=(lg_bad, lg_r), data_root=tmp_path)
    lg_p = _payload(tmp_path, "readers_long_s3.json", "readers_long", NPZ, rs_long, admission=adm)
    # a readers_long pair alone yields labels, no K-2 word
    alone = rl.conclude_from(lg_p, lg_r, data_root=tmp_path)
    assert "k2" not in alone and "readers_long" in alone["note"] and alone["labels"]["RL|" + L1]["label"] == rl.LABEL_SPLIT
    # a reopen-grade cell at L1 triggers S1 and reads ISOLATED until S1 lands; S1 payloads are stage-bound and reopen the word
    rs2 = {**rs, "RN|" + L1: _readouts(L1, mt=(0.006, 0.002, 0.01))}
    rd_p4 = _payload(tmp_path, "readers_s3.json", "readers", NPZ, rs2, admission=adm)
    rd_r4 = _payload(tmp_path, "readers_s3_r.json", "readers", NPZ_R, rs2, admission=adm)
    out4 = rl.conclude_from(rd_p4, rd_r4, lens_pair=(lens_p, lens_r), data_root=tmp_path)
    assert out4["k2"]["word"] == rl.K2_ISOLATED and out4["k2"]["s1_trigger_readers"] == ["RN"] and out4["readers_long_runs"] is False
    s1_rs = {"RN|L1_concept_k16": _readouts("L1_concept_k16", mt=(0.006, 0.002, 0.01))}
    s1_p = _payload(tmp_path, "readers_s1.json", "s1", {"shadow_s0.npz": "c" * 64}, s1_rs, tag="concept", readers_list=("RN",))
    s1_r = _payload(tmp_path, "readers_s1_r.json", "s1", {"shadow_s8.npz": "d" * 64}, s1_rs, tag="concept", readers_list=("RN",))
    out5 = rl.conclude_from(rd_p4, rd_r4, lens_pair=(lens_p, lens_r), s1_pair=(s1_p, s1_r), data_root=tmp_path)
    assert out5["k2"]["word"] == rl.K2_REOPENED and out5["k2"]["reopen_provisional"] and out5["k2"]["reopened"] == ["RN|" + L1]


def test_lens_riders_passed_admits_the_balanced_lens_only_on_two_verified_lens_payloads(tmp_path, monkeypatch):
    _fake_rider(monkeypatch, root=tmp_path)
    assert not rl.lens_riders_passed(None)["ok"] and not rl.lens_riders_passed(["a"])["ok"]
    lens_p, lens_r = _lens_pair(tmp_path)
    assert "in that order" in rl.lens_riders_passed([str(lens_r), str(lens_p)])["reason"]
    assert "in that order" in rl.lens_riders_passed([str(lens_p), str(lens_p)])["reason"]
    assert "missing" in rl.lens_riders_passed([str(lens_p), str(tmp_path / "lens_s3_r.json.gone")])["reason"] or \
        "in that order" in rl.lens_riders_passed([str(lens_p), str(tmp_path / "lens_s3_r.json.gone")])["reason"]
    res = rl.lens_riders_passed([str(lens_p), str(lens_r)])
    assert res["ok"] and res["payloads"]["lens_s3.json"]["sha256"] == rl._sha(lens_p)
    scratch = tmp_path / "sub"
    scratch.mkdir()
    bad = _payload(scratch, "lens_s3_r.json", "lens", NPZ_R, {"R0|" + BAL: _readouts(BAL)})
    res2 = rl.lens_riders_passed([str(lens_p), str(bad)])
    assert not res2["ok"] and "lies outside" in res2["reason"]          # a registered name in a scratch directory is not a payload
    partial = _payload(tmp_path, "lens_s3_r.json", "lens", NPZ_R, {"R0|" + BAL: _readouts(BAL)}, partial=True)
    res3 = rl.lens_riders_passed([str(lens_p), str(partial)])
    assert not res3["ok"] and "partial" in res3["reason"]


def test_rerun_identity_reports_missing_rows():
    rows = _rows_of(rl.grid_readers(("RN",), (BAL,)))
    lens_rows = _rows_of(rl.grid_lens())
    assert rl.rerun_identity(rows, lens_rows)["all_identical"]
    partial = rl.rerun_identity(rows[:-1], lens_rows)
    assert not partial["all_identical"] and any(v.get("missing_in") == "stage" for v in partial["cells"].values())


# ---------------------------------------------------------------------------
# frozen chain, registry and run refusals
# ---------------------------------------------------------------------------

def test_frozen_chain_assertion_and_registry_are_consistent():
    chain = rl.assert_frozen_chain()
    assert chain["amended_sha256"] == rl.AMENDED_INSTRUMENT_SHA256
    assert set(rl.HARVEST_OF_OUT) == {n for names in rl.REGISTERED_OUTS.values() for n in names} == set(rl.ROLE_OF_OUT)
    assert set(rl.HARVEST_OF_OUT.values()) <= set(rl.HARVEST_FILES)
    assert all(rl.ROLE_OF_OUT[n] == ("replication" if n.endswith("_r.json") else "primary") for n in rl.ROLE_OF_OUT)
    src = (ROOT / "tools" / "run_reader_lens.py").read_text(encoding="utf-8")
    cuda = src.index('os.environ["CUDA_VISIBLE_DEVICES"] = ""')
    first_import = min(src.index(s) for s in ("import torch", "from sideband", "import run_fullfree", "from run_"))
    assert cuda < first_import                                     # the GPU is hidden before any module that could touch it
    assert rl.REOPEN_SPACES == (L1, BAL) and rl.THREADS == 6 and rl.N_BOOT == 2000


def _ns(**kw):
    return type("A", (), kw)()


BASE = dict(threads=6, stage="lens", harvest="results/real/harvest_moe", only=None, smoke_cell=None, device="cpu",
            resume=False, readers=None, lens_payloads=None, n_boot=2000)
REG = str(ROOT / "results" / "real" / "lens_s3.json")


@needs_torch
def test_run_refuses_unregistered_results_paths_smokes_non_cpu_threads_and_untracked_tools(monkeypatch):
    with pytest.raises(SystemExit, match="unregistered out name"):
        rl.run(_ns(**BASE, out=str(ROOT / "results" / "real" / "not_registered.json")))
    with pytest.raises(SystemExit, match="smoke runs may not write"):
        rl.run(_ns(**{**BASE, "only": "x"}, out=REG))
    with pytest.raises(SystemExit, match="not a registered out of stage"):
        rl.run(_ns(**{**BASE, "stage": "readers"}, out=REG))
    with pytest.raises(SystemExit, match="belongs to"):
        rl.run(_ns(**{**BASE, "harvest": "results/real/harvest_moe_r"}, out=REG))
    with pytest.raises(SystemExit, match="CPU only"):
        rl.run(_ns(**{**BASE, "device": "cuda"}, out=REG))
    with pytest.raises(SystemExit, match="--threads 6"):
        rl.run(_ns(**{**BASE, "threads": 8}, out=REG))
    with pytest.raises(SystemExit, match="--n-boot 2000"):
        rl.run(_ns(**{**BASE, "n_boot": 50}, out=REG))
    monkeypatch.setattr(rl, "_git", lambda strict=False: ("deadbeef", [" M docs/BLUEPRINT.md"]))
    with pytest.raises(SystemExit, match="not clean"):
        rl.run(_ns(**BASE, out=REG))
    monkeypatch.setattr(rl, "_git", lambda strict=False: ("deadbeef", []))
    monkeypatch.setattr(rl, "_tool_tracked", lambda: False)
    with pytest.raises(SystemExit, match="not git-tracked"):
        rl.run(_ns(**BASE, out=REG))
    monkeypatch.setattr(rl, "_tool_tracked", lambda: True)
    with pytest.raises(SystemExit, match="disagrees with the registered companion"):
        rl.run(_ns(**BASE, out=REG, fidelity="results/real/harvest_fidelity_rider.json"))
    with pytest.raises(SystemExit, match="disagrees with the registered value"):
        rl.run(_ns(**BASE, out=REG, n_slots=512))
    # a readers stage on a registered out needs both lens payloads with a passing rider (checked before any state file)
    with pytest.raises(SystemExit, match="not admitted"):
        rl.run(_ns(**{**BASE, "stage": "readers"}, out=str(ROOT / "results" / "real" / "readers_s3.json")))


def test_fill_harvest_files_fills_the_registered_companions_and_refuses_unknown_harvests():
    a = _ns(harvest="results/real/harvest_moe_r", fidelity=None, phase3_state=None, phase3_payload=None, space_tag=None,
            n_slots=None, buckets16=None, glue16=None, buckets512=None, glue512=None, groups=None)
    filled = rl.fill_harvest_files(a, registered=True)
    assert a.space_tag == "olmoe" and a.n_slots == 64 and Path(a.phase3_state).name == "probes_s3_replication.json.state.jsonl"
    assert set(filled) == set(rl.HARVEST_FILES["harvest_moe_r"])
    b = _ns(harvest="results/real/harvest_shadow", fidelity=None, phase3_state=None, phase3_payload=None, space_tag=None,
            n_slots=None, buckets16=None, glue16=None, buckets512=None, glue512=None, groups=None)
    rl.fill_harvest_files(b, registered=False)
    assert b.space_tag == "concept" and b.n_slots == 512 and Path(b.groups).name == "concept_groups_v1.json"
    with pytest.raises(SystemExit, match="not a registered harvest"):
        rl.fill_harvest_files(_ns(harvest="results/real/harvest_x"), registered=True)
    assert rl.fill_harvest_files(_ns(harvest="results/real/harvest_x"), registered=False) == {}


def test_git_helper_fails_closed_when_strict(monkeypatch):
    import subprocess

    def boom(*a, **kw):
        raise OSError("no git")
    monkeypatch.setattr(subprocess, "run", boom)
    assert rl._git() == ("unknown", [])
    with pytest.raises(SystemExit, match="git check failed"):
        rl._git(strict=True)

"""Phase-3 probe machinery: pure data-layer tests (CI-safe) and a trainer
sanity check (torch; skips in CI)."""

import sys
from pathlib import Path

import numpy as np
import pytest

from sideband.harvest import pairs_per_row
from sideband.probes import (DenseBlock, SlotsBlock, anchor_table, labels_for,
                             merged_label_map, slots_multi_hot)

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))


def _has(mod: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(mod) is not None


class TestLabelLayer:
    def test_merged_label_map_matches_registered_rule(self):
        # buckets [0,0,1,1,2,2], glue {2}: concepts {0->0, 1->1}, glue -> C=2
        buckets = np.array([0, 0, 1, 1, 2, 2])
        label_of_token, n_classes = merged_label_map(buckets, [2])
        assert n_classes == 3
        np.testing.assert_array_equal(label_of_token, [0, 0, 1, 1, 2, 2])

    def test_merged_label_map_unbucketed_joins_glue_class(self):
        buckets = np.array([0, 1, -1, 2])  # token 2 absent from buckets file
        label_of_token, n_classes = merged_label_map(buckets, [2])
        # concepts {0,1} -> {0,1}; glue bucket 2 -> class 2; unbucketed -> class 2
        assert n_classes == 3
        np.testing.assert_array_equal(label_of_token, [0, 1, 2, 2])

    def test_anchor_table_matches_pair_counts(self):
        lengths = np.array([5, 1, 3])
        for j in (1, 2, 3, 4):
            rows, anchors = anchor_table(lengths, j, tmax=5)
            expect = sum(max(0, int(n) - (j - 1)) for n in lengths)
            assert len(rows) == len(anchors) == expect
        # total over offsets == pairs_per_row sum
        total = sum(len(anchor_table(lengths, j, 5)[0]) for j in (1, 2, 3, 4))
        assert total == sum(pairs_per_row(int(n)) for n in lengths)

    def test_labels_offset1_are_anchor_tokens(self):
        tokens = np.array([[3, 1, 4, 1, 5], [2, 7, 1, 0, 0]])
        lengths = np.array([5, 3])
        lmap = np.arange(10)  # identity label map
        rows, anchors = anchor_table(lengths, 1, 5)
        lab = labels_for(tokens, rows, anchors, 1, lmap)
        np.testing.assert_array_equal(lab, [3, 1, 4, 1, 5, 2, 7, 1])
        rows2, anchors2 = anchor_table(lengths, 3, 5)
        lab2 = labels_for(tokens, rows2, anchors2, 3, lmap)
        np.testing.assert_array_equal(lab2, [4, 1, 5, 1])  # tokens[a+2]

    def test_shuffle_preserves_marginals_breaks_alignment(self):
        rng = np.random.default_rng(0)
        tokens = rng.integers(0, 6, (4, 40))
        lengths = np.full(4, 40)
        lmap = np.arange(6)
        rows, anchors = anchor_table(lengths, 2, 40)
        lab = labels_for(tokens, rows, anchors, 2, lmap)
        sh = labels_for(tokens, rows, anchors, 2, lmap, shuffle_shift=17, lengths=lengths)
        assert not np.array_equal(lab, sh)
        for r in range(4):
            m = rows == r
            # At offset 2 the label indices are {1..39}; shifted by +17 mod 40
            # they become {0..16, 18..39} — one index swapped per row, so per-
            # class counts move by at most 1 and totals are identical.
            c_lab = np.bincount(lab[m], minlength=6)
            c_sh = np.bincount(sh[m], minlength=6)
            assert c_lab.sum() == c_sh.sum()
            assert np.abs(c_lab - c_sh).max() <= 1
            # Alignment is destroyed for the overwhelming majority of anchors.
            assert (lab[m] == sh[m]).mean() < 0.5

    def test_slots_multi_hot(self):
        slots = np.array([[[0, 2, -1], [1, 1, -1]],
                          [[3, -1, -1], [0, 3, 2]]], dtype=np.int16)  # (2, L=2, 3)
        mh = slots_multi_hot(slots, n_slots=4)
        assert mh.shape == (2, 8)
        np.testing.assert_array_equal(mh[0], [1, 0, 1, 0, 0, 1, 0, 0])
        np.testing.assert_array_equal(mh[1], [0, 0, 0, 1, 1, 0, 1, 1])

    def test_blocks_dims_and_batches(self):
        dense = DenseBlock(np.ones((5, 3), np.float16))
        sl = SlotsBlock(np.full((5, 2, 4), -1, np.int16), n_slots=6)
        assert dense.dim == 3 and sl.dim == 12
        assert dense.batch(np.array([0, 2])).dtype == np.float32
        assert sl.batch(np.array([1])).sum() == 0  # all-pad rows -> zero features


class TestCriterionLayer:
    """margins()/verdict()/r2_summary()/oq6_survival() compute the
    criterion-bearing numbers — critic round 4 found three live defects in
    exactly this (then-untested) layer. CI-safe synthetic cell fixtures."""

    @staticmethod
    def _cell(space, off, feats, cap, seed, clusters, shuffled=False, acc=0.5):
        from run_probes import cell_id

        return {"cell": cell_id(space, off, feats, cap, seed, shuffled),
                "space": space, "offset": off, "features": feats,
                "capacity": cap, "seed": seed, "shuffled": shuffled,
                "test_acc": acc, "_clusters": dict(clusters)}

    def test_margins_hand_computed(self):
        from run_probes import margins

        c = self._cell("L1", 2, "c", "linear", 0, {0: [9, 10], 1: [8, 10]})
        a = self._cell("L1", 2, "a", "linear", 0, {0: [7, 10], 1: [7, 10]})
        rows = margins([c, a], "c")
        assert len(rows) == 1
        m = rows[0]
        assert m["margin"] == pytest.approx((9 + 8 - 7 - 7) / 20)  # 0.15
        assert m["per_seed_margin"] == {0: pytest.approx(0.15)}
        assert m["n_clusters"] == 2 and m["n_seeds"] == 1

    def test_margins_survive_json_roundtrip(self):
        """State-file resume stringifies _clusters keys; a mixed
        fresh+resumed run must compute the same margin (critic-demonstrated
        empty-intersection defect)."""
        import json as _json

        from run_probes import margins

        c = self._cell("L1", 2, "c", "linear", 0, {0: [9, 10], 1: [8, 10]})
        a = _json.loads(_json.dumps(
            self._cell("L1", 2, "a", "linear", 0, {0: [7, 10], 1: [7, 10]})))
        rows = margins([c, a], "c")
        assert rows and rows[0]["margin"] == pytest.approx(0.15)

    def test_margins_pairing_mismatch_refused(self):
        from run_probes import margins

        c = self._cell("L1", 2, "c", "linear", 0, {0: [9, 10], 1: [8, 10]})
        a = self._cell("L1", 2, "a", "linear", 0, {0: [7, 10], 1: [7, 9]})
        with pytest.raises(SystemExit, match="pairing broken"):
            margins([c, a], "c")

    def test_margins_expected_cluster_count_enforced(self):
        from run_probes import margins

        c = self._cell("L1", 2, "c", "linear", 0, {0: [9, 10], 1: [8, 10]})
        a = self._cell("L1", 2, "a", "linear", 0, {0: [7, 10], 1: [7, 10]})
        with pytest.raises(SystemExit, match="expected 30"):
            margins([c, a], "c", expected_clusters=30)

    # ---- verdict() against the amended registered rule ----

    @staticmethod
    def _full_grid(override=None):
        """12 offset>=2 triples, all safely negative unless overridden."""
        rows = []
        for space, cap in (("L1", "linear"), ("L1", "mlp256"),
                           ("L2", "linear"), ("L3", "linear")):
            for off in (2, 3, 4):
                rows.append({"space": space, "offset": off, "capacity": cap,
                             "margin": -0.01, "ci95": [-0.02, -0.001],
                             "per_seed_margin": {0: -0.01, 1: -0.01, 2: -0.01},
                             "n_seeds": 3, "n_clusters": 30})
        if override:
            rows[0].update(override)
        return rows

    def test_verdict_clean_existence_is_provisional(self):
        from run_probes import verdict

        v = verdict(self._full_grid({"margin": 0.01, "ci95": [0.002, 0.02],
                                     "per_seed_margin": {0: 0.01, 1: 0.012, 2: 0.008}}),
                    r2_pass=True)
        assert v["verdict"].startswith("EXISTENCE")
        assert "provisional" in v["verdict"]
        assert len(v["existence_triples"]) == 1

    def test_verdict_significant_but_immaterial_is_not_existence(self):
        from run_probes import verdict

        v = verdict(self._full_grid({"margin": 0.003, "ci95": [0.001, 0.004],
                                     "per_seed_margin": {0: 0.003, 1: 0.003, 2: 0.003}}),
                    r2_pass=True)
        # Bounded below the materiality floor everywhere -> NEGATIVE.
        assert v["verdict"] == "NEGATIVE"

    def test_verdict_mixed_sign_seeds_is_open(self):
        from run_probes import verdict

        v = verdict(self._full_grid({"margin": 0.01, "ci95": [0.002, 0.02],
                                     "per_seed_margin": {0: 0.01, 1: 0.02, 2: -0.001}}),
                    r2_pass=True)
        assert v["verdict"] == "OPEN"  # not EXISTENCE; CI upper >= floor

    def test_verdict_partial_or_empty_grid_never_negative(self):
        from run_probes import verdict

        assert verdict([], r2_pass=True)["verdict"] == "INCOMPLETE"
        assert verdict(self._full_grid()[:11], r2_pass=True)["verdict"] == "INCOMPLETE"
        short = self._full_grid()
        short[3]["n_seeds"] = 2
        assert verdict(short, r2_pass=True)["verdict"] == "INCOMPLETE"

    def test_verdict_r2_gate(self):
        from run_probes import verdict

        assert verdict(self._full_grid(), r2_pass=None)["verdict"] == "R2_FAILED_OR_MISSING"
        assert verdict(self._full_grid(), r2_pass=False)["verdict"] == "R2_FAILED_OR_MISSING"
        assert verdict(self._full_grid(), r2_pass=True)["verdict"] == "NEGATIVE"

    def test_verdict_open_when_upper_crosses_floor(self):
        from run_probes import verdict

        v = verdict(self._full_grid({"ci95": [-0.02, 0.01], "margin": -0.001,
                                     "per_seed_margin": {0: -0.001, 1: 0.0, 2: -0.002}}),
                    r2_pass=True)
        assert v["verdict"] == "OPEN"

    def test_r2_summary_pass_fail_and_missing(self):
        from run_probes import r2_summary

        sa = self._cell("L1", 2, "a", "linear", 0, {0: [5, 10]}, shuffled=True, acc=0.50)
        sc_ok = self._cell("L1", 2, "c", "linear", 0, {0: [5, 10]}, shuffled=True, acc=0.505)
        sc_bad = self._cell("L1", 2, "c", "linear", 0, {0: [7, 10]}, shuffled=True, acc=0.52)
        assert r2_summary([sa, sc_ok])["pass"] is True
        assert r2_summary([sa, sc_bad])["pass"] is False
        assert r2_summary([sa]) is None  # missing pair blocks the verdict
        assert r2_summary([]) is None

    def test_oq6_survival_defined_gating(self):
        from run_probes import oq6_survival

        mc = [{"space": "L1", "offset": 2, "capacity": "linear",
               "margin": 0.004, "ci95": [0.001, 0.007]}]
        mh_pos = [{"space": "L1", "offset": 2, "capacity": "linear",
                   "margin": 0.02, "ci95": [0.01, 0.03]}]
        mh_null = [{"space": "L1", "offset": 2, "capacity": "linear",
                    "margin": 0.02, "ci95": [-0.001, 0.04]}]
        s = oq6_survival(mc, mh_pos)
        assert s[0]["defined"] and s[0]["survival_fraction"] == pytest.approx(0.2)
        s2 = oq6_survival(mc, mh_null)
        assert not s2[0]["defined"] and s2[0]["survival_fraction"] is None


class TestPrefixTopic:
    """PrefixTopicBlock (post-hoc P1): features must come from tokens
    strictly BEFORE the offset-1 label (tokens[row, :anchor]) — an
    off-by-one here would smuggle the anchor's own sampled token into the
    'decoder-free' prefix and fake a topic explanation."""

    def _block(self, tokens, rows, anchors, n512=8, n16=4):
        from sideband.probes import PrefixTopicBlock

        vocab = int(tokens.max()) + 1
        map512 = (np.arange(vocab) % n512).astype(np.int64)
        map16 = (np.arange(vocab) % n16).astype(np.int64)
        return PrefixTopicBlock(tokens, rows, anchors, map512, n512, map16, n16), map512, map16

    def test_matches_independent_reference(self):
        from collections import Counter

        rng = np.random.default_rng(0)
        tokens = rng.integers(0, 50, size=(3, 30))
        rows = np.array([0, 1, 2, 2])
        anchors = np.array([0, 5, 17, 29])
        blk, map512, map16 = self._block(tokens, rows, anchors)
        X = blk.batch(np.arange(4))
        assert X.shape == (4, 8 + 3 * 4 + 1) and blk.dim == X.shape[1]
        for i in range(4):
            r, a = rows[i], anchors[i]
            pre = tokens[r, :a].tolist()
            ref = np.zeros(blk.dim, dtype=np.float64)
            if a > 0:
                for cls, n in Counter(map512[t] for t in pre).items():
                    ref[cls] = n / a
                for cls, n in Counter(map16[t] for t in pre).items():
                    ref[8 + cls] = n / a
                for wi, w in enumerate((16, 64)):
                    win = pre[-w:]
                    for cls, n in Counter(map16[t] for t in win).items():
                        ref[8 + 4 + wi * 4 + cls] = n / len(win)
            ref[-1] = np.log1p(a)
            np.testing.assert_allclose(X[i], ref, atol=1e-6)

    def test_anchor_token_excluded_prefix_included(self):
        tokens = np.zeros((1, 10), dtype=np.int64)
        tokens[0, 9] = 9  # vocab headroom for the mutations below; outside prefix
        rows = np.array([0])
        anchors = np.array([5])
        blk, _, _ = self._block(tokens, rows, anchors)
        base = blk.batch(np.array([0])).copy()
        tokens[0, 5] = 7  # the offset-1 token: must NOT move the features
        same = blk.batch(np.array([0]))
        np.testing.assert_array_equal(base, same)
        tokens[0, 4] = 7  # last prefix token: MUST move them
        moved = blk.batch(np.array([0]))
        assert not np.array_equal(base, moved)

    def test_empty_prefix_and_full_row(self):
        tokens = np.arange(20).reshape(1, 20) % 6
        blk, _, _ = self._block(tokens, np.array([0, 0]), np.array([0, 20]))
        X = blk.batch(np.arange(2))
        assert np.all(X[0, :-1] == 0.0) and X[0, -1] == 0.0  # a=0: no prefix
        assert X[1, :8].sum() == pytest.approx(1.0)  # full-prefix hist normalized
        assert X[1, -1] == pytest.approx(np.log1p(20))

    def test_window_uses_last_tokens_only(self):
        tokens = np.zeros((1, 40), dtype=np.int64)
        tokens[0, :24] = 1  # old tokens class 1; last 16 (indices 24..39) class 0
        blk, _, map16 = self._block(tokens, np.array([0]), np.array([40]))
        X = blk.batch(np.array([0]))
        w16 = X[0, 8 + 4: 8 + 8]
        assert w16[map16[0]] == pytest.approx(1.0)  # window sees only class 0
        assert w16[map16[1]] == pytest.approx(0.0)


class TestPosthocCriterion:
    """run_posthoc_topic's pairing/binding/conclusion layer (CI-safe)."""

    @staticmethod
    def _cell(space, off, feats, seed, clusters):
        from run_probes import cell_id

        return {"cell": cell_id(space, off, feats, "linear", seed),
                "space": space, "offset": off, "features": feats,
                "capacity": "linear", "seed": seed, "shuffled": False,
                "test_acc": 0.5, "_clusters": dict(clusters)}

    def test_margins_base_feats_pairing(self):
        from run_probes import margins

        top = self._cell("L1", 2, "abt", 0, {0: [9, 10], 1: [8, 10]})
        base = self._cell("L1", 2, "at", 0, {0: [7, 10], 1: [7, 10]})
        rows = margins([top, base], "abt", base_feats="at")
        assert rows and rows[0]["pair"] == "abt-at"
        assert rows[0]["margin"] == pytest.approx(0.15)
        assert margins([top, base], "abt") == []  # default base "a" absent

    def test_load_phase3_cells_bindings(self, tmp_path):
        import json as _json

        from run_posthoc_topic import load_phase3_cells
        from run_probes import state_header

        shas = {"s0.npz": "aa"}
        cell = {"cell": "x", "_clusters": {"0": [1, 2]}}
        headered = tmp_path / "h.state.jsonl"
        headered.write_text(_json.dumps(state_header(shas)) + "\n" + _json.dumps(cell) + "\n")
        got = load_phase3_cells(headered, tmp_path / "absent.json", shas)
        assert len(got) == 1 and got[0]["_clusters"] == {0: [1, 2]}
        with pytest.raises(SystemExit, match="DIFFERENT harvest"):
            load_phase3_cells(headered, tmp_path / "absent.json", {"s0.npz": "zz"})

        legacy = tmp_path / "l.state.jsonl"
        legacy.write_text(_json.dumps(cell) + "\n")
        payload = tmp_path / "p.json"
        payload.write_text(_json.dumps({"provenance": {"harvest_npz_sha256": shas}}))
        assert len(load_phase3_cells(legacy, payload, shas)) == 1
        payload.write_text(_json.dumps({"provenance": {"harvest_npz_sha256": {"s0.npz": "zz"}}}))
        with pytest.raises(SystemExit, match="DIFFERENT"):
            load_phase3_cells(legacy, payload, shas)

    def test_conclusion_labels(self):
        from run_posthoc_topic import conclusion

        def m2(space, off, margin, lo, hi, seeds=(0.01, 0.01, 0.01)):
            return {"space": space, "offset": off, "capacity": "linear",
                    "margin": margin, "ci95": [lo, hi],
                    "per_seed_margin": {i: s for i, s in enumerate(seeds)}}

        def grid(primary):  # six cells with the given L1/off2 row
            return [primary] + [m2(s, o, 0.001, -0.002, 0.004)
                                for s in ("L2_concept_k512", "L3_concept_groups_v1")
                                for o in (2, 3)] + [m2("L1_concept_k16", 3, 0.001, -0.002, 0.004)]

        quiet = grid(m2("L1_concept_k16", 2, 0.001, -0.002, 0.004))
        fires = grid(m2("L1_concept_k16", 2, 0.012, 0.006, 0.018))
        assert conclusion(fires, quiet)["label"] == "P1-SURVIVES"
        assert conclusion(quiet, quiet)["label"] == "P1-DEFLATES"
        # amended gate: a quiet M2 may NOT deflate while the equal-dims
        # arm still shows signal (dilution alone cannot produce DEFLATES)
        loud_m2n = grid(m2("L1_concept_k16", 2, 0.02, 0.01, 0.03))
        assert conclusion(quiet, loud_m2n)["label"] == "MIXED"
        loud_other = quiet[:1] + quiet[2:] + [m2("L2_concept_k512", 2, 0.02, 0.01, 0.03)]
        assert conclusion(loud_other, quiet)["label"] == "MIXED"
        assert conclusion(fires[:1], quiet)["label"] == "INCOMPLETE"
        assert conclusion(fires, quiet[:2])["label"] == "INCOMPLETE"
        neg_seed = grid(m2("L1_concept_k16", 2, 0.012, 0.006, 0.018,
                           seeds=(0.02, 0.02, -0.001)))
        assert conclusion(neg_seed, quiet)["label"] == "MIXED"

    def test_slot_shift_destroys_alignment_preserves_rows(self):
        """The (atn) shift must stay inside each row's valid anchor range
        and move every anchor in rows longer than the shift."""
        import run_posthoc_topic as rpt

        lengths = np.array([256, 100, 18, 5])
        anchors = np.array([0, 99, 17, 4])
        rows = np.arange(4)
        shifted = (anchors + rpt.SLOT_SHIFT) % lengths[rows]
        assert np.all(shifted < lengths[rows]) and np.all(shifted >= 0)
        assert np.all(shifted[:2] != anchors[:2])  # long rows: moved
        # length-5 row self-maps only when (a+17) % 5 == a — not here
        assert shifted[3] == (4 + 17) % 5


class TestPosthocParametrization:
    """S3 P1-analog (conditional pin in the S3 registration, owed at
    F-17): run_posthoc_topic gains the same source knobs as run_probes —
    every default must remain the committed S1 instrument, and a
    cross-source mixup must not silently produce a verdict."""

    def test_parser_defaults_are_s1(self):
        from run_posthoc_topic import build_parser

        d = vars(build_parser().parse_args([]))
        assert d["space_tag"] == "concept" and d["n_slots"] == 512
        assert d["parent_finding"] == "F-15"
        assert d["harvest"] == "results/real/harvest_shadow"
        assert d["out"] == "results/real/posthoc_topic_s1.json"
        for arg, name in (("buckets16", "buckets_k16.json"),
                          ("glue16", "glue_k16.json"),
                          ("buckets512", "buckets_k512.json"),
                          ("glue512", "glue_k512.json"),
                          ("groups", "concept_groups_v1.json")):
            assert d[arg].endswith(name)

    def test_conclusion_primary_space_parametrized(self):
        from run_posthoc_topic import conclusion

        def m2(space, off, margin, lo, hi):
            return {"space": space, "offset": off, "capacity": "linear",
                    "margin": margin, "ci95": [lo, hi],
                    "per_seed_margin": {i: margin for i in range(3)}}

        olmoe = [m2("L1_olmoe_k16", 2, 0.012, 0.006, 0.018)] + \
            [m2(s, o, 0.001, -0.002, 0.004)
             for s in ("L2_olmoe_k512", "L3_olmoe_groups_v1") for o in (2, 3)] + \
            [m2("L1_olmoe_k16", 3, 0.001, -0.002, 0.004)]
        got = conclusion(olmoe, olmoe, primary_space="L1_olmoe_k16", parent="F-17")
        assert got["label"] == "P1-SURVIVES"
        assert "amend F-17" in got["rule"]
        # default primary space against olmoe rows: no silent verdict
        assert conclusion(olmoe, olmoe)["label"] == "INCOMPLETE"


class TestD2D3Instrument:
    """K-3 arc D2/D3 instrument (registered 2026-09-01): train_probe's
    full_eval path must leave the default return byte-identical, and the
    tool's pure readout functions must be exact."""

    @staticmethod
    def _tiny(seed=0):
        rng = np.random.default_rng(3)
        n, d = 240, 8
        X = rng.normal(size=(n, d)).astype(np.float32)
        y = (X[:, 0] + 0.2 * rng.normal(size=n) > 0).astype(np.int64)
        split = np.array(["train"] * 160 + ["val"] * 40 + ["test"] * 40)

        class _B:
            dim = d

            def batch(self, idx):
                return X[idx]

        return [_B()], y, split

    @pytest.mark.skipif(not _has("torch"), reason="needs torch")   # 2026-10-15: the gate sits on the one test that
    def test_full_eval_default_path_byte_identical(self):            # trains; the readout checks below need numpy only
        from sideband.probes import train_probe

        blocks, y, split = self._tiny()
        a = train_probe(blocks, y, split, 2, "linear", 0, device="cpu",
                        epochs=3, batch_size=64)
        b = train_probe(blocks, y, split, 2, "linear", 0, device="cpu",
                        epochs=3, batch_size=64, full_eval=True)
        assert a["test_acc"] == b["test_acc"]
        assert a["val_acc_best"] == b["val_acc_best"]
        assert a["best_epoch"] == b["best_epoch"]
        np.testing.assert_array_equal(a["test_correct"], b["test_correct"])
        assert "full" not in a and "full" in b
        for name in ("train", "val", "test"):
            f = b["full"][name]
            np.testing.assert_array_equal(
                f["correct"], f["pred"] == y[f["idx"]])
            assert np.all((f["prob_max"] >= 0.5 - 1e-12) & (f["prob_max"] <= 1.0))
        np.testing.assert_array_equal(b["full"]["test"]["correct"],
                                      b["test_correct"])

    def test_precision_at_and_p_correct(self):
        from run_error_predictor import p_correct, precision_at

        score = np.array([0.9, 0.8, 0.7, 0.1])
        correct = np.array([True, False, True, True])
        assert precision_at(0.25, score, correct) == 1.0     # top-1
        assert precision_at(0.5, score, correct) == 0.5      # top-2
        assert precision_at(1.0, score, correct) == 0.75
        full = {"prob_max": np.array([0.9, 0.6]), "pred": np.array([1, 0])}
        np.testing.assert_allclose(p_correct(full), [0.9, 0.4])

    def test_ece_of(self):
        from run_error_predictor import ece_of

        conf = np.array([0.95] * 20)
        correct = np.array([True] * 19 + [False])
        r = ece_of(conf, correct)
        np.testing.assert_allclose(r["ece"], abs(0.95 - 0.95), atol=1e-9)
        r2 = ece_of(np.array([0.95] * 10), np.array([False] * 10))
        np.testing.assert_allclose(r2["ece"], 0.95, atol=1e-9)

    def test_selection_tie_break(self):
        # mean-over-seeds VAL precision; ties to lower offset then L1<L2<L3. Until 2026-10-16 this
        # test re-typed the tool's key (image audit S6a-C-5); it now calls the tool's selection_key
        from run_error_predictor import selection_key

        space_order = ["L1_concept_k16", "L2_concept_k512", "L3_concept_groups_v1"]
        stats = {("L2_concept_k512", 3): 0.9, ("L2_concept_k512", 2): 0.9,
                 ("L1_concept_k16", 2): 0.9, ("L3_concept_groups_v1", 2): 0.8}
        best = max(stats, key=selection_key(stats, space_order))
        assert best == ("L1_concept_k16", 2)
        # precision wins over offset and space; a lower offset wins a tie; an earlier space wins
        # a tie at the same offset
        assert max(stats | {("L3_concept_groups_v1", 4): 0.95}, key=selection_key(stats | {("L3_concept_groups_v1", 4): 0.95}, space_order)) == ("L3_concept_groups_v1", 4)
        tie = {("L3_concept_groups_v1", 1): 0.9, ("L1_concept_k16", 2): 0.9}
        assert max(tie, key=selection_key(tie, space_order)) == ("L3_concept_groups_v1", 1)
        same_off = {("L2_concept_k512", 2): 0.9, ("L1_concept_k16", 2): 0.9}
        assert max(same_off, key=selection_key(same_off, space_order)) == ("L1_concept_k16", 2)


class TestStateFile:
    """parse_state enforces the harvest-binding header (registered
    2026-08-31, critic round): a stale checkpoint from a different harvest
    resuming under fresh provenance would fabricate a replication."""

    SHAS = {"shadow_s8.npz": "aa", "shadow_s9.npz": "bb"}

    def _text(self, header_shas=None, cells=(), header=True, tail=""):
        import json as _json

        from run_probes import state_header

        lines = []
        if header:
            lines.append(_json.dumps(state_header(header_shas or self.SHAS)))
        for cid in cells:
            lines.append(_json.dumps({"cell": cid, "_clusters": {"0": [1, 2]}}))
        return "\n".join(lines) + ("\n" + tail if tail else "")

    def test_roundtrip_and_cluster_key_normalization(self):
        from run_probes import parse_state

        done = parse_state(self._text(cells=["c1", "c2"]), self.SHAS)
        assert set(done) == {"c1", "c2"}
        assert done["c1"]["_clusters"] == {0: [1, 2]}  # int keys restored

    def test_headerless_refused(self):
        from run_probes import parse_state

        with pytest.raises(SystemExit, match="harvest-binding header"):
            parse_state(self._text(cells=["c1"], header=False), self.SHAS)

    def test_wrong_harvest_refused(self):
        from run_probes import parse_state

        with pytest.raises(SystemExit, match="DIFFERENT harvest"):
            parse_state(self._text(header_shas={"shadow_s0.npz": "zz"}), self.SHAS)

    def test_empty_file_refused(self):
        from run_probes import parse_state

        with pytest.raises(SystemExit, match="empty/headerless"):
            parse_state("", self.SHAS)

    def test_torn_final_line_dropped_but_torn_middle_aborts(self):
        from run_probes import parse_state

        done = parse_state(self._text(cells=["c1"], tail='{"cell": "c2'), self.SHAS)
        assert set(done) == {"c1"}  # torn tail dropped
        torn_middle = self._text(cells=["c1"], tail='{"torn') + '\n{"cell": "c3", "_clusters": {}}'
        with pytest.raises(SystemExit, match="corrupt state line"):
            parse_state(torn_middle, self.SHAS)

    def test_header_only_resumes_zero_cells(self):
        from run_probes import parse_state

        assert parse_state(self._text(), self.SHAS) == {}


@pytest.mark.skipif(not _has("torch"), reason="needs torch")
class TestTrainProbe:  # pragma: no cover - runs where torch is installed
    def _toy(self, n=3000, d=6, n_classes=3, informative=True, seed=0):
        rng = np.random.default_rng(seed)
        y = rng.integers(0, n_classes, n)
        X = rng.normal(size=(n, d)).astype(np.float32)
        if informative:
            X[np.arange(n), y] += 3.0  # linearly separable-ish
        split = np.array(["train"] * (n // 2) + ["val"] * (n // 4) + ["test"] * (n - n // 2 - n // 4))
        return X, y, split

    def test_learns_separable_and_is_deterministic(self):
        from sideband.probes import train_probe

        X, y, split = self._toy()
        r1 = train_probe([DenseBlock(X)], y, split, 3, "linear", seed=0,
                         device="cpu", epochs=5, batch_size=256)
        r2 = train_probe([DenseBlock(X)], y, split, 3, "linear", seed=0,
                         device="cpu", epochs=5, batch_size=256)
        assert r1["test_acc"] > 0.75  # chance is 1/3; the point is >> chance
        assert r1["test_acc"] == r2["test_acc"]
        np.testing.assert_array_equal(r1["test_correct"], r2["test_correct"])
        assert len(r1["test_correct"]) == r1["n_test"]

    def test_uninformative_features_stay_near_chance(self):
        from sideband.probes import train_probe

        X, y, split = self._toy(informative=False)
        r = train_probe([DenseBlock(X)], y, split, 3, "linear", seed=0,
                        device="cpu", epochs=5, batch_size=256)
        assert r["test_acc"] < 0.45  # chance ~1/3 with sampling noise

    def test_mlp_capacity_runs(self):
        from sideband.probes import train_probe

        X, y, split = self._toy(n=1200)
        r = train_probe([DenseBlock(X)], y, split, 3, "mlp256", seed=1,
                        device="cpu", epochs=3, batch_size=256)
        assert r["test_acc"] > 0.8


class TestS3Parametrization:
    """S3 registration (2026-08-31): the probe runner's source knobs must
    leave the default S1 instrument byte-identical and refuse geometry
    mismatches."""

    def test_space_names_default_is_s1(self):
        from run_probes import space_names

        assert space_names() == {"L1": "L1_concept_k16", "L2": "L2_concept_k512",
                                 "L3": "L3_concept_groups_v1"}
        assert space_names("olmoe") == {"L1": "L1_olmoe_k16", "L2": "L2_olmoe_k512",
                                        "L3": "L3_olmoe_groups_v1"}

    def test_build_spaces_defaults_load_committed_s1(self):
        from run_probes import build_spaces

        spaces = build_spaces(None)  # data arg unused; default = committed S1 files
        assert set(spaces) == {"L1_concept_k16", "L2_concept_k512",
                               "L3_concept_groups_v1"}
        assert spaces["L1_concept_k16"]["n_classes"] == 16
        assert spaces["L2_concept_k512"]["n_classes"] == 511
        assert spaces["L3_concept_groups_v1"]["n_classes"] == 17

    def test_slots_block_refuses_wrong_alphabet(self):
        from run_probes import SlotsAnchorBlock

        slots = np.full((3, 4, 2, 8), -1, np.int16)
        slots[0, 0, 0, :3] = [0, 5, 63]
        rows = np.zeros(1, np.int64)
        anchors = np.zeros(1, np.int64)
        blk = SlotsAnchorBlock(slots, rows, anchors, n_slots=64)  # fits
        assert blk.dim == 2 * 64
        with pytest.raises(SystemExit, match="wrong --n-slots"):
            SlotsAnchorBlock(slots, rows, anchors, n_slots=63)  # 63 >= 63

    def test_feature_blocks_passes_n_slots_through(self):
        from run_probes import feature_blocks

        class _D:
            def array(self, key):
                assert key == "slots"
                s = np.full((2, 3, 4, 8), -1, np.int16)
                s[:, :, :, 0] = 7
                return s

        rows = np.zeros(2, np.int64)
        anchors = np.zeros(2, np.int64)
        (blk,) = feature_blocks(_D(), "b", rows, anchors, n_slots=64)
        assert blk.dim == 4 * 64
        hot = blk.batch(np.arange(2))
        assert hot.shape == (2, 256)
        np.testing.assert_array_equal(np.nonzero(hot[0])[0], [7, 71, 135, 199])


class TestBindSpacesToHarvest:
    """Critic blocker (2026-08-31): the CPU probe chain must refuse space
    files the harvest did not log its masses against, and an --n-slots
    that is not the harvest's telemetry alphabet."""

    @staticmethod
    def _meta_for(tmp_path, content=b"BUCKETS-A"):
        import hashlib

        p = tmp_path / "buckets_x.json"
        p.write_bytes(content)
        return p, {"buckets16_sha256": hashlib.sha256(content).hexdigest(),
                   "n_slots": 512}

    def test_matching_sha_passes(self, tmp_path):
        from run_probes import bind_spaces_to_harvest

        p, meta = self._meta_for(tmp_path)
        bind_spaces_to_harvest(meta, {"buckets16": str(p)}, n_slots=512)

    def test_wrong_file_refused(self, tmp_path):
        from run_probes import bind_spaces_to_harvest

        p, meta = self._meta_for(tmp_path)
        p.write_bytes(b"DIFFERENT")
        with pytest.raises(SystemExit, match="wrong --buckets"):
            bind_spaces_to_harvest(meta, {"buckets16": str(p)})

    def test_unbound_meta_key_skipped(self, tmp_path):
        from run_probes import bind_spaces_to_harvest

        p, _ = self._meta_for(tmp_path)
        bind_spaces_to_harvest({"n_slots": 64}, {"buckets16": str(p)}, n_slots=64)

    def test_n_slots_mismatch_refused(self, tmp_path):
        from run_probes import bind_spaces_to_harvest

        _, meta = self._meta_for(tmp_path)
        with pytest.raises(SystemExit, match="telemetry"):
            bind_spaces_to_harvest(meta, {}, n_slots=64)  # meta says 512
        bind_spaces_to_harvest({"n_experts": 64}, {}, n_slots=64)  # S3 shape


class TestVerifyLoadRegime:
    """Critic blocker (2026-08-31): the load regime is verified by module
    INSPECTION, not flag trust. Duck-typed model — no torch needed."""

    class Params4bit:  # exact bnb class name the detector matches
        pass

    class _Plain:
        pass

    def _model(self, gate_quantized=False, lm_quantized=False, with_gate=True):
        q, plain = self.Params4bit, self._Plain

        class Mod:
            def __init__(self, cls):
                self.weight = cls()

        class Model:
            def __init__(self):
                self.lm_head = Mod(q if lm_quantized else plain)
                self._mods = ([("model.layers.0.mlp.gate",
                                Mod(q if gate_quantized else plain))]
                              if with_gate else [])

            def named_modules(self):
                return self._mods + [("lm_head", self.lm_head)]

        return Model()

    def test_clean_regime_records_inspection(self):
        from sideband.real.moe_telemetry import verify_load_regime

        rec = verify_load_regime(self._model(), True, True)
        assert rec["gates_verified_unquantized"] == 1
        assert rec["gate_weight_class"] == "_Plain"
        assert rec["lm_head_weight_class"] == "_Plain"

    def test_quantized_gate_refused(self):
        from sideband.real.moe_telemetry import verify_load_regime

        with pytest.raises(SystemExit, match="QUANTIZED"):
            verify_load_regime(self._model(gate_quantized=True), True, True)

    def test_quantized_lm_head_refused(self):
        from sideband.real.moe_telemetry import verify_load_regime

        with pytest.raises(SystemExit, match="lm_head"):
            verify_load_regime(self._model(lm_quantized=True), True, False)

    def test_no_gate_match_refused(self):
        from sideband.real.moe_telemetry import verify_load_regime

        with pytest.raises(SystemExit, match="no modules match"):
            verify_load_regime(self._model(with_gate=False), True, True)

    def test_bf16_load_trivial(self):
        from sideband.real.moe_telemetry import verify_load_regime

        rec = verify_load_regime(self._model(), False, False)
        assert "no quantization" in rec["verified"]


@pytest.mark.skipif(not _has("torch"), reason="needs torch")
class TestStageEInstrument:
    """K-3 stage-E instrument changes (clarifications E1/E7, 2026-09-02):
    train_probe's return_weights path must leave the default byte-identical,
    and the exported weights applied via scheduler.LinearProbe must
    reproduce full_eval's pred/prob_max (the export self-check's logic)."""

    def test_return_weights_default_path_byte_identical(self):
        from sideband.probes import train_probe

        blocks, y, split = TestD2D3Instrument._tiny()
        a = train_probe(blocks, y, split, 2, "linear", 0, device="cpu",
                        epochs=3, batch_size=64)
        b = train_probe(blocks, y, split, 2, "linear", 0, device="cpu",
                        epochs=3, batch_size=64, return_weights=True,
                        full_eval=True)
        assert a["test_acc"] == b["test_acc"]
        assert a["val_acc_best"] == b["val_acc_best"]
        assert a["best_epoch"] == b["best_epoch"]
        np.testing.assert_array_equal(a["test_correct"], b["test_correct"])
        assert "weights" not in a
        assert set(b["weights"]) == {"weight", "bias"}
        assert b["weights"]["weight"].shape == (2, 8)

    def test_linear_probe_reproduces_full_eval(self):
        from sideband.probes import train_probe
        from sideband.scheduler import LinearProbe

        blocks, y, split = TestD2D3Instrument._tiny()
        r = train_probe(blocks, y, split, 2, "linear", 0, device="cpu",
                        epochs=3, batch_size=64, return_weights=True,
                        full_eval=True)
        probe = LinearProbe(r["weights"]["weight"], r["weights"]["bias"])
        X = blocks[0].batch(np.arange(240))
        for name in ("val", "test"):
            f = r["full"][name]
            for i, idx in enumerate(f["idx"][:25]):
                cls, conf = probe(X[idx])
                assert cls == int(f["pred"][i])
                assert abs(conf - float(f["prob_max"][i])) < 1e-5

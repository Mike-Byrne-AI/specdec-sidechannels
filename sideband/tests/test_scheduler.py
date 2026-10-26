"""CI tests for sideband.scheduler — the K-3 Attempt #1 pure-numpy
scheduling machinery (arc registration 2026-09-01, freeze pins + stage-E
clarifications 2026-09-02). Pure numpy; no torch."""

from __future__ import annotations

import numpy as np
import pytest

from sideband.scheduler import (GAMMA_BASE, GAMMA_MAX, MASS_KEYS,
                                QUANTILE_LEVELS, STOP_POSITIONS, LinearProbe,
                                SchedulerPolicy, Thresholds,
                                anchor_free_summaries, materialize_thresholds,
                                probe_input, search_frontier,
                                select_thresholds)


class TestConstants:
    def test_pinned_values(self):
        assert GAMMA_BASE == 4 and GAMMA_MAX == 6
        assert STOP_POSITIONS == (1, 2)
        assert len(QUANTILE_LEVELS) == 19
        assert QUANTILE_LEVELS[0] == 0.05 and QUANTILE_LEVELS[-1] == 0.95


class TestMaterialize:
    def test_quantiles_match_numpy(self):
        rng = np.random.default_rng(0)
        s1 = rng.uniform(size=500)
        s2 = rng.uniform(size=500) * 0.5
        t = materialize_thresholds("probe", 0.25, 0.80, s1, s2)
        assert t.stop[0] == float(np.quantile(s1, 0.25))
        assert t.stop[1] == float(np.quantile(s2, 0.25))
        assert t.extend == float(np.quantile(np.minimum(s1, s2), 0.80))
        assert t.kind == "probe"

    def test_paired_min_not_marginal_min(self):
        # The extend threshold lives on the PER-BLOCK min distribution:
        # anti-correlated signals make it differ from either marginal.
        s1 = np.array([0.1, 0.9, 0.1, 0.9])
        s2 = np.array([0.9, 0.1, 0.9, 0.1])
        t = materialize_thresholds("draft_conf", 0.5, 0.5, s1, s2)
        assert t.extend == 0.1  # min is 0.1 in every block

    def test_validation(self):
        with pytest.raises(ValueError):
            materialize_thresholds("weird", 0.5, 0.5, [0.1], [0.1])
        with pytest.raises(ValueError):
            materialize_thresholds("probe", 0.5, 0.5, [0.1, 0.2], [0.1])
        with pytest.raises(ValueError):
            materialize_thresholds("probe", 0.0, 0.5, [0.1], [0.1])
        with pytest.raises(ValueError):
            materialize_thresholds("probe", 0.5, 1.0, [0.1], [0.1])


def _thr(kind: str, stop=(0.3, 0.4), extend=0.8) -> Thresholds:
    return Thresholds(kind=kind, stop_level=0.5, extend_level=0.5,
                      stop=stop, extend=extend)


class TestFixedPolicy:
    def test_never_stops_or_extends(self):
        pol = SchedulerPolicy("fixed", gamma_base=6, gamma_max=6)
        assert not pol.stop_at(1, q_signal=0.0)
        assert not pol.extend(q_signals=(1.0, 1.0))

    def test_rejects_thresholds(self):
        with pytest.raises(ValueError):
            SchedulerPolicy("fixed", thresholds=_thr("probe"))


class TestDraftConfPolicy:
    def test_stop_low_signal(self):
        pol = SchedulerPolicy("draft_conf", thresholds=_thr("draft_conf"))
        assert pol.stop_at(1, q_signal=0.29)
        assert pol.stop_at(1, q_signal=0.30)   # <= threshold fires (E3)
        assert not pol.stop_at(1, q_signal=0.31)
        assert pol.stop_at(2, q_signal=0.40)   # per-position materialization
        assert not pol.stop_at(2, q_signal=0.41)
        assert not pol.stop_at(3, q_signal=0.0)  # positions >= 3 ride

    def test_extend_high_min(self):
        pol = SchedulerPolicy("draft_conf", thresholds=_thr("draft_conf"))
        assert pol.extend(q_signals=(0.85, 0.90))
        assert not pol.extend(q_signals=(0.70, 0.95))

    def test_missing_signal_raises(self):
        pol = SchedulerPolicy("draft_conf", thresholds=_thr("draft_conf"))
        with pytest.raises(ValueError):
            pol.stop_at(1)
        with pytest.raises(ValueError):
            pol.extend(q_signals=(0.9,))

    def test_kind_mismatch(self):
        with pytest.raises(ValueError):
            SchedulerPolicy("draft_conf", thresholds=_thr("probe"))


class TestHeadPolicy:
    """OQ-15 STAGE-C FREEZE: kind 'head' — STOP iff S_j < stop[j-1]
    (strict; low predicted survival stops), EXTEND iff S_4*a_hat_5 >=
    extend (high predicted survival extends)."""

    def _pol(self):
        return SchedulerPolicy("head", thresholds=_thr("head"))

    def test_stop_strict_below(self):
        pol = self._pol()
        assert pol.stop_at(1, head_score=0.29)
        assert not pol.stop_at(1, head_score=0.30)  # strict <: equal rides
        assert pol.stop_at(2, head_score=0.39)
        assert not pol.stop_at(2, head_score=0.40)
        assert not pol.stop_at(3, head_score=0.0)   # positions >= 3 ride

    def test_extend_at_or_above(self):
        pol = self._pol()
        assert pol.extend(head_score=0.80)
        assert pol.extend(head_score=0.81)
        assert not pol.extend(head_score=0.79)

    def test_missing_score_raises(self):
        pol = self._pol()
        with pytest.raises(ValueError):
            pol.stop_at(1, q_signal=0.5)
        with pytest.raises(ValueError):
            pol.extend(q_signals=(0.9, 0.9))

    def test_kind_mismatch_and_probe_arm_refusal(self):
        with pytest.raises(ValueError):
            SchedulerPolicy("head", thresholds=_thr("draft_conf"))
        with pytest.raises(ValueError):
            SchedulerPolicy("head", thresholds=_thr("head"), probe_arm="c")


class TestProbePolicy:
    GLUE = 5

    def _pol(self):
        return SchedulerPolicy("probe", thresholds=_thr("probe"),
                               probe_arm="c", glue_class=self.GLUE)

    def test_stop_confident_disagreement(self):
        pol = self._pol()
        assert pol.stop_at(1, probe_pred=2, probe_conf=0.5, draft_class=3)
        assert not pol.stop_at(1, probe_pred=2, probe_conf=0.2, draft_class=3)
        assert not pol.stop_at(1, probe_pred=3, probe_conf=0.9, draft_class=3)
        assert pol.stop_at(2, probe_pred=2, probe_conf=0.4, draft_class=3)
        assert not pol.stop_at(2, probe_pred=2, probe_conf=0.35, draft_class=3)
        assert not pol.stop_at(3, probe_pred=2, probe_conf=1.0, draft_class=3)

    def test_glue_is_undefined_not_disagreement(self):
        # E2: a glue class on EITHER side makes the comparison undefined —
        # neither STOP nor EXTEND may fire from it.
        pol = self._pol()
        assert not pol.stop_at(1, probe_pred=self.GLUE, probe_conf=1.0, draft_class=3)
        assert not pol.stop_at(1, probe_pred=2, probe_conf=1.0, draft_class=self.GLUE)

    def test_extend_agreement_both_offsets(self):
        pol = self._pol()
        assert pol.extend(probe_preds=(2, 3), probe_confs=(0.9, 0.85),
                          draft_classes=(2, 3))
        # one mismatch, one glue side, or low min conf each block extend
        assert not pol.extend(probe_preds=(2, 3), probe_confs=(0.9, 0.85),
                              draft_classes=(2, 4))
        assert not pol.extend(probe_preds=(2, self.GLUE), probe_confs=(0.9, 0.9),
                              draft_classes=(2, self.GLUE))
        assert not pol.extend(probe_preds=(2, 3), probe_confs=(0.9, 0.75),
                              draft_classes=(2, 3))

    def test_validation(self):
        with pytest.raises(ValueError):
            SchedulerPolicy("probe", thresholds=_thr("probe"), probe_arm="c")
        with pytest.raises(ValueError):
            SchedulerPolicy("probe", thresholds=_thr("probe"), probe_arm="x",
                            glue_class=5)
        with pytest.raises(ValueError):
            SchedulerPolicy("draft_conf", thresholds=_thr("draft_conf"),
                            probe_arm="a")


class TestAnchorFeatures:
    VOCAB = 10

    def _maps(self):
        rng = np.random.default_rng(1)
        return {name: rng.integers(0, n, size=self.VOCAB).astype(np.int64)
                for name, n in (("16", 4), ("32", 5), ("64", 6), ("512", 7))}

    def _p(self):
        rng = np.random.default_rng(2)
        p = rng.uniform(size=self.VOCAB)
        return p / p.sum()

    def test_summaries_dtypes_and_values(self):
        p, maps = self._p(), self._maps()
        s = anchor_free_summaries(p, maps)
        for name, n in (("16", 4), ("32", 5), ("64", 6), ("512", 7)):
            m = s[f"mass{name}"]
            assert m.dtype == np.float16 and m.shape == (n,)
            assert abs(float(m.astype(np.float64).sum()) - 1.0) < 5e-3
        assert s["entropy"].dtype == np.float32
        manual = -np.sum(p * np.log(p))
        assert abs(float(s["entropy"]) - manual) < 1e-6
        # top arrays zero-padded to top_m (harvest_batch layout)
        assert s["top_p"].shape == (32,) and s["top_ids"].shape == (32,)
        assert s["top_p"].dtype == np.float16 and s["top_ids"].dtype == np.int32
        vals = s["top_p"][: self.VOCAB].astype(np.float64)
        assert np.all(np.diff(vals) <= 0)  # sorted descending
        assert np.all(s["top_p"][self.VOCAB:] == 0)
        assert int(s["argmax"]) == int(np.argmax(p))

    def test_probe_input_layout(self):
        p, maps = self._p(), self._maps()
        s = anchor_free_summaries(p, maps)
        x = probe_input(s)
        assert x.dtype == np.float32
        assert x.shape == (4 + 5 + 6 + 7 + 1 + 32,)
        # segment order: mass16..mass512, entropy, top_p (E7)
        o = 0
        for name, n in (("16", 4), ("32", 5), ("64", 6), ("512", 7)):
            np.testing.assert_array_equal(x[o:o + n],
                                          s[f"mass{name}"].astype(np.float32))
            o += n
        assert x[o] == np.float32(s["entropy"])
        np.testing.assert_array_equal(x[o + 1:], s["top_p"].astype(np.float32))

    def test_probe_input_with_slots(self):
        p, maps = self._p(), self._maps()
        s = anchor_free_summaries(p, maps)
        slots = np.array([[0, 2, -1], [5, 7, 1]], dtype=np.int16)  # (L=2, top_n=3)
        x = probe_input(s, slots=slots, n_slots=8)
        base = 4 + 5 + 6 + 7 + 1 + 32
        assert x.shape == (base + 16,)
        hot = x[base:]
        expect = np.zeros(16, dtype=np.float32)
        expect[[0, 2, 8 + 5, 8 + 7, 8 + 1]] = 1.0
        np.testing.assert_array_equal(hot, expect)

    def test_mass_keys_pinned(self):
        assert MASS_KEYS == ("mass16", "mass32", "mass64", "mass512")


class TestLinearProbe:
    def test_argmax_and_confidence(self):
        pr = LinearProbe(np.eye(2, dtype=np.float32), np.zeros(2, np.float32))
        cls, conf = pr(np.array([2.0, 1.0], np.float32))
        assert cls == 0
        assert abs(conf - 1.0 / (1.0 + np.exp(-1.0))) < 1e-12
        assert pr.n_classes == 2 and pr.dim == 2

    def test_dim_mismatch(self):
        pr = LinearProbe(np.eye(2, dtype=np.float32), np.zeros(2, np.float32))
        with pytest.raises(ValueError):
            pr(np.zeros(3, np.float32))

    def test_bad_shapes(self):
        with pytest.raises(ValueError):
            LinearProbe(np.zeros((2, 3)), np.zeros(3))


def _fake_anchor(d_h=8, n_layers=2, top_n=3):
    from sideband.real.k3_live import AnchorRead

    summ = {"mass16": np.zeros(4, np.float16), "mass32": np.zeros(5, np.float16),
            "mass64": np.zeros(6, np.float16), "mass512": np.zeros(7, np.float16),
            "entropy": np.float32(1.0), "argmax": np.int32(0),
            "top_ids": np.zeros(32, np.int32), "top_p": np.zeros(32, np.float16)}
    return AnchorRead(abs_pos=10, summaries=summ,
                      slots=np.full((n_layers, top_n), -1, np.int16),
                      h=np.zeros(d_h, np.float16),
                      probe_pred={"a": (1, 2), "c": (3, 4)},
                      probe_conf={"a": (0.5, 0.6), "c": (0.7, 0.8)})


class TestByproductRecorder:
    """k3_live.ByproductRecorder — the E8 byproduct log (torch-free)."""

    def test_flags_and_padding(self):
        from sideband.real.k3_live import ByproductRecorder

        rec = ByproductRecorder(gamma_max=6)
        # rejection at drafted position 1 of a stopped 2-token block
        rec.add_block(_fake_anchor(), gamma_used=2, stop_pos=2,
                      extend_fired=False, accepted=1, proposed=[11, 12],
                      analytic=[0.9, 0.1], q_sigs=[0.4, 0.2],
                      draft_classes=[3, 5])
        # full-accept extended block
        rec.add_block(_fake_anchor(), gamma_used=6, stop_pos=0,
                      extend_fired=True, accepted=6,
                      proposed=list(range(6)), analytic=[0.5] * 6,
                      q_sigs=[0.9, 0.8], draft_classes=[1, 1])
        out = rec.finalize()
        assert int(out["n_blocks"]) == 2
        np.testing.assert_array_equal(out["acc_flags"][0], [1, 0, -1, -1, -1, -1])
        np.testing.assert_array_equal(out["acc_flags"][1], [1] * 6)
        np.testing.assert_array_equal(out["proposed"][0], [11, 12, -1, -1, -1, -1])
        assert np.isnan(out["analytic"][0][2:]).all()
        assert out["gamma_used"].tolist() == [2, 6]
        assert out["stop_pos"].tolist() == [2, 0]
        assert out["extend"].tolist() == [0, 1]
        np.testing.assert_allclose(out["q_sig"][0], [0.4, 0.2], rtol=1e-6)
        np.testing.assert_array_equal(out["probe_pred_c"][0], [3, 4])

    def test_inconsistent_record_refused(self):
        from sideband.real.k3_live import ByproductRecorder

        rec = ByproductRecorder(gamma_max=6)
        with pytest.raises(ValueError):
            rec.add_block(_fake_anchor(), gamma_used=2, stop_pos=0,
                          extend_fired=False, accepted=1, proposed=[1],
                          analytic=[0.5, 0.5], q_sigs=[0.1], draft_classes=[1])

    def test_empty_finalize(self):
        from sideband.real.k3_live import ByproductRecorder

        assert int(ByproductRecorder().finalize()["n_blocks"]) == 0


class TestK3Config:
    def test_recorder_requires_reader(self):
        from sideband.real.k3_live import ByproductRecorder, K3Config

        pol = SchedulerPolicy("fixed")
        with pytest.raises(ValueError):
            K3Config(policy=pol, reader=None, recorder=ByproductRecorder())

    def test_probe_policy_requires_reader(self):
        from sideband.real.k3_live import K3Config

        pol = SchedulerPolicy("probe", thresholds=_thr("probe"),
                              probe_arm="c", glue_class=5)
        with pytest.raises(ValueError):
            K3Config(policy=pol, reader=None)

    def test_off_configuration_allowed(self):
        from sideband.real.k3_live import K3Config

        K3Config(policy=SchedulerPolicy("fixed"))  # E10 instruments-OFF

    def test_head_policy_config_requirements(self):
        from sideband.real.k3_live import K3Config

        pol = SchedulerPolicy("head", thresholds=_thr("head"))
        with pytest.raises(ValueError):   # needs reader AND scorer
            K3Config(policy=pol)
        with pytest.raises(ValueError):   # scorer only for head kind
            K3Config(policy=SchedulerPolicy("fixed"), head_scorer=object())
        # gamma_base != 4 refused (S_4 * a_hat_5 extend semantics)
        pol5 = SchedulerPolicy("head", gamma_base=5, gamma_max=6,
                               thresholds=_thr("head"))
        with pytest.raises(ValueError, match="gamma_base 4"):
            K3Config(policy=pol5, reader=object(), head_scorer=object())


class _CountingOracle:
    """Synthetic eval oracle with the driver's caching contract."""

    def __init__(self, budget_fn, tpc_fn=None):
        self.budget_fn = budget_fn
        self.tpc_fn = tpc_fn or (lambda s, e: 3.0 + 0.01 * s - 0.005 * e)
        self.cache: dict = {}
        self.n_evals = 0

    def __call__(self, s, e):
        if (s, e) not in self.cache:
            self.n_evals += 1
            self.cache[(s, e)] = {"budget": self.budget_fn(s, e),
                                  "tokens_per_call": self.tpc_fn(s, e)}
        return self.cache[(s, e)]


class TestFrontierSearch:
    """The THRESHOLD-SEARCH REGISTRATION's pinned procedure (2026-09-02),
    checked against brute force on synthetic surfaces."""

    N = 19

    def _brute_frontier(self, oracle_fn, b_ref):
        out = {}
        for s in range(self.N):
            feas = [e for e in range(self.N)
                    if oracle_fn(s, e)["budget"] <= b_ref]
            if feas:
                out[s] = min(feas)
        return out

    def test_matches_brute_force_on_monotone_surface(self):
        # budget decreasing in extend level (the registered direction),
        # rising with stop level (probe-arm shape).
        def budget(s, e):
            return 1.20 + 0.004 * s - 0.006 * e

        oracle = _CountingOracle(budget)
        res = search_frontier(oracle, n_levels=self.N, b_ref=1.25)
        n_search_evals = oracle.n_evals  # before the brute-force sweep below
        brute = self._brute_frontier(_CountingOracle(budget), 1.25)
        assert res["frontier"] == brute
        assert res["excluded"] == [s for s in range(self.N) if s not in brute]
        # pruning actually prunes: the registered <= 6/level bound holds
        assert n_search_evals <= 6 * self.N

    def test_exclusion_and_all_infeasible(self):
        oracle = _CountingOracle(lambda s, e: 2.0)  # never feasible
        res = search_frontier(oracle, n_levels=self.N, b_ref=1.25)
        assert res["frontier"] == {} and len(res["excluded"]) == self.N
        assert select_thresholds(oracle, res["frontier"], 1.25) == {
            "label": "FAILED_INFEASIBLE"}

    def test_noise_never_fabricates_feasibility(self):
        # Non-monotone realized budget: whatever the bisection lands on,
        # the returned point's OWN eval must be feasible (the registered
        # no-interpolation rule); noise may only under-optimize.
        rng = np.random.default_rng(7)
        noise = rng.normal(0, 0.02, size=(self.N, self.N))

        def budget(s, e):
            return 1.24 - 0.004 * e + noise[s, e]

        oracle = _CountingOracle(budget)
        res = search_frontier(oracle, n_levels=self.N, b_ref=1.25)
        for s, e in res["frontier"].items():
            assert oracle(s, e)["budget"] <= 1.25
        sel = select_thresholds(oracle, res["frontier"], 1.25)
        assert sel["label"] == "SELECTED"
        assert sel["budget"] <= 1.25

    def test_selection_tie_breaks(self):
        # two frontier points with identical tokens/call: lower budget
        # wins; identical budget too: lower stop level wins.
        recs = {(0, 3): {"budget": 1.20, "tokens_per_call": 3.5},
                (1, 2): {"budget": 1.10, "tokens_per_call": 3.5},
                (2, 2): {"budget": 1.10, "tokens_per_call": 3.5}}
        oracle = lambda s, e: recs[(s, e)]  # noqa: E731
        sel = select_thresholds(oracle, {0: 3, 1: 2, 2: 2}, 1.25)
        assert (sel["stop_idx"], sel["extend_idx"]) == (1, 2)

    def test_selection_assert_fires_on_broken_bookkeeping(self):
        oracle = lambda s, e: {"budget": 9.9, "tokens_per_call": 3.0}  # noqa: E731
        with pytest.raises(AssertionError, match="B_ref"):
            select_thresholds(oracle, {0: 0}, 1.25)

    def test_requires_b_ref(self):
        with pytest.raises(ValueError):
            search_frontier(_CountingOracle(lambda s, e: 1.0),
                            n_levels=self.N, b_ref=None)


class TestLoadProbeWeights:
    def _write(self, tmp_path, tamper=False):
        import hashlib
        import json

        arrays = {}
        for arm in ("a", "c"):
            for off in (2, 3):
                arrays[f"W_{arm}_off{off}"] = np.zeros((4, 6), np.float32)
                arrays[f"b_{arm}_off{off}"] = np.zeros(4, np.float32)
        npz = tmp_path / "w.npz"
        np.savez(npz, **arrays)
        sha = hashlib.sha256(npz.read_bytes()).hexdigest()
        if tamper:
            sha = "0" * 64
        (tmp_path / "w.meta.json").write_text(json.dumps({"npz_sha256": sha}))
        return npz

    def test_loads_four_probes(self, tmp_path):
        from sideband.real.k3_live import load_probe_weights

        probes, meta = load_probe_weights(self._write(tmp_path))
        assert set(probes) == {("a", 2), ("a", 3), ("c", 2), ("c", 3)}
        assert probes[("c", 2)].n_classes == 4

    def test_sha_mismatch_refused(self, tmp_path):
        from sideband.real.k3_live import load_probe_weights

        with pytest.raises(SystemExit, match="refusing unbound"):
            load_probe_weights(self._write(tmp_path, tamper=True))

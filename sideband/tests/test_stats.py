"""CI machinery for the real-model audit (Phase 0a exit criterion)."""

import numpy as np
import pytest

from sideband.stats import (clopper_pearson, cluster_bootstrap_ci,
                            paired_cluster_delta_ci, paired_ratio_delta_ci,
                            paired_ratio_delta_of_deltas_ci)

# Reference values generated once with scipy.stats.beta (scipy 1.16.3):
#   lo = beta.ppf(alpha/2, k, n-k+1) (0 if k==0)
#   hi = beta.ppf(1-alpha/2, k+1, n-k) (1 if k==n)
# scipy is NOT a dependency; these constants pin our bisection implementation
# to the standard formulation.
SCIPY_REFERENCE = [
    (0, 50, 0.05, 0.000000000000, 0.071121736464),
    (50, 50, 0.05, 0.928878263536, 1.000000000000),
    (3, 50, 0.05, 0.012548587835, 0.165481946604),
    (17, 100, 0.05, 0.102264910036, 0.258175410632),
    (89, 100, 0.05, 0.811698867804, 0.943792979715),
    (1200, 1500, 0.05, 0.778845471288, 0.819972879838),
    (7, 8, 0.05, 0.473490329125, 0.996840276469),
    (1, 2, 0.05, 0.012579117093, 0.987420882907),
    (250, 10000, 0.05, 0.022028967353, 0.028251857386),
    (17, 100, 0.01, 0.085947259924, 0.286759505760),
]


class TestClopperPearson:
    @pytest.mark.parametrize("k,n,alpha,lo_ref,hi_ref", SCIPY_REFERENCE)
    def test_matches_scipy_reference(self, k, n, alpha, lo_ref, hi_ref):
        lo, hi = clopper_pearson(k, n, alpha)
        assert lo == pytest.approx(lo_ref, abs=1e-9)
        assert hi == pytest.approx(hi_ref, abs=1e-9)

    @pytest.mark.parametrize("k,n,alpha,lo_ref,hi_ref", SCIPY_REFERENCE)
    def test_contains_point_estimate(self, k, n, alpha, lo_ref, hi_ref):
        lo, hi = clopper_pearson(k, n, alpha)
        assert lo <= k / n <= hi

    def test_edges(self):
        lo, hi = clopper_pearson(0, 30)
        assert lo == 0.0 and 0.0 < hi < 1.0
        lo, hi = clopper_pearson(30, 30)
        assert 0.0 < lo < 1.0 and hi == 1.0

    def test_narrows_with_n(self):
        w200 = np.diff(clopper_pearson(160, 200))[0]
        w2000 = np.diff(clopper_pearson(1600, 2000))[0]
        assert w2000 < w200 / 2

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            clopper_pearson(5, 4)
        with pytest.raises(ValueError):
            clopper_pearson(-1, 4)
        with pytest.raises(ValueError):
            clopper_pearson(1, 4, alpha=0.0)


class TestClusterBootstrap:
    def test_deterministic_given_seed(self):
        succ = np.array([8, 5, 9, 2, 7, 6])
        tri = np.array([10, 9, 12, 4, 8, 7])
        a = cluster_bootstrap_ci(succ, tri, seed=42)
        b = cluster_bootstrap_ci(succ, tri, seed=42)
        assert a == b
        c = cluster_bootstrap_ci(succ, tri, seed=43)
        assert a != c  # different draw, almost surely different percentile

    def test_contains_pooled_fraction_when_homogeneous(self):
        gen = np.random.default_rng(0)
        tri = gen.integers(5, 30, size=40).astype(float)
        succ = np.round(tri * 0.8)
        lo, hi = cluster_bootstrap_ci(succ, tri, seed=1)
        pooled = succ.sum() / tri.sum()
        assert lo <= pooled <= hi
        assert 0.0 <= lo <= hi <= 1.0

    def test_wider_than_binomial_under_cluster_correlation(self):
        """Perfectly correlated clusters (all-or-nothing prompts): the
        cluster bootstrap must be wider than the independence CI."""
        tri = np.full(20, 10.0)
        succ = np.array([10.0] * 16 + [0.0] * 4)  # pooled 0.8, but clustered
        blo, bhi = cluster_bootstrap_ci(succ, tri, seed=2)
        clo, chi = clopper_pearson(160, 200)
        assert (bhi - blo) > (chi - clo)

    def test_zero_trial_clusters_are_handled(self):
        succ = np.array([5.0, 0.0, 3.0])
        tri = np.array([8.0, 0.0, 5.0])
        lo, hi = cluster_bootstrap_ci(succ, tri, seed=3)
        assert 0.0 <= lo <= hi <= 1.0

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            cluster_bootstrap_ci(np.array([1.0]), np.array([2.0]))  # 1 cluster
        with pytest.raises(ValueError):
            cluster_bootstrap_ci(np.array([3.0, 1.0]), np.array([2.0, 2.0]))  # succ > tri
        with pytest.raises(ValueError):
            cluster_bootstrap_ci(np.array([0.0, 0.0]), np.array([0.0, 0.0]))  # no trials


class TestPairedRatioDelta:
    """paired_ratio_delta_ci — the K-3 matched-budget tokens/call delta
    estimand (stage-E clarification E6, 2026-09-02)."""

    def test_reduces_to_paired_cluster_delta_when_trials_shared(self):
        # With identical denominators the joint-ratio bootstrap collapses
        # algebraically to the fraction-difference bootstrap, and both use
        # one integers() draw, so the same resamples underlie both. The
        # forms round differently (a/t - b/t vs (a-b)/t), so equality
        # holds to float associativity, not bit-exactly.
        gen = np.random.default_rng(5)
        tri = gen.integers(5, 40, size=25).astype(float)
        sa = np.floor(tri * gen.uniform(0.5, 1.0, size=25))
        sb = np.floor(tri * gen.uniform(0.3, 0.8, size=25))
        want = paired_cluster_delta_ci(sa, sb, tri, seed=7)
        got = paired_ratio_delta_ci(sa, tri, sb, tri, seed=7)
        np.testing.assert_allclose(got, want, rtol=1e-12, atol=1e-14)

    def test_point_is_ratio_of_totals_difference(self):
        na = np.array([30.0, 40.0])
        da = np.array([10.0, 10.0])
        nb = np.array([25.0, 35.0])
        db = np.array([12.0, 8.0])
        delta, lo, hi = paired_ratio_delta_ci(na, da, nb, db, seed=0)
        assert delta == (70.0 / 20.0) - (60.0 / 20.0)
        assert lo <= delta <= hi

    def test_detects_real_gap_with_differing_trials(self):
        # Arm a averages ~3.5 emitted/call, arm b ~3.0, with per-prompt
        # block counts that differ across arms (the actual K-3 shape).
        gen = np.random.default_rng(11)
        da = gen.integers(40, 90, size=30).astype(float)
        db = da + gen.integers(-8, 9, size=30)
        na = np.round(da * gen.normal(3.5, 0.1, size=30))
        nb = np.round(db * gen.normal(3.0, 0.1, size=30))
        delta, lo, hi = paired_ratio_delta_ci(na, da, nb, db, seed=1)
        assert 0.3 < delta < 0.7
        assert lo > 0

    def test_deterministic_given_seed(self):
        na = np.array([30.0, 42.0, 18.0])
        da = np.array([9.0, 12.0, 6.0])
        nb = np.array([28.0, 39.0, 15.0])
        db = np.array([10.0, 11.0, 6.0])
        assert (paired_ratio_delta_ci(na, da, nb, db, seed=3)
                == paired_ratio_delta_ci(na, da, nb, db, seed=3))

    def test_rejects_bad_inputs(self):
        ones = np.array([1.0, 1.0])
        with pytest.raises(ValueError):
            paired_ratio_delta_ci(np.array([1.0]), np.array([1.0]), ones, ones)
        with pytest.raises(ValueError):
            paired_ratio_delta_ci(-ones, ones, ones, ones)
        with pytest.raises(ValueError):
            paired_ratio_delta_ci(ones, np.zeros(2), ones, ones)


class TestPairedRatioDeltaOfDeltas:
    """OQ-20 readout R2: the cross-seed difference of two paired legs."""

    @staticmethod
    def _four(seed=5, n=40):
        gen = np.random.default_rng(seed)
        d = gen.integers(40, 90, size=n).astype(float)
        mk = lambda mu: np.round(d * gen.normal(mu, 0.1, size=n))  # noqa: E731
        return mk(3.3), d, mk(3.0), d + gen.integers(-5, 6, size=n), mk(3.2), d, mk(3.0), d

    def test_identical_legs_give_zero_with_a_zero_interval(self):
        na, da, nb, db, *_ = self._four()
        dd, lo, hi = paired_ratio_delta_of_deltas_ci(na, da, nb, db, na, da, nb, db, seed=0)
        assert dd == 0.0 and lo == 0.0 and hi == 0.0

    def test_reduces_to_the_single_leg_when_the_second_leg_is_null(self):
        na, da, nb, db, *_ = self._four()
        one = paired_ratio_delta_ci(na, da, nb, db, n_boot=500, seed=3)
        two = paired_ratio_delta_of_deltas_ci(na, da, nb, db, nb, db, nb, db, n_boot=500, seed=3)
        assert two == one

    def test_point_is_the_difference_of_the_two_pooled_deltas(self):
        na, da, nb, db, nc, dc, nd, dd_ = self._four()
        dd, lo, hi = paired_ratio_delta_of_deltas_ci(na, da, nb, db, nc, dc, nd, dd_, seed=0)
        want = (na.sum() / da.sum() - nb.sum() / db.sum()) - (nc.sum() / dc.sum() - nd.sum() / dd_.sum())
        assert dd == want and lo <= dd <= hi

    def test_deterministic_given_seed_and_rejects_bad_inputs(self):
        na, da, nb, db, nc, dc, nd, dd_ = self._four()
        assert (paired_ratio_delta_of_deltas_ci(na, da, nb, db, nc, dc, nd, dd_, seed=2)
                == paired_ratio_delta_of_deltas_ci(na, da, nb, db, nc, dc, nd, dd_, seed=2))
        ones = np.ones(2)
        with pytest.raises(ValueError):
            paired_ratio_delta_of_deltas_ci(ones, ones, ones, ones, ones, ones, ones, np.zeros(2))
        with pytest.raises(ValueError):
            paired_ratio_delta_of_deltas_ci(ones, ones, ones, ones, ones, ones, -ones, ones)

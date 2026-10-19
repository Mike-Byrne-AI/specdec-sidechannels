"""Rank-census instrument tests. Every fixture has an answer known by
construction; the RED-proof test shows the instrument FIRES under a deliberate
off-by-one so a green result later means something (cross-research C1 rule)."""

import numpy as np
import pytest

from amber.rankcensus import calibrate_tau, rank_census, stable_topk, top2_gap


def _peaky(n=40, v=16, seed=0):
    g = np.random.default_rng(seed)
    logits = g.normal(size=(n, v))
    logits[np.arange(n), g.integers(0, v, n)] += 6.0  # clear winner per row
    return logits


class TestPrimitives:
    def test_stable_topk_tie_break_matches_codec_convention(self):
        logits = np.array([[0.2, 0.4, 0.2, 0.2]])
        assert stable_topk(logits, 4).tolist() == [[1, 0, 2, 3]]

    def test_top2_gap(self):
        logits = np.array([[1.0, 3.0, 2.5], [0.0, 0.0, 0.0]])
        np.testing.assert_allclose(top2_gap(logits), [0.5, 0.0])

    def test_shape_and_finite_validation(self):
        with pytest.raises(ValueError):
            rank_census(np.zeros((3, 4)), np.zeros((4, 4)))
        with pytest.raises(ValueError):
            rank_census(np.zeros((3, 4)), np.full((3, 4), np.nan))
        with pytest.raises(ValueError):
            rank_census(np.zeros(4), np.zeros(4))


class TestCensus:
    def test_identical_dumps_zero_flips(self):
        L = _peaky()
        c = rank_census(L, L.copy(), ks=(1, 4, 8), tau=1e-6)
        assert c.top1_flips == 0 and c.top1_flip_rate == 0.0
        assert all(r == 0.0 for r in c.topk_set_flip_rate.values())
        assert all(r == 0.0 for r in c.topk_order_flip_rate.values())
        assert c.flips_beyond_tau == 0 and c.flip_gap_min is None
        assert c.max_abs_logit_delta == 0.0 and c.longest_flip_run == 0

    def test_constructed_flips_are_counted_and_attributed_exactly(self):
        n, v = 20, 8
        ref = np.zeros((n, v))
        ref[:, 0] = 5.0
        ref[:, 1] = 4.0                # gap 1.0 everywhere...
        ref[3, 1] = 4.99               # ...except a near-tie (gap 0.01) at 3
        ref[7, 1] = 4.99               # and at 7
        alt = ref.copy()
        alt[3, 1] = 5.02               # near-tie flips (within any sane tau)
        alt[7, 1] = 5.02
        alt[11, 1] = 6.0               # a WIDE-gap flip: the bug class
        c = rank_census(ref, alt, ks=(1, 2, 3), tau=0.05)
        assert c.top1_flips == 3
        assert c.top1_flip_rate == pytest.approx(3 / n)
        assert c.flips_within_tau == 2 and c.flips_beyond_tau == 1
        assert c.flip_gap_min == pytest.approx(0.01)
        assert c.flip_gap_max == pytest.approx(1.0)
        # top-2 SET is unchanged at every flip (0<->1 swap), ORDER is not
        assert c.topk_set_flip_rate["2"] == 0.0
        assert c.topk_order_flip_rate["2"] == pytest.approx(3 / n)
        assert c.topk_set_flip_rate["3"] == 0.0

    def test_set_vs_order_distinction(self):
        ref = np.array([[3.0, 2.0, 1.0, 0.0]])
        alt = np.array([[3.0, 2.0, 0.0, 1.0]])  # tokens 2/3 swap: affects k>=3 order, set only at k=3
        c = rank_census(ref, alt, ks=(1, 2, 3, 4))
        assert c.top1_flips == 0
        assert c.topk_order_flip_rate == {"1": 0.0, "2": 0.0, "3": 1.0, "4": 1.0}
        assert c.topk_set_flip_rate == {"1": 0.0, "2": 0.0, "3": 1.0, "4": 0.0}

    def test_ks_clipped_to_vocab(self):
        L = _peaky(v=6)
        c = rank_census(L, L, ks=(1, 64))
        assert c.ks == [1, 6]

    def test_burstiness_distinguishes_clustered_from_scattered(self):
        n, v = 640, 4
        ref = np.zeros((n, v)); ref[:, 0] = 1.0
        # scattered: one flip per 64-window
        alt_s = ref.copy(); alt_s[::64, 1] = 2.0
        # clustered: the same 10 flips, all consecutive
        alt_c = ref.copy(); alt_c[100:110, 1] = 2.0
        cs = rank_census(ref, alt_s, ks=(1,), window=64)
        cc = rank_census(ref, alt_c, ks=(1,), window=64)
        assert cs.top1_flips == cc.top1_flips == 10
        assert cs.dispersion_index == pytest.approx(0.0)
        assert cc.dispersion_index > 1.0
        assert cs.longest_flip_run == 1 and cc.longest_flip_run == 10

    def test_red_proof_offset_bug_fires(self):
        """Deliberate off-by-one alignment (the XB-3 left-pad hazard): the
        instrument must report flips even though the two dumps are the same
        data. If this ever passes silently, the instrument is broken."""
        L = _peaky(n=64, v=16, seed=3)
        shifted = np.roll(L, 1, axis=0)
        c = rank_census(L, shifted, ks=(1,), tau=1e-3)
        assert c.top1_flips > 0
        assert c.flips_beyond_tau > 0     # wide-gap flips => flagged as a bug
        # and restored to green
        assert rank_census(L, L, ks=(1,), tau=1e-3).flips_beyond_tau == 0


class TestCalibration:
    def test_calibrated_tau_is_the_benign_tail(self):
        L = _peaky(n=200, v=32, seed=5)
        g = np.random.default_rng(6)
        benign = L + g.normal(scale=1e-4, size=L.shape)
        tau = calibrate_tau(L, benign, quantile=0.999)
        assert 2e-4 < tau < 6e-4  # ~3.3 sigma of a 1e-4 gaussian
        # a flip caused by that benign noise sits within tau; a wide-gap one does not
        c = rank_census(L, benign, ks=(1,), tau=2 * tau)
        assert c.flips_beyond_tau == 0

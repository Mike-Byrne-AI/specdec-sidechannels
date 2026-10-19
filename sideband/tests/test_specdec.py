"""The load-bearing tests: the verifier is exact, and steering cannot change
the output distribution — only the speed."""

import numpy as np
import pytest

from sideband.dists import normalize, rng, tv_distance
from sideband.specdec import (
    RunMetrics,
    analytic_acceptance,
    residual_distribution,
    run_block,
    spec_step,
)
from sideband.steering import bucket_bias


def induced_distribution(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Closed-form distribution of spec_step's emitted token.

    P(emit y) = min(p, q)[y] + (1 - sum min(p, q)) * r[y]
    which must equal p exactly for the scheme to be lossless.
    """
    p, q = normalize(p), normalize(q)
    accept = np.minimum(p, q)
    r = residual_distribution(p, q)
    return accept + (1.0 - accept.sum()) * r


def random_dist(gen, v, sparsity=0.0):
    p = gen.random(v)
    if sparsity > 0:
        p[gen.random(v) < sparsity] = 0.0
    if p.sum() == 0:
        p[int(gen.integers(v))] = 1.0
    return normalize(p)


class TestExactness:
    def test_enumeration_random_pairs(self):
        gen = rng(0)
        for _ in range(200):
            v = int(gen.integers(2, 40))
            p = random_dist(gen, v)
            q = random_dist(gen, v, sparsity=0.3)
            np.testing.assert_allclose(induced_distribution(p, q), p, atol=1e-12)

    def test_enumeration_identical_dists(self):
        p = normalize(np.array([0.5, 0.25, 0.25]))
        np.testing.assert_allclose(induced_distribution(p, p), p, atol=1e-15)

    def test_enumeration_disjoint_supports(self):
        p = normalize(np.array([1.0, 1.0, 0.0, 0.0]))
        q = normalize(np.array([0.0, 0.0, 1.0, 1.0]))
        np.testing.assert_allclose(induced_distribution(p, q), p, atol=1e-15)

    def test_enumeration_q_missing_p_support(self):
        p = normalize(np.array([0.6, 0.3, 0.1]))
        q = normalize(np.array([1.0, 1.0, 0.0]))  # q never proposes token 2
        np.testing.assert_allclose(induced_distribution(p, q), p, atol=1e-15)

    def test_losslessness_under_arbitrary_steering(self):
        """THE safety property: any steered q still yields emitted ~ p."""
        gen = rng(1)
        for _ in range(100):
            v = int(gen.integers(4, 30))
            p = random_dist(gen, v)
            q = random_dist(gen, v)
            bucket = gen.choice(v, size=max(1, v // 3), replace=False)
            beta = float(gen.uniform(-5, 8))
            q_steered = bucket_bias(q, bucket, beta)
            np.testing.assert_allclose(induced_distribution(p, q_steered), p, atol=1e-12)

    def test_empirical_matches_target(self):
        gen = rng(2)
        p = normalize(np.array([0.45, 0.30, 0.15, 0.07, 0.03]))
        q = normalize(np.array([0.05, 0.10, 0.35, 0.30, 0.20]))
        n = 200_000
        counts = np.zeros(5)
        for _ in range(n):
            counts[spec_step(gen, p, q).emitted] += 1
        assert np.abs(counts / n - p).max() < 0.005


class TestProposalCoupling:
    """spec_step(proposed=x): the caller-supplied-proposal mode a real
    adapter must use so the verified token IS the token that conditioned the
    rest of the block (adapter bug fixed 2026-08-29)."""

    def test_supplied_proposal_is_respected(self):
        gen = rng(20)
        p = normalize(np.array([0.5, 0.3, 0.2]))
        q = normalize(np.array([0.2, 0.5, 0.3]))
        for x in range(3):
            out = spec_step(gen, p, q, proposed=x)
            assert out.proposed == x
            assert out.accept_prob == pytest.approx(min(1.0, p[x] / q[x]))

    def test_target_favored_proposal_always_accepts(self):
        gen = rng(21)
        p = normalize(np.array([0.7, 0.2, 0.1]))
        q = normalize(np.array([0.3, 0.4, 0.3]))
        assert all(spec_step(gen, p, q, proposed=0).accepted for _ in range(500))

    def test_exactness_with_external_draw(self):
        """Emitted ~ p when the caller draws x ~ q itself and passes it in —
        the end-to-end law the adapter relies on."""
        gen = rng(22)
        p = normalize(np.array([0.45, 0.30, 0.15, 0.07, 0.03]))
        q = normalize(np.array([0.05, 0.10, 0.35, 0.30, 0.20]))
        n = 200_000
        counts = np.zeros(5)
        from sideband.dists import sample

        for _ in range(n):
            x = sample(gen, q)  # the adapter's own draft draw
            counts[spec_step(gen, p, q, proposed=x).emitted] += 1
        assert np.abs(counts / n - p).max() < 0.005

    def test_conditional_law_by_enumeration(self):
        """P(emit y | proposed=x) = min(1,p/q)[x]*delta_xy + (1-min)*r[y];
        summing over x ~ q must recover p exactly."""
        gen = rng(23)
        p = random_dist(gen, 8)
        q = random_dist(gen, 8, sparsity=0.2)
        r = residual_distribution(p, q)
        total = np.zeros(8)
        for x in np.flatnonzero(q > 0):
            a = min(1.0, p[x] / q[x])
            cond = (1.0 - a) * r
            cond[x] += a
            total += q[x] * cond
        np.testing.assert_allclose(total, p, atol=1e-12)

    def test_zero_mass_proposal_fails_loud(self):
        """A supplied proposal with q[x] == 0 is a caller contract violation
        (x was not drawn from this q) — must raise, never silently accept."""
        gen = rng(25)
        p = normalize(np.array([0.5, 0.3, 0.2]))
        q = normalize(np.array([0.5, 0.5, 0.0]))
        with pytest.raises(ValueError, match="zero probability"):
            spec_step(gen, p, q, proposed=2)

    def test_none_path_unchanged(self):
        """Default mode must be byte-identical to the pre-change behavior:
        same draws, same outcomes at the same seed. Until 2026-10-16 this compared
        two identical calls (proposed=None is the default), which no change could
        fail (image audit S6a-C-2); the seed-24 draws are pinned instead, read from
        the function on the day the pin was written."""
        p = normalize(np.array([0.5, 0.3, 0.2]))
        q = normalize(np.array([0.2, 0.5, 0.3]))
        # twenty consecutive outcomes from one generator, then the next uniform draw, so both the
        # outcomes and the number of draws each step consumes are pinned (a single outcome is
        # (1, True, 1) at about a third of seeds; the reviewer measured 31.5% of seeds 0..1999)
        pinned = [(1, True, 1), (1, True, 1), (1, True, 1), (2, True, 2), (2, False, 0), (1, False, 0),
                  (2, True, 2), (0, True, 0), (1, True, 1), (1, True, 1), (2, True, 2), (0, True, 0),
                  (2, True, 2), (1, True, 1), (2, True, 2), (1, False, 0), (2, True, 2), (1, True, 1),
                  (2, True, 2), (1, True, 1)]
        for kwargs in ({}, {"proposed": None}):
            gen = rng(24)
            outs = [spec_step(gen, p, q, **kwargs) for _ in range(20)]
            assert [(o.proposed, o.accepted, o.emitted) for o in outs] == pinned
            assert gen.random() == pytest.approx(0.8028609677665026, abs=1e-15)


class TestAcceptance:
    def test_analytic_identity(self):
        gen = rng(3)
        p = random_dist(gen, 12)
        q = random_dist(gen, 12)
        assert analytic_acceptance(p, q) == pytest.approx(1.0 - tv_distance(p, q))

    def test_empirical_matches_analytic(self):
        gen = rng(4)
        p = random_dist(gen, 10)
        q = random_dist(gen, 10)
        n = 100_000
        acc = sum(spec_step(gen, p, q).accepted for _ in range(n)) / n
        assert acc == pytest.approx(analytic_acceptance(p, q), abs=0.01)

    def test_identical_dists_always_accept(self):
        gen = rng(5)
        p = normalize(np.array([0.7, 0.2, 0.1]))
        assert all(spec_step(gen, p, p).accepted for _ in range(2000))

    def test_steering_toward_p_raises_analytic_acceptance(self):
        p = normalize(np.array([0.05, 0.05, 0.6, 0.3]))
        q = normalize(np.array([0.4, 0.4, 0.1, 0.1]))
        q_good = bucket_bias(q, np.array([2, 3]), beta=2.0)
        assert analytic_acceptance(p, q_good) > analytic_acceptance(p, q)

    def test_wrong_bucket_boost_lowers_acceptance(self):
        p = normalize(np.array([0.05, 0.05, 0.6, 0.3]))
        q = normalize(np.array([0.25, 0.25, 0.3, 0.2]))
        q_bad = bucket_bias(q, np.array([0, 1]), beta=3.0)
        assert analytic_acceptance(p, q_bad) < analytic_acceptance(p, q)


class TestResidual:
    def test_residual_is_positive_part_normalized(self):
        p = normalize(np.array([0.5, 0.3, 0.2]))
        q = normalize(np.array([0.2, 0.5, 0.3]))
        r = residual_distribution(p, q)
        expect = np.clip(p - q, 0, None)
        np.testing.assert_allclose(r, expect / expect.sum(), atol=1e-15)

    def test_residual_equal_dists_falls_back_to_p(self):
        p = normalize(np.array([0.6, 0.4]))
        np.testing.assert_allclose(residual_distribution(p, p), p, atol=1e-15)


class TestBlock:
    def test_full_accept_yields_bonus(self):
        gen = rng(6)
        p = normalize(np.array([0.5, 0.3, 0.2]))
        block = run_block(gen, [p, p, p, p], [p, p, p])  # q == p: always accept
        assert block.n_accepted == 3
        assert block.bonus is not None
        assert len(block.emitted) == 4
        assert block.tokens_per_target_call == 4

    def test_stop_on_first_rejection(self):
        gen = rng(7)
        p = normalize(np.array([1.0, 0.0]))
        q_reject = normalize(np.array([0.0, 1.0]))  # proposes 1, p rejects it
        block = run_block(gen, [p, p, p], [q_reject, p])
        assert block.n_accepted == 0
        assert block.bonus is None
        assert block.emitted == [0]  # residual sample must be token 0
        assert len(block.steps) == 1

    def test_block_indexes_target_and_draft_by_offset(self):
        """One-hot distributions make the index that run_block uses at every offset visible
        in its outputs (written 2026-10-16, lane C of the 2026-10-15 image audit, item
        S6a-C-9: index mutants passed the suite before). target_dists[j] is one-hot on token
        10 + j, the bonus dist on 99; a draft one-hot on the same token is accepted with
        probability one, a draft one-hot elsewhere is rejected with probability one and the
        residual is the target's own token, so the emitted sequence names the index read
        at each step, the stop index names the rejected offset, and the bonus names the
        gamma-th target dist."""
        def one_hot(i, n=100):
            v = np.zeros(n)
            v[i] = 1.0
            return v

        targets = [one_hot(10), one_hot(11), one_hot(12), one_hot(99)]
        for seed in (0, 1, 2):
            block = run_block(rng(seed), targets, [one_hot(10), one_hot(11), one_hot(12)])
            assert block.emitted == [10, 11, 12, 99] and block.bonus == 99
            assert block.n_accepted == 3 and [s.offset for s in block.steps] == [1, 2, 3]
            assert [(s.proposed, s.accepted, s.emitted) for s in block.steps] == [
                (10, True, 10), (11, True, 11), (12, True, 12)]
            # a wrong draft at the second position: the step records offset 2, the residual
            # sample is target_dists[1]'s token, n_accepted is the number of steps before it
            block = run_block(rng(seed), targets, [one_hot(10), one_hot(40), one_hot(12)])
            assert block.emitted == [10, 11] and block.bonus is None and block.n_accepted == 1
            assert [(s.offset, s.proposed, s.accepted, s.emitted) for s in block.steps] == [
                (1, 10, True, 10), (2, 40, False, 11)]
            # a wrong draft at the third position: the bonus dist is never read
            block = run_block(rng(seed), targets, [one_hot(10), one_hot(11), one_hot(41)])
            assert block.emitted == [10, 11, 12] and block.bonus is None and block.n_accepted == 2
            assert block.steps[-1].offset == 3 and block.steps[-1].emitted == 12

    def test_block_requires_bonus_dist(self):
        gen = rng(8)
        p = normalize(np.array([0.5, 0.5]))
        with pytest.raises(ValueError):
            run_block(gen, [p, p], [p, p])  # missing gamma+1-th target dist

    def test_metrics_accounting(self):
        gen = rng(9)
        p = normalize(np.array([0.5, 0.3, 0.2]))
        m = RunMetrics()
        for _ in range(50):
            m.update(run_block(gen, [p, p, p], [p, p]))
        assert m.n_blocks == 50
        assert m.acceptance_rate == pytest.approx(1.0)
        assert m.tokens_per_target_call == pytest.approx(3.0)  # 2 accepts + bonus
        assert m.acceptance_by_offset() == {1: 1.0, 2: 1.0}

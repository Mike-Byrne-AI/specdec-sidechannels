"""Posterior-mechanism (D-10) and rejection-accounting (F-8) tests.

Deterministic given seeds, so exact inequalities at pinned configs are safe.
"""

import numpy as np
import pytest

from sideband.dists import normalize, rng
from sideband.pipeline import run_simulation, train_sidecar
from sideband.steering import posterior_bias
from sideband.synthetic import World, WorldConfig


def hard_world(n_slots=64, seed=0):
    return World(WorldConfig(
        n_slots=n_slots, support_gain=0.5, support_noise=0.5,
        background_noise=0.25, top_n=16, seed=seed,
    ))


class TestPosteriorBias:
    def test_uniform_posterior_is_exact_noop(self):
        w = World(WorldConfig(n_concepts=4, block_size=10, n_function=12))
        q = w.draft_dist(1)
        post = np.full(4, 0.25)
        np.testing.assert_allclose(posterior_bias(q, w.bucket_of_token, post, 3.0), q, atol=1e-12)

    def test_beta_zero_is_exact_noop(self):
        w = World(WorldConfig(n_concepts=4, block_size=10, n_function=12))
        q = w.draft_dist(2)
        post = np.array([0.7, 0.1, 0.1, 0.1])
        np.testing.assert_allclose(posterior_bias(q, w.bucket_of_token, post, 0.0), q, atol=1e-12)

    def test_one_hot_boosts_target_demotes_other_concepts(self):
        """The bidirectional shape that beat the argmax oracle (F-7): boost
        the predicted bucket, demote the other topical buckets, and let the
        glue bucket rise relative to the demoted ones."""
        w = World(WorldConfig(n_concepts=4, block_size=10, n_function=12))
        q = w.draft_dist(3)  # draft believes concept 3
        post = np.zeros(4); post[1] = 1.0
        q2 = posterior_bias(q, w.bucket_of_token, post, 2.5)
        m0, m2 = w.bucket_mass(q), w.bucket_mass(q2)
        fb = w.cfg.function_bucket
        assert m2[1] > m0[1]                       # predicted bucket up
        for b in (0, 2, 3):
            assert m2[b] < m0[b]                   # other concepts down
        assert m2[fb] > m0[fb]                     # glue spared, rises relatively

    def test_result_is_distribution(self):
        w = World(WorldConfig(n_concepts=4, block_size=10, n_function=12))
        q = w.draft_dist(0)
        post = normalize(rng(0).random(4))
        q2 = posterior_bias(q, w.bucket_of_token, post, 5.0)
        assert q2.min() > 0
        assert q2.sum() == pytest.approx(1.0, abs=1e-12)


class TestPipelineMechanism:
    def test_all_policies_run_with_posterior_mech(self):
        w = hard_world()
        model, _ = train_sidecar(w, seed=1, n_train=2500, epochs=8)
        for policy in ("oracle_concept_now", "oracle_concept_stale", "free_lastp", "sidecar"):
            res = run_simulation(w, seed=2, n_positions=800, gamma=3, policy=policy,
                                 beta=2.5, steer_gate="disagree", steer_mech="posterior",
                                 sidecar=model)
            d = res.to_dict()
            assert d["steer_mech"] == "posterior"
            assert d["steered_positions"] > 0
            assert 0.0 <= d["acceptance_rate"] <= 1.0

    def test_unknown_mechanism_rejected(self):
        w = hard_world()
        with pytest.raises(ValueError):
            run_simulation(w, seed=3, n_positions=100, gamma=2, policy="free_lastp",
                           beta=1.0, steer_mech="telepathy")

    def test_posterior_oracle_beats_argmax_oracle(self):
        """The mechanism finding at the oracle level (F-7): centered one-hot
        bias > single-bucket boost, same information, same gate."""
        w = hard_world(n_slots=64)
        kw = dict(seed=401, n_positions=6000, gamma=4,
                  policy="oracle_concept_stale", beta=2.5, steer_gate="disagree")
        am = run_simulation(w, steer_mech="argmax", **kw).analytic_acceptance
        po = run_simulation(w, steer_mech="posterior", **kw).analytic_acceptance
        assert po > am

    def test_posterior_sidecar_beats_argmax_sidecar(self):
        w = hard_world(n_slots=64)
        model, acc = train_sidecar(w, seed=300, n_train=8000, epochs=12)
        assert acc > 0.7
        kw = dict(seed=401, n_positions=6000, gamma=4, policy="sidecar",
                  beta=2.5, steer_gate="disagree", sidecar=model)
        am = run_simulation(w, steer_mech="argmax", **kw).analytic_acceptance
        po = run_simulation(w, steer_mech="posterior", **kw).analytic_acceptance
        assert po > am


class TestRejectionAccounting:
    def test_mass_estimator_tracks_sampled_estimator(self):
        """Same estimand, different variance (F-8): the analytic residual
        cross-bucket mass should sit near the sampled fraction."""
        w = World(WorldConfig(draft_alpha=0.6))
        res = run_simulation(w, seed=5, n_positions=6000, gamma=4, policy="none")
        sampled = res.cross_bucket_fraction()
        mass = res.cross_bucket_mass_fraction()
        assert 0.0 < mass < 1.0
        assert abs(mass - sampled) < 0.05
        assert len(res.residual_cross_mass) == len(res.rejection_buckets)

    def test_rejection_bits_finite_positive(self):
        w = World(WorldConfig(draft_alpha=0.6))
        res = run_simulation(w, seed=6, n_positions=3000, gamma=4, policy="none")
        bits = np.asarray(res.rejection_bits)
        assert len(bits) > 20
        assert np.isfinite(bits).all()
        assert (bits > 0).all()
        assert res.mean_rejection_bits() == pytest.approx(float(bits.mean()))

    def test_steered_runs_also_account(self):
        w = hard_world(n_slots=256)
        res = run_simulation(w, seed=7, n_positions=3000, gamma=4,
                             policy="oracle_concept_stale", beta=2.5,
                             steer_gate="disagree", steer_mech="posterior")
        d = res.to_dict()
        assert np.isfinite(d["cross_bucket_residual_mass"])
        assert np.isfinite(d["mean_rejection_bits"])

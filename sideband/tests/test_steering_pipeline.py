import numpy as np
import pytest

from sideband.dists import normalize, rng
from sideband.pipeline import POLICIES, run_simulation, train_sidecar
from sideband.steering import GatedSteerer, bucket_bias
from sideband.synthetic import World, WorldConfig


def tiny_world(seed=0, **overrides) -> World:
    kwargs = dict(
        n_concepts=4, block_size=10, n_function=12, n_units=256,
        units_per_concept=10, n_slots=96, top_n=12,
        rho=0.9, draft_alpha=0.6, draft_temperature=1.8, seed=seed,
    )
    kwargs.update(overrides)
    return World(WorldConfig(**kwargs))


class TestSteering:
    def test_beta_zero_is_exact_noop(self):
        gen = rng(0)
        q = normalize(gen.random(20))
        np.testing.assert_allclose(bucket_bias(q, np.arange(5), 0.0), q, atol=1e-15)

    def test_bias_moves_mass_into_bucket_monotonically(self):
        q = normalize(np.ones(10))
        bucket = np.array([0, 1, 2])
        masses = [bucket_bias(q, bucket, b)[bucket].sum() for b in (0.0, 1.0, 2.0, 4.0)]
        assert all(m2 > m1 for m1, m2 in zip(masses, masses[1:]))

    def test_bias_never_zeroes_tokens(self):
        q = normalize(np.ones(10))
        out = bucket_bias(q, np.array([0]), 30.0)
        assert (out > 0).all()

    def test_gating_blocks_low_confidence(self):
        q = normalize(np.arange(1.0, 6.0))
        s = GatedSteerer(beta=3.0, tau=0.8)
        np.testing.assert_allclose(s.steer(q, np.array([0]), confidence=0.5), q)
        assert not np.allclose(s.steer(q, np.array([0]), confidence=0.9), q)


class TestPosteriorBiasNegativeBuckets:
    def test_negative_bucket_ids_get_zero_boost(self):
        """Real buckets files mark absent tokens with -1; ext[-1] used to WRAP
        to the last bucket's boost. Negative ids must behave as glue (0)."""
        from sideband.steering import posterior_bias

        q = normalize(np.ones(6))
        buckets = np.array([0, 1, 2, -1, -1, 3])
        post = np.array([0.7, 0.1, 0.1, 0.1])  # C=4, bucket 0 boosted
        out = posterior_bias(q, buckets, post, beta=3.0)
        # the two -1 tokens must move together and identically to a glue
        # bucket id outside [0, C): compare against an explicit glue id.
        buckets_glue = np.array([0, 1, 2, 4, 4, 3])
        out_glue = posterior_bias(q, buckets_glue, post, beta=3.0)
        np.testing.assert_allclose(out, out_glue, atol=1e-15)


class TestConceptPrimitives:
    """The real adapter's concept-space semantics (steering.concept_posterior /
    concept_argmax / apply_concept_steering) pinned by hand values AND by
    equivalence with the synthetic World — the critic's mutation set (sharp
    branch swap, glue-in-the-gate, glue-boosted) must each turn a test red."""

    SBOT = np.array([0, 0, 1, 1, -1, -1])  # 6 tokens, C=2 concept, 2 glue

    def test_concept_posterior_hand_values(self):
        from sideband.steering import concept_posterior

        p = np.array([0.1, 0.1, 0.2, 0.2, 0.3, 0.1])  # concept mass .2/.4
        post = concept_posterior(p, self.SBOT, C=2)
        np.testing.assert_allclose(post, [1 / 3, 2 / 3], atol=1e-15)

    def test_concept_posterior_sharp_is_one_hot_at_argmax(self):
        """Kills the sharp/soft branch swap (critic M1): sharp must be
        EXACTLY one-hot, and at the SOFT posterior's argmax."""
        from sideband.steering import concept_posterior

        p = np.array([0.1, 0.1, 0.2, 0.2, 0.3, 0.1])
        sharp = concept_posterior(p, self.SBOT, C=2, sharp=True)
        np.testing.assert_array_equal(sharp, [0.0, 1.0])
        soft = concept_posterior(p, self.SBOT, C=2, sharp=False)
        assert not np.array_equal(soft, sharp)
        assert sharp[soft.argmax()] == 1.0

    def test_concept_posterior_zero_concept_mass_is_none(self):
        from sideband.steering import concept_posterior

        p = np.array([0.0, 0.0, 0.0, 0.0, 0.6, 0.4])  # all mass on glue
        assert concept_posterior(p, self.SBOT, C=2) is None

    def test_concept_argmax_ignores_dominant_glue_mass(self):
        """Kills glue-on-one-side-of-the-gate (critic M2): glue holds 0.9 of
        the mass. Any mutant that lets glue vote (raw argmax, or clipping -1
        ids into bucket 0) answers 0; the concept answer is 1."""
        from sideband.steering import concept_argmax

        p = np.array([0.01, 0.02, 0.03, 0.04, 0.5, 0.4])  # concept: b0=.03 < b1=.07
        assert concept_argmax(p, self.SBOT, C=2) == 1

    def test_world_equivalence(self):
        """concept_posterior/concept_argmax == World.bucket_mass[:C] /
        top_concept_bucket under the glue<->function-bucket mapping — the
        real adapter and the synthetic findings measure the same thing."""
        from sideband.steering import concept_argmax, concept_posterior

        world = tiny_world()
        C = world.cfg.n_concepts
        sbot = np.where(world.bucket_of_token == world.cfg.function_bucket,
                        -1, world.bucket_of_token)
        gen = rng(7)
        for _ in range(5):
            p = normalize(gen.random(world.cfg.vocab_size))
            bm = world.bucket_mass(p)[:C]
            np.testing.assert_allclose(concept_posterior(p, sbot, C), bm / bm.sum(),
                                       atol=1e-12)
            assert concept_argmax(p, sbot, C) == world.top_concept_bucket(p)

    def test_gate_closed_returns_q_untouched(self):
        from sideband.steering import apply_concept_steering

        q = normalize(np.array([0.5, 0.3, 0.05, 0.05, 0.05, 0.05]))  # top concept 0
        post = np.array([0.9, 0.1])  # predicts 0 -> agree -> closed
        out, opened = apply_concept_steering(q, self.SBOT, 2, post, beta=3.0)
        assert not opened and out is q

    def test_gate_ignores_glue_domination(self):
        """q's raw-mass argmax is glue, but its top CONCEPT bucket agrees
        with the prediction: the gate must stay CLOSED (D-7, both sides)."""
        from sideband.steering import apply_concept_steering

        q = np.array([0.06, 0.0, 0.04, 0.0, 0.5, 0.4])
        post = np.array([0.9, 0.1])
        out, opened = apply_concept_steering(q, self.SBOT, 2, post, beta=3.0)
        assert not opened

    def test_disagreement_opens_and_biases(self):
        from sideband.steering import apply_concept_steering, posterior_bias

        q = normalize(np.array([0.05, 0.05, 0.4, 0.3, 0.1, 0.1]))  # top concept 1
        post = np.array([0.8, 0.2])  # predicts 0 -> disagree
        out, opened = apply_concept_steering(q, self.SBOT, 2, post, beta=2.0)
        assert opened
        np.testing.assert_allclose(out, posterior_bias(q, self.SBOT, post, 2.0), atol=1e-15)

    def test_glue_tokens_never_boosted_by_either_mech(self):
        """Kills glue-boosted (critic M3 class): within-glue probability
        ratios must be invariant under both mechanisms."""
        from sideband.steering import apply_concept_steering

        q = normalize(np.array([0.05, 0.05, 0.4, 0.3, 0.15, 0.05]))
        post = np.array([0.9, 0.1])
        for mech in ("posterior", "argmax"):
            out, opened = apply_concept_steering(q, self.SBOT, 2, post, beta=4.0,
                                                 gate="always", mech=mech)
            assert opened
            assert out[4] / out[5] == pytest.approx(q[4] / q[5], rel=1e-12)
            # and the predicted bucket's tokens must actually rise
            assert out[0] + out[1] > q[0] + q[1]

    def test_always_gate_is_the_control_arm(self):
        from sideband.steering import apply_concept_steering

        q = normalize(np.array([0.5, 0.3, 0.05, 0.05, 0.05, 0.05]))
        post = np.array([0.9, 0.1])  # agree -> disagree gate closes, always opens
        _, closed = apply_concept_steering(q, self.SBOT, 2, post, 3.0, gate="disagree")
        _, opened = apply_concept_steering(q, self.SBOT, 2, post, 3.0, gate="always")
        assert not closed and opened


class TestPipeline:
    def test_all_policies_run_and_account(self):
        w = tiny_world()
        model, _ = train_sidecar(w, seed=1, n_train=3000, epochs=10)
        for policy in POLICIES:
            res = run_simulation(
                w, seed=2, n_positions=800, gamma=3, policy=policy,
                beta=2.0 if policy != "none" else 0.0, sidecar=model,
                steer_gate="disagree",
            )
            d = res.to_dict()
            assert d["n_blocks"] > 0
            assert 0.0 <= d["acceptance_rate"] <= 1.0
            assert d["n_emitted"] >= d["n_accepted"]
            if policy not in ("none",):
                assert d["steered_positions"] > 0

    def test_oracle_now_beats_vanilla_analytically(self):
        w = tiny_world()
        base = run_simulation(w, seed=3, n_positions=2500, gamma=3, policy="none")
        oracle = run_simulation(
            w, seed=3, n_positions=2500, gamma=3, policy="oracle_concept_now",
            beta=2.5, steer_gate="disagree",
        )
        assert oracle.analytic_acceptance > base.analytic_acceptance + 0.03

    def test_stale_oracle_between_vanilla_and_fresh_oracle(self):
        w = tiny_world(rho=0.8)
        kw = dict(seed=4, n_positions=2500, gamma=4)
        steer = dict(beta=2.5, steer_gate="disagree")
        base = run_simulation(w, policy="none", **kw).analytic_acceptance
        stale = run_simulation(w, policy="oracle_concept_stale", **steer, **kw).analytic_acceptance
        fresh = run_simulation(w, policy="oracle_concept_now", **steer, **kw).analytic_acceptance
        assert base < stale < fresh

    def test_huge_beta_hurts_stale_policy(self):
        """The function-word tax: past some beta, boosting the topical block
        suppresses the shared function tokens the target still wants."""
        w = tiny_world()
        kw = dict(seed=5, n_positions=2000, gamma=3, policy="oracle_concept_stale",
                  steer_gate="always")
        mild = run_simulation(w, beta=0.6, **kw).analytic_acceptance
        huge = run_simulation(w, beta=12.0, **kw).analytic_acceptance
        assert huge < mild

    def test_disagree_gate_dominates_always_at_moderate_beta(self):
        w = tiny_world()
        kw = dict(seed=12, n_positions=2500, gamma=3, policy="oracle_concept_now", beta=2.5)
        always = run_simulation(w, steer_gate="always", **kw).analytic_acceptance
        disagree = run_simulation(w, steer_gate="disagree", **kw).analytic_acceptance
        assert disagree > always

    def test_cross_bucket_fraction_bounds_and_presence(self):
        w = tiny_world(draft_alpha=0.5)
        res = run_simulation(w, seed=6, n_positions=2500, gamma=3, policy="none")
        f = res.cross_bucket_fraction()
        assert 0.0 < f < 1.0
        assert res.to_dict()["n_rejections"] > 50

    def test_sidecar_requires_model(self):
        w = tiny_world()
        with pytest.raises(ValueError):
            run_simulation(w, seed=7, n_positions=100, gamma=2, policy="sidecar")

    def test_unknown_policy_rejected(self):
        w = tiny_world()
        with pytest.raises(ValueError):
            run_simulation(w, seed=8, n_positions=100, gamma=2, policy="telepathy")

    def test_sidecar_tracks_stale_oracle(self):
        """A well-trained sidecar should land near the stale-concept oracle
        (its information ceiling) and above vanilla."""
        w = tiny_world()
        model, holdout = train_sidecar(w, seed=9, n_train=6000, epochs=20)
        assert holdout > 0.9
        kw = dict(seed=10, n_positions=2500, gamma=3, beta=2.5, steer_gate="disagree")
        base = run_simulation(w, policy="none", seed=10, n_positions=2500, gamma=3).analytic_acceptance
        stale = run_simulation(w, policy="oracle_concept_stale", **kw).analytic_acceptance
        side = run_simulation(w, policy="sidecar", sidecar=model, **kw).analytic_acceptance
        assert side > base + 0.01
        assert side <= stale + 0.01  # cannot beat its information ceiling

    def test_free_lastp_matches_stale_oracle_in_this_world(self):
        """By construction the synthetic world's telemetry and last-verified p
        encode the SAME latent concept, so free_lastp ~ oracle_concept_stale.
        This is the documented limitation (OQ-1), pinned as a test."""
        w = tiny_world()
        kw = dict(seed=11, n_positions=2500, gamma=3, beta=2.5, steer_gate="disagree")
        free = run_simulation(w, policy="free_lastp", **kw).analytic_acceptance
        stale = run_simulation(w, policy="oracle_concept_stale", **kw).analytic_acceptance
        assert free == pytest.approx(stale, abs=0.01)


class TestTelemetryStreamIsolation:
    """D-6: telemetry reads draw from their own RNG stream, so a policy that reads telemetry at
    every block stays paired with one that never reads it, at the same seed. Test written
    2026-10-16 (lane C of the 2026-10-15 image audit, item S6a-C-3): nothing exercised the
    isolation before, and a mutant that draws telemetry from the main stream passed the suite."""

    def test_sidecar_at_beta_zero_is_paired_with_policy_none(self):
        from sideband.sidecar import SoftmaxRegression

        w = tiny_world()
        x = w.sketch.multi_hot(w.telemetry(rng(0), 0))
        model = SoftmaxRegression(x.shape[0], w.cfg.n_concepts, seed=0)
        calls = []
        real = w.telemetry

        def spy(gen, c):
            calls.append(c)
            return real(gen, c)

        w.telemetry = spy
        kw = dict(seed=5, n_positions=800, gamma=3)
        none = run_simulation(w, policy="none", **kw)
        assert calls == []                      # policy none never reads telemetry
        side = run_simulation(w, policy="sidecar", beta=0.0, sidecar=model, **kw)
        assert len(calls) > 100                 # the sidecar read it at every block
        assert side.steered_positions == 0      # beta 0: the steering is an exact no-op
        # the same seed gives the same draft/verify trajectory: every metric, every rejection,
        # every analytic acceptance. A telemetry read from the main stream would shift the
        # draws after the first block and break the pairing.
        assert side.metrics.to_dict() == none.metrics.to_dict()
        assert side.rejection_buckets == none.rejection_buckets
        assert side.rejection_bits == none.rejection_bits
        assert side.analytic_acc_sum == none.analytic_acc_sum
        assert side.analytic_by_offset == none.analytic_by_offset

    def test_telemetry_stream_is_seed_bound(self):
        """The isolated stream is a function of the seed: the generator the pipeline hands to
        telemetry starts in the same state for the same seed and in another state for another
        seed (anti-vacuity for the test above: a seed-free telemetry stream would pair every run
        with policy none and still be wrong under D-6's intent)."""
        import json as _json

        from sideband.sidecar import SoftmaxRegression

        w = tiny_world()
        real = w.telemetry
        x = w.sketch.multi_hot(real(rng(0), 0))
        model = SoftmaxRegression(x.shape[0], w.cfg.n_concepts, seed=0)

        def first_state(seed):
            states = []

            def spy(gen, c):
                if not states:
                    states.append(_json.dumps(gen.bit_generator.state, sort_keys=True))
                return real(gen, c)

            w.telemetry = spy
            run_simulation(w, seed=seed, n_positions=300, gamma=3, policy="sidecar", beta=0.0, sidecar=model)
            assert states, "the sidecar policy read no telemetry"
            return states[0]

        assert first_state(1) == first_state(1)
        assert first_state(1) != first_state(2)

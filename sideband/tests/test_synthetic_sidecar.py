import numpy as np
import pytest

from sideband.dists import rng
from sideband.sidecar import SoftmaxRegression
from sideband.synthetic import TelemetryDataset, World, WorldConfig


def small_world(seed=0, **overrides) -> World:
    cfg = WorldConfig(
        n_concepts=4, block_size=10, n_function=12, n_units=256,
        units_per_concept=10, n_slots=96, top_n=12, seed=seed, **overrides,
    )
    return World(cfg)


class TestWorld:
    def test_emission_rows_are_distributions(self):
        w = small_world()
        np.testing.assert_allclose(w.P.sum(axis=1), 1.0, atol=1e-9)
        np.testing.assert_allclose(w.Q.sum(axis=1), 1.0, atol=1e-9)
        assert (w.P >= 0).all() and (w.Q >= 0).all()

    def test_function_mass_matches_lambda(self):
        w = small_world()
        fb = w.cfg.function_bucket
        for c in range(w.cfg.n_concepts):
            mass = w.bucket_mass(w.P[c])
            assert mass[fb] == pytest.approx(w.cfg.lambda_function, abs=1e-9)
            assert mass[c] == pytest.approx(
                (1 - w.cfg.lambda_function) * (1 - w.cfg.eps_leak), abs=1e-9
            )

    def test_bucket_of_token_layout(self):
        w = small_world()
        B, C = w.cfg.block_size, w.cfg.n_concepts
        assert w.bucket_of_token[0] == 0
        assert w.bucket_of_token[B * C - 1] == C - 1
        assert w.bucket_of_token[-1] == w.cfg.function_bucket
        assert len(w.tokens_in_bucket(0)) == B
        assert len(w.tokens_in_bucket(w.cfg.function_bucket)) == w.cfg.n_function

    def test_draft_flatter_than_target(self):
        from sideband.dists import entropy

        w = small_world()
        for c in range(w.cfg.n_concepts):
            assert entropy(w.Q[c]) > entropy(w.P[c])

    def test_concept_path_stickiness(self):
        w = small_world(rho=0.9)
        path = w.sample_concept_path(rng(1), 20_000)
        stay = (path[1:] == path[:-1]).mean()
        assert stay == pytest.approx(0.9, abs=0.02)

    def test_draft_concept_corruption_rate(self):
        w = small_world(draft_alpha=0.7)
        gen = rng(2)
        hits = np.mean([w.draft_concept(gen, 1) == 1 for _ in range(20_000)])
        assert hits == pytest.approx(0.7, abs=0.02)

    def test_telemetry_is_slot_ids_only(self):
        w = small_world()
        slots = w.telemetry(rng(3), 2)
        assert slots.dtype.kind == "i"
        assert slots.max() < w.cfg.n_slots
        # top_n units can collide into fewer slots but never more
        assert len(slots) <= w.cfg.top_n

    def test_telemetry_separates_concepts(self):
        """Same-concept telemetry should overlap more than cross-concept."""
        w = small_world()
        gen = rng(4)

        def jac(a, b):
            a, b = set(a.tolist()), set(b.tolist())
            return len(a & b) / len(a | b)

        same = np.mean([jac(w.telemetry(gen, 0), w.telemetry(gen, 0)) for _ in range(60)])
        cross = np.mean([jac(w.telemetry(gen, 0), w.telemetry(gen, 1)) for _ in range(60)])
        assert same > cross + 0.15


class TestSidecar:
    def test_gradients_match_finite_differences(self):
        gen = rng(5)
        X = gen.random((6, 5))
        y = np.array([0, 1, 2, 0, 1, 2])
        m = SoftmaxRegression(5, 3, seed=0)
        loss, dW, db = m.loss_and_grads(X, y, l2=0.01)
        eps = 1e-6
        for idx in [(0, 0), (2, 1), (4, 2)]:
            m.W[idx] += eps
            lp, _, _ = m.loss_and_grads(X, y, l2=0.01)
            m.W[idx] -= 2 * eps
            lm, _, _ = m.loss_and_grads(X, y, l2=0.01)
            m.W[idx] += eps
            assert dW[idx] == pytest.approx((lp - lm) / (2 * eps), rel=1e-4, abs=1e-8)
        m.b[1] += eps
        lp, _, _ = m.loss_and_grads(X, y, l2=0.01)
        m.b[1] -= 2 * eps
        lm, _, _ = m.loss_and_grads(X, y, l2=0.01)
        m.b[1] += eps
        assert db[1] == pytest.approx((lp - lm) / (2 * eps), rel=1e-4, abs=1e-8)

    def test_learns_telemetry_to_concept(self):
        w = small_world()
        data = TelemetryDataset.harvest(w, rng(6), 4000)
        m = SoftmaxRegression(w.cfg.n_slots, w.cfg.n_concepts, seed=1)
        m.fit(data.X[:3200], data.y[:3200], epochs=20)
        assert m.accuracy(data.X[3200:], data.y[3200:]) > 0.9

    def test_training_is_deterministic(self):
        w = small_world()
        data = TelemetryDataset.harvest(w, rng(7), 1000)
        a = SoftmaxRegression(w.cfg.n_slots, w.cfg.n_concepts, seed=2)
        b = SoftmaxRegression(w.cfg.n_slots, w.cfg.n_concepts, seed=2)
        a.fit(data.X, data.y, epochs=5)
        b.fit(data.X, data.y, epochs=5)
        np.testing.assert_array_equal(a.W, b.W)

    def test_predict_one_confidence(self):
        m = SoftmaxRegression(4, 3, seed=3)
        c, conf = m.predict_one(np.ones(4))
        assert 0 <= c < 3
        assert 1 / 3 - 1e-9 <= conf <= 1.0

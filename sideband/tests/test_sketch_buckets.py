import numpy as np
import pytest

from sideband.buckets import kmeans, pca_project, purity
from sideband.dists import rng
from sideband.sketch import HashSketch


class TestKMeansIterates:
    def test_actually_iterates_past_init(self):
        """Regression: the convergence check used to fire on iteration 1
        (inf <= inf), returning k-means++ init + one Lloyd step for every
        input. Unstructured data must take multiple iterations — and the
        isfinite guard makes n_iter >= 2 structurally true, so require > 2
        to also catch an always-return-at-2 regression (measured 23 here)."""
        X = rng(3).normal(size=(600, 10))
        res = kmeans(X, k=12, seed=0)
        assert res.n_iter > 2

    def test_more_iterations_strictly_lower_inertia(self):
        """Strict: on unstructured data extra Lloyd iterations must actually
        improve inertia (the buggy code returned identical results for both
        calls, so equality here would mask the regression)."""
        X = rng(4).normal(size=(400, 8))
        full = kmeans(X, k=10, seed=1, max_iter=200)
        one = kmeans(X, k=10, seed=1, max_iter=1)
        assert full.inertia < one.inertia


class TestPCAProject:
    def test_matches_svd_subspace_distances(self):
        """eigh-PCA and svd-PCA span the same subspace, so pairwise distances
        after projection must agree (the property k-means depends on)."""
        gen = rng(0)
        X = gen.normal(size=(200, 30)) @ gen.normal(size=(30, 30))  # anisotropic
        dim = 5
        Ze = pca_project(X, dim)
        mu = X.mean(axis=0)
        _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
        Zs = (X - mu) @ Vt[:dim].T
        de = np.linalg.norm(Ze[:50, None, :] - Ze[None, :50, :], axis=-1)
        ds = np.linalg.norm(Zs[:50, None, :] - Zs[None, :50, :], axis=-1)
        np.testing.assert_allclose(de, ds, atol=1e-8)

    def test_chunking_is_invisible(self):
        gen = rng(1)
        X = gen.normal(size=(100, 12))
        np.testing.assert_allclose(pca_project(X, 4, chunk=7), pca_project(X, 4, chunk=100), atol=1e-10)

    def test_deterministic(self):
        gen = rng(2)
        X = gen.normal(size=(50, 8))
        np.testing.assert_array_equal(pca_project(X, 3), pca_project(X, 3))

    def test_rejects_bad_dim(self):
        X = np.zeros((10, 4))
        with pytest.raises(ValueError):
            pca_project(X, 0)
        with pytest.raises(ValueError):
            pca_project(X, 4)


class TestHashSketch:
    def test_deterministic_given_seed(self):
        a = HashSketch(1000, 64, seed=7)
        b = HashSketch(1000, 64, seed=7)
        np.testing.assert_array_equal(a.slot_of_unit, b.slot_of_unit)
        imp = rng(0).random(1000)
        np.testing.assert_array_equal(a.slots_for(imp, 16), b.slots_for(imp, 16))

    def test_top_units_orders_by_magnitude_with_stable_ties(self):
        s = HashSketch(6, 6, seed=0)
        imp = np.array([0.5, -0.9, 0.5, 0.1, 0.9, 0.0])
        top = s.top_units(imp, 4)
        # |.| desc, index asc on ties: 1 (0.9) before 4 (0.9); 0 before 2 (0.5)
        assert top.tolist() == [1, 4, 0, 2]

    def test_slots_are_sorted_unique(self):
        s = HashSketch(500, 8, seed=1)  # heavy collisions by construction
        slots = s.slots_for(rng(2).random(500), 64)
        assert len(slots) == len(set(slots.tolist()))
        assert sorted(slots.tolist()) == slots.tolist()
        assert slots.max() < 8

    def test_multi_hot_roundtrip(self):
        s = HashSketch(100, 32, seed=3)
        slots = s.slots_for(rng(4).random(100), 10)
        v = s.multi_hot(slots)
        assert v.shape == (32,)
        np.testing.assert_array_equal(np.flatnonzero(v), slots)

    def test_more_slots_fewer_collisions(self):
        small = HashSketch(2048, 64, seed=5).expected_collision_rate()
        large = HashSketch(2048, 8192, seed=5).expected_collision_rate()
        assert large < small

    def test_top_n_clamped_to_units(self):
        s = HashSketch(10, 100, seed=6)
        assert len(s.top_units(np.ones(10), 50)) == 10

    def test_shape_guard(self):
        s = HashSketch(10, 4, seed=0)
        with pytest.raises(ValueError):
            s.slots_for(np.ones(11), 3)


class TestKMeans:
    @staticmethod
    def _blobs(gen, k=5, per=40, d=8, spread=6.0, noise=0.4):
        centers = gen.normal(0, spread, size=(k, d))
        X = np.vstack([c + gen.normal(0, noise, size=(per, d)) for c in centers])
        y = np.repeat(np.arange(k), per)
        return X, y

    def test_recovers_well_separated_blobs(self):
        gen = rng(10)
        X, y = self._blobs(gen)
        res = kmeans(X, k=5, seed=0)
        assert purity(res.labels, y) > 0.98

    def test_deterministic_given_seed(self):
        gen = rng(11)
        X, _ = self._blobs(gen)
        a = kmeans(X, k=5, seed=3)
        b = kmeans(X, k=5, seed=3)
        np.testing.assert_array_equal(a.labels, b.labels)
        assert a.inertia == b.inertia

    def test_inertia_nonincreasing_in_k(self):
        gen = rng(12)
        X, _ = self._blobs(gen, k=4, per=30)
        i3 = kmeans(X, k=3, seed=0).inertia
        i8 = kmeans(X, k=8, seed=0).inertia
        assert i8 <= i3

    def test_k_guards(self):
        X = rng(13).random((5, 2))
        with pytest.raises(ValueError):
            kmeans(X, k=0)
        with pytest.raises(ValueError):
            kmeans(X, k=6)

    def test_purity_perfect_and_chance(self):
        y = np.array([0, 0, 1, 1])
        assert purity(np.array([1, 1, 0, 0]), y) == 1.0  # relabeling is fine
        assert purity(np.array([0, 0, 0, 0]), y) == 0.5

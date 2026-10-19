"""Distribution utilities. Deterministic, numpy-only.

Everything downstream (verifier math, steering, synthetic world) goes through
these helpers so numerical conventions live in one place.
"""

from __future__ import annotations

import numpy as np

Array = np.ndarray

EPS = 1e-12


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def spawn(seed: int, n: int) -> list[np.random.Generator]:
    """n independent child generators from one seed (stable across runs)."""
    ss = np.random.SeedSequence(seed)
    return [np.random.default_rng(s) for s in ss.spawn(n)]


def softmax(logits: Array, axis: int = -1) -> Array:
    z = logits - logits.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def normalize(p: Array) -> Array:
    p = np.clip(np.asarray(p, dtype=np.float64), 0.0, None)
    s = p.sum()
    if s <= 0:
        raise ValueError("cannot normalize a zero/negative-mass vector")
    return p / s


def tv_distance(p: Array, q: Array) -> float:
    """Total variation distance between two distributions on the same support."""
    return float(0.5 * np.abs(np.asarray(p) - np.asarray(q)).sum())


def entropy(p: Array) -> float:
    p = np.asarray(p, dtype=np.float64)
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


def sample(gen: np.random.Generator, p: Array) -> int:
    """Sample an index from distribution p (defensively renormalized)."""
    p = normalize(p)
    return int(gen.choice(p.shape[0], p=p))


def temper(p: Array, temperature: float) -> Array:
    """Temperature-scale a probability vector: p^(1/T), renormalized.

    T > 1 flattens, T < 1 sharpens. T == 1 returns a normalized copy.
    """
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    p = np.clip(np.asarray(p, dtype=np.float64), EPS, None)
    return normalize(p ** (1.0 / temperature))


def zipf(n: int, s: float = 1.1) -> Array:
    """Zipf-like distribution over n items (rank 1 most probable)."""
    ranks = np.arange(1, n + 1, dtype=np.float64)
    return normalize(ranks ** (-s))

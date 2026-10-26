"""Vocabulary bucketing: deterministic k-means++ (numpy only).

Used two ways:
- synthetic: verify buckets recovered from noisy token embeddings match the
  ground-truth blocks (purity test), so the bucketing step itself is trusted;
- real: `sideband.real.bucketize_vocab` runs this on unembedding (lm_head)
  rows. Cluster on OUTPUT-side vectors: acceptance is about output tokens.

Deterministic given seed; no sklearn dependency. For very large vocabularies
on the GPU box, swapping in faiss/sklearn is fine — keep the seed and the
purity check.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dists import Array


@dataclass
class KMeansResult:
    centroids: Array          # (k, d)
    labels: Array             # (n,)
    inertia: float
    n_iter: int


def pca_project(X: Array, dim: int, chunk: int = 8192) -> Array:
    """Project rows onto the top-`dim` principal components via the d x d
    covariance eigendecomposition.

    Chosen over full SVD for memory: at real-vocab scale (128k x 4096) SVD
    wants O(n*d) float64 workspace (~13GB); this needs O(d^2) for the Gram
    matrix (~134MB) plus one chunk at a time. The top-dim eigenspace of the
    covariance IS the top-dim right-singular subspace, and pairwise distances
    after projection are basis-independent, so downstream k-means behaves
    identically to the SVD formulation (tested). Deterministic.
    """
    X = np.asarray(X)
    n, d = X.shape
    if not 0 < dim < d:
        raise ValueError(f"need 0 < dim < d={d}, got {dim}")
    mu = X.mean(axis=0, dtype=np.float64)
    C = np.zeros((d, d), dtype=np.float64)
    for s in range(0, n, chunk):
        B = X[s : s + chunk].astype(np.float64) - mu
        C += B.T @ B
    _, V = np.linalg.eigh(C)  # ascending eigenvalues
    P = V[:, ::-1][:, :dim]  # top-dim eigenvectors
    out = np.empty((n, dim), dtype=np.float64)
    for s in range(0, n, chunk):
        out[s : s + chunk] = (X[s : s + chunk].astype(np.float64) - mu) @ P
    return out


def _pairwise_sq_dists(X: Array, C: Array) -> Array:
    # (n, k) squared euclidean distances, numerically safe
    x2 = (X * X).sum(axis=1, keepdims=True)
    c2 = (C * C).sum(axis=1)[None, :]
    d = x2 + c2 - 2.0 * (X @ C.T)
    return np.clip(d, 0.0, None)


def kmeans(X: Array, k: int, seed: int = 0, max_iter: int = 200, tol: float = 1e-8) -> KMeansResult:
    X = np.asarray(X, dtype=np.float64)
    n = X.shape[0]
    if k <= 0 or k > n:
        raise ValueError(f"k must be in [1, n={n}]")
    gen = np.random.default_rng(seed)

    # --- k-means++ init ---
    centroids = np.empty((k, X.shape[1]))
    centroids[0] = X[gen.integers(n)]
    closest = _pairwise_sq_dists(X, centroids[:1]).min(axis=1)
    for j in range(1, k):
        total = closest.sum()
        if total <= 0:
            centroids[j] = X[gen.integers(n)]
        else:
            centroids[j] = X[gen.choice(n, p=closest / total)]
        closest = np.minimum(closest, _pairwise_sq_dists(X, centroids[j : j + 1]).min(axis=1))

    # --- Lloyd iterations ---
    labels = np.zeros(n, dtype=np.int64)
    prev_inertia = np.inf
    for it in range(1, max_iter + 1):
        d = _pairwise_sq_dists(X, centroids)
        labels = d.argmin(axis=1)
        inertia = float(d[np.arange(n), labels].sum())
        for j in range(k):
            members = X[labels == j]
            if len(members) > 0:
                centroids[j] = members.mean(axis=0)
            else:  # re-seed empty cluster at the worst-fit point
                centroids[j] = X[d.min(axis=1).argmax()]
        # prev_inertia is inf on the first pass; inf - x <= tol * inf is TRUE
        # (inf <= inf), so without the isfinite guard this returned after ONE
        # Lloyd iteration, always. Invisible on the easy synthetic world
        # (k-means++ init already solves it); caught on the first real-vocab
        # run (n_iter == 1 on 128k points).
        if np.isfinite(prev_inertia) and prev_inertia - inertia <= tol * max(prev_inertia, 1.0):
            return KMeansResult(centroids, labels, inertia, it)
        prev_inertia = inertia
    return KMeansResult(centroids, labels, inertia, max_iter)


def purity(pred_labels: Array, true_labels: Array) -> float:
    """Fraction of points whose predicted cluster's majority true label matches
    their own true label. 1.0 == perfect recovery up to relabeling."""
    pred_labels = np.asarray(pred_labels)
    true_labels = np.asarray(true_labels)
    correct = 0
    for j in np.unique(pred_labels):
        members = true_labels[pred_labels == j]
        counts = np.bincount(members)
        correct += counts.max()
    return correct / len(true_labels)

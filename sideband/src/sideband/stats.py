"""Confidence intervals for audit reporting. Deterministic, numpy-only.

Written for the Phase 0a exit criterion ("cross-bucket fraction per k with
CIs", docs/BLUEPRINT.md). Two estimators, reported together:

- `clopper_pearson`: exact binomial CI, computed by bisection on the binomial
  tail probability itself — the defining equations, no special-function code
  to get subtly wrong. Assumes independent trials. Audit rejections are NOT
  independent across positions within a prompt, so treat this interval's
  width as the optimistic end.
- `cluster_bootstrap_ci`: percentile bootstrap that resamples CLUSTERS
  (prompts) with replacement, honest about within-prompt correlation.
  Deterministic given seed. Not a conservative interval: a percentile
  bootstrap under-covers at small cluster counts (measured 2026-10-16 for
  `paired_cluster_delta_ci`, the same recipe, on an F-24-shaped paired
  process, docs/audits/2026-10-15-image-audit/coverage.py: coverage
  0.897 / 0.939 / 0.948 at 10 / 30 / 60 clusters for a nominal 0.95, the
  textbook (n-1)/n and z-for-t narrowing).

The pair brackets the uncertainty from two sides; neither end is conservative
at small cluster counts, so report both, never just the first.
Values are pinned against scipy.stats.beta in tests/test_stats.py (scipy is
not a dependency — the constants were generated once and committed).
"""

from __future__ import annotations

import numpy as np

from .dists import Array


def _log_binom_tail(k_lo: int, k_hi: int, n: int, p: float, logfact: Array) -> float:
    """log P(k_lo <= X <= k_hi) for X ~ Binomial(n, p), via logsumexp."""
    i = np.arange(k_lo, k_hi + 1, dtype=np.int64)
    logp, log1p = np.log(p), np.log1p(-p)
    terms = logfact[n] - logfact[i] - logfact[n - i] + i * logp + (n - i) * log1p
    m = terms.max()
    return float(m + np.log(np.exp(terms - m).sum()))


def _bisect(f, lo: float, hi: float, iters: int = 80) -> float:
    """Root of monotone f on [lo, hi] by fixed-iteration bisection (f(lo) and
    f(hi) must bracket 0). 80 iterations => interval width ~1e-24."""
    flo = f(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if (f(mid) > 0) == (flo > 0):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact (1 - alpha) binomial CI for k successes in n independent trials.

    lower solves P(X >= k | p) = alpha/2 (0 when k == 0);
    upper solves P(X <= k | p) = alpha/2 (1 when k == n).
    Each evaluation is O(n); with 80 bisection steps this is fine for any
    audit-sized n. Matches scipy's beta-quantile formulation to ~1e-10.
    """
    if not 0 <= k <= n or n <= 0:
        raise ValueError(f"need 0 <= k <= n with n > 0, got k={k}, n={n}")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    logfact = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, n + 1, dtype=np.float64)))))
    half = alpha / 2.0
    tiny = 1e-15

    if k == 0:
        lo = 0.0
    else:
        lo = _bisect(lambda p: _log_binom_tail(k, n, n, p, logfact) - np.log(half),
                     tiny, 1.0 - tiny)
    if k == n:
        hi = 1.0
    else:
        hi = _bisect(lambda p: np.log(half) - _log_binom_tail(0, k, n, p, logfact),
                     tiny, 1.0 - tiny)
    return lo, hi


def cluster_bootstrap_ci(
    successes: Array,
    trials: Array,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile CI for the pooled fraction sum(successes)/sum(trials),
    resampling clusters with replacement.

    For the rejection audit: one cluster per prompt, successes = cross-bucket
    rejections, trials = rejections. Requires >= 2 clusters. Deterministic
    given seed (own generator; never touches simulation RNG streams, D-6).
    Resamples with zero total trials are dropped (possible only when some
    clusters have zero trials).
    """
    successes = np.asarray(successes, dtype=np.float64)
    trials = np.asarray(trials, dtype=np.float64)
    if successes.shape != trials.shape or successes.ndim != 1:
        raise ValueError("successes and trials must be 1-D arrays of equal length")
    n_clusters = successes.shape[0]
    if n_clusters < 2:
        raise ValueError("cluster bootstrap needs >= 2 clusters")
    if np.any(trials < 0) or np.any(successes < 0) or np.any(successes > trials):
        raise ValueError("need 0 <= successes <= trials per cluster")
    if trials.sum() <= 0:
        raise ValueError("no trials in any cluster")

    gen = np.random.default_rng(seed)
    idx = gen.integers(0, n_clusters, size=(n_boot, n_clusters))
    s = successes[idx].sum(axis=1)
    t = trials[idx].sum(axis=1)
    valid = t > 0
    frac = s[valid] / t[valid]
    lo, hi = np.percentile(frac, [100 * alpha / 2.0, 100 * (1.0 - alpha / 2.0)])
    return float(lo), float(hi)


def paired_cluster_delta_ci(
    successes_a: Array,
    successes_b: Array,
    trials: Array,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """(delta, lo, hi) for the POOLED PAIRED difference of two fractions
    measured on the same trials per cluster: delta = sum(a - b) / sum(n),
    percentile CI by resampling clusters with replacement.

    The Phase-3 margin estimand: one cluster per test prompt, successes_x =
    correct predictions of probe x on that prompt's anchors, trials = the
    prompt's anchors (identical for both probes — pairing is per anchor).
    Same recipe and defaults as cluster_bootstrap_ci; deterministic given
    seed (own generator, D-6)."""
    successes_a = np.asarray(successes_a, dtype=np.float64)
    successes_b = np.asarray(successes_b, dtype=np.float64)
    trials = np.asarray(trials, dtype=np.float64)
    if not (successes_a.shape == successes_b.shape == trials.shape) or trials.ndim != 1:
        raise ValueError("successes_a/successes_b/trials must be 1-D arrays of equal length")
    n_clusters = trials.shape[0]
    if n_clusters < 2:
        raise ValueError("cluster bootstrap needs >= 2 clusters")
    for s in (successes_a, successes_b):
        if np.any(s < 0) or np.any(s > trials):
            raise ValueError("need 0 <= successes <= trials per cluster")
    if trials.sum() <= 0:
        raise ValueError("no trials in any cluster")

    delta = float((successes_a - successes_b).sum() / trials.sum())
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, n_clusters, size=(n_boot, n_clusters))
    d = (successes_a - successes_b)[idx].sum(axis=1)
    t = trials[idx].sum(axis=1)
    valid = t > 0
    frac = d[valid] / t[valid]
    lo, hi = np.percentile(frac, [100 * alpha / 2.0, 100 * (1.0 - alpha / 2.0)])
    return delta, float(lo), float(hi)


def paired_ratio_delta_ci(
    num_a: Array,
    den_a: Array,
    num_b: Array,
    den_b: Array,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """(delta, lo, hi) for sum(num_a)/sum(den_a) - sum(num_b)/sum(den_b)
    with a JOINT cluster bootstrap: one index draw is applied to BOTH
    arms' per-cluster (numerator, denominator) pairs, so the pairing at
    identical seeds is preserved while each arm keeps its OWN trial
    counts — the K-3 matched-budget tokens/call delta estimand (stage-E
    clarification E6, 2026-09-02: paired_cluster_delta_ci's conventions
    extended to per-arm denominators; same n_boot/seed/percentile
    recipe, deterministic given seed, D-6).

    For tokens/call: one cluster per prompt, num_x = emitted tokens,
    den_x = verify calls (n_blocks) of arm x on that prompt. Resamples
    where either arm's total denominator is zero are dropped (possible
    only when some clusters have zero denominator)."""
    num_a = np.asarray(num_a, dtype=np.float64)
    den_a = np.asarray(den_a, dtype=np.float64)
    num_b = np.asarray(num_b, dtype=np.float64)
    den_b = np.asarray(den_b, dtype=np.float64)
    shapes = {a.shape for a in (num_a, den_a, num_b, den_b)}
    if len(shapes) != 1 or num_a.ndim != 1:
        raise ValueError("num/den arrays must be 1-D and of equal length")
    n_clusters = num_a.shape[0]
    if n_clusters < 2:
        raise ValueError("cluster bootstrap needs >= 2 clusters")
    for arr in (num_a, den_a, num_b, den_b):
        if np.any(arr < 0):
            raise ValueError("numerators and denominators must be >= 0")
    if den_a.sum() <= 0 or den_b.sum() <= 0:
        raise ValueError("no trials in some arm")

    delta = float(num_a.sum() / den_a.sum() - num_b.sum() / den_b.sum())
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, n_clusters, size=(n_boot, n_clusters))
    ta = den_a[idx].sum(axis=1)
    tb = den_b[idx].sum(axis=1)
    valid = (ta > 0) & (tb > 0)
    d = (num_a[idx].sum(axis=1)[valid] / ta[valid]
         - num_b[idx].sum(axis=1)[valid] / tb[valid])
    lo, hi = np.percentile(d, [100 * alpha / 2.0, 100 * (1.0 - alpha / 2.0)])
    return delta, float(lo), float(hi)


def paired_ratio_delta_of_deltas_ci(
    num_a: Array,
    den_a: Array,
    num_b: Array,
    den_b: Array,
    num_c: Array,
    den_c: Array,
    num_d: Array,
    den_d: Array,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """(dd, lo, hi) for the DIFFERENCE of two paired ratio deltas on one
    cluster set: (sum(num_a)/sum(den_a) - sum(num_b)/sum(den_b)) -
    (sum(num_c)/sum(den_c) - sum(num_d)/sum(den_d)), with ONE joint cluster
    index draw applied to all four arms' per-cluster (numerator, denominator)
    pairs — the cross-seed difference of two tokens/call legs replayed on the
    same prompts (OQ-20 seed-replay readout R2: (a, b) the leg at one seed,
    (c, d) the same two policies at another). paired_ratio_delta_ci's recipe
    exactly (same n_boot / seed / percentile; the index draws are the same
    draws, so with num_c == num_d and den_c == den_d this reduces to that
    estimator's interval bit for bit). Resamples where any arm's total
    denominator is zero are dropped."""
    arrs = [np.asarray(x, dtype=np.float64)
            for x in (num_a, den_a, num_b, den_b, num_c, den_c, num_d, den_d)]
    shapes = {x.shape for x in arrs}
    if len(shapes) != 1 or arrs[0].ndim != 1:
        raise ValueError("num/den arrays must be 1-D and of equal length")
    n_clusters = arrs[0].shape[0]
    if n_clusters < 2:
        raise ValueError("cluster bootstrap needs >= 2 clusters")
    for arr in arrs:
        if np.any(arr < 0):
            raise ValueError("numerators and denominators must be >= 0")
    nums, dens = arrs[0::2], arrs[1::2]
    if any(x.sum() <= 0 for x in dens):
        raise ValueError("no trials in some arm")

    def _dd(sums_n, sums_d):
        return (sums_n[0] / sums_d[0] - sums_n[1] / sums_d[1]) - (sums_n[2] / sums_d[2] - sums_n[3] / sums_d[3])

    dd = float(_dd([x.sum() for x in nums], [x.sum() for x in dens]))
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, n_clusters, size=(n_boot, n_clusters))
    tn = [x[idx].sum(axis=1) for x in nums]
    td = [x[idx].sum(axis=1) for x in dens]
    valid = np.ones(n_boot, dtype=bool)
    for t in td:
        valid &= t > 0
    d = _dd([t[valid] for t in tn], [t[valid] for t in td])
    lo, hi = np.percentile(d, [100 * alpha / 2.0, 100 * (1.0 - alpha / 2.0)])
    return dd, float(lo), float(hi)

"""Rank-stability census: the instrument for OQ-2 / BLUEPRINT Phase 2.

Amber's determinism contract (D-5, narrowed by F-2) is that the DRAFT's token
ORDERING reproduces at decode time — not its logits bitwise. This module
measures how far two logit dumps of the same draft over the same teacher-forced
positions (e.g. CPU fp32 vs GPU bf16, or batch=1 vs batch=8) disagree in
exactly the quantity the codec depends on:

  * top-1 flip rate      — the draft argmax changed (a rank-1 correction
                           becomes a silent decode divergence)
  * top-k SET flip rate  — the set of top-k tokens changed (an escape symbol
                           would be needed)
  * top-k ORDER flip rate — the tuple changed (the rank of some correction
                           would change)
  * near-tie attribution — every top-1 flip carries the reference top-2 logit
                           gap at that position; a flip at a hairline gap is
                           fp noise, a flip at a wide gap is a BUG (probelab
                           81-C rule via cross-research XB-3). The tolerance
                           `tau` is CALIBRATED from a benign perturbation, never
                           picked (eot TP-10 method).
  * burstiness           — index of dispersion of flip counts over windows and
                           the longest run of consecutive flips. Lockstep
                           E-006: bursty corrections are a different wire
                           format (run-length vs position-delta), not a tuning
                           problem.

Provenance: lockstep TP-4 / E-006 (drift census shape), cross-research XB-3
(calibrated tolerance, near-tie budget, discrete invariants never toleranced).
Order convention is the codec's own `stable_order` (descending value, ascending
index on ties) applied to logits, so this instrument and the codec agree on
what "the order" is by construction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


def _validate_pair(ref: np.ndarray, alt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ref = np.asarray(ref)
    alt = np.asarray(alt)
    if ref.ndim != 2 or alt.ndim != 2:
        raise ValueError("logit dumps must be 2-D arrays of shape (positions, vocab)")
    if ref.shape != alt.shape:
        raise ValueError(f"logit dumps differ in shape: {ref.shape} vs {alt.shape}")
    if ref.shape[0] == 0 or ref.shape[1] < 2:
        raise ValueError("need at least one position and a vocabulary of size >= 2")
    if not (np.all(np.isfinite(ref)) and np.all(np.isfinite(alt))):
        raise ValueError("logit dumps contain non-finite values")
    return ref.astype(np.float64), alt.astype(np.float64)


def stable_topk(logits: np.ndarray, k: int) -> np.ndarray:
    """Top-k token indices per row, descending value, ascending index on ties.
    Same lexsort convention as amber.codec.stable_order (full-order version)."""
    n, v = logits.shape
    if not (1 <= k <= v):
        raise ValueError(f"k must be in [1, vocab]; got {k} for vocab {v}")
    idx = np.lexsort((np.broadcast_to(np.arange(v), (n, v)), -logits), axis=1)
    return idx[:, :k]


def top2_gap(logits: np.ndarray) -> np.ndarray:
    """Reference top-1 minus top-2 logit per position (>= 0)."""
    part = -np.partition(-logits, 1, axis=1)[:, :2]
    return part[:, 0] - part[:, 1]


@dataclass
class RankCensus:
    n_positions: int
    vocab: int
    ks: list[int]
    top1_flip_rate: float
    top1_flips: int
    topk_set_flip_rate: dict[str, float]
    topk_order_flip_rate: dict[str, float]
    # near-tie attribution of top-1 flips (gaps are from the REFERENCE dump)
    tau: float | None
    flip_gap_min: float | None
    flip_gap_median: float | None
    flip_gap_max: float | None
    flips_within_tau: int | None
    flips_beyond_tau: int | None      # the number that must be 0 for a clean pass
    # burstiness of top-1 flips
    window: int
    dispersion_index: float | None    # var/mean of per-window flip counts; ~1 Poisson
    longest_flip_run: int
    max_abs_logit_delta: float
    p99_abs_logit_delta: float
    delta_coverage: float = 1.0       # fraction of ref top-k tokens present in alt dump (top-k mode)

    def to_dict(self) -> dict:
        return asdict(self)


def rank_census(ref_logits, alt_logits, ks=(1, 8, 64), tau: float | None = None,
                window: int = 64) -> RankCensus:
    """Compare two logit dumps of the same positions. `ref` defines the gaps.

    ks beyond the vocabulary size are clipped to it (and reported as such)."""
    ref, alt = _validate_pair(ref_logits, alt_logits)
    n, v = ref.shape
    if window < 1:
        raise ValueError("window must be >= 1")
    ks_eff = sorted({min(int(k), v) for k in ks})
    if any(k < 1 for k in ks_eff):
        raise ValueError("ks must be >= 1")

    kmax = max(ks_eff)
    ref_top = stable_topk(ref, kmax)
    alt_top = stable_topk(alt, kmax)
    delta = np.abs(ref - alt)
    return _census_core(ref_top, alt_top, top2_gap(ref), ks_eff, tau, window,
                        max_delta=float(delta.max()), p99_delta=float(np.percentile(delta, 99)),
                        vocab=v)


def _census_core(ref_top: np.ndarray, alt_top: np.ndarray, gaps: np.ndarray, ks_eff: list[int],
                 tau: float | None, window: int, max_delta: float, p99_delta: float,
                 vocab: int | None = None) -> RankCensus:
    n = ref_top.shape[0]
    top1_flip = ref_top[:, 0] != alt_top[:, 0]
    n_flips = int(top1_flip.sum())

    set_rates: dict[str, float] = {}
    order_rates: dict[str, float] = {}
    for k in ks_eff:
        r, a = ref_top[:, :k], alt_top[:, :k]
        order_flip = np.any(r != a, axis=1)
        set_flip = np.array([set(r[i].tolist()) != set(a[i].tolist()) for i in range(n)], dtype=bool)
        set_rates[str(k)] = float(set_flip.mean())
        order_rates[str(k)] = float(order_flip.mean())

    flip_gaps = np.asarray(gaps)[top1_flip]
    if n_flips:
        gmin, gmed, gmax = float(flip_gaps.min()), float(np.median(flip_gaps)), float(flip_gaps.max())
    else:
        gmin = gmed = gmax = None
    within = beyond = None
    if tau is not None:
        if tau < 0:
            raise ValueError("tau must be >= 0")
        within = int((flip_gaps <= tau).sum())
        beyond = int((flip_gaps > tau).sum())

    # burstiness
    n_win = int(np.ceil(n / window))
    counts = np.array([top1_flip[i * window:(i + 1) * window].sum() for i in range(n_win)], dtype=np.float64)
    if n_win >= 2 and counts.mean() > 0:
        dispersion = float(counts.var(ddof=1) / counts.mean())
    else:
        dispersion = None
    longest = 0
    run = 0
    for f in top1_flip:
        run = run + 1 if f else 0
        longest = max(longest, run)

    return RankCensus(
        n_positions=n, vocab=int(vocab if vocab is not None else ref_top.shape[1]), ks=ks_eff,
        top1_flip_rate=float(top1_flip.mean()), top1_flips=n_flips,
        topk_set_flip_rate=set_rates, topk_order_flip_rate=order_rates,
        tau=tau, flip_gap_min=gmin, flip_gap_median=gmed, flip_gap_max=gmax,
        flips_within_tau=within, flips_beyond_tau=beyond,
        window=window, dispersion_index=dispersion, longest_flip_run=longest,
        max_abs_logit_delta=max_delta, p99_abs_logit_delta=p99_delta,
    )


def canonical_topk(idx: np.ndarray, val: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Re-sort a top-k dump into the codec's convention (value desc, index asc
    on ties). torch.topk is not tie-stable; fp16/int8 arms DO produce exact
    ties, and a tie-order difference is not a rank flip."""
    idx = np.asarray(idx); val = np.asarray(val, dtype=np.float64)
    if idx.shape != val.shape or idx.ndim != 2:
        raise ValueError("idx/val must be 2-D arrays of identical shape (positions, k)")
    order = np.lexsort((idx, -val), axis=1)
    return np.take_along_axis(idx, order, 1), np.take_along_axis(val, order, 1)


def aligned_delta(ref_idx, ref_val, alt_idx, alt_val) -> tuple[np.ndarray, float]:
    """|ref - alt| over reference top-k tokens that also appear in the alt dump
    (positions x k, NaN where absent) and the coverage fraction. Tokens that
    fall out of the alt top-k are a SET flip, reported separately — their
    value delta is unknowable from a dump."""
    n, k = ref_idx.shape
    delta = np.full((n, k), np.nan)
    for i in range(n):
        pos = {int(t): j for j, t in enumerate(alt_idx[i])}
        for j, t in enumerate(ref_idx[i]):
            m = pos.get(int(t))
            if m is not None:
                delta[i, j] = abs(ref_val[i, j] - alt_val[i, m])
    coverage = float(np.isfinite(delta).mean())
    return delta, coverage


def rank_census_topk(ref_idx, ref_val, alt_idx, alt_val, ks=(1, 8, 64), tau: float | None = None,
                     window: int = 64) -> RankCensus:
    """Same census as rank_census, from top-k DUMPS (positions, k) instead of
    full logits. ks are clipped to the dump width. Logit-delta stats are over
    aligned tokens only (see aligned_delta); `vocab` reports the dump width."""
    ref_idx, ref_val = canonical_topk(ref_idx, ref_val)
    alt_idx, alt_val = canonical_topk(alt_idx, alt_val)
    if ref_idx.shape != alt_idx.shape:
        raise ValueError(f"dumps differ in shape: {ref_idx.shape} vs {alt_idx.shape}")
    if not (np.all(np.isfinite(ref_val)) and np.all(np.isfinite(alt_val))):
        raise ValueError("dumps contain non-finite values")
    n, kd = ref_idx.shape
    if kd < 2:
        raise ValueError("need k >= 2 in the dump for a top-2 gap")
    if window < 1:
        raise ValueError("window must be >= 1")
    ks_eff = sorted({min(int(k), kd) for k in ks})
    if any(k < 1 for k in ks_eff):
        raise ValueError("ks must be >= 1")
    gaps = ref_val[:, 0] - ref_val[:, 1]
    delta, coverage = aligned_delta(ref_idx, ref_val, alt_idx, alt_val)
    finite = delta[np.isfinite(delta)]
    c = _census_core(ref_idx, alt_idx, gaps, ks_eff, tau, window,
                     max_delta=float(finite.max()) if finite.size else float("nan"),
                     p99_delta=float(np.percentile(finite, 99)) if finite.size else float("nan"))
    c.vocab = kd
    c.delta_coverage = coverage
    return c


def calibrate_tau_topk(ref_idx, ref_val, benign_idx, benign_val, quantile: float = 0.999) -> float:
    ref_idx, ref_val = canonical_topk(ref_idx, ref_val)
    benign_idx, benign_val = canonical_topk(benign_idx, benign_val)
    if not (0 < quantile <= 1):
        raise ValueError("quantile must be in (0, 1]")
    delta, _ = aligned_delta(ref_idx, ref_val, benign_idx, benign_val)
    finite = delta[np.isfinite(delta)]
    if finite.size == 0:
        raise ValueError("no aligned tokens between reference and benign dumps")
    return float(np.quantile(finite, quantile))


def calibrate_tau(ref_logits, benign_logits, quantile: float = 0.999) -> float:
    """Calibrated tolerance (eot TP-10 / XB-3 rule 1): the tail of the
    per-logit |delta| distribution under a BENIGN perturbation (same rows in a
    different batch composition, a second identical run, ...). A top-1 flip
    whose reference top-2 gap exceeds ~2*tau cannot be explained by that
    perturbation and is a bug, not drift."""
    ref, ben = _validate_pair(ref_logits, benign_logits)
    if not (0 < quantile <= 1):
        raise ValueError("quantile must be in (0, 1]")
    return float(np.quantile(np.abs(ref - ben), quantile))

"""K-3 Attempt #1 adaptive-block-scheduling machinery (pure numpy).

Implements the registered actuator (docs/BLUEPRINT.md, PHASE-4 K-3
ATTEMPT #1 ARC REGISTRATION 2026-09-01; D2/D3 FREEZE PINS 2026-09-02;
STAGE-E ENGINEERING CLARIFICATIONS E1-E11 2026-09-02). The GPU loop
(sideband.real.hf_specdec) consults this module for every STOP/EXTEND
decision; everything here is deterministic and consumes no RNG (the
E8 read-only constraint is structural).

Design facts this module encodes (see the registration for rationale):
- STOP consults exist at drafted positions 1-2 only (offsets 2-3 from
  the block anchor); positions >= 3 ride uninterrupted.
- EXTEND is a single per-block decision after base drafting completes,
  raising the block's draft budget from gamma_base=4 to gamma_max=6.
  STOP and EXTEND are mutually exclusive by construction.
- Probe arms (E2): a comparison is DEFINED only when both the probe's
  full-label-space argmax and the draft token's class are CONCEPT
  classes (glue/unbucketed merged class excluded, D-7). STOP =
  defined AND differs AND conf >= per-offset threshold; EXTEND =
  defined AND equal at BOTH offsets AND min conf >= threshold.
- Draft-confidence arm (E3): signal_j = q_j(x_j); STOP fires on LOW
  signal (<= threshold), EXTEND on high min (>= threshold) — the
  direction inversion vs the probe arms is the registered analog.
- Thresholds are quantile LEVELS materialized per consult position on
  the vanilla val run's block-start signal distributions (freeze pin
  1 + E5), np.quantile linear interpolation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .probes import slots_multi_hot

GAMMA_BASE = 4
GAMMA_MAX = 6
STOP_POSITIONS = (1, 2)  # 1-based drafted positions = offsets 2-3
# The pinned threshold grid recipe (Amendment #1): quantile levels.
QUANTILE_LEVELS = tuple(round(0.05 * k, 2) for k in range(1, 20))  # 0.05..0.95
MASS_KEYS = ("mass16", "mass32", "mass64", "mass512")
TOP_M = 32


@dataclass(frozen=True)
class Thresholds:
    """One (stop_level, extend_level) point of the pinned 2-D grid,
    materialized (E5): stop[j-1] = quantile(stop_level) of consult
    position j's own val signal distribution; extend =
    quantile(extend_level) of the val distribution of the per-block
    min over the two positions."""

    kind: str  # "probe" | "draft_conf" | "head" (OQ-15 Stage C: stop on
    #            S_1/S_2 quantiles, extend on the S_4*a_hat_5 quantile —
    #            grids built driver-side from the exported heads)
    stop_level: float
    extend_level: float
    stop: tuple[float, float]
    extend: float


def materialize_thresholds(kind: str, stop_level: float, extend_level: float,
                           sig1, sig2) -> Thresholds:
    """sig1/sig2: PAIRED per-block block-start signal samples for consult
    positions 1/2 from the vanilla-arm val run (E5; probe arms:
    conf_off2/conf_off3, arm 2: q_1(x_1)/q_2(x_2)). Pairing is required
    because the extend threshold lives on the distribution of the
    per-block min. np.quantile default (linear) interpolation, pinned."""
    if kind not in ("probe", "draft_conf"):
        raise ValueError(f"unknown threshold kind {kind!r}")
    s1 = np.asarray(sig1, dtype=np.float64)
    s2 = np.asarray(sig2, dtype=np.float64)
    if s1.ndim != 1 or s1.shape != s2.shape or s1.size == 0:
        raise ValueError("sig1/sig2 must be equal-length non-empty 1-D paired arrays")
    for lv in (stop_level, extend_level):
        if not 0.0 < lv < 1.0:
            raise ValueError(f"quantile level {lv} outside (0, 1)")
    return Thresholds(
        kind=kind, stop_level=float(stop_level), extend_level=float(extend_level),
        stop=(float(np.quantile(s1, stop_level)), float(np.quantile(s2, stop_level))),
        extend=float(np.quantile(np.minimum(s1, s2), extend_level)),
    )


class SchedulerPolicy:
    """Arm-level policy consulted by the spec-decode loop.

    kind "fixed": never stops or extends — arms 1 (gamma_base=4) and 5
    (gamma_base=6, the descriptive always-6 control runs as fixed with
    gamma_base=6). kind "draft_conf": arm 2 (E3). kind "probe": arms 3
    ((a), probe_arm="a") and 4 ((c), probe_arm="c"); needs glue_class
    (the merged glue/unbucketed label class, E2)."""

    def __init__(self, kind: str, gamma_base: int = GAMMA_BASE,
                 gamma_max: int = GAMMA_MAX, thresholds: Thresholds | None = None,
                 probe_arm: str | None = None, glue_class: int | None = None):
        if kind not in ("fixed", "draft_conf", "probe", "head"):
            raise ValueError(f"unknown policy kind {kind!r}")
        if kind == "fixed":
            if thresholds is not None:
                raise ValueError("fixed policy takes no thresholds")
        else:
            if thresholds is None or thresholds.kind != kind:
                raise ValueError(f"{kind} policy needs matching thresholds")
        if kind == "probe":
            if probe_arm not in ("a", "c") or glue_class is None:
                raise ValueError("probe policy needs probe_arm in {'a','c'} and glue_class")
        elif probe_arm is not None:
            raise ValueError("probe_arm is only meaningful for kind='probe'")
        if gamma_base < 1 or gamma_max < gamma_base:
            raise ValueError("need 1 <= gamma_base <= gamma_max")
        self.kind = kind
        self.gamma_base = int(gamma_base)
        self.gamma_max = int(gamma_max)
        self.thresholds = thresholds
        self.probe_arm = probe_arm
        self.glue_class = None if glue_class is None else int(glue_class)

    # -- consults ----------------------------------------------------------
    def stop_at(self, j: int, *, q_signal: float | None = None,
                probe_pred: int | None = None, probe_conf: float | None = None,
                draft_class: int | None = None,
                head_score: float | None = None) -> bool:
        """STOP consult at 1-based drafted position j (positions 1-2 only).
        head_score (kind 'head', OQ-15 STAGE-C FREEZE): the running
        predicted-survival product S_j; STOP fires iff S_j < stop[j-1]
        (strict, as registered — low predicted survival stops)."""
        if self.kind == "fixed" or j not in STOP_POSITIONS:
            return False
        if self.kind == "draft_conf":
            if q_signal is None:
                raise ValueError("draft_conf stop consult needs q_signal")
            return bool(q_signal <= self.thresholds.stop[j - 1])
        if self.kind == "head":
            if head_score is None:
                raise ValueError("head stop consult needs head_score")
            return bool(head_score < self.thresholds.stop[j - 1])
        if probe_pred is None or probe_conf is None or draft_class is None:
            raise ValueError("probe stop consult needs probe_pred/probe_conf/draft_class")
        if probe_pred == self.glue_class or draft_class == self.glue_class:
            return False  # undefined comparison (E2): neither STOP nor EXTEND
        return bool(probe_pred != draft_class
                    and probe_conf >= self.thresholds.stop[j - 1])

    def extend(self, *, q_signals=None, probe_preds=None, probe_confs=None,
               draft_classes=None, head_score: float | None = None) -> bool:
        """EXTEND consult (E4): one decision per block, after base drafting.
        Inputs are the two consult positions' values, in position order.
        head_score (kind 'head'): S_4 * a_hat_5; EXTEND fires iff >=
        threshold (high predicted survival extends)."""
        if self.kind == "fixed" or self.gamma_max <= self.gamma_base:
            return False
        if self.kind == "draft_conf":
            if q_signals is None or len(q_signals) != 2:
                raise ValueError("draft_conf extend consult needs both q_signals")
            return bool(min(q_signals) >= self.thresholds.extend)
        if self.kind == "head":
            if head_score is None:
                raise ValueError("head extend consult needs head_score")
            return bool(head_score >= self.thresholds.extend)
        if any(v is None or len(v) != 2 for v in (probe_preds, probe_confs, draft_classes)):
            raise ValueError("probe extend consult needs both positions' preds/confs/classes")
        for i in (0, 1):
            if (probe_preds[i] == self.glue_class
                    or draft_classes[i] == self.glue_class
                    or probe_preds[i] != draft_classes[i]):
                return False  # not a defined agreement at this offset (E2)
        return bool(min(probe_confs) >= self.thresholds.extend)


# ---------------------------------------------------------------------------
# Anchor feature assembly + probe inference (E7): live features must mirror
# the harvest dtypes exactly before probe input, in feature_blocks order.
# ---------------------------------------------------------------------------

def anchor_free_summaries(p: np.ndarray, bucket_maps: dict[str, np.ndarray],
                          top_m: int = TOP_M) -> dict:
    """Harvest-dtype free summaries of the anchor distribution p (E7):
    mass{16,32,64,512} float16, entropy float32, argmax int32, top-m ids
    int32 + probs float16 sorted descending, zero-padded to top_m (the
    harvest_batch layout). bucket_maps: {"16": full-coverage int map, ...}."""
    p = np.asarray(p, dtype=np.float64)
    out: dict = {}
    for name in ("16", "32", "64", "512"):
        bm = bucket_maps[name]
        n = int(bm.max()) + 1
        out[f"mass{name}"] = np.bincount(bm, weights=p, minlength=n).astype(np.float16)
    out["entropy"] = np.float32(-np.sum(np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0)))
    k = min(top_m, p.shape[0])
    order = np.argsort(-p, kind="stable")[:k]
    top_ids = np.zeros(top_m, dtype=np.int32)
    top_p = np.zeros(top_m, dtype=np.float16)
    top_ids[:k] = order.astype(np.int32)
    top_p[:k] = p[order].astype(np.float16)
    out["top_ids"] = top_ids
    out["top_p"] = top_p
    out["argmax"] = np.int32(order[0])
    return out


def probe_input(summaries: dict, slots: np.ndarray | None = None,
                n_slots: int = 512) -> np.ndarray:
    """float32 probe input vector in the feature_blocks order (E7):
    mass16, mass32, mass64, mass512, entropy, top_p [, slots multi-hot].
    slots: (L, top_n) int16 sorted-unique -1-padded (the (c) arm)."""
    parts = [np.asarray(summaries[key], dtype=np.float32).ravel() for key in MASS_KEYS]
    parts.append(np.asarray([summaries["entropy"]], dtype=np.float32))
    parts.append(np.asarray(summaries["top_p"], dtype=np.float32).ravel())
    if slots is not None:
        parts.append(slots_multi_hot(np.asarray(slots)[None, ...], n_slots)[0])
    return np.concatenate(parts)


# ---------------------------------------------------------------------------
# Threshold search (THRESHOLD-SEARCH REGISTRATION, 2026-09-02): the pinned
# deterministic frontier procedure, as pure functions over an eval oracle so
# the GPU driver carries no search logic of its own. eval_fn(stop_idx,
# ext_idx) -> dict with at least {"budget", "tokens_per_call"}; the driver
# caches evals, so repeated calls are lookups (every selected point is
# thereby backed by an actual eval — the registered no-interpolation rule).
# ---------------------------------------------------------------------------

def _min_feasible_extend(eval_fn, stop_idx: int, n_levels: int,
                         b_ref: float, warm_start: int | None) -> int | None:
    """Minimal feasible extend-level index at one stop level, by the
    registered warm-start + bisection on REALIZED budget (assumed
    nonincreasing in the extend level; a noise-broken assumption
    under-optimizes, never fabricates feasibility — the terminal
    candidate is always verified by its own eval). None = excluded."""
    def feasible(e: int) -> bool:
        return eval_fn(stop_idx, e)["budget"] <= b_ref

    lo, hi = 0, n_levels - 1
    if warm_start is not None:
        if feasible(warm_start):
            lo, hi = 0, warm_start
        elif warm_start == n_levels - 1:
            return None  # nothing above the warm start to search
        else:
            lo, hi = warm_start + 1, n_levels - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo if feasible(lo) else None


def search_frontier(eval_fn, n_levels: int = len(QUANTILE_LEVELS),
                    b_ref: float = None) -> dict:
    """Walk the 19 stop levels in ascending order; per level find the
    minimal feasible extend level (warm-started from the previous
    level's answer). Returns {"frontier": {stop_idx: ext_idx},
    "excluded": [stop_idx, ...]}."""
    if b_ref is None or b_ref <= 0:
        raise ValueError("search needs a positive frozen B_ref")
    frontier: dict[int, int] = {}
    excluded: list[int] = []
    warm: int | None = None
    for s in range(n_levels):
        e = _min_feasible_extend(eval_fn, s, n_levels, b_ref, warm)
        if e is None:
            excluded.append(s)
        else:
            frontier[s] = e
            warm = e
    return {"frontier": frontier, "excluded": excluded}


def select_thresholds(eval_fn, frontier: dict[int, int], b_ref: float) -> dict:
    """The registered selection over the evaluated frontier points:
    maximize val tokens/call; ties -> lower realized budget (Amendment
    #1); residual exact-float ties -> lower stop level, then lower
    extend level (the registration's completion). Asserts at selection
    time that the chosen pair's LOGGED eval is feasible (driver-gate
    carry #1). Empty frontier -> FAILED_INFEASIBLE marker; the caller
    applies the registered comparability-fallback corner."""
    if not frontier:
        return {"label": "FAILED_INFEASIBLE"}
    rows = []
    for s, e in sorted(frontier.items()):
        r = eval_fn(s, e)
        rows.append((r["tokens_per_call"], -r["budget"], -s, -e, s, e, r))
    rows.sort(reverse=True)
    _, _, _, _, s, e, r = rows[0]
    if not r["budget"] <= b_ref:  # the registered machine-check
        raise AssertionError(
            f"selected point ({s},{e}) has logged budget {r['budget']} > "
            f"B_ref {b_ref} — frontier bookkeeping is broken")
    return {"label": "SELECTED", "stop_idx": s, "extend_idx": e,
            "stop_level": QUANTILE_LEVELS[s] if s < len(QUANTILE_LEVELS) else None,
            "extend_level": QUANTILE_LEVELS[e] if e < len(QUANTILE_LEVELS) else None,
            "tokens_per_call": r["tokens_per_call"], "budget": r["budget"]}


class LinearProbe:
    """An exported committed Phase-3 linear cell (E1), applied per anchor:
    float32 logits -> float64 softmax (train_probe full_eval semantics,
    E7). Returns (argmax class, max softmax) — the frozen confidence
    signal is the max softmax over the FULL label space."""

    def __init__(self, W: np.ndarray, b: np.ndarray):
        self.W = np.asarray(W, dtype=np.float32)
        self.b = np.asarray(b, dtype=np.float32)
        if self.W.ndim != 2 or self.b.shape != (self.W.shape[0],):
            raise ValueError(f"bad probe shapes W{self.W.shape} b{self.b.shape}")

    @property
    def n_classes(self) -> int:
        return int(self.W.shape[0])

    @property
    def dim(self) -> int:
        return int(self.W.shape[1])

    def __call__(self, x: np.ndarray) -> tuple[int, float]:
        x = np.asarray(x, dtype=np.float32)
        if x.shape != (self.dim,):
            raise ValueError(f"probe input dim {x.shape} != ({self.dim},)")
        logits = (self.W @ x + self.b).astype(np.float64)
        z = np.exp(logits - logits.max())
        post = z / z.sum()
        return int(np.argmax(post)), float(post.max())

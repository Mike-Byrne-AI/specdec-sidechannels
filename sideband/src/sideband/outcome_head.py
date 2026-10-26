"""OQ-15 Stage-I machinery (FOLD-BACK #1 ARC REGISTRATION, BLUEPRINT
2026-09-03): sha-verified byproduct loading, feature assembly THROUGH the
committed scheduler.probe_input (never re-implemented — D-3), the F-16
alignment-destroying slot shift, closed-form ridge heads, and the pooled
squared-error aggregation that stats.paired_cluster_delta_ci consumes.

CPU-only; no torch. Deterministic: the only RNG is the pinned split
permutation (SPLIT_SEED); ridge is a float64 closed form with no
training seed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .scheduler import probe_input

SPLIT_SEED = 15          # registered: default_rng(15).permutation(N)
TRAIN_FRAC, VAL_FRAC = 0.6, 0.2   # 126/42/42 at the registered N=210
NOISE_SHIFT = 17         # F-16's recipe: block b reads block (b+17) mod n
LAMBDA_GRID = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
GATE_OFFSETS = (1, 2, 3, 4)      # the on-policy gamma-4 schedule
FEATURE_SETS = ("free", "tel", "noise")
N_SLOTS = 512
SUMMARY_KEYS = ("mass16", "mass32", "mass64", "mass512",
                "entropy", "argmax", "top_ids", "top_p")


def stage1_split(n_prompts: int) -> dict[str, np.ndarray]:
    """Registered prompt-level split: TRAIN/VAL/TEST = 60/20/20 of the
    permuted prompt indices (126/42/42 at the registered N=210). Both
    seed-runs of a prompt share its split by construction (the split is
    over prompt ids, not rows)."""
    perm = np.random.default_rng(SPLIT_SEED).permutation(n_prompts)
    n_tr = int(n_prompts * TRAIN_FRAC)
    n_va = int(n_prompts * VAL_FRAC)
    return {"train": perm[:n_tr], "val": perm[n_tr:n_tr + n_va],
            "test": perm[n_tr + n_va:]}


def verify_byproduct(byp_dir: Path, summary_path: Path) -> list[Path]:
    """The registered binding: every npz's sha256 must match the committed
    run summary's byproduct_sha256 map. Refuses on any mismatch, missing
    file, or unlisted extra. Returns files sorted by name (= p-index
    order for the zero-padded p{i:03d} names)."""
    want = json.loads(summary_path.read_text())["byproduct_sha256"]
    have = {f.name: f for f in byp_dir.glob("p*.npz")}
    if set(have) != set(want):
        raise SystemExit(f"byproduct set mismatch under {byp_dir}: "
                         f"missing={sorted(set(want) - set(have))[:3]} "
                         f"extra={sorted(set(have) - set(want))[:3]}")
    out = []
    for name in sorted(want):
        got = hashlib.sha256(have[name].read_bytes()).hexdigest()
        if got != want[name]:
            raise SystemExit(f"sha256 mismatch for {byp_dir / name}: "
                             f"summary {want[name][:12]}.. file {got[:12]}..")
        out.append(have[name])
    return out


def prompt_index_map(gen_path: Path) -> dict[int, int]:
    """p-index -> orig_prompt_idx from the run's gen sidecar (the cluster
    key; identity for full-population runs, but never assumed)."""
    out: dict[int, int] = {}
    for line in gen_path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out[int(row["prompt_idx"])] = int(row["orig_prompt_idx"])
    return out


def noise_shift_index(n_blocks: int) -> np.ndarray:
    """F-16's alignment destruction within a prompt-run: block b takes
    block (b+17) mod n_blocks's slot vector."""
    return (np.arange(n_blocks) + NOISE_SHIFT) % n_blocks


def noise_self_maps(n_blocks: int) -> bool:
    """The disclosed sliver: the shift is the identity iff n_blocks
    divides NOISE_SHIFT (n_blocks in {1, 17})."""
    return n_blocks >= 1 and NOISE_SHIFT % n_blocks == 0


def block_core_features(z: dict, feature_set: str,
                        n_slots: int = N_SLOTS) -> np.ndarray:
    """(n_blocks, dims) float64 core features, one probe_input call per
    block — the committed assembler is the assembler. free -> 657 dims;
    tel/noise -> 657 + 4*n_slots (free + slots multi-hot; noise uses the
    shifted slot rows). q_sig is appended separately (per-offset
    availability). n_slots is a test-sizing knob only — the registered
    run uses the default 512 and records the value used in its meta."""
    if feature_set not in FEATURE_SETS:
        raise ValueError(f"unknown feature set {feature_set!r}")
    n = int(np.asarray(z["gamma_used"]).shape[0])
    slot_rows = None
    if feature_set == "tel":
        slot_rows = np.asarray(z["slots"])
    elif feature_set == "noise":
        slot_rows = np.asarray(z["slots"])[noise_shift_index(n)]
    rows = []
    for b in range(n):
        summ = {k: np.asarray(z[k])[b] for k in SUMMARY_KEYS}
        if slot_rows is None:
            rows.append(probe_input(summ))
        else:
            rows.append(probe_input(summ, slots=slot_rows[b], n_slots=n_slots))
    return np.stack(rows).astype(np.float64)


def qsig_cols(z: dict, offset: int) -> np.ndarray:
    """The registered availability rule: offset j sees q_sig[0:min(j,2)]
    (q_sig[k] = q(x_{k+1}), known pre-verify once position k+1 is
    drafted). Refuses NaN — the fixed-schedule runs always draft both
    consult positions, so a NaN is a data-contract violation."""
    k = min(int(offset), 2)
    q = np.asarray(z["q_sig"], dtype=np.float64)[:, :k]
    if np.isnan(q).any():
        raise SystemExit("NaN q_sig in a fixed-schedule byproduct row")
    return q


def offset_rows(z: dict, offset: int) -> np.ndarray:
    """Boolean mask of blocks whose drafted range reaches this offset."""
    return np.asarray(z["gamma_used"]).astype(np.int64) >= int(offset)


def analytic_target(z: dict, offset: int) -> np.ndarray:
    """Primary regression target at the masked rows: analytic acceptance
    1 - TV(p_j, q_j), in [0,1], never survival-conditioned."""
    m = offset_rows(z, offset)
    y = np.asarray(z["analytic"], dtype=np.float64)[m, int(offset) - 1]
    if np.isnan(y).any():
        raise SystemExit("NaN analytic inside the drafted range")
    return y


def binary_target(z: dict, offset: int) -> tuple[np.ndarray, np.ndarray]:
    """(mask, labels) for the REPORTED classification variant: accept
    flag on REACHED positions only (acc_flags >= 0) — survival-
    conditioned by construction, labeled per D-9."""
    flags = np.asarray(z["acc_flags"])[:, int(offset) - 1]
    m = flags >= 0
    return m, flags[m].astype(np.float64)


@dataclass
class Standardizer:
    mu: np.ndarray
    sd: np.ndarray   # zero-variance features carry sd=1 -> standardized 0

    @classmethod
    def from_moments(cls, s1: np.ndarray, s2: np.ndarray, n: int) -> "Standardizer":
        mu = s1 / n
        var = np.maximum(s2 / n - mu * mu, 0.0)
        sd = np.sqrt(var)
        sd[sd == 0.0] = 1.0
        return cls(mu=mu, sd=sd)

    def apply(self, x: np.ndarray) -> np.ndarray:
        return (np.asarray(x, dtype=np.float64) - self.mu) / self.sd


def ridge_fit(gram: np.ndarray, xty: np.ndarray, lam: float) -> np.ndarray:
    """Closed-form ridge on the augmented design [1, X_std]: solve
    (G + lam * D) w = X^T y with D = diag(0, 1, ..., 1) — the intercept
    is unpenalized. gram/xty are accumulated over standardized rows."""
    d = np.eye(gram.shape[0])
    d[0, 0] = 0.0
    return np.linalg.solve(gram + float(lam) * d, xty)


def augment(x_std: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((x_std.shape[0], 1)), x_std])


def predict_clipped(w: np.ndarray, x_std: np.ndarray) -> np.ndarray:
    """Predictions clipped to [0,1] (registered: keeps per-position
    squared error <= 1, the paired_cluster_delta_ci validity condition)."""
    return np.clip(augment(x_std) @ w, 0.0, 1.0)


class HeadScorer:
    """Frozen Stage-I/Stage-C ridge heads for live scoring (STAGE-C
    FREEZE, BLUEPRINT 2026-09-03). One family ('free' or 'tel'),
    offsets 1-5. a_hat_i = clip([1, (x - mu_i)/sd_i] @ w_i, 0, 1) in
    float64 with x = core ++ q_sig[0:min(i,2)] — bit-matching the
    training pipeline's Standardizer.apply + predict_clipped, asserted
    by the export self-check."""

    OFFSETS = (1, 2, 3, 4, 5)

    def __init__(self, npz_path, family: str):
        if family not in ("free", "tel"):
            raise ValueError(f"unknown head family {family!r}")
        self.family = family
        self.npz_path = str(npz_path)
        z = np.load(npz_path)
        self.params: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for off in self.OFFSETS:
            try:
                mu = z[f"{family}_off{off}_mu"]
                sd = z[f"{family}_off{off}_sd"]
                w = z[f"{family}_off{off}_w"]
            except KeyError as e:
                raise ValueError(f"{npz_path} missing head {family}_off{off}") from e
            if w.shape[0] != mu.shape[0] + 1 or mu.shape != sd.shape:
                raise ValueError(f"inconsistent shapes for {family}_off{off}")
            self.params[off] = (mu.astype(np.float64), sd.astype(np.float64),
                                w.astype(np.float64))

    def a_hat(self, core: np.ndarray, q_sigs, offset: int) -> float:
        """Predicted analytic acceptance at 1-based drafted offset,
        given the anchor core vector and the q_sigs drafted SO FAR
        (the registered availability rule: offset i consumes
        q_sig[0:min(i,2)], all drafted by any decision point that
        needs a_hat_i)."""
        k = min(int(offset), 2)
        if len(q_sigs) < k:
            raise ValueError(f"offset {offset} needs {k} q_sigs, have {len(q_sigs)}")
        mu, sd, w = self.params[int(offset)]
        x = np.concatenate([np.asarray(core, dtype=np.float64),
                            np.asarray(q_sigs[:k], dtype=np.float64)])
        if x.shape[0] != mu.shape[0]:
            raise ValueError(f"feature dim {x.shape[0]} != head dim {mu.shape[0]} "
                             f"({self.family}_off{offset})")
        # the EXACT training-pipeline op (predict_clipped on a 1-row
        # batch) — a scalar w[0] + xs@w[1:] form sums in a different
        # order and breaks the export self-check's bit-equality
        xs = ((x - mu) / sd)[None, :]
        return float(predict_clipped(w, xs)[0])

    def survival(self, core: np.ndarray, q_sigs, upto: int) -> float:
        """S_j = product of a_hat_1..a_hat_j (the registered
        independence approximation)."""
        s = 1.0
        for i in range(1, int(upto) + 1):
            s *= self.a_hat(core, q_sigs, i)
        return s


def auc_score(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank AUC with midranks for ties (scipy-free)."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.float64)
    n_pos = float(labels.sum())
    n_neg = float(len(labels) - labels.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="stable")
    ranks = np.empty(len(scores), dtype=np.float64)
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return float((ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2.0)
                 / (n_pos * n_neg))


def precision_at_coverage(scores: np.ndarray, labels: np.ndarray,
                          coverage: float = 0.20) -> tuple[float, float]:
    """(precision, realized_coverage) selecting scores >= the
    (1-coverage) quantile — ties are all included, so realized coverage
    can exceed the nominal (reported alongside, the D2 convention)."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.float64)
    thr = np.quantile(scores, 1.0 - coverage)
    sel = scores >= thr
    if not sel.any():
        return float("nan"), 0.0
    return float(labels[sel].mean()), float(sel.mean())

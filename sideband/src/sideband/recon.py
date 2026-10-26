"""OQ-16 Stage-R machinery (FOLD-BACK #2 ARC REGISTRATION, BLUEPRINT
2026-09-04): multi-output ridge reconstruction of the anchor hidden state
h_a from anchor-time features, the two-leg gate (existence vs the
alignment-destroyed twin AND deployability vs free features), and the
GATING five-seed stale-target control.

Shares the committed Stage-I primitives (sha-verified loading, feature
assembly through scheduler.probe_input, Standardizer, ridge_fit) by
import — never re-implemented (D-3). CPU-only; no torch. Deterministic:
the only RNGs are the pinned split permutation (outcome_head.SPLIT_SEED)
and the pinned stale-target permutations below.
"""

from __future__ import annotations

import numpy as np

from .outcome_head import (  # noqa: F401  (re-exported for the tool/tests)
    Standardizer,
    augment,
    block_core_features,
    noise_self_maps,
    prompt_index_map,
    ridge_fit,
    stage1_split,
    verify_byproduct,
)

# Registered constants (OQ-16 arc registration, 2026-09-04).
RECON_LAMBDA_GRID = (1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3, 1e4, 1e5)
STALE_SEEDS = (0, 1, 2, 3, 4)
H_DIM = 4096
N_PROMPTS_PER_POP = 210
# run_index order 0..3 is the stale-control RNG binding — pinned.
RECON_RUNS = (
    {"stem": "k3_verdict_arm1", "pop": "k3"},
    {"stem": "k3_verdict_s1_arm1", "pop": "k3"},
    {"stem": "oq15c_verdict_arm1", "pop": "oq15"},
    {"stem": "oq15c_verdict_s3_arm1", "pop": "oq15"},
)
FEATURE_SETS = ("free", "tel", "noise")
PASS_LABEL = "STAGE-R PASS"
CEILING_LABEL = "RECONSTRUCTION-CEILING NULL"
DILUTION_LABEL = "RECONSTRUCTION-DILUTION NULL"

# DR-1 / DR-2 post-gate diagnostics (BLUEPRINT 2026-09-04, registered
# after the Stage-R gate was read; NON-CRITERION). FREETOK = free core ++
# a 2048-dim multi-hot of the anchor's top-32 next-token ids hashed by
# id mod FREETOK_BINS — equal dims to TEL, deployment-free information.
FREETOK_ARM = "freetok"
FREETOK_BINS = 2048
TRIVIAL_ARM = "trivial"
DR1_CONFIRMED = "DEPLOYABLE-MARGIN CONFIRMED"
DR1_NOT_CONFIRMED = "DEPLOYABLE-MARGIN NOT CONFIRMED"
DR2_ABOVE_TOKEN = "TELEMETRY-ABOVE-TOKEN"
DR2_NOT_EXCLUDED = "TOKEN-IDENTITY-NOT-EXCLUDED"
# DR-3 (BLUEPRINT 2026-09-04, registered after DR-2 was read): does
# telemetry add anything ON TOP of p? UNION = TEL ++ TOK (4753 dims);
# UNIONNOISE = NOISE ++ TOK, the equal-dims alignment-destroyed anchor
# for the slot block inside the union.
UNION_ARM = "union"
UNION_NOISE_ARM = "unionnoise"
DR3_BEYOND = "TELEMETRY-BEYOND-P"
DR3_NOT_BEYOND = "TELEMETRY-NOT-BEYOND-P"
# DR-4 (BLUEPRINT 2026-09-04, registered after DR-3 was read; NON-
# CRITERION): the equal-dims BETTER-token-encoding comparator for the
# union. FREETOK2 = FREE ++ TOK_A (the DR-2 multi-hot, id mod 2048) ++
# TOK_B (2048 bins under a salted multiplicative hash; bin VALUE = the
# token's top_p, so the value-to-id pairing the multi-hot loses is
# carried; within-row collisions sum) = 4753 dims, UNION's dims.
FREETOK2_ARM = "freetok2"
TOKB_MULT = 2654435761          # Knuth's multiplicative constant (2^32/phi)
TOKB_SALT = 0x9E3779B9
TOKB_SHIFT = 21                 # top 11 of 32 bits -> 2048 bins
DR4_CONFIRMED = "BEYOND-P CONFIRMED"
DR4_REDUCES = "REDUCES-TO-ENCODING"
DR4_TOOTHLESS = "COMPARATOR-TOOTHLESS"


def tok_block(z: dict, n_bins: int = FREETOK_BINS) -> np.ndarray:
    """(n_blocks, n_bins) multi-hot of hashed top-32 next-token ids
    (id mod n_bins; negative/padding ids ignored)."""
    ids = np.asarray(z["top_ids"], dtype=np.int64)
    n = int(np.asarray(z["gamma_used"]).shape[0])
    if ids.ndim != 2 or ids.shape[0] != n:
        raise SystemExit("top_ids shape does not match the block count")
    tok = np.zeros((n, n_bins), dtype=np.float64)
    for b in range(n):
        row = ids[b]
        row = row[row >= 0]
        if row.size:
            tok[b, np.unique(row % n_bins)] = 1.0
    return tok


def freetok_features(z: dict, n_slots: int = 512,
                     n_bins: int = FREETOK_BINS) -> np.ndarray:
    """(n_blocks, 657 + n_bins) float64: the free core (through the
    committed assembler) ++ tok_block. The DR-2 arm."""
    core = block_core_features(z, "free", n_slots=n_slots)
    return np.hstack([core, tok_block(z, n_bins)])


def tokb_bins(ids: np.ndarray, n_bins: int = FREETOK_BINS) -> np.ndarray:
    """Salted multiplicative hash of token ids -> [0, n_bins): the top
    bits of (id * TOKB_MULT + TOKB_SALT) mod 2^32 (Fibonacci hashing).
    Deliberately NOT id mod n_bins: the two hashes give the linear
    readout two different collision patterns per id."""
    u = (np.asarray(ids, dtype=np.uint64) * np.uint64(TOKB_MULT)
         + np.uint64(TOKB_SALT)) & np.uint64(0xFFFFFFFF)
    return ((u >> np.uint64(TOKB_SHIFT)) % np.uint64(n_bins)).astype(np.int64)


def tokb_block(z: dict, n_bins: int = FREETOK_BINS) -> np.ndarray:
    """(n_blocks, n_bins) float64: bin value = the top-32 token's top_p
    (float16 log -> float64) at its salted-hash bin; within-row
    collisions sum; negative/padding ids ignored. The DR-4 block."""
    ids = np.asarray(z["top_ids"], dtype=np.int64)
    p = np.asarray(z["top_p"], dtype=np.float64)
    n = int(np.asarray(z["gamma_used"]).shape[0])
    if ids.ndim != 2 or ids.shape[0] != n or p.shape != ids.shape:
        raise SystemExit("top_ids/top_p shapes do not match the block count")
    out = np.zeros((n, n_bins), dtype=np.float64)
    for b in range(n):
        keep = ids[b] >= 0
        np.add.at(out[b], tokb_bins(ids[b][keep], n_bins), p[b][keep])
    return out


def freetok2_features(z: dict, n_slots: int = 512,
                      n_bins: int = FREETOK_BINS) -> np.ndarray:
    """(n_blocks, 657 + 2*n_bins) float64: FREETOK ++ tokb_block — the
    DR-4 comparator at UNION's dims."""
    return np.hstack([freetok_features(z, n_slots=n_slots, n_bins=n_bins),
                      tokb_block(z, n_bins)])


def dr4_label(union_vs_freetok2_pooled: tuple,
              freetok2_vs_freetok_pooled: tuple) -> str:
    """COMPARATOR-TOOTHLESS unless the better encoding beats FREETOK (CI
    lower > 0 — it must extract MORE of p, or it prices nothing); then
    BEYOND-P CONFIRMED iff the union beats it at equal dims (CI lower
    > 0), else REDUCES-TO-ENCODING."""
    if not freetok2_vs_freetok_pooled[1] > 0.0:
        return DR4_TOOTHLESS
    return (DR4_CONFIRMED if union_vs_freetok2_pooled[1] > 0.0
            else DR4_REDUCES)


def arm_features(z: dict, arm: str, n_slots: int = 512) -> np.ndarray:
    """Dispatch: the three registered arms go through the committed
    block_core_features; FREETOK through freetok_features; the DR-3
    union arms = the tel / noise cores ++ tok_block; the DR-4 FREETOK2
    = FREETOK ++ tokb_block."""
    if arm == FREETOK_ARM:
        return freetok_features(z, n_slots=n_slots)
    if arm == FREETOK2_ARM:
        return freetok2_features(z, n_slots=n_slots)
    if arm == UNION_ARM:
        return np.hstack([block_core_features(z, "tel", n_slots=n_slots),
                          tok_block(z)])
    if arm == UNION_NOISE_ARM:
        return np.hstack([block_core_features(z, "noise", n_slots=n_slots),
                          tok_block(z)])
    return block_core_features(z, arm, n_slots=n_slots)


def dr3_label(union_vs_freetok_pooled: tuple,
              union_vs_unionnoise_pooled: tuple) -> str:
    """TELEMETRY-BEYOND-P iff BOTH the union beats FREETOK (CI lower > 0)
    AND the union beats its alignment-destroyed anchor (CI lower > 0) —
    dilution-priced, block-aligned information on top of p."""
    ok = (union_vs_freetok_pooled[1] > 0.0
          and union_vs_unionnoise_pooled[1] > 0.0)
    return DR3_BEYOND if ok else DR3_NOT_BEYOND


def dr1_label(tel_vs_trivial: dict) -> str:
    """DEPLOYABLE-MARGIN CONFIRMED iff the pooled CI lower > 0 AND every
    per-population CI lower > 0 (tel_vs_trivial = {'pooled': (d, lo,
    hi), 'per_pop': {pop: (d, lo, hi)}})."""
    ok = tel_vs_trivial["pooled"][1] > 0.0 and all(
        v[1] > 0.0 for v in tel_vs_trivial["per_pop"].values())
    return DR1_CONFIRMED if ok else DR1_NOT_CONFIRMED


def dr2_label(tel_vs_freetok_pooled: tuple) -> str:
    """TELEMETRY-ABOVE-TOKEN iff the pooled tel_vs_freetok CI lower > 0."""
    return (DR2_ABOVE_TOKEN if tel_vs_freetok_pooled[1] > 0.0
            else DR2_NOT_EXCLUDED)


def h_target(z: dict) -> np.ndarray:
    """(n_blocks, h_dim) float64 target from the byproduct's h_a log
    (float16 on disk — the cast is part of the registered target).
    Refuses non-finite values: h_a is a norm output and a NaN/inf row is
    a data-contract violation, not something to impute around."""
    y = np.asarray(z["h"], dtype=np.float64)
    if y.ndim != 2:
        raise SystemExit("byproduct h is not 2-D")
    if not np.isfinite(y).all():
        raise SystemExit("non-finite h_a in a byproduct row")
    return y


def stale_perm(stale_seed: int, run_index: int, pid: int, n: int) -> np.ndarray:
    """The DI-1 permutation recipe verbatim: an isolated per-(seed, run,
    prompt) generator so the permutation is identical across passes.
    The split is prompt-level, so this maps TRAIN rows to TRAIN rows and
    VAL/TEST rows within their own role — the Gram-sharing precondition
    (asserted here, not assumed)."""
    perm = np.random.default_rng(
        stale_seed * 1_000_000 + run_index * 10_000 + pid
    ).permutation(n)
    assert perm.shape == (n,) and np.array_equal(np.sort(perm), np.arange(n))
    return perm


def centered_cosine_rows(pred_std: np.ndarray, y_std: np.ndarray) -> np.ndarray:
    """Per-block cosine between prediction and truth in standardized
    space (the train mean is the origin there, so this IS the
    mean-removed direction proxy — REPORTED, not gating). Zero-norm rows
    yield NaN; callers count them rather than dropping silently."""
    pn = np.linalg.norm(pred_std, axis=1)
    yn = np.linalg.norm(y_std, axis=1)
    denom = pn * yn
    out = np.full(pred_std.shape[0], np.nan)
    ok = denom > 0
    out[ok] = (pred_std[ok] * y_std[ok]).sum(axis=1) / denom[ok]
    return out


def stage_r_gate(live_noise: tuple, live_free: tuple,
                 stale_noise_points) -> dict:
    """The registered two-leg all-hold gate, mechanical.

    live_noise / live_free: (delta, lo, hi) from paired_ratio_delta_ci.
    stale_noise_points: the five stale-seed delta_noise points.

    Leg 1 (existence): delta_noise CI lower > 0 AND point >
    stale_mean + 3*stale_sd (ddof=1) AND point > max(stale points).
    Leg 2 (deployability): delta_free CI lower > 0. Straddles fail."""
    stales = np.asarray(stale_noise_points, dtype=np.float64)
    if stales.shape != (len(STALE_SEEDS),):
        raise SystemExit("gate needs exactly one stale point per seed")
    s_mean = float(stales.mean())
    s_sd = float(stales.std(ddof=1))
    s_max = float(stales.max())
    bar = s_mean + 3.0 * s_sd
    leg1 = {
        "ci_lower_positive": bool(live_noise[1] > 0.0),
        "above_3sd_bar": bool(live_noise[0] > bar),
        "above_stale_max": bool(live_noise[0] > s_max),
        "stale_mean": s_mean, "stale_sd": s_sd, "stale_max": s_max,
        "bar_3sd": bar,
    }
    leg1["holds"] = (leg1["ci_lower_positive"] and leg1["above_3sd_bar"]
                     and leg1["above_stale_max"])
    leg2 = {"ci_lower_positive": bool(live_free[1] > 0.0)}
    leg2["holds"] = leg2["ci_lower_positive"]
    if not leg1["holds"]:
        label = CEILING_LABEL
    elif not leg2["holds"]:
        label = DILUTION_LABEL
    else:
        label = PASS_LABEL
    return {"leg1": leg1, "leg2": leg2, "label": label}


# ---------------------------------------------------------------------------
# STAGE A — ACTUATOR (OQ-16 STAGE-A FREEZE, BLUEPRINT 2026-09-04): the
# CPU side of the SD^2-style injection. Everything here is numpy and
# tested; the torch side (sideband.real.steer_inject) consumes it and is
# asserted against adapter_forward_np on the GPU box.
# ---------------------------------------------------------------------------

# The block-emission arithmetic of hf_specdec.spec_decode_prompt (whole-
# block emission: accepted + 1 tokens per block — the residual or the
# bonus). Absolute token indices in the full id sequence (prompt first).
def block_token_spans(prompt_len: int, accepted) -> np.ndarray:
    """(n_blocks, 2) int64 [start, end] INCLUSIVE indices of each block's
    emitted tokens: block 0 starts at prompt_len; block b emits
    accepted[b] + 1 tokens; block b+1 starts right after."""
    acc = np.asarray(accepted, dtype=np.int64)
    if acc.ndim != 1 or (acc < 0).any():
        raise ValueError("accepted must be a 1-D non-negative array")
    spans = np.zeros((acc.shape[0], 2), dtype=np.int64)
    start = int(prompt_len)
    for b, a in enumerate(acc.tolist()):
        spans[b] = (start, start + a)
        start = start + a + 1
    return spans


def anchor_positions_from_spans(prompt_len: int, spans: np.ndarray) -> np.ndarray:
    """The byproduct's anchor_pos, recomputed: block 0 consults the
    prefill anchor at prompt_len - 1 (the prompt's last token); block
    b >= 1 consults the LAST VERIFIED row — the row whose input token is
    the previous block's last emitted token minus one, i.e. start_b - 2
    (hf_specdec: abs_pos = len(ids) - 2 after the append). Asserted
    against the logged anchor_pos by the data-assembly path — a
    data-contract check, never assumed."""
    n = spans.shape[0]
    out = np.empty(n, dtype=np.int64)
    if n == 0:
        return out
    out[0] = int(prompt_len) - 1
    out[1:] = spans[1:, 0] - 2
    return out


def guide_block_per_row(prompt_len: int, spans: np.ndarray, total_len: int
                        ) -> np.ndarray:
    """(total_len,) int64: for each INPUT row t (the drafter's row with
    input token t predicts token t+1), the block whose delta applies —
    rows start_b - 1 .. end_b - 1 belong to block b (its drafted rows,
    incl. the bonus row of a full-accept block, exactly the rows the
    drafter would run with that block's delta set); prompt rows before
    prompt_len - 1 and the final row (no target) are -1."""
    g = np.full(int(total_len), -1, dtype=np.int64)
    for b in range(spans.shape[0]):
        s, e = int(spans[b, 0]), int(spans[b, 1])
        if e >= total_len:
            raise ValueError("block span exceeds the sequence")
        g[s - 1:e] = b
    return g


def block_dict_from_anchor(summaries: dict, slots: np.ndarray) -> dict:
    """A one-block byproduct-shaped dict from a live AnchorRead's parts,
    so the live reconstruction runs through arm_features — the SAME
    assembler the export trained through (D-3 spirit; E7 dtypes are the
    reader's own)."""
    z = {k: np.asarray(v)[None, ...] for k, v in summaries.items()}
    z["slots"] = np.asarray(slots)[None, ...]
    z["gamma_used"] = np.zeros(1, dtype=np.int16)
    return z


class LiveReconstructor:
    """Frozen ridge reconstruction h_hat for one anchor (STAGE-A FREEZE
    export: results/real/oq16_recon_weights.npz). Arithmetic mirrors the
    training pipeline exactly: clip to TRAIN support, standardize
    (Standardizer.apply), augment, @ w, then un-standardize the target
    (t_mu + t_sd * pred). Float64 throughout; single-row gemv (the
    export self-check bounds its deviation from the batch path)."""

    def __init__(self, npz_path, arm: str, n_slots: int = 512):
        z = np.load(npz_path)
        self.arm = arm
        self.n_slots = int(n_slots)
        self.std = Standardizer(mu=z[f"{arm}_mu"], sd=z[f"{arm}_sd"])
        self.lo, self.hi = z[f"{arm}_lo"], z[f"{arm}_hi"]
        self.w = z[f"{arm}_w"]
        self.t_mu, self.t_sd = z["target_mu"], z["target_sd"]
        if self.w.shape[0] != self.std.mu.shape[0] + 1:
            raise ValueError("weights/moments dims disagree")

    def predict_std(self, x_raw: np.ndarray) -> np.ndarray:
        x = np.clip(np.asarray(x_raw, dtype=np.float64), self.lo, self.hi)
        return augment(self.std.apply(x)) @ self.w

    def reconstruct_rows(self, x_raw: np.ndarray) -> np.ndarray:
        """(n, h_dim) float64 in raw h units."""
        return self.t_mu + self.t_sd * self.predict_std(x_raw)

    def reconstruct(self, summaries: dict, slots: np.ndarray) -> np.ndarray:
        """(h_dim,) float64 for one live anchor."""
        z = block_dict_from_anchor(summaries, slots)
        x = arm_features(z, self.arm, n_slots=self.n_slots)
        return self.reconstruct_rows(x)[0]


def layer_norm_np(h: np.ndarray, weight: np.ndarray, bias: np.ndarray,
                  eps: float = 1e-5) -> np.ndarray:
    """torch.nn.LayerNorm semantics (biased variance) in float64."""
    h = np.asarray(h, dtype=np.float64)
    mu = h.mean(-1, keepdims=True)
    var = ((h - mu) ** 2).mean(-1, keepdims=True)
    return (h - mu) / np.sqrt(var + eps) * weight + bias


def adapter_forward_np(h: np.ndarray, ln_w: np.ndarray, ln_b: np.ndarray,
                       u: np.ndarray, v: np.ndarray, eps: float = 1e-5
                       ) -> np.ndarray:
    """The pinned injection adapter, reference arithmetic: delta[l] =
    (LayerNorm(h) @ u) @ v[l]  — u: (h_dim, r), v: (n_layers, r, d_ff).
    SD^2's zero-initialised linear map from the (normed) steering vector
    to one d_ff-dim bias per drafter layer, factorised through rank r
    (the box-memory deviation the freeze discloses). Returns (n_layers,
    d_ff). v starts at zero -> the adapter is a no-op until trained."""
    g = layer_norm_np(h, ln_w, ln_b, eps) @ np.asarray(u, dtype=np.float64)
    return np.einsum("r,lrf->lf", g, np.asarray(v, dtype=np.float64))

#!/usr/bin/env python
"""tools/run_prefetch_readouts.py — OQ-9 STAGE-1 PREFETCH READOUTS on the
committed S3 (OLMoE router) harvests.

Registered 2026-09-14 in docs/BLUEPRINT.md ("OQ-9 STAGE-1 PREFETCH READOUTS
REGISTRATION"); NON-CRITERION for every existing finding. CPU only; numpy
only — nothing in this file imports torch, so its tests run in CI.

Index convention (sideband.harvest): forward t has INPUT tokens[t-1], OUTPUT
p_t, routing S[t]; tokens[t] is sampled from p_t. At anchor t the decoder
holds S[t] (the address stream) and tokens[t] (the bonus token, free): S[t+1]
is the routing of the forward tokens[t] feeds; S[t+2] is the routing of the
forward the draft's first proposal feeds (stand-in: the true tokens[t+1], the
D-2 ceiling draft).

Arms (every arm of a horizon on IDENTICAL positions; readers fit on TRAIN
rows pooled over seeds, lambda selected on VAL, every reported number read
on the TEST prompts with prompt-cluster bootstrap CIs from sideband.stats):
  recency      the B most recently used distinct experts per gate — a cache
               policy, no fitting; B = 8 is self-reuse.            (i)
  marginal     the B most frequent experts per gate at the target positions.
  free_table   zero-fit: top-B of TABLE(tokens[t]) — the train conditional
               expert frequencies given the input token (j = 1 only).
  free_tok     ridge on TABLE(tokens[t]) ++ bias — the FREE input-token arm.
  history      ridge on S[t] multi-hot ++ bias — address-only.        (i-b)
  history_tok  ridge on S[t] ++ TABLE(tokens[t]) ++ bias — addresses over the
               free token: the D-5 analogue for prefetch.
  draft_free   j = 2: TABLE(tokens[t]) ++ TABLE(tokens[t+1]) ++ bias.  (iii)
  draft_full   j = 2: S[t] ++ TABLE(tokens[t]) ++ TABLE(tokens[t+1]) ++ bias.
  intra        gate l from gates 0..l-k of the SAME position (lead k).  (ii)
  marginal_all the B most frequent experts per gate over all positions.
  front_*      REPORTED ONLY: gates 0..l-1 of the anchor predicting the
               merged-glue L1 class at offsets 1 and 2, beside the previous
               position's standardized free summaries and the majority floor.

Labels are mechanical (conclude()); --conclude-from recomputes every point,
CI, delta and label from the state file and refuses a payload whose stored
numbers differ.

Usage:
  python tools/run_prefetch_readouts.py --harvest results/real/harvest_moe \
      --out results/real/prefetch_s3.json
  python tools/run_prefetch_readouts.py --harvest results/real/harvest_moe_r \
      --out results/real/prefetch_s3_r.json
  python tools/run_prefetch_readouts.py --conclude-from results/real/prefetch_s3.json
Smoke (disclosed in the registration; refused under results/):
  python tools/run_prefetch_readouts.py --harvest results/real/harvest_moe_r \
      --only-seeds 8 --smoke-split-val --out <scratch>/prefetch_smoke.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sideband.harvest import label_index, split_of_prompt, verified_seed_files  # noqa: E402
from sideband.probes import anchor_table, load_label_space, slots_multi_hot  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402
from sideband.stats import cluster_bootstrap_ci, paired_cluster_delta_ci  # noqa: E402

REGISTERED = ("OQ-9 STAGE-1 PREFETCH READOUTS REGISTRATION "
              "(docs/BLUEPRINT.md, 2026-09-14; NON-CRITERION)")
N_EXPERTS = 64
N_GATES = 16
TOP_K = 8
D_MH = N_GATES * N_EXPERTS                      # 1024: one multi-hot / one table vector
BUDGETS = (8, 16, 32)
HORIZONS = (1, 2, 3, 4)
DRAFT_HORIZON = 2
LEADS = (1, 2, 4)
OFFSETS_IV = (1, 2)
LAMBDAS = (0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0)   # widened pre-freeze after the first smoke selected 1000 (the edge)
LABEL_BUDGET = 16
LABEL_HORIZON = 1
LABEL_LEAD = 1
P1_WINDOW_BUDGET = 32                            # P1's "union of the last 4 sets" window, reported
MATERIAL = 0.05
CACHE_BAR = 0.90
N_BOOT = 2000
BOOT_SEED = 0
CHUNK = 4096
BUCKETS16 = ROOT / "results" / "real" / "buckets_olmoe_k16.json"
GLUE16 = ROOT / "results" / "real" / "glue_olmoe_k16.json"
ARMS_REQUIRED = ("recency", "marginal", "free_table", "free_tok", "history", "history_tok",
                 "draft_free", "draft_full", "intra", "marginal_all",
                 "front_gates", "front_free", "front_floor")
# slices of the horizon design [S[t] (1024) ++ TABLE(tokens[t]) (1024) ++ TABLE(tokens[t+1]) (1024, j = 2 only) ++ bias]
ARM_SLICES = {
    "history": (0, D_MH),
    "free_tok": (D_MH, 2 * D_MH),
    "history_tok": (0, 2 * D_MH),
    "draft_free": (D_MH, 3 * D_MH),
    "draft_full": (0, 3 * D_MH),
}
LEARNED_ARMS_OF_HORIZON = {1: ("history", "free_tok", "history_tok"),
                           2: ("history", "free_tok", "history_tok", "draft_free", "draft_full"),
                           3: ("history", "free_tok", "history_tok"),
                           4: ("history", "free_tok", "history_tok")}
SPLITS = ("train", "val", "test")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

class S3Data:
    """The S3 harvest opened through the sha-bound loader; rows concatenated
    over shards and padded to a common T (slots -1 beyond length)."""

    def __init__(self, harvest_dir, only_seeds=None, smoke_split_val: bool = False):
        self.dir = Path(harvest_dir)
        pairs = verified_seed_files(self.dir)
        if only_seeds is not None:
            keep = {int(s) for s in only_seeds}
            pairs = [(m, p) for m, p in pairs if int(m["seed"]) in keep]
            if not pairs:
                raise SystemExit(f"--only-seeds {sorted(keep)}: no shard left in {self.dir}")
        self.metas = [m for m, _ in pairs]
        self.seeds = [int(m["seed"]) for m in self.metas]
        self.npz_shas = {m["npz_file"]: m["npz_sha256"] for m in self.metas}
        zs = [np.load(p) for _, p in pairs]
        T = max(int(z["tokens"].shape[1]) for z in zs)

        def pad(a, fill):
            if a.shape[1] == T:
                return a
            padv = np.full((a.shape[0], T - a.shape[1]) + a.shape[2:], fill, dtype=a.dtype)
            return np.concatenate([a, padv], axis=1)

        self.T = T
        self.tokens = np.concatenate([pad(z["tokens"], 0) for z in zs]).astype(np.int64)
        self.lengths = np.concatenate([z["lengths"] for z in zs]).astype(np.int64)
        self.prompt_idx = np.concatenate([z["prompt_idx"] for z in zs]).astype(np.int64)
        self.slots = np.concatenate([pad(z["slots"], -1) for z in zs]).astype(np.int16)
        self.mass16 = np.concatenate([pad(z["mass16"], 0) for z in zs]).astype(np.float64)
        self.mass64 = np.concatenate([pad(z["mass64"], 0) for z in zs]).astype(np.float64)
        self.entropy = np.concatenate([pad(z["entropy"], 0) for z in zs]).astype(np.float64)
        self.split = np.array([split_of_prompt(int(p)) for p in self.prompt_idx])
        self.smoke = bool(smoke_split_val)
        if smoke_split_val:
            keep = self.split == "val"
            if not keep.any():
                raise SystemExit("--smoke-split-val: no val rows")
            for name in ("tokens", "lengths", "prompt_idx", "slots", "mass16", "mass64", "entropy"):
                setattr(self, name, getattr(self, name)[keep])
            self.split = np.array(SPLITS, dtype=object)[(self.prompt_idx // 7) % 3].astype(str)
        self.n_rows = int(self.tokens.shape[0])
        self._check_layout()

    def _check_layout(self) -> None:
        if self.slots.ndim != 4 or self.slots.shape[2:] != (N_GATES, TOP_K):
            raise SystemExit(f"slots shape {self.slots.shape} is not (rows, T, {N_GATES}, {TOP_K})")
        if np.any(self.lengths < 1) or np.any(self.lengths > self.T):
            raise SystemExit("row lengths outside [1, T]")
        pos = np.arange(self.T)[None, :]
        valid = pos < self.lengths[:, None]
        v = self.slots[valid]
        if v.size and (v.min() < 0 or v.max() >= N_EXPERTS):
            raise SystemExit("expert ids outside [0, 64) at a valid position")
        if v.size and np.any(np.diff(v, axis=-1) <= 0):
            raise SystemExit("slots are not strictly increasing within a gate (set semantics violated)")
        if np.any(self.slots[~valid] != -1):
            raise SystemExit("slots beyond a row's length are not -1")
        for pid in np.unique(self.prompt_idx):
            got = set(self.split[self.prompt_idx == pid].tolist())
            if len(got) != 1:
                raise SystemExit(f"prompt {pid} maps to splits {got}")

    def rows_of(self, split: str) -> np.ndarray:
        return np.flatnonzero(self.split == split)


# ---------------------------------------------------------------------------
# Position tables (reuse sideband.probes.anchor_table; never re-derived)
# ---------------------------------------------------------------------------

def positions_horizon(lengths: np.ndarray, j: int, T: int):
    """Anchors t with t + j < row length (the target S[t+j] exists)."""
    return anchor_table(lengths, j + 1, T)


def positions_all(lengths: np.ndarray, T: int):
    return anchor_table(lengths, 1, T)


def positions_iv(lengths: np.ndarray, offset: int, T: int):
    """Anchors a >= 1 whose offset label is in range (a FREE_PREV row exists)."""
    rows, anchors = anchor_table(lengths, offset, T)
    keep = anchors >= 1
    return rows[keep], anchors[keep]


def restrict(rows: np.ndarray, anchors: np.ndarray, row_mask: np.ndarray):
    keep = row_mask[rows]
    return rows[keep], anchors[keep]


# ---------------------------------------------------------------------------
# Readout (i): recency policies
# ---------------------------------------------------------------------------

def recency_hits(slots: np.ndarray, lengths: np.ndarray, budgets=BUDGETS, horizons=HORIZONS):
    """hits[(B, j)] -> (R, L) int64, needed[j] -> (R, L) int64 for the
    RECENCY_B policy: at position t the resident set is the B most recently
    used distinct experts at that gate up to and including t (last-use
    descending; ties by expert id ascending); hit = target expert resident."""
    R, T, L, K = slots.shape
    E = N_EXPERTS
    last = np.full((R, L, E), -1, dtype=np.int64)
    eid = np.arange(E, dtype=np.int64)
    gate_ix = np.arange(L)[None, :]
    hits = {(B, j): np.zeros((R, L), np.int64) for B in budgets for j in horizons}
    needed = {j: np.zeros((R, L), np.int64) for j in horizons}
    rows = np.arange(R)
    maxB = max(budgets)
    for t in range(T):
        valid = t < lengths
        if not valid.any():
            break
        vr = rows[valid]
        s = slots[vr, t].astype(np.int64)                        # (n, L, K)
        for kk in range(K):
            last[vr[:, None], gate_ix, s[:, :, kk]] = t
        key = np.where(last >= 0, last * E + (E - 1 - eid), -1)  # desc last-use, asc id
        order = np.argsort(-key, axis=2, kind="stable")[:, :, :maxB]
        used = last >= 0
        for j in horizons:
            tj = t + j
            if tj >= T:
                continue
            ok = valid & (tj < lengths)
            if not ok.any():
                continue
            tgt = slots[:, tj].astype(np.int64)                    # (R, L, K)
            needed[j][ok] += K
            for B in budgets:
                resident = np.zeros((R, L, E), dtype=bool)
                np.put_along_axis(resident, order[:, :, :B], True, axis=2)
                resident &= used
                m = np.take_along_axis(resident, np.clip(tgt, 0, None), axis=2) & (tgt >= 0)
                h = m.sum(axis=2)
                hits[(B, j)][ok] += h[ok]
    return hits, needed


# ---------------------------------------------------------------------------
# Linear readers: Grams, ridge, top-B
# ---------------------------------------------------------------------------

def with_bias(X: np.ndarray) -> np.ndarray:
    return np.hstack([X, np.ones((X.shape[0], 1), dtype=X.dtype)])


def class_onehot(y: np.ndarray, n_classes: int) -> np.ndarray:
    out = np.zeros((y.shape[0], n_classes), dtype=np.float64)
    out[np.arange(y.shape[0]), y] = 1.0
    return out


def ridge_solve(G: np.ndarray, C: np.ndarray, lam: float) -> np.ndarray:
    return np.linalg.solve(G + lam * np.eye(G.shape[0]), C)


def topb_order(scores: np.ndarray, B: int) -> np.ndarray:
    """(N, L, B) expert indices: the B largest scores per gate, ties by expert
    id ascending (stable sort on the negated scores)."""
    return np.argsort(-scores, axis=2, kind="stable")[:, :, :B]


def hits_from_scores(scores_flat: np.ndarray, Y_flat: np.ndarray, B: int) -> np.ndarray:
    """scores/Y (N, L*E) -> (N, L) hit counts at budget B."""
    N = scores_flat.shape[0]
    sc = scores_flat.reshape(N, N_GATES, N_EXPERTS)
    yy = Y_flat.reshape(N, N_GATES, N_EXPERTS)
    return np.take_along_axis(yy, topb_order(sc, B), axis=2).sum(axis=2)


def hits_from_fixed_resident(Y_flat: np.ndarray, resident: np.ndarray) -> np.ndarray:
    """resident (L, B) expert indices, the same for every position."""
    N = Y_flat.shape[0]
    yy = Y_flat.reshape(N, N_GATES, N_EXPERTS)
    idx = np.broadcast_to(resident[None, :, :], (N,) + resident.shape)
    return np.take_along_axis(yy, idx, axis=2).sum(axis=2)


def resident_from_counts(counts: np.ndarray, B: int) -> np.ndarray:
    """counts (L, E) -> (L, B) the B most frequent experts per gate (ties by id)."""
    return np.argsort(-counts, axis=1, kind="stable")[:, :B]


def per_prompt(values: np.ndarray, prompt_of_pos: np.ndarray, prompt_ids: np.ndarray) -> np.ndarray:
    """Sum (N, ...) values into (P, ...) by prompt id (prompt_ids sorted)."""
    pos = np.searchsorted(prompt_ids, prompt_of_pos)
    out = np.zeros((prompt_ids.shape[0],) + values.shape[1:], dtype=np.int64)
    np.add.at(out, pos, values)
    return out


def arm_slice(arm: str, d_total: int) -> np.ndarray:
    lo, hi = ARM_SLICES[arm]
    return np.r_[np.arange(lo, hi), d_total - 1]


# ---------------------------------------------------------------------------
# The stage-1 computation
# ---------------------------------------------------------------------------

class Stage1:
    def __init__(self, data: S3Data, label_of_token: np.ndarray, n_classes: int,
                 budgets=BUDGETS, horizons=HORIZONS, leads=LEADS, lambdas=LAMBDAS,
                 chunk: int = CHUNK):
        self.d = data
        self.label_of_token = label_of_token
        self.n_classes = int(n_classes)
        self.budgets = tuple(budgets)
        self.horizons = tuple(horizons)
        self.leads = tuple(leads)
        self.lambdas = tuple(float(x) for x in lambdas)
        self.chunk = int(chunk)
        vmax = int(self.d.tokens.max()) + 1
        if vmax > self.label_of_token.shape[0]:
            raise SystemExit("a token id exceeds the label space")
        self.vocab = vmax
        self.masks = {s: self.d.split == s for s in SPLITS}
        self.prompt_ids = {s: np.unique(self.d.prompt_idx[self.masks[s]]) for s in SPLITS}
        self.n_positions: dict = {}
        self.val_table: dict = {}
        self.lambda_selected: dict = {}
        self.grid_edge: dict = {}

    # ----- feature builders -------------------------------------------------
    def mh(self, rows, anchors) -> np.ndarray:
        return slots_multi_hot(self.d.slots[rows, anchors], N_EXPERTS).astype(np.float64)

    def table_vec(self, tok: np.ndarray, prompt: np.ndarray | None = None) -> np.ndarray:
        """(N, 1024) TABLE(tok): per-gate conditional expert frequencies of the
        forward a token feeds, from TRAIN positions; a token with no train
        count at a gate takes the marginal frequencies at the j = 1 target
        positions (MARGINAL's counts). At TRAIN rows pass prompt = the row's
        prompt_idx and every contribution of that PROMPT under this key
        (all seeds, all positions) is subtracted first — LEAVE-ONE-PROMPT-
        OUT, the test information set exactly, since test prompts are
        disjoint from train (critic's second and third passes)."""
        tok = np.asarray(tok, dtype=np.int64)
        c = self.token_table[tok].astype(np.float64)                    # (N, L, E)
        if prompt is not None:
            pk = np.asarray(prompt, dtype=np.int64) * self.vocab + tok
            idx = np.searchsorted(self.pair_keys, pk)
            idx_c = np.minimum(idx, self.pair_keys.shape[0] - 1)
            if not np.all(self.pair_keys[idx_c] == pk):
                raise SystemExit("internal: a train row's (prompt, key) pair is missing from the pair table")
            c -= self.pair_counts[idx_c].astype(np.float64)
            if c.min() < 0:
                raise SystemExit("internal: leave-one-prompt-out removed a contribution the table never counted")
        tot = c.sum(axis=2, keepdims=True)
        marg = self.marginal_freq[None, :, :]
        freq = np.where(tot > 0, c / np.maximum(tot, 1.0), marg)
        return freq.reshape(tok.shape[0], D_MH)

    def free_prev_raw(self, rows, anchors) -> np.ndarray:
        a1 = anchors - 1
        return np.hstack([self.d.mass16[rows, a1], self.d.mass64[rows, a1],
                          self.d.entropy[rows, a1][:, None]])

    def free_prev(self, rows, anchors) -> np.ndarray:
        """[z-scored (mass16, mass64, entropy) at a-1 (TRAIN moments) ++ one-hot
        L1 class of tokens[a-1]]."""
        a1 = anchors - 1
        z = (self.free_prev_raw(rows, anchors) - self.fp_mean) / self.fp_sd
        lab = self.label_of_token[self.d.tokens[rows, a1]]
        return np.hstack([z, class_onehot(lab, self.n_classes)])

    def iv_labels(self, rows, anchors, offset) -> np.ndarray:
        li = np.array([label_index(int(a), offset) for a in anchors], dtype=np.int64)
        return self.label_of_token[self.d.tokens[rows, li]]

    def horizon_design(self, rows, anchors, j, lopo: bool = False) -> tuple[np.ndarray, np.ndarray]:
        """X = [S[t] ++ TABLE(tokens[t]) ++ (j = 2: TABLE(tokens[t+1])) ++ bias],
        Y = S[t+j] multi-hot. lopo=True (TRAIN rows only): each TABLE block is
        read leave-one-prompt-out — every contribution of the row's own
        prompt under that key is removed; the row's own (t -> t+1) and, at
        j = 2, (t+1 -> t+2) contributions are among them by construction
        (t + j < length)."""
        d = self.d
        prompt = d.prompt_idx[rows] if lopo else None
        blocks = [self.mh(rows, anchors), self.table_vec(d.tokens[rows, anchors], prompt)]
        if j == DRAFT_HORIZON:
            blocks.append(self.table_vec(d.tokens[rows, anchors + 1], prompt))
        return with_bias(np.hstack(blocks)), self.mh(rows, anchors + j)

    def table_coverage(self) -> dict:
        """Per split: share of j = 1 positions whose key token has no train
        count (marginal fallback); on train also the singleton-key share; on
        test also the draft key tokens[t+1] at j = 2."""
        d = self.d
        out = {}
        for split in SPLITS:
            rows, anchors = restrict(*positions_horizon(d.lengths, 1, d.T), self.masks[split])
            cnt = self.token_table[d.tokens[rows, anchors]].sum(axis=(1, 2))
            entry = {"n": int(rows.shape[0]), "zero_count_share": float((cnt == 0).mean()) if rows.size else None}
            if split == "train":
                entry["singleton_key_share"] = float((cnt == N_GATES * TOP_K).mean()) if rows.size else None
            if split == "test":
                r2, a2 = restrict(*positions_horizon(d.lengths, DRAFT_HORIZON, d.T), self.masks[split])
                c2 = self.token_table[d.tokens[r2, a2 + 1]].sum(axis=(1, 2))
                entry["draft_key_zero_count_share"] = float((c2 == 0).mean()) if r2.size else None
            out[split] = entry
        return out

    # ----- pass 1: train statistics ----------------------------------------
    def fit(self) -> None:
        d = self.d
        train = self.masks["train"]
        dX = D_MH + 1
        # (ii) + marginal_all: every valid train position
        rows, anchors = restrict(*positions_all(d.lengths, d.T), train)
        self.n_positions["all/train"] = int(rows.shape[0])
        G = np.zeros((dX, dX))
        for s in range(0, rows.shape[0], self.chunk):
            X = with_bias(self.mh(rows[s:s + self.chunk], anchors[s:s + self.chunk]))
            G += X.T @ X
        self.G_all = G
        self.counts_all = np.diag(G)[:D_MH].reshape(N_GATES, N_EXPERTS).copy()
        # TABLE: train positions t (t + 1 < length), key tokens[t] -> S[t+1]
        rows, anchors = restrict(*positions_horizon(d.lengths, 1, d.T), train)
        tok = d.tokens[rows, anchors]
        sl = d.slots[rows, anchors + 1].astype(np.int64)                   # (N, L, K)
        gate = np.arange(N_GATES)[None, :, None]
        flat = (tok[:, None, None] * D_MH + gate * N_EXPERTS + sl).ravel()
        self.token_table = np.bincount(flat, minlength=self.vocab * D_MH) \
            .reshape(self.vocab, N_GATES, N_EXPERTS).astype(np.int64)
        # leave-one-prompt-out support: the same contributions keyed by (prompt, token)
        pair_key = d.prompt_idx[rows] * self.vocab + tok
        self.pair_keys, inv = np.unique(pair_key, return_inverse=True)
        flat_p = (inv.reshape(-1)[:, None, None] * D_MH + gate * N_EXPERTS + sl).ravel()
        self.pair_counts = np.bincount(flat_p, minlength=self.pair_keys.shape[0] * D_MH) \
            .reshape(self.pair_keys.shape[0], N_GATES, N_EXPERTS).astype(np.int32)
        if not np.array_equal(self.pair_counts.sum(axis=0), self.token_table.sum(axis=0)):
            raise SystemExit("internal: the (prompt, token) pair table does not sum to the token table")
        counts_h1 = self.token_table.sum(axis=0).astype(np.float64)        # marginal at j = 1 targets
        self.marginal_freq = counts_h1 / np.maximum(counts_h1.sum(axis=1, keepdims=True), 1.0)
        # horizon Grams over the full design; every learned arm is a slice
        self.G_h, self.C_h, self.counts_h = {}, {}, {}
        for j in self.horizons:
            rows, anchors = restrict(*positions_horizon(d.lengths, j, d.T), train)
            self.n_positions[f"horizon{j}/train"] = int(rows.shape[0])
            dD = (3 if j == DRAFT_HORIZON else 2) * D_MH + 1
            Gj = np.zeros((dD, dD)); Cj = np.zeros((dD, D_MH))
            for s in range(0, rows.shape[0], self.chunk):
                X, Y = self.horizon_design(rows[s:s + self.chunk], anchors[s:s + self.chunk], j, lopo=True)
                Gj += X.T @ X
                Cj += X.T @ Y
            self.G_h[j], self.C_h[j] = Gj, Cj
            self.counts_h[j] = Cj[-1].reshape(N_GATES, N_EXPERTS).copy()   # bias row = target counts
        if not np.array_equal(self.counts_h[1], counts_h1):
            raise SystemExit("internal: j = 1 target counts differ between the table and the Gram")
        # (iv) per offset: train moments for FREE_PREV first, then Grams
        self.G_g, self.C_g, self.G_f, self.C_f, self.floor_class = {}, {}, {}, {}, {}
        rows, anchors = restrict(*positions_iv(d.lengths, 1, d.T), train)
        raw = self.free_prev_raw(rows, anchors)
        self.fp_mean = raw.mean(axis=0)
        sd = raw.std(axis=0)
        self.fp_sd = np.where(sd > 0, sd, 1.0)
        dF = raw.shape[1] + self.n_classes + 1
        for o in OFFSETS_IV:
            rows, anchors = restrict(*positions_iv(d.lengths, o, d.T), train)
            self.n_positions[f"iv{o}/train"] = int(rows.shape[0])
            Gg = np.zeros((dX, dX)); Cg = np.zeros((dX, self.n_classes))
            Gf = np.zeros((dF, dF)); Cf = np.zeros((dF, self.n_classes))
            for s in range(0, rows.shape[0], self.chunk):
                r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
                Y = class_onehot(self.iv_labels(r, a, o), self.n_classes)
                Xg = with_bias(self.mh(r, a)); Xf = with_bias(self.free_prev(r, a))
                Gg += Xg.T @ Xg; Cg += Xg.T @ Y
                Gf += Xf.T @ Xf; Cf += Xf.T @ Y
            self.G_g[o], self.C_g[o], self.G_f[o], self.C_f[o] = Gg, Cg, Gf, Cf
            cls_counts = Cg[-1]
            self.floor_class[o] = int(np.flatnonzero(cls_counts == cls_counts.max())[0])
        # solve every reader at every lambda
        self.W_h = {}
        for j in self.horizons:
            dD = self.G_h[j].shape[0]
            for arm in LEARNED_ARMS_OF_HORIZON[j]:
                F = arm_slice(arm, dD)
                Gs = self.G_h[j][np.ix_(F, F)]; Cs = self.C_h[j][F]
                for lam in self.lambdas:
                    self.W_h[(arm, j, lam)] = ridge_solve(Gs, Cs, lam)
        self.W_i = {}
        for k in self.leads:
            for l in range(k, N_GATES):
                F = np.r_[np.arange(N_EXPERTS * (l - k + 1)), dX - 1]
                tgt = np.arange(N_EXPERTS * l, N_EXPERTS * (l + 1))
                Gs = self.G_all[np.ix_(F, F)]; Cs = self.G_all[np.ix_(F, tgt)]
                for lam in self.lambdas:
                    self.W_i[(k, l, lam)] = ridge_solve(Gs, Cs, lam)
        self.W_g, self.W_f = {}, {}
        for o in OFFSETS_IV:
            for l in range(1, N_GATES + 1):
                F = np.r_[np.arange(N_EXPERTS * l), dX - 1]
                Gs = self.G_g[o][np.ix_(F, F)]; Cs = self.C_g[o][F]
                for lam in self.lambdas:
                    self.W_g[(o, l, lam)] = ridge_solve(Gs, Cs, lam)
            for lam in self.lambdas:
                self.W_f[(o, lam)] = ridge_solve(self.G_f[o], self.C_f[o], lam)

    # ----- pass 2: evaluation on a split -------------------------------------
    def evaluate(self, split: str) -> dict:
        """Per-prompt hit / needed tables for every arm, every lambda.
        out[(arm, B, key, depth, lam)] = (hits (P, L) or (P, 1), needed (P, L) or (P, 1))"""
        d = self.d
        mask = self.masks[split]
        pids = self.prompt_ids[split]
        P = pids.shape[0]
        dX = D_MH + 1
        out: dict = {}

        def acc(key, h, n):
            if key in out:
                out[key][0][...] += h; out[key][1][...] += n
            else:
                out[key] = (h.copy(), n.copy())

        # (i) recency: policy over rows of this split (row-level walk)
        rows_split = np.flatnonzero(mask)
        hits, needed = recency_hits(d.slots[rows_split], d.lengths[rows_split], self.budgets, self.horizons)
        pos = np.searchsorted(pids, d.prompt_idx[rows_split])
        for j in self.horizons:
            n = np.zeros((P, N_GATES), np.int64); np.add.at(n, pos, needed[j])
            for B in self.budgets:
                h = np.zeros((P, N_GATES), np.int64); np.add.at(h, pos, hits[(B, j)])
                acc(("recency", B, j, None, None), h, n)
        # horizon tables: marginal, free_table, and the learned arms
        for j in self.horizons:
            rows, anchors = restrict(*positions_horizon(d.lengths, j, d.T), mask)
            self.n_positions[f"horizon{j}/{split}"] = int(rows.shape[0])
            res_m = {B: resident_from_counts(self.counts_h[j], B) for B in self.budgets}
            for s in range(0, rows.shape[0], self.chunk):
                r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
                pp = d.prompt_idx[r]
                X, Y = self.horizon_design(r, a, j)
                n = per_prompt(np.full((r.shape[0], N_GATES), TOP_K, np.int64), pp, pids)
                for B in self.budgets:
                    acc(("marginal", B, j, None, None),
                        per_prompt(hits_from_fixed_resident(Y, res_m[B]), pp, pids), n)
                if j == 1:
                    tv = X[:, D_MH:2 * D_MH]                                     # TABLE(tokens[t])
                    for B in self.budgets:
                        acc(("free_table", B, j, None, None),
                            per_prompt(hits_from_scores(tv, Y, B), pp, pids), n)
                for arm in LEARNED_ARMS_OF_HORIZON[j]:
                    F = arm_slice(arm, X.shape[1])
                    Xa = X[:, F]
                    for lam in self.lambdas:
                        sc = Xa @ self.W_h[(arm, j, lam)]
                        for B in self.budgets:
                            acc((arm, B, j, None, lam), per_prompt(hits_from_scores(sc, Y, B), pp, pids), n)
        # (ii) + marginal_all: every valid position
        rows, anchors = restrict(*positions_all(d.lengths, d.T), mask)
        self.n_positions[f"all/{split}"] = int(rows.shape[0])
        res_all = {B: resident_from_counts(self.counts_all, B) for B in self.budgets}
        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            pp = d.prompt_idx[r]
            Xm = self.mh(r, a)
            X = with_bias(Xm)
            n = per_prompt(np.full((r.shape[0], N_GATES), TOP_K, np.int64), pp, pids)
            for B in self.budgets:
                acc(("marginal_all", B, 0, None, None),
                    per_prompt(hits_from_fixed_resident(Xm, res_all[B]), pp, pids), n)
            for k in self.leads:
                for lam in self.lambdas:
                    h = {B: np.zeros((r.shape[0], N_GATES), np.int64) for B in self.budgets}
                    for l in range(k, N_GATES):
                        F = np.r_[np.arange(N_EXPERTS * (l - k + 1)), dX - 1]
                        sc = X[:, F] @ self.W_i[(k, l, lam)]                            # (N, E)
                        yy = Xm[:, N_EXPERTS * l:N_EXPERTS * (l + 1)]
                        for B in self.budgets:
                            order = np.argsort(-sc, axis=1, kind="stable")[:, :B]
                            h[B][:, l] = np.take_along_axis(yy, order, axis=1).sum(axis=1)
                    for B in self.budgets:
                        nn = n.copy(); nn[:, :k] = 0
                        acc(("intra", B, k, None, lam), per_prompt(h[B], pp, pids), nn)
        # (iv) front-loading
        for o in OFFSETS_IV:
            rows, anchors = restrict(*positions_iv(d.lengths, o, d.T), mask)
            self.n_positions[f"iv{o}/{split}"] = int(rows.shape[0])
            for s in range(0, rows.shape[0], self.chunk):
                r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
                pp = d.prompt_idx[r]
                y = self.iv_labels(r, a, o)
                n = per_prompt(np.ones((r.shape[0], 1), np.int64), pp, pids)
                Xg = with_bias(self.mh(r, a)); Xf = with_bias(self.free_prev(r, a))
                acc(("front_floor", None, o, None, None),
                    per_prompt((y == self.floor_class[o]).astype(np.int64)[:, None], pp, pids), n)
                for lam in self.lambdas:
                    pred = np.argmax(Xf @ self.W_f[(o, lam)], axis=1)
                    acc(("front_free", None, o, None, lam),
                        per_prompt((pred == y).astype(np.int64)[:, None], pp, pids), n)
                    for l in range(1, N_GATES + 1):
                        F = np.r_[np.arange(N_EXPERTS * l), dX - 1]
                        pred = np.argmax(Xg[:, F] @ self.W_g[(o, l, lam)], axis=1)
                        acc(("front_gates", None, o, l, lam),
                            per_prompt((pred == y).astype(np.int64)[:, None], pp, pids), n)
        return out

    # ----- lambda selection on val --------------------------------------------
    def select_lambdas(self, val: dict) -> None:
        def pooled(arm, B, key, depth, lam):
            h, n = val[(arm, B, key, depth, lam)]
            return float(h.sum() / n.sum()) if n.sum() > 0 else float("nan")

        def pick(family, score_of):
            best_lam, best = None, -np.inf
            table = {}
            for lam in self.lambdas:
                v = score_of(lam)
                table[str(lam)] = v
                if v > best:                       # strict: ties keep the smaller lambda
                    best, best_lam = v, lam
            self.val_table[family] = table
            self.lambda_selected[family] = best_lam
            self.grid_edge[family] = bool(best_lam in (self.lambdas[0], self.lambdas[-1]))

        for j in self.horizons:
            for arm in LEARNED_ARMS_OF_HORIZON[j]:
                pick(f"{arm}/j{j}", lambda lam, arm=arm, j=j: pooled(arm, LABEL_BUDGET, j, None, lam))
        for k in self.leads:
            pick(f"intra/lead{k}", lambda lam, k=k: pooled("intra", LABEL_BUDGET, k, None, lam))
        pick("front_free", lambda lam: pooled("front_free", None, 1, None, lam))

        def gates_score(lam):
            hs = sum(val[("front_gates", None, 1, l, lam)][0].sum() for l in range(1, N_GATES + 1))
            ns = sum(val[("front_gates", None, 1, l, lam)][1].sum() for l in range(1, N_GATES + 1))
            return float(hs / ns) if ns > 0 else float("nan")
        pick("front_gates", gates_score)

    def family_of(self, arm, key) -> str | None:
        if arm in ARM_SLICES:
            return f"{arm}/j{key}"
        if arm == "intra":
            return f"intra/lead{key}"
        if arm in ("front_free", "front_gates"):
            return arm
        return None

    # ----- state rows at the selected lambdas ---------------------------------
    def state_rows(self, test: dict) -> list[dict]:
        pids = self.prompt_ids["test"]
        rows = []
        for (arm, B, key, depth, lam), (h, n) in test.items():
            fam = self.family_of(arm, key)
            if fam is not None and lam != self.lambda_selected[fam]:
                continue
            if fam is None and lam is not None:
                continue
            for pi, pid in enumerate(pids):
                for g in range(h.shape[1]):
                    if n[pi, g] == 0:
                        continue
                    rows.append({"arm": arm, "budget": B, "key": int(key), "depth": depth,
                                 "gate": int(g) if h.shape[1] == N_GATES else -1,
                                 "prompt_idx": int(pid), "hits": int(h[pi, g]), "needed": int(n[pi, g])})
        return sort_rows(rows)


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes this from the state file)
# ---------------------------------------------------------------------------

def _sort_key(r: dict):
    return (r["arm"], -1 if r["budget"] is None else int(r["budget"]), int(r["key"]),
            -1 if r["depth"] is None else int(r["depth"]), int(r["gate"]), int(r["prompt_idx"]))


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=_sort_key)


def _group(rows: list[dict]) -> dict:
    """{(arm, budget, key, depth): {gate: {prompt: (hits, needed)}}}"""
    g: dict = {}
    for r in rows:
        k = (r["arm"], r["budget"], int(r["key"]), r["depth"])
        g.setdefault(k, {}).setdefault(int(r["gate"]), {})[int(r["prompt_idx"])] = (int(r["hits"]), int(r["needed"]))
    return g


def _arrays(cell: dict, prompts: list[int]):
    h = np.array([cell.get(p, (0, 0))[0] for p in prompts], dtype=np.float64)
    n = np.array([cell.get(p, (0, 0))[1] for p in prompts], dtype=np.float64)
    return h, n


def _pooled(gates: dict, prompts: list[int], gate_filter=None):
    H = np.zeros(len(prompts)); N = np.zeros(len(prompts))
    for g, cell in gates.items():
        if gate_filter is not None and g not in gate_filter:
            continue
        h, n = _arrays(cell, prompts)
        H += h; N += n
    return H, N


def _point_ci(h: np.ndarray, n: np.ndarray, n_boot: int, seed: int) -> dict:
    lo, hi = cluster_bootstrap_ci(h, n, n_boot=n_boot, seed=seed)
    return {"point": float(h.sum() / n.sum()), "ci_lo": lo, "ci_hi": hi, "needed": int(n.sum())}


def _delta(ha, hb, n, n_boot, seed) -> dict:
    d, lo, hi = paired_cluster_delta_ci(ha, hb, n, n_boot=n_boot, seed=seed)
    return {"delta": d, "lo": lo, "hi": hi, "needed": int(n.sum())}


def _reading(dl: dict, material: float = MATERIAL) -> str:
    if dl["lo"] > 0 and dl["delta"] >= material:
        return "SIGNAL"
    if dl["hi"] < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"


LABEL_DELTAS = {
    "history": ("history", "recency", LABEL_HORIZON),
    "address_beyond_token": ("history_tok", "free_tok", LABEL_HORIZON),
    "draft": ("draft_full", "history_tok", DRAFT_HORIZON),
}


def conclude(rows: list[dict], n_boot: int = N_BOOT, seed: int = BOOT_SEED,
             budgets=BUDGETS, horizons=HORIZONS, leads=LEADS) -> dict:
    rows = sort_rows(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    groups = _group(rows)
    tables: dict = {}
    for (arm, B, key, depth), gates in groups.items():
        name = f"{arm}|B={B}|key={key}|depth={depth}"
        entry = {"arm": arm, "budget": B, "key": key, "depth": depth, "per_gate": {}}
        for g in sorted(gates):
            h, n = _arrays(gates[g], prompts)
            entry["per_gate"][str(g)] = _point_ci(h, n, n_boot, seed)
        H, N = _pooled(gates, prompts)
        entry["all"] = _point_ci(H, N, n_boot, seed)
        tables[name] = entry

    def pooled_of(arm, B, key, depth=None, gate_filter=None):
        gates = groups.get((arm, B, int(key), depth))
        if gates is None:
            return None
        return _pooled(gates, prompts, gate_filter)

    def delta_of(a, b, gate_filter=None):
        pa, pb = pooled_of(*a, gate_filter=gate_filter), pooled_of(*b, gate_filter=gate_filter)
        if pa is None or pb is None:
            return None
        if not np.array_equal(pa[1], pb[1]):
            raise SystemExit(f"pairing violated: {a} and {b} have different per-prompt trials")
        return _delta(pa[0], pb[0], pa[1], n_boot, seed)

    deltas: dict = {}
    for B in budgets:
        for j in horizons:
            for a, b in (("history", "recency"), ("history", "marginal"), ("free_tok", "recency"),
                         ("history_tok", "free_tok"), ("history_tok", "recency"), ("history_tok", "history")):
                deltas[f"{a}-{b}|B={B}|j={j}"] = delta_of((a, B, j), (b, B, j))
        deltas[f"free_table-recency|B={B}|j=1"] = delta_of(("free_table", B, 1), ("recency", B, 1))
        deltas[f"free_tok-free_table|B={B}|j=1"] = delta_of(("free_tok", B, 1), ("free_table", B, 1))
        for a, b in (("draft_full", "history_tok"), ("draft_free", "free_tok"), ("draft_full", "draft_free"),
                     ("draft_full", "recency")):
            deltas[f"{a}-{b}|B={B}|j={DRAFT_HORIZON}"] = delta_of((a, B, DRAFT_HORIZON), (b, B, DRAFT_HORIZON))
        for k in leads:
            gf = set(range(k, N_GATES))
            deltas[f"intra-marginal_all|B={B}|lead={k}"] = delta_of(("intra", B, k), ("marginal_all", B, 0), gate_filter=gf)
    for o in OFFSETS_IV:
        for l in range(1, N_GATES + 1):
            deltas[f"front_gates-front_free|o={o}|depth={l}"] = delta_of(("front_gates", None, o, l), ("front_free", None, o))
            deltas[f"front_gates-front_floor|o={o}|depth={l}"] = delta_of(("front_gates", None, o, l), ("front_floor", None, o))
        deltas[f"front_free-front_floor|o={o}"] = delta_of(("front_free", None, o), ("front_floor", None, o))
    deltas = {k: v for k, v in deltas.items() if v is not None}

    present = {r["arm"] for r in rows}
    missing = [a for a in ARMS_REQUIRED if a not in present]
    rec_key = f"recency|B={LABEL_BUDGET}|key={LABEL_HORIZON}|depth=None"
    p1_key = f"recency|B={P1_WINDOW_BUDGET}|key={LABEL_HORIZON}|depth=None"
    need_keys = {name: f"{a}-{b}|B={LABEL_BUDGET}|j={j}" for name, (a, b, j) in LABEL_DELTAS.items()}
    need_keys["intra_forward"] = f"intra-marginal_all|B={LABEL_BUDGET}|lead={LABEL_LEAD}"
    missing_cells = [k for k in list(need_keys.values()) + [rec_key, p1_key]
                     if k not in deltas and k not in tables]
    labels: dict = {"missing_arms": missing, "missing_label_cells": missing_cells}
    if missing or missing_cells:
        labels.update({"cache_sufficient": None, "history": None, "address_beyond_token": None,
                       "intra_forward": None, "draft": None, "stage": "INCOMPLETE", "sideband_sentence": None})
        return {"tables": tables, "deltas": deltas, "labels": labels}
    rec = tables[rec_key]["all"]["point"]
    labels["recency_16_j1_point"] = rec
    labels["cache_sufficient"] = bool(rec >= CACHE_BAR)
    labels["recency_32_j1_point"] = tables[p1_key]["all"]["point"]
    labels["p1_window_kill_would_fire"] = bool(tables[p1_key]["all"]["point"] >= CACHE_BAR)
    for name, key in need_keys.items():
        labels[name] = _reading(deltas[key])
        labels[f"{name}_delta"] = deltas[key]
    if labels["cache_sufficient"]:
        labels["stage"] = "CACHE-SUFFICIENT"
    elif labels["history"] == "SIGNAL" or labels["intra_forward"] == "SIGNAL":
        labels["stage"] = "PREFETCH-HEADROOM"
    else:
        labels["stage"] = "PREFETCH-NOT-SHOWN"
    labels["sideband_sentence"] = {
        "SIGNAL": "the address stream adds a material margin over the free input token at this reader",
        "NOT-SHOWN": "no material margin of the address stream over the free input token is shown at this reader",
        "NEGATIVE": "the address stream reads below the free input token at this reader",
    }[labels["address_beyond_token"]]
    labels["rule"] = (f"CACHE-SUFFICIENT iff recency B={LABEL_BUDGET} j={LABEL_HORIZON} pooled point >= {CACHE_BAR} "
                      f"(recency B={P1_WINDOW_BUDGET}, P1's window, reported with its own would-fire flag); "
                      f"readings SIGNAL iff CI95 lower > 0 and delta >= +{MATERIAL}, NEGATIVE iff CI95 upper < 0, "
                      f"else NOT-SHOWN; HISTORY = history - recency (j=1), ADDRESS-BEYOND-TOKEN = history_tok - free_tok "
                      f"(j=1), INTRA-FORWARD = intra lead {LABEL_LEAD} - marginal_all (gates >= {LABEL_LEAD}), "
                      f"DRAFT = draft_full - history_tok (j={DRAFT_HORIZON}); stage PREFETCH-HEADROOM iff HISTORY or "
                      f"INTRA-FORWARD reads SIGNAL; the sideband sentence follows ADDRESS-BEYOND-TOKEN alone; every "
                      f"label scoped to the registered linear readers at hit rate; NON-CRITERION")
    return {"tables": tables, "deltas": deltas, "labels": labels}


# ---------------------------------------------------------------------------
# Provenance, I/O, CLI
# ---------------------------------------------------------------------------

def _git() -> tuple[str, list[str]]:
    try:
        c = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
        st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, cwd=ROOT, check=True).stdout
        tracked = [ln[3:].strip() for ln in st.splitlines() if ln.strip()]
        return (c + ("-dirty" if tracked else ""), tracked)
    except Exception:  # pragma: no cover - git absent
        return ("unknown", [])


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _under_results(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to((ROOT / "results").resolve())
        return True
    except ValueError:
        return False


def run(args) -> dict:
    started = time.time()
    only = [int(s) for s in args.only_seeds.split(",")] if args.only_seeds else None
    smoke = bool(args.smoke_split_val or only is not None)
    out = Path(args.out)
    if smoke and _under_results(out):
        raise SystemExit("a smoke (--only-seeds / --smoke-split-val) may not write under results/")
    lambdas = tuple(float(x) for x in args.lambdas.split(",")) if getattr(args, "lambdas", None) else LAMBDAS
    if lambdas != LAMBDAS and not smoke and _under_results(out):
        raise SystemExit("a non-registered lambda grid may not write under results/")
    data = S3Data(args.harvest, only_seeds=only, smoke_split_val=args.smoke_split_val)
    label_of_token, n_classes = load_label_space(args.buckets, args.glue)
    st = Stage1(data, label_of_token, n_classes, lambdas=lambdas)
    st.fit()
    val = st.evaluate("val")
    st.select_lambdas(val)
    test = st.evaluate("test")
    rows = st.state_rows(test)
    conclusion = conclude(rows)
    git_commit, tracked = _git()
    prov = {
        "registered": REGISTERED,
        "git_commit": git_commit,
        "git_status_tracked": tracked,
        "instrument_sha256": _sha(Path(__file__)),
        "harvest_dir": str(args.harvest),
        "harvest_npz_sha256": data.npz_shas,
        "seeds": data.seeds,
        "smoke": smoke,
        "smoke_split_val": bool(args.smoke_split_val),
        "label_space": {"buckets": str(args.buckets), "buckets_sha256": _sha(args.buckets),
                        "glue": str(args.glue), "glue_sha256": _sha(args.glue), "n_classes": int(n_classes)},
        "constants": {"budgets": list(BUDGETS), "horizons": list(HORIZONS), "draft_horizon": DRAFT_HORIZON,
                      "leads": list(LEADS), "offsets_iv": list(OFFSETS_IV), "lambdas": list(lambdas),
                      "label_budget": LABEL_BUDGET, "p1_window_budget": P1_WINDOW_BUDGET, "material": MATERIAL,
                      "cache_bar": CACHE_BAR, "n_boot": N_BOOT, "boot_seed": BOOT_SEED, "chunk": CHUNK},
        "n_positions": st.n_positions,
        "n_test_prompts": int(st.prompt_ids["test"].shape[0]),
        "floor_class": {str(o): st.floor_class[o] for o in OFFSETS_IV},
        "table_coverage": st.table_coverage(),
        "free_prev_moments": {"mean_sha256": hashlib.sha256(st.fp_mean.tobytes()).hexdigest(),
                              "sd_sha256": hashlib.sha256(st.fp_sd.tobytes()).hexdigest(), "dims": int(st.fp_mean.shape[0])},
        "lambda_selected": {k: float(v) for k, v in st.lambda_selected.items()},
        "lambda_grid_edge": st.grid_edge,
        "val_table": st.val_table,
        "args": redact_args(vars(args)),
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "started_unix": started,
        "runtime_s": time.time() - started,
    }
    payload = {"registered": REGISTERED, "provenance": prov, "conclusion": conclusion, "n_state_rows": len(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    state_path = Path(str(out) + ".state.jsonl")
    with open(state_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"state_header": True, "registered": REGISTERED,
                             "harvest_npz_sha256": data.npz_shas, "smoke": smoke}) + "\n")
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    meta_path = Path(str(out)[:-5] + ".meta.json") if str(out).endswith(".json") else Path(str(out) + ".meta.json")
    meta_path.write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print_summary(payload)
    return payload


def load_state(state_path: Path) -> tuple[dict, list[dict]]:
    lines = Path(state_path).read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    if not header.get("state_header"):
        raise SystemExit("state file has no header row")
    return header, [json.loads(ln) for ln in lines[1:] if ln.strip()]


def conclude_from(payload_path: Path) -> dict:
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if payload.get("registered") != REGISTERED:
        raise SystemExit("payload is not an OQ-9 stage-1 payload")
    header, rows = load_state(Path(str(payload_path) + ".state.jsonl"))
    if header["harvest_npz_sha256"] != payload["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("state header harvest shas differ from the payload's")
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit("state row count differs from the payload's")
    got = conclude(rows)
    if json.dumps(got, sort_keys=True) != json.dumps(payload["conclusion"], sort_keys=True):
        raise SystemExit("RECOMPUTE MISMATCH: the state file does not reproduce the payload's conclusion")
    tag = " (SMOKE — not evidence)" if payload["provenance"].get("smoke") else ""
    print(f"conclude-from: state file reproduces the payload exactly{tag}")
    print_summary(payload)
    return got


def print_summary(payload: dict) -> None:
    c = payload["conclusion"]; lab = c["labels"]
    print(f"STAGE LABEL: {lab.get('stage')}   (smoke={payload['provenance'].get('smoke')})")
    if lab.get("stage") == "INCOMPLETE":
        print("missing arms:", lab["missing_arms"], "missing label cells:", lab["missing_label_cells"]); return
    print(f"  recency B=16 j=1: {lab['recency_16_j1_point']:.4f}  cache_sufficient={lab['cache_sufficient']}   "
          f"recency B=32 j=1: {lab['recency_32_j1_point']:.4f}  p1_window_would_fire={lab['p1_window_kill_would_fire']}")
    for name in ("history", "address_beyond_token", "intra_forward", "draft"):
        d = lab[f"{name}_delta"]
        print(f"  {name:21s} {lab[name]:10s} delta {d['delta']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]")
    print(f"  sideband sentence: {lab['sideband_sentence']}")
    for B in BUDGETS:
        for arm, key in (("recency", 1), ("marginal", 1), ("free_table", 1), ("free_tok", 1), ("history", 1),
                         ("history_tok", 1), ("recency", 2), ("free_tok", 2), ("history_tok", 2),
                         ("draft_free", 2), ("draft_full", 2)):
            t = c["tables"].get(f"{arm}|B={B}|key={key}|depth=None")
            if t:
                a = t["all"]; print(f"  B={B:2d} j={key} {arm:12s} {a['point']:.4f} [{a['ci_lo']:.4f}, {a['ci_hi']:.4f}]")
    for k in LEADS:
        t = c["tables"].get(f"intra|B=16|key={k}|depth=None")
        m = c["tables"].get("marginal_all|B=16|key=0|depth=None")
        if t and m:
            print(f"  intra lead {k} B=16 pooled {t['all']['point']:.4f}  (marginal_all {m['all']['point']:.4f})")
    for o in OFFSETS_IV:
        fl = c["tables"].get(f"front_floor|B=None|key={o}|depth=None"); fr = c["tables"].get(f"front_free|B=None|key={o}|depth=None")
        g16 = c["tables"].get(f"front_gates|B=None|key={o}|depth=16"); g1 = c["tables"].get(f"front_gates|B=None|key={o}|depth=1")
        if fl and fr and g16 and g1:
            print(f"  front o={o}: floor {fl['all']['point']:.4f} free_prev {fr['all']['point']:.4f} "
                  f"gates<=1 {g1['all']['point']:.4f} gates<=16 {g16['all']['point']:.4f}")
    print("  lambda:", payload["provenance"].get("lambda_selected"))
    print("  grid-edge:", payload["provenance"].get("lambda_grid_edge"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default=str(ROOT / "results" / "real" / "harvest_moe"))
    ap.add_argument("--out", default=str(ROOT / "results" / "real" / "prefetch_s3.json"))
    ap.add_argument("--buckets", default=str(BUCKETS16))
    ap.add_argument("--glue", default=str(GLUE16))
    ap.add_argument("--only-seeds", default=None, help="smoke only: comma-separated generation seeds")
    ap.add_argument("--smoke-split-val", action="store_true",
                    help="smoke only: keep the val prompts and re-split them by (prompt_idx // 7) %% 3")
    ap.add_argument("--lambdas", default=None, help="tests/smoke only: comma-separated grid (refused under results/)")
    ap.add_argument("--conclude-from", default=None, help="recompute a payload's conclusion from its state file")
    args = ap.parse_args(argv)
    if args.conclude_from:
        conclude_from(Path(args.conclude_from))
        return
    run(args)


if __name__ == "__main__":
    main()

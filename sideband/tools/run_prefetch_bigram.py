#!/usr/bin/env python
"""tools/run_prefetch_bigram.py — OQ-9 STAGE-1 POST-HOC DIAGNOSTIC: the FREE-BIGRAM
TWIN of the ADDRESS-BEYOND-TOKEN reading (F-26).

Registered 2026-10-01 as a dated AMENDMENT to the stage-1 block in
docs/BLUEPRINT.md ("OQ-9 STAGE-1 FREE-BIGRAM TWIN REGISTRATION"), written
before any readout of it ran on either S3 harvest. NON-CRITERION for every
finding's mechanical label; it executes ONE pinned consequence, a dated
STATUS line under F-26's sideband sentence. CPU only; numpy only — nothing in
this file imports torch, so its tests run in CI.

WHY. F-26's free arm is a ONE-TOKEN table of tokens[t]. The previous token
tokens[t-1] is exactly as free to the decoder and is not in it, and the data
say gate 0 of OLMoE routes primarily on it (the critic's blocking objection at
the F-26 landing). This diagnostic puts the previous token into the free
baseline at EQUAL DIMS and re-reads the margin.

THE FROZEN INSTRUMENT. tools/run_prefetch_readouts.py (sha 8529532d4d78...,
attested by both committed stage-1 payloads) is imported by bare module name
and NEVER edited; this file refuses to run unless its LF-normalised bytes
still hash to the frozen sha. Its S3Data loader (sha-bound harvest shards),
its leave-one-prompt-out TABLE encoding, its ridge / top-B / per-prompt
machinery and its bootstrap helpers are reused; nothing of them is
re-derived. The committed stage-1 cells are NOT reused as numbers: every arm
below is re-trained on the BIGRAM positions so that all arms share positions
exactly (the frozen state rows pool over t = 0 too and cannot be restricted).

INDEX CONVENTION (the frozen one, verified against the harvester pre-freeze
and on the data at the F-26 landing): forward t has INPUT tokens[t-1],
OUTPUT p_t and routing S[t]; tokens[t] is sampled from p_t. At anchor t the
decoder holds S[t], tokens[t] AND tokens[t-1]; the target is S[t+1], the
routing of the forward tokens[t] feeds.

POSITIONS. The BIGRAM positions: anchors t with t >= 1 and t + 1 < row length
(tokens[t-1] and S[t+1] both exist), horizon j = 1 only. Every arm is read
on these positions, so per-prompt trials are equal across arms.

TABLES (train-fit; every table block is read LEAVE-ONE-PROMPT-OUT at train
rows exactly as the frozen instrument reads its TABLE; val and test rows read
the full train table; a key with no train count at a gate takes MARGINAL's
frequencies at the j = 1 targets, the frozen fallback):
  TABLE_CUR(x)  = the frozen TABLE: train conditional expert frequencies of
                  S[t+1] keyed on tokens[t] = x, built over the frozen
                  instrument's own j = 1 train positions (t = 0 included) —
                  asserted equal to Stage1.fit's table in the tests.
  TABLE_PREV(x) = train conditional expert frequencies of S[t+1] keyed on
                  tokens[t-1] = x, built over the bigram train positions.
DESIGN (one float64 Gram over the bigram train positions, every arm a slice):
  [ S[t] multi-hot (1024) ++ TABLE_CUR(tokens[t]) (1024)
    ++ TABLE_PREV(tokens[t-1]) (1024) ++ TABLE_CUR(tokens[t-1]) (1024) ++ bias ]
Two FREE encodings of the previous token are carried, both 1024-dim:
  (b) prev_table         TABLE_PREV(tokens[t-1]) — target-aligned, the
                         critic's diagnostic table;
  (a) cur_table_at_prev  TABLE_CUR(tokens[t-1]) — the frozen table read at the
                         previous token (its train routing profile for the
                         forward it fed, an estimate of S[t]).
ARMS (slices ++ bias; dims in parentheses):
  history           S[t]                                   (1025)
  free_tok          TABLE_CUR(tokens[t])                   (1025)  the F-26 free arm
  history_tok       S[t] ++ TABLE_CUR(tokens[t])           (2049)  the F-26 address arm
  free_bigram_b     TABLE_CUR(tokens[t]) ++ (b)            (2049)
  free_bigram_a     TABLE_CUR(tokens[t]) ++ (a)            (2049)
  FREE_BIGRAM       = free_bigram_b or free_bigram_a, the ENCODING SELECTED
                      ON VAL (pooled hit rate at B = 16, jointly with lambda;
                      ties keep (b)) — THE equal-dims twin of history_tok
  history_bigram_b  S[t] ++ free_bigram_b's blocks         (3073)
  history_bigram_a  S[t] ++ free_bigram_a's blocks         (3073)
  HISTORY_BIGRAM    = the one matching FREE_BIGRAM's encoding
  free_all          TABLE_CUR(tokens[t]) ++ (b) ++ (a)     (3073)  reported
  history_all       S[t] ++ free_all's blocks              (4097)  reported
Readers: closed-form ridge in float64, every coordinate incl. the bias
regularised alike; one lambda per arm selected on val (the frozen grid,
strict >, ties keep the smaller; grid-edge flagged); resident set at gate l
= the B largest predicted scores among that gate's 64 (ties by expert id
ascending, stable sort); hit rate as the frozen instrument counts it. Val is
read at every lambda; TEST is read at the selected lambdas only.

READOUTS at B = 16 (8 and 32 reported), paired per prompt on identical
positions, cluster bootstrap over the 30 test prompts (n_boot 2000, seed 0):
  ADDRESS-BEYOND-TOKEN (re-measured) = history_tok - free_tok    PRECONDITION
  GATE  D_eq  = history_tok - FREE_BIGRAM        (equal dims)     THE gate
  D_add       = HISTORY_BIGRAM - FREE_BIGRAM     (the address stream over
                                                  the free bigram)
  BIGRAM GAIN = FREE_BIGRAM - free_tok  (what the free previous token adds;
                per gate it IS the per-gate drop of the margin, so "driven by
                gate 0" = gate 0 has the largest per-gate gain)
  reported: history_tok - the unselected free bigram; free_all - FREE_BIGRAM;
            history_all - free_all; HISTORY_BIGRAM - history_tok.
Readings by the frozen rule: SIGNAL iff CI95 lower > 0 and point >= +0.05;
NEGATIVE iff CI95 upper < 0; else NOT-SHOWN.
LABELS (mechanical; the PRIMARY harvest's label is the label, the replication
is computed identically and reported as agrees / disagrees):
  REMEASURE-INVALID  |re-measured ADDRESS-BEYOND-TOKEN - the committed cell|
                     > 0.01 on the harvest: the re-trained readers do not
                     reproduce F-26's cell; no further label.
  FREE-HISTORY       D_eq not SIGNAL and D_add not SIGNAL.
  COMPLEMENTARY      D_eq not SIGNAL and D_add SIGNAL.
  SURVIVES           D_eq SIGNAL and D_add SIGNAL.
  READER-INCONSISTENT  D_eq SIGNAL and D_add not SIGNAL.
  INCOMPLETE         a registered arm or label cell is missing.
--conclude-from recomputes every table, CI, delta and label from the state
file (its header carries the selected encoding and the committed cell) and
refuses a payload whose stored numbers differ. Evidence files are written
with LF newlines on every platform.

Usage:
  python tools/run_prefetch_bigram.py --harvest results/real/harvest_moe \
      --out results/real/prefetch_bigram_s3.json
  python tools/run_prefetch_bigram.py --harvest results/real/harvest_moe_r \
      --out results/real/prefetch_bigram_s3_r.json
  python tools/run_prefetch_bigram.py --conclude-from results/real/prefetch_bigram_s3.json
Smoke (disclosed in the registration; refused under results/):
  python tools/run_prefetch_bigram.py --harvest results/real/harvest_moe_r \
      --only-seeds 8 --smoke-split-val --out <scratch>/bigram_smoke.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import run_prefetch_readouts as pr  # noqa: E402  (the FROZEN instrument)
from sideband.probes import load_label_space  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402

# the frozen instrument's LF-normalised sha256 (= tests/test_prefetch_landing.py INSTRUMENT_SHA256,
# = both committed stage-1 payloads' provenance.instrument_sha256)
FROZEN_INSTRUMENT_SHA256 = "8529532d4d787833cfa667a11d406ffa928c9c079836401e4930d43a6fb0e69a"


def assert_frozen_instrument(path: Path | None = None) -> str:
    """Refuse unless the frozen instrument on disk still hashes (CRLF -> LF) to the frozen sha."""
    p = Path(path) if path is not None else Path(pr.__file__)
    sha = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != FROZEN_INSTRUMENT_SHA256:
        raise SystemExit(f"{p}: sha {sha[:12]} is not the frozen instrument {FROZEN_INSTRUMENT_SHA256[:12]} — refusing")
    return sha


assert_frozen_instrument()

REGISTERED = ("OQ-9 STAGE-1 FREE-BIGRAM TWIN REGISTRATION "
              "(docs/BLUEPRINT.md, 2026-10-01 amendment; post-hoc diagnostic; NON-CRITERION)")
E, L, K, D = pr.N_EXPERTS, pr.N_GATES, pr.TOP_K, pr.D_MH
BUDGETS, LAMBDAS = pr.BUDGETS, pr.LAMBDAS
LABEL_BUDGET, MATERIAL, N_BOOT, BOOT_SEED, CHUNK = pr.LABEL_BUDGET, pr.MATERIAL, pr.N_BOOT, pr.BOOT_SEED, pr.CHUNK
HORIZON = 1
REMEASURE_TOL = 0.01
COMMITTED_KEY = f"history_tok-free_tok|B={LABEL_BUDGET}|j={HORIZON}"
COMMITTED_OF_HARVEST = {"harvest_moe": "prefetch_s3.json", "harvest_moe_r": "prefetch_s3_r.json"}
ENCODINGS = ("prev_table", "cur_table_at_prev")          # (b) first: ties keep it
ENC_SUFFIX = {"prev_table": "b", "cur_table_at_prev": "a"}
BLOCKS = {"hist": (0, D), "cur": (D, 2 * D), "prev_b": (2 * D, 3 * D), "prev_a": (3 * D, 4 * D)}
D_X = 4 * D + 1
ARM_BLOCKS = {
    "history": ("hist",),
    "free_tok": ("cur",),
    "history_tok": ("hist", "cur"),
    "free_bigram_b": ("cur", "prev_b"),
    "free_bigram_a": ("cur", "prev_a"),
    "history_bigram_b": ("hist", "cur", "prev_b"),
    "history_bigram_a": ("hist", "cur", "prev_a"),
    "free_all": ("cur", "prev_b", "prev_a"),
    "history_all": ("hist", "cur", "prev_b", "prev_a"),
}
ARMS_REQUIRED = tuple(ARM_BLOCKS)
SPLITS = pr.SPLITS


def arm_cols(arm: str) -> np.ndarray:
    cols = [np.arange(*BLOCKS[b]) for b in ARM_BLOCKS[arm]]
    return np.r_[np.concatenate(cols), D_X - 1]


def arm_dims(arm: str) -> int:
    return int(arm_cols(arm).shape[0])


def bigram_positions(lengths: np.ndarray, T: int):
    """Anchors t with t >= 1 and t + 1 < row length."""
    rows, anchors = pr.positions_horizon(lengths, HORIZON, T)
    keep = anchors >= 1
    return rows[keep], anchors[keep]


# ---------------------------------------------------------------------------
# The computation (a Stage1 subclass: mh / table_vec / masks / prompt_ids reused)
# ---------------------------------------------------------------------------

class Bigram(pr.Stage1):
    """Fits the two tables and the one bigram Gram; evaluates every arm on the
    bigram positions of a split. lambdas as the frozen grid unless a test grid
    is passed."""

    def __init__(self, data: pr.S3Data, label_of_token: np.ndarray, n_classes: int, lambdas=LAMBDAS, chunk: int = CHUNK):
        super().__init__(data, label_of_token, n_classes, budgets=BUDGETS, horizons=(HORIZON,), leads=(),
                         lambdas=lambdas, chunk=chunk)
        self.encoding_selected: str | None = None

    # ----- tables ---------------------------------------------------------------
    def _count_table(self, key_tok: np.ndarray, prompt: np.ndarray, sl: np.ndarray):
        """(table (vocab, L, E) int64, pair_keys, pair_counts (P, L, E) int32) from
        key tokens, their prompts and the target slots — the frozen construction."""
        gate = np.arange(L)[None, :, None]
        flat = (key_tok[:, None, None] * D + gate * E + sl).ravel()
        table = np.bincount(flat, minlength=self.vocab * D).reshape(self.vocab, L, E).astype(np.int64)
        pair_key = prompt * self.vocab + key_tok
        pair_keys, inv = np.unique(pair_key, return_inverse=True)
        flat_p = (inv.reshape(-1)[:, None, None] * D + gate * E + sl).ravel()
        pair_counts = np.bincount(flat_p, minlength=pair_keys.shape[0] * D).reshape(pair_keys.shape[0], L, E).astype(np.int32)
        if not np.array_equal(pair_counts.sum(axis=0), table.sum(axis=0)):
            raise SystemExit("internal: a (prompt, token) pair table does not sum to its token table")
        return table, pair_keys, pair_counts

    def fit_tables(self) -> None:
        d = self.d
        train = self.masks["train"]
        # TABLE_CUR exactly as the frozen Stage1.fit builds it: j = 1 train positions, t = 0 included
        rows, anchors = pr.restrict(*pr.positions_horizon(d.lengths, HORIZON, d.T), train)
        self.n_positions["horizon1/train"] = int(rows.shape[0])
        sl = d.slots[rows, anchors + 1].astype(np.int64)
        self.token_table, self.pair_keys, self.pair_counts = self._count_table(
            d.tokens[rows, anchors], d.prompt_idx[rows], sl)
        counts_h1 = self.token_table.sum(axis=0).astype(np.float64)
        self.marginal_freq = counts_h1 / np.maximum(counts_h1.sum(axis=1, keepdims=True), 1.0)
        # TABLE_PREV: S[t+1] keyed on tokens[t-1] over the bigram train positions
        rows, anchors = pr.restrict(*bigram_positions(d.lengths, d.T), train)
        self.n_positions["bigram/train"] = int(rows.shape[0])
        sl = d.slots[rows, anchors + 1].astype(np.int64)
        self.prev_table, self.prev_pair_keys, self.prev_pair_counts = self._count_table(
            d.tokens[rows, anchors - 1], d.prompt_idx[rows], sl)

    def prev_table_vec(self, tok_prev: np.ndarray, prompt: np.ndarray | None = None) -> np.ndarray:
        """(N, 1024) TABLE_PREV(tok_prev); at TRAIN rows (prompt given) every
        contribution of the row's own prompt under this key is removed first
        (leave-one-prompt-out), the frozen table_vec's rule on the prev table."""
        tok_prev = np.asarray(tok_prev, dtype=np.int64)
        c = self.prev_table[tok_prev].astype(np.float64)
        if prompt is not None:
            pk = np.asarray(prompt, dtype=np.int64) * self.vocab + tok_prev
            idx = np.searchsorted(self.prev_pair_keys, pk)
            idx_c = np.minimum(idx, self.prev_pair_keys.shape[0] - 1)
            if not np.all(self.prev_pair_keys[idx_c] == pk):
                raise SystemExit("internal: a train row's (prompt, previous token) pair is missing from the prev pair table")
            c -= self.prev_pair_counts[idx_c].astype(np.float64)
            if c.min() < 0:
                raise SystemExit("internal: leave-one-prompt-out removed a contribution the prev table never counted")
        tot = c.sum(axis=2, keepdims=True)
        freq = np.where(tot > 0, c / np.maximum(tot, 1.0), self.marginal_freq[None, :, :])
        return freq.reshape(tok_prev.shape[0], D)

    def design(self, rows, anchors, lopo: bool = False):
        d = self.d
        prompt = d.prompt_idx[rows] if lopo else None
        tok, tokp = d.tokens[rows, anchors], d.tokens[rows, anchors - 1]
        blocks = [self.mh(rows, anchors), self.table_vec(tok, prompt),
                  self.prev_table_vec(tokp, prompt), self.table_vec(tokp, prompt)]
        return pr.with_bias(np.hstack(blocks)), self.mh(rows, anchors + HORIZON)

    def table_coverage(self) -> dict:
        """Per split, over the bigram positions: share of positions whose key has
        no train count in TABLE_CUR at tokens[t], in TABLE_PREV at tokens[t-1]
        and in TABLE_CUR at tokens[t-1] (the marginal fallback); on train also
        each table's singleton-key share."""
        d = self.d
        out = {}
        for split in SPLITS:
            rows, anchors = pr.restrict(*bigram_positions(d.lengths, d.T), self.masks[split])
            if rows.size == 0:
                out[split] = {"n": 0}
                continue
            c_cur = self.token_table[d.tokens[rows, anchors]].sum(axis=(1, 2))
            c_prev = self.prev_table[d.tokens[rows, anchors - 1]].sum(axis=(1, 2))
            c_cur_at_prev = self.token_table[d.tokens[rows, anchors - 1]].sum(axis=(1, 2))
            entry = {"n": int(rows.shape[0]),
                     "zero_count_share_cur": float((c_cur == 0).mean()),
                     "zero_count_share_prev": float((c_prev == 0).mean()),
                     "zero_count_share_cur_at_prev": float((c_cur_at_prev == 0).mean())}
            if split == "train":
                entry["singleton_key_share_cur"] = float((c_cur == L * K).mean())
                entry["singleton_key_share_prev"] = float((c_prev == L * K).mean())
            out[split] = entry
        return out

    # ----- fit -------------------------------------------------------------------
    def fit(self) -> None:
        self.fit_tables()
        d = self.d
        rows, anchors = pr.restrict(*bigram_positions(d.lengths, d.T), self.masks["train"])
        G = np.zeros((D_X, D_X)); C = np.zeros((D_X, D))
        for s in range(0, rows.shape[0], self.chunk):
            X, Y = self.design(rows[s:s + self.chunk], anchors[s:s + self.chunk], lopo=True)
            G += X.T @ X
            C += X.T @ Y
        self.G, self.C = G, C
        self.W = {}
        for arm in ARMS_REQUIRED:
            F = arm_cols(arm)
            Gs, Cs = G[np.ix_(F, F)], C[F]
            for lam in self.lambdas:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)

    # ----- evaluate --------------------------------------------------------------
    def evaluate(self, split: str, lambdas_of_arm: dict | None = None) -> dict:
        """out[(arm, B, lam)] = (hits (P, L), needed (P, L)) over the bigram
        positions of the split; every lambda unless lambdas_of_arm restricts."""
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = pr.restrict(*bigram_positions(d.lengths, d.T), self.masks[split])
        self.n_positions[f"bigram/{split}"] = int(rows.shape[0])
        maxB = max(self.budgets)
        out: dict = {}

        def acc(key, h, n):
            if key in out:
                out[key][0][...] += h; out[key][1][...] += n
            else:
                out[key] = (h.copy(), n.copy())

        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            pp = d.prompt_idx[r]
            X, Y = self.design(r, a)
            yy = Y.reshape(r.shape[0], L, E)
            n = pr.per_prompt(np.full((r.shape[0], L), K, np.int64), pp, pids)
            for arm in ARMS_REQUIRED:
                Xa = X[:, arm_cols(arm)]
                lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                for lam in lams:
                    sc = (Xa @ self.W[(arm, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(sc, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        acc((arm, B, lam), pr.per_prompt(h, pp, pids), n)
        return out

    # ----- selection on val -----------------------------------------------------------
    def select(self, val: dict) -> None:
        def pooled(arm, lam):
            h, n = val[(arm, LABEL_BUDGET, lam)]
            return float(h.sum() / n.sum()) if n.sum() > 0 else float("nan")

        for arm in ARMS_REQUIRED:
            best_lam, best, table = None, -np.inf, {}
            for lam in self.lambdas:
                v = pooled(arm, lam)
                table[str(lam)] = v
                if v > best:                           # strict: ties keep the smaller lambda
                    best, best_lam = v, lam
            self.val_table[arm] = table
            self.lambda_selected[arm] = best_lam
            self.grid_edge[arm] = bool(best_lam in (self.lambdas[0], self.lambdas[-1]))
        # the FREE_BIGRAM encoding: the better val-best of the two 2049-dim free arms; ties keep (b)
        self.encoding_selected = select_encoding(self.val_table, self.lambda_selected)

    def state_rows(self, test: dict) -> list[dict]:
        pids = self.prompt_ids["test"]
        rows = []
        for (arm, B, lam), (h, n) in test.items():
            if lam != self.lambda_selected[arm]:
                continue
            for pi, pid in enumerate(pids):
                for g in range(L):
                    if n[pi, g] == 0:
                        continue
                    rows.append({"arm": arm, "budget": B, "key": HORIZON, "depth": None, "gate": g,
                                 "prompt_idx": int(pid), "hits": int(h[pi, g]), "needed": int(n[pi, g])})
        return pr.sort_rows(rows)


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes it from the state file)
# ---------------------------------------------------------------------------

# The pinned sentences use the frozen NOT-SHOWN wording ("no material margin ... is shown"): a delta that is
# CI-positive below the +0.05 floor is NOT-SHOWN, never "no better" or "reproduced" (critic design round, B1).
# The landing text quotes D_eq, D_add and BIGRAM GAIN with their CIs beside whichever sentence applies.
_AT = f"at this reader (B = {LABEL_BUDGET}, j = {HORIZON})"
SENTENCES = {
    "FREE-HISTORY": (f"no material margin (at or above +{MATERIAL}) of the address block over an equal-dims free "
                     f"bigram block is shown, and no material margin of the address stream over the free bigram is "
                     f"shown, {_AT}"),
    "COMPLEMENTARY": (f"no material margin (at or above +{MATERIAL}) of the address block over an equal-dims free "
                      f"bigram block is shown, while the address stream adds a material margin over the free bigram, "
                      f"{_AT}"),
    "SURVIVES": (f"the address block adds a material margin over an equal-dims free bigram block and the address "
                 f"stream adds a material margin over the free bigram {_AT}"),
    "READER-INCONSISTENT": (f"the equal-dims comparison reads a material margin while the union reader does not; no "
                            f"sideband sentence is written {_AT}"),
    "REMEASURE-INVALID": ("the re-trained readers do not reproduce the committed ADDRESS-BEYOND-TOKEN cell within "
                          "the tolerance; the run is void and its deltas are numbers, not readings"),
    "INCOMPLETE": None,
}
OUT_OF_HARVEST = {"harvest_moe": "prefetch_bigram_s3.json", "harvest_moe_r": "prefetch_bigram_s3_r.json"}


def free_arm_of(encoding: str) -> str:
    return f"free_bigram_{ENC_SUFFIX[encoding]}"


def history_arm_of(encoding: str) -> str:
    return f"history_bigram_{ENC_SUFFIX[encoding]}"


def other_encoding(encoding: str) -> str:
    return [e for e in ENCODINGS if e != encoding][0]


def conclude(rows: list[dict], encoding: str, committed_abt: float | None,
             n_boot: int = N_BOOT, seed: int = BOOT_SEED, budgets=BUDGETS) -> dict:
    if encoding not in ENCODINGS:
        raise SystemExit(f"unknown encoding {encoding!r}")
    rows = pr.sort_rows(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    groups = pr._group(rows)
    tables: dict = {}
    for (arm, B, key, depth), gates in groups.items():
        name = f"{arm}|B={B}"
        entry = {"arm": arm, "budget": B, "dims": arm_dims(arm) if arm in ARM_BLOCKS else None, "per_gate": {}}
        for g in sorted(gates):
            h, n = pr._arrays(gates[g], prompts)
            entry["per_gate"][str(g)] = pr._point_ci(h, n, n_boot, seed)
        H, N = pr._pooled(gates, prompts)
        entry["all"] = pr._point_ci(H, N, n_boot, seed)
        tables[name] = entry

    def pooled_of(arm, B):
        gates = groups.get((arm, B, HORIZON, None))
        return None if gates is None else pr._pooled(gates, prompts)

    def delta_of(a, b, B):
        pa, pb = pooled_of(a, B), pooled_of(b, B)
        if pa is None or pb is None:
            return None
        if not np.array_equal(pa[1], pb[1]):
            raise SystemExit(f"pairing violated: {a} and {b} have different per-prompt trials at B={B}")
        return pr._delta(pa[0], pb[0], pa[1], n_boot, seed)

    free, hist, free_other = free_arm_of(encoding), history_arm_of(encoding), free_arm_of(other_encoding(encoding))
    # every arm present must share history_tok's per-prompt trials at every budget (the unselected arms too)
    for B in budgets:
        ref = pooled_of("history_tok", B)
        if ref is None:
            continue
        for arm in ARMS_REQUIRED:
            pa = pooled_of(arm, B)
            if pa is not None and not np.array_equal(pa[1], ref[1]):
                raise SystemExit(f"pairing violated: {arm} and history_tok have different per-prompt trials at B={B}")
    deltas: dict = {}
    for B in budgets:
        for name, a, b in (("address_beyond_token_re", "history_tok", "free_tok"),
                           ("gate_eq", "history_tok", free),
                           ("address_beyond_bigram", hist, free),
                           ("bigram_gain", free, "free_tok"),
                           ("gate_eq_unselected", "history_tok", free_other),
                           ("free_all-free_bigram", "free_all", free),
                           ("history_all-free_all", "history_all", "free_all"),
                           ("history_bigram-history_tok", hist, "history_tok"),
                           ("history_tok-history", "history_tok", "history"),
                           ("free_bigram_b-free_bigram_a", "free_bigram_b", "free_bigram_a")):
            deltas[f"{name}|B={B}"] = delta_of(a, b, B)
    deltas = {k: v for k, v in deltas.items() if v is not None}

    present = {r["arm"] for r in rows}
    missing = [a for a in ARMS_REQUIRED if a not in present]
    need = [f"{n}|B={LABEL_BUDGET}" for n in ("address_beyond_token_re", "gate_eq", "address_beyond_bigram", "bigram_gain")]
    missing_cells = [k for k in need if k not in deltas]
    labels: dict = {"encoding": encoding, "free_bigram_arm": free, "history_bigram_arm": hist,
                    "missing_arms": missing, "missing_label_cells": missing_cells,
                    "committed_address_beyond_token": committed_abt, "remeasure_tolerance": REMEASURE_TOL}
    if missing or missing_cells:
        labels.update({"label": "INCOMPLETE", "sentence": None, "remeasure_ok": None,
                       "gate_eq_reading": None, "address_beyond_bigram_reading": None})
        return {"tables": tables, "deltas": deltas, "labels": labels}
    abt = deltas[f"address_beyond_token_re|B={LABEL_BUDGET}"]
    labels["address_beyond_token_re"] = abt
    if committed_abt is None:
        labels["remeasure_ok"] = None                      # smoke / test: not applicable
        labels["remeasure_gap"] = None
    else:
        labels["remeasure_gap"] = float(abt["delta"] - committed_abt)
        labels["remeasure_ok"] = bool(abs(labels["remeasure_gap"]) <= REMEASURE_TOL)
    eq, add, gain = (deltas[f"{n}|B={LABEL_BUDGET}"] for n in ("gate_eq", "address_beyond_bigram", "bigram_gain"))
    labels["gate_eq"] = eq; labels["address_beyond_bigram"] = add; labels["bigram_gain"] = gain
    labels["gate_eq_reading"] = pr._reading(eq)
    labels["address_beyond_bigram_reading"] = pr._reading(add)
    labels["bigram_gain_reading"] = pr._reading(gain)
    # per-gate bigram gain at the label budget (= the per-gate drop of the margin); the critic's "driven by gate 0"
    tf, tt = tables[f"{free}|B={LABEL_BUDGET}"]["per_gate"], tables[f"free_tok|B={LABEL_BUDGET}"]["per_gate"]
    per_gate_gain = {g: float(tf[g]["point"] - tt[g]["point"]) for g in tf}
    labels["per_gate_bigram_gain"] = per_gate_gain
    gmax = max(per_gate_gain, key=lambda g: (per_gate_gain[g], -int(g)))   # an exact float tie keeps the lower gate id
    labels["largest_gain_gate"] = int(gmax)
    labels["driven_by_gate0"] = bool(int(gmax) == 0)
    # gate 0's share of the summed per-gate gain (every gate has equal trials, so the pooled gain is the mean of
    # the per-gate gains): the critic's bound — gate 0 can add at most (1 - free_tok at gate 0) / 16 to the pooled gain
    total_gain = float(sum(per_gate_gain.values()))
    labels["gate0_gain_share"] = float(per_gate_gain["0"] / total_gain) if total_gain > 0 else None
    labels["gate0_gain_cap"] = float((1.0 - tt["0"]["point"]) / L)
    if labels["remeasure_ok"] is False:
        lab = "REMEASURE-INVALID"
    else:
        e_sig, a_sig = labels["gate_eq_reading"] == "SIGNAL", labels["address_beyond_bigram_reading"] == "SIGNAL"
        lab = ("SURVIVES" if (e_sig and a_sig) else "COMPLEMENTARY" if (not e_sig and a_sig)
               else "FREE-HISTORY" if (not e_sig and not a_sig) else "READER-INCONSISTENT")
    labels["label"] = lab
    labels["sentence"] = SENTENCES[lab]
    labels["rule"] = (f"readings SIGNAL iff CI95 lower > 0 and delta >= +{MATERIAL}, NEGATIVE iff CI95 upper < 0, else "
                      f"NOT-SHOWN, at B={LABEL_BUDGET}, j={HORIZON}, on the bigram positions (t >= 1); PRECONDITION "
                      f"|re-measured history_tok - free_tok minus the committed cell| <= {REMEASURE_TOL} else "
                      f"REMEASURE-INVALID; D_eq = history_tok - FREE_BIGRAM (equal dims, encoding selected on val); "
                      f"D_add = HISTORY_BIGRAM - FREE_BIGRAM; SURVIVES iff both SIGNAL, COMPLEMENTARY iff only D_add, "
                      f"FREE-HISTORY iff neither, READER-INCONSISTENT iff only D_eq; the primary harvest's label is the "
                      f"label; NON-CRITERION, one pinned consequence (a dated STATUS line under F-26)")
    return {"tables": tables, "deltas": deltas, "labels": labels}


# ---------------------------------------------------------------------------
# Provenance, I/O, CLI
# ---------------------------------------------------------------------------

def _write_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def committed_cell(harvest_dir: Path, committed_arg: str | None, smoke: bool, out_under_results: bool) -> dict | None:
    """The committed stage-1 payload's ADDRESS-BEYOND-TOKEN cell for this harvest
    (path, sha, delta, freeze commit), or None for a smoke / an explicit 'none'
    outside results/. A smoke never reads the cell: its re-split rows are not
    the committed cell's rows, so the precondition is not applicable to it."""
    if smoke:
        return None
    if committed_arg is not None and committed_arg.lower() == "none":
        if out_under_results and not smoke:
            raise SystemExit("a registered run must read the committed stage-1 payload (--committed none is refused under results/)")
        return None
    explicit = committed_arg is not None
    if not explicit:
        name = COMMITTED_OF_HARVEST.get(Path(harvest_dir).name)
        if name is None:
            if not out_under_results:
                return None
            raise SystemExit(f"no committed stage-1 payload is known for harvest {Path(harvest_dir).name}; pass --committed")
        path = ROOT / "results" / "real" / name
    else:
        path = Path(committed_arg)
        if out_under_results and path.resolve() != (ROOT / "results" / "real" / COMMITTED_OF_HARVEST.get(Path(harvest_dir).name, "")).resolve():
            raise SystemExit("under results/ the committed payload must be the registered one for this harvest")
    if not path.exists():
        if not explicit and not out_under_results:
            return None                                   # the derived default is absent on this checkout; no cell
        raise SystemExit(f"committed stage-1 payload {path} not found")
    return read_committed_cell(path)


def read_committed_cell(path: Path) -> dict:
    """The ADDRESS-BEYOND-TOKEN cell of a committed stage-1 payload, with the bytes it was read from."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("registered") != pr.REGISTERED:
        raise SystemExit(f"{path} is not an OQ-9 stage-1 payload")
    cell = payload["conclusion"]["deltas"][COMMITTED_KEY]
    rp = path.resolve()
    rel = rp.relative_to(ROOT.resolve()).as_posix() if rp.is_relative_to(ROOT.resolve()) else rp.as_posix()
    return {"path": rel, "sha256": pr._sha(path), "git_commit": payload["provenance"]["git_commit"],
            "instrument_sha256": payload["provenance"]["instrument_sha256"], "key": COMMITTED_KEY,
            "delta": float(cell["delta"]), "lo": float(cell["lo"]), "hi": float(cell["hi"])}


def select_encoding(val_table: dict, lambda_selected: dict) -> str:
    """The FREE_BIGRAM encoding from a val table: the better val-best of the two 2049-dim free arms, ties to
    (b). Used at run time and re-derived by --conclude-from from the payload's own provenance."""
    best_enc, best = None, -np.inf
    for enc in ENCODINGS:
        arm = free_arm_of(enc)
        v = val_table[arm][str(lambda_selected[arm])]
        if v > best:
            best, best_enc = v, enc
    return best_enc


def run(args) -> dict:
    started = time.time()
    frozen_sha = assert_frozen_instrument()
    only = [int(s) for s in args.only_seeds.split(",")] if args.only_seeds else None
    smoke = bool(args.smoke_split_val or only is not None)
    out = Path(args.out)
    under = pr._under_results(out)
    if smoke and under:
        raise SystemExit("a smoke (--only-seeds / --smoke-split-val) may not write under results/")
    lambdas = tuple(float(x) for x in args.lambdas.split(",")) if getattr(args, "lambdas", None) else LAMBDAS
    if lambdas != LAMBDAS and not smoke and under:
        raise SystemExit("a non-registered lambda grid may not write under results/")
    state_path = Path(str(out) + ".state.jsonl")
    meta_path = Path(str(out)[:-5] + ".meta.json") if str(out).endswith(".json") else Path(str(out) + ".meta.json")
    if under:
        for p in (out, state_path, meta_path):
            if p.exists():
                raise SystemExit(f"{p} exists: a registered payload is never overwritten (delete it by hand if that is the intent)")
        want = OUT_OF_HARVEST.get(Path(args.harvest).name)
        if want is None or out.resolve() != (ROOT / "results" / "real" / want).resolve():
            raise SystemExit(f"under results/ the out path for harvest {Path(args.harvest).name} must be "
                             f"results/real/{want or '<unknown harvest>'}")
    committed = committed_cell(Path(args.harvest), args.committed, smoke, under)
    data = pr.S3Data(args.harvest, only_seeds=only, smoke_split_val=args.smoke_split_val)
    label_of_token, n_classes = load_label_space(args.buckets, args.glue)
    bg = Bigram(data, label_of_token, n_classes, lambdas=lambdas)
    bg.fit()
    val = bg.evaluate("val")
    bg.select(val)
    test = bg.evaluate("test", lambdas_of_arm=bg.lambda_selected)
    rows = bg.state_rows(test)
    committed_abt = None if committed is None else committed["delta"]
    conclusion = conclude(rows, bg.encoding_selected, committed_abt)
    git_commit, tracked = pr._git()
    prov = {
        "registered": REGISTERED,
        "git_commit": git_commit,
        "git_status_tracked": tracked,
        "instrument_sha256": pr._sha(Path(__file__)),
        "frozen_instrument": {"path": "tools/run_prefetch_readouts.py", "sha256_lf": frozen_sha},
        "harvest_dir": str(args.harvest),
        "harvest_npz_sha256": data.npz_shas,
        "seeds": data.seeds,
        "smoke": smoke,
        "smoke_split_val": bool(args.smoke_split_val),
        "committed_cell": committed,
        "label_space": {"buckets": str(args.buckets), "buckets_sha256": pr._sha(args.buckets),
                        "glue": str(args.glue), "glue_sha256": pr._sha(args.glue), "n_classes": int(n_classes)},
        "constants": {"budgets": list(BUDGETS), "horizon": HORIZON, "lambdas": list(lambdas), "label_budget": LABEL_BUDGET,
                      "material": MATERIAL, "remeasure_tolerance": REMEASURE_TOL, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
                      "chunk": CHUNK, "encodings": list(ENCODINGS), "arm_dims": {a: arm_dims(a) for a in ARMS_REQUIRED}},
        "n_positions": bg.n_positions,
        "n_test_prompts": int(bg.prompt_ids["test"].shape[0]),
        "table_coverage": bg.table_coverage(),
        "encoding_selected": bg.encoding_selected,
        "lambda_selected": {k: float(v) for k, v in bg.lambda_selected.items()},
        "lambda_grid_edge": bg.grid_edge,
        "val_table": bg.val_table,
        "args": redact_args(vars(args)),
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "started_unix": started,
        "runtime_s": time.time() - started,
    }
    payload = {"registered": REGISTERED, "provenance": prov, "conclusion": conclusion, "n_state_rows": len(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    header = {"state_header": True, "registered": REGISTERED, "harvest_npz_sha256": data.npz_shas, "smoke": smoke,
              "encoding": bg.encoding_selected, "committed_cell": committed}
    _write_lf(state_path, "".join(json.dumps(x) + "\n" for x in [header] + rows))
    _write_lf(out, json.dumps(payload, indent=1))
    _write_lf(meta_path, json.dumps(prov, indent=1))
    print_summary(payload)
    return payload


def conclude_from(payload_path: Path) -> dict:
    assert_frozen_instrument()
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if payload.get("registered") != REGISTERED:
        raise SystemExit("payload is not a free-bigram twin payload")
    header, rows = pr.load_state(Path(str(payload_path) + ".state.jsonl"))
    if header["harvest_npz_sha256"] != payload["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("state header harvest shas differ from the payload's")
    if header.get("encoding") != payload["provenance"]["encoding_selected"]:
        raise SystemExit("state header encoding differs from the payload's")
    if header.get("committed_cell") != payload["provenance"]["committed_cell"]:
        raise SystemExit("state header committed cell differs from the payload's")
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit("state row count differs from the payload's")
    prov = payload["provenance"]
    # the encoding is RE-DERIVED from the payload's own val table, never trusted from the header
    if select_encoding(prov["val_table"], prov["lambda_selected"]) != header["encoding"]:
        raise SystemExit("the state header's encoding is not the one the payload's val table selects")
    cell = header.get("committed_cell")
    if cell is not None:
        # the committed cell is RE-READ from the committed payload when it is present: same bytes, same delta
        cpath = ROOT / cell["path"] if not Path(cell["path"]).is_absolute() else Path(cell["path"])
        if cpath.exists():
            fresh = read_committed_cell(cpath)
            if fresh["sha256"] != cell["sha256"] or fresh["delta"] != cell["delta"]:
                raise SystemExit(f"the committed stage-1 payload {cell['path']} is not the one this run read "
                                 f"(sha {cell['sha256'][:12]} -> {fresh['sha256'][:12]})")
        else:
            print(f"note: committed stage-1 payload {cell['path']} not present; its cell is taken from the header")
    got = conclude(rows, header["encoding"], None if cell is None else cell["delta"])
    if json.dumps(got, sort_keys=True) != json.dumps(payload["conclusion"], sort_keys=True):
        raise SystemExit("RECOMPUTE MISMATCH: the state file does not reproduce the payload's conclusion")
    tag = " (SMOKE — not evidence)" if payload["provenance"].get("smoke") else ""
    print(f"conclude-from: state file reproduces the payload exactly{tag}")
    print_summary(payload)
    return got


def print_summary(payload: dict) -> None:
    c = payload["conclusion"]; lab = c["labels"]; prov = payload["provenance"]
    print(f"LABEL: {lab.get('label')}   (smoke={prov.get('smoke')}; encoding={lab.get('encoding')})")
    if lab.get("label") == "INCOMPLETE":
        print("missing arms:", lab["missing_arms"], "missing label cells:", lab["missing_label_cells"]); return
    ca = lab.get("committed_address_beyond_token")
    print(f"  committed ADDRESS-BEYOND-TOKEN {ca if ca is None else format(ca, '+.4f')}   re-measured "
          f"{lab['address_beyond_token_re']['delta']:+.4f} [{lab['address_beyond_token_re']['lo']:+.4f}, "
          f"{lab['address_beyond_token_re']['hi']:+.4f}]   remeasure_ok={lab['remeasure_ok']}")
    for name in ("gate_eq", "address_beyond_bigram", "bigram_gain"):
        d = lab[name]
        print(f"  {name:22s} {lab[name + '_reading']:10s} delta {d['delta']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]")
    share = lab.get("gate0_gain_share")
    print(f"  largest per-gate bigram gain at gate {lab['largest_gain_gate']} (driven_by_gate0={lab['driven_by_gate0']}; "
          f"gate 0 share of the summed gain {share if share is None else format(share, '.4f')}; "
          f"gate 0 cap on the pooled gain {lab['gate0_gain_cap']:.4f})")
    print(f"  sentence: {lab['sentence']}")
    for B in BUDGETS:
        for arm in ARMS_REQUIRED:
            t = c["tables"].get(f"{arm}|B={B}")
            if t:
                a = t["all"]; print(f"  B={B:2d} {arm:17s} {a['point']:.4f} [{a['ci_lo']:.4f}, {a['ci_hi']:.4f}]")
    for B in BUDGETS:
        for name in ("gate_eq", "address_beyond_bigram", "bigram_gain", "gate_eq_unselected", "free_all-free_bigram",
                     "history_all-free_all"):
            d = c["deltas"].get(f"{name}|B={B}")
            if d:
                print(f"  B={B:2d} {name:22s} {d['delta']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]")
    print("  lambda:", prov.get("lambda_selected"))
    print("  grid-edge:", prov.get("lambda_grid_edge"))
    print("  coverage:", prov.get("table_coverage"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default=str(ROOT / "results" / "real" / "harvest_moe"))
    ap.add_argument("--out", default=str(ROOT / "results" / "real" / "prefetch_bigram_s3.json"))
    ap.add_argument("--buckets", default=str(pr.BUCKETS16))
    ap.add_argument("--glue", default=str(pr.GLUE16))
    ap.add_argument("--committed", default=None,
                    help="the committed stage-1 payload whose ADDRESS-BEYOND-TOKEN cell is the precondition "
                         "(default: derived from the harvest name; 'none' only outside results/)")
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

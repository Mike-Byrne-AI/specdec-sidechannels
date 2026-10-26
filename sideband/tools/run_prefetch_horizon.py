#!/usr/bin/env python
"""tools/run_prefetch_horizon.py — OQ-9 STAGE-1 POST-HOC DIAGNOSTIC: the HORIZON READ at the R2
encoding (K-6 lead-time pricing): does the address stream add a material margin over the forward's
own final-norm state plus two tokens' smoothed routing profiles at horizons 2, 3 and 4?

Registered 2026-10-04 as a dated AMENDMENT to the R2 block in docs/BLUEPRINT.md ("OQ-9 STAGE-1
HORIZON READ REGISTRATION"), written before any readout of it ran on either S3 harvest.
NON-CRITERION for every finding's mechanical label; it executes two pinned consequences, a dated
STATUS line under F-26 (the fourth) and a dated K-6 STATUS line. It is NOT a rung on the
horizon-1 margin (R2 closed that ladder): the horizon-1 cells are REPRODUCED here as the
precondition, never re-read. CPU only; numpy only — nothing in this file imports torch,
transformers or safetensors.

WHY. Prefetch pays only if the resident set is chosen before the fetch latency elapses, and that
is a lead-time question. Every rung from F-26 through R2 was read at horizon 1 (the next
forward). F-26's post-hoc reading (2), unregistered, is the one thread that points the other
way: at the one-token free arm the token's margin over the cache decayed across horizons 1..4
while the address margin stayed near its horizon-1 value. R2's hidden-state arm, the one that
absorbed the address stream at horizon 1, was never read past it. This read prices that cell.

THE FROZEN INSTRUMENTS. tools/run_prefetch_r2.py (sha eaf671fdb9d6..., attested by both
committed R2 payloads) is imported by bare module name and NEVER edited; this file refuses to
run unless its LF-normalised bytes still hash to that sha, and its own import-time assertions
cover the stratified tool (39a6cd587492...), the twin (10599fa98c27...) and the stage-1 parent
(8529532d4d78...). R2's class is reused for the tables, the leave-one-prompt-out reads, the
hidden block, the smoothed blocks, the Gram-block algebra and the ridge readers; this file
parametrises the HORIZON: the positions (t >= 1 and t + j < row length), the target S[t+j], the
per-horizon Gram, the per-horizon val selection and the per-horizon evaluation.

INDEX CONVENTION (the frozen one): forward t has INPUT tokens[t-1], OUTPUT p_t, routing S[t] and
final-norm state hidden[t]; tokens[t] is sampled from p_t. At anchor t the decoder holds S[t],
tokens[t], tokens[t-1] and hidden[t]; the target at horizon j is S[t+j], the routing of the
forward j steps on. FEATURES STAY AT TIME t; the TOKEN TABLES ARE HORIZON-MATCHED: at horizon j
TABLE_CUR^j(tokens[t]) holds the train frequencies of S[t+j] given tokens[t] (over t >= 0, t + j <
length, the frozen construction with the target moved) and TABLE_PREV^j(tokens[t-1]) those of
S[t+j] given tokens[t-1] (over the horizon's positions), both read leave-one-prompt-out at train
rows exactly as the twin reads its tables, with the horizon's own marginal as the twin arms'
fallback; SMOOTH_k^j is the same family on those counts with the REPLAY as its prior (the replay
estimates the forward a token feeds, i.e. horizon 1, so at j >= 2 it is a prior misaligned by
j - 1 forwards, as TABLE_PREV's already is at j = 1; k is selected per horizon, so a prior that
hurts costs the free arm at selection, and the k = 0 end is the horizon's own table). At j = 1
every table is R2's table. The hidden block H(t) and the address block S[t] have no
horizon-matched form (they are the forward's state, read linearly at every horizon, as at j = 1):
the ladder's standing shape, the free side a fitted lookup of the token, the address side a
linear read. Coverage (the two unions) is read from the horizon's own train tables.

DESIGN per horizon j: the R2 Gram statements accumulated over the horizon's TRAIN positions
(t >= 1, t + j < length; at j = 1 exactly R2's positions, chunks and statements) with Y =
S[t+j] and the horizon's tables; the hidden block's train support, moments and 1024 directions
are fit ONCE on the horizon-1 train positions (R2's) and shared by every horizon. k and lambda
for free_r2 selected jointly on the horizon's pooled VAL positions by R2's rule, every other R2
arm's lambda on val at that k; the twin's arms' lambdas on val too (stage 1's per-horizon rule).
AT HORIZON 1 every selection is TAKEN from the committed R2 payload (k, the twin's lambdas, the R2
arms' lambdas), so the horizon-1 arms ARE R2's readers and their rows are R2's rows (REPRODUCE);
what val would re-select at horizon 1 is computed and recorded beside it (a consistency datum).
ARMS. Horizon 1: R2's nineteen (the REPRODUCE set) plus marginal. Horizons 2..4, twelve:
  marginal           bias only — the train marginal's top-B, the floor of the horizon      (1)
  history            S[t]                                                             (1025)
  free_tok           TABLE_CUR(tokens[t])                                             (1025)
  history_tok        S[t] ++ TABLE_CUR                                                (2049)
  FREE_BIGRAM        TABLE_CUR ++ TABLE_PREV (the twin's selected encoding)           (2049)
  HISTORY_BIGRAM     S[t] ++ FREE_BIGRAM's blocks                                     (3073)
  free_r2            SMOOTH_k*(tokens[t]) ++ SMOOTH_k*(tokens[t-1])                   (2049)
  history_tok_r2     S[t] ++ SMOOTH_k*(tokens[t])                                     (2049)
  history_bigram_r2  S[t] ++ free_r2's blocks                                         (3073)
  h_only             H(t)                                                             (1025)
  free_h             free_r2's blocks ++ H(t)      the strongest free arm R2 built    (3073)
  history_all_h      S[t] ++ free_h's blocks                                          (4097)
STATE ROWS: one per (arm, budget, gate, test prompt, HORIZON, SCOPE) with scope the two coverage
unions of the stratified read (covered / fallback, read from the horizon's OWN train tables; the
meta's strata_counts and table_coverage are the horizon-1 records); ALL is their sum.

READOUTS at B = 16 (8 and 32 reported), paired per prompt on identical positions within a
(horizon, scope), cluster bootstrap over the 30 test prompts (n_boot 2000, seed 0), readings by
the frozen rule (SIGNAL iff CI95 lower > 0 and point >= +0.05; NEGATIVE iff CI95 upper < 0; else
NOT-SHOWN):
  PRECONDITION REPRODUCE  every (arm, budget, gate, prompt) row of the committed R2 state file,
                          summed over its six strata into the two unions, equals this read's
                          horizon-1 row, hits AND needed (EXACT; hits-only mismatches on at most
                          0.1% of those rows within +-1 hit NEAR, said in words; else INVALID,
                          void); IDENTITY: this read's horizon-1 D_eq^H, D_add^H, the dilution
                          anchor and free_h - free_r2 on ALL, CI included, equal the R2 payload's
                          cells to 1e-12.
  PER HORIZON j in {2, 3, 4}, on ALL:
    D_eq^H(j)  = history_bigram_r2 - free_h       (3073 against 3073; S[t] against H(t))
    D_add^H(j) = history_all_h - free_h           (the address stream over the strongest free arm R2 built)
    anchor(j)  = history_all_h - history_bigram_r2 (= D_add^H - D_eq^H, the dilution anchor)
    READER GUARD(j): free_h - free_r2 or the anchor NEGATIVE on ALL (adding H degraded a reader)
    Q(j) by R2's Q2 rule: H-SURVIVES (both SIGNAL) / H-COMPLEMENTARY (only D_add^H) / H-ABSORBS
    (neither) / H-INCONSISTENT (only D_eq^H; cause "reader" / "floor straddle" / "neither")
    FLOOR STRADDLE flags on both readings; a straddle selects the "not settled at this power"
    sentence for that horizon.
  REPORTED per horizon and scope: ABT = history_tok - free_tok (F-26's reading at this horizon),
    D_eq = history_tok - FREE_BIGRAM and D_add = HISTORY_BIGRAM - FREE_BIGRAM (the twin's),
    D_eq^R2 = history_tok_r2 - free_r2 and D_add^R2 = history_bigram_r2 - free_r2 (R2's Q1),
    h_only against free_tok, history and history_tok, free_h - free_r2, every arm against the
    marginal (the horizon's headroom over its floor), the covered / fallback readings of the two
    label cells, every arm's point and CI, the per-horizon k and lambda tables with grid-edge
    flags; the horizon-1 re-selection against R2's; TREND: D_add^H and D_eq^H at horizons 1..4
    side by side (different position sets: a description, never a reading).
LABELS (mechanical; the PRIMARY harvest's label is the label; the replication is reported as
agrees / disagrees per horizon):
  REPRODUCE-INVALID | INCOMPLETE   (void: numbers only)
  LEAD-TIME-ABSORBED        Q(j) = H-ABSORBS at every j in {2, 3, 4}
  LEAD-TIME-SURVIVES@j      H-SURVIVES at some j; j the smallest such horizon
  LEAD-TIME-COMPLEMENTARY@j no H-SURVIVES, H-COMPLEMENTARY at some j; j the smallest such
  LEAD-TIME-INCONSISTENT    otherwise (some H-INCONSISTENT, no SURVIVES and no COMPLEMENTARY)
Per-horizon sentences and the stage sentence are number-free templates (the horizon index and the
budget are constants, not readouts); the STATUS lines at landing quote the BLUEPRINT's pinned
words with the numbers beside them. Under the guard a horizon's branch sentence is replaced and
nothing is claimed for it; the mechanical label stays and is quoted.
--conclude-from recomputes every table, CI, delta, the REPRODUCE and identity checks against the
committed R2 payload and state file (re-read, re-hashed, every header field compared), every
per-horizon k and lambda from the payload's own val tables, the horizon-1 selections against the
R2 record, and every label from the state file, and refuses a payload whose stored numbers
differ. It needs no checkpoint. Evidence files are written with LF newlines on every platform.

Usage:
  python tools/run_prefetch_horizon.py --harvest results/real/harvest_moe \\
      --out results/real/prefetch_horizon_s3.json
  python tools/run_prefetch_horizon.py --harvest results/real/harvest_moe_r \\
      --out results/real/prefetch_horizon_s3_r.json
  python tools/run_prefetch_horizon.py --conclude-from results/real/prefetch_horizon_s3.json
Smoke (disclosed in the registration; refused under results/; no R2 payload read):
  python tools/run_prefetch_horizon.py --harvest results/real/harvest_moe_r \\
      --only-seeds 8 --smoke-split-val --r2 none --out <scratch>/horizon_smoke.json
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
import run_prefetch_readouts as pr  # noqa: E402  (the FROZEN stage-1 instrument)
import run_prefetch_bigram as rb  # noqa: E402  (the FROZEN twin)
import run_prefetch_strat as rs  # noqa: E402  (the FROZEN stratified read)
import run_prefetch_r2 as r2  # noqa: E402  (the FROZEN generalising free baseline; asserts its parents at import)
from sideband.probes import load_label_space  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402

# the R2 tool's LF-normalised sha256 (= tests/test_prefetch_r2_landing.py INSTRUMENT_SHA256,
# = both committed R2 payloads' provenance.instrument_sha256)
R2_INSTRUMENT_SHA256 = "eaf671fdb9d637624c012b5555a06d1a7ff82072d09829c1d31c3aa492231a84"


def assert_frozen_r2(path: Path | None = None) -> str:
    """Refuse unless the R2 tool on disk still hashes (CRLF -> LF) to the attested sha."""
    p = Path(path) if path is not None else Path(r2.__file__)
    sha = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != R2_INSTRUMENT_SHA256:
        raise SystemExit(f"{p}: sha {sha[:12]} is not the frozen R2 tool {R2_INSTRUMENT_SHA256[:12]} — refusing")
    return sha


assert_frozen_r2()
r2.assert_frozen_strat()
rs.assert_frozen_twin()
rb.assert_frozen_instrument()

REGISTERED = ("OQ-9 STAGE-1 HORIZON READ REGISTRATION "
              "(docs/BLUEPRINT.md, 2026-10-04 amendment; post-hoc diagnostic; NON-CRITERION; a K-6 lead-time datum)")
E, L, K, D = r2.E, r2.L, r2.K, r2.D
BUDGETS, LAMBDAS, K_GRID = r2.BUDGETS, r2.LAMBDAS, r2.K_GRID
LABEL_BUDGET, MATERIAL, N_BOOT, BOOT_SEED, CHUNK = r2.LABEL_BUDGET, r2.MATERIAL, r2.N_BOOT, r2.BOOT_SEED, r2.CHUNK
HORIZONS = (1, 2, 3, 4)
LABEL_HORIZONS = (2, 3, 4)
REPRODUCE_HORIZON = 1
STATE_SCOPES = ("covered", "fallback")
UNIONS = {u: tuple(rs.UNIONS[u]) for u in STATE_SCOPES}   # the two coverage unions (the stratified tool's third, "all", is their sum)
SCOPES = STATE_SCOPES + ("all",)
REPRODUCE_NEAR_SHARE, REPRODUCE_NEAR_HITS = r2.REPRODUCE_NEAR_SHARE, r2.REPRODUCE_NEAR_HITS
IDENTITY_TOL = r2.IDENTITY_TOL
# the horizon-1 cells this read must reproduce from the R2 payload (its delta names), keyed by this file's names
IDENTITY_CELLS = {"d_eq_h": "d_eq_h", "d_add_h": "d_add_h", "anchor": "history_all_h-history_bigram_r2",
                  "free_h-free_r2": "free_h-free_r2"}
ARMS_TWIN = rb.ARMS_REQUIRED
ARMS_R2 = r2.ARMS_R2
ARMS_J1 = r2.ARMS_REQUIRED + ("marginal",)          # horizon 1: the REPRODUCE set plus the floor
ARMS_H_FIXED = ("marginal", "history", "free_tok", "history_tok", "free_r2", "history_tok_r2", "history_bigram_r2",
                "h_only", "free_h", "history_all_h")
ARMS_RIDGE_R2 = r2.ARMS_RIDGE_R2                    # the R2 ridge arms (free_r2 first in its grid)
ARM_BLOCKS_H = dict(r2.ARM_BLOCKS_R2, marginal=("bias",))
ARM_K = r2.ARM_K
R2_OF_HARVEST = {"harvest_moe": "prefetch_r2_s3.json", "harvest_moe_r": "prefetch_r2_s3_r.json"}
OUT_OF_HARVEST = {"harvest_moe": "prefetch_horizon_s3.json", "harvest_moe_r": "prefetch_horizon_s3_r.json"}
# the R2 selections this read takes at horizon 1 and must find re-selected on val there (reported, not a label)
RESELECT_ARMS = ARMS_RIDGE_R2


def arms_h(encoding: str) -> tuple:
    """The twelve horizon arms under the twin's selected encoding."""
    return ARMS_H_FIXED[:4] + (rb.free_arm_of(encoding), rb.history_arm_of(encoding)) + ARMS_H_FIXED[4:]


def arm_dims(arm: str, encoding: str) -> int:
    if arm == "marginal":
        return 1
    return r2.arm_dims(arm, encoding)


def horizon_positions(lengths: np.ndarray, j: int, T: int):
    """Anchors t with t >= 1 (a previous token exists) and t + j < row length (the target S[t+j] exists);
    at j = 1 exactly the twin's bigram positions."""
    rows, anchors = pr.positions_horizon(lengths, int(j), T)
    keep = anchors >= 1
    return rows[keep], anchors[keep]


# ---------------------------------------------------------------------------
# The computation (an R2 subclass: tables, hidden block, smoothed blocks, Gram algebra reused)
# ---------------------------------------------------------------------------

class Horizon(r2.R2):
    """R2's fit and evaluation with the horizon as a parameter. fit_base() fits the twin's tables and the
    hidden block once (on the horizon-1 train positions); run_horizon(j, ...) accumulates the Gram over
    the horizon's train positions with Y = S[t+j], solves the arms, selects on val and evaluates test."""

    def __init__(self, data: pr.S3Data, label_of_token: np.ndarray, n_classes: int, hidden: np.ndarray,
                 replay: np.ndarray, r2ref: dict | None = None, horizons=HORIZONS, lambdas=LAMBDAS, k_grid=K_GRID,
                 chunk: int = CHUNK):
        super().__init__(data, label_of_token, n_classes, hidden, replay, strat=None, lambdas=lambdas, k_grid=k_grid, chunk=chunk)
        self.r2ref = r2ref
        self.horizons = tuple(int(j) for j in horizons)
        if list(self.horizons) != sorted(set(self.horizons)) or self.horizons[0] != REPRODUCE_HORIZON:
            raise SystemExit(f"horizons must be strictly increasing and start at {REPRODUCE_HORIZON} (the REPRODUCE horizon)")
        if r2ref is not None:
            self.encoding_selected = r2ref["encoding"]
        self.sel: dict = {}                              # j -> the horizon's selection record
        self.tables: dict = {}                           # j -> the horizon's token tables (the frozen construction, target moved)
        self.j: int | None = None

    # ----- the horizon-matched tables ---------------------------------------------
    TABLE_FIELDS = ("token_table", "pair_keys", "pair_counts", "marginal_freq", "prev_table", "prev_pair_keys", "prev_pair_counts")

    def fit_tables_h(self, j: int) -> dict:
        """The twin's two tables with the target moved to S[t+j]: TABLE_CUR^j over t >= 0, t + j < length
        (keyed on tokens[t]) and TABLE_PREV^j over the horizon's positions (keyed on tokens[t-1]); the
        horizon's marginal from TABLE_CUR^j's column sums. At j = 1 identical to Bigram.fit_tables."""
        d = self.d
        train = self.masks["train"]
        rows, anchors = pr.restrict(*pr.positions_horizon(d.lengths, j, d.T), train)
        self.n_positions[f"horizon{j}/train"] = int(rows.shape[0])
        sl = d.slots[rows, anchors + j].astype(np.int64)
        token_table, pair_keys, pair_counts = self._count_table(d.tokens[rows, anchors], d.prompt_idx[rows], sl)
        counts = token_table.sum(axis=0).astype(np.float64)
        marginal_freq = counts / np.maximum(counts.sum(axis=1, keepdims=True), 1.0)
        rows, anchors = pr.restrict(*horizon_positions(d.lengths, j, d.T), train)
        sl = d.slots[rows, anchors + j].astype(np.int64)
        prev_table, prev_pair_keys, prev_pair_counts = self._count_table(d.tokens[rows, anchors - 1], d.prompt_idx[rows], sl)
        return {"token_table": token_table, "pair_keys": pair_keys, "pair_counts": pair_counts, "marginal_freq": marginal_freq,
                "prev_table": prev_table, "prev_pair_keys": prev_pair_keys, "prev_pair_counts": prev_pair_counts}

    def use_tables(self, j: int) -> None:
        for name in self.TABLE_FIELDS:
            setattr(self, name, self.tables[j][name])

    # ----- positions and masks ---------------------------------------------------
    def positions(self, split: str, j: int):
        d = self.d
        return pr.restrict(*horizon_positions(d.lengths, j, d.T), self.masks[split])

    def union_masks(self, rows, anchors) -> dict:
        m = self.strata_masks(rows, anchors)
        return {u: np.logical_or.reduce([m[s] for s in parts]) for u, parts in UNIONS.items()}

    # ----- the shared fits -------------------------------------------------------
    def fit_base(self) -> None:
        """The horizon-1 tables by the FROZEN construction (Bigram.fit_tables, R2's tables), the hidden block on
        the horizon-1 train positions (R2's)."""
        self.fit_tables()
        self.tables[REPRODUCE_HORIZON] = {name: getattr(self, name) for name in self.TABLE_FIELDS}
        rows, anchors = self.positions("train", REPRODUCE_HORIZON)
        self.fit_hidden(rows, anchors)

    # ----- per-horizon Gram ------------------------------------------------------
    def accumulate(self, j: int) -> None:
        """R2.fit's Gram loop over the horizon's train positions with Y = S[t+j]; at j = 1 R2's own
        positions, chunks and statements."""
        rows, anchors = self.positions("train", j)
        self.n_positions[f"horizon{j}/bigram/train"] = int(rows.shape[0])
        if rows.shape[0] == 0:
            raise SystemExit(f"no train positions at horizon {j}")
        D_X = r2.D_X
        G = np.zeros((D_X, D_X)); C = np.zeros((D_X, D))
        Ghh = np.zeros((D, D)); Ghs = np.zeros((D, D)); Ghb = np.zeros(D); Ch = np.zeros((D, D))
        Gkk = {k: np.zeros((2 * D, 2 * D)) for k in self.k_grid}
        Gks = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        Gkh = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        Gkb = {k: np.zeros(2 * D) for k in self.k_grid}
        Ck = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            X, _ = self.design(r, a, lopo=True)              # the twin's statement; its Y is the horizon-1 target
            Y = self.mh(r, a + j)
            G += X.T @ X
            C += X.T @ Y
            S = X[:, :D]
            Hb = self.h_block(r, a)
            Ghh += Hb.T @ Hb; Ghs += Hb.T @ S; Ghb += Hb.sum(axis=0); Ch += Hb.T @ Y
            for k, Sk in self.smooth_blocks(r, a, self.k_grid, lopo=True).items():
                Gkk[k] += Sk.T @ Sk; Gks[k] += Sk.T @ S; Gkh[k] += Sk.T @ Hb; Gkb[k] += Sk.sum(axis=0); Ck[k] += Sk.T @ Y
        self.G, self.C = G, C
        self.Ghh, self.Ghs, self.Ghb, self.Ch = Ghh, Ghs, Ghb, Ch
        self.Gkk, self.Gks, self.Gkh, self.Gkb, self.Ck = Gkk, Gks, Gkh, Gkb, Ck

    def arm_gram(self, arm: str, k: float | None):
        blocks = ARM_BLOCKS_H[arm]
        Gs = np.block([[self._pair(a, b, k) for b in blocks] for a in blocks])
        Cs = np.vstack([self._target(a, k) for a in blocks])
        return Gs, Cs

    def _arm_design(self, arm: str, blocks: dict, k: float | None) -> np.ndarray:
        cols = []
        for b in ARM_BLOCKS_H[arm]:
            cols.append(blocks[(b, k)] if b in ("cur", "prev") else blocks[b])
        return np.hstack(cols)

    def solve_twin(self, lams_of_arm: dict | None, arms=ARMS_TWIN) -> None:
        """The given twin arms from the twin's Gram: at every lambda, or at the given ones only."""
        for arm in arms:
            F = rb.arm_cols(arm)
            Gs, Cs = self.G[np.ix_(F, F)], self.C[F]
            lams = self.lambdas if lams_of_arm is None else (lams_of_arm[arm],)
            for lam in lams:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)

    def solve_grid(self) -> None:
        """free_r2 at every (k, lambda); h_only, replay_cur and marginal at every lambda; the fixed-k ends."""
        self.Wk = {}
        for k in self.k_grid:
            Gs, Cs = self.arm_gram("free_r2", k)
            for lam in self.lambdas:
                self.Wk[("free_r2", k, lam)] = pr.ridge_solve(Gs, Cs, lam)
        for arm in ("h_only", "replay_cur", "marginal"):
            Gs, Cs = self.arm_gram(arm, ARM_K.get(arm))
            for lam in self.lambdas:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)
        for arm in ("free_backoff", "free_replay"):
            for lam in self.lambdas:
                self.W[(arm, lam)] = self.Wk[("free_r2", ARM_K[arm], lam)]

    # ----- evaluation at a horizon -----------------------------------------------
    def evaluate_free_grid(self, split: str, j: int | None = None) -> dict:
        """out[(k, lam, B, scope)] = (hits, needed) for free_r2 at every (k, lambda), scopes the two unions."""
        j = self.j if j is None else j
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = self.positions(split, j)
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
            Y = self.mh(r, a + j)
            yy = Y.reshape(r.shape[0], L, E)
            masks = {u: m for u, m in self.union_masks(r, a).items() if m.any()}
            n_full = np.full((r.shape[0], L), K, np.int64)
            bias = np.ones((r.shape[0], 1))
            for k, Sk in self.smooth_blocks(r, a, self.k_grid).items():
                Xa = np.hstack([Sk, bias])
                for lam in self.lambdas:
                    sc = (Xa @ self.Wk[("free_r2", k, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(sc, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        for scope, m in masks.items():
                            acc((k, lam, B, scope), pr.per_prompt(h[m], pp[m], pids), pr.per_prompt(n_full[m], pp[m], pids))
        return out

    def select_k(self, grid: dict) -> None:
        """R2's rule over the union scopes: (k, lambda) for free_r2 on the pooled val positions at the label
        budget, strict >, k outer then lambda, ties keep the smaller; both grid edges flagged."""
        best, best_k, best_lam, table = -np.inf, None, None, {}
        for k in self.k_grid:
            table[r2.k_tag(k)] = {}
            for lam in self.lambdas:
                h = sum(grid[(k, lam, LABEL_BUDGET, s)][0].sum() for s in STATE_SCOPES if (k, lam, LABEL_BUDGET, s) in grid)
                n = sum(grid[(k, lam, LABEL_BUDGET, s)][1].sum() for s in STATE_SCOPES if (k, lam, LABEL_BUDGET, s) in grid)
                v = float(h / n) if n > 0 else float("nan")
                table[r2.k_tag(k)][str(lam)] = v
                if v > best:
                    best, best_k, best_lam = v, k, lam
        self.k_val_table = table
        if best_k is None:
            raise SystemExit("select_k: no (k, lambda) pair has a val hit rate (every cell NaN)")
        self.k_selected = best_k
        self.k_grid_edge = bool(best_k in (self.k_grid[0], self.k_grid[-1]))
        self.lambda_selected["free_r2"] = best_lam
        self.grid_edge["free_r2"] = bool(best_lam in (self.lambdas[0], self.lambdas[-1]))
        self.val_table["free_r2"] = table[r2.k_tag(best_k)]

    @staticmethod
    def _pooled_all(val: dict, arm: str, lam: float) -> float:
        h = sum(val[(arm, LABEL_BUDGET, lam, s)][0].sum() for s in STATE_SCOPES if (arm, LABEL_BUDGET, lam, s) in val)
        n = sum(val[(arm, LABEL_BUDGET, lam, s)][1].sum() for s in STATE_SCOPES if (arm, LABEL_BUDGET, lam, s) in val)
        return float(h / n) if n > 0 else float("nan")

    def evaluate(self, split: str, encoding: str | None = None, arms=ARMS_J1, lambdas_of_arm: dict | None = None,
                 j: int | None = None) -> dict:
        """out[(arm, B, lam, scope)] = (hits (P, L), needed (P, L)) over the horizon's positions of the split
        in that union scope; every lambda unless lambdas_of_arm. The twin's arms are read exactly as R2
        reads them (the same column slices of the same design)."""
        j = self.j if j is None else j
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = self.positions(split, j)
        self.n_positions[f"horizon{j}/bigram/{split}"] = int(rows.shape[0])
        maxB = max(self.budgets)
        need_r2 = any(a_ in ARMS_R2 or a_ == "marginal" for a_ in arms)
        ks_set = set()
        for a_ in arms:
            if a_ in ARMS_RIDGE_R2:
                kk = ARM_K.get(a_, self.k_selected)
                if kk is None:
                    raise SystemExit("evaluate: the selected k is not set (select_k first)")
                ks_set.add(kk)
        ks = tuple(sorted(ks_set, key=lambda x: (bool(np.isinf(x)), x)))
        out: dict = {}

        def acc(key, h, n):
            if key in out:
                out[key][0][...] += h; out[key][1][...] += n
            else:
                out[key] = (h.copy(), n.copy())

        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            pp = d.prompt_idx[r]
            X, _ = self.design(r, a)
            Y = self.mh(r, a + j)
            yy = Y.reshape(r.shape[0], L, E)
            masks = {u: m for u, m in self.union_masks(r, a).items() if m.any()}
            n_full = np.full((r.shape[0], L), K, np.int64)
            blocks = self._blocks(r, a, X, ks) if need_r2 else None
            for arm in arms:
                if arm == "replay_zerofit":
                    sc = self.replay[d.tokens[r, a]].reshape(r.shape[0], L, E)
                    lams = (None,)
                elif arm in ARMS_TWIN:
                    sc = None
                    lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                    Xa = X[:, rb.arm_cols(arm)]
                else:
                    sc = None
                    lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                    Xa = self._arm_design(arm, blocks, ARM_K.get(arm, self.k_selected))
                for lam in lams:
                    scores = sc if sc is not None else (Xa @ self.W[(arm, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(scores, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        for scope, m in masks.items():
                            acc((arm, B, lam, scope), pr.per_prompt(h[m], pp[m], pids), pr.per_prompt(n_full[m], pp[m], pids))
        return out

    # ----- one horizon end to end ------------------------------------------------
    def run_horizon(self, j: int) -> list[dict]:
        """Accumulate, solve, select and evaluate horizon j; returns its test state rows and records its
        selection under self.sel[j]. At the REPRODUCE horizon with an R2 reference every selection is
        the reference's; what val would re-select is recorded beside it."""
        self.j = int(j)
        ref = self.r2ref if j == REPRODUCE_HORIZON else None
        self.W = {}
        self.val_table, self.lambda_selected, self.grid_edge = {}, {}, {}
        self.k_selected, self.k_grid_edge, self.k_val_table = None, None, {}
        if j not in self.tables:
            self.tables[j] = self.fit_tables_h(j)
        self.use_tables(j)
        self.accumulate(j)
        arms = ARMS_J1 if j == REPRODUCE_HORIZON else arms_h(self.encoding_selected)
        twin_arms = tuple(a for a in arms if a in ARMS_TWIN)
        reselect = None
        if ref is not None:
            # R2's readers: the twin's arms at the twin's lambdas, the R2 arms at R2's k and lambdas
            self.solve_twin({a: float(ref["lambda_selected"][a]) for a in ARMS_TWIN})
            self.solve_grid()
            grid = self.evaluate_free_grid("val", j)
            self.select_k(grid)                                  # what val re-selects, recorded below
            re_k, re_lam_free, re_table = self.k_selected, self.lambda_selected["free_r2"], self.k_val_table
            re_edge = self.k_grid_edge
            self.k_selected = r2.k_of_tag(ref["k_selected"])
            self.k_grid_edge = bool(self.k_selected in (self.k_grid[0], self.k_grid[-1]))
            self.fit_k(self.k_selected)
            arms_val = tuple(a for a in ARMS_RIDGE_R2 if a != "free_r2") + ("marginal",)
            val = self.evaluate("val", arms=arms_val, j=j)
            self.select(val, arms_val)                           # val's lambdas (marginal keeps its own)
            re_lams = {a: self.lambda_selected[a] for a in arms_val if a != "marginal"}
            re_lams["free_r2"] = re_lam_free
            for a in ARMS_TWIN + tuple(x for x in ARMS_RIDGE_R2):
                self.lambda_selected[a] = float(ref["lambda_selected"][a])
                self.grid_edge[a] = None
            self.lambda_selected["replay_zerofit"] = None
            self.grid_edge["replay_zerofit"] = None
            self.val_table["free_r2"] = re_table[r2.k_tag(re_k)]
            self.k_val_table = re_table
            source = {a: "r2" for a in ARMS_TWIN + ARMS_R2}
            source["replay_zerofit"] = None
            source["marginal"] = "val"
            reselect = {"k": r2.k_tag(re_k), "k_grid_edge": re_edge,
                        "lambda": {a: float(v) for a, v in re_lams.items()},
                        "matches_r2": bool(r2.k_tag(re_k) == ref["k_selected"] and
                                           all(float(re_lams[a]) == float(ref["lambda_selected"][a]) for a in RESELECT_ARMS))}
        else:
            self.solve_twin(None, arms=ARMS_TWIN if j == REPRODUCE_HORIZON else twin_arms)
            if j == REPRODUCE_HORIZON:
                val_twin = self.evaluate("val", arms=ARMS_TWIN, j=j)
                self.select(val_twin, ARMS_TWIN)                 # the twin's own rule incl. the encoding
                if self.encoding_selected is None:
                    raise SystemExit("internal: the twin's encoding was not selected at horizon 1")
                arms = ARMS_J1
            else:
                self.W = {k_: w for k_, w in self.W.items() if k_[0] in twin_arms}     # the four unused twin arms are not solved
                val_twin = self.evaluate("val", arms=twin_arms, j=j)
                self.select(val_twin, twin_arms)
            self.solve_grid()
            grid = self.evaluate_free_grid("val", j)
            self.select_k(grid)
            self.fit_k(self.k_selected)
            arms_val = tuple(a for a in arms if a not in ARMS_TWIN and a not in ("free_r2", "replay_zerofit"))
            val = self.evaluate("val", arms=arms_val, j=j)
            self.select(val, arms_val)
            self.lambda_selected.setdefault("replay_zerofit", None)
            self.grid_edge.setdefault("replay_zerofit", None)
            source = {a: "val" for a in arms}
            source["replay_zerofit"] = None
        if j != REPRODUCE_HORIZON:
            for a in arms:
                if a not in self.lambda_selected:
                    raise SystemExit(f"internal: no lambda selected for {a} at horizon {j}")
        test = self.evaluate("test", arms=arms, lambdas_of_arm=self.lambda_selected, j=j)
        if j != REPRODUCE_HORIZON:
            self.tables.pop(j, None)                         # the horizon's two (vocab, 16, 64) int64 tables leave the dict here; the
                                                             # table attributes still reference them until the next use_tables
        self.sel[j] = {"arms": list(arms), "k_selected": r2.k_tag(self.k_selected), "k_grid_edge": self.k_grid_edge,
                       "k_val_table": self.k_val_table,
                       "lambda_selected": {a: (None if self.lambda_selected.get(a) is None else float(self.lambda_selected[a])) for a in arms},
                       "lambda_source": {a: source.get(a) for a in arms},
                       "lambda_grid_edge": {a: self.grid_edge.get(a) for a in arms},
                       "val_table": {a: self.val_table[a] for a in arms if a in self.val_table},
                       "reselect": reselect}
        return self.state_rows(test, j)

    def state_rows(self, test: dict, j: int | None = None) -> list[dict]:
        j = self.j if j is None else j
        pids = self.prompt_ids["test"]
        rows = []
        for (arm, B, lam, scope), (h, n) in test.items():
            if lam != self.lambda_selected.get(arm):
                continue
            for pi, pid in enumerate(pids):
                for g in range(L):
                    if n[pi, g] == 0:
                        continue
                    rows.append({"arm": arm, "budget": B, "key": int(j), "depth": None, "gate": g,
                                 "prompt_idx": int(pid), "scope": scope, "hits": int(h[pi, g]), "needed": int(n[pi, g])})
        return sort_rows(rows)


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes it from the state file)
# ---------------------------------------------------------------------------

def _sort_key(r: dict):
    scope = STATE_SCOPES.index(r["scope"]) if r["scope"] in STATE_SCOPES else len(STATE_SCOPES)   # _group refuses the latter
    return (int(r["key"]), r["arm"], int(r["budget"]), scope, int(r["gate"]), int(r["prompt_idx"]))


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=_sort_key)


def _group(rows: list[dict]) -> dict:
    """{(arm, budget, horizon, scope): {gate: {prompt: (hits, needed)}}} over the two unions and their sum ALL."""
    g: dict = {}
    seen: set = set()
    for r in rows:
        if r["scope"] not in STATE_SCOPES:
            raise SystemExit(f"state row with scope {r['scope']!r}: only the two unions are stored")
        ident = (r["arm"], int(r["budget"]), int(r["key"]), r["scope"], int(r["gate"]), int(r["prompt_idx"]))
        if ident in seen:
            raise SystemExit(f"duplicate state row {ident}")
        seen.add(ident)
        for scope in (r["scope"], "all"):
            cell = g.setdefault((r["arm"], int(r["budget"]), int(r["key"]), scope), {}).setdefault(int(r["gate"]), {})
            h, n = cell.get(int(r["prompt_idx"]), (0, 0))
            cell[int(r["prompt_idx"])] = (h + int(r["hits"]), n + int(r["needed"]))
    return g


def _index_mine(rows: list[dict]) -> dict:
    return {(r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]), r["scope"]): (int(r["hits"]), int(r["needed"]))
            for r in rows if int(r["key"]) == REPRODUCE_HORIZON and r["arm"] in r2.ARMS_REQUIRED}


def _index_r2(r2_rows: list[dict]) -> dict:
    """The committed R2 rows summed over their six strata into the two unions."""
    union_of = {s: u for u, parts in UNIONS.items() for s in parts}
    out: dict = {}
    for r in r2_rows:
        if r["arm"] not in r2.ARMS_REQUIRED:
            continue
        u = union_of.get(r["stratum"])
        if u is None:
            raise SystemExit(f"R2 state row with stratum {r['stratum']!r} outside the six strata")
        key = (r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]), u)
        h, n = out.get(key, (0, 0))
        out[key] = (h + int(r["hits"]), n + int(r["needed"]))
    return out


def reproduce_check(rows: list[dict], r2_rows: list[dict]) -> dict:
    """The REPRODUCE precondition: this read's horizon-1 rows for R2's nineteen arms against the committed
    R2 rows summed into the two unions, hits AND needed, to the integer (R2's own NEAR rule)."""
    mine, theirs = _index_mine(rows), _index_r2(r2_rows)
    missing = sorted(k for k in theirs if k not in mine)
    extra = sorted(k for k in mine if k not in theirs)
    needed_mm, hits_mm, max_gap = 0, 0, 0
    for k, (h, n) in theirs.items():
        if k not in mine:
            continue
        hm, nm = mine[k]
        if nm != n:
            needed_mm += 1
        elif hm != h:
            hits_mm += 1
            max_gap = max(max_gap, abs(hm - h))
    n_rows = len(theirs)
    exact = not missing and not extra and needed_mm == 0 and hits_mm == 0
    near = (not exact and not missing and not extra and needed_mm == 0
            and hits_mm <= int(REPRODUCE_NEAR_SHARE * n_rows) and max_gap <= REPRODUCE_NEAR_HITS)
    status = "EXACT" if exact else "NEAR" if near else "INVALID"
    return {"n_r2_union_rows": n_rows, "n_compared": n_rows - len(missing), "missing_here": len(missing),
            "extra_here": len(extra), "needed_mismatch_rows": needed_mm, "hits_mismatch_rows": hits_mm,
            "max_abs_hits_gap": int(max_gap), "near_share_cap": REPRODUCE_NEAR_SHARE, "near_hits_cap": REPRODUCE_NEAR_HITS,
            "status": status, "ok": bool(status != "INVALID")}


_H = "the forward's final-norm state at the address block's width in the free arm"
_NM = f"no material margin (at or above +{MATERIAL})"
_STR = f"at least one CI95 straddles the +{MATERIAL} floor"


def _at(j: int) -> str:
    return f"at this reader (B = {LABEL_BUDGET}, j = {j})"


def sentence_horizon(q: str, straddle: bool, j: int) -> str:
    """R2's Q2 sentences, at horizon j (number-free templates)."""
    at = _at(j)
    if q == "H-SURVIVES":
        return (f"with {_H}, both readings are SIGNAL by the rule while {_STR}: not settled at this power, {at}" if straddle else
                f"with {_H}, at horizon {j} the address block adds a material margin over the equal-dims free block and the "
                f"address stream adds a material margin over the free bigram plus the hidden block: a lead-time datum at this "
                f"reader against the free arms R2 built (the p_t summaries and the full h_a not included), with H at 1024 of "
                f"2048 dimensions, {at} (the stage sentence governs; the motivation struck at horizon 1 stays struck)")
    if q == "H-COMPLEMENTARY":
        return (f"with {_H}, the union reading is SIGNAL and the equal-dims reading is not, by the rule, while {_STR}: not "
                f"settled at this power, {at}" if straddle else
                f"with {_H}, at horizon {j} {_NM} of the address block over the equal-dims free block is shown, while the "
                f"address stream adds a material margin over the free bigram plus the hidden block, {at} (the stage sentence "
                f"governs; the motivation struck at horizon 1 stays struck)")
    if q == "H-ABSORBS":
        return (f"with {_H}, neither reading is SIGNAL by the rule while {_STR}: not settled at this power, {at}" if straddle else
                f"with {_H}, at horizon {j} {_NM} of the address block over the equal-dims free block is shown and none of the "
                f"address stream over the free bigram plus the hidden block: at this horizon the forward's own final-norm state "
                f"plus two tokens' smoothed routing profiles show no material address margin (NON-CRITERION; K-2 is "
                f"untouched), {at}")
    if q == "H-INCONSISTENT":
        return (f"with {_H}, the equal-dims comparison reads a material margin while the union reader does not"
                + (f", and {_STR}" if straddle else "") + f"; no sentence on the margin is written, {at}")
    raise SystemExit(f"unknown horizon label {q!r}")


_READER_GUARD = (f"with {_H}, at horizon {{J}} {{WHICH}} {{VERB}} NEGATIVE: the hidden block degrades a reader at this train "
                 f"size; the horizon's label is mechanical and is quoted, but no branch claim is written for it")
_NEG_EQ = "the address block reads below the equal-dims free block with the hidden block (NEGATIVE); "
_NEG_ADD = "the address stream reads below the free bigram plus the hidden block (NEGATIVE); "
_STRUCK = ("the address-beyond-free motivation struck at horizon 1 stays struck and this cell does not reinstate it; a stage-2 "
           "registration may cite it only under the operator's words authorizing stage 2 in those words, and must re-read the "
           "margin against free_h on its own population at that horizon")
SENTENCE_STAGE = {
    "LEAD-TIME-ABSORBED": (f"with the forward's final-norm state at the address block's width and two tokens' smoothed routing "
                           f"profiles in the free arm, {_NM} of the address block over the equal-dims free block and none of the "
                           f"address stream over the free arm is shown at horizon 2, 3 or 4, as at horizon 1 (R2): at this reader "
                           f"the address stream is not shown to add a material hit-rate margin over free information at any horizon "
                           f"1..4 (lead time counted in forwards; no latency priced; NON-CRITERION; K-2 is untouched; K-6 stays "
                           f"UNTESTED and this is its lead-time datum); the stage-2 strike stands, PREFETCH-HEADROOM (which does "
                           f"not depend on this margin) stands, and OQ-9's prefetch half closes at this reader"),
    "LEAD-TIME-SURVIVES": (f"at horizon {{J}} the address block adds a material margin over the equal-dims free block and the "
                           f"address stream adds a material margin over the free bigram plus the hidden block: a lead-time cell at "
                           f"horizon {{J}}, at this reader, against the free arms R2 built (the p_t summaries and the full h_a not "
                           f"included), with H at 1024 of 2048 dimensions; {_STRUCK}"),
    "LEAD-TIME-COMPLEMENTARY": (f"at horizon {{J}} {_NM} of the address block over the equal-dims free block is shown while the "
                                f"address stream adds a material margin over the free bigram plus the hidden block: a lead-time "
                                f"cell for the union reader only, at horizon {{J}}, at this reader; {_STRUCK}"),
    "LEAD-TIME-INCONSISTENT": ("the equal-dims comparison reads a material margin at some horizon while the union reader does "
                               "not, and no horizon reads SURVIVES or COMPLEMENTARY; no sentence on the margin is written"),
}
_STAGE_STRADDLE = "; a CI95 straddles the +{M} floor at horizon(s) {JS}: not settled at this power there"
_STAGE_GUARD = "; the reader guard fired at horizon(s) {JS}, where no branch claim is written"
_STAGE_EDGE = "; free_h's lambda sits at the grid's edge at horizon(s) {JS} (the free arm is bounded by the grid there), said in words"
_WITHHELD = ("the stage label reads {LABEL} by the rule while {WHY}; the label is mechanical and is quoted, but no closing "
             "claim is written")
SENTENCE_VOID = {
    "REPRODUCE-INVALID": ("this read's horizon-1 rows do not reproduce the committed R2 rows for R2's arms (or a horizon-1 "
                          "identity cell is not the R2 payload's); the run is void and its deltas are numbers, not readings"),
    "INCOMPLETE": None,
}
DELTA_PAIRS = (("abt", "history_tok", "free_tok"),
               ("gate_eq", "history_tok", "FREE"),
               ("d_add_bigram", "HIST", "FREE"),
               ("gate_eq_r2", "history_tok_r2", "free_r2"),
               ("d_add_r2", "history_bigram_r2", "free_r2"),
               ("d_eq_h", "history_bigram_r2", "free_h"),
               ("d_add_h", "history_all_h", "free_h"),
               ("anchor", "history_all_h", "history_bigram_r2"),
               ("free_h-free_r2", "free_h", "free_r2"),
               ("h_only-free_tok", "h_only", "free_tok"),
               ("h_only-history", "h_only", "history"),
               ("h_only-history_tok", "h_only", "history_tok"),
               ("free_r2-FREE", "free_r2", "FREE"),
               ("history_tok_r2-history_tok", "history_tok_r2", "history_tok"))
FLOOR_ARMS = ("history", "free_tok", "history_tok", "FREE", "HIST", "free_r2", "history_tok_r2", "history_bigram_r2",
              "h_only", "free_h", "history_all_h")
HORIZON_FIELDS = ("q", "d_eq_h", "d_add_h", "anchor", "free_h_gain", "d_eq_h_reading", "d_add_h_reading", "anchor_reading",
                  "free_h_gain_reading", "d_eq_h_floor_straddle", "d_add_h_floor_straddle", "floor_straddle", "negative",
                  "reader_guard", "inconsistent_cause", "d_eq_h_covered", "d_add_h_covered", "d_eq_h_fallback", "d_add_h_fallback",
                  "d_eq_h_covered_reading", "d_add_h_covered_reading", "d_eq_h_fallback_reading", "d_add_h_fallback_reading",
                  "b8_b32_disagree", "sentence")
READING_FIELDS = ("horizons", "stage", "first_horizon", "straddle_horizons", "guard_horizons", "free_h_edge_horizons", "trend",
                  "sentence", "said_in_words", "label_horizons")


def _straddle(dl: dict) -> bool:
    return bool(dl["lo"] <= MATERIAL <= dl["hi"])


def conclude(rows: list[dict], encoding: str, k_of_horizon: dict, r2_rows: list[dict] | None,
             r2_cells: dict | None = None, n_boot: int = N_BOOT, seed: int = BOOT_SEED, budgets=BUDGETS,
             horizons=HORIZONS, free_h_edge: dict | None = None) -> dict:
    """free_h_edge: {horizon: bool}, whether free_h's selected lambda sits at an end of the grid at that horizon (the FREE-ARM
    EDGE rule: at the first SURVIVES / COMPLEMENTARY horizon it withholds the closing claim; elsewhere it is said in words)."""
    if encoding not in rb.ENCODINGS:
        raise SystemExit(f"unknown encoding {encoding!r}")
    fh_edge = {str(j): bool((free_h_edge or {}).get(str(j), (free_h_edge or {}).get(j, False))) for j in horizons}
    rows = sort_rows(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    groups = _group(rows)
    free, hist = rb.free_arm_of(encoding), rb.history_arm_of(encoding)
    names = {"FREE": free, "HIST": hist}
    present_arms = {j: sorted({r["arm"] for r in rows if int(r["key"]) == j}) for j in horizons}
    tables: dict = {}
    for (arm, B, j, scope), gates in groups.items():
        entry = {"arm": arm, "budget": B, "horizon": j, "scope": scope,
                 "dims": arm_dims(arm, encoding) if (arm in r2.ARMS_REQUIRED or arm == "marginal") else None, "per_gate": {}}
        for g in sorted(gates):
            h, n = pr._arrays(gates[g], prompts)
            entry["per_gate"][str(g)] = pr._point_ci(h, n, n_boot, seed)
        H, N = pr._pooled(gates, prompts)
        entry["all"] = pr._point_ci(H, N, n_boot, seed)
        tables[f"{arm}|B={B}|j={j}|{scope}"] = entry

    def pooled_of(arm, B, j, scope):
        gates = groups.get((names.get(arm, arm), B, j, scope))
        return None if gates is None else pr._pooled(gates, prompts)

    for j in horizons:
        for B in budgets:
            for scope in SCOPES:
                ref = pooled_of("history_tok", B, j, scope)
                if ref is None:
                    continue
                for arm in present_arms[j]:
                    pa = pooled_of(arm, B, j, scope)
                    if pa is not None and not np.array_equal(pa[1], ref[1]):
                        raise SystemExit(f"pairing violated: {arm} and history_tok have different per-prompt trials at B={B}, j={j} in {scope}")

    def delta_of(a, b, B, j, scope):
        pa, pb = pooled_of(a, B, j, scope), pooled_of(b, B, j, scope)
        if pa is None or pb is None:
            return None
        if not np.array_equal(pa[1], pb[1]):
            raise SystemExit(f"pairing violated: {a} and {b} have different per-prompt trials at B={B}, j={j} in {scope}")
        return pr._delta(pa[0], pb[0], pa[1], n_boot, seed)

    deltas: dict = {}
    for j in horizons:
        for B in budgets:
            for scope in SCOPES:
                for name, a, b in DELTA_PAIRS:
                    dl = delta_of(a, b, B, j, scope)
                    if dl is not None:
                        deltas[f"{name}|B={B}|j={j}|{scope}"] = dl
                for arm in FLOOR_ARMS:
                    dl = delta_of(arm, "marginal", B, j, scope)
                    if dl is not None:
                        deltas[f"{arm}-marginal|B={B}|j={j}|{scope}"] = dl

    scopes: dict = {}
    for j in horizons:
        ref_all = pooled_of("history_tok", LABEL_BUDGET, j, "all")
        scopes[str(j)] = {}
        for scope in SCOPES:
            pa = pooled_of("history_tok", LABEL_BUDGET, j, scope)
            if pa is None:
                scopes[str(j)][scope] = {"positions": 0, "share": 0.0, "prompts_with_positions": 0}
                continue
            scopes[str(j)][scope] = {"positions": int(round(float(pa[1].sum()) / (L * K))),
                                     "share": float(pa[1].sum() / ref_all[1].sum()) if ref_all is not None and ref_all[1].sum() > 0 else None,
                                     "prompts_with_positions": int((pa[1] > 0).sum())}

    labels: dict = {"encoding": encoding, "free_bigram_arm": free, "history_bigram_arm": hist,
                    "k_of_horizon": {str(j): k_of_horizon.get(str(j), k_of_horizon.get(j)) for j in horizons},
                    "scopes": scopes, "arms_per_horizon": {str(j): present_arms[j] for j in horizons}}
    need = {str(j): [a for a in (ARMS_J1 if j == REPRODUCE_HORIZON else arms_h(encoding)) if a not in present_arms[j]] for j in horizons}
    labels["missing_arms"] = {j: a for j, a in need.items() if a}
    label_h = tuple(j for j in horizons if j != REPRODUCE_HORIZON)      # the registered run's (2, 3, 4); a shorter smoke's beyond 1
    labels["label_horizons"] = list(label_h)
    if not label_h:
        # a run of the REPRODUCE horizon alone has nothing to label: void, never a vacuous ABSORBED
        labels.update({"label": "INCOMPLETE", "void": True, "missing_label_cells": ["no label horizon beyond the REPRODUCE horizon"]})
        for f_ in READING_FIELDS:
            labels[f_] = None
        return {"tables": tables, "deltas": deltas, "labels": labels}
    label_cells = [f"{name}|B={LABEL_BUDGET}|j={j}|all" for j in label_h for name in ("d_eq_h", "d_add_h", "anchor", "free_h-free_r2")]
    identity_cells = [f"{name}|B={LABEL_BUDGET}|j={REPRODUCE_HORIZON}|all" for name in IDENTITY_CELLS]
    labels["missing_label_cells"] = [c for c in label_cells + identity_cells if c not in deltas]
    rep = None if r2_rows is None else reproduce_check(rows, r2_rows)
    labels["reproduce"] = rep
    if r2_cells is not None:
        ok = True
        for mine_name, theirs_name in IDENTITY_CELLS.items():
            mine, theirs = deltas.get(f"{mine_name}|B={LABEL_BUDGET}|j={REPRODUCE_HORIZON}|all"), r2_cells.get(theirs_name)
            if mine is None or theirs is None:
                ok = False
                continue
            ok = ok and all(abs(float(mine[kk]) - float(theirs[kk])) <= IDENTITY_TOL for kk in ("delta", "lo", "hi"))
        labels["identity_matches_r2"] = bool(ok)
    else:
        labels["identity_matches_r2"] = None
    if rep is None:
        labels["reproduce_status"], labels["reproduce_ok"] = None, None
    else:
        status = rep["status"]
        if status != "INVALID" and labels["identity_matches_r2"] is False:
            status = "INVALID"
        labels["reproduce_status"], labels["reproduce_ok"] = status, bool(status != "INVALID")
    if labels["missing_arms"] or labels["missing_label_cells"]:
        labels.update({"label": "INCOMPLETE", "void": True})
        for f_ in READING_FIELDS:
            labels[f_] = None
        return {"tables": tables, "deltas": deltas, "labels": labels}

    # per-horizon readings (every horizon, the REPRODUCE horizon included for the trend; labels on 2..4)
    per: dict = {}
    for j in horizons:
        c = lambda name, scope="all", B=LABEL_BUDGET: deltas.get(f"{name}|B={B}|j={j}|{scope}")  # noqa: E731
        eq, add, anc, gain = c("d_eq_h"), c("d_add_h"), c("anchor"), c("free_h-free_r2")
        hj: dict = {"d_eq_h": eq, "d_add_h": add, "anchor": anc, "free_h_gain": gain}
        hj["d_eq_h_reading"], hj["d_add_h_reading"] = pr._reading(eq), pr._reading(add)
        hj["anchor_reading"], hj["free_h_gain_reading"] = pr._reading(anc), pr._reading(gain)
        hj["d_eq_h_floor_straddle"], hj["d_add_h_floor_straddle"] = _straddle(eq), _straddle(add)
        hj["floor_straddle"] = bool(hj["d_eq_h_floor_straddle"] or hj["d_add_h_floor_straddle"])
        hj["negative"] = bool(hj["d_eq_h_reading"] == "NEGATIVE" or hj["d_add_h_reading"] == "NEGATIVE")
        hj["reader_guard"] = bool(gain["hi"] < 0 or anc["hi"] < 0)
        e_sig, u_sig = hj["d_eq_h_reading"] == "SIGNAL", hj["d_add_h_reading"] == "SIGNAL"
        q = ("H-SURVIVES" if (e_sig and u_sig) else "H-COMPLEMENTARY" if (not e_sig and u_sig)
             else "H-ABSORBS" if (not e_sig and not u_sig) else "H-INCONSISTENT")
        hj["q"] = q
        hj["inconsistent_cause"] = (None if q != "H-INCONSISTENT" else "reader" if anc["hi"] < 0
                                    else "floor straddle" if hj["floor_straddle"] else "neither")
        for scope in STATE_SCOPES:
            for name in ("d_eq_h", "d_add_h"):
                dl = c(name, scope)
                hj[f"{name}_{scope}"] = dl
                hj[f"{name}_{scope}_reading"] = None if dl is None else pr._reading(dl)
        said = []
        for name in ("d_eq_h", "d_add_h"):
            for B in budgets:
                if B == LABEL_BUDGET:
                    continue
                other = c(name, "all", B)
                if other is not None and pr._reading(other) != hj[f"{name}_reading"]:
                    said.append(f"{name}|B={B}|j={j}|all: {pr._reading(other)}")
        hj["b8_b32_disagree"] = said
        if hj["reader_guard"]:
            parts = [w for w, flag in (("free_h - free_r2", gain["hi"] < 0), ("the dilution anchor history_all_h - history_bigram_r2", anc["hi"] < 0)) if flag]
            s = _READER_GUARD.replace("{J}", str(j)).replace("{WHICH}", " and ".join(parts)).replace("{VERB}", "read" if len(parts) > 1 else "reads")
        else:
            s = sentence_horizon(q, hj["floor_straddle"], j)
        if hj["d_add_h_reading"] == "NEGATIVE":
            s = _NEG_ADD + s
        if hj["d_eq_h_reading"] == "NEGATIVE":
            s = _NEG_EQ + s
        hj["sentence"] = s
        per[str(j)] = {f_: hj[f_] for f_ in HORIZON_FIELDS}
    labels["horizons"] = per
    qs = {j: per[str(j)]["q"] for j in label_h}
    surv = [j for j in label_h if qs[j] == "H-SURVIVES"]
    comp = [j for j in label_h if qs[j] == "H-COMPLEMENTARY"]
    if surv:
        stage, first = "LEAD-TIME-SURVIVES", surv[0]
    elif comp:
        stage, first = "LEAD-TIME-COMPLEMENTARY", comp[0]
    elif all(qs[j] == "H-ABSORBS" for j in label_h):
        stage, first = "LEAD-TIME-ABSORBED", None
    else:
        stage, first = "LEAD-TIME-INCONSISTENT", None
    labels["stage"], labels["first_horizon"] = stage, first
    labels["straddle_horizons"] = [j for j in label_h if per[str(j)]["floor_straddle"]]
    labels["guard_horizons"] = [j for j in label_h if per[str(j)]["reader_guard"]]
    labels["free_h_edge_horizons"] = [j for j in label_h if fh_edge[str(j)]]
    labels["trend"] = {name: {str(j): deltas.get(f"{name}|B={LABEL_BUDGET}|j={j}|all") for j in horizons}
                       for name in ("d_eq_h", "d_add_h", "anchor", "abt", "gate_eq_r2", "free_h-free_r2", "h_only-history")}
    labels["said_in_words"] = {"b8_b32_disagree": [x for j in label_h for x in per[str(j)]["b8_b32_disagree"]],
                               "negative_horizons": [j for j in label_h if per[str(j)]["negative"]],
                               "fallback_signal": [f"{name}|j={j}" for j in label_h for name in ("d_eq_h", "d_add_h")
                                                   if per[str(j)][f"{name}_fallback_reading"] == "SIGNAL"],
                               "free_h_edge_horizons": labels["free_h_edge_horizons"],
                               "h_only_above_history_tok": {str(j): bool(deltas[f"h_only-history_tok|B={LABEL_BUDGET}|j={j}|all"]["delta"] > 0)
                                                            for j in horizons if f"h_only-history_tok|B={LABEL_BUDGET}|j={j}|all" in deltas}}
    if labels["reproduce_ok"] is False:
        labels["label"] = "REPRODUCE-INVALID"
        labels["void"] = True
        labels["sentence"] = SENTENCE_VOID["REPRODUCE-INVALID"]
        for f_ in READING_FIELDS:
            if f_ != "sentence":
                labels[f_] = None
    else:
        labels["void"] = False
        labels["label"] = stage if first is None else f"{stage}@{first}"
        js = lambda lst: ", ".join(str(j) for j in lst)  # noqa: E731
        # the closing claim is WITHHELD by a straddle, a guard or a free_h grid edge at the FIRST horizon of a SURVIVES /
        # COMPLEMENTARY label (a later clean horizon does not rescue it), and by a straddle or a guard at ANY horizon under
        # ABSORBED; elsewhere each is said beside the claim
        withhold = []
        if stage in ("LEAD-TIME-SURVIVES", "LEAD-TIME-COMPLEMENTARY"):
            if per[str(first)]["floor_straddle"]:
                withhold.append(f"a CI95 straddles the +{MATERIAL} floor at horizon {first}")
            if first in labels["guard_horizons"]:
                withhold.append(f"the reader guard fired at horizon {first} (the hidden block degrades a reader there)")
            if first in labels["free_h_edge_horizons"]:
                withhold.append(f"free_h's lambda sits at the grid's edge at horizon {first} (the free arm is bounded by the grid there)")
        elif stage == "LEAD-TIME-ABSORBED":
            if labels["straddle_horizons"]:
                withhold.append(f"a CI95 straddles the +{MATERIAL} floor at horizon(s) {js(labels['straddle_horizons'])}")
            if labels["guard_horizons"]:
                withhold.append(f"the reader guard fired at horizon(s) {js(labels['guard_horizons'])} (the hidden block degrades a reader there)")
        if withhold:
            s = _WITHHELD.replace("{LABEL}", labels["label"]).replace("{WHY}", " and ".join(withhold))
        else:
            s = SENTENCE_STAGE[stage].replace("{J}", "" if first is None else str(first))
            if labels["straddle_horizons"]:
                s = s + _STAGE_STRADDLE.replace("{M}", str(MATERIAL)).replace("{JS}", js(labels["straddle_horizons"]))
            if labels["guard_horizons"]:
                s = s + _STAGE_GUARD.replace("{JS}", js(labels["guard_horizons"]))
            if labels["free_h_edge_horizons"]:
                s = s + _STAGE_EDGE.replace("{JS}", js(labels["free_h_edge_horizons"]))
        labels["sentence"] = s
    labels["rule"] = (f"readings SIGNAL iff CI95 lower > 0 and delta >= +{MATERIAL}, NEGATIVE iff CI95 upper < 0, else NOT-SHOWN, "
                      f"at B={LABEL_BUDGET}, on the horizon's positions (t >= 1, t + j < length) pooled over the two coverage "
                      f"unions; PRECONDITION REPRODUCE: this read's horizon-{REPRODUCE_HORIZON} rows for R2's nineteen arms equal "
                      f"the committed R2 state rows summed over their six strata into the two unions (hits-only mismatches on at "
                      f"most {REPRODUCE_NEAR_SHARE:.1%} of them within +-{REPRODUCE_NEAR_HITS} hit are NEAR; more, any needed "
                      f"mismatch, or a horizon-1 identity cell (D_eq^H, D_add^H, the anchor, free_h - free_r2 on all) that is not "
                      f"the R2 payload's to {IDENTITY_TOL:g} is INVALID = void, numbers only); per horizon the free arm's k and "
                      f"lambda selected jointly on that horizon's val positions (strict >, smaller k then smaller lambda on ties), "
                      f"every other arm's lambda on val at that k, the horizon-1 selections taken from the R2 payload; per horizon "
                      f"j in {list(LABEL_HORIZONS)} on all positions: H-SURVIVES iff history_bigram_r2 - free_h and history_all_h - "
                      f"free_h both SIGNAL, H-COMPLEMENTARY iff only the union, H-ABSORBS iff neither, H-INCONSISTENT iff only the "
                      f"equal-dims (cause reader iff the anchor's CI95 upper < 0, floor straddle iff a CI95 contains +{MATERIAL}, "
                      f"else neither); STAGE: LEAD-TIME-SURVIVES@j iff some horizon reads H-SURVIVES (j the smallest), else "
                      f"LEAD-TIME-COMPLEMENTARY@j iff some reads H-COMPLEMENTARY, else LEAD-TIME-ABSORBED iff every horizon reads "
                      f"H-ABSORBS, else LEAD-TIME-INCONSISTENT; a CI95 containing +{MATERIAL} is a floor straddle, flagged, and a "
                      f"straddle at a label horizon selects that horizon's not-settled sentence (at the first horizon of a SURVIVES / "
                      f"COMPLEMENTARY label, or under ABSORBED at any, the stage's closing claim is withheld; a later clean horizon "
                      f"does not rescue it); READER GUARD per horizon: where free_h - free_r2 or history_all_h - history_bigram_r2 on "
                      f"all reads NEGATIVE the horizon's label stays but its branch sentence is replaced (at the first horizon, or "
                      f"under ABSORBED at any, the closing claim is withheld); FREE-ARM EDGE: where free_h's selected lambda sits at "
                      f"an end of the grid at the first SURVIVES / COMPLEMENTARY horizon the closing claim is withheld, elsewhere it "
                      f"is said in words; a NEGATIVE D_eq^H and a NEGATIVE D_add^H each carry their own prefix; a fallback-scope "
                      f"SIGNAL on a label cell is said in words; the primary harvest's label is the label; the cross-harvest "
                      f"conditions (the closure line, the OQ-9 line) are executed at landing by the registration's text; NON-CRITERION, two "
                      f"pinned consequences (a dated STATUS line under F-26 and a dated K-6 STATUS line); no label reinstates stage "
                      f"2 and no further rung is registered at any horizon")
    return {"tables": tables, "deltas": deltas, "labels": labels}


# ---------------------------------------------------------------------------
# Provenance, I/O, CLI
# ---------------------------------------------------------------------------

def read_r2(path: Path) -> dict:
    """The committed R2 payload and its state file: the encoding, k and every lambda it carries (taken
    verbatim at horizon 1), its four identity cells and the rows REPRODUCE is checked against."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("registered") != r2.REGISTERED:
        raise SystemExit(f"{path} is not a generalising free baseline (R2) payload")
    prov = payload["provenance"]
    if prov.get("instrument_sha256") != R2_INSTRUMENT_SHA256:
        raise SystemExit(f"{path} was not written by the frozen R2 tool ({str(prov.get('instrument_sha256'))[:12]})")
    if prov.get("strat") is None or prov.get("encoding_source") != "strat":
        raise SystemExit(f"{path} did not take its encoding and lambdas from a committed stratified payload")
    if prov.get("smoke"):
        raise SystemExit(f"{path} is a smoke payload, not a registered R2 run")
    state_path = Path(str(path) + ".state.jsonl")
    if not state_path.exists():
        raise SystemExit(f"R2 state file {state_path} not found")
    header, rows = pr.load_state(state_path)
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit(f"{state_path}: row count differs from the R2 payload's")
    cells = {}
    for theirs in IDENTITY_CELLS.values():
        key = f"{theirs}|B={LABEL_BUDGET}|all"
        if key not in payload["conclusion"]["deltas"]:
            raise SystemExit(f"{path} lacks the identity cell {key}")
        cells[theirs] = payload["conclusion"]["deltas"][key]
    lam = prov["lambda_selected"]
    return {"path": rs._rel(path), "sha256": pr._sha(path), "state_path": rs._rel(state_path), "state_sha256": pr._sha(state_path),
            "git_commit": prov["git_commit"], "instrument_sha256": prov["instrument_sha256"],
            "encoding": prov["encoding_selected"], "k_selected": prov["k_selected"],
            "lambda_selected": {a: (None if lam.get(a) is None else float(lam[a])) for a in r2.ARMS_REQUIRED},
            "strat_path": prov["strat"]["path"], "strat_sha256": prov["strat"]["sha256"],
            "n_state_rows": int(payload["n_state_rows"]), "harvest_npz_sha256": prov["harvest_npz_sha256"],
            "replay_source_sha256": prov["replay_source"]["sha256"], "cells": cells, "_rows": rows}


def r2_reference(harvest_dir: Path, r2_arg: str | None, smoke: bool, out_under_results: bool) -> dict | None:
    if smoke:
        return None
    if r2_arg is not None and r2_arg.lower() == "none":
        if out_under_results:
            raise SystemExit("a registered run must read the committed R2 payload (--r2 none is refused under results/)")
        return None
    explicit = r2_arg is not None
    want = R2_OF_HARVEST.get(Path(harvest_dir).name)
    if not explicit:
        if want is None:
            if not out_under_results:
                return None
            raise SystemExit(f"no committed R2 payload is known for harvest {Path(harvest_dir).name}; pass --r2")
        path = ROOT / "results" / "real" / want
    else:
        path = Path(r2_arg)
        if out_under_results and path.resolve() != (ROOT / "results" / "real" / (want or "")).resolve():
            raise SystemExit("under results/ the R2 payload must be the registered one for this harvest")
    if not path.exists():
        if not explicit and not out_under_results:
            return None
        raise SystemExit(f"R2 payload {path} not found")
    return read_r2(path)


def _r2_header(ref: dict | None) -> dict | None:
    return None if ref is None else {k: v for k, v in ref.items() if k != "_rows"}


def _select_lambda(table: dict, lambdas) -> float:
    best_lam, best = None, -np.inf
    for lam in lambdas:
        v = table[str(float(lam))]
        if v > best:
            best, best_lam = v, float(lam)
    return best_lam


def _select_k_from_table(table: dict, k_grid, lambdas):
    best, best_k, best_lam = -np.inf, None, None
    for k in k_grid:
        for lam in lambdas:
            v = table[r2.k_tag(k)][str(float(lam))]
            if v > best:
                best, best_k, best_lam = v, k, float(lam)
    return best_k, best_lam


def run(args) -> dict:
    started = time.time()
    sha_start = pr._sha(Path(__file__))              # the bytes this run attests: hashed BEFORE any work, re-checked before writing
    git_start = pr._git()
    r2_sha = assert_frozen_r2()
    strat_sha = r2.assert_frozen_strat()
    twin_sha = rs.assert_frozen_twin()
    parent_sha = rb.assert_frozen_instrument()
    only = [int(s) for s in args.only_seeds.split(",")] if args.only_seeds else None
    smoke = bool(args.smoke_split_val or only is not None)
    out = Path(args.out)
    under = pr._under_results(out)
    if smoke and under:
        raise SystemExit("a smoke (--only-seeds / --smoke-split-val) may not write under results/")
    lambdas = tuple(float(x) for x in args.lambdas.split(",")) if getattr(args, "lambdas", None) else LAMBDAS
    k_grid = tuple(r2.k_of_tag(x) for x in args.k_grid.split(",")) if getattr(args, "k_grid", None) else K_GRID
    horizons = tuple(int(x) for x in args.horizons.split(",")) if getattr(args, "horizons", None) else HORIZONS
    if list(horizons) != sorted(set(horizons)) or horizons[0] != REPRODUCE_HORIZON or len(horizons) < 2:
        raise SystemExit(f"--horizons must be strictly increasing, start at {REPRODUCE_HORIZON} (the REPRODUCE horizon) and name "
                         f"at least one further horizon")
    if (lambdas != LAMBDAS or k_grid != K_GRID or horizons != HORIZONS) and under:
        raise SystemExit("a non-registered lambda grid, k grid or horizon set may not write under results/")
    if under and args.replay != "hf":
        raise SystemExit("under results/ the replay source must be the pinned checkpoint (--replay hf)")
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
    ref = r2_reference(Path(args.harvest), args.r2, smoke, under)
    if under and ref is not None and ref["encoding"] != "prev_table":
        raise SystemExit("under results/ the R2 payload's twin encoding must be prev_table (both committed R2 payloads carry it)")
    src = r2.load_replay_source(args.replay)
    if under and src["sha256"] != r2.REPLAY_SOURCE_SHA256:
        raise SystemExit(f"replay source sha {src['sha256'][:12]} is not the pinned {r2.REPLAY_SOURCE_SHA256[:12]}: refusing under results/")
    if under and (src["eps"] != 1e-5 or src["gates"].shape[0] != L):
        raise SystemExit("under results/ the replay's eps must be 1e-5 and its layer count 16 (config.json is outside the pinned sha)")
    if ref is not None and src["sha256"] != ref["replay_source_sha256"]:
        raise SystemExit("the replay source is not the one the R2 payload was read with; REPRODUCE would not be the same reader")
    data = pr.S3Data(args.harvest, only_seeds=only, smoke_split_val=args.smoke_split_val)
    if ref is not None and ref["harvest_npz_sha256"] != data.npz_shas:
        raise SystemExit("the R2 payload was read on different harvest shards than this run opens")
    hidden = r2.load_hidden(data)
    label_of_token, n_classes = load_label_space(args.buckets, args.glue)
    vocab = int(data.tokens.max()) + 1
    t_replay = time.time()
    replay = r2.replay_table(src, vocab)
    t_replay = time.time() - t_replay
    hz = Horizon(data, label_of_token, n_classes, hidden, replay, r2ref=ref, horizons=horizons, lambdas=lambdas, k_grid=k_grid)
    hz.fit_base()
    strata_counts, table_coverage = hz.strata_counts(), hz.table_coverage()     # the horizon-1 records (R2's)
    rows: list[dict] = []
    elapsed: dict = {}
    for j in hz.horizons:
        t0 = time.time()
        rows.extend(hz.run_horizon(j))
        elapsed[str(j)] = time.time() - t0
    hz.use_tables(REPRODUCE_HORIZON)
    encoding = hz.encoding_selected
    k_of_horizon = {str(j): hz.sel[j]["k_selected"] for j in hz.horizons}
    free_h_edge = {str(j): bool(float(hz.sel[j]["lambda_selected"]["free_h"]) in (lambdas[0], lambdas[-1])) for j in hz.horizons}
    conclusion = conclude(rows, encoding, k_of_horizon, None if ref is None else ref["_rows"],
                          None if ref is None else ref["cells"], horizons=hz.horizons, free_h_edge=free_h_edge)
    if pr._sha(Path(__file__)) != sha_start:
        raise SystemExit("the instrument's bytes changed during the run: refusing to write (rerun from the bytes to be attested)")
    git_commit, tracked = pr._git()
    if (git_commit, tracked) != git_start:
        raise SystemExit("the tree changed during the run (HEAD or the tracked status): refusing to write")
    prov = {
        "registered": REGISTERED,
        "git_commit": git_commit,
        "git_status_tracked": tracked,
        "instrument_sha256": sha_start,
        "frozen_r2": {"path": "tools/run_prefetch_r2.py", "sha256_lf": r2_sha},
        "frozen_strat": {"path": "tools/run_prefetch_strat.py", "sha256_lf": strat_sha},
        "frozen_twin": {"path": "tools/run_prefetch_bigram.py", "sha256_lf": twin_sha},
        "frozen_instrument": {"path": "tools/run_prefetch_readouts.py", "sha256_lf": parent_sha},
        "harvest_dir": str(args.harvest),
        "harvest_npz_sha256": data.npz_shas,
        "seeds": data.seeds,
        "smoke": smoke,
        "smoke_split_val": bool(args.smoke_split_val),
        "r2": _r2_header(ref),
        "replay_source": r2._source_record(src),
        "replay_source_pinned": r2.REPLAY_SOURCE_SHA256,
        "replay_source_matches_pinned": bool(src["sha256"] == r2.REPLAY_SOURCE_SHA256),
        "replay_vocab": int(vocab),
        "replay_probe": r2.replay_probe(replay),
        "replay_seconds": t_replay,
        "hidden": {"width": int(hidden.shape[2]), "dtype": str(hidden.dtype), "train_positions": hz.h_n,
                   "kept_variance_share": hz.h_kept_share, "eigen_top8": hz.h_eigen_top, "eigen_1024th": hz.h_eigen_last,
                   "eigen_1025th": hz.h_eigen_next},
        "label_space": {"buckets": str(args.buckets), "buckets_sha256": pr._sha(args.buckets),
                        "glue": str(args.glue), "glue_sha256": pr._sha(args.glue), "n_classes": int(n_classes),
                        "n_tokens": int(label_of_token.shape[0])},
        "constants": {"budgets": list(BUDGETS), "horizons": list(hz.horizons), "label_horizons": list(LABEL_HORIZONS),
                      "reproduce_horizon": REPRODUCE_HORIZON, "lambdas": list(lambdas), "k_grid": [r2.k_tag(k) for k in k_grid],
                      "label_budget": LABEL_BUDGET, "material": MATERIAL, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
                      "chunk": CHUNK, "scopes": list(SCOPES), "unions": {k: list(v) for k, v in UNIONS.items()},
                      "reproduce_near_share": REPRODUCE_NEAR_SHARE, "reproduce_near_hits": REPRODUCE_NEAR_HITS,
                      "identity_tol": IDENTITY_TOL, "identity_cells": dict(IDENTITY_CELLS), "token_probe": list(r2.TOKEN_PROBE),
                      "arm_dims": {a: arm_dims(a, encoding) for a in ARMS_J1}, "arms_h": list(arms_h(encoding)),
                      "arm_k": {a: r2.k_tag(ARM_K[a]) for a in ARM_K}},
        "n_positions": hz.n_positions,
        "n_test_prompts": int(hz.prompt_ids["test"].shape[0]),
        "strata_counts": strata_counts,
        "table_coverage": table_coverage,
        "encoding_selected": encoding,
        "encoding_source": "r2" if ref is not None else "val",
        "selection": {str(j): hz.sel[j] for j in hz.horizons},
        "elapsed_per_horizon_s": elapsed,
        "blas": rs.blas_info(),
        "args": redact_args(vars(args)),
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "started_unix": started,
        "runtime_s": time.time() - started,
    }
    payload = {"registered": REGISTERED, "provenance": prov, "conclusion": conclusion, "n_state_rows": len(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    header = {"state_header": True, "registered": REGISTERED, "harvest_npz_sha256": data.npz_shas, "smoke": smoke,
              "encoding": encoding, "horizons": list(hz.horizons), "k_of_horizon": k_of_horizon,
              "lambda_selected": {str(j): hz.sel[j]["lambda_selected"] for j in hz.horizons},
              "r2": _r2_header(ref), "replay_source_sha256": src["sha256"]}
    rs._write_lf(state_path, "".join(json.dumps(x) + "\n" for x in [header] + rows))
    rs._write_lf(out, json.dumps(payload, indent=1))
    rs._write_lf(meta_path, json.dumps(prov, indent=1))
    print_summary(payload)
    return payload


def conclude_from(payload_path: Path) -> dict:
    assert_frozen_r2()
    r2.assert_frozen_strat()
    rs.assert_frozen_twin()
    rb.assert_frozen_instrument()
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if payload.get("registered") != REGISTERED:
        raise SystemExit("payload is not a horizon read payload")
    header, rows = pr.load_state(Path(str(payload_path) + ".state.jsonl"))
    prov = payload["provenance"]
    if header["harvest_npz_sha256"] != prov["harvest_npz_sha256"]:
        raise SystemExit("state header harvest shas differ from the payload's")
    if header.get("encoding") != prov["encoding_selected"]:
        raise SystemExit("state header encoding differs from the payload's")
    if header.get("horizons") != prov["constants"]["horizons"]:
        raise SystemExit("state header horizons differ from the payload's")
    if header.get("k_of_horizon") != {j: prov["selection"][j]["k_selected"] for j in prov["selection"]}:
        raise SystemExit("state header k per horizon differs from the payload's")
    if header.get("lambda_selected") != {j: prov["selection"][j]["lambda_selected"] for j in prov["selection"]}:
        raise SystemExit("state header lambdas differ from the payload's")
    if header.get("r2") != prov["r2"]:
        raise SystemExit("state header R2 reference differs from the payload's")
    if header.get("replay_source_sha256") != prov["replay_source"]["sha256"]:
        raise SystemExit("state header replay source sha differs from the payload's")
    if header.get("registered") != REGISTERED or bool(header.get("smoke")) != bool(prov.get("smoke")):
        raise SystemExit("state header registration or smoke flag differs from the payload's")
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit("state row count differs from the payload's")
    lambdas = [float(x) for x in prov["constants"]["lambdas"]]
    k_grid = [r2.k_of_tag(x) for x in prov["constants"]["k_grid"]]
    lam_keys = {str(float(x)) for x in lambdas}
    horizons = [int(j) for j in prov["constants"]["horizons"]]
    if [int(j) for j in prov["selection"]] != horizons:
        raise SystemExit("the payload's selection records do not cover its horizons")
    ref_rec = prov.get("r2")
    for j in horizons:
        sel = prov["selection"][str(j)]
        kt = sel["k_val_table"]
        if set(kt) != {r2.k_tag(k) for k in k_grid} or any(set(row) != lam_keys for row in kt.values()):
            raise SystemExit(f"the payload's k val table at horizon {j} does not carry its own k and lambda grids")
        want_arms = list(ARMS_J1 if j == REPRODUCE_HORIZON else arms_h(header["encoding"]))
        if sel["arms"] != want_arms:
            raise SystemExit(f"the payload's arm list at horizon {j} is not the registered one")
        taken = bool(j == REPRODUCE_HORIZON and ref_rec is not None)
        want_source = {a: (None if a == "replay_zerofit" else "r2" if (taken and a != "marginal") else "val") for a in want_arms}
        if sel["lambda_source"] != want_source:
            raise SystemExit(f"the payload's lambda sources at horizon {j} are not what the registration pins")
        ridge_val = [a for a in want_arms if a != "replay_zerofit" and not (taken and a in ARMS_TWIN)]
        for arm in ridge_val:
            if set(sel["val_table"].get(arm, {})) != lam_keys:
                raise SystemExit(f"the payload's val table for {arm} at horizon {j} does not carry its own lambda grid")
        k_best, lam_best = _select_k_from_table(kt, k_grid, lambdas)
        if taken:
            # the R2 selections were TAKEN; the val re-selection is recorded beside them and must be what the tables say
            if sel["k_selected"] != ref_rec["k_selected"]:
                raise SystemExit("the payload's horizon-1 k is not the R2 payload's")
            if bool(sel.get("k_grid_edge")) != bool(r2.k_of_tag(sel["k_selected"]) in (k_grid[0], k_grid[-1])):
                raise SystemExit("the payload's horizon-1 k grid-edge flag is not what the taken k implies")
            for a in ARMS_TWIN + ARMS_R2:
                if a == "replay_zerofit":
                    continue
                if float(sel["lambda_selected"][a]) != float(ref_rec["lambda_selected"][a]):
                    raise SystemExit(f"the payload's horizon-1 lambda for {a} is not the R2 payload's")
                if sel["lambda_grid_edge"].get(a) is not None:
                    raise SystemExit(f"the payload's horizon-1 grid-edge flag for {a} is not null (a taken lambda carries none)")
            re = sel["reselect"]
            if re is None or r2.k_tag(k_best) != re["k"] or lam_best != float(re["lambda"]["free_r2"]):
                raise SystemExit("the payload's horizon-1 re-selection of (k, lambda) for free_r2 is not what its k table selects")
            if bool(re.get("k_grid_edge")) != bool(k_best in (k_grid[0], k_grid[-1])):
                raise SystemExit("the payload's horizon-1 re-selection k grid-edge flag is not what its k implies")
            if sel["val_table"].get("free_r2") != kt[re["k"]]:
                raise SystemExit("the payload's horizon-1 free_r2 val table is not its k table's row at the re-selected k")
            for a in RESELECT_ARMS:
                if a == "free_r2":
                    continue
                if _select_lambda(sel["val_table"][a], lambdas) != float(re["lambda"][a]):
                    raise SystemExit(f"the payload's horizon-1 re-selection of lambda for {a} is not what its val table selects")
            want_match = bool(re["k"] == ref_rec["k_selected"] and all(float(re["lambda"][a]) == float(ref_rec["lambda_selected"][a]) for a in RESELECT_ARMS))
            if bool(re["matches_r2"]) != want_match:
                raise SystemExit("the payload's horizon-1 re-selection flag is not what its tables imply")
            lam_m = float(sel["lambda_selected"]["marginal"])
            if _select_lambda(sel["val_table"]["marginal"], lambdas) != lam_m:
                raise SystemExit("the payload's horizon-1 lambda for marginal is not the one its val table selects")
            if bool(sel["lambda_grid_edge"].get("marginal")) != bool(lam_m in (lambdas[0], lambdas[-1])):
                raise SystemExit("the payload's horizon-1 grid-edge flag for marginal is not what its lambda implies")
        else:
            if r2.k_tag(k_best) != sel["k_selected"] or lam_best != float(sel["lambda_selected"]["free_r2"]):
                raise SystemExit(f"the payload's (k, lambda) for free_r2 at horizon {j} is not the pair its k table selects")
            if bool(sel.get("k_grid_edge")) != bool(k_best in (k_grid[0], k_grid[-1])):
                raise SystemExit(f"the payload's k grid-edge flag at horizon {j} is not what its selected k implies")
            if sel["val_table"].get("free_r2") != kt[r2.k_tag(k_best)]:
                raise SystemExit(f"the payload's free_r2 val table at horizon {j} is not its k table's row at the selected k")
            for arm in sel["arms"]:
                if arm in ("free_r2", "replay_zerofit"):
                    continue
                if _select_lambda(sel["val_table"][arm], lambdas) != float(sel["lambda_selected"][arm]):
                    raise SystemExit(f"the payload's lambda for {arm} at horizon {j} is not the one its val table selects")
            for arm in sel["arms"]:
                if arm == "replay_zerofit":
                    continue
                lam = float(sel["lambda_selected"][arm])
                if bool(sel["lambda_grid_edge"].get(arm)) != bool(lam in (lambdas[0], lambdas[-1])):
                    raise SystemExit(f"the payload's grid-edge flag for {arm} at horizon {j} is not what its lambda implies")
    if pr._under_results(Path(payload_path)):
        if prov.get("smoke") or header.get("r2") is None:
            raise SystemExit("a payload under results/ must be a registered run with an R2 record")
        if lambdas != list(LAMBDAS) or prov["constants"]["k_grid"] != [r2.k_tag(k) for k in K_GRID] or horizons != list(HORIZONS):
            raise SystemExit("a payload under results/ must carry the registered lambda grid, k grid and horizons")
        if prov["replay_source"].get("sha256") != r2.REPLAY_SOURCE_SHA256 or prov["replay_source"].get("kind") != "hf":
            raise SystemExit("a payload under results/ must carry the pinned replay source")
    r2_rows, r2_cells = None, None
    rr = header.get("r2")
    if rr is not None:
        if rr["encoding"] != header["encoding"]:
            raise SystemExit("the state header's encoding is not the R2 payload's")
        rpath = ROOT / rr["path"] if not Path(rr["path"]).is_absolute() else Path(rr["path"])
        if not rpath.exists():
            raise SystemExit(f"the committed R2 payload {rr['path']} is not present; REPRODUCE cannot be recomputed")
        fresh = read_r2(rpath)
        if fresh["sha256"] != rr["sha256"] or fresh["state_sha256"] != rr["state_sha256"]:
            raise SystemExit(f"the committed R2 payload {rr['path']} is not the one this run read "
                             f"(sha {rr['sha256'][:12]} -> {fresh['sha256'][:12]}; state {rr['state_sha256'][:12]} -> "
                             f"{fresh['state_sha256'][:12]})")
        if _r2_header(fresh) != rr:
            raise SystemExit(f"the committed R2 payload {rr['path']} differs from the header's record of it beyond the shas")
        r2_rows, r2_cells = fresh["_rows"], fresh["cells"]
    fh_edge = {j: bool(float(header["lambda_selected"][j]["free_h"]) in (lambdas[0], lambdas[-1])) for j in header["lambda_selected"]}
    got = conclude(rows, header["encoding"], header["k_of_horizon"], r2_rows, r2_cells, horizons=tuple(horizons), free_h_edge=fh_edge)
    if json.dumps(got, sort_keys=True) != json.dumps(payload["conclusion"], sort_keys=True):
        raise SystemExit("RECOMPUTE MISMATCH: the state file does not reproduce the payload's conclusion")
    tag = " (SMOKE — not evidence)" if prov.get("smoke") else ""
    print(f"conclude-from: state file reproduces the payload exactly{tag}")
    print_summary(payload)
    return got


def _fmt(d: dict | None) -> str:
    return "n/a" if d is None else f"{d['delta']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]"


def print_summary(payload: dict) -> None:
    c = payload["conclusion"]; lab = c["labels"]; prov = payload["provenance"]
    print(f"LABEL: {lab.get('label')}   (smoke={prov.get('smoke')}; encoding={lab.get('encoding')} from "
          f"{prov.get('encoding_source')}; k per horizon={lab.get('k_of_horizon')}; void={lab.get('void')})")
    rep = lab.get("reproduce")
    if rep is None:
        print("  REPRODUCE: not applicable (no R2 payload read)")
    else:
        print(f"  REPRODUCE: {lab.get('reproduce_status')} (rows {rep['status']})  R2 union rows {rep['n_r2_union_rows']}  compared "
              f"{rep['n_compared']}  missing {rep['missing_here']}  extra {rep['extra_here']}  needed mismatches "
              f"{rep['needed_mismatch_rows']}  hits mismatches {rep['hits_mismatch_rows']}  max |gap| {rep['max_abs_hits_gap']}  "
              f"identity (D_eq^H, D_add^H, anchor, free_h - free_r2 at j=1 = R2's): {lab.get('identity_matches_r2')}")
    if lab.get("label") == "INCOMPLETE":
        print("missing arms:", lab["missing_arms"], "missing label cells:", lab["missing_label_cells"]); return
    for j, sc in lab["scopes"].items():
        print(f"  j={j} positions " + "  ".join(f"{s} {v.get('positions', 0)} ({v.get('share')})" for s, v in sc.items()))
    if lab.get("horizons"):
        for j, hj in lab["horizons"].items():
            print(f"  j={j} {str(hj['q']):16s} D_eq^H {str(hj['d_eq_h_reading']):10s} {_fmt(hj['d_eq_h'])}  D_add^H "
                  f"{str(hj['d_add_h_reading']):10s} {_fmt(hj['d_add_h'])}  anchor {_fmt(hj['anchor'])}  free_h-free_r2 "
                  f"{_fmt(hj['free_h_gain'])}  straddle={hj['floor_straddle']} guard={hj['reader_guard']} neg={hj['negative']}")
            print(f"       covered D_eq^H {_fmt(hj['d_eq_h_covered'])} D_add^H {_fmt(hj['d_add_h_covered'])} | fallback D_eq^H "
                  f"{_fmt(hj['d_eq_h_fallback'])} D_add^H {_fmt(hj['d_add_h_fallback'])}  b8/b32 {hj['b8_b32_disagree']}")
            print(f"       sentence: {hj['sentence']}")
        print(f"  STAGE {lab.get('stage')} first={lab.get('first_horizon')} straddles={lab.get('straddle_horizons')} guards={lab.get('guard_horizons')} "
              f"free_h edges={lab.get('free_h_edge_horizons')}")
        print(f"  sentence: {lab['sentence']}")
        print(f"  said in words: {lab.get('said_in_words')}")
        tr = lab.get("trend") or {}
        for name, by_j in tr.items():
            print(f"  trend {name:14s} " + " | ".join(f"j={j} {_fmt(d)}" for j, d in by_j.items()))
    for j in prov["constants"]["horizons"]:
        for B in BUDGETS:
            parts = []
            for name, _, _ in DELTA_PAIRS:
                d = c["deltas"].get(f"{name}|B={B}|j={j}|all")
                if d:
                    parts.append(f"{name} {_fmt(d)}")
            for i in range(0, len(parts), 4):
                print((f"  j={j} B={B:2d} all " if i == 0 else f"  {'':14s}") + " | ".join(parts[i:i + 4]))
        for B in BUDGETS:
            arms = prov["selection"][str(j)]["arms"]
            print(f"  j={j} B={B:2d} " + " | ".join(f"{a} {c['tables'][f'{a}|B={B}|j={j}|all']['all']['point']:.4f}"
                                                  for a in arms if f"{a}|B={B}|j={j}|all" in c["tables"]))
    for j, sel in prov["selection"].items():
        print(f"  j={j} k={sel['k_selected']} edge={sel['k_grid_edge']} lambda={sel['lambda_selected']} source={sel['lambda_source']} "
              f"grid-edge={sel['lambda_grid_edge']} reselect={sel.get('reselect')}")
    print("  elapsed per horizon:", prov.get("elapsed_per_horizon_s"))
    print("  hidden:", prov.get("hidden"))
    print("  replay source:", {k: v for k, v in (prov.get("replay_source") or {}).items() if k in ("kind", "sha256", "snapshot", "path")},
          "matches pinned:", prov.get("replay_source_matches_pinned"))
    print("  blas:", prov.get("blas"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default=str(ROOT / "results" / "real" / "harvest_moe"))
    ap.add_argument("--out", default=str(ROOT / "results" / "real" / "prefetch_horizon_s3.json"))
    ap.add_argument("--buckets", default=str(pr.BUCKETS16))
    ap.add_argument("--glue", default=str(pr.GLUE16))
    ap.add_argument("--r2", default=None,
                    help="the committed R2 payload whose encoding, k, lambdas and state rows this read takes at horizon 1 "
                         "(default: derived from the harvest name; 'none' only outside results/)")
    ap.add_argument("--replay", default="hf",
                    help="'hf' = the pinned cached checkpoint snapshot (required under results/); or a path to an .npz "
                         "fixture (embed, gates, norms, eps) for tests")
    ap.add_argument("--only-seeds", default=None, help="smoke only: comma-separated generation seeds")
    ap.add_argument("--smoke-split-val", action="store_true",
                    help="smoke only: keep the val prompts and re-split them by (prompt_idx // 7) %% 3")
    ap.add_argument("--lambdas", default=None, help="tests/smoke only: comma-separated grid (refused under results/)")
    ap.add_argument("--k-grid", default=None, help="tests/smoke only: comma-separated k grid, 'inf' allowed (refused under results/)")
    ap.add_argument("--horizons", default=None, help="tests/smoke only: comma-separated horizons starting at 1 (refused under results/)")
    ap.add_argument("--conclude-from", default=None, help="recompute a payload's conclusion from its state file")
    args = ap.parse_args(argv)
    if args.conclude_from:
        conclude_from(Path(args.conclude_from))
        return
    run(args)


if __name__ == "__main__":
    main()

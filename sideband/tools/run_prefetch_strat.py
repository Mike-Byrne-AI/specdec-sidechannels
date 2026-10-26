#!/usr/bin/env python
"""tools/run_prefetch_strat.py — OQ-9 STAGE-1 POST-HOC DIAGNOSTIC: the STRATIFIED
COVERAGE READ of the free-bigram twin's margin (F-26's 2026-10-01 status line), with a
free p_t-summary block beside it.

Registered 2026-10-01 as a dated AMENDMENT to the free-bigram twin block in
docs/BLUEPRINT.md ("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION"), written
before any readout of it ran on either S3 harvest; amended in the critic's design
round the same day, before the freeze. NON-CRITERION for every finding's mechanical
label; it executes ONE pinned consequence, a dated STATUS line under F-26 on the
standing of the twin's coverage caveat. CPU only; numpy only — nothing in this file
imports torch, so its tests run in CI.

WHY. The twin's SURVIVES label carries a COVERAGE CAVEAT: an unregistered val-only
diagnostic put the material part of the pooled margin D_eq = history_tok -
FREE_BIGRAM on positions whose token key the train tables never saw. Two
questions, read on the same positions:
  Q1 (COVERAGE)  where does the surviving margin sit — on the positions whose
                 token keys the train tables saw, or on the positions with at
                 least one unseen key, where a free table reads the marginal?
  Q2 (p_t)       at an unseen current token S[t] predates tokens[t] and can carry
                 only the forward's PREDICTION of it (information p_t holds, free
                 under D-5 in the information sense) or context: with a free block
                 of p_t's stored summaries in BOTH arms, does the twin's verdict
                 stand — does the address block still beat the equal-dims free
                 block, and does the address stream still add over the union?

THE FROZEN INSTRUMENTS. tools/run_prefetch_bigram.py (the twin; sha
10599fa98c27..., attested by both committed twin payloads) is imported by bare
module name and NEVER edited; this file refuses to run unless its LF-normalised
bytes still hash to that sha. The twin's own import-time assertion covers the
stage-1 parent tools/run_prefetch_readouts.py (8529532d4d78...). The twin's
Bigram class is reused for the tables, the leave-one-prompt-out reads, the
bigram positions and the design; its Gram is accumulated here with the twin's
own statements on the same chunks, and the twin's nine arms are solved at the
twin's SELECTED lambdas read from the committed twin payload (encoding and
lambdas taken verbatim, never re-selected), so those arms ARE the twin's readers.

STRATA (per test position, from the twin's TRAIN tables; a train occurrence adds
16 x 8 = 128 counts, so a token's count is a multiple of 128 or zero and "unseen"
is per token). cu = TABLE_CUR has no train count at tokens[t]; pu = TABLE_PREV
none at tokens[t-1]. Six disjoint strata partition the positions:
  covered_1 | covered_2_4 | covered_5p   not cu, not pu; split by the SMALLER of
                                         the two keys' train occurrence counts
                                         (1 / 2..4 / 5 or more)
  cur_unseen (cu, not pu) | prev_unseen (not cu, pu) | both_unseen (cu, pu)
Unions recomputed in conclude(): covered = the three covered strata (the Q1 gate's
scope); fallback = the three unseen strata; all = every position.

THE p_t BLOCK. PT(t) = [mass16[t] (16) ++ mass64[t] (64) ++ entropy[t] / ln V (1)],
81 float64 coordinates in [0, 1]: the harvest's stored summaries of the output
distribution p_t of forward t, the distribution tokens[t] was sampled from (the
stored argmax at index t equals tokens[t] on 0.72 of the train positions of
moe_s0, against 0.01 / 0.02 for the neighbours; the harvester stores the masses
and entropy of the forward whose routing is slots[t], then samples tokens[t] from
that p). V = the label space's token count. p_t is free in the information sense
(the prefetcher runs beside the model that computed it); it arrives after the LM
head while S[t] arrives layer by layer, so nothing here is a timing claim.

DESIGN. The twin's [S[t] ++ TABLE_CUR(tokens[t]) ++ TABLE_PREV(tokens[t-1]) ++
TABLE_CUR(tokens[t-1]) ++ bias] (4097 columns, bias at 4096) extended by PT's 81
columns AFTER the bias, so every twin column keeps its index; the twin's Gram is
accumulated exactly as the twin does and the cross terms with PT beside it.
ARMS (dims): the twin's nine at the twin's lambdas —
  history 1025, free_tok 1025, history_tok 2049, free_bigram_b / _a 2049,
  history_bigram_b / _a 3073, free_all 3073, history_all 4097
  (FREE_BIGRAM / HISTORY_BIGRAM = the twin's selected encoding)
and FOUR new arms, lambdas selected on the pooled VAL positions (frozen grid):
  pt_only            PT                                           (82)
  free_bigram_pt     TABLE_CUR(tokens[t]) ++ selected prev table ++ PT   (2130)
  history_tok_pt     S[t] ++ TABLE_CUR(tokens[t]) ++ PT            (2130)
  history_bigram_pt  S[t] ++ free_bigram_pt's blocks               (3154)

READOUTS at B = 16 (8 and 32 reported), paired per prompt within a stratum,
cluster bootstrap over the 30 test prompts (n_boot 2000, seed 0):
  PRECONDITION REPRODUCE  the stratified rows summed over the six strata equal the
                          committed twin's state rows (hits AND needed); hits-only
                          mismatches on at most 0.1% of the twin's rows, each
                          within +-1 hit, are REPRODUCE-NEAR (said in words); more,
                          any needed mismatch, or an EXACT whose pooled D_eq does
                          not equal the twin's committed D_eq (the identity check)
                          is REPRODUCE-INVALID (void)
  Q1 GATE    D_eq^COV  = history_tok - FREE_BIGRAM on covered
  Q1 BRANCH  D_eq^FB   = the same on fallback
  Q2 GATE    D_eq^PT   = history_tok_pt - free_bigram_pt on all (equal dims, PT on
                         both sides: the twin's D_eq with the summaries added)
  Q2 BRANCH  D_add^PT  = history_bigram_pt - free_bigram_pt on all (the union)
  reported per scope: ADDRESS-BEYOND-TOKEN, BIGRAM GAIN, D_add, PT GAIN =
  free_bigram_pt - FREE_BIGRAM, D_pt = history_tok - free_bigram_pt (the
  asymmetric replacement read: the free side holds the previous-token table and
  the summaries, the address side neither), D_eq^PT, D_add^PT, pt_only - free_tok,
  history_tok_pt - history_tok, history_bigram_pt - history_tok_pt (the dilution
  anchor of D_add^PT - D_eq^PT); every arm's point and CI; scope shares.
Readings by the frozen rule: SIGNAL iff CI95 lower > 0 and point >= +0.05;
NEGATIVE iff CI95 upper < 0; else NOT-SHOWN. A CI95 containing the floor is a
FLOOR STRADDLE, flagged on all four label-bearing readings; a straddle on the Q1
gate, or on EITHER Q2 reading, selects the pinned sentence that says "not settled
at this power" instead of claiming the branch (so PT-ABSORBS strikes stage 2 only
when neither Q2 CI contains the floor); a straddle on the Q1 branch is said in
words. A void payload carries its deltas as numbers and null reading fields.
LABELS (mechanical; the PRIMARY harvest's label is the label):
  REPRODUCE-INVALID | INCOMPLETE                              (void: numbers only)
  Q1: COVERED-MATERIAL   D_eq^COV SIGNAL
      FALLBACK-LOCATED   D_eq^COV not SIGNAL and D_eq^FB SIGNAL
      UNLOCATED          neither SIGNAL
  Q2: PT-SURVIVES        D_eq^PT SIGNAL and D_add^PT SIGNAL
      PT-COMPLEMENTARY   D_eq^PT not SIGNAL and D_add^PT SIGNAL
      PT-ABSORBS         neither SIGNAL
      PT-INCONSISTENT    D_eq^PT SIGNAL and D_add^PT not SIGNAL (a knife-edge;
                         "reader" only if history_bigram_pt - history_tok_pt has
                         CI95 upper < 0, else "floor straddle")
  label = "Q1 / Q2", e.g. "FALLBACK-LOCATED / PT-SURVIVES".
--conclude-from recomputes every table, CI, delta, the REPRODUCE check against the
committed twin state file (re-read and re-hashed, every header field compared) and
every label from the state file, and refuses a payload whose stored numbers differ.
Evidence files are written with LF newlines on every platform.

Usage:
  python tools/run_prefetch_strat.py --harvest results/real/harvest_moe \
      --out results/real/prefetch_strat_s3.json
  python tools/run_prefetch_strat.py --harvest results/real/harvest_moe_r \
      --out results/real/prefetch_strat_s3_r.json
  python tools/run_prefetch_strat.py --conclude-from results/real/prefetch_strat_s3.json
Smoke (disclosed in the registration; refused under results/; no twin payload is read):
  python tools/run_prefetch_strat.py --harvest results/real/harvest_moe_r \
      --only-seeds 8 --smoke-split-val --twin none --out <scratch>/strat_smoke.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import run_prefetch_readouts as pr  # noqa: E402  (the FROZEN stage-1 instrument)
import run_prefetch_bigram as rb  # noqa: E402  (the FROZEN twin; asserts its parent at import)
from sideband.probes import load_label_space  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402

# the twin's LF-normalised sha256 (= tests/test_prefetch_bigram_landing.py INSTRUMENT_SHA256,
# = both committed twin payloads' provenance.instrument_sha256)
TWIN_INSTRUMENT_SHA256 = "10599fa98c276751f3296ecff6815aae07a701e35d13b5a2fb6ff8170ba7a11a"


def assert_frozen_twin(path: Path | None = None) -> str:
    """Refuse unless the twin on disk still hashes (CRLF -> LF) to the attested sha."""
    p = Path(path) if path is not None else Path(rb.__file__)
    sha = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != TWIN_INSTRUMENT_SHA256:
        raise SystemExit(f"{p}: sha {sha[:12]} is not the frozen twin {TWIN_INSTRUMENT_SHA256[:12]} — refusing")
    return sha


assert_frozen_twin()
rb.assert_frozen_instrument()

REGISTERED = ("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION "
              "(docs/BLUEPRINT.md, 2026-10-01 amendment; post-hoc diagnostic; NON-CRITERION)")
E, L, K, D = rb.E, rb.L, rb.K, rb.D
BUDGETS, LAMBDAS = rb.BUDGETS, rb.LAMBDAS
LABEL_BUDGET, MATERIAL, N_BOOT, BOOT_SEED, CHUNK = rb.LABEL_BUDGET, rb.MATERIAL, rb.N_BOOT, rb.BOOT_SEED, rb.CHUNK
HORIZON = rb.HORIZON
D_PT = 16 + 64 + 1                       # mass16 ++ mass64 ++ entropy / ln V
BIAS_COL = rb.D_X - 1                    # 4096: the twin's bias column keeps its index
PT_COLS = np.arange(rb.D_X, rb.D_X + D_PT)
D_X = rb.D_X + D_PT                      # 4178
COUNTS_PER_OCCURRENCE = L * K            # 128: one train occurrence of a key adds this to its table count
STRATA = ("covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen")
UNIONS = {"covered": ("covered_1", "covered_2_4", "covered_5p"),
          "fallback": ("cur_unseen", "prev_unseen", "both_unseen"),
          "all": STRATA}
SCOPES = STRATA + tuple(UNIONS)
ARMS_TWIN = rb.ARMS_REQUIRED
ARMS_PT = ("pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt")
ARMS_REQUIRED = ARMS_TWIN + ARMS_PT
PT_BLOCKS = {"pt_only": (), "free_bigram_pt": ("cur", "prev"), "history_tok_pt": ("hist", "cur"),
             "history_bigram_pt": ("hist", "cur", "prev")}
TWIN_OF_HARVEST = {"harvest_moe": "prefetch_bigram_s3.json", "harvest_moe_r": "prefetch_bigram_s3_r.json"}
OUT_OF_HARVEST = {"harvest_moe": "prefetch_strat_s3.json", "harvest_moe_r": "prefetch_strat_s3_r.json"}
REPRODUCE_NEAR_SHARE = 0.001             # hits-only mismatches tolerated as NEAR: at most this share of twin rows ...
REPRODUCE_NEAR_HITS = 1                  # ... each within +-1 hit
SPLITS = pr.SPLITS


def arm_cols(arm: str, encoding: str) -> np.ndarray:
    """Design columns of an arm: the twin's arms exactly as the twin indexes them; the PT arms
    = their twin blocks (the selected previous-token table where 'prev') ++ bias ++ PT."""
    if arm in rb.ARM_BLOCKS:
        return rb.arm_cols(arm)
    if encoding not in rb.ENCODINGS:
        raise SystemExit(f"unknown encoding {encoding!r}")
    prev = "prev_" + rb.ENC_SUFFIX[encoding]
    blocks = [prev if b == "prev" else b for b in PT_BLOCKS[arm]]
    cols = [np.arange(*rb.BLOCKS[b]) for b in blocks]
    head = np.concatenate(cols) if cols else np.zeros(0, dtype=np.int64)
    return np.r_[head, BIAS_COL, PT_COLS]


def arm_dims(arm: str, encoding: str) -> int:
    return int(arm_cols(arm, encoding).shape[0])


def blas_info() -> dict:
    """The BLAS numpy was built against and the thread caps in force: a different summation
    order is the one named way a clean rerun could miss REPRODUCE EXACT."""
    out: dict = {"cpu_count": os.cpu_count()}
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        out[var] = os.environ.get(var)
    try:
        deps = np.show_config(mode="dicts").get("Build Dependencies", {})
        out["blas"] = {"name": deps.get("blas", {}).get("name"), "version": deps.get("blas", {}).get("version"),
                       "lapack": deps.get("lapack", {}).get("name")}
    except Exception:  # pragma: no cover - older numpy
        out["blas"] = None
    return out


# ---------------------------------------------------------------------------
# The computation (a Bigram subclass: tables, lopo reads, positions and design reused)
# ---------------------------------------------------------------------------

class Strat(rb.Bigram):
    """Fits the twin's tables and Gram (the twin's own statements) plus the cross terms
    with the p_t block; evaluates the twin's arms and the PT arms on the bigram
    positions of a split, split into the six coverage strata."""

    def __init__(self, data: pr.S3Data, label_of_token: np.ndarray, n_classes: int, twin: dict | None = None,
                 lambdas=LAMBDAS, chunk: int = CHUNK):
        super().__init__(data, label_of_token, n_classes, lambdas=lambdas, chunk=chunk)
        self.twin = twin
        self.ent_scale = float(np.log(label_of_token.shape[0]))
        if twin is not None:
            self.encoding_selected = twin["encoding"]
            for arm in ARMS_TWIN:
                self.lambda_selected[arm] = float(twin["lambda_selected"][arm])
                self.grid_edge[arm] = None                      # the twin's flag; not re-derived here
        self.lambda_source = {a: ("twin" if twin is not None else "val") for a in ARMS_TWIN}
        self.lambda_source.update({a: "val" for a in ARMS_PT})

    # ----- the p_t block --------------------------------------------------------------
    def pt_vec(self, rows, anchors) -> np.ndarray:
        d = self.d
        return np.hstack([d.mass16[rows, anchors], d.mass64[rows, anchors],
                          (d.entropy[rows, anchors] / self.ent_scale)[:, None]])

    def design_pt(self, rows, anchors, lopo: bool = False):
        X, Y = self.design(rows, anchors, lopo=lopo)        # the twin's design, bias last
        return np.hstack([X, self.pt_vec(rows, anchors)]), Y

    # ----- strata ---------------------------------------------------------------------
    def strata_masks(self, rows, anchors) -> dict:
        """The six strata from the TRAIN tables: unseen-key strata by which table is blind;
        covered positions split by the smaller of the two keys' train occurrence counts."""
        d = self.d
        c_cur = self.token_table[d.tokens[rows, anchors]].sum(axis=(1, 2))
        c_prev = self.prev_table[d.tokens[rows, anchors - 1]].sum(axis=(1, 2))
        cu, pu = c_cur == 0, c_prev == 0
        covered = ~cu & ~pu
        occ = np.minimum(c_cur, c_prev) // COUNTS_PER_OCCURRENCE
        return {"covered_1": covered & (occ == 1), "covered_2_4": covered & (occ >= 2) & (occ <= 4),
                "covered_5p": covered & (occ >= 5),
                "cur_unseen": cu & ~pu, "prev_unseen": ~cu & pu, "both_unseen": cu & pu}

    def strata_counts(self) -> dict:
        """Per split: positions per stratum and their shares (the registered coverage strata)."""
        d = self.d
        out = {}
        for split in SPLITS:
            rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks[split])
            if rows.size == 0:
                out[split] = {"n": 0}
                continue
            m = self.strata_masks(rows, anchors)
            entry = {"n": int(rows.shape[0])}
            for s in STRATA:
                entry[s] = {"n": int(m[s].sum()), "share": float(m[s].mean())}
            for u, parts in UNIONS.items():
                entry[u] = {"n": int(sum(m[s].sum() for s in parts)), "share": float(sum(m[s].mean() for s in parts))}
            out[split] = entry
        return out

    # ----- fit ------------------------------------------------------------------------
    def fit(self) -> None:
        self.fit_tables()
        d = self.d
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks["train"])
        G = np.zeros((rb.D_X, rb.D_X)); C = np.zeros((rb.D_X, D))
        Gxp = np.zeros((rb.D_X, D_PT)); Gpp = np.zeros((D_PT, D_PT)); Cp = np.zeros((D_PT, D))
        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            X, Y = self.design(r, a, lopo=True)              # the twin's statement, the twin's chunks
            G += X.T @ X
            C += X.T @ Y
            P = self.pt_vec(r, a)
            Gxp += X.T @ P
            Gpp += P.T @ P
            Cp += P.T @ Y
        self.G, self.C = G, C                                 # the twin's Gram
        self.G_full = np.block([[G, Gxp], [Gxp.T, Gpp]])
        self.C_full = np.vstack([C, Cp])
        self.W = {}
        for arm in ARMS_TWIN:
            F = rb.arm_cols(arm)
            Gs, Cs = G[np.ix_(F, F)], C[F]
            lams = self.lambdas if self.twin is None else (self.lambda_selected[arm],)
            for lam in lams:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)

    def fit_pt(self, encoding: str) -> None:
        """The four PT arms at every lambda, for the given encoding of the previous token."""
        for arm in ARMS_PT:
            F = arm_cols(arm, encoding)
            Gs, Cs = self.G_full[np.ix_(F, F)], self.C_full[F]
            for lam in self.lambdas:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)

    # ----- evaluate -------------------------------------------------------------------
    def evaluate(self, split: str, encoding: str, arms=ARMS_REQUIRED, lambdas_of_arm: dict | None = None) -> dict:
        """out[(arm, B, lam, stratum)] = (hits (P, L), needed (P, L)) over the bigram
        positions of the split in that stratum; every lambda unless lambdas_of_arm."""
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks[split])
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
            X, Y = self.design_pt(r, a)
            yy = Y.reshape(r.shape[0], L, E)
            masks = {k: m for k, m in self.strata_masks(r, a).items() if m.any()}
            n_full = np.full((r.shape[0], L), K, np.int64)
            for arm in arms:
                Xa = X[:, arm_cols(arm, encoding)]
                lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                for lam in lams:
                    sc = (Xa @ self.W[(arm, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(sc, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        for stratum, m in masks.items():
                            acc((arm, B, lam, stratum), pr.per_prompt(h[m], pp[m], pids), pr.per_prompt(n_full[m], pp[m], pids))
        return out

    # ----- selection on val -----------------------------------------------------------
    @staticmethod
    def _pooled_all(val: dict, arm: str, lam: float) -> float:
        h = sum(val[(arm, LABEL_BUDGET, lam, s)][0].sum() for s in STRATA if (arm, LABEL_BUDGET, lam, s) in val)
        n = sum(val[(arm, LABEL_BUDGET, lam, s)][1].sum() for s in STRATA if (arm, LABEL_BUDGET, lam, s) in val)
        return float(h / n) if n > 0 else float("nan")

    def select(self, val: dict, arms) -> None:
        """Lambda per arm on the pooled val positions (the frozen rule: strict >, ties keep the
        smaller; grid-edge flagged). Without a twin the encoding is selected on the twin arms'
        val table by the twin's own rule; with a twin it is the twin's."""
        for arm in arms:
            best_lam, best, table = None, -np.inf, {}
            for lam in self.lambdas:
                v = self._pooled_all(val, arm, lam)
                table[str(lam)] = v
                if v > best:
                    best, best_lam = v, lam
            self.val_table[arm] = table
            self.lambda_selected[arm] = best_lam
            self.grid_edge[arm] = bool(best_lam in (self.lambdas[0], self.lambdas[-1]))
        if self.twin is None and set(ARMS_TWIN) <= set(arms):
            self.encoding_selected = rb.select_encoding(self.val_table, self.lambda_selected)

    def state_rows(self, test: dict) -> list[dict]:
        pids = self.prompt_ids["test"]
        rows = []
        for (arm, B, lam, stratum), (h, n) in test.items():
            if lam != self.lambda_selected[arm]:
                continue
            for pi, pid in enumerate(pids):
                for g in range(L):
                    if n[pi, g] == 0:
                        continue
                    rows.append({"arm": arm, "budget": B, "key": HORIZON, "depth": None, "gate": g,
                                 "prompt_idx": int(pid), "stratum": stratum, "hits": int(h[pi, g]), "needed": int(n[pi, g])})
        return sort_rows(rows)


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes it from the state file)
# ---------------------------------------------------------------------------

def _stratum_rank(stratum: str) -> int:
    if stratum not in STRATA:
        raise SystemExit(f"unknown stratum {stratum!r}")
    return STRATA.index(stratum)


def _sort_key(r: dict):
    return (r["arm"], int(r["budget"]), int(r["key"]), -1 if r["depth"] is None else int(r["depth"]),
            int(r["gate"]), int(r["prompt_idx"]), _stratum_rank(r["stratum"]))


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=_sort_key)


def _group(rows: list[dict]) -> dict:
    """{(arm, budget, scope): {gate: {prompt: (hits, needed)}}} for the six strata and the
    three unions (summed per (gate, prompt) across their strata)."""
    g: dict = {}
    for r in rows:
        _stratum_rank(r["stratum"])
        g.setdefault((r["arm"], int(r["budget"]), r["stratum"]), {}).setdefault(int(r["gate"]), {})[int(r["prompt_idx"])] = (int(r["hits"]), int(r["needed"]))
    for (arm, B, stratum) in list(g):
        for union, parts in UNIONS.items():
            if stratum not in parts:
                continue
            tgt = g.setdefault((arm, B, union), {})
            for gate, cell in g[(arm, B, stratum)].items():
                tc = tgt.setdefault(gate, {})
                for p, (h, n) in cell.items():
                    h0, n0 = tc.get(p, (0, 0))
                    tc[p] = (h0 + h, n0 + n)
    return g


def _twin_index(twin_rows: list[dict]) -> dict:
    """{(arm, budget, gate, prompt): (hits, needed)} of a twin state file."""
    idx = {}
    for r in twin_rows:
        idx[(r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]))] = (int(r["hits"]), int(r["needed"]))
    return idx


def reproduce_check(rows: list[dict], twin_rows: list[dict]) -> dict:
    """The REPRODUCE precondition: the stratified rows of the twin's arms, summed over the
    six strata, against the twin's state rows, hits AND needed, to the integer."""
    mine: dict = {}
    for r in rows:
        if r["arm"] not in ARMS_TWIN:
            continue
        k = (r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]))
        h0, n0 = mine.get(k, (0, 0))
        mine[k] = (h0 + int(r["hits"]), n0 + int(r["needed"]))
    twin = _twin_index(twin_rows)
    missing = sorted(k for k in twin if k not in mine)
    extra = sorted(k for k in mine if k not in twin)
    needed_mm, hits_mm, max_gap = 0, 0, 0
    for k, (h, n) in twin.items():
        if k not in mine:
            continue
        hm, nm = mine[k]
        if nm != n:
            needed_mm += 1
        elif hm != h:
            hits_mm += 1
            max_gap = max(max_gap, abs(hm - h))
    n_twin = len(twin)
    exact = not missing and not extra and needed_mm == 0 and hits_mm == 0
    near = (not exact and not missing and not extra and needed_mm == 0
            and hits_mm <= int(REPRODUCE_NEAR_SHARE * n_twin) and max_gap <= REPRODUCE_NEAR_HITS)
    status = "EXACT" if exact else "NEAR" if near else "INVALID"
    return {"n_twin_rows": n_twin, "n_compared": n_twin - len(missing), "missing_in_strat": len(missing),
            "extra_in_strat": len(extra), "needed_mismatch_rows": needed_mm, "hits_mismatch_rows": hits_mm,
            "max_abs_hits_gap": int(max_gap), "near_share_cap": REPRODUCE_NEAR_SHARE, "near_hits_cap": REPRODUCE_NEAR_HITS,
            "status": status, "ok": bool(status != "INVALID")}


_AT = f"at this reader (B = {LABEL_BUDGET}, j = {HORIZON})"
_NM = f"no material margin (at or above +{MATERIAL})"
_COV = "the positions whose token keys the train tables saw"
_FB = ("the positions with at least one unseen key (the current-token table blind in both arms, the free "
       "previous-token table blind, or both)")
_PT = "the forward's own output-distribution summaries (mass16, mass64, entropy) in both arms"
# Q1 sentences, (label, floor straddle on D_eq^COV) -> sentence; the straddle variant claims nothing beyond the rule
SENTENCES_Q1 = {
    ("COVERED-MATERIAL", False): (f"the coverage caveat on the free-bigram twin is retired at this encoding: the address "
                                  f"block's equal-dims margin over the free bigram block is material on {_COV}, as well as "
                                  f"pooled, {_AT}"),
    ("COVERED-MATERIAL", True): (f"the address block's equal-dims margin on {_COV} reads SIGNAL by the rule with a CI95 that "
                                 f"straddles the +{MATERIAL} floor: the coverage caveat is not retired at this power, {_AT}"),
    ("FALLBACK-LOCATED", False): (f"the material part of the surviving pooled margin is located on {_FB}: {_NM} of the address "
                                  f"block over an equal-dims free bigram block is shown on {_COV}, while a material margin is "
                                  f"shown on {_FB}, {_AT}"),
    ("FALLBACK-LOCATED", True): (f"the address block's equal-dims margin on {_COV} reads NOT-SHOWN by the rule with a CI95 that "
                                 f"straddles the +{MATERIAL} floor, while a material margin is shown on {_FB}: the location is "
                                 f"indicated, not settled, at this power, {_AT}"),
    ("UNLOCATED", False): (f"this split does not locate the surviving margin at this power: {_NM} of the address block over "
                           f"an equal-dims free bigram block is shown on {_COV} and none on {_FB}, {_AT}"),
    ("UNLOCATED", True): (f"this split does not locate the surviving margin at this power: the equal-dims margin on {_COV} "
                          f"straddles the +{MATERIAL} floor and {_NM} is shown on {_FB}, {_AT}"),
}
# Q2 sentences, (label, floor straddle on EITHER Q2 reading) -> sentence; a straddle on D_eq^PT or on D_add^PT
# selects the variant that claims nothing beyond the rule (the stage-2 strike under PT-ABSORBS needs the False variant)
_STR = f"at least one CI95 straddles the +{MATERIAL} floor"
SENTENCES_Q2 = {
    ("PT-SURVIVES", False): (f"with {_PT}, the address block adds a material margin over the equal-dims free block and the "
                             f"address stream adds a material margin over the free bigram plus the summaries: the twin's verdict "
                             f"stands at this encoding of p_t, {_AT}"),
    ("PT-SURVIVES", True): (f"with {_PT}, both Q2 readings are SIGNAL by the rule while {_STR}: the twin's verdict with p_t is "
                            f"not settled at this power, {_AT}"),
    ("PT-COMPLEMENTARY", False): (f"with {_PT}, {_NM} of the address block over the equal-dims free block is shown, while the "
                                  f"address stream adds a material margin over the free bigram plus the summaries, {_AT}"),
    ("PT-COMPLEMENTARY", True): (f"with {_PT}, the union reading is SIGNAL and the equal-dims reading is not, by the rule, while "
                                 f"{_STR}: the twin's verdict with p_t is not settled at this power, {_AT}"),
    ("PT-ABSORBS", False): (f"with {_PT}, {_NM} of the address block over the equal-dims free block is shown and none of the "
                            f"address stream over the free bigram plus the summaries, {_AT}"),
    ("PT-ABSORBS", True): (f"with {_PT}, neither Q2 reading is SIGNAL by the rule while {_STR}: not settled at this power, "
                           f"{_AT}"),
    ("PT-INCONSISTENT", False): (f"with {_PT}, the equal-dims comparison reads a material margin while the union reader does "
                                 f"not; no sentence on the twin's verdict is written, {_AT}"),
    ("PT-INCONSISTENT", True): (f"with {_PT}, the equal-dims comparison reads a material margin while the union reader does "
                                f"not, and {_STR}; no sentence on the twin's verdict is written, {_AT}"),
}
_FB_STRADDLE = f"; the unseen-key reading's CI95 straddles the +{MATERIAL} floor"
SENTENCE_VOID = {
    "REPRODUCE-INVALID": ("the stratified rows do not reproduce the committed twin's state rows (or the pooled D_eq is not the "
                          "twin's); the run is void and its deltas are numbers, not readings"),
    "INCOMPLETE": None,
}
DELTA_PAIRS = (("address_beyond_token", "history_tok", "free_tok"),
               ("gate_eq", "history_tok", "FREE"),
               ("address_beyond_bigram", "HIST", "FREE"),
               ("bigram_gain", "FREE", "free_tok"),
               ("pt_gain", "free_bigram_pt", "FREE"),
               ("d_pt", "history_tok", "free_bigram_pt"),
               ("d_eq_pt", "history_tok_pt", "free_bigram_pt"),
               ("d_add_pt", "history_bigram_pt", "free_bigram_pt"),
               ("pt_only-free_tok", "pt_only", "free_tok"),
               ("history_tok_pt-history_tok", "history_tok_pt", "history_tok"),
               ("history_bigram_pt-history_tok_pt", "history_bigram_pt", "history_tok_pt"))
LABEL_CELLS = (f"gate_eq|B={LABEL_BUDGET}|covered", f"gate_eq|B={LABEL_BUDGET}|fallback",
               f"d_eq_pt|B={LABEL_BUDGET}|all", f"d_add_pt|B={LABEL_BUDGET}|all")
READING_FIELDS = ("gate_eq_covered_reading", "gate_eq_fallback_reading", "d_eq_pt_all_reading", "d_add_pt_all_reading",
                  "d_pt_all_reading", "gate_eq_readings", "d_pt_readings", "d_eq_pt_readings",
                  "covered_negative", "pt_inconsistent_cause")       # a void payload carries numbers, nothing read from them


def _straddle(dl: dict) -> bool:
    return bool(dl["lo"] <= MATERIAL <= dl["hi"])


def conclude(rows: list[dict], encoding: str, twin_rows: list[dict] | None, twin_gate_eq: dict | None = None,
             n_boot: int = N_BOOT, seed: int = BOOT_SEED, budgets=BUDGETS) -> dict:
    if encoding not in rb.ENCODINGS:
        raise SystemExit(f"unknown encoding {encoding!r}")
    rows = sort_rows(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    groups = _group(rows)
    free, hist = rb.free_arm_of(encoding), rb.history_arm_of(encoding)
    names = {"FREE": free, "HIST": hist}
    tables: dict = {}
    for (arm, B, scope), gates in groups.items():
        entry = {"arm": arm, "budget": B, "scope": scope,
                 "dims": arm_dims(arm, encoding) if arm in ARMS_REQUIRED else None, "per_gate": {}}
        for g in sorted(gates):
            h, n = pr._arrays(gates[g], prompts)
            entry["per_gate"][str(g)] = pr._point_ci(h, n, n_boot, seed)
        H, N = pr._pooled(gates, prompts)
        entry["all"] = pr._point_ci(H, N, n_boot, seed)
        tables[f"{arm}|B={B}|{scope}"] = entry

    def pooled_of(arm, B, scope):
        gates = groups.get((names.get(arm, arm), B, scope))
        return None if gates is None else pr._pooled(gates, prompts)

    # pairing: every arm present shares history_tok's per-prompt trials in every scope at every budget
    for B in budgets:
        for scope in SCOPES:
            ref = pooled_of("history_tok", B, scope)
            if ref is None:
                continue
            for arm in ARMS_REQUIRED:
                pa = pooled_of(arm, B, scope)
                if pa is not None and not np.array_equal(pa[1], ref[1]):
                    raise SystemExit(f"pairing violated: {arm} and history_tok have different per-prompt trials at B={B} in {scope}")

    def delta_of(a, b, B, scope):
        pa, pb = pooled_of(a, B, scope), pooled_of(b, B, scope)
        if pa is None or pb is None:
            return None
        if not np.array_equal(pa[1], pb[1]):
            raise SystemExit(f"pairing violated: {a} and {b} have different per-prompt trials at B={B} in {scope}")
        return pr._delta(pa[0], pb[0], pa[1], n_boot, seed)

    deltas: dict = {}
    for B in budgets:
        for scope in SCOPES:
            for name, a, b in DELTA_PAIRS:
                dl = delta_of(a, b, B, scope)
                if dl is not None:
                    deltas[f"{name}|B={B}|{scope}"] = dl

    # scope positions and shares, from history_tok's trials at the label budget (every arm shares them)
    scopes: dict = {}
    ref_all = pooled_of("history_tok", LABEL_BUDGET, "all")
    for scope in SCOPES:
        pa = pooled_of("history_tok", LABEL_BUDGET, scope)
        if pa is None:
            scopes[scope] = {"positions": 0, "share": 0.0, "prompts_with_positions": 0}
            continue
        scopes[scope] = {"positions": int(round(float(pa[1].sum()) / (L * K))),
                         "share": float(pa[1].sum() / ref_all[1].sum()) if ref_all is not None and ref_all[1].sum() > 0 else None,
                         "prompts_with_positions": int((pa[1] > 0).sum())}

    present = {r["arm"] for r in rows}
    missing = [a for a in ARMS_REQUIRED if a not in present]
    missing_cells = [k for k in LABEL_CELLS if k not in deltas]
    labels: dict = {"encoding": encoding, "free_bigram_arm": free, "history_bigram_arm": hist,
                    "missing_arms": missing, "missing_label_cells": missing_cells, "scopes": scopes}
    rep = None if twin_rows is None else reproduce_check(rows, twin_rows)
    labels["reproduce"] = rep
    # the identity check: the ALL scope repeats the twin's D_eq (same rows, same seed) when the twin reproduced
    ide = deltas.get(f"gate_eq|B={LABEL_BUDGET}|all")
    if twin_gate_eq is not None and ide is not None:
        labels["all_gate_eq_matches_twin"] = bool(all(abs(float(ide[k]) - float(twin_gate_eq[k])) <= 1e-12 for k in ("delta", "lo", "hi")))
    else:
        labels["all_gate_eq_matches_twin"] = None
    if rep is None:
        labels["reproduce_status"], labels["reproduce_ok"] = None, None
    else:
        status = rep["status"]
        if status != "INVALID" and labels["all_gate_eq_matches_twin"] is False:
            status = "INVALID"                                 # EXACT or NEAR rows whose pooled D_eq is not the twin's: void
        labels["reproduce_status"], labels["reproduce_ok"] = status, bool(status != "INVALID")
    if missing or missing_cells:
        labels.update({"label": "INCOMPLETE", "void": True, "q1": None, "q2": None, "sentence": None})
        return {"tables": tables, "deltas": deltas, "labels": labels}
    cov, fb, eqpt, addpt = (deltas[k] for k in LABEL_CELLS)
    dpt = deltas.get(f"d_pt|B={LABEL_BUDGET}|all")
    anchor = deltas.get(f"history_bigram_pt-history_tok_pt|B={LABEL_BUDGET}|all")
    labels.update({"gate_eq_covered": cov, "gate_eq_fallback": fb, "d_eq_pt_all": eqpt, "d_add_pt_all": addpt,
                   "d_pt_all": dpt, "pt_dilution_anchor": anchor})
    labels["gate_eq_covered_reading"] = pr._reading(cov)
    labels["gate_eq_fallback_reading"] = pr._reading(fb)
    labels["d_eq_pt_all_reading"] = pr._reading(eqpt)
    labels["d_add_pt_all_reading"] = pr._reading(addpt)
    labels["d_pt_all_reading"] = None if dpt is None else pr._reading(dpt)
    for name, field in (("gate_eq", "gate_eq_readings"), ("d_pt", "d_pt_readings"), ("d_eq_pt", "d_eq_pt_readings")):
        labels[field] = {s: pr._reading(deltas[f"{name}|B={LABEL_BUDGET}|{s}"])
                         for s in SCOPES if f"{name}|B={LABEL_BUDGET}|{s}" in deltas}
    labels["covered_floor_straddle"] = _straddle(cov)
    labels["fallback_floor_straddle"] = _straddle(fb)
    labels["d_eq_pt_floor_straddle"] = _straddle(eqpt)
    labels["d_add_pt_floor_straddle"] = _straddle(addpt)
    labels["q2_floor_straddle"] = bool(labels["d_eq_pt_floor_straddle"] or labels["d_add_pt_floor_straddle"])
    labels["d_pt_floor_straddle"] = None if dpt is None else _straddle(dpt)
    labels["covered_negative"] = bool(labels["gate_eq_covered_reading"] == "NEGATIVE")
    c_sig, f_sig = labels["gate_eq_covered_reading"] == "SIGNAL", labels["gate_eq_fallback_reading"] == "SIGNAL"
    q1 = "COVERED-MATERIAL" if c_sig else "FALLBACK-LOCATED" if f_sig else "UNLOCATED"
    e_sig, a_sig = labels["d_eq_pt_all_reading"] == "SIGNAL", labels["d_add_pt_all_reading"] == "SIGNAL"
    q2 = ("PT-SURVIVES" if (e_sig and a_sig) else "PT-COMPLEMENTARY" if (not e_sig and a_sig)
          else "PT-ABSORBS" if (not e_sig and not a_sig) else "PT-INCONSISTENT")
    labels["pt_inconsistent_cause"] = (None if q2 != "PT-INCONSISTENT"
                                       else "reader" if (anchor is not None and anchor["hi"] < 0) else "floor straddle")
    labels["q1"], labels["q2"] = q1, q2
    if labels["reproduce_ok"] is False:
        labels["label"] = "REPRODUCE-INVALID"
        labels["void"] = True
        labels["sentence"] = SENTENCE_VOID["REPRODUCE-INVALID"]
        labels["q1"], labels["q2"] = None, None                 # a void payload carries numbers, not readings
        for f in READING_FIELDS:
            labels[f] = None
    else:
        labels["label"] = f"{q1} / {q2}"
        labels["void"] = False
        s1 = SENTENCES_Q1[(q1, labels["covered_floor_straddle"])]
        if labels["covered_negative"]:
            s1 = (f"the address block reads below the equal-dims free bigram block on {_COV} (NEGATIVE); " + s1)
        if labels["fallback_floor_straddle"]:
            s1 = s1 + _FB_STRADDLE
        s2 = SENTENCES_Q2[(q2, labels["q2_floor_straddle"])]
        labels["sentence"] = s1 + "; " + s2
    labels["rule"] = (f"readings SIGNAL iff CI95 lower > 0 and delta >= +{MATERIAL}, NEGATIVE iff CI95 upper < 0, else "
                      f"NOT-SHOWN, at B={LABEL_BUDGET}, j={HORIZON}, on the twin's bigram positions split by train-table "
                      f"coverage (six strata; covered = the three covered strata, fallback = the three unseen strata); "
                      f"PRECONDITION REPRODUCE: the stratified rows summed over the strata equal the committed twin's state rows "
                      f"(hits-only mismatches on at most {REPRODUCE_NEAR_SHARE:.1%} of its rows within +-{REPRODUCE_NEAR_HITS} "
                      f"hit are NEAR; more, any needed mismatch, or a pooled D_eq that is not the twin's is INVALID = void, "
                      f"numbers only); Q1 COVERED-MATERIAL iff D_eq on covered SIGNAL, FALLBACK-LOCATED iff not and D_eq on "
                      f"fallback SIGNAL, else UNLOCATED; Q2 on all positions with the p_t block in both arms: PT-SURVIVES iff "
                      f"history_tok_pt - free_bigram_pt and history_bigram_pt - free_bigram_pt both SIGNAL, PT-COMPLEMENTARY "
                      f"iff only the union, PT-ABSORBS iff neither, PT-INCONSISTENT iff only the equal-dims; a CI95 containing "
                      f"+{MATERIAL} is a floor straddle, flagged, and the pinned sentence then claims nothing beyond the rule; "
                      f"the primary harvest's label is the label; NON-CRITERION, one pinned consequence (a dated STATUS line "
                      f"under F-26)")
    return {"tables": tables, "deltas": deltas, "labels": labels}


# ---------------------------------------------------------------------------
# Provenance, I/O, CLI
# ---------------------------------------------------------------------------

def _write_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _rel(path: Path) -> str:
    rp = Path(path).resolve()
    return rp.relative_to(ROOT.resolve()).as_posix() if rp.is_relative_to(ROOT.resolve()) else rp.as_posix()


def read_twin(path: Path) -> dict:
    """The committed twin payload and its state file: the encoding and lambdas this read takes
    verbatim, the committed D_eq (the identity check) and the rows REPRODUCE is checked against."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("registered") != rb.REGISTERED:
        raise SystemExit(f"{path} is not a free-bigram twin payload")
    prov = payload["provenance"]
    if prov.get("instrument_sha256") != TWIN_INSTRUMENT_SHA256:
        raise SystemExit(f"{path} was not written by the frozen twin ({str(prov.get('instrument_sha256'))[:12]})")
    state_path = Path(str(path) + ".state.jsonl")
    if not state_path.exists():
        raise SystemExit(f"twin state file {state_path} not found")
    header, rows = pr.load_state(state_path)
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit(f"{state_path}: row count differs from the twin payload's")
    return {"path": _rel(path), "sha256": pr._sha(path), "state_path": _rel(state_path), "state_sha256": pr._sha(state_path),
            "git_commit": prov["git_commit"], "instrument_sha256": prov["instrument_sha256"],
            "encoding": prov["encoding_selected"], "lambda_selected": {k: float(v) for k, v in prov["lambda_selected"].items()},
            "n_state_rows": int(payload["n_state_rows"]), "harvest_npz_sha256": prov["harvest_npz_sha256"],
            "gate_eq": payload["conclusion"]["deltas"][f"gate_eq|B={LABEL_BUDGET}"], "_rows": rows}


def twin_reference(harvest_dir: Path, twin_arg: str | None, smoke: bool, out_under_results: bool) -> dict | None:
    """The committed twin payload for this harvest, or None for a smoke / an explicit 'none' outside
    results/. A smoke never reads it (its re-split rows are not the twin's rows)."""
    if smoke:
        return None
    if twin_arg is not None and twin_arg.lower() == "none":
        if out_under_results:
            raise SystemExit("a registered run must read the committed twin payload (--twin none is refused under results/)")
        return None
    explicit = twin_arg is not None
    want = TWIN_OF_HARVEST.get(Path(harvest_dir).name)
    if not explicit:
        if want is None:
            if not out_under_results:
                return None
            raise SystemExit(f"no committed twin payload is known for harvest {Path(harvest_dir).name}; pass --twin")
        path = ROOT / "results" / "real" / want
    else:
        path = Path(twin_arg)
        if out_under_results and path.resolve() != (ROOT / "results" / "real" / (want or "")).resolve():
            raise SystemExit("under results/ the twin payload must be the registered one for this harvest")
    if not path.exists():
        if not explicit and not out_under_results:
            return None
        raise SystemExit(f"twin payload {path} not found")
    return read_twin(path)


def _twin_header(twin: dict | None) -> dict | None:
    return None if twin is None else {k: v for k, v in twin.items() if k != "_rows"}


def run(args) -> dict:
    started = time.time()
    twin_sha = assert_frozen_twin()
    parent_sha = rb.assert_frozen_instrument()
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
    twin = twin_reference(Path(args.harvest), args.twin, smoke, under)
    data = pr.S3Data(args.harvest, only_seeds=only, smoke_split_val=args.smoke_split_val)
    if twin is not None and twin["harvest_npz_sha256"] != data.npz_shas:
        raise SystemExit("the twin payload was read on different harvest shards than this run opens")
    label_of_token, n_classes = load_label_space(args.buckets, args.glue)
    st = Strat(data, label_of_token, n_classes, twin=twin, lambdas=lambdas)
    st.fit()
    if twin is None:
        # the twin's own rule, re-run: lambdas and the encoding selected on the pooled val positions
        val_twin = st.evaluate("val", rb.ENCODINGS[0], arms=ARMS_TWIN)
        st.select(val_twin, ARMS_TWIN)
    encoding = st.encoding_selected
    st.fit_pt(encoding)
    val_pt = st.evaluate("val", encoding, arms=ARMS_PT)
    st.select(val_pt, ARMS_PT)
    test = st.evaluate("test", encoding, arms=ARMS_REQUIRED, lambdas_of_arm=st.lambda_selected)
    rows = st.state_rows(test)
    conclusion = conclude(rows, encoding, None if twin is None else twin["_rows"], None if twin is None else twin["gate_eq"])
    git_commit, tracked = pr._git()
    prov = {
        "registered": REGISTERED,
        "git_commit": git_commit,
        "git_status_tracked": tracked,
        "instrument_sha256": pr._sha(Path(__file__)),
        "frozen_twin": {"path": "tools/run_prefetch_bigram.py", "sha256_lf": twin_sha},
        "frozen_instrument": {"path": "tools/run_prefetch_readouts.py", "sha256_lf": parent_sha},
        "harvest_dir": str(args.harvest),
        "harvest_npz_sha256": data.npz_shas,
        "seeds": data.seeds,
        "smoke": smoke,
        "smoke_split_val": bool(args.smoke_split_val),
        "twin": _twin_header(twin),
        "label_space": {"buckets": str(args.buckets), "buckets_sha256": pr._sha(args.buckets),
                        "glue": str(args.glue), "glue_sha256": pr._sha(args.glue), "n_classes": int(n_classes),
                        "n_tokens": int(label_of_token.shape[0])},
        "constants": {"budgets": list(BUDGETS), "horizon": HORIZON, "lambdas": list(lambdas), "label_budget": LABEL_BUDGET,
                      "material": MATERIAL, "n_boot": N_BOOT, "boot_seed": BOOT_SEED, "chunk": CHUNK,
                      "strata": list(STRATA), "unions": {k: list(v) for k, v in UNIONS.items()}, "d_pt": D_PT,
                      "counts_per_occurrence": COUNTS_PER_OCCURRENCE,
                      "entropy_scale_ln_v": st.ent_scale, "reproduce_near_share": REPRODUCE_NEAR_SHARE,
                      "reproduce_near_hits": REPRODUCE_NEAR_HITS,
                      "arm_dims": {a: arm_dims(a, encoding) for a in ARMS_REQUIRED}},
        "n_positions": st.n_positions,
        "n_test_prompts": int(st.prompt_ids["test"].shape[0]),
        "strata_counts": st.strata_counts(),
        "table_coverage": st.table_coverage(),
        "encoding_selected": encoding,
        "encoding_source": "twin" if twin is not None else "val",
        "lambda_selected": {k: float(v) for k, v in st.lambda_selected.items()},
        "lambda_source": st.lambda_source,
        "lambda_grid_edge": st.grid_edge,
        "val_table": st.val_table,
        "blas": blas_info(),
        "args": redact_args(vars(args)),
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "started_unix": started,
        "runtime_s": time.time() - started,
    }
    payload = {"registered": REGISTERED, "provenance": prov, "conclusion": conclusion, "n_state_rows": len(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    header = {"state_header": True, "registered": REGISTERED, "harvest_npz_sha256": data.npz_shas, "smoke": smoke,
              "encoding": encoding, "lambda_selected": prov["lambda_selected"], "twin": _twin_header(twin)}
    _write_lf(state_path, "".join(json.dumps(x) + "\n" for x in [header] + rows))
    _write_lf(out, json.dumps(payload, indent=1))
    _write_lf(meta_path, json.dumps(prov, indent=1))
    print_summary(payload)
    return payload


def conclude_from(payload_path: Path) -> dict:
    assert_frozen_twin()
    rb.assert_frozen_instrument()
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if payload.get("registered") != REGISTERED:
        raise SystemExit("payload is not a stratified coverage read payload")
    header, rows = pr.load_state(Path(str(payload_path) + ".state.jsonl"))
    prov = payload["provenance"]
    if header["harvest_npz_sha256"] != prov["harvest_npz_sha256"]:
        raise SystemExit("state header harvest shas differ from the payload's")
    if header.get("encoding") != prov["encoding_selected"]:
        raise SystemExit("state header encoding differs from the payload's")
    if header.get("lambda_selected") != prov["lambda_selected"]:
        raise SystemExit("state header lambdas differ from the payload's")
    if header.get("twin") != prov["twin"]:
        raise SystemExit("state header twin reference differs from the payload's")
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit("state row count differs from the payload's")
    # the PT arms' lambdas are RE-DERIVED from the payload's own val table, never trusted from the header
    for arm in ARMS_PT:
        table = prov["val_table"][arm]
        best_lam, best = None, -np.inf
        for lam in prov["constants"]["lambdas"]:
            v = table[str(float(lam))]
            if v > best:
                best, best_lam = v, float(lam)
        if best_lam != float(prov["lambda_selected"][arm]):
            raise SystemExit(f"the payload's lambda for {arm} is not the one its val table selects")
    twin_rows, twin_gate_eq = None, None
    tw = header.get("twin")
    if tw is not None:
        # the twin's encoding and lambdas, taken verbatim, must be the ones this payload used
        if tw["encoding"] != header["encoding"]:
            raise SystemExit("the state header's encoding is not the twin's")
        for arm in ARMS_TWIN:
            if float(tw["lambda_selected"][arm]) != float(header["lambda_selected"][arm]):
                raise SystemExit(f"the state header's lambda for {arm} is not the twin's")
        tpath = ROOT / tw["path"] if not Path(tw["path"]).is_absolute() else Path(tw["path"])
        if not tpath.exists():
            raise SystemExit(f"the committed twin payload {tw['path']} is not present; REPRODUCE cannot be recomputed")
        fresh = read_twin(tpath)
        if fresh["sha256"] != tw["sha256"] or fresh["state_sha256"] != tw["state_sha256"]:
            raise SystemExit(f"the committed twin payload {tw['path']} is not the one this run read "
                             f"(sha {tw['sha256'][:12]} -> {fresh['sha256'][:12]}; state {tw['state_sha256'][:12]} -> "
                             f"{fresh['state_sha256'][:12]})")
        if _twin_header(fresh) != tw:
            raise SystemExit(f"the committed twin payload {tw['path']} differs from the header's record of it beyond the shas")
        twin_rows, twin_gate_eq = fresh["_rows"], fresh["gate_eq"]
    got = conclude(rows, header["encoding"], twin_rows, twin_gate_eq)
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
    print(f"LABEL: {lab.get('label')}   (smoke={prov.get('smoke')}; encoding={lab.get('encoding')} from {prov.get('encoding_source')}; void={lab.get('void')})")
    rep = lab.get("reproduce")
    if rep is None:
        print("  REPRODUCE: not applicable (no twin payload read)")
    else:
        print(f"  REPRODUCE: {lab.get('reproduce_status')} (rows {rep['status']})  twin rows {rep['n_twin_rows']}  compared {rep['n_compared']}  "
              f"missing {rep['missing_in_strat']}  extra {rep['extra_in_strat']}  needed mismatches {rep['needed_mismatch_rows']}  "
              f"hits mismatches {rep['hits_mismatch_rows']}  max |gap| {rep['max_abs_hits_gap']}  "
              f"identity (all D_eq = twin's): {lab.get('all_gate_eq_matches_twin')}")
    if lab.get("label") == "INCOMPLETE":
        print("missing arms:", lab["missing_arms"], "missing label cells:", lab["missing_label_cells"]); return
    for scope in SCOPES:
        s = lab["scopes"].get(scope, {})
        share = s.get("share")
        print(f"  scope {scope:12s} positions {s.get('positions', 0):7d}  share {share if share is None else format(share, '.4f')}  "
              f"prompts {s.get('prompts_with_positions', 0)}")
    rd = lab.get("gate_eq_readings") or {}
    print(f"  Q1 {lab.get('q1')}: D_eq covered {str(rd.get('covered')):10s} {_fmt(lab['gate_eq_covered'])}  "
          f"straddle={lab['covered_floor_straddle']}  negative={lab['covered_negative']}")
    print(f"     D_eq fallback {str(rd.get('fallback')):10s} {_fmt(lab['gate_eq_fallback'])}  straddle={lab['fallback_floor_straddle']}")
    print(f"  Q2 {lab.get('q2')}: D_eq^PT all {str(lab.get('d_eq_pt_all_reading')):10s} {_fmt(lab['d_eq_pt_all'])}  straddle={lab['d_eq_pt_floor_straddle']}")
    print(f"     D_add^PT all {str(lab.get('d_add_pt_all_reading')):10s} {_fmt(lab['d_add_pt_all'])}  straddle={lab['d_add_pt_floor_straddle']}  "
          f"(Q2 straddle={lab['q2_floor_straddle']})  anchor hb_pt-ht_pt {_fmt(lab['pt_dilution_anchor'])}  "
          f"inconsistent cause={lab['pt_inconsistent_cause']}")
    print(f"     D_pt all (asymmetric, reported) {str(lab.get('d_pt_all_reading')):10s} {_fmt(lab['d_pt_all'])}")
    print(f"  sentence: {lab['sentence']}")
    for B in BUDGETS:
        for scope in SCOPES:
            parts = []
            for name, _, _ in DELTA_PAIRS:
                d = c["deltas"].get(f"{name}|B={B}|{scope}")
                if d:
                    parts.append(f"{name} {_fmt(d)}")
            if parts:
                print(f"  B={B:2d} {scope:12s} " + " | ".join(parts[:6]))
                if len(parts) > 6:
                    print(f"  {'':17s}" + " | ".join(parts[6:]))
    for B in BUDGETS:
        for arm in ARMS_REQUIRED:
            t = c["tables"].get(f"{arm}|B={B}|all")
            if t:
                a = t["all"]; print(f"  B={B:2d} {arm:18s} all {a['point']:.4f} [{a['ci_lo']:.4f}, {a['ci_hi']:.4f}]")
    print("  lambda:", prov.get("lambda_selected"))
    print("  lambda source:", prov.get("lambda_source"))
    print("  grid-edge:", prov.get("lambda_grid_edge"))
    print("  strata (test):", prov.get("strata_counts", {}).get("test"))
    print("  blas:", prov.get("blas"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default=str(ROOT / "results" / "real" / "harvest_moe"))
    ap.add_argument("--out", default=str(ROOT / "results" / "real" / "prefetch_strat_s3.json"))
    ap.add_argument("--buckets", default=str(pr.BUCKETS16))
    ap.add_argument("--glue", default=str(pr.GLUE16))
    ap.add_argument("--twin", default=None,
                    help="the committed free-bigram twin payload whose encoding, lambdas and state rows this read takes "
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

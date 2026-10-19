#!/usr/bin/env python3
"""OQ-17 FULL-FREE existence re-test (registered 2026-09-06 in
docs/BLUEPRINT.md "OQ-17 FULL-FREE EXISTENCE RE-TEST REGISTRATION", BEFORE
any registered cell ran; critic round applied before the freeze commit;
CRITERION-BEARING for the K-2 existence findings F-15 / F-17 through that
block's pinned consequence rules — NOT a P1-style diagnostic).

QUESTION. F-15/F-17 measured the telemetry margin against (a) = 657 logged
summaries of p_a. Two later results say that baseline was never pushed to
its ceiling: F-22 DR-2 (a hashed encoding of p_a's top-32 token ids
reconstructs h_a at least as well as telemetry) and F-23 (h_a, the
harvest's `hidden` array — the final-norm state that produced p_a — is an
exact linear function of the FULL p_a, i.e. free under D-5). The registered
linear (h) arm is not a usable reader of that free information: it sits at
or below the majority floor on 6 of the 8 harvest x offset-2/3 cells (a
linear model contains the constant predictor, so sitting below it is a
trainer failure on raw h_a, not a representational limit). This tool runs the FULL
free baseline — (a) ++ TOK ++ z-scored h_a — through the registered
trainer at both registered capacities, with and without the telemetry
block, against the equal-dims alignment-destroyed telemetry twin.

ARMS (feature labels in cell ids; block order identical across arms so the
seeded init tensor lands on the same feature positions):
  fplus   = (a) 657 ++ TOK ++ hz     TOK = multi-hot of the anchor's top-32
            next-token ids hashed id mod 2048 (the DR-2 rule,
            sideband.recon.FREETOK_BINS); hz = h_a clipped to the TRAIN
            support and z-scored per channel with TRAIN-split moments
            (4096 dims on S1, 2048 on S3)
  fplus_b = fplus ++ (b) aligned telemetry multi-hot (2048 on S1, 1024 on S3)
  fplus_n = fplus ++ ALIGNMENT-DESTROYED telemetry: the slot vector of anchor
            (a + 17) mod row-length (run_posthoc_topic.SLOT_SHIFT — R2's
            shift trick on features). Equal dims to fplus_b by
            construction (refused otherwise).
CELLS per harvest: L1 x off2 x {linear, mlp256} x train seeds {0,1,2} x 3
arms = 18; S1 adds L1 x off3 x mlp256 x 3 seeds x 3 arms = 9 (the F-15
horizon; offsets are bound to the source: "2,3" for --space-tag concept,
"2" otherwise); plus the LEAK RIDER: shuffled fplus and shuffled fplus_b at
L1/off2/linear/seed 0, run FIRST, two legs, either halts the grid:
  leg 1  shuffled fplus   <= the COMMITTED Phase-3 shuffled (a) cell + 0.01
         (a leak in the blocks shared by all arms — TOK, hz — shows here)
  leg 2  shuffled fplus_b <= shuffled fplus + 0.01 (a leak in the slots block)
Same trainer, budget, estimand and bootstrap as Phase 3 (seed-summed
per-prompt successes, paired_cluster_delta_ci, n_boot 2000, seed 0).

READOUTS (pinned):
  D  = acc(fplus_b) - acc(fplus_n)   equal dims — THE gate readout
  Mt = acc(fplus_b) - acc(fplus)     dims-asymmetric; quoted beside D
  Mn = acc(fplus_n) - acc(fplus)     pure dilution; descriptive
  Mf = acc(fplus)   - acc(a)         vs the COMMITTED Phase-3 (a) cells
  Mc = acc(fplus)   - acc(c)         vs the committed telemetry arm
READER VALIDITY (precondition, per harvest, at the gate cell L1/off2/
mlp256): every one of the 9 unshuffled probes has test_acc >=
majority_rate_test - 0.001 AND the Mf row at the gate cell has CI95 upper
>= 0; otherwise the harvest is READER-INVALID and no label may issue.
GATE CELL per harvest: L1 / off2 / mlp256, D fires iff CI95 lower > 0, all
three seeds positive, point >= +0.005 (the Phase-3 triple rule; the row
must carry n_seeds 3, n_clusters 30 and the fplus_b-fplus_n pairing).
LABELS per source, from BOTH harvests (--conclude-from PRIMARY REPLICATION):
  READER-INVALID      either harvest fails the precondition
  SURVIVES-FULL-FREE  the gate fires on both harvests (the licensed
                      sentence depends on Mt: see the registration)
  SPLIT               one fires, one does not (OPEN at the full-free level)
  ABSORBED            neither fires AND every D row's CI95 upper < +0.005
                      on both harvests (the strong null)
  NOT-SHOWN           neither fires, but some D row's CI95 upper >= +0.005
  INCOMPLETE          a gate row is missing
S1 offset-3 rows carry the HORIZON note (OFF3-SURVIVES / OFF3-ABSORBED only
when both off3 CI95 uppers are < +0.005 / OFF3-NOT-SHOWN / OFF3-SPLIT /
OFF3-INCOMPLETE); linear rows are reported. ABSORBED and SURVIVES are both
scoped to the registered reader at the registered budget (the payload
reports best_epoch per cell; the smoke selected epoch 0 on every fplus cell).

Run (GPU box):
    python tools/run_fullfree.py --out results/real/fullfree_s1.json
    python tools/run_fullfree.py --harvest results/real/harvest_shadow_r \
        --fidelity results/real/harvest_fidelity_rider_r.json \
        --phase3-state results/real/probes_s1_replication.json.state.jsonl \
        --phase3-payload results/real/probes_s1_replication.json \
        --out results/real/fullfree_s1_r.json
    (S3: --space-tag olmoe --n-slots 64 --parent-finding F-17 and the olmoe
     buckets/glue/groups/rider/phase-3 paths from the S3 Phase-3 payload.)
    python tools/run_fullfree.py --conclude-from results/real/fullfree_s1.json \
        results/real/fullfree_s1_r.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.provenance import redact_args  # noqa: E402
from sideband.recon import FREETOK_BINS  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import HarvestData  # noqa: E402
from run_posthoc_topic import SLOT_SHIFT, load_phase3_cells  # noqa: E402
from run_probes import (REAL, MATERIALITY, AnchorBlock,  # noqa: E402
                        SlotsAnchorBlock, bind_spaces_to_harvest,
                        build_spaces, cell_id, feature_blocks, margins,
                        parse_state, run_cell, space_names, state_header)

SEEDS = (0, 1, 2)
ARMS = ("fplus", "fplus_b", "fplus_n")
GATE_OFFSET = 2
GATE_CAPACITY = "mlp256"
R2_BAND = 0.01
READER_FLOOR_TOL = 0.001
SD_FLOOR = 1e-6
GATE_PAIR = "fplus_b-fplus_n"
LABEL_SURVIVES = "SURVIVES-FULL-FREE"
LABEL_ABSORBED = "ABSORBED"
LABEL_NOT_SHOWN = "NOT-SHOWN"
LABEL_SPLIT = "SPLIT"
LABEL_INCOMPLETE = "INCOMPLETE"
LABEL_READER_INVALID = "READER-INVALID"
REGISTERED_OUTS = ("fullfree_s1.json", "fullfree_s1_r.json",
                   "fullfree_s3.json", "fullfree_s3_r.json")
# Registered offsets and harvest pairs, bound to the source tag / space.
OFFSETS_OF_TAG = {"concept": (2, 3), "olmoe": (2,)}
HARVESTS_OF_SPACE = {"L1_concept_k16": ("results/real/harvest_shadow",
                                        "results/real/harvest_shadow_r"),
                     "L1_olmoe_k16": ("results/real/harvest_moe",
                                      "results/real/harvest_moe_r")}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Feature blocks
# ---------------------------------------------------------------------------

def tok_multi_hot(ids: np.ndarray, n_bins: int = FREETOK_BINS) -> np.ndarray:
    """(B, top_n) token ids -> (B, n_bins) float32 multi-hot of id mod
    n_bins; negative (padding) ids ignored. The per-anchor form of
    sideband.recon.tok_block (asserted equal by tests)."""
    ids = np.asarray(ids, dtype=np.int64)
    B = ids.shape[0]
    out = np.zeros((B, n_bins), dtype=np.float32)
    keep = (ids >= 0).ravel()
    rows = np.repeat(np.arange(B), ids.shape[1])[keep]
    out[rows, ids.ravel()[keep] % n_bins] = 1.0
    return out


class TokAnchorBlock:
    """Per-batch multi-hot of the anchor's top-32 next-token ids — the
    same (row, anchor) coordinates the registered (a) blocks read."""

    def __init__(self, top_ids: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 n_bins: int = FREETOK_BINS):
        self.top_ids, self.rows, self.anchors, self.n_bins = top_ids, rows, anchors, int(n_bins)

    @property
    def dim(self) -> int:
        return self.n_bins

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return tok_multi_hot(self.top_ids[self.rows[idx], self.anchors[idx]], self.n_bins)


def train_moments(hidden: np.ndarray, lengths: np.ndarray, split_names: np.ndarray,
                  sd_floor: float = SD_FLOOR) -> dict:
    """Per-channel TRAIN-split moments of the hidden array over every valid
    position of every train row (float64 accumulation): lo/hi = train
    support (the clip), mu/sd = the z-score. VAL/TEST rows never
    contribute. Returns float32 arrays + a sha256 over them."""
    d = int(hidden.shape[2])
    s = np.zeros(d, np.float64)
    ss = np.zeros(d, np.float64)
    lo = np.full(d, np.inf, np.float64)
    hi = np.full(d, -np.inf, np.float64)
    n = 0
    n_rows = 0
    for r in np.nonzero(split_names == "train")[0]:
        L = int(lengths[r])
        if L <= 0:
            continue
        x = hidden[r, :L].astype(np.float64)
        s += x.sum(0)
        ss += (x * x).sum(0)
        lo = np.minimum(lo, x.min(0))
        hi = np.maximum(hi, x.max(0))
        n += L
        n_rows += 1
    if n == 0:
        raise SystemExit("no train-split positions for the hidden moments")
    mu = s / n
    var = np.maximum(ss / n - mu * mu, 0.0)
    sd = np.maximum(np.sqrt(var), sd_floor)
    arrs = {k: v.astype(np.float32) for k, v in
            (("mu", mu), ("sd", sd), ("lo", lo), ("hi", hi))}
    sha = hashlib.sha256(np.concatenate([arrs[k] for k in ("mu", "sd", "lo", "hi")]).tobytes()).hexdigest()
    return {**arrs, "sha256": sha, "n_train_rows": int(n_rows),
            "n_train_positions": int(n), "sd_floor": float(sd_floor)}


class HiddenZBlock:
    """h_a per batch: clip to the TRAIN support, then per-channel z-score
    with TRAIN moments — the F-22 DR-1 support-clip lesson applied to the
    one raw-valued block. Same (row, anchor) coordinates as AnchorBlock."""

    def __init__(self, hidden: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 moments: dict):
        self.inner = AnchorBlock(hidden, rows, anchors)
        self.mu, self.sd = moments["mu"], moments["sd"]
        self.lo, self.hi = moments["lo"], moments["hi"]

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        x = self.inner.batch(idx)
        return ((np.clip(x, self.lo, self.hi) - self.mu) / self.sd).astype(np.float32, copy=False)


def make_factories(top_ids: np.ndarray, hidden: np.ndarray, slots: np.ndarray,
                   lengths: np.ndarray, n_slots: int, moments: dict,
                   n_bins: int = FREETOK_BINS) -> dict:
    """The three arms' EXTRA blocks (appended after the registered (a)
    blocks by run_cell): order TOK, hz, then the slots block last — the
    same order in fplus_b and fplus_n."""

    def free_extras(rows, anchors):
        return [TokAnchorBlock(top_ids, rows, anchors, n_bins),
                HiddenZBlock(hidden, rows, anchors, moments)]

    def fplus(rows, anchors):
        return free_extras(rows, anchors)

    def fplus_b(rows, anchors):
        return free_extras(rows, anchors) + [SlotsAnchorBlock(slots, rows, anchors, n_slots)]

    def fplus_n(rows, anchors):
        shifted = (anchors + SLOT_SHIFT) % lengths[rows]
        return free_extras(rows, anchors) + [SlotsAnchorBlock(slots, rows, shifted, n_slots)]

    return {"fplus": fplus, "fplus_b": fplus_b, "fplus_n": fplus_n}


# ---------------------------------------------------------------------------
# Grid, rider, precondition, labels
# ---------------------------------------------------------------------------

def offsets_for_tag(tag: str) -> tuple[int, ...]:
    if tag not in OFFSETS_OF_TAG:
        raise SystemExit(f"unregistered --space-tag {tag!r}: offsets are bound to the source")
    return OFFSETS_OF_TAG[tag]


def build_grid(space: str, offsets: tuple[int, ...]) -> list[tuple]:
    """(space, offset, arm, capacity, seed, shuffled). The leak rider's
    shuffled pair runs first; offset 2 at both capacities; any further
    offset at mlp256 only (the registered economy for this test)."""
    if not offsets or any(o < 2 for o in offsets):
        raise SystemExit("offsets must be >= 2 (K-2 reads offsets >= 2)")
    grid = [(space, GATE_OFFSET, "fplus", "linear", 0, True),
            (space, GATE_OFFSET, "fplus_b", "linear", 0, True)]
    for off in offsets:
        caps = ("linear", "mlp256") if off == GATE_OFFSET else ("mlp256",)
        for seed in SEEDS:
            for cap in caps:
                for arm in ARMS:
                    grid.append((space, off, arm, cap, seed, False))
    return grid


def committed_shuffled_a(p3_cells: list[dict], space: str) -> dict | None:
    cid = cell_id(space, GATE_OFFSET, "a", "linear", 0, shuffled=True)
    return next((c for c in p3_cells if c.get("cell") == cid), None)


def rider_check(cells: list[dict], p3_cells: list[dict], space: str,
                band: float = R2_BAND) -> dict:
    """Two-leg leak rider on the shuffled cells present so far; raises
    SystemExit on a failed leg (fresh or resumed cells alike). Returns the
    legs evaluated so far."""
    sf = next((c for c in cells if c["shuffled"] and c["features"] == "fplus"), None)
    sb = next((c for c in cells if c["shuffled"] and c["features"] == "fplus_b"), None)
    ca = committed_shuffled_a(p3_cells, space)
    if ca is None:
        raise SystemExit("committed Phase-3 shuffled (a) cell missing from the state file — "
                         "leg 1 of the leak rider cannot run")
    out = {"band": band, "committed_shuffled_a": ca["test_acc"]}
    if sf is not None:
        out["shuffled_fplus"] = sf["test_acc"]
        out["leg1_pass"] = bool(sf["test_acc"] <= ca["test_acc"] + band)
        if not out["leg1_pass"]:
            raise SystemExit(f"LEAK RIDER leg 1 FAILED: shuffled fplus {sf['test_acc']:.4f} > "
                             f"committed shuffled (a) {ca['test_acc']:.4f} + {band} — a leak in "
                             "the TOK / hz blocks; halting")
    if sb is not None:
        if sf is None:
            raise SystemExit("shuffled fplus_b has no shuffled fplus partner (--only too narrow?)")
        out["shuffled_fplus_b"] = sb["test_acc"]
        out["leg2_pass"] = bool(sb["test_acc"] <= sf["test_acc"] + band)
        if not out["leg2_pass"]:
            raise SystemExit(f"LEAK RIDER leg 2 FAILED: shuffled fplus_b {sb['test_acc']:.4f} > "
                             f"shuffled fplus {sf['test_acc']:.4f} + {band} — a leak in the "
                             "slots block; halting")
    out["pass"] = bool(out.get("leg1_pass") and out.get("leg2_pass"))
    return out


def reader_validity(cells: list[dict], mf_rows: list[dict], space: str,
                    tol: float = READER_FLOOR_TOL) -> dict:
    """The pinned precondition at the gate cell: all 9 unshuffled probes
    hold the constant predictor (test_acc >= majority - tol) and the full
    free baseline is not CI-clear worse than its own (a) subset."""
    gate_cells = [c for c in cells if not c["shuffled"] and c["space"] == space
                  and c["offset"] == GATE_OFFSET and c["capacity"] == GATE_CAPACITY]
    gaps = {c["cell"]: c["test_acc"] - c["majority_rate_test"] for c in gate_cells}
    mf = next((m for m in mf_rows if m["space"] == space and m["offset"] == GATE_OFFSET
               and m["capacity"] == GATE_CAPACITY), None)
    complete = len(gate_cells) == len(ARMS) * len(SEEDS) and mf is not None
    floor_ok = complete and all(g >= -tol for g in gaps.values())
    mf_ok = complete and mf["ci95"][1] >= 0
    # best_epoch summary: REPORTED, never gating (second critic round: the
    # smoke selected epoch 0 on every fplus cell; the reader is disclosed)
    best_epochs = {arm: sorted(int(c["best_epoch"]) for c in gate_cells
                               if c["features"] == arm and c.get("best_epoch") is not None)
                   for arm in ARMS}
    return {"ok": bool(complete and floor_ok and mf_ok), "complete": bool(complete),
            "floor_ok": bool(floor_ok), "mf_ok": bool(mf_ok),
            "min_acc_minus_floor": (min(gaps.values()) if gaps else None),
            "mf_gate_ci_upper": (mf["ci95"][1] if mf else None),
            "best_epochs_gate_cell": best_epochs,
            "tol": tol,
            "rule": ("all 9 gate-cell probes test_acc >= majority_rate_test - tol AND "
                     "Mf(L1/off2/mlp256) CI95 upper >= 0; else READER-INVALID")}


def gate_fires(row: dict | None) -> bool:
    """The Phase-3 triple rule on one D row, with the structural guards
    run_probes.verdict applies (three seeds, thirty clusters, right pair)."""
    if row is None or row.get("pair") != GATE_PAIR:
        return False
    if row.get("n_seeds") != len(SEEDS) or row.get("n_clusters") != 30:
        return False
    return bool(row["ci95"][0] > 0
                and all(v > 0 for v in row["per_seed_margin"].values())
                and row["margin"] >= MATERIALITY)


def gate_row(rows: list[dict], space: str, offset: int = GATE_OFFSET,
             capacity: str = GATE_CAPACITY) -> dict | None:
    return next((m for m in rows if m["space"] == space
                 and m["offset"] == offset and m["capacity"] == capacity), None)


def source_label(primary: dict | None, replication: dict | None,
                 primary_rows: list[dict] | None = None,
                 replication_rows: list[dict] | None = None,
                 reader_ok: tuple[bool, bool] = (True, True)) -> str:
    """Pinned per-source label from the two harvests' gate rows (and, for
    ABSORBED, every D row of both harvests)."""
    if primary is None or replication is None:
        return LABEL_INCOMPLETE
    if not (reader_ok[0] and reader_ok[1]):
        return LABEL_READER_INVALID
    fp, fr = gate_fires(primary), gate_fires(replication)
    if fp and fr:
        return LABEL_SURVIVES
    if fp != fr:
        return LABEL_SPLIT
    rows = list(primary_rows or []) + list(replication_rows or [])
    if rows and all(m["ci95"][1] < MATERIALITY for m in rows):
        return LABEL_ABSORBED
    return LABEL_NOT_SHOWN


def horizon_note(primary_off3: dict | None, replication_off3: dict | None) -> str | None:
    """S1 offset-3 HORIZON rule (reported, mlp256). OFF3-ABSORBED needs both
    rows to fail AND both CI95 uppers below the floor — a straddle is
    OFF3-NOT-SHOWN, never a narrowing note (second critic round)."""
    if primary_off3 is None and replication_off3 is None:
        return None
    if primary_off3 is None or replication_off3 is None:
        return "OFF3-INCOMPLETE"
    fp, fr = gate_fires(primary_off3), gate_fires(replication_off3)
    if fp and fr:
        return "OFF3-SURVIVES"
    if not fp and not fr:
        if primary_off3["ci95"][1] < MATERIALITY and replication_off3["ci95"][1] < MATERIALITY:
            return "OFF3-ABSORBED"
        return "OFF3-NOT-SHOWN"
    return "OFF3-SPLIT"


def _same_path(a: str, b: str) -> bool:
    try:
        if Path(a).resolve() == Path(b).resolve():
            return True
    except OSError:
        pass
    return Path(a).as_posix().rstrip("/") == Path(b).as_posix().rstrip("/")


def expected_d_rows(space: str) -> int:
    """off2 at two capacities plus one mlp256 row per further offset."""
    tag = "concept" if space == "L1_concept_k16" else "olmoe"
    return 2 + (len(OFFSETS_OF_TAG[tag]) - 1)


def _check_payload(p: dict, role: str) -> str:
    """Structural refusals for --conclude-from; returns the space."""
    sp = p["gate"]["space"]
    if p.get("partial"):
        raise SystemExit(f"{role} payload is PARTIAL (--only run) — no label may issue")
    rider = p.get("rider") or {}
    if not rider.get("pass"):
        raise SystemExit(f"{role} payload's leak rider did not pass — no label may issue")
    if sp not in HARVESTS_OF_SPACE:
        raise SystemExit(f"{role} payload's space {sp!r} is not a registered source")
    tag = "concept" if sp == "L1_concept_k16" else "olmoe"
    if tuple(p.get("offsets", ())) != OFFSETS_OF_TAG[tag]:
        raise SystemExit(f"{role} payload's offsets {p.get('offsets')} are not the registered "
                         f"{list(OFFSETS_OF_TAG[tag])} for {sp}")
    want = HARVESTS_OF_SPACE[sp][0 if role == "primary" else 1]
    if not _same_path(str(p.get("harvest", "")), want):
        raise SystemExit(f"{role} payload's harvest {p.get('harvest')!r} is not the registered "
                         f"{role} harvest {want!r}")
    out_name = Path(str(((p.get("provenance") or {}).get("args") or {}).get("out", ""))).name
    want_out = (("fullfree_s1" if tag == "concept" else "fullfree_s3")
                + ("" if role == "primary" else "_r") + ".json")
    if out_name != want_out:
        raise SystemExit(f"{role} payload was written to {out_name!r}, not the registered "
                         f"{want_out!r} — its state file is scratch, no label may issue")
    if len(p.get("d_fplus_b_vs_fplus_n", [])) != expected_d_rows(sp):
        raise SystemExit(f"{role} payload carries {len(p.get('d_fplus_b_vs_fplus_n', []))} D rows, "
                         f"expected {expected_d_rows(sp)} for {sp} — INCOMPLETE")
    return sp


def conclude(primary_payload: dict, replication_payload: dict) -> dict:
    """Mechanical per-source conclusion from two committed payloads."""
    sp = _check_payload(primary_payload, "primary")
    if _check_payload(replication_payload, "replication") != sp:
        raise SystemExit("the two payloads are from different sources (space names differ)")
    if primary_payload["provenance"]["harvest_npz_sha256"] == \
            replication_payload["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two payloads bind the SAME harvest — not a primary/replication pair")
    p_rows, r_rows = primary_payload["d_fplus_b_vs_fplus_n"], replication_payload["d_fplus_b_vs_fplus_n"]
    gp, gr = gate_row(p_rows, sp), gate_row(r_rows, sp)
    rv = (bool(primary_payload["reader_valid"]["ok"]),
          bool(replication_payload["reader_valid"]["ok"]))
    label = source_label(gp, gr, p_rows, r_rows, reader_ok=rv)
    mt_p = gate_row(primary_payload["mt_fplus_b_vs_fplus"], sp)
    mt_r = gate_row(replication_payload["mt_fplus_b_vs_fplus"], sp)
    # the "full" license needs BOTH Mt rows present with CI95 upper >= 0; a
    # missing row is not a non-negative row (second critic round)
    mt_upper_neg = any(m is None or m["ci95"][1] < 0 for m in (mt_p, mt_r))
    out = {
        "space": sp,
        "label": label,
        "reader_valid": {"primary": rv[0], "replication": rv[1]},
        "gate_primary": gp, "gate_replication": gr,
        "gate_fires": {"primary": gate_fires(gp), "replication": gate_fires(gr)},
        "mt_at_gate": {"primary": mt_p, "replication": mt_r},
        "survives_license": (None if label != LABEL_SURVIVES else
                             ("equal-dims-only" if mt_upper_neg else "full")),
        "all_d_ci_uppers_below_floor": bool(p_rows and r_rows and all(
            m["ci95"][1] < MATERIALITY for m in list(p_rows) + list(r_rows))),
        "horizon_off3": horizon_note(gate_row(p_rows, sp, offset=3),
                                     gate_row(r_rows, sp, offset=3)),
        "linear_off2_reported": {"primary": gate_row(p_rows, sp, capacity="linear"),
                                 "replication": gate_row(r_rows, sp, capacity="linear")},
        "materiality_floor": MATERIALITY,
        "rule": ("OQ-17 registration (docs/BLUEPRINT.md, 2026-09-06, before any registered "
                 "cell ran; critic round applied before the freeze commit): gate = "
                 "L1/off2/mlp256 D = acc(fplus_b) - acc(fplus_n), Phase-3 triple rule, both "
                 "harvests per source; READER-INVALID precondition; ABSORBED needs every D "
                 "CI95 upper < +0.005 on both harvests, else NOT-SHOWN"),
    }
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/fullfree_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="substring filter on cell ids (smoke)")
    # Source parametrization (registered S3 instrument-change pattern): every
    # default is the S1 path/tag/alphabet; offsets are bound to the tag.
    ap.add_argument("--space-tag", default="concept")
    ap.add_argument("--n-slots", type=int, default=512,
                    help="telemetry alphabet (S1 slots 512, S3 experts 64); bound to the meta")
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    ap.add_argument("--parent-finding", default="F-15",
                    help="the K-2 finding the consequence rules act on (S1 F-15, S3 F-17)")
    ap.add_argument("--conclude-from", nargs=2, metavar=("PRIMARY", "REPLICATION"),
                    default=None, help="print the per-source label from two payloads; runs nothing")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.conclude_from:
        pp = json.loads(Path(args.conclude_from[0]).read_text())
        rp = json.loads(Path(args.conclude_from[1]).read_text())
        print(json.dumps(conclude(pp, rp), indent=1))
        return

    registered_outs = {(REAL / n).resolve() for n in REGISTERED_OUTS}
    if args.only and Path(args.out).resolve() in registered_outs:
        raise SystemExit("--only smoke runs may not write a registered out path")
    offsets = offsets_for_tag(args.space_tag)

    data = HarvestData(args.harvest)
    split_names = data.row_split()  # R3 abort-on-violation, before anything trains
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)

    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing (registered gate)")
    rider_payload = json.loads(fid.read_text())
    if rider_payload.get("verdict") != "PASS":
        raise SystemExit("R1 rider verdict is not PASS — harvest quarantined")
    if rider_payload.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider validated a DIFFERENT harvest version")

    p3_cells = load_phase3_cells(Path(args.phase3_state),
                                 Path(args.phase3_payload), data.npz_shas)
    p3_payload = json.loads(Path(args.phase3_payload).read_text())
    re_m = margins(p3_cells, "c", expected_clusters=30)
    want = {(m["space"], m["offset"], m["capacity"]): m for m in p3_payload["margins"]}
    for m in re_m:
        w = want.get((m["space"], m["offset"], m["capacity"]))
        if w is None or abs(m["margin"] - w["margin"]) > 1e-12 \
                or max(abs(a - b) for a, b in zip(m["ci95"], w["ci95"])) > 1e-12:
            raise SystemExit("phase-3 state file does not reproduce its own payload "
                             f"margins at {m['space']} off{m['offset']} {m['capacity']}")

    names = space_names(args.space_tag)
    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    space = names["L1"]
    if space not in spaces:
        raise SystemExit(f"label space {space} not built")
    if committed_shuffled_a(p3_cells, space) is None:
        raise SystemExit("committed shuffled (a) cell missing — the leak rider's leg 1 needs it")

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    t_m = time.time()
    moments = train_moments(hidden, data.lengths, split_names)
    print(f"[moments] train rows {moments['n_train_rows']}, positions "
          f"{moments['n_train_positions']}, sha {moments['sha256'][:12]}, "
          f"{time.time() - t_m:.0f}s", flush=True)
    factory_of = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments)

    probe_rows = np.zeros(1, np.int64)
    a_dim = sum(b.dim for b in feature_blocks(data, "a", probe_rows, probe_rows,
                                              n_slots=args.n_slots))
    dims_recorded = {arm: [b.dim for b in factory_of[arm](probe_rows, probe_rows)]
                     for arm in ARMS}
    dims_recorded["a"] = int(a_dim)
    dims_recorded["hidden"] = int(hidden.shape[2])
    dims_recorded["tok_bins"] = int(FREETOK_BINS)
    dims_total = {arm: int(a_dim + sum(dims_recorded[arm])) for arm in ARMS}
    if dims_total["fplus_b"] != dims_total["fplus_n"]:
        raise SystemExit("twin arms are not equal-dims — refusing")

    grid = build_grid(space, offsets)
    state_path = Path(args.out + ".state.jsonl")
    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells: list[dict] = []
    rider = None
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if args.only and args.only not in cid:
            continue
        if cid in done:
            res = done[cid]
            cells.append(res)
        else:
            res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                           shuffled=shuffled, extra_factory=factory_of[arm],
                           feats_label=arm, n_slots=args.n_slots)
            cells.append(res)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
                  f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
                  f"total {time.time() - t0:.0f}s", flush=True)
        if shuffled:
            # both legs, fresh or resumed alike (a halt a Ctrl-C disarms is not a halt)
            rider = rider_check(cells, p3_cells, space)

    r2_ok = bool(rider and rider.get("pass"))
    expected = None if args.only else 30
    pooled = cells + p3_cells
    d_rows = margins(cells, "fplus_b", expected_clusters=expected, base_feats="fplus_n") if r2_ok else []
    mt = margins(cells, "fplus_b", expected_clusters=expected, base_feats="fplus") if r2_ok else []
    mn = margins(cells, "fplus_n", expected_clusters=expected, base_feats="fplus") if r2_ok else []
    mf = margins(pooled, "fplus", expected_clusters=expected, base_feats="a") if r2_ok else []
    mc = margins(pooled, "fplus", expected_clusters=expected, base_feats="c") if r2_ok else []
    reader = reader_validity(cells, mf, space)
    gate = gate_row(d_rows, space)

    def _git() -> tuple[str, list[str]]:
        """HEAD plus a -dirty flag over TRACKED files only (untracked
        evidence files — the other process's payloads, this run's own
        state file — no longer make the attestation uninformative); the
        porcelain list is recorded beside it."""
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, timeout=10)
            lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
            return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
        except Exception:
            return "unknown", []

    git_commit, git_porcelain = _git()

    import torch

    payload = {
        "registered": ("OQ-17 FULL-FREE EXISTENCE RE-TEST REGISTRATION (docs/BLUEPRINT.md, "
                       "2026-09-06, before any registered cell ran; critic round applied before "
                       f"the freeze commit); consequence rules act on {args.parent_finding}"),
        "harvest": args.harvest,
        "n_cells": len([c for c in cells if not c["shuffled"]]),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),  # FRESH-STATE PIN: 0 on a registered run
        "offsets": list(offsets),
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "rider": rider,
        "reader_valid": reader,
        "d_fplus_b_vs_fplus_n": d_rows,
        "mt_fplus_b_vs_fplus": mt,
        "mn_fplus_n_vs_fplus_dilution": mn,
        "mf_fplus_vs_a": mf,
        "mc_fplus_vs_c": mc,
        "gate": {"space": space, "offset": GATE_OFFSET, "capacity": GATE_CAPACITY,
                 "row": gate, "fires": bool(reader["ok"] and gate_fires(gate)),
                 "label_if_alone": (LABEL_READER_INVALID if not reader["ok"] else None),
                 "rule": ("READER-INVALID precondition, then D CI95 lower > 0, all three "
                          "seeds positive, point >= +0.005")},
        "standardization": {
            "block": "hz = clip(h_a, train lo, train hi) then (x - train mu) / max(train sd, sd_floor)",
            "moments_sha256": moments["sha256"],
            "n_train_rows": moments["n_train_rows"],
            "n_train_positions": moments["n_train_positions"],
            "sd_floor": moments["sd_floor"],
            "sd_min": float(moments["sd"].min()), "sd_median": float(np.median(moments["sd"])),
            "sd_max": float(moments["sd"].max()),
            "abs_lo_hi_max": float(max(np.abs(moments["lo"]).max(), np.abs(moments["hi"]).max())),
        },
        "phase3_state": str(args.phase3_state),
        "phase3_payload_margins_reproduced": True,
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "label_space_sha256": {p.name: _sha(p) for p in (
                Path(args.buckets16), Path(args.glue16),
                Path(args.buckets512), Path(args.glue512),
                Path(args.groups)) if p.exists()},
            "feature_dims_recorded": dims_recorded,
            "arm_dims_total": dims_total,
            "phase3_state_sha256": _sha(Path(args.phase3_state)),
            "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
            "slot_shift": SLOT_SHIFT,
            "torch_version": torch.__version__,
            "device": args.device,
            "determinism_note": ("CUDA probe training uses atomics; per-cell results are "
                                 "evidenced by the recorded state file, not rerun-exactness"),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(json.dumps({"reader_valid": reader["ok"], "gate_fires": payload["gate"]["fires"],
                      "gate": gate, "rider": rider, "n_d_rows": len(d_rows)}, indent=1))


if __name__ == "__main__":
    main()

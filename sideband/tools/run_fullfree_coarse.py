#!/usr/bin/env python3
"""OQ-18 COARSE-LABEL FULL-FREE existence re-test at L2 / L3 (registered
2026-09-06 in docs/BLUEPRINT.md "OQ-18 COARSE-LABEL FULL-FREE RE-TEST
REGISTRATION", BEFORE any registered cell ran; critic round applied before
the freeze commit; CRITERION-BEARING for F-15 / F-17 at their L2 / L3 cells
through that block's pinned consequence rules). Plan of record 2026-09-06:
OQ-18 (this) -> OQ-19 (oracle-intermediate ceiling) -> assess.

QUESTION. F-24 (OQ-17) re-tested F-15 / F-17 against the FULL free baseline
at L1 only (the finest label space) and read ABSORBED at both sources. The
coarser spaces L2 (k512 concepts + merged glue) and L3 (transition-coherent
concept groups) carry the LARGEST registered margins over the 657-summary
proxy, and those margins GROW with coarse-graining (F-15 / F-17, primary /
replication, all LINEAR cells — Phase 3 ran L2 / L3 at linear capacity
only: L2 off2 +0.0277 / +0.0245 at S1 and +0.0206 / +0.0207 at S3; L3 off2
+0.0443 / +0.0427 at S1 and +0.0721 / +0.0730 at S3). They stand against
the proxy and were never tested against the full free baseline. This tool
runs the OQ-17 design at L2 and L3.

ARMS (feature labels in cell ids; block ORDER identical across arms so the
seeded init tensor lands on the same feature positions):
  fplus   = (a) 657 ++ TOK ++ hz — the OQ-17 full free baseline (TOK =
            multi-hot of the anchor's top-32 next-token ids hashed id mod
            2048; hz = h_a clipped to the TRAIN support and z-scored with
            TRAIN moments; byte-identical rule to run_fullfree.py, whose
            moments sha must equal the committed OQ-17 payload's for the
            same harvest — asserted at launch)
  fplus_b = fplus ++ (b) aligned telemetry multi-hot
  fplus_r = fplus ++ the CORRECTED equal-dims twin: the slots of the same-
            generation-index row of a DIFFERENT PROMPT of the same split at
            the same anchor index (run_fullfree_twin.derangement_by_prompt,
            default_rng(1000 + train seed)) — the twin OQ-17's post-hoc
            diagnostic found label-inert / prompt-independent by construction
            (NOT accuracy-inert: F-24's Mn_r was +0.0032 / +0.0020 / +0.0033 /
            +0.0005) and TWIN-ROBUST at both sources. The OQ-17 shift twin
            (anchor + 17 on the same row) is NOT used: it reads beyond the
            label position for ~94% of anchors.
  a       = the registered 657-summary arm run FRESH at mlp256 (Phase 3 has
            no mlp256 cells at L2 / L3) so Mf and the precondition read at
            the gate capacity; the COMMITTED linear (a) / (c) cells are
            paired for Mf / Mc at linear and for the Mf_x collapse leg.
CELLS per harvest, per space (L2 then L3): the LEAK RIDER first — shuffled
(a), shuffled fplus, shuffled fplus_b at off2 / linear / seed 0 (the
shuffled (a) reference is FRESH because Phase 3 shuffled L1 only; leg 1:
shuffled fplus <= shuffled (a) + 0.01, leg 2: shuffled fplus_b <= shuffled
fplus + 0.01, either failure halts the run before any payload is written,
so the whole harvest — both spaces — is then label-less) — then fresh (a)
x mlp256 x off2 x 3 seeds, then off2 x {linear, mlp256} x 3 seeds x 3 arms
= 18, then each further registered offset x mlp256 x 3 seeds x 3 arms = 9.
Offsets are BOUND per space to the F-15 / F-17 firing sets (fired on BOTH
harvests): S1 L2 {2,3}, S1 L3 {2,3}, S3 L2 {2,3}, S3 L3 {2,3,4}. Totals per
harvest: S1 33 + 33 = 66 cells (60 trained + 6 shuffled); S3 33 + 42 = 75
(69 + 6). Same trainer, budget, estimand and bootstrap as Phase 3 / OQ-17
(seed-summed per-prompt successes, paired_cluster_delta_ci, n_boot 2000,
seed 0; exactly 30 test clusters or the pairing is refused).

READOUTS per space (pinned):
  D    = acc(fplus_b) - acc(fplus_r)   equal dims — THE gate readout
  Mt   = acc(fplus_b) - acc(fplus)     dims-asymmetric; quoted beside D
  Mn_r = acc(fplus_r) - acc(fplus)     the corrected twin's own gain; descriptive
  Mf   = acc(fplus)   - acc(a)         fresh (a) at mlp256, committed (a) at linear
  Mf_x = acc(fplus, mlp256) - acc(committed (a), linear)   the collapse leg
  Mc   = acc(fplus)   - acc(c)         committed (c) at linear; reported
READER VALIDITY per space at the gate cell off2 / mlp256, three legs: every
one of the 12 unshuffled probes (3 arms + (a), 3 seeds) has test_acc >=
majority_rate_test - 0.001; the Mf row at the gate cell has CI95 upper >= 0;
AND the Mf_x row (fplus at mlp256 paired against the COMMITTED linear (a)
cells of the same rows and anchors) has CI95 upper >= 0 — the leg that sees
a reader collapsed to the constant predictor (test_acc == majority on every
probe passes legs 1-2 with Mf = 0 exactly; it cannot pass leg 3 where the
committed linear (a) reads above the floor). Otherwise that (harvest,
space) is READER-INVALID and no label issues.
GATE per space per harvest: off2 / mlp256 D under the Phase-3 triple rule
(CI95 lower > 0, all three seeds positive, point >= +0.005; the row must
carry n_seeds 3, n_clusters 30 and the fplus_b-fplus_r pairing).
LABELS per (source, space), from BOTH harvests (--conclude-from PRIMARY
REPLICATION): READER-INVALID / SURVIVES-FULL-FREE / SPLIT / ABSORBED (every
D row's CI95 upper < +0.005 on both harvests) / NOT-SHOWN, the OQ-17 rules
verbatim (INCOMPLETE is the label of a payload-less source: --conclude-from
refuses a payload with a missing D row, so it never issues from it);
HORIZON notes OFF3-* (and OFF4-* on S3 L3) at each further offset, the
OQ-17 rule (a straddle never narrows). A SURVIVES license is FULL only if
Mt's AND Mn_r's CI95 uppers are >= 0 on both harvests (a fire bought by a
CI-clear harmful twin is equal-dims-only). Every label is a statement about
the registered reader at the registered budget.

Run (GPU box):
    python tools/run_fullfree_coarse.py --out results/real/fullfree_coarse_s1.json
    python tools/run_fullfree_coarse.py --harvest results/real/harvest_shadow_r \
        --fidelity results/real/harvest_fidelity_rider_r.json \
        --phase3-state results/real/probes_s1_replication.json.state.jsonl \
        --phase3-payload results/real/probes_s1_replication.json \
        --out results/real/fullfree_coarse_s1_r.json
    (S3: --space-tag olmoe --n-slots 64 --parent-finding F-17 and the olmoe
     buckets / glue / groups / rider / phase-3 paths.)
    python tools/run_fullfree_coarse.py --conclude-from \
        results/real/fullfree_coarse_s1.json results/real/fullfree_coarse_s1_r.json
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
from run_posthoc_topic import load_phase3_cells  # noqa: E402
from run_probes import (REAL, MATERIALITY, SlotsAnchorBlock,  # noqa: E402
                        bind_spaces_to_harvest, build_spaces, cell_id,
                        feature_blocks, margins, parse_state, run_cell,
                        space_names, state_header)
from run_fullfree import (R2_BAND, READER_FLOOR_TOL, LABEL_SURVIVES,  # noqa: E402
                          LABEL_ABSORBED, LABEL_NOT_SHOWN, LABEL_SPLIT,
                          LABEL_INCOMPLETE, LABEL_READER_INVALID,
                          HiddenZBlock, TokAnchorBlock, _same_path, _sha,
                          train_moments)
from run_fullfree_twin import (TWIN_SEED_BASE, CONSTRUCTION,  # noqa: E402
                               OtherRowSlotsBlock, derangement_by_prompt,
                               twin_geometry)

SEEDS = (0, 1, 2)
ARMS = ("fplus", "fplus_b", "fplus_r")
TWIN_ARM = "fplus_r"
BASE_ARM = "a"
LIN_BASE = "a_lin"          # the COMMITTED linear (a) cells relabeled for the Mf_x collapse leg
GATE_OFFSET = 2
GATE_CAPACITY = "mlp256"
GATE_PAIR = "fplus_b-fplus_r"
PAIR_MT = "fplus_b-fplus"
PAIR_MNR = "fplus_r-fplus"
PAIR_MF = "fplus-a"
PAIR_MFX = f"fplus-{LIN_BASE}"
LEVELS = ("L2", "L3")
REGISTERED_OUTS = ("fullfree_coarse_s1.json", "fullfree_coarse_s1_r.json",
                   "fullfree_coarse_s3.json", "fullfree_coarse_s3_r.json")
# Registered offsets per space: the F-15 / F-17 firing sets that fired on
# BOTH harvests (results/real/probes_{s1,s1_replication,s3,s3_replication}
# .json decision.existence_triples, read 2026-09-06). S1 L2 off4 fired on
# the primary only and is NOT registered.
OFFSETS_OF_SPACE = {"L2_concept_k512": (2, 3), "L3_concept_groups_v1": (2, 3),
                    "L2_olmoe_k512": (2, 3), "L3_olmoe_groups_v1": (2, 3, 4)}
HARVESTS_OF_TAG = {"concept": ("results/real/harvest_shadow", "results/real/harvest_shadow_r"),
                   "olmoe": ("results/real/harvest_moe", "results/real/harvest_moe_r")}
OUT_STEM_OF_TAG = {"concept": "fullfree_coarse_s1", "olmoe": "fullfree_coarse_s3"}
# The committed OQ-17 payload of each registered harvest: its hz moments sha
# must equal this run's (the "byte-identical rule" claim, asserted).
FULLFREE_OF_HARVEST = {"results/real/harvest_shadow": "fullfree_s1.json",
                       "results/real/harvest_shadow_r": "fullfree_s1_r.json",
                       "results/real/harvest_moe": "fullfree_s3.json",
                       "results/real/harvest_moe_r": "fullfree_s3_r.json"}


def tag_of_space(space: str) -> str:
    for tag in HARVESTS_OF_TAG:
        if f"_{tag}_" in space:
            return tag
    raise SystemExit(f"space {space!r} belongs to no registered source")


def offsets_for_space(space: str, offsets_of: dict | None = None) -> tuple[int, ...]:
    table = OFFSETS_OF_SPACE if offsets_of is None else offsets_of
    if space not in table:
        raise SystemExit(f"unregistered space {space!r}: offsets are bound per space")
    offs = tuple(int(o) for o in table[space])
    if not offs or any(o < 2 for o in offs) or offs[0] != GATE_OFFSET:
        raise SystemExit(f"{space}: registered offsets must start at {GATE_OFFSET} (K-2 reads offsets >= 2)")
    return offs


def registered_spaces(tag: str) -> tuple[str, ...]:
    names = space_names(tag)
    return tuple(names[lv] for lv in LEVELS)


# ---------------------------------------------------------------------------
# Feature factories (per train seed: the corrected twin's derangement is
# seeded by the train seed, as in the OQ-17 diagnostic)
# ---------------------------------------------------------------------------

def make_factories(top_ids: np.ndarray, hidden: np.ndarray, slots: np.ndarray,
                   lengths: np.ndarray, n_slots: int, moments: dict,
                   perms: dict[int, np.ndarray], n_bins: int = FREETOK_BINS) -> dict:
    """{(arm, seed): factory}. Each factory returns the arm's EXTRA blocks
    (appended after the registered (a) blocks by run_cell): TOK, hz, then
    the slots block last — the same order in fplus_b and fplus_r."""

    def free_extras(rows, anchors):
        return [TokAnchorBlock(top_ids, rows, anchors, n_bins),
                HiddenZBlock(hidden, rows, anchors, moments)]

    def fplus(rows, anchors):
        return free_extras(rows, anchors)

    def fplus_b(rows, anchors):
        return free_extras(rows, anchors) + [SlotsAnchorBlock(slots, rows, anchors, n_slots)]

    def twin_factory(perm):
        def fplus_r(rows, anchors):
            return free_extras(rows, anchors) + [
                OtherRowSlotsBlock(slots, rows, anchors, lengths, perm, n_slots)]
        return fplus_r

    out = {}
    for seed in SEEDS:
        if seed not in perms:
            raise SystemExit(f"no derangement for train seed {seed}")
        out[("fplus", seed)] = fplus
        out[("fplus_b", seed)] = fplus_b
        out[("fplus_r", seed)] = twin_factory(perms[seed])
    return out


# ---------------------------------------------------------------------------
# Grid, committed-cell checks, rider, precondition, labels
# ---------------------------------------------------------------------------

def build_grid(spaces: tuple[str, ...] | list[str], offsets_of: dict | None = None) -> list[tuple]:
    """(space, offset, arm, capacity, seed, shuffled), space by space: the
    leak rider's three shuffled cells first (fresh shuffled (a) reference,
    shuffled fplus, shuffled fplus_b), then the fresh (a) mlp256 cells,
    then off2 at both capacities and every further registered offset at
    mlp256 only (the OQ-17 economy)."""
    grid: list[tuple] = []
    for sp in spaces:
        offs = offsets_for_space(sp, offsets_of)
        grid += [(sp, GATE_OFFSET, BASE_ARM, "linear", 0, True),
                 (sp, GATE_OFFSET, "fplus", "linear", 0, True),
                 (sp, GATE_OFFSET, "fplus_b", "linear", 0, True)]
        grid += [(sp, GATE_OFFSET, BASE_ARM, GATE_CAPACITY, seed, False) for seed in SEEDS]
        for off in offs:
            caps = ("linear", GATE_CAPACITY) if off == GATE_OFFSET else (GATE_CAPACITY,)
            for seed in SEEDS:
                for cap in caps:
                    for arm in ARMS:
                        grid.append((sp, off, arm, cap, seed, False))
    if len({cell_id(*c) for c in grid}) != len(grid):
        raise SystemExit("duplicate cell ids in the grid")
    return grid


def check_grid_against_committed(grid: list[tuple], p3_ids: set[str],
                                 spaces: tuple[str, ...] | list[str],
                                 offsets_of: dict | None = None) -> None:
    """Refuse (i) any grid cell id that already exists in the committed
    Phase-3 state (no committed cell is ever re-trained or overwritten) and
    (ii) a missing committed linear (a) / (c) cell at any registered
    (space, offset, seed) — Mf / Mc / Mf_x pair against them."""
    dup = [cell_id(*c) for c in grid if cell_id(*c) in p3_ids]
    if dup:
        raise SystemExit(f"grid cell ids collide with committed Phase-3 cells: {dup[:3]} ...")
    for sp in spaces:
        for off in offsets_for_space(sp, offsets_of):
            for seed in SEEDS:
                for base in ("a", "c"):
                    if cell_id(sp, off, base, "linear", seed) not in p3_ids:
                        raise SystemExit(f"committed Phase-3 ({base}) linear cell missing at "
                                         f"{sp} off{off} s{seed}")


def relabel_committed_linear_a(p3_cells: list[dict], space: str, offset: int = GATE_OFFSET,
                               capacity: str = GATE_CAPACITY) -> list[dict]:
    """Copies of the COMMITTED unshuffled linear (a) cells of the space at
    the gate offset, relabeled features=LIN_BASE at the gate capacity, so
    margins() pairs the gate-capacity fplus cells against the LINEAR read of
    their own 657-dim subset (same rows, anchors and trials) — the Mf_x
    collapse leg of the precondition. Nothing else is copied or changed."""
    out = []
    for c in p3_cells:
        if (c.get("space") == space and c.get("offset") == offset and c.get("features") == "a"
                and c.get("capacity") == "linear" and not c.get("shuffled")):
            d = dict(c)
            d["features"] = LIN_BASE
            d["capacity"] = capacity
            d["cell"] = cell_id(space, offset, LIN_BASE, capacity, int(c["seed"]))
            out.append(d)
    return out


def rider_check(cells: list[dict], space: str, band: float = R2_BAND) -> dict | None:
    """Two-leg leak rider per space on the shuffled cells present so far;
    raises SystemExit on a failed leg (fresh or resumed cells alike). The
    reference is this run's own shuffled (a) cell of the same space (Phase
    3 shuffled L1 only). Returns None until any shuffled cell of the space
    exists."""
    sh = [c for c in cells if c["shuffled"] and c["space"] == space and c["offset"] == GATE_OFFSET
          and c["capacity"] == "linear"]
    if not sh:
        return None
    sa = next((c for c in sh if c["features"] == BASE_ARM), None)
    sf = next((c for c in sh if c["features"] == "fplus"), None)
    sb = next((c for c in sh if c["features"] == "fplus_b"), None)
    if sa is None:
        raise SystemExit(f"{space}: the fresh shuffled (a) reference is missing — leg 1 of the "
                         "leak rider cannot run (--only too narrow?)")
    out = {"band": band, "space": space, "shuffled_a": sa["test_acc"]}
    if sf is not None:
        out["shuffled_fplus"] = sf["test_acc"]
        out["leg1_pass"] = bool(sf["test_acc"] <= sa["test_acc"] + band)
        if not out["leg1_pass"]:
            raise SystemExit(f"LEAK RIDER leg 1 FAILED at {space}: shuffled fplus {sf['test_acc']:.4f} "
                             f"> shuffled (a) {sa['test_acc']:.4f} + {band} — a leak in the TOK / hz "
                             "blocks; halting")
    if sb is not None:
        if sf is None:
            raise SystemExit(f"{space}: shuffled fplus_b has no shuffled fplus partner")
        out["shuffled_fplus_b"] = sb["test_acc"]
        out["leg2_pass"] = bool(sb["test_acc"] <= sf["test_acc"] + band)
        if not out["leg2_pass"]:
            raise SystemExit(f"LEAK RIDER leg 2 FAILED at {space}: shuffled fplus_b {sb['test_acc']:.4f} "
                             f"> shuffled fplus {sf['test_acc']:.4f} + {band} — a leak in the slots "
                             "block; halting")
    out["pass"] = bool(out.get("leg1_pass") and out.get("leg2_pass"))
    return out


def reader_validity(cells: list[dict], mf_rows: list[dict], mfx_rows: list[dict], space: str,
                    tol: float = READER_FLOOR_TOL) -> dict:
    """The pinned three-leg precondition at the space's gate cell: all 12
    unshuffled probes (3 arms + (a), 3 seeds) hold the constant predictor;
    the full free baseline is not CI-clear worse than its own fresh (a)
    subset (Mf); and it is not CI-clear worse than the COMMITTED LINEAR read
    of that subset (Mf_x) — the leg a collapsed reader cannot pass."""
    probes = tuple(ARMS) + (BASE_ARM,)
    gate_cells = [c for c in cells if not c["shuffled"] and c["space"] == space
                  and c["offset"] == GATE_OFFSET and c["capacity"] == GATE_CAPACITY
                  and c["features"] in probes]
    gaps = {c["cell"]: c["test_acc"] - c["majority_rate_test"] for c in gate_cells}

    def _gate(rows, pair):
        return next((m for m in rows if m["space"] == space and m["offset"] == GATE_OFFSET
                     and m["capacity"] == GATE_CAPACITY and m.get("pair") == pair), None)

    mf = _gate(mf_rows, PAIR_MF)
    mfx = _gate(mfx_rows, PAIR_MFX)
    complete = len(gate_cells) == len(probes) * len(SEEDS) and mf is not None and mfx is not None
    floor_ok = complete and all(g >= -tol for g in gaps.values())
    mf_ok = complete and mf["ci95"][1] >= 0
    mfx_ok = complete and mfx["ci95"][1] >= 0
    best_epochs = {arm: sorted(int(c["best_epoch"]) for c in gate_cells
                               if c["features"] == arm and c.get("best_epoch") is not None)
                   for arm in probes}
    fplus_minus_floor = sorted(round(c["test_acc"] - c["majority_rate_test"], 6)
                               for c in gate_cells if c["features"] == "fplus")
    return {"ok": bool(complete and floor_ok and mf_ok and mfx_ok), "complete": bool(complete),
            "floor_ok": bool(floor_ok), "mf_ok": bool(mf_ok), "mfx_ok": bool(mfx_ok),
            "n_gate_probes": len(gate_cells),
            "min_acc_minus_floor": (min(gaps.values()) if gaps else None),
            "mf_gate_ci_upper": (mf["ci95"][1] if mf else None),
            "mfx_gate_ci_upper": (mfx["ci95"][1] if mfx else None),
            "mfx_gate_margin": (mfx["margin"] if mfx else None),
            "acc_fplus_minus_floor_per_seed": fplus_minus_floor,
            "best_epochs_gate_cell": best_epochs,
            "tol": tol,
            "rule": ("all 12 gate-cell probes (3 arms + (a), 3 seeds) test_acc >= "
                     "majority_rate_test - tol AND Mf(off2/mlp256, vs fresh (a)) CI95 upper >= 0 "
                     "AND Mf_x(off2: fplus mlp256 vs the COMMITTED linear (a)) CI95 upper >= 0; "
                     "else READER-INVALID")}


def fires_triple(row: dict | None, pair: str) -> bool:
    """The Phase-3 triple rule on one margin row of the given pairing, with
    the structural guards (three seeds, thirty clusters, the right pair)."""
    if row is None or row.get("pair") != pair:
        return False
    if row.get("n_seeds") != len(SEEDS) or row.get("n_clusters") != 30:
        return False
    return bool(row["ci95"][0] > 0
                and all(v > 0 for v in row["per_seed_margin"].values())
                and row["margin"] >= MATERIALITY)


def gate_fires(row: dict | None) -> bool:
    """The triple rule on a D row (the fplus_b-fplus_r pairing)."""
    return fires_triple(row, GATE_PAIR)


def gate_row(rows: list[dict], space: str, offset: int = GATE_OFFSET,
             capacity: str = GATE_CAPACITY) -> dict | None:
    return next((m for m in rows if m["space"] == space
                 and m["offset"] == offset and m["capacity"] == capacity), None)


def source_label(primary: dict | None, replication: dict | None,
                 primary_rows: list[dict] | None = None,
                 replication_rows: list[dict] | None = None,
                 reader_ok: tuple[bool, bool] = (True, True)) -> str:
    """Pinned per-(source, space) label from the two harvests' gate rows
    (and, for ABSORBED, every D row of both harvests) — the OQ-17 rule."""
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


def horizon_note(primary_row: dict | None, replication_row: dict | None, offset: int) -> str | None:
    """HORIZON rule at a further offset (mlp256): OFFk-ABSORBED needs both
    rows to fail AND both CI95 uppers below the floor; a straddle is
    OFFk-NOT-SHOWN, never a narrowing note (the OQ-17 rule)."""
    k = f"OFF{int(offset)}"
    if primary_row is None and replication_row is None:
        return None
    if primary_row is None or replication_row is None:
        return f"{k}-INCOMPLETE"
    fp, fr = gate_fires(primary_row), gate_fires(replication_row)
    if fp and fr:
        return f"{k}-SURVIVES"
    if not fp and not fr:
        if primary_row["ci95"][1] < MATERIALITY and replication_row["ci95"][1] < MATERIALITY:
            return f"{k}-ABSORBED"
        return f"{k}-NOT-SHOWN"
    return f"{k}-SPLIT"


def expected_d_rows(space: str) -> int:
    """off2 at two capacities plus one mlp256 row per further offset."""
    return 2 + (len(offsets_for_space(space)) - 1)


def only_match(only: str | None, cid: str) -> bool:
    """--only: comma-separated substrings, any match (smoke only)."""
    if not only:
        return True
    return any(s and s in cid for s in only.split(","))


def _rows_of(payload: dict, space: str, key: str) -> list[dict]:
    return list(((payload.get("per_space") or {}).get(space) or {}).get(key) or [])


def _check_payload(p: dict, role: str) -> str:
    """Structural refusals for --conclude-from; returns the source tag."""
    tag = p.get("tag")
    if p.get("partial"):
        raise SystemExit(f"{role} payload is PARTIAL (--only run) — no label may issue")
    if tag not in HARVESTS_OF_TAG:
        raise SystemExit(f"{role} payload's tag {tag!r} is not a registered source")
    if tuple(p.get("levels", ())) != LEVELS:
        raise SystemExit(f"{role} payload's levels {p.get('levels')} are not the registered {list(LEVELS)}")
    spaces = registered_spaces(tag)
    if tuple(p.get("spaces_registered", ())) != spaces:
        raise SystemExit(f"{role} payload's spaces are not the registered {list(spaces)}")
    want = HARVESTS_OF_TAG[tag][0 if role == "primary" else 1]
    if not _same_path(str(p.get("harvest", "")), want):
        raise SystemExit(f"{role} payload's harvest {p.get('harvest')!r} is not the registered "
                         f"{role} harvest {want!r}")
    out_name = Path(str(((p.get("provenance") or {}).get("args") or {}).get("out", ""))).name
    want_out = OUT_STEM_OF_TAG[tag] + ("" if role == "primary" else "_r") + ".json"
    if out_name != want_out:
        raise SystemExit(f"{role} payload was written to {out_name!r}, not the registered "
                         f"{want_out!r} — its state file is scratch, no label may issue")
    for sp in spaces:
        ps = (p.get("per_space") or {}).get(sp)
        if not ps:
            raise SystemExit(f"{role} payload carries no block for {sp} — INCOMPLETE")
        if not (ps.get("rider") or {}).get("pass"):
            raise SystemExit(f"{role} payload's leak rider did not pass at {sp} — no label may issue")
        if tuple((p.get("offsets_of_space") or {}).get(sp, ())) != offsets_for_space(sp):
            raise SystemExit(f"{role} payload's offsets at {sp} are not the registered "
                             f"{list(offsets_for_space(sp))}")
        d_rows = ps.get("d_fplus_b_vs_fplus_r") or []
        if len(d_rows) != expected_d_rows(sp):
            raise SystemExit(f"{role} payload carries {len(d_rows)} D rows at {sp}, expected "
                             f"{expected_d_rows(sp)} — INCOMPLETE")
        for m in d_rows:
            if m.get("pair") != GATE_PAIR or m.get("n_seeds") != len(SEEDS) or m.get("n_clusters") != 30:
                raise SystemExit(f"{role} payload's D row at {sp} off{m.get('offset')} "
                                 f"{m.get('capacity')} is not structurally complete "
                                 f"(pair / n_seeds 3 / n_clusters 30) — no label may issue")
    return tag


def conclude(primary_payload: dict, replication_payload: dict) -> dict:
    """Mechanical per-(source, space) conclusion from two committed payloads."""
    tag = _check_payload(primary_payload, "primary")
    if _check_payload(replication_payload, "replication") != tag:
        raise SystemExit("the two payloads are from different sources")
    if primary_payload["provenance"]["harvest_npz_sha256"] == \
            replication_payload["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two payloads bind the SAME harvest — not a primary/replication pair")
    out_spaces = {}
    for sp in registered_spaces(tag):
        p_rows = _rows_of(primary_payload, sp, "d_fplus_b_vs_fplus_r")
        r_rows = _rows_of(replication_payload, sp, "d_fplus_b_vs_fplus_r")
        gp, gr = gate_row(p_rows, sp), gate_row(r_rows, sp)
        rv = (bool(primary_payload["per_space"][sp]["reader_valid"]["ok"]),
              bool(replication_payload["per_space"][sp]["reader_valid"]["ok"]))
        label = source_label(gp, gr, p_rows, r_rows, reader_ok=rv)
        mt_p = gate_row(_rows_of(primary_payload, sp, "mt_fplus_b_vs_fplus"), sp)
        mt_r = gate_row(_rows_of(replication_payload, sp, "mt_fplus_b_vs_fplus"), sp)
        mnr_p = gate_row(_rows_of(primary_payload, sp, "mn_r_fplus_r_vs_fplus"), sp)
        mnr_r = gate_row(_rows_of(replication_payload, sp, "mn_r_fplus_r_vs_fplus"), sp)
        # the FULL license needs Mt AND Mn_r rows present with CI95 upper >= 0
        # on both harvests: a fire bought by a CI-clear harmful twin (D = Mt -
        # Mn_r) is equal-dims-only (pre-run critic round, B3)
        mt_upper_neg = any(m is None or m["ci95"][1] < 0 for m in (mt_p, mt_r))
        mnr_upper_neg = any(m is None or m["ci95"][1] < 0 for m in (mnr_p, mnr_r))
        if label != LABEL_SURVIVES:
            license_, reason = None, None
        elif not mt_upper_neg and not mnr_upper_neg:
            license_, reason = "full", None
        else:
            license_ = "equal-dims-only"
            reason = ("Mt CI95 upper < 0 on a harvest" if mt_upper_neg else
                      "Mn_r CI95 upper < 0 on a harvest (fire inflated by the twin's own cost)")
        horizons = {f"off{o}": horizon_note(gate_row(p_rows, sp, offset=o),
                                            gate_row(r_rows, sp, offset=o), o)
                    for o in offsets_for_space(sp) if o != GATE_OFFSET}
        out_spaces[sp] = {
            "label": label,
            "reader_valid": {"primary": rv[0], "replication": rv[1]},
            "gate_primary": gp, "gate_replication": gr,
            "gate_fires": {"primary": gate_fires(gp), "replication": gate_fires(gr)},
            "mt_at_gate": {"primary": mt_p, "replication": mt_r},
            "mn_r_at_gate": {"primary": mnr_p, "replication": mnr_r},
            # the helps-direction readings pinned in the registration (C5)
            "mt_fires_triple_rule": {"primary": fires_triple(mt_p, PAIR_MT),
                                     "replication": fires_triple(mt_r, PAIR_MT)},
            "mn_r_fires_triple_rule": {"primary": fires_triple(mnr_p, PAIR_MNR),
                                       "replication": fires_triple(mnr_r, PAIR_MNR)},
            "survives_license": license_,
            "license_reason": reason,
            "all_d_ci_uppers_below_floor": bool(p_rows and r_rows and all(
                m["ci95"][1] < MATERIALITY for m in list(p_rows) + list(r_rows))),
            "horizons": horizons,
            "linear_off2_reported": {"primary": gate_row(p_rows, sp, capacity="linear"),
                                     "replication": gate_row(r_rows, sp, capacity="linear")},
            "reader_valid_detail": {
                "primary": {k: primary_payload["per_space"][sp]["reader_valid"].get(k)
                            for k in ("mfx_gate_margin", "mfx_gate_ci_upper", "acc_fplus_minus_floor_per_seed")},
                "replication": {k: replication_payload["per_space"][sp]["reader_valid"].get(k)
                                for k in ("mfx_gate_margin", "mfx_gate_ci_upper", "acc_fplus_minus_floor_per_seed")}},
        }
    return {
        "tag": tag,
        "spaces": out_spaces,
        "materiality_floor": MATERIALITY,
        "rule": ("OQ-18 registration (docs/BLUEPRINT.md, 2026-09-06, before any registered cell "
                 "ran; critic round applied before the freeze commit): per space, gate = "
                 "off2/mlp256 D = acc(fplus_b) - acc(fplus_r), Phase-3 triple rule, both harvests "
                 "per source; three-leg READER-INVALID precondition; ABSORBED needs every D CI95 "
                 "upper < +0.005 on both harvests, else NOT-SHOWN; horizons per further offset; "
                 "a SURVIVES license is full only with Mt and Mn_r CI95 uppers >= 0 on both"),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/fullfree_coarse_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None,
                    help="comma-separated substring filter on cell ids (smoke; any match)")
    ap.add_argument("--resume", action="store_true",
                    help="continue a crashed REGISTERED run from its state file")
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
                    default=None, help="print the per-space labels from two payloads; runs nothing")
    return ap


def committed_moments_sha(harvest: str) -> str | None:
    """The hz moments sha of the committed OQ-17 payload for this harvest
    (None for a harvest outside the registered four)."""
    for h, name in FULLFREE_OF_HARVEST.items():
        if _same_path(harvest, h):
            p = REAL / name
            if not p.exists():
                raise SystemExit(f"committed OQ-17 payload {p} missing — the moments binding cannot be checked")
            return json.loads(p.read_text())["standardization"]["moments_sha256"]
    return None


def main() -> None:
    args = build_parser().parse_args()

    if args.conclude_from:
        pp = json.loads(Path(args.conclude_from[0]).read_text())
        rp = json.loads(Path(args.conclude_from[1]).read_text())
        print(json.dumps(conclude(pp, rp), indent=1))
        return

    registered_outs = {(REAL / n).resolve() for n in REGISTERED_OUTS}
    out_path = Path(args.out).resolve()
    registered = out_path in registered_outs
    if args.only and registered:
        raise SystemExit("--only smoke runs may not write a registered out path")
    if registered and OUT_STEM_OF_TAG[args.space_tag] not in out_path.name:
        raise SystemExit(f"registered out {out_path.name} does not belong to --space-tag {args.space_tag}")
    state_path = Path(args.out + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a "
                         "crashed registered run")
    if args.space_tag not in HARVESTS_OF_TAG:
        raise SystemExit(f"unregistered --space-tag {args.space_tag!r}")

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
    p3_ids = {c["cell"] for c in p3_cells}

    spaces = build_spaces(data, tag=args.space_tag,
                          buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512,
                          groups_path=args.groups)
    reg_spaces = registered_spaces(args.space_tag)
    for sp in reg_spaces:
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built")
    grid = build_grid(reg_spaces)
    check_grid_against_committed(grid, p3_ids, reg_spaces)

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    t_m = time.time()
    moments = train_moments(hidden, data.lengths, split_names)
    committed_sha = committed_moments_sha(args.harvest)
    if committed_sha is not None and committed_sha != moments["sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's for this harvest "
                         f"({moments['sha256'][:12]} vs {committed_sha[:12]}) — refusing")
    print(f"[moments] train rows {moments['n_train_rows']}, positions "
          f"{moments['n_train_positions']}, sha {moments['sha256'][:12]}"
          f"{' == committed OQ-17' if committed_sha else ' (harvest outside the registered four)'}, "
          f"{time.time() - t_m:.0f}s", flush=True)
    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    all_offsets = sorted({o for sp in reg_spaces for o in offsets_for_space(sp)})
    geometry = {str(seed): {f"off{o}": twin_geometry(data.lengths, perms[seed], o,
                                                     data.tokens.shape[1], data.prompt_idx)
                            for o in all_offsets}
                for seed in SEEDS}
    for seed, g in geometry.items():
        for o, gg in g.items():
            if gg["corrected_twin_same_prompt_frac"] != 0.0:
                raise SystemExit(f"corrected twin reads its own prompt at seed {seed} {o} — refusing")
    perm_shas = {str(seed): hashlib.sha256(perms[seed].astype(np.int64).tobytes()).hexdigest()
                 for seed in SEEDS}
    factory_of = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments, perms)

    probe_rows = np.zeros(1, np.int64)
    a_dim = sum(b.dim for b in feature_blocks(data, "a", probe_rows, probe_rows,
                                              n_slots=args.n_slots))
    dims_recorded = {arm: [b.dim for b in factory_of[(arm, SEEDS[0])](probe_rows, probe_rows)]
                     for arm in ARMS}
    dims_recorded["a"] = int(a_dim)
    dims_recorded["hidden"] = int(hidden.shape[2])
    dims_recorded["tok_bins"] = int(FREETOK_BINS)
    dims_total = {arm: int(a_dim + sum(dims_recorded[arm])) for arm in ARMS}
    if dims_total["fplus_b"] != dims_total["fplus_r"]:
        raise SystemExit("twin arms are not equal-dims — refusing")

    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells: list[dict] = []
    riders: dict[str, dict | None] = {sp: None for sp in reg_spaces}
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if not only_match(args.only, cid):
            continue
        if cid in done:
            res = done[cid]
            cells.append(res)
        else:
            if arm == BASE_ARM:
                res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                               shuffled=shuffled, n_slots=args.n_slots)
            else:
                res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device,
                               shuffled=shuffled, extra_factory=factory_of[(arm, seed)],
                               feats_label=arm, n_slots=args.n_slots)
            cells.append(res)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} "
                  f"(maj {res['majority_rate_test']:.4f}) {res['runtime_s']}s "
                  f"total {time.time() - t0:.0f}s", flush=True)
        if shuffled:
            # both legs, fresh or resumed alike (a halt a Ctrl-C disarms is not a halt)
            riders[sp] = rider_check(cells, sp)

    expected = None if args.only else 30
    pooled = cells + p3_cells
    per_space = {}
    for sp in reg_spaces:
        r2_ok = bool(riders[sp] and riders[sp].get("pass"))
        sp_cells = [c for c in cells if c["space"] == sp]
        sp_pooled = [c for c in pooled if c["space"] == sp]
        sp_lin = relabel_committed_linear_a(p3_cells, sp)
        d_rows = margins(sp_cells, "fplus_b", expected_clusters=expected, base_feats=TWIN_ARM) if r2_ok else []
        mt = margins(sp_cells, "fplus_b", expected_clusters=expected, base_feats="fplus") if r2_ok else []
        mnr = margins(sp_cells, TWIN_ARM, expected_clusters=expected, base_feats="fplus") if r2_ok else []
        mf = margins(sp_pooled, "fplus", expected_clusters=expected, base_feats="a") if r2_ok else []
        mfx = margins(sp_cells + sp_lin, "fplus", expected_clusters=expected, base_feats=LIN_BASE) if r2_ok else []
        mc = margins(sp_pooled, "fplus", expected_clusters=expected, base_feats="c") if r2_ok else []
        reader = reader_validity(sp_cells, mf, mfx, sp)
        gate = gate_row(d_rows, sp)
        per_space[sp] = {
            "offsets": list(offsets_for_space(sp)),
            "n_cells": len([c for c in sp_cells if not c["shuffled"]]),
            "rider": riders[sp],
            "reader_valid": reader,
            "gate": {"space": sp, "offset": GATE_OFFSET, "capacity": GATE_CAPACITY,
                     "row": gate, "fires": bool(reader["ok"] and gate_fires(gate)),
                     "label_if_alone": (LABEL_READER_INVALID if not reader["ok"] else None),
                     "rule": ("three-leg READER-INVALID precondition, then D CI95 lower > 0, all "
                              "three seeds positive, point >= +0.005")},
            "d_fplus_b_vs_fplus_r": d_rows,
            "mt_fplus_b_vs_fplus": mt,
            "mn_r_fplus_r_vs_fplus": mnr,
            "mf_fplus_vs_a": mf,
            "mfx_fplus_vs_committed_linear_a": mfx,
            "mc_fplus_vs_c": mc,
        }

    def _git() -> tuple[str, list[str]]:
        """HEAD plus a -dirty flag over TRACKED files only; the porcelain
        list is recorded beside it."""
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
        "registered": ("OQ-18 COARSE-LABEL FULL-FREE RE-TEST REGISTRATION (docs/BLUEPRINT.md, "
                       "2026-09-06, before any registered cell ran; critic round applied before "
                       f"the freeze commit); consequence rules act on {args.parent_finding}"),
        "harvest": args.harvest,
        "tag": args.space_tag,
        "levels": list(LEVELS),
        "spaces_registered": list(reg_spaces),
        "n_cells": len([c for c in cells if not c["shuffled"]]),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),  # FRESH-STATE PIN: 0 on a registered run
        "offsets_of_space": {sp: list(offsets_for_space(sp)) for sp in reg_spaces},
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "per_space": per_space,
        "standardization": {
            "block": "hz = clip(h_a, train lo, train hi) then (x - train mu) / max(train sd, sd_floor)",
            "moments_sha256": moments["sha256"],
            "moments_sha_matches_committed_oq17": (None if committed_sha is None else True),
            "n_train_rows": moments["n_train_rows"],
            "n_train_positions": moments["n_train_positions"],
            "sd_floor": moments["sd_floor"],
            "sd_min": float(moments["sd"].min()), "sd_median": float(np.median(moments["sd"])),
            "sd_max": float(moments["sd"].max()),
            "abs_lo_hi_max": float(max(np.abs(moments["lo"]).max(), np.abs(moments["hi"]).max())),
        },
        "twin": {"arm": TWIN_ARM, "seed_base": TWIN_SEED_BASE, "construction": CONSTRUCTION,
                 "perm_sha256": perm_shas, "geometry": geometry},
        "phase3_state": str(args.phase3_state),
        "phase3_payload_margins_reproduced": True,
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "instrument_sha256": _sha(Path(__file__)),
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
            "torch_version": torch.__version__,
            "device": args.device,
            "determinism_note": ("CUDA probe training uses atomics; per-cell results are "
                                 "evidenced by the recorded state file, not rerun-exactness"),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(json.dumps({sp: {"reader_valid": per_space[sp]["reader_valid"]["ok"],
                           "gate_fires": per_space[sp]["gate"]["fires"],
                           "gate": per_space[sp]["gate"]["row"],
                           "rider": per_space[sp]["rider"],
                           "n_d_rows": len(per_space[sp]["d_fplus_b_vs_fplus_r"])}
                      for sp in reg_spaces}, indent=1))


if __name__ == "__main__":
    main()

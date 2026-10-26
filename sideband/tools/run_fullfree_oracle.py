#!/usr/bin/env python3
"""DRAFT STATUS (2026-10-01): UNFROZEN. Committed as a DRAFT beside
docs/OQ19_ORACLE_CEILING_DRAFT.md. The registration block this docstring
names was never inserted into docs/BLUEPRINT.md, no freeze commit exists and
no replay or registered cell has run; the text below describes the draft as
it stood on 2026-09-07.

SKIPPED (dated note 2026-10-11): the operator's decision is to skip OQ-19.
No freeze commit exists and none is planned; DRAFT_UNFROZEN stays True and
main() keeps refusing to run, as tests/test_fullfree_oracle.py pins.

OQ-19 ORACLE-INTERMEDIATE CEILING probe (plan of record item 2, 2026-09-06;
registered in docs/BLUEPRINT.md "OQ-19 ORACLE-INTERMEDIATE CEILING
REGISTRATION" BEFORE any registered cell ran; two pre-run critic rounds
applied before the freeze commit; NON-CRITERION for F-15 / F-17 — it
measures the ceiling every sketch competes for and prices P9, never a
finding's label).

QUESTION. Every S1 / S3 telemetry source is a LOSSY VIEW of an intermediate
activation of the same forward pass (S1: the MLP intermediate at the four
tapped down_proj layers, a deterministic function of the MLP INPUT; S3: the
router's expert choice, a deterministic function of the ROUTER INPUT),
while the full free baseline holds that forward pass's final state h_a
exactly (F-23). Does the TRUE activation the sketch is a function of — the
post-attention-norm output at the registered layers, replayed from the
logged generations by sideband.real.oracle_replay with a per-position
fidelity record — carry future-concept information beyond the full free
baseline at the registered reader?

ARMS (block ORDER identical across arms; the committed fplus / fplus_b /
fplus_r / (a) cells of the SAME harvest are paired, never re-trained):
  fplus_o      = (a) ++ TOK ++ hz ++ oz      oz = the oracle block (L x d),
                 clipped to the TRAIN support and z-scored with TRAIN moments
                 exactly as hz (run_fullfree.train_moments on the replayed
                 array; its sha recorded)
  fplus_o_r    = (a) ++ TOK ++ hz ++ oz read from the prompt-level-deranged
                 row (run_fullfree_twin.derangement_by_prompt, seed 1000 +
                 train seed — the OQ-18 twin rows; perm shas asserted equal
                 to the committed twin payload's); equal dims
  fplus_o_lead = (a) ++ TOK ++ hz ++ oz read at anchor min(a + 2, length - 1)
                 — the forward that CONSUMED the offset-2 label — a POSITIVE
                 CONTROL, leaky by construction, never a result: it certifies
                 the registered reader is not BLIND to the oracle block (not
                 that it is sensitive to a weak signal in it); at the gate
                 offset only
  S3 only: fplus_b4 = (a) ++ TOK ++ hz ++ the expert ids of the FOUR
                 registered router layers only (the like-for-like sketch of
                 what the oracle covers; the committed fplus_b spans all 16),
           fplus_r4 = its deranged twin
CELLS per harvest, per space (L1 then L3; L2 omitted and said so): the
LEAK RIDER first — shuffled fplus_o at off2 / linear / seed 0 against the
COMMITTED shuffled fplus of the same space + 0.01 (a (row, anchor) leak in
the block assembly; the rider is BLIND to a misaligned replay — alignment
is certified by the per-position h_a and drawn-token comparisons and the
load-time lengths / prompt_idx equality) — then at off2 every arm x mlp256
x 3 seeds, and at each further registered offset the arms minus the lead
control: S1 L1 {2,3}, S1 L3 {2,3}, S3 L1 {2}, S3 L3 {2,3}. Totals: S1 32
cells (30 trained + 2 shuffled); S3 44 (42 + 2).

READOUTS per space (pinned):
  D_o  = acc(fplus_o)   - acc(fplus_o_r)   equal dims — THE gate readout
  Mt_o = acc(fplus_o)   - acc(fplus)       vs the committed fplus; beside D_o
  Mn_o = acc(fplus_o_r) - acc(fplus)       the oracle twin's own gain
  Lead = acc(fplus_o_lead) - acc(fplus_o)  the positive control (precondition leg)
  D_sk = acc(fplus_b)   - acc(fplus_r)     the committed sketch on the same rows
         (at L1 off3, where no fplus_r cell was committed, fplus_n is the base
         and the row is labeled so)
  D_4  = acc(fplus_b4)  - acc(fplus_r4)    S3 only: the like-for-like sketch
  SF   = D_sk / D_o (S1) or D_4 / D_o (S3) at the gate cell — the SURVIVAL
         FRACTION with a cluster-bootstrap CI (ratio of seed-summed per-
         prompt success deltas over the 30 test prompts; n_boot 2000, seed
         0, the house draw convention) — written as UNDEFINED where D_o does
         not fire; a point above 1 reads "the sketch above the raw block at
         this reader" and earns READER-LIMITED only with CI lower > 1; a
         point below 0 "the sketch's own delta is negative"
  Mf_x = acc(fplus_o, mlp256) - acc(committed linear (a))   the collapse leg
PRECONDITIONS per (harvest, space): ORACLE fidelity (every side-file's
drawn-token match rate >= 0.99, minimum per-layer mean sketch-set overlap
>= 0.95, h_a relative max-abs median <= 0.01 and p99 <= 0.05; exact-match
rates are REPORTED, never gating), else ORACLE-INVALID and the tool refuses
to train; READER validity, four legs: every new mlp256 probe at the gate
cell holds test_acc >= majority - 0.001; Mf_x's CI95 upper >= 0; the Lead
row fires the Phase-3 triple rule with point >= +0.02; all rows complete.
GATE per space per harvest: off2 / mlp256 D_o under the Phase-3 triple rule.
LABELS per (source, space) from both harvests: ORACLE-INVALID / READER-
INVALID / HEADROOM (fires both) / SPLIT / NO-HEADROOM (every D_o row's CI95
upper < +0.005 on both harvests) / NOT-SHOWN; horizons OFF3-*; the
READER-LIMITED reading is recorded when the committed like-for-like sketch
D fires the triple rule on BOTH harvests while the oracle reads NO-HEADROOM
(a sketch is a function of the oracle, so that pattern says the reader
failed to recover from the raw block what it recovers from the sketch —
never that the sketch fire is an artifact).

RAM: the S1 primary oracle array is ~14 GB; the tool refuses to start unless
available memory exceeds the array plus 8 GB (psutil, a dev dependency), so
runs go one process at a time and never beside another probe run.

Run (GPU box):
    python tools/run_fullfree_oracle.py --out results/real/fullfree_oracle_s1.json
    python tools/run_fullfree_oracle.py --conclude-from \
        results/real/fullfree_oracle_s1.json results/real/fullfree_oracle_s1_r.json
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
from sideband.probes import HarvestData  # noqa: E402
from sideband.real.oracle_replay import OracleData, REGISTERED_LAYERS  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_posthoc_topic import load_phase3_cells  # noqa: E402
from run_probes import (REAL, MATERIALITY, SlotsAnchorBlock,  # noqa: E402
                        bind_spaces_to_harvest, build_spaces, cell_id,
                        feature_blocks, margins, normalize_clusters,
                        parse_state, run_cell, space_names, state_header)
from run_fullfree import (R2_BAND, READER_FLOOR_TOL, HiddenZBlock,  # noqa: E402
                          TokAnchorBlock, _same_path, _sha, train_moments)
from run_fullfree_twin import (TWIN_SEED_BASE, CONSTRUCTION,  # noqa: E402
                               derangement_by_prompt, load_fullfree_cells,
                               twin_geometry)
from run_fullfree_coarse import (LIN_BASE, relabel_committed_linear_a,  # noqa: E402
                                 only_match)

SEEDS = (0, 1, 2)
ARMS_O = ("fplus_o", "fplus_o_r", "fplus_o_lead")
ARMS_4 = ("fplus_b4", "fplus_r4")
TWIN_ARM = "fplus_o_r"
LEAD_ARM = "fplus_o_lead"
LEAD = 2                 # the forward that consumed the offset-2 label
LEAD_MIN = 0.02          # the positive control must clear this at the gate cell
GATE_OFFSET = 2
GATE_CAPACITY = "mlp256"
GATE_PAIR = "fplus_o-fplus_o_r"
PAIR_MTO = "fplus_o-fplus"
PAIR_MNO = "fplus_o_r-fplus"
PAIR_LEAD = "fplus_o_lead-fplus_o"
PAIR_DSK = "fplus_b-fplus_r"
PAIR_DSK_N = "fplus_b-fplus_n"
PAIR_D4 = "fplus_b4-fplus_r4"
PAIR_MFX = f"fplus_o-{LIN_BASE}"
LEVELS = ("L1", "L3")
OFFSETS_OF_SPACE = {"L1_concept_k16": (2, 3), "L3_concept_groups_v1": (2, 3),
                    "L1_olmoe_k16": (2,), "L3_olmoe_groups_v1": (2, 3)}
SKETCH_LAYERS_OF_TAG = {"concept": None, "olmoe": (3, 7, 11, 15)}
FID_TOKEN_MIN = 0.99
FID_OVERLAP_MIN = 0.95
FID_H_REL_MEDIAN_MAX = 0.01
FID_H_REL_P99_MAX = 0.05
RAM_MARGIN_BYTES = 8 * 1024 ** 3
LABEL_HEADROOM = "HEADROOM"
LABEL_NO_HEADROOM = "NO-HEADROOM"
LABEL_NOT_SHOWN = "NOT-SHOWN"
LABEL_SPLIT = "SPLIT"
LABEL_READER_INVALID = "READER-INVALID"
LABEL_ORACLE_INVALID = "ORACLE-INVALID"
LABEL_INCOMPLETE = "INCOMPLETE"
REGISTERED_OUTS = ("fullfree_oracle_s1.json", "fullfree_oracle_s1_r.json",
                   "fullfree_oracle_s3.json", "fullfree_oracle_s3_r.json")
# DRAFT STATUS (2026-10-01): while True, main() refuses to run anything and every payload stamp is prefixed
# "UNFROZEN DRAFT". Flip it to False only in the freeze commit that inserts the registration block into
# docs/BLUEPRINT.md (docs/OQ19_ORACLE_CEILING_DRAFT.md lists what that commit owes). The tests import the
# module's pure-numpy layer and never call main().
DRAFT_UNFROZEN = True
HARVESTS_OF_TAG = {"concept": ("results/real/harvest_shadow", "results/real/harvest_shadow_r"),
                   "olmoe": ("results/real/harvest_moe", "results/real/harvest_moe_r")}
OUT_STEM_OF_TAG = {"concept": "fullfree_oracle_s1", "olmoe": "fullfree_oracle_s3"}
PREFIX_OF_TAG = {"concept": "shadow", "olmoe": "moe"}
N_TRAINED_OF_TAG = {"concept": 30, "olmoe": 42}
PARENT_FINDING_OF_TAG = {"concept": "F-15", "olmoe": "F-17"}
ALPHABET_KEY_OF_TAG = {"concept": "n_slots", "olmoe": "n_experts"}
COMMITTED_OF_HARVEST = {
    "results/real/harvest_shadow": {"oracle_dir": "results/real/oracle_shadow",
                                    "fullfree": "fullfree_s1.json", "twin": "fullfree_s1_twin.json",
                                    "coarse": "fullfree_coarse_s1.json"},
    "results/real/harvest_shadow_r": {"oracle_dir": "results/real/oracle_shadow_r",
                                      "fullfree": "fullfree_s1_r.json", "twin": "fullfree_s1_r_twin.json",
                                      "coarse": "fullfree_coarse_s1_r.json"},
    "results/real/harvest_moe": {"oracle_dir": "results/real/oracle_moe",
                                 "fullfree": "fullfree_s3.json", "twin": "fullfree_s3_twin.json",
                                 "coarse": "fullfree_coarse_s3.json"},
    "results/real/harvest_moe_r": {"oracle_dir": "results/real/oracle_moe_r",
                                   "fullfree": "fullfree_s3_r.json", "twin": "fullfree_s3_r_twin.json",
                                   "coarse": "fullfree_coarse_s3_r.json"},
}


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
        raise SystemExit(f"{space}: registered offsets must start at {GATE_OFFSET}")
    return offs


def registered_spaces(tag: str) -> tuple[str, ...]:
    names = space_names(tag)
    return tuple(names[lv] for lv in LEVELS)


def arms_for_tag(tag: str) -> tuple[str, ...]:
    return ARMS_O + (ARMS_4 if SKETCH_LAYERS_OF_TAG.get(tag) else ())


def arms_at_offset(arms: tuple[str, ...], offset: int) -> tuple[str, ...]:
    """The lead control runs at the gate offset only."""
    return arms if offset == GATE_OFFSET else tuple(a for a in arms if a != LEAD_ARM)


def committed_of_harvest(harvest: str) -> dict:
    for h, d in COMMITTED_OF_HARVEST.items():
        if _same_path(harvest, h):
            return d
    raise SystemExit(f"harvest {harvest!r} is not one of the four registered harvests")


# ---------------------------------------------------------------------------
# Blocks and factories
# ---------------------------------------------------------------------------

class OtherRowZBlock:
    """The clipped / z-scored block of pi(row) at anchor mod length[pi(row)]
    — the corrected-twin read of a dense block."""

    def __init__(self, arr: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 lengths: np.ndarray, perm: np.ndarray, moments: dict):
        other = perm[rows]
        self.other_anchors = anchors % lengths[other]
        self.inner = HiddenZBlock(arr, other, self.other_anchors, moments)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.inner.batch(idx)


class LeadZBlock:
    """The positive control: the same dense block read at min(anchor + LEAD,
    length - 1) of the SAME row — a state that has consumed the offset-2
    label (or, at the row's last anchors, the state that produced its
    distribution). Leaky by construction; never a result."""

    def __init__(self, arr: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 lengths: np.ndarray, moments: dict, lead: int = LEAD):
        self.lead_anchors = np.minimum(anchors + int(lead), lengths[rows] - 1)
        if np.any(self.lead_anchors < anchors):
            raise SystemExit("lead anchors fall behind their anchors — inconsistent lengths")
        self.inner = HiddenZBlock(arr, rows, self.lead_anchors, moments)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.inner.batch(idx)


class SubsetSlotsBlock:
    """The registered (b) slots block restricted to a subset of the tapped
    layers (a strided view; nothing copied)."""

    def __init__(self, slots: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 layer_idx: tuple[int, ...], n_slots: int):
        self.layer_idx = tuple(int(i) for i in layer_idx)
        if len(set(self.layer_idx)) != len(self.layer_idx) or any(i < 0 or i >= slots.shape[2] for i in self.layer_idx):
            raise SystemExit(f"layer subset {list(self.layer_idx)} is not a subset of the {slots.shape[2]} tapped layers")
        self.inner = SlotsAnchorBlock(slots[:, :, list(self.layer_idx), :], rows, anchors, n_slots)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.inner.batch(idx)


class OtherRowSubsetSlotsBlock:
    def __init__(self, slots: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 lengths: np.ndarray, perm: np.ndarray, layer_idx: tuple[int, ...], n_slots: int):
        other = perm[rows]
        self.other_anchors = anchors % lengths[other]
        self.inner = SubsetSlotsBlock(slots, other, self.other_anchors, layer_idx, n_slots)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.inner.batch(idx)


def make_factories(top_ids: np.ndarray, hidden: np.ndarray, oracle_flat: np.ndarray,
                   slots: np.ndarray, lengths: np.ndarray, n_slots: int,
                   moments_h: dict, moments_o: dict, perms: dict[int, np.ndarray],
                   sketch_layers: tuple[int, ...] | None, n_bins: int = FREETOK_BINS) -> dict:
    """{(arm, seed): factory}: TOK, hz, then the arm's own block last."""

    def free_extras(rows, anchors):
        return [TokAnchorBlock(top_ids, rows, anchors, n_bins),
                HiddenZBlock(hidden, rows, anchors, moments_h)]

    def fplus_o(rows, anchors):
        return free_extras(rows, anchors) + [HiddenZBlock(oracle_flat, rows, anchors, moments_o)]

    def fplus_o_lead(rows, anchors):
        return free_extras(rows, anchors) + [LeadZBlock(oracle_flat, rows, anchors, lengths, moments_o)]

    def twin_o(perm):
        def fplus_o_r(rows, anchors):
            return free_extras(rows, anchors) + [
                OtherRowZBlock(oracle_flat, rows, anchors, lengths, perm, moments_o)]
        return fplus_o_r

    def fplus_b4(rows, anchors):
        return free_extras(rows, anchors) + [SubsetSlotsBlock(slots, rows, anchors, sketch_layers, n_slots)]

    def twin_4(perm):
        def fplus_r4(rows, anchors):
            return free_extras(rows, anchors) + [
                OtherRowSubsetSlotsBlock(slots, rows, anchors, lengths, perm, sketch_layers, n_slots)]
        return fplus_r4

    out = {}
    for seed in SEEDS:
        if seed not in perms:
            raise SystemExit(f"no derangement for train seed {seed}")
        out[("fplus_o", seed)] = fplus_o
        out[("fplus_o_r", seed)] = twin_o(perms[seed])
        out[("fplus_o_lead", seed)] = fplus_o_lead
        if sketch_layers:
            out[("fplus_b4", seed)] = fplus_b4
            out[("fplus_r4", seed)] = twin_4(perms[seed])
    return out


# ---------------------------------------------------------------------------
# Grid, committed cells, rider, preconditions, readouts, labels
# ---------------------------------------------------------------------------

def build_grid(spaces: tuple[str, ...] | list[str], arms: tuple[str, ...],
               offsets_of: dict | None = None) -> list[tuple]:
    grid: list[tuple] = []
    for sp in spaces:
        offs = offsets_for_space(sp, offsets_of)
        grid.append((sp, GATE_OFFSET, "fplus_o", "linear", 0, True))
        for off in offs:
            for seed in SEEDS:
                for arm in arms_at_offset(arms, off):
                    grid.append((sp, off, arm, GATE_CAPACITY, seed, False))
    if len({cell_id(*c) for c in grid}) != len(grid):
        raise SystemExit("duplicate cell ids in the grid")
    return grid


def committed_cells_for(space: str, fullfree_cells: list[dict], twin_cells: list[dict],
                        coarse_cells: list[dict]) -> list[dict]:
    """The committed cells paired at a space: OQ-17 + its twin diagnostic at
    L1, OQ-18 at L3 — only cells of that space, features fplus / fplus_b /
    fplus_n / fplus_r / a (and their shuffled rider cells)."""
    lv = space.split("_")[0]
    src = (fullfree_cells + twin_cells) if lv == "L1" else coarse_cells
    keep = {"fplus", "fplus_b", "fplus_n", "fplus_r", "a"}
    out = [c for c in src if c.get("space") == space and c.get("features") in keep]
    if not any(c["features"] == "fplus" and not c["shuffled"] for c in out):
        raise SystemExit(f"no committed fplus cells at {space} — the pairing base is missing")
    return out


def check_grid_against_committed(grid: list[tuple], committed_ids: set[str]) -> None:
    dup = [cell_id(*c) for c in grid if cell_id(*c) in committed_ids]
    if dup:
        raise SystemExit(f"grid cell ids collide with committed cells: {dup[:3]} ...")


def rider_check(cells: list[dict], committed: list[dict], space: str, band: float = R2_BAND) -> dict | None:
    so = next((c for c in cells if c["shuffled"] and c["space"] == space and c["features"] == "fplus_o"
               and c["offset"] == GATE_OFFSET and c["capacity"] == "linear"), None)
    if so is None:
        return None
    sf = next((c for c in committed if c["shuffled"] and c["space"] == space and c["features"] == "fplus"
               and c["offset"] == GATE_OFFSET and c["capacity"] == "linear"), None)
    if sf is None:
        raise SystemExit(f"{space}: the committed shuffled fplus reference is missing — the rider cannot run")
    out = {"band": band, "space": space, "committed_shuffled_fplus": sf["test_acc"],
           "shuffled_fplus_o": so["test_acc"]}
    out["pass"] = bool(so["test_acc"] <= sf["test_acc"] + band)
    if not out["pass"]:
        raise SystemExit(f"LEAK RIDER FAILED at {space}: shuffled fplus_o {so['test_acc']:.4f} > committed "
                         f"shuffled fplus {sf['test_acc']:.4f} + {band} — a leak in the oracle block; halting")
    return out


def fires_triple(row: dict | None, pair: str) -> bool:
    if row is None or row.get("pair") != pair:
        return False
    if row.get("n_seeds") != len(SEEDS) or row.get("n_clusters") != 30:
        return False
    return bool(row["ci95"][0] > 0
                and all(v > 0 for v in row["per_seed_margin"].values())
                and row["margin"] >= MATERIALITY)


def reader_validity(cells: list[dict], mfx_rows: list[dict], lead_rows: list[dict], space: str,
                    arms: tuple[str, ...], tol: float = READER_FLOOR_TOL) -> dict:
    """Four legs at the gate cell: the new probes on the floor; Mf_x; the
    LEAD positive control firing the triple rule with point >= LEAD_MIN (a
    reader that never opens the oracle block cannot pass); all rows present."""
    gate_cells = [c for c in cells if not c["shuffled"] and c["space"] == space
                  and c["offset"] == GATE_OFFSET and c["capacity"] == GATE_CAPACITY
                  and c["features"] in arms]
    gaps = {c["cell"]: c["test_acc"] - c["majority_rate_test"] for c in gate_cells}

    def _gate(rows, pair):
        return next((m for m in rows if m["space"] == space and m["offset"] == GATE_OFFSET
                     and m["capacity"] == GATE_CAPACITY and m.get("pair") == pair), None)

    mfx = _gate(mfx_rows, PAIR_MFX)
    lead = _gate(lead_rows, PAIR_LEAD)
    complete = len(gate_cells) == len(arms) * len(SEEDS) and mfx is not None and lead is not None
    floor_ok = complete and all(g >= -tol for g in gaps.values())
    mfx_ok = complete and mfx["ci95"][1] >= 0
    lead_ok = complete and fires_triple(lead, PAIR_LEAD) and lead["margin"] >= LEAD_MIN
    best_epochs = {arm: sorted(int(c["best_epoch"]) for c in gate_cells
                               if c["features"] == arm and c.get("best_epoch") is not None)
                   for arm in arms}
    return {"ok": bool(complete and floor_ok and mfx_ok and lead_ok), "complete": bool(complete),
            "floor_ok": bool(floor_ok), "mfx_ok": bool(mfx_ok), "lead_ok": bool(lead_ok),
            "n_gate_probes": len(gate_cells),
            "min_acc_minus_floor": (min(gaps.values()) if gaps else None),
            "mfx_gate_margin": (mfx["margin"] if mfx else None),
            "mfx_gate_ci_upper": (mfx["ci95"][1] if mfx else None),
            "lead_gate_margin": (lead["margin"] if lead else None),
            "lead_gate_ci": (lead["ci95"] if lead else None),
            "lead_min": LEAD_MIN,
            "acc_fplus_o_minus_floor_per_seed": sorted(round(c["test_acc"] - c["majority_rate_test"], 6)
                                                       for c in gate_cells if c["features"] == "fplus_o"),
            "best_epochs_gate_cell": best_epochs, "tol": tol,
            "rule": (f"all {len(arms) * len(SEEDS)} new gate-cell probes test_acc >= majority_rate_test - tol "
                     "AND Mf_x(fplus_o mlp256 vs the COMMITTED linear (a)) CI95 upper >= 0 AND the LEAD "
                     f"control (fplus_o_lead - fplus_o) fires the triple rule with point >= {LEAD_MIN}; "
                     "else READER-INVALID")}


def oracle_validity(od: OracleData | None = None, token_min: float | None = None,
                    overlap_min: float | None = None, h_rel_median: float | None = None,
                    h_rel_p99: float | None = None, exact_min: float | None = None) -> dict:
    """The ORACLE fidelity precondition from the side-file metas (recomputed
    from the arrays at load): the drawn-token match, the mean overlap and
    the h_a relative-difference legs gate; exact match is reported."""
    if od is not None:
        token_min, overlap_min, h_rel_median, h_rel_p99, exact_min = (
            od.token_match_rate_min, od.slot_overlap_mean_min, od.h_relmax_median_max,
            od.h_relmax_p99_max, od.slot_exact_rate_min)
    ok = bool(None not in (token_min, overlap_min, h_rel_median, h_rel_p99)
              and token_min >= FID_TOKEN_MIN and overlap_min >= FID_OVERLAP_MIN
              and h_rel_median <= FID_H_REL_MEDIAN_MAX and h_rel_p99 <= FID_H_REL_P99_MAX)
    return {"ok": ok, "token_match_rate_min": token_min, "slot_overlap_mean_min": overlap_min,
            "h_relmax_median_max": h_rel_median, "h_relmax_p99_max": h_rel_p99,
            "slot_exact_match_rate_min_reported": exact_min,
            "floors": {"token_match_rate_min": FID_TOKEN_MIN, "slot_overlap_mean_min": FID_OVERLAP_MIN,
                       "h_relmax_median_max": FID_H_REL_MEDIAN_MAX, "h_relmax_p99_max": FID_H_REL_P99_MAX},
            "rule": ("every side-file's drawn-token match rate >= 0.99 AND minimum per-layer MEAN sketch-set "
                     "overlap >= 0.95 AND h_a relative max-abs median <= 0.01 AND p99 <= 0.05 (exact-match "
                     "rates reported, never gating); else ORACLE-INVALID (no cell trains)")}


def gate_fires(row: dict | None) -> bool:
    return fires_triple(row, GATE_PAIR)


def gate_row(rows: list[dict], space: str, offset: int = GATE_OFFSET,
             capacity: str = GATE_CAPACITY) -> dict | None:
    return next((m for m in rows if m["space"] == space
                 and m["offset"] == offset and m["capacity"] == capacity), None)


def source_label(primary: dict | None, replication: dict | None,
                 primary_rows: list[dict] | None = None,
                 replication_rows: list[dict] | None = None,
                 reader_ok: tuple[bool, bool] = (True, True),
                 oracle_ok: tuple[bool, bool] = (True, True)) -> str:
    if not (oracle_ok[0] and oracle_ok[1]):
        return LABEL_ORACLE_INVALID
    if primary is None or replication is None:
        return LABEL_INCOMPLETE
    if not (reader_ok[0] and reader_ok[1]):
        return LABEL_READER_INVALID
    fp, fr = gate_fires(primary), gate_fires(replication)
    if fp and fr:
        return LABEL_HEADROOM
    if fp != fr:
        return LABEL_SPLIT
    rows = list(primary_rows or []) + list(replication_rows or [])
    if rows and all(m["ci95"][1] < MATERIALITY for m in rows):
        return LABEL_NO_HEADROOM
    return LABEL_NOT_SHOWN


def horizon_note(primary_row: dict | None, replication_row: dict | None, offset: int) -> str | None:
    k = f"OFF{int(offset)}"
    if primary_row is None and replication_row is None:
        return None
    if primary_row is None or replication_row is None:
        return f"{k}-INCOMPLETE"
    fp, fr = gate_fires(primary_row), gate_fires(replication_row)
    if fp and fr:
        return f"{k}-HEADROOM"
    if not fp and not fr:
        if primary_row["ci95"][1] < MATERIALITY and replication_row["ci95"][1] < MATERIALITY:
            return f"{k}-NO-HEADROOM"
        return f"{k}-NOT-SHOWN"
    return f"{k}-SPLIT"


def survival_fraction(cells: list[dict], space: str, top_sk: str, base_sk: str,
                      top_o: str = "fplus_o", base_o: str = TWIN_ARM, offset: int = GATE_OFFSET,
                      capacity: str = GATE_CAPACITY, n_boot: int = 2000, seed: int = 0) -> dict | None:
    """SF = (sum over prompts and train seeds of the sketch's paired success
    delta) / (the same for the oracle) on the same 30 test prompts; a cluster
    bootstrap over prompts (own generator seed 0, the house draw convention
    of one (n_boot, n) index matrix) gives the CI. None when a pairing is
    incomplete (no house helper admits signed per-cluster numerators, hence
    the local loop). The caller writes it only where the oracle's gate fires."""
    cells = [normalize_clusters(dict(c)) for c in cells if not c.get("shuffled")]
    by_id = {c["cell"]: c for c in cells}

    def deltas(top: str, base: str):
        per = {}
        for s in SEEDS:
            t = by_id.get(cell_id(space, offset, top, capacity, s))
            b = by_id.get(cell_id(space, offset, base, capacity, s))
            if t is None or b is None:
                return None
            for p in t["_clusters"]:
                if p not in b["_clusters"] or t["_clusters"][p][1] != b["_clusters"][p][1]:
                    return None
                per[p] = per.get(p, 0.0) + (t["_clusters"][p][0] - b["_clusters"][p][0])
        return per

    dsk, do = deltas(top_sk, base_sk), deltas(top_o, base_o)
    if dsk is None or do is None or set(dsk) != set(do) or len(dsk) != 30:
        return None
    prompts = sorted(dsk)
    a = np.array([dsk[p] for p in prompts], np.float64)
    b = np.array([do[p] for p in prompts], np.float64)
    if b.sum() <= 0:
        return {"defined": False, "reason": "oracle delta sum <= 0", "n_clusters": len(prompts)}
    point = float(a.sum() / b.sum())
    n = len(prompts)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    num = a[idx].sum(axis=1)
    den = b[idx].sum(axis=1)
    ok = den > 0
    boots = np.full(n_boot, np.nan)
    boots[ok] = num[ok] / den[ok]
    lo, hi = (float(np.percentile(boots[ok], 2.5)), float(np.percentile(boots[ok], 97.5))) if ok.sum() else (None, None)
    if point > 1:
        reading = ("READER-LIMITED (CI lower > 1): the sketch beats the raw block at this reader"
                   if (lo is not None and lo > 1) else "point above 1: the sketch above the raw block at this reader")
    elif point < 0:
        reading = "the sketch's own delta is negative"
    else:
        reading = "fraction of the oracle headroom recovered"
    return {"defined": True, "point": point, "ci95": [lo, hi], "n_boot": n_boot,
            "n_boot_undefined": int((~ok).sum()), "n_clusters": n,
            "pair": f"({top_sk}-{base_sk})/({top_o}-{base_o})", "reading": reading}


def expected_d_rows(space: str) -> int:
    return len(offsets_for_space(space))


def _rows_of(payload: dict, space: str, key: str) -> list[dict]:
    return list(((payload.get("per_space") or {}).get(space) or {}).get(key) or [])


def _check_payload(p: dict, role: str, verify_files: bool = True) -> str:
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
        raise SystemExit(f"{role} payload's harvest {p.get('harvest')!r} is not the registered {role} harvest {want!r}")
    args = (p.get("provenance") or {}).get("args") or {}
    out_name = Path(str(args.get("out", ""))).name
    want_out = OUT_STEM_OF_TAG[tag] + ("" if role == "primary" else "_r") + ".json"
    if out_name != want_out:
        raise SystemExit(f"{role} payload was written to {out_name!r}, not the registered {want_out!r}")
    if p.get("n_cells") != N_TRAINED_OF_TAG[tag]:
        raise SystemExit(f"{role} payload carries {p.get('n_cells')} trained cells, expected {N_TRAINED_OF_TAG[tag]}")
    if not isinstance(p.get("resumed_cells"), int):
        raise SystemExit(f"{role} payload does not record resumed_cells")
    if tuple(int(x) for x in (p.get("oracle") or {}).get("layers", ())) != REGISTERED_LAYERS[PREFIX_OF_TAG[tag]]:
        raise SystemExit(f"{role} payload's oracle layers are not the registered ones")
    for sp in spaces:
        ps = (p.get("per_space") or {}).get(sp)
        if not ps:
            raise SystemExit(f"{role} payload carries no block for {sp} — INCOMPLETE")
        if not (ps.get("rider") or {}).get("pass"):
            raise SystemExit(f"{role} payload's leak rider did not pass at {sp} — no label may issue")
        if tuple((p.get("offsets_of_space") or {}).get(sp, ())) != offsets_for_space(sp):
            raise SystemExit(f"{role} payload's offsets at {sp} are not the registered {list(offsets_for_space(sp))}")
        d_rows = ps.get("d_o_fplus_o_vs_fplus_o_r") or []
        if len(d_rows) != expected_d_rows(sp):
            raise SystemExit(f"{role} payload carries {len(d_rows)} D_o rows at {sp}, expected {expected_d_rows(sp)}")
        for m in d_rows:
            if m.get("pair") != GATE_PAIR or m.get("n_seeds") != len(SEEDS) or m.get("n_clusters") != 30:
                raise SystemExit(f"{role} payload's D_o row at {sp} off{m.get('offset')} is not structurally complete")
    if verify_files:
        prov = p["provenance"]
        committed = committed_of_harvest(str(p["harvest"]))
        for k in ("fullfree", "twin", "coarse"):
            pl, st = REAL / committed[k], REAL / (committed[k] + ".state.jsonl")
            if not (pl.exists() and st.exists()):
                raise SystemExit(f"{role} payload's committed {k} payload / state file are missing")
            if _sha(pl) != (prov.get("committed_payload_sha256") or {}).get(k) or \
                    _sha(st) != (prov.get("committed_state_sha256") or {}).get(k):
                raise SystemExit(f"{role} payload's committed {k} payload / state file changed on disk since the run")
        od = REAL.parent.parent / committed["oracle_dir"]
        metas = (p.get("oracle") or {}).get("side_file_meta_sha256") or {}
        npzs = (p.get("oracle") or {}).get("side_file_sha256") or {}
        if not metas:
            raise SystemExit(f"{role} payload records no oracle meta shas")
        for name, sha in metas.items():
            f = od / name
            if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != sha:
                raise SystemExit(f"{role} payload's committed oracle meta {name} is missing or changed on disk")
            m = json.loads(f.read_text())
            if npzs.get(m["npz_file"]) != m["npz_sha256"]:
                raise SystemExit(f"{role} payload's oracle npz sha for {m['npz_file']} disagrees with its committed meta")
            npz = od / m["npz_file"]
            if npz.exists() and hashlib.sha256(npz.read_bytes()).hexdigest() != m["npz_sha256"]:
                raise SystemExit(f"{role} payload's oracle side-file {m['npz_file']} changed on disk")
    return tag


def conclude(primary_payload: dict, replication_payload: dict, verify_files: bool = True) -> dict:
    tag = _check_payload(primary_payload, "primary", verify_files)
    if _check_payload(replication_payload, "replication", verify_files) != tag:
        raise SystemExit("the two payloads are from different sources")
    if primary_payload["provenance"]["harvest_npz_sha256"] == replication_payload["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two payloads bind the SAME harvest — not a primary/replication pair")
    sk_pair = PAIR_D4 if SKETCH_LAYERS_OF_TAG.get(tag) else PAIR_DSK
    sk_key = "d_4_fplus_b4_vs_fplus_r4" if SKETCH_LAYERS_OF_TAG.get(tag) else "d_sk_fplus_b_vs_fplus_r"
    out_spaces = {}
    for sp in registered_spaces(tag):
        p_rows = _rows_of(primary_payload, sp, "d_o_fplus_o_vs_fplus_o_r")
        r_rows = _rows_of(replication_payload, sp, "d_o_fplus_o_vs_fplus_o_r")
        gp, gr = gate_row(p_rows, sp), gate_row(r_rows, sp)
        rv = (bool(primary_payload["per_space"][sp]["reader_valid"]["ok"]),
              bool(replication_payload["per_space"][sp]["reader_valid"]["ok"]))
        ov = (bool(primary_payload["oracle"]["validity"]["ok"]), bool(replication_payload["oracle"]["validity"]["ok"]))
        label = source_label(gp, gr, p_rows, r_rows, reader_ok=rv, oracle_ok=ov)
        skp = gate_row(_rows_of(primary_payload, sp, sk_key), sp)
        skr = gate_row(_rows_of(replication_payload, sp, sk_key), sp)
        sk_fires = (fires_triple(skp, sk_pair), fires_triple(skr, sk_pair))
        full_p = gate_row(_rows_of(primary_payload, sp, "d_sk_fplus_b_vs_fplus_r"), sp)
        full_r = gate_row(_rows_of(replication_payload, sp, "d_sk_fplus_b_vs_fplus_r"), sp)
        full_fires = (fires_triple(full_p, PAIR_DSK), fires_triple(full_r, PAIR_DSK))
        horizons = {f"off{o}": horizon_note(gate_row(p_rows, sp, offset=o), gate_row(r_rows, sp, offset=o), o)
                    for o in offsets_for_space(sp) if o != GATE_OFFSET}
        out_spaces[sp] = {
            "label": label,
            "oracle_valid": {"primary": ov[0], "replication": ov[1]},
            "reader_valid": {"primary": rv[0], "replication": rv[1]},
            "lead_control": {"primary": primary_payload["per_space"][sp]["reader_valid"].get("lead_gate_margin"),
                             "replication": replication_payload["per_space"][sp]["reader_valid"].get("lead_gate_margin")},
            "gate_primary": gp, "gate_replication": gr,
            "gate_fires": {"primary": gate_fires(gp), "replication": gate_fires(gr)},
            "mt_o_at_gate": {"primary": gate_row(_rows_of(primary_payload, sp, "mt_o_fplus_o_vs_fplus"), sp),
                             "replication": gate_row(_rows_of(replication_payload, sp, "mt_o_fplus_o_vs_fplus"), sp)},
            "mn_o_at_gate": {"primary": gate_row(_rows_of(primary_payload, sp, "mn_o_fplus_o_r_vs_fplus"), sp),
                             "replication": gate_row(_rows_of(replication_payload, sp, "mn_o_fplus_o_r_vs_fplus"), sp)},
            "sketch_d_at_gate": {"pair": sk_pair, "primary": skp, "replication": skr,
                                 "fires": {"primary": sk_fires[0], "replication": sk_fires[1]}},
            # S3 only: the committed SIXTEEN-layer sketch beside the four-layer
            # oracle is reported, never a READER-LIMITED or closure input
            "full_sketch_d_at_gate": {"pair": PAIR_DSK, "primary": full_p, "replication": full_r,
                                      "fires": {"primary": full_fires[0], "replication": full_fires[1]},
                                      "like_for_like": sk_pair == PAIR_DSK},
            "survival_fraction": {"primary": primary_payload["per_space"][sp].get("survival_fraction"),
                                  "replication": replication_payload["per_space"][sp].get("survival_fraction")},
            # a sketch is a function of the oracle: the like-for-like sketch
            # firing on BOTH harvests beside an oracle null says the reader
            # failed to recover from the raw block what it recovers from the
            # sketch (second critic round, B2) — never that the fire is an artifact
            "reader_limited_reading": bool(label == LABEL_NO_HEADROOM and sk_fires[0] and sk_fires[1]),
            "all_d_o_ci_uppers_below_floor": bool(p_rows and r_rows and all(
                m["ci95"][1] < MATERIALITY for m in list(p_rows) + list(r_rows))),
            "horizons": horizons,
        }
    return {"tag": tag, "spaces": out_spaces, "materiality_floor": MATERIALITY,
            "resumed_cells": {"primary": primary_payload.get("resumed_cells"),
                              "replication": replication_payload.get("resumed_cells")},
            "rule": ("OQ-19 registration: per space, ORACLE-INVALID / READER-INVALID preconditions (four reader "
                     "legs incl. the lead control), then gate off2/mlp256 D_o = acc(fplus_o) - acc(fplus_o_r) "
                     "under the Phase-3 triple rule on both harvests; NO-HEADROOM needs every D_o CI95 upper < "
                     "+0.005 on both, else NOT-SHOWN; the survival fraction is defined only where D_o fires; "
                     "READER-LIMITED when the like-for-like committed sketch fires on both harvests under NO-HEADROOM")}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--fidelity", default="results/real/harvest_fidelity_rider.json")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/fullfree_oracle_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="comma-separated substring filter on cell ids (smoke)")
    ap.add_argument("--resume", action="store_true",
                    help="continue a crashed REGISTERED run from its own state file (resumed_cells is recorded)")
    ap.add_argument("--space-tag", default="concept")
    ap.add_argument("--n-slots", type=int, default=512, help="must equal the harvest's alphabet (asserted)")
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    ap.add_argument("--parent-finding", default=None, help="derived from --space-tag (F-15 / F-17) unless given")
    ap.add_argument("--conclude-from", nargs=2, metavar=("PRIMARY", "REPLICATION"), default=None)
    return ap


def ram_check(needed_bytes: int) -> dict:
    """Refuse to start unless available memory covers the oracle array plus
    the margin (psutil, a dev dependency; the S1 primary array is ~14 GB on
    a 32 GB box)."""
    try:
        import psutil
    except ImportError as e:  # pragma: no cover - environment
        raise SystemExit("psutil is required for the RAM guard: pip install -e '.[dev]'") from e
    avail = int(psutil.virtual_memory().available)
    ok = avail >= needed_bytes + RAM_MARGIN_BYTES
    return {"available_bytes": avail, "needed_bytes": int(needed_bytes), "margin_bytes": RAM_MARGIN_BYTES, "ok": ok}


def main() -> None:
    args = build_parser().parse_args()
    if DRAFT_UNFROZEN:
        raise SystemExit("OQ-19 is an UNFROZEN DRAFT (docs/OQ19_ORACLE_CEILING_DRAFT.md): no registration block "
                         "exists in docs/BLUEPRINT.md and no freeze commit exists; refusing to run. Set "
                         "DRAFT_UNFROZEN = False in the freeze commit, never before.")
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
    if args.space_tag not in HARVESTS_OF_TAG:
        raise SystemExit(f"unregistered --space-tag {args.space_tag!r}")
    if registered and OUT_STEM_OF_TAG[args.space_tag] not in out_path.name:
        raise SystemExit(f"registered out {out_path.name} does not belong to --space-tag {args.space_tag}")
    state_path = Path(args.out + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a crashed run")
    parent_finding = args.parent_finding or PARENT_FINDING_OF_TAG[args.space_tag]
    if registered and parent_finding != PARENT_FINDING_OF_TAG[args.space_tag]:
        raise SystemExit(f"--parent-finding {parent_finding} is not {PARENT_FINDING_OF_TAG[args.space_tag]} for this source")
    committed = committed_of_harvest(args.harvest)
    if registered:
        # launch-time primary / replication pairing (a swap would be caught only at conclude otherwise)
        want_h = HARVESTS_OF_TAG[args.space_tag][1 if out_path.name.endswith("_r.json") else 0]
        if not _same_path(args.harvest, want_h):
            raise SystemExit(f"registered out {out_path.name} must run on {want_h}, not {args.harvest}")
    prefix = PREFIX_OF_TAG[args.space_tag]
    layers = REGISTERED_LAYERS[prefix]

    data = HarvestData(args.harvest)
    split_names = data.row_split()
    alphabet = int(data.ref_meta[ALPHABET_KEY_OF_TAG[args.space_tag]])
    if args.n_slots != alphabet:
        raise SystemExit(f"--n-slots {args.n_slots} is not the harvest's alphabet {alphabet}")
    bind_spaces_to_harvest(data.ref_meta, {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)
    fid = Path(args.fidelity)
    if not fid.exists():
        raise SystemExit("R1 harvest-fidelity rider missing (registered gate)")
    rider_payload = json.loads(fid.read_text())
    if rider_payload.get("verdict") != "PASS" or rider_payload.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 rider is not a PASS for this harvest version — quarantined")

    needed = int(data.n_rows) * int(data.tokens.shape[1]) * len(layers) * int(data.array("hidden").shape[2]) * 2
    ram = ram_check(needed)
    if not ram["ok"]:
        raise SystemExit(f"RAM: {ram['available_bytes'] / 1e9:.1f} GB available, need the {needed / 1e9:.1f} GB oracle "
                         f"array plus {RAM_MARGIN_BYTES / 1e9:.0f} GB — run one oracle process at a time, never beside "
                         "another probe run")

    od = OracleData(committed["oracle_dir"], data, layers)
    if od.d != int(data.array("hidden").shape[2]):
        raise SystemExit(f"oracle width {od.d} is not the model's hidden width {data.array('hidden').shape[2]}")
    ov = oracle_validity(od)
    if not ov["ok"]:
        raise SystemExit(f"ORACLE-INVALID: {json.dumps(ov)} — no cell trains on an unfaithful replay")
    print(f"[oracle] {od.oracle_flat.shape} float16 from {od.dir}; token match min {od.token_match_rate_min:.4f}, "
          f"overlap mean min {od.slot_overlap_mean_min:.4f}, exact min {od.slot_exact_rate_min:.4f}, "
          f"h relmax median max {od.h_relmax_median_max:.2e}", flush=True)

    p3_cells = load_phase3_cells(Path(args.phase3_state), Path(args.phase3_payload), data.npz_shas)
    ff_payload = json.loads((REAL / committed["fullfree"]).read_text())
    tw_payload = json.loads((REAL / committed["twin"]).read_text())
    co_payload = json.loads((REAL / committed["coarse"]).read_text())
    for name, pl in (("fullfree", ff_payload), ("twin", tw_payload), ("coarse", co_payload)):
        if pl.get("partial") or pl["provenance"]["harvest_npz_sha256"] != data.npz_shas:
            raise SystemExit(f"committed {name} payload is partial or binds a different harvest")
    ff_cells = load_fullfree_cells(REAL / (committed["fullfree"] + ".state.jsonl"), data.npz_shas)
    tw_cells = load_fullfree_cells(REAL / (committed["twin"] + ".state.jsonl"), data.npz_shas)
    co_cells = load_fullfree_cells(REAL / (committed["coarse"] + ".state.jsonl"), data.npz_shas)
    if ff_payload["standardization"]["moments_sha256"] != co_payload["standardization"]["moments_sha256"]:
        raise SystemExit("the committed OQ-17 and OQ-18 payloads disagree on the hz moments sha")

    spaces = build_spaces(data, tag=args.space_tag, buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512, groups_path=args.groups)
    reg_spaces = registered_spaces(args.space_tag)
    arms = arms_for_tag(args.space_tag)
    sketch_layers = SKETCH_LAYERS_OF_TAG.get(args.space_tag)
    committed_by_space = {sp: committed_cells_for(sp, ff_cells, tw_cells, co_cells) for sp in reg_spaces}
    p3_ids = {c["cell"] for c in p3_cells}
    for sp in reg_spaces:
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built")
        for seed in SEEDS:
            if cell_id(sp, GATE_OFFSET, "a", "linear", seed) not in p3_ids:
                raise SystemExit(f"committed Phase-3 (a) linear cell missing at {sp} off2 s{seed}")
    grid = build_grid(reg_spaces, arms)
    check_grid_against_committed(grid, p3_ids | {c["cell"] for c in ff_cells + tw_cells + co_cells})

    reproduced = {}
    for sp in reg_spaces:
        cm = committed_by_space[sp]
        row = gate_row(margins(cm, "fplus_b", expected_clusters=30, base_feats="fplus_r"), sp)
        want = (gate_row(tw_payload["d_r_fplus_b_vs_fplus_r"], sp) if sp.startswith("L1")
                else gate_row(co_payload["per_space"][sp]["d_fplus_b_vs_fplus_r"], sp))
        if row is None or want is None or abs(row["margin"] - want["margin"]) > 1e-12 \
                or max(abs(a - b) for a, b in zip(row["ci95"], want["ci95"])) > 1e-12:
            raise SystemExit(f"committed sketch gate row at {sp} does not reproduce from the state files")
        reproduced[sp] = row

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    moments_h = train_moments(hidden, data.lengths, split_names)
    if moments_h["sha256"] != ff_payload["standardization"]["moments_sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's — refusing")
    t_m = time.time()
    moments_o = train_moments(od.oracle_flat, data.lengths, split_names)
    print(f"[moments] hz {moments_h['sha256'][:12]} == committed; oz {moments_o['sha256'][:12]} "
          f"({time.time() - t_m:.0f}s)", flush=True)
    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    perm_shas = {str(seed): hashlib.sha256(perms[seed].astype(np.int64).tobytes()).hexdigest() for seed in SEEDS}
    if perm_shas != {str(k): v for k, v in tw_payload["twin"]["perm_sha256"].items()}:
        raise SystemExit("the derangements differ from the committed twin payload's — not the same other-prompt rows")
    all_offsets = sorted({o for sp in reg_spaces for o in offsets_for_space(sp)})
    geometry = {str(seed): {f"off{o}": twin_geometry(data.lengths, perms[seed], o, data.tokens.shape[1], data.prompt_idx)
                            for o in all_offsets} for seed in SEEDS}
    for seed, g in geometry.items():
        for o, gg in g.items():
            if gg["corrected_twin_same_prompt_frac"] != 0.0:
                raise SystemExit(f"twin reads its own prompt at seed {seed} {o} — refusing")
    factory_of = make_factories(top_ids, hidden, od.oracle_flat, slots, data.lengths, args.n_slots,
                                moments_h, moments_o, perms, sketch_layers)
    probe_rows = np.zeros(1, np.int64)
    a_dim = sum(b.dim for b in feature_blocks(data, "a", probe_rows, probe_rows, n_slots=args.n_slots))
    dims_recorded = {arm: [b.dim for b in factory_of[(arm, SEEDS[0])](probe_rows, probe_rows)] for arm in arms}
    dims_total = {arm: int(a_dim + sum(dims_recorded[arm])) for arm in arms}
    if not (dims_total["fplus_o"] == dims_total["fplus_o_r"] == dims_total["fplus_o_lead"]):
        raise SystemExit("oracle arms are not equal-dims — refusing")
    if sketch_layers and dims_total["fplus_b4"] != dims_total["fplus_r4"]:
        raise SystemExit("four-layer sketch twin arms are not equal-dims — refusing")

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
            res = run_cell(data, spaces, sp, off, "a", cap, seed, args.device, shuffled=shuffled,
                           extra_factory=factory_of[(arm, seed)], feats_label=arm, n_slots=args.n_slots)
            cells.append(res)
            with state_path.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} (maj {res['majority_rate_test']:.4f}) "
                  f"{res['runtime_s']}s total {time.time() - t0:.0f}s", flush=True)
        if shuffled:
            riders[sp] = rider_check(cells, committed_by_space[sp], sp)

    expected = None if args.only else 30
    per_space = {}
    for sp in reg_spaces:
        r2_ok = bool(riders[sp] and riders[sp].get("pass"))
        sp_cells = [c for c in cells if c["space"] == sp]
        cm = committed_by_space[sp]
        pooled = sp_cells + cm
        sp_lin = relabel_committed_linear_a(p3_cells, sp)
        d_o = margins(sp_cells, "fplus_o", expected_clusters=expected, base_feats=TWIN_ARM) if r2_ok else []
        mt_o = margins(pooled, "fplus_o", expected_clusters=expected, base_feats="fplus") if r2_ok else []
        mn_o = margins(pooled, TWIN_ARM, expected_clusters=expected, base_feats="fplus") if r2_ok else []
        lead = margins(sp_cells, LEAD_ARM, expected_clusters=expected, base_feats="fplus_o") if r2_ok else []
        mfx = margins(sp_cells + sp_lin, "fplus_o", expected_clusters=expected, base_feats=LIN_BASE) if r2_ok else []
        d_sk = margins(cm, "fplus_b", expected_clusters=expected, base_feats="fplus_r") if r2_ok else []
        d_sk_n = margins(cm, "fplus_b", expected_clusters=expected, base_feats="fplus_n") if r2_ok else []
        d_4 = margins(sp_cells, "fplus_b4", expected_clusters=expected, base_feats="fplus_r4") if (r2_ok and sketch_layers) else []
        mt_4 = margins(pooled, "fplus_b4", expected_clusters=expected, base_feats="fplus") if (r2_ok and sketch_layers) else []
        reader = reader_validity(sp_cells, mfx, lead, sp, arms)
        gate = gate_row(d_o, sp)
        fires = bool(reader["ok"] and gate_fires(gate))
        if args.only or not r2_ok:
            sf = None
        elif not fires:
            sf = {"defined": False, "reason": "the oracle gate did not fire (or the reader is invalid) — no ratio"}
        else:
            sf = (survival_fraction(pooled, sp, "fplus_b4", "fplus_r4") if sketch_layers
                  else survival_fraction(pooled, sp, "fplus_b", "fplus_r"))
        per_space[sp] = {
            "offsets": list(offsets_for_space(sp)),
            "n_cells": len([c for c in sp_cells if not c["shuffled"]]),
            "rider": riders[sp],
            "reader_valid": reader,
            "gate": {"space": sp, "offset": GATE_OFFSET, "capacity": GATE_CAPACITY, "row": gate, "fires": fires},
            "d_o_fplus_o_vs_fplus_o_r": d_o,
            "mt_o_fplus_o_vs_fplus": mt_o,
            "mn_o_fplus_o_r_vs_fplus": mn_o,
            "lead_fplus_o_lead_vs_fplus_o": lead,
            "mfx_fplus_o_vs_committed_linear_a": mfx,
            "d_sk_fplus_b_vs_fplus_r": d_sk,
            "d_sk_n_fplus_b_vs_fplus_n": d_sk_n,
            "d_4_fplus_b4_vs_fplus_r4": d_4,
            "mt_4_fplus_b4_vs_fplus": mt_4,
            "survival_fraction": sf,
            "committed_sketch_gate_row_reproduced": reproduced[sp],
        }

    def _git() -> tuple[str, list[str]]:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                               text=True, timeout=10)
            lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
            return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
        except Exception:
            return "unknown", []

    git_commit, git_porcelain = _git()
    import torch
    payload = {
        "registered": (("UNFROZEN DRAFT (2026-10-01; no registration block exists in docs/BLUEPRINT.md) -- "
                        if DRAFT_UNFROZEN else "")
                       + "OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION (docs/BLUEPRINT.md; before any "
                       f"registered cell ran; critic rounds applied before the freeze commit); parent {parent_finding}"),
        "harvest": args.harvest, "tag": args.space_tag, "levels": list(LEVELS),
        "spaces_registered": list(reg_spaces), "arms": list(arms),
        "n_cells": len([c for c in cells if not c["shuffled"]]),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),
        "offsets_of_space": {sp: list(offsets_for_space(sp)) for sp in reg_spaces},
        "cells": [{k: v for k, v in c.items() if k != "_clusters"} for c in cells],
        "per_space": per_space,
        "oracle": {"dir": str(od.dir), "layers": list(layers), "layer_names": od.layer_names, "d": od.d,
                   "dims": int(od.oracle_flat.shape[2]), "side_file_sha256": od.npz_shas,
                   "side_file_meta_sha256": od.meta_shas,
                   "fidelity_per_seed": {str(m["seed"]): m["fidelity"] for m in od.metas},
                   "versions_per_seed": {str(m["seed"]): {k: m.get(k) for k in
                                                          ("torch_version", "transformers_version",
                                                           "bitsandbytes_version", "attn_implementation", "gpu")}
                                         for m in od.metas},
                   "validity": ov, "sketch_layers_like_for_like": list(sketch_layers) if sketch_layers else None,
                   "lead_control": {"arm": LEAD_ARM, "lead": LEAD, "min_margin": LEAD_MIN}},
        "ram_at_launch": ram,
        "standardization": {"hz_moments_sha256": moments_h["sha256"], "oz_moments_sha256": moments_o["sha256"],
                            "oz_sd_min": float(moments_o["sd"].min()), "oz_sd_median": float(np.median(moments_o["sd"])),
                            "oz_sd_max": float(moments_o["sd"].max()),
                            "oz_abs_lo_hi_max": float(max(np.abs(moments_o["lo"]).max(), np.abs(moments_o["hi"]).max()))},
        "twin": {"arm": TWIN_ARM, "seed_base": TWIN_SEED_BASE, "construction": CONSTRUCTION,
                 "perm_sha256": perm_shas, "perm_sha256_equals_committed_twin": True, "geometry": geometry},
        "committed": {k: committed[k] for k in ("fullfree", "twin", "coarse")},
        "provenance": {"git_commit": git_commit, "git_status_tracked": git_porcelain,
                       "instrument_sha256": _sha(Path(__file__)), "args": redact_args(vars(args)),
                       "harvest_npz_sha256": data.npz_shas,
                       "committed_payload_sha256": {k: _sha(REAL / committed[k]) for k in ("fullfree", "twin", "coarse")},
                       "committed_state_sha256": {k: _sha(REAL / (committed[k] + ".state.jsonl"))
                                                  for k in ("fullfree", "twin", "coarse")},
                       "feature_dims_recorded": dims_recorded, "arm_dims_total": dims_total,
                       "phase3_state_sha256": _sha(Path(args.phase3_state)),
                       "torch_version": torch.__version__, "device": args.device},
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(json.dumps({sp: {"reader_valid": per_space[sp]["reader_valid"]["ok"],
                           "lead_margin": per_space[sp]["reader_valid"]["lead_gate_margin"],
                           "gate_fires": per_space[sp]["gate"]["fires"], "gate": per_space[sp]["gate"]["row"],
                           "rider": per_space[sp]["rider"], "survival_fraction": per_space[sp]["survival_fraction"]}
                      for sp in reg_spaces}, indent=1))


if __name__ == "__main__":
    main()

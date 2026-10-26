#!/usr/bin/env python
"""tools/run_reader_lens.py — READER-AND-LENS RE-TEST AT S3 (docs/BLUEPRINT.md,
"READER-AND-LENS RE-TEST AT S3 REGISTRATION", 2026-10-05; pre-run).

Two halves on the committed S3 harvests through the FROZEN OQ-18 chain
(tools/run_fullfree_coarse_amended.py and its parents, imported by bare name,
asserted at import, never edited):
  STAGE lens      the F-25 grid at the BALANCED L3 lens
                  (results/real/concept_groups_olmoe_balanced_v1.json) under the
                  registered reader R0, plus the PROXY cells (fresh linear (a)
                  and (c) at off2) that re-read F-17's L3 headline at that lens;
  STAGE readers   readers RN (hz rescaled) and RT (two-tower) at the gate cell
                  off2 / mlp256 of L1, the lopsided L3 and the balanced L3, plus
                  the three R0 linear (a) cells at the balanced lens (the Mf_x
                  reference there, re-trainings of STAGE lens's proxy (a) cells);
  STAGE readers_long  reader RL (60 epochs, lr 1e-3), the pinned conditional;
  STAGE s1        the S1 L1 gate cell under the readers the block names.
Readers (sideband.probes.train_probe, the registered trainer, for R0 / RN / RL;
a two-tower trainer in this file for RT that reproduces train_probe bit-exactly
when no slots tower exists — a CI test):
  R0  mlp256, 30 epochs, lr 3e-3 (the registered reader).
  RN  the HZ block alone rescaled by c_HZ = sqrt(m_SLOTS / m_HZ), m = the mean
      squared per-anchor norm over the cell's TRAIN anchors (m_SLOTS from the
      ALIGNED slots block at the same anchors, so c_HZ is the same for the
      three arms of a cell); A, TOK and the slots blocks unscaled; then R0's
      trainer. Under AdamW a rescale by c of one family equals init x c and
      learning rate x c for that family's first-layer weights (recorded).
  RT  tower A Linear(d_A, 256) -> ReLU over A ++ TOK ++ HZ; tower B
      Linear(d_slots, 64) -> ReLU over the slots block where present; head
      Linear(256 + 64, n_classes); parameters built A, head, B so the no-B
      model IS mlp256 with the identical seeded initialisation.
  RL  mlp256, 60 epochs, lr 1e-3.
Estimand, pairing, bootstrap, rider, precondition and labels: F-25's, imported
(margins, reader_validity, source_label, horizon_note, rider_check_amended,
run_cell_diag). CPU only: CUDA is hidden at import and torch is limited to
--threads (six registered). Evidence files are written with LF newlines. The
state file holds one row per (reader, cell) under a header that records HEAD
at launch; --conclude-from PRIMARY REPLICATION verifies each payload (out name,
role-bound harvest, registry, row set, HEAD, rider recomputed from the shuffled
rows' histograms) and recomputes every margin, precondition, label and licence
from the state files, refusing a mismatch.

Usage:
  python tools/run_reader_lens.py --stage lens --harvest results/real/harvest_moe --out results/real/lens_s3.json
  python tools/run_reader_lens.py --stage lens --harvest results/real/harvest_moe_r --out results/real/lens_s3_r.json
  python tools/run_reader_lens.py --stage readers --harvest results/real/harvest_moe --out results/real/readers_s3.json \
      --lens-payloads results/real/lens_s3.json results/real/lens_s3_r.json
  python tools/run_reader_lens.py --conclude-from results/real/lens_s3.json results/real/lens_s3_r.json
  python tools/run_reader_lens.py --conclude-from results/real/readers_s3.json results/real/readers_s3_r.json \
      [--long results/real/readers_long_s3.json results/real/readers_long_s3_r.json] [--s1 results/real/readers_s1.json results/real/readers_s1_r.json]
The per-harvest companion files (fidelity rider, Phase-3 state and payload, label
spaces, n_slots, space tag) are filled from HARVEST_FILES when not given and
refused when they disagree with it on a registered out.
Smoke (refused under results/): --only <substring> or --smoke-cell READER|space|offset|arm|capacity|seed.
"""

from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""          # the GPU carries the operator's job; CPU only, by registration

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import HarvestData, anchor_table, labels_for, train_probe  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402
import run_fullfree_coarse_amended as am  # noqa: E402  (the FROZEN amended instrument; its import asserts its parent chain)
from run_fullfree_coarse import (SEEDS, ARMS, TWIN_ARM, BASE_ARM, GATE_OFFSET, GATE_CAPACITY,  # noqa: E402
                                 LIN_BASE, make_factories, relabel_committed_linear_a,
                                 reader_validity, gate_row, gate_fires, source_label, horizon_note, fires_triple,
                                 committed_moments_sha, LABEL_SURVIVES, LABEL_ABSORBED, LABEL_NOT_SHOWN, LABEL_SPLIT,
                                 LABEL_READER_INVALID, LABEL_INCOMPLETE)
from run_fullfree import train_moments, _sha  # noqa: E402
from run_fullfree_twin import derangement_by_prompt, twin_geometry, TWIN_SEED_BASE, CONSTRUCTION  # noqa: E402
from run_oq18_rider_diag import run_cell_diag, normalize_hist  # noqa: E402
from run_posthoc_topic import load_phase3_cells  # noqa: E402
from run_probes import (REAL, MATERIALITY, SlotsAnchorBlock, bind_spaces_to_harvest, build_spaces, cell_id,  # noqa: E402
                        feature_blocks, margins, state_header)

AMENDED_INSTRUMENT = Path(__file__).resolve().parent / "run_fullfree_coarse_amended.py"
AMENDED_INSTRUMENT_SHA256 = "aafd3ae849984092ea81ce7ff5cd47f1b18e089e95cd960d86630162b5ad8612"
REGISTERED = ("READER-AND-LENS RE-TEST AT S3 REGISTRATION (docs/BLUEPRINT.md, 2026-10-05; pre-run; the frozen "
              "OQ-18 chain imported, never edited; CPU only)")
READERS = {
    "R0": {"kind": "plain", "capacity": "mlp256", "epochs": 30, "lr": 3e-3, "what": "the registered reader"},
    "RN": {"kind": "hz_rescaled", "capacity": "mlp256", "epochs": 30, "lr": 3e-3,
           "what": "the hz block alone rescaled to the aligned slots block's mean squared norm over the train anchors "
                   "(c_HZ = sqrt(m_SLOTS / m_HZ)); A, TOK and the slots blocks unscaled"},
    "RT": {"kind": "two_tower", "capacity": "mlp256", "epochs": 30, "lr": 3e-3, "tower_a": 256, "tower_b": 64,
           "what": "tower A over A ++ TOK ++ HZ, tower B over the slots block, head over the concatenation"},
    "RL": {"kind": "plain", "capacity": "mlp256", "epochs": 60, "lr": 1e-3, "what": "the registered model at twice the epochs and a third of the lr"},
}
STAGE_READERS = {"lens": ("R0",), "readers": ("RN", "RT"), "readers_long": ("RL",), "s1": None}   # s1: --readers
SPACE_L1 = {"olmoe": "L1_olmoe_k16", "concept": "L1_concept_k16"}
SPACE_L3_LOP = "L3_olmoe_groups_v1"
SPACE_L3_BAL = "L3_olmoe_balanced_v1"
LENS_OFFSETS = (2, 3, 4)
PROXY_CAP = "linear"
REGISTERED_OUTS = {"lens": ("lens_s3.json", "lens_s3_r.json"), "readers": ("readers_s3.json", "readers_s3_r.json"),
                   "readers_long": ("readers_long_s3.json", "readers_long_s3_r.json"),
                   "s1": ("readers_s1.json", "readers_s1_r.json")}
HARVEST_OF_OUT = {"lens_s3.json": "harvest_moe", "lens_s3_r.json": "harvest_moe_r",
                  "readers_s3.json": "harvest_moe", "readers_s3_r.json": "harvest_moe_r",
                  "readers_long_s3.json": "harvest_moe", "readers_long_s3_r.json": "harvest_moe_r",
                  "readers_s1.json": "harvest_shadow", "readers_s1_r.json": "harvest_shadow_r"}
ROLE_OF_OUT = {n: ("replication" if n.endswith("_r.json") else "primary") for n in HARVEST_OF_OUT}
# the per-harvest companion files of the registered runs (F-24 / F-25's), filled when not given, refused when they disagree
HARVEST_FILES = {
    "harvest_moe": {"space_tag": "olmoe", "n_slots": 64, "fidelity": "harvest_fidelity_rider_olmoe.json",
                    "phase3_state": "probes_s3.json.state.jsonl", "phase3_payload": "probes_s3.json",
                    "buckets16": "buckets_olmoe_k16.json", "glue16": "glue_olmoe_k16.json",
                    "buckets512": "buckets_olmoe_k512.json", "glue512": "glue_olmoe_k512.json", "groups": "concept_groups_olmoe_v1.json"},
    "harvest_moe_r": {"space_tag": "olmoe", "n_slots": 64, "fidelity": "harvest_fidelity_rider_olmoe_r.json",
                      "phase3_state": "probes_s3_replication.json.state.jsonl", "phase3_payload": "probes_s3_replication.json",
                      "buckets16": "buckets_olmoe_k16.json", "glue16": "glue_olmoe_k16.json",
                      "buckets512": "buckets_olmoe_k512.json", "glue512": "glue_olmoe_k512.json", "groups": "concept_groups_olmoe_v1.json"},
    "harvest_shadow": {"space_tag": "concept", "n_slots": 512, "fidelity": "harvest_fidelity_rider.json",
                       "phase3_state": "probes_s1.json.state.jsonl", "phase3_payload": "probes_s1.json",
                       "buckets16": "buckets_k16.json", "glue16": "glue_k16.json",
                       "buckets512": "buckets_k512.json", "glue512": "glue_k512.json", "groups": "concept_groups_v1.json"},
    "harvest_shadow_r": {"space_tag": "concept", "n_slots": 512, "fidelity": "harvest_fidelity_rider_r.json",
                         "phase3_state": "probes_s1_replication.json.state.jsonl", "phase3_payload": "probes_s1_replication.json",
                         "buckets16": "buckets_k16.json", "glue16": "glue_k16.json",
                         "buckets512": "buckets_k512.json", "glue512": "glue_k512.json", "groups": "concept_groups_v1.json"},
}
F17_L3_MARGIN = {"primary": 0.0721, "replication": 0.0730}       # F-17's recorded lopsided L3 proxy margin at off2 (FINDINGS.md)
THREADS = 6
EXPECTED_CLUSTERS = 30
SCALE_BATCH = 16384
K2_STANDS, K2_REOPENED, K2_ISOLATED, K2_UNSETTLED, K2_INCOMPLETE = ("K-2-NOT-OVERTURNED-AT-S3", "K-2-REOPENED-AT", "K-2-ISOLATED",
                                                                     "K-2-UNSETTLED", "K-2-INCOMPLETE")
LENS_SURVIVES, LENS_COLLAPSE, LENS_SPLIT, LENS_NOT_SHOWN = "LENS-SURVIVES", "LENS-COLLAPSE", "LENS-SPLIT", "LENS-NOT-SHOWN"
GROWTH_LOST, GROWTH_SURVIVES, GROWTH_UNSETTLED, GROWTH_SPLIT = ("L3-GROWTH-LOST", "L3-GROWTH-SURVIVES", "L3-GROWTH-NOT-SETTLED",
                                                                "L3-GROWTH-SPLIT")
N_BOOT = 2000                                                  # the registered bootstrap draws; refused otherwise on a registered out
PAYLOAD_ROOT = REAL                                            # where a verified payload must live (tests override)
LABEL_STRONGER = "SURVIVES-STRONGER"
REOPEN_SPACES = (SPACE_L1["olmoe"], SPACE_L3_BAL)              # the lopsided lens never decides a reopen


def assert_frozen_chain() -> dict:
    """The amended instrument on disk is the one this file was frozen against,
    and its own parent assertion holds."""
    am.assert_frozen_instrument()
    got = _sha(AMENDED_INSTRUMENT)
    if got != AMENDED_INSTRUMENT_SHA256:
        raise SystemExit(f"the frozen amended instrument hashes to {got[:12]}, not {AMENDED_INSTRUMENT_SHA256[:12]} — refusing")
    return {"amended_sha256": got, "coarse_sha256": am.FROZEN_INSTRUMENT_SHA256}


# ---------------------------------------------------------------------------
# Blocks and readers
# ---------------------------------------------------------------------------

class ScaledBlock:
    """A block multiplied by one float32 constant (RN's hz rescale)."""

    def __init__(self, inner, scale: float):
        self.inner, self.scale = inner, np.float32(scale)

    @property
    def dim(self) -> int:
        return self.inner.dim

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return (self.inner.batch(idx) * self.scale).astype(np.float32, copy=False)


def family_of_blocks(blocks_a: list, extras: list) -> list[tuple[str, list]]:
    """The four families in the registered block order: A (the (a) blocks), then
    each extra block by its class: TOK, HZ, SLOTS (aligned or twin)."""
    fams: list[tuple[str, list]] = [("A", list(blocks_a))]
    for b in extras:
        name = type(b).__name__
        if "Tok" in name:
            fams.append(("TOK", [b]))
        elif "Hidden" in name:
            fams.append(("HZ", [b]))
        elif "Slots" in name:
            fams.append(("SLOTS", [b]))
        else:
            raise SystemExit(f"unknown extra block class {name}")
    return fams


def mean_squared_norms(named_blocks: list[tuple[str, list]], train_idx: np.ndarray, batch: int = SCALE_BATCH) -> dict[str, float]:
    """m_F = mean over the train anchors of ||x_F||^2, one streaming pass in float64."""
    sums = {name: 0.0 for name, _ in named_blocks}
    n = 0
    for s in range(0, len(train_idx), batch):
        sl = train_idx[s: s + batch]
        n += len(sl)
        for name, blocks in named_blocks:
            x = np.concatenate([b.batch(sl) for b in blocks], axis=1).astype(np.float64)
            sums[name] += float((x * x).sum())
    return {name: sums[name] / n for name, _ in named_blocks}


def hz_rescale(fams: list[tuple[str, list]], ref_slots, train_idx: np.ndarray) -> tuple[list, dict]:
    """RN: scale the HZ block by c_HZ = sqrt(m_SLOTS / m_HZ), m_SLOTS from the
    ALIGNED slots block at the same anchors; every other block unchanged. A cell
    without an HZ block is returned unscaled (identical to R0)."""
    hz = [b for name, blocks in fams if name == "HZ" for b in blocks]
    if not hz:
        return [b for _, blocks in fams for b in blocks], {"c_hz": None, "note": "no hz block: the cell is R0's"}
    m = mean_squared_norms([("HZ", hz), ("SLOTS_ALIGNED", [ref_slots])], train_idx)
    c = float(np.sqrt(m["SLOTS_ALIGNED"] / m["HZ"])) if m["HZ"] > 0 else 1.0
    out = []
    for name, blocks in fams:
        out += [ScaledBlock(b, c) for b in blocks] if name == "HZ" else list(blocks)
    return out, {"c_hz": c, "m_hz": m["HZ"], "m_slots_aligned": m["SLOTS_ALIGNED"],
                 "adam_equivalence": "under AdamW the rescale equals init x c_hz and lr x c_hz on the hz first-layer weights"}


def train_two_tower(tower_a: list, tower_b: list, labels: np.ndarray, split_of_anchor: np.ndarray, n_classes: int,
                    seed: int, device: str = "cpu", epochs: int = 30, batch_size: int = 4096, lr: float = 3e-3,
                    width_a: int = 256, width_b: int = 64, eval_batch: int = 16384) -> dict:
    """train_probe's loop (same generator use, batch order, selection and
    evaluation) with the two-tower model; with no tower-B blocks the model is
    mlp256 with the identical seeded init and the run is bit-exact with
    train_probe (asserted by tests/test_reader_lens.py)."""
    import torch

    y = labels.astype(np.int64)
    tr = split_of_anchor == "train"
    va = split_of_anchor == "val"
    te = split_of_anchor == "test"
    g = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    dev = torch.device(device if (device == "cpu" or torch.cuda.is_available()) else "cpu")
    d_a = sum(b.dim for b in tower_a)
    d_b = sum(b.dim for b in tower_b)
    has_b = d_b > 0

    class TwoTower(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.a = torch.nn.Linear(d_a, width_a)
            self.head = torch.nn.Linear(width_a + (width_b if has_b else 0), n_classes)
            self.b = torch.nn.Linear(d_b, width_b) if has_b else None

        def forward(self, xa, xb=None):
            h = torch.relu(self.a(xa))
            if self.b is not None:
                h = torch.cat([h, torch.relu(self.b(xb))], dim=1)
            return self.head(h)

    model = TwoTower().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    yt = torch.from_numpy(y)
    idx_tr = np.nonzero(tr)[0]

    def assemble(idx):
        xa = torch.from_numpy(np.concatenate([b.batch(idx) for b in tower_a], axis=1)).to(dev)
        xb = torch.from_numpy(np.concatenate([b.batch(idx) for b in tower_b], axis=1)).to(dev) if has_b else None
        return xa, xb

    def acc_on(mask):
        idx = np.nonzero(mask)[0]
        correct = np.zeros(len(idx), dtype=bool)
        model.eval()
        with torch.no_grad():
            for s in range(0, len(idx), eval_batch):
                sl = idx[s: s + eval_batch]
                xa, xb = assemble(sl)
                correct[s: s + len(sl)] = (model(xa, xb).argmax(-1).cpu().numpy() == y[sl])
        return float(correct.mean()), correct

    best_val, best_state, best_epoch = -1.0, None, -1
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(len(idx_tr), generator=g).numpy()
        for s in range(0, len(idx_tr), batch_size):
            sl = idx_tr[perm[s: s + batch_size]]
            xa, xb = assemble(sl)
            yb = yt[sl].to(dev)
            opt.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(model(xa, xb), yb)
            loss.backward()
            opt.step()
        val_acc, _ = acc_on(va)
        if val_acc > best_val:
            best_val, best_epoch = val_acc, epoch
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    test_acc, test_correct = acc_on(te)
    return {"test_acc": test_acc, "val_acc_best": best_val, "best_epoch": best_epoch,
            "n_train": int(tr.sum()), "n_val": int(va.sum()), "n_test": int(te.sum()), "test_correct": test_correct,
            "towers": {"a_dim": int(d_a), "b_dim": int(d_b), "width_a": int(width_a), "width_b": int(width_b if has_b else 0)}}


def run_cell_reader(data, spaces: dict, space: str, offset: int, arm: str, cap: str, seed: int,
                    reader: str, factory_of: dict, n_slots: int, device: str = "cpu") -> dict:
    """One unshuffled cell under a reader. arm in ARMS + ("a", "c"); the blocks are
    assembled exactly as run_probes.run_cell assembles them ((a) blocks first, the
    arm's extras after, in the factories' order); under R0 the call is run_cell's
    own trainer call (bit-exact, a CI test)."""
    spec = READERS[reader]
    if cap != spec["capacity"] and not (cap == "linear" and spec["kind"] in ("plain", "hz_rescaled")):
        raise SystemExit(f"reader {reader} runs at {spec['capacity']}; a {cap} cell is not registered under it")
    sp = spaces[space]
    rows, anchors = anchor_table(data.lengths, offset, data.tokens.shape[1])
    labels = labels_for(data.tokens, rows, anchors, offset, sp["label_map"])
    split = data.row_split()[rows]
    blocks_a = feature_blocks(data, "a", rows, anchors, n_slots=n_slots)
    if arm == "c":
        extras = feature_blocks(data, "c", rows, anchors, n_slots=n_slots)[len(blocks_a):]   # the slots block
    else:
        extras = [] if arm == BASE_ARM else list(factory_of[(arm, seed)](rows, anchors))
    t0 = time.time()
    params: dict = {"kind": spec["kind"], "epochs": spec["epochs"], "lr": spec["lr"]}
    if spec["kind"] == "plain":
        res = train_probe(blocks_a + extras, labels, split, sp["n_classes"], cap, seed, device=device,
                          epochs=spec["epochs"], lr=spec["lr"])
    elif spec["kind"] == "hz_rescaled":
        fams = family_of_blocks(blocks_a, extras)
        ref = SlotsAnchorBlock(data.array("slots"), rows, anchors, n_slots)
        blocks, scale_info = hz_rescale(fams, ref, np.nonzero(split == "train")[0])
        params["rescale"] = scale_info
        res = train_probe(blocks, labels, split, sp["n_classes"], cap, seed, device=device,
                          epochs=spec["epochs"], lr=spec["lr"])
    elif spec["kind"] == "two_tower":
        fams = family_of_blocks(blocks_a, extras)
        tower_a = [b for name, blocks in fams if name != "SLOTS" for b in blocks]
        tower_b = [b for name, blocks in fams if name == "SLOTS" for b in blocks]
        res = train_two_tower(tower_a, tower_b, labels, split, sp["n_classes"], seed, device=device,
                              epochs=spec["epochs"], lr=spec["lr"], width_a=spec["tower_a"], width_b=spec["tower_b"])
        params["towers"] = res["towers"]
    else:
        raise SystemExit(f"unknown reader kind {spec['kind']}")
    te_idx = np.nonzero(split == "test")[0]
    prompts_of_test = data.prompt_idx[rows[te_idx]]
    y_test = labels[te_idx]
    maj_label = np.bincount(labels[split == "train"]).argmax()
    return {
        "cell": cell_id(space, offset, arm, cap, seed), "reader": reader, "reader_params": params,
        "space": space, "offset": offset, "features": arm, "capacity": cap, "seed": seed, "shuffled": False,
        "test_acc": res["test_acc"], "val_acc_best": res["val_acc_best"], "best_epoch": res["best_epoch"],
        "n_train": res["n_train"], "n_val": res["n_val"], "n_test": res["n_test"],
        "majority_rate_test": float((y_test == maj_label).mean()),
        "runtime_s": round(time.time() - t0, 1),
        "_clusters": {int(p): [int(res["test_correct"][prompts_of_test == p].sum()), int((prompts_of_test == p).sum())]
                      for p in np.unique(prompts_of_test)},
    }


# ---------------------------------------------------------------------------
# Grids
# ---------------------------------------------------------------------------

def grid_lens(space: str = SPACE_L3_BAL, offsets: tuple[int, ...] = LENS_OFFSETS) -> list[tuple]:
    """(space, offset, arm, capacity, seed, shuffled, reader): the amended rider's
    four shuffled cells, the fresh (a) mlp256, off2 at both capacities and the
    further offsets at mlp256 for the three arms, then the PROXY cells (fresh
    linear (a) and (c) at off2). 49 cells."""
    g: list[tuple] = [(space, GATE_OFFSET, arm, "linear", 0, True, "R0") for arm in am.SHUFFLED_ARMS]
    g += [(space, GATE_OFFSET, BASE_ARM, GATE_CAPACITY, s, False, "R0") for s in SEEDS]
    for off in offsets:
        caps = ("linear", GATE_CAPACITY) if off == GATE_OFFSET else (GATE_CAPACITY,)
        for s in SEEDS:
            for cap in caps:
                for arm in ARMS:
                    g.append((space, off, arm, cap, s, False, "R0"))
    g += [(space, GATE_OFFSET, BASE_ARM, PROXY_CAP, s, False, "R0") for s in SEEDS]
    g += [(space, GATE_OFFSET, "c", PROXY_CAP, s, False, "R0") for s in SEEDS]
    _check_unique(g)
    return g


def grid_readers(readers: tuple[str, ...], spaces: tuple[str, ...]) -> list[tuple]:
    """Per (reader, space): the fresh (a) at the gate capacity and the three arms
    at the gate cell, three seeds; at the balanced lens three R0 linear (a)
    cells (the Mf_x reference; re-trainings of STAGE lens's proxy (a)); no rider
    cells (the block's rule)."""
    g: list[tuple] = []
    for r in readers:
        for sp in spaces:
            g += [(sp, GATE_OFFSET, BASE_ARM, GATE_CAPACITY, s, False, r) for s in SEEDS]
            for s in SEEDS:
                for arm in ARMS:
                    g.append((sp, GATE_OFFSET, arm, GATE_CAPACITY, s, False, r))
    if SPACE_L3_BAL in spaces:
        g += [(SPACE_L3_BAL, GATE_OFFSET, BASE_ARM, PROXY_CAP, s, False, "R0") for s in SEEDS]
    _check_unique(g)
    return g


def _check_unique(g: list[tuple]) -> None:
    keys = {(c[6], cell_id(*c[:6])) for c in g}
    if len(keys) != len(g):
        raise SystemExit("duplicate (reader, cell) in the grid")


def grid_keys(g: list[tuple]) -> set[tuple[str, str]]:
    return {(c[6], cell_id(*c[:6])) for c in g}


def row_key(row: dict) -> tuple[str, str]:
    return (str(row.get("reader", "R0")), row["cell"])


def check_grid_against_committed(g: list[tuple], p3_ids: set[str]) -> list[str]:
    """Refuse any grid cell whose id exists among the committed Phase-3 cells,
    EXCEPT the fresh (a) mlp256 cells at L1 (S3 and S1), which share ids with the
    committed R0 cells by construction; those are returned (named) and never
    pooled with the committed cells at the gate capacity."""
    shared, bad = [], []
    for c in g:
        cid = cell_id(*c[:6])
        if cid in p3_ids:
            if c[2] == BASE_ARM and c[3] == GATE_CAPACITY and c[0] in SPACE_L1.values():
                shared.append(cid)
            else:
                bad.append(cid)
    if bad:
        raise SystemExit(f"grid cell ids collide with committed Phase-3 cells: {bad[:3]} ...")
    return sorted(set(shared))


def smoke_cell_grid(spec: str) -> tuple[list[tuple], tuple[str, ...], tuple[str, ...]]:
    """One unshuffled cell from 'READER|space|offset|arm|capacity|seed' (a smoke to a scratch path:
    the timing cell of the registration's PRE-FREEZE round; refused under results/)."""
    parts = spec.split("|")
    if len(parts) != 6:
        raise SystemExit("--smoke-cell wants READER|space|offset|arm|capacity|seed")
    reader, space, off, arm, cap, seed = parts
    if reader not in READERS:
        raise SystemExit(f"unknown reader {reader!r}")
    return [(space, int(off), arm, cap, int(seed), False, reader)], (reader,), (space,)


def stage_spaces(stage: str, tag: str) -> tuple[str, ...]:
    if stage == "lens":
        return (SPACE_L3_BAL,)
    if stage in ("readers", "readers_long"):
        return (SPACE_L1["olmoe"], SPACE_L3_LOP, SPACE_L3_BAL)
    if stage == "s1":
        return (SPACE_L1["concept"],)
    raise SystemExit(f"unknown stage {stage!r}")


def stage_grid(stage: str, tag: str, readers: tuple[str, ...] | None) -> tuple[list[tuple], tuple[str, ...], tuple[str, ...]]:
    sps = stage_spaces(stage, tag)
    if stage == "lens":
        return grid_lens(), ("R0",), sps
    if stage in ("readers", "readers_long"):
        rs = STAGE_READERS[stage]
        return grid_readers(rs, sps), rs, sps
    if not readers:
        raise SystemExit("--readers is required for the s1 stage (the readers the block names)")
    bad = [r for r in readers if r not in READERS]
    if bad:
        raise SystemExit(f"unknown reader(s) {bad} — the registry knows {sorted(READERS)}")
    return grid_readers(tuple(readers), sps), tuple(readers), sps


# ---------------------------------------------------------------------------
# Readouts and labels (the frozen rules, per reader)
# ---------------------------------------------------------------------------

def readouts_for(cells: list[dict], space: str, reader: str, p3_cells: list[dict], lens_lin_a: list[dict],
                 expected: int | None) -> dict:
    """Every pairing of F-25 for one (reader, space). Mf pairs the reader's OWN
    fresh (a): the committed Phase-3 (a) cells at the gate capacity are never
    pooled (their ids coincide with the fresh L1 cells); Mf_x pairs the
    committed linear (a) where the space has one, else this run's R0 linear
    (a) at the balanced lens (relabelled LIN_BASE at the gate capacity)."""
    rc = [c for c in cells if c.get("reader", "R0") == reader and c["space"] == space]
    if space == SPACE_L3_BAL:
        lin = []
        for c in lens_lin_a:
            if c["space"] == space and c["offset"] == GATE_OFFSET:
                d = dict(c)
                d["features"], d["capacity"] = LIN_BASE, GATE_CAPACITY
                d["cell"] = cell_id(space, GATE_OFFSET, LIN_BASE, GATE_CAPACITY, int(c["seed"]))
                lin.append(d)
        committed = []
    else:
        lin = relabel_committed_linear_a(p3_cells, space)
        committed = [c for c in p3_cells if c["space"] == space
                     and not (c["features"] == BASE_ARM and c["capacity"] == GATE_CAPACITY)]
    pooled = rc + committed + [c for c in lens_lin_a if c["space"] == space and c.get("reader") != reader]
    out = {
        "d_fplus_b_vs_fplus_r": margins(rc, "fplus_b", expected_clusters=expected, base_feats=TWIN_ARM),
        "mt_fplus_b_vs_fplus": margins(rc, "fplus_b", expected_clusters=expected, base_feats="fplus"),
        "mn_r_fplus_r_vs_fplus": margins(rc, TWIN_ARM, expected_clusters=expected, base_feats="fplus"),
        "mf_fplus_vs_a": margins(rc, "fplus", expected_clusters=expected, base_feats="a"),
        "mfx_fplus_vs_linear_a": margins(rc + lin, "fplus", expected_clusters=expected, base_feats=LIN_BASE),
        "mc_fplus_vs_c": margins(pooled, "fplus", expected_clusters=expected, base_feats="c"),
    }
    out["reader_valid"] = reader_validity(rc, out["mf_fplus_vs_a"], out["mfx_fplus_vs_linear_a"], space)
    gate = gate_row(out["d_fplus_b_vs_fplus_r"], space)
    out["gate"] = {"row": gate, "fires": bool(out["reader_valid"]["ok"] and gate_fires(gate))}
    out["best_epochs"] = {arm: sorted(int(c["best_epoch"]) for c in rc if c["features"] == arm and not c["shuffled"]
                                      and c["offset"] == GATE_OFFSET and c["capacity"] == GATE_CAPACITY)
                          for arm in tuple(ARMS) + (BASE_ARM,)}
    if reader == "RN":
        out["rescale"] = {c["cell"]: (c.get("reader_params") or {}).get("rescale") for c in rc if not c["shuffled"]}
    return out


def proxy_readout(cells: list[dict], space: str, expected: int | None) -> dict | None:
    """P = acc((c), linear) - acc((a), linear) at off2 on the fresh R0 cells."""
    rc = [c for c in cells if c.get("reader", "R0") == "R0" and c["space"] == space and not c["shuffled"]
          and c["capacity"] == PROXY_CAP and c["offset"] == GATE_OFFSET and c["features"] in ("a", "c")]
    rows = margins(rc, "c", expected_clusters=expected, base_feats="a")
    row = next((m for m in rows if m["offset"] == GATE_OFFSET and m["capacity"] == PROXY_CAP), None)
    if row is None:
        return None
    floors = {arm: sorted(round(c["test_acc"] - c["majority_rate_test"], 6) for c in rc if c["features"] == arm)
              for arm in ("a", "c")}
    return {"row": row, "fires": fires_triple(row, "c-a"), "acc_minus_floor_per_seed": floors}


def lens_label(p_primary: dict | None, p_replication: dict | None) -> str:
    if p_primary is None or p_replication is None:
        return LABEL_INCOMPLETE
    fp, fr = p_primary["fires"], p_replication["fires"]
    if fp and fr:
        return LENS_SURVIVES
    if fp != fr:
        return LENS_SPLIT
    if p_primary["row"]["ci95"][1] < MATERIALITY and p_replication["row"]["ci95"][1] < MATERIALITY:
        return LENS_COLLAPSE
    return LENS_NOT_SHOWN


def growth_reading(p: dict | None, l2_margin: float | None) -> str | None:
    """P's CI95 against the committed L2 (c) - (a) linear margin of the same harvest:
    upper below it = the L3 growth over L2 did not survive the size-capped lens
    (the headline's size was mega-group membership); lower above it = survives;
    else not settled. Cross-space margins are not like-for-like (said in words)."""
    if p is None or l2_margin is None:
        return None
    lo, hi = p["row"]["ci95"]
    if hi < l2_margin:
        return GROWTH_LOST
    if lo > l2_margin:
        return GROWTH_SURVIVES
    return GROWTH_UNSETTLED


def growth_combined(primary: str | None, replication: str | None) -> str | None:
    """The ONE growth word over both harvests: LOST iff LOST on both (and only
    then the 'coarser claim' sentence); SURVIVES iff SURVIVES on both; SPLIT iff
    exactly one harvest is LOST or SURVIVES; otherwise NOT-SETTLED."""
    if primary is None or replication is None:
        return None
    if primary == replication and primary in (GROWTH_LOST, GROWTH_SURVIVES):
        return primary
    decided = [w for w in (primary, replication) if w in (GROWTH_LOST, GROWTH_SURVIVES)]
    if len(decided) == 1 or (len(decided) == 2 and primary != replication):
        return GROWTH_SPLIT
    return GROWTH_UNSETTLED


def licence_of(label: str, mt_p, mt_r, mnr_p, mnr_r) -> tuple[str | None, str | None]:
    """F-25's licence rule on a SURVIVES label."""
    if label not in (LABEL_SURVIVES, LABEL_STRONGER):
        return None, None
    mt_neg = any(m is None or m["ci95"][1] < 0 for m in (mt_p, mt_r))
    mnr_neg = any(m is None or m["ci95"][1] < 0 for m in (mnr_p, mnr_r))
    if not mt_neg and not mnr_neg:
        return "full", None
    return "equal-dims-only", ("Mt CI95 upper < 0 on a harvest" if mt_neg else
                               "Mn_r CI95 upper < 0 on a harvest (fire inflated by the twin's own cost)")


def pair_label(rp: dict, rr: dict, offsets: tuple[int, ...], stronger_word: bool = False) -> dict:
    """One (reader, space) across the two harvests through the frozen rules; in a
    readers stage the frozen SURVIVES word is written SURVIVES-STRONGER."""
    gp, gr = rp["gate"]["row"], rr["gate"]["row"]
    label = source_label(gp, gr, rp["d_fplus_b_vs_fplus_r"], rr["d_fplus_b_vs_fplus_r"],
                         reader_ok=(bool(rp["reader_valid"]["ok"]), bool(rr["reader_valid"]["ok"])))
    if stronger_word and label == LABEL_SURVIVES:
        label = LABEL_STRONGER
    sp = (gp or gr or {}).get("space") or (rp["d_fplus_b_vs_fplus_r"][0]["space"] if rp["d_fplus_b_vs_fplus_r"] else None)
    mt_p = gate_row(rp["mt_fplus_b_vs_fplus"], sp) if sp else None
    mt_r = gate_row(rr["mt_fplus_b_vs_fplus"], sp) if sp else None
    mnr_p = gate_row(rp["mn_r_fplus_r_vs_fplus"], sp) if sp else None
    mnr_r = gate_row(rr["mn_r_fplus_r_vs_fplus"], sp) if sp else None
    lic, reason = licence_of(label, mt_p, mt_r, mnr_p, mnr_r)
    horizons = {f"off{o}": horizon_note(gate_row(rp["d_fplus_b_vs_fplus_r"], sp, offset=o),
                                        gate_row(rr["d_fplus_b_vs_fplus_r"], sp, offset=o), o)
                for o in offsets if o != GATE_OFFSET} if sp else {}
    mt_triple = {"primary": fires_triple(mt_p, "fplus_b-fplus"), "replication": fires_triple(mt_r, "fplus_b-fplus")}
    return {"label": label, "licence": lic, "licence_reason": reason,
            "gate": {"primary": gp, "replication": gr},
            "mt": {"primary": mt_p, "replication": mt_r}, "mn_r": {"primary": mnr_p, "replication": mnr_r},
            "mt_fires_triple": mt_triple,
            "mn_r_fires_triple": {"primary": fires_triple(mnr_p, "fplus_r-fplus"), "replication": fires_triple(mnr_r, "fplus_r-fplus")},
            "reader_valid": {"primary": rp["reader_valid"]["ok"], "replication": rr["reader_valid"]["ok"]},
            "best_epochs": {"primary": rp["best_epochs"], "replication": rr["best_epochs"]},
            "horizons": horizons}


def reopen_eligible(v: dict) -> bool:
    """A reopen-grade cell: SURVIVES-STRONGER with the FULL licence AND Mt firing
    the triple rule on both harvests."""
    return (v["label"] == LABEL_STRONGER and v["licence"] == "full"
            and bool(v["mt_fires_triple"]["primary"]) and bool(v["mt_fires_triple"]["replication"]))


def k2_sentence(labels_by_rs: dict[tuple[str, str], dict], s1_by_r: dict[str, dict] | None) -> dict:
    """The pinned K-2 sentence at S3 over the (reader, space) labels of the readers
    stages. The lopsided lens never decides a reopen; REOPENED needs a
    reopen-grade cell at L1 or the balanced L3 AND the same reader reopen-grade
    at S1 L1; READER-INVALID cells are VOID and the word is read over the valid
    cells, named."""
    valid = {k: v for k, v in labels_by_rs.items() if v["label"] != LABEL_READER_INVALID}
    void = sorted(f"{r}|{sp}" for (r, sp), v in labels_by_rs.items() if v["label"] == LABEL_READER_INVALID)
    surv = sorted(f"{r}|{sp}" for (r, sp), v in valid.items() if v["label"] == LABEL_STRONGER)
    split = sorted(f"{r}|{sp}" for (r, sp), v in valid.items() if v["label"] == LABEL_SPLIT)
    s1_trigger = sorted({r for (r, sp), v in valid.items() if sp in REOPEN_SPACES and reopen_eligible(v)})
    reopened = []
    for (r, sp), v in valid.items():
        if sp not in REOPEN_SPACES or not reopen_eligible(v):
            continue
        s1 = (s1_by_r or {}).get(r)
        if s1 and reopen_eligible(s1):
            reopened.append(f"{r}|{sp}")
    if not valid:
        word = K2_INCOMPLETE
    elif reopened:
        word = K2_REOPENED
    elif surv:
        word = K2_ISOLATED
    elif split:
        word = K2_UNSETTLED
    else:
        word = K2_STANDS
    pending = bool(s1_trigger) and not (s1_by_r and all(r in s1_by_r for r in s1_trigger))
    return {"word": word, "over_valid_cells_only": bool(void), "void_cells": void,
            "reopen_provisional": bool(reopened),
            "reopen_rider_rule": ("a REOPENED word is PROVISIONAL until a reader-matched rider (the four amended-rider "
                                  "shuffled cells under that reader at mlp256, off2, seed 0, on both S3 harvests and at "
                                  "S1 L1) passes under its own dated registration; the word is written with that "
                                  "qualifier and no K-2 line moves before the rider lands") if reopened else None,
            "survives_stronger": surv, "split": split, "reopened": sorted(reopened),
            "s1_trigger_readers": s1_trigger, "s1_pending": pending,
            "narrowed_cells": sorted(f"{r}|{sp}" for (r, sp), v in valid.items() if v["label"] == LABEL_ABSORBED),
            "not_narrowed_cells": sorted(f"{r}|{sp}" for (r, sp), v in valid.items() if v["label"] == LABEL_NOT_SHOWN),
            "rule": ("over the valid cells: NOT-OVERTURNED iff every one ABSORBED or NOT-SHOWN (narrowed only where ABSORBED); "
                     "REOPENED iff a cell at L1 or the balanced L3 is reopen-grade (SURVIVES-STRONGER, FULL licence, Mt "
                     "firing the triple rule on both harvests) AND the same reader is reopen-grade at S1 L1; the "
                     "lopsided lens never decides a reopen; ISOLATED iff some SURVIVES-STRONGER without that; UNSETTLED "
                     "iff some SPLIT and no SURVIVES-STRONGER; INCOMPLETE iff no valid cell; VOID cells named")}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def _git(strict: bool = False) -> tuple[str, list[str]]:
    """(HEAD, porcelain lines over TRACKED files), run at the repo root; with
    strict, a failed git is a refusal, never a clean-looking 'unknown'."""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10, check=True)
        d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                           capture_output=True, text=True, timeout=10, check=True)
    except Exception as e:  # noqa: BLE001
        if strict:
            raise SystemExit(f"git check failed ({e}) — refusing to train on a registered out path")
        return "unknown", []
    return r.stdout.strip(), [ln for ln in d.stdout.splitlines() if ln.strip()]


def _tool_tracked() -> bool:
    t = subprocess.run(["git", "ls-files", "--error-unmatch", str(Path(__file__).resolve())], cwd=ROOT,
                       capture_output=True, text=True, timeout=10)
    return t.returncode == 0


def _under_results(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to((REAL.parent).resolve())
        return True
    except ValueError:
        return False


def _write_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_state(path: Path, npz_shas: dict | None) -> tuple[dict, dict[tuple[str, str], dict]]:
    """Header and rows keyed by (reader, cell): parse_state's semantics — a
    headerless or sha-mismatched file is refused, a torn final line dropped."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if not lines:
        raise SystemExit(f"{path.name}: empty state file — refusing to resume")
    try:
        header = json.loads(lines[0])
    except ValueError:
        raise SystemExit(f"{path.name}: unreadable header — refusing to resume; delete it or use a different --out")
    if not isinstance(header, dict) or header.get("kind") != "state_header" or header.get("harvest_npz_sha256") is None:
        raise SystemExit(f"{path.name}: not a state header — refusing")
    bound = header["harvest_npz_sha256"]
    if npz_shas is not None and bound != npz_shas:
        raise SystemExit(f"{path.name}: state header binds a different harvest — refusing")
    rows: dict[tuple[str, str], dict] = {}
    for i, line in enumerate(lines[1:], start=2):
        try:
            d = json.loads(line)
        except ValueError:
            if i == len(lines):
                break                                  # a torn final line (a crash mid-write) is dropped
            raise SystemExit(f"{path.name}: corrupt row {i} — refusing")
        d = normalize_hist(d)
        if "_clusters" in d:
            d["_clusters"] = {int(k): v for k, v in d["_clusters"].items()}
        rows[row_key(d)] = d
    return header, rows


def truncate_torn(path: Path) -> int:
    """On --resume, cut a torn final line (a crash mid-write) off the state file
    so the rows appended next start on a clean line; returns the bytes dropped
    (recorded in the payload). A file ending in a newline is untouched."""
    b = path.read_bytes()
    if not b or b.endswith(b"\n"):
        return 0
    keep = b.rfind(b"\n") + 1
    with open(path, "r+b") as fh:
        fh.truncate(keep)
    return len(b) - keep


def spaces_for(data, args) -> dict:
    """L1 and the LOPSIDED L3 from the registered files; the BALANCED L3 renamed
    from a second build_spaces call over the balanced artifact."""
    base = build_spaces(data, tag=args.space_tag, buckets16=args.buckets16, glue16=args.glue16,
                        buckets512=args.buckets512, glue512=args.glue512, groups_path=args.groups)
    if args.space_tag == "olmoe" and Path(args.balanced_groups).exists():
        bal = build_spaces(data, tag=args.space_tag, buckets16=args.buckets16, glue16=args.glue16,
                           buckets512=args.buckets512, glue512=args.glue512, groups_path=args.balanced_groups)
        base[SPACE_L3_BAL] = bal["L3_olmoe_groups_v1"]
    return base


def fill_harvest_files(args, registered: bool) -> dict:
    """The companion files of the harvest: filled from HARVEST_FILES where not
    given; a disagreement with the table is refused on a registered out."""
    name = Path(args.harvest).name
    table = HARVEST_FILES.get(name)
    if table is None:
        if registered:
            raise SystemExit(f"{name} is not a registered harvest")
        return {}
    filled = {}
    for key, fname in table.items():
        want = fname if key in ("space_tag", "n_slots") else str(REAL / fname)
        got = getattr(args, key, None)
        if got is None:
            setattr(args, key, want)
            filled[key] = want
        elif registered and str(got).replace("\\", "/").rstrip("/").split("/")[-1] != str(want).replace("\\", "/").split("/")[-1] \
                and key not in ("space_tag", "n_slots"):
            raise SystemExit(f"--{key.replace('_', '-')} {got} disagrees with the registered companion of {name} ({fname})")
        elif registered and key in ("space_tag", "n_slots") and got != want:
            raise SystemExit(f"--{key.replace('_', '-')} {got} disagrees with the registered value for {name} ({want})")
    return filled


def lens_riders_passed(paths: list[str] | None) -> dict:
    """STAGE readers' admission rule for the balanced lens: the two STAGE lens
    payloads, named lens_s3.json then lens_s3_r.json, each VERIFIED as a lens
    payload of its role (verify_payload: registry, role-bound harvest, clean
    tree, instrument sha, state rows, the rider recomputed) with the balanced
    rider passing. Never a refusal here: the caller decides (a registered
    readers run refuses; a smoke drops the space)."""
    if not paths or len(paths) != 2:
        return {"ok": False, "reason": "no --lens-payloads given"}
    names = [Path(p).name for p in paths]
    if names != list(REGISTERED_OUTS["lens"]):
        return {"ok": False, "reason": f"--lens-payloads must be {list(REGISTERED_OUTS['lens'])} in that order, got {names}"}
    out: dict = {"ok": True, "payloads": {}}
    for p, role in zip(paths, ("primary", "replication")):
        pp = Path(p)
        if not pp.exists():
            return {"ok": False, "reason": f"{p} missing"}
        try:
            d, _ = verify_payload(pp, role, expect_stage="lens")
        except SystemExit as e:
            return {"ok": False, "reason": f"{pp.name}: {e}"}
        ok = bool((d["riders"].get(SPACE_L3_BAL) or {}).get("pass"))
        out["payloads"][pp.name] = {"sha256": _sha(pp), "rider_pass": ok, "ok": ok}
        out["ok"] = out["ok"] and ok
    return out


def run(args) -> None:
    chain = assert_frozen_chain()
    import torch
    torch.set_num_threads(int(args.threads))
    out_path = Path(args.out).resolve()
    registered_outs = {(REAL / n).resolve() for names in REGISTERED_OUTS.values() for n in names}
    registered = out_path in registered_outs
    if _under_results(out_path) and not registered:
        raise SystemExit("an unregistered out name may not be written under results/")
    if registered:
        if args.only or args.smoke_cell:
            raise SystemExit("--only / --smoke-cell smoke runs may not write a registered out path")
        if out_path.name not in REGISTERED_OUTS[args.stage]:
            raise SystemExit(f"{out_path.name} is not a registered out of stage {args.stage}")
        if Path(args.harvest).name != HARVEST_OF_OUT[out_path.name]:
            raise SystemExit(f"{out_path.name} belongs to {HARVEST_OF_OUT[out_path.name]}, not {Path(args.harvest).name}")
        if args.device != "cpu":
            raise SystemExit("a registered run is CPU only")
        if int(args.threads) != THREADS:
            raise SystemExit(f"a registered run uses --threads {THREADS}")
        if int(args.n_boot) != N_BOOT:
            raise SystemExit(f"a registered run uses --n-boot {N_BOOT}")
        head, porcelain = _git(strict=True)
        if porcelain:
            raise SystemExit("the tracked tree is not clean — a registered run refuses to write under results/:\n" + "\n".join(porcelain))
        if not _tool_tracked():
            raise SystemExit("the instrument is not git-tracked — commit the registration first")
    else:
        head, porcelain = _git()
    filled = fill_harvest_files(args, registered)
    bal_admission = None
    if args.stage in ("readers", "readers_long") and not args.smoke_cell:
        bal_admission = lens_riders_passed(getattr(args, "lens_payloads", None))
        if registered and not bal_admission["ok"]:
            raise SystemExit(f"the balanced lens is not admitted to this stage (STAGE lens's rider must have passed on "
                             f"both harvests): {bal_admission}")
    state_path = Path(str(out_path) + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a crashed registered run")
    torn_dropped = 0

    data = HarvestData(args.harvest)
    split_names = data.row_split()
    bind_spaces_to_harvest(data.ref_meta, {"buckets16": args.buckets16, "buckets512": args.buckets512}, n_slots=args.n_slots)
    fid = Path(args.fidelity)
    rider_payload = json.loads(fid.read_text()) if fid.exists() else None
    if rider_payload is None or rider_payload.get("verdict") != "PASS" or rider_payload.get("npz_sha256_validated") != data.npz_shas:
        raise SystemExit("R1 harvest-fidelity rider missing, not PASS, or for a different harvest version")
    p3_cells = load_phase3_cells(Path(args.phase3_state), Path(args.phase3_payload), data.npz_shas)
    p3_payload = json.loads(Path(args.phase3_payload).read_text())
    re_m = margins(p3_cells, "c", expected_clusters=EXPECTED_CLUSTERS)
    want = {(m["space"], m["offset"], m["capacity"]): m for m in p3_payload["margins"]}
    for m in re_m:
        w = want.get((m["space"], m["offset"], m["capacity"]))
        if w is None or abs(m["margin"] - w["margin"]) > 1e-12 or max(abs(a - b) for a, b in zip(m["ci95"], w["ci95"])) > 1e-12:
            raise SystemExit("phase-3 state file does not reproduce its own payload margins — refusing")
    p3_ids = {c["cell"] for c in p3_cells}
    spaces = spaces_for(data, args)
    if args.smoke_cell:
        grid, readers, reg_spaces = smoke_cell_grid(args.smoke_cell)
    else:
        grid, readers, reg_spaces = stage_grid(args.stage, args.space_tag, tuple(args.readers.split(",")) if args.readers else None)
    shared_ids = check_grid_against_committed(grid, p3_ids)
    if bal_admission is not None and not bal_admission["ok"]:      # a smoke without the lens payloads drops the space
        grid = [c for c in grid if c[0] != SPACE_L3_BAL]
        reg_spaces = tuple(sp for sp in reg_spaces if sp != SPACE_L3_BAL)
    for sp in reg_spaces:
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built (balanced artifact missing?)")

    hidden, top_ids, slots = data.array("hidden"), data.array("top_ids"), data.array("slots")
    moments = train_moments(hidden, data.lengths, split_names)
    committed_sha = committed_moments_sha(args.harvest)
    if committed_sha is not None and committed_sha != moments["sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's — refusing")
    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    all_offsets = sorted({c[1] for c in grid})
    geometry = {str(seed): {f"off{o}": twin_geometry(data.lengths, perms[seed], o, data.tokens.shape[1], data.prompt_idx)
                            for o in all_offsets} for seed in SEEDS}
    for seed, g in geometry.items():
        for o, gg in g.items():
            if gg["corrected_twin_same_prompt_frac"] != 0.0:
                raise SystemExit(f"corrected twin reads its own prompt at seed {seed} {o} — refusing")
    factory_of = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments, perms)

    done: dict[tuple[str, str], dict] = {}
    if state_path.exists():
        header, done = load_state(state_path, data.npz_shas)
        if registered and header.get("git_head") != head:
            raise SystemExit(f"the state file was started at HEAD {str(header.get('git_head'))[:12]}, the tree is at {head[:12]} — "
                             "no commit between a stage's launch and its landing; refusing to resume")
        torn_dropped = truncate_torn(state_path)                 # after the header and HEAD checks: a refused resume cuts nothing
        print(f"[resume] {len(done)} rows already in the state file; torn bytes dropped {torn_dropped}", flush=True)
    else:
        hdr = state_header(data.npz_shas)
        hdr.update({"registered": REGISTERED, "stage": args.stage, "readers": list(readers), "spaces": list(reg_spaces),
                    "label_space_sha256": _label_shas(args), "frozen_chain": chain, "threads": int(args.threads),
                    "git_head": head, "harvest": Path(args.harvest).name, "out": out_path.name,
                    "shared_committed_ids": shared_ids, "balanced_admission": bal_admission})
        _write_lf(state_path, json.dumps(hdr) + "\n")

    expected = None if (args.only or args.smoke_cell) else EXPECTED_CLUSTERS
    t0 = time.time()
    cells: list[dict] = []
    riders: dict[str, dict | None] = {}
    for i, (sp, off, arm, cap, seed, shuffled, reader) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if args.only and not any(s and s in cid for s in args.only.split(",")):
            continue
        key = (reader, cid)
        if key in done:
            cells.append(done[key])
        else:
            if shuffled:
                res = run_cell_diag(data, spaces, sp, off, arm, seed, args.device, factory_of, args.n_slots)
                res["reader"] = reader
            else:
                res = run_cell_reader(data, spaces, sp, off, arm, cap, seed, reader, factory_of, args.n_slots, args.device)
            cells.append(res)
            with open(state_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(res) + "\n")
            print(f"[{i + 1}/{len(grid)}] {reader} {cid}: test_acc={res['test_acc']:.4f} (maj {res['majority_rate_test']:.4f}) "
                  f"epoch {res.get('best_epoch')} {res['runtime_s']}s total {time.time() - t0:.0f}s", flush=True)
        if shuffled:
            riders[sp] = am.rider_check_amended(cells, sp, int(spaces[sp]["n_classes"]), n_boot=args.n_boot,
                                                expected_clusters=expected)

    lens_lin_a = [c for c in cells if c.get("reader") == "R0" and c["space"] == SPACE_L3_BAL and c["features"] == BASE_ARM
                  and c["capacity"] == "linear" and not c["shuffled"]]
    per_rs = {}
    if not args.smoke_cell:
        for r in readers:
            for sp in reg_spaces:
                per_rs[f"{r}|{sp}"] = readouts_for(cells, sp, r, p3_cells, lens_lin_a, expected)
    proxy = proxy_readout(cells, SPACE_L3_BAL, expected) if (args.stage == "lens" and not args.smoke_cell) else None
    head_now, porcelain_now = _git(strict=registered)
    if registered and head_now != head:
        raise SystemExit("HEAD moved during the run — no commit between a stage's launch and its landing; refusing to write")
    payload = {
        "registered": REGISTERED, "stage": args.stage, "role": ROLE_OF_OUT.get(out_path.name),
        "harvest": args.harvest, "tag": args.space_tag,
        "readers": {r: READERS[r] for r in readers}, "spaces": list(reg_spaces),
        "offsets": {sp: (list(LENS_OFFSETS) if args.stage == "lens" else [GATE_OFFSET]) for sp in reg_spaces},
        "n_cells": len([c for c in cells if not c["shuffled"]]), "partial": bool(args.only or args.smoke_cell),
        "smoke_cell": args.smoke_cell, "resumed_cells": int(sum(1 for c in cells if row_key(c) in done)),
        "cells": [{k: v for k, v in c.items() if k not in ("_clusters", "_hist")} for c in cells],
        "riders": riders, "per_reader_space": per_rs, "proxy": proxy,
        "shared_committed_ids": shared_ids, "balanced_admission": bal_admission,
        "standardization": {"moments_sha256": moments["sha256"], "moments_sha_matches_committed_oq17": (None if committed_sha is None else True)},
        "twin": {"arm": TWIN_ARM, "seed_base": TWIN_SEED_BASE, "construction": CONSTRUCTION,
                 "perm_sha256": {str(s): hashlib.sha256(perms[s].astype(np.int64).tobytes()).hexdigest() for s in SEEDS},
                 "geometry": geometry},
        "provenance": {
            "git_commit": head_now, "git_status_tracked": porcelain_now, "instrument_sha256": _sha(Path(__file__)),
            "frozen_chain": chain, "args": redact_args(vars(args)), "companion_files_filled": filled,
            "harvest_npz_sha256": data.npz_shas, "label_space_sha256": _label_shas(args),
            "phase3_state_sha256": _sha(Path(args.phase3_state)), "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
            "device": args.device, "threads": int(args.threads), "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "torn_bytes_dropped_on_resume": int(torn_dropped),
            "torch_version": torch.__version__, "numpy_version": np.__version__, "python_version": platform.python_version(),
            "platform": platform.platform(), "state_file": state_path.name,
            "determinism_note": "CPU training; the landing condition re-runs one gate cell per reader from a clean clone, rows identical except runtime_s",
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    payload["provenance"]["state_sha256"] = _sha(state_path)
    _write_lf(out_path, json.dumps(payload, indent=1) + "\n")
    print(json.dumps({k: {"reader_valid": v["reader_valid"]["ok"], "gate_fires": v["gate"]["fires"],
                          "D": (v["gate"]["row"] or {}).get("margin")} for k, v in per_rs.items()}, indent=1))
    if proxy:
        print("proxy P:", proxy["row"]["margin"], proxy["row"]["ci95"], "fires", proxy["fires"])


def _label_shas(args) -> dict:
    return {Path(p).name: _sha(Path(p)) for p in (args.buckets16, args.glue16, args.buckets512, args.glue512, args.groups,
                                                 args.balanced_groups) if p and Path(p).exists()}


# ---------------------------------------------------------------------------
# conclude-from
# ---------------------------------------------------------------------------

def verify_payload(path: Path, role: str, expect_stage: str | None = None) -> tuple[dict, list[dict]]:
    """One payload: a registered out name of its stage (and of the EXPECTED
    stage where the caller binds one: --lens is lens, --long readers_long, --s1
    s1) with the role-bound harvest, a clean tracked tree, the registry's
    readers and spaces, the registered n_boot, a state file whose sha, HEAD and
    row set match, riders of the stage's shape (the balanced rider alone in a
    lens payload, none in a readers payload) that recompute from the shuffled
    rows' histograms and passed. Returns (payload, cells)."""
    path = Path(path)
    p = json.loads(path.read_text(encoding="utf-8"))
    stage = p.get("stage")
    if stage not in REGISTERED_OUTS or path.name not in REGISTERED_OUTS[stage]:
        raise SystemExit(f"{path.name} is not a registered out of stage {stage!r} — refusing")
    if path.resolve().parent != Path(PAYLOAD_ROOT).resolve():
        raise SystemExit(f"{path} lies outside {PAYLOAD_ROOT} — a registered payload lives there and nowhere else; refusing")
    if expect_stage is not None and stage != expect_stage:
        raise SystemExit(f"{path.name} is a {stage} payload where a {expect_stage} payload is required — refusing")
    if ROLE_OF_OUT[path.name] != role or p.get("role") != role:
        raise SystemExit(f"{path.name} is the {ROLE_OF_OUT[path.name]} payload, read as {role} — refusing")
    if Path(p["harvest"]).name != HARVEST_OF_OUT[path.name]:
        raise SystemExit(f"{path.name} binds harvest {p['harvest']}, not {HARVEST_OF_OUT[path.name]} — refusing")
    if p.get("partial") or p.get("smoke_cell"):
        raise SystemExit(f"{path.name} is a partial / smoke payload — refusing")
    prov = p["provenance"]
    if prov["git_status_tracked"]:
        raise SystemExit(f"{path.name} was written over a dirty tracked tree — refusing")
    if prov["instrument_sha256"] != _sha(Path(__file__)):
        raise SystemExit(f"{path.name}: the instrument's bytes differ from the attested sha — refusing")
    exp_readers = STAGE_READERS[stage] if stage != "s1" else tuple(p["readers"])
    if tuple(p["readers"]) != tuple(exp_readers) or tuple(p["spaces"]) != stage_spaces(stage, p["tag"]):
        raise SystemExit(f"{path.name}: readers or spaces differ from the registry — refusing")
    if any(r not in READERS for r in p["readers"]):
        raise SystemExit(f"{path.name}: unknown reader in the payload — refusing")
    if int(prov["args"].get("n_boot", -1)) != N_BOOT:
        raise SystemExit(f"{path.name}: n_boot {prov['args'].get('n_boot')} is not the registered {N_BOOT} — refusing")
    riders = p.get("riders") or {}
    if stage == "lens" and set(riders) != {SPACE_L3_BAL}:
        raise SystemExit(f"{path.name}: a lens payload carries the balanced rider alone, got {sorted(riders)} — refusing")
    if stage != "lens" and riders:
        raise SystemExit(f"{path.name}: a {stage} payload carries no rider cells, got {sorted(riders)} — refusing")
    st = path.parent / prov["state_file"]
    if _sha(st) != prov["state_sha256"]:
        raise SystemExit(f"{path.name}: state file sha differs from its payload — refusing")
    header, rows = load_state(st, prov["harvest_npz_sha256"])
    if header.get("git_head") != prov["git_commit"] or header.get("out") != path.name:
        raise SystemExit(f"{path.name}: the state header's HEAD or out name differs from the payload — refusing")
    grid, _, _ = stage_grid(stage, p["tag"], tuple(p["readers"]))
    if set(rows) != grid_keys(grid):
        raise SystemExit(f"{path.name}: the state rows are not the stage's grid ({len(rows)} rows against {len(grid)}) — refusing")
    cells = list(rows.values())
    for sp, stored in riders.items():
        n_classes = int(next(c["n_classes"] for c in cells if c["shuffled"] and c["space"] == sp))
        re_rider = am.rider_check_amended(cells, sp, n_classes, n_boot=N_BOOT, expected_clusters=EXPECTED_CLUSTERS)
        if json.dumps(re_rider, sort_keys=True) != json.dumps(stored, sort_keys=True):
            raise SystemExit(f"{path.name}: the rider at {sp} does not recompute from the shuffled rows — refusing")
        if not (stored or {}).get("pass"):
            raise SystemExit(f"{path.name}: the rider at {sp} did not pass — refusing")
    return p, cells


def recompute_readouts(p: dict, cells: list[dict], data_root: Path = REAL) -> dict:
    p3_state = data_root / Path(p["provenance"]["args"]["phase3_state"]).name
    p3_payload = data_root / Path(p["provenance"]["args"]["phase3_payload"]).name
    p3 = load_phase3_cells(p3_state, p3_payload, p["provenance"]["harvest_npz_sha256"])
    lens_lin_a = [c for c in cells if c.get("reader") == "R0" and c["space"] == SPACE_L3_BAL and c["features"] == BASE_ARM
                  and c["capacity"] == "linear" and not c["shuffled"]]
    re_rs = {f"{r}|{sp}": readouts_for(cells, sp, r, p3, lens_lin_a, EXPECTED_CLUSTERS) for r in p["readers"] for sp in p["spaces"]}
    if json.dumps(re_rs, sort_keys=True) != json.dumps(p["per_reader_space"], sort_keys=True):
        raise SystemExit("conclude-from: per_reader_space does not reproduce from the state file — refusing")
    if p["stage"] == "lens":
        re_proxy = proxy_readout(cells, SPACE_L3_BAL, EXPECTED_CLUSTERS)
        if json.dumps(re_proxy, sort_keys=True) != json.dumps(p["proxy"], sort_keys=True):
            raise SystemExit("conclude-from: the proxy readout does not reproduce — refusing")
    return re_rs


def committed_l2_margin(p: dict, data_root: Path = REAL) -> float | None:
    """The committed Phase-3 L2 (c) - (a) linear off2 margin of the payload's harvest."""
    pay = json.loads((data_root / Path(p["provenance"]["args"]["phase3_payload"]).name).read_text(encoding="utf-8"))
    for m in pay.get("margins", []):
        if m["space"].startswith("L2_") and m["offset"] == GATE_OFFSET and m["capacity"] == "linear":
            return float(m["margin"])
    return None


def rerun_identity(stage_cells: list[dict], lens_cells: list[dict]) -> dict:
    """The three R0 linear (a) cells at the balanced lens, re-trained in a
    readers stage, against STAGE lens's proxy (a) rows: identical except
    runtime_s (the landing's determinism check, said in words, never a
    refusal)."""
    def pick(cells):
        return {c["cell"]: c for c in cells if c.get("reader") == "R0" and c["space"] == SPACE_L3_BAL
                and c["features"] == BASE_ARM and c["capacity"] == PROXY_CAP and not c["shuffled"] and c["offset"] == GATE_OFFSET}
    a, b = pick(stage_cells), pick(lens_cells)
    out = {}
    for cid in sorted(set(a) | set(b)):
        if cid not in a or cid not in b:
            out[cid] = {"identical": False, "missing_in": ("stage" if cid not in a else "lens")}
            continue
        diff = sorted(k for k in set(a[cid]) | set(b[cid]) if k != "runtime_s"
                      and json.dumps(a[cid].get(k), sort_keys=True) != json.dumps(b[cid].get(k), sort_keys=True))
        out[cid] = {"identical": not diff, "differing_fields": diff}
    return {"cells": out, "all_identical": bool(out) and all(v["identical"] for v in out.values()),
            "rule": "every field except runtime_s equal between the readers-stage row and the lens-stage row"}


def _check_admission(payload: dict, name: str, lens_pair) -> None:
    """A readers-stage payload admitted the balanced space on the two lens
    payloads whose shas it recorded; the --lens pair given must be those."""
    recorded = ((payload.get("balanced_admission") or {}).get("payloads") or {})
    for lpath in lens_pair:
        lpath = Path(lpath)
        if (recorded.get(lpath.name) or {}).get("sha256") != _sha(lpath):
            raise SystemExit(f"the {name} payload admitted the balanced space on a different {lpath.name} than the one given — refusing")


def labels_of_pair(pp: dict, rp: dict, offsets: tuple[int, ...], stronger: bool) -> dict:
    out = {}
    for key in pp["per_reader_space"]:
        out[key] = pair_label(pp["per_reader_space"][key], rp["per_reader_space"][key], offsets, stronger_word=stronger)
    return out


def conclude_from(primary: Path, replication: Path, long_pair: tuple[Path, Path] | None = None,
                  s1_pair: tuple[Path, Path] | None = None, lens_pair: tuple[Path, Path] | None = None,
                  data_root: Path = REAL) -> dict:
    """Mechanical labels from the payloads' state files, re-derived through the
    frozen rules; every payload verified and STAGE-BOUND (the pair's stage from
    its payloads; --lens must be lens, --long readers_long, --s1 s1); the K-2
    sentence is issued from a READERS pair only, over readers + readers_long
    (where given) with S1 where given, and REQUIRES the lens pair, whose shas
    must equal the readers payloads' recorded admission; the R0 linear (a)
    rerun identity per harvest comes with it. A readers_long or s1 pair alone
    yields labels only."""
    pp, pc = verify_payload(primary, "primary")
    rp, rc = verify_payload(replication, "replication")
    if pp["stage"] != rp["stage"]:
        raise SystemExit("payloads differ in stage — refusing")
    if pp["provenance"]["harvest_npz_sha256"] == rp["provenance"]["harvest_npz_sha256"]:
        raise SystemExit("the two payloads bind the SAME harvest — not a primary / replication pair")
    recompute_readouts(pp, pc, data_root)
    recompute_readouts(rp, rc, data_root)
    stage = pp["stage"]
    offsets = tuple(LENS_OFFSETS) if stage == "lens" else (GATE_OFFSET,)
    labels = labels_of_pair(pp, rp, offsets, stronger=(stage != "lens"))
    out: dict = {"stage": stage, "labels": labels, "materiality_floor": MATERIALITY,
                 "rule": "F-25's frozen rules per (reader, space); the registration block pins the stage words"}
    if stage == "lens":
        l2 = {"primary": committed_l2_margin(pp, data_root), "replication": committed_l2_margin(rp, data_root)}
        growth = {"primary": growth_reading(pp["proxy"], l2["primary"]), "replication": growth_reading(rp["proxy"], l2["replication"])}
        growth["combined"] = growth_combined(growth["primary"], growth["replication"])
        out["lens"] = {"proxy_label": lens_label(pp["proxy"], rp["proxy"]),
                       "proxy": {"primary": pp["proxy"], "replication": rp["proxy"]},
                       "f17_recorded_margins": F17_L3_MARGIN,
                       "ratio_to_f17": {role: ((d["proxy"]["row"]["margin"] / F17_L3_MARGIN[role]) if d["proxy"] else None)
                                        for role, d in (("primary", pp), ("replication", rp))},
                       "committed_l2_margin": l2, "growth_over_l2": growth,
                       "riders": {"primary": pp["riders"], "replication": rp["riders"]}}
    if stage == "readers":
        if not lens_pair:
            raise SystemExit("a readers conclusion requires --lens (the two lens payloads that admitted the balanced space)")
        lp, lc = verify_payload(lens_pair[0], "primary", expect_stage="lens")
        lr, lcr = verify_payload(lens_pair[1], "replication", expect_stage="lens")
        _check_admission(pp, "primary readers", lens_pair)
        _check_admission(rp, "replication readers", lens_pair)
        out["r0_linear_a_rerun"] = {"primary": rerun_identity(pc, lc), "replication": rerun_identity(rc, lcr)}
        trigger_cells = {k: v for k, v in labels.items() if k.split("|", 1)[1] in REOPEN_SPACES}
        out["readers_long_runs"] = not any(v["label"] in (LABEL_STRONGER, LABEL_SPLIT) for v in trigger_cells.values())
        all_labels = {tuple(k.split("|", 1)): v for k, v in labels.items()}
        if long_pair:
            lgp, lgc = verify_payload(long_pair[0], "primary", expect_stage="readers_long")
            lgr, lgcr = verify_payload(long_pair[1], "replication", expect_stage="readers_long")
            _check_admission(lgp, "primary readers_long", lens_pair)
            _check_admission(lgr, "replication readers_long", lens_pair)
            recompute_readouts(lgp, lgc, data_root)
            recompute_readouts(lgr, lgcr, data_root)
            long_labels = labels_of_pair(lgp, lgr, (GATE_OFFSET,), stronger=True)
            out["labels_readers_long"] = long_labels
            all_labels.update({tuple(k.split("|", 1)): v for k, v in long_labels.items()})
        s1 = None
        if s1_pair:
            sp_, sc = verify_payload(s1_pair[0], "primary", expect_stage="s1")
            sr_, scr = verify_payload(s1_pair[1], "replication", expect_stage="s1")
            recompute_readouts(sp_, sc, data_root)
            recompute_readouts(sr_, scr, data_root)
            s1_labels = labels_of_pair(sp_, sr_, (GATE_OFFSET,), stronger=True)
            out["labels_s1"] = s1_labels
            s1 = {k.split("|", 1)[0]: v for k, v in s1_labels.items()}
        out["k2"] = k2_sentence(all_labels, s1)
    elif stage in ("readers_long", "s1"):
        out["note"] = f"a {stage} pair alone yields labels; the K-2 sentence is issued from the readers pair with --long / --s1"
    print(json.dumps(out, indent=1, default=str)[:6000])
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=("lens", "readers", "readers_long", "s1"), default=None)
    ap.add_argument("--readers", default=None, help="s1 stage: comma-separated readers the block names")
    ap.add_argument("--harvest", default="results/real/harvest_moe")
    ap.add_argument("--space-tag", default=None, choices=("olmoe", "concept"))
    ap.add_argument("--n-slots", type=int, default=None)
    ap.add_argument("--buckets16", default=None)
    ap.add_argument("--glue16", default=None)
    ap.add_argument("--buckets512", default=None)
    ap.add_argument("--glue512", default=None)
    ap.add_argument("--groups", default=None)
    ap.add_argument("--balanced-groups", default=str(REAL / "concept_groups_olmoe_balanced_v1.json"))
    ap.add_argument("--fidelity", default=None)
    ap.add_argument("--phase3-state", default=None)
    ap.add_argument("--phase3-payload", default=None)
    ap.add_argument("--lens-payloads", nargs=2, default=None, metavar=("LENS_PRIMARY", "LENS_REPLICATION"),
                    help="readers stages: the committed STAGE lens payloads (their rider admits the balanced lens)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=THREADS)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--only", default=None, help="smoke only: comma-separated cell-id substrings (refused under results/)")
    ap.add_argument("--smoke-cell", default=None, help="smoke only: one cell READER|space|offset|arm|capacity|seed (refused under results/)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--conclude-from", nargs=2, default=None, metavar=("PRIMARY", "REPLICATION"))
    ap.add_argument("--long", nargs=2, default=None, metavar=("LONG_PRIMARY", "LONG_REPLICATION"))
    ap.add_argument("--s1", nargs=2, default=None, metavar=("S1_PRIMARY", "S1_REPLICATION"))
    ap.add_argument("--lens", nargs=2, default=None, metavar=("LENS_PRIMARY", "LENS_REPLICATION"),
                    help="conclude-from of a readers stage: the lens payloads, for the R0 linear (a) rerun identity")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.conclude_from:
        conclude_from(Path(args.conclude_from[0]), Path(args.conclude_from[1]),
                      tuple(Path(p) for p in args.long) if args.long else None,
                      tuple(Path(p) for p in args.s1) if args.s1 else None,
                      tuple(Path(p) for p in args.lens) if args.lens else None)
        return
    if args.smoke_cell and not args.stage:
        args.stage = "lens"                      # a smoke cell borrows the lens stage's bookkeeping
    if not args.stage or not args.out:
        raise SystemExit("--stage and --out are required for a run")
    run(args)


if __name__ == "__main__":
    main()

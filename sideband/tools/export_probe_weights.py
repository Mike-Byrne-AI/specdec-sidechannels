#!/usr/bin/env python3
"""K-3 stage-E probe-weight export (BLUEPRINT arc registration 2026-09-01;
stage-E clarifications E1/E7, 2026-09-02).

Retrains the FOUR committed Phase-3 cells the live scheduler deploys —
L1_concept_k16 | off{2,3} | {a,c} | linear | s0 (E1: seed 0, the standing
convention) — and REFUSES to export unless each retrain reproduces its
committed state cell bit-exactly (BINDING GATE: test_acc, per-cluster
counts, val_acc_best, best_epoch — the D2/D3-strengthened form). Weights
were never saved in Phase 3; retraining is seed-deterministic, and the
gate is what makes the export the audited object rather than a fresh one.

SELF-CHECK (E7): the exported weights, applied via
sideband.scheduler.LinearProbe (float32 logits -> float64 softmax) to
>= 1000 sampled committed-harvest anchors per cell, must reproduce the
full-eval pred EXACTLY and prob_max within 1e-5 (pinned tolerance for
CPU-vs-GPU op order), else the export refuses.

Output: results/real/k3_probe_weights.npz + .meta.json (committed
evidence; the meta binds the npz by sha and records the harvest binding,
tap parameters, and label-space shas the runner re-checks at load).

Run (GPU box):
    python tools/export_probe_weights.py
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import HarvestData, anchor_table, labels_for, train_probe  # noqa: E402
from sideband.scheduler import LinearProbe  # noqa: E402
from run_error_predictor import load_committed_cells_any  # noqa: E402
from run_probes import (REAL, bind_spaces_to_harvest, build_spaces,  # noqa: E402
                        cell_id, feature_blocks, space_names)

EXPORT_SEED = 0            # E1: the standing convention, pinned pre-choice
OFFSETS = (2, 3)
ARMS = ("a", "c")
SELF_CHECK_N = 1000        # per cell, E7
SELF_CHECK_PROB_TOL = 1e-5  # E7, pinned


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/k3_probe_weights.npz")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--overwrite", action="store_true",
                    help="results/ files are committed evidence; refusing is the default")
    args = ap.parse_args()

    out_path = Path(args.out)
    meta_path = out_path.with_suffix(".meta.json")
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists — committed evidence; pass --overwrite deliberately")

    data = HarvestData(args.harvest)
    data.row_split()
    bucket_paths = {f"buckets{k}": str(REAL / f"buckets_k{k}.json")
                    for k in ("16", "32", "64", "512")}
    bind_spaces_to_harvest(data.ref_meta, bucket_paths, n_slots=512)
    committed = load_committed_cells_any(Path(args.phase3_state),
                                         Path(args.phase3_payload), data.npz_shas)
    spaces = build_spaces(data)
    l1 = space_names("concept")["L1"]
    n_classes = spaces[l1]["n_classes"]

    arrays: dict[str, np.ndarray] = {}
    cell_records = []
    t0 = time.time()
    for arm in ARMS:
        for off in OFFSETS:
            cid = cell_id(l1, off, arm, "linear", EXPORT_SEED)
            want = committed.get(cid)
            if want is None:
                raise SystemExit(f"committed cell missing for {cid}")
            rows, anchors = anchor_table(data.lengths, off, data.tokens.shape[1])
            labels = labels_for(data.tokens, rows, anchors, off,
                                spaces[l1]["label_map"])
            split = data.row_split()[rows]
            blocks = feature_blocks(data, arm, rows, anchors, n_slots=512)
            res = train_probe(blocks, labels, split, n_classes, "linear",
                              EXPORT_SEED, args.device, full_eval=True,
                              return_weights=True)
            # BINDING GATE (E1): bit-exact reproduction of the committed cell.
            te_idx = np.nonzero(split == "test")[0]
            prompts_of_test = data.prompt_idx[rows[te_idx]]
            got_clusters = {int(p): [int(res["test_correct"][prompts_of_test == p].sum()),
                                     int((prompts_of_test == p).sum())]
                            for p in np.unique(prompts_of_test)}
            # Hard-indexed (critic advisory 2026-09-02): a committed cell
            # missing a gate field must KeyError, never weaken the gate.
            if (res["test_acc"] != want["test_acc"]
                    or got_clusters != want["_clusters"]
                    or res["val_acc_best"] != want["val_acc_best"]
                    or res["best_epoch"] != want["best_epoch"]):
                raise SystemExit(
                    f"BINDING GATE REFUSED at {cid}: retrain does not reproduce "
                    f"the committed cell (acc {res['test_acc']} vs {want['test_acc']}, "
                    f"val {res['val_acc_best']} vs {want['val_acc_best']}, "
                    f"epoch {res['best_epoch']} vs {want['best_epoch']}) — "
                    "instrument drift, refusing to export")
            W = res["weights"]["weight"].astype(np.float32)
            b = res["weights"]["bias"].astype(np.float32)
            arrays[f"W_{arm}_off{off}"] = W
            arrays[f"b_{arm}_off{off}"] = b
            # SELF-CHECK (E7): LinearProbe on sampled anchors reproduces
            # the full-eval pred exactly and prob_max within tolerance.
            probe = LinearProbe(W, b)
            rng = np.random.default_rng(0)
            worst = 0.0
            n_checked = 0
            for splitname in ("train", "val", "test"):
                f = res["full"][splitname]
                take = min(SELF_CHECK_N, len(f["idx"]))
                pick = rng.choice(len(f["idx"]), size=take, replace=False)
                X = np.concatenate([blk.batch(f["idx"][pick]) for blk in blocks], axis=1)
                for i, row in enumerate(pick):
                    cls, conf = probe(X[i])
                    if cls != int(f["pred"][row]):
                        raise SystemExit(
                            f"EXPORT SELF-CHECK FAILED at {cid} ({splitname} anchor "
                            f"{int(f['idx'][row])}): pred {cls} != full-eval "
                            f"{int(f['pred'][row])}")
                    dev = abs(conf - float(f["prob_max"][row]))
                    worst = max(worst, dev)
                    if dev > SELF_CHECK_PROB_TOL:
                        raise SystemExit(
                            f"EXPORT SELF-CHECK FAILED at {cid}: prob_max deviation "
                            f"{dev:.2e} > {SELF_CHECK_PROB_TOL}")
                    n_checked += 1
            cell_records.append({
                "cell": cid, "arm": arm, "offset": off,
                "binding_gate": "PASS",
                "test_acc": res["test_acc"], "val_acc_best": res["val_acc_best"],
                "best_epoch": res["best_epoch"],
                "W_shape": list(W.shape),
                "self_check_n": n_checked,
                "self_check_worst_prob_dev": worst,
            })
            print(f"[export] {cid}: gate PASS, self-check {n_checked} anchors "
                  f"worst prob dev {worst:.2e}", flush=True)

    np.savez(out_path, **arrays)

    def _git() -> str:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True, timeout=10)
            d = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10)
            return (r.stdout.strip() or "unknown") + ("-dirty" if d.stdout.strip() else "")
        except Exception:
            return "unknown"

    import torch
    ref = data.ref_meta
    meta = {
        "registered": "K-3 stage-E probe export (arc registration 2026-09-01; "
                      "clarifications E1/E7 2026-09-02); export seed 0, binding "
                      "gate bit-exact vs committed Phase-3 cells",
        "npz_file": out_path.name,
        "npz_sha256": _sha(out_path),
        "cells": cell_records,
        "space": l1, "n_classes": n_classes,
        "glue_class": n_classes - 1,
        "export_seed": EXPORT_SEED,
        "self_check_prob_tol": SELF_CHECK_PROB_TOL,
        # E12(ii): the harvest temperature the probes' features assume; the
        # runner refuses an instruments-on run at any other temperature.
        "harvest_temperature": float(ref["temperature"]),
        "harvest_npz_sha256": data.npz_shas,
        "phase3_state_sha256": _sha(Path(args.phase3_state)),
        "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
        "label_space_sha256": {Path(p).name: _sha(Path(p)) for p in
                               list(bucket_paths.values())
                               + [str(REAL / "glue_k16.json")]},
        # Tap parameters the live runner must reproduce EXACTLY (the live
        # tap binds to these at startup — same sketches or refuse).
        "tap": {k: ref[k] for k in ("layer_regex", "layers", "n_slots", "top_n",
                                    "sketch_seed", "layer_names",
                                    "sketch_layer_seeds", "model", "target_load")},
        "buckets_sha256": {k: ref.get(f"{k}_sha256") for k in bucket_paths},
        "torch_version": torch.__version__,
        "device": args.device,
        "git_commit": _git(),
        "runtime_s": round(time.time() - t0, 1),
    }
    meta_path.write_text(json.dumps(meta, indent=1, sort_keys=True))
    print(f"[export] 4 cells -> {out_path} (+ meta); runtime {meta['runtime_s']}s")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""D2/D3 diagnostics for the K-3 Attempt #1 arc (BLUEPRINT registration
2026-09-01, incl. the dated pre-run clarifications; NON-CRITERION —
nothing here can amend F-15..F-18).

D2 = OQ-14(ii) error-predictor heads: for each (space, offset in {2,3},
arm in {a, c}, seed in {0,1,2}), retrain the committed Phase-3 LINEAR
base probe (BINDING GATE: the retrain must reproduce the committed
state cell — test_acc and per-cluster counts — bit-exactly, else this
tool REFUSES), then train a LINEAR head on the base arm's own features
predicting the base probe's per-anchor correctness (train split only).
Readouts: precision/coverage curves at {0.05..0.50 step 0.05} on VAL
and TEST, both arms symmetrically (OQ-14 guardrail).

D3 = OQ-14(iii) calibration: reliability curves (10 equal-width bins)
+ ECE for the base probes' max-softmax confidence, same splits.

Decision block (mechanical, per the dated clarifications): PER-ARM cell
selection — each arm selects its (space, offset) by the MEAN over head
seeds of VAL precision at coverage 0.20 exactly; ties break to lower
offset, then space order L1 < L2 < L3; the selected cell's TEST curve
is reported and the selection is inherited regardless. Signal form per
arm: D2 head by default, swapped to the base probe's raw posterior iff
the selected cell's test-split ECE (mean over seeds) <= 0.05.

Run (GPU box):
    python tools/run_error_predictor.py --out results/real/error_predictor_s1.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.provenance import redact_args  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sideband.probes import (HarvestData, anchor_table, labels_for,  # noqa: E402
                             train_probe)
from run_probes import (REAL, bind_spaces_to_harvest, build_spaces,  # noqa: E402
                        cell_id, feature_blocks, normalize_clusters,
                        parse_state, space_names, state_header)

OFFSETS = (2, 3)
SEEDS = (0, 1, 2)
ARMS = ("a", "c")
COVERAGES = tuple(round(0.05 * k, 2) for k in range(1, 11))  # 0.05..0.50
SELECT_COVERAGE = 0.20
ECE_SWAP_MAX = 0.05
N_ECE_BINS = 10


def _sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


def clusters_of(test_correct: np.ndarray, prompts_of_test: np.ndarray) -> dict:
    """Per-prompt [n_correct, n_total] — byte-compatible with run_cell's
    _clusters (the binding-gate comparison target)."""
    return {int(p): [int(test_correct[prompts_of_test == p].sum()),
                     int((prompts_of_test == p).sum())]
            for p in np.unique(prompts_of_test)}


def load_committed_cells_any(state_path: Path, payload_path: Path,
                             npz_shas: dict) -> dict[str, dict]:
    """Headerless-tolerant loader (the original probes_s1 state predates
    the sha header): binds through the payload's provenance shas, the
    same legacy chain run_posthoc_topic uses."""
    lines = state_path.read_text().splitlines()
    first = json.loads(lines[0])
    if isinstance(first, dict) and first.get("kind") == "state_header":
        if first.get("harvest_npz_sha256") != npz_shas:
            raise SystemExit("phase-3 state header binds a DIFFERENT harvest")
        body = lines[1:]
    else:
        payload = json.loads(payload_path.read_text())
        if payload.get("provenance", {}).get("harvest_npz_sha256") != npz_shas:
            raise SystemExit("phase-3 payload provenance binds a DIFFERENT "
                             "harvest (legacy headerless state file)")
        body = lines
    out = {}
    for ln in body:
        if ln.strip():
            c = normalize_clusters(json.loads(ln))
            out[c["cell"]] = c
    return out


def p_correct(full_split: dict) -> np.ndarray:
    """Head's P(base correct) per anchor from a binary head's outputs."""
    pm, pred = full_split["prob_max"], full_split["pred"]
    return np.where(pred == 1, pm, 1.0 - pm)


def precision_at(cov: float, score: np.ndarray, correct: np.ndarray) -> float:
    """Precision among the top-cov fraction ranked by score (desc);
    deterministic tie-break by anchor index (stable argsort)."""
    n = len(score)
    k = max(1, int(np.ceil(cov * n)))
    order = np.argsort(-score, kind="stable")[:k]
    return float(correct[order].mean())


def ece_of(conf: np.ndarray, correct: np.ndarray, n_bins: int = N_ECE_BINS) -> dict:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = np.clip(np.digitize(conf, edges[1:-1]), 0, n_bins - 1)
    rows, ece = [], 0.0
    for b in range(n_bins):
        m = bins == b
        n = int(m.sum())
        if n == 0:
            rows.append({"bin": b, "n": 0})
            continue
        acc, mc = float(correct[m].mean()), float(conf[m].mean())
        ece += abs(acc - mc) * n / len(conf)
        rows.append({"bin": b, "n": n, "conf": mc, "acc": acc})
    return {"ece": float(ece), "bins": rows}


def selection_key(stats: dict, space_order: list):
    """The registered selection order for a (space, offset) cell: highest mean VAL precision,
    ties to the lower offset, then to the earlier space in space_order (L1 before L2 before L3).
    Module-level since 2026-10-16 (lane C of the 2026-10-15 image audit, item S6a-C-5) so
    tests/test_probes.py calls the key the tool uses instead of re-typing it; the tuple is the
    one the decision block has used since the registration."""
    return lambda k: (stats[k], -k[1], -space_order.index(k[0]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default="results/real/harvest_shadow")
    ap.add_argument("--phase3-state", default="results/real/probes_s1.json.state.jsonl")
    ap.add_argument("--phase3-payload", default="results/real/probes_s1.json")
    ap.add_argument("--out", default="results/real/error_predictor_s1.json")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="substring filter (smoke)")
    args = ap.parse_args()

    if args.only and Path(args.out).resolve() == (REAL / "error_predictor_s1.json").resolve():
        raise SystemExit("--only smoke runs may not write the registered out path")

    data = HarvestData(args.harvest)
    data.row_split()
    bind_spaces_to_harvest(data.ref_meta,
                           {"buckets16": str(REAL / "buckets_k16.json"),
                            "buckets512": str(REAL / "buckets_k512.json")},
                           n_slots=512)
    committed = load_committed_cells_any(Path(args.phase3_state),
                                         Path(args.phase3_payload), data.npz_shas)
    spaces = build_spaces(data)
    names = space_names("concept")
    space_order = [names["L1"], names["L2"], names["L3"]]

    state_path = Path(args.out + ".state.jsonl")
    done: dict[str, dict] = {}
    if state_path.exists():
        done = parse_state(state_path.read_text(), data.npz_shas)
        print(f"[resume] {len(done)} cells already done")
    else:
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    cells = []
    grid = [(sp, off, arm, seed) for sp in space_order for off in OFFSETS
            for arm in ARMS for seed in SEEDS]
    for i, (sp, off, arm, seed) in enumerate(grid):
        cid = "D2|" + cell_id(sp, off, arm, "linear", seed)
        if args.only and args.only not in cid:
            continue
        if cid in done:
            cells.append(done[cid])
            continue
        t_cell = time.time()
        rows, anchors = anchor_table(data.lengths, off, data.tokens.shape[1])
        labels = labels_for(data.tokens, rows, anchors, off,
                            spaces[sp]["label_map"])
        split = data.row_split()[rows]
        blocks = feature_blocks(data, arm, rows, anchors, n_slots=512)
        base = train_probe(blocks, labels, split, spaces[sp]["n_classes"],
                           "linear", seed, args.device, full_eval=True)
        # BINDING GATE: bit-exact reproduction of the committed cell.
        want = committed.get(cell_id(sp, off, arm, "linear", seed))
        if want is None:
            raise SystemExit(f"committed cell missing for {cid}")
        te_idx = np.nonzero(split == "test")[0]
        prompts_of_test = data.prompt_idx[rows[te_idx]]
        got_clusters = clusters_of(base["test_correct"], prompts_of_test)
        if (base["test_acc"] != want["test_acc"]
                or got_clusters != want["_clusters"]
                or base["val_acc_best"] != want.get("val_acc_best", base["val_acc_best"])
                or base["best_epoch"] != want.get("best_epoch", base["best_epoch"])):
            raise SystemExit(
                f"BINDING GATE REFUSED at {cid}: retrained base probe does "
                f"not reproduce the committed cell (acc {base['test_acc']} vs "
                f"{want['test_acc']}, val {base['val_acc_best']} vs "
                f"{want.get('val_acc_best')}, epoch {base['best_epoch']} vs "
                f"{want.get('best_epoch')}) — instrument drift, do not proceed")
        # D2 head: correctness labels over ALL anchors from the base full eval.
        y_head = np.zeros(len(rows), dtype=np.int64)
        for s in ("train", "val", "test"):
            f = base["full"][s]
            y_head[f["idx"]] = f["correct"].astype(np.int64)
        head = train_probe(blocks, y_head, split, 2, "linear", seed,
                           args.device, full_eval=True)
        rec = {"cell": cid, "space": sp, "offset": off, "arm": arm,
               "seed": seed, "base_test_acc": base["test_acc"],
               "binding_gate": "PASS",
               "head_test_acc": head["test_acc"],
               "runtime_s": round(time.time() - t_cell, 1)}
        for splitname in ("val", "test"):
            bf, hf = base["full"][splitname], head["full"][splitname]
            score = p_correct(hf)
            rec[f"{splitname}_precision_at"] = {
                str(c): precision_at(c, score, bf["correct"]) for c in COVERAGES}
            rec[f"{splitname}_base_rate"] = float(bf["correct"].mean())
            rec[f"{splitname}_ece"] = ece_of(bf["prob_max"], bf["correct"])
        # state cells carry no _clusters (no bootstrap here); keep the
        # header binding + full curves as the recomputable record.
        cells.append(rec)
        with state_path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[{i + 1}/{len(grid)}] {cid}: base {base['test_acc']:.4f} "
              f"head {head['test_acc']:.4f} "
              f"p@.2 val {rec['val_precision_at']['0.2']:.4f}", flush=True)

    # Decision block — mechanical, per the dated pre-run clarifications.
    decision = {}
    expected = None if args.only else len(grid)
    if len(cells) == expected:
        for arm in ARMS:
            stats = {}
            for sp in space_order:
                for off in OFFSETS:
                    sel = [c for c in cells if c["arm"] == arm
                           and c["space"] == sp and c["offset"] == off]
                    stats[(sp, off)] = float(np.mean(
                        [c["val_precision_at"][str(SELECT_COVERAGE)] for c in sel]))
            best = max(stats, key=selection_key(stats, space_order))
            sel_cells = [c for c in cells if c["arm"] == arm
                         and c["space"] == best[0] and c["offset"] == best[1]]
            test_ece = float(np.mean([c["test_ece"]["ece"] for c in sel_cells]))
            decision[arm] = {
                "selected_space": best[0], "selected_offset": best[1],
                "val_precision_at_020_mean": stats[best],
                "test_precision_at_020_mean": float(np.mean(
                    [c["test_precision_at"][str(SELECT_COVERAGE)] for c in sel_cells])),
                "test_base_rate_mean": float(np.mean(
                    [c["test_base_rate"] for c in sel_cells])),
                "test_ece_mean": test_ece,
                "signal_form": ("raw_posterior" if test_ece <= ECE_SWAP_MAX
                                else "d2_head"),
                "rule": "per-arm selection, mean-over-seeds VAL precision at "
                        "coverage 0.20, ties to lower offset then L1<L2<L3; "
                        "ECE swap at test mean <= 0.05 (dated pre-run "
                        "clarifications, 2026-09-01)"}
    else:
        decision = {"label": "INCOMPLETE(partial)"}

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
    payload = {
        "registered": "D2/D3 diagnostics (K-3 Attempt #1 arc, BLUEPRINT "
                      "2026-09-01, incl. dated pre-run clarifications); "
                      "NON-CRITERION — cannot amend F-15..F-18",
        "n_cells": len(cells), "partial": bool(args.only),
        "cells": cells, "decision": decision,
        "provenance": {
            "git_commit": _git(), "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "phase3_state_sha256": _sha(Path(args.phase3_state)),
            "phase3_payload_sha256": _sha(Path(args.phase3_payload)),
            "coverages": list(COVERAGES), "select_coverage": SELECT_COVERAGE,
            "ece_swap_max": ECE_SWAP_MAX, "n_ece_bins": N_ECE_BINS,
            "torch_version": torch.__version__,
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, indent=1))
    print(f"[D2/D3] decision: { {a: d.get('signal_form') for a, d in decision.items() if isinstance(d, dict)} } -> {args.out}")


if __name__ == "__main__":
    main()

"""OQ-18 LEAK-RIDER POSITIVE CONTROL (docs/OQ18_RIDER_POSCONTROL.md,
registered 2026-09-13 before any control cell trained; proposed by the
pre-commit critic round on the 2026-09-07 rider amendment).

Does the AMENDED leg (twin-referenced dependence excess, docs/
OQ18_RIDER_DIAGNOSTIC.md) actually FIRE on a literal non-causal block of
the modality the rider guards? fplus_leak = fplus ++ the same row's slots
block read at the shuffled label's OWN position li = (a + off - 1 +
SHUFFLE_SHIFT) mod length[row] — the exact index labels_for() uses — equal
dims with fplus_b / fplus_r. One linear cell per space at off2 / seed 0
with the prediction dump; the reference rows (shuffled a / fplus /
fplus_b / fplus_r at seed 0) are the diagnostic's own, reused from its
state file (same labels, split and wrap flags, so the histograms pair
exactly). Statistics: run_oq18_rider_diag.excess_stats with the leak cell
in the aligned arm's seat (key fplus_b; the cell's features field says
fplus_leak), so "fplus_b-fplus" is the registered raw leg 2 applied to the
leak and "fplus_b-fplus_r" the amended leg applied to it. Verdict rules
pinned in the registration document. Nothing here reads an OQ-18 label.
GPU box only; nothing in CI imports torch through this file's helpers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.provenance import redact_args  # noqa: E402
from sideband.harvest import label_index  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_oq18_rider_diag as rd  # noqa: E402
from run_probes import (REAL, SHUFFLE_SHIFT, SlotsAnchorBlock, bind_spaces_to_harvest,  # noqa: E402
                        build_spaces, cell_id, parse_state, state_header)
from run_fullfree import _sha, _same_path  # noqa: E402
from run_fullfree_coarse import (SEEDS, GATE_OFFSET, REGISTERED_OUTS, make_factories,  # noqa: E402
                                 committed_moments_sha)

REGISTRATION_DOC = Path(__file__).resolve().parent.parent / "docs" / "OQ18_RIDER_POSCONTROL.md"
POS_OUT = "results/real/oq18_rider_poscontrol_s1.json"
LEAK_ARM = "fplus_leak"
SEAT_ARM = "fplus_b"                     # the leak cell sits in the aligned arm's seat for the statistics
REFERENCE_ARMS = ("a", "fplus", "fplus_b", "fplus_r")
CONTROL_SPACES = (rd.SPACE_L3, rd.SPACE_L2)
CONTROL_SEED = 0
CAPACITY = "linear"
PAIR_RAW = "fplus_b-fplus"               # = raw leg 2 applied to the leak (leak - fplus)
PAIR_AMENDED = "fplus_b-fplus_r"         # = the amended leg applied to the leak (leak - fplus_r)
V_CONFIRMED = "DOMINANCE-CONFIRMED-HERE"
V_FALSIFIED = "DOMINANCE-FALSIFIED"
V_PARTIAL = "PARTIAL"
V_UNINFORMATIVE = "UNINFORMATIVE"
V_INCOMPLETE = "INCOMPLETE"


# ---------------------------------------------------------------------------
# The leak block
# ---------------------------------------------------------------------------

def leak_anchors(anchors: np.ndarray, rows: np.ndarray, lengths: np.ndarray,
                 offset: int = GATE_OFFSET, shift: int = SHUFFLE_SHIFT) -> np.ndarray:
    """The shuffled label's own position for every anchor: (label_index(a,
    off) + shift) mod length[row] — byte-for-byte the index labels_for()
    reads the shuffled label from."""
    li = np.array([label_index(int(a), offset) for a in anchors], dtype=np.int64)
    return (li + shift) % lengths[rows]


def make_leak_factory(fplus_factory, slots: np.ndarray, lengths: np.ndarray, n_slots: int,
                      offset: int = GATE_OFFSET, shift: int = SHUFFLE_SHIFT):
    """fplus's extras (TOK, hz) followed by the slots block at the leak
    anchors: the same block class and order as fplus_b, other position."""
    def fplus_leak(rows, anchors):
        la = leak_anchors(np.asarray(anchors), np.asarray(rows), lengths, offset, shift)
        return list(fplus_factory(rows, anchors)) + [SlotsAnchorBlock(slots, rows, la, n_slots)]
    return fplus_leak


# ---------------------------------------------------------------------------
# Readouts and verdict (pinned)
# ---------------------------------------------------------------------------

def space_readout(ref: dict[str, dict], leak: dict, n_classes: int, sel: str = "all",
                  n_boot: int = rd.N_BOOT, expected_clusters: int | None = rd.EXPECTED_CLUSTERS,
                  band: float = rd.BAND, material: float = rd.MATERIAL) -> dict:
    """excess_stats with the leak cell in the aligned arm's seat; the raw
    and amended legs applied to it; the flags the verdict reads."""
    if leak.get("features") != LEAK_ARM:
        raise SystemExit(f"leak cell has features {leak.get('features')!r}, not {LEAK_ARM!r}")
    for arm in REFERENCE_ARMS:
        if arm not in ref or "_hist" not in ref[arm]:
            raise SystemExit(f"reference row {arm} missing or without histograms")
    if "_hist" not in leak:
        raise SystemExit("leak cell carries no histograms")
    seated = {"a": [ref["a"]], "fplus": [ref["fplus"]], SEAT_ARM: [leak], "fplus_r": [ref["fplus_r"]]}
    st = rd.excess_stats(seated, n_classes, sel, n_boot, rd.BOOT_SEED, expected_clusters)
    raw = st["pairs"][PAIR_RAW]
    twin = st["pairs"][PAIR_AMENDED]
    leg = rd.amended_leg(twin, band, material)
    arms = {("fplus_leak" if a == SEAT_ARM else a): v for a, v in st["arms"].items()}
    out = {
        "selection": sel, "n_prompts": st["n_prompts"], "n_anchors": st["n_anchors"],
        "n_boot": st["n_boot"], "boot_seed": st["boot_seed"],
        "majority_label": st["majority_label"], "label_majority_rate": st["label_majority_rate"],
        "arms": arms,
        "pairs": {"fplus_leak-fplus": raw, "fplus_leak-fplus_r": twin,
                  **({"fplus-a": st["pairs"]["fplus-a"]} if "fplus-a" in st["pairs"] else {})},
        "raw_leak": float(raw["d_acc"]), "raw_leak_ci95": raw.get("ci95_d_acc"),
        "dE_leak_f": float(raw["d_E"]), "dE_leak_f_ci95": raw.get("ci95_d_E"),
        "dE_leak_r": float(twin["d_E"]), "dE_leak_r_ci95": twin.get("ci95_d_E"),
        "X_leak": float(twin["d_acc"]), "X_leak_ci95": twin.get("ci95_d_acc"),
        "amended_leg": leg,
        "amended_fires": bool(leg["fails"]),
        "raw_fires": bool(raw["d_acc"] > band),
        "band": band, "material": material,
    }
    return out


def aligned_reference(ref: dict[str, dict], n_classes: int, sel: str = "all",
                      n_boot: int = rd.N_BOOT, expected_clusters: int | None = rd.EXPECTED_CLUSTERS) -> dict:
    """The diagnostic's own seed-0 aligned numbers beside the leak's: E(fplus_b)
    and dE_br, recomputed from the same reference rows."""
    st = rd.excess_stats({a: [ref[a]] for a in REFERENCE_ARMS}, n_classes, sel, n_boot,
                         rd.BOOT_SEED, expected_clusters)
    return {"E_fplus_b": st["arms"]["fplus_b"]["E"], "E_fplus_b_ci95": st["arms"]["fplus_b"].get("ci95_E"),
            "dE_br": st["pairs"][rd.PAIR_TWIN]["d_E"], "dE_br_ci95": st["pairs"][rd.PAIR_TWIN].get("ci95_d_E"),
            "leg2_raw": st["pairs"][rd.PAIR_LEG2_RAW]["d_acc"]}


def verdict(flags: dict[str, dict], spaces: tuple[str, ...] = CONTROL_SPACES) -> dict:
    """flags[space] = {"amended_fires": bool, "raw_fires": bool}; the pinned
    rule of docs/OQ18_RIDER_POSCONTROL.md."""
    missing = [sp for sp in spaces if sp not in flags]
    if missing:
        return {"verdict": V_INCOMPLETE, "reason": f"control cell missing at {missing}", "per_space": flags}
    falsified = [sp for sp in spaces if flags[sp]["raw_fires"] and not flags[sp]["amended_fires"]]
    fired = [sp for sp in spaces if flags[sp]["amended_fires"]]
    if falsified:
        v, why = V_FALSIFIED, f"raw leg fires and the amended leg does not at {falsified}"
    elif len(fired) == len(spaces):
        v, why = V_CONFIRMED, "the amended leg fires at both spaces"
    elif fired:
        v, why = V_PARTIAL, f"the amended leg fires at {fired} only; no falsification"
    else:
        v, why = V_UNINFORMATIVE, "neither leg fires at either space"
    return {"verdict": v, "reason": why, "per_space": flags,
            "consequence": ("the 2026-09-07 amendment is WITHDRAWN by a dated note before any amended "
                            "cell trains; S1 stays label-less; S3 concludes under the frozen instrument"
                            if v == V_FALSIFIED else "the amended runs proceed")}


# ---------------------------------------------------------------------------
# CLI and guards
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = rd.build_parser()
    ap.set_defaults(out=POS_OUT)
    ap.add_argument("--diag-payload", default=rd.DIAG_OUT)
    return ap


def check_out(out: str, only: str | None) -> tuple[Path, bool]:
    out_path = Path(out).resolve()
    if out_path.name in REGISTERED_OUTS or _same_path(out, rd.DIAG_OUT):
        raise SystemExit(f"{out} is a registered OQ-18 out path — the control never writes it")
    registered = _same_path(out, POS_OUT)
    if only and registered:
        raise SystemExit("--only smoke runs may not write the registered control out path")
    return out_path, registered


def load_diagnostic(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"diagnostic payload {p} missing — the control pairs with its rows")
    d = json.loads(p.read_text())
    if d.get("partial") or (d.get("verdict") or {}).get("branch") != rd.BRANCH_B:
        raise SystemExit("the control is registered under the diagnostic's AMENDABLE verdict only")
    return d


def reference_rows(state_rows: dict[str, dict], diag_payload: dict, space: str,
                   seed: int = CONTROL_SEED) -> dict[str, dict]:
    """The diagnostic's seed-0 rows for the four reference arms, tied to the
    committed payload's cell entries (test_acc equality)."""
    by_id = {c["cell"]: c for c in diag_payload["cells"]}
    ref = {}
    for arm in REFERENCE_ARMS:
        cid = cell_id(space, GATE_OFFSET, arm, CAPACITY, seed, True)
        row = state_rows.get(cid)
        if row is None or "_hist" not in row:
            raise SystemExit(f"diagnostic state row {cid} missing or without histograms")
        if cid not in by_id or float(by_id[cid]["test_acc"]) != float(row["test_acc"]):
            raise SystemExit(f"diagnostic state row {cid} does not match the committed payload's cell")
        ref[arm] = row
    return ref


def _git() -> tuple[str, list[str]]:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, timeout=10)
        lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
        return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
    except Exception:  # noqa: BLE001
        return "unknown", []


def main() -> None:
    args = build_parser().parse_args()
    out_path, registered = check_out(args.out, args.only)
    if not REGISTRATION_DOC.exists():
        raise SystemExit(f"{REGISTRATION_DOC} missing — refusing to run an unregistered control")
    reg_sha = _sha(REGISTRATION_DOC)
    if not _same_path(args.harvest, rd.DIAG_HARVEST):
        raise SystemExit("the control is registered on the S1 primary harvest only")
    state_path = Path(args.out + ".state.jsonl")
    if registered and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a crashed run")
    diag = load_diagnostic(args.diag_payload)
    diag_state = Path(args.diag_payload + ".state.jsonl")
    if not diag_state.exists():
        raise SystemExit(f"{diag_state} missing")

    data = rd.HarvestData(args.harvest)
    split_names = data.row_split()
    bind_spaces_to_harvest(data.ref_meta, {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)
    spaces = build_spaces(data, tag="concept", buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512, groups_path=args.groups)
    for sp in CONTROL_SPACES:
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built")
    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    moments = rd.train_moments(hidden, data.lengths, split_names)
    if committed_moments_sha(args.harvest) != moments["sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's — refusing")
    perms = {seed: rd.derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    base = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments, perms)
    leak_factory = make_leak_factory(base[("fplus", CONTROL_SEED)], slots, data.lengths, args.n_slots)
    factory_of = {(LEAK_ARM, CONTROL_SEED): leak_factory}
    # equal dims with the aligned arm, checked on a small anchor sample
    rows0, anchors0 = rd.anchor_table(data.lengths, GATE_OFFSET, data.tokens.shape[1])
    probe_rows, probe_anchors = rows0[:8], anchors0[:8]
    dim_leak = sum(b.dim for b in leak_factory(probe_rows, probe_anchors))
    dim_b = sum(b.dim for b in base[("fplus_b", CONTROL_SEED)](probe_rows, probe_anchors))
    if dim_leak != dim_b:
        raise SystemExit(f"leak arm dims {dim_leak} != aligned arm dims {dim_b} — refusing")

    state_rows = {k: rd.normalize_hist(v) for k, v in parse_state(diag_state.read_text(), data.npz_shas).items()}
    refs = {sp: reference_rows(state_rows, diag, sp) for sp in CONTROL_SPACES}

    done: dict[str, dict] = {}
    if state_path.exists():
        done = {k: rd.normalize_hist(v) for k, v in parse_state(state_path.read_text(), data.npz_shas).items()}
        print(f"[resume] {len(done)} cells already done", flush=True)
    else:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    grid = [(sp, GATE_OFFSET, LEAK_ARM, CAPACITY, CONTROL_SEED, True) for sp in CONTROL_SPACES]
    cells: list[dict] = []
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if not rd.only_match(args.only, cid):
            continue
        if cid in done:
            cells.append(done[cid])
            continue
        res = rd.run_cell_diag(data, spaces, sp, off, arm, seed, args.device, factory_of, args.n_slots)
        cells.append(res)
        with state_path.open("a") as f:
            f.write(json.dumps(res) + "\n")
        print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} (maj "
              f"{res['majority_rate_test']:.4f}, q_maj {res['q_majority']:.4f}, epoch {res['best_epoch']}) "
              f"{res['runtime_s']}s total {time.time() - t0:.0f}s", flush=True)

    expected = None if args.only else rd.EXPECTED_CLUSTERS
    per_space: dict = {}
    flags: dict = {}
    for sp in CONTROL_SPACES:
        leak = next((c for c in cells if c["space"] == sp), None)
        if leak is None:
            continue
        n_classes = int(spaces[sp]["n_classes"])
        entry = {sel: space_readout(refs[sp], leak, n_classes, sel, args.n_boot, expected) for sel in rd.SELECTIONS}
        entry["aligned_reference"] = aligned_reference(refs[sp], n_classes, "all", args.n_boot, expected)
        per_space[sp] = entry
        flags[sp] = {"amended_fires": entry["all"]["amended_fires"], "raw_fires": entry["all"]["raw_fires"],
                     "dE_leak_r": entry["all"]["dE_leak_r"], "dE_leak_r_ci95": entry["all"]["dE_leak_r_ci95"],
                     "raw_leak": entry["all"]["raw_leak"], "E_leak": entry["all"]["arms"]["fplus_leak"]["E"]}
    v = verdict(flags)
    v["partial"] = bool(args.only)

    git_commit, git_porcelain = _git()
    import torch
    payload = {
        "registered": ("OQ-18 LEAK-RIDER POSITIVE CONTROL (docs/OQ18_RIDER_POSCONTROL.md, 2026-09-13, "
                       "before any control cell trained)"),
        "registration_sha256": reg_sha,
        "harvest": args.harvest,
        "shift": int(SHUFFLE_SHIFT),
        "construction": ("fplus_leak = fplus ++ SlotsAnchorBlock at li = (label_index(a, off) + shift) "
                         "mod length[row]; statistics with the leak cell in the fplus_b seat"),
        "n_cells": len(cells),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),
        "cells": [{k: v_ for k, v_ in c.items() if k != "_hist"} for c in cells],
        "reference_rows": {sp: {a: {k: v_ for k, v_ in r.items() if k != "_hist"} for a, r in refs[sp].items()}
                           for sp in refs},
        "per_space": per_space,
        "verdict": v,
        "diagnostic": {"payload": args.diag_payload, "payload_sha256": _sha(Path(args.diag_payload)),
                       "state_sha256": _sha(diag_state), "registration_sha256": diag.get("registration_sha256"),
                       "branch": diag["verdict"]["branch"], "mechanism": diag["verdict"]["mechanism"]},
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "instrument_sha256": _sha(Path(__file__)),
            "diag_instrument_sha256": _sha(Path(rd.__file__)),
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "arm_dims": {"fplus_leak": int(dim_leak), "fplus_b": int(dim_b)},
            "state_file": str(state_path),
            "torch": torch.__version__,
            "cuda": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1))
    print(json.dumps({"verdict": v, "per_space": {sp: {k: flags[sp][k] for k in flags[sp]} for sp in flags}},
                     indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

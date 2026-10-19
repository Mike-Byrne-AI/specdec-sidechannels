#!/usr/bin/env python
"""OQ-18 LEAK-RIDER DIAGNOSTIC — the registered post-hoc diagnosis of the
leak-rider fire at S1 L3 (docs/OQ18_RIDER_DIAGNOSTIC.md, registered
2026-09-07 before any diagnostic cell trained; this tool records that
document's sha256 in its payload and refuses to run without it).

WHAT FIRED. The registered S1 primary run of OQ-18 (freeze 15c4e9c) halted
at cell 36/66 on LEAK RIDER leg 2 at L3_concept_groups_v1: shuffled fplus_b
0.5314 > shuffled fplus 0.5182 + 0.01. The "shuffle" is the registered
17-position circular label shift within the row (SHUFFLE_SHIFT); leg 2 is
dims-asymmetric (fplus_b against fplus) and has no equal-dims twin, and
both arms sit far below the majority rate — so the fire can be
prediction-marginal drift, prompt-independent position / occupancy
information the corrected twin shares, or CONTENT TRANSFER (a pipeline
leak or persistent row-level topic information the twin lacks — not
separable by this instrument, which is a position-specificity test of
the aligned block at the shifted label, not a pipeline-leak test; the
registered rider treats both as disqualifying). Only the third is a
rider fire in the registered sense; the first two are non-leaks.

WHAT THIS MEASURES. The registered rider cells re-trained in-process with
the K-3-arc prediction dump (train_probe full_eval=True: trajectory and
default return values byte-identical, asserted by tests), plus the missing
equal-dims twin (shuffled fplus_r) and two more train seeds at L3, and the
four seed-0 arms at L2 as reported context. Per test prompt, split by the
wrap flag, each cell stores its prediction and shifted-label histograms;
from them the DEPENDENCE EXCESS E_X = acc_X - sum_c q_X(c) p(c) (accuracy
beyond what the prediction and label marginals explain; exactly 0 for a
constant predictor) and the paired differences between arms, with a
cluster bootstrap over the 30 test prompts (n_boot 2000, seed 0,
percentile, marginals recomputed inside each resample).

BRANCHES (pinned in the document; S1 L3 pooled three-seed statistics):
precondition T (the re-trained seed-0 raw leg-2 excess exceeds the band,
else INDETERMINATE-NOT-REPRODUCED); A CONTENT-TRANSFER (pooled dE_br CI95
lower > 0 and point >= +0.005; a pipeline leak or persistent row-topic
content, not separable here); B AMENDABLE (not A, the AMENDED LEG passes
at seed 0 -- fails on dE_br > 0.01 or CI-clear >= +0.005 -- and pooled
dE_br <= 0.01) with the mechanism sub-reading MARGINAL-DRIFT /
TWIN-MATCHED / DRIFT-DOMINANT from dE_bf's CI and the pinned qualifiers
(wrap on A; power, compression, twin anomaly and the X_raw sentence on
B); C INDETERMINATE otherwise. L2 enters no branch. Pre-read critic round
applied 2026-09-07 (the document's dated section).

Out path: results/real/oq18_rider_diag_s1.json (+ .state.jsonl, sha-header
bound to the harvest). Never a registered OQ-18 out path; --only smokes go
to results/smoke/ only; the FRESH-STATE PIN applies to the registered
diagnostic out.
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
from sideband.probes import HarvestData, anchor_table, labels_for, train_probe  # noqa: E402
from sideband.harvest import label_index  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_probes import (REAL, SHUFFLE_SHIFT, bind_spaces_to_harvest, build_spaces,  # noqa: E402
                        cell_id, feature_blocks, parse_state, state_header)
from run_fullfree import R2_BAND, _sha, _same_path, train_moments  # noqa: E402
from run_fullfree_twin import derangement_by_prompt, twin_geometry  # noqa: E402
from run_fullfree_coarse import (SEEDS, BASE_ARM, GATE_OFFSET, REGISTERED_OUTS,  # noqa: E402
                                 make_factories, committed_moments_sha)

REGISTRATION_DOC = Path(__file__).resolve().parent.parent / "docs" / "OQ18_RIDER_DIAGNOSTIC.md"
DIAG_HARVEST = "results/real/harvest_shadow"
DIAG_OUT = "results/real/oq18_rider_diag_s1.json"
COMMITTED_STATE = "results/real/fullfree_coarse_s1.json.state.jsonl"   # the fired run's state file (the tie)
SPACE_L3 = "L3_concept_groups_v1"
SPACE_L2 = "L2_concept_k512"
DIAG_ARMS = ("a", "fplus", "fplus_b", "fplus_r")
SEEDS_OF_SPACE = {SPACE_L3: (0, 1, 2), SPACE_L2: (0,)}
CAPACITY = "linear"
BAND = R2_BAND            # 0.01, the registered rider band
MATERIAL = 0.005          # the OQ-18 materiality floor
N_BOOT = 2000
BOOT_SEED = 0
EXPECTED_CLUSTERS = 30
REPRO_TOL = 1e-9
SELECTIONS = ("all", "nonwrapped", "wrapped")
PAIRS = (("fplus_b", "fplus"), ("fplus_b", "fplus_r"), ("fplus", "a"), ("fplus_r", "fplus"))
PAIR_LEG2_RAW = "fplus_b-fplus"
PAIR_TWIN = "fplus_b-fplus_r"

BRANCH_A = "CONTENT-TRANSFER"
BRANCH_B = "AMENDABLE"
BRANCH_C = "INDETERMINATE"
BRANCH_T = "INDETERMINATE-NOT-REPRODUCED"
BRANCH_INCOMPLETE = "INCOMPLETE"
MECH_DRIFT = "MARGINAL-DRIFT"
MECH_TWIN = "TWIN-MATCHED"
MECH_DRIFT_DOM = "DRIFT-DOMINANT"
Q_MAJ_DELTA = 0.02          # compression qualifier threshold (pre-read critic round, C7)
POWER_HALF_WIDTH = 0.005    # power qualifier threshold (pre-read critic round, B3)
PRE_ROUND_REGISTRATION_SHA256 = "1904dd6245e090e8117e4e7d37428004a5c54b3697549e5e283ca4baedb676b8"


# ---------------------------------------------------------------------------
# Grid and cells
# ---------------------------------------------------------------------------

def build_grid() -> list[tuple[str, int, str, str, int, bool]]:
    """L3 seed 0 first (the tie to the registered rider cells plus the
    missing twin), then L3 seeds 1 and 2, then the four L2 seed-0 cells."""
    grid: list[tuple] = []
    for sp in (SPACE_L3, SPACE_L2):
        for seed in SEEDS_OF_SPACE[sp]:
            for arm in DIAG_ARMS:
                grid.append((sp, GATE_OFFSET, arm, CAPACITY, seed, True))
    return grid


def wrap_flags(anchors: np.ndarray, rows: np.ndarray, lengths: np.ndarray,
               offset: int, shift: int = SHUFFLE_SHIFT) -> np.ndarray:
    """True where the shifted label index wraps to the row's first positions."""
    li = np.array([label_index(int(a), offset) for a in anchors], dtype=np.int64)
    return (li + shift) >= lengths[rows]


def histograms(pred: np.ndarray, y: np.ndarray, prompts: np.ndarray, wrap: np.ndarray,
               n_classes: int) -> dict[int, dict]:
    """Per test prompt, index 0 = non-wrapped anchors, 1 = wrapped: anchor
    count, correct count, prediction histogram, shifted-label histogram."""
    out: dict[int, dict] = {}
    for p in np.unique(prompts):
        m = prompts == p
        rec: dict = {"n": [], "correct": [], "pred": [], "label": []}
        for w in (False, True):
            mm = m & (wrap == w)
            rec["n"].append(int(mm.sum()))
            rec["correct"].append(int((pred[mm] == y[mm]).sum()))
            rec["pred"].append(np.bincount(pred[mm], minlength=n_classes).astype(int).tolist())
            rec["label"].append(np.bincount(y[mm], minlength=n_classes).astype(int).tolist())
        out[int(p)] = rec
    return out


def normalize_hist(cell: dict) -> dict:
    if "_hist" in cell:
        cell["_hist"] = {int(k): v for k, v in cell["_hist"].items()}
    return cell


def run_cell_diag(data: HarvestData, spaces: dict, space: str, offset: int, arm: str, seed: int,
                  device: str, factory_of: dict, n_slots: int, shift: int = SHUFFLE_SHIFT) -> dict:
    """One shuffled linear cell with the prediction dump. The blocks, labels
    and trainer call are the registered OQ-18 rider cell's (run_probes.
    run_cell with the arm's factory) plus full_eval=True."""
    sp = spaces[space]
    rows, anchors = anchor_table(data.lengths, offset, data.tokens.shape[1])
    labels = labels_for(data.tokens, rows, anchors, offset, sp["label_map"],
                        shuffle_shift=shift, lengths=data.lengths)
    split = data.row_split()[rows]
    blocks = feature_blocks(data, "a", rows, anchors, n_slots=n_slots)
    if arm != BASE_ARM:
        blocks = blocks + list(factory_of[(arm, seed)](rows, anchors))
    t0 = time.time()
    res = train_probe(blocks, labels, split, sp["n_classes"], CAPACITY, seed,
                      device=device, full_eval=True)
    te = res["full"]["test"]
    if not np.array_equal(te["correct"], res["test_correct"]):
        raise SystemExit("full_eval test correctness differs from the default path — refusing")
    idx = te["idx"]
    y = labels[idx]
    pred = te["pred"]
    prompts = data.prompt_idx[rows[idx]]
    wrap = wrap_flags(anchors[idx], rows[idx], data.lengths, offset, shift)
    maj_label = int(np.bincount(labels[split == "train"]).argmax())
    return {
        "cell": cell_id(space, offset, arm, CAPACITY, seed, True),
        "space": space, "offset": offset, "features": arm, "capacity": CAPACITY,
        "seed": seed, "shuffled": True, "shift": int(shift),
        "test_acc": res["test_acc"], "val_acc_best": res["val_acc_best"],
        "best_epoch": res["best_epoch"],
        "n_train": res["n_train"], "n_val": res["n_val"], "n_test": res["n_test"],
        "majority_rate_test": float((y == maj_label).mean()),
        "majority_label": maj_label,
        "q_majority": float((pred == maj_label).mean()),
        "wrap_frac_test": float(wrap.mean()),
        "n_classes": int(sp["n_classes"]),
        "runtime_s": round(time.time() - t0, 1),
        "_hist": histograms(pred, y, prompts, wrap, sp["n_classes"]),
    }


# ---------------------------------------------------------------------------
# Statistics: dependence excess and paired differences, cluster bootstrap
# ---------------------------------------------------------------------------

def _arrays(cells: list[dict], n_classes: int, prompts: list[int], sel: str):
    parts = {"all": (0, 1), "nonwrapped": (0,), "wrapped": (1,)}[sel]
    P = len(prompts)
    N = np.zeros(P)
    C = np.zeros(P)
    PH = np.zeros((P, n_classes))
    LH = np.zeros((P, n_classes))
    for c in cells:
        h = c["_hist"]
        for i, p in enumerate(prompts):
            rec = h[p]
            for w in parts:
                N[i] += rec["n"][w]
                C[i] += rec["correct"][w]
                PH[i] += np.asarray(rec["pred"][w], dtype=np.float64)
                LH[i] += np.asarray(rec["label"][w], dtype=np.float64)
    return N, C, PH, LH


def _pct(v) -> list[float]:
    a = np.asarray(v, dtype=np.float64)
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


def excess_stats(cells_of_arm: dict[str, list[dict]], n_classes: int, sel: str = "all",
                 n_boot: int = N_BOOT, seed: int = BOOT_SEED,
                 expected_clusters: int | None = EXPECTED_CLUSTERS,
                 pairs: tuple = PAIRS) -> dict:
    """Per arm: acc, chance = q . p, E = acc - chance (pooled over the cells'
    seeds by summing per-prompt counts, the house estimand); per pair:
    d_acc and d_E on the same prompts. CI95 by cluster bootstrap over the
    prompts with every marginal recomputed inside each resample."""
    arms = [a for a in DIAG_ARMS if cells_of_arm.get(a)]
    if not arms:
        raise SystemExit("no cells to summarize")
    seeds = {a: sorted(c["seed"] for c in cells_of_arm[a]) for a in arms}
    if len({tuple(s) for s in seeds.values()}) != 1:
        raise SystemExit(f"arms carry different seed sets: {seeds}")
    prompts = sorted(set.intersection(*(set(c["_hist"]) for a in arms for c in cells_of_arm[a])))
    if expected_clusters is not None and len(prompts) != expected_clusters:
        raise SystemExit(f"paired prompt set has {len(prompts)} clusters, expected {expected_clusters}")
    maj = {c["majority_label"] for a in arms for c in cells_of_arm[a]}
    if len(maj) != 1:
        raise SystemExit(f"cells disagree on the majority label: {maj}")
    maj_label = maj.pop()
    arr = {a: _arrays(cells_of_arm[a], n_classes, prompts, sel) for a in arms}
    ref = arr[arms[0]]
    for a in arms[1:]:
        if not np.array_equal(arr[a][0], ref[0]) or not np.array_equal(arr[a][3], ref[3]):
            raise SystemExit(f"shifted-label histograms differ between {arms[0]} and {a} — pairing broken")
    if ref[0].sum() <= 0:
        raise SystemExit(f"selection {sel!r} has no anchors")

    def point(draw: np.ndarray) -> dict:
        out = {}
        for a in arms:
            N, C, PH, LH = arr[a]
            n = N[draw].sum()
            acc = C[draw].sum() / n
            q = PH[draw].sum(0) / n
            p = LH[draw].sum(0) / n
            chance = float(q @ p)
            out[a] = (float(acc), chance, float(acc - chance), float(q[maj_label]), float(p[maj_label]))
        return out

    full = np.arange(len(prompts))
    pt = point(full)
    boots_acc = {a: np.zeros(n_boot) for a in arms}
    boots_e = {a: np.zeros(n_boot) for a in arms}
    if n_boot:
        rng = np.random.default_rng(seed)
        for b in range(n_boot):
            draw = rng.integers(0, len(prompts), len(prompts))
            r = point(draw)
            for a in arms:
                boots_acc[a][b] = r[a][0]
                boots_e[a][b] = r[a][2]
    res = {"selection": sel, "n_prompts": len(prompts), "n_anchors": float(ref[0].sum()),
           "seeds": seeds[arms[0]], "n_boot": int(n_boot), "boot_seed": int(seed),
           "majority_label": int(maj_label), "label_majority_rate": pt[arms[0]][4],
           "arms": {}, "pairs": {}}
    for a in arms:
        acc, chance, e, qm, _ = pt[a]
        d = {"acc": acc, "chance": chance, "E": e, "q_majority": qm}
        if n_boot:
            d["ci95_acc"] = _pct(boots_acc[a])
            d["ci95_E"] = _pct(boots_e[a])
        res["arms"][a] = d
    for x, yv in pairs:
        if x in arms and yv in arms:
            d = {"d_acc": pt[x][0] - pt[yv][0], "d_E": pt[x][2] - pt[yv][2]}
            if n_boot:
                d["ci95_d_acc"] = _pct(boots_acc[x] - boots_acc[yv])
                d["ci95_d_E"] = _pct(boots_e[x] - boots_e[yv])
            res["pairs"][f"{x}-{yv}"] = d
    return res


# ---------------------------------------------------------------------------
# Branch (pinned) and the determinism tie
# ---------------------------------------------------------------------------

def amended_leg(pair: dict, band: float = BAND, material: float = MATERIAL) -> dict:
    """The AMENDED LEG 2 (docs/OQ18_RIDER_DIAGNOSTIC.md): at a (fplus_b,
    fplus_r) shuffled pair it FAILS if dE_br > band OR (CI95 lower > 0 AND
    dE_br >= material); otherwise it passes."""
    d = float(pair["d_E"])
    ci = pair.get("ci95_d_E")
    lo = None if ci is None else float(ci[0])
    fail_band = d > band
    fail_ci = bool(lo is not None and lo > 0 and d >= material)
    reason = ("point above the band" if fail_band else
              "CI-clear and material" if fail_ci else "within the band and not CI-clear-material")
    return {"d_E": d, "ci95_d_E": (None if ci is None else [float(ci[0]), float(ci[1])]),
            "fails": bool(fail_band or fail_ci), "reason": reason}


def branch(l3_pooled: dict, l3_per_seed: dict[int, dict], l3_pooled_nonwrapped: dict | None = None,
           band: float = BAND, material: float = MATERIAL) -> dict:
    """The pinned rules (docs/OQ18_RIDER_DIAGNOSTIC.md, Branches, after the
    pre-read critic round). Mechanical."""
    def have(d: dict | None, k: str) -> bool:
        return bool(d) and k in d.get("pairs", {})

    s0 = l3_per_seed.get(0)
    out: dict = {"band": band, "material": material,
                 "leg2_raw_per_seed": {int(s): st["pairs"][PAIR_LEG2_RAW]["d_acc"]
                                       for s, st in l3_per_seed.items() if have(st, PAIR_LEG2_RAW)}}
    if not (have(s0, PAIR_LEG2_RAW) and have(s0, PAIR_TWIN) and have(l3_pooled, PAIR_TWIN)
            and have(l3_pooled, PAIR_LEG2_RAW) and "ci95_d_E" in l3_pooled["pairs"][PAIR_TWIN]
            and "ci95_d_E" in s0["pairs"][PAIR_TWIN]):
        out["branch"] = BRANCH_INCOMPLETE
        out["reason"] = "the seed-0 rider cells, the twin, or the CIs are missing"
        return out
    leg2_raw_seed0 = s0["pairs"][PAIR_LEG2_RAW]["d_acc"]
    out["leg2_raw_seed0"] = leg2_raw_seed0
    out["tie_reproduces"] = bool(leg2_raw_seed0 > band)
    if not out["tie_reproduces"]:
        out["branch"] = BRANCH_T
        out["reason"] = "the re-trained seed-0 raw leg-2 excess does not exceed the band"
        return out
    br = l3_pooled["pairs"][PAIR_TWIN]
    bf = l3_pooled["pairs"][PAIR_LEG2_RAW]
    d_br, (lo_br, hi_br) = br["d_E"], br["ci95_d_E"]
    leg = amended_leg(s0["pairs"][PAIR_TWIN], band, material)
    x_raw_s0 = float(s0["pairs"][PAIR_TWIN]["d_acc"])
    out.update({"dE_br_pooled": d_br, "dE_br_ci95": [lo_br, hi_br],
                "dE_br_seed0": leg["d_E"], "dE_br_seed0_ci95": leg["ci95_d_E"],
                "amended_leg_seed0": leg,
                "dE_bf_pooled": bf["d_E"], "dE_bf_ci95": bf["ci95_d_E"],
                "x_raw_pooled": br["d_acc"], "x_raw_ci95": br["ci95_d_acc"],
                "x_raw_seed0": x_raw_s0,
                "x_raw_sentence": ("the registered statistic, twin-referenced, would also have passed"
                                   if x_raw_s0 <= band else
                                   "the registered statistic, twin-referenced, would still have fired")})
    a_fires = bool(lo_br > 0 and d_br >= material)
    if a_fires:
        out["branch"] = BRANCH_A
        out["reason"] = "pooled dE_br CI95 lower > 0 and point >= material"
    elif (not leg["fails"]) and d_br <= band:
        out["branch"] = BRANCH_B
        out["reason"] = "not A; the amended leg passes at seed 0; pooled dE_br within the band"
    else:
        out["branch"] = BRANCH_C
        out["reason"] = ("neither A nor B: " + ("the amended leg fails at seed 0 (" + leg["reason"] + ")"
                                                if leg["fails"] else "pooled dE_br above the band"))
    lo_bf, hi_bf = bf["ci95_d_E"]
    if lo_bf <= 0 <= hi_bf:
        out["mechanism"] = MECH_DRIFT
    elif lo_bf > 0:
        out["mechanism"] = MECH_TWIN
    else:
        out["mechanism"] = MECH_DRIFT_DOM
    quals: list[str] = []
    if out["branch"] == BRANCH_A:
        nw = (l3_pooled_nonwrapped or {}).get("pairs", {}).get(PAIR_TWIN)
        nw_fires = bool(nw and "ci95_d_E" in nw and nw["ci95_d_E"][0] > 0 and nw["d_E"] >= material)
        out["nonwrapped_dE_br"] = None if not nw else {"d_E": nw["d_E"], "ci95_d_E": nw.get("ci95_d_E")}
        if not nw_fires:
            quals.append("concentrated on wrapped anchors (row-end / row-opening recall), not row-level content")
    if out["branch"] == BRANCH_B:
        lo0, hi0 = leg["ci95_d_E"]
        half = (hi0 - lo0) / 2.0
        out["dE_br_seed0_half_width"] = half
        if half > POWER_HALF_WIDTH:
            quals.append(f"underpowered against a materiality-sized excess (seed-0 dE_br CI95 half-width {half:.4f})")
        qb = s0.get("arms", {}).get("fplus_b", {}).get("q_majority")
        qr = s0.get("arms", {}).get("fplus_r", {}).get("q_majority")
        if qb is not None and qr is not None:
            out["q_majority_seed0"] = {"fplus_b": qb, "fplus_r": qr}
            if qb - qr > Q_MAJ_DELTA:
                quals.append("no EXPRESSED dependence at this reader: the aligned arm sits closer to the "
                             f"majority predictor than its twin by {qb - qr:.4f}")
        if hi_br < 0:
            quals.append("twin anomaly: pooled dE_br CI-clear negative (disclosed like an Mn_r fire)")
    out["qualifiers"] = quals
    return out


def reproduction(diag_cells: list[dict], committed: dict[str, dict], tol: float = REPRO_TOL) -> dict:
    """|acc(re-trained)| - acc(state row)| per registered shuffled cell present
    in both; REPRODUCED at <= tol."""
    out = {}
    for c in diag_cells:
        s = committed.get(c["cell"])
        if s is None:
            continue
        diff = abs(float(c["test_acc"]) - float(s["test_acc"]))
        out[c["cell"]] = {"diag": float(c["test_acc"]), "state": float(s["test_acc"]),
                          "abs_diff": diff, "reproduced": bool(diff <= tol),
                          "best_epoch_diag": c["best_epoch"], "best_epoch_state": s.get("best_epoch")}
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", default=DIAG_HARVEST)
    ap.add_argument("--out", default=DIAG_OUT)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--only", default=None, help="comma-separated substring filter on cell ids (smoke)")
    ap.add_argument("--resume", action="store_true", help="continue a crashed run from its state file")
    ap.add_argument("--n-slots", type=int, default=512)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--buckets16", default=str(REAL / "buckets_k16.json"))
    ap.add_argument("--glue16", default=str(REAL / "glue_k16.json"))
    ap.add_argument("--buckets512", default=str(REAL / "buckets_k512.json"))
    ap.add_argument("--glue512", default=str(REAL / "glue_k512.json"))
    ap.add_argument("--groups", default=str(REAL / "concept_groups_v1.json"))
    return ap


def check_out(out: str, only: str | None) -> tuple[Path, bool]:
    """(resolved out path, registered_diag). Refuses any registered OQ-18 out
    path and an --only smoke on the registered diagnostic out."""
    out_path = Path(out).resolve()
    if out_path in {(REAL / n).resolve() for n in REGISTERED_OUTS}:
        raise SystemExit("this diagnostic never writes a registered OQ-18 out path")
    registered_diag = out_path == Path(DIAG_OUT).resolve()
    if only and registered_diag:
        raise SystemExit("--only smoke runs may not write the registered diagnostic out path")
    return out_path, registered_diag


def only_match(only: str | None, cid: str) -> bool:
    if not only:
        return True
    return any(s and s in cid for s in only.split(","))


def _git() -> tuple[str, list[str]]:
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        d = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, timeout=10)
        lines = [ln for ln in d.stdout.splitlines() if ln.strip()]
        return (r.stdout.strip() or "unknown") + ("-dirty" if lines else ""), lines
    except Exception:
        return "unknown", []


def main() -> None:
    args = build_parser().parse_args()
    out_path, registered_diag = check_out(args.out, args.only)
    if not REGISTRATION_DOC.exists():
        raise SystemExit(f"{REGISTRATION_DOC} missing — refusing to run an unregistered diagnostic")
    reg_sha = _sha(REGISTRATION_DOC)
    if not _same_path(args.harvest, DIAG_HARVEST):
        raise SystemExit("the diagnostic is registered on the S1 primary harvest only")
    state_path = Path(args.out + ".state.jsonl")
    if registered_diag and state_path.exists() and not args.resume:
        raise SystemExit(f"FRESH-STATE PIN: {state_path} exists; pass --resume only to continue a crashed "
                         "run or the disclosed pre-read critic resume (docs/OQ18_RIDER_DIAGNOSTIC.md, "
                         "'Pre-read critic round')")

    data = HarvestData(args.harvest)
    split_names = data.row_split()
    bind_spaces_to_harvest(data.ref_meta, {"buckets16": args.buckets16, "buckets512": args.buckets512},
                           n_slots=args.n_slots)
    spaces = build_spaces(data, tag="concept", buckets16=args.buckets16, glue16=args.glue16,
                          buckets512=args.buckets512, glue512=args.glue512, groups_path=args.groups)
    for sp in (SPACE_L3, SPACE_L2):
        if sp not in spaces:
            raise SystemExit(f"label space {sp} not built")

    hidden = data.array("hidden")
    top_ids = data.array("top_ids")
    slots = data.array("slots")
    moments = train_moments(hidden, data.lengths, split_names)
    committed_sha = committed_moments_sha(args.harvest)
    if committed_sha != moments["sha256"]:
        raise SystemExit("hz moments sha differs from the committed OQ-17 payload's — refusing")
    perms = {seed: derangement_by_prompt(data.prompt_idx, split_names, seed) for seed in SEEDS}
    geometry = {}
    for seed in SEEDS:
        g = twin_geometry(data.lengths, perms[seed], GATE_OFFSET, data.tokens.shape[1], data.prompt_idx)
        if g["corrected_twin_same_prompt_frac"] != 0.0:
            raise SystemExit(f"corrected twin reads its own prompt at seed {seed} — refusing")
        geometry[str(seed)] = g
    perm_shas = {str(seed): hashlib.sha256(perms[seed].astype(np.int64).tobytes()).hexdigest()
                 for seed in SEEDS}
    factory_of = make_factories(top_ids, hidden, slots, data.lengths, args.n_slots, moments, perms)

    committed_state = Path(COMMITTED_STATE)
    committed_rows = (parse_state(committed_state.read_text(), data.npz_shas)
                      if committed_state.exists() else {})
    committed_state_sha = _sha(committed_state) if committed_state.exists() else None

    done: dict[str, dict] = {}
    if state_path.exists():
        done = {k: normalize_hist(v) for k, v in parse_state(state_path.read_text(), data.npz_shas).items()}
        print(f"[resume] {len(done)} cells already done")
    else:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w") as f:
            f.write(json.dumps(state_header(data.npz_shas)) + "\n")

    t0 = time.time()
    grid = build_grid()
    cells: list[dict] = []
    for i, (sp, off, arm, cap, seed, shuffled) in enumerate(grid):
        cid = cell_id(sp, off, arm, cap, seed, shuffled)
        if not only_match(args.only, cid):
            continue
        if cid in done:
            cells.append(done[cid])
            continue
        res = run_cell_diag(data, spaces, sp, off, arm, seed, args.device, factory_of, args.n_slots)
        cells.append(res)
        with state_path.open("a") as f:
            f.write(json.dumps(res) + "\n")
        print(f"[{i + 1}/{len(grid)}] {cid}: test_acc={res['test_acc']:.4f} (maj "
              f"{res['majority_rate_test']:.4f}, q_maj {res['q_majority']:.4f}, epoch {res['best_epoch']}) "
              f"{res['runtime_s']}s total {time.time() - t0:.0f}s", flush=True)

    expected = None if args.only else EXPECTED_CLUSTERS
    per_space: dict = {}
    for sp in (SPACE_L3, SPACE_L2):
        sp_cells = [c for c in cells if c["space"] == sp]
        if not sp_cells:
            continue
        n_classes = int(spaces[sp]["n_classes"])
        by_arm_all = {a: [c for c in sp_cells if c["features"] == a] for a in DIAG_ARMS}
        seeds_present = sorted({c["seed"] for c in sp_cells})
        # arms are pooled only over the seeds every arm has
        common = sorted(set.intersection(*(set(c["seed"] for c in v) for v in by_arm_all.values() if v)))
        by_arm = {a: [c for c in v if c["seed"] in common] for a, v in by_arm_all.items()}
        entry: dict = {"seeds_present": seeds_present, "seeds_pooled": common, "pooled": {}, "per_seed": {}}
        if common:
            for sel in SELECTIONS:
                entry["pooled"][sel] = excess_stats(by_arm, n_classes, sel, args.n_boot, BOOT_SEED, expected)
            for seed in common:
                one = {a: [c for c in v if c["seed"] == seed] for a, v in by_arm.items()}
                entry["per_seed"][str(seed)] = {sel: excess_stats(one, n_classes, sel, args.n_boot, BOOT_SEED, expected)
                                                for sel in SELECTIONS}
        per_space[sp] = entry

    l3 = per_space.get(SPACE_L3, {})
    verdict = branch(l3.get("pooled", {}).get("all", {}),
                     {int(s): v.get("all", {}) for s, v in l3.get("per_seed", {}).items()},
                     l3.get("pooled", {}).get("nonwrapped"))
    verdict["reproduction"] = reproduction(cells, committed_rows)
    n_registered_shuffled = sum(1 for v in committed_rows.values() if v.get("shuffled"))
    verdict["reproduced_all"] = bool(verdict["reproduction"]) and all(
        v["reproduced"] for v in verdict["reproduction"].values())
    verdict["tie_scope"] = ("registered-run" if (verdict["reproduced_all"]
                                                 and len(verdict["reproduction"]) == n_registered_shuffled)
                            else "construction")
    verdict["partial"] = bool(args.only)

    git_commit, git_porcelain = _git()
    import torch
    payload = {
        "registered": ("OQ-18 LEAK-RIDER DIAGNOSTIC (docs/OQ18_RIDER_DIAGNOSTIC.md, 2026-09-07, "
                       "before any diagnostic cell trained)"),
        "registration_sha256": reg_sha,
        "pre_round_registration_sha256": PRE_ROUND_REGISTRATION_SHA256,
        "harvest": args.harvest,
        "shift": int(SHUFFLE_SHIFT),
        "n_cells": len(cells),
        "partial": bool(args.only),
        "resumed_cells": int(sum(1 for c in cells if c["cell"] in done)),
        "cells": [{k: v for k, v in c.items() if k != "_hist"} for c in cells],
        "per_space": per_space,
        "verdict": verdict,
        "fired_rider": {"state_file": COMMITTED_STATE, "state_sha256": committed_state_sha,
                        "rows": {k: {kk: vv for kk, vv in v.items() if kk != "_clusters"}
                                 for k, v in committed_rows.items() if v.get("shuffled")}},
        "standardization": {"moments_sha256": moments["sha256"], "matches_committed_oq17": True},
        "twin": {"seed_base_note": "derangement_by_prompt(prompt_idx, split, seed) as in the OQ-18 instrument",
                 "perm_sha256": perm_shas, "geometry": geometry},
        "provenance": {
            "git_commit": git_commit,
            "git_status_tracked": git_porcelain,
            "instrument_sha256": _sha(Path(__file__)),
            "args": redact_args(vars(args)),
            "harvest_npz_sha256": data.npz_shas,
            "state_file": str(state_path),
            "torch": torch.__version__,
            "cuda": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1))
    print(json.dumps({k: verdict.get(k) for k in ("branch", "mechanism", "reason", "qualifiers",
                                                   "tie_reproduces", "tie_scope", "leg2_raw_per_seed",
                                                   "amended_leg_seed0", "dE_br_pooled", "dE_br_ci95",
                                                   "dE_bf_pooled", "dE_bf_ci95", "x_raw_seed0",
                                                   "x_raw_sentence", "x_raw_pooled", "x_raw_ci95",
                                                   "reproduced_all")}, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

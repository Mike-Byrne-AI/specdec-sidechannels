"""OQ-16 Stage R (FOLD-BACK #2 ARC REGISTRATION, BLUEPRINT 2026-09-04):
multi-output ridge reconstruction of the anchor hidden state h_a from
anchor-time features over the four registered vanilla byproduct runs,
with the two-leg gate and the GATING five-seed stale-target control —
live gate and all five controls in ONE deterministic invocation.

Arms: FREE (657 anchor-time dims), TEL (free ++ 4x512 slot multi-hot),
NOISE (TEL with the F-16 alignment-destroying shift). Target: h_a
(float16 log -> float64), z-scored per coordinate on pooled TRAIN
moments; all MSEs in standardized units. NO q_sig anywhere (it does not
exist at the anchor — the registration's deployment-honest feature set).

Estimand: pooled TEST standardized MSE; deltas via
stats.paired_ratio_delta_ci (num = per-cluster SSE, den = per-cluster
position count, identical across arms; n_boot 2000, seed 0). Cluster =
(population, orig_prompt_idx); prompt-level 126/42/42 splits per
population by the Stage-I recipe.

Outputs next to --out (house conventions: meta BEFORE the run, state
jsonl as the recompute surface, summary as completion marker):
  <out>.meta.json, <out>.state.jsonl, <out> (summary json)

Registered command line (no overrides):
  python tools/train_recon.py --out results/real/oq16_stage_r.json
Sizing knobs (--n-slots, --lambdas) exist for the synthetic CI test and
REFUSE the registered output path (the Stage-I registered-outs guard).
Stale seeds are gate constants and are NOT CLI-reachable.

DR-1 / DR-2 POST-GATE DIAGNOSTICS (BLUEPRINT 2026-09-04, registered
after the gate was read; NON-CRITERION): --feature-clip restricts every
feature to its TRAIN [min, max] support before standardization (the
critic-identified standardization pathology guard); --freetok adds the
equal-dims token-identity baseline arm. Both are MODE overrides: they
refuse the registered out, keep the registered-shape asserts ON, and
are recorded in meta. The tool always emits the trivial-baseline
per-cluster rows and the REPORTED tel_vs_trivial delta; with the modes
OFF every pre-existing registered field is bit-identical (the
INVARIANCE LEG, results/real/oq16_stage_r_inv.json).

DR-3 (--union, needs --freetok): UNION = TEL ++ TOK and UNIONNOISE =
NOISE ++ TOK, the union's equal-dims alignment-destroyed anchor.
DR-4 (--freetok2, needs --union): FREETOK2 = FREETOK ++ TOK_B (salted-
hash bins valued by top_p) — the equal-dims better-token-encoding
comparator for the union; readouts union_vs_freetok2 (primary),
freetok2_vs_freetok (the comparator's teeth), freetok2_vs_free,
tel_vs_freetok2. Every mode is additive: the shared arms reproduce
the earlier runs bit-identically (critic-recomputed dr -> dr3).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sideband.recon import (  # noqa: E402
    FEATURE_SETS,
    FREETOK2_ARM,
    FREETOK_ARM,
    FREETOK_BINS,
    H_DIM,
    N_PROMPTS_PER_POP,
    RECON_LAMBDA_GRID,
    RECON_RUNS,
    STALE_SEEDS,
    TRIVIAL_ARM,
    UNION_ARM,
    UNION_NOISE_ARM,
    Standardizer,
    arm_features,
    augment,
    centered_cosine_rows,
    dr1_label,
    dr2_label,
    dr3_label,
    dr4_label,
    h_target,
    noise_self_maps,
    prompt_index_map,
    ridge_fit,
    stage1_split,
    stage_r_gate,
    verify_byproduct,
)
from sideband.outcome_head import N_SLOTS  # noqa: E402
from sideband.stats import paired_ratio_delta_ci  # noqa: E402

REGISTERED_OUT = (Path(__file__).resolve().parents[1] / "results" / "real"
                  / "oq16_stage_r.json")
VARIANTS = ("live",) + STALE_SEEDS


def _git_commit() -> str:
    try:
        import subprocess
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True).stdout.strip()
        return (head + ("-dirty" if dirty else "")) if head else "unknown"
    except OSError:
        return "unknown"


def load_run(root: Path, spec: dict) -> dict:
    stem = spec["stem"]
    byp = root / f"{stem}.jsonl.byproduct"
    summary = root / f"{stem}.summary.json"
    gen = root / f"{stem}.gen.jsonl"
    files = verify_byproduct(byp, summary)
    return {"stem": stem, "pop": spec["pop"], "files": files,
            "idx_map": prompt_index_map(gen),
            "summary_sha": hashlib.sha256(summary.read_bytes()).hexdigest()}


def iter_prompts(run: dict):
    for f in run["files"]:
        yield run["idx_map"][int(f.stem[1:])], dict(np.load(f))


def _stale_perm(seed: int, run_index: int, pid: int, n: int) -> np.ndarray:
    from sideband.recon import stale_perm
    return stale_perm(seed, run_index, pid, n)


def pipeline(root: Path, out: Path, n_slots: int | None = None,
             lambda_grid: tuple | None = None, write: bool = True,
             feature_clip: bool = False, freetok: bool = False,
             union: bool = False, freetok2: bool = False,
             return_weights: tuple = ()) -> dict:
    overrides: dict = {}
    if n_slots is not None and n_slots != N_SLOTS:
        overrides["n_slots"] = n_slots
    n_slots = n_slots if n_slots is not None else N_SLOTS
    if lambda_grid is not None and tuple(lambda_grid) != RECON_LAMBDA_GRID:
        overrides["lambda_grid"] = list(lambda_grid)
    lambda_grid = tuple(lambda_grid) if lambda_grid is not None else RECON_LAMBDA_GRID
    modes: dict = {}
    if feature_clip:
        modes["feature_clip"] = True
    if union and not freetok:
        raise SystemExit("--union needs --freetok (union_vs_freetok is its readout)")
    if freetok2 and not union:
        raise SystemExit("--freetok2 needs --union (union_vs_freetok2 is its readout)")
    arms = tuple(FEATURE_SETS) + ((FREETOK_ARM,) if freetok else ()) \
        + ((UNION_ARM, UNION_NOISE_ARM) if union else ()) \
        + ((FREETOK2_ARM,) if freetok2 else ())
    if freetok:
        modes["freetok"] = FREETOK_BINS
    if union:
        modes["union"] = True
    if freetok2:
        modes["freetok2"] = True

    runs = [load_run(root, spec) for spec in RECON_RUNS]

    # populations + splits (per pop, Stage-I recipe verbatim)
    pops: dict[str, int] = {}
    for run in runs:
        ids = sorted(set(run["idx_map"].values()))
        n_pop = len(ids)
        if ids != list(range(n_pop)):
            raise SystemExit(f"{run['stem']}: orig ids are not 0..{n_pop - 1}")
        prev = pops.setdefault(run["pop"], n_pop)
        if prev != n_pop:
            raise SystemExit(f"population {run['pop']} size mismatch")
    if not overrides:
        if set(pops.values()) != {N_PROMPTS_PER_POP}:
            raise SystemExit("registered run demands 210 prompts per population "
                             "(sizing overrides only on non-registered outs)")
    split = {pop: stage1_split(n) for pop, n in pops.items()}
    role_of = {}
    for pop, parts in split.items():
        for name, idx in parts.items():
            for i in idx:
                role_of[(pop, int(i))] = name

    meta = {
        "tool": "train_recon",
        "registration": "OQ-16 FOLD-BACK #2 (BLUEPRINT 2026-09-04)",
        "git_commit": _git_commit(), "started_unix": time.time(),
        "runs": [r["stem"] for r in runs],
        "populations": pops,
        "split_sizes": {p: {k: len(v) for k, v in s.items()}
                        for p, s in split.items()},
        "summary_sha256": {r["stem"]: r["summary_sha"] for r in runs},
        "lambda_grid": list(lambda_grid), "n_slots": n_slots,
        "stale_seeds": list(STALE_SEEDS),
        "sizing_overrides": overrides,
        "modes": modes,
        "arms": list(arms),
        "numpy_version": np.__version__,
    }
    if write:
        out.parent.mkdir(parents=True, exist_ok=True)
        Path(str(out) + ".meta.json").write_text(json.dumps(meta, indent=2))

    def rows_of(role: str):
        for run_idx, run in enumerate(runs):
            for pid, z in iter_prompts(run):
                if role_of[(run["pop"], pid)] == role:
                    yield run_idx, run["pop"], pid, z

    # ---- PASS 1: standardizer moments + TRAIN support (TRAIN only) ----
    mom = {fs: None for fs in arms}
    lo_hi = {fs: None for fs in arms}
    y_mom = None
    h_dim = None
    n_train_rows = 0
    sliver = 0
    for run_idx, run in enumerate(runs):
        for pid, z in iter_prompts(run):
            n = int(np.asarray(z["gamma_used"]).shape[0])
            if noise_self_maps(n):
                sliver += 1
            if role_of[(run["pop"], pid)] != "train":
                continue
            y = h_target(z)
            if h_dim is None:
                h_dim = y.shape[1]
                if not overrides and h_dim != H_DIM:
                    raise SystemExit(f"registered run demands h_dim {H_DIM}, "
                                     f"data has {h_dim}")
            if y.shape[1] != h_dim:
                raise SystemExit("inconsistent h dims across runs")
            if y_mom is None:
                y_mom = [np.zeros(h_dim), np.zeros(h_dim)]
            y_mom[0] += y.sum(0)
            y_mom[1] += (y * y).sum(0)
            n_train_rows += y.shape[0]
            for fs in arms:
                x = arm_features(z, fs, n_slots=n_slots)
                if mom[fs] is None:
                    mom[fs] = [np.zeros(x.shape[1]), np.zeros(x.shape[1])]
                    lo_hi[fs] = [x.min(0).copy(), x.max(0).copy()]
                mom[fs][0] += x.sum(0)
                mom[fs][1] += (x * x).sum(0)
                np.minimum(lo_hi[fs][0], x.min(0), out=lo_hi[fs][0])
                np.maximum(lo_hi[fs][1], x.max(0), out=lo_hi[fs][1])
    if n_train_rows == 0:
        raise SystemExit("no TRAIN rows")
    feat_std = {fs: Standardizer.from_moments(mom[fs][0], mom[fs][1],
                                              n_train_rows)
                for fs in arms}
    targ_std = Standardizer.from_moments(y_mom[0], y_mom[1], n_train_rows)

    def prep(fs: str, x_raw: np.ndarray) -> np.ndarray:
        """Standardized augmented design; with the DR-1 clip ON, raw
        values are first restricted to the TRAIN [min, max] support
        (TRAIN rows are unchanged by construction). Clip OFF is the
        registered path — the array is untouched."""
        if feature_clip:
            x_raw = np.clip(x_raw, lo_hi[fs][0], lo_hi[fs][1])
        return augment(feat_std[fs].apply(x_raw))

    # ---- PASS 2: TRAIN Gram + per-variant cross-moments ----
    dims = {fs: mom[fs][0].shape[0] for fs in arms}
    G = {fs: np.zeros((dims[fs] + 1, dims[fs] + 1)) for fs in arms}
    B = {fs: {v: np.zeros((dims[fs] + 1, h_dim)) for v in VARIANTS}
         for fs in arms}
    for run_idx, pop, pid, z in rows_of("train"):
        n = int(np.asarray(z["gamma_used"]).shape[0])
        y_live = targ_std.apply(h_target(z))
        y_var = {"live": y_live}
        for s in STALE_SEEDS:
            y_var[s] = y_live[_stale_perm(s, run_idx, pid, n)]
        for fs in arms:
            xa = prep(fs, arm_features(z, fs, n_slots=n_slots))
            G[fs] += xa.T @ xa
            for v in VARIANTS:
                B[fs][v] += xa.T @ y_var[v]

    # ---- PASS 3: cache VAL + TEST rows ----
    cache: dict[str, list] = {"val": [], "test": []}
    for role in ("val", "test"):
        for run_idx, pop, pid, z in rows_of(role):
            n = int(np.asarray(z["gamma_used"]).shape[0])
            seg = {
                "run_idx": run_idx, "pop": pop, "pid": pid, "n": n,
                "y": targ_std.apply(h_target(z)),
                "x": {fs: prep(fs, arm_features(z, fs, n_slots=n_slots))
                      for fs in arms},
            }
            cache[role].append(seg)
    if not cache["val"] or not cache["test"]:
        raise SystemExit("empty VAL or TEST split")

    def seg_y(seg: dict, variant) -> np.ndarray:
        if variant == "live":
            return seg["y"]
        return seg["y"][_stale_perm(variant, seg["run_idx"], seg["pid"],
                                    seg["n"])]

    def solve_all(fs: str, lam: float) -> dict:
        stacked = np.hstack([B[fs][v] for v in VARIANTS])
        w_all = ridge_fit(G[fs], stacked, lam)
        return {v: w_all[:, i * h_dim:(i + 1) * h_dim]
                for i, v in enumerate(VARIANTS)}

    # ---- lambda selection on VAL (per arm x variant; tie -> larger) ----
    val_positions = sum(seg["n"] for seg in cache["val"]) * h_dim
    val_mse: dict = {fs: {v: {} for v in VARIANTS} for fs in arms}
    for fs in arms:
        for lam in lambda_grid:
            w_by_v = solve_all(fs, lam)
            sse = {v: 0.0 for v in VARIANTS}
            for seg in cache["val"]:
                for v in VARIANTS:
                    err = seg["x"][fs] @ w_by_v[v] - seg_y(seg, v)
                    sse[v] += float((err * err).sum())
            for v in VARIANTS:
                val_mse[fs][v][lam] = sse[v] / val_positions
    chosen = {fs: {} for fs in arms}
    for fs in arms:
        for v in VARIANTS:
            best = min(val_mse[fs][v].values())
            chosen[fs][v] = max(l for l in lambda_grid
                                if val_mse[fs][v][l] == best)

    # ---- TEST eval at chosen lambdas ----
    cluster_keys = sorted({(seg["pop"], seg["pid"]) for seg in cache["test"]})
    key_index = {k: i for i, k in enumerate(cluster_keys)}
    n_cl = len(cluster_keys)
    sse_cl = {fs: {v: np.zeros(n_cl) for v in VARIANTS} for fs in arms}
    cnt_cl = np.zeros(n_cl)
    for seg in cache["test"]:
        cnt_cl[key_index[(seg["pop"], seg["pid"])]] += seg["n"] * h_dim
    coord_sse = {fs: np.zeros(h_dim) for fs in arms}
    coord_triv = np.zeros(h_dim)
    triv_cl = np.zeros(n_cl)
    cos_rows = {fs: [] for fs in arms}
    w_live: dict = {}
    for fs in arms:
        w_by_lam = {lam: None for lam in set(chosen[fs].values())}
        for lam in w_by_lam:
            w_by_lam[lam] = solve_all(fs, lam)
        if fs in return_weights:
            w_live[fs] = w_by_lam[chosen[fs]["live"]]["live"]
        for seg in cache["test"]:
            ci = key_index[(seg["pop"], seg["pid"])]
            for v in VARIANTS:
                w = w_by_lam[chosen[fs][v]][v]
                pred = seg["x"][fs] @ w
                err = pred - seg_y(seg, v)
                sse_cl[fs][v][ci] += float((err * err).sum())
                if v == "live":
                    coord_sse[fs] += (err * err).sum(0)
                    cos_rows[fs].append(centered_cosine_rows(pred, seg["y"]))
    for seg in cache["test"]:
        ci = key_index[(seg["pop"], seg["pid"])]
        triv_cl[ci] += float((seg["y"] * seg["y"]).sum())
        coord_triv += (seg["y"] * seg["y"]).sum(0)
    test_positions = float(cnt_cl.sum())
    triv_mse = float(triv_cl.sum()) / test_positions

    # ---- deltas + gate ----
    def sse_of(arm: str, v):
        return triv_cl if arm == TRIVIAL_ARM else sse_cl[arm][v]

    def delta(fs_a: str, fs_b: str, v, mask=None) -> tuple:
        a, b, c = sse_of(fs_a, v), sse_of(fs_b, v), cnt_cl
        if mask is not None:
            a, b, c = a[mask], b[mask], c[mask]
        d, lo, hi = paired_ratio_delta_ci(a, c, b, c, n_boot=2000, seed=0)
        return (d, lo, hi)

    pop_mask = {pop: np.array([k[0] == pop for k in cluster_keys])
                for pop in pops}
    pop_ok = {pop: m.sum() >= 2 for pop, m in pop_mask.items()}

    def delta_block(fs_a: str, fs_b: str) -> dict:
        """pooled live + per-pop live + all stale variants (pooled)."""
        return {
            "pooled": delta(fs_a, fs_b, "live"),
            "per_pop": {pop: delta(fs_a, fs_b, "live", pop_mask[pop])
                        for pop in pops if pop_ok[pop]},
            "stale": {str(s): delta(fs_a, fs_b, s) for s in STALE_SEEDS},
        }

    d_noise = {v: delta("noise", "tel", v) for v in VARIANTS}
    d_free = {v: delta("free", "tel", v) for v in VARIANTS}
    gate = stage_r_gate(d_noise["live"], d_free["live"],
                        [d_noise[s][0] for s in STALE_SEEDS])

    # per-population registered deltas (REPORTED)
    per_pop = {}
    for pop in pops:
        if pop_ok[pop]:
            per_pop[pop] = {
                "delta_noise": delta("noise", "tel", "live", pop_mask[pop]),
                "delta_free": delta("free", "tel", "live", pop_mask[pop]),
            }

    # REPORTED extras: trivial-baseline margin (+ DR-2 arm deltas)
    tel_vs_trivial = delta_block(TRIVIAL_ARM, "tel")
    extras = {"tel_vs_trivial": tel_vs_trivial}
    labels = {}
    if feature_clip:
        labels["dr1"] = dr1_label(tel_vs_trivial)
    if freetok:
        extras["tel_vs_freetok"] = delta_block(FREETOK_ARM, "tel")
        extras["freetok_vs_free"] = delta_block("free", FREETOK_ARM)
        extras["freetok_vs_trivial"] = delta_block(TRIVIAL_ARM, FREETOK_ARM)
        labels["dr2"] = dr2_label(extras["tel_vs_freetok"]["pooled"])
    if union:
        extras["union_vs_freetok"] = delta_block(FREETOK_ARM, UNION_ARM)
        extras["union_vs_unionnoise"] = delta_block(UNION_NOISE_ARM, UNION_ARM)
        extras["union_vs_tel"] = delta_block("tel", UNION_ARM)
        labels["dr3"] = dr3_label(extras["union_vs_freetok"]["pooled"],
                                  extras["union_vs_unionnoise"]["pooled"])
    if freetok2:
        extras["union_vs_freetok2"] = delta_block(FREETOK2_ARM, UNION_ARM)
        extras["freetok2_vs_freetok"] = delta_block(FREETOK_ARM, FREETOK2_ARM)
        extras["freetok2_vs_free"] = delta_block("free", FREETOK2_ARM)
        extras["tel_vs_freetok2"] = delta_block(FREETOK2_ARM, "tel")
        labels["dr4"] = dr4_label(extras["union_vs_freetok2"]["pooled"],
                                  extras["freetok2_vs_freetok"]["pooled"])

    def cos_summary(fs: str) -> dict:
        c = np.concatenate(cos_rows[fs])
        ok = np.isfinite(c)
        q = (np.percentile(c[ok], [25, 50, 75]).tolist()
             if ok.any() else [None] * 3)
        return {"q25": q[0], "median": q[1], "q75": q[2],
                "n": int(ok.sum()), "n_zero_norm": int((~ok).sum())}

    def coord_r2_quartiles(fs: str) -> list:
        with np.errstate(divide="ignore", invalid="ignore"):
            r2 = 1.0 - coord_sse[fs] / coord_triv
        r2 = r2[np.isfinite(r2)]
        return np.percentile(r2, [25, 50, 75]).tolist()

    def jsonable(block: dict) -> dict:
        return {"pooled": list(block["pooled"]),
                "per_pop": {p: list(v) for p, v in block["per_pop"].items()},
                "stale": {s: list(v) for s, v in block["stale"].items()}}

    test_mse = {fs: float(sse_cl[fs]["live"].sum() / test_positions)
                for fs in arms}
    summary = {
        "registration": meta["registration"],
        "gate": gate,
        "delta_noise": {str(v): list(d_noise[v]) for v in VARIANTS},
        "delta_free": {str(v): list(d_free[v]) for v in VARIANTS},
        "test_mse": test_mse,
        "trivial_baseline_test_mse": triv_mse,
        "r2": {fs: 1.0 - test_mse[fs] / triv_mse for fs in arms},
        "per_population": {p: {k: list(vv) for k, vv in d.items()}
                           for p, d in per_pop.items()},
        "chosen_lambda": {fs: {str(v): chosen[fs][v] for v in VARIANTS}
                          for fs in arms},
        "lambda_grid_edge_selected": bool(any(
            chosen[fs][v] in (lambda_grid[0], lambda_grid[-1])
            for fs in arms for v in VARIANTS)),
        "val_mse": {fs: {str(v): {str(l): val_mse[fs][v][l]
                                  for l in lambda_grid}
                         for v in VARIANTS} for fs in arms},
        "centered_cosine": {fs: cos_summary(fs) for fs in arms},
        "per_coord_r2_quartiles": {fs: coord_r2_quartiles(fs)
                                   for fs in arms},
        "n_test_positions": test_positions,
        "n_test_clusters": n_cl,
        "n_train_rows": n_train_rows,
        "noise_self_map_sliver": sliver,
        "h_dim": h_dim,
        "feature_dims": dims,
        "reported_deltas": {k: jsonable(v) for k, v in extras.items()},
        "modes": modes,
        "diagnostic_labels": labels,
        "note": ("legs per the registered gate; everything outside `gate` "
                 "is REPORTED, not gating; diagnostic_labels are the DR-1 / "
                 "DR-2 / DR-3 / DR-4 NON-CRITERION labels (present only in "
                 "their modes)"),
    }

    state_rows = []
    for fs in arms:
        for v in VARIANTS:
            for i, k in enumerate(cluster_keys):
                state_rows.append({
                    "arm": fs, "variant": str(v), "pop": k[0],
                    "orig_prompt_idx": k[1],
                    "sse": sse_cl[fs][v][i], "count": cnt_cl[i]})
    for i, k in enumerate(cluster_keys):
        state_rows.append({"arm": TRIVIAL_ARM, "variant": "live",
                           "pop": k[0], "orig_prompt_idx": k[1],
                           "sse": triv_cl[i], "count": cnt_cl[i]})

    if write:
        state_path = Path(str(out) + ".state.jsonl")
        with state_path.open("w") as sf:
            sf.write(json.dumps({
                "header": True, **{k: v for k, v in meta.items()
                                   if k != "started_unix"},
                "split": {p: {k: sorted(int(i) for i in v)
                              for k, v in s.items()}
                          for p, s in split.items()}}) + "\n")
            for row in state_rows:
                sf.write(json.dumps(row) + "\n")
        out.write_text(json.dumps(summary, indent=2))
    return {"summary": summary, "state_rows": state_rows, "meta": meta,
            "chosen": chosen, "split": split, "n_slots": n_slots,
            "feat_std": feat_std, "targ_std": targ_std, "lo_hi": lo_hi,
            "weights_live": w_live, "runs": runs, "role_of": role_of,
            "h_dim": h_dim}


# ---------------------------------------------------------------------------
# STAGE-A EXPORT (OQ-16 STAGE-A FREEZE, BLUEPRINT 2026-09-04): the frozen
# reconstruction the actuator arms inject. Binding-gated on the committed
# DR-4 summary (bit-exact recompute on the pinned fields AND a weight-level
# binding: a TRAIN refit reproduces the DR-4 live weights within
# STAGE_A_WEIGHT_TOL), then: cross-fitted h_hat for adapter training
# (N_FOLDS folds per population by the pinned split permutation — every
# prompt's h_hat from a fit that never saw it), and a full refit on all
# prompts for the verdict-time weights — every fit at the DR-4 VAL-chosen
# live lambda of its arm (no re-selection). Export self-check: the live
# single-row path bit-equals a single-row batch call and deviates from the
# batch path by <= the pinned bound. Weights + h_hat are gitignored (size);
# their shas live in the committed export summary.
# ---------------------------------------------------------------------------

STAGE_A_BIND_FIELDS = ("gate", "reported_deltas", "test_mse", "r2",
                       "chosen_lambda", "diagnostic_labels", "feature_dims",
                       "modes")
STAGE_A_BATCH_TOL = 1e-9   # standardized units; judgment-call, measured at export
STAGE_A_WEIGHT_TOL = 1e-9  # weight-level binding to the DR-4 live TRAIN fit
N_FOLDS = 5                # cross-fit folds per population (critic advisory)
DR4_OUT = REGISTERED_OUT.with_name("oq16_stage_r_dr4.json")
EXPORT_NPZ = REGISTERED_OUT.with_name("oq16_recon_weights.npz")
EXPORT_HHAT = REGISTERED_OUT.with_name("oq16_recon_hhat")
EXPORT_SUMMARY = REGISTERED_OUT.with_name("oq16_stage_a_export.json")


def _json_norm(x):
    return json.loads(json.dumps(x))


def fold_index(n_prompts: int, n_folds: int = N_FOLDS) -> np.ndarray:
    """Cross-fit fold of each prompt id: its position in the pinned split
    permutation (outcome_head.SPLIT_SEED) mod n_folds — deterministic,
    role-agnostic, ~equal folds per population, so every prompt's h_hat
    comes from a fit on (n_folds-1)/n_folds of its population (168/210 at
    the registered size) — one ridge quality for the whole training set."""
    from sideband.outcome_head import SPLIT_SEED
    perm = np.random.default_rng(SPLIT_SEED).permutation(n_prompts)
    pos = np.empty(n_prompts, dtype=np.int64)
    pos[perm] = np.arange(n_prompts)
    return pos % n_folds


def fit_arms(runs: list, keep, arms: tuple, lam_by_arm: dict, n_slots: int,
             h_dim: int) -> dict:
    """Ridge fit of every arm on the rows of prompts with keep(pop, pid)
    True — the pipeline's arithmetic verbatim (fit-side moments +
    support, clip, Standardizer, augment, Gram/B, ridge_fit; live target
    only). Returns per-arm Standardizer / support / weights and the
    target Standardizer."""
    mom = {fs: None for fs in arms}
    lo_hi = {fs: None for fs in arms}
    y_mom = None
    n_rows = 0
    for run in runs:
        for pid, z in iter_prompts(run):
            if not keep(run["pop"], pid):
                continue
            y = h_target(z)
            if y_mom is None:
                y_mom = [np.zeros(h_dim), np.zeros(h_dim)]
            y_mom[0] += y.sum(0)
            y_mom[1] += (y * y).sum(0)
            n_rows += y.shape[0]
            for fs in arms:
                x = arm_features(z, fs, n_slots=n_slots)
                if mom[fs] is None:
                    mom[fs] = [np.zeros(x.shape[1]), np.zeros(x.shape[1])]
                    lo_hi[fs] = [x.min(0).copy(), x.max(0).copy()]
                mom[fs][0] += x.sum(0)
                mom[fs][1] += (x * x).sum(0)
                np.minimum(lo_hi[fs][0], x.min(0), out=lo_hi[fs][0])
                np.maximum(lo_hi[fs][1], x.max(0), out=lo_hi[fs][1])
    if n_rows == 0:
        raise SystemExit("fit_arms: no rows in the fit roles")
    feat_std = {fs: Standardizer.from_moments(mom[fs][0], mom[fs][1], n_rows)
                for fs in arms}
    targ_std = Standardizer.from_moments(y_mom[0], y_mom[1], n_rows)

    def prep(fs, x_raw):
        return augment(feat_std[fs].apply(np.clip(x_raw, lo_hi[fs][0],
                                                  lo_hi[fs][1])))

    dims = {fs: mom[fs][0].shape[0] for fs in arms}
    G = {fs: np.zeros((dims[fs] + 1, dims[fs] + 1)) for fs in arms}
    B = {fs: np.zeros((dims[fs] + 1, h_dim)) for fs in arms}
    for run in runs:
        for pid, z in iter_prompts(run):
            if not keep(run["pop"], pid):
                continue
            y = targ_std.apply(h_target(z))
            for fs in arms:
                xa = prep(fs, arm_features(z, fs, n_slots=n_slots))
                G[fs] += xa.T @ xa
                B[fs] += xa.T @ y
    w = {fs: ridge_fit(G[fs], B[fs], lam_by_arm[fs]) for fs in arms}
    return {"feat_std": feat_std, "lo_hi": lo_hi, "w": w, "targ_std": targ_std,
            "n_rows": n_rows}


def _live_from_fit(fit: dict, arm: str, n_slots: int):
    """A LiveReconstructor over in-memory fit results (no npz)."""
    from sideband.recon import LiveReconstructor
    lr = LiveReconstructor.__new__(LiveReconstructor)
    lr.arm = arm
    lr.n_slots = int(n_slots)
    lr.std = fit["feat_std"][arm]
    lr.lo, lr.hi = fit["lo_hi"][arm]
    lr.w = fit["w"][arm]
    lr.t_mu, lr.t_sd = fit["targ_std"].mu, fit["targ_std"].sd
    return lr


def stage_a_export(root: Path, arms: tuple, overwrite: bool = False,
                   n_slots: int | None = None, lambda_grid: tuple | None = None,
                   committed: Path = DR4_OUT, npz_path: Path = EXPORT_NPZ,
                   hhat_dir: Path = EXPORT_HHAT,
                   summary_path: Path = EXPORT_SUMMARY,
                   self_check_blocks: int = 1000) -> dict:
    if npz_path.exists() and not overwrite:
        raise SystemExit(f"{npz_path} exists; pass --overwrite to redo")
    committed_json = json.loads(committed.read_text())

    # (i) recompute the DR-4 configuration in-process + BINDING GATE
    res = pipeline(root, out=None, n_slots=n_slots, lambda_grid=lambda_grid,
                   write=False, feature_clip=True, freetok=True, union=True,
                   freetok2=True, return_weights=arms)
    for field in STAGE_A_BIND_FIELDS:
        got, want = _json_norm(res["summary"][field]), _json_norm(committed_json[field])
        if got != want:
            raise SystemExit(f"BINDING GATE REFUSED: recomputed {field!r} != "
                             f"committed {committed}\n got: {got}\nwant: {want}")
    print("[stage-a] binding gate PASS: recompute bit-exact on "
          + ", ".join(STAGE_A_BIND_FIELDS))
    ns = res["n_slots"]
    runs, role_of, h_dim = res["runs"], res["role_of"], res["h_dim"]
    lam_by_arm = {fs: float(res["chosen"][fs]["live"]) for fs in arms}

    # (i-b) WEIGHT-LEVEL BINDING: fit_arms on the TRAIN prompts must
    # reproduce the DR-4 live weights (same rows, moments, clip, lambda;
    # the DR-4 solve carried six RHS blocks, this one carries one, so
    # LAPACK blocking may differ at the ulp — measured, bounded, recorded)
    bind = fit_arms(runs, lambda pop, pid: role_of[(pop, pid)] == "train",
                    arms, lam_by_arm, ns, h_dim)
    weight_binding = {}
    for fs in arms:
        dev = float(np.max(np.abs(bind["w"][fs] - res["weights_live"][fs])))
        weight_binding[fs] = {"max_abs_dev": dev,
                              "bit_exact": bool(np.array_equal(
                                  bind["w"][fs], res["weights_live"][fs]))}
        if dev > STAGE_A_WEIGHT_TOL:
            raise SystemExit(f"WEIGHT BINDING REFUSED: {fs} TRAIN refit deviates "
                             f"{dev:.3e} from the DR-4 live weights")
    print(f"[stage-a] weight binding PASS: {weight_binding}")

    # (ii) cross-fitted h_hat for adapter training: N_FOLDS folds per
    # population by the pinned permutation; every prompt's h_hat comes
    # from a fit that never saw it, at (N_FOLDS-1)/N_FOLDS of its
    # population — one ridge quality for the whole training set
    n_pop = {}
    for (pop, pid) in role_of:
        n_pop[pop] = max(n_pop.get(pop, 0), pid + 1)
    fold_of = {pop: fold_index(n) for pop, n in n_pop.items()}
    fits = {}
    fold_readout: dict = {}
    hhat_shas: dict = {}
    fold_of_prompt: dict = {}
    hhat_dir.mkdir(parents=True, exist_ok=True)
    for k in range(N_FOLDS):
        fold = str(k)
        fit = fit_arms(runs, lambda pop, pid: int(fold_of[pop][pid]) != k,
                       arms, lam_by_arm, ns, h_dim)
        fits[fold] = fit
        sse = {fs: 0.0 for fs in arms}
        sse_triv = 0.0
        n_pos = 0
        n_pred = 0
        for run in runs:
            run_dir = hhat_dir / run["stem"]
            run_dir.mkdir(parents=True, exist_ok=True)
            for pid, z in iter_prompts(run):
                if int(fold_of[run["pop"]][pid]) != k:
                    continue
                y_std = fit["targ_std"].apply(h_target(z))
                out = {"fold": np.array(fold), "orig_prompt_idx": np.int64(pid)}
                for fs in arms:
                    lr = _live_from_fit(fit, fs, ns)
                    pred_std = lr.predict_std(arm_features(z, fs, n_slots=ns))
                    err = pred_std - y_std
                    sse[fs] += float((err * err).sum())
                    out[fs] = (lr.t_mu + lr.t_sd * pred_std).astype(np.float32)
                sse_triv += float((y_std * y_std).sum())
                n_pos += y_std.size
                n_pred += 1
                f = run_dir / f"p{pid:03d}.npz"
                np.savez(f, **out)
                hhat_shas[f"{run['stem']}/{f.name}"] = hashlib.sha256(
                    f.read_bytes()).hexdigest()
                fold_of_prompt[f"{run['pop']}:{pid}"] = fold
        fold_readout[fold] = {
            "n_fit_rows": fit["n_rows"], "n_pred_prompt_runs": n_pred,
            "n_pred_positions": n_pos,
            "std_mse": {fs: sse[fs] / n_pos for fs in arms},
            "trivial_std_mse": sse_triv / n_pos,
        }
        print(f"[stage-a] fold {fold}: {fit['n_rows']} fit rows -> "
              f"{ {fs: round(sse[fs] / n_pos, 5) for fs in arms} } "
              f"(trivial {sse_triv / n_pos:.5f})")

    # (iii) full refit -> verdict-time weights
    full = fit_arms(runs, lambda pop, pid: True, arms, lam_by_arm, ns, h_dim)
    arrays = {"target_mu": full["targ_std"].mu, "target_sd": full["targ_std"].sd}
    for fs in arms:
        arrays[f"{fs}_mu"] = full["feat_std"][fs].mu
        arrays[f"{fs}_sd"] = full["feat_std"][fs].sd
        arrays[f"{fs}_lo"] = full["lo_hi"][fs][0]
        arrays[f"{fs}_hi"] = full["lo_hi"][fs][1]
        arrays[f"{fs}_w"] = full["w"][fs]
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(npz_path, **arrays)

    # (iv) EXPORT SELF-CHECK on the exported npz through the live class
    from sideband.recon import LiveReconstructor, block_dict_from_anchor  # noqa: F401
    from sideband.outcome_head import SUMMARY_KEYS
    live = {fs: LiveReconstructor(npz_path, fs, n_slots=ns) for fs in arms}
    checked = 0
    max_dev = 0.0
    for pid, z in iter_prompts(runs[0]):
        n = int(np.asarray(z["gamma_used"]).shape[0])
        for fs in arms:
            x = arm_features(z, fs, n_slots=ns)
            batch = live[fs].reconstruct_rows(x)
            for b in range(n):
                summ = {k: np.asarray(z[k])[b] for k in SUMMARY_KEYS}
                got = live[fs].reconstruct(summ, np.asarray(z["slots"])[b])
                single = live[fs].reconstruct_rows(x[b:b + 1])[0]
                if not np.array_equal(got, single):
                    raise SystemExit(f"EXPORT SELF-CHECK FAILED (a): {fs} prompt "
                                     f"{pid} block {b} — live path != single-row")
                dev = float(np.max(np.abs((batch[b] - got) / live[fs].t_sd)))
                max_dev = max(max_dev, dev)
                if dev > STAGE_A_BATCH_TOL:
                    raise SystemExit(f"EXPORT SELF-CHECK FAILED (b): {fs} prompt "
                                     f"{pid} block {b} — batch deviation {dev:.3e}"
                                     f" > {STAGE_A_BATCH_TOL}")
        checked += n
        if checked >= self_check_blocks:
            break
    print(f"[stage-a] export self-check PASS: {checked} blocks x {len(arms)} "
          f"arms; single-row bit-equal; max batch deviation {max_dev:.3e}")

    summary = {
        "registration": "OQ-16 STAGE-A FREEZE (BLUEPRINT 2026-09-04)",
        "git_commit": _git_commit(), "numpy_version": np.__version__,
        "arms": list(arms), "lambda_by_arm": lam_by_arm, "n_slots": ns,
        "binding": {"committed": committed.name,
                    "committed_sha256": hashlib.sha256(
                        committed.read_bytes()).hexdigest(),
                    "bound_fields": list(STAGE_A_BIND_FIELDS)},
        "weight_binding": {"tol": STAGE_A_WEIGHT_TOL, **weight_binding},
        "n_folds": N_FOLDS,
        "folds": fold_readout,
        "fold_of_prompt": fold_of_prompt,
        "full_fit_rows": full["n_rows"],
        "weights_npz": npz_path.name,
        "weights_sha256": hashlib.sha256(npz_path.read_bytes()).hexdigest(),
        "hhat_dir": hhat_dir.name, "hhat_sha256": hhat_shas,
        "self_check_blocks": checked, "self_check_max_batch_deviation": max_dev,
        "self_check_tol": STAGE_A_BATCH_TOL,
        "note": ("fold readouts are REPORTED cross-fit reconstruction quality "
                 "(standardized on each fold's own fit moments); verdict "
                 "weights are the full refit at the DR-4 live lambdas; h_hat "
                 "stored float32"),
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[stage-a] wrote {npz_path} (sha {summary['weights_sha256'][:12]}..), "
          f"{len(hhat_shas)} h_hat files, {summary_path}")
    return {"summary": summary, "fits": fits, "full": full, "res": res}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="results/real")
    ap.add_argument("--out", default=None)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--n-slots", type=int, default=None,
                    help="synthetic-test sizing only; refuses the registered out")
    ap.add_argument("--lambdas", default=None,
                    help="synthetic-test sizing only; refuses the registered out")
    ap.add_argument("--feature-clip", action="store_true",
                    help="DR-1 mode: clip features to TRAIN support; refuses "
                         "the registered out")
    ap.add_argument("--freetok", action="store_true",
                    help="DR-2 mode: add the FREETOK arm; refuses the "
                         "registered out")
    ap.add_argument("--union", action="store_true",
                    help="DR-3 mode: add the UNION/UNIONNOISE arms (needs "
                         "--freetok); refuses the registered out")
    ap.add_argument("--freetok2", action="store_true",
                    help="DR-4 mode: add the FREETOK2 equal-dims better-"
                         "token-encoding comparator (needs --union); "
                         "refuses the registered out")
    ap.add_argument("--stage-a-export", default=None,
                    help="STAGE-A FREEZE: comma-separated arms to export "
                         "(binding-gated on the committed DR-4 summary; "
                         "writes the gitignored weights npz + h_hat dir and "
                         "the committed export summary; takes no other "
                         "sizing/mode flags; --out is ignored)")
    args = ap.parse_args()

    if args.stage_a_export:
        if any((args.n_slots, args.lambdas, args.feature_clip, args.freetok,
                args.union, args.freetok2)):
            raise SystemExit("--stage-a-export takes no sizing/mode flags "
                             "(it runs the DR-4 configuration verbatim)")
        arms = tuple(a.strip() for a in args.stage_a_export.split(",") if a.strip())
        stage_a_export(Path(args.data_root), arms, overwrite=args.overwrite)
        return

    lambda_grid = (tuple(float(x) for x in args.lambdas.split(","))
                   if args.lambdas else None)
    overrides = {}
    if args.n_slots is not None and args.n_slots != N_SLOTS:
        overrides["n_slots"] = args.n_slots
    if lambda_grid is not None and lambda_grid != RECON_LAMBDA_GRID:
        overrides["lambda_grid"] = list(lambda_grid)
    if args.feature_clip:
        overrides["feature_clip"] = True
    if args.freetok:
        overrides["freetok"] = True
    if args.union:
        overrides["union"] = True
    if args.freetok2:
        overrides["freetok2"] = True
    if not args.out:
        raise SystemExit("--out is required (except with --stage-a-export)")
    out = Path(args.out)
    if overrides and out.resolve() == REGISTERED_OUT.resolve():
        raise SystemExit("sizing/mode overrides may not write the registered "
                         "output path (registered-outs guard)")
    if out.exists() and not args.overwrite:
        raise SystemExit(f"{out} exists; pass --overwrite to redo")

    res = pipeline(Path(args.data_root), out, n_slots=args.n_slots,
                   lambda_grid=lambda_grid, feature_clip=args.feature_clip,
                   freetok=args.freetok, union=args.union,
                   freetok2=args.freetok2)
    s = res["summary"]
    print(f"[stage-r] label: {s['gate']['label']}")
    print(f"[stage-r] delta_noise live: {s['delta_noise']['live']}")
    print(f"[stage-r] delta_free  live: {s['delta_free']['live']}")
    print(f"[stage-r] tel_vs_trivial: "
          f"{s['reported_deltas']['tel_vs_trivial']['pooled']}")
    for k, v in s["diagnostic_labels"].items():
        print(f"[stage-r] {k}: {v}")
    print(f"[stage-r] wrote {out}")


if __name__ == "__main__":
    main()

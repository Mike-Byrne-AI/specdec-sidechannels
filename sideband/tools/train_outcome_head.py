"""OQ-15 Stage I driver (FOLD-BACK #1 ARC REGISTRATION, BLUEPRINT
2026-09-03). CPU-only; no torch; deterministic given the registered
constants — no training seed exists.

Reads the four registered arm-1 byproduct runs (verdict seeds 0/1 = gate
data; val/tapcal = TRAIN-only rows), verifies every npz sha256 against the
committed run summaries, trains the 12 gate ridge heads (3 feature sets x
offsets 1-4) plus the reported-only binary variant, and evaluates the ONE
gate criterion:

    delta_noise = pooled TEST MSE(NOISE) - pooled TEST MSE(TEL)
    via stats.paired_cluster_delta_ci  (PASS iff CI95 lower > 0)

plus the registered reported quantities (delta_free, per-offset deltas,
trivial train-mean baselines, binary AUC / precision@0.20, noise self-map
sliver). Outputs next to --out (house conventions: meta BEFORE the run,
state jsonl as the recompute surface, summary as completion marker):
  <out>.meta.json, <out>.state.jsonl, <out> (summary json)

The split is over prompt ids (default_rng(15), 60/20/20 -> 126/42/42 at
the registered N=210); N is read from the gate runs so the synthetic CI
test can exercise the identical code path at a small N. Lambda per head
by VAL pooled MSE on the head's own target (the only selection DOF;
binary heads use the same rule on their own target, reported-only).

--stage-c-freeze (STAGE-C FREEZE, BLUEPRINT 2026-09-03): re-runs the
pipeline in-process, REFUSES unless it reproduces the committed
results/real/oq15_stage1.json bit-exactly on the pinned fields, trains
the offset-5 heads on the arm-5 byproducts (evidence
results/real/oq15_offset5.json + state), writes
results/real/oq15_head_weights.npz (+ meta json), and runs the export
self-check (>= 1000 blocks scored through the npz via HeadScorer must
bit-equal the training pipeline's predictions).
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

from sideband.outcome_head import (  # noqa: E402
    FEATURE_SETS, GATE_OFFSETS, LAMBDA_GRID, HeadScorer, Standardizer,
    analytic_target, augment, binary_target, block_core_features,
    noise_self_maps, offset_rows, precision_at_coverage, prompt_index_map,
    auc_score, predict_clipped, qsig_cols, ridge_fit, stage1_split,
    verify_byproduct)
from sideband.stats import paired_cluster_delta_ci  # noqa: E402

GATE_RUNS = (("k3_verdict_arm1", 0), ("k3_verdict_s1_arm1", 1))
TRAIN_ONLY_RUNS = ("k3_val_arm1", "k3_tapcal_arm1")
HEADS = tuple((fs, off) for fs in FEATURE_SETS for off in GATE_OFFSETS)
# STAGE-C FREEZE: offset-5 heads train on the arm-5 byproducts (both
# verdict seeds; fixed-schedule but off-policy w.r.t. gamma-4, disclosed
# — the seed-0 run is the VOIDED verdict run, arm 5 scheduler-inert).
OFFSET5_RUNS = ("k3_verdict_arm5", "k3_verdict_s1_arm5")
FREEZE_BIND_FIELDS = ("delta_noise", "delta_free", "per_offset", "test_mse",
                      "per_head_test_mse", "chosen_lambda")


def load_run(root: Path, stem: str) -> dict:
    byp = root / f"{stem}.jsonl.byproduct"
    summary = root / f"{stem}.summary.json"
    gen = root / f"{stem}.gen.jsonl"
    files = verify_byproduct(byp, summary)
    idx_map = prompt_index_map(gen)
    return {"stem": stem, "files": files, "idx_map": idx_map,
            "summary_sha": hashlib.sha256(summary.read_bytes()).hexdigest()}


def iter_prompts(run: dict):
    for f in run["files"]:
        p_idx = int(f.stem[1:])
        yield run["idx_map"][p_idx], dict(np.load(f))


def head_xy(cores: dict, z: dict, fs: str, off: int, binary: bool):
    """Standardizable design columns + target for one head on one prompt."""
    m = offset_rows(z, off)
    x = np.hstack([cores[fs], qsig_cols(z, off)])
    if binary:
        mb, y = binary_target(z, off)
        return x[mb], y
    return x[m], analytic_target(z, off)


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


def pipeline(root: Path, out: Path, n_slots: int, lambda_grid: tuple,
             stale_seed: int | None, overrides: dict,
             write: bool = True) -> dict:
    """The registered Stage-I compute, extracted verbatim from the original
    main() (STAGE-C FREEZE refactor — the binding gate machine-checks that
    this move preserved every number). write=False skips all file output
    (the freeze mode's in-process recompute)."""
    gate = [load_run(root, stem) for stem, _seed in GATE_RUNS]
    extra = [load_run(root, stem) for stem in TRAIN_ONLY_RUNS]
    n_files = {r["stem"]: len(r["files"]) for r in gate}
    if len(set(n_files.values())) != 1:
        raise SystemExit(f"gate runs disagree on prompt count: {n_files}")
    n_prompts = next(iter(n_files.values()))
    sizing = {k: v for k, v in overrides.items()
              if k in ("n_slots", "lambda_grid")}
    if not sizing and n_prompts != 210:
        raise SystemExit(f"registered run expects 210 verdict prompts, got {n_prompts}")
    for r in gate:
        pids_r = {r["idx_map"][int(f.stem[1:])] for f in r["files"]}
        if pids_r != set(range(n_prompts)):
            raise SystemExit(f"{r['stem']}: prompt ids do not cover "
                             f"range({n_prompts}) — split would silently drop rows")
    split = stage1_split(n_prompts)
    in_split = {name: set(int(i) for i in idx) for name, idx in split.items()}

    meta = {
        "tool": "train_outcome_head", "registration": "OQ-15 FOLD-BACK #1 (BLUEPRINT 2026-09-03)",
        "git_commit": _git_commit(),
        "started_unix": time.time(), "n_prompts": n_prompts,
        "split_sizes": {k: len(v) for k, v in split.items()},
        "gate_runs": [r["stem"] for r in gate],
        "train_only_runs": [r["stem"] for r in extra],
        "summary_sha256": {r["stem"]: r["summary_sha"] for r in gate + extra},
        "lambda_grid": list(lambda_grid), "n_slots": n_slots,
        "sizing_overrides": overrides,
    }
    if write:
        out.parent.mkdir(parents=True, exist_ok=True)
        Path(str(out) + ".meta.json").write_text(json.dumps(meta, indent=2))

    run_index = {stem: i for i, stem in enumerate(
        [s for s, _ in GATE_RUNS] + list(TRAIN_ONLY_RUNS))}

    def maybe_stale(stem: str, pid: int, z: dict) -> dict:
        """DI-1: replace the TARGET rows (analytic + acc_flags) with a
        seeded random permutation of the prompt-run's own blocks;
        features untouched. Per-row isolated RNG so the permutation is
        identical across passes."""
        if stale_seed is None:
            return z
        n = int(np.asarray(z["gamma_used"]).shape[0])
        perm = np.random.default_rng(
            stale_seed * 1_000_000 + run_index[stem] * 10_000 + pid
        ).permutation(n)
        return {**z, "analytic": np.asarray(z["analytic"])[perm],
                "acc_flags": np.asarray(z["acc_flags"])[perm]}

    def train_rows():
        for run in gate:
            for pid, z in iter_prompts(run):
                if pid in in_split["train"]:
                    yield ("verdict", pid), maybe_stale(run["stem"], pid, z)
        for run in extra:
            for pid, z in iter_prompts(run):
                yield ("valpop", pid), maybe_stale(run["stem"], pid, z)

    def split_rows(name: str):
        for run in gate:
            for pid, z in iter_prompts(run):
                if pid in in_split[name]:
                    yield run["stem"], pid, maybe_stale(run["stem"], pid, z)

    def cores_of(z: dict) -> dict:
        return {fs: block_core_features(z, fs, n_slots=n_slots)
                for fs in FEATURE_SETS}

    # PASS 1: standardizer moments + train target means (trivial baseline)
    mom: dict = {}
    y_sum = {(off, b): [0.0, 0] for off in GATE_OFFSETS for b in (False, True)}
    for _key, z in train_rows():
        cores = cores_of(z)
        for fs, off in HEADS:
            for binary in (False, True):
                x, y = head_xy(cores, z, fs, off, binary)
                k = (fs, off, binary)
                if k not in mom:
                    mom[k] = [np.zeros(x.shape[1]), np.zeros(x.shape[1]), 0]
                mom[k][0] += x.sum(axis=0)
                mom[k][1] += (x * x).sum(axis=0)
                mom[k][2] += x.shape[0]
                if fs == "free":
                    y_sum[(off, binary)][0] += float(y.sum())
                    y_sum[(off, binary)][1] += len(y)
    std = {k: Standardizer.from_moments(*v) for k, v in mom.items()}
    y_mean = {k: v[0] / v[1] for k, v in y_sum.items()}

    # PASS 2: gram/xty accumulation on standardized augmented rows
    gram: dict = {}
    for _key, z in train_rows():
        cores = cores_of(z)
        for fs, off in HEADS:
            for binary in (False, True):
                k = (fs, off, binary)
                x, y = head_xy(cores, z, fs, off, binary)
                xa = augment(std[k].apply(x))
                if k not in gram:
                    d = xa.shape[1]
                    gram[k] = [np.zeros((d, d)), np.zeros(d)]
                gram[k][0] += xa.T @ xa
                gram[k][1] += xa.T @ y
    weights = {k + (lam,): ridge_fit(g, b, lam)
               for k, (g, b) in gram.items() for lam in lambda_grid}

    # PASS 3: lambda selection by VAL pooled MSE (per head, own target)
    val_se: dict = {k: {lam: [0.0, 0] for lam in lambda_grid} for k in gram}
    for _stem, _pid, z in split_rows("val"):
        cores = cores_of(z)
        for k in gram:
            fs, off, binary = k
            x, y = head_xy(cores, z, fs, off, binary)
            xs = std[k].apply(x)
            for lam in lambda_grid:
                pred = predict_clipped(weights[k + (lam,)], xs)
                val_se[k][lam][0] += float(((pred - y) ** 2).sum())
                val_se[k][lam][1] += len(y)
    chosen = {}
    for k, per_lam in val_se.items():
        mses = {lam: se / n for lam, (se, n) in per_lam.items()}
        # registered tie-break: toward the LARGER lambda (more regularized)
        chosen[k] = min(lambda_grid, key=lambda lam: (mses[lam], -lam))

    # PASS 4: TEST evaluation -> state rows + pooled gate arithmetic
    state_rows = []
    cluster: dict = {}
    bin_scores: dict = {(fs, off): [[], []] for fs, off in HEADS}
    self_map_prompt_runs = 0
    for stem, pid, z in split_rows("test"):
        n_blocks = int(np.asarray(z["gamma_used"]).shape[0])
        if noise_self_maps(n_blocks):
            self_map_prompt_runs += 1
        cores = cores_of(z)
        row = {"run": stem, "prompt": pid, "n_blocks": n_blocks}
        for k in gram:
            fs, off, binary = k
            x, y = head_xy(cores, z, fs, off, binary)
            pred = predict_clipped(weights[k + (chosen[k],)], std[k].apply(x))
            se = float(((pred - y) ** 2).sum())
            tag = f"{fs}_off{off}" + ("_bin" if binary else "")
            row[tag] = {"se": se, "n": len(y)}
            if binary:
                bin_scores[(fs, off)][0].extend(pred.tolist())
                bin_scores[(fs, off)][1].extend(y.tolist())
            else:
                c = cluster.setdefault(pid, {})
                agg = c.setdefault(fs, [0.0, 0])
                agg[0] += se
                agg[1] += len(y)
                per_off = c.setdefault(f"{fs}_off{off}", [0.0, 0])
                per_off[0] += se
                per_off[1] += len(y)
                base = c.setdefault(f"base_off{off}", [0.0, 0])
                base[0] += float(((y_mean[(off, False)] - y) ** 2).sum())
                base[1] += len(y)
        state_rows.append(row)

    pids = sorted(cluster)
    trials = np.array([cluster[p]["free"][1] for p in pids], dtype=float)
    for p in pids:  # pooled trials must agree across feature sets (paired)
        ns = {fs: cluster[p][fs][1] for fs in FEATURE_SETS}
        if len(set(ns.values())) != 1:
            raise SystemExit(f"unpaired trial counts at prompt {p}: {ns}")

    def delta(a_fs: str, b_fs: str, suffix: str = ""):
        sa = np.array([cluster[p][a_fs + suffix][0] for p in pids])
        sb = np.array([cluster[p][b_fs + suffix][0] for p in pids])
        t = np.array([cluster[p][a_fs + suffix][1] for p in pids], dtype=float)
        d, lo, hi = paired_cluster_delta_ci(sa, sb, t, n_boot=2000, seed=0)
        return {"delta": d, "ci95": [lo, hi]}

    delta_noise = delta("noise", "tel")
    delta_free = delta("free", "tel")
    stage1_pass = delta_noise["ci95"][0] > 0.0
    summary = {
        "registration": meta["registration"],
        "criterion": "delta_noise = pooled TEST MSE(NOISE) - MSE(TEL); PASS iff CI95 lower > 0",
        "delta_noise": delta_noise, "delta_free": delta_free,
        "per_offset": {
            f"off{off}": {"noise_minus_tel": delta("noise", "tel", f"_off{off}"),
                          "free_minus_tel": delta("free", "tel", f"_off{off}")}
            for off in GATE_OFFSETS},
        "test_mse": {f"{fs}": sum(cluster[p][fs][0] for p in pids) / trials.sum()
                     for fs in FEATURE_SETS},
        "per_head_test_mse": {
            f"{fs}_off{off}": (sum(cluster[p][f"{fs}_off{off}"][0] for p in pids)
                               / sum(cluster[p][f"{fs}_off{off}"][1] for p in pids))
            for fs in FEATURE_SETS for off in GATE_OFFSETS},
        "trivial_baseline_test_mse": {
            f"off{off}": (sum(cluster[p][f"base_off{off}"][0] for p in pids)
                          / sum(cluster[p][f"base_off{off}"][1] for p in pids))
            for off in GATE_OFFSETS},
        "chosen_lambda": {f"{fs}_off{off}" + ("_bin" if b else ""): chosen[(fs, off, b)]
                          for fs, off, b in chosen},
        "binary_sidebar_survival_conditioned": {
            f"{fs}_off{off}": {
                "auc": auc_score(np.array(bin_scores[(fs, off)][0]),
                                 np.array(bin_scores[(fs, off)][1])),
                "precision_at_0.20_accept_tail": precision_at_coverage(
                    np.array(bin_scores[(fs, off)][0]),
                    np.array(bin_scores[(fs, off)][1])),
                # ledger (c)'s failure-predictor tail: predicted-reject
                "precision_at_0.20_reject_tail": precision_at_coverage(
                    1.0 - np.array(bin_scores[(fs, off)][0]),
                    1.0 - np.array(bin_scores[(fs, off)][1]))}
            for fs, off in HEADS},
        "noise_self_map_prompt_runs": self_map_prompt_runs,
        "n_test_clusters": len(pids), "n_test_positions": int(trials.sum()),
        "stage1_pass": bool(stage1_pass),
        "branch": ("STAGE I PASS -> Stage C (user-gated)" if stage1_pass
                   else "INFORMATION-CEILING NULL (skip OQ-16, lane stops)"),
        "sizing_overrides": overrides,
        "note": "delta_free and everything below the criterion are REPORTED, not gating",
    }

    if write:
        state_path = Path(str(out) + ".state.jsonl")
        with state_path.open("w") as sf:
            sf.write(json.dumps({"header": True, **meta,
                                 "split": {k: sorted(int(i) for i in v)
                                           for k, v in split.items()}}) + "\n")
            for row in state_rows:
                sf.write(json.dumps(row) + "\n")
        out.write_text(json.dumps(summary, indent=2))
    return {"summary": summary, "state_rows": state_rows, "meta": meta,
            "weights": weights, "std": std, "chosen": chosen, "gate": gate,
            "split": split, "n_slots": n_slots}


def train_offset5(root: Path, out5: Path, lambda_grid: tuple,
                  overwrite: bool, n_slots: int | None = None) -> dict:
    """STAGE-C FREEZE (ii): offset-5 heads (FREE and TEL) on the arm-5
    byproducts, both verdict seeds — same registered split /
    standardizer / lambda recipe, target = analytic at offset 5,
    features = core + q_sig[0:2]. TEST MSE vs the trivial train-mean
    baseline is REPORTED, never gating. Evidence: <out5> + sha-headed
    state (committed) + meta."""
    if out5.exists() and not overwrite:
        raise SystemExit(f"{out5} exists; pass --overwrite to redo")
    runs = [load_run(root, stem) for stem in OFFSET5_RUNS]
    n_prompts = len(runs[0]["files"])
    for r in runs:
        pids_r = {r["idx_map"][int(f.stem[1:])] for f in r["files"]}
        if pids_r != set(range(n_prompts)):
            raise SystemExit(f"{r['stem']}: prompt ids do not cover range({n_prompts})")
    split = stage1_split(n_prompts)
    in_split = {name: set(int(i) for i in idx) for name, idx in split.items()}
    fams = ("free", "tel")
    off = 5

    meta = {
        "tool": "train_outcome_head --stage-c-freeze offset5",
        "registration": "OQ-15 STAGE-C FREEZE (BLUEPRINT 2026-09-03)",
        "git_commit": _git_commit(), "started_unix": time.time(),
        "runs": [r["stem"] for r in runs],
        "summary_sha256": {r["stem"]: r["summary_sha"] for r in runs},
        "off_policy_disclosure": ("fixed gamma-6 schedule, off-policy w.r.t. "
                                  "gamma-4; the seed-0 run is the VOIDED "
                                  "seed-0 verdict run (arm 5 scheduler-inert; "
                                  "void resolved at F-19) — disclosed per the "
                                  "STAGE-C FREEZE"),
        "lambda_grid": list(lambda_grid),
    }
    Path(str(out5) + ".meta.json").write_text(json.dumps(meta, indent=2))

    def rows(names: set[str] | None):
        for run in runs:
            for pid, z in iter_prompts(run):
                if names is None or pid in names:
                    yield run["stem"], pid, z

    from sideband.outcome_head import N_SLOTS as _NS
    ns = n_slots if n_slots is not None else _NS

    def xy(z: dict, fam: str):
        m = offset_rows(z, off)
        x = np.hstack([block_core_features(z, fam, n_slots=ns),
                       qsig_cols(z, off)])
        return x[m], analytic_target(z, off)

    mom = {f: None for f in fams}
    y_tr = [0.0, 0]
    for _stem, _pid, z in rows(in_split["train"]):
        for f in fams:
            x, y = xy(z, f)
            if mom[f] is None:
                mom[f] = [np.zeros(x.shape[1]), np.zeros(x.shape[1]), 0]
            mom[f][0] += x.sum(axis=0)
            mom[f][1] += (x * x).sum(axis=0)
            mom[f][2] += x.shape[0]
            if f == "free":
                y_tr[0] += float(y.sum())
                y_tr[1] += len(y)
    std = {f: Standardizer.from_moments(*mom[f]) for f in fams}
    y_mean = y_tr[0] / y_tr[1]

    gram = {f: None for f in fams}
    for _stem, _pid, z in rows(in_split["train"]):
        for f in fams:
            x, y = xy(z, f)
            xa = augment(std[f].apply(x))
            if gram[f] is None:
                gram[f] = [np.zeros((xa.shape[1], xa.shape[1])),
                           np.zeros(xa.shape[1])]
            gram[f][0] += xa.T @ xa
            gram[f][1] += xa.T @ y
    weights = {(f, lam): ridge_fit(*gram[f], lam)
               for f in fams for lam in lambda_grid}

    val_se = {f: {lam: [0.0, 0] for lam in lambda_grid} for f in fams}
    for _stem, _pid, z in rows(in_split["val"]):
        for f in fams:
            x, y = xy(z, f)
            xs = std[f].apply(x)
            for lam in lambda_grid:
                pred = predict_clipped(weights[(f, lam)], xs)
                val_se[f][lam][0] += float(((pred - y) ** 2).sum())
                val_se[f][lam][1] += len(y)
    chosen = {}
    for f in fams:
        mses = {lam: se / n for lam, (se, n) in val_se[f].items()}
        chosen[f] = min(lambda_grid, key=lambda lam: (mses[lam], -lam))

    state_rows = []
    test_se = {f: [0.0, 0] for f in fams}
    base_se = [0.0, 0]
    for stem, pid, z in rows(in_split["test"]):
        row = {"run": stem, "prompt": pid}
        for f in fams:
            x, y = xy(z, f)
            pred = predict_clipped(weights[(f, chosen[f])], std[f].apply(x))
            se = float(((pred - y) ** 2).sum())
            row[f"{f}_off5"] = {"se": se, "n": len(y)}
            test_se[f][0] += se
            test_se[f][1] += len(y)
            if f == "free":
                tse = float(((y_mean - y) ** 2).sum())
                # per-row trivial SE completes the committed recompute
                # surface (critic advisory at the freeze round)
                row["trivial_off5"] = {"se": tse, "n": len(y)}
                base_se[0] += tse
                base_se[1] += len(y)
        state_rows.append(row)

    summary = {
        "registration": meta["registration"],
        "role": "REPORTED-only (never gating): the Stage-C extend signal's a_hat_5 heads",
        "chosen_lambda": {f: chosen[f] for f in fams},
        "test_mse": {f: test_se[f][0] / test_se[f][1] for f in fams},
        "trivial_baseline_test_mse": base_se[0] / base_se[1],
        "n_test_positions": test_se["free"][1],
        "off_policy_disclosure": meta["off_policy_disclosure"],
    }
    with Path(str(out5) + ".state.jsonl").open("w") as sf:
        sf.write(json.dumps({"header": True, **meta}) + "\n")
        for row in state_rows:
            sf.write(json.dumps(row) + "\n")
    out5.write_text(json.dumps(summary, indent=2))
    return {"summary": summary, "weights": weights, "std": std,
            "chosen": chosen, "runs": runs}


def _json_norm(obj):
    return json.loads(json.dumps(obj))


def _nearly(a, b, rel=1e-12):
    """Equal up to a relative floating-point drift of `rel`: the thread-count and numpy-wheel
    effects measured 2026-10-14 sit at the 15th decimal (docs/SHARP_EDGES.md); shapes and
    non-floats must match exactly. Decides which hint the binding gate's refusal carries."""
    if isinstance(a, float) and isinstance(b, float):
        return a == a and b == b and abs(a - b) <= rel * max(abs(a), abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_nearly(x, y, rel) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_nearly(a[k], b[k], rel) for k in a)
    return a == b


def stage_c_freeze(root: Path, overwrite: bool, n_slots: int | None = None,
                   lambda_grid: tuple | None = None) -> None:
    """STAGE-C FREEZE (BLUEPRINT 2026-09-03): binding-gated recompute,
    offset-5 training, weight export, self-check. n_slots/lambda_grid
    are IN-PROCESS TEST PARAMETERS only — the CLI always runs the
    registered configuration."""
    from sideband.outcome_head import N_SLOTS
    ns = n_slots if n_slots is not None else N_SLOTS
    grid = lambda_grid if lambda_grid is not None else LAMBDA_GRID
    committed_path = root / "oq15_stage1.json"
    committed = json.loads(committed_path.read_text())
    npz_path = root / "oq15_head_weights.npz"
    npz_meta_path = root / "oq15_head_weights.meta.json"
    out5 = root / "oq15_offset5.json"
    if npz_path.exists() and not overwrite:
        raise SystemExit(f"{npz_path} exists; pass --overwrite to redo")

    # (i) in-process recompute + BINDING GATE (bit-exact on pinned fields)
    fr_overrides = {}
    if ns != N_SLOTS:
        fr_overrides["n_slots"] = ns
    if grid != LAMBDA_GRID:
        fr_overrides["lambda_grid"] = list(grid)
    res = pipeline(root, out=None, n_slots=ns, lambda_grid=grid,
                   stale_seed=None, overrides=fr_overrides, write=False)
    for field in FREEZE_BIND_FIELDS:
        got = _json_norm(res["summary"][field])
        want = _json_norm(committed[field])
        if got != want:
            # the hint names the measured cause when the mismatch has its signature (2026-10-15, lane 2 of
            # the public-cut batch: the critic and the failure-mode reviewer asked that a real tamper not
            # be read as drift, and that the advice fit what the record carries)
            hint = ("hint: a mismatch at the 15th decimal is the signature of a floating-point drift, not of an "
                    "edited file: on this tool's synthetic test fixture, delta_noise moved that much between BLAS "
                    "thread caps (OPENBLAS_NUM_THREADS 2 and 24 under numpy 2.4.6) and between numpy wheels 2.3.5 "
                    "and 2.4.6 (docs/SHARP_EDGES.md, the 2026-10-14 thread-count entry; docs/REPRODUCE.md section "
                    "4); the committed real summaries record neither the thread cap nor the wheel, so compare with "
                    "the writing run's environment where it is known, and do not overwrite the summary"
                    if _nearly(got, want) else
                    "hint: the mismatch is far larger than the floating-point drift measured on this box (the 15th "
                    "decimal); a changed input or an edited summary, not the thread count or the numpy wheel")
            raise SystemExit(f"BINDING GATE REFUSED: recomputed {field!r} != "
                             f"committed {committed_path}\n got: {got}\nwant: {want}\n" + hint)
    print("[freeze] binding gate PASS: recompute bit-exact on "
          + ", ".join(FREEZE_BIND_FIELDS))

    # (ii) offset-5 heads on the arm-5 byproducts
    off5 = train_offset5(root, out5, grid, overwrite, n_slots=ns)
    print(f"[freeze] offset-5 heads: lambdas {off5['summary']['chosen_lambda']} "
          f"test_mse {off5['summary']['test_mse']} "
          f"(trivial {off5['summary']['trivial_baseline_test_mse']:.6f})")

    # (iii) export npz: {free,tel}_off{1..5}_{mu,sd,w}
    arrays: dict[str, np.ndarray] = {}
    for fam in ("free", "tel"):
        for off in GATE_OFFSETS:
            k = (fam, off, False)
            st = res["std"][k]
            w = res["weights"][k + (res["chosen"][k],)]
            arrays[f"{fam}_off{off}_mu"] = st.mu
            arrays[f"{fam}_off{off}_sd"] = st.sd
            arrays[f"{fam}_off{off}_w"] = w
        arrays[f"{fam}_off5_mu"] = off5["std"][fam].mu
        arrays[f"{fam}_off5_sd"] = off5["std"][fam].sd
        arrays[f"{fam}_off5_w"] = off5["weights"][(fam, off5["chosen"][fam])]
    np.savez(npz_path, **arrays)

    # (iv) EXPORT SELF-CHECK, two assertions (STAGE-C FREEZE): (a) the
    # live scorer BIT-EQUALS a single-row recomputation through
    # predict_clipped (algorithmic identity); (b) it deviates from the
    # training pipeline's BATCH predictions by <= 1e-12 (this box's
    # BLAS accumulates batched vs single-row gemv differently; measured
    # 3.2e-14, the pin carries ~30x margin).
    scorers = {fam: HeadScorer(npz_path, fam) for fam in ("free", "tel")}
    checked = 0
    max_batch_dev = 0.0
    run0 = res["gate"][0]
    for pid, z in iter_prompts(run0):
        cores = {"free": block_core_features(z, "free", n_slots=ns),
                 "tel": block_core_features(z, "tel", n_slots=ns)}
        qs = np.asarray(z["q_sig"], dtype=np.float64)
        n = cores["free"].shape[0]
        for fam in ("free", "tel"):
            for off in (1, 2, 3, 4, 5):
                if off <= 4:
                    k = (fam, off, False)
                    st, w = res["std"][k], res["weights"][k + (res["chosen"][k],)]
                else:
                    st = off5["std"][fam]
                    w = off5["weights"][(fam, off5["chosen"][fam])]
                kq = min(off, 2)
                x = np.hstack([cores[fam], qs[:, :kq]])
                want_batch = predict_clipped(w, st.apply(x))
                got = np.array([scorers[fam].a_hat(cores[fam][b],
                                                   qs[b].tolist(), off)
                                for b in range(n)])
                single = np.array([predict_clipped(w, st.apply(x[b:b + 1]))[0]
                                   for b in range(n)])
                if not np.array_equal(single, got):
                    raise SystemExit(f"EXPORT SELF-CHECK FAILED (a): {fam}_off{off} "
                                     f"prompt {pid} — live scorer != single-row "
                                     "predict_clipped")
                dev = float(np.max(np.abs(want_batch - got))) if n else 0.0
                max_batch_dev = max(max_batch_dev, dev)
                if dev > 1e-12:
                    raise SystemExit(f"EXPORT SELF-CHECK FAILED (b): {fam}_off{off} "
                                     f"prompt {pid} — batch deviation {dev:.3e} "
                                     "> 1e-12")
        checked += n
        if checked >= 1000:
            break
    print(f"[freeze] export self-check PASS: {checked} blocks x 10 heads; "
          f"single-row bit-equal; max batch deviation {max_batch_dev:.3e} <= 1e-12")

    npz_meta = {
        "registration": "OQ-15 STAGE-C FREEZE (BLUEPRINT 2026-09-03)",
        "git_commit": _git_commit(),
        "npz_sha256": hashlib.sha256(npz_path.read_bytes()).hexdigest(),
        "binding": {"oq15_stage1_sha256": hashlib.sha256(
                        committed_path.read_bytes()).hexdigest(),
                    "bound_fields": list(FREEZE_BIND_FIELDS)},
        "offset5_evidence": out5.name,
        "offset5_summary_sha256": hashlib.sha256(out5.read_bytes()).hexdigest(),
        "chosen_lambda": {
            **{f"{fam}_off{off}": res["chosen"][(fam, off, False)]
               for fam in ("free", "tel") for off in GATE_OFFSETS},
            **{f"{fam}_off5": off5["chosen"][fam] for fam in ("free", "tel")}},
        "self_check_blocks": checked,
        "self_check_max_batch_deviation": max_batch_dev,
    }
    npz_meta_path.write_text(json.dumps(npz_meta, indent=2))
    print(f"[freeze] wrote {npz_path} + meta (sha {npz_meta['npz_sha256'][:12]}..)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", default=str(Path("results") / "real"))
    ap.add_argument("--out", default=str(Path("results") / "real" / "oq15_stage1.json"))
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--n-slots", type=int, default=None,
                    help="TEST-SIZING OVERRIDE ONLY; registered runs use "
                         "the default (512) and any override is recorded "
                         "in meta+summary as sizing_overrides")
    ap.add_argument("--lambdas", default=None,
                    help="TEST-SIZING OVERRIDE ONLY (comma-separated); "
                         "registered runs use the pinned grid")
    ap.add_argument("--stale-target-perm-seed", type=int, default=None,
                    help="DI-1 stale-target control (registered 2026-09-03): "
                         "permute each (run,prompt)'s analytic+acc_flags rows "
                         "by default_rng(seed*1000000 + run_index*10000 + pid). "
                         "Diagnostic only; refuses the primary registered out.")
    ap.add_argument("--stage-c-freeze", action="store_true",
                    help="STAGE-C FREEZE: binding-gated recompute + offset-5 "
                         "training + weight export + self-check (no other "
                         "flags allowed except --data-root/--overwrite)")
    args = ap.parse_args()

    from sideband import outcome_head as _oh
    if args.stage_c_freeze:
        if args.n_slots is not None or args.lambdas is not None \
                or args.stale_target_perm_seed is not None:
            raise SystemExit("--stage-c-freeze takes no sizing/diagnostic "
                             "overrides (the binding gate runs the registered "
                             "configuration only)")
        stage_c_freeze(Path(args.data_root), args.overwrite)
        return

    n_slots = args.n_slots if args.n_slots is not None else _oh.N_SLOTS
    lambda_grid = (tuple(float(x) for x in args.lambdas.split(","))
                   if args.lambdas else LAMBDA_GRID)
    overrides = {}
    if n_slots != _oh.N_SLOTS:
        overrides["n_slots"] = n_slots
    if lambda_grid != LAMBDA_GRID:
        overrides["lambda_grid"] = list(lambda_grid)
    stale_seed = args.stale_target_perm_seed
    if stale_seed is not None:
        overrides["stale_target_perm_seed"] = stale_seed

    root = Path(args.data_root)
    out = Path(args.out)
    registered_out = (Path("results") / "real" / "oq15_stage1.json").resolve()
    if overrides and out.resolve() == registered_out:
        raise SystemExit("sizing overrides may not write the registered "
                         "output path (critic advisory: registered-outs guard)")
    if out.exists() and not args.overwrite:
        raise SystemExit(f"{out} exists; pass --overwrite to redo")

    res = pipeline(root, out, n_slots, lambda_grid, stale_seed, overrides,
                   write=True)
    summary = res["summary"]
    print(json.dumps({"stage1_pass": summary["stage1_pass"],
                      "branch": summary["branch"],
                      "delta_noise": summary["delta_noise"],
                      "delta_free": summary["delta_free"]},
                     indent=2))


if __name__ == "__main__":
    main()

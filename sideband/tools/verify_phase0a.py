#!/usr/bin/env python3
"""Phase 0a verification: recompute every F-10 support claim from the
committed evidence files, with pinned recipes, and write the results to
results/real/phase0a_verification.json (cited by F-10's source line).

Checks (exit 1 if any fails):
  A. KV rider (WHY_THIS_DIES): cached-vs-uncached bidirectional point-in-CI
     for acceptance (both mean-of-rates and pooled frames) and residual mass.
  B. NF4-vs-bf16 prompt-paired deltas: acceptance and pooled residual mass,
     percentile bootstrap over prompts (seed 0, n_boot 20000 — the pinned
     recipe; both pooled and per-prompt-mean frames reported).
  C. Trajectory identity across the k=256/512/1024 audits: every rejection
     tuple (prompt, position, offset, proposed, emitted) equal AND per-prompt
     (n_blocks, n_proposed, n_accepted) equal. Identity is expected BY
     CONSTRUCTION (at steer=none, buckets touch only audit labels); this
     confirms it empirically at every logged coordinate. Accepted-token
     identity between rejections is implied by construction, not logged.
  D. Clean-vs-dirty-tree behavioral equivalence: the clean-tree sanity_k512
     segment must match audit_k512 bit-exactly on their 20 shared prompts
     (rejection tuples, float64 masses, per-prompt counts).

Run: python tools/verify_phase0a.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.stats import cluster_bootstrap_ci  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
BOOT_SEED, N_BOOT = 0, 20_000


def load(name: str):
    stats = sorted((json.loads(l) for l in (REAL / f"{name}.stats.jsonl").open()),
                   key=lambda d: d["prompt_idx"])
    recs = [json.loads(l) for l in (REAL / f"{name}.jsonl").open()]
    summ = json.loads((REAL / f"{name}.summary.json").read_text())
    return stats, recs, summ


def acc_frames(stats):
    succ = np.array([s["n_accepted"] for s in stats], float)
    tri = np.array([s["n_proposed"] for s in stats], float)
    return {
        "mean_of_rates": float(np.mean(succ / tri)),
        "pooled": float(succ.sum() / tri.sum()),
        "ci_pooled_cluster": list(cluster_bootstrap_ci(succ, tri, seed=BOOT_SEED)),
    }


def mass_pooled(recs) -> float:
    return float(np.mean([r["cross_bucket_residual_mass"] for r in recs]))


def paired_bootstrap(per_prompt_a, per_prompt_b, pooled_fn):
    """Percentile CI for pooled_fn(A) - pooled_fn(B) resampling PROMPTS with
    replacement, arms paired by prompt (per-prompt RNG streams pair them)."""
    n = len(per_prompt_a)
    gen = np.random.default_rng(BOOT_SEED)
    idx = gen.integers(0, n, size=(N_BOOT, n))
    deltas = np.array([pooled_fn([per_prompt_a[i] for i in row]) - pooled_fn([per_prompt_b[i] for i in row])
                       for row in idx])
    return float(deltas.mean()), [float(x) for x in np.percentile(deltas, [2.5, 97.5])]


def main() -> int:
    out: dict = {"boot_seed": BOOT_SEED, "n_boot": N_BOOT}
    failures: list[str] = []

    # ---- A. KV rider ------------------------------------------------------
    st_c, rec_c, _ = load("sanity_k512")
    st_u, rec_u, _ = load("sanity_k512_nokv")
    acc_c, acc_u = acc_frames(st_c), acc_frames(st_u)
    m_c = mass_pooled(rec_c)
    m_u = mass_pooled(rec_u)

    def mass_ci(recs):
        by = {}
        for r in recs:
            by.setdefault(r["prompt_idx"], []).append(r["cross_bucket_residual_mass"])
        succ = np.array([sum(v) for v in by.values()])
        tri = np.array([float(len(v)) for v in by.values()])
        return list(cluster_bootstrap_ci(succ, tri, seed=BOOT_SEED))

    mci_c, mci_u = mass_ci(rec_c), mass_ci(rec_u)
    kv = {
        "cached": {"acc": acc_c, "mass": m_c, "mass_ci": mci_c},
        "uncached": {"acc": acc_u, "mass": m_u, "mass_ci": mci_u},
        "checks": {
            "acc_pooled_cached_in_uncached_ci": acc_u["ci_pooled_cluster"][0] <= acc_c["pooled"] <= acc_u["ci_pooled_cluster"][1],
            "acc_pooled_uncached_in_cached_ci": acc_c["ci_pooled_cluster"][0] <= acc_u["pooled"] <= acc_c["ci_pooled_cluster"][1],
            "acc_mor_cached_in_uncached_ci": acc_u["ci_pooled_cluster"][0] <= acc_c["mean_of_rates"] <= acc_u["ci_pooled_cluster"][1],
            "acc_mor_uncached_in_cached_ci": acc_c["ci_pooled_cluster"][0] <= acc_u["mean_of_rates"] <= acc_c["ci_pooled_cluster"][1],
            "mass_cached_in_uncached_ci": mci_u[0] <= m_c <= mci_u[1],
            "mass_uncached_in_cached_ci": mci_c[0] <= m_u <= mci_c[1],
        },
    }
    kv["verdict"] = "PASS" if all(kv["checks"].values()) else "FAIL"
    out["kv_rider"] = kv
    if kv["verdict"] != "PASS":
        failures.append("KV rider")

    # ---- B. NF4-vs-bf16 paired deltas ------------------------------------
    st_b, rec_b, _ = load("sanity_k512_bf16")
    pa = [(s["n_accepted"], s["n_proposed"]) for s in st_c]
    pb = [(s["n_accepted"], s["n_proposed"]) for s in st_b]

    def pooled_acc(pairs):
        a = sum(x for x, _ in pairs)
        t = sum(y for _, y in pairs)
        return a / t

    d_acc, d_acc_ci = paired_bootstrap(pa, pb, pooled_acc)

    def per_prompt_masses(recs):
        by: dict[int, list[float]] = {}
        for r in recs:
            by.setdefault(r["prompt_idx"], []).append(r["cross_bucket_residual_mass"])
        return [by.get(i, []) for i in sorted({r["prompt_idx"] for r in recs})]

    ma, mb = per_prompt_masses(rec_c), per_prompt_masses(rec_b)

    def pooled_mass(groups):
        flat = [m for g in groups for m in g]
        return sum(flat) / len(flat)

    d_mass, d_mass_ci = paired_bootstrap(ma, mb, pooled_mass)
    out["nf4_vs_bf16"] = {
        "acc_delta_pooled": d_acc, "acc_delta_ci95": d_acc_ci,
        "acc_delta_mean_of_rates": float(np.mean([a / t for a, t in pa]) - np.mean([a / t for a, t in pb])),
        "mass_delta_pooled": d_mass, "mass_delta_ci95": d_mass_ci,
        "mass_delta_per_prompt_mean_frame": float(np.mean([np.mean(g) for g in ma]) - np.mean([np.mean(g) for g in mb])),
        "note": "paired at prompt granularity via per-prompt RNG streams; "
                "within-prompt trajectories diverge after the first differing acceptance",
    }

    # ---- C. cross-k trajectory identity ----------------------------------
    def rej_keys(recs):
        return [(r["prompt_idx"], r["position"], r["offset"], r["proposed"], r["emitted"]) for r in recs]

    def counts(stats):
        return [(s["prompt_idx"], s["n_blocks"], s["n_proposed"], s["n_accepted"]) for s in stats]

    ks = {}
    for k in (256, 512, 1024):
        st, rc, _ = load(f"audit_k{k}")
        ks[k] = (rej_keys(rc), counts(st))
    ident = {
        "rejection_tuples_equal": ks[256][0] == ks[512][0] == ks[1024][0],
        "per_prompt_counts_equal": ks[256][1] == ks[512][1] == ks[1024][1],
        "n_rejections": len(ks[512][0]),
    }
    out["cross_k_identity"] = ident
    if not (ident["rejection_tuples_equal"] and ident["per_prompt_counts_equal"]):
        failures.append("cross-k identity")

    # ---- D. clean-vs-dirty-tree overlap ----------------------------------
    st_a, rec_a, _ = load("audit_k512")
    n_overlap = len(st_c)
    a20 = [r for r in rec_a if r["prompt_idx"] < n_overlap]
    c20 = list(rec_c)
    same_tuples = rej_keys(a20) == rej_keys(c20)
    same_masses = ([r["cross_bucket_residual_mass"] for r in a20]
                   == [r["cross_bucket_residual_mass"] for r in c20])
    same_counts = counts([s for s in st_a if s["prompt_idx"] < n_overlap]) == counts(st_c)
    out["clean_vs_dirty_overlap"] = {
        "n_prompts": n_overlap, "rejection_tuples_equal": same_tuples,
        "masses_bitwise_equal": same_masses, "per_prompt_counts_equal": same_counts,
    }
    if not (same_tuples and same_masses and same_counts):
        failures.append("clean/dirty overlap")

    out["verdict"] = "PASS" if not failures else f"FAIL: {failures}"
    (REAL / "phase0a_verification.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps({k: v for k, v in out.items() if k != "kv_rider"}, indent=2))
    print("kv_rider verdict:", kv["verdict"], kv["checks"])
    print("VERDICT:", out["verdict"])
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Phase 0b analysis: paired per-prompt comparison of every steered arm
against the vanilla arm, with the pinned bootstrap recipe (seed 0,
n_boot 20000 for the paired deltas; cluster CIs use sideband.stats defaults,
n_boot 2000 — the same split verify_phase0a and the committed summaries use).

Pairing is valid because all arms share per-prompt RNG streams at the same
seed (D-6); the tool REFUSES arms whose metas disagree on anything but the
steering knobs (steer, beta, bucket_source, steer_gate) — in particular the
cache path (no_kv_cache) may never differ between compared arms (K-1 rider).

Per arm, deltas vs vanilla (all pooled ratio-of-sums; PLUG-IN point estimate
= pooled(arm) - pooled(vanilla), with the bootstrap-mean reported alongside):
  - acceptance (empirical; mean-of-rates frame reported alongside);
  - analytic drafted acceptance (D-9 variance-reduced estimand);
  - tokens per target call = 1 + n_accepted / n_blocks.
Diagnostics: gate-open rate, n_steerable, per-offset analytic table.

Riders (pre-registered, BLUEPRINT Phase 0b protocol):
  - vanilla-rerun point-in-CI vs audit_k512 (F-10 verification-by-rerun);
  - KV spot rider: phase0b_sharp_b3 restricted to the FIRST 20 prompts vs
    phase0b_sharp_b3_nokv (>= 20 prompts, --no-kv-cache), the six
    bidirectional point-in-CI checks of verify_phase0a check A (both
    acceptance frames + residual mass). A MISSING nokv run fails the tool:
    steered results may not be cited without it.

Run: python tools/analyze_phase0b.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sideband.stats import cluster_bootstrap_ci  # noqa: E402

REAL = Path(__file__).resolve().parent.parent / "results" / "real"
BOOT_SEED, N_BOOT = 0, 20_000

# Meta keys every compared arm must agree on (everything identity-relevant
# except the steering knobs).
MUST_MATCH = (
    "target", "draft", "buckets_sha256", "glue_sha256", "prompts_sha256",
    "templated_prompt0_ids_sha256", "seed", "gamma", "max_new", "temperature",
    "load_4bit", "no_kv_cache", "no_chat_template", "n_prompts",
)


def load_stats(stem: str) -> tuple[list[dict], dict]:
    stats = sorted((json.loads(l) for l in (REAL / f"{stem}.stats.jsonl").open()),
                   key=lambda d: d["prompt_idx"])
    meta = json.loads((REAL / f"{stem}.meta.json").read_text())
    if not (REAL / f"{stem}.summary.json").exists():
        raise SystemExit(f"{stem}.summary.json missing — run incomplete, refusing to analyze")
    return stats, meta


def paired_ratio_delta(num_a, den_a, num_v, den_v) -> dict:
    """Plug-in pooled-ratio delta + percentile bootstrap over prompts
    (vectorized; identical resamples to verify_phase0a's recipe)."""
    num_a, den_a = np.asarray(num_a, float), np.asarray(den_a, float)
    num_v, den_v = np.asarray(num_v, float), np.asarray(den_v, float)
    n = len(num_a)
    plugin = float(num_a.sum() / den_a.sum() - num_v.sum() / den_v.sum())
    gen = np.random.default_rng(BOOT_SEED)
    idx = gen.integers(0, n, size=(N_BOOT, n))
    deltas = (num_a[idx].sum(1) / den_a[idx].sum(1)
              - num_v[idx].sum(1) / den_v[idx].sum(1))
    return {"plugin": plugin, "boot_mean": float(deltas.mean()),
            "ci95": [float(x) for x in np.percentile(deltas, [2.5, 97.5])]}


def arm_summary(stats) -> dict:
    succ = np.array([s["n_accepted"] for s in stats], float)
    tri = np.array([s["n_proposed"] for s in stats], float)
    n_steer = sum(s.get("n_steerable", 0) for s in stats)
    n_open = sum(s.get("n_gate_open", 0) for s in stats)
    by_off: dict[str, list[float]] = {}
    for s in stats:
        for j, (sm, n) in s.get("analytic_acc_drafted_by_offset", {}).items():
            cell = by_off.setdefault(j, [0.0, 0.0])
            cell[0] += sm
            cell[1] += n
    an_sum = sum(s.get("analytic_acc_drafted_sum", 0.0) for s in stats)
    an_n = sum(s.get("analytic_acc_drafted_n", 0) for s in stats)
    nb = sum(s["n_blocks"] for s in stats)
    return {
        "n_prompts": len(stats),
        "acceptance_pooled": float(succ.sum() / tri.sum()),
        "acceptance_mean_of_rates": float(np.mean(succ / tri)),
        "acceptance_ci95_cluster": list(cluster_bootstrap_ci(succ, tri, seed=BOOT_SEED)),
        "analytic_acceptance_drafted_pooled": (an_sum / an_n) if an_n else None,
        "analytic_drafted_by_offset": {
            j: (v[0] / v[1] if v[1] else None) for j, v in sorted(by_off.items())
        },
        "tokens_per_target_call_pooled": 1.0 + float(succ.sum()) / nb,
        "n_steerable": n_steer,
        "n_gate_open": n_open,
        "gate_open_rate": (n_open / n_steer) if n_steer else None,
    }


def acc_frames(stats) -> dict:
    succ = np.array([s["n_accepted"] for s in stats], float)
    tri = np.array([s["n_proposed"] for s in stats], float)
    return {"mean_of_rates": float(np.mean(succ / tri)),
            "pooled": float(succ.sum() / tri.sum()),
            "ci_pooled_cluster": list(cluster_bootstrap_ci(succ, tri, seed=BOOT_SEED))}


def kv_spot_rider(cached_stem: str, nokv_stem: str) -> tuple[dict, bool]:
    """verify_phase0a check A, applied to the steered arm's first-N-prompt
    slice vs its --no-kv-cache re-run: six bidirectional point-in-CI checks."""
    if not (REAL / f"{nokv_stem}.stats.jsonl").exists():
        return {"status": f"MISSING {nokv_stem} — steered results may not be cited"}, False
    st_u, meta_u = load_stats(nokv_stem)
    st_all, meta_c = load_stats(cached_stem)
    n = len(st_u)
    st_c = [s for s in st_all if s["prompt_idx"] < n]
    knobs = ("steer", "bucket_source", "steer_gate", "steer_mech", "beta")
    knob_mismatch = [k for k in knobs if meta_u.get(k) != meta_c.get(k)]
    id_mismatch = [k for k in MUST_MATCH if k not in ("no_kv_cache", "n_prompts")
                   and meta_u.get(k) != meta_c.get(k)]
    if knob_mismatch or id_mismatch or not meta_u.get("no_kv_cache"):
        return {"status": f"INVALID PAIR: knobs {knob_mismatch}, identity {id_mismatch}, "
                          f"nokv={meta_u.get('no_kv_cache')}"}, False

    def masses(stem, n_keep):
        by: dict[int, list[float]] = {}
        for line in (REAL / f"{stem}.jsonl").open():
            r = json.loads(line)
            if r["prompt_idx"] < n_keep:
                by.setdefault(r["prompt_idx"], []).append(r["cross_bucket_residual_mass"])
        flat = [m for v in by.values() for m in v]
        succ = np.array([sum(v) for v in by.values()])
        tri = np.array([float(len(v)) for v in by.values()])
        return float(np.mean(flat)), list(cluster_bootstrap_ci(succ, tri, seed=BOOT_SEED))

    ac, au = acc_frames(st_c), acc_frames(st_u)
    mc, mci_c = masses(cached_stem, n)
    mu, mci_u = masses(nokv_stem, n)
    checks = {
        "acc_pooled_cached_in_uncached_ci": au["ci_pooled_cluster"][0] <= ac["pooled"] <= au["ci_pooled_cluster"][1],
        "acc_pooled_uncached_in_cached_ci": ac["ci_pooled_cluster"][0] <= au["pooled"] <= ac["ci_pooled_cluster"][1],
        "acc_mor_cached_in_uncached_ci": au["ci_pooled_cluster"][0] <= ac["mean_of_rates"] <= au["ci_pooled_cluster"][1],
        "acc_mor_uncached_in_cached_ci": ac["ci_pooled_cluster"][0] <= au["mean_of_rates"] <= ac["ci_pooled_cluster"][1],
        "mass_cached_in_uncached_ci": mci_u[0] <= mc <= mci_u[1],
        "mass_uncached_in_cached_ci": mci_c[0] <= mu <= mci_c[1],
    }
    ok = all(checks.values())
    return {"status": "PASS" if ok else "FAIL — quarantine all steered results",
            "n_prompts": n,
            "cached": {"acc": ac, "mass": mc, "mass_ci": mci_c},
            "uncached": {"acc": au, "mass": mu, "mass_ci": mci_u},
            "checks": checks}, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", default="phase0b_vanilla_k512")
    ap.add_argument("--arms", nargs="*", default=[
        f"phase0b_{v}_b{b}" for v in ("soft", "sharp") for b in (1, 2, 3, 4)]
        + ["phase0b_sharp_b3_always", "phase0b_sharp_b3_cover90"])
    ap.add_argument("--kv-cached-stem", default="phase0b_sharp_b3")
    ap.add_argument("--kv-nokv-stem", default="phase0b_sharp_b3_nokv")
    ap.add_argument("--gate-space-arms", nargs="*", default=["phase0b_sharp_b3_cover90"],
                    help="arms allowed to differ from vanilla on glue_sha256 AND "
                         "buckets_sha256 ONLY — the gating space IS the treatment (K-7 gate "
                         "re-test / OQ-12 coarse arms). Sound because a steer=none trajectory "
                         "is bucketization- and glue-independent by construction (buckets "
                         "only decorate records), verified empirically on both axes: "
                         "buckets by the k=256/512/1024 audit identity (verify_phase0a "
                         "check C), glue by F-11's bit-identical vanilla re-run. The "
                         "exemption is recorded on the arm's output row.")
    ap.add_argument("--skip-kv-rider", action="store_true",
                    help="analyze without the KV spot rider (results stay quarantined)")
    ap.add_argument("--out", default="results/real/phase0b_analysis.json")
    args = ap.parse_args()

    stats_v, meta_v = load_stats(args.vanilla)
    out: dict = {"boot_seed": BOOT_SEED, "n_boot_paired": N_BOOT, "n_boot_cluster": 2000,
                 "vanilla": {"stem": args.vanilla, **arm_summary(stats_v)}}
    failures: list[str] = []

    # Rider 1: the vanilla re-run verifies F-10's acceptance by point-in-CI.
    audit_stats = sorted((json.loads(l) for l in (REAL / "audit_k512.stats.jsonl").open()),
                         key=lambda d: d["prompt_idx"])
    succ0 = np.array([s["n_accepted"] for s in audit_stats], float)
    tri0 = np.array([s["n_proposed"] for s in audit_stats], float)
    ci0 = list(cluster_bootstrap_ci(succ0, tri0, seed=BOOT_SEED))
    van_point = out["vanilla"]["acceptance_pooled"]
    out["vanilla_rerun_rider"] = {
        "audit_k512_acceptance_pooled": float(succ0.sum() / tri0.sum()),
        "audit_k512_ci95_cluster": ci0,
        "vanilla_rerun_point": van_point,
        "point_in_ci": bool(ci0[0] <= van_point <= ci0[1]),
    }
    if not out["vanilla_rerun_rider"]["point_in_ci"]:
        failures.append("vanilla re-run acceptance outside audit_k512 CI")

    # Rider 2: KV spot rider on the confirmatory arm.
    if args.skip_kv_rider:
        out["kv_spot_rider"] = {"status": "SKIPPED — steered results quarantined"}
        failures.append("KV spot rider skipped")
    else:
        out["kv_spot_rider"], ok = kv_spot_rider(args.kv_cached_stem, args.kv_nokv_stem)
        if not ok:
            failures.append(f"KV spot rider: {out['kv_spot_rider']['status']}")

    prompts_v = [s["prompt_idx"] for s in stats_v]
    acc_v = ([s["n_accepted"] for s in stats_v], [s["n_proposed"] for s in stats_v])
    an_v = ([s["analytic_acc_drafted_sum"] for s in stats_v],
            [s["analytic_acc_drafted_n"] for s in stats_v])
    tp_v = ([s["n_accepted"] for s in stats_v], [s["n_blocks"] for s in stats_v])
    out["arms"] = {}
    for stem in args.arms:
        if not (REAL / f"{stem}.stats.jsonl").exists():
            out["arms"][stem] = {"status": "MISSING"}
            failures.append(f"{stem} missing")
            continue
        stats_a, meta_a = load_stats(stem)
        exempt = stem in args.gate_space_arms
        must = [k for k in MUST_MATCH
                if not (exempt and k in ("glue_sha256", "buckets_sha256"))]
        mism = [k for k in must if meta_a.get(k) != meta_v.get(k)]
        if mism:
            failures.append(f"{stem} meta mismatch on {mism}")
            out["arms"][stem] = {"status": f"META MISMATCH: {mism}"}
            continue
        if [s["prompt_idx"] for s in stats_a] != prompts_v:
            failures.append(f"{stem} prompt set differs from vanilla")
            out["arms"][stem] = {"status": "PROMPT SET MISMATCH"}
            continue
        rates_a = np.array([s["n_accepted"] / s["n_proposed"] for s in stats_a])
        rates_v = np.array([s["n_accepted"] / s["n_proposed"] for s in stats_v])
        out["arms"][stem] = {
            "status": "OK",
            "gate_space_exemption": exempt or None,
            "glue_sha256": meta_a.get("glue_sha256") if exempt else None,
            "buckets_sha256": meta_a.get("buckets_sha256") if exempt else None,
            "buckets_k": meta_a.get("buckets_k") if exempt else None,
            "steer": {k: meta_a.get(k) for k in ("steer", "bucket_source", "steer_gate",
                                                 "steer_mech", "beta")},
            **arm_summary(stats_a),
            "delta_vs_vanilla": {
                "acceptance_pooled": paired_ratio_delta(
                    [s["n_accepted"] for s in stats_a], [s["n_proposed"] for s in stats_a],
                    *acc_v),
                "acceptance_mean_of_rates": float(np.mean(rates_a - rates_v)),
                "analytic_drafted_pooled": paired_ratio_delta(
                    [s["analytic_acc_drafted_sum"] for s in stats_a],
                    [s["analytic_acc_drafted_n"] for s in stats_a], *an_v),
                "tokens_per_target_call_pooled": paired_ratio_delta(
                    [s["n_accepted"] for s in stats_a], [s["n_blocks"] for s in stats_a],
                    *tp_v),
            },
        }

    out["verdict"] = "OK" if not failures else f"ISSUES: {failures}"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True))
    compact = {}
    for stem, a in out["arms"].items():
        d = a.get("delta_vs_vanilla", {}).get("acceptance_pooled", {})
        compact[stem] = {"acc": a.get("acceptance_pooled"), "d_acc": d.get("plugin"),
                         "d_ci": d.get("ci95"), "gate": a.get("gate_open_rate"),
                         "status": a.get("status")}
    print(json.dumps({"vanilla_acc": out["vanilla"]["acceptance_pooled"],
                      "vanilla_rider": out["vanilla_rerun_rider"]["point_in_ci"],
                      "kv_rider": out["kv_spot_rider"].get("status"),
                      "arms": compact, "verdict": out["verdict"]}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

"""OQ-20 SEED-REPLAY READOUTS: the cross-seed spread of the record's two
conversion-verdict VS-VANILLA legs — F-19's arm 4 vs arm 1 on the K-3
population at seed 1 and F-21's arm 7 vs arm 1 on the OQ-15 population at
seed 3 — replayed with the SAME frozen policies at ONE new sampling seed (6),
read from committed summaries only: CPU, numpy, seconds. NON-CRITERION for
F-19, F-21 and F-27 (docs/BLUEPRINT.md, "SEED-REPLAY OF THE CONVERSION-VERDICT
LEGS REGISTRATION", 2026-10-09, pre-run). Every recipe is the record's: the
E6 leg (sideband.stats.paired_ratio_delta_ci, joint prompt-cluster bootstrap,
n_boot 2000, seed 0; the +0.062 bar; the pairwise budget guard, epsilon 0.01)
with its constants taken from the frozen tools/run_noise_floor.py (F-27),
which also lends its loader and reliability readout; tests/test_seed_replay.py
pins the leg equal to tools/e6_gate.pair on the committed legs. The one new
estimator — the difference of two legs under one joint draw — is
sideband.stats.paired_ratio_delta_of_deltas_ci. Nothing under tools/ is
imported except the frozen F-27 instrument.

Readouts per population (K3 the label population, OQ15 the replication;
co-primary — the roles fix the stage word's argument order only):
  R1  the leg at the new seed: tokens/call of the telemetry arm minus the
      vanilla arm (pooled ratios), CI95 by the E6 recipe, the budget guard
      as a label (GUARD-HELD / GUARD-BREACHED; never a retune, never a WIN).
  R2  the cross-seed difference Delta = delta_verdict - delta_new with its
      joint-draw CI95; the label MUTUAL-COVERAGE if each seed's delta lies
      inside the other seed's CI95, else DELTA-MOVES; beside the label, the
      pinned READING from the label and whether Delta's CI95 contains zero:
      MUTUAL-COVERAGE + contains zero  -> REPRODUCES
      MUTUAL-COVERAGE + excludes zero  -> PROMPT-STABLE-SHIFT (smaller than either leg's CI)
      DELTA-MOVES + contains zero      -> WITHIN-CROSS-SEED-NOISE
      DELTA-MOVES + excludes zero      -> MOVED-BEYOND-JOINT-CI
  R3  the bar at the new seed on this single leg: BAR-CLEARED (CI95 lower
      above zero AND point at or above +0.062; the pre-registered surprise)
      or BAR-NOT-CLEARED. A single comparator never decides a WIN; the
      reading is unguarded and has no free column (D-5).
  R4  the F-27 extension: the vanilla run at the new seed makes a new seed
      pair with each committed vanilla seed; per pair the per-prompt r with
      its prompt-bootstrap CI95 (run_noise_floor.reliability) and the
      cross-seed null delta (lower seed minus higher) with its CI95 half-width
      at n = 210 (the pairs share runs: not independent replications);
      R-CONSISTENT if the committed pair's r (read from the F-27 payload)
      lies inside both new pairs' CI95, else R-SHIFTS.
  R5  THE FREE LEG at the new seed (operator's addition, 2026-10-09): the
      telemetry arm minus the mechanism-matched FREE arm (K-3 arm 4 vs arm 3,
      the (a)-probe free scheduler; OQ-15 arm 7 vs arm 6, head_free — F-21's
      decisive leg), the E6 recipe, the guard (tel at most free + 0.01) as a
      label GUARD-FREE-HELD / GUARD-FREE-BREACHED.
  R6  the free leg's cross-seed difference with its joint-draw CI95, the
      label MUTUAL-COVERAGE / DELTA-MOVES and the same four readings as R2.
  R7  the bar on the free leg at the new seed: BAR-CLEARED-FREE (CI95 lower
      above zero AND point at or above +0.062; a surprise, never a WIN) or
      BAR-NOT-CLEARED-FREE.
  R8  descriptive: the free arm minus vanilla at the new seed (K-3 arm 3 vs
      arm 1; OQ-15 arm 6 vs arm 1) beside the verdict seed's same leg, with
      the MUTUAL-COVERAGE / DELTA-MOVES label and reading — unless the two
      arms differ on fewer than R8_MIN_DIFFERING prompts at either seed or
      either leg's CI95 has zero width, when R8 reads NEAR-IDENTICAL-ARMS
      with the counts and carries no label and no reading (K-3's arm 3
      fired on one prompt of 210 at seed 1); its legs carry no bar or guard
      field; no bar, no surprise.
The stage words over both populations, issued at landing from the two
payloads (--stage-word): over R2, SPREAD-COVERED (both MUTUAL-COVERAGE) /
SPREAD-SPLIT (one) / SPREAD-MOVES (neither); over R6 the same with the
prefix FREE- (FREE-SPREAD-COVERED / -SPLIT / -MOVES).

  python tools/run_seed_replay.py --population k3 --launch-commit <sha> --out results/real/seed_replay_k3.json
  python tools/run_seed_replay.py --population oq15 --launch-commit <sha> --out results/real/seed_replay_oq15.json
  python tools/run_seed_replay.py --conclude-from results/real/seed_replay_k3.json
  python tools/run_seed_replay.py --stage-word results/real/seed_replay_k3.json results/real/seed_replay_oq15.json
  python tools/run_seed_replay.py --population k3 --precondition-only [--launch-commit <sha>]
  python tools/run_seed_replay.py --replay-check [--launch-commit <sha>]

--replay-check is the pinned launch gate: the six replay sidecars written at
the OLD verdict seeds from the clone of the launch commit
(results/real/oq20_replay_{k3,oq15c}_s{1,3}_arm{1,3,4,6,7}.jsonl, committed
with the FREEZE line) are compared with the committed verdict files — every
replayed prompt's generated_ids token for token against the .gen.jsonl row,
and its .stats.jsonl row in every field except run_id, seconds and
peak_vram_gb — so the gate is recomputable from the repo; exit 2 on any
difference. A run's resume is read from its meta's `resumed` flag and its
run_ids (the instrument keeps the original meta's `resume` argument False).

A registered run refuses to write under results/ unless the tracked tree is
clean, --launch-commit is given and every new-seed meta carries exactly that
commit (no -dirty suffix). Smoke (refused under results/): --n-boot and
--draws overrides, and a --data-root other than results/real. The state
file beside the payload carries a sha header over every input (summaries,
metas, the prompt file, the policy and bucket files, the F-27 payload) and one
row per readout; --conclude-from recomputes every number from the summaries
on disk (floats within 1e-12, labels exactly) and refuses any difference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import run_noise_floor as nf  # noqa: E402  (frozen; imported, never edited)
from sideband.stats import paired_ratio_delta_ci, paired_ratio_delta_of_deltas_ci  # noqa: E402

REAL = ROOT / "results" / "real"
REGISTERED = ("SEED-REPLAY OF THE CONVERSION-VERDICT LEGS REGISTRATION (docs/BLUEPRINT.md, 2026-10-09; pre-run; "
              "NON-CRITERION for F-19, F-21 and F-27; a methods datum)")
NEW_SEED = 6                     # the registered new seed; each population's `new_seed` field below carries it, so a
#                                  seed-7 fallback for ONE population (VOID SEMANTICS) is a dated amendment to that field
R8_MIN_DIFFERING = 10            # R8 needs the free and vanilla arms to differ on at least this many prompts at each seed
FULL_N = nf.FULL_N
GAMMA = nf.GAMMA
BAR, EPSILON, N_BOOT, BOOT_SEED = nf.BAR, nf.EPSILON, nf.N_BOOT, nf.BOOT_SEED
RELIABILITY_DRAWS, RELIABILITY_SEED = nf.RELIABILITY_DRAWS, nf.RELIABILITY_SEED
FAMILIES, FAMILY_COUNT = nf.FAMILIES, nf.FAMILY_COUNT
FLOAT_TOL = 1e-12
# the configuration keys every new-seed meta must share with its verdict-seed meta of the same arm (the model
# pair and its load, the schedule, the prompts and their binding, the policy files, the reader, the environment)
SAME_CONFIG_KEYS = ("arm", "arm_kind", "target", "draft", "target_load", "load_4bit", "gamma_base", "gamma_base_effective",
                    "gamma_max", "max_new", "temperature", "chat_template_used", "no_chat_template", "no_instruments",
                    "instruments", "select_split", "n_prompts", "prompts", "prompts_sha256", "templated_prompt0_ids_sha256",
                    "date_string_pinned", "rng_scheme", "probe_weights_sha256", "probe_weights_meta_sha256",
                    "thresholds_sha256", "head_weights_sha256", "probe_arm", "head_family", "torch_version",
                    "transformers_version", "numpy_version", "gpu")
READOUT_NAMES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")
R2_READING = {(True, True): "REPRODUCES", (True, False): "PROMPT-STABLE-SHIFT",
              (False, True): "WITHIN-CROSS-SEED-NOISE", (False, False): "MOVED-BEYOND-JOINT-CI"}
# the pinned replay check: (replay stem, committed verdict stem, replayed prompts, verdict seed)
REPLAY_SPECS = (("oq20_replay_k3_s1_arm1", "k3_verdict_s1_arm1", 6, 1), ("oq20_replay_k3_s1_arm4", "k3_verdict_s1_arm4", 6, 1),
                ("oq20_replay_k3_s1_arm3", "k3_verdict_s1_arm3", 6, 1),
                ("oq20_replay_oq15c_s3_arm1", "oq15c_verdict_s3_arm1", 1, 3),
                ("oq20_replay_oq15c_s3_arm7", "oq15c_verdict_s3_arm7", 1, 3),
                ("oq20_replay_oq15c_s3_arm6", "oq15c_verdict_s3_arm6", 1, 3))
STATS_IGNORE = ("run_id", "seconds", "peak_vram_gb")
GEN_IGNORE = ("run_id",)
META_BOUND = ("arm", "seed", "prompts_sha256", "thresholds_sha256", "probe_weights_sha256", "head_weights_sha256")

POPULATIONS = {
    "k3": {"key": "k3", "role": "label", "finding": "F-19", "prompts": "data/prompts_k3_verdict.jsonl",
           "verdict_seed": 1, "new_seed": NEW_SEED, "tel_arm": 4, "tel_name": "probe (c) telemetry scheduling (arm 4)",
           "free_arm": 3, "free_name": "probe (a) free scheduling (arm 3)",
           "verdict": {"vanilla": "k3_verdict_s1_arm1", "tel": "k3_verdict_s1_arm4", "free": "k3_verdict_s1_arm3"},
           "new": {"vanilla": "k3_seed6_arm1", "tel": "k3_seed6_arm4", "free": "k3_seed6_arm3"},
           "vanilla_seeds": {0: "k3_verdict_arm1", 1: "k3_verdict_s1_arm1"},
           "noise_floor": "noise_floor_k3",
           "policy_files": {"thresholds": "k3_thresholds_arm4_v2.json", "free_thresholds": "k3_thresholds_arm3.json",
                            "probe_weights": "k3_probe_weights.npz"},
           "bound_files": ("buckets_k16.json", "glue_k16.json")},
    "oq15": {"key": "oq15", "role": "replication", "finding": "F-21", "prompts": "data/prompts_oq15_verdict.jsonl",
             "verdict_seed": 3, "new_seed": NEW_SEED, "tel_arm": 7, "tel_name": "C4 head_tel (arm 7)",
             "free_arm": 6, "free_name": "C3 head_free (arm 6)",
             "verdict": {"vanilla": "oq15c_verdict_s3_arm1", "tel": "oq15c_verdict_s3_arm7", "free": "oq15c_verdict_s3_arm6"},
             "new": {"vanilla": "oq15c_seed6_arm1", "tel": "oq15c_seed6_arm7", "free": "oq15c_seed6_arm6"},
             "vanilla_seeds": {2: "oq15c_verdict_arm1", 3: "oq15c_verdict_s3_arm1"},
             "noise_floor": "noise_floor_oq15",
             "policy_files": {"thresholds": "oq15c_thresholds_arm7_v2.json", "free_thresholds": "oq15c_thresholds_arm6.json",
                              "head_weights": "oq15_head_weights.npz", "probe_weights": "k3_probe_weights.npz"},
             "bound_files": ("buckets_k16.json", "glue_k16.json")},
}


def registered_constants() -> dict:
    return {"new_seed": NEW_SEED, "new_seeds": {k: v["new_seed"] for k, v in POPULATIONS.items()}, "full_n": FULL_N,
            "gamma": GAMMA, "bar": BAR, "epsilon": EPSILON, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
            "reliability_draws": RELIABILITY_DRAWS, "reliability_seed": RELIABILITY_SEED, "families": list(FAMILIES),
            "family_count": FAMILY_COUNT, "same_config_keys": list(SAME_CONFIG_KEYS), "float_tol": FLOAT_TOL,
            "r8_min_differing": R8_MIN_DIFFERING}


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git() -> tuple[str, list[str]]:
    """HEAD and the tracked-file status; a failed git is a refusal, never a clean-looking 'unknown' (run_reader_lens's rule)."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10,
                              check=True).stdout.strip()
        st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                            text=True, timeout=10, check=True).stdout
        return head or "unknown", [ln for ln in st.splitlines() if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        return "unknown", ["git unavailable"]


def _under_results(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to((ROOT / "results").resolve())
        return True
    except ValueError:
        return False


def _py(x):
    if isinstance(x, dict):
        return {str(k): _py(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_py(v) for v in x]
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


# ---------------------------------------------------------------------------
# Loading and the precondition
# ---------------------------------------------------------------------------

def load_meta(stem: str, root: Path) -> dict:
    p = Path(root) / f"{stem}.meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def resumed(meta: dict) -> bool:
    """tools/run_k3_arms.py keeps the original meta's `resume` argument (False) on --resume and sets `resumed`
    while appending a second run_id; either marks a resumed run."""
    return bool(meta.get("resumed")) or len(meta.get("run_ids") or []) > 1


def load_pop(key: str, root: Path = REAL, prompts_root: Path = ROOT) -> dict:
    spec = POPULATIONS[key]
    root = Path(root)
    stems = {"verdict_vanilla": spec["verdict"]["vanilla"], "verdict_tel": spec["verdict"]["tel"],
             "verdict_free": spec["verdict"]["free"], "new_vanilla": spec["new"]["vanilla"], "new_tel": spec["new"]["tel"],
             "new_free": spec["new"]["free"]}
    for seed, stem in spec["vanilla_seeds"].items():
        stems[f"vanilla_seed{seed}"] = stem
    runs, metas, missing = {}, {}, []
    for tag, stem in stems.items():
        if not (root / f"{stem}.summary.json").exists():
            missing.append(stem)
            continue
        runs[tag] = nf.load_run(stem, root)
        metas[tag] = load_meta(stem, root)
    families, prompts_sha = nf.load_families(Path(prompts_root) / spec["prompts"])
    policy = {name: {"path": f"results/real/{fn}", "sha256": _sha(root / fn) if (root / fn).exists() else None}
              for name, fn in spec["policy_files"].items()}
    bound = {fn: {"path": f"results/real/{fn}", "sha256": _sha(root / fn) if (root / fn).exists() else None}
             for fn in spec["bound_files"]}
    nf_path = root / f"{spec['noise_floor']}.json"
    noise = json.loads(nf_path.read_text(encoding="utf-8")) if nf_path.exists() else None
    return {"key": key, "role": spec["role"], "finding": spec["finding"], "spec": spec, "stems": stems, "runs": runs,
            "metas": metas, "missing": missing, "families": families, "prompts_path": spec["prompts"],
            "prompts_sha256": prompts_sha, "policy": policy, "bound_files": bound,
            "noise_floor": noise, "noise_floor_path": f"results/real/{spec['noise_floor']}.json",
            "noise_floor_sha256": _sha(nf_path) if nf_path.exists() else None}


def precondition(pop: dict, launch_commit: str | None) -> dict:
    """REPRODUCE AND BIND: every run's pooled fields bit-exact and per-prompt
    ratio exact, the prompt set complete and identical across runs, the
    vanilla arms' n_drafted == GAMMA n_blocks, the metas' seeds as registered
    (verdict seed on the verdict pair, NEW_SEED on the new pair), the new-seed
    metas carrying exactly the launch commit (no -dirty), the same
    configuration keys as their verdict-seed metas (SAME_CONFIG_KEYS), the
    policy files on disk at the shas every telemetry meta attests, the bound
    bucket / glue files present, the family counts, and the committed F-27
    payload present with its reliability and with ITS inputs the vanilla
    runs loaded here (summary and meta shas, the prompt file). Any failure
    refuses."""
    spec, runs, metas = pop["spec"], pop["runs"], pop["metas"]
    checks: dict = {"all_runs_present": not pop["missing"]}
    if pop["missing"]:
        return {"checks": checks, "holds": False, "missing": pop["missing"], "n_checks": len(checks)}
    for tag, r in runs.items():
        checks[f"pooled_tokens_per_call_bit_exact_{tag}"] = bool(
            float(r["emitted"].sum() / r["blocks"].sum()) == r["summary_tokens_per_call"])
        checks[f"pooled_drafted_per_emitted_bit_exact_{tag}"] = bool(
            float(r["drafted"].sum() / r["emitted"].sum()) == r["summary_drafted_per_emitted"])
        checks[f"per_prompt_ratio_exact_{tag}"] = bool(np.max(np.abs(r["tpc_field"] - r["emitted"] / r["blocks"])) <= 1e-12)
        checks[f"blocks_positive_{tag}"] = bool(np.all(r["blocks"] > 0))
        checks[f"prompt_set_complete_{tag}"] = bool(r["prompt_idx"].shape[0] == FULL_N
                                                   and np.array_equal(r["prompt_idx"], np.arange(FULL_N)))
        checks[f"orig_prompt_idx_is_prompt_idx_{tag}"] = bool(np.array_equal(r["orig_prompt_idx"], r["prompt_idx"]))
        checks[f"meta_prompts_sha_is_file_{tag}"] = bool(metas[tag].get("prompts_sha256") == pop["prompts_sha256"])
        if "vanilla" in tag:
            checks[f"drafted_is_gamma_blocks_{tag}"] = bool(np.array_equal(r["drafted"], GAMMA * r["blocks"]))
            checks[f"meta_arm_is_1_{tag}"] = bool(metas[tag].get("arm") == 1)
        elif "free" in tag:
            checks[f"meta_arm_is_free_{tag}"] = bool(metas[tag].get("arm") == spec["free_arm"])
        else:
            checks[f"meta_arm_is_tel_{tag}"] = bool(metas[tag].get("arm") == spec["tel_arm"])
    for tag in ("verdict_vanilla", "verdict_tel", "verdict_free"):
        checks[f"meta_seed_is_verdict_{tag}"] = bool(metas[tag].get("seed") == spec["verdict_seed"])
    for seed in spec["vanilla_seeds"]:
        checks[f"meta_seed_is_{seed}_vanilla_seed{seed}"] = bool(metas[f"vanilla_seed{seed}"].get("seed") == seed)
    for tag, base_tag in (("new_vanilla", "verdict_vanilla"), ("new_tel", "verdict_tel"), ("new_free", "verdict_free")):
        checks[f"meta_seed_is_new_{tag}"] = bool(metas[tag].get("seed") == spec["new_seed"])
        gc = metas[tag].get("git_commit")
        checks[f"meta_launch_commit_clean_{tag}"] = bool(launch_commit is not None and gc == launch_commit
                                                         and "-dirty" not in str(gc))
        base = metas[base_tag]
        same = {k: metas[tag].get(k) == base.get(k) for k in SAME_CONFIG_KEYS}
        checks[f"same_configuration_as_verdict_{tag}"] = all(same.values())
        checks[f"same_configuration_detail_{tag}"] = [k for k, v in same.items() if not v]
        checks[f"resumed_{tag}"] = resumed(metas[tag])
    for name, old, new in (("thresholds", "verdict_tel", "new_tel"), ("free_thresholds", "verdict_free", "new_free")):
        th = pop["policy"].get(name, {}).get("sha256")
        checks[f"{name}_file_is_{old}_meta_sha"] = bool(th is not None and metas[old].get("thresholds_sha256") == th)
        checks[f"{name}_file_is_{new}_meta_sha"] = bool(th is not None and metas[new].get("thresholds_sha256") == th)
    arms_with = {"probe_weights": ("verdict_tel", "new_tel", "verdict_free", "new_free"),
                 "head_weights": ("verdict_tel", "new_tel", "verdict_free", "new_free") if spec["key"] == "oq15" else ()}
    for name in ("probe_weights", "head_weights"):
        if name in pop["policy"]:
            sha = pop["policy"][name]["sha256"]
            checks[f"{name}_file_is_meta_sha"] = bool(sha is not None and all(metas[t].get(f"{name}_sha256") == sha
                                                                                for t in arms_with[name]))
    checks["bound_files_present"] = all(v["sha256"] is not None for v in pop["bound_files"].values())
    counts = {f: pop["families"].count(f) for f in FAMILIES}
    checks["family_counts"] = bool(len(pop["families"]) == FULL_N and all(counts[f] == FAMILY_COUNT for f in FAMILIES))
    nfp = pop["noise_floor"]
    checks["noise_floor_payload_present_with_reliability"] = bool(
        isinstance(nfp, dict) and isinstance(nfp.get("readouts", {}).get("reliability", {}).get("r"), float)
        and nfp.get("population") == pop["key"])
    if checks["noise_floor_payload_present_with_reliability"]:
        prov = nfp.get("provenance", {})
        summ = prov.get("summaries", {}) if isinstance(prov, dict) else {}
        bound_runs = all(summ.get(stem, {}).get("sha256") == runs[f"vanilla_seed{seed}"]["sha256"]
                         and summ.get(stem, {}).get("meta_sha256") == runs[f"vanilla_seed{seed}"]["meta_sha256"]
                         for seed, stem in spec["vanilla_seeds"].items())
        checks["noise_floor_inputs_are_the_loaded_vanilla_runs"] = bool(bound_runs)
        checks["noise_floor_prompts_are_this_file"] = bool(
            isinstance(prov.get("prompts"), dict) and prov["prompts"].get("sha256") == pop["prompts_sha256"])
    booleans = {k: v for k, v in checks.items() if isinstance(v, bool) and not k.startswith("resumed_")}
    return {"checks": checks, "family_counts": counts, "n_checks": len(booleans), "holds": all(booleans.values())}


# ---------------------------------------------------------------------------
# Readouts
# ---------------------------------------------------------------------------

def pooled(run: dict) -> dict:
    return {"tokens_per_call": float(run["emitted"].sum() / run["blocks"].sum()),
            "drafted_per_emitted": float(run["drafted"].sum() / run["emitted"].sum()),
            "n_prompts": int(run["prompt_idx"].shape[0])}


def leg(tel: dict, vanilla: dict, n_boot: int = N_BOOT) -> dict:
    """The E6 leg tel vs vanilla: the record's recipe (tests pin it equal to tools/e6_gate.pair at N_BOOT)."""
    if not np.array_equal(tel["prompt_idx"], vanilla["prompt_idx"]):
        raise SystemExit("arms are not on the same prompt set — the pairing is void")
    d, lo, hi = paired_ratio_delta_ci(tel["emitted"], tel["blocks"], vanilla["emitted"], vanilla["blocks"],
                                      n_boot=n_boot, seed=BOOT_SEED)
    pa, pb = pooled(tel), pooled(vanilla)
    gm = pb["drafted_per_emitted"] + EPSILON - pa["drafted_per_emitted"]
    return {"delta": d, "ci_lower": lo, "ci_upper": hi, "ci_lower_positive": bool(lo > 0.0), "point_at_bar": bool(d >= BAR),
            "budget_guard_margin": gm, "guard_holds": bool(gm >= 0.0), "leg_holds": bool(lo > 0.0 and d >= BAR and gm >= 0.0)}


def readouts(pop: dict, n_boot: int = N_BOOT, draws: int = RELIABILITY_DRAWS) -> dict:
    runs, spec, metas = pop["runs"], pop["spec"], pop["metas"]
    ns = spec["new_seed"]
    vv, vt, nv, nt = runs["verdict_vanilla"], runs["verdict_tel"], runs["new_vanilla"], runs["new_tel"]
    verdict = leg(vt, vv, n_boot)
    new = leg(nt, nv, n_boot)
    dd, lo, hi = paired_ratio_delta_of_deltas_ci(vt["emitted"], vt["blocks"], vv["emitted"], vv["blocks"],
                                                 nt["emitted"], nt["blocks"], nv["emitted"], nv["blocks"],
                                                 n_boot=n_boot, seed=BOOT_SEED)
    new_in_verdict = bool(verdict["ci_lower"] <= new["delta"] <= verdict["ci_upper"])
    verdict_in_new = bool(new["ci_lower"] <= verdict["delta"] <= new["ci_upper"])
    mutual = new_in_verdict and verdict_in_new
    contains_zero = bool(lo <= 0.0 <= hi)
    r1 = {"seed": ns, "tel_arm": spec["tel_arm"], "tel_name": spec["tel_name"], **new,
          "tokens_per_call": {"vanilla": pooled(nv)["tokens_per_call"], "tel": pooled(nt)["tokens_per_call"]},
          "drafted_per_emitted": {"vanilla": pooled(nv)["drafted_per_emitted"], "tel": pooled(nt)["drafted_per_emitted"]},
          "guard_label": "GUARD-HELD" if new["guard_holds"] else "GUARD-BREACHED",
          "resumed": {"vanilla": resumed(metas["new_vanilla"]), "tel": resumed(metas["new_tel"])}}
    r2 = {"verdict_seed": spec["verdict_seed"], "verdict_leg": verdict, "delta_verdict": verdict["delta"],
          "delta_new": new["delta"], "difference": dd, "ci_lower": lo, "ci_upper": hi,
          "difference_ci_half_width": (hi - lo) / 2.0, "difference_ci_contains_zero": contains_zero,
          "new_delta_inside_verdict_ci": new_in_verdict, "verdict_delta_inside_new_ci": verdict_in_new,
          "same_sign": bool(np.sign(verdict["delta"]) == np.sign(new["delta"])),
          "verdict_ci_half_width": (verdict["ci_upper"] - verdict["ci_lower"]) / 2.0,
          "label": "MUTUAL-COVERAGE" if mutual else "DELTA-MOVES", "reading": R2_READING[(mutual, contains_zero)]}
    r3 = {"bar": BAR, "ci_lower_positive": new["ci_lower_positive"], "point_at_bar": new["point_at_bar"],
          "label": "BAR-CLEARED" if (new["ci_lower_positive"] and new["point_at_bar"]) else "BAR-NOT-CLEARED",
          "note": "a single comparator never decides a WIN; unguarded, no free column (D-5); the all-comparator rule "
                  "of F-19 / F-21 is not run here; opens no arc, licenses no registration"}
    committed = pop["noise_floor"]["readouts"]["reliability"]
    pairs = {}
    for seed in sorted(spec["vanilla_seeds"]):
        old = runs[f"vanilla_seed{seed}"]
        if not seed < ns:
            raise SystemExit("the cross-seed null delta is the lower seed minus the higher (F-27's convention); a committed "
                             f"vanilla seed {seed} is not below {ns}")
        rel = nf.reliability(nf.per_prompt_y(old), nf.per_prompt_y(nv), pop["families"], draws=draws, seed=RELIABILITY_SEED)
        d, dlo, dhi = paired_ratio_delta_ci(old["emitted"], old["blocks"], nv["emitted"], nv["blocks"], n_boot=n_boot,
                                            seed=BOOT_SEED)
        pairs[f"{seed}_{ns}"] = {"seeds": [seed, ns], "reliability": rel,
                                       "cross_seed_null_delta": {"delta": d, "ci_lower": dlo, "ci_upper": dhi,
                                                                 "ci_half_width": (dhi - dlo) / 2.0},
                                       "committed_r_inside_ci": bool(rel["ci_lower"] <= committed["r"] <= rel["ci_upper"])}
    r4 = {"committed_pair": {"seeds": sorted(spec["vanilla_seeds"]), "r": committed["r"], "ci_lower": committed["ci_lower"],
                             "ci_upper": committed["ci_upper"], "payload": pop["noise_floor_path"]},
          "pairs": pairs, "note": "the new pairs share the new-seed vanilla run with each other and a committed run with "
                                  "F-27's pair: not independent replications",
          "label": "R-CONSISTENT" if all(p["committed_r_inside_ci"] for p in pairs.values()) else "R-SHIFTS"}
    # ---- the free legs (operator's addition, 2026-10-09): tel vs the mechanism-matched free arm, and free vs vanilla ----
    vf, nfr = runs["verdict_free"], runs["new_free"]
    r5, r6 = cross_seed_leg(vt, vf, nt, nfr, n_boot)
    r5.update({"seed": ns, "tel_arm": spec["tel_arm"], "free_arm": spec["free_arm"], "free_name": spec["free_name"],
               "tokens_per_call": {"free": pooled(nfr)["tokens_per_call"], "tel": pooled(nt)["tokens_per_call"]},
               "drafted_per_emitted": {"free": pooled(nfr)["drafted_per_emitted"], "tel": pooled(nt)["drafted_per_emitted"]},
               "guard_label": "GUARD-FREE-HELD" if r5["guard_holds"] else "GUARD-FREE-BREACHED",
               "resumed_free": resumed(metas["new_free"])})
    r6["verdict_seed"] = spec["verdict_seed"]
    r7 = {"bar": BAR, "ci_lower_positive": r5["ci_lower_positive"], "point_at_bar": r5["point_at_bar"],
          "label": "BAR-CLEARED-FREE" if (r5["ci_lower_positive"] and r5["point_at_bar"]) else "BAR-NOT-CLEARED-FREE",
          "note": "the mechanism-matched comparator (D-11) on a single leg at one new seed; a surprise, never a WIN; the "
                  "all-comparator rule of F-19 / F-21 is not run here; opens no arc, licenses no registration"}
    r8_leg, r8_diff = cross_seed_leg(vf, vv, nfr, nv, n_boot)
    differing = {"verdict": int(np.sum((vf["emitted"] != vv["emitted"]) | (vf["blocks"] != vv["blocks"]))),
                 "new": int(np.sum((nfr["emitted"] != nv["emitted"]) | (nfr["blocks"] != nv["blocks"])))}
    zero_width = (r8_diff["verdict_leg"]["ci_upper"] == r8_diff["verdict_leg"]["ci_lower"]) or (r8_leg["ci_upper"] == r8_leg["ci_lower"])
    near_identical = min(differing.values()) < R8_MIN_DIFFERING or zero_width
    r8 = {"what": "free arm minus vanilla (descriptive; no bar, no guard, no surprise)", "seed": ns, "free_arm": spec["free_arm"],
          "verdict_seed": spec["verdict_seed"], "new_leg": _descriptive(r8_leg), **r8_diff,
          "verdict_leg": _descriptive(r8_diff["verdict_leg"]), "n_differing_prompts": differing,
          "min_differing_prompts": R8_MIN_DIFFERING, "either_ci_zero_width": bool(zero_width)}
    if near_identical:
        r8["label"], r8["reading"] = "NEAR-IDENTICAL-ARMS", None
    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6, "R7": r7, "R8": r8}


def _descriptive(leg_dict: dict) -> dict:
    """A leg without its bar and guard fields (R8 is a description: no bar, no guard, no WIN booleans)."""
    return {k: v for k, v in leg_dict.items()
            if k not in ("ci_lower_positive", "point_at_bar", "budget_guard_margin", "guard_holds", "leg_holds")}


def cross_seed_leg(v_a: dict, v_b: dict, n_a: dict, n_b: dict, n_boot: int) -> tuple[dict, dict]:
    """A leg (arm a minus arm b) at the verdict seed and at the new seed, and the cross-seed difference of the two
    with its joint-draw CI95, the MUTUAL-COVERAGE / DELTA-MOVES label and the pinned reading (R2's machinery)."""
    verdict = leg(v_a, v_b, n_boot)
    new = leg(n_a, n_b, n_boot)
    dd, lo, hi = paired_ratio_delta_of_deltas_ci(v_a["emitted"], v_a["blocks"], v_b["emitted"], v_b["blocks"],
                                                 n_a["emitted"], n_a["blocks"], n_b["emitted"], n_b["blocks"],
                                                 n_boot=n_boot, seed=BOOT_SEED)
    new_in_verdict = bool(verdict["ci_lower"] <= new["delta"] <= verdict["ci_upper"])
    verdict_in_new = bool(new["ci_lower"] <= verdict["delta"] <= new["ci_upper"])
    mutual = new_in_verdict and verdict_in_new
    contains_zero = bool(lo <= 0.0 <= hi)
    diff = {"verdict_leg": verdict, "delta_verdict": verdict["delta"], "delta_new": new["delta"], "difference": dd,
            "ci_lower": lo, "ci_upper": hi, "difference_ci_half_width": (hi - lo) / 2.0, "difference_ci_contains_zero": contains_zero,
            "new_delta_inside_verdict_ci": new_in_verdict, "verdict_delta_inside_new_ci": verdict_in_new,
            "same_sign": bool(np.sign(verdict["delta"]) == np.sign(new["delta"])),
            "verdict_ci_half_width": (verdict["ci_upper"] - verdict["ci_lower"]) / 2.0,
            "label": "MUTUAL-COVERAGE" if mutual else "DELTA-MOVES", "reading": R2_READING[(mutual, contains_zero)]}
    return dict(new), diff


def labels_of(ro: dict) -> dict:
    return {"R2": ro["R2"]["label"], "R2_reading": ro["R2"]["reading"], "R3": ro["R3"]["label"],
            "guard": ro["R1"]["guard_label"], "R4": ro["R4"]["label"],
            "R6": ro["R6"]["label"], "R6_reading": ro["R6"]["reading"], "R7": ro["R7"]["label"],
            "guard_free": ro["R5"]["guard_label"], "R8": ro["R8"]["label"]}


def stage_word(label_r2: str, replication_r2: str, prefix: str = "") -> str:
    n = sum(1 for x in (label_r2, replication_r2) if x == "MUTUAL-COVERAGE")
    return prefix + {2: "SPREAD-COVERED", 1: "SPREAD-SPLIT", 0: "SPREAD-MOVES"}[n]


# ---------------------------------------------------------------------------
# Run, outputs, conclude-from
# ---------------------------------------------------------------------------

def header_of(pop: dict, launch_commit: str | None, constants: dict, smoke: bool) -> dict:
    inputs = {tag: {"stem": pop["stems"][tag], "summary_sha256": pop["runs"][tag]["sha256"],
                    "meta_sha256": pop["runs"][tag]["meta_sha256"]} for tag in pop["runs"]}
    return {"kind": "state_header", "registered": REGISTERED, "population": pop["key"], "role": pop["role"],
            "finding": pop["finding"], "launch_commit": launch_commit, "constants": constants, "smoke": smoke,
            "instrument": "tools/run_seed_replay.py", "instrument_sha256": _sha(Path(__file__)),
            "inputs": inputs, "prompts": pop["prompts_path"], "prompts_sha256": pop["prompts_sha256"],
            "policy_files": pop["policy"], "bound_files": pop["bound_files"], "noise_floor_payload": pop["noise_floor_path"],
            "noise_floor_sha256": pop["noise_floor_sha256"], "readouts": list(READOUT_NAMES)}


def write_outputs(out: Path, pop: dict, prec: dict, ro: dict, header: dict, launch_commit: str | None, smoke: bool) -> None:
    state_path = Path(str(out) + ".state.jsonl")
    rows = [{"kind": "readout", "name": name, "values": _py(ro[name])} for name in READOUT_NAMES]
    with open(state_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(_py(header), sort_keys=True) + "\n")
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    head, tracked = _git()
    payload = {"registered": REGISTERED, "population": pop["key"], "role": pop["role"], "finding": pop["finding"],
               "seeds": {"verdict": pop["spec"]["verdict_seed"], "new": pop["spec"]["new_seed"],
                         "vanilla_pairs": [[s, pop["spec"]["new_seed"]] for s in sorted(pop["spec"]["vanilla_seeds"])]},
               "launch_commit": launch_commit, "smoke": smoke, "precondition": _py(prec), "readouts": _py(ro),
               "labels": labels_of(ro), "n_state_rows": len(rows),
               "provenance": {"instrument": "tools/run_seed_replay.py", "instrument_sha256": header["instrument_sha256"],
                              "git_commit": head, "git_status_tracked": tracked, "inputs": header["inputs"],
                              "prompts": pop["prompts_path"], "prompts_sha256": pop["prompts_sha256"],
                              "policy_files": pop["policy"], "bound_files": pop["bound_files"],
                              "noise_floor_payload": pop["noise_floor_path"], "noise_floor_sha256": pop["noise_floor_sha256"],
                              "state_file": state_path.name, "state_sha256": _sha(state_path), "constants": header["constants"],
                              "numpy_version": np.__version__, "python_version": platform.python_version(),
                              "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}
    Path(out).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def run(args: argparse.Namespace) -> dict:
    out = Path(args.out)
    smoke = args.n_boot is not None or args.draws is not None or Path(args.data_root).resolve() != REAL.resolve()
    if _under_results(out):
        if smoke:
            raise SystemExit("a smoke (--n-boot / --draws / --data-root) may not write under results/")
        if not args.launch_commit:
            raise SystemExit("a registered run needs --launch-commit (the clean commit the new-seed runs launched from)")
        if out.name != f"seed_replay_{args.population}.json":
            raise SystemExit(f"a registered run writes results/real/seed_replay_{args.population}.json (the registered out; its "
                             f"state file is un-ignored by name), not {out.name}")
        head, tracked = _git()
        if tracked or head == "unknown":
            raise SystemExit("the tracked tree is not clean (or git failed) — a registered run refuses to write under results/:\n"
                             + "\n".join(tracked))
    pop = load_pop(args.population, Path(args.data_root), Path(args.prompts_root))
    prec = precondition(pop, args.launch_commit)
    if not prec["holds"]:
        failed = [k for k, v in prec["checks"].items() if v is False and not k.startswith("resumed_")]
        raise SystemExit("precondition does not hold: " + ", ".join(failed) + (f"; missing {prec['missing']}" if prec.get("missing") else ""))
    n_boot = int(args.n_boot) if args.n_boot else N_BOOT
    draws = int(args.draws) if args.draws else RELIABILITY_DRAWS
    constants = {**registered_constants(), "n_boot_used": n_boot, "reliability_draws_used": draws}
    ro = readouts(pop, n_boot=n_boot, draws=draws)
    header = header_of(pop, args.launch_commit, constants, smoke)
    write_outputs(out, pop, prec, ro, header, args.launch_commit, smoke)
    lab = labels_of(ro)
    print(f"{pop['key']} ({pop['role']}, {pop['finding']}): R1 delta at seed {pop['spec']['new_seed']} {ro['R1']['delta']:+.6f} "
          f"[{ro['R1']['ci_lower']:+.6f}, {ro['R1']['ci_upper']:+.6f}] {lab['guard']}; R2 {lab['R2']} / {lab['R2_reading']} "
          f"(difference {ro['R2']['difference']:+.6f} [{ro['R2']['ci_lower']:+.6f}, {ro['R2']['ci_upper']:+.6f}]); "
          f"R3 {lab['R3']}; R4 {lab['R4']}; R5 free leg {ro['R5']['delta']:+.6f} [{ro['R5']['ci_lower']:+.6f}, "
          f"{ro['R5']['ci_upper']:+.6f}] {lab['guard_free']}; R6 {lab['R6']} / {lab['R6_reading']} (difference "
          f"{ro['R6']['difference']:+.6f} [{ro['R6']['ci_lower']:+.6f}, {ro['R6']['ci_upper']:+.6f}]); R7 {lab['R7']}; R8 {lab['R8']}")
    print(f"wrote {out} and {out}.state.jsonl")
    return ro


def precondition_only(args: argparse.Namespace) -> None:
    pop = load_pop(args.population, Path(args.data_root), Path(args.prompts_root))
    prec = precondition(pop, args.launch_commit)
    for k, v in prec["checks"].items():
        print(f"  {k}: {v}")
    print(f"precondition {'HOLDS' if prec['holds'] else 'FAILS'} ({prec['n_checks']} checks)")
    if not prec["holds"]:
        raise SystemExit("precondition does not hold")


def conclude_from(payload_path: Path, data_root: Path = REAL, prompts_root: Path = ROOT) -> dict:
    """Recompute every readout and label from the summaries on disk, bound
    to the payload's state header; refuse any difference (floats within
    FLOAT_TOL, labels exactly)."""
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    state_path = Path(str(payload_path) + ".state.jsonl")
    if payload.get("smoke") and _under_results(payload_path):
        raise SystemExit("a smoke payload under results/ — refusing")
    if _sha(Path(__file__)) != payload["provenance"]["instrument_sha256"]:
        raise SystemExit("the instrument's bytes differ from the sha the payload attests — refusing")
    if _sha(state_path) != payload["provenance"]["state_sha256"]:
        raise SystemExit("the state file's sha differs from the payload's provenance — refusing")
    lines = state_path.read_text(encoding="utf-8").splitlines()
    header, rows = json.loads(lines[0]), [json.loads(ln) for ln in lines[1:]]
    if header.get("kind") != "state_header" or [r["name"] for r in rows] != list(READOUT_NAMES):
        raise SystemExit("state header does not describe the rows — refusing")
    if header["constants"] != payload["provenance"]["constants"]:
        raise SystemExit("the state header's constants differ from the payload's — refusing")
    if payload.get("launch_commit") != header.get("launch_commit") or payload["provenance"]["inputs"] != header["inputs"]:
        raise SystemExit("the payload's launch commit or inputs differ from the sha-bound state header — refusing")
    c = {k: v for k, v in header["constants"].items() if k not in ("n_boot_used", "reliability_draws_used")}
    if c != registered_constants() or header["constants"]["n_boot_used"] != N_BOOT \
            or header["constants"]["reliability_draws_used"] != RELIABILITY_DRAWS:
        if _under_results(payload_path):
            raise SystemExit(f"unregistered constants under results/ — refusing: {header['constants']}")
    pop = load_pop(payload["population"], Path(data_root), Path(prompts_root))
    for tag, inp in header["inputs"].items():
        if tag not in pop["runs"] or pop["runs"][tag]["sha256"] != inp["summary_sha256"]:
            raise SystemExit(f"{inp['stem']}.summary.json on disk is not the one the state file read — refusing")
        if pop["runs"][tag]["meta_sha256"] != inp["meta_sha256"]:
            raise SystemExit(f"{inp['stem']}.meta.json on disk is not the one the state file read — refusing")
    if pop["prompts_sha256"] != header["prompts_sha256"]:
        raise SystemExit("the prompt file on disk is not the one the state file read — refusing")
    if pop["noise_floor_sha256"] != header["noise_floor_sha256"]:
        raise SystemExit("the committed noise_floor payload on disk is not the one the state file read — refusing")
    if pop["policy"] != header["policy_files"] or pop["bound_files"] != header["bound_files"]:
        raise SystemExit("a policy or bound file on disk is not the one the state file read — refusing")
    prec = precondition(pop, header["launch_commit"])
    if not prec["holds"]:
        raise SystemExit("conclude-from: the precondition no longer holds — refusing")
    if _py(prec) != payload["precondition"]:
        raise SystemExit("conclude-from: the precondition's checks differ from the payload's — refusing")
    ro = readouts(pop, n_boot=header["constants"]["n_boot_used"], draws=header["constants"]["reliability_draws_used"])
    for row in rows:
        if not nf._close(_py(ro[row["name"]]), row["values"], FLOAT_TOL):
            raise SystemExit(f"conclude-from: recomputed {row['name']} differs from the state row — refusing")
    if not nf._close(_py(ro), payload["readouts"], FLOAT_TOL) or labels_of(ro) != payload["labels"]:
        raise SystemExit("conclude-from: recomputed readouts or labels differ from the payload — refusing")
    print(f"conclude-from OK: {payload['population']} labels {payload['labels']} reproduce from the summaries on disk")
    return payload


def _jsonl_rows(path: Path) -> list[dict]:
    rows = [json.loads(ln) for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    return sorted(rows, key=lambda d: d["prompt_idx"])


def _compare_rows(got: list[dict], want: list[dict], ignore: tuple[str, ...]) -> list[dict]:
    out = []
    for g, w in zip(got, want):
        keys = sorted((set(g) | set(w)) - set(ignore))
        diffs = {k: [g.get(k), w.get(k)] for k in keys if g.get(k) != w.get(k)}
        out.append({"prompt_idx": w.get("prompt_idx"), "match": not diffs, "differing_fields": sorted(diffs)})
    return out


def replay_check(root: Path = REAL, specs=REPLAY_SPECS, launch_commit: str | None = None) -> dict:
    """The pinned launch gate, recomputable from the repo: each replay sidecar's first rows against the committed
    verdict files — generated_ids token for token (every .gen.jsonl field but run_id) and every .stats.jsonl field
    but run_id, seconds and peak_vram_gb — plus the replay meta bound to the verdict meta (arm, seed, prompt and
    policy shas), n_prompts as pinned, and the clean launch commit when one is given."""
    root = Path(root)
    report = {"specs": [list(s) for s in specs], "launch_commit": launch_commit, "arms": {}, "all_match": True}
    for rs, vs, k, seed in specs:
        entry: dict = {"verdict_stem": vs, "n_prompts": k, "seed": seed}
        missing = [f"{rs}.{e}" for e in ("gen.jsonl", "stats.jsonl", "meta.json") if not (root / f"{rs}.{e}").exists()]
        if missing:
            entry.update({"match": False, "missing": missing})
            report["arms"][rs], report["all_match"] = entry, False
            print(f"REPLAY {rs}: MISSING {missing}")
            continue
        gen = _compare_rows(_jsonl_rows(root / f"{rs}.gen.jsonl"), _jsonl_rows(root / f"{vs}.gen.jsonl")[:k], GEN_IGNORE)
        stats = _compare_rows(_jsonl_rows(root / f"{rs}.stats.jsonl"), _jsonl_rows(root / f"{vs}.stats.jsonl")[:k], STATS_IGNORE)
        rm, vm = load_meta(rs, root), load_meta(vs, root)
        meta_ok = {key: rm.get(key) == vm.get(key) for key in META_BOUND}
        meta_ok["seed_is_pinned"] = rm.get("seed") == seed
        meta_ok["n_prompts_is_pinned"] = rm.get("n_prompts") == k
        gc = str(rm.get("git_commit"))
        meta_ok["launch_commit_clean"] = launch_commit is None or (gc == launch_commit and "-dirty" not in gc)
        n_gen, n_stats = len(_jsonl_rows(root / f"{rs}.gen.jsonl")), len(_jsonl_rows(root / f"{rs}.stats.jsonl"))
        entry.update({"gen_rows": gen, "stats_rows": stats, "meta": meta_ok, "git_commit": gc,
                      "match": bool(n_gen == k and n_stats == k and all(r["match"] for r in gen)
                                    and all(r["match"] for r in stats) and all(meta_ok.values()))})
        report["arms"][rs] = entry
        report["all_match"] &= entry["match"]
        print(f"REPLAY {rs} vs {vs} (seed {seed}, {k} prompt{'s' if k > 1 else ''}): generated_ids "
              f"{sum(r['match'] for r in gen)}/{k} token-exact; stats rows {sum(r['match'] for r in stats)}/{k} equal except "
              f"run_id/seconds/peak_vram_gb; meta {'bound' if all(meta_ok.values()) else 'NOT bound ' + str([m for m, v in meta_ok.items() if not v])}; "
              f"git {gc}; {'PASS' if entry['match'] else 'FAIL'}")
    print(f"REPLAY CHECK {'PASS' if report['all_match'] else 'FAIL -> REPLAY-MISMATCH'}")
    return report


def stage_word_from(label_path: Path, replication_path: Path) -> str:
    a = json.loads(Path(label_path).read_text(encoding="utf-8"))
    b = json.loads(Path(replication_path).read_text(encoding="utf-8"))
    if (a["role"], b["role"]) != ("label", "replication"):
        raise SystemExit("--stage-word takes the label payload then the replication payload")
    if a.get("registered") != REGISTERED or b.get("registered") != REGISTERED:
        raise SystemExit("--stage-word takes this registration's payloads only")
    for p, pl in ((label_path, a), (replication_path, b)):
        if pl.get("smoke") and _under_results(p):
            raise SystemExit(f"a smoke payload under results/ — refusing ({p})")
    word = stage_word(a["labels"]["R2"], b["labels"]["R2"])
    free = stage_word(a["labels"]["R6"], b["labels"]["R6"], "FREE-")
    print(f"stage word {word}: {a['population']} R2 {a['labels']['R2']} ({a['labels']['R2_reading']}), "
          f"{b['population']} R2 {b['labels']['R2']} ({b['labels']['R2_reading']})")
    print(f"free-leg stage word {free}: {a['population']} R6 {a['labels']['R6']} ({a['labels']['R6_reading']}), "
          f"{b['population']} R6 {b['labels']['R6']} ({b['labels']['R6_reading']})")
    return word


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", choices=sorted(POPULATIONS), default=None)
    ap.add_argument("--out", default=None, help="payload path; the state file is written beside it")
    ap.add_argument("--launch-commit", default=None, help="the clean commit the new-seed GPU runs launched from")
    ap.add_argument("--data-root", default=str(REAL))
    ap.add_argument("--prompts-root", default=str(ROOT))
    ap.add_argument("--precondition-only", action="store_true")
    ap.add_argument("--conclude-from", default=None, help="recompute a payload's readouts and labels from its state file")
    ap.add_argument("--stage-word", nargs=2, default=None, metavar=("LABEL_PAYLOAD", "REPLICATION_PAYLOAD"))
    ap.add_argument("--replay-check", action="store_true", help="the pinned launch gate over the committed replay sidecars")
    ap.add_argument("--n-boot", default=None, help="smoke only: bootstrap draws (refused under results/)")
    ap.add_argument("--draws", default=None, help="smoke only: reliability draws (refused under results/)")
    args = ap.parse_args()
    if args.replay_check:
        if not replay_check(Path(args.data_root), launch_commit=args.launch_commit)["all_match"]:
            raise SystemExit(2)
        return
    if args.conclude_from:
        conclude_from(Path(args.conclude_from), Path(args.data_root), Path(args.prompts_root))
        return
    if args.stage_word:
        stage_word_from(Path(args.stage_word[0]), Path(args.stage_word[1]))
        return
    if not args.population:
        raise SystemExit("--population is required")
    if args.precondition_only:
        precondition_only(args)
        return
    if not args.out:
        raise SystemExit("--out is required for a run")
    run(args)


if __name__ == "__main__":
    main()

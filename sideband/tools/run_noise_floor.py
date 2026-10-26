#!/usr/bin/env python
"""tools/run_noise_floor.py — SEED-NOISE FLOOR READOUTS on the four committed
vanilla gamma-4 verdict runs (docs/IDEAS.md rank 1's first step).

Registered 2026-10-04 in docs/BLUEPRINT.md ("SEED-NOISE FLOOR READOUTS
REGISTRATION"); NON-CRITERION for every finding; a methods datum. CPU only;
numpy only — nothing in this file imports torch, and nothing under tools/ is
imported (the frozen-instrument closure stays this file alone).

Data: the per_prompt_stats of two committed vanilla summaries per population
(the same 210 prompts at two sampling seeds; K3 = F-19's seed pair 0 / 1 on
data/prompts_k3_verdict.jsonl, OQ15 = seeds 2 / 3 on
data/prompts_oq15_verdict.jsonl), their metas (seed and prompt-file sha, the
binding) and the prompt files' "family" field.

Estimand (E6): tokens/call on a prompt set = sum n_emitted / sum n_blocks;
the NULL DELTA = seed A (the lower seed) minus seed B on the same prompts;
CI95 by sideband.stats.paired_ratio_delta_ci (n_boot 2000, seed 0), exactly
as tools/e6_gate.py computes a gate leg; budget = sum n_drafted / sum
n_emitted; the pairwise budget guard dpe_tested <= dpe_comparator + 0.01.
Between fixed-gamma-4 vanilla runs n_drafted == 4 n_blocks on every prompt
(a PRECONDITION), so dpe = 4 / tokens-per-call and the guard cannot bind:
the guarded rates equal the unguarded ones by algebra (an identity check).
This is a CROSS-SEED, same-policy, single-comparator null; the record's
gate legs are same-seed (D-6) and all-comparator, and that null is not
measured here.

Readouts (per population, all 210 prompts):
  R1 reliability     Pearson r of per-prompt tokens/call across the seeds,
                     prompt-bootstrap CI95 (2000 draws, own rng(0)); r per
                     family and the within-family r (family-centred); the sd
                     of the 420 prompt-run values; mean |y_A - y_B|.
  R2 decomposition   nested sums of squares seed-within-prompt /
                     prompt-within-family / family: SS / 420 and SS shares
                     (ML), plus the balanced nested method-of-moments
                     components (SS_seed/210; (SS_prompt/207 - SS_seed/210)/2;
                     (SS_family/2 - SS_prompt/207)/140).
  R3 half-width      M = 1000 subsets without replacement at n in {30, 42,
                     84, 126} (own rng(1)), the full set at 210; per subset
                     delta, lo, hi, dpe_A, dpe_B; half-width quantiles per n.
  R4 exceedance      f_plus / f_minus / f_two / f_one of the +0.062 bar.
  R5 single-leg rule g_* (CI95 lower > 0 AND point >= bar) in both
                     orientations, with and without the budget guard.
  R6 F-19 percentile the share of pooled n = 30 null draws >= +0.059725.
  SWAP companion     on every subset (and M draws of the full set) a random
                     per-prompt seed-label swap (own rng(2)): a null centred
                     at zero without finite-population shrinkage; reported,
                     never a label.
Labels are mechanical (conclude()); --conclude-from recomputes every
readout and label from the state file and the committed summaries and
refuses a payload whose stored numbers differ. Evidence files are written
with LF newlines. BLAS threads: a default of 2 is set unless the environment
already names a value; the value in force is recorded.

Usage:
  python tools/run_noise_floor.py --population k3 --out results/real/noise_floor_k3.json
  python tools/run_noise_floor.py --population oq15 --out results/real/noise_floor_oq15.json
  python tools/run_noise_floor.py --population k3 --precondition-only
  python tools/run_noise_floor.py --conclude-from results/real/noise_floor_k3.json
Smoke (refused under results/): --m-subsets / --sizes / --n-boot overrides.
"""

from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "2")  # the GPU box carries other work; the value in force is recorded

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sideband.stats import paired_ratio_delta_ci  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "results" / "real"

REGISTERED = ("SEED-NOISE FLOOR READOUTS REGISTRATION (docs/BLUEPRINT.md, 2026-10-04; pre-run; "
              "NON-CRITERION; a methods datum on the committed vanilla runs)")
BAR = 0.062                      # docs/ECONOMICS.md S5 materiality bar, tokens per verify call
EPSILON = 0.01                   # pairwise budget guard allowance (K-3 arc registration)
GAMMA = 4                        # the vanilla arms' fixed draft length: n_drafted == GAMMA * n_blocks
N_BOOT, BOOT_SEED = 2000, 0      # the paired_ratio_delta_ci recipe of F-19 / F-21 / e6_gate
SIZES = (30, 42, 84, 126, 210)   # prompt counts the record has used
M_SUBSETS = 1000                 # subsets per n below 210; swap draws per n at every n
RELIABILITY_DRAWS, RELIABILITY_SEED = 2000, 0
SUBSET_SEED = 1
SWAP_SEED = 2
KILL = 0.02                      # IDEAS rank 1: f_one at n = 30 below 2% -> FLOOR-WEAK
RULE_REPORT = 0.01               # reporting threshold for RULE-LEAKS@30 (no consequence)
LABEL_N, FULL_N = 30, 210
# F-19's val-selected advantage on 30 val prompts: k3_threshold_search_arm4.json
# selection.tokens_per_call minus k3_val_arm1.summary.json tokens_per_call.
F19_VAL_ADVANTAGE = 3.191969887076537 - 3.1322448979591835
FAMILIES = ("instruct", "story", "summarize")
FAMILY_COUNT = 70

POPULATIONS = {
    "k3": {"role": "label", "prompts": "data/prompts_k3_verdict.jsonl",
           "a": ("k3_verdict_arm1", 0), "b": ("k3_verdict_s1_arm1", 1),
           "note": "F-19's seed pair; the seed-0 verdict SET was voided for the test arm's "
                   "budget guard, the vanilla run was never voided as a measurement"},
    "oq15": {"role": "replication", "prompts": "data/prompts_oq15_verdict.jsonl",
             "a": ("oq15c_verdict_arm1", 2), "b": ("oq15c_verdict_s3_arm1", 3),
             "note": "F-21's population; the seed-2 Stage-C SET was voided for the test arm's "
                     "budget guard, the vanilla run was never voided as a measurement"},
}


def registered_constants() -> dict:
    return {"bar": BAR, "epsilon": EPSILON, "gamma": GAMMA, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
            "sizes": list(SIZES), "m_subsets": M_SUBSETS, "subset_seed": SUBSET_SEED, "swap_seed": SWAP_SEED,
            "reliability_draws": RELIABILITY_DRAWS, "reliability_seed": RELIABILITY_SEED, "kill": KILL,
            "rule_report": RULE_REPORT, "label_n": LABEL_N, "full_n": FULL_N, "f19_val_advantage": F19_VAL_ADVANTAGE,
            "families": list(FAMILIES), "family_count": FAMILY_COUNT}


# ---------------------------------------------------------------------------
# Loading and the precondition
# ---------------------------------------------------------------------------

def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git() -> tuple[str, str]:
    """(HEAD sha, porcelain status of TRACKED files) or ('unknown', 'unknown')."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
        return head, status
    except (OSError, subprocess.CalledProcessError):
        return "unknown", "unknown"


def _under_results(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to((ROOT / "results").resolve())
        return True
    except ValueError:
        return False


def _write_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_run(stem: str, root: Path = REAL) -> dict:
    """The per-prompt (emitted, blocks, drafted) rows of a committed summary,
    sorted by prompt_idx, with the summary's own pooled fields for the gate
    and the meta's seed and prompt-file sha for the binding."""
    path = Path(root) / f"{stem}.summary.json"
    s = json.loads(path.read_text(encoding="utf-8"))
    pp = sorted(s["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    meta_path = Path(root) / f"{stem}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return {
        "stem": stem, "path": path, "sha256": _sha(path),
        "meta_path": meta_path, "meta_sha256": _sha(meta_path) if meta_path.exists() else None,
        "meta_seed": meta.get("seed"), "meta_prompts_sha256": meta.get("prompts_sha256"),
        "prompt_idx": np.array([int(p["prompt_idx"]) for p in pp], dtype=np.int64),
        "orig_prompt_idx": np.array([int(p.get("orig_prompt_idx", p["prompt_idx"])) for p in pp], dtype=np.int64),
        "emitted": np.array([p["n_emitted"] for p in pp], dtype=np.float64),
        "blocks": np.array([p["n_blocks"] for p in pp], dtype=np.float64),
        "drafted": np.array([p["n_drafted"] for p in pp], dtype=np.float64),
        "tpc_field": np.array([p["tokens_per_call"] for p in pp], dtype=np.float64),
        "summary_tokens_per_call": float(s["tokens_per_call"]),
        "summary_drafted_per_emitted": float(s["drafted_per_emitted"]),
    }


def load_families(path: Path) -> tuple[list[str], str]:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [str(r["family"]) for r in rows], _sha(path)


def load_population(key: str, root: Path = REAL, prompts_root: Path = ROOT) -> dict:
    spec = POPULATIONS[key]
    a, b = load_run(spec["a"][0], root), load_run(spec["b"][0], root)
    families, prompts_sha = load_families(Path(prompts_root) / spec["prompts"])
    return {"key": key, "role": spec["role"], "a": a, "b": b, "seeds": (spec["a"][1], spec["b"][1]),
            "families": families, "prompts_path": spec["prompts"], "prompts_sha256": prompts_sha}


def precondition(pop: dict) -> dict:
    """REPRODUCE: pooled fields bit-exact, per-prompt ratio exact, prompt sets
    identical and complete, orig_prompt_idx == prompt_idx (the family binding),
    n_drafted == GAMMA n_blocks everywhere (the guard identity), the metas'
    seeds and prompt-file sha bound, family counts 70 / 70 / 70. Any failure
    voids."""
    a, b = pop["a"], pop["b"]
    checks = {}
    for tag, r, seed in (("a", a, pop["seeds"][0]), ("b", b, pop["seeds"][1])):
        checks[f"pooled_tokens_per_call_bit_exact_{tag}"] = bool(
            float(r["emitted"].sum() / r["blocks"].sum()) == r["summary_tokens_per_call"])
        checks[f"pooled_drafted_per_emitted_bit_exact_{tag}"] = bool(
            float(r["drafted"].sum() / r["emitted"].sum()) == r["summary_drafted_per_emitted"])
        checks[f"per_prompt_ratio_exact_{tag}"] = bool(
            np.max(np.abs(r["tpc_field"] - r["emitted"] / r["blocks"])) <= 1e-12)
        checks[f"blocks_positive_{tag}"] = bool(np.all(r["blocks"] > 0))
        checks[f"drafted_is_gamma_blocks_{tag}"] = bool(np.array_equal(r["drafted"], GAMMA * r["blocks"]))
        checks[f"orig_prompt_idx_is_prompt_idx_{tag}"] = bool(np.array_equal(r["orig_prompt_idx"], r["prompt_idx"]))
        checks[f"meta_seed_is_registered_{tag}"] = bool(r["meta_seed"] == seed)
        checks[f"meta_prompts_sha_is_file_{tag}"] = bool(r["meta_prompts_sha256"] == pop["prompts_sha256"])
    n = int(a["prompt_idx"].shape[0])
    checks["prompt_sets_identical"] = bool(a["prompt_idx"].shape == b["prompt_idx"].shape
                                           and np.array_equal(a["prompt_idx"], b["prompt_idx"]))
    checks["prompt_set_complete"] = bool(n == FULL_N and np.array_equal(a["prompt_idx"], np.arange(FULL_N)))
    counts = {f: pop["families"].count(f) for f in FAMILIES}
    checks["family_counts"] = bool(len(pop["families"]) == FULL_N and all(counts[f] == FAMILY_COUNT for f in FAMILIES)
                                   and len(pop["families"]) == n)
    return {"checks": checks, "family_counts": counts, "n_prompts": n, "n_checks": len(checks),
            "holds": all(checks.values())}


# ---------------------------------------------------------------------------
# Readouts
# ---------------------------------------------------------------------------

def per_prompt_y(run: dict) -> np.ndarray:
    return run["emitted"] / run["blocks"]


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    xc, yc = x - x.mean(), y - y.mean()
    den = math.sqrt(float((xc * xc).sum()) * float((yc * yc).sum()))
    return float((xc * yc).sum() / den) if den > 0 else float("nan")


def reliability(ya: np.ndarray, yb: np.ndarray, families: list[str] | None = None,
                draws: int = RELIABILITY_DRAWS, seed: int = RELIABILITY_SEED) -> dict:
    """R1: Pearson r across the seeds with a prompt-bootstrap percentile CI95
    (half-width (hi - lo) / 2); r per family and the within-family r (both
    series centred on their own family means per seed), reported without CIs."""
    n = ya.shape[0]
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, n, size=(draws, n))
    xs, ys = ya[idx], yb[idx]
    xc = xs - xs.mean(axis=1, keepdims=True)
    yc = ys - ys.mean(axis=1, keepdims=True)
    den = np.sqrt((xc * xc).sum(axis=1) * (yc * yc).sum(axis=1))
    valid = den > 0
    rs = (xc * yc).sum(axis=1)[valid] / den[valid]
    lo, hi = np.percentile(rs, [2.5, 97.5])
    both = np.concatenate([ya, yb])
    out = {"r": _pearson(ya, yb), "ci_lower": float(lo), "ci_upper": float(hi), "ci_half_width": float((hi - lo) / 2.0),
           "n_draws_valid": int(valid.sum()), "n_draws": int(draws), "seed": int(seed),
           "sd_prompt_runs": float(both.std(ddof=0)), "mean_abs_seed_diff": float(np.abs(ya - yb).mean()),
           "mean_a": float(ya.mean()), "mean_b": float(yb.mean())}
    if families is not None:
        fam = np.array(families)
        ya_c, yb_c = ya.copy(), yb.copy()
        per_family = {}
        for f in sorted(set(families)):
            m = fam == f
            per_family[f] = _pearson(ya[m], yb[m])
            ya_c[m] -= ya[m].mean()
            yb_c[m] -= yb[m].mean()
        out["r_per_family"] = per_family
        out["r_within_family"] = _pearson(ya_c, yb_c)
    return out


def decompose(ya: np.ndarray, yb: np.ndarray, families: list[str]) -> dict:
    """R2: nested sums of squares over the 2n prompt-run values y[p, s]; SS / 2n
    and SS shares (ML), plus the balanced nested method-of-moments components
    (two seeds per prompt, 70 prompts per family, three families: df 210 /
    207 / 2). A negative component is reported as computed and said in
    words; the MoM shares are defined only where all three are >= 0."""
    y = np.stack([ya, yb], axis=1)              # (n, 2)
    fam = np.array(families)
    n = y.shape[0]
    ybar = float(y.mean())
    ybar_p = y.mean(axis=1)                     # (n,)
    ss_total = float(((y - ybar) ** 2).sum())
    ss_seed = float(((y - ybar_p[:, None]) ** 2).sum())
    ss_prompt, ss_family, fam_means = 0.0, 0.0, {}
    fams = sorted(set(families))
    for f in fams:
        m = fam == f
        ybar_f = float(y[m].mean())
        ss_prompt += float((2.0 * (ybar_p[m] - ybar_f) ** 2).sum())
        ss_family += float(2.0 * m.sum() * (ybar_f - ybar) ** 2)
        fam_means[f] = {"pooled": ybar_f, "a": float(ya[m].mean()), "b": float(yb[m].mean()), "n_prompts": int(m.sum())}
    total_rel_err = abs(ss_total - (ss_seed + ss_prompt + ss_family)) / max(ss_total, 1e-300)
    denom = 2.0 * n
    n_fam = len(fams)
    df_seed, df_prompt, df_family = n, n - n_fam, n_fam - 1
    per_family_obs = denom / n_fam                       # 140 prompt-runs per family when balanced
    ms_seed = ss_seed / df_seed if df_seed > 0 else float("nan")
    ms_prompt = ss_prompt / df_prompt if df_prompt > 0 else float("nan")
    ms_family = ss_family / df_family if df_family > 0 else float("nan")
    mom = {"seed_within_prompt": ms_seed,
           "prompt_within_family": (ms_prompt - ms_seed) / 2.0,
           "family": (ms_family - ms_prompt) / per_family_obs}
    mom_nonneg = all(v >= 0 for v in mom.values())
    mom_total = sum(mom.values())
    return {"n_prompt_runs": int(denom), "grand_mean": ybar,
            "ss": {"total": ss_total, "seed_within_prompt": ss_seed, "prompt_within_family": ss_prompt, "family": ss_family},
            "variance": {"total": ss_total / denom, "seed_within_prompt": ss_seed / denom,
                         "prompt_within_family": ss_prompt / denom, "family": ss_family / denom},
            "share": {"seed_within_prompt": ss_seed / ss_total if ss_total > 0 else float("nan"),
                      "prompt_within_family": ss_prompt / ss_total if ss_total > 0 else float("nan"),
                      "family": ss_family / ss_total if ss_total > 0 else float("nan")},
            "identity_rel_err": float(total_rel_err), "identity_holds": bool(total_rel_err <= 1e-9),
            "mom": {"df": {"seed_within_prompt": int(df_seed), "prompt_within_family": int(df_prompt), "family": int(df_family)},
                    "mean_square": {"seed_within_prompt": ms_seed, "prompt_within_family": ms_prompt, "family": ms_family},
                    "component": mom, "all_nonnegative": bool(mom_nonneg), "total": float(mom_total),
                    "share": ({k: v / mom_total for k, v in mom.items()} if mom_nonneg and mom_total > 0 else None),
                    "note": "balanced nested method of moments; family has two df and is a fixed effect of three named "
                            "families, so its component is a descriptive variance of three means"},
            "family_means": fam_means}


def draw_subsets(sizes: tuple[int, ...], m_subsets: int, n_total: int, seed: int = SUBSET_SEED) -> dict[int, np.ndarray]:
    """Per n (ascending): m_subsets SORTED index sets without replacement, or the
    one full set at n == n_total. One generator per call, n drawn in order."""
    gen = np.random.default_rng(seed)
    out: dict[int, np.ndarray] = {}
    for n in sorted(sizes):
        if n > n_total:
            raise ValueError(f"subset size {n} exceeds the {n_total} prompts")
        if n == n_total:
            out[n] = np.arange(n_total, dtype=np.int64)[None, :]
            continue
        rows = np.empty((m_subsets, n), dtype=np.int64)
        for k in range(m_subsets):
            rows[k] = np.sort(gen.choice(n_total, size=n, replace=False))
        out[n] = rows
    return out


def draw_swaps(sizes: tuple[int, ...], m_subsets: int, seed: int = SWAP_SEED) -> dict[int, np.ndarray]:
    """Per n (ascending): m_subsets boolean masks of length n (True = the
    prompt's seed labels are swapped), one generator per call."""
    gen = np.random.default_rng(seed)
    return {n: gen.integers(0, 2, size=(m_subsets, n)).astype(bool) for n in sorted(sizes)}


def mask_to_hex(mask: np.ndarray) -> str:
    bits = "".join("1" if b else "0" for b in mask)
    return f"{len(mask)}:{int(bits, 2):x}" if len(mask) else "0:0"


def hex_to_mask(text: str) -> np.ndarray:
    n_s, hx = text.split(":")
    n = int(n_s)
    bits = bin(int(hx, 16))[2:].zfill(n) if n else ""
    return np.array([c == "1" for c in bits[-n:]], dtype=bool) if n else np.zeros(0, dtype=bool)


def subset_row(a: dict, b: dict, idx: np.ndarray, swap: np.ndarray | None = None,
               n_boot: int = N_BOOT, boot_seed: int = BOOT_SEED) -> dict:
    """One state row: the null delta A - B on these prompts with its CI95, the
    half-width and both budgets (the bootstrap is e6_gate's recipe); with a
    swap mask, the SWAP companion on the same prompts (A' = A where not
    swapped, B where swapped; B' the complement)."""
    ea, ba, da = a["emitted"][idx], a["blocks"][idx], a["drafted"][idx]
    eb, bb, db = b["emitted"][idx], b["blocks"][idx], b["drafted"][idx]
    delta, lo, hi = paired_ratio_delta_ci(ea, ba, eb, bb, n_boot=n_boot, seed=boot_seed)
    row = {"delta": float(delta), "lo": float(lo), "hi": float(hi), "hw": float((hi - lo) / 2.0),
           "dpe_a": float(da.sum() / ea.sum()), "dpe_b": float(db.sum() / eb.sum())}
    if swap is not None:
        ea2, ba2 = np.where(swap, eb, ea), np.where(swap, bb, ba)
        eb2, bb2 = np.where(swap, ea, eb), np.where(swap, ba, bb)
        d2, lo2, hi2 = paired_ratio_delta_ci(ea2, ba2, eb2, bb2, n_boot=n_boot, seed=boot_seed)
        row.update({"swap": mask_to_hex(swap), "delta_sw": float(d2), "lo_sw": float(lo2), "hi_sw": float(hi2),
                    "hw_sw": float((hi2 - lo2) / 2.0), "n_swapped": int(swap.sum())})
    return row


def _rate(count: int, m: int) -> dict:
    f = count / m
    return {"rate": float(f), "count": int(count), "m": int(m), "se": float(math.sqrt(f * (1.0 - f) / m))}


def _half(two: dict) -> dict:
    """The one-sided rate: half the two-sided count rate, SE half of its SE."""
    return {"rate": two["rate"] / 2.0, "se": two["se"] / 2.0, "count": two["count"], "m": two["m"]}


def _quantiles(x: np.ndarray) -> dict:
    return {"median": float(np.median(x)), "mean": float(x.mean()), "p05": float(np.percentile(x, 5)),
            "p95": float(np.percentile(x, 95)), "min": float(x.min()), "max": float(x.max())}


def _rates(d: np.ndarray, lo: np.ndarray, hi: np.ndarray, dpe_a: np.ndarray | None, dpe_b: np.ndarray | None,
           bar: float, epsilon: float) -> dict:
    m = d.shape[0]
    plus, minus = d >= bar, d <= -bar
    win_plus, win_minus = (lo > 0) & plus, (hi < 0) & minus
    out = {"f_plus": _rate(int(plus.sum()), m), "f_minus": _rate(int(minus.sum()), m),
           "f_two": _rate(int(plus.sum() + minus.sum()), m),
           "g_plus": _rate(int(win_plus.sum()), m), "g_minus": _rate(int(win_minus.sum()), m),
           "g_two": _rate(int(win_plus.sum() + win_minus.sum()), m)}
    out["f_one"] = _half(out["f_two"])
    out["g_one"] = _half(out["g_two"])
    if dpe_a is not None:
        guard_a, guard_b = dpe_a <= dpe_b + epsilon, dpe_b <= dpe_a + epsilon   # A tested vs B; B tested vs A
        out["g_plus_guard"] = _rate(int((win_plus & guard_a).sum()), m)
        out["g_minus_guard"] = _rate(int((win_minus & guard_b).sum()), m)
        out["g_two_guard"] = _rate(int((win_plus & guard_a).sum() + (win_minus & guard_b).sum()), m)
        out["g_one_guard"] = _half(out["g_two_guard"])
        out["guard_holds_a_over_b"] = _rate(int(guard_a.sum()), m)
        out["guard_holds_b_over_a"] = _rate(int(guard_b.sum()), m)
        out["guard_identity_holds"] = bool(out["g_two_guard"]["count"] == out["g_two"]["count"]
                                           and out["g_plus_guard"]["count"] == out["g_plus"]["count"])
    return out


def rates_for_n(rows: list[dict], n: int | None = None, bar: float = BAR, epsilon: float = EPSILON,
                full_n: int | None = None) -> dict:
    """R3 quantiles, R4 exceedance and R5 single-leg rates over one n's subsets,
    plus the SWAP companion over every row. At n == full_n the primary rows
    are one draw (idx 0); the swap rows are all of them."""
    full_n = FULL_N if full_n is None else full_n
    primary = rows if (n is None or n != full_n) else [r for r in rows if r["idx"] == 0]
    d = np.array([r["delta"] for r in primary]); lo = np.array([r["lo"] for r in primary]); hi = np.array([r["hi"] for r in primary])
    hw = np.array([r["hw"] for r in primary]); dpe_a = np.array([r["dpe_a"] for r in primary]); dpe_b = np.array([r["dpe_b"] for r in primary])
    m = d.shape[0]
    out = {"m": int(m), "single_draw": bool(m == 1), "half_width": _quantiles(hw),
           "delta": {"mean": float(d.mean()), "sd": float(d.std(ddof=0)), "min": float(d.min()), "max": float(d.max())}}
    out.update(_rates(d, lo, hi, dpe_a, dpe_b, bar, epsilon))
    if m == 1:
        out["single"] = {k: primary[0][k] for k in ("delta", "lo", "hi", "hw", "dpe_a", "dpe_b")}
    swap_rows = [r for r in rows if "delta_sw" in r]
    if swap_rows:
        ds = np.array([r["delta_sw"] for r in swap_rows]); los = np.array([r["lo_sw"] for r in swap_rows])
        his = np.array([r["hi_sw"] for r in swap_rows]); hws = np.array([r["hw_sw"] for r in swap_rows])
        sw = {"m": int(ds.shape[0]), "half_width": _quantiles(hws),
              "delta": {"mean": float(ds.mean()), "sd": float(ds.std(ddof=0)), "min": float(ds.min()), "max": float(ds.max())},
              "mean_n_swapped": float(np.mean([r["n_swapped"] for r in swap_rows]))}
        sw.update(_rates(ds, los, his, None, None, bar, epsilon))
        out["swap"] = sw
    return out


def f19_percentile(rows_30: list[dict], advantage: float = F19_VAL_ADVANTAGE) -> dict:
    """R6: the share of the pooled n = 30 null draws {delta, -delta} at or above
    F-19's val-selected advantage; a description, not a reading of F-19. The
    SWAP companion's share beside it."""
    d = np.array([r["delta"] for r in rows_30])
    pooled = np.concatenate([d, -d])
    k = int((pooled >= advantage).sum())
    out = {"advantage": float(advantage), "share_at_or_above": k / pooled.shape[0], "count": k,
           "n_pooled": int(pooled.shape[0]), "percentile_of_advantage": 1.0 - k / pooled.shape[0]}
    sw = [r for r in rows_30 if "delta_sw" in r]
    if sw:
        ds = np.array([r["delta_sw"] for r in sw])
        pooled_sw = np.concatenate([ds, -ds])
        ks = int((pooled_sw >= advantage).sum())
        out["swap"] = {"share_at_or_above": ks / pooled_sw.shape[0], "count": ks, "n_pooled": int(pooled_sw.shape[0])}
    return out


def readouts_from_rows(pop: dict, state_rows: list[dict], sizes: tuple[int, ...] = SIZES,
                       reliability_draws: int = RELIABILITY_DRAWS, full_n: int = FULL_N, label_n: int = LABEL_N) -> dict:
    """Every readout from the per-subset rows plus the per-prompt values."""
    ya, yb = per_prompt_y(pop["a"]), per_prompt_y(pop["b"])
    by_n: dict[int, list[dict]] = {n: [] for n in sizes}
    for r in state_rows:
        by_n[int(r["n"])].append(r)
    per_n = {str(n): rates_for_n(by_n[n], n=n, full_n=full_n) for n in sizes}
    full = per_n.get(str(full_n))
    return {"reliability": reliability(ya, yb, pop["families"], draws=reliability_draws),
            "decomposition": decompose(ya, yb, pop["families"]),
            "per_n": per_n,
            "f19": f19_percentile(by_n[label_n]) if label_n in by_n else None,
            "full_set_delta": full["single"]["delta"] if full is not None and "single" in full else None,
            "guard_identity_holds_everywhere": bool(all(per_n[str(n)].get("guard_identity_holds", True) for n in sizes))}


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes it)
# ---------------------------------------------------------------------------

def conclude(readouts: dict, prec: dict, role: str, kill: float = KILL, bar: float = BAR,
             rule_report: float = RULE_REPORT, label_n: int = LABEL_N, full_n: int = FULL_N) -> dict:
    if not prec["holds"] or not readouts["decomposition"]["identity_holds"]:
        return {"label": "REPRODUCE-INVALID", "stage": None, "role": role, "readings": {}, "void": True,
                "sentences": ["the precondition failed: every readout is a number and the label is REPRODUCE-INVALID"]}
    f_one = readouts["per_n"][str(label_n)]["f_one"]
    label = "FLOOR-MATERIAL" if f_one["rate"] >= kill else "FLOOR-WEAK"
    within = bool(abs(f_one["rate"] - kill) < 2.0 * f_one["se"])
    hw210 = readouts["per_n"][str(full_n)]["half_width"]["median"]
    bar_reading = "BAR-RESOLVED@210" if hw210 < bar else "BAR-UNRESOLVED@210"
    g1 = readouts["per_n"][str(label_n)]["g_one"]["rate"]
    rule_reading = "RULE-LEAKS@30" if g1 > rule_report else "RULE-TIGHT@30"
    stage = None
    if role == "label":
        stage = "NOTE-STANDS" if label == "FLOOR-MATERIAL" else "NOTE-COLLAPSES"
    sentences = [f"f_one at n = {label_n} is {f_one['rate']:.4f} (SE {f_one['se']:.4f}) against the {kill:.2f} threshold: {label}"]
    if within:
        sentences.append("the label sits within Monte Carlo error of its threshold")
    sentences.append(f"the n = {full_n} half-width is {hw210:.4f} against the {bar} bar: {bar_reading}")
    sentences.append(f"g_one at n = {label_n} is {g1:.4f} (the guarded rate is the same number by algebra): {rule_reading}")
    if not readouts.get("guard_identity_holds_everywhere", True):
        sentences.append("the guard identity FAILED on some n: said in words at landing")
    return {"label": label, "within_two_se_of_threshold": within, "stage": stage, "role": role, "void": False,
            "readings": {"bar": bar_reading, "rule": rule_reading}, "sentences": sentences}


# ---------------------------------------------------------------------------
# Run, state file, provenance, conclude-from
# ---------------------------------------------------------------------------

def compute_population(pop: dict, sizes: tuple[int, ...] = SIZES, m_subsets: int = M_SUBSETS,
                       n_boot: int = N_BOOT, reliability_draws: int = RELIABILITY_DRAWS) -> tuple[list[dict], dict, dict]:
    """(state rows, readouts, conclusion) for one population. Rows: one per
    (n, idx) for idx in range(m_subsets) at every n; at n == FULL_N every row
    holds the full set (prompts "all") and its own swap mask."""
    prec = precondition(pop)
    n_total = int(pop["a"]["prompt_idx"].shape[0])
    subsets = draw_subsets(sizes, m_subsets, n_total)
    swaps = draw_swaps(sizes, m_subsets)
    rows: list[dict] = []
    for n in sorted(sizes):
        for k in range(m_subsets):
            idx = subsets[n][0] if n == n_total else subsets[n][k]
            row = {"n": int(n), "idx": int(k), "prompts": "all" if n == n_total else [int(i) for i in idx]}
            row.update(subset_row(pop["a"], pop["b"], idx, swap=swaps[n][k], n_boot=n_boot))
            rows.append(row)
    readouts = readouts_from_rows(pop, rows, sizes=sizes, reliability_draws=reliability_draws, full_n=n_total)
    conclusion = conclude(readouts, prec, pop["role"], full_n=n_total)
    return rows, readouts, conclusion


def _header(pop: dict, constants: dict, n_rows: int) -> dict:
    return {"header": True, "registered": REGISTERED, "population": pop["key"], "role": pop["role"],
            "seeds": list(pop["seeds"]),
            "summary_sha256": {pop["a"]["stem"]: pop["a"]["sha256"], pop["b"]["stem"]: pop["b"]["sha256"]},
            "meta_sha256": {pop["a"]["stem"]: pop["a"]["meta_sha256"], pop["b"]["stem"]: pop["b"]["meta_sha256"]},
            "prompts": pop["prompts_path"], "prompts_sha256": pop["prompts_sha256"],
            "constants": constants, "n_rows": int(n_rows)}


def _constants(sizes, m_subsets, n_boot, reliability_draws) -> dict:
    c = registered_constants()
    c.update({"n_boot": int(n_boot), "sizes": [int(s) for s in sizes], "m_subsets": int(m_subsets),
              "reliability_draws": int(reliability_draws)})
    return c


def _rel(path: Path) -> str:
    """Repo-relative posix path where the file is under ROOT, else the absolute path."""
    try:
        return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(path).resolve().as_posix()


def write_outputs(out: Path, pop: dict, rows: list[dict], readouts: dict, conclusion: dict, prec: dict,
                  constants: dict, smoke: bool, started: float) -> None:
    git_commit, tracked = _git()
    state_path = Path(str(out) + ".state.jsonl")
    header = _header(pop, constants, len(rows))
    _write_lf(state_path, "\n".join(json.dumps(r, sort_keys=True) for r in [header, *rows]) + "\n")
    payload = {
        "registered": REGISTERED,
        "population": pop["key"], "role": pop["role"], "seeds": list(pop["seeds"]), "note": POPULATIONS[pop["key"]]["note"],
        "precondition": prec,
        "readouts": readouts,
        "conclusion": conclusion,
        "n_state_rows": len(rows),
        "provenance": {
            "git_commit": git_commit, "git_status_tracked": tracked,
            "instrument_sha256": _sha(Path(__file__)),
            "summaries": {pop["a"]["stem"]: {"path": _rel(pop["a"]["path"]), "sha256": pop["a"]["sha256"],
                                             "meta_sha256": pop["a"]["meta_sha256"]},
                          pop["b"]["stem"]: {"path": _rel(pop["b"]["path"]), "sha256": pop["b"]["sha256"],
                                             "meta_sha256": pop["b"]["meta_sha256"]}},
            "prompts": {"path": pop["prompts_path"], "sha256": pop["prompts_sha256"]},
            "state_file": state_path.name, "state_sha256": _sha(state_path),
            "constants": constants, "smoke": bool(smoke),
            "blas_threads_env": {v: os.environ.get(v) for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
            "numpy_version": np.__version__, "python_version": platform.python_version(), "platform": platform.platform(),
            "started_unix": started, "runtime_s": time.time() - started,
        },
    }
    _write_lf(out, json.dumps(payload, indent=1) + "\n")


def run(args) -> None:
    started = time.time()
    out = Path(args.out)
    sizes = tuple(int(s) for s in args.sizes.split(",")) if args.sizes else SIZES
    m_subsets = int(args.m_subsets) if args.m_subsets else M_SUBSETS
    n_boot = int(args.n_boot) if args.n_boot else N_BOOT
    smoke = (sizes != SIZES) or (m_subsets != M_SUBSETS) or (n_boot != N_BOOT)
    if _under_results(out):
        if smoke:
            raise SystemExit("a smoke (--sizes / --m-subsets / --n-boot) may not write under results/")
        _, tracked = _git()
        if tracked != "":
            raise SystemExit(f"the tracked tree is not clean — a registered run refuses to write under results/:\n{tracked}")
    pop = load_population(args.population, Path(args.data_root), Path(args.prompts_root))
    rows, readouts, conclusion = compute_population(pop, sizes=sizes, m_subsets=m_subsets, n_boot=n_boot)
    constants = _constants(sizes, m_subsets, n_boot, RELIABILITY_DRAWS)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_outputs(out, pop, rows, readouts, conclusion, precondition(pop), constants, smoke, started)
    print(f"{args.population}: label {conclusion['label']} stage {conclusion['stage']} readings {conclusion['readings']}")
    for s in conclusion["sentences"]:
        print("  " + s)
    print(f"wrote {out} and {out}.state.jsonl ({len(rows)} rows) in {time.time() - started:.1f} s")


def precondition_only(args) -> None:
    """The loader and the PRECONDITION alone (its checks, not R2's identity);
    no cross-seed statistic is computed or printed."""
    pop = load_population(args.population, Path(args.data_root), Path(args.prompts_root))
    prec = precondition(pop)
    print(json.dumps({"population": args.population, **prec}, indent=1))
    if not prec["holds"]:
        raise SystemExit("precondition does not hold")


def _close(a, b, tol: float = 1e-12) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        if math.isnan(a) and math.isnan(b):
            return True
        return abs(float(a) - float(b)) <= tol
    return a == b


def conclude_from(payload_path: Path, data_root: Path = REAL, prompts_root: Path = ROOT) -> dict:
    """Recompute every readout, reading and label from the state file and the
    committed summaries; refuse a payload whose stored numbers differ, a smoke
    payload under results/, unregistered constants under results/, or an
    instrument whose bytes no longer hash to the attested sha."""
    payload_path = Path(payload_path)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    prov = payload["provenance"]
    under = _under_results(payload_path)
    if under and prov.get("smoke"):
        raise SystemExit("a smoke payload under results/ — refusing")
    if prov["instrument_sha256"] != _sha(Path(__file__)):
        raise SystemExit("the instrument's bytes differ from the sha the payload attests — refusing (a frozen "
                         "instrument must not change; compare against the committed bytes)")
    state_path = payload_path.parent / prov["state_file"]
    if _sha(state_path) != prov["state_sha256"]:
        raise SystemExit("the state file's sha differs from the payload's provenance — refusing")
    lines = state_path.read_text(encoding="utf-8").splitlines()
    header, rows = json.loads(lines[0]), [json.loads(x) for x in lines[1:]]
    if not header.get("header") or header["n_rows"] != len(rows) or len(rows) != payload["n_state_rows"]:
        raise SystemExit("state header does not describe the rows — refusing")
    c = header["constants"]
    if c != prov["constants"]:
        raise SystemExit("the state header's constants differ from the payload's — refusing")
    if under and c != registered_constants():
        raise SystemExit(f"unregistered constants under results/ — refusing: {c} != {registered_constants()}")
    pop = load_population(payload["population"], data_root, prompts_root)
    for stem, sha in header["summary_sha256"].items():
        run_sha = pop["a"]["sha256"] if pop["a"]["stem"] == stem else pop["b"]["sha256"]
        if run_sha != sha:
            raise SystemExit(f"{stem}.summary.json on disk is not the one the state file read — refusing")
    if pop["prompts_sha256"] != header["prompts_sha256"]:
        raise SystemExit("the prompt file on disk is not the one the state file read — refusing")
    for stem, sha in header.get("meta_sha256", {}).items():
        run_meta_sha = pop["a"]["meta_sha256"] if pop["a"]["stem"] == stem else pop["b"]["meta_sha256"]
        if run_meta_sha != sha:
            raise SystemExit(f"{stem}.meta.json on disk is not the one the state file read — refusing")
    sizes = tuple(int(s) for s in c["sizes"])
    n_total = int(pop["a"]["prompt_idx"].shape[0])
    # every row re-derived from its stored prompt set and swap mask (the bootstrap recipe is deterministic)
    recomputed = []
    for r in rows:
        idx = np.arange(n_total, dtype=np.int64) if r["prompts"] == "all" else np.array(r["prompts"], dtype=np.int64)
        swap = hex_to_mask(r["swap"]) if "swap" in r else None
        row = {"n": r["n"], "idx": r["idx"], "prompts": r["prompts"]}
        row.update(subset_row(pop["a"], pop["b"], idx, swap=swap, n_boot=int(c["n_boot"]), boot_seed=int(c["boot_seed"])))
        recomputed.append(row)
    if not _close(recomputed, rows):
        raise SystemExit("conclude-from: a state row does not reproduce from its prompt set and swap mask — refusing")
    # the subsets and swaps re-drawn from the generators (determinism of the draw)
    redraw = draw_subsets(sizes, int(c["m_subsets"]), n_total, seed=int(c["subset_seed"]))
    reswap = draw_swaps(sizes, int(c["m_subsets"]), seed=int(c["swap_seed"]))
    for r in rows:
        want = redraw[int(r["n"])][0] if r["prompts"] == "all" else redraw[int(r["n"])][int(r["idx"])]
        got = np.arange(n_total) if r["prompts"] == "all" else np.array(r["prompts"])
        if not np.array_equal(want, got) or ("swap" in r and not np.array_equal(reswap[int(r["n"])][int(r["idx"])], hex_to_mask(r["swap"]))):
            raise SystemExit("conclude-from: the stored subsets or swap masks are not the generators' draws — refusing "
                             f"(numpy {np.__version__} here against {prov.get('numpy_version')} at the run: a Generator "
                             "stream difference across numpy versions is the likely cause; the rows above still reproduce)")
    prec = precondition(pop)
    readouts = readouts_from_rows(pop, rows, sizes=sizes, reliability_draws=int(c["reliability_draws"]), full_n=n_total)
    conclusion = conclude(readouts, prec, pop["role"], full_n=n_total)
    for name, mine, stored in (("precondition", prec, payload["precondition"]), ("readouts", readouts, payload["readouts"]),
                               ("conclusion", conclusion, payload["conclusion"])):
        if not _close(mine, stored):
            raise SystemExit(f"conclude-from: recomputed {name} differs from the payload — refusing")
    print(f"conclude-from: state file reproduces the payload exactly ({len(rows)} rows; label {conclusion['label']}, "
          f"stage {conclusion['stage']}, readings {conclusion['readings']})")
    return {"precondition": prec, "readouts": readouts, "conclusion": conclusion}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--population", choices=sorted(POPULATIONS), default=None)
    ap.add_argument("--out", default=None, help="payload path; the state file is written beside it")
    ap.add_argument("--data-root", default=str(REAL))
    ap.add_argument("--prompts-root", default=str(ROOT))
    ap.add_argument("--precondition-only", action="store_true", help="run the loader and the PRECONDITION only; no statistic")
    ap.add_argument("--conclude-from", default=None, help="recompute a payload's readouts and label from its state file")
    ap.add_argument("--sizes", default=None, help="smoke only: comma-separated prompt counts (refused under results/)")
    ap.add_argument("--m-subsets", default=None, help="smoke only: subsets per n (refused under results/)")
    ap.add_argument("--n-boot", default=None, help="smoke only: bootstrap draws (refused under results/)")
    args = ap.parse_args()
    if args.conclude_from:
        conclude_from(Path(args.conclude_from), Path(args.data_root), Path(args.prompts_root))
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

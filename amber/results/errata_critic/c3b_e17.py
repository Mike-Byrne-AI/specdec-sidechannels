#!/usr/bin/env python3
"""Critic, third batch, SECOND pass, row E17: independent recompute of rows.E17 of results/errata_recompute_3.json
(payload at d1a9f9d), with the escape-cost fields: near-tie masses over all census positions and over the kept
positions, for TinyLlama (results/p2, checked against results/p2_tinyllama_dumps.sha256, and that manifest against
the original results/p2_dumps.sha256) and Llama-3.2-1B-Instruct (results/p2_llama32); the cost-site statuses and
their status under the pinned tolerance. Labels and printed figures are parsed or checked against the claim text at
168efb0. Standalone: no imports from experiments/errata_* or amber. torch blocked.
"""
import sys

sys.modules["torch"] = None
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ARM_OF = {"fp16": "cuda_fp16_b1", "bf16": "cuda_bf16_b1", "int8": "cuda_int8_b1", "nf4": "cuda_nf4_b1"}


def show(c, p):
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{c}:{p}"]).decode("utf-8")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def manifest(path):
    out = {}
    for ln in (REPO / path).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            d_, _, rel = ln.partition("  "); out[rel] = d_
    return out


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def masses(dumps, man_path, thresholds):
    man = manifest(man_path); pre = f"results/{dumps}/"
    used = [r for r in man if r in (pre + "corpus.json", pre + "corpus.npz") or r.startswith(pre + "cpu_fp32/")]
    bad = [r for r in used if sha(REPO / r) != man[r]]
    assert not bad, bad
    cj = json.loads((REPO / pre / "corpus.json").read_text()); L = np.load(REPO / pre / "corpus.npz")["tokens"].shape[1]
    meta = json.loads((REPO / pre / "cpu_fp32/meta.json").read_text()); vv = []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        with np.load(REPO / pre / "cpu_fp32" / f"shard_{s:04d}.npz") as z:
            v = z["val"].astype(np.float64); vv.append(v.reshape(-1, v.shape[-1]))
    v = -np.sort(-np.concatenate(vv), axis=1); g = v[:, 0] - v[:, 1]
    keep = np.ones(g.size, bool); keep[L - 1::L] = False
    return {"corpus_sha256": cj["corpus_sha256"], "manifest_checked": len(used), "positions": int(g.size), "positions_kept": int(keep.sum()),
            "mass_pct": {k: 100 * float((g < t).mean()) for k, t in thresholds.items()},
            "mass_pct_kept_positions": {k: 100 * float((g[keep] < t).mean()) for k, t in thresholds.items()}}


def main():
    row = json.loads((REPO / "results/errata_recompute_3.json").read_text(encoding="utf-8"))["rows"]["E17"]; pay = row["value"]
    F = show("168efb0", "FINDINGS.md").split("\n"); OQ = show("168efb0", "OPEN_QUESTIONS.md").split("\n")
    specs = {"F-5 (FINDINGS.md:40)": (F[39], "results/p2_rank_census.json", "p2", "results/p2_tinyllama_dumps.sha256",
                                      {"0.142": 6.7, "0.465": 19.0, "0.93": 32.6}, {"cuda_fp16_b1": 6.7, "cuda_bf16_b1": 32.6}, 1),
             "F-7 (FINDINGS.md:54)": (F[53], "results/p2_llama32_rank_census.json", "p2_llama32", "results/p2_dumps.sha256",
                                      {"0.142": 8.3, "0.465": 23.2, "0.93": 39.1}, {"cuda_fp16_b1": 8, "cuda_bf16_b1": 39}, 0)}
    printed_in_text = {"F-5": all(x in F[39] for x in ("6.7% of positions at 0.142 (fp16's 2tau)", "19.0% at 0.465", "32.6% at 0.93 (bf16's 2tau)")),
                       "F-7": all(x in F[53] for x in ("P(gap<0.142/0.465/0.93) = 8.3% / 23.2% / 39.1%", "bf16 decoder is ~39% of positions on this model, for fp16 ~8%")),
                       "OQ-2:16": all(x in OQ[15] for x in ("~8% of positions for an fp16 decoder", "~39% for bf16"))}
    oldp2 = manifest("results/p2_dumps.sha256"); newp2 = manifest("results/p2_tinyllama_dumps.sha256")
    mcheck = {"tinyllama_manifest_entries": len(newp2), "identical_to_original_pins": all(oldp2.get(k) == v for k, v in newp2.items())}
    mine = {"sites": {}}; n4 = n2 = n = 0; matches = []; lab = {}; site_st = {}; under = {}
    for site, (line, cpath, dumps, man, pm, pc, nd) in specs.items():
        c = json.loads((REPO / cpath).read_text()); taus = c["calibrated_tau_per_arm"]; rws = {r["arm"]: r for r in c["rows"]}
        out = {"census": cpath, "arms": {}}
        for m in re.finditer(r"(\d+) beyond 2tau=([0-9.]+[0-9])", line):
            before = line[:m.start()]; arm = ARM_OF[max(ARM_OF, key=lambda k: before.rfind(k))]
            cnt, label = int(m.group(1)), float(m.group(2)); tau = taus[arm]; r = rws[arm]; mult = int(round(label / tau))
            n += 1; n4 += mult == 4; n2 += mult == 2; matches.append(cnt == r["flips_beyond_tau"])
            out["arms"][arm] = {"label": label, "tau": tau, "tau_field": r["tau"], "tau_field_is_2tau": abs(r["tau"] - 2 * tau) < 1e-9, "label_over_tau": label / tau,
                                "multiple": mult, "label_is_2tau": mult == 2, "printed_beyond": cnt, "census_beyond_at_2tau": r["flips_beyond_tau"],
                                "count_matches": cnt == r["flips_beyond_tau"], "top1_flips": r["top1_flips"], "flip_gap_max": r["flip_gap_max"],
                                "gap_max_below_2tau": r["flip_gap_max"] < r["tau"], "gap_max_below_label": r["flip_gap_max"] < label}
        lab[f"{site}, labels"] = "CONFIRMED" if all(a["multiple"] == 2 for a in out["arms"].values()) else "CORRECTED"
        two = {a: 2 * taus[a] for a in ("cuda_bf16_b1", "cuda_fp16_b1")}
        ms = masses(dumps, man, {k: float(k) for k in pm} | {f"2tau_{a}": t for a, t in two.items()})
        ec = {"corpus_sha256": ms["corpus_sha256"], "dumps": f"results/{dumps}", "manifest": man, "manifest_checked": ms["manifest_checked"],
              "positions": ms["positions"], "positions_kept": ms["positions_kept"], "mass_pct": ms["mass_pct"], "mass_pct_kept_positions": ms["mass_pct_kept_positions"],
              "problems": [], "printed_mass_pct_at": pm, "instrument_ok": all(round(ms["mass_pct"][k], 1) == v for k, v in pm.items()),
              "instrument_ok_under_pinned_tolerance": all(abs(ms["mass_pct_kept_positions"][k] - v) < 0.05 for k, v in pm.items()),
              "two_tau": two, "mass_pct_at_2tau": {a: ms["mass_pct"][f"2tau_{a}"] for a in two}, "printed_cost_pct": pc}
        ec["cost_differs_at_printed_precision"] = {a: round(ec["mass_pct_at_2tau"][a], nd) != pc[a] for a in two}
        out["escape_cost"] = ec; mine["sites"][site] = out
        dec = "CORRECTED" if any(ec["cost_differs_at_printed_precision"].values()) else "CONFIRMED"
        site_st[f"{site}, escape cost at 2 tau"] = dec if ec["instrument_ok"] else "UNRECOMPUTABLE"
        under[f"{site}, escape cost at 2 tau"] = dec if ec["instrument_ok_under_pinned_tolerance"] else "UNRECOMPUTABLE"
    f7 = mine["sites"]["F-7 (FINDINGS.md:54)"]["escape_cost"]; oqp = {"cuda_fp16_b1": 8, "cuda_bf16_b1": 39}
    oqd = {a: round(f7["mass_pct_at_2tau"][a], 0) != oqp[a] for a in f7["mass_pct_at_2tau"]}
    mine["sites"]["OPEN_QUESTIONS.md:16"] = {"same_dumps_as": "F-7 (FINDINGS.md:54)", "printed_cost_pct": oqp, "mass_pct_at_2tau": f7["mass_pct_at_2tau"],
                                             "cost_differs_at_printed_precision": oqd}
    oqdec = "CORRECTED" if any(oqd.values()) else "CONFIRMED"
    site_st["OPEN_QUESTIONS.md:16 (escape cost at 2 tau)"] = oqdec if f7["instrument_ok"] else "UNRECOMPUTABLE"
    under["OPEN_QUESTIONS.md:16 (escape cost at 2 tau)"] = oqdec if f7["instrument_ok_under_pinned_tolerance"] else "UNRECOMPUTABLE"
    b = json.loads((REPO / "results/p2b_escape_robustness.json").read_text()); tl = json.loads((REPO / "results/p2_llama32_rank_census.json").read_text())["calibrated_tau_per_arm"]
    mine["p2b_thetas_over_llama_tau"] = {str(t): {"over_fp16_tau": t / tl["cuda_fp16_b1"], "over_bf16_tau": t / tl["cuda_bf16_b1"]} for t in b["thetas"] if t > 0}
    mine.update({"n_labels": n, "n_labels_4tau": n4, "n_labels_2tau": n2, "counts_all_match": all(matches), "pinned_rule_sites": ["FINDINGS.md:40", "FINDINGS.md:54"],
                 "code_semantics": pay["code_semantics"]})
    st = {"status": "CONFIRMED" if all(x == "CONFIRMED" for x in lab.values()) else "CORRECTED", "status_by_count": "CONFIRMED" if all(matches) else "CORRECTED",
          "status_by_claim_site": {**lab, **site_st}, "status_under_pinned_tolerance": {**lab, **under}}
    fa, fb = dict(flatten(mine)), dict(flatten(pay)); maxd = 0.0; neq = []
    for k in set(fa) & set(fb):
        x, y = fa[k], fb[k]
        if isinstance(x, (str, bool)) or isinstance(y, (str, bool)) or x is None or y is None:
            if x != y:
                neq.append((k, x, y))
            continue
        maxd = max(maxd, abs(float(x) - float(y)))
    pst = {k: row[k] for k in st}
    out = {"compare_value": {"n": len(set(fa) & set(fb)), "max_abs_diff": maxd, "nonnumeric_unequal": neq, "only_in_payload": sorted(set(fb) - set(fa)),
                             "only_in_mine": sorted(set(fa) - set(fb))},
           "status_mine": st, "status_payload": pst, "status_equal": st == pst, "manifests": mcheck, "printed_figures_in_claim_text": printed_in_text,
           "where": row["where"], "prediction": row["prediction"]}
    text = json.dumps(out, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

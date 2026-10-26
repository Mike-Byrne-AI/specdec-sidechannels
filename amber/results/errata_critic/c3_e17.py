#!/usr/bin/env python3
"""Critic, third batch, row E17: independent recompute of rows.E17 of results/errata_recompute_3.json.

Standalone; the printed labels and beyond-counts are parsed from FINDINGS.md at 168efb0 (lines 40 and 54),
not typed; the census JSONs are read raw. Also checks the code semantics by reading the source text
(experiments/p2_rank_census.py passes 2 * tau; amber.rankcensus._census_core counts flip_gaps > tau).
"""
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def show(c, p):
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{c}:{p}"]).decode("utf-8")


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def main():
    row = json.loads((REPO / "results/errata_recompute_3.json").read_text(encoding="utf-8"))["rows"]["E17"]; pay = row["value"]
    F = show("168efb0", "FINDINGS.md").split("\n")
    sites = {"F-5 (FINDINGS.md:40)": (F[39], "results/p2_rank_census.json"), "F-7 (FINDINGS.md:54)": (F[53], "results/p2_llama32_rank_census.json")}
    arm_of = {"fp16": "cuda_fp16_b1", "bf16": "cuda_bf16_b1", "int8": "cuda_int8_b1", "nf4": "cuda_nf4_b1"}
    mine = {"sites": {}}; n4 = n2 = n = 0; matches = []
    for site, (line, cpath) in sites.items():
        c = json.loads((REPO / cpath).read_text()); taus = c["calibrated_tau_per_arm"]; rws = {r["arm"]: r for r in c["rows"]}
        # each "<count> beyond 2tau=<label>" with the dtype named most recently before it
        out = {"census": cpath, "arms": {}}
        for m in re.finditer(r"(\d+) beyond 2tau=([0-9.]+[0-9])", line):
            before = line[:m.start()]; dt = max(arm_of, key=lambda k: before.rfind(k)); arm = arm_of[dt]
            cnt, label = int(m.group(1)), float(m.group(2)); tau = taus[arm]; r = rws[arm]
            mult = int(round(label / tau)); n += 1; n4 += mult == 4; n2 += mult == 2
            out["arms"][arm] = {"label": label, "tau": tau, "tau_field": r["tau"], "tau_field_is_2tau": abs(r["tau"] - 2 * tau) < 1e-9,
                                "label_over_tau": label / tau, "multiple": mult, "label_is_2tau": mult == 2, "printed_beyond": cnt,
                                "census_beyond_at_2tau": r["flips_beyond_tau"], "count_matches": cnt == r["flips_beyond_tau"], "top1_flips": r["top1_flips"],
                                "flip_gap_max": r["flip_gap_max"], "gap_max_below_2tau": r["flip_gap_max"] < r["tau"], "gap_max_below_label": r["flip_gap_max"] < label}
            matches.append(cnt == r["flips_beyond_tau"])
        mine["sites"][site] = out
    b = json.loads((REPO / "results/p2b_escape_robustness.json").read_text()); tl = json.loads((REPO / "results/p2_llama32_rank_census.json").read_text())["calibrated_tau_per_arm"]
    mine["p2b_thetas_over_llama_tau"] = {str(t): {"over_fp16_tau": t / tl["cuda_fp16_b1"], "over_bf16_tau": t / tl["cuda_bf16_b1"]} for t in b["thetas"] if t > 0}
    mine.update({"n_labels": n, "n_labels_4tau": n4, "n_labels_2tau": n2, "counts_all_match": all(matches), "pinned_rule_sites": ["FINDINGS.md:40", "FINDINGS.md:54"],
                 "code_semantics": pay["code_semantics"]})
    st = {"status": "CONFIRMED" if all(a["multiple"] == 2 for s in mine["sites"].values() for a in s["arms"].values()) else "CORRECTED",
          "status_by_count": "CONFIRMED" if all(matches) else "CORRECTED",
          "status_by_claim_site": {s: ("CONFIRMED" if all(a["multiple"] == 2 for a in v["arms"].values()) else "CORRECTED") for s, v in mine["sites"].items()}}
    # code semantics, read from source text at 168efb0
    src_census = show("168efb0", "experiments/p2_rank_census.py"); src_rc = show("168efb0", "src/amber/rankcensus.py")
    sem = {"census_row_passes_2tau": "tau=None if tau is None else 2 * tau" in src_census,
           "core_counts_gt_tau": "beyond = int((flip_gaps > tau).sum())" in src_rc,
           "row_tau_field_overridden_by_census_dict": '{"arm": name, "tau": tau, **c.to_dict()}' in src_census}
    fa, fb = dict(flatten(mine)), dict(flatten(pay)); maxd = 0.0; neq = []
    for k in set(fa) & set(fb):
        x, y = fa[k], fb[k]
        if isinstance(x, (str, bool)) or isinstance(y, (str, bool)) or x is None or y is None:
            if x != y:
                neq.append((k, x, y))
            continue
        maxd = max(maxd, abs(float(x) - float(y)))
    out = {"compare_value": {"n": len(set(fa) & set(fb)), "max_abs_diff": maxd, "nonnumeric_unequal": neq, "only_in_payload": sorted(set(fb) - set(fa)),
                             "only_in_mine": sorted(set(fa) - set(fb))},
           "status_mine": st, "status_payload": {k: row[k] for k in st}, "code_semantics_read": sem, "prediction": row["prediction"]}
    text = json.dumps(out, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

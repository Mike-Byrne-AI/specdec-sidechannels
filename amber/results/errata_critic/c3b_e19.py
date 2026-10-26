#!/usr/bin/env python3
"""Critic, third batch, SECOND pass, row E19: independent recompute of rows.E19 (payload at d1a9f9d), now with the
post-hoc fields: exact Poisson O/E intervals (my bisection, not scipy), margins, out-of-sample status, the F-10 caveat site.

Standalone: no imports from experiments/errata_* or amber; raw np.load of the dump shards (manifest-checked),
my own canonical ordering, binning, nearest-non-empty fill, exposure matching and hazard sums. torch blocked.
Audit extras: Poisson intervals on O/E, the binning-robustness of status_e15_rule_gap_conditioned, and
whether the primary definition reproduces the second-batch critic's post-hoc p2_quantile20 values exactly.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]; RES = REPO / "results"; OUT = RES / "p2_llama32"; R = 64
ARMS = {"cuda_bf16_b1": "cuda_bf16", "cuda_fp16_b1": "cuda_fp16"}
BINNINGS = (("quantile", 20), ("quantile", 10), ("quantile", 50), ("log", 8), ("log", 16), ("log", 32), ("log", 64))


def jl(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_arm(name):
    meta = json.loads((OUT / name / "meta.json").read_text()); ii, vv = [], []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        with np.load(OUT / name / f"shard_{s:04d}.npz") as z:
            ii.append(z["idx"]); vv.append(z["val"])
    i = np.concatenate(ii); v = np.concatenate(vv).astype(np.float64); k = i.shape[2]; i, v = i.reshape(-1, k), v.reshape(-1, k)
    o1 = np.argsort(i, 1, kind="stable"); i, v = np.take_along_axis(i, o1, 1), np.take_along_axis(v, o1, 1)
    o2 = np.argsort(-v, 1, kind="stable"); return np.take_along_axis(i, o2, 1), np.take_along_axis(v, o2, 1)


def edges_for(kind, n, g):
    if kind == "quantile":
        return np.quantile(g, [k / n for k in range(1, n)])
    lo = g[g > 0].min(); hi = g.max()
    return 10 ** np.linspace(math.log10(lo), math.log10(hi), n + 1)[1:-1]


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def poisson_ci(o, a=0.05):
    """Exact (Garwood) interval by bisection on the Poisson CDF (no scipy)."""
    def cdf(k, m):
        t = math.exp(-m); s = t
        for i in range(1, k + 1):
            t *= m / i; s += t
        return s
    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if o == 0 else solve(lambda m: (1 - cdf(o - 1, m)) - a / 2 < 0 and 1 or -1, 0.0, 10 * o + 10)
    upper = solve(lambda m: cdf(o, m) - a / 2 > 0 and 1 or -1, 0.0, 10 * o + 50)
    return lower, upper


def main():
    row = jl("results/errata_recompute_3.json")["rows"]["E19"]; pay = row["value"]
    man = {}
    for ln in (RES / "p2_dumps.sha256").read_text().splitlines():
        if ln.strip():
            d_, _, rel = ln.partition("  "); man[rel] = d_
    used = [r for r in man if r.startswith("results/p2_llama32/corpus") or any(r.startswith(f"results/p2_llama32/{a}/") for a in ("cpu_fp32", "cuda_bf16_b1", "cuda_fp16_b1"))]
    bad = [r for r in used if sha(REPO / r) != man[r]]; assert not bad, bad
    cmeta = json.loads((OUT / "corpus.json").read_text()); tokens = np.load(OUT / "corpus.npz")["tokens"]; L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False; true = tokens[:, 1:].reshape(-1).astype(np.int64)
    Ei, Ev = load_arm("cpu_fp32"); Ei, Ev = Ei[keep], Ev[keep]
    hit = Ei == true[:, None]; rk = np.where(hit.any(1), hit.argmax(1) + 1, Ei.shape[1] + 1); a_mask = rk == 1
    gd = (Ev[:, 0] - Ev[:, 1])[a_mask]
    b = jl("results/p2b_escape_robustness.json"); p4 = jl("results/p4_real_archive.json")["report"]; e15 = jl("results/errata_recompute_2.json")["rows"]["E15"]["value"]
    recs = {}
    for f in sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz"))):
        with np.load(f) as z:
            recs[int(Path(f).name[4:8])] = (z["flag"].astype(int), z["rank"].astype(np.int64), z["gap"].astype(np.float64))
    mine = {"manifest_checked": len(used), "corpus_sha256": cmeta["corpus_sha256"], "dump_rank1_positions": int(a_mask.sum()),
            "dump_rank1_gap_quantiles": {q: float(np.quantile(gd, float(q))) for q in ("0.01", "0.1", "0.5", "0.9")},
            "binnings": [f"{k}{n}" for k, n in BINNINGS], "primary": "quantile20", "arms": {}, "prediction_sources": pay["prediction_sources"],
            "pinned_rule_sites": ["FINDINGS.md:78"], "prediction_note": pay["prediction_note"]}
    crit = jl("results/errata_critic/c2_e15_gapsens.out.json")
    audit = {}
    okp = []; e15ok = []; oos = []; ro_z = []
    for D, arm in ARMS.items():
        Di, _ = load_arm(D); Di = Di[keep]; dA = (Di[:, 0] != true)[a_mask]
        r0 = [r for r in b["report"]["cpu_fp32"]["decoders"][D] if r["theta"] == 0.0][0]
        assert int(dA.sum()) == r0["desyncs"]["A"]
        pC = np.zeros(R + 2)
        for rr, e in r0["C_desync_by_rank"].items():
            pC[int(rr)] = e["desync"] / e["n"] if e["n"] else 0.0
        rws, nd = [], []
        for f in sorted(glob.glob(str(RES / f"p4/decode_{arm}/shard_*.npz"))):
            with np.load(f) as z:
                rws += z["row"].tolist(); nd += z["n_decoded"].tolist()
        meas = p4["arms"][arm]; OA = int(meas["first_desync_class_counts"].get("A", 0))
        per = {}
        for kind, n in BINNINGS:
            ed = edges_for(kind, n, gd); nb = len(ed) + 1
            bi = np.searchsorted(ed, gd, side="right"); cnt = np.bincount(bi, minlength=nb); des = np.bincount(bi, weights=dA.astype(float), minlength=nb)
            rate = np.where(cnt > 0, des / np.maximum(cnt, 1), np.nan); filled = np.flatnonzero(cnt > 0)

            def haz(g):
                j = np.searchsorted(ed, g, side="right"); h = rate[j].copy(); e = np.isnan(h)
                if e.any():
                    h[e] = rate[filled[np.abs(filled[None, :] - j[e][:, None]).argmin(1)]]
                return h, int(e.sum())
            EA = 0.0; nemp = 0
            for r_, n_ in zip(rws, nd):
                fl, _, g = recs[int(r_)]; ga = g[:n_][fl[:n_] == 0]
                if ga.size:
                    h, e = haz(ga); EA += float(h.sum()); nemp += e
            hs = 0.0; N = 0; surv = []
            for k_ in sorted(recs):
                fl, rr, g = recs[k_]; h = np.zeros(fl.size)
                if (fl == 0).any():
                    h[fl == 0], _ = haz(g[fl == 0])
                c = fl == 1; h[c] = pC[rr[c]]
                hs += float(h.sum()); N += fl.size; surv.append(float(np.prod(1 - h)))
            fail = 1 - float(np.mean(surv))
            cmpd = {"rate_measured_gt_predicted": meas["desyncs_per_token"] > hs / N, "fail_measured_gt_predicted": meas["fail_rate"] > fail}
            per[f"{kind}{n}"] = {"bins": nb, "empty_dump_bins": int((cnt == 0).sum()), "p4_rank1_exposure_in_empty_bins": nemp, "E_A": EA, "O_A": OA,
                                 "z": (OA - EA) / math.sqrt(EA), "one_in": N / hs, "fail_exact": fail, "comparisons": cmpd}
        pr = per["quantile20"]; okp.append(abs(pr["z"]) < 2); e15ok.append(all(pr["comparisons"].values()))
        tag = "bf16" if "bf16" in D else "fp16"
        lo_, hi_ = poisson_ci(OA); cq = crit[D]["by_binning"]["p2_quantile20"]
        cpq = {"compensator_A": cq["compensator_A"], "fail_exact": cq["fail_exact"], "one_in": cq["one_in"]}
        mine["arms"][D] = {"p4_arm": arm, "dump_A_desyncs": int(dA.sum()), "observed_A_first": OA, "rank_only": e15["arms"][D]["compensator_theta0_h4"]["A"],
                           "by_binning": per, "measured": {"one_in": 1 / meas["desyncs_per_token"], "fail_rate": meas["fail_rate"]},
                           "grid_E_A_range": [min(x["E_A"] for x in per.values()), max(x["E_A"] for x in per.values())],
                           "binnings": len(per), "grid_z_range": [min(x["z"] for x in per.values()), max(x["z"] for x in per.values())],
                           "oe_interval_primary": {"high": hi_ / pr["E_A"], "level": 0.95, "low": lo_ / pr["E_A"], "ratio": OA / pr["E_A"]},
                           "margins_primary": {"fail_measured_minus_predicted": meas["fail_rate"] - pr["fail_exact"],
                                               "one_in_predicted_over_measured_minus_1": pr["one_in"] / (1 / meas["desyncs_per_token"]) - 1},
                           "e15_rule_holds_at_binnings": sum(1 for x in per.values() if all(x["comparisons"].values())),
                           "critic_p2_quantile20": cpq,
                           "primary_equals_critic": all(abs(a - b) <= 1e-9 * max(1.0, abs(b)) for a, b in ((pr["E_A"], cpq["compensator_A"]), (pr["fail_exact"], cpq["fail_exact"]), (pr["one_in"], cpq["one_in"])))}
        oos.append(all(abs(v["z"]) < 2 for k, v in per.items() if k != "quantile20")); ro_z.append(abs(e15["arms"][D]["compensator_theta0_h4"]["A"]["z"]) > 2)
        mine[f"{tag}_E_A"] = pr["E_A"]; mine[f"{tag}_z"] = pr["z"]; mine[f"{tag}_one_in"] = pr["one_in"]; mine[f"{tag}_fail_exact"] = pr["fail_exact"]
        lo, hi = poisson_ci(OA)
        audit[D] = {"O_over_E_primary": OA / pr["E_A"], "O_poisson95": [lo, hi], "O_over_E_95": [lo / pr["E_A"], hi / pr["E_A"]],
                    "e15_rule_by_binning": {k: all(v["comparisons"].values()) for k, v in per.items()},
                    "z_range": [min(v["z"] for v in per.values()), max(v["z"] for v in per.values())]}
    crit = jl("results/errata_critic/c2_e15_gapsens.out.json")
    audit["primary_equals_critic_p2_quantile20"] = {D: {"E_A": [mine["arms"][D]["by_binning"]["quantile20"]["E_A"], crit[D]["by_binning"]["p2_quantile20"]["compensator_A"]],
                                                       "fail": [mine["arms"][D]["by_binning"]["quantile20"]["fail_exact"], crit[D]["by_binning"]["p2_quantile20"]["fail_exact"]],
                                                       "one_in": [mine["arms"][D]["by_binning"]["quantile20"]["one_in"], crit[D]["by_binning"]["p2_quantile20"]["one_in"]]} for D in ARMS}
    st = {"status": "CONFIRMED" if all(okp) else "CORRECTED", "status_e15_rule_gap_conditioned": "CONFIRMED" if all(e15ok) else "CORRECTED",
          "status_out_of_sample": "CONFIRMED" if all(oos) else "CORRECTED"}
    st["status_by_claim_site"] = {"FINDINGS.md:78 (F-10 caveat: the per-rank rates are what transfer; the rank-only rank-1 rate does not, E15)": "CORRECTED" if any(ro_z) else "CONFIRMED",
                                  "FINDINGS.md:136 (F-15's E15 bullet: the correction excess is not identified; stands, not conditioned here)": "CONFIRMED"}
    fa, fb = dict(flatten(mine)), dict(flatten(pay)); maxd = 0.0; worst = None; neq = []
    for k in set(fa) & set(fb):
        x, y = fa[k], fb[k]
        if isinstance(x, (str, bool)) or isinstance(y, (str, bool)) or x is None or y is None:
            if x != y:
                neq.append((k, x, y))
            continue
        d = abs(float(x) - float(y))
        if d > maxd:
            maxd, worst = d, k
    out = {"compare_value": {"n": len(set(fa) & set(fb)), "max_abs_diff": maxd, "worst": worst, "nonnumeric_unequal": neq,
                             "only_in_payload": sorted(set(fb) - set(fa)), "only_in_mine": sorted(set(fa) - set(fb))},
           "status_mine": st, "status_payload": {k: row[k] for k in st}, "status_equal": st == {k: row[k] for k in st}, "audit": audit,
           "prediction": row["prediction"], "post_hoc": row.get("post_hoc"), "where": row["where"]}
    text = json.dumps(out, indent=1, default=float) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

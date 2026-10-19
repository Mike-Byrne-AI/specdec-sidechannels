#!/usr/bin/env python3
"""Critic, second batch, SECOND pass, row E15: independent recompute of the regenerated payload
(results/errata_recompute_2.json at 553ffb4), including the post-critic fields.

Standalone: no imports from experiments/errata_* (the code under test); raw np.load of every
source; my own canonical ordering and manifest check for the P2 dumps. torch is blocked.
Compares every leaf of rows.E15 (value, statuses, prediction, where) with my recompute.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
R = 64
ARMS = {"cuda_bf16_b1": "cuda_bf16", "cuda_fp16_b1": "cuda_fp16"}
FLAGS = ("A", "C", "T", "X")
CK = [str(r) for r in range(2, R + 1)]
ALLK = ["1"] + CK + ["X"]


def jl(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def hist(ranks):
    r = np.asarray(ranks, np.int64)
    h = {str(k): int(np.count_nonzero(r == k)) for k in range(1, R + 1)}
    h["X"] = int(np.count_nonzero(r > R)); h["N"] = int(r.size)
    return h


def rates_of(row):
    sc, d, cb = row["symbol_counts"], row["desyncs"], row["C_desync_by_rank"]
    p = {"1": d["A"] / sc["A"] if sc["A"] else None, "X": d["X"] / sc["X"] if sc["X"] else None}
    for r in range(2, R + 1):
        e = cb.get(str(r)); p[str(r)] = (e["desync"] / e["n"]) if e and e["n"] else None
    return p


def setcoded_of(row):
    by = row["setcoded_C"]["by_bucket"]; p = {"1": None, "X": None}
    for r in range(2, R + 1):
        e = by.get(str((r - 1).bit_length() - 1)); p[str(r)] = (e["desync"] / e["n"]) if e and e["n"] else None
    return p


def expect(h, p, ks):
    num = 0.0
    for k in ks:
        if h[k]:
            if p[k] is None:
                raise ValueError(k)
            num += h[k] * p[k]
    return {"N": h["N"], "expected_desyncs": num, "rate": num / h["N"], "one_in": h["N"] / num if num else None}


def hz(p, ks):
    t = np.zeros(R + 2)
    for k in ks:
        if p[k] is not None:
            t[R + 1 if k == "X" else int(k)] = p[k]
    return t


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def cmp(a, b):
    fa, fb = dict(flatten(a)), dict(flatten(b))
    maxd = 0.0; worst = None; neq = []
    for k in set(fa) & set(fb):
        x, y = fa[k], fb[k]
        if x is None or y is None or isinstance(x, (bool, str)) or isinstance(y, (bool, str)):
            if x != y:
                neq.append((k, x, y))
            continue
        d = abs(float(x) - float(y))
        if d > maxd:
            maxd, worst = d, k
    return {"n_compared": len(set(fa) & set(fb)), "only_in_payload": sorted(set(fb) - set(fa)), "only_in_mine": sorted(set(fa) - set(fb)),
            "max_abs_diff": maxd, "worst_key": worst, "nonnumeric_unequal": neq}


def main():
    row15 = jl("results/errata_recompute_2.json")["rows"]["E15"]; pay = row15["value"]
    p4full = jl("results/p4_real_archive.json"); p4 = p4full["report"]; p1 = jl("results/p1_divergence.json")
    b = jl("results/p2b_escape_robustness.json"); dec = b["report"]["cpu_fp32"]["decoders"]; xb3 = b["xb3_wide_gap_check"]
    cens = jl("results/p2_llama32_rank_census.json")
    cr = jl("results/errata_recompute.json")["rows"]["E9"]["value"]["claim_regime_rows"]
    mine = {"claim_regime_rows": cr, "arm_map": ARMS}
    # P1 draft ranks (raw)
    meta = jl("results/p1/draft/meta.json"); parts = []
    for f in sorted(glob.glob(str(RES / "p1/draft/shard_*.npz"))):
        with np.load(f) as z:
            parts.append(z["ranks"].astype(np.int64))
    ranks1 = np.concatenate(parts)
    # P4 streams by row
    recs = {}; tot = {n: 0 for n in FLAGS}; consistent = True
    for f in sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz"))):
        with np.load(f) as z:
            fl = z["flag"].astype(int); rk = z["rank"].astype(np.int64); gp = z["gap"].astype(np.float64)
        for i, n in enumerate(FLAGS):
            tot[n] += int((fl == i).sum())
        consistent &= bool(np.all(rk[fl == 0] == 1) and np.all((rk[fl == 1] >= 2) & (rk[fl == 1] <= R)) and np.all(rk[fl == 3] > R))
        recs[int(Path(f).name[4:8])] = (np.where(fl == 3, R + 1, rk), fl, gp)
    order = sorted(recs)
    reg = {"archives": len(recs), "flag_totals": tot, "positions": int(sum(recs[k][0].size for k in order)),
           "content_tokens_json": p4["content_tokens"], "class_rank_consistent": consistent,
           "sides": {"p2b": {"model": b["model"], "snapshot": cens["provenance"]["cpu_fp32"]["snapshot"], "regime": b["regime"], "census_regime": cens["regime"]},
                     "p4": {"draft": p4full["draft"], "model": p4full["model"], "regime": p4full["regime"]}}}
    reg["ok"] = tot["T"] == 0 and reg["positions"] == p4["content_tokens"] and consistent and len(recs) == p4["archives"]
    mine["regime_check"] = reg
    # cross-check the snapshot against the dump meta (the census provenance is what the payload reads)
    dump_snap = json.loads((RES / "p2_llama32/cpu_fp32/meta.json").read_text())["provenance"]["snapshot"]
    # instrument checks + exposures
    inst = {"N1": int(ranks1.size), "p1_positions": p1["row"]["positions"], "divergence_recomputed": float((ranks1 != 1).mean()),
            "divergence_json": p1["row"]["divergence_rate"], "p1_scoring_dtype": p1.get("dtype"), "shards": {}}
    expo = {}
    for D, arm in ARMS.items():
        first, nd, rws = [], [], []
        for f in sorted(glob.glob(str(RES / f"p4/decode_{arm}/shard_*.npz"))):
            with np.load(f) as z:
                first += z["first"].tolist(); nd += z["n_decoded"].tolist(); rws += z["row"].tolist()
        fails = sum(1 for x in first if x >= 0)
        inst["shards"][arm] = {"archives": len(first), "fails": fails, "n_decoded_total": int(sum(nd)), "rate_from_shards": fails / sum(nd),
                               "rate_json": p4["arms"][arm]["desyncs_per_token"],
                               "n_decoded_minus_first_on_fails": sorted({int(n - f) for n, f in zip(nd, first) if f >= 0}),
                               "rows_in_streams": all(int(r) in recs for r in rws)}
        expo[arm] = [(int(r), int(f), int(n)) for r, f, n in zip(rws, first, nd)]
    inst["ok"] = (inst["N1"] == inst["p1_positions"] and abs(inst["divergence_recomputed"] - inst["divergence_json"]) < 1e-6
                  and all(abs(s["rate_from_shards"] - s["rate_json"]) < 1e-12 and s["rows_in_streams"] for s in inst["shards"].values()))
    mine["instrument_check"] = inst
    h4 = hist(np.concatenate([recs[k][0] for k in order])); h1 = hist(ranks1); Lbar = p4["content_tokens"] / p4["archives"]
    # gap shares: P2 dumps (cpu_fp32, kept, rank_of_true == 1) vs P4 A-flag positions
    man = {}
    for ln in (RES / "p2_dumps.sha256").read_text().splitlines():
        if ln.strip():
            d_, _, rel = ln.partition("  "); man[rel] = d_
    used = [r for r in man if r.startswith("results/p2_llama32/corpus") or r.startswith("results/p2_llama32/cpu_fp32/")]
    bad = [r for r in used if sha(REPO / r) != man[r]]
    thr = {D: xb3[f"cpu_fp32->{D}"]["pair_budget_2tau"] for D in ARMS}
    gs = {"manifest_checked": len(used), "problems": bad, "thresholds_source": "results/p2b_escape_robustness.json xb3_wide_gap_check pair_budget_2tau"}
    cmeta = json.loads((RES / "p2_llama32/corpus.json").read_text())
    tokens = np.load(RES / "p2_llama32/corpus.npz")["tokens"]; L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False
    true = tokens[:, 1:].reshape(-1).astype(np.int64)
    cm = json.loads((RES / "p2_llama32/cpu_fp32/meta.json").read_text()); ii, vv = [], []
    for s in range((cm["n_seqs"] + cm["shard_size"] - 1) // cm["shard_size"]):
        with np.load(RES / f"p2_llama32/cpu_fp32/shard_{s:04d}.npz") as z:
            ii.append(z["idx"]); vv.append(z["val"])
    idx = np.concatenate(ii); val = np.concatenate(vv).astype(np.float64); k = idx.shape[2]; idx, val = idx.reshape(-1, k), val.reshape(-1, k)
    o1 = np.argsort(idx, 1, kind="stable"); idx, val = np.take_along_axis(idx, o1, 1), np.take_along_axis(val, o1, 1)
    o2 = np.argsort(-val, 1, kind="stable"); idx, val = np.take_along_axis(idx, o2, 1), np.take_along_axis(val, o2, 1)
    idx, val = idx[keep], val[keep]
    hit = idx == true[:, None]; rank_true = np.where(hit.any(1), hit.argmax(1) + 1, idx.shape[1] + 1)
    g2 = (val[:, 0] - val[:, 1])[rank_true == 1]
    g4 = np.concatenate([recs[k_][2][recs[k_][1] == 0] for k_ in order])
    gs["p2_dumps_rank1"] = {D: {"threshold": float(t), "share": float((g2 < t).mean()), "n": int(g2.size)} for D, t in thr.items()}
    gs["corpus"] = {k_: cmeta[k_] for k_ in ("model_id", "text_path", "text_sha256", "corpus_sha256")}
    gs["p4_archives_rank1"] = {D: {"threshold": float(t), "share": float((g4 < t).mean()), "n": int(g4.size)} for D, t in thr.items()}
    mine.update({"h4": h4, "h1": h1, "Lbar": Lbar, "gap_shares": gs, "arms": {}})
    reversals = []; claim_ok = []; class_ok = {"A": [], "C": [], "all": []}
    for D, arm in ARMS.items():
        rws = {f"{r['theta']}/{r['m']}": r for r in dec[D]}; p0 = rates_of(rws["0.0/2"]); pcr = rates_of(rws[cr[0]])
        c_only = {kk: {"h4": expect(h4, rates_of(r), CK), "h1": expect(h1, rates_of(r), CK)} for kk, r in rws.items()}
        a4 = expect(h4, p0, ALLK); a1 = expect(h1, p0, ALLK); sc = expect(h1, setcoded_of(rws[cr[0]]), CK)

        def fexact(p, ks):
            t = hz(p, ks); surv = np.array([np.prod(1 - t[np.minimum(recs[k_][0], R + 1)]) for k_ in order])
            return {"archives": int(surv.size), "expected_fails": float((1 - surv).sum()), "fail_rate": float(1 - surv.mean())}
        fe = {"all_theta0_h4": fexact(p0, ALLK), "c_only_claim_regime_h4": fexact(pcr, CK)}
        fp = {"all_theta0_h4": 1 - math.exp(-Lbar * a4["rate"]), "c_only_claim_regime_h1": 1 - math.exp(-Lbar * c_only[cr[0]]["h1"]["rate"])}
        m = p4["arms"][arm]
        cmp_ = {"rate_measured_gt_predicted": m["desyncs_per_token"] > a4["rate"], "fail_measured_gt_predicted": m["fail_rate"] > fe["all_theta0_h4"]["fail_rate"]}
        reversals += [f"{D}: {kk}" for kk, ok in cmp_.items() if not ok]
        tag = "bf16" if "bf16" in D else "fp16"
        oi = c_only[cr[0]]["h1"]["one_in"]; claim_ok.append(int(math.floor(oi / 10 + 0.5)) * 10 == {"bf16": 170, "fp16": 1070}[tag])
        # compensator over the decoded positions (theta-0 per-rank rates; X has rate 0)
        t0 = hz(p0, ALLK); E = {"A": 0.0, "C": 0.0, "X": 0.0}
        for r_, f_, n_ in expo[arm]:
            s = np.minimum(recs[r_][0][:n_], R + 1); h = t0[s]
            E["A"] += float(h[s == 1].sum()); E["C"] += float(h[(s >= 2) & (s <= R)].sum()); E["X"] += float(h[s == R + 1].sum())
        O = {"A": 0, "C": 0, "X": 0}
        for kk, v in m["first_desync_class_counts"].items():
            O["C" if kk.startswith("C") else kk] += int(v)
        comp = {}
        for c in ("A", "C", "X"):
            comp[c] = {"observed": float(O[c]), "expected": E[c], "ratio": O[c] / E[c] if E[c] else None, "z": (O[c] - E[c]) / math.sqrt(E[c]) if E[c] else None}
        Ot, Et = float(sum(O.values())), sum(E.values())
        comp["all"] = {"observed": Ot, "expected": Et, "ratio": Ot / Et, "z": (Ot - Et) / math.sqrt(Et)}
        comp["predicted_first_desync_shares"] = {c: E[c] / Et for c in ("A", "C", "X")}
        for c in class_ok:
            class_ok[c].append(comp[c]["ratio"] is not None and comp[c]["ratio"] > 1)
        mine["arms"][D] = {"p4_arm": arm, "c_only": c_only, "all_theta0": {"h4": a4, "h1": a1}, "setcoded_c_only_claim_regime_h1": sc,
                           "fail_exact": fe, "fail_poisson": fp, "comparisons": cmp_, "compensator_theta0_h4": comp,
                           "measured": {"desyncs_per_token": m["desyncs_per_token"], "one_in": 1 / m["desyncs_per_token"], "fail_rate": m["fail_rate"],
                                        "archives": m["archives"], "byte_exact": m["byte_exact"], "first_desync_class_counts": m["first_desync_class_counts"],
                                        "definition": pay["arms"][D]["measured"]["definition"]}}
        mine[f"{tag}_all_theta0_one_in"] = a4["one_in"]; mine[f"{tag}_all_theta0_one_in_h1"] = a1["one_in"]
        mine[f"{tag}_measured_one_in"] = 1 / m["desyncs_per_token"]; mine[f"{tag}_claim_regime_one_in"] = oi
        mine[f"{tag}_fail_poisson_claim_regime_pct"] = 100 * fp["c_only_claim_regime_h1"]
    mine["reversals"] = reversals
    mine["prediction_sources"] = pay["prediction_sources"]          # labels, checked by hand against REPORT.md and the protocol
    st = lambda ok: "CONFIRMED" if ok else "CORRECTED"  # noqa: E731
    my_status = {"status": st(not reversals), "status_in_claim_regime": st(all(claim_ok)),
                 "status_by_class": {c: st(all(v)) for c, v in class_ok.items()}}
    my_status["status_by_claim_site"] = {
        "FINDINGS.md:72 (F-10 headline, in its own regime)": my_status["status_in_claim_regime"],
        "FINDINGS.md:76 (item (4), in its own regime)": my_status["status_in_claim_regime"],
        "docs/BLUEPRINT.md:57 (in its own regime)": my_status["status_in_claim_regime"],
        "FINDINGS.md:85 (F-11, corrections more fragile: class C over the decoded positions)": my_status["status_by_class"]["C"]}
    pay_status = {k: row15[k] for k in my_status}
    out = {"compare_value": cmp(mine, pay), "compare_status": cmp(my_status, pay_status), "status_mine": my_status,
           "dump_meta_snapshot_equals_census_snapshot": dump_snap == reg["sides"]["p2b"]["snapshot"],
           "gap_share_manifest_bad": bad, "prediction": row15["prediction"], "where": row15["where"]}
    Path(__file__).with_suffix(".out.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("compare_value", "compare_status", "dump_meta_snapshot_equals_census_snapshot")}, indent=1, default=float))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Critic, second batch, THIRD pass, row E16: independent recompute of the regenerated payload
(results/errata_recompute_2.json at 3cec4df): claim scope over all five arms, pinned_rule_sites.

Standalone: no imports from experiments/errata_* and no amber imports; raw np.load of the dump
shards, my own canonical ordering, alignment and manifest check. torch is blocked.
Compares every leaf of rows.E16 (value and status fields) with my recompute; also checks the
top-1 claim sites against ALL arms' slot-0 counts, not only cuda_fp32_b1's.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"; OUT = RES / "p2_llama32"; R = 64
SCORED = ("cuda_fp32_b1", "cuda_fp32_b8"); INFO = ("cuda_fp16_b1", "cuda_bf16_b1", "cuda_bf16_b8")
ARMS = ("cpu_fp32",) + SCORED + INFO
BUCKETS = ((0, 0), (1, 1), (2, 7), (8, 15), (16, 63))
DBUCKETS = ((0, 0), (1, 7), (8, 15), (16, 63))


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
    i = np.concatenate(ii); v = np.concatenate(vv).astype(np.float64); k = i.shape[2]
    i, v = i.reshape(-1, k), v.reshape(-1, k)
    o1 = np.argsort(i, 1, kind="stable"); i, v = np.take_along_axis(i, o1, 1), np.take_along_axis(v, o1, 1)
    o2 = np.argsort(-v, 1, kind="stable"); return np.take_along_axis(i, o2, 1), np.take_along_axis(v, o2, 1)


def align(E_i, D_i, D_v):
    """For every encoder slot (full width), the decoder value of the same token (nan if absent): sort + searchsorted."""
    s = np.argsort(D_i, 1); Ds = np.take_along_axis(D_i, s, 1); Dvs = np.take_along_axis(D_v, s, 1)
    loc = np.empty(E_i.shape, np.int64)
    for t in range(E_i.shape[0]):
        loc[t] = np.searchsorted(Ds[t], E_i[t])
    loc = np.minimum(loc, E_i.shape[1] - 1); ok = np.take_along_axis(Ds, loc, 1) == E_i
    return np.where(ok, np.take_along_axis(Dvs, loc, 1), np.nan)


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
    row16 = jl("results/errata_recompute_2.json")["rows"]["E16"]; pay = row16["value"]
    man = {}
    for ln in (RES / "p2_dumps.sha256").read_text().splitlines():
        if ln.strip():
            d_, _, rel = ln.partition("  "); man[rel] = d_
    used = [r for r in man if r.startswith("results/p2_llama32/corpus") or any(r.startswith(f"results/p2_llama32/{a}/") for a in ARMS)]
    bad = [r for r in used if sha(REPO / r) != man[r]]
    assert not bad, bad
    cmeta = json.loads((OUT / "corpus.json").read_text()); tokens = np.load(OUT / "corpus.npz")["tokens"]; L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False
    arms = {}
    for a in ARMS:
        i, v = load_arm(a); arms[a] = (i[keep], v[keep])
    b = jl("results/p2b_escape_robustness.json"); xb3 = b["xb3_wide_gap_check"]
    cens = jl("results/p2_llama32_rank_census.json"); census = cens["calibrated_tau_per_arm"]
    src_rc = (REPO / "src/amber/rankcensus.py").read_text(encoding="utf-8")
    qdef = float(re.search(r"def calibrate_tau_topk\([^)]*quantile: float = ([0-9.]+)\)", src_rc).group(1))
    E_i, E_v = arms["cpu_fp32"]; n = E_i.shape[0]; g12 = E_v[:, 0] - E_v[:, 1]
    mine = {"manifest_checked": len(used), "corpus_sha256": cmeta["corpus_sha256"], "n": int(n), "dump_width": int(E_i.shape[1]), "R": R, "tau_cpu_fp32": 0.0,
            "encoder_top2_gap_quantiles": {"p01": float(np.quantile(g12, 0.01)), "p50": float(np.median(g12))},
            "tau_definition": {"function": "amber.rankcensus.calibrate_tau_topk", "topk_used": cens["topk_used"], "quantile": qdef,
                               "note": pay["tau_definition"]["note"]}, "arms": {}}

    def prefix_key(p):
        s, o = p // (L - 1), p % (L - 1)
        return tokens[s, :o + 1].tobytes()
    slot0_all = {}
    for D in SCORED + INFO:
        D_i, D_v = arms[D]
        neq = E_i[:, :R] != D_i[:, :R]; pos = np.flatnonzero(neq.any(1)); j = neq[pos].argmax(1); tok = D_i[pos, j]
        hit = E_i[pos] == tok[:, None]; found = hit.any(1); k = np.where(found, hit.argmax(1), -1)
        g = np.full(pos.size, np.nan); g[found] = np.abs(E_v[pos[found], j[found]] - E_v[pos[found], k[found]]); gf = g[found]
        key = f"cpu_fp32->{D}"; two_tau = 2 * census[D] if D in census else None
        if key in xb3:
            budget = xb3[key]["pair_budget_2tau"]; src = "results/p2b_escape_robustness.json xb3_wide_gap_check pair_budget_2tau (the XB-3 check's own budget)"
        else:
            budget = two_tau; src = "2 * calibrated_tau_per_arm from results/p2_llama32_rank_census.json (census-derived proxy; P2b's TAU has no entry)"
        bk = {}
        for lo, hi in BUCKETS:
            sel = (j >= lo) & (j <= hi); gs = g[sel & found]
            bk[str(lo) if lo == hi else f"{lo}-{hi}"] = {"n": int(sel.sum()), "max_g": float(gs.max()) if gs.size else None, "above_budget": int((gs > budget).sum())}
        slot0_all[D] = bk["0"]
        aligned = align(E_i, D_i, D_v)                      # decoder value of each encoder slot's token (full width)
        above = np.flatnonzero(found & (np.nan_to_num(g, nan=-1.0) > budget)); events = []
        for ii in above:
            p, jj, kk = int(pos[ii]), int(j[ii]), int(k[ii])
            dj = float(aligned[p, jj] - E_v[p, jj]); dk = float(aligned[p, kk] - E_v[p, kk])
            events.append({"position": p, "sequence": p // (L - 1), "offset": p % (L - 1), "slot_j": jj, "encoder_slot_k": kk, "g": float(g[ii]),
                           "enc_gap_top1_top2": float(E_v[p, 0] - E_v[p, 1]), "dec_delta_token_j": dj, "dec_delta_token_k": dk, "pair_drift": dk - dj})
        q = lambda x: float(np.quantile(gf, x))  # noqa: E731
        s = {"n_diff": int(pos.size), "n_absent": int((~found).sum()), "n_nonadjacent": int((found & (k != j + 1)).sum()),
             "g_quantiles": {"min": q(0), "p50": q(.5), "p90": q(.9), "p99": q(.99), "max": q(1)}, "by_slot_bucket": bk, "budget": budget,
             "count_above_budget": int((gf > budget).sum()), "two_tau_census": two_tau, "count_above_two_tau_census": int((gf > two_tau).sum()),
             "budget_source": src, "calibrated_tau_census": census.get(D), "events_above_budget": events,
             "distinct_contexts": len({prefix_key(int(p)) for p in pos}), "distinct_contexts_above_budget": len({prefix_key(int(pos[ii])) for ii in above}),
             "role": "scored" if D in SCORED else "informational"}
        if D in SCORED:
            delta = aligned[:, :R] - E_v[:, :R]; ad = np.abs(delta); by = {}
            for lo, hi in DBUCKETS:
                x = ad[:, lo:hi + 1]; x = x[np.isfinite(x)]
                by[str(lo) if lo == hi else f"{lo}-{hi}"] = {"n": int(x.size), "q": float(np.quantile(x, 0.999))}
            pdft = np.abs(delta[:, :-1] - delta[:, 1:]); fin = np.isfinite(pdft)
            s["drift"] = {"quantile": 0.999, "abs_delta_q_by_slot_bucket": by, "absent": int((~np.isfinite(delta)).sum()), "budget": float(budget),
                          "adjacent_pairs": int(fin.sum()), "adjacent_pairs_drift_above_budget": int((pdft[fin] > budget).sum())}
        mine["arms"][D] = s
    for D, tag in (("cuda_fp32_b1", "b1"), ("cuda_fp32_b8", "b8")):
        s = mine["arms"][D]
        mine[f"{tag}_count_above_budget"] = s["count_above_budget"]; mine[f"{tag}_n_diff"] = s["n_diff"]
        mine[f"{tag}_max_g"] = s["g_quantiles"]["max"]; mine[f"{tag}_n_nonadjacent"] = s["n_nonadjacent"]
    mine["pinned_rule_sites"] = ["FINDINGS.md:114", "OPEN_QUESTIONS.md:15", "README.md:50"]
    st = lambda ok: "CONFIRMED" if ok else "CORRECTED"  # noqa: E731
    my_status = {"status": st(mine["b1_count_above_budget"] == 0),
                 "status_by_arm": {D: st(mine["arms"][D]["count_above_budget"] == 0) for D in SCORED},
                 "status_at_claim_scope": {D: st(mine["arms"][D]["by_slot_bucket"]["0"]["above_budget"] == 0) for D in SCORED + INFO}}
    sall = st(all(v == "CONFIRMED" for v in my_status["status_at_claim_scope"].values()))
    my_status["status_by_claim_site"] = {"FINDINGS.md:76 (F-10 item (1), A desyncs at theta 0: slot 0, every arm)": sall,
                                         "FINDINGS.md:55 (F-7 caveats, top-1 flips: slot 0, every arm)": sall,
                                         "OPEN_QUESTIONS.md:16 (top-1 flips: slot 0, every arm)": sall,
                                         "FINDINGS.md:114, OPEN_QUESTIONS.md:15, README.md:50 (F-14's E8a sentence, every order difference a near-tie: all depths)": my_status["status"]}
    pay_status = {k: row16[k] for k in my_status}
    out = {"manifest": {"checked": len(used), "bad": bad}, "compare_value": cmp(mine, pay), "compare_status": cmp(my_status, pay_status),
           "status_mine": my_status, "slot0_all_arms": slot0_all,
           "slot0_all_arms_status": st(all(v["above_budget"] == 0 for v in slot0_all.values())), "where": row16["where"], "prediction": row16["prediction"]}
    Path(__file__).with_suffix(".out.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("manifest", "compare_value", "compare_status", "slot0_all_arms", "slot0_all_arms_status")}, indent=1, default=float))


if __name__ == "__main__":
    main()

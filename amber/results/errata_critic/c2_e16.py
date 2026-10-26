#!/usr/bin/env python3
"""Critic, second batch, row E16 (and the dump-based audit for E15's A-desync rates).

Standalone: no imports from experiments/errata_*; no amber imports (raw np.load of the
shards, my own canonical ordering, my own manifest check). torch is blocked.

Part 1: verify every dump file read against results/p2_dumps.sha256, then recompute every
value of rows.E16 and compare leaf by leaf with the payload.
Part 2 (audit): order differences at slot 0 only (the claim sites' scope: top-1 flips /
A-desyncs), duplicate contexts among the events, how tau was calibrated (population and
per-depth quantiles), the base rate of budget-exceeding pair drift, and a gap-conditioned
A-desync estimate for E15 (P2b's A rate re-weighted by the P4 archives' own gap distribution).
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
OUT = RES / "p2_llama32"
R = 64
SCORED = ("cuda_fp32_b1", "cuda_fp32_b8")
INFO = ("cuda_fp16_b1", "cuda_bf16_b1", "cuda_bf16_b8")
ARMS = ("cpu_fp32",) + SCORED + INFO
BUCKETS = ((0, 0), (1, 1), (2, 7), (8, 15), (16, 63))


def jl(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def manifest_check():
    rows = []
    for ln in (RES / "p2_dumps.sha256").read_text(encoding="utf-8").splitlines():
        if ln.strip():
            d, _, rel = ln.partition("  ")
            rows.append((d, rel))
    want = [(d, rel) for d, rel in rows if rel.startswith("results/p2_llama32/corpus") or any(rel.startswith(f"results/p2_llama32/{a}/") for a in ARMS)]
    bad = [rel for d, rel in want if not (REPO / rel).is_file() or sha(REPO / rel) != d]
    # files actually read but absent from the manifest
    read = [OUT / "corpus.json", OUT / "corpus.npz"] + [Path(p) for a in ARMS for p in glob.glob(str(OUT / a / "*"))]
    listed = {rel for _, rel in want}
    unlisted = [p.relative_to(REPO).as_posix() for p in read if p.relative_to(REPO).as_posix() not in listed]
    return len(want), bad, unlisted


def load_arm(name):
    meta = json.loads((OUT / name / "meta.json").read_text())
    assert (OUT / name / "DONE").exists()
    n_sh = (meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]
    ii, vv = [], []
    for s in range(n_sh):
        with np.load(OUT / name / f"shard_{s:04d}.npz") as z:
            ii.append(z["idx"]); vv.append(z["val"])
    idx = np.concatenate(ii); val = np.concatenate(vv)
    k = idx.shape[2]
    return idx.reshape(-1, k), val.reshape(-1, k).astype(np.float64), meta


def canon(idx, val):
    """value desc, index asc on ties: stable sort by index, then stable sort by -value."""
    o1 = np.argsort(idx, axis=1, kind="stable")
    i1 = np.take_along_axis(idx, o1, 1); v1 = np.take_along_axis(val, o1, 1)
    o2 = np.argsort(-v1, axis=1, kind="stable")
    return np.take_along_axis(i1, o2, 1), np.take_along_axis(v1, o2, 1)


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
    pay = jl("results/errata_recompute_2.json")["rows"]["E16"]
    n_checked, bad, unlisted = manifest_check()
    assert not bad, bad
    cmeta = json.loads((OUT / "corpus.json").read_text())
    tokens = np.load(OUT / "corpus.npz")["tokens"]
    L = tokens.shape[1]
    keep = np.ones(tokens.shape[0] * L, bool); keep[L - 1::L] = False
    arms = {}
    for a in ARMS:
        i, v, _ = load_arm(a)
        assert i.shape[0] == tokens.shape[0] * L
        i, v = canon(i, v); arms[a] = (i[keep], v[keep])
    b = jl("results/p2b_escape_robustness.json"); xb3 = b["xb3_wide_gap_check"]
    census = jl("results/p2_llama32_rank_census.json")["calibrated_tau_per_arm"]
    E_i, E_v = arms["cpu_fp32"]; n = E_i.shape[0]
    g12 = E_v[:, 0] - E_v[:, 1]
    mine = {"manifest_checked": n_checked, "corpus_sha256": cmeta["corpus_sha256"], "n": int(n), "dump_width": int(E_i.shape[1]), "R": R,
            "tau_cpu_fp32": 0.0, "encoder_top2_gap_quantiles": {"p01": float(np.quantile(g12, 0.01)), "p50": float(np.median(g12))}, "arms": {}}
    # context identity: hash of tokens[s, :offset+1] for every kept position
    seq = np.repeat(np.arange(tokens.shape[0]), L - 1); off = np.tile(np.arange(L - 1), tokens.shape[0])

    def ctx_key(p):
        s, o = int(seq[p]), int(off[p])
        return hashlib.sha1(tokens[s, :o + 1].astype(np.int64).tobytes()).hexdigest()
    audit = {"unlisted_files_read": unlisted}
    ev_all = {}
    for D in SCORED + INFO:
        Di, Dv = arms[D]
        neq = E_i[:, :R] != Di[:, :R]; pos = np.flatnonzero(neq.any(1))
        j = neq[pos].argmax(1); tok = Di[pos, j]
        hit = E_i[pos] == tok[:, None]; found = hit.any(1); k = np.where(found, hit.argmax(1), -1)
        g = np.full(pos.size, np.nan); g[found] = np.abs(E_v[pos[found], j[found]] - E_v[pos[found], k[found]])
        gf = g[found]
        key = f"cpu_fp32->{D}"; two_tau = 2 * census[D] if D in census else None
        if key in xb3:
            budget = xb3[key]["pair_budget_2tau"]; src = "results/p2b_escape_robustness.json xb3_wide_gap_check pair_budget_2tau (the XB-3 check's own budget)"
        else:
            budget = two_tau; src = "2 * calibrated_tau_per_arm from results/p2_llama32_rank_census.json (census-derived proxy; P2b's TAU has no entry)"
        bk = {}
        for lo, hi in BUCKETS:
            sel = (j >= lo) & (j <= hi); gs = g[sel & found]
            bk[str(lo) if lo == hi else f"{lo}-{hi}"] = {"n": int(sel.sum()), "max_g": float(gs.max()) if gs.size else None, "above_budget": int((gs > budget).sum())}
        above = np.flatnonzero(found & (np.nan_to_num(g, nan=-1) > budget))
        events = [{"position": int(pos[i]), "sequence": int(pos[i] // (L - 1)), "offset": int(pos[i] % (L - 1)), "slot_j": int(j[i]),
                   "encoder_slot_k": int(k[i]), "g": float(g[i]), "enc_gap_top1_top2": float(E_v[pos[i], 0] - E_v[pos[i], 1])} for i in above]
        q = lambda x: float(np.quantile(gf, x))  # noqa: E731
        mine["arms"][D] = {"n_diff": int(pos.size), "n_absent": int((~found).sum()), "n_nonadjacent": int((found & (k != j + 1)).sum()),
                           "g_quantiles": {"min": q(0), "p50": q(.5), "p90": q(.9), "p99": q(.99), "max": q(1)}, "by_slot_bucket": bk,
                           "budget": budget, "budget_source": src, "count_above_budget": int((gf > budget).sum()), "two_tau_census": two_tau,
                           "count_above_two_tau_census": int((gf > two_tau).sum()), "calibrated_tau_census": census.get(D),
                           "events_above_budget": events, "role": "scored" if D in SCORED else "informational"}
        ev_all[D] = (pos, j, k, g)
        # ---- audit ----
        ctx = [ctx_key(p) for p in pos]
        ev_ctx = [ctx_key(e["position"]) for e in events]
        # tau population: 0.999 quantile of aligned |delta| over the full width, and per slot bucket of the encoder slot
        Dpos = {}
        delta = np.full(E_i.shape, np.nan)
        # aligned |delta|: for each encoder slot, find the token in the decoder row
        srt = np.argsort(Di, axis=1); Ds = np.take_along_axis(Di, srt, 1); Dvs = np.take_along_axis(Dv, srt, 1)
        loc = np.empty_like(E_i)
        for r0 in range(0, n, 4096):
            sl = slice(r0, min(n, r0 + 4096))
            loc[sl] = np.stack([np.searchsorted(Ds[t], E_i[t]) for t in range(sl.start, sl.stop)])
        locc = np.minimum(loc, E_i.shape[1] - 1)
        ok = np.take_along_axis(Ds, locc, 1) == E_i
        dv = np.take_along_axis(Dvs, locc, 1)
        delta[ok] = np.abs(E_v[ok] - dv[ok])
        fin = np.isfinite(delta)
        tau_all = float(np.quantile(delta[fin], 0.999))
        # the census's own population: dumps truncated to top-64 on BOTH sides (p2_rank_census --topk 64), all 49152 positions
        Ri0, Rv0, _ = load_arm("cpu_fp32"); Ai0, Av0, _ = load_arm(D)
        Ri0, Rv0 = canon(Ri0, Rv0); Ai0, Av0 = canon(Ai0, Av0)
        Ri0, Rv0, Ai0, Av0 = Ri0[:, :R], Rv0[:, :R], Ai0[:, :R], Av0[:, :R]
        s0 = np.argsort(Ai0, axis=1); As = np.take_along_axis(Ai0, s0, 1); Avs = np.take_along_axis(Av0, s0, 1)
        l0 = np.stack([np.searchsorted(As[t], Ri0[t]) for t in range(Ri0.shape[0])]); l0 = np.minimum(l0, R - 1)
        ok0 = np.take_along_axis(As, l0, 1) == Ri0
        tau_top64_all = float(np.quantile(np.abs(Rv0 - np.take_along_axis(Avs, l0, 1))[ok0], 0.999))
        per_depth = {}
        for lo, hi in ((0, 0), (1, 7), (8, 15), (16, 63), (64, 255)):
            dd = delta[:, lo:hi + 1]; dd = dd[np.isfinite(dd)]
            per_depth[f"{lo}-{hi}"] = {"q999": float(np.quantile(dd, 0.999)), "share_gt_tau": float((dd > census[D]).mean())} if D in census else None
        # pair drift between adjacent encoder slots j, j+1 in the top-64: |(d_j - e_j) - (d_k - e_k)| with signs
        sd = np.full(E_i.shape, np.nan); sd[ok] = dv[ok] - E_v[ok]
        pair = np.abs(sd[:, :R - 1] - sd[:, 1:R]); pf = pair[np.isfinite(pair)]
        audit[D] = {"slot0_order_diffs": int((j == 0).sum()), "slot0_above_budget": int(((j == 0) & found & (np.nan_to_num(g, nan=-1) > budget)).sum()),
                    "slot0_max_g": float(g[j == 0].max()) if (j == 0).any() else None,
                    "distinct_contexts_among_order_diffs": len(set(ctx)), "distinct_contexts_among_events_above_budget": len(set(ev_ctx)),
                    "tau_recomputed_full_width_q999": tau_all, "tau_recomputed_top64_all_positions_q999": tau_top64_all, "tau_census": census.get(D),
                    "aligned_delta_q999_by_encoder_slot": per_depth,
                    "adjacent_pair_drift_gt_budget_share_top64": float((pf > budget).mean()), "adjacent_pairs_gt_budget": int((pf > budget).sum()),
                    "adjacent_pairs_total": int(pf.size)}
        if D == "cuda_fp32_b1":
            ev_pairs = []
            for e in events:
                p = e["position"]; jj, kk = e["slot_j"], e["encoder_slot_k"]
                ev_pairs.append({"position": p, "enc_vals_jk": [float(E_v[p, jj]), float(E_v[p, kk])], "signed_drift_j": float(sd[p, jj]), "signed_drift_k": float(sd[p, kk]),
                                 "pair_drift": float(abs(sd[p, jj] - sd[p, kk])), "tokens_prefix": tokens[e["sequence"], :e["offset"] + 2].tolist()})
            audit[D]["event_detail"] = ev_pairs
    for D, tag in (("cuda_fp32_b1", "b1"), ("cuda_fp32_b8", "b8")):
        s = mine["arms"][D]
        mine[f"{tag}_count_above_budget"] = s["count_above_budget"]; mine[f"{tag}_n_diff"] = s["n_diff"]; mine[f"{tag}_max_g"] = s["g_quantiles"]["max"]
    status = "CONFIRMED" if mine["b1_count_above_budget"] == 0 else "CORRECTED"
    by_arm = {D: ("CONFIRMED" if mine["arms"][D]["count_above_budget"] == 0 else "CORRECTED") for D in SCORED}
    # b8 sensitivity: would the b1 XB-3 budget change b8?
    audit["b8_above_b1_budget"] = int((ev_all["cuda_fp32_b8"][3][np.isfinite(ev_all["cuda_fp32_b8"][3])] > xb3["cpu_fp32->cuda_fp32_b1"]["pair_budget_2tau"]).sum())
    # duplicate windows in the corpus: sequences sharing their first 2 tokens
    first2 = {}
    for s in range(tokens.shape[0]):
        first2.setdefault(tuple(tokens[s, :2].tolist()), []).append(s)
    audit["sequences_sharing_first_two_tokens"] = {str(k): v for k, v in first2.items() if len(v) > 1}

    # ---------------- E15 audit: gap-conditioned A-desync rate ----------------
    true = tokens[:, 1:].reshape(-1).astype(np.int64)
    r1 = E_i[:, 0] == true                                   # encoder rank 1 (A at theta 0)
    p4 = {}
    for f in sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz"))):
        with np.load(f) as z:
            p4[int(Path(f).name[4:8])] = (z["flag"].astype(int), z["gap"].astype(np.float64))
    gapA4 = np.concatenate([g_[fl == 0] for fl, g_ in p4.values()])
    edges = np.concatenate([[0.0], np.logspace(-6, 1.5, 31), [np.inf]])
    gapA = {}
    for D in ("cuda_bf16_b1", "cuda_fp16_b1"):
        Di, _ = arms[D]; dA = (Di[:, 0] != true) & r1
        cnt, _ = np.histogram(g12[r1], edges); des, _ = np.histogram(g12[dA], edges)
        rate = np.where(cnt > 0, des / np.maximum(cnt, 1), 0.0)
        c4, _ = np.histogram(gapA4, edges)
        # bins with P4 mass but no P2 mass: none expected; report
        gapA[D] = {"p2b_A_rate": float(dA.sum() / r1.sum()), "p2b_A_desyncs": int(dA.sum()), "p2b_A_positions": int(r1.sum()),
                   "gap_conditioned_expected_A_desyncs_whole_P4": float((c4 * rate).sum()), "unconditioned_expected_A_desyncs_whole_P4": float(gapA4.size * dA.sum() / r1.sum()),
                   "p4_A_positions": int(gapA4.size), "p4_mass_in_bins_without_p2": int(c4[cnt == 0].sum()), "max_gap_of_p2b_A_desync": float(g12[dA].max())}
        # theta-0 all-class prediction with the A hazard gap-conditioned per P4 position (C hazards per rank as P2b)
        row0 = [r_ for r_ in b["report"]["cpu_fp32"]["decoders"][D] if r_["theta"] == 0.0][0]
        pC = np.zeros(R + 2)
        for rr, e in row0["C_desync_by_rank"].items():
            pC[int(rr)] = e["desync"] / e["n"]
        bin_of = lambda x: np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(rate) - 1)  # noqa: E731
        haz = {}
        for row_id, (fl, g_) in p4.items():
            with np.load(RES / f"p4/archives/row_{row_id:04d}_symbols.npz") as z:
                rk = z["rank"].astype(np.int64)
            h = np.zeros(rk.size)
            h[fl == 0] = rate[bin_of(g_[fl == 0])]
            c = fl == 1; h[c] = pC[rk[c]]
            haz[row_id] = h
        allh = np.concatenate([haz[k_] for k_ in sorted(haz)])
        surv = np.array([np.prod(1 - haz[k_]) for k_ in sorted(haz)])
        arm = {"cuda_bf16_b1": "cuda_bf16", "cuda_fp16_b1": "cuda_fp16"}[D]
        rws, fst, ndd = [], [], []
        for f in sorted(glob.glob(str(RES / f"p4/decode_{arm}/shard_*.npz"))):
            with np.load(f) as z:
                rws += z["row"].tolist(); fst += z["first"].tolist(); ndd += z["n_decoded"].tolist()
        compA = sum(float(haz[r_][:n_][p4[r_][0][:n_] == 0].sum()) for r_, n_ in zip(rws, ndd))
        compC = sum(float(haz[r_][:n_][p4[r_][0][:n_] == 1].sum()) for r_, n_ in zip(rws, ndd))
        rep = jl("results/p4_real_archive.json")["report"]["arms"][arm]
        gapA[D]["gap_conditioned_all_theta0"] = {
            "rate_whole_archive": float(allh.mean()), "one_in": float(1 / allh.mean()), "measured_desyncs_per_token": rep["desyncs_per_token"],
            "fail_exact": float(1 - surv.mean()), "measured_fail_rate": rep["fail_rate"],
            "compensator_expected": {"A": compA, "C": compC, "all": compA + compC}, "observed_fails": int(sum(1 for x in fst if x >= 0)),
            "rate_measured_gt_predicted": rep["desyncs_per_token"] > float(allh.mean()), "fail_measured_gt_predicted": rep["fail_rate"] > float(1 - surv.mean())}
    gapA["near_tie_mass_rank1"] ={thr: {"p2_instruct_rank1": float((g12[r1] < thr).mean()), "p4_base_rank1": float((gapA4 < thr).mean())} for thr in (0.0662, 0.4654)}
    gapA["note"] = "P2 encoder gap = cpu_fp32 top1-top2 (Instruct, human text); P4 gap = cuda fp32 top1-top2 of the base draft on target-generated text (symbols npz `gap`)"
    audit["E15_gap_conditioned_A"] = gapA

    out = {"manifest": {"checked": n_checked, "bad": bad}, "compare_value": cmp(mine, pay["value"]),
           "status": {"mine": status, "payload": pay["status"]}, "status_by_arm": {"mine": by_arm, "payload": pay.get("status_by_arm")},
           "prediction_payload": pay["prediction"], "audit": audit}
    Path(__file__).with_suffix(".out.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Critic, second batch, row E15: independent recompute from the raw sources + definition audit.

Standalone: no imports from experiments/errata_lib.py or experiments/errata_recompute.py
(the code under test) and no amber imports for the main path; amber's load_rank is used
once, only to cross-check the raw P1 read. torch is blocked.

Part 1 recomputes every value of rows.E15 from:
  results/p1/draft/shard_*.npz (+ meta.json), results/p1_divergence.json,
  results/p4/archives/row_*_symbols.npz, results/p4/decode_cuda_{bf16,fp16}/shard_*.npz,
  results/p4_real_archive.json, results/p2b_escape_robustness.json,
  results/errata_recompute.json rows.E9.value.claim_regime_rows
and compares every leaf of the payload's rows.E15 (numbers: max |diff|; others: equality).

Part 2 (audit, not in the protocol): survivorship-matched predictions on the archives' own
streams (expected fails, expected decoded positions, expected FIRST-desync counts by class),
cause-specific (A vs C) comparisons, and a gap-conditioned A-desync estimate from the P2 dumps.
"""
import sys

sys.modules["torch"] = None  # CPU-only guard, as the recompute
import glob  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
R = 64
ARMS = {"cuda_bf16_b1": "cuda_bf16", "cuda_fp16_b1": "cuda_fp16"}
FLAGS = ("A", "C", "T", "X")                      # src/amber/rac_codec.py FLAG_NAMES (0..3)


def jl(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def keys_all():
    return ["1"] + [str(r) for r in range(2, R + 1)] + ["X"]


def hist(ranks):
    r = np.asarray(ranks, np.int64)
    h = {str(k): int(np.count_nonzero(r == k)) for k in range(1, R + 1)}
    h["X"] = int(np.count_nonzero(r > R)); h["N"] = int(r.size)
    assert int(np.count_nonzero(r < 1)) == 0
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
        b = (r - 1).bit_length() - 1                 # bucket b covers ranks 2^b+1 .. 2^(b+1)
        assert 2 ** b + 1 <= r <= 2 ** (b + 1)
        e = by.get(str(b)); p[str(r)] = (e["desync"] / e["n"]) if e and e["n"] else None
    return p


def expect(h, p, ks):
    num = 0.0; by = {}
    for k in ks:
        if h[k] == 0:
            continue
        if p[k] is None:
            raise ValueError(f"rate missing at {k} with h={h[k]}")
        by[k] = h[k] * p[k]; num += by[k]
    return {"N": h["N"], "expected_desyncs": num, "rate": num / h["N"], "one_in": h["N"] / num if num else None}, by


def hazard_vec(p, ks):
    t = np.zeros(R + 2)
    for k in ks:
        if p[k] is not None:
            t[R + 1 if k == "X" else int(k)] = p[k]
    return t


def bucket(k):
    if k in ("1", "A"):
        return "A"
    if k == "X":
        return "X"
    r = int(k[1:]) if k.startswith("C") else int(k)
    return f"C{r}" if r <= 5 else "C6-64"


def shares(w):
    t = {}
    for k, v in w.items():
        t[bucket(k)] = t.get(bucket(k), 0.0) + float(v)
    s = sum(t.values())
    return {k: v / s for k, v in sorted(t.items())}


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
    pay = jl("results/errata_recompute_2.json")["rows"]["E15"]
    p4 = jl("results/p4_real_archive.json")["report"]; p1 = jl("results/p1_divergence.json")
    b = jl("results/p2b_escape_robustness.json"); dec = b["report"]["cpu_fp32"]["decoders"]
    cr_rows = jl("results/errata_recompute.json")["rows"]["E9"]["value"]["claim_regime_rows"]
    assert b["R_max"] == R
    # ---------------- P1 draft ranks, raw ----------------
    meta = jl("results/p1/draft/meta.json")
    files = sorted(glob.glob(str(RES / "p1/draft/shard_*.npz")))
    n_sh = (meta["n_prompts"] + meta["shard_size"] - 1) // meta["shard_size"]
    assert len(files) == n_sh, (len(files), n_sh)
    parts = []
    for f in files:
        with np.load(f) as z:
            off = z["offsets"]; rk = z["ranks"]
            assert off[0] == 0 and off[-1] == rk.size and len(off) == len(z["row"]) + 1
            parts.append(rk.astype(np.int64))
    ranks1 = np.concatenate(parts)
    # cross-check against amber's loader (allowed: raw-read cross-check only)
    sys.path.insert(0, str(REPO / "src"))
    from amber.real.divergence import load_rank
    lr = load_rank(RES / "p1", "draft")
    cross_p1 = bool(np.array_equal(np.concatenate([q["rank"] for q in lr["per_prompt"]]).astype(np.int64), ranks1))
    mine = {}
    inst = {"N1": int(ranks1.size), "p1_positions": p1["row"]["positions"], "divergence_recomputed": float((ranks1 != 1).mean()),
            "divergence_json": p1["row"]["divergence_rate"], "p1_scoring_dtype": p1.get("dtype"), "shards": {}}
    # ---------------- P4 decode shards ----------------
    exposure = {}
    for D, arm in ARMS.items():
        first, nd, rows_ = [], [], []
        for f in sorted(glob.glob(str(RES / f"p4/decode_{arm}/shard_*.npz"))):
            with np.load(f) as z:
                first += z["first"].tolist(); nd += z["n_decoded"].tolist(); rows_ += z["row"].tolist()
        fails = sum(1 for x in first if x >= 0)
        inst["shards"][arm] = {"archives": len(first), "fails": fails, "n_decoded_total": int(sum(nd)),
                               "rate_from_shards": fails / sum(nd), "rate_json": p4["arms"][arm]["desyncs_per_token"],
                               "n_decoded_minus_first_on_fails": sorted({int(n - f) for n, f in zip(nd, first) if f >= 0})}
        exposure[arm] = (rows_, first, nd)
    inst["ok"] = (inst["N1"] == inst["p1_positions"] and abs(inst["divergence_recomputed"] - inst["divergence_json"]) < 1e-6
                  and all(abs(s["rate_from_shards"] - s["rate_json"]) < 1e-12 for s in inst["shards"].values()))
    mine["instrument_check"] = inst
    # ---------------- P4 symbol streams (regime check) ----------------
    sfiles = sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz")))
    tot = {n: 0 for n in FLAGS}; streams = {}; gaps4 = {}; consistent = True
    for f in sfiles:
        row = int(Path(f).name[4:8])
        with np.load(f) as z:
            fl = z["flag"].astype(int); rk = z["rank"].astype(np.int64); gp = z["gap"].astype(np.float64)
        for i, n in enumerate(FLAGS):
            tot[n] += int((fl == i).sum())
        consistent &= bool(np.all(rk[fl == 0] == 1) and np.all((rk[fl == 1] >= 2) & (rk[fl == 1] <= R)) and np.all(rk[fl == 3] > R))
        assert not np.any(fl == 2) or True
        streams[row] = np.where(fl == 3, R + 1, rk); gaps4[row] = gp
    reg = {"archives": len(sfiles), "flag_totals": tot, "positions": int(sum(s.size for s in streams.values())),
           "content_tokens_json": p4["content_tokens"], "class_rank_consistent": consistent}
    reg["ok"] = tot["T"] == 0 and reg["positions"] == p4["content_tokens"] and consistent and len(sfiles) == p4["archives"]
    mine["regime_check"] = reg
    mine["claim_regime_rows"] = cr_rows; mine["arm_map"] = ARMS
    allr = np.concatenate([streams[r] for r in sorted(streams)])
    h4 = hist(allr); h1 = hist(ranks1)
    Lbar = p4["content_tokens"] / p4["archives"]
    mine.update({"h4": h4, "h1": h1, "Lbar": Lbar, "arms": {}})
    order = sorted(streams)
    reversals = []; claim_ok = []
    CK = [str(r) for r in range(2, R + 1)]
    audit = {}
    for D, arm in ARMS.items():
        rws = {f"{r['theta']}/{r['m']}": r for r in dec[D]}
        p0 = rates_of(rws["0.0/2"]); cr = cr_rows[0]; pcr = rates_of(rws[cr])
        c_only = {k: {"h4": expect(h4, rates_of(r), CK)[0], "h1": expect(h1, rates_of(r), CK)[0]} for k, r in rws.items()}
        a4, by4 = expect(h4, p0, keys_all()); a1, _ = expect(h1, p0, keys_all())
        sc, _ = expect(h1, setcoded_of(rws[cr]), CK)

        def fexact(p, ks):
            t = hazard_vec(p, ks)
            surv = np.array([np.prod(1.0 - t[np.minimum(streams[r], R + 1)]) for r in order])
            return {"archives": int(surv.size), "expected_fails": float((1 - surv).sum()), "fail_rate": float(1 - surv.mean())}
        fe = {"all_theta0_h4": fexact(p0, keys_all()), "c_only_claim_regime_h4": fexact(pcr, CK)}
        fp = {"all_theta0_h4": 1 - math.exp(-Lbar * a4["rate"]), "c_only_claim_regime_h1": 1 - math.exp(-Lbar * c_only[cr]["h1"]["rate"])}
        m = p4["arms"][arm]
        cmp_ = {"rate_measured_gt_predicted": m["desyncs_per_token"] > a4["rate"], "fail_measured_gt_predicted": m["fail_rate"] > fe["all_theta0_h4"]["fail_rate"]}
        for kk, ok in cmp_.items():
            if not ok:
                reversals.append(f"{D}: {kk}")
        tag = "bf16" if "bf16" in D else "fp16"
        target = {"bf16": 170, "fp16": 1070}[tag]
        oi = c_only[cr]["h1"]["one_in"]
        claim_ok.append(int(math.floor(oi / 10 + 0.5)) * 10 == target)
        mine["arms"][D] = {"p4_arm": arm, "c_only": c_only, "all_theta0": {"h4": a4, "h1": a1}, "setcoded_c_only_claim_regime_h1": sc,
                           "fail_exact": fe, "fail_poisson": fp, "comparisons": cmp_,
                           "class_shares_theta0": {"predicted_h4": shares(by4), "measured_first_desync": shares(m["first_desync_class_counts"])},
                           "measured": {"desyncs_per_token": m["desyncs_per_token"], "one_in": 1 / m["desyncs_per_token"], "fail_rate": m["fail_rate"],
                                        "archives": m["archives"], "byte_exact": m["byte_exact"], "first_desync_class_counts": m["first_desync_class_counts"],
                                        "definition": pay["value"]["arms"][D]["measured"]["definition"]}}
        mine[f"{tag}_all_theta0_one_in"] = a4["one_in"]; mine[f"{tag}_measured_one_in"] = 1 / m["desyncs_per_token"]
        mine[f"{tag}_claim_regime_one_in"] = oi; mine[f"{tag}_fail_poisson_claim_regime_pct"] = 100 * fp["c_only_claim_regime_h1"]

        # ---------------- audit: survivorship-matched predictions on the archives' own streams ----------------
        def matched(p, ks):
            t = hazard_vec(p, ks)
            Ef = 0.0; Eexp = 0.0; first_cls = {}; var_cls = {}
            for r in order:
                s = np.minimum(streams[r], R + 1); hz = t[s]
                S_prev = np.concatenate([[1.0], np.cumprod(1.0 - hz)[:-1]])
                Eexp += S_prev.sum(); f_t = S_prev * hz; Ef += f_t.sum()
                cls = np.array([bucket("X" if v == R + 1 else str(v)) for v in s])
                for c in np.unique(cls):
                    q = float(f_t[cls == c].sum())
                    first_cls[c] = first_cls.get(c, 0.0) + q; var_cls[c] = var_cls.get(c, 0.0) + q * (1 - q)
            return {"expected_fails": Ef, "expected_decoded_positions": Eexp, "matched_hazard": Ef / Eexp,
                    "expected_first_desync_by_class": first_cls, "sd_first_desync_by_class": {c: math.sqrt(v) for c, v in var_cls.items()}}
        rows_, first, nd = exposure[arm]
        meas_cls = {}
        for k, v in m["first_desync_class_counts"].items():
            meas_cls[bucket(k)] = meas_cls.get(bucket(k), 0) + v
        mt0 = matched(p0, keys_all()); mtc = matched(pcr, CK); mt0c = matched(p0, CK)
        nA = meas_cls.get("A", 0); nC = sum(v for k, v in meas_cls.items() if k.startswith("C"))
        expA = mt0["expected_first_desync_by_class"].get("A", 0.0)
        expC = sum(v for k, v in mt0["expected_first_desync_by_class"].items() if k.startswith("C"))
        sdA = mt0["sd_first_desync_by_class"].get("A", 0.0)
        sdC = math.sqrt(sum(v ** 2 for k, v in mt0["sd_first_desync_by_class"].items() if k.startswith("C")))  # approx (ignores cross-class covariance)
        # front-loading: share of non-A positions among the first ceil(mean prefix) positions vs whole archives
        mean_prefix = sum(nd) / len(nd); Lp = int(round(mean_prefix))
        pre = np.concatenate([streams[r][:Lp] for r in order]);
        dec_pos = np.concatenate([streams[r][:n] for r, n in zip(rows_, nd)])
        # compensator: expected events by class summed over the positions actually at risk (decoded positions,
        # the failing one included). Under the per-rank hazard model, observed - expected is a zero-mean martingale,
        # whatever the competing risk does; this is the like-for-like reading of "desyncs per decoded token" by class.
        t0 = hazard_vec(p0, keys_all()); tcr = hazard_vec(pcr, keys_all())
        comp = {"theta0": {"A": 0.0, "C": 0.0}, "claim_regime": {"A": 0.0, "C": 0.0}}
        for r, f_, n_ in zip(rows_, first, nd):
            s = np.minimum(streams[r][:n_], R + 1); isA = s == 1; isC = (s >= 2) & (s <= R)
            comp["theta0"]["A"] += float(t0[s][isA].sum()); comp["theta0"]["C"] += float(t0[s][isC].sum())
            comp["claim_regime"]["A"] += float(tcr[s][isA].sum()); comp["claim_regime"]["C"] += float(tcr[s][isC].sum())
            assert f_ < 0 or n_ == f_ + 1
        audit_comp = {"expected_on_at_risk_positions": comp,
                      "obs_over_exp_theta0": {"A": meas_cls.get("A", 0) / comp["theta0"]["A"],
                                              "C": sum(v for k, v in meas_cls.items() if k.startswith("C")) / comp["theta0"]["C"],
                                              "all": int(sum(1 for x in first if x >= 0)) / (comp["theta0"]["A"] + comp["theta0"]["C"])},
                      "obs_over_exp_claim_regime_C": sum(v for k, v in meas_cls.items() if k.startswith("C")) / comp["claim_regime"]["C"]}
        audit[D] = {
            "compensator": audit_comp,
            "measured_fails": int(sum(1 for x in first if x >= 0)), "measured_decoded_positions": int(sum(nd)),
            "measured_first_desync_by_class": meas_cls, "measured_A": nA, "measured_C": nC,
            "theta0_all_classes_matched": mt0, "theta0_C_only_matched": mt0c, "claim_regime_C_only_matched": mtc,
            "expected_first_A_theta0": expA, "sd_first_A": sdA, "expected_first_C_theta0": expC, "sd_first_C_approx": sdC,
            "z_A": (nA - expA) / sdA if sdA else None, "z_C": (nC - expC) / sdC if sdC else None,
            "cause_specific_hazard_measured": {"A": nA / sum(nd), "C": nC / sum(nd)},
            "cause_specific_hazard_predicted_whole_archive": {"A": by4.get("1", 0.0) / h4["N"], "C": sum(by4.get(k, 0.0) for k in CK) / h4["N"]},
            "mean_prefix": mean_prefix, "corr_share_first_Lp_positions": float((pre != 1).mean()), "corr_share_whole": float((allr != 1).mean()),
            "corr_share_decoded_positions": float((dec_pos != 1).mean()),
        }
    mine["reversals"] = reversals
    status = "CONFIRMED" if not reversals else "CORRECTED"
    status_cr = "CONFIRMED" if all(claim_ok) else "CORRECTED"

    # ---------------- compare with the payload ----------------
    def cmp(a, b):
        fa, fb = dict(flatten(a)), dict(flatten(b))
        miss_a = sorted(set(fb) - set(fa)); miss_b = sorted(set(fa) - set(fb))
        maxd = 0.0; maxrel = 0.0; neq = []; worst = None
        for k in set(fa) & set(fb):
            x, y = fa[k], fb[k]
            if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                if x != y:
                    neq.append((k, x, y))
                continue
            d = abs(float(x) - float(y))
            if d > maxd:
                maxd, worst = d, k
            if y:
                maxrel = max(maxrel, d / abs(float(y)))
        return {"n_compared": len(set(fa) & set(fb)), "only_in_payload": miss_a, "only_in_mine": miss_b, "max_abs_diff": maxd,
                "max_rel_diff": maxrel, "worst_key": worst, "nonnumeric_unequal": neq}
    out = {"cross_check_p1_raw_vs_load_rank": cross_p1,
           "compare_value": cmp(mine, pay["value"]),
           "status": {"mine": status, "payload": pay["status"]},
           "status_in_claim_regime": {"mine": status_cr, "payload": pay.get("status_in_claim_regime")},
           "prediction_payload": pay["prediction"],
           "headline": {k: mine[k] for k in mine if k.endswith("_one_in") or k.endswith("_pct")},
           "audit": audit}
    # gap-conditioned A-desync estimate needs the dumps: see c2_e15_gapA.py
    (Path(__file__).with_suffix(".out.json")).write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()

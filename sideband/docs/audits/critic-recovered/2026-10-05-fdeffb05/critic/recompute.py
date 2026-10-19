import json, sys, hashlib, math
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/<user>/Desktop/Research/sideband")
REAL = ROOT / "results" / "real"
POPS = {"k3": ("k3_verdict_arm1", "k3_verdict_s1_arm1", "data/prompts_k3_verdict.jsonl"),
        "oq15": ("oq15c_verdict_arm1", "oq15c_verdict_s3_arm1", "data/prompts_oq15_verdict.jsonl")}
BAR, ADV = 0.062, 3.191969887076537 - 3.1322448979591835
SIZES, M = (30, 42, 84, 126, 210), 1000
FAMS = ("instruct", "story", "summarize")

def run(stem):
    s = json.loads((REAL / (stem + ".summary.json")).read_text(encoding="utf-8"))
    pp = sorted(s["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    return {k: np.array([p[f] for p in pp], float) for k, f in (("e", "n_emitted"), ("b", "n_blocks"), ("d", "n_drafted"))}

def boot(ea, ba, eb, bb, n_boot=2000, seed=0):
    n = ea.shape[0]
    idx = np.random.default_rng(seed).integers(0, n, size=(n_boot, n))
    d = ea[idx].sum(1) / ba[idx].sum(1) - eb[idx].sum(1) / bb[idx].sum(1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return ea.sum() / ba.sum() - eb.sum() / bb.sum(), lo, hi

def se1(c, mm):
    f = c / mm
    return math.sqrt(f * (1 - f) / mm) / 2

def conv(o):
    if isinstance(o, dict):
        return {str(k): conv(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [conv(v) for v in o]
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o

def readouts_for(key):
    sa, sb, pf = POPS[key]
    A, B = run(sa), run(sb)
    fam = np.array([json.loads(l)["family"] for l in (ROOT / pf).read_text(encoding="utf-8").splitlines() if l.strip()])
    ya, yb = A["e"] / A["b"], B["e"] / B["b"]
    R = {}
    R["r"] = np.corrcoef(ya, yb)[0, 1]
    idx = np.random.default_rng(0).integers(0, 210, size=(2000, 210))
    rs = np.array([np.corrcoef(ya[i], yb[i])[0, 1] for i in idx])
    R["r_lo"], R["r_hi"] = np.percentile(rs, [2.5, 97.5])
    R["sd"] = np.concatenate([ya, yb]).std()
    R["mad"] = np.abs(ya - yb).mean()
    R["r_fam"] = {f: np.corrcoef(ya[fam == f], yb[fam == f])[0, 1] for f in FAMS}
    yac, ybc = ya.copy(), yb.copy()
    for f in FAMS:
        m = fam == f
        yac[m] -= ya[m].mean()
        ybc[m] -= yb[m].mean()
    R["r_within"] = np.corrcoef(yac, ybc)[0, 1]
    Y = np.stack([ya, yb], 1)
    g = Y.mean()
    yp = Y.mean(1)
    sst = ((Y - g) ** 2).sum()
    sss = ((Y - yp[:, None]) ** 2).sum()
    ssp = sum(2 * ((yp[fam == f] - Y[fam == f].mean()) ** 2).sum() for f in FAMS)
    ssf = sum(140 * (Y[fam == f].mean() - g) ** 2 for f in FAMS)
    R["ss_var"] = (sst / 420, sss / 420, ssp / 420, ssf / 420)
    R["ss_share"] = (sss / sst, ssp / sst, ssf / sst)
    R["ss_ident"] = abs(sst - sss - ssp - ssf) / sst
    ms_s, ms_p, ms_f = sss / 210, ssp / 207, ssf / 2
    mom = (ms_s, (ms_p - ms_s) / 2, (ms_f - ms_p) / 140)
    R["mom"] = mom
    R["mom_share"] = tuple(v / sum(mom) for v in mom)
    R["fam_means"] = {f: Y[fam == f].mean() for f in FAMS}
    R["fam_means_ab"] = {f: (ya[fam == f].mean(), yb[fam == f].mean()) for f in FAMS}
    R["drafted_gamma"] = bool(np.array_equal(A["d"], 4 * A["b"]) and np.array_equal(B["d"], 4 * B["b"]))
    return A, B, R

def rows_for(key, A, B, R):
    lines = (REAL / ("noise_floor_" + key + ".json.state.jsonl")).read_text(encoding="utf-8").splitlines()
    header, rows = json.loads(lines[0]), [json.loads(x) for x in lines[1:]]
    gen1 = np.random.default_rng(1)
    gen2 = np.random.default_rng(2)
    subs, masks = {}, {}
    for n in SIZES:
        if n == 210:
            subs[n] = [np.arange(210)] * M
        else:
            subs[n] = [np.sort(gen1.choice(210, size=n, replace=False)) for _ in range(M)]
    for n in SIZES:
        masks[n] = gen2.integers(0, 2, size=(M, n)).astype(bool)
    disc, nrows, sub_ok, mask_ok = 0.0, 0, True, True
    byn = {n: [] for n in SIZES}
    for row in rows:
        n, k = row["n"], row["idx"]
        ix = subs[n][k]
        got = np.arange(210) if row["prompts"] == "all" else np.array(row["prompts"])
        sub_ok = sub_ok and np.array_equal(ix, got)
        nbits, hx = row["swap"].split(":")
        bits = bin(int(hx, 16))[2:].zfill(int(nbits))[-int(nbits):]
        mk = np.array([c == "1" for c in bits])
        mask_ok = mask_ok and np.array_equal(mk, masks[n][k])
        d, lo, hi = boot(A["e"][ix], A["b"][ix], B["e"][ix], B["b"][ix])
        ea2 = np.where(mk, B["e"][ix], A["e"][ix])
        ba2 = np.where(mk, B["b"][ix], A["b"][ix])
        eb2 = np.where(mk, A["e"][ix], B["e"][ix])
        bb2 = np.where(mk, A["b"][ix], B["b"][ix])
        d2, lo2, hi2 = boot(ea2, ba2, eb2, bb2)
        dpa = A["d"][ix].sum() / A["e"][ix].sum()
        dpb = B["d"][ix].sum() / B["e"][ix].sum()
        pairs = ((d, row["delta"]), (lo, row["lo"]), (hi, row["hi"]), ((hi - lo) / 2, row["hw"]), (d2, row["delta_sw"]),
                 (lo2, row["lo_sw"]), (hi2, row["hi_sw"]), ((hi2 - lo2) / 2, row["hw_sw"]), (dpa, row["dpe_a"]), (dpb, row["dpe_b"]))
        disc = max(disc, max(abs(a - b) for a, b in pairs))
        byn[n].append(dict(d=d, l=lo, h=hi, hw=(hi - lo) / 2, d2=d2, l2=lo2, h2=hi2, hw2=(hi2 - lo2) / 2, dpa=dpa, dpb=dpb, k=k))
        nrows += 1
    R["row_maxdisc"], R["nrows"] = disc, nrows
    R["subsets_regenerated"], R["masks_regenerated"] = bool(sub_ok), bool(mask_ok)
    R["header_constants"] = header["constants"]
    return byn

def rates_for(byn, R):
    per = {}
    for n in SIZES:
        rs_ = byn[n]
        prim = [x for x in rs_ if x["k"] == 0] if n == 210 else rs_
        d = np.array([x["d"] for x in prim])
        lo = np.array([x["l"] for x in prim])
        hi = np.array([x["h"] for x in prim])
        dpa = np.array([x["dpa"] for x in prim])
        dpb = np.array([x["dpb"] for x in prim])
        hw = np.array([x["hw"] for x in prim])
        m = len(prim)
        fp, fm = int((d >= BAR).sum()), int((d <= -BAR).sum())
        gp, gm = int(((lo > 0) & (d >= BAR)).sum()), int(((hi < 0) & (d <= -BAR)).sum())
        gpg = int(((lo > 0) & (d >= BAR) & (dpa <= dpb + 0.01)).sum())
        gmg = int(((hi < 0) & (d <= -BAR) & (dpb <= dpa + 0.01)).sum())
        d2 = np.array([x["d2"] for x in rs_])
        lo2 = np.array([x["l2"] for x in rs_])
        hi2 = np.array([x["h2"] for x in rs_])
        hw2 = np.array([x["hw2"] for x in rs_])
        ms_ = len(rs_)
        sfp, sfm = int((d2 >= BAR).sum()), int((d2 <= -BAR).sum())
        sgp, sgm = int(((lo2 > 0) & (d2 >= BAR)).sum()), int(((hi2 < 0) & (d2 <= -BAR)).sum())
        per[n] = dict(m=m, n_fp=fp, n_fm=fm, n_gp=gp, n_gm=gm, f_plus=fp / m, f_minus=fm / m, f_two=(fp + fm) / m,
                      f_one=(fp + fm) / (2 * m), f_one_se=se1(fp + fm, m), g_one=(gp + gm) / (2 * m), g_one_se=se1(gp + gm, m),
                      g_guard_equal=(gpg == gp and gmg == gm),
                      hw_med=float(np.median(hw)), hw_mean=float(hw.mean()), hw_p05=float(np.percentile(hw, 5)), hw_p95=float(np.percentile(hw, 95)),
                      d_mean=float(d.mean()), d_sd=float(d.std()),
                      sw_m=ms_, sw_n_fp=sfp, sw_n_fm=sfm, sw_f_one=(sfp + sfm) / (2 * ms_), sw_f_one_se=se1(sfp + sfm, ms_),
                      sw_f_plus=sfp / ms_, sw_f_minus=sfm / ms_,
                      sw_g_one=(sgp + sgm) / (2 * ms_), sw_g_one_se=se1(sgp + sgm, ms_), sw_hw_med=float(np.median(hw2)),
                      sw_d_mean=float(d2.mean()), sw_d_sd=float(d2.std()))
    R["per"] = per
    d30 = np.array([x["d"] for x in byn[30]])
    R["r6"] = float((np.concatenate([d30, -d30]) >= ADV).mean())
    d30s = np.array([x["d2"] for x in byn[30]])
    R["r6_sw"] = float((np.concatenate([d30s, -d30s]) >= ADV).mean())
    R["full_delta"], R["full_lo"], R["full_hi"] = byn[210][0]["d"], byn[210][0]["l"], byn[210][0]["h"]

def compare(key, R):
    payload = json.loads((REAL / ("noise_floor_" + key + ".json")).read_text(encoding="utf-8"))
    pr = payload["readouts"]
    rel = pr["reliability"]
    cmp = [(R["r"], rel["r"]), (R["r_lo"], rel["ci_lower"]), (R["r_hi"], rel["ci_upper"]),
           (R["sd"], rel["sd_prompt_runs"]), (R["mad"], rel["mean_abs_seed_diff"]), (R["r_within"], rel["r_within_family"])]
    cmp += [(R["r_fam"][f], rel["r_per_family"][f]) for f in FAMS]
    sh = pr["decomposition"]["share"]
    cmp += list(zip(R["ss_share"], (sh["seed_within_prompt"], sh["prompt_within_family"], sh["family"])))
    mc = pr["decomposition"]["mom"]["component"]
    cmp += list(zip(R["mom"], (mc["seed_within_prompt"], mc["prompt_within_family"], mc["family"])))
    msh = pr["decomposition"]["mom"]["share"]
    cmp += list(zip(R["mom_share"], (msh["seed_within_prompt"], msh["prompt_within_family"], msh["family"])))
    for n in SIZES:
        p, q = pr["per_n"][str(n)], R["per"][n]
        cmp += [(q["f_plus"], p["f_plus"]["rate"]), (q["f_minus"], p["f_minus"]["rate"]), (q["f_two"], p["f_two"]["rate"]),
                (q["f_one"], p["f_one"]["rate"]), (q["f_one_se"], p["f_one"]["se"]), (q["g_one"], p["g_one"]["rate"]),
                (q["g_one_se"], p["g_one"]["se"]), (q["g_one"], p["g_one_guard"]["rate"]),
                (q["hw_med"], p["half_width"]["median"]), (q["hw_mean"], p["half_width"]["mean"]),
                (q["hw_p05"], p["half_width"]["p05"]), (q["hw_p95"], p["half_width"]["p95"]),
                (q["sw_f_one"], p["swap"]["f_one"]["rate"]), (q["sw_g_one"], p["swap"]["g_one"]["rate"]),
                (q["sw_hw_med"], p["swap"]["half_width"]["median"])]
    cmp += [(R["r6"], pr["f19"]["share_at_or_above"]), (R["r6_sw"], pr["f19"]["swap"]["share_at_or_above"]),
            (R["full_delta"], pr["full_set_delta"])]
    R["maxdisc_vs_payload"] = max(abs(a - b) for a, b in cmp)
    R["n_compared"] = len(cmp)
    R["payload_conclusion"] = payload["conclusion"]
    pv = payload["provenance"]
    R["payload_prov"] = {k: pv[k] for k in ("git_commit", "git_status_tracked", "instrument_sha256", "state_sha256", "smoke", "numpy_version")}
    sp = REAL / ("noise_floor_" + key + ".json.state.jsonl")
    R["state_sha_ok"] = hashlib.sha256(sp.read_bytes()).hexdigest() == pv["state_sha256"]

out = {}
for key in POPS:
    A, B, R = readouts_for(key)
    byn = rows_for(key, A, B, R)
    rates_for(byn, R)
    compare(key, R)
    out[key] = R
    print(key, "rows", R["nrows"], "row maxdisc", R["row_maxdisc"], "subsets", R["subsets_regenerated"], "masks", R["masks_regenerated"],
          "state sha ok", R["state_sha_ok"], "gamma", R["drafted_gamma"], "ss ident", R["ss_ident"],
          "maxdisc vs payload", R["maxdisc_vs_payload"], "over", R["n_compared"])
Path(sys.argv[1]).write_text(json.dumps(conv(out), indent=1), encoding="utf-8")

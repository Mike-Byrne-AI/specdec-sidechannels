
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

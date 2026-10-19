
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

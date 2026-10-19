

def finish(pay, hdr, rows, D, out):
    cmp, scope_arr, acc = out.pop("_cmp"), out.pop("_scope_arr"), out.pop("_acc")
    prov, conc = pay["provenance"], pay["conclusion"]
    lab = conc["labels"]
    allN = scope_arr("history_tok", LB, "all")[1].sum()
    for scope in SCOPES:
        n = scope_arr("history_tok", LB, scope)[1]
        cmp(round(n.sum() / (L * K)), lab["scopes"][scope]["positions"], scope + "|pos")
        cmp(n.sum() / allN, lab["scopes"][scope]["share"], scope + "|share")
        cmp(int((n.sum(0) > 0).sum()), lab["scopes"][scope]["prompts_with_positions"], scope + "|prompts")
    st = prov["strat"]
    _, srows = load(st["state_path"])
    def idx(rr):
        return {(r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]), r["stratum"]): (int(r["hits"]), int(r["needed"])) for r in rr if r["arm"] in TWIN}
    mine, theirs = idx(rows), idx(srows)
    hmm = sum(1 for k in theirs if k in mine and mine[k][0] != theirs[k][0])
    nmm = sum(1 for k in theirs if k in mine and mine[k][1] != theirs[k][1])
    out["reproduce"] = {"strat_twin_rows": len(theirs), "r2_twin_rows": len(mine), "missing": len(set(theirs) - set(mine)), "extra": len(set(mine) - set(theirs)), "hits_mm": hmm, "needed_mm": nmm, "strat_rows_total": len(srows), "strat_arms": sorted({r["arm"] for r in srows})}
    cmp(len(theirs), lab["reproduce"]["n_strat_rows"], "rep n"); cmp(hmm, lab["reproduce"]["hits_mismatch_rows"], "rep h"); cmp(nmm, lab["reproduce"]["needed_mismatch_rows"], "rep n2")
    spay = json.load(open(st["path"], encoding="utf-8"))
    idmax = 0.0
    for scope in ("all", "covered", "fallback"):
        theirs_c = spay["conclusion"]["deltas"][f"gate_eq|B={LB}|{scope}"]
        for f in ("delta", "lo", "hi"):
            idmax = max(idmax, abs(D[f"gate_eq|B={LB}|{scope}"][f] - theirs_c[f]))
            idmax = max(idmax, abs(st["gate_eq"][scope][f] - theirs_c[f]))
    out["identity_max_abs"] = idmax
    stab = 0.0; nst = 0
    for arm in TWIN:
        for B in BUDGETS:
            for scope in SCOPES:
                key = f"{arm}|B={B}|{scope}"
                if key in spay["conclusion"]["tables"]:
                    nst += 1
                    for f in ("point", "ci_lo", "ci_hi", "needed"):
                        stab = max(stab, abs(spay["conclusion"]["tables"][key]["all"][f] - conc["tables"][key]["all"][f]))
    out["twin_tables_vs_strat_max_abs"] = (stab, nst)
    sd = 0.0; nsd = 0
    for k, v in spay["conclusion"]["deltas"].items():
        if k in conc["deltas"]:
            nsd += 1
            for f in ("delta", "lo", "hi", "needed"):
                sd = max(sd, abs(v[f] - conc["deltas"][k][f]))
    out["shared_deltas_vs_strat_max_abs"] = (sd, nsd)
    kv = prov["k_val_table"]
    best = -math.inf; bk = bl = None
    for kt in KTAGS:
        for lam in LAMS:
            v = kv[kt][str(lam)]
            if v > best:
                best, bk, bl = v, kt, lam
    out["k_reselect"] = (bk, bl, best)
    out["k_ok"] = (bk == prov["k_selected"] and bl == prov["lambda_selected"]["free_r2"] and prov["k_grid_edge"] == (bk in ("0", "inf")))
    out["free_r2_val_row_is_k_row"] = prov["val_table"]["free_r2"] == kv[bk]
    lam_ok = {}
    for arm in RIDGE_R2:
        vt = prov["val_table"][arm]
        b = -math.inf; bl2 = None
        for lam in LAMS:
            if vt[str(lam)] > b:
                b, bl2 = vt[str(lam)], lam
        edge = bl2 in (LAMS[0], LAMS[-1])
        lam_ok[arm] = (bl2, prov["lambda_selected"][arm], bl2 == prov["lambda_selected"][arm], edge, prov["lambda_grid_edge"][arm] == edge)
    out["lambda_reselect"] = lam_ok
    out["twin_lambdas_eq_strat"] = all(prov["lambda_selected"][a] == st["lambda_selected"][a] for a in TWIN)
    return lab, mine, theirs, hmm, nmm, idmax


def reproduce(res, twin_name):
    thdr, trows, tsha = read_jsonl(ROOT + "/results/real/" + twin_name + ".json.state.jsonl")
    ai = {a: i for i, a in enumerate(ARMS)}; bi = {b: i for i, b in enumerate(BUDGETS)}
    pix = {p: i for i, p in enumerate(res["prompts"])}
    Hs, Ns = res["H"].sum(axis=2), res["N"].sum(axis=2)
    hm = 0; nm = 0; maxgap = 0; nrow = 0; extra = 0; cmp_vals = 0
    tk = set()
    for r in trows:
        k = (ai[r["arm"]], bi[r["budget"]], int(r["gate"]), pix[int(r["prompt_idx"])])
        assert k not in tk
        tk.add(k); nrow += 1; cmp_vals += 2
        if Ns[k] != r["needed"]:
            nm += 1
        if Hs[k] != r["hits"]:
            hm += 1; maxgap = max(maxgap, abs(int(Hs[k]) - r["hits"]))
    for a in TWIN_ARMS:
        for B in BUDGETS:
            for gg in range(NG):
                for p in range(30):
                    k = (ai[a], bi[B], gg, p)
                    if k not in tk and Ns[k] > 0:
                        extra += 1
    return {"twin_rows": nrow, "values_compared": cmp_vals, "needed_mm": nm, "hits_mm": hm, "max_gap": maxgap,
            "extra_in_strat": extra, "twin_state_sha": tsha, "twin_hdr": thdr}

def leaves(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, pre + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, pre + "[" + str(i) + "]")
    else:
        yield pre, x

def compare(mine, theirs, label):
    mm = dict(leaves(mine)); tt = dict(leaves(theirs))
    maxd = 0.0; n = 0; nonnum = []; missing = []
    for k, v in mm.items():
        if k not in tt:
            missing.append(k)
            continue
        t = tt[k]; n += 1
        if isinstance(v, (bool, str)) or isinstance(t, (bool, str)) or v is None or t is None:
            if v != t:
                nonnum.append((k, v, t))
        else:
            maxd = max(maxd, abs(float(v) - float(t)))
    return {"what": label, "compared": n, "max_abs": maxd, "nonnum_mismatch": nonnum[:10], "n_nonnum_mismatch": len(nonnum),
            "missing_in_payload": missing[:10], "n_missing": len(missing), "payload_leaves": len(tt),
            "payload_leaves_not_recomputed": sorted(set(tt) - set(mm))[:60]}

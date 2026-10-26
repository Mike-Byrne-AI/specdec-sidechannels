
def recompute(name):
    hdr, rows, ssha = read_jsonl(ROOT + "/results/real/" + name + ".json.state.jsonl")
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    assert len(prompts) == 30, len(prompts)
    pix = {p: i for i, p in enumerate(prompts)}
    ai = {a: i for i, a in enumerate(ARMS)}; bi = {b: i for i, b in enumerate(BUDGETS)}; si = {s: i for i, s in enumerate(STRATA)}
    H = np.zeros((13, 3, 6, NG, 30), np.int64); N = np.zeros_like(H); seen = np.zeros(H.shape, dtype=bool)
    bad = 0
    for r in rows:
        assert set(r) == {"arm", "budget", "key", "depth", "gate", "prompt_idx", "stratum", "hits", "needed"}, r
        assert r["key"] == 1 and r["depth"] is None
        k = (ai[r["arm"]], bi[r["budget"]], si[r["stratum"]], int(r["gate"]), pix[int(r["prompt_idx"])])
        assert not seen[k], ("dup", r)
        H[k] = r["hits"]; N[k] = r["needed"]; seen[k] = True
        if not (0 <= r["hits"] <= r["needed"]) or r["needed"] <= 0:
            bad += 1
    assert bad == 0
    Hf = H.astype(np.float64); Nf = N.astype(np.float64)
    def sc(arr, scope):
        idx = [si[s] for s in (UNIONS[scope] if scope in UNIONS else [scope])]
        return arr[:, :, idx].sum(axis=2)
    pair_viol = int((N != N[:1]).any(axis=0).sum())
    bud_viol = int((N != N[:, :1]).any(axis=1).sum())
    gate_viol = int((N != N[:, :, :, :1]).any(axis=3).sum())
    mult_viol = int((N % K != 0).sum())
    pres_viol = int((seen != seen[:1, :1]).sum())
    out = {"rows": len(rows), "state_sha": ssha, "hdr": hdr, "prompts": prompts,
           "checks": {"pairing_arms_cells_violating": pair_viol, "pairing_budgets_violating": bud_viol,
                      "gate_uniform_violations": gate_viol, "needed_mult_K_violations": mult_viol,
                      "row_presence_violations": pres_viol}}
    tables, deltas, dropped = {}, {}, 0
    for a in ARMS:
        for B in BUDGETS:
            for scope in SCOPES:
                h = sc(Hf, scope)[ai[a], bi[B]]; n = sc(Nf, scope)[ai[a], bi[B]]
                if n.sum() == 0:
                    continue
                pg = {}
                for g in range(NG):
                    if n[g].sum() == 0:
                        continue
                    lo, hi, dr = ratio_ci(h[g], n[g]); dropped += dr
                    pg[str(g)] = {"point": float(h[g].sum() / n[g].sum()), "ci_lo": lo, "ci_hi": hi, "needed": int(n[g].sum())}
                hp, np_ = h.sum(axis=0), n.sum(axis=0)
                lo, hi, dr = ratio_ci(hp, np_); dropped += dr
                tables[a + "|B=" + str(B) + "|" + scope] = {"arm": a, "budget": B, "scope": scope, "dims": DIMS[a], "per_gate": pg,
                    "all": {"point": float(hp.sum() / np_.sum()), "ci_lo": lo, "ci_hi": hi, "needed": int(np_.sum())}}
    names = {"FREE": "free_bigram_b", "HIST": "history_bigram_b"}
    for B in BUDGETS:
        for scope in SCOPES:
            for nm, a, b in PAIRS:
                a2, b2 = names.get(a, a), names.get(b, b)
                ha = sc(Hf, scope)[ai[a2], bi[B]].sum(axis=0); hb = sc(Hf, scope)[ai[b2], bi[B]].sum(axis=0)
                na = sc(Nf, scope)[ai[a2], bi[B]].sum(axis=0); nb = sc(Nf, scope)[ai[b2], bi[B]].sum(axis=0)
                assert np.array_equal(na, nb)
                if na.sum() == 0:
                    continue
                d, lo, hi, dr = delta_ci(ha, hb, na); dropped += dr
                deltas[nm + "|B=" + str(B) + "|" + scope] = {"delta": d, "lo": lo, "hi": hi, "needed": int(na.sum())}
    out["tables"], out["deltas"], out["boot_dropped_resamples"] = tables, deltas, dropped
    n_all = sc(Nf, "all")[ai["history_tok"], bi[16]].sum(axis=0)
    scopes = {}
    for scope in SCOPES:
        n = sc(Nf, scope)[ai["history_tok"], bi[16]].sum(axis=0)
        scopes[scope] = {"positions": int(round(n.sum() / (NG * K))), "share": float(n.sum() / n_all.sum()),
                         "prompts_with_positions": int((n > 0).sum())}
    out["scopes"] = scopes
    out["per_prompt_positions"] = {s: (N[ai["history_tok"], bi[16], si[s], 0] // K).tolist() for s in STRATA}
    out["H"], out["N"] = H, N
    return out

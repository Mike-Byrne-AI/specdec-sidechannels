

def run(name):
    pay = json.load(open(f"results/real/{name}.json", encoding="utf-8"))
    hdr, rows = load(f"results/real/{name}.json.state.jsonl")
    prov, conc = pay["provenance"], pay["conclusion"]
    out = {"name": name}
    assert len(rows) == pay["n_state_rows"]
    out["n_rows"] = len(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    P = len(prompts); pidx = {p: i for i, p in enumerate(prompts)}
    out["n_prompts"] = P
    out["prompts_all_test"] = all(split_of_prompt(p) == "test" for p in prompts)
    arms = sorted({r["arm"] for r in rows})
    out["arms"] = arms
    H = {}; N = {}; seen = set(); dup = 0
    for r in rows:
        key = (r["arm"], int(r["budget"]), r["stratum"], int(r["gate"]), int(r["prompt_idx"]))
        if key in seen:
            dup += 1
        seen.add(key)
        a = (r["arm"], int(r["budget"]))
        if a not in H:
            H[a] = np.zeros((6, L, P)); N[a] = np.zeros((6, L, P))
        s = STRATA.index(r["stratum"])
        H[a][s, int(r["gate"]), pidx[int(r["prompt_idx"])]] += int(r["hits"])
        N[a][s, int(r["gate"]), pidx[int(r["prompt_idx"])]] += int(r["needed"])
        assert 0 <= int(r["hits"]) <= int(r["needed"])
    out["dup_rows"] = dup

    def scope_arr(arm, B, scope):
        idx = [STRATA.index(s) for s in (UNIONS[scope] if scope in UNIONS else [scope])]
        return H[(arm, B)][idx].sum(axis=0), N[(arm, B)][idx].sum(axis=0)

    acc = {"mx": 0.0, "n": 0, "worst": None}
    def cmp(a, b, tag):
        acc["n"] += 1
        dd = abs(float(a) - float(b))
        if dd > acc["mx"]:
            acc["mx"], acc["worst"] = dd, tag
    tkeys = set()
    for arm in arms:
        for B in BUDGETS:
            for scope in SCOPES:
                h, n = scope_arr(arm, B, scope)
                key = f"{arm}|B={B}|{scope}"; tkeys.add(key)
                t = conc["tables"][key]
                for g in range(L):
                    if n[g].sum() == 0:
                        continue
                    lo, hi = cluster_bootstrap_ci(h[g], n[g], n_boot=NB, seed=SEED)
                    pg = t["per_gate"][str(g)]
                    cmp(h[g].sum() / n[g].sum(), pg["point"], key + f"|g{g}|pt"); cmp(lo, pg["ci_lo"], key + "lo"); cmp(hi, pg["ci_hi"], key + "hi"); cmp(n[g].sum(), pg["needed"], key + "n")
                Hs, Ns = h.sum(axis=0), n.sum(axis=0)
                lo, hi = cluster_bootstrap_ci(Hs, Ns, n_boot=NB, seed=SEED)
                cmp(Hs.sum() / Ns.sum(), t["all"]["point"], key + "|pt"); cmp(lo, t["all"]["ci_lo"], key + "|lo"); cmp(hi, t["all"]["ci_hi"], key + "|hi"); cmp(Ns.sum(), t["all"]["needed"], key + "|n")
    out["table_keys_equal"] = tkeys == set(conc["tables"])
    pairing_ok = True
    D = {}
    for B in BUDGETS:
        for scope in SCOPES:
            ref = scope_arr("history_tok", B, scope)[1].sum(axis=0)
            for arm in arms:
                if not np.array_equal(scope_arr(arm, B, scope)[1].sum(axis=0), ref):
                    pairing_ok = False
            for nm, a, b in PAIRS:
                ha, na = scope_arr(a, B, scope); hb, nb = scope_arr(b, B, scope)
                Ha, Na, Hb, Nb = ha.sum(0), na.sum(0), hb.sum(0), nb.sum(0)
                assert np.array_equal(Na, Nb)
                dlt, lo, hi = paired_cluster_delta_ci(Ha, Hb, Na, n_boot=NB, seed=SEED)
                D[f"{nm}|B={B}|{scope}"] = {"delta": dlt, "lo": lo, "hi": hi, "needed": int(Na.sum())}
    out["pairing_ok"] = pairing_ok
    out["delta_keys_equal"] = set(D) == set(conc["deltas"])
    for k, v in D.items():
        for f in ("delta", "lo", "hi", "needed"):
            cmp(v[f], conc["deltas"][k][f], k + "|" + f)
    out["_cmp"] = cmp; out["_scope_arr"] = scope_arr; out["_acc"] = acc
    return pay, hdr, rows, D, out

def scope_cell(arm, B, scope):
    parts = [scope] if scope in STRATA else UN[scope]
    out = {}
    for s in parts:
        for g, hn in cell.get((arm, B, s), {}).items():
            h0, n0 = out.get(g, (0, 0)); out[g] = (h0 + hn[0], n0 + hn[1])
    return out

viol = 0; checked = 0
for B in BUD:
    for s in STRATA:
        ref = {g: hn[1] for g, hn in cell[("history_tok", B, s)].items()}
        for a in ARMS:
            checked += 1
            if {g: hn[1] for g, hn in cell[(a, B, s)].items()} != ref: viol += 1
        if ref != {g: hn[1] for g, hn in cell[("history_tok", 8, s)].items()}: viol += 1
print("pairing (B, stratum, arm) cells checked", checked, "violations", viol)
pos = {}
for s in STRATA:
    pos[s] = sum(v[1] for v in cell[("history_tok", 16, s)].values()) / 128
print("positions per stratum", {s: pos[s] for s in STRATA}, "sum", sum(pos.values()), "meta bigram/test", meta["n_positions"].get("bigram/test"))
sc_meta = meta["strata_counts"]["test"]
print("meta strata_counts test", {s: (sc_meta[s]["n"], round(sc_meta[s]["share"], 6)) for s in STRATA}, "n", sc_meta["n"])

IDX = np.random.default_rng(0).integers(0, P, size=(NB, P))
def my_ci(h, n):
    s = h[IDX].sum(1); t = n[IDX].sum(1); v = t > 0
    lo, hi = np.percentile(s[v] / t[v], [2.5, 97.5]); return float(h.sum() / n.sum()), float(lo), float(hi)
def my_delta(ha, hb, n):
    d = (ha - hb)[IDX].sum(1); t = n[IDX].sum(1); v = t > 0
    lo, hi = np.percentile(d[v] / t[v], [2.5, 97.5]); return float((ha - hb).sum() / n.sum()), float(lo), float(hi)
pidx = {p: i for i, p in enumerate(prompts)}
def per_prompt(c, gate=None):
    h = np.zeros(P); n = np.zeros(P)
    for gp, hn in c.items():
        if gate is not None and gp[0] != gate: continue
        h[pidx[gp[1]]] += hn[0]; n[pidx[gp[1]]] += hn[1]
    return h, n
MAXD = [0.0]; NCMP = [0]; WORST = [None]; LIBD = [0.0]; STRMM = []
def cmp(a, b, tag):
    NCMP[0] += 1
    if isinstance(a, (bool, str, dict, list)) or isinstance(b, (bool, str, dict, list)) or a is None or b is None:
        if a != b: STRMM.append((tag, a, b))
        return
    d = abs(float(a) - float(b))
    if d > MAXD[0]: MAXD[0], WORST[0] = d, tag

mine_tab = {}
for a in ARMS:
    for B in BUD:
        for sc in SCOPES:
            c = scope_cell(a, B, sc); h, n = per_prompt(c)
            pt, lo, hi = my_ci(h, n)
            l2 = lib_ci(h, n, n_boot=NB, seed=0); LIBD[0] = max(LIBD[0], abs(l2[0] - lo), abs(l2[1] - hi))
            mine_tab[(a, B, sc)] = (pt, lo, hi, n.sum())
            t = C["tables"][f"{a}|B={B}|{sc}"]
            cmp(a, t["arm"], ("tab", a, B, sc, "arm")); cmp(B, t["budget"], ("tab", a, B, sc, "B")); cmp(sc, t["scope"], ("tab", a, B, sc, "scope"))
            for v, k in ((pt, "point"), (lo, "ci_lo"), (hi, "ci_hi"), (n.sum(), "needed")): cmp(v, t["all"][k], ("tab", a, B, sc, k))
            cmp(len(t["per_gate"]), 16, ("tab", a, B, sc, "ngates"))
            for g in gates:
                hg, ng = per_prompt(c, g); pg, lg, hg2 = my_ci(hg, ng); tg = t["per_gate"][str(g)]
                for v, k in ((pg, "point"), (lg, "ci_lo"), (hg2, "ci_hi"), (ng.sum(), "needed")): cmp(v, tg[k], ("pg", a, B, sc, g, k))
print("tables recomputed", len(mine_tab), "payload tables", len(C["tables"]))

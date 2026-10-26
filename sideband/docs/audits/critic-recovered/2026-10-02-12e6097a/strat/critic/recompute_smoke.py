import sys, json
sys.path.insert(0, "src")
import numpy as np
from sideband.stats import paired_cluster_delta_ci as lib_delta, cluster_bootstrap_ci as lib_ci

S = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\smoke"
lines = open(S + r"\strat_smoke.json.state.jsonl", encoding="utf-8").read().splitlines()
hdr = json.loads(lines[0]); assert hdr["state_header"]
rows = [json.loads(l) for l in lines[1:] if l.strip()]
payload = json.load(open(S + r"\strat_smoke.json", encoding="utf-8"))
C = payload["conclusion"]
print("rows", len(rows), "payload n_state_rows", payload["n_state_rows"])
STRATA = ["covered", "cur_unseen", "prev_unseen", "both_unseen"]
SCOPES = STRATA + ["fallback", "all"]
UN = {"fallback": STRATA[1:], "all": STRATA}
ARMS = ["history","free_tok","history_tok","free_bigram_b","free_bigram_a","history_bigram_b","history_bigram_a",
        "free_all","history_all","pt_only","free_bigram_pt","history_tok_pt","history_bigram_pt"]
BUD = [8, 16, 32]
enc = hdr["encoding"]; suf = {"prev_table": "b", "cur_table_at_prev": "a"}[enc]
FREE, HIST = "free_bigram_" + suf, "history_bigram_" + suf
print("encoding", enc, FREE, HIST)
cell = {}
for r in rows:
    assert r["key"] == 1 and r["depth"] is None and r["stratum"] in STRATA
    k = (r["arm"], r["budget"], r["stratum"]); g = (r["gate"], r["prompt_idx"])
    assert g not in cell.setdefault(k, {})
    assert 0 <= r["hits"] <= r["needed"]
    cell[k][g] = (r["hits"], r["needed"])
prompts = sorted({r["prompt_idx"] for r in rows}); P = len(prompts)
gates = sorted({r["gate"] for r in rows})
print("prompts", P, prompts, "gates", len(gates), "arms ok", sorted({r["arm"] for r in rows}) == sorted(ARMS))

def scope_cell(arm, B, scope):
    parts = [scope] if scope in STRATA else UN[scope]
    out = {}
    for s in parts:
        for g, hn in cell.get((arm, B, s), {}).items():
            h0, n0 = out.get(g, (0, 0)); out[g] = (h0 + hn[0], n0 + hn[1])
    return out

pair_viol = 0; checked = 0
for B in BUD:
    for s in STRATA:
        ref = dict((g, hn[1]) for g, hn in cell[("history_tok", B, s)].items())
        for a in ARMS:
            got = dict((g, hn[1]) for g, hn in cell[(a, B, s)].items())
            checked += 1
            if got != ref: pair_viol += 1
print("pairing: (B,stratum,arm) cells checked", checked, "per-(prompt,gate) needed violations", pair_viol)
for s in STRATA:
    r8 = dict((g, hn[1]) for g, hn in cell[("history_tok", 8, s)].items())
    for B in BUD:
        assert dict((g, hn[1]) for g, hn in cell[("history_tok", B, s)].items()) == r8
    per_p = {}
    for gp, n in r8.items(): per_p.setdefault(gp[1], set()).add(n)
    assert all(len(v) == 1 for v in per_p.values())
    assert all(len([gp for gp in r8 if gp[1] == pp]) == 16 for pp in per_p)
tot_pos = 0
for s in STRATA:
    npos = sum(v[1] for v in cell[("history_tok", 16, s)].values()) / (16 * 8)
    tot_pos += npos
    print("  stratum", s, "positions", npos)
print("  sum of strata positions", tot_pos)

IDX = np.random.default_rng(0).integers(0, P, size=(2000, P))
def my_ci(h, n):
    s = h[IDX].sum(1); t = n[IDX].sum(1); v = t > 0
    lo, hi = np.percentile(s[v] / t[v], [2.5, 97.5]); return float(h.sum() / n.sum()), float(lo), float(hi)
def my_delta(ha, hb, n):
    d = (ha - hb)[IDX].sum(1); t = n[IDX].sum(1); v = t > 0
    lo, hi = np.percentile(d[v] / t[v], [2.5, 97.5]); return float((ha - hb).sum() / n.sum()), float(lo), float(hi)
pidx = dict((p, i) for i, p in enumerate(prompts))
def per_prompt(c, gate=None):
    h = np.zeros(P); n = np.zeros(P)
    for gp, hn in c.items():
        if gate is not None and gp[0] != gate: continue
        h[pidx[gp[1]]] += hn[0]; n[pidx[gp[1]]] += hn[1]
    return h, n
MAXD = [0.0]; NCMP = [0]; WORST = [None]; LIBD = [0.0]; STRMM = [0]
def cmp(a, b, tag):
    NCMP[0] += 1
    if isinstance(a, (bool, str)) or isinstance(b, (bool, str)) or a is None or b is None:
        if a != b:
            print("MISMATCH", tag, a, b); STRMM[0] += 1
        return
    d = abs(float(a) - float(b))
    if d > MAXD[0]: MAXD[0], WORST[0] = d, tag

mine_tab = {}
for a in ARMS:
    for B in BUD:
        for sc in SCOPES:
            c = scope_cell(a, B, sc)
            h, n = per_prompt(c)
            pt, lo, hi = my_ci(h, n)
            l2 = lib_ci(h, n, n_boot=2000, seed=0); LIBD[0] = max(LIBD[0], abs(l2[0] - lo), abs(l2[1] - hi))
            mine_tab[(a, B, sc)] = (pt, lo, hi, n.sum())
            t = C["tables"][a + "|B=" + str(B) + "|" + sc]
            cmp(pt, t["all"]["point"], ("tab", a, B, sc, "pt")); cmp(lo, t["all"]["ci_lo"], ("tab", a, B, sc, "lo"))
            cmp(hi, t["all"]["ci_hi"], ("tab", a, B, sc, "hi")); cmp(n.sum(), t["all"]["needed"], ("tab", a, B, sc, "n"))
            cmp(len(t["per_gate"]), 16, ("tab", a, B, sc, "ngates"))
            for g in gates:
                hg, ng = per_prompt(c, g)
                pg, lg, hg2 = my_ci(hg, ng)
                tg = t["per_gate"][str(g)]
                cmp(pg, tg["point"], ("pg", a, B, sc, g)); cmp(lg, tg["ci_lo"], ("pg", a, B, sc, g)); cmp(hg2, tg["ci_hi"], ("pg", a, B, sc, g))
print("tables recomputed", len(mine_tab), "payload tables", len(C["tables"]))
PAIRS = [("address_beyond_token","history_tok","free_tok"),("gate_eq","history_tok",FREE),("address_beyond_bigram",HIST,FREE),
         ("bigram_gain",FREE,"free_tok"),("pt_gain","free_bigram_pt",FREE),("d_pt","history_tok","free_bigram_pt"),
         ("d_eq_pt","history_tok_pt","free_bigram_pt"),("d_add_pt","history_bigram_pt","free_bigram_pt"),
         ("pt_only-free_tok","pt_only","free_tok"),("history_tok_pt-history_tok","history_tok_pt","history_tok")]
mine_d = {}
for B in BUD:
    for sc in SCOPES:
        for name, a, b in PAIRS:
            ha, na = per_prompt(scope_cell(a, B, sc)); hb, nb = per_prompt(scope_cell(b, B, sc))
            assert np.array_equal(na, nb)
            d, lo, hi = my_delta(ha, hb, na)
            l2 = lib_delta(ha, hb, na, n_boot=2000, seed=0); LIBD[0] = max(LIBD[0], abs(l2[0]-d), abs(l2[1]-lo), abs(l2[2]-hi))
            mine_d[(name, B, sc)] = (d, lo, hi, na.sum())
            pd = C["deltas"][name + "|B=" + str(B) + "|" + sc]
            for i, k in enumerate(("delta", "lo", "hi", "needed")):
                cmp((d, lo, hi, na.sum())[i], pd[k], ("delta", name, B, sc, k))
print("deltas recomputed", len(mine_d), "payload deltas", len(C["deltas"]))

def reading(d, lo, hi):
    if lo > 0 and d >= 0.05: return "SIGNAL"
    if hi < 0: return "NEGATIVE"
    return "NOT-SHOWN"
L = C["labels"]
cov, fb, dpt = mine_d[("gate_eq",16,"covered")], mine_d[("gate_eq",16,"fallback")], mine_d[("d_pt",16,"all")]
rc, rf, rp = reading(*cov[:3]), reading(*fb[:3]), reading(*dpt[:3])
q1 = "COVERED-MATERIAL" if rc == "SIGNAL" else "COVERAGE-EFFECT" if rf == "SIGNAL" else "UNLOCATED"
q2 = "PT-SURVIVES" if rp == "SIGNAL" else "PT-ABSORBS"
rdeq = reading(*mine_d[("d_eq_pt",16,"all")][:3])
checks = [("gate_eq_covered_reading", rc), ("gate_eq_fallback_reading", rf), ("d_pt_all_reading", rp), ("q1", q1), ("q2", q2),
          ("label", q1 + " / " + q2),
          ("covered_floor_straddle", bool(cov[1] <= 0.05 <= cov[2])), ("d_pt_floor_straddle", bool(dpt[1] <= 0.05 <= dpt[2])),
          ("d_eq_pt_all_reading", rdeq), ("d_eq_pt_agrees_with_d_pt", rdeq == rp),
          ("free_bigram_arm", FREE), ("history_bigram_arm", HIST), ("encoding", enc)]
for k, v in checks:
    cmp(v, L[k], ("label", k))
for s in SCOPES:
    cmp(reading(*mine_d[("gate_eq",16,s)][:3]), L["gate_eq_readings"][s], ("gate_eq_readings", s))
    cmp(reading(*mine_d[("d_pt",16,s)][:3]), L["d_pt_readings"][s], ("d_pt_readings", s))
for nm, tup in (("gate_eq_covered", cov), ("gate_eq_fallback", fb), ("d_pt_all", dpt)):
    for i, k in enumerate(("delta", "lo", "hi", "needed")): cmp(tup[i], L[nm][k], (nm, k))
allN = mine_tab[("history_tok", 16, "all")][3]
for s in SCOPES:
    h, n = per_prompt(scope_cell("history_tok", 16, s))
    cmp(round(n.sum() / 128), L["scopes"][s]["positions"], ("scope", s, "positions"))
    cmp(n.sum() / allN, L["scopes"][s]["share"], ("scope", s, "share"))
    cmp(int((n > 0).sum()), L["scopes"][s]["prompts_with_positions"], ("scope", s, "prompts"))
print("MAX ABS DISCREPANCY vs payload:", repr(MAXD[0]), "over", NCMP[0], "compared values; string/bool mismatches", STRMM[0], "worst", WORST[0])
print("own bootstrap vs sideband.stats max abs diff:", repr(LIBD[0]))
print("labels:", q1, "/", q2, "| readings cov/fb/dpt", rc, rf, rp, "| straddles", cov[1] <= 0.05 <= cov[2], dpt[1] <= 0.05 <= dpt[2])
def f(t): return "%+.4f [%+.4f, %+.4f]" % (t[0], t[1], t[2])
for B in BUD:
    for sc in SCOPES:
        print("B=%2d %-12s " % (B, sc) + " | ".join(nm + " " + f(mine_d[(nm,B,sc)]) for nm, x, y in PAIRS))
for a in ARMS:
    t = mine_tab[(a,16,"all")]
    print("B=16 %-18s all %.4f [%.4f, %.4f]" % (a, t[0], t[1], t[2]))
out = dict(deltas=dict((k[0] + "|B=" + str(k[1]) + "|" + k[2], v[:3]) for k, v in mine_d.items()),
           tables=dict((k[0] + "|B=" + str(k[1]) + "|" + k[2], v[:3]) for k, v in mine_tab.items()))
json.dump(out, open(r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\critic\mine.json", "w"))

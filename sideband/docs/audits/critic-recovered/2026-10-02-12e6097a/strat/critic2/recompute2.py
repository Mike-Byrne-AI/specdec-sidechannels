import sys, json
sys.path.insert(0, "src")
import numpy as np
from sideband.stats import paired_cluster_delta_ci as lib_delta, cluster_bootstrap_ci as lib_ci
S = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\smoke"
OUT = r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\critic2"
print("numpy", np.__version__)
def load_state(p):
    lines = open(p, encoding="utf-8").read().splitlines()
    h = json.loads(lines[0]); assert h["state_header"] is True
    return h, [json.loads(l) for l in lines[1:] if l.strip()]
hdr, rows = load_state(S + r"\strat_smoke2.json.state.jsonl")
payload = json.load(open(S + r"\strat_smoke2.json", encoding="utf-8"))
meta = json.load(open(S + r"\strat_smoke2.meta.json", encoding="utf-8"))
C = payload["conclusion"]; LAB = C["labels"]
print("rows", len(rows), "payload n_state_rows", payload["n_state_rows"], "header twin", hdr["twin"], "smoke", hdr["smoke"])
print("meta == payload provenance:", meta == payload["provenance"])
STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UN = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + ["covered", "fallback", "all"]
ARMS = ["history","free_tok","history_tok","free_bigram_b","free_bigram_a","history_bigram_b","history_bigram_a",
        "free_all","history_all","pt_only","free_bigram_pt","history_tok_pt","history_bigram_pt"]
BUD = [8, 16, 32]; MAT = 0.05; NB = 2000
enc = hdr["encoding"]; suf = {"prev_table": "b", "cur_table_at_prev": "a"}[enc]
FREE, HIST = "free_bigram_" + suf, "history_bigram_" + suf
print("encoding", enc, FREE, HIST)
cell = {}
for r in rows:
    assert set(r) == {"arm","budget","key","depth","gate","prompt_idx","stratum","hits","needed"}, r
    assert r["key"] == 1 and r["depth"] is None and r["stratum"] in STRATA and r["arm"] in ARMS and r["budget"] in BUD
    k = (r["arm"], r["budget"], r["stratum"]); g = (r["gate"], r["prompt_idx"])
    assert g not in cell.setdefault(k, {}), ("dup", k, g)
    assert 0 <= r["hits"] <= r["needed"] and r["needed"] > 0 and r["needed"] % 8 == 0
    cell[k][g] = (r["hits"], r["needed"])
prompts = sorted({r["prompt_idx"] for r in rows}); P = len(prompts)
gates = sorted({r["gate"] for r in rows})
print("prompts", P, "gates", len(gates), "arms", len({r["arm"] for r in rows}), "cells", len(cell))
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
PAIRS = [("address_beyond_token","history_tok","free_tok"),("gate_eq","history_tok",FREE),("address_beyond_bigram",HIST,FREE),
         ("bigram_gain",FREE,"free_tok"),("pt_gain","free_bigram_pt",FREE),("d_pt","history_tok","free_bigram_pt"),
         ("d_eq_pt","history_tok_pt","free_bigram_pt"),("d_add_pt","history_bigram_pt","free_bigram_pt"),
         ("pt_only-free_tok","pt_only","free_tok"),("history_tok_pt-history_tok","history_tok_pt","history_tok"),
         ("history_bigram_pt-history_tok_pt","history_bigram_pt","history_tok_pt")]
mine_d = {}
for B in BUD:
    for sc in SCOPES:
        for name, a, b in PAIRS:
            ha, na = per_prompt(scope_cell(a, B, sc)); hb, nb = per_prompt(scope_cell(b, B, sc))
            assert np.array_equal(na, nb)
            d, lo, hi = my_delta(ha, hb, na)
            l2 = lib_delta(ha, hb, na, n_boot=NB, seed=0); LIBD[0] = max(LIBD[0], abs(l2[0]-d), abs(l2[1]-lo), abs(l2[2]-hi))
            mine_d[(name, B, sc)] = (d, lo, hi, na.sum())
            pd = C["deltas"][f"{name}|B={B}|{sc}"]
            for i, k in enumerate(("delta", "lo", "hi", "needed")): cmp((d, lo, hi, na.sum())[i], pd[k], ("delta", name, B, sc, k))
print("deltas recomputed", len(mine_d), "payload deltas", len(C["deltas"]))
print("payload delta keys not recomputed:", set(C["deltas"]) - {f"{n}|B={B}|{s}" for (n, B, s) in mine_d})

def reading(d, lo, hi):
    if lo > 0 and d >= MAT: return "SIGNAL"
    if hi < 0: return "NEGATIVE"
    return "NOT-SHOWN"
def strad(t): return bool(t[1] <= MAT <= t[2])
cov, fb = mine_d[("gate_eq",16,"covered")], mine_d[("gate_eq",16,"fallback")]
eqpt, addpt = mine_d[("d_eq_pt",16,"all")], mine_d[("d_add_pt",16,"all")]
dpt, anc = mine_d[("d_pt",16,"all")], mine_d[("history_bigram_pt-history_tok_pt",16,"all")]
rc, rf, re_, ra, rp = reading(*cov[:3]), reading(*fb[:3]), reading(*eqpt[:3]), reading(*addpt[:3]), reading(*dpt[:3])
q1 = "COVERED-MATERIAL" if rc == "SIGNAL" else "FALLBACK-LOCATED" if rf == "SIGNAL" else "UNLOCATED"
es, as_ = re_ == "SIGNAL", ra == "SIGNAL"
q2 = "PT-SURVIVES" if es and as_ else "PT-COMPLEMENTARY" if (not es and as_) else "PT-ABSORBS" if (not es and not as_) else "PT-INCONSISTENT"
cause = None if q2 != "PT-INCONSISTENT" else ("reader" if anc[2] < 0 else "floor straddle")
mine_lab = {"encoding": enc, "free_bigram_arm": FREE, "history_bigram_arm": HIST, "missing_arms": [], "missing_label_cells": [],
            "reproduce": None, "all_gate_eq_matches_twin": None, "reproduce_status": None, "reproduce_ok": None,
            "gate_eq_covered_reading": rc, "gate_eq_fallback_reading": rf, "d_eq_pt_all_reading": re_, "d_add_pt_all_reading": ra,
            "d_pt_all_reading": rp, "covered_floor_straddle": strad(cov), "d_eq_pt_floor_straddle": strad(eqpt),
            "d_add_pt_floor_straddle": strad(addpt), "d_pt_floor_straddle": strad(dpt),
            "covered_negative": rc == "NEGATIVE", "pt_inconsistent_cause": cause, "q1": q1, "q2": q2,
            "label": f"{q1} / {q2}", "void": False}
checked_keys = set()
for k, v in mine_lab.items():
    cmp(v, LAB.get(k, "<ABSENT>"), ("label", k)); checked_keys.add(k)
for nm, tup in (("gate_eq_covered", cov), ("gate_eq_fallback", fb), ("d_eq_pt_all", eqpt), ("d_add_pt_all", addpt),
                ("d_pt_all", dpt), ("pt_dilution_anchor", anc)):
    for i, k in enumerate(("delta", "lo", "hi", "needed")): cmp(tup[i], LAB[nm][k], (nm, k))
    checked_keys.add(nm)
for name, field in (("gate_eq", "gate_eq_readings"), ("d_pt", "d_pt_readings"), ("d_eq_pt", "d_eq_pt_readings")):
    cmp(sorted(LAB[field]), sorted(SCOPES), (field, "keys"))
    for s in SCOPES: cmp(reading(*mine_d[(name,16,s)][:3]), LAB[field][s], (field, s))
    checked_keys.add(field)
allN = mine_tab[("history_tok", 16, "all")][3]
for s in SCOPES:
    h, n = per_prompt(scope_cell("history_tok", 16, s))
    cmp(round(n.sum() / 128), LAB["scopes"][s]["positions"], ("scope", s, "positions"))
    cmp(n.sum() / allN, LAB["scopes"][s]["share"], ("scope", s, "share"))
    cmp(int((n > 0).sum()), LAB["scopes"][s]["prompts_with_positions"], ("scope", s, "prompts"))
checked_keys.add("scopes")
sys.path.insert(0, "tools")
import run_prefetch_strat as rs
s1 = rs.SENTENCES_Q1[(q1, strad(cov))]
if rc == "NEGATIVE": s1 = "the address block reads below the equal-dims free bigram block on " + rs._COV + " (NEGATIVE); " + s1
cmp(s1 + "; " + rs.SENTENCES_Q2[(q2, strad(eqpt))], LAB["sentence"], ("label", "sentence")); checked_keys.add("sentence")
checked_keys.add("rule")
print("label keys NOT checked:", sorted(set(LAB) - checked_keys))
print("MAX ABS DISCREPANCY vs payload:", repr(MAXD[0]), "over", NCMP[0], "compared values; non-numeric mismatches", len(STRMM), "worst", WORST[0])
for m in STRMM[:10]: print("  MISMATCH", m)
print("own bootstrap vs sideband.stats max abs diff:", repr(LIBD[0]))
print("LABEL", q1, "/", q2, "| readings cov/fb/eqpt/addpt/dpt", rc, rf, re_, ra, rp,
      "| straddles cov/eqpt/addpt/dpt", strad(cov), strad(eqpt), strad(addpt), strad(dpt), "| cause", cause, "| void False")
def f(t): return "%+.4f [%+.4f, %+.4f]" % (t[0], t[1], t[2])
for B in BUD:
    for sc in SCOPES:
        print("B=%2d %-12s " % (B, sc) + " | ".join(nm + " " + f(mine_d[(nm,B,sc)]) for nm, x, y in PAIRS))
for B in BUD:
    for a in ARMS:
        print("B=%2d %-18s all %.4f [%.4f, %.4f]" % ((B, a) + mine_tab[(a,B,"all")][:3]))
for s in SCOPES:
    print("scope", s, "positions", LAB["scopes"][s]["positions"], "share %.4f" % LAB["scopes"][s]["share"], "prompts", LAB["scopes"][s]["prompts_with_positions"])
h1, rows1 = load_state(S + r"\strat_smoke.json.state.jsonl")
idx1 = {}
for r in rows1:
    k = (r["arm"], r["budget"], r["gate"], r["prompt_idx"], r["stratum"]); assert k not in idx1; idx1[k] = (r["hits"], r["needed"])
idx2 = {}
for r in rows:
    st = "covered" if r["stratum"] in UN["covered"] else r["stratum"]
    k = (r["arm"], r["budget"], r["gate"], r["prompt_idx"], st)
    h0, n0 = idx2.get(k, (0, 0)); idx2[k] = (h0 + r["hits"], n0 + r["needed"])
mm_h = sum(1 for k in idx1 if k in idx2 and idx2[k][0] != idx1[k][0]); mm_n = sum(1 for k in idx1 if k in idx2 and idx2[k][1] != idx1[k][1])
print("smoke1 rows", len(rows1), "smoke2 collapsed rows", len(idx2), "missing", len(set(idx1) - set(idx2)), "extra", len(set(idx2) - set(idx1)),
      "hits mismatches", mm_h, "needed mismatches", mm_n, "identical dicts", idx1 == idx2)
print("headers: encodings", h1["encoding"], hdr["encoding"], "lambdas equal", h1["lambda_selected"] == hdr["lambda_selected"],
      "harvest shas equal", h1["harvest_npz_sha256"] == hdr["harvest_npz_sha256"])
json.dump({"deltas": {f"{k[0]}|B={k[1]}|{k[2]}": v[:3] for k, v in mine_d.items()},
           "tables": {f"{k[0]}|B={k[1]}|{k[2]}": v[:3] for k, v in mine_tab.items()}}, open(OUT + r"\mine2.json", "w"))

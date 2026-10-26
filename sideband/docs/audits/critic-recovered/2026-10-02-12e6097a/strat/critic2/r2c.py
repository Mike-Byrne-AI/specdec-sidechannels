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

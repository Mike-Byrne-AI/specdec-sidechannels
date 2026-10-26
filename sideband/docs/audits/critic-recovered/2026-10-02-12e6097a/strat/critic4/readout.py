import json, sys
D = json.load(open(sys.argv[1]))
FLOOR = 0.05
def R(d):
    if d["lo"] > 0 and d["delta"] >= FLOOR: return "SIGNAL"
    if d["hi"] < 0: return "NEGATIVE"
    return "NOT-SHOWN"
def f(d): return "%+.4f [%+.4f, %+.4f] %s%s" % (d["delta"], d["lo"], d["hi"], R(d), " STRADDLE" if d["lo"] <= FLOOR <= d["hi"] else "")
SC = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen", "covered", "fallback", "all"]
NAMES = ["address_beyond_token", "gate_eq", "address_beyond_bigram", "bigram_gain", "pt_gain", "d_pt", "d_eq_pt", "d_add_pt",
         "pt_only-free_tok", "history_tok_pt-history_tok", "history_bigram_pt-history_tok_pt"]
for name, r in D.items():
    dl = r["deltas"]; sc = r["scopes"]
    print("=" * 30, name)
    print("scopes:", {s: (sc[s]["positions"], round(sc[s]["share"], 4), sc[s]["prompts_with_positions"]) for s in SC})
    for B in (16, 8, 32):
        print("--- B =", B)
        for nm in NAMES:
            print("  %-34s" % nm, " | ".join("%s %s" % (s, f(dl["%s|B=%d|%s" % (nm, B, s)])) for s in ("all", "covered", "fallback")))
        for nm in ("gate_eq", "pt_gain", "d_pt", "d_eq_pt", "d_add_pt", "address_beyond_token", "bigram_gain", "address_beyond_bigram", "history_tok_pt-history_tok", "history_bigram_pt-history_tok_pt"):
            print("  %-34s" % (nm + " strata"), " | ".join("%s %s" % (s, f(dl["%s|B=%d|%s" % (nm, B, s)])) for s in SC[:6]))
    t = r["arm_tables"]
    print("arms B=16 all:", {a: "%.4f [%.4f, %.4f]" % (t[a + "|B=16|all"]["point"], t[a + "|B=16|all"]["ci_lo"], t[a + "|B=16|all"]["ci_hi"])
                            for a in ["history", "free_tok", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b", "history_bigram_a", "free_all", "history_all", "pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt"]})
    # identity
    s_cov, s_fb = sc["covered"]["share"], sc["fallback"]["share"]
    for B in (8, 16, 32):
        for nm in ("gate_eq", "d_eq_pt", "d_add_pt", "d_pt", "pt_gain"):
            pooled = dl["%s|B=%d|all" % (nm, B)]["delta"]; rec = s_cov * dl["%s|B=%d|covered" % (nm, B)]["delta"] + s_fb * dl["%s|B=%d|fallback" % (nm, B)]["delta"]
            print("  identity", nm, B, "pooled %.15f recon %.15f diff %.2e" % (pooled, rec, pooled - rec))
    # six-strata identity
    pooled = dl["gate_eq|B=16|all"]["delta"]
    rec = sum(sc[s]["share"] * dl["gate_eq|B=16|" + s]["delta"] for s in SC[:6])
    print("  identity six strata gate_eq B16 diff %.2e" % (pooled - rec))
    # covered split
    c12 = sc["covered_1"]["share"] + sc["covered_2_4"]["share"]
    print("  covered_1+covered_2_4 share %.4f" % c12)
    # per prompt min positions for each stratum
    ppp = r["per_prompt_positions"]
    print("  per-prompt positions min/max:", {s: (min(v), max(v), sum(1 for x in v if x == 0)) for s, v in ppp.items()})

import sys, json, collections
sys.path.insert(0, "src")
P = json.load(open("results/real/prefetch_strat_s3.json"))
R = json.load(open("results/real/prefetch_strat_s3_r.json"))
TP = json.load(open("results/real/prefetch_bigram_s3.json"))
TR = json.load(open("results/real/prefetch_bigram_s3_r.json"))
out = []
def chk(name, got, want):
    ok = got == want
    out.append((ok, name, got, want))
f4 = lambda x: f"{x:.4f}"
for X, tag, T in ((P, "P", TP), (R, "R", TR)):
    pv = X["provenance"]; st = pv["strata_counts"]["test"]; L = X["conclusion"]["labels"]
    sc = L["scopes"]
    out.append((None, f"--- {tag}", None, None))
    for s in ("covered", "fallback", "cur_unseen", "prev_unseen", "both_unseen", "covered_1", "covered_2_4", "covered_5p"):
        out.append((None, f"{tag} share {s}", f4(st[s]["share"]), f4(sc[s]["share"])))
        out.append((None, f"{tag} n {s}", st[s]["n"], sc[s]["positions"]))
        out.append((None, f"{tag} prompts {s}", sc[s]["prompts_with_positions"], None))
    for a in ("history", "free_tok", "history_tok", "free_bigram_b", "history_bigram_b", "pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt"):
        out.append((None, f"{tag} arm {a} B=16 all", f4(X["conclusion"]["tables"][f"{a}|B=16|all"]["all"]["point"]), None))
    out.append((None, f"{tag} runtime", round(pv["runtime_s"], 1), None))
    out.append((None, f"{tag} n_state_rows", X["n_state_rows"], None))
    out.append((None, f"{tag} lambda", pv["lambda_selected"], pv["lambda_grid_edge"]))
    # twin's committed B=32 D_eq
    td = T["conclusion"]["deltas"]
    for k in td:
        if k.startswith("gate_eq") and "32" in k:
            out.append((None, f"{tag} twin {k}", f4(td[k]["delta"]), None))
    out.append((None, f"{tag} table_coverage test cur/prev", f4(pv["table_coverage"]["test"]["zero_count_share_cur"]), f4(pv["table_coverage"]["test"]["zero_count_share_prev"])))
    out.append((None, f"{tag} cur_unseen+both", f4(st["cur_unseen"]["share"] + st["both_unseen"]["share"]), f4(st["prev_unseen"]["share"] + st["both_unseen"]["share"])))
    out.append((None, f"{tag} sparse covered share", f4(st["covered_1"]["share"] + st["covered_2_4"]["share"]), None))
    out.append((None, f"{tag} reproduce", L["reproduce"]["n_compared"], L["reproduce"]["status"]))
    out.append((None, f"{tag} train singleton share cur", f4(pv["table_coverage"]["train"]["singleton_key_share_cur"]), None))
    out.append((None, f"{tag} label", L["label"], L["sentence"] == P["conclusion"]["labels"]["sentence"]))
    out.append((None, f"{tag} straddles cov/fb/eqpt/addpt/q2/dpt/neg", (L["covered_floor_straddle"], L["fallback_floor_straddle"], L["d_eq_pt_floor_straddle"], L["d_add_pt_floor_straddle"], L["q2_floor_straddle"], L["d_pt_floor_straddle"], L["covered_negative"]), None))
    out.append((None, f"{tag} readings eq/dpt/eqpt", (L["gate_eq_readings"], ), None))
    out.append((None, f"{tag} dpt readings", L["d_pt_readings"], L["d_eq_pt_readings"]))
for r in out:
    print(r[1], "|", r[2], "|", r[3])

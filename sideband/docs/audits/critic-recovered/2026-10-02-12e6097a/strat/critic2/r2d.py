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

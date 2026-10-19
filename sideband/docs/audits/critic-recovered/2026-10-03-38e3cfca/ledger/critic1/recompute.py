import json, sys, collections
ROOT = r"C:\Users\<user>\Desktop\Research\sideband"
for tag, f in [("P", "results/real/prefetch_strat_s3.json"), ("R", "results/real/prefetch_strat_s3_r.json")]:
    pay = json.load(open(ROOT + "/" + f, encoding="utf-8"))
    rows = []
    with open(ROOT + "/" + f + ".state.jsonl", encoding="utf-8") as fh:
        hdr = json.loads(fh.readline())
        for line in fh:
            rows.append(json.loads(line))
    print("=====", tag, "rows", len(rows), "payload n_state_rows", pay["n_state_rows"])
    arms = sorted(set(r["arm"] for r in rows)); keys = sorted(set(r["key"] for r in rows)); buds = sorted(set(r["budget"] for r in rows))
    print("arms", arms, "keys", keys, "budgets", buds, "depths", sorted(set(str(r["depth"]) for r in rows)))
    # pooled hit rates by (arm,budget,key=1,scope)
    COV = ["covered_1", "covered_2_4", "covered_5p"]; FB = ["cur_unseen", "prev_unseen", "both_unseen"]
    scopes = {s: [s] for s in COV + FB}; scopes["covered"] = COV; scopes["fallback"] = FB; scopes["all"] = COV + FB
    H = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r["key"] != 1: continue
        for sc, mem in scopes.items():
            if r["stratum"] in mem:
                h = H[(r["arm"], r["budget"], sc)]; h[0] += r["hits"]; h[1] += r["needed"]
    def rate(a, b, sc):
        h = H[(a, b, sc)]; return h[0] / h[1]
    defs = {"gate_eq": ("history_tok", "free_bigram_b"), "d_eq_pt": ("history_tok_pt", "free_bigram_pt"),
            "d_add_pt": ("history_bigram_pt", "free_bigram_pt"), "d_pt": ("history_tok", "free_bigram_pt"),
            "pt_gain": ("free_bigram_pt", "free_bigram_b")}
    maxd = 0.0; n = 0
    for nm, (a, b) in defs.items():
        for sc in scopes:
            for B in buds:
                k = f"{nm}|B={B}|{sc}"
                if k not in pay["conclusion"]["deltas"]: continue
                mine = rate(a, B, sc) - rate(b, B, sc)
                d = abs(mine - pay["conclusion"]["deltas"][k]["delta"]); maxd = max(maxd, d); n += 1
                if d > 1e-12: print("MISMATCH", k, mine, pay["conclusion"]["deltas"][k]["delta"])
    print("point-estimate recompute: n", n, "max abs discrepancy", maxd)
    # strata position shares at test from needed at one arm/budget/key/gate
    one = [r for r in rows if r["arm"] == "free_bigram_b" and r["budget"] == 16 and r["key"] == 1 and r["gate"] == 0]
    tot = sum(r["needed"] for r in one)
    by = collections.Counter()
    for r in one: by[r["stratum"]] += r["needed"]
    for s in COV + FB: print(" share", s, round(by[s] / tot, 4))
    print(" covered", round(sum(by[s] for s in COV) / tot, 4), "fallback", round(sum(by[s] for s in FB) / tot, 4))
    bu = collections.Counter()
    for r in one:
        if r["stratum"] == "both_unseen": bu[r["prompt_idx"]] += r["needed"]
    tb = sum(bu.values())
    top = bu.most_common(3)
    print(" both_unseen prompts", len(bu), "top", [(p, round(c / tb, 4)) for p, c in top])
    # check same at all gates/arms
    shares13 = set()
    for arm in arms:
        for g in sorted(set(r["gate"] for r in rows)):
            sub = [r for r in rows if r["arm"] == arm and r["budget"] == 16 and r["key"] == 1 and r["gate"] == g and r["stratum"] == "both_unseen"]
            t = sum(r["needed"] for r in sub); c = sum(r["needed"] for r in sub if r["prompt_idx"] == 13)
            shares13.add(round(c / t, 10))
    print(" prompt-13 share invariant across arms/gates:", shares13)
    # both_unseen gate_eq
    print(" both_unseen gate_eq", round(rate("history_tok", 16, "both_unseen") - rate("free_bigram_b", 16, "both_unseen"), 4))
    print(" hit rates B16 all:", {a: round(rate(a, 16, "all"), 4) for a in arms})
    print(" runtime_s", pay["provenance"]["runtime_s"])

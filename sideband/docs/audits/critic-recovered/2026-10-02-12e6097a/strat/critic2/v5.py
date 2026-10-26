import sys, types
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
import run_prefetch_strat as rs
L, E, K = 16, 64, 8
# (1) occurrence bins: token t has occ[t] train occurrences in TABLE_CUR, pocc[t] in TABLE_PREV
V = 12
occ  = np.array([0, 1, 2, 4, 5, 9, 1, 7, 3, 0, 6, 1])
pocc = np.array([0, 5, 9, 4, 5, 1, 0, 2, 3, 3, 0, 1])
tt = np.zeros((V, L, E), np.int64); pt = np.zeros((V, L, E), np.int64)
for v in range(V):
    tt[v, :, :K] = occ[v]; pt[v, :, :K] = pocc[v]          # each occurrence adds 1 to K experts at each of L gates = 128
tokens = np.array([[3, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]])
fake = types.SimpleNamespace(d=types.SimpleNamespace(tokens=tokens), token_table=tt, prev_table=pt)
anchors = np.arange(1, tokens.shape[1]); rows = np.zeros_like(anchors)
m = rs.Strat.strata_masks(fake, rows, anchors)
got = {int(a): [s for s in rs.STRATA if m[s][i]] for i, a in enumerate(anchors)}
bad = 0
for i, a in enumerate(anchors):
    c, p = occ[tokens[0, a]], pocc[tokens[0, a - 1]]
    if c == 0 and p == 0: want = "both_unseen"
    elif c == 0: want = "cur_unseen"
    elif p == 0: want = "prev_unseen"
    else:
        o = min(c, p); want = "covered_1" if o == 1 else "covered_2_4" if o <= 4 else "covered_5p"
    if got[int(a)] != [want]: bad += 1; print("BIN MISMATCH", a, c, p, got[int(a)], want)
print("occurrence-bin cases", len(anchors), "mismatches", bad, "bins hit", sorted({g[0] for g in got.values()}))
# (2) a void payload (REPRODUCE-INVALID) built on a PT-INCONSISTENT / NEGATIVE-covered row set: which reading-derived fields survive?
def mk(rates, per=100, prompts=(0, 1), default=0.80):
    out = []
    for arm in rs.ARMS_REQUIRED:
        for s in rs.STRATA:
            r = rates.get(arm, {}).get(s, default)
            for p in prompts:
                for g in range(L):
                    out.append({"arm": arm, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "stratum": s, "hits": int(round(per * r)), "needed": per})
    return out
cov = ("covered_1", "covered_2_4", "covered_5p"); fbk = ("cur_unseen", "prev_unseen", "both_unseen")
sp = lambda a, b: {**{s: a for s in cov}, **{s: b for s in fbk}}
fl = lambda a: {s: a for s in rs.STRATA}
rows = mk({"history_tok": sp(0.80, 0.95), "free_bigram_b": sp(0.90, 0.70), "history_tok_pt": fl(0.88), "history_bigram_pt": fl(0.84)})
def twin_of(rows):
    acc = {}
    for r in rows:
        if r["arm"] not in rs.ARMS_TWIN: continue
        k = (r["arm"], r["budget"], r["gate"], r["prompt_idx"]); h, n = acc.get(k, (0, 0)); acc[k] = (h + r["hits"], n + r["needed"])
    return [{"arm": a, "budget": B, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "hits": h, "needed": n} for (a, B, g, p), (h, n) in acc.items()]
tw = twin_of(rows); tw[0] = dict(tw[0], needed=tw[0]["needed"] + 1)
lab = rs.conclude(rows, "prev_table", tw, n_boot=200, budgets=(16,))["labels"]
keep = {k: lab[k] for k in ("label", "void", "q1", "q2", "covered_negative", "pt_inconsistent_cause", "covered_floor_straddle",
                            "d_eq_pt_floor_straddle", "d_add_pt_floor_straddle", "d_pt_floor_straddle", "gate_eq_covered_reading")}
print("VOID payload label fields:", keep)
# (3) straddles on the BRANCH deltas: D_eq^FB and D_add^PT straddle while the gates do not
rows = mk({"history_tok": sp(0.83, 0.88), "free_bigram_b": sp(0.80, 0.80), "history_tok_pt": fl(0.84), "history_bigram_pt": fl(0.86)}, prompts=(0,)) + \
       mk({"history_tok": sp(0.83, 0.84), "free_bigram_b": sp(0.80, 0.80), "history_tok_pt": fl(0.84), "history_bigram_pt": fl(0.88)}, prompts=(1,))
c = rs.conclude(rows, "prev_table", None, n_boot=200, budgets=(16,)); lab = c["labels"]
f = lambda d: "%+.4f [%+.4f, %+.4f]" % (d["delta"], d["lo"], d["hi"])
print("branch-straddle case: label", lab["label"], "| D_eq^COV", f(lab["gate_eq_covered"]), "straddle", lab["covered_floor_straddle"],
      "| D_eq^FB", f(lab["gate_eq_fallback"]), lab["gate_eq_fallback_reading"], "| D_eq^PT", f(lab["d_eq_pt_all"]), lab["d_eq_pt_all_reading"],
      "straddle", lab["d_eq_pt_floor_straddle"], "| D_add^PT", f(lab["d_add_pt_all"]), lab["d_add_pt_all_reading"], "straddle", lab["d_add_pt_floor_straddle"])
print("  fallback straddle field present:", any("fallback" in k and "straddle" in k for k in lab))
print("  sentence:", lab["sentence"])

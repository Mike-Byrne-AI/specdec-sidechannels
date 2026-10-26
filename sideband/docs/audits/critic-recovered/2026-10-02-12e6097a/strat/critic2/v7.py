import sys
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import run_prefetch_strat as rs
L = 16
def mk(rates, per=1000, prompts=(0,), default=0.80):
    out = []
    for arm in rs.ARMS_REQUIRED:
        for s in rs.STRATA:
            r = rates.get(arm, {}).get(s, default)
            for p in prompts:
                for g in range(L):
                    out.append({"arm": arm, "budget": 16, "key": 1, "depth": None, "gate": g, "prompt_idx": p, "stratum": s, "hits": int(round(per * r)), "needed": per})
    return out
fl = lambda a: {s: a for s in rs.STRATA}
cov = ("covered_1", "covered_2_4", "covered_5p"); fbk = ("cur_unseen", "prev_unseen", "both_unseen")
sp = lambda a, b: {**{s: a for s in cov}, **{s: b for s in fbk}}
base = {"history_tok": sp(0.83, 0.95), "free_bigram_b": sp(0.80, 0.80)}
rows = mk({**base, "history_tok_pt": fl(0.840), "history_bigram_pt": fl(0.843)}, prompts=(0,)) + \
       mk({**base, "history_tok_pt": fl(0.840), "history_bigram_pt": fl(0.853)}, prompts=(1,))
lab = rs.conclude(rows, "prev_table", None, n_boot=200, budgets=(16,))["labels"]
f = lambda d: "%+.4f [%+.4f, %+.4f]" % (d["delta"], d["lo"], d["hi"])
print("label", lab["label"])
print("D_eq^PT", f(lab["d_eq_pt_all"]), lab["d_eq_pt_all_reading"], "straddle", lab["d_eq_pt_floor_straddle"])
print("D_add^PT", f(lab["d_add_pt_all"]), lab["d_add_pt_all_reading"], "straddle", lab["d_add_pt_floor_straddle"])
print("sentence Q2:", lab["sentence"].split("; ", 1)[1])

import pickle, sys, json
res = pickle.load(open(sys.argv[1], "rb"))
f = lambda d: "%+.4f [%+.4f, %+.4f]" % (d["delta"], d["lo"], d["hi"])
names = ["shrinkage", "gate_eq", "gate_eq_r2", "gate_eq_r2_twinarm", "d_add_r2", "d_eq_h", "d_add_h", "history_all_h-history_bigram_r2",
         "free_h-free_r2", "history_tok_r2-history_tok", "backoff-free_bigram", "replay-free_bigram", "free_r2-free_backoff", "free_r2-free_replay",
         "replay_cur-free_tok", "replay_zerofit-free_tok", "h_only-free_tok", "h_only-history_tok", "address_beyond_bigram"]
for nm in ("prefetch_r2_s3", "prefetch_r2_s3_r"):
    D = res[nm]["D"]
    print("=====", nm)
    for B in (16,):
        for s in ("all", "covered", "fallback", "covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"):
            print("B=%d %-12s" % (B, s), " | ".join("%s %s" % (n, f(D["%s|B=%d|%s" % (n, B, s)])) for n in names[:9]))
            print("               ", " | ".join("%s %s" % (n, f(D["%s|B=%d|%s" % (n, B, s)])) for n in names[9:]))
    for B in (8, 32):
        for s in ("all", "fallback", "covered"):
            print("B=%d %-9s" % (B, s), " | ".join("%s %s" % (n, f(D["%s|B=%d|%s" % (n, B, s)])) for n in ("gate_eq_r2", "d_eq_h", "d_add_h", "shrinkage", "free_h-free_r2", "history_all_h-history_bigram_r2", "history_tok_r2-history_tok")))
    print("points B=16 all:")
    for a, t in sorted(res[nm]["pts"].items()):
        print("   %-18s %.4f [%.4f, %.4f]   fallback %.4f" % (a, t["point"], t["ci_lo"], t["ci_hi"], res[nm]["pts_fb"][a]["point"]))

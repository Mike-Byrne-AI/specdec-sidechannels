# UNREGISTERED critic diagnostics (license nothing): cluster concentration, leave-one-prompt-out on label cells.
import sys, json
import numpy as np
sys.path.insert(0, "C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/critic4")
import recompute as rc
ROOT = rc.ROOT
for name in ("prefetch_strat_s3", "prefetch_strat_s3_r"):
    r = rc.recompute(name)
    H, N = r["H"].astype(float), r["N"].astype(float)
    P = r["prompts"]; ai = {a: i for i, a in enumerate(rc.ARMS)}; si = {s: i for i, s in enumerate(rc.STRATA)}
    b16 = 1
    pos = {s: N[ai["history_tok"], b16, si[s], 0] / 8 for s in rc.STRATA}
    fb = pos["cur_unseen"] + pos["prev_unseen"] + pos["both_unseen"]
    top = int(np.argmax(pos["both_unseen"]))
    print("=====", name)
    print("both_unseen top prompt", P[top], "positions", pos["both_unseen"][top], "of", pos["both_unseen"].sum(),
          "share %.4f" % (pos["both_unseen"][top] / pos["both_unseen"].sum()))
    o = np.argsort(-fb)[:3]
    print("fallback top prompts", [(P[i], int(fb[i]), round(fb[i] / fb.sum(), 4)) for i in o], "total", int(fb.sum()))
    def delta(a, b, strata, drop=None):
        idx = [si[s] for s in strata]
        ha = H[ai[a], b16][idx].sum(axis=(0, 1)); hb = H[ai[b], b16][idx].sum(axis=(0, 1)); n = N[ai[a], b16][idx].sum(axis=(0, 1))
        keep = np.ones(30, bool)
        if drop is not None:
            keep[drop] = False
        return (ha - hb)[keep].sum() / n[keep].sum()
    cells = {"D_eq^COV": ("history_tok", "free_bigram_b", rc.UNIONS["covered"]), "D_eq^FB": ("history_tok", "free_bigram_b", rc.UNIONS["fallback"]),
             "D_eq^PT": ("history_tok_pt", "free_bigram_pt", rc.STRATA), "D_add^PT": ("history_bigram_pt", "free_bigram_pt", rc.STRATA),
             "D_eq both_unseen": ("history_tok", "free_bigram_b", ["both_unseen"])}
    for k, (a, b, st) in cells.items():
        full = delta(a, b, st)
        loo = [delta(a, b, st, drop=i) for i in range(30)]
        print("  %-18s full %+.4f  drop-top-both-unseen-prompt %+.4f  LOO min %+.4f max %+.4f" % (k, full, delta(a, b, st, drop=top), min(loo), max(loo)))
    pay = json.load(open(ROOT + "/results/real/" + name + ".json", encoding="utf-8"))
    tc = pay["provenance"]["table_coverage"]["test"]; sc = pay["conclusion"]["labels"]["scopes"]
    print("  cu share (cur_unseen+both) %.6f vs zero_count_share_cur %.6f ; pu %.6f vs %.6f" % (
        sc["cur_unseen"]["share"] + sc["both_unseen"]["share"], tc["zero_count_share_cur"],
        sc["prev_unseen"]["share"] + sc["both_unseen"]["share"], tc["zero_count_share_prev"]))
    print("  expected rows 13*3*16*(30*6 - empty) =", 13 * 3 * 16 * (30 * 6 - int((N[0, 0, :, 0, :] == 0).sum())), "actual", r["rows"])

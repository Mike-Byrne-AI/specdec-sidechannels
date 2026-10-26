# Independent recompute of the R2 payloads from their state files (critic, recompute mode).
import sys, json, math
sys.path.insert(0, "src")
import numpy as np
from sideband.stats import paired_cluster_delta_ci, cluster_bootstrap_ci
from sideband.harvest import split_of_prompt

STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UNIONS = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + list(UNIONS)
BUDGETS = [8, 16, 32]
LB = 16; MAT = 0.05; NB = 2000; SEED = 0; L = 16; K = 8
TWIN = ["history", "free_tok", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b", "history_bigram_a", "free_all", "history_all"]
R2 = ["free_r2", "history_tok_r2", "history_bigram_r2", "free_backoff", "free_replay", "replay_cur", "replay_zerofit", "h_only", "free_h", "history_all_h"]
RIDGE_R2 = [a for a in R2 if a != "replay_zerofit"]
LAMS = [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
KTAGS = ["0", "2", "8", "32", "128", "512", "inf"]
FREE, HIST = "free_bigram_b", "history_bigram_b"
PAIRS = [("address_beyond_token", "history_tok", "free_tok"), ("gate_eq", "history_tok", FREE), ("address_beyond_bigram", HIST, FREE),
         ("bigram_gain", FREE, "free_tok"), ("shrinkage", "free_r2", FREE), ("gate_eq_r2", "history_tok_r2", "free_r2"),
         ("gate_eq_r2_twinarm", "history_tok", "free_r2"), ("d_add_r2", "history_bigram_r2", "free_r2"),
         ("backoff-free_bigram", "free_backoff", FREE), ("replay-free_bigram", "free_replay", FREE),
         ("free_r2-free_backoff", "free_r2", "free_backoff"), ("free_r2-free_replay", "free_r2", "free_replay"),
         ("replay_cur-free_tok", "replay_cur", "free_tok"), ("replay_zerofit-free_tok", "replay_zerofit", "free_tok"),
         ("history_tok_r2-history_tok", "history_tok_r2", "history_tok"), ("h_only-free_tok", "h_only", "free_tok"),
         ("h_only-history_tok", "h_only", "history_tok"), ("free_h-free_r2", "free_h", "free_r2"),
         ("d_eq_h", "history_bigram_r2", "free_h"), ("d_add_h", "history_all_h", "free_h"),
         ("history_all_h-history_bigram_r2", "history_all_h", "history_bigram_r2")]


def load(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return json.loads(lines[0]), [json.loads(x) for x in lines[1:] if x.strip()]


def reading(d):
    if d["lo"] > 0 and d["delta"] >= MAT:
        return "SIGNAL"
    if d["hi"] < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"


def straddle(d):
    return d["lo"] <= MAT <= d["hi"]


def run(name):
    pay = json.load(open(f"results/real/{name}.json", encoding="utf-8"))
    hdr, rows = load(f"results/real/{name}.json.state.jsonl")
    prov, conc = pay["provenance"], pay["conclusion"]
    out = {"name": name}
    assert len(rows) == pay["n_state_rows"]
    out["n_rows"] = len(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    P = len(prompts); pidx = {p: i for i, p in enumerate(prompts)}
    out["n_prompts"] = P
    out["prompts_all_test"] = all(split_of_prompt(p) == "test" for p in prompts)
    arms = sorted({r["arm"] for r in rows})
    out["arms"] = arms
    H = {}; N = {}; seen = set(); dup = 0
    for r in rows:
        key = (r["arm"], int(r["budget"]), r["stratum"], int(r["gate"]), int(r["prompt_idx"]))
        if key in seen:
            dup += 1
        seen.add(key)
        a = (r["arm"], int(r["budget"]))
        if a not in H:
            H[a] = np.zeros((6, L, P)); N[a] = np.zeros((6, L, P))
        s = STRATA.index(r["stratum"])
        H[a][s, int(r["gate"]), pidx[int(r["prompt_idx"])]] += int(r["hits"])
        N[a][s, int(r["gate"]), pidx[int(r["prompt_idx"])]] += int(r["needed"])
        assert 0 <= int(r["hits"]) <= int(r["needed"])
    out["dup_rows"] = dup

    def scope_arr(arm, B, scope):
        idx = [STRATA.index(s) for s in (UNIONS[scope] if scope in UNIONS else [scope])]
        return H[(arm, B)][idx].sum(axis=0), N[(arm, B)][idx].sum(axis=0)

    acc = {"mx": 0.0, "n": 0, "worst": None}
    def cmp(a, b, tag):
        acc["n"] += 1
        dd = abs(float(a) - float(b))
        if dd > acc["mx"]:
            acc["mx"], acc["worst"] = dd, tag
    tkeys = set()
    for arm in arms:
        for B in BUDGETS:
            for scope in SCOPES:
                h, n = scope_arr(arm, B, scope)
                key = f"{arm}|B={B}|{scope}"; tkeys.add(key)
                t = conc["tables"][key]
                for g in range(L):
                    if n[g].sum() == 0:
                        continue
                    lo, hi = cluster_bootstrap_ci(h[g], n[g], n_boot=NB, seed=SEED)
                    pg = t["per_gate"][str(g)]
                    cmp(h[g].sum() / n[g].sum(), pg["point"], key + f"|g{g}|pt"); cmp(lo, pg["ci_lo"], key + "lo"); cmp(hi, pg["ci_hi"], key + "hi"); cmp(n[g].sum(), pg["needed"], key + "n")
                Hs, Ns = h.sum(axis=0), n.sum(axis=0)
                lo, hi = cluster_bootstrap_ci(Hs, Ns, n_boot=NB, seed=SEED)
                cmp(Hs.sum() / Ns.sum(), t["all"]["point"], key + "|pt"); cmp(lo, t["all"]["ci_lo"], key + "|lo"); cmp(hi, t["all"]["ci_hi"], key + "|hi"); cmp(Ns.sum(), t["all"]["needed"], key + "|n")
    out["table_keys_equal"] = tkeys == set(conc["tables"])
    pairing_ok = True
    D = {}
    for B in BUDGETS:
        for scope in SCOPES:
            ref = scope_arr("history_tok", B, scope)[1].sum(axis=0)
            for arm in arms:
                if not np.array_equal(scope_arr(arm, B, scope)[1].sum(axis=0), ref):
                    pairing_ok = False
            for nm, a, b in PAIRS:
                ha, na = scope_arr(a, B, scope); hb, nb = scope_arr(b, B, scope)
                Ha, Na, Hb, Nb = ha.sum(0), na.sum(0), hb.sum(0), nb.sum(0)
                assert np.array_equal(Na, Nb)
                dlt, lo, hi = paired_cluster_delta_ci(Ha, Hb, Na, n_boot=NB, seed=SEED)
                D[f"{nm}|B={B}|{scope}"] = {"delta": dlt, "lo": lo, "hi": hi, "needed": int(Na.sum())}
    out["pairing_ok"] = pairing_ok
    out["delta_keys_equal"] = set(D) == set(conc["deltas"])
    for k, v in D.items():
        for f in ("delta", "lo", "hi", "needed"):
            cmp(v[f], conc["deltas"][k][f], k + "|" + f)
    out["_cmp"] = cmp; out["_scope_arr"] = scope_arr; out["_acc"] = acc
    return pay, hdr, rows, D, out


def finish(pay, hdr, rows, D, out):
    cmp, scope_arr, acc = out.pop("_cmp"), out.pop("_scope_arr"), out.pop("_acc")
    prov, conc = pay["provenance"], pay["conclusion"]
    lab = conc["labels"]
    allN = scope_arr("history_tok", LB, "all")[1].sum()
    for scope in SCOPES:
        n = scope_arr("history_tok", LB, scope)[1]
        cmp(round(n.sum() / (L * K)), lab["scopes"][scope]["positions"], scope + "|pos")
        cmp(n.sum() / allN, lab["scopes"][scope]["share"], scope + "|share")
        cmp(int((n.sum(0) > 0).sum()), lab["scopes"][scope]["prompts_with_positions"], scope + "|prompts")
    st = prov["strat"]
    _, srows = load(st["state_path"])
    def idx(rr):
        return {(r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]), r["stratum"]): (int(r["hits"]), int(r["needed"])) for r in rr if r["arm"] in TWIN}
    mine, theirs = idx(rows), idx(srows)
    hmm = sum(1 for k in theirs if k in mine and mine[k][0] != theirs[k][0])
    nmm = sum(1 for k in theirs if k in mine and mine[k][1] != theirs[k][1])
    out["reproduce"] = {"strat_twin_rows": len(theirs), "r2_twin_rows": len(mine), "missing": len(set(theirs) - set(mine)), "extra": len(set(mine) - set(theirs)), "hits_mm": hmm, "needed_mm": nmm, "strat_rows_total": len(srows), "strat_arms": sorted({r["arm"] for r in srows})}
    cmp(len(theirs), lab["reproduce"]["n_strat_rows"], "rep n"); cmp(hmm, lab["reproduce"]["hits_mismatch_rows"], "rep h"); cmp(nmm, lab["reproduce"]["needed_mismatch_rows"], "rep n2")
    spay = json.load(open(st["path"], encoding="utf-8"))
    idmax = 0.0
    for scope in ("all", "covered", "fallback"):
        theirs_c = spay["conclusion"]["deltas"][f"gate_eq|B={LB}|{scope}"]
        for f in ("delta", "lo", "hi"):
            idmax = max(idmax, abs(D[f"gate_eq|B={LB}|{scope}"][f] - theirs_c[f]))
            idmax = max(idmax, abs(st["gate_eq"][scope][f] - theirs_c[f]))
    out["identity_max_abs"] = idmax
    stab = 0.0; nst = 0
    for arm in TWIN:
        for B in BUDGETS:
            for scope in SCOPES:
                key = f"{arm}|B={B}|{scope}"
                if key in spay["conclusion"]["tables"]:
                    nst += 1
                    for f in ("point", "ci_lo", "ci_hi", "needed"):
                        stab = max(stab, abs(spay["conclusion"]["tables"][key]["all"][f] - conc["tables"][key]["all"][f]))
    out["twin_tables_vs_strat_max_abs"] = (stab, nst)
    sd = 0.0; nsd = 0
    for k, v in spay["conclusion"]["deltas"].items():
        if k in conc["deltas"]:
            nsd += 1
            for f in ("delta", "lo", "hi", "needed"):
                sd = max(sd, abs(v[f] - conc["deltas"][k][f]))
    out["shared_deltas_vs_strat_max_abs"] = (sd, nsd)
    kv = prov["k_val_table"]
    best = -math.inf; bk = bl = None
    for kt in KTAGS:
        for lam in LAMS:
            v = kv[kt][str(lam)]
            if v > best:
                best, bk, bl = v, kt, lam
    out["k_reselect"] = (bk, bl, best)
    out["k_ok"] = (bk == prov["k_selected"] and bl == prov["lambda_selected"]["free_r2"] and prov["k_grid_edge"] == (bk in ("0", "inf")))
    out["free_r2_val_row_is_k_row"] = prov["val_table"]["free_r2"] == kv[bk]
    lam_ok = {}
    for arm in RIDGE_R2:
        vt = prov["val_table"][arm]
        b = -math.inf; bl2 = None
        for lam in LAMS:
            if vt[str(lam)] > b:
                b, bl2 = vt[str(lam)], lam
        edge = bl2 in (LAMS[0], LAMS[-1])
        lam_ok[arm] = (bl2, prov["lambda_selected"][arm], bl2 == prov["lambda_selected"][arm], edge, prov["lambda_grid_edge"][arm] == edge)
    out["lambda_reselect"] = lam_ok
    out["twin_lambdas_eq_strat"] = all(prov["lambda_selected"][a] == st["lambda_selected"][a] for a in TWIN)
    return lab, mine, theirs, hmm, nmm, idmax


def labels(pay, hdr, D, out, lab, mine, theirs, hmm, nmm, idmax):
    conc = pay["conclusion"]
    def d(nm, s, B=LB):
        return D[f"{nm}|B={B}|{s}"]
    fb, al, eqh, addh = d("gate_eq_r2", "fallback"), d("gate_eq_r2", "all"), d("d_eq_h", "all"), d("d_add_h", "all")
    q1 = "R2-FALLBACK-SURVIVES" if reading(fb) == "SIGNAL" else ("R2-POOLED-ONLY" if reading(al) == "SIGNAL" else "R2-ABSORBED")
    e = reading(eqh) == "SIGNAL"
    u = reading(addh) == "SIGNAL"
    if e and u:
        q2 = "H-SURVIVES"
    elif u:
        q2 = "H-COMPLEMENTARY"
    elif not e:
        q2 = "H-ABSORBS"
    else:
        q2 = "H-INCONSISTENT"
    hg, anc = d("free_h-free_r2", "all"), d("history_all_h-history_bigram_r2", "all")
    hand_all, hand_fb = d("history_tok_r2-history_tok", "all"), d("history_tok_r2-history_tok", "fallback")
    exact = (hmm == 0 and nmm == 0 and idmax <= 1e-12 and len(set(theirs) ^ set(mine)) == 0)
    m = {
        "q1": q1, "q2": q2, "label": q1 + " / " + q2,
        "gate_eq_r2_fallback_reading": reading(fb), "gate_eq_r2_all_reading": reading(al),
        "d_eq_h_all_reading": reading(eqh), "d_add_h_all_reading": reading(addh),
        "fallback_floor_straddle": straddle(fb), "all_floor_straddle": straddle(al),
        "d_eq_h_floor_straddle": straddle(eqh), "d_add_h_floor_straddle": straddle(addh),
        "q2_floor_straddle": straddle(eqh) or straddle(addh),
        "shrinkage_floor_straddle": {s: straddle(d("shrinkage", s)) for s in ("fallback", "covered", "all")},
        "shrinkage_readings": {s: reading(d("shrinkage", s)) for s in SCOPES},
        "gate_eq_r2_readings": {s: reading(d("gate_eq_r2", s)) for s in SCOPES},
        "d_eq_h_readings": {s: reading(d("d_eq_h", s)) for s in SCOPES},
        "q2_reader_guard": (hg["hi"] < 0) or (anc["hi"] < 0),
        "address_handicap": (hand_all["hi"] < 0) or (hand_fb["hi"] < 0),
        "k_at_replay_end": hdr["k_selected"] == "inf",
        "gate_eq_r2_covered_reading": reading(d("gate_eq_r2", "covered")),
        "free_h_gain_reading": reading(hg), "h_anchor_reading": reading(anc),
        "address_handicap_reading": reading(hand_all), "address_handicap_fallback_reading": reading(hand_fb),
        "d_add_h_fallback_reading": reading(d("d_add_h", "fallback")),
        "d_add_r2_floor_straddle": straddle(d("d_add_r2", "all")),
        "d_add_r2_fallback_floor_straddle": straddle(d("d_add_r2", "fallback")),
        "fallback_negative": reading(fb) == "NEGATIVE", "all_negative": reading(al) == "NEGATIVE",
        "h_negative": (reading(eqh) == "NEGATIVE") or (reading(addh) == "NEGATIVE"),
        "reproduce_status": "EXACT" if exact else "NOT-EXACT",
        "void": False, "h_inconsistent_cause": None,
    }
    mm = {}
    for k, v in m.items():
        if lab.get(k) != v:
            mm[k] = (v, lab.get(k))
    out["label_field_mismatches"] = mm
    out["n_label_fields_compared"] = len(m)
    out["SHARE_mine"] = d("shrinkage", "fallback")["delta"] / d("gate_eq", "fallback")["delta"]
    out["SHARE_payload"] = lab["shrinkage_share_of_fallback_margin"]
    said = []
    for nm, s in (("gate_eq_r2", "fallback"), ("gate_eq_r2", "all"), ("d_eq_h", "all"), ("d_add_h", "all")):
        for B in (8, 32):
            if reading(d(nm, s, B)) != reading(d(nm, s)):
                said.append(nm + "|B=" + str(B) + "|" + s + ": " + reading(d(nm, s, B)))
    def pt(arm):
        return conc["tables"][arm + "|B=16|all"]["all"]["point"]
    my_said = {"b8_b32_disagree": said,
               "limit_arm_above_free_r2": [a for a in ("free_backoff", "free_replay") if pt(a) > pt("free_r2")],
               "h_only_above_history_tok": pt("h_only") > pt("history_tok"),
               "replay_zerofit_all_point": pt("replay_zerofit")}
    out["said_match"] = (my_said == lab["said_in_words"])
    out["said"] = my_said
    out["pts"] = {a: conc["tables"][a + "|B=16|all"]["all"] for a in out["arms"]}
    out["pts_fb"] = {a: conc["tables"][a + "|B=16|fallback"]["all"] for a in out["arms"]}
    out["D"] = D


if __name__ == "__main__":
    import pickle
    res = {}
    for name in ("prefetch_r2_s3", "prefetch_r2_s3_r"):
        pay, hdr, rows, D, out = run(name)
        acc = out["_acc"]
        lab, mine, theirs, hmm, nmm, idmax = finish(pay, hdr, rows, D, out)
        labels(pay, hdr, D, out, lab, mine, theirs, hmm, nmm, idmax)
        a = abs(out["SHARE_mine"] - out["SHARE_payload"])
        out["max_abs_discrepancy"] = max(acc["mx"], a)
        out["n_values_compared"] = acc["n"] + 1
        out["worst"] = acc["worst"]
        res[name] = out
        print("=====", name)
        for k, v in out.items():
            if k in ("D", "pts", "pts_fb"):
                continue
            print(k, "=", v)
    pickle.dump(res, open(sys.argv[1], "wb"))

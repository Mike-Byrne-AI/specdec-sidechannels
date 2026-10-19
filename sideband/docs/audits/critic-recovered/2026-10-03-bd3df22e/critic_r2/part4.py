

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

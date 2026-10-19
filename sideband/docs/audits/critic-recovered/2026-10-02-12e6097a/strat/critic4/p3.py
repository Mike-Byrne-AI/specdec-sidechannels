
def R(d):
    return reading(d["delta"], d["lo"], d["hi"])

def S(d):
    return straddle(d["lo"], d["hi"])

def labels_of(deltas):
    L = {}
    cov, fb = deltas["gate_eq|B=16|covered"], deltas["gate_eq|B=16|fallback"]
    eqpt, addpt = deltas["d_eq_pt|B=16|all"], deltas["d_add_pt|B=16|all"]
    dpt, anc = deltas["d_pt|B=16|all"], deltas["history_bigram_pt-history_tok_pt|B=16|all"]
    L["gate_eq_covered_reading"], L["gate_eq_fallback_reading"] = R(cov), R(fb)
    L["d_eq_pt_all_reading"], L["d_add_pt_all_reading"], L["d_pt_all_reading"] = R(eqpt), R(addpt), R(dpt)
    L["gate_eq_readings"] = {s: R(deltas["gate_eq|B=16|" + s]) for s in SCOPES}
    L["d_pt_readings"] = {s: R(deltas["d_pt|B=16|" + s]) for s in SCOPES}
    L["d_eq_pt_readings"] = {s: R(deltas["d_eq_pt|B=16|" + s]) for s in SCOPES}
    L["covered_floor_straddle"], L["fallback_floor_straddle"] = S(cov), S(fb)
    L["d_eq_pt_floor_straddle"], L["d_add_pt_floor_straddle"], L["d_pt_floor_straddle"] = S(eqpt), S(addpt), S(dpt)
    L["q2_floor_straddle"] = bool(S(eqpt) or S(addpt))
    L["covered_negative"] = R(cov) == "NEGATIVE"
    if R(cov) == "SIGNAL":
        q1 = "COVERED-MATERIAL"
    elif R(fb) == "SIGNAL":
        q1 = "FALLBACK-LOCATED"
    else:
        q1 = "UNLOCATED"
    e = R(eqpt) == "SIGNAL"
    a_ = R(addpt) == "SIGNAL"
    if e and a_:
        q2 = "PT-SURVIVES"
    elif a_:
        q2 = "PT-COMPLEMENTARY"
    elif not e:
        q2 = "PT-ABSORBS"
    else:
        q2 = "PT-INCONSISTENT"
    L["q1"], L["q2"], L["label"] = q1, q2, q1 + " / " + q2
    if q2 != "PT-INCONSISTENT":
        L["pt_inconsistent_cause"] = None
    else:
        L["pt_inconsistent_cause"] = "reader" if anc["hi"] < 0 else "floor straddle"
    L["gate_eq_covered"], L["gate_eq_fallback"], L["d_eq_pt_all"], L["d_add_pt_all"] = cov, fb, eqpt, addpt
    L["d_pt_all"], L["pt_dilution_anchor"] = dpt, anc
    L["void"] = False
    L["missing_arms"] = []
    L["missing_label_cells"] = []
    L["encoding"], L["free_bigram_arm"], L["history_bigram_arm"] = "prev_table", "free_bigram_b", "history_bigram_b"
    return L

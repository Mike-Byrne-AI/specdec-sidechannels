# Independent recompute of the OQ-9 stratified coverage read (critic round 4). numpy + stdlib only.
# Does not import sideband or the repo tools. Reads only the state files and payloads.
import json, sys, hashlib
import numpy as np

ROOT = "C:/Users/<user>/Desktop/Research/sideband"
STRATA = ["covered_1", "covered_2_4", "covered_5p", "cur_unseen", "prev_unseen", "both_unseen"]
UNIONS = {"covered": STRATA[:3], "fallback": STRATA[3:], "all": STRATA}
SCOPES = STRATA + list(UNIONS)
ARMS = ["history", "free_tok", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b",
        "history_bigram_a", "free_all", "history_all", "pt_only", "free_bigram_pt", "history_tok_pt", "history_bigram_pt"]
TWIN_ARMS = ARMS[:9]
DIMS = {"history": 1025, "free_tok": 1025, "history_tok": 2049, "free_bigram_b": 2049, "free_bigram_a": 2049,
        "history_bigram_b": 3073, "history_bigram_a": 3073, "free_all": 3073, "history_all": 4097,
        "pt_only": 82, "free_bigram_pt": 2130, "history_tok_pt": 2130, "history_bigram_pt": 3154}
BUDGETS = [8, 16, 32]
NG = 16
K = 8
FLOOR = 0.05
PAIRS = [("address_beyond_token", "history_tok", "free_tok"), ("gate_eq", "history_tok", "FREE"),
         ("address_beyond_bigram", "HIST", "FREE"), ("bigram_gain", "FREE", "free_tok"),
         ("pt_gain", "free_bigram_pt", "FREE"), ("d_pt", "history_tok", "free_bigram_pt"),
         ("d_eq_pt", "history_tok_pt", "free_bigram_pt"), ("d_add_pt", "history_bigram_pt", "free_bigram_pt"),
         ("pt_only-free_tok", "pt_only", "free_tok"), ("history_tok_pt-history_tok", "history_tok_pt", "history_tok"),
         ("history_bigram_pt-history_tok_pt", "history_bigram_pt", "history_tok_pt")]
CR = bytes([13])
NL = chr(10)

def read_jsonl(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    assert CR not in raw, path
    lines = raw.decode("utf-8").split(NL)
    assert lines[-1] == ""
    lines = lines[:-1]
    hdr = json.loads(lines[0])
    rows = [json.loads(x) for x in lines[1:]]
    return hdr, rows, hashlib.sha256(raw).hexdigest()

BOOT_IDX = np.random.default_rng(0).integers(0, 30, size=(2000, 30))

def ratio_ci(h, n):
    s = h[BOOT_IDX].sum(axis=1); t = n[BOOT_IDX].sum(axis=1)
    v = t > 0
    lo, hi = np.percentile(s[v] / t[v], [2.5, 97.5])
    return float(lo), float(hi), int((~v).sum())

def delta_ci(ha, hb, n):
    d = float((ha - hb).sum() / n.sum())
    dd = (ha - hb)[BOOT_IDX].sum(axis=1); t = n[BOOT_IDX].sum(axis=1)
    v = t > 0
    lo, hi = np.percentile(dd[v] / t[v], [2.5, 97.5])
    return d, float(lo), float(hi), int((~v).sum())

def reading(d, lo, hi):
    if lo > 0 and d >= FLOOR:
        return "SIGNAL"
    if hi < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"

def straddle(lo, hi):
    return bool(lo <= FLOOR <= hi)

def recompute(name):
    hdr, rows, ssha = read_jsonl(ROOT + "/results/real/" + name + ".json.state.jsonl")
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    assert len(prompts) == 30, len(prompts)
    pix = {p: i for i, p in enumerate(prompts)}
    ai = {a: i for i, a in enumerate(ARMS)}; bi = {b: i for i, b in enumerate(BUDGETS)}; si = {s: i for i, s in enumerate(STRATA)}
    H = np.zeros((13, 3, 6, NG, 30), np.int64); N = np.zeros_like(H); seen = np.zeros(H.shape, dtype=bool)
    bad = 0
    for r in rows:
        assert set(r) == {"arm", "budget", "key", "depth", "gate", "prompt_idx", "stratum", "hits", "needed"}, r
        assert r["key"] == 1 and r["depth"] is None
        k = (ai[r["arm"]], bi[r["budget"]], si[r["stratum"]], int(r["gate"]), pix[int(r["prompt_idx"])])
        assert not seen[k], ("dup", r)
        H[k] = r["hits"]; N[k] = r["needed"]; seen[k] = True
        if not (0 <= r["hits"] <= r["needed"]) or r["needed"] <= 0:
            bad += 1
    assert bad == 0
    Hf = H.astype(np.float64); Nf = N.astype(np.float64)
    def sc(arr, scope):
        idx = [si[s] for s in (UNIONS[scope] if scope in UNIONS else [scope])]
        return arr[:, :, idx].sum(axis=2)
    pair_viol = int((N != N[:1]).any(axis=0).sum())
    bud_viol = int((N != N[:, :1]).any(axis=1).sum())
    gate_viol = int((N != N[:, :, :, :1]).any(axis=3).sum())
    mult_viol = int((N % K != 0).sum())
    pres_viol = int((seen != seen[:1, :1]).sum())
    out = {"rows": len(rows), "state_sha": ssha, "hdr": hdr, "prompts": prompts,
           "checks": {"pairing_arms_cells_violating": pair_viol, "pairing_budgets_violating": bud_viol,
                      "gate_uniform_violations": gate_viol, "needed_mult_K_violations": mult_viol,
                      "row_presence_violations": pres_viol}}
    tables, deltas, dropped = {}, {}, 0
    for a in ARMS:
        for B in BUDGETS:
            for scope in SCOPES:
                h = sc(Hf, scope)[ai[a], bi[B]]; n = sc(Nf, scope)[ai[a], bi[B]]
                if n.sum() == 0:
                    continue
                pg = {}
                for g in range(NG):
                    if n[g].sum() == 0:
                        continue
                    lo, hi, dr = ratio_ci(h[g], n[g]); dropped += dr
                    pg[str(g)] = {"point": float(h[g].sum() / n[g].sum()), "ci_lo": lo, "ci_hi": hi, "needed": int(n[g].sum())}
                hp, np_ = h.sum(axis=0), n.sum(axis=0)
                lo, hi, dr = ratio_ci(hp, np_); dropped += dr
                tables[a + "|B=" + str(B) + "|" + scope] = {"arm": a, "budget": B, "scope": scope, "dims": DIMS[a], "per_gate": pg,
                    "all": {"point": float(hp.sum() / np_.sum()), "ci_lo": lo, "ci_hi": hi, "needed": int(np_.sum())}}
    names = {"FREE": "free_bigram_b", "HIST": "history_bigram_b"}
    for B in BUDGETS:
        for scope in SCOPES:
            for nm, a, b in PAIRS:
                a2, b2 = names.get(a, a), names.get(b, b)
                ha = sc(Hf, scope)[ai[a2], bi[B]].sum(axis=0); hb = sc(Hf, scope)[ai[b2], bi[B]].sum(axis=0)
                na = sc(Nf, scope)[ai[a2], bi[B]].sum(axis=0); nb = sc(Nf, scope)[ai[b2], bi[B]].sum(axis=0)
                assert np.array_equal(na, nb)
                if na.sum() == 0:
                    continue
                d, lo, hi, dr = delta_ci(ha, hb, na); dropped += dr
                deltas[nm + "|B=" + str(B) + "|" + scope] = {"delta": d, "lo": lo, "hi": hi, "needed": int(na.sum())}
    out["tables"], out["deltas"], out["boot_dropped_resamples"] = tables, deltas, dropped
    n_all = sc(Nf, "all")[ai["history_tok"], bi[16]].sum(axis=0)
    scopes = {}
    for scope in SCOPES:
        n = sc(Nf, scope)[ai["history_tok"], bi[16]].sum(axis=0)
        scopes[scope] = {"positions": int(round(n.sum() / (NG * K))), "share": float(n.sum() / n_all.sum()),
                         "prompts_with_positions": int((n > 0).sum())}
    out["scopes"] = scopes
    out["per_prompt_positions"] = {s: (N[ai["history_tok"], bi[16], si[s], 0] // K).tolist() for s in STRATA}
    out["H"], out["N"] = H, N
    return out

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

def reproduce(res, twin_name):
    thdr, trows, tsha = read_jsonl(ROOT + "/results/real/" + twin_name + ".json.state.jsonl")
    ai = {a: i for i, a in enumerate(ARMS)}; bi = {b: i for i, b in enumerate(BUDGETS)}
    pix = {p: i for i, p in enumerate(res["prompts"])}
    Hs, Ns = res["H"].sum(axis=2), res["N"].sum(axis=2)
    hm = 0; nm = 0; maxgap = 0; nrow = 0; extra = 0; cmp_vals = 0
    tk = set()
    for r in trows:
        k = (ai[r["arm"]], bi[r["budget"]], int(r["gate"]), pix[int(r["prompt_idx"])])
        assert k not in tk
        tk.add(k); nrow += 1; cmp_vals += 2
        if Ns[k] != r["needed"]:
            nm += 1
        if Hs[k] != r["hits"]:
            hm += 1; maxgap = max(maxgap, abs(int(Hs[k]) - r["hits"]))
    for a in TWIN_ARMS:
        for B in BUDGETS:
            for gg in range(NG):
                for p in range(30):
                    k = (ai[a], bi[B], gg, p)
                    if k not in tk and Ns[k] > 0:
                        extra += 1
    return {"twin_rows": nrow, "values_compared": cmp_vals, "needed_mm": nm, "hits_mm": hm, "max_gap": maxgap,
            "extra_in_strat": extra, "twin_state_sha": tsha, "twin_hdr": thdr}

def leaves(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, pre + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, pre + "[" + str(i) + "]")
    else:
        yield pre, x

def compare(mine, theirs, label):
    mm = dict(leaves(mine)); tt = dict(leaves(theirs))
    maxd = 0.0; n = 0; nonnum = []; missing = []
    for k, v in mm.items():
        if k not in tt:
            missing.append(k)
            continue
        t = tt[k]; n += 1
        if isinstance(v, (bool, str)) or isinstance(t, (bool, str)) or v is None or t is None:
            if v != t:
                nonnum.append((k, v, t))
        else:
            maxd = max(maxd, abs(float(v) - float(t)))
    return {"what": label, "compared": n, "max_abs": maxd, "nonnum_mismatch": nonnum[:10], "n_nonnum_mismatch": len(nonnum),
            "missing_in_payload": missing[:10], "n_missing": len(missing), "payload_leaves": len(tt),
            "payload_leaves_not_recomputed": sorted(set(tt) - set(mm))[:60]}

def main(dump_path):
    allres = {}
    for name, twin in (("prefetch_strat_s3", "prefetch_bigram_s3"), ("prefetch_strat_s3_r", "prefetch_bigram_s3_r")):
        res = recompute(name)
        res["labels"] = labels_of(res["deltas"])
        pay = json.load(open(ROOT + "/results/real/" + name + ".json", encoding="utf-8"))
        c = pay["conclusion"]
        print("=====", name, "rows", res["rows"], "payload n_state_rows", pay["n_state_rows"], "state sha", res["state_sha"][:12])
        print("checks", res["checks"], "boot dropped resamples", res["boot_dropped_resamples"])
        print("tables", len(res["tables"]), "payload", len(c["tables"]), "deltas", len(res["deltas"]), "payload", len(c["deltas"]))
        print("extra payload tables:", sorted(set(c["tables"]) - set(res["tables"]))[:5], "extra payload deltas:", sorted(set(c["deltas"]) - set(res["deltas"]))[:5])
        tot = 0; mx = 0.0
        for what, mine, theirs in (("tables", res["tables"], c["tables"]), ("deltas", res["deltas"], c["deltas"]),
                                   ("scopes", res["scopes"], c["labels"]["scopes"]), ("labels", res["labels"], c["labels"])):
            cm = compare(mine, theirs, what)
            print(cm)
            tot += cm["compared"]; mx = max(mx, cm["max_abs"])
        print("TOTAL compared", tot, "max abs", mx)
        stc = pay["provenance"]["strata_counts"]["test"]
        m2 = 0.0
        for s in SCOPES:
            m2 = max(m2, abs(stc[s]["n"] - res["scopes"][s]["positions"]), abs(stc[s]["share"] - res["scopes"][s]["share"]))
        print("provenance strata_counts.test vs state-derived scopes max abs", m2)
        rep = reproduce(res, twin)
        print("REPRODUCE", {k: v for k, v in rep.items() if k != "twin_hdr"})
        tw = json.load(open(ROOT + "/results/real/" + twin + ".json", encoding="utf-8"))
        ge = tw["conclusion"]["deltas"]["gate_eq|B=16"]; mine = res["deltas"]["gate_eq|B=16|all"]
        print("IDENTITY gate_eq all vs twin:", {k: (mine[k], ge[k], abs(mine[k] - ge[k])) for k in ("delta", "lo", "hi", "needed")})
        for tkk, mk in (("address_beyond_bigram|B=16", "address_beyond_bigram|B=16|all"), ("bigram_gain|B=16", "bigram_gain|B=16|all"),
                        ("address_beyond_token_re|B=16", "address_beyond_token|B=16|all"), ("gate_eq|B=8", "gate_eq|B=8|all"),
                        ("gate_eq|B=32", "gate_eq|B=32|all")):
            t = tw["conclusion"]["deltas"][tkk]; m = res["deltas"][mk]
            print("  twin", tkk, max(abs(t[k] - m[k]) for k in ("delta", "lo", "hi")))
        mxt = 0.0; nt = 0
        for key, tt in tw["conclusion"]["tables"].items():
            arm, Bs = key.split("|"); m = res["tables"][arm + "|" + Bs + "|all"]
            for k in ("point", "ci_lo", "ci_hi"):
                mxt = max(mxt, abs(tt["all"][k] - m["all"][k])); nt += 1
            for gg, v in tt["per_gate"].items():
                for k in ("point", "ci_lo", "ci_hi"):
                    mxt = max(mxt, abs(v[k] - m["per_gate"][gg][k])); nt += 1
        print("  twin tables vs ALL scope: compared", nt, "max abs", mxt)
        allres[name] = res
    dump = {}
    for name, res in allres.items():
        dump[name] = {"deltas": res["deltas"], "scopes": res["scopes"], "labels": res["labels"],
                      "arm_tables": {k: v["all"] for k, v in res["tables"].items()},
                      "per_prompt_positions": res["per_prompt_positions"], "checks": res["checks"]}
    with open(dump_path, "w") as fh:
        json.dump(dump, fh, indent=1)

if __name__ == "__main__":
    main(sys.argv[1])

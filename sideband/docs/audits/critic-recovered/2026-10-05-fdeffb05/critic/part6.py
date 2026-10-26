
def compare(key, R):
    payload = json.loads((REAL / ("noise_floor_" + key + ".json")).read_text(encoding="utf-8"))
    pr = payload["readouts"]
    rel = pr["reliability"]
    cmp = [(R["r"], rel["r"]), (R["r_lo"], rel["ci_lower"]), (R["r_hi"], rel["ci_upper"]),
           (R["sd"], rel["sd_prompt_runs"]), (R["mad"], rel["mean_abs_seed_diff"]), (R["r_within"], rel["r_within_family"])]
    cmp += [(R["r_fam"][f], rel["r_per_family"][f]) for f in FAMS]
    sh = pr["decomposition"]["share"]
    cmp += list(zip(R["ss_share"], (sh["seed_within_prompt"], sh["prompt_within_family"], sh["family"])))
    mc = pr["decomposition"]["mom"]["component"]
    cmp += list(zip(R["mom"], (mc["seed_within_prompt"], mc["prompt_within_family"], mc["family"])))
    msh = pr["decomposition"]["mom"]["share"]
    cmp += list(zip(R["mom_share"], (msh["seed_within_prompt"], msh["prompt_within_family"], msh["family"])))
    for n in SIZES:
        p, q = pr["per_n"][str(n)], R["per"][n]
        cmp += [(q["f_plus"], p["f_plus"]["rate"]), (q["f_minus"], p["f_minus"]["rate"]), (q["f_two"], p["f_two"]["rate"]),
                (q["f_one"], p["f_one"]["rate"]), (q["f_one_se"], p["f_one"]["se"]), (q["g_one"], p["g_one"]["rate"]),
                (q["g_one_se"], p["g_one"]["se"]), (q["g_one"], p["g_one_guard"]["rate"]),
                (q["hw_med"], p["half_width"]["median"]), (q["hw_mean"], p["half_width"]["mean"]),
                (q["hw_p05"], p["half_width"]["p05"]), (q["hw_p95"], p["half_width"]["p95"]),
                (q["sw_f_one"], p["swap"]["f_one"]["rate"]), (q["sw_g_one"], p["swap"]["g_one"]["rate"]),
                (q["sw_hw_med"], p["swap"]["half_width"]["median"])]
    cmp += [(R["r6"], pr["f19"]["share_at_or_above"]), (R["r6_sw"], pr["f19"]["swap"]["share_at_or_above"]),
            (R["full_delta"], pr["full_set_delta"])]
    R["maxdisc_vs_payload"] = max(abs(a - b) for a, b in cmp)
    R["n_compared"] = len(cmp)
    R["payload_conclusion"] = payload["conclusion"]
    pv = payload["provenance"]
    R["payload_prov"] = {k: pv[k] for k in ("git_commit", "git_status_tracked", "instrument_sha256", "state_sha256", "smoke", "numpy_version")}
    sp = REAL / ("noise_floor_" + key + ".json.state.jsonl")
    R["state_sha_ok"] = hashlib.sha256(sp.read_bytes()).hexdigest() == pv["state_sha256"]

out = {}
for key in POPS:
    A, B, R = readouts_for(key)
    byn = rows_for(key, A, B, R)
    rates_for(byn, R)
    compare(key, R)
    out[key] = R
    print(key, "rows", R["nrows"], "row maxdisc", R["row_maxdisc"], "subsets", R["subsets_regenerated"], "masks", R["masks_regenerated"],
          "state sha ok", R["state_sha_ok"], "gamma", R["drafted_gamma"], "ss ident", R["ss_ident"],
          "maxdisc vs payload", R["maxdisc_vs_payload"], "over", R["n_compared"])
Path(sys.argv[1]).write_text(json.dumps(conv(out), indent=1), encoding="utf-8")

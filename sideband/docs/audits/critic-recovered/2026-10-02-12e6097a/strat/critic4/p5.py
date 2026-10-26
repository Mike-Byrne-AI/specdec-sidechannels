
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

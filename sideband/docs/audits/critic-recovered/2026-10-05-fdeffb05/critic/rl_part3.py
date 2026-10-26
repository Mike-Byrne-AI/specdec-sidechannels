
out = {}
for role, name, p3pay, f17 in (("primary", "lens_s3.json", "probes_s3.json", 0.0721), ("replication", "lens_s3_r.json", "probes_s3_replication.json", 0.0730)):
    hdr, rows = load(name)
    R = {}
    for key, top, base in (("D", "fplus_b", "fplus_r"), ("Mt", "fplus_b", "fplus"), ("Mn_r", "fplus_r", "fplus")):
        for off, cap in ((2, "linear"), (2, "mlp256"), (3, "mlp256"), (4, "mlp256")):
            R[key + "|" + str(off) + "|" + cap] = margin(rows, top, base, off, cap)
    for off, cap in ((2, "linear"), (2, "mlp256")):
        R["Mf|" + str(off) + "|" + cap] = margin(rows, "fplus", "a", off, cap)
    R["Mfx|2|mlp256"] = margin(rows, "fplus", "a", 2, "mlp256", base_cap="linear")
    R["Mc|2|linear"] = margin(rows, "fplus", "c", 2, "linear")
    R["P|2|linear"] = margin(rows, "c", "a", 2, "linear")
    gate = [find(rows, arm, 2, "mlp256", s) for arm in ("fplus", "fplus_b", "fplus_r", "a") for s in (0, 1, 2)]
    gaps = [r["test_acc"] - r["majority_rate_test"] for r in gate]
    rv = {"floor_ok": all(g >= -TOL for g in gaps), "min_gap": min(gaps), "mf_upper": R["Mf|2|mlp256"]["ci"][1], "mfx_upper": R["Mfx|2|mlp256"]["ci"][1]}
    rv["ok"] = rv["floor_ok"] and rv["mf_upper"] >= 0 and rv["mfx_upper"] >= 0
    best = {arm: sorted(find(rows, arm, 2, "mlp256", s)["best_epoch"] for s in (0, 1, 2)) for arm in ("fplus", "fplus_b", "fplus_r", "a")}
    sh = {r["features"]: r for r in rows if r["shuffled"]}
    E = E_stats(sh)
    floors = {arm: sorted(round(find(rows, arm, 2, "linear", s)["test_acc"] - find(rows, arm, 2, "linear", s)["majority_rate_test"], 6) for s in (0, 1, 2)) for arm in ("a", "c")}
    l2 = l2_margin(p3pay); P = R["P|2|linear"]
    growth = "LOST" if P["ci"][1] < l2["margin"] else ("SURVIVES" if P["ci"][0] > l2["margin"] else "NOT-SETTLED")
    out[role] = {"R": R, "rv": rv, "best": best, "sh_acc": {a: sh[a]["test_acc"] for a in sh},
                 "leg1": sh["fplus"]["test_acc"] <= sh["a"]["test_acc"] + BAND,
                 "raw2": sh["fplus_b"]["test_acc"] - sh["fplus"]["test_acc"], "E": E,
                 "leg2_fail": E["dE"] > BAND or (E["ciE"][0] > 0 and E["dE"] >= MAT),
                 "floors": floors, "l2": l2["margin"], "growth": growth, "ratio": P["m"] / f17, "P_fires": fires(P),
                 "runtime_rows": sum(r["runtime_s"] for r in rows), "n_rows": len(rows),
                 "maj": sorted({round(r["majority_rate_test"], 6) for r in rows if not r["shuffled"]})}

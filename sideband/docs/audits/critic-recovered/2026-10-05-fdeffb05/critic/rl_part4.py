pr, rp = out["primary"], out["replication"]
gp, gr = pr["R"]["D|2|mlp256"], rp["R"]["D|2|mlp256"]
if not (pr["rv"]["ok"] and rp["rv"]["ok"]): label = "READER-INVALID"
elif fires(gp) and fires(gr): label = "SURVIVES-FULL-FREE"
elif fires(gp) != fires(gr): label = "SPLIT"
elif all(o["R"][k]["ci"][1] < MAT for o in (pr, rp) for k in o["R"] if k.startswith("D|")): label = "ABSORBED"
else: label = "NOT-SHOWN"
hor = {}
for off in (3, 4):
    a, b = pr["R"]["D|" + str(off) + "|mlp256"], rp["R"]["D|" + str(off) + "|mlp256"]
    fa, fb = fires(a), fires(b)
    hor[off] = "SURVIVES" if fa and fb else ("SPLIT" if fa != fb else ("ABSORBED" if a["ci"][1] < MAT and b["ci"][1] < MAT else "NOT-SHOWN"))
Pp, Pr = pr["R"]["P|2|linear"], rp["R"]["P|2|linear"]
lens = ("LENS-SURVIVES" if pr["P_fires"] and rp["P_fires"] else "LENS-SPLIT" if pr["P_fires"] != rp["P_fires"]
        else "LENS-COLLAPSE" if Pp["ci"][1] < MAT and Pr["ci"][1] < MAT else "LENS-NOT-SHOWN")
g = (pr["growth"], rp["growth"])
comb = g[0] if g[0] == g[1] and g[0] in ("LOST", "SURVIVES") else ("SPLIT" if sum(x in ("LOST", "SURVIVES") for x in g) >= 1 else "NOT-SETTLED")
res = {"label": label, "horizons": hor, "lens": lens, "growth": {"primary": g[0], "replication": g[1], "combined": comb}, "harvests": out}
json.dump(res, open(sys.argv[1], "w"), indent=1, default=float)
def f(r):
    return "%+.4f [%+.4f, %+.4f] seeds %s" % (r["m"], r["ci"][0], r["ci"][1], "/".join("%+.4f" % v for v in r["per"].values()))
for role, o in out.items():
    print("==", role, "rows", o["n_rows"], "majority rates", o["maj"], "sum of row runtimes %.1f s" % o["runtime_rows"])
    for k in o["R"]:
        print("  %-16s %s" % (k, f(o["R"][k])))
    print("  reader-validity", o["rv"], "best epochs", o["best"])
    print("  rider: shuffled acc", o["sh_acc"], "leg1", o["leg1"], "raw leg2 %+.4f" % o["raw2"], "E", o["E"]["E"],
          "dE %+.5f CI %s x_raw %+.5f amended leg2 FAILS %s" % (o["E"]["dE"], o["E"]["ciE"], o["E"]["x_raw"], o["leg2_fail"]))
    print("  P fires", o["P_fires"], "ratio %.4f L2 %+.4f growth %s acc-floor %s" % (o["ratio"], o["l2"], o["growth"], o["floors"]))
print("LABEL", label, "| horizons", hor, "| LENS", lens, "| growth", res["growth"])

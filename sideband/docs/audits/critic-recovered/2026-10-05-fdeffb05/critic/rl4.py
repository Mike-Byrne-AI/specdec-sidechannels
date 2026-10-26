labels = {}
for reader in ("RN", "RT", "RL"):
    for sp in SPACES:
        rp, rr = H["primary"][(reader, sp)], H["replication"][(reader, sp)]
        lab, lic = label_of(rp, rr)
        reasons = []
        if lab == "SURVIVES-STRONGER":
            if any(x["R"]["Mt"]["ci"][1] < 0 for x in (rp, rr)): reasons.append("Mt upper < 0 on a harvest")
            if any(x["R"]["Mn_r"]["ci"][1] < 0 for x in (rp, rr)): reasons.append("Mn_r upper < 0 on a harvest")
        mt_tr = (fires(rp["R"]["Mt"]), fires(rr["R"]["Mt"]))
        labels[(reader, sp)] = {"label": lab, "licence": lic, "reasons": reasons, "mt_triple": mt_tr,
                                "reopen": lab == "SURVIVES-STRONGER" and lic == "full" and all(mt_tr)}
valid = {k: v for k, v in labels.items() if v["label"] != "READER-INVALID"}
surv = sorted(k for k, v in valid.items() if v["label"] == "SURVIVES-STRONGER")
split = sorted(k for k, v in valid.items() if v["label"] == "SPLIT")
reopen_cells = sorted(k for k, v in valid.items() if k[1] in (L1, BAL) and v["reopen"])
if not valid:
    word = "K-2-INCOMPLETE"
elif surv:
    word = "K-2-ISOLATED"
elif split:
    word = "K-2-UNSETTLED"
else:
    word = "K-2-NOT-OVERTURNED-AT-S3"
def fmt(r, d=4):
    pat = "%+." + str(d) + "f [%+." + str(d) + "f, %+." + str(d) + "f] seeds %s"
    return pat % (r["m"], r["ci"][0], r["ci"][1], "/".join("%+.4f" % v for v in r["per"].values()))
for sp in SPACES:
    print("== RL", sp, labels[("RL", sp)])
    for role in ("primary", "replication"):
        x = H[role][("RL", sp)]
        for k in ("D", "Mt", "Mn_r", "Mf", "Mfx", "Mc"):
            if x["R"].get(k):
                print("   ", role[:4], "%-5s" % k, fmt(x["R"][k], 6 if k == "D" else 4))
        print("    ", role[:4], "rv", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in x["rv"].items()}, "best", x["best"])
print("ALL NINE:", {k[0] + "|" + k[1]: (v["label"], v["licence"]) for k, v in labels.items()})
print("K-2 word", word, "| surv", surv, "| split", split, "| reopen-grade", reopen_cells, "| S1 trigger", sorted({k[0] for k in reopen_cells}))
print("narrowed", sorted(k for k, v in valid.items() if v["label"] == "ABSORBED"), "| not narrowed", sorted(k for k, v in valid.items() if v["label"] == "NOT-SHOWN"))
print("R0 linear (a) identity vs lens rows:", {r: {k: v for k, v in H[r].items() if str(k).startswith("ident_")} for r in ("primary", "replication")})
out = {"labels": {k[0] + "|" + k[1]: v for k, v in labels.items()}, "word": word,
       "R": {role: {k[0] + "|" + k[1]: v for k, v in H[role].items() if isinstance(k, tuple)} for role in ("primary", "replication")}}
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)

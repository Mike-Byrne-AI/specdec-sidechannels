def fmt(r, d=4):
    pat = "%+." + str(d) + "f [%+." + str(d) + "f, %+." + str(d) + "f] seeds %s"
    return pat % (r["m"], r["ci"][0], r["ci"][1], "/".join("%+.4f" % v for v in r["per"].values()))
for reader in ("RN", "RT"):
    for sp in SPACES:
        print("==", reader, sp, labels[(reader, sp)])
        for role in ("primary", "replication"):
            x = H[role][(reader, sp)]
            for k in ("D", "Mt", "Mn_r", "Mf", "Mfx", "Mc"):
                if x["R"].get(k):
                    print("   ", role[:4], "%-5s" % k, fmt(x["R"][k], 6 if k == "D" else 4))
            print("    ", role[:4], "rv", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in x["rv"].items()}, "best", x["best"], "c_hz", x["resc"])
print("K-2 word", word, "| surv", surv, "| split", split, "| reopen-grade cells", reopen_cells, "| readers_long_runs", rl_runs)
print("narrowed", sorted(k for k, v in valid.items() if v["label"] == "ABSORBED"), "| not narrowed", sorted(k for k, v in valid.items() if v["label"] == "NOT-SHOWN"))
print("rerun identity differing fields", {r: H[r]["ident"] for r in ("primary", "replication")}, "| row runtime sums", {r: round(H[r]["runtime"], 1) for r in ("primary", "replication")})
out = {"labels": {k[0] + "|" + k[1]: v for k, v in labels.items()}, "word": word,
       "R": {role: {k[0] + "|" + k[1]: {"R": v["R"], "rv": v["rv"], "best": v["best"], "resc": v["resc"]} for k, v in H[role].items() if isinstance(k, tuple)} for role in ("primary", "replication")}}
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)

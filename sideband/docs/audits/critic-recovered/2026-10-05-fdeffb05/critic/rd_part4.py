labels = {}
for reader in ("RN", "RT"):
    for sp in SPACES:
        rp, rr = H["primary"][(reader, sp)], H["replication"][(reader, sp)]
        lab, lic = label_of(rp, rr)
        mt_tr = (fires(rp["R"]["Mt"]), fires(rr["R"]["Mt"]))
        labels[(reader, sp)] = {"label": lab, "licence": lic, "mt_triple": mt_tr, "reopen": lab == "SURVIVES-STRONGER" and lic == "full" and all(mt_tr)}
valid = {k: v for k, v in labels.items() if v["label"] != "READER-INVALID"}
surv = [k for k, v in valid.items() if v["label"] == "SURVIVES-STRONGER"]
split = [k for k, v in valid.items() if v["label"] == "SPLIT"]
reopen_cells = [k for k, v in valid.items() if k[1] in (L1, BAL) and v["reopen"]]
if not valid:
    word = "K-2-INCOMPLETE"
elif surv:
    word = "K-2-ISOLATED"
elif split:
    word = "K-2-UNSETTLED"
else:
    word = "K-2-NOT-OVERTURNED-AT-S3"
rl_runs = not any(v["label"] in ("SURVIVES-STRONGER", "SPLIT") for k, v in labels.items() if k[1] in (L1, BAL))

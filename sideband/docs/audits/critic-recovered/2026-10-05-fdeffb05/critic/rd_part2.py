
def readouts(rows, p3, reader, space):
    g = lambda arm: [pick(rows, reader, space, arm, "mlp256", s) for s in (0, 1, 2)]
    R = {"D": pair_margin(g("fplus_b"), g("fplus_r")), "Mt": pair_margin(g("fplus_b"), g("fplus")),
         "Mn_r": pair_margin(g("fplus_r"), g("fplus")), "Mf": pair_margin(g("fplus"), g("a"))}
    if space == BAL:
        lin = [pick(rows, "R0", BAL, "a", "linear", s) for s in (0, 1, 2)]
    else:
        lin = [next(c for c in p3 if c["space"] == space and c["offset"] == 2 and c["features"] == "a" and c["capacity"] == "linear" and c["seed"] == s and not c.get("shuffled")) for s in (0, 1, 2)]
    R["Mfx"] = pair_margin(g("fplus"), lin)
    cm = [c for c in p3 if c["space"] == space and c["offset"] == 2 and c["features"] == "c" and c["capacity"] == "mlp256" and not c.get("shuffled")]
    R["Mc"] = pair_margin(g("fplus"), sorted(cm, key=lambda c: c["seed"])) if (space != BAL and len(cm) == 3) else None
    gaps = [c["test_acc"] - c["majority_rate_test"] for arm in ("fplus", "fplus_b", "fplus_r", "a") for c in g(arm)]
    rv = {"floor_ok": all(x >= -TOL for x in gaps), "min_gap": min(gaps), "mf_up": R["Mf"]["ci"][1], "mfx_up": R["Mfx"]["ci"][1]}
    rv["ok"] = rv["floor_ok"] and rv["mf_up"] >= 0 and rv["mfx_up"] >= 0
    best = {arm: sorted(c["best_epoch"] for c in g(arm)) for arm in ("fplus", "fplus_b", "fplus_r", "a")}
    resc = sorted({round(c["reader_params"]["rescale"]["c_hz"], 6) for arm in ("fplus", "fplus_b", "fplus_r") for c in g(arm)}) if reader == "RN" else None
    return R, rv, best, resc

def label_of(rp, rr):
    if not (rp["rv"]["ok"] and rr["rv"]["ok"]):
        return "READER-INVALID", None
    fp, fr = fires(rp["R"]["D"]), fires(rr["R"]["D"])
    if fp and fr:
        neg = any(x["R"][k]["ci"][1] < 0 for x in (rp, rr) for k in ("Mt", "Mn_r"))
        return "SURVIVES-STRONGER", ("equal-dims-only" if neg else "full")
    if fp != fr:
        return "SPLIT", None
    if rp["R"]["D"]["ci"][1] < MAT and rr["R"]["D"]["ci"][1] < MAT:
        return "ABSORBED", None
    return "NOT-SHOWN", None

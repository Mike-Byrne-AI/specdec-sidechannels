import os
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[v] = "4"
import json, sys
import numpy as np
REAL = "results/real"
MAT, TOL, NB = 0.005, 0.001, 2000
L1, LOP, BAL = "L1_olmoe_k16", "L3_olmoe_groups_v1", "L3_olmoe_balanced_v1"
SPACES = (L1, LOP, BAL)

def rows_of(path):
    lines = [l for l in open(path, encoding="utf-8").read().split("\n") if l.strip()]
    out = []
    for l in lines[1:]:
        d = json.loads(l)
        if "_clusters" in d: d["_clusters"] = {int(k): v for k, v in d["_clusters"].items()}
        out.append(d)
    return json.loads(lines[0]), out

def boot(diff, n, seed=0, n_boot=NB):
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, len(n), size=(n_boot, len(n)))
    lo, hi = np.percentile(diff[idx].sum(1) / n[idx].sum(1), [2.5, 97.5])
    return float(lo), float(hi)

def pick(rows, reader, space, arm, cap, seed):
    m = [r for r in rows if r.get("reader", "R0") == reader and r["space"] == space and r["features"] == arm
         and r["capacity"] == cap and r["seed"] == seed and r["offset"] == 2 and not r["shuffled"]]
    assert len(m) == 1, (reader, space, arm, cap, seed, len(m))
    return m[0]

def pair_margin(tops, bases):
    prompts = sorted(set.intersection(*(set(t["_clusters"]) & set(b["_clusters"]) for t, b in zip(tops, bases))))
    st = np.zeros(len(prompts)); sb = np.zeros(len(prompts)); n = np.zeros(len(prompts)); per = {}
    for s, (t, b) in enumerate(zip(tops, bases)):
        tt = np.array([t["_clusters"][p][0] for p in prompts], float); bb = np.array([b["_clusters"][p][0] for p in prompts], float)
        tn = np.array([t["_clusters"][p][1] for p in prompts], float); bn = np.array([b["_clusters"][p][1] for p in prompts], float)
        assert np.array_equal(tn, bn)
        st += tt; sb += bb; n += tn; per[s] = float((tt - bb).sum() / tn.sum())
    lo, hi = boot(st - sb, n)
    return {"m": float((st - sb).sum() / n.sum()), "ci": [lo, hi], "per": per, "nc": len(prompts)}

def fires(r):
    return r is not None and r["nc"] == 30 and r["ci"][0] > 0 and all(v > 0 for v in r["per"].values()) and r["m"] >= MAT

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

H = {}
STAGES = (("readers", ("RN", "RT")), ("readers_long", ("RL",)))
for role, suffix, p3name in (("primary", "", "probes_s3.json.state.jsonl"), ("replication", "_r", "probes_s3_replication.json.state.jsonl")):
    _, p3 = rows_of(REAL + "/" + p3name)
    p3 = [c for c in p3 if "cell" in c and "_clusters" in c]
    _, lens = rows_of(REAL + "/lens_s3" + suffix + ".json.state.jsonl")
    H[role] = {}
    for stage, readers in STAGES:
        hdr, rows = rows_of(REAL + "/" + stage + "_s3" + suffix + ".json.state.jsonl")
        for reader in readers:
            for sp in SPACES:
                R, rv, best, resc = readouts(rows, p3, reader, sp)
                H[role][(reader, sp)] = {"R": R, "rv": rv, "best": best}
        ident = {}
        for s in (0, 1, 2):
            a = pick(rows, "R0", BAL, "a", "linear", s); b = pick(lens, "R0", BAL, "a", "linear", s)
            ident[s] = [k for k in sorted(set(a) | set(b)) if k != "runtime_s" and json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True)]
        H[role]["ident_" + stage] = ident
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

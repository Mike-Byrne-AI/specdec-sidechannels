import os
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[v] = "4"
import json, sys
import numpy as np
REAL = "results/real"
MAT, TOL, BAND, NB = 0.005, 0.001, 0.01, 2000
BAL = "L3_olmoe_balanced_v1"

def load(name):
    lines = [l for l in open(REAL + "/" + name + ".state.jsonl", encoding="utf-8").read().split("\n") if l.strip()]
    hdr = json.loads(lines[0]); rows = []
    for l in lines[1:]:
        d = json.loads(l)
        if "_clusters" in d: d["_clusters"] = {int(k): v for k, v in d["_clusters"].items()}
        if "_hist" in d: d["_hist"] = {int(k): v for k, v in d["_hist"].items()}
        rows.append(d)
    return hdr, rows

def boot(diff, n, seed=0, n_boot=NB):
    gen = np.random.default_rng(seed)
    idx = gen.integers(0, len(n), size=(n_boot, len(n)))
    d = diff[idx].sum(1); t = n[idx].sum(1)
    lo, hi = np.percentile(d / t, [2.5, 97.5])
    return float(lo), float(hi)

def find(rows, arm, off, cap, seed, shuffled=False):
    m = [r for r in rows if r["features"] == arm and r["offset"] == off and r["capacity"] == cap
         and r["seed"] == seed and bool(r["shuffled"]) == shuffled and r["space"] == BAL]
    assert len(m) == 1, (arm, off, cap, seed, len(m))
    return m[0]

def margin(rows, top, base, off, cap, base_cap=None):
    base_cap = base_cap or cap
    pairs = [(find(rows, top, off, cap, s), find(rows, base, off, base_cap, s)) for s in (0, 1, 2)]
    prompts = sorted(set.intersection(*(set(t["_clusters"]) & set(b["_clusters"]) for t, b in pairs)))
    st = np.zeros(len(prompts)); sb = np.zeros(len(prompts)); n = np.zeros(len(prompts)); per = {}
    for s, (t, b) in enumerate(pairs):
        tt = np.array([t["_clusters"][p][0] for p in prompts], float); bb = np.array([b["_clusters"][p][0] for p in prompts], float)
        tn = np.array([t["_clusters"][p][1] for p in prompts], float); bn = np.array([b["_clusters"][p][1] for p in prompts], float)
        assert np.array_equal(tn, bn)
        st += tt; sb += bb; n += tn; per[s] = float((tt - bb).sum() / tn.sum())
    m = float((st - sb).sum() / n.sum()); lo, hi = boot(st - sb, n)
    return {"m": m, "ci": [lo, hi], "per": per, "nc": len(prompts)}

def fires(r):
    return r["nc"] == 30 and r["ci"][0] > 0 and all(v > 0 for v in r["per"].values()) and r["m"] >= MAT

def E_stats(sh):
    arms = [a for a in ("a", "fplus", "fplus_b", "fplus_r") if a in sh]
    prompts = sorted(set.intersection(*(set(sh[a]["_hist"]) for a in arms)))
    A = {}
    for a in arms:
        h = sh[a]["_hist"]
        N = np.array([sum(h[p]["n"]) for p in prompts], float); C = np.array([sum(h[p]["correct"]) for p in prompts], float)
        PH = np.array([np.sum(h[p]["pred"], axis=0) for p in prompts], float); LH = np.array([np.sum(h[p]["label"], axis=0) for p in prompts], float)
        A[a] = (N, C, PH, LH)
    def pt(draw):
        o = {}
        for a in arms:
            N, C, PH, LH = A[a]; n = N[draw].sum()
            acc = C[draw].sum() / n; q = PH[draw].sum(0) / n; p = LH[draw].sum(0) / n
            o[a] = (acc, acc - float(q @ p))
        return o
    full = pt(np.arange(len(prompts)))
    rng = np.random.default_rng(0); bE = {a: [] for a in arms}
    for _ in range(NB):
        r = pt(rng.integers(0, len(prompts), len(prompts)))
        for a in arms: bE[a].append(r[a][1])
    dE = full["fplus_b"][1] - full["fplus_r"][1]
    ciE = [float(np.percentile(np.array(bE["fplus_b"]) - np.array(bE["fplus_r"]), q)) for q in (2.5, 97.5)]
    return {"E": {a: full[a][1] for a in arms}, "dE": dE, "ciE": ciE, "x_raw": full["fplus_b"][0] - full["fplus_r"][0], "nprompts": len(prompts)}

def l2_margin(payload):
    p = json.load(open(REAL + "/" + payload, encoding="utf-8"))
    return [m for m in p["margins"] if m["space"] == "L2_olmoe_k512" and m["offset"] == 2 and m["capacity"] == "linear"][0]

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

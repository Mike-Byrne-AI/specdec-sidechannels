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

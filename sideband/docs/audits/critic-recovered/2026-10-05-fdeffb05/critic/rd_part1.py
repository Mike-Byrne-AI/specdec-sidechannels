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

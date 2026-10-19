
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

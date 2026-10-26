
def run(stem):
    s = json.loads((REAL / (stem + ".summary.json")).read_text(encoding="utf-8"))
    pp = sorted(s["per_prompt_stats"], key=lambda d: d["prompt_idx"])
    return {k: np.array([p[f] for p in pp], float) for k, f in (("e", "n_emitted"), ("b", "n_blocks"), ("d", "n_drafted"))}

def boot(ea, ba, eb, bb, n_boot=2000, seed=0):
    n = ea.shape[0]
    idx = np.random.default_rng(seed).integers(0, n, size=(n_boot, n))
    d = ea[idx].sum(1) / ba[idx].sum(1) - eb[idx].sum(1) / bb[idx].sum(1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return ea.sum() / ba.sum() - eb.sum() / bb.sum(), lo, hi

def se1(c, mm):
    f = c / mm
    return math.sqrt(f * (1 - f) / mm) / 2

def conv(o):
    if isinstance(o, dict):
        return {str(k): conv(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [conv(v) for v in o]
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o

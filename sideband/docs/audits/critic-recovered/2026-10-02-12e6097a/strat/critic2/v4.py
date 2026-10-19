import json, sys, re
import numpy as np
R = r"C:\Users\<user>\Desktop\Research\sideband\results\real"
for nm in ("prefetch_bigram_s3.json", "prefetch_bigram_s3_r.json"):
    lines = open(R + "\\" + nm + ".state.jsonl", encoding="utf-8").read().splitlines()
    rows = [json.loads(l) for l in lines[1:] if l.strip()]
    acc = {}
    for r in rows:
        if r["budget"] != 16: continue
        k = (r["arm"], r["prompt_idx"]); h, n = acc.get(k, (0, 0)); acc[k] = (h + r["hits"], n + r["needed"])
    prompts = sorted({p for (_, p) in acc}); P = len(prompts)
    ha = np.array([acc[("history_bigram_b", p)][0] for p in prompts], float); hb = np.array([acc[("history_tok", p)][0] for p in prompts], float)
    n = np.array([acc[("history_tok", p)][1] for p in prompts], float)
    assert np.array_equal(n, np.array([acc[("history_bigram_b", p)][1] for p in prompts], float))
    idx = np.random.default_rng(0).integers(0, P, size=(2000, P))
    d = (ha - hb)[idx].sum(1) / n[idx].sum(1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    print(nm, "HISTORY_BIGRAM(b) - history_tok B=16: %+.4f [%+.4f, %+.4f]" % ((ha - hb).sum() / n.sum(), lo, hi), "P", P)
bp = open(r"C:\Users\<user>\Desktop\Research\sideband\docs\BLUEPRINT.md", encoding="utf-8").read()
i0 = bp.index("OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION (2026-10-01, pre-run")
pre = bp[:i0]
for s in ("+0.0454 / +0.0472", "0.9115 / 0.8634", "+0.1844", "+0.1695", "+0.1190", "+0.1169", "+0.4491", "+0.3680", "0.787", "0.804", "0.0987", "0.1418", "0.0113", "0.0141"):
    print(repr(s), "occurs before the block:", pre.count(s))
fi = open(r"C:\Users\<user>\Desktop\Research\sideband\FINDINGS.md", encoding="utf-8").read()
for s in ("+0.1844", "0.787", "0.0987", "0.0113", "0.9115"):
    print(repr(s), "in FINDINGS:", fi.count(s))

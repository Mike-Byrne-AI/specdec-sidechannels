# cell-by-cell placement check: each expected fragment is BUILT from the payloads (primary / replication
# in that order) and must occur verbatim (whitespace-normalised) in the named region.
import json, re
R = r"C:\Users\<user>\Desktop\Research\sideband"
P = [json.load(open(R + "/results/real/prefetch_strat_s3.json")), json.load(open(R + "/results/real/prefetch_strat_s3_r.json"))]
def d(k, i): return P[i]["conclusion"]["deltas"][k]
def s(x): return f"{x:+.4f}"
def pt(k): return f"{s(d(k,0)['delta'])} / {s(d(k,1)['delta'])}"
def ci(k, i): v = d(k, i); return f"{s(v['delta'])} [{s(v['lo'])}, {s(v['hi'])}]"
def pci(k): return f"{ci(k,0)} / {ci(k,1)}"
def sh(sc): return " / ".join(f"{p['conclusion']['labels']['scopes'][sc]['share']:.4f}" for p in P)
def norm(t): return re.sub(r"\s+", " ", t)
def region(path, a, b):
    t = norm(open(R + "/" + path, encoding="utf-8").read()); i = t.index(norm(a)); j = t.index(norm(b), i); return t[i:j]
K = lambda n, sc, B=16: f"{n}|B={B}|{sc}"
cov = sum(1 for _ in [0])
contrib = [P[i]["conclusion"]["labels"]["scopes"]["covered"]["share"] * d(K("gate_eq","covered"), i)["delta"] for i in (0, 1)]
ratio = [contrib[i] / d(K("gate_eq","all"), i)["delta"] for i in (0, 1)]
arc = region("docs/FINDINGS_INDEX.md", "The stratified coverage read (2026-10-02;", "Kill-criterion outcome")
row = region("docs/FINDINGS_INDEX.md", "stratified read (2026-10-02, test split", "| stands (NON-CRITERION")
chg = region("CHANGELOG.md", "- 09e846b feat(prefetch)", "- fea2431 feat(prefetch)")
checks = {
 "arc": [f"twin's {P[0]['conclusion']['labels']['reproduce']['n_twin_rows']:,} committed state",
   f"covered positions ({sh('covered')} of the test positions) D_eq {pci(K('gate_eq','covered'))} (NOT-SHOWN, the floor inside the CI)",
   f"unseen key ({sh('fallback')}) {pci(K('gate_eq','fallback'))} (SIGNAL)",
   f"D_eq^PT {pci(K('d_eq_pt','all'))} (SIGNAL, the floor inside the CI)",
   f"D_add^PT {pci(K('d_add_pt','all'))} (SIGNAL)",
   f"PT GAIN on all positions {pt(K('pt_gain','all'))}, on the covered ones {pt(K('pt_gain','covered'))}",
   f"carry {s(contrib[0])} / {s(contrib[1])} of the pooled {pt(K('gate_eq','all'))} ({ratio[0]:.3f} / {ratio[1]:.3f} of it)",
   f"D_add^PT on the covered positions {pt(K('d_add_pt','covered'))}, SIGNAL, the floor inside the CI",
   f"at B = 8 the covered positions read SIGNAL, D_eq {pt(K('gate_eq','covered',8))}",
   f"D_eq^PT {pt(K('d_eq_pt','all',32))} and D_add^PT {pt(K('d_add_pt','all',32))}, where Q2 would read PT-ABSORBS",
   f"D_eq {pt(K('gate_eq','covered_1'))} at one (SIGNAL), {pt(K('gate_eq','covered_2_4'))} at two to four (SIGNAL, the floor inside the CI) and {pt(K('gate_eq','covered_5p'))} at five or more (NOT-SHOWN, the floor inside the CI; {sh('covered_5p')} of the positions)",
   f"both-unseen stratum ({sh('both_unseen')} of the positions) reads {pt(K('gate_eq','both_unseen'))} and draws 0.3482 / 0.5379",
   "81 coordinates", "fea2431", "(prompt 13)"],
 "row": [f"covered D_eq {pci(K('gate_eq','covered'))}, unseen-key {pt(K('gate_eq','fallback'))}; D_eq^PT {pci(K('d_eq_pt','all'))}, D_add^PT {pt(K('d_add_pt','all'))}",
   f"one / two to four / five or more {s(d(K('gate_eq','covered_1'),0)['delta'])} / {s(d(K('gate_eq','covered_2_4'),0)['delta'])} / {s(d(K('gate_eq','covered_5p'),0)['delta'])} (replication {s(d(K('gate_eq','covered_1'),1)['delta'])} / {s(d(K('gate_eq','covered_2_4'),1)['delta'])} / {s(d(K('gate_eq','covered_5p'),1)['delta'])})"],
 "chg": [f"twin's {P[0]['conclusion']['labels']['reproduce']['n_twin_rows']:,} committed state rows and the pooled D_eq equals the twin's {pt(K('gate_eq','all'))}",
   f"D_eq {pci(K('gate_eq','covered'))} (NOT-SHOWN, the floor inside the CI), on the unseen-key positions {pt(K('gate_eq','fallback'))} (SIGNAL)",
   f"D_eq^PT {pt(K('d_eq_pt','all'))} (SIGNAL, the floor inside the CI) and D_add^PT {pt(K('d_add_pt','all'))} (SIGNAL)",
   f"D_eq {pt(K('gate_eq','covered_1'))} at one (SIGNAL), {pt(K('gate_eq','covered_2_4'))} at two to four (SIGNAL) and {pt(K('gate_eq','covered_5p'))} at five or more (NOT-SHOWN)",
   f"({P[0]['n_state_rows']:,} / {P[1]['n_state_rows']:,} rows)"],
}
regs = {"arc": arc, "row": row, "chg": chg}
bad = 0; n = 0
for r, frags in checks.items():
    for f in frags:
        n += 1
        if norm(f) not in regs[r]: bad += 1; print("NOT FOUND in", r, ":", f)
nums = {r: len(re.findall(r"[+-]?\d[\d,]*\.\d+", regs[r])) for r in regs}
print("fragments", n, "missing", bad, "| decimals per region", nums)
# prompt 13 shares recomputed from state
for i, f in enumerate(["prefetch_strat_s3", "prefetch_strat_s3_r"]):
    c13 = t = 0
    with open(R + f"/results/real/{f}.json.state.jsonl", encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            x = json.loads(line)
            if x["arm"] == "history_tok" and x["budget"] == 16 and x["gate"] == 5 and x["stratum"] == "both_unseen":
                t += x["needed"]; c13 += x["needed"] if x["prompt_idx"] == 13 else 0
    print(f, "prompt-13 share", f"{c13/t:.4f}")

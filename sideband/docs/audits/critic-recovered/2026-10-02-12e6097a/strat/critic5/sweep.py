import json, re, sys, collections
P = json.load(open("results/real/prefetch_strat_s3.json")); R = json.load(open("results/real/prefetch_strat_s3_r.json"))
TP = json.load(open("results/real/prefetch_bigram_s3.json")); TR = json.load(open("results/real/prefetch_bigram_s3_r.json"))
known = collections.defaultdict(set)
def add(s, why): known[s].add(why)
for X, t, T in ((P, "P", TP), (R, "R", TR)):
    pv = X["provenance"]; st = pv["strata_counts"]["test"]
    for s, v in st.items():
        if isinstance(v, dict): add(f"{v['share']:.4f}", f"{t} share {s}"); add(f"{v['n']:,}", f"{t} n {s}"); add(str(v['n']), f"{t} n {s}")
    for k, tb in X["conclusion"]["tables"].items():
        if "B=16" in k and k.endswith("|all"): add(f"{tb['all']['point']:.4f}", f"{t} arm {k}")
    for k, d in X["conclusion"]["deltas"].items():
        add(f"{d['delta']:+.4f}", f"{t} delta {k}")
    for k, d in T["conclusion"]["deltas"].items():
        if isinstance(d, dict) and "delta" in d: add(f"{d['delta']:+.4f}", f"{t} twin {k}")
    add(f"{pv['runtime_s']:.1f}", f"{t} runtime"); add(f"{X['n_state_rows']:,}", f"{t} rows")
    for a, l in pv["lambda_selected"].items(): add(str(l), f"{t} lambda {a}")
    for s, v in X["conclusion"]["labels"]["scopes"].items(): add(str(v["prompts_with_positions"]), f"{t} prompts {s}")
add("12,960", "twin rows"); add("81", "d_pt"); add("0.3482", "P prompt13 share (state recompute)"); add("0.5379", "R prompt13 share (state recompute)")
add("0.05", "floor"); add("+0.05", "floor"); add("16", "B"); add("8", "B"); add("32", "B"); add("1", "j"); add("30", "prompts"); add("13", "prompt 13")
txt = open(sys.argv[1], encoding="utf-8").read()
txt = re.sub(r"\s+", " ", txt)
NUM = r"[+-]\d+\.\d+"
TRI = rf"{NUM} \[{NUM}, {NUM}\]"
pairs = list(re.finditer(rf"{TRI}\s*/\s*{TRI}", txt))
spans = [(m.start(), m.end()) for m in pairs]
n_pair_nums = 6 * len(pairs)
toks = []
for m in re.finditer(r"(?<![\w.])[+-]?\d[\d,]*(?:\.\d+)?", txt):
    if any(a <= m.start() < b for a, b in spans): continue
    toks.append(m)
miss = []
for m in toks:
    s = m.group(0).rstrip(",")
    ctx = txt[max(0, m.start() - 60):m.end() + 10]
    if s in known or s.lstrip("+") in known:
        continue
    miss.append((s, ctx))
print("pairs", len(pairs), "pair numbers", n_pair_nums, "scalar tokens", len(toks), "unmatched", len(miss))
for s, c in miss: print("  UNMATCHED", repr(s), "::", c)

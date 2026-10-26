import json
import numpy as np
S = r"C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/4f289fb0-652a-439c-a5cf-abf830e63352/scratchpad/bigram_smoke/bigram_smoke.json"
payload = json.load(open(S, encoding="utf-8"))
lines = open(S + ".state.jsonl", encoding="utf-8").read().splitlines()
header = json.loads(lines[0])
rows = [json.loads(x) for x in lines[1:] if x.strip()]
print("header keys", sorted(header), "smoke", header["smoke"], "encoding", header["encoding"], "committed", header["committed_cell"])
print("n rows", len(rows), "payload n_state_rows", payload["n_state_rows"])
arms = sorted({r["arm"] for r in rows})
budgets = sorted({r["budget"] for r in rows})
prompts = sorted({r["prompt_idx"] for r in rows})
gates = sorted({r["gate"] for r in rows})
print("arms", arms)
print("budgets", budgets, "prompts", len(prompts), prompts, "gates", len(gates))
print("keys", {r["key"] for r in rows}, "depths", {r["depth"] for r in rows})
P, G = len(prompts), len(gates)
pix = {p: i for i, p in enumerate(prompts)}
H = {}
N = {}
seen = set()
for r in rows:
    t = (r["arm"], r["budget"], r["gate"], r["prompt_idx"])
    assert t not in seen
    seen.add(t)
    k = (r["arm"], r["budget"])
    if k not in H:
        H[k] = np.zeros((P, G))
        N[k] = np.zeros((P, G))
    H[k][pix[r["prompt_idx"]], r["gate"]] += r["hits"]
    N[k][pix[r["prompt_idx"]], r["gate"]] += r["needed"]
ok = True
for B in budgets:
    ref = N[(arms[0], B)]
    for a in arms:
        if not np.array_equal(N[(a, B)], ref):
            ok = False
            print("PAIRING DIFF", a, B)
print("pairing per (budget,gate,prompt) equal across all arms:", ok)
print("needed per prompt (B=16):", N[(arms[0], 16)].sum(1).astype(int).tolist())
print("needed equal across gates per prompt:", all(np.all(N[(a, B)] == N[(a, B)][:, :1]) for a in arms for B in budgets))
print("hits <= needed everywhere:", all(np.all(H[k] <= N[k]) for k in H))


def boot_idx(n, n_boot=2000, seed=0):
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def ci_frac(h, n):
    idx = boot_idx(len(h))
    s = h[idx].sum(1)
    t = n[idx].sum(1)
    v = t > 0
    lo, hi = np.percentile(s[v] / t[v], [2.5, 97.5])
    return float(h.sum() / n.sum()), float(lo), float(hi)


def ci_delta(ha, hb, n):
    idx = boot_idx(len(n))
    d = (ha - hb)[idx].sum(1)
    t = n[idx].sum(1)
    v = t > 0
    lo, hi = np.percentile(d[v] / t[v], [2.5, 97.5])
    return float((ha - hb).sum() / n.sum()), float(lo), float(hi)


def reading(d, lo, hi, mat=0.05):
    if lo > 0 and d >= mat:
        return "SIGNAL"
    if hi < 0:
        return "NEGATIVE"
    return "NOT-SHOWN"


pc = payload["conclusion"]
state = {"max": 0.0, "n": 0, "worst": None}


def cmp(a, b, what):
    state["n"] += 1
    dv = abs(float(a) - float(b))
    if dv > state["max"]:
        state["max"], state["worst"] = dv, what
for (a, B) in H:
    name = f"{a}|B={B}"
    t = pc["tables"][name]
    p, lo, hi = ci_frac(H[(a, B)].sum(1), N[(a, B)].sum(1))
    cmp(p, t["all"]["point"], name + " pt")
    cmp(lo, t["all"]["ci_lo"], name + " lo")
    cmp(hi, t["all"]["ci_hi"], name + " hi")
    cmp(N[(a, B)].sum(), t["all"]["needed"], name + " needed")
    for g in gates:
        p, lo, hi = ci_frac(H[(a, B)][:, g], N[(a, B)][:, g])
        tg = t["per_gate"][str(g)]
        cmp(p, tg["point"], f"{name} g{g} pt")
        cmp(lo, tg["ci_lo"], f"{name} g{g} lo")
        cmp(hi, tg["ci_hi"], f"{name} g{g} hi")
print("n tables in payload", len(pc["tables"]), "recomputed", len(H))
enc = header["encoding"]
suf = {"prev_table": "b", "cur_table_at_prev": "a"}[enc]
oth = {"b": "a", "a": "b"}[suf]
FB, HB, FBo = f"free_bigram_{suf}", f"history_bigram_{suf}", f"free_bigram_{oth}"
dl = {}
PAIRS = (("address_beyond_token_re", "history_tok", "free_tok"), ("gate_eq", "history_tok", FB),
         ("address_beyond_bigram", HB, FB), ("bigram_gain", FB, "free_tok"),
         ("gate_eq_unselected", "history_tok", FBo), ("free_all-free_bigram", "free_all", FB),
         ("history_all-free_all", "history_all", "free_all"), ("history_bigram-history_tok", HB, "history_tok"),
         ("history_tok-history", "history_tok", "history"),
         ("free_bigram_b-free_bigram_a", "free_bigram_b", "free_bigram_a"))
for B in budgets:
    for name, a, b in PAIRS:
        d, lo, hi = ci_delta(H[(a, B)].sum(1), H[(b, B)].sum(1), N[(a, B)].sum(1))
        key = f"{name}|B={B}"
        dl[key] = (d, lo, hi)
        t = pc["deltas"][key]
        cmp(d, t["delta"], key + " d")
        cmp(lo, t["lo"], key + " lo")
        cmp(hi, t["hi"], key + " hi")
        cmp(N[(a, B)].sum(), t["needed"], key + " needed")
print("n deltas payload", len(pc["deltas"]), "recomputed", len(dl), "same keys", set(dl) == set(pc["deltas"]))
lab = pc["labels"]
eq, add, gain, abt = dl["gate_eq|B=16"], dl["address_beyond_bigram|B=16"], dl["bigram_gain|B=16"], dl["address_beyond_token_re|B=16"]
r_eq, r_add, r_gain = reading(*eq), reading(*add), reading(*gain)
if r_eq == "SIGNAL" and r_add == "SIGNAL":
    label = "SURVIVES"
elif r_eq == "SIGNAL":
    label = "READER-INCONSISTENT"
elif r_add == "SIGNAL":
    label = "COMPLEMENTARY"
else:
    label = "FREE-HISTORY"
print("my readings", r_eq, r_add, r_gain, "label", label)
print("payload readings", lab["gate_eq_reading"], lab["address_beyond_bigram_reading"], lab["bigram_gain_reading"], lab["label"])
pg = {}
for g in gates:
    pg[g] = H[(FB, 16)][:, g].sum() / N[(FB, 16)][:, g].sum() - H[("free_tok", 16)][:, g].sum() / N[("free_tok", 16)][:, g].sum()
    cmp(pg[g], lab["per_gate_bigram_gain"][str(g)], f"pg gain g{g}")
srt = sorted(pg.items(), key=lambda kv: -kv[1])
print("per-gate gain top 4:", [(g, round(v, 4)) for g, v in srt[:4]], "argmax", srt[0][0], "payload", lab["largest_gain_gate"])
print("gate0 share of summed per-gate gain:", round(pg[0] / sum(pg.values()), 4))
print("mean per-gate gain", round(float(np.mean(list(pg.values()))), 6), "vs pooled", round(gain[0], 6))
print("min per-gate gain", round(min(pg.values()), 4), "n negative gates", sum(v < 0 for v in pg.values()))
for nm, v in (("gate_eq", eq), ("address_beyond_bigram", add), ("bigram_gain", gain), ("address_beyond_token_re", abt)):
    cmp(v[0], lab[nm]["delta"], "lab " + nm)
    cmp(v[1], lab[nm]["lo"], "lab " + nm)
    cmp(v[2], lab[nm]["hi"], "lab " + nm)
print("MAX ABS DISCREPANCY", state["max"], "over", state["n"], "compared numbers; worst", state["worst"])
prov = payload["provenance"]
vt = prov["val_table"]
lam_ok = True
for a, tab in vt.items():
    best, bl = -np.inf, None
    for lk in sorted(tab, key=float):
        if tab[lk] > best:
            best, bl = tab[lk], float(lk)
    if bl != prov["lambda_selected"][a]:
        lam_ok = False
        print("LAMBDA MISMATCH", a, bl, prov["lambda_selected"][a])
print("lambda selection reproduces from val_table:", lam_ok)
vb = vt["free_bigram_b"][str(prov["lambda_selected"]["free_bigram_b"])]
va = vt["free_bigram_a"][str(prov["lambda_selected"]["free_bigram_a"])]
print("val best free_bigram_b", vb, "free_bigram_a", va, "selected", prov["encoding_selected"])
print("val tables:")
for a, t in vt.items():
    print(" ", a, {k: round(v, 5) for k, v in t.items()})
for a in ["free_tok", "history", "history_tok", "free_bigram_b", "free_bigram_a", "history_bigram_b", "history_bigram_a", "free_all", "history_all"]:
    print(f"B16 {a} {H[(a, 16)].sum() / N[(a, 16)].sum():.4f}")
for k in ["address_beyond_token_re|B=16", "gate_eq|B=16", "address_beyond_bigram|B=16", "bigram_gain|B=16", "gate_eq|B=8", "gate_eq|B=32"]:
    d, lo, hi = dl[k]
    print(f"{k} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]")
print("n_positions", prov["n_positions"])
print("runtime_s", prov["runtime_s"])
print("coverage test", prov["table_coverage"]["test"])
print("git", prov["git_commit"], prov["git_status_tracked"])
print("instrument sha", prov["instrument_sha256"], "frozen", prov["frozen_instrument"])
print("lambda_selected", prov["lambda_selected"])
print("grid_edge", prov["lambda_grid_edge"])
print("seeds", prov["seeds"], "smoke", prov["smoke"], prov["smoke_split_val"], "committed", prov["committed_cell"])

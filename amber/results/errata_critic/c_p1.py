"""Critic: independent recompute of E2, E3, E4, E5, E6, E8b, E10 from raw shards.
Own code; amber loaders used only as a cross-check of the raw reads."""
import sys
sys.modules["torch"] = None
import json, glob, math
from pathlib import Path
import numpy as np

REPO = Path(r"C:\Users\Michael\Desktop\SaaS\amber")
R = REPO / "results"
PAY = json.loads((R / "errata_recompute.json").read_text(encoding="utf-8"))["rows"]
out = {}

def maxdisc(mine, theirs, tag):
    """print and return abs / rel discrepancy"""
    if isinstance(mine, (int, np.integer)) and isinstance(theirs, int):
        d = abs(int(mine) - theirs); print(f"  {tag}: mine={mine} payload={theirs} diff={d}"); return float(d), 0.0
    a = abs(float(mine) - float(theirs)); rel = a / abs(float(theirs)) if theirs else a
    print(f"  {tag}: mine={mine!r} payload={theirs!r} abs={a:.3e} rel={rel:.3e}"); return a, rel

# ---------------- raw generate read ----------------
gmeta = json.loads((R / "p1/generate/meta.json").read_text())
gshards = sorted(glob.glob(str(R / "p1/generate/shard_*.npz")))
raw = {}
pad_issues = 0
for f in gshards:
    z = np.load(f)
    ids, pl, rows = z["ids"], z["prompt_len"], z["row"]
    for i in range(ids.shape[0]):
        a = ids[i]
        neg = np.flatnonzero(a < 0)
        if neg.size:
            # padding must be a contiguous right tail of -1
            if not (np.all(a[neg[0]:] < 0) and np.all(a[neg[0]:] == -1)):
                pad_issues += 1
            a = a[:neg[0]]
        assert int(rows[i]) not in raw
        raw[int(rows[i])] = (a.astype(np.int64), int(pl[i]))
print("generate shards", len(gshards), "rows", len(raw), "pad issues", pad_issues, "rows==0..199", sorted(raw) == list(range(200)))
# cross-check with amber's loader
from amber.real.divergence import load_generated, load_rank
lg = load_generated(R / "p1")
assert [r for r, _, _ in lg] == list(range(200)), "load_generated row order"
assert all(np.array_equal(raw[r][0], ids) and raw[r][1] == pl for r, ids, pl in lg)
print("raw read == load_generated: OK")

gen = {r: ids[pl:] for r, (ids, pl) in raw.items()}
glen = {r: len(g) for r, g in gen.items()}

# ---------------- E2 ----------------
print("E2")
max_new = gmeta["max_new"]
n_cap = sum(1 for v in glen.values() if v == max_new)
last = {r: int(g[-1]) if len(g) else None for r, g in gen.items()}
n_eos = sum(1 for v in last.values() if v == 128001)
n_eot = sum(1 for v in last.values() if v == 128009)
both = sum(1 for r in gen if glen[r] == max_new and last[r] == 128001)
neither = sum(1 for r in gen if glen[r] != max_new and last[r] != 128001)
eos_anywhere = sum(1 for g in gen.values() if (g == 128001).any())
eos_mid = sum(1 for g in gen.values() if (g[:-1] == 128001).any())
over = sum(1 for v in glen.values() if v > max_new)
e2 = dict(max_new=max_new, n_cap=n_cap, n_eos=n_eos, n_eot=n_eot, min_gen=min(glen.values()), n_empty=sum(v == 0 for v in glen.values()),
          n_rows=len(glen), total_gen=sum(glen.values()))
print(" ", e2, "cap&eos", both, "neither", neither, "eos anywhere", eos_anywhere, "eos mid", eos_mid, "over cap", over)
# what threshold gives 193?
srt = sorted(glen.values()); print("  sorted short lens:", srt[:16])
d = 0
for k, v in e2.items():
    d = max(d, maxdisc(v, PAY["E2"]["value"][k], k)[0])
st = "CONFIRMED" if (n_cap == 193 and e2["min_gen"] == 21 and e2["n_empty"] == 0) else "CORRECTED"
out["E2"] = (st, d); print("  status", st, "payload", PAY["E2"]["status"])

# ---------------- E3 ----------------
print("E3")
def my_loop(g, W, P):
    g = [int(x) for x in g]; n = len(g)
    if n < W:
        return 0.0, 0
    t = g[n - W:]
    per = 0
    for p in range(1, P + 1):
        if all(t[i] == t[i + p] for i in range(W - p)):
            per = p; break
    if per == 0:
        return 0.0, 0
    s = W
    while s < n and g[n - s - 1] == g[n - s - 1 + per]:
        s += 1
    return s / n, per

from amber.real.longhorizon import loop_fraction, distinct_ngram_ratio
order = list(range(200))
def loop_stats(W, P, t):
    fl, tok = [], 0
    for r in order:
        fr, per = my_loop(gen[r], W, P)
        fl.append(fr >= t); tok += int(round(fr * glen[r]))
    return fl, tok
fl, tok = loop_stats(128, 64, 0.5)
# cross-check against amber's function
mism = 0
for r in order:
    a = loop_fraction(gen[r], window=128, max_period=64); b = my_loop(gen[r], 128, 64)
    mism += (abs(a[0] - b[0]) > 0 or a[1] != b[1])
print("  my_loop vs amber loop_fraction mismatches:", mism)
n_looped = sum(fl); looped_rows = [r for r, f in zip(order, fl) if f]
print("  n_looped", n_looped, "tokens_in_loop", tok, "share", tok / sum(glen.values()))
print("  looped rows all full-cap:", all(glen[r] == 256 for r in looped_rows), " looped among EOS rows:", sum(1 for r in looped_rows if last[r] == 128001))
# tokens in loop restricted to looped rows only (alternative reading of sum(tokens_in_loop))
tok_looped_only = sum(int(round(my_loop(gen[r], 128, 64)[0] * glen[r])) for r in looped_rows)
print("  tokens_in_loop over LOOPED rows only:", tok_looped_only)
d3 = 0
d3 = max(d3, maxdisc(n_looped, PAY["E3"]["value"]["n_looped"], "n_looped")[0])
d3 = max(d3, maxdisc(tok, PAY["E3"]["value"]["tokens_in_loop"], "tokens_in_loop")[0])
print("  looped_rows equal:", looped_rows == PAY["E3"]["value"]["looped_rows"])
# grid
gmis = 0; gmin = (10**9, 10**9)
pg = {(x["W"], x["P"], x["t"]): x for x in PAY["E3"]["value"]["grid"]}
for W in (64, 128, 192, 256):
    for P in (16, 32, 64, 128):
        if P >= W: continue
        for t in (0.25, 0.5, 0.75):
            f2, tk2 = loop_stats(W, P, t)
            x = pg[(W, P, t)]
            if x["n_looped"] != sum(f2) or x["tokens_in_loop"] != tk2:
                gmis += 1; print("   grid mismatch", W, P, t, sum(f2), tk2, x)
            gmin = (min(gmin[0], sum(f2)), min(gmin[1], tk2))
print("  grid mismatches", gmis, "len", len(pg), "grid min n_looped/tokens", gmin)
# repetition (a) and (b), own code
pooled_d = pooled_t = 0; ratios = []; num = den = 0
for r in order:
    g = [int(x) for x in gen[r]]
    grams = [tuple(g[i:i + 4]) for i in range(len(g) - 3)]
    if grams:
        pooled_d += len(set(grams)); pooled_t += len(grams); ratios.append(len(set(grams)) / len(grams))
    seen = set()
    for i in range(3, len(g)):
        k = tuple(g[i - 3:i + 1]); num += k in seen; seen.add(k)
    den += max(len(g) - 3, 0)
# amber cross-check of distinct ratio
assert all(abs(distinct_ngram_ratio(gen[r], 4) - (len(set(tuple(int(x) for x in gen[r][i:i+4]) for i in range(len(gen[r])-3)))/(len(gen[r])-3))) < 1e-15 for r in order)
dv = PAY["E3"]["value"]
d3 = max(d3, maxdisc(pooled_d, dv["distinct_4gram"]["pooled_distinct"], "pooled_distinct")[0])
d3 = max(d3, maxdisc(pooled_t, dv["distinct_4gram"]["pooled_total"], "pooled_total")[0])
d3 = max(d3, maxdisc(float(np.mean(ratios)), dv["distinct_4gram"]["unweighted_mean_ratio"], "unweighted_mean_ratio")[1])
d3 = max(d3, maxdisc(num, dv["repeat_4gram_share"]["num"], "rep num")[0])
d3 = max(d3, maxdisc(den, dv["repeat_4gram_share"]["den"], "rep den")[0])
st = "CORRECTED" if (n_looped >= 20 or tok >= 0.10 * sum(glen.values())) else "CONFIRMED"
out["E3"] = (st, d3); print("  status", st, "payload", PAY["E3"]["status"])
flags = dict(zip(order, fl))

# ---------------- E4 ----------------
print("E4")
dmeta = json.loads((R / "p1/draft/meta.json").read_text())
draft = {}
for f in sorted(glob.glob(str(R / "p1/draft/shard_*.npz"))):
    z = np.load(f); off = z["offsets"]
    for i, r in enumerate(z["row"]):
        draft[int(r)] = (z["ranks"][off[i]:off[i + 1]].astype(np.int64), z["log2q"][off[i]:off[i + 1]])
assert sorted(draft) == list(range(200))
lr = load_rank(R / "p1", "draft")
assert [p["row"] for p in lr["per_prompt"]] == list(range(200))
assert all(np.array_equal(draft[p["row"]][0], p["rank"]) and np.array_equal(draft[p["row"]][1], p["log2q"]) for p in lr["per_prompt"])
print("  raw draft == load_rank OK; per-row length == gen_len:", all(len(draft[r][0]) == glen[r] for r in order))
print("  min rank", min(int(draft[r][0].min()) for r in order))
def gbits(n):
    assert n >= 1
    return 2 * (int(n).bit_length() - 1) + 1
def my_amber(ranks):
    b = 0; gap = 0
    for x in ranks:
        x = int(x)
        if x == 1: gap += 1; continue
        b += gbits(gap + 1) + gbits(x - 1); gap = 0
    return b
p1 = json.loads((R / "p1_divergence.json").read_text())["row"]
allr = np.concatenate([draft[r][0] for r in order]); allq = np.concatenate([draft[r][1] for r in order])
N = allr.size
a_all = my_amber(allr) / N
ac32 = float(-allq.mean()); ac64 = float(-allq.astype(np.float64).mean())
# exact (math.fsum) mean for reference
acx = -math.fsum(float(x) for x in allq) / N
print(f"  N={N} json_positions={p1['positions']} amber={a_all!r} json={p1['amber_v0_bits_per_token']!r} diff={abs(a_all-p1['amber_v0_bits_per_token']):.2e}")
print(f"  ac f32={ac32!r} f64={ac64!r} fsum={acx!r} json={p1['ac_under_draft_bits_per_token']!r}  f32diff={abs(ac32-p1['ac_under_draft_bits_per_token']):.2e} f64diff={abs(ac64-p1['ac_under_draft_bits_per_token']):.2e}")
inst_ok_f32 = abs(a_all - p1['amber_v0_bits_per_token']) < 1e-9 and abs(ac32 - p1['ac_under_draft_bits_per_token']) < 1e-9
inst_ok_f64 = abs(a_all - p1['amber_v0_bits_per_token']) < 1e-9 and abs(ac64 - p1['ac_under_draft_bits_per_token']) < 1e-9
print("  instrument check f32:", inst_ok_f32, " f64 (pre-amendment reading):", inst_ok_f64)
strata = {}
for name, sel in (("all", order), ("looped", [r for r in order if flags[r]]), ("nonlooped", [r for r in order if not flags[r]])):
    rk = np.concatenate([draft[r][0] for r in sel]); q = np.concatenate([draft[r][1] for r in sel]); n = rk.size
    cc = my_amber(rk) / n; pa = sum(my_amber(draft[r][0]) for r in sel) / n
    ac = -math.fsum(float(x) for x in q) / n
    ac_f32 = float(-q.mean())
    strata[name] = dict(N=n, rows=len(sel), amber_concat=cc, amber_perarchive=pa, ac=ac, delta_concat=cc - ac, rel_perarchive=pa / ac - 1,
                        delta_concat_f32=cc - ac_f32, rel_perarchive_f32=pa / ac_f32 - 1)
d4 = 0; d4r = 0
for s in strata:
    for k in ("N", "rows", "amber_concat", "amber_perarchive", "ac", "delta_concat", "rel_perarchive"):
        a, rel = maxdisc(strata[s][k], PAY["E4"]["value"]["strata"][s][k], f"{s}.{k}")
        d4 = max(d4, a); d4r = max(d4r, rel)
print("  f32-ac variants: looped delta", strata["looped"]["delta_concat_f32"], "nonlooped rel", strata["nonlooped"]["rel_perarchive_f32"])
sl, sn = strata["looped"], strata["nonlooped"]
st = "CORRECTED" if (np.sign(sl["delta_concat"]) != np.sign(sn["delta_concat"]) or abs(sn["rel_perarchive"]) > 0.02) else "CONFIRMED"
print("  sign looped", np.sign(sl["delta_concat"]), "sign nonlooped", np.sign(sn["delta_concat"]), "|rel_nonlooped|", abs(sn["rel_perarchive"]))
# also with grid extremes of loop rule: does status survive?
for (W, P, t) in ((256, 16, 0.5), (192, 128, 0.5), (64, 16, 0.75)):
    f2, _ = loop_stats(W, P, t); fd = dict(zip(order, f2))
    res = {}
    for name, flag in (("looped", True), ("nonlooped", False)):
        sel = [r for r in order if fd[r] == flag]
        rk = np.concatenate([draft[r][0] for r in sel]); q = np.concatenate([draft[r][1] for r in sel]); n = rk.size
        ac = float(-q.astype(np.float64).mean()); res[name] = (my_amber(rk) / n - ac, sum(my_amber(draft[r][0]) for r in sel) / n / ac - 1)
    print(f"   sensitivity W{W}/P{P}/t{t}: delta_looped={res['looped'][0]:+.4f} delta_nonlooped={res['nonlooped'][0]:+.4f} rel_pa_nonlooped={res['nonlooped'][1]:+.4f}")
out["E4"] = (st, d4); print("  status", st, "payload", PAY["E4"]["status"], "max abs", d4, "max rel", d4r)

# ---------------- E5 ----------------
print("E5")
sh = gmeta["shards"]; print("  n_shards", len(sh), "keys", sorted(sh, key=int)[:3], "...")
nt = np.array([sh[k]["new_tokens"] for k in sorted(sh, key=int)], float); sec = np.array([sh[k]["seconds"] for k in sorted(sh, key=int)], float)
tps = np.array([sh[k]["tok_per_s"] for k in sorted(sh, key=int)], float)
# does new_tokens per shard equal the generated tokens of its rows?
ntchk = all(sh[k]["new_tokens"] == sum(glen[r] for r in range(sh[k]["rows"][0], sh[k]["rows"][1] + 1)) for k in sh)
print("  shard new_tokens == sum gen_len over its rows:", ntchk, " tok_per_s == new/sec:", np.allclose(tps, nt / sec, rtol=0, atol=1e-9))
e5 = dict(weighted=nt.sum() / sec.sum(), unweighted=tps.mean(), median=float(np.median(tps)), min=tps.min(), max=tps.max(), n=len(sh))
d5 = 0; d5r = 0
for k, v in e5.items():
    a, rel = maxdisc(v, PAY["E5"]["value"][k], k); d5 = max(d5, a); d5r = max(d5r, rel)
print(f"  weighted {e5['weighted']:.4f} -> {e5['weighted']:.1f}; unweighted {e5['unweighted']:.4f}; median {e5['median']:.2f}")
print("  excluding shard 0..k slow warmup:", [(i, round(nt[i:].sum() / sec[i:].sum(), 2)) for i in range(0, 4)])
print("  per-shard tok/s:", np.round(tps, 1).tolist())
st = "CONFIRMED" if f"{e5['weighted']:.1f}" == "32.8" else "CORRECTED"
out["E5"] = (st, d5); print("  status", st, "payload", PAY["E5"]["status"], "max rel", d5r)

# ---------------- E6 ----------------
print("E6")
enc = json.loads((R / "p4/encode_meta.json").read_text())
pr = enc["per_row"]; keys = sorted(pr, key=int)
print("  n per_row", len(keys), "rows==0..199", [int(k) for k in keys] == list(range(200)))
Ls = np.array([pr[k]["length"] for k in keys], float); Ss = np.array([pr[k]["score_seconds"] for k in keys], float)
print("  length == gen_len for all rows:", all(pr[k]["length"] == glen[int(k)] for k in keys))
agg = Ls.sum() / Ss.sum()
print(f"  aggregate {agg!r} json {enc['encode_pos_per_s']!r} diff {abs(agg-enc['encode_pos_per_s']):.2e}; rounds to {agg:.0f}")
v = Ls / Ss; med = float(np.median(v))
d6 = 0
for f in (0.1, 0.25, 0.5):
    stl = v < f * med
    clean = Ls[~stl].sum() / Ss[~stl].sum()
    x = [g for g in PAY["E6"]["value"]["grid"] if g["f"] == f][0]
    print(f"  f={f}: n_stalled={stl.sum()} sec_stalled={Ss[stl].sum():.4f}/{Ss.sum():.4f} clean={clean:.2f} 1.5*agg={1.5*agg:.1f}")
    for k, mv in (("n_stalled", int(stl.sum())), ("seconds_stalled", Ss[stl].sum()), ("clean", clean), ("median_v", med), ("aggregate", agg), ("seconds_total", Ss.sum())):
        d6 = max(d6, maxdisc(mv, x[k], f"f{f}.{k}")[1] if not isinstance(mv, int) else maxdisc(mv, x[k], f"f{f}.{k}")[0])
stl = v < 0.25 * med
print("  pinned stalled rows", np.flatnonzero(stl).tolist() == PAY["E6"]["value"]["pinned"]["stalled_rows"])
print("  stalled rows detail (row, len, sec, v):", [(int(i), int(Ls[i]), round(Ss[i], 4), round(v[i], 1)) for i in np.flatnonzero(stl)])
# short rows: is the stall rule picking up tiny rows whose per-row rate is dominated by fixed overhead?
print("  rows with length < 64:", [(i, int(Ls[i]), round(Ss[i], 4), round(v[i], 1)) for i in range(200) if Ls[i] < 64])
# alternative: drop only the 2+ second stalls (seconds > 1.0)
big = Ss > 1.0
print(f"  alt (rows with >1s): n={big.sum()} clean={Ls[~big].sum()/Ss[~big].sum():.1f}")
# robustness: exclude rows 0 (warm-up) only
print(f"  exclude row 0 only: {Ls[1:].sum()/Ss[1:].sum():.1f}")
st = "CONFIRMED" if (f"{agg:.0f}" == "991" and Ls[~stl].sum() / Ss[~stl].sum() < 1.5 * agg) else "CORRECTED"
out["E6"] = (st, d6); print("  status", st, "payload", PAY["E6"]["status"])

# ---------------- E8b ----------------
print("E8b")
tot_pos = 0; tot_fail = 0; d8 = 0
for arm in ("cuda_fp32", "cpu_fp32"):
    rows_, first, nd = [], [], []
    for f in sorted(glob.glob(str(R / "p4" / f"decode_{arm}" / "shard_*.npz"))):
        z = np.load(f); rows_ += z["row"].tolist(); first += z["first"].tolist(); nd += z["n_decoded"].tolist()
    nf = sum(1 for x in first if x >= 0); pos = sum(nd)
    full = all(nd[i] == glen[rows_[i]] for i in range(len(rows_)))
    print(f"  {arm}: rows={len(rows_)} unique={len(set(rows_))} rows==range? {rows_ == list(range(len(rows_)))} fail={nf} positions={pos} n_decoded==gen_len all: {full}")
    pv = PAY["E8b"]["value"][arm]
    for k, mv in (("n_rows", len(rows_)), ("n_fail", nf), ("positions", pos)):
        d8 = max(d8, maxdisc(mv, pv[k], f"{arm}.{k}")[0])
    tot_pos += pos; tot_fail += nf
d8 = max(d8, maxdisc(tot_pos, PAY["E8b"]["value"]["positions_total"], "positions_total")[0])
d8 = max(d8, maxdisc(tot_fail, PAY["E8b"]["value"]["n_fail_total"], "n_fail_total")[0])
print("  sum gen_len rows 0..23:", sum(glen[r] for r in range(24)))
st = "CONFIRMED" if (tot_fail == 0 and 54500 <= tot_pos < 55500) else "CORRECTED"
out["E8b"] = (st, d8); print("  status", st, "payload", PAY["E8b"]["status"])

# ---------------- E10 ----------------
print("E10")
dsh = dmeta["shards"]; ks = sorted(dsh, key=int)
pos = np.array([dsh[k]["positions"] for k in ks], float); sec = np.array([dsh[k]["seconds"] for k in ks], float)
print("  n_shards", len(ks), "positions sum", pos.sum())
w = pos.sum() / sec.sum(); uw = float(np.mean(pos / sec))
d10 = 0; d10r = 0
for k, mv in (("weighted", w), ("unweighted", uw), ("median", float(np.median(pos / sec))), ("min", (pos / sec).min()), ("max", (pos / sec).max())):
    a, rel = maxdisc(mv, PAY["E10"]["value"]["draft_scoring"][k], k); d10 = max(d10, a); d10r = max(d10r, rel)
for k in ("content_bytes_per_token", "amber_v0_bits_per_token", "ac_under_draft_bits_per_token", "zstd19_bits_per_token", "positions", "divergence_rate"):
    a, rel = maxdisc(p1[k], PAY["E10"]["value"][k], k); d10 = max(d10, a)
# independent: divergence rate from ranks
print("  divergence from ranks:", float((allr != 1).mean()), "json", p1["divergence_rate"])
st = "CONFIRMED" if (9150 <= w < 9250 and f"{p1['content_bytes_per_token']:.2f}" == "4.73") else "CORRECTED"
print(f"  weighted={w:.2f}  -> '9.2k' ; content_bytes {p1['content_bytes_per_token']:.4f}")
out["E10"] = (st, d10); print("  status", st, "payload", PAY["E10"]["status"], "max rel", d10r)

json.dump({k: list(v) for k, v in out.items()}, open(Path(__file__).with_suffix(".out.json"), "w"), indent=1)
print(out)

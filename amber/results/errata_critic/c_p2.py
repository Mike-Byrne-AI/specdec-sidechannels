"""Critic: independent E8a, E8c, E9 (JSON reads + own re-simulation from the P2 dumps)."""
import sys
sys.modules["torch"] = None
import json, glob, hashlib
from pathlib import Path
import numpy as np

REPO = Path(r"C:\Users\Michael\Desktop\SaaS\amber"); R = REPO / "results"; D = R / "p2_llama32"
PAY = json.loads((R / "errata_recompute.json").read_text(encoding="utf-8"))["rows"]
B = json.loads((R / "p2b_escape_robustness.json").read_text(encoding="utf-8"))
out = {}

def trow(rows, theta, m):
    hits = [r for r in rows if r["theta"] == theta and r["m"] == m]
    assert len(hits) == 1, (theta, m, len(hits)); return hits[0]

# ---------------- E8a (JSON) ----------------
print("E8a")
rows = B["report"]["cpu_fp32"]["decoders"]["cuda_fp32_b1"]
r0 = trow(rows, 0.0, 2)
mine = {"n": r0["n"], "desync_total_theta0": r0["desync_total"], "A_desync_gap_max_theta0": r0["A_desync_gap"]["max"],
        "desyncs_theta0": r0["desyncs"], "desync_total_by_theta_m": {f"{r['theta']}/{r['m']}": r["desync_total"] for r in rows}}
pv = PAY["E8a"]["value"]; d8a = 0
for k in mine:
    eq = mine[k] == pv[k]; print(f"  {k}: mine={mine[k]} payload={pv[k]} equal={eq}"); d8a = max(d8a, 0 if eq else 1)
print("  symbol sum check", sum(r0["desyncs"].values()) == r0["desync_total"], "positions", B["positions"])
st = "CONFIRMED" if (r0["desync_total"] == 0 and r0["n"] == 49056) else "CORRECTED"
out["E8a"] = (st, d8a); print("  status", st, "payload", PAY["E8a"]["status"])

# ---------------- E9 (JSON) ----------------
print("E9")
def depth(row):
    sc = row["symbol_counts"]; byr = row["C_desync_by_rank"]
    prim = {1: row["desyncs"]["A"] / sc["A"]}
    for r in range(2, 65):
        if str(r) in byr and byr[str(r)]["n"]:
            prim[r] = byr[str(r)]["desync"] / byr[str(r)]["n"]
    bk = {}
    for lo, hi in ((2, 2), (3, 8), (9, 16), (17, 64)):
        ds = sum(byr[str(r)]["desync"] for r in range(lo, hi + 1) if str(r) in byr)
        ns = sum(byr[str(r)]["n"] for r in range(lo, hi + 1) if str(r) in byr)
        bk[(lo, hi)] = ds / ns
    # consistency: per-rank C desync sum == desyncs.C ; per-rank n sum == symbol_counts.C
    cs = sum(v["desync"] for v in byr.values()); cn = sum(v["n"] for v in byr.values())
    return prim, bk, (cs == row["desyncs"]["C"], cn == sc["C"]), row["desync_total"] / row["n"]
d9 = 0.0; d9n = 0
for enc, rep in B["report"].items():
    for dec, rws in rep["decoders"].items():
        prim, bk, cons, ov = depth(trow(rws, 0.0, 2))
        if not all(cons): print("   CONSISTENCY FAIL", enc, dec, cons)
        pt = PAY["E9"]["value"]["tables"][enc][dec]
        for r, v in prim.items():
            d9 = max(d9, abs(v - pt["primary"][str(r)])); d9n += 1
        for (lo, hi), v in bk.items():
            d9 = max(d9, abs(v - pt["buckets"][f"{lo}-{hi}"]["primary"]))
        d9 = max(d9, abs(ov - pt["overall"]))
print("  E9 tables max abs discrepancy", d9, "over", d9n, "per-rank entries; payload has encoders", list(PAY["E9"]["value"]["tables"]))
bf = trow(B["report"]["cpu_fp32"]["decoders"]["cuda_bf16_b1"], 0.0, 2); fp = trow(B["report"]["cpu_fp32"]["decoders"]["cuda_fp16_b1"], 0.0, 2)
pb, bb, _, _ = depth(bf); pf, bfk, _, _ = depth(fp)
pct = lambda v, nd: f"{100*v:.{nd}f}"
checks = {"bf16_rank2_2.7": pct(pb[2], 1) == "2.7", "bf16_rank3_9.3": pct(pb[3], 1) == "9.3", "bf16_rank4_15.3": pct(pb[4], 1) == "15.3",
          "bf16_rank8_25.6": pct(pb[8], 1) == "25.6", "bf16_17-64_60": pct(bb[(17, 64)], 0) == "60",
          "fp16_rank2_0.4": pct(pf[2], 1) == "0.4", "fp16_rank3_1.5": pct(pf[3], 1) == "1.5", "fp16_rank8_3.7": pct(pf[8], 1) == "3.7",
          "fp16_17-64_14": pct(bfk[(17, 64)], 0) == "14", "headline_rank2_3pct": pct(pb[2], 0) == "3",
          "headline_rank3-8_9-26": min(round(100 * pb[r]) for r in range(3, 9)) == 9 and max(round(100 * pb[r]) for r in range(3, 9)) == 26}
print("  theta0 values: bf16 r2", pct(pb[2], 2), "r3", pct(pb[3], 2), "r4", pct(pb[4], 2), "r8", pct(pb[8], 2), "17-64", pct(bb[(17, 64)], 2),
      "| fp16 r2", pct(pf[2], 2), "r3", pct(pf[3], 2), "r8", pct(pf[8], 2), "17-64", pct(bfk[(17, 64)], 2))
print("  bf16 ranks 3..8 rounded:", [round(100 * pb[r]) for r in range(3, 9)], " A top1", pct(pb[1], 2))
for k, v in checks.items():
    pvv = PAY["E9"]["value"]["printed_figure_checks"][k]
    print(f"   {k}: mine={v} payload={pvv}" + ("" if v == pvv else "  <-- MISMATCH"))
st = "CONFIRMED" if all(checks.values()) else "CORRECTED"
out["E9"] = (st, d9); print("  status", st, "payload", PAY["E9"]["status"])
# Independent check of the F-10 rank-2 "2.7% / 0.4%" theta claim, and the body's whole item (3)
print("  F-10 item (3) under every (theta,m), encoder cpu_fp32:")
for dec in ("cuda_bf16_b1", "cuda_fp16_b1", "cuda_bf16_b8"):
    for r in B["report"]["cpu_fp32"]["decoders"][dec] if dec != "cuda_bf16_b8" else []:
        p, b, _, _ = depth(r)
        print(f"   {dec} th{r['theta']}/m{r['m']}: C={r['symbol_counts']['C']} Cdes={r['desyncs']['C']} ({100*r['desyncs']['C']/r['symbol_counts']['C']:.1f}%) "
              f"r2={pct(p[2],2)} r3={pct(p[3],2)} r4={pct(p[4],2)} r8={pct(p[8],2)} 17-64={pct(b[(17,64)],1)} A={r['desyncs']['A']} T={r['desyncs']['T']} "
              f"Tn={r['symbol_counts']['T']} sc_C={r['setcoded_C']['desync']}")
# bf16_b1 -> bf16_b8 "3,819 (22.9%; rank 2 2.1%, 3 7.5%)"
for r in B["report"]["cuda_bf16_b1"]["decoders"]["cuda_bf16_b8"]:
    p, b, _, _ = depth(r)
    print(f"   bf16_b1->bf16_b8 th{r['theta']}/m{r['m']}: C={r['symbol_counts']['C']} Cdes={r['desyncs']['C']} ({100*r['desyncs']['C']/r['symbol_counts']['C']:.1f}%) r2={pct(p[2],2)} r3={pct(p[3],2)} A={r['desyncs']['A']}")
matches = []
for r in B["report"]["cpu_fp32"]["decoders"]["cuda_bf16_b1"]:
    rf = trow(B["report"]["cpu_fp32"]["decoders"]["cuda_fp16_b1"], r["theta"], r["m"])
    if pct(depth(r)[0][2], 1) == "2.7" and pct(depth(rf)[0][2], 1) == "0.4":
        matches.append(f"{r['theta']}/{r['m']}")
print("  (theta,m) where bf16 r2 -> 2.7 and fp16 r2 -> 0.4:", matches, " payload:", PAY["E9"]["value"]["theta_m_matching_printed_rank2"])

# ---------------- dumps: manifest check (own hashing) ----------------
print("manifest")
man = [ln.split("  ", 1) for ln in (R / "p2_dumps.sha256").read_text(encoding="utf-8").splitlines() if ln.strip()]
need = [(h, p) for h, p in man if p.startswith(("results/p2_llama32/corpus", "results/p2_llama32/cpu_fp32/", "results/p2_llama32/cuda_fp32_b8/",
                                               "results/p2_llama32/cuda_fp32_b1/", "results/p2_llama32/cuda_bf16_b1/", "results/p2_llama32/cuda_fp16_b1/"))]
bad = [p for h, p in need if hashlib.sha256((REPO / p).read_bytes()).hexdigest() != h]
print("  entries checked", len(need), "bad", bad)
n_e8c = sum(1 for h, p in need if p.startswith(("results/p2_llama32/corpus", "results/p2_llama32/cpu_fp32/", "results/p2_llama32/cuda_fp32_b8/")))
print("  of which E8c scope", n_e8c, "payload manifest_checked", PAY["E8c"]["value"]["manifest_checked"])
# files present on disk in those dirs but NOT in the manifest?
for arm in ("cpu_fp32", "cuda_fp32_b8"):
    on_disk = sorted(p.relative_to(REPO).as_posix() for p in (D / arm).rglob("*") if p.is_file())
    listed = sorted(p for _, p in need if p.startswith(f"results/p2_llama32/{arm}/"))
    print(f"  {arm}: on disk {len(on_disk)} listed {len(listed)} equal {on_disk == listed}")

# ---------------- own loaders + simulate ----------------
tokens = np.load(D / "corpus.npz")["tokens"].astype(np.int64)
S, L = tokens.shape
def load(arm):
    meta = json.loads((D / arm / "meta.json").read_text())
    idx, val, rr = [], [], []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        z = np.load(D / arm / f"shard_{s:04d}.npz"); idx.append(z["idx"]); val.append(z["val"]); rr += z["rows"].tolist()
    assert rr == list(range(S)), f"{arm} rows order {rr[:10]}"
    idx = np.concatenate(idx); val = np.concatenate(val)            # (S, L, K)
    assert idx.shape[:2] == (S, L)
    # own canonical order: value desc, index asc, stable
    v64 = val.astype(np.float64)
    o = np.lexsort((idx, -v64), axis=-1)
    idx = np.take_along_axis(idx, o, -1); v64 = np.take_along_axis(v64, o, -1)
    # drop last position of each sequence (no next token)
    return idx[:, :L - 1, :].reshape(-1, idx.shape[-1]), v64[:, :L - 1, :].reshape(-1, idx.shape[-1])
true = tokens[:, 1:].reshape(-1)
print("  positions", true.size)

def rank_true(idx):
    hit = idx == true[:, None]; has = hit.any(1)
    return np.where(has, hit.argmax(1) + 1, idx.shape[1] + 1)

def mysim(eidx, ev, didx, theta, m, RMAX=64):
    re_ = rank_true(eidx); gap = ev[:, 0] - ev[:, 1]
    T = (theta > 0) & (gap < theta) & (re_ <= m)
    A = (~T) & (re_ == 1); C = (~T) & (re_ >= 2) & (re_ <= RMAX)
    res = true.copy()
    res[A] = didx[A, 0]
    res[C] = didx[C, re_[C] - 1]
    if T.any():
        es = np.sort(eidx[T, :m], 1); ds = np.sort(didx[T, :m], 1)
        slot = np.array([int(np.flatnonzero(es[i] == true[T][i])[0]) for i in range(es.shape[0])])
        res[T] = ds[np.arange(len(slot)), slot]
    des = res != true
    byr = {r: (int((C & (re_ == r)).sum()), int((des & C & (re_ == r)).sum())) for r in range(2, RMAX + 1)}
    return dict(n=int(true.size), total=int(des.sum()), A=int((des & A).sum()), C=int((des & C).sum()), T=int((des & T).sum()), X=0,
                nA=int(A.sum()), nC=int(C.sum()), nT=int(T.sum()), byr=byr, des=des, re=re_, gap=gap,
                Agapmax=float(gap[A & des].max()) if (A & des).any() else None)

enc_idx, enc_val = load("cpu_fp32")
# ---------------- E8c ----------------
print("E8c")
d_idx, _ = load("cuda_fp32_b8")
s = mysim(enc_idx, enc_val, d_idx, 0.0, 2)
rdec = rank_true(d_idx)
ev = [dict(position=int(t), sequence=int(t // (L - 1)), offset=int(t % (L - 1)), enc_rank_of_true=int(s["re"][t]), dec_rank_of_true=int(rdec[t]),
           enc_gap=float(enc_val[t, 0] - enc_val[t, 1])) for t in np.flatnonzero(s["des"])]
print("  n", s["n"], "total", s["total"], "A/C/T", s["A"], s["C"], s["T"], "events", ev)
for e in ev:
    t = e["position"]; r = e["enc_rank_of_true"]
    print(f"   seq {e['sequence']} off {e['offset']}: token {true[t]} == corpus[{e['sequence']},{e['offset']+1}]={tokens[e['sequence'], e['offset']+1]}; "
          f"enc top-6 idx {enc_idx[t,:6].tolist()} val {np.round(enc_val[t,:6],5).tolist()}; dec top-6 idx {d_idx[t,:6].tolist()}")
    # gap between the swapped pair in the encoder (rank r vs r+1)
    print(f"   enc val[r-1]-val[r] (rank {r} vs {r+1}) = {enc_val[t, r-1] - enc_val[t, r]:.3e}; enc top1-top2 gap {enc_val[t,0]-enc_val[t,1]:.5f}")
pe = PAY["E8c"]["value"]
d8c = 0
d8c = max(d8c, abs(s["n"] - pe["n"]), abs(s["total"] - pe["desync_total"]))
for k in "ACTX": d8c = max(d8c, abs(s[k] - pe["desyncs"][k]))
for r in range(2, 9):
    d8c = max(d8c, abs(s["byr"][r][0] - pe["C_desync_by_rank_2_8"][str(r)]["n"]), abs(s["byr"][r][1] - pe["C_desync_by_rank_2_8"][str(r)]["desync"]))
for a_, b_ in zip(ev, pe["events"]):
    for k in ("position", "sequence", "offset", "enc_rank_of_true", "dec_rank_of_true"):
        d8c = max(d8c, abs(a_[k] - b_[k]))
    d8c = max(d8c, abs(a_["enc_gap"] - b_["enc_gap"]))
d8c = max(d8c, abs(len(ev) - len(pe["events"])))
print("  E8c maxdisc", d8c)
# all positions where the decoder's order differs from the encoder's order within top-64 (beyond the coded rank)
diff_any = (enc_idx[:, :64] != d_idx[:, :64]).any(1)
print("  positions with any top-64 order difference (enc vs dec):", int(diff_any.sum()), "; with true token coded at a differing slot:", int(s["des"].sum()))
# other thetas for completeness
for th, m in ((0.142, 2), (0.465, 2)):
    s2 = mysim(enc_idx, enc_val, d_idx, th, m); print(f"  theta {th}/m{m}: total {s2['total']} A{s2['A']} C{s2['C']} T{s2['T']}")
st = "CONFIRMED" if s["total"] == 0 else "CORRECTED"
out["E8c"] = (st, d8c); print("  status", st, "payload", PAY["E8c"]["status"])

# ---------------- re-simulate the JSON rows E8a/E9 rely on, from dumps ----------------
print("JSON reproduction from dumps")
jd = 0
for dec in ("cuda_fp32_b1", "cuda_bf16_b1", "cuda_fp16_b1"):
    didx, _ = load(dec)
    for th, m in ((0.0, 2), (0.465, 2)):
        s2 = mysim(enc_idx, enc_val, didx, th, m)
        jr = trow(B["report"]["cpu_fp32"]["decoders"][dec], th, m)
        ok = (s2["total"] == jr["desync_total"] and s2["A"] == jr["desyncs"]["A"] and s2["C"] == jr["desyncs"]["C"] and s2["T"] == jr["desyncs"]["T"]
              and s2["nA"] == jr["symbol_counts"]["A"] and s2["nC"] == jr["symbol_counts"]["C"] and s2["nT"] == jr["symbol_counts"]["T"]
              and all(jr["C_desync_by_rank"].get(str(r), {"n": 0, "desync": 0}) == {"n": s2["byr"][r][0], "desync": s2["byr"][r][1]} for r in range(2, 65) if s2["byr"][r][0]))
        jd += 0 if ok else 1
        print(f"  cpu_fp32->{dec} th{th}/m{m}: mine total {s2['total']} (A{s2['A']} C{s2['C']} T{s2['T']}), json {jr['desync_total']}; match all fields: {ok}"
              + (f"  Agapmax {s2['Agapmax']!r} json {jr['A_desync_gap']['max']!r}" if dec == 'cuda_fp32_b1' and th == 0 else ""))
    del didx
print("  JSON-vs-dumps mismatching rows:", jd)
json.dump({k: list(v) for k, v in out.items()}, open(Path(__file__).with_suffix(".out.json"), "w"), indent=1)
print(out)

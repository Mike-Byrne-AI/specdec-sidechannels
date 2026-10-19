"""Read-only recompute for S3-C-1 (image audit 2026-10-15, section B item 2): seed-inclusive
intervals for the label-bearing rows of F-24, the corrected twin and F-25.

Reads the committed payloads and state files under results/real/ and writes seed_var_out.json next
to itself. Each row records the payload interval (reproduced to 1e-12, field "reproduced"), the
three per-seed margins, and three seed-inclusive approximations: "hypot" (the finder's normal
combination of the bootstrap SE and the seed SE, which double-counts the prompt x seed
interaction), "mom" (a two-way method of moments that subtracts that interaction, truncated at 0),
"pigeon" (a prompt x seed pigeonhole percentile bootstrap, 4000 reps, rng 20261015), plus "t2", a
seed-only t interval on 2 df. Three seeds cannot measure the component; the three brackets say how
fragile each reading is.

Pinned 2026-10-16 before the lane-B rerun, asserted by the script: all 72 rows reproduce their
payload interval and per-seed points to 1e-12; the F-25 S1_r L2 linear off2 D row reads hypot
[-0.0012, +0.0055], mom [-0.0007, +0.0050], pigeon [-0.0002, +0.0064] at four places; the F-24 S1
corrected-twin Mn_r rows (primary, replication) read hypot [-0.0006, +0.0071] / [-0.0007, +0.0047],
mom [-0.0003, +0.0068] / [+0.0003, +0.0037], pigeon [+0.0001, +0.0071] / [-0.0008, +0.0052]. The
script exits non-zero on any mismatch and writes only when every pin holds; the output records the
numpy version (the pigeonhole bootstrap draws from numpy's Generator, whose streams are not promised
stable across numpy releases; the pins were set under numpy 2.3.5). A few seconds on CPU.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]  # docs/audits/<folder>/ -> the repository root
sys.path.insert(0, str(REPO / "src"))
from sideband.stats import paired_cluster_delta_ci  # noqa: E402  (the repo bootstrap, to prove reproduction)

R = REPO / "results" / "real"
SEEDS = (0, 1, 2)
PINS = {  # (tag, space substring, offset, capacity) -> {approx: (lo, hi)} at four places
    ("F25 coarse_s1_r D", "L2", 2, "linear"): {"hypot": (-0.0012, 0.0055), "mom": (-0.0007, 0.0050), "pigeon": (-0.0002, 0.0064)},
    ("TWIN s1 mn_r", "L1", 2, "mlp256"): {"hypot": (-0.0006, 0.0071), "mom": (-0.0003, 0.0068), "pigeon": (0.0001, 0.0071)},
    ("TWIN s1_r mn_r", "L1", 2, "mlp256"): {"hypot": (-0.0007, 0.0047), "mom": (0.0003, 0.0037), "pigeon": (-0.0008, 0.0052)},
}


def load_state(p):
    lines = (R / p).read_text(encoding="utf-8").split("\n")
    out = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        c = json.loads(line)
        out[c["cell"]] = c
    return out


def table(cells, space, off, cap, top, base):
    rows = {}
    for s in SEEDS:
        t = next(c for c in cells.values() if not c["shuffled"] and c["space"] == space and c["offset"] == off
                 and c["capacity"] == cap and c["features"] == top and c["seed"] == s)
        b = next(c for c in cells.values() if not c["shuffled"] and c["space"] == space and c["offset"] == off
                 and c["capacity"] == cap and c["features"] == base and c["seed"] == s)
        rows[s] = (t["_clusters"], b["_clusters"])
    prompts = sorted(set.intersection(*(set(t) for t, _ in rows.values())), key=int)
    X = np.zeros((3, len(prompts))); N = np.zeros(len(prompts)); TS = np.zeros(len(prompts)); BS = np.zeros(len(prompts))
    for i, s in enumerate(SEEDS):
        t, b = rows[s]
        ts = np.array([t[p][0] for p in prompts], float); bs = np.array([b[p][0] for p in prompts], float)
        tn = np.array([t[p][1] for p in prompts], float); bn = np.array([b[p][1] for p in prompts], float)
        assert np.array_equal(tn, bn)
        if i == 0: N = tn
        else: assert np.array_equal(N, tn)
        X[i] = ts - bs; TS += ts; BS += bs
    return X, N, TS, BS


def analyse(X, N, TS, BS, rng):
    S, P = X.shape
    delta, lo, hi = paired_cluster_delta_ci(TS, BS, N * S)
    m_s = X.sum(1) / N.sum()
    se_boot = (hi - lo) / (2 * 1.96)
    sd_seed = m_s.std(ddof=1)
    se_seed = sd_seed / math.sqrt(S)
    # (1) finder's approximation: hypot of bootstrap SE and seed SE (double-counts the interaction)
    tot1 = math.hypot(se_boot, se_seed)
    f1 = (delta - 1.96 * tot1, delta + 1.96 * tot1)
    # (2) two-way method of moments: remove the prompt x seed interaction already in the bootstrap
    rmean = X.mean(0, keepdims=True); cmean = X.mean(1, keepdims=True); g = X.mean()
    resid = X - rmean - cmean + g
    sum_sig2 = (resid ** 2).sum() * P / ((S - 1) * (P - 1))   # approx sum_p var(gamma_ps) in count^2
    tau2 = sum_sig2 / N.sum() ** 2                              # interaction variance inside one m_s
    sig2_beta = max(0.0, sd_seed ** 2 - tau2)
    tot2 = math.sqrt(se_boot ** 2 + sig2_beta / S)
    f2 = (delta - 1.96 * tot2, delta + 1.96 * tot2)
    # (3) pigeonhole (prompt x seed) bootstrap, percentile; conservative (Owen 2007)
    B = 4000
    pi = rng.integers(0, P, size=(B, P)); si = rng.integers(0, S, size=(B, S))
    num = np.empty(B); den = np.empty(B)
    for k in range(B):
        sub = X[si[k]][:, pi[k]]
        num[k] = sub.sum(); den[k] = N[pi[k]].sum() * S
    f3 = tuple(np.percentile(num / den, [2.5, 97.5]))
    # (4) seed-only t interval on per-seed margins (2 df)
    f4 = (m_s.mean() - 4.303 * se_seed, m_s.mean() + 4.303 * se_seed)
    return dict(delta=delta, ci=(lo, hi), per_seed=m_s.tolist(), se_boot=se_boot, se_seed=se_seed,
                ratio=se_seed / se_boot, tau=math.sqrt(tau2), sig_beta=math.sqrt(sig2_beta),
                hypot=f1, mom=f2, pigeon=f3, t2=f4)


def fmt(a): return f"[{a[0]:+.4f}, {a[1]:+.4f}]"


def main() -> int:
    rng = np.random.default_rng(20261015)
    out = []

    def report(tag, row, cells, top, base):
        X, N, TS, BS = table(cells, row["space"], row["offset"], row["capacity"], top, base)
        r = analyse(X, N, TS, BS, rng)
        rep = abs(r["delta"] - row["margin"]) < 1e-12 and abs(r["ci"][0] - row["ci95"][0]) < 1e-12 and abs(r["ci"][1] - row["ci95"][1]) < 1e-12
        ps = row["per_seed_margin"]
        rep_ps = all(abs(r["per_seed"][i] - ps[str(s)]) < 1e-12 for i, s in enumerate(SEEDS))
        line = (f"{tag:44s} {row['space'][:14]:14s} off{row['offset']} {row['capacity']:6s} {top}-{base:8s} "
                f"m {r['delta']:+.4f} ci {fmt(r['ci'])} seeds {' '.join(f'{v:+.4f}' for v in r['per_seed'])} "
                f"| seSeed/seBoot {r['ratio']:.2f} | hypot {fmt(r['hypot'])} | MoM {fmt(r['mom'])} sigB {r['sig_beta']:.4f} tau {r['tau']:.4f} "
                f"| pigeon {fmt(r['pigeon'])} | t2 {fmt(r['t2'])} | repro {rep and rep_ps}")
        print(line)
        out.append(dict(tag=tag, space=row["space"], offset=row["offset"], capacity=row["capacity"], pair=f"{top}-{base}", **{k: v for k, v in r.items()}, reproduced=bool(rep and rep_ps)))

    # F-24 registered payloads
    for h in ("s1", "s1_r", "s3", "s3_r"):
        p = json.loads((R / f"fullfree_{h}.json").read_text(encoding="utf-8"))
        cells = load_state(f"fullfree_{h}.json.state.jsonl")
        for row in p["d_fplus_b_vs_fplus_n"]:
            report(f"F24 fullfree_{h} D", row, cells, "fplus_b", "fplus_n")
        for key, top, base in (("mt_fplus_b_vs_fplus", "fplus_b", "fplus"), ("mn_fplus_n_vs_fplus_dilution", "fplus_n", "fplus")):
            for row in p[key]:
                if row["offset"] == 2 and row["capacity"] == "mlp256":
                    report(f"F24 fullfree_{h} {key[:2]}", row, cells, top, base)
        # twin
        tp = json.loads((R / f"fullfree_{h}_twin.json").read_text(encoding="utf-8"))
        tcells = dict(cells); tcells.update(load_state(f"fullfree_{h}_twin.json.state.jsonl"))
        for key, top, base in (("d_r_fplus_b_vs_fplus_r", "fplus_b", "fplus_r"), ("mn_r_fplus_r_vs_fplus", "fplus_r", "fplus"),
                               ("t_fplus_n_vs_fplus_r", "fplus_n", "fplus_r")):
            for row in tp[key]:
                report(f"TWIN {h} {key.split('_')[0]}{'_r' if '_r_' in key[:5] else ''}", row, tcells, top, base)

    # F-25 coarse payloads
    for h in ("s1", "s1_r", "s3", "s3_r"):
        p = json.loads((R / f"fullfree_coarse_{h}.json").read_text(encoding="utf-8"))
        cells = load_state(f"fullfree_coarse_{h}.json.state.jsonl")
        for sp, v in p["per_space"].items():
            for row in v["d_fplus_b_vs_fplus_r"]:
                report(f"F25 coarse_{h} D", row, cells, "fplus_b", "fplus_r")
            for key, top, base in (("mn_r_fplus_r_vs_fplus", "fplus_r", "fplus"), ("mt_fplus_b_vs_fplus", "fplus_b", "fplus")):
                for row in v[key]:
                    if row["offset"] == 2 and row["capacity"] == "mlp256":
                        report(f"F25 coarse_{h} {key[:4]}", row, cells, top, base)

    failed = []
    if len(out) != 72 or not all(r["reproduced"] for r in out):
        failed.append(("rows / reproduced", len(out), sum(r["reproduced"] for r in out)))
    for (tag, sub, off, cap), want in PINS.items():
        rows = [r for r in out if r["tag"] == tag and sub in r["space"] and r["offset"] == off and r["capacity"] == cap]
        if len(rows) != 1:
            failed.append(("pin row missing", tag)); continue
        for k, (lo, hi) in want.items():
            got = (round(rows[0][k][0], 4), round(rows[0][k][1], 4))
            if got != (lo, hi):
                failed.append((tag, k, got, (lo, hi)))
    if failed:
        print("PIN MISMATCH:", failed, "| numpy", np.__version__)
        return 1
    (Path(__file__).with_name("seed_var_out.json")).write_bytes(
        (json.dumps({"numpy": np.__version__, "rows": out}, indent=1) + "\n").encode("utf-8"))
    print(f"all pins hold over {len(out)} rows; wrote seed_var_out.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

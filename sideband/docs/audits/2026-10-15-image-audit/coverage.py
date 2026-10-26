"""Independent coverage check of sideband.stats.paired_cluster_delta_ci (image audit 2026-10-15,
section B item 4; the S6a refuter's script, rs6a/coverage.py, made tree-relative).

DGP (the refuter's, F-24-shaped): K prompt clusters; anchors per prompt n_i ~ U{40..400};
baseline accuracy p_i ~ Beta(6,4) (mean 0.6); heterogeneous per-prompt true effect
d_i ~ N(0.003, 0.02); per anchor, b ~ Bern(p_i), a = b with discordant flips set so
P(a)=clip(p_i+d_i) and the discordance floor is 0.04 (paired probes agree on most anchors).
Target = population ratio E[n (pa - pb)] / E[n], computed from 4e6 cluster draws of the
expectations (no Bernoulli noise). Coverage = fraction of replicates whose 95% CI holds the target.

Pinned 2026-10-16 before the lane-B rerun, all three rows deterministic (generator seed
20261015 + K, bootstrap seed = replicate index, n_boot 2000): K=30, R=4000 is the audit's own run
and must give 3756 hits (coverage 0.939); K=10, R=2000 must give 1794 hits (0.897) and K=60,
R=2000 1896 hits (0.948), the figures the audit quoted. The script exits non-zero on any
mismatch and writes coverage_out.json next to itself only when every pin holds; the output
records the numpy version (Generator streams are not promised stable across numpy releases;
the pins were set under numpy 2.3.5).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))  # docs/audits/<folder>/ -> repo/src
import numpy as np  # noqa: E402

from sideband.stats import paired_cluster_delta_ci  # noqa: E402

PINS = {30: (4000, 3756), 10: (2000, 1794), 60: (2000, 1896)}


def draw_clusters(g, K):
    n = g.integers(40, 401, size=K)
    p = g.beta(6, 4, size=K)
    d = g.normal(0.003, 0.02, size=K)
    pa = np.clip(p + d, 0.0, 1.0)
    return n, p, pa


def simulate(g, K):
    n, p, pa = draw_clusters(g, K)
    sa = np.empty(K); sb = np.empty(K)
    for i in range(K):
        b = g.random(n[i]) < p[i]
        # flips: move from b to a with base discordance 0.04 each way, then shift to hit pa
        # P(a=1|b=1)=1-f10, P(a=1|b=0)=f01 ; pa = p(1-f10) + (1-p) f01
        f10 = 0.04
        need = pa[i] - p[i] * (1 - f10)
        f01 = need / (1 - p[i]) if p[i] < 1 else 0.0
        if f01 < 0:  # cannot reach pa with f10=0.04: raise f10 instead, f01=0
            f01 = 0.0; f10 = 1 - pa[i] / p[i]
        f01 = min(max(f01, 0.0), 1.0)
        u = g.random(n[i])
        a = np.where(b, u >= f10, u < f01)
        sa[i] = a.sum(); sb[i] = b.sum()
    return sa, sb, n.astype(float)


def truth(seed=12345, M=4_000_000):
    g = np.random.default_rng(seed)
    n, p, pa = draw_clusters(g, M)
    return float((n * (pa - p)).sum() / n.sum())


def main() -> int:
    T = truth()
    rows = []
    failed = []
    for K, (R, want_hits) in PINS.items():
        g = np.random.default_rng(20261015 + K)
        hit = 0; lo_miss = 0; hi_miss = 0; widths = []
        t0 = time.time()
        for r in range(R):
            sa, sb, n = simulate(g, K)
            d, lo, hi = paired_cluster_delta_ci(sa, sb, n, n_boot=2000, seed=r)
            if lo <= T <= hi: hit += 1
            elif T < lo: lo_miss += 1
            else: hi_miss += 1
            widths.append(hi - lo)
        c = hit / R
        row = dict(K=K, R=R, truth=T, hits=hit, coverage=c, mc_se=float(np.sqrt(c * (1 - c) / R)),
                   miss_below=lo_miss, miss_above=hi_miss, mean_width=float(np.mean(widths)))
        print(json.dumps(row), f"({time.time() - t0:.0f} s)")
        rows.append(row)
        if hit != want_hits:
            failed.append((K, hit, want_hits))
    if failed:
        print("PIN MISMATCH (K, hits, pinned):", failed, "| numpy", np.__version__)
        return 1
    out = {"numpy": np.__version__, "rows": rows}
    Path(__file__).with_name("coverage_out.json").write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print("all pins hold; wrote coverage_out.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

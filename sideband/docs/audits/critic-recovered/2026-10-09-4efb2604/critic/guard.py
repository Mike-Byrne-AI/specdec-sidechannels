import sys
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
from math import erf, sqrt
import run_seed_replay as sr
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
for key in ("k3", "oq15"):
    pop = sr.load_pop(key); vv, vt = pop["runs"]["verdict_vanilla"], pop["runs"]["verdict_tel"]
    gap = vv["drafted"].sum()/vv["emitted"].sum() - vt["drafted"].sum()/vt["emitted"].sum()
    g = np.random.default_rng(0); idx = g.integers(0, 210, size=(4000, 210))
    gb = vv["drafted"][idx].sum(1)/vv["emitted"][idx].sum(1) - vt["drafted"][idx].sum(1)/vt["emitted"][idx].sum(1)
    se = gb.std()
    # breach at seed 6 needs gap6 < -0.01; cross-seed difference sd ~ sqrt(2)*se (no stable share) .. se*sqrt(2*(1-rho))
    for rho in (0.0, 0.42):
        sd = se*sqrt(2*(1-rho)); p = Phi((-0.01 - gap)/sd)
        print(f"{key}: gap {gap:.6f} boot SE {se:.6f}; P(breach at seed 6 | stable share {rho}) ~ {p:.4f}")
    # bar-cleared probability at seed 6 under same model
    d = (vt["emitted"].sum()/vt["blocks"].sum()) - (vv["emitted"].sum()/vv["blocks"].sum())
    ib = (vt["emitted"][idx].sum(1)/vt["blocks"][idx].sum(1)) - (vv["emitted"][idx].sum(1)/vv["blocks"][idx].sum(1))
    sel = ib.std()
    for rho in (0.0, 0.42):
        sd = sel*sqrt(2*(1-rho)); print(f"   P(point >= 0.062 at seed 6 | rho {rho}) ~ {1-Phi((0.062-d)/sd):.4f}; P(|Delta|<0.02) ~ {2*Phi(0.02/sd)-1:.3f}; P(|Delta|<0.04) ~ {2*Phi(0.04/sd)-1:.3f}")

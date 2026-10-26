import sys, json
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import numpy as np
import run_seed_replay as sr, e6_gate as e6, run_noise_floor as nf
from sideband.stats import paired_ratio_delta_ci, paired_ratio_delta_of_deltas_ci
for key in ("k3", "oq15"):
    pop = sr.load_pop(key)  # new-seed runs absent -> runs has verdict + vanilla seeds only
    vv, vt = pop["runs"]["verdict_vanilla"], pop["runs"]["verdict_tel"]
    leg = e6.pair(sr.as_e6(vt), sr.as_e6(vv))
    dd = paired_ratio_delta_of_deltas_ci(vt["emitted"], vt["blocks"], vv["emitted"], vv["blocks"], vv["emitted"], vv["blocks"], vv["emitted"], vv["blocks"])
    print(key, "reduction bit-exact on committed data:", dd == (leg["delta"], leg["ci_lower"], leg["ci_upper"]), dd)
    # self-difference: identical legs -> zero
    z = paired_ratio_delta_of_deltas_ci(vt["emitted"], vt["blocks"], vv["emitted"], vv["blocks"], vt["emitted"], vt["blocks"], vv["emitted"], vv["blocks"])
    print("   self difference", z)
    # R4 recipe vs F-27 committed full-set row: use the committed pair (lower, higher)
    seeds = sorted(pop["spec"]["vanilla_seeds"]); a = pop["runs"][f"vanilla_seed{seeds[0]}"]; b = pop["runs"][f"vanilla_seed{seeds[1]}"]
    rel = nf.reliability(nf.per_prompt_y(a), nf.per_prompt_y(b), pop["families"], draws=sr.RELIABILITY_DRAWS, seed=sr.RELIABILITY_SEED)
    d, lo, hi = paired_ratio_delta_ci(a["emitted"], a["blocks"], b["emitted"], b["blocks"], n_boot=sr.N_BOOT, seed=sr.BOOT_SEED)
    c = pop["noise_floor"]["readouts"]
    print("   R4 recipe reproduces F-27 r/CI:", (rel["r"], rel["ci_lower"], rel["ci_upper"]) == (c["reliability"]["r"], c["reliability"]["ci_lower"], c["reliability"]["ci_upper"]),
          " half-width:", (hi - lo) / 2.0 == c["per_n"]["210"]["single"]["hw"], " delta:", d == c["per_n"]["210"]["single"]["delta"])
    # leg SE and the MC null operating characteristic
    hw = (leg["ci_upper"] - leg["ci_lower"]) / 2
    from math import erf, sqrt
    Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
    for rho in (0.0, 0.2, 0.42):
        z_ = 1.96 / sqrt(2 * (1 - rho)); print(f"   P(MC | exchangeable seeds, stable share {rho}) ~ {2*Phi(z_)-1:.3f}")
    # per-prompt delta structure
    y = lambda r: r["emitted"] / r["blocks"]
    dp = y(vt) - y(vv)
    print(f"   per-prompt leg deltas: exactly-zero prompts {int((dp==0).sum())}, sd {dp.std():.4f}, leg hw {hw:.6f}")

"""F-4 across training seeds (image audit 2026-10-15, section B item 5; the S8 refuter's checks
misc_checks.py and f4_rhos.py merged into one tree-relative script).

Mirrors experiments/e04_staleness_decay.py exactly (WorldConfig(rho=rho), n_positions 14000, gamma 6,
policies "none" and "oracle_concept_stale" with beta 2.5 and the disagreement gate, analytic acceptance by
offset) and repeats it at seeds 200 to 209 for rho 0.6, 0.75 and 0.9. The seed-200 run must reproduce the
committed results/e04_staleness_decay.json stale-minus-vanilla deltas to 1e-12 at every offset.

Pinned 2026-10-16 before the lane-B rerun (the audit's figures), asserted by the script: rho 0.6 offset 1
stale minus vanilla by seed = -0.0039, +0.0001, -0.0015, -0.0012, -0.0003, -0.0022, +0.0047, +0.0010,
+0.0029, +0.0057 (mean +0.0005, SE 0.0010, negative on 5 of 10, the committed seed-200 value the most
negative of the ten); rho 0.6 offsets 2 to 6 negative on 10 of 10 with means -0.0121, -0.0194, -0.0228,
-0.0259, -0.0267; offset 1 at rho 0.75 and 0.9 positive on 10 of 10 with means +0.0097 and +0.0174. The
script exits non-zero on any mismatch and writes f4_seeds_out.json next to itself only when every pin
holds; the output records the numpy version. About two minutes on CPU.
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]  # docs/audits/<folder>/ -> the repository root
sys.path.insert(0, str(REPO / "src"))
from sideband.pipeline import run_simulation  # noqa: E402
from sideband.synthetic import World, WorldConfig  # noqa: E402

SEEDS = list(range(200, 210))
RHOS = (0.6, 0.75, 0.9)
N_POS, GAMMA, BETA = 14000, 6, 2.5
PIN_OFF1_RHO06 = [-0.0039, 0.0001, -0.0015, -0.0012, -0.0003, -0.0022, 0.0047, 0.0010, 0.0029, 0.0057]
PIN_MEANS_RHO06 = {1: 0.0005, 2: -0.0121, 3: -0.0194, 4: -0.0228, 5: -0.0259, 6: -0.0267}
PIN_OFF1_MEANS = {0.75: 0.0097, 0.9: 0.0174}


def by_offset(res):
    return {j: float(sum(v) / len(v)) for j, v in sorted(res.analytic_by_offset.items())}


def main() -> int:
    committed = json.loads((REPO / "results" / "e04_staleness_decay.json").read_text(encoding="utf-8"))
    crow = {r["rho"]: r for r in committed["rows"]}
    out = {"numpy": np.__version__, "seeds": SEEDS, "n_positions": N_POS, "gamma": GAMMA, "beta": BETA, "rows": []}
    failed = []
    for rho in RHOS:
        world = World(WorldConfig(rho=rho))
        deltas = {j: [] for j in range(1, GAMMA + 1)}
        reproduced = None
        for s in SEEDS:
            kw = dict(seed=s, n_positions=N_POS, gamma=GAMMA)
            base = by_offset(run_simulation(world, policy="none", **kw))
            stale = by_offset(run_simulation(world, policy="oracle_concept_stale", beta=BETA,
                                             steer_gate="disagree", **kw))
            for j in deltas:
                deltas[j].append(stale[j] - base[j])
            if s == 200:
                c = crow[rho]
                reproduced = all(abs(stale[j] - c["stale_by_offset"][str(j)]) < 1e-12
                                 and abs(base[j] - c["vanilla_by_offset"][str(j)]) < 1e-12 for j in deltas)
                if not reproduced:
                    failed.append(("e04 seed-200 reproduction", rho))
        for j, v in deltas.items():
            a = np.array(v)
            row = dict(rho=rho, offset=j, values=[float(x) for x in a], seed200=float(a[0]),
                       mean=float(a.mean()), sd=float(a.std(ddof=1)), se=float(a.std(ddof=1) / np.sqrt(len(a))),
                       n_neg=int((a < 0).sum()), n_pos=int((a > 0).sum()), reproduced_seed200=bool(reproduced))
            print(f"rho {rho} off{j} seed200 {row['seed200']:+.4f} mean {row['mean']:+.4f} se {row['se']:.4f} "
                  f"neg {row['n_neg']}/10 reproduced {reproduced}")
            out["rows"].append(row)
            if rho == 0.6:
                if round(row["mean"], 4) != PIN_MEANS_RHO06[j]:
                    failed.append(("rho 0.6 mean", j, round(row["mean"], 4)))
                if j == 1:
                    if [round(x, 4) for x in a] != PIN_OFF1_RHO06 or row["n_neg"] != 5 or min(a) != a[0]:
                        failed.append(("rho 0.6 offset-1 values", [round(x, 4) for x in a]))
                    if round(row["se"], 4) != 0.0010:
                        failed.append(("rho 0.6 offset-1 se", round(row["se"], 4)))
                elif row["n_neg"] != 10:
                    failed.append(("rho 0.6 n_neg", j, row["n_neg"]))
            elif j == 1 and (row["n_pos"] != 10 or round(row["mean"], 4) != PIN_OFF1_MEANS[rho]):
                failed.append(("offset-1 at rho", rho, row["n_pos"], round(row["mean"], 4)))
    if failed:
        print("PIN MISMATCH:", failed, "| numpy", np.__version__)
        return 1
    (Path(__file__).with_name("f4_seeds_out.json")).write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print("all pins hold; wrote f4_seeds_out.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""P01 — Anytime posterior on partial evidence (the streaming architecture's
EVIDENCE axis; feeds OQ-11 / future e08).

Models a device that reveals only the first ceil(f * top_n) strongest
accesses (fetch-priority order — a modeling choice, regime note), with the
SAME classifier reading whatever partial slot set exists and the centered
posterior mechanism (D-10) consuming the resulting sharpness unmodified.

Single seed, hardened K=256 world. First run (2026-08-28): signal strongly
front-loaded — f=0.25 gives decode acc ~0.98 and steering recovery +0.83
(full-trained) / +0.94 (anytime-trained); f=0.5 matches full evidence.
Promotion to e08 requires: seeds, an intra-block scheduler for the TIMING
axis (fresher positions mid-block), non-priority reveal orders, and smoke
mode. Do not cite these numbers in FINDINGS.
"""
import numpy as np

from sideband.dists import rng
from sideband.pipeline import run_simulation, train_sidecar
from sideband.synthetic import TelemetryDataset, World, WorldConfig

HARD = dict(support_gain=0.5, support_noise=0.5, background_noise=0.25, top_n=16)


class PartialWorld(World):
    def __init__(self, cfg, frac_mode):
        super().__init__(cfg)
        self.frac_mode = frac_mode  # float (fixed) or "mixed"

    def telemetry(self, gen, concept):
        a = self.activation(gen, int(concept))
        f = float(gen.choice([0.25, 0.5, 0.75, 1.0])) if self.frac_mode == "mixed" else self.frac_mode
        n = max(1, int(np.ceil(f * self.cfg.top_n)))
        units = self.sketch.top_units(a, n)
        return np.unique(self.sketch.slot_of_unit[units])


def main():
    cfg = WorldConfig(n_slots=256, **HARD)
    m_full, acc_full = train_sidecar(PartialWorld(cfg, 1.0), seed=300, n_train=10000, epochs=12)
    m_any, acc_any = train_sidecar(PartialWorld(cfg, "mixed"), seed=300, n_train=10000, epochs=12)
    print(f"train: full acc={acc_full:.3f}  anytime acc={acc_any:.3f}")
    base = run_simulation(PartialWorld(cfg, 1.0), seed=401, n_positions=6000, gamma=4,
                          policy="none").analytic_acceptance
    oracle = run_simulation(PartialWorld(cfg, 1.0), seed=401, n_positions=6000, gamma=4,
                            policy="oracle_concept_stale", beta=2.5, steer_gate="disagree",
                            steer_mech="posterior").analytic_acceptance
    print(f"vanilla={base:.4f} posterior-oracle={oracle:.4f}")
    for f in (0.25, 0.5, 0.75, 1.0):
        wf = PartialWorld(cfg, f)
        for name, m in (("full", m_full), ("anytime", m_any)):
            d = TelemetryDataset.harvest(wf, rng(777), 3000)
            P = m.probs(d.X)
            r = run_simulation(wf, seed=401, n_positions=6000, gamma=4, policy="sidecar",
                               beta=2.5, steer_gate="disagree", steer_mech="posterior",
                               sidecar=m).analytic_acceptance
            print(f"f={f} {name:7s} dec={float((P.argmax(1)==d.y).mean()):.3f} "
                  f"conf={float(P.max(1).mean()):.2f} recovery={(r-base)/(oracle-base):+.3f}")


if __name__ == "__main__":
    main()

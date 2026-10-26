"""A01 — Archive rate vs draft quality (the thesis in one curve).

Compresses target-greedy sequences at several draft qualities and compares:
  amber          actual payload bits/token (headers excluded, O(1))
  ideal_regimeA  H2(d) + d * E[-log2 q~(x) | divergence]   (this format's
                 information bound: divergence indicator + correction coded
                 under q renormalized over non-argmax tokens)
  ac_under_q     E[-log2 q(x)]  — the rate an arithmetic coder achieves with
                 ONLY the draft and no structure assumption (regime-B
                 reference). Regime A beating this is the point: determinism
                 adds structure that pure draft-side coding cannot see.
  zlib_raw       zlib -9 on the raw uint16 token stream (naive baseline)
  raw            log2(V)
"""

from __future__ import annotations

import json
import time
import zlib
from pathlib import Path

import numpy as np

from sideband.synthetic import World, WorldConfig

from amber.codec import encode, stable_order

RESULTS = Path(__file__).resolve().parent.parent / "results"


def ledger(cfg: WorldConfig, path_seed: int, draft_seed: int, T: int) -> dict:
    arc, tokens = encode(cfg, path_seed, draft_seed, T)
    world = World(cfg)
    path = world.sample_concept_path(np.random.default_rng(path_seed), T)
    gen_draft = np.random.default_rng(draft_seed)
    n_div = 0
    corr_bits_ideal = 0.0
    ac_bits = 0.0
    for t in range(T):
        c = int(path[t])
        x = int(np.argmax(world.P[c]))
        q = world.draft_dist(world.draft_concept(gen_draft, c))
        ac_bits += -np.log2(max(q[x], 1e-300))
        order = stable_order(q)
        if int(order[0]) != x:
            n_div += 1
            denom = 1.0 - q[order[0]]
            corr_bits_ideal += -np.log2(max(q[x] / max(denom, 1e-300), 1e-300))
    d = n_div / T
    h2 = 0.0 if d in (0.0, 1.0) else -(d * np.log2(d) + (1 - d) * np.log2(1 - d))
    return {
        "divergence_rate": d,
        "amber_bits_per_token": arc.header["payload_bits"] / T,
        "ideal_regimeA_bits_per_token": h2 + corr_bits_ideal / T,
        "ac_under_q_bits_per_token": ac_bits / T,
        "zlib_raw_bits_per_token": len(zlib.compress(tokens.astype("<u2").tobytes(), 9)) * 8 / T,
        "raw_bits_per_token": float(np.log2(cfg.vocab_size)),
        "compression_vs_raw": float(np.log2(cfg.vocab_size)) / (arc.header["payload_bits"] / T),
    }


def main() -> None:
    T = 20000
    rows = []
    for alpha in (0.5, 0.7, 0.9, 0.97):
        per_seed = [ledger(WorldConfig(draft_alpha=alpha, seed=s), 100 + s, 200 + s, T)
                    for s in (0, 1)]
        row = {"draft_alpha": alpha}
        for k in per_seed[0]:
            row[k] = float(np.mean([p[k] for p in per_seed]))
        rows.append(row)
        print({k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()})
    payload = {
        "_experiment": "a01_rate_vs_draft_quality", "_written_unix": int(time.time()),
        "T": T, "seeds": [0, 1], "rows": rows,
        "regime": "sideband synthetic concept-HMM v0 world, target-greedy content, "
                  "amber v0 codec (Elias-gamma gaps+ranks); headers excluded from rates",
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "a01_rate_vs_draft_quality.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print("[saved] results/a01_rate_vs_draft_quality.json")


if __name__ == "__main__":
    main()

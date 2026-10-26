#!/usr/bin/env python3
"""Critic, third batch, E17 audit (not a protocol quantity): do the 4-tau labels reach the escape-cost figures?

F-5 (FINDINGS.md:40) prices the escape as P(gap < threshold) "at 0.142 (fp16's 2tau) ... 0.93 (bf16's 2tau)" and F-7
(FINDINGS.md:54) says "the escape-symbol cost for a bf16 decoder is ~39% of positions on this model, for fp16 ~8%" from
P(gap < 0.142 / 0.465 / 0.93) = 8.3% / 23.2% / 39.1%. This reproduces F-7's near-tie masses from the cpu_fp32 dump
(manifest-checked) and evaluates them at the census's actual 2 tau (fp16 0.0662, bf16 0.4654). torch blocked.
"""
import sys

sys.modules["torch"] = None
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]; RES = REPO / "results"; OUT = RES / "p2_llama32"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    man = {}
    for ln in (RES / "p2_dumps.sha256").read_text().splitlines():
        if ln.strip():
            d_, _, rel = ln.partition("  "); man[rel] = d_
    used = [r for r in man if r.startswith("results/p2_llama32/cpu_fp32/")]
    assert all(sha(REPO / r) == man[r] for r in used)
    meta = json.loads((OUT / "cpu_fp32/meta.json").read_text()); vv = []
    for s in range((meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]):
        with np.load(OUT / "cpu_fp32" / f"shard_{s:04d}.npz") as z:
            vv.append(z["val"][..., :2].astype(np.float64))
    v = np.concatenate(vv).reshape(-1, 2); g = v[:, 0] - v[:, 1]           # top-k dumps are sorted by value; top-1 minus top-2
    tl = json.loads((RES / "p2_llama32_rank_census.json").read_text())["calibrated_tau_per_arm"]
    th = {"0.142": 0.142, "0.465": 0.465, "0.93": 0.93, "2tau_fp16": 2 * tl["cuda_fp16_b1"], "2tau_bf16": 2 * tl["cuda_bf16_b1"],
          "4tau_fp16": 4 * tl["cuda_fp16_b1"], "4tau_bf16": 4 * tl["cuda_bf16_b1"]}
    out = {"positions": int(g.size), "share_gap_below": {k: float((g < t).mean()) for k, t in th.items()}, "thresholds": th,
           "printed_F7": {"0.142": 0.083, "0.465": 0.232, "0.93": 0.391, "bf16_cost": "~39%", "fp16_cost": "~8%"}}
    text = json.dumps(out, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Profile advisor — is a (vocab, grid, drift) combination even buildable?

This tool exists because F-5 and F-6 were latent in the repo for three
sessions: the coder was measured on a 256-symbol alphabet while the roadmap
planned a 128k-token model, and nothing connected the two. That class of
error should cost one command, not an archaeology session.

Given a vocabulary size and a decode-profile grid, it reports:

  * FEASIBLE?     -- can a CDF exist at all (total >= V, total <= 2^prob_bits)
  * floor mass    -- probability mass eaten by the mandatory >=1 unit/symbol
  * excess bits   -- ratio damage from grid quantization (KL, measured)
  * correction rate for the logit-space design (F-7's law: k*eps/delta)

Usage:
    python tools/lockstep_profile_advisor.py                    # survey table
    python tools/lockstep_profile_advisor.py --vocab 128256 --prob-bits 24
    python tools/lockstep_profile_advisor.py --vocab 128256 --top-k 64 \
        --logit-step 1e-3 --drift 1e-7
"""

from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import lockstep.cdf as cdf_mod  # noqa: E402
import lockstep.rac as rac  # noqa: E402

CODER_SAFE_PROB_BITS = 30  # WNC: range > QUARTER = 2^(CODE_BITS-2) after renorm


def peaky(V, tau=3.0):
    w = [math.exp(-i / tau) for i in range(min(V, 4096))]
    w += [1e-12] * max(0, V - 4096)
    Z = sum(w)
    return [x / Z for x in w]


def excess_bits(V, prob_bits, dist=peaky):
    """KL(p || quantized p) in bits/token. Patches TOTAL_MAX to measure
    grids the shipped lsp0 constant forbids -- that IS the point (F-5)."""
    T = 1 << prob_bits
    if V > T:
        return None
    saved = rac.TOTAL_MAX
    try:
        rac.TOTAL_MAX = cdf_mod.TOTAL_MAX = max(T, saved)
        p = dist(V)
        w = [max(1, round(x * 1e12)) for x in p]
        f = cdf_mod.quantize_weights(w, T)
        return sum(pi * math.log2(pi / (fi / T))
                   for pi, fi in zip(p, f) if pi > 0)
    finally:
        rac.TOTAL_MAX = cdf_mod.TOTAL_MAX = saved


def entropy(V, dist=peaky):
    return -sum(x * math.log2(x) for x in dist(V) if x > 0)


def report_vocab(V, prob_bits):
    T = 1 << prob_bits
    print(f"\nvocab V={V:,}   grid T=2^{prob_bits}={T:,}")
    if prob_bits > CODER_SAFE_PROB_BITS:
        print(f"  [FAIL] prob_bits {prob_bits} exceeds coder-safe {CODER_SAFE_PROB_BITS} "
              f"for CODE_BITS={rac.CODE_BITS} (range > 2^{rac.CODE_BITS-2} after renorm)")
        return
    if V > T:
        print(f"  [FAIL] INFEASIBLE: every symbol needs >=1 unit, so total >= {V:,} > {T:,}")
        print(f"         -> need prob_bits >= {math.ceil(math.log2(V))} just to build a CDF (F-5)")
        return
    floor = V / T
    eb = excess_bits(V, prob_bits)
    H = entropy(V)
    loss = eb / H * 100 if H else 0
    verdict = "OK" if loss < 1 else ("MARGINAL" if loss < 10 else "RATIO DESTROYED")
    print(f"  units/symbol : {T/V:,.1f}")
    print(f"  floor mass   : {floor*100:5.2f}%   (mass forced onto the tail by the >=1 rule)")
    print(f"  excess bits  : {eb:.3f} / H={H:.3f}  = {loss:.1f}% ratio loss   [{verdict}]")


def report_logit_design(k, delta, drift):
    rate = k * drift / delta
    print(f"\nlogit-space design (F-7):  top-k={k}  logit step={delta:.0e}  drift={drift:.0e}")
    print(f"  predicted correction rate : {rate*100:.2f}% of tokens   "
          f"[{'sparse — side-stream viable' if rate < 0.05 else 'TOO DENSE — safeguard economics break'}]")
    print(f"  law: rate ~ k * drift / step   (measured 0.67% vs 0.64% predicted at k=64, "
          f"step=1e-3, drift=1e-7)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vocab", type=int)
    p.add_argument("--prob-bits", type=int)
    p.add_argument("--top-k", type=int, default=64)
    p.add_argument("--logit-step", type=float, default=1e-3)
    p.add_argument("--drift", type=float, default=1e-7)
    a = p.parse_args()

    if a.vocab:
        report_vocab(a.vocab, a.prob_bits or 20)
        report_logit_design(a.top_k, a.logit_step, a.drift)
        return 0

    print(f"survey — shipped lsp0 has PROB_BITS_MAX={int(math.log2(rac.TOTAL_MAX))} "
          f"(coder-safe ceiling is {CODER_SAFE_PROB_BITS}; see F-5)")
    for V in (256, 32768, 128256):
        for pb in (16, 20, 24):
            report_vocab(V, pb)
    report_logit_design(a.top_k, a.logit_step, a.drift)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

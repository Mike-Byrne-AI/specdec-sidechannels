#!/usr/bin/env python3
"""Lockstep cost & break-even model — is compute-for-storage worth it here?

The project's entire thesis is that LLM-based archival beats a classical
codec *for some corpus size and access pattern* once you count the
GPU-hours spent packing. This tool computes that, so the claim is a
number instead of a hope (docs/07 Blueprint A, OQ-8, docs/08 killer #1).  # [withheld: Blueprint A, docs/07 not in this repository; see WITHHELD.md]

It is deliberately simple, dependency-free, and honest about being a
model: every input is explicit, and the answer is only as good as the
throughput and price numbers you feed it (get pack/decode throughput from
a real run via tools/lockstep_bench.py, not from optimism).

Cost model (per corpus, over a retention window):

    storage_cost = stored_GB * $/GB-month * months
    pack_cost    = (raw_GB / pack_throughput_GBps / 3600) * pack_$/hour
    read_cost    = reads * (raw_GB / decode_throughput_GBps / 3600) * decode_$/hour
                 + reads * stored_GB * egress_$/GB      # if reads leave the tier

Compared across three storage strategies: raw, a classical baseline
(e.g. zstd -19), and Lockstep lsp1. Prints per-strategy TCO and the
break-even retention/read frequency where the ranking flips.

Usage:
    python tools/lockstep_costmodel.py                 # built-in scenarios
    python tools/lockstep_costmodel.py --json          # machine-readable
    python tools/lockstep_costmodel.py --scenario compliance_cold
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict


@dataclass
class Strategy:
    name: str
    ratio: float          # raw_bytes / stored_bytes (higher = smaller)
    pack_gbps: float      # pack throughput, GB/s (0 => negligible, e.g. raw)
    decode_gbps: float    # decode throughput, GB/s (0 => negligible)
    pack_dollars_hr: float
    decode_dollars_hr: float


@dataclass
class Scenario:
    name: str
    raw_gb: float
    retention_months: float
    reads_over_window: float
    storage_dollars_gb_month: float
    egress_dollars_gb: float          # charged per read if data leaves tier
    reads_leave_tier: bool


def tco(strat: Strategy, sc: Scenario) -> dict:
    stored_gb = sc.raw_gb / strat.ratio
    storage = stored_gb * sc.storage_dollars_gb_month * sc.retention_months
    pack = 0.0
    if strat.pack_gbps > 0:
        pack = (sc.raw_gb / strat.pack_gbps / 3600.0) * strat.pack_dollars_hr
    decode = 0.0
    if strat.decode_gbps > 0:
        decode = sc.reads_over_window * (sc.raw_gb / strat.decode_gbps / 3600.0) \
                 * strat.decode_dollars_hr
    egress = 0.0
    if sc.reads_leave_tier:
        egress = sc.reads_over_window * stored_gb * sc.egress_dollars_gb
    total = storage + pack + decode + egress
    return {"strategy": strat.name, "stored_gb": round(stored_gb, 3),
            "storage": storage, "pack": pack, "decode": decode,
            "egress": egress, "total": total}


def break_even_reads(a: Strategy, b: Strategy, sc: Scenario,
                     lo: float = 0.0, hi: float = 1e9) -> float | None:
    """Reads/window at which strategy a's TCO crosses b's, or None if they
    never cross in [lo, hi]. Monotone in reads, so bisect the difference."""
    def diff(reads: float) -> float:
        s = Scenario(**{**asdict(sc), "reads_over_window": reads})
        return tco(a, s)["total"] - tco(b, s)["total"]
    dlo, dhi = diff(lo), diff(hi)
    if (dlo > 0) == (dhi > 0):
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if (diff(mid) > 0) == (dlo > 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# Baselines are illustrative defaults; override with measured numbers.
STRATEGIES = {
    "raw": Strategy("raw", ratio=1.0, pack_gbps=0, decode_gbps=0,
                    pack_dollars_hr=0, decode_dollars_hr=0),
    "zstd19": Strategy("zstd -19", ratio=3.5, pack_gbps=0.03, decode_gbps=1.0,
                       pack_dollars_hr=0.10, decode_dollars_hr=0.10),  # CPU box
    "lockstep_lsp1": Strategy("lockstep lsp1", ratio=6.0, pack_gbps=0.0005,
                              decode_gbps=0.002, pack_dollars_hr=2.50,
                              decode_dollars_hr=2.50),  # GPU-ish; PLACEHOLDER ratios/speeds
}

SCENARIOS = {
    "compliance_cold": Scenario("compliance_cold", raw_gb=1000, retention_months=84,
                                reads_over_window=2, storage_dollars_gb_month=0.004,
                                egress_dollars_gb=0.09, reads_leave_tier=True),
    "ediscovery_warm": Scenario("ediscovery_warm", raw_gb=200, retention_months=24,
                                reads_over_window=500, storage_dollars_gb_month=0.02,
                                egress_dollars_gb=0.09, reads_leave_tier=True),
    "research_steward": Scenario("research_steward", raw_gb=5000, retention_months=120,
                                 reads_over_window=50, storage_dollars_gb_month=0.004,
                                 egress_dollars_gb=0.02, reads_leave_tier=False),
}


def run(scenario_key: str, as_json: bool) -> dict:
    sc = SCENARIOS[scenario_key]
    rows = [tco(s, sc) for s in STRATEGIES.values()]
    rows.sort(key=lambda r: r["total"])
    be = break_even_reads(STRATEGIES["lockstep_lsp1"], STRATEGIES["zstd19"], sc)
    result = {"scenario": asdict(sc), "ranking": rows,
              "lsp1_vs_zstd_break_even_reads": be}
    if as_json:
        return result
    print(f"\n=== {sc.name} ===")
    print(f"  {sc.raw_gb:g} GB raw, {sc.retention_months:g} mo retention, "
          f"{sc.reads_over_window:g} reads, storage ${sc.storage_dollars_gb_month}/GB-mo")
    print(f"  {'strategy':<16}{'stored GB':>10}{'storage':>10}{'pack':>10}"
          f"{'decode':>10}{'egress':>10}{'TOTAL':>12}")
    for r in rows:
        print(f"  {r['strategy']:<16}{r['stored_gb']:>10.2f}{r['storage']:>10.2f}"
              f"{r['pack']:>10.2f}{r['decode']:>10.2f}{r['egress']:>10.2f}"
              f"{r['total']:>12.2f}")
    winner = rows[0]["strategy"]
    print(f"  winner: {winner}")
    if be is None:
        print("  lsp1 vs zstd: no read-frequency crossover in range "
              "(one dominates regardless of reads)")
    else:
        print(f"  lsp1 vs zstd break-even: ~{be:.0f} reads over the window "
              f"(more reads favor the cheaper-to-decode strategy)")
    print("  NOTE: lsp1 ratio/throughput are PLACEHOLDERS — feed measured "
          "numbers from tools/lockstep_bench.py before trusting any verdict.")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", choices=sorted(SCENARIOS), default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    keys = [args.scenario] if args.scenario else sorted(SCENARIOS)
    out = {k: run(k, args.json) for k in keys}
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

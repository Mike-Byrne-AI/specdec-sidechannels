"""A02 — Attestation and the recalibration blind spot.

L0 (draft-only): header fingerprint — catches declared model/config mismatch.
L1 (target present): recomputed divergence set must equal recorded
corrections; forged tokens must fail.

Also measured: which silent model substitutions (fingerprint deliberately
refreshed, so L0 is bypassed) change decode output — i.e. what L0 alone
cannot see. Rank coding is provably invariant to monotone recalibration of
the draft (temperature), so that axis decodes IDENTICALLY: robustness and an
attestation blind spot at once. Order-changing drift (alpha, zipf shape) is
loud.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from sideband.synthetic import WorldConfig

from amber.codec import Archive, attest_with_target, decode, encode, reseal

RESULTS = Path(__file__).resolve().parent.parent / "results"


def substitute(arc: Archive, **cfg_overrides) -> Archive:
    h = dict(arc.header)
    cfg = dict(h["cfg"]); cfg.update(cfg_overrides)
    h["cfg"] = cfg
    return Archive(header=reseal(h), payload=arc.payload)


def main() -> None:
    T = 8000
    base_cfg = WorldConfig(draft_alpha=0.7, draft_temperature=1.6, seed=0)
    arc, tokens = encode(base_cfg, 100, 200, T)

    honest = attest_with_target(arc, tokens)
    forged = tokens.copy(); forged[T // 2] = (forged[T // 2] + 1) % base_cfg.vocab_size
    forged_rep = attest_with_target(arc, forged)

    subs = {
        "temperature_1.6->2.4 (monotone recalibration)": dict(draft_temperature=2.4),
        "draft_alpha_0.7->0.6": dict(draft_alpha=0.6),
        "zipf_s_1.1->1.2": dict(zipf_s=1.2),
    }
    sub_rows = []
    for name, ov in subs.items():
        out = decode(substitute(arc, **ov))
        sub_rows.append({"substitution": name,
                         "token_change_rate_vs_true": float((out != tokens).mean())})
        print(sub_rows[-1])

    payload = {
        "_experiment": "a02_attestation", "_written_unix": int(time.time()),
        "T": T,
        "honest_attestation": honest,
        "forged_token_attestation": forged_rep,
        "silent_substitutions_L0_bypassed": sub_rows,
        "regime": "amber v0 rank codec on sideband synthetic world; L0=fingerprint, "
                  "L1=target divergence-set equality",
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "a02_attestation.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    print("honest:", honest)
    print("forged:", forged_rep)
    print("[saved] results/a02_attestation.json")


if __name__ == "__main__":
    main()

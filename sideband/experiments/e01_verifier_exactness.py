"""E01 — Verifier exactness demo.

Beyond the unit tests: measure the worst-case deviation between the
closed-form induced distribution and the target over many random (p, q)
pairs, with and without steering, plus one large empirical run. This is the
'the floor is solid' artifact the rest of the project stands on.
"""

from __future__ import annotations

import argparse

import numpy as np

from _util import save_json, smoke_results
from sideband.dists import normalize, rng
from sideband.specdec import residual_distribution, spec_step
from sideband.steering import bucket_bias


def induced(p, q):
    accept = np.minimum(p, q)
    return accept + (1.0 - accept.sum()) * residual_distribution(p, q)


def main(smoke: bool = False) -> dict:
    if smoke:
        smoke_results()   # results/smoke/, never the committed payload (2026-10-16, lane C)
    gen = rng(0)
    n_pairs = 200 if smoke else 2000
    worst_plain = worst_steered = 0.0
    for _ in range(n_pairs):
        v = int(gen.integers(2, 64))
        p = normalize(gen.random(v))
        q = normalize(np.where(gen.random(v) < 0.3, 0.0, gen.random(v)) + 1e-15)
        worst_plain = max(worst_plain, float(np.abs(induced(p, q) - p).max()))
        bucket = gen.choice(v, size=max(1, v // 3), replace=False)
        q_s = bucket_bias(q, bucket, float(gen.uniform(-6, 9)))
        worst_steered = max(worst_steered, float(np.abs(induced(p, q_s) - p).max()))

    n_samples = 20_000 if smoke else 500_000
    p = normalize(np.array([0.45, 0.30, 0.15, 0.07, 0.03]))
    q = normalize(np.array([0.05, 0.10, 0.35, 0.30, 0.20]))
    counts = np.zeros(5)
    for _ in range(n_samples):
        counts[spec_step(gen, p, q).emitted] += 1
    emp_dev = float(np.abs(counts / n_samples - p).max())

    payload = {
        "n_random_pairs": n_pairs,
        "worst_abs_dev_closed_form_plain": worst_plain,
        "worst_abs_dev_closed_form_steered": worst_steered,
        "empirical_samples": n_samples,
        "empirical_max_abs_dev": emp_dev,
        "regime": "mathematical property of the rejection scheme; distribution-agnostic",
    }
    save_json("e01_verifier_exactness.json", payload)
    print(payload)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(**vars(ap.parse_args()))

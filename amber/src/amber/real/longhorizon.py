"""Pure helpers for P7 (long-horizon + true multi-turn): session assembly by
iterated generation with full history, and the repetition diagnostics the
protocol's degeneracy rule (P7_PROTOCOL.md A5) depends on. No torch; tested
in tests/test_longhorizon.py."""

from __future__ import annotations

import numpy as np


def build_multiturn(prompts_ids: list[list[int]], gen) -> tuple[np.ndarray, list[dict]]:
    """Iterate turns: turn i's context is the WHOLE session so far plus its
    own prompt; `gen(ctx_ids) -> continuation ids`. Returns (all_ids int64 —
    exactly the concatenation a v4 session archive stores — and turn metas
    [{prompt_len, gen_len, first_token}])."""
    all_ids: list[int] = []
    metas: list[dict] = []
    for p_ids in prompts_ids:
        p_ids = [int(x) for x in p_ids]
        if not p_ids:
            raise ValueError("empty turn prompt")
        g = [int(x) for x in gen(all_ids + p_ids)]
        metas.append({"prompt_len": len(p_ids), "gen_len": len(g), "first_token": p_ids[0]})
        all_ids += p_ids + g
    return np.asarray(all_ids, np.int64), metas


def tail_loop_period(ids, window: int = 512, max_period: int = 256) -> int:
    """Smallest p <= max_period such that the last `window` tokens are exactly
    periodic with period p; 0 if none (or the sequence is shorter than the
    window — undecidable at this window, reported as no loop)."""
    t = np.asarray(ids)[-window:]
    if len(t) < window:
        return 0
    for p in range(1, max_period + 1):
        if np.array_equal(t[p:], t[:-p]):
            return p
    return 0


def loop_fraction(gen_ids, window: int = 512, max_period: int = 256) -> tuple[float, int]:
    """(fraction of gen_ids inside the maximal periodic suffix, period);
    (0.0, 0) when tail_loop_period finds none."""
    p = tail_loop_period(gen_ids, window, max_period)
    if p == 0:
        return 0.0, 0
    a = np.asarray(gen_ids)
    n = len(a)
    s = window
    while s < n and a[n - s - 1] == a[n - s - 1 + p]:
        s += 1
    return s / n, p


def distinct_ngram_ratio(ids, n: int = 4) -> float:
    """#distinct n-grams / #n-grams; 1.0 for sequences shorter than n."""
    a = [int(x) for x in ids]
    if len(a) < n:
        return 1.0
    total = len(a) - n + 1
    return len({tuple(a[i:i + n]) for i in range(total)}) / total

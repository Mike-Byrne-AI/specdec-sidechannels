"""P7 pure helpers: multi-turn session assembly (contexts grow, the
concatenation matches what a v4 archive stores) and the repetition
diagnostics behind P7_PROTOCOL.md's degeneracy rule (A5)."""

import numpy as np

from amber.real.longhorizon import build_multiturn, distinct_ngram_ratio, loop_fraction, tail_loop_period


def test_build_multiturn_contexts_grow_and_concat_matches():
    seen = []

    def gen(ctx):
        seen.append(list(ctx))
        return [100 + len(ctx), 200 + len(ctx)]

    all_ids, metas = build_multiturn([[5, 6], [7], [8, 9, 10]], gen)
    assert [m["prompt_len"] for m in metas] == [2, 1, 3]
    assert [m["gen_len"] for m in metas] == [2, 2, 2]
    assert [m["first_token"] for m in metas] == [5, 7, 8]
    assert seen[0] == [5, 6]
    assert seen[1] == [5, 6, 102, 202, 7]           # turn 2 sees turn 1's generation
    assert seen[2][:5] == [5, 6, 102, 202, 7]       # turn 3 sees everything before it
    assert len(all_ids) == sum(m["prompt_len"] + m["gen_len"] for m in metas)
    np.testing.assert_array_equal(all_ids[:5], [5, 6, 102, 202, 7])


def test_tail_loop_detected_with_period_and_fraction():
    rng = np.random.default_rng(0)
    head = rng.integers(0, 50, 300)
    ids = np.concatenate([head, np.tile([1, 2, 3, 4, 5], 200)])
    frac, period = loop_fraction(ids)
    assert period == 5
    assert abs(frac - 1000 / 1300) < 0.02


def test_no_loop_on_high_entropy_text():
    rng = np.random.default_rng(1)
    ids = rng.integers(0, 5000, 800)
    assert tail_loop_period(ids) == 0
    assert loop_fraction(ids) == (0.0, 0)


def test_short_sequences_and_distinct_ngrams():
    assert tail_loop_period([1, 2, 3]) == 0          # shorter than the window: undecidable -> 0
    assert loop_fraction([1] * 100) == (0.0, 0)      # ditto (window 512)
    assert distinct_ngram_ratio([7] * 100) < 0.02
    assert distinct_ngram_ratio(list(range(100))) == 1.0
    assert distinct_ngram_ratio([1, 2]) == 1.0

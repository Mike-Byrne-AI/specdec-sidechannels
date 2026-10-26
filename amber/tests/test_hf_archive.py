"""hf-kind archives without torch: a toy autoregressive 'draft' (logits are a
deterministic function of the context) drives both the teacher-forced
encoder and the incremental decoder. Byte-exact roundtrip for gamma and
rac1, X escapes for deep ranks, typed failure on payload/header/content
corruption, drift -> first-mismatch attribution, and the D-2 reproduction
test that the decoder is really draft-only (a different draft desyncs)."""

import numpy as np
import pytest

from amber.rac_codec import FLAG_A, FLAG_C, FLAG_X, CoderParams
from amber.real.archive import (build_archive, canonical_topk_row, content_digest, decode_archive,
                                encode_symbols, parse_archive, payload_to_symbols)

V = 300
MODEL = {"id": "toy/draft", "snapshot": "abc123", "dtype": "fp32"}


def toy_logits(context: list[int], seed: int = 0) -> np.ndarray:
    """Deterministic 'draft': logits depend on the last two tokens."""
    g = np.random.default_rng(seed + 1000 * (context[-1] % 97) + (context[-2] % 89 if len(context) > 1 else 0))
    return g.normal(size=V).round(2)          # rounding -> real ties


def stable_rank(logits, tok):
    return 1 + int((logits > logits[tok]).sum()) + int(((logits == logits[tok]) & (np.arange(V) < tok)).sum())


def teacher_force(prompt, tokens, seed=0, topm=2):
    ranks, gaps, topm_idx = [], [], []
    ctx = list(prompt)
    for t in tokens:
        lg = toy_logits(ctx, seed); idx, val = canonical_topk_row(lg, np.arange(V))
        ranks.append(stable_rank(lg, t)); gaps.append(val[0] - val[1]); topm_idx.append(idx[:topm]); ctx.append(int(t))
    return np.array(ranks), np.array(gaps), np.array(topm_idx)


def make_stepper_factory(seed=0, k=128, perturb=None):
    def factory():
        ctx = []
        def step(new_ids):
            ctx.extend(new_ids)
            lg = toy_logits(ctx, seed)
            if perturb is not None:
                lg = perturb(len(ctx), lg)
            idx, val = canonical_topk_row(lg, np.arange(V))
            return idx[:k], val[:k]
        return step
    return factory


def make_content(seed, n=150, div=0.1):
    """Target-like content: mostly the draft's argmax, sometimes rank 2..5, rarely deep."""
    g = np.random.default_rng(seed); prompt = [1, 2, 3]; ctx = list(prompt); toks = []
    for _ in range(n):
        lg = toy_logits(ctx); idx, _ = canonical_topk_row(lg, np.arange(V))
        u = g.random()
        t = int(idx[0]) if u > div else int(idx[g.integers(1, 5)]) if u > 0.01 else int(idx[g.integers(64, 200)])
        toks.append(t); ctx.append(t)
    return prompt, np.array(toks)


@pytest.mark.parametrize("coder", ["gamma", "rac1"])
def test_roundtrip_byte_exact_incremental_decode(coder):
    prompt, toks = make_content(1)
    p = CoderParams(max_rank=64, vocab_bits=(V - 1).bit_length())
    ranks, gaps, tm = teacher_force(prompt, toks)
    syms = encode_symbols(ranks, gaps, tm, toks, p)
    assert any(f == FLAG_X for f, _ in syms) and any(f == FLAG_C for f, _ in syms)
    blob = build_archive(MODEL, V, prompt, toks, syms, coder, p)
    h, payload, pp = parse_archive(blob)
    assert payload_to_symbols(payload, h["payload_bits"], h["length"], h["n_corrections"], coder, pp) == syms
    out, first, _ = decode_archive(blob, make_stepper_factory())
    assert first == -1
    np.testing.assert_array_equal(out, toks)


def test_payload_and_header_corruption_are_typed():
    prompt, toks = make_content(2); p = CoderParams(vocab_bits=(V - 1).bit_length())
    syms = encode_symbols(*teacher_force(prompt, toks), toks, p)
    blob = build_archive(MODEL, V, prompt, toks, syms, "gamma", p)
    for i in range(8, len(blob), 11):
        bad = bytearray(blob); bad[i] ^= 0x08
        with pytest.raises(ValueError):
            decode_archive(bytes(bad), make_stepper_factory())


def test_different_draft_desyncs_loudly_and_pinning_works():
    prompt, toks = make_content(3); p = CoderParams(vocab_bits=(V - 1).bit_length())
    syms = encode_symbols(*teacher_force(prompt, toks), toks, p)
    blob = build_archive(MODEL, V, prompt, toks, syms, "gamma", p)
    with pytest.raises(ValueError, match="content_sha"):
        decode_archive(blob, make_stepper_factory(seed=5))      # a different draft
    out, first, _ = decode_archive(blob, make_stepper_factory(seed=5), truth=toks)
    assert 0 <= first < len(toks) and (out[first] != toks[first])
    with pytest.raises(ValueError, match="pinned"):
        decode_archive(blob, make_stepper_factory(), expected_fingerprint="0" * 16)


def test_near_tie_drift_first_mismatch_is_attributable():
    """Decoder drift below the encoder's gaps changes nothing; a top-2 swap at
    a wide-gap A position desyncs at exactly that position (rank census logic)."""
    prompt, toks = make_content(4); p = CoderParams(vocab_bits=(V - 1).bit_length())
    ranks, gaps, tm = teacher_force(prompt, toks)
    syms = encode_symbols(ranks, gaps, tm, toks, p)
    blob = build_archive(MODEL, V, prompt, toks, syms, "gamma", p)
    tiny = lambda n, lg: lg + 1e-4 * np.sin(np.arange(V) + n)      # noqa: E731  (gaps are multiples of 0.01)
    out, first, _ = decode_archive(blob, make_stepper_factory(perturb=tiny), truth=toks)
    assert first == -1
    a_pos = next(i for i, (f, _) in enumerate(syms) if f == FLAG_A and i > 5)
    def swap(n, lg):
        if n == len(prompt) + a_pos:
            i, v = canonical_topk_row(lg, np.arange(V)); lg = lg.copy(); lg[i[0]], lg[i[1]] = lg[i[1]], lg[i[0]]
        return lg
    out, first, _ = decode_archive(blob, make_stepper_factory(perturb=swap), truth=toks)
    assert first == a_pos


def test_content_digest_is_over_int32_ids():
    assert content_digest(np.array([1, 2, 3])) == content_digest(np.array([1, 2, 3], dtype=np.int64))
    assert content_digest(np.array([1, 2, 3])) != content_digest(np.array([1, 2, 4]))

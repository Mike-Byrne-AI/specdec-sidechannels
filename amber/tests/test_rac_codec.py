"""v2 coder tests: exact stream roundtrip, codec byte-exactness under rac1,
loud typed failure on payload corruption (payload_sha), and the D-2
decode-side reproduction test for the tie escape — a decoder whose draft
reorders the top-2 at near-ties still reproduces the bytes, and the test is
RED-proof: the same perturbation WITHOUT the escape (and a perturbation the
escape does not cover) visibly breaks decoding."""

import random

import numpy as np
import pytest
from sideband.synthetic import WorldConfig

from amber.codec import Archive, decode, encode, stable_order
from amber.rac_codec import (FLAG_A, FLAG_C, FLAG_T, FLAG_X, CoderParams, PayloadDecoder, PayloadEncoder,
                             classify, decode_stream, encode_stream)

CFG = dict(n_concepts=40, n_units=200, n_slots=3)


def _random_stream(n, p, seed=0):
    g = random.Random(seed); out = []
    for _ in range(n):
        r = g.random()
        if r < 0.85:
            out.append((FLAG_A, 0))
        elif r < 0.93:
            out.append((FLAG_C, g.choice([r for r in (2, 2, 2, 3, 3, 4, 5, 7, 12, 30, p.max_rank) if r <= p.max_rank])))
        elif r < 0.99 and p.tie_margin > 0:
            out.append((FLAG_T, g.randrange(p.tie_topm)))
        else:
            out.append((FLAG_X, g.randrange(1 << p.vocab_bits)))
    return out


class TestStream:
    @pytest.mark.parametrize("p", [CoderParams(), CoderParams(tie_margin=0.5, tie_topm=4),
                                   CoderParams(tie_margin=1.0, tie_topm=3, max_rank=5, vocab_bits=6, increment=8, rescale_limit=1 << 12)])
    def test_roundtrip_and_ideal_cost_tracks_real_bytes(self, p):
        syms = _random_stream(5000, p)
        pay, ideal = encode_stream(syms, p)
        assert decode_stream(pay, len(syms), p) == syms
        assert abs(8 * len(pay) - ideal) < 40      # flush + byte padding only

    def test_deterministic_bytes(self):
        p = CoderParams(tie_margin=0.5); syms = _random_stream(2000, p, seed=3)
        assert encode_stream(syms, p)[0] == encode_stream(syms, p)[0]

    def test_extra_ctx_changes_bytes_and_must_match_on_decode(self):
        p = CoderParams(n_extra_ctx=3); syms = _random_stream(2000, p)
        ctx = [i % 3 for i in range(2000)]
        pay, _ = encode_stream(syms, p, ctx)
        assert decode_stream(pay, 2000, p, ctx) == syms
        try:                                                    # value contexts are a desync hazard:
            assert decode_stream(pay, 2000, p, [0] * 2000) != syms  # wrong stream, or a loud grammar error
        except ValueError:
            pass

    def test_grammar_violations_are_typed(self):
        p = CoderParams(max_rank=8)
        enc = PayloadEncoder(p)
        with pytest.raises(ValueError):
            enc.step(0, FLAG_C, 9)
        with pytest.raises(ValueError):
            enc.step(0, FLAG_T, 0)                    # no tie escape configured
        with pytest.raises(ValueError):
            enc.step(0, FLAG_X, 1 << 17)
        assert classify(1, 5.0, p) == FLAG_A and classify(3, 5.0, p) == FLAG_C and classify(9, 5.0, p) == FLAG_X
        pt = CoderParams(tie_margin=0.5, tie_topm=2)
        assert classify(1, 0.1, pt) == FLAG_T and classify(2, 0.1, pt) == FLAG_T and classify(3, 0.1, pt) == FLAG_C

    def test_garbage_payload_is_loud_or_bounded(self):
        p = CoderParams(max_rank=8)
        dec = PayloadDecoder(b"\xff" * 64, p)
        # Every decoded symbol is either a valid grammar symbol or a ValueError —
        # never an out-of-range rank handed to the caller.
        for t in range(200):
            try:
                flag, value = dec.step(t)
            except ValueError:
                break
            assert flag in (FLAG_A, FLAG_C, FLAG_T, FLAG_X)
            if flag == FLAG_C:
                assert 2 <= value <= 8


class TestCodecV2:
    @pytest.mark.parametrize("coder,tm,m", [("gamma", 0.0, 2), ("rac1", 0.0, 2), ("rac1", 0.3, 2), ("rac1", 0.3, 4)])
    def test_roundtrip_byte_exact(self, coder, tm, m):
        for alpha, seed in ((0.5, 0), (0.9, 2)):
            cfg = WorldConfig(draft_alpha=alpha, seed=seed, **CFG)
            arc, tokens = encode(cfg, 10 + seed, 20 + seed, 500, coder=coder, tie_margin=tm, tie_topm=m)
            out = decode(Archive.from_bytes(arc.to_bytes()))
            np.testing.assert_array_equal(out, tokens)
            assert arc.header["coder"] == coder and arc.header["version"] == 2

    def test_rac1_beats_gamma_on_the_synthetic_world(self):
        cfg = WorldConfig(seed=5, **CFG)
        g, _ = encode(cfg, 1, 2, 1500, coder="gamma")
        r, _ = encode(cfg, 1, 2, 1500, coder="rac1")
        assert r.header["payload_bits"] < g.header["payload_bits"]

    def test_payload_corruption_is_typed_before_replay(self):
        cfg = WorldConfig(seed=1, **CFG)
        arc, _ = encode(cfg, 1, 2, 400, coder="rac1", tie_margin=0.3)
        blob = arc.to_bytes(); start = len(blob) - len(arc.payload)
        for i in range(start, len(blob), 7):
            bad = bytearray(blob); bad[i] ^= 0x10
            with pytest.raises(ValueError, match="payload_sha"):
                Archive.from_bytes(bytes(bad))
        # in-process Archive with a mutated payload: decode() validates too
        with pytest.raises(ValueError, match="payload_sha"):
            decode(Archive(header=arc.header, payload=arc.payload[:-1] + b"\x00"))

    def test_gamma_cannot_carry_tie_margin(self):
        cfg = WorldConfig(seed=1, **CFG)
        with pytest.raises(ValueError):
            encode(cfg, 1, 2, 100, coder="gamma", tie_margin=0.5)
        with pytest.raises(ValueError):
            encode(cfg, 1, 2, 100, coder="lz77")


def _swap_top(q, a, b):
    """Return q with the a-th and b-th ranked probabilities exchanged (an
    order flip the codec's stable order will see)."""
    order = stable_order(q); q = q.copy()
    q[order[a]], q[order[b]] = q[order[b]], q[order[a]]
    return q


class TestTieEscapeDecodeSideReproduction:
    """D-2: the escape is a decoder-visible mechanism; prove it does what it
    claims under a drifted decoder, and prove the test can fail."""

    def _pair(self, tm, m=2):
        cfg = WorldConfig(seed=7, **CFG)
        return encode(cfg, 3, 4, 600, coder="rac1", tie_margin=tm, tie_topm=m)

    def test_top2_flip_at_every_position_is_survived_with_escape(self):
        arc, tokens = self._pair(tm=1.0)      # the synthetic top-2 gap (F-3) is 0.186 < 1.0
        out = decode(arc, perturb=lambda t, q: _swap_top(q, 0, 1) if t % 3 == 0 else q)
        np.testing.assert_array_equal(out, tokens)

    def test_same_flip_breaks_decoding_without_escape(self):
        arc, tokens = self._pair(tm=0.0)
        out = decode(arc, perturb=lambda t, q: _swap_top(q, 0, 1) if t % 3 == 0 else q)
        assert not np.array_equal(out, tokens)

    def test_flip_outside_the_escaped_set_is_not_covered(self):
        # A rank-1/rank-3 swap changes the top-2 SET: with tie_topm=2 the
        # escape cannot help and the archive visibly desyncs (the set-change
        # residual p2b measures); widening the set to m=4 covers it. (This
        # synthetic world has no rank-3/4 corrections at all — every wrong
        # draft is wrong by hundreds of ranks — so the swap is applied to the
        # draft's top-3, which exists at every position.)
        arc, tokens = self._pair(tm=1.0, m=2)
        out = decode(arc, perturb=lambda t, q: _swap_top(q, 0, 2))
        assert not np.array_equal(out, tokens)
        arc4, tokens4 = self._pair(tm=1.0, m=4)
        out4 = decode(arc4, perturb=lambda t, q: _swap_top(q, 0, 2))
        np.testing.assert_array_equal(out4, tokens4)

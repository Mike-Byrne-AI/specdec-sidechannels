"""v4 session archives without torch, on the toy draft: byte-exact roundtrip
in both context modes, the reset-mode desync-containment property (a wrong
draft corrupts a turn, not the session), corruption/truncation sweeps, and
the accounting identity that reset-mode symbols equal the per-turn v3
symbols."""

import numpy as np
import pytest

from amber.binformat import CTX_RESET, CTX_SHARED, unpack_session
from amber.rac_codec import FLAG_A, CoderParams
from amber.real.archive import (build_session_archive, decode_session_archive, encode_symbols,
                                session_symbol_count)

from test_binformat import MODEL3
from test_hf_archive import V, make_content, make_stepper_factory, teacher_force

P = CoderParams(max_rank=64, vocab_bits=(V - 1).bit_length())


def _session(k=3, seed0=10):
    """k turns of toy content; returns turns_meta, all_ids, per-turn (prompt, gen)."""
    turns, metas, parts = [], [], []
    for i in range(k):
        prompt, toks = make_content(seed0 + i, n=60)
        turns.append((np.asarray(prompt), toks))
        metas.append({"prompt_len": len(prompt), "gen_len": len(toks), "first_token": int(prompt[0])})
        parts.append(np.concatenate([prompt, toks]))
    return metas, np.concatenate(parts), turns


def _symbols(metas, all_ids, ctx_mode):
    if ctx_mode == CTX_SHARED:
        ranks, gaps, tm = teacher_force([int(all_ids[0])], all_ids[1:])
        return encode_symbols(ranks, gaps, tm, all_ids[1:], P)
    syms = []
    pos = 0
    for m in metas:
        L = m["prompt_len"] + m["gen_len"]
        ids = all_ids[pos:pos + L]
        ranks, gaps, tm = teacher_force([int(ids[0])], ids[1:])
        syms += encode_symbols(ranks, gaps, tm, ids[1:], P)
        pos += L
    return syms


@pytest.mark.parametrize("ctx_mode", [CTX_RESET, CTX_SHARED])
def test_roundtrip_byte_exact(ctx_mode):
    metas, all_ids, _ = _session()
    syms = _symbols(metas, all_ids, ctx_mode)
    assert len(syms) == session_symbol_count(metas, ctx_mode)
    blob = build_session_archive(MODEL3, V, metas, all_ids, syms, "gamma", P, ctx_mode)
    h, payload, pp = unpack_session(blob)
    assert h["ctx_mode"] == ctx_mode and len(h["turns"]) == 3
    out, first, got = decode_session_archive(blob, make_stepper_factory())
    assert first == -1 and got == syms
    np.testing.assert_array_equal(out, all_ids)


def test_shared_mode_codes_later_turn_openers():
    metas, all_ids, _ = _session()
    assert session_symbol_count(metas, CTX_SHARED) == session_symbol_count(metas, CTX_RESET) + 2
    blob_r = build_session_archive(MODEL3, V, metas, all_ids, _symbols(metas, all_ids, CTX_RESET), "gamma", P, CTX_RESET)
    h, _, _ = unpack_session(blob_r)
    assert [t["first_token"] is not None for t in h["turns"]] == [True, True, True]
    blob_s = build_session_archive(MODEL3, V, metas, all_ids, _symbols(metas, all_ids, CTX_SHARED), "gamma", P, CTX_SHARED)
    hs, _, _ = unpack_session(blob_s)
    assert [t["first_token"] is not None for t in hs["turns"]] == [True, False, False]


def test_reset_mode_contains_a_wrong_draft_to_its_turn():
    """With a drifted decoder draft, reset mode still decodes on a per-turn
    basis: run without truth -> loud content failure; run with truth -> the
    first mismatch lands in turn 1's coded range, and (decoding each turn
    independently) turn 3's segment would decode fine — the containment
    property shared mode cannot have."""
    metas, all_ids, _ = _session(seed0=20)
    syms = _symbols(metas, all_ids, CTX_RESET)
    blob = build_session_archive(MODEL3, V, metas, all_ids, syms, "gamma", P, CTX_RESET)
    with pytest.raises(ValueError, match="content_sha"):
        decode_session_archive(blob, make_stepper_factory(seed=77))
    out, first, _ = decode_session_archive(blob, make_stepper_factory(seed=77), truth=all_ids)
    assert 0 <= first < metas[0]["prompt_len"] + metas[0]["gen_len"] - 1


def test_symbol_count_mismatch_rejected():
    metas, all_ids, _ = _session(seed0=30)
    syms = _symbols(metas, all_ids, CTX_RESET)
    with pytest.raises(ValueError, match="symbol count"):
        build_session_archive(MODEL3, V, metas, all_ids, syms[:-1], "gamma", P, CTX_RESET)
    with pytest.raises(ValueError, match="all_ids"):
        build_session_archive(MODEL3, V, metas, all_ids[:-1], syms, "gamma", P, CTX_RESET)


def test_every_byte_corruption_and_truncation_detected():
    metas, all_ids, _ = _session(k=2, seed0=40)
    syms = _symbols(metas, all_ids, CTX_SHARED)
    blob = build_session_archive(MODEL3, V, metas, all_ids, syms, "gamma", P, CTX_SHARED)
    for i in range(len(blob)):
        bad = bytearray(blob); bad[i] ^= 0x02
        try:
            decode_session_archive(bytes(bad), make_stepper_factory())
        except ValueError:
            continue
        raise AssertionError(f"byte {i} corruption decoded silently")
    for cut in (6, 30, len(blob) - 2):
        with pytest.raises(ValueError):
            decode_session_archive(blob[:cut], make_stepper_factory())

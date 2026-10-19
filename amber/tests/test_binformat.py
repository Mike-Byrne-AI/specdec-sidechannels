"""v3 binary archives without torch: varint edges, byte-exact roundtrip with
the prompt segment DECODED (not fed), full single-byte corruption sweep
(every byte of header and payload -> typed ValueError or a detected content
mismatch, never a silent wrong file), truncation, and size accounting
against the JSON v2 archive of the same content."""

import numpy as np
import pytest

from amber.binformat import fixed_overhead_bytes, pack, read_varint, unpack, write_varint
from amber.rac_codec import FLAG_A, FLAG_X, CoderParams
from amber.real.archive import (build_archive, build_binary_archive, decode_binary_archive, encode_symbols)

from test_hf_archive import (MODEL, V, make_content, make_stepper_factory, teacher_force)

MODEL3 = {"id": MODEL["id"], "snapshot": "ab" * 20, "dtype": "fp32"}


def _v3_blob(seed=1, coder="gamma"):
    prompt, toks = make_content(seed)
    all_ids = np.concatenate([prompt, toks])
    p = CoderParams(max_rank=64, vocab_bits=(V - 1).bit_length())
    ranks, gaps, tm = teacher_force([prompt[0]], all_ids[1:])   # score from position 1
    syms = encode_symbols(ranks, gaps, tm, all_ids[1:], p)
    return build_binary_archive(MODEL3, V, all_ids, len(prompt), syms, coder, p), all_ids, syms, p


class TestVarint:
    def test_roundtrip_edges(self):
        for v in (0, 1, 127, 128, 300, 1 << 14, (1 << 35) - 1):
            out = bytearray(); write_varint(out, v)
            got, pos = read_varint(bytes(out), 0)
            assert got == v and pos == len(out)

    def test_rejects_bad(self):
        out = bytearray()
        with pytest.raises(ValueError):
            write_varint(out, -1)
        with pytest.raises(ValueError):
            write_varint(out, 1 << 35)
        with pytest.raises(ValueError):
            read_varint(b"\x80\x80", 0)          # truncated continuation
        with pytest.raises(ValueError):
            read_varint(b"\xff\xff\xff\xff\xff\xff", 0)


@pytest.mark.parametrize("coder", ["gamma", "rac1"])
def test_v3_roundtrip_prompt_segment_decoded(coder):
    blob, all_ids, syms, p = _v3_blob(coder=coder)
    h, payload, pp = unpack(blob)
    assert h["model"] == MODEL3 and h["prompt_len"] == 3 and pp.max_rank == 64
    out, first, got_syms = decode_binary_archive(blob, make_stepper_factory())
    assert first == -1 and got_syms == syms
    np.testing.assert_array_equal(out, all_ids)     # prompt reconstructed too


def test_v3_smaller_than_v2_json():
    blob, all_ids, syms, p = _v3_blob()
    prompt = all_ids[:3]
    ranks, gaps, tm = teacher_force(prompt.tolist(), all_ids[3:])
    v2 = build_archive(MODEL, V, prompt.tolist(), all_ids[3:], encode_symbols(ranks, gaps, tm, all_ids[3:], p), "gamma", p)
    assert len(blob) < len(v2) - 200                # the JSON header alone is > 300 B
    assert len(blob) < fixed_overhead_bytes(MODEL3["id"], True) + len(blob) - 40  # sanity: overhead fn is bytes-scale


def test_every_single_byte_corruption_is_detected():
    blob, all_ids, _, _ = _v3_blob(seed=2)
    for i in range(len(blob)):
        bad = bytearray(blob); bad[i] ^= 0x04
        try:
            out, first, _ = decode_binary_archive(bytes(bad), make_stepper_factory())
        except ValueError:
            continue
        raise AssertionError(f"byte {i} corruption decoded silently")


def test_truncation_is_typed():
    blob, _, _, _ = _v3_blob(seed=3)
    for cut in (3, 8, 20, len(blob) // 2, len(blob) - 1):
        with pytest.raises(ValueError):
            decode_binary_archive(blob[:cut], make_stepper_factory())


def test_wrong_draft_and_pinning():
    blob, all_ids, _, _ = _v3_blob(seed=4)
    with pytest.raises(ValueError, match="content_sha"):
        decode_binary_archive(blob, make_stepper_factory(seed=9))
    out, first, _ = decode_binary_archive(blob, make_stepper_factory(seed=9), truth=all_ids)
    assert first >= 0
    with pytest.raises(ValueError, match="pinned"):
        decode_binary_archive(blob, make_stepper_factory(), expected_fingerprint="00" * 8)


def test_pack_validation():
    p = CoderParams(vocab_bits=9)
    kw = dict(model_id="m/x", snapshot=None, dtype="fp32", fingerprint8=b"\x01" * 8, vocab_size=V,
              coder="gamma", p=p, first_token=1, prompt_len=2, length=1, n_corrections=0,
              payload=b"", content_sha8=b"\x02" * 8)
    pack(**kw)
    with pytest.raises(ValueError):
        pack(**{**kw, "coder": "lz"})
    with pytest.raises(ValueError):
        pack(**{**kw, "dtype": "int8"})
    with pytest.raises(ValueError):
        pack(**{**kw, "snapshot": "abcd"})          # not 40 hex
    with pytest.raises(ValueError):
        pack(**{**kw, "fingerprint8": b"\x01" * 7})
    with pytest.raises(ValueError):
        pack(**{**kw, "p": CoderParams(tie_margin=0.5, vocab_bits=9)})   # gamma + escape

"""Untrusted-archive hardening (lockstep F-3 / D-11 pattern, ported).

Contract under test: any byte sequence handed to Archive.from_bytes / decode
either round-trips exactly or raises ValueError — never a bare builtin
(KeyError, TypeError, json errors, IndexError, OverflowError, MemoryError) and
never silent success on a forged header. Mutation positions/bytes come from
lockstep's specified DRBG so the sweep is reproducible across machines."""

import json

import numpy as np
import pytest
from lockstep.drbg import deterministic_ints
from sideband.synthetic import WorldConfig

from amber.codec import MAX_HEADER_BYTES, Archive, decode, encode

CFG = dict(n_concepts=6, block_size=12, n_function=20, n_units=128,
           units_per_concept=8, n_slots=32, top_n=8)


def _archive(seed=0, length=300):
    cfg = WorldConfig(seed=seed, **CFG)
    arc, tokens = encode(cfg, 1, 2, length)
    return arc, tokens


def _forge(arc: Archive, **fields) -> bytes:
    h = dict(arc.header); h.update(fields)
    return Archive(header=h, payload=arc.payload).to_bytes()


class TestMutationSweep:
    def test_seeded_single_byte_mutations_never_leak(self):
        arc, tokens = _archive()
        blob = arc.to_bytes()
        n = 400
        positions = deterministic_ints("amber-hardening-pos", n, 0, len(blob) - 1)
        values = deterministic_ints("amber-hardening-val", n, 0, 255)
        hlen = int.from_bytes(blob[4:8], "big")
        header_end = 8 + hlen
        header_silent = 0
        for pos, val in zip(positions, values):
            mut = bytearray(blob)
            if mut[pos] == val:
                val ^= 0xFF
            mut[pos] = val
            try:
                out = decode(Archive.from_bytes(bytes(mut)))
            except ValueError:
                continue
            except Exception as exc:  # noqa: BLE001 - the whole point
                pytest.fail(f"leaked {type(exc).__name__} at byte {pos}: {exc}")
            # A mutation that decodes must be either harmless (payload padding /
            # a header field that does not shape decode) or produce different
            # tokens; it must never claim to be the original archive while
            # decoding differently under a forged fingerprint.
            if np.array_equal(out, tokens):
                continue
            # Payload-bit mutations legitimately decode to different tokens (no
            # payload digest in v0 — documented gap, DECISIONS D-7); a HEADER
            # mutation that decodes to different tokens is silent corruption.
            if pos < header_end:
                header_silent += 1
        assert header_silent == 0

    def test_header_region_mutations_are_loud(self):
        arc, tokens = _archive()
        blob = arc.to_bytes()
        hlen = int.from_bytes(blob[4:8], "big")
        header_end = 8 + hlen
        for pos in range(0, header_end):
            mut = bytearray(blob)
            mut[pos] ^= 0x01
            try:
                out = decode(Archive.from_bytes(bytes(mut)))
            except ValueError:
                continue
            except Exception as exc:  # noqa: BLE001
                pytest.fail(f"leaked {type(exc).__name__} at header byte {pos}: {exc}")
            # only JSON whitespace/insignificant mutations may survive, and
            # they must decode to the identical sequence
            np.testing.assert_array_equal(out, tokens)


class TestHeaderForgery:
    @pytest.mark.parametrize("field,value", [
        ("length", -1), ("length", 10**12), ("length", "300"), ("length", True),
        ("n_corrections", -1), ("n_corrections", 10**9), ("n_corrections", 1.5),
        ("payload_bits", -1), ("payload_bits", 10**12), ("payload_bits", None),
        ("path_seed", "x"), ("draft_seed", 1.0), ("fingerprint", 123),
        ("fingerprint", "0" * 15), ("version", 1), ("version", 3), ("magic", "AMBX"),
        ("coder", "lz"), ("tie_margin", -1.0), ("tie_margin", "0"), ("tie_topm", 1), ("max_rank", 1),
        ("payload_sha", "0" * 16), ("payload_sha", 5),
        ("header_sha", "0" * 16), ("header_sha", 1),
        ("cfg", None), ("cfg", []), ("cfg", {"not_a_field": 1}),
    ])
    def test_forged_field_is_typed_failure(self, field, value):
        arc, _ = _archive()
        with pytest.raises(ValueError):
            decode(Archive.from_bytes(_forge(arc, **{field: value})))

    def test_missing_field_is_typed_failure(self):
        arc, _ = _archive()
        for key in list(arc.header):
            h = dict(arc.header); del h[key]
            with pytest.raises(ValueError):
                decode(Archive.from_bytes(Archive(header=h, payload=arc.payload).to_bytes()))

    def test_declared_length_bomb_rejected_before_replay(self):
        arc, _ = _archive()
        # a resealed bomb (attacker recomputes the digest) must still be
        # rejected at parse time by the length ceiling, before any replay work
        from amber.codec import reseal
        h = dict(arc.header); h["length"] = 10**12; h["n_corrections"] = 0
        blob = Archive(header=reseal(h), payload=arc.payload).to_bytes()
        with pytest.raises(ValueError, match="length"):
            Archive.from_bytes(blob)

    def test_caller_can_lower_max_length(self):
        arc, _ = _archive(length=300)
        with pytest.raises(ValueError, match="length"):
            Archive.from_bytes(arc.to_bytes(), max_length=100)

    def test_payload_bits_beyond_payload_rejected(self):
        arc, _ = _archive()
        with pytest.raises(ValueError):
            Archive.from_bytes(_forge(arc, payload_bits=8 * len(arc.payload) + 1))


class TestMalformedFraming:
    def test_truncated_and_oversized_headers(self):
        arc, _ = _archive()
        blob = arc.to_bytes()
        for cut in (0, 3, 4, 7, 8, 12, len(blob) // 2):
            with pytest.raises(ValueError):
                Archive.from_bytes(blob[:cut])
        big = b"AMBR" + (MAX_HEADER_BYTES + 1).to_bytes(4, "big") + b"{}"
        with pytest.raises(ValueError, match="header"):
            Archive.from_bytes(big)

    def test_non_json_and_non_object_headers(self):
        for body in (b"\xff\xfe", b"[1,2]", b"42", b'"s"', b"{", b'{"a": NaN}'):
            blob = b"AMBR" + len(body).to_bytes(4, "big") + body
            with pytest.raises(ValueError):
                Archive.from_bytes(blob)

    def test_duplicate_json_keys_rejected(self):
        arc, _ = _archive()
        hj = json.dumps(arc.header, sort_keys=True)
        dup = hj[:-1] + ', "length": 5}'   # second 'length' key
        blob = b"AMBR" + len(dup.encode()).to_bytes(4, "big") + dup.encode() + arc.payload
        with pytest.raises(ValueError, match="duplicate"):
            Archive.from_bytes(blob)

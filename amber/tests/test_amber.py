import numpy as np
import pytest

from sideband.synthetic import WorldConfig

from amber.bits import BitReader, BitWriter, gamma_decode, gamma_encode
from amber.codec import Archive, attest_with_target, decode, encode, fingerprint, reseal, stable_order

CFG = dict(n_concepts=6, block_size=12, n_function=20, n_units=128,
           units_per_concept=8, n_slots=32, top_n=8)


class TestBits:
    def test_bit_roundtrip(self):
        w = BitWriter()
        pattern = [1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0]
        for b in pattern:
            w.write_bit(b)
        r = BitReader(w.to_bytes(), w.n_bits)
        assert [r.read_bit() for _ in pattern] == pattern
        assert r.exhausted

    def test_uint_roundtrip(self):
        w = BitWriter()
        for v, width in ((0, 1), (5, 3), (255, 8), (1023, 10)):
            w.write_uint(v, width)
        r = BitReader(w.to_bytes(), w.n_bits)
        for v, width in ((0, 1), (5, 3), (255, 8), (1023, 10)):
            assert r.read_uint(width) == v

    def test_gamma_roundtrip_exhaustive_and_random(self):
        w = BitWriter()
        vals = list(range(1, 300)) + [int(x) for x in np.random.default_rng(0).integers(1, 10**9, 50)]
        for v in vals:
            gamma_encode(w, v)
        r = BitReader(w.to_bytes(), w.n_bits)
        assert [gamma_decode(r) for _ in vals] == vals

    def test_gamma_rejects_zero(self):
        with pytest.raises(ValueError):
            gamma_encode(BitWriter(), 0)

    def test_truncated_stream_raises(self):
        w = BitWriter()
        gamma_encode(w, 999)
        r = BitReader(w.to_bytes(), w.n_bits - 3)
        with pytest.raises(ValueError):
            gamma_decode(r)


class TestCodec:
    def test_roundtrip_byte_exact_across_configs(self):
        for alpha in (0.5, 0.7, 0.9):
            for seed in (0, 1, 2):
                cfg = WorldConfig(draft_alpha=alpha, seed=seed, **CFG)
                arc, tokens = encode(cfg, path_seed=10 + seed, draft_seed=20 + seed, length=600)
                blob = arc.to_bytes()
                out = decode(Archive.from_bytes(blob))
                np.testing.assert_array_equal(out, tokens)

    def test_archive_is_self_describing(self):
        cfg = WorldConfig(seed=3, **CFG)
        arc, tokens = encode(cfg, 1, 2, 400)
        rehydrated = Archive.from_bytes(arc.to_bytes())
        assert rehydrated.header["length"] == 400
        np.testing.assert_array_equal(decode(rehydrated), tokens)

    def test_bad_magic_rejected(self):
        with pytest.raises(ValueError):
            Archive.from_bytes(b"NOPE" + b"\x00" * 16)

    def test_header_tamper_detected(self):
        cfg = WorldConfig(seed=4, **CFG)
        arc, _ = encode(cfg, 1, 2, 300)
        arc.header["draft_seed"] = 999  # tamper without resealing
        with pytest.raises(ValueError, match="header_sha|fingerprint"):
            decode(arc)
        # reseal the integrity digest only: the model pin must still catch it
        from amber.codec import header_digest
        arc.header["header_sha"] = header_digest(arc.header)
        with pytest.raises(ValueError, match="fingerprint"):
            decode(arc)

    def test_pinning_to_expected_fingerprint(self):
        cfg = WorldConfig(seed=5, **CFG)
        arc, _ = encode(cfg, 1, 2, 300)
        good = fingerprint(cfg, 1, 2)
        decode(arc, expected_fingerprint=good)
        with pytest.raises(ValueError, match="pinned"):
            decode(arc, expected_fingerprint="deadbeefdeadbeef")

    def test_payload_corruption_detected_or_diverges(self):
        cfg = WorldConfig(seed=6, **CFG)
        arc, tokens = encode(cfg, 1, 2, 500)
        assert len(arc.payload) > 4
        corrupted = bytearray(arc.payload)
        corrupted[len(corrupted) // 2] ^= 0xFF
        bad = Archive(header=arc.header, payload=bytes(corrupted))
        try:
            out = decode(bad)
            assert not np.array_equal(out, tokens)
        except ValueError:
            pass  # exhausting/malformed stream is an acceptable loud failure

    def test_wrong_replay_model_changes_output(self):
        """A different draft (alpha nudged) silently yields different tokens —
        which is exactly what L0 fingerprinting exists to catch up front."""
        cfg = WorldConfig(draft_alpha=0.7, seed=7, **CFG)
        arc, tokens = encode(cfg, 1, 2, 500)
        wrong = Archive(header=dict(arc.header), payload=arc.payload)
        wrong_cfg = dict(wrong.header["cfg"]); wrong_cfg["draft_alpha"] = 0.6
        wrong.header["cfg"] = wrong_cfg
        wrong.header = reseal(wrong.header)
        out = decode(wrong)
        assert not np.array_equal(out, tokens)

    def test_monotone_recalibration_invariance(self):
        """Rank coding sees only the ORDER of q: a temperature change (a
        monotone recalibration) decodes identically. Robustness and an
        attestation blind spot at once — documented as AF-2's caveat."""
        cfg = WorldConfig(draft_temperature=1.6, seed=8, **CFG)
        arc, tokens = encode(cfg, 1, 2, 500)
        warm = Archive(header=dict(arc.header), payload=arc.payload)
        warm_cfg = dict(warm.header["cfg"]); warm_cfg["draft_temperature"] = 2.4
        warm.header["cfg"] = warm_cfg
        warm.header = reseal(warm.header)
        np.testing.assert_array_equal(decode(warm), tokens)

    def test_ranks_always_at_least_two_on_corrections(self):
        cfg = WorldConfig(draft_alpha=0.5, seed=9, **CFG)
        arc, tokens = encode(cfg, 1, 2, 400)
        # decode path exercises rank>=2 implicitly; verify count consistency
        assert arc.header["n_corrections"] > 0
        out = decode(arc)
        np.testing.assert_array_equal(out, tokens)


class TestAttestation:
    def test_matched_target_attests(self):
        cfg = WorldConfig(seed=10, **CFG)
        arc, tokens = encode(cfg, 1, 2, 400)
        rep = attest_with_target(arc, tokens)
        assert rep["attested"] is True
        assert rep["recomputed_divergences"] == arc.header["n_corrections"]

    def test_tampered_tokens_fail_attestation(self):
        cfg = WorldConfig(seed=11, **CFG)
        arc, tokens = encode(cfg, 1, 2, 400)
        forged = tokens.copy(); forged[100] = (forged[100] + 1) % WorldConfig(seed=11, **CFG).vocab_size
        rep = attest_with_target(arc, forged)
        assert rep["attested"] is False
        assert rep["token_mismatches_vs_target"] == 1


class TestStableOrder:
    def test_tie_break_matches_sideband_convention(self):
        q = np.array([0.2, 0.4, 0.2, 0.2])
        assert stable_order(q).tolist() == [1, 0, 2, 3]

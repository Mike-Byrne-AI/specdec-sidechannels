"""End-to-end codec tests over the reference models."""

import unittest

from . import _SRC  # noqa
from lockstep.codec import decode_bytes, encode_bytes, roundtrip_ok
from lockstep.drbg import deterministic_bytes
from lockstep.models import AdaptiveByteModel, UniformModel


CORPORA = {
    "empty": b"",
    "one": b"\x00",
    "all_bytes": bytes(range(256)) * 3,
    "ascii": (b"Information can live in computation instead of storage. "
              b"The grid is the sponge; the coder is the ledger. ") * 40,
    "random_2k": deterministic_bytes("codec-rand", 2048),
    "runs": b"A" * 1500 + b"B" * 1500,
}


class TestCodec(unittest.TestCase):
    def test_adaptive_roundtrips_all_corpora(self):
        for name, data in CORPORA.items():
            with self.subTest(corpus=name):
                self.assertTrue(roundtrip_ok(data, AdaptiveByteModel), name)

    def test_uniform_roundtrips_and_is_incompressible(self):
        data = CORPORA["ascii"]
        payload = encode_bytes(data, UniformModel())
        self.assertEqual(decode_bytes(payload, len(data), UniformModel()), data)
        # uniform model can't beat 1.0x by more than coder epsilon
        self.assertGreater(len(payload), len(data) - 4)

    def test_adaptive_beats_uniform_on_text(self):
        data = CORPORA["ascii"]
        a = len(encode_bytes(data, AdaptiveByteModel()))
        u = len(encode_bytes(data, UniformModel()))
        self.assertLess(a, u // 2, f"adaptive {a} vs uniform {u}")

    def test_bitstream_is_repeatable(self):
        data = CORPORA["random_2k"]
        p1 = encode_bytes(data, AdaptiveByteModel())
        p2 = encode_bytes(data, AdaptiveByteModel())
        self.assertEqual(p1, p2)

    def test_encoder_decoder_are_separate_instances(self):
        data = CORPORA["runs"]
        payload = encode_bytes(data, AdaptiveByteModel())
        self.assertEqual(decode_bytes(payload, len(data), AdaptiveByteModel()), data)


if __name__ == "__main__":
    unittest.main()

"""Conformance vectors: the profile's promise, written down as hashes.

Every runtime that claims decode profile lsp0 must reproduce these
payload hashes bit-exactly. Regenerate ONLY on an intentional format
break, via: python tools/lockstep_gen_vectors.py --write
"""

import hashlib
import json
import os
import unittest

from . import _SRC  # noqa
from lockstep.codec import decode_bytes, encode_bytes
from lockstep.drbg import deterministic_bytes
from lockstep.models import make_model

VECTORS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "conformance", "vectors_v0.json")


def _materialize(case):
    inp = case["input"]
    if inp["kind"] == "literal-utf8":
        return inp["text"].encode("utf-8")
    if inp["kind"] == "drbg":
        return deterministic_bytes(inp["seed"], inp["n"])
    if inp["kind"] == "byte-ramp":
        return bytes(range(256)) * inp["repeat"]
    raise AssertionError(f"unknown input kind {inp['kind']}")


class TestConformance(unittest.TestCase):
    def test_vectors_reproduce_bit_exactly(self):
        self.assertTrue(os.path.exists(VECTORS),
                        "missing conformance/vectors_v0.json — run "
                        "python tools/lockstep_gen_vectors.py --write")
        with open(VECTORS) as f:
            spec = json.load(f)
        self.assertEqual(spec["profile"], "lsp0")
        for case in spec["cases"]:
            with self.subTest(case=case["name"]):
                data = _materialize(case)
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 case["original_sha256"], "input drifted")
                payload = encode_bytes(data, make_model(case["model"]))
                self.assertEqual(len(payload), case["payload_size"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(),
                                 case["payload_sha256"],
                                 "ENCODER no longer conforms to lsp0")
                back = decode_bytes(payload, len(data), make_model(case["model"]))
                self.assertEqual(back, data, "DECODER desync")


if __name__ == "__main__":
    unittest.main()

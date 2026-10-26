"""Container format: identity, tamper evidence, and failure taxonomy."""

import json
import struct
import unittest

from . import _SRC  # noqa
from lockstep import container
from lockstep.container import ContainerError, pack, read_manifest, unpack
from lockstep.drbg import deterministic_bytes


DATA = (b"Model-pinned archives: the manifest is the contract. " * 30
        + deterministic_bytes("container", 512))


class TestContainer(unittest.TestCase):
    def test_pack_unpack_identity(self):
        self.assertEqual(unpack(pack(DATA)), DATA)

    def test_manifest_pins_what_matters(self):
        m = read_manifest(pack(DATA))
        self.assertEqual(m["profile"]["id"], "lsp0")
        self.assertEqual(m["original"]["size"], len(DATA))
        self.assertIn("sha256", m["original"])
        self.assertIn("sha256", m["payload"])
        self.assertEqual(m["profile"]["model"]["model"], "adaptive-order1")

    def test_payload_tamper_is_loud_and_diagnosed(self):
        blob = bytearray(pack(DATA))
        blob[-3] ^= 0x40
        with self.assertRaises(ContainerError) as cm:
            unpack(bytes(blob))
        self.assertIn("payload hash", str(cm.exception))

    def test_manifest_tamper_is_loud(self):
        blob = pack(DATA)
        (mlen,) = struct.unpack(">I", blob[4:8])
        m = json.loads(blob[8:8 + mlen])
        m["original"]["sha256"] = "0" * 64
        mb = json.dumps(m, sort_keys=True, separators=(",", ":")).encode()
        forged = blob[:4] + struct.pack(">I", len(mb)) + mb + blob[8 + mlen:]
        with self.assertRaises(ContainerError) as cm:
            unpack(forged)
        self.assertIn("decoder desync", str(cm.exception))

    def test_bad_magic_and_truncation(self):
        with self.assertRaises(ContainerError):
            read_manifest(b"NOPE" + b"\x00" * 16)
        with self.assertRaises(ContainerError):
            unpack(pack(DATA)[:-5])

    def test_unknown_pinned_model_refused(self):
        blob = pack(DATA)
        (mlen,) = struct.unpack(">I", blob[4:8])
        m = json.loads(blob[8:8 + mlen])
        m["profile"]["model"]["model"] = "llama-3-8b-q4"
        mb = json.dumps(m, sort_keys=True, separators=(",", ":")).encode()
        forged = blob[:4] + struct.pack(">I", len(mb)) + mb + blob[8 + mlen:]
        with self.assertRaises(ContainerError) as cm:
            unpack(forged)
        self.assertIn("not provided by this runtime", str(cm.exception))

    def test_verify_only_writes_nothing_and_passes(self):
        self.assertIsNone(unpack(pack(DATA), verify_only=True))

    def test_empty_input(self):
        self.assertEqual(unpack(pack(b"")), b"")


if __name__ == "__main__":
    unittest.main()

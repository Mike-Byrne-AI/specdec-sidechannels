"""Adversarial container and manifest regression tests."""

import json
import struct
import unittest

from . import _SRC  # noqa
from lockstep.container import MAX_MANIFEST_SIZE, pack, read_manifest, unpack
from lockstep.errors import (
    DesyncError,
    IntegrityError,
    ManifestError,
    ManifestResourceLimitError,
    ResourceLimitError,
    UnsupportedProfileError,
)


def _split(blob):
    mlen = struct.unpack(">I", blob[4:8])[0]
    return json.loads(blob[8 : 8 + mlen]), blob[8 + mlen :]


def _forge(manifest, payload=b""):
    mbytes = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return b"LSA0" + struct.pack(">I", len(mbytes)) + mbytes + payload


class TestContainerHardening(unittest.TestCase):
    def test_every_pinned_model_parameter_is_enforced(self):
        blob = pack(b"model pinning matters " * 80)
        manifest, payload = _split(blob)
        mutations = {
            "alphabet": 999,
            "increment": 25,
            "rescale_limit": 257,
        }
        for key, value in mutations.items():
            changed = json.loads(json.dumps(manifest))
            changed["profile"]["model"][key] = value
            with self.subTest(key=key):
                with self.assertRaises(UnsupportedProfileError):
                    unpack(_forge(changed, payload))

    def test_required_model_parameter_cannot_be_omitted(self):
        blob = pack(b"x" * 100)
        manifest, payload = _split(blob)
        del manifest["profile"]["model"]["increment"]
        with self.assertRaises(UnsupportedProfileError):
            unpack(_forge(manifest, payload))

    def test_unknown_extension_keys_remain_forward_compatible(self):
        blob = pack(b"extensions")
        manifest, payload = _split(blob)
        manifest["x-future"] = {"flag": True}
        self.assertEqual(unpack(_forge(manifest, payload)), b"extensions")

    def test_duplicate_json_keys_are_rejected(self):
        manifest = (
            b'{"format":"wrong","format":"lockstep-container",'
            b'"format_version":0}'
        )
        blob = b"LSA0" + struct.pack(">I", len(manifest)) + manifest
        with self.assertRaises(ManifestError) as cm:
            read_manifest(blob)
        self.assertIn("duplicate JSON key", str(cm.exception))

    def test_huge_json_integer_is_wrapped_as_manifest_error(self):
        manifest = (
            '{"format":"lockstep-container","format_version":'
            + "9" * 5000
            + "}"
        ).encode("ascii")
        blob = b"LSA0" + struct.pack(">I", len(manifest)) + manifest
        with self.assertRaises(ManifestError):
            read_manifest(blob)

    def test_nonfinite_json_constant_is_rejected(self):
        manifest = b'{"format":"lockstep-container","format_version":NaN}'
        blob = b"LSA0" + struct.pack(">I", len(manifest)) + manifest
        with self.assertRaises(ManifestError):
            read_manifest(blob)

    def test_unpaired_unicode_surrogate_is_rejected(self):
        blob = pack(b"unicode extension")
        manifest, payload = _split(blob)
        canonical = json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        raw = b'{"x-future":"\\ud800",' + canonical[1:]
        forged = b"LSA0" + struct.pack(">I", len(raw)) + raw + payload
        with self.assertRaises(ManifestError):
            read_manifest(forged)

    def test_float_exponent_overflow_is_rejected_even_in_extension(self):
        blob = pack(b"float extension")
        manifest, payload = _split(blob)
        canonical = json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        raw = b'{"x-future":1e999,' + canonical[1:]
        forged = b"LSA0" + struct.pack(">I", len(raw)) + raw + payload
        with self.assertRaises(ManifestError):
            read_manifest(forged)

    def test_finite_float_in_unknown_extension_is_ignored(self):
        blob = pack(b"finite extension")
        manifest, payload = _split(blob)
        manifest["x-future"] = 1.25
        self.assertEqual(unpack(_forge(manifest, payload)), b"finite extension")

    def test_unsupported_version_profile_and_coder_are_distinct(self):
        blob = pack(b"unsupported classification")
        manifest, payload = _split(blob)
        mutations = (
            ("format_version", 1),
            ("profile.id", "lsp9"),
            ("profile.coder.code_bits", 31),
            ("profile.coder.prob_bits_max", 15),
        )
        for path, value in mutations:
            changed = json.loads(json.dumps(manifest))
            if path == "format_version":
                changed[path] = value
            elif path == "profile.id":
                changed["profile"]["id"] = value
            else:
                changed["profile"]["coder"][path.rsplit(".", 1)[1]] = value
            with self.subTest(path=path):
                with self.assertRaises(UnsupportedProfileError):
                    read_manifest(_forge(changed, payload))

    def test_manifest_length_limit_applies_before_parse(self):
        declared = MAX_MANIFEST_SIZE + 1
        blob = b"LSA0" + struct.pack(">I", declared)
        with self.assertRaises(ManifestResourceLimitError):
            read_manifest(blob)

    def test_manifest_reader_rejects_payload_padding_and_truncation(self):
        blob = pack(b"framing")
        with self.assertRaises(IntegrityError):
            read_manifest(blob + b"padding")
        with self.assertRaises(IntegrityError):
            read_manifest(blob[:-1])

    def test_actual_and_declared_payload_limits_are_enforced(self):
        blob = pack(b"a" * 2000, "uniform")
        with self.assertRaises(ResourceLimitError):
            read_manifest(blob, max_payload_size=10)

        manifest, payload = _split(blob)
        manifest["payload"]["size"] = 10_000
        with self.assertRaises(ManifestResourceLimitError):
            read_manifest(_forge(manifest, payload), max_payload_size=2500)

    def test_writer_is_optional_but_typed_when_present(self):
        blob = pack(b"writer")
        manifest, payload = _split(blob)
        del manifest["writer"]
        self.assertEqual(unpack(_forge(manifest, payload)), b"writer")
        manifest["writer"] = {"tool": 7, "version": "0"}
        with self.assertRaises(ManifestError):
            unpack(_forge(manifest, payload))
        manifest["writer"] = {"tool": "lockstep"}
        with self.assertRaises(ManifestError):
            unpack(_forge(manifest, payload))

    def test_payload_damage_has_specific_exception(self):
        blob = bytearray(pack(b"damage" * 100))
        blob[-1] ^= 1
        with self.assertRaises(IntegrityError):
            unpack(bytes(blob))

    def test_decoded_hash_mismatch_has_specific_exception(self):
        blob = pack(b"desync" * 100)
        manifest, payload = _split(blob)
        manifest["original"]["sha256"] = "0" * 64
        with self.assertRaises(DesyncError):
            unpack(_forge(manifest, payload))

    def test_invalid_reader_limit_is_caller_error(self):
        with self.assertRaises(ValueError):
            unpack(pack(b"x"), verify_only=1)
        with self.assertRaises(ValueError):
            read_manifest(pack(b"x"), max_original_size=True)
        with self.assertRaises(ValueError):
            read_manifest(pack(b"x"), max_payload_size=-1)


if __name__ == "__main__":
    unittest.main()

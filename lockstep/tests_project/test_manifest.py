"""Strict manifest validation — regression tests for the F-3 hardening.

Every malformed manifest must raise ManifestError (a ContainerError), and
NO test here may see a bare KeyError/TypeError/AttributeError. The bomb
ceiling must refuse an oversized declared original size before any decode.
"""

import json
import struct
import unittest

from . import _SRC  # noqa
from lockstep.container import pack, unpack
from lockstep.manifest import (DEFAULT_MAX_ORIGINAL_SIZE, ManifestError,
                               validate_manifest)

E = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _good_manifest():
    return {
        "format": "lockstep-container",
        "format_version": 0,
        "profile": {"id": "lsp0",
                    "coder": {"code_bits": 32, "prob_bits_max": 16},
                    "model": {"model": "uniform"}},
        "original": {"size": 0, "sha256": E},
        "payload": {"size": 0, "sha256": E},
    }


def _forge(manifest, payload=b""):
    mb = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return b"LSA0" + struct.pack(">I", len(mb)) + mb + payload


class TestManifestValidation(unittest.TestCase):
    def test_good_manifest_passes(self):
        self.assertEqual(validate_manifest(_good_manifest())["format_version"], 0)

    def test_non_dict_roots_rejected(self):
        for bad in ([], "x", 7, None, 3.14):
            with self.assertRaises(ManifestError):
                validate_manifest(bad)

    def test_each_field_type_enforced(self):
        mutators = [
            ("format", "not-lockstep"),
            ("format_version", "0"),
            ("format_version", 1),
            ("profile", 7),
            ("original", "x"),
            ("payload", []),
        ]
        for key, val in mutators:
            m = _good_manifest()
            m[key] = val
            with self.subTest(key=key, val=val):
                with self.assertRaises(ManifestError):
                    validate_manifest(m)

    def test_bool_is_not_accepted_as_size(self):
        m = _good_manifest()
        m["original"]["size"] = True  # bool is an int subclass; must be refused
        with self.assertRaises(ManifestError):
            validate_manifest(m)

    def test_negative_size_rejected(self):
        m = _good_manifest()
        m["original"]["size"] = -1
        with self.assertRaises(ManifestError):
            validate_manifest(m)

    def test_sha_must_be_lowercase_hex_64(self):
        for bad in ("ZZ", "0" * 63, "0" * 65, E.upper(), 123):
            m = _good_manifest()
            m["original"]["sha256"] = bad
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    validate_manifest(m)

    def test_coder_constants_pinned(self):
        for key, val in (("code_bits", 16), ("prob_bits_max", 20)):
            m = _good_manifest()
            m["profile"]["coder"][key] = val
            with self.subTest(key=key):
                with self.assertRaises(ManifestError):
                    validate_manifest(m)

    def test_unknown_model_rejected_when_registry_supplied(self):
        m = _good_manifest()
        m["profile"]["model"]["model"] = "llama-3-8b"
        with self.assertRaises(ManifestError):
            validate_manifest(m, known_models={"uniform", "adaptive-order1"})
        # but tolerated when the caller defers model checking
        self.assertEqual(validate_manifest(m, known_models=None)["format_version"], 0)

    def test_bomb_ceiling_refuses_oversized_declared_size(self):
        m = _good_manifest()
        m["original"]["size"] = 10 ** 12
        with self.assertRaises(ManifestError):
            validate_manifest(m, max_original_size=DEFAULT_MAX_ORIGINAL_SIZE)

    def test_unpack_never_leaks_builtin_exceptions(self):
        forgeries = [
            _forge({"format": "lockstep-container", "format_version": 0,
                    "original": {"size": 1, "sha256": "0" * 64},
                    "profile": {"id": "lsp0", "coder": {"code_bits": 32, "prob_bits_max": 16},
                                "model": {"model": "uniform"}}}),  # missing payload
            _forge({"format": "lockstep-container", "format_version": 0, "payload": "hi",
                    "original": {"size": 0, "sha256": E},
                    "profile": {"id": "lsp0", "coder": {"code_bits": 32, "prob_bits_max": 16},
                                "model": {"model": "uniform"}}}),  # payload not dict
            b"LSA0" + struct.pack(">I", 2) + b"[]",                 # manifest is a list
            _forge({"format": "lockstep-container", "format_version": 0,
                    "payload": {"size": 0, "sha256": E},
                    "original": {"size": 0, "sha256": E}, "profile": 7}),  # profile scalar
        ]
        for blob in forgeries:
            with self.subTest(blob=blob[:16]):
                with self.assertRaises(ManifestError):
                    unpack(blob)

    def test_caller_bound_enforced_on_real_container(self):
        blob = pack(b"x" * 300)
        with self.assertRaises(ManifestError):
            unpack(blob, max_original_size=100)
        self.assertEqual(unpack(blob, max_original_size=10_000), b"x" * 300)

    def test_legit_container_still_round_trips(self):
        self.assertEqual(unpack(pack(b"unchanged path")), b"unchanged path")


if __name__ == "__main__":
    unittest.main()

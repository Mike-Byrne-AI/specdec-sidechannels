"""Streaming codec and atomic file-container behavior."""

import hashlib
import io
import json
import os
import struct
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from . import _SRC  # noqa
from lockstep.codec import decode_stream, encode_bytes, encode_stream
from lockstep import container as container_module
from lockstep.container import (
    pack,
    pack_file,
    read_manifest_file,
    unpack_file,
    verify_file,
)
from lockstep.errors import DesyncError, IntegrityError, ResourceLimitError
from lockstep.models import make_model


class TestStreamingCodec(unittest.TestCase):
    def test_stream_encoder_is_bit_identical_to_memory_encoder(self):
        data = (bytes(range(256)) + b"deterministic-stream\n" * 20) * 8
        expected = encode_bytes(data, make_model("adaptive-order1"))
        sink = io.BytesIO()
        stats = encode_stream(
            io.BytesIO(data), sink, make_model("adaptive-order1"), chunk_size=37
        )
        self.assertEqual(sink.getvalue(), expected)
        self.assertEqual(stats.input_bytes, len(data))
        self.assertEqual(stats.payload_bytes, len(expected))

    def test_stream_decoder_matches_memory_path(self):
        data = b"decode in bounded chunks\n" * 400
        payload = encode_bytes(data, make_model("adaptive-order1"))
        sink = io.BytesIO()
        written = decode_stream(
            io.BytesIO(payload),
            len(data),
            make_model("adaptive-order1"),
            sink,
            chunk_size=31,
        )
        self.assertEqual(written, len(data))
        self.assertEqual(sink.getvalue(), data)


class TestStreamingContainerFiles(unittest.TestCase):
    def test_pack_file_is_byte_identical_to_pack(self):
        data = b"file and memory APIs share one format\n" * 200
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.bin"
            archive = Path(tmp) / "archive.lsa"
            source.write_bytes(data)
            stats = pack_file(str(source), str(archive))
            expected = pack(data)
            self.assertEqual(archive.read_bytes(), expected)
            self.assertEqual(stats["out_bytes"], len(expected))
            self.assertEqual(stats["payload_bytes"], read_manifest_file(archive)["payload"]["size"])

    def test_verify_and_unpack_file_roundtrip(self):
        data = hashlib.sha256(b"seed").digest() * 400
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.bin"
            archive = Path(tmp) / "archive.lsa"
            output = Path(tmp) / "output.bin"
            source.write_bytes(data)
            pack_file(source, archive, "uniform")
            verified = verify_file(archive)
            unpacked = unpack_file(archive, output)
            self.assertEqual(verified["out_bytes"], len(data))
            self.assertEqual(unpacked["out_bytes"], len(data))
            self.assertEqual(output.read_bytes(), data)

    def test_source_mutation_between_hash_and_decode_is_detected(self):
        data = b"stable snapshot required" * 300
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.lsa"
            destination = Path(tmp) / "existing.bin"
            archive.write_bytes(pack(data))
            destination.write_bytes(b"KEEP-ME")
            real_hash_exact = container_module._hash_exact
            mutated = False

            def hash_then_mutate(stream, size, label="payload"):
                nonlocal mutated
                digest = real_hash_exact(stream, size, label)
                if not mutated and label == "payload":
                    mutated = True
                    with open(archive, "r+b") as attacker:
                        attacker.seek(-1, os.SEEK_END)
                        value = attacker.read(1)
                        attacker.seek(-1, os.SEEK_END)
                        attacker.write(bytes([value[0] ^ 1]))
                        attacker.flush()
                return digest

            with mock.patch.object(
                container_module, "_hash_exact", side_effect=hash_then_mutate
            ):
                with self.assertRaises(IntegrityError):
                    unpack_file(archive, destination)
            self.assertTrue(mutated)
            self.assertEqual(destination.read_bytes(), b"KEEP-ME")

    def test_failed_decode_never_clobbers_existing_destination(self):
        data = b"atomic output" * 300
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.lsa"
            destination = Path(tmp) / "existing.bin"
            archive.write_bytes(pack(data))
            destination.write_bytes(b"KEEP-ME")

            blob = archive.read_bytes()
            mlen = struct.unpack(">I", blob[4:8])[0]
            manifest = json.loads(blob[8 : 8 + mlen])
            manifest["original"]["sha256"] = "0" * 64
            mbytes = json.dumps(
                manifest, sort_keys=True, separators=(",", ":")
            ).encode()
            archive.write_bytes(
                b"LSA0" + struct.pack(">I", len(mbytes)) + mbytes + blob[8 + mlen :]
            )

            with self.assertRaises(DesyncError):
                unpack_file(archive, destination)
            self.assertEqual(destination.read_bytes(), b"KEEP-ME")
            self.assertEqual(list(Path(tmp).glob(".existing.bin.*.tmp")), [])

    def test_pack_limit_does_not_replace_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "large.bin"
            destination = Path(tmp) / "existing.lsa"
            source.write_bytes(b"x" * 100)
            destination.write_bytes(b"KEEP")
            with self.assertRaises(ResourceLimitError):
                pack_file(source, destination, max_original_size=10)
            self.assertEqual(destination.read_bytes(), b"KEEP")

    def test_pack_payload_growth_limit_does_not_replace_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.bin"
            destination = Path(tmp) / "existing.lsa"
            source.write_bytes(bytes(range(256)) * 8)
            destination.write_bytes(b"KEEP")
            with self.assertRaises(ResourceLimitError):
                pack_file(
                    source, destination, "uniform", max_payload_size=32
                )
            self.assertEqual(destination.read_bytes(), b"KEEP")
            self.assertEqual(list(Path(tmp).glob(".existing.lsa.*.tmp")), [])

    def test_source_and_destination_may_be_the_same_path_safely(self):
        data = b"in-place workflows still use atomic replacement" * 50
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "same.bin"
            path.write_bytes(data)
            pack_file(path, path)
            self.assertNotEqual(path.read_bytes(), data)
            unpack_file(path, path)
            self.assertEqual(path.read_bytes(), data)

    def test_read_manifest_file_detects_padding_without_decoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.lsa"
            archive.write_bytes(pack(b"padding") + b"extra")
            with self.assertRaises(IntegrityError):
                read_manifest_file(archive)


if __name__ == "__main__":
    unittest.main()

"""Lockstep container v0 (``.lsa``): framing, integrity, and safe file I/O.

The in-memory API remains small and convenient. File APIs are incremental,
verify payload integrity before decoding, and publish destination files with an
atomic replace only after the decoded digest succeeds.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from . import __version__
from .codec import decode_bytes, decode_stream, encode_bytes, encode_stream
from .errors import (
    CoderError,
    ContainerError,
    DesyncError,
    IntegrityError,
    ManifestError,
    ManifestResourceLimitError,
    ResourceLimitError,
    UnsupportedProfileError,
)
from .manifest import (
    DEFAULT_MAX_ORIGINAL_SIZE,
    DEFAULT_MAX_PAYLOAD_SIZE,
    FORMAT_NAME,
    FORMAT_VERSION,
    PROFILE_ID,
    validate_manifest,
)
from .models import MODEL_PROFILES, MODEL_REGISTRY, make_model
from .rac import CODE_BITS, PROB_BITS_MAX

MAGIC = b"LSA0"
MAX_MANIFEST_SIZE = 1 * 1024 * 1024
_JSON_INT_DIGITS = 128
_JSON_FLOAT_CHARS = 256
_IO_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class _Frame:
    manifest: dict
    manifest_length: int
    payload_offset: int
    payload_size: int
    total_size: int
    prefix_sha256: str


class _DuplicateKeyError(ValueError):
    pass


def _canonical_json(obj: dict) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _same_digest(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def _resolve_limit(value: Optional[int], default: int, name: str) -> int:
    resolved = default if value is None else value
    if not isinstance(resolved, int) or isinstance(resolved, bool) or resolved < 0:
        raise ValueError(f"{name} must be a non-negative integer (not bool)")
    return resolved


def _json_object(pairs: list[tuple[str, Any]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateKeyError(f"duplicate JSON key {key!r}")
        obj[key] = value
    return obj


def _json_int(text: str) -> int:
    digits = text[1:] if text.startswith("-") else text
    if len(digits) > _JSON_INT_DIGITS:
        raise ValueError(f"JSON integer exceeds {_JSON_INT_DIGITS} digits")
    return int(text)


def _json_float(text: str) -> float:
    if len(text) > _JSON_FLOAT_CHARS:
        raise ValueError(f"JSON floating-point literal exceeds {_JSON_FLOAT_CHARS} characters")
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"JSON floating-point literal {text!r} is not finite")
    return value


def _reject_json_constant(text: str) -> None:
    raise ValueError(f"non-finite JSON constant {text!r} is not permitted")


def _validate_json_strings(root: Any) -> None:
    stack = [root]
    while stack:
        value = stack.pop()
        if isinstance(value, str):
            if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
                raise ValueError("JSON string contains an unpaired Unicode surrogate")
        elif isinstance(value, dict):
            stack.extend(value.keys())
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)


def _parse_manifest_bytes(data: bytes) -> dict:
    try:
        text = data.decode("utf-8")
        parsed = json.loads(
            text,
            object_pairs_hook=_json_object,
            parse_int=_json_int,
            parse_float=_json_float,
            parse_constant=_reject_json_constant,
        )
        _validate_json_strings(parsed)
        return parsed
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateKeyError,
        ValueError,
        RecursionError,
    ) as exc:
        raise ManifestError(f"manifest is not valid unambiguous JSON: {exc}") from exc


def _manifest_for(data_size: int, data_sha: str, payload_size: int, payload_sha: str,
                  model_profile: dict) -> dict:
    return {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "profile": {
            "id": PROFILE_ID,
            "coder": {"code_bits": CODE_BITS, "prob_bits_max": PROB_BITS_MAX},
            "model": model_profile,
        },
        "original": {"size": data_size, "sha256": data_sha},
        "payload": {"size": payload_size, "sha256": payload_sha},
        "writer": {"tool": "lockstep", "version": __version__},
    }


def _model(name: str):
    if not isinstance(name, str) or name not in MODEL_REGISTRY:
        raise UnsupportedProfileError(
            f"unknown model {name!r} (have: {sorted(MODEL_REGISTRY)})"
        )
    try:
        return make_model(name)
    except CoderError as exc:
        raise UnsupportedProfileError(str(exc)) from exc


def _bytes_view(value: Any, name: str) -> memoryview:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise ContainerError(f"{name} must be bytes-like")
    try:
        return memoryview(value).cast("B")
    except (TypeError, ValueError) as exc:
        raise ContainerError(f"{name} must be a one-dimensional byte buffer") from exc


def pack(data: bytes, model_name: str = "adaptive-order1") -> bytes:
    view = _bytes_view(data, "data")
    raw = bytes(view)
    model = _model(model_name)
    profile = model.profile_fields()
    try:
        payload = encode_bytes(raw, model)
    except CoderError as exc:
        raise ContainerError(f"encode failed: {exc}") from exc
    manifest = _manifest_for(
        len(raw), _sha256_hex(raw), len(payload), _sha256_hex(payload), profile
    )
    manifest_bytes = _canonical_json(manifest)
    if len(manifest_bytes) > MAX_MANIFEST_SIZE:
        raise ResourceLimitError("generated manifest exceeds MAX_MANIFEST_SIZE")
    return MAGIC + struct.pack(">I", len(manifest_bytes)) + manifest_bytes + payload


def read_manifest(
    blob: bytes,
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
    max_manifest_size: int = MAX_MANIFEST_SIZE,
) -> dict:
    """Parse and strictly validate a manifest from an in-memory container."""
    original_limit = _resolve_limit(
        max_original_size, DEFAULT_MAX_ORIGINAL_SIZE, "max_original_size"
    )
    payload_limit = _resolve_limit(
        max_payload_size, DEFAULT_MAX_PAYLOAD_SIZE, "max_payload_size"
    )
    manifest_limit = _resolve_limit(max_manifest_size, MAX_MANIFEST_SIZE, "max_manifest_size")
    view = _bytes_view(blob, "blob")
    if len(view) < 8 or bytes(view[:4]) != MAGIC:
        raise ContainerError("not a Lockstep container (bad magic)")
    manifest_length = struct.unpack(">I", bytes(view[4:8]))[0]
    if manifest_length > manifest_limit:
        raise ManifestResourceLimitError(
            f"manifest length {manifest_length} exceeds max_manifest_size {manifest_limit}"
        )
    if len(view) < 8 + manifest_length:
        raise ContainerError("truncated manifest")
    actual_payload_size = len(view) - 8 - manifest_length
    if actual_payload_size > payload_limit:
        raise ResourceLimitError(
            f"actual payload size {actual_payload_size} exceeds max_payload_size {payload_limit}"
        )
    parsed = _parse_manifest_bytes(bytes(view[8 : 8 + manifest_length]))
    manifest = validate_manifest(
        parsed,
        max_original_size=original_limit,
        max_payload_size=payload_limit,
        known_models=MODEL_REGISTRY,
        expected_model_profiles=MODEL_PROFILES,
    )
    if actual_payload_size != manifest["payload"]["size"]:
        raise IntegrityError("payload size mismatch (truncated or padded)")
    return manifest


def unpack(
    blob: bytes,
    verify_only: bool = False,
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
    max_manifest_size: int = MAX_MANIFEST_SIZE,
) -> Optional[bytes]:
    if not isinstance(verify_only, bool):
        raise ValueError("verify_only must be a bool")
    view = _bytes_view(blob, "blob")
    manifest = read_manifest(
        view,
        max_original_size=max_original_size,
        max_payload_size=max_payload_size,
        max_manifest_size=max_manifest_size,
    )
    manifest_length = struct.unpack(">I", bytes(view[4:8]))[0]
    payload = bytes(view[8 + manifest_length :])
    payload_info = manifest["payload"]
    original_info = manifest["original"]
    if len(payload) != payload_info["size"]:
        raise IntegrityError("payload size mismatch (truncated or padded)")
    if not _same_digest(_sha256_hex(payload), payload_info["sha256"]):
        raise IntegrityError("payload hash mismatch: container damaged in transit/storage")

    model_name = manifest["profile"]["model"]["model"]
    try:
        data = decode_bytes(payload, original_info["size"], _model(model_name))
    except CoderError as exc:
        raise DesyncError(f"decoder failed: {exc}") from exc
    if not _same_digest(_sha256_hex(data), original_info["sha256"]):
        raise DesyncError(
            "decoded output hash mismatch: decoder desync (nondeterministic model?)"
        )
    return None if verify_only else data


def _read_exact(stream: Any, size: int, label: str) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        try:
            chunk = stream.read(size - len(chunks))
        except (OSError, TypeError, ValueError) as exc:
            raise ContainerError(f"failed reading {label}: {exc}") from exc
        if not chunk:
            raise ContainerError(f"truncated {label}")
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise ContainerError(f"binary stream returned non-bytes data for {label}")
        chunks.extend(bytes(chunk))
    return bytes(chunks)


def _file_frame(
    stream: Any,
    *,
    max_original_size: Optional[int],
    max_payload_size: Optional[int],
    max_manifest_size: int,
) -> _Frame:
    original_limit = _resolve_limit(
        max_original_size, DEFAULT_MAX_ORIGINAL_SIZE, "max_original_size"
    )
    payload_limit = _resolve_limit(
        max_payload_size, DEFAULT_MAX_PAYLOAD_SIZE, "max_payload_size"
    )
    manifest_limit = _resolve_limit(max_manifest_size, MAX_MANIFEST_SIZE, "max_manifest_size")

    header = _read_exact(stream, 8, "container header")
    if header[:4] != MAGIC:
        raise ContainerError("not a Lockstep container (bad magic)")
    manifest_length = struct.unpack(">I", header[4:8])[0]
    if manifest_length > manifest_limit:
        raise ManifestResourceLimitError(
            f"manifest length {manifest_length} exceeds max_manifest_size {manifest_limit}"
        )
    manifest_bytes = _read_exact(stream, manifest_length, "manifest")
    parsed = _parse_manifest_bytes(manifest_bytes)
    manifest = validate_manifest(
        parsed,
        max_original_size=original_limit,
        max_payload_size=payload_limit,
        known_models=MODEL_REGISTRY,
        expected_model_profiles=MODEL_PROFILES,
    )
    payload_offset = 8 + manifest_length
    try:
        total_size = os.fstat(stream.fileno()).st_size
    except (AttributeError, OSError) as exc:
        raise ContainerError(f"container file size is unavailable: {exc}") from exc
    actual_payload_size = total_size - payload_offset
    if actual_payload_size < 0:
        raise ContainerError("truncated manifest")
    if actual_payload_size > payload_limit:
        raise ResourceLimitError(
            f"actual payload size {actual_payload_size} exceeds max_payload_size {payload_limit}"
        )
    declared_payload_size = manifest["payload"]["size"]
    if actual_payload_size != declared_payload_size:
        raise IntegrityError("payload size mismatch (truncated or padded)")
    return _Frame(
        manifest=manifest,
        manifest_length=manifest_length,
        payload_offset=payload_offset,
        payload_size=actual_payload_size,
        total_size=total_size,
        prefix_sha256=_sha256_hex(header + manifest_bytes),
    )


def read_manifest_file(
    src_path: str,
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
    max_manifest_size: int = MAX_MANIFEST_SIZE,
) -> dict:
    with open(src_path, "rb") as stream:
        frame = _file_frame(
            stream,
            max_original_size=max_original_size,
            max_payload_size=max_payload_size,
            max_manifest_size=max_manifest_size,
        )
    return frame.manifest


class _DigestingReader:
    def __init__(self, raw: Any, max_bytes: int) -> None:
        self.raw = raw
        self.max_bytes = max_bytes
        self.count = 0
        self.hasher = hashlib.sha256()

    def read(self, size: int) -> bytes:
        chunk = self.raw.read(size)
        if chunk in (b"", None):
            return b""
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise ContainerError("binary input returned non-bytes data")
        data = bytes(chunk)
        self.count += len(data)
        if self.count > self.max_bytes:
            raise ResourceLimitError(
                f"input size exceeds max_original_size {self.max_bytes}"
            )
        self.hasher.update(data)
        return data

    @property
    def digest(self) -> str:
        return self.hasher.hexdigest()


class _DigestingWriter:
    def __init__(self, raw: Optional[Any], max_bytes: Optional[int] = None) -> None:
        self.raw = raw
        self.max_bytes = max_bytes
        self.count = 0
        self.hasher = hashlib.sha256()

    def write(self, data: bytes) -> int:
        payload = bytes(data)
        next_count = self.count + len(payload)
        if self.max_bytes is not None and next_count > self.max_bytes:
            raise ResourceLimitError(
                f"stream output exceeds max_payload_size {self.max_bytes}"
            )
        if self.raw is not None:
            offset = 0
            while offset < len(payload):
                try:
                    wrote = self.raw.write(payload[offset:])
                except (OSError, TypeError, ValueError) as exc:
                    raise ContainerError(f"failed writing stream output: {exc}") from exc
                remaining = len(payload) - offset
                if (
                    not isinstance(wrote, int)
                    or isinstance(wrote, bool)
                    or wrote <= 0
                    or wrote > remaining
                ):
                    raise ContainerError("binary output reported an invalid write count")
                offset += wrote
        self.hasher.update(payload)
        self.count = next_count
        return len(payload)

    @property
    def digest(self) -> str:
        return self.hasher.hexdigest()


class _BoundedDigestingReader:
    """Read and hash exactly one physical payload, never bytes beyond it."""

    def __init__(self, raw: Any, size: int) -> None:
        self.raw = raw
        self.remaining = size
        self.hasher = hashlib.sha256()

    def read(self, size: int) -> bytes:
        if self.remaining == 0:
            return b""
        if not isinstance(size, int) or isinstance(size, bool):
            raise ContainerError("binary input read size must be an integer")
        request = self.remaining if size < 0 else min(size, self.remaining)
        if request == 0:
            return b""
        try:
            chunk = self.raw.read(request)
        except (OSError, TypeError, ValueError) as exc:
            raise ContainerError(f"failed reading payload: {exc}") from exc
        if not chunk:
            raise IntegrityError("payload truncated during decode")
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise ContainerError("binary input returned non-bytes payload data")
        data = bytes(chunk)
        if len(data) > request:
            raise ContainerError("binary input returned more payload bytes than requested")
        self.remaining -= len(data)
        self.hasher.update(data)
        return data

    def finish_digest(self) -> str:
        while self.remaining:
            self.read(min(_IO_CHUNK, self.remaining))
        return self.hasher.hexdigest()


def _hash_exact(stream: Any, size: int, label: str = "payload") -> str:
    reader = _BoundedDigestingReader(stream, size)
    try:
        return reader.finish_digest()
    except IntegrityError as exc:
        raise IntegrityError(f"{label} truncated while hashing") from exc


def _write_all(stream: Any, data: bytes, label: str) -> None:
    offset = 0
    while offset < len(data):
        try:
            wrote = stream.write(data[offset:])
        except (OSError, TypeError, ValueError) as exc:
            raise ContainerError(f"failed writing {label}: {exc}") from exc
        remaining = len(data) - offset
        if (
            not isinstance(wrote, int)
            or isinstance(wrote, bool)
            or wrote <= 0
            or wrote > remaining
        ):
            raise ContainerError(f"binary output reported an invalid write count for {label}")
        offset += wrote


def _temp_output(destination: Path) -> tuple[Any, str]:
    parent = destination.parent if str(destination.parent) else Path(".")
    fd, path = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(parent)
    )
    return os.fdopen(fd, "w+b"), path


def _commit_temp(stream: Any, path: str, destination: Path) -> None:
    stream.flush()
    os.fsync(stream.fileno())
    stream.close()
    os.replace(path, destination)


def _remove_temp(stream: Optional[Any], path: Optional[str]) -> None:
    if stream is not None and not stream.closed:
        stream.close()
    if path:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def pack_file(
    src_path: str,
    dst_path: str,
    model_name: str = "adaptive-order1",
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
) -> dict:
    original_limit = _resolve_limit(
        max_original_size, DEFAULT_MAX_ORIGINAL_SIZE, "max_original_size"
    )
    payload_limit = _resolve_limit(
        max_payload_size, DEFAULT_MAX_PAYLOAD_SIZE, "max_payload_size"
    )
    source_path = Path(src_path)
    destination = Path(dst_path)
    try:
        declared_size = source_path.stat().st_size
    except OSError:
        declared_size = None
    if declared_size is not None and declared_size > original_limit:
        raise ResourceLimitError(
            f"input size {declared_size} exceeds max_original_size {original_limit}"
        )

    model = _model(model_name)
    profile = model.profile_fields()
    parent = destination.parent if str(destination.parent) else Path(".")
    payload_file = tempfile.TemporaryFile(mode="w+b", dir=str(parent))
    output_stream = None
    output_temp = None
    try:
        with open(source_path, "rb") as source:
            digesting_source = _DigestingReader(source, original_limit)
            digesting_payload = _DigestingWriter(payload_file, payload_limit)
            try:
                stats = encode_stream(digesting_source, digesting_payload, model)
            except CoderError as exc:
                raise ContainerError(f"encode failed: {exc}") from exc
        if stats.input_bytes != digesting_source.count:
            raise ContainerError("stream encoder input accounting mismatch")
        if stats.payload_bytes != digesting_payload.count:
            raise ContainerError("stream encoder payload accounting mismatch")

        manifest = _manifest_for(
            digesting_source.count,
            digesting_source.digest,
            digesting_payload.count,
            digesting_payload.digest,
            profile,
        )
        manifest_bytes = _canonical_json(manifest)
        if len(manifest_bytes) > MAX_MANIFEST_SIZE:
            raise ResourceLimitError("generated manifest exceeds MAX_MANIFEST_SIZE")

        payload_file.flush()
        payload_file.seek(0)
        output_stream, output_temp = _temp_output(destination)
        _write_all(output_stream, MAGIC, "container magic")
        _write_all(
            output_stream, struct.pack(">I", len(manifest_bytes)), "manifest length"
        )
        _write_all(output_stream, manifest_bytes, "manifest")
        while True:
            chunk = payload_file.read(_IO_CHUNK)
            if not chunk:
                break
            _write_all(output_stream, chunk, "payload")
        out_bytes = 8 + len(manifest_bytes) + digesting_payload.count
        _commit_temp(output_stream, output_temp, destination)
        output_stream = None
        output_temp = None
    finally:
        payload_file.close()
        _remove_temp(output_stream, output_temp)

    return {
        "in_bytes": digesting_source.count,
        "out_bytes": out_bytes,
        "payload_bytes": digesting_payload.count,
        "ratio": (digesting_source.count / out_bytes) if out_bytes else 0.0,
        "model": model_name,
    }


def _decode_file(
    src_path: str,
    dst_path: Optional[str],
    *,
    max_original_size: Optional[int],
    max_payload_size: Optional[int],
    max_manifest_size: int,
) -> dict:
    destination = Path(dst_path) if dst_path is not None else None
    output_stream = None
    output_temp = None
    try:
        with open(src_path, "rb") as source:
            frame = _file_frame(
                source,
                max_original_size=max_original_size,
                max_payload_size=max_payload_size,
                max_manifest_size=max_manifest_size,
            )
            source.seek(frame.payload_offset)
            payload_digest = _hash_exact(source, frame.payload_size)
            if not _same_digest(payload_digest, frame.manifest["payload"]["sha256"]):
                raise IntegrityError(
                    "payload hash mismatch: container damaged in transit/storage"
                )

            if destination is not None:
                output_stream, output_temp = _temp_output(destination)
            digesting_output = _DigestingWriter(output_stream)
            source.seek(frame.payload_offset)
            current_payload = _BoundedDigestingReader(source, frame.payload_size)
            model_name = frame.manifest["profile"]["model"]["model"]
            decode_error = None
            written = None
            try:
                written = decode_stream(
                    current_payload,
                    frame.manifest["original"]["size"],
                    _model(model_name),
                    digesting_output,
                )
            except CoderError as exc:
                decode_error = exc

            current_payload_digest = current_payload.finish_digest()
            if not _same_digest(
                current_payload_digest, frame.manifest["payload"]["sha256"]
            ):
                raise IntegrityError("payload changed while the archive was being decoded")

            source.seek(0)
            current_prefix_digest = _hash_exact(
                source, frame.payload_offset, "container header or manifest"
            )
            if not _same_digest(current_prefix_digest, frame.prefix_sha256):
                raise IntegrityError(
                    "container header or manifest changed while the archive was being decoded"
                )
            try:
                current_size = os.fstat(source.fileno()).st_size
            except (AttributeError, OSError) as exc:
                raise ContainerError(f"container file size is unavailable: {exc}") from exc
            if current_size != frame.total_size:
                raise IntegrityError("container size changed while the archive was being decoded")

            if decode_error is not None:
                raise DesyncError(f"decoder failed: {decode_error}") from decode_error
            if written != digesting_output.count:
                raise DesyncError("stream decoder output accounting mismatch")
            if not _same_digest(
                digesting_output.digest, frame.manifest["original"]["sha256"]
            ):
                raise DesyncError(
                    "decoded output hash mismatch: decoder desync (nondeterministic model?)"
                )

        if destination is not None:
            _commit_temp(output_stream, output_temp, destination)
            output_stream = None
            output_temp = None
        return {
            "in_bytes": frame.total_size,
            "payload_bytes": frame.payload_size,
            "out_bytes": digesting_output.count,
            "model": frame.manifest["profile"]["model"]["model"],
        }
    finally:
        _remove_temp(output_stream, output_temp)


def unpack_file(
    src_path: str,
    dst_path: str,
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
    max_manifest_size: int = MAX_MANIFEST_SIZE,
) -> dict:
    return _decode_file(
        src_path,
        dst_path,
        max_original_size=max_original_size,
        max_payload_size=max_payload_size,
        max_manifest_size=max_manifest_size,
    )


def verify_file(
    src_path: str,
    *,
    max_original_size: Optional[int] = None,
    max_payload_size: Optional[int] = None,
    max_manifest_size: int = MAX_MANIFEST_SIZE,
) -> dict:
    return _decode_file(
        src_path,
        None,
        max_original_size=max_original_size,
        max_payload_size=max_payload_size,
        max_manifest_size=max_manifest_size,
    )

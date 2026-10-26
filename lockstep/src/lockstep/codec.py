"""Model-agnostic lossless codec for bytes and binary streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import CoderError
from .models import PredictiveModel
from .rac import RangeDecoder, RangeEncoder

DEFAULT_STREAM_CHUNK = 64 * 1024


@dataclass(frozen=True)
class EncodeStreamStats:
    input_bytes: int
    payload_bytes: int


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_chunk_size(chunk_size: int) -> None:
    if not _is_nonnegative_int(chunk_size) or chunk_size == 0:
        raise CoderError("chunk_size must be a positive integer")


def _validate_sink(sink: Any) -> None:
    if not callable(getattr(sink, "write", None)):
        raise CoderError("output sink must provide write(bytes)")


def _write_all(sink: Any, data: bytes) -> None:
    _validate_sink(sink)
    offset = 0
    while offset < len(data):
        try:
            wrote = sink.write(data[offset:])
        except (OSError, TypeError, ValueError) as exc:
            raise CoderError(f"failed writing decoded stream: {exc}") from exc
        remaining = len(data) - offset
        if (
            not isinstance(wrote, int)
            or isinstance(wrote, bool)
            or wrote <= 0
            or wrote > remaining
        ):
            raise CoderError("output sink reported an invalid write count")
        offset += wrote


def _encode_chunk(enc: RangeEncoder, data: bytes, model: PredictiveModel) -> None:
    for symbol in data:
        cdf = model.next_cdf()
        c_lo, c_hi, total = cdf.interval(symbol)
        enc.encode(c_lo, c_hi, total)
        model.update(symbol)


def encode_bytes(data: bytes, model: PredictiveModel) -> bytes:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise CoderError("data must be bytes-like")
    try:
        view = memoryview(data).cast("B")
    except (TypeError, ValueError) as exc:
        raise CoderError("data must be a one-dimensional byte buffer") from exc
    enc = RangeEncoder()
    _encode_chunk(enc, bytes(view), model)
    return enc.finish()


def encode_stream(
    source: Any,
    sink: Any,
    model: PredictiveModel,
    *,
    chunk_size: int = DEFAULT_STREAM_CHUNK,
) -> EncodeStreamStats:
    """Encode a binary source incrementally into ``sink``.

    Streaming output is bit-identical to :func:`encode_bytes` for the same
    byte sequence and fresh model state.
    """
    _validate_chunk_size(chunk_size)
    if not callable(getattr(source, "read", None)):
        raise CoderError("input source must provide read(size)")
    enc = RangeEncoder(sink)
    input_bytes = 0
    while True:
        try:
            chunk = source.read(chunk_size)
        except (OSError, TypeError, ValueError) as exc:
            raise CoderError(f"failed reading input stream: {exc}") from exc
        if chunk in (b"", None):
            break
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise CoderError("binary source read() returned non-bytes data")
        try:
            data = bytes(memoryview(chunk).cast("B"))
        except (TypeError, ValueError) as exc:
            raise CoderError("binary source returned an invalid byte buffer") from exc
        if not data:
            break
        input_bytes += len(data)
        _encode_chunk(enc, data, model)
    enc.finish()
    return EncodeStreamStats(input_bytes=input_bytes, payload_bytes=enc.output_size)


def decode_bytes(payload: bytes, n_bytes: int, model: PredictiveModel) -> bytes:
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise CoderError("payload must be bytes-like")
    if not _is_nonnegative_int(n_bytes):
        raise CoderError("n_bytes must be a non-negative integer (not bool)")
    dec = RangeDecoder(payload)
    out = bytearray()
    for _ in range(n_bytes):
        cdf = model.next_cdf()
        target = dec.decode_target(cdf.total)
        symbol = cdf.find(target)
        c_lo, c_hi, total = cdf.interval(symbol)
        dec.update(c_lo, c_hi, total)
        model.update(symbol)
        out.append(symbol)
    return bytes(out)


def decode_stream(
    source: Any,
    n_bytes: int,
    model: PredictiveModel,
    sink: Any,
    *,
    chunk_size: int = DEFAULT_STREAM_CHUNK,
) -> int:
    """Decode exactly ``n_bytes`` from a binary source into ``sink``."""
    if not _is_nonnegative_int(n_bytes):
        raise CoderError("n_bytes must be a non-negative integer (not bool)")
    _validate_chunk_size(chunk_size)
    _validate_sink(sink)
    dec = RangeDecoder(source)
    out = bytearray()
    written = 0
    for _ in range(n_bytes):
        cdf = model.next_cdf()
        target = dec.decode_target(cdf.total)
        symbol = cdf.find(target)
        c_lo, c_hi, total = cdf.interval(symbol)
        dec.update(c_lo, c_hi, total)
        model.update(symbol)
        out.append(symbol)
        if len(out) >= chunk_size:
            _write_all(sink, bytes(out))
            written += len(out)
            out.clear()
    if out:
        _write_all(sink, bytes(out))
        written += len(out)
    return written


def roundtrip_ok(data: bytes, make_model) -> bool:
    payload = encode_bytes(data, make_model())
    try:
        back = decode_bytes(payload, len(data), make_model())
    except CoderError:
        return False
    return back == data

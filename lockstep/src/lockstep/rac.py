"""Pure-integer arithmetic coder (Witten–Neal–Cleary style).

Determinism contract
--------------------
Every arithmetic operation in this module is performed on exact Python
integers. Public inputs are checked strictly: floats and ``bool`` values are
rejected rather than being silently coerced into the trust base.

``RangeEncoder`` can optionally write bytes incrementally to a binary sink.
The default in-memory mode and streaming mode execute the same coder state
machine and therefore emit identical payload bytes.
"""

from __future__ import annotations

from typing import Any, Optional

from .errors import CoderError

CODE_BITS = 32
TOP = 1 << CODE_BITS
MASK = TOP - 1
HALF = TOP >> 1
QUARTER = TOP >> 2
THREE_QUARTERS = HALF + QUARTER

PROB_BITS_MAX = 16
TOTAL_MAX = 1 << PROB_BITS_MAX

_IO_CHUNK = 64 * 1024


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class _BitWriter:
    __slots__ = ("_buf", "_acc", "_nbits", "_sink", "_written")

    def __init__(self, sink: Optional[Any] = None) -> None:
        if sink is not None and not callable(getattr(sink, "write", None)):
            raise CoderError("stream sink must provide write(bytes)")
        self._buf = bytearray()
        self._acc = 0
        self._nbits = 0
        self._sink = sink
        self._written = 0

    def _flush(self) -> None:
        if self._sink is None or not self._buf:
            return
        data = bytes(self._buf)
        offset = 0
        while offset < len(data):
            try:
                wrote = self._sink.write(data[offset:])
            except (OSError, TypeError, ValueError) as exc:
                raise CoderError(f"failed writing coded stream: {exc}") from exc
            remaining = len(data) - offset
            if not _is_int(wrote) or wrote <= 0 or wrote > remaining:
                raise CoderError("stream sink reported an invalid write count")
            offset += wrote
        self._written += len(data)
        self._buf.clear()

    def _append_byte(self, value: int) -> None:
        self._buf.append(value)
        if self._sink is not None and len(self._buf) >= _IO_CHUNK:
            self._flush()

    def write(self, bit: int) -> None:
        if not _is_int(bit) or bit not in (0, 1):
            raise CoderError("bit must be integer 0 or 1")
        self._acc = (self._acc << 1) | bit
        self._nbits += 1
        if self._nbits == 8:
            self._append_byte(self._acc)
            self._acc = 0
            self._nbits = 0

    def getvalue(self) -> bytes:
        if self._nbits:
            self._append_byte(self._acc << (8 - self._nbits))
            self._acc = 0
            self._nbits = 0
        if self._sink is not None:
            self._flush()
            return b""
        return bytes(self._buf)

    @property
    def bytes_written(self) -> int:
        return self._written + len(self._buf)


class _BitReader:
    """Read bits MSB-first from bytes or a binary stream.

    Zero-padding after physical end-of-stream is part of profile ``lsp0``.
    Streaming reads are buffered so decoding does not perform one Python I/O
    call per payload byte.
    """

    __slots__ = (
        "_data", "_pos", "_source", "_chunk", "_chunk_pos", "_acc", "_nbits"
    )

    def __init__(self, source: Any) -> None:
        self._data = None
        self._pos = 0
        self._source = None
        self._chunk = memoryview(b"")
        self._chunk_pos = 0
        self._acc = 0
        self._nbits = 0

        if isinstance(source, (bytes, bytearray, memoryview)):
            try:
                self._data = memoryview(source).cast("B")
            except (TypeError, ValueError) as exc:
                raise CoderError("payload must be a one-dimensional byte buffer") from exc
        elif callable(getattr(source, "read", None)):
            self._source = source
        else:
            raise CoderError("payload must be bytes-like or a binary stream")

    def _next_byte(self) -> Optional[int]:
        if self._data is not None:
            if self._pos >= len(self._data):
                return None
            value = self._data[self._pos]
            self._pos += 1
            return int(value)

        if self._chunk_pos >= len(self._chunk):
            try:
                chunk = self._source.read(_IO_CHUNK)
            except (OSError, TypeError, ValueError) as exc:
                raise CoderError(f"failed reading coded stream: {exc}") from exc
            if chunk in (b"", None):
                return None
            if not isinstance(chunk, (bytes, bytearray, memoryview)):
                raise CoderError("binary stream read() returned non-bytes data")
            try:
                self._chunk = memoryview(chunk).cast("B")
            except (TypeError, ValueError) as exc:
                raise CoderError("binary stream returned an invalid byte buffer") from exc
            self._chunk_pos = 0
            if len(self._chunk) == 0:
                return None

        value = int(self._chunk[self._chunk_pos])
        self._chunk_pos += 1
        return value

    def read(self) -> int:
        if self._nbits == 0:
            value = self._next_byte()
            if value is None:
                return 0
            self._acc = value
            self._nbits = 8
        self._nbits -= 1
        return (self._acc >> self._nbits) & 1


def _check_interval(c_lo: int, c_hi: int, total: int) -> None:
    if not (_is_int(c_lo) and _is_int(c_hi) and _is_int(total)):
        raise CoderError("cumulative interval and total must be integers (not bool)")
    if not (0 < total <= TOTAL_MAX):
        raise CoderError(f"total must be in (0, {TOTAL_MAX}], got {total}")
    if not (0 <= c_lo < c_hi <= total):
        raise CoderError(f"invalid cumulative interval [{c_lo}, {c_hi}) of {total}")


class RangeEncoder:
    """Arithmetic encoder.

    With no ``sink`` the encoded payload is returned by :meth:`finish`. With a
    binary ``sink``, bytes are emitted incrementally, :meth:`finish` returns
    ``b\"\"``, and :attr:`output_size` reports the number of payload bytes.
    """

    def __init__(self, sink: Optional[Any] = None) -> None:
        self._low = 0
        self._high = MASK
        self._pending = 0
        self._out = _BitWriter(sink)
        self._finished = False

    def _emit(self, bit: int) -> None:
        self._out.write(bit)
        inv = bit ^ 1
        while self._pending:
            self._out.write(inv)
            self._pending -= 1

    def encode(self, c_lo: int, c_hi: int, total: int) -> None:
        if self._finished:
            raise CoderError("encode() after finish()")
        _check_interval(c_lo, c_hi, total)
        span = self._high - self._low + 1
        # Order matters: compute high before mutating low.
        self._high = self._low + (span * c_hi) // total - 1
        self._low = self._low + (span * c_lo) // total
        while True:
            if self._high < HALF:
                self._emit(0)
            elif self._low >= HALF:
                self._emit(1)
                self._low -= HALF
                self._high -= HALF
            elif self._low >= QUARTER and self._high < THREE_QUARTERS:
                self._pending += 1
                self._low -= QUARTER
                self._high -= QUARTER
            else:
                break
            self._low <<= 1
            self._high = (self._high << 1) | 1

    def finish(self) -> bytes:
        if self._finished:
            raise CoderError("finish() called twice")
        self._finished = True
        self._pending += 1
        if self._low < QUARTER:
            self._emit(0)
        else:
            self._emit(1)
        return self._out.getvalue()

    @property
    def output_size(self) -> int:
        return self._out.bytes_written


class RangeDecoder:
    """Arithmetic decoder mirroring :class:`RangeEncoder` bit-for-bit."""

    def __init__(self, source: Any) -> None:
        self._in = _BitReader(source)
        self._low = 0
        self._high = MASK
        self._value = 0
        for _ in range(CODE_BITS):
            self._value = (self._value << 1) | self._in.read()

    def decode_target(self, total: int) -> int:
        if not _is_int(total):
            raise CoderError("total must be an integer (not bool)")
        if not (0 < total <= TOTAL_MAX):
            raise CoderError(f"total must be in (0, {TOTAL_MAX}], got {total}")
        span = self._high - self._low + 1
        target = ((self._value - self._low + 1) * total - 1) // span
        if not (0 <= target < total):
            raise CoderError("decoder desync: target outside [0, total)")
        return target

    def update(self, c_lo: int, c_hi: int, total: int) -> None:
        _check_interval(c_lo, c_hi, total)
        span = self._high - self._low + 1
        self._high = self._low + (span * c_hi) // total - 1
        self._low = self._low + (span * c_lo) // total
        while True:
            if self._high < HALF:
                pass
            elif self._low >= HALF:
                self._value -= HALF
                self._low -= HALF
                self._high -= HALF
            elif self._low >= QUARTER and self._high < THREE_QUARTERS:
                self._value -= QUARTER
                self._low -= QUARTER
                self._high -= QUARTER
            else:
                break
            self._low <<= 1
            self._high = (self._high << 1) | 1
            self._value = (self._value << 1) | self._in.read()

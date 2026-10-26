"""Specified deterministic random bytes for tests and conformance vectors."""

from __future__ import annotations

import hashlib
import struct
from typing import Any

from .errors import CoderError


def _nonnegative_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CoderError(f"{name} must be a non-negative integer (not bool)")
    return value


def deterministic_bytes(seed: str, n: int) -> bytes:
    if not isinstance(seed, str):
        raise CoderError("seed must be a string")
    _nonnegative_int(n, "n")
    out = bytearray()
    index = 0
    try:
        encoded_seed = seed.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CoderError("seed must contain valid Unicode scalar values") from exc
    while len(out) < n:
        out += hashlib.sha256(encoded_seed + struct.pack(">Q", index)).digest()
        index += 1
    return bytes(out[:n])


def deterministic_ints(seed: str, n: int, lo: int, hi: int) -> list[int]:
    """Return ``n`` deterministic integers in the inclusive range ``[lo, hi]``."""
    _nonnegative_int(n, "n")
    if not isinstance(lo, int) or isinstance(lo, bool):
        raise CoderError("lo must be an integer (not bool)")
    if not isinstance(hi, int) or isinstance(hi, bool):
        raise CoderError("hi must be an integer (not bool)")
    if hi < lo:
        raise CoderError("hi must be >= lo")
    span = hi - lo + 1
    raw = deterministic_bytes(seed, n * 4)
    return [
        lo + (int.from_bytes(raw[4 * index : 4 * index + 4], "big") % span)
        for index in range(n)
    ]

"""Exact bit I/O and Elias-gamma coding.

Deliberately boring: every byte of an archive must be reproducible and every
decode exactly invertible. Elias-gamma is the v0 universal integer code
(encodes n >= 1 in 2*floor(log2 n) + 1 bits) — simple, stateless, and
sufficient to make the format real. An arithmetic/range coder is a marked
upgrade path (see BLUEPRINT), gated on the mismatch problem PMATIC
formalizes: adaptive coders amplify tiny model drift into cascading decode
failure, which is exactly the failure mode the determinism runtime exists to
eliminate.
"""

from __future__ import annotations


class BitWriter:
    def __init__(self):
        self._bits: list[int] = []

    def write_bit(self, b: int) -> None:
        self._bits.append(1 if b else 0)

    def write_uint(self, value: int, width: int) -> None:
        """MSB-first fixed-width unsigned integer."""
        if value < 0 or value >= (1 << width):
            raise ValueError(f"{value} does not fit in {width} bits")
        for i in range(width - 1, -1, -1):
            self._bits.append((value >> i) & 1)

    @property
    def n_bits(self) -> int:
        return len(self._bits)

    def to_bytes(self) -> bytes:
        out = bytearray()
        acc, n = 0, 0
        for b in self._bits:
            acc = (acc << 1) | b
            n += 1
            if n == 8:
                out.append(acc)
                acc, n = 0, 0
        if n:
            out.append(acc << (8 - n))  # zero-padded final byte
        return bytes(out)


class BitReader:
    def __init__(self, data: bytes, n_bits: int):
        if n_bits > 8 * len(data):
            raise ValueError("n_bits exceeds available data")
        self._data = data
        self._n_bits = n_bits
        self._pos = 0

    def read_bit(self) -> int:
        if self._pos >= self._n_bits:
            raise ValueError("bitstream exhausted (truncated or corrupt archive)")
        byte = self._data[self._pos >> 3]
        bit = (byte >> (7 - (self._pos & 7))) & 1
        self._pos += 1
        return bit

    def read_uint(self, width: int) -> int:
        v = 0
        for _ in range(width):
            v = (v << 1) | self.read_bit()
        return v

    @property
    def exhausted(self) -> bool:
        return self._pos >= self._n_bits


def gamma_encode(w: BitWriter, n: int) -> None:
    """Elias gamma for n >= 1: (b-1) zero bits, then the b bits of n."""
    if n < 1:
        raise ValueError("Elias gamma encodes integers >= 1")
    b = n.bit_length()
    for _ in range(b - 1):
        w.write_bit(0)
    w.write_uint(n, b)


def gamma_decode(r: BitReader) -> int:
    z = 0
    while r.read_bit() == 0:
        z += 1
        if z > 63:
            raise ValueError("malformed gamma code (corrupt archive)")
    n = 1
    for _ in range(z):
        n = (n << 1) | r.read_bit()
    return n

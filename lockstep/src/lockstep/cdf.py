"""Cumulative distribution tables and deterministic quantizers."""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Any, List, Sequence

from .errors import CoderError
from .rac import TOTAL_MAX

DEFAULT_TOTAL = 1 << 15


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class Cdf:
    """Immutable cumulative table over symbols ``0..V-1``."""

    __slots__ = ("_cum", "_total")

    def __init__(self, cum: Sequence[int]) -> None:
        try:
            values = tuple(cum)
        except TypeError as exc:
            raise CoderError("cum must be an iterable of integers") from exc
        if len(values) < 2 or values[0] != 0:
            raise CoderError("cum must start at 0 and cover >=1 symbol")
        if any(not _is_int(value) for value in values):
            raise CoderError("cumulative values must be integers (not bool)")
        for a, b in zip(values, values[1:]):
            if b <= a:
                raise CoderError("every symbol must have frequency >= 1")
        if values[-1] > TOTAL_MAX:
            raise CoderError(f"total {values[-1]} exceeds TOTAL_MAX {TOTAL_MAX}")
        object.__setattr__(self, "_cum", values)
        object.__setattr__(self, "_total", values[-1])

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Cdf instances are immutable")

    @property
    def cum(self) -> tuple[int, ...]:
        return self._cum

    @property
    def total(self) -> int:
        return self._total

    @classmethod
    def from_freqs(cls, freqs: Sequence[int]) -> "Cdf":
        try:
            values = tuple(freqs)
        except TypeError as exc:
            raise CoderError("frequencies must be an iterable of integers") from exc
        if not values:
            raise CoderError("at least one frequency is required")
        if any(not _is_int(freq) for freq in values):
            raise CoderError("frequencies must be integers (not bool)")
        cum = [0]
        acc = 0
        for freq in values:
            if freq < 1:
                raise CoderError("frequencies must be >= 1")
            acc += freq
            cum.append(acc)
        return cls(cum)

    def interval(self, symbol: int) -> tuple[int, int, int]:
        if not _is_int(symbol):
            raise CoderError("symbol must be an integer (not bool)")
        if not (0 <= symbol < self.num_symbols):
            raise CoderError(f"symbol {symbol} outside alphabet [0, {self.num_symbols})")
        return self.cum[symbol], self.cum[symbol + 1], self.total

    def find(self, target: int) -> int:
        """Map a decoder target in ``[0, total)`` to its symbol."""
        if not _is_int(target):
            raise CoderError("target must be an integer (not bool)")
        if not (0 <= target < self.total):
            raise CoderError(f"target {target} outside [0, {self.total})")
        return bisect_right(self.cum, target) - 1

    @property
    def num_symbols(self) -> int:
        return len(self.cum) - 1


def quantize_weights(weights: Sequence[int], total: int = DEFAULT_TOTAL) -> List[int]:
    """Integer weights to frequencies summing to ``total``, each at least 1."""
    try:
        values = tuple(weights)
    except TypeError as exc:
        raise CoderError("weights must be an iterable of integers") from exc
    n = len(values)
    if n == 0:
        raise CoderError("no symbols")
    if not _is_int(total):
        raise CoderError("total must be an integer (not bool)")
    if total < n or total > TOTAL_MAX:
        raise CoderError(f"total must be in [{n}, {TOTAL_MAX}]")
    if any(not _is_int(weight) for weight in values):
        raise CoderError("weights must be integers (not bool)")
    if any(weight < 0 for weight in values):
        raise CoderError("weights must be non-negative")
    wsum = sum(values)
    if wsum == 0:
        values = (1,) * n
        wsum = n
    budget = total - n
    base = [(weight * budget) // wsum for weight in values]
    remainders = [(weight * budget) % wsum for weight in values]
    leftover = budget - sum(base)
    order = sorted(range(n), key=lambda index: (-remainders[index], index))
    for index in order[:leftover]:
        base[index] += 1
    return [value + 1 for value in base]


def quantize_probs(probs: Sequence[float], total: int = DEFAULT_TOTAL) -> List[int]:
    """Float probabilities to integer frequencies. Research surface only.

    The apportionment rule is fixed, but producing identical floating-point
    inputs remains the caller's responsibility. Non-finite values are rejected
    explicitly so malformed inputs fail as :class:`CoderError`.
    """
    try:
        raw_values = tuple(probs)
    except TypeError as exc:
        raise CoderError("probabilities must be an iterable of numbers") from exc
    n = len(raw_values)
    if n == 0:
        raise CoderError("no symbols")
    if not _is_int(total):
        raise CoderError("total must be an integer (not bool)")
    if total < n or total > TOTAL_MAX:
        raise CoderError(f"total must be in [{n}, {TOTAL_MAX}]")

    values = []
    for value in raw_values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CoderError("probabilities must be real numbers (not bool)")
        try:
            converted = float(value)
        except (OverflowError, ValueError) as exc:
            raise CoderError("probabilities must be finite real numbers") from exc
        if not math.isfinite(converted):
            raise CoderError("probabilities must be finite")
        if converted < 0.0:
            raise CoderError("probabilities must be non-negative")
        values.append(converted)

    psum = sum(values)
    if not math.isfinite(psum):
        raise CoderError("probability sum must be finite")
    if psum <= 0.0:
        return [total // n + (1 if index < total % n else 0) for index in range(n)]

    budget = total - n
    scaled = [value / psum * budget for value in values]
    base = [int(value) for value in scaled]
    remainders = [value - floor for value, floor in zip(scaled, base)]
    leftover = budget - sum(base)
    order = sorted(range(n), key=lambda index: (-remainders[index], index))
    for index in order[:leftover]:
        base[index] += 1
    return [value + 1 for value in base]

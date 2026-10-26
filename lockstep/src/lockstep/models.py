"""Predictive models for the reference codec."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Protocol, Sequence

from .cdf import Cdf
from .errors import CoderError

ALPHABET = 256

_ADAPTIVE_PROFILE = MappingProxyType(
    {
        "model": "adaptive-order1",
        "alphabet": ALPHABET,
        "increment": 24,
        "rescale_limit": 1 << 15,
    }
)
_UNIFORM_PROFILE = MappingProxyType(
    {
        "model": "uniform",
        "alphabet": ALPHABET,
    }
)
MODEL_PROFILES = MappingProxyType(
    {
        "adaptive-order1": _ADAPTIVE_PROFILE,
        "uniform": _UNIFORM_PROFILE,
    }
)


def _valid_symbol(symbol: Any) -> bool:
    return isinstance(symbol, int) and not isinstance(symbol, bool) and 0 <= symbol < ALPHABET


class PredictiveModel(Protocol):
    """Both sides call ``next_cdf`` and ``update`` in identical lockstep."""

    def next_cdf(self) -> Cdf: ...
    def update(self, symbol: int) -> None: ...
    def profile_fields(self) -> dict: ...


class StaticModel:
    """Fixed order-0 distribution from exact integer frequencies."""

    def __init__(self, freqs: Sequence[int]) -> None:
        self._cdf = Cdf.from_freqs(freqs)
        if self._cdf.num_symbols != ALPHABET:
            raise CoderError(f"StaticModel needs {ALPHABET} symbols")

    def next_cdf(self) -> Cdf:
        return self._cdf

    def update(self, symbol: int) -> None:
        if not _valid_symbol(symbol):
            raise CoderError(f"symbol {symbol!r} outside alphabet")

    def profile_fields(self) -> dict:
        return {"model": "static-order0", "alphabet": ALPHABET}


class UniformModel(StaticModel):
    def __init__(self) -> None:
        super().__init__([1] * ALPHABET)

    def profile_fields(self) -> dict:
        return dict(MODEL_PROFILES["uniform"])


class AdaptiveByteModel:
    """Order-1 adaptive byte model, entirely integer and deterministic."""

    INCREMENT = MODEL_PROFILES["adaptive-order1"]["increment"]
    RESCALE_LIMIT = MODEL_PROFILES["adaptive-order1"]["rescale_limit"]

    def __init__(self) -> None:
        self._rows = {}
        self._context = 0

    def _row(self, context: int) -> list:
        entry = self._rows.get(context)
        if entry is None:
            entry = [[1] * ALPHABET, ALPHABET]
            self._rows[context] = entry
        return entry

    def next_cdf(self) -> Cdf:
        return Cdf.from_freqs(self._row(self._context)[0])

    def update(self, symbol: int) -> None:
        if not _valid_symbol(symbol):
            raise CoderError(f"symbol {symbol!r} outside alphabet")
        entry = self._row(self._context)
        row, total = entry
        row[symbol] += self.INCREMENT
        total += self.INCREMENT
        if total > self.RESCALE_LIMIT:
            total = 0
            for index in range(ALPHABET):
                row[index] = max(1, (row[index] + 1) >> 1)
                total += row[index]
        entry[1] = total
        self._context = symbol

    def profile_fields(self) -> dict:
        return dict(MODEL_PROFILES["adaptive-order1"])


MODEL_REGISTRY = MappingProxyType(
    {
        "adaptive-order1": AdaptiveByteModel,
        "uniform": UniformModel,
    }
)


def expected_model_profile(name: str) -> dict:
    try:
        return dict(MODEL_PROFILES[name])
    except (KeyError, TypeError) as exc:
        raise CoderError(f"unknown model {name!r} (have: {sorted(MODEL_REGISTRY)})") from exc


def make_model(name: str) -> PredictiveModel:
    if not isinstance(name, str) or name not in MODEL_REGISTRY:
        raise CoderError(f"unknown model {name!r} (have: {sorted(MODEL_REGISTRY)})")
    return MODEL_REGISTRY[name]()

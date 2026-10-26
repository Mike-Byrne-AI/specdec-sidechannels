"""Address-stream sketches.

The observable in this project is never an activation value — it is the SET of
memory slots touched (or, for the shadow variant, the set that WOULD be
touched). A `HashSketch` models a device with `n_units` addressable weight
groups hashed into `n_slots` physical slots; given an activation/importance
vector it reports the slots reached by the top-N most important units.

The same class is used by the synthetic world and by the real shadow-telemetry
hook (`sideband.real.shadow_telemetry`), so collision behavior is identical in
both regimes.
"""

from __future__ import annotations

import numpy as np

from .dists import Array


class HashSketch:
    def __init__(self, n_units: int, n_slots: int, seed: int):
        if n_slots <= 0 or n_units <= 0:
            raise ValueError("n_units and n_slots must be positive")
        self.n_units = n_units
        self.n_slots = n_slots
        gen = np.random.default_rng(seed)
        # Random static hash: unit -> slot. Deterministic given seed.
        self.slot_of_unit = gen.integers(0, n_slots, size=n_units, dtype=np.int64)

    def top_units(self, importance: Array, n: int) -> Array:
        """Indices of the n most important units, |importance| descending.

        Ties break by ascending unit index so results are stable across runs
        and platforms.
        """
        imp = np.abs(np.asarray(importance, dtype=np.float64))
        if imp.shape != (self.n_units,):
            raise ValueError(f"importance must have shape ({self.n_units},)")
        n = min(n, self.n_units)
        order = np.lexsort((np.arange(self.n_units), -imp))
        return order[:n]

    def slots_for(self, importance: Array, n: int) -> Array:
        """Sorted unique slot ids reached by the top-n units. The telemetry."""
        units = self.top_units(importance, n)
        return np.unique(self.slot_of_unit[units])

    def multi_hot(self, slots: Array) -> Array:
        """Feature vector for the sidecar: 1.0 at each accessed slot."""
        v = np.zeros(self.n_slots, dtype=np.float64)
        v[np.asarray(slots, dtype=np.int64)] = 1.0
        return v

    def expected_collision_rate(self) -> float:
        """Fraction of units sharing a slot with at least one other unit."""
        counts = np.bincount(self.slot_of_unit, minlength=self.n_slots)
        colliding = counts[counts > 1].sum()
        return float(colliding) / self.n_units

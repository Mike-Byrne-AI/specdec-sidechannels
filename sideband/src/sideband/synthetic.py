"""Synthetic concept-HMM world.

Purpose: a fully controlled testbed where every quantity the real experiments
need (latent concept, telemetry, cross-bucket rejections, staleness) has a
known ground truth, so the pipeline/analysis code can be validated end to end
on CPU in seconds before any GPU port.

World model
-----------
- A latent concept path c_1..c_T follows a sticky Markov chain: stay with
  prob rho, else jump uniformly to another concept. Expected run length is
  1/(1-rho).
- Vocab = n_concepts blocks of block_size topical tokens, plus n_function
  shared "function" tokens. bucket(token) is the block id, or FUNCTION_BUCKET.
- Target emission given concept c: with prob lambda_function emit a function
  token (Zipf), else a token from block c (Zipf, with a small eps_leak to
  other blocks). The target is a PERFECT observer of the latent concept.
- Draft emission: the draft sees a CORRUPTED concept (true with prob
  draft_alpha, else uniformly another concept, independently per position)
  and emits a temperature-flattened version of the target's table. This
  yields both cross-bucket disagreements (wrong concept) and within-bucket
  disagreements (right concept, wrong token) with tunable rates.
- Telemetry given concept c: an activation vector over n_units where a fixed
  random support set of units_per_concept units per concept is hot (plus
  noise); the observable is HashSketch.slots_for(activation, top_n) — the
  slot SET only, never values.

Regime notes (cite findings from this world with these attached):
- The target is state-observed (no inference-over-history). This isolates the
  steering question from belief tracking.
- Telemetry and the target's own next-token distribution are both functions of
  the SAME latent concept here, so in this world a telemetry sidecar can at
  best MATCH the free-information baseline (steering from the target's last
  verified distribution). Whether real hidden-state sketches carry MORE than
  the last verified p is exactly what the real-model phase must measure
  (OPEN_QUESTIONS OQ-1); this world cannot answer it by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field  # noqa: F401  (field unused since the frozen-dict rewrite; cleanup owed)

import numpy as np

from .dists import Array, normalize, temper, zipf
from .sketch import HashSketch


@dataclass
class WorldConfig:
    # Vocabulary / concepts
    n_concepts: int = 12
    block_size: int = 40
    n_function: int = 80
    zipf_s: float = 1.1
    lambda_function: float = 0.45
    eps_leak: float = 0.02
    # Latent dynamics
    rho: float = 0.92
    # Draft degradation
    draft_alpha: float = 0.70
    draft_temperature: float = 1.6
    # Telemetry
    n_units: int = 4096
    units_per_concept: int = 24
    support_gain: float = 1.0
    support_noise: float = 0.25
    background_noise: float = 0.05
    n_slots: int = 512
    top_n: int = 32
    # Token embeddings (for bucket-recovery tests)
    emb_dim: int = 16
    emb_centroid_scale: float = 3.0
    emb_noise: float = 0.5
    seed: int = 0

    @property
    def vocab_size(self) -> int:
        return self.n_concepts * self.block_size + self.n_function

    @property
    def function_bucket(self) -> int:
        return self.n_concepts


class World:
    def __init__(self, cfg: WorldConfig):
        self.cfg = cfg
        gen = np.random.default_rng(cfg.seed)
        C, B, F, V = cfg.n_concepts, cfg.block_size, cfg.n_function, cfg.vocab_size

        # --- token -> bucket ground truth ---------------------------------
        self.bucket_of_token = np.empty(V, dtype=np.int64)
        for c in range(C):
            self.bucket_of_token[c * B : (c + 1) * B] = c
        self.bucket_of_token[C * B :] = cfg.function_bucket

        # --- target emission table P[c] over V -----------------------------
        block_dist = zipf(B, cfg.zipf_s)
        func_dist = zipf(F, cfg.zipf_s)
        self.P = np.zeros((C, V), dtype=np.float64)
        for c in range(C):
            row = np.zeros(V)
            own = np.zeros(V)
            own[c * B : (c + 1) * B] = block_dist
            leak = np.zeros(V)
            other = np.ones(C * B, dtype=bool)
            other[c * B : (c + 1) * B] = False
            leak[:C * B][other[: C * B]] = 1.0
            leak = leak / max(leak.sum(), 1.0)
            topical = (1.0 - cfg.eps_leak) * own + cfg.eps_leak * leak
            row[: C * B] = (1.0 - cfg.lambda_function) * topical[: C * B]
            row[C * B :] = cfg.lambda_function * func_dist
            self.P[c] = normalize(row)

        # Draft table: temperature-flattened target rows.
        self.Q = np.stack([temper(self.P[c], cfg.draft_temperature) for c in range(C)])

        # --- telemetry -----------------------------------------------------
        self.support = np.stack(
            [gen.choice(cfg.n_units, size=cfg.units_per_concept, replace=False) for _ in range(C)]
        )
        self.sketch = HashSketch(cfg.n_units, cfg.n_slots, seed=cfg.seed + 1)

        # --- token embeddings (for k-means recovery tests) ------------------
        centroids = gen.normal(0.0, cfg.emb_centroid_scale, size=(C + 1, cfg.emb_dim))
        self.embeddings = np.empty((V, cfg.emb_dim))
        for t in range(V):
            self.embeddings[t] = centroids[self.bucket_of_token[t]] + gen.normal(
                0.0, cfg.emb_noise, size=cfg.emb_dim
            )

    # --- latent dynamics ----------------------------------------------------
    def sample_concept_path(self, gen: np.random.Generator, length: int) -> Array:
        C, rho = self.cfg.n_concepts, self.cfg.rho
        path = np.empty(length, dtype=np.int64)
        path[0] = gen.integers(C)
        for t in range(1, length):
            if gen.random() < rho or C == 1:
                path[t] = path[t - 1]
            else:
                # uniform over the other C-1 concepts
                j = gen.integers(C - 1)
                path[t] = j if j < path[t - 1] else j + 1
        return path

    # --- model distributions --------------------------------------------------
    def target_dist(self, concept: int) -> Array:
        return self.P[concept]

    def draft_concept(self, gen: np.random.Generator, concept: int) -> int:
        cfg = self.cfg
        if gen.random() < cfg.draft_alpha or cfg.n_concepts == 1:
            return concept
        j = int(gen.integers(cfg.n_concepts - 1))
        return j if j < concept else j + 1

    def draft_dist(self, draft_concept: int) -> Array:
        return self.Q[draft_concept]

    # --- telemetry -------------------------------------------------------------
    def activation(self, gen: np.random.Generator, concept: int) -> Array:
        cfg = self.cfg
        a = gen.normal(0.0, cfg.background_noise, size=cfg.n_units)
        a[self.support[concept]] += cfg.support_gain + gen.normal(
            0.0, cfg.support_noise, size=cfg.units_per_concept
        )
        return a

    def telemetry(self, gen: np.random.Generator, concept: int) -> Array:
        """Observable slot set for one position. Values never leave the device."""
        return self.sketch.slots_for(self.activation(gen, concept), self.cfg.top_n)

    # --- convenience ------------------------------------------------------------
    def bucket_mass(self, p: Array) -> Array:
        """Aggregate a token distribution into bucket masses (C+1,)."""
        nb = self.cfg.n_concepts + 1
        out = np.zeros(nb)
        np.add.at(out, self.bucket_of_token, p)
        return out

    def tokens_in_bucket(self, bucket: int) -> Array:
        return np.flatnonzero(self.bucket_of_token == bucket)

    def top_concept_bucket(self, p: Array) -> int:
        """Argmax bucket mass over CONCEPT buckets only (function bucket
        excluded). Concept predictions and gate comparisons must both live in
        concept space: the shared function bucket can dominate raw bucket
        mass (it did, at default lambda_function=0.45 — see F-3 caveats) and
        would otherwise make every position look like a disagreement."""
        return int(self.bucket_mass(p)[: self.cfg.n_concepts].argmax())


@dataclass
class TelemetryDataset:
    """Aligned (slot multi-hot, concept) pairs harvested from a concept path."""

    X: Array  # (n, n_slots) multi-hot
    y: Array  # (n,) concept ids

    @staticmethod
    def harvest(world: World, gen: np.random.Generator, n: int) -> "TelemetryDataset":
        path = world.sample_concept_path(gen, n)
        X = np.zeros((n, world.cfg.n_slots))
        for i, c in enumerate(path):
            X[i] = world.sketch.multi_hot(world.telemetry(gen, int(c)))
        return TelemetryDataset(X=X, y=path.copy())

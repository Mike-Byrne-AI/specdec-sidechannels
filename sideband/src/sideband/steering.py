"""Draft steering mechanisms.

Steering ONLY modifies the draft distribution q. The verifier (specdec) is
untouched, so the emitted-token distribution stays exactly the target's — the
losslessness property tested in tests/test_specdec.py. Steering is therefore
a pure speed knob: it helps iff it moves q toward p (acceptance = 1 - TV).

Mechanisms (see DECISIONS D-8 and D-10):
- bucket_bias: hard-argmax boost of one bucket (v1 mechanism; kept as the
  comparison arm and for oracle ceilings that predate D-10).
- posterior_bias: CENTERED posterior-mass bias — boost each concept bucket b
  by beta * (P(b) - 1/C), non-concept (glue) tokens get 0. A uniform
  posterior is an exact no-op, so decoder uncertainty degrades the boost
  gracefully; a confident posterior boosts the predicted bucket AND demotes
  the other topical buckets while sparing glue tokens. Measured to dominate
  argmax+tau at every sideband width tested (F-7) — but ONLY behind the
  disagreement gate; ungated it reinstates the F-3 tax at full strength.

Encoded lessons:
- soft additive bias, never a hard mask (beta->inf pathology, F-3);
- the DISAGREEMENT gate is the load-bearing gate; confidence-tau is
  subsumed by centering in the posterior mechanism (F-7).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dists import Array, normalize, softmax


def bucket_bias(q: Array, bucket_tokens: Array, beta: float) -> Array:
    """Additive log-space boost of `beta` on `bucket_tokens`; renormalized.

    beta == 0 is an exact no-op. Never zeroes any token's probability.
    """
    if beta == 0.0:
        return normalize(q)
    logits = np.log(np.clip(np.asarray(q, dtype=np.float64), 1e-12, None))
    logits[np.asarray(bucket_tokens, dtype=np.int64)] += beta
    return softmax(logits)


def posterior_bias(
    q: Array, bucket_of_token: Array, posterior: Array, beta: float
) -> Array:
    """Centered posterior-mass bias (D-10 mechanism).

    posterior is a distribution over the C concept buckets (ids 0..C-1).
    Token boost = beta * (posterior[bucket] - 1/C) for concept-bucket tokens,
    0 for any other bucket id (glue/function). Exact no-op when beta == 0 or
    the posterior is uniform.
    """
    posterior = np.asarray(posterior, dtype=np.float64)
    C = posterior.shape[0]
    centered = posterior - 1.0 / C
    if beta == 0.0 or np.max(np.abs(centered)) < 1e-15:
        return normalize(q)
    bucket_of_token = np.asarray(bucket_of_token, dtype=np.int64)
    ext = np.zeros(int(bucket_of_token.max()) + 1, dtype=np.float64)
    ext[:C] = centered
    boost = ext[np.clip(bucket_of_token, 0, None)]
    # Negative bucket ids (tokens absent from a real buckets file) are glue:
    # zero boost. Without the mask, ext[-1] would WRAP to the last bucket's
    # boost — silent and wrong (latent; synthetic ids are always >= 0).
    boost[bucket_of_token < 0] = 0.0
    logits = np.log(np.clip(np.asarray(q, dtype=np.float64), 1e-12, None))
    logits += beta * boost
    return softmax(logits)


@dataclass
class GatedSteerer:
    """Apply a bucket bias only when confidence clears a threshold."""

    beta: float
    tau: float = 0.0  # minimum confidence; 0 disables gating

    def steer(self, q: Array, bucket_tokens: Array, confidence: float = 1.0) -> Array:
        if confidence < self.tau:
            return normalize(q)
        return bucket_bias(q, bucket_tokens, self.beta)


# --- concept-space primitives for the REAL adapter (OQ-4/D-7) ---------------
# steer_bucket_of_token maps tokens to compact concept ids 0..C-1 with glue /
# unbucketed tokens at -1 (glue.glue_remap). These three functions are the
# real-vocab analogs of World.bucket_mass(p)[:C] / World.top_concept_bucket /
# the pipeline steering branch, pinned equivalent by tests — hf_specdec calls
# them instead of re-implementing the semantics inline (the same discipline
# D-3 imposes on verifier math).


def concept_posterior(
    p: Array, steer_bucket_of_token: Array, C: int, sharp: bool = False
) -> Array | None:
    """Concept-bucket masses of p, renormalized over the C concept buckets.

    Glue/unbucketed tokens (id -1) contribute nothing. Returns None when p
    puts zero mass on concept tokens (no basis for a prediction — callers
    must not steer). sharp=True returns a one-hot at the argmax (the D-11
    sharpened free variant); ties break to the lowest bucket id.
    """
    valid = steer_bucket_of_token >= 0
    bm = np.bincount(steer_bucket_of_token[valid],
                     weights=np.asarray(p, dtype=np.float64)[valid], minlength=C)
    s = bm.sum()
    if s <= 0.0:
        return None
    post = bm / s
    if sharp:
        oh = np.zeros(C)
        oh[int(post.argmax())] = 1.0
        return oh
    return post


def concept_argmax(dist: Array, steer_bucket_of_token: Array, C: int) -> int:
    """Top CONCEPT bucket of a token distribution (glue excluded, D-7)."""
    valid = steer_bucket_of_token >= 0
    return int(np.bincount(steer_bucket_of_token[valid],
                           weights=np.asarray(dist, dtype=np.float64)[valid],
                           minlength=C).argmax())


def apply_concept_steering(
    q: Array,
    steer_bucket_of_token: Array,
    C: int,
    posterior: Array,
    beta: float,
    gate: str = "disagree",
    mech: str = "posterior",
) -> tuple[Array, bool]:
    """One drafted position: gate in concept space, then bias q.

    Returns (q', gate_open). gate='disagree' opens only where the draft's own
    top concept bucket differs from the posterior's argmax (F-3/F-7: the
    load-bearing gate); 'always' is the control arm. mech='posterior' applies
    posterior_bias (glue ids < 0 get zero boost, D-10); 'argmax' hard-boosts
    the predicted bucket's tokens (v1 comparison arm). q is returned
    UNTOUCHED (not renormalized) when the gate is closed.
    """
    b = int(posterior.argmax())
    if gate == "disagree" and concept_argmax(q, steer_bucket_of_token, C) == b:
        return q, False
    if mech == "posterior":
        return posterior_bias(q, steer_bucket_of_token, posterior, beta), True
    return bucket_bias(q, np.flatnonzero(steer_bucket_of_token == b), beta), True

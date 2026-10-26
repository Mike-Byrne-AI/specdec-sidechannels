"""Exact speculative decoding (Leviathan et al. 2023 rejection scheme).

This module is the single source of truth for verifier math in this repo.
The synthetic testbed and the real-model adapters (`sideband.real.hf_specdec`)
both call `spec_step` / `run_block`, so the accept/reject logic that is proven
exact by tests/test_specdec.py is the same logic that runs against HF logits.

Key property (tested by enumeration): for ANY draft distribution q — including
arbitrarily steered q — the emitted token is distributed exactly as the target
distribution p. Steering can only change speed, never output quality.

Per-step acceptance probability is analytically 1 - TV(p, q); this is also
tested. Higher acceptance == faster decode, and steering earns its keep iff
it moves q toward p.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .dists import Array, normalize, sample, tv_distance


@dataclass
class StepOutcome:
    """One draft position's verification result."""

    proposed: int          # token the draft proposed (x ~ q)
    accepted: bool
    emitted: int           # == proposed if accepted, else residual sample ~ r
    accept_prob: float     # min(1, p[x]/q[x]) for the proposed x
    offset: int = 0        # 1-based position within the draft block


@dataclass
class BlockOutcome:
    """One draft-then-verify block."""

    steps: list[StepOutcome]
    n_accepted: int
    emitted: list[int]     # accepted prefix + (residual sample | bonus token)
    bonus: int | None      # target-sampled bonus token iff all gamma accepted

    @property
    def tokens_per_target_call(self) -> int:
        # One target forward verifies the whole block and always yields
        # n_accepted tokens plus either a residual sample or a bonus token.
        return len(self.emitted)


def residual_distribution(p: Array, q: Array) -> Array:
    """Normalized positive part of (p - q); equals p when p == q."""
    r = np.clip(np.asarray(p, dtype=np.float64) - np.asarray(q, dtype=np.float64), 0.0, None)
    s = r.sum()
    if s <= 0.0:
        return normalize(p)
    return r / s


def spec_step(gen: np.random.Generator, p: Array, q: Array, proposed: int | None = None) -> StepOutcome:
    """One exact accept/reject step.

    Draft proposes x ~ q; accept with prob min(1, p[x]/q[x]); on rejection,
    emit a sample from the residual max(0, p-q)/Z. Emitted ~ p exactly.

    `proposed`: the caller's own draw x ~ q. A real adapter MUST pass the
    token its draft actually rolled out — that token conditioned every later
    draft/target distribution in the block, and verifying an independent
    redraw decouples the verified path from the conditioning path (the bug
    class fixed 2026-08-29; see tests). When None, spec_step draws x itself —
    correct for the synthetic pipeline, where nothing else conditions on the
    realization. Exactness holds in both modes PROVIDED the caller's x was
    truly sampled from this q.
    """
    p = normalize(p)
    q = normalize(q)
    x = int(proposed) if proposed is not None else sample(gen, q)
    px, qx = float(p[x]), float(q[x])
    if proposed is not None and qx <= 0.0:
        # A supplied proposal with zero draft mass means the caller's x was
        # NOT drawn from this q — the exact contract violation this parameter
        # exists to prevent. Fail loud, never silently accept.
        raise ValueError(f"proposed token {x} has zero probability under q")
    a = 1.0 if qx <= 0.0 else min(1.0, px / qx)  # self-sampled mode: qx>0 whenever x is sampled
    if gen.random() < a:
        return StepOutcome(proposed=x, accepted=True, emitted=x, accept_prob=a)
    y = sample(gen, residual_distribution(p, q))
    return StepOutcome(proposed=x, accepted=False, emitted=y, accept_prob=a)


def analytic_acceptance(p: Array, q: Array) -> float:
    """P(accept) = sum_x min(p, q) = 1 - TV(p, q)."""
    return 1.0 - tv_distance(normalize(p), normalize(q))


def run_block(
    gen: np.random.Generator,
    target_dists: list[Array],
    draft_dists: list[Array],
) -> BlockOutcome:
    """Verify one block of gamma draft positions.

    target_dists has gamma + 1 entries: p for each draft position plus the
    bonus position sampled from the target when every draft token is accepted.
    draft_dists has gamma entries (q per draft position). In a real system the
    gamma + 1 target distributions come from ONE parallel target forward; here
    the caller supplies them.
    """
    gamma = len(draft_dists)
    if len(target_dists) != gamma + 1:
        raise ValueError("need gamma+1 target dists (last one is the bonus position)")

    steps: list[StepOutcome] = []
    emitted: list[int] = []
    for j in range(gamma):
        out = spec_step(gen, target_dists[j], draft_dists[j])
        out.offset = j + 1
        steps.append(out)
        emitted.append(out.emitted)
        if not out.accepted:
            return BlockOutcome(steps=steps, n_accepted=j, emitted=emitted, bonus=None)

    bonus = sample(gen, normalize(target_dists[gamma]))
    emitted.append(bonus)
    return BlockOutcome(steps=steps, n_accepted=gamma, emitted=emitted, bonus=bonus)


@dataclass
class RunMetrics:
    """Aggregates over many blocks."""

    n_blocks: int = 0
    n_proposed: int = 0
    n_accepted: int = 0
    n_emitted: int = 0
    accepted_by_offset: dict[int, int] = field(default_factory=dict)
    proposed_by_offset: dict[int, int] = field(default_factory=dict)
    rejections: list[tuple[int, int]] = field(default_factory=list)  # (proposed, emitted)

    def update(self, block: BlockOutcome) -> None:
        self.n_blocks += 1
        self.n_emitted += len(block.emitted)
        for st in block.steps:
            self.n_proposed += 1
            self.proposed_by_offset[st.offset] = self.proposed_by_offset.get(st.offset, 0) + 1
            if st.accepted:
                self.n_accepted += 1
                self.accepted_by_offset[st.offset] = self.accepted_by_offset.get(st.offset, 0) + 1
            else:
                self.rejections.append((st.proposed, st.emitted))

    @property
    def acceptance_rate(self) -> float:
        return self.n_accepted / max(1, self.n_proposed)

    @property
    def mean_accepted_per_block(self) -> float:
        return self.n_accepted / max(1, self.n_blocks)

    @property
    def tokens_per_target_call(self) -> float:
        # Every block costs exactly one target forward.
        return self.n_emitted / max(1, self.n_blocks)

    def acceptance_by_offset(self) -> dict[int, float]:
        return {
            j: self.accepted_by_offset.get(j, 0) / n
            for j, n in sorted(self.proposed_by_offset.items())
        }

    def to_dict(self) -> dict:
        return {
            "n_blocks": self.n_blocks,
            "n_proposed": self.n_proposed,
            "n_accepted": self.n_accepted,
            "n_emitted": self.n_emitted,
            "acceptance_rate": self.acceptance_rate,
            "mean_accepted_per_block": self.mean_accepted_per_block,
            "tokens_per_target_call": self.tokens_per_target_call,
            "acceptance_by_offset": self.acceptance_by_offset(),
        }

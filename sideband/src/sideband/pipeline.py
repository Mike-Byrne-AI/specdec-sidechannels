"""End-to-end simulation: spec decoding over a concept path under a policy.

Policies (who supplies the concept prediction, and with what information):

  none                 vanilla speculative decoding (lower baseline).
  oracle_concept_now   TRUE concept at each drafted position. Non-causal:
                       no real system has this. Ceiling with perfect, fresh
                       state knowledge.
  oracle_concept_stale TRUE concept at the last verified position, held for
                       the whole block. Causal information set == what a
                       PERFECT telemetry decoder would know. The gap
                       (now - stale) is the pure staleness tax.
  free_lastp           the target's distribution at the last verified
                       position, projected to concept-bucket masses. FREE in
                       any spec decode (the target computed it during
                       verification) — no telemetry needed. Any telemetry
                       claim must beat or justify itself against this (D-5).
  sidecar              learned classifier on the telemetry (slot set) at the
                       last verified position, held for the block. The
                       deployable policy.

Mechanisms (steer_mech, D-8/D-10):
  argmax     v1: hard boost of the argmax bucket, confidence-tau gated.
  posterior  v2, D-10's default (this function's parameter default stays
             "argmax"; dated note 2026-10-16): centered posterior-mass bias
             (steering.posterior_bias).
             Oracles use a one-hot posterior; free_lastp uses normalized
             concept-bucket masses of p_last; sidecar uses its full softmax.

Gating (steer_gate): the DISAGREEMENT gate ('disagree') applies the bias only
where the draft's own top CONCEPT bucket differs from the prediction's argmax
— measured load-bearing for BOTH mechanisms (F-3, F-7). 'always' exists as
the control arm.

Causality is enforced by construction: causal policies only receive state
from positions <= last verified position. Telemetry is drawn once per
position from its OWN rng stream (D-6) and cached — the same slots the
"device" emitted are what the sidecar sees, re-drafts included.

Rejection accounting (D-9 adjacent): for every rejection we record the
proposed/emitted bucket pair (sampled estimator), the analytic residual
cross-bucket MASS (variance-free estimator, F-8), and the ideal correction
cost -log2 r[emitted] in bits (fuel for the verified-archives track, e07).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .dists import rng
from .sidecar import SoftmaxRegression
from .specdec import RunMetrics, analytic_acceptance, residual_distribution, run_block
from .steering import GatedSteerer, posterior_bias
from .synthetic import World

POLICIES = ("none", "oracle_concept_now", "oracle_concept_stale", "free_lastp", "sidecar")
MECHANISMS = ("argmax", "posterior")


@dataclass
class SimResult:
    policy: str
    beta: float
    tau: float
    metrics: RunMetrics
    steer_gate: str = "always"
    steer_mech: str = "argmax"
    analytic_acc_sum: float = 0.0
    analytic_acc_n: int = 0
    analytic_by_offset: dict[int, list[float]] = field(default_factory=dict)
    rejection_buckets: list[tuple[int, int]] = field(default_factory=list)  # (bucket_proposed, bucket_emitted)
    residual_cross_mass: list[float] = field(default_factory=list)
    rejection_bits: list[float] = field(default_factory=list)  # -log2 r[emitted]
    steered_positions: int = 0

    @property
    def analytic_acceptance(self) -> float:
        return self.analytic_acc_sum / max(1, self.analytic_acc_n)

    def cross_bucket_fraction(self) -> float:
        """SAMPLED estimator: fraction of rejections whose emitted (residual-
        sampled) token sits in a different bucket than the proposed one."""
        if not self.rejection_buckets:
            return float("nan")
        diff = sum(1 for a, b in self.rejection_buckets if a != b)
        return diff / len(self.rejection_buckets)

    def cross_bucket_mass_fraction(self) -> float:
        """ANALYTIC estimator (F-8): mean over rejections of the residual
        distribution's mass OUTSIDE the proposed token's bucket. Same
        estimand as cross_bucket_fraction, zero sampling variance."""
        if not self.residual_cross_mass:
            return float("nan")
        return float(np.mean(self.residual_cross_mass))

    def mean_rejection_bits(self) -> float:
        """Ideal entropy-coding cost of one correction, bits (e07 fuel)."""
        if not self.rejection_bits:
            return float("nan")
        return float(np.mean(self.rejection_bits))

    def to_dict(self) -> dict:
        d = {
            "policy": self.policy,
            "beta": self.beta,
            "tau": self.tau,
            "steer_gate": self.steer_gate,
            "steer_mech": self.steer_mech,
            "analytic_acceptance": self.analytic_acceptance,
            "analytic_acceptance_by_offset": {
                j: float(np.mean(v)) for j, v in sorted(self.analytic_by_offset.items())
            },
            "cross_bucket_fraction_of_rejections": self.cross_bucket_fraction(),
            "cross_bucket_residual_mass": self.cross_bucket_mass_fraction(),
            "mean_rejection_bits": self.mean_rejection_bits(),
            "n_rejections": len(self.rejection_buckets),
            "steered_positions": self.steered_positions,
        }
        d.update(self.metrics.to_dict())
        return d


def run_simulation(
    world: World,
    seed: int,
    n_positions: int,
    gamma: int,
    policy: str = "none",
    beta: float = 0.0,
    tau: float = 0.0,
    sidecar: SoftmaxRegression | None = None,
    steer_gate: str = "always",
    steer_mech: str = "argmax",
) -> SimResult:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; choose from {POLICIES}")
    if policy == "sidecar" and sidecar is None:
        raise ValueError("policy 'sidecar' needs a trained sidecar model")
    if steer_gate not in ("always", "disagree"):
        raise ValueError("steer_gate must be 'always' or 'disagree'")
    if steer_mech not in MECHANISMS:
        raise ValueError(f"steer_mech must be one of {MECHANISMS}")

    gen = rng(seed)
    # Telemetry gets its OWN stream (D-6): policies that read telemetry must
    # not perturb the draft/verify trajectory, or policy comparisons at the
    # same seed stop being paired (this bit us in e05 v0).
    gen_tel = rng(seed + 987_654_321)
    path = world.sample_concept_path(gen, n_positions + gamma + 2)
    steerer = GatedSteerer(beta=beta, tau=tau)
    telemetry_cache: dict[int, np.ndarray] = {}
    C = world.cfg.n_concepts

    def telemetry_at(pos: int) -> np.ndarray:
        if pos not in telemetry_cache:
            telemetry_cache[pos] = world.telemetry(gen_tel, int(path[pos]))
        return telemetry_cache[pos]

    def one_hot(c: int) -> np.ndarray:
        v = np.zeros(C)
        v[c] = 1.0
        return v

    def block_choice(last_pos: int) -> tuple[int | None, float, np.ndarray | None]:
        """Causal policies: (argmax bucket, confidence, posterior) held for
        the block. Posterior is over the C concept buckets."""
        if policy == "oracle_concept_stale":
            c = int(path[last_pos])
            return c, 1.0, one_hot(c)
        if policy == "free_lastp":
            p_last = world.target_dist(int(path[last_pos]))
            bm = world.bucket_mass(p_last)[:C]
            post = bm / bm.sum()
            return int(post.argmax()), 1.0, post
        if policy == "sidecar":
            x = world.sketch.multi_hot(telemetry_at(last_pos))
            post = sidecar.probs(x[None, :])[0]
            return int(post.argmax()), float(post.max()), post
        return None, 0.0, None

    res = SimResult(policy=policy, beta=beta, tau=tau, steer_gate=steer_gate,
                    steer_mech=steer_mech, metrics=RunMetrics())
    pos = 0  # last verified/emitted position; position 0 acts as the prompt
    while pos + gamma + 1 < n_positions:
        held_b, held_conf, held_post = block_choice(pos)
        target_dists = [world.target_dist(int(path[pos + 1 + j])) for j in range(gamma + 1)]
        draft_dists = []
        for j in range(gamma):
            c_draft = world.draft_concept(gen, int(path[pos + 1 + j]))
            q = world.draft_dist(c_draft)
            if policy == "oracle_concept_now":
                c_now = int(path[pos + 1 + j])
                b, conf, post = c_now, 1.0, one_hot(c_now)
            else:
                b, conf, post = held_b, held_conf, held_post

            gate_open = True
            if steer_gate == "disagree" and b is not None:
                gate_open = world.top_concept_bucket(q) != b

            if policy != "none" and b is not None and gate_open and conf >= tau:
                if steer_mech == "posterior":
                    q_steered = posterior_bias(q, world.bucket_of_token, post, beta)
                else:
                    q_steered = steerer.steer(q, world.tokens_in_bucket(b), confidence=conf)
                if beta != 0.0:
                    res.steered_positions += 1
            else:
                q_steered = q

            draft_dists.append(q_steered)
            a = analytic_acceptance(target_dists[j], q_steered)
            res.analytic_acc_sum += a
            res.analytic_acc_n += 1
            res.analytic_by_offset.setdefault(j + 1, []).append(a)

        block = run_block(gen, target_dists, draft_dists)
        res.metrics.update(block)
        for st in block.steps:
            if not st.accepted:
                res.rejection_buckets.append(
                    (int(world.bucket_of_token[st.proposed]), int(world.bucket_of_token[st.emitted]))
                )
                j = st.offset - 1
                r = residual_distribution(target_dists[j], draft_dists[j])
                same = world.bucket_of_token == world.bucket_of_token[st.proposed]
                res.residual_cross_mass.append(float(1.0 - r[same].sum()))
                res.rejection_bits.append(float(-np.log2(max(r[st.emitted], 1e-300))))
        pos += len(block.emitted)
    return res


def train_sidecar(world: World, seed: int, n_train: int = 20000, epochs: int = 25) -> tuple[SoftmaxRegression, float]:
    """Harvest a telemetry dataset and fit the sidecar; returns (model, holdout_acc)."""
    from .synthetic import TelemetryDataset

    gen = rng(seed)
    data = TelemetryDataset.harvest(world, gen, n_train)
    n_val = max(1, n_train // 5)
    Xtr, ytr = data.X[:-n_val], data.y[:-n_val]
    Xva, yva = data.X[-n_val:], data.y[-n_val:]
    model = SoftmaxRegression(world.cfg.n_slots, world.cfg.n_concepts, seed=seed + 1)
    model.fit(Xtr, ytr, epochs=epochs)
    return model, model.accuracy(Xva, yva)

"""HF target/draft speculative decoding with rejection-audit logging.

GPU box. Default path keeps per-prompt KV caches on both models, cropped to
the verified prefix after every block: per block it feeds ~2*gamma+2 token
positions instead of the reference path's (gamma+1)*L + O(gamma^2) at prefix
length L — the ratio GROWS with L (wall-clock is deliberately unmeasured;
D-9's ban stands). --no-kv-cache selects the exact-recompute reference. The
acceptance ESTIMAND is identical on both paths — bf16 kernel tiling makes
individual trajectories diverge at the bit level, which the sanity pass
checks with a small A/B (expect equal within sampling noise, never
bit-identical). Wall-clock claims remain BANNED from this file (D-9): the
cache makes runs faster, it does not make timing measurements a benchmark.

The accept/reject/residual math is `sideband.specdec.spec_step` — the numpy
code proven exact by tests/test_specdec.py — applied to distributions pulled
out of torch logits, WITH the drafted token passed through as the proposal
(spec_step(proposed=...)): the verified token must be the token that
conditioned the rest of the block. Single source of truth, per DECISIONS D-3.

Crash resilience: per-prompt RNG streams (dists.spawn — child i is
independent of the prompt count, so streams are resume-stable and
NF4-vs-bf16 comparisons pair at prompt granularity as the K-1 sanity pass
requires); per-prompt stats checkpointed to <out>.stats.jsonl and flushed +
fsynced with the audit records after every prompt; `--resume` validates the
meta sidecar against the current invocation, repairs any torn tail from a
hard kill, and continues from the first incomplete prompt.

Usage (Phase 0a audit, defaults mirror the SD^2 pairing):
    python -m sideband.real.hf_specdec \
        --target meta-llama/Llama-3.1-8B-Instruct \
        --draft  meta-llama/Llama-3.2-1B-Instruct \
        --buckets results/real/buckets_k512.json \
        --prompts data/prompts.jsonl --n-prompts 200 \
        --gamma 4 --max-new 256 --temperature 1.0 \
        --load-4bit --out results/real/audit_k512.jsonl

With --buckets from bucketize_vocab.py, every rejection is logged with
proposed/emitted tokens and their buckets; `summarize_audit` reports the
cross-bucket fraction and residual mass with the CIs the pre-registered K-1
rule reads. A provenance .meta.json (written BEFORE the run), a .stats.jsonl
(per-prompt checkpoint), and a .summary.json (completion marker) sit next to
the audit jsonl. The buckets file must match --target (model id + n_tokens
are checked; --allow-buckets-mismatch to override deliberately).

On a 12GB card, add --load-4bit: the TARGET loads in NF4 (draft stays bf16).
Acceptance is then a property of the quantized target; regime-label any
finding accordingly. Models must be fully GPU-resident — silent CPU offload
by device_map="auto" is refused unless --allow-cpu-offload (the bf16
confirmation path in K-1's near-band rule is the legitimate use).

Steering hooks: pass --steer bucket --beta B --bucket-source free_lastp to
reproduce the synthetic policies against real models. The sidecar policy
plugs in once Phase 2/3 telemetry exists on the box.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..dists import normalize, spawn
from ..glue import glue_remap, load_glue, rejection_masses
from ..specdec import analytic_acceptance, spec_step
from ..stats import clopper_pearson, cluster_bootstrap_ci
from ..steering import apply_concept_steering, concept_posterior
from . import require_real_deps

# Args that define the run's identity: a --resume whose invocation differs on
# any of these is a different experiment and is refused.
RESUME_IDENTITY_ARGS = (
    "target", "draft", "buckets", "glue", "prompts", "n_prompts", "gamma",
    "max_new", "temperature", "steer", "bucket_source", "steer_gate",
    "steer_mech", "beta", "seed", "load_4bit", "no_chat_template",
    "allow_cpu_offload", "no_kv_cache", "log_generated",
)

# Llama-style chat templates interpolate a date; pin it so tokenized prefixes
# are identical across run dates ("deterministic given --seed" must not
# depend on the wall clock). Shared with harvest_freq.py.
PINNED_DATE = "26 Jul 2024"


@dataclass
class AuditRecord:
    prompt_idx: int
    position: int
    offset: int
    proposed: int
    emitted: int
    proposed_bucket: int | None
    emitted_bucket: int | None
    cross_bucket_residual_mass: float | None = None  # analytic estimator (F-8)
    run_id: str | None = None  # which segment (original or a resume) wrote it
    # Mass of the normalized residual r on GLUE-bucket tokens (OQ-4), when a
    # glue file is loaded; includes the proposed token's own bucket when that
    # bucket is glue. The concept-level steerable mass is derived, never
    # stored: residual mass in concept buckets != proposed's bucket
    #   = (1 - residual_mass_glue) - (1 - cross_bucket_residual_mass)   [proposed in concept]
    #   = (1 - residual_mass_glue)                                       [proposed in glue]
    residual_mass_glue: float | None = None

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


def _dist_from_logits(logits_row, temperature: float) -> np.ndarray:
    """torch logits row -> float64 numpy distribution."""
    import torch

    t = max(temperature, 1e-4)
    p = torch.softmax(logits_row.float() / t, dim=-1)
    return normalize(p.detach().cpu().numpy().astype(np.float64))


def load_buckets(
    path: str | None,
    vocab_size: int,
    expect_model: str | None = None,
    allow_mismatch: bool = False,
) -> np.ndarray | None:
    """Load a bucketize_vocab output, refusing silent mismatches.

    A buckets file built on a different model with the same tokenizer (e.g.
    the draft) would load cleanly and yield a plausible-but-wrong K-1 number;
    the file's own `model` and `n_tokens` fields make the check trivial."""
    if path is None:
        return None
    data = json.loads(Path(path).read_text())
    problems = []
    if expect_model is not None and data.get("model") not in (None, expect_model):
        problems.append(f"buckets file was built on {data['model']!r}, not {expect_model!r}")
    if data.get("n_tokens") is not None and int(data["n_tokens"]) != int(vocab_size):
        problems.append(f"buckets file covers {data['n_tokens']} tokens, model vocab is {vocab_size}")
    if problems and not allow_mismatch:
        raise SystemExit("refusing buckets file:\n  - " + "\n  - ".join(problems)
                         + "\n(--allow-buckets-mismatch to override deliberately)")
    for pr in problems:
        print(f"[buckets MISMATCH OVERRIDDEN] {pr}")
    arr = np.full(vocab_size, -1, dtype=np.int64)
    for tok, b in data["bucket_of_token"].items():
        arr[int(tok)] = int(b)
    return arr


# redact_args lives in the torch-free sideband.provenance module so CPU
# tools can share it; re-exported here for the existing import sites.
from ..provenance import _REDACT_STEMS, redact_args  # noqa: E402,F401


def _atomic_write_text(path: Path, text: str) -> None:
    """Atomic in namespace AND durable: fsync the tmp file before the rename,
    so a power loss after os.replace cannot persist the name without the
    bytes (repairs rewrite committed-evidence files; a truncated audit next
    to an intact stats file would silently skew K-1)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def repair_partial_outputs(
    out_path: Path, stats_path: Path, records_expected: bool = False,
    gen_path: Path | None = None,
) -> tuple[set[int], int]:
    """After a hard kill: drop the stats file's torn tail, then drop audit
    records that belong to prompts without a completed stats line (the
    in-flight prompt) or that are themselves torn. Atomic rewrites.

    records_expected (buckets on): a prompt's record count must equal its
    stats line's n_proposed - n_accepted (one record per rejection); a
    completed-looking prompt failing that invariant lost records to a torn
    write and is DEMOTED to incomplete so it re-runs cleanly.

    gen_path (--log-generated): the .gen.jsonl gets the same treatment —
    keep the FIRST parseable line per completed prompt, drop the rest (the
    fsync ordering writes gen before stats, so a completed prompt has
    exactly one durable gen line; anything else is in-flight debris).
    Returns (completed prompt idxs, n audit lines dropped)."""
    stats_rows: list[dict] = []
    if stats_path.exists():
        for line in stats_path.read_text().splitlines():
            try:
                d = json.loads(line)
                int(d["prompt_idx"])
            except (json.JSONDecodeError, KeyError, ValueError):
                break  # torn tail — everything after is unusable
            stats_rows.append(d)

    audit_lines: list[tuple[int, str]] = []
    n_total = 0
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            n_total += 1
            try:
                audit_lines.append((int(json.loads(line).get("prompt_idx", -1)), line))
            except json.JSONDecodeError:
                audit_lines.append((-1, None))  # torn — never kept

    count_by_prompt: dict[int, int] = {}
    for idx, line in audit_lines:
        if line is not None:
            count_by_prompt[idx] = count_by_prompt.get(idx, 0) + 1

    completed: set[int] = set()
    kept_stats: list[str] = []
    for d in stats_rows:
        i = int(d["prompt_idx"])
        if records_expected:
            expected = int(d.get("n_proposed", 0)) - int(d.get("n_accepted", 0))
            if count_by_prompt.get(i, 0) != expected:
                continue  # demote: this prompt's records are damaged — re-run it
        completed.add(i)
        kept_stats.append(json.dumps(d))
    _atomic_write_text(stats_path, "\n".join(kept_stats) + ("\n" if kept_stats else ""))

    kept = [line for idx, line in audit_lines if line is not None and idx in completed]
    _atomic_write_text(out_path, "\n".join(kept) + ("\n" if kept else ""))

    if gen_path is not None and gen_path.exists():
        kept_gen: list[str] = []
        seen: set[int] = set()
        for line in gen_path.read_text().splitlines():
            try:
                i = int(json.loads(line)["prompt_idx"])
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # torn
            if i in completed and i not in seen:
                seen.add(i)
                kept_gen.append(line)
        _atomic_write_text(gen_path, "\n".join(kept_gen) + ("\n" if kept_gen else ""))

    return completed, n_total - len(kept)


def spec_decode_prompt(
    target,
    draft,
    input_ids,
    gamma: int,
    max_new: int,
    temperature: float,
    gen: np.random.Generator,
    bucket_of_token: np.ndarray | None = None,
    steer_beta: float = 0.0,
    steer_source: str = "none",  # none | free_lastp | free_lastp_sharp (D-11) | oracle_nextp (D-2-named ceiling)
    steer_gate: str = "disagree",  # always | disagree (see synthetic F-3)
    steer_mech: str = "posterior",  # argmax | posterior (D-10 default)
    prompt_idx: int = 0,
    run_id: str | None = None,
    use_kv_cache: bool = True,
    steer_bucket_of_token: np.ndarray | None = None,
    glue_mask: np.ndarray | None = None,
    k3=None,
):
    """Run one prompt; returns (generated_ids, audit_records, stats).

    k3 (default None = byte-identical legacy path) is a k3_live.K3Config:
    the K-3 Attempt #1 adaptive-block-scheduling instrument (BLUEPRINT
    arc registration 2026-09-01 + stage-E clarifications E1-E11). With
    k3 set: q is NEVER modified (steering/oracle modes are refused); a
    PREFILL forward primes the target cache and produces the first
    block's anchor read at the prompt's last token (the cache is then
    cropped one position so every block's verify forward contains its
    own anchor row); per block, the policy consults STOP at drafted
    positions 1-2 and EXTEND once after base drafting (gamma varies per
    block); after each verify the anchor (row base + accepted count —
    conditioned on accepted content only) is read for the NEXT block's
    consults and logged read-only to the byproduct recorder. All k3
    logging is passive (no extra forwards beyond the prefill, which is
    uniform across arms and excluded from the call count per E6; no RNG
    consumption).

    Steering lives in CONCEPT space (D-7): `steer_bucket_of_token` maps
    tokens to compact concept-bucket ids 0..C-1 with glue/unbucketed tokens
    at -1 (glue.glue_remap builds it). The block-held posterior is the
    concept-bucket mass of last_p renormalized over concept buckets — the
    exact real analog of pipeline.py's `bucket_mass(p_last)[:C]` — sharpened
    to a one-hot at its argmax for the D-11 `free_lastp_sharp` variant. The
    disagreement gate compares top CONCEPT buckets on both sides, and the
    bias is steering.posterior_bias (glue ids < 0 get zero boost) — the
    tested numpy mechanism, not a re-implementation. When
    steer_bucket_of_token is None, every non-negative bucket id counts as
    concept (the pre-OQ-4 behavior, kept for the no-glue path and tests).

    `glue_mask` (bool over tokens) only feeds the audit record's
    residual_mass_glue field; it never affects the trajectory.

    Stats carry two analytic-acceptance estimands (D-9): `_drafted` sums
    1 - TV(p_j, q_j) over ALL gamma drafted positions of every block
    (including rows past a rejection — agreement along the drafted
    trajectory, the closest real analog of the synthetic unconditional
    metric), while `_verified` sums only positions the verify loop reached
    (survival-conditioned, comparable to empirical acceptance).

    use_kv_cache=True (default): per-prompt DynamicCaches on both models,
    cropped after every block — same logits in exact arithmetic, ~2*gamma+2
    token-positions per block vs (gamma+1)*L + O(gamma^2) uncached. Because
    the accepted tokens ARE the drafted tokens (proposal coupling), their KV
    entries are already in both caches; only the block's final emitted token
    (residual or bonus) is not, so both caches are cropped to len(ids) - 1
    (the DRAFT cache may already sit at len(ids) - 2 after a full-accept
    block — it never saw the gamma-th drafted token; hence the min() at the
    crop and a possibly 2-token delta next block. Do not "simplify" the
    delta to one token). use_kv_cache=False is the exact-recompute reference
    path for the pre-registered A/B (WHY_THIS_DIES K-1 KV rider): expect
    acceptance EQUAL WITHIN SAMPLING NOISE, not bit-identical (kernels tile
    by shape; the uncached path already re-computes the same position at
    different lengths across blocks, so neither path is bit-canonical).
    """
    torch, _ = require_real_deps()
    device = next(target.parameters()).device
    ids = input_ids.to(device)
    records: list[AuditRecord] = []
    n_proposed = n_accepted = n_blocks = 0
    n_steerable = n_gate_open = 0
    an_drafted = np.zeros(2)   # [sum, n] over all drafted positions
    an_verified = np.zeros(2)  # [sum, n] over verify-loop-reached positions
    an_by_offset: dict[int, list[float]] = {}
    last_p: np.ndarray | None = None  # target dist at last verified position
    steer_on = steer_beta != 0.0 and steer_source in ("free_lastp", "free_lastp_sharp")
    # oracle_nextp: NON-CAUSAL CEILING (D-2-named; no deployable system has
    # p_j before drafting position j). The target is stepped INCREMENTALLY
    # during drafting so each position's steering posterior is the concept
    # posterior of the target's OWN fresh distribution there. Active even at
    # beta=0 so the per-step feeding path itself is testable (steering
    # no-ops then). Registered: BLUEPRINT Phase 0c attribution rider.
    oracle_mode = steer_source == "oracle_nextp"
    sbot = steer_bucket_of_token
    if (steer_on or oracle_mode) and sbot is None and bucket_of_token is not None:
        # no glue file: every real bucket is a concept bucket (compact already)
        sbot = np.where(bucket_of_token >= 0, bucket_of_token, -1)
    if (steer_on or oracle_mode) and sbot is not None:
        C = int(sbot.max()) + 1
        if C < 2:
            raise ValueError("steering needs >= 2 concept buckets")
    else:
        steer_on = False
        oracle_mode = False
    if k3 is not None and (steer_on or oracle_mode or steer_beta != 0.0):
        raise ValueError("K-3 scheduling never modifies q — steering/oracle "
                         "modes are mutually exclusive with k3 (arc registration)")
    if k3 is not None and getattr(k3, "inject", None) is not None:
        # OQ-16 STAGE-A: draft-SIDE q modification through the drafter's
        # MLP up-projection hooks (D-1's bright line; the verifier and
        # sideband.specdec are untouched). One delta per block from the
        # block's consulted anchor; no RNG consumption; per-prompt reset.
        k3.inject.reset()
    n_drafted = n_stop_blocks = n_extend_blocks = 0
    anchor_read = None
    draft_cache = target_cache = None
    if use_kv_cache:
        from transformers import DynamicCache

        draft_cache, target_cache = DynamicCache(), DynamicCache()

    with torch.no_grad():
        if k3 is not None:
            # PREFILL (arc registration + E6): one target forward over the
            # prompt produces the FIRST block's anchor read at the prompt's
            # last token. On the cached path the cache is then cropped one
            # position, so every block's verify delta starts at the token
            # feeding the block's own row base+0 — the anchor row for an
            # accepted-count of 0 is then always inside the verify capture.
            # Uniform across arms; excluded from the verify-call count (E6).
            if use_kv_cache:
                pre_logits = target(ids, past_key_values=target_cache,
                                    use_cache=True).logits[0, -1]
            else:
                pre_logits = target(ids).logits[0, -1]
            if k3.reader is not None:
                p0 = _dist_from_logits(pre_logits, temperature)
                anchor_read = k3.reader.read(p0, pos=int(ids.shape[1]) - 1,
                                             abs_pos=int(ids.shape[1]) - 1)
            if use_kv_cache:
                target_cache.crop(ids.shape[1] - 1)
                assert target_cache.get_seq_length() == ids.shape[1] - 1, \
                    "DynamicCache.crop semantics changed — prefill state invalid"
        while ids.shape[1] - input_ids.shape[1] < max_new:
            n_blocks += 1
            # --- draft gamma tokens autoregressively -----------------------
            draft_ids = ids
            if use_kv_cache:
                # feed only what the draft cache hasn't seen. Usually 1 token
                # (cache at len(ids)-1), but 2 after a full-accept block: the
                # draft cache never saw the gamma-th drafted token, so it
                # sits at len(ids)-2 there. Never assume a 1-token delta.
                d_delta = ids[:, draft_cache.get_seq_length():]
            # Block-held prediction (mirrors pipeline.block_choice): the
            # concept posterior of last_p, computed ONCE per block — last_p
            # is fixed for the whole block, per D-2 causality. None when
            # last_p puts zero mass on concept tokens (do not steer).
            block_post: np.ndarray | None = None
            if steer_on and last_p is not None:
                block_post = concept_posterior(
                    last_p, sbot, C, sharp=(steer_source == "free_lastp_sharp"))

            qs: list[np.ndarray] = []
            proposed: list[int] = []
            if oracle_mode:
                # --- ORACLE-CEILING PATH: interleave target and draft -------
                # Each drafted position j first gets the target's TRUE p_j
                # (one incremental target step), whose concept posterior
                # steers q_j — per-position and fresh, never block-held.
                # After gamma steps one more target step yields the bonus
                # row, leaving the target cache at len(ids)+gamma — the same
                # terminal state as the standard batched forward, so the
                # crop logic below is shared unchanged.
                ps = []
                if use_kv_cache:
                    t_delta = ids[:, target_cache.get_seq_length():]
                else:
                    t_ids = ids
                for _ in range(gamma):
                    if use_kv_cache:
                        t_row = target(t_delta, past_key_values=target_cache,
                                       use_cache=True).logits[0, -1]
                    else:
                        t_row = target(t_ids).logits[0, -1]
                    p_here = _dist_from_logits(t_row, temperature)
                    ps.append(p_here)
                    if use_kv_cache:
                        d_logits = draft(d_delta, past_key_values=draft_cache,
                                         use_cache=True).logits[0, -1]
                    else:
                        d_logits = draft(draft_ids).logits[0, -1]
                    q = _dist_from_logits(d_logits, temperature)
                    if steer_beta != 0.0:
                        post = concept_posterior(p_here, sbot, C)
                        if post is not None:
                            n_steerable += 1
                            q, gate_open = apply_concept_steering(
                                q, sbot, C, post, steer_beta,
                                gate=steer_gate, mech=steer_mech)
                            n_gate_open += int(gate_open)
                    x = int(gen.choice(q.shape[0], p=q))
                    qs.append(q)
                    proposed.append(x)
                    xt = torch.tensor([[x]], device=device, dtype=ids.dtype)
                    if use_kv_cache:
                        d_delta = xt
                        t_delta = xt
                    else:
                        draft_ids = torch.cat([draft_ids, xt], dim=1)
                        t_ids = torch.cat([t_ids, xt], dim=1)
                if use_kv_cache:
                    bonus_row = target(t_delta, past_key_values=target_cache,
                                       use_cache=True).logits[0, -1]
                else:
                    bonus_row = target(t_ids).logits[0, -1]
            else:
                stop_pos = 0
                extend_fired = False
                q_sigs: list[float] = []
                d_classes: list[int] = []
                if k3 is None:
                    for _ in range(gamma):
                        if use_kv_cache:
                            d_logits = draft(d_delta, past_key_values=draft_cache,
                                             use_cache=True).logits[0, -1]
                        else:
                            d_logits = draft(draft_ids).logits[0, -1]
                        q = _dist_from_logits(d_logits, temperature)
                        if block_post is not None:
                            n_steerable += 1
                            # Concept-space gate + bias (D-7/D-10) via the tested
                            # helpers — semantics pinned against the synthetic
                            # World in tests/test_steering_pipeline.py.
                            q, gate_open = apply_concept_steering(
                                q, sbot, C, block_post, steer_beta,
                                gate=steer_gate, mech=steer_mech)
                            n_gate_open += int(gate_open)
                        x = int(gen.choice(q.shape[0], p=q))
                        qs.append(q)
                        proposed.append(x)
                        xt = torch.tensor([[x]], device=device, dtype=ids.dtype)
                        if use_kv_cache:
                            d_delta = xt  # next draft step consumes just this token
                        else:
                            draft_ids = torch.cat([draft_ids, xt], dim=1)
                else:
                    # K-3 drafting: q untouched; STOP consults at drafted
                    # positions 1-2 only; EXTEND decided once after base
                    # drafting (E4). All consult inputs are read-only.
                    # BLOCK 1 NEVER CONSULTS (E12): the prefill anchor's
                    # offset-1 token IS drafted position 1, so a block-1
                    # consult would read the off2 probe against an offset-1
                    # token — the block rides at gamma_base in every arm.
                    pol = k3.policy
                    consults_on = n_blocks > 1
                    g_target = pol.gamma_base
                    # Head arms (OQ-15 STAGE-C FREEZE): score through the
                    # frozen heads; core = the reader's own probe_input
                    # vector (family free -> x["a"], tel -> x["c"]).
                    # a_hats grows as q_sigs arrive; S_j = prod(a_hats[:j]).
                    a_hats: list[float] = []
                    head_core = None
                    if pol.kind == "head":
                        head_core = anchor_read.x[
                            "a" if k3.head_scorer.family == "free" else "c"]
                    if k3.inject is not None:
                        # STAGE-A: this block's delta from the anchor it
                        # CONSULTS (the prefill read for block 1, else the
                        # last verified row) — set before the first draft
                        # step, live for every drafted row of the block.
                        k3.inject.start_block(anchor_read)
                    while len(proposed) < g_target:
                        if use_kv_cache:
                            d_logits = draft(d_delta, past_key_values=draft_cache,
                                             use_cache=True).logits[0, -1]
                        else:
                            d_logits = draft(draft_ids).logits[0, -1]
                        q = _dist_from_logits(d_logits, temperature)
                        x = int(gen.choice(q.shape[0], p=q))
                        qs.append(q)
                        proposed.append(x)
                        xt = torch.tensor([[x]], device=device, dtype=ids.dtype)
                        if use_kv_cache:
                            d_delta = xt
                        else:
                            draft_ids = torch.cat([draft_ids, xt], dim=1)
                        j = len(proposed)  # 1-based drafted position
                        if j <= 2:  # the two consult positions (offsets 2-3)
                            q_sigs.append(float(q[x]))
                            d_classes.append(k3.reader.token_class(x)
                                             if k3.reader is not None else -1)
                            pp = pc = None
                            if pol.probe_arm is not None:
                                pp = anchor_read.probe_pred[pol.probe_arm][j - 1]
                                pc = anchor_read.probe_conf[pol.probe_arm][j - 1]
                            hs = None
                            if pol.kind == "head" and consults_on:
                                a_hats.append(k3.head_scorer.a_hat(
                                    head_core, q_sigs, j))
                                hs = 1.0
                                for a in a_hats:
                                    hs *= a  # S_j
                            if consults_on and pol.stop_at(
                                    j, q_signal=q_sigs[-1], probe_pred=pp,
                                    probe_conf=pc, draft_class=d_classes[-1],
                                    head_score=hs):
                                stop_pos = j
                                g_target = j
                        if (consults_on and len(proposed) == pol.gamma_base
                                and stop_pos == 0
                                and not extend_fired and len(q_sigs) == 2):
                            if pol.kind == "draft_conf":
                                fire = pol.extend(q_signals=tuple(q_sigs))
                            elif pol.kind == "probe":
                                fire = pol.extend(
                                    probe_preds=anchor_read.probe_pred[pol.probe_arm],
                                    probe_confs=anchor_read.probe_conf[pol.probe_arm],
                                    draft_classes=tuple(d_classes))
                            elif pol.kind == "head":
                                # S_4 * a_hat_5 = prod(a_hat_1..a_hat_5)
                                while len(a_hats) < 5:
                                    a_hats.append(k3.head_scorer.a_hat(
                                        head_core, q_sigs, len(a_hats) + 1))
                                ext_score = 1.0
                                for a in a_hats[:5]:
                                    ext_score *= a
                                fire = pol.extend(head_score=ext_score)
                            else:
                                fire = False
                            if fire:
                                extend_fired = True
                                g_target = pol.gamma_max

                if k3 is not None and k3.inject is not None:
                    k3.inject.end_block()   # hooks inert before the verify
                # --- one target forward over prefix + drafted tokens --------
                g_block = len(proposed)  # == gamma unless k3 stopped/extended
                if use_kv_cache:
                    tc = target_cache.get_seq_length()
                    full = torch.cat(
                        [ids, torch.tensor([proposed], device=device, dtype=ids.dtype)], dim=1
                    )
                    t_logits = target(full[:, tc:], past_key_values=target_cache,
                                      use_cache=True).logits[0]
                    base = ids.shape[1] - 1 - tc  # row predicting draft position 0
                else:
                    t_logits = target(draft_ids).logits[0]
                    base = ids.shape[1] - 1  # logits[base + j] predict draft position j
                # All g_block target dists up front: the analytic sums (D-9)
                # cover every DRAFTED position, including rows past the
                # block's rejection point (drafted-trajectory estimand).
                ps = [_dist_from_logits(t_logits[base + j], temperature) for j in range(g_block)]
                bonus_row = t_logits[base + g_block]
            g_block = len(proposed)
            avals = [analytic_acceptance(ps[j], qs[j]) for j in range(g_block)]
            for j, a in enumerate(avals):
                an_drafted += (a, 1.0)
                cell = an_by_offset.setdefault(j + 1, [0.0, 0.0])
                cell[0] += a
                cell[1] += 1.0
            emitted: list[int] = []
            for j in range(g_block):
                p = ps[j]
                an_verified += (avals[j], 1.0)
                # The verified proposal IS the drafted token (proposed=...):
                # it conditioned every later q/p in this block. Letting
                # spec_step redraw its own proposal decouples the verified
                # path from the conditioning path (bug fixed 2026-08-29).
                out = spec_step(gen, p, qs[j], proposed=proposed[j])
                n_proposed += 1
                if out.accepted:
                    n_accepted += 1
                    emitted.append(out.emitted)
                    last_p = p
                    continue
                emitted.append(out.emitted)
                last_p = p
                if bucket_of_token is not None:
                    cross_m, glue_m = rejection_masses(
                        p, qs[j], bucket_of_token, out.proposed, glue_mask)
                    records.append(
                        AuditRecord(
                            prompt_idx=prompt_idx,
                            position=ids.shape[1] + j,
                            offset=j + 1,
                            proposed=out.proposed,
                            emitted=out.emitted,
                            proposed_bucket=int(bucket_of_token[out.proposed]),
                            emitted_bucket=int(bucket_of_token[out.emitted]),
                            cross_bucket_residual_mass=cross_m,
                            run_id=run_id,
                            residual_mass_glue=glue_m,
                        )
                    )
                break
            else:
                # all gamma accepted -> bonus token from the target
                p_bonus = _dist_from_logits(bonus_row, temperature)
                emitted.append(int(gen.choice(p_bonus.shape[0], p=p_bonus)))
                last_p = p_bonus

            ids = torch.cat(
                [ids, torch.tensor([emitted], device=device, dtype=ids.dtype)], dim=1
            )
            if use_kv_cache:
                # Everything in ids except its LAST token (the residual or
                # bonus emission) was fed to both models as rollout, and with
                # proposal coupling those tokens are identical to the rollout
                # — so both caches are valid up to len(ids) - 1, exactly.
                n_keep = ids.shape[1] - 1
                target_cache.crop(n_keep)
                draft_cache.crop(min(n_keep, draft_cache.get_seq_length()))
                # Guard against cache-semantics drift in future transformers
                # (crop meaning, sliding-window layers): silent corruption
                # here would be indistinguishable from a bad audit number.
                assert target_cache.get_seq_length() == n_keep, \
                    "DynamicCache.crop semantics changed — audit invalid"

            if k3 is not None:
                # ANCHOR read for the NEXT block (arc registration): the row
                # that produced this block's emitted residual-or-bonus token,
                # index base + accepted count — conditioned on accepted
                # content only. Its input token sits at ids[-2] after the
                # append above. The verify forward's captures are still the
                # latest (nothing forwards between verify and here).
                blk_acc = len(emitted) - 1
                if k3.reader is not None:
                    p_anchor = ps[blk_acc] if blk_acc < g_block else p_bonus
                    new_read = k3.reader.read(p_anchor, pos=base + blk_acc,
                                              abs_pos=int(ids.shape[1]) - 2)
                    if k3.recorder is not None:
                        k3.recorder.add_block(
                            anchor=anchor_read, gamma_used=g_block,
                            stop_pos=stop_pos, extend_fired=extend_fired,
                            accepted=blk_acc, proposed=proposed,
                            analytic=avals, q_sigs=q_sigs,
                            draft_classes=d_classes)
                    anchor_read = new_read
                n_drafted += g_block
                n_stop_blocks += int(stop_pos > 0)
                n_extend_blocks += int(extend_fired)

            if emitted and hasattr(target.config, "eos_token_id"):
                eos = target.config.eos_token_id
                eos_set = set(eos) if isinstance(eos, (list, tuple)) else {eos}
                if any(t in eos_set for t in emitted):
                    break

    stats = {
        "n_blocks": n_blocks,
        "n_proposed": n_proposed,
        "n_accepted": n_accepted,
        "acceptance_rate": n_accepted / max(1, n_proposed),
        # D-9 analytic estimands; sums+ns so pooled means stay exact.
        "analytic_acc_drafted_sum": float(an_drafted[0]),
        "analytic_acc_drafted_n": int(an_drafted[1]),
        "analytic_acceptance_drafted": float(an_drafted[0] / max(1.0, an_drafted[1])),
        "analytic_acc_verified_sum": float(an_verified[0]),
        "analytic_acc_verified_n": int(an_verified[1]),
        "analytic_acc_drafted_by_offset": {
            str(j): [float(v[0]), int(v[1])] for j, v in sorted(an_by_offset.items())
        },
        # Gate diagnostics (F-3's story is about how often the gate opens).
        "n_steerable": n_steerable,
        "n_gate_open": n_gate_open,
    }
    if k3 is not None:
        # K-3 gate arithmetic (E6): tokens/call excludes the uniform
        # prefill; drafted counts are the budget-guard numerator input.
        n_emitted = int(ids.shape[1] - input_ids.shape[1])
        stats.update({
            "n_drafted": n_drafted,
            "n_emitted": n_emitted,
            "n_stop_blocks": n_stop_blocks,
            "n_extend_blocks": n_extend_blocks,
            "tokens_per_call": n_emitted / max(1, n_blocks),
            "drafted_per_emitted": n_drafted / max(1, n_emitted),
        })
    return ids, records, stats


def summarize_audit(records: list[AuditRecord], glue_bucket_ids=None) -> dict:
    """Cross-bucket share of rejections, with CIs per the Phase 0a exit
    criterion and kill rule K-1 (docs/WHY_THIS_DIES.md).

    With `glue_bucket_ids` (OQ-4), a `glue` section decomposes the same
    rejections into concept space:
    - concept_cross_fraction (primary token-level estimand, pre-registered in
      the K-7 addendum): fraction of ALL rejections whose emitted token sits
      in a CONCEPT bucket different from the proposed token's bucket — the
      corrections a concept-level bias could in principle have anticipated.
    - residual_mass_concept_other: the mass analog, derived per record from
      cross_bucket_residual_mass and residual_mass_glue (see AuditRecord);
      only records carrying residual_mass_glue contribute.
    - involvement fractions (proposed/emitted in glue) as diagnostics.

    Both estimands get uncertainty:
    - sampled fraction: Clopper-Pearson (assumes independent rejections —
      optimistic, positions within a prompt are correlated) AND a
      prompt-cluster bootstrap (conservative; K-1 reads this one).
    - residual MASS (the F-8 default estimand): prompt-cluster bootstrap
      only — it is not Bernoulli, so CP does not apply.

    Cluster frame: prompts with >= 1 logged rejection (zero-rejection prompts
    contribute no Bernoulli trials; at temperature 1.0 essentially every
    prompt rejects, so the frames coincide in practice).

    The by-offset breakdown is SURVIVAL-CONDITIONED (an offset-j rejection
    conditions on j-1 accepts — the D-9 distinction applies here too) and is
    reported with its n per cell; deep offsets are small-n.

    n_negative_bucket_records counts rejections whose proposed or emitted
    token was absent from buckets.json (bucket -1); should be 0 for a
    same-tokenizer pair — nonzero means the bucket file mismatches the model.
    """
    n = len(records)
    cross = sum(1 for r in records if r.proposed_bucket != r.emitted_bucket)
    by_offset: dict[int, list[int]] = {}
    by_prompt: dict[int, list[int]] = {}
    by_prompt_mass: dict[int, list[float]] = {}
    n_neg = 0
    for r in records:
        is_cross = int(r.proposed_bucket != r.emitted_bucket)
        by_offset.setdefault(r.offset, []).append(is_cross)
        by_prompt.setdefault(r.prompt_idx, []).append(is_cross)
        if r.cross_bucket_residual_mass is not None:
            by_prompt_mass.setdefault(r.prompt_idx, []).append(float(r.cross_bucket_residual_mass))
        if (r.proposed_bucket is not None and r.proposed_bucket < 0) or (
            r.emitted_bucket is not None and r.emitted_bucket < 0
        ):
            n_neg += 1
    masses = [m for v in by_prompt_mass.values() for m in v]

    ci_binom = clopper_pearson(cross, n) if n else None
    ci_prompt = None
    if len(by_prompt) >= 2:
        succ = np.array([float(sum(v)) for v in by_prompt.values()])
        tri = np.array([float(len(v)) for v in by_prompt.values()])
        ci_prompt = cluster_bootstrap_ci(succ, tri, seed=0)
    mass_ci_prompt = None
    if len(by_prompt_mass) >= 2:
        msucc = np.array([float(sum(v)) for v in by_prompt_mass.values()])
        mtri = np.array([float(len(v)) for v in by_prompt_mass.values()])
        mass_ci_prompt = cluster_bootstrap_ci(msucc, mtri, seed=0)

    out = {
        "n_rejections": n,
        "n_prompts_with_rejections": len(by_prompt),
        "n_negative_bucket_records": n_neg,
        "cross_bucket_fraction": cross / n if n else float("nan"),
        "cross_bucket_fraction_ci95_binomial": ci_binom,
        "cross_bucket_fraction_ci95_prompt_bootstrap": ci_prompt,
        "cross_bucket_residual_mass": float(np.mean(masses)) if masses else float("nan"),
        "cross_bucket_residual_mass_ci95_prompt_bootstrap": mass_ci_prompt,
        "cross_bucket_fraction_by_offset": {
            k: {"n": len(v), "fraction": float(np.mean(v))} for k, v in sorted(by_offset.items())
        },
    }
    if glue_bucket_ids is not None and n:
        gset = {int(b) for b in glue_bucket_ids}
        p_glue = np.array([r.proposed_bucket in gset for r in records])
        e_glue = np.array([r.emitted_bucket in gset for r in records])
        e_concept = np.array([(r.emitted_bucket is not None and r.emitted_bucket >= 0
                               and r.emitted_bucket not in gset) for r in records])
        cc = np.array([bool(ec and r.emitted_bucket != r.proposed_bucket)
                       for ec, r in zip(e_concept, records)])
        cc_by_prompt: dict[int, list[int]] = {}
        cm_by_prompt: dict[int, list[float]] = {}
        for r, is_cc in zip(records, cc):
            cc_by_prompt.setdefault(r.prompt_idx, []).append(int(is_cc))
            if r.cross_bucket_residual_mass is not None and r.residual_mass_glue is not None:
                # Derivation documented on AuditRecord: mass in concept
                # buckets other than the proposed token's bucket.
                if r.proposed_bucket in gset:
                    m = 1.0 - r.residual_mass_glue
                else:
                    m = r.cross_bucket_residual_mass - r.residual_mass_glue
                cm_by_prompt.setdefault(r.prompt_idx, []).append(float(np.clip(m, 0.0, 1.0)))
        cc_ci = None
        if len(cc_by_prompt) >= 2:
            cc_ci = cluster_bootstrap_ci(
                np.array([float(sum(v)) for v in cc_by_prompt.values()]),
                np.array([float(len(v)) for v in cc_by_prompt.values()]), seed=0)
        cms = [m for v in cm_by_prompt.values() for m in v]
        cm_ci = None
        if len(cm_by_prompt) >= 2:
            cm_ci = cluster_bootstrap_ci(
                np.array([float(sum(v)) for v in cm_by_prompt.values()]),
                np.array([float(len(v)) for v in cm_by_prompt.values()]), seed=0)
        out["glue"] = {
            "n_glue_buckets": len(gset),
            "proposed_in_glue_fraction": float(p_glue.mean()),
            "emitted_in_glue_fraction": float(e_glue.mean()),
            "glue_involved_fraction": float((p_glue | e_glue).mean()),
            "concept_cross_fraction": float(cc.mean()),
            "concept_cross_fraction_ci95_binomial": clopper_pearson(int(cc.sum()), n),
            "concept_cross_fraction_ci95_prompt_bootstrap": cc_ci,
            "residual_mass_concept_other": float(np.mean(cms)) if cms else None,
            "residual_mass_concept_other_ci95_prompt_bootstrap": cm_ci,
            "n_records_with_glue_mass": len(cms),
        }
    return out


def _assert_gpu_resident(model, name: str, allow_cpu_offload: bool) -> None:
    """device_map="auto" silently maps layers to CPU when VRAM is short —
    a 20-100x slowdown with no error. Refuse unless explicitly allowed
    (the K-1 bf16-confirmation path is the legitimate use)."""
    devs = set()
    if hasattr(model, "hf_device_map") and model.hf_device_map:
        devs = {str(d) for d in model.hf_device_map.values()}
    else:
        devs = {str(next(model.parameters()).device)}
    bad = {d for d in devs if not (d.startswith("cuda") or d.isdigit())}
    if bad:
        msg = f"{name} has modules on {sorted(bad)} — silent CPU offload/disk spill."
        if not allow_cpu_offload:
            raise SystemExit(msg + " Free VRAM (or --load-4bit), or pass --allow-cpu-offload "
                                   "for a deliberate offloaded run (expect 20-100x slower).")
        print(f"[WARNING, allowed] {msg}")


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--draft", required=True)
    ap.add_argument("--buckets", default=None)
    ap.add_argument("--glue", default=None,
                    help="glue json from `python -m sideband.glue` (OQ-4). Steering then runs "
                         "in CONCEPT space (glue excluded from gate + posterior, D-7), and audit "
                         "records carry residual_mass_glue. Must derive from the exact --buckets "
                         "file (sha-checked).")
    ap.add_argument("--prompts", default=None, help="jsonl with a 'prompt' field; default: builtin toy prompts")
    ap.add_argument("--n-prompts", type=int, default=50)
    ap.add_argument("--gamma", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--steer", choices=["none", "bucket"], default="none")
    ap.add_argument("--bucket-source", choices=["free_lastp", "free_lastp_sharp", "oracle_nextp"],
                    default="free_lastp",
                    help="free_lastp: posterior = concept-bucket masses of last verified p; "
                         "free_lastp_sharp: one-hot at its argmax (both D-11 free variants); "
                         "oracle_nextp: NON-CAUSAL CEILING (D-2-named) — per-position concept "
                         "posterior of the target's own fresh p_j, target stepped incrementally "
                         "during drafting; exists only to bound the actuator (BLUEPRINT Phase "
                         "0c attribution rider), never deployable")
    ap.add_argument("--steer-gate", choices=["always", "disagree"], default="disagree")
    ap.add_argument("--steer-mech", choices=["argmax", "posterior"], default="posterior")
    ap.add_argument("--beta", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--load-4bit", action="store_true",
                    help="load the TARGET in 4-bit NF4 (+double-quant, bf16 compute) so an "
                         "8B target fits a 12GB card; the draft stays bf16. REGIME NOTE: "
                         "acceptance is then a property of the NF4-quantized target — label "
                         "results accordingly, and expect softer comparability to published "
                         "bf16 numbers.")
    ap.add_argument("--out", default="results/real/audit.jsonl")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow replacing an existing audit at --out "
                         "(results/ files are committed evidence; refusing is the default)")
    ap.add_argument("--resume", action="store_true",
                    help="continue an interrupted run at --out: validates the meta sidecar "
                         "against this invocation, repairs any torn tail, skips completed "
                         "prompts (per-prompt RNG streams make this exact).")
    ap.add_argument("--no-chat-template", action="store_true",
                    help="tokenize prompts as raw text. Default: apply the tokenizer's chat "
                         "template when it has one — instruct models decoded without their "
                         "template run in an off-distribution completion regime, which is "
                         "not the deployment the audit is about.")
    ap.add_argument("--log-generated", action="store_true",
                    help="write each prompt's generated token ids to <out>.gen.jsonl (same "
                         "fsync/repair discipline as the audit records). Used for the OQ-4 "
                         "frequency cross-check against the target-only harvest — NOTE the "
                         "estimand skew: rows here can run past the first EOS (the final "
                         "block lands whole) while harvest_freq truncates at first EOS; "
                         "truncate these rows the same way before comparing counts.")
    ap.add_argument("--no-kv-cache", action="store_true",
                    help="exact-recompute reference path (no per-prompt KV caches): "
                         "(gamma+1)*prefix_len token-positions per block instead of "
                         "~2*gamma+2; same estimand. Used by the cached-vs-uncached "
                         "A/B pre-registered in WHY_THIS_DIES K-1.")
    ap.add_argument("--skip-preflight", action="store_true",
                    help="skip the fail-closed GPU/disk/reboot preflight (not recommended)")
    ap.add_argument("--allow-buckets-mismatch", action="store_true",
                    help="load a buckets file whose model/n_tokens disagree with --target")
    ap.add_argument("--allow-cpu-offload", action="store_true",
                    help="permit device_map to place layers on CPU (bf16-confirmation path); "
                         "otherwise refused as a silent 20-100x slowdown")
    args = ap.parse_args()

    if args.resume and args.overwrite:
        raise SystemExit("--resume and --overwrite are mutually exclusive")

    from ._preflight import preflight

    # --skip-preflight disarms the GATE but still measures: the overridden
    # runs are exactly the ones whose box state most needs recording.
    preflight_report = preflight(
        disk_path=Path(args.out).resolve().anchor or ".",
        force=args.skip_preflight,
    )

    tok = transformers.AutoTokenizer.from_pretrained(args.target)
    use_chat = (not args.no_chat_template) and tok.chat_template is not None
    # torch_dtype is set in BOTH branches: without it, bnb historically casts
    # the non-quantized modules (embeddings, norms, lm_head) to fp16, making
    # the actual numerics transformers-version-dependent and the meta label a
    # lie. With it, NF4 weights + bf16 everything else, version-stable.
    target_kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if args.load_4bit:
        target_kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    target = transformers.AutoModelForCausalLM.from_pretrained(args.target, **target_kwargs).eval()
    draft = transformers.AutoModelForCausalLM.from_pretrained(
        args.draft, torch_dtype=torch.bfloat16, device_map="auto"
    ).eval()
    _assert_gpu_resident(target, "target", args.allow_cpu_offload)
    _assert_gpu_resident(draft, "draft", args.allow_cpu_offload)

    # Load-bearing assumption, enforced: ONE tokenizer drives both models.
    # spec_step compares p and q at the same token ids; a same-size but
    # different tokenizer would run and produce silent garbage.
    tok_draft = transformers.AutoTokenizer.from_pretrained(args.draft)
    if target.config.vocab_size != draft.config.vocab_size:
        raise SystemExit(
            f"vocab_size mismatch: target {target.config.vocab_size} vs draft "
            f"{draft.config.vocab_size} — the pair cannot spec-decode."
        )
    if tok.get_vocab() != tok_draft.get_vocab():
        raise SystemExit(
            "target and draft tokenizers disagree (same size, different vocab): "
            "spec decoding needs one shared tokenizer."
        )

    def encode_prompt(p: str):
        if use_chat:
            return tok.apply_chat_template(
                [{"role": "user", "content": p}],
                add_generation_prompt=True, return_tensors="pt",
                date_string=PINNED_DATE,
            )
        return tok(p, return_tensors="pt").input_ids

    if args.prompts:
        prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    else:
        prompts = [
            "Explain how a refrigerator keeps food cold.",
            "Write a short story about a lighthouse keeper.",
            "Summarize the causes of the French Revolution.",
        ] * ((args.n_prompts // 3) + 1)
    prompts = prompts[: args.n_prompts]

    buckets = load_buckets(args.buckets, target.config.vocab_size,
                           expect_model=args.target, allow_mismatch=args.allow_buckets_mismatch)

    def _sha256(path: str | None) -> str | None:
        if path is None or not Path(path).exists():
            return None
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    steer_map = glue_mask = None
    concept_C = None
    glue_ids, glue_data = load_glue(args.glue, expect_buckets_sha256=_sha256(args.buckets),
                                    allow_mismatch=args.allow_buckets_mismatch)
    if glue_ids is not None:
        if buckets is None:
            raise SystemExit("--glue requires --buckets")
        if (buckets < 0).any():
            # The residual_mass_concept_other derivation assumes zero mass on
            # unbucketed tokens (see AuditRecord); a partial-coverage buckets
            # file would silently inflate the concept-other estimand.
            raise SystemExit(f"--glue requires a buckets file covering every token id "
                             f"({int((buckets < 0).sum())} of {buckets.shape[0]} unbucketed).")
        steer_map, glue_mask, concept_C = glue_remap(buckets, glue_ids)
        print(f"[glue] {len(glue_ids)} glue buckets excluded; C={concept_C} concept buckets")

    # Per-prompt RNG streams (dists.spawn): child i depends only on (seed, i),
    # never on the prompt count or on other prompts' realized trajectories —
    # this is what makes --resume exact and cross-arm comparisons prompt-paired.
    gens = spawn(args.seed, len(prompts))

    out_path = Path(args.out)
    stats_path = out_path.with_suffix(".stats.jsonl")
    meta_path = out_path.with_suffix(".meta.json")
    summary_path = out_path.with_suffix(".summary.json")
    gen_path = out_path.with_suffix(".gen.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _git(cmd: list[str]) -> str:
        r = subprocess.run(["git", *cmd], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        if r.returncode != 0:
            # A failed git (non-repo deployment, path outside the repo) must
            # surface as "unknown", never as a clean-looking answer.
            raise RuntimeError(f"git {cmd[0]} failed: {r.stderr.strip()}")
        return r.stdout.strip()

    def _git_commit() -> str:
        try:
            dirty = "-dirty" if _git(["status", "--porcelain"]) else ""
            return (_git(["rev-parse", "HEAD"]) or "unknown") + dirty
        except Exception:
            return "unknown"

    def _buckets_file_git_clean() -> bool | None:
        if args.buckets is None:
            return None
        try:
            return _git(["status", "--porcelain", "--", str(Path(args.buckets).resolve())]) == ""
        except Exception:
            return None  # indeterminate, not "clean"

    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    completed: set[int] = set()

    if args.resume:
        if not (out_path.exists() and meta_path.exists()):
            raise SystemExit(f"--resume needs an existing {out_path} and {meta_path}")
        if summary_path.exists():
            raise SystemExit(f"{summary_path} exists — that run completed; nothing to resume "
                             "(use a new --out, or --overwrite to redo it).")
        old_meta = json.loads(meta_path.read_text())
        mismatches = [f"{k}: {old_meta.get(k)!r} != {getattr(args, k)!r}"
                      for k in RESUME_IDENTITY_ARGS if old_meta.get(k) != getattr(args, k)]
        cur_ids_sha = (hashlib.sha256(json.dumps(encode_prompt(prompts[0])[0].tolist()).encode()).hexdigest()
                       if prompts else None)
        for k, cur in (("buckets_sha256", _sha256(args.buckets)),
                       ("glue_sha256", _sha256(args.glue)),
                       ("prompts_sha256", _sha256(args.prompts)),
                       # Pins the TOKENIZATION, not just the prompt text: a
                       # transformers upgrade or template change between
                       # segments would silently pool two encoding regimes.
                       ("templated_prompt0_ids_sha256", cur_ids_sha)):
            if old_meta.get(k) != cur:
                mismatches.append(f"{k}: {old_meta.get(k)!r} != {cur!r}")
        if mismatches:
            raise SystemExit("--resume refused, invocation differs from the original run:\n  - "
                             + "\n  - ".join(mismatches))
        if old_meta.get("git_commit") != _git_commit():
            print(f"[resume WARNING] code version changed since the original segment: "
                  f"{old_meta.get('git_commit')} -> {_git_commit()} — the artifact mixes code versions.")
        completed, dropped = repair_partial_outputs(out_path, stats_path,
                                                    records_expected=args.buckets is not None,
                                                    gen_path=gen_path if args.log_generated else None)
        meta = old_meta
        meta.setdefault("run_ids", [meta.get("run_id")])
        meta["run_ids"].append(run_id)
        meta["resumed"] = True
        meta.setdefault("segments", []).append({
            "run_id": run_id, "git_commit": _git_commit(),
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        })
        _atomic_write_text(meta_path, json.dumps(meta, indent=2, sort_keys=True))
        print(f"[resume] {len(completed)} prompts already complete; "
              f"dropped {dropped} torn/in-flight audit lines; continuing as run {run_id}")
    else:
        if out_path.exists() and not args.overwrite:
            raise SystemExit(
                f"{out_path} already exists; results/ files are committed evidence. "
                "Pass --resume to continue it, --overwrite to replace it, or use a distinct --out."
            )
        # Fresh (or overwrite) run: clear every sidecar of a previous run NOW
        # so a crash can never leave a mixed meta(B)+summary(A) state.
        summary_path.unlink(missing_ok=True)
        stats_path.unlink(missing_ok=True)
        gen_path.unlink(missing_ok=True)
        if args.load_4bit:
            import bitsandbytes  # noqa: F401  (version for the regime record)

            bnb_version = bitsandbytes.__version__
        else:
            bnb_version = None
        meta = {
            **redact_args(vars(args)),
            "run_id": run_id,
            "run_ids": [run_id],
            "rng_scheme": "per-prompt spawn(seed, n)[i] (dists.spawn; resume-stable, prompt-paired)",
            "target_load": "nf4-double-quant-bf16compute" if args.load_4bit else "bf16",
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "bitsandbytes_version": bnb_version,
            "numpy_version": np.__version__,
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_deterministic": False,
            "verification_note": "CUDA/bnb kernels are not bitwise deterministic; verification "
                                 "of this artifact = re-run + CI overlap, never byte-diff.",
            "git_commit": _git_commit(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "preflight": preflight_report,
            "chat_template_used": use_chat,
            "date_string_pinned": PINNED_DATE if use_chat else None,
            "templated_prompt0_ids_sha256": (
                hashlib.sha256(json.dumps(encode_prompt(prompts[0])[0].tolist()).encode()).hexdigest()
                if prompts else None
            ),
            "buckets_sha256": _sha256(args.buckets),
            "buckets_k": (json.loads(Path(args.buckets).read_text()).get("k") if args.buckets else None),
            "buckets_model": (json.loads(Path(args.buckets).read_text()).get("model") if args.buckets else None),
            "buckets_file_git_clean": _buckets_file_git_clean(),
            "glue_sha256": _sha256(args.glue),
            "glue_n_buckets": (len(glue_ids) if glue_ids is not None else None),
            "glue_rule": (glue_data.get("rule") if glue_data else None),
            "concept_C": concept_C,
            "prompts_sha256": _sha256(args.prompts),
        }
        _atomic_write_text(meta_path, json.dumps(meta, indent=2, sort_keys=True))
        out_path.write_text("")  # truncate/create the audit jsonl

    import contextlib

    with contextlib.ExitStack() as stack:
        f = stack.enter_context(out_path.open("a"))
        sf = stack.enter_context(stats_path.open("a"))
        gf = stack.enter_context(gen_path.open("a")) if args.log_generated else None
        for i, prompt in enumerate(prompts):
            if i in completed:
                continue
            t0 = time.time()
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
            ids = encode_prompt(prompt)
            out_ids, records, stats = spec_decode_prompt(
                target, draft, ids, args.gamma, args.max_new, args.temperature, gens[i],
                bucket_of_token=buckets,
                steer_beta=args.beta if args.steer == "bucket" else 0.0,
                steer_source=args.bucket_source, steer_gate=args.steer_gate,
                steer_mech=args.steer_mech, prompt_idx=i, run_id=run_id,
                use_kv_cache=not args.no_kv_cache,
                steer_bucket_of_token=steer_map, glue_mask=glue_mask,
            )
            for r in records:
                f.write(r.to_json() + "\n")
            dt = time.time() - t0
            stats_line = {
                "prompt_idx": i, "run_id": run_id, "seconds": round(dt, 2),
                "peak_vram_gb": (round(torch.cuda.max_memory_allocated() / 2**30, 2)
                                 if torch.cuda.is_available() else None),
                **stats,
            }
            # ORDERING IS LOAD-BEARING: records (and the gen line, when on)
            # are fully fsynced BEFORE the stats line leaves the userspace
            # buffer. A stats line on disk is therefore a guarantee its
            # records/gen line are on disk; the inverse crash (records
            # durable, stats lost) re-runs the prompt and repair drops the
            # orphans. Do not "simplify" to one fsync.
            f.flush(); os.fsync(f.fileno())
            if gf is not None:
                gf.write(json.dumps({"prompt_idx": i, "run_id": run_id,
                                     "generated_ids": out_ids[0, ids.shape[1]:].tolist()}) + "\n")
                gf.flush(); os.fsync(gf.fileno())
            sf.write(json.dumps(stats_line) + "\n")
            sf.flush(); os.fsync(sf.fileno())
            print(f"[{i + 1}/{len(prompts)}] acc={stats['acceptance_rate']:.3f} "
                  f"rej={len(records)} {dt:.1f}s", flush=True)

    # Summary is assembled from DISK (stats jsonl), not RAM, so it covers
    # prompts completed by earlier segments of a resumed run.
    per_prompt = [json.loads(l) for l in stats_path.read_text().splitlines()]
    per_prompt.sort(key=lambda d: d["prompt_idx"])
    acc = float(np.mean([s["acceptance_rate"] for s in per_prompt])) if per_prompt else float("nan")
    all_lines = out_path.read_text().splitlines()
    if buckets is not None:
        # Cross-file invariant: one audit record per rejection. A mismatch
        # means records were lost or duplicated — refuse to summarize
        # corrupted evidence (run --resume to repair, then investigate).
        expected = sum(int(s["n_proposed"]) - int(s["n_accepted"]) for s in per_prompt)
        if expected != len(all_lines):
            raise SystemExit(f"record-count invariant violated: stats imply {expected} "
                             f"rejections, audit jsonl holds {len(all_lines)} lines.")
    if args.log_generated:
        gen_prompts = {json.loads(l)["prompt_idx"] for l in gen_path.read_text().splitlines()}
        if gen_prompts != {s["prompt_idx"] for s in per_prompt}:
            raise SystemExit("gen-file invariant violated: .gen.jsonl prompt set differs "
                             "from completed stats lines (run --resume to repair).")
    summary: dict = {"run_id": run_id, "run_ids": meta.get("run_ids", [run_id]),
                     "mean_acceptance_rate": acc,
                     "n_prompts_completed": len(per_prompt),
                     "n_rejections_logged": len(all_lines),
                     "per_prompt_stats": per_prompt}
    if buckets is not None and all_lines:
        recs = [AuditRecord(**json.loads(l)) for l in all_lines]
        summary["audit"] = summarize_audit(recs, glue_bucket_ids=glue_ids)
    _atomic_write_text(summary_path, json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps({k: v for k, v in summary.items() if k != "per_prompt_stats"}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

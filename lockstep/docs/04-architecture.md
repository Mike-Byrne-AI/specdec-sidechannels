# Architecture blueprint

## Layer diagram

```text
            +--------------------------------------------------+
  archive   |  .lsa container: manifest (JSON) + coded payload |
            |  pins: profile id, model hash, coder constants,  |
            |  original/payload sha256                          |
            +-------------------------▲------------------------+
                                      |
            +-------------------------+------------------------+
  codec     |  encode/decode loop (codec.py) — model-agnostic  |
            +------------▲-----------------------▲-------------+
                         |                       |
            +------------+----------+  +---------+-------------+
  model     |  PredictiveModel      |  |  arithmetic coder     |
  surface   |  v0: integer adaptive |  |  (rac.py) 32-bit WNC, |
  (N1..N7   |  lsp1: LLM adapter    |  |  integer-only         |
  live here)|  + logit grid         |  |  TRUST BASE           |
            |  + safeguard stream   |  +-----------------------+
            +-----------------------+
                         |
            +------------▼--------------------------------------+
  ground    |  conformance vectors + envprobe + (TP-4) GPU     |
  truth     |  determinism harness — "deterministic" is tested |
            +---------------------------------------------------+
```

## The two-tier trust model

**Tier 0 (trust base):** rac.py, quantize_weights, container.py.
Integer-only, stdlib-only, spec-frozen. A bug here is a format incident.

**Tier 1 (model surface):** everything that produces probabilities.
v0's adaptive model is Tier-1 code that happens to be integer, so it
inherits Tier-0 guarantees. The lsp1 LLM adapter will not — it gets
three compensating mechanisms instead:

1. **Grid** — logits/probabilities quantized to the lsp grid; drift
   below half a step is absorbed (F-2 measures this at 200/200 for
   eps=1e-11 on a 2^15 grid; the honest boundary sits near half a grid
   step, ~1.5e-5 in probability space). Dated note (2026-10-18): F-21, an
   erratum to F-2, moves that boundary to the point where the order of the
   largest-remainder residues changes, far below half a step for V=128.
2. **Safeguard stream** (TP-2, after PA-7) — encoder records, for the
   rare positions where the decoder's recomputed grid cell could
   plausibly differ, a small correction record; decode applies it before
   coding. Overhead is the drift rate times record size — measure, don't
   guess (E-004).
3. **Conformance** — a runtime doesn't "support lsp1" because its README
   says so; it reproduces the vectors or it doesn't.

## Decode profile = the exact arithmetic, written down

A profile (specs/decode-profile-v0.md) pins: coder constants, alphabet,
model class and every parameter, quantizer rule, context policy, and the
vector set that proves conformance. Profiles are append-only: lsp0 today,
lsp1 with the LLM adapter, lsp2 when the safeguard stream lands. A
container names exactly one profile.

## Failure taxonomy (already implemented)

| Check | Fails when | Meaning |
|---|---|---|
| payload sha256 | bytes changed after pack | storage/transport damage |
| decode raises CoderError | model desync mid-stream | nondeterminism (N1–N7) or wrong model |
| original sha256 | decode "succeeded" but bytes differ | silent desync — the nightmare case, made loud |

## Performance posture

The reference implementation is honest-slow (~32 KiB/s in pure Python,
run_002). That is a feature at this stage: it keeps the trust base
readable and portable. Speed lives in future work: a C/Rust port of
rac.py *verified against the same vectors*, and llama.cpp doing the
model math. Never trade auditability of Tier 0 for throughput.

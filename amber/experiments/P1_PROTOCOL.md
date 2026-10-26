# P1 — Real greedy divergence rate (OQ-1) — pre-registration

Frozen 2026-08-29 before any generation. Provenance: amber F-1 (the synthetic
rate curve this replaces), D-6 (four baselines mandatory), WHY_THIS_DIES K-2,
sideband Phase 0a (prompt set, hf harness pattern), lockstep F-8 (throughput is
measured, never projected).

## Question
For a tokenizer-matched Llama pair on this box, at what fraction of positions
does the DRAFT's greedy token differ from the TARGET's greedy output, and does
amber's v0 format (gaps+ranks, draft-only decode) beat a content coder on the
same text?

## Setup
- Target: `meta-llama/Llama-3.2-3B` (base), bf16, greedy, batch=1, KV cache,
  max_new=256, EOS stops. Draft: `meta-llama/Llama-3.2-1B` (base), bf16,
  teacher-forced, full-vocab stable rank per generated position. Both base
  models — an instruct draft against a base target would confound alignment
  with tuning ([withheld: a private repository's lesson (plan section 3); see WITHHELD.md]: match the pair on everything but size).
- Prompts: sideband `data/prompts.jsonl`, first 200 of 210 (3 families x 70
  topics, interleaved, no RNG); sha256 pinned in `results/p1/prompts.json`.
- Content definition = what the target GENERATED. The target is also
  teacher-forced over its own output (self-consistency); the rate at which
  its forward-pass argmax disagrees with its generated token is reported and
  must be ~0 — a nonzero rate is the KV-cache-vs-full-forward kernel
  difference (P2 F-5's N2 class) and would mean the ENCODER must define
  content by forward-pass semantics, not by generate().

## Metrics (per token of generated text; headers excluded)
- divergence rate (draft rank != 1), overall / per family / per 64-position
  bucket / per-prompt spread (p10/p50/p90).
- amber_v0 bits: exact Elias-gamma bits codec.encode would emit.
- ideal regime-A bound: H2(p_div) + p_div * H(empirical rank | correction).
- AC-under-draft: -mean log2 q_draft(true) (regime-B baseline; draft at decode).
- zstd -19, lzma -9, zlib -9 on the decoded UTF-8 text, bits per token.
- raw: log2(128256) = 16.97.
- draft near-tie mass at the P2 thresholds (0.142 / 0.465 / 0.93).

## Bands
- **PASS**: amber_v0 < zstd19 AND amber_v0 < AC-under-draft. The asymmetric
  format earns its existence on real target-generated text.
- **AC-ONLY**: amber_v0 < AC-under-draft but >= zstd19. The draft-relative
  structure is real, but a content coder wins; the coder upgrade (lockstep
  rac, ~1.4 bits/token on synthetic) and hints (OQ-4) are the remaining
  levers, and the kill is deferred to them, not dodged.
- **K-2 KILL**: amber_v0 >= zstd19 AND amber_v0 >= AC-under-draft. The
  compression story dies for this pair; the attestation primitive (F-2)
  survives on its own.
- Self-consistency < 99.9% => recorded as its own finding before any rate is
  interpreted; the content definition question (above) must be settled.

## Stop conditions
- Generation producing >10% empty/EOS-immediate continuations (base model
  refusing the instruction-style prompts) => report, and re-run with a plain
  text-continuation prompt set; do not cherry-pick prompts post hoc.
- Any NaN logit => refuse to write (capture rule).

## Commands
```
python -m amber.real.divergence all            # generate, then draft + target_selfcheck ranks; resumable
python experiments/p1_divergence.py
```

## Post-run note (2026-08-29, after F-8; does not change the run)
The band table was not complementary: the outcome amber >= AC-under-draft AND
amber < zstd19 (which is what happened, by 0.0015 bits/token on the AC side)
matched no band. Recorded as a protocol defect in F-8. A future protocol
version should split PASS into PASS-BOTH / PASS-ZSTD-TIE-AC and treat the AC
comparison as a signed margin with a pre-declared noise floor (per-prompt
bootstrap), not a strict inequality.

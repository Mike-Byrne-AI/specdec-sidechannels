# P4 — Real archives: encode with the draft, decode with the draft alone — pre-registration

Frozen 2026-08-30 before any archive was written. Provenance: F-8 (the P1
stream this archives), F-10/D-8 (the fp32-class decoder contract this
tests directly), F-9 (gamma default), lockstep D-9 (dual hash: content
digest makes a silent desync a typed failure), P2/P3 protocols.

## Question
Does a real amber archive — header pinning the draft (model id, snapshot,
dtype) + prompt ids + gamma payload — decode BYTE-EXACTLY with the draft
alone when the draft is replayed incrementally (KV cache, one token at a
time) rather than teacher-forced as at encode time, and how does that depend
on the decoder's dtype? F-10 predicted this from dumps; this measures it.

## Setup
- Content: results/p1 generated tokens (Llama-3.2-3B greedy, 200 prompts,
  48,958 tokens). The target is never loaded here.
- Encoder: Llama-3.2-1B base, **cuda fp32**, ONE teacher-forced full forward
  per prompt (no KV cache), full-vocab stable rank (value desc, index asc),
  top-2 gap, canonical top-m ids. coder=gamma (F-9/D-8 default), tie_margin
  0 (escape off, D-8), max_rank 64 (beyond: X raw id).
- Decoder arms, all incremental with KV cache, batch 1: cuda_fp32 (the
  contract), cuda_bf16, cuda_fp16; cpu_fp32 on the first 24 prompts (slow).
  Canonical top-128 per step; A -> order[0], C -> order[rank-1], X -> id.
- Every archive carries content_sha (sha256 of the generated ids) and the
  decoder verifies it: a desync that reaches the end is a ValueError, never a
  silently wrong file. Experiment mode also stops at the first mismatch
  (truth known) and records its position and symbol class.

## Metrics
- Per arm: archives byte-exact (count / 200), first-desync position
  distribution, first-desync symbol class (A / C rank r / X), tokens decoded
  before first desync per archive.
- Rate: payload bits/token and TOTAL archive bits/token including the JSON
  header with prompt ids (the honest file-size number; prompts average ~30
  tokens).
- Throughput: decoder tokens/s per arm (batch 1, KV) — the decode-side cost
  of the fp32 contract, measured, next to the encode-side teacher-forced rate.

## Pre-registered predictions (from F-10's per-rank rates on P1's rank mix)
- cuda_fp32: >= 99% of archives byte-exact. Any failure is investigated
  first as the KV-cache-vs-full-forward kernel difference at fp32 (F-8's
  0.33% was bf16); an fp32 desync with encoder gap > 1e-3 is a pipeline bug.
- cuda_bf16: ~1 desync per 170 tokens => ~76% of 245-token archives fail
  (band 50-90%); cuda_fp16: ~1 per 1070 => ~20% fail (band 8-35%).
- cpu_fp32: same as cuda_fp32 (F-7: 1 flip / 49k cross-device).
Outside these bands => F-10's transfer from teacher-forced text to
target-generated text is wrong in a way to be characterised, not tuned.

## Stop conditions
- Encoder self-check: decoding each archive's SYMBOL stream (no model) must
  reproduce the encoder's symbols exactly before any model decode runs.
- Any NaN logit => refuse to write (capture rule).

## Commands
```
python experiments/p4_real_archive.py encode
python experiments/p4_real_archive.py decode --arm cuda_fp32 --arm cuda_bf16 --arm cuda_fp16
python experiments/p4_real_archive.py decode --arm cpu_fp32 --n-prompts 24
python experiments/p4_real_archive.py report
```

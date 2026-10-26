# P5 — Binary format v3 + prompt coded with the draft (OQ-7) — pre-registration

Frozen 2026-08-30 before any v3 archive was written. Provenance: F-11/D-9
(the 551 B JSON header and the "header is the file size" finding), F-10/D-8
(fp32 contract; the prompt segment adds coded depth at real-text ranks),
D-6 (baselines per archive), lockstep D-9 (damage detection, not forgery).

## Question
How small does a REAL, self-describing, verifiable archive of a ~250-token
session get, once the header is binary and the prompt is coded with the
draft instead of stored as ids — and does the fp32 contract still hold when
the coded stream includes the prompt segment (real-text ranks, deeper than
target-generated content)?

## Format v3 (src/amber/binformat.py; kind byte "hfb")
    AMBR | u8 ver=3 | u8 kind=2 | u8 coder | u8 dtype | flags u8
    varint(len)+utf8 model_id | [snapshot 20 B if flag] | fingerprint 8 B
    varint vocab, max_rank, tie_topm | [f32 tie_margin if coder=rac1]
    varint first_token, prompt_len, length, n_corrections, payload_bits
    payload_sha 8 B | content_sha 8 B | header_sha 8 B (over all prior bytes)
    payload
- ONE payload stream, two segments: prompt tokens 1..P-1 (the first token is
  carried raw — no context to predict it from), then the generated tokens.
  Same {A, C, X} grammar against the draft in both; content_sha covers the
  full reconstructed sequence. Digests stay 8 B (damage detection posture);
  all field costs are reported so trims are visible decisions, not defaults.
- Fixed cost accounting, computed BEFORE the run: ~106 B with snapshot
  (~86 B without) = 3.46 (2.81) bits per generated token at 245 tokens.
  This is the floor of this design; the finding must state it as such.

## Setup
Same content and encoder as P4 (P1's 200 prompts, Llama-3.2-1B base, cuda
fp32 teacher-forced — one forward per prompt now scoring positions 1..L).
Decode: cuda_fp32, all 200 archives, incremental KV from the first token
(prompt segment decoded, not fed), stop at first mismatch with truth known.

## Metrics
- File sizes: v2 JSON (P4's, measured) vs v3 binary, total bits per
  generated token and per all tokens; header breakdown by field group
  (framing/model pin/digests/ints/prompt payload/content payload).
- Prompt coding: bits per prompt token under the draft (rank-coded), vs raw
  varint ids and raw 17-bit ids; prompt-segment rank distribution.
- D-6 per-archive baselines on the same text: zstd-19 per archive on full
  text (7.28 bits/gen-token at P4), zstd-19 concatenated (3.94), raw.
- Crossover curve: total bits/token vs archive length L (analytic from the
  measured fixed cost + measured payload rate), reporting the L where v3
  beats zstd-19-concatenated and where the header falls under 10% of the file.
- Byte-exactness: archives exact / 200 under cuda_fp32.

## Pre-registered predictions
- v3 total: 4.0-4.6 bits per generated token with snapshot (payload 0.44 +
  prompt ~0.3-0.7 + fixed ~3.5); 5-7x smaller than the JSON v2 file; still
  ABOVE zstd-19-concatenated (3.94) at L=245 — the point of the crossover
  curve is to say at what L that flips, not to pretend it flips at 245.
- Prompt coding: 6-14 bits per prompt token (instruction text under a base
  1B from BOS is mid-rank); beats 17-bit raw always; varint raw (~14) is the
  band's upper edge.
- fp32 decode: 200/200 byte-exact including prompt segments (F-10: fp32
  order exact to rank 64; deeper prompt ranks are X). Any failure =>
  investigated as a format bug first, contract question second.

## Stop conditions
- Symbol self-check (payload -> symbols == encoder's symbols) per archive
  before any model decode; NaN logits refuse to write.

## Commands
```
python experiments/p5_binformat.py encode
python experiments/p5_binformat.py decode
python experiments/p5_binformat.py report
```

# P6 — Session-level archives: one header, many turns (OQ-7) — pre-registration

Frozen 2026-08-30 before any session archive was written. Provenance: F-12/
D-10 (the 97 B floor and the rate law 917/L + 0.455 this amortises), F-11
(fp32 contract), D-2 (everything that shapes the code must be decoder-
visible — session history is, so both context modes are legal formats).

## Question
A session archive packs k turns (prompt_t, gen_t) under ONE model pin and
digest set. How does the file rate fall with k, and does letting the draft
condition across turns help or hurt on THIS data — where the caveat is
structural: P1's target generated every turn independently, so cross-turn
context is information the target never saw. Shared-context coding of
independently-generated turns is expected to be biased AGAINST amber; the
faithful shared-context measurement needs true multi-turn generation
(future run, belongs with long-horizon).

## Format v4 addition (kind byte 3, src/amber/binformat.py)
Same frame, pin, and digest layout as v3; then:
    u8 ctx_mode (0 = reset per turn, 1 = shared history)
    varint n_turns; per turn: varint prompt_len, gen_len,
    [varint first_token per turn if ctx_mode 0; else one first_token]
One payload stream over every coded position; content_sha over the full
session token sequence. ctx_mode 0 replays each turn from its own first
token (KV reset); ctx_mode 1 replays the whole session in one context.

## Setup
P1's 200 prompts+generations in row order, grouped into sessions of k in
{2, 4, 8, 16} (plus k=1 = v3 baseline from F-12). Encoder Llama-3.2-1B base
cuda fp32; ctx_mode 0 scores each turn independently (as P5); ctx_mode 1
scores the whole session teacher-forced in 512-token KV chunks (chunked vs
full forward is inside the measured fp32 contract, F-11: 0 desyncs across
kernel paths). gamma coder, max_rank 64.

## Metrics
- Total file bits per generated token vs k, both modes; breakdown fixed /
  per-turn table / prompt payload / content payload.
- Per-turn-index rates under ctx_mode 1 vs 0: prompt bits/token and content
  bits/token for turn 1 vs turns 2+ (does history help the draft?).
- Baselines per k: k separate v3 files (the "many headers" comparison),
  zstd-19 on each session's full text, zstd-19 concatenated over everything,
  raw. Byte-exactness: decode ALL k=8 sessions draft-only at cuda fp32 in
  ctx_mode 1 (the new replay path), and the first 8 in ctx_mode 0.

## Pre-registered predictions
- ctx_mode 0, k=8: 1.4-1.9 bits/gen-token (content 0.455 + prompt 0.575 +
  amortised header+table ~0.5); k=16: 1.2-1.7. Monotone falling in k.
- Session file vs k separate v3 files at k=8: 25-45% smaller.
- ctx_mode 1 vs 0 at k=8: prompt payload for turns 2+ FALLS (band 0.2-0.6
  of mode-0's per-token cost — repeated instruction style is predictable);
  content payload for turns 2+ moves within [0.8x, 1.3x] of mode 0 — sign
  genuinely unknown, biased against amber by construction (above).
- Decode: 25/25 (mode 1) and 8/8 (mode 0) byte-exact at fp32. Any failure
  is a format/replay bug first (chunked-encode vs incremental-decode is new
  surface), contract question second.

## Stop conditions
- Symbol self-check per session before any model decode; NaN logits refuse.
- GPU stages are shard-resumable and short; if the box is busy they can be
  rerun without loss.

## Commands
```
python experiments/p6_sessions.py encode
python experiments/p6_sessions.py decode
python experiments/p6_sessions.py report
```

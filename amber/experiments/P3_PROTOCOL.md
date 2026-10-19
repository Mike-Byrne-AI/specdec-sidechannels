# P3 — Coder upgrade (lockstep rac) and the near-tie escape (Phase 2b) — pre-registration

Frozen 2026-08-30 before the rac coder touched any P1 data. Provenance: amber
F-8 (the 0.474 / 0.472 tie this targets), BLUEPRINT "Coder upgrade path" and
Phase 2b, lockstep rac (integer WNC, D-7 import), P1_PROTOCOL's post-run note
(signed margin + noise floor instead of strict inequality), PMATIC's mismatch
warning (adaptive coders cascade on any context the decoder cannot reproduce).

## Two questions
1. **Coder**: does an adaptive integer arithmetic coder over the (flag, rank)
   stream, with contexts that are functions of the CODED SYMBOL HISTORY and
   position only (never of logit values), beat AC-under-draft on held-out
   target-generated text? Contexts of that kind are exactly reproducible by
   any decoder whose draft is rank-stable (D-5) — no new determinism ask.
2. **Escape**: what does a decoder-blind near-tie escape cost, and does it
   make a lower-precision decoder byte-exact against an fp32 (or batch-1)
   encoder on the P2 dumps?

## Format v2 (src/amber/rac_codec.py, codec.py VERSION 2)
Per position one flag symbol from {A, C, T, X}, coded adaptively:
- **A** agree: rank 1 and encoder gap >= theta. Decoder emits its argmax.
- **C** correction: 2 <= rank <= R, gap-not-tie. Rank coded as a log2 bucket
  (adaptive) + mantissa (adaptive for <= 4 bits, uniform beyond). Decoder
  emits its order[rank-1].
- **T** tie escape: encoder gap < theta AND rank <= m. Codes the token's slot
  among the top-m tokens sorted by INDEX (uniform log2 m bits). Decoder
  sorts its own top-m set by index. Robust to any reordering inside the top-m
  set; breaks only if the SET changes.
- **X** raw: rank > R. Token id in ceil(log2 V) uniform bits. Always robust.
Flag context = (previous flag, position bucket t>>6 capped at 3). theta, m,
R are header fields; `payload_sha` (sha256[:16] of the payload) is added so
any payload corruption is a typed failure before replay — closes the D-7
"payload digest" item. The v0 gamma path is kept bit-identical (coder="gamma")
so F-1/F-8 numbers stay comparable.

## Data and split
P1 run (results/p1): 200 prompts, 48,958 tokens, Llama-3.2-3B -> 1B base.
- **Tuning set**: prompt rows 0-99. Model hyperparameters (increment,
  rescale limit, context choice) may be chosen here and ONLY here.
- **Held-out**: rows 100-199. Every rate in the finding is a held-out rate;
  tuning-set rates are shown labelled and never quoted alone.
- Two stream modes, both reported: `per_prompt` (each prompt an independent
  archive: coder learning cost paid 100 times; the short-document limit) and
  `concatenated` (models persist across prompts; the long-archive limit).
  Elias-gamma is stateless, so v0 is identical in both.

## Metrics (bits per token of target-generated text; headers excluded)
- amber_v0 (gamma), rac1 (theta=0), rac1 at theta in {0.142, 0.465, 0.93}
  with m in {2, 4}, R = 64; D-6 baselines recomputed on the same split:
  AC-under-draft, zstd-19 / lzma / zlib-9 on the split's text, raw log2 V.
- **Noise floor**: per-prompt bootstrap (1000 resamples, seed 0) of the
  held-out difference (rac1 - AC-under-draft) in bits/token; 95% CI.
- Escape price = rac1(theta, m) - rac1(0) on held-out, per stream mode; and
  the alternative's price: fp32-mandated decode costs 7361/2015 = 3.65x the
  bf16 draft replay time on this box (P2 F-7 throughputs, batch 1).

## Bands (question 1, concatenated mode, held-out)
- **PASS**: rac1(0) < AC-under-draft and the bootstrap 95% CI of the
  difference excludes 0.
- **TIE**: CI includes 0.
- **LOSE**: rac1(0) > AC-under-draft with CI excluding 0. Then the only
  remaining lever is value-dependent context (q_max / gap buckets), which is
  a grid-crossing hazard (F-6/F-7: 22-41% at 1e-3 even at fp32); it is
  measured here for its GAIN only (variant `rac1_qctx`, in-sample-safe
  because it uses the same tuning split) and is NOT adopted into the format
  by this protocol regardless of size.
Per-prompt mode is reported alongside; it is expected to be worse (learning
cost on 245-token documents) and does not decide the band.

## Robustness simulation (question 2; experiments/p2b_escape_robustness.py)
P2 Llama-3.2-1B-Instruct dumps (results/p2_llama32, 49,152 positions, top-256
per arm; true token = corpus next token). Symbol stream is built under the
ENCODER arm with the v2 classifier; each position is then resolved under the
DECODER arm's top-256; a **desync** is a position whose resolved token differs
from the true token (with an adaptive coder one desync kills the rest of the
archive, so the count, not the rate, is the number). Coverage: positions with
encoder rank > 256 are X (always robust) and positions whose decoder-side
resolution needs a rank beyond 256 are counted as `unresolvable` (reported,
not hidden).
- Encoder arms: cpu_fp32 (the reference) and cuda_bf16_b1 (the serving case:
  an archive written by a batch-1 bf16 server).
- Decoder arms: cuda_fp32_b1, cuda_fp16_b1, cuda_bf16_b1, cuda_bf16_b8,
  cuda_int8_b1, cuda_nf4_b1.
- Variants: theta in {0, 0.142, 0.465, 0.93}, m in {2, 4}, R = 64; desyncs
  attributed by symbol class (A: top-1 flip beyond theta; T: top-m set
  change; C: order change at rank r, reported as a per-rank curve).
- Also computed (analytic, no codec support): a `set-coded` C variant where
  rank r is coded as (bucket b, slot among the top-2^(b+1) set by index) —
  robust iff that SET is stable; price +1 bit per C symbol.
- **Bands**: (i) fp32-encoded, fp16-decoded at theta=0.142 and fp32-decoded
  at any theta: A/T desyncs = 0 expected; C desyncs are the number to learn.
  (ii) bf16 b1 -> bf16 b8 at theta=0.93 (2*tau_bf16): A/T desyncs = 0
  expected. (iii) any A-desync with encoder gap >= 2*tau_decoder is a
  pipeline bug (XB-3), investigated before anything is reported. Nonzero C
  desyncs at ranks 2..64 mean the top-1 escape is necessary but not
  sufficient, and the set-coded variant's residual decides Phase 2b's next
  format step.

## Stop conditions
- Symbol-level roundtrip (encode -> decode of the flag/rank stream) must be
  exact on every prompt before any rate is reported.
- Any rac CoderError on real data => reported as a coder bug, not tuned away.

## Commands
```
python experiments/p3_rac_rate.py
python experiments/p2b_escape_robustness.py
```

## Post-run note (2026-08-30, after F-9/F-10; does not change the runs)
Question 1's band fired PASS on the held-out CI, but the tuning half shows
the opposite sign (AC wins by 0.013) with a CI that includes 0. A single-
split CI was too weak against prompt-half heterogeneity; the next protocol
should require sign agreement across both halves (or a cross-validated
difference) before PASS. Recorded here and in F-9's caveats, not
reinterpreted. Question 2's expected band (i) held for A/T; the C-desync
number it asked for turned out to be the whole story (F-10).

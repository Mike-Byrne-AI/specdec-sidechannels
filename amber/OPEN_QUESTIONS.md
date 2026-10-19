# Open Questions

## OQ-1 — Real greedy divergence rate for aligned pairs  [first answer: F-8; coder ceiling: F-9]
F-9: the coder upgrade is worth 1% (0.417 vs 0.421 bits/token held-out); amber-vs-AC is +/-0.02 with split-dependent sign; the 23-27% lever is value context, which D-8 forbids. Remaining rate levers are hints (OQ-4) and the content mix, not the coder.
Llama-3.2-3B -> 1B (base/base), 48,958 target-generated tokens: 6.8% (front-loaded 15% -> 1.8% across a 256-token horizon); amber v0 0.474 bits/token vs zstd 3.62, tie with AC-under-draft 0.472. Open: long-horizon rate, text-continuation corpus, 8B -> 1B (nf4 target), and the coder upgrade that would take the format below AC.
THE number: fraction of positions where the draft's greedy token differs
from the target's, for Llama-3.2-3B/1B and 3.1-8B/1B on target-generated
text. Sets the real compression ratio via F-1's curve. Fits the 3080 Ti
(both models, greedy, no sampling); reuse sideband's hf harness replay
pattern. Crossover to care about: divergence bits vs zstd on the same text.

## OQ-2 — Is rank stability achievable cheaply on real hardware?  [answered for one box: F-5/F-6/F-7 top-1, F-10 ranks 2..64, F-11 end-to-end]
F-11: real archives decode byte-exactly under fp32 (200/200 GPU, 24/24 CPU, KV vs teacher-forced); bf16 fails 84%, fp16 28.5%. The contract is measured. Open: cross-GPU-architecture fp32.
F-10 closes the depth gap the census left: at fp32 the order is exactly stable to rank 64 (0 desyncs / 49k); at bf16 it is not (3% at rank 2, 9-26% at ranks 3..8), and the top-1 escape cannot fix that. Decoder contract = fp32-class replay (D-8), 3.65x slower than bf16. Open: cross-GPU-architecture at fp32, and a direct bf16 decode of a real archive once the draft-replay decoder exists.
> Erratum (2026-10-10; F-14 row E8a): E8a: at theta 0 (the shipped default) cpu_fp32 -> cuda_fp32_b1 has 1 desync in 49056 positions (class A, gap 1.34e-05); 0 at theta in {0.142, 0.465, 0.93}, as F-10's body states, so the headline's zero is the escape-on count and the shipped contract has one. As an ORDER claim (OQ-2) it is false at every theta: the top-64 order differs from cpu_fp32 at 379 positions, every one a near-tie (the largest encoder gap between the two tokens competing for the first differing slot is 1.48e-04); what is stable is the resolved token, and only at batch 1 with the escape on.
Answered for one box, two models (F-5 TinyLlama, F-7 Llama-3.2-1B-Instruct): FREE within fp32 across device and batch (0-1 flips / 49k), 0.1-0.4% at fp16, 1-2% at bf16 with every flip a near-tie; escape-symbol cost = P(gap<threshold): ~8% of positions for an fp16 decoder, ~39% for bf16 on Llama-3.2-1B. Open: cross-GPU-architecture, the base-1B draft's gap distribution (Phase 1), and the escape-symbol format (BLUEPRINT Phase 2b).
> Erratum (2026-10-11; F-16 row E17): E17: 6 of the 7 printed "2tau" thresholds are 4 tau and 1 is 2 tau by the census's own calibrated tau; every printed beyond-count equals the census's count, which the census took at 2 tau (its per-row tau field holds 2 tau and its beyond-count compares each flip gap with that field), so the claims "every flip within 2 tau" stand. The escape-cost figures quoted at those labels do not: F-5 (FINDINGS.md:40): the near-tie mass reproduces at the printed thresholds (6.7% at 0.142 (printed 6.7), 19.0% at 0.465 (printed 19.0), 32.6% at 0.93 (printed 32.6)), and at the census's 2 tau it is bf16 19.0% at 2 tau = 0.465 against the printed 32.6%; fp16 3.4% at 2 tau = 0.0711 against the printed 6.7%. F-7 (FINDINGS.md:54): the near-tie mass reproduces at the printed thresholds (8.3% at 0.142 (printed 8.3), 23.2% at 0.465 (printed 23.2), 39.1% at 0.93 (printed 39.1)), and at the census's 2 tau it is bf16 23.3% at 2 tau = 0.465 against the printed 39%; fp16 4.1% at 2 tau = 0.0662 against the printed 8%; OPEN_QUESTIONS.md:16 repeats the printed 8% and 39%. Labels: F-5 (FINDINGS.md:40): bf16 0.93 is 4 tau (tau 0.2325; printed 0 beyond, census 0 beyond 2 tau = 0.4649; largest flip gap 0.231); fp16 0.142 is 4 tau (tau 0.03554; printed 0 beyond, census 0 beyond 2 tau = 0.07109; largest flip gap 0.0408); int8 5.0 is 4 tau (tau 1.251; printed 0 beyond, census 0 beyond 2 tau = 2.501; largest flip gap 1.97); nf4 12.3 is 4 tau (tau 3.075; printed 3 beyond, census 3 beyond 2 tau = 6.15; largest flip gap 7.06). F-7 (FINDINGS.md:54): bf16 0.93 is 4 tau (tau 0.2327; printed 0 beyond, census 0 beyond 2 tau = 0.4654; largest flip gap 0.263); fp16 0.066 is 2 tau (tau 0.03312; printed 0 beyond, census 0 beyond 2 tau = 0.06625; largest flip gap 0.0239); int8 6.6 is 4 tau (tau 1.649; printed 2 beyond, census 2 beyond 2 tau = 3.298; largest flip gap 3.66). P2b's escape thresholds, taken from F-5's labels, are 0.142 (4.3 fp16 tau, 0.6 bf16 tau), 0.465 (14.0 fp16 tau, 2.0 bf16 tau), 0.93 (28.1 fp16 tau, 4.0 bf16 tau); 0.465 is bf16's 2 tau, the setting the record used.
> Erratum (2026-10-11; F-15 row E16): E16: the top-64 order of cuda_fp32_b1 differs from cpu_fp32 at 379 of 49056 positions (378 distinct contexts); the encoder gap between the two tokens competing for the first differing slot (always the adjacent token) has median 6.7e-06 and max 1.48e-04 against an encoder top-2 gap of median 1.35 (p01 0.012), so F-14's "every one a near-tie" holds at logit scale; at the record's fp32 pair budget 2(tau_enc + tau_dec) = 8.6e-05, which that sentence did not state, 2 positions exceed it, 1 distinct context (sequence 89 offset 1, slot 43, gap 1.48e-04 (1.7x the budget), pair drift 4.50e-04; sequence 93 offset 1, slot 43, gap 1.48e-04 (1.7x the budget), pair drift 4.50e-04): a tail drift, not evidence of a pipeline bug, since tau is the 0.999 quantile of the aligned top-64 deltas (not a top-1 calibration), that quantile falls with depth on this arm (slot 0: 5.9e-05, slots 1-7: 4.8e-05, slots 8-15: 4.4e-05, slots 16-63: 4.0e-05), and 328 of 3090528 adjacent top-64 pairs drift by more than the budget. By first differing slot: slot 0: 1; slot 1: 2; slots 2-7: 11; slots 8-15: 13; slots 16-63: 352 (2 above). At slot 0, the scope of every claim site (F-7's and OQ-2's top-1 flips, F-10's A desyncs), the counts above budget are cuda_bf16_b1 0 of 983; cuda_bf16_b8 0 of 834; cuda_fp16_b1 0 of 208; cuda_fp32_b1 0 of 1; cuda_fp32_b8 0 of 0: the top-1 claims stand. At batch 8 (411 positions, 411 contexts, max 5.72e-05) 0 exceed that arm's 2 tau of 9.73e-05 (a census-derived proxy; P2b has no batch-8 budget) and 254 of 3090528 adjacent pairs drift by more than it. The other decoders at depth, informational: cuda_bf16_b1: order differs at 49056 of 49056 (48933 contexts), 4 above its budget 4.65e-01; cuda_bf16_b8: order differs at 49056 of 49056 (48933 contexts), 7 above its budget 4.52e-01; cuda_fp16_b1: order differs at 48090 of 49056 (47967 contexts), 4 above its budget 6.62e-02.
F-2/D-5: the codec needs order-preserving draft replay, not bitwise logits.
Measure rank-flip rates across: dtype (bf16/fp16/fp32), quantization
(int8/int4), batch size, kernel backends. If top-rank stability is near-free,
the determinism-layer dependency gets dramatically lighter; if not, this is
lockstep's precise workload. Instrument: src/amber/rankcensus.py (shaken
down on synthetic drift in a03, F-3). Protocol: lockstep E-006 shape with
cross-research XB-3 discipline — tolerance CALIBRATED from a benign
perturbation (calibrate_tau), every top-1 flip attributed to its reference
top-2 gap (a wide-gap flip is a bug, not drift), batch-size invariance as a
mask-bug detector, burstiness reported (bursty => different wire format).
The CPU is the second "device": one box suffices for the first census.

## OQ-7 — Header and prompt cost on short archives  [opened by F-11; answered: F-12 (binary+prompt), F-13 (sessions)]
F-13: k-turn reset-mode sessions reach 1.65 (k=8) / 1.45 (k=16) bits/gen-token — 2.6-2.9x under separate files, 3.4x under zstd-19 per session; shared-context coding loses on independently-generated turns (+16-39% content) and is reserved for true multi-turn data. Remaining here: true multi-turn generation (with the long-horizon run).
F-12: binary v3 = 130 B mean (97 B floor); prompt coded with the draft at 11.3 bits/token; rate = 917/L + 0.455 bits/token; crossover vs zstd-concat at L~263; header >10% of file until L~15k. Remaining: session-level archives (one header, many turns) and the long-horizon payload rate.
> Erratum (2026-10-11; F-16 row E18): E18: on the held-out half (P1 rows 100-199, 24780 generated tokens; dictionaries trained on rows 0-99), per archive on the full text: zstd-19 6.775 bits per generated token without a dictionary (the text carries the special-token literals E7 found, which a dictionary absorbs), 4.834 with a 4096 B dictionary (requested 4 KB), 4.439 with a 16384 B dictionary (requested 16 KB), 4.481 with a 22323 B dictionary (requested 64 KB), 4.481 with a 22323 B dictionary (requested 256 KB); amber v3 4.181 (1.050 without its 97 B fixed header). The 16 KB dictionary lowers the comparator by 34%; amber's per-archive advantage is 1.62x without it and 1.06x with it (9.728 for zstd once the dictionary's own bytes are spread over these archives). Sessions in reset mode whose rows are all held out: k=16 (5 sessions): amber v4 1.37, zstd-19 4.35 without and 3.51 with the 16 KB dictionary (multiples 3.2x and 2.6x; effect 19%); k=8 (12 sessions): amber v4 1.58, zstd-19 4.97 without and 3.70 with the 16 KB dictionary (multiples 3.1x and 2.3x; effect 25%). Concatenated full text: 3.81 without and 3.64 with the dictionary (effect 5%); by F-12's rate law the crossover moves from L 273 to 288. Content, concatenated generated text: amber v0 0.4213 against zstd-19 3.470 without and 3.322 with a dictionary trained on generated text (effect 4%): 8.2x and 7.9x. On the 22 held-out rows whose repeat-4-gram share is below one half: amber v3 5.10 against dictionary zstd 10.26 (14.38 without). Under the harvest's own definitions (special tokens skipped; repeat share over the row length) the same quantities are 6.251 and 4.446 per archive and, on 23 rows, 5.253 against 10.330, which is what its predictions were; without the literals the effects are 29% per archive, 18% and 23% for the sessions and 4% concatenated, every status unchanged. D-6's zstd rows were strawmen at the per-archive scale, strawmen at the session scale and fair at the concatenated scale; the dictionaries were trained on the other half of the same prompt families, which favours zstd.
At ~250 tokens per archive the per-archive constant dominates: JSON header 551 B (18.5 bits/token), binary estimate 3.3 bits/token vs payload 0.44. Levers: binary header, coding the prompt with the draft (AC-under-draft on user text), session-level archives (many turns, one header), and reporting rate as a function of archive length. Compare against zstd on the full text per archive (7.3 bits/token) and concatenated (3.9).
> Erratum (2026-10-10; F-14 row E7): E7: reproduces (7.2805 bits per generated token with zstandard 0.25.0, tokenizer snapshot 4e20de36); the per-archive text includes decoded special-token literals (200 of 200 archives carry <\|begin_of_text\|>, 14 carry <\|end_of_text\|>, 3610 B in all); without them 6.75.

## OQ-3 — Seeded-sampling archives (regime A at high content entropy)
Designed, not built: proposals replayed from a stored seed; per-position
accept bit; rejected/bonus tokens coded by rank under q. Content entropy is
high by construction, so the zlib comparison from F-1's caveat inverts —
this is where the format's structural edge should show. Needs sideband's
verifier core (D-1) and the seed-replay determinism contract.

## OQ-4 — Hint channel under the e07 budget
sideband F-9: dense hints lose 20:1; total break-even ~0.16 bits/token in
that regime. Amber's hint mechanism must be event-driven (block-sparse
bucket hints, boundary flags) and always reported net-of-cost. Hints are
decoder-visible bits, so D-2 is satisfied by construction.

## OQ-5 — Serving-compatibility tradeoff
Quantify the speedup cost of archive-compatible serving modes (deterministic
proposals, hint-only steering) vs steering-optimal spec decoding — the price
of "the serving trace is the archive". If small, the free-byproduct
economics (determinism-layer F-8/D-14) close; if large, packing is a
distinct pass again and the cost model must be re-run.

## OQ-6 — Freedom to operate
[withheld: OQ-6's body: three patent numbers, the claim reading and the counsel sentence (plan 10.3; 15.1 call 2); the question stays as structure under its heading; see WITHHELD.md]
Dated note (2026-10-18): the search this question asks for before any
publication was not re-run, and no counsel review ran; the owner waived the
gate for the public cut of this record (BLUEPRINT's gate, its dated note of
the same day). The only re-read is the claim reading of 2026-10-11 on
sideband's prior-art map (a textual reading, not legal advice). The question
stays open.

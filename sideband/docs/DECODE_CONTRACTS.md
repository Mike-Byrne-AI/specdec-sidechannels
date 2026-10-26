# Device drift and two decode contracts: grid crossings and rank-order mismatches (a harvested note)

Written 2026-10-11 from committed payloads in two sibling repositories, both
private and parked: amber at 69b437cba973 (tag `errata-batch-3-landed`) and
lockstep at 54d83f4b5e1e. It is harvested here because sideband is where the
write-up is built (docs/ECOSYSTEM.md). Every measured number below was
generated from those payloads by key; the Sources table at the end gives each
one's repository, commit, file and key, and the payload wins on any
disagreement. Status words: a HARVESTED NOTE, NON-CRITERION for every sideband
finding, decision and kill status. None of these runs used sideband's NF4
target, its sampling or its telemetry, and nothing in sideband's record
depends on them; P2b and the Llama arm of the census did use sideband's draft
model, Llama-3.2-1B-Instruct, on the same card.

## The question

A decoder that replays a model to reproduce an encoder's decisions (an
arithmetic-coded archive, a rank-coded archive, a seeded replay) needs the
model's logits to come out the same on the decoding machine. They are not
exactly the same: the same weights on another device, kernel path or precision
give logits that differ by a small drift. This note asks how often that drift
changes a decision, under the two contracts a replaying decoder can rest on:

- **Value contract** (lockstep's proposed lsp1 profile, its D-13): the decoder
  must reproduce the grid cell, floor(logit / delta), of each of the top-k
  logits. It breaks at a position when any of those k logits sits within the
  drift of a grid line.
- **Order contract** (amber's rank codec): the decoder must reproduce only the
  rank order of the tokens it codes. It breaks at a position when the coded
  token and its neighbour in rank are closer than the drift between them.

Both are driven by the same per-logit drift. They differ in what the drift has
to cross: grid lines sit wherever the grid puts them, whatever the text, while
the gaps between ranked tokens come from the model.

## The data

- **The E-006 census** (amber's Phase 2, a partial run of lockstep's
  experiment E-006: one GPU architecture where E-006 asked for two, and the
  burstiness of crossings not computed, as amber's F-6 says): top-64 logits at
  49,152 teacher-forced positions, CPU fp32 as the reference device against a
  GPU under fp32, fp16 and bf16, for TinyLlama-1.1B-Chat and
  Llama-3.2-1B-Instruct. A position crosses when any of the reference's top-64
  tokens changes grid cell or leaves the other arm's top-64.
- **P2b** (amber): meta-llama/Llama-3.2-1B-Instruct top-256 dumps at 49,056
  positions; symbol streams built under cpu_fp32 and resolved under each GPU
  arm. The theta 0 rows (no top-1 escape) are used throughout.
- **P4** (amber): 200 real archives of 48,958 target-generated tokens
  (Llama-3.2-3B greedy text, meta-llama/Llama-3.2-1B as the draft), encoded on
  cuda fp32 and decoded draft-only with incremental KV.
- **amber's 2026-10 errata pass**: pre-registered CPU recomputes of the above,
  each reproduced by an independent critic; rows E8b, E8c, E15, E16 and E19
  are used here.

One box, one GPU architecture (NVIDIA GeForce RTX 3080 Ti, torch 2.6.0+cu124),
1B-class models.

## 1. The drift

| model | GPU arm against cpu_fp32 | drift p50 | p99 | max |
|---|---|---|---|---|
| TinyLlama-1.1B-Chat | fp32 | 2.9e-6 | 1.5e-5 | 1.3e-4 |
| TinyLlama-1.1B-Chat | fp16 | 0.0031 | 0.017 | 0.19 |
| TinyLlama-1.1B-Chat | bf16 | 0.024 | 0.13 | 0.78 |
| Llama-3.2-1B-Instruct | fp32 | 6.7e-6 | 2.9e-5 | 4.5e-4 |
| Llama-3.2-1B-Instruct | fp16 | 0.0036 | 0.019 | 0.80 |
| Llama-3.2-1B-Instruct | bf16 | 0.028 | 0.14 | 1.6 |

The bf16 median drift is about 8,300 times the fp32 one on TinyLlama and about
4,200 times on Llama. Drift here is the absolute logit difference between the
two arms, as amber's F-5 and F-6 report it; the code that computed it is not
in amber's committed tree, so which tokens' logits enter the quantiles cannot
be read back from the payload.

## 2. The value contract: grid crossings track k * eps / delta

Lockstep derived the rate on synthetic logits (its F-7): when each of k logits
moves by eps and grid lines are delta apart, a position crosses with
probability about k * eps / delta while that is small. Its synthetic check was
10/1500 = 0.67% measured against 0.64% predicted at delta 1e-3 (lockstep
docs/09-emergent-synthesis.md: counts in prose, no committed payload). On real
logits, with eps the measured fp32 median drift and k = 64:

| model | delta | positions crossing at fp32 | k * eps_p50 / delta | measured over predicted |
|---|---|---|---|---|
| TinyLlama-1.1B-Chat | 1e-2 | 2.6% | 1.8% | 1.41 |
| TinyLlama-1.1B-Chat | 1e-3 | 21.9% | 18.3% | 1.19 |
| TinyLlama-1.1B-Chat | 1e-4 | 90.8% | 1.83 (above 1: saturated) | - |
| Llama-3.2-1B-Instruct | 1e-2 | 5.0% | 4.3% | 1.18 |
| Llama-3.2-1B-Instruct | 1e-3 | 40.8% | 42.7% | 0.96 |
| Llama-3.2-1B-Instruct | 1e-4 | 99.4% | 4.27 (above 1: saturated) | - |

- fp16 and bf16 cross at 100% of positions at every delta on both models.
- The predicted column uses the unrounded median drift. amber's F-6 and F-7
  and lockstep's F-12 and F-13 print 1.9% and 19% (TinyLlama) and 4.5% and 45%
  (Llama) for the same cells because they rounded the median to 3e-6 and 7e-6.
- Using only the median drift, the rule sizes the fp32 rate within a factor of
  0.96 to 1.41 in the four unsaturated cells: low in three of them and high in
  one (Llama at delta 1e-3). Two readings fit, both probable and untested: a
  rule built on the median should run low if the drift is right-skewed (p99
  over p50 is 5.3 and 4.3; the payload carries no mean), and a linear rule
  should run high once two crossings start to share a position.
- At delta 1e-3 the value contract needs a correction at 21.9% and 40.8% of
  positions even at fp32; only delta 1e-2 is sparse (2.6%, 5.0%), and fp16 and
  bf16 cross everywhere. Lockstep's E-006 protocol had pinned a stop condition
  at drift above about 1e-5; the fp32 median sits below it on both models and
  the p99 above it.

## 3. The order contract: mismatches by rank depth

P2b, theta 0, encoder cpu_fp32. Rank 1 is the share of top-1 symbols (25,306
of the 49,056 positions) that resolve to a different token; rank r is the
share of correction symbols at that rank that do (18,400 positions code a rank
from 2 to 64; the other 5,350 code a token beyond rank 64 raw and cannot
mis-order).

| decoder | rank 1 | rank 2 | rank 3 | rank 4 | rank 8 | ranks 17-64 | all corrections |
|---|---|---|---|---|---|---|---|
| fp32, batch 1 | 1 of 25,306 | 0 | 0 | 0 | 0 | 0 | 0 of 18,400 |
| fp16, batch 1 | 0.10% | 0.72% | 1.5% | 2.2% | 3.7% | 14.4% | 4.7% |
| bf16, batch 1 | 0.63% | 6.0% | 9.3% | 15.3% | 25.6% | 59.8% | 24.4% |
| bf16, batch 8 | 0.58% | 6.1% | 9.5% | 13.9% | 23.2% | 58.7% | 24.0% |
| int8 weights, batch 1 | 2.0% | 17.4% | 27.9% | 41.1% | 62.9% | 90.1% | 49.8% |
| nf4 weights, batch 1 | 6.8% | 40.5% | 56.6% | 69.8% | 85.9% | 96.5% | 70.8% |

- **fp32** resolves 1 of 25,306 top-1 symbols wrongly (the swapped pair 1.3e-5
  apart) and every correction correctly. Its top-64 order is not identical to
  the CPU's: it differs at 379 positions, each first at an adjacent pair. At 2
  of those positions (1 context) the swapped tokens sat further apart than the
  record's fp32 pair budget of 8.6e-5, so not every order difference is a
  near-tie at that budget; none is at the top slot (E16). At batch 8, which
  P2b did not run, the errata pass found one desync in 49,056 positions at
  every escape setting: a token at encoder rank 4 resolved at rank 5, the
  swapped pair 3.0e-5 apart (E8c).
- **bf16** mis-resolves 0.63% of top-1 symbols but 6.0% at rank 2, 25.6% at
  rank 8 and 59.8% across ranks 17 to 64. A census that checks only the top-1
  token sees the smallest of these numbers. The rise with rank fits logits
  crowding at depth, but that reading is probable, not shown: each rank's rate
  comes from different positions (flatter distributions code deeper ranks), so
  depth and position type are confounded.
- **int8 and nf4** change the weights, not only the arithmetic; their rows
  measure weight quantization against fp32, not device drift.

## 4. End to end on real archives

| decoder | archives decoded byte-exact | first desync, one per ... decoded positions |
|---|---|---|
| cuda fp32 | 200 of 200 | none |
| cpu fp32 | 24 of 24 | none |
| cuda bf16 | 32 of 200 (84.0% fail) | 65.1 |
| cuda fp16 | 143 of 200 (28.5% fail) | 670.5 |

- fp32 decoded 54,810 positions with no failure, 48,958 on the GPU and 5,852
  on the CPU, across the split between the encoder's teacher-forced forward
  and the decoder's incremental KV path (E8b).
- Predicting the archives from the dumps' theta 0 rates of every class by rank
  alone, weighted by the archives' coded ranks, gives one desync per 76.6
  (bf16) and 501.0 (fp16) tokens and whole-archive failure of 91.9% and 37.2%,
  above the measured 84.0% and 28.5%. By class, top-1 desyncs come in under
  that prediction (bf16 28 observed against 63.8 expected, z -4.5; fp16 9
  against 35.2, z -4.4) and corrections over it (bf16 140 against 81.6, z
  +6.5; fp16 48 against 38.6, z +1.5) (E15).
- Conditioning the top-1 term on the encoder's top-2 gap, rather than on rank
  alone, brings it to 33.3 expected against 28 observed for bf16 (z -0.9) and
  15.0 against 9 for fp16 (z -1.6). With the rank-only correction term beside
  it, the prediction becomes one desync per 103.2 (bf16) and 681.7 (fp16)
  tokens and whole-archive failure of 74.7% and 27.4%; the failure prediction
  is now BELOW the measured rates, at all 7 binnings on both arms (E19). That
  rule was written after its primary binning's values were in the record; the
  other binnings had not been seen, and across all of them the top-1 z runs
  from -1.3 to -0.4 (bf16) and -1.8 to -0.5 (fp16).
- So whether the archives fail more or less often than the dumps predict
  depends on how the top-1 term is predicted. Both predictors share the same
  rank-only correction term, which the archives exceed clearly for bf16 (z
  +6.5) and within noise for fp16 (z +1.5). That excess stays unexplained:
  model, content and kernel path all differ between the dumps and the
  archives.

## What carries over

- One measured drift sizes both contracts. The value contract fails at a rate
  set by the drift and the grid alone, about k * eps / delta, whatever the
  text; the order contract fails only where the model puts two ranked tokens
  within the drift of each other. On this box the order contract is nearly
  free at fp32 (1 desync in 49,056 positions at batch 1), while the value
  contract needs corrections at 2.6% to 40.8% of positions at fp32 for delta
  1e-2 to 1e-3 and fails everywhere at fp16 and bf16. Reduced-precision order
  failures are smallest at the top of the dumps (0.63% of bf16 top-1 symbols)
  and rise with rank, but top-1 desyncs still caused 28 of the 168 bf16 and 9
  of the 57 fp16 first desyncs in the archives (E15).
- The principle is not new: it is the margin condition any tolerance-based
  replay check rests on. The 2026-10-09 review harvest (agent output, not
  re-checked here) names exllamav3's model_diff as printing agreement by rank
  depth since 2025-05. For the value contract, lockstep's prior-art log (its
  docs/02-prior-art.md, links last checked 2026-07 and not re-verified here)
  has PA-3 (arXiv 2603.25526), which proposes quantizing logits for bit-exact
  reproducibility and describes kernels drifting by about 1e-7. lockstep's
  note does not give the scale of that figure, so it is not compared here with
  section 1's drift, an absolute difference on logits of magnitude about 10
  (amber F-6). The log also has PA-7 (arXiv 2410.09872), which quantizes
  critical outputs and adds a safeguard bitstream, the design lockstep's lsp1
  would have used to carry the crossings in section 2.
- Limits: one box and one GPU architecture; the CPU is the only second device;
  two 1B-class models. fp32 is not exact even at batch 1 (1 top-1 desync, 379
  order differences) and adds a correction desync at batch 8, so the fp32 pin
  is shown sufficient for these archives on this box only; fp32 across GPU
  architectures was never measured. The Llama logit dumps behind P2b and E16
  stay unpublished (licence); this note carries summary statistics only.
- For sideband's own artifacts: docs/REPRODUCE.md section 4 already says the
  CUDA paths are not bit-deterministic. Section 1 shows how far the logits of
  sideband's own draft model move on the same card when the arithmetic changes
  (CPU fp32 against GPU bf16), so a re-run of sideband's GPU arms elsewhere
  should be expected to differ at the token level and agree, at best, at the
  level of the confidence intervals. That is borrowed evidence: a re-run on
  another GPU at the same precision was never measured, the NF4 8B target was
  never measured here, and these runs did no temperature-1.0 sampling.

## Sources

Keys are JSON Pointers into the file at the commit (lockstep markdown is cited
by line); derived numbers name their formula. Commits: amber
69b437cba97347c52df1264d3b7aae71d8db95db, lockstep
54d83f4b5e1ed286b9551eba45798c69a6a8479f.

Dated note 2026-10-12 (plan 10.4, landed with the export tool): once amber's
folder ships in the public specdec-sidechannels repository, the 197 amber
rows will resolve inside the tree, because the export keeps file contents
byte for byte and a git blob id is a content hash, so
`git hash-object amber/<file>` from a clone is expected to print the id the
row cites; the export's fresh-clone proof runs that check from the public
folder when it exists, and no public folder exists at this note's date. What
was run: the 7 distinct file-and-blob pairs the amber rows cite were
recomputed at amber 69b437c in the PRIVATE checkout on 2026-10-12 and all 7
match. The 16 lockstep rows cite 54d83f4 while lockstep exports at its
parked commit cdfe0b3: docs/02-prior-art.md (0a75cc5a5406),
docs/09-emergent-synthesis.md (86b6e14eebbf),
experiments/E-006-real-logit-crossing-rate.md (1c7d9a12208f) have the same
blob at both commits; trellis-docs/trellis-findings.md is deb58818d8ef at
54d83f4 and 70e63b54f996 at cdfe0b3, one hunk of 8 lines appended after line
176 with the cited lines 84, 116, 124 and 134 unchanged; the f14.date row
resolves through lockstep commit f9e9c9c, which no fresh-history export
carries, so its value is stated here: 2026-08-29; the 5 rows citing
docs/09-emergent-synthesis.md resolve only if lockstep's survey ships that
document. Until the public repository exists these ids resolve only in the
private checkouts; the 69 derived rows name their formulas.

| number | repository | file (blob) | key or formula |
|---|---|---|---|
| e10.Bps | derived | - | e10.rate * e10.bpt |
| e10.MBps | derived | - | e10.Bps / 1e6 |
| e10.bpt | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E10/value/content_bytes_per_token |
| e10.rate | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E10/value/draft_scoring/weighted |
| e10.status | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E10/status |
| e10.x_vs5 | derived | - | 5e6 / e10.Bps |
| e10.x_vs_be | derived | - | l.be * 1e6 / e10.Bps |
| e15.bf16.A.expected | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/A/expected |
| e15.bf16.A.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/A/observed |
| e15.bf16.A.z | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/A/z |
| e15.bf16.C.expected | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/C/expected |
| e15.bf16.C.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/C/observed |
| e15.bf16.C.z | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/C/z |
| e15.bf16.all.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/compensator_theta0_h4/all/observed |
| e15.bf16.archives | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/measured/archives |
| e15.bf16.exact | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/measured/byte_exact |
| e15.bf16.fail | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/measured/fail_rate |
| e15.bf16.one_in | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/measured/one_in |
| e15.bf16.pred_fail | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/fail_exact/all_theta0_h4/fail_rate |
| e15.bf16.pred_one_in | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_bf16_b1/all_theta0/h4/one_in |
| e15.fp16.A.expected | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/A/expected |
| e15.fp16.A.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/A/observed |
| e15.fp16.A.z | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/A/z |
| e15.fp16.C.expected | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/C/expected |
| e15.fp16.C.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/C/observed |
| e15.fp16.C.z | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/C/z |
| e15.fp16.all.observed | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/compensator_theta0_h4/all/observed |
| e15.fp16.archives | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/measured/archives |
| e15.fp16.exact | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/measured/byte_exact |
| e15.fp16.fail | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/measured/fail_rate |
| e15.fp16.one_in | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/measured/one_in |
| e15.fp16.pred_fail | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/fail_exact/all_theta0_h4/fail_rate |
| e15.fp16.pred_one_in | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/value/arms/cuda_fp16_b1/all_theta0/h4/one_in |
| e15.status | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E15/status |
| e16.above | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/arms/cuda_fp32_b1/count_above_budget |
| e16.above_ctx | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/arms/cuda_fp32_b1/distinct_contexts_above_budget |
| e16.above_slot0 | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/arms/cuda_fp32_b1/by_slot_bucket/0/above_budget |
| e16.budget | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/arms/cuda_fp32_b1/budget |
| e16.n_diff | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/arms/cuda_fp32_b1/n_diff |
| e16.nonadjacent | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/value/b1_n_nonadjacent |
| e16.scope_fp32 | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/status_at_claim_scope/cuda_fp32_b1 |
| e16.status | amber | results/errata_recompute_2.json (9be96ef5bfd0) | /rows/E16/status |
| e19.bf16.E | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/bf16_E_A |
| e19.bf16.all_bins_measured_above | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_bf16_b1/by_binning/*/comparisons/fail_measured_gt_predicted (true at every binning) |
| e19.bf16.obs | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_bf16_b1/observed_A_first |
| e19.bf16.pred_fail | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/bf16_fail_exact |
| e19.bf16.pred_one_in | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/bf16_one_in |
| e19.bf16.z | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/bf16_z |
| e19.bf16.zhi | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_bf16_b1/grid_z_range/1 |
| e19.bf16.zlo | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_bf16_b1/grid_z_range/0 |
| e19.fp16.E | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/fp16_E_A |
| e19.fp16.all_bins_measured_above | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_fp16_b1/by_binning/*/comparisons/fail_measured_gt_predicted (true at every binning) |
| e19.fp16.obs | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_fp16_b1/observed_A_first |
| e19.fp16.pred_fail | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/fp16_fail_exact |
| e19.fp16.pred_one_in | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/fp16_one_in |
| e19.fp16.z | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/fp16_z |
| e19.fp16.zhi | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_fp16_b1/grid_z_range/1 |
| e19.fp16.zlo | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/arms/cuda_fp16_b1/grid_z_range/0 |
| e19.n_binnings | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/binnings |
| e19.primary | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/value/primary |
| e19.status | amber | results/errata_recompute_3.json (80356a9e4452) | /rows/E19/status |
| e6.0.bf16.cross.1e-2 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.0.bf16.cross.1e-3 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.0.bf16.cross.1e-4 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.0.bf16.eps_max | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/eps_max |
| e6.0.bf16.eps_p50 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/eps_p50 |
| e6.0.bf16.eps_p99 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_bf16_b1/eps_p99 |
| e6.0.bf16_over_fp32 | derived | - | e6.0.bf16.eps_p50 / fp32.eps_p50 |
| e6.0.fp16.cross.1e-2 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.0.fp16.cross.1e-3 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.0.fp16.cross.1e-4 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.0.fp16.eps_max | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/eps_max |
| e6.0.fp16.eps_p50 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/eps_p50 |
| e6.0.fp16.eps_p99 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp16_b1/eps_p99 |
| e6.0.fp32.cross.1e-2 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.0.fp32.cross.1e-3 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.0.fp32.cross.1e-4 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.0.fp32.eps_max | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/eps_max |
| e6.0.fp32.eps_p50 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/eps_p50 |
| e6.0.fp32.eps_p99 | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /grid_crossing_e006/cuda_fp32_b1/eps_p99 |
| e6.0.law.1e-2 | derived | - | 64 * e6.0.fp32.eps_p50 / 1e-2 |
| e6.0.law.1e-3 | derived | - | 64 * e6.0.fp32.eps_p50 / 1e-3 |
| e6.0.law.1e-4 | derived | - | 64 * e6.0.fp32.eps_p50 / 1e-4 |
| e6.0.law_r.1e-2 | derived | - | 64 * 3e-06 / 1e-2 (eps rounded as printed in the sources) |
| e6.0.law_r.1e-3 | derived | - | 64 * 3e-06 / 1e-3 (eps rounded as printed in the sources) |
| e6.0.law_r.1e-4 | derived | - | 64 * 3e-06 / 1e-4 (eps rounded as printed in the sources) |
| e6.0.ratio.1e-2 | derived | - | e6.0.fp32.cross.1e-2 / e6.0.law.1e-2 |
| e6.0.ratio.1e-3 | derived | - | e6.0.fp32.cross.1e-3 / e6.0.law.1e-3 |
| e6.0.regime | amber | results/p2_e006_grid_crossing.json (6c858e472137) | /regime |
| e6.0.tail | derived | - | e6.0.fp32.eps_p99 / eps_p50 |
| e6.1.bf16.cross.1e-2 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.1.bf16.cross.1e-3 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.1.bf16.cross.1e-4 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.1.bf16.eps_max | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/eps_max |
| e6.1.bf16.eps_p50 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/eps_p50 |
| e6.1.bf16.eps_p99 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_bf16_b1/eps_p99 |
| e6.1.bf16_over_fp32 | derived | - | e6.1.bf16.eps_p50 / fp32.eps_p50 |
| e6.1.fp16.cross.1e-2 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.1.fp16.cross.1e-3 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.1.fp16.cross.1e-4 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.1.fp16.eps_max | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/eps_max |
| e6.1.fp16.eps_p50 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/eps_p50 |
| e6.1.fp16.eps_p99 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp16_b1/eps_p99 |
| e6.1.fp32.cross.1e-2 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.01 |
| e6.1.fp32.cross.1e-3 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.001 |
| e6.1.fp32.cross.1e-4 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/pos_rate_any_crossing_k64_delta0.0001 |
| e6.1.fp32.eps_max | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/eps_max |
| e6.1.fp32.eps_p50 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/eps_p50 |
| e6.1.fp32.eps_p99 | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /grid_crossing_e006/cuda_fp32_b1/eps_p99 |
| e6.1.law.1e-2 | derived | - | 64 * e6.1.fp32.eps_p50 / 1e-2 |
| e6.1.law.1e-3 | derived | - | 64 * e6.1.fp32.eps_p50 / 1e-3 |
| e6.1.law.1e-4 | derived | - | 64 * e6.1.fp32.eps_p50 / 1e-4 |
| e6.1.law_r.1e-2 | derived | - | 64 * 7e-06 / 1e-2 (eps rounded as printed in the sources) |
| e6.1.law_r.1e-3 | derived | - | 64 * 7e-06 / 1e-3 (eps rounded as printed in the sources) |
| e6.1.law_r.1e-4 | derived | - | 64 * 7e-06 / 1e-4 (eps rounded as printed in the sources) |
| e6.1.ratio.1e-2 | derived | - | e6.1.fp32.cross.1e-2 / e6.1.law.1e-2 |
| e6.1.ratio.1e-3 | derived | - | e6.1.fp32.cross.1e-3 / e6.1.law.1e-3 |
| e6.1.regime | amber | results/p2_llama32_e006_grid_crossing.json (a9e3aff9fadb) | /regime |
| e6.1.tail | derived | - | e6.1.fp32.eps_p99 / eps_p50 |
| e6.ratio_hi | derived | - | max of the four unsaturated ratios |
| e6.ratio_lo | derived | - | min of the four unsaturated ratios |
| e8b.status | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/status |
| e8c.dec_rank | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/events/0/dec_rank_of_true |
| e8c.enc_rank | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/events/0/enc_rank_of_true |
| e8c.gap | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/events/0/enc_gap_at_swapped_pair |
| e8c.n | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/n |
| e8c.od_b1 | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/order_differences_vs_cpu_fp32/cuda_fp32_b1/positions_top64_order_differs |
| e8c.od_b8 | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/order_differences_vs_cpu_fp32/cuda_fp32_b8/positions_top64_order_differs |
| e8c.status | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/status |
| e8c.total | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8c/value/desync_total |
| f14.date | lockstep | - | git log -1 --format=%ad --date=short f9e9c9c (F-14's commit) |
| f14.days | derived | - | 2026-10-09 minus f14.date (review date: lockstep TP-7, task-packs/done) |
| l.be | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 84 |
| l.e006_stop | lockstep | experiments/E-006-real-logit-crossing-rate.md (1c7d9a12208f) | line 42 |
| l.f12_law | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 116 |
| l.f13_law | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 124 |
| l.f14_5mbs | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 134 |
| l.f14_twoorders | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 134 |
| l.f7_den | lockstep | docs/09-emergent-synthesis.md (86b6e14eebbf) | line 92 |
| l.f7_meas | lockstep | docs/09-emergent-synthesis.md (86b6e14eebbf) | line 92 |
| l.f7_num | lockstep | docs/09-emergent-synthesis.md (86b6e14eebbf) | line 92 |
| l.f7_pred | lockstep | docs/09-emergent-synthesis.md (86b6e14eebbf) | line 92 |
| l.f7_synth | lockstep | docs/09-emergent-synthesis.md (86b6e14eebbf) | line 92 |
| l.f8_be | lockstep | trellis-docs/trellis-findings.md (deb58818d8ef) | line 84 |
| l.pa3 | lockstep | docs/02-prior-art.md (0a75cc5a5406) | line 17 |
| l.pa3_drift | lockstep | docs/02-prior-art.md (0a75cc5a5406) | line 21 |
| l.pa7 | lockstep | docs/02-prior-art.md (0a75cc5a5406) | line 35 |
| p2b.cuda_bf16_b1.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/2/desync |
| p2b.cuda_bf16_b1.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/3/desync |
| p2b.cuda_bf16_b1.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/4/desync |
| p2b.cuda_bf16_b1.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/8/desync |
| p2b.cuda_bf16_b1.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/desyncs/A |
| p2b.cuda_bf16_b1.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/desyncs/C |
| p2b.cuda_bf16_b1.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/2/n |
| p2b.cuda_bf16_b1.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/3/n |
| p2b.cuda_bf16_b1.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/4/n |
| p2b.cuda_bf16_b1.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/C_desync_by_rank/8/n |
| p2b.cuda_bf16_b1.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/symbol_counts/A |
| p2b.cuda_bf16_b1.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/symbol_counts/C |
| p2b.cuda_bf16_b1.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b1/0/symbol_counts/X |
| p2b.cuda_bf16_b1.r1 | derived | - | p2b.cuda_bf16_b1.dA / nA |
| p2b.cuda_bf16_b1.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_bf16_b1.r2 | derived | - | d2/n2 |
| p2b.cuda_bf16_b1.r3 | derived | - | d3/n3 |
| p2b.cuda_bf16_b1.r4 | derived | - | d4/n4 |
| p2b.cuda_bf16_b1.r8 | derived | - | d8/n8 |
| p2b.cuda_bf16_b1.rC | derived | - | p2b.cuda_bf16_b1.dC / nC |
| p2b.cuda_bf16_b8.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/2/desync |
| p2b.cuda_bf16_b8.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/3/desync |
| p2b.cuda_bf16_b8.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/4/desync |
| p2b.cuda_bf16_b8.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/8/desync |
| p2b.cuda_bf16_b8.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/desyncs/A |
| p2b.cuda_bf16_b8.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/desyncs/C |
| p2b.cuda_bf16_b8.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/2/n |
| p2b.cuda_bf16_b8.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/3/n |
| p2b.cuda_bf16_b8.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/4/n |
| p2b.cuda_bf16_b8.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/C_desync_by_rank/8/n |
| p2b.cuda_bf16_b8.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/symbol_counts/A |
| p2b.cuda_bf16_b8.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/symbol_counts/C |
| p2b.cuda_bf16_b8.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_bf16_b8/0/symbol_counts/X |
| p2b.cuda_bf16_b8.r1 | derived | - | p2b.cuda_bf16_b8.dA / nA |
| p2b.cuda_bf16_b8.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_bf16_b8.r2 | derived | - | d2/n2 |
| p2b.cuda_bf16_b8.r3 | derived | - | d3/n3 |
| p2b.cuda_bf16_b8.r4 | derived | - | d4/n4 |
| p2b.cuda_bf16_b8.r8 | derived | - | d8/n8 |
| p2b.cuda_bf16_b8.rC | derived | - | p2b.cuda_bf16_b8.dC / nC |
| p2b.cuda_fp16_b1.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/2/desync |
| p2b.cuda_fp16_b1.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/3/desync |
| p2b.cuda_fp16_b1.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/4/desync |
| p2b.cuda_fp16_b1.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/8/desync |
| p2b.cuda_fp16_b1.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/desyncs/A |
| p2b.cuda_fp16_b1.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/desyncs/C |
| p2b.cuda_fp16_b1.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/2/n |
| p2b.cuda_fp16_b1.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/3/n |
| p2b.cuda_fp16_b1.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/4/n |
| p2b.cuda_fp16_b1.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/C_desync_by_rank/8/n |
| p2b.cuda_fp16_b1.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/symbol_counts/A |
| p2b.cuda_fp16_b1.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/symbol_counts/C |
| p2b.cuda_fp16_b1.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp16_b1/0/symbol_counts/X |
| p2b.cuda_fp16_b1.r1 | derived | - | p2b.cuda_fp16_b1.dA / nA |
| p2b.cuda_fp16_b1.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_fp16_b1.r2 | derived | - | d2/n2 |
| p2b.cuda_fp16_b1.r3 | derived | - | d3/n3 |
| p2b.cuda_fp16_b1.r4 | derived | - | d4/n4 |
| p2b.cuda_fp16_b1.r8 | derived | - | d8/n8 |
| p2b.cuda_fp16_b1.rC | derived | - | p2b.cuda_fp16_b1.dC / nC |
| p2b.cuda_fp32_b1.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/2/desync |
| p2b.cuda_fp32_b1.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/3/desync |
| p2b.cuda_fp32_b1.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/4/desync |
| p2b.cuda_fp32_b1.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/8/desync |
| p2b.cuda_fp32_b1.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/desyncs/A |
| p2b.cuda_fp32_b1.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/desyncs/C |
| p2b.cuda_fp32_b1.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/2/n |
| p2b.cuda_fp32_b1.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/3/n |
| p2b.cuda_fp32_b1.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/4/n |
| p2b.cuda_fp32_b1.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/C_desync_by_rank/8/n |
| p2b.cuda_fp32_b1.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/symbol_counts/A |
| p2b.cuda_fp32_b1.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/symbol_counts/C |
| p2b.cuda_fp32_b1.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/symbol_counts/X |
| p2b.cuda_fp32_b1.r1 | derived | - | p2b.cuda_fp32_b1.dA / nA |
| p2b.cuda_fp32_b1.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_fp32_b1.r2 | derived | - | d2/n2 |
| p2b.cuda_fp32_b1.r3 | derived | - | d3/n3 |
| p2b.cuda_fp32_b1.r4 | derived | - | d4/n4 |
| p2b.cuda_fp32_b1.r8 | derived | - | d8/n8 |
| p2b.cuda_fp32_b1.rC | derived | - | p2b.cuda_fp32_b1.dC / nC |
| p2b.cuda_int8_b1.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/2/desync |
| p2b.cuda_int8_b1.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/3/desync |
| p2b.cuda_int8_b1.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/4/desync |
| p2b.cuda_int8_b1.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/8/desync |
| p2b.cuda_int8_b1.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/desyncs/A |
| p2b.cuda_int8_b1.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/desyncs/C |
| p2b.cuda_int8_b1.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/2/n |
| p2b.cuda_int8_b1.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/3/n |
| p2b.cuda_int8_b1.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/4/n |
| p2b.cuda_int8_b1.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/C_desync_by_rank/8/n |
| p2b.cuda_int8_b1.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/symbol_counts/A |
| p2b.cuda_int8_b1.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/symbol_counts/C |
| p2b.cuda_int8_b1.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_int8_b1/0/symbol_counts/X |
| p2b.cuda_int8_b1.r1 | derived | - | p2b.cuda_int8_b1.dA / nA |
| p2b.cuda_int8_b1.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_int8_b1.r2 | derived | - | d2/n2 |
| p2b.cuda_int8_b1.r3 | derived | - | d3/n3 |
| p2b.cuda_int8_b1.r4 | derived | - | d4/n4 |
| p2b.cuda_int8_b1.r8 | derived | - | d8/n8 |
| p2b.cuda_int8_b1.rC | derived | - | p2b.cuda_int8_b1.dC / nC |
| p2b.cuda_nf4_b1.d2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/2/desync |
| p2b.cuda_nf4_b1.d3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/3/desync |
| p2b.cuda_nf4_b1.d4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/4/desync |
| p2b.cuda_nf4_b1.d8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/8/desync |
| p2b.cuda_nf4_b1.dA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/desyncs/A |
| p2b.cuda_nf4_b1.dC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/desyncs/C |
| p2b.cuda_nf4_b1.n2 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/2/n |
| p2b.cuda_nf4_b1.n3 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/3/n |
| p2b.cuda_nf4_b1.n4 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/4/n |
| p2b.cuda_nf4_b1.n8 | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/C_desync_by_rank/8/n |
| p2b.cuda_nf4_b1.nA | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/symbol_counts/A |
| p2b.cuda_nf4_b1.nC | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/symbol_counts/C |
| p2b.cuda_nf4_b1.nX | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_nf4_b1/0/symbol_counts/X |
| p2b.cuda_nf4_b1.r1 | derived | - | p2b.cuda_nf4_b1.dA / nA |
| p2b.cuda_nf4_b1.r17_64 | derived | - | sum desync / sum n over C_desync_by_rank ranks 17..64 of cell 0 |
| p2b.cuda_nf4_b1.r2 | derived | - | d2/n2 |
| p2b.cuda_nf4_b1.r3 | derived | - | d3/n3 |
| p2b.cuda_nf4_b1.r4 | derived | - | d4/n4 |
| p2b.cuda_nf4_b1.r8 | derived | - | d8/n8 |
| p2b.cuda_nf4_b1.rC | derived | - | p2b.cuda_nf4_b1.dC / nC |
| p2b.fp32.A_gap | amber | results/p2b_escape_robustness.json (7a84b002376c) | /report/cpu_fp32/decoders/cuda_fp32_b1/0/A_desync_gap/max |
| p2b.model | amber | results/p2b_escape_robustness.json (7a84b002376c) | /model |
| p2b.n | amber | results/p2b_escape_robustness.json (7a84b002376c) | /positions |
| p4.archives | amber | results/p4_real_archive.json (26ccf5cf5536) | /report/archives |
| p4.cpu_fp32.fail | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cpu_fp32/n_fail |
| p4.cpu_fp32.pos | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cpu_fp32/positions |
| p4.cpu_fp32.rows | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cpu_fp32/n_rows |
| p4.cuda_fp32.fail | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cuda_fp32/n_fail |
| p4.cuda_fp32.pos | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cuda_fp32/positions |
| p4.cuda_fp32.rows | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/cuda_fp32/n_rows |
| p4.draft | amber | results/p4_real_archive.json (26ccf5cf5536) | /draft |
| p4.gpu | amber | results/p4_real_archive.json (26ccf5cf5536) | /encoder_provenance/gpu |
| p4.pos_total | amber | results/errata_recompute.json (551a1ccd868b) | /rows/E8b/value/positions_total |
| p4.tokens | amber | results/p4_real_archive.json (26ccf5cf5536) | /report/content_tokens |
| p4.torch | amber | results/p4_real_archive.json (26ccf5cf5536) | /encoder_provenance/torch |

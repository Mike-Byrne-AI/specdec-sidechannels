# Findings Index

A reader's map of the 27 registered findings in `FINDINGS.md` (F-0 through
F-26, entry dates 2026-08-28 to 2026-09-15; dated addenda inside the
entries: F-22 through 2026-09-05, the F-15 .. F-18 errata and notes of
2026-09-06 and 2026-09-14, F-25's amendment and post-hoc lines of 2026-09-14,
F-26's post-hoc line of 2026-09-15 and its status lines of 2026-10-01 and 2026-10-02; the
rows and arc sections for F-24 .. F-26 were added on 2026-10-01). `FINDINGS.md` is registered text: an entry is never
rewritten after it lands; corrections and later readings are added inside the
entry as dated addenda, notes, or errata. This index is a derived reading aid,
not evidence. If the two ever disagree, the entry in `FINDINGS.md` wins.

House terms are collected in `docs/GLOSSARY.md`; the ones this page leans on
are defined briefly at first use below. The plan of record is
`docs/BLUEPRINT.md`; the kill criteria (K-1 .. K-7) are in
`docs/WHY_THIS_DIES.md`; the decisions (D-1 .. D-11) are in `DECISIONS.md`;
the open questions (OQ-1 .. OQ-19) are in `OPEN_QUESTIONS.md`.

## How to read the status column

- **stands**: the registered verdict is unchanged and no later entry narrows it.
- **qualified**: the verdict stands as registered, but a later finding or a
  dated note inside the entry narrows its scope or its meaning; the row says
  which.
- **superseded-in-part**: a specific sentence inside the entry has been
  superseded by a dated note in the same entry (never by a rewrite). Only
  F-22 carries this today; F-23 is the erratum finding that supersedes
  F-22's lane meaning (never its readouts). Dated 2026-10-01: F-15 and F-17
  carry DATED ERRATA of 2026-09-06 (F-24) and of 2026-09-14 (F-25; F-17's L3
  line is a DATED STATUS) inside their entries, and F-16 / F-18 carry DATED
  NOTES of both dates; their rows
  below quote the FINDINGS.md table's own status wording (F-15 / F-17:
  "stands against the 657-summary PROXY" plus the dated errata; F-16 / F-18:
  "stands; erratum-noted" plus the dated notes) rather than this page's
  three words, and the entry wins on any disagreement.

Three layers that this repo keeps apart, and that a reader must not conflate:

- **existence**: does the telemetry stream carry information about upcoming
  tokens that the decoder does not already have for free? Measured as probe
  accuracy margins at offsets >= 2 (kill criterion K-2; F-15, F-17).
- **conversion**: does that information turn into more emitted tokens per
  verifier call at a matched drafting budget? (kill criterion K-3; F-19,
  F-21). Two conversion attempts have been run and both were nulls.
- **reconstruction**: how much of the target model's anchor hidden state can
  be rebuilt linearly from the stream? (OQ-16 Stage R; F-22). A pass here
  licenses nothing at the conversion layer; F-23 then closed the lane
  because the target itself is free information under D-5.

Two later kinds of entry (added 2026-10-01): F-24 and F-25 re-test the
existence layer against a FULL free baseline ((a) ++ hashed token ids ++
z-scored h_a) at a registered reader and are criterion-bearing for F-15 /
F-17 through pinned consequence rules; F-26 sits outside the three layers
altogether - a prefetch hit-rate count on the OLMoE router stream,
registered NON-CRITERION as a K-6 datum, with its free-bigram twin carried
as a dated status line inside the entry.

The currency of every real-model conversion claim is emitted tokens per verify
call (estimand E6) at matched drafted-per-emitted budget (dpe); Phase 0
findings use acceptance rate. No wall-clock or speedup measurement exists
anywhere in the repo (D-9; K-5 untested).

Numbers: every number on this page is copied from the `FINDINGS.md` entry
named in its row or sentence; the evidence column lists committed files that
entry cites. Real-model intervals are 95% prompt-cluster bootstrap CIs unless
the entry says otherwise; synthetic runs are deterministic given the seed and
report no CI.

Vocabulary used in the table, in brief:

- **verifier / target p / draft q**: speculative decoding drafts gamma tokens
  from a small draft model q, and a large target model p accepts or rejects
  them (Leviathan rejection sampling) so that emitted tokens follow p exactly.
- **acceptance**: the per-position probability a drafted token is accepted;
  the analytic form is 1 - TV(p, q) (D-9).
- **bucket / glue / concept bucket**: a partition of the vocabulary (ground
  truth blocks in the synthetic world; k-means over the target's output
  embedding rows on real models). Glue buckets hold function tokens and are
  excluded from gates and predictions (D-7); the remaining buckets are
  "concept" buckets.
- **free information / free_lastp**: the target's distribution at the last
  verified position, which every speculative decoder computes anyway (D-5).
  Any telemetry claim is measured against it.
- **telemetry / S1 / S3**: what a device could observe about the target's
  forward pass without reading values. S1 = weight-slot occupancy taps on
  Llama-3.1-8B (a value-aware compute-tier signal); S3 = the expert ids
  chosen by OLMoE-1B-7B's routers (a pure address stream). S2 (KV pages) was
  never run.
- **anchor**: the block-start position where telemetry is read.
- **regime**: the exact measurement conditions on the entry's `- regime:`
  line; a finding cited outside its regime is a bug (D-4).

## Summary table

| id | date | arc | regime (short) | claim | headline number with CI | status | evidence |
|---|---|---|---|---|---|---|---|
| F-0 | 2026-08-28 | Synthetic world | Mathematical property of the Leviathan rejection scheme; any p, q on a shared vocabulary | The verifier reproduces the target distribution exactly even when the draft is arbitrarily steered, so steering can only change speed, never output quality | enumeration at atol 1e-12 over 200 random pairs plus adversarial edge cases (exact; no CI) | stands | tests/test_specdec.py; src/sideband/specdec.py |
| F-1 | 2026-08-28 | Synthetic world | 2000 random (p, q) pairs, vocab 2-64, sparsity-injected q, steered beta in [-6, 9] | Measured exactness sits at float64 epsilon and empirical sampling agrees within noise | worst closed-form deviation 2.2e-16; empirical max deviation 3.2e-4 over 500k samples (sigma about 7e-4; no CI) | stands | results/e01_verifier_exactness.json |
| F-2 | 2026-08-28 | Synthetic world | concept-HMM v0, draft_alpha swept; gamma=4; 24k positions x 3 seeds | Most rejections are cross-bucket and the share grows as the draft degrades; this bounds the addressable share of failures, not the gain | cross-bucket fraction 89.3% / 83.1% / 76.1% at draft_alpha 0.5 / 0.7 / 0.9; vanilla acceptance 0.546 / 0.618 / 0.694 (no CI) | stands (regime-bound; the real analog is F-10) | results/e02_crossbucket_audit.json |
| F-3 | 2026-08-28 | Synthetic world | concept-HMM v0; gamma=4; 16k positions; oracle policies | Always-on bucket boosting nearly self-cancels; gating the boost on draft-vs-prediction disagreement keeps the gain and skips the function-word tax | ungated peak +0.010 (0.6294 vs vanilla 0.6194 at beta=0.5), collapse to 0.4376 at beta=6; gated stale oracle 0.6389 at beta=3 (+0.0195), fresh oracle 0.6653 at beta=4 (+0.046) (no CI) | stands (synthetic); qualified on real models by F-12 | results/e03_oracle_ceiling.json |
| F-4 | 2026-08-28 | Synthetic world | concept-HMM v0, rho swept; gated beta=2.5; gamma=6; 14k positions; analytic acceptance | A prediction held for a whole block helps only when concept persistence comfortably exceeds gamma; otherwise it is net harmful at every offset | stale-minus-vanilla at offsets 1 -> 6: rho=0.6 -0.004 -> -0.026; rho=0.97 +0.018 -> +0.019 (no CI) | stands; became K-3's named mechanism (real persistence 0.027 in F-12 fails the hold rule) | results/e04_staleness_decay.json |
| F-5 | 2026-08-28 | Synthetic world | hardened telemetry, n_slots swept; gated beta=2.5; gamma=4; 12k positions | A narrow sideband with an inaccurate decoder is worse than no steering when ungated and harmless with a confidence gate | ungated recovery -152% (K=8) to +95% (K=1024); gated tau=0.5 -1% to +99%; decoder accuracy 0.16 to 1.00; stale-oracle ceiling +0.016 (no CI) | stands (the shape is the claim); qualified by F-7 (tau subsumed by centering) | results/e05_sidecar_recovery.json |
| F-6 | 2026-08-28 | Synthetic world | structural property of concept-HMM v0 | Steering from the last verified distribution and from a stale telemetry oracle give identical curves, so no synthetic telemetry win is possible | both best 0.6389 at beta=3, equal at every beta and gate (no CI) | stands (re-confirmed in F-7's caveat) | results/e03_oracle_ceiling.json; tests/test_steering_pipeline.py |
| F-7 | 2026-08-28 | Synthetic world | part A default world n=12000, seeds 400-401; part B hardened n=8000, seeds 401-402 | A centered posterior-mass bias beats single-bucket argmax boosting for every policy and width; the disagreement gate stays load-bearing | stale oracle +0.0165 vs +0.0124, fresh +0.0272 vs +0.0255, free_lastp +0.0152 vs +0.0124 over vanilla 0.6197; posterior oracle 0.6365 vs argmax 0.6343 (no CI) | stands (synthetic); qualified - the mechanism is dead on real models (F-12, F-13) | results/e06_posterior_mechanism.json |
| F-8 | 2026-08-28 | Synthetic world | same runs as F-2, bit-exact after the v0.2.0 pipeline rewrite | The analytic cross-bucket residual-mass estimator matches the sampled fraction with zero sampling variance and becomes the default estimand | 0.8924 vs 0.8933 (alpha 0.5), 0.8358 vs 0.8315 (0.7), 0.7624 vs 0.7611 (0.9); e03 vanilla 0.6194399309459379 bit-exact | stands (concordance replicated within 0.003 on real models in F-10) | results/e02_crossbucket_audit.json; src/sideband/pipeline.py |
| F-9 | 2026-08-28 | Synthetic world | posterior mechanism, gate, beta=2.5, gamma=4, n=16000, seeds 500-501; ideal-coding ledger | Priced in bits, dense per-position hints lose 20:1 while free steering saves bits at zero hint cost | vanilla 1.270 correction bits/token; free steering saves 0.100 bits/token; dense hint net -3.18 bits/token; break-even hint budget 0.162 bits/token (no CI) | stands as a v0 synthetic ledger; qualified - the free-steering half did not transfer (F-12) | results/e07_hint_rate.json |
| F-10 | 2026-08-29 | Real Phase 0 | REAL: Llama-3.1-8B-Instruct NF4 target + Llama-3.2-1B-Instruct bf16 draft; gamma=4; temperature 1.0; 210 prompts; seed 0; k-means buckets k in {256, 512, 1024} | Real rejections are mostly bucket-level disagreements; kill criterion K-1 does not fire and the quantization choice does not change the verdict | cross-bucket residual mass 0.778 [0.769, 0.787] (k=256), 0.812 [0.804, 0.820] (k=512), 0.863 [0.856, 0.870] (k=1024); mean acceptance 0.763; 11,287 rejections | stands; qualified by F-11 (glue haircut to 0.56-0.67) | results/real/audit_k512.summary.json; results/real/phase0a_verification.json |
| F-11 | 2026-08-30 | Real Phase 0 | same pair; glue by the K-7 rule (top-100 tokens of a 53,441-token target-only harvest, 80% frequency-mass cover) | Glue concentrates in 2-4 buckets per granularity; after excluding it the majority of rejections are still concept-to-concept jumps | concept-to-concept 0.565 [0.554, 0.575] (k=256), 0.610 [0.600, 0.621] (k=512), 0.674 [0.664, 0.684] (k=1024); glue tokens are 41% of generated text | stands (OQ-4 answered) | results/real/glue_phase0a_analysis.json; results/real/glue_k512.json |
| F-12 | 2026-08-30 | Real Phase 0 | same pair, Phase 0b; k=512 with glue excluded; posterior mechanism; disagree gate; two free variants x beta {1, 2, 3, 4} | Free-information steering never beats vanilla and the confirmatory arm is harmful; the disagreement gate is open about 94% of the time and consecutive-token bucket persistence is about 0.03 | best +0.0025 [-0.0028, +0.0079] (soft beta=1); confirmatory sharp beta=3 -0.0098 [-0.0155, -0.0039]; vanilla 0.7628; gate open 93.6-94.0%; persistence 0.027 | stands; its coarse-gating caveat (OQ-12) was closed negative by F-13 | results/real/phase0b_analysis.json; results/real/bucket_persistence_k512.json |
| F-13 | 2026-08-30 | Real Phase 0 | same pair, Phase 0c stage 1; coarse gating spaces k in {16, 32, 64}; {soft, sharp} x beta=3 | Coarsening restores the gate's selectivity but every arm still loses to vanilla: the free-information actuator is dead as built at every tested granularity | gate-open 0.55-0.56 (C=15), 0.67 (C=31), 0.80-0.81 (C=62) vs 0.94 (C=510); k16 soft -0.0029 [-0.0088, +0.0029] (the only straddle); k64 sharp -0.0252 [-0.0317, -0.0186] | stands; attribution caveat carried to F-14 | results/real/phase0c_analysis.json; results/real/oq12_diagnostics.json |
| F-14 | 2026-08-30 | Real Phase 0 | Phase 0c attribution rider; oracle_nextp at k=16, soft, beta=3 (a D-2-named non-causal ceiling) | A perfect per-position forecast converts to at most +0.007 acceptance through the bucket-bias actuator at coarse k; registered verdict STRADDLE | +0.0014 [-0.0043, +0.0069]; truth-informed gate opens at 15.9% of steerable positions (n=69,192) | stands (STRADDLE as registered; ceiling bounded at +0.0069 for this cell); the fine-k oracle cell is unrun | results/real/phase0c_oracle_analysis.json |
| F-15 | 2026-08-31 | Existence probes | REAL: NF4 Llama-3.1-8B; S1 shadow taps at layers {7, 15, 23, 31} (top-32-of-512 slots); seeds 0..7 (1,693,036 pairs) plus pinned replication seeds 8..11 (849,536 pairs); 30 test prompt clusters | Compute-tier weight-slot telemetry predicts the concept of tokens 2-3 ahead better than a probe on all 657 logged free summaries of p_a; K-2's existence question is answered YES for S1 | pinned triple L1_concept_k16/off2/linear replication +0.0141 [+0.0081, +0.0203]; margins +0.008..+0.044 top-1 over floors 0.41-0.59; 0/4 offset-4 triples re-fired | stands against the 657-summary PROXY (mechanism qualified by F-16; F-20 argues it is not obviously threatened); DATED ERRATUM 2026-09-06 (F-24): ABSORBED by the full free baseline at the registered reader at the pinned cells L1 offsets 2-3, TWIN-ROBUST at the corrected twin; DATED 2026-09-14 (F-25, OQ-18 at the registered reader): L2 ABSORBED; L3 NOT-SHOWN at the L3 group lens | results/real/probes_s1.json; results/real/probes_s1_replication.json |
| F-16 | 2026-08-31 | Existence probes | post-hoc P1 diagnostic at S1 (NON-CRITERION); prefix histogram block (t) = 560 dims; {L1, L2, L3} x offsets {2, 3}; both harvests | The S1 margin is not prefix-topic state: histograms of already-generated tokens predict about nothing and the margin passes the equal-dims noise control | (t) alone max abs(acc - floor) 4.3e-4; M2 L1/off2 +0.0177 [+0.0119, +0.0232]; measured dilution M2noise -0.0045..+3.3e-5 | stands; erratum-noted (dims 3265/1217, dated in the BLUEPRINT P1 outcome); dated note 2026-09-06 (F-24): the shift-17 equal-dims twin is NOT inert under a null direction, and the mechanism reading is moot for the S1 L1 off2-3 margin at the registered reader; dated note 2026-09-14 (F-25): mechanism reading moot at L2 at the registered reader | results/real/posthoc_topic_s1.json; results/real/posthoc_topic_s1_r.json |
| F-17 | 2026-09-01 | Existence probes | REAL: OLMoE-1B-7B-0125-Instruct NF4 (routers and lm_head unquantized); S3 = top-8-of-64 expert ids at 16 gates (1024 dims); seeds 0..7 (1,647,264 pairs) plus replication 8..11 (827,324 pairs) | Pure address-stream router ids predict the concept 2 tokens ahead (3-4 under coarse labels) beyond the free baseline; K-2 answered YES for S3 | pinned gate replication +0.0173 [+0.0133, +0.0221]; L3/off2 +0.0721 [+0.0652, +0.0792]; margins +0.006..+0.073 top-1 over floors 0.42-0.59 | stands against the 657-summary PROXY (qualified by F-18: about 1/10 of the L3 margin is topic-shaped; S2 unrun); DATED ERRATUM 2026-09-06 (F-24): ABSORBED by the full free baseline at the registered reader at the pinned cells L1 offset 2, TWIN-ROBUST at the corrected twin; DATED 2026-09-14 (F-25, OQ-18 at the registered reader): L2 ABSORBED; L3 SPLIT at the L3 group lens (fired on the replication harvest only) | results/real/probes_s3.json; results/real/probes_s3_replication.json |
| F-18 | 2026-09-01 | Existence probes | post-hoc P1-analog at S3 (NON-CRITERION); 72 cells per harvest, both S3 harvests | The S3 margin is not prefix-topic state at the histogram level; the one real topic component (L3 groups) is about a tenth of the tap's margin there | M2 L1_olmoe_k16/off2/linear +0.012958 [+0.008783, +0.016809]; L1/L2 M3 abs(point) <= 0.00094; L3/off3 M3 +0.006972 [+0.003302, +0.011127] | stands; erratum-noted (t dim is 560, identical to S1; dated 2026-09-01); dated note 2026-09-06 (F-24): the mechanism reading is moot for the S3 L1 off2 margin at the registered reader; the L3 statements are untouched; dated note 2026-09-14 (F-25): mechanism reading moot at L2 at the registered reader | results/real/posthoc_topic_s3.json; results/real/posthoc_topic_s3_r.json |
| F-19 | 2026-09-03 | Conversion attempt 1 | REAL Llama pair, NF4, RTX 3080 Ti; K-3 Attempt #1; arms vanilla gamma-4 / draft-confidence / (a)-probe / (c)-probe telemetry / gamma-6 control; 30 val + 210 fresh verdict prompts; estimand E6 | Adaptive block scheduling on the frozen S1 probes does not convert: telemetry ties vanilla in tokens per verify call, far below the registered bar; K-3 fires | arm4-vs-arm1 +0.006860 [-0.015024, +0.025572] against bar +0.062; val-tuned +0.060 shrank to +0.007; vanilla 3.020427 tokens/call, telemetry 3.027287 | stands (K-3 fired as registered); erratum-noted (threshold-search and arm-2 selection errata, dated) | results/real/k3_verdict_s1_arm4.summary.json; results/real/k3_verdict_s1_arm1.summary.json |
| F-20 | 2026-09-03 | Fold-back #1 | CPU analysis of the K-3 arm-1 byproduct logs (17,673 + 17,581 blocks x 4 offsets); closed-form ridge acceptance heads; 42 prompt clusters, 28,616 positions | The existence gate passes mechanically, but a five-seed stale-target control leaves the margin indistinguishable from zero-information draws; the free-features head beats the telemetry head outright | delta_noise +0.000763 [+0.000308, +0.001215]; stale-target primary +0.000643 [-0.000076, +0.001357]; delta_free -0.00286 [-0.00322, -0.00252] | qualified (the mechanical PASS stands by registration; its registered meaning is removed, pinned label ARTIFACT-DOMINANT) | results/real/oq15_stage1.json; results/real/oq15_stage1_rotcheck.json |
| F-21 | 2026-09-04 | Fold-back #1 | same pair; OQ-15 Stage C; arms vanilla / draft-confidence / head_free (657 dims) / head_tel (2705 dims); 30 val + 210 verdict prompts; E6 | The telemetry head ties vanilla and loses CI-clear to the identical policy driven by free features: CONVERSION-MODE NULL | C4-vs-C1 +0.002664 [-0.044719, +0.046727]; C4-vs-C3 -0.081846 [-0.132484, -0.035567]; vanilla 3.00827523663776 tokens/call, head_free 3.0927852831273355, head_tel 3.010939077751599 | stands (terminal for OQ-15) | results/real/oq15c_verdict_s3_arm7.summary.json; results/real/oq15c_verdict_s3_arm6.summary.json |
| F-22 | 2026-09-04 (addenda 2026-09-04 DR-3, 2026-09-05 DR-4) | Fold-back #2 | CPU analysis of four vanilla gamma-4 byproduct runs (70,529 blocks, two prompt populations); target = 4096-dim anchor hidden state h_a z-scored on TRAIN moments; multi-output ridge; 84 TEST clusters | Telemetry linearly reconstructs the anchor state above the noise twin and the free features (Stage R PASS), but the registered magnitudes are pathology-inflated; a free hashed token encoding (FREETOK) reconstructs slightly better; telemetry plus FREETOK (UNION) beats FREETOK; a second token comparator (FREETOK2, built to be stronger) landed CI-clear worse than FREETOK (COMPARATOR-TOOTHLESS), so "beyond p" stays unpriced | registered delta_noise +0.176469 [+0.130414, +0.251518], delta_free +0.204984 [+0.153698, +0.288162]; DR-1 tel_vs_trivial +0.250784 [+0.239316, +0.261616] (R^2 +0.253); DR-2 tel_vs_freetok -0.004792 [-0.007192, -0.002600]; DR-3 union_vs_freetok +0.065180 [+0.062411, +0.067705]; DR-4 freetok2_vs_freetok -0.003085 [-0.004984, -0.001280] | qualified; superseded-in-part (dated notes 2026-09-04 and 2026-09-05 inside the entry) | results/real/oq16_stage_r.json; results/real/oq16_stage_r_dr4.json |
| F-23 | 2026-09-05 | Fold-back #2 (closure) | Mathematical identity checked numerically on 48 pinned byproduct rows (the first 4 blocks of the first 3 prompts of each of the four vanilla gamma-4 verdict runs, sha-bound) against the cached Llama-3.1-8B-Instruct lm_head (untied, bias-free, 128256 x 4096) | The registered reconstruction target h_a is an exact linear function of the anchor's logits and hence of the full next-token distribution p, free information under D-5; the stream's reconstruction is a lossy copy of what the decoder already has; the Stage-A telemetry arms are struck pre-GPU; no partition branch claimed (limbo clause honored), mechanism TARGET-FREE | argmax match 48/48; top-32 overlap 0.9948 mean; full-logit inverse relative error 2.5e-8 median; top-k closed-form per-row R^2 +1.0000 (k = 4097) / +0.506 (2048) / +0.216 (512) / +0.078 (128) / +0.014 (32) | stands (terminal for OQ-16; every F-22 readout stands as pinned, its lane meaning superseded) | results/real/oq16_ha_identity.json; tools/ha_identity_check.py |
| F-24 | 2026-09-06 | Full-free re-tests | REAL: probe training only on the four committed Phase-3 harvests (S1 primary seeds 0..7 and replication 8..11 of the NF4 Llama-3.1-8B shadow-tap harvest; S3 primary and replication of the OLMoE-1B-7B router harvest); OQ-17 registration frozen at 1d1a7f8; full free baseline fplus = (a) 657 summaries ++ hashed top-32 token ids ++ z-scored h_a; registered reader = AdamW at mlp256, 30 epochs with the epoch selected on val (one to three passes at these cells); pinned L1 offset-2 cells (S1 also offset 3); 30 test prompt clusters | The F-15 and F-17 existence margins are ABSORBED by the full free baseline at the registered reader on both harvests of both sources: no MATERIAL (+0.005) equal-dims margin; telemetry on top of the full free baseline still adds about +0.003 (Mt) CI-clear on three of four harvests, matched by the corrected twin's own gain (Mn_r +0.0032 / +0.0020 at S1), under which Mt stops being evidence of telemetry information; the corrected-twin diagnostic read TWIN-ROBUST at both sources; the pinned prediction (S1 SURVIVES-FULL-FREE; S3 SPLIT or NOT-SHOWN) failed on both sources | gate D S1 +0.0002 [-0.0012, +0.0015] / +0.0012 [-0.0003, +0.0028]; S3 +0.0003 [-0.0013, +0.0020] / +0.0001 [-0.0019, +0.0021]; every D CI95 upper below +0.005; Mt S1 +0.0034 [+0.0021, +0.0048] / +0.0033 [+0.0012, +0.0052], S3 +0.0033 [+0.0013, +0.0054] / +0.0013 [-0.0008, +0.0035] | stands (criterion-bearing for F-15 / F-17 through the pinned OQ-17 consequence rules; K-2 FIRED at the registered reader at the pinned L1 cells of both sources per the 2026-09-06 STATUS; critic-recomputed three times) | results/real/fullfree_s1.json; results/real/fullfree_s3.json; results/real/fullfree_s1_twin.json; results/real/fullfree_s3_twin.json (each with its replication and state file); tools/run_fullfree.py; tools/run_fullfree_twin.py |
| F-25 | 2026-09-14 | Full-free re-tests | the same four harvests and full free baseline; OQ-18 registration frozen at 15c4e9c; coarse labels L2 / L3 (every L3 label read at the L3 group lens: S1 one mega-group of 455/510 concepts, S3 two mega-groups of 268 and 193); read under the 2026-09-07 leak-rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band) - a disclosed post-hoc reroute around a fired kill condition, a fresh test only at the other three harvests; the registered raw leg is reported at every cell and was above its band at two (S1 L3 +0.0132, S1_r L2 +0.0105); at S1 L3 the amended pass is not a CI-clear null (dE_br +0.0026, upper +0.0054) | At the registered reader with the corrected twin: S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2 ABSORBED, S3 L3 SPLIT (fired on the replication harvest only; the entry's post-hoc line reads the fire as inflated by up to 0.0067 by the twin's own cost, not as half a survival); prediction 3/4 held on labels; the L1 verdict (F-24) untouched; no all-space sentence issues | gate D S1 L2 +0.0011 [-0.0001, +0.0023] / +0.0006 [-0.0007, +0.0020]; S1 L3 +0.0010 [-0.0006, +0.0026] / +0.0012 [-0.0015, +0.0040]; S3 L2 +0.0018 [+0.0008, +0.0030] / +0.0003 [-0.0009, +0.0013]; S3 L3 +0.0041 [+0.0026, +0.0055] / +0.0053 [+0.0019, +0.0091] with Mt +0.0010 [-0.0012, +0.0030] / -0.0014 [-0.0041, +0.0016] | stands; registered-reader scope; consequences executed on F-15 / F-17 / F-16 / F-18 / K-2 as pinned; the rider amendment is disclosed in the entry's bracketed preface | results/real/fullfree_coarse_s1.json; results/real/fullfree_coarse_s3.json (each with its replication and state file); tools/run_fullfree_coarse_amended.py; results/real/fullfree_coarse_s3.rider_v1.json; results/real/fullfree_coarse_s3_r.rider_v1.json (the frozen-instrument payloads, preserved) |
| F-26 | 2026-09-15 (dated status lines 2026-10-01, 2026-10-02) | OQ-9 stage 1, prefetch | REAL: CPU-only readouts on the two committed S3 harvests of OLMoE-1B-7B-0125-Instruct (NF4, bf16 routers; 210 prompts x 256 tokens; primary seeds 0..7, replication 8..11 on the same prompts); the sorted top-8 expert ids at 16 gates, no router weights; estimand = hit rate of the next forward's expert sets at residency budget B of 64 per gate; linear ridge readers, 30 test prompts, prompt-cluster bootstrap CI95; registration frozen at c4c4511; NON-CRITERION, a K-6 datum | The router address stream is a prefetch source with headroom over a recency cache and a material margin over the free input token at B = 16, j = 1 (stage PREFETCH-HEADROOM, the seed replication agrees on every label); the margin is below the +0.05 floor at B = 32 at j = 1 and above it at j = 2 / 3 / 4 (+0.0545 / +0.0534 at j = 2; CI lower above the floor at j = 3 / 4 only); the critic's scope objection (the equally free previous token is not in the one-token baseline and gate 0 routes on it; F-26's GATE-0 NOTE records an unresolved alternative, that the stored gate-0 slot lags one forward) was answered by the equal-dims free-bigram twin on 2026-10-01: SURVIVES at that encoding, with a coverage caveat (the material part of the surviving margin sits on positions whose token key the train tables never saw); nothing reads it as context information or as support for the sideband premise | B = 16, j = 1: recency 0.5197 / 0.5155, free one-token table 0.8111 / 0.8036, history 0.8064 / 0.8056, history ++ token 0.9143 / 0.9108; HISTORY +0.2867 [+0.2784, +0.2939] / +0.2901 [+0.2808, +0.2978]; ADDRESS-BEYOND-TOKEN +0.1032 [+0.0926, +0.1146] / +0.1072 [+0.0952, +0.1206] (B = 32, j = 1: +0.0405 / +0.0434; B = 32, j = 3 / 4: +0.0683 / +0.0654, +0.0698 / +0.0669); INTRA-FORWARD +0.4861 [+0.4710, +0.5009] / +0.4816 [+0.4663, +0.4975]; DRAFT ceiling (horizon 2) +0.1556 [+0.1512, +0.1599] / +0.1545 [+0.1495, +0.1594]; twin (2026-10-01): D_eq +0.0609 [+0.0514, +0.0712] / +0.0659 [+0.0547, +0.0788], D_add +0.0661 [+0.0569, +0.0762] / +0.0705 [+0.0592, +0.0834], at B = 32 (j = 1, the twin's only horizon; the j = 2..4 margins are over the one-token table and were never tested against the bigram twin) D_eq +0.0261 / +0.0287; covered-key D_eq +0.0454 / +0.0472 on val (unregistered diagnostic, not evidence) | stands (NON-CRITERION; dated status line 2026-10-01: SURVIVES at this encoding with the coverage caveat; K-5 / K-6 stay UNTESTED; prior art occupies every cell; the stratified covered-vs-fallback test read ran on 2026-10-02 (FALLBACK-LOCATED / PT-SURVIVES on both harvests, both gates straddling the floor: the caveat indicated, not settled; next rung R2, a free baseline whose encoding handles unseen and sparse keys)) | results/real/prefetch_s3.json; results/real/prefetch_s3_r.json; results/real/prefetch_bigram_s3.json; results/real/prefetch_bigram_s3_r.json; results/real/prefetch_strat_s3.json; results/real/prefetch_strat_s3_r.json (each with .meta.json and .state.jsonl); tools/run_prefetch_readouts.py; tools/run_prefetch_bigram.py; tools/run_prefetch_strat.py |

## Arcs

### Synthetic world (F-0 .. F-9)

The first arc built the verifier and a synthetic concept-HMM testbed (tokens
grouped into ground-truth concept buckets, with a tunable draft) and used it
to fix the shapes that every later experiment inherits. The verifier is
exact by enumeration and at float64 epsilon under measurement (F-0, F-1), so
acceptance rate is the only outcome any steering experiment can move. In this
world most rejections are cross-bucket (76.1% to 89.3%, F-2), always-on
bucket boosting self-cancels unless gated on disagreement (F-3), a
block-held prediction ages out unless concept persistence comfortably exceeds
gamma (F-4), a narrow sideband with a weak decoder is harmful ungated and
harmless gated (F-5), a centered posterior bias dominates argmax boosting
(F-7), and dense per-position hints lose 20:1 in a bit ledger (F-9). The
structural result is F-6: steering from free information and from a stale
telemetry oracle are identical curves here, so this world can never show a
telemetry win and the existence question had to move to real models.

Kill-criterion outcome: none adjudicated. K-2 is provably un-adjudicable in
this world (F-6); K-4 received only a shape (F-5). The mechanism rules from
F-3, F-7 and the "free steering pays" half of F-9 were later qualified on real
models (F-12, F-13).

### Real Phase 0 (F-10 .. F-14)

The first GPU results ran a Llama-3.1-8B-Instruct NF4 target with a
Llama-3.2-1B-Instruct bf16 draft over 210 committed prompts (F-10). Rejections
are overwhelmingly bucket-level (residual mass 0.778 to 0.863 by k, F-10), and
after glue buckets are excluded by the pre-registered K-7 rule the majority
are still concept-to-concept jumps (0.565 to 0.674 by k, F-11), so the
addressable share of failures is real. Free-information bucket-bias steering,
however, never beats vanilla and is harmful at the confirmatory setting
(-0.0098 [-0.0155, -0.0039], F-12); the diagnosis is a gate that is open about
94% of the time over 510 fine buckets and a bucket persistence of 0.027 that
makes any block-held prediction stale by construction. Coarsening the gating
space restores the gate's selectivity but every arm still loses (F-13), and a
perfect non-causal forecast at coarse k converts to at most +0.0069 acceptance
through this actuator (F-14).

Kill-criterion outcome: K-1 (rejections not cross-bucket) did not fire (F-10);
K-7 (glue tax cannot be neutralized) did not fire as written (F-11). The
free-information actuator was killed as built (F-12, F-13, F-14), which set
the D-5 free baseline at zero on real models and blocked Phase 4 until a
different actuator existed; no K-3 verdict was reached here.

### Existence probes (F-15 .. F-18)

Phase 3 asked kill criterion K-2's question directly: do probes on free
summaries plus telemetry beat probes on free summaries alone at offsets >= 2?
At S1 (weight-slot occupancy taps on the Llama target) the pinned replication
triple re-fired at +0.0141 [+0.0081, +0.0203] and all eight offset-2/offset-3
triples re-fired, while free information dies by offset 3 and offset 4 is not
established (F-15). At S3 (OLMoE router expert ids, a pure address stream) the
pinned gate re-fired at +0.0173 [+0.0133, +0.0221] with the entire firing set
reproducing cell-for-cell (F-17). Two registered post-hoc diagnostics then
tested the cheapest software substitute, concept histograms of the already
generated prefix: at both sources it predicts about nothing and the telemetry
margin passes an equal-dimension alignment-destroyed noise control (F-16,
F-18), with one honest qualifier that about a tenth of S3's coarse-group
margin is genuinely topic-shaped.

Kill-criterion outcome: K-2 survived at S1 (F-15) and at S3 (F-17), both on
pinned fresh-seed replications, against the 657-summary PROXY; S2 (KV pages)
was never run. Dated 2026-10-01: at the registered reader of the FULL free
baseline K-2 FIRED at the pinned L1 cells of both sources (F-24) and at L2
(F-25), with L3 OPEN; see the full-free re-tests arc below. Every entry in
this arc carries the same caveat: existence is not an actuator, and K-3
(conversion) was untouched.

### Conversion attempt 1 (F-19)

K-3 Attempt #1 froze the S1 probes and used them to decide, per block, when to
stop drafting early or extend the block, comparing five arms at matched
drafting budget on 210 fresh prompts with emitted tokens per verify call as
the estimand. The telemetry arm landed at +0.006860 [-0.015024, +0.025572]
over vanilla against a registered bar of +0.062, and a val-tuned advantage of
+0.060 shrank to +0.007 on fresh prompts (F-19). The pairwise budget guard was
breached twice by a real mechanism (the extend channel inflates budget on
harder prompts), and an information-free gamma-6 control showed raw
tokens per call is buyable without information, which is why matched budget
was load-bearing.

Kill-criterion outcome: K-3 fired exactly as registered. Per the dated
fold-back count amendment this opened a two-lane fold-back (OQ-15, then
OQ-16, hard stop after the second); the per-offset gating rules, the
staleness map, and the byproduct logs were the registered salvage.

### Fold-back #1 (F-20, F-21)

OQ-15 trained ridge heads to predict per-position analytic acceptance from the
K-3 byproduct logs. The Stage I existence gate passed mechanically at
delta_noise +0.000763 [+0.000308, +0.001215], but a five-seed stale-target
control (targets replaced by within-prompt permutations, so no block-aligned
information exists for any head) produced margins of the same magnitude and
spread, and the free-features head beat the telemetry head outright
(delta_free -0.00286 [-0.00322, -0.00252]); the pinned label is
ARTIFACT-DOMINANT and the registered meaning of the pass is removed (F-20).
Stage C then drove live stop/extend decisions from the frozen heads on 210
fresh prompts: the telemetry head tied vanilla (+0.002664 [-0.044719,
+0.046727]) and lost CI-clear to the same policy on free features
(-0.081846 [-0.132484, -0.035567]), the live mirror of F-20's delta_free
(F-21). A seed-2 budget-guard breach was traced to a selection-time gap
between arms, fixed by a registered re-freeze, and the seed-3 rerun cleared
the guard on every leg.

Kill-criterion outcome: by the pinned partition, Stage I PASSED plus Stage C
NOT-WIN equals CONVERSION-MODE NULL, the second conversion null on the lane,
which hands off to OQ-16 rather than stopping the lane. One descriptive
observation survives without a registered CI: head_free posted the highest
tokens per call on both seeds at a budget below vanilla's.

### Fold-back #2 (F-22 with DR-1 .. DR-4; closed by F-23)

OQ-16 asked how much of the anchor hidden state h_a (the vector SD^2-style
draft steering would inject) survives linear reconstruction from the S1
stream. Stage R PASSED against its own pinned expectation of a dilution null:
registered delta_noise +0.176469 [+0.130414, +0.251518] and delta_free
+0.204984 [+0.153698, +0.288162] (F-22). The critic round found two
out-of-support test prompts inflating those magnitudes by about 25%; under
the registered DR-1 train-support clip the deployable reading is
tel_vs_trivial +0.250784 [+0.239316, +0.261616], an R^2 of +0.253 for
telemetry. DR-2 showed a free hashed encoding of the top-32 next-token ids
(FREETOK) reconstructs h_a slightly better than telemetry
(-0.004792 [-0.007192, -0.002600]); DR-3 showed telemetry plus that encoding
(UNION) beats FREETOK by +0.065180 [+0.062411, +0.067705] on both prompt
populations; DR-4's second token comparator (FREETOK2, intended to be stronger) landed COMPARATOR-TOOTHLESS, CI-clear worse than FREETOK
(-0.003085 [-0.004984, -0.001280] against FREETOK), so whether telemetry adds
information "beyond p" itself remains unpriced.

F-23 (2026-09-05) then closed the lane by dated erratum. The target h_a is
the verifier's final-norm output at the anchor, the lm_head input, and the
lm_head is an untied, bias-free linear map of full column rank, so the
anchor's logits determine h_a exactly and the full next-token distribution p
(free information under D-5) determines it up to floating-point error:
full-logit inverse relative error 2.5e-8 median, top-4097 log-prob recovery
per-row R^2 +1.0000, top-32 recovery R^2 +0.014, on 48 pinned rows against the
cached lm_head. The FREE and FREETOK arms were lossy proxies for p itself;
the stream's reconstruction is a lossy copy of what the decoder already has;
"beyond p" is priced at this target (nothing is).

Kill-criterion outcome: no kill verdict; K-3 stays fired from F-19. Stage A
(SD^2-style draft-side injection with arms vanilla / oracle_h / free_inject =
FREETOK / tel_inject = UNION) was frozen pre-GPU at commit 2e44105 and closed
the same day by the dated OQ-16 erratum (F-23): the telemetry arms are struck
because their target follows exactly from the verifier's own p; the oracle
arm is a free-actuator question outside the lane (own registration required
if it ever runs); no partition branch is claimed - the limbo clause forbids
re-labeling a never-run stage a null and the partition's VOID precedent
applies - mechanism TARGET-FREE. The fold-back hard stop holds;
no third mechanism is authorized.

### Full-free re-tests (F-24, F-25; added 2026-10-01)

After F-23 the question moved one level up: not "is the reconstruction
target free" but "does the existence margin itself survive a FULL free
baseline" - the 657 summaries of p_a plus a hashed multi-hot of the anchor's
top-32 next-token ids plus the z-scored anchor state h_a, read by a
registered AdamW reader at mlp256 (30 epochs, the epoch selected on val;
one to three passes at F-24's pinned L1 cells, more at F-25's L2 / L3 cells,
where the per-cell best epochs are in the payloads), with an equal-dims
alignment-destroyed twin pricing dilution. OQ-17 (F-24) ran it at the pinned
L1 offset-2 cells of both sources on both harvests: every gate D has its CI95
upper below the +0.005 materiality floor (S1 +0.0002 [-0.0012, +0.0015] /
+0.0012 [-0.0003, +0.0028]; S3 +0.0003 [-0.0013, +0.0020] / +0.0001 [-0.0019,
+0.0021]), the registered ABSORBED condition (every D row, linear and
offset-3 included, with its CI95 upper below +0.005 and no fire on either
harvest), while telemetry on top of the full free baseline still adds about
+0.003 (Mt) CI-clear on three of four harvests - matched by the corrected
twin's own gain (Mn_r +0.0032 [+0.0016, +0.0050] / +0.0020 [+0.0002, +0.0037]
at S1; the S3 pair is in the entry), under which Mt stops being evidence of
telemetry information. The pinned prediction (S1 SURVIVES-FULL-FREE; S3 SPLIT
or NOT-SHOWN) failed on both sources. The S1 critic recompute found the
registered shift twin NOT inert; a post-hoc diagnostic, registered before it
ran, re-read the gate against a corrected prompt-level-deranged twin:
TWIN-ROBUST at both sources, so the null does not depend on the control.
OQ-18 (F-25) extended the same test to the coarse labels L2 / L3. Its
registered leak rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01
band); a dated amendment replaced that leg with a twin-referenced
dependence-excess leg after the fire - disclosed in the entry's preface as a
post-hoc reroute around a fired kill condition, fresh only at the other three
harvests, with a positive control confirming the amended leg fires on a
literal non-causal block; the registered raw leg is reported at every cell
and was above its band at two (S1 L3 +0.0132, S1_r L2 +0.0105), and at S1 L3
the amended pass is not a CI-clear null (dE_br +0.0026, upper +0.0054).
Labels: S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2 ABSORBED, S3 L3 SPLIT (fired on
the replication harvest only, D +0.0053 [+0.0019, +0.0091] decomposing into
Mt -0.0014 [-0.0041, +0.0016] and the twin's own cost Mn_r -0.0067, so the
entry's post-hoc line reads it as inflated by up to 0.0067 and not as half a
survival), every L3 label read through the lopsided group lens the
registration names.

Kill-criterion outcome: K-2 FIRED at the registered reader at the pinned L1
cells of both sources (the 2026-09-06 STATUS in docs/WHY_THIS_DIES.md: the
existence layer is NOT SHOWN anywhere at that reader at L1, and the
stronger-reader residual is the one named path to overturn) and at L2 at
both sources (the 2026-09-14 STATUS); S1 L3 and S3 L3 are OPEN at the
full-free level (NOT-SHOWN / SPLIT). F-25 adds no all-space sentence (not all
four (source, space) pairs read ABSORBED). Dated errata inside F-15 / F-17
and dated notes inside F-16 / F-18 carry the consequences; the original
wording stays beside them.

### OQ-9 stage 1, prefetch (F-26 and its free-bigram twin; added 2026-10-01)

With the thesis closed negative at the registered reader, the lane turned to
the prefetch half of OQ-9 on the committed OLMoE router harvests - cells the
registration pins as OCCUPIED (address-only history tables, cross-layer
routing predictors, and draft-conditioned expert prefetch, SP-MoE; the
history and cross-layer ids to verify) - measured here with the record's own
free baseline and no model forward. The estimand is a hit
rate: of the next forward's eight experts per gate, the share inside a
resident set of B of 64, linear ridge readers, 30 test prompts. At B = 16,
horizon 1, a recency cache covers 0.5197 / 0.5155, the free one-token train
table 0.8111 / 0.8036, the routing history alone 0.8064 / 0.8056, and history
plus the token 0.9143 / 0.9108 (F-26). The four readings all read SIGNAL:
HISTORY +0.2867 / +0.2901 over the cache, ADDRESS-BEYOND-TOKEN +0.1032
[+0.0926, +0.1146] / +0.1072 [+0.0952, +0.1206] over the one-token table
(below the +0.05 floor at B = 32 for j = 1: +0.0405 / +0.0434, while the
B = 32 margin at j = 3 / 4 reads +0.0683 / +0.0654 and +0.0698 / +0.0669 with
CI lower above the floor), INTRA-FORWARD +0.4861 /
+0.4816 (gate l from the earlier gates of the same forward), and the
perfect-draft ceiling at horizon 2 +0.1556 / +0.1545; stage label
PREFETCH-HEADROOM, the seed replication agreeing on every label. The landing
critic's one blocking objection was on interpretation: the previous token is
exactly as free as the current one, is not in the one-token baseline, and
gate 0 routes on it (an unresolved alternative, that the stored gate-0 slot
lags one forward, is recorded in F-26's GATE-0 NOTE). That became the free-bigram twin, registered as a dated
amendment with both predictions pinned (the critic's: the margin drops to or
below the floor) and run on 2026-10-01: with the previous token in the
baseline at equal dims the address block still adds +0.0609 [+0.0514,
+0.0712] / +0.0659 [+0.0547, +0.0788] (D_eq) and the address stream over the
free bigram +0.0661 / +0.0705 (D_add) - SURVIVES; both pinned modal
expectations had put D_eq below material (the critic's clause FAILED, the
assistant's modal label MISSED) - while the free previous token accounts for
0.4104 / 0.3858 of the re-measured margin (point ratios) and both readings
fall below the floor at B = 32 (the twin ran at horizon 1 only; the horizon
2..4 margins are over the one-token table and were never tested against the
bigram twin). The critic's coverage caveat is carried on
every text: on val the covered-key D_eq is +0.0454 / +0.0472, below the
floor, against +0.12..+0.45 on the primary where a token key is unseen (an
unregistered diagnostic, not evidence), so the material part of the surviving
margin sits where the free tables are blind; the diagnostic locates the
margin without naming its mechanism, and nothing in the entry reads any of
this as context information in the address stream or as support for the
sideband premise. F-26's post-hoc reading (NOT a registered readout; it
changes no label and licenses nothing) records that ADDRESS-BEYOND-TOKEN
stays near +0.10 at every horizon 1..4 (+0.1032 to +0.0933 primary, +0.1072
to +0.0912 replication) while the token's own margin over the cache decays
from +0.2913 to +0.0427 (+0.2881 to +0.0415), with the entry's own qualifier
that "routing history" may be standing in for free token history; the twin
tested horizon 1 only.
(2026-10-02: the stratified read ran — FALLBACK-LOCATED / PT-SURVIVES on
both harvests, both gates straddling the floor: covered-position D_eq
+0.0463 / +0.0481 below the floor with the floor inside the CI, unseen-key
+0.1940 / +0.1741; the caveat indicated, not settled; next rung R2, a free
baseline whose encoding handles unseen and sparse keys; F-26's second dated
status line)

Kill-criterion outcome: none; F-26 is NON-CRITERION for every existing
finding and a K-6 datum only (a count, not bytes, latency or a boundary
argument; K-6 stays UNTESTED by its dated STATUS lines of 2026-09-15,
2026-10-01 and 2026-10-02, K-5 by the 2026-09-05 one). Prior art occupies every cell as pinned. The steer half of OQ-9
is PARKED (no actuator in the record converts). The stratified covered-vs-fallback
read of D_eq on the TEST split, with a free arm from the harvest's stored p_t
summaries, ran on 2026-10-02 (FALLBACK-LOCATED / PT-SURVIVES on both harvests,
both gates straddling the floor: the caveat indicated, not settled); the next rung
is R2, a free baseline whose encoding handles unseen and sparse keys; stage 2 (a real
draft partner for OLMoE) is an option under its own registration, not a plan.

## How findings relate

A short dependency list: which findings qualify, confirm, or bound which.

- F-0 and F-1 underwrite every later acceptance number: the verifier is
  exact, so no steering result can be blamed on verifier drift (D-3).
- F-2 -> F-8 -> F-10: the synthetic cross-bucket share motivated the analytic
  estimator, which replicated on real models within 0.003 (F-10), and F-11
  then haircut F-10's bucket-level share (0.78-0.86) to a concept-level share
  (0.56-0.67) by excluding glue.
- F-3, F-7 (gate and posterior mechanism, synthetic) are qualified by F-12
  and F-13: on real models the gate is uninformative at fine k and the
  mechanism loses at every tested granularity; F-14 bounds the same
  actuator's oracle ceiling at coarse k at +0.0069.
- F-4's hold rule is shown to fail on real models by F-12's measured
  persistence of 0.027 (F-12's by-offset analytic table is flat, so
  within-block staleness was not the limiting factor there); F-4 is the
  mechanism named in K-3's kill text.
- F-5 is qualified by F-7 (the confidence gate is subsumed by centering); F-6
  is re-confirmed by F-7's caveat and is why K-2 could only be adjudicated on
  GPUs.
- F-9's "free steering pays" half is qualified by F-12 (the real free baseline
  is zero); its "dense hints lose" shape is the standing constraint for OQ-7.
- F-12 sets the D-5 denominator to zero and removes K-2's fold-to-free
  salvage; F-13 closes F-12's OQ-12 caveat negative; F-14 carries F-13's
  attribution caveat as a registered STRADDLE.
- F-15 (S1 existence) is mechanism-qualified by F-16; F-17 (S3 existence) is
  mechanism-qualified by F-18. F-20 states that F-15 and F-17 are not
  obviously threatened by its own stale-target result (different readout,
  margins about 20x larger, far more training anchors).
- F-19 consumes F-15's probes and is the first conversion null; F-20 and
  F-21 consume F-19's byproduct logs: F-20 is a prediction-layer result (the
  telemetry head loses to the free head, delta_free CI-clear negative) and
  F-21 is the second conversion null (the telemetry-head arm loses to the
  free-head arm at matched budget, CI-clear).
- F-22 consumes the same byproduct logs at the reconstruction layer. Its
  registered magnitudes are qualified by DR-1 inside the entry; its DR-2
  sentence "ties a free encoding of p" and its K-2 location are superseded in
  DR-3's qualified sense by a dated note; DR-4 leaves "beyond p" unpriced.
  F-22 explicitly does not re-fire K-2 (that verdict was at the existence
  layer on a different target) and licenses no conversion claim.
- F-23 consumes the same byproduct rows plus the cached lm_head. It
  supersedes F-22's lane meaning (the target is free information) without
  touching any F-22 readout, and it leaves F-15/F-17 standing: their targets
  are future-position concepts that the anchor's p does not determine, and
  the OQ-6 h-probe (a linear probe on the full logit vector under the
  identity) adds nothing over their free arm at the pinned cells; a
  nonlinear-in-p free baseline was never run.
- Entries with dated errata (F-16, F-18, F-19, F-22, and F-23 as the OQ-16
  erratum finding) keep their original
  wording; the dated erratum is the correction of record (inside the entry
  for F-18 and F-22; in the docs/BLUEPRINT.md block the entry names for
  F-16 and F-19).
- (added 2026-10-01) F-24 consumes the four Phase-3 harvests of F-15 / F-17
  and is criterion-bearing for both through pinned consequence rules: dated
  errata inside F-15 and F-17 (ABSORBED at the registered reader at the
  pinned L1 cells), dated notes inside F-16 / F-18 (mechanism readings moot
  at those cells), and the K-2 STATUS of 2026-09-06. F-23's identity is why
  "full" means (a) ++ TOK ++ h_a: h_a is the free information p_a determines.
- (added 2026-10-01) F-25 extends F-24 to L2 / L3 at the registered reader
  with the corrected twin; its consequences are dated into F-15 / F-17 (L2
  ABSORBED at both; S1 L3 NOT-SHOWN, S3 L3 SPLIT) and F-16 / F-18 (mechanism
  reading moot at L2); it leaves the L1 verdict of F-24 untouched.
- (added 2026-10-01) F-26 is outside the three layers: a prefetch hit-rate
  count, NON-CRITERION, touching no F-15 / F-17 / F-24 / F-25 sentence; its
  dated addenda are its post-hoc line of 2026-09-15 and the free-bigram twin's
  status line of 2026-10-01 (with, from 2026-10-02, the stratified read's status
  line beside it); the twin's line answers the landing critic's scope objection at one encoding and
  carries the coverage caveat (left indicated, not settled, by the
  2026-10-02 stratified read); the K-6 STATUS lines of 2026-09-15,
  2026-10-01 and 2026-10-02 record it as a count, never as economics.

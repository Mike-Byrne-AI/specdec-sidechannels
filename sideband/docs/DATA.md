# Data inventory

License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).
Repository: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`, folder sideband/. Inventory taken 2026-09-05 at HEAD 8542ef5 (2e44105 plus the release-hygiene commit, which touches no result) on the
GPU box (RTX 3080 Ti, 12 GB), where the gitignored raws still exist. Every
count, shape and size below was read from a file in this session; shapes were
taken with `np.load` on one file per family.

Two tiers. COMMITTED: `git ls-files results` = 371 files, 100,825,557 bytes
(363 under results/real, including 27 `*.state.jsonl` evidence files and 2
npz). GITIGNORED raws on this box: 3,894 files, 13,369,799,824 bytes = 24
harvest npz (10,131,081,744 B) + 2,160 k3 byproduct npz (1,797,516,744 B) +
1,710 oq15c byproduct npz (1,441,201,336 B). Every raw is bound by sha256 in a
committed meta or summary; spot-checks this session all matched (the four run
summaries named in the oq16 state header, p000/p209 of k3_verdict_arm1,
shadow_s0.npz, k3_probe_weights.npz, oq15_head_weights.npz, the prompt file
and probe-weights shas in k3_verdict_arm1.meta.json).

Model pairs and settings, from the metas: target `meta-llama/Llama-3.1-8B-Instruct`
loaded `nf4-double-quant-bf16compute`, draft `meta-llama/Llama-3.2-1B-Instruct`,
`gamma_base 4`, `gamma_max 6`, `temperature 1.0`, `max_new 256`, chat template
with the date pinned to `26 Jul 2024`, torch 2.6.0+cu124, transformers 4.57.3,
numpy 2.3.5; the MoE source is `allenai/OLMoE-1B-7B-0125-Instruct` with the 16
routers and lm_head kept bf16 (`gates_verified_unquantized 16`). House terms (everything else - glue and concept buckets, K-3 / OQ-15C, the
verdict / val / tapcal run kinds, b_ref, stale seeds, FREETOK / UNION /
FREETOK2, binding gate, winner's curse, analytic acceptance - is defined in
docs/GLOSSARY.md):
an *anchor* is the last verified position at the start of a draft block;
*offset j* is the j-th token after it (offset 1 = the token sampled from the
anchor's own distribution p_a); *slots* are the top-32-of-512 hashed weight-slot
ids per tapped layer (source S1) or the top-8-of-64 expert ids per MoE gate
(S3); a *byproduct* is the per-block log a K-3 / OQ-15C arm writes.

## Assets

### (a) Vanilla gamma-4 verdict byproducts, four runs (GITIGNORED) + committed sidecars

- Location: `results/real/{k3_verdict_arm1,k3_verdict_s1_arm1,oq15c_verdict_arm1,oq15c_verdict_s3_arm1}.jsonl.byproduct/p000..p209.npz`; sidecars `<run>.gen.jsonl`, `.stats.jsonl`, `.summary.json`, `.meta.json` committed (`<run>.jsonl` itself is a 0-byte marker).
- Binding: `summary.json.byproduct_sha256` (210 entries per run); `sideband.outcome_head.verify_byproduct` refuses missing, extra or mismatched files.
- Contents (np.load on k3_verdict_arm1 p000.npz, 838,212 B, 83 blocks): `anchor_pos (n,) int32` [43..297]; `slots (n,4,32) int16` in -1..511; `h (n,4096) float16` (model.norm output at the anchor); `mass16/32/64/512 (n,k) float16`; `entropy (n,) float32` (units undocumented in the metas); `argmax int32`; `top_ids (n,32) int32`; `top_p (n,32) float16`; `probe_pred_a/probe_pred_c (n,2) int32` and `probe_conf_a/c (n,2) float32` (frozen L1_concept_k16 probes at offsets 2,3); `q_sig (n,2) float32` (draft q of the proposed token at drafted slots 1,2); `gamma_used int16`, `stop_pos int8`, `extend int8`, `accepted int16` 0..4; `proposed (n,6) int32` (-1 pad); `acc_flags (n,6) int8` (1 accepted / 0 rejected / -1 unreached); `analytic (n,6) float32` = 1 - TV(p_j, q_j), the per-slot analytic acceptance probability (TV = total variation distance between the target and draft distributions at drafted slot j; D-9), NaN pad, exactly one third; `draft_class (n,6) int32`; `n_blocks` scalar.
- Counts (summary.json `totals`): 17,581 / 17,673 / 17,632 / 17,643 blocks = 70,529 (F-22); tokens per verify call 3.032023206871054 / 3.020426639506592 / 3.0257486388384756 / 3.00827523663776; drafted per emitted 1.319251116197051 / 1.3243162233046084 / 1.3219868791002811 / 1.3296655675930287. gen.jsonl: 210 rows `{prompt_idx, orig_prompt_idx, run_id, prompt_len, generated_ids}`, prompt_len 42..59, generated length 93..260 (per-run minima 96 / 151 / 146 / 93). stats.jsonl: 210 rows with n_blocks, n_proposed, n_accepted, acceptance_rate, analytic sums by offset, n_stop_blocks, n_extend_blocks, seconds, peak_vram_gb (7.77-7.8).
- Provenance: `tools/run_k3_arms.py` over `src/sideband/real/hf_specdec.py` + k3_live.py; seeds 0/1 on data/prompts_k3_verdict.jsonl, seeds 2/3 on data/prompts_oq15_verdict.jsonl; k3_verdict_arm1 meta git `e0ae94f-dirty`, run_id 20260902T203132Z. Runs [0] and [2] are voided attempts' vanilla arms (disclosed in F-22).
- Size: 170M / 171M / 171M / 171M (du); ~0.33 MB gen + ~0.16 MB stats per run.

### (b) Adaptive-arm, val and tapcal byproducts, 17 more dirs (GITIGNORED), same schema

- Location: `k3_verdict_arm{2,3,4,5}`, `k3_verdict_s1_arm{2..5}`, `oq15c_verdict_arm{2,6,7}`, `oq15c_verdict_s3_arm{2,6,7}` (210 npz each), `k3_val_arm1`, `k3_tapcal_arm1`, `oq15c_val_arm1` (30 each); all 21 byproduct dirs 3.1G (du).
- Differences from (a): gamma_used 1..6, stop_pos and extend vary, q_sig NaN where the policy did not consult. From the summaries: k3_verdict_arm3 ((a)-probe policy, seed 0) 4 stop / 1 extend blocks of 17,583 and k3_verdict_s1_arm3 0 / 1 of 17,673, drafted 70,322 vs vanilla's 70,324 - effectively two more vanilla trajectories; k3_verdict_arm5 (fixed gamma 6) 15,567 blocks, 93,402 drafted, t/c 3.4438877111839146, dpe 1.7422170823151966; k3_val_arm1 2,450 blocks, dpe 1.2770393536617148 (= K-3 `b_ref`); oq15c_val_arm1 2,508 blocks, dpe 1.3255813953488371 (= OQ-15C `B_ref`); k3_tapcal_arm1 2,410 blocks.
- Provenance: same tool and pair; thresholds bound by sha in each meta.

### (c1) S1 shadow-slot harvest (GITIGNORED npz, committed metas/summaries)

- Location: `results/real/harvest_shadow/shadow_s{0..7}.npz` (+ `.meta.json`), `harvest_shadow_r/shadow_s{8..11}.npz`; `harvest_shadow_summary.json`, `harvest_shadow_r_summary.json`, `harvest_audit.json`, `harvest_fidelity_rider{,_r}.json`, `fidelity_calibration.json`.
- Contents (np.load shadow_s0.npz, 532,228,886 B): `tokens (210,256) int32`; `entropy (210,256) float32` [0..10.69]; `argmax (210,256) int32`; `top_ids (210,256,32) int32`; `top_p (210,256,32) float16`; `slots (210,256,4,32) int16` in -1..511; `hidden (210,256,4096) float16`; `lengths (210,) int32` [30..256]; `prompt_idx (210,) int32`; `mass16/32/64/512 float16`.
- Counts (summaries): primary 425,779 anchors, 1,693,036 (anchor, offset) pairs (offsets 425,779 / 424,099 / 422,419 / 420,739), splits train/val/test 1,210,644 / 238,752 / 243,640 by `prompt_idx % 7`, eos_hit_fraction 0.04523809523809524, mean length 253.43988095238095, exit bar 1,000,000 met; replication 213,644 anchors, 849,536 pairs (607,452 / 121,024 / 121,060), `EXIT_BAR_NOT_MET` by registered design (F-15). harvest_audit.json: 1,680 rows, 425,779 tokens.
- Provenance (shadow_s0.meta.json): `src/sideband/real/shadow_telemetry.py`, target-only sampled generations, taps at `model.layers.{7,15,23,31}.mlp.down_proj`, n_slots 512, top_m 32, batch 16, data/prompts.jsonl (sha 0237fb62...), seed 0 with `SeedSequence(seed).spawn(n_prompts)[i]` row seeds, git e8669d2, runtime 263.0 s per seed; buckets_k{16,32,64,512} shas recorded.
- Size: 8 x 532,228,886 B = 4.0G primary, 4 x the same = 2.0G replication (du).

### (c2) S3 MoE-router harvest (GITIGNORED npz, committed metas/summaries)

- Location: `results/real/harvest_moe/moe_s{0..7}.npz`, `harvest_moe_r/moe_s{8..11}.npz` (+ metas); `harvest_moe{,_r}_summary.json`, `harvest_audit_olmoe{,_r}.json`, `harvest_fidelity_rider_olmoe{,_r}.json`, `fidelity_calibration_olmoe.json`.
- Contents (np.load moe_s0.npz, 312,027,926 B): as (c1) but `tokens` are OLMoE ids (vocab 50,304 per buckets_olmoe_k512.json), `entropy` [0..7.25], `slots (210,256,16,8) int16` in 0..63 (sorted expert ids, -1 pad), `hidden (210,256,2048) float16`, `lengths` [114..256].
- Counts: primary 414,336 anchors, 1,647,264 pairs (414,336 / 412,656 / 410,976 / 409,296), splits 1,174,184 / 235,460 / 237,620, bar met; replication 208,091 anchors, 827,324 pairs (591,904 / 115,880 / 119,540). harvest_audit_olmoe.json: 1,680 rows, 414,336 tokens.
- Provenance (moe_s0.meta.json): `src/sideband/real/moe_telemetry.py`, telemetry = router top-8 expert ids per MoE layer, no router weights stored, `n_experts 64`, `top_k 8`, git 892a40a-dirty, runtime 2,255.1 s per seed.
- Size: 8 x 312,027,926 B = 2.4G primary, 4 x the same = 1.2G replication.

### (d) Probe grids, post-hoc topic controls, error predictor (COMMITTED)

- Location: `results/real/probes_s1.json` (+ `.state.jsonl`, 162 rows, headerless), `probes_s1_replication`, `probes_s3` (state 163 lines = header + 162), `probes_s3_replication`, `posthoc_topic_s1{,_r}`, `posthoc_topic_s3{,_r}` (73 lines = header + 72), `error_predictor_s1` (37 lines = header + 36).
- State row (probes_s1): `{cell 'L1_concept_k16|off2|a|linear|s0[|SHUFFLED]', space, offset, features, capacity, seed, shuffled, test_acc, val_acc_best, best_epoch, n_train 303261, n_val 59808, n_test 61030, majority_rate_test 0.5888907094871375, runtime_s, _clusters {test prompt: [n_correct, n]} over 30 prompts}`. The `_clusters` counts are what reproduce every CI (docs/REPRODUCE.md section 2).
- Payload: probes_s1 162 cells, runtime 17,621.1 s, `decision.best_offset_ge2_ci_upper` 0.050850775137805074, R2 shuffle pass (shuffled_a 0.5888907094871375 at off2), provenance git fba1fb3-dirty, CUDA. posthoc_topic_s1: 72 cells, `P1-SURVIVES`, primary margin 0.017701676770986947 [0.011888581009705891, 0.023187151127181303]. error_predictor_s1: 36 cells, runtime 8,250.7 s; selected L1_concept_k16 off2 with test precision at coverage 0.20 of 0.7918783112130646 (a) / 0.8356272871265498 (c) over base rates 0.605915123709651 / 0.6222513517941995.
- Provenance: `tools/run_probes.py`, `run_posthoc_topic.py`, `run_error_predictor.py` (torch, CUDA) over (c1)/(c2); estimator `sideband.stats.paired_cluster_delta_ci`, n_boot 2000, seed 0.
- Size: probes_s1.json 92,125 B; error_predictor_s1.json 123,113 B.

### (e) Phase-0 rejection records and analyses (COMMITTED)

- Location: `results/real/audit_k{256,512,1024}.jsonl` (+ `.stats.jsonl`, `.summary.json`, `.meta.json`), `sanity_k512{,_bf16,_nokv}.*`, `phase0b_*.jsonl`, `phase0c_*.jsonl`, `phase0b_vanilla_k512.gen.jsonl`, analyses `phase0a_verification.json`, `phase0b_analysis.json`, `phase0c_analysis.json`, `phase0c_oracle_analysis.json`, `glue_phase0a_analysis.json`, `oq12_diagnostics.json`.
- Contents: one record per rejection `{prompt_idx, position, offset 1..4, proposed, emitted, proposed_bucket, emitted_bucket, cross_bucket_residual_mass, run_id}`; audit_k512.jsonl 11,287 records (2,386,854 B), phase0b_vanilla_k512.jsonl 11,287, phase0b_sharp_b3.jsonl 11,830. audit_k512.summary.json: cross_bucket_fraction 0.8134136617347391 (by offset 0.8150890997454293 / 0.817910447761194 / 0.8086580086580086 / 0.8074344911639244, n 4321 / 3015 / 2310 / 1641), cross_bucket_residual_mass 0.8120061747513188, mean_acceptance_rate 0.7631885975075244, 210 prompts.
- Provenance: `src/sideband/real/hf_specdec.py`, same Llama pair, data/prompts.jsonl seed 0.

### (f) Label spaces: buckets, glue, concept groups, frequencies, persistence (COMMITTED)

- Location: `buckets_k{16,32,64,256,512,1024}.json`, `buckets_olmoe_k{16,32,64,512}.json`, `glue_k*.json`, `glue_olmoe_k{16,512}.json`, `concept_groups_v1.json`, `concept_groups_olmoe_v1.json`, `gen_freq{,_olmoe}.json`, `bucket_persistence_k{16,32,64,512}.json`.
- Contents: buckets_k512 = k-means over `lm_head.weight` (bf16, shape [128256, 4096]) after PCA to 128 dims, seed 0, 124 iterations, largest bucket 1,184, median 226.5, no empty bucket, `bucket_of_token` 128,256 entries (1,785,596 B); buckets_k16: 97 iterations, largest 24,585; buckets_olmoe_k512: 50,304 tokens, 57 iterations, largest 490. glue_k512: rule `top_n-frequency-mass-cover` (top_n 100, mass_cover 0.8), glue buckets [59, 403], covered_mass_share 0.8007060603513491, sensitivity at 0.90 -> [59, 196, 214, 269, 380, 403], top glue tokens ',' 2685, ' the' 2533, '.' 1445, ' a' 1229; glue_k16 -> [3]. concept_groups_v1: 510 concepts into 16 groups by spectral clustering of the concept-bigram adjacency graph (`construction.algorithm: spectral`, glue skipped and joined), sizes [8, 2, 2, 2, 2, 8, 2, 5, 2, 2, 2, 3, 3, 455, 10, 2], glue_class_id 16. gen_freq: 53,441 generated tokens, 9,922 distinct. bucket_persistence_k512: concept-concept p_same_bucket 0.02706469973283773 over 17,218 pairs, mean run length 1.0149421233206144 (max 8), glue_token_share 0.4084657073444216.
- Provenance: `src/sideband/real/bucketize_vocab.py`, `sideband.glue` + `tools/analyze_glue.py`, `tools/build_concept_groups.py`, `src/sideband/real/harvest_freq.py`, `tools/bucket_persistence.py`. These are the sha anchors every harvest meta and probe payload binds to.

### (g) OQ-16 reconstruction: summaries, metas, per-cluster SSE state (COMMITTED)

- Location: `results/real/oq16_stage_r{,_inv,_dr,_dr3,_dr4}.json` + `.meta.json` + `.state.jsonl`; the 15 files sum to 1,517,492 B (state files 178,069 / 188,303 / 248,286 / 368,676 / 429,135 B; summaries 10,356 to 32,935 B).
- Contents: state row `{arm, variant ('live' or stale seed '0'..'4'), pop, orig_prompt_idx, sse, count}` with count 720,896 = 176 blocks x 4096 per row; 1,512 rows registered (+ header), 3,612 in DR-4. Summary: `n_test_positions` 59,183,104, `n_test_clusters` 84, `n_train_rows` 42,160, `feature_dims` free 657 / tel 2705 / noise 2705 (UNION and FREETOK2 4753, F-22), deltas by `stats.paired_ratio_delta_ci`, gate, per_population, val_mse tables, R2, diagnostic_labels.
- Provenance: `tools/train_recon.py` / `src/sideband/recon.py` (CPU ridge) over the four (a) runs; header git bd71358-dirty; summary shas of the four runs bound in the header (verified).
- F-23 identity check: `results/real/oq16_ha_identity.json` (4,311 B): lm_head provenance (snapshot, shard, shard sha256, `tie_word_embeddings` false, 128256 x 4096), twelve pinned npz provenance rows with sha256 (first 4 blocks of the first 3 prompts of each (a) run), forward / inverse / top-k tables; producer `tools/ha_identity_check.py`; git 8542ef5-dirty.
- Absent at HEAD: `oq16_recon_weights.npz`, `oq16_recon_hhat/`, `oq16_inject_*.pt`, `oq16_stage_a_export.json` (named in .gitignore; Stage A never ran, and F-23 struck its telemetry arms).

### (h) Threshold searches and frozen thresholds (COMMITTED)

- Location: `k3_threshold_search_arm{2,3,4}.json` (+ state), `oq15c_search_arm{2,6,7}.json` (+ state), `k3_thresholds_arm{2,3,4,4_v2}.json`, `oq15c_thresholds_arm{2,6,7,7_v2}.json`.
- Contents: k3 arm 2: `b_ref` 1.2770393536617148, 42 evals, runtime 13,743.5 s, selection stop q0.25 / extend q0.5 at t/c 3.0968914008881714, budget 1.2746708382218745; thresholds stop [0.16655869036912918, 0.16311196982860565], extend 0.30184970796108246. oq15c arm 2: `b_ref` 1.3255813953488371, 41 evals, stop q0.1 / extend q0.75, t/c 3.1036761668731927. State row: `{stop_idx, extend_idx, stop_level, extend_level, stop_values, extend_value, tokens_per_call, budget, per_prompt (30 x [n_emitted, n_blocks, n_drafted, n_stop_blocks, n_extend_blocks]), runtime_s}`; 43 lines = header + 42.
- Provenance: `tools/k3_threshold_search.py` (GPU evals over the val byproducts).

### (i) Prompt sets (COMMITTED)

`data/prompts.jsonl`, `prompts_k3_verdict.jsonl`, `prompts_oq15_verdict.jsonl`, `prompts_oq16_verdict.jsonl` (210 rows each, 70 instruct / 70 story / 70 summarize, 210 unique topics) and `prompts_oq15_val.jsonl` (30 = 10/10/10); rows `{prompt, family, topic}`; 870 lines total; generators `data/make_prompts*.py` (data/README.md maps each set to its generator; `prompts_k3_verdict.jsonl` has none, commit 2db51aa). The OQ-16 set has no run at HEAD.

### (j) Exported frozen weights and riders (COMMITTED)

- `k3_probe_weights.npz` (432,598 B): `W_a_off{2,3} (16,657) float32`, `W_c_off{2,3} (16,2705) float32`, biases `(16,)`; meta: harvest test_acc 0.6056 (a off2) / 0.5915 (a off3) / 0.6224 (c off2) / 0.6005 (c off3), binding_gate PASS, worst self-check prob deviation 1.3487e-06, glue_class 15, git 69cb8f2-dirty, sha bound to probes_s1.json and its state.
- `oq15_head_weights.npz` (411,604 B): 30 float64 arrays `{free,tel}_off{1..5}_{mu,sd,w}` (free mu/sd 658 or 659 dims, w 659 or 660 incl. bias); meta: every chosen lambda 10.0 (grid edge), self-check 1,050 blocks max deviation 6.772360450213455e-15, bound to oq15_stage1.json and oq15_offset5.json.
- Riders: k3_tap_rider.json PASS (12 rejection-terminated triples, 2 anchors shared with the calibration sample), k3_containment_rider.json PASS on the bit-identity branch (10 prompts, 340.9 s), harvest_fidelity_rider.json PASS (7 long triples, teacher-forced full forward, no KV reuse).

## Unregistered exploratory observations

Everything in this section was recomputed in this session from the files
named, on the GPU box, by an unregistered script. These are NOT findings: no
regime tag, no pre-registered readout, no CI unless stated. Do not cite them
as results; they are leads for a registration.

| Observation | Numbers (file) |
|---|---|
| Story prompts are the hard family in every vanilla run | pooled n_accepted/n_proposed by family: story 0.7155 / 0.7217 / 0.7239 / 0.7162 vs instruct 0.7671 / 0.7633 / 0.7625 / 0.7528 and summarize 0.7671 / 0.7574 / 0.7593 / 0.7676 for the four (a) runs; t/c story 2.8517-2.8994 vs 3.0537-3.1380 (`<run>.stats.jsonl` + `data/prompts_*.jsonl`); audit_k512.stats.jsonl story 0.7261 vs 0.7764 / 0.7865. Summarize rows hit EOS most often (0.114 / 0.143 / 0.114 / 0.157 vs story 0.029 / 0.014 / 0.057 / 0.014, gen.jsonl). |
| Accepted-count histogram differs from the F-19 quoted distribution | k3_verdict_arm1 P(k=0..4) 0.2603 / 0.1872 / 0.1333 / 0.0985 / 0.3207 (n 17,581); the other three runs 0.2658 / 0.1819 / 0.1351 / 0.1006 / 0.3166, 0.2631 / 0.1873 / 0.1295 / 0.1008 / 0.3192, 0.2621 / 0.1919 / 0.1339 / 0.0997 / 0.3124 (byproduct `accepted`). F-19 quotes 0.2509 / 0.1751 / 0.1341 / 0.0953 / 0.3445 as "the committed gamma-4 accepted-length distribution"; docs/BLUEPRINT.md (K-3 arc registration, MEASURED BASIS) says it was computed 2026-09-01 from the committed phase0b vanilla records over 17,220 blocks, i.e. results/real/phase0b_vanilla_k512 (data/prompts.jsonl, seed 0, an earlier code state), so the histograms differ by population and run, not by an error. |
| Early-generation easy region | k3_verdict_arm1, generated position = anchor_pos - prompt_len + 1: mean accepted per block 2.324 in [0,32) (P(4) 0.396, P(0) 0.203) vs 1.938-2.038 in every later 32-token bin (P(4) 0.301-0.319); the first block after prefill accepts 2.51 (n 210). |
| D-9 survival conditioning, quantified | k3_verdict_arm1 empirical acceptance among survivors by drafted slot 0.7397 / 0.7469 / 0.7587 / 0.7651 (n 17,581 / 13,005 / 9,713 / 7,369) vs analytic 1-TV over all drafted slots 0.7375 / 0.7362 / 0.7344 / 0.7335; survivors' own analytic 0.7375 / 0.7510 / 0.7587 / 0.7640. oq15c_verdict_s3_arm1: 0.7379 / 0.7400 / 0.7547 / 0.7580 vs 0.7362 / 0.7323 / 0.7346 / 0.7304. |
| The draft's q(x) is a monotone acceptance predictor (unregistered) | k3_verdict_arm1 P(accept at slot 1) by q_sig decile 0.479, 0.499, 0.578, 0.628, 0.676, 0.776, 0.852, 0.928, 0.982, 0.998 (decile edges 0.016 / 0.105 / 0.265 / 0.451 / 0.645 / 0.813 / 0.927 / 0.985 / 0.999); corr(q_sig, accept1) 0.418, corr(analytic1, accept1) 0.529; oq15c_verdict_s3_arm1 0.453 ... 0.999, corr 0.416 / 0.524. (The exploratory pass also reported a scratch ridge for the block's accepted count; not re-run here, no number cited.) |
| Anchor confidence is a weak predictor of the draft's fate | k3_verdict_arm1 corr(top-1 p_a, accepted) 0.096, corr(entropy, accepted) -0.074; P(accept1) 0.688 for top-1 < 0.3 (n 3,000) vs 0.812 for top-1 >= 0.99 (n 1,684); median top-1 0.583, 0.096 of anchors >= 0.99; entropy terciles accept 2.24 / 2.03 / 1.82 per block. |
| h_a is tightly normed, no massive-activation coordinate | k3_verdict_arm1 (float16 -> float64) norm p1 / median / p99 125.5 / 146.9 / 150.3, max abs 51.75, median per-coordinate sd 2.09, largest-mean coordinate 1917 at 8.76, consecutive-anchor cosine p10 / median / p90 0.149 / 0.356 / 0.657, corr(norm, accepted) -0.005. |
| Rejection residual mass is bimodal; the commonest rejections are function-word swaps | audit_k512.jsonl (11,287): median cross_bucket_residual_mass 0.996, 0.555 above 0.99, 0.173 below 0.5; top (proposed -> emitted) pairs ' the'->' a' 51, ' a'->' the' 47, ' and'->',' 46, ','->' and' 44, ','->'.' 33, '.'->',' 32 (decoded via glue_k512.json); EOT 128009 emitted in 1 rejection, newline 198 in 3; rejections per prompt 11 / 53.5 / 84 (min / median / max). |
| Outputs overshoot max_new; no loops | generated_ids length min / p25 / median / p75 / max 96 / 256 / 257 / 258 / 260 (k3_verdict_arm1) and 93 / 256 / 257 / 258 / 260 (oq15c_verdict_s3_arm1); 0 rows with an 8-gram repeated 4+ times in either. |
| Telemetry churns almost completely token to token | shadow_s0.npz: consecutive-position Jaccard of the 32-slot sets 0.143 / 0.171 / 0.179 / 0.213 for layers 7 / 15 / 23 / 31, 1 identical consecutive set in 211,264; slot-usage entropy 8.79 / 8.91 / 8.61 / 7.73 bits of 9, layer-31 top-10 slots carry 0.152. moe_s0.npz: consecutive top-8 expert overlap 2.01-3.67 of 8, peaking at gates 4-6 (3.48 / 3.67 / 3.61); identical consecutive sets at most 0.0098 per gate; expert-usage entropy 5.71-5.89 of 6 bits. |
| The K-3 (a)-probe policy was almost inert | k3_verdict_arm3 4 stop / 1 extend of 17,583 blocks; k3_verdict_s1_arm3 0 / 1 of 17,673 (summary.json), so their byproducts are near-vanilla trajectories. |
| Frozen S1 probe margin shrinks on fresh prompts under live decoding - ALIGNMENT-SENSITIVE | Label = k16 class (`sideband.probes.load_label_space` on buckets_k16 + glue_k16) of generated_ids[anchor_pos - prompt_len + j] for offset j, the one convention consistent with block 0 (anchor = last prompt token, prompt_len 44, anchor_pos 43, offset 1 = generated_ids[0]) and with later blocks (anchor = producer of the already-emitted bonus token). Offset 2: (a) 0.5949 / (c) 0.6020 / floor 0.5805, c-a +0.0071 (k3_verdict_arm1, n 17,581); +0.0064 / +0.0067 / +0.0039 on the other three runs; offset 3 c-a +0.0071 / +0.0056 / +0.0066 / +0.0042. Harvest test_acc of the same cells 0.6056 / 0.6224 (k3_probe_weights.meta.json). By family at offset 2 (k3_verdict_arm1): summarize +0.0218 (floor 0.5096), instruct +0.0012 (0.6280), story -0.0006 (0.5996). Caveat: under the other reading (offset 1 = the block's first drafted slot for every block) both probes fall below the floor (c-a -0.0217); no finding fixes the byproduct's anchor convention in writing, so this row needs a registered alignment before any use. |

## Questions this data could answer (ideas, unregistered)

- Per-prompt heterogeneity of the F-15/F-17 margins from the `_clusters` counts in (d): is the margin carried by a few prompts or families (test prompts are `prompt_idx % 7 == 6`), and by the summarize family's lower floor?
- The beyond-gamma acceptance decay from the fixed gamma-6 arm (b): 15,567 blocks x 6 slots per seed, which no finding tabulates.
- Where adaptive stops fire (position, family, glue vs content) and whether the head arms' stops hit blocks that would have been accepted anyway (acc_flags are logged up to the stop).
- Paired-seed divergence: the block at which each policy first leaves the vanilla trajectory (D-6 shared streams) and how much of the t/c delta is post-divergence drift.
- Scalar targets for the slot stream from (c1)/(c2): entropy or top-1 mass at offsets 2-3, clause boundaries, glue-vs-content status; per-layer / per-gate ablation of the margin (OQ-14(i), unrun); slot- or expert-to-concept dictionaries.
- A finer rejection taxonomy from (e): reversible function-word swaps vs content divergences, near-1 vs near-0 residual mass by offset and family, and per-prompt difficulty stability across the 22 phase-0 arms.
- What the k-means concepts in (f) are linguistically; whether the 455-of-510 spectral mega-group means k512 concept space is one connected blob under bigram adjacency.
- Per-prompt reconstruction gain from the (g) state rows: is telemetry's advantage concentrated in low-entropy or story prompts, and do the five stale variants agree per prompt?
- Frontier shape from (h): about 250 (policy, threshold) points with 30 per-prompt tuples; how many val prompts drive each selected cell (the F-19 winner's-curse sizing: the val-tuned advantage shrinking on fresh prompts, docs/GLOSSARY.md).
- Cross-model paired comparison on the shared 210 prompts (eos_hit 0.04523809523809524 for Llama vs the OLMoE summaries' values; entropy; persistence) between a dense and a MoE instruct model.
- Dataset reuse: 70k (anchor state, telemetry, p summaries, proposals, per-slot accept flags) tuples from (a), and 425k anchors with full 4096-dim final-norm states from (c1), on open models.

## Zenodo deposit of the gitignored raws (2026-10-19)

Dated addition, 2026-10-19 (plan 15.10 of the public cut): every gitignored file
under results/real on this box on 2026-10-19 is the deposit of the Zenodo record
DOI 10.5281/zenodo.23462826 (https://doi.org/10.5281/zenodo.23462826; the
operator's upload was in progress when this was written, and the record publishes
after the repository's release): 5,175 files,
14,456,199,684 bytes (`git ls-files --others --ignored --exclude-standard
results/real` and the size of each file), in 34 zip archives written by 7-Zip at
its fastest deflate level by a script outside the repository, one per
`*.jsonl.byproduct` folder (33), each carrying its folder as its one top-level
entry so that it extracts into place, and one, `_loose_files.zip`, holding the 24
harvest shards by bare file name without their folders (the packing script gave
7-Zip the file paths): moe_s0 to moe_s7 belong in `harvest_moe/`, moe_s8 to
moe_s11 in `harvest_moe_r/`, shadow_s0 to shadow_s7 in `harvest_shadow/` and
shadow_s8 to shadow_s11 in `harvest_shadow_r/` (the stems are unique, and each
shard's committed `.meta.json` has the same stem). The inventory at the top of this file
(2026-09-05) counted 3,894 files and 13,369,799,824 bytes; the twelve folders
written after it, the three `k3_seed6_*` and three `oq15c_seed6_*` arms and the
six `oq20_replay_*` runs (their files' times 2026-10-09 to 2026-10-10, the OQ-20
seed-replay lane), hold the other 1,281. The table is read from the list the
packing script wrote beside the archives (deposit_list.json, with
sha256sums.txt; both are kept in the private record): the sha256 is the zip
file's, the member count is the number of files inside it, the bytes are the
zip's size. Every raw file keeps its own sha256 in its run's committed meta or
summary, so an extracted file is verified against those, not against this
table; this table verifies a downloaded archive before it is opened.

Dated note, 2026-10-26 (plan 16.40 of the public cut): the record was published.
Zenodo's API for record 23462826, read on 2026-10-26, gives status published, created
2026-10-25T08:52:17 UTC, 35 files (the 34 archives in the table below and
sha256sums.txt) totalling 10,050,223,667 bytes, publication date 2026-10-19 (the
version's date), version v1.0.0, and the repository's tree at v1.0.0 as its related
identifier (isSupplementTo). The words above that the upload "was in progress" and
that the record "publishes after the repository's release" were true when written
and stay as written.

| Archive | Source under results/real | Files inside | Bytes | sha256 |
|---|---|---|---|---|
| k3_seed6_arm1.jsonl.byproduct.zip | k3_seed6_arm1.jsonl.byproduct | 210 | 128,954,213 | 25a1f820ca6f64214f38916b3f52bae07351b6bb58967231bd26fe40d67cc40a |
| k3_seed6_arm3.jsonl.byproduct.zip | k3_seed6_arm3.jsonl.byproduct | 210 | 128,923,352 | 3ead007f8ee8b7381c846f4912a9ec2cd4bda6e82a1d7869422bfe2c0f84f11e |
| k3_seed6_arm4.jsonl.byproduct.zip | k3_seed6_arm4.jsonl.byproduct | 210 | 127,530,568 | d663e8fa331e6dc6d7468bc7770bcef976b382a49b6b2c17d6972d0b4294d52c |
| k3_tapcal_arm1.jsonl.byproduct.zip | k3_tapcal_arm1.jsonl.byproduct | 30 | 17,533,585 | 6c7a8f483fd2322de8ebef087a2a12395c214ae5f39ab4dc5811f25f60f96cc2 |
| k3_val_arm1.jsonl.byproduct.zip | k3_val_arm1.jsonl.byproduct | 30 | 17,809,581 | 2d4327a8c7a0053d970de67de928c8a311e3a91bd132103b708bda4accd6ba9f |
| k3_verdict_arm1.jsonl.byproduct.zip | k3_verdict_arm1.jsonl.byproduct | 210 | 127,992,345 | 00c31ab93b64d0c60469309aadba8cf85fe73d796beccc44c71a964b607017b2 |
| k3_verdict_arm2.jsonl.byproduct.zip | k3_verdict_arm2.jsonl.byproduct | 210 | 133,090,628 | b84b6cc062713cd60ad807abf6ad83d6b827337ec55bc5517004fcfd44080c6c |
| k3_verdict_arm3.jsonl.byproduct.zip | k3_verdict_arm3.jsonl.byproduct | 210 | 128,004,122 | 745c6379fd669dbed23d993ae0b440c821b4d4279c462acc27da23cf9e8ff991 |
| k3_verdict_arm4.jsonl.byproduct.zip | k3_verdict_arm4.jsonl.byproduct | 210 | 128,017,521 | 10cb3738d3e903d9ec08d0fc047d935e0ea9c8edba1893bfb3c9fbe4f67ea8a0 |
| k3_verdict_arm5.jsonl.byproduct.zip | k3_verdict_arm5.jsonl.byproduct | 210 | 114,041,502 | 46f31e271a3da211413d71629882472f31c871c534f754c8a33d6d406933580e |
| k3_verdict_s1_arm1.jsonl.byproduct.zip | k3_verdict_s1_arm1.jsonl.byproduct | 210 | 128,782,960 | f4fec0bded3a6ddaa9f75a0a4403e92c3a0de9b4155e00a05cd575a599b50d96 |
| k3_verdict_s1_arm2.jsonl.byproduct.zip | k3_verdict_s1_arm2.jsonl.byproduct | 210 | 130,974,885 | e6c491b4aa72e903d776d4ef2a2e1dd17d49f9f24187b33132fb6bd985cce6ac |
| k3_verdict_s1_arm3.jsonl.byproduct.zip | k3_verdict_s1_arm3.jsonl.byproduct | 210 | 128,784,040 | ad922f1a64f2fc12ca05e612150749f97a066cb389b4c067aca478647df274fb |
| k3_verdict_s1_arm4.jsonl.byproduct.zip | k3_verdict_s1_arm4.jsonl.byproduct | 210 | 128,702,541 | adec765f0dcc652045575b4981bc33f1fa9e5ffee858b9f9292a7a66572d7174 |
| k3_verdict_s1_arm5.jsonl.byproduct.zip | k3_verdict_s1_arm5.jsonl.byproduct | 210 | 114,592,871 | cb1e3928f1f0506853fe2f9664ec003e558bf53b6721738eaf3591b19e563ef7 |
| oq15c_seed6_arm1.jsonl.byproduct.zip | oq15c_seed6_arm1.jsonl.byproduct | 210 | 128,549,655 | 725f4246a03b0ea0892588425668ab250a377562e9e403be9b5688d30aeebda8 |
| oq15c_seed6_arm6.jsonl.byproduct.zip | oq15c_seed6_arm6.jsonl.byproduct | 210 | 126,824,483 | ed4984ddd6fd8dfe0862f25a15850fdc2a9e107f0e590f9529b24b830cd723cf |
| oq15c_seed6_arm7.jsonl.byproduct.zip | oq15c_seed6_arm7.jsonl.byproduct | 210 | 130,072,704 | cb10c77d244a4bb9dd61a3f92c2ea00db87bb759112f3f6460a5b0cc88cfe545 |
| oq15c_val_arm1.jsonl.byproduct.zip | oq15c_val_arm1.jsonl.byproduct | 30 | 18,297,435 | 2a24c5327f686d7b32d3253be216005f5a8001cebffd7639d5a8b52bab15afc9 |
| oq15c_verdict_arm1.jsonl.byproduct.zip | oq15c_verdict_arm1.jsonl.byproduct | 210 | 128,426,501 | 75cbbe00841443c817df3c9dd78fa2d02d1323f850dc2c344bbaca0ec18fee32 |
| oq15c_verdict_arm2.jsonl.byproduct.zip | oq15c_verdict_arm2.jsonl.byproduct | 210 | 128,089,127 | d3e13410364221ad78d46156f3a0f568fcfa238736042939b9312ac723a4acf8 |
| oq15c_verdict_arm6.jsonl.byproduct.zip | oq15c_verdict_arm6.jsonl.byproduct | 210 | 125,340,016 | dd3e6dda403f5aec87a3979d40c3becbc59e401ee1f350f545842d6377fcb1e4 |
| oq15c_verdict_arm7.jsonl.byproduct.zip | oq15c_verdict_arm7.jsonl.byproduct | 210 | 127,405,711 | 267ff2a8f5b6318cc0656adce05f8c4ea5a8a81fcaaf2fc71e9a180105cf2972 |
| oq15c_verdict_s3_arm1.jsonl.byproduct.zip | oq15c_verdict_s3_arm1.jsonl.byproduct | 210 | 128,530,153 | 7aa8a3aa505d08ffa69c2547c751fae0b697fcc917942548c6c28527faf39316 |
| oq15c_verdict_s3_arm2.jsonl.byproduct.zip | oq15c_verdict_s3_arm2.jsonl.byproduct | 210 | 128,312,366 | b279a4e4508077414e8a1a87a19bd061d7984451b4c5c0c4383440644f017f8d |
| oq15c_verdict_s3_arm6.jsonl.byproduct.zip | oq15c_verdict_s3_arm6.jsonl.byproduct | 210 | 126,862,519 | 4be12c97bfd3f198c9be5cae433554c826881a9f3a897112401bc886dd7650c6 |
| oq15c_verdict_s3_arm7.jsonl.byproduct.zip | oq15c_verdict_s3_arm7.jsonl.byproduct | 210 | 130,013,001 | c9673f16d1fa27847d589172dcbd1aed418eb7cdfa731da74dcc7161a9c3aeb9 |
| oq20_replay_k3_s1_arm1.jsonl.byproduct.zip | oq20_replay_k3_s1_arm1.jsonl.byproduct | 6 | 3,925,326 | f69d28e13911110abb805937e13369f1c7ca474a2407ab2e0bb3cde179ccfbf2 |
| oq20_replay_k3_s1_arm3.jsonl.byproduct.zip | oq20_replay_k3_s1_arm3.jsonl.byproduct | 6 | 3,925,326 | 8330c931aeb126a87cf4af3fec48e28e36dd8ad143ab45538cb98cdf3959b287 |
| oq20_replay_k3_s1_arm4.jsonl.byproduct.zip | oq20_replay_k3_s1_arm4.jsonl.byproduct | 6 | 3,873,808 | 80fef9b9ba566275a2d8bf08cc98ccba9a5e803ec8a1b6c2ab0cdc6576575c33 |
| oq20_replay_oq15c_s3_arm1.jsonl.byproduct.zip | oq20_replay_oq15c_s3_arm1.jsonl.byproduct | 1 | 560,865 | 58fbe3aafe7e8f229013cb58730979ed0708fd29bf413a738a8aba89545b680d |
| oq20_replay_oq15c_s3_arm6.jsonl.byproduct.zip | oq20_replay_oq15c_s3_arm6.jsonl.byproduct | 1 | 570,812 | e1dee339c6782725dfb224649d60a7cad5570373fc61ea546f1f0a57833f4bde |
| oq20_replay_oq15c_s3_arm7.jsonl.byproduct.zip | oq20_replay_oq15c_s3_arm7.jsonl.byproduct | 1 | 676,905 | 265df9b1e56643b4dd9a2b0ce0c23ee2e7d3a20dbb3dc6c7d5d222e976762524 |
| _loose_files.zip | the 24 harvest shards, by bare name (their folders above) | 24 | 6,926,228,698 | 143c403f9c0acf14d447e2fe4238dc0a33135d155bed0e19a6367e109595ad77 |
| Total, 34 archives | 33 byproduct folders and the 24 shards | 5,175 | 10,050,220,125 | |

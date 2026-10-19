# ERRATA_PROTOCOL — pre-registration of the 2026-10 errata recompute

Frozen 2026-10-10, before `experiments/errata_recompute.py` existed or ran.
Parent: docs/ERRATA_PLAN.md (step 2). Pinned state: amber HEAD `6672db4`
(tree `44811bf`), clean tracked tree. Every source below is cited by its git
blob id at that commit (`git rev-parse 6672db4:<path>`); the recompute
payload records the same ids programmatically and refuses to run on a dirty
tracked tree.

Rules of this document:
- A row's quantity, its definition, its sources and its decision rule are
  fixed here. Where a definition needs a choice (the loop rule, the stall
  rule, the depth denominators) the choice is pinned and a sensitivity grid
  is pinned beside it; the status is decided at the pinned setting only.
- Status vocabulary: CONFIRMED (the recomputed value equals the printed
  claim at its printed precision), CORRECTED (it does not), UNRECOMPUTABLE
  (a named source is missing or an instrument check fails; the reason is
  recorded). E14 carries no quantity; see its row.
- The harvest's values (`sideband/harvest/amber-lockstep-review-2026-10-09`,
  agent output) are predictions, scored after the run and never cited.
- Amendments are dated entries in the log at the end, written before any
  result is read. After the first run of the recompute, this file changes
  only by appending to that log.
- The recompute is CPU-only. The script sets `sys.modules["torch"] = None`
  before any import, so a torch import anywhere in its path raises; the
  payload records that flag. The tokenizer is loaded for E7 only, offline
  (`HF_HUB_OFFLINE=1`), through amber's own loader, and its `tokenizer.json`
  sha256 is recorded. The payload is written with LF line endings (results/
  is `-text`).

## Sources at 6672db4

| path | blob / tree id | used by |
|---|---|---|
| results/p1_divergence.json | 90a49e37e97db9c66f5e7b89cc3af2b5b716c3f9 | E1, E4, E10 |
| results/p1/generate (tree; 25 shards + meta.json e66d597e) | 8ed5d8099f7c844af3d97f198c6378612c63b2e5 | E1, E2, E3, E4, E5, E7 |
| results/p1/draft (tree; 25 shards + meta.json a0cc6830) | 0fbf1b20f3e1880ae495f2f8f9ae77782a2461f6 | E4, E10 |
| results/p4/encode_meta.json | c78926527a64a0725e802396a857d2d66b7f771b | E1, E6, E7 |
| results/p4/decode_cuda_fp32 (tree) | 02b6b9a31bcb0fc31d634b110705a2d20a3e280d | E8b |
| results/p4/decode_cpu_fp32 (tree) | 000764556da8441ff292f98dd2700f60b691eaf2 | E8b |
| results/p2b_escape_robustness.json | 7a84b002376c64717fcf9283e7f23f922e30a228 | E8a, E9 |
| results/p2_dumps.sha256 (pins the local, untracked results/p2_llama32) | aad41c716bd031935da0f0bf8b88be1d5850e485 | E8c |
| src/amber/real/archive.py | d95c531bf097ca3be66d6effb63e5b3be79c4615 | E1, E11, E12 |
| src/amber/real/divergence.py | 090e42b7d5f88de859d0e08e91a646418893227a | E2, E3, E4, E7 |
| src/amber/real/longhorizon.py | 4d55729b8872970e18ae47be0ff4ffb656e4fe72 | E3 |
| src/amber/real/capture.py | d2428cd6fea99c9ff86685d2f9510cbd82612641 | E7, E8c |
| src/amber/codec.py | 8c85ebaef79e59eb19c0f2bb2dadd29ae9b3124e | E11, E12 |
| src/amber/binformat.py | d8b3050dfbb2725b2a0899182bba251621314bea | E11 |
| src/amber/rac_codec.py | a0e5a69d5abeb4862171faab12a205c2671752df | E8c, E11 |
| experiments/p1_divergence.py | 9a4a63c559735fc58e8ff095da62b740eee43f32 | E4 (`amber_bits`), E7 (`content_coders`) |
| experiments/p2b_escape_robustness.py | d3493119d90cc63d41714eee37e3912263003f50 | E8c (`simulate`) |
| experiments/p4_real_archive.py | 3884d53541dd25e9f7be9fa8f1eb8ea24dd72658 | E1, E6, E7 |
| FINDINGS.md | 30fd27da6c9b531fa8597fe164914ef47214f5b0 | claim texts |
| DECISIONS.md | 2ae5d840e5a7f0d3bf48e9c98dd93859188fdbda | E8b claim |
| OPEN_QUESTIONS.md | 6d220b298ec8c0d9406aa6756257a6a82f4f6d3b | E7, E8a claims |
| README.md | bd1dc7325b8490141b2eb2357ef0d6215c6dc1fc | E1, E8a, E12 claims |
| docs/BLUEPRINT.md | e19515fa3fd9bb7b2a77f006247d915ec3240c4a | E1, E12 claims |
| docs/PRIOR_ART.md | 1ffa04e778e246779abee26f9579767da1f57ccd | E13 claim |
| pyproject.toml | 1298d49e4ecc4400232cb1e2a8b715c846f774f2 | E1, E12 claims |
| experiments/P7_PROTOCOL.md | 80fde1ad1980c15e7e518e68e66b1fe0e27ca34f | E14 |

Line numbers below are at this commit (FINDINGS.md lines are unchanged from
8662535).

## Rows

### E1 — "compress with the target model, decode with the draft"

- Claim: README.md:3-4, docs/BLUEPRINT.md:3-4, pyproject.toml:8.
- Quantity: the model the real-archive encoder runs. Values recorded:
  `results/p4/encode_meta.json` keys `draft` and `model.id`;
  `results/p1/generate/meta.json` key `target`; `results/p1_divergence.json`
  keys `draft` and `target`; line 1 of `src/amber/real/archive.py` (the
  docstring) verbatim; the first argument of the `load_model(` call inside
  `encode_stage` in `experiments/p4_real_archive.py` verbatim.
- Rule: CORRECTED iff `encode_meta.model.id` equals the P1 draft id and
  differs from the P1 target id; CONFIRMED iff it equals the target id.
- Prediction: the draft codes both ends; the target only generates.

### E2 — "193/200 prompts hit the 256 cap"

- Claim: FINDINGS.md:57 ("193/200 prompts hit the 256 cap, min 21, 0 empty").
- Definition: rows from `amber.real.divergence.load_generated(results/p1)`;
  `gen_len_r = len(ids_r) - prompt_len_r`; `max_new` read from
  `results/p1/generate/meta.json` (expected 256; the row is UNRECOMPUTABLE if
  not). `n_cap = #{gen_len_r == max_new}`; `n_eos = #{last generated id ==
  128001}` (Llama-3 `<|end_of_text|>`, pinned here; `n_eot` for 128009 is
  reported beside it); `min_gen`, `n_empty = #{gen_len_r == 0}`, `n_rows`,
  `total_gen` (expected 48,958).
- Rule: CONFIRMED iff `n_cap == 193` and `min_gen == 21` and `n_empty == 0`;
  CORRECTED otherwise.
- Prediction: 186/200; 14 rows end at EOS 128001.

### E3 — continuations "are fluent"

- Claim: FINDINGS.md:60 (caveat line). Not a number; the erratum states the
  loop fraction under the pinned rule.
- Definition (amber's instrument, D-1): per row, `frac_r, period_r =
  amber.real.longhorizon.loop_fraction(gen_ids_r, window=W, max_period=P)`;
  the row is LOOPED iff `frac_r >= t`. Pinned setting: `W=128, P=64,
  t=0.5` (amber's defaults, 512/256, cannot fire on 256-token rows and are
  not used). `tokens_in_loop_r = round(frac_r * gen_len_r)`.
  Grid, reported beside the pinned count: `W in {64, 128, 192, 256}`,
  `P in {16, 32, 64, 128}` with `P < W`, `t in {0.25, 0.5, 0.75}`.
  Repetition, two definitions, both reported: (a) amber's
  `distinct_ngram_ratio(gen_ids_r, 4)`: unweighted mean over rows and the
  pooled ratio `sum(distinct) / sum(total)`; (b) the harvest's: the share
  of generated positions `i >= 3` whose 4-gram `g[i-3..i]` also ends at
  some `j < i` in the same row, denominator `sum_r max(gen_len_r - 3, 0)`.
- Rule: CORRECTED iff, at the pinned setting, `n_looped >= 20` (10% of
  rows) or `sum(tokens_in_loop) >= 0.10 * total_gen`; CONFIRMED otherwise.
- Prediction: 125/200 looped (106-138 across definitions); (b) = 70.8%.

### E4 — amber v0 0.4738 "ties" AC-under-draft 0.4723 bits/token

- Claim: FINDINGS.md:59 (and the F-8 headline "ties AC-under-draft exactly").
- Instrument check first: with ranks and log2q from
  `amber.real.divergence.load_rank(results/p1, "draft")` concatenated in
  row order, `amber_bits(ranks) / N` (`experiments/p1_divergence.amber_bits`)
  must equal `results/p1_divergence.json row.amber_v0_bits_per_token` and
  `-mean(log2q)` must equal `row.ac_under_draft_bits_per_token`, both within
  1e-9; otherwise the row is UNRECOMPUTABLE (instrument mismatch).
- Definition: strata `S in {looped, nonlooped}` under E3's pinned flag.
  Per stratum: `N_S`; `amber_concat_S = amber_bits(ranks of S rows
  concatenated in row order) / N_S`; `amber_perarchive_S = sum_r
  amber_bits(ranks_r) / N_S`; `ac_S = -mean(log2q over S)`;
  `delta_concat_S = amber_concat_S - ac_S`; `rel_perarchive_S =
  amber_perarchive_S / ac_S - 1`. Also `amber_perarchive_all`.
- Rule: CORRECTED iff `sign(delta_concat_looped) != sign(delta_concat_nonlooped)`
  or `|rel_perarchive_nonlooped| > 0.02`; CONFIRMED otherwise.
- Prediction: concatenated, nonlooped +0.0835 and looped -0.0422 bits/token;
  per archive, amber trails AC by 7-10% on nonlooped rows.

### E5 — "target generation 32.8 tok/s"

- Claim: FINDINGS.md:59.
- Source: `results/p1/generate/meta.json` `shards[s].{seconds, new_tokens,
  tok_per_s}` (25 shards expected).
- Definition: `weighted = sum(new_tokens) / sum(seconds)`; `unweighted =
  mean_s(tok_per_s)`; `median_s(tok_per_s)`; `min`, `max`; `n_shards`.
  No "steady" figure: no rule for one is pinned.
- Rule: CONFIRMED iff `weighted` rounds to 32.8 at one decimal; CORRECTED
  otherwise, naming which pinned definition (if any) rounds to 32.8.
- Prediction: unweighted 32.8; weighted 25.0.

### E6 — "991 pos/s" teacher-forced encode

- Claim: FINDINGS.md:78 (regime) and :80 ("38x slower than the 991 pos/s").
- Source: `results/p4/encode_meta.json` `encode_pos_per_s` and
  `per_row[r].{length, score_seconds}` (200 rows expected).
- Definition: `aggregate = sum(length) / sum(score_seconds)` (must equal
  `encode_pos_per_s` within 1e-9, else UNRECOMPUTABLE); per-row rate
  `v_r = length_r / score_seconds_r`; `median_v`; stall rule: row r is
  STALLED iff `v_r < f * median_v`, pinned `f = 0.25`, grid `f in {0.1,
  0.25, 0.5}`; `n_stalled`, `seconds_stalled`, `seconds_total`,
  `clean = sum(length over not stalled) / sum(seconds over not stalled)`.
- Rule: CONFIRMED iff `aggregate` rounds to 991 and `clean < 1.5 *
  aggregate`; CORRECTED iff `aggregate` does not round to 991 or `clean >=
  1.5 * aggregate` (the printed rate then describes the stalls, not the
  instrument).
- Prediction: 15 stalled rows holding 36.3 of 49.4 s; clean about 4.2k pos/s.

### E7 — zstd-19 per archive "7.28" bits per generated token

- Claim: FINDINGS.md:80; OPEN_QUESTIONS.md:31 carries "7.3".
- Source: the P4 texts are P1's sequences (`experiments/p4_real_archive.py`
  reports over `load_generated`); tokenizer =
  `amber.real.capture._load_tokenizer(encode_meta["draft"])` with
  `HF_HUB_OFFLINE=1`; the resolved `tokenizer.json` path and sha256 are
  recorded (expected prefix 79e3e522, snapshot 4e20de36). Compressor:
  `zstandard.ZstdCompressor(level=19)` as in `content_coders`; the
  `zstandard` version is recorded.
- Definition: `n_tok = sum(gen_len_r)`; (a) as printed:
  `8 * sum_r len(zstd19(tok.decode(ids_r.tolist()).encode("utf-8"))) / n_tok`;
  (b) the same with `skip_special_tokens=True`; (c) `n_rows_with_bot` whose
  text (a) contains the literal `<|begin_of_text|>`, `n_rows_with_eot` whose
  text (a) contains `<|end_of_text|>`; (d) `bytes_a`, `bytes_b` (compressed
  totals) and `literal_bytes = sum_r (len(text_a_r) - len(text_b_r))`.
- Rule: CONFIRMED iff (a) rounds to 7.28 at two decimals; CORRECTED
  otherwise. (b)-(d) are reported in the erratum line regardless.
- Prediction: (b) = 6.75; the begin literal is 17 B per archive; 14 end
  literals.

### E8 — "0 desyncs" (three claims, three sources)

E8a. Claim: FINDINGS.md:69 headline "(0 desyncs / 49k positions / all ranks
to 64)"; README.md:34; OPEN_QUESTIONS.md:14.
- Source: `results/p2b_escape_robustness.json`
  `report.cpu_fp32.decoders.cuda_fp32_b1`, the row with `theta == 0.0`
  (the shipped D-8 default, `tie_margin = 0`) and the rows with `theta in
  {0.142, 0.465, 0.93}` (m 2 and 4).
- Definition: at theta 0: `n`, `desync_total`, `desyncs.{A,C,T,X}`,
  `A_desync_gap.max`; at each other theta/m: `desync_total`.
- Rule: CONFIRMED iff `desync_total(theta=0) == 0` and `n == 49056`;
  CORRECTED otherwise (F-10's body item (2) already prints 1 at theta 0 and
  0 at theta >= 0.142; the erratum is the headline's scope).
- Prediction: 1 desync at theta 0, gap 1.3e-5.

E8b. Claim: DECISIONS.md:100 "0 desyncs / 55k positions" (D-8 verification
by F-11).
- Source: `results/p4/decode_cuda_fp32/shard_*.npz` and
  `results/p4/decode_cpu_fp32/shard_*.npz`, arrays `row, first, n_decoded`
  (`first == -1` means byte-exact; `n_decoded` = replayed positions).
- Definition: per arm `n_rows`, `n_fail = #{first >= 0}`, `positions =
  sum(n_decoded)`; totals over both arms.
- Rule: CONFIRMED iff `n_fail_total == 0` and `54500 <= positions_total <
  55500`; CORRECTED otherwise.
- Prediction (this protocol's, not the harvest's, which did not separate
  this claim): 0 / 54,858 (48,958 + 5,900), CONFIRMED.

E8c. Claim: F-10's "only an fp32-class decoder is clean" extended to the
batch-8 fp32 arm that P2b did not run (`decoders` in the JSON has no
`cuda_fp32_b8`).
- Source: the local dumps `results/p2_llama32/{corpus.json, corpus.npz,
  cpu_fp32/*, cuda_fp32_b8/*}`. Before the read, `tools/sha256_manifest.py
  check results/p2_dumps.sha256` must pass for every entry under those
  paths; otherwise UNRECOMPUTABLE.
- Function: `experiments/p2b_escape_robustness.simulate(enc_idx, enc_val,
  dec_idx, true, theta=0.0, m=2)` with the same `true`, `keep` and
  `canonical_topk` as that script's `main` (encoder `cpu_fp32`, decoder
  `cuda_fp32_b8`).
- Definition: `n` (expected 49,056), `desync_total`, `desyncs.{A,C,T,X}`,
  `C_desync_by_rank[r]` for r in 2..8, and for each desync position its
  encoder rank of the true token and the decoder's rank of the true token.
- Rule: CONFIRMED iff `desync_total == 0`; CORRECTED otherwise.
- Prediction: 1 desync, a rank-4/5 swap; 2 per 98,112 across the two fp32
  decoder arms.

### E9 — the depth table

- Claim: FINDINGS.md:69 headline "3% of rank-2 and 9-26% of rank-3..8" and
  body item (3): fp32->bf16 "rank 2 2.7%, 3 9.3%, 4 15.3%, 8 25.6%, 17-64
  60%"; fp32->fp16 "rank 2 0.4%, rank 3 1.5%, rank 8 3.7%, ranks 17-64 14%".
- Source: `results/p2b_escape_robustness.json`, encoder `cpu_fp32`, every
  decoder in `report.cpu_fp32.decoders`, the `theta == 0.0` row; the same
  table for encoder `cuda_bf16_b1`.
- Definition (primary): depth 1 = `desyncs.A / symbol_counts.A`; depth r in
  2..64 = `C_desync_by_rank[r].desync / C_desync_by_rank[r].n`; buckets
  `{2}, {3..8}, {9..16}, {17..64}` = `sum(desync) / sum(n)` over the bucket;
  overall = `desync_total / n`. Alternative denominator, reported beside it
  for matching printed figures only: `desync / n` (all positions).
- Rule: CONFIRMED iff every printed figure above equals the primary
  definition for its arm at the printed precision (the headline's "3%" is
  the rank-2 bf16 value rounded to a whole percent; "9-26%" is the
  min..max over ranks 3..8, each rounded); CORRECTED otherwise, naming
  each figure that differs.
- Prediction: bf16 0.63% top-1, 6.0% rank 2, 59.8% ranks 17-64 (the
  harvest's); the 6.0% is expected to match an alternative denominator,
  not the primary.

### E10 — lockstep's inputs: 9.2k positions/s and 4.73 bytes/token

- Claim: FINDINGS.md:57 ("draft rank scoring 9.2k positions/s") and :57/59
  ("4.73 bytes/token").
- Source: `results/p1/draft/meta.json` `shards[s].{positions, seconds}`;
  `results/p1_divergence.json row.{content_bytes_per_token,
  amber_v0_bits_per_token, ac_under_draft_bits_per_token,
  zstd19_bits_per_token, positions, divergence_rate}` verbatim at full
  precision.
- Definition: `weighted = sum(positions) / sum(seconds)`; `unweighted =
  mean_s(positions_s / seconds_s)`; the JSON values copied.
- Rule: CONFIRMED iff `weighted` is in [9150, 9250) and
  `content_bytes_per_token` rounds to 4.73; CORRECTED otherwise.
- Prediction: 9,233 and 4.7277.

### E11 — the declared-length ceiling "checked BEFORE any replay"

- Claim: FINDINGS.md:31 (F-4). The claim is read onto every decode path
  that exists at this commit: hf JSON (`decode_archive`), v3 binary
  (`decode_binary_archive`), v4 session (`decode_session_archive`).
- Procedure: craft, for each path, an archive that is valid except for its
  declared length `L = 2**24 + 1` (one past `codec.DEFAULT_MAX_LENGTH`),
  with 0 corrections and an empty gamma payload (`payload_bits 0`), vocab
  128256, model `{id "errata-test", snapshot None, dtype "fp32"}`, all
  digests computed by the format's own functions (`hf_fingerprint`,
  `payload_digest`, `header_digest`, `binformat._d8`); the hf JSON header
  is framed exactly as `build_archive` frames it. Then monkeypatch
  `amber.real.archive.payload_to_symbols` to raise a sentinel
  `WorkStarted`, give a stepper that also raises `WorkStarted`, and call
  the path's decoder. Outcome per path: `refused` (ValueError before the
  sentinel), `work_started` (the sentinel), or the exception's type.
  Control: the same crafting with `L = 3` must reach `work_started` on
  every path; if it does not, the crafting is wrong and the row is
  UNRECOMPUTABLE.
- Rule: CONFIRMED iff all three bomb paths are `refused`; CORRECTED iff any
  bomb path is `work_started`.
- Prediction: hf JSON refused (`validate_hf_header` has `max_length`);
  v3 and v4 work_started (`unpack`/`unpack_session` check `length >= 0`
  only).

### E12 — "attesting" read onto real archives

- Claim: README.md:3-4, docs/BLUEPRINT.md:3-4, pyproject.toml:8
  ("attesting"); F-2's L1 is synthetic (its regime line stands).
- Definition: (a) `set(["cfg", "path_seed", "draft_seed"]) &
  amber.real.archive.HF_REQUIRED` (the header keys `attest_with_target`
  reads, `src/amber/codec.py:370-386`, against the hf header's field set);
  (b) the number of lines containing `attest` in `src/amber/real/*.py`,
  `experiments/p4_real_archive.py`, `p5_binformat.py`, `p6_sessions.py`;
  (c) the number of lines containing `payload` in the source of
  `attest_with_target` (`inspect.getsource`).
- Rule: CORRECTED iff (a) is empty and (b) is 0 (no L1 path exists for
  real archives); CONFIRMED otherwise. (c) is reported.
- Prediction: (a) empty, (b) 0, (c) 0.

### E13 — PMATIC's arXiv id

- Claim: docs/PRIOR_ART.md:10 "PMATIC (arXiv 2601.17684)".
- Procedure: fetch `https://arxiv.org/abs/2601.17684` and
  `https://arxiv.org/abs/2601.10678` with `urllib` (timeout 30 s), save the
  bytes to `results/errata_web/arxiv_<id>.html`, record each file's sha256
  and the fetch time; parse `<meta name="citation_title">` and every
  `<meta name="citation_author">`.
- Rule: CONFIRMED iff 2601.17684's title contains "PMATIC"
  (case-insensitive); CORRECTED iff it does not and 2601.10678's does;
  UNRECOMPUTABLE if a fetch fails or neither title contains it.
- Prediction: 2601.10678, Adler and Tang; 2601.17684 is a different paper.

### E14 — the P7 pre-registration

- Claim: experiments/P7_PROTOCOL.md "Frozen 2026-08-30".
- Definition: `ran = results/p7 exists on disk or git ls-files results/p7
  is non-empty` (expected false). No other quantity.
- Rule: status is CONFIRMED when `ran` is false (nothing ran, the frozen
  text is accurate); the action is a dated withdrawal line in
  experiments/P7_PROTOCOL.md stating that no GPU stage ran and none will.

## Payload: results/errata_recompute.json

```
provenance: {head, tree, clean_tracked_tree, script_blob, script_sha256_lf,
             python, numpy, zstandard, transformers, torch_blocked,
             torch_in_sys_modules, written_unix, inputs: {path: blob_id}}
rows: {E1..E14 (E8 as E8a, E8b, E8c): {claim, where: [...], value: {...},
       status, prediction: {...}, note}}
```
One stable key per quantity named above (for example `rows.E2.value.n_cap`,
`rows.E5.value.weighted`, `rows.E8a.value.desync_total_theta0`), so the
write-up's claims manifest can address each by repo, commit, file and key.

## Amendment log

2026-10-10, after the first dry run of the recompute (values had been seen;
none of these change a decision that depends on a value):
- E4: the instrument check compares the AC term as `p1_divergence.py:119`
  computes it, `float(-log2q.mean())` on the float32 array; a float64 mean
  missed the 1e-9 tolerance by 1.2e-8. The strata report float64 means (the
  rule's quantities are of order 0.05-0.1; the dtype cannot move them).
- E7: transformers 4.57.3 calls `model_info()` over the network for a repo
  id even with `local_files_only=True` (`_patch_mistral_regex` ->
  `is_base_mistral`), which `HF_HUB_OFFLINE=1` blocks. The pinned loader
  (`amber.real.capture._load_tokenizer`) is pointed at the cached snapshot
  directory of the same repo instead (its path, snapshot name and
  `tokenizer.json` sha256 are recorded). Same files, same tokenizer.
- E13: the pinned rule keyed on `citation_title`; neither page's title
  contains "PMATIC" (the name is in an abstract). Rule as amended: CONFIRMED
  iff 2601.17684's `citation_abstract` contains "PMATIC" (case-insensitive);
  CORRECTED iff it does not and 2601.10678's does; UNRECOMPUTABLE if a fetch
  fails or neither abstract contains it. Title checks stay in the payload.
- E9: an informational `alt_c` column (`desync_r / all C symbols`) is added
  to the payload beside the pinned primary and alternative denominators, to
  identify which denominator F-10's printed rank-2 figures used. No rule
  change.
- E9 (second dry run): the payload also carries the primary rank-2 value
  under every (theta, m) row of the JSON, and the list of (theta, m) at which
  the bf16 and fp16 rank-2 values round to F-10's printed "2.7%" and "0.4%".
  Informational: the pinned rule still scores the theta = 0 table.
- E1: line 2 of the `archive.py` docstring is recorded beside line 1
  (informational; the sentence spans both lines).
- Dry runs save the E13 pages to a temporary directory, not results/.

2026-10-10, after the critic's recompute (an independent opus agent; its
report and scripts are under results/errata_critic/; RECOMPUTE DISCREPANCY 0,
BLOCKING 2). Values had been seen. These entries correct the log, add fields
and change wording; no pinned rule's verdict is changed:
- Correction to the entry above: its opening sentence was wrong. The E4, E7
  and E13 amendments each moved a row from UNRECOMPUTABLE (the pinned
  procedure could not execute or decide) to a decided status, and the E13
  change was motivated by what the fetched pages showed. None moved a row
  between CONFIRMED and CORRECTED. The two dry-run payloads that show the
  pre-amendment statuses are committed under results/errata_dryruns/. The
  payload carries `status_under_pinned_rule` beside `status` for those three
  rows, and the errata text states both.
- E9, a protocol defect (the critic's BLOCKING 1): the pinned rule checks
  F-10's figures at theta 0, but F-10's item (3) is the theta 0.465 / m 2 row
  of the JSON (its C-desync counts occur in no other row) and F-10 does not
  say so. The pinned verdict stands as the defect's record; the payload adds
  `status_in_claim_regime` (the printed figures checked at every theta/m row,
  CONFIRMED if some row matches all of them) and the erratum reads "regime
  unstated; at the shipped theta 0 the rank-2 figures are ...". E8a gets the
  same field: F-10's body states theta >= 0.142 for its zero.
- E13 (the critic's BLOCKING 2): see the correction above. The payload stores
  the full abstracts, not a prefix cut before the PMATIC mention.
- Informational fields, no rule change: E4 reports the strata at every
  loop-grid setting (the per-archive direction is not robust across the
  grid, so the erratum states none); E8b reads results/p4_real_archive.json
  (F-11's own source, missing from the source table) and quotes F-11:80's
  CPU count beside the recomputed one; E8c records the swapped pair's own gap
  (the recorded gap is top-1 to top-2), the desync's persistence under every
  theta/m, and the number of positions where each fp32 arm's top-64 ORDER
  differs from cpu_fp32 (order differences, not desyncs); E12 greps all of
  src/, experiments/, tools/ and tests/; E14 also checks
  results/p7_longhorizon.json.
- Wording: E11's erratum says the ceiling was not carried to v3/v4 (F-4 was
  accurate for the JSON format it described); E6's says "excluding" the
  stalled rows rather than attributing them.
- Not adopted: the critic's proposed E15 (F-10 item (4) and P4's predictions
  used theta 0.465 rates while F-11 decoded at theta 0; theta 0 rates predict
  the bf16 and fp16 archive failure rates differently). A new row written
  after its values were computed would be post hoc; it is left to the
  operator as a follow-up.

2026-10-10, after the critic's second pass (RECOMPUTE DISCREPANCY 0,
BLOCKING 1, on the generated E8a text):
- Correction to the entry above: "E8a gets the same field" took the regime
  from F-10's body, not from the claim sites. The field is now per claim
  site (`status_by_claim_site`): the F-10 headline, whose body states the
  escape-on regime, CONFIRMED; README.md:34, the shipped theta 0 contract,
  CORRECTED; OPEN_QUESTIONS.md:14, an order claim, CORRECTED at every theta
  (the top-64 order differs at the positions E8c counts). The generated
  sentence "'exactly order-stable' holds for the resolved token, not for the
  order" was false and is withdrawn: the resolved token is stable only at
  batch 1 with the escape on, and E8c's wording carries the same qualifier.
- Informational: E8c also records, over the order-differing positions, the
  largest encoder-value gap between the two tokens competing for the first
  differing slot (the near-tie measure; the adjacent-gap statistic stays,
  named for what it is); the depth table carries the A-desync count beside
  the top-1 rate; each amendment label says when it was written; the F-14
  title counts the rows decided only through amendments; E8b's note says the
  rule does not score F-11:80's rounded CPU count; the DECISIONS.md note is
  placed after the end of D-9's bullet, not inside its sentence.

2026-10-10, second batch (rows E15 and E16), written before any code for
them existed or ran. Pinned state: amber HEAD `509ad90` (tree
`ee34f6f`), clean tracked tree; the sources below are cited by blob id
at that commit, and claim line numbers are at that commit (FINDINGS.md and
OPEN_QUESTIONS.md have moved since 6672db4 by the F-14 insertions). Both
rows were proposed by the critic (results/errata_critic/REPORT.md: first
pass item 13; third pass item 2); the critic's values are this batch's
predictions, scored after the run and never cited. The owner chose this
batch on 2026-10-10 after the first batch had landed. The rules at the top
of this document apply unchanged; this entry may be corrected only by
appending below it.

Payload: results/errata_recompute_2.json, a second file rather than a
rewrite of results/errata_recompute.json (so that every numeral F-14 cites
keeps its source, and E13's saved pages are not refetched): `provenance` as
before plus `batch: 2`; `rows: {E15, E16}`; `summary`. Written by
`experiments/errata_recompute.py --rows E15,E16 --out
results/errata_recompute_2.json` on a clean tracked tree (a row subset may
be written only to a non-default `--out`). Text:
`experiments/errata_text.py --payload results/errata_recompute_2.json
--finding F-15` lands a NEW finding F-15 (F-14 is append-only), one dated
erratum line under each finding a row names, pointer notes where `where`
says, and one line under the README status header; the same append-only
and pinned-blob checks. Critic: an independent opus agent recomputes both
rows from the sources below; its verbatim report is appended to
results/errata_critic/REPORT.md.

Sources at 509ad90 (new or re-pinned for this batch):

| path | blob / tree id | used by |
|---|---|---|
| results/p1/draft | 0fbf1b20f3e1880ae495f2f8f9ae77782a2461f6 | E15 (h1; tree, as pinned for E4) |
| results/p1_divergence.json | 90a49e37e97db9c66f5e7b89cc3af2b5b716c3f9 | E15 instrument check (i) |
| results/p4/archives | c650a00e4c379ebce78eecdcf6020893f9a4335e | E15 (h4, regime check; tree: 200 archives + 200 symbol streams) |
| results/p4/decode_cuda_bf16 | 314faf06c347773699119b9252dae8ff927b4216 | E15 instrument check (ii) (tree) |
| results/p4/decode_cuda_fp16 | bba01814675f16c94b3cbc7b055dbf2e38854608 | E15 instrument check (ii) (tree) |
| results/p4_real_archive.json | 26ccf5cf55362d02a3c75ef16bd7eb5e6d63d548 | E15 measured values |
| results/p2b_escape_robustness.json | 7a84b002376c64717fcf9283e7f23f922e30a228 | E15 per-rank rates; E16 budgets (`xb3_wide_gap_check`) |
| results/p2_llama32_rank_census.json | d6bba4839e86aeeb4601625c6f786c2f3a09fe83 | E16 (`calibrated_tau_per_arm`) |
| results/p2_dumps.sha256 | aad41c716bd031935da0f0bf8b88be1d5850e485 | E16 (pins the local dumps) |
| experiments/p2b_escape_robustness.py | d3493119d90cc63d41714eee37e3912263003f50 | E15 class rules (`simulate`), E16 (`TAU`) |
| experiments/p4_real_archive.py | 3884d53541dd25e9f7be9fa8f1eb8ea24dd72658 | E15 (how `desyncs_per_token` and the class names are computed) |
| src/amber/rac_codec.py | a0e5a69d5abeb4862171faab12a205c2671752df | E15 (`FLAG_NAMES`) |
| src/amber/rankcensus.py | 4e01ccd4761965b719b42e5c8ae1e36b78dc38c3 | E16 (`calibrate_tau_topk`) |
| src/amber/real/capture.py | d2428cd6fea99c9ff86685d2f9510cbd82612641 | E16 (`load_corpus`, `load_arm`) |
| src/amber/real/divergence.py | 090e42b7d5f88de859d0e08e91a646418893227a | E15 (`load_rank`) |
| FINDINGS.md | e3ac4ebd2c2efa87cd5a89ce3a50104919312562 | claim texts (F-7:55, F-10:72/76, F-11:85) |
| OPEN_QUESTIONS.md | a8545f77b45d14b331663804bfdcf6ede722b7d6 | E16 claim (line 16) |
| docs/BLUEPRINT.md | 5abed3e0ba832f26f9499612522958736c892154 | E15 claim (line 57) |
| results/errata_critic/REPORT.md | 649e07df0615968d6f1a2145ace8bb54533e8c01 | the predictions (first pass item 13; third pass item 2) |
| results/errata_recompute.json | 551a1ccd868be0ed35080a8a0d606f61f55031da | E9's `claim_regime_rows`, E8c's order-difference definition |

### E15 — F-10's "one desync per ~170 target-generated tokens" and F-11's "slightly MORE fragile"

- Claim: FINDINGS.md:72 (F-10 headline, "one desync per ~170
  target-generated tokens"); FINDINGS.md:76 (item (4): "expected C-desyncs
  per target-generated token fp16 1/1070 (set-coded 1/2900), bf16 1/170
  (1/370)"); FINDINGS.md:85 (F-11 caveats: predictions "landed in band but
  not on the point (bf16 84% vs 76%, fp16 28.5% vs 20%): target-generated
  corrections are slightly MORE fragile than the dumps' mix");
  docs/BLUEPRINT.md:57 ("one desync per ~170 tokens on P1's mix"). The
  defect under test (the critic's): item (4) and F-11's point predictions
  weight P2b's per-rank rates at theta 0.465 / m 2 (E9's claim regime) and
  count C desyncs only, while F-11 decoded with the escape off (theta 0),
  where A desyncs count too.
- Regime check: `results/p4/archives/row_*_symbols.npz` (200 files; arrays
  `flag`, `rank`, `gap`; class names by `amber.rac_codec.FLAG_NAMES`, as
  `experiments/p4_real_archive.py` reads them): the T (escape) count must
  be 0 and the position total must equal `report.content_tokens` of
  results/p4_real_archive.json; otherwise UNRECOMPUTABLE (the archives were
  not coded at theta 0, or the streams are not the decoded ones).
- Instrument checks: (i) the concatenated P1 draft ranks
  (`amber.real.divergence.load_rank(results/p1, "draft")`, as E4) have
  `N1 == row.positions` and `mean(rank != 1)` within 1e-6 of
  `row.divergence_rate` in results/p1_divergence.json; (ii) per P4 arm,
  `fails / sum(n_decoded)` over `results/p4/decode_<arm>/shard_*.npz`
  (`fails = #{first >= 0}`) equals `report.arms.<arm>.desyncs_per_token`
  within 1e-12. Either failure: UNRECOMPUTABLE.
- Definition. Arms: P2b decoder `cuda_bf16_b1` is P4 arm `cuda_bf16`; P2b
  `cuda_fp16_b1` is P4 `cuda_fp16` (both batch 1); encoder `cpu_fp32` in
  P2b (P4's encoder is cuda fp32: the same dtype pair on a different
  device; recorded, not corrected for). Rank histograms: `h4(r)` = count of
  P4 symbol positions whose coded rank is r (A = 1; C = its `rank`; X =
  above 64; total `N4`), the primary weighting (the positions F-11
  decoded); `h1(r)` the same over the P1 draft ranks (F-10's own input;
  total `N1`). Per-rank rates from the P2b row (theta, m) of
  `report.cpu_fp32.decoders.<D>`: `p(1) = desyncs.A / symbol_counts.A`;
  `p(r) = C_desync_by_rank[r].desync / C_desync_by_rank[r].n` for r in
  2..64 (UNRECOMPUTABLE if `.n == 0` at an r with `h(r) > 0`); `p(X) =
  desyncs.X / symbol_counts.X` (0 by construction). Quantities, per arm:
  `c_only[theta/m] = sum_(r=2..64) h(r) p(r) / N` for every theta/m row and
  both weightings (F-10's item (4) is `c_only` at E9's `claim_regime_rows`
  under h1); `all_theta0 = (h(1) p(1) + sum_(r=2..64) h(r) p(r) + h(X)
  p(X)) / N` at theta 0 (the decode regime), both weightings;
  `setcoded_c_only` at E9's claim regime under h1 from
  `setcoded_C.by_bucket` (bucket b covers ranks 2^b + 1 .. 2^(b+1); F-10's
  "1/370" and "1/2900"); fail-rate predictions `fail_poisson = 1 -
  exp(-Lbar * rate)` with `Lbar = content_tokens / archives` from the P4
  report (how F-11's "76%" and "20%" are expected to arise from `c_only`
  in the claim regime under h1) and `fail_exact = 1 - mean_a prod_(t in a)
  (1 - p(r_t))` over the 200 P4 archives' own streams (no approximation),
  for `all_theta0` and for `c_only` in the claim regime. Measured, from
  results/p4_real_archive.json `report.arms.<arm>`: `desyncs_per_token`
  (first desyncs per decoded position: decode stops at the first desync and
  `n_decoded = first + 1` on a failing archive, so this is a hazard
  estimate over the decoded prefix, not a count over all positions; the
  erratum says so), `fail_rate`, `archives`, `content_tokens`,
  `first_desync_class_counts`. Informational: the predicted share of
  desyncs by class at theta 0 (A, C2, C3, C4, C5, C6-64, X; from `h4(r)
  p(r)`) beside the measured first-desync class counts.
- Rule: CONFIRMED iff, for both arms, `desyncs_per_token > all_theta0(h4)`
  and `fail_rate > fail_exact(all_theta0, h4)` (the archives are more
  fragile than the theta 0 prediction on both metrics); CORRECTED
  otherwise, naming each comparison that reverses. Also
  `status_in_claim_regime`: CONFIRMED iff `1 / c_only(h1)` in the claim
  regime rounds to 170 (bf16) and to 1070 (fp16) at the nearest ten
  (F-10's figures reproduce in their own regime); CORRECTED otherwise.
- Prediction (the critic's): theta 0 rates including A desyncs predict
  1/77 (bf16) and 1/502 (fp16) against measured 1/65 and 1/670, so fp16
  reverses: CORRECTED. This protocol's own: the 1/170 and 1/1070 reproduce
  under h1 in the claim regime (`status_in_claim_regime` CONFIRMED), and
  `fail_poisson` from them prints 76% and 20%.

### E16 — "every flip a near-tie" and XB-3's "no wide-gap flip", read at depth

- Claim: FINDINGS.md:76 (item (1): "every A-desync at theta=0 has encoder
  gap below the pair budget 2(tau_enc+tau_dec) (XB-3 check: no wide-gap
  flip, no pipeline bug)"); FINDINGS.md:55 (F-7 caveats: "every flip is a
  near-tie"); OPEN_QUESTIONS.md:16 ("with every flip a near-tie"). E8c
  counted the positions where an fp32 decoder's top-64 ORDER differs from
  cpu_fp32 and F-14 calls every one "a near-tie" without a threshold; this
  row supplies the threshold the record's own instrument uses and counts
  the positions above it.
- Source: the local dumps `results/p2_llama32/{corpus.json, corpus.npz,
  cpu_fp32/*, <D>/*}` for every decoder read, each entry checked against
  results/p2_dumps.sha256 first (UNRECOMPUTABLE otherwise); the same
  `load_corpus`, `load_arm`, `canonical_topk` and `keep` mask as E8c.
  Budgets: results/p2b_escape_robustness.json
  `xb3_wide_gap_check["cpu_fp32-><D>"].pair_budget_2tau` (the XB-3 check's
  own numbers, 2 (tau_enc + tau_dec) with tau_cpu = 0 and tau from that
  script's `TAU` dict), and results/p2_llama32_rank_census.json
  `calibrated_tau_per_arm` (tau as `amber.rankcensus.calibrate_tau_topk`
  returns it: the 0.999 quantile of the arm's aligned |delta logit| against
  cpu_fp32; the census's per-row `tau` field holds 2 tau, because
  `experiments/p2_rank_census.py` passes `2 * tau` to the census).
- Definition: for decoder D, encoder cpu_fp32, over the kept positions
  (expected 49,056): an order-differing position is one where
  `enc_idx[:, :64] != dec_idx[:, :64]` anywhere (E8c's definition); at
  each, `j` = the first differing slot (0-based), `tok` = the decoder's
  token at slot j, `k` = the encoder slot of `tok` over the full dump width
  (absent is counted and excluded from g), `g = |enc_val[j] - enc_val[k]|`
  (the encoder gap between the two tokens competing for slot j: E8c's
  near-tie measure). Report per D: `n_diff`; quantiles of g (min, p50, p90,
  p99, max); counts and max g by slot bucket j in {0, 1, 2-7, 8-15,
  16-63}; `n_nonadjacent` (k != j + 1); `n_absent`; `budget` with its
  source; `count_above_budget`; `two_tau_census = 2 *
  calibrated_tau_per_arm[D]` and `count_above_two_tau_census`. Budget:
  cuda_fp32_b1: the XB-3 check's `pair_budget_2tau` (expected 8.6e-05);
  cuda_fp32_b8: P2b's `TAU` has no entry, so `budget = two_tau_census` for
  that arm, labelled as the census-derived proxy; informational arms
  cuda_fp16_b1, cuda_bf16_b1, cuda_bf16_b8: their XB-3 `pair_budget_2tau`.
- Rule: scored on cuda_fp32_b1 (the arm the XB-3 check ran and the "every
  flip" claims measured): CONFIRMED iff `count_above_budget == 0`;
  CORRECTED otherwise. cuda_fp32_b8 carries `status_by_arm`, not scored
  (no printed claim names its budget). The informational arms carry no
  status.
- Prediction (the critic's): at 2 of the 379 b1 positions g exceeds
  8.6e-05 (max 1.478195e-04): CORRECTED; b8 max 5.722046e-05, so 0 above
  either b8 budget; the competing token is always the adjacent one.

Observed while pinning E16's budgets; recorded, NOT scored (the values were
seen before any rule could be written): FINDINGS.md:40 (F-5) prints "2tau"
thresholds of 0.142 (fp16), 0.93 (bf16), 5.0 (int8) and 12.3 (nf4) for
TinyLlama, and FINDINGS.md:54 (F-7) prints 0.93 (bf16) and 6.6 (int8) for
Llama-3.2-1B, while the two census JSONs' `calibrated_tau_per_arm` values
(results/p2_rank_census.json, results/p2_llama32_rank_census.json) are one
quarter of those labels: the labels are 4 tau, twice the census's own
per-row `tau` field (which holds 2 tau). F-7's fp16 "0.066" and every
P2b/F-10/F-11 budget are 2 tau. The thetas P2b tested (0.142, 0.465, 0.93)
were taken from F-5's labels. Whether the census's `flips_beyond_2tau`
counts compared gaps against 2 tau or 4 tau is not determined here. A
candidate row for a later batch under its own pre-registration; it does not
touch E15 or E16.

2026-10-10, after the dry run of the second batch (values had been seen; no
rule changed; the dry-run payload is committed as
results/errata_dryruns/dry_b2.json beside its stderr, line endings
normalised to LF):
- E16: the payload also carries the encoder's top-1/top-2 gap quantiles
  (p01, p50) over the kept positions, the scale against which the
  order-difference gaps are read. Informational.
- E15: nothing added. The dry run shows the two metrics disagreeing for
  bf16 (per-token hazard above the theta-0 prediction, whole-archive fail
  rate below it); the erratum states that the hazard is measured over the
  decoded prefix (mean prefix length = `n_decoded_total / archives` from
  the shards block) and the fail rate over whole archives, and prints the
  predicted and measured desync class shares. Wording only.

2026-10-11 UTC (the evening of 2026-10-10 on this box), after the critic's
recompute of the second batch (a new opus agent; its report and c2_*.py
scripts are under results/errata_critic/; RECOMPUTE DISCREPANCY 0,
BLOCKING 2). Values had been seen. No pinned rule's verdict changes; each
BLOCKING objection is recorded as a protocol defect in the E9 manner, with
a field beside the pinned status that scores the claim at its own scope:
- E15, a protocol defect (the critic's BLOCKING 1): the pinned rule scores
  FINDINGS.md:85, a claim about corrections (C symbols), on an all-class
  quantity, and the all-class reversal comes from the rank-1 (A) term
  alone. Added, no rule change: per class (A, C, X) and all-class, the
  observed first desyncs against the expected count summed over the
  positions each archive actually decoded (`sum over t < n_decoded of
  p(r_t)`, the compensator, unbiased under the hazard model), the ratio
  O/E, an approximate Poisson z = (O - E) / sqrt(E), and the like-for-like
  predicted first-desync shares E_c / E_total; `status_by_class` (per
  class, CONFIRMED iff O/E > 1 on both arms); `status_by_claim_site`
  (FINDINGS.md:72, FINDINGS.md:76 and docs/BLUEPRINT.md:57, figures in
  their own regime: the claim-regime status; FINDINGS.md:85, a corrections
  claim: the C-class status). The regime of the two sides is recorded from
  the JSONs (P2b: model id and snapshot, teacher-forced windows of the P2
  corpus; P4: draft id and snapshot, target-generated text, incremental
  KV). The mechanism the critic identified is measured without a model: the
  share of rank-1 positions whose top-2 gap lies below the bf16 and the
  fp16 pair budgets, in the P2 dumps (cpu_fp32, kept positions, rank 1 by
  `rank_of_true`) and in the P4 archives (A-flag positions, the symbol
  streams' `gap`). The critic's gap-conditioned A rate is a post-hoc model
  and stays in its report. Flat `*_all_theta0_one_in_h1` fields are added;
  the critic's 1/77 and 1/502 are scored against them (its computation
  weighted by the P1 ranks) and `prediction_sources` labels each prediction
  as the critic's or this protocol's. The erratum states the by-class result
  and does not say the direction reverses.
- E16, a protocol defect (the critic's BLOCKING 2): the three claim sites
  are top-1 statements and the rule counts order differences at every
  depth; the sentence the depth count contradicts is F-14's own E8a text
  ("every one a near-tie" over the order-differing positions:
  FINDINGS.md:114, OPEN_QUESTIONS.md:15, README.md:50 at 509ad90), which is
  added to `where`. Added, no rule change: `status_at_claim_scope` per
  scored arm (CONFIRMED iff the slot-0 count above budget is 0, from the
  slot bucket already in the payload) and `status_by_claim_site` (the
  top-1 sites take cuda_fp32_b1's slot-0 status; the F-14 sentence sites
  take the pinned status). Informational, after the critic's ADVISORY 3 and
  4: the number of distinct contexts (token prefixes up to the position)
  among the order-differing positions and among those above budget; for
  each event above budget, the decoder's value change on each of the two
  tokens and the pair drift (the change of their gap); tau as the census
  computed it (`amber.rankcensus.calibrate_tau_topk` over the dumps
  truncated to the census's `topk_used`, at its default quantile; the
  source line above omitted the top-64 truncation); for the scored arms,
  the aligned delta of every encoder top-64 token (decoder value minus
  encoder value, the token found over the full dump width), its 0.999
  quantile by slot bucket {0, 1-7, 8-15, 16-63}, and the count of adjacent
  top-64 pairs whose drift exceeds the budget against the number of pairs.
  The generated text says "tail drift", not "wide-gap flip", and does not
  say that tau was calibrated at top-1.
- Pointer notes: two locations in the same file whose line ranges touch
  take one note (OPEN_QUESTIONS.md:15 and :16).
- Audit trail (the critic's ADVISORY 8): results/errata_dryruns/dry_b2.json
  was re-run after the informational field was added. The run whose values
  were seen first, written at cfb9595 before any amendment, is now
  committed as results/errata_dryruns/dry_b2_pre.json with its stderr (LF);
  the "after the dry run" entry above refers to that run.
- Not adopted: a noise allowance in the binary rules (the z scores are
  reported; the rules stay as pinned); the critic's gap-conditioned
  prediction as a row quantity.

2026-10-11 UTC, after the critic's second pass (RECOMPUTE DISCREPANCY 0,
BLOCKING 1, on the generated F-15 caveats line). Values had been seen; no
pinned verdict changes:
- The generated sentence "F-5's and F-7's printed '2tau' thresholds are
  four times the census tau" dropped the exception the observation above
  states: F-7's fp16 label is 2 tau. The generator now says so. Verified on
  the critic's aside: `experiments/p2_rank_census.py` passes `2 * tau` to
  the census and `amber.rankcensus._census_core` counts `flip_gaps > tau`,
  so the census's beyond-2tau counts were taken at 2 tau; only F-5's four
  labels and F-7's bf16 and int8 labels are 4 tau. The candidate row is a
  label defect, not a count defect.
- E16: `status_at_claim_scope` is computed for every arm read (the three
  top-1 claim sites are claims about the fp16 and bf16 arms too), and the
  top-1 sites' `status_by_claim_site` is CONFIRMED iff the slot-0 count
  above budget is 0 on every arm; the text prints each arm's slot-0 count.
  The text no longer calls the exceedance "not a wide-gap flip" (under the
  depth reading it is one by the record's definition, FINDINGS.md:76); it
  says F-14's sentence holds at logit scale and names the one context above
  the budget as a tail drift, not evidence of a pipeline bug.
- E15: `fail_exact` adds the theta-0 whole-archive failure prediction under
  C hazards alone and under A hazards alone (h4 streams), so the by-class
  statement covers both metrics; the text says "the prediction counts C
  desyncs only" instead of "that regime is ... C desyncs only".
  `class_shares_theta0` (predicted shares of all desyncs against measured
  shares of first desyncs, not like-for-like) was dropped at the previous
  landing and is recorded here; the compensator's
  `predicted_first_desync_shares` replaces it. F-11's printed per-token
  figures leave the `prediction` dict (they are quotations, not
  predictions) and are kept as `value.f11_printed_one_in` with a rounding
  check. Both rows carry `pinned_rule_sites`, the claim sites the pinned
  rule scores (E15: FINDINGS.md:85; E16: F-14's sentence sites).
- Text: the F-15 title and the README note count rows corrected under their
  pinned rules and, beside that, claim sites standing at their own scope;
  the title attributes the cross-regime comparison to F-11; the regime line
  names the protocol entries behind the cited blob; the source line lists
  dry_b2_pre.json; the predictions line labels each prediction's source; a
  pointer line under a finding, or a note at another site, is labelled
  "erratum" only where a site it points for is CORRECTED or is a pinned
  rule's site, and "note" otherwise; the dry run prints insertions in write
  order.

2026-10-11 UTC, after the critic's third pass (RECOMPUTE DISCREPANCY 0,
BLOCKING 0; nothing false in the nine insertions). Values had been seen; no
pinned verdict changes; wording and labels only:
- E15 text: the sentence that set the C-hazards-only failure prediction
  beside the all-class measured failure rates overstated the excess on the
  failure metric. It now compares that prediction with the C-caused
  failures (the compensator's observed C first desyncs over the archives)
  and prints the excess in binomial standard deviations of the predicted
  rate, computed from payload values; the direction clause is generated
  from the comparison.
- E16: `prediction_sources` added (every E16 prediction is the critic's:
  REPORT.md first pass items 5 and 13, third pass item 2), a label, so the
  predictions line can label every prediction.
- Text: the caveats line states the label rule in full ("erratum" where a
  site is corrected or is the site a pinned rule scores); the title and the
  README note say "claim-site statuses" (E16's F-14 sentence is one status
  over three locations); the regime line says the pre-registration was
  committed before the first code for the rows and that the order of
  writing is self-reported.
- House rule: 05c3305 and 3cec4df were committed with two failing tests
  (both test expectations; the chain joined the test run with a semicolon
  instead of a gate); 8515734 corrected the tests and says so. Recorded
  here as the critic's ADVISORY 4.

2026-10-11 UTC, after the critic's fourth (narrow) pass (RECOMPUTE
DISCREPANCY 0, BLOCKING 0; nothing false in the nine insertions). One
label corrected, no value or status touched: the entry above credited
E16's predictions to "first pass items 5 and 13; third pass item 2", but
item 13 is the E15 proposal, and `b8_count_above_budget` = 0 was this
protocol's own inference from the critic's b8 maximum. `prediction_sources`
is now per key: the order-difference counts from the first pass (item 5)
and second pass (item 4), the maxima, the b1 count above budget and the
adjacent competitor from the third pass (item 2), and the b8 count above
budget from this protocol. The predictions line then labels that one
"(protocol)". The payload is regenerated for the label; F-15 lands from it.

2026-10-11 UTC, third batch (rows E17, E18 and E19), written before any code
for them existed or ran. Pinned state: amber HEAD `168efb0` (tree
`85c3582`, the F-15 landing, tag errata-batch-2-landed), clean tracked
tree; sources are cited by blob id at that commit and claim line numbers are
at that commit. Owner's decision of 2026-10-11: run this batch, then move
the record to sideband and archive this repository. The rules at the top of
this document apply; payload results/errata_recompute_3.json (`batch: 3`),
written by `experiments/errata_recompute.py --rows E17,E18,E19 --out
results/errata_recompute_3.json` on a clean tracked tree; text by
`experiments/errata_text.py --payload results/errata_recompute_3.json
--finding F-16`, landing a new finding F-16 with the same append-only and
pinned-blob checks and the label rule of the second batch; an independent
opus critic recomputes every value before the landing. Values seen before
this entry: E17's label ratios (recorded unscored in the second-batch
entry); E18's and E19's predictions below are agent output (the review
harvest and the second batch's critic), scored after the run, never cited.

Sources at 168efb0 (new or re-pinned for this batch):

| path | blob / tree id | used by |
|---|---|---|
| results/p2_rank_census.json | 98e1b588740211f6b0c7748aae2771f55d009207 | E17 (TinyLlama tau, per-row tau field, flips_beyond_tau, flip_gap_max) |
| results/p2_llama32_rank_census.json | d6bba4839e86aeeb4601625c6f786c2f3a09fe83 | E17 (Llama-3.2-1B-Instruct, the same) |
| experiments/p2_rank_census.py | 602f2562c059fb03380d33afd9de271d516e273d | E17 (`census_row` passes `2 * tau`) |
| src/amber/rankcensus.py | 4e01ccd4761965b719b42e5c8ae1e36b78dc38c3 | E17 (`_census_core` counts `flip_gaps > tau`) |
| results/p2b_escape_robustness.json | 7a84b002376c64717fcf9283e7f23f922e30a228 | E17 (thetas), E19 (theta-0 C rates) |
| results/p1/generate | 8ed5d8099f7c844af3d97f198c6378612c63b2e5 | E18 texts (tree) |
| results/p1/draft | 0fbf1b20f3e1880ae495f2f8f9ae77782a2461f6 | E18 content bits (tree) |
| results/p1_divergence.json | 90a49e37e97db9c66f5e7b89cc3af2b5b716c3f9 | E18 instrument check |
| results/p5_binformat.json | 552ed33fb779f0fa53ff2c0b6415c63ac65f489f | E18 (curve_model, fixed_header_bytes, printed comparators) |
| results/p5/encode_meta.json | 2fdfd1a1fc9391aac9a8f0130d75b14e05333b24 | E18 (per-row v3 bytes) |
| results/p6_sessions.json | 53c12e6a2297858d14d842421081e25964668bda | E18 (printed per-session comparators) |
| results/p6/k8_m0 | d1be47a4b439b397c7fb967b0ad06083dad3fb9f | E18 sessions k=8 (tree) |
| results/p6/k16_m0 | f6c6f208c4fe58a98d03d9f45c8f4f49cfb6cd3f | E18 sessions k=16 (tree) |
| experiments/p5_binformat.py | 818d781d8073ca316156975bef78dafbfe85f6d9 | E18 (how the full text was decoded for zstd) |
| experiments/p6_sessions.py | 31a6e7895730ebc2f50984aa4e2590b18b7fa6a6 | E18 (per-session zstd definition) |
| experiments/p1_divergence.py | 9a4a63c559735fc58e8ff095da62b740eee43f32 | E18 (`amber_bits`) |
| src/amber/real/capture.py | d2428cd6fea99c9ff86685d2f9510cbd82612641 | E18 (`_load_tokenizer`) |
| results/p4/archives | c650a00e4c379ebce78eecdcf6020893f9a4335e | E19 (rank-1 gaps and flags; tree) |
| results/p4/decode_cuda_bf16 | 314faf06c347773699119b9252dae8ff927b4216 | E19 exposure (tree) |
| results/p4/decode_cuda_fp16 | bba01814675f16c94b3cbc7b055dbf2e38854608 | E19 exposure (tree) |
| results/p4_real_archive.json | 26ccf5cf55362d02a3c75ef16bd7eb5e6d63d548 | E19 observed first desyncs |
| results/p2_dumps.sha256 | aad41c716bd031935da0f0bf8b88be1d5850e485 | E19 (pins the local dumps) |
| results/errata_recompute_2.json | 9be96ef5bfd08b5582025a154d490ec0d1456d95 | E19 (E15's compensator, the rank-only baseline) |
| results/errata_critic/c2_e15_gapsens.out.json | e863e8c8c8adcee411a3d359466bd82c2ad1d5bb | E19 predictions (the critic's post-hoc binnings) |
| FINDINGS.md | 1aef109e9411b54129e08ac35d1cedda51096067 | claim texts (lines 40, 54, 58, 62, 76, 91, 94, 101, 136) |
| DECISIONS.md | dfc9e0724ca4a9bd11cc090fcba3de7cf85a7ac7 | E18 claims (D-6 at 39-44; line 132) |
| README.md | b58a0b29daa7fcf7a8c4051f3259a2918357491d | E18 claims (31, 45-46) |
| docs/BLUEPRINT.md | 47f41ab80c47b84c98b50f73314b26564d4f9dbe | E18 claims (50, 81) |
| OPEN_QUESTIONS.md | 0192820aa501696b274d1658acd60f7d8de30b07 | E18 claims (31, 32) |
| sideband harvest `scratchpad/amber-audit/spot6.py` (untracked agent output) | sha256 16287b93720382ed | E18 predictions |
| sideband harvest `scratchpad/amber-audit/spot7.py` (untracked agent output) | sha256 7193399480e8650f | E18 predictions |
| sideband harvest `scratchpad/sb-late/zdict_sess.py` (untracked agent output) | sha256 9f6b55072b409215 | E18 predictions |

### E17 — F-5's and F-7's printed "2tau" thresholds

- Claim: FINDINGS.md:40 (F-5: "0 beyond 2tau=0.142" for fp16, "0 beyond
  2tau=0.93" for bf16, "0 beyond 2tau=5.0" for int8, "3 beyond 2tau=12.3,
  gap max 7.06" for nf4); FINDINGS.md:54 (F-7: "0 beyond 2tau=0.066" for
  fp16, "0 beyond 2tau=0.93" for bf16, "2 beyond 2tau=6.6" for int8).
- Source: `calibrated_tau_per_arm` and the per-arm rows (`tau`,
  `top1_flips`, `flips_beyond_tau`, `flips_within_tau`, `flip_gap_max`) of
  results/p2_rank_census.json (F-5, TinyLlama) and
  results/p2_llama32_rank_census.json (F-7); arms cuda_fp16_b1, cuda_bf16_b1,
  cuda_int8_b1, cuda_nf4_b1. Code semantics, read not re-run:
  `experiments/p2_rank_census.py` `census_row` passes `tau = 2 * tau` to
  `rank_census_topk`, whose `_census_core` counts `flips_beyond_tau` as
  `flip_gaps > tau`; so a row's `tau` field is 2 tau and its beyond-count
  is taken at 2 tau.
- Definition: per printed label, `tau` (calibrated), `tau_field` (the row's;
  check `tau_field == 2 * tau` within 1e-9, else UNRECOMPUTABLE),
  `multiple = round(label / tau)`, `label_is_2tau = (multiple == 2)`; per
  printed beyond-count, the row's `flips_beyond_tau` and whether it equals
  the printed count; `flip_gap_max` against `tau_field` and against the
  label (a printed count above 0 with `flip_gap_max` below the label cannot
  be a count at the label). Informational: the P2b thetas (0.142, 0.465,
  0.93, from results/p2b_escape_robustness.json `thetas`) as multiples of
  F-7's fp16 and bf16 tau.
- Rule: CORRECTED iff any printed label's `multiple` is not 2 (the label
  misstates the threshold); CONFIRMED otherwise. `status_by_count`:
  CONFIRMED iff every printed beyond-count equals the row's
  `flips_beyond_tau`; CORRECTED otherwise.
- Prediction (this protocol's; the ratios were seen): F-5's four labels and
  F-7's bf16 and int8 labels are 4 tau, F-7's fp16 label is 2 tau:
  CORRECTED; every beyond-count equals the census's count at 2 tau
  (`status_by_count` CONFIRMED); F-5's nf4 "3 beyond 2tau=12.3" has
  `flip_gap_max` 7.06 below 12.3, so its count is at 2 tau = 6.15.

### E18 — the zstd baselines carry no dictionary (D-6 read at the per-archive scale)

- Claim: DECISIONS.md:39-44 (D-6: "a format that only beats strawmen is not
  a format"); FINDINGS.md:58 and :62 (F-8: "7.6x below zstd-19"; "zstd-19
  3.618"); FINDINGS.md:91 and :94 (F-12: "the crossover vs
  zstd-19-concatenated is L~263"; "vs zstd-19 on the full text 7.28 per
  archive / 3.94 concatenated"); FINDINGS.md:101 (F-13: "amber wins 3.4x at
  k=16 at the file level"); README.md:31 ("7.6x below zstd-19"), README.md:45-46
  ("beating zstd-19-concatenated beyond L~263", "3.4x under zstd-19 per
  session"); docs/BLUEPRINT.md:50 ("7.6x below zstd-19"), docs/BLUEPRINT.md:81
  ("beats zstd-concat beyond L~263"); OPEN_QUESTIONS.md:31 ("3.4x under
  zstd-19 per session"), OPEN_QUESTIONS.md:32 ("crossover vs zstd-concat at
  L~263"); DECISIONS.md:132 ("3.4x under zstd-19 per session"). Every zstd
  comparator in the record runs without a dictionary; for a codec whose
  decoder is a shared model, a dictionary trained on held-out output of the
  same kind is the cheap shared-side-information comparator (the harvest's
  reading of the compression-research amortised-dictionary rule).
- Split: P1 rows 0-99 train the dictionaries; rows 100-199 are held out
  (row order; the harvest's split). Every rate below is on the held-out rows
  unless it says otherwise.
- Text: `full_r = tok.decode(ids_r)` (prompt and generation, special-token
  literals included, as `experiments/p5_binformat.py` `report_stage`
  decodes it) and `gen_r = tok.decode(ids_r[prompt_len_r:])`, UTF-8 bytes;
  tokenizer as E7 (the cached snapshot directory, offline; path and
  `tokenizer.json` sha256 recorded). `G` = generated tokens over the
  held-out rows (expected to equal the sum of `gen_len_r`).
- Dictionaries: `zstandard.train_dictionary(size, [full_r for r in 0..99],
  level=19)` for `size` in {4096, 16384, 65536, 262144} bytes, primary
  16384; `d16g` = the same size trained on `gen_r` of rows 0-99 (for the
  generated-text comparison). Each dictionary's byte length, sha256 and
  `dict_id` and the zstandard version are recorded. Compressors:
  `ZstdCompressor(level=19, dict_data=d)` and `ZstdCompressor(level=19)`.
- Quantities (bits per generated token): per archive, `zstd_arch[none]` and
  `zstd_arch[size]` = `8 * sum_r len(compress(full_r)) / G`; `amber_v3_arch`
  = `8 * sum_r per_row[r].bytes / G` from results/p5/encode_meta.json;
  informational `amber_v3_payload_only` = the same with `fixed_header_bytes`
  (results/p5_binformat.json) subtracted per archive, and
  `zstd_arch_dict16_amortised` = `zstd_arch[16384] + 8 * len(d16) / G`.
  Concatenated full text: `zstd_concat[none]`, `zstd_concat[16384]` on
  `"".join(full_r)`; crossover `L* = per_archive_const_bits /
  (zstd_concat - payload_gen_rate)` with both constants from
  results/p5_binformat.json `curve_model`, for both comparators (the
  printed 263 is this formula on all rows without a dictionary). Content:
  `amber_v0_content` = `sum_r amber_bits(ranks_r) / G` over the held-out
  rows' P1 draft ranks (`experiments/p1_divergence.amber_bits`, as E4;
  instrument check as E4's over all rows, else UNRECOMPUTABLE);
  `zstd_gen_concat[none]` and `zstd_gen_concat[d16g]` on `"".join(gen_r)`;
  multiples `zstd_gen_concat / amber_v0_content`. Sessions, reset mode, k in
  {8, 16}: the sessions of results/p6/k{k}_m0/meta.json whose `rows` are
  all >= 100; `amber_v4_session[k]` = `8 * sum bytes / sum gen_tokens`
  (meta); `zstd_session[k][none]` and `[16384]` = `8 * sum_s
  len(compress("".join(full_r for r in rows_s))) / sum gen_tokens` (the
  definition of `experiments/p6_sessions.py`, with the dictionary added);
  multiples `zstd_session / amber_v4_session`. Repetition split
  (informational): held-out rows whose repeat-4-gram share (E3's harvest
  definition, per row) is below 0.5: `amber_v3_arch` and `zstd_arch[16384]`
  over those rows. Dictionary effect at each scale: `effect = (none -
  dict16) / none`.
- Rule (per claim site, `status_by_claim_site`; the dictionary effect scored
  at the claim's own scale, threshold 0.10: a tenth moves the leading digit
  of a two-significant-figure multiple): per archive (D-6, F-12:94):
  CORRECTED iff `effect_arch > 0.10`; sessions k=16 (F-13:101, README:46,
  OPEN_QUESTIONS.md:31, DECISIONS.md:132): CORRECTED iff `effect_session16 >
  0.10`; concatenated full text (F-12:91, README:45, docs/BLUEPRINT.md:81,
  OPEN_QUESTIONS.md:32): CORRECTED iff `effect_concat > 0.10`; concatenated
  generated text (F-8:58/62, README:31, docs/BLUEPRINT.md:50): CORRECTED iff
  `effect_gen_concat > 0.10`; CONFIRMED otherwise in each case. The row's
  `status` is the per-archive one (the D-6 reading). Recomputed multiples
  and crossovers are reported beside each site whatever its status.
- Prediction (the harvest's, `amber-audit/spot6.py` and `spot7.py`, agent
  output): held-out per archive, amber v3 4.181, zstd-19 6.251, with a
  dictionary 4.737 (4 KB), 4.446 (16 KB), 4.408 (64 KB), so `effect_arch`
  about 0.29: CORRECTED; on held-out rows with repeat share below 0.5, amber
  5.253 against 10.330. This protocol's own: the concatenated effects are
  below 0.10 (both concatenated sites CONFIRMED); the session effect is not
  predicted.

### E19 — the rank-1 term transfers once conditioned on the top-2 gap

- Claim: FINDINGS.md:76 (F-10 item (4): "Cross-experiment estimate,
  weighting p2b's per-rank desync rates by P1's rank histogram (probable,
  different content)"); FINDINGS.md:136 (F-15's E15 bullet: P2b's rank-only
  rank-1 rate over-predicts the archives' rank-1 desyncs; "whether the
  correction excess is a property of target-generated content is not
  identified"). This row tests the transfer of the rank-1 (A) term across
  model, content and kernel path once the rate is conditioned on the
  encoder's top-2 gap; the correction (C) term cannot be conditioned the
  same way, because the P4 symbol streams carry only the top-2 gap, and
  stays rank-only.
- Source: the local dumps (manifest check for corpus, cpu_fp32,
  cuda_bf16_b1, cuda_fp16_b1; `load_corpus`, `load_arm`, `canonical_topk`,
  `keep` as E8c); the P4 symbol streams (`flag`, `rank`, `gap`), the P4
  decode shards (exposure, as E15's compensator) and
  results/p4_real_archive.json `first_desync_class_counts`; the theta-0 row
  of results/p2b_escape_robustness.json for the C rates (as E15);
  results/errata_recompute_2.json rows.E15 for the rank-only baseline.
- Definition: in the dumps, rank-1 positions are those with
  `rank_of_true == 1`; an A desync is one whose decoder top-1 differs from
  the true token (P2b's theta-0 A desync); `gap` = encoder top-1 minus
  top-2. Primary binning: 20 equal-count bins, edges at the quantiles
  0.05..0.95 of the dumps' rank-1 gaps (values outside the extremes fall in
  the end bins); `rate_D[b] = desyncs[b] / positions[b]` per decoder D in
  {cuda_bf16_b1, cuda_fp16_b1}. Sensitivity grid: equal-count with 10 and
  50 bins; log-spaced edges from the smallest positive rank-1 gap to the
  largest with 8, 16, 32 and 64 bins (the number of P4 rank-1 exposure
  positions falling in a bin the dumps leave empty is reported; such
  positions take the nearest non-empty bin's rate). Transfer: over each P4
  arm's decoded positions (`t < n_decoded`, rows matched to the streams as
  E15), `E_A = sum over A-flag positions of rate_D[bin(gap_t)]`; observed
  `O_A` = the arm's rank-1 first desyncs (E15's `observed_by_class`); `z =
  (O_A - E_A) / sqrt(E_A)`; beside it E15's rank-only `E_A` and z. Full
  prediction with the gap-conditioned A term and E15's rank-only C term
  (h4, theta 0): per-token hazard over all positions (`one_in`), the
  whole-archive `fail_exact` with per-position hazards, and E15's four
  comparisons against the measured hazard and failure rate.
- Rule: CONFIRMED iff `|z| < 2` for both arms at the primary binning (the
  dumps' rank-1 rate transfers to the archives once conditioned on the
  gap); CORRECTED otherwise. `status_e15_rule_gap_conditioned`: E15's pinned
  rule re-evaluated with the gap-conditioned prediction (CONFIRMED iff the
  measured hazard and failure rate exceed it on both arms). FINDINGS.md:136's
  "not identified" sentence concerns the C term, which this row does not
  condition; its claim-site status is CONFIRMED (it stands) and says so.
- Prediction (the second batch's critic, post hoc,
  results/errata_critic/c2_e15_gapsens.out.json, agent output): bf16 E_A
  30.0 to 33.3 against 28 observed, fp16 11.2 to 15.0 against 9, across its
  five binnings: CONFIRMED; with that A term the theta-0 prediction is one
  desync per 103 to 105 tokens and 73.9% to 74.7% failure for bf16, per 682
  to 725 and 25.9% to 27.4% for fp16, and the measured values exceed it on
  all four comparisons (`status_e15_rule_gap_conditioned` CONFIRMED).

2026-10-11 UTC, after the critic's pass on the third batch (RECOMPUTE
DISCREPANCY 0, BLOCKING 2). Values had been seen; no pinned verdict changes;
one row is relabelled post hoc and one correction is widened:
- E17 (the critic's BLOCKING 1): "only the labels are wrong" understated the
  correction. The 4-tau labels also produced the escape-cost figures quoted
  at them: FINDINGS.md:40 ("6.7% of positions at 0.142 (fp16's 2tau), 19.0%
  at 0.465, 32.6% at 0.93 (bf16's 2tau)"), FINDINGS.md:54 ("near-tie mass
  P(gap<0.142/0.465/0.93) = 8.3% / 23.2% / 39.1%", "the escape-symbol cost
  for a bf16 decoder is ~39% of positions on this model, for fp16 ~8%") and
  OPEN_QUESTIONS.md:16 ("~8% of positions for an fp16 decoder, ~39% for
  bf16"), now in `where`. Added: the near-tie mass (the share of kept
  positions whose cpu_fp32 top-2 gap lies below a threshold) at the printed
  thresholds and at each dtype's 2 tau, for Llama-3.2-1B-Instruct from the
  pinned dumps and for TinyLlama from results/p2, pinned for this purpose by
  results/p2_tinyllama_dumps.sha256 (written with tools/sha256_manifest.py
  and committed before the recompute). Instrument check: the printed masses
  at the printed thresholds must reproduce within 0.05 percentage points.
  Cost sites' `status_by_claim_site`: CORRECTED iff the mass at 2 tau,
  rounded as printed (whole percent), differs from the printed figure. The
  row status stays CORRECTED; the note no longer says "label defect only";
  `n_labels` counts the printed labels (the critic's ADVISORY 10).
- E19 (the critic's BLOCKING 2, the E13 case): the primary binning and the
  rule were written after the critic's post-hoc p2_quantile20 values
  (results/errata_critic/c2_e15_gapsens.out.json, committed 93ea7de) were in
  the record, and the primary values equal them by construction. The row
  carries `post_hoc` saying so; its `prediction` dict is emptied (not
  scored: identical by construction) with a `prediction_note`; a new field
  `status_out_of_sample` is CONFIRMED iff the absolute z is below 2 at every
  one of the six other binnings (chosen before any of their values were
  seen); the F-16 regime line says E19's primary values had been seen. The
  claim site FINDINGS.md:77 (item (4), C-only with the escape on; the critic's
  ADVISORY 6) is replaced by FINDINGS.md:78, F-10's caveat "the per-rank rates
  are what transfer, the mix is not", whose status is CORRECTED: E15 showed
  the rank-only rank-1 rate does not transfer, and E19 is consistent with
  transfer through the gap. Added (ADVISORY 5): the exact Poisson 95%
  interval of O/E per arm, the margins of the four E15 comparisons at the
  primary binning, and the count of binnings at which E15's rule holds; the
  text says "consistent with transfer at this sample size".
- Line pins (ADVISORY 3): the entry above cites FINDINGS.md:76, :94 and :101,
  which at 168efb0 are the findings' source lines; the claims are at 77, 95
  and 102 (the F-15 landing moved them). Corrected in `where`, the claim-site
  keys and `pinned_rule_sites`.
- E18 (ADVISORIES 4, 7, 8): FINDINGS.md:86 (F-11's "7.28 per archive") and
  DECISIONS.md:105 ("comparable to zstd") join `where` at the per-archive
  scale; the harvest's six predictions are scored against values computed
  under its own definitions (`harvest_definitions`: text decoded with
  special tokens skipped, repeat share divided by the row length), beside
  the pinned ones; `effects_without_literals` (the same effects on text
  decoded with special tokens skipped, dictionary retrained on it) are
  reported beside the pinned effects; the predictions line labels the
  harvest's values "(harvest)".
- Text (ADVISORY 9): the caveats line states the label rule as implemented:
  "erratum" where the row's pinned status is CORRECTED and a site there is
  corrected or is the site its pinned rule scores.

2026-10-11 UTC, after the dry run of the revised third batch (values had
been seen; the run is committed as results/errata_dryruns/dry_b3b.json). An
instrument-tolerance defect of the E4/E7 kind in the entry above: E17's
near-tie masses were computed over the kept positions (49,056, E8c's mask)
and checked within 0.05 percentage points, and F-7's printed "23.2%" at
0.465 came out 23.25% (the census counted all 49,152 positions, and a figure
printed at one decimal allows half a unit), so the F-7 and OPEN_QUESTIONS.md
cost sites came out UNRECOMPUTABLE. As amended: the masses are computed
over all census positions (every window position, no mask) and the
instrument check passes iff each printed mass reproduces at its printed
precision (rounded to one decimal); the kept-position masses stay in the
payload beside them. The payload records the sites' status under the entry
above as `status_under_pinned_tolerance`. This moves those sites from
UNRECOMPUTABLE to a decided status; no CONFIRMED/CORRECTED verdict changes.

2026-10-11 UTC, after the critic's second pass on the third batch
(RECOMPUTE DISCREPANCY 4.4e-16, floating point only; BLOCKING 1, on the
generated F-16 caveats line; the instrument amendment above judged the
E4/E7 kind). Text and labels only; no value or verdict changes:
- The caveats sentence said E17's masses are over the kept positions; they
  are over all census positions (49,152), as the entry above and the payload
  say. Fixed.
- E18's `prediction` dict restores the keys the third-batch entry pinned
  (per-archive zstd without and with each dictionary, and the repetition
  split under the pinned definitions) beside the `harvest_def_*` keys, so
  the scoring record shows both: the harvest's values miss the pinned
  quantities (its text skipped special tokens and its repeat share divides
  by the row length) and hit the same quantities under its own definitions.
- The F-16 source line lists results/errata_dryruns/dry_b3b.json.
- E19's FINDINGS.md:78 site key says its CORRECTED rests on E15's rank-only
  compensator z, a field added after the second batch's values were seen.
- A wording slip in the post-critic entry above: the cost comparison rounds
  at each figure's printed precision (F-5's to one decimal, F-7's and
  OPEN_QUESTIONS.md's to a whole percent), as the code does, not "whole
  percent" throughout.

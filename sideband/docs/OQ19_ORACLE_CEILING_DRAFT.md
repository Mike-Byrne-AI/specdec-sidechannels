# OQ-19 ORACLE-INTERMEDIATE CEILING — REGISTRATION DRAFT (UNFROZEN)

**STATUS (2026-10-01): UNFROZEN DRAFT. NOT A REGISTRATION. NOTHING OF OQ-19 HAS RUN.**

**Dated note 2026-10-11: SKIPPED by the operator's decision. No freeze
commit, no registration block, no harvest; this draft and the instrument
files stay as committed on 2026-10-01, unchanged except for dated notes
like this one, the run refusal in place.**

This file holds, verbatim, the registration block that was drafted for OQ-19
(plan-of-record item 2 of 2026-09-06, the oracle-intermediate ceiling: do the
TRUE tap-layer activations carry future-concept information beyond the full
free baseline at the registered reader?) together with the dated ledger note
that was to accompany it. It is committed so that the draft survives; it
confers no registration. Read it as a design proposal.

What is true on 2026-10-01, checked against the tree and the git log:

- docs/BLUEPRINT.md holds NO OQ-19 registration block (`git grep -c
  "OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION" -- docs/BLUEPRINT.md`
  prints nothing and exits 1: no match). No freeze commit exists. No
  replay, no registered cell and no GPU work of OQ-19 has run. The
  OPEN_QUESTIONS.md OQ-19 entry (the outline this block supersedes "where
  the two differ") stands as the only committed statement of the question.
  The tool refuses to run while its `DRAFT_UNFROZEN` flag is True
  (tools/run_fullfree_oracle.py, main()), and any payload it would write
  is stamped "UNFROZEN DRAFT"; the flag flips only in the freeze commit.
- The block's own words — "registered", "inserted here before any replay
  launched", "the freeze commit" — describe the plan as it was written on
  2026-09-06/07, not anything that happened. Its opening says two pre-run
  critic rounds; the PRE-RUN CRITIC ROUNDS bullet at its end records three
  (the opening was written before the third). The instrument docstrings
  say "registered in docs/BLUEPRINT.md" for the same reason; each carries
  a DRAFT banner since 2026-10-01.
- The instrument exists as three files, committed with this draft and
  banner-marked: src/sideband/real/oracle_replay.py, tools/run_fullfree_oracle.py
  and tests/test_fullfree_oracle.py (their last-modified times as listed on
  2026-10-01 before the banner edit: 2026-09-06 23:27, 2026-09-06 23:28 and
  2026-09-07 03:43; the banner edit reset them). The test file's pure-numpy
  tests pass without torch, 11 passed / 2 skipped on 2026-10-01. The three
  sat untracked in the worktree from 2026-09-07 to 2026-10-01; the
  registered commits of that period left them out — c4c4511 and fa6537e
  say so in their messages, c23f214 does not mention them (the gitignored
  HANDOFF.md records that it, too, left them out deliberately).
- How the draft was lost and recovered: the 2026-09-07 session that wrote
  it ended at the rate limit, the same night the OQ-18 leak rider fired at
  S1 L3 and took the lane (rider amendment 5ef3ccf, F-25 fa6537e), and the
  block lived only in that session's scratchpad. On 2026-10-01 it was
  rebuilt from the session transcript under the old project slug
  (`c--Users-Michael-Desktop-sideband`; the repo moved from
  Desktop\sideband to Desktop\Research\sideband) by replaying the
  transcript's Write/Edit calls, 471 lines, the count the 2026-09-14
  handoff recorded for it. docs/SHARP_EDGES.md "Work outside git is lost"
  records the mechanism.
- The post-F-25 review of 2026-09-14 recommended that OQ-19 be skipped or
  shrunk to a pilot (HANDOFF NEWEST-29, a gitignored file; the
  recommendation is restated here so that it survives). The owner has not
  decided. On 2026-09-14/15 the lane went to OQ-9 stage 1 instead (F-26).

## What a freeze would still owe (from the recovered patch scripts and the block's own bullets)

Recorded so that a future freeze does not rediscover them; none is done.

1. Insert the block below into docs/BLUEPRINT.md immediately before the
   "## Eval protocol (non-negotiable)" heading, and append the ledger note
   below to the OQ-19 entry of OPEN_QUESTIONS.md (the recovered
   `patch_docs_oq19.py` did both; its OPEN_QUESTIONS guard string did not
   match the note's wording, so re-check idempotence).
2. .gitignore: ignore `results/real/oracle_*/*.npz` (the replay side-files
   are gitignored raws, sha-bound by their committed metas) and negate the
   four state files `results/real/fullfree_oracle_{s1,s1_r,s3,s3_r}.json.state.jsonl`
   back in as evidence.
3. pyproject.toml: `psutil>=5.9` in the dev extra (the probe tool's RAM
   guard; the test imports it with importorskip; the RAM test already reads
   a fixed `available` figure, the recovered `patch_ram_test.py` having been
   applied before 2026-10-01).
4. The SMOKE CONTACT bullet at the end of the block is empty by design: it
   is to be recorded before the freeze commit, after the GPU is free.
5. Re-read every "registered" / "freeze" sentence in the block and the three
   docstrings and make them true, or strike them, at freeze time; remove the
   DRAFT banners and flip `DRAFT_UNFROZEN` to False then and only then.
6. Decide first whether to run OQ-19 at all, or as a pilot (the 2026-09-14
   recommendation), and record the decision with its date.
7. Line endings before any attestation: tools/run_fullfree_oracle.py is
   CRLF in this worktree and LF in the index, and the driver attests the
   RAW bytes of its own file (`run_fullfree._sha`, `sha256(read_bytes())`),
   so a freeze run from this worktree would cite a CRLF sha that an LF
   checkout cannot reproduce, while `git status` reads the file as clean
   under autocrlf, so the `-dirty` guard would not catch it (the EVID-1
   class; docs/SHARP_EDGES.md "Frozen instruments are byte-pinned").
   Normalising the file to LF on disk alone does NOT close it: this box
   checks out with `core.autocrlf=true` and `.gitattributes` covers only
   `results/**`, so a fresh clone here writes CRLF again and an LF sha
   would then fail to reproduce (the other half of EVID-1). The two fixes
   that close both halves, in the freeze commit: make the attestation
   LF-normalised (`tools/run_prefetch_bigram.py:141-144` is the precedent,
   `.replace(b"\\r\\n", b"\\n")` before hashing), or store LF and pin the
   file with an `eol=lf` / `-text` attribute. tests/test_fullfree_oracle.py
   is also CRLF on disk but nothing hashes it; normalise it for
   consistency only. (Added 2026-10-01 from the docs-maintainer's audit and
   the critic's scoped pass; read from the code, nothing has run.)

## The registration block as drafted (verbatim; rebuilt 2026-10-01 from the 2026-09-07 transcript)

OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION (2026-09-06, pre-run;
written BEFORE any replay or registered cell ran, while the OQ-18 runs
were in flight, and held in scratch until their payloads were written
so that their attestation stayed clean; inserted here before any replay
launched; two pre-run critic rounds applied and recorded at the end of
this block; the replays and the registered cells launch only after the
freeze commit AND after OQ-18's labels are read):
- PROVENANCE / PLAN OF RECORD. Item 2 of the user's 2026-09-06 plan of
  record ("the oracle-intermediate ceiling second, and then assess").
  NON-CRITERION for F-15 / F-17: this test measures the ceiling every
  sketch competes for and prices P9 (docs/FUTURE_IDEAS.md); it changes [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
  no finding's label in any branch (a dated note may be added to a
  finding, never a relabel). The ledger outline (OPEN_QUESTIONS.md
  OQ-19, same day) is SUPERSEDED by this block where the two differ;
  the dated note under that entry names every departure, including the
  outline's two STRUCK sentences (its "reader artifact" reading and its
  "no sketch ... can beat ... there" closure) and its wrong "5 x 210"
  (both sources hold 8 primary and 4 replication seeds).
- THE POINT. The S1 and S3 telemetry sources are LOSSY VIEWS of an
  intermediate activation of the same forward pass: the S1 sketch
  reads the down_proj input act(gate(x)) * up(x), a deterministic
  function of the MLP input x = post_attention_layernorm(residual) at
  the tapped layer (transformers 4.57.3 modeling_llama.py: the decoder
  layer feeds the norm's output to the MLP, whose down_proj input is
  act_fn(gate_proj(x)) * up_proj(x)); the S3 expert set is
  topk(softmax(gate(x))) of the router input x, the post-attention-
  norm output of that MoE layer (modeling_olmoe.py: the norm's output
  is reshaped and fed to the gate). The full free baseline holds that
  forward pass's FINAL state h_a exactly (F-23). A lossy view cannot
  carry information its source does not, so the true x at the tapped
  layers bounds IN INFORMATION every sketch of them and every union of
  such sketches — and the stored oz IS x up to numerics: both RMSNorms
  return bf16, and float16 stores a bf16 normal exactly within its
  range (the capture refuses a non-finite or out-of-range value;
  values below float16's smallest normal lose precision, a sub-bf16-
  noise effect). SCOPE, pinned:
  (1) that is an information bound, NOT a bound on a fixed reader's
  accuracy (OQ-17 (iv): raw h_a sat below the floor at linear while
  the 657 summaries of the same p_a read fine), so every label here is
  a statement about the registered reader; in particular, since a
  sketch is a function of x, a SKETCH FIRE beside an oracle null proves
  that the registered reader failed to recover from the raw block what
  it recovers from the sketch — it can never mean the sketch fire was
  an artifact (the reading is named READER-LIMITED below); (2) S2's
  attention pages depend on the K cache of EARLIER positions, which x
  at the anchor does not determine, so S2 (P8) is NOT bounded here.
- DESIGN: REPLAY, not re-harvest (dated 2026-09-06, before any
  replay). sideband.real.oracle_replay drives each committed harvest's
  logged generations through the IDENTICAL batched, left-padded, KV-
  cached path the harvester used — the same prompt batches in the same
  order (batch 16 from the parent meta; chunk_bounds reproduces the
  harvester's range(0, n, 16) slicing), the same padding and chat
  template with the pinned date, the same forward kwargs, the same
  library versions and GPU (the replay asserts transformers, torch and
  the GPU name equal to the parent meta's — 4.57.3 / 2.6.0+cu124 / RTX
  3080 Ti — and records bitsandbytes and the attention implementation),
  the model and load regime READ FROM THE PARENT METAS (S1: NF4 double-
  quant bf16-compute; S3: NF4 with bf16 routers, verified by module
  inspection as the harvester does), AND the harvester's own per-row
  sampling generators, re-seeded from the parent's row-seed convention
  and DRAWN AT EVERY STEP exactly as the harvester drew. Running rows
  are fed the LOGGED token; rows past their logged length are fed the
  DRAWN token. Why the draws matter (second critic round, B1): the
  harvester kept sampling and feeding post-EOS tokens on finished rows
  and only zeroed them in storage; on dense Llama a finished row's
  input cannot touch another row's numbers, but OLMoE's MoE block
  groups tokens per expert ACROSS the rows of a batch and its 4-bit
  kernels take different paths for one-token and multi-token expert
  inputs (the gemv-vs-gemm path R1 calibrated), so a finished row's
  input changes the running rows' numerics — 35.5% / 32.8% of valid
  S3 positions (primary / replication) are EXPOSED, a running row's
  step counting as exposed iff another row of its batch has a logged
  length below that step (12.6% / 8.3% at S1). Feeding the drawn token
  restores the identical inputs, and the draws themselves are STORED
  (drawn, every step, post-EOS included), so the post-EOS feeds are on
  record. The capture point is the harvester's (after the forward that
  produced p_a, before the next token is fed) and is CERTIFIED IN CODE:
  on the first batch of every seed a pre-hook on each registered
  layer's MLP module asserts that the tensor the MLP receives equals
  the captured norm output (the replay aborts otherwise; the meta
  records the check). Everything beyond a row's length is zeroed on
  write and again on load, in the oracle and in every fidelity array;
  only `drawn` is kept whole. Why replay: (i) the SAME rows, labels,
  anchors, committed cells and twins as OQ-17 / OQ-18 — the oracle
  arms pair against the committed fplus / fplus_b / fplus_r cells on
  identical prompts, and the sketch's D on those rows is already
  committed evidence; (ii) no new population and no new fidelity
  rider; (iii) FIDELITY IS MEASURED, not assumed, per position: the
  DRAWN token against the logged token — a one-sample test of p_a at
  that position, whose match RATE over valid positions bounds the mean
  discrepancy of the replayed p from the logged one; a flipped draw on
  a valid position does not perturb the replay (the logged token is
  still fed) and reads as a p-difference, not misalignment, which
  would show as match rates far below the floor and O(1) h differences
  on every row; the post-EOS draws are certified only indirectly,
  through the running rows' subsequent h_a and draw matches — beside
  two DETERMINISTIC p diagnostics, reported never gating: the
  recomputed argmax against the logged argmax and the recomputed
  probabilities of the logged top-32 ids against the logged top-32
  probabilities (max-abs); the recomputed sketch (the S1 ShadowTap re-
  created with the parent meta's layers and per-layer sketch seeds,
  asserted equal; the S3 RouterTap) against the logged slots — set
  OVERLAP per layer (the fraction of the logged set found in the
  recomputed set) and exact equality as a diagnostic — and the
  recomputed h_a against the logged hidden (max-abs difference).
  ALIGNMENT CERTIFICATE: the oracle is captured in the same forward as
  h_replay, and h_replay must agree with h_logged at the same anchor
  within the registered floors (an off-by-one would show as O(1)
  differences on every row); at load the probe tool additionally requires each side-file's
  lengths and prompt_idx to equal the harvest rows it occupies (the
  lengths leg is the one that can see a seed swap — prompt_idx is
  arange(210) on every seed), recomputes every meta's fidelity summary
  from the arrays and refuses a mismatch. The side-files live in their
  OWN directories (results/real/oracle_shadow, oracle_shadow_r,
  oracle_moe, oracle_moe_r): sideband.harvest.verified_seed_files
  refuses a harvest directory with mixed prefixes, so nothing is
  written beside the committed npz (the replay refuses an out-dir that
  is the harvest directory or holds another prefix's metas, and NEVER
  rewrites a committed side-file, --overwrite or not); each
  oracle_s{seed}.meta.json (committed) binds the PARENT npz sha, the
  layers, the load regime, the versions, the GPU and the fidelity
  summary, and the oracle npz (gitignored raw) binds to its meta by
  sha. The loader opens each parent's side-file BY THE PARENT'S NAME in
  the harvest's own seed order (verified_seed_files sorts
  lexicographically, so a replication harvest reads s10, s11, s8, s9 —
  a numeric-seed sort would have refused every replication harvest;
  caught on critic review). The R1 rider's calibrated tolerances
  (overlap 27-31 of 32 across the gemv-vs-gemm kernel paths) are NOT
  the relevant band here: the replay uses the incremental path with
  the same batch composition and the same inputs; the fidelity record
  says how close it gets, and the floors below decide.
- ORACLE DEFINITION AND LAYERS (pinned). oz = the post-attention-norm
  output at the last position per row, float16, at layers l in: S1 =
  {7, 15, 23, 31} — ALL FOUR tapped down_proj layers, so the oracle
  covers everything the S1 sketch reads and the committed fplus_b /
  fplus_r pair is like-for-like; S3 = {3, 7, 11, 15} of the sixteen
  router layers, evenly spaced with the last MoE block included — a
  storage / width economy (16 x 2048 = 32,768 oracle dims and about
  28 GB per primary harvest were judged too wide for the registered
  reader and this box), so S3 trains a LIKE-FOR-LIKE four-layer sketch
  arm beside the oracle (fplus_b4 / fplus_r4 = the expert ids of those
  four layers only, 4 x 64 = 256 dims, expected arm total 5,009,
  recorded, never asserted) and REPORTS the committed sixteen-layer D
  beside it — the sixteen-layer sketch reads layers the oracle does
  not cover, so it is never an input to READER-LIMITED or to any
  closure sentence. Dims: S1 oracle 4 x 4096 = 16,384 (fplus_o 657 +
  2048 + 4096 + 16,384 = 23,185); S3 4 x 2048 = 8,192 (fplus_o
  12,945). Storage, float16 over the parent's padded (rows, T = 256):
  14.09 GB for S1 primary (8 x 210 x 256 x 16,384 x 2 bytes), 7.05 GB
  S1 replication, 7.05 GB S3 primary, 3.52 GB S3 replication, 31.7 GB
  in all (critic recompute; 140 GB free on the volume on 2026-09-06;
  the replay's preflight requires the side-file bytes plus 5 GB free).
  RAM: the S1 primary oracle array is 14.09 GB (13.12 GiB) in memory
  beside the harvest's own arrays; the box holds 31.8 GiB (34.1 GB);
  the probe tool REFUSES TO START unless available memory (psutil,
  added to the dev extra in the freeze commit) exceeds the array plus
  8 GiB — the guard compares bytes — recorded in the payload, so
  oracle probe runs go ONE PROCESS AT A TIME and never beside an OQ-18
  process; the tool also asserts the oracle width equals the model's
  hidden width, refuses a registered out paired with the wrong harvest
  at launch, and refuses a --parent-finding that is not the source's.
- FIDELITY PRECONDITION (pinned; mechanical in the probe tool, from
  summaries it recomputes from the arrays). Per side-file, over VALID
  positions only: (1) the drawn-token match rate must be >= 0.99; (2)
  the minimum per-layer MEAN sketch-set overlap must be >= 0.95; (3)
  the h_a relative max-abs difference (|h_replay - h_logged|_max /
  |h_logged|_max) must have median <= 0.01 AND 99th percentile <= 0.05.
  The exact-match rate is REPORTED as the sketch-sensitivity diagnostic
  and never gates (bit-exactness is not oracle faithfulness: a same-
  model non-bit-exact forward gives 27-31 of 32 overlap while its
  oracle would still be within bf16 noise of x; and a median-only h leg
  would let half the positions come from a wrong context — hence the
  p99 leg). Otherwise the source is ORACLE-INVALID: the probe tool
  REFUSES TO TRAIN A CELL, no label issues, and the registered path is
  a DATED diagnosis of the replay (batch composition, kernel non-
  determinism, load regime) — never a widened floor and never a label
  read through an unfaithful oracle. Expectation: draws matching at
  0.999 or better, overlap near 1.0 and h_exact_rate above 0.9 (the
  same kernel path on the same batches with the same inputs).
- ARMS (block ORDER identical across arms — TOK and hz are the OQ-17
  factory's own classes, byte-identical by a CI test; the committed
  cells are PAIRED, never re-trained):
  fplus_o      = (a) ++ TOK ++ hz ++ oz, with oz clipped to the TRAIN
                 support and z-scored with TRAIN moments by the hz rule
                 (run_fullfree.train_moments on the replayed array; its
                 sha recorded; the hz moments sha asserted equal to the
                 committed OQ-17 payload's);
  fplus_o_r    = (a) ++ TOK ++ hz ++ oz read from the prompt-level-
                 deranged row (run_fullfree_twin.derangement_by_prompt,
                 seed 1000 + train seed — the SAME other-prompt rows as
                 OQ-18's twin: the tool asserts its per-seed permutation
                 shas equal to the committed twin payload's, so the
                 oracle twin and the sketch twin share their derangement
                 mechanically: a matched control, no bias in D_o or the
                 survival-fraction point, a positively correlated twin-
                 noise term that narrows the ratio's CI), equal dims by
                 construction (refused otherwise);
  fplus_o_lead = (a) ++ TOK ++ hz ++ oz read at anchor min(a + 2,
                 length - 1) of the SAME row — the forward that CONSUMED
                 the offset-2 label (at a row's last anchors, the
                 forward that produced its distribution). A POSITIVE
                 CONTROL, leaky by construction, at the gate offset
                 only, never a result. What it certifies and what it
                 does not: a reader that never opens the 16,384-dim
                 block returns D_o = 0 with a narrow CI and would read
                 NO-HEADROOM by reader failure (the direction this arc
                 has gone twice), and this arm refuses that reader; it
                 does NOT certify sensitivity to a WEAK signal in the
                 block (a graded control would be needed for that), and
                 that residual is the stronger-reader path named under
                 every label;
  S3 only: fplus_b4 = (a) ++ TOK ++ hz ++ the four registered layers'
                 expert ids (SubsetSlotsBlock, a strided view of the
                 committed slots array) and fplus_r4 = its deranged twin.
  The committed cells paired: at L1 the OQ-17 payload's fplus /
  fplus_b / fplus_n and its shuffled fplus, plus the OQ-17 twin
  diagnostic's fplus_r (off2 mlp256 only); at L3 the OQ-18 payload's
  fplus / fplus_b / fplus_r / (a) and its shuffled fplus; all read
  through their sha-header-bound state files, and the committed sketch
  gate row (D_r at L1 from the twin payload; D at L3 from the OQ-18
  payload) must reproduce from those cells to 1e-12 at load or the run
  aborts. Pairing new cells with committed cells is safe by
  construction: the same harvest gives the same anchor table, split
  and trials; margins() refuses unequal trials or any cluster count
  but 30. The tool refuses any grid cell id colliding with a committed
  cell, asserts --n-slots equal to the harvest's alphabet (512 slots /
  64 experts) and derives the parent finding from the source tag.
- CELLS. Per harvest, space by space — L1 then L3; L2 is OMITTED for
  economy and said so (OQ-18 covers L2 for the sketch; the ceiling at
  L2 is not measured): the LEAK RIDER first — shuffled fplus_o at off2
  / linear / seed 0 against the COMMITTED shuffled fplus of the same
  space + 0.01 — then at off2 every arm x mlp256 x 3 seeds, and at each
  further registered offset the arms minus the lead control: S1 L1
  {2, 3} (F-15's horizon), S1 L3 {2, 3}, S3 L1 {2} (F-17's L1 horizon),
  S3 L3 {2, 3} (OQ-18's off4 is not carried). Totals: S1 2 x (1 + 3 x 3
  + 2 x 3) = 32 cells (30 trained + 2 shuffled); S3 (1 + 5 x 3) + (1 +
  5 x 3 + 4 x 3) = 44 (42 + 2); four harvests, 144 trained + 8
  shuffled. WHAT THE RIDER DOES AND DOES NOT SEE: it catches a (row,
  anchor)-level leak in the block assembly, as OQ-17 / OQ-18's legs
  do; it is BLIND to a misaligned replay (an oracle captured one step
  late would predict the true label and the shifted label alike), so
  alignment rests on the h_a and drawn-token certificates and the
  load-time row checks, not on the rider. Its effective detection
  threshold is wider than 0.01 because a high-dimensional epoch-0
  shuffled arm sits below the shuffled reference (OQ-17 / OQ-18
  smokes: 1.2-1.9 points; at 23,185 dims expect more) — carried as a
  disclosure, the band not tightened post hoc. A failed leg halts the
  run before any payload (the harvest, hence the source, is then
  label-less). Trainer, budget, estimand, bootstrap and pairing byte-
  identical to Phase 3 / OQ-17 / OQ-18.
- READER-VALIDITY PRECONDITION per (harvest, space) at the gate cell
  off2 / mlp256, FOUR legs: (1) every new mlp256 probe (9 on S1, 15 on
  S3) has test_acc >= majority_rate_test - 0.001; (2) the Mf_x row —
  fplus_o at mlp256 paired against the COMMITTED linear (a) cells of
  the same rows (the OQ-18 collapse leg) — has CI95 upper >= 0; (3)
  the LEAD row, acc(fplus_o_lead) - acc(fplus_o), fires the Phase-3
  triple rule with point >= +0.02; (4) all rows structurally complete.
  Else READER-INVALID at that space; the dense 16,384-dim oz block
  dominating the input norm (F-24's mechanism, four times hz's width)
  is the likeliest cause and is named as the reader residual under
  every label. The committed fplus / fplus_b / fplus_r probes were
  valid when committed and are not re-checked.
- READOUTS (pinned), per space: D_o = acc(fplus_o) - acc(fplus_o_r),
  equal dims, THE gate readout; Mt_o = acc(fplus_o) - acc(fplus)
  against the committed fplus, quoted beside D_o; Mn_o = acc(fplus_o_r)
  - acc(fplus), the oracle twin's own gain; Lead = acc(fplus_o_lead) -
  acc(fplus_o), the control, quoted with every label; D_sk =
  acc(fplus_b) - acc(fplus_r), the committed sketch on the same rows
  (at L1 off3, where no fplus_r cell was committed, the fplus_n row is
  reported and labeled so); D_4 = acc(fplus_b4) - acc(fplus_r4), S3
  only, the like-for-like sketch; SF = D_sk / D_o (S1) or D_4 / D_o
  (S3) at the gate cell — the SURVIVAL FRACTION, the ratio of the
  seed-summed per-prompt paired success deltas over the same 30 test
  prompts, with a cluster-bootstrap percentile CI (one (n_boot, n)
  index matrix from default_rng(0), the house draw convention; n_boot
  2000; resamples with a non-positive oracle denominator are dropped
  and counted; no house helper admits signed per-cluster numerators,
  hence the local loop) — WRITTEN AS UNDEFINED by the tool wherever
  D_o does not fire or the reader is invalid, so no ratio to a null
  denominator ever exists to quote; a point above 1 reads "the sketch
  above the raw block at this reader" and earns the READER-LIMITED
  name only with CI lower > 1; a point below 0 "the sketch's own delta
  is negative"; Mf_x as above.
- GATE AND LABELS (pinned). Gate per (harvest, space): off2 / mlp256
  D_o under the Phase-3 triple rule (CI95 lower > 0, all three seeds
  positive, point >= +0.005; n_seeds 3, n_clusters 30, the fplus_o-
  fplus_o_r pairing). Per (SOURCE, SPACE) from both harvests (tools/
  run_fullfree_oracle.py --conclude-from PRIMARY REPLICATION,
  mechanical; it refuses a partial payload, a failed rider, a payload
  whose harvest / out name / levels / offsets / oracle layers are not
  the registered ones, a trained-cell count other than 30 (S1) / 42
  (S3), a missing or structurally thin D_o row, a same-harvest pair,
  and — re-hashing on disk — any committed payload or state file, any
  committed oracle META, or any oracle npz present on disk that changed
  since the run; the npz are gitignored and re-hashed only when
  present, the metas always; resumed_cells is RECORDED and disclosed,
  not refused — a crash late in a 7-10 hour run continues from its own
  state file with --resume): ORACLE-INVALID if either harvest fails
  the fidelity floors; READER-INVALID if either fails the reader
  precondition; HEADROOM iff the gate fires on both; SPLIT iff on one;
  NO-HEADROOM iff on neither AND every D_o row of both harvests at
  that space has CI95 upper < +0.005; NOT-SHOWN otherwise. HORIZON at
  off3 (S1 both spaces, S3 L3): OFF3-HEADROOM / OFF3-NO-HEADROOM /
  OFF3-NOT-SHOWN / OFF3-SPLIT / OFF3-INCOMPLETE by the OQ-17 rule.
  READER-LIMITED READING, recorded mechanically: the committed LIKE-
  FOR-LIKE sketch's gate row (D_sk at S1, D_4 at S3) fires the triple
  rule on BOTH harvests while the oracle reads NO-HEADROOM at that
  space (a one-harvest sketch fire is not READER-LIMITED; the S3
  sixteen-layer sketch never is). MULTIPLICITY: eight gate cells (two
  sources x two spaces x two harvests) and six horizon cells (three
  (source, space) pairs x two harvests), one readout each, no
  correction, both harvests as the insurance.
- READINGS AND CONSEQUENCES (pinned; NON-CRITERION — no F-15 / F-17
  relabel in any branch):
  * NO-HEADROOM at (source, space) WITHOUT the READER-LIMITED reading:
    a dated STATUS line on K-2 naming the reader and the layers: "the
    z-scored raw activation block at these layers adds no material
    margin over the full free baseline at the registered reader, and
    none of the MEASURED like-for-like sketches of those layers fired
    the registered rule on both harvests either; at this reader a
    further sketch of those layers, or a union of them (P9), is not
    worth a cell; the stronger-reader residual is the only open path
    on the existence layer" — at S3 scoped to the four registered
    layers. The sentence is scoped to the reader and the measured
    encodings — never "no sketch can": a fixed reader's null on one
    encoding does not bound its accuracy on another (SCOPE (1)).
  * NO-HEADROOM WITH the READER-LIMITED reading: NO closure sentence
    issues. A dated note on the finding that carries the like-for-like
    sketch fire (the OQ-18 finding — F-25 by sequence, unwritten at
    this registration — for OQ-18's L3 rows; F-24's twin-diagnostic
    rows at L1) says only: "the raw-activation ceiling test read NO-HEADROOM
    at the same reader; the reader is thereby shown not to recover
    from the raw block, at this reader, the information it recovers
    from the sketch; the sketch fire stands as measured". The route is
    the stronger-reader path; the sketch fire is never called an
    artifact.
  * HEADROOM: the table is MEASURED — D_o beside Mt_o, Mn_o and the
    Lead control, the SF with its CI — and quoted in a dated STATUS
    line on K-2; the MIRROR reading is pinned too: HEADROOM beside a
    committed like-for-like sketch that did not fire (F-24's L1 cells
    are that case if D_o fires there) says the sketch's encoding lost,
    at this reader, information the raw block carries (SF near 0) —
    non-criterion, reported. P9 is then a candidate for that headroom,
    with this rider: if OQ-18 has read ABSORBED at L3 as well as L1
    (K-2 FIRED at every registered space at the registered reader),
    any further telemetry existence test, P9 included, is a POST-HOC
    REROUTE AROUND A FIRED KILL CONDITION in those words, needs its own
    registration and the user's authorization in those terms, and
    this block does not authorize it. EAGLE-3 (docs/PRIOR_ART.md:
    multi-layer target features as draft input) is named as the
    deployable form of the ceiling — a positive result re-derives its
    premise, and the D-2-named oracle is observability-violating and
    never a deployable source.
  * NOT-SHOWN / SPLIT: OPEN; dated STATUS lines naming the harvests;
    no closure sentence either way; a third harvest is not authorized.
  * ORACLE-INVALID / READER-INVALID: no reading; the dated diagnosis /
    reader amendment named above, before any further cell.
  * Every sentence names the reader and the layers and quotes the Lead
    control; none touches conversion (K-3), acceptance or wall-clock.
- HONEST PREDICTION (pinned before any replay): fidelity — drawn-token
  match >= 0.999, per-layer mean overlap >= 0.99 and h_exact_rate
  above 0.9 on every side-file, h relative max-abs median below 1e-3;
  Lead fires with point >= +0.05 at every gate cell (the control
  passes). Per (source, space): S1 L1 NOT-SHOWN, with D_o
  +0.003..+0.010 — surprise in either direction: HEADROOM, or
  NO-HEADROOM (every upper below the floor at that band is unlikely);
  S1 L3 HEADROOM with D_o +0.010..+0.030 — surprise: NOT-SHOWN or
  NO-HEADROOM; S3 L1 NOT-SHOWN — surprise: HEADROOM or NO-HEADROOM; S3
  L3 HEADROOM with D_o +0.010..+0.040 — surprise: anything else. SF
  where defined below 0.3 at S1 and below 0.5 at S3 (the four-layer
  sketch) — surprise: SF above 0.5 anywhere, or a point above 1; Mt_o
  positive at every gate. Also surprising: ORACLE-INVALID (a token-
  match rate below 0.99 would say the replay is not the identical
  path after all); READER-INVALID at S1 (the 23,185-dim arm),
  including a Lead below +0.02.
- RUN ORDER AND SCOPE. Nothing launches until OQ-18's four payloads are
  written and its labels read (plan-of-record order). Then: the four
  replays, one at a time (planning figures from the parent metas'
  runtime_s, critic recompute: S1 primary mean 263 s per seed, S1
  replication mean 490 s, S3 primary mean 2718 s, S3 replication mean
  2172 s — about 68 minutes for S1 and 8.5 hours for S3 in all, plus
  the per-step draws; not wall-clock claims, D-9); then the four probe
  runs ONE PROCESS AT A TIME in the order S1 primary, S1 replication,
  S3 primary, S3 replication (the RAM guard enforces it), and NO probe
  launches while any OQ-18 process is alive; probe-time planning:
  OQ-17's S1 cells averaged 547 s at 6.8-8.8k dims, data-assembly
  bound, so at 23,185 dims expect two to three times that — of the
  order of 7-10 hours of cells per S1 harvest and comparable for S3's
  five arms. The gitignored oracle npz files are kept for the arc and
  their metas are COMMITTED BEFORE ANY PROBE RUN, so every payload
  binds committed metas. --only smoke runs on scratch out paths only
  (a smoke of each tool disclosed before the freeze; smoke state never
  copied in); FRESH-STATE PIN on the registered state files. The
  replay module, the probe tool, their tests, the psutil dev
  dependency and the .gitignore lines (the oracle npz ignored; the
  fullfree_oracle state files negated) are committed in the freeze
  commit and every launch is from that HEAD. What this does not do:
  touch any finding's label, run L2, run S2, test a stronger reader,
  or claim conversion.
- EVIDENCE. results/real/oracle_{shadow,shadow_r,moe,moe_r}/oracle_s*
  .meta.json (committed; npz gitignored, sha-bound); results/real/
  fullfree_oracle_s1.json, fullfree_oracle_s1_r.json,
  fullfree_oracle_s3.json, fullfree_oracle_s3_r.json (+ .state.jsonl,
  negated in .gitignore); src/sideband/real/oracle_replay.py; tools/
  run_fullfree_oracle.py; tests/test_fullfree_oracle.py (registered
  spaces / offsets / arms / layers; the grid with the lead control at
  the gate offset only and its refusal against committed ids; the
  oracle, lead and subset blocks with their twins and the free blocks'
  byte-identity to the OQ-17 factory; the committed-cell selection per
  space; the rider against the committed shuffled fplus; the oracle and
  four-leg reader preconditions including the reader that never opens
  the block; the labels and horizons; the survival-fraction bootstrap
  with the house draw convention and its undefined and READER-LIMITED
  forms; --conclude-from refusals including counts and the on-disk
  re-hash of the committed files and metas, resumed cells recorded;
  the replay helpers, the set-overlap rule, the hygiene finalizer, the
  fidelity summary and its recompute check, and the loader's seed-
  order / row-alignment / fidelity-recompute / out-dir refusals on
  real files).
- PRE-RUN CRITIC ROUNDS (recompute mode, 2026-09-06, before the freeze
  commit; nothing of OQ-19 had run). ROUND 1 recomputed every figure
  and found three blockers, all applied: the side-file loader sorted
  by numeric seed and would have refused both replication harvests —
  it now opens each parent's side-file by the parent's name in the
  harvest's own order and checks lengths / prompt_idx row by row, with
  a real-file test on seeds 8-11; the NO-HEADROOM consequence inverted
  data processing — the "reader artifact" reading became READER-
  LIMITED, no closure sentence issues under it, the closure sentence is
  scoped to the measured encodings, and no non-criterion relabel of a
  criterion-bearing fire exists; NO-HEADROOM was not separable from a
  reader that never opens the oracle block — the fplus_o_lead positive
  control and its precondition leg were added; plus its conditions
  (overlap floors instead of bit-exactness, the rider's blindness
  stated, versions asserted, the figures corrected, the post-hoc-
  reroute wording, SF undefined under a null gate, out-dir / overwrite
  refusals, re-hash in conclude, the RAM guard, symmetric surprises).
  ROUND 2 found three more blockers, all applied: the "identical path"
  premise was false on OLMoE at about a third of positions because the
  harvester fed post-EOS samples to finished rows and the replay fed
  zeros — the replay now re-seeds the harvester's generators, draws at
  every step, feeds the draws to finished rows and gates on the drawn-
  token match rate; psutil was an undeclared dependency — added to the
  dev extra with an install hint on import failure; the "when present"
  test re-hashed gitignored npz files — --conclude-from now re-hashes
  the committed metas and the npz only when present; plus its
  conditions (the .gitignore lines in the freeze commit, the committed
  side-file never rewritten, the closure sentence scoped to like-for-
  like sketches firing on both harvests and to the four S3 layers, the
  READER-LIMITED wording, the ledger note naming the struck sentences,
  the L3 fire attributed to F-25, the Lead leg's scope stated, --resume
  recorded not refused, the house draw convention, the fidelity
  summary recomputed at load, the twin permutation shas asserted, the
  alphabet and parent finding derived, the GPU name and disk headroom
  asserted, the mirror reading pinned, non-finite captures refused).
  ROUND 3 confirmed the replay loop step for step against the
  harvester (generators, draw order, the break step, the EOS step's
  feed) and found three more, all applied: the ledger-note patch was
  not idempotent (guard string fixed); the drawn-token certificate was
  overstated and the draws were not stored — `drawn` is now stored
  whole, the certificate is worded as a match RATE bounding the mean
  p-discrepancy with the post-EOS feeds certified only indirectly, and
  the deterministic argmax / top-32-probability diagnostics were added
  (reported); the ledger note omitted two departures (off4 not
  carried; the oracle is the post-attention-norm OUTPUT, not the
  residual input) — added; plus its advisories (the git-tracked check
  fails closed, the load-time finiteness check on float16 without a
  cast, the row-seed convention and layer-count assertions, the
  launch-time pairing refusal, the in-code MLP-input check on the
  first batch, the h arrays zeroed beyond length, units and wording).
- SMOKE CONTACT: (recorded before the freeze commit, after OQ-18's
  labels are read and the GPU is free.)

## The dated ledger note as drafted (verbatim; it was to be appended to the OQ-19 entry of OPEN_QUESTIONS.md)

(Dated note, 2026-09-06, later the same day, before any replay or
registered cell: the outline above is SUPERSEDED by the BLUEPRINT block
"OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION", the registration of
record, in these respects. STRUCK from the outline's (v): the sentence
"a sketch-D fire on the same rows with D_o null is a READER ARTIFACT ...
and routes to the stronger-reader path, never to a sketch-beats-oracle
claim" and the sentence "no sketch of these layers and no union of them
can beat the full free baseline THERE" — a sketch is a function of the
oracle, so a sketch fire beside an oracle null proves the reader failed
to recover from the raw block what it recovers from the sketch, never
that the fire was an artifact (the reading is now READER-LIMITED, with
no closure sentence under it, and the closure sentence elsewhere is
scoped to the measured like-for-like encodings at the registered
reader). DEPARTURES: (1) the oracle is produced by REPLAYING each
committed harvest's logged generations through the harvester's
identical batched KV-cached path with the harvester's own per-row
generators re-seeded and drawn at every step (running rows fed the
logged token, finished rows the drawn token — the OLMoE MoE block
groups tokens across rows, so finished rows' inputs matter), not by
harvesting a fresh population; the oracle arms therefore pair against
the SAME rows, committed cells and twins as OQ-17 / OQ-18, and fidelity
is MEASURED per position (drawn-token match rate, the draws stored;
argmax and top-32-probability diagnostics; sketch-set overlap per layer
with exact match as a diagnostic; h_a max-abs difference as the
alignment certificate) with pinned floors, ORACLE-INVALID below them;
(2) both sources hold 8 primary and 4 replication seeds — "5 x 210" was
wrong; (3) layers: S1 7 / 15 / 23 / 31 (all four tapped, not two), S3
3 / 7 / 11 / 15 of 16 with a like-for-like four-layer sketch arm
(fplus_b4 / fplus_r4), the sixteen-layer sketch reported only; the
stored oracle is the post-attention-norm OUTPUT (the MLP / router
input, certified in code on the first batch of every seed), not the
outline's "residual-stream input" — RMSNorm discards the residual's
scale, a definitional change that is right for the information
argument; (4) label spaces L1 and L3 only (L2 omitted, stated), and the
horizons are off3 only — the outline's S3 L3 off4 is not carried; (5) the committed fplus /
fplus_b / fplus_r cells are PAIRED, not re-measured; (6) a four-leg
reader precondition including the fplus_o_lead POSITIVE CONTROL (the
oracle read two positions ahead; a reader that never opens the block
cannot pass its leg; it certifies not-blind, not sensitivity to a weak
signal); (7) the survival fraction's CI is a local cluster bootstrap in
the house draw convention (no house helper admits signed per-cluster
numerators), not sideband.stats.paired_ratio_delta_ci, and it is written
as UNDEFINED where D_o does not fire; (8) labels HEADROOM / SPLIT /
NO-HEADROOM / NOT-SHOWN / READER-INVALID / ORACLE-INVALID with the
READER-LIMITED reading; the honest prediction is pinned in the block.
Instrument: src/sideband/real/oracle_replay.py, tools/run_fullfree_
oracle.py, tests/test_fullfree_oracle.py; evidence results/real/
oracle_*/oracle_s*.meta.json and results/real/fullfree_oracle_{s1,s1_r,
s3,s3_r}.json + state files. Nothing launches until OQ-18's labels are
read.)

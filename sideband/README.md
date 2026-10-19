# sideband

When a large language model generates text, something has to fetch its
weights. A memory device that serves them, or a tier that holds a
mixture-of-experts model's experts, sees which weight groups or experts each
token touched, as a byproduct, without reading an activation value or a
logit. sideband asked whether that address stream could help the small draft
model in speculative decoding guess upcoming tokens better. The verifier is
never touched, so the most this could buy is speed, never a different output
(F-0, F-1). This repository is the record of that test: two streams, S1 and
S3 (defined below), on one consumer GPU, in registered runs between
2026-08-29 and 2026-10-17.

**The answer is negative at the registered reader at L1 and L2, the label
spaces where the kill criterion fired at both sources, and at L1 under three
stronger readers as well; it is open at L3, the grouped label space (the
three spaces and the reader are defined below); the record issues no
all-space sentence.** The probes do find a small signal. At the pinned L1
cells, with a linear probe, the stream raises top-1 accuracy at predicting
the concept bucket of the token two positions ahead by +0.0141 at S1 (the
replication harvest) and +0.0147 at S3 (the primary) over a 657-number
summary of what the decoder already knows (F-15, F-17; the table below gives
the companion harvests). Against the fuller free baseline the record then
built, the logged summaries of the target's next-token distribution, its
hashed top-32 token ids and its hidden state at the anchor, read by the
registered reader mlp256, the stream's own margin at those L1 cells is about
+0.003 (F-24's words), under the +0.005 floor the registration set, and no
material amount more than a scrambled block of the same size adds; at L2 the
same reading holds (F-25, read under a rider amendment the record calls "a
post-hoc reroute around a fired kill condition"). Three stronger probe
readers, run later at both sources, did not overturn the L1 result (F-28 at
S3, where they also read the L3 lenses; F-29 at S1), and L3 stays open at
both sources. At S1 two registered attempts to turn the signal into more
emitted tokens per verify call were null against the bar set in advance,
+0.062 tokens per call over every comparator arm (F-19, F-21), and the
hidden state one lane tried to rebuild from the stream turned out to be an
exact function of the target's own next-token distribution, information the
decoder already has (F-23). Conversion and reconstruction were never run at
S3, and this page reads them as unrun, not as nulls.

How it was run, and by whom. Every real-model run was registered in
docs/BLUEPRINT.md before its data existed, with its cells, readouts and
conclusion labels pinned, and judged against kill criteria written first
(docs/WHY_THIS_DIES.md); the record names its own exceptions where they
occur, F-25's rider amendment above among them, and registered text with an
error gets a dated erratum, never a rewrite. One human researcher set the
questions, the kill criteria and every launch, void and close decision, and
arbitrated. An AI coding assistant (Claude Code) built the instruments, ran
the analyses and drafted the registrations, the findings and the
documentation, this page included. The "adversarial reviewer" or "critic"
named throughout is a second AI agent of the same model family as the
assistant, run as its subagent: not a human, and narrower than an
independent reviewer. Its body is .claude/agents/sideband-critic.md (naming
the Opus model since 2026-10-01); from Phase 3 of the record on (the probe
stage, F-15 onward) it recomputed the landed labels and intervals from the
committed state files and per-prompt summaries and blocked commits until
its objections were answered. A recovered selection of its scripts and
round reports of the harness era (from 2026-10-01; the earlier rounds were
not found) is under docs/audits/critic-recovered/; what it caught is in
docs/METHOD.md section 6 and what it cannot in section 7. Nothing here
measures speed: wall-clock claims are banned by rule (D-9), and the currency
is emitted tokens per verify call.

Terms this page uses, one line each (full entries in docs/GLOSSARY.md):

- S1 and S3: the two streams tested. S1 is a value-aware tap on the
  Llama-3.1-8B-Instruct target (at four layers, the slot ids of the top-32
  units ranked by activation magnitude times weight-column norm, hashed into
  512 slots; it needs activation values to rank them), with
  Llama-3.2-1B-Instruct as the draft. S3 is the pure address stream:
  OLMoE-1B-7B-0125-Instruct's top-8-of-64 expert ids at each of its 16
  gates, no router logits, no values. S2, KV pages, was never run.
- Free baseline: what any speculative decoder already has at the last
  verified position (D-5); every margin is measured over it. The proxy free
  baseline is a 657-number summary of the target's next-token distribution;
  the full free baseline adds its hashed top-32 token ids and its anchor
  hidden state.
- Equal-dims twin: the same block of features with its alignment to the
  data destroyed, trained beside the tested block from the mechanism
  controls on (F-16) and in every full-free re-test (F-24 onward); a margin
  the twin also shows is not credited to the block.
- Reader: the probe, a small classifier (linear or the MLP called mlp256),
  that reads the features; the registered reader is mlp256 at the
  registered training budget, and F-28 and F-29 tried three stronger ones.
  Every label is a statement about the reader that produced it.
- Cell: a (label space, offset, reader capacity) combination of the probe
  grid; the registration names in advance which cells decide a label.
  F-24 and F-29 gate on the L1 cell at offset 2; F-25 on the L2 and L3
  cells; F-28 on L1 and the two L3 lenses.
- L1, L2, L3: the three label spaces the probes predict for the upcoming
  token: 16 classes, 15 concept buckets and a merged glue class (L1); 510
  concepts plus the glue class (L2); and 16 transition-coherent groups of
  those concepts plus the glue class (L3, a lopsided partition the record
  calls the mega-group lens, with a balanced variant at S3).
- Anchor and offset: the anchor is the last verified position, whose
  forward produced the telemetry; offset j is j tokens ahead of it.
- ABSORBED, NOT-SHOWN, SPLIT, K-2-ISOLATED, K-2-NOT-OVERTURNED-AT-S1: the
  pinned conclusion labels; each links to its glossary entry in the table
  below. ABSORBED means no material margin over the full free baseline at
  the +0.005 floor, never "no margin".
- Never run is never read as a null: a stage that did not run (conversion
  and reconstruction at S3; the S2 stream) is reported as unrun.
- Tokens per verify call: the currency of conversion; the bar, +0.062 tokens
  per call over every comparator arm, vanilla included, was pinned on
  2026-09-01 before any conversion run (docs/ECONOMICS.md).

## The verdict in the record's words

**The answer is negative at the registered reader's pinned cells, and the
record issues no all-space sentence.** At the pinned L1 and L2 cells of
both sources the margin the probes detect in the stream is ABSORBED by the
full free baseline: no material equal-dims margin at the +0.005 floor,
never "no margin"; the coarse-label L3 cells are OPEN at both sources. At
S1, the value-aware tap, conversion into emitted tokens per verify call was
not shown in two registered attempts, and the hidden state the
reconstruction lane targeted turned out to be an exact function of free
information; neither was run at S3, the pure address stream, and this page
reads them as unrun, not as nulls, under the record's rule that a stage
never run is never read as a null. Three layers are kept apart and the
scorecard reads them one at a time; each conclusion label links to its
entry in docs/GLOSSARY.md, and every number is copied from FINDINGS.md or
this page.

| Layer | Verdict | One number | Record |
|---|---|---|---|
| Existence: does the stream carry future-concept information the decoder does not already have? | Shown against the proxy free baseline at two sources (F-15, F-17), then [ABSORBED](docs/GLOSSARY.md#a) by the full free baseline at the registered reader at the pinned L1 cells of both sources (F-24) and at L2 (F-25, read under a rider amendment the record calls "a post-hoc reroute around a fired kill condition"); L3 open at both sources (S1 [NOT-SHOWN](docs/GLOSSARY.md#n), S3 [SPLIT](docs/GLOSSARY.md#s)); under three stronger readers at S3 the final word is [K-2-ISOLATED](docs/GLOSSARY.md#k) (F-28); under the same three readers at S1 the word is [K-2-NOT-OVERTURNED-AT-S1](docs/GLOSSARY.md#k) (F-29: R-N (hz-rescaled) ABSORBED; R-T (two-tower) ABSORBED; R-L (longer budget) ABSORBED). Kill criterion K-2 FIRED at the registered reader at L1 and L2, with the +0.005 materiality scope; no all-space sentence. | every equal-dims gate D CI95 upper below +0.005 at the F-24 cells (mlp256), against the linear proxy margins of +0.0141 [+0.0081, +0.0203] at S1 (the pinned replication cell; the primary's point +0.0163) and +0.0147 [+0.0113, +0.0182] at S3 (primary; replication +0.0173 [+0.0133, +0.0221]) | FINDINGS.md F-15, F-17, F-24, F-25, F-28, F-29; docs/WHY_THIS_DIES.md K-2 |
| Conversion, S1 only (never run at S3): does that information buy tokens per verify call at a matched drafting budget? | Not shown in two registered attempts, both null against the bar "CI95 lower > 0 and point >= +0.062"; K-3 FIRED at Attempt #1; the fold-back hard stop holds. | +0.006860 [-0.015024, +0.025572] tokens per call vs vanilla (F-19); +0.002664 [-0.044719, +0.046727] vs vanilla and -0.081846 [-0.132484, -0.035567] vs the same head on free features (F-21) | FINDINGS.md F-19, F-21; docs/WHY_THIS_DIES.md K-3 |
| Reconstruction, S1 only (never run at S3): how much of the verifier's anchor hidden state does a linear map recover from the stream? | A qualified pass at the registered gate (F-22), closed by the dated erratum F-23: the target is an exact linear function of the anchor's full next-token distribution, free under D-5 ([TARGET-FREE](docs/GLOSSARY.md#t)); no partition branch claimed. | delta_free +0.204984 [+0.153698, +0.288162] (F-22; inflated about 25% by two out-of-support test prompts); full-logit inverse relative error 2.5e-8 median (F-23) | FINDINGS.md F-22, F-23 |

Two side results stand beside the verdicts, both NON-CRITERION: the
seed-noise floor (F-27: a same-policy seed change moves pooled tokens per
call by a CI95 half-width of 0.0385 / 0.0398 at 210 prompts on the K3 /
OQ15 populations; [FLOOR-MATERIAL](docs/GLOSSARY.md#f),
[BAR-RESOLVED@210, RULE-LEAKS@30](docs/GLOSSARY.md#b)) and the prefetch
read on the OLMoE router stream (F-26 and its rungs:
[PREFETCH-HEADROOM](docs/GLOSSARY.md#p) stands, while with the forward's
own final-norm state (reduced to 1024 directions) and two tokens' smoothed
routing profiles in the free arm no material margin of the address stream
is shown at horizons 1 to 4 at this reader,
[LEAD-TIME-ABSORBED](docs/GLOSSARY.md#l), where "absorbs" names the label,
not a mechanism; K-6 stays UNTESTED). No wall-clock or speedup claim of this
system exists in this repository (D-9; instrument runtimes are logged as
provenance only).

Dated note 2026-10-17: the plain-language opening and the term list above
were added in lane D of the 2026-10-15 image audit
(docs/audits/2026-10-15-image-audit/README.md), whose two walkthrough
readers met the record's labels before their definitions, and one of whom,
reading the staging export, found the reviewer named as an agent only at
line 169 of it (the audit report's figure). The front door of 2026-10-14
stands in this section unchanged: its verdict paragraph, its table and its
side-results paragraph; its first paragraph, the question and the two
sources, is folded into the opening above.

## Check a number without a GPU

The Quickstart below recomputes F-22's registered margin from the committed
state file with the record's own estimator in one Python snippet, and notes
that the same recipe over a run's state file or summary reproduces F-15,
F-17, F-19, F-20 and F-21; the registered CPU analyses from Phase 3 on
ship per-cluster `*.state.jsonl` recompute surfaces under results/real/,
and the GPU verdict runs their per-prompt summaries.

## How to read the record

- docs/REPORT.md: the technical report with its scorecard; start here. Its
  abstract keeps the 2026-09-05 wording ("existence is shown") under the
  dated record-boundary note above it, which reads that sentence as
  superseded by F-24; the first scorecard row keeps the same wording and
  the dated rows added beneath it carry the later words.
- docs/FINDINGS_INDEX.md: one line per finding, F-0 to F-29, then
  FINDINGS.md for the entry itself (regime and source lines on every one).
- docs/WHY_THIS_DIES.md: the seven kill criteria with dated STATUS blocks.
- docs/BLUEPRINT.md: every registration, amendment and outcome in order
  (the audit trail, not an introduction; docs/BLUEPRINT_INDEX.md lists its
  blocks).
- docs/GLOSSARY.md: house terms, and a headed entry for each label the
  front door above links (all but TARGET-FREE's added on 2026-10-14);
  docs/METHOD.md: how the research was run; docs/LESSONS.md: the rules the
  record's own limitations taught, from the 2026-10-15 image audit
  (docs/audits/2026-10-15-image-audit/, the report and its recompute scripts).
- [tests/README.md](tests/README.md): what the test suite checks, which
  tests fail rather than skip when committed evidence is missing, which
  test files a registration pins byte for byte, and how to run part of it.

## What a clone cannot reproduce

- The raw arrays: 3,894 gitignored .npz files, 13,369,799,824 bytes (about
  13.4 GB) by the 2026-09-05 inventory (docs/DATA.md); 5,175 files, 14,456,199,684
  bytes on 2026-10-19 with the twelve seed-6 and replay folders (docs/DATA.md,
  the deposit section); sha256-bound in the committed metas and summaries; the tools
  that consume them refuse to run without them (the repo map below), and
  the committed `*.state.jsonl` files are the intended CPU recompute
  surface.
- The GPU runs themselves: a 12 GB card and the gated Llama checkpoints; a
  fresh harvest need not be bit-identical to the committed one, because the
  CUDA paths are not bit-deterministic (docs/REPRODUCE.md section 4). CPU
  recomputes from committed evidence reproduce the record's numbers given
  the file order and the numpy version the record names (the same section).

## The question in full

The opening as it stood from 2026-09-05 to 2026-10-13, unchanged:

**Can the memory-access address stream alone - which weight groups or experts
the verifier touched, with no activation values and no logits leaving the
device - steer a speculative-decoding draft model enough to matter?**

Speculative decoding lets a small draft model propose a block of tokens that a
large target model (the verifier) accepts or rejects in one forward pass; the
Leviathan/Chen rejection scheme guarantees the output distribution is the
target's. A weight-serving memory device, or any tiered fetch-on-demand weight
store, sees for free which weight groups or MoE experts the target touched per
token. That address stream costs no accelerator compute and no floats on the
wire. SD^2 (docs/PRIOR_ART.md) shows that a drafter steered by the verifier's
full hidden state accepts more tokens; this repo asks what survives when the
only signal is a hash sketch of the access pattern. Because only the draft
side is ever modified, steering can change speed but never outputs - the
verifier here is exact to float64 epsilon under arbitrary steering (F-0/F-1:
worst closed-form deviation 2.2e-16, FINDINGS.md; results/e01_verifier_exactness.json).

Three layers are kept apart throughout and must not be conflated: EXISTENCE
(does the stream carry information the decoder does not already have),
CONVERSION (does that information buy tokens per verify call), and
RECONSTRUCTION (how much of the verifier's hidden state the stream recovers).
Every real-model number below is from one pair - Llama-3.1-8B-Instruct (NF4)
target with a Llama-3.2-1B-Instruct draft, or OLMoE-1B-7B-0125-Instruct for
the MoE source - at draft length gamma 4, temperature 1.0, one RTX 3080 Ti
(12 GB), 210-prompt sets (a pinned 150/30/30-cluster harvest split for the
probes; a fresh verdict population for each conversion run). No wall-clock or
speedup claim exists anywhere in this repo (D-9; the seconds the run metas log
are provenance); the currency is emitted tokens per verify call.

## Status at a glance

House status words (docs/GLOSSARY.md): "shown" = a registered gate or
finding says so, with a CI clear of zero on the registered estimand; "not
shown" = the registered test ran and did not clear its bar (a null), or the
claim was never put to a registered test; "unpriced" = a quantity the repo
names but has not measured, or cannot separate under the registered readout,
so no magnitude is licensed; "qualified" = shown, but only in a narrower
sense than the plain words suggest, and the qualifier is part of the claim.
CI95 = prompt-cluster bootstrap 95% interval; every number is copied from
FINDINGS.md, whose entries name the results/ files. House terms the table
uses without expansion (anchor, offset, free baseline, matched drafting
budget, fold-back, lane, support clip, noise twin, the DR-n diagnostics)
are defined in docs/GLOSSARY.md.

| Layer | Status | Headline numbers (FINDINGS.md) | Evidence |
|---|---|---|---|
| Existence: telemetry carries future-concept information beyond the strongest free baseline at offsets >= 2 (2-3 at S1; 2 at S3, reaching 3-4 only under coarse labels) (kill criterion K-2) | shown against the 657-summary proxy, replicated on fresh seeds at two sources; DATED NOTE 2026-09-06 (F-24): ABSORBED by the FULL free baseline ((a) ++ hashed token ids ++ z-scored h_a) at the registered reader at the pinned L1 offset-2 cells of both sources — every equal-dims D CI95 upper below +0.005, Mt beside it about +0.003 (dated note 2026-10-12: the four F-24 cells read +0.0034 / +0.0033 at S1 and +0.0033 / +0.0013 at S3, primary / replication; F-24's own words are "+0.003 or less", a three-place rounding); corrected-twin reading TWIN-ROBUST (S1) / TWIN-ROBUST (S3); K-2 STATUS 2026-09-06 | S1 (compute-tier weight-slot tap, Llama-3.1-8B): pinned replication cell +0.0141 [+0.0081, +0.0203] top-1 accuracy over the free-features probe; margins span +0.008..+0.044 over floors of 0.41-0.59 (F-15). S3 (pure address stream: top-8-of-64 expert ids at 16 OLMoE gates): +0.0147 [+0.0113, +0.0182] primary, +0.0173 [+0.0133, +0.0221] replication, up to +0.0721 [+0.0652, +0.0792] at coarse labels (F-17). Neither margin is prefix-topic state at the histogram-feature level (F-16, F-18; richer prefix families remain an untested residual; dated note 2026-10-12: F-16 and F-18 each carry a dated note of 2026-09-06 reading the mechanism moot for the L1 margin at the registered reader, in their words "a margin below the materiality floor and not beyond the equal-dims twin has no mechanism to price", with "the histogram-level rejection of topic-state as an explanation of the PROXY margin" untouched). | results/real/probes_s1*.json, probes_s3*.json and their .state.jsonl; DATED NOTE 2026-09-14 (F-25): [read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] at the coarse label spaces L2 / L3 the re-test reads S1 L2 ABSORBED; S1 L3 NOT-SHOWN; S3 L2 ABSORBED; S3 L3 SPLIT (every L3 label read at the L3 group lens (S1: one mega-group of 455/510 concepts including all 165 zero-degree concepts, the next group 10; S3: two mega-groups of 268 and 193 = 461/510 including all 20 zero-degree concepts)) against the full free baseline at the registered reader; DATED NOTE 2026-10-05 (F-28, STAGE LENS): through a size-capped BALANCED lens at S3 L3 the full-free re-test reads ABSORBED at the registered reader (D +0.0019 [+0.0006, +0.0032] / +0.0004 [-0.0011, +0.0018], every upper below +0.005 at off2 / off3 / off4; Mn_r +0.0023 [+0.0010, +0.0038] / +0.0017 [-0.0000, +0.0035], the corrected twin point-positive on both harvests, CI-clear on the primary only) where the lopsided lens read SPLIT, and F-17's proxy margin survives the lens at +0.0221 [+0.0187, +0.0258] / +0.0195 [+0.0160, +0.0232] (0.307 / 0.267 of the recorded margin) with its growth over L2 NOT-SETTLED; the stronger readers (STAGE READERS) are not yet run; DATED NOTE 2026-10-05 (F-28, STAGE READERS): under the hz-rescaled and two-tower readers at the S3 gate cells R-N (hz-rescaled) at L1 ABSORBED; R-N (hz-rescaled) at the lopsided L3 SURVIVES-STRONGER (EQUAL-DIMS-ONLY, the twin's larger cost); R-N (hz-rescaled) at the balanced L3 NOT-SHOWN; R-T (two-tower) at L1 ABSORBED; R-T (two-tower) at the lopsided L3 ABSORBED; R-T (two-tower) at the balanced L3 ABSORBED; the K-2 word at S3 K-2-ISOLATED (under readers R-N and R-T at S3 (R-L pending); one more family of readers, not K-2's universal; interim: READERS-LONG runs under the pinned trigger and the one sentence lands with it); DATED NOTE 2026-10-09 (F-28, STAGE READERS-LONG): under the longer-budget reader at the S3 gate cells R-L (longer budget) at L1 ABSORBED; R-L (longer budget) at the lopsided L3 SURVIVES-STRONGER (EQUAL-DIMS-ONLY, inflated by the twin's own cost); R-L (longer budget) at the balanced L3 ABSORBED; the FINAL K-2 word at S3 over both reader stages K-2-ISOLATED (under readers R-N, R-T and R-L at S3; one more family of readers, not K-2's universal); S1 not run; DATED NOTE 2026-10-17 (F-29, S1 READER RE-TEST): at the S1 gate cell under the same three readers R-N (hz-rescaled) ABSORBED (D +0.0026 [+0.0008, +0.0043] / +0.0022 [+0.000497, +0.0039]); R-T (two-tower) ABSORBED (D +0.000339 [-0.000377, +0.0011] / +0.0011 [+0.000363, +0.0019]); R-L (longer budget) ABSORBED (D +0.000382 [-0.0009, +0.0016] / -0.000044 [-0.0014, +0.0013]); the S1 word K-2-NOT-OVERTURNED-AT-S1 (under readers R-N, R-T and R-L at S1; one more family of readers, not K-2's universal) |
| Conversion: information becomes tokens per verify call at matched drafting budget (K-3) | not shown - two registered attempts, both null against the bar "CI95 lower > 0 and point >= +0.062" | Attempt #1, adaptive block scheduling on frozen S1 probes: +0.006860 CI95 [-0.015024, +0.025572] vs vanilla (F-19). Fold-back #1, outcome-supervised acceptance head: +0.002664 CI95 [-0.044719, +0.046727] vs vanilla and -0.081846 [-0.132484, -0.035567] vs the same head on free features only (F-21). Earlier, the bucket-bias logit actuator was null-to-harmful (confirmatory arm -0.0098 [-0.0155, -0.0039], F-12) at every tested granularity (F-13) with a perfect-forecast ceiling of +0.0014 [-0.0043, +0.0069] acceptance (F-14). | results/real/k3_verdict_s1_arm*.summary.json, oq15c_verdict_s3_arm*.summary.json |
| Reconstruction: a linear map from the S1 stream recovers the anchor hidden state h_a (OQ-16 Stage R) | shown at the reconstruction level, then closed by the dated erratum F-23 (2026-09-05): the target is free information; no partition branch claimed | Registered gate: delta_free +0.204984 [+0.153698, +0.288162] over the free baseline (F-22), inflated about 25% by two out-of-support test prompts. Deployable reading with the DR-1 support clip: tel_vs_trivial +0.250784 [+0.239316, +0.261616]; R^2 free / telemetry / noise twin +0.083 / +0.253 / +0.090. DR-2: a free hashed encoding of p's top-32 token ids (FREETOK) reconstructs slightly better than telemetry, -0.004792 [-0.007192, -0.002600] (FREETOK R^2 +0.258). DR-3: telemetry plus that encoding (UNION) beats FREETOK by +0.065180 [+0.062411, +0.067705] (UNION R^2 +0.324; 37.5% of the free margin). DR-4: the stronger token-encoding comparator was itself worse than FREETOK, -0.003085 [-0.004984, -0.001280], label COMPARATOR-TOOTHLESS, so whether telemetry adds anything beyond p itself stayed unpriced. F-23 then priced it by identity: h_a is an exact linear function of the anchor's full next-token distribution p (48 pinned rows: full-logit inverse relative error 2.5e-8 median; top-4097 log-probs per-row R^2 +1.0000; top-32 R^2 +0.014), so the stream's reconstruction is a lossy copy of information the decoder already has. | results/real/oq16_stage_r*.json and .state.jsonl; results/real/oq16_ha_identity.json |

Dated note 2026-10-11: the three rows above were checked against
FINDINGS.md through F-28 at the public cut; every number they quote
appears in FINDINGS.md and no row changed. Two paragraphs below the
table, written 2026-09-05, gained dated notes the same day (the one-line
reading; the "two stronger free baselines" bullet). Dated 2026-10-12: the
existence row gained two dated clauses that day; its earlier numbers are
unchanged and the four numbers added appear in F-24.

Stage A - the SD^2-style injection actuator that would have tested conversion
of the reconstruction - was frozen pre-GPU in commit 2e44105 (docs/BLUEPRINT.md,
STAGE-A FREEZE, 2026-09-05) and closed the same day by the dated OQ-16 erratum
(F-23) before any GPU run: its telemetry arms are struck because the vector
they would inject follows exactly from the verifier's own next-token
distribution, and the remaining oracle arm is a free-actuator question outside
the lane's claim that needs its own registration if it is ever run. No export,
adapter, or GPU run exists; the lane has ended and the fold-back hard stop holds.

The calibrated one-line reading: existence of a cheap signal that the
registered free baselines do not carry is established at probe level; usable
magnitude through any actuator tried is not; and the reconstruction lane ended
when its target turned out to be free information. See docs/REPORT.md for the
full narrative and docs/FINDINGS_INDEX.md for a one-line-per-finding index.

Dated note 2026-10-11 on the reading above (written 2026-09-05, before
F-24): "established at probe level" holds only against the 657-summary
proxy (F-15, F-17). Against the full free baseline, at the registered
reader, K-2 FIRED at the probe level at L1 (F-24: ABSORBED at both
sources, twin-robust at both) and at L2 (F-25, both sources, read under
the rider amendment the existence row's F-25 note carries); L3 is OPEN
at both sources (F-25: S1 L3 NOT-SHOWN, S3 L3 SPLIT; "no all-space
sentence issues", docs/WHY_THIS_DIES.md K-2 STATUS 2026-09-14). F-28
then tested the stronger-reader residual at the S3 gate cells only (L1
and both L3 lenses, offset 2): the final K-2 word there is K-2-ISOLATED
("one more family of readers, not K-2's universal"; the S3 L1 kill
stands, S3 L3 stays OPEN at the registered reader); S1 not run. (Dated
2026-10-17: the S1 gate cell then ran under the same three readers as a
new registration, F-29: K-2-NOT-OVERTURNED-AT-S1.)

What is NOT measured here, so that the two existence results are not read as
a speedup claim:

- Wall-clock, latency, throughput, energy: nothing, by rule (D-9; K-5). The
  HF adapter crops KV caches by default (since b1dae57, 2026-08-29), but
  nothing here is a benchmark harness, so it is acceptance-valid only; the
  sidecar's own latency was never timed.
- Source S2 (KV pages): never run. Kill criteria K-4, K-5, K-6: untested; no
  finding rules on them (docs/WHY_THIS_DIES.md, dated STATUS lines).
- Cross-seed variance of a verdict: every CI is across prompt clusters at one
  registered seed (plus one voided seed per arc that told the same story); the
  seed-vs-seed noise floor exists only as an unregistered planning note
  (docs/BLUEPRINT.md, STAGE-A FREEZE power note).
  Dated note 2026-10-04 (F-27): the seed-vs-seed floor is now MEASURED for the
  VANILLA policy at two seed pairs — a CI95 half-width of 0.0385 / 0.0398 at
  210 prompts and 0.0982 / 0.1032 at 30, per-prompt seed-pair r 0.4232 /
  0.4172, a +0.062 point win by seed noise alone in 0.1060 / 0.1320 of
  30-prompt subsets (a cross-seed, same-policy, single-comparator null;
  docs/NOISE_FLOOR.md); the verdict arms' own cross-seed variance and the
  same-seed null the gate legs faced stay unmeasured.
  Dated note 2026-10-10 (OQ-20, F-27's STAGE REPLAY line): one further seed
  per vs-vanilla leg and per mechanism-matched free leg was run — each
  verdict's two legs replayed at seed 6 under their frozen policies read
  MUTUAL-COVERAGE / REPRODUCES on both populations (SPREAD-COVERED,
  FREE-SPREAD-COVERED; K3 +0.010340 [-0.009288, +0.030521] vs vanilla and
  +0.010109 [-0.009724, +0.030422] vs the free arm, OQ15 -0.018029 [-0.065168,
  +0.028495] and -0.053623 [-0.107526, -0.002448], every guard held, no bar
  cleared); on K3 the two stage words are not two confirmations (the free leg
  is nearly the vs-vanilla leg, |R5 - R1| = 0.000231), and on OQ15 the
  cross-seed differences' CI95 half-widths (0.0666 / 0.0707) exceed the +0.062
  bar, so a bar-sized move is not resolved there; the cross-seed variance
  stays unestimated; the draft_conf legs and the same-seed null stay
  unmeasured.
  Dated note 2026-10-16 (image audit): every probe CI (F-15 to F-18, F-24, F-25,
  F-28) is a prompt-cluster bootstrap over counts summed across three train
  seeds, so it is also conditional on those three trained probes. The audit's
  seed-inclusive brackets (docs/audits/2026-10-15-image-audit/seed_var_out.json)
  cover 72 rows of F-24, its corrected twin and F-25 only; F-15 to F-18 and
  F-28, its SURVIVES-STRONGER cells included, are not bracketed. No label moves;
  three bracketed readings are seed-sensitive (F-25's S1 L2 deciding row, F-24's
  S1 corrected-twin CI-clear reading, F-24's S3 linear CI-positive qualifier)
  and a fourth, the primary S3 L3 Mn_r below-zero reading behind F-25's post-hoc
  "same shape" sentence, has its upper above zero under all three (dated notes
  there).
- The existence margins (F-15, F-17) against two stronger free baselines:
  one that includes the anchor's token identities (the FREETOK class DR-2
  introduced at the reconstruction layer), and a NONLINEAR probe on the full
  next-token distribution (the OQ-6 h-probe exists only at linear capacity,
  where it adds nothing over the 657 summaries; F-23 (iii)). Both untested;
  docs/IDEAS.md carries them. [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
  Dated note 2026-10-11: "both untested" was written 2026-09-05. F-24
  (2026-09-06) tested the margins at the registered reader against a
  baseline carrying hashed token identities and z-scored h_a read at
  mlp256 (F-24's full free baseline; h_a is an exact linear function of
  the full p, F-23): ABSORBED at both sources; F-25 extended the re-test
  to L2 / L3 and F-28 to three more readers at S3. The F-28 readers ran
  only at the S3 gate cells (L1, both L3 lenses, offset 2); every other S3
  cell and all of S1 stay untested under them (S1 not run, final; dated
  2026-10-17: the S1 gate cell then ran under them as a new registration,
  F-29, K-2-NOT-OVERTURNED-AT-S1), and a
  reader outside that family stays untested everywhere (F-28's
  K-2-ISOLATED word; dated note 2026-10-12: "that family" is the three
  F-28 readers R-N, R-T and R-L, and the registered reader itself ran in
  F-24, F-25 and F-28's STAGE LENS, R0 in its payloads).
- Other model pairs, longer prompts, batch above 1, an unquantized verifier
  (beyond the 20-prompt bf16 rider in F-10), a fine-tuned drafter.
- The anticipatory reconstruction target (the verifier's state at FUTURE
  anchors), the one reconstruction question F-23 leaves open; the fine-k oracle
  cell F-14 left; a distilled-drafter comparator.

## What this repo is

A pre-registered, kill-criteria-gated test of one question, built so that the
record is hard to fool. The method, in five bullets (full treatment in
docs/METHOD.md):

- Every stage is registered as a dated block in docs/BLUEPRINT.md before any
  number exists: data, estimand, decision rule, an exhaustive set of pinned
  conclusion labels, the honest expected outcome, reserved seeds.
- Kill criteria K-1..K-7 (docs/WHY_THIS_DIES.md) were written first, with
  their decision rules; outcomes are recorded in place and a fired kill is
  followed by a registered fold-back count and a hard stop.
- Findings enter FINDINGS.md only with `- regime:` and `- source:` lines that
  point at committed evidence; tools/lint_findings.py enforces it in CI
  (D-4). A finding cited outside its regime is a bug.
- An adversarial critic agent (.claude/agents/sideband-critic.md) reviews every
  experiment diff; its highest-value mode is recomputing each CI from the
  committed *.state.jsonl files with a fresh implementation. It found the
  errors the prose missed, including the standardization pathology behind
  F-22's inflated registered magnitudes.
  Dated note 2026-10-17: a recovered selection of its recompute scripts and
  round reports of the harness era is committed under
  docs/audits/critic-recovered/; its
  [README](docs/audits/critic-recovered/README.md) says what they are and
  are not (the reviewer's scratch, labelled recovered, not instruments) and
  what the archive's rule left behind.
- Registered text with an error gets a dated erratum, never a rewrite;
  post-hoc diagnostics are themselves registered with pinned labels and may
  price a result but never reclassify it.

Two further rules a reader will meet everywhere: every telemetry claim is
compared against the free-information baseline - what any speculative decoder
already has at the last verified position (D-5) - and policies are compared
at identical seeds with telemetry drawn from an isolated RNG stream (D-6).

## Quickstart

CPU only; Python >= 3.10 (tested with 3.11.9; CI uses 3.12). `make` is not
required - the Makefile targets are the raw commands below.

```
git clone https://github.com/Mike-Byrne-AI/specdec-sidechannels specdec-sidechannels
cd specdec-sidechannels/sideband
python -m venv .venv
# Linux/macOS: source .venv/bin/activate    Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"                                 # numpy, pytest and ruff
python -m pytest -q tests/test_specdec.py tests/test_stats.py     # 1-2 minute sanity subset
python -m pytest -q                                               # full suite, 775 tests in 53 files, all tracked (2026-10-17, python -m pytest --collect-only -q; tests/README.md)
python tools/lint_findings.py                                     # expected: lint_findings: OK (30 findings, all carry regime + tracked evidence) (2026-10-17)
python experiments/run_all.py --smoke                             # CI variant; writes results/smoke/ (gitignored)
```

The full suite took about 24 minutes in one pre-release run on a Windows 11
box (a one-off timing, not a committed number); on a torch-less `.[dev]` install the torch-gated tests
skip rather than fail (three previously unguarded tests in tests/test_probes.py
now carry the skip guard). A `Windows fatal exception: access violation`
banner from tests/test_outcome_head.py's subprocess is noise on Windows; the
test passes. The full experiment run `python experiments/run_all.py` (no
flag) REWRITES the committed results/e0*.json evidence and is meant to be run
deliberately; its docstring estimates 10-15 min CPU. GPU adapters need
`pip install -e ".[real]"` and the port checklist near the end of
docs/BLUEPRINT.md; `.[analysis]` adds scipy/scikit-learn for
tools/build_concept_groups.py only.

Recompute F-22's registered delta_free from the committed state file (run from
the repo root; both lines print the same triple, bit-for-bit):

```python
import json, numpy as np
from sideband.stats import paired_ratio_delta_ci
rows=[json.loads(l) for l in open('results/real/oq16_stage_r.json.state.jsonl')][1:]  # keep FILE ORDER
A=lambda a:[r for r in rows if r['arm']==a and r['variant']=='live']
f,t=A('free'),A('tel')
print(paired_ratio_delta_ci([r['sse'] for r in f],[r['count'] for r in f],[r['sse'] for r in t],[r['count'] for r in t],n_boot=2000,seed=0))
print(json.load(open('results/real/oq16_stage_r.json'))['delta_free']['live'])
# (0.204983722587619, 0.15369761574819202, 0.28816195871219474)  = F-22's +0.204984 [+0.153698, +0.288162]
```

Row order matters: the point estimate is order-invariant, the bootstrap CI is
not. The same recipe (paired_ratio_delta_ci or paired_cluster_delta_ci over a
run's state file or summary per_prompt_stats) reproduces F-15, F-17, F-19,
F-20, F-21 and the DR-1..DR-4 readouts without a GPU.

## Repo map

```
src/sideband/          numpy core (torch-free): specdec (the exact verifier, single source of
                       truth, D-3), dists, sketch, buckets, synthetic, sidecar, steering,
                       pipeline, stats (Clopper-Pearson, cluster bootstraps, paired ratio delta),
                       glue, harvest, probes, scheduler, outcome_head, recon, provenance
src/sideband/real/     GPU adapters (torch imported lazily): hf_specdec (target/draft loop,
                       audit, K-3/Stage-A instrument), bucketize_vocab, harvest_freq,
                       shadow_telemetry (S1), moe_telemetry (S3), shadow_kv_telemetry (S2,
                       unrun), fidelity riders, k3_live, k3_tap_rider, steer_inject (Stage A)
tools/                 43 drivers at the top level (2026-10-17, ls tools/*.py): run_probes, run_posthoc_topic,
                       run_k3_arms, k3_threshold_search, train_outcome_head, train_recon,
                       train_inject, export_probe_weights, analyze_*, verify_phase0a,
                       lint_findings, e6_gate (F-19/F-21 gate recompute from committed
                       summaries), ha_identity_check (F-23), run_fullfree / run_fullfree_twin /
                       run_fullfree_coarse* (F-24/F-25), run_fullfree_oracle (the unfrozen
                       OQ-19 draft, unrun), run_prefetch_readouts / run_prefetch_bigram /
                       run_prefetch_strat / run_prefetch_r2 / run_prefetch_horizon (F-26, its rungs and the horizon read),
                       landing_text (the landing-text kit), ...
tests/                 53 test files, 775 tests, all tracked (2026-10-17, python -m pytest --collect-only -q);
                       tests/README.md says what each kind of file checks; the load-bearing part (exactness by enumeration,
                       gradients, sha-binding refusals, byte-identity of instrument paths)
experiments/           e01-e07 synthetic experiments + run_all; probes/ holds uncitable explorations
data/                  five committed prompt sets (210/210/30/210/210) and their generators
results/               committed evidence: 517 files, 264,906,304 bytes (about 265 MB; 2026-10-10), almost all
                       under results/real/ (run summaries, metas, stats, rejection logs, label
                       spaces, and the registered *.state.jsonl recompute surfaces)
docs/                  BLUEPRINT (+ BLUEPRINT_INDEX), WHY_THIS_DIES, ECONOMICS, PRIOR_ART,
                       ECOSYSTEM, FUTURE_IDEAS, IDEAS, plus METHOD, GLOSSARY, FINDINGS_INDEX, [withheld: FUTURE_IDEAS, IDEAS not in this repository; see WITHHELD.md]
                       REPRODUCE, DATA, THIRD_PARTY, REPORT, RELEASE_NOTES, LESSONS,
                       audits/ (the 2026-10-15 image audit's report and recompute scripts)
```

Not in the repo (gitignored, sha256-bound in the committed metas and
summaries): 3,894 raw .npz files, 13,369,799,824 bytes (about 13.4 GB) - the
24 harvest shards (10,131,081,744 bytes), 2,160 K-3 byproduct arrays
(1,797,516,744) and 1,710 OQ-15C byproduct arrays (1,441,201,336), as of
2026-09-05; on 2026-10-19 the twelve seed-6 and replay folders add 1,281 files
and 1,086,399,860 bytes, 5,175 files and 14,456,199,684 bytes in all
(docs/DATA.md, the deposit section). Tools that
consume them (train_recon, train_outcome_head, summarize_harvest, ...) refuse
to run without them; the committed *.state.jsonl files are the intended CPU
recompute surface. Stage-A artifacts (oq16_recon_weights.npz, oq16_inject_*.pt)
are declared in .gitignore and do not exist. Smoke outputs go to
results/smoke/ (gitignored).

Evidence layout, so that nothing is mistaken for corruption: every GPU run
under results/real/ is a quartet - <run>.summary.json (the numbers and the
sha256 map of its raw arrays), <run>.stats.jsonl (one line per prompt),
<run>.meta.json (arguments, git stamp, model ids) and <run>.gen.jsonl
(generated token ids) - plus a gitignored <run>.jsonl.byproduct/ directory
of per-prompt npz arrays. The 21 <run>.jsonl files of the K-3 and OQ-15C
arms are zero bytes by design: tools/run_k3_arms.py writes an empty marker
("jsonl reserved; stats carry data"). Registered CPU analyses write a
<name>.json summary, a <name>.json.meta.json and a <name>.json.state.jsonl
(the per-cluster recompute surface). .gitattributes marks results/** -text
so checkouts are byte-exact, because the sha chains would break otherwise.
results/summary.json is a hand-assembled timing note from the v0.2.0
assembly, not tool output, and the only file under results/ that is.

## How to read the logs

- FINDINGS.md - 27 entries, F-0..F-26, each with regime and source lines.
  (Dated note 2026-10-12: 29 entries, F-0..F-28, the lint's count. 2026-10-17:
  30 entries, F-0..F-29, `python tools/lint_findings.py`.)
  Entries are long; read docs/FINDINGS_INDEX.md first and use the entry as
  the reference. Numbers "as registered" and their dated errata sit
  side by side on purpose.
- DECISIONS.md - D-1..D-11, the standing rules (D-1 input-dependent telemetry
  only; D-3 one verifier; D-5 free baseline mandatory; D-9 analytic
  per-position acceptance is the headline, wall-clock banned).
- OPEN_QUESTIONS.md - OQ-1..OQ-20, with dated status tails; OQ-16 was closed
  by the 2026-09-05 dated erratum (F-23). No lane is live.
- docs/BLUEPRINT.md - 13,842 lines on 2026-10-10 (10,692 on 2026-10-04, 9,280 on 2026-10-03, 7,977 on 2026-10-02, 6,905 on 2026-10-01, 4,020 at the 2026-09-05
  cut) of dated registrations, amendments,
  outcomes and errata in chronological order. It is the plan of record and
  the audit trail, not an introduction: start from docs/REPORT.md and
  docs/FINDINGS_INDEX.md, then follow their pointers into it;
  docs/BLUEPRINT_INDEX.md lists its registration and outcome blocks in order.
- docs/WHY_THIS_DIES.md (K-1..K-7 with outcomes) and docs/ECONOMICS.md (the
  +0.062 tokens/call bar, pinned 2026-09-01 before any conversion run, and
  the unmeasured device economics K-5/K-6).
- docs/GLOSSARY.md - every house term (anchor, offset, glue bucket, FREETOK,
  void semantics, stale-target control, ...).

## Provenance and privacy notes

- Dated note 2026-10-16: three sentences of this file (the overview's last
  sentence, the setup paragraph's last sentence and the first bullet of the
  "not measured" list) said that the HF adapter recomputed prefixes or that no
  wall-clock number exists. They were corrected in place after the 2026-10-15
  image audit (docs/audits/2026-10-15-image-audit/README.md, section B item
  1): the adapter has cropped KV caches by default since b1dae57 (2026-08-29),
  logged runtimes are provenance, and the wall-clock ban stands on the
  absence of a benchmark harness (DECISIONS.md D-9, dated note 2026-10-16).
- Run metas record the operator's absolute invocation paths (80 committed
  results/real files at HEAD on 2026-10-16, 30 when this was written on 2026-09-05;
  keys such as buckets16/32/64/512, glue16, probe_weights, val_run, and in the
  later instruments args, label_space, companion_files_filled). Those key values
  are inert provenance: no tool dereferences them, and a public clone runs
  without those paths existing. They are not edited because results/ is
  committed evidence and several of these files are sha256-bound by other
  files. The shared guard sideband.provenance.redact_args keeps
  credential-shaped arguments out of every future meta; it does not relativize
  paths, so new runs will still record the operator's paths. Dated note
  2026-10-16: three recorded path kinds are read back (the Phase-3 companions
  as basenames by the frozen reader-lens tool, the rider file by one test, a
  relative backslash harvest_dir by one prefetch test), which is why six tests
  were red on a Linux clone until lane A (c41f9f1) handled them test-side;
  docs/RELEASE_NOTES.md 3.1 lists them.
- Registration before data is attested by commit order in the private history
  where the registration and the run landed in separate commits (most of the
  record; the exceptions are disclosed where they occur, such as the R1
  recalibration amendment and its rerun sharing commit e6b22c9, dated erratum
  in docs/BLUEPRINT.md; the commit messages ship as docs/COMMIT_LOG.md in the
  public cut) and by the sha-bound state files; a -dirty meta attests the
  in-flight text rather than proving it (docs/REPORT.md); the public
  repository is fresh-history, so a reader cannot verify the order from git
  alone (dated note 2026-10-16).
- HANDOFF.md is an operator-local session log. Registered text
  (docs/BLUEPRINT.md, FINDINGS.md F-22) cites it as attestation context; it
  is intentionally unpublished and gitignored.
- Many metas carry a `-dirty` git stamp. What the dirt was, and where a
  clean-worktree rerun backs the run, is explained in docs/RELEASE_NOTES.md.
- results/real/*.gen.jsonl files contain generated token ids from the Llama
  and OLMoE models named above; no decoded text is shipped. Third-party model
  terms are the owner's check (docs/THIRD_PARTY.md).

## Prior art positioning

Names and ids below are those in docs/PRIOR_ART.md, which asks that arXiv ids
be re-verified before external citation.

- SD^2, "Steering Pretrained Drafters during Speculative Decoding" (arXiv
  2511.09844, AAAI 2026): same Llama pair, drafter steered from verifier
  hidden states; the ceiling this repo measures against. Per PRIOR_ART's
  dated correction (2026-09-04), its "+35% / +22%" are cross-pair maxima; for
  this pair, Table 1 gives block efficiency 4.44 -> 4.79 under sampling at
  k = 8 (+0.35 tokens per block, speedup 1.07), unquantized, batch 12 - a
  cross-gamma prior for our gamma 4 / NF4 / batch-1 regime, not a bar.
- EAGLE-3 (Li et al.): multi-layer target features as draft input; the far
  ceiling of target-informed drafting, not observability-constrained.
- SpecDec++: adaptive block length from an acceptance-prediction head; the
  nearest relative of the K-3 scheduler and the OQ-15 head, and the class of
  the draft-confidence comparator arm both verdicts included.
- Leviathan et al. 2023 / Chen et al. 2023: the rejection scheme
  src/sideband/specdec.py implements verbatim; losslessness is theirs.
- "I Know What You Said" (arXiv 2505.06738) and "Spill The Beans" (arXiv
  2505.00817): access patterns leak token-level information as an attack;
  this repo is the constructive dual. SP-MoE (arXiv 2510.10302) predicts
  target routing from the draft for prefetching - the reverse arrow of F-17.
  (Measured on this repo's OLMoE harvest as OQ-9 stage 1, 2026-09-15, F-26:
  routing history plus the free bonus token covers 0.91 of the next
  forward's expert sets at 16 of 64 resident, against 0.52 for a recency
  cache and 0.81 for a one-token table alone; a hit-rate count, not a
  speedup; the free previous token is not yet in the baseline; prior art
  occupies the cell.) (2026-10-01: the free previous token entered the baseline at equal dims —
  label SURVIVES at this encoding; the address block over an equal-dims free
  bigram block +0.0609 / +0.0659 (SIGNAL / SIGNAL), the
  address stream over the free bigram +0.0661 / +0.0705 (SIGNAL / SIGNAL); below the
  floor at B = 32; the material part of the margin sits on positions whose
  token key the train tables never saw (covered-position D_eq below the floor
  in an unregistered diagnostic), so it is read neither as context nor as
  support for the sideband premise; see F-26's dated status line.)
  (2026-10-02, STRATIFIED COVERAGE READ of the twin's margin, both runs from
  the clean freeze commit fea2431; label FALLBACK-LOCATED / PT-SURVIVES on
  both harvests, REPRODUCE EXACT, both gates straddling the floor: on the
  covered positions (0.9013 / 0.8582) D_eq +0.0463 / +0.0481, CI-positive
  below the floor with the floor inside the CI; on the unseen-key positions
  (0.0987 / 0.1418) +0.1940 / +0.1741 (SIGNAL); with p_t's stored summaries
  in both arms D_eq^PT +0.0532 / +0.0565 and D_add^PT +0.0583 / +0.0609
  (SIGNAL, the equal-dims CI containing the floor); the caveat is neither
  retired nor confirmed at this power — its location is indicated, not
  settled; the sparse covered keys (one to four train occurrences) read at
  or above the floor while the well-covered keys do not; next rung R2, a
  free baseline whose encoding handles unseen and sparse keys; see F-26's
  second dated status line and the block's OUTCOME.)
  (2026-10-03, GENERALISING FREE BASELINE (R2), both runs from the clean
  freeze commit 2fe5926; label R2-FALLBACK-SURVIVES / H-ABSORBS on both
  harvests, REPRODUCE EXACT, no straddle on the unseen-key gate or either Q2
  reading, k = 128 interior: against replay-prior smoothed tables the
  address block still adds +0.0732 [+0.0623, +0.0834] / +0.0662 [+0.0559,
  +0.0773] on the unseen-key positions (SIGNAL) while the encoding recovers
  +0.1971 [+0.1697, +0.2266] / +0.1822 [+0.1557, +0.2167] of hit rate there
  — the located margin is NOT shown to be table sparsity at this encoding;
  the pooled Q1 reading +0.0493 [+0.0425, +0.0577] / +0.0506 [+0.0433,
  +0.0594] reads NOT-SHOWN / SIGNAL by the rule with the CI95 straddling the
  floor on both — the one label-bearing reading on which the harvests
  differ, said in words; with the forward's stored final-norm state in the
  free arm the address block adds +0.0111 [+0.0078, +0.0150] / +0.0106
  [+0.0068, +0.0153] and the address stream +0.0172 [+0.0139, +0.0210] /
  +0.0162 [+0.0126, +0.0206], both NOT-SHOWN — no material margin (at or
  above +0.05) of the address block over the equal-dims free block, nor of
  the address stream over the free bigram plus the hidden block, is shown
  (both readings CI-positive below the floor) at this reader, and STAGE 2's
  ADDRESS-BEYOND-FREE MOTIVATION IS STRUCK by the pinned condition (beside
  the strike, as pinned: D_add^H on the unseen-key positions +0.0399
  [+0.0279, +0.0514] / +0.0286 [+0.0195, +0.0386] (NOT-SHOWN; the primary's
  CI95 containing the floor); PREFETCH-HEADROOM stands; K-6 stays UNTESTED).
  The free-baseline ladder under F-26 is closed as pre-committed; no further
  rung on this margin. See F-26's third dated status line and the block's
  OUTCOME.)
  (2026-10-04, HORIZON READ at the R2 encoding, both runs from the clean
  tree at 5e0e2a9, frozen at b41d3f3; label LEAD-TIME-ABSORBED on both
  harvests, REPRODUCE EXACT, no straddle, guard or free_h grid edge at any
  label horizon: with the forward's final-norm state and two tokens'
  smoothed routing profiles in the free arm the address block over the
  equal-dims free block reads horizon 2 +0.0034 [-0.0008, +0.0084] / +0.0024
  [-0.0021, +0.0080]; horizon 3 +0.0016 [-0.0032, +0.0070] / +0.0002
  [-0.0052, +0.0063]; horizon 4 -0.0002 [-0.0052, +0.0056] / -0.0023
  [-0.0075, +0.0039] and the address stream over the free arm horizon 2
  +0.0178 [+0.0138, +0.0223] / +0.0153 [+0.0113, +0.0203]; horizon 3 +0.0173
  [+0.0129, +0.0223] / +0.0135 [+0.0093, +0.0187]; horizon 4 +0.0149
  [+0.0105, +0.0198] / +0.0104 [+0.0062, +0.0154] (primary / replication;
  every one of the six label readings NOT-SHOWN by the rule) — no material
  margin (at or above +0.05) is shown at horizon 2, 3 or 4, as at horizon 1
  (R2); the stage-2 strike stands, PREFETCH-HEADROOM stands, K-6 stays
  UNTESTED (a lead-time datum in forwards, not latency), and OQ-9's prefetch
  half closes at this reader (beside the closure, as pinned, the unseen-key
  readings: horizon 2: D_eq^H +0.0333 [+0.0173, +0.0486] / +0.0172 [+0.0067,
  +0.0272] (NOT-SHOWN), D_add^H +0.0455 [+0.0318, +0.0582] / +0.0282
  [+0.0197, +0.0368] (NOT-SHOWN; the primary's CI95 containing the floor);
  horizon 3: D_eq^H +0.0433 [+0.0188, +0.0683] / +0.0231 [+0.0057, +0.0412]
  (NOT-SHOWN; the primary's CI95 containing the floor), D_add^H +0.0499
  [+0.0290, +0.0710] / +0.0309 [+0.0175, +0.0449] (NOT-SHOWN; the primary's
  CI95 containing the floor); horizon 4: D_eq^H +0.0431 [+0.0164, +0.0689] /
  +0.0196 [+0.0042, +0.0373] (NOT-SHOWN; the primary's CI95 containing the
  floor), D_add^H +0.0483 [+0.0264, +0.0693] / +0.0254 [+0.0134, +0.0390]
  (NOT-SHOWN; the primary's CI95 containing the floor)). See F-26's fourth
  dated status line and the block's OUTCOME.)

## What's next

The lane's registrations leave the owner these decisions (docs/REPORT.md
section 8 carries them in full):

- Close on F-23. The record is complete as it stands: existence at two
  sources, two conversion nulls, one reconstruction pass whose target proved
  free, every number with a CI and a critic recompute.
  Dated note 2026-10-12: this list predates F-24 (2026-09-06); F-24 to
  F-28 landed after it. "Existence at two sources" is now read under the
  dated note beneath the one-line reading above (K-2 FIRED at L1 and L2
  at the registered reader, the L2 reads under the rider amendment the
  existence row's F-25 note carries, L3 OPEN at both sources, F-28's
  final word K-2-ISOLATED at S3).
- Register and run the free-actuator readout: vanilla versus the true anchor
  state injected through the frozen rank-512 adapter, seed 4 on
  data/prompts_oq16_verdict.jsonl, the frozen bar and budget guard. A win
  there would be an SD^2 configuration result on this box, not a sideband
  result, and it needs its own dated registration before anything runs.
- Authorize, in those words, an exception to the fold-back hard stop for the
  anticipatory target (the verifier's state at future anchors). Nothing is
  registered for it and no evidence bears on it beyond the F-15/F-17
  existence margins.
- Pick a LICENSE and a release tag, and fill CITATION.cff
  (docs/RELEASE_NOTES.md).
  Dated note 2026-10-17: MIT was chosen on 2026-10-12; the licence sentence
  below and CITATION.cff are filled at export.

## License, version, how this was built

License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).
CITATION.cff at the repository root is the citation; this folder's CITATION.cff describes the folder.
Version 0.3.0 (pyproject.toml, src/sideband/__init__.py).

Committed between 2026-08-29 and 2026-09-05 (git log; the verifier-exactness
and synthetic-world findings F-0..F-9 are dated 2026-08-28) by a human who set the
questions, the kill criteria, the gates and every launch, void and close
decision; an AI coding assistant (Claude Code) that built the instruments,
ran the analyses and drafted registrations and findings; and a second,
adversarial agent (.claude/agents/sideband-critic.md) that recomputed results
from the committed state files and blocked commits until its objections were
dispositioned. The human arbitrated. At 8542ef5, 65 of the 70 commits carry a
Co-Authored-By trailer naming the assistant.

Dated note 2026-10-17: the history now runs to 2026-10-17 (`git log
--date=short`; CHANGELOG.md lists the arcs). The roles above are restated
in plain words at the top of this page, and the critic's recovered rounds
are under docs/audits/critic-recovered/.

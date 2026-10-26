# Open Questions

## OQ-1 — Does real telemetry carry anything beyond the last verified p? — ANSWERED YES at source S1 (F-15, 2026-08-31); S2/S3 open
(Dated note 2026-09-05: this header's "S2/S3 open" is superseded - S3 was ANSWERED YES by F-17 (2026-09-01), replicated, with F-18's topic control; S2 (KV pages) was never run. The header is registered text and is left as written.)
THE existence question. The synthetic world cannot answer it (F-6). Protocol
(Phase 3): train three causal probes predicting the target's next-token
bucket at offsets 1..gamma — features (a) last verified p only, (b) telemetry
slots only, (c) both. Telemetry earns its existence iff (c) > (a) at offsets
>= 2 by a margin that survives seeds. SD^2 shows the information exists in
hidden states; the bet is that it survives projection to an address set.
Harvest protocol feeding this (sources, block-start alignment, pinned
prompt-level split, volume rule): BLUEPRINT Phase 2, registered 2026-08-30.
The h_a hidden-state reference feature logged there gives OQ-6's
DENOMINATOR a direct measurement path (probe on h_a vs probe on slots,
same anchors); h_a is not an information bound on mid-layer taps at
offsets >= 2 — see the registration's wording.
Probe protocol: BLUEPRINT Phase 3 (registered 2026-08-30) — label spaces
L1 concept_k16 / L2 concept_k512 / L3 concept_groups_v1 (transition-
coherent groupings of the k512 concept buckets, train-split-fit; the
"buckets as conceptual ideas" axis, user-proposed), decision rule with a
+0.005 materiality floor, fidelity/label-shuffle/split riders, S1 harvest
audited pre-registration (results/real/harvest_audit.json: contamination
0.8%, majority floors 0.591/0.413).
RESOLVED at S1 (2026-08-31, F-15): the original grid returned EXISTENCE
provisional (10/12 offset-≥2 triples fired, all 12 CI-positive) and the
registered replication on fresh seeds 8..11 CONFIRMED it — the pinned
L1/off2/linear triple re-fired (+0.0141 [+0.0081, +0.0203], all seeds
positive) and all eight off2/off3 triples re-fired (8/8; off4 did not
re-establish — the demonstrated horizon is 2–3 tokens). The shape held
on both datasets: free info collapses to the majority floor by offset 3,
telemetry-alone stays CI-positive over the full 657-dim free baseline,
and (c−a) is CI-negative at free-saturated offset 1 (the internal
control against index-shift leaks). Riders R1/R2/R3 passed on both
harvests; critic recomputed both decisions from the state files
bit-exact. Evidence: probes_s1.json + probes_s1_replication.json (+
state files). WHAT REMAINS OPEN under this OQ: (i) S2/S3 — the
per-source scope note means the address-stream story is still untested;
(ii) mechanism — the TOPIC-STATE half is now REJECTED (F-16, post-hoc
P1, 2026-08-31: prefix concept-histograms predict ~nothing, add
~nothing to free, and the tap margin passes the equal-dims noise
control intact on both harvests); residuals: prompt-token-augmented
prefix control and richer-than-histogram prefix families (each a new
registration), plus the calibration pass (probelab port) still queued;
(iii) conversion to acceptance is K-3/Phase 4, not this question.

## OQ-2 — Real cross-bucket rejection fraction — ANSWERED (F-10, 2026-08-29)
Synthetic said 76–89% (F-2). Real answer: 78–86% residual mass depending on
k (0.778/0.812/0.863 at k=256/512/1024, tight prompt-cluster CIs), sampled
fraction flat across offsets, NF4 and bf16 arms agreeing. K-1 did not fire —
see F-10 for the regime. Remaining sub-questions: glue-involved share of the
crossings (OQ-4 — "bucket-level" is not yet "concept-level"), and
sensitivity to a non-k-means bucketization ([withheld: a private repository's seeded-basket bucketizer (plan section 3); see WITHHELD.md]) as a robustness check before external writeups.

## OQ-3 — Real bucket-level persistence
F-4's rule (hold a bucket only if run length >> gamma) needs the real
autocorrelation of target token buckets. Cheap: compute from any generation
log once buckets.json exists. Sets viable gamma and whether per-offset decay
of the boost is needed.

## OQ-4 — Glue-bucket identification in real k-means space — ANSWERED (F-11, 2026-08-30)
D-7's real analog. Candidate: buckets holding most of the top-100 frequency
tokens are glue; exclude them from prediction and gate comparisons. Validate
by re-running the audit summary with and without exclusion.
ANSWER: glue is concentrated (2/2/4 buckets at k=256/512/1024, 80% of
top-100 frequency mass, textbook function tokens) and identification works;
concept-level share after exclusion = 0.56/0.61/0.67 by k (token and mass
estimators concordant), so the F-10 reopen trigger does not fire. BUT the
identification being clean did not rescue the gate: the disagreement gate
stays open ~94% of the time at k=512 (F-12) — the problem moved from "can
glue be found" (yes) to "is bucket-argmax disagreement informative at fine
k" (no; OQ-12).

## OQ-5 — Hardware sideband width and sidecar latency budget
e05's shape (F-5) says a few hundred slots suffice IN-SIM and that gating
rescues narrow sidebands. Real: how many (layer, expert) or slot features
does the probe need, and does sidecar inference fit inside the draft loop's
latency budget? The premise dies on economics, not accuracy, if a wide
sideband or a slow sidecar is required.

## OQ-6 — What fraction of SD^2 survives the observability constraint?
SD^2 reports +35% accepted tokens steering the drafter with verifier hidden
states. Our ceiling is at or below that. The mature framing of this project
is: how much of that gain survives when the feature vector is a hash sketch
of the access pattern instead of the hidden state?
(Dated note 2026-09-05: at the reconstruction layer this question closed by
identity, F-23 - the anchor state SD^2 would inject follows exactly from the
verifier's own next-token distribution at that position, so no part of it
needs the sideband; the acceptance-level fraction was never measured. The
"+35%" above is a cross-pair maximum per docs/PRIOR_ART.md's dated
correction of 2026-09-04; this pair's Table-1 number is block efficiency
4.44 -> 4.79 at k = 8, unquantized.)

## OQ-7 — Verified archives: the spec-decode trace as a codec
Compress with the target, store accept-bits + corrections entropy-coded under
the DRAFT, decompress with the draft alone — byte-exact, which hard-requires
a deterministic decode runtime (the determinism-layer dependency; and its
cost model's surviving regime — pack as a free byproduct of inference — is
exactly what serving-time spec decoding provides). Decode-time rejection rate
doubles as attestation: wrong/drifted decoder => acceptance collapses.
e07's v0 ledger sets the constraint: free-causal steering already saves
~0.10 bits/token at zero cost, and the TOTAL break-even hint budget is
~0.16 bits/token in this regime — so hint channels must be event-driven or
sub-bit (topic-shift flags, rejection-anticipating hints), never dense
per-position codes (F-9). REQUIRED before any claim: prior-art pass against
the LLM arithmetic-coding lineage (LLMZip, ts_zip) — the candidate novelty
is the asymmetric-decode + hint-rate-tradeoff + attestation bundle.

(Dated note 2026-10-11, harvested from the parked sibling lockstep: the
dependency named in the first sentence was never built, lockstep F-19 finding
no lsp1 profile in its source; for amber's archives on one box, an fp32 replay
pin was enough, with no runtime (docs/DECODE_CONTRACTS.md). The parenthesis's
claim that serving-time spec decoding provides lockstep's surviving regime was
never measured. The only pack rate in lockstep's record is a separately run
bf16, batch-1 draft-scoring pass at 0.0437 MB/s (9,233 positions/s times
4.7277 bytes/token, amber's errata row E10), 460x short of the 20.1 MB/s
break-even of lockstep F-8 (lockstep F-17); "pack as a free byproduct" would
hold only if the serving draft pass were itself the archive's encode pass, a
premise lockstep never measured. This note leaves OQ-7's status to the owner.)

(Dated note 2026-10-15: status TRANSFERRED to amber/, the operator's call PC-6 of
2026-10-14 (section 13 of the public-cut plan of record, a document the public cut
withholds; sideband/WITHHELD.md in the cut says why). What transfers is the
question: amber is where the archive build moved, and amber is parked (docs/BLUEPRINT.md's
T-A dated note of 2026-10-11, under the v0.2.0 addendum heading). F-9's constraint stands
as sideband's own result; no amber result is claimed here, and the
amber survey adds the pointer to amber's own findings. This answers the 2026-10-11
note's last sentence.)

## OQ-8 — KV-page telemetry
The alternate Phase-2 track with a hardware premise that already exists (KV
offloading / paged attention). Telemetry = top-k attended page ids per layer
(real/shadow_kv_telemetry.py harvests it via eager attention; the honest
production tap is the paging layer's block tables). Questions: is the page
stream more predictive than the weight-access stream; does an ATTENTION
TRANSPLANT mechanism (bias draft attention toward the target's hot pages)
beat logit-space steering; what page size preserves signal? Nearest relative
TriForce (see PRIOR_ART) — ours is the page-ids-only, separate-draft cousin.

## OQ-9 — Bidirectional sidecar
SP-MoE runs draft->target-experts for prefetching; we run target->draft for
steering. Does ONE representation on the sideband serve both heads (steer +
prefetch)? Cheap first test: add a prefetch-hit-rate metric to the existing
synthetic sidecar. If yes, the hardware story amortizes one sideband twice
and Phase 5's economics improve.
(2026-09-06 dated note: the cheapest first step is now docs/
FUTURE_IDEAS.md P1 — cross-token expert reuse and cross-layer [withheld: FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
routing predictability on the existing S3 OLMoE harvest, CPU-only,
no model forward; unregistered, idea-tier.)

(2026-09-14 dated note: STAGE 1 REGISTERED — "OQ-9 STAGE-1 PREFETCH
READOUTS REGISTRATION" in docs/BLUEPRINT.md, written before any readout
ran: P1 (i)-(iii) of docs/FUTURE_IDEAS.md on the committed S3 harvests [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
(primary = verdict, replication = confirmatory), CPU only, no model
forward, as RE-INDEXED in the critic round (S[t+1] is the routing of the
forward the free bonus token tokens[t] feeds; DRAFT at horizon 2 with the
true tokens[t+1] as the perfect draft), plus the free input-token arms
FREE_TOK / HISTORY_TOK / FREE_TABLE and the ADDRESS-BEYOND-TOKEN reading
(the D-5 analogue for prefetch, the one reading that speaks to this
question), plus a REPORTED-ONLY front-loading curve (iv) on the timing
edge; four readings HISTORY / ADDRESS-BEYOND-TOKEN / INTRA-FORWARD /
DRAFT at budget 16, the stage labels CACHE-SUFFICIENT /
PREFETCH-HEADROOM / PREFETCH-NOT-SHOWN / INCOMPLETE, and a sideband
sentence that follows ADDRESS-BEYOND-TOKEN alone; NON-CRITERION for
every existing finding; prior art pinned as occupied (the value is the
measurement on this model, not novelty).
The STEER HALF of this question is PARKED by this note: no actuator in
the record converts (F-12..F-14, F-19, F-21, F-23), so "one
representation serves both" cannot be posed until one does. Instrument
tools/run_prefetch_readouts.py; evidence results/real/prefetch_s3.json,
prefetch_s3_r.json + state files.)

(2026-09-15 OUTCOME, F-26: stage 1 LANDED on both S3 harvests from a
clean tree at c4c4511; stage label PREFETCH-HEADROOM on the primary, the
replication (a seed replication on the same prompts) agrees on every
label. At B = 16 of 64 experts per gate, hit rate on the next forward's
expert sets: recency cache 0.5197 / 0.5155, free one-token table 0.8111
/ 0.8036, address-only history 0.8064 / 0.8056, addresses ++ token
0.9143 / 0.9108; ADDRESS-BEYOND-TOKEN +0.1032 [+0.0926, +0.1146] /
+0.1072 [+0.0952, +0.1206] SIGNAL, so the sideband sentence in its pinned
words: "the address stream adds a material margin over the free input
token at this reader" — SCOPED by the critic's blocking objection: the
free arm is a ONE-TOKEN table, the equally free previous token is not in
it, and gate 0 routes primarily on that previous token (per-gate margin
+0.221 / +0.224 there), so an unknown share of the +0.10 is free
token-history information; the equal-dims free-bigram twin is the unrun,
unregistered next rung (the critic predicts the margin falls to or below
the +0.05 floor). At B = 32 the same margin is +0.0405 / +0.0434, below
the floor. INTRA-FORWARD +0.4861 / +0.4816 (gate l from the earlier
gates of the same forward: 0.9115 / 0.9128 pooled against marginal
0.4236 / 0.4293); DRAFT (the true next token as the D-2 ceiling draft,
horizon 2) +0.1556 / +0.1545. Prediction: three clauses held in full,
three held on their label with a sub-clause missed high (the HISTORY
arm by +0.006, ADDRESS-BEYOND-TOKEN by +0.003 / +0.007) or partial; the
+0.15 surprise line not reached. Prior art occupies every cell, as pinned; K-5 / K-6 stay
unpriced; NON-CRITERION. The STEER half stays PARKED. Stage 2 (a real
draft partner for OLMoE) is a live OPTION under its own registration and
GPU authorization, not a plan of record. Full outcome: the OUTCOME
paragraph of the stage-1 block in docs/BLUEPRINT.md; F-26.)

(2026-10-03, a dated line under the stage-2 sentence above: the generalising
free baseline (R2) read H-ABSORBS on both harvests with no straddle and no
guard, so by the pinned condition stage 2's address-beyond-free motivation
is STRUCK — no material margin (at or above +0.05) of the address block over
the equal-dims free block, nor of the address stream over the free bigram
plus the hidden block, is shown (both readings CI-positive below the floor);
beside the strike, as pinned: D_add^H on the unseen-key positions +0.0399
[+0.0279, +0.0514] / +0.0286 [+0.0195, +0.0386] (NOT-SHOWN; the primary's
CI95 containing the floor); Q1's unseen-key survival is not a motivation for
it; the option stays open only under a motivation of its own. The full note
sits at the end of OQ-9.)

(2026-10-04, a dated line under the stage-2 sentence above: the horizon read
at the R2 encoding read LEAD-TIME-ABSORBED on both harvests with no
straddle, guard or free_h grid edge at any label horizon, so the strike
stands at horizons 2, 3 and 4 as at horizon 1 — no material margin (at or
above +0.05) of the address block over the equal-dims free block (horizon 2
+0.0034 [-0.0008, +0.0084] / +0.0024 [-0.0021, +0.0080]; horizon 3 +0.0016
[-0.0032, +0.0070] / +0.0002 [-0.0052, +0.0063]; horizon 4 -0.0002 [-0.0052,
+0.0056] / -0.0023 [-0.0075, +0.0039]) nor of the address stream over the
free arm (horizon 2 +0.0178 [+0.0138, +0.0223] / +0.0153 [+0.0113, +0.0203];
horizon 3 +0.0173 [+0.0129, +0.0223] / +0.0135 [+0.0093, +0.0187]; horizon 4
+0.0149 [+0.0105, +0.0198] / +0.0104 [+0.0062, +0.0154]) is shown (the six
readings NOT-SHOWN by the rule; beside the closure, as pinned, the
unseen-key readings sit in the closure note at the end of OQ-9: the
primary's unseen-key CI95 contains the floor on 5 of the six fallback label
cells, the replication's on none); the option stays open only under a
motivation of its own, which this record does not supply.)

(2026-10-01 dated note: FREE-BIGRAM TWIN REGISTERED — "OQ-9 STAGE-1
FREE-BIGRAM TWIN REGISTRATION" in docs/BLUEPRINT.md, a dated amendment to
the stage-1 block written before any readout of it ran: the critic's
blocking objection at the F-26 landing (the equally free previous token is
not in the one-token free arm; gate 0 routes on it) becomes a post-hoc
diagnostic on both S3 harvests — the previous token enters the free
baseline at EQUAL DIMS (TABLE_CUR(tokens[t]) ++ a 1024-dim free encoding of
tokens[t-1], the encoding selected on val between the target-aligned
previous-token table and the frozen table read at the previous token),
every arm re-trained on the bigram positions t >= 1 with the re-measured
ADDRESS-BEYOND-TOKEN as a precondition (within 0.01 of the committed
+0.1032 / +0.1072), the gate D_eq = history_tok - FREE_BIGRAM (the
critic's named readout) beside D_add = HISTORY_BIGRAM - FREE_BIGRAM (the
address stream over the free bigram), labels FREE-HISTORY / COMPLEMENTARY /
SURVIVES / READER-INCONSISTENT / REMEASURE-INVALID / INCOMPLETE, both
predictions pinned (the critic's: the margin drops to or below the floor,
driven by gate 0; the assistant's: D_eq +0.03..+0.08 straddling the floor,
D_add +0.05..+0.09 SIGNAL, COMPLEMENTARY most likely). NON-CRITERION: F-26's
mechanical labels stand; the one pinned consequence is a dated STATUS line
on the standing of F-26's sideband sentence. Instrument
tools/run_prefetch_bigram.py (imports the frozen stage-1 instrument and
refuses a modified one); evidence results/real/prefetch_bigram_s3.json,
prefetch_bigram_s3_r.json + state files.)

(2026-10-01 OUTCOME of the free-bigram twin: both runs landed from the clean freeze commit d55e62f; label SURVIVES on the primary, the replication AGREES on the label and on both readings (a SEED replication on the same prompts; the primary's label is the label). At B = 16, j = 1 on the bigram positions — re-measured ADDRESS-BEYOND-TOKEN +0.1033 / +0.1074 (precondition held both); FREE_BIGRAM 0.8534 / 0.8449 (encoding prev_table / prev_table) against free_tok 0.8110 / 0.8035 and history_tok 0.9143 / 0.9109; BIGRAM GAIN +0.0424 [+0.0407, +0.0441] / +0.0414 [+0.0398, +0.0430]; D_eq +0.0609 [+0.0514, +0.0712] / +0.0659 [+0.0547, +0.0788] (SIGNAL / SIGNAL); D_add +0.0661 [+0.0569, +0.0762] / +0.0705 [+0.0592, +0.0834] (SIGNAL / SIGNAL); at B = 32 D_eq +0.0261 / +0.0287 and D_add +0.0275 / +0.0300, CI-positive below the floor (NOT-SHOWN); the free previous token accounts for 0.4104 / 0.3858 of the re-measured margin (point ratios); gate 0 is the largest per-gate gain on both (contribution 0.0138 / 0.0135 of the pooled gain). Pinned sentence: "the address block adds a material margin over an equal-dims free bigram block and the address stream adds a material margin over the free bigram at this reader (B = 16, j = 1)". the address block adds +0.0609 [+0.0514, +0.0712] over an equal-dims free bigram block and +0.0661 [+0.0569, +0.0762] over the free bigram at this reader; the critic's bigram objection is answered at THIS ENCODING (two additive 1024-dim train tables), not for previous-token information in general — with the coverage caveat: the material part of the surviving margin sits on positions whose token key the train tables never saw (covered-position D_eq +0.0454 / +0.0472 on val in an unregistered diagnostic, below the floor; D_eq at or above the floor on 16 / 17 of 30 test prompts); the diagnostic locates the margin, not its mechanism, so the label holds at THIS ENCODING and F-26's 'not context, not support for the sideband premise' stands; the stratified test-split read is the next rung; the pair-keyed table named at registration has worse coverage and is not the next rung. Both pinned modal predictions put D_eq below material and it read SIGNAL (the critic's clause FAILED, the assistant's modal label MISSED, the named alternative occurred). NON-CRITERION; K-5 / K-6 stay UNTESTED; D_add is never read as context. Full outcome: the amendment block's OUTCOME paragraph in docs/BLUEPRINT.md; F-26's dated status line.)

(2026-10-01 dated note: STRATIFIED COVERAGE READ REGISTERED — "OQ-9 STAGE-1
STRATIFIED COVERAGE READ REGISTRATION" in docs/BLUEPRINT.md, a dated
amendment to the twin block written before any readout of it ran; the
next rung the twin's OUTCOME named: D_eq on the TEST bigram positions
split by train-table coverage (COVERED / CUR-UNSEEN / PREV-UNSEEN /
BOTH-UNSEEN) at the twin's selected lambdas, with a free arm of the
forward's stored p_t summaries (mass16 ++ mass64 ++ entropy / ln V, 81
dims) beside it; precondition REPRODUCE (the stratified rows sum to the
twin's committed state rows); Q1 labels COVERED-MATERIAL /
FALLBACK-LOCATED / UNLOCATED on D_eq over covered against unseen-key
positions (covered split by train occurrences, reported), Q2 labels
PT-SURVIVES / PT-COMPLEMENTARY / PT-ABSORBS / PT-INCONSISTENT on the
equal-dims and union readouts with the p_t block in both arms; the
assistant's prediction pinned at registration (FALLBACK-LOCATED /
PT-SURVIVES modal, both gates near the floor) and the critic's recorded in
the design round, both before the freeze; floor straddles pinned to a
"not settled at this power" sentence.
NON-CRITERION: F-26's labels and the twin's SURVIVES stand; the one
pinned consequence is a dated STATUS line under F-26 on the standing of
the coverage caveat. Instrument tools/run_prefetch_strat.py (imports the
frozen twin and refuses a modified one); evidence
results/real/prefetch_strat_s3.json, prefetch_strat_s3_r.json + state
files.)

(2026-10-02, STRATIFIED COVERAGE READ of the twin's margin, both runs
from the clean freeze commit fea2431; label FALLBACK-LOCATED /
PT-SURVIVES on both harvests, REPRODUCE EXACT, both gates straddling the
floor: on the covered positions (0.9013 / 0.8582) D_eq +0.0463 /
+0.0481, CI-positive below the floor with the floor inside the CI; on
the unseen-key positions (0.0987 / 0.1418) +0.1940 / +0.1741 (SIGNAL);
with p_t's stored summaries in both arms D_eq^PT +0.0532 / +0.0565 and
D_add^PT +0.0583 / +0.0609 (SIGNAL, the equal-dims CI containing the
floor); the caveat is neither retired nor confirmed at this power — its
location is indicated, not settled; the sparse covered keys (one to four
train occurrences) read at or above the floor while the well-covered
keys do not; next rung R2, a free baseline whose encoding handles unseen
and sparse keys; see F-26's second dated status line and the block's
OUTCOME.)

(2026-10-02 dated note: GENERALISING FREE BASELINE (R2) REGISTERED — "OQ-9
STAGE-1 GENERALISING FREE BASELINE REGISTRATION (R2)" in docs/BLUEPRINT.md,
a dated amendment to the stratified-read block written before any readout
of it ran; the next rung that read's OUTCOME named: the twin's free tables
replaced by replay-prior smoothed count tables (the model's own routers
applied to the token's normalised input embedding as the Dirichlet prior
of each key's count row, one weight k selected on val from {0, 2, 8, 32,
128, 512, inf} jointly with lambda), so that no free row is ever at the
marginal; Q1 reads the SHRINKAGE free_r2 - FREE_BIGRAM (the headline) and
the equal-dims gate history_tok_r2 - free_r2 on the unseen-key positions
and pooled (labels R2-FALLBACK-SURVIVES / R2-POOLED-ONLY / R2-ABSORBED);
Q2 puts the forward's stored final-norm state (clipped, z-scored and
reduced to 1024 principal directions on train) into the free arm and
reads the equal-dims and union readouts (labels H-SURVIVES /
H-COMPLEMENTARY / H-ABSORBS / H-INCONSISTENT); precondition REPRODUCE
against the stratified read's committed state rows; the assistant's
prediction pinned at registration (R2-FALLBACK-SURVIVES / H-ABSORBS modal,
the fallback gate straddling the floor) and the critic's recorded in the
design round, both before the freeze; floor straddles pinned to a "not
settled at this power" sentence; R2 pre-committed as the LAST rung on this
margin. NON-CRITERION: F-26's labels, the twin's SURVIVES and the
stratified read's labels stand; the one pinned consequence is a dated
STATUS line under F-26. Instrument tools/run_prefetch_r2.py (imports the
frozen stratified tool and refuses a modified one; the replay's checkpoint
tensors pinned by sha); evidence results/real/prefetch_r2_s3.json,
prefetch_r2_s3_r.json + state files.)

(2026-10-03, GENERALISING FREE BASELINE (R2), both runs from the clean
freeze commit 2fe5926; label R2-FALLBACK-SURVIVES / H-ABSORBS on both
harvests, REPRODUCE EXACT, no straddle on the unseen-key gate or either Q2
reading, k = 128 interior: against replay-prior smoothed tables the address
block still adds +0.0732 [+0.0623, +0.0834] / +0.0662 [+0.0559, +0.0773] on
the unseen-key positions (SIGNAL) while the encoding recovers +0.1971
[+0.1697, +0.2266] / +0.1822 [+0.1557, +0.2167] of hit rate there — the
located margin is NOT shown to be table sparsity at this encoding; the
pooled Q1 reading +0.0493 [+0.0425, +0.0577] / +0.0506 [+0.0433, +0.0594]
reads NOT-SHOWN / SIGNAL by the rule with the CI95 straddling the floor on
both — the one label-bearing reading on which the harvests differ, said in
words; with the forward's stored final-norm state in the free arm the
address block adds +0.0111 [+0.0078, +0.0150] / +0.0106 [+0.0068, +0.0153]
and the address stream +0.0172 [+0.0139, +0.0210] / +0.0162 [+0.0126,
+0.0206], both NOT-SHOWN — no material margin (at or above +0.05) of the
address block over the equal-dims free block, nor of the address stream over
the free bigram plus the hidden block, is shown (both readings CI-positive
below the floor) at this reader, and STAGE 2's ADDRESS-BEYOND-FREE
MOTIVATION IS STRUCK by the pinned condition (beside the strike, as pinned:
D_add^H on the unseen-key positions +0.0399 [+0.0279, +0.0514] / +0.0286
[+0.0195, +0.0386] (NOT-SHOWN; the primary's CI95 containing the floor);
PREFETCH-HEADROOM stands; K-6 stays UNTESTED). The free-baseline ladder
under F-26 is closed as pre-committed; no further rung on this margin. See
F-26's third dated status line and the block's OUTCOME.)

(2026-10-04 dated note: HORIZON READ REGISTERED — "OQ-9 STAGE-1 HORIZON READ
REGISTRATION" in docs/BLUEPRINT.md, a dated amendment to the R2 block written
before any readout of it ran; NOT a rung on the horizon-1 margin (R2 closed
that ladder; its horizon-1 cells are REPRODUCED here as the precondition,
never re-read) but a K-6 LEAD-TIME DATUM: prefetch pays only if the resident
set is chosen before the fetch latency elapses, every rung from F-26 through
R2 was read at horizon 1, and F-26's post-hoc reading (2), unregistered, is
the one thread that points the other way (at the one-token free arm the
token's margin over the cache decayed across horizons 1..4 while the address
margin held). The read: at horizons j = 2, 3, 4 on the positions t >= 1,
t + j < length, with the features at time t (R2's address block S[t], R2's
hidden block H(t), the smoothed token tables HORIZON-MATCHED to S[t+j] with
the horizon-1 replay as their prior, k and lambda selected per horizon on
val), D_eq^H(j) = history_bigram_r2 - free_h and D_add^H(j) = history_all_h -
free_h at B = 16 by R2's Q2 rule per horizon, with R2's straddle and
reader-guard rules; the stage label LEAD-TIME-ABSORBED (H-ABSORBS at every
horizon) / LEAD-TIME-SURVIVES@j / LEAD-TIME-COMPLEMENTARY@j /
LEAD-TIME-INCONSISTENT; the primary harvest's label is the label. NON-
CRITERION: no label of F-26, the twin, the stratified read or R2 moves; the
stage-2 strike STANDS under every label and this registration opens nothing;
no further free-baseline rung is registered at any horizon. Two pinned
consequences: a fourth dated STATUS line under F-26 and a dated K-6 STATUS
line in docs/WHY_THIS_DIES.md; under LEAD-TIME-ABSORBED on BOTH harvests
with no straddle and no guard at any label horizon on either, OQ-9's
prefetch half CLOSES at this reader by a dated line here (the fallback
readings beside it); under a SURVIVES / COMPLEMENTARY label, and only
where the replication reads the same per-horizon label at the same
horizon with no straddle, guard or free_h grid edge there on either
harvest and the two harvests agree on the stage label (the same word and
the same @j), the cell is recorded here in the registration's pinned words only
— the address-beyond-free motivation struck at horizon 1 stays struck,
this record opens no stage-2 registration, and a future one may cite the
cell only under the operator's words authorizing stage 2 in those words
and must re-read the margin against free_h on its own population at that
horizon. The assistant's prediction is pinned in the block before the
smoke (LEAD-TIME-ABSORBED modal, a floor straddle at horizon 4 about even,
D_add^H rising with the horizon, NOT-SHOWN modal with SIGNAL at horizon 4
about a quarter); the critic's sits beside it under HONEST PREDICTION,
pasted verbatim from its design round. Instrument tools/run_prefetch_horizon.py
(imports the frozen R2 tool and refuses a modified one); evidence
results/real/prefetch_horizon_s3.json, prefetch_horizon_s3_r.json + state
files.)

(2026-10-04 OUTCOME, HORIZON READ: both runs landed from the clean tree at
5e0e2a9 (frozen at b41d3f3); label LEAD-TIME-ABSORBED on the primary, the
replication AGREES on the stage label and on every per-horizon label;
REPRODUCE EXACT and the horizon-1 identity held on both; no straddle, guard
or free_h grid edge at any label horizon on either harvest, so by the pinned
condition OQ-9's PREFETCH HALF CLOSES AT THIS READER: "with the forward's
final-norm state at the address block's width and two tokens' smoothed
routing profiles in the free arm, no material margin (at or above +0.05) of
the address block over the equal-dims free block (horizon 2 +0.0034
[-0.0008, +0.0084] / +0.0024 [-0.0021, +0.0080]; horizon 3 +0.0016 [-0.0032,
+0.0070] / +0.0002 [-0.0052, +0.0063]; horizon 4 -0.0002 [-0.0052, +0.0056]
/ -0.0023 [-0.0075, +0.0039]) and none of the address stream over the free
arm (horizon 2 +0.0178 [+0.0138, +0.0223] / +0.0153 [+0.0113, +0.0203];
horizon 3 +0.0173 [+0.0129, +0.0223] / +0.0135 [+0.0093, +0.0187]; horizon 4
+0.0149 [+0.0105, +0.0198] / +0.0104 [+0.0062, +0.0154]) is shown at horizon
2, 3 or 4, as at horizon 1 (R2): at this reader the address stream is not
shown to add a material hit-rate margin over free information at any horizon
1..4 (lead time counted in forwards; no latency priced; NON-CRITERION; K-2
is untouched; K-6 stays UNTESTED and this is its lead-time datum); the
stage-2 strike stands, PREFETCH-HEADROOM (which does not depend on this
margin) stands, and OQ-9's prefetch half closes at this reader" — with the
FALLBACK readings beside it, as pinned (horizon 2: D_eq^H +0.0333 [+0.0173,
+0.0486] / +0.0172 [+0.0067, +0.0272] (NOT-SHOWN), D_add^H +0.0455 [+0.0318,
+0.0582] / +0.0282 [+0.0197, +0.0368] (NOT-SHOWN; the primary's CI95
containing the floor); horizon 3: D_eq^H +0.0433 [+0.0188, +0.0683] /
+0.0231 [+0.0057, +0.0412] (NOT-SHOWN; the primary's CI95 containing the
floor), D_add^H +0.0499 [+0.0290, +0.0710] / +0.0309 [+0.0175, +0.0449]
(NOT-SHOWN; the primary's CI95 containing the floor); horizon 4: D_eq^H
+0.0431 [+0.0164, +0.0689] / +0.0196 [+0.0042, +0.0373] (NOT-SHOWN; the
primary's CI95 containing the floor), D_add^H +0.0483 [+0.0264, +0.0693] /
+0.0254 [+0.0134, +0.0390] (NOT-SHOWN; the primary's CI95 containing the
floor)). What remains for the prefetch half is stage 2 under a motivation
this record does not supply, or the write-ups; the STEER half stays PARKED.
Full outcome: F-26's fourth dated status line and the OUTCOME of the horizon
block in docs/BLUEPRINT.md.)

## OQ-10 — Draft blindspot atlas and adaptive gamma
Calibrate draft confidence against acceptance outcome: high-confidence
rejections are the draft's blind spots. Classify them cross-bucket (concept
blindness, steerable) / within-bucket (token choice) / structural-boundary
tokens (the EOT-tracking prediction: rejections cluster at boundaries — one
grep of the audit jsonl tests it). Feeds adaptive block length from cheap
features (SpecDec++-adjacent; the delta is telemetry features + this
taxonomy). Also the info-budget protocol for OQ-1: report achieved gain over
the I(telemetry; bucket) bound as mechanism efficiency.

## OQ-12 — Gate/steer granularity — ANSWERED NEGATIVE (F-13, 2026-08-30)
Coarsening FIXES THE GATE (open rate 0.55/0.67/0.80 at C=15/31/62, joining
0.94 at C=510 — the granularity diagnosis confirmed as a measured curve)
but NOT THE MECHANISM: all six pre-registered arms land in the BROKEN cell
(best: k16 soft -0.0029 [-0.0088, +0.0029] with gate 0.559 > the 0.5 bar;
analytic estimand negative for all six). Residual failure CONSISTENT WITH
the free predictor's forecast quality (persistence 1.07-1.14 across coarse
k, 1.14 even at k=16) but OVERDETERMINED per the registered caveat (halved
headroom, glue-dominated stream) — the mechanism-matched oracle-ceiling
arm (BLUEPRINT Phase 0c attribution rider) decides. RIDER RAN (F-14):
STRADDLE (+0.0014 [-0.0043, +0.0069]; attribution stays open) — but the
oracle ceiling at the tested cell (k=16, beta=3, soft, one seed) is
bounded at <= +0.0069, and the beta-invariant part is the truth-gate rate:
15.9% open (the draft already agrees with the target's fresh concept
profile ~84% of the time at C=15), so even perfect forecasting has almost
nothing to act on there. Free-information bucket-bias steering is dead as
built at k in {16, 32, 64, 512}; the granularity trap holds at every
TESTED cell, with the FINE-k oracle (perfect forecast x the 0.61 headroom)
the open remainder — no sweet-spot claim extends to it. Phase 4 stays
blocked; telemetry's question stays K-2's registered one (offsets >= 2).
Untested residue: the fine-k oracle (the clean K-3 actuator ceiling —
register before running); coarse-k low-beta interaction; per-offset decay
of held predictions; a mechanism-crossed arm (oracle gate x free
posterior) if the gating-vs-direction decomposition ever needs settling.

## OQ-12 (original statement) — Gate/steer granularity: coarse concept space over fine audit space
Phase 0b's diagnosis (F-12): at k=512 the disagreement gate is open ~94% of
positions — argmax-vs-argmax agreement is near-impossible over 510 buckets —
and the free baseline lands at zero-to-negative even though 61% of rejection
mass is concept-addressable (F-11). The synthetic gate worked over C=12.
Hypothesis: gate AND bias in a COARSE space (C ~ 12-64: k-means over bucket
centroids, or a small-k bucketization) while auditing fine. Cheap test
(pre-register first): re-run the confirmatory arm + vanilla with a coarse
gating space; success = gate-open rate well below always-on AND delta >= 0.
Also in scope: per-offset decay of the held prediction, and whether the
posterior mechanism needs the gate at all in coarse space (F-7 says gated
only). Supporting measurement (committed): consecutive concept-bucket
persistence at k=512 is 0.027 with mean run length 1.015
(results/real/bucket_persistence_k512.json) — F-4's hold rule fails
outright in fine space, so ANY block-held fine-bucket prediction is stale
after ~1 token regardless of its source. BLOCKING for Phase 4 only:
steering through a net-harmful mechanism would fire K-3 spuriously. Phase
2/3 are NOT blocked — the harvest is granularity-agnostic and K-2's probes
compare information content, not steering deltas; OQ-12's outcome informs
their label space (coarse buckets), it does not gate them.

## OQ-11 — Streaming / anytime steering: signals DURING the target's forward
The schedule half of the original SRAM intuition, revived: PEARL-style
concurrent drafting exists but runs BLIND during verification, and FlexDraft
names the resulting bonus-token / accept-length uncertainty as the paradigm's
core problem. The proposal: an anytime sidecar on the per-layer event stream
(MoE gates fire layer-by-layer — a natively timed source) emits a posterior
that SHARPENS as the forward progresses; the D-10 centered mechanism consumes
partial evidence unmodified (softer posterior => smaller bias, automatically).
p01 probe: in the hardened synthetic world the signal is strongly
front-loaded (f=0.25 of evidence ~ full-evidence steering; anytime training
helps most at low f) — regime-bound, priority-ordered reveal. Open: real
front-loading curves per telemetry source; the TIMING axis (intra-block
scheduler, fresher positions); value concentration in disaggregated
memory-bound deployments (this is where K-6 improves); ConFu as the
values-crossing comparator for measuring the observability tax directly.
(2026-09-06 dated note: the "real front-loading curve per telemetry
source" for S3 is docs/FUTURE_IDEAS.md P1 (ii) — layer l+1 expert [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
set predicted from layers <= l of the same token, computable from
the existing harvest with no model forward; unregistered.)

## OQ-13 — S3 margin composition: floors, lenses, and where the signal lives
Provenance: user-proposed 2026-09-01 during the S3 primary-grid session.
Every item is a POST-REPLICATION pre-registered secondary analysis,
NON-CRITERION for the S3 verdict (primary evidence probes_s3.json @
dec515b, EXISTENCE provisional pending the seeds-8..11 replication; these
activate on CONFIRMED, and stay worth running on OPEN). Motivating facts
(committed): the k16 majority floor IS the glue bucket at 0.5803
(harvest_audit_olmoe.json); the L3 headline (+0.0721 off2) reads through a
lopsided lens (two mega-groups cover ~461/510 concepts, incl. all 20
zero-degree buckets); margins concentrate at off2 and in L3.
Questions, cheapest first, floors measured before any probe runs:
(i) TWO-STAGE DECOMPOSITION ("mega bucket + X = target"): split top-1 into
coarse-step accuracy x within-group refinement accuracy. Conserves task
difficulty, relocates visibility — does the telemetry edge live in picking
the group or refining inside it? The within-group readout escapes floor
domination (concept-space cousin of the glue-conditioned readout). Feeds
K-3 actuator design (at which granularity to trust the signal). CPU.
(ii) BALANCED-LENS ROBUSTNESS: pin ONE size-capped grouping procedure
before results are read; ask "does the L3 signal survive a balanced
lens?" Collapse => the headline was mostly mega-group membership (a
coarser claim); survival => the groups signal is rich. NOT a
bigger-number hunt — lens-shopping is the named failure mode, and the
recorded-lens number stands regardless of this outcome. CPU.
(iii) FLOOR-REDUCTION menu: glue-conditioned readout (content-token-only
scoring; likely needs cell re-runs — state files carry cluster counts,
not confusions); glue-SPLIT label space (registered deviation from the
merged-glue label convention — "which function word" is legitimate for
acceptance, D-7 gate semantics untouched); content-dense prompt families
(code/math/structured; GPU harvest, CHANGES THE POPULATION CLAIM,
independently motivated for external validity). Volume extension seeds
12+ (reserved in the S3 registration) is the pure power lever — narrows
CIs, moves no floor.

(2026-10-05 dated note: item (ii) REGISTERED as one half of "READER-AND-LENS
RE-TEST AT S3 REGISTRATION" in docs/BLUEPRINT.md (the operator's decision of
2026-10-05 folded the balanced-lens read into the stronger-reader re-test of
F-24 / F-25), written before the lens artifact existed: ONE size-capped
grouping, Fiedler-order quantile binning of the same transition affinity into
16 contiguous bins of 31 or 32 concepts (cap 32 against the lopsided lens's
268), the zero-degree concepts to the smallest bins, glue class 16; the PROXY
question answered on fresh linear (c) - (a) cells at off2 (labels
LENS-SURVIVES / LENS-COLLAPSE / LENS-SPLIT / LENS-NOT-SHOWN by the Phase-3
triple rule, the ratio to F-17's +0.0721 / +0.0730 reported, no threshold on
it), and the full-free re-test at that lens under F-25's frozen rules; no
second lens whatever the labels; the recorded-lens number stands regardless.
The artifact, built 2026-10-05 after the pin, is LESS coherent than k16 on the
train glue-dropped chain: persistence 0.1033 against its own label-marginal
shuffle baseline sum q^2 0.0777 (excess 0.026), k16 0.2293 against 0.1902
(excess 0.039), the lopsided lens 0.6748 against 0.5291 (excess 0.146;
baselines critic-recomputed, no committed artifact records them), so a
LENS-COLLAPSE is ambiguous between "mostly mega-group membership" and "a
lens too fine for transition coherence" and is written with both readings;
the registration also reads P beside the committed L1 and L2 margins
(per harvest L3-GROWTH-LOST / -SURVIVES / -NOT-SETTLED, combined over the
two harvests into LOST iff both LOST, SURVIVES iff both SURVIVES, SPLIT iff
exactly one is decided or the two disagree, else NOT-SETTLED; the "coarser
claim" sentence is written for the combined LOST only). Items (i) and (iii)
stay unregistered. Instrument tools/run_reader_lens.py;
lens builder tools/build_balanced_groups.py; evidence results/real/lens_s3.json
and lens_s3_r.json + state files; the outcome lands as a dated note here.)

(2026-10-05 OUTCOME, STAGE LENS (F-28): both registered runs from the clean
tree at d3504b2; the lens built once as pinned (sizes [32 x 14, 31 x 2],
Fiedler gap 0.0166; train glue-dropped persistence 0.1033 against the
lopsided lens's 0.6748 and k16's 0.2293). PROXY: LENS-SURVIVES — P +0.0221
[+0.0187, +0.0258] / +0.0195 [+0.0160, +0.0232], 0.307 / 0.267 of F-17's
+0.0721 / +0.0730; GROWTH over the committed L2 margin (+0.0206 / +0.0207):
NOT-SETTLED on both harvests, combined L3-GROWTH-NOT-SETTLED — the margin
exists under a size-capped partition, its size over L2 is not settled at
this power, and the "coarser claim" sentence is not written; the 657-summary
proxy (a) at linear reads only about +0.003 above the majority floor at this
lens (the same floor as the lopsided lens's) while the full free baseline at
mlp256 reads about +0.04 (at matched capacity: linear (a) +0.0029..+0.0035 /
+0.0025..+0.0030 against fplus +0.0270..+0.0281 / +0.0243..+0.0256; mlp256
(a) +0.0046..+0.0048 / +0.0018..+0.0032 against fplus +0.0411..+0.0431 /
+0.0360..+0.0398 (primary / replication, ranges over the three seeds)), so P
is essentially acc((c)) minus the floor and the lens is predictable by the
full baseline, not by the proxy. FULL-FREE at the balanced lens: ABSORBED (D
+0.0019 [+0.0006, +0.0032] / +0.0004 [-0.0011, +0.0018]; Mt +0.0042
[+0.0025, +0.0061] / +0.0021 [+0.0002, +0.0041]; Mn_r +0.0023 [+0.0010,
+0.0038] / +0.0017 [-0.0000, +0.0035], the corrected twin point-positive on
both harvests, CI-clear on the primary only, where it cost at the lopsided
lens; OFF3-ABSORBED, OFF4-ABSORBED), written beside F-25's S3 L3 SPLIT as a
dated note. No second lens; the lopsided-lens numbers stand as registered.
Item (ii) at this lens: the (c) - (a) margin exists under the size cap
(LENS-SURVIVES); its size over L2 is not settled (combined
L3-GROWTH-NOT-SETTLED); neither the struck "rich" sentence nor the "coarser
claim" sentence is written.)

## OQ-14 — Extraction ceiling and usable signal: ensembles, error-predictors, calibration
Provenance: user-proposed 2026-09-01 (same session). Framing constraint:
probes RECOVER signal from the recorded (telemetry, free) pair; they
cannot create it — each item either closes the gap to the fixed
mutual-information ceiling or converts raw accuracy into USABLE
(selective) signal. Measured anchor that the ceiling is NOT reached:
capacity alone moved L1/off2 c-a from +0.0147 (linear) to +0.0200
(mlp256) on the primary S3 grid — the linear probe leaves signal in the
well. Everything below is mechanism-tier until run (direction sound,
magnitudes unmeasured).
GUARDRAIL for all items: the estimand is a DIFFERENCE (c-a); any
extraction upgrade (ensemble, boosting, capacity) must be applied to BOTH
arms at matched capacity or the margin is confounded by generic
ensemble/capacity goodness. The grid's like-vs-like capacity pairing is
this rule; keep it.
(i) PER-LAYER PROBE ENSEMBLE + combiner over the 16 gate streams. Primary
value is diagnostic: WHICH LAYERS carry the future? A concentrated answer
narrows the physical sideband (tap fewer wires) and feeds OQ-5 / K-6
economics directly. CPU; slots are already stored per-layer.
(ii) ERROR-PREDICTOR HEAD (a second probe trained to predict when the
first is wrong): selective prediction. Never raises raw accuracy; raises
precision-at-coverage, which is what D-8's confidence gates consume.
Ranked highest here for the K-3 road — act only when right, stand down
otherwise. Readout: precision/coverage curves on the confident subset,
both arms symmetrically.
STATUS (2026-09-02): ANSWERED at S1 by the K-3 arc's D2/D3 stage
(results/real/error_predictor_s1.json, critic-recomputed) — selective
prediction works: test precision@0.20 = 0.7919 (a) / 0.8356 (c) over
base rates 0.6059/0.6223; both arms select L1/off2; full readout and
freeze pins in the BLUEPRINT K-3 arc block.
(iii) CALIBRATION readout: do the probes' graded distributions calibrate
(80%-confident right ~80% of the time)? A calibrated 60% probe is worth
more to an actuator than its top-1 suggests. Probe-side complement of
OQ-10's draft-confidence atlas.
STATUS (2026-09-02): ANSWERED at S1 (same evidence as (ii)) — the
probes calibrate: test ECE 0.0082 (a) / 0.0408 (c) at the selected
L1/off2 cell, both under the pinned 0.05 swap bar (the (c) margin is
0.009 — disclosed), so the RAW POSTERIOR is the frozen K-3 confidence
signal and the D2 heads served as verification.
(iv) Boosting / residual probes: further capacity rungs under the same
guardrail; diminishing returns expected. All CPU on existing harvests;
all post-replication, each with its own registration.

## OQ-15 — Outcome-supervised readout: telemetry as symbols, decoder behavior as supervision
Provenance: user-proposed 2026-09-01 (post-F-18, post-economics-memo,
the gain-staging conversation). QUEUED BEHIND the K-3 attempt by user
direction — explore after the current error-predictor lane resolves.
THE REFRAME: every committed probe is supervised on a PROXY task
(future concept buckets — chosen for a clean existence question, not
because concepts are what a decoder needs). This OQ retargets the
supervision to the outcome itself: P(draft token at offset j is
rejected | telemetry at anchor).
PRIMARY SUPERVISION TARGET (added 2026-09-02, before any OQ-15 data
exists): the per-position ANALYTIC acceptance 1 - TV(p_j, q_j) — the
D-9 estimand the harness already computes at every drafted position —
as a REGRESSION target. Graded (every sample carries a value in
[0,1] instead of one bit), variance-reduced, and IDENTICAL to the
quantity a scheduler consumes, so no translation loss between what
the reader predicts and what the actuator acts on. The binary
accept/reject head remains as the classification variant. The K-3
byproduct log records the per-position analytic values (see the
dated byproduct amendment in the BLUEPRINT K-3 arc block). The telemetry/probe readings are
treated as arbitrary internal symbols — a language grounded only by
outcome labels, never by assigned meaning. This ESCAPES both measured
bounds: F-14's ~zero oracle ceiling is specific to (concept task x
bucket-bias actuator), and the F-15/F-17 probe margins are
proxy-task lower bounds, not bounds on I(telemetry; draft-failure) —
which has NEVER been measured and may be larger or smaller than the
concept slice.
Constraints pinned at ledgering, before any data exists:
(a) The information ceiling relocates, it does not vanish: nothing
downstream can know more about draft failure than the telemetry
carries about draft failure (the OQ-14 charter's law, restated).
(b) DATA: all committed harvests are target-only — no draft ran, so
no failure labels exist. This lane needs a PAIRED harvest
(speculative-decoding runs logging telemetry per drafted position +
accept/reject outcomes), its own registration. The Llama pair +
shadow taps (S1 instruments) is the ready-made venue; an OLMoE draft
partner is unverified.
(c) MANDATORY BASELINE (D-5's analog): a failure predictor on FREE
features (draft confidence, last-p summaries — SpecDec++'s feature
class, the incumbent) runs alongside; telemetry must add
precision-at-coverage beyond it, with the F-16-style equal-dims
noise anchor. Without that arm this is dominated-baseline theater.
(d) The economics memo's K-3 bars apply UNCHANGED (they were pinned
mechanism-agnostically); no new goalposts.
CHEAP PILOT (zero new GPU, gates the paired-harvest spend): on the
existing committed harvests, does telemetry predict the TARGET'S OWN
upcoming difficulty (entropy/sharpness of p at offsets >= 2) beyond
the free summaries? A draft-free correlate of hard-to-draft
positions. VERIFY FIRST that the per-position free summaries contain
the needed label components (unchecked at ledgering).
SCALING EXTRAPOLATION (user, same session): the industrialized
version — standard transformer training on (telemetry sequence ->
accept/reject) at serving-fleet scale, labels a free byproduct of
production spec decoding (every serving run generates them; no human
labels). Sound as supervised learning. Pinned caveats: scale REACHES
the information ceiling, it cannot RAISE it (small probes are the
cheap estimator of whether the ceiling justifies the spend — run the
pilot before the fleet); the learned mapping is pair-specific and
policy-dependent (once the system acts on its predictions the data
distribution shifts — off-policy drift, periodic retraining); any
deployed artifact must distill back under the draft-loop latency
budget or K-5 eats the win. Prior art: Hashemi et al. (learned
memory-access prediction — address streams are learnable at hardware
timescales) supports; SpecDec++ is the draft-features incumbent to
beat; the telemetry-features acceptance head remains the unclaimed
cell (OQ-10's note).
(2026-09-02 FOLD-BACK COUNT AMENDMENT, BLUEPRINT: OQ-15 is now
FOLD-BACK #1, run first if Attempt #1 nulls. Its arc registration
must pin the primary comparison the cross-lane skip condition
reads: telemetry-featured head vs matched-capacity free-baseline
head, with the F-16 equal-dims noise anchor, on held-out outcome
prediction — AND the exhaustive terminal-outcome partition {WIN,
information-ceiling null, conversion-mode null} with its
statistical criteria and the anchor's classification role
(decidability pin, BLUEPRINT amendment); unclassifiable outcomes
default to information-ceiling null. An information-ceiling null
here skips OQ-16 and stops the lane; a conversion-mode null hands
off to OQ-16.)
(2026-09-03: ARC REGISTERED — the OQ-15 FOLD-BACK #1 ARC
REGISTRATION block in docs/BLUEPRINT.md pins the terminal-outcome
partition, Stage I (information, CPU, the arm-1 byproduct logs) and
Stage C (conversion, GPU, fresh committed populations, unchanged
bars). The CHEAP PILOT stage above is SUPERSEDED: its purpose was
gating a paired-harvest spend, and the registered byproduct
amendment collected the paired data for free — constraint (b) is
satisfied by the K-3 byproduct logs, no new harvest needed.
Constraint (c)'s GATE role is superseded by a dated pre-commit
clause in the registration block: the gate is the equal-dims
noise-twin MSE comparison (F-16's measured dilution can fake a
null on a TEL-vs-FREE gate); the FREE predictor still runs
alongside and precision-at-coverage is still computed — both
REPORTED, per the supersession clause.)
(2026-09-03, STAGE I RESOLVED — F-20: the gate PASSED mechanically
(+0.00076 CI95 [+0.00031, +0.00121]) but the registered DI-1
stale-target control (five permutation seeds, pinned label
ARTIFACT-DOMINANT) leaves the margin indistinguishable at this
power from zero-information target draws (five-seed spread
-0.00071..+0.00064, mean ~0, sd ~ the live margin; live point rank
1/6, p ~ 0.17), and the telemetry head loses outright to the free
head (delta_free -0.00286, CI-clear negative, every offset).
Block-aligned outcome information above free signals is NOT
demonstrated. Stage C remains authorized by the partition and
USER-GATED; the lane sits at that cost decision. See the BLUEPRINT
STAGE-I OUTCOME note and F-20.)
(2026-09-04, RESOLVED — CONVERSION-MODE NULL at Stage C, F-21: the
user took the Stage-C fork; the GPU chain ran clean; the seed-2
verdicts breached the pairwise budget guard on the head_free leg
(a selection-time gap, not inflation — new failure mode vs F-19),
the registered void semantics executed (46ab439: quarantine held,
val-only re-freeze to the comparator's own val budget, seed-3
whole-stage rerun), the guard then cleared every leg and the gate
resolved NOT WIN: head_tel ties vanilla (+0.003, straddle) and
loses CI-clear to head_free (-0.082) — the conversion-level mirror
of F-20's delta_free. By the pinned partition: CONVERSION-MODE
NULL. OQ-15 is CLOSED as fold-back #1; OQ-16 is now AUTHORIZED as
fold-back #2 (new arc, new registration, user GPU authorization
required); the lane hard-stops after #2.)

## OQ-16 — Vector reconstruction: telemetry -> hidden-state steering vector, SD^2's actuator under the observability constraint
Provenance: user-proposed 2026-09-02 ("what if it read the hidden
state directly instead of looking at token baskets"), refined jointly
in-session. QUEUED as a FOLD-BACK CANDIDATE alongside OQ-15: K-3's
kill text permits ONE fold-back — if Attempt #1 nulls, the registered
choice is between OQ-15 (outcome-supervised classification) and this
lane; both are data-fed by the K-3 byproduct logs (see the dated
2026-09-02 byproduct amendment in the BLUEPRINT K-3 arc block).
THE REFRAME: keep the observability constraint (addresses only cross
the wire); change the SUPERVISION to dense regression — a probe
trained to RECONSTRUCT the hidden-state steering vector from
telemetry, consumed on the DRAFT side by SD^2's proven injection
mechanism (draft-side q modification is fair game per D-1's bright
line; F-0 losslessness holds for any q). The token-basket
quantization leaves the supervision entirely. This turns OQ-6 into a
literal measurement: what fraction of SD^2's vector survives
reconstruction from the address stream?
WHY PRIOR BOUNDS DO NOT APPLY: not bucket-bias (F-12/F-13/F-14
inapplicable); supervision is not the topic proxy (F-15/F-17 margins
bound a different readout slice); and the committed OQ-6 h-probe
result — the raw hidden state LOSING to telemetry at matched linear
budget, both sources, both runs — is a statement about extracting
FROM h under a cheap budget, and says nothing about reconstructing
TOWARD h from telemetry.
MEASUREMENT PATH, cheapest first: (i) probe-land regression:
telemetry -> h_a (the SD^2 steering vector's position) and the
anticipatory variant telemetry -> h at future anchors; readouts =
R^2 / cosine to the true vector, plus a DOWNSTREAM proxy (does the
reconstructed vector's injection direction correlate with the true
one's). (ii) Actuator stage only if (i) is non-null: reconstructed
vector into the draft's MLP states per SD^2 (their code is public;
prior-art machinery, not ours). MANDATORY BASELINES pinned at
ledgering: a free-features reconstruction arm (D-5's analog —
reconstruct h from the anchor free summaries; telemetry must beat
it), and the F-16-style equal-dims noise anchor. If run as the K-3
fold-back, the economics memo's bars apply UNCHANGED.
HONEST SIZING (mechanism-tier until run): 513-768 bits/token of
addresses reconstructing a 4096-dim bf16 vector is ~100x
underdetermined — the question is whether the STEERING-RELEVANT
subspace is recoverable, not the whole vector; direction sound,
magnitude unmeasured. SD^2's own limitation (hidden-state
intervention can derail the draft) applies to the injection stage;
the confidence-gating lessons (D-8/F-5) carry over.
(2026-09-02 FOLD-BACK COUNT AMENDMENT, BLUEPRINT: the "ONE
fold-back" sentence above is superseded — OQ-16 is FOLD-BACK #2,
running iff OQ-15 nulls in conversion mode; SKIPPED if OQ-15
nulls at the information ceiling; the lane hard-stops after #2 or
the skip, no third mechanism.)
(2026-09-04: AUTHORIZED — OQ-15 resolved CONVERSION-MODE NULL at
Stage C (F-21), the branch that hands off here. Execution remains
a NEW arc: full registration (partition, bars, populations) and
user GPU authorization required before anything runs. Honest
weight carried from F-20/F-21: the S1-tier value-slot stream
showed no block-aligned information margin over free signals and
lost at both prediction and conversion; OQ-16's bet is a
DIFFERENT target (dense h_a reconstruction), but the same stream
feeds it — the mandatory free-reconstruction baseline is where
that concern is priced. F-21's one supportive datum: the head
actuator machinery converts free signals live (head_free
descriptive observation), so an actuator path exists if the
reconstruction stage ever clears its baselines.)
(2026-09-04: ARC REGISTERED — the OQ-16 FOLD-BACK #2 ARC
REGISTRATION block in docs/BLUEPRINT.md pins the terminal-outcome
partition (every branch ends the lane; a Stage-R PASS authorizes
exactly one user-gated actuator stage), Stage R (CPU-only
reconstruction of the logged h_a from the four vanilla verdict
byproduct runs, ~70.5k blocks, two populations; two-leg gate:
TEL-vs-NOISE existence with a GATING five-seed stale-target
control baked into the criterion, AND TEL-vs-FREE deployability;
direction proxy reported-only), and the Stage-A
deferred-constants skeleton. Three design decisions put to the
user pre-registration; honest expectation pinned: a leg-2 failure
(dilution/deployability null) is the expected outcome. Stage R
awaits launch.)
(2026-09-04, STAGE R RAN — F-22: STAGE-R PASS by the pinned gate
(delta_noise +0.176, ~32x the stale 3-sd bar; delta_free +0.205),
the lane's first surprising branch — the pinned dilution-null
expectation is refuted. The critic's attack round found no leak
(byte-identical rerun, bit-exact fresh bootstrap) but a
standardization pathology on two out-of-support test prompts
inflating the registered deltas ~25% and leaving the honest
TEL-vs-trivial margin CI-straddling. Registered post-gate
diagnostics (non-criterion): DR-1 (feature-support clip) =
DEPLOYABLE-MARGIN CONFIRMED (+0.251 [+0.239, +0.262], both
populations; TEL R^2 ~0.25, cosine ~0.50); DR-2 (equal-dims
FREETOK = free ++ hashed top-32 next-token ids, deployment-free) =
TOKEN-IDENTITY-NOT-EXCLUDED — FREETOK reconstructs h_a CI-clear
slightly BETTER than telemetry (-0.005 [-0.007, -0.003]) and
reaches a margin over FREE at least as large as telemetry's
(+0.174; the TEL-vs-FREETOK design does not show composition —
DR-3 resolves that). ANSWER to this ledger's literal question:
about a quarter of the anchor state survives linear reconstruction
from the address stream — and a free encoding of the output
distribution's top-32 token identities recovers at least as much.
Stage A stays AUTHORIZED and USER-GATED by the partition; as a
TELEMETRY test it has no reconstruction-level basis for a win and
two conversion nulls against it, and a free-reconstruction
injection test is a different, unregistered question.)
(2026-09-04, DR-3 RAN — registered pre-run in 2ec789f; SUPERSEDES
the previous note's "no reconstruction-level basis" sentence:
TELEMETRY-BEYOND-P. UNION = telemetry ++ p's top-32 support beats FREETOK by
+0.065 [+0.062, +0.068] (both pops) and its alignment-destroyed
anchor by +0.078 — 37.5% of the free margin, above the pinned
"would surprise" line. So the address stream DOES carry block-
aligned, dilution-priced information about the anchor state beyond
FREETOK's 2048-bin hashed encoding of p's top-32 support ("beyond
p" itself is unpriced until a better-token-encoding comparator,
DR-4, runs): small in absolute terms (R^2 0.258 -> 0.324) but
CI-tight and replicating on two disjoint prompt populations. This reopens the Stage-A telemetry question with a
reconstruction-level basis; the actuator claim pinned for a
Stage-A freeze is UNION-vs-FREETOK, both free-augmented. Whether that increment
converts to acceptance at matched budget is unmeasured (two
conversion nulls on the lane); Stage A remains AUTHORIZED and the
user's call, GPU untouched.)
(2026-09-05, DR-4 RAN — registered pre-run in c2181b1, the lane's
last reconstruction-level diagnostic: COMPARATOR-TOOTHLESS. The
value-paired second-hash encoding of p's top-32 is CI-clear WORSE
than FREETOK at the registered readout (-0.003 [-0.005, -0.001]),
which is UNANCHORED (no destroyed-TOK_B twin), so the block's
contribution is not separable from its +2048-dim dilution — the
committed VAL table says it helps at high lambda. "Beyond p" stays
UNPRICED; DR-4 did not deliver the basis the registration said a
Stage-A telemetry test needs; the pre-registered recommendation —
treat it as NOT confirmed for the Stage-A decision — stands, and
Stage A, if run, proceeds on the user's decision with that on the
table. FREETOK stays the free comparator. The anchored DR-5 would
resolve the caveat but is forbidden by the fold-back-#2 hard stop
unless the user authorizes an exception in those words. GPU
untouched.)
(2026-09-05, STAGE-A FREEZE landed (BLUEPRINT), pre-GPU and critic-
gated twice: SD^2-style up-projection injection with a frozen
drafter and a rank-512 zero-initialised adapter (owned deviations
from SD^2 disclosed); arms vanilla / oracle_h (TRUE h_a, the
actuator ceiling) / free_inject (FREETOK) / tel_inject (UNION);
fresh 210-prompt verdict population with a mechanical paraphrase
refusal; export binding-gated on DR-4 (fields + weights), five-fold
cross-fit h_hat for adapter training; ladder A0 (oracle vs vanilla,
E6 +0.062 bar unchanged) before A1 (free-actuator readout + the
telemetry verdict T-vs-V and T-vs-F); each rung user-launched. GPU
untouched.)
(2026-09-05, CLOSED BY DATED ERRATUM — TARGET-FREE (F-23; BLUEPRINT
"OQ-16 DATED ERRATUM + LANE CLOSURE"): the registered target h_a is
an exact linear function of the verifier's full next-token
distribution at the anchor (48 pinned rows: full-logit inverse
relative error 2.5e-8; top-4097 log-probs per-row R^2 +1.0000; top-32
R^2 +0.014), i.e. free information under D-5. The stream's reconstruction
is K-2's lossy copy; "beyond p" is priced at this target (nothing
is); the Stage-A telemetry arms are struck pre-GPU; the oracle arm is
the deployable free-actuator arm and needs its own registration if
run. No partition branch is claimed (the limbo clause is honored; the
partition's VOID precedent applies): CLOSED BY DATED ERRATUM,
mechanism TARGET-FREE. The lane ENDS; the hard stop holds; the anticipatory target (h at future anchors) is the one
reconstruction question left open and is NOT authorized.)

## OQ-17 — Does the existence margin survive the FULL free baseline (p_a summaries + token identities + h_a, read nonlinearly)? — REGISTERED 2026-09-06, pre-run, critic-gated
Provenance: user-authorized 2026-09-06 ("lets run the next leg") after
the 2026-09-05 reading of F-23; item 1 of the post-F-23 options. THE
question F-23 left on the existence layer, sharpened by the record:
F-15/F-17 measured telemetry against (a) = 657 summaries of p_a; F-22
DR-2 showed a hashed encoding of p_a's top-32 token ids reconstructs
h_a at least as well as telemetry; F-23 showed h_a is an exact linear
function of the full p_a (free under D-5); and the registered linear
(h) arm sits at or below the majority floor on 6 of the 8 harvest x
offset-2/3 cells (below it on the four offset-3 cells: a trainer
failure on raw h_a, since a linear model contains the constant
predictor), so the "(h) adds nothing over (a)"
defence was a statement about an unusable reader. Meanwhile telemetry
ALONE beats (a) at offset 2 on all four harvests (b-a mlp256 +0.0149 /
+0.0154 at S1, +0.0100 / +0.0069 at S3), so the stream is not a copy of
the summaries; whether it is a copy of the full p_a is what this asks.
Protocol (docs/BLUEPRINT.md "OQ-17 FULL-FREE EXISTENCE RE-TEST
REGISTRATION", 2026-09-06, written before any registered cell ran and
amended on critic review before the freeze commit): arms fplus = (a)
++ TOK ++ hz (h_a clipped to the train support and z-scored with
train-split moments), fplus_b = fplus ++ aligned telemetry, fplus_n =
fplus ++ alignment-destroyed telemetry (equal dims, same block order);
L1 / off2 at linear and mlp256, S1 adds off3 at mlp256; seeds {0,1,2};
both harvests per source; the registered optimizer and budget. A
two-leg leak rider (shuffled fplus vs the committed shuffled (a);
shuffled fplus_b vs shuffled fplus) runs first and halts on failure. A
READER-VALIDITY precondition (all nine gate-cell probes hold the
majority floor; Mf CI upper >= 0) must pass before any label. Gate:
L1/off2/mlp256 D = acc(fplus_b) - acc(fplus_n) under the Phase-3
triple rule; per-source labels from both harvests: SURVIVES-FULL-FREE
/ SPLIT / ABSORBED (every D CI upper below +0.005 on both harvests) /
NOT-SHOWN (fails without excluding) / READER-INVALID / INCOMPLETE; Mt
is quoted beside D and decides which SURVIVES sentence is licensed.
Consequence rules pinned there (ABSORBED = dated erratum on F-15 or
F-17 and K-2 re-read as FIRED at that source; NOT-SHOWN = wording
erratum, K-2 OPEN at the full-free level; SPLIT = OPEN, no relabel;
SURVIVES = residuals close per the licensed sentence). CRITERION-
BEARING, unlike P1. Honest prediction pinned there: S1 survives with a
smaller margin (+0.005..+0.012); S3 splits or is not shown.
Instrument: tools/run_fullfree.py (+ tests/test_fullfree.py); evidence
results/real/fullfree_{s1,s1_r,s3,s3_r}.json + state files.
Dated note (2026-09-06, after the S1 payloads and the S1 critic recompute
were read, before any registered twin cell ran; one scratch cell is
disclosed in the block): the S1 registered label is ABSORBED
(horizon OFF3-ABSORBED; reader valid on both harvests; both rider legs
pass). The critic found the equal-dims twin non-inert (Mn CI-clear
positive at the primary gate; the shift-17 read lands beyond the label
position for most anchors), so a POST-HOC TWIN-INERTNESS DIAGNOSTIC is
registered in the BLUEPRINT block (arm fplus_r = fplus ++ the slots of
the same-generation-index row of a different prompt at the same anchor
index; readouts D_r / Mn_r / T at the gate
cell; readings TWIN-ROBUST / TWIN-MASKED / TWIN-SPLIT / TWIN-DEPENDENT /
TWIN-INCOMPLETE; non-criterion; it pins which qualifier the consequence
text carries). The consequence text is written only after the four twin
payloads are read; S3's registered label is read when its replication
finishes. Evidence: results/real/fullfree_{s1,s1_r,s3,s3_r}_twin.json +
state files; tools/run_fullfree_twin.py; tests/test_fullfree_twin.py.
OUTCOME (2026-09-06, F-24): S1 ABSORBED (OFF3-ABSORBED), S3 ABSORBED at the
registered reader — gate D +0.0002 / +0.0012 (S1) and +0.0003 / +0.0001
(S3), every D CI95 upper below +0.005, Mt beside it +0.0034 / +0.0033
and +0.0033 / +0.0013; the full free baseline beats the 657-summary
proxy by +0.018..+0.037 at the gate and beats the committed telemetry arm
outright at mlp256 on three of four harvests. Prediction failed on both
sources. Twin diagnostic: S1 TWIN-ROBUST, S3 TWIN-ROBUST (the null reproduces at the corrected twin on both sources).
Consequences executed: F-15 / F-17 dated errata scoped to the re-tested
cells; K-2 STATUS per source; F-16 / F-18 moot notes. OQ-17 is CLOSED
as a question; what remains open is the owner's: a registered re-test
with the corrected twin and/or a stronger reader (not authorized here).

(2026-10-05 dated note: the stronger-reader residual named above is REGISTERED
for S3 as "READER-AND-LENS RE-TEST AT S3 REGISTRATION" in docs/BLUEPRINT.md:
an HZ-RESCALED reader (the hz block alone multiplied by sqrt(m_SLOTS / m_HZ)
over the train anchors, so it no longer dominates the input norm F-24 named;
every other block unscaled) and a TWO-TOWER reader (the slots block with its
own first layer) at the S3 gate cells of L1 and both L3 lenses, with a
LONGER-BUDGET reader and S1 L1 as pinned conditional stages, the twin control
and the frozen label rules unchanged; labels SURVIVES-STRONGER / SPLIT /
ABSORBED / NOT-SHOWN / READER-INVALID per (reader, space) and ONE K-2 sentence
over the valid cells (NOT-OVERTURNED-AT-S3 / REOPENED-AT / ISOLATED /
UNSETTLED / INCOMPLETE): a reopen needs a REOPEN-GRADE cell (SURVIVES-STRONGER
with the FULL licence AND Mt firing the Phase-3 triple rule on both S3
harvests) at L1 or the BALANCED L3 — the lopsided lens never decides a reopen
— and the same reader reopen-grade at S1 L1, and stays PROVISIONAL until a
reader-matched rider passes under its own registration; ABSORBED under a
reader narrows the residual at that cell, NOT-SHOWN neither overturns nor
narrows, and at L3 (OPEN at the registered reader) an ABSORBED under a reader
is written beside the open label, never as a kill. CPU only. One more family
of readers: K-2's universal is not established by it either way.)

(2026-10-05 OUTCOME, STAGE READERS (F-28): the stronger-reader residual
tested at S3 under R-N (hz-rescaled) and R-T (two-tower): R-N (hz-rescaled)
at L1 ABSORBED; R-N (hz-rescaled) at the lopsided L3 SURVIVES-STRONGER
(EQUAL-DIMS-ONLY, the twin's larger cost); R-N (hz-rescaled) at the balanced
L3 NOT-SHOWN; R-T (two-tower) at L1 ABSORBED; R-T (two-tower) at the
lopsided L3 ABSORBED; R-T (two-tower) at the balanced L3 ABSORBED; the K-2
word at S3 K-2-ISOLATED; per cell, ABSORBED narrows the residual to readers
outside these families and NOT-SHOWN neither overturns nor narrows; the
registered-reader kill stands as a statement about that reader; STAGE
READERS-LONG RUNS (no SURVIVES-STRONGER or SPLIT at L1 or the balanced L3);
STAGE S1 is not triggered by this stage (no reopen-grade cell at L1 or the
balanced L3); final at the READERS-LONG landing.)

(2026-10-09 OUTCOME, STAGE READERS-LONG (F-28): the longer-budget reader at
the same cells reads R-L (longer budget) at L1 ABSORBED; R-L (longer budget)
at the lopsided L3 SURVIVES-STRONGER (EQUAL-DIMS-ONLY, inflated by the
twin's own cost); R-L (longer budget) at the balanced L3 ABSORBED; the ONE
K-2 sentence over both reader stages: K-2-ISOLATED (the word is unchanged
from the READERS landing's interim K-2-ISOLATED); the K-2 word is FINAL for
this registration; the stronger-reader residual at L1 is narrowed under R-L
as under R-N and R-T (ABSORBED narrows, not closes; NOT-SHOWN neither
overturns nor narrows); STAGE S1 does NOT run (no reopen-grade cell at L1 or
the balanced L3 under any reader) — FINAL.)

(2026-10-17 OUTCOME, S1 READER RE-TEST (F-29): the stronger-reader residual
at S1 named above, tested under the three F-28 readers at the S1 gate cell:
R-N (hz-rescaled) ABSORBED (D +0.0026 [+0.0008, +0.0043] / +0.0022
[+0.000497, +0.0039]); R-T (two-tower) ABSORBED (D +0.000339 [-0.000377,
+0.0011] / +0.0011 [+0.000363, +0.0019]); R-L (longer budget) ABSORBED (D
+0.000382 [-0.0009, +0.0016] / -0.000044 [-0.0014, +0.0013]); the S1 word
K-2-NOT-OVERTURNED-AT-S1 (under readers R-N, R-T and R-L at S1; one more
family of readers, not K-2's universal); the residual is narrowed where
ABSORBED (R-N (hz-rescaled), R-T (two-tower), R-L (longer budget); narrowed,
not closed) and not narrowed where NOT-SHOWN (none); the S3 word
K-2-ISOLATED (final) does not move.)

## OQ-18 — Does the COARSE-LABEL existence margin (L2 / L3) survive the full free baseline? — REGISTERED 2026-09-06, pre-run, critic-gated; PLAN OF RECORD item 1; LEAK RIDER AMENDED 2026-09-07 after the S1 L3 fire (dated note at the end of the entry)
Provenance: user decision 2026-09-06 ("Lets make this the plan, to the
L2 and L3 full-free re-test first, the oracle-intermediate ceiling
second and then assess where to go from there"). F-24 re-tested F-15 /
F-17 at L1 only and read ABSORBED at both sources; its errata say in
terms that L2 / L3 stand against the 657-summary proxy and are untested
against the full free baseline. The coarse-label margins over the proxy
are the largest in the record and grow with coarse-graining (all
linear cells; primary / replication): S1 L2 off2 +0.0277 / +0.0245, L3
off2 +0.0443 / +0.0427; S3 L2 off2 +0.0206 / +0.0207, L3 off2 +0.0721 /
+0.0730 (results/real/probes_*.json existence triples; recomputed by
the critic). The L3 lens is lopsided — S1: one mega-group of 455/510
concepts including all 165 zero-degree concepts; S3: two mega-groups of
268 and 193 = 461/510 including all 20 zero-degree concepts — and every
L3 statement is read through it.
Protocol (docs/BLUEPRINT.md "OQ-18 COARSE-LABEL FULL-FREE RE-TEST
REGISTRATION", 2026-09-06, written before any registered cell ran and
amended on critic review before the freeze commit): the OQ-17 design at
L2 and L3 — arms fplus = (a) ++ TOK ++ hz, fplus_b = fplus ++ aligned
telemetry, fplus_r = fplus ++ the CORRECTED prompt-level-deranged twin
(label-inert by construction, not accuracy-inert; the construction
F-24's diagnostic found TWIN-ROBUST; the OQ-17 shift twin is not used);
fresh (a) cells at mlp256 (Phase 3 ran L2 / L3 at linear only); offsets
bound per space to the cells that fired on both harvests (S1 L2 {2,3},
S1 L3 {2,3}, S3 L2 {2,3}, S3 L3 {2,3,4}); a per-space leak rider with a
fresh shuffled (a) reference (a failed leg halts the run and leaves the
source label-less); a THREE-leg reader-validity precondition (twelve
probes on the floor; Mf against the fresh (a); Mf_x against the
COMMITTED linear (a) — the leg a reader collapsed to the constant
predictor cannot pass); gate off2 / mlp256 D = acc(fplus_b) -
acc(fplus_r) under the Phase-3 triple rule; labels per (source, space)
from both harvests: SURVIVES-FULL-FREE / SPLIT / ABSORBED / NOT-SHOWN /
READER-INVALID with OFF3 / OFF4 horizon notes; Mt AND Mn_r quoted beside
D, the license FULL only with both uppers >= 0 on both harvests;
helps-direction readings pinned; consequence rules per label pinned
there (SURVIVES = dated STATUS lines on F-15 / F-17 and K-2 scoping the
F-24 kill to L1 and date-superseding K-2's "anywhere" sentence;
ABSORBED = dated erratum extension and the K-2 kill extended to L_k at
the registered reader; NOT-SHOWN / SPLIT = OPEN; READER-INVALID = dated
reader amendment first). Honest prediction pinned there before the
smokes: S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2 ABSORBED, S3 L3 SURVIVES
at off2 with D +0.005..+0.020. Instrument: tools/run_fullfree_coarse.py
(+ tests/test_fullfree_coarse.py); evidence results/real/
fullfree_coarse_{s1,s1_r,s3,s3_r}.json + state files. CRITERION-BEARING
for F-15 / F-17 at their L2 / L3 cells; touches neither conversion nor
the L1 verdict.
(Dated note, 2026-09-07: the S1 primary registered run HALTED on LEAK
RIDER leg 2 at L3 (shuffled fplus_b 0.5314 > shuffled fplus 0.5182 +
0.01, excess +0.0132); per the registration S1 went label-less. The
registered diagnostic (docs/OQ18_RIDER_DIAGNOSTIC.md, written before
any diagnostic cell trained and critic-gated before its verdict was
read; evidence results/real/oq18_rider_diag_s1.json + state file) read
branch AMENDABLE, mechanism TWIN-MATCHED, no qualifiers: the fire
reproduces exactly (raw leg 2 +0.0132 / +0.0136 / +0.0141 at seeds
0-2) and decomposes, pooled, into +0.0092 of prediction-marginal drift
and +0.0045 of dependence excess that the equal-dims prompt-deranged
twin mostly shares, leaving a twin-referenced residual dE_br of +0.0018
pooled (CI95 -0.0004..+0.0039) and +0.0026 at seed 0 (CI95 -0.0004..
+0.0054); X_raw at seed 0 +0.0006. Its pinned prediction (B /
MARGINAL-DRIFT) held on the branch and on dE_br and failed on the
mechanism (dE_bf CI-clear by +0.0001) and on the seeds-1/2 clause. The
rider's leg 2 was AMENDED (BLUEPRINT dated amendment of this date):
the twin-referenced dependence-excess leg replaces the raw
dims-asymmetric comparison at all four harvests, a post-hoc reroute
around a fired kill condition, disclosed in those words on every label
read under it; instrument tools/run_fullfree_coarse_amended.py (new
file; the frozen instrument stays byte-identical). S1 primary resumed
from its committed state file (30 unshuffled L2 cells reused, the
shuffled rows re-trained with the prediction dump; licensed by the
diagnostic's L2
seed-0 amended leg, dE_br +0.0005, CI95 -0.0001..+0.0011), S1
replication fresh, S3 payloads preserved as *.rider_v1.json and never
concluded, their runs resumed under the amended instrument. The
amendment was written 2026-09-07 and COMMITTED 2026-09-13 after a
session interruption (API rate limit mid critic round); both frozen S3
runs finished in the interval, so the S3 replication's v1 payload
records 15c4e9c-dirty over the three then-uncommitted amendment
documentation files (disclosed in the BLUEPRINT bullet; instrument sha
frozen). A registered POSITIVE CONTROL (docs/OQ18_RIDER_POSCONTROL.md:
the amended leg against a literal non-causal slots block read at the
shuffled label's own position) runs BEFORE any amended cell trains;
DOMINANCE-FALSIFIED withdraws the amendment, its outcome is recorded
in the BLUEPRINT bullet.
Outcome (2026-09-13): DOMINANCE-CONFIRMED-HERE; dE(leak - fplus_r)
+0.3007 at L3 (CI95 +0.2914..+0.3106) and +0.2493 at L2 (CI95
+0.2360..+0.2614); raw +0.2833 / +0.0928; the amended runs proceed.
Nothing else in the registration changed; the
honest prediction stands.)
OUTCOME (2026-09-14, F-25): [read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] S1 L2 ABSORBED; S1 L3 NOT-SHOWN; S3 L2 ABSORBED; S3 L3 SPLIT (every L3 label read at the L3 group lens (S1: one mega-group of 455/510 concepts including all 165 zero-degree concepts, the next group 10; S3: two mega-groups of 268 and 193 = 461/510 including all 20 zero-degree concepts)) at the registered reader — S1 L2 gate D +0.0011 [-0.0001, +0.0023] / +0.0006 [-0.0007, +0.0020]; S1 L3 gate D +0.0010 [-0.0006, +0.0026] / +0.0012 [-0.0015, +0.0040]; S3 L2 gate D +0.0018 [+0.0008, +0.0030] / +0.0003 [-0.0009, +0.0013]; S3 L3 gate D +0.0041 [+0.0026, +0.0055] / +0.0053 [+0.0019, +0.0091]. Prediction 3/4 held (S1 L2 predicted ABSORBED, read ABSORBED (held); S1 L3 predicted NOT-SHOWN, read NOT-SHOWN (held); S3 L2 predicted ABSORBED, read ABSORBED (held); S3 L3 predicted SURVIVES-FULL-FREE, read SPLIT (FAILED)). Consequences executed per the pinned rules (dated errata / STATUS lines on F-15 / F-17, K-2 STATUS, F-16 / F-18 notes where ABSORBED). OQ-18 is CLOSED as a question; the plan of record proceeds to OQ-19. SUB-CLAUSES of the pinned prediction, scored: S1 L2 gate D within +/-0.003 of zero HELD (+0.0011 / +0.0006); every D upper below the floor HELD; Mt +0.002..+0.006 FAILED on the primary (+0.0015) and HELD on the replication (+0.0022). S1 L3 gate D point below +0.005 with at least one D upper at or above it HELD. S3 L3 SURVIVES at off2 with D +0.005..+0.020 on both harvests and Mt positive FAILED (read SPLIT: primary D +0.0041, replication Mt -0.0014); OFF3-NOT-SHOWN or OFF3-SURVIVES HELD (OFF3-SURVIVES); OFF4-ABSORBED FAILED (OFF4-NOT-SHOWN: replication off4 D +0.0035 [+0.0009, +0.0064]). Mf CI-clear positive at every gate cell HELD (lowers S1 L2 +0.0371, S1 L3 +0.0804, S1_r L2 +0.0350, S1_r L3 +0.0724, S3 L2 +0.0268, S3 L3 +0.0830, S3_r L2 +0.0219, S3_r L3 +0.0765). S3 L3 SPLIT was named in advance among the outcomes that would surprise. RIDER REPORT and POST-HOC READING: see the F-25 entry's '- amendment:' and '- post-hoc reading:' lines (registered raw leg 2 above its band at S1 L3 and at S1_r L2, amended leg passing everywhere, the S1 L3 pass not CI-clear; the S3 L3 replication fire is written, in the pinned words, at equal dims inflated by up to |Mn_r| by the twin's own cost, Mt not CI-clear either way).

(2026-10-05 dated note: the S3 L3 SPLIT above and the S3 L1 kill of F-24 are
re-tested under two further readers and, at L3, through a balanced lens, in
"READER-AND-LENS RE-TEST AT S3 REGISTRATION" (docs/BLUEPRINT.md; the
operator's fold of 2026-10-05); the full-free label at the balanced lens is
written beside this entry's SPLIT as a dated note at landing, with Mt and Mn_r
beside D as F-25 pins; the lopsided-lens number stands as registered.)

(2026-10-05 OUTCOME, STAGE LENS of the reader-and-lens re-test (F-28):
through the balanced lens the S3 L3 cell reads ABSORBED at the registered
reader — D +0.0019 [+0.0006, +0.0032] / +0.0004 [-0.0011, +0.0018], Mt
+0.0042 [+0.0025, +0.0061] / +0.0021 [+0.0002, +0.0041], Mn_r +0.0023
[+0.0010, +0.0038] / +0.0017 [-0.0000, +0.0035] (the corrected twin
point-positive on both harvests, CI-clear on the primary only, where it cost
at the lopsided lens), OFF3-ABSORBED, OFF4-ABSORBED — written beside this
entry's SPLIT as the dated note; the SPLIT at the lopsided lens stands as
registered; the stronger readers are STAGE READERS, not yet run.)

(2026-10-05 OUTCOME, STAGE READERS (F-28): the S3 L3 cell under the stronger
readers reads, at the lopsided lens, R-N (hz-rescaled) SURVIVES-STRONGER
(EQUAL-DIMS-ONLY, the twin's larger cost) and R-T (two-tower) ABSORBED, and
at the balanced lens R-N (hz-rescaled) NOT-SHOWN and R-T (two-tower)
ABSORBED (D rows in F-28); K-2 at S3 L3 stays OPEN at the registered reader;
the K-2 word at S3 K-2-ISOLATED.)

(2026-10-09 OUTCOME, STAGE READERS-LONG (F-28): the S3 L3 cell under the
longer-budget reader reads, at the lopsided lens, R-L (longer budget)
SURVIVES-STRONGER (EQUAL-DIMS-ONLY, inflated by the twin's own cost) and at
the balanced lens ABSORBED (D rows in F-28); K-2 at S3 L3 stays OPEN at the
registered reader; the FINAL K-2 word at S3 K-2-ISOLATED.)

## OQ-19 — Oracle-intermediate CEILING: do the TRUE tap-layer activations carry future-concept information beyond the full free baseline at all? — PLAN OF RECORD item 2 (2026-09-06); design pinned in outline; registration block owed before its harvest launches — SKIPPED (operator, 2026-10-11; dated note at the end of the entry)
Provenance: the same 2026-09-06 decision, after the discussion of
whether information was "left on the table" with S2 or in a
comparison of the three telemetry readings. THE POINT: the S1 and S3
telemetry sources are LOSSY VIEWS of an intermediate activation of the
same forward pass (S1: the MLP intermediate at the four tapped
down_proj layers, a function of the residual stream entering that MLP;
S3: the router's expert choice, a function of the residual stream
entering that MoE layer), while the full free baseline holds that
forward pass's FINAL state h_a exactly (F-23). A lossy view cannot carry
information its source does not, so the TRUE activation at a tapped
layer bounds, IN INFORMATION, every sketch of it and every union of
sketches across such sources (a "comparison of the three readings" is a
union arm, not a separate readout — a nonlinear reader of the union
sees the interactions). Measuring that bound first tells us whether
there is anything for a sketch to recover before any sketch or union
is built. Scope of the bound, pinned on critic review (2026-09-06):
(1) it is an information bound, NOT a bound on a fixed reader's
accuracy — the in-repo counterexample is OQ-17 (iv), where raw 4096-dim
h_a sat below the floor at linear while the 657 summaries of the same
p_a read fine — so every OQ-19 label is scoped to the registered reader
like every other label in this arc; (2) it does NOT cover S2: the
attention pages depend on the K cache of EARLIER positions, which the
anchor position's residual input does not determine, so P8 keeps its
own free-twin design and is not gated on OQ-19's label.
Design outline (firm; the remaining constants are pinned in the
BLUEPRINT block before the harvest launches): (i) RE-HARVEST per source
under the registered generation regime, storing, beside everything the
registered harvesters store, the residual-stream INPUT to the tapped
module at REGISTERED layers (S1: two of the four tapped layers 7 / 15 /
23 / 31, mid and late, chosen at registration from the metas with the
storage budget disclosed; S3: two of the sixteen router layers,
likewise), float16, sha-bound metas — the quantity the sketch is a
function of. bf16 kernels are not bit-deterministic, so this is a NEW
population and every arm is re-measured on its rows (no cross-harvest
pairing). (ii) ARMS: fplus, fplus_b, fplus_r (the OQ-18 arms, so the
sketch margin D is re-measured on the same rows), plus fplus_o = fplus
++ oz (the oracle block: the stored activation clipped to the TRAIN
support and z-scored with TRAIN moments, the hz rule) and fplus_o_r =
fplus ++ the same block read from the prompt-level-deranged row (the
equal-dims twin, the OQ-18 construction). (iii) READOUTS per label
space (L1, L2, L3) at off2 / mlp256, horizons off3 (off4 on S3 L3):
D_o = acc(fplus_o) - acc(fplus_o_r) (THE gate), Mt_o = acc(fplus_o) -
acc(fplus), D (the sketch, same rows), and the SURVIVAL FRACTION D /
D_o where D_o fires (the OQ-6 ratio at the existence layer: how much of
the oracle headroom the address stream recovers), with a cluster-
bootstrap CI over the same 30 test prompts via sideband.stats.
paired_ratio_delta_ci. (iv) LABELS per (source, space) from both
harvests, the OQ-17 / OQ-18 rules with the names HEADROOM (D_o fires
both) / SPLIT / NO-HEADROOM (every D_o upper < +0.005 both) / NOT-SHOWN
/ READER-INVALID (the OQ-18 three-leg precondition, with oz in place of
the telemetry block for the floor leg) / INCOMPLETE. (v) CONSEQUENCES:
NO-HEADROOM at every (source, space) — at the registered reader the
S1 / S3 sketch questions and the same-model union (docs/FUTURE_IDEAS.md [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
P9) CLOSE: no sketch of these layers and no union of them can beat the
full free baseline THERE, and the only open path on the existence layer
is the stronger-reader residual (the D-2-named oracle is observability-
violating and never a deployable source); a sketch-D fire on the same
rows with D_o null is a READER ARTIFACT (the sketch's encoding suits
this reader better than the raw activation does) and routes to the
stronger-reader path, never to a sketch-beats-oracle claim. HEADROOM at
a (source, space) — the table is MEASURED (D_o beside Mt_o), the sketch
margins from OQ-17 / OQ-18 are re-read as survival fractions of it, and
P9 becomes a live candidate for that headroom, with EAGLE-3
(docs/PRIOR_ART.md: multi-layer target features as draft input) named
as the deployable form of the ceiling — a positive result re-derives
its premise. (vi) READER: the registered reader, symmetric scope, with
the stronger-reader residual named under both labels. Cost: one
harvest per source (GPU, model forward; the S1 regime is 8 seeds x 210
prompts, the S3 regime 5 x 210 (dated correction 2026-09-14: 8 x 210, moe_s0..s7)) plus probe cells; storage pinned at
registration. Honest prediction: pinned in the BLUEPRINT block before
the harvest launches, not here. NOT launched until OQ-18's labels are
read (plan of record order).
(2026-10-01 dated note: STATUS UNFROZEN DRAFT, UNDECIDED. The BLUEPRINT
registration block this entry defers to was drafted on 2026-09-06/07
(three pre-run critic rounds recorded at its end) together with the
instrument, but the 2026-09-07 session ended at the rate limit, the same
night the OQ-18 leak rider fired and took the lane, before the block was
inserted into docs/BLUEPRINT.md or anything was committed. The draft was
rebuilt from that session's transcript on 2026-10-01 and is committed
VERBATIM as docs/OQ19_ORACLE_CEILING_DRAFT.md, with the instrument files
src/sideband/real/oracle_replay.py, tools/run_fullfree_oracle.py and
tests/test_fullfree_oracle.py each carrying a DRAFT banner. Nothing of
OQ-19 has run; no freeze commit exists; docs/BLUEPRINT.md holds no OQ-19
block. The post-F-25 review of 2026-09-14 recommended skipping OQ-19 or
shrinking it to a pilot; the owner has not decided; the lane went to OQ-9
stage 1 (F-26) instead. What a freeze would still owe is listed in the
draft file.)
(2026-10-11 dated note: SKIPPED. The operator's decision of 2026-10-11 is
to skip OQ-19: no freeze commit, no registration block, no harvest. The
draft stays as committed on 2026-10-01, unchanged except for dated notes
like this one (docs/OQ19_ORACLE_CEILING_DRAFT.md
and the three instrument files with their DRAFT banners; DRAFT_UNFROZEN
stays True in tools/run_fullfree_oracle.py, with the run refusal that
tests/test_fullfree_oracle.py pins). Nothing of OQ-19 has run, so the
question carries no label and no finding rules on it; the ceiling it was
to measure stays unpriced.)

## OQ-20 — Cross-seed replay of the two conversion-verdict legs: how far does a verdict's tokens/call delta move when the same frozen policies are re-run at a new seed? — REGISTERED 2026-10-09 (pre-run; NON-CRITERION; the freeze follows the critic's design round)
Provenance: F-27 (2026-10-04) measured the seed-to-seed noise of VANILLA
tokens/call on the committed runs and named, in docs/NOISE_FLOOR.md and
README, what it left unmeasured: "the record's verdict arms' own
cross-seed variance" and "the same-seed null the gate legs faced". The
operator approved this readout on 2026-10-09 after the assistant's
assessment of what F-27 left open, and confirmed the pins (seed 6 with
seed 7 reserved, both populations, the stage words). THE POINT: every
conversion verdict in the record (F-19, F-21) is an all-comparator rule
over legs that are each a DELTA between two arms at ONE seed, read
against a prompt-cluster CI; F-27 priced how far vanilla alone moves
across seeds — plausibly (argued, not measured) an upper bound on the
same-seed null, and only for a policy whose per-prompt variance does not
exceed vanilla's, which F-21's leg already exceeds (half-width 0.045723
against 0.0398) — and it says nothing about a delta's own seed-to-seed
spread. This question replays each verdict's VS-VANILLA leg — K-3 arm 1
and arm 4 (the (c)-probe scheduler under its re-frozen v2 thresholds;
F-19's leg +0.006860 [-0.015024, +0.025572] at seed 1) on the K-3
prompts, OQ-15 arm 1 and arm 7 (C4 head_tel under its v2 thresholds;
F-21's leg +0.002664 [-0.044719, +0.046727] at seed 3) on the OQ-15
prompts — and, by the operator's pre-freeze amendment A1 (2026-10-09,
"add"), each verdict's mechanism-matched FREE leg too (K-3 arm 3, the
(a)-probe free scheduler, F-19's arm 4 vs arm 3 +0.006974 [-0.014909,
+0.025690]; OQ-15 arm 6, head_free, F-21's decisive arm 7 vs arm 6
-0.081846 [-0.132484, -0.035567]) — at ONE new seed, 6, six runs in all,
and reads (R1) the vs-vanilla leg at the new seed with the budget guard
as a label, (R2) its cross-seed difference with the label
MUTUAL-COVERAGE / DELTA-MOVES and a pinned reading from that label and
the difference's CI, (R3) the bar at the new seed as a pre-registered
surprise, never a WIN, (R4) F-27's reliability on the two new vanilla
seed pairs with the label R-CONSISTENT / R-SHIFTS, and (R5-R7, A1) the
same three readings for the free leg plus (R8) the free arm vs vanilla
as a description (NEAR-IDENTICAL-ARMS where the two arms barely differ,
as K-3's arm 3 does; no bar, no guard; not rank 9's closure readout);
the stage words over both populations SPREAD-COVERED / SPREAD-SPLIT /
SPREAD-MOVES over R2 and FREE-SPREAD-... over R6. One new seed gives one
realised cross-seed difference per leg, not a variance estimate; the
draft_conf legs are not replayed, a replayed free leg describes the
verdict's own comparison at one more seed and tests nothing about
telemetry over free information, and the same-seed null the gate legs
faced stays unmeasured here too. Design, pins, the honest prediction,
void semantics and consequences: docs/BLUEPRINT.md, "SEED-REPLAY OF THE
CONVERSION-VERDICT LEGS REGISTRATION (2026-10-09)". Instruments:
tools/run_k3_arms.py for the six GPU runs from a clean clone of the
launch commit (not byte-pinned; a pinned token-exact replay of the first
prompts at the old seeds gates the launch), tools/run_seed_replay.py for
the CPU readouts (tests/test_seed_replay.py; the one new estimator in
sideband.stats). Cost about 4.4 GPU-hours. NON-CRITERION for F-19, F-21
and F-27; no wall-clock sentence (D-9).

(2026-10-10 OUTCOME: the six seed-6 runs from the clean clone of the launch
commit b6d3701, the two CPU readouts from the clean tree at c62f03d;
SPREAD-COVERED over R2 and FREE-SPREAD-COVERED over R6 — K3 R1 +0.010340
[-0.009288, +0.030521] GUARD-HELD, R2 MUTUAL-COVERAGE / REPRODUCES
(difference -0.003479 [-0.033416, +0.022758]), R5 +0.010109 [-0.009724,
+0.030422] GUARD-FREE-HELD, R6 MUTUAL-COVERAGE / REPRODUCES (difference
-0.003135 [-0.033327, +0.023051]), R8 NEAR-IDENTICAL-ARMS; OQ15 R1 -0.018029
[-0.065168, +0.028495] GUARD-HELD, R2 MUTUAL-COVERAGE / REPRODUCES
(difference +0.020693 [-0.044830, +0.088277]), R5 -0.053623 [-0.107526,
-0.002448] GUARD-FREE-HELD, R6 MUTUAL-COVERAGE / REPRODUCES (difference
-0.028223 [-0.099002, +0.042346]), R8 DELTA-MOVES / WITHIN-CROSS-SEED-NOISE;
R3 / R7 BAR-NOT-CLEARED / BAR-NOT-CLEARED-FREE and R4 R-CONSISTENT on both.
R2's and R6's CI95 half-widths on OQ15, 0.0666 and 0.0707, both exceed the
+0.062 bar, so a cross-seed move the size of the bar is not resolved there,
as the registration said it would not be (on K3 they are 0.0281 and 0.0282);
on K3 the free leg is nearly the vs-vanilla leg (|R5 - R1| = 0.000231), so
the two stage words are not two confirmations there. One further seed per
leg, one realised cross-seed difference each: the cross-seed variance stays
unestimated, the draft_conf legs and the same-seed null unmeasured;
NON-CRITERION, no verdict moves. F-27's STAGE REPLAY line carries the
readouts; the block's OUTCOME scores both predictions (the assistant's 2 of
3 modal labels, the critic's 22 of 22 scored clauses; both predictors called
OQ15's R8 MUTUAL-COVERAGE and both missed — the assistant's modal clause
FAILED, the critic's clause was calibration at about 0.8 and reads against);
tests/test_seed_replay_landing.py pins the labels and both stage words;
tools/run_seed_replay.py joins the frozen closure.)

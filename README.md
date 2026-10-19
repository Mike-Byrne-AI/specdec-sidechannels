# specdec-sidechannels

Three research records about what a speculative-decoding system gives away for
free, published together as they stood at their pinned commits.

When a large language model generates text, a small draft model can propose
several tokens at once and the large model, the verifier, checks them in one
pass; the verifier's rejection rule keeps the output exactly its own, so a
better draft buys speed and never changes a result. Something also has to
fetch the large model's weights, and whatever serves them, a memory device or
a tier holding a mixture-of-experts model's experts, sees which weight groups
or experts each token touched, as a byproduct, without reading an activation
value or a logit. sideband, the central experiment, asked whether that
address stream tells the draft model anything the decoder does not already
have, and whether it converts into more emitted tokens. amber asked whether
the draft model's rank corrections toward target-generated text make a
byte-exact archive of that text. lockstep built a pure-integer coder with
conformance vectors, which amber carries as an option, and proposed the
model-pinned container such an archive would need.

The answers are negative or narrow. sideband tested two streams, S1, a
value-aware tap on a Llama-3.1-8B target, and S3, the pure address stream of
an OLMoE model's routers (both described in the next section). Its probes do
find a small signal: at the pinned L1 cells, with a linear probe, the stream
raises top-1 accuracy at predicting the concept bucket of the token two
positions ahead by +0.0141 at S1 (the replication harvest) and +0.0147 /
+0.0173 at S3 (primary / replication) over a summary of what the decoder
already knows (F-15, F-17). Against the fuller free baseline the record then
built (the logged summaries of the target's next-token distribution, its
hashed top-32 token ids and its anchor hidden state, as this pipeline
encodes them), read by the registered reader mlp256, the stream's own margin
at those L1 cells is about +0.003 (F-24's words), under the +0.005 floor set
in advance, and no material amount more than a scrambled block of the same
size adds; at L2 the same reading holds (F-25, read under a rider amendment
the record calls "a post-hoc reroute around a fired kill condition"); three
stronger probe readers, run later at both sources, did not overturn the L1
result (F-28 at S3, where they also read the L3 lenses; F-29 at S1), and L3,
the grouped label space, stays open at both. At S1 two registered attempts
to convert the signal into emitted tokens per verify call were null against
the bar set in advance (F-19, F-21), and the hidden state its reconstruction
lane targeted is an exact function of the target's own next-token
distribution, free information (F-23); conversion and reconstruction were
never run at S3.
amber's codec decodes its archives byte-exactly under an fp32 contract on
one box (200 of 200 on the GPU, 24 of 24 on the CPU), and its errata pass
corrected 16 of the 21 claims it checked. lockstep's byte-model coder and
its conformance vectors stand; the model-backed profile was never built,
and the economics behind it did not survive measurement.

How the work was run, and by whom. Every real-model run in sideband was
registered before its data and gated by kill criteria written in advance,
and from Phase 3 on had its labels recomputed from committed state files and
per-prompt summaries by an adversarial reviewer; every record is corrected
by dated errata, never rewrites, and names its own exceptions (listed under
"How the work was run" below). One human researcher set the questions, the
kill criteria and every launch, void and close decision; an AI coding
assistant (Claude Code) built the instruments, ran the analyses and drafted
the registrations, the findings and the documentation, this file included;
and the adversarial reviewer, the "critic" named throughout, is a second AI
agent of the same model family as the assistant, run as its subagent: not a
human, and narrower than an independent reviewer (its body is
`sideband/.claude/agents/sideband-critic.md`; what it caught is in
`sideband/docs/METHOD.md` section 6 and what it cannot in section 7, and a
recovered selection of its rounds of the harness era is under
`sideband/docs/audits/critic-recovered/`); the human arbitrated. What this
repository is, and what it leaves out, is stated below the three parts.

Terms this file uses, one line each (full entries in
[sideband/docs/GLOSSARY.md](sideband/docs/GLOSSARY.md)):

- Free baseline: what any speculative decoder already has at the last
  verified position (sideband D-5); every margin is measured over it. The
  proxy free baseline is a 657-number summary of the target's next-token
  distribution; the full free baseline adds its hashed top-32 token ids and
  its anchor hidden state.
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
- ABSORBED, NOT-SHOWN, SPLIT, SURVIVES-STRONGER, EQUAL-DIMS-ONLY,
  K-2-ISOLATED, K-2-NOT-OVERTURNED-AT-S1: the pinned conclusion labels, each
  linked to its glossary entry where it appears below. ABSORBED means no
  material margin over the full free baseline at the +0.005 floor, never
  "no margin".
- Never run is never read as a null: a stage that did not run (conversion
  and reconstruction at S3; the KV-page stream S2) is reported as unrun.
- Tokens per verify call: the currency of conversion; the bar, +0.062 tokens
  per call over every comparator arm, vanilla included, was pinned on
  2026-09-01 before any conversion run.

| Folder | What it is | Where it ended |
|---|---|---|
| `sideband/` | Can the memory-access address stream a weight-serving device sees for free steer a speculative-decoding drafter enough to matter? | Existence ABSORBED by the full free baseline at the pinned cells, with the L3 cells left open (S1 L3 NOT-SHOWN, S3 L3 SPLIT); conversion not shown in two registered attempts at S1; the reconstruction target at S1 proved to be free information. The table below carries the record's own words per layer and source |
| `amber/` | Archives of model-generated text coded as a draft model's rank corrections, decoded with the draft alone, byte-exact under a measured contract | A codec with a measured rate, a decode contract shown sufficient on one box, and an errata pass that corrected 16 of the 21 claims it checked |
| `lockstep/` | A pure-integer arithmetic coder with conformance vectors, and a proposed model-pinned archive profile | The byte-model coder and its vectors stand; the model-backed profile was never built and the economics behind it did not survive measurement |

The three records cite each other. sideband's `docs/DECODE_CONTRACTS.md`
reads the other two folders' committed payloads; its Sources table cites
amber's files by git blob id, which `git hash-object <file>` reproduces
from the amber folder because the export keeps file contents, a check the
export's fresh-clone proof runs.

## The question and the answer

The rejection scheme of speculative decoding guarantees that the output
distribution is the target's, so steering the drafter can change speed but
never outputs (sideband F-0 and F-1: worst closed-form deviation 2.2e-16).
sideband tested two streams. S1 is a value-aware
compute-tier tap on the Llama-3.1-8B-Instruct target: at four layers, the
slot ids of the top-32 units ranked by activation magnitude times
weight-column norm, hashed into 512 slots; it needs activation values to
rank the units. S3 is "the PURE ADDRESS-STREAM source the original
hardware premise named" (F-17): OLMoE-1B-7B-0125-Instruct's own
top-8-of-64 expert ids at each of its 16 gates, addresses only, no router
logits, no values. Existence was tested at both sources. Conversion and
reconstruction ran at S1 only; at the pure address stream they were never
run, and this file reads them as unrun, not as nulls, under the record's
rule that a stage never run is never read as a null. Three layers are
never conflated.

Seven kill criteria were written before the data
(`sideband/docs/WHY_THIS_DIES.md`, dated STATUS blocks appended as each fired
or stood): K-1 (rejections are not cross-bucket) did not fire (F-10); K-2
(telemetry adds nothing beyond free information) FIRED at the registered
reader at the pinned L1 cells of both sources (F-24) and at L2 (F-25, read
under a rider amendment the record calls "a post-hoc reroute around a fired
kill condition"), each with the +0.005 materiality scope, with L3 open at both
sources, the final word at S3 under three stronger readers
[K-2-ISOLATED](sideband/docs/GLOSSARY.md#k) (F-28) and the word at S1 under
the same three readers
[K-2-NOT-OVERTURNED-AT-S1](sideband/docs/GLOSSARY.md#k) (F-29); K-3 (probe margins do not
convert to acceptance) FIRED at Attempt #1 (F-19) and stayed fired through
fold-back #1 (F-21) and the dated closure of fold-back #2 (F-23); K-7 (the
glue-bucket tax) did not fire as written, while its gate-health diagnostic
fired and was re-routed to OQ-12 (F-11 to F-14); K-4, K-5 and K-6 are
UNTESTED. The conclusion labels linked in this file each have a headed entry
under their letter in [sideband/docs/GLOSSARY.md](sideband/docs/GLOSSARY.md):
[ABSORBED](sideband/docs/GLOSSARY.md#a),
[NOT-SHOWN](sideband/docs/GLOSSARY.md#n),
[SPLIT](sideband/docs/GLOSSARY.md#s),
[SURVIVES-STRONGER](sideband/docs/GLOSSARY.md#s),
[EQUAL-DIMS-ONLY](sideband/docs/GLOSSARY.md#e),
[K-2-ISOLATED](sideband/docs/GLOSSARY.md#k),
[K-2-NOT-OVERTURNED-AT-S1](sideband/docs/GLOSSARY.md#k), and the prefetch and
noise-floor labels, linked where they appear.

| Layer and source | Question | Verdict, in the record's words | Headline numbers | Where |
|---|---|---|---|---|
| Existence, S1 and S3 | Does the stream carry future-concept information the decoder does not already have? | shown against the proxy free baseline, replicated on fresh seeds (F-15, F-17). At the registered reader the full free baseline ABSORBS the margin at the pinned L1 offset-2 cell of both sources (F-24: every equal-dims D CI95 upper below +0.005 at those cells). At the coarse label spaces: S1 L2 [ABSORBED](sideband/docs/GLOSSARY.md#a), S1 L3 [NOT-SHOWN](sideband/docs/GLOSSARY.md#n), S3 L2 ABSORBED, S3 L3 [SPLIT](sideband/docs/GLOSSARY.md#s) (F-25). Under three further readers at S3 the final word is [K-2-ISOLATED](sideband/docs/GLOSSARY.md#k): two [SURVIVES-STRONGER](sideband/docs/GLOSSARY.md#s) cells at the lopsided lens, both [EQUAL-DIMS-ONLY](sideband/docs/GLOSSARY.md#e) (one "two costs", one "inflated by the twin's own cost"), at a lens "which never decides a reopen"; "no reopen-grade cell anywhere"; "one more family of readers, not K-2's universal" (F-28). Under the same three readers at S1 the word is [K-2-NOT-OVERTURNED-AT-S1](sideband/docs/GLOSSARY.md#k): R-N (hz-rescaled), R-T (two-tower) and R-L (longer budget) each read ABSORBED at the S1 gate cell (F-29). The record issues no all-space sentence. | proxy margins in top-1 accuracy at the pinned cells: S1 +0.0141 [+0.0081, +0.0203] (replication harvest); S3 +0.0147 [+0.0113, +0.0182] primary, +0.0173 [+0.0133, +0.0221] replication. The KV-page stream S2 is unrun. | `sideband/FINDINGS.md` F-15, F-17, F-24, F-25, F-28, F-29; `sideband/docs/WHY_THIS_DIES.md` K-2 |
| Conversion, S1 | Does that information buy emitted tokens per verify call at a matched drafting budget? | not shown: two registered attempts, both null against the bar "CI lower > 0 and point >= +0.062"; K-3 FIRED at Attempt #1. Never run at S3. | +0.006860 [-0.015024, +0.025572] vs vanilla (F-19); +0.002664 [-0.044719, +0.046727] vs vanilla and -0.081846 [-0.132484, -0.035567] vs the same head on free features (F-21) | `sideband/FINDINGS.md` F-19, F-21; `sideband/docs/WHY_THIS_DIES.md` K-3 |
| Reconstruction, S1 | How much of the verifier's anchor hidden state does a linear map recover from the stream? | qualified pass at the registered gate (F-22; the registered magnitude is inflated about 25% by two out-of-support test prompts), then closed by dated erratum: the target is free information, no partition branch claimed (F-23). Never run at S3. | delta_free +0.204984 [+0.153698, +0.288162]; the anchor hidden state follows from the anchor's full logits at relative error 2.5e-8 median | `sideband/FINDINGS.md` F-22, F-23 |

Every interval is a prompt-cluster bootstrap CI95: the probe tests over
the 30 held-out clusters of a pinned 150/30/30 split of a 210-prompt
harvest, the conversion verdicts over fresh 210-prompt populations, F-22
over 84 clusters. The model pair is Llama-3.1-8B-Instruct (NF4) as target
with Llama-3.2-1B-Instruct as draft, draft length 4 at the vanilla arm;
OLMoE-1B-7B-0125-Instruct for S3; one RTX 3080 Ti with 12 GB. No
wall-clock or speedup claim of sideband's own exists anywhere in its
record (D-9; its instruments log per-prompt seconds as provenance only),
and every speedup figure its record quotes is prior art's, not its own.
Wall-clock claims are banned because nothing in sideband is a benchmark
harness (the HF adapter crops KV caches by default, but every run is one
shared consumer GPU with no timing control), so the wall-clock criterion K-5 is
UNTESTED, as are K-4 and K-6; the boundary question K-6 asks was never
posed with a positive number in hand.

## The three parts

### sideband/

The experiment above, plus two side results. The seed-noise floor (F-27): a
same-policy seed change moves pooled tokens per call by a CI95 half-width of
0.0385 / 0.0398 at 210 prompts and 0.0982 / 0.1032 at 30 (the K3 / OQ15
populations); at 30 prompts a +0.062 point win appears by seed noise alone in
0.1060 / 0.1320 of subsets and a single comparator leg of the F-19 win rule
passes in 0.0235 / 0.0375. The labels:
[FLOOR-MATERIAL](sideband/docs/GLOSSARY.md#f) on both populations,
[BAR-RESOLVED@210, RULE-LEAKS@30](sideband/docs/GLOSSARY.md#b); a cross-seed,
same-policy, single-comparator null, the same-seed null unmeasured. The
prefetch read (F-26, a K-6 datum, not a criterion): on the OLMoE router stream
the next-forward expert-set hit rate at 16 of 64 resident experts is 0.9143 /
0.9108 (primary / replication, here and below) for routing history plus the
free token against 0.5197 / 0.5155 for a recency cache and 0.8111 / 0.8036 for
a one-token table alone ([PREFETCH-HEADROOM](sideband/docs/GLOSSARY.md#p)),
and the address block over the free input token alone
([ADDRESS-BEYOND-TOKEN](sideband/docs/GLOSSARY.md#a)) read +0.1032 / +0.1072
at that budget. The rungs that followed, each registered before it ran, carry
their own labels. The equal-dims free-bigram twin, +0.0609 / +0.0659:
"SURVIVES at THIS ENCODING". The generalising free baseline
([R2-FALLBACK-SURVIVES](sideband/docs/GLOSSARY.md#r),
[H-ABSORBS](sideband/docs/GLOSSARY.md#h)): "R2-FALLBACK-SURVIVES / H-ABSORBS",
where the margin over free token tables on the unseen-key positions "is NOT
shown to be table sparsity" while with "the forward's stored final-norm state
in the free arm" no material margin is shown ("absorbs" names the label, not a
mechanism), so "STAGE 2's ADDRESS-BEYOND-FREE MOTIVATION IS STRUCK". The
horizon read: [LEAD-TIME-ABSORBED](sideband/docs/GLOSSARY.md#l), where "OQ-9's
prefetch half closes at this reader" and "the datum points toward the
alternative, not the premise". That hidden state is the alternative K-6 names.
F-26's own words: nothing in it reads the margin "as support for the sideband
premise". K-6 stays UNTESTED.

What the folder holds: `FINDINGS.md` F-0 to F-29, each with a regime line
and a source line pointing at committed evidence, lint-enforced;
`DECISIONS.md`; `OPEN_QUESTIONS.md`; `docs/BLUEPRINT.md`, the registrations
appended before each run; `docs/WHY_THIS_DIES.md`, the kill criteria with
dated STATUS blocks; `docs/REPORT.md`, the technical report with its
scorecard; `docs/NOISE_FLOOR.md`; `docs/DECODE_CONTRACTS.md`, the note
harvested from the other two folders; `docs/METHOD.md`, how the research
was run; `results/`, the committed payloads and, for the registered
real-model runs from Phase 3 on, the per-cluster state files the intervals
recompute from; and the Espalier harness that gated changes from its
deployment on 2026-09-30 onward (`.claude/`, `tools/cc/`,
`ESPALIER_MEMORY.md`).

Reusable on its own: the exact verifier (`sideband/src/sideband/specdec.py`,
the Leviathan rejection scheme, the single source of verifier math in the
folder, its exactness checked against the closed form in
`sideband/tests/test_specdec.py`, F-0 and F-1); the prompt-cluster bootstrap and the
paired-ratio estimators (`sideband/src/sideband/stats.py`, deterministic,
numpy only); the findings lint that refuses an entry without a regime line
and tracked evidence (`sideband/tools/lint_findings.py`); the landing-text
kit that traces every numeral of a landing text to a payload field and
applies it by anchors in the file's own line ending
(`sideband/tools/landing_text.py`); the critic agent's body with its
recompute checklist (`sideband/.claude/agents/sideband-critic.md`) and the
hook code it ran under (`sideband/tools/cc/`; the per-machine wiring in
.claude/settings.json is not shipped); the method itself
(`sideband/docs/METHOD.md`) and the seed-noise-floor methods note
(`sideband/docs/NOISE_FLOOR.md`).

### amber/

An archive of target-generated text as the draft model's rank corrections,
encoded from the draft's teacher-forced logits over the target's text and
decoded by the draft alone, byte-exact under an fp32 contract; the draft codes
both ends and the target only generates (F-14 row E1, which corrected the
record's first line). Regime of the F-8 and errata figures: meta-llama/Llama-3.2-3B
as the target and meta-llama/Llama-3.2-1B as the draft, both base
checkpoints, greedy generation on one consumer GPU (F-8's regime line); the
F-11 archives are about 245 tokens each, decoded at fp32 with the gamma coder
and the escape off, and E18's recomputes ran on the CPU. Over 48,958
generated tokens, greedy divergence is 6.78% and
amber v0 codes the text at 0.4738 bits per token against 0.4723 for
arithmetic coding under the draft and 3.618 for zstd-19 on the same text
(F-8). The tie with arithmetic coding is a mixture: 125 of 200 rows end in an
exact periodic tail covering 60.7% of the generated tokens (row E3), and on
the rows without loops amber reads 0.8929 against 0.8094 bits per token, on
the looped rows 0.2515 against 0.2937 (row E4). Split the same way on
2026-10-18 (amber's results/diagnostics_2026-10-18/p1_stratified.json, from the
script beside it), greedy divergence on the rows without loops is 13.40% and
zstd-19 on their text 7.492 bits per token, so amber's multiple over zstd-19
there is 8.39x against the headline 7.64x. The zstd baselines were
strawmen at the per-archive scale: with a 16 KB dictionary trained on the
other half of the same prompt families, amber's per-archive advantage is
1.06x (1.62x without the dictionary), the content-level multiple on
concatenated generated text is 7.9x with a dictionary, and on the held-out
rows whose repeat share is below one half amber v3 reads 5.10 against 10.26
for dictionary zstd (F-16 row E18). What holds is narrower and exact: under
the fp32 contract 200 of 200 archives decode byte-exactly on the GPU and 24
of 24 on the CPU, while bf16 decoders fail 84% of archives and fp16 decoders
28.5% (F-11); both are rates for decoders of a different dtype than the fp32
encoder (amber's P4 protocol), and say nothing about a same-dtype bf16
contract, which ts_zip's page states its model achieves deterministically
across GPU and CPU models (F-11's two dated notes of 2026-10-18). Real
archives carry no attestation (row E12). The errata pass
(F-14 to F-16, rows E1 to E19) corrected 12 of 16 checked claims in its first
batch with 4 confirmed, 2 of 2 in its second, and 2 of 3 in its third with 1
confirmed, each row recomputed under a rule pinned before the recompute ran
(except E4, E7 and E13, decided through logged amendments, two of E17's
claim sites, decided after a revised dry run, and E19, labelled post hoc, as
F-14 and F-16 say) and re-derived by a second AI agent of the
same model family as the assistant, run as its subagent
(`amber/results/errata_critic/REPORT.md`).

What the folder leaves out, and what in it is third-party: its workflow file
is withheld (it names private repositories and a token); the patent passages
at four sites are withheld by marker, with the kill criterion K-1 and the
open question OQ-6 kept as structure; four mentions of private sibling
repositories are replaced by markers and a fifth, in a source file two
errata payloads pin by blob, stays as name-only residue; four
sibling-checkout paths in
`amber/docs/ERRATA_PLAN.md` are scrubbed; `amber/WITHHELD.md` lists each, and
`amber/docs/COMMIT_LOG.md` holds the private commit messages.
`amber/results/errata_web/` holds two saved arXiv abstract pages, F-14 row
E13's digest-bound evidence; they are arXiv's and the papers' authors'
content and are not covered by this repository's licence. The P1 shards and
the P4 to P6 archives under `amber/results/` are outputs of the Llama 3.2
checkpoints named in NOTICE. A rerun of the errata recompute from this folder
is partial by construction: of the 119 input entries its payloads pin, 28
name earlier versions of files and resolve only in the private history
(three of them `amber/pyproject.toml`, which the first front-door commit edited),
two name the private bytes of `amber/docs/PRIOR_ART.md`, which the patent
withhold edits, five rows read logit dumps that were never tracked, and in
this folder layout the recompute's provenance lookups record None (the audit
report's section A, items 5 and 6); on the author's machine, at 69b437c, the
instrument regenerated every non-network row of the three payloads with no
differing value (a refuter's dry run of 2026-10-17; the front-door commits
since changed no instrument, payload or result). A read-only
image audit of 2026-10-17 (`amber/docs/audits/2026-10-17-image-audit/README.md`:
nineteen agents, 141 findings, none refuted outright, 7 high survivors; no
finding's status word changed, while three pre-registered P3 band readings,
two reported as held and read as missed and one reported as not fired and
read as fired, and F-12's byte breakdown are among the survivors) lists the
sentences it found
overclaimed, F-13's turn-confinement clause and F-12's 97 B header figure
among them, as candidates for dated errata; none is landed in this cut.

Reusable on its own: the real-archive code (`amber/src/amber/real/archive.py`),
the synthetic-world codec (`amber/src/amber/codec.py`), the binary framing
(`amber/src/amber/binformat.py`; row E11 records an unfixed regression in
its declared-length check), the coder over lockstep
(`amber/src/amber/rac_codec.py`), the rank-flip census instrument
(`amber/src/amber/rankcensus.py`), and the errata protocol
(`amber/experiments/ERRATA_PROTOCOL.md`) with its recompute payloads.

### lockstep/

A pure-integer 32-bit arithmetic coder with bit-exact conformance vectors
for its byte-model profile lsp0, a container that pins coder constants and
every model parameter, and typed failure categories. The proposed
model-backed profile lsp1 was never built (F-19). The thesis it was for
did not survive measurement: packing is 92% of total cost under the cost
model's placeholder inputs (F-8); the pack rate measured at batch 1 is
0.0437 MB/s, a units slip of 114.5x in the earlier figure, which leaves it
460x short of the cost model's break-even (F-17). That break-even is itself
built from placeholder prices and ratios: across the record's own
alternative inputs the gap runs from 55x to 988x, and with any decode rate
the record measured in place of the cost model's decode placeholder, LLM
archiving costs more than zstd -19 even with packing free, so the verdict
that the standalone thesis loses survives while F-8's 92% does not (the
folder's audit report, item B3). On amber's logit dumps, the value contract
the profile rested on crosses a grid line at 22% of positions for
TinyLlama-1.1B and 41% for Llama-3.2-1B under fp32 cross-device drift
(delta 1e-3, top 64), and at 100% under bf16 or fp16 (F-12, F-13). What
holds instead is narrower than a pin on token order. On the teacher-forced
dumps an fp32 decoder "resolves 1 of 25,306 top-1 symbols wrongly (the
swapped pair 1.3e-5 apart) and every correction correctly"; its top-64
order differs from the CPU's at 379 positions, and at 2 of those "the
swapped tokens sat further apart than the record's fp32 pair budget of
8.6e-5, so not every order difference is a near-tie at that budget; none is
at the top slot"; at batch 8 there is "one desync in 49,056 positions at
every escape setting". On the archives themselves the fp32 decode read 0
failures over 54,810 replayed positions. The fp32 pin "is shown sufficient
for these archives on this box only" (F-18;
`sideband/docs/DECODE_CONTRACTS.md`). Those are amber's measurements, and
amber's payloads are primary (F-20).

What the folder leaves out: its own workflow file (a workflow in a
sub-folder never runs; the root workflow's lockstep job runs its five
validation commands); a planning document, whose one-sentence version
`lockstep/README.md` quotes, a review with six proposals for further work
(two of them later built), and engineering notes on patents and licensing,
each withheld whole; the body of TP-5, the two patent numbers with their
claim reading at two sites, two open questions on a commercial offering, a
prior-art section on market signals and the closing positioning paragraph,
each withheld by marker, the counsel sentences around them kept; two paths
into the amber checkout in TP-7, scrubbed. `lockstep/WITHHELD.md` lists each, and
`lockstep/docs/COMMIT_LOG.md` holds the private commit messages. The folder
ships the agent harness its record was kept with (`lockstep/.claude/`,
`lockstep/tools/trellis_*.py`), an earlier form of the one sideband ships;
its reference checker reads finding IDs in a form the record does not use,
so its repair gate's `refs` step checks none of the twenty findings. A read-only image
audit of 2026-10-18 (`lockstep/docs/audits/2026-10-18-image-audit/README.md`:
nineteen agents, 165 findings, 2 refuted outright, 25 high survivors in ten
distinct defects) found the two vector files breaking the conformance check
on a Windows git clone, which the folder's `.gitattributes` now prevents,
and lists F-2's half-step absorption boundary, F-6's drift model, the
economics' stated reason, F-15's "amber's production coder" and the
decisions' uniform [imagined] tag among the candidates for dated errata;
none is landed in lockstep's findings log.

Reusable on its own: the integer range coder `lockstep.rac`, which amber
carries as its long-stream coder option while keeping Elias-gamma as its
default (amber `DECISIONS.md`); the lsp0 conformance vectors, which
reproduced all 6 payload hashes byte-exactly on a second operating system
and CPython build (F-11) and from three encoders the audit's agents wrote
without importing lockstep (two of them by agents who had read the reference
code), under the reading of
`lockstep/specs/decode-profile-v0.md` the reference code follows (a reading
of its renormalisation sentence as three loops reproduces 1 of the 6), and
which do not exercise the adaptive model's rescale clause (no vector drives a
row total past 3,712 of the 32,768 limit, so a coder without the clause
reproduces the five adaptive-model vectors, the uniform sixth having no such
clause; lockstep's VALIDATION.md, dated note of 2026-10-18); and
the cost model (`lockstep/tools/lockstep_costmodel.py`), which prints its
lsp1 ratio and speed inputs as placeholders and gives no source for its
prices.

## What this repository is, and what it leaves out

This repository is a fresh-history export of three private
repositories, so the commit hashes the records cite refer to the private
histories; sideband's commit messages are kept in
`sideband/docs/COMMIT_LOG.md`, amber's in `amber/docs/COMMIT_LOG.md` and
lockstep's in `lockstep/docs/COMMIT_LOG.md`. The three records' registered
text, findings, decisions and evidence are as they stand in the private
records (what the amber and lockstep folders withhold is listed in their
sections above and in `amber/WITHHELD.md` and `lockstep/WITHHELD.md`). What the export changes (front doors rewritten to lead with
the question and the answer, partial withholds marked in place,
placeholders filled) and what it leaves out (the operator logs and session
scratch, the planning documents of this cut, the idea documents, and the
lockstep documents its folder withholds) are listed in WITHHELD.md.

## How the work was run

- Registration before data, in sideband: a run's cells, readouts and
  conclusion labels are pinned in `sideband/docs/BLUEPRINT.md` before it
  runs; post-hoc diagnostics are registered the same way, with their
  branches named before the read. The record names its own exceptions,
  among them: F-25 was read under a rider amendment written after the
  registered rider fired, in its words "a post-hoc reroute around a fired
  kill condition"; F-25 and F-26 each carry a post-hoc reading marked
  "written AFTER the labels were read; NOT a registered readout", and
  F-26's coverage caveat came from an unregistered diagnostic; F-22 quotes an
  "UNREGISTERED drop-two diagnostic" as such; amber's F-14 has three rows
  "decided only through logged amendments", E4 among them, and its row E19
  is decided by a rule written after its values were seen and says so.
  lockstep's findings log was not registered in advance.
- Kill criteria written before the data, with dated STATUS blocks appended
  as they fired or stood (`sideband/docs/WHY_THIS_DIES.md`).
- The free baseline: every sideband margin is measured against what the
  decoder already has (D-5), with an alignment-destroyed twin at equal
  dimensions beside it, so a margin that any block of the same size would
  show is read as nothing.
- The critic: an adversarial reviewer that recomputes labels and numbers
  from committed evidence, run before the landings of the real-model runs;
  its rounds are logged in `sideband/CHANGELOG.md` from 2026-10-01 and in
  the commit messages before that (`sideband/docs/COMMIT_LOG.md`). A
  recovered selection of its recompute scripts and round reports of the
  harness era, committed on 2026-10-17, is under
  `sideband/docs/audits/critic-recovered/`, whose README says what they
  are and are not and what was left behind (the rounds that reviewed this
  cut's own tool are withheld with it). amber's
  errata pass used an independent agent with the sideband critic's
  recompute checklist adapted to amber
  (`amber/results/errata_critic/REPORT.md`).
- Dated errata, never rewrites: registered text with an error gets a dated
  note; amber's three errata batches, 21 rows, are the example with the
  most rows.
- The noise floor measured (F-27), so a win bar is read against the spread
  a seed change produces.
- The harness: Espalier (github.com/Mike-Byrne-AI/espalier-harness) gates
  writes behind execution plans and hooks; deployed on sideband on
  2026-09-30 and adopted on 2026-10-01, it gated changes from its
  deployment on, shell writes excepted, as sideband's `CLAUDE.md` says.
  sideband's `.claude/` bodies and `tools/cc/` hooks are the configuration
  it ran under. The per-machine hook wiring is not shipped: that file says
  to run `python -m espalier doctor .` on a fresh checkout before trusting
  the gate, and warns that `espalier init` or `upgrade` regenerates the
  managed command bodies and would drop the critic lane.

## Check a number in under a second

From a clone, with Python 3.10 or newer and numpy (the record's run used
numpy 2.3.5), this recomputes the registered reconstruction margin of
sideband F-22 from the committed state file with the record's own
estimator, and prints the committed value beside it. Keep the state file's
row order: it is load-bearing for the interval.

```
cd sideband
python - <<'EOF'
import json, sys, numpy as np
sys.path.insert(0, 'src')
from sideband.stats import paired_ratio_delta_ci
rows = [json.loads(l) for l in open('results/real/oq16_stage_r.json.state.jsonl') if l.strip()][1:]
A = lambda a: [r for r in rows if r['arm'] == a and r['variant'] == 'live']
f, t = A('free'), A('tel')
print(paired_ratio_delta_ci([r['sse'] for r in f], [r['count'] for r in f],
                            [r['sse'] for r in t], [r['count'] for r in t], n_boot=2000, seed=0))
print(json.load(open('results/real/oq16_stage_r.json'))['delta_free']['live'])
EOF
```

Expected, both lines: 0.204983722587619, 0.15369761574819202,
0.28816195871219474 over 84 clusters (F-22 prints it as +0.204984
[+0.153698, +0.288162]). On PowerShell, save the Python between the
markers to a file and run it. `sideband/docs/RELEASE_NOTES.md` section 7
says which committed files recompute F-15, F-17, F-19, F-20 and F-21 the
same way (F-19 and F-21 from the per-prompt rows of their summary files,
the others from state files).

## Re-run

Install from this clone; none of the three packages is on PyPI, and two of
the names there belong to other projects:

```
python -m pip install -e "./sideband[dev]" -e ./lockstep -e ./amber
```

amber depends on the other two. Two re-run modes exist and are kept
apart:

- CPU, minutes: the test suites, the findings lint and the synthetic
  experiments (`sideband/docs/REPRODUCE.md` section 1: `python -m pytest
  -q`, `python tools/lint_findings.py`, `python experiments/run_all.py
  --smoke`; the smoke flag writes under `results/smoke/`, never over the
  committed evidence). Three checks in sideband's suite recompute
  registered payloads byte for byte from committed state files, and one
  synthetic fixture expects a zero margin and failed on a negative one:
  all four hold on the author's machine and in Linux containers on its
  CPU, and all four failed on GitHub's ubuntu runner on the first CI run
  (2026-10-19). The three skip under the variable CI, by name and each
  saying why, and may refuse on another machine; the fourth's assertion is
  narrowed to a positive margin, dated (`sideband/tests/README.md`, "Fail,
  not skip"); whether those three checks' landed words reproduce off the
  author's machine is not measured. On another machine, set `CI=1`
  before `pytest` to skip those three by name (in a clone that git can
  read, no other test's outcome depends on that variable;
  `SIDEBAND_REQUIRE_CPU_BOUND=1` runs them regardless); added 2026-10-19
  after the second CI run.
- GPU, hours: sideband's real-model runs need a 12 GB card, the gated
  Llama checkpoints (meta-llama/Llama-3.1-8B-Instruct,
  meta-llama/Llama-3.2-1B-Instruct) and allenai/OLMoE-1B-7B-0125-Instruct
  (`sideband/docs/THIRD_PARTY.md`); amber's runs used Llama-3.2-3B and
  Llama-3.2-1B base, Llama-3.2-1B-Instruct and TinyLlama-1.1B-Chat.
  Recomputing on the committed
  harvests is exact on the author's machine and needs the deposit below
  (`sideband/docs/REPRODUCE.md`, the dated notes of 2026-10-14 and
  2026-10-19); replicating on a fresh
  harvest uses the same instruments on a new population and is not
  bit-identical, because bf16 kernels are not bit-deterministic.

## Not in this repository

| Item | Files | Bytes | How it is bound |
|---|---|---|---|
| The sideband harvest shards (`results/real/harvest_*/*.npz`) | 24 | 10,131,081,744 | sha256 in each shard's committed `.meta.json` and in the provenance of the payloads that read it |
| The K-3 and OQ-15 per-prompt byproduct arrays | 2,160 and 1,710 | 3,238,718,080 | sha256 per file in each run's committed summary; the verifier refuses a missing, extra or mismatched file |
| The seed-6 replications and the OQ-20 replays, twelve byproduct folders written 2026-10-09 and 2026-10-10 | 1,281 | 1,086,399,860 | sha256 per file in each run's committed summary, the same verifier (re-measured 2026-10-19) |

14,456,199,684 bytes in all (about 14.5 GB), the three rows exactly: the first
two are the 2026-09-05 inventory's counts, the third the twelve folders written
after it, re-measured on 2026-10-19 (every gitignored file under
`sideband/results/real/` on that day: 5,175 files). The Zenodo deposit holds
exactly these files in 34 zip archives: one per byproduct folder (33) and one
holding the 24 harvest shards by bare file name, without their folders
(`sideband/docs/DATA.md` gives each shard's folder and lists the archives with
their sha256 and member counts): DOI 10.5281/zenodo.23462826
(https://doi.org/10.5281/zenodo.23462826). The sha256 bindings committed here
verify any copy.
WITHHELD.md lists what the export leaves out. The Llama 3.1 and 3.2
community licences list "outputs or results" separately from the Llama
Materials they govern; the "Built with Llama" notice is in NOTICE and the
licence copies are under `licenses/` anyway, for the model-output files
under `sideband/results/` and `amber/results/` (amber's model use is stated
in NOTICE since its survey of 2026-10-17; the lockstep folder carries no
model output, as NOTICE states since its survey of 2026-10-18). That is a reading of the licence text, not legal advice.

## Licence and citation

MIT, one licence for the whole repository: all three folders, code,
documents and results (chosen 2026-10-12), with the Llama notice above.
CITATION.cff at the root is the citation; the Zenodo record carries the
data citation: DOI 10.5281/zenodo.23462826
(https://doi.org/10.5281/zenodo.23462826).

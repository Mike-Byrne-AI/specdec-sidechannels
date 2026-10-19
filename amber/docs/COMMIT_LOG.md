# Commit log of the private amber repository

67 commits, newest first, up to 0b061b54d92c0c6abe926dedab1bcd6394ee7c85, the commit this folder is exported from. The public repository has a fresh history, so the hashes the record cites (FINDINGS.md, docs/ERRATA_PLAN.md, experiments/ERRATA_PROTOCOL.md) resolve here and nowhere else in the public tree; the review rounds each landing records are in these messages. Absolute paths outside the repository are scrubbed; paths into the author's own sideband checkouts stay (the export's own-checkout rule). 0 messages name a private repository or match the deny list: each keeps its subject with the match replaced and has its body replaced by a `[withheld: ...]` line. A line naming a file this export withholds carries the same marker the rest of the folder uses.

## 0b061b5 2026-10-18 record: dated notes for the owner's two public-cut calls of 2026-10-18 (the four token-id folders ship; the gate before publication waived)

````text
docs/ERRATA_PLAN.md: a dated note under step 1's bullet on results/p1, p4, p5 and p6. The owner's call of 2026-10-18 supersedes the bullet's last sentence: the folders ship in the public repository under its root notice for Llama-derived material, as sideband's own model-output files ship; they are the evidence behind F-8 and F-11 to F-13, and every errata row loads P1.

docs/BLUEPRINT.md: a dated note under the FTO gate of OQ-6. Waived by the owner for the public cut: no counsel review ran, and the prior-art search OQ-6 asks for before any publication was not re-run; the prior-art map's papers were refreshed on 2026-10-18 and the granted patent's claims re-read on sideband's prior-art map on 2026-10-11 (a textual reading, not legal advice); the repository is published as a parked research record under the MIT licence, K-1 unchecked.

OPEN_QUESTIONS.md: a dated note under OQ-6 saying the same from the question's side (the question stays open). docs/WHY_THIS_DIES.md: a dated note under K-1 (unfired and unchecked at publication, by the owner's waiver).

Amended before any push after the critic's recompute of the same evening (sideband's plan of record, section 15.9): the gate note's search sentence now tracks OQ-6's own words, and the OQ-6 and K-1 notes were added. Append-only against the parent: 4 files, 22 inserted lines, 0 removed. Every line citation into these files in the errata payloads, the protocol and the recompute script sits above the insertion points (docs/BLUEPRINT.md lines 3-4, 50, 57, 77-78 and 81; none into docs/ERRATA_PLAN.md past line 103; none into OPEN_QUESTIONS.md or docs/WHY_THIS_DIES.md at or past the notes), and the export's three Replace anchors in these files match byte for byte. Validation on the final tree: pytest 160 passed in 4.86s; tools/lint_findings.py lint_findings: OK (16 findings, all carry regime + evidence); git status showing only the edited files before the commit.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5fbc9bd 2026-10-18 record: second dated note under F-11 (the bf16 and fp16 rates are cross-dtype); the diagnostic records its library versions; prior-art wording

````text
After the critic's recompute of 2026-10-18 (sideband's plan of record, section 15.8, review): the F-11 dated note of the same day said the bf16 and fp16 rates were "not of the formats"; P4's archives were encoded at cuda fp32 (experiments/P4_PROTOCOL.md line 18) and decoded at bf16 or fp16, so the rates are cross-dtype figures, and a second dated note withdraws the phrase and qualifies "bound by nothing in the file" to nothing beyond id, snapshot and dtype (append-only; the first note stands as written). README's dated note names the comparator its "survives the split" refers to (concatenated zstd-19 with no dictionary). docs/PRIOR_ART.md's 2026-10-18 section: the thresholded-ranking entry names its corpus (source code) and its full title; the nondeterminism entry's gloss is scoped to what the fetched abstract states; the ts_zip entry bears on a same-dtype contract F-11 did not measure; one title's capitalisation. results/diagnostics_2026-10-18/p1_stratified.py records the zstandard, transformers and tokenizers versions in its provenance block (the JSON changes in that block only; every figure and the pinned EXPECTED are unchanged; two runs byte-identical). No edit to experiments/ or src/. pytest and tools/lint_findings.py on the final tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## e9bec74 2026-10-18 record: P1 stratified diagnostic and first-screen note; F-11 dated note on what the fp32 contract pins; prior-art additions and a withdrawn-reading note

````text
Dated notes from the cold read of 2026-10-18 (five unanchored reviewers; recorded in sideband's plan of record, section 15.8):
- results/diagnostics_2026-10-18/p1_stratified.py + .json: P1 split by E3's loop rule (W=128, P=64, t=0.5); every all-rows figure reproduces results/p1_divergence.json and the E3/E4 rows before it reports; non-looped greedy divergence 0.133978 against the headline 0.067834, zstd-19 on the non-looped text 7.491921 bits per token, amber's multiple over zstd-19 there 8.39x against 7.636x; expected figures pinned in the header; two runs byte-identical.
- README first screen: a dated note giving those figures beside the headline ones.
- FINDINGS.md F-11: a dated note that the fp32 contract pins dtype alone (archive.py MODEL_FIELDS; capture.py Arm) and that the bf16/fp16 failure rates are properties of this PyTorch stack at these settings (ts_zip evaluates in BF16 deterministically across GPU and CPU models, quoted from its page, fetched 2026-10-18).
- docs/PRIOR_ART.md: a 2026-10-18 additions section (LLMZip's encoding schemes by its section titles; thresholded symbol ranking, arXiv 2607.24192; numerical nondeterminism in LLM inference, arXiv 2506.09501; two LLM-generated-text compression papers, arXiv 2505.06297 and 2604.02343; ts_zip's determinism statement), each fetched and read that day; and a dated note beside the first granted-patent entry that its claim reading was withdrawn on sideband's map on 2026-10-11.
No edit to experiments/, src/ or any sha-pinned file. Validation: pytest -q and tools/lint_findings.py on the final tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c917a2a 2026-10-18 Front door and audit report corrected after the critic's second round (2026-10-18)

````text
README.md: the P2 protocol entered git in a commit carrying only a 64-position smoke payload, thirteen minutes before the commit that carried its full payload, and the capture's own file write times put the start of that run seconds after the protocol commit (the earlier wording, "before its full run", was wrong); F-16 decided two of E17's claim sites after a revised dry run, so E17 joins the rows decided after values were seen.

docs/audits/2026-10-17-image-audit/README.md: item 5 gives the pinned-input counts at 69b437c and at the front-door commits (91 resolve at the tree and 28 only in history, the three more being pyproject.toml, pinned by all three payloads and edited by the first front-door commit; the protocol tables 58 matching and 17 history-only), and names the one pinned input the export edits (docs/PRIOR_ART.md, pinned twice) instead of pointing at a second that does not exist; the section-B introduction counts three P3 band readings (bands (i) and (ii) reported as held and read as missed; band (iii) reported as not fired and read as fired on two pairs); item 17 carries the corrected P2 sentence; the first paragraph counts the commits after 69b437c.

No finding, decision, protocol, payload or result changed. Not pushed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 68c04bc 2026-10-18 Front door and audit report corrected after the critic's round (2026-10-18)

````text
README.md's first screen: the errata rows are described as pinned before each recompute except where the record says otherwise (F-14 decided E4, E7 and E13 through logged amendments; F-16 labels E19 post hoc); the P2 protocol is attested by git thirteen minutes before its full run (the commit that added it carried a 64-position smoke payload), so the self-attested set is P3 to P6; the P1 shards reproduce F-8's divergence and arithmetic-coding rate, read by an agent of the assistant's model family, while rows E2 and E5 corrected two other F-8 figures from the same shards; the synthetic experiments and the hardening sweep have no protocol and the kill criteria entered with the first findings.

docs/audits/2026-10-17-image-audit/README.md: "no band verdict moved" replaced by what the refuters found (no status word changed; two pre-registered P3 band readings read as missed from the committed payload and F-12's byte breakdown moves); the protocol source-table count is the refuter's (75 rows, 60 blob ids and 15 tree ids, 59 matching); the reproducibility sentence is scoped to the author's machine; the P2b figures are the refuters' (m=2 and m=4 of one bf16 pair; the pipeline-bug budget 2x to about 5,400x looser); 1.36x for the F-1 ratio; the rankcensus.py mention stays as residue because two payloads pin its blob.

No finding, decision, protocol, payload or result changed. Not pushed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 87fc714 2026-10-17 Front door for publication (2026-10-17): first screen, audit report, pyproject description and scipy

````text
README.md opens with a plain-language first screen (the question, the answer as corrected by F-14 to F-16 with every figure beside its finding and row, who ran it and how, one line per term, where to look, the install for both layouts, the third-party content under results/) above the record as it stood on 2026-10-11, which is kept beneath with its errata in place; the paragraph on how it was run states what git shows about each protocol's entry into history.

docs/audits/2026-10-17-image-audit/README.md is the curated report of a read-only image audit (nineteen agents: ten slice finders, one record reader, two reader walkthroughs, six default-refuted refuters; 141 findings, 101 confirmed, 38 downgraded, 2 upgraded, 0 refuted, 11 added; 152 survivors, 7 high). Its section B lists the candidates for dated errata; none is landed here.

pyproject.toml: the description states the corrected claim instead of the withdrawn tagline; the dev extra declares scipy, which tests/test_errata_recompute.py reaches through experiments/errata_lib.py (the suite read 1 failed, 159 passed with scipy hidden; 160 passed on this box).

No finding, decision, protocol, payload or result changed. Not pushed: Actions are enabled on the remote.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 69b437c 2026-10-11 Errata, third batch landed: F-16 and dated lines, generated from results/errata_recompute_3.json

````text
experiments/errata_text.py --payload results/errata_recompute_3.json
--finding F-16, applied once: the F-16 block appended to FINDINGS.md; dated
pointer lines under F-5, F-7, F-10, F-11, F-12 and F-13 (erratum) and under
F-8 and F-15 (note); erratum notes after OPEN_QUESTIONS.md lines 16 and
31-32, after D-6, D-11's bullets at 105 and 132 in DECISIONS.md and after
README.md line 50; notes after BLUEPRINT's Phase 1 and Phase 2c paragraphs;
a status line under the README heading. Append-only. Critic: three passes
on this batch, recompute discrepancy 0 / 4.4e-16 / 0, BLOCKING 2 -> 1 -> 0,
every objection recorded in the protocol's amendment log.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 1c6b746 2026-10-11 Errata critic, third batch, third (narrow) pass: report appended verbatim with its script

````text
RECOMPUTE DISCREPANCY 0, BLOCKING 0, nothing false in the nine insertions.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 70b6dcc 2026-10-11 Errata recompute payload, third batch, third landing: pinned prediction keys beside the harvest's

````text
Written on a clean tree by experiments/errata_recompute.py --rows
E17,E18,E19. Values and statuses unchanged; E18's prediction dict carries
both key sets; E19's F-10 site key names its provenance.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f492e68 2026-10-11 Errata, third batch after the critic's second pass: caveats sentence, pinned predictions restored, source line, site provenance

````text
The F-16 caveats line now says the escape-cost masses are over all census
positions; E18's prediction dict carries the entry's pinned keys beside the
harvest-definition keys so the scoring shows both the misses and the hits;
the source line lists dry_b3b.json and the TinyLlama manifest; E19's F-10
site key says its verdict rests on E15's rank-only compensator z. Dated
entry in the protocol. No value or verdict changed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 09ec8c5 2026-10-11 Errata critic, third batch, second pass: report appended verbatim with its scripts

````text
RECOMPUTE DISCREPANCY 4.4e-16 (floating point only), both earlier BLOCKING
objections fixed, the instrument amendment judged the E4/E7 kind; BLOCKING 1
on the generated caveats line (masses are over all census positions, not
the kept ones); three advisories.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d1a9f9d 2026-10-11 Errata recompute payload, third batch, second landing: post-critic fields

````text
Written on a clean tree by experiments/errata_recompute.py --rows
E17,E18,E19. Statuses unchanged (E17 CORRECTED, E18 CORRECTED, E19
CONFIRMED post hoc); the F-7 and OQ-2 escape-cost sites are decided
(CORRECTED) under the amended instrument check.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2c5e06a 2026-10-11 Errata, third batch after the critic: escape costs at 2 tau, E19 post hoc, pins, harvest definitions, literal-free effects

````text
E17: near-tie masses at the printed thresholds and at each dtype's 2 tau
for both models (TinyLlama from the newly pinned dumps), the escape-cost
sites added (OPEN_QUESTIONS.md:16), n_labels counts the printed labels;
the revised dry run (committed as dry_b3b.json) showed F-7's printed
"23.2%" missing a 0.05-point tolerance over the kept positions, so the
masses are taken over all census positions and checked at the printed
precision, with status_under_pinned_tolerance recording the sites that
were UNRECOMPUTABLE before that amendment. E18: line pins corrected (95,
102), F-11 and DECISIONS.md:105 added, the harvest's predictions scored
against values under its own definitions, effects without the special-token
literals beside the pinned ones. E19: post hoc (its primary binning equals
the critic's earlier values), predictions not scored, status_out_of_sample
over the six other binnings, exact Poisson O/E intervals and margins, claim
site moved to F-10's caveat (CORRECTED: the rank-only rank-1 rate does not
transfer). Generator: brackets for the new fields, predictions labelled
harvest/critic/protocol, texts and caveats rewritten accordingly.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d350243 2026-10-11 Errata protocol: post-critic entry for the third batch; TinyLlama dumps pinned by manifest

````text
Records the critic's BLOCKING 1 (E17: the 4-tau labels also produced the
escape-cost figures; near-tie masses at 2 tau added for both models, OQ-2
joins the sites) and BLOCKING 2 (E19 relabelled post hoc: its primary
binning equals the critic's own earlier values; predictions not scored;
status_out_of_sample over the six other binnings; claim site moved to
F-10's caveat), the three line pins corrected (77, 95, 102), E18's added
sites, harvest-definition values and literal-free effects, the label rule
wording. results/p2_tinyllama_dumps.sha256 pins the local TinyLlama dumps
E17 reads for F-5's costs. errata_lib: poisson_ratio_interval.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 27854d4 2026-10-11 Errata critic, third batch, first pass: report appended verbatim with its scripts

````text
RECOMPUTE DISCREPANCY 0 (113 + 126 + 192 leaves), BLOCKING 2: E17's
"only the labels are wrong" understates the correction (the 4-tau labels
reached the escape-cost figures of F-5, F-7 and OQ-2); E19's status was
decided by a rule whose primary binning equals the critic's own post-hoc
second-batch values, committed before the entry. Eight advisories.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 1ac19bf 2026-10-11 Errata text: E18 prints each dictionary's actual byte length beside the requested size

````text
The 64 KB and 256 KB requests both yield one 22,323-byte dictionary (zstd
caps it at the training data); the sentence now says so. No value touched.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 727338d 2026-10-11 Errata text: F-16 caveats line without a literal pipe (corrective)

````text
5b5664f exposed one failing test once the third payload existed: the
typed "|z| < 2" in the F-16 caveats line is an unescaped pipe in generated
markdown. Reworded; no value or status touched.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5b5664f 2026-10-11 Errata recompute payload, third batch: results/errata_recompute_3.json (E17, E18, E19)

````text
Written on a clean tree by experiments/errata_recompute.py --rows
E17,E18,E19. Statuses: E17 CORRECTED (6 of 7 labels are 4 tau; counts
CONFIRMED), E18 CORRECTED (per-archive and session scales; concatenated
scales CONFIRMED), E19 CONFIRMED (gap-conditioned rank-1 transfer; E15's
rule CONFIRMED under it).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## a90c107 2026-10-11 Errata recompute and text, third batch: rows E17, E18, E19, helpers, tests, dry-run evidence

````text
errata_lib: label_multiple, bits_per_token, dictionary_effect,
crossover_length, gap binning (equal-count and log edges), binned_rates
and apply_rates (nearest non-empty bin). errata_recompute: e17 (printed
"2tau" labels against the census tau and per-row tau field, beyond-counts
at 2 tau, P2b thetas as tau multiples), e18 (zstd-19 dictionaries trained
on P1 rows 0-99 at 4/16/64/256 KB, held-out rows 100-199 per archive, per
session k=8/16, concatenated full and generated text, crossover by F-12's
rate law, repetition split; dictionary effect scored per claim site at a
tenth), e19 (the dumps' rank-1 desync rate by top-2 gap bin, 20 equal-count
bins with a six-binning grid, transferred to the archives' decoded
positions, |z| < 2; E15's rule re-evaluated). Generator: F-16 block, row
texts, a third-batch README note, notes sharing an insertion point merged.
First dry run committed as results/errata_dryruns/dry_b3.json (LF).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 04dbf23 2026-10-11 Errata protocol: third-batch entry pinning E17, E18 and E19 before any code

````text
E17: F-5's and F-7's printed "2tau" thresholds against the census tau and
the per-row tau field (2 tau), with the beyond-counts checked at 2 tau.
E18: the zstd baselines carry no dictionary; dictionaries trained on P1
rows 0-99 (4/16/64/256 KB), held-out rows 100-199, per archive, per
session (k=8, 16, reset mode), concatenated full text and generated text;
the dictionary effect scored at each claim's own scale (threshold 0.10),
D-6 read at the per-archive scale as the row status. E19: the rank-1 desync
rate of the dumps conditioned on the encoder's top-2 gap (20 equal-count
bins, grid beside) transferred to the P4 archives over the decoded
positions, scored by |z| < 2; the C term stays rank-only. Predictions are
the harvest's and the second batch's critic's, scored after the run.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 168efb0 2026-10-10 Errata, second batch landed: F-15 and dated lines, generated from results/errata_recompute_2.json

````text
experiments/errata_text.py --payload results/errata_recompute_2.json
--finding F-15, applied once: the F-15 block appended to FINDINGS.md; dated
pointer lines under F-7 and F-10 (note: every site there stands at its own
scope), F-11 and F-14 (erratum); a note after BLUEPRINT's Phase 2
paragraph; erratum notes after OPEN_QUESTIONS.md lines 15-16 and README.md
line 50; a status line under the README heading. Append-only: every
original line survives unchanged and in order. Critic: four passes on this
batch, recompute discrepancy 0 each, BLOCKING 2 -> 1 -> 0 -> 0, every
objection recorded in the protocol's amendment log.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8a19a66 2026-10-10 Errata recompute payload, second batch, fifth landing: E16 prediction sources per key

````text
Written on a clean tree by experiments/errata_recompute.py --rows E15,E16.
Only the label field changed; every value and status is unchanged.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c3dc45e 2026-10-10 Errata, second batch after the critic's fourth pass: E16 prediction sources per key

````text
Protocol: dated entry. The label credited E16's predictions to the E15
proposal's item and to the critic for a count the protocol inferred; it is
now per key, with b8_count_above_budget labelled as this protocol's.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b791f65 2026-10-10 Errata critic, second batch, fourth (narrow) pass: report appended verbatim with its script

````text
RECOMPUTE DISCREPANCY 0, BLOCKING 0, nothing false in the nine insertions;
one label advisory (E16's prediction sources).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 980597b 2026-10-10 Errata recompute payload, second batch, fourth landing: E16 prediction sources labelled

````text
Written on a clean tree by experiments/errata_recompute.py --rows E15,E16.
Only the label field is new; every value and status is unchanged.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8211329 2026-10-10 Errata, second batch after the critic's third pass: like-for-like failure sentence, labels, wording

````text
Protocol: dated entry for the third pass. E15 text compares the C-hazards-
only failure prediction with the C-caused failures and prints the excess
in binomial sd of the predicted rate; E16 gains prediction_sources; the
caveats line states the label rule in full; "claim-site statuses" in the
title and README note; the regime line says the pre-registration was
committed before the first code and that the order of writing is
self-reported. The house-rule breach of 05c3305 / 3cec4df is recorded.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 79f2005 2026-10-10 Errata critic, second batch, third pass: report appended verbatim with its scripts

````text
RECOMPUTE DISCREPANCY 0 (467 + 379 value leaves, every status field),
BLOCKING 0, nothing false in the nine insertions; five advisories.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8515734 2026-10-10 Tests: two wrong expectations in the new errata text tests (corrective)

````text
05c3305 and 3cec4df were committed with these two tests failing: the chain
that committed them joined the test run with a semicolon instead of a gate.
Both failures were in the expectations, not the code: claim_site_counts
forgot that a CONFIRMED row without claim-site fields counts as a standing
site, and a prediction of 1.5 against a value of 1.49 is a hit at the
prediction's own precision. The generator and the recompute are unchanged.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 3cec4df 2026-10-10 Errata recompute payload, second batch, third landing: all-arm claim scope, by-class fail rates

````text
Written on a clean tree by experiments/errata_recompute.py --rows E15,E16.
Statuses unchanged; status_at_claim_scope now covers every arm read, and
the top-1 claim sites are CONFIRMED on all of them.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 05c3305 2026-10-10 Errata, second batch after the critic's second pass: amendment, all-arm claim scope, by-class fail rates, labelled text

````text
Protocol: dated entry recording the critic's BLOCKING 1 (the generated
caveats sentence overgeneralised the 2tau observation; F-7's fp16 label is
2 tau; the census's own beyond-2tau counts were taken at 2 tau) and the
fields and wording adopted from its advisories. Recompute: E16's
status_at_claim_scope over every arm read and the top-1 sites scored on all
of them; E15's theta-0 whole-archive failure prediction under C hazards
alone and A hazards alone; F-11's printed per-token figures moved out of
the prediction dict (quotations, with a rounding check); pinned_rule_sites
on both rows. Generator: the fixed caveats sentence; E16 says F-14's
sentence holds at logit scale and names the one context above budget as a
tail drift; E15 covers both metrics by class; predictions labelled by
source; the title and README note count rows corrected under pinned rules
and claim sites standing at their own scope; pointer lines labelled
erratum or note by the sites they point for; the dry run prints in write
order. Tests for the labels, counts and sources.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 6998aba 2026-10-10 Errata critic, second batch, second pass: report appended verbatim with its scripts

````text
RECOMPUTE DISCREPANCY 0 (450 + 376 value leaves and every status field
reproduced), both earlier BLOCKING objections fixed; BLOCKING 1 on the
generated F-15 caveats line (F-7's fp16 "2tau" label is 2 tau, not 4 tau).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 553ffb4 2026-10-10 Errata recompute payload, second batch, second landing: post-critic fields

````text
Written on a clean tree by experiments/errata_recompute.py --rows E15,E16.
Statuses unchanged (E15 CORRECTED, CONFIRMED in the claim's own regime and
for corrections by class; E16 CORRECTED at depth, CONFIRMED at the claims'
own scope on both arms).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 9c325c4 2026-10-10 Errata recompute and text, second batch after the critic: by-class compensator, claim-scope statuses, drift fields

````text
E15: regime of both sides from the JSONs; observed first desyncs by class
against the expected count over the decoded positions (ratio, z, predicted
first-desync shares); rank-1 gap shares under the bf16 and fp16 pair budgets
in the P2 dumps and the P4 archives; status_by_class and status_by_claim_site;
*_h1 fields with the critic's predictions scored against them and labelled.
E16: F-14's E8a sentence sites added to `where`; status_at_claim_scope (slot 0)
and status_by_claim_site; distinct contexts; per-event decoder deltas and pair
drift; the census tau definition; aligned top-64 deltas by slot and the
adjacent-pair drift count for the scored arms. Generator: both texts
rewritten (by-class result, tail drift, top-1 claims stand), touching note
locations merged, same-index insertions keep list order, the refusal check
precedes text generation; tests for every helper. The committed second
payload predates these fields: its text test xfails until it is regenerated.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 53053f2 2026-10-10 Errata protocol: post-critic amendment for the second batch; pre-amendment dry run preserved

````text
Both BLOCKING objections recorded as protocol defects in the E9 manner,
no pinned verdict changed: E15 gains the per-class compensator, z scores,
status_by_class, status_by_claim_site, the regime of both sides and the
rank-1 gap shares; E16 gains status_at_claim_scope, status_by_claim_site,
F-14's E8a sentence sites in `where`, distinct contexts, per-event decoder
deltas, the census tau definition, aligned-delta quantiles by slot and the
adjacent-pair drift count. dry_b2_pre.json is the run whose values were
seen first (cfb9595), per the critic's ADVISORY 8.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 93ea7de 2026-10-10 Errata critic, second batch, first pass: report appended verbatim with its scripts

````text
RECOMPUTE DISCREPANCY 0 (399 + 283 payload leaves reproduced), BLOCKING 2:
E15's pinned rule scores a corrections claim on an all-class quantity and
the reversal is the rank-1 term alone; E16's rule reads top-1 claim sites
at depth. Scripts c2_*.py and their .out.json outputs as the agent left them.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## a00c50c 2026-10-10 Errata text generator: per-row text functions, --payload/--finding, F-15 block

````text
row_texts is now a table of per-row functions over the rows a payload
carries, so the second payload (E15, E16) generates without the first
batch's rows. New: f15_block with its own title, regime and source lines;
status_bracket renders status_by_arm; readme_status_note per finding and
status_note_index places it after any earlier note; main takes --payload
and --finding and refuses once that finding exists. E15 and E16 texts: every
numeral from results/errata_recompute_2.json; slot buckets in numeric
order; the E15 class-mix sentence names both candidate causes and claims
neither. Tests parametrised over both payloads.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 861c553 2026-10-10 Errata recompute payload, second batch: results/errata_recompute_2.json (E15, E16)

````text
Written by experiments/errata_recompute.py --rows E15,E16 on a clean tree
at b35e126. Statuses: E15 CORRECTED (CONFIRMED in the claim's own regime),
E16 CORRECTED (cuda_fp32_b1; cuda_fp32_b8 CONFIRMED by arm).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b35e126 2026-10-10 Errata recompute, second batch: rows E15 and E16, helpers, tests, dry-run evidence

````text
errata_lib: rank_histogram, rank_rates, setcoded_rates, expected_rate,
fail_rate_exact, fail_rate_poisson, class shares (E15); order_diff_events
and gap_summary (E16); six tests on synthetic inputs. errata_recompute:
e15 (regime check on the P4 symbol streams, instrument checks on the P1
ranks and the decode shards, theta-0 all-class and C-only predictions
under both weightings, exact and Poisson fail rates, class shares) and
e16 (order-differing positions of five decoder arms against the XB-3 pair
budget or the census 2*tau, by slot bucket); --rows now writes a subset
to a non-default --out; provenance carries batch and rows_requested.
Protocol: dated post-dry-run entry (one informational field). Dry-run
payload committed under results/errata_dryruns/ (LF).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## cfb9595 2026-10-10 Errata protocol: second-batch amendment pinning E15 and E16 before any code

````text
Dated entry at the end of the amendment log. E15: F-10 item (4)'s
"1/170, 1/1070" and F-11's "slightly MORE fragile" are C-only rates at
theta 0.465 while F-11 decoded at theta 0; the row pins the theta-0
all-class prediction weighted by the P4 archives' own coded ranks, the
claim-regime reproduction under P1's ranks, exact and Poisson fail-rate
predictions, and the instrument and regime checks. E16: the near-tie
measure of E8c gets the record's own threshold (the XB-3 pair budget for
cuda_fp32_b1; the census 2*tau for cuda_fp32_b8, labelled a proxy) and
counts order-differing positions above it, by slot bucket. The critic's
values are the predictions. Second payload file, new finding F-15.
Also records, unscored, that F-5/F-7's printed "2tau" labels are 4 tau.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 509ad90 2026-10-10 ERRATA_PLAN marked done; CLAUDE.md names the sibling path as laid out on this box

````text
docs/ERRATA_PLAN.md: a dated DONE line under its status (amber 0f6d2f0, lockstep
TP-7 54d83f4; the critic ran from amber; E11 record-only and E15 deferred by the
operator). CLAUDE.md: the sideband sibling is ../../Research/sideband here, not
../sideband (a path, not a rule change). 137 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 0f6d2f0 2026-10-10 Errata landed (ERRATA_PLAN steps 5-6): F-14 and dated notes, generated from results/errata_recompute.json

````text
FINDINGS.md gains F-14 (the 2026-10 errata pass: 12 of 16 checked claims
corrected, 4 confirmed, 3 decided only through logged amendments) and one
dated "erratum" line at the end of F-2, F-4, F-8, F-10 and F-11. Dated
pointer notes follow the other claim sites each row names (README.md,
docs/BLUEPRINT.md, DECISIONS.md, OPEN_QUESTIONS.md, docs/PRIOR_ART.md) plus
one under the README status header, and experiments/P7_PROTOCOL.md carries
its withdrawal line. Every numeral, date and commit id in the inserted text
was generated by experiments/errata_text.py from the payload at 4492ec0;
every original line survives unchanged and in order (checked); markdown
pipes are escaped.

Critic trail (results/errata_critic/REPORT.md, all three passes verbatim):
pass 1 discrepancy 0 / BLOCKING 2 (E9's rule checked F-10's table at the
wrong theta; E13's amendment was post hoc), pass 2 discrepancy 0 / BLOCKING
1 (a false E8a sentence), pass 3 discrepancy 0 / BLOCKING 0. Advisories left
open and recorded there: rows.E8a.note's last clause contradicts the
headline's per-site CONFIRMED (not printed); "near-tie" carries no
threshold (2 of 379 b1 order differences exceed the fp32 pair budget
8.6e-05); the proposed E15 (F-10/P4 predictions at theta 0.465 vs F-11's
theta 0 decode) is left to the operator, as is the E11 binformat fix.

137 tests, lint OK (14 findings). Local only; the repo stays private.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 31ee98b 2026-10-10 Errata text generator: E8a/E8c wording per the critic's second pass, DECISIONS note after the bullet

````text
E8a: the false sentence is withdrawn; the bullet states the per-site
statuses, calls OQ-2's claim an order claim false at every theta with the
near-tie measure, and says the resolved token is stable only at batch 1 with
the escape on. E8c carries the same qualifier. E9 says "other printed
depths" and prints the A-desync count beside the top-1 rate. The F-14 title
counts the rows decided only through logged amendments. DECISIONS.md notes
are placed after the paragraph (D-9's bullet spans two lines; the note no
longer lands inside its sentence). 137 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 4492ec0 2026-10-10 Errata recompute payload, third landing: E8a per-site statuses, order-difference near-tie measure

````text
Regenerated on a clean tracked tree by the previous commit's script. All 16
statuses unchanged. New: rows.E8a.status_by_claim_site, rows.E8c.value
.order_differences_vs_cpu_fp32.*.max_encoder_gap_between_tokens_competing_
for_first_differing_slot, desyncs_A in every depth table, amendment labels
with their timing. 137 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 070430b 2026-10-10 Errata recompute after the critic's second pass: E8a status per claim site, near-tie measure for order differences

````text
The critic's one remaining BLOCKING objection: E8a's single claim-regime
status took its regime from F-10's body, which is wrong for README.md:34
(the shipped theta 0 contract) and OPEN_QUESTIONS.md:14 (an order claim).
E8a now carries status_by_claim_site: the F-10 headline CONFIRMED in its
escape-on regime, README:34 CORRECTED, OQ-2:14 CORRECTED (filled from E8c's
top-64 order-difference count). E8c adds the near-tie measure over the
order-differing positions (the largest encoder-value gap between the two
tokens competing for the first differing slot) and the A-desync count in
every depth table; the amendment labels say when each was written; E8b's
note says the rule does not score F-11:80's rounded CPU count. The protocol
log gains the matching dated entry, which withdraws the false "exactly
order-stable holds for the resolved token" sentence. 137 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d0eae27 2026-10-10 Fix the generator test for the qualified status brackets; correct the two previous commit messages' test record

````text
tests/test_errata_text.py expected "  - E4 [CORRECTED]" but the F-14 bullets
now carry qualifiers inside the bracket ("[CORRECTED; UNRECOMPUTABLE under
the pinned rule, ...]"); the test now checks the status prefix and, where
the payload carries them, the qualifier phrases.

Record correction: 12e4867's message said "146 of 147 tests pass"; the
suite at that commit was 135 passed, 2 failed (both in this file, against
the pre-revision payload). 3e91148 landed with this one test still failing
because the commit chain piped pytest through tail and so never saw its
exit status. Both commits are local. From here: 137 passed, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 3e91148 2026-10-10 Errata recompute payload, second landing: results/errata_recompute.json after the critic

````text
Regenerated on a clean tracked tree by the revised script (previous commit).
Statuses unchanged (CONFIRMED E7, E8b, E10, E14; CORRECTED the other 12);
new fields: status_under_pinned_rule for E4/E7/E13, status_in_claim_regime
for E8a/E9, E4 loop-grid strata, E8b's p4_real_archive cross-check, E8c's
pair gap / persistence / order-difference counts, E12's wide grep, E13's
full abstracts, E14's extra check. 147 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 12e4867 2026-10-10 Errata pass after the critic (step 4): protocol log corrected, E9 regime defect recorded, evidence committed

````text
The critic (an independent opus agent; its verbatim report and scripts are
under results/errata_critic/) reproduced every payload value (recompute
discrepancy 0) and raised two blocking objections, both about rules:
- E9: the pinned rule checks F-10's per-rank table at theta 0, but the table
  is the theta 0.465 / m 2 row of the JSON (its C-desync counts occur in no
  other row) and F-10 never says so. The pinned verdict stands as the
  defect's record; the payload adds status_in_claim_regime (the printed
  figures checked at every theta/m row; CONFIRMED at 0.465/2) and the
  erratum reads "regime unstated; at the shipped theta 0 rank 2 is ...".
  E8a gets the same field.
- E13: the title->abstract amendment was written after the pages were read
  and moved the row from UNRECOMPUTABLE to CORRECTED, so the log's claim
  that no amendment changed a value-dependent decision was false (E4 and E7
  also moved UNRECOMPUTABLE -> decided). The log now says so by appending;
  those rows carry status_under_pinned_rule beside status; the two dry-run
  payloads that show the pre-amendment statuses are committed under
  results/errata_dryruns/.
Advisories taken: E4 strata at every loop-grid setting (per-archive
direction not robust; none stated), E8b reads results/p4_real_archive.json
and quotes F-11:80's CPU count, E8c records the swapped pair's own gap, the
desync's persistence under every theta/m and the top-64 order-difference
counts, E12 greps all code dirs, E13 stores full abstracts, E14 checks
p7_longhorizon.json, E6/E11 wording. The proposed E15 is left to the operator.

Transient: tests/test_errata_text.py reads the committed payload, which
predates these fields; it is green again at the next commit, which lands the
regenerated payload. 146 of 147 tests pass here; lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## fc52e8e 2026-10-10 Errata text generator (ERRATA_PLAN step 5, code only): F-14 and the dated notes from the payload

````text
experiments/errata_text.py turns results/errata_recompute.json into the
record changes and nothing in them is typed: the date comes from
provenance.written_unix, commit and blob ids from provenance, every figure
from rows.<id>.value, the claims' own printed numbers quoted from
rows.<id>.claim, and the insertion points from each row's `where` entries
(FINDINGS lines are mapped to their finding block; other files get a dated
note after the referenced line or paragraph; one summary note under the
README status header). It verifies each target file's HEAD blob still equals
the blob the run pinned, inserts bottom-up so every original line survives in
order (checked), escapes pipes, and refuses a second run once F-14 exists.
--dry-run prints every insertion. Not applied yet: the record changes land
after the critic's recompute (step 4).

tests/test_errata_text.py: placement derivation, append-only insertion,
note styles, lint lines and source paths on the committed payload, no raw
pipes, second-run refusal. 137 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 04cbfe9 2026-10-10 Errata recompute payload (ERRATA_PLAN step 3 landing): results/errata_recompute.json

````text
Written by experiments/errata_recompute.py at 20dd31d on a clean tracked
tree, CPU only (torch blocked), every input cited by blob id, LF bytes.
Statuses under experiments/ERRATA_PROTOCOL.md: CONFIRMED E7, E8b, E10, E14;
CORRECTED E1, E2, E3, E4, E5, E6, E8a, E8c, E9, E11, E12, E13; none
UNRECOMPUTABLE. Values live in the payload (rows.<id>.value.<key>); the
errata text (step 5) is generated from it, not typed. results/errata_web/
holds the two arXiv abstract pages E13 read, with their sha256 in the payload.

Next: the critic's independent re-derivation (step 4) before any errata
text lands.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 20dd31d 2026-10-10 Errata recompute script (ERRATA_PLAN step 3): rows E1-E14 from committed evidence

````text
experiments/errata_recompute.py computes every protocol row from sources at
the pinned commit (E8c from the local dumps after a manifest check) with
amber's own functions (load_generated/load_rank, loop_fraction,
distinct_ngram_ratio, p1_divergence.amber_bits, p2b simulate, the hf/v3/v4
decoders), applies the protocol's decision rules verbatim, records
provenance (HEAD, tree, clean-tree flag, every input's blob id, the script's
own blob, library versions, torch blocked) and writes LF JSON with one stable
key per quantity. It refuses to write on a dirty tracked tree; --dry-run
prints instead and saves E13's pages to a temp dir. experiments/errata_lib.py
holds the side-effect-free helpers (loop/stall rules, stratified rates, depth
table, E11 crafting + sentinel probe, arXiv meta parsing), tested on
synthetic inputs in tests/test_errata_recompute.py (9 tests).

ERRATA_PROTOCOL.md gains its dated amendment log from two dry runs: E4's
instrument check uses the instrument's float32 mean; E7 loads the pinned
tokenizer from the cached snapshot dir (transformers 4.57 calls model_info()
for repo ids even offline); E13's rule keys on citation_abstract (neither
title contains PMATIC); informational columns for E9 (alt_c, rank-2 under
every theta) and E1. No value-dependent rule changed.

132 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 73575a8 2026-10-10 ERRATA_PROTOCOL: pre-register the 2026-10 errata recompute (E1-E14)

````text
Pinned at 6672db4 before any recompute exists: for every row, the claim and
its locations, the quantity and its exact definition (loop rule W=128/P=64/
t=0.5 with a grid; stall rule 0.25 x median with a grid; depth denominators
per symbol class), the sources by blob id, the amber function used (D-1),
the decision rule (CONFIRMED / CORRECTED / UNRECOMPUTABLE) and the harvest's
value as a scored prediction. E8 is split: E8a F-10's P2b headline at
theta 0, E8b D-8's "0 desyncs / 55k" from the P4 decode shards, E8c the
cuda_fp32_b8 decoder P2b never ran (local dumps, pinned by the manifest).
E11 tests the three decode paths with a sentinel-patched symbol expansion
and a small-length control. The blob-id table was checked mechanically
against git (one hand-typed id corrected before commit).

ERRATA_PLAN step 2. 123 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 6672db4 2026-10-10 Evidence commit: track the P1/P4/P5/P6 raws, pin the P2 dumps by sha256 manifest

````text
- results/p1, p4, p5, p6 leave .gitignore (1,384 files, ~8.3 MB: generation,
  draft and self-check shards, the P4/P5/P6 archives and decode metadata) so
  the errata recomputes can cite them by blob id. They hold Llama-3.2-generated
  token ids; this repo stays private.
- results/p2 and results/p2_llama32 (961 MB each) stay local;
  results/p2_dumps.sha256 (286 entries) pins them, written by
  tools/sha256_manifest.py (write/check, sha256sum-compatible, LF; 3 tests).
- docs/ERRATA_PLAN.md: the 14-row errata plan written 2026-10-10 from the
  sideband session, as received.
- pyproject: the install-path comment matches the box (sideband lives at
  ../../Research/sideband; install the siblings with --no-deps).

ERRATA_PLAN step 1, part 2. 123 tests, lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b794f86 2026-10-10 Evidence bytes: results/** -text so every checkout writes the committed bytes

````text
core.autocrlf=true on this box left 20 of 24 tracked results files LF in the
index and CRLF on disk, so an on-disk sha256 never matched the blob: the
2026-10-09 harvest pinned p2b_escape_robustness.json at 27eae3b6 / 600,477 B,
while the blob of record is 2af76ce1 / 576,178 B (id 7a84b002). The blobs are
the evidence the findings cite, so they are kept as they are and the working
tree is rewritten from the index; verified disk == blob for all 24 files after
the rewrite (they differed only by CRLF before). Cite results by blob id
(git rev-parse HEAD:<path>); recomputes must write results with explicit LF.

ERRATA_PLAN step 1, part 1. 123 tests, lint OK, no content change.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8662535 2026-08-30 P7 pre-registration: long-horizon archives (caps 2048/4096/8192, rate-vs-L against the F-12 law, repetition/degeneracy rule) + TRUE multi-turn sessions (12x8 turns generated with full history; the F-13 shared-vs-reset sign test, bands frozen). Pure helpers (build_multiturn, loop diagnostics) with tests; chunked scorer gains measurement-only log2q for the AC-under-draft baseline (D-6, never read by the format). No GPU stage run yet.

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 11aef4d 2026-08-30 CI: check out private sibling repos (sideband, lockstep) via SIBLINGS_TOKEN instead of assuming local sibling paths; fail loudly when the secret is missing

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 83f498f 2026-08-30 Session archives v4 (F-13, D-11): one pin/digest set + per-turn table, ctx_mode reset|shared; reset-mode k=8/16 reaches 1.65/1.45 bits/gen-token (2.6-2.9x under separate files, 3.4x under zstd-19 per session); shared context loses +16-39% content on independently-generated turns as pre-registered and is reserved for true multi-turn data; 33/33 fp32 byte-exact incl. 4k-token replays; desyncs turn-confined in reset mode; 116 tests

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 78e7bcd 2026-08-30 Format v3 binary + draft-coded prompt (F-12, D-10): 130 B mean archive (97 B fixed floor), 4.26 bits/gen-token at L=245 (header 3.17 + prompt 0.57 + content 0.45), prompt rank-coded at 11.3 vs 17.3 bits/token, 200/200 fp32 byte-exact with prompt segment decoded; rate law 917/L + 0.455, zstd-concat crossover L~263; every-byte corruption sweep; 110 tests

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 4d1c0ea 2026-08-30 Real archives (F-11, D-9): hf archive kind (model pin, prompt ids, content digest), teacher-forced fp32 encoder, incremental KV draft-only decoder; P4 run: 200/200 GPU + 24/24 CPU byte-exact under fp32, bf16 84% / fp16 28.5% archive failure in F-10's bands; header dominates short archives (OQ-7); 101 tests

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## ded7067 2026-08-30 Format v2 + P3/P2b (F-9, F-10, D-8): lockstep.rac coder with value-free contexts (+1% over gamma on the real stream, -40% on short archives; gamma stays default), near-tie escape built and priced (0.14-0.42 bits/token), cross-arm robustness sim shows bf16 decoders mis-resolve 3-26% of shallow-rank corrections -> fp32-class decoder contract; payload digest closes D-7's open item; value contexts (-23%) measured and forbidden; 95 tests

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 7ab4ed2 2026-08-29 Phase 1 run (F-8): Llama-3.2-3B->1B greedy divergence 6.8%, amber v0 0.474 bits/token vs zstd-19 3.62 (K-2 does not fire), tie with AC-under-draft; protocol dead-zone recorded; target generate-vs-forward self-consistency 99.67% flagged for L1 attestation; OQ-1/BLUEPRINT/WHY_THIS_DIES/README updated

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 70147cd 2026-08-29 P1 ledger output named per out-dir; ignore raw p1 dumps

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 9c26110 2026-08-29 F-7: Phase 2 replicated on Llama-3.2-1B-Instruct — fp32 order stable to 1 flip/49k, fp16 0.42%, bf16 2.0% (all near-ties), run-to-run bit-identical, 1e-3 grid crosses at 41% at fp32; census output named per out-dir; TinyLlama census restored

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 1d536e0 2026-08-29 Phase 1 tooling (OQ-1/K-2): resumable target greedy generation + teacher-forced full-vocab draft rank dumps (amber.real.divergence), D-6 four-way ledger with exact amber bits, a01-style ideal bound, AC-under-draft, zstd/lzma/zlib on text; P1 protocol pre-registration with PASS/AC-ONLY/K-2 bands and target self-consistency check; tests for stable rank, bit accounting, resume

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 476a1ac 2026-08-29 Phase 2 run (F-5/F-6): TinyLlama rank census on the 3080 Ti — fp32 cross-device order exactly stable, bf16 1.0% near-tie flips, run-to-run bit-identical; band (c) fired on bf16 batch dependence, investigated as N2 kernel selection; E-006 grid-crossing readout (22% at delta 1e-3 even at fp32); fp32 batch-8 discriminator arm; post-hoc block labeled in census

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 2b91dac 2026-08-29 Phase 2 tooling: resumable shard-atomic top-k logit capture (amber.real.capture, no-padding teacher forcing, offline-first loading, provenance), top-k rank census + tie-stable canonicalization, P2 protocol pre-registration with per-arm tau and determinism checks, tests for resume/batch/topk equivalence; draft = TinyLlama-1.1B (Llama-3.2 gated, not authorized on this box)

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 546ab4d 2026-08-29 amber v0.2.0: lockstep sibling dependency (D-7), sealed+typed header after mutation sweep found silent length corruption (F-4), rank-stability census instrument validated on synthetic drift (F-3, a03), Phase 2 protocol + bands in BLUEPRINT, OQ-6 Google integer-net patents, PRIOR_ART lockstep entries

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 91e6445 2026-08-29 amber v0.1.0: verified-archives v0 codec (target-encode, draft-only decode, byte-exact), attestation L0/L1, rate curve F-1 with honest zlib caveat, rank-stability narrowing F-2, blueprint with kill criteria and FTO gate

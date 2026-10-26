# Lessons from the record's own limitations

Written 2026-10-16 as the closing step of lane B of the public-cut plan, after the
2026-10-15 image audit (docs/audits/2026-10-15-image-audit/README.md, the audit's report with
the recompute scripts beside it). Each entry below is a limitation that stays in the
evidence: the instruments are frozen (their bytes are attested by committed payloads) and
the registered runs are not repeated, so the record carries a dated note or erratum beside
the affected text instead of a fix. For each one: the mechanism, the cost as measured, the
rule the next instrument follows, and where the repository itself does not yet follow the
rule. The dated notes in FINDINGS.md, DECISIONS.md and docs/BLUEPRINT.md are the primary
text; this file is a derived reading aid, and on any disagreement the record's dated note
wins. Figures quoted from the audit folder's reruns of 2026-10-16 name their file; the
counts in entries 7, 8 and 13 were measured on the tree the same day by the commands named.

## 1. A mechanism sentence copied forward past the code

- Mechanism: "the HF adapter recomputes prefixes" was written on 2026-08-29 and was false
  from a commit later that day (b1dae57, cropped KV caches by default). Twelve files
  carried the sentence, eight of them written after that commit, because each new
  document copied it from the last one instead of the code; a thirteenth, docs/METHOD.md,
  quotes the critic's rule that carried it.
- Measured cost: fifteen false or stale statements, zero numbers moved; the ban itself was
  right for a different reason (no benchmark harness exists).
- Rule: a mechanism claim has one home (here DECISIONS.md D-9 and its dated note of
  2026-10-16); every other file cites the home rather than restating the mechanism, and a
  ban states its own ground, not a code detail that can change.
- Not yet followed by: this lane's own dated notes, which restate the b1dae57 mechanism
  beside each stale sentence so that a reader of that sentence alone sees the correction;
  the cost is accepted, and tests/test_record_claims.py pins the code default they cite.

## 2. Intervals that are conditional on the trained seeds

- Mechanism: every probe CI is a prompt-cluster bootstrap over counts summed across three
  train seeds (tools/run_probes.py, frozen), so it is conditional on those three trained
  probes; the registered all-seeds rule protects the fire direction only. The registered
  disclosure that the seed "only shuffles AdamW batch order" was false: the trainer seeds
  the initial weights too (dated erratum in docs/BLUEPRINT.md).
- Measured cost: across the 40 D rows the seed SE runs 0.33 to
  3.26 times the bootstrap SE (docs/audits/2026-10-15-image-audit/seed_var_out.json, which brackets
  72 rows of F-24, its corrected twin and F-25; F-15 to F-18 and F-28 are not bracketed).
  No label moves under the three approximations. Three bracketed readings are
  seed-sensitive: F-25's S1 L2 deciding row, +0.0022 [+0.0003, +0.0039], reads
  [-0.0012, +0.0055] / [-0.00065, +0.00498] / [-0.0002, +0.0064]; F-24's S1 corrected-twin
  CI-clear reading is lost under two of three; F-24's S3 linear CI-positive qualifier is
  lost under all three. A fourth, descriptive reading, the primary S3 L3 Mn_r below-zero
  value behind F-25's post-hoc "same shape" sentence, has its upper above zero under all
  three. Three seeds are two degrees of freedom; the component is bracketed, not measured.
- Rule: a registration states what its interval conditions on, in the regime line, and
  either registers a seed-inclusive interval beside the cluster bootstrap or says the seed
  component is unmeasured; a disclosure about a trainer is written after reading the
  trainer.
- Not yet followed by: F-28's SURVIVES-STRONGER cells and the F-15 to F-18 margins, which
  carry the conditioning note but no bracket (F-28's dated note of 2026-10-16 says so).

## 3. A scorer that ran live without its support clip

- Mechanism: the frozen Stage-C heads (tools/train_outcome_head.py) export TRAIN moments
  but no TRAIN support, and the live scorer applies only the [0, 1] output clip; the
  standardization pathology that F-22 (iii) records for Stage R reached the live decisions
  of F-21, where the record said nothing about it. Stage A was pinned with "the support
  clip live" without back-checking Stage C.
- Measured cost: a counterfactual TRAIN-support clip changes 41 of
  17,185 consulted decisions on arm 6 and 41 of 17,616
  on arm 7 (0.24% / 0.23%); a first-order estimate of
  the direct tokens/call effect is at most 0.0119 / 0.0116 (five drafted
  tokens between a stop at position 1 and an extension to six; the rest of a changed
  prompt's trajectory is not priced), inside every interval of F-21; the replay matches all
  logged decisions (docs/audits/2026-10-15-image-audit/replay_c1.json).
- Rule: a scorer that runs live carries its TRAIN support clip, pinned at the freeze; when
  a pathology is found in one stage, every stage that shares the code path is back-checked
  in the same landing.

## 4. The percentile bootstrap at thirty clusters

- Mechanism: a percentile cluster bootstrap narrows by (n-1)/n and uses z where t belongs,
  so it under-covers at small cluster counts; src/sideband/stats.py called it "the
  conservative end" (relative to Clopper-Pearson), and no document disclosed the
  shortfall at the record's cluster counts.
- Measured cost: coverage 0.897 / 0.939 / 0.948 at 10 / 30 / 60 clusters for a
  nominal 0.95 on an F-24-shaped paired simulation of paired_cluster_delta_ci
  (docs/audits/2026-10-15-image-audit/coverage_out.json). The nearest label-deciding bound to the +0.005 floor is
  F-28's RN at L1 replication gate upper +0.004951 (results/real/readers_s3_r.json),
  which a t-for-z correction carries to +0.005026: under that correction the cell would
  read NOT-SHOWN instead of ABSORBED by the frozen rule, while the registered estimator is
  the percentile bootstrap, the label stands as registered, and the final S3 word
  K-2-ISOLATED does not change (F-28's dated note).
- Rule: METHOD states the coverage of the interval method at the cluster count in use
  before the first landing that uses it; a new instrument at thirty clusters uses a
  t-multiplier or a bias-corrected bootstrap and says which.
- Not yet followed by: every landed interval, by construction; the record discloses the
  one cell the correction would move and leaves the labels as registered.

## 5. A sign sentence from one seed

- Mechanism: the synthetic experiments ran one seed per curve (e04: seed 200), and F-4
  wrote "net harmful at every offset" from that curve at rho 0.6.
- Measured cost: over seeds 200 to 209 the offset-1 value is +0.0005 on average
  (SE 0.0010), negative on 5 of 10, with the committed seed the most negative of the ten;
  offsets 2 to 6 are negative on all ten, so the rule of thumb stands and one committed
  clause does not (docs/audits/2026-10-15-image-audit/f4_seeds_out.json).
- Rule: a sign sentence is written only after the seeds that could overturn it have run;
  a curve from one seed is labelled as one seed in the finding's regime line (F-4's regime
  line carries that clause since 2026-10-16; F-3 and F-5 are one-seed curves too).

## 6. A ledger that omits a term that differs between arms

- Mechanism: F-9's bit ledger priced corrections and hints but not the bonus token the
  verifier emits when a whole block is accepted, and the omission was not listed among the
  ledger's caveats; the bonus rate differs between arms, so the omission favours the arm
  it was meant to judge.
- Measured cost: with the bonus term priced the dense hint's break-even budget of 0.162
  bits per token is about 26% high and the loss ratio reads about
  26:1 instead of 20:1; the direction holds
  (docs/audits/2026-10-15-image-audit/e07_ledger_out.json).
- Rule: a ledger lists every term it omits and says whether each is arm-invariant; a term
  that is not arm-invariant is priced or no budget number is stated.

## 7. Counts and dates in prose

- Mechanism: counts were typed on a date and never re-measured: 30 path-bearing files
  (80 at HEAD), 609 and 711 tests (734), 27 findings in the lint line (29), 45 test files
  (47), 40 top-level tools (41), "batch-16" in a payload for a batch-10 run, "smoke runs
  no longer overwrite evidence" when each script's own flag still does, and the
  tool-docstring counts of docs/CONVENTIONS.md.
- Measured cost: seven stale statements a reader can falsify with one command each; no
  number of the record moved. This lane's first draft typed three more ("fourteen files",
  a helper count that did not add up, "two path kinds"), caught by its reviewers.
- Rule: every count in prose carries its date and the command that measured it, is
  written into the file by the generator that measured it (never retyped from a print),
  and is re-measured whenever the quantity it counts can have changed, not only when the
  file is touched.
- Not yet followed by: the counts in this file and in README.md, which carry their date but
  not their commands; and the next landing that adds a test or a tool moves 734 and 41.

## 8. One provenance stamp with two meanings

- Mechanism: the instruments' git helpers disagree on what -dirty means. Measured at HEAD
  on 2026-10-16: in tools/run_*.py twelve copies count modified tracked files only and four
  count untracked files too (run_probes, run_posthoc_topic, run_k3_arms,
  run_error_predictor); the adapter hf_specdec, the harvesters and the trainers count
  untracked files, 20 plain `git status --porcelain` call sites against 13 with
  --untracked-files=no under src/, tools/ and experiments/ (the harness's tools/cc
  excluded); two documents each described one of the behaviours as the rule.
- Measured cost: a provenance reader gets contradictory definitions; nothing is unattested,
  but what a stamp attests must be read from the instrument's own helper.
- Rule: one provenance helper in the library with one definition; until a frozen
  instrument's copy is retired, the record names which definition each payload carries.
- Not yet followed by: every instrument and the adapter; the dated notes of 2026-10-16 in
  docs/SHARP_EDGES.md and docs/REPORT.md give the split.

## 9. A bold claim without a forward pointer

- Mechanism: the registration log announced EXISTENCE CONFIRMED in bold at two sites and
  in two verdict lines, and later read ABSORBED and K-2 FIRED thousands of lines below;
  nothing at the claims pointed forward, so a top-down reader or a quotation of the bold
  line gives the opposite of the record's final state.
- Measured cost: no number, but the one defect both walkthrough readers of the audit hit
  first; the premise paragraph and docs/REPORT.md's abstract carried the same exposure.
- Rule: when a later entry overturns or narrows a bold claim, the landing that records the
  later entry appends a dated forward pointer at the claim in the same commit; the
  registered text is never rewritten.
- Not yet followed by: CITATION.cff's abstract, which still reads "existence is shown"
  (the export tool rewrites that file's authors block, so its text is lane C's to touch).

## 10. Undefined voices

- Mechanism: the registration log scored predictions as "the assistant's" against "the
  critic's" and reported "critic-recomputed to 0.0" without saying that the assistant is
  an AI co-author, the critic an LLM review agent, and the user, operator and owner one
  person.
- Measured cost: the review chain read as more independent than it is, to every reader
  who did not already know the harness.
- Rule: a document that names roles defines them in its front matter; an LLM review is
  named as such wherever its recompute is cited.

## 11. A threshold supported by the run it then judged

- Mechanism: the R1 fidelity rider's entropy tolerance cited "v2 max 0.0773" among its
  support, and v2 was the rerun then judged against that tolerance; both payloads arrived
  in one commit and the text never defined v2.
- Measured cost: the entropy leg's pass is not independent of its threshold; the overlap
  and mass legs are independent and stand, and the AND-structure limits what the entropy
  leg alone licenses (dated erratum in docs/BLUEPRINT.md).
- Rule: calibration data and the judged run are different draws, and the registration
  says which draw supports each tolerance.

## 12. Citations recalled from memory

- Mechanism: an attribute of a benchmark ("seeded realizations") entered registered text
  from a recalled idea list; the landing's source check found no such thing, and the
  correction sat far from the claim.
- Measured cost: one false attribute in registered text, corrected in its OUTCOME; other
  recalled identifiers remain marked "to verify" in docs/PRIOR_ART.md.
- Rule: an identifier or attribute recalled rather than read is marked "recalled,
  unverified" at the point of use until it is read at the source; a correction is placed
  beside the claim, not only in the outcome.
- Not yet followed by: the recalled identifiers docs/PRIOR_ART.md lists for verification,
  a lane of their own.

## 13. Absolute paths stored in evidence

- Mechanism: instruments recorded the operator's absolute invocation paths in payloads,
  and three recorded path kinds are read back: the Phase-3 companion paths as basenames
  by the frozen reader-lens tool with the running OS's semantics, the amendment's rider
  path by one test, and a relative backslash harvest_dir by one prefetch test.
- Measured cost: six tests red on a fresh Linux clone (three, two and one) until lane A
  (c41f9f1, 2026-10-16) handled them test-side; 80 tracked payloads under results/ and
  87 tracked files tree-wide carry such paths (git grep -l -E on the home-path pattern)
  and are disclosed, not edited.
- Rule: an instrument stores repository-relative paths; a reader that must consume a
  recorded path normalises it with PureWindowsPath before taking a name.
- Not yet followed by: the instruments, whose shared guard does not relativize paths, so a
  new run still records the operator's paths (README.md's provenance note says so).

## 14. A smoke flag that writes into the evidence

- Mechanism: the driver's --smoke redirects to a gitignored folder, but each experiment
  script's own --smoke does not, and the release notes generalised the driver's fix.
- Measured cost: a one-command rerun of a script dirties a committed payload (caught by the
  evidence-bytes test and git status; no committed number changed).
- Rule: a smoke path redirects at the script level, and the document that claims a fix
  names the exact entry point it covers.
- Not yet followed by: experiments/e01 to e07, lane C's fix.

## 15. The audit method that found these

- Mechanism: twenty-four finders read the code in two modes, a tone reader read the
  registration log, two walkthrough readers used the export, and twelve refuters re-derived
  every number with the default set to refute.
- Measured cost: of 375 findings, 45 were refuted and 136 downgraded; the raw finder list
  would have misled by about half, and zero committed labels were overturned.
- Rule: a finding is acted on after a refuter has recomputed it; a review that cannot be
  recomputed is labelled judgement, as the tone section of the audit report is.
- Not yet followed by: this lane itself, which acted on B1 (verified by the orchestrator's
  own read and re-verified here, no refuter) and on B7 (tone, judgement, no refuter), and
  says so; the lane's own three reviewers then found eleven wording and count errors in its
  first draft, which is the rule's point.

## 16. The site survey before registration

- Mechanism: two of the record's largest turns were arguable before any run. OQ-16's
  reconstruction target is the lm_head input, so the softmax-bottleneck identity settles it
  (F-23's dated note of 2026-10-18); and the first free baseline left token ids out while, at
  S3, the published analyses of MoE routing say routing follows token identity (F-24's dated
  note of the same day: consistent with the absorption measured, not a prediction of it,
  since the re-test added token ids and the standardized state in one arm). The registration
  apparatus checks procedure, not premises, so it could not catch either: a kill criterion
  and a pinned prediction test what was asked, not whether the question was already answered.
- Measured cost: the OQ-16 lane through its Stage R run and Stage A freeze (F-22, F-23); the
  existence claims F-15 and F-17 and their re-tests F-24, F-25, F-28 and F-29, at readers
  below the practice the probing references describe (untuned, where Pimentel et al. ask for
  the highest-performing probe available; scored on top-1 accuracy; on raw inputs at F-15 and
  F-17). Counted in registered stages and findings, not hours: two stages of OQ-16 and four
  re-test findings. The cold read of 2026-10-18 (five reviewers briefed without the record's
  conclusions; docs/PUBLIC_CUT_PLAN.md 15.8) named both. [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
- Rule: before a freeze, write the strongest "already known, or settled by an identity"
  argument against the question; read the three nearest papers literally; read ten raw
  samples of the data in hand; run a tuned standard baseline. Formalise only what survives
  that page, and put the papers the argument needed into docs/PRIOR_ART.md before the
  registration, not after the result (its 2026-10-18 additions are the ones this record
  needed).
- Not yet followed by: every registration in this record, all of which predate the rule, and
  the harness, which has no pre-registration checklist step for it.

# Changelog

Dates are commit dates from `git log --date=short` (70 commits on main as
of 2026-09-05, HEAD 8542ef5; every commit is authored `sideband
<sideband@local>`). Entries are grouped by the arc they belong to; short
hashes are given so that the commits the registered documents cite by hash
can be matched. The version
labels that appear in the history (v0.1.0, v0.2.0, v0.2.1, all on
2026-08-29) were never git-tagged; v0.3.0 is the first tagged release and
is pending (docs/RELEASE_NOTES.md). Finding ids (F-n), decisions (D-n),
open questions (OQ-n) and kill criteria (K-n) refer to FINDINGS.md,
DECISIONS.md, OPEN_QUESTIONS.md and docs/WHY_THIS_DIES.md. Arc vocabulary
(rung, fold-back, void semantics, rider, stale-target control, tap,
byproduct, critic-gated) is defined in docs/GLOSSARY.md; the findings map
with headline numbers is docs/FINDINGS_INDEX.md.

Dated extension (2026-10-01): the sections from `[0.3.0]` down were written
on 2026-09-05; the sections between here and `[0.3.0]` were added on
2026-10-01 from `git log --date=short` on branch `espalier-trial` (HEAD
f8fc727, 94 commits; `main` sits at c23f214, the F-26 landing, 13 commits
behind it; nothing is tagged). Subjects after f1aabe4 follow the harness
`<type>(<scope>): <description>` convention.

Dated extension (2026-10-02): the section between here and `2026-10-01` was
added on 2026-10-02 from `git log --date=short` on branch `espalier-trial`
(HEAD 9130d16, 99 commits; `main` still sits at c23f214, 81 commits, 18
behind it; nothing is tagged). The 2026-10-01 paragraph's "between here and
`[0.3.0]`" now also spans this section, and the 2026-10-01 section gains the
two commits of that day it lacked (28c110f, which could not cite itself, and
eb0154d), each marked as added on 2026-10-02.

## 2026-10-19 - The pinned export: the Zenodo DOI filled, the deposit manifest, the release (branch main)

- (the source commit of the release export; its hash is recorded in the handoff's memory row;
  dated note 2026-10-19: superseded as the release's source by the second source commit, the
  bullet below)
  docs(release): the three Zenodo DOI placeholders are filled at the source
  commit (docs/PUBLIC_CUT_PLAN.md 15.10): the root README's two DOI lines and [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  the root CITATION.cff's message name DOI 10.5281/zenodo.23462826, the record
  reserved on 2026-10-18 for the gitignored raws; the release date is given to
  the export by its flag on the day. The root README's data table gains the row of
  the twelve seed-6 and replay folders (1,281 files, 1,086,399,860 bytes) and
  its total is re-measured at 14,456,199,684 bytes, about 14.5 GB (plan 13.3's
  deferred re-measure, by hand since the packer gave way to the hand-zipped
  deposit); its deposit sentence describes the deposit as it was made: exactly
  those 5,175 files in 34 zip archives, one per byproduct folder and one
  holding the 24 harvest shards by bare file name, their folders given in
  docs/DATA.md. docs/DATA.md gains
  a dated section tabulating the 34 archives (source folder, files inside, bytes,
  sha256) from the list the packing script wrote beside them, with the
  reconciliation against the 2026-09-05 inventory (the twelve seed-6 and replay
  folders of 2026-10-09 and 2026-10-10 hold the other 1,281 files) and the shard
  archive's flat layout with each shard's folder; the two list files are kept in
  the private record. This folder's README.md gives its two counts of the raws
  (3,894 files, 13.4 GB) dated clauses with the 2026-10-19 figures. The export
  test's three real-tree
  pending lists shrink to the release date alone. docs/SHARP_EDGES.md gains the
  entry on `.espalier-state/` being one folder per checkout shared by every
  session open in it. No tool change: the three hardening items the previous
  entry's review left open (the workflow reader's quoted-key gap, a per-job head
  check of the sibling clones, an environment allowlist) go to a follow-up, the
  clone heads being read by hand from the proof's scratch for this release.
- (the second source commit; its hash is in the handoff's memory row; dated note
  2026-10-19, later: superseded as the release's source by the third source commit,
  the bullet below)
  test(ci): three tests skip under CI by name, each with its reason, and one
  assertion is narrowed with a dated amendment. The
  public cut's first CI run (GitHub's ubuntu-24.04 runner, Python 3.12, numpy
  2.5.4, scipy 1.18.1, scipy-openblas 0.3.34.106.0, 2 CPUs; 2026-10-19) read
  4 failed, 716 passed, 39 skipped in the sideband job while amber and
  lockstep passed: the three lens-rider reproductions of the reader-and-lens
  landing tests (the frozen instrument's byte-for-byte rider gate refused
  before labelling) and the prefetch-r2 replay-rule fixture test (its twin's
  fallback margin read NEGATIVE -0.0011 where this box reads exactly zero, so
  the share read -416.67, every earlier assertion of that test holding there
  and every later one whose value its output prints satisfied).
  Four Docker containers on this box's CPU passed all four: python:3.12 with
  the runner's versions; numpy 2.3.5 with scipy 1.17.1; the runner's versions
  with the same OpenBLAS build at 2 threads on 2 pinned CPUs; and
  ubuntu:24.04 under the same. The runner's CPU and the kernel OpenBLAS
  selects for it is the leading candidate; which operation moves is not
  measured. The guard on the three is `skipif(bool(os.environ.get("CI"))
  and os.environ.get("SIDEBAND_REQUIRE_CPU_BOUND") != "1")`; the fourth's
  share assertion is conditioned on a positive twin margin; no instrument
  gate is loosened and no instrument changes; the export's proof on this box still
  runs the three (the release export's proof receipt, kept in the private
  record, is the witness; the first export's read 724 passed, 35 skipped).
  tests/test_prefetch_r2.py is a registration-pinned file, so the dated
  amendment sits at the end of docs/BLUEPRINT.md and the file's sha256
  moves to 7528cfef155d. The root
  README's GPU sentence ("exact on the author's machine") and CPU bullet,
  tests/README's "Fail, not skip" section, the four
  module docstrings, docs/REPRODUCE.md and docs/RELEASE_NOTES.md say so,
  dated, and docs/SHARP_EDGES.md gains the entry. The first export (688c547)
  and its PASSED proof stay in the private record; the release export is the
  one at this commit. Dated note 2026-10-19, later: the proof stays private;
  the first export's commit and its failed run stay on the release repository,
  reachable by SHA and listed under its Actions (kept or deleted on the owner's
  call, the bullet below).
- (the third source commit; its hash is in the handoff's memory row)
  docs(release): one shipped sentence for a reader on another machine, after
  the owner's word on this approach, read by 16:43 (docs/PUBLIC_CUT_PLAN.md 15.10 [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  records it verbatim; 15.11 the lane): the root README's CPU bullet and
  tests/README's "Fail, not skip" paragraph say to set `CI=1` before `pytest` to
  skip the three named machine-bound lens gates, no other test's outcome
  depending on that variable in a clone that git can read, with
  `SIDEBAND_REQUIRE_CPU_BOUND=1` running them regardless; docs/RELEASE_NOTES.md's
  step-8 note records that the word on this approach was read by 16:43 and that
  its rule holds for the word on the narrowed assertion. No tool, test-code,
  workflow or instrument change. The second export's PASSED proof stays in the
  private record, while its commit (01def67) and its green CI run stay on the
  release repository outside main's history, reachable by SHA and listed under
  its Actions, as the first export's commit and failed run do (the owner's call
  on keeping or deleting them is asked before the flip and recorded in the
  private plan; kept until then: that run is the failure this section
  describes); the release export is the one at this commit.

## 2026-10-18 - The owner's calls of the evening: decision 2, items 12, 16 and 19; the sibling proof stages (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row)
  feat(export): the operator's four calls of 2026-10-18 landed (docs/PUBLIC_CUT_PLAN.md [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  15.9) and `prove` gains the amber and lockstep stages. Decision 2 ("Ship it"):
  amber's results/p1, p4, p5 and p6 (Llama-generated token ids, 1,384 tracked files)
  ship under the root Llama notice; the errata plan's step-1 sentence becomes a
  decided keep in the AMBER spec (record_decisions, eight entries now), with a dated
  note under the bullet in amber's own record, so the export's last record-flag
  drops. Item 16 ("Keep the pointer."): amber's prior-art note keeps pointing at
  sideband's 2026-10-11 note; no bytes change. Item 12 ("we can ship that one too"):
  lockstep's commercial register ships as written, with dated notes at F-8, docs/09's
  EF-4 and D-14 pointing to its audit's item B3. Item 19 ("im not doing council for
  this"; "lets put it out and skip the search for now"): amber's gate before
  publication is waived by the owner in a dated line under the gate (no counsel
  review; the prior-art search OQ-6 asks for not re-run), with dated lines under OQ-6
  and K-1. The pins move to amber 0b061b5 (four files, 22 inserted lines; pytest 160
  passed, lint OK) and lockstep a84bef4 (three notes in the audit item's own words;
  its five validation commands exit 0 in a copy), each commit amended once before any
  push after the critic's round. `prove` reads the exported root workflow right after
  the clone and runs each sibling folder's job as the workflow states it (one clone
  and one venv per job, the job's working directory and env with the venv first on
  PATH, each run line as that venv's own program, then its pip freeze, in the
  workflow's order; a workflow the strict reader cannot follow, a sibling with no
  job, a job for no exported folder or a run line the proof cannot run fails the
  proof right after the clone, before any venv is built), in place of the two
  refusals; the scratch folder must be empty; the proof stamp is bound to the
  manifest's bytes as the gate stamp is, and an amended or rebased sibling pin is a
  binding blocker. The commands are the workflow's; the interpreter, the platform
  and the line endings are this box's, and the receipt says so. Four new tests and
  three extended ones pin the reader, the translator and the stages (the fake-run prove
  test asserts the sideband-only receipt resolves no sibling job, and that the sideband
  job's run lines are among the hard-coded stages). The root README's provenance comment names the
  new pins. The first verification export, at the worktree snapshot fe52a31 with the
  pre-amendment pins: 2,731 files, 285,584,431 bytes; NO-GO 4, every blocker a pending
  placeholder (the Zenodo DOI three times, the release date), every other class 0; its
  proof PASSED-NOGO, 21 stages at exit 0, by the tool before the review's fix batch (the
  landing tool runs 25 stages there); the later export and runs are recorded in 15.9.

## 2026-10-18 - The cold read's dated-note batch across the three folders (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row)
  docs(record): the pre-release dated-note batch of docs/PUBLIC_CUT_PLAN.md [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  15.8, after five unanchored reviewers read the three repositories cold on
  2026-10-18. In this repository: docs/PRIOR_ART.md gains a 2026-10-18
  section (twelve papers, each fetched that day: the softmax bottleneck
  behind F-23, the MoE-routing analyses behind F-24, future-token
  information, probing practice, routing as signal, Spec-Bench); FINDINGS.md
  gains dated notes under F-23 and F-24 placing the record's own concessions
  against that literature; tests/test_frozen_imports_pinned.py pins the two
  frozen modules the later instruments import by bare name
  (tools/run_probes.py, tools/run_posthoc_topic.py), with `-text` lines and
  the evidence pins regenerated (+2); docs/LESSONS.md entry 16 (the site
  survey before registration); tools/lint_findings.py's docstring scopes
  "CI" to the public workflow. In the export tool: decision 1 of 2026-10-18
  (keep) turns the seven amber critic-script flags into decided keeps
  (record_decisions), and both sibling pins move: amber to 5fbc9bd (e9bec74:
  the P1 stratified diagnostic and its first-screen note, F-11's dated note,
  prior-art additions, a withdrawn-reading note; 5fbc9bd: the note's
  correction after the critic's recompute, the diagnostic's library versions)
  and lockstep to 4b6bcc1 (2e20b0f: F-21, an erratum to F-2; the
  vector-coverage note; ts_zip's determinism quoted; F-16's scope note; the
  MIT licence and PEP 639 fields; the owner's provenance line; `__all__`;
  4b6bcc1: the F-16 note's correction, the coverage script's self-test). The
  root README names both new pins and
  carries a dated sentence beside the amber headline figures and scope
  clauses on the bf16 sentence and the conformance vectors. Open for the
  operator: decision 2 (the only record-flag left), lockstep's commercial
  register in docs/08 and the cent-precise cost figures in docs/09 and F-8,
  and amber's pointer to sideband's 2026-10-11 prior-art note (plan 15.8
  items 11, 12 and 16).

## 2026-10-18 - The lockstep survey: the LOCKSTEP FolderSpec, the audit, lockstep's front door (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(export): the lockstep folder enters
  the public cut (docs/PUBLIC_CUT_PLAN.md 15.6, 15.7). The LOCKSTEP FolderSpec [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  binds the lockstep checkout at 145e33a, the fourth of four commits of
  2026-10-18 revising lockstep's front door or its audit report in its own
  repository (not pushed; Actions are enabled on its remote):
  the planning document, the review with its parked proposals, the patent notes
  and the workflow withheld whole; TP-5's body withheld by section, because the
  agent harness's reference checker resolves the citations of TP-5 to the file;
  the two patent numbers and their claim reading withheld by anchor at two
  sites, the counsel sentences around them kept; OQ-9, OQ-10 and two prior-art
  passages withheld by the operator's call 3 of 2026-10-18; the harness and the
  archived task packs shipped (calls 1 and 2); TP-7's two paths into the amber
  checkout scrubbed; three extra mention forms for the record's shorthand
  citations of the withheld documents; four probes for the patent numbers.
  Tool: the placeholder scan honours a residue entry whose own text carries the
  match; prove refuses lockstep/ until it has a proof stage, as it refuses
  amber/. The root CI gains a lockstep job (the five validation commands), the
  allowlist 40 lockstep entries, SIDEBAND's spec four residue entries for
  sideband lines naming the withheld review; the root README's lockstep section
  is rewritten from lockstep's record at the pin with its placeholder removed,
  NOTICE states that the lockstep folder runs no neural model, and
  docs/ECOSYSTEM.md's "amber's production coder" carries a dated note. Tests:
  the lockstep spec's pins and a three-folder real-tree fixture (skipped where a
  sibling checkout is absent, failing under SIDEBAND_REQUIRE_AMBER=1 or
  SIDEBAND_REQUIRE_LOCKSTEP=1). The read-only image audit of lockstep (19 Opus
  agents; 165 findings, 131 confirmed, 31 downgraded, 1 upgraded, 2 refuted, 8
  added; 171 survivors, 25 high in ten distinct defects) is lockstep's
  docs/audits/2026-10-18-image-audit/README.md, committed with lockstep's new
  first screen and a .gitattributes that keeps the two conformance-vector copies
  LF in a clone (a Windows clone made with core.autocrlf=true had failed
  self-check; the generator's half stays open). Staging exports: 69 blockers at
  cdfe0b3 with the draft spec; with the final spec, the allowlist and the root
  README at the pin, 12: pending 4 and record-flag 8 (amber's open calls),
  every other class 0. Review: the critic's rounds, a code review and a
  failure-mode review, and the fix batches they led to (plan 15.7).

## 2026-10-18 - The amber survey: the AMBER FolderSpec, the audit, amber's front door (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(export): the amber folder enters
  the public cut (docs/PUBLIC_CUT_PLAN.md 15.5). The AMBER FolderSpec binds [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  the amber checkout at c917a2a, the third of three front-door commits in
  amber's own repository (not pushed; Actions are enabled on its remote):
  the workflow withheld whole, the patent passages withheld by anchor at four
  sites with K-1 and OQ-6 kept as structure (call 2), four private-name
  mentions replaced in place and one kept as residue in a payload-pinned
  file, the two saved arXiv pages kept (call 3, decided
  2026-10-17), docs/ERRATA_PLAN.md's four sibling-checkout paths scrubbed
  (call 1), the Hugging Face cache paths in eight frozen files as residue,
  eight operator flags (the seven critic scripts whose path carries the
  sibling checkouts' parent folder name; the plan's "never for public
  release" sentence). FolderSpec gains `paths_note` and `log_cites`, the
  per-folder sentences of WITHHELD.md and the commit log; the root CI gains
  an amber job; the allowlist nine amber entries; the root README's amber
  section is rewritten from amber's record at the pin with its placeholder
  removed, and NOTICE states amber's model use. Found and fixed in the tool:
  a spec whose every withheld key is exempt compiled an empty mention
  alternation, which matched every line; at review, a folder's files were
  scanned against its own withheld names only, residue entries had no
  staleness rule, and WITHHELD.md dangled an empty clause. Tests: the amber spec's pins and an
  amber real-tree fixture (skipped where the checkout is absent). The
  read-only image audit of amber (19 Opus agents; 141 findings, 101 confirmed,
  38 downgraded, 2 upgraded, 0 refuted, 11 added; 152 survivors, 7 high; no
  finding's status word changed, three pre-registered P3 band readings and
  F-12's byte breakdown among the survivors) is amber's
  docs/audits/2026-10-17-image-audit/README.md,
  committed with amber's new first screen and two pyproject lines (the
  corrected description; scipy declared for the one test that needs it).
  Staging exports: 41 blockers at 69b437c with the draft spec; with the final
  spec and sources at the pin, 14 blockers: layout 1, pending 5, record-flag 8 (the lockstep layout blocker,
  the pending markers and the operator flags), every other class 0.

## 2026-10-17 - The export tool's per-folder binding (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(export): the per-folder binding of
  docs/PUBLIC_CUT_PLAN.md 10.7, landed before the sibling surveys by the [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  operator's word of 2026-10-17 (plan section 15). FolderSpec gains `checkout`
  and `commit`; `Export.bind` resolves each folder's private checkout and
  pinned commit, overridable per run by `--checkout NAME=PATH` and
  `--folder-commit NAME=REV`; the folder's tree, commit log and WITHHELD.md
  come from that binding; the pre-push seat-belt's forbidden remotes are the
  union over every bound checkout; the manifest records `source_commits` and
  `checkouts`, `scan` re-binds from them, and `prove` carries `source_commits`
  in the receipt. From the review batch: a sibling exported at a commit other
  than its spec's pin is a blocker of class binding, at export and at scan;
  every folder's withheld blobs are registered before any folder is edited, so
  the digest scrub no longer depends on the export order; the hook's forbidden
  list carries each sibling spec's own checkout's remotes too, and a sibling
  with no remote anywhere is a blocker; a refusal quotes git's stderr for a
  plain directory and says in its own words that a bare repository is not a
  work tree, and scan's says what scan can do. Found by the lane's two dry exports and fixed
  here: the mention marker sorted names by lower case alone, so a case-variant
  pair fell to set order and two exports of one tree differed in one marker of
  ESPALIER_MEMORY.md; the key is now (lower case, text), probed in fresh
  processes under seven hash seeds in test_helpers. New fixture test
  test_fixture_sibling_folder_is_bound_to_its_own_checkout_and_pin: a second
  private repository exported at a pin older than its HEAD, each refusal the
  test names (the unresolvable spec pin is owed its line), its
  own remote refused by the hook, scan's re-binding, the pin and no-remote
  blockers, a refused re-run leaving the previous export in place, a
  sibling's withheld digest scrubbed from a folder exported before it, a
  spec's own remote forbidden when a run binds a clone. Proof on 2026-10-17,
  on the final tool and test bytes (this entry was written after the runs;
  the whole suite ran again on the untouched final tree before the commit):
  the export test file 20 passed in 831.54 s, the
  three enumerator-pin files 16 passed, ruff clean, the before and after
  dry exports at the same verdict and file count with only the two generated
  files differing. Plan section 15 also records the operator's four calls on
  amber (docs/ERRATA_PLAN.md ships with four of its six path lines scrubbed
  and two kept under the own-checkout rule, the patent chart withheld, the
  saved arXiv pages withheld with a digest-scan question left to the operator,
  the commit log ships, the bundle carries the three histories) and the amber
  gate counts measured at 69b437c.

## 2026-10-17 - Lane D of the image audit: plain-language first screens and tests/README.md (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) docs(craft): lane D of the 2026-10-15
  image audit (docs/PUBLIC_CUT_PLAN.md 14.3). README.md opens with a [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  plain-language question, answer and roles paragraph and a term list before
  its first label, the 2026-10-14 front door kept beneath under "The verdict
  in the record's words"; its how-to-read list, Quickstart and repo-map
  counts re-measured on 2026-10-17 (53 test files, 775 tests, 30 findings, 43
  top-level tools). The public cut's root README gets the same opening, its
  two repeated sentences removed and F-29 carried into its existence row and
  kill-criteria paragraph (it still read "S1 not run"), and README.md's two
  remaining "S1 not run" clauses gain dated pointers to F-29; CITATION.cff's
  dated note gains the F-29 clause. New: tests/README.md (the kinds of test
  file, fail-vs-skip as measured, the six freeze-pinned test files, how to
  run), with a dated pointer to it in docs/CONVENTIONS.md "Tests". Dated
  notes in the audit README and plan 14.3. No frozen tool,
  payload, state file or registered text changed; no label moved.

## 2026-10-17 - The recovered critic folder, the public-cut plan's lever 3 (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) docs(record): the recovered critic
  folder - docs/audits/critic-recovered/ with recover.py, gen_readme.py and
  its two manifests: 308 of the 2026-10-16 archive's 309 critic scratch
  files (a selection of the reviewer's recompute scripts, outputs and round
  reports of 2026-10-01 to 2026-10-16: the archive's rule took the top-level
  files of four suffixes inside critic-named folders) laid out by session,
  home paths scrubbed to `<user>`, every byte pinned, lanes attributed by
  commit-time windows; the five public-cut lanes' rounds, one copy of
  docs/REPORT.md and one diff hunk of the withheld idea file withheld from
  the public cut, the rest frozen and exported; the folder pinned `-text`,
  its session folders left out of ruff, all of it out of the evidence-bytes
  citer scans (RECOVERED_PREFIXES in
  tests/test_evidence_bytes.py and tools/evidence_pins.py);
  tests/test_critic_recovered.py; the export tool's spec extended (withhold,
  mention-exempt, residue, sweep) and its withheld-digest scan corrected for
  empty files, which had flagged the OQ-20 driver log's empty-freeze digest;
  dated notes in the image-audit README, plan 14.2 item 3, README.md and
  the root README source; a SHARP_EDGES entry on withheld-name derivation.

## 2026-10-17 - S1 reader re-test: the two registered runs landed, the S1 word (branch main)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(evidence): land the S1 reader
  re-test - both registered runs from the clean tree at 46a812f,
  results/real/readers_s1.json and readers_s1_r.json with their state files
  (36 rows each; the primary resumed at the same HEAD after a header-only
  first launch, resumed_cells 0), the word payload
  results/real/readers_s1_word.json written at the launch HEAD; R-N
  (hz-rescaled) ABSORBED; R-T (two-tower) ABSORBED; R-L (longer budget)
  ABSORBED; the S1 word K-2-NOT-OVERTURNED-AT-S1; F-29 with its regime and
  source lines; a dated note in F-24's status cell; the K-2 STATUS line in
  docs/WHY_THIS_DIES.md; the OQ-17 note; the dated pointer under the
  READER-AND-LENS block; pointers in README, docs/REPORT.md,
  docs/FINDINGS_INDEX.md, docs/GLOSSARY.md; tests/test_reader_s1_landing.py;
  tools/run_reader_s1.py joins the frozen closure (seventeen files, fourteen
  attested); the block's OUTCOME.
- 46a812f (2026-10-16) feat(registration): freeze the S1 reader re-test and
  its rider - the freeze commit; the runs launched from it.

## 2026-10-16 - S1 reader re-test: the registration, the word instrument and the F-24 support artifacts (branch main)

- (this freeze's commit; its hash is in the handoff's memory row)
  feat(registration): freeze the S1 reader re-test and its rider. Lever 1
  of docs/PUBLIC_CUT_PLAN.md section 14.2: the S1 READER RE-TEST [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  REGISTRATION appended at the end of docs/BLUEPRINT.md (the frozen
  tools/run_reader_lens.py `s1` stage runs the three F-28 readers R-N, R-T
  and R-L at the S1 gate cell on both committed S1 harvests, 36 cells per
  harvest; the prediction, the per-reader labels, the S1 word
  K-2-NOT-OVERTURNED / REOPENED / ISOLATED / UNSETTLED / INCOMPLETE-AT-S1
  and the consequences pinned before any reader-variant cell trains; the
  pre-freeze smoke of one committed-type R-0 cell disclosed, CPU / CUDA
  1.217); its index row; a new instrument tools/run_reader_s1.py that
  imports the frozen tool by bare name, asserts its raw-byte sha and
  issues the S1 word from the frozen labels (the OQ-18 amended-instrument
  precedent), with tests/test_reader_s1.py (every word branch, the conclude
  flow on fake payloads, every refusal, the sha assertion); `-text` lines
  for both and the test hand-pinned in tests/test_evidence_bytes.py. Lever
  2, the rider: docs/audits/2026-10-16-f24-support/ with three committed
  scripts and their outputs regenerating F-24's three support figures
  (the cross-seed collapse +0.1127 and the same-subtrahend control
  +0.4815 on the S3 primary; the position-only predictor equal to the floor
  at every anchor index on both primaries; the S1 per-anchor L2 medians hz
  65.21, slots 11.14, TOK 5.66), every pin held (F-24's "+0.58..+0.76"
  covers three of the four harvests; the S3 replication's recorded +0.4062
  / +0.4500 is named); F-24's dated note of 2026-10-16 points there. The
  critic's design round (NO-GO on five blocking objections, all applied)
  and the code review are recorded at the end of the block. No frozen tool, payload, state file or
  registered text changed; no label moved; the registered runs launch from
  this commit.

## 2026-10-16 - Image audit lane C: guards as strong as their names; the science-lever plan (branch main)

- (this landing's first commit; its hash is in the handoff's memory row)
  docs(plan): docs/PUBLIC_CUT_PLAN.md section 14, the operator's decisions [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  of 2026-10-16: the public cut stays Tier C with a fresh history; four
  science levers become lanes (an S1 stronger-reader re-test with the F-24
  support-number artifacts as its rider, a recovered critic folder, the
  private history as a restricted bundle beside the Zenodo deposit with a
  signed tag); the lane order and the cost estimates, as estimates.
- (this landing's second commit; its hash is in the handoff's memory row)
  test(guards): lane C of the 2026-10-15 image audit, section C. The
  findings lint reads a wrapped source bullet whole; an absolute
  evidence-citation pin (tests/evidence_pins.json, tools/evidence_pins.py,
  check 6 of the evidence-bytes test); an F-24 landing test attesting the
  fullfree instrument; the twin, rider-diagnostic and control verdicts
  pinned; a Stage-I positive control; a D-6 telemetry-stream test; a
  run_block index test; the tautology pinned; the selection key called
  from tools/run_error_predictor.py; both lens builders pinned; the
  per-script --smoke root fix (experiments/_util.py smoke_results(), an LF
  writer); the sharp-variant cached-vs-uncached asserts restored;
  weights_only on the adapter load (tools/run_k3_arms.py's blob moves; the
  OQ-20 environment capture records the old one and the path never ran);
  the file://// fold in tools/export_public_cut.py and its hook pipeline [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  (the tool's digest moves); CITATION.cff's dated forward pointer with
  K-2's scope; dated closing lines in docs/RELEASE_NOTES.md,
  docs/SHARP_EDGES.md, docs/TASK_RECIPES.md and the audit report;
  .gitattributes gains `-text` lines for the two files the lane made
  sha-cited (tools/run_fullfree.py, tools/build_concept_groups.py). The
  e01 and e07 payloads, stored CRLF, flip to LF when next regenerated. No
  frozen tool, payload, state file or registered text changed; no label
  moved.

## 2026-10-16 - Image audit lanes A and B: CI portability, then the record errata batch (branch main)

- c41f9f1 test: make the suite green on a Linux clone without torch (lane A,
  13 files under tests/, docs/ and task-packs/; the six Linux-red landing
  tests and a seventh found by the proof fixed test-side; the frozen tools and
  payloads byte-identical; proven in a Docker python:3.12 clone with `.[dev]`
  only; 82bc72d is its memory row).
- (this landing's commit; its hash is in the handoff's memory row)
  docs(record): lane B of the 2026-10-15 image audit, the record errata
  batch. The adapter has cropped KV caches by default since b1dae57
  (2026-08-29); fifteen statements in twelve files said it recomputes
  prefixes, and each now carries a dated note (true when written) or a dated
  erratum (false when written) pointing at DECISIONS.md D-9's dated note,
  which restates the wall-clock ban on its real ground (no benchmark
  harness; logged runtimes are provenance); README.md's three front-door
  sentences and docs/public_cut/ROOT_README.md are corrected in place. Dated [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  notes record that every probe interval is conditional on the three trained
  seeds (F-24 (iii), F-25's S1 L2 deciding row, README; the BLUEPRINT
  disclosure that the seed only shuffles batch order gets a dated erratum),
  that the live Stage-C heads of F-21 ran without a support clip (41 / 41
  decisions per arm would change under one; pointers from F-22, F-27, the
  BLUEPRINT and the glossary), that the percentile cluster bootstrap covers
  about 0.94 at 30 clusters (stats.py docstring, METHOD, NOISE_FLOOR, F-24),
  that F-4's offset-1 sign at rho 0.6 is seed noise and F-9's ledger omits
  the bonus token (dated errata; a dated clause on the F-3, F-4, F-5 regime
  lines names the argmax mechanism; D-10 gains a dated note), and the stale
  counts (80 path-bearing payloads, 734 tests in 47 files, 29 findings, the
  per-script smoke flag, batch 10 in the fidelity calibration, the two
  meanings of -dirty; the F-26 summary row levelled). docs/BLUEPRINT.md gains
  a front-matter note defining its voices, forward pointers under the premise
  and the two bold EXISTENCE outcomes, errata at the R1 entropy tolerance,
  the P1 header and the SPEED-Bench attribute, and the operator's three calls
  of 2026-10-16 (the two PC-2 lines kept with dated notes; the OQ-20 command
  paths kept under RELEASE_NOTES 3.1 as extended; README gains the
  registration-order sentence). Evidence: docs/audits/2026-10-15-image-audit/
  holds the scrubbed audit report and the recompute scripts whose numbers
  entered the record, each rerun from the committed tree before the commit;
  docs/LESSONS.md closes the lane with one entry per limitation that stays in
  the evidence; tests/test_record_claims.py pins the BLUEPRINT index's line
  numbers, run_simulation's argmax default and the adapter's KV-cache default;
  docs/BLUEPRINT_INDEX.md's Line column and docs/METHOD.md's BLUEPRINT line
  citations are regenerated after the insertions.

## 2026-10-15 - Public cut: lane 2 of the decision batch, the tool and the record (branch main)

- (this landing's commit; its hash is in the handoff's memory row)
  feat(public-cut): lane 2 of the 2026-10-14 decision batch, calls PC-1,
  PC-2, PC-3, PC-6, PC-9 and PC-10; docs/PUBLIC_CUT_PLAN.md section 13 [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  records all ten calls and was written first in the lane, before any other
  edit, from the session ledger of the calls. The export tool,
  tools/export_public_cut.py (+261 -60 against HEAD): `--author` is [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  repeatable, `Name` or `Name <email>`, the entries become the authors block
  of the root CITATION.cff and of the folder's (the source's one
  pending-author entry is the anchor the block replaces; no flag and no
  identity file leave the token), docs/public_cut/identity.json (+12, new) [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  supplies the decided identity as the default for every parameter a flag
  leaves pending and for the git identity of the export commit, and an
  author's own mailbox passes the email scan on the CITATION.cff files only
  (PC-1); the 2026-10-10 memory row's third assessment sentence is withheld
  under a marker, the 2026-10-11 row's deny-list match is kept by a decided
  entry whose reason WITHHELD.md publishes, two probes flag any later
  recurrence of the withheld sentence anywhere in the folder in any case, and
  a decision covers one line, a second occurrence being a record-flag of its
  own, so `operator_flags` is empty, `record_decisions` holds three entries
  and `withheld_probes` two (PC-3); the nine gaps of plan 12.5 and 12.7 are
  closed (PC-10; plan 13.5 tabulates gap, clause, fix and test):
  home-directory paths match in any case; the sweep cuts the mathematical
  phrases out of a line instead of skipping the line, a line entry of the
  allowlist being matched against the uncut line and a word entry against
  the cut text; the hook's Python twin folds ASCII case only, as the hook's
  `tr` does, and reads the port in ASCII digits; every file outside an
  exported folder takes the withheld-name check against every folder's
  names; a provisional manifest with the merged push records is written
  before any deletion, and `scan`, `prove` and the pre-push hook refuse an
  in-progress manifest; a `previous_export` of another shape than the tool
  writes is refused before anything is read from it; the deny list matches
  the hyphenated spelling of its release-wording pattern; an exported
  .gitattributes drops the lines that NAME a withheld file and WITHHELD.md
  lists the drop, a glob that merely matches a withheld path staying because
  it pins exported files too; the frozen set is the paths whose `text`
  attribute the tree's .gitattributes leaves unset, by `git check-attr`
  itself over the tree's attribute files written into a scratch repository
  with the system and global attribute files disabled: three reviews found a
  Python reader getting a new form wrong each time, so there is no reader
  now, and the test pins the plumbing against an independent `git check-attr`
  call per .gitattributes content (62 contents, among them the forms the
  reviews found). Beside the gaps: `scan` refuses an export made by another
  revision of the tool instead of reporting a verdict about it, and the
  binding gate's hint (below) fits what the record carries. The allowlist,
  docs/public_cut/tone_allowlist.txt (+10 -6): the three reason comments [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  that carried the flag phrase record the operator's call PC-2 of 2026-10-14
  (all three kept) and the header gains a dated line and a note on its
  load-bearing blank line, so the file parses with no flagged entry; the
  header's mechanism sentence is the phrase's one remaining occurrence, and
  the 45 line and 1 word entries are unchanged. The tests:
  tests/test_export_public_cut.py (+253 -39) pins zero allowlist-flag and [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  record-flag hits, three decided keeps, the pending hits by path (the two
  survey lines and the Zenodo DOI twice in the README, the DOI and the
  release date in CITATION.cff, nothing in any folder file) and the identity
  fills, plants a fixture case for gaps 1, 2, 4 and 8, adds a test each for
  gaps 5, 6 and 9 (the ninth the plumbing of the git delegation, plus a test
  that a global attributes file does not reach the scratch repository) and
  for the authors block, the identity file and the mailbox scope, adds a
  non-ASCII spelling to the hook parity test and asserts the probe, the
  one-line rule, the scan's refusal and the hook's refusal of a provisional
  manifest; tests/test_outcome_head.py (+17 -5) says logical-processor
  count in its docstring, states the agreement claim as measured (the
  critic's two wordings handed over by lane 1) and asserts the hint's two
  forms; tests/test_evidence_bytes.py (+15 -4): the new-receipt remedy
  branches when a path-keyed digest is a blob at another path (the third
  wording) and says so when the key names no path.
  tools/train_outcome_head.py (+26 -1): the BINDING GATE REFUSED message
  appends one of two hints: when every differing value sits within a relative
  1e-12 of its committed twin, the drift hint names the two measured sources
  of such a mismatch (OPENBLAS_NUM_THREADS 2 and 24 under numpy 2.4.6; numpy
  2.3.5 against 2.4.6, docs/SHARP_EDGES.md's 2026-10-14 entry) and that the
  committed real summaries record neither; otherwise the hint says the
  mismatch is far larger than that drift. The gate is unchanged, and the tool
  is outside the frozen closure (pyproject's ruff exclusions). The record
  documents: docs/BLUEPRINT.md's v0.2.0 addendum heading gains the dated
  status note plan 10.3 named (T-A to T-D's standing from the glossary rows;
  PC-2's Flag C); OQ-7 reads TRANSFERRED to amber/ by dated notes in
  OPEN_QUESTIONS.md and docs/GLOSSARY.md (PC-6); the wall-clock sentence of
  docs/public_cut/ROOT_README.md reads "of sideband's own" with the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  prior-art clause (PC-6; an export-only source, reworded in place);
  CLAUDE.md's harness heading and docs/CONVENTIONS.md carry the main-branch
  amendment (PC-9); docs/TASK_RECIPES.md's landing recipe and
  docs/SHARP_EDGES.md's EVID-1 entry carry dated updates on the export
  policy, the sweep and the attribute lines. 17 files in the diff against
  HEAD, this entry and the plan included. Reviews, counts carried from the
  reports, whose final texts the lane's scratch keeps verbatim under
  reviews/ (the agents' own transcripts were empty when copied): the
  sideband-critic in diff mode, five reads, four NO-GO (5 blocking and 13
  advisory items with 79 numbers recomputed and one oracle count off; 2
  blocking and 7 advisory with 93 recomputed and none off; 3 blocking and 9
  advisory with 112 recomputed and one exit code off; 2 blocking and 7
  advisory with 84 recomputed and a count off by 2) and the fifth GO with 5
  advisories, 122 values recomputed and 0 off; the failure-mode reviewer,
  REQUEST CHANGES with 2 blocking gaps, 6 gaps and 10 rough edges; the code
  reviewer, REQUEST CHANGES with 3 latent defects, 5 warnings and 4 nits.
  The accepted items landed as four fix batches (the three first reads; the
  critic's second read; the critic's third read, which retired the reader
  for git itself; the critic's fourth read, which made the delegation's
  scratch-folder cleanup non-fatal after the five-file run found the
  rmtree-failure test red), each dry-run in a scratch clone before the tree
  was touched, except the real-tree pending pin, which followed a red tree
  run directly, and with the third and fourth batches' dry runs covering 3
  and 4 of the 19 tests (the first of those let the cleanup regression
  through to the five-file run, which now covers both); the lane's scratch
  labels its edit scripts fix 1 to fix 5 (1 and 2 the first batch, 3 the
  second, 4 the third, 5 the fourth), and the fifth read's advisories landed
  after its GO as this text and one test line (fix 6: the rmtree-failure
  test keeps the delegation's scratch folder in pytest's temp dir), proved
  by the five snapshot files and the re-run controls, not by another read.
  Proofs, each on the final code bytes and named by its log in plan 13.5:
  tests/test_outcome_head.py with tests/test_evidence_bytes.py, 20 passed
  in 43.88 s; tools/lint_findings.py OK at 29 findings; the frozen set
  against an independent `git check-attr` outside the test, 62 contents
  and 0 differences; a worktree export into scratch with the identity
  flags and `--release-date` (no git, no receipt; its folder files read at
  HEAD 10050ec, so the lane's record edits are swept only by the real-tree
  snapshot test), exit 0, NO-GO at 9 blockers: layout 2 (amber/ and
  lockstep/ absent), tool 1 (uncommitted), sources 1 (worktree), pending 5
  (the two survey lines and the three Zenodo DOI placeholders at the root),
  no hit in any other class, the log recording both authors in the root
  CITATION.cff, three decided keeps in the folder WITHHELD.md and the
  withheld sentence absent from the exported memory file; the same export
  without any identity flag, the identity file supplying them (the command
  line and exit 0 in its log), NO-GO at 10 blockers, the sixth pending the
  release date, which only the day's flag fills. Controls in scratch clones
  of 10050ec, every run on the test file as it lands or on the one form of it
  named below: against HEAD's tool the file does not collect (exit 2, a
  TypeError on the new spec field), so for the forms that follow the field
  was shimmed into HEAD's tool as accepted-and-ignored; form 1, the file as
  it lands, 16 failed and 3 passed in 416.44 s, the passes
  `fixture_clean_tree_reaches_go_stamp_and_push`,
  `fixture_prove_reaches_a_verdict_and_stamps_only_an_exact_passed`,
  `real_tree_frozen_files_are_byte_identical_and_anchors_matched`,
  whose inputs HEAD's tool already handles, the failures 13 on an assertion of
  their own; 1 on a refusal HEAD's tool does not raise (`pytest.raises` saw
  none) (`helpers`); 2 on a TypeError
  (`frozen_set_ignores_the_global_attributes_file`,
  `frozen_set_reads_gitattributes_as_git_check_attr_does`) (plan 13.5 names
  every test); among
  those on an assertion of their own, 10 demo-fixture exports share
  one cause, HEAD's "no marker" refusal of the fixture's new attribute line
  (one refused run each, counted from the log's failure sections) before any
  other case is reached; form 2, the file with that attribute line reduced to
  the two lines HEAD's tool does not refuse, 12 failed and 7 passed in
  497.20 s, the passes `fixture_clean_tree_reaches_go_stamp_and_push`,
  `fixture_git_init_identity_hook_and_rerun_refusals`,
  `fixture_no_git_rerun_and_failed_git_step_are_cleared`,
  `fixture_prove_reaches_a_verdict_and_stamps_only_an_exact_passed`,
  `fixture_prove_refuses_before_any_stage`,
  `fixture_refused_anchor_leaves_the_previous_export_in_place`,
  `real_tree_frozen_files_are_byte_identical_and_anchors_matched`, the
  failures 7 on an assertion of their own; 1 on a AttributeError; 1 on a
  refusal HEAD's tool does not raise (`pytest.raises` saw none) (`helpers`); 1
  on a FileNotFoundError
  (`fixture_a_run_that_dies_after_the_clear_keeps_the_push_record`); 2 on a
  TypeError (`frozen_set_ignores_the_global_attributes_file`,
  `frozen_set_reads_gitattributes_as_git_check_attr_does`); of the failures on
  another exception, the
  dying run's FileNotFoundError is the manifest HEAD's tool unlinked (gap 5
  itself) and the gone-repository test's KeyError the `in_progress` field
  HEAD's tool never writes, while the two frozen-set tests' TypeError is the
  landed staticmethod call HEAD's method does not accept and says only that
  HEAD differs, as does a test that stops at its first assertion HEAD's tool
  cannot meet (`helpers`, before its gap 1, 3 and 7 assertions), so three
  direct controls stand beside them: HEAD's deny list leaves the hyphenated
  spelling of its release-wording pattern unmatched and matches the spaced
  one; HEAD's reader differs from `git check-attr` on 55 of the 62
  contents; and the fixture export under HEAD's shimmed tool, on the form-2
  fixture, misses the gap-2 hit (the fixture's sweep file, line 6) and the
  gap-4 hits (README.md line 3, ci.yml line 2) that the export under the
  landed tool, on the landed fixture, reports; the evidence test
  with a staged receipt whose tool digest is the allowlist's committed blob,
  1 failed and 4 passed in 27.67 s on the new "but at" remedy. The export test
  file itself (19 tests) sweeps this entry through its real-tree snapshot,
  so its run on the final bytes follows this text: its result, with the five
  snapshot test files, the staging scan re-run, the full suite and the
  preflight run, is reported in the handoff's memory row. No pinned export
  and no receipt in this lane, by the operator's confirmation of 2026-10-15
  (plan 13.4): the pinned export and its proof move to the final source
  commit.

## 2026-10-14 - Public cut: the gates lane (lane 1 of the decision batch; branch main)

- (this landing's commit; its hash is in the handoff's memory row)
  test(gates): two evidence gates amended under calls PC-4 and PC-5 of the
  2026-10-14 public-cut decision batch (ten operator calls, held in the
  session memory until docs/PUBLIC_CUT_PLAN.md section 13 lands with lane [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  2; the "PC-" prefix keeps them apart from DECISIONS.md's D-n), so that
  lane 2's edits to the export tool and the allowlist can land green and
  the suite passes under current numpy on this box (the public workflow,
  ubuntu-latest with Python 3.12, has not run; the CI rehearsal is call
  PC-8). On the same date, outside any lane: `main` fast-forwarded onto
  `espalier-trial` (c23f214..b924585) and pushed, the working branch
  switched to `main` (call PC-9), and the private, empty
  `specdec-sidechannels` repository created for the rehearsal (call PC-8).
  tests/test_evidence_bytes.py (PC-4, the receipt lock): the 2026-10-13
  form kept the export tool's proof receipts as citers of check 4, so an
  uncommitted edit to tools/export_public_cut.py or [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  docs/public_cut/tone_allowlist.txt went red on that check's HEAD-count [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  (the file's new bytes cited nowhere while HEAD's were cited by the
  receipt) until a receipt citing the new digest landed with the edit
  (plan 12.7). Now the `.json` receipts under docs/public_cut/proofs/ are [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  not citers of check 4 at HEAD or now, and a fifth check binds each
  receipt at the commit it names: a receipt HEAD holds equals HEAD's copy
  once CRLF is folded (never edited); it parses; its 40-hex
  `source_commit` is an ancestor of HEAD; every 64-hex value under a key
  that names a sha256 is the digest, stored or LF-folded, of the file the
  key names at that commit (the tool for `tool_sha256`, the allowlist for
  `allowlist_sha256`); no receipt tracked at HEAD is missing from the tree
  or from disk. A digest that names bytes no commit holds (an uncommitted
  tool's, or the allowlist digest a `--worktree-sources` export takes over
  CRLF worktree bytes on this checkout) is refused with the remedy in its
  message, a string under a sha256 key that is not 64 lowercase hex is
  refused, and a receipt with no digest under such a key binds nothing
  and passes. What the call gave up: a committed edit to the tool or the allowlist no longer needs a
  receipt beside it, so the newest receipt may describe an older tool, and
  nothing makes the next export's receipt follow. Of the two committed
  receipts, the 2026-10-12 one, a `--worktree-sources` export, carries no
  digest and so binds nothing, and the 2026-10-13 one carries two distinct
  digests in three places, both resolving at a0a4d30 as stored (both
  blobs are LF there). Proofs: the file on the tree in its second form,
  the one the second critic read looked at, 20 passed in 37.05 s together
  with tests/test_outcome_head.py (that form's control logs were
  overwritten by the final form's re-run and are not cited); on the final
  form, which differs from the second in its messages, the refusal of a
  malformed digest string, comments and docstrings: the file on the tree
  20 passed in 38.67 s together with tests/test_outcome_head.py; in the
  scratch clone of b924585 with that form copied in from the worktree
  (sha da7e8527d64a of its CRLF worktree bytes here), fifteen runs over
  thirteen states: the clean clone 5 passed; a line
  appended to the tool, uncommitted, 5 passed under the new test and
  1 failed, 3 passed under HEAD's test on its HEAD-count assertion
  (tools/export_public_cut.py cited 2 at HEAD, 0 now); a comment appended [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  to the allowlist likewise 5 passed and 1 failed, 3 passed (the allowlist
  cited 1 at HEAD, 0 now); the HEAD receipt with a tampered digest, with a
  commit of forty zeros, and with its verdict rewritten, each 1 failed,
  4 passed on the never-edited clause; the receipt removed with `git rm`
  1 failed, 4 passed on the gone clause, and deleted on disk alone
  4 failed, 1 passed (the gone clause, and the three scans of checks 2 to
  4 erroring on the missing tracked file as they always did); a staged new
  receipt naming a dangling commit (`commit-tree`, no ref, `merge-base
  --is-ancestor` exit 1) 1 failed, 4 passed on the ancestor clause; a
  staged new receipt with a 64-hex string planted in a stage tail
  5 passed; one carrying the empty blob's digest as `tool_sha256`, and
  one carrying an unknown `allowlist_sha256`, each 1 failed, 4 passed
  with the new-receipt remedy; a staged `README.md` under proofs/
  5 passed; every exit as expected and none unexpected. A further set,
  same form and clone, four runs: the clean clone 5 passed, a staged new
  receipt with 64 uppercase F as `tool_sha256` and one with a prefixed
  digest each 1 failed, 4 passed on the new message, one with a null
  5 passed; every exit as expected and none unexpected.
  tests/test_outcome_head.py (PC-5, the numpy route): the stage-C freeze
  recompute and the tampered-summary refusal of
  test_stage_c_freeze_end_to_end run in a fresh interpreter (`_run_freeze`,
  `sys.executable -c` with tools/ on its path) instead of inside the
  pytest process, the contract the tool's own CLI has (main() runs
  --stage-c-freeze as its own process); the refusal asserts a non-zero
  exit and "BINDING GATE REFUSED" on stderr. No change to
  tools/train_outcome_head.py (the gate stays bit-exact) and no numpy
  pin. Proof: the file on the box, 15 passed in 24.57 s in its first form
  and within the 20-passed runs of the later forms (the docstring alone
  changed between them). Validation in scratch (plan 12.7's open route,
  decided as PC-5): two fresh clones of this tree at b924585, each with
  tests/test_evidence_bytes.py in its first form copied in, each with a fresh
  venv of Python 3.11.9 installed as `[dev,analysis]` with numpy pinned
  2.4.6 on the pip line (scipy 1.17.1, scikit-learn 1.9.1, pytest 9.1.1;
  torch not importable), the receipt's pytest command, the two
  concurrently on this box, on Windows: clone V, with the worktree
  tests/test_outcome_head.py in its first form, 667 passed, 34 skipped in
  14,601.71 s, exit 0; clone D, with HEAD's in-process form of that file
  instrumented by a scratch probe (numpy runtime and error state,
  threadpools, the alignment of every array the freeze reads through
  NpzFile.__getitem__, the refusal caught, the same probe in a fresh
  interpreter on the same files), 2 failed, 665 passed, 34 skipped in
  14,594.49 s, exit 1: the instrumented test on the refusal it was built
  to catch (recomputed delta_noise 0.0074441302104752485 against the
  committed 0.007444130210472721) and the export test's real-tree scan on
  the probe's scratch path inside the instrumented file, the path gate
  doing its job on a file that never enters the tree. The mechanism,
  measured: the probe read numpy's OpenBLAS at 24 threads inside the
  pytest process (766 modules loaded, scipy among them, with scipy's own
  OpenBLAS at 2) and at 2 threads in the fresh interpreter (256 modules);
  tools/run_noise_floor.py, a frozen instrument, sets OMP_NUM_THREADS,
  OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 2 at import when they are
  unset (`os.environ.setdefault`), and four module-level imports pull it
  in at collection (tests/test_noise_floor.py,
  tests/test_noise_floor_landing.py, and tools/run_seed_replay.py through
  tests/test_seed_replay.py and tests/test_seed_replay_landing.py), after
  numpy's BLAS loaded at the box's logical-processor count (numpy's
  OpenBLAS, loaded with no variable set, read 24 and kept it after the
  variables were set later in the same process), so a later child that
  inherits the environment runs 2 (the one
  measured did); the stage-I tool on the same synthetic root under the V
  venv gives 0.007444130210472721 at OPENBLAS_NUM_THREADS=2 and
  0.0074441302104752485 at 24, the refusal's two values,
  2.527492104498208e-15 apart (numpy 2.4.6 bundles OpenBLAS 0.3.31.188.0),
  while the box's numpy 2.3.5 (OpenBLAS 0.3.30) gives 0.007444130210476211
  at both. So the old test compared a 2-thread subprocess against a
  24-thread in-process recompute; the new test's two children share one
  environment. The record: a dated update under the 2026-10-13 EVID-1
  entry and a new thread-count entry in docs/SHARP_EDGES.md (three other
  in-process recompute families passed under 2.4.6 in the failure-mode
  reviewer's scratch runs, one at 1 thread and one at 4, whose logs record
  counts (41 and 26 passed), not the test sets or command lines, so the
  pairing rests on that reviewer's report; the prefetch landing family in
  one run under 2.3.5; the four entry points; a Practice paragraph naming
  threadpool_info(), the numpy wheel and the thread caps); a dated note in
  docs/REPRODUCE.md section 4 (the
  byte-identical-rerun sentence holds under one wheel and one thread
  count; results/real/oq15_stage1.json, its meta and
  oq15_head_weights.meta.json record neither); a seventh note in
  docs/TASK_RECIPES.md's landing recipe; a dated note in plan 12.7
  pointing at both calls. Reviews: a critic round in diff mode and a
  failure-mode round on the first form, whose findings (the ancestor
  check, receipt immutability, keyed and path-bound digests, the
  new-receipt remedy, `.json`-only receipts, the on-disk deletion case,
  the blob-digest cache, the HEAD-count explanation, clone D's setup, the
  Stage-I label, the generalised sentences, the dropped-guarantee
  sentence, the entry points (three found by that round, a fourth by
  the re-read), the Practice primitive, the three
  dated notes, the PC- names) landed as one batch that the control sets
  and the proofs above cover; declined in this lane: a hint in the
  gate tool's refusal message (PC-5 said no tool change; a lane-2
  candidate) and an unmeasured conftest hook; then a critic re-read of
  that second form, whose blockers were sentences of this entry and the
  record (the entry-point count, the form of the evidence test the clones
  carried, the worktree-sources sentence) and whose advisories landed with
  them (a malformed digest string refused, a remedy in every message, scope words
  on the recompute sites and the CPU kernel, the summary label, the
  allowlist line-ending observation in plan 12.7), as a third form; then
  a third read, whose blockers were form labels on runs the second form
  had made, a full run claimed on a form none had run on, and an erratum
  written without evidence of the earlier state, landed with the control
  sets and the full suite re-run on the final test files; then a fourth
  read, whose blockers were a count of states, this sentence's omission
  of that second blocker, and "core count" for a logical-processor count,
  landed as documentation (the one copy of "core count" in a test
  docstring, tests/test_outcome_head.py, is left for lane 2 so the suite
  run below keeps its shas); then re-reads until the round that cleared
  the commit, named in the handoff's memory row. Full suite on this box,
  numpy 2.3.5, on the final code bytes (the test files at shas
  da7e8527d64a and 9aaed50391e2 of their worktree bytes here, CRLF and LF
  respectively, unchanged since; the blobs this commit stores are LF, ce28b51ef2af
  and 9aaed50391e2, and a checkout on this box writes both CRLF), before
  this entry's proof sentences were filled in: 721 passed, 5 skipped in
  3,909.32 s, exit 0 (the control sets overlapped its first minutes; most
  of the gap to an earlier full run on this box on pre-final test bytes,
  721 passed, 5 skipped in 1,800.15 s, is unexplained); after it,
  documentation only; the files
  that snapshot the worktree or read the documents, re-run on the filled-in
  documents, 83 passed, 1 skipped in 451.38 s, exit 0, and re-run again
  after this form's edits, reported in the handoff's memory row.

## 2026-10-14 - Public cut: the front-doors lane (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  docs(public-cut): the two front doors of the public cut and the glossary
  entries they link, with the export test's licence oracle fixed. README.md
  gains a front door above its unchanged status page (+85 lines, a pure
  insertion): the question, the negative answer at the registered reader's
  pinned L1 and L2 cells (L3 open at both sources), a three-row scorecard
  whose labels link to docs/GLOSSARY.md, the two
  NON-CRITERION side results, how to check a number without a GPU, how to
  read the record and what a clone cannot reproduce; the 2026-09-05 opening
  moves verbatim under "The question in full" and everything from "Status
  at a glance" on is byte-identical, every dated note included.
  docs/public_cut/ROOT_README.md (the public root README; +133 -50): a [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  plain abstract on top, the export-provenance paragraph moved verbatim
  below the three parts, a kill-criteria paragraph (K-1 did not fire; K-2
  FIRED at the registered reader's pinned L1 and L2 cells of both sources,
  each with the +0.005 materiality scope and L2 read under the rider
  amendment, L3 open; K-3 FIRED at Attempt #1; K-7 did not fire as
  written; K-4 to K-6 UNTESTED), sideband's
  "Reusable on its own" list, glossary links on the labels (six in a
  sentence after the three-layers paragraph, the rest where they appear);
  three pieces of its committed text rewritten: the folder-table sideband
  row now scopes conversion and reconstruction to S1, the side-results
  paragraph is re-wrapped with two label parentheticals inserted
  (ADDRESS-BEYOND-TOKEN; R2-FALLBACK-SURVIVES / H-ABSORBS), and its two
  sentences that read "absorbs" as a mechanism are reworded to the
  label-not-mechanism form the R2 registration pins; its draft-provenance
  comment, stripped at export, is extended and its date clause made plural.
  docs/GLOSSARY.md (+44 -3): fifteen headed entries for the record's
  conclusion labels (ABSORBED, ADDRESS-BEYOND-TOKEN, BAR-RESOLVED@210 /
  RULE-LEAKS@30, EQUAL-DIMS-ONLY, FLOOR-MATERIAL, H-ABSORBS, K-2-ISOLATED,
  LEAD-TIME-ABSORBED, NOT-SHOWN, PREFETCH-HEADROOM, R2-FALLBACK-SURVIVES,
  SPLIT, SURVIVES-STRONGER, TWIN-ROBUST, and RULE-LEAKS@30 as a
  cross-reference), each stating its registered rule, every number copied
  from FINDINGS.md, docs/WHY_THIS_DIES.md or the registration in
  docs/BLUEPRINT.md, a ten-line dated note in the header listing them,
  and dated clauses on the K-2 row, the Finding (F-N) entry (29,
  F-0..F-28) and the Mega-group lens entry through F-28.
  tests/test_export_public_cut.py: the real-tree oracle on the Llama 3.2 [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  licence copy compares the snapshot commit's blob instead of the worktree
  copy, which is CRLF in a fresh autocrlf clone while the blob is LF (the
  file read 1 failed, 13 passed in such a clone before the fix; 14 passed on
  the box and 14 passed in a fresh clone after it). Proofs: the real-tree
  export tests over each README draft (3 passed, twice), then the whole
  export test file over each fix batch, 14 passed in each of seven logged
  runs (three batches on the box and in a fresh clone with the four files
  copied in, the fourth in a clone), and the fourth batch's file again
  inside the full suite, the landing-text number
  tracer at zero unknown numbers on every file, no tone-sweep hit and no
  allowlist edit (the 12.7 receipt lock untouched); four critic rounds in
  diff mode with every quoted number recomputed (NO-GO at 8, 2 and 2
  blockers, then GO with 0 numeric discrepancies and three wording
  advisories, all taken; the blockers were an all-space K-2 sentence, the
  label word "absorbs" written as a mechanism in the draft and in two
  committed sentences of the root README, a date range, label rules
  misstated or missing in the glossary, a twin reading generalised beyond
  the harvest that licensed it, proxy margins quoted without their harvest
  and cell, S1 results reading as answers about the pure address stream,
  and label coverage claims and label counts that disagreed between
  files),
  then diff-mode re-reads of the advisory edits and of the two records,
  NO-GO at 5, 4, 1 and 1 blockers, every one a sentence (nine of this
  entry, two of the plan note), until the round that cleared the commit,
  named in the handoff's memory row by its number and blocker count; the
  full suite on the tree with the four
  files as they stood after the advisory edits: 720 passed, 5 skipped in
  4,335.76 s, exit 0 (after it, documentation only: one word inserted in
  the root README's abstract, this entry and the plan note; the files that
  snapshot the worktree or read the documents were re-run on the final
  bytes, the result in the handoff's memory row). Plan 12.7 gains a dated
  note (withheld with the plan)
  recording the numpy separation it named: the staging export's full suite
  in two fresh clones and venvs, 1 failed, 651 passed, 34 skipped (exit 1,
  the binding gate's SystemExit) under numpy 2.4.6 and 652 passed, 34
  skipped (exit 0) under numpy 2.3.5, same scipy, same command.

## 2026-10-13 - Public cut: the pinned export and its proof, commit B (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  docs(public-cut): the export of the public cut pinned to a0a4d30, 2
  commits after commit A (3e7b744; `git diff --name-only` between them lists
  ESPALIER_MEMORY.md, docs/SHARP_EDGES.md only, so the tool, its test and
  the authored sources are commit A's), written into the staging folder
  without worktree sources as a fresh history of 1 commit: 805 files,
  273,619,564 bytes, 795 of 810 tracked paths exported, 124 lines marked,
  verdict NO-GO with 28 blockers (2 layout, 21 pending, 3 allowlist flags, 2
  record flags; the allowlist-stale, sources and tool blockers of the
  worktree export are gone, 32 to 28); `scan` exit 2 with no gate stamp; the
  fresh-clone proof in 1,854 s: 1 failed, 651 passed, 34 skipped in 1,790.17
  s with the analysis extra installed (the binding-gate refusal of the last
  proof recurred on bit-identical values; the test passed alone and with its
  file in the proof venv and alone on this box), the stages after pytest did
  not run (lint, smoke, worked-example, evidence-bytes), result FAILED, exit
  2, no proof stamp was written; the receipt under docs/public_cut/proofs/; [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  plan section 12.7, withheld with the plan, generated by a session script
  from the sources 12.7 names, with the literals it carries named in it.
  tests/test_evidence_bytes.py: check 4 gains a dated exemption for a file
  cited only by the export tool's proof receipts by the sha256 of its
  LF-folded bytes (the receipt's digests of the tool and the allowlist, both
  withheld; a literal `-text` line naming one is refused at export, a `*`
  glob line breaks the real-tree frozen-set oracle, and a `?` glob passes
  both only by hiding the name from the mention guard, so the lane amended
  the test instead), held to that fold against the index blob, the
  HEAD-count check applying while an edit is uncommitted; the full suite
  before the amendment read 1 failed, 719 passed, 5 skipped with that one
  failure, the edited file's tests 4 passed in 27.83 s after it, the files
  that snapshot the worktree or read the changed documents 80 passed, 1
  skipped after the amendment and before round eight's rewording, and the
  full suite again on the tree after the amendment and that rewording: 720
  passed, 5 skipped in 3,760.32 s, exit 0; an eighth tool gap (dropping
  withheld paths' attribute lines at export) and a ninth (the frozen set
  reads only `-text` lines and only `*` globs, so `?` and `[]` globs,
  `binary` lines and basename patterns escape it) are recorded in 12.7.
  Eleven critic rounds preceded this text: four on the first text (NO-GO at
  6, 6 and 2 blockers, then GO), two diff-mode re-reads of its advisories
  (GO, GO), and, after the red full run and the test amendment, five on the
  amended text (NO-GO at 3, 3, 1 and 1 blockers, then GO); counts from the
  critic reports; the round that cleared the commit is named in the
  handoff's memory row.

## 2026-10-13 - Public cut: the export tool, commit A (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  feat(public-cut): tools/export_public_cut.py, the export tool of plan [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  section 6 as 10.7, 11 and 12 amended it: the layout written from a pinned
  commit through one `git cat-file --batch` (raw blobs, byte-identical in
  the export repository, autocrlf off, `add -A -f`), the withhold list
  applied whole and by unique anchor with `[withheld: ...]` markers, the
  mention rule with names derived from the withhold list and the mention
  marker its only exemption, the placeholder fills and an export note on
  every sentence found describing the private install contract (7),
  the generated WITHHELD.md files and
  docs/COMMIT_LOG.md with a deny list, the scan (secret shapes, home-directory
  paths, withheld and private names, withheld digests to the 12-hex prefix,
  the 10.9 sweep against a reviewed allowlist with operator flags, the
  `[pending:` class, the tool pinned to the commit, the deny list over the
  record file the sweep excludes with reasoned keeps published in
  WITHHELD.md and stale spec entries flagged), the manifest with a sha256
  per file and the clear-before-write refusals (a hand edit, a foreign file,
  a remote or a push record, a commit or ref beyond the export, a repository
  that is gone), the pinned identity, the pre-push seat-belt
  with a gate stamp from `scan`, a proof stamp from `prove` and a push
  record beside and inside the repository, the SHIP
  verdict separate from the write (exit 2 for a verdict, 3 for a refusal),
  and `prove` (fresh clone, venv with the analysis extra, suite, lint, smoke,
  the README worked example, the amber blob-id check, a qualified receipt);
  tests/test_export_public_cut.py (a fixture [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  repository with one file per case, a clean fixture that reaches GO and a
  stamped push, and real-tree tests on a worktree snapshot); sources under
  docs/public_cut/ (LICENSE, NOTICE, CITATION.cff, ci.yml, tone_allowlist.txt [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  with 45 reviewed line entries and 1 word entry, the two Llama licence texts);
  docs/DECODE_CONTRACTS.md's dated note of plan 10.4 in conditional form
  (every id and count re-derived from the sibling checkouts);
  docs/THIRD_PARTY.md's dated note on the two probe-weight files; a sentence
  of docs/public_cut/ROOT_README.md and pyproject.toml's comment on the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  analysis extra; plan section 12 (12.1 to 12.6 and 12.8; 12.7 awaits commit
  B); several worktree-sources staging exports of sideband, the last 805
  files, 273,588,148 bytes, verdict NO-GO with the expected 32 blockers, and
  a fresh-clone proof of one of them (5525c83, not the first made), FAILED at 7 failed, 645 passed,
  34 skipped in the subfolder clone without torch (4 scipy-dependent
  tests, 2 subfolder path checks, 1 binding-gate refusal by 2.5e-15 on
  the point and 4.6e-15 and 9.6e-15 on the interval bounds, in the full
  run only; receipt under docs/public_cut/proofs/), with the test-only fixes for the first two [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  classes (tests/test_balanced_groups.py skips without scipy unless
  SIDEBAND_REQUIRE_ANALYSIS is set; tests/test_evidence_bytes.py prefixes
  top-level git paths from a subfolder). Found on the way: the exported
  `.gitignore` hid one tracked harness file under case-insensitive matching
  (the force-add and a tracked-count check are the fix); the tool's own
  anchors quote the withheld passages, so the tool and its test are withheld
  from the export; an earlier pending rule's backtick exemption hid the
  backticked instances (7 of the 21 pending lines at the last
  staging export). Nine critic rounds before this text (NO-GO at 9, 5, 7, 6,
  2, 4, 2, 2 and 2 blockers, counts carried from the lane's notes as the plan's
  status paragraph says; every blocker a sentence or a one-condition fix, each round's
  fixed before the next; the code-reviewer and failure-mode-reviewer agents
  ran alongside each round), and the round that cleared the commit is named
  in the handoff's memory row.

## 2026-10-12 - Public cut: the root README draft, in tree (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  docs(public-cut): docs/public_cut/ROOT_README.md, the source of the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  public repository's root README (plan 10.6), 327 lines drafted
  from the record as read that day: the question and the answer in the
  record's words per layer and source, open and unrun cells named; the
  three folders and what each found, nulls and errata included; how the
  work was run, with the exceptions the record names; what is reusable;
  the one-second check from docs/RELEASE_NOTES.md section 7; the two
  re-run modes; what is not in the repository; licence and citation. The
  amber and lockstep sections are pre-survey skeletons under a
  `[pending:` marker (5 occurrences of the marker form in the
  draft, one in the provenance comment the export strips).
  docs/PUBLIC_CUT_PLAN.md section 11, the second 2026-10-12 amendment: [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
  MIT for the whole release (the operator's call), the README source in
  tree and withheld, `[pending:` as a placeholder class, the staging
  folder renamed to specdec-sidechannels, the README's worked example and
  the amber blob-id check added to the fresh-clone proof, oracles.
  Sections 1 to 10 unchanged. No code, evidence, registration block or
  finding changed; no GPU.
- Provenance check of the draft (scratch script, definition in plan 11.6):
  91 distinct numeric literals found verbatim in the twelve
  named sources; the 10.9 hype sweep printed 0 lines; every cited path
  present; a negative control caught one of two changed numbers (the
  other exists in FINDINGS.md on its own account), so the script is the
  first pass and the critic's read is the gate.
- Critic diff pass over both files (sideband-critic, diff mode; no payload
  recomputed): round one NO-GO (10 blockers: an all-space "closed negative
  at every registered test" the record refuses; the conversion and
  reconstruction rows untagged by source where only S1 ran; F-27's
  seed-noise fraction read as the rule leak; F-26's closing rungs left out;
  amber's E3 and E4 omitted; lockstep's order stability overstated and
  lockstep.rac called amber's production coder; registration and critic
  claims stated for all three records; the harness's and the critic's
  coverage overstated; "nothing rewritten for publication"; 14 advisories),
  round two NO-GO (2 blockers, both in sentences written to fix round one:
  the F-26 rungs read as "closed" where the record's labels are SURVIVES
  at this encoding and R2-FALLBACK-SURVIVES / H-ABSORBS with the forward's
  stored final-norm state as what absorbs the margin, and "every one a
  near-tie" repeating a sentence the record had corrected; 13 advisories),
  round three GO (9 advisories, one a landing condition: this section in
  the same commit), round four GO (2 advisories: a hash example in plan
  11.7 mislabelled as lockstep's own, corrected before the commit; the
  same landing condition). Every blocker after round one was a sentence
  written to fix the previous round.

## 2026-10-12 - Critic notes landed; the public cut re-scoped to the trio (branch espalier-trial)

- (this landing's first commit; its hash is in the handoff's memory row)
  docs(record): the dated notes the 2026-10-11 critic rounds left standing.
  README.md: the existence row's "about +0.003" gains the four F-24 Mt
  values and F-24's "+0.003 or less", a three-place rounding; its F-16/F-18
  sentence gains the findings' dated moot notes, quoted; the 2026-10-11
  sub-line says what "that family" is (the three F-28 readers; the
  registered reader ran in F-24, F-25 and F-28's STAGE LENS); the
  "27 entries" line gains the lint's 29, F-0..F-28; the "Close on F-23"
  bullet gains a note that it predates F-24 and points at the one-line
  reading's dated note, rider-amendment pointer included; the 2026-10-11
  check note records that the existence row gained two dated clauses.
  OPEN_QUESTIONS.md: the OQ-19 header gains "SKIPPED (operator,
  2026-10-11; dated note at the end of the entry)". docs/THIRD_PARTY.md: a
  dated disclosure that no harvest meta records a checkpoint revision (24
  metas: model, git_commit, npz_sha256), where the record pins snapshots
  instead (the four prefetch metas' replay_source b89a7c4;
  oq16_ha_identity's Llama 0e9e39f2), and that the harvested revisions are
  inferred from the one-snapshot caches, with the cache and git-entry
  dates. No code, evidence, registration block or finding changed; no GPU.
- (this landing's second commit)
  docs(plan): section 10 of the public-cut plan, the 2026-10-12 amendment:
  the trio goes public under the hype-strip condition; the project is one
  repository, specdec-sidechannels, with a root README and three folders;
  no PyPI; the raw harvests go to a Zenodo deposit; the hype sweep becomes
  an export gate with its command pinned (46 / 12 / 49 lines on the three
  trees); lockstep's first-cut withhold list; item 5 dissolves into a dated
  DECODE_CONTRACTS line with the lockstep blobs spelled out (197 amber rows
  resolve by blob id; 16 lockstep rows handled file by file); the order of
  work amended. Sections 1 to 9 unchanged.
- Critic diff pass over both: round one NO-GO (2 blockers, both in the
  amendment: "every Sources row resolves" ignored lockstep's moved blob and
  "150 citations" was an undercount of 213; 10 advisories; 48 items),
  round two NO-GO (1 blocker, the "[imagined]" count's split; 4 advisories;
  44 items), round three GO (1 advisory; 20 items), round four NO-GO (1
  blocker, a date generalised from one file; 1 advisory; 10 items), round
  five GO (7 items). Every blocker after round one was a sentence written
  to fix the previous round.

## 2026-10-12 - Public cut, section 5: the record lines owed before the export (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  docs(record): the dated lines that the public-cut plan's section 5
  owes the private record before the export, items 1 to 4.
  docs/ECOSYSTEM.md's amber and lockstep entries each name the two as the
  commercial branches of this research, both private (amber's record last
  moved at 69b437c, lockstep parked at cdfe0b3; both HEADs read from the
  checkouts that day). OQ-19 is SKIPPED by the operator's decision: dated
  notes in OPEN_QUESTIONS.md, in docs/OQ19_ORACLE_CEILING_DRAFT.md, in the
  DRAFT banner of tools/run_fullfree_oracle.py, on docs/GLOSSARY.md's
  OQ-19 row and after docs/BLUEPRINT.md's "OQ-19 decided after";
  DRAFT_UNFROZEN stays True and tests/test_fullfree_oracle.py is
  unchanged (13 passed, 2 skipped). docs/THIRD_PARTY.md's OLMoE row names
  Apache 2.0 from the model card at snapshot b89a7c4 (the local Hub
  cache's revision, the one the Hub API returned the same day; the harvest
  metas record no revision), and its stale ECOSYSTEM line-range pointer
  to the Llama gate note gains a dated correction. README.md's "Status at
  a glance" was checked against FINDINGS.md through F-28: every number
  present (by script over the whole section; the critic's read of the
  section's 24 point-plus-CI groups agreeing), no row changed, and two
  paragraphs below the table written on 2026-09-05 gained dated notes
  because F-24 overturned them (the one-line reading's "established at
  probe level"; the "two stronger free baselines ... both untested"
  bullet). Item 5 (docs/DECODE_CONTRACTS.md's private sources) waits on
  the operator's call. No code behaviour, evidence, registration block or
  finding changed; no GPU. Critic diff pass: round one NO-GO (1 blocker,
  the two README paragraphs, and 9 advisories; every point-plus-CI group
  matched its source), the blocker and three advisories applied as one
  batch; round two NO-GO (3 blockers: two scope errors in the new README
  notes and this entry naming the withheld plan file; 6 advisories);
  round three NO-GO (1 blocker, the README note's L2 gap; 3 advisories);
  round four NO-GO (1 blocker, the same note's offsets; 1 advisory);
  round five GO with one advisory left standing. Every blocker after
  round one was a sentence written to fix the previous round.

## 2026-10-11 - Lockstep harvested: the decode-contracts note and dated notes (branch espalier-trial)

- (this landing's commit; its hash is in the handoff's memory row)
  docs(record): sideband's own dated lines on the amber/lockstep harvest
  claims - docs/PRIOR_ART.md's OQ-7 cell gains a dated note with four
  corrections (US 12,547,833's granted independent claims require a
  last-token replacement, which claim 1 recites as lossy, and no claim names
  the decoder's LLM; PMATIC is arXiv 2601.10678 and 2601.17684 is Hu and
  Tang; the asymmetric bundle is partly published and the built archive is
  draft-coded on both sides; the rank cell has been occupied since LLMZip
  v1), with a pointer under the LLMZip / ts_zip entry; dated qualifiers on
  docs/REPORT.md's F-9 row and docs/GLOSSARY.md's break-even entry
  (synthetic only; F-12's real-model free baseline gives the free-steering
  saving no support as built; amber's archive has no verifier-side
  steering), on the GLOSSARY verified-archives entry (rejection-rate
  attestation never built; amber's L1 target recompute is synthetic only)
  and on its OQ-7 row (the prior-art pass pointer); a dated correction to
  docs/ECOSYSTEM.md's amber entry (imports sideband.synthetic only; key
  files; P7 withdrawn; parked since v0.4.0 on 2026-08-30, record last moved
  at 69b437c). Every arXiv id fetched live on 2026-10-11, two abstract pages
  saved beside the review's texts; the patent claims read from two
  renderings. No code, evidence, registration block or finding changed; no
  GPU. Critic claims pass: round one NO-GO (3 blockers, 10 advisories over
  about 80 checks; the numbers and ids matched their sources, the objections
  were to quotes, citations, scope and one restatement amber's errata had
  corrected), all thirteen applied by regenerating the files; round two
  NO-GO (2 new blockers from the regeneration, a transitive import and this
  bullet's own summary of round one, plus 4 advisories over 51 checks), all
  six applied the same way; round three NO-GO (1 new blocker, a one-word
  scope, plus 2 advisories over 37 checks), all three applied the same way;
  the fourth round is recorded in the handoff's memory row.

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) docs(harvest): harvest the parked
  sibling lockstep - docs/DECODE_CONTRACTS.md, a HARVESTED NOTE and
  NON-CRITERION (grid crossings under a value contract beside amber's
  rank-order mismatches under an order contract, every number generated by
  key from amber 69b437c and lockstep 54d83f4, with a Sources table); dated
  notes in OPEN_QUESTIONS.md OQ-7, docs/BLUEPRINT.md T-A, docs/GLOSSARY.md
  (the OQ-7 row and the verified-archives entry) and docs/ECOSYSTEM.md (the
  lockstep entry) saying that lockstep's runtime was never built and its
  byproduct economics never measured; a dated addition to docs/METHOD.md
  section 6 (lockstep F-14's 114.5x pack-rate error). No code, evidence,
  registration block or finding changed; no GPU.

- (the follow-up commit, run from the lockstep session; its hash is in the
  handoff's memory row) docs(harvest): lockstep's standalone-merit verdict
  and its three parked blueprints - a second dated note in docs/ECOSYSTEM.md
  (the lockstep entry: problem right, prescription wrong, economics moot;
  what stands; what was never tested) and a new section in
  docs/FUTURE_IDEAS.md carrying lockstep Blueprints E (decode receipt), D [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
  (recipe-pinned derived data) and the unbuilt citation-regime half of F,
  each with its promotion path. No code, evidence, registration block or
  finding changed; no GPU; no critic round (idea-tier text only; every
  number from lockstep findings read in the session).

## 2026-10-10 - OQ-20 seed replay landed: the two conversion verdicts' legs at a new seed (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(evidence): land the OQ-20 seed
  replay - both CPU readouts from the clean tree at c62f03d,
  results/real/seed_replay_k3.json and seed_replay_oq15.json with their
  state files; stage words SPREAD-COVERED and FREE-SPREAD-COVERED (R2 and R6
  MUTUAL-COVERAGE / REPRODUCES on both populations; every guard held, no bar
  cleared, R4 R-CONSISTENT on both, R8 NEAR-IDENTICAL-ARMS on K3 and
  DELTA-MOVES on OQ15); F-27's STAGE REPLAY line; dated notes in
  docs/NOISE_FLOOR.md, README, docs/REPORT.md and docs/FINDINGS_INDEX.md;
  NON-CRITERION notes in F-19's and F-21's status cells; the OUTCOME under
  OQ-20 and the block's OUTCOME with both predictions scored;
  tests/test_seed_replay_landing.py; the tool joins the frozen closure (ruff
  exclude, CLAUDE.md thirteen attested of sixteen, the CONVENTIONS,
  SHARP_EDGES and TASK_RECIPES entries); the block's DATED AMENDMENT AND
  ERRATA (tests/test_seed_replay.py's three pre-run assertions amended to
  branch on the evidence, the FREEZE line's short-sha gate command, the two
  environment captures, the launch driver's log and the gate's stdout
  committed as evidence under results/real/oq20_*).
- c62f03d feat(evidence): the six OQ-20 seed-6 runs - the thirty sidecars of
  K-3 arms 1, 4 and 3 and OQ-15 arms 1, 7 and 6 at seed 6 from the clean
  clone of b6d3701. Committed without running the suite: the frozen
  tests/test_seed_replay.py was red at this commit (1 failed of 18, a
  pre-run assertion), disclosed in the block's DATED AMENDMENT.
- a960709 docs(memory): log the OQ-20 freeze and launch - the handoff row
  written with the runs in flight.
- 9163706 docs(registration): OQ-20 FREEZE line and the replay-check
  sidecars - the pinned token-exact replay of the first prompts at the old
  seeds from the clean clone, PASS on all six arms; the environment-capture
  deviation disclosed.
- b6d3701 feat(registration): freeze OQ-20, the seed replay of the verdict
  legs - the OQ-20 entry, the registration block (readouts R1-R8, the labels
  and readings, the stage words, both predictions, void semantics, the
  critic's five rounds and a code review), tools/run_seed_replay.py,
  tests/test_seed_replay.py, the one new estimator
  sideband.stats.paired_ratio_delta_of_deltas_ci.

## 2026-10-09 - Reader-and-lens re-test at S3: stage READERS-LONG landed, the K-2 word final (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row,
since a commit cannot cite itself) feat(evidence): land the reader-and-lens
stage READERS-LONG - both registered runs from the clean tree at f050574,
results/real/readers_long_s3.json and readers_long_s3_r.json with their
state files; R-L (longer budget) at L1 ABSORBED; R-L (longer budget) at the
lopsided L3 SURVIVES-STRONGER (EQUAL-DIMS-ONLY, inflated by the twin's own
cost); R-L (longer budget) at the balanced L3 ABSORBED; the ONE K-2 sentence
over both reader stages K-2-ISOLATED; F-28's STAGE READERS-LONG line with
dated notes on F-24 and F-25; the final K-2 STATUS line in
docs/WHY_THIS_DIES.md; OUTCOME notes under OQ-17 and OQ-18; pointers in
README, docs/REPORT.md, docs/FINDINGS_INDEX.md;
tests/test_reader_lens_readers_long_landing.py; the block's OUTCOME.
- 1fafdfe docs(memory): log the mid-landing handoff of stage READERS-LONG -
the handoff row written between the read of the runs and this landing.
- f050574 (2026-10-05) docs(memory): log the reader-and-lens stage READERS
landing - the handoff row; the stage launched from this commit.

## 2026-10-05 - Reader-and-lens re-test at S3: stage READERS landed (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row,
since a commit cannot cite itself) feat(evidence): land the reader-and-lens
stage READERS - both registered runs from the clean tree at 790b2fc,
results/real/readers_s3.json and readers_s3_r.json with their state files;
the K-2 word K-2-ISOLATED; per cell R-N (hz-rescaled) at L1 ABSORBED; R-N
(hz-rescaled) at the lopsided L3 SURVIVES-STRONGER (EQUAL-DIMS-ONLY, the
twin's larger cost); R-N (hz-rescaled) at the balanced L3 NOT-SHOWN; R-T
(two-tower) at L1 ABSORBED; R-T (two-tower) at the lopsided L3 ABSORBED; R-T
(two-tower) at the balanced L3 ABSORBED; F-28's STAGE READERS line with
dated notes on F-24 and F-25; the K-2 STATUS line in docs/WHY_THIS_DIES.md;
OUTCOME notes under OQ-17 and OQ-18; pointers in README, docs/REPORT.md,
docs/FINDINGS_INDEX.md; tests/test_reader_lens_readers_landing.py; the
block's OUTCOME with both predictions scored. - 790b2fc docs(memory): log
the reader-and-lens stage LENS landing - the handoff row; the stage launched
from this commit.

## 2026-10-05 - Reader-and-lens re-test at S3: stage LENS landed (branch
espalier-trial)  - (the landing commit; its hash is recorded in the
handoff's memory row, since a commit cannot cite itself) feat(evidence):
land the reader-and-lens stage LENS - both registered runs from the clean
tree at d3504b2, results/real/lens_s3.json and lens_s3_r.json with their
state files; full-free ABSORBED at the balanced lens (OFF3-ABSORBED,
OFF4-ABSORBED), proxy LENS-SURVIVES with the combined growth word
L3-GROWTH-NOT-SETTLED; F-28 in FINDINGS.md with dated notes on F-17 and
F-25; the block's OUTCOME with both predictions scored; dated OUTCOME notes
under OQ-13 (ii) and OQ-18; pointers in README, docs/REPORT.md,
docs/FINDINGS_INDEX.md; tests/test_reader_lens_landing.py; the tool joins
the frozen closure (ruff exclude, CLAUDE.md twelve attested of fifteen, the
CONVENTIONS and SHARP_EDGES entries). - d3504b2 docs(memory): log the
reader-and-lens freeze lane - the handoff row; the stage launched from this
commit. - b128fda feat(instrument): register the reader-and-lens re-test at
S3 - the registration block (the balanced lens pinned before it was built;
readers R-0 / R-N hz-only rescale / R-T two-tower / R-L; stages LENS /
READERS / READERS-LONG / S1; labels, licences, the K-2 word; both
predictions), tools/run_reader_lens.py, tools/build_balanced_groups.py and
the artifact, tests (26 + 7), the pins; four critic rounds and the code
review recorded in the block.

## 2026-10-04 - Seed-noise floor readouts: a methods datum on the committed vanilla runs (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row,
  since a commit cannot cite itself) feat(evidence): land the seed-noise
  floor readouts - both registered runs from the clean tree at 906edfd,
  results/real/noise_floor_k3.json and noise_floor_oq15.json with their
  state files; label FLOOR-MATERIAL on both populations, stage NOTE-STANDS,
  readings BAR-RESOLVED@210 and RULE-LEAKS@30; F-27 in FINDINGS.md; the
  block's OUTCOME with both predictions scored and the pinned prior-art
  search recorded; docs/NOISE_FLOOR.md (the methods note); dated notes under
  IDEAS rank 1, on README's cross-seed bullet, on docs/REPORT.md's [withheld: IDEAS not in this repository; see WITHHELD.md]
  single-seed line and in F-19's status cell;
  tests/test_noise_floor_landing.py; the tool joins the frozen closure (ruff
  exclude, CLAUDE.md eleven attested of fourteen, the CONVENTIONS and
  SHARP_EDGES entries).
- 906edfd feat(instrument): register the seed-noise floor readouts - the
  registration block (reliability, nested sums of squares as SS shares and
  method-of-moments components, paired-ratio half-width vs n, the
  symmetrised one-sided null exceedance of the +0.062 bar, single-comparator
  false positives of the F-19 leg rule with the guard as an identity check,
  the F-19 percentile, a seed-label swap companion; labels FLOOR-MATERIAL /
  FLOOR-WEAK on IDEAS rank 1's 2% kill; both predictions pinned), [withheld: IDEAS not in this repository; see WITHHELD.md]
  tools/run_noise_floor.py, tests/test_noise_floor.py (21 tests), the IDEAS [withheld: IDEAS not in this repository; see WITHHELD.md]
  dated note, two state-file negations, `-text` for the tool and the test;
  the critic's three pre-freeze rounds recorded in the block.

## 2026-10-04 - OQ-9 stage 1: the horizon read at the R2 encoding, a K-6 lead-time datum (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row, since
  a commit cannot cite itself) feat(prefetch): land the horizon read - both
  registered runs from the clean tree at 5e0e2a9,
  results/real/prefetch_horizon_s3{,_r}.json with their metas and state
  files; label LEAD-TIME-ABSORBED on both harvests (H-ABSORBS at every
  horizon, REPRODUCE EXACT at horizon 1); F-26's fourth dated status line;
  the dated K-6 STATUS line; the block's OUTCOME with both predictions
  scored; the OQ-9 closure note and the dated line under its stage-2
  sentence; dated pointers on the sites the registration names;
  tests/test_prefetch_horizon_landing.py; the tool joins the frozen closure
  (ruff exclude, CLAUDE.md ten attested of thirteen, the SHARP_EDGES entry);
  the measured counts in README and docs/CONVENTIONS.md.
- 5e0e2a9 docs(memory): log the horizon-read registration (retroactive) -
  the session-log row for the registration session, which ended on the
  freeze commit without a handoff; the runs started from this commit.
- b41d3f3 feat(prefetch): register the horizon read at the R2 encoding - the
  dated amendment block (horizons 2, 3, 4 on both S3 harvests, features at t
  as R2 builds them, the token tables horizon-matched, k and lambda
  re-selected per horizon on val, horizon 1 reproducing R2's rows; labels,
  straddle, guard and free-arm-edge rules, two pinned consequences and both
  predictions pinned; NOT a rung on the horizon-1 margin),
  tools/run_prefetch_horizon.py, tests/test_prefetch_horizon.py (nineteen
  tests), the OQ-9 dated note, two state-file negations, `-text` for the
  tool and the test; the critic's five rounds and a code-reviewer pass
  recorded in the block's pre-freeze round.

## 2026-10-04 - EVID-1: sha-cited files outside results/ stored as cited (branch espalier-trial; lane and approval of 2026-10-03)

- (the EVID-1 commit; its hash is recorded in the handoff's memory row, since
  a commit cannot cite itself) fix(evidence): pin the fifteen sha-cited files
  outside results/ with `-text` in .gitattributes and store each as it is on
  disk (six blobs LF to CRLF by line endings only, among them the two frozen
  instruments run_fullfree_coarse_amended.py and run_oq18_rider_diag.py whose
  attested bytes are CRLF; no disk byte, citation or payload number changed),
  plus `-text` for tests/test_prefetch_r2.py, the R2 freeze record's 12-hex
  raw-bytes pin; check 4 of tests/test_evidence_bytes.py derives the cited set
  from the citations and enforces the pin; forward-ledger row EVID-1 struck
  with the measurements (186 of 186 citations reproduce on both kinds of
  clone; the three tests that failed on a core.autocrlf=true clone pass);
  dated updates on two docs/SHARP_EDGES.md entries, docs/CONVENTIONS.md and
  docs/TASK_RECIPES.md; README test count re-measured (584). No research text
  or results/ file touched; no on-disk (attested) instrument byte changed, the
  two frozen instruments' stored blobs changed by line endings only, with the
  operator's word recorded in the commit message.

## 2026-10-03 - The landing-text kit (branch espalier-trial)

- (the kit commit; its hash is recorded in the handoff's memory row, since a
  commit cannot cite itself) feat(tools): add the landing-text kit -
  tools/landing_text.py, the mechanics three scratch landing generators rewrote
  (the free-bigram twin, the stratified read, R2), kept once: a primary /
  replication payload pair whose reading words come from the instrument's own
  rule, a number registry so no numeral is typed and paired fragments so a
  reading that differs by side is a recorded pair, a banned-phrase assert over
  whitespace-collapsed case-folded text, and an applier that edits a record
  file by exact anchors in its own line ending with the blank-line rule for
  paragraph insertions, a region for shared phrases and a check over the diff's
  added lines; tests/test_landing_text.py (23 tests, with a positive control on
  the committed R2 payloads); a landing-texts recipe in docs/TASK_RECIPES.md;
  dated updates on the two landing-text entries of docs/SHARP_EDGES.md folding
  the three R2 landing footguns; docs/CONVENTIONS.md; README counts re-measured
  (583 tests / 34 test files / 35 drivers). No research text, instrument,
  payload or frozen-closure entry touched.

## 2026-10-03 - OQ-9 stage 1: the generalising free baseline (R2), the last rung on the twin's margin (branch espalier-trial)

- (the landing commit; its hash is recorded in the handoff's memory row, since
  a commit cannot cite itself) feat(prefetch): land the generalising free
  baseline (R2) - both registered runs from the freeze commit,
  results/real/prefetch_r2_s3{,_r}.json with their metas and state files;
  label R2-FALLBACK-SURVIVES / H-ABSORBS on both harvests; F-26's third dated
  status line; the block's OUTCOME with both predictions scored; the OQ-9
  outcome note; dated pointers on the sites the registration names;
  tests/test_prefetch_r2_landing.py; the tool joins the frozen closure (ruff
  exclude, CLAUDE.md nine attested of twelve, the SHARP_EDGES entry); the
  derived ledgers levelled.
- 2fe5926 feat(prefetch): register the generalising free baseline (R2) - the
  dated amendment block (replay-prior smoothed tables with the model's own
  routers on the token's normalised input embedding, one weight k selected on
  val; the stored final-norm state as a second question; REPRODUCE against the
  stratified read's rows; labels, straddle sentences, qualifiers, a reader
  guard and both predictions pinned; R2 pre-committed as the last rung),
  tools/run_prefetch_r2.py, tests/test_prefetch_r2.py (21 tests), the OQ-9
  dated note, two state-file negations; the critic's four rounds and a code-
  reviewer pass recorded in the block's pre-freeze round.

## 2026-10-02 - OQ-9 stage 1: the stratified coverage read of the free-bigram twin's margin (branch espalier-trial)

- 9130d16 docs(memory): log the stratified read's lane and its landing
  footguns - the ESPALIER_MEMORY.md session row for the whole lane;
  docs/SHARP_EDGES.md gains the three footguns the generated landing exposed
  (a revert re-materialising LF-convention files as CRLF, a wrapped phrase
  defeating exact replacement, a phrase shared with frozen registered text)
  and docs/CONVENTIONS.md the generated-landing practice.
- 09e846b feat(prefetch): land the stratified coverage read of the twin's
  margin - FALLBACK-LOCATED / PT-SURVIVES on both S3 harvests, the seed
  replication agreeing; REPRODUCE EXACT (the stratified rows sum to the
  twin's 12,960 committed state rows and the pooled D_eq equals the twin's
  +0.0609 / +0.0659). Both gates straddle the +0.05 floor at B = 16, j = 1:
  on the covered positions D_eq +0.0463 [+0.0398, +0.0541] / +0.0481
  [+0.0411, +0.0564] (NOT-SHOWN, the floor inside the CI), on the unseen-key
  positions +0.1940 / +0.1741 (SIGNAL); with the forward's stored
  output-distribution summaries in both arms D_eq^PT +0.0532 / +0.0565
  (SIGNAL, the floor inside the CI) and D_add^PT +0.0583 / +0.0609 (SIGNAL).
  So the coverage caveat is indicated, not settled, and the twin's verdict
  with p_t is not settled at this power; no stage-2 sentence follows.
  Reported, not a label: the covered positions split by the smaller key's
  train occurrences read D_eq +0.0658 / +0.0683 at one (SIGNAL), +0.0552 /
  +0.0503 at two to four (SIGNAL, the floor inside the CI) and +0.0438 /
  +0.0456 at five or more (NOT-SHOWN, the floor inside the CI). Six critic
  rounds across the lane, no blocker a number and every one applied;
  recompute at 0.0 over
  53,116 values; a clean-clone rerun of the replication byte-identical; 804
  landing numbers checked, 0 misquotes. results/real/prefetch_strat_s3{,_r}.json
  + .meta.json + .json.state.jsonl (110,448 / 111,696 rows); F-26's second
  dated status line; the amendment block's OUTCOME; dated pointers on five
  texts and three derived ledgers; tests/test_prefetch_strat_landing.py; the
  frozen closure at eleven files, eight attested.
- fea2431 feat(prefetch): register the stratified coverage read - the dated
  amendment block "OQ-9 STAGE-1 STRATIFIED COVERAGE READ REGISTRATION" (six
  train-coverage strata, four arms carrying the stored p_t summaries,
  branches, straddle sentences and both predictions pinned before any read);
  tools/run_prefetch_strat.py (imports the frozen twin by bare module name
  and refuses a modified one), tests/test_prefetch_strat.py (17 tests), two
  state-file negations, the OQ-9 dated note; three critic rounds (two NO-GO
  on text with every blocker applied, then GO).

## 2026-10-01 - Espalier harness adopted; the free-bigram twin of F-26; OQ-19 landed as an unfrozen draft (branch espalier-trial)

- eb0154d docs(memory): log the ledger session and the handoff-gap footgun
  - one ESPALIER_MEMORY.md row covering the fourth session (which died
  before its handoff) and the fifth session's retroactive handoff;
  docs/SHARP_EDGES.md gains the footgun with its oracle. (Added to this
  section on 2026-10-02.)
- 28c110f docs(ledger): index, changelog and glossary through F-26 and the
  twin - docs/FINDINGS_INDEX.md gains the F-24 .. F-26 rows and two arc
  sections, this file its dated sections since the release cut,
  docs/REPORT.md and docs/GLOSSARY.md dated notes, README.md its entry
  counts; FINDINGS.md's derived index table gains the F-26 row (one inserted
  line, no entry text touched); no F-27; three critic rounds to GO; 508
  passed / 5 skipped. (Added to this section on 2026-10-02: the commit could
  not cite itself.)
- f8fc727 test(instruments): guard the OQ-19 draft refusal, pin the encoding
  rule - two tests for the DRAFT_UNFROZEN run refusal (the code-reviewer's
  one WARN); the free-bigram tests gain the encoding-selection rule and the
  --conclude-from header refusals; 513 tests collected.
- edb95f5 docs(memory): record the free-bigram twin landing and the OQ-19
  draft (ESPALIER_MEMORY.md session row).
- 5760b3b docs(harness): refresh conventions and sharp edges after the twin
  landed (the byte-pinned frozen-instrument footgun recorded in
  docs/SHARP_EDGES.md).
- 6eaabf4 feat(prefetch): land the free-bigram twin, SURVIVES with a coverage
  caveat - results/real/prefetch_bigram_s3{,_r}.json + .meta.json +
  .json.state.jsonl; F-26's dated status line; the amendment block's OUTCOME
  in docs/BLUEPRINT.md; OQ-9 / P1 / README / K-6 dated notes;
  tests/test_prefetch_bigram_landing.py; frozen-closure bookkeeping
  (pyproject force-exclude, CLAUDE.md, docs/CONVENTIONS.md).
- d55e62f feat(prefetch): register the free-bigram twin of F-26's margin -
  tools/run_prefetch_bigram.py (imports the frozen stage-1 instrument and
  refuses a modified one), tests/test_prefetch_bigram.py, the dated
  amendment block "OQ-9 STAGE-1 FREE-BIGRAM TWIN REGISTRATION" with both
  predictions pinned before the read.
- 0a29d83 docs(oq19): land the oracle-ceiling registration draft as unfrozen
  - docs/OQ19_ORACLE_CEILING_DRAFT.md (the block drafted 2026-09-06/07,
  rebuilt verbatim from that session's transcript), src/sideband/real/oracle_replay.py, tools/run_fullfree_oracle.py
  and tests/test_fullfree_oracle.py with DRAFT banners and a run refusal;
  nothing of OQ-19 has run; the skip-or-pilot decision stays with the owner.
- 8f96ea5 docs(memory), ab12cbd chore(harness): harness initialisation
  finished - espalier.toml with the plan gate everywhere; ruff pyflakes-only
  with the frozen instrument closure force-excluded; tools/lint_findings.py
  requires tracked evidence; memory row.
- d614666 fix(results): store results bytes as checked out and as cited - 84
  results blobs renormalised in the index (line endings only, disk untouched)
  and pinned by tests/test_evidence_bytes.py.
- 5db262d docs(memory), c20dce4 feat(harness), 918cc9c docs(harness): the
  sideband-critic adopted as a review lane (tests/test_critic_lane.py);
  docs/CONVENTIONS.md and docs/SHARP_EDGES.md grounded on this tree; memory
  row.

## 2026-09-30 - Espalier trial deployed on a branch

- f1aabe4 Espalier trial: deploy espalier-harness (engine at main 2cb371b) on
  branch espalier-trial; no research-record change.

## 2026-09-15 - OQ-9 stage 1 (F-26): prefetch readouts on the OLMoE harvests

- c23f214 F-26 landed: PREFETCH-HEADROOM on the primary S3 harvest, the seed
  replication agrees on every label; HISTORY +0.2867 / +0.2901,
  ADDRESS-BEYOND-TOKEN +0.1032 / +0.1072 at B = 16 over the free one-token
  table (below the +0.05 floor at B = 32, j = 1), INTRA-FORWARD +0.4861 / +0.4816,
  DRAFT ceiling +0.1556 / +0.1545; two critic rounds (recompute from both
  state files to 0.0 over 1599 triples per harvest; a 412-number text check);
  the critic's blocking objection on interpretation carried as a SCOPE
  sentence on every label-bearing text; NON-CRITERION, K-6 stays UNTESTED;
  results/real/prefetch_s3{,_r}.json + state files +
  tests/test_prefetch_landing.py.
- c4c4511 OQ-9 STAGE-1 PREFETCH READOUTS: registration + instrument
  tools/run_prefetch_readouts.py (pre-run; critic-gated: three design passes
  + a final confirmation, every smoke recomputed from its state file).

## 2026-09-14 - OQ-18 landed (F-25)

- fa6537e F-25: OQ-18 COARSE-LABEL FULL-FREE RE-TEST landed under the
  2026-09-07 rider amendment (two critic recompute rounds from the state
  files, max discrepancy 0.0): S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2
  ABSORBED, S3 L3 SPLIT at the registered reader; prediction 3/4 held on
  labels; the registered raw leg reported at every cell (above its band at S1
  L3 and S1_r L2).

## 2026-09-13 - OQ-18 leak-rider amendment and its positive control

- 3ec1064 OQ-18 LEAK-RIDER POSITIVE CONTROL: DOMINANCE-CONFIRMED-HERE - the
  amended (twin-referenced dependence-excess) leg fires on a literal
  non-causal slots block at both spaces; nothing trained under the amendment
  yet.
- 5ef3ccf OQ-18 RIDER AMENDMENT (written 2026-09-07, committed 2026-09-13;
  critic-recomputed): the S1 L3 rider fire read AMENDABLE / TWIN-MATCHED; leg
  2 amended to the twin-referenced dependence-excess leg at all four harvests
  (a disclosed post-hoc reroute around a fired kill condition); amended
  instrument as a new file, tools/run_fullfree_coarse_amended.py; the S1
  state file committed at the fired sha.

## 2026-09-06 - OQ-17 landed (F-24); OQ-18 registered; launching-point ideas

- 15c4e9c OQ-18 COARSE-LABEL FULL-FREE RE-TEST: registration + instrument
  (pre-run; critic-gated; plan of record OQ-18 -> OQ-19 -> assess).
- d68aaad docs/FUTURE_IDEAS.md: post-F-24 launching-point entries P1-P7 [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
  (user-proposed) + OQ-9 / OQ-11 dated notes; idea-tier, nothing registered.
- 0b82e98 F-24: OQ-17 FULL-FREE EXISTENCE RE-TEST - F-15 and F-17 margins
  ABSORBED by the full free baseline at the registered reader (both sources,
  both harvests); corrected-twin diagnostic TWIN-ROBUST at both sources;
  prediction failed on both sources; dated errata on F-15 / F-17, K-2
  STATUS, F-16 / F-18 notes.
- 675a8f6 OQ-17 registered runs landed (S1 and S3 both ABSORBED at the
  registered reader; finding text withheld) + POST-HOC TWIN-INERTNESS
  DIAGNOSTIC registration (pre-run; critic-gated).
- 1d1a7f8 OQ-17 FULL-FREE EXISTENCE RE-TEST REGISTRATION (pre-run;
  critic-gated twice): can the K-2 existence margin survive the full free
  baseline?

## [0.3.0] - 2026-09-05 (the commit on top of 8542ef5, untagged): release documents, F-23, gate recompute tools

- FINDINGS.md F-23: OQ-16 CLOSED BY DATED ERRATUM (TARGET-FREE). The
  reconstruction target h_a is an exact linear function of the anchor's
  full next-token distribution, free information under D-5; the Stage-A
  telemetry arms are struck pre-GPU; no partition branch is claimed
  (the limbo clause is honored). Critic-recomputed with an independent
  implementation before the commit. Evidence:
  results/real/oq16_ha_identity.json from tools/ha_identity_check.py
  (GPU-box CPU tool: needs the cached lm_head and the gitignored raws;
  never imported by CI); tests/test_ha_identity.py checks the closed-form
  arithmetic on a synthetic unembedding. docs/BLUEPRINT.md block OQ-16
  DATED ERRATUM + LANE CLOSURE; OPEN_QUESTIONS.md OQ-16 closure note and
  OQ-6 dated note.
- tools/e6_gate.py + tests/test_e6_gate.py: recompute the F-19 / F-21
  tokens-per-call gates and budget guards from the committed summaries.
- Dated STATUS addenda: docs/WHY_THIS_DIES.md (K-2, K-3, K-4..K-6),
  docs/ECONOMICS.md section 6a verdict, OPEN_QUESTIONS.md OQ-1 note.
- New documents: README.md (rewritten), docs/REPORT.md, docs/METHOD.md,
  docs/GLOSSARY.md, docs/FINDINGS_INDEX.md, docs/REPRODUCE.md,
  docs/DATA.md, docs/THIRD_PARTY.md, docs/RELEASE_NOTES.md, docs/IDEAS.md, [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
  docs/BLUEPRINT_INDEX.md, data/README.md, CHANGELOG.md, CONTRIBUTING.md,
  CITATION.cff (placeholder); docs/ECOSYSTEM.md without local paths.

## [0.3.0] - 2026-09-05 (8542ef5, untagged)

Release hygiene only; no evidence file changes. The code items below are
commit 8542ef5 'Release audit (code): ...'; the documents are the working
tree of this pass, to be committed on top of it.

- Version 0.3.0 in pyproject.toml and src/sideband/__init__.py; `readme`
  field; new `analysis` extra (scipy, scikit-learn) for
  tools/build_concept_groups.py.
- `redact_args` moved to the torch-free src/sideband/provenance.py
  (re-exported from src/sideband/real/hf_specdec.py); the four tools that
  wrote `vars(args)` unredacted now route through it; new test
  tests/test_tools_and_real.py::test_every_meta_args_writer_redacts.
- torch skip guards on tests/test_probes.py::TestD2D3Instrument and
  ::TestStageEInstrument, so a `pip install -e ".[dev]"` clone passes.
- experiments/run_all.py --smoke writes to results/smoke/ (gitignored)
  instead of overwriting the committed results/*.json.
- .gitignore: HANDOFF.md (operator-local session log) and results/smoke/.
- New docs: docs/RELEASE_NOTES.md, docs/THIRD_PARTY.md, CHANGELOG.md,
  CONTRIBUTING.md; docs/ECOSYSTEM.md sibling-projects section rewritten
  without absolute paths; README.md and docs/METHOD.md rewritten in the
  same pass (separate tasks).

## 2026-09-05 - OQ-16 DR-4 and the Stage-A freeze

- 2e44105 OQ-16 STAGE-A FREEZE (pre-GPU; critic-gated): SD^2-style
  draft-side injection instrument - frozen drafter, rank-512 zero-init
  adapter on the MLP up-projections, oracle-ceiling rung A0 before the
  reconstruction rung A1, fresh 210-prompt verdict population; no GPU run
  exists at this commit.
- 786ab59 OQ-16 DR-4: COMPARATOR-TOOTHLESS - "beyond p" stays unpriced;
  F-22 dated addendum; the last reconstruction-level diagnostic of the
  lane.

## 2026-09-04 - OQ-15 terminal (F-21), OQ-16 Stage R (F-22), DR-1..DR-3

- c2181b1 OQ-16 DR-4 REGISTRATION (pre-run): the equal-dims FREETOK2
  comparator and its pinned labels.
- 7fb3440 OQ-16 DR-3: TELEMETRY-BEYOND-P - the union of telemetry and the
  hashed top-32 support beats the free token-identity arm; F-22 addendum.
- 2ec789f F-22: OQ-16 Stage R PASS by the gate; DR-1 confirms the
  deployable margin; DR-2 shows a free token-identity encoding
  reconstructs h_a at least as well; DR-3 registered pre-run.
- bd71358 OQ-16 FOLD-BACK #2 ARC REGISTRATION + Stage-R instrument
  (pre-run; critic-gated).
- ad32345 F-21: OQ-15 Stage C CONVERSION-MODE NULL; seed-3 guard clears
  every leg; OQ-16 (fold-back #2) authorized.

## 2026-09-03 - K-3 verdict (F-19) and OQ-15 Stage I / Stage C

- 46ab439 OQ-15 Stage C: seed-2 verdicts breach the pairwise guard
  (arm-6 leg); registered void semantics executed, seed-3 rerun.
- 9e8fa4a OQ-15 STAGE-C FREEZE: deferred-constants amendment, head-policy
  instrument, binding-gated weight export (pre-GPU; critic-gated).
- 44b08fa F-20: OQ-15 Stage I mechanical PASS; the five-seed stale-target
  control leaves the margin indistinguishable from zero-information
  draws; the telemetry head loses to the free head outright.
- 89b38ef OQ-15 FOLD-BACK #1 ARC REGISTRATION + Stage-I instrument
  (pre-run; critic-gated).
- 77d5249 F-19: K-3 Attempt #1 NULL (verdict, seed-1 void-rerun),
  critic-recomputed bit-exact; arc concludes, fold-back #1 = OQ-15.

## 2026-09-02 - K-3 stage E, threshold searches, precondition, void

- 92fa9cb K-3 FOLD-BACK COUNT AMENDMENT (user-directed): one fold-back
  widened to a structured two, critic-gated.
- 48814ac K-3 VOID: budget guard breached on the arm-2 leg; void
  semantics executed, seed-1 rerun launching.
- cbe3ee3 K-3 precondition COMPLETE (arms 1-3, verdict population,
  seed 0): NO FOLD-BACK, verdict proceeds.
- e0ae94f K-3 stage E: threshold searches complete (arms 2/3/4),
  critic-recomputed; selections frozen.
- 0663864 K-3 threshold-search driver + B_ref evidence, critic-gated.
- 36600cb K-3 tap rider PASS (16/16) + threshold-search registration.
- 7d3450f K-3 stage-E evidence: export/containment/calibration PASS +
  tolerance amendment.
- 69cb8f2 K-3 stage E: live scheduling instrument + clarifications
  E1-E12, critic-gated.
- dc03bfa D2/D3 evidence committed + K-3 confidence signal FROZEN.
- eaea1d5 OQ-16 ledgered (vector reconstruction -> SD^2 actuator under
  the observability constraint) + dated K-3 byproduct amendment.
- cf90b41 OQ-15 primary supervision = analytic-acceptance regression;
  byproduct amendment extended; docs/FUTURE_IDEAS.md created. [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
- 41bdbc7, 713a1cf, 32f34ec, 3ca9373 FUTURE_IDEAS entries (telemetry-Medusa, [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]
  post-arc asset distillation, trajectory-anomaly idea with its
  provenance correction and complementarity assessment).

## 2026-09-01 - S3 existence (F-17/F-18), economics memo, K-3 registration

- f623e33 D2/D3 instrument: error-predictor + calibration tool,
  critic-gated; full_eval probe path (default byte-identical).
- 2db51aa K-3 verdict prompt set committed BEFORE any D2/D3 output exists.
- 1c14db4 K-3 Attempt #1 arc REGISTERED: adaptive-scheduling actuator,
  matched-budget gate, D2/D3 diagnostics - three critic rounds.
- 59b3305 OQ-15 ledgered: outcome-supervised readout.
- 39e05c0 K-5/K-6 economics memo (docs/ECONOMICS.md): the K-3 win and
  materiality bars pinned before any actuator experiment exists.
- 6cf7e1e F-18: S3 P1-analog - P1-SURVIVES on both harvests.
- f3bb32e F-17: EXISTENCE at S3 CONFIRMED - pure address-stream
  MoE-router telemetry replicates on fresh seeds.
- 83406b1 S3 replication harvest evidence (seeds 8-11); R1-S3 16/16 PASS.
- d8cb7a0 OQ-13 + OQ-14 ledgered (post-replication registered secondaries).
- dec515b S3 grid: provisional EXISTENCE, critic-verified by
  recomputation; replication running.

## 2026-08-31 - S1 existence (F-15/F-16), S3 registration, working practices

- 808266e S3 harvest evidence: 8 seeds, exit bar MET; R1-S3 16/16 PASS.
- 892a40a S3 spaces + calibration + tolerance amendment.
- 3eb5efd S3 registration + instrument: MoE router address stream (OLMoE).
- f3d05d4 CLAUDE.md: working practices earned on the Phase-2/3/P1 arc.
- 1e12957 F-16: the tap margin is not topic-state (post-hoc P1).
- 1a54fb7 P1 registration: prefix-topic control (pre-results).
- 958b0fb F-15: K-2 survived at S1 - telemetry beats free information at
  offsets 2-3, replicated.
- 86136c8 Phase 3 S1 grid evidence: verdict EXISTENCE (provisional),
  replication registered.

## 2026-08-30 - Phase 0b/0c results (F-11..F-14), Phase 2 harvest, Phase 3 registration

- fba1fb3 Ecosystem: probe-estate salvage survey.
- e6b22c9 R1 quarantine cycle: tolerances recalibrated via the registered
  path, fresh-triple rerun 16/16 PASS; L3 artifact built.
- 9ca4308 Phase 3 implementation: probe machinery, riders R1/R2/R3, L3
  builder, runner.
- c344e15 Phase 3 registered: probe protocol, decision rule, riders;
  pre-probe audit committed.
- 0aa38dc Phase 2 S1 harvest evidence: 8 seeds, exit bar MET.
- e8669d2 Phase 2 registered + shadow harvester: block-start alignment,
  4-space free-info logging, sha-bound evidence chain.
- 7d46466 F-14: oracle ceiling at coarse k bounded at ~zero; attribution
  rider returns the registered STRADDLE.
- 910522b oracle_nextp: the attribution rider arm.
- 814fc34 F-13: OQ-12 answered negative - coarse gating restores gate
  selectivity, mechanism still loses.
- 8f2f1ba OQ-12 evidence: coarse bucketizations, glue sets, diagnostics.
- 89173bd OQ-12 / Phase 0c protocol pre-registered.
- 6045158 F-11 + F-12: OQ-4 answered; Phase 0b free baseline is null;
  gate-granularity failure diagnosed.

## 2026-08-29 - v0.1.0, v0.2.0, v0.2.1 and Phase 0a (F-10)

- 6a468f1 OQ-4 evidence: frequency harvest, glue sets, Phase 0a re-analysis.
- db9df6b OQ-4 + Phase 0b machinery: concept-space steering, glue
  identification, pre-registered protocols.
- 1fb67f3 F-10: Phase 0a real cross-bucket audit - kill criterion K-1
  does not fire.
- b1dae57 KV-cache fast path with exact-recompute reference.
- f946a50 Audit run semantics: proposal coupling, per-prompt RNG, resume,
  evidence binding.
- 883dd6a Phase 0a evidence: vocab buckets k=256/512/1024 for
  Llama-3.1-8B-Instruct.
- 4b7194d kmeans convergence bug fix + Phase 0a audit inputs.
- 3da97f4 Phase 0a prerequisites: CI machinery, NF4 target loading, K-1
  pre-registration.
- 83c9bd5 docs/ECOSYSTEM.md: sibling-repo map.
- c93b427 v0.2.1: prior-art deep dive, OQ-11 streaming/anytime steering,
  probes/ tier with p01_anytime_posterior.
- bcaa84e v0.2.0: posterior mechanism default (F-7, D-10/D-11),
  variance-free cross-bucket estimator (F-8), verified-archives hint
  ledger (F-9), KV-page telemetry adapter, emergent tracks OQ-7..10; v0.1
  results reproduced bit-exact.
- 21b9010 v0.1.0: exact verifier core, synthetic testbed, gated steering
  mechanism (F-3), real-model adapters, seeded findings F-0..F-6,
  blueprint v2 with kill criteria.

# Commit log of the private sideband repository

186 commits, newest first, up to e3d7ea76b93dd5497aae99d75abc2fe590b7bce7, the commit this folder is exported from. The public repository has a fresh history, so the hashes the record cites (FINDINGS.md, DECISIONS.md, OPEN_QUESTIONS.md, docs/BLUEPRINT.md, CHANGELOG.md) resolve here and nowhere else in the public tree; the review rounds each landing records are in these messages. Absolute paths outside the repository are scrubbed; paths into the author's own sideband checkouts stay (the export's own-checkout rule). 8 messages name a private repository or match the deny list: each keeps its subject with the match replaced and has its body replaced by a `[withheld: ...]` line. A line naming a file this export withholds carries the same marker the rest of the folder uses.

## e3d7ea7 2026-10-19 docs(release): one CI=1 sentence for a reader on another machine

````text
The public cut's third source commit (plan 15.11). The owner's word on
the one-sentence approach, read by 16:43 on 2026-10-19: "lets take the
'add one line for warning and move on' approach here". The root README
source's CPU bullet and tests/README's "Fail, not skip" paragraph gain
one sentence telling a reader on another machine to set CI=1 before
pytest to skip the three named machine-bound lens gates (in a clone
that git can read, no other test's outcome depends on that variable;
SIDEBAND_REQUIRE_CPU_BOUND=1 runs them regardless). The step-8 note of
docs/RELEASE_NOTES.md records, dated, that the word on this approach
was read by 16:43 and that its rule holds for the word on the narrowed
assertion, asked again at 17:10 and open when this commit was made.
CHANGELOG marks the second source commit superseded as the release's
source, describes this one, and says where the earlier exports'
commits and workflow runs stay (the release repository, by SHA and
under its Actions; keeping or deleting them is the owner's call, asked
before the flip). The plan records the word verbatim with its time,
pre-registers the third export, its scan, proof, push and CI run, the
tag before the flip, and carries two dated amendments and a dated
erratum after three critic rounds (NO-GO, NO-GO, GO with seven
advisories, each taken). The lane's record folder, private beside the
public-cut sources, holds the briefs, the reports (checked against the
session transcript), the logs and the sweep. No tool, test-code,
workflow or instrument change.

Proof, under the record's carve-out for a docs-only edit, after the
last shipped edit (18:14:11): the export tool's own test file 28
passed in 1868.54 s (18:14:15 to 18:45:24, exit 0);
tests/test_harness_doc_claims.py, tests/test_reader_s1_landing.py and
tests/test_evidence_bytes.py 15 passed in 37.51 s (exit 0 at
18:15:02); tests/test_evidence_bytes.py over the record folder 7 passed
in 25.50 s (exit 0 at 18:46:49); after the last record edit (19:05:05)
the same three readers 15 passed in 27.47 s (exit 0 at 19:05:35) and
python tools/evidence_pins.py 160 cited digests, 0 unresolved, 0
uncited, 0 moved, 0 new, the folder's 26 files intent-to-add.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d7b656d 2026-10-19 docs(memory): log the pinned-export lane, thirteen critic rounds, release held

````text
The forty-second session's row: commit A exported, proved and pushed; the first CI run red on four CPU-bound gates; the CI fix landed as commit C, exported, proved, force-pushed and CI-green; commit D the record. The next session picks up at the one open gate: the operator's word on the named skips and the narrowed assertion, then the flip and the v1.0.0 tag.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b3efafb 2026-10-19 docs(record): export 2 proved, CI green, flip held for the owner's word

````text
The private record's commit after the public cut's second source commit
(plan 15.10). The second export of that commit (export head 01def67,
2,731 files) read SHIP: GO, its proof PASSED with every one of 25 stages
at exit 0 and the sideband stage at 724 passed, 35 skipped, so the three
lens gates ran in the proof; its receipt joins the proofs folder. The
three proof clones' heads equal the export head (the by-hand check for
the deferred tool item). The export was force-pushed, with a lease on
the first export's head, onto the still-private release repository, and
its CI run 39296259806 read green on all three jobs, the sideband job at
717 passed, 42 skipped, the expectation written before it; the job's log
joins the record folder with the thirteenth critic round's brief and
report. The plan records all of it, the post-flip export rule, and the
one thing still open: the owner's word that the three named skips and
the narrowed prefetch assertion (vacuous on GitHub's runner) satisfy the
release gate; the flip to public and the v1.0.0 tag wait on it.

No shipped file changes in this commit: a tests/README run line and a
CHANGELOG bullet drafted for it were restored to the previous commit's
text after the critic found the line misdated two batches and cited the
wrong chain's counts; the record carries the facts instead.

Proof: the pins tool reads 0 new, 0 unresolved; the export tool's test
file (28 passed), the evidence, critic-lane and record-claims tests (17
passed) and the pins ran on this tree before the two shipped files were
restored and the withheld edits made, which no test reads.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## bb916db 2026-10-19 test(ci): skip three CPU-bound gates under CI, narrow one assertion

````text
The public cut's second source commit (plan 15.10), after the release
repository's first CI run on ubuntu read 4 failed, 716 passed, 39
skipped in the sideband job while amber and lockstep passed. Three
landing tests reproduce registered lens payloads byte for byte through
the frozen instrument's rider gate; that gate refused on GitHub's runner
(Python 3.12, numpy 2.5.4, scipy-openblas 0.3.34.106.0, 2 CPUs) and
holds on the author's machine and in four Linux containers on its CPU
that matched the runner's versions, OpenBLAS build, thread count and
distribution, so the runner's CPU is the leading candidate and which
operation moves is not measured. Those three tests now skip under the
variable CI, by name and each saying why, with SIDEBAND_REQUIRE_CPU_BOUND=1
running them anywhere. The fourth failure was a synthetic prefetch
fixture whose twin's fallback margin read NEGATIVE on the runner where
the author's machine reads exactly zero; its one share assertion is
narrowed to a positive twin margin, with a dated amendment at the end of
docs/BLUEPRINT.md because that test file is registration-pinned (its
sha256 prefix moves from c9a8efa7cd5e to 7528cfef155d). No instrument,
tool or workflow changes.

The record says so, dated: the root README source's CPU bullet and GPU
sentence, tests/README's "Fail, not skip" section, docs/SHARP_EDGES.md's
new entry, docs/REPRODUCE.md, docs/RELEASE_NOTES.md, the four module
docstrings, CHANGELOG's second bullet. The private record gains the
first export's proof receipt, the CI job's logs, the four container logs,
the targeted and suite logs, and every critic brief and report of the
lane (twelve rounds on this commit's diff; the reports regenerated from
the session transcript).

Proof: no full suite ran on the committed tree. The fourth full run
(10:38:28 to 11:25:20, 782 passed, 5 skipped, exit 0) ran across the
docs-only batches of 10:54:54 and 11:08:50; the batches of 11:31:30 and
12:13:53 and the new withheld files came after it. Under the record's
carve-out for docs-only edits, the tests that read those files were
re-run after the last edit: the export tool's own test file alone (28
passed), the three BLUEPRINT readers, the evidence and critic-lane tests,
and the pins tool (0 new). The four edited test files: 33 passed with CI
unset, 30 passed and 3 skipped under CI=1, the override runs a gate.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 9957e59 2026-10-19 docs(release): fill the Zenodo DOI, re-measure the raws, add the deposit manifest

````text
The public cut's final source commit before the v1.0.0 export (plan
15.10). The three Zenodo DOI placeholders in the root README source and
the root CITATION.cff source now read 10.5281/zenodo.23462826, the
record reserved on 2026-10-18 for the gitignored raws and read off the
draft page by the operator on 2026-10-19; the release date is given to
the export by its flag on the day, so CITATION.cff keeps that token.

The root README's data table gains a third row, the twelve seed-6 and
replay folders of 2026-10-09 and 2026-10-10 (1,281 files, 1,086,399,860
bytes, bound by each run's committed summary), and its total is
re-measured at 14,456,199,684 bytes for 5,175 files, exactly the Zenodo
deposit: 34 zip archives, one per byproduct folder and one holding the
24 harvest shards by bare file name. docs/DATA.md gains a dated section
tabulating the archives (source folder, files inside, bytes, sha256)
from the list the packing script wrote beside them, with the shards'
folder mapping and the reconciliation against the 2026-09-05 inventory;
the two list files are kept beside the export sources. README.md's two
counts of the raws gain dated clauses. The export test's three
real-tree pending lists shrink to the release date alone.
docs/SHARP_EDGES.md gains the entry on the hooks' state folder being one
per checkout, shared by every session open in it. No tool change.

Proved by the full suite on this tree after the last shipped edit (782
passed, 5 skipped in 3,089.79 s, exit 0), the five real-tree export
tests before it (5 passed in 1,698.36 s), the pins tool (160 digests, 0
new), and three critic rounds (two NO-GO on text, then GO on conditions
met here).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d0eb166 2026-10-19 docs(memory): log plan 15.9's landing, the raw scan and six critic rounds

````text
The row records the forty-first session: the owner's four calls landed in both siblings and the export tool's prove running the sibling jobs from the workflow (ecceaad), the raw scan that cleared the Zenodo deposit, three full runs and six critic rounds to GO. The next session picks up the pinned-export lane: fill the DOI and the release date at the final source commit, export, prove, push the private remote with Actions on, flip and tag.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## ecceaad 2026-10-19 feat(export): land the owner's four calls; prove runs the sibling jobs

````text
Decision 2 ("Ship it"): amber's results/p1, p4, p5 and p6 ship; the
errata plan's step-1 sentence becomes a decided keep in the AMBER spec
(record_decisions), with a dated note in amber's own record, so the
export's last record-flag drops. Item 16 ("Keep the pointer."): no bytes
change. Item 12 ("we can ship that one too"): lockstep's commercial
register ships as written, with dated notes at F-8, docs/09's EF-4 and
D-14 pointing to the audit's item B3. Item 19: amber's gate before
publication is waived by the owner in a dated line (no counsel review;
the prior-art search not re-run), with dated lines under OQ-6 and K-1.
The pins move to amber 0b061b5 and lockstep a84bef4.

prove reads the exported root workflow right after the clone and runs
each sibling folder's job as the workflow states it (one clone and one
venv per job, the job's working directory and env, each run line as the
venv's own program, then its pip freeze), in place of the two refusals;
a strict line reader refuses what it cannot follow; a sibling job must
run in its own folder; the scratch folder must be empty; the proof stamp
binds the manifest bytes as read, and a manifest that moves during the
proof fails it; an amended or rebased sibling pin is a binding blocker;
the launching shell's GIT_*, PIP_*, SIDEBAND_*, TRELLIS_*, PYTHONPATH,
PYTHONHOME and PYTEST_ADDOPTS never reach a stage (the tool's own stages
set SIDEBAND_REQUIRE_ANALYSIS themselves).

Record: docs/PUBLIC_CUT_PLAN.md 15.9 (the verbatim calls, two exports, [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
the first proof, the sibling run, the raw scan, six critic rounds and
the full runs), CHANGELOG.md, tests/README.md, docs/TASK_RECIPES.md,
docs/SHARP_EDGES.md, docs/CONVENTIONS.md, docs/public_cut/ROOT_README.md [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
and docs/public_cut/ci.yml. The full run read 782 passed, 5 skipped in [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
3,440.02 s (the first run read 1 failed, 781 passed, 5 skipped: the
launching shell's SIDEBAND_REQUIRE_ANALYSIS reached the amber job, fixed
in the drop list; the second was stopped for the hardening batch).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 57867dc 2026-10-18 docs(memory): log the cold read and the dated-note batch, three critic rounds, landed

````text
The fortieth session's row: five unanchored cold reads of the three repositories, the dated-note batch landed at 783763c with both sibling pins moved (amber 5fbc9bd, lockstep 4b6bcc1), the bf16 scope claim withdrawn, decision 1 recorded, the suite green once. The next session picks up the sibling prove stages, then the packer lane with lever 4, then the one pinned export, with the operator's open calls listed in plan 15.8.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 783763c 2026-10-18 docs(record): cold-read dated notes, moved sibling pins, two byte pins

````text
Five reviewers read the three repositories cold on 2026-10-18 with the
owner's question and none of the record's conclusions
(docs/PUBLIC_CUT_PLAN.md 15.8). This commit lands what the record owed [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
them in this repository and pins the siblings' own landings.

- docs/PRIOR_ART.md gains a 2026-10-18 section: twelve papers, each
  fetched that day and logged with its fetched title (the softmax
  bottleneck behind F-23; the MoE-routing analyses F-24 is consistent
  with; future-token information; probing practice; routing as signal;
  the Spec-Bench survey).
- FINDINGS.md gains dated notes under F-23 and F-24 placing the record's
  own concessions against that literature, scoped to what the fetched
  abstracts state and, for routing, to S3.
- tests/test_frozen_imports_pinned.py pins tools/run_probes.py and
  tools/run_posthoc_topic.py by their LF sha256 (both unchanged since
  8542ef5); .gitattributes holds both -text; tests/evidence_pins.json
  gains the two digests; a scratch-worktree mutation of each file fails
  its test.
- tools/export_public_cut.py: the seven amber critic-script flags become [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  decided keeps (the operator's word, 2026-10-18); the amber pin moves
  to 5fbc9bd and the lockstep pin to 4b6bcc1, the commits carrying their
  dated notes and the corrections made after the critic's recompute;
  the residue reasons point at the decisions.
  tests/test_export_public_cut.py follows the change. [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
- docs/public_cut/ROOT_README.md names the new pins and carries a dated [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  sentence beside the amber headline figures (non-looped divergence
  13.40%, zstd-19 at 7.492 bits per token, 8.39x against 7.64x) and
  scope clauses on the bf16 sentence (cross-dtype rates) and on the
  conformance vectors (none reaches the rescale clause); the tone
  allowlist gains one entry for a quoted paper title.
- docs/LESSONS.md entry 16 (the site survey before registration);
  tools/lint_findings.py's docstring scopes "CI" to the public workflow;
  CHANGELOG, tests/README.md and the plan's 15.8.

Proof: an export at the worktree snapshot 5e96c74 with both new pins
read NO-GO 5 (pending 4, record-flag 1, every other class 0); the full
suite once on the final tool and tests with both sibling fixtures
required, 778 passed, 5 skipped; three critic recomputes (maximum
discrepancy 0 on every figure; one prose count corrected); code review
approved with notes.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## bdda569 2026-10-18 docs(memory): log the lockstep survey lane, six review rounds, landed

````text
The session row records the lockstep folder's entry into the public cut
at 9e04741, its audit, the review rounds and the operator's open calls.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 9e04741 2026-10-18 feat(export): the lockstep folder enters the public cut with its survey

````text
The LOCKSTEP FolderSpec (docs/PUBLIC_CUT_PLAN.md 15.6 and 15.7) binds [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
the lockstep checkout at the fourth of four commits of 2026-10-18
revising lockstep's front door or its audit report, which the plan and
the CHANGELOG name. The operator's three calls of 2026-10-18 are
applied: the agent harness the record was kept with ships, the archived
and never-run task packs ship, and the commercial-positioning passages
(two open questions, a prior-art section on market signals and its
closing paragraph) are withheld by marker. Withheld whole: the planning
document, the review with its parked proposals, the patent and licensing
notes and the private workflow. The patent-review task pack keeps its
title and archive status, its body withheld by section, because the
harness's reference checker resolves the record's citations of it to the
file; the two patent numbers and their claim reading are withheld by
anchor at two sites, the counsel sentences around them kept. Two home
paths into the amber checkout are scrubbed; three extra mention forms
catch the record's shorthand citations of the withheld documents,
measured over the three trees, with four sideband lines kept as residue;
four probes make a recurrence of either patent number a blocker.

Tool: the placeholder scan honours a residue entry whose own text
carries the match, which keeps the cost model's label for its assumed
inputs; prove refuses an export holding the lockstep folder until it has
a proof stage, as it refuses amber's. The root CI source gains a
lockstep job running the folder's five validation commands; the tone
allowlist 40 lockstep entries, each with its reason. The root README's
lockstep section is rewritten from lockstep's record at the pin with its
placeholder removed; NOTICE says the folder runs no neural model;
docs/ECOSYSTEM.md's line calling lockstep's range coder amber's
production coder carries a dated note. Tests: the lockstep spec's pins
and a three-folder real-tree fixture that skips where a sibling checkout
is absent and fails instead when either SIDEBAND_REQUIRE variable is
set.

Staging exports: 69 blockers at the previous pin with a draft spec; 12
with the final spec at the new pin (the pending markers and amber's
operator flags), every other class 0; the folder's five validation
commands pass inside a copy of the export and in fresh clones made with
core.autocrlf true and false. The read-only image audit of lockstep (19
Opus agents; 165 findings, 131 confirmed, 31 downgraded, 1 upgraded, 2
refuted, 8 added; 171 survivors, 25 high in ten distinct defects) is
committed in lockstep's own repository with its new first screen and a
.gitattributes that keeps the two conformance-vector copies LF in a
clone. Full suite on the final tool and tests: 775 passed, 5 skipped.
The critic's six rounds, five of them NO-GO on sentences, and the code
and failure-mode reviews are recorded in the plan; lockstep's commits
and this one are not pushed.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 9a3f03c 2026-10-18 docs(memory): log the amber survey lane, six review rounds, landed

````text
The row records the amber audit-plus-survey lane (the AMBER FolderSpec at amber's third front-door commit, the audit's tally, the root README's amber section, the tests, plan 15.5, CHANGELOG), the tool defects fixed at review, the review rounds and preflight's suite on the final tree. The next session picks up lockstep's survey through the lane, with the operator's five open calls of plan 15.5.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 49aabc1 2026-10-18 feat(export): the amber folder enters the public cut, its survey landed

````text
The AMBER FolderSpec (docs/PUBLIC_CUT_PLAN.md 15.5) binds the amber [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
checkout at its third front-door commit (2026-10-18, after the critic's
two rounds), which the plan and the CHANGELOG name: the private workflow withheld whole; the patent passages
withheld by exact anchor at their four sites with the kill criterion K-1
and the open question OQ-6 kept as structure (the operator's call 2);
four private-name mentions replaced in place and a fifth kept as residue
in a file two errata payloads pin by blob; the two saved arXiv pages
kept (call 3, decided 2026-10-17: withholding them would make their
digests withheld digests inside frozen evidence); docs/ERRATA_PLAN.md's
four sibling-checkout paths scrubbed and its two sideband-checkout paths
kept (call 1); the Hugging Face cache paths in eight frozen files as
residue; eight operator flags that block the verdict until decided (the
seven critic scripts whose absolute path carries the sibling checkouts'
parent folder name; the plan's sentence of 2026-10-10 that four
token-id folders are never for public release). FolderSpec gains
paths_note and log_cites, the per-folder sentences of WITHHELD.md's Paths
paragraph and the commit log, with sideband's former text on its spec;
mention_re returns a never-matching pattern when a spec derives no name
(an empty alternation matched every line and refused amber's .gitignore)
and refuses an empty alternative; every file is scanned against every
folder's withheld names, not its own folder's only; a residue entry that
matches no line is a stale-record hit; prove refuses while amber has no
proof stage; the manifest records pin_on_remote and head_past_pin.
The root CI source gains an amber job (green once lockstep's folder
exists); the tone allowlist nine amber entries; the root README's amber
section is rewritten from amber's record at the pin with its placeholder
removed and the two sentences deferring to amber's survey reworded;
NOTICE states amber's model use. Tests: the amber spec's pins and an
amber real-tree fixture reusing the sideband snapshot, skipped with its
reason where the checkout is absent.

Staging exports: 41 blockers at the previous pin with a draft spec, 14
with the final spec and sources at the new pin (the lockstep layout
blocker, the pending markers, the operator flags), every other class 0. The read-only
image audit of amber (19 Opus agents; 141 findings, 101 confirmed, 38
downgraded, 2 upgraded, 0 refuted, 11 added; 152 survivors, 7 high; no
finding's status word changed, three pre-registered P3 band readings and
F-12's byte breakdown among the survivors) is committed in amber's own
repository with its new first screen and two pyproject lines, corrected
in two further commits after the critic's rounds; none is pushed. Plan
15.1 carries the dated call-3 line, 15.5 the landing, 13.4, 14.3 and 15.4
dated lines. No frozen tool, payload, state file or registered text
changed; no label moved.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 6b11486 2026-10-17 docs(memory): log the binding lane, four review rounds, landed at 517e46a

````text
The row records the per-folder binding lane (tool, test, plan section 15 with the operator's four calls on amber, CHANGELOG), the marker-order fix, the review rounds and preflight's suite on the untouched tree. The next session picks up the amber audit-plus-survey through the lane, with the digest-scan question of call 3 for the operator.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 517e46a 2026-10-17 feat(export): bind each public folder to its own checkout and pin

````text
tools/export_public_cut.py reads each public folder from its own private [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
checkout at its own pinned commit (plan 10.7; landed before the sibling
surveys by the operator's word of 2026-10-17, plan 14.3 dated line and
section 15). FolderSpec gains `checkout` and `commit`; Export.bind
resolves (checkout, sha) per folder, overridable per run by --checkout
NAME=PATH and --folder-commit NAME=REV, with every unresolved binding a
refusal (exit 3) before anything on disk is touched, git's stderr quoted
for a plain directory and the tool's own words for a bare repository;
export_folder, withheld_md and commit_log read the binding; load_folder
registers every folder's withheld blobs before any folder is edited, so
the digest scrub and the commit log do not depend on the export order;
forbidden_remotes is the union over the tool's repository, every bound
checkout and each sibling spec's own checkout, and a sibling with no
remote anywhere is a blocker; a sibling exported at a commit other than
its spec's pin is a blocker of class binding, at export and at scan; the
export commit's message names each folder's sha12; the manifest records
source_commits and checkouts, scan re-binds from them (a refusal names
what scan can do), prove carries source_commits in the receipt. Sideband
stays bound to --repo and --commit; no FolderSpec but sideband's exists
(grep -c "FolderSpec(" prints 1).

Found by the lane's two dry exports and fixed here: mark_mentions sorted
marker names with key=str.lower alone, so a case-variant pair (IDEAS.md, [withheld: IDEAS.md not in this repository; see WITHHELD.md]
ideas.md) fell to set order, which varies with the process hash seed, [withheld: ideas.md not in this repository; see WITHHELD.md]
and two exports of one commit could differ in one marker of
ESPALIER_MEMORY.md; the key is now (lower, text), probed in fresh
processes under PYTHONHASHSEED 1 to 7 in test_helpers (the old key fails
that probe at seeds 1, 2, 3 and 7).

tests/test_export_public_cut.py: [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
test_fixture_sibling_folder_is_bound_to_its_own_checkout_and_pin (a
second private repository exported at a pin older than its HEAD; each
refusal the test names; its remote refused by the hook and forbidden
still when a clone of it is bound; scan's re-binding, refusals and hint;
the pin and no-remote blockers; a refused re-run leaving the previous
export in place; a sibling's withheld digest scrubbed from a folder
exported before it); the prove receipt's source_commits asserted.

docs/PUBLIC_CUT_PLAN.md: a dated line under 14.3 and section 15 (the [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
operator's four calls on amber verbatim with the assistant's reading,
the amber gate counts at 69b437c, the mapping of sideband's removal
classes onto amber, the binding as landed, the ordering defect, the
proof, the traps for the survey lane including the digest-scan question
that call 3 opens, the owed items). CHANGELOG.md entry.

Proof, 2026-10-17: the export test file 20 passed in 831.54 s on the
final tool and test bytes (real-tree tests included);
tests/test_evidence_bytes.py tests/test_harness_doc_claims.py
tests/test_critic_lane.py 16 passed in 55.63 s; preflight's `ruff check
.` on the final tree: All checks passed; lint_findings OK (30); espalier
audit pass, integrity ok; reflect 25 gaps / 4 orphans, unchanged from
the pre-lane baseline; a dry export of HEAD with HEAD's tool
(988369c7b637) against a dry export of a snapshot holding HEAD plus the
final tool and the final test (ed5be8d01c6a) with the final tool
(cac6f8da674a): the same NO-GO (8 blockers), 1,002 files, only the two
generated files differing. Preflight's full suite on the untouched final
tree, started after the last edit: 771 passed, 5 skipped in 2656.62 s.
Review: the sideband-critic four rounds (diff, confirmation, two scoped)
and the code reviewer two rounds, all Opus, one fix batch per round; the
last round GO with advisories only. No frozen tool, payload, state file
or registered text changed; the plan and CHANGELOG diffs are insertions
only.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d4c4284 2026-10-17 docs(memory): log lane D, the first screens and tests/README.md, landed

````text
The row records lane D's landing at 837251c (plain-language first screens for README.md and the public root README, tests/README.md, F-29 carried into the root README and CITATION.cff; three review rounds each; the full suite 770 passed, 5 skipped) and the headline rules the critic enforced. The next session picks up plan 14.3's order: the amber survey, the per-folder binding, the packer with lever 4, the pinned export.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 837251c 2026-10-17 docs(craft): lane D, plain-language first screens and tests/README.md

````text
Lane D of the 2026-10-15 image audit (docs/PUBLIC_CUT_PLAN.md 14.3), the [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
two items it named plus the first-screen item both walkthrough readers put
first. Documentation only: no frozen tool, payload, state file or
registered text changed; no label moved.

README.md: a plain-language opening (the question; the answer scoped to the
registered reader with the probe capacity named beside every margin; how it
was run and by whom: one human researcher who arbitrated, an AI coding
assistant, and the critic as a second AI agent of the same model family run
as the assistant's subagent) and a one-line-per-term list before the first
house label; the 2026-10-14 front door kept beneath under "The verdict in
the record's words" (its verdict paragraph, table and side-results paragraph
byte-identical; its first paragraph folded into the opening); the
how-to-read list gains tests/README.md, F-29 and the REPORT abstract's
record-boundary note; Quickstart and repo-map counts re-measured on
2026-10-17 (53 test files, 775 tests collected, 30 findings, 43 top-level
tools); dated notes on the licence bullet, the history's end and the two
remaining "S1 not run" clauses (F-29 pointers).

docs/public_cut/ROOT_README.md: the same kind of opening, the two repeated [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
sentences removed, "What this repository is" folded upward, the first two
sentences of "The question and the answer" shortened to their F-0/F-1
clause, and F-29 carried into the kill-criteria paragraph, the existence
row and "F-0 to F-29" (it still read "S1 not run" after the S1 reader
re-test landed at c9649bb); [pending: count unchanged at 5. CITATION.cff: a
dated F-29 clause under the abstract's 2026-10-16 note.

tests/README.md (new): the four kinds of test file, fail-vs-skip as
measured (the five skips on a fully provisioned box and what else skips on
a .[dev] install; ten of twelve landing files assert the evidence exists,
two still skip, two skip a checkpoint-dependent test; every count with its
date and command), the six test files a freeze record pins (HAND_PINNED,
-text) and their two disclosed post-freeze edits, the conftest fixture, the
import mechanics, the witnesses' staging rule, how to run with TP-1's
measured timings. docs/CONVENTIONS.md "Tests" gains a dated pointer to it
with two moved facts.

Dated notes: docs/audits/2026-10-15-image-audit/README.md (section D
dispositioned; the deferred items named), docs/PUBLIC_CUT_PLAN.md 14.3, [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
CHANGELOG.md.

Reviews, both on Opus, three rounds each, edits frozen while they read and
one fix batch per round. sideband-critic (diff mode): NO-GO at six blockers
(probe capacities mixed in the headline numbers; "did not overturn" read
over L2, where no stronger reader ran; "coarsest" for L3, a space of 16
groups like L1's 16 classes; the registration claim without F-25's reroute
words; the critic's independence overstated; the ls-files claim in
tests/README.md), NO-GO at one (the headline had dropped "at the registered
reader"), GO. code-reviewer: NO-GO at nine (the same ls-files and
"coarsest" items, the conftest sha claim, "No torch" and "no committed
evidence" as universals, the landing-test rule, box-dependent skips, the
export test's snapshot commit, the REPORT scorecard pointer), NO-GO at two
(a landing-docstring count, nine against eight for the full phrase; counts
without date and command), NO-GO at one clause ("say so" with the wrong
antecedent), with that clause's fix pre-approved; applied as the fourth
batch with two whitespace-only rewraps, word diff "say so" to "declare
CI-safety or no torch".

Proofs: tests/test_export_public_cut.py over the step-0 README (19 passed, [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
539.27 s); the export tests plus tests/test_harness_doc_claims.py,
tests/test_evidence_bytes.py and tests/test_critic_lane.py over the tree
after each batch (35 passed, 724.89 s; 675.22 s; 1,048.06 s); python
tools/lint_findings.py OK (30); tools/cc/reflect_protocol.py 4 orphans (as
at HEAD) and 25 gaps (21 at HEAD; the four new are the root README's
export-relative glossary links, the known false-positive class); line
endings preserved (LF; ROOT_README.md and CITATION.cff CRLF). Full suite on
the final tree: 770 passed, 5 skipped in 3,822.43 s (python -m pytest -q
-p no:cacheprovider -rs; the five skips are the record's expected five).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 31ce0f9 2026-10-17 docs(memory): log lever 3, the recovered critic folder, three review rounds

````text
The thirty-fifth session's row: the recovered critic folder landed as a selection by the archive's real rule, the two addendum archives on the Desktop awaiting the operator's call, the export-spec footguns measured, the reviewers' three rounds each to GO. The next session picks up lane D (craft) from cc/GOAL.md's owed list.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8a0f44e 2026-10-17 docs(record): land the recovered critic folder of the reviewer's rounds

````text
The critic agent's recompute scripts, outputs and round reports of the
harness era (2026-10-01 to 2026-10-16) survived only in per-session
scratch under Temp; an archive of them with a sha256 manifest was made
on 2026-10-16 outside Temp and outside the repository. This commit
copies that archive into docs/audits/critic-recovered/ through
recover.py beside it (the archive's rule, recovered from the archive,
took the top-level files of four suffixes directly inside critic-named
folders, so this is a selection; what it left behind is named in the
README and was copied to a second archive): 308 of the archive's 309
files laid out as <date>-<session8>/<subpath> under 16 session folders,
the one derived index of 14,915,488 bytes listed and not copied (pool.py
beside it rebuilds it from the committed payloads), home paths scrubbed
to a <user> token (121 files, 248 substitutions; the name is read from
the archive manifest, never written in the script), a lane per file from
its session and the lane commits' times, and two manifests pinning every
byte: MANIFEST.json for the rows the public cut exports and
MANIFEST_WITHHELD.json for the rows it withholds, split so no digest of
a withheld file sits in a public one. The folder is labelled recovered:
the reviewer's scratch as it was left, not an instrument and not a
result; its README says what it establishes and what it does not, and
which rounds of the era left no scratch to recover.

Public cut: the five public-cut lanes' rounds (153 files) review the
withheld export tool, its test and the plan and go with them, as do one
copy of docs/REPORT.md carrying the placeholders the export fills and
one diff hunk of the withheld idea file; the other 153 files are frozen
and exported, fourteen of them with a residue entry (twelve for the
record's own pointer to a withheld idea file, one for the R1 landing
diff whose idea-file hunk the record holds elsewhere, one for a status
line naming the withheld test; a frozen file takes no marker). The
export tool's spec carries the keys, the mention exemptions, the residue
lines and the sweep exclusion, pinned to the public manifest by its
test; its withheld-digest scan no longer registers the empty digest,
which seven empty withheld files had turned into a hit on the OQ-20
driver log's zero-line pip freeze.

Guards: the folder is pinned -text by one glob line (the export test's
real-tree frozen oracle mirrors it by prefix), its session folders left
out of ruff, and all of it left out as a citer of the evidence-bytes
checks 2 to 4 and 6 and of the pins tool (RECOVERED_PREFIXES in both,
held equal by the scope test), since its files quote digests in
whichever form the reviewer hashed. tests/test_critic_recovered.py holds
the folder to its manifests on disk and in the index, with the text
attribute unset on every file, no stray user segment, the lane of every
row re-derived from the manifest's own windows and its cutoff checked
against git where the commit resolves, the README regenerated byte for
byte by gen_readme.py, and the counts consistent; it reads whichever
manifests are present, so it holds in the public clone.

Record: dated notes in the image audit's README (the walkthrough's
second doubt, answered in part), the public-cut plan's item for this
lever (the oracle passes), CHANGELOG.md, README.md and the root README
source; a SHARP_EDGES entry on withheld-name derivation from withhold
keys and on frozen files taking no marker. The S1 reader re-test lane's
rounds postdate the archive and sit in a third copy; landing either
addendum is a separate call.

Proof: recover.py --check rebuilds the folder from the archive with 0
differing bytes; the folder test, the export tool's fixture and
real-tree tests, the evidence-bytes and doc-claims tests and ruff are
green; the critic and a code reviewer each read the diff over three
rounds, the third at GO; the full suite passed on the final tree (770
passed, 5 skipped).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 1e44e0e 2026-10-17 docs(memory): log the S1 reader re-test lane, registered to landed

````text
The thirty-fourth session row: the registration and freeze at 46a812f, the two registered runs, the word K-2-NOT-OVERTURNED-AT-S1 with every reader ABSORBED, the critic's recompute round and the landing at c9649bb; the footguns measured. The next session picks up plan 14.2 item 3, the recovered critic folder lane, then lane D.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c9649bb 2026-10-17 feat(evidence): land the S1 reader re-test, K-2-NOT-OVERTURNED-AT-S1

````text
Both registered runs of the S1 READER RE-TEST REGISTRATION (docs/
BLUEPRINT.md, 2026-10-16) from the clean tree at the freeze commit
46a812f: results/real/readers_s1.json and readers_s1_r.json with their
state files, 36 rows each (the primary resumed at the same HEAD after a
header-only first launch, resumed_cells 0; the replication launched
beside it under the registered rule at 6.1 GB free), and the word
payload results/real/readers_s1_word.json written by
tools/run_reader_s1.py --conclude at the launch HEAD before this commit.
At the S1 gate cell every reader reads ABSORBED (R-N, R-T, R-L; every
D upper below +0.005 on both harvests; no licence to name, no void
reader) and the S1 word is K-2-NOT-OVERTURNED-AT-S1: the registered
reader's S1 kill of 2026-09-06 stands, narrowed at all three readers
to readers outside these families; one more family of readers, not
K-2's universal; the S3 word K-2-ISOLATED does not move. The honest
prediction scored 35 of 36 clauses HELD (the failed one: R-T's
replication median best epoch below 1); no pre-registered surprise
occurred; the three clean-clone gate-cell reruns were identical except
runtime_s.

Record: F-29 with its regime and source lines and its top-table row;
the dated note in F-24's status cell; the K-2 STATUS line in
docs/WHY_THIS_DIES.md; the OQ-17 note; the dated pointer under the
READER-AND-LENS block; the block's OUTCOME with the launch record, the
budget against the estimate, the scoring and the shapes of each D;
pointers in README, docs/REPORT.md, docs/FINDINGS_INDEX.md (row, arc
section, counts), docs/GLOSSARY.md (the K-2 row and the word's entry),
CHANGELOG.md; docs/BLUEPRINT_INDEX.md's Line column regenerated by
title. Code: tests/test_reader_s1_landing.py (fails, never skips, on
missing evidence; pins both instruments' shas, the payloads' and state
files' shas, the labels, the licences, the word, the pairing checks,
the R-N scale constants and the gate margins), tests/conftest.py (the
S1 pair and the twin payloads join the data-root fixture);
tools/run_reader_s1.py joins the frozen closure (pyproject
extend-exclude; seventeen files, fourteen attested, in CLAUDE.md,
docs/CONVENTIONS.md, docs/SHARP_EDGES.md, docs/TASK_RECIPES.md);
tests/evidence_pins.json regenerated.

Gated: the critic's recompute round (Opus) re-derived every readout,
label and the word from the state files at a maximum difference of
0.0 over 342 numbers and returned NO-GO on three wording objections,
all applied by regenerating the texts (the signed clause-(6)
differences; the mechanism caveat; the index paragraph's kill
sentence) with its advisories, recorded in a dated line under the
OUTCOME; landing texts generated
through a number registry and checked against the diff's added lines;
findings lint OK; full suite green on this tree. No frozen tool,
payload, state file or registered text changed; registered text
appended only.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 46a812f 2026-10-16 feat(registration): freeze the S1 reader re-test and its rider

````text
Registers, before any reader-variant cell at S1 trains, a run of the
frozen reader-lens instrument's s1 stage under the three F-28 readers
(hz-rescaled, two-tower, longer budget) at the S1 gate cell on both
committed S1 harvests: lever 1 of docs/PUBLIC_CUT_PLAN.md section 14.2, [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
the record's named path to overturn the F-24 kill at S1, decided by the
operator on 2026-10-16. A new registration, not an amendment of the
reader-and-lens block, whose conditional S1 stage stays unrun and whose
S3 word does not move. CRITERION-BEARING for K-2's status at S1 and
F-24's S1 cells through the pinned consequences; the prediction (ABSORBED
modal per reader, K-2-NOT-OVERTURNED-AT-S1 modal) and every branch pinned
before any read; a pre-freeze smoke of one committed-type R-0 cell
disclosed (CPU matches the CUDA row to 8e-5; CPU/CUDA 1.217).

Record: the S1 READER RE-TEST REGISTRATION block appended at the end of
docs/BLUEPRINT.md with its index row; the F-24 dated note; the CHANGELOG
section. Code: tools/run_reader_s1.py (imports the frozen tool by bare
name, asserts its raw-byte digest at import and before any conclusion,
refuses any reader set but the registered three in order, issues the S1
word from the frozen labels, records the pairing checks) and
tests/test_reader_s1.py (every word branch, the conclude flow on fake
payloads, every refusal, the import-time assertion in a fresh
interpreter); their -text pins and the HAND_PINNED entry. Lever 2, the
rider: docs/audits/2026-10-16-f24-support/, three committed scripts and
outputs regenerating F-24's three support figures with header pins set
before the rerun, every pin holding (the cross-seed collapse and the
same-subtrahend control; the position-only predictor equal to the floor
at every anchor index on both primaries; the S1 per-anchor input norms
with the hot counts). The docs refresh (a sharp-edge entry on dating a
registration from the box clock, a conventions note on test-fixture
imports and the two audit-folder output forms, a pending closure
instance, one memory row).

Gated: critic design round NO-GO on five blocking objections (recompute
discrepancy 5.6e-16 on the rider), confirmation round NO-GO on two
one-line items, third round GO; code review REQUEST CHANGES with one
block, every finding applied; docs refresh; full suite green on this
tree after two post-GO edits named in the block: the instrument's and
the rider scripts' docstrings no longer name a file the public cut
withholds (the export's real-tree scan flagged the first full run), and
the lane-C session row of ESPALIER_MEMORY.md has its one quoted
deny-list word scrubbed under a dated bracket (that row was written
after the previous session's suite ran; the operator may reinstate the
word by a decided entry). No frozen tool, payload, state file or
registered text changed; no label moved. The registered runs launch
from the clean tree at this commit.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f692032 2026-10-16 docs(memory): log lane C, the three reviews, the science-lever plan

````text
The thirty-third session's row: lane C of the image audit landed at ff0aa4b with plan section 14 at 5d1598c; the critic, code and failure-mode reviews and the one fix batch; the full suite and the Linux clone; the counting and digest lessons. The next session picks up the S1 stronger-reader re-test lane with its rider, then the recovered critic folder, then lane D.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## ff0aa4b 2026-10-16 test(guards): lane C of the image audit, guards as strong as their names

````text
Section C of the 2026-10-15 image audit found guards weaker than their
names. Each fix is test-side or in an editable tool; no frozen tool,
payload, state file or registered text changed, and no label moved.

- The findings lint reads a wrapped `- source:` bullet whole; it had
  read only the first physical line, so the paths on continuation lines
  were never checked (nine more now, counted by its own parser).
- An absolute evidence-citation pin: tools/evidence_pins.py lists every
  cited digest that resolves to a tracked file (tests/evidence_pins.json)
  and check 6 of tests/test_evidence_bytes.py compares a fresh scan with
  it, so a committed hand-edit of cited evidence fails without a HEAD
  comparison. Two files became sha-cited and gained their `-text` line.
- tests/test_fullfree_landing.py pins F-24's landed labels, gate rows and
  provenance and attests tools/run_fullfree.py to its freeze-commit blob.
- The twin, rider-diagnostic and positive-control verdicts are pinned as
  landed instead of accepted from a set.
- A Stage-I positive control on the sign of the criterion and its MSE
  identity, and a null control on magnitude (the bootstrap undercovers at
  the synthetic sizes, so a null root can read CI-clear; the comment says
  so).
- A D-6 test: the sidecar policy at beta zero stays paired with policy
  none at the same seed while reading telemetry every block.
- A one-hot run_block index test; the spec_step tautology pinned to its
  seed-24 draws; the selection key called from tools/run_error_predictor
  instead of re-typed; both lens builders pinned by digest.
- A per-script --smoke root fix: experiments/_util.py smoke_results()
  routes every save to results/smoke/, every script and run_all.py call
  it, and save_json writes LF on every OS.
- The sharp-variant cached-vs-uncached asserts restored (dropped on
  2026-08-30); weights_only on the adapter load.
- tools/export_public_cut.py and its hook pipeline fold a doubled leading [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  slash after the scheme strip (the file://// gap lane A's Linux proof
  found); the tool's digest moves, which the receipt form of 2026-10-14
  allows without a receipt beside it.
- CITATION.cff's abstract carries a dated forward pointer to F-24; dated
  closing lines in docs/RELEASE_NOTES.md, docs/SHARP_EDGES.md and the
  audit report; CHANGELOG.

Proof: every step's targeted tests; the export tests (19 passed); the
GPU class of tests/test_tools_and_real.py on this box (4 passed); the
findings lint (29 findings OK); ruff clean over the lane's Python; the
full suite with BLAS threads capped (748 passed, 5 skipped, 27:10; the
run before it read one vocabulary hit in a docstring, fixed by one
word); a fresh Linux clone
(python:3.12, numpy 2.5.4, no torch) green on the lane's targets (258
passed, 20 skipped for torch, scipy and the real extras) with one
experiment's --smoke run leaving the committed payload untouched;
three reviewers (critic in diff mode, code, failure-mode) read the
diff and their accepted findings landed as one batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5d1598c 2026-10-16 docs(plan): section 14, the science levers decided on 2026-10-16

````text
docs/PUBLIC_CUT_PLAN.md gains a fifth dated amendment recording the [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
operator's decisions of 2026-10-16, taken after lane B of the image
audit landed. The public cut stays as sections 1 to 13 leave it: the
full tree with marked redactions, a fresh history with the scrubbed
commit log, the withhold list unchanged. Publishing the private history
itself was weighed and declined; the section records what it would have
bought (a consistent, unsigned, self-dated chain) and what it would have
cost (the sibling material in the withheld files, the ECOSYSTEM
sections and the commit messages that name a private repository), with
the command beside each count.

Four levers from the researcher walkthrough's five doubts become lanes:
an S1 stronger-reader re-test (registered, criterion-bearing for the
K-2 word at S1), the three F-24 support numbers regenerated as
committed artifacts (its rider), a recovered folder of the critic
reports surviving in the author's scratch (the harness era only), and
the private history as a git bundle deposited with restricted access
beside the Zenodo data deposit, its sha256 published and the v1.0.0 tag
signed. The outside half of the reviewer doubt stays the operator's
action. Lane order and cost estimates are written as estimates.

Proof: the section's three oracles print their "now" values; the
export tool's home-path and tone patterns find nothing in the section;
the file is withheld from the public cut by section 3, so the private
names it quotes stay private.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 1cbb736 2026-10-16 docs(memory): log lane B, the three reviews, the F-28 coverage bound

````text
The thirty-second session row records the record errata batch (c2b45ff), the three reviewers' findings and the one fix batch, the full-suite and Linux-clone proofs, and the F-28 RN-at-L1 bound the critic found; two SHARP_EDGES entries record the line-citation shift and the typed-count trap. The next session picks up lane C (guards, the hook gap, the tie-break test).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c2b45ff 2026-10-16 docs(record): lane B, the record errata batch after the 2026-10-15 image audit

````text
The HF adapter has cropped KV caches by default since b1dae57 (2026-08-29);
fifteen statements in twelve files said it recomputes prefixes. Each now
carries a dated note (true when written: DECISIONS D-9, CLAUDE.md,
WHY_THIS_DIES, BLUEPRINT Phase 5, the critic agent) or a dated erratum
(false when written: GLOSSARY, REPORT, RELEASE_NOTES, ECONOMICS, NOISE_FLOOR,
WHY_THIS_DIES K-5 status) pointing at D-9's dated note, which restates the
wall-clock ban on its real ground: nothing here is a benchmark harness, and
logged runtimes are provenance. CLAUDE.md's bullet and the critic's rule 7
now state the current rule first with the old clause marked superseded;
METHOD's quotation of the old rule carries a pointer. README's three
front-door sentences and docs/public_cut/ROOT_README.md are corrected in [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
place (every speedup figure the record quotes is prior art's).

Dated notes, numbers generated from the committed outputs by script:
- F-24 (iii), F-25's S1 L2 deciding row, F-28, README: every probe interval
  is conditional on the three trained seeds; the audit's three seed-inclusive
  brackets cover 72 rows of F-24, its twin and F-25 (F-28 is not bracketed);
  no label moves; three readings and one descriptive value are seed-sensitive;
  BLUEPRINT's "the train seed only shuffles batch order" gets a dated erratum.
- F-21: the live Stage-C heads ran without a support clip; a counterfactual
  TRAIN-support clip changes 41 / 41 of 17,185 / 17,616 consulted decisions;
  pointers from F-22 (iii), F-27's replay line, BLUEPRINT and the glossary.
- stats.py docstring, METHOD, NOISE_FLOOR, F-24, F-28: the percentile cluster
  bootstrap covers 0.897 / 0.939 / 0.948 at 10 / 30 / 60 clusters; the nearest
  label-deciding bound is F-28's RN at L1 replication gate upper +0.004951,
  which a t-for-z correction carries to +0.005026, NOT-SHOWN by the frozen
  rule; the registered estimator stands and K-2-ISOLATED does not change.
- F-4: the offset-1 sign at rho 0.6 is seed noise over ten seeds; F-9: the
  bonus token is unpriced, the 0.162 budget about a quarter high; a dated
  clause on the F-3, F-4, F-5 and F-6 regime lines names the argmax mechanism
  (pipeline.py's docstring now says which default is whose); D-10 gains a
  dated note.
- Stale counts, each re-measured by command: 80 path-bearing payloads (30
  written), 734 tests in 47 files, 29 findings, 41 tools, the per-script
  smoke flag, batch 10 in the fidelity calibration, the git helpers' two
  meanings of -dirty (12 tracked-only against 4 untracked-counting copies in
  tools/run_*.py; 20 against 13 call sites tree-wide), CONVENTIONS' docstring
  counts; the F-26 summary row levelled.
- BLUEPRINT: a front-matter note defining the document's voices; forward
  pointers under the premise, the two bold EXISTENCE outcomes and the two
  Phase-3 verdict lines; errata at the R1 entropy tolerance, the P1 header
  and the SPEED-Bench attribute; the operator's three calls of 2026-10-16
  recorded (the two PC-2 lines kept with dated notes and a dated line in the
  plan's section 13; the OQ-20 command paths kept under RELEASE_NOTES 3.1 as
  extended; README gains the registration-order sentence). BLUEPRINT_INDEX's
  Line column and METHOD's BLUEPRINT line citations regenerated after the
  insertions; tests/test_record_claims.py pins the index rows to their
  lines, run_simulation's argmax default and the adapter's KV-cache default.

Evidence: docs/audits/2026-10-15-image-audit/ holds the scrubbed audit
report and the recompute scripts whose numbers entered the record; each
asserts its pinned figures, records the numpy version and was rerun from
the committed tree before this commit (seed_var to 1e-12, coverage 3756 of
4000 hits, f4 and e07 reproducing their payloads, the two replays identical
to the audit's run). docs/LESSONS.md closes the lane with one entry per
limitation that stays in the evidence and names where the tree does not yet
follow each rule. Three reviewers (critic in recompute mode, code-reviewer,
failure-mode reviewer) read the first draft; their blockers, all wording and
count errors, landed as one batch. No frozen instrument, payload, state file
or experiment script changed; no label moved.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 82bc72d 2026-10-16 docs(memory): log lane A, the Linux proof and the thread thrash

````text
The row records lane A's landing at c41f9f1, the three Docker proof rounds that found the seventh red test and the pre-push hook's four-slash gap, the two reviews, and the capped full run; the sharp-edge entry records the BLAS thread thrash measured today. The next session picks up lane B, the record errata batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c41f9f1 2026-10-16 test: make the suite green on a Linux clone without torch

````text
Six landing tests read committed payloads' Windows path strings back
through POSIX Path().name and failed on Linux. Two now take the basename
with PureWindowsPath, and the three reader-lens landing tests give the
frozen conclude_from a data root, a new tests/conftest.py session
fixture, in which the recorded Phase-3 paths resolve by the tool's own
rule on any OS, each copy bound to the sha256 its payload records. The
module-level torch import-or-skip in tests/test_reader_lens.py hid 21
torch-free tests wherever torch is absent; it becomes a per-test skip on
the five that need torch, with a dated amendment of the file's sha12 pin
in the reader-and-lens registration block. The class-level torch gate in
tests/test_probes.py moves onto the one method that trains. The export
tool's test built a four-slash file URL on POSIX that git accepts and
the pre-push hook admits; it now builds the URL with one leading slash,
feeds the upper-cased local path to the hook directly on every OS, and
the hook's gap is recorded in docs/SHARP_EDGES.md for a later change.
Dated notes in docs/CONVENTIONS.md and the test-suite task pack record
that a conftest now exists. No frozen tool, payload or state file
changes.

Proved on this box (726 passed, 5 skipped) and in a fresh Linux clone
with Python 3.12 and the dev extras only, where the seven target files
went from six failures and a skipped module at HEAD to green, and the
export test file passes.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## a88e0d1 2026-10-15 docs(memory): log the image audit and the approved lanes A to D

````text
The row records the 39-agent read-only audit (375 findings, 45 refuted, 4 high / 41 medium survivors, zero committed labels overturned), the verified KV-crop wording gap and the operator-approved plan; the next session opens lane A (the six Linux-red tests and the torch importorskip) through /implement-task --multi before the private push.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 4c6b043 2026-10-15 docs(memory): log lane 2 of the batch, five critic reads, git as the frozen-set oracle

````text
The row records lane 2's landing at 5c264b0, the four fix batches and five critic reads, the proofs on the final bytes and the post-commit staging re-export; the next session picks up the surveys, the packer and the DOI before the one pinned export.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5c264b0 2026-10-15 feat(public-cut): lane 2 lands the tool, the allowlist and the record

````text
Lane 2 of the 2026-10-14 decision batch, calls PC-1, PC-2, PC-3, PC-6,
PC-9 and PC-10. docs/PUBLIC_CUT_PLAN.md section 13 records the ten calls [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
and was written first in the lane. The export tool: a repeatable
--author whose entries become the CITATION authors block,
docs/public_cut/identity.json as the default for every identity [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
parameter a flag leaves pending and for the export commit's git
identity, an author's mailbox allowed on the CITATION.cff files only;
the 2026-10-10 memory row's third assessment sentence withheld under a
marker, the 2026-10-11 row's deny-list match kept by a decided entry,
two probes against the withheld sentence recurring, a decision covering
one line; the nine gaps of plan 12.5 and 12.7 closed, the frozen set
taken from git check-attr itself over the tree's attribute files; scan
refuses an export made by another tool revision. The allowlist's three
flagged comments record the call; the binding gate's refusal carries a
two-form hint (drift or a larger mismatch); the three test wordings
handed over by lane 1; dated notes in BLUEPRINT (Flag C),
OPEN_QUESTIONS and GLOSSARY (OQ-7 TRANSFERRED to amber/), CLAUDE.md and
CONVENTIONS (main), TASK_RECIPES and SHARP_EDGES (the export policy,
the sweep, the attribute lines); the ROOT_README wall-clock sentence
reworded.

No pinned export and no receipt in this lane (plan 13.4, the operator's
confirmation of 2026-10-15); the pinned export moves to the final
source commit. Proofs: CHANGELOG.md's lane-2 entry and plan 13.5; the
export test file, the five snapshot test files, the full suite and the
preflight run in the handoff's memory row. Reviews: sideband-critic
(diff mode with recompute, four reads and a clearing re-read),
failure-mode reviewer, code reviewer; four fix batches.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 10050ec 2026-10-15 docs(memory): log the decision batch, lane 1, the thread-count mechanism, TP-1

````text
The row records the ten PC- calls, lane 1's landing at 51ceb9c with the measured BLAS thread-count mechanism, the seven reviews and the final document-test run, and TP-1 at 49c55ad; the next session picks up lane 2 (tool, allowlist, docs, plan section 13), exporting from committed sources only.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 49c55ad 2026-10-15 docs(task-pack): TP-1 test-suite speed, measure then tier, parallelise and cache

````text
A Kind: PACK blueprint with its runbook, force-added past the harness rule that ignores
task-packs/* (f1aabe4): Task 0 measures (serial --durations=0; a scratch-venv parallel
feasibility run twice plus a one-thread variant) and can drop any lever or end the pack;
levers are a slow marker and a quick tier for lane proofs, pytest-xdist with loadfile
distribution, cached reads in tests/test_evidence_bytes.py, the export file by measurement,
the public workflow line only after a parallel pass, and four lane-practice lines. No
registered recompute is cheapened. scope-check exit 0 with the homonym gaps acknowledged.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 51ceb9c 2026-10-15 test(gates): receipts bind at their source commit; freeze recompute in a fresh process (PC-4, PC-5)

````text
Lane 1 of the 2026-10-14 public-cut decision batch (ten operator calls PC-1..PC-10,
in session memory until plan section 13 lands with lane 2).

tests/test_evidence_bytes.py (PC-4): the export tool's proof receipts are no
longer citers of check 4, so an uncommitted edit to tools/export_public_cut.py [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
or docs/public_cut/tone_allowlist.txt no longer reds the suite (the "receipt [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
lock" of plan 12.7). A fifth check binds each tracked .json receipt at the
commit it names: unchanged from HEAD's copy once CRLF is folded, parsed, a
40-hex source_commit that is an ancestor of HEAD, every string under a
sha256-named key a 64-lowercase-hex digest of the file the key names at that
commit (tool, allowlist) as stored or LF-folded, no receipt tracked at HEAD
missing from the tree or disk. A digest naming bytes no commit holds is refused
with the remedy in the message. Given up, by that call: a committed tool edit
no longer needs a receipt beside it.

tests/test_outcome_head.py (PC-5): test_stage_c_freeze_end_to_end runs the
stage-C freeze recompute and the tampered-summary refusal in a fresh
interpreter, the tool's real contract. No gate change, no numpy pin.

Mechanism of plan 12.7's numpy 2.4.6 refusal, measured: tools/run_noise_floor.py
setdefaults OMP/OPENBLAS/MKL_NUM_THREADS=2 at import, pulled in at collection by
four module-level imports after numpy's OpenBLAS loaded at 24 threads; under
numpy 2.4.6 (OpenBLAS 0.3.31.188.0) the stage-I delta_noise differs by
2.527492104498208e-15 between 2 and 24 threads, the refusal's two values bit for
bit; under 2.3.5 (OpenBLAS 0.3.30) identical at both.

Validation: a fresh clone under numpy 2.4.6, full suite 667 passed, 34 skipped,
exit 0 (first-form tests). This box, final code bytes, numpy 2.3.5: 721 passed,
5 skipped, exit 0. Controls in a scratch clone: fifteen runs over thirteen
states and a further four, every exit as expected.

Docs: docs/SHARP_EDGES.md (EVID-1 update; a new thread-count entry),
docs/REPRODUCE.md section 4 dated note, docs/TASK_RECIPES.md seventh note,
docs/PUBLIC_CUT_PLAN.md 12.7 dated note, CHANGELOG.md gates-lane entry. [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]

Reviews: sideband-critic diff mode (five reads, the last two GO) and the
failure-mode reviewer, both opus; every number in the record traced to a log.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b924585 2026-10-14 docs(memory): log the front-doors lane, ten critic reads, numpy separation

````text
The session row records the front-doors lane landed at d481935 (README front door, root README revision, glossary label entries, the licence-oracle fix, the CHANGELOG entry and the plan 12.7 note), its four critic rounds and six re-reads, every proof run with its numbers, and the numpy separation (2.4.6 reproduces the binding-gate refusal, 2.3.5 does not). The next session picks up the lockstep and amber surveys (plan 10.3), then the post; the operator's calls and the push stay open.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d481935 2026-10-14 docs(public-cut): front doors, glossary labels, licence oracle fix

````text
The front-doors lane of the public cut (plan 12.6's next step).
README.md gains a front door above its unchanged status page (+85
lines, a pure insertion): the question, the negative answer at the
registered reader's pinned L1 and L2 cells (L3 open at both sources), a
three-row scorecard whose labels link to docs/GLOSSARY.md, the two
NON-CRITERION side results, how to check a number without a GPU, how to
read the record and what a clone cannot reproduce; the 2026-09-05
opening moves verbatim under "The question in full" and everything from
"Status at a glance" on is byte-identical, every dated note included.

docs/public_cut/ROOT_README.md (+133 -50): a plain abstract on top, the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
export-provenance paragraph moved verbatim below the three parts, a
kill-criteria paragraph, sideband's "Reusable on its own" list and
glossary links on the labels; the provenance comment extended; three
pieces of its committed text rewritten (the folder-table sideband row
scoped to S1, the side-results paragraph re-wrapped with two label
parentheticals, two sentences reading "absorbs" as a mechanism
reworded).

docs/GLOSSARY.md (+44 -3): fifteen headed entries for the record's
labels, each stating its registered rule, every number copied from
FINDINGS.md, docs/WHY_THIS_DIES.md or the registration in
docs/BLUEPRINT.md; a dated header note; dated clauses on the K-2 row,
the Finding (F-N) entry and the Mega-group lens entry through F-28.

tests/test_export_public_cut.py: the real-tree oracle on the Llama 3.2 [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
licence copy compares the snapshot commit's blob, not the worktree copy
(CRLF in a fresh autocrlf clone, LF in the blob): 1 failed, 13 passed
in such a clone before the fix; 14 passed on the box and 14 passed in
a fresh clone after it.

Proofs: real-tree export tests over each README draft (3 passed, twice),
the whole export test file, 14 passed in each of seven logged runs
(three fix batches on the box and in a fresh clone, the fourth in a
clone) and the fourth batch's file again inside the full suite, the
landing-text number tracer at zero unknown numbers on every file, no
tone-sweep hit, no allowlist edit; four critic rounds (NO-GO at 8, 2 and
2 blockers, then GO, 0 numeric discrepancies) and diff-mode re-reads of
the advisory edits and the records; the full suite on the tree with the
four files as they stood after the advisory edits: 720 passed, 5 skipped
in 4,335.76 s, exit 0 (after it, documentation only: one word in the
root README's abstract and the two records below, with the touched-file
tests re-run on the final bytes, 105 passed, 1 skipped); preflight's
full suite on the final bytes: 720 passed, 5 skipped in 5,031.20 s,
exit 0.

CHANGELOG.md carries the entry; plan 12.7 gains a dated note recording
the numpy separation it named (the staging export's full suite in two
fresh clones: 1 failed, 651 passed, 34 skipped under numpy 2.4.6, the
binding gate's SystemExit; 652 passed, 34 skipped under numpy 2.3.5).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 304559f 2026-10-13 docs(memory): log commit B, the test amendment, twelve critic rounds

````text
The row records commit B's pinned export, its failed proof, the red first suite and the FOLDED_CITERS amendment, the second green suite and the landing at 977ff11. The next session picks up the front-doors lane; the operator calls are listed in cc/GOAL.md.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 977ff11 2026-10-13 docs(public-cut): land the pinned export and its fresh-clone proof

````text
Plan 10.8 step 3, commit B (sections 12.6 and 12.7): the staging export
written from this commit's parent, 2 commits after commit A, without
worktree sources (805 files, verdict NO-GO with 28 blockers; the
allowlist-stale, sources and tool classes of the worktree export gone),
scan exit 2, the fresh-clone proof (1 failed, 651 passed, 34 skipped;
result FAILED, exit 2; the binding-gate refusal of the last proof
recurred), the receipt under docs/public_cut/proofs/, plan 12.7 and the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
CHANGELOG entry generated by a session script from the sources 12.7
names, its carried literals named in 12.7; tests/test_evidence_bytes.py
gains a dated exemption for files cited only by the export receipts by
their LF-folded sha256 (an attribute pin for the withheld tool and
allowlist is refused at export, breaks the frozen-set oracle, or hides
the name), held to the fold instead, flagged for the operator in 12.7
with an eighth and a ninth tool gap. The seven gaps of 12.5 untouched.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## a0a4d30 2026-10-13 docs(memory): log the export-tool lane, ten critic rounds, commit B next

````text
The row records commit A of the export tool (3e7b744), the review history, the suite on an untouched tree and the tree-guard footgun (f45fd0f). The next session picks up commit B: the pinned export at the landing commit, its hour-long proof, plan 12.7 and the receipt.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f45fd0f 2026-10-13 docs(sharp-edges): tree guard trips when a record file moves mid-suite

````text
The registered instruments hash HEAD and the tracked status at the start
of a run and refuse to write when either differs at the end. Reverting
or regenerating a tracked record file while the full suite runs makes
the shift-rule guard test of tests/test_prefetch_horizon.py fail with
the tree-changed message although it passes alone. Measured today: one
failure and 719 passes with a revert inside the run, 720 passes on the
untouched tree. The entry names the symptom, the cause and the proof.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 3e7b744 2026-10-13 feat(public-cut): export tool for the three-folder public cut

````text
tools/export_public_cut.py writes the public layout from a pinned [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
commit: raw blobs through one git cat-file batch into a fresh-history
repository (autocrlf off, forced add, blob ids checked), the withhold
list applied whole and by unique anchor with [withheld: ...] markers,
a mention rule for the withheld names, placeholder fills, generated
WITHHELD.md and docs/COMMIT_LOG.md (bodies withheld by a deny list),
and a scan (secret shapes, home-directory paths, withheld and private
names, withheld digests, the tone sweep against a reviewed allowlist,
the [pending: class, record lines flagged for the operator with
reasoned keeps published without their text, stale spec entries). The
verdict is separate from the write (exit 2 for a NO-GO under --ship or
scan, 3 for a refusal); the manifest carries a sha256 per file; a
re-run refuses a hand edit, a foreign file, a remote or push record, a
commit or ref beyond the export and a repository that is gone; the
commit identity is pinned; a pre-push seat-belt needs a GO manifest, a
gate stamp from scan and a proof stamp from prove, and strips any
credential before recording a push. prove clones the export, builds a
venv with the analysis extra, runs the suite, the lint, the smoke, the
README worked example, the amber blob check and the evidence-bytes
test, and writes a qualified receipt; only an exact PASSED stamps.
This is the first of two landings: the pinned export at this commit
and its fresh-clone proof follow.

Sources under docs/public_cut/: LICENSE (MIT), NOTICE, CITATION.cff, [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
the root workflow, the tone allowlist with reasons, the two Llama
licence texts, and the FAILED receipt of the fresh-clone proof of a
staging export (seven failures: four tests needing scipy, two
subfolder path checks, one binding-gate refusal in the full run only).
Test-only fixes for the first two classes: tests/test_balanced_groups.py
skips the Fiedler tests without scipy unless SIDEBAND_REQUIRE_ANALYSIS
is set; tests/test_evidence_bytes.py prefixes top-level git paths from
a subfolder. Dated notes in docs/DECODE_CONTRACTS.md (plan 10.4, every
id re-derived) and docs/THIRD_PARTY.md (two probe-weight files ship).
Plan section 12 records the design calls, errata, open calls and
oracles; CHANGELOG, SHARP_EDGES, TASK_RECIPES, CONVENTIONS, the root
README source and the pyproject comment are updated.

Proved by tests/test_export_public_cut.py (a fixture repository with [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
one file per case, a clean fixture that reaches GO and a stamped push,
hook and normaliser twin tests, prove run to a verdict with faked
stages, and real-tree tests on a worktree snapshot), the three-file
suite, the full suite, and the critic's recomputation of every count
in section 12 to zero discrepancy.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 7106d06 2026-10-12 docs(memory): log the root README lane, its four critic rounds and the parallel lane

````text
The twenty-fourth session's row: the README source landed in tree at c7f8999 under plan section 11 (MIT for the whole release), four critic rounds and their lessons, the temporary-index commit beside a parallel dashboard lane. Next session picks up plan 10.8 step 3, the export tool.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c7f8999 2026-10-12 docs(public-cut): root README draft in tree, plan section 11, MIT for the release

````text
docs/public_cut/ROOT_README.md: the source of the public specdec-sidechannels [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
root README (plan 10.6), 327 lines drafted from the record as read on
2026-10-12: the question and the answer in the record's words per layer and
source, open and unrun cells named; the three folders and what each found,
nulls and errata included; how the work was run, with the exceptions the
record names; what is reusable; the one-second check from
docs/RELEASE_NOTES.md section 7; the two re-run modes; what is not in the
repository; licence and citation. The amber and lockstep sections are
pre-survey skeletons under a [pending: ...] marker (5 occurrences of the
form, one in the provenance comment the export strips).

docs/PUBLIC_CUT_PLAN.md section 11, the second 2026-10-12 amendment: MIT for [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
the whole release, all three folders, code, documents and results (the
operator's call); the README source in tree and withheld; [pending: as a
placeholder class the export refuses; the staging folder renamed to
specdec-sidechannels; the README's worked example and the amber blob-id
check added to the fresh-clone proof; the per-folder commit-log question
given to the surveys; oracles. Sections 1 to 10 unchanged.

CHANGELOG.md: the section for this landing with the four critic rounds
(diff mode: NO-GO with 10 blockers, NO-GO with 2, GO with 9 advisories, GO
with 2; every blocker after round one a sentence written to fix the previous
round). Provenance check of the draft: 91 distinct numeric literals verbatim
in the named sources, the 10.9 hype sweep at 0 lines, every cited path
present. Full suite 706 passed, 5 skipped, twice: after the fix batch (1:14:52) and at the preflight run (1:31:31). No code, evidence, registration block or
finding changed; no GPU.

Staged by exact blob: a parallel session's findings-dashboard additions to
the same two files (plan section 12, a README section) stay in the working
tree for that lane's own critic, test and commit.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 0e6e948 2026-10-12 docs(memory): log the critic notes, the trio decision and the next step

````text
The row records the two landings (48c9fc3 the dated notes, 75de9a0 the
plan amendment), the operator's decisions of the day (the trio public
under the hype-strip condition, one repository named
specdec-sidechannels, no PyPI, a Zenodo deposit for the raw harvests),
the five critic rounds and their lesson, the export-tool inputs found,
and the next step: the root README draft, then the export tool.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 75de9a0 2026-10-12 docs(plan): amend the public cut to the trio under one project name

````text
Section 10 of the public-cut plan records the operator's decisions of
2026-10-12 as a dated amendment; sections 1 to 9 are unchanged.

- The three repositories go public, on the condition that hype,
  brainstorming, forks and product material are stripped; the reason
  and the superseded sentences are named.
- The project is one repository, specdec-sidechannels (free on
  GitHub), with a root README and the three sub-repositories as
  folders; the package names stay; no PyPI anywhere.
- The hype sweep becomes an export gate, its exact command pinned
  (46, 12 and 49 lines on the three trees today); lockstep's first-cut
  withhold list; amber's front door rewritten; one survey session per
  sibling before its export.
- Item 5 dissolves into a dated DECODE_CONTRACTS line: the 197 amber
  rows resolve by blob id inside the repository; the 16 lockstep rows
  are handled file by file, including the one cited blob that moved
  between the cited and the parked commit.
- The raw harvests go to a Zenodo deposit; the root README's outline;
  the export tool parameterised by sub-repository; the order of work.

Proof: the same five critic passes as the companion commit (the two
round-one blockers were in this section and are fixed), findings lint
and ruff clean, espalier audit and integrity clean, the full suite
706 passed and 5 skipped in one run after the last batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 48c9fc3 2026-10-12 docs(record): dated notes for the critic advisories left standing

````text
The critic rounds that gated yesterday's landing left seven advisories
on pre-existing record text. Each is now a dated note; no sentence was
rewritten.

- README.md: the existence row's "about +0.003" gains the four F-24 Mt
  values and F-24's "+0.003 or less", a three-place rounding; its F-16
  and F-18 sentence gains the findings' dated moot notes, quoted; the
  2026-10-11 sub-line says what "that family" is (the three F-28
  readers; the registered reader ran in F-24, F-25 and F-28's STAGE
  LENS); the "27 entries" line gains the lint's 29, F-0..F-28; the
  "Close on F-23" bullet gains a note that it predates F-24 and points
  at the one-line reading's dated note; the 2026-10-11 check note
  records the row's two new clauses.
- OPEN_QUESTIONS.md: the OQ-19 header gains "SKIPPED (operator,
  2026-10-11; dated note at the end of the entry)".
- docs/THIRD_PARTY.md: a dated disclosure that no harvest meta records
  a checkpoint revision, where the record pins snapshots instead, and
  that the harvested revisions are inferred from the one-snapshot
  caches, with the cache and git-entry dates.
- CHANGELOG.md: the entry for this landing and its companion commit.

No code behaviour, evidence, registration block or finding changed;
no GPU.

Proof: five sideband-critic passes in diff mode over this diff and the
companion plan amendment (two blockers in the amendment and one date
and one count in these notes, each fixed as one sentence; the fifth
pass GO with nothing advisory), targeted tests green after each batch,
findings lint and ruff clean, espalier audit and integrity clean, the
full suite 706 passed and 5 skipped in one run after the last batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 14e2f3e 2026-10-12 docs(memory): log the section-5 landing and its five critic rounds

````text
The row records the four record lines landed at 929493a, the critic
rounds that gated them, the export-tool notes owed to the public-cut
plan's section 6, and the next step: item 5 on the operator's word,
then the export tool. The CHANGELOG section header takes the landing
commit's date (the notes were written before midnight, the commit
landed after it).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 929493a 2026-10-12 docs(record): dated lines owed before the public cut, items 1 to 4

````text
The public-cut plan's section 5 owes the private record five dated
lines before the export; this lands the first four, as dated notes,
never rewrites.

- docs/ECOSYSTEM.md: the amber and lockstep entries each name the two
  as the commercial branches of this research, both private (amber's
  record last moved at 69b437c, lockstep parked at cdfe0b3).
- OQ-19 is skipped by the operator's decision: dated notes in
  OPEN_QUESTIONS.md, docs/OQ19_ORACLE_CEILING_DRAFT.md, the DRAFT banner
  of tools/run_fullfree_oracle.py, docs/GLOSSARY.md's row and
  docs/BLUEPRINT.md's reader-lane close. DRAFT_UNFROZEN stays True and
  its test is unchanged.
- docs/THIRD_PARTY.md: the OLMoE row names Apache 2.0 from the model
  card at snapshot b89a7c4; its stale ECOSYSTEM line-range pointer to
  the Llama gate note gains a dated correction.
- README.md: the status table checked against FINDINGS.md through
  F-28 (every number present, no row changed); two paragraphs below
  it written on 2026-09-05 gained dated notes because F-24 overturned
  them.
- CHANGELOG.md: the entry for this landing.

Item 5 (docs/DECODE_CONTRACTS.md's private sources) waits on the
operator's call. No code behaviour, evidence, registration block or
finding changed; no GPU.

Proof: five sideband-critic passes in diff mode (the first found the
two README paragraphs; the next three each blocked one sentence
written to fix the last; the fifth GO), targeted tests green after
each batch, findings lint and ruff clean, espalier audit and integrity
clean, the full suite 706 passed and 5 skipped in one run after the
last batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 7d6c6b8 2026-10-11 docs(memory): log the public-cut scoping and its locked plan

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## d64b0e7 2026-10-11 docs(plan): lock the public-cut plan of record

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## 58ff002 2026-10-11 docs(memory): log the record-lines landing and the write-up entry point

````text
The row records the twenty-first session: the last pre-write-up step of the settled order landed at 5dc6318 (dated notes on PRIOR_ART, REPORT, GLOSSARY, ECOSYSTEM; four critic passes to GO), with the lessons on stale index entries after a revert and on new sentences being new claims. The next session picks up the write-up itself, with the operator's calls on its main piece, its location, OQ-7's status word, LICENSE and marin #7183.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5dc6318 2026-10-11 docs(record): dated lines on the amber/lockstep harvest claims

````text
Sideband's own sentences that the 2026-10-09 review of the sibling
repositories showed wrong now carry dated correction notes; nothing is
rewritten. This closes the last pre-write-up step of the settled order
(amber's errata, then lockstep's, then these lines).

docs/PRIOR_ART.md, the OQ-7 cell: (a) US 12,547,833's granted
independent claims require a last-token replacement, which claim 1
recites as lossy, and no claim names the decoder's LLM, so "the
symmetric version is claimed" is withdrawn; (b) PMATIC is arXiv
2601.10678 (Adler and Tang) and 2601.17684 is Hu and Tang's
mismatch-resistant coder; (c) the asymmetric bundle is partly
published (Rinberg et al. 2604.02343, Mao et al. 2505.06297 at
title level, DiFR 2511.20621) and the built archive in amber is
draft-coded on both sides; (d) the rank cell has been occupied since
LLMZip v1 coded ranks with zlib. A pointer under the LLMZip / ts_zip
entry.

docs/REPORT.md (the F-9 row) and docs/GLOSSARY.md (the break-even
entry): synthetic regime only; the free-steering saving has no
real-model support as built (F-12's pooled acceptance delta, F-13,
F-14's k=16 oracle ceiling), and amber's archive has no verifier-side
steering. GLOSSARY's verified-archives entry and OQ-7 row: the
rejection-rate attestation was never built (amber's L1 target
recompute is synthetic only; a drifted decoder is detected, not
located, by the content digest) and a pointer to the prior-art note.

docs/ECOSYSTEM.md, the amber entry: amber imports sideband.synthetic
only (through amber.codec at module level, so its real-archive
experiments load it too), never sideband.specdec; its key files; P7
withdrawn; parked since v0.4.0, record last moved at 69b437c.

Every arXiv id fetched live on 2026-10-11, two abstract pages saved
beside the review's downloaded texts; the patent claims read from two
independent renderings (not legal advice). Files regenerated from one
script in each file's own line ending, never patched by hand.

Proof: critic claims pass, four passes (three blockers, then two, then
one, then none; about 200 numbers, ids and quotes checked; the F-14
figure recomputed from its payload at zero discrepancy); lint_findings
OK (29); tests/test_harness_doc_claims.py, test_critic_lane.py and
test_evidence_bytes.py 13 passed; the full suite not run (docs-only).
No code, evidence, registration block or finding changed; no GPU.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8e3949b 2026-10-11 docs(harvest): lockstep's standalone-merit verdict and its three parked blueprints

````text
A second dated note on docs/ECOSYSTEM.md's lockstep entry (problem right, prescription wrong, economics moot; what stands; the two never-run tests) and a new docs/FUTURE_IDEAS.md section carrying lockstep Blueprints E (decode receipt), D (recipe-pinned derived data) and the unbuilt citation-regime half of F, each with a promotion path; CHANGELOG bullet; ESPALIER_MEMORY row. Run from the lockstep session outside the lane: no execution plan, no critic round; idea-tier text, every number from lockstep findings read in the session. [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]

Tests: lint_findings OK (29); test_harness_doc_claims, test_critic_lane, test_evidence_bytes 13 passed in 29.5 s; full suite not run (docs-only). No code, evidence, registration block or finding changed; no GPU.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## e74cbd7 2026-10-11 docs(harvest): harvest the parked sibling lockstep

````text
docs/DECODE_CONTRACTS.md, a HARVESTED NOTE and NON-CRITERION: grid
crossings under a value contract beside amber's rank-order mismatches
under an order contract, every number generated by key from amber
69b437c (tag errata-batch-3-landed) and lockstep 54d83f4, with a Sources
table of file, blob and JSON Pointer. Dated notes in OPEN_QUESTIONS.md
OQ-7, docs/BLUEPRINT.md T-A, docs/GLOSSARY.md (OQ-7 row, verified-archives
entry) and docs/ECOSYSTEM.md (lockstep entry): lockstep's runtime was never
built and its byproduct economics were never measured. A dated addition
to docs/METHOD.md section 6 (lockstep F-14's 114.5x pack-rate error).

Critic: round one NO-GO (3 blockers, 7 advisories; max discrepancy 0);
confirmation round GO (max discrepancy 0; 4 advisories applied after GO).
Tests: lint_findings OK (29); the 21 doc-reading test files 286 passed,
5 skipped. No code, evidence, registration block or finding changed.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## f23f18e 2026-10-10 docs(memory): log the write-up program design and per-repo errata plans

````text
[withheld: the message matches the deny list (plan 12); see WITHHELD.md]
````

## 738bddc 2026-10-10 docs(memory): log the OQ-20 seed-replay landing and the write-up direction

````text
The seventeenth session's row: OQ-20 landed at 362964a (SPREAD-COVERED / FREE-SPREAD-COVERED), the five critic rounds and the amendment they forced, the suite, and the operator's direction to jump into the write-up after closing the amber and lockstep records.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 362964a 2026-10-10 feat(evidence): land the OQ-20 seed replay of the conversion-verdict legs

````text
Both CPU readouts of the OQ-20 registration (docs/BLUEPRINT.md,
"SEED-REPLAY OF THE CONVERSION-VERDICT LEGS REGISTRATION", 2026-10-09)
from the clean tree at c62f03d, the commit of the six seed-6 runs'
sidecars: results/real/seed_replay_k3.json and seed_replay_oq15.json
with their state files. Stage words SPREAD-COVERED over R2 and
FREE-SPREAD-COVERED over R6: each conversion verdict's vs-vanilla leg
(F-19 arm 4 vs arm 1; F-21 arm 7 vs arm 1) and its mechanism-matched
free leg (arm 4 vs arm 3; arm 7 vs arm 6), replayed at seed 6 under the
frozen policies, reads MUTUAL-COVERAGE / REPRODUCES on both populations
(K3 +0.010340 [-0.009288, +0.030521] vs vanilla and +0.010109
[-0.009724, +0.030422] vs the free arm; OQ15 -0.018029 [-0.065168,
+0.028495] and -0.053623 [-0.107526, -0.002448]); every guard held, no
bar cleared, R4 R-CONSISTENT on both; R8 NEAR-IDENTICAL-ARMS on K3
(fixed by the seed-1 count) and DELTA-MOVES / WITHIN-CROSS-SEED-NOISE on
OQ15 (a description, no consequence). One further seed per leg: the
cross-seed variance stays unestimated, the draft_conf legs and the
same-seed null unmeasured; NON-CRITERION, no verdict, label or kill
status moves.

Record: F-27's STAGE REPLAY line and NON-CRITERION notes in F-19's,
F-21's and F-27's status cells (FINDINGS.md); dated notes in
docs/NOISE_FLOOR.md, README's "What is NOT measured" bullet,
docs/REPORT.md's single-seed limitation and docs/FINDINGS_INDEX.md
(header, F-27 row, arc addendum); the OUTCOME under OQ-20
(OPEN_QUESTIONS.md); the block's OUTCOME with both predictions scored
under the five conventions (the assistant's 2 of 3 modal labels HELD,
the OQ-15 R8 clause FAILED; the critic's 22 of 22 scored clauses HELD;
the mechanical halves apart; no pinned surprise fired); a dated note
under docs/IDEAS.md rank 1; CHANGELOG; tests/test_seed_replay_landing.py [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
(labels, readings, both stage words, shas, legs at six decimals);
tools/run_seed_replay.py joins the frozen closure (pyproject's ruff
extend-exclude, CLAUDE.md thirteen attested of sixteen, the CONVENTIONS,
SHARP_EDGES and TASK_RECIPES entries); README's measured counts.

Disclosed in the block's DATED AMENDMENT AND ERRATA: (1) the frozen
tests/test_seed_replay.py carried three assertions written for the
pre-run tree that failed by construction once the evidence existed, one
of them at c62f03d itself, which was committed WITHOUT running the suite
against CLAUDE.md's make-test rule; each now branches on the evidence's
presence with a dated comment, and the file's sha12 moves from
7d05f02b3354 to 48aec0c0590e (still -text and HAND_PINNED; the
instrument 0b00f8dfd4cf untouched). (2) The FREEZE line's quoted gate
command abbreviates the launch commit; the gate that PASSED ran with
the full sha, as the driver script shows. (3) The two environment
captures (before the replay check, after the last run; sha256 f9bea69f
each, 201 distributions) are committed as results/real/oq20_env_capture_
{before,after}_runs.txt.

Proof: sideband-critic recompute (opus) on the payloads at maximum
discrepancy 0.0 (by its own count 206 numeric and 100 label leaves),
every precondition re-verified, NO-GO on the test-file item above,
resolved by the amendment. Text round NO-GO on two sentences (a false
"float-ties" gloss on K-3's R8; a sign artifact in "R5 and R1 differ
by +0.000231") and thirteen advisories, 0 misquoted numerals of 431;
all applied by revert-and-regenerate. Confirmation GO with four
advisories (the erratum's citation of the driver's argument; the
caveats in F-19's and F-21's status cells and the IDEAS note; the R8 [withheld: IDEAS not in this repository; see WITHHELD.md]
gloss's wording; the CHANGELOG's evidence list), applied as named
post-GO edits by a second regeneration. Re-hash NO-GO on one real
defect: an unescaped pipe in two table cells (F-19's status cell in
FINDINGS.md, F-27's row in the index) truncated the rendered rows;
fixed as abs(R5 - R1) in cells, with a pipe-count test over both record
tables added to the landing test. Second re-hash GO at FINDINGS.md
4e16c7235b28, README.md 1451d9e4d418, docs/REPORT.md 82c8fb352974,
docs/NOISE_FLOOR.md 2e363b3df796, docs/FINDINGS_INDEX.md 7adf0a2274be,
OPEN_QUESTIONS.md 0f804a115a80, CHANGELOG.md cc14b46094b2,
docs/IDEAS.md <digest of a withheld file, scrubbed at export>, docs/BLUEPRINT.md bfcb540e01dd, [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
pyproject.toml 1941d5c6faa4, CLAUDE.md 4740283dc2a5,
docs/CONVENTIONS.md b8a265920642, docs/SHARP_EDGES.md c6bde41610a8,
docs/TASK_RECIPES.md 063d216254c7, tests/test_seed_replay.py
48aec0c0590e (raw-byte sha12; the record files are committed at those
bytes), with three advisories on the new test's latent gaps (pipes
inside code spans, short delimiter rows, rows without a leading pipe)
applied as one named post-GO edit to tests/test_seed_replay_landing.py
alone (19e24f96f065; 8 passed). landing_text check 0 findings over 16
texts and the diff's added lines (245 registered numbers); lint 29
findings OK; ruff clean; targeted tests green on every round; full
suite 704 passed, 5 skipped of 709 in 5,234 s (1:27:14, slowed by the
review rounds' own test calls), started on the tree after the first
fix batch; no code or test file changed after its start except the two
pipe-count tests added to tests/test_seed_replay_landing.py, which ran
alone (8 passed), and the later prose regenerations re-ran the
record-reading tests (test_evidence_bytes, test_harness_doc_claims) on
the final tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c62f03d 2026-10-10 feat(evidence): the six OQ-20 seed-6 runs, registered arms from the clean clone

````text
The six registered runs of the OQ-20 seed replay (docs/BLUEPRINT.md,
"SEED-REPLAY OF THE CONVERSION-VERDICT LEGS REGISTRATION", 2026-10-09;
amendment A1 added the two free arms): K-3 arms 1, 4 and 3 and OQ-15
arms 1, 7 and 6, each over its 210-prompt verdict population at seed 6
with the frozen policies the verdict runs used, launched sequentially
from the clean clone of the launch commit b6d3701 with --out into this
tree (2026-10-09 21:27 to 2026-10-10 02:27). Every meta carries the
bare launch commit (no -dirty), seed 6, a single run_id and no resume;
every stats and gen file has 210 rows; the environment capture taken
after the last run equals the one taken before the first (sha256
f9bea69f...). The thirty sidecars (five per arm) land as evidence under
results/real/{k3,oq15c}_seed6_arm*; the .byproduct/ raws stay
gitignored and sha-bound in the summaries. No readout has been run:
the readouts, stage words and the landing follow from this clean tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## a960709 2026-10-09 docs(memory): log the OQ-20 freeze and launch

````text
Records the second leg of the sixteenth session: OQ-20 registered through five critic rounds and a code review, frozen at b6d3701, the six-arm replay gate passed, the FREEZE line and replay sidecars at 9163706, six seed-6 runs launched from a clean clone. The next session picks up the readouts and the landing once the runs finish.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 9163706 2026-10-09 docs(registration): OQ-20 FREEZE line and the replay-check sidecars

````text
The dated FREEZE line of the OQ-20 block: the freeze commit b6d3701 is
the launch commit; the pinned replay check ran from a clean clone of it
with the six registered arms at their old verdict seeds (K-3 arms 1, 4
and 3 over six prompts at seed 1; OQ-15 arms 1, 7 and 6 over one prompt
at seed 3) and the tool's own gate (`--replay-check --launch-commit
b6d3701`) read every replayed prompt token-exact and every stats row
equal except run_id, seconds and peak_vram_gb, with each replay meta
bound to its verdict meta and to the bare launch commit: PASS on all
six. The thirty replay sidecars (five per arm) land as evidence under
results/real/oq20_replay_*; the byproducts stay gitignored. The line
also discloses one deviation: `pip freeze` raises on this box, so the
environment capture is the importlib.metadata name==version list (201
distributions, sha256 f9bea69f...), taken after the replay check and
before any seed-6 run, nothing installed in between. The seed-6 runs
launch from the same clone next.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b6d3701 2026-10-09 feat(registration): freeze OQ-20, the seed replay of the verdict legs

````text
Registers, before any run, a cross-seed replay of the record's two
conversion-verdict legs: F-19's arm 4 vs arm 1 on the K-3 prompts (seed
1) and F-21's arm 7 vs arm 1 on the OQ-15 prompts (seed 3), replayed
with the same frozen policies at one new seed, 6, plus (amendment A1,
the operator's "add") each verdict's mechanism-matched free arm (K-3 arm
3, OQ-15 arm 6). F-27 measured how far vanilla alone moves across seeds
and named the verdict arms' own cross-seed spread as unmeasured; this
closes that gap as a methods datum. NON-CRITERION for F-19, F-21 and
F-27: no label moves.

Record: the OQ-20 entry in OPEN_QUESTIONS.md and the registration block
in docs/BLUEPRINT.md (pins, six sequential GPU runs from a clean clone
of this commit, a token-exact replay check at the old seeds as the
launch gate, readouts R1-R8 with their labels and readings, two stage
words, the honest prediction, void semantics, consequences; the critic's
rounds recorded with every amendment marked). Code:
tools/run_seed_replay.py (the CPU readouts; imports only the frozen F-27
instrument; a --replay-check launch-gate mode; a sha-headed state file
with --conclude-from) and tests/test_seed_replay.py; one new estimator
sideband.stats.paired_ratio_delta_of_deltas_ci with its tests; the -text
pins and HAND_PINNED entry for the new files; the two state-file
negations; the docs refresh (five sharp-edge entries, one conventions
bullet).

Gated: critic design round GO-WITH-AMENDMENTS (recompute discrepancy 0),
confirmation round NO-GO on two fixes, re-check GO, A1 round NO-GO on
three fixes, A1 re-check GO; code review REQUEST CHANGES with no BLOCK,
every finding applied; docs refresh; full suite green on this tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 3949993 2026-10-09 docs(memory): log the reader-and-lens stage READERS-LONG landing

````text
Records the READERS-LONG landing at 7f0af3e: the final K-2 word K-2-ISOLATED, the critic's two text rounds, and the lessons on reused tags and carried row literals. The next session picks up the negative-result report.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 7f0af3e 2026-10-09 feat(evidence): land the reader-and-lens stage READERS-LONG

````text
Both registered STAGE READERS-LONG runs from the clean tree at f050574
(the handoff commit after the readers landing 34078d1; the instrument
d1125670be05 as frozen): results/real/readers_long_s3.json and
readers_long_s3_r.json with their state files (39 rows each; 25,119.3 /
13,603.0 s elapsed on CPU at six threads, CUDA hidden; the balanced
space admitted on both verified lens payloads; the primary's first
launch died at data load with a MemoryError before any row and was
relaunched as a fresh registered run from the same HEAD). The ONE K-2
sentence over STAGE READERS and STAGE READERS-LONG, issued from the
readers pair with the lens and long payloads: K-2-ISOLATED, FINAL and
unchanged from the interim — the longer-budget reader reads ABSORBED at
L1 (D +0.0012 / +0.0015) and at the balanced L3 (D +0.0015 / +0.0005),
and SURVIVES-STRONGER with the EQUAL-DIMS-ONLY licence at the lopsided
L3 (D +0.005107 / +0.005410; Mt +0.0023 / +0.0031 CI-clear positive with
the points below the floor; Mn_r -0.0028 / -0.0023: the fire is inflated
by the twin's own cost; the lopsided lens never decides a reopen; the
pre-registered surprises "a reader reading SURVIVES-STRONGER at the
lopsided lens and ABSORBED at the balanced one" and "Mn_r non-negative
at the balanced lens on both harvests" occurred under this reader); S1
not triggered (final); the S3 L1 kill stands at the registered reader,
S3 L3 stays OPEN. RL clean-clone rerun of the L1 gate cell identical
except runtime_s; the three R0 linear (a) cells identical to the lens
rows on both harvests.

Record: F-28's STAGE READERS-LONG line (with a regime-and-evidence
sentence naming both reader stages' payloads and landing tests) and
dated notes in the F-24, F-25 and F-28 status cells; the final K-2
STATUS line in docs/WHY_THIS_DIES.md; OUTCOME notes under OQ-17 and
OQ-18; pointers in README, docs/REPORT.md, docs/FINDINGS_INDEX.md,
CHANGELOG.md; the block's OUTCOME with the predictions scored (not
additive to the READERS landing's tallies);
tests/test_reader_lens_readers_long_landing.py. Critic: recompute round
from the state files GO (0 difference over 630 numbers); landing text
round one NO-GO on four sentence blockers (R-L's twin-cost tag, an
overclaimed "most favourable" Mt, the survival count, F-28's missing
evidence pointer), fixed in the generator and re-applied; text round two
GO. Full suite on CPU: 676 passed, 5 skipped. The lane closes with this
landing: every unconditional stage has landed, the conditional
READERS-LONG has landed and the conditional S1 did not trigger; the next
program item is the negative-result report.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 1fafdfe 2026-10-09 docs(memory): log the mid-landing handoff of stage READERS-LONG

````text
The row records the completed READERS-LONG runs, the critic's recompute GO and the final K-2 word, the untracked evidence, and the scratchpad kit path with the exact chain to finish the landing.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f050574 2026-10-05 docs(memory): log the reader-and-lens stage READERS landing

````text
The session row records F-28's STAGE READERS labels, the interim K-2 word, the critic rounds, the suite and the reruns; the next leg launches STAGE READERS-LONG on both S3 harvests from this commit, no commit between launch and landing.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 34078d1 2026-10-05 feat(evidence): land the reader-and-lens stage READERS

````text
Both registered STAGE READERS runs from the clean tree at 790b2fc (the
handoff commit after the lens landing 9bbe905; the instrument d1125670be05
as frozen): results/real/readers_s3.json and readers_s3_r.json with their
state files (75 rows each; 23,314.0 / 11,799.0 s elapsed on CPU, two
six-thread processes concurrent, CUDA hidden; the balanced space admitted
on both verified lens payloads). The K-2 word at S3, pinned before any cell
trained and issued from this pair with the lens payloads: K-2-ISOLATED —
the hz-rescaled reader at the lopsided L3 reads SURVIVES-STRONGER with the
EQUAL-DIMS-ONLY licence (D +0.0080 / +0.0130; Mt -0.0041 / -0.0015, CI-clear
negative on the primary; Mn_r -0.0121 / -0.0144: the fire is the corrected
twin's own cost, and the lopsided lens never decides a reopen), beside its
balanced-lens NOT-SHOWN; both readers ABSORBED at L1 (hz-rescaled D +0.0030
/ +0.0032, two-tower +0.0006 / +0.0007) and the two-tower reader ABSORBED at
both L3 lenses; the registered-reader kill stands as a statement about that
reader; INTERIM: READERS-LONG's trigger fires (no SURVIVES-STRONGER or SPLIT
at L1 or the balanced L3), so the one K-2 sentence is re-issued over both
stages at its landing; S1 not triggered. Clean-clone reruns of the RN and RT
gate cells identical except runtime_s; the three R0 linear (a) cells at the
balanced lens identical to the lens stage's rows.

Record: F-28's STAGE READERS line with dated notes in the F-24 and F-25
status cells; the K-2 STATUS line in docs/WHY_THIS_DIES.md; OUTCOME notes
under OQ-17 and OQ-18; pointers in README, docs/REPORT.md,
docs/FINDINGS_INDEX.md, CHANGELOG.md; the block's OUTCOME with both
predictions scored; tests/test_reader_lens_readers_landing.py. Critic:
recompute round from the state files; landing text round GO. Next: STAGE
READERS-LONG on both harvests from this commit's clean tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 790b2fc 2026-10-05 docs(memory): log the reader-and-lens stage LENS landing

````text
The session row records F-28's labels and numbers, the critic rounds, the suite and the rerun; the next leg launches STAGE READERS on both S3 harvests from this commit with the two lens payloads as admission, no commit between launch and landing.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 9bbe905 2026-10-05 feat(evidence): land the reader-and-lens stage LENS

````text
Both registered STAGE LENS runs from the clean tree at d3504b2 (the handoff
commit after the freeze b128fda; the instrument d1125670be05 as frozen):
results/real/lens_s3.json and lens_s3_r.json with their state files (49 rows
each; 15,302.5 / 7,808.9 s on CPU at six threads, CUDA hidden, concurrent).
Mechanical labels through the frozen OQ-18 rules: FULL-FREE at the balanced
L3 lens ABSORBED at the registered reader (gate D +0.0019 [+0.0006, +0.0032]
/ +0.0004 [-0.0011, +0.0018]; every D upper below +0.005 at off2 / off3 /
off4; OFF3-ABSORBED, OFF4-ABSORBED; Mt +0.0042 / +0.0021; Mn_r +0.0023 /
+0.0017, the corrected twin point-positive on both harvests and CI-clear on
the primary only, where it cost at the lopsided lens; the pre-registered
point-estimate surprise occurred) where the lopsided lens read SPLIT (F-25, standing
as registered); PROXY-LENS LENS-SURVIVES (P +0.0221 [+0.0187, +0.0258] /
+0.0195 [+0.0160, +0.0232], 0.307 / 0.267 of F-17's +0.0721 / +0.0730) with
the growth over the committed L2 margin NOT-SETTLED on both harvests
(combined L3-GROWTH-NOT-SETTLED): existence under a size cap, size not
settled; the full free baseline recovers the whole proxy margin. No K-2
word from this stage (it is STAGE READERS'). Clean-clone rerun of the gate
cell identical except runtime_s.

Record: F-28 in FINDINGS.md with dated notes in the F-17 and F-25 status
cells; the block's OUTCOME with both predictions scored (the assistant's 10
of 16 clauses held, the critic's 6 of 6 with one calibration-only clause);
OUTCOME notes under OQ-13 (ii) and
OQ-18; pointers in README, docs/REPORT.md, docs/FINDINGS_INDEX.md,
CHANGELOG.md; tests/test_reader_lens_landing.py (fails, never skips; pins
the instrument, payload and state shas and the labels); the tool joins the
frozen closure (pyproject extend-exclude; CLAUDE.md twelve attested of
fifteen; docs/CONVENTIONS.md and docs/SHARP_EDGES.md). Critic: recompute
round with a maximum difference of 0 over 232 compared numbers; landing
text round GO. Next: STAGE READERS with --lens-payloads from this commit's
clean tree.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d3504b2 2026-10-05 docs(memory): log the reader-and-lens freeze lane

````text
The session row records the registration's freeze at b128fda, the four critic rounds and the code review, the suite result, and the lessons; the next session (or this one, after the handoff) launches STAGE LENS on both S3 harvests and lands per stage with no commit between launch and landing.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b128fda 2026-10-05 feat(instrument): register the reader-and-lens re-test at S3

````text
Pre-run registration (docs/BLUEPRINT.md, "READER-AND-LENS RE-TEST AT S3
REGISTRATION", 2026-10-05): OQ-13 (ii)'s balanced-lens read and the
stronger-reader re-test of F-24 / F-25 as ONE registration on the two
committed S3 harvests, CPU only, through the frozen OQ-18 chain imported by
bare name. STAGE LENS (R0 at the Fiedler-binned balanced L3 lens, 49 cells
per harvest, F-25's grid plus the fresh linear (c) - (a) proxy); STAGE
READERS (RN = hz-only rescale to the aligned slots norm, RT = two-tower,
at the L1 / lopsided L3 / balanced L3 gate cells, 75 cells per harvest);
conditional READERS-LONG and S1 stages. Labels, licences, horizons and the
K-2 sentence pinned (reopen-grade = SURVIVES-STRONGER + FULL licence + Mt
triple rule; the lopsided lens never decides a reopen; REOPENED provisional
until a reader-matched rider; the all-space word K-2-NOT-OVERTURNED-AT-S3;
the combined L3-GROWTH word against the committed L2 margin). Honest
prediction (the assistant's and the critic's) written before any cell
trained; clause (1)'s persistence sub-clause already FAILED by the artifact.

Instrument tools/run_reader_lens.py (CUDA hidden at import; asserts the
amended instrument's frozen sha; HARVEST_FILES companions; --conclude-from
binds every payload to its stage and role, verifies registry, row set,
HEAD, n_boot and riders, and issues the K-2 word from a readers pair with
--lens only); lens builder tools/build_balanced_groups.py and the artifact
results/real/concept_groups_olmoe_balanced_v1.json (sizes [32 x 14, 31 x 2],
Fiedler gap 0.0166, train glue-dropped persistence 0.1033 against the
lopsided 0.6748 and k16 0.2293); tests/test_reader_lens.py (26) and
tests/test_balanced_groups.py (7). Pins: -text and HAND_PINNED for the tool,
its test and the builder; eight state-file negations in .gitignore; files
at the freeze (raw bytes): tool d1125670be05, test 99acea801eab, builder
d6fda8997c65, artifact 3186abb35e52. OPEN_QUESTIONS.md dated notes under
OQ-13, OQ-17, OQ-18.

Critic: design round NO-GO (8 blockers, 15 advisories) and confirmation
round NO-GO (3 blockers, 9 advisories), each applied as one batch with the
harness code review (2 blocks, 10 advisories); third round NO-GO on one
text error (the rename record); fourth round GO. No cell of the
registration has trained.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 23d1983 2026-10-05 docs(memory): log the seed-noise floor lane

````text
The row records the seed-noise floor registration, runs and landing (F-27 at 73d8dc2, freeze 906edfd) with the critic's five rounds and the lane's footguns. The next session picks up item 2 of the operator's program, the balanced-lens read at S3 L3, through the same lane.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 73d8dc2 2026-10-05 feat(evidence): land the seed-noise floor readouts

````text
Both registered runs from the clean tree at the freeze commit 906edfd
(CPU, BLAS threads capped at two; the GPU carried another job), each
reproduced exactly from its state file and the committed summaries by
the instrument's --conclude-from. Label FLOOR-MATERIAL on both
populations (f_one at n = 30 0.1060 on K3, 0.1320 on OQ15, against the
2% kill IDEAS rank 1 pinned), stage NOTE-STANDS, readings [withheld: IDEAS not in this repository; see WITHHELD.md]
BAR-RESOLVED@210 (half-widths 0.0385 / 0.0398 against the 0.062 bar)
and RULE-LEAKS@30 (g_one 0.0235 / 0.0375; the guard identity held at
every n) on both; the replication agrees. A same-policy seed change
moves pooled tokens/call by a CI95 half-width of about 0.04 at 210
prompts and about 0.10 at 30; one seed's per-prompt tokens/call
correlates 0.42 with the other seed's; a +0.062 point win appears by
seed noise alone in about one 30-prompt subset in nine. A cross-seed,
same-policy, single-comparator null; the record's legs are same-seed
and all-comparator, and that null stays unmeasured. NON-CRITERION: no
verdict, label or kill status moves.

What changed:
- results/real/noise_floor_k3.json, noise_floor_oq15.json and their
  .state.jsonl (5,000 rows each: every subset's prompt indices and swap
  mask with its delta, CI and budgets; the header binds the summary,
  meta and prompt-file shas).
- FINDINGS.md: F-27 (the entry and its table row); a dated note in
  F-19's status cell placing its val-selected +0.0597 at the 88th
  percentile of a single 30-prompt cross-seed null draw, the four
  unmodeled factors named.
- docs/BLUEPRINT.md: the block's OUTCOME — every readout, the pinned
  sentence filled, the prior-art search record (criterion not met; the
  note stands), both predictions scored under the five conventions
  (the assistant's 24 of 27, (9) 3 of 4 and (10) 4 of 4 tallied apart,
  the critic's 10 of 10), the review rounds.
- docs/NOISE_FLOOR.md: the methods note (acceptance-level; the
  paired-ratio package section; prior art).
- docs/IDEAS.md (the OUTCOME note under rank 1), README.md and [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
  docs/REPORT.md (dated notes on the cross-seed and single-seed
  sentences), docs/FINDINGS_INDEX.md (header, row, arc section),
  CHANGELOG.md (the section).
- tests/test_noise_floor_landing.py: six tests pinning the instrument
  sha, both state shas, the run commit, the labels and eight headline
  numbers per population, and running --conclude-from on both.
- The tool joins the frozen closure: pyproject.toml extend-exclude,
  CLAUDE.md (eleven attested of fourteen), docs/CONVENTIONS.md and
  docs/SHARP_EDGES.md.

How it was proved: every landing numeral generated from the payloads
through a registry and traced by tools/landing_text.py over the diff's
added lines (0 findings); lint_findings OK (28 findings); the critic's
landing round in recompute mode re-derived every state row bit-exactly
and every readout within 1.7e-16 from the summaries and state files,
then read NO-GO on six text items (false comparison sentences, a
malformed index row, carries the registration pinned but the entry
lacked, a prior-art judgement that had not re-checked SPEED-Bench at
its source), all applied by revert-and-regenerate; its confirmation
round NO-GO on one leftover (the SPEED-Bench description), applied the
same way; its re-read GO; ruff clean; the full suite with CUDA hidden
and BLAS threads capped at two, on the tree before that last text-only
pass: 631 passed, 5 skipped in 21 minutes; after it the landing test,
the instrument tests and the three guard tests: 40 passed.

Files at the landing (sha256, first twelve hex, as staged; the
instrument tools/run_noise_floor.py unchanged at abb0bec95a22):
results/real/noise_floor_k3.json 2030f33a4f60, its state file
4032925543a3, results/real/noise_floor_oq15.json 2a9d1ccc0851, its
state file d271650df468, tests/test_noise_floor_landing.py
81a80ad97f1d, docs/NOISE_FLOOR.md 41f5bc22ebd1, FINDINGS.md
c1e28ee06338, docs/BLUEPRINT.md 42529d4cfee4, docs/IDEAS.md [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
a9b917deb98f, README.md 88e3a6c823c0, docs/REPORT.md c312cf048d40,
docs/FINDINGS_INDEX.md dc89152dedca, CHANGELOG.md 4e943c4b2d0b,
CLAUDE.md 7c012d3caa96, docs/CONVENTIONS.md bc8f65e918f5,
docs/SHARP_EDGES.md f5eddc3f35da, pyproject.toml 38353ca42dd7.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 906edfd 2026-10-04 feat(instrument): register the seed-noise floor readouts

````text
Pre-run registration, critic-gated; nothing has run on the seed pairs
and no result exists. Every conversion verdict in the record carries a
CI across prompt clusters at one seed, and the +0.062 tokens/call bar
with the F-19 WIN rule was priced against those CIs; the seed-to-seed
noise floor existed only as the STAGE-A FREEZE power note and IDEAS [withheld: IDEAS not in this repository; see WITHHELD.md]
rank 1's unregistered recompute. This registration prices it on the
four committed vanilla gamma-4 verdict runs (K3 = seeds 0 / 1 on the
k3 verdict prompts, F-19's pair; OQ15 = seeds 2 / 3 on the oq15
verdict prompts), CPU only, from the summaries' per-prompt rows:
seed-pair reliability with a prompt-bootstrap CI and the within-family
r; the nested sums of squares as ML shares and as balanced
method-of-moments components; the paired-ratio half-width at n = 30 /
42 / 84 / 126 / 210 over 1,000 subsets per n; the null exceedance of
the bar as the symmetrised one-sided rate; single-comparator false
positives of the F-19 leg rule (the budget guard cannot bind between
fixed-gamma vanilla runs, so the guarded rate is an identity check);
the percentile of F-19's val-selected +0.059725 under the n = 30 null;
and a non-label seed-label swap companion centred at zero. Labels
FLOOR-MATERIAL / FLOOR-WEAK on IDEAS's 2% kill, K3 the label [withheld: IDEAS not in this repository; see WITHHELD.md]
population and OQ15 the replication; readings BAR-RESOLVED@210 and
RULE-LEAKS@30 beside the label. It is a cross-seed, same-policy,
single-comparator null; the record's legs are same-seed and
all-comparator, and that null stays unmeasured. NON-CRITERION for
every finding; the pinned consequences are dated lines (F-27, the
methods note docs/NOISE_FLOOR.md under the pinned prior-art search,
pointers in README, REPORT, IDEAS and F-19's status cell). [withheld: IDEAS not in this repository; see WITHHELD.md]

What changed:
- tools/run_noise_floor.py: the instrument (numpy only, imports
  sideband.stats and nothing under tools/); nineteen precondition
  checks bind the pooled fields, the per-prompt ratios, gamma, the
  metas' seeds and prompt-file sha and the families; it attests its
  raw bytes, refuses to write under results/ on a dirty tracked tree,
  writes LF, and --conclude-from recomputes every row, readout and
  label from the state file and refuses any drift.
- tests/test_noise_floor.py: twenty-one tests on synthetic 210-prompt
  pairs (identity and method-of-moments definitions, planted
  components, per-family r, subset and swap determinism, the e6
  recipe, the rates in both orientations with the guard identity, the
  labels, every refusal, no torch); the precondition on the committed
  summaries, no cross-seed statistic.
- docs/BLUEPRINT.md: the registration block with both predictions
  pinned and the three review rounds' records.
- docs/IDEAS.md: a dated REGISTERED note under rank 1. [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
- .gitignore: the two state-file negations; .gitattributes: -text for
  the tool and the test file; tests/test_evidence_bytes.py: the test
  file hand-pinned.

How it was proved: critic design round NO-GO on seven items and eleven
advisories (the guard identity, the halved seed term, which null this
is, a re-reading of F-19, known cells scored as predictions, the SE
formula, the subsampling caveat's direction), all applied in one
batch; confirmation round NO-GO on two text items and eight advisories
(a loosened range restored, "upper bound" qualified), applied; re-hash
round GO with two cosmetic advisories, applied as named post-GO edits
to the block alone; --precondition-only nineteen of nineteen on both
populations; the full suite on the final bytes with CUDA hidden and
BLAS threads capped at two (the GPU carries another job): 625 passed,
5 skipped in 24 minutes.

Files at the freeze (sha256, first twelve hex, as the critic's final GO
hashed the two instruments; the others as staged):
tools/run_noise_floor.py abb0bec95a22, tests/test_noise_floor.py
732a886e5693, docs/BLUEPRINT.md 1b4bed58d62d, docs/IDEAS.md [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
8cd36dab1046, .gitignore ed147f962a0b, .gitattributes 4a13c0e92248,
tests/test_evidence_bytes.py 6c59f27695ad.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## ed5c164 2026-10-04 docs(memory): log the horizon-read landing lane

````text
The row records the twelfth session: the readiness checks, the two registered runs from 5e0e2a9, the recompute and clean-clone proofs, the landing lane's review rounds and fix batches, the commit b71e9ca and the lessons.

The next session picks up the owner's standing calls: LINT-1, the OQ-19 decision, the push of main, the write-ups and the generator-tracking option; nothing is in flight.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b71e9ca 2026-10-04 feat(prefetch): land the horizon read at the R2 encoding

````text
Both registered runs of the OQ-9 stage-1 HORIZON READ (frozen at
b41d3f3; launched from the clean tree at 5e0e2a9, the memory-row commit
after the freeze, under the operator's words "all approved"), their
metas and state files, and the pinned consequences. LABEL LEAD-TIME-
ABSORBED on both harvests (H-ABSORBS at every horizon 1..4), REPRODUCE
EXACT against the committed R2 rows at horizon 1 with the identity on
the four cells, no straddle, guard or free_h grid edge at any label
horizon on either harvest, so the pinned closure applies: at this
reader the address stream is not shown to add a material hit-rate
margin over free information at any horizon 1..4; the stage-2 strike
stands, PREFETCH-HEADROOM stands, OQ-9's prefetch half closes at this
reader, K-6 stays UNTESTED with its lead-time datum (in forwards; no
latency priced). NOT a rung on the horizon-1 margin; no further rung.

What changed:
- results/real/prefetch_horizon_s3{,_r}.json + .meta.json +
  .json.state.jsonl
- FINDINGS.md: F-26's fourth dated status line (every number derived
  from
  the payloads through tools/landing_text.py; both predictions scored).
- docs/WHY_THIS_DIES.md: the dated K-6 STATUS line (which way the datum
  points; why K-6 stays UNTESTED).
- OPEN_QUESTIONS.md: the OQ-9 closure note and the dated line under the
  stage-2 sentence.
- docs/BLUEPRINT.md: the horizon block's DATED NOTE pinning the
  clean-clone failure branch (18:11, before the rerun was read) and the
  OUTCOME (predictions scored, the critic recompute record, the clean-
  clone
  rerun byte-identical, the landing rounds).
- Dated pointers: README, docs/FUTURE_IDEAS.md P1, docs/REPORT.md, [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
  docs/FINDINGS_INDEX.md, docs/GLOSSARY.md, CHANGELOG.md.
- tests/test_prefetch_horizon_landing.py: pins the instrument sha, both
  state files' shas, REPRODUCE from the committed R2 state files, the
  labels and flags as landed, the cross-harvest closure condition; the
  cache check skips only where the cache is absent.
- The tool joins the frozen closure: pyproject.toml extend-exclude,
  CLAUDE.md (ten attested of thirteen), docs/CONVENTIONS.md,
  docs/SHARP_EDGES.md; measured counts in README and
  docs/CONVENTIONS.md.

How it was proved: critic recompute GO at maximum discrepancy 0.0
(75,816 payload values, 1,188 identity values, 218,880 REPRODUCE
comparisons; seven advisories, all applied); the clean-clone rerun of
the primary from b41d3f3 BYTE-IDENTICAL (state sha e768ca7a68db); the
kit's check at 0 findings over every edited file; the code review
APPROVE (five nits, two applied; its re-check held); the critic's text
round NO-GO on seven text items (3,283 numerals checked, 3 misquotes;
all sentences and counts, none touching a label), the fix batch by
revert-and-replay from HEAD, the confirmation round GO with two
advisories (3,354 numerals, 0 misquotes), both applied as named post-GO
edits by a second replay, the re-hash GO with no objection (3,362
numerals, 0 misquotes) at the seventeen shas below; the full suite 604
passed, 5 skipped of 609 collected in 2,977.7 s with the reviewers
running beside it (load, not cost).

Files at the final GO (sha256, first twelve hex): FINDINGS.md
65af281b261f, docs/BLUEPRINT.md 616a93a66537, docs/WHY_THIS_DIES.md
4a40215f64b9, OPEN_QUESTIONS.md d8606dde628d, README.md 1081769f7907,
docs/FUTURE_IDEAS.md d07fd5723abc, docs/REPORT.md 7acb05f550b9, [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
docs/FINDINGS_INDEX.md 762cf0ece160, docs/GLOSSARY.md af8048796a9e,
CHANGELOG.md 8daba1741529, CLAUDE.md ba38767fddee, docs/CONVENTIONS.md
5541e123e55c, docs/SHARP_EDGES.md 18e372a00d3a, pyproject.toml
9981f8fba38c, docs/TASK_RECIPES.md fb085c3c3e6e, ESPALIER_MEMORY.md
be3526579061, tests/test_prefetch_horizon_landing.py 8d0c87ed1ac8
(worktree bytes; the LF files LF on disk, the CRLF files CRLF).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5e0e2a9 2026-10-04 docs(memory): log the horizon-read registration (retroactive)

````text
The row reconstructs the eleventh session (the horizon-read registration lane through the freeze commit b41d3f3, which ended without a handoff) and the twelfth session's pre-launch checks, push and approval.

The next session picks up the registered horizon runs (primary then replication, no commit between launch and landing) or, if both payloads exist, the landing lane.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b41d3f3 2026-10-04 feat(prefetch): register the horizon read at the R2 encoding

````text
Pre-run registration, critic-gated; nothing has launched and no result
exists. The OQ-9 prefetch ladder (F-26, the free-bigram twin, the
stratified read, R2) was read at horizon 1 only, and prefetch pays only
if the resident set is chosen before the fetch latency elapses. This
read prices horizons 2, 3 and 4 on the two S3 harvests as a K-6
lead-time datum: features at time t exactly as R2 builds them (the
address block, the hidden block, the smoothed bigram tables), the token
tables horizon-matched to the routing j forwards on, k and lambda
re-selected per horizon on val. At horizon 1 every selection is taken
from the committed R2 payload and the rows must reproduce R2's rows
summed to the two coverage unions, with an identity on four cells. Per
horizon R2's Q2 rule labels the equal-dims and union readings; a stage
label LEAD-TIME-ABSORBED / -SURVIVES@j / -COMPLEMENTARY@j /
-INCONSISTENT follows, with straddle, reader-guard and free-arm-edge
rules that withhold the closing claim. Two pinned consequences: a
fourth dated STATUS line under F-26 and a dated K-6 STATUS line; the
stage-2 strike stands under every label and no further rung is
registered at any horizon.

What changed:
- tools/run_prefetch_horizon.py: the instrument, an R2 subclass; it
  pins the frozen R2 tool's sha at import, hashes its own bytes at the
  run's start and refuses to write if they change; --conclude-from
  recomputes every number and label from the state file.
- tests/test_prefetch_horizon.py: nineteen tests on CPU fixtures (the
  horizon-1 rows reproduce a fixture R2 run; the horizon tables equal
  the frozen construction at horizon 1 and a brute-force recount at
  horizon 2; planted rules read the labels they should; the label and
  withholding rules; the guards and recompute refusals; no torch).
- docs/BLUEPRINT.md: the registration block with both predictions
  pinned, the disclosed smoke, and the review rounds' records.
- OPEN_QUESTIONS.md: a dated note at the end of OQ-9.
- .gitignore: the two state-file negations; .gitattributes: -text for
  the tool and the test file; tests/test_evidence_bytes.py: the test
  file hand-pinned; docs/CONVENTIONS.md: one dated sentence on when a
  hand-pinned entry is added.

How it was proved: code review APPROVE (four warnings applied); critic
design round NO-GO on two text items and twelve advisories, confirmation
NO-GO on two, re-confirmation GO with nine advisories, re-hash NO-GO on
one, final re-hash GO; the smoke on moe_s8's val prompts recomputed by
the critic at maximum discrepancy 0.0 and rerun through the final bytes
with a byte-identical state file (a6bec0d74678); the full suite on the
final bytes with nothing else running: 598 passed, 5 skipped.

Files at the freeze (sha256, first twelve hex, as the critic's final GO
hashed them; docs/BLUEPRINT.md gained one append-only paragraph after):
tools/run_prefetch_horizon.py cc6a7fb0bc50, tests/test_prefetch_horizon.py
94de43b4d675, docs/BLUEPRINT.md 0ed6de7eac57 (76226c5a5ada at the
commit), OPEN_QUESTIONS.md 1c40de588735, .gitignore a6d4563e193d,
.gitattributes 0b79728f8481, tests/test_evidence_bytes.py 1204515ae6ca,
docs/CONVENTIONS.md 8e0843368950.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## dc7ed5b 2026-10-04 docs(memory): log the evidence-pinning lane

````text
The tenth-session row: what the lane stored and enforced, the seven critic rounds and their outcome, the three line-ending traps measured on the way, and the owner's unchanged calls. The next session opens on a clean tree with nothing in flight.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 0eb73d9 2026-10-04 fix(evidence): store the sha-cited files outside results/ as cited

````text
Fifteen tracked files outside results/ are cited by sha256 in other
tracked text files (186 citations: 165 in results/ payloads, 12 in
state-file headers, 9 in tests/, tools/ and docs/BLUEPRINT.md). All were
stored LF with no -text attribute, so a checkout's core.autocrlf decided
their bytes. Measured in scratch clones of 41359bd: an autocrlf=false
clone reproduced none of the 99 citations of the six CRLF-cited files
(the four data/prompts*.jsonl, tools/run_fullfree_coarse_amended.py,
tools/run_oq18_rider_diag.py) with every citation-bearing test green; an
autocrlf=true clone reproduced none of the 87 raw-bytes citations of the
nine LF-stored files and failed
test_frozen_instrument_sha_is_pinned_and_true_on_disk and the two
test_committed_*_payload_reproduces_its_verdict tests.

The fix. .gitattributes pins the fifteen with -text, plus
tests/test_prefetch_r2.py (docs/BLUEPRINT.md's R2 freeze record pins it
by a 12-hex raw-LF sha, outside the 64-hex scan). `git add --renormalize`
in this worktree, where the disk bytes are the cited bytes, stored each
as it is on disk: six blobs changed from LF to CRLF by line endings only,
nine unchanged; no byte on disk changed (18 of 18 sha256 of the frozen
closure and the cited files identical before and after). After the fix,
fresh clones of either autocrlf setting reproduce 186 of 186.

Two of the six are frozen instruments. Their attested bytes ARE the CRLF
bytes; this commit makes the stored blob equal the attested bytes for the
first time. Operator authorisation, 2026-10-03, after the blob change was
spelled out in the plan and in a follow-up question: "got it, approved".

Enforcement: tests/test_evidence_bytes.py check 4 derives the cited set
from the full-sha256 citations and requires the -text attribute (worktree
and index), a citation of the disk bytes themselves (another line-ending
form is a stale checkout when the index holds the cited bytes, else an
unreproducible chain, each with its own remedy), index-blob equality with
the disk bytes, and citation counts no lower than HEAD's; HAND_PINNED
holds the 12-hex pin to the attribute. Seven negative controls in the
fixed clone fire five of its six messages, each in the state it
describes; the sixth fired in the critic's re-runs. The forward ledger's
row for this defect is struck with the measurements.

Also: dated updates on two docs/SHARP_EDGES.md entries (three traps
measured on the way: a fresh autocrlf=true clone writes every text file
CRLF; git status stays clean behind the stat cache; an existing
autocrlf=true checkout that pulls a new -text line keeps stale copies,
remedy `landing_text.py eol --fix-lf`) and a grep -i -F exit-134 footgun
on this box; docs/CONVENTIONS.md, docs/TASK_RECIPES.md (the freeze commit
adds the -text line), CHANGELOG.md, README.md (584 tests),
ESPALIER_MEMORY.md (dated note on the 2026-10-01 row). No research text,
payload, results/ file or on-disk instrument byte touched.

Reviews: sideband-critic recompute, seven rounds to GO (two blocking,
then one, one, GO, then two single-sentence blockers on the re-hash
rounds, then GO; byte and count discrepancy 0 throughout); code-reviewer
APPROVE, REQUEST CHANGES (docstring), APPROVE, APPROVE. Suite after the
fix batches: 579 passed, 5 skipped of 584 collected. Final
LF-normalised sha256 (first 12) at the critic's GO: .gitattributes
b0bdbe063116, CHANGELOG.md df2a8227e64d, ESPALIER_MEMORY.md 4b3aae14ebd2,
docs/CONVENTIONS.md 9ecf157eb144, docs/SHARP_EDGES.md 2f6e82445799,
tests/test_evidence_bytes.py b515034728c5, README.md 415bd6c388f0,
docs/TASK_RECIPES.md 4736080260a0, task-packs/FORWARD_LEDGER.md
0202600b3ab9, task-packs/LEDGER_PROBES.json ed3690048197.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 41359bd 2026-10-03 docs(memory): log the landing-text kit lane

````text
The ninth-session row: the kit's design, the four review rounds and their shas, the suite, and the lessons the kit's own first use taught. The next session picks up from the owner's open calls; nothing is in flight.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## cf4eccf 2026-10-03 feat(tools): add the landing-text kit

````text
Three landings (the free-bigram twin 2026-10-01, the stratified read
2026-10-02, R2 2026-10-03) each rewrote the same generator and applier
mechanics as session scratch and each paid a fix round to the same
footguns. tools/landing_text.py keeps the mechanics once; the sentences
and anchors stay per landing.

- tools/landing_text.py: new, standalone (no sideband, numpy or torch
  import; the instrument's reading rule is passed in). Pair: a primary /
  replication payload pair, provenance asserts, a number registry
  (f4/num/ci/pair/pp/pt), readings from the rule with rdp recording a
  split reading as a pair, straddle, score, write (texts + numbers.json
  after a case-folded, whitespace-collapsed banned-phrase assert). Doc:
  one record file in its own line ending (detected, mixed refused, expect
  catches a revert's CRLF), once / replace_once / flex_replace_once, a
  Region that re-looks its bounds up on every call, para_end by the
  blank-line rule (refuses a tight bullet list), insert_after_paragraph,
  insert_after_line, append_line, rewrap_bullet (refuses a span over a
  blank line), write with dry. wrap holds backtick spans together. CLI:
  check (unknown numbers, pairs lost in application, banned phrases over
  generated texts or the diff's added lines; untracked paths refused) and
  eol (survey, --expect, --fix-lf).
- tests/test_landing_text.py: 23 tests, synthetic fixtures, a git-init
  test for the diff path, a positive control on the committed R2 payloads
  (the unseen-key pair verbatim in F-26's 2026-10-03 status line; the
  pooled split as the payloads' own label fields read it).
- docs/TASK_RECIPES.md: the landing-texts recipe (generate / apply /
  check / fix by revert-and-regenerate; expect="lf" on every LF file).
- docs/SHARP_EDGES.md: dated updates on the two landing-text entries;
  the first folds the three footguns the R2 landing exposed (held as a
  reflect candidate until now) and names what the kit refuses; the
  suite-time entry's counts re-measured.
- docs/CONVENTIONS.md: the tool-script naming line and the standalone
  exception, both bullets re-wrapped.
- README.md: counts re-measured on this tree (583 tests, 34 test files,
  35 drivers); CHANGELOG.md: a dated section.

Applied through the kit itself (its first live use): every doc edit by
Doc in the file's own line ending, every fix by revert-and-regenerate;
no registered text, instrument, payload or frozen-closure entry touched.

Reviews: sideband-critic (diff mode) NO-GO on 4 BLOCKING / 9 advisory,
all applied in one batch; code-reviewer REQUEST CHANGES (3 BLOCK / 5
SHOULD), all applied; confirmation round: code-reviewer APPROVE
(tools cd8a25aae88c, tests 7b106ffab879) and sideband-critic GO with 4
advisories, all applied as named post-GO edits (record-free fixture
values; "every numeral outside the docstring's exclusions"; the
tight-list refusal extended to numbered items and table rows; the LF
list replaced by the survey rule); re-hash round: sideband-critic GO
with one wording nit; docs-maintainer (propose-only) four count and
pointer updates in docs/CONVENTIONS.md and docs/SHARP_EDGES.md, applied
with the nit as named post-GO edits; re-hash GO with one dated-count
advisory (the SHARP_EDGES proof line) and a cosmetic wrap, both applied;
last re-hash: sideband-critic GO with no objections at LF-normalised
shas tools/landing_text.py 7bddcc8774e6, tests/test_landing_text.py
6db101c10b22, docs/TASK_RECIPES.md 2c1248531a79, docs/SHARP_EDGES.md
ccc91c49d1a3, docs/CONVENTIONS.md 17ee1b8df305, README.md 74bd01a0d84c,
CHANGELOG.md 23cf27470fc7 (41 numbers checked, 0 wrong). Suite: 578
passed, 5 skipped in 2,225 s (37:04; the critic's confirmation rounds
overlapped its first minutes). lint_findings OK (27); ruff clean.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## fdca294 2026-10-03 docs(memory): log the R2 landing lane and reconcile 744 vs 804

````text
The 2026-10-03 Session Log row records the R2 lane end to end (freeze 2fe5926, landing 2f13134): the labels, the critic's recompute and four text rounds, the measured counts, and the 744-vs-804 reconciliation (804 was the stratified confirmation round's count alone; the dated erratum sits on that OUTCOME). The lint-policy row now says twelve frozen files, nine attested; the oldest row moved to docs/session-archive.md. The next session opens on nothing in flight: the write-ups, the OQ-19 decision, the EVID-1 and LINT-1 lanes and the push of main are the owner's calls.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2f13134 2026-10-03 feat(prefetch): land the generalising free baseline (R2)

````text
Both registered runs of the generalising free baseline (replay-prior
smoothed count tables with the model's own routers on the token's
normalised input embedding, one weight k selected on val; the forward's
stored final-norm state as a second question) ran from the clean freeze
commit 2fe5926 on the two S3 harvests and landed as
results/real/prefetch_r2_s3{,_r}.json with their metas and state files.

Label R2-FALLBACK-SURVIVES / H-ABSORBS on both harvests, REPRODUCE EXACT
against the stratified read's rows, k = 128 interior, no straddle on the
unseen-key gate or either Q2 reading: against the generalising free
block the address block still adds a material margin on the unseen-key
positions while the encoding recovers more hit rate there than that
margin (the located margin is NOT shown to be table sparsity at this
encoding); with the stored final-norm state in the free arm no material
margin of the address block or of the address stream is shown, so by the
pinned condition stage 2's address-beyond-free motivation is struck. The
free-baseline ladder under F-26 is closed as pre-committed.

Record: F-26's third dated status line; the block's OUTCOME with both
predictions scored, the critic's recompute record and the landing
rounds; the OQ-9 note and a dated line under its stage-2 sentence; dated
pointers on the sites the registration names; a dated erratum on the
stratified read's OUTCOME (its checked-number count was the confirmation
round's alone); the derived ledgers; README counts measured on this
tree; the tool joins the frozen closure (ruff exclude, CLAUDE.md nine
attested of twelve, the SHARP_EDGES entry); the harness docs refreshed;
tests/test_prefetch_r2_landing.py.

Proof: critic recompute GO at maximum absolute discrepancy 0.0 over
74,366 values from the two state files; clean-clone rerun of the
primary byte-identical; the landing-text round NO-GO on eight blocking
items, all applied by revert-and-regenerate; the confirmation round GO
scoped to file shas with six advisories, applied as named post-GO
edits; the re-hash round GO with one wording nit, applied and named; the
final re-hash GO scoped to ten file shas (FINDINGS.md b7dfd39a680d,
docs/BLUEPRINT.md b2a7f837e02b, OPEN_QUESTIONS.md 37272acd5eec,
docs/FINDINGS_INDEX.md e29197c68a26, README.md d93515c70a15, the five
others as read); landing and harness-doc tests green; findings lint OK
(27); ruff clean; audit and integrity clean; full suite 555 passed,
5 skipped in 1,187 s at preflight.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2fe5926 2026-10-03 feat(prefetch): register the generalising free baseline (R2)

````text
Register the fourth and last rung of the OQ-9 stage-1 free-baseline
ladder as a dated amendment block in docs/BLUEPRINT.md, written before
any readout ran on either S3 harvest, with the operator's confirmation
of the design ("confirm, with the hidden arm as Q2").

The free arm replaces the twin's count tables by replay-prior smoothed
tables: each gate's router applied to the token's normalised input
embedding (the cached OLMoE checkpoint, parsed with numpy only and
pinned by a sha over exactly the tensors read) as the Dirichlet prior
of a leave-one-prompt-out count row, one weight k selected on val from
{0, 2, 8, 32, 128, 512, inf} jointly with lambda, so that no free row
is ever at the marginal. Q1 reads the shrinkage over the twin's free
arm and the equal-dims gate on the unseen-key positions and pooled;
Q2 puts the forward's stored final-norm state (clipped, z-scored and
reduced to 1024 principal directions on train) into the free arm and
reads the equal-dims and union margins, with a reader guard where the
hidden block degrades an arm. Precondition: this read's rows for the
twin's nine arms reproduce the stratified read's committed rows per
stratum, and the twin's D_eq on three scopes equals its cells. Labels,
straddle sentences, qualifiers, said-in-words flags and both
predictions are pinned; R2 is pre-committed as the last rung on this
margin.

tools/run_prefetch_r2.py imports the frozen stratified tool by bare
module name and refuses a modified one; tests/test_prefetch_r2.py (21
tests) covers the chain's assertions, the smoothing identities, the
replay against brute force, three rule fixtures, mechanical labels for
every branch, REPRODUCE against a fixture payload, the guards and the
exact recompute's refusals. OPEN_QUESTIONS.md carries the OQ-9 dated
note; .gitignore un-ignores the two state files the registered runs
will write.

Proof: ruff clean; findings lint OK; the full suite 549 passed, 5
skipped in 758 s on these bytes; one disclosed smoke on shard s8's val
prompts recomputes exactly. Reviews: the sideband-critic's design round
(NO-GO, 7 blocking, 11 advisory), confirmation (NO-GO, 2 blocking, 7
advisory), final re-read (GO) and re-confirmation after the code review
(NO-GO on one item, then GO), every item applied and recorded in the
block's pre-freeze round with the critic's prediction verbatim; a
code-reviewer pass (REQUEST CHANGES: 1 BLOCK, 1 WARN, 13 NOTEs; then
APPROVE on two edits, applied). The critic's final GO is scoped to
these bytes, sha256 first twelve hex: docs/BLUEPRINT.md 04b3e3d49c6e,
tools/run_prefetch_r2.py eaf671fdb9d6, tests/test_prefetch_r2.py
c9a8efa7cd5e, OPEN_QUESTIONS.md bad0979ef4c8, .gitignore 272d3e6a1c57,
recorded here rather than in the block so the block's hash stands.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d56f12c 2026-10-02 docs(memory): log the docs lane that levelled the derived ledgers

````text
The row records the seventh session: the derived ledgers (changelog,
findings index, README counts, conventions) levelled for the stratified
coverage read through the full lane, four critic text rounds with every
blocker a sentence and none a number, and a dated note that the previous
row's checked-number count disagrees with the registered outcome and is
not reconciled. Two patterns join the table: a cut-truncated grep line
is not a read, and a docs lane starts by grepping the target docs. The
oldest session row moves to docs/session-archive.md under the file's
keep-five policy.

The next session picks up R2, a free baseline whose encoding handles
unseen and sparse keys, through the lane, or the evidence-reproducibility
ledger item first.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## b35a202 2026-10-02 docs(ledger): level the derived ledgers after the stratified read

````text
The changelog gains a dated section for the stratified coverage read's
registration, landing and memory commits, plus the two commits of the
previous day it could not carry (one was the commit that wrote it). The
findings index gains a dated arc paragraph for the read that keeps the
registered entry's qualifiers (most of the pooled margin accrues on the
covered positions; the union's margin is not confined to the unseen
keys; where the margin sits is budget-dependent), the row's headline
numbers, and header and overview clauses. The README's counts are
re-derived from the tree and dated. CONVENTIONS gains two bullets from
the lane's lessons (straddle wording belongs in the registration block,
recorded as a lesson not yet a convention; the critic's "what would
change my mind" check is run when cheap, a standing practice) and
levelled counts. No research text changes.

Proved: every number in the generated regions emitted from the two
committed payloads and checked back by script (a positive control on
the registered status line flagged exactly its non-payload numbers);
four sideband-critic text rounds (two NO-GO on sentences, every blocker
and accepted advisory applied by reverting and regenerating, then GO
twice; about 181 numbers checked cell by cell, 0 decimal misquotes); a
fresh reader of the arc section alone answered where the margin accrues
correctly; line endings preserved per file; 528 passed / 5 skipped;
ruff and the findings lint clean; audit, integrity and reflect clean.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 9130d16 2026-10-02 docs(memory): log the stratified read's lane and its landing footguns

````text
The row records the whole lane of the stratified coverage read in one session: registration through three critic rounds, the freeze, the registered runs, the recompute round and clean-clone rerun, the generated landing texts through two more rounds, and the landing commit; SHARP_EDGES gains the three footguns the generated landing exposed and CONVENTIONS the generated-landing practice.
The next session picks up R2, a free baseline whose encoding handles unseen and sparse keys, through the same lane, or the derived-ledger levelling as a docs lane.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 09e846b 2026-10-02 feat(prefetch): land the stratified coverage read of the twin's margin

````text
Both registered runs from the clean freeze read FALLBACK-LOCATED /
PT-SURVIVES, the replication agreeing; the stratified rows reproduce
the twin's committed state rows to the integer and the pooled margin
equals the twin's. Both gates straddle the +0.05 floor: on positions
whose token keys the train tables saw the equal-dims margin sits just
below the floor with the floor inside its CI, on positions with an
unseen key it is large and clear, and with the forward's stored output
summaries in both arms the twin's two readings both read SIGNAL with
the equal-dims CI across the floor. So the coverage caveat is indicated,
not settled, and the twin's verdict with p_t is not settled at this
power; no stage-2 sentence follows. Keys seen once or a few times in
train read above the floor while well-covered keys do not, a reported
pattern.

The landing adds the second dated status line under the finding, the
block's OUTCOME with both predictions scored, dated pointers on every
text that carries the caveat (five sites and three derived ledgers), a
landing test that fails rather than skips on missing evidence, and the
new instrument in the frozen closure (eleven files, eight attested).

Proved: 528 passed / 5 skipped on the landing tree before two docs-only
fix batches, whose touched tests re-ran green; ruff and the findings
lint clean; sideband-critic recompute at discrepancy 0.0 over 53,116
values, a clean-clone rerun byte-identical, a landing-text round and
its confirmation (every objection applied, 804 numbers checked, 0
misquotes); audit, integrity and reflect clean.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## fea2431 2026-10-02 feat(prefetch): register the stratified coverage read

````text
The free-bigram twin's SURVIVES label carries a coverage caveat: an
unregistered diagnostic put the material part of its pooled margin on
positions whose token key the train tables never saw. This registers
the read that settles it before any number is read: the twin's own
readers, taken verbatim from its committed payload, evaluated on the
test bigram positions split into six train-coverage strata, with a free
block of the forward's stored output-distribution summaries beside them
in both arms. Branches, consequence sentences, floor-straddle wording
and both predictions are pinned in the blueprint block; the instrument
imports the frozen twin by bare module name and refuses a modified one;
the two state-file negations and the open-questions note are added.

Proved: 525 passed / 5 skipped; ruff and the findings lint clean; three
sideband-critic rounds (two NO-GO on text with every blocker applied,
then GO), each with an independent recompute of the disclosed smoke at
discrepancy 0.0; both frozen instruments byte-unchanged.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## eb0154d 2026-10-01 docs(memory): log the ledger session and the handoff-gap footgun

````text
The row records the fourth session (derived ledgers levelled with the record, three critic rounds to GO, no new finding) which died before its handoff, and the fifth session's retroactive handoff; SHARP_EDGES gains the footgun with its oracle.
The next session picks up R1, the stratified covered-vs-fallback test read with the p_t-summary free arm, registered with its branches before any read, then R2 before any GPU.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 28c110f 2026-10-01 docs(ledger): index, changelog and glossary through F-26 and the twin

````text
The derived reading aids stopped at F-23 and the 2026-09-05 release cut
while FINDINGS.md runs to F-26 with a 2026-10-01 status line. This
brings them level with the committed record. docs/FINDINGS_INDEX.md
gains the F-24, F-25 and F-26 rows, two arc sections (the full-free
re-tests; OQ-9 stage 1 with its free-bigram twin), dependency bullets
and the dated status wording on the F-15..F-18 rows. CHANGELOG.md gains
dated sections for every commit since the release cut. docs/REPORT.md
carries a dated note for F-26 and the twin on its record-boundary line
and its economics row. docs/GLOSSARY.md updates the F-N / OQ-N ranges,
the K-2 and K-6 rows and the OQ-9 row, and adds OQ-17..OQ-19. README.md
updates its entry counts. FINDINGS.md's derived index table gains the
F-26 row: one inserted line, no entry text touched. No new finding and
no F-27: the twin's registration pinned a dated status line under F-26
as its only consequence.

Proved: tools/lint_findings.py OK (27 findings); the full suite 508
passed / 5 skipped; three sideband-critic rounds (diff mode; recompute
on the FINDINGS.md row with every prefetch state file reproducing its
payload at discrepancy 0.0; a scoped confirmation) ending GO, every
blocking and advisory item applied; every number copied from the
entries and payloads; line endings preserved per file.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f8fc727 2026-10-01 test(instruments): guard the OQ-19 draft refusal, pin the encoding rule

````text
Follow-up to the code-reviewer's pass on this session's diff (APPROVE,
one WARN): the OQ-19 draft's run guard had no test, so two CI-safe
tests now exercise it (main() refuses with the defaults while
DRAFT_UNFROZEN is set; the flag is tied to the absence of the
registration block in docs/BLUEPRINT.md, so the freeze must flip both).
The free-bigram tests gain the encoding-selection rule (ties keep the
previous-token table; each arm read at its own lambda) and the three
header-only refusals of --conclude-from; the landing test re-derives the
encoding from the val table under every numpy. CONVENTIONS records the
three test-docstring forms and the one cross-test fixture import; the
suite count quoted in README, CONVENTIONS and SHARP_EDGES is re-measured
(513 collected). The frozen instruments are untouched; their nits are
listed as follow-ups in the goal snapshot.

Proved: the three test files 45 passed / 2 skipped; the critic-lane and
doc-claims witnesses pass; ruff clean; collect-only prints 513.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## edb95f5 2026-10-01 docs(memory): record the free-bigram twin landing and the OQ-19 draft

````text
The session-log row records the reconciled OQ sequence, the three research commits (OQ-19 unfrozen draft, the free-bigram twin's registration and its SURVIVES-with-coverage-caveat landing), the critic arc and the docs refresh. The next session picks up the stratified covered-vs-fallback test read or EVID-1; the OQ-19 decision stays the operator's.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5760b3b 2026-10-01 docs(harness): refresh conventions and sharp edges after the twin landed

````text
Twenty-one anchored corrections from the docs-maintainer's audit of this
session's three commits: the frozen-instrument entry now says three
instruments are sha-pinned and records a new footgun (the free-bigram
tool checks its parent's sha at import, so one byte edit to
run_prefetch_readouts.py aborts the whole pytest collection, not two
files); suite and state-file counts re-measured (509 collected, 45
tracked state files, 13 run_*.py tools, 18 flat test files); the OQ-19
files are tracked, so the "untracked" premises in CONVENTIONS and the
dirty-attestation entry are rewritten; the new import chain, the LF
evidence writer and the DRAFT_UNFROZEN guard recorded as single
instances, not conventions; TASK_RECIPES gains the frozen-closure step
a landing owes; README's test counts; the OQ-19 draft's owed list
gains the CRLF attestation hazard as item 7.

Proved: the critic-lane and doc-claims witnesses and the evidence test
pass (12 passed); findings lint OK; a scoped critic pass on the two
record-surface files (README counts, the draft's item 7).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 6eaabf4 2026-10-01 feat(prefetch): land the free-bigram twin, SURVIVES with a coverage caveat

````text
Both registered runs of the free-bigram twin landed from the freeze
commit d55e62f (primary seeds 0..7, replication seeds 8..11; payloads,
metas and state files committed as evidence). With the equally free
previous token in the baseline at equal dims, the address block still
reads +0.0609 / +0.0659 over the free bigram block at B = 16 and the
address stream +0.0661 / +0.0705 over the free bigram, both CI-clear
above the +0.05 floor: label SURVIVES on both harvests, the free
previous token accounting for 0.41 / 0.39 of F-26's +0.10 margin. The
critic's prediction (a drop to the floor) failed; the assistant's
modal label (COMPLEMENTARY) missed, its named alternative occurred.

Carried on every text as a caveat, not a label change: the material
part of the surviving margin sits on positions whose token key the
train tables never saw (covered-position D_eq below the floor in an
unregistered val-only diagnostic; the floor cleared on 16 / 17 of 30
test prompts), so nothing reads it as context or as sideband-premise
support, and the stratified test-split read is the next rung. B = 32
readings are below the floor. F-26 gains a dated status line; the
stage-1 OUTCOME, OQ-9, P1, README and K-6 gain dated pointers; the
instrument joins the frozen closure (ruff, CLAUDE.md, conventions).

Proved: the critic recomputed every table, delta and label from the
two state files to a maximum discrepancy of 0.0 (1,993 values per
harvest) and checked 446 quoted numbers with no misquote; three
blocking objections and the advisories applied in one batch; a scoped
second pass checked 659 numbers with no misquote and its one objection
(a mechanism claim the diagnostic never measured) was reworded out;
landing test pins labels, shas and the freeze commit; targeted suite
102 passed; findings lint OK; ruff clean.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d55e62f 2026-10-01 feat(prefetch): register the free-bigram twin of F-26's margin

````text
Pre-run registration (a dated amendment to the OQ-9 stage-1 block in
docs/BLUEPRINT.md) of the post-hoc diagnostic the F-26 landing critic
named: put the equally free previous token into the free baseline at
equal dims and re-read ADDRESS-BEYOND-TOKEN on both S3 harvests. The
new tool tools/run_prefetch_bigram.py imports the frozen stage-1
instrument by module name and refuses a modified one, re-trains every
arm on the bigram positions (t >= 1) from one Gram, selects the free
encoding of the previous token on val, and recomputes its labels from
its state file. Gate D_eq = history_tok - FREE_BIGRAM beside D_add =
HISTORY_BIGRAM - FREE_BIGRAM; labels FREE-HISTORY / COMPLEMENTARY /
SURVIVES / READER-INCONSISTENT / REMEASURE-INVALID; both predictions
pinned before any read; NON-CRITERION with one pinned consequence, a
dated STATUS line under F-26. State files negated in .gitignore; a
dated note under OQ-9 in the ledger.

Proved: 18 tests in tests/test_prefetch_bigram.py; the smoke on
replication shard 8's val prompts recomputed exactly by the tool and
independently by the critic (max discrepancy 0.0); the critic's design
round applied (one blocker on the pinned wording, ten advisories);
frozen instrument sha unchanged; ruff clean; findings lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 0a29d83 2026-10-01 docs(oq19): land the oracle-ceiling registration draft as unfrozen

````text
The OQ-19 registration block drafted on 2026-09-06/07 (rebuilt from
that session's transcript) and its three instrument files are
committed as a DRAFT: no block in docs/BLUEPRINT.md, no freeze commit,
nothing of OQ-19 has run. docs/OQ19_ORACLE_CEILING_DRAFT.md holds the
block verbatim with a status header and the list of what a freeze
would still owe; the instrument's main() refuses to run while its
DRAFT_UNFROZEN flag is set and stamps any payload UNFROZEN DRAFT; the
module docstrings carry DRAFT banners. The OQ-19 ledger entry gains a
dated status note; the sharp-edges entry about the untracked files is
removed and the work-outside-git entry dated.

Proved: tests/test_fullfree_oracle.py 11 passed / 2 skipped; the
critic lane witness passes; git grep finds no OQ-19 block in
BLUEPRINT; the tool's run refusal exercised by hand.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8f96ea5 2026-10-01 docs(memory): record the finished harness setup and its review arc

````text
The session-log row records the seven setup decisions landed, the three review lanes and three critic rounds that gated them, the two commits and the two new ledger rows; the decision and pattern tables gain the rows the next session should not re-litigate.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## ab12cbd 2026-10-01 chore(harness): finish initialisation and close the owed setup list

````text
Set the adopter config, lint policy and harness references the first
preflight needs, close the findings-lint blind spot, and record what
this lane measured.

- espalier.toml keeps the plan gate everywhere it applies
  (plan_exempt_prefixes = []): an unplanned edit under src, tools,
  experiments, results or data is what the lane exists to prevent.
- pyproject.toml configures ruff to pyflakes only, excludes the
  harness-owned tools/cc tree and the nine frozen-instrument files
  outright (force-exclude), adds ruff to the dev extra, and sets pytest
  pythonpath to src so a clone tests its own tree instead of whichever
  checkout the global editable install points at. Three remaining
  unused imports carry a line-level noqa.
- tools/lint_findings.py requires a cited source path to be tracked by
  git, not merely present, and resolves the citation forms the findings
  log uses: brace shorthand, parenthesised tokens, bare file names after
  a cited path, data/ and tools/ prefixes. It reads existence-only
  without git and fails under CI without it. Eighteen new tests cover
  it.
- CLAUDE.md gains a harness section (lane order, the gate's exact scope
  and exemptions, per-machine hooks, harness docs, managed bodies,
  frozen instruments); tests/test_harness_doc_claims.py holds the gate
  list and the frozen closure against the hook and the payloads.
- docs: SHARP_EDGES entries rewritten for what this lane fixed and
  measured, out-of-tree numbers labelled; CONVENTIONS, CONTRIBUTING,
  README, REPRODUCE, METHOD and the FINDINGS header updated for the
  lint contract and the suite counts; the critic agent body notes the
  import binding.
- Forward ledger: the seven onboarding rows struck through the ledger
  verb (the last one by this preflight); a new class and row for the
  sha-cited files outside results/ that do not reproduce on a fresh
  clone, and a hygiene row for the five marked unused imports, each
  with a probe.

Proved by: ruff check . exits 0; reflect-deep exits 0 with no gaps or
orphans; audit and integrity verify pass; the findings lint reads OK
over 27 findings resolving 296 paths; the lint, witness, lane and
evidence tests pass; the full suite passed on the final tree (483
passed, 5 skipped in 3:59); three critic recompute rounds, a code
review and a failure-mode review, with their accepted findings landed
as three batches.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d614666 2026-10-01 fix(results): store results bytes as checked out and as cited

````text
84 of the 408 tracked files under results/ were CRLF on disk and LF in
the index while git status read clean: the index stat cache had not
been refreshed, so a fresh clone wrote the LF bytes (verified in a
scratch clone). Three of the 84 are cited by their on-disk sha256 in 28
tracked files under four provenance keys, and no LF sha is cited
anywhere, so every fresh clone broke those 28 chains. The other 81 are
cited by nothing; for them the change records the bytes as regenerated
on this Windows box (the writers use text mode without newline=).

results/** already carries the -text attribute. git add --renormalize
stored the on-disk bytes: every blob changed by line endings only
(recomputed old against new after LF normalisation), the index equals
the disk for all 84, and no disk byte or number changed. The new
tests/test_evidence_bytes.py pins results/ over tracked files only:
every tracked results file hashes unfiltered to its index blob; no
tracked text file cites the sha of a results file's other line-ending
twin; and no results file is cited fewer times than at HEAD, so a
regenerated, edited or deleted cited file is named with both counts.
Scope is results/ only: twelve sha-cited files under data/, tools/ and
docs/ have the same exposure and are filed as a forward-ledger row for
their own lane.

Proved by: in a scratch clone the old HEAD fails the twin scan on 28
citations, the committed state passes, one file put back as its LF
blob fails on 7, and after a scratch commit a one-byte change and a
deletion of a cited file each fail naming the file; the critic
recomputed the renormalisation and the citations in three recompute
rounds, maximum discrepancy 0.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5db262d 2026-10-01 docs(memory): record the espalier trial's grounding and critic lane

````text
The session-log row records what this session established: the docs
grounded on the tree, the sideband critic adopted as a review lane, the
commit convention switched to the harness format, and the standing rule
that no subagent runs on Fable without permission. The next session
picks up the owner's decisions on the owed list in the goal snapshot.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c20dce4 2026-10-01 feat(harness): adopt the sideband critic as a review lane

````text
Give the project's adversarial reviewer a harness-style agent header
(tool allowlist without Write, model pinned to opus) and a /critic
skill that dispatches it under one mode rule: recompute when the scope
touches evidence or the findings log, diff otherwise. Wire it into the
preflight, implement-task and implement-pack reviewer steps as a third
lane that fires on its own research-record surface, held as one
canonical list, under the same dispatch-together and edit-freeze rule;
a blocking objection is a no-go. Preflight also runs the findings lint,
a hard stop only when the findings log is in the diff. A new test
asserts the lane, the list, the unmanaged files and a pinned non-Fable
model on every agent, so a harness re-init that drops the lane goes
red. The decisions and the re-init hazard are recorded in the memory,
recipe and sharp-edges docs.

Proved by: harness audit and integrity verify pass; the lane test
passes; the full suite is green; both harness reviewers' findings
landed as one batch.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 918cc9c 2026-10-01 docs(harness): ground conventions and sharp edges on this tree

````text
Replace the two espalier seed placeholders with what the repository
actually does, measured on 2026-10-01: layout and import direction,
naming, instrument-script shape, refusal patterns, test shape, code
style and the evidence pattern, plus fifteen sharp edges this tree and
this box actually have. Records the commit-convention decision: from
this commit on, the branch follows the harness's conventional format.

Proved by: every cited anchor and count re-derived from the tree;
findings lint OK; suite green (counts in the handoff).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## f1aabe4 2026-09-30 Espalier trial: deploy espalier-harness (engine at main 2cb371b) on a branch

````text
Files written by 'espalier init .' only (workflow profile): .claude agents,
commands, skills, workflows; tools/cc hooks; seeded docs, memory, cc, and
the forward ledger with seven onboarding rows; .gitignore harness block.
No source, test, result or existing doc touched; CLAUDE.md kept as is.
Suite before commit: 453 passed, 5 skipped (matches F-26).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## c23f214 2026-09-15 F-26: OQ-9 STAGE-1 PREFETCH READOUTS landed (two critic rounds: recompute from both state files to 0.0 over 1599 triples per harvest; 412-number text check): PREFETCH-HEADROOM on the primary S3 harvest, the seed replication agrees on every label; HISTORY +0.2867 / +0.2901, ADDRESS-BEYOND-TOKEN +0.1032 / +0.1072 at B=16 over the free ONE-TOKEN table (below the +0.05 floor at B=32), INTRA-FORWARD +0.4861 / +0.4816, DRAFT ceiling +0.1556 / +0.1545; CACHE-SUFFICIENT and the P1-window kill did not fire; prediction: 3 clauses held in full, the HISTORY-arm and ADDRESS-BEYOND-TOKEN magnitude sub-clauses MISSED-HIGH, (iv) partial; the critic's blocking objection on interpretation (the equally free previous token is not in the baseline and gate 0 routes on it) carried as a SCOPE sentence on every label-bearing text, the equal-dims free-bigram twin named as the unrun, unregistered next rung; NON-CRITERION, K-6 stays UNTESTED; payloads + state files + tests/test_prefetch_landing.py committed (453 passed / 5 skipped; lint OK, 27 findings)

````text
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c4c4511 2026-09-15 OQ-9 STAGE-1 PREFETCH READOUTS: registration + instrument (pre-run; NON-CRITERION; critic-gated: three design passes + a final confirmation, every smoke recomputed from its state file to 0.0)

````text
- docs/BLUEPRINT.md: the registration block. P1 (i)-(iii) re-indexed to the forward each token feeds (S[t+1] is the routing of the forward the free bonus token tokens[t] feeds; the draft cell sits at horizon 2 with the true tokens[t+1] as the D-2 ceiling draft); free input-token arms FREE_TOK / HISTORY_TOK / FREE_TABLE on a train token table read leave-one-prompt-out; the ADDRESS-BEYOND-TOKEN reading (the D-5 analogue for prefetch) and a sideband sentence that follows it alone; recency / marginal baselines at budgets 8 / 16 / 32; intra-forward prefetch at leads 1 / 2 / 4; a reported-only front-loading curve; labels CACHE-SUFFICIENT / PREFETCH-HEADROOM / PREFETCH-NOT-SHOWN / INCOMPLETE; honest prediction pinned; four disclosed smokes on replication shard moe_s8 VAL prompts only; the primary shards and both TEST splits unread.
- OPEN_QUESTIONS.md: OQ-9 dated note (stage 1 registered; the steer half PARKED: no actuator in the record converts); the OQ-19 "5 x 210" line annotated in place (8 x 210).
- docs/FUTURE_IDEAS.md: P1 dated correction (eight shards, not five; (iii) as written was mis-indexed; the residency budget the kill rule lacked). [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
- tools/run_prefetch_readouts.py (numpy only; nothing imports torch; --conclude-from is the exact recompute surface) and tests/test_prefetch_readouts.py (16 tests).
- .gitignore: results/real/prefetch_s3{,_r}.json.state.jsonl are evidence.

Suite 450 passed / 5 skipped; lint OK (26 findings). Nothing registered has run. The OQ-19 files stay untracked and OQ-19 is undecided.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## fa6537e 2026-09-14 F-25: OQ-18 COARSE-LABEL FULL-FREE RE-TEST landed under the 2026-09-07 rider amendment (two critic recompute rounds from the state files, max discrepancy 0.0): S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2 ABSORBED, S3 L3 SPLIT at the registered reader; prediction 3/4 held on labels with the pinned sub-clauses scored in F-25; amended rider leg passed at all eight cells, the registered raw leg reported (above its band at S1 L3 and S1_r L2); dated errata / STATUS / K-2 lines executed as pinned; the pinned disclosure on every label read

````text
- results/real/fullfree_coarse_{s1,s1_r,s3,s3_r}.json + .state.jsonl (evidence; every payload attests 3ec1064-dirty over exactly the licensed S1 state-file append, git_status_licensed true; amended instrument aafd3ae8... importing the frozen instrument byte-identical at 5efa7063...; resume plan as written: S1 resumed 30 / retrained 6, S1_r fresh, S3 and S3_r resumed 69 / retrained 6; moments == committed OQ-17)
- results/real/fullfree_coarse_s3.rider_v1.json, fullfree_coarse_s3_r.rider_v1.json (the frozen-instrument S3 payloads, preserved at the recorded shas 8fc04f27... / 33e73c08..., NEVER concluded; no v1 label read)
- labels read only through tools/run_fullfree_coarse_amended.py --conclude-from (refuses v1 payloads and unlicensed attestations; carries the disclosure): S1 L2 gate D +0.0011 [-0.0001, +0.0023] / +0.0006 [-0.0007, +0.0020]; S1 L3 +0.0010 [-0.0006, +0.0026] / +0.0012 [-0.0015, +0.0040]; S3 L2 +0.0018 [+0.0008, +0.0030] / +0.0003 [-0.0009, +0.0013]; S3 L3 +0.0041 [+0.0026, +0.0055] / +0.0053 [+0.0019, +0.0091] with Mt +0.0010 [-0.0012, +0.0030] / -0.0014 [-0.0041, +0.0016] and Mn_r -0.0031 [-0.0053, -0.0010] / -0.0067 [-0.0090, -0.0042] (the replication fire is carried by the corrected twin's own CI-clear cost; post-hoc reading in F-25, unregistered, licenses nothing)
- riders: amended dE_br S1 L2 +0.0005, S1 L3 +0.0026 (= the diagnostic's seed-0 value), S1_r L2 -0.0005, S1_r L3 -0.0017, S3 L2 +0.0001, S3 L3 +0.0007, S3_r L2 +0.0001, S3_r L3 +0.0007, none failing; registered raw leg 2 +0.0132 at S1 L3 (the fire) and +0.0105 at S1_r L2 (under the frozen rider the S1 replication would also have halted, at L2), within the band elsewhere
- FINDINGS.md: F-25 entry (with '- amendment:' rider report / attestation / process note and '- post-hoc reading:' lines) and scorecard row; dated bullets on F-15 / F-16 / F-17 / F-18 and their scorecard cells; docs/WHY_THIS_DIES.md K-2 STATUS block; docs/REPORT.md row; README.md existence-row note; OPEN_QUESTIONS.md OQ-18 OUTCOME (CLOSED; plan of record proceeds to OQ-19); docs/BLUEPRINT.md OQ-18 OUTCOME block — all dated additions, no registered text rewritten (texts generated by scratchpad fill_oq18.py / render_f25.py / add_landing_notes_0914.py from the payloads and conclude outputs)
- tests/test_fullfree_coarse.py: the committed-payload test skips amended payloads by a dated note (its resumed_cells == 0 clause was waived by the amendment); tests/test_fullfree_coarse_amended.py: test_committed_amended_payloads_reproduce_their_conclusion (resume plan, licensed attestation, v1 preservation shas, the raw-leg-above-band set, the four landed labels, v1 refusal)
- every L3 sentence carries the pinned lens qualifier; the pinned ABSORBED / NOT-SHOWN consequence sentences are verbatim with (F-25) outside the quotes; the S1 L3 amended pass is stated as not CI-clear (upper +0.0054) with the diagnostic's pooled seeds 0-2 (+0.0018 [-0.0004, +0.0039]) beside it; the S1 replication halt is stated as a counterfactual with its basis (frozen grid order + SystemExit before the first unshuffled cell; all 18 retrained shuffled rows equal their frozen rows' test_acc to 0.0 in the committed state files)
- process note (disclosed in F-25): a key-scrubbed print of the S1 primary payload overran into the S1 L2 gate row before the conclude step; no label string, no v1 payload read; texts mechanical
- the untracked OQ-19 files (src/sideband/real/oracle_replay.py, tests/test_fullfree_oracle.py, tools/run_fullfree_oracle.py) are NOT part of this commit

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 3ec1064 2026-09-13 OQ-18 LEAK-RIDER POSITIVE CONTROL landed: DOMINANCE-CONFIRMED-HERE — the amended (twin-referenced dependence-excess) leg fires on a literal non-causal slots block at both spaces; the amended runs may proceed; nothing trained under the amendment yet

````text
- results/real/oq18_rider_poscontrol_s1.json + .state.jsonl (evidence; registered in docs/OQ18_RIDER_POSCONTROL.md at 5ef3ccf BEFORE it ran; registration sha ad9f018a... recorded and unchanged; HEAD 5ef3ccf clean at write time; arm dims 8192 = 8192)
- L3: E(leak) +0.3085, dE(leak - fplus_r) +0.3007 (CI95 +0.2914..+0.3106) -> amended leg FIRES; raw acc(leak) - acc(fplus) +0.2833 -> raw leg FIRES
- L2: E(leak) +0.2505, dE(leak - fplus_r) +0.2493 (CI95 +0.2360..+0.2614) -> amended leg FIRES; raw +0.0928 -> raw leg FIRES (the leak block drops the chance term from 0.3978 to 0.2414, so the raw leg understates a leak the E leg sees in full: the drift-sharpness claim, measured at this leak size)
- prediction (pinned before any control cell trained): both flags at both spaces HELD; dE >= +0.01 at both HELD; larger at L3 than at L2 HELD
- docs/BLUEPRINT.md: dated POSITIVE CONTROL OUTCOME sentence in the amendment bullet; OPEN_QUESTIONS.md: outcome line in the OQ-18 dated note (numbers written by scratchpad/oq18/apply_control_outcome.py from the payload)
- the frozen S3 payloads and state files, and the untracked OQ-19 files, remain outside this commit

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 5ef3ccf 2026-09-13 OQ-18 RIDER AMENDMENT (written 2026-09-07, committed 2026-09-13; critic-recomputed): registered diagnostic of the S1 L3 leak-rider fire read AMENDABLE / TWIN-MATCHED; leg 2 amended to the twin-referenced dependence-excess leg at all four harvests (post-hoc reroute around a fired kill condition, disclosed); amended instrument as a new file; S1 state file committed at the fired sha; POSITIVE CONTROL registered (unrun); nothing trained under the amendment yet

````text
- docs/OQ18_RIDER_DIAGNOSTIC.md (registration of the diagnostic, byte-identical to the sha the payload records: 4f7d3feb...; pre-round sha 1904dd62... recorded in its last section)
- tools/run_oq18_rider_diag.py, tests/test_oq18_rider_diag.py (the committed-payload test now runs)
- results/real/oq18_rider_diag_s1.json + .state.jsonl (evidence; .gitignore negation added): 16 cells, resumed_cells 2 under the documented pre-round stop; verdict AMENDABLE / TWIN-MATCHED / no qualifiers / tie registered-run; raw leg 2 +0.0132 / +0.0136 / +0.0141 at seeds 0-2; dE_br pooled +0.0018 (CI95 -0.0004..+0.0039), seed 0 +0.0026 (CI95 -0.0004..+0.0054); dE_bf pooled +0.0045 (CI95 +0.0001..+0.0090); X_raw seed 0 +0.0006; L2 seed 0 dE_br +0.0005 (CI95 -0.0001..+0.0011); every number recomputed by the critic from the state file to 1e-12
- results/real/fullfree_coarse_s1.json.state.jsonl (36 rows: the fired run's record, sha a563decd...; the amended resume appends to it, the one licensed tracked modification)
- docs/BLUEPRINT.md dated amendment bullet (before "## Eval protocol"); OPEN_QUESTIONS.md OQ-18 header status + dated note. Disclosed there: the six-day gap between writing and commit; the S3 replication v1 payload's 15c4e9c-dirty attestation over the three then-uncommitted documentation files (a deviation from the registration's "later HEAD, clean tree" expectation); the amended instrument drafted before the verdict was read; ERRATUM 33 -> 30 reused L2 cells; the pre-commit critic round's items
- tools/run_fullfree_coarse_amended.py, tests/test_fullfree_coarse_amended.py (imports the frozen instrument, byte-identical at 5efa7063...): start-up guard tolerates exactly the licensed S1 state-file append; git_status_licensed recorded; --conclude-from refuses a payload attested over anything else; disclosure carries the dominance sentence and labels X_raw as the S1 diagnostic's
- docs/OQ18_RIDER_POSCONTROL.md, tools/run_oq18_rider_poscontrol.py, tests/test_oq18_rider_poscontrol.py: registered positive control (fplus ++ the same row's slots at the shuffled label's own position; the amended and raw legs applied; DOMINANCE-FALSIFIED withdraws the amendment), pinned and committed BEFORE it runs; .gitignore negation for its state file
- the frozen S3 payloads and state files, and the untracked OQ-19 files, are NOT part of this commit

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 15c4e9c 2026-09-06 OQ-18 COARSE-LABEL FULL-FREE RE-TEST: registration + instrument (pre-run; critic-gated; plan of record OQ-18 -> OQ-19 -> assess)

````text
Plan of record set 2026-09-06 by the user after the F-24 close: re-test
F-15 / F-17 at the coarse label spaces L2 / L3 against the full free
baseline first, then the oracle-intermediate ceiling (OQ-19), then
assess. This commit is the FREEZE for item 1; no registered cell has
run. docs/BLUEPRINT.md gains the "OQ-18 COARSE-LABEL FULL-FREE RE-TEST
REGISTRATION" block (why: the L2 / L3 margins over the 657-summary
proxy are the largest in the record and grow with coarse-graining,
S3 L3 off2 +0.0721 / +0.0730, all linear cells, untested against the
full free baseline; arms fplus / fplus_b / fplus_r with the corrected
prompt-level-deranged twin as the registered twin; fresh (a) cells at
mlp256; offsets bound per space to the both-harvest firing sets; a
per-space leak rider with a fresh shuffled (a) reference; a THREE-leg
reader-validity precondition whose third leg, fplus at mlp256 against
the committed linear (a), refuses a reader collapsed to the constant
predictor; gate off2 / mlp256 D under the Phase-3 triple rule; labels
per (source, space) from both harvests; the license full only with Mt
and Mn_r CI95 uppers >= 0; helps-direction readings; consequence rules
per label; honest prediction S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2
ABSORBED, S3 L3 SURVIVES with D +0.005..+0.020; three smokes disclosed;
the pre-run critic round recorded). OPEN_QUESTIONS.md gains OQ-18 and
the OQ-19 outline (its registration block is owed before its harvest
launches, after OQ-18 is read); docs/FUTURE_IDEAS.md gains P8 (S2 with [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
the drafter-attention free twin) and P9 (same-model union).

Instrument tools/run_fullfree_coarse.py imports the OQ-17 blocks and
the OQ-17 corrected twin (never re-implemented), asserts the hz
moments sha against the committed OQ-17 payload of the same harvest,
refuses a grid colliding with committed cell ids or missing a committed
linear base at any registered (space, offset, seed), enforces the
fresh-state pin and refuses --only on registered outs. tests/
test_fullfree_coarse.py: 10 tests + the committed-payload check (skips
until the payloads exist). .gitignore negates the four state files.

Pre-run critic round (recompute mode): every WHY number reproduced from
the committed payloads; three blockers applied (the S1 L3 lens
qualifier corrected to one mega-group of 455/510 with all 165
zero-degree concepts; the Mf_x collapse leg added; the clean-fire
license rule added), seven conditions and the notes applied as
recorded in the block. Suite green; lint OK.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## d68aaad 2026-09-06 FUTURE_IDEAS: post-F-24 launching-point entries P1-P7 (user-proposed 2026-09-06) + OQ-9 / OQ-11 dated notes; idea-tier, nothing registered, nothing run [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]

````text
Records the two conceptual pictures raised after the OQ-17 close and maps
them onto known cells: (1) execution-checked relaxed acceptance with the
slow model as a stimulus rather than a verifier; (2) the inverted
architecture in which the big model consumes the calculation of a small
compressed model on non-HBM memory. Each entry carries prior art
(recalled, ids to verify), the repo assets it reuses, the cheapest first
readout, a kill condition and a cost tier: P1 expert-prefetch readouts on
the existing OLMoE router harvest (the OQ-9 first step and the OQ-11
front-loading curve; CPU-only), P2 free actuator V vs O (frozen Stage-A
arms; own dated registration per F-23), P3 stale-stimulus ladder, P4
layer-split self-speculative drafting across memory tiers, P5
execution-checked relaxed acceptance, P6 proxy-tuning logit delta, P7
calibrated cascade. A framing note pins the three channels by which a
small model can help a big one (time, cost, a tuned delta) with
layer-split reuse as the exception, and an easiest-to-run ranking names
the OQ-17 stronger-reader re-test as the only unrun item that still
bears on the sideband thesis. Docs only; suite 385 passed / 1 skipped;
lint OK (25 findings).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 0b82e98 2026-09-06 F-24: OQ-17 FULL-FREE EXISTENCE RE-TEST — F-15 and F-17 margins ABSORBED by the full free baseline at the registered reader (both sources, both harvests); corrected-twin diagnostic TWIN-ROBUST at both sources; prediction failed on both sources; dated errata on F-15 / F-17, K-2 STATUS, F-16 / F-18 notes

````text
Registered labels (tools/run_fullfree.py --conclude-from, mechanical): S1
ABSORBED (horizon OFF3-ABSORBED), S3 ABSORBED — at the registered reader
at the registered budget, at the pinned L1 offset-2 cells (S1 also
offset 3). Gate D = acc(fplus_b) - acc(fplus_n) at L1/off2/mlp256:
S1 +0.0002 [-0.0012, +0.0015] / +0.0012 [-0.0003, +0.0028]; S3 +0.0003
[-0.0013, +0.0020] / +0.0001 [-0.0019, +0.0021]; every D row's CI95
upper below +0.005 on every harvest (max +0.0029). Mt = acc(fplus_b) -
acc(fplus) beside it: S1 +0.0034 [+0.0021, +0.0048] / +0.0033 [+0.0012,
+0.0052]; S3 +0.0033 [+0.0013, +0.0054] / +0.0013 [-0.0008, +0.0035] —
CI-clear on three of four harvests, below the +0.005 floor at the point
on all four, so the licensed sentence is "no MATERIAL equal-dims
margin", never "no margin". The full free baseline ((a) ++ hashed
top-32 ids ++ z-scored h_a) beats the 657-summary proxy by +0.018..
+0.037 at the gate and beats the committed (a)+(b) telemetry arm
outright at mlp256 on three of four harvests. Reader valid and both
rider legs pass everywhere; resumed_cells 0.

Post-hoc, non-criterion TWIN-INERTNESS DIAGNOSTIC (registered 675a8f6
before any registered twin cell ran; tools/run_fullfree_twin.py): the
registered shift twin had been found non-inert (it reads the same row
17 positions ahead, beyond the label position for ~94% of anchors; Mn
CI-clear +0.0033 / +0.0030 on the primaries). The prompt-level
corrected twin reads TWIN-ROBUST at both sources — D_r S1 +0.0002
[-0.0009, +0.0014] / +0.0013 [-0.0002, +0.0028], S3 +0.0000 [-0.0014,
+0.0014] / +0.0008 [-0.0014, +0.0029] — and itself gains CI-clear over
the base on three of four harvests (Mn_r +0.0032 / +0.0020 / +0.0033 /
+0.0005) with T at zero everywhere, so under the pinned CORRECTED-TWIN-
HELPS reading the label-consumption mechanism is withdrawn there: at
this reader any of the three same-marginal sparse blocks tested adds
+0.0005..+0.0034 and the aligned block carries no material margin
beyond either twin — the strongest form of the null. The diagnostic's
own pinned prediction (S1 TWIN-DEPENDENT) failed in branch, Mn_r sign
and T. The per-cluster correlations recorded in the twin payloads are
a shared-subtrahend artifact and license nothing (post-run critic
recompute; dated note in the OUTCOME block).

Both honest predictions failed: S1 was predicted to SURVIVE with D
+0.005..+0.012, S3's ABSORBED was called unlikely; the D CIs are about
half the Phase-3 (b)-(a) widths because the twins share most dims and
the seeded init, and the non-inert twin drove D to zero by subtraction.

Consequences executed exactly per the pinned rules, dated, never
rewrites: F-15 and F-17 dated errata scoped to the re-tested cells (S1
L1 offsets 2-3, the off3 leg resting on the registered twin only; S3 L1
offset 2 — L2 / L3 and further offsets stand against the proxy,
untested against the full free baseline); K-2 STATUS (2026-09-06) per
source, FIRED at the probe level at the registered reader with both
scopes (reader; +0.005 materiality), stronger-reader residual named,
twin-robust disclosure — "ABSORBED at BOTH sources: the existence layer
is NOT SHOWN anywhere at the registered reader; the 2026-09-05 salvage
line is all that stands"; F-16 / F-18 dated "moot" notes; scorecard
STATUS lines; dated notes in docs/REPORT.md and README.md; OQ-17 dated
OUTCOME in OPEN_QUESTIONS.md and an OQ-17 OUTCOME block in the
BLUEPRINT. Not licensed anywhere: a SURVIVES sentence, an unscoped K-2
kill, "no margin", any relabel of the L2 / L3 / further-offset claims,
any consequence from Mc, conversion / acceptance / wall-clock claims.

Evidence: results/real/fullfree_{s1,s1_r,s3,s3_r}_twin.json + state
files (this commit; bind 675a8f6 clean, instrument sha recorded) and
the four registered payloads committed at 675a8f6. Critic rounds, all
recompute mode, all before this text: S1 pair, S3 pair, twin pre-run
review, twin post-run recompute of all four payloads — every payload
number reproduced from the state files to 0.0. The S3 replication
parent payload's 1d1a7f8-dirty attestation (docs-only dirt written
mid-run; tools/src/tests unchanged) is disclosed in F-24. Suite green;
lint OK (25 findings).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 675a8f6 2026-09-06 OQ-17 registered runs landed (S1 and S3 both ABSORBED at the registered reader; finding text withheld) + POST-HOC TWIN-INERTNESS DIAGNOSTIC registration (pre-run; critic-gated)

````text
Evidence: the four registered OQ-17 payloads and their sha-header-bound
state files (results/real/fullfree_s1.json, fullfree_s1_r.json,
fullfree_s3.json, fullfree_s3_r.json + .state.jsonl), all run from
1d1a7f8 with resumed_cells 0, partial false, both rider legs passing and
the reader-validity precondition holding on every harvest. The
registered mechanical conclusion (tools/run_fullfree.py --conclude-from)
is ABSORBED for S1 (horizon OFF3-ABSORBED) and ABSORBED for S3: the
gate D = acc(fplus_b) - acc(fplus_n) at L1/off2/mlp256 is +0.0002
[-0.0012, +0.0015] / +0.0012 [-0.0003, +0.0028] on the two S1 harvests
and +0.0003 [-0.0013, +0.0020] / +0.0001 [-0.0019, +0.0021] on the two S3
harvests, with every D row's CI95 upper below +0.005 (max +0.0029); Mt =
acc(fplus_b) - acc(fplus) beside it is +0.0034 [+0.0021, +0.0048] /
+0.0033 [+0.0012, +0.0052] (S1) and +0.0033 [+0.0013, +0.0054] / +0.0013
[-0.0008, +0.0035] (S3). Two critic recompute rounds (one per source)
reproduced every payload number from the state files to 0.0. The pinned
honest prediction failed on both sources. The S3 replication payload
records 1d1a7f8-dirty over three documentation files (this commit's twin
registration, written while that run was in flight; tools/ and src/
unchanged). NO finding text is written in this commit: the S1 critic
round found the equal-dims twin non-inert (it reads the same row's
slots 17 positions ahead, beyond the label position for about 94% of
anchors, and gains CI-clear over the base on the S1 and S3 primary
gates), so the consequence text waits for the diagnostic below.

Registration: docs/BLUEPRINT.md "OQ-17 POST-HOC TWIN-INERTNESS
DIAGNOSTIC" (+ an OPEN_QUESTIONS.md dated note), written after the S1
payloads and critic round were read and before any registered twin cell
ran; NON-CRITERION (cannot change a registered label; pins which
qualifier the consequence text carries). Arm fplus_r = fplus ++ the
slots of the same-generation-index row of a different prompt of the same
split at the same anchor index (a within-split prompt-level derangement
per train seed); the gate cell only, three seeds, all four harvests;
readouts D_r / Mn_r / T; readings TWIN-ROBUST / TWIN-MASKED (clean fires
only) / TWIN-SPLIT / TWIN-DEPENDENT / TWIN-INCOMPLETE plus a T reading;
dilution caveat, corrected-twin-helps reading, floor resolution and
multiplicity pinned; honest prediction pinned (S1 TWIN-DEPENDENT). One
pre-run critic round (four blockers applied: clean-fire rule; the draft's
row-level derangement read sibling generations of the same prompt for
3-6% of test anchors and was replaced; the instrument had to be
committed before launch; label index a+1 and two wording fixes) and two
disclosed scratch smoke cells are recorded inside the block.

Instrument: tools/run_fullfree_twin.py (+ tests/test_fullfree_twin.py,
CI-safe, no torch; the committed-payload test recomputes the three
readouts from the state files at 1e-12); .gitignore negates the four
twin state files. Suite 383 passed / 3 skipped; lint OK (24 findings).
The registered twin runs launch from this commit.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 1d1a7f8 2026-09-06 OQ-17 FULL-FREE EXISTENCE RE-TEST REGISTRATION (pre-run; critic-gated twice): can the K-2 existence margin survive the full free baseline?

````text
Registers, before any registered cell ran, the test F-23 left open on the
existence layer: F-15/F-17 measured telemetry against (a) = 657 summaries
of p_a, but F-22 DR-2 (hashed top-32 token ids reconstruct h_a as well as
telemetry) and F-23 (h_a is an exact linear function of the full p_a,
free under D-5) say that baseline was a proxy, and the registered linear
(h) arm is not a usable reader of it (at or below the majority floor on
6 of 8 harvest x offset-2/3 cells; a linear model contains the constant
predictor). Meanwhile telemetry ALONE beats (a) at offset 2 on all four
harvests (b-a mlp256 +0.0149/+0.0154 S1, +0.0100/+0.0069 S3).

Design (docs/BLUEPRINT.md block + OPEN_QUESTIONS.md OQ-17): arms fplus =
(a) ++ TOK (DR-2 rule) ++ hz (h_a clipped to the train support and
z-scored with train-split moments, sha in provenance), fplus_b = fplus ++
aligned telemetry, fplus_n = fplus ++ alignment-destroyed telemetry
(equal dims, same block order); L1/off2 at linear and mlp256, S1 adds
off3 at mlp256; seeds {0,1,2}; both harvests per source; the registered
optimizer and budget; a two-leg leak rider (shuffled fplus vs the
committed shuffled (a); shuffled fplus_b vs shuffled fplus) runs first;
a READER-VALIDITY precondition (all nine gate-cell probes hold the
floor; Mf CI upper >= 0) gates any label. Gate L1/off2/mlp256 D =
acc(fplus_b) - acc(fplus_n) under the Phase-3 triple rule; per-source
labels from both harvests: SURVIVES-FULL-FREE / SPLIT / ABSORBED (every D
CI upper < +0.005 on both harvests) / NOT-SHOWN / READER-INVALID /
INCOMPLETE, each scoped to the registered reader; Mt quoted beside D
decides the licensed SURVIVES sentence; consequence rules and an honest
prediction pinned (S1 survives with a smaller margin; S3 splits or is
not shown). CRITERION-BEARING for F-15/F-17, unlike P1.

Critic rounds before this commit (sideband-critic, recompute mode): round
1 blocked eight points (a shuffled-cell floor quoted as the floor; the
raw trainer cannot hold the constant predictor on h_a-bearing arms, so
h_a standardization + the precondition were pinned; a rider leg blind to
shared-block leaks; labeler guards; a straddle read as a K-2 kill; SPLIT
read as "stands"; SURVIVES licensed without Mt); round 2 blocked three
more (a 7-of-8 miscount, an unsourced number, the same straddle loophole
in the horizon rule, ABSORBED not reader-scoped). All applied and
recorded inside the block. Two scratch smokes under results/smoke/
(gitignored) are disclosed in the block as pre-registration contact: the
raw instrument's shuffled cells sat 3.5 points below the constant
predictor; the standardized instrument's rider legs pass and its
unshuffled fplus mlp256 seed-0 cell reaches 0.6454 (floor 0.5914;
committed (a) 0.6071, (c) 0.6360), best_epoch 0.

Instrument: tools/run_fullfree.py (+ tests/test_fullfree.py, CI-safe, no
torch); .gitignore negates the four registered state files. No
registered cell has run at this commit; the runs launch from it. Suite
green; lint OK (24 findings).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 601c210 2026-09-05 Release prep: newcomer docs + F-23 OQ-16 closure by dated erratum + status addenda + gate recompute tools

````text
F-23 (OQ-16 CLOSED BY DATED ERRATUM, TARGET-FREE): the registered
reconstruction target h_a (final-norm output at the anchor = lm_head
input) is an exact linear function of the anchor's logits and hence of
the full next-token distribution p, which D-5 defines as free. Checked on
48 pinned byproduct rows against the cached Llama-3.1-8B-Instruct lm_head
(untied, bias-free, 128256 x 4096): argmax 48/48, top-32 overlap 0.9948,
full-logit inverse relative error 2.5e-8 median (float32 floor; 1e-15
class from float64 logits), top-k log-prob recovery per-row R^2 +1.0000
(k=4097) / +0.506 / +0.216 / +0.078 / +0.014 (32); W_U full column rank,
the ones-vector direction costs nothing in conditioning, bf16 log-probs
alone recover h_a to <1% relative error. Every Stage-R and DR readout
stands as pinned; their lane meaning collapses: the stream's
reconstruction is K-2's lossy copy of free information; Stage-A telemetry
arms struck pre-GPU; arm O is a free-actuator question outside the lane
(own registration required); NO partition branch claimed (the limbo
clause forbids re-labeling a never-run stage a null; the partition's VOID
precedent applies); the lane ends; the hard stop holds. F-15/F-17 stand:
the OQ-6 h-probe (a linear probe on the full logit vector under the
identity) adds nothing over their free arm; a nonlinear-in-p free
baseline was never run. Critic round with an independent implementation
before this commit: forward numbers exact, inverse to 8 figures, k<4097
rows to 7+ digits; the k=4097 row's normal-equations artifact replaced by
an SVD solve; three sentences of the first draft blocked and rewritten.

Evidence: results/real/oq16_ha_identity.json (tools/ha_identity_check.py;
GPU-box CPU tool, never imported by CI) + tests/test_ha_identity.py.
Registered text: docs/BLUEPRINT.md "OQ-16 DATED ERRATUM + LANE CLOSURE";
OPEN_QUESTIONS.md OQ-16 closure, OQ-6 and OQ-1 dated notes; dated STATUS
addenda in docs/WHY_THIS_DIES.md (K-2, K-3, K-4..6) and docs/ECONOMICS.md
section 6a. tools/e6_gate.py + tests/test_e6_gate.py recompute the
F-19/F-21 gates from committed summaries.

Newcomer documentation set (numbers verified against committed files):
README.md rewritten; docs/REPORT.md, METHOD.md, GLOSSARY.md,
FINDINGS_INDEX.md, REPRODUCE.md, DATA.md, THIRD_PARTY.md,
RELEASE_NOTES.md, IDEAS.md (all UNREGISTERED), BLUEPRINT_INDEX.md; [withheld: IDEAS.md not in this repository; see WITHHELD.md]
CHANGELOG.md, CONTRIBUTING.md, CITATION.cff (placeholder),
data/README.md; docs/ECOSYSTEM.md without local paths. No GPU has run.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 8542ef5 2026-09-05 Release audit (code): torch skip guards so a torch-less clone is green; --smoke writes to results/smoke/ instead of over committed evidence; redact_args moved to a torch-free sideband.provenance and applied by every meta-writing tool (guard test); version 0.3.0; 'analysis' extra; HANDOFF.md gitignored

````text
Findings of the pre-release audit (fresh-clone simulation + hygiene sweep;
no secrets, emails, or hostnames anywhere in the tree or history):
- tests/test_probes.py: TestD2D3Instrument and TestStageEInstrument lack
  the torch skip guard the neighbouring class has -> 3 failures on a
  fresh `pip install -e ".[dev]"` clone (ModuleNotFoundError at
  src/sideband/probes.py lazy import). Guarded.
- experiments/run_all.py --smoke (the CI step) overwrote all eight
  committed results/e0*.json + results/summary.json in place. The smoke
  variant now writes to results/smoke/ (gitignored); the full run keeps
  its deliberate rewrite semantics, stated in the docstring.
- Four tools stored vars(args) unredacted (k3_threshold_search,
  run_error_predictor, run_posthoc_topic, run_probes). redact_args now
  lives in src/sideband/provenance.py (torch-free) and is applied at all
  nine meta-writing sites; hf_specdec re-exports it for existing
  imports; tests/test_tools_and_real.py gains a static guard test.
- pyproject: version 0.3.0 (src/sideband/__init__.py in step), readme
  field, and an 'analysis' extra declaring scipy + scikit-learn for
  tools/build_concept_groups.py (previously undeclared).
- .gitignore: HANDOFF.md (operator-local session log referenced by
  registered text; never published) and results/smoke/.
No results/ file touched. Suite green (full run, exit 0); lint OK (23).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2e44105 2026-09-05 OQ-16 STAGE-A FREEZE (pre-GPU; critic-gated): SD^2-style draft-side injection instrument — frozen drafter, rank-512 zero-init adapter on the MLP up-projections, oracle-ceiling rung A0 before the reconstruction rung A1, fresh 210-prompt verdict population with a mechanical paraphrase refusal; no GPU run exists at this commit

````text
Registration (docs/BLUEPRINT.md STAGE-A FREEZE, dated 2026-09-05, the
arc's deferred-constants amendment; written after DR-4 was read, its
DR-4-dependent sentences derived from the DR-4 registration's pre-run
MEANING clause and disclosed as such):
- Actuator = SD^2 "merged" (public code read): delta_l added to the
  drafter's up-projection output before the SiLU gate product, every
  layer; adapter LayerNorm(4096) -> U(4096x512) -> V_l(512x8192)
  zero-init. Owned deviations disclosed: rank-512 factorisation (box
  memory), FROZEN drafter (SD^2 fine-tunes; hence the oracle-ceiling
  rung), single-position norm-output vector, KL on the runs' own text
  with the realised block structure, previous-block delta on the
  earlier row of a 2-token feed (train/inference row assignment
  identical; a departure from SD^2's inference rule).
- Arms: V vanilla / O oracle_h (TRUE h_a, D-2-named ceiling) /
  F free_inject (FREETOK ridge; DR-4 left FREETOK the mandatory
  comparator) / T tel_inject (UNION ridge); gamma 4 fixed, E6
  tokens/call, +0.062 bar, pairwise budget guard (mechanical at fixed
  gamma), void semantics verbatim; verdict seed 4, seed 5 reserved.
- Ladder: A0 O-vs-V clears -> A1 (F-vs-V = FREE-ACTUATOR readout,
  own label; T-vs-V AND T-vs-F = the telemetry verdict, a WIN
  licensed only as "beyond FREETOK at the actuator", never "beyond
  p"); A0 fails -> ACTUATOR-CEILING NULL, lane ends, F/T optional
  reported-only. A1 runs only by the user's decision with DR-4's
  COMPARATOR-TOOTHLESS label and its pinned recommendation in view.
  D-9 analytic acceptance REPORTED per arm.
- Population: data/prompts_oq16_verdict.jsonl (210 fresh; generator
  refuses >= 2 shared content words / summarize-object containment /
  exact collisions against all four committed sets — the critic's
  blocker: 83 of the first draft's topics were paraphrases); power
  note from the committed vanilla pairs (CI half-width ~0.039 at
  n=210 vs ~0.09 at n=42), critic-recomputed.
- Export: --stage-a-export freetok,union — binding gate on the DR-4
  summary fields AND a weight-level TRAIN-refit binding (<= 1e-9),
  five-fold cross-fit h_hat by the pinned permutation, full refit at
  the DR-4 lambdas, self-check (<= 1e-9; a trip refuses).
- Adapter training: tools/train_inject.py — forward KL full vocab,
  verifier NF4 frozen, drafter frozen, TRAIN+TEST train / VAL selects
  the epoch (worse-than-no-op flagged, never swapped), AdamW 1e-3 ->
  1e-4, 6 epochs, seed 0; OOM fallbacks pinned in order (gradient
  checkpointing, then rank 256, all three adapters alike).
- Mechanical asserts: per-block hook applications == n_layers x
  gamma; per-prompt injected blocks == verify blocks; adapter torch-
  vs-numpy self-check (relative to output magnitude); every sha
  binding (adapter + meta, export, geometry, smoke refusal, model
  pair, resume identity).
- Honest expectation: A0 open (SD^2's +0.35/block is at k=8, batched,
  unquantized — a cross-gamma prior, no ratio licensed; PRIOR_ART
  dated correction carries the regime); A1's prior against.

Instrument: src/sideband/recon.py (block arithmetic asserted against
the committed p000 anchors, LiveReconstructor, adapter_forward_np),
tools/train_recon.py (stage_a_export; pipeline return_weights),
src/sideband/real/steer_inject.py (assemble_prompt contracts,
sha-bound h_hat, build_adapter, adapter_self_check, UpProjInjector,
BlockInjector), src/sideband/real/k3_live.py (K3Config.inject rules),
src/sideband/real/hf_specdec.py (start/end-block hooks; the K-3
q-guard unchanged for scheduling arms), tools/run_k3_arms.py (arms
8-10), tools/train_inject.py (GPU trainer), data/make_prompts_oq16.py
+ prompts_oq16_verdict.jsonl, .gitignore (weights/h_hat/adapters).
Tests +6 (block arithmetic, adapter reference, export e2e incl.
binding refusal + five folds + sha maps + self-check, assemble_prompt
contracts + h_hat sha, K3Config rules, CLI guard). Two critic rounds
(Stage-A package: 3 blockers + 9 advisories; DR-4 recompute: plan-text
advisories) applied. Suite 355 passed + 1 skipped; lint OK (23).

No GPU has run; no export, adapter, or verdict artifact exists.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 786ab59 2026-09-05 OQ-16 DR-4: COMPARATOR-TOOTHLESS — the value-paired second-hash encoding of p is CI-clear worse than FREETOK at the registered (unanchored) readout, so "beyond p" stays unpriced and Stage A proceeds only on the user's decision; F-22 dated addendum; the lane's last reconstruction-level diagnostic

````text
DR-4 (registered pre-run in c2181b1; the run started 10.9 s after
that commit — git-anchored): FREETOK2 = FREE ++ TOK_A ++ TOK_B (2048
salted-hash bins valued by top_p; 4753 dims = UNION's) vs FREETOK and
vs UNION. Pinned label: COMPARATOR-TOOTHLESS.
- freetok2_vs_freetok -0.003085 [-0.004984, -0.001280] (k3 -0.003521;
  oq15 -0.002658) — CI-clear NEGATIVE; FREETOK2 wins 37/84 clusters.
  The teeth clause fails, so union_vs_freetok2 +0.068265 [+0.065783,
  +0.070556] is REPORTED, not labelling: identically union_vs_freetok
  minus freetok2_vs_freetok; at equal dims the encoding closes NONE
  of the DR-3 gap (union beats FREETOK2 in 84/84 clusters, min
  +0.036). FREETOK2 R^2 +0.255 vs FREETOK +0.258.
- Pinned magnitudes carried: 1.047 of the DR-3 margin (surprising
  side (ii) fired mechanically and VACUOUSLY — the comparator is worse
  than FREETOK) and -0.018 of the free margin. Honest prediction
  (teeth at +0.02..+0.05): FAILED ON SIGN, recorded against.
- CAVEAT (critic blocker, wording corrected pre-commit; heuristic,
  not a registered readout): the teeth readout is UNANCHORED — no
  alignment-destroyed TOK_B twin was registered — so it charges the
  block its +2048-dim dilution; the committed VAL table shows
  FREETOK2 beating FREETOK at lambda 1e5 and a positive live-minus-
  stale gap at every lambda (+0.047 .. +0.020), so the live -0.0031
  is consistent with a +0.02..+0.03 block-aligned contribution offset
  by dilution at the selected lambda 1e4 — and equally with less.
  LICENSED: TOK_B does not net a positive margin over FREETOK at
  either arm's VAL-optimal lambda; its contribution is not separable
  from dilution under the registered readout. NOT licensed:
  "extracts nothing", "saturated", "pure dilution". The anchored
  DR-5 (FREETOK ++ destroyed TOK_B) would resolve it but is forbidden
  by the fold-back-#2 hard stop unless the user authorizes an
  exception in those words. Dated erratum: TOK_B is sparse like
  TOK_A with heavy-tailed values, not "dense-valued".
- MEANING: DR-4 did NOT deliver the basis the registration said a
  Stage-A telemetry test NEEDS; "beyond p" stays UNPRICED; the pre-
  registered recommendation stands (treat as NOT confirmed for the
  Stage-A decision) and Stage A, if run, proceeds on the user's
  decision with that on the table (HANDOFF's "only if DR-4 holds"
  relaxed to the registration's "the user decides", named as such);
  FREETOK stays the Stage-A free comparator; a Stage-A telemetry WIN
  could only be licensed as "converts beyond FREETOK, the strongest
  free encoding tested, at the actuator", never "beyond p".

Critic recompute round: all 11 readouts x 8 cells bit-exact by fresh
implementation (three implementations); label reproduced; the
arithmetic identity bit-exact; DR-3 consistency — 3108/3108 shared
state rows raw-text identical, every shared summary field identical;
clean-worktree re-run at c2181b1 byte-identical (summary + 3612 state
rows) — the -dirty meta attested moot; instrument audit clean (hash B
uniform over all 2048 bins, (mod, hash-B) identifies all 128256 ids,
three real rows hand-computed bit-exact, clip touches 0.15% of TEST
nonzeros). 3 wording blockers + 5 advisories applied. Suite 355
passed + 1 skipped; lint OK (23 findings).

Evidence: results/real/oq16_stage_r_dr4.json (+ sha-headed state,
meta). BLUEPRINT DR-4 OUTCOME note; F-22 DR-4 ADDENDUM + sources;
OPEN_QUESTIONS OQ-16 tail.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## c2181b1 2026-09-04 OQ-16 DR-4 REGISTRATION (pre-run; git anchor): the equal-dims better-token-encoding comparator FREETOK2 = FREE ++ TOK_A ++ TOK_B (salted-hash bins valued by top_p) at UNION's 4753 dims; labels BEYOND-P CONFIRMED / REDUCES-TO-ENCODING / COMPARATOR-TOOTHLESS pinned; the lane's last reconstruction-level diagnostic

````text
Registered in docs/BLUEPRINT.md after the DR-3 OUTCOME note, BEFORE
any DR-4 number exists (DR-3's numbers were read and motivate it;
disclosed). Question: DR-3's +0.065 union margin over FREETOK cannot
separate hash/pairing loss about p's exact top-32 from information
beyond p. Comparator: TOK_B = 2048 bins under a salted multiplicative
hash (top 11 bits of (id*2654435761 + 0x9E3779B9) mod 2^32) with bin
value = the token's top_p (within-row collisions sum) — a second
collision pattern per id plus the value-to-id pairing, deployment-
free. PRIMARY readout union_vs_freetok2 at equal dims (same free core
and TOK_A; slots vs TOK_B as the third block); TEETH readout
freetok2_vs_freetok (CI lower > 0 required, else COMPARATOR-
TOOTHLESS and "beyond p" stays unpriced); BEYOND-P CONFIRMED iff
union_vs_freetok2 pooled CI95 lower > 0, else REDUCES-TO-ENCODING
(kills the Stage-A telemetry test pre-GPU). Magnitude carried as a
fraction of union_vs_freetok (+0.065180) and of freetok_vs_free
(+0.173871). Honest prediction: teeth expected (+0.02..+0.05);
union_vs_freetok2 positive and smaller than +0.065; surprising sides
= a collapse (CI lower <= 0) or more than half the DR-3 margin
surviving (>= +0.033). No DR-5 (fold-back-#2 hard stop).

Instrument (additive; shared arms must reproduce DR-3 bit-identically
— the critic's dr3 -> dr4 recompute): recon.tokb_bins / tokb_block /
freetok2_features / arm_features("freetok2") / dr4_label;
tools/train_recon.py --freetok2 (needs --union; refuses the registered
out; meta modes.freetok2); readouts union_vs_freetok2,
freetok2_vs_freetok, freetok2_vs_free, tel_vs_freetok2; label dr4.
Tests (+3): hash-B properties over the Llama-3 vocabulary (near-
uniform, <1% agreement with id mod 2048), value-paired block incl.
collision sums and shape refusal, dims 4753 = UNION's at n_slots 512,
label cells; e2e on a value-paired synthetic construction lands
BEYOND-P CONFIRMED and on the token-free one COMPARATOR-TOOTHLESS,
with the label recomputed from the summary's own numbers; CLI guard.
.gitignore negation for results/real/oq16_stage_r_dr4.json.state.jsonl.

Suite 349 passed + 1 skipped; lint OK (23 findings). No result exists
at this commit.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 7fb3440 2026-09-04 OQ-16 DR-3: TELEMETRY-BEYOND-P — the union of telemetry and p's hashed top-32 support reconstructs h_a CI-clear better than the free token-identity arm (+0.065, 37.5% of the free margin, both populations); F-22 dated addendum; "beyond p" qualified pending a better-token-encoding comparator

````text
DR-3 (registered pre-run in 2ec789f; run started 7.9 s after that
commit — git-anchored): UNION = TEL ++ TOK (4753 dims) vs FREETOK,
with UNIONNOISE = NOISE ++ TOK as the equal-dims alignment-destroyed
anchor. Pinned label: TELEMETRY-BEYOND-P.
- union_vs_freetok +0.065180 [+0.062411, +0.067705] (k3 +0.0639
  [+0.0597, +0.0680]; oq15 +0.0665 [+0.0629, +0.0697]);
  union_vs_unionnoise +0.078089 [+0.075624, +0.080368]; both legs
  CI-clear on both DISJOINT prompt populations; union beats freetok,
  unionnoise and tel in 84/84 clusters.
- MAGNITUDE (carried as pinned): 37.5% of the free margin
  (freetok_vs_free +0.173871), ABOVE the pre-run "would surprise"
  line (a quarter) — the surprising side landed a second time,
  recorded against the prediction. UNION R^2 +0.324 (cosine median
  0.579) vs FREETOK +0.258, UNIONNOISE +0.245. Decomposition
  (mutually consistent): block-aligned ~+0.081, prompt-level ~+0.010,
  dilution ~-0.026 per +2048 dims (~5x F-16's scale — calibration
  note for any Stage-A freeze), net +0.065.
- WHAT IT LICENSES: the S1 stream carries block-aligned, dilution-
  priced information about the anchor state beyond FREETOK's
  2048-bin hashed encoding of p's top-32 support — small, CI-tight,
  replicating. QUALIFIER (critic blocker, wording corrected pre-
  commit): the anchor cannot separate slot information that is a
  function of p's EXACT top-32 (hash collisions, value-to-id
  pairing) from information beyond p; "beyond p" is unpriced
  pending a registered equal-dims better-token-encoding comparator
  (DR-4 candidate). Stale-netted +0.055 relabelled a LOWER BOUND
  (dilution unpaid); the dilution-priced estimate is the +0.078
  anchor readout. K-2 relation: most of what telemetry reconstructs
  is a lossy copy of what p reveals; between a third and a half of
  its margin is not, depending on dilution pricing.
- MEANING FOR THE LANE (pinned words): reopens the Stage-A telemetry
  question with a reconstruction-level basis; the Stage-A claim
  pinned FOR THE FREEZE (no Stage-A registration exists yet) is
  UNION-vs-FREETOK at the actuator, both free-augmented, FREETOK the
  mandatory free comparator. No conversion-level claim is licensed;
  two conversion nulls on the lane remain the closest precedents.
  STAGE-R PASS stands; Stage A AUTHORIZED and USER-GATED; NO GPU
  spend (user re-decides with DR-3 in view).

Critic recompute round: fresh-implementation bootstrap bit-exact on
all 56 reported cells + gate cells + labels; union code path
verified from the raws; dr->dr3 additivity bit-identical (25 shared
state vectors, every summary field); full rerun from the committed
code byte-identical (summary; 3108/3108 state rows); timeline
anchored. 3 wording blockers + advisories applied (dilution-unpaid
relabel, "beyond FREETOK's encoding" qualifier, dated pointer from
the superseded F-22 bullet to the addendum, +0.065 vs +0.066 MSE/R^2
digits, "disjoint" not "independent", "pinned for the freeze" not
"registered", dated erratum on the registration's e2e-test claim,
-dirty attestation). Suite 346 passed + 1 skipped; lint OK (23).

Evidence: results/real/oq16_stage_r_dr3.json (+ sha-headed state,
meta). BLUEPRINT DR-3 OUTCOME note; F-22 DR-3 ADDENDUM + dated note
+ sources; OPEN_QUESTIONS OQ-16 tail.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2ec789f 2026-09-04 F-22: OQ-16 Stage R PASS by the gate; DR-1 confirms the deployable margin (R^2 ~0.25); DR-2 shows a free token-identity encoding reconstructs h_a at least as well as telemetry; DR-3 registered pre-run

````text
Stage R (registered bd71358, user-launched) resolved STAGE-R PASS —
the lane's first surprising branch, the pinned dilution-null
expectation refuted: delta_noise +0.176469 [+0.130414, +0.251518]
(~32x the five-seed stale 3-sd bar), delta_free +0.204984
[+0.153698, +0.288162], both populations CI-clear. Critic attack
round (rule 7): no leak (feature path reads summaries + slots only;
h and slots logged from the same verify forward), deterministic
rerun BYTE-IDENTICAL, fresh-implementation bootstrap bit-exact —
but a STANDARDIZATION PATHOLOGY (rare mass512 buckets with TRAIN
sd ~1e-7; standardized inputs up to 26,662 on two out-of-support
oq15 test prompts) inflates the registered deltas ~25% and leaves
the honest TEL-vs-trivial margin CI-straddling (+0.107 [-0.070,
+0.221]).

Post-gate diagnostics DR-1/DR-2 registered with pinned labels and
predictions BEFORE running (the DI-1 pattern; non-criterion):
- Instrument extension: feature-support clip (TRAIN [min,max] per
  feature; an out-of-support guard, not an sd floor), trivial-
  baseline rows + REPORTED tel_vs_trivial in every run, equal-dims
  FREETOK arm (free ++ hashed top-32 next-token ids). INVARIANCE
  LEG: modes OFF reproduces the registered run bit-exact on every
  gate-bearing field and all 1,512 state rows; one ulp on the
  reported trivial MSE (per-cluster accumulation) explained.
- DR-1 = DEPLOYABLE-MARGIN CONFIRMED: tel_vs_trivial +0.250784
  [+0.239316, +0.261616], both pops; TEL R^2 +0.253, cosine 0.50;
  lambdas free/tel INTERIOR (1e4) for the first time on the lane.
- DR-2 = TOKEN-IDENTITY-NOT-EXCLUDED: tel_vs_freetok -0.004792
  [-0.007192, -0.002600] CI-clear negative; freetok_vs_free
  +0.173871 — a free encoding of p's top-32 support reconstructs
  h_a at least as well as telemetry. Critic wording blockers
  fixed pre-commit: the TEL-vs-FREETOK design licenses "the
  telemetry margin is not evidence of information beyond what p
  reveals at this readout", NOT "composed of token identity"; no
  conversion-level probability is licensed by a reconstruction CI.
- OQ-16's literal answer: ~a quarter of the anchor state survives
  linear reconstruction from the address stream, and a free
  encoding of p's top-32 token identities recovers at least as
  much (K-2's "lossy copy of what the decoder already has", at the
  reconstruction level; K-2 not re-fired — different target).

DR-3 REGISTERED PRE-RUN (this commit is the git anchor): UNION =
TEL ++ TOK vs FREETOK, with UNIONNOISE = NOISE ++ TOK as the
equal-dims alignment-destroyed anchor; labels TELEMETRY-BEYOND-P
iff both union_vs_freetok and union_vs_unionnoise CI-lower > 0,
else TELEMETRY-NOT-BEYOND-P; magnitude carried as a fraction of
the free margin; honest prediction: small either way. Instrument:
--union mode (refuses the registered out; requires --freetok).

FORMAL STATE: Stage R PASS stands; Stage A AUTHORIZED and
USER-GATED; user authorized GPU spend but NOTHING runs until the
DR-3 result is in view and the user re-decides. Critic recompute
round on DR-1/DR-2 + F-22: every delta/CI/label bit-exact from
the state files by fresh implementation; 2 wording blockers + 9
advisories applied (digits, R^2 two-of-three, 20-sd count
definition, partial grid edge under clip, timeline attestation,
K-2 relation). Suite 346 passed + 1 skipped; lint OK (23).

Evidence: results/real/oq16_stage_r{,_inv,_dr}.json (+ sha-headed
states, metas; .gitignore negations incl. the pending _dr3).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## bd71358 2026-09-04 OQ-16 FOLD-BACK #2 ARC REGISTRATION + Stage-R instrument (pre-run; critic-gated)

````text
User started OQ-16 after F-21 ("lets start oq16") — the LAST arc in
the K-3 lane. Three design decisions put to the user before the
registration was written (recommended defaults accepted): training
data = all four vanilla verdict byproduct runs; Stage-R gate =
two-leg AND (existence vs the noise twin AND deployability vs
free); the direction proxy is REPORTED, not gating.

The OQ-16 ARC REGISTRATION block (BLUEPRINT, after the STAGE-C
OUTCOME note) pins, before anything runs:
- TERMINAL-OUTCOME PARTITION: RECONSTRUCTION-CEILING NULL (leg 1
  fails; block-aligned bounding carried from F-16/F-18) /
  RECONSTRUCTION-DILUTION NULL (leg 1 holds, leg 2 fails) /
  STAGE-R PASS (authorizes ONE user-gated actuator stage) /
  ACTUATOR NULL / WIN — every branch ends the lane; unclassifiable
  -> ceiling null; OQ-15's limbo pins mirrored.
- STAGE R (CPU, committed evidence only): reconstruct the logged
  h_a (float16 4096-dim model.norm output at the anchor — the SD^2
  steering position, logged by the dated 2026-09-02 byproduct
  amendment) from anchor-time features via the committed
  probe_input assembly (free 657 / tel 2705 / noise = F-16 shift
  17; NO q_sig — it does not exist at the anchor, verified at the
  critic round). Four vanilla runs (~70,529 blocks; runs [0] and
  [2] are voided attempts' vanilla arms — logging was never
  quarantined, disclosed), two populations, prompt-level 126/42/42
  splits (Stage-I recipe). Multi-output closed-form ridge, target
  z-scored per coordinate on TRAIN moments, WIDENED lambda grid
  (1e-2..1e5; three straight grid-edge precedents named). Estimand:
  pooled TEST standardized MSE; deltas by stats.paired_ratio_delta_ci
  (per-cluster SSE / position counts; the E6-committed function —
  paired_cluster's [0,1] validity condition does not fit unbounded
  squared errors, validity note pinned).
- GATE: leg 1 delta_noise CI-lower>0 AND point > stale_mean+3*sd
  AND point > stale max, with a GATING five-seed stale-target
  control (DI-1 recipe verbatim, lambda re-selected inside every
  control — the F-20 lesson baked into the criterion, not bolted
  on); leg 2 delta_free CI-lower>0. Straddles fail. Labels are
  pinned strings the summary prints mechanically.
- STAGE A skeleton (deferred-constants): SD^2-style draft-side
  injection, full spec by dated freeze BEFORE any run, economics
  bars unchanged, F-21's pairwise-selected-budget check mandatory.
- HONEST EXPECTATION: leg-2 failure (dilution null) is the
  expected outcome given F-20's CI-negative delta_free on the same
  stream; the dense 4096-dim state-identity target is the
  registered reason to measure anyway.

Instrument: src/sideband/recon.py (imports the committed Stage-I
primitives — D-3; stale_perm with bijection assert, two-leg gate,
centered cosine) + tools/train_recon.py (one deterministic
invocation computes the live gate and all five controls sharing
verified-invariant Grams; meta before the run, sha-headed state as
the recompute surface; registered-outs guard repo-anchored) +
tests/test_recon.py (13 tests: constants, DI-1 recipe equality,
gate labels incl. straddle-fail, refusals, multi-output ridge,
three e2e gate-semantics constructions — slot-carried h -> PASS,
noise h -> CEILING, prompt-level-only h -> CEILING (the critic's
gate-soundness probe: the stale control and noise twin must price
prompt-level statistics), state-file bit-exact delta reproduction,
CLI guard).

Critic round (pre-commit, registration-before-run gate): NO
UNPINNED DOF found; standardize/permute commutation and
Gram-sharing verified valid; q_sig-absent-at-anchor verified TRUE
in k3_live/hf_specdec; structural claims recomputed against the
raws (70,529 blocks exactly); 1 blocker fixed (an edit had
swallowed the "## Eval protocol" heading — restored) + advisories
applied: voided-run provenance disclosure, dead test branch
replaced with an impossibility assert (stale-max clause implied by
the 3-sd clause at n=5), repo-anchored guard, realized
feature_dims recorded in the summary, standardized-vs-raw-space
note on the direction proxy.

Suite 339 passed + 1 skipped; lint OK. NOTHING HAS RUN: Stage R
awaits launch (CPU, est. ~20-60 min).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## ad32345 2026-09-04 F-21: OQ-15 Stage C CONVERSION-MODE NULL — head_tel ties vanilla and loses CI-clear to head_free at matched budget; seed-3 guard clears every leg; OQ-16 (fold-back #2) authorized

````text
The seed-3 void-rerun (the registered single rerun, arms 6,7,1,2,
whole stage, arm 7 at the v2 VOID_REFREEZE thresholds) resolved the
OQ-15 arc:

- GUARD: clears every leg — arm 7 dpe 1.2742347176420175 below all
  three comparators outright; the pinned honest prediction held
  (differential drift realized -0.0065 vs +0.0293 re-breach
  threshold).
- GATE (E6 pooled t/c, paired_ratio_delta_ci n_boot 2000 seed 0):
  NOT WIN, no guard asterisk. C4-vs-C1 +0.002664 [-0.044719,
  +0.046727]; C4-vs-C2 -0.050425 [-0.109388, +0.005772]; C4-vs-C3
  -0.081846 [-0.132484, -0.035567] CI-CLEAR NEGATIVE — the
  conversion-level mirror of F-20's delta_free: the telemetry head
  loses to the free head at prediction AND at live conversion.
- TERMINAL CLASSIFICATION (pinned partition, mechanical): Stage I
  PASSED + Stage C NOT-WIN = CONVERSION-MODE NULL. OQ-15 CLOSED as
  fold-back #1; OQ-16 authorized as fold-back #2 (new arc, new
  registration, user GPU authorization required); lane hard-stops
  after #2.

F-21 carries the pinned finding duties: extend-signal breakdown
(off5 heads worse than trivial 0.05470/0.05975 vs 0.05222;
tel_off3/off4 worse than per-offset baselines — every EXTEND rode
on factors with no held-out advantage over constants), all-ten
lambda grid-edge, RNG-children note, extend-open v2 operating
point (4138/4142 stop/extend blocks vs v1's near-inert 1341/1745),
seed-2 disclosure table (read post-gate only), -dirty meta
artifact, analytic estimand REPORTED with the F-19 composition
confound (head_tel tops analytic acceptance while drafting fewest
tokens — the conversion failure in one line). Descriptive flag, no
CI claimed: head_free posted the highest pooled t/c on both seeds
at sub-vanilla budget — a head_free-vs-vanilla claim would need
its own registered readout; recorded as OQ-16's one supportive
datum (the actuator converts free signals; the telemetry stream is
what failed).

Critic recompute round: gate recomputed bit-exact by a fresh
independent bootstrap implementation from the stats files; binding
asserts verified (arm 7 -> v2 sha, arms 2/6 -> v1 shas, val_run,
head-weights sha, seed 3, prompts sha); quarantine postmortem
clean (void commit 46ab439 at 02:25:02Z, first seed-3 run_id 49 s
later; seed-2 gate metrics appear only in post-gate text); every
rounded digit in all three prose blocks audited (one misrounded
drift digit fixed pre-commit); no unregistered claims. Suite 326
passed + 1 skipped; lint OK (22 findings).

BLUEPRINT gains the dated STAGE-C OUTCOME block; OPEN_QUESTIONS
gains the OQ-15 RESOLVED and OQ-16 AUTHORIZED tail notes. Evidence:
seed-3 verdict sidecars all four arms (byproduct raws gitignored,
shas in summaries).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 46ab439 2026-09-03 OQ-15 Stage C: seed-2 verdicts BREACH pairwise guard (arm-6 leg); registered void semantics executed, seed-3 rerun launching

````text
GPU chain through the seed-2 verdicts completed clean (containment
recheck PASS on the bit-identity branch; B_ref frozen at
oq15c_val_arm1 dpe 1.3255813953488371; searches arms 2/6/7 SELECTED
under the registered constrained-maximization key). At the verdict
budget-guard evaluation (budget columns only, quarantine per the
registered void semantics): arm 7's drafted-per-emitted
1.312796030373656 vs the arm-6 allowance 1.2973549568599316 + 0.01
— BREACH by 0.00544 (~0.54x epsilon). Arm-1/arm-2 legs comply
outright. Arm 7's gate metrics are QUARANTINED UNREAD (arms 1/2
seed-2 tokens-per-call held unread too — beyond-the-letter, critic
advisory); one comparator exposure (arm 6's pooled summary in the
task's stdout tail, seen pre-guard-evaluation) is disclosed in the
amendment and cannot move the gate (seed-3 supersedes all seed-2
records as gate inputs).

STAGE-C VOID EXECUTION block appended to BLUEPRINT (dated
2026-09-03, written before any quarantined metric was read; the
Attempt-#1 template transposed):
- MECHANISM: not val->verdict inflation this time — arm 7 held its
  budget (+0.0008); the 2.6x-epsilon pairwise gap was baked in AT
  SELECTION (frontier-grid discreteness: arm 7 selected 0.0136
  below the common cap, arm 6 0.0398 below). Knowable at freeze
  time from committed selection budgets; not noticed; the pairwise
  guard exists precisely for this.
- RE-FREEZE (reduced-cap branch, val evidence only): new cap =
  1.2858072916666667 (arm 6's SELECTED val budget) — removes the
  val-time pairwise gap by construction; K-3's min-budget cap rule
  deliberately NOT transposed (would force a degenerate floor cell
  here, reasons in the block); verdict-side caps rejected as
  forbidden tuning. Selection key unchanged, outcome unique and
  forced from the committed arm-7 search state: (stop q0.15,
  extend q0.75), val t/c 2.96675791943684, val budget
  1.266543633008173 -> oq15c_thresholds_arm7_v2.json
  (VOID_REFREEZE; provenance carries supersedes/void_cap/rule +
  val_run retained for the gate-time binding asserts).
- HONEST PREDICTION pinned: re-breach requires differential drift
  > +0.0293; seed-2 differential was -0.0107 — guard expected to
  clear with ~0.04 margin (caveats owned: K-3's +0.064 inflation
  exceeds the threshold; v2 moves extend-open). Win side: the
  re-freeze cuts arm 7's val t/c by 0.093 while the bar demands
  +0.062 over every comparator — the registered conversion-mode
  null expectation strengthens.
- RERUN SPEC: whole verdict stage at RESERVED SEED 3, order
  6, 7, 1, 2, arm 7 at v2, arms 2/6 unchanged, outs
  oq15c_verdict_s3_arm{N}.jsonl; all four run regardless; second
  breach on any leg FAILS that leg, no further reruns.

Critic round (pre-commit, quarantine-respecting): breach arithmetic
and every rounded digit recomputed bit-exact from summaries' budget
fields (one misrounded drift digit caught and fixed pre-commit);
v2 selection recomputed from the committed state file (18 feasible,
unique winner, tie-break never engaged); cap-rule license audited;
blind membership test confirms no undisclosed verdict float in any
prose file; resume/misbind foot-guns checked in run_k3_arms.

Evidence committed: oq15c containment rider, val run, searches +
sha-headed states, thresholds (v1 x3 + arm-7 v2), seed-2 verdict
sidecars all four arms (byproduct raws gitignored, shas in
summaries). Suite 326 passed + 1 skipped; lint OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 9e8fa4a 2026-09-03 OQ-15 STAGE-C FREEZE: deferred-constants amendment + head-policy instrument + binding-gated weight export (pre-GPU; critic-gated)

````text
User authorized Stage C after reading F-20. The registration's
DEFERRED CONSTANTS clause is discharged by a dated STAGE-C FREEZE
block (BLUEPRINT, after the Stage-I/DI-1 outcome notes) that only
materializes mechanics — no gating quantity touched (bars, guard,
comparators, populations, seeds, policy family were registered
pre-Stage-I):

- Head export + BINDING GATE: --stage-c-freeze re-runs the Stage-I
  pipeline in-process and refuses unless bit-exact vs the committed
  oq15_stage1.json on {delta_noise, delta_free, per_offset,
  test_mse, per_head_test_mse, chosen_lambda}; trains the OFFSET-5
  heads (free/tel) on the arm-5 byproducts (both seeds; off-policy +
  voided-seed-0 provenance disclosed; evidence oq15_offset5.json +
  sha-headed state, REPORTED-only); writes oq15_head_weights.npz +
  meta; EXPORT SELF-CHECK with two assertions — single-row
  bit-equality (algorithmic identity of the live path) and <= 1e-12
  vs batch predictions (this box's BLAS accumulates batched vs
  single-row gemv differently; measured 3.2e-14 pre-pin, ~30x
  margin; the live system is internally consistent single-row).
- Live scoring path: HeadScorer (CPU, outcome_head) — a_hat_i =
  clip([1,(x-mu)/sd]@w) via the exact predict_clipped op; S_j
  products; AnchorRead carries the reader's probe_input vectors;
  K3Config.head_scorer; SchedulerPolicy kind "head" (STOP iff S_j <
  tau strict; EXTEND iff S_4*a_hat_5 >= tau; corner (0.95,0.95) per
  the directions note); hf_specdec k3 loop scores lazily as q_sigs
  arrive; block 1 never consults (structural, unchanged).
- Runner arms 6 (head_free) / 7 (head_tel) with --head-weights
  (sha into meta + resume identity); thresholds kind "head".
- Search driver arms 6/7: S_1/S_2/S_ext grids materialized OFFLINE
  from the C1 val byproduct through the exported heads (consulting
  rows >= 1, E12); frontier machinery VERBATIM; val-run bindings
  parameterized (--expect-seed/--eval-split; K-3 defaults kept).
- Pinned artifact names (oq15c_*), run order (containment recheck
  -> oq15c_val_arm1 -> searches 2,6,7 -> verdict 2,7,1,6 at seed 2),
  E10 containment re-validation before verdicts, void semantics as
  registered, and the HONEST EXPECTATION (F-19 pattern): a C4 WIN
  is NOT expected given F-20; the expected terminal state is a
  conversion-mode null — Stage C is the registered toll for
  fold-back #2, run because a live measurement is evidence a
  forecast is not.

Freeze RAN (CPU, per the pinned order freeze -> critic -> commit;
the in-session text-before-run ordering is operator-attested, and
nothing gating derives from the read offset-5 numbers): binding
gate PASS bit-exact on all six fields; offset-5 heads trained —
lambdas 10.0/10.0 (grid edge again), TEST MSE free 0.05470 / tel
0.05975 vs trivial 0.05222 — BOTH WORSE THAN TRIVIAL, the extend
signal is near-uninformative (finding duty pinned in the freeze
block: per-factor extend breakdown + all-ten grid-edge
disclosure); export self-check PASS (1050 blocks x 10 heads,
single-row bit-equal, max batch deviation 6.8e-15 <= 1e-12).

Critic round (pre-commit): offset-5 evidence recomputed bit-exact
from raws; the exported off1-4 heads verified to reproduce the
committed Stage-I state rows 672/672 cells bit-exactly; amendment
scope audited (no gating quantity touched); hf_specdec non-head
paths verified behaviorally unchanged; freeze test params verified
not CLI-reachable. 1 blocker fixed (containment artifact name ->
the tool's actual one-payload shape) + advisories: pinned exact
GPU command lines + gate-time binding asserts (the
old-K-3-thresholds foot-gun named), per-row trivial SE added to
the off5 state (freeze re-run), gamma_base==4 refusal for head
policies, RNG-children methods note.

Tests: head policy (scheduler), HeadScorer bit-equality, freeze
end-to-end on synthetic data incl. binding-gate tamper refusal,
K3Config head requirements. Suite green; lint OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 44b08fa 2026-09-03 F-20: OQ-15 Stage I — mechanical PASS; the registered five-seed stale-target control leaves the margin indistinguishable from zero-information draws; telemetry loses to free outright

````text
Stage-I gate (registered 89b38ef, run after registration): delta_noise
+0.000763 CI95 [+0.000308, +0.001215] on 42 TEST clusters / 28,616
positions -> mechanical PASS. Critic recompute: bit-exact from state
rows two independent ways, plus a BYTE-IDENTICAL deterministic rerun
from the sha-verified raws; split/sha/timeline bindings confirmed.

DI-1 stale-target control (critic-proposed; registered with pinned
conclusion labels BEFORE running — the P1 pattern): targets randomly
permuted within each (run,prompt) so no block-aligned information
exists for any arm; prompt-level channels cancel between TEL and
NOISE. Pinned two-cell labels: primary +0.000643 [-0.000076,
+0.001357] -> ARTIFACT-DOMINANT; replicate +0.000276 [-0.000424,
+0.000943] -> ARTIFACT-NOT-EXCLUDED; disagreement rule carries
ARTIFACT-DOMINANT. SEED-SPREAD EXTENSION (registered before running,
reported-only): seeds 2/3/4 = +0.000164 / -0.000713 (CI-negative) /
-0.000105 — five-seed mean ~+0.000053, sd ~0.0005. REFINED READING
(the extension's own registered honest-weight sentence fires): the
redundancy channel is DRAW VARIANCE of the live margin's magnitude,
not systematic bias; no stale cell is CI-positive on the pooled
delta; the live point is rank 1/6 (one-sided p ~0.17) at ~1.4 sd
above the stale mean. Existence claim: UNSUPPORTED-BUT-NOT-REFUTED
at this power. Method lesson: a single stale draw misleads in either
direction — multi-seed stale-target controls are the F-16-extension
practice.

Reported alongside (mandated in F-20): delta_free -0.00286 [-0.00322,
-0.00252] — the TEL head loses OUTRIGHT to the FREE head at every
offset despite +2048 extra dims; all 24 lambdas at the grid edge;
binary sidebar non-corroborating (survival-conditioned, labeled).

FORMAL STATE: the mechanical PASS stands (DI-1 non-criterion; no
reclassification channel; post-readout gating amendments prohibited).
Stage C remains authorized and USER-GATED; what the control removes
is the pass's registered MEANING — block-aligned acceptance-relevant
information above free signals is NOT demonstrated.

Also: .gitignore negations for six Stage-I state files (critic
blocker); --stale-target-perm-seed in tools/train_outcome_head.py
(refused on the primary registered path, recorded in meta+summary) +
test; BLUEPRINT DI-1 registration + seed-spread extension + dated
STAGE-I OUTCOME note; OPEN_QUESTIONS OQ-15 tail note; schema-residue
and provenance disclosures per the final critic round.

Critic rounds: gate recompute (bit-exact + byte-identical rerun),
DI-1 recompute (bit-exact both cells + one-cell deterministic rerun,
label arithmetic verified, design re-checked with measured
permutation-alignment slivers), fix verification.

Suite 319 passed + 1 skipped; lint 21 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 89b38ef 2026-09-03 OQ-15 FOLD-BACK #1 ARC REGISTRATION + Stage-I instrument (pre-run; critic-gated)

````text
The registration the FOLD-BACK COUNT AMENDMENT and F-19's kill text
require, pinned before any OQ-15 head or aggregate exists.

TERMINAL-OUTCOME PARTITION (the decidability pin's payload): WIN /
INFORMATION-CEILING NULL (skip OQ-16, lane stops) / CONVERSION-MODE
NULL (hands to OQ-16); straddles read as FAIL; unclassifiable
defaults to ceiling null; the equal-dims alignment-destroyed head IS
the matched-capacity free baseline (anchor-explained lift = ceiling
null); limbo dispositions pinned (never-run Stage C = lane OPEN;
data loss = VOID-BY-DATA-LOSS, never a null).

STAGE I (information; CPU; no GPU): arm-1 verdict byproducts seeds
0+1 = gate data (val/tapcal arm-1 TRAIN-only); split default_rng(15)
-> 126/42/42 prompts, both seed-runs share a prompt's split; target
= per-position analytic acceptance (the amendment-named regression
target); features through the committed scheduler.probe_input (free
657 + q_sig availability rule; TEL +2048 slots; NOISE = F-16's
(b+17) mod n shift); closed-form ridge, lambda-on-VAL the only DOF
(ties -> larger lambda); ONE criterion: delta_noise = pooled TEST
MSE(NOISE) - MSE(TEL) via paired_cluster_delta_ci, PASS iff CI95
lower > 0. delta_free, per-offset deltas, trivial baseline, binary
sidebar (both tails, survival-conditioned per D-9) REPORTED.

Critic registration-gate round: partition decidability verified
(no unclassifiable outcome constructed); code-vs-pins verified
(split, q_sig semantics vs hf_specdec, shift, sha refusal, SE<=1
validity, cluster pooling); populations mechanically verified
(210/30, 70/70/70 + 10/10/10, unique topics, zero overlap with both
committed sets); no leak path found. 2 text blockers fixed: (1)
dated supersession clause for ledger constraint (c)'s gate role
(gate = noise-twin MSE, dilution rationale, rejected reading named,
precision-at-coverage retained as reported); (2) the F-16/F-18
shifted-slots asymmetry sentence carried — ceiling null claims no
BLOCK-ALIGNED information above free + prompt-level telemetry
statistics. Advisories applied: registered-outs override guard +
tests, 210/pid-coverage assertions, sliver scope, Stage-C block-1
consult sentence, voided seed-0 arm-5 provenance disclosure,
term-(d) citation removed, both-tail precision, per-head test MSEs,
git meta, docstring.

STAGE C (conversion; GPU; only on Stage-I pass; user-gated): fresh
populations committed HERE, before any Stage-I number exists —
data/prompts_oq15_verdict.jsonl (210) + data/prompts_oq15_val.jsonl
(30), generator with mechanical overlap/overwrite refusals; verdict
seed 2, reserved rerun seed 3; arms vanilla/draft-conf/FREE-head/
TEL-head; head-policy family pinned (S_j product thresholds, one
quantile level each, frontier machinery verbatim, cap = B_ref);
bars UNCHANGED (CI95 lower > 0, point >= +0.062, pairwise guard
+0.01); Attempt-#1 void semantics verbatim.

PRE-REGISTRATION DATA CONTACT disclosed in the block (structural
inspection only; no aggregate outcome statistic computed).

Nothing has run on real data; the registered Stage-I run starts
only after this commit, and is held for the user alongside all GPU.

Suite 318 passed + 1 skipped; lint 20 OK; 12 new CPU tests
(constants, split, shift, probe_input equivalence, availability
rule, masking, ridge, metrics, end-to-end synthetic tool run,
override guard, sha refusal).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 77d5249 2026-09-03 F-19: K-3 Attempt #1 NULL (verdict, seed-1 void-rerun) - critic-recomputed bit-exact; arc concludes, fold-back #1 = OQ-15

````text
Seed-1 gate (210 fresh prompts): arm4-vs-arm1 +0.006860 CI95
[-0.015024,+0.025572]; arm4-vs-arm3 +0.006974 [-0.014909,+0.025690];
arm4-vs-arm2 +0.048863 [-0.007393,+0.104327] with the budget guard
breached a second time (1.317033 vs 1.285681, margin +0.0314 ~ seed-0's
+0.0289 - the pinned honest prediction confirmed). NOT WIN: every leg
fails both statistical criteria; arm-2 additionally the guard. The
+0.060 val-tuned advantage shrank to +0.007 on fresh prompts; the
voided seed-0 run shows +0.0105 independently. Arm 5 (info-free
gamma-6): t/c 3.428 at dpe 1.750 - the gaming channel the matched-
budget frame existed to expose; geometric closed-form predicts 3.613
(+0.185 optimism, disclosed). Contingency did not fire (needs a
passing arm-2 leg). Analytic estimand reported per Amendment #1's
demotion: 0.7344/0.7454/0.7343/0.7350/0.7313 pooled (arms 1-5),
concordant with the null.

Final critic round: full recompute from stats files (own bootstrap
implementation + repo estimator, bit-exact agreement on all three
legs, guard margins, P-stage fold-back, closed form, inflation table,
timeline/quarantine audit incl. git -S proof the quarantined numbers
never entered prose pre-F-19). Verdict on the null: CLEARED, nothing
moves it. Two text blockers fixed in F-19 (the "every criterion"
overclaim -> every leg fails both statistical criteria with arm-1/3
guards satisfied; the arm-4 grid span 1.2485-1.2912 not -1.2777) +
advisories applied (uncommitted process claim dropped; analytic line
added; 25-s launch-vs-commit timing disclosed; meta skew note; the
word "widened" in the fold-back citation; dated BLUEPRINT erratum on
the two overbroad void-execution sentences - stop-q0.10 row dips
before rising, bottom nine not all-e0-except-tenth).

Evidence: results/real/k3_verdict_s1_arm{1..5} sidecars (byproduct
raws gitignored per E8, per-file sha256s in summaries).

K-3 Attempt #1 concludes. Next per the amended kill text: OQ-15 arc
registration (must pin the exhaustive terminal-outcome partition
before running).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 92fa9cb 2026-09-02 K-3 FOLD-BACK COUNT AMENDMENT (user-directed): one fold-back widened to a structured two, critic-gated

````text
Made while the seed-1 void-rerun was in flight, before any seed-1
output existed to read, seed-0 arm-4/5 gate metrics still quarantined.
Widens ONLY what happens after an Attempt-#1 null; Attempt #1's bar,
guard, epsilon, and void semantics untouched.

Structure (BLUEPRINT block + dated notes in OPEN_QUESTIONS OQ-15/16,
ECONOMICS S5, WHY_THIS_DIES K-3): fold-back #1 = OQ-15
(outcome-supervised head, the registered cheap pilot); #2 = OQ-16
(vector reconstruction -> SD^2 injection), run only on a
conversion-mode OQ-15 null. Cross-lane skip: an information-ceiling
OQ-15 null (telemetry fails to beat the matched-capacity free head +
F-16 noise anchor on held-out outcome prediction) skips OQ-16 and
stops the lane. Hard stop at first WIN / both resolved / skip; no
third mechanism.

Critic round: 3 blockers + 4 advisories, ALL applied: (1) the
ECONOMICS S5 kill sentence sits under its own amendment lock -- dated
cross-note added with the explicit argument (the lock protects bars;
the count is post-null sequencing; pre-result w.r.t. the unevaluated
seed-1 gate); (2) blindness overstatement corrected in the amendment's
own words (made AFTER the breach was known, with the re-breach
prediction committed: blind to outcomes, not prospects;
content-blindness is the operational claim -- every pin reads
identically in a cruising-Attempt-#1 world); (3) decidability pin:
OQ-15's registration must pin an exhaustive terminal-outcome partition
with statistical criteria and the anchor's classification role;
unclassifiable outcomes default to information-ceiling null (skip and
stop, the conservative branch). Advisories: prediction-vs-intervention
loophole in the skip's bridge named so it is never cited as a theorem;
WHY_THIS_DIES citation chain repaired; the resolved precondition
fold-back sentence marked historical; cross-site consistency verified
by the critic.

Critic's ruling on the dodge question, recorded honestly: the clean
window was before the breach was known and was missed; what carries
the amendment is structure, not timing.

Suite green; lint OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 48814ac 2026-09-02 K-3 VOID: budget guard breached on the arm-2 leg; registered void semantics executed, seed-1 rerun launching

````text
Seed-0 verdict runs (arms 4/5) completed; the pairwise budget guard
BREACHED on the arm-2 leg: arm 4 drafted_per_emitted
1.313114692793837 > arm 2's 1.274202241344063 + 0.01 (margin +0.0289,
~2.9x epsilon). Arm-1/arm-3 legs comply. Per the registered VOID
SEMANTICS, arms 4/5 gate metrics are QUARANTINED UNREAD (budget
columns only consulted; run stdout unopened); their evidence files are
committed here unread.

Dated VOID EXECUTION block added to BLUEPRINT: mechanism disclosure
(val->verdict budget inflation vanilla +0.042 / arm3 +0.048 / arm4
+0.064 vs arm2 -0.0005 -- q-stopping self-regulates, the extend-open
channel inflates; the registered budgets-equalize expectation failed
in mechanism, not noise); single re-freeze via the reduced-cap branch
(cap = min committed arm-4 eval budget 1.248526908471913 ->
deterministic selection stop q0.35 / extend q0.05, lands as
k3_thresholds_arm4_v2.json, VOID_REFREEZE); honest prediction pinned
pre-rerun (0.0006 val shave vs 0.029 breach: likely re-breach; a
second breach FAILS the arm-2 leg, no further reruns); whole-stage
seed-1 rerun spec (arms 2,4,1,3,5 order pinned, all five run
regardless); P-stage "no rerun" sentence superseded for gate purposes.

Critic round (fresh recompute): CLEARED, 0 blockers. Breach arithmetic
exact; NO quarantine leak in block or v2 file; re-freeze recomputed
from the state file alone, exact match incl. shas, loadable by
load_thresholds; arm-4-only retune judged the only clean reading
(retuning comparators would shrink the breached allowance and tune
policies whose gate metrics were read); whole-stage seed-1 = the only
D-6-compliant execution; cap-gaming check: no cap choice could shave
more than 0.000556. Four advisories, all applied in this commit
(finer-grid sentence reworded from demonstration; supersession
sentence added; commit-before-launch; run order pinned).

Suite 306 passed + 1 skipped.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 3ca9373 2026-09-02 FUTURE_IDEAS: complementarity assessment folded into the [private repository] entry [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## cbe3ee3 2026-09-02 K-3 precondition COMPLETE (arms 1-3, verdict population, seed 0): NO FOLD-BACK, verdict proceeds

````text
Registered P-stage runs on data/prompts_k3_verdict.jsonl (210 prompts,
seed 0, instruments on, --load-4bit; memo no-amendment lock engaged at
first read). Pooled results:
  arm 1 vanilla g4:  t/c 3.032023206871054  budget 1.319251116197051
  arm 2 draft-conf:  t/c 2.9538317962231004 budget 1.274202241344063
  arm 3 (a)-probe:   t/c 3.032474549280555  budget 1.318867216804201

FOLD-BACK EVAL (registered, mechanical): arm 3 vs arm 1 tokens/call
delta via stats.paired_ratio_delta_ci (per-prompt n_emitted/n_blocks
from the committed stats.jsonl files, n_boot 2000, seed 0):
  delta +0.000451, CI95 [-0.001952, +0.003220]
CI95 upper > 0 => the fold-back condition (upper < 0) does NOT fire.
Verdict stage proceeds; arms 4-5 launched on the same population/seed.
These arm 1-3 records ARE the verdict data for arms 1-3 (BLUEPRINT
P-stage registration); no rerun.

Note for the finding: arm 3 is a near-exact null vs vanilla (its
stop-q0.95 threshold rarely fires; paired trajectories nearly
identical => the tight CI). Byproduct raw arrays gitignored per E8;
summaries carry per-file sha256 bindings.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 32f34ec 2026-09-02 FUTURE_IDEAS: provenance correction on the [private repository] entry (user, 2026-09-02) [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## 713a1cf 2026-09-02 FUTURE_IDEAS: post-arc asset distillation (probe playbook, data generator) + cross-repo [private repository] idea [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## e0ae94f 2026-09-02 K-3 stage E: threshold searches complete (arms 2/3/4), critic-recomputed; selections frozen

````text
Registered frontier search executed, 97 evals total (42/23/32 vs the
114/arm bound). Selections (val, 30 prompts, seed 0):
  arm 2 draft-conf: stop q0.25 extend q0.5,  t/c 3.096891, budget 1.274671
  arm 3 (a)-probe:  stop q0.95 extend q0.05, t/c 3.147662, budget 1.271306
  arm 4 (c)-probe:  stop q0.4  extend q0.05, t/c 3.191970, budget 1.249083
All budgets <= B_ref 1.2770393536617148.

Critic recompute from the raw state files: all 97 eval ratios bit-exact
from per_prompt rows; warm-start bisection replay matches the logged
eval order exactly (no off-procedure evals); frontier / exclusion /
minimality evidence reproduces; selection key reproduces all three
payloads and thresholds files; header bindings (b_ref, byproduct shas,
prompts sha, grids shas) verified. CLEARED with one blocking
documentation objection, resolved in this commit:

- BLUEPRINT dated erratum: the registered "constrained max over its
  evaluated set" sentence is falsified by arm 2's own log (feasible
  (q0.15,q0.7) at t/c 3.124012 > selected 3.096891 - a realized
  inversion of the expectation-level frontier argument). Selection
  stands (post-hoc switch = procedure-shopping; gap is inside noise,
  CI95 [-0.129,+0.177]); residual is anti-conservative (~0.027 val
  t/c) and now covered by a pre-registered contingency: a narrow
  arm-4-vs-arm-2 verdict pass (< +0.031 t/c above the +0.062 bar)
  triggers one robustness run at the alternative cell; the WIN must
  then hold against both arm-2 variants.
- Disclosures carried into the finding: arm-3 tuning degenerate
  (all-e0 frontier, grid-edge winner, span inside single-eval noise);
  arm-4 stop-q0.15 exclusion margins +1.083e-4..+2.87e-3 with a
  second realized inversion (outcome-irrelevant); bit-identical
  plateaus across distinct materialized thresholds = driver-gate
  carry #2 (per-eval RNG freshness) observed holding in production.

Suite 306 passed + 1 skipped; lint_findings OK (19).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 0663864 2026-09-02 K-3 threshold-search driver + B_ref evidence (B_ref = 1.27704), critic-gated

````text
results/real/k3_val_arm1.*: the registered E5 B_ref/materialization
run (arm 1, val split, seed 0, instruments on): 30 prompts, 2450
blocks, B_REF = pooled drafted-per-emitted = 1.2770393536617148
(9800/7674, critic-recomputed bit-exact), tokens/call 3.1322,
mean-of-prompts acceptance 0.7626 (on the committed 0.763 basis),
30/30 byproduct shas in the summary. Byproduct rows >= 1 are the
quantile-materialization distributions (E12 row-0 filter).

Search machinery (THRESHOLD-SEARCH REGISTRATION 2026-09-02):
- sideband/scheduler.py: _min_feasible_extend (warm-start + bisection
  on realized budget; terminal candidate always verified by its own
  eval; None = excluded), search_frontier, select_thresholds (max val
  tokens/call, ties -> lower budget -> lower stop -> lower extend;
  the selection-time feasibility assert = driver-gate carry #1).
  Critic measured the implementation's worst case over all monotone
  cutoffs + 400 adversarial non-monotone patterns: 6 unique
  evals/level, so the registered <= 114/arm bound holds as written.
- tests/test_scheduler.py TestFrontierSearch (6): brute-force
  equality within the 6/level bound; exclusion + all-infeasible;
  noise never fabricates feasibility; tie-breaks; assert-fires;
  B_ref required.
- tools/k3_threshold_search.py: the driver (no search logic of its
  own): binds the val run, freezes B_ref into the sha-headed state
  file (refuse-on-mismatch resume), materializes grids from
  CONSULTING blocks only, models loaded once, fresh spawn(0,n) per
  eval + encoding sha assert (carry #2), dedupe recorded as
  dedupe_of (critic: semantically exact, deterministic across
  resume), FAILED_INFEASIBLE corner labeled comparability-fallback,
  outputs search payload + k3_thresholds_arm{N}.json (load_thresholds
  format verified line-by-line by the critic). Critic fix applied:
  the overwrite guard refuses on payload existence alone (a completed
  search is never silently re-run); payload carries the
  warm-across-excluded and reader-free-arm-2 disclosures.
- .gitignore: negations for the three search state files.

Critic: B_ref evidence + machinery CLEARED (asks (i)-(vi) all held:
no fabricated feasibility, dedupe sound, single-block edges loud-not-
silent, thresholds format compatible, no cross-eval state leak, no
procedural asymmetry favoring arm 4) after the one-line overwrite-
guard fix. Suite 306 passed + 1 skipped.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 36600cb 2026-09-02 K-3 tap rider PASS (16/16) + threshold-search registration, critic-verified

````text
results/real/k3_tap_rider.json: live-tap fidelity rider verdict PASS,
16/16 triples at rng lineage 0, 12/16 from rejection-terminated blocks
(top-up never fired), 2/16 anchors shared with the calibration sample
(critic-verified: excluding both, the 14 fresh triples independently
clear every gate with >= 4x margin; the entropy max is one of the
shared anchors reproducing the calibration comparison bit-identically
- a free reproducibility check, not contamination). Margins: overlap
28..31 vs floor 20; mass linf max 0.0600 vs 0.1109; entropy max 0.1303
vs 0.3909. THE LIVE INSTRUMENT IS VALIDATED - stage E closes.

BLUEPRINT: THRESHOLD-SEARCH REGISTRATION (dated 2026-09-02, before the
B_ref run, the driver tool, or any tuning eval exists): measured cost
basis (347.0 s per 30-prompt val eval); the frontier argument (at
fixed stop level, lowering the extend level weakly raises both
realized budget and tokens/call, so each stop level's best feasible
point is its frontier point); pinned deterministic procedure
(per-stop-level bisection on realized budget with warm-start check;
worst case <= 114 evals/arm, ~11.0 h at the measured basis - critic
arithmetic fix pre-commit; dedupe on identical materialized values;
feasibility <= B_ref EXACTLY; infeasible stop levels excluded;
FAILED-INFEASIBLE corner branch labeled a COMPARABILITY FALLBACK
outside the constrained-max frame, structurally near-unreachable,
B_ref-tripwire named); selection completion (max val tokens/call,
ties to lower realized budget, residual ties to lower stop then lower
extend - zero residual discretion); honesty clauses (expectation-level
monotonicity; noise risks under-optimization never gate invalidity;
identical procedure across arms so pruning cannot favor the telemetry
arm; claim = constrained max over the EVALUATED set); mechanics
(B_ref = pooled drafted-per-emitted of the NEW seed-0 vanilla val
run, frozen at first read; driver tool loads models once with
DRIVER-GATE CARRIES pinned: selection-time feasibility assert,
per-eval fresh spawn(0,n) + encoding asserted in-process; eval log +
sha-headed state file committed; k3_thresholds_arm{N}.json outputs).

Critic: rider payload recomputed triple-by-triple (16/16 agrees);
registration cleared after the 95->114 arithmetic fix; corner-branch
label and driver-gate carries applied as prescribed. Suite 300+1s.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 7d3450f 2026-09-02 K-3 stage-E evidence: export/containment/calibration PASS + tolerance amendment, critic-verified

````text
GPU chain (committed order, exit 0 end to end):
- results/real/k3_probe_weights.npz + .meta.json: the four live probes
  (L1_concept_k16 off{2,3} {a,c} linear s0); binding gate 4/4 PASS
  bit-exact vs committed probes_s1 state cells; E7 self-check 3000
  anchors/cell, worst prob dev 1.35e-06 (30x under the 1e-5 pin);
  meta carries tap params, harvest/bucket shas, harvest_temperature.
- results/real/k3_containment_rider.json: E10 verdict PASS at the
  STRONGEST branch — OFF/OFF2 bit-identical armed the bit-identity
  bar, and ON/OFF is bit-identical on all 10 prompts (first
  divergence None everywhere). The live instruments are read-only at
  the bit level in the registered containment configuration (one
  GPU/kernel stack, vanilla arm — scope kept).
- results/real/k3_tapcal_arm1.*: the registered calibration live run
  (arm 1, val prompts, seed 100, instruments on): 30 prompts, 2410
  blocks, tokens/call 3.156, drafted-per-emitted 1.2674 (= 4/3.156
  exactly), mean-of-prompts acceptance 0.7703 (pooled 0.7697).
  Byproduct raw arrays gitignored; per-file shas in the summary.
- results/real/k3_tap_calibration.json: 30 aligned + 30 off-by-one
  anchors, 15/30 rejection-terminated. ALIGNED: min-overlap 27..32/32,
  mass512 L-inf <= 0.03698, entropy <= 0.13030. MISALIGNED: overlap
  <= 13, mass >= 0.21398, entropy min 0.0063.

STAGE-E TOLERANCE AMENDMENT (BLUEPRINT, dated 2026-09-02,
post-calibration pre-rider; E9 mapping applied mechanically, critic
recomputed every constant from the payload): SLOT_OVERLAP_MIN =
ceil((27+13)/2) = 20; MASS_LINF_MAX = 3.0 x 0.03698068857192993 =
0.11094206571578979; ENTROPY_ABS_MAX = 3.0 x 0.1302955150604248 =
0.3908865451812744; ARGMAX_GAP = MASS_LINF_MAX. Exact products, not
rounded (rounding would need a rule E9 never supplied; S1/S3 rounded
- disclosed difference). Separation: mass separates cleanly
(misaligned min 1.93x above tolerance); entropy does NOT separate at
the minimum (S1 caveat, adjacent positions) - the AND-structure is
load-bearing, overlap the sharp discriminator, misaligned entropy p50
still 2x above tolerance. Constants set in k3_tap_rider.py,
refuse-until-pinned guard retained, cycle bound armed.

Critic: amendment round CLEARED (all four constants recomputed exact;
E12(iv) duties discharged; exact-products reading endorsed;
calibration run internally coherent to the last digit; containment
scope kept). Suite 300 passed + 1 skipped.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 69cb8f2 2026-09-02 K-3 stage E: live scheduling instrument + clarifications E1-E12, critic-gated

````text
BLUEPRINT: STAGE-E ENGINEERING CLARIFICATIONS E1-E11 (dated 2026-09-02,
written before any stage-E code existed) close the arc registration's
open DOFs: E1 live probes = seed-0 exports of the four committed
L1_concept_k16 off{2,3} {a,c} linear cells (binding gate incl.
val_acc_best/best_epoch); E2 agreement semantics (full-label-space
argmax, comparison DEFINED only when both sides are concept classes —
glue on either side fires neither STOP nor EXTEND); E3 arm-2 mapping
(stop on LOW q(sampled), extend on high min, per-position quantiles);
E4 extend = one decision per block after base drafting; E5
materialization = vanilla val run block-start signals, np.quantile
linear, seed conventions; E6 gate arithmetic (tokens/call = emitted per
verify call, prefill excluded uniformly; delta = paired_ratio_delta_ci
joint cluster bootstrap); E7 harvest-dtype feature mirroring + f32
logits -> f64 softmax inference + export self-check; E8 byproduct
format; E9 live-tap rider + tolerance MAPPING pinned before any
comparison data; E10 containment rider with both branches pinned; E11
change scope. E12 (dated, on the critic's stage-E round): BLOCK-1
CONSULT EXCLUSION — the prefill anchor's offset-1 token IS drafted
position 1, so block-1 consults would misalign the off2 probe by one
position; no adaptive arm consults on block 1 (uniform, D-11), E5
materialization restricted to consulting blocks; temperature binding;
E8/E9 errata; finding-carry notes.

Instrument (default paths behavior-identical, tested):
- sideband/scheduler.py: Thresholds/materialize_thresholds,
  SchedulerPolicy (fixed/draft_conf/probe), anchor_free_summaries,
  probe_input, LinearProbe — pure numpy, CI-tested.
- sideband/stats.py: paired_ratio_delta_ci (E6 estimand), tested
  incl. exact-collapse-to-paired_cluster_delta_ci when trials shared.
- sideband/probes.py: train_probe +return_weights (default
  byte-identical, tested).
- sideband/real/k3_live.py: LiveShadowTap (all-position capture),
  LiveNormCatch, LiveReader (requires all four probe cells),
  ByproductRecorder, K3Config, build_live_reader (shared constructor),
  load_probe_weights (sha-bound).
- sideband/real/hf_specdec.py: spec_decode_prompt +k3 param — prefill
  + crop-one (every block's verify capture contains its own anchor row
  base+accepted-count), k3 drafting branch with consults gated off on
  block 1 (E12), gamma->g_block refactor, anchor read/record after
  crop, k3 stats (tokens_per_call, drafted_per_emitted, stop/extend
  counts).
- tools/export_probe_weights.py: binding gate bit-exact vs committed
  probes_s1 state cells (hard-indexed fields) + E7 self-check;
  records tap params, harvest/bucket shas, harvest_temperature.
- tools/run_k3_arms.py: arms 1-5 runner (house meta/stats/gen/summary/
  resume; byproduct npz per prompt, shas in summary; --select-split
  val; --no-instruments = containment OFF mode; temperature bound to
  the harvest when instruments on).
- sideband/real/k3_tap_rider.py: --mode calibrate|rider, constants
  None until the dated tolerance amendment; rejection-terminated
  anchors required; calibrate/rider intersection count disclosed.
- tools/k3_containment_rider.py: ON/OFF/OFF2, both E10 branches.
- .gitignore: results/real/*.byproduct/ (raw byproduct; summary
  carries the shas).

Tests: tests/test_scheduler.py (29), stats + probes additions,
tests/test_tools_and_real.py TestK3SpecDecode (4: k3-off-config vs
legacy torch.equal EXACT through prefill+crop-one; forced stop/extend
block shapes pinning the E12 exclusion and E6 arithmetic; reader/
recorder anchor-position invariants confirming the critic's prefill
off-by-one). Suite 300 passed + 1 skipped; lint 19 OK.

Critic: round 1 = 2 blockers (block-1 skew; missing CPU coverage) + 9
advisories — all fixed as prescribed; verification round cleared.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## dc03bfa 2026-09-02 D2/D3 evidence committed + K-3 confidence signal FROZEN: raw posterior at L1/off2, both arms; freeze pins close the two threshold-semantics DOFs

````text
results/real/error_predictor_s1.json + sha-headered state file land
as committed evidence (36/36 cells, partial false, ALL 36 binding
gates PASS — every retrained base probe reproduced its committed
Phase-3 cell bit-exactly, full audit not spot; runtime 8,250.7s,
per-cell sum 8,247.6s, fresh single pass). Critic RECOMPUTED the
entire decision block from the state file alone: max abs deviation
0.0; the pre-registration smoke cell is bit-exact across the
instrument changes (behavior-neutrality confirmed empirically).

DECISION (both arms, clear margins, tie-breaks never engaged):
selected cell L1_concept_k16/off2; signal_form RAW_POSTERIOR (test
ECE 0.0082 (a) / 0.0408 (c) — the (c) swap clears the 0.05 bar by
0.009, disclosed). Selective prediction is real: test precision@0.20
0.7919 (a) / 0.8356 (c) over base rates 0.6059/0.6223 (+19/+21
points); (c)-(a) gap +0.051 val / +0.044 test.

FREEZE PINS (dated, before any val threshold search): (1) STOP
threshold = one quantile level materialized per-offset on each
offset's own val confidence distribution (normalizes the off2/off3
shift, keeps the search 2-D); (2) EXTEND = agreement at BOTH offsets
2-3 AND min(conf_off2, conf_off3) >= extend quantile level. Critic
wording advisories applied (byproduct 'no GATING quantity'; stage-E
logging pinned READ-ONLY, D-6 preserved). OQ-14(ii)/(iii) marked
ANSWERED at S1 with status notes.

Suite 260 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 41bdbc7 2026-09-02 FUTURE_IDEAS: telemetry-Medusa / draft-free drafter (user-proposed 2026-09-02) with measured sizing + top-k containment pilot as promotion condition [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## cf90b41 2026-09-02 OQ-15 primary supervision = analytic-acceptance regression (dated 2026-09-02, pre-data); byproduct amendment extended (per-position analytic values); docs/FUTURE_IDEAS.md created [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]

````text
OQ-15 gains its primary regression target: the per-position analytic
acceptance 1-TV(p_j,q_j) (the D-9 estimand the harness already
computes) — graded, denser than binary accept/reject, and identical
to the quantity a scheduler consumes; binary head stays as the
classification variant. The K-3 byproduct amendment now also logs the
per-position analytic values (zero decision content, pre-arm-run,
flagged for the critic's next round alongside h_a).

docs/FUTURE_IDEAS.md: new idea-tier parking lot, explicitly [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
unregistered with a promotion rule (an idea becomes real only via its
own OQ ledger entry). Seeded with the 2026-09-02 session batch:
run-length distribution head, boundary/event flags (F-9-aligned),
future-distribution distillation (the F-14 fine-k open remainder),
contrastive alignment as OQ-16's recommended-if-promoted first stage,
self-supervised telemetry pretraining, zero-label anomaly scoring,
runtime-monitoring aside; OQ-7/OQ-9 cross-referenced, not duplicated.

Suite 260 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## eaea1d5 2026-09-02 OQ-16 ledgered (vector reconstruction: telemetry -> hidden-state steering vector, SD^2 actuator under the observability constraint) + dated K-3 byproduct amendment (anchor h_a logging)

````text
OQ-16, user-proposed 2026-09-02: keep addresses-only across the wire,
retarget supervision to dense regression (reconstruct the steering
vector; SD^2's proven injection consumes it draft-side, lossless per
F-0). Escapes the bucket-bias bounds and the topic-proxy margins; the
committed OQ-6 h-probe result (h LOSING to telemetry at matched
linear budget, both sources) is an extraction-budget statement and
does not bound reconstruction toward h. Queued as a K-3 FOLD-BACK
candidate alongside OQ-15 (one fold-back permitted by the kill text);
mandatory free-features reconstruction baseline + equal-dims noise
anchor pinned at ledgering; ~100x underdetermination sized honestly
(steering-relevant subspace is the question, mechanism-tier).

BLUEPRINT K-3 arc: dated pre-run amendment (2026-09-02, before any
precondition/verdict arm ran; D2/D3 unaffected) — byproduct logs
additionally record anchor h_a per block, all arms; zero decision
content; feeds both fold-back candidates from the same runs. Flagged
for the critic's next round.

Suite 260 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f623e33 2026-09-01 D2/D3 instrument: error-predictor + calibration tool, critic-gated; full_eval probe path (default byte-identical)

````text
train_probe gains optional full_eval (per-anchor correctness/pred/
max-softmax on all splits, computed post-training under no_grad;
default return byte-identical — critic-verified structurally, RNG
self-seeded per call; asserted by TestD2D3Instrument).
tools/run_error_predictor.py: 36 cells (3 spaces x offsets 2-3 x
arms a/c x seeds 0-2), BINDING GATE refuses unless the retrained
base probe reproduces its committed Phase-3 state cell bit-exactly
(test_acc + per-prompt clusters + val_acc_best + best_epoch, the
critic's strengthened form); LINEAR heads on own-arm features
predict base correctness; precision/coverage {0.05..0.50} + ECE
readouts; mechanical per-arm decision per the dated pre-run
clarifications; bind_spaces_to_harvest on the load path (registered
consumer rule); sha-headered state file, per-cell runtimes.
BLUEPRINT: clarifications timing corrected to 'before any REGISTERED
cell' with the dated smoke disclosure (one guard-permitted scratch
cell, numbers seen, no clarification content derives from it,
tie-break caveat owned). Critic instrument gate: byte-identity and
leak-freedom VERIFIED at code level, both blockers applied verbatim,
cleared to run.

Suite 260 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 2db51aa 2026-09-01 K-3 verdict prompt set committed BEFORE any D2/D3 output exists (arc Amendment #2)

````text
data/prompts_k3_verdict.jsonl: 210 prompts, same recipe as the
committed probe population (3 families x 70, verb split 35/35 per
family, round-robin interleave, one unique topic per prompt for
prompt-cluster independence). Zero topic overlap with
data/prompts.jsonl (checked mechanically at generation; the
generator refuses overlap and overwrite). This is the verdict
population for the K-3 Attempt #1 gate; the 150 probe-train prompts
are excluded from the gate per the registered amendment, and the
population-selection surface closes with this commit — no D2/D3
diagnostic has run yet.

Suite 256 passed + 1 skipped.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 1c14db4 2026-09-01 K-3 Attempt #1 arc REGISTERED: adaptive-scheduling actuator, matched-budget gate, D2/D3 diagnostics — three critic rounds, all pre-result

````text
PHASE-4 K-3 ATTEMPT #1 ARC REGISTRATION + D2/D3 DIAGNOSTICS
REGISTRATION (BLUEPRINT, after the Phase-4 charter) + revised DATED
PRE-RESULT AMENDMENTS (ECONOMICS.md). Actuator family: telemetry-
informed adaptive block scheduling (q never modified; STOP consults
offsets 2-3 only; EXTEND to gamma_max=6 under the labeled registered
bet — horizon-level ALLOCATION triggers, not off-6-7 prediction).
Arms: vanilla gamma-4 / skeleton-matched draft-confidence incumbent
(claim-scope bound vs unrestricted SpecDec++) / (a)-probe free /
(c)-probe telemetry / fixed gamma-6 descriptive frontier control.

GATE (amendment #1, hardened across three critic rounds): tokens per
target call AT MATCHED DRAFTING BUDGET — constrained maximization on
val at cap B_ref exactly, pinned quantile grid, all-hold win (every
comparator: CI lower > 0, point >= +0.062, pairwise budget guard
epsilon 0.01), pinned void semantics with seed-1 reserve. Measured
basis from committed phase0b records: accepted-length distribution
P(k=0..4) = 0.2509/0.1751/0.1341/0.0953/0.3445 over 17,220 blocks
(critic-verified bit-level); information-free skew residual measured
+0.0103 (17% of bar). Critic rounds killed in sequence: acceptance
gameable by truncation; raw tokens/call gameable by gamma inflation
(~7x bar, information-free); +/-0.05 tolerance funding 83% of the
bar; the round-2 prescriptions' own cap/guard collision voiding all
wins. Anchor corrected to base+accepted-count (phantom-context
hazard; rider must include rejection-terminated blocks); probe
export bit-exact reproduction gate; D2/D3 one-choice-one-rule
selection (VAL-selected at coverage 0.20, test reported, inherited;
ECE<=0.05 swap); precondition operationalized (arm-3 CI upper < 0
folds back) on the verdict population; verdict prompt set to be
authored+committed BEFORE any D2/D3 output is read (amendment #2,
next action).

Suite 256 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 59b3305 2026-09-01 OQ-15 ledgered: outcome-supervised readout — telemetry as symbols, decoder behavior as supervision (user-proposed 2026-09-01; queued behind the K-3 error-predictor attempt)

````text
Retargets supervision from the concept proxy task to draft-failure
outcomes; escapes F-14's actuator-specific oracle bound and the
proxy-margin bounds. Pinned at ledgering: the information ceiling
relocates to I(telemetry; draft-failure) (unmeasured); needs a paired
harvest (committed harvests are target-only, no failure labels);
mandatory free-features failure-predictor baseline (SpecDec++ feature
class) + equal-dims noise anchor; economics-memo K-3 bars apply
unchanged; cheap draft-free pilot on existing harvests gates the
paired-harvest spend. Scaling extrapolation recorded with caveats
(scale reaches the ceiling, cannot raise it; pair-specific;
off-policy drift; K-5 distillation requirement).

Suite 256 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 39e05c0 2026-09-01 K-5/K-6 economics memo: K-3 win/materiality bars PINNED before any actuator experiment exists

````text
docs/ECONOMICS.md (new) + a matching PHASE-5 SKELETON + K-3 BARS
REGISTERED block in BLUEPRINT Phase 5. Written after F-18, before any
K-3 actuator work. The memo decomposes the main argument (existence
DONE at S1+S3, both priced; conversion K-3 OPEN with the
F-12/F-13/F-14 graveyard tabulated; economics OPEN), assembles the
measured-inputs table (every value source-cited), derives the
sideband widths (S3 513-768 bits/token, S1 676-1152, vs SD^2's
65,536 bits/position — ratios 57-128x) and the acceptance <->
tokens/call coupling (~6.2, one F-12 dose point, labeled a
linearization), and splits the verdict into two deployment lanes
(A: software index-stream steering in MoE serving — no device, but
SD^2-in-software owned as the in-lane alternative; B: the
memory-side device, which needs a defended values-cannot-cross
boundary or concedes per K-6's own text).

PINNED BARS (may not be amended after any K-3 result is read):
- K-3 WIN: paired deltas vs ALL THREE comparators (vanilla + both
  D-11 free arms); gating delta = the MINIMUM; CI95 lower > 0, point
  >= +0.010 acceptance, analytic concordant. Anchors: F-14's
  dead-actuator oracle ceiling CI-upper +0.0069 (tested coarse-k
  cell), ~2x harness CI half-width.
- Lane-B operational bar: point >= +0.044 acceptance (~+0.27
  tokens/call); the motivating "25% of SD^2" label mixes bases
  (~37% like-for-like) — disclosed, the acceptance number gates.
- Phase 4 stays blocked by its own registered condition
  (non-negative free arm); these bars do not unblock it.
- S2 settled as Lane-B breadth, off the K-3 critical path.

Critic pre-commit gate: all table numbers verified source-exact, all
derived arithmetic recomputed exact; SEVEN wording/precision blockers
(range splicing in two table rows, Lane-B base mismatch, WIN-bar
comparator ambiguity, Lane-A "K-6 moot" overreach, F-14 quoted above
strength, a pointer bug, an OQ miscitation) all fixed as prescribed
before this commit, plus four advisories (Phase-4 block statement,
S3 horizon wording, off3 topic-share ratio, both Lane-B device
variants) incorporated.

No wall-clock claims (D-9/K-5 stand). No findings entry (registration
text, not evidence). Suite 256 passed + 1 skipped; lint 19 OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 6cf7e1e 2026-09-01 F-18: S3 P1-analog — P1-SURVIVES both harvests; the address-stream margin is not prefix-topic state (histogram family)

````text
The conditional P1-analog pinned in the S3 registration (owed at F-17)
ran to completion. Instrument: tools/run_posthoc_topic.py
source-parametrized (defaults byte-identical to the committed S1
instrument — asserted by TestPosthocParametrization, full-path
neutrality critic-verified at a PRE-RUN gate; bind_spaces_to_harvest +
--n-slots binding on load; cross-source primary lookup returns
INCOMPLETE). Instantiation registered in BLUEPRINT before any
registered cell ran, with a dated disclosure of the guard-permitted
smoke (later verified bit-exact vs the registered state — an
accidental determinism check).

RESULTS (72 cells x 2 harvests, partial=false, runtimes 14,265.9 s /
7,202.9 s): the pinned primary cell M2 L1_olmoe_k16/off2/linear fired
all three conditions on the PRIMARY harvest: +0.012958 [+0.008783,
+0.016809], per-seed +0.012667/+0.013356/+0.012852; replication
confirmatory +0.017465 [+0.013190, +0.022209], row-wise |delta| <=
0.0045 (M2) / 0.0051 (M2n). M3 = (at)-(a) ~0 at L1/L2 (all
CI-crossing, |point| <= 0.00094); one honest qualifier: a small REAL
topic component at the L3 group lens (M3 off3 +0.006972 fires the
floor on primary), ~1/10 the tap's L3 margin (M2 +0.067859). M2noise
band -0.0108..+0.0015 (wider than S1's) — dilution depresses M2, the
equal-dims M2n confirms. (t)-(b) CI-negative in all 12 rows both
harvests.

The critic RECOMPUTED all six readout families and BOTH conclusion
labels from the state files alone (fresh implementation): max abs
deviation 0.000e+00; grid identity exact; sha chain closed (posthoc
headers == committed grid headers == harvest metas; phase3 +
label-space shas match); args == the pinned commands verbatim; ZERO
BLOCKERS, both rounds (pre-run gate: one wording blocker, fixed
pre-launch with the smoke disclosure).

Mechanism language F-17 withheld is now permitted in F-18's registered
form: the S3 signal lives in the model's computation, not its emitted
text, at the histogram family level — with the L3 qualifier and the
prompt-token residual standing. Dated erratum in-finding and in the
BLUEPRINT outcome block: t dim is 560 IDENTICAL to S1 (alphabets merge
to the same 511/16), only the slots block differs (1024 vs 2048);
"differ from S1's 560/3266" was wrong as drafted.

Payload provenance f3bb32e-dirty: the dirt IS the instrument +
registration landing in this commit (critic-gated pre-run; smoke
bit-exactness + recompute make silent drift immaterial to the
numbers). FINDINGS.md: F-18 appended (regime + source per D-4).
BLUEPRINT: instantiation block (with smoke disclosure) + outcome block
+ erratum. No acceptance claims, no wall-clock claims; K-3 untouched.

Suite 256 passed + 1 skipped; lint_findings OK (19 findings).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f3bb32e 2026-09-01 F-17: EXISTENCE at S3 CONFIRMED — pure address-stream MoE-router telemetry replicates on fresh seeds

````text
Replication grid (registered step 10, fixed L3 lens, 156 cells + 6 R2,
partial=false, runtime 6,009 s): results/real/probes_s3_replication.json
+ its sha-headered state file land here as committed evidence. The
critic INDEPENDENTLY RECOMPUTED the entire decision from the state file
alone (fresh implementation; per-cluster counts -> seed-summed
prompt-cluster bootstrap n_boot 2000 seed 0): max abs deviation
0.000e+00 across all margins, CI bounds, per-seed points, R2, floors,
and OQ-6 rows; grid identity exact (zero missing/extra/duplicate
cells); ZERO BLOCKERS, both rounds of this arc.

The PINNED gate L1_olmoe_k16/off2/linear RE-FIRED on fresh seeds 8-11:
+0.0173 [+0.0133, +0.0221], per-seed +0.0180/+0.0175/+0.0163 — all
three registered conditions. Branch: CONFIRMED (OPEN requires
pinned-triple fail; NOT-REPLICATED requires nothing to re-fire; R1-S3
passed 16/16 at rng-seed 1). The whole firing set reproduced
cell-for-cell: same 7 of 12 triples fire, same 5 don't; margins agree
within 0.006 (median ~0.002). Headline L3/off2 +0.0721 -> +0.0730
[+0.0646, +0.0813].

Sha chain closed: state header == committed harvest_moe_r metas ==
rider bindings == payload provenance; concept_groups_olmoe_v1
sha-identical across 808266e/dec515b/disk (read, never refit);
provenance 83406b1-dirty = untracked-only (HANDOFF + state file),
attested; zero tracked drift.

Disclosures carried into F-17's caveats (critic list): confirmatory
weight rides the pinned cell only (7/7 breadth is descriptive);
L2/off3 materiality edge on BOTH runs (points +0.005145/+0.006169
clear the 0.005 floor, CI-lowers below it; rule gates on point;
verdicts robust to dropping; boot-seed scans 1..10 all positive —
replication gate [+0.0132,+0.0135], edge [+0.0042,+0.0044]);
L1/off3/mlp256 non-firing profile degraded on replication (fails all
three, one seed negative); glue is the majority class in all three
spaces on both harvests (0.5803/0.5865, 0.4214/0.4276); OQ-6 h-a
crossing at off2, CI-negative at off3/4 on both runs (wording guards);
cosmetic runner strings (S1 date in decision.rule; generic provisional
verdict text, superseded by the pinned branch per S1 precedent); audit
provenance d8cb7a0-dirty (ran before its own evidence commit).

FINDINGS.md: F-17 appended (regime + source per D-4, all disclosures).
docs/BLUEPRINT.md: S3 OUTCOME + REPLICATION OUTCOME block appended to
the S3 registration; the conditional P1-analog is now OWED before any
mechanism language attaches to S3. Per-source scorecard: S1 YES, S3
YES, S2 unrun. K-3 remains the load-bearing open risk. No wall-clock
claims, no acceptance claims.

Suite 254 passed + 1 skipped; lint_findings OK (18 findings). Code
unchanged at 83406b1.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 83406b1 2026-09-01 S3 replication harvest evidence: 827k pairs, seeds 8-11; R1-S3 16/16 PASS at rng-seed 1

````text
Registered replication chain (BLUEPRINT S3 block step 10), run in pinned
order after the primary grid's provisional EXISTENCE (dec515b):

results/real/harvest_moe_r/: 4 sha-bound seed metas (npz gitignored) +
harvest_moe_r_summary.json: 827,324 pairs, split 591,904 / 115,880 /
119,540 train/val/test, no problems. The tool's EXIT_BAR_NOT_MET
verdict is the Phase-2 FULL-harvest rule, superseded by the
registration's 4-seed replication pin (S1 precedent, BLUEPRINT F-15
outcome block). Harvest ran with --skip-preflight (Windows
pending-reboot advisory; flag recorded in meta args; seed-resumable by
design).

harvest_audit_olmoe_r.json: contamination test-in-train 0.37% distinct
/ 0.47% occurrence; duplication mean 0.9940 (min 0.9147); loopy rows
0. k16 off2 test majority = glue bucket at 0.5865 on the replication
data (primary: 0.5803).

harvest_fidelity_rider_olmoe_r.json: R1-S3 16/16 PASS at rng-seed 1
(pinned lineage), first attempt, cycle bound not stressed on either
harvest. Worst per-triple min expert overlap 7/8 (bar >= 5), worst
mass512 L-inf 2.62e-02 (bar 0.20; calibration band 0.0666). Rider
binds the exact npz shas it validated.

Archival duty: second on-disk copy at
<path outside the repository, scrubbed at export>, all 4 npz
sha256s verified against the committed metas after copy
(operator-attested; no artifact records the check).

Replication grid RUNNING (fixed L3 lens concept_groups_olmoe_v1, never
refit; gate L1_olmoe_k16/off2/linear; pre-named branches decide
CONFIRMED / OPEN / NOT-REPLICATED). Its payload + state file land with
the verdict commit after the critic round. Suite 254 passed + 1
skipped; code unchanged at d8cb7a0.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## d8cb7a0 2026-09-01 OQ-13 (S3 margin composition: two-stage decomposition, balanced-lens robustness, floor-reduction menu) + OQ-14 (extraction ceiling: per-layer ensemble, error-predictor head, calibration; symmetric-upgrade guardrail) - user-proposed 2026-09-01, all post-replication registered secondaries

## dec515b 2026-09-01 S3 grid: provisional EXISTENCE, critic-verified by recomputation; replication running

````text
Registered step-9 grid on the S3 harvest (156 cells + 6 R2 shuffle
cells, partial=false, runtime 12,211 s): results/real/probes_s3.json +
its state file (committed evidence; sha-header bound to the 8 harvest
metas). Verdict printed and INDEPENDENTLY RECOMPUTED by the critic from
the state file alone (per-cluster counts -> seed-summed prompt-cluster
bootstrap n_boot 2000 seed 0, two implementations agreeing < 1e-15):
every margin, CI bound, per-seed point, the firing set, R2, R3, OQ-6,
floors, and the multiplicity arithmetic are BIT-EXACT. No blockers.

7 of 12 offset>=2 (telemetry+free vs free) triples fire the registered
three conditions + 0.005 materiality, all three seeds positive:
- L1_olmoe_k16 off2: linear +0.0147 [+0.0113, +0.0182] (THE PINNED
  REPLICATION GATE CELL), mlp256 +0.0200 [+0.0167, +0.0232]
- L2_olmoe_k512 off2: linear +0.0206 [+0.0171, +0.0244];
  off3 linear +0.0051 [+0.0036, +0.0066]
- L3_olmoe_groups_v1: off2 +0.0721 [+0.0652, +0.0792] (headline),
  off3 +0.0419 [+0.0338, +0.0502], off4 +0.0207 [+0.0145, +0.0269]
R2 label-shuffle PASS at all offsets (both probes at the shuffled
floor, gaps <= 1.7e-5).

Registered disclosures (full list in the critic report; owed in the
eventual finding text):
- Multiplicity: 12 uncorrected triples -> family-wise false-EXISTENCE
  1 - 0.975^12 = 0.262 under a global null; hence PROVISIONAL, and the
  pinned replication (fresh seeds 8-11) is the arbiter.
- L2/off3 rides the materiality edge (point margin +0.00514 vs floor
  0.005; CI lower +0.00363 below it). The registered rule gates (iii)
  on the point margin; verdict robust to dropping this triple. Boot-
  seed scan 1..10 (disclosure only): fired CI-lowers all stay positive.
- S3's shape is NOT S1's: margins concentrate at off2 and in the L3
  groups space; L1 dies by off3 (+0.0020, below floor) where S1's L1
  off3 fired; free-baseline acc sits ~at the glue floor at off2
  (L1 +0.0013 over 0.5803). Do not borrow F-15 language.
- L3 lens is lopsided (two mega-groups cover ~461/510 concepts, incl.
  all 20 zero-degree buckets); the +0.0721 headline reads through the
  recorded lens per S1 precedent.
- OQ-6 h-a is CI-crossing or negative at every offset >= 2 (the
  2048-dim hidden-state probe adds nothing beyond free info here, and
  sits below (a) at off3/4); report with wording guards, never as an
  information bound.
- decision.rule string carries the hardwired S1 date (2026-08-30); the
  payload's top-level "registered" key correctly cites the S3 block
  (2026-08-31). Finding will cite the S3 registration.
- Payload provenance is 808266e-dirty: OPERATOR ATTESTATION - the dirt
  at write time was untracked-only (HANDOFF.md + the two probes_s3
  outputs committed here); tracked tree clean at 808266e throughout
  the run. No artifact records this beyond git status at review time.

Floors match harvest_audit_olmoe.json bit-exactly (majority class IS
glue in all three spaces: L1 0.5803, L2 0.4214, L3 = L2). Volume bar
met (1,647,264 >= 1M): seeds 8-11 stayed fresh for replication, now
harvesting -> results/real/harvest_moe_r (preflight overridden with
--skip-preflight on a Windows pending-reboot advisory; recorded in
meta args). Next: replication summarize/audit + archive, rider
rng-seed 1, replication grid vs the FIXED L3 lens; the pre-named
branches decide CONFIRMED / OPEN / NOT-REPLICATED.

Suite 254 passed + 1 skipped. Code unchanged at 808266e.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 808266e 2026-08-31 S3 harvest evidence: 1.65M pairs across 8 seeds, exit bar MET; R1-S3 16/16 PASS

````text
Registered steps 5-8 of the S3 pipeline (BLUEPRINT S3 block), run in
pinned order after the 8-seed harvest completed exit 0:

results/real/harvest_moe/: 8 sha-bound seed metas (npz gitignored per
protocol) + harvest_moe_summary.json (verdict OK, no problems):
1,647,264 (telemetry, label) pairs - exit bar 1M met with the
registered 8 seeds, no extension needed. Split 1,174,184 / 235,460 /
237,620 train/val/test.

harvest_audit_olmoe.json: contamination test-in-train 0.52% distinct /
0.64% occurrence; duplication mean 0.9887 (min 0.8645); loopy rows 0.
As pre-registered, the audit MEASURES AND NAMES the k16 floor concern
from the 1-bucket 95.7%-cover glue: majority class at offset 2 on test
IS the glue bucket (class 15) at rate 0.5803 (15/16 classes seen,
entropy 2.217 bits). L1_olmoe_k16 cells are judged against this floor.

harvest_fidelity_rider_olmoe.json: R1-S3 16/16 PASS at rng-seed 0,
first attempt, cycle bound not stressed. Worst per-triple min expert
overlap 7/8 (bar >= 5), worst mass512 L-inf 5.57e-02 (bar 0.20; inside
the calibrated aligned band 0.0666) - the address stream reproduces at
calibration fidelity under the armed tolerances. Rider binds the exact
npz shas it validated.

concept_groups_olmoe_v1.json: 16 groups over the 510 concept buckets,
fallback unused, first run is the artifact (overwrite guard armed).
Size profile skewed (two large groups 193/268, fourteen of 2..9);
glue-dropped train persistence 0.675 (groups) vs 0.229 (raw k16).

Archival duty (registered): second on-disk copy at
<path outside the repository, scrubbed at export> (16 files, 2.32 GB),
all 8 npz sha256s verified against the committed metas after copy
(operator-attested; no artifact records the check).

Code at 892a40a unchanged. Step 9 grid running; its state
file and payload land with the verdict commit after the critic round.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 892a40a 2026-08-31 S3 spaces + calibration + tolerance amendment (registered steps 1-4, critic-verified)

````text
Registered pipeline steps 1-4 run in pinned order, artifacts committed
as evidence:
- buckets_olmoe_k{16,32,64,512}.json: committed recipe verbatim
  (L2-norm, PCA-128, kmeans seed 0) on OLMoE's untied lm_head; all four
  converged (n_iter 101/67/115/57, none max_iter-bound), 0 empty
  buckets.
- gen_freq_olmoe.json: 52,145 tokens over the 210 committed prompts
  under the verified NF4+bf16-routers regime (mean generated length
  ~248 of 256 -> low EOS attrition; projected pairs comfortably above
  the 1M bar, to be confirmed by the harvest summary).
- glue_olmoe_k16.json (1 bucket, 95.7% top-100 mass cover) and
  glue_olmoe_k512.json (2 buckets, 86.2%): K-7 rule verbatim,
  concentration flags False, decoded glue tokens are textbook function
  tokens. k16's sensitivity axis is degenerate this run (same 1-bucket
  set at 70/80/90 cover) and its glue bucket holds 21.9% of the vocab
  -> the L1 majority floor may sit high; measured and named by the
  audit before any grid, as registered.
- fidelity_calibration_olmoe.json: 30 aligned + 30 off-by-one anchors,
  seed-100 non-audit, S1 calibration protocol verbatim; ALIGNED expert
  overlap 7..8/8, mass512 L-inf <= 0.0666, entropy <= 0.1676;
  MISALIGNED overlap <= 2, mass p50 0.887, entropy p50 0.766. The
  address stream reproduces almost exactly under the rider regime.
- TOLERANCE AMENDMENT (dated, BLUEPRINT S3 block) under the
  pre-registered derivation mapping: EXPERT_OVERLAP_MIN 5/8,
  MASS_LINF_MAX 0.20 (3.0x aligned max), ENTROPY_ABS_MAX 0.50 (3.0x;
  disclosed weakest separation, 1.53x below the misaligned median),
  ARGMAX_GAP 0.20. Constants set in fidelity_rider_moe.py (docstring
  updated to past tense); cycle bound ARMED.
- TestFidelityCalibrationConsistencyS3 pins constants<->evidence
  mechanically (betweenness, 3.0x mapping, below-median, gap >= 2x).

Critic verified the amendment BY RECOMPUTATION from the raw payload
(summary dists re-derived at 1e-12; both readings of the placement
mapping land on overlap 5; no number outside the registered mapping;
stage-A sweep found nothing disqualifying). Suite 254 passed + 1
skipped; lint 17 findings OK. Next: registered step 5, the 8-seed
harvest.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 3eb5efd 2026-08-31 S3 registration + instrument: MoE router address stream (OLMoE), critic-cleared

````text
Registers the S3 run of the Phase-3 protocol (BLUEPRINT "S3 RUN OF THIS
PROTOCOL", 2026-08-31, amended same day on critic review, all BEFORE any
S3 artifact exists): tap = the model's own top-8 expert ids per 16
router gates (addresses only, 96 B/token; router weights excluded by
construction), stored under the npz "slots" key so the committed
Phase-3 instrument runs verbatim at n_slots=64; NF4-with-bf16-routers
load regime; spaces rebuilt on OLMoE's own vocab (bucketize / freq /
K-7 glue verbatim, commands + evidence files pinned in the block);
R1-S3 tolerances pinned by dated amendment from a fresh calibration
BEFORE the rider runs (derivation mapping + pre-named
entropy-undercoverage mechanism + cycle bound; rng lineage starts 0);
replication PINNED before the primary grid exists (L1_olmoe_k16/off2/
linear + all non-firing branches; seeds 8..11 reserved, volume
extension starts at 12); conditional P1-analog. Model facts verified
from the local snapshot (config + safetensors headers); BOS == EOS ==
50279 quirk disclosed; missing model.safetensors.index.json fetched
(the only network touch).

Instrument (S1 defaults byte-identical, asserted by tests and by the
critic's independent reruns):
- moe_telemetry.py REWRITTEN to the batched pattern: RouterTap drives
  the unchanged shadow_telemetry.harvest_batch; on-box ground truth vs
  output_router_logits: 0/256 row-layer mismatches.
- CRITIC BLOCKER 1: the bnb skip-list spelling "mlp.gate" silently
  quantized the routers (found on-box and by the critic independently;
  matching is leaf-name/dotted-prefix). Fixed to ["gate","lm_head"],
  and verify_load_regime() now inspects modules POST-LOAD in all four
  GPU load paths — metas record the inspection, never the flag;
  falsification run: the reverted list is refused loudly on a real
  4-bit load.
- CRITIC BLOCKER 2: CPU harvest consumers accepted cross-model spaces
  silently. run_probes/audit_harvest/build_concept_groups/
  fidelity_rider_moe now BIND space files to the harvest metas'
  buckets*_sha256 and --n-slots to the meta's telemetry alphabet;
  build_spaces refuses a groups artifact from a different k512
  bucketization; committed S1 chain verified green on every binding.
- verified_seed_files: prefix-generic glob + mixed-prefix refusal;
  summarize/audit widened with S3 identity keys (summarize
  regeneration now adds six null identity keys on S1 dirs — disclosed,
  committed summaries stand).
- build_concept_groups: argparse + the results-are-evidence overwrite
  guard it lacked (a bare --help invocation used to EXECUTE it).
- harvest_freq: --bf16-routers (default off = S1 behavior, load tag
  unchanged).
- NEW: tools/calibrate_fidelity_moe.py, sideband/real/
  fidelity_rider_moe.py (tolerances unset; refuses to run until the
  registered amendment pins them).
- .gitignore: harvest_moe dirs + preemptive state-file negations for
  the registered S3 runs.

Critic: 2 blockers + 3 should-fixes + notes, all closed; final verdict
CLEAR with both falsification conditions run in the critic's own hands.
Suite 253 passed + 1 skipped; lint 17 findings OK.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f3d05d4 2026-08-31 CLAUDE.md: working practices earned on the Phase-2/3/P1 arc (numbers-from-files, pre-register post-hoc diagnostics, state files as evidence, equal-dims noise anchor, dated errata)

## 1e12957 2026-08-31 F-16: the tap margin is not topic-state (post-hoc P1, both harvests)

````text
Mechanical label P1-SURVIVES on both harvests, per the registration
committed BEFORE any diagnostic result existed (1a54fb7). The topic-state
explanation of F-15 fails every pinned readout at the histogram-family
level: (t) prefix-topic alone sits ON the majority floor in all six cells
on both harvests (max gap 4.3e-4 / 7.6e-4); adding it to the free
baseline moves nothing (M3 max +0.0042, below the materiality floor);
the tap margin passes through intact (M2 fires 6/6 both harvests,
primary +0.0096..+0.0406 - magnitudes indistinguishable from F-15); and
the equal-dims noise control removes the dilution confound (M2n fires
6/6, +0.0101..+0.0451 primary; measured dilution M2noise
-0.0045..+3.3e-5 - real, small, and DEPRESSING M2, not inflating it).
Whatever the S1 tap carries about offsets 2-3 is not recoverable from
the decoder's generated-token history at the histogram level.

Critic round 4: all six readout families on both harvests recomputed
from the sha-headered state files bit-exact; P1-SURVIVES re-derived
mechanically; my "M2n larger everywhere" sub-claim REFUTED (3/12 cells
invert by <= 1e-4 where dilution ~ 0) and the finding wording carries
the corrected form; should-fixes applied: dims erratum (3265/1217, the
registered amendment text left as written and corrected in a dated
erratum), "approximately bracket" hedge with the anti-M2n channel
named, histogram-family scope on the k-NN queue item (the
embedding-similarity control is a richer family under the residual,
not subsumed), (t)-aliveness clause (CI-positive M3 rows impossible
with a dead feature path).

Residuals carried: prompt-token-augmented prefix control (open,
expected small, unquantified), richer prefix families (new
registrations). NON-CRITERION: F-15's verdict is untouched; K-3
remains the load-bearing risk. Suite 233 passed; lint 17 findings.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 1a54fb7 2026-08-31 P1 registration: prefix-topic control for the F-15 tap margin (pre-results)

````text
Post-hoc diagnostic P1, registered in BLUEPRINT BEFORE any diagnostic
result was read (NON-CRITERION - cannot amend F-15): can decoder-free
prefix features (concept histograms of the accepted-token history, 560
dims from tokens[row,:anchor] only) reproduce the tap margin at offsets
2-3? Readouts pinned: M2=(abt)-(at); M2n=(abt)-(atn) the EQUAL-DIMS tap
test against alignment-destroyed slots (anchor+17 mod row-length, R2's
shift on features - dilution cancels); M2noise=(atn)-(at); M3/M4/(t)-(b)
paired against committed Phase-3 state cells. Labels pinned: P1-SURVIVES
iff L1/off2/linear M2 fires the three Phase-3 conditions; P1-DEFLATES
iff all six M2 AND all six M2n CI uppers < +0.005 (budget-dilution
amendment, critic round - dilution alone may not produce a deflation);
else MIXED.

Critic round 3 (pre-results, no state consulted): no blockers; cured its
should-fixes - dim arithmetic corrected in prose (n512=511, (t)=560; the
code always used the loaded alphabet), budget-qualified DEFLATES + the
18-cell (atn) noise anchor registered, provenance additions (label-space
+ phase3 state/payload shas, slot_shift) and a load-time gate that
recomputes the committed payload margins from the loaded state cells
(1e-12) so a wrong-training-run state file fails closed. Critic verified:
prefix boundary mutants actually kill (live mutant runs), margins/
run_cell default paths reproduce the committed Phase-3 payloads
bit-exact, conclusion() labels disjoint and tested.

Instrument changes (defaults byte-identical): margins(base_feats=),
run_cell(extra_factory/feats_label), PrefixTopicBlock + 12 new tests.
Suite 233 passed. Primary 54-cell grid in flight on the old code; the
18 atn cells run on resume after it completes - state cells unchanged,
aggregation deterministic.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 958b0fb 2026-08-31 F-15: K-2 survived at S1 - telemetry beats free info at offsets 2-3, replicated

````text
The registered replication PASSED by its pinned rule (committed in 86136c8
BEFORE the replication ran): fresh harvest seeds 8..11 (849,536 pairs,
separate dir, R1 16/16 PASS at rng-seed 2 first attempt, R2 pass, archive
sha-verified operator-attested), same 156-cell grid, and the pinned
L1_concept_k16/off2/linear triple RE-FIRED: +0.0141 [+0.0081, +0.0203],
all three train seeds positive, point above the +0.005 floor. Breadth:
all 8 off2/off3 triples re-fired (8/8); 0/4 off4 re-fired (the horizon
established is 2-3 tokens, off4 is NOT established). Free-info collapse
to the majority floor by offset 3, telemetry-alone CI-positivity, and
the offset-1 CI-negative internal control all reproduced on fresh data.

EXISTENCE at S1 is CONFIRMED; the provisional qualifier lifts. Scope
guards carried in F-15: per-source (S1 compute-tier taps only - S2/S3
untested, the address-stream hardware story lives there), existence !=
actuator (K-3 now the load-bearing risk; F-14 measured the existing
actuator's coarse-k oracle ceiling at ~zero), mechanism unresolved
(anticipation vs persistent topic-state - post-hoc k-NN control queued),
L3 mega-group lens, OQ-6 undefined on both runs (budget statement).

Critic gate (second round, same reviewer): recomputed all replication
margins/CIs from the state file BIT-EXACT, confirmed the pinned-rule
application and the 8/12 firing census, verified the state-file sha
header binds to harvest_shadow_r, found NO blockers; four prose
should-fixes applied (cross-run agreement 0.006 not 0.003, off3 triple
count, exact b-a crossing list, archival attestation tagged) plus
precision notes (margin span +0.008..+0.044, one-model regime, OQ-6
replication numbers labeled, payload verdict-string supersession note).

Evidence: probes_s1_replication.json + state file (sha-header bound),
harvest_shadow_r metas + summary (EXIT_BAR_NOT_MET = Phase-2 full-
harvest bar, superseded by the registered 4-seed pin, disclosed),
harvest_fidelity_rider_r.json. Suite 225 passed; lint 16 findings clean.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 86136c8 2026-08-31 Phase 3 S1 grid evidence: verdict EXISTENCE (provisional), replication registered

````text
Grid completed: 156 registered cells + 6 R2 shuffle, no partial, 17,621 s
(results/real/probes_s1.json + its state file, committed as evidence per
critic gate - the per-prompt cluster counts reproduce the bootstrap).
Mechanical decision block: 10/12 offset->=2 (c)-(a) triples fire all three
registered conditions; all 12 CI95-positive (both misses are offset-4
materiality misses, +0.0045/+0.0034 < +0.005). Free info collapses to the
majority floor by offset 3; telemetry-alone stays CI-positive over free
in 11/12 triples; (c)-(a) is CI-NEGATIVE at free-saturated offset 1.
R2 label-shuffle PASS at every offset (|gap| <= 5e-5); R1 PASS bound to
the exact npz shas; R3 clean. OQ-6 UNDEFINED at every offset >= 2 (h-a CI
crosses zero at off2, h below (a) at off3/4 under the registered budget).

Per the registered rule NO positive K-2 finding lands yet: F-15 is
withheld until the seeds-8..11 replication passes. Replication registered
in BLUEPRINT before it runs: fresh harvest to harvest_shadow_r (no
pooling), R1 at rng-seed 2 under the cycle bound, same grid, decision
pinned to L1_concept_k16/off2/linear re-firing; non-EXISTENCE branches
pinned (OPEN on triple-swap, NOT-REPLICATED->OPEN, no NEGATIVE from the
underpowered replication).

Critic round (this commit): independent recomputation from the state file
matched the payload bit-exact (same 10/12 triples, same verdict); no leak
channel found (off1-negative internal control excludes index-shift leaks
R2 would miss). Blocker cured: state file is now committed evidence, not
gitignored scratch. Should-fixes cured: harvest_shadow_r npzs ignored;
non-EXISTENCE replication branches pinned; state files now carry a
harvest-binding sha header and run_probes refuses mismatched/headerless
resume (parse_state + 6 tests). --fidelity arg added so the replication
binds its own R1 rider without touching committed evidence. Suite 225.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## fba1fb3 2026-08-30 Ecosystem: probe-estate salvage survey ([private repository] / [private repository] / [private repository] / Ideas)

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## e6b22c9 2026-08-30 R1 quarantine cycle: a-priori tolerances failed 12/16, recalibrated via the registered path, fresh-triple rerun 16/16 PASS; L3 artifact built

````text
The chain, in order (all preserved): (1) R1 v1 at the a-priori tolerances
FAILED 12/16 (harvest_fidelity_rider_v1_failed.json) - quarantine per the
rule. (2) Calibration on FRESH seed-100 non-audit anchors under exact
harvest regime vs exact rider regime, with deliberate off-by-one negative
controls (tools/calibrate_fidelity.py -> fidelity_calibration.json):
aligned bnb-NF4 kernel noise spans overlap 27-31 / mass Linf <= 0.027;
misaligned collapses to overlap <= 12 / mass Linf median 0.99 - the
separation that makes recalibration honest. (3) Dated amendment: overlap
>= 20, mass <= 0.08, entropy <= 0.10, argmax gap 0.08; entropy support
stated honestly (calibration UNDERCOVERED its tail - audit triples reach
0.077 with clean overlap/mass; support = real-data band + misaligned
median 3.7x above); CYCLE BOUND registered: cycle one, no further
widening absent a new named mechanism + critic review, rerun seeds
advance +1. (4) Rerun on fresh triples (rng-seed 1): 16/16 PASS,
sha-bound to this harvest. Critic verified the chain from the files
(v1 failure signature inside the calibrated aligned band on overlap and
mass; calibration exercised the identical committed harvest code) and
passed it with the two registration edits included here. Consistency
test added: rider constants must keep their derivation relationships to
the committed calibration evidence.

L3 artifact (concept_groups_v1.json): first run, no fallback, subgraph
connected (n_comp=1), 165 zero-degree buckets -> largest group as
registered. READING LENS, recorded: group sizes [8,2,2,2,2,8,2,5,2,2,2,
3,3,455,10,2] - one mega-group of 455/510 concepts, so its high
persistence (0.92 glue-dropped) is mostly the mega-group triviality; its
3 grid triples are low-information cells and stay inside the registered
12 (multiplicity unchanged).

Suite 219 passed.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 9ca4308 2026-08-30 Phase 3 implementation: probe machinery, riders R1/R2/R3, L3 builder, runner

````text
src/sideband/probes.py (data layer: HarvestData over sha-verified npz,
anchor_table/labels_for single-sourced on harvest.label_index, lazy
feature blocks - the dense (c) matrix never materializes; train_probe with
identical per-cell optimizer budget, val-only selection, single test
read), sideband.harvest.verified_seed_files (the only sanctioned harvest-
open path, used by every Phase-3 consumer), stats.paired_cluster_delta_ci
(pooled paired fraction delta, same recipe as cluster_bootstrap_ci),
real/fidelity_rider.py (R1: registered criteria, sha-binding of the PASS
to the exact npz bytes, regime asserts), tools/build_concept_groups.py
(L3 per the registered rule + the dated pre-build degeneracy amendment:
nonzero-degree subgraph clustering, connected-components fallback,
zero-degree -> largest group, all recorded), tools/run_probes.py (the
registered 156-cell grid + 6 R2 cells; R2 runs first and halts fresh OR
resumed; resume state int-normalizes cluster keys and drops a torn final
line; partial runs cannot write the registered out path and can never
yield NEGATIVE - INCOMPLETE instead; payload carries full provenance and
refuses an R1 pass bound to different harvest bytes).

Critic rounds 4-5: 7 blocking objections cured, 3 of them critic-
REPRODUCED defects in the criterion layer (resume key corruption, empty-
grid NEGATIVE, R2 halt disarming on restart) - all now pinned by 12
CI-safe criterion-layer fixtures incl. the hand-computed 0.15 margin and
the significant-but-immaterial -> NEGATIVE case; L3 spectral-degeneracy
amendment (disconnected affinity graph) landed dated BEFORE the artifact
build. Round-5 verdict: PASS. Suite 218 passed.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## c344e15 2026-08-30 Phase 3 registered: probe protocol, decision rule, riders; pre-probe audit committed

````text
BLUEPRINT Phase 3 protocol (pre-registered, amended same day on critic
review - all amendments landed BEFORE any probe ran): label rule (concept
ids + one merged glue class; predicting glue is part of the task), three
label spaces (L1 concept_k16 primary / L2 concept_k512 / L3
concept_groups_v1 - transition-coherent groupings of k512 concept buckets,
train-split-fit, skip-and-join chain semantics pinned, first-run-is-
artifact), feature sets with (a) = ALL logged free summaries (657 dims -
the critic caught the per-space 18-dim (a) as a handicapped free
baseline, the exact hole Phase 2 closed at the logging level), pinned
optimizer budget, seed-combined margin estimand (one CI per triple, no
best-of-three-CIs pick), decision rule with the +0.005 materiality floor
gating BOTH verdicts, owned multiplicity (~26% family-wise under global
null) with a fresh-harvest-seed replication required before any positive
K-2 finding lands, riders R1 (harvest fidelity, a-priori NF4 tolerances
with a registered recalibration path) / R2 (label-shuffle null, RELATIVE
band: shuffled-(c) vs shuffled-(a), offsets 2-4) / R3 (split integrity),
OQ-6 survival fraction fenced off from any SD^2-percentage reading.

Pre-probe audit (tools/audit_harvest.py + results/real/harvest_audit.json,
run before the registration was drafted, feeding it mechanically):
cross-split 8-gram contamination 0.8% distinct / 1.4% occurrence, seeds
diverge (0.96 distinct-gram ratio within prompt), loopy rows 0.24%,
majority floors 0.591 (L1) / 0.413 (L2). Audit npz reads are sha-verified
and the report embeds npz shas + git commit (critic round). Registration
committed BEFORE the L3 artifact is built and before any probe trains.

Critic round 3: 7 blocking objections cured (handicapped (a), unpinned CI
seed-aggregation, materiality asymmetry, unowned multiplicity, audit
provenance, L3 chain ambiguity, commit scoping - this commit contains
exactly the five reviewed paths). Suite 206 passed.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 0aa38dc 2026-08-30 Phase 2 S1 harvest evidence: 1.69M pairs across 8 seeds, exit bar MET

````text
results/real/harvest_shadow/: 8 sha-bound seed metas (npz gitignored per
protocol) + harvest_shadow_summary.json (verdict OK, no problems):
1,693,036 (telemetry, label) pairs over offsets 1..4 - exit bar 1M met
with the registered 8 seeds, no extension needed. 425,779 anchors, mean
length 253.4/256 (only 4.5% of rows hit EOS before the cap), split
1.21M/239k/244k train/val/test. Slot-occupancy entropy 8.79/8.91/8.61/7.73
bits of 9 across layers 7/15/23/31; ~31 unique slots per anchor; all four
mass spaces sum to 1 within 4.3e-4 - the tap stream is input-dependent,
not static, and the free-info logs are exact.

Archival duty (registered): second on-disk copy at
<path outside the repository, scrubbed at export> (16 files, 3.97GB),
all 8 npz sha256s verified against the committed metas after copy.

Code at e8669d2 unchanged; suite 189 passed.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## e8669d2 2026-08-30 Phase 2 registered + shadow harvester: block-start alignment, 4-space free-info logging, sha-bound evidence chain

````text
Pre-registration (BLUEPRINT Phase 2, before any harvest artifact): sources
S1 shadow taps / S2 KV pages / S3 OLMoE routing with per-source K-2 reads;
block-start alignment (sideband.harvest.label_index, offset 1 = the token
sampled from p_a, K-2 reads offsets >= 2); exact p_a masses logged in ALL
FOUR committed bucket spaces with Phase-3 label spaces restricted to
logged-mass spaces (critic: under-logging would handicap probe (a)); h_a
logged as OQ-6 DENOMINATOR reference, explicitly NOT an information bound
on mid-layer taps at offsets >= 2; prompt-split pinned (idx % 7 ->
150/30/30); >= 1M pair volume rule; gitignored npz bound by sha256 in
committed metas + archival duty.

Harvester rewrite (real/shadow_telemetry.py): batched left-padded KV-cached
NF4 decoding, explicit position ids, per-row SeedSequence-spawn generators,
GPU-scored ShadowTap with dequantized column norms, NormCatch, resume.
tools/summarize_harvest.py verifies shas + cross-seed identity + recounts.

Critic-reviewed (2 rounds, PASS): 4 mutants proven killed by direct
mutation runs (slots anchor misbinding, pos_next off-by-one via a
position-id spy - value tests are blind to it at ~5e-4 logit scale under
f16 storage, layer-seed convention drift, n_rec final-anchor drop - the
critic-suggested max(lengths) invariant was itself insufficient, absolute
anchor-count assert added instead). 18 new tests; suite 189 passed.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 7d46466 2026-08-30 F-14: oracle ceiling at coarse k bounded at ~zero; attribution rider returns the registered STRADDLE

````text
oracle_nextp at k=16 (soft beta=3, 210 prompts, seed 0): delta +0.0014
[-0.0043, +0.0069] (analytic +0.0033 [-0.0010, +0.0075]) — STRADDLE per
the registered rule; attribution between forecast quality and the
actuator stays open, and the writeup assigns none (free-vs-oracle gap
+0.0043 has CI through zero; not decomposed). The substantive bounds:
perfect per-position forecasting converts to <= +0.0069 at this cell, and
the beta-invariant truth-gate rate is 15.9% — at C=15 the draft already
agrees with the target fresh concept profile ~84% of the time. The
granularity trap holds at every TESTED cell; the fine-k oracle is the
named open remainder (no sweet-spot claim extends to it).

Hardening: stale-oracle mutant (steer with p_(j-1), verify with p_j)
proven to survive the old spy, now killed by identity-pinning spies
(every verified p must be a steering-posterior input object); duplicated
assert block removed; 20-prompt real-hardware --no-kv-cache oracle spot
rider PASSED all six containments (new code path, so the F-13
byte-identical argument was unavailable). K-7 outcome updated (rider ran,
straddle); OQ-12/BLUEPRINT scoped per critic (no fully-measured claim, no
wins claim, tested-cell language throughout).

Critic-gated round 3: all numbers independently reproduced (analysis json
bit-identical); three blocking objections (smuggled attribution,
axis-coverage overclaim, sign overclaim) cured; mutant-kill verified by
direct mutation run.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 910522b 2026-08-30 oracle_nextp: the attribution rider arm (D-2-named non-causal ceiling)

````text
Per-position steering from the target's OWN fresh p_j: the target is
stepped incrementally against its KV cache during drafting (terminal cache
state identical to the batched forward, so crop logic is shared); bonus
row from one extra step. Implementation gate passed: at beta=0 the oracle
path reproduces the standard path bit-exactly on the tiny harness (3
seeds x both cache modes), and the cached-vs-uncached A/B holds steered
with full crop coverage; spy test pins FRESH per-position posteriors
(kills a block-held mutant). Suite 169 -> 171.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 814fc34 2026-08-30 F-13: OQ-12 answered negative — coarse gating restores gate selectivity, mechanism still loses; attribution rider registered

````text
All six pre-registered Phase 0c arms BROKEN (best: k16 soft -0.0029
[-0.0088,+0.0029], gate 0.559 > the 0.5 bar; analytic estimand negative
for all six; five acceptance CIs definitively negative). The granularity
diagnosis is CONFIRMED as a measured monotone curve: gate-open
0.55/0.67/0.80/0.94 at C=15/31/62/510. Free-information bucket-bias
steering is dead as built (beta=3 at coarse k) at k in {16,32,64,512}.

Residual-cause attribution deliberately WITHHELD per the protocol's own
overdetermination caveat (halved headroom, 71% glue-involved rejections,
one glue bucket = 59% of generated mass at k16): a mechanism-matched
ORACLE-CEILING arm (--bucket-source oracle_nextp, per-position target
posterior, D-2-named non-causal ceiling) is registered in BLUEPRINT with
its decision rule fixed before implementation — CI lower > 0 confirms
forecast quality as the failure; CI upper < 0 kills the actuator for ANY
predictor.

Also: D-1 scope note (passive-store vs compute-tier; taps allowed, gates
on the observed model forbidden; premise widening dated, not retconned),
K-2 scope note (per-source verdicts; taps-only survival = re-scoping not
rescue; free-steering salvage line voided by F-12), BLUEPRINT origin
frame (acceptance = transfer-latency budget; 3.11 tokens/call measured,
cost model unmeasured per K-5), OQ-12 ANSWERED, K-7 closure.

Critic-gated: every number independently recomputed (analysis json
bit-identical to a fresh pinned-invocation run); blocking objection
(single-cause attribution violating the registered caveat) cured by
withholding attribution + registering the oracle rider; all 8 advisories
applied.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 8f2f1ba 2026-08-30 OQ-12 evidence: coarse bucketizations, glue sets, viability diagnostics

````text
k=16/32/64 (same tool/PCA/seed as fine; converged). Glue: 1/1/2 buckets at
80% cover. Viability (committed-records re-analysis): concept-cross 0.314
[0.303,0.325] / 0.421 [0.410,0.432] / 0.533 [0.522,0.545] — ALL THREE
VIABLE (CI lower >= 0.25); persistence 0.295/0.213/0.142 (vs 0.027 at
k=512); glue-involved 71/54/49%. Stage 1 runs all six arms.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 89173bd 2026-08-30 OQ-12 / Phase 0c protocol: coarse gating space, pre-registered before any steered coarse run

````text
- BLUEPRINT Phase 0c block: viability rule (concept-cross CI lower >= 0.25
  from committed records), criterion-bearing estimand named (empirical
  acceptance_pooled plugin+ci95; analytic = concordance only), EXHAUSTIVE
  verdict cells (WIN gate-rescued/bias-despite-gate, RESCUED-TO-NEUTRAL,
  BROKEN — open-gate straddles are BROKEN), pinned analysis invocation,
  stage-2 selector + entry criteria (F-3 ordering + second neutral beta;
  WIN requires seed-1 replication), honest provenance stamp anchored to
  commit 6045158, k=16 overdetermination caveat.
- analyze_phase0b: gate-space exemption extended to buckets_sha256 (sound
  by the committed k256/512/1024 audit identity + F-11 bit-identity; both
  cited), exemption recorded per arm.
- oq12_diagnostics.py: pre-GPU headroom/persistence/glue diagnostics from
  committed records; n_negative_bucket_records carried.
- .gitattributes: results/** -text (sha256 provenance chains must survive
  checkout).

Critic-gated: 4 blocking objections cured (exhaustive cells, named
estimand, stage-2 criteria, protocol/evidence commit split + provable
stamp); advisories applied (citation fix, WIN gate clause, caveats,
pinned invocation, negative-bucket field, gitattributes).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 6045158 2026-08-30 F-11 + F-12: OQ-4 answered, Phase 0b free baseline is null, gate-granularity failure diagnosed

````text
F-11 (OQ-4): glue is concentrated and identifiable (2/2/4 buckets cover 80%
of top-100 frequency mass at k=256/512/1024; textbook function tokens);
concept-level cross share 0.565/0.610/0.674 token-level, 0.607 mass-level
at k=512 (estimators concordant); pre-registered F-10 reopen trigger does
NOT fire; verdict rule-insensitive (every committed alternative glue set:
CI lower bound >= 0.485). Vanilla re-run reproduced the committed audit
trajectories BIT-IDENTICALLY (11,287 tuples, masses, counts).

F-12 (Phase 0b): the D-5 free-information denominator is ZERO — best arm
+0.0025 (CI through 0), confirmatory sharp beta=3 arm -0.0098 [-0.0155,
-0.0039], harm dose-monotone in beta; F-3 tax reproduced on real models
(always -0.0168 < gated -0.0098 < vanilla). Diagnosis EARNED per the
pre-registered protocol: gate open ~94% in every gated arm; the 90%-cover
re-test (tripled glue set) moves it only to 93.6% with delta still <= 0;
concept-bucket persistence at k=512 is 0.027 (run length 1.015 — F-4 hold
rule fails by construction). Granularity, not glue identification.
Riders: vanilla point-in-CI (bit-identical); KV spot rider 6/6 PASS.

Consequences recorded: K-7 outcome (identification works, granularity
concern live), OQ-12 opened (coarse gating space; blocks Phase 4 only —
Phases 2/3 proceed, K-2 compares information not steering deltas), OQ-3
partially answered at k=512, README/BLUEPRINT status updated.

Tools: analyze_phase0b gate-space exemption (glue-as-treatment arms),
analyze_glue alternative-set re-analysis, bucket_persistence.py.
Evidence: 12 arms (~2.5M drafted positions), all metas at 6a468f1.

Critic-gated: all numbers independently recomputed by the critic from
evidence (bootstrap reimplemented from scratch); both blocking objections
cured (90%-cover re-test run before concluding; Phase 3 unblocked).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 6a468f1 2026-08-29 OQ-4 evidence: frequency harvest, glue sets (k=256/512/1024), Phase 0a re-analysis

````text
- gen_freq.json: 53,441 target-only sampled tokens (NF4, 210 prompts, seed 0).
- glue_k*.json: pre-registered rule output — glue is CONCENTRATED (2/2/4
  buckets, no concentration flag); decoded top glue tokens are textbook
  function words/punctuation.
- glue_phase0a_analysis.json: concept-level cross fraction on the committed
  11,287 rejections = 0.565/0.610/0.674 at k=256/512/1024 (cluster CIs);
  F-10 reopen trigger does NOT fire; bucket-level recomputation matches the
  committed summaries bit-exactly. Finding entry lands with Phase 0b (mass-
  level confirmation from the vanilla arm still pending).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## db9df6b 2026-08-29 OQ-4 + Phase 0b machinery: concept-space steering, glue identification, pre-registered protocols

````text
- sideband/glue.py: pre-registered glue-bucket identification (top-100
  frequency-mass 80% greedy cover, sensitivity sets, count-rule crosscheck,
  concentration flag), glue_remap (compact concept ids, glue -> -1),
  load_glue (sha-bound to its buckets file, no None bypass),
  rejection_masses (residual decomposition via specdec.residual_distribution).
- steering.py: concept_posterior / concept_argmax / apply_concept_steering —
  the real adapter's concept-space semantics as pure tested helpers, pinned
  equivalent to World.bucket_mass[:C] / top_concept_bucket; D-11 sharp
  variant; glue zero-boost via posterior_bias negative-id convention.
- hf_specdec: steering block delegates to the helpers (block-held posterior,
  D-7 concept gate both sides); --bucket-source free_lastp_sharp; --glue
  (sha-checked, remapped, meta-stamped, resume-identity, full-coverage
  guard); analytic-acceptance recording (D-9: drafted + verified frames,
  by-offset sums); gate diagnostics; --log-generated sidecar with the same
  fsync/repair discipline; AuditRecord.residual_mass_glue + documented
  concept-other derivation; summarize_audit glue section.
- real/harvest_freq.py: target-only frequency harvest (batched, left-pad,
  per-row EOS truncation, pinned chat-template date).
- tools/analyze_glue.py: OQ-4 validation on committed Phase 0a records,
  bucket-level must match committed summaries bit-exactly, F-10 reopen
  trigger (all-of-KS enforced).
- tools/analyze_phase0b.py: paired plug-in deltas + vectorized bootstrap
  (seed 0 / 20000), MUST_MATCH incl. cache path, vanilla-rerun rider,
  enforced KV spot rider on the confirmatory arm.
- Pre-registrations BEFORE any glue/steered number exists: WHY_THIS_DIES
  K-7 addendum (glue rule + F-10 reopen trigger + gate-health diagnostic);
  BLUEPRINT Phase 0b protocol (arms incl. always-gate control, confirmatory
  arm = sharp beta 3, metrics, riders).
- Tests 155 -> 169; critic mutation set M1/M2/M3/M6 each turns tests red
  (verified by direct mutation runs); full suite green.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 1fb67f3 2026-08-29 F-10: Phase 0a real cross-bucket audit — kill criterion K-1 does not fire

````text
First real-model result. Llama-3.1-8B-Instruct (NF4) + Llama-3.2-1B-Instruct
(bf16), 210 committed prompts, gamma=4, temperature 1.0, seed 0, per-prompt
RNG streams, KV-cached path. Of 11,287 rejections, cross-bucket residual
mass = 0.778 [0.769, 0.787] / 0.812 [0.804, 0.820] / 0.863 [0.856, 0.870]
at k=256/512/1024 (prompt-cluster bootstrap CIs; sampled fraction agrees
within 0.003 everywhere). The pre-registered kill rule (CI upper < 0.25 at
every k) does not fire; no CI touches the caution band. Sampled fraction
flat by offset. The three k rows re-bucketize verified-identical
trajectories, so the k-trend is exactly paired.

Pre-registered riders all satisfied and now committed as evidence
(tools/verify_phase0a.py -> results/real/phase0a_verification.json, pinned
recipes): KV cached-vs-uncached A/B PASS on all six bidirectional
containments; NF4-vs-bf16 paired acceptance delta -0.002 pooled CI95
[-0.021, +0.018]; paired mass shift +0.031 CI95 [+0.003, +0.060] (real,
barely resolved — carried as a caveat); clean-vs-dirty-tree behavioral
equivalence bit-exact on the 20-prompt overlap.

Evidence: full audit + sanity sidecar sets under results/real/ (jsonl,
stats, meta, summary per run). OQ-2 marked answered; WHY_THIS_DIES K-1
outcome recorded with the rule retained verbatim; README status updated.

sideband-critic on the writeup: 1 BLOCKING (verification computations
uncommitted — fixed via tools/verify_phase0a.py), 8 ADVISORY (trajectory-
identity wording tightened, mass-shift uncertainty quantified, by-offset
estimand labeled, 0.857->0.856 rounding, sanity-band attribution to the
port checklist, bucket-level vs concept-level hedge + OQ-4 follow-up,
dirty-tree disclosure) — all applied.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## b1dae57 2026-08-29 KV-cache fast path with exact-recompute reference (red-team commit 2)

````text
spec_decode_prompt(use_kv_cache=True) default: per-prompt DynamicCaches on
both models, fed deltas only, cropped to len(ids)-1 after every block —
valid because proposal coupling makes the accepted tokens identical to the
rollout tokens already in the caches; only the block's final emitted
(residual/bonus) token is uncached. Per block this feeds ~2*gamma+2 token
positions instead of (gamma+1)*prefix_len + O(gamma^2); wall-clock remains
deliberately unmeasured (D-9 ban stands). --no-kv-cache keeps the
exact-recompute reference path; no_kv_cache joins RESUME_IDENTITY_ARGS (a
pre-existing incomplete run from before this commit is therefore
unresumable by design — none exists). Runtime assert guards against
DynamicCache.crop semantics drift in future transformers.

Validation: torch-guarded tests (run on this box, skip in CI) pin cached ==
reference on a tiny fp32 CPU Llama pair at temperature 0.2 — mixed
acceptance asserted in-test (rejections at offset 1 and deeper, full-accept
bonus blocks, non-empty audit records), trajectories and stats bitwise
equal, audit records exact on all discrete fields with a 1e-6 tolerance on
the residual-mass float (fp32 reduction-order jitter, measured ~4e-8).
WHY_THIS_DIES K-1 gains the pre-registered cached-vs-uncached A/B rider
(>= 20 prompts, bidirectional point-in-CI rule, FAIL quarantines cached
results; compared arms must always agree on the cache path).

sideband-critic on the diff: 2 BLOCKING, both fixed — (1) the original
tests ran at acceptance 1.0 so every crop was a no-op and an off-by-one
crop mutant survived; now mutation-killing by construction; (2) the
'~4-5x' prose was wrong as arithmetic and banned as wall-clock — replaced
with the token-position formula. Advisories applied: false draft-cache
comment corrected, crop guard, A/B pre-registration, arms-share-path rule.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f946a50 2026-08-29 Audit run semantics: proposal coupling, per-prompt RNG, resume, evidence binding (red-team commit 1)

````text
Adjudicated red-team fixes, all landing BEFORE any real audit exists:

- spec_step(proposed=...): a real adapter passes the token its draft
  actually rolled out, so the verified proposal IS the conditioning token
  (previously spec_step redrew its own proposal — accepted tokens could
  differ from the tokens that conditioned the rest of the block, putting
  every block>=2 statistic on off-distribution prefixes). Default None
  preserves the synthetic pipeline byte-exactly (pinned by test; e07
  regenerates bit-exact). Zero-mass supplied proposal fails loud.
- Per-prompt RNG streams via dists.spawn: resume-stable, and NF4-vs-bf16
  comparisons pair at prompt granularity as K-1's sanity pass requires.
- Crash resilience: per-prompt stats checkpoint (<out>.stats.jsonl),
  fsync-ordered writes (records durable before their stats line), --resume
  with identity validation (args + buckets/prompts sha + TEMPLATED-IDS sha
  so tokenizer/template drift between segments is refused), torn-tail
  repair with a record-count invariant that demotes damaged prompts,
  per-segment provenance, summary assembled from disk, atomic+fsynced
  sidecar writes, record-count invariant re-checked at summary time.
- Evidence binding: buckets file must match --target (model + n_tokens;
  --allow-buckets-mismatch to override), -dirty parity in git provenance,
  buckets_file_git_clean recorded (None when git is unavailable, never a
  false clean).
- Preflight (fail-closed): free VRAM + median GPU utilization + free disk
  on the output volume + Windows pending-reboot, measured even when
  --skip-preflight disarms the gate; device-placement assert refuses
  silent CPU offload (--allow-cpu-offload for the K-1 bf16 path).
- steering.posterior_bias: negative bucket ids (absent tokens in real
  buckets files) now get zero boost — ext[-1] used to wrap to the last
  bucket (latent; synthetic ids are non-negative, results unaffected).
- Meta: redacted args (word-boundary matching), rng scheme, cuda versions,
  nondeterminism disclosure. WHY_THIS_DIES K-1: pairing-granularity note +
  sharp re-run verification criterion (point estimate inside the original
  cluster-bootstrap CI), both pre-registered before any number exists.

sideband-critic on the diff: 1 BLOCKING (resume tokenization drift —
fixed), 10 ADVISORY (all applied except consolidating the adapter's inline
posterior with steering.posterior_bias, deferred with its TODO).
Tests: 130 passed (20 new torch-free tests incl. repair/redaction/binding).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 883dd6a 2026-08-29 Phase 0a evidence: vocab buckets k=256/512/1024 for Llama-3.1-8B-Instruct

````text
Fixed-kmeans partitions of the 128256 lm_head rows (PCA-128, seed 0), each
converged before max_iter (n_iter 187/124/79), zero empty buckets, full
provenance embedded (source key/shard/dtype, git commit 4b7194d, size
stats). These are the bucket files the K-1 audit will cite by sha256.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 4b7194d 2026-08-29 kmeans convergence bug fix + Phase 0a audit inputs (critic-reviewed)

````text
BUG: kmeans convergence check fired on iteration 1 for every input
(prev_inertia=inf makes inf <= inf true), so every clustering was
k-means++ init + one Lloyd step. Invisible on the easy synthetic world;
caught because the first real-vocab run reported n_iter=1 on 128k points.
isfinite guard + regression tests (n_iter > 2; strict inertia decrease).
Blast radius verified by critic: kmeans is used only by tests and the
real bucketize path first run tonight — no committed finding touched.

bucketize_vocab: read lm_head.weight directly from safetensors shards
(~2GB) instead of instantiating the model (fp32 8B load = ~32GB, OOMs
this box); covariance-eigh PCA instead of full SVD (same subspace, same
k-means distances — tested; SVD workspace at 128k x 4096 is ~13GB);
refuses input-embedding fallback for untied models; provenance in the
output json (key used, shard, shapes, git commit, n_iter/max_iter_bound,
size stats); --overwrite guard mirroring hf_specdec.

hf_specdec: chat template applied by default (Instruct pair decoded
raw-completion-style is off-distribution; --no-chat-template to disable),
date_string pinned so tokenized prefixes don't depend on the run date,
templated-ids sha256 in meta; hard guard that target and draft share one
tokenizer (vocab_size + vocab equality) — silent-garbage failure mode
otherwise.

data/: deterministic 210-prompt set (instruct/story/summarize, one UNIQUE
topic per prompt so K-1's prompt-cluster bootstrap resamples independent
clusters), committed as audit input evidence.

WHY_THIS_DIES K-1: regime amended (dated, still before any real number):
chat template on with pinned date, committed prompt set, short-prefix
caveat.

sideband-critic: 2 BLOCKING (K-1 template pin: done; don't commit the
pre-fix buckets json: deleted) + 8 ADVISORY, all applied except the
by-design tol note (n_iter/max_iter_bound now observable in output).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 3da97f4 2026-08-29 Phase 0a prerequisites: CI machinery, NF4 target loading, K-1 pre-registration

````text
- sideband.stats: exact Clopper-Pearson by bisection on the binomial tail
  (numpy-only, pinned against scipy-generated constants) + prompt-cluster
  percentile bootstrap. Report both: CP assumes independent rejections
  (optimistic), the cluster bootstrap owns within-prompt correlation.
- summarize_audit: CIs for BOTH estimands (sampled fraction: CP + cluster
  bootstrap; residual mass, the F-8 default: bootstrap only), by-offset
  cells now carry n and are labeled survival-conditioned (D-9), negative-
  bucket sanity counter.
- hf_specdec --load-4bit: target in NF4/double-quant with bf16 compute AND
  bf16 non-quantized modules (explicit torch_dtype so numerics are
  transformers-version-stable); draft stays bf16. Regime note in help.
- Run provenance: .meta.json written before the run (run_id, versions incl.
  bitsandbytes, git commit, GPU, buckets/prompts sha256, buckets k),
  .summary.json after (stale one unlinked at start so a crash cannot leave
  a mismatched meta+summary pair); refuse to overwrite an existing audit
  jsonl without --overwrite.
- WHY_THIS_DIES K-1: decision rule pre-registered before any real number
  exists (estimand = residual mass, decision reads the cluster-bootstrap CI
  upper bound < 0.25 at every k in {256,512,1024}; near-threshold band
  requires bf16 confirmation; NF4-vs-bf16 paired delta in the sanity pass).

sideband-critic run on the diff: 3 BLOCKING + 4 ADVISORY objections, all
addressed above (B1 pre-registration, B2 mass CI, B3 sidecar consistency).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 83c9bd5 2026-08-29 docs: ECOSYSTEM.md — sibling-repo map and borrowable tools per phase

````text
[withheld: the message describes private repositories (plan 12); see WITHHELD.md]
````

## c93b427 2026-08-29 v0.2.1: prior-art deep dive (PEARL/AMUSD, ConFu, DREAM, SpecPIM/HPIM, PMATIC, symmetric LLM-AC patent, speculative KV coding), OQ-11 streaming/anytime steering, probes/ tier with p01 anytime-posterior

## bcaa84e 2026-08-29 sideband v0.2.0: posterior mechanism default (F-7, D-10/D-11), variance-free cross-bucket estimator (F-8), verified-archives hint ledger (F-9), KV-page telemetry adapter, emergent tracks OQ-7..10; v0.1 results reproduced bit-exact

## 21b9010 2026-08-29 sideband v0.1.0: exact verifier core, synthetic testbed, gated steering mechanism (F-3), real-model adapters, seeded findings F-0..F-6, blueprint v2 with kill criteria

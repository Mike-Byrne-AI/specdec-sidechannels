# The recovered critic folder (2026-10-17)

Lever 3 of the public-cut plan, section 14.2 item 3 (the plan is a withheld file; the public cut's WITHHELD.md
names it). The image audit's researcher walkthrough (docs/audits/2026-10-15-image-audit/README.md,
"Walkthroughs") named as its second doubt that the reviewer is the same AI and that its reports were
uncommitted. The reviewer is the sideband critic agent (.claude/agents/sideband-critic.md), dispatched by the
assistant on the registrations and landings of the harness era; its recompute scripts, their outputs and its
round reports lived only in the per-session scratch under the box's Temp folder. On 2026-10-16 a selection of
them was copied, with a sha256 manifest, to a dated archive outside Temp and outside the repository
(`C:\Users\<user>\Desktop\Research\sideband-critic-scratch-2026-10-16`, 309 files, copied
2026-10-16T09:56:28Z; its manifest's sha256 is in MANIFEST.json). The archive's rule, recovered from the
archive itself on 2026-10-17 (it rebuilds the archive exactly): the files directly inside a folder whose name starts with critic, with the suffix .py, .txt, .json or .md; nothing nested below such a folder, nothing of another suffix.
This folder is that archive, copied by `recover.py` beside it on 2026-10-17: 308 files under
16 session folders, one file listed and not copied, two manifests pinning every byte. What the rule
left behind is named below. Everything here is labelled RECOVERED: it is a selection of the reviewer's scratch as
it was left, not a registered instrument and not a result.

## What it is, and what it is not

- The scripts are what the reviewer ran to recompute labels and numbers from the committed state files and
  payloads at the time; the `.json` files are their outputs; the `.txt` and `.md` files are its round reports,
  the diffs and record excerpts it read, and its scratch notes. A script's paths point at the session scratchpad
  of its day (scrubbed, see below), so no script runs as copied; none is re-run by any test, and none is an
  instrument whose bytes a payload attests.
- What the folder establishes is narrower than independence: that the recompute rounds the record's OUTCOME
  blocks and memory rows describe existed, in part, and what those rounds computed and reported. The reviewer
  is an agent of the same model family as the assistant that wrote the registrations: the agent file
  .claude/agents/sideband-critic.md carries `model: opus` in every version since c20dce4 (2026-10-01, before
  the first file here), the later versions ab12cbd and c2b45ff included. The outside half of the doubt, a rerun
  of the committed audit scripts by a non-Anthropic model or a human colleague, stays the operator's action
  (section 14.2's closing paragraph).
- A report's claims are the reviewer's at its date. Later rounds and landings answered or superseded some of
  them; the record's dated text, not the report, is authoritative. Where a report quotes a number, the
  committed payload it recomputed from is the source.
- The folder covers the harness era only (2026-10-01 to 2026-10-16). The September rounds, F-24's among them,
  are not here: the scratch root of the repository's earlier path holds nothing (section 14.2 item 3 records
  the search).

## Layout, scrub, lanes, manifests

- Layout: `<UTC day of the session's earliest file>-<first 8 of the session id>/<archive path minus '<session>/scratchpad/'>`.
- Scrub: the user's name after 'Users' or 'home' plus a run of path separators or a hyphen, with no word character after it, any case, replaced by the user token; nothing else changed; line endings kept. 121 files carry 248 substitutions in all
  (40 files and 92 in the exported rows); the archive digest
  (`sha256_source`) and the committed digest (`sha256`) of every row record the change, and a row with no
  substitution has the two equal. A reader who knows the name can reproduce an archive digest from the
  committed bytes; the name is public in the record's author block and in the own-checkout paths the export
  keeps, so the digest hides nothing the tree does not already show. The scrubbed form of the scratchpad root
  reads `C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\<session>\scratchpad\`.
  Nothing else in any file changed; line endings are kept (the manifests record each file's form). The bare
  name remains in 1 file(s), 1 occurrence(s): a copied
  test fixture quoting the public author name, in a withheld file.
- Lanes: the first window of the file's session whose cutoff (the author time of the first commit the window lists) is after the file's archive mtime (recover.py LANES). A file past every window of its session would have been an error, not a guess.
  In the table, each window shows its closing commit first, the lane's other commits after it, and the number
  of files it holds; a window with 0 files is a lane whose rounds the archive's rule did not catch.
- Manifests: MANIFEST.json holds the rows the public cut exports and lists the withheld sessions and files by
  name and count, with no digest of a withheld file; MANIFEST_WITHHELD.json holds the withheld rows with their
  digests and is withheld with them. Each row: committed path, archive path, session, lane, commits, archive
  mtime, both sizes, both digests, substitution count, line-ending form, export status. `recover.py` writes
  both; `gen_readme.py` writes this file from MANIFEST.json alone (it names the withheld files and carries the
  per-session counts), so the public clone regenerates the same bytes.

## Sessions and lanes

| Folder | Session | Files | Scrubs | Lane windows (closing commit first; files before its time take the window) |
|---|---|---|---|---|
| `2026-10-01-64064aa4` | `64064aa4` | 11 | 12 | harness initialisation: results bytes stored as checked out and as cited (ab12cbd, d614666) [11] |
| `2026-10-01-4f289fb0` | `4f289fb0` | 3 | 2 | free-bigram twin of F-26's margin: registration rounds (d55e62f, 6eaabf4) [3] |
| `2026-10-02-12e6097a` | `12e6097a` | 67 | 61 | R1 stratified coverage read: registration rounds (fea2431) [31]; R1 stratified coverage read: landing rounds (09e846b) [36] |
| `2026-10-03-38e3cfca` | `38e3cfca` | 6 | 2 | derived ledgers levelled after the stratified read (b35a202) [6] |
| `2026-10-03-bd3df22e` | `bd3df22e` | 9 | 0 | R2 generalising free baseline: registration round (2fe5926) [1]; R2 generalising free baseline: landing rounds (2f13134) [8] |
| `2026-10-03-58dc4aea` | `58dc4aea` | 6 | 0 | landing-text kit: the diff-mode read over the record files (cf4eccf) [6] |
| `2026-10-04-d880d7a7` | `d880d7a7` | 3 | 2 | EVID-1: sha-cited files outside results/ stored as cited (0eb73d9) [3] |
| `2026-10-04-ae76f7e0` | `ae76f7e0` | 1 | 0 | horizon read at the R2 encoding: registration round (b41d3f3) [1] |
| `2026-10-05-fdeffb05` | `fdeffb05` | 39 | 13 | seed-noise floor readouts (F-27): landing rounds (73d8dc2, 906edfd) [8]; reader-and-lens re-test at S3: registration rounds (b128fda) [0]; reader-and-lens stage LENS (F-28): landing rounds (9bbe905) [13]; reader-and-lens stage READERS: landing rounds (34078d1) [10]; reader-and-lens stage READERS-LONG: landing rounds (7f0af3e) [8] |
| `2026-10-09-4efb2604` | `4efb2604` | 7 | 0 | OQ-20 seed replay of the verdict legs: registration rounds (b6d3701, 9163706) [7] |
| `2026-10-13-b10c3ea1` (withheld from the public cut) | `b10c3ea1` | 10 | 6 | public cut: the export tool, commit A (3e7b744) [10] |
| `2026-10-13-46731adb` (withheld from the public cut) | `46731adb` | 46 | 38 | public cut: commit B, the pinned export and its proof (977ff11) [46] |
| `2026-10-14-a8adf32c` (withheld from the public cut) | `a8adf32c` | 73 | 85 | public cut: the front-doors lane (d481935) [73] |
| `2026-10-15-c8cb4ef4` (withheld from the public cut) | `c8cb4ef4` | 1 | 0 | public cut: decision batch lane 1, the gates (51ceb9c) [1] |
| `2026-10-15-9dfaf64d` (withheld from the public cut) | `9dfaf64d` | 23 | 27 | public cut: decision batch lane 2, the tool, the allowlist and the record (5c264b0) [23] |
| `2026-10-16-4a635c95` | `4a635c95` | 3 | 0 | image audit lane A: CI portability (c41f9f1) [3] |

## What the archive's rule left behind

The rule took only the top-level files of four suffixes inside critic-named folders. Still in Temp on
2026-10-17, and copied that day to a second archive by a wider rule (every file under a critic-named folder at
any depth, except copied trees and results copies, and every file whose name starts with critic outside such a
folder), were: the nested round folders of three sessions (the harness initialisation's rounds two and three,
EVID-1's rounds five to seven, the reader-and-lens landings' probe outputs), the `.log` captures beside the
archived scripts, the dispatch briefs the assistant wrote for some rounds, the registration report of the
reader-and-lens re-test (`critic_design_report.txt`, the window the table shows with 0 files) and the five
critic reads of the public-cut decision batch's lane 2 (`lane2/reviews/critic_read1.md` to `critic_read5.md`).
The S1 reader re-test lane's rounds (2026-10-16/17) postdate the first archive and sit in a third copy. Landing
either as a dated addendum to this folder is a separate call. The copies, beside the first archive:

- `sideband-critic-scratch-2026-10-17` (50 files): the S1 reader re-test lane's critic scratch (session 2722c7ea).
- `sideband-critic-scratch-2026-10-17-omitted` (562 files): what the first archive's rule left behind, by the wider rule.

Lanes of the era whose rounds appear in neither archive: the free-bigram twin's landing rounds and the fourth
session's three rounds over the derived ledgers (2026-10-01), the noise-floor registration (906edfd) and the
horizon-read landing (b71e9ca) of 2026-10-04, the OQ-20 landing's five critic rounds (2026-10-10), the docs
lanes of 2026-10-11 and 2026-10-12 (the record lines, the public-cut plan and the root README's four rounds
among them), the nineteenth session's rounds, run from the lockstep checkout and so under that checkout's Temp
slug, and the image audit's lanes B and C, which left no critic-named folder (lane C's session left two
reviewer scripts, in the second archive). ESPALIER_MEMORY.md's session rows describe each.

## Withheld from the public cut

155 of the 308 copied files are withheld from the public cut and stay in the private tree:

- `2026-10-13-b10c3ea1/` (10 files): critic rounds of the public-cut lane (the export tool, commit A, 3e7b744): they review the withheld export tool, its test and the plan, quoting their text, digests and placeholders, and go with them (plan 12; 14.2 item 3).
- `2026-10-13-46731adb/` (46 files): critic rounds of the public-cut lane (commit B, the pinned export and its proof, 977ff11): they review the withheld export tool, its test and the plan, quoting their text, digests and placeholders, and go with them (plan 12; 14.2 item 3).
- `2026-10-14-a8adf32c/` (73 files): critic rounds of the public-cut lane (the front-doors lane, d481935): they review the withheld export tool, its test and the plan, quoting their text, digests and placeholders, and go with them (plan 12; 14.2 item 3).
- `2026-10-15-c8cb4ef4/` (1 file): critic rounds of the public-cut lane (decision batch lane 1, the gates, 51ceb9c): they review the withheld export tool, its test and the plan, quoting their text, digests and placeholders, and go with them (plan 12; 14.2 item 3).
- `2026-10-15-9dfaf64d/` (23 files): critic rounds of the public-cut lane (decision batch lane 2, the tool, the allowlist and the record, 5c264b0): they review the withheld export tool, its test and the plan, quoting their text, digests and placeholders, and go with them (plan 12; 14.2 item 3).
- `2026-10-03-58dc4aea/critic/REPORT.md`: the critic's copy of docs/REPORT.md as of 2026-10-03, carrying the placeholders the export fills in the tracked file.
- `2026-10-02-12e6097a/strat/critic5/diff_ptrs.txt`: a diff hunk of the withheld idea file read by the R1 landing's fifth round; its lines go with the file they come from (plan section 3).
- `MANIFEST_WITHHELD.json`: their rows and digests.

The reasons above are the export tool's own (its spec holds the same keys and wording, pinned to this manifest
by the tool's test). The public reader sees the other 153 files byte for byte, the science lanes'
rounds among them, fourteen of them with a residue entry in the tool's spec for a mention a frozen file cannot
mark: twelve quote the record's own pointer to a withheld idea file, one is the R1 landing diff the critic
read (its hunk of the idea file is the dated status line the record also holds in OPEN_QUESTIONS.md and
README.md), one holds a git status line naming the withheld test. WITHHELD.md lists them.

## Listed and not copied

- `12e6097a-8666-465a-b5a3-e76024a56cff/scratchpad/strat/critic6/pool.json` (would have been `2026-10-02-12e6097a/strat/critic6/pool.json`; 14,915,488 bytes, sha256 `d7cf82537cd0048fcc9e18fdfd110ce279b4c364c19b842a11b4decc12a4ac00`):
  a derived index (every formatted number of the R1 payloads mapped to the JSON paths holding it), 14,915,488 bytes, rebuilt by pool.py beside it from the committed payloads; not a report or a script.

## Where the words are

The reports and record excerpts, by folder (the scripts and outputs sit beside them; MANIFEST.json is the full
index; a file marked withheld is not in the public cut):

- `2026-10-02-12e6097a/`: `strat/critic/block_now.txt`, `strat/critic2/round1_report.txt`, `strat/critic3/round2_report.txt`, `strat/critic5/diff_bp.txt`, `strat/critic5/diff_ptrs.txt` (withheld), `strat/critic5/o_sweep.txt`, `strat/critic5/outcome.txt`, `strat/critic5/outcome_flat.txt`, `strat/critic6/added.txt`, `strat/critic6/outcome.txt`, `strat/critic6/outcome_n.txt`, `strat/critic6/removed.txt`, `strat/critic6/status.txt`.
- `2026-10-03-38e3cfca/`: [ledger/critic1/fi_head.md](2026-10-03-38e3cfca/ledger/critic1/fi_head.md).
- `2026-10-03-bd3df22e/`: `critic_confirm/mine.txt`.
- `2026-10-03-58dc4aea/`: [critic/FINDINGS.md](2026-10-03-58dc4aea/critic/FINDINGS.md), `critic/REPORT.md` (withheld), [critic/WHY.md](2026-10-03-58dc4aea/critic/WHY.md), [critic/reg.md](2026-10-03-58dc4aea/critic/reg.md), [critic/reg2.md](2026-10-03-58dc4aea/critic/reg2.md).
- `2026-10-05-fdeffb05/`: `critic/added2.txt`, `critic/landing_added.txt`, `critic/readers_added.txt`, `critic/readers_added2.txt`.
- `2026-10-13-b10c3ea1/`: `critic1/eco58.md` (withheld), `critic1/ecoHEAD.md` (withheld), `critic1/sweep.txt` (withheld).
- `2026-10-13-46731adb/`: `critic10/plan_added.txt` (withheld), `critic10/plan_removed.txt` (withheld), `critic11/cl_added.txt` (withheld), `critic11/dry_cl.txt` (withheld), `critic11/dry_msg.txt` (withheld), `critic11/dry_plan.txt` (withheld), `critic11/plan_added.txt` (withheld), `critic11/se_added.txt` (withheld), `critic12/cl_wt.txt` (withheld), `critic12/dry15_cl.txt` (withheld), `critic12/dry15_plan.txt` (withheld), `critic12/plan127.txt` (withheld), `critic9/dry12_plan.txt` (withheld), `critic9/plan_added.txt` (withheld), `critic9/plan_plus.txt` (withheld).
- `2026-10-14-a8adf32c/`: `critic_frontdoors2/status_before.txt` (withheld).
- `2026-10-15-9dfaf64d/`: `critic_ga1/README.md` (withheld) (empty), `critic_ga1/crlf.md` (withheld) (empty), `critic_ga1/other.md` (withheld) (empty).
- `2026-10-16-4a635c95/`: `critic/status_before.txt`.

## Holding the folder to its manifests

- `tests/test_critic_recovered.py`: every row's file present with its digest and size on disk and in the index
  (`git hash-object --no-filters`), git's `text` attribute unset on every file (the glob line in .gitattributes;
  a checkout's autocrlf never rewrites these bytes), no home-path user segment other than the token and the
  fixture names of the copied tests, the lane of every row re-derived from the manifest's own windows and, where
  the commits resolve, the windows' times checked against git, the counts consistent across the two manifests,
  and this README regenerated byte for byte. It reads whichever manifests are present, so it holds in the public
  clone too.
- `python -I docs/audits/critic-recovered/recover.py --source <the archive> --date 2026-10-17 --check` rebuilds
  the folder in memory from the archive and reports any byte that differs and any file the build would not write
  (0 and none at the landing).
- The folder's session folders are left out of ruff (pyproject `extend-exclude`), and all of it out of the
  evidence-bytes citer scans (tests/test_evidence_bytes.py and tools/evidence_pins.py, RECOVERED_PREFIXES): its
  files quote digests of results files and instruments in whichever form the reviewer hashed, and the manifests
  quote the folder's own digests, none of which is a citation the record makes. In the public cut the folder is
  frozen (emitted byte for byte) and outside the tone sweep, like the logs.
- [docs/REPORT.md](../../REPORT.md), FINDINGS.md and docs/WHY_THIS_DIES.md are the record; the copies of them here (the
  landing-text kit's session read them as they stood on 2026-10-03) are the reviewer's inputs of that day.

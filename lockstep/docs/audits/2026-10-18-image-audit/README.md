# Pre-publication image audit of lockstep, 2026-10-18

Read-only. The tracked tree was untouched at cdfe0b3 throughout; this report and the
front-door revision beside it are the commits after it (four, all on 2026-10-18: the first,
and corrections after the critic's first, second and fourth rounds). The audit's working files (the
finders' and refuters' JSON, their scratch scripts, the two reader walkthroughs) stay in the
author's private scratch and are not shipped; the counts below were printed by a tally script
over those files on 2026-10-18, and the recomputed figures are the refuters' own, each
reproduced from the committed files at cdfe0b3 (and amber's payloads at the commits lockstep
cites) with code of their own. One disclosure about the orchestrator: its baseline run of the
five validation commands on the checkout, before the audit began, wrote three gitignored
outputs (`tools/__pycache__/` and `.claude/hooks/__pycache__/`, from the repair gate's
`compileall` step, which ignores PYTHONDONTWRITEBYTECODE, and `.claude/GODFILE.md`, from its
godfile step); `git status --porcelain` stayed empty.

## How it was run

- 172 tracked files at cdfe0b3 (`git ls-files | wc -l`), in five slices: the coder core
  (src/lockstep/rac.py, codec.py, cdf.py, models.py, drbg.py, specs/decode-profile-v0.md);
  the container, CLI and conformance surface (container.py, manifest.py, cli.py,
  conformance.py, envprobe.py, errors.py, the container and conformance specs, the packaging);
  the research instruments and protocols (tools/lockstep_costmodel.py,
  tools/lockstep_profile_advisor.py, tools/lockstep_gen_vectors.py, the two vector files,
  experiments/E-001 to E-006); the tests (tests_project/); the agent harness the record was
  kept with (tools/trellis_*.py, .claude/, memory/, the harness pages of trellis-docs/).
- Each slice was read by two Opus finders (a correctness lens; a craft lens), the record
  documents by one more (the findings, decisions and runs logs, docs/01, 02, 04, 05, 08 and
  09, README, ASSESSMENT, VALIDATION, CLAUDE.md, CHANGELOG, TP-7, TP-8 and the archived task
  packs' status lines), and a staging export of the public layout by two readers in role: a
  research scientist with thirty minutes and a hiring manager with five. Every finding then
  went to a default-refuted Opus refuter for its slice (six refuters; the record's refuter
  also judged the two readers' findings, which amber's audit of 2026-10-17 left unrefuted),
  who reproduced each claim with their own code, searched the record for prior disclosure,
  and added what the finders missed. Nineteen agents in all, each an instance of the same
  model family as the orchestrating assistant, which wrote the briefs and this report and ran
  none of the recomputes itself; its own runs were lockstep's five validation commands, on the
  checkout and inside the staging export.
- Tally: 165 findings as found (33 high, 76 medium, 56 low); 131 confirmed, 31 downgraded, 1
  upgraded, 2 refuted; 8 added by the refuters. Survivors: 171, of which 25 high, 65 medium,
  81 low. The 25 high survivors are ten distinct defects; seven of the 25 are one, the vector
  files' line endings (item A1), found independently by seven agents in four slices.

## The answer to "what does the repository tell a stranger"

The researcher would reuse the coder and the conformance vectors, cite F-17 as an example of
the record correcting itself, and cite amber, not lockstep, for the determinism measurements;
lockstep's economics read as bound to placeholder inputs. The hiring manager would not forward
the folder as staged, because its first screen said the repository stays private, has no
licence and names talking to prospective users as its next work, and would forward it with
the front door rewritten.

What held, as measured in the audit: the tests_project suite (82 passed, 39 subtests) on CPython
3.10 to 3.14 on Linux and 3.11 on Windows; the harness suite (115 passed, 4 skipped) and the
repair gate; `self-check` 6 of 6 vectors; three encoders the agents wrote without importing
lockstep each reproduced all six payload hashes, under the reading of specs/decode-profile-v0.md
the reference code follows (not independently of it: the agents of slice S1 had read rac.py;
item D3); no untyped exception on any malformed manifest tried, 3,000 random mutations
included (14 of which the reader accepted), though one malformed form, a null `writer`, is
accepted where the container specification says reject (S2-C-5); F-4, F-5 and F-17's
arithmetic reproduce to the
printed digit; the F-12, F-13, F-17, F-18 and F-20 figures checked against amber's payloads at
the cited commits match at printed precision.

## A. Before the public push (this commit, or the export)

1. **The vector files' line endings** (S2-C-1, S2-K-1, S3-C-5, S3-K-1, S4-C-1, S4-K-1,
   S5-C-2; high). src/lockstep/conformance.py pins the sha256 of the packaged
   `vectors_v0.json`'s LF bytes and the tree tracked no .gitattributes, so a clone made with
   `core.autocrlf=true` (Git for Windows' default) wrote both copies with CRLF (3,290 bytes
   against 3,208): `self-check` exited 1 with "packaged conformance-vector bytes do not match
   the pinned lsp0 digest" and the tests_project suite read 3 failed, 79 passed, while
   `tools/lockstep_gen_vectors.py --check` printed OK (item C1). F-11's Windows reproduction
   stands for its regime, a tree unpacked from an archive, which never passed through a git
   checkout. The first front-door commit adds a .gitattributes marking both copies `-text`. The
   generator's half stays open (item C1): with the attribute set, a CRLF file written by
   `--write` on Windows is committed as written, where git, under core.autocrlf true or input,
   had converted it before.
2. **The licence** (R-2, W1-3, W2-1; high). README.md's Licensing paragraph said no licence was
   selected and the repository should not be presented as licensed; the harness decision D-1
   says "This revision uses the MIT license"; the public repository's root licence is MIT for
   all three folders. The front door's dated note states the last. Left for a later patch: the
   package metadata declares no licence, and a wheel built from this folder alone carries no
   licence file (S2-C-4, S2-K-10; the field's form depends on the setuptools range the
   project pins).
3. **The sentences the release falsifies** (R-1, W1-9, W2-3; medium): "the repository stays
   private" (README.md's first banner), TP-7's "stays private" and F-19's "Anything public about this work
   is built elsewhere". The front door's dated notes supersede them; the sentences stay as
   written.
4. **The parking banner's verdict** (R-3, W1-1; high). README.md's parking banner says "the contract that
   holds is an fp32 pin on token order (F-18)"; F-18 says the resolved token is stable at
   batch 1 with the escape on, while the top-64 order differs at 379 of 49,056 positions and a
   batch-8 decoder desyncs once. The front door states F-18's reading; the banner stays as
   written.
5. **Pointers into withheld documents** (R-16, W1-8, W2-7, S5-C-7, S5-K-5, S3-C-9; medium): the
   export marks every line naming a withheld file, and the marker rule now also matches the
   shorthand forms the record uses (`docs/07`, the "Blueprint" letters of the withheld review); [withheld: docs/07 not in this repository; see WITHHELD.md]
   the parking banner's pointer to sideband's withheld idea list is recorded in the export's
   WITHHELD.md.
6. **CI** (R-17, S4-C-5, S4-K-12, S5-C-8; low to medium): VALIDATION.md, ASSESSMENT.md,
   CHANGELOG.md and F-10 describe this folder's own workflow, which the public repository does
   not ship; its root workflow runs the five validation commands from this folder.
7. **TP-7's two home-directory paths into the amber checkout** (R-19; low) are scrubbed by the
   export; its third path, into the sideband checkout, ships under the export's own-checkout
   rule, as the sibling folders' do.

## B. Record-level: candidates for dated errata, none landed in the findings log

Each needs lockstep's own append-only lane (a dated finding or note, never a rewrite). The
shipped harness tests pin some of the text a fix would touch (MISSED-S5-1: rewriting D-1 fails
`.claude/trellis-tests/test_public_project_surface.py`, removing the bootstrap permission
fails `test_settings_scope.py`), so the notes are appended or the test changes in the same
commit.

1. **F-2's absorption boundary** (R-8, S1-C-1; high). F-2 says the integer grid absorbs drift
   up to about half a grid step. F-2's own generator (tests_project/test_cdf.py: 200 cases,
   V=128, total 2^15) keeps 165 of 200 CDFs identical at 1e-7, 98 at 3e-7, 10 at 1e-6 and 0
   at 2e-6, against a half step of 1.53e-5: the median case flips at 0.02 of a half step and
   none survives a quarter step; the boundary scales as step/V. F-2's two printed counts
   (200/200 at its two endpoints) reproduce. docs/01, docs/04, the test's docstring and EF-7's
   "The finding was never wrong" (docs/09) repeat the half-step claim.
2. **F-6's drift model** (S3-C-1; high). F-6's counts (24/24, 0/24) reproduce only when the
   1e-7 drift is applied as an absolute probability change on every symbol; applied as a logit
   drift, as OQ-12, F-7 and E-006 define it, a 2^20 grid at V=32,768 stays identical in 23 or 24
   of 24 trials. The later measured drift (about 6.7e-6) brings 2^20 at V=128,256 back to 0/24,
   so the verdict F-6 drew holds at measured drift, by a different route. Its probes were never
   committed (R-21).
3. **The economics' stated reason** (S3-C-2, S3-C-3, S3-K-3, W1-6, W2-9, MISSED-S3-1; high).
   F-8's "pack is 92% of TCO" and its "with pack cost set to zero, lsp1 wins by 23%" both come
   from a 2 MB/s decode placeholder. Every rate the record measured is far slower (the 9,233
   positions/s teacher-forced replay, amber's 26 tok/s GPU decode, its 8.66 tok/s CPU decode),
   and with any of them in the cost model lsp1 costs more than zstd -19 even with packing free,
   so D-14's free-packing branch does not survive measured inputs either. F-19 calls the
   economics "measured", but its 460x divides one measured rate by a break-even built from
   placeholder prices and ratios; across the record's own alternative inputs the gap runs from
   55x to 988x. The verdict, that the standalone thesis loses, survives every input set the
   refuters tried; the reason given for it does not.
4. **"amber's production coder"** (R-5, W1-2, W2-2; high). F-15's title, the run_010 row and
   F-19's "What stands" say lockstep.rac became amber's production coder. amber's D-8
   keeps Elias-gamma as the default with rac as the long-stream option, and the real archives
   amber decoded by draft replay record gamma as their coder (the P4, P5 and P6 payloads), rac
   having been measured in P3's rate comparison (amber's F-9). sideband's docs/ECOSYSTEM.md
   repeated the claim and carries a dated note since 2026-10-18.
5. **F-15's and F-16's Status "verified"** (R-6; high): outside the log's vocabulary (acted on,
   queued, noted), on evidence F-20 calls amber's, and on headlines F-18 qualifies.
6. **Every decision tagged [imagined]** (R-9, W1-4; high): the legend defines the tag as "design
   choice not yet built", and D-7, D-9 and D-11 are built and tested, D-15 is in use by amber,
   and D-8, D-10, D-13 and D-14 describe a profile F-19 records as never built (the refuter's
   reading; F-19 names no decision).
7. **The runs table** (S3-C-4, R-7, W1-11; high to medium): run_009's row keeps "F-8's
   placeholder was 10-20x too pessimistic on pack speed", which F-17 withdraws (the measured
   rate is 11.5x below the placeholder), and its "32.8 tok/s", which F-17 corrects to 25.0
   token-weighted; the linked-findings table has no rows for F-17 to F-20.
8. **F-15's "~3.65x bf16 time"** (MISSED-R-1; medium) is a ratio of amber's teacher-forced capture
   throughputs, not of replay; amber's P4 replay ran fp32 faster than bf16, and F-16 itself says
   fp32 was not slower.
9. **F-14's "the archive's encode AND decode work"** (MISSED-S3-2; medium): the 9,233
   positions/s is teacher-forced replay; decode ran at 26 tok/s (F-16).
10. **D-12's reason** (S1-C-4; medium): raising the coder's probability total does not break the
    lsp0 vectors (all six reproduce at 2^24 and 2^30); what breaks is the manifest's exact pin.
11. **Damage reported as something else** (S2-K-2, MISSED-S2-1, S1-C-3; medium): neither digest
    covers the manifest, so in a 645-byte archive 59 of the single-bit flips read as "decoder
    desync (nondeterministic model?)" and 63 as an unsupported profile; docs/04's row "decode
    raises CoderError = model desync" never fires, because the coder cannot detect damage and
    the payload digest catches it first.
12. **F-3's "the coder/model core is robust" and the 10,000-case sweep** (S4-C-2, S4-K-11,
    MISSED-S4-1; medium): the sweep has no committed instrument, and a byte-mutation sweep
    cannot reach the decoder past the payload digest.
13. **F-8's figures beyond the cost model** (S3-C-6, S3-K-2, MISSED-R-2; medium): the committed
    tool prints F-4's numbers; F-8's need a source edit, and its hybrid-routing figures have no
    instrument.
14. **E-006's stop condition** (S3-C-7, S3-K-10; medium) names no statistic; the two recorded runs
    sit below it at the median and above it at p99 and max, and no entry says whether it fired.
15. **F-6's "E-002/E-004 re-scoped"** (S3-C-8, S3-K-8; medium): both protocols are unchanged since
    the import and still describe the probability grid F-6 ruled out.
16. **"Crosses at 22% to 41% of positions"** (R-4; medium) is the 1e-3 grid only; the record's own
    candidate 1e-2 grid crosses at 2.6% and 5.0% (F-12, F-13) and was never priced.
17. **Stale status text** (R-11, R-12, R-13, R-15, S3-K-7, S3-K-9; medium): docs/08's "Honest
    current status" (no killer answered, "the core tech is proven"), README's "Research
    direction", OQs answered or mooted but not struck, the profile advisor's default verdict at
    the 1e-7 drift the record later measured 30x to 70x too small, and protocols with no status
    lines.
18. **Prior art** (R-20; medium): the gap docs/02 claims ignores ts_zip's published cross-hardware
    determinism, and PA-10's throughput cost misreads its source.
19. **The harness's history inside the record** (R-10, S5-K-2; medium): D-1 to D-5 and run_001 are
    the harness template's own entries, and their "task pack 4/5" sources collide with lockstep's
    own TP-4 and TP-5.

## C. Guards weaker than their names

1. `tools/lockstep_gen_vectors.py --check` compares newline-folded text and never hashes the
   files, so it passes the CRLF copies that fail `self-check`; `--write` writes CRLF on Windows
   (S2-C-2; medium).
2. The harness's reference checker, godfile and citation hook recognise finding IDs written
   `F<N>`; this record writes `F-N`, so the repair gate's `refs` step checks none of the twenty
   findings or their 270 citations in the files it reads (a planted F-99 passes), and its "all
   stable references resolve" is true today by accident (S5-C-1, S5-K-1; medium).
3. The 768-case fuzzer reaches the range decoder in 8 cases, each with the authentic payload,
   and never checks a successful unpack's output; no test checks the CLI's failure exit (a CLI
   exiting 0 on a damaged archive passes); two parser guards and two re-checks can be deleted
   with the suite green (S4-C-3, S4-C-4, S4-C-6, S4-C-7; medium to low). The code held where the
   refuters tested it directly (2,800 hash-consistent hostile payloads, 0 leaked exceptions).
4. No lsp0 vector reaches the adaptive model's rescale step, so an implementation with no rescale
   passes 6 of 6 (S1-K-1; medium).
5. `self-check` skips the streaming codec the CLI uses, and pytest runs the checkout's source,
   not an installed build (S2-K-8; medium).
6. The harness's hooks call `python` and fail open where only `python3` exists (S5-C-4, probable);
   its shared permissions let an agent rewrite the gates' own code and run the bootstrap, which
   replaces CLAUDE.md, without a prompt (S5-C-5, S5-C-3; medium).

## D. Code and craft

1. `quantize_probs` gives different CDFs for bit-identical float inputs on CPython 3.11 and
   earlier against 3.12 and later (`sum()` became compensated); no lsp0 path calls it and no
   vector byte moves (S1-C-2; medium).
2. A `read()` returning None is taken as end of stream by the streaming encoder and decoder, so a
   non-blocking source truncates silently (S1-C-6, S1-K-8; medium); `pack_file` and
   `unpack_file` publish files with mode 0600 (S2-C-3; medium).
3. The decode profile leaves the coder's initial state and the DRBG counter's start index
   unstated, which an implementer must supply, and its renormalisation sentence reads as three
   successive loops, under which an encoder reproduces 1 of the 6 vectors; under the one loop
   rac.py runs it reproduces 6 of 6 (S1-C-9, S1-K-2, W1-14; low).
4. Half the tracked files are the harness (96 of 172), which the README never explains; its
   install manual names an installer and a release gate that are not here (S5-K-3, S5-C-6;
   medium). The research used its findings, decisions and runs logs, the task-pack format and the
   critic agent.
5. Template residue in the harness's agents and skills, and in CLAUDE.md's opening (S5-K-4,
   S5-K-6, R-13; low to medium).

## What this commit changes, and does not

README.md gains a plain-language first screen above the record as it stood on 2026-10-11, which
is kept beneath unchanged; the first screen carries the dated notes of A2, A3, A4, A6, B4 and
B17. A .gitattributes marks the two vector copies `-text` (A1). This report is added. The second
commit corrects the first screen and this report after the critic's first round (the cost
model's labels, the encoders' independence, F-5's place, the pack rate's scope, the harness's
test count, the roles sentence), the third after its second (item B4's archive scope, item A1's
line-ending condition, section B's heading, who had read the reference code), the fourth after
its fourth (the malformed-manifest sentence's scope, item B4's payloads). No finding,
decision, protocol, test, tool or vector changed. Not pushed: Actions are enabled on the
remote.

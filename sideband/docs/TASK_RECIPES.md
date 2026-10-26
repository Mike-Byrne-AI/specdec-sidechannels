<!-- espalier:seed-version v0.8.0b2 sha256:24ceb6501c4a660a1ff9378ee5a4404fe99713220163afdbfcb66d7f0e1773d6 -->
<!-- espalier:seed-doc — Illustrative reference from Espalier-Harness.
     The examples below describe the harness's OWN conventions; adapt them
     to your repo. This file is yours — unmarked, refreshed on re-init only
     while it still matches the copy it was deployed from, and otherwise
     left exactly as you left it. -->

# Espalier-Harness — Task Recipes

## Starting a New Session

The SessionStart hook already loads state. Typing `/context-load`
at session begin is no longer needed; reserve it for explicit mid-session
re-orient, post-PostCompact recovery, or DEGRADED-surface recovery.

```
/status              — 10-line view: branch, dirty files, blueprint, fingerprint
/context-load        — explicit re-orient (mid-session, post-compact, DEGRADED recovery)
```

## Making a Change

Focused change (one bounded edit, one proof path):
```
/implement-task <description>
  → presents plan, waits for approval
  → creates one-step execution plan
  → implements
  → runs pytest tests/test_{module}.py -q
  → reports results
```

Coordinated change (3+ files, migrations, refactors, release hardening):
```
/implement-task --multi <description>
  → multi-phase with per-step gates and final integration check
```

## Before Pushing
```
/preflight           — full gate: lint + tests + surface audit + reflect
/commit              — review uncommitted changes, run risk check, stage and commit
```

## Landing a Finding or an Experiment Change (this repository)

CLAUDE.md: run the sideband-critic before merging experiment changes or new findings; its
highest-value mode recomputes decisions from the raw state files, not reading the diff.
```
/implement-task <registration or landing>   — plan, edits, targeted proof (the critic lane fires in step 6)
/critic <finding | payload | diff>           — sideband-critic, recompute mode by default; BLOCKING = no-go
/preflight                                   — findings lint in step 1; the critic lane in step 6 on the record surface
/commit                                      — harness convention (docs/CONVENTIONS.md, "Decision (2026-10-01)")
```
The lane lives in managed command bodies that a harness re-init regenerates — see
docs/SHARP_EDGES.md, "Managed harness files regenerate on re-init".

A landing whose payload attests a new instrument sha extends the frozen closure (first done 2026-10-01, the
free-bigram twin): add the tool to `extend-exclude` in `pyproject.toml` in the landing commit, or
`tests/test_harness_doc_claims.py::test_ruff_excludes_exactly_the_frozen_instrument_closure` goes red (checked
in a scratch clone: d55e62f plus the landed payloads with `pyproject.toml` unchanged gave 1 failed); then update
the closure counts in CLAUDE.md's Harness section, docs/CONVENTIONS.md ("Code style") and docs/SHARP_EDGES.md
("Frozen instruments are byte-pinned").
From 2026-10-03 (EVID-1) the freeze commit also adds `tools/<tool>.py -text` to `.gitattributes`, so every checkout
writes the bytes the payload will attest; once a payload cites the sha, check 4 of `tests/test_evidence_bytes.py` goes
red without the line. Any other file a payload cites by sha (a registration doc, a prompt file) gets the same line.
From 2026-10-16 (lane C of the image audit) any commit that adds, removes or changes a full-sha256 citation of a
tracked file (a payload's provenance, a test pin, a doc quoting a digest) runs `python tools/evidence_pins.py`, then
`python tools/evidence_pins.py --write`, and commits tests/evidence_pins.json in the same commit; check 6 of
tests/test_evidence_bytes.py is red otherwise, and `--write` refuses to drop a digest whose bytes changed unless the
landing names it with `--accept`.

Third instance, 2026-10-03 (`tools/run_prefetch_r2.py`): `pyproject.toml` `extend-exclude` lists twelve tool entries
beside `tools/cc`; CLAUDE.md says nine attested of twelve. Three habits from that lane (docs/SHARP_EDGES.md has the
measured entries): run the long test file alone with the maximum background timeout; put the critic's verdict and the
hashed files' shas in the freeze commit's body and name every post-GO edit in the record (docs/CONVENTIONS.md, "Evidence
and commits"); hold the turn open with a Monitor on `.espalier-state/code_reviewed` while a background reviewer runs, so
the Stop gate is not re-triggered. A registered rerun of this tool needs the Hugging Face cache and LF bytes on disk;
`--conclude-from` and `tests/test_prefetch_r2_landing.py` need only the committed state files.

Fourth instance, 2026-10-04 (`tools/run_prefetch_horizon.py`, the horizon read): `pyproject.toml` `extend-exclude`
lists thirteen tool entries beside `tools/cc`; CLAUDE.md says ten attested of thirteen. The `-text` line went in with
the freeze commit (b41d3f3), as the EVID-1 rule asks, so check 4 of `tests/test_evidence_bytes.py` stayed green when
the payloads cited the sha; the pyproject entry waited for the landing commit, and the witness test was red on the
tree from the moment the payloads existed until it went in (the recompute critic's advisory 2): add the entry in the
same edit as the payloads, before any proof run.

Fifth instance, 2026-10-04/05 (`tools/run_noise_floor.py`, the seed-noise floor readouts): `pyproject.toml`
`extend-exclude` lists fourteen tool entries beside `tools/cc`, eleven attested. The `-text` lines for
`tools/run_noise_floor.py` and `tests/test_noise_floor.py` went in with the freeze commit (906edfd), and `HAND_PINNED`
in `tests/test_evidence_bytes.py` gained the test file there; the pyproject entry went in at the landing commit
(73d8dc2) in the same edit as the payloads, so the witness test was not observed red: the entry preceded the
first proof run after the payloads existed (the fourth instance's advisory, applied). The landing texts were
generated through a registry with the carried literals (range bounds,
regime constants, arXiv ids, a modified table row's own numerals) registered; the kit's `Pair` class is
prefetch-shaped, so this payload family used its own generator over the kit's `check` / `Doc` / `wrap` / `score`.

Sixth instance, 2026-10-10 (`tools/run_seed_replay.py`, the OQ-20 seed replay): `pyproject.toml`
`extend-exclude` lists sixteen tool entries beside `tools/cc`, thirteen attested. The `-text` lines for the
tool and `tests/test_seed_replay.py` went in with the freeze commit (b6d3701) and `HAND_PINNED` gained the
test file there; the pyproject entry went in at the landing commit in the same edit as the payloads (the
fourth instance's advisory, applied). Two habits from this lane: registered GPU runs launch from a clean clone
of the launch commit with `--out` into the working tree, because the instrument's git stamp counts untracked
files (probably why every earlier verdict meta reads `-dirty`; the registration's reading, probable, not
verified); and the launch gate is the tool's own `--replay-check` over committed sidecars, recomputable by
anyone, never a deleted scratch comparison. The landing texts were generated through a registry with the
carried literals (the record rows a status note re-emits, the registration's ranges and probabilities)
registered; the kit's `Pair` is prefetch-shaped, so this family used its own generator over the kit's `check`
/ `Doc` / `wrap` / `score`. One failure of this lane: the frozen test file's pre-run assertions went red the
moment the seed-6 sidecars were committed, and that commit was made without running the suite (the critic's
landing round caught it; the block's DATED AMENDMENT discloses it). Run the frozen test file before an
evidence-only commit, and write a pre-run assertion as a branch on the evidence's presence from the freeze on.

Seventh note, 2026-10-14 (the thread-count entry of docs/SHARP_EDGES.md): a registered run whose field a later
test recomputes bit-exactly records in its payload's provenance the runtime thread count and kernel from
`threadpoolctl.threadpool_info()`, the numpy version and the OpenBLAS build `np.show_runtime()` reports, and the
thread-cap environment variables in force; a NEW registration's recompute test runs under the same numpy wheel and
thread caps, in its own process rather than inside the pytest process (the existing in-process landing recomputes
stand as registered; call PC-5 of the public-cut decision batch; `tests/test_outcome_head.py` is the pattern).

Seventh instance, PENDING (registered 2026-10-16, not frozen or landed; the 2026-10-14 paragraph above is a note,
not an instance): `tools/run_reader_s1.py`, the S1 reader re-test's word instrument. Its `-text` line and one for
`tests/test_reader_s1.py` sit in the uncommitted `.gitattributes` for the freeze commit, and `HAND_PINNED` in
`tests/test_evidence_bytes.py` gains the test file in the same change, because the registration's freeze line cites
the test by a 12-hex digest the scanner does not see. The tool joins `extend-exclude` at the landing, not at the
freeze; the registration (docs/BLUEPRINT.md, "S1 READER RE-TEST REGISTRATION") puts the closure then at seventeen
files, fourteen attested, against sixteen tool entries beside `tools/cc` on 2026-10-16
(`sed -n '/extend-exclude/,/\]/p' pyproject.toml | grep -c '"tools/run'`). The instrument imports the frozen
`tools/run_reader_lens.py` by bare name and asserts its raw-byte sha256 at import and again before any conclusion
(`tools/run_reader_s1.py:99 assert_frozen_reader_lens`), the parent guard `run_prefetch_bigram` set, without its LF
normalisation. A dated line here records the landing when it happens. Landed 2026-10-17: `tools/run_reader_s1.py` joined `extend-exclude` at the landing commit in the same edit as the word payload (seventeen tool entries beside `tools/cc`, fourteen attested); `tests/test_reader_s1_landing.py` pins both instruments' shas, the state files' shas, the labels, the licences, the word and the pairing checks; the three clean-clone gate-cell reruns were identical except runtime_s.

Landing texts, from 2026-10-03 (`tools/landing_text.py`, the kit; its docstring has the API): the generator and
the applier stay per-landing scratch scripts that import the kit by bare name from `tools/`. GENERATE: build a
`Pair` from the two payloads with the instrument's own reading function and floor
(`run_prefetch_readouts._reading` and `MATERIAL` for the prefetch family), `assert_registered` on the freeze
commit and the label, and compose every sentence from `pair` / `pp` / `pt` / `rdp` so that no numeral and no
reading word is typed; `Pair.write` refuses a banned phrase (whitespace-collapsed, case-folded) and writes the
texts (LF) beside `numbers.json`; `check` traces every numeral outside the docstring's exclusions and every split
reading, while a single derived word is guarded by derivation alone. APPLY: survey line endings first
(`python tools/landing_text.py eol`, at HEAD, before the first edit), then one `Doc` per record file with
`expect="lf"` on EVERY file the survey read LF (FINDINGS.md, README.md and CLAUDE.md among them: a
`git checkout --` on this box re-materialises each of them as CRLF, and a detected ending would follow the
residue), CRLF files detected, mixed refused; `refuse_if_present` on the dated marker; insertions by
`insert_after_paragraph` (the blank-line rule; it refuses inside a tight list of bullets, numbered items or table
rows such as a FINDINGS.md block, where `insert_after_line` is the tool) or `insert_after_line`; replacements by
`replace_once` / `flex_replace_once` (across a wrap) inside a `region` wherever a frozen text carries the same
phrase; `write(dry=True)` first. CHECK: `git add -N` any new file (an untracked path is refused), then
`python tools/landing_text.py check <numbers.json> --added <every edited file>` (unknown numbers, pairs lost in
application, banned phrases on the diff's added lines, a note on any file that is not a pure insertion) before the
critic's text round. FIX by revert-and-regenerate, never by patching the file: `git checkout --` the generated
files, `python tools/landing_text.py eol --fix-lf <every LF file among them>`, regenerate, re-apply, re-check;
every post-GO edit is named in the record and re-hashed (docs/CONVENTIONS.md, "Evidence and commits").
`tests/test_landing_text.py` pins the kit, including the 2026-10-03 case on the committed R2 payloads.

> **Interpreter note.** The commands below spell `python`. A stock macOS ships only
> `python3` (and it is 3.9; Espalier requires 3.10+), while many Windows installs ship
> only `python`. Use whichever both resolves AND reports 3.10+
> (`<name> --version`); on a stock macOS `python3` resolves but is 3.9.
> `espalier doctor .` checks this for you.

For a release commit, run the three-tier ladder (see `docs/RELEASE_CHECKLIST.md` — self-host only;
`scripts/` and the release checklist are not deployed by `init`):
```bash
# Espalier source repo only -- not deployed by init
python scripts/release_check.py                  # Tier 1 — fast signal (seconds; 19 passed, 3 skipped)
espalier pre-release .                           # Tier 2 — local readiness gate (about 45 min serial with tests on: 2,711 s measured 2026-09-23, bounded at twice that)
python scripts/final_release_matrix.py           # Tier 3 — publish proof (6 stages; 55:39 measured 2026-09-23, stage 02 alone 45:14; the matrix strips the opt-in flags from every child that would act on them, so none are set here)
python scripts/release_check.py --validate-archive "$(ls dist/final-release-matrix/source_archive_work/archive_out/*.zip)"   # the archive the matrix built, inside stage 02's work dir
```
Inspect `reports/final_release_candidate_report.json` (written by the matrix; Espalier source repo only) for `ready_to_tag: true` before `git tag`.

## Exporting the public cut

A private-workflow recipe: the tool, its test and the plan are withheld from the public cut, so a reader of the
public repository cannot run it (the mention rule marks the lines below that name them).
Plan of record: docs/PUBLIC_CUT_PLAN.md sections 6, 7, 10.7, 11 and 12; the staging folder is the one plan 11.4 [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
names. The tool is `tools/export_public_cut.py` [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
(pinned test: `tests/test_export_public_cut.py`); the export-only sources live under `docs/public_cut/` and must be [withheld: docs/public_cut/, tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
COMMITTED for a pinned export (`--worktree-sources` reads the worktree instead and records a blocker).
```
python tools/export_public_cut.py export --target <staging>\export [--repo R] [--folders F] [--commit HEAD] [--worktree-sources] [--no-git] [--ship] [--force-fresh-history] [--repo-url U] [--author A]... [--copyright-holder H] [--release-date D] [--release-tag T] [--git-user U --git-email E] [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
python tools/export_public_cut.py scan --target <staging>\export [--repo R] [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
python tools/export_public_cut.py prove --target <staging>\export --scratch <empty dir> [--receipt <path>] [--skip-suite] [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
```
- The manifest lands beside the target (`<staging>\export.manifest.json`); the verdict prints `SHIP: GO` or
  `SHIP: NO-GO (<n> blockers)` with every blocker listed. `export` exits 0 either way unless `--ship` (NO-GO -> 2) or
  a secret-shaped hit (always 2, and git is skipped); `scan` is the gate and exits 2 on any blocker; a refusal or an
  error (a bad manifest, a missing source, an anchor that does not match) exits 3, so "exits 2" never passes on a
  crash. A re-run removes
  the manifest's paths (a deleted one is skipped), the repository, the stamps and the push record when no listed
  file has changed, and refuses a hand-edited file, a foreign file and a repository that has a remote or a push
  record (`--force-fresh-history` to confirm a rewrite; the record is carried into the new manifest's
  `previous_export`, so every later re-export of a once-pushed history needs the flag too).
- The order is `export`, then `scan` (the gate: exit 2 on any blocker; on GO it writes `<staging>\export.gate.json`),
  then `prove` (exit 0 only on an exact PASSED, which writes `<staging>\export.proof.json`), then `git remote add` and
  `git push` from `<staging>\export`. The export repository's `pre-push` hook refuses a push unless the manifest beside
  it says GO and a gate stamp from a GO `scan` binds that manifest's bytes and HEAD (a refused scan removes the stamp
  first), the proof stamp is for HEAD, every pushed sha (an annotated tag resolved to its commit) is HEAD, and the
  remote, normalised (case, scheme, user, a port, a leading `www.`, the scp colon, a trailing slash or `.git`), is not
  one of the private checkout's; it is a seat-belt, not a gate: `--no-verify`, a hand-edited manifest, a second clone,
  an ssh alias from `~/.ssh/config`, a different host for the same service (`ssh.github.com:443`), a trailing-dot host,
  the scp absolute form `git@host:/o/p` and any other spelling the normalisation does not fold all pass it. A push the
  hook admits (a `--dry-run` and a push the server then rejects both count) is appended to `<staging>\export.pushed`
  and to the repository's own `.git/export-pushed`, with any `user:token@` part of the URL stripped, whatever the
  scheme's case, up to the last `@` before the path (the tool strips the same from every remote it records or
  prints; a backslash path is left alone); a push made with `--no-verify` or from a second clone leaves no record. A re-export after either record is refused without `--force-fresh-history` whether or not the remote is
  still configured, and so is one whose manifest records a repository now gone from `export\.git` with no record
  beside it (the record inside may have gone with it); a re-export is refused, flag or not, while the repository holds
  a commit or a ref beyond the export commit (a tag of that commit is fine, and the rewrite deletes it with every other
  local ref, so re-add the remote, re-tag, force-push the tag and re-create any release the host bound to the old
  tag). A moved or renamed `export\` folder keeps the hook but fails closed until the
  manifest and stamps beside it are moved with it; moving the whole staging folder carries them, and the hook admits.
  An allowlist entry whose reason says "flagged for the operator", a record line the tool's spec flags, and a
  deny-list match in a record file the sweep excludes (ESPALIER_MEMORY.md) that no `record_decisions` entry of the
  spec covers (class record-flag; a decision covers exactly the spans of its own text, so a match reaching beyond
  one, a word the decision cuts through or a second occurrence, still flags; a decision covering every occurrence
  of an outright flag's text clears that flag; a kept line is listed in the folder's WITHHELD.md by its reason,
  never by its text, and a reason that repeats the decision's text, matches the deny list or contains a flagged
  text is refused when the spec loads) are blockers until the operator decides, and a record file, flag or
  decision in the spec that matches nothing in the export is a blocker of its own (class record-stale, whose
  message says to remove the entry: withholding or scrubbing a flagged or decided line also removes its spec entry
  and updates the pins in `test_real_tree_scan_has_only_the_expected_hits` and the kept-line count in
  `test_real_tree_oracles_of_plan_sections_7_11_8_and_12`; keeping a flagged line adds a decision, which updates
  the same pins and, being a tool edit, needs a fresh pinned export from the new tool commit);
  `git log -G"flagged for the operator" -- docs/public_cut/tone_allowlist.txt` lists every commit whose diff touched a [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  flag line (`-S` would list only the commits that changed how many there are). `--worktree-sources` always yields a blocker (the sources are
  unpinned), as does a tool that differs from the pinned commit's copy; `--no-git` makes `prove` impossible. The commit
  identity is pinned (`sideband <sideband@local>`) unless `--git-user` and `--git-email` are both given; the public
  author is the operator's call. A correction after a push is a fresh history and a force-push: `--force-fresh-history`
  announces it and records the previous remotes and head in the new manifest; the old commits stay reachable by sha
  on the host and in any copy of the repository, so a first push that exposed something is a matter for the host's
  support, not a re-export. Dated update 2026-10-15 (lane 2 of the public-cut batch, plan 13.4): a decision, like
  any other edit of the tool or the allowlist, needs no pinned export until the final source commit, since the
  receipts bind at their own commits (PC-4) and lane 2 landed on a staging scan alone; the public author is
  decided (PC-1): docs/public_cut/identity.json supplies the identity defaults, `--author` is repeatable (`Name` or [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  `Name <email>`), and the git identity of the export commit follows the same file unless the flags override it.
- `prove` needs an EMPTY scratch folder and takes about an hour (the suite; `--skip-suite` for a partial proof); it
  refuses before any stage when the tool on disk differs from the one that made the export or the export ran with
  `--no-git`, and only an exact PASSED (never PASSED-PARTIAL or PASSED-NOGO) exits 0 and writes the proof stamp.
  Dated update 2026-10-18 (plan 15.9): with amber/ or lockstep/ in the export, `prove` reads the exported root
  workflow (`.github/workflows/ci.yml` in the clone) right after the clone stage and, after its own stages, runs
  each sibling folder's job as that workflow states it, in the workflow's order (amber, then lockstep): one clone
  and one venv per job, the job's working directory and env with the venv first on PATH, each run line as that
  venv's own program (`pip`, `python` and `pytest` only), then that venv's `pip freeze`. The stages are named
  `<job>-clone`, `<job>-venv`, `<job>-run<k>` and `<job>-pip-freeze` (a hyphen, since each names its log beside the
  clone), and the receipt records `sibling_jobs`, `sibling_pip_freeze`, `env_dropped` (PYTHONPATH, PYTHONHOME,
  PYTEST_ADDOPTS, PIP_* and GIT_* never reach a stage; since 2026-10-19 the launching shell's SIDEBAND_* and TRELLIS_* are
  dropped too, the tool's own stages setting SIDEBAND_REQUIRE_ANALYSIS themselves (the full run saw the launching
  shell's analysis switch reach the amber job; the critic's second round named lockstep's root override) and, when the
  workflow's python-version is not the box's,
  `sibling_python_mismatch`: the commands are the workflow's, the interpreter and the platform are this box's. A
  workflow the reader cannot follow (a plain workflow-level `env:` or `defaults:` key, since a quoted or otherwise
  spelled one passes unread, an inline or flow-style block, a job key other than runs-on, env, defaults
  and steps, an action other than checkout or setup-python, a block-scalar or empty `run`, a step-level key, a job
  with no working directory or no run step, no jobs), a sibling folder with no job, a job for no exported folder,
  or a run line naming another program or carrying a shell operator fails the proof (FAILED, exit 2, receipt
  written) right after the clone, before any venv is built. "Empty" means empty: a leftover `venv_amber` from a
  failed run is refused like a leftover `clone`. `--skip-suite` resolves the sibling jobs and runs none. The hour
  above predates these stages; the 15.9 proof took 59.5 minutes end to end, 55 of them sideband's own suite, the
  two sibling jobs about two minutes together.
- The private worktree and index are never written by `export`, `scan` or `prove`; the real-tree tests commit a
  snapshot of the worktree through a temporary index on the scratch ref `refs/tmp/export-snapshot` (deleted at
  teardown), so the pre-commit state is what they export.
- A new sweep hit is handled by a reviewed entry in `docs/public_cut/tone_allowlist.txt`, a reason comment directly [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  above each (required): `line<TAB><export path> :: <collapsed text>` or `word<TAB><token>`. A line entry for an
  exported folder whose text is on no line the sweep reaches, and a word entry whose word is on none, are blockers
  whose message says to edit the allowlist (the sweep reaches the top-level root files and each folder's *.md and
  *.py minus its exclusions, skipping a line that carries an exclusion phrase such as "dot product"; dated update
  2026-10-15: since lane 2 the phrase is cut out of the line and the rest is swept, gap 2 of plan 13, and a line
  entry's text is matched against the uncut line while a word entry is matched against the cut text).
- Sweep before the tree is exported and before each commit (dated 2026-10-18, plans 15.8 and 15.9). A tone-sweep
  word on an added line surfaces only when `tests/test_export_public_cut.py` runs its real-tree tests (15.8's one [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  word read 3 failed, 21 passed on that file's first run, and the file ran green after an allowlist entry), and
  every commit message up to the export commit is published in its folder's generated `docs/COMMIT_LOG.md`, where a
  deny-list or private-name match replaces the message's body with a marker. So run the tool's own patterns over
  the text first: import the tool by bare name from `tools/` and, for each line, apply `SWEEP_V` with the `SWEEP_X`
  phrases cut out (`SWEEP_X.sub(" ", line)`, as the sweep does), `COMMIT_LOG_DENY`, `PRIVATE_RE`, `PENDING_RE` and
  `PLACEHOLDER_RES`, and for every spec in `FOLDERS.values()` its `mention_re()` through `unmarked_names` (the
  spec's `extra_mentions` ride in it) and its `withheld_probes`; run it over the `+` lines (not `+++`) of
  `git diff HEAD -U0 -- <files>` and over the message file. A mention hit on a shipped line is a marker the export
  will place (in a frozen file, a blocker: the next bullet); in a message, reword it (15.8: lockstep's first draft
  named the withheld plan file). Plan 15.9's amber bullet records the lane's run. The script stays per-lane
  scratch, like the landing-text generator, so loop over every spec: sideband's probes and mention form are not
  lockstep's.
- A new withhold-whole key, or a new `-text` pin (dated 2026-10-17, the recovered critic folder): the spec derives a
  withheld name from every `withhold_whole` key without a `mention_exempt` entry (the path, the basename, an
  underscored stem; `FolderSpec.mention_patterns`), so a FILE key whose basename is a word of the record (`REPORT.md`,
  `MANIFEST_WITHHELD`) gets a `mention_exempt` entry with its reason in the same edit, and a FOLDER key gets none
  (it derives only its full path); `ep.SIDEBAND.mention_re().pattern` (the command in the SHARP_EDGES entry) shows
  what a key adds. A file the export freezes is emitted byte for byte and takes no `[withheld: ...]` marker and no
  fill, so with the pin line in the worktree run
  `python -m pytest -q tests/test_export_public_cut.py::test_real_tree_scan_has_only_the_expected_hits` before the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  pin is committed: a `withheld-name`, `private-name` or `path` hit in a frozen file is answered by a residue entry
  when the text is the record's own provenance, by withholding the file, or by changing a generated file's
  generator and regenerating, never by editing frozen bytes; and a frozen file that reproduces lines of a withheld
  file (a diff hunk, a copy) is withheld, whatever its mention says. A glob pin also needs the real-tree frozen
  oracle's prefix tuple extended by hand (docs/SHARP_EDGES.md, the EVID-1 `-text` entry). An empty withheld file
  needs nothing since the same day: it registers no withheld digest.
- Footguns: docs/SHARP_EDGES.md, "A fresh git repository built from exported files dropped a tracked file", "A tool
  that withholds passages by exact anchor cannot ship in its own export", "`mv` of a Desktop folder fails with
  'Device or resource busy'", "The `[pending:` placeholder class vs its instances" and "A test that exports `HEAD`
  cannot see a lane's uncommitted sources"; and, dated 2026-10-17, "A withhold-whole key's basename becomes a
  withheld name tree-wide, and a frozen file takes no marker".

## Grounding / Re-analyzing the Repo

First session after `init` (no saved fingerprint): `/analyze` **grounds**
the harness — repo-analyst establishes the baseline and docs-maintainer
populates docs/CONVENTIONS.md from your code. Later runs detect drift:
```
/analyze
  → runs repo-analyst agent
  → first run: establishes the baseline (grounding)
  → later runs: detects drift vs reports/repo_fingerprint.json
  → reports changed signals
  → run `espalier fingerprint .` to save new baseline
```

## Checking Harness Health
```
/smoke               — structural check + espalier audit . (JSON report, exits non-zero on failures)
/design              — full harness config review: agents, commands, hooks, docs freshness
```

## After Finding a New Footgun
```
# Add entry to docs/SHARP_EDGES.md
# Format:
## {Edge Name}
**What it is:** {description}
**How you hit it:** {triggering scenario}
**How to avoid it:** {fix or prevention}
```

## Authoring a Task Pack

Before implementing a pack, run the scope pre-flight to surface reference gaps:
```bash
espalier scope-check "task-packs/TP-<N>-<name>.md"
```

Three exit codes:
- 0 — pack has no scope gap, or operator accepted with `--accept-scope-gap "<reason>"`
- 1 — nothing parsed: no `## Affected symbols` / `## Affected literals` section, or every bullet declares nothing on purpose (a clean skip); or a declared one that parsed to zero entries, marked by a `scope-check: DECLARED_BUT_EMPTY --` line (the cause is printed; fix the pack before proceeding)
- 2 — scope gap present and unacknowledged

If exit 2: either expand `Scope (in)` to cover the gap, or accept it with a reason:
```bash
espalier scope-check <pack> --accept-scope-gap "test-driven discovery on small pack"
```

See `docs/PACK_AUTHORING.md` for the required `Affected symbols` section format.

## A mechanical `/goal` for pack execution

`/goal` is judged by a separate tool-less model that can only see what the
session surfaced — so the condition must be provable by **visible artifacts**,
never "the work was good" (see `docs/CC_AUTOMATION.md`, Espalier source repo — not deployed by `init`).
A copy-ready condition
for driving one pack to landing:

```
/goal Land task-packs/TP-<N>-<name>.md: scope-check printed, the pack's edits
applied, earn-the-red shown in the transcript (mutate -> RED -> revert), the full
pytest suite green (pytest output present), `espalier audit .` clean, and exactly
one atomic commit visible in `git log`. Run every gate synchronously in the
foreground and read its result in the same turn. Stop after 40 turns if not done.
```

Why each clause: every requirement is a *visible proof a tool-less judge can
read* (a printed report, pytest output, a `git log` line) — not a quality
judgment. Never accept "red-team ran" as proof (FAILURE_MODES §1.1 / §11.12);
keep depth-judgment + adversarial refuters in the work-turn. The `or stop after N`
clause bounds an unsatisfiable goal. For unattended multi-pack runs this is what
the loop-over-`claude -p` driver issues per pack
(`docs/AUTONOMOUS_EXECUTION.md`, Espalier source repo — not deployed by `init`).

## Adding a Test
```
/test-this <path/to/module.py>
  → test-writer agent reads module, checks existing tests/
  → generates test_module.py matching project patterns
  → runs pytest tests/<test_module>.py -v before presenting
```

## Archiving Claude Code session transcripts

`~/.claude/projects/` is auto-pruned by Claude Code on a retention timer. Set
`cleanupPeriodDays` in `~/.claude/settings.json` to stop the clock — but that
only prevents *pruning*, it does not create a second copy.

```
# Espalier source repo only -- not deployed by init
python3 scripts/archive_transcripts.py --check     # report only, writes nothing
python3 scripts/archive_transcripts.py             # archive if grown past the threshold
python3 scripts/archive_transcripts.py --force     # archive regardless
python3 scripts/archive_transcripts.py --print-plist   # launchd job, absolute paths filled in
```

The threshold is **growth since the last archive**, not absolute size — with
retention pinned the source only grows, so an absolute threshold would re-archive
the whole tree on every run once crossed.

Exit codes are distinct so a scheduler can tell the cases apart:
`0` archived and verified · `1` script error or refused · `2` verification failed
(the partial archive is discarded) · `3` below threshold, nothing written ·
`4` archived, **and the source had shrunk since the last run** — investigate.

Verification is three gates, all required: `tarfile` completed and skipped
nothing, the gzip stream decompresses end to end, and the archive's member count
equals `len(snapshot)` — the list taken *before* writing, never the count of what
tar managed to write. The file only takes its final name after all three pass.

It refuses rather than guesses in four cases, each earned from a demonstrated
failure: a source with zero files, a source the walk could not fully read, a
target filename that already exists (pass `--force`), and a `--dest` whose parent
is missing (an unmounted volume). It prunes only archives recorded in its own
manifest, never the one it just wrote, and never below one.

Pipe `--print-plist` to a file under `~/Library/LaunchAgents/` and `launchctl
load` it if you want it scheduled; the script never installs itself.

## Updating Docs After Code Changes
```
# Spawn docs-maintainer agent:
# "Update docs/CONVENTIONS.md — we added X pattern to espalier/Y.py"
# "docs/SHARP_EDGES.md — we fixed the Z footgun, remove that entry"
# "ESPALIER_MEMORY.md session log — record today's changes"
```

## Good Prompts

### For /implement-task
- "Add return type hint to all public functions in espalier/doctor.py"
- "Fix the bare except in espalier/scanners/imports.py line 42"
- "Add test coverage for the happy path in espalier/diffing.py"

### For /design (harness config review)
- "Review the harness setup — we added a new espalier/migrations.py module"
- "Check if any commands reference paths that no longer exist"
- "Is the test-writer agent up to date with our new fixture patterns?"

### For agents
- "Use the architecture-analyst to check if this PR violates layer boundaries"
- "Use the code-reviewer to review tools/cc/hooks/write_guard.py"
- "Use the docs-maintainer to check if docs/CONVENTIONS.md still matches the code"

<!-- espalier:seed-version v0.8.0b2 sha256:1c8220c2f79d8eca23d641eab33a02484c92588572092ba75b8bf3f836737e65 -->
# Sharp Edges

Footguns this repo, and this Windows box, actually have. Each was checked against a file or a command on
2026-10-01 at HEAD f1aabe4. An entry is the footgun, the mistake it prevents, and a one-line way to prove you
have hit it. Items marked "operator-supplied, 2026-10-01" come from the operator, not from the repo; where a
command can confirm one, it is given. Inferences are labelled. Delete an entry when what it describes is fixed and
nothing remains; when a fix leaves a residual footgun, rewrite the entry and date it.
An entry that outgrows ~30 lines moves to `docs/sharp-edges/` (see its README.md); `/recall <topic>` indexes
this file per `##` section.

Long-form entries under `docs/sharp-edges/` (seeded by the harness; kept because they describe the loop this
repo runs): [closed-loop-verification-trap](sharp-edges/closed-loop-verification-trap.md),
[convergence-is-an-angle-set-property](sharp-edges/convergence-is-an-angle-set-property.md),
[hook-exit-codes-channel-xor](sharp-edges/hook-exit-codes-channel-xor.md); the folder's
[README](sharp-edges/README.md) carries the filing rules.

## Targeted pytest runs: the editable install now points here (fixed 2026-10-01); cwd still matters

**Footgun (fixed 2026-10-01):** `sideband` used to resolve through a stale global editable install (`pip show
sideband` reported 0.2.0 at `C:\Users\Michael\Desktop\sideband`, a moved directory), so a single-file run of any
test importing the package died with `ModuleNotFoundError`, while the whole suite collected only because tracked
tools (`tools/e6_gate.py` among them) prepend `src/` to `sys.path` when a test imports them early in collection.
`python -m pip install -e ".[dev]"` from this repo root (README's own install step) re-pointed the finder:
`pip show sideband` now reads 0.3.0 at `...\Research\sideband`, `import sideband` works from any cwd, and
`python -m pytest --collect-only -q tests/test_stats.py` collects 33 tests with no flag. The shell-independent
fallback `python -m pytest -o pythonpath=src ...` still works on a box where the install is stale again.
What remains: tools default to cwd-relative paths (`tests/test_fullfree.py:310` pins `results/real/harvest_shadow`)
and `tests/test_oq18_rider_diag.py:223` evaluates a cwd-relative `skipif` at import, so run from the repo root;
a wrong cwd silently skips that test. One more edge (2026-10-01): the editable install binds `import sideband` to
ONE checkout. In a scratch clone a bare `python` imports this tree's `src/` (uncommitted edits included), not the
clone's; pytest's `pythonpath = ["src"]` (pyproject.toml, rootdir-relative) and `sys.path.insert(0, "src")` (relative to
the working directory, so run from the repo root) keep a clone on its own tree, and README's `pip install -e ".[dev]"` run inside a clone retargets the global finder.
**Mistake it prevents:** concluding the code or tests are broken, or "fixing" imports, when the finder is stale;
running tests from a sub-directory; trusting a bare import inside a scratch clone.
**Proof you hit it:** `pip show sideband` names a directory that does not exist, or `python -m pytest
--collect-only -q tests/test_stats.py` ends in `ModuleNotFoundError` (both clean on 2026-10-01 after the re-point).

## The full suite is slow; run the targeted file first

**Footgun:** operator-supplied, 2026-10-01: the full suite takes about 7 minutes on this box (6:54 and 7:57 on
2026-10-01, timed in-session; not reproducible from the tree). 583 tests are collected on 2026-10-03 with tests/test_landing_text.py (560 after the R2 landing; 513 after the code-review follow-up of 2026-10-01, 509 after the free-bigram landing; 506 at d55e62f, measured in an autocrlf=false scratch clone; 488 when this entry was written, 13 of them in `tests/test_fullfree_oracle.py`, tracked since 2026-10-01). Each registered instrument has its
own test file (`tests/test_prefetch_readouts.py` for `tools/run_prefetch_readouts.py`), which is the unit to run
after an edit. Use `-rs` to see why something skipped (5 skips are expected, see docs/CONVENTIONS.md "Tests").
**Mistake it prevents:** re-running everything after each edit, or reading a long silent run as a hang and
stacking a second run on top of it. Observed 2026-10-01 while another session's pytest was running: a background
full run reached ~56% in 25 minutes before its time limit killed it (cause not isolated).
**Proof you hit it:** `python -m pytest --collect-only -q | tail -1` prints `583 tests collected ...` (2026-10-03, with tests/test_landing_text.py; 560 after the R2 landing, measured in this audit; 513 on 2026-10-01 after the code-review follow-up; 509 after the free-bigram landing); a full
run is minutes, not seconds (time it before relying on a figure).
**Update 2026-10-03:** the R2 freeze commit's body records the full suite at 549 passed, 5 skipped in 758 s on its bytes.
Lane-reported, not re-timed here: two concurrent pytest sessions of the same long test file inflated each other from
about 13 minutes to 25-67 minutes, and two 40-minute background runs died at their time limit. Run the long file alone
and give the background run the maximum timeout (7200000 ms for a background Bash call).

## No `make`; shells differ; `python` only

**Footgun:** operator-supplied, 2026-10-01: `make` is not installed here, PowerShell is the primary shell, and
the Bash tool is Git Bash, so each takes its own syntax. Checked: `make` and `python3` are found in neither shell;
`python` is 3.11.9 (`...\Python311`). The Makefile targets by hand: `test` = `pytest -q`; `lint` =
`python tools/lint_findings.py` (standalone, works as is: `lint_findings: OK (27 findings ...)`); `experiments` =
`python experiments/run_all.py` (see the next entry); `all` = all three. Env vars: `PYTHONPATH=src cmd`
(Git Bash) versus `$env:PYTHONPATH="src"; cmd` (PowerShell); paths `C:/...` or `/c/...` versus `C:\...`. To check
line endings use `git ls-files --eol <path>` or Python bytes: a `grep -c $'\r'` through the Bash tool counted
every line as a match (observed 2026-10-01).
**Mistake it prevents:** typing `make test`, `python3`, or pasting a POSIX one-liner into PowerShell (or the
reverse).
**Proof you hit it:** `make test` -> "command not found" (Git Bash) / "not recognized" (PowerShell).

**Update 2026-10-04:** GNU grep 3.0 here aborts with exit 134 and prints nothing when `-i` and `-F` are combined
(`grep -i -F pattern file`; in a pipe the pipeline's exit is the last command's and the 134 hides in PIPESTATUS; `-F`
alone and `-i` alone work), so an absence check written that way is vacuous: a grep that printed nothing may have
crashed. Found by the critic on the EVID-1 lane and reproduced on this box; use Python for absence checks over the
record, or drop `-i`.

## A full `experiments/run_all.py` rewrites committed evidence

**Footgun:** `make all` and `make experiments` are the FULL run: `experiments/run_all.py` says "~10-15 min;
REWRITES the committed results/e0*.json + results/summary.json", and `experiments/_util.py:17 save_json` stamps
`_written_unix`, so a rerun dirties evidence even when every number reproduces. `--smoke` writes to
`results/smoke/` (gitignored); `.github/workflows/ci.yml` runs only `--smoke`.
**Mistake it prevents:** running the full target as a "does it still work" check and leaving, committing or
hand-reverting a diff in `results/`.
**Proof you hit it:** after a full run `git status --short results/` lists the `e0*.json` files and
`summary.json` (read from the code; the full run was not executed to check).
**Dated note 2026-10-16:** `--smoke` is safe only through `run_all.py`; a script run on its own
(`python experiments/e04_staleness_decay.py --smoke`) writes its smoke payload over the committed
`results/e04_staleness_decay.json` (reproduced in a clone by the image audit; the evidence-bytes test and
`git status` catch it; the root fix is lane C's).
**Fixed 2026-10-16 (lane C):** `main(smoke=True)` of every script calls `smoke_results()` from experiments/_util.py
first (a programmatic call is covered too), run_all.py calls it, and e06's partial files follow the same directory;
tests/test_experiments_smoke.py runs a script from a scratch copy and checks that the committed path stays untouched.
save_json writes LF on every OS since the same lane; e01 and e07 are stored CRLF today and flip when next regenerated.

## Local green is not CI green: torch is installed here, CI installs only `.[dev]` (export note 2026-10-13: the public root workflow installs `.[dev,analysis]`)

**Footgun:** torch, transformers, scipy, scikit-learn and psutil all import on this box;
`.github/workflows/ci.yml:11` runs `pip install -e ".[dev]"` (numpy, pytest and ruff). [export note 2026-10-13: the public repository's root workflow installs `.[dev,analysis]`] A module-level import of any
of them, or a torch test without a guard, passes here and fails on a clean clone: release audit 8542ef5 found
exactly that (3 failures in `tests/test_probes.py` on a fresh `.[dev]` clone). The guard idiom is a per-file
`_has("torch")` plus `@pytest.mark.skipif(not _has("torch"), ...)`; torch is imported inside function bodies.
**Mistake it prevents:** treating a green local run as proof for CI, or "simplifying" a lazy in-function
`import torch` to module level.
**Proof you hit it:** `python -c "import importlib.util as u; print(u.find_spec('torch') is not None)"` prints
`True`. Faking absence with `sys.modules['torch'] = None` makes `TestRealSubpackage::test_with_torch_smoke` fail
as an artifact (its skipif tests `'torch' not in sys.modules`); on the three torch-guard files that fake gave
101 passed, 27 skipped, 1 failed (that artifact). A clean `.[dev]` venv is the faithful check; none was run.

## Frozen instruments are byte-pinned, and later instruments import earlier ones

**Footgun:** `tools/run_fullfree_coarse_amended.py:195 assert_frozen_instrument()` hashes the raw bytes of
`tools/run_fullfree_coarse.py` and exits "... refusing" unless they equal `FROZEN_INSTRUMENT_SHA256`
(`5efa7063767b...`); `tests/test_prefetch_landing.py` pins `tools/run_prefetch_readouts.py` by an LF-normalised
sha (`8529532d4d78...`). Later instruments import earlier ones by bare module name (`from run_probes import ...`,
`import run_fullfree_coarse as fz`), so an edit to a shared instrument also changes its successors, and only
three instruments are sha-pinned in code or tests (two until 2026-10-01; see the update below). Any byte change counts, line endings included:
`core.autocrlf=true` is set system-wide here and 18 tracked `.py` files under tools/, src/, tests/ and
experiments/ are CRLF in the worktree (`git ls-files --eol`, 2026-10-01).
**Mistake it prevents:** reformatting, "tidying" or re-saving a frozen instrument (or running a formatter over
`tools/`) and finding out at the next registered run.
**Proof you hit it:** `git ls-files --eol tools/run_fullfree_coarse.py` should read `w/lf`, and
`python -c "import hashlib; print(hashlib.sha256(open('tools/run_fullfree_coarse.py','rb').read()).hexdigest()[:12])"`
should print `5efa7063767b`.
**Update 2026-10-01 (later):** a seventh attested instrument, `tools/run_prefetch_bigram.py` (the free-bigram twin of F-26), joined the closure at its landing. It pins its parent `run_prefetch_readouts.py` by LF-normalised sha in code (`:138`) and is itself pinned, also LF-normalised, by `tests/test_prefetch_bigram_landing.py:28`. The ruff list has ten tool entries beside `tools/cc`, and `tests/test_harness_doc_claims.py` derives them. The parent check runs at IMPORT, not at run time (`tools/run_prefetch_bigram.py:150` is a module-level call). In a scratch copy with one line appended to the parent, `pytest` stopped with `INTERNALERROR> SystemExit: ... is not the frozen instrument 8529532d4d78 — refusing`, exit code 3, and ran no tests (pytest 8.4.2, 2026-10-01). So a byte edit to `run_prefetch_readouts.py` aborts the whole suite, not just two files. The pin normalises CRLF, so a line-ending change alone does not fire it (read from the code). The CRLF count above is 20 since the OQ-19 draft's `tools/run_fullfree_oracle.py` and `tests/test_fullfree_oracle.py` were committed (both `i/lf w/crlf`). That draft attests its raw `__file__` bytes (`run_fullfree._sha`), so a freeze run from this worktree would cite CRLF bytes that an LF checkout does not reproduce: the EVID-1 break (inference from the code; nothing of OQ-19 has run).
**Update 2026-10-02:** an eighth attested instrument, `tools/run_prefetch_strat.py` (the stratified coverage read of the twin's margin), joined the closure at its landing. It pins the twin `run_prefetch_bigram.py` by LF-normalised sha in code (`:152`, asserted at import by `:164`) and is itself pinned by `tests/test_prefetch_strat_landing.py`; the twin's own import-time assertion covers the stage-1 parent. A byte edit to the stage-1 parent aborts the whole suite's collection (measured 2026-10-01: INTERNALERROR SystemExit, exit code 3, no tests run); an edit to the twin would do the same through this file's import-time assertion (an inference from the same mechanism, not measured). The ruff list has eleven tool entries beside `tools/cc`.
**Update 2026-10-03:** a ninth attested instrument, `tools/run_prefetch_r2.py` (the generalising free baseline, R2, the last rung on the twin's margin), joined the closure at its landing. It pins the stratified tool `run_prefetch_strat.py` by LF-normalised sha in code and asserts it at import (the chain's own assertions cover the twin and the stage-1 parent), and is itself pinned by `tests/test_prefetch_r2_landing.py`; a byte edit to any of its three parents aborts the suite's collection through the import-time assertions (the stage-1 case measured 2026-10-01, the others by the same mechanism). The ruff list has twelve tool entries beside `tools/cc`. This instrument also reads the Hugging Face cache (the pinned OLMoE snapshot, parsed with numpy only, no torch) and refuses to write under results/ unless the tensors it reads hash to its pinned sha, so a registered rerun needs that cache on the box; `--conclude-from`, the recompute and the landing test need only the state files (the landing test's one cache-dependent check skips, and says so, where the cache is absent). Bytes (read 2026-10-03): the tool is `i/lf w/lf` and attests its RAW bytes (`pr._sha(Path(__file__))`, a plain `read_bytes` sha, at `tools/run_prefetch_r2.py:1328`), so a registered rerun from a clean clone needs LF on disk (`core.autocrlf=false` on this box), while `tests/test_prefetch_r2_landing.py:46-51` normalises CRLF to LF before comparing and so passes on either checkout.

**Update 2026-10-04:** a tenth attested instrument, `tools/run_prefetch_horizon.py` (the horizon read at the R2
encoding, a K-6 lead-time datum; not a rung on the horizon-1 margin), joined the closure at its landing. It pins the
R2 tool `run_prefetch_r2.py` by LF-normalised sha in code (`assert_frozen_r2`, asserted at import; the chain's own
assertions cover the stratified tool, the twin and the stage-1 parent), carries `-text` in .gitattributes since its
freeze commit b41d3f3 (so every checkout writes the LF bytes it attests raw, the EVID-1 rule), and is pinned by
`tests/test_prefetch_horizon_landing.py` together with both state files' shas. The ruff list has thirteen tool entries
beside `tools/cc`, ten of them attested. A registered rerun needs the Hugging Face cache (the pinned OLMoE snapshot)
and the committed R2 payload and state file beside it (REPRODUCE reads them); `--conclude-from`, the recompute and the
landing test need only the committed files. The registered runs attest the memory-row commit after the freeze
(5e0e2a9), not the freeze commit itself: a session boundary fell between the freeze and the launch, and the instrument
records HEAD at the run, not the freeze.

**Update 2026-10-04 (later):** an eleventh attested instrument, `tools/run_noise_floor.py` (the seed-noise floor
readouts on the four committed vanilla verdict runs; a methods datum, not a rung), joined the closure at its landing.
It imports nothing under tools/ by design (tools/e6_gate.py, whose estimand it repeats, stays a live recompute
surface outside the closure), attests its raw bytes, carries `-text` since its freeze commit 906edfd, and is pinned by
`tests/test_noise_floor_landing.py` with both state files' shas. The ruff list has fourteen tool entries beside
`tools/cc`, eleven of them attested. A registered rerun needs only the committed summaries, metas and prompt files
(no cache, no GPU); `--conclude-from` re-derives every row from its stored prompt set and swap mask and refuses any
drift, including a meta or summary file on disk that is not the one the state file read.

**Update 2026-10-05:** a twelfth attested instrument, `tools/run_reader_lens.py` (the reader-and-lens re-test at S3:
the balanced-lens stage landed; the readers stages run through the same file), joined the closure at the lens
landing. It imports the frozen OQ-18 chain by bare name and asserts the amended instrument's sha at import, hides
CUDA at import, carries `-text` since its freeze commit b128fda, and is pinned by `tests/test_reader_lens_landing.py`
with both lens state files' shas. The ruff list has fifteen tool entries beside `tools/cc`, twelve of them attested.
Its `--conclude-from` binds every payload to its stage and role and to the tool's CURRENT bytes, so a dated
amendment of a reader is a new file that imports this one (the OQ-18 precedent), never an edit; a registered
readers run refuses unless both lens payloads verify with their riders passed (`--lens-payloads`).

**Update 2026-10-10:** a thirteenth attested instrument, `tools/run_seed_replay.py` (the OQ-20 seed replay
readouts on the committed verdict and seed-6 runs; a methods datum extending F-27, not a rung), joined the
closure at its landing. It imports the frozen `tools/run_noise_floor.py` by bare name (its loader, reliability
readout and constants) and nothing else under tools/ (tools/e6_gate.py stays outside the closure: the test
pins the leg equal to it instead), imports no torch, carries `-text` since its freeze commit b6d3701, and is
pinned by `tests/test_seed_replay_landing.py` with both state files' shas. The ruff list has sixteen tool
entries beside `tools/cc`, thirteen of them attested. Its registered runs refuse a dirty TRACKED tree and bind
every seed-6 meta to the bare launch commit (`--launch-commit`); `--conclude-from` re-derives every readout
from the summaries on disk against the sha-bound state header and refuses any drift; `--replay-check` is the
recomputable launch gate over the committed replay sidecars. Its frozen TEST file carried three assertions
written for the pre-run tree (no payload under results/, the new-seed runs missing) that failed by
construction once the evidence existed, one of them at the sidecars' own commit, which was made without
running the suite; amended at the landing by a dated line (the block's DATED AMENDMENT). Lesson: a frozen test
asserts the evidence's ABSENCE only inside a branch on its presence, and an evidence-only commit still runs
the frozen test file first.

**Update 2026-10-17:** a fourteenth attested instrument, `tools/run_reader_s1.py` (the S1 reader re-test's
word instrument: it issues the S1 word from the frozen per-reader labels; F-29), joined the closure at its
landing. It imports the frozen `tools/run_reader_lens.py` by bare name and asserts that file's raw-byte sha256
at import and again before any conclusion, imports nothing else under tools/ and no torch, carries `-text`
since its freeze commit 46a812f, and is pinned by `tests/test_reader_s1_landing.py` with both instruments'
shas, both state files' shas and the word payload's sha. The ruff list has seventeen tool entries beside
`tools/cc`, fourteen of them attested. Its registered word
(`--conclude ... --out results/real/readers_s1_word.json`) refuses a dirty TRACKED tree, an existing out, a
foreign data root, differing launch commits and any reader set but R-N, R-T, R-L in that order; the frozen
tool's own `--conclude-from` on an s1 pair yields the labels and no word.

**Update 2026-10-03 (later, EVID-1):** the nine attested instruments, the two OQ-18 registration docs and the four
prompt files now carry `-text` in `.gitattributes`, so every checkout writes their attested bytes: the seven LF-stored
instruments LF, and `tools/run_fullfree_coarse_amended.py` / `tools/run_oq18_rider_diag.py` CRLF (their blobs were
renormalised from LF to the CRLF bytes their payloads attest; no disk byte changed). The three closure members that
are imported but never cited (`run_fullfree.py`, `run_posthoc_topic.py`, `run_probes.py`) stay unpinned;
`run_posthoc_topic.py` and `run_probes.py` are still `i/lf w/crlf` here. A clean clone made with `core.autocrlf=true`
now writes `tools/run_prefetch_r2.py` LF (`i/lf w/lf attr/-text`, measured in a scratch clone of the fixed tree), so a
registered rerun from a clone no longer depends on that setting for the instrument file. A new instrument gets its
`-text` line in its freeze commit (docs/TASK_RECIPES.md), or check 4 of `tests/test_evidence_bytes.py` goes red once a
payload cites its sha.

## Evidence bytes under results/ are stored as cited (84 files renormalised 2026-10-01); a clean `git status` was not proof

**Footgun (fixed 2026-10-01 for results/):** `.gitattributes` sets `results/** -text` so evidence is stored byte-exact,
but 84 of 408 tracked `results/` files were CRLF on disk and LF in the index while `git status` read clean: the
index stat cache had not been refreshed (`results/e01_verifier_exactness.json`: 395 B in HEAD 5db262d, 404 B on
disk, reported unmodified). A fresh clone therefore wrote the LF bytes (verified in a scratch clone); that any stat
refresh would flip the 84 to modified is an inference from the mechanism, not observed. Three of the 84 are cited
by their on-disk sha256 in 28 tracked files under four keys (`freq_sha256` x7 for `gen_freq.json`; `glue_sha256`
x11 and `provenance/label_space_sha256/glue_k512.json` x8 for `glue_k512.json`; `glue_sha256` x1 and
`arms/phase0b_sharp_b3_cover90/glue_sha256` x1 for `glue_k512_cover90.json`); no LF sha is cited anywhere. The
other 81 are cited by nothing: for them the change records the bytes as regenerated on this Windows box rather than
restoring a cited state (the writers open files in text mode without `newline=`, so whichever platform wrote last
decides the line endings; `experiments/_util.py` `save_json` is one). Remedy taken: `git add --renormalize --
results/` stored the on-disk bytes (84 blobs changed by line endings only, recomputed old-vs-new after LF
normalisation by this session and twice by the critic; no disk byte and no number changed), and
`tests/test_evidence_bytes.py` pins results/ over TRACKED files only: (1) every tracked results file hashes
(`git hash-object --no-filters`) to its index blob, intent-to-add entries reported apart; (2) no tracked text file
cites the sha of a results file's other line-ending twin (a 64-hex scan, no provenance parser, a loose
anti-vacuity floor); (3) no results file is cited fewer times than at HEAD, so a regenerated, edited, renamed or
deleted cited file is named with both counts. In a scratch clone: the old HEAD fails (2) on 28 citations; the
planned state passes; `gen_freq.json` put back as its LF blob fails (2) on 7; after a scratch commit, one byte
appended to `glue_k512.json` fails (3) as `(glue_k512.json, 19, 0)` and deleting `gen_freq.json` as
`(gen_freq.json, 7, 0)`. SCOPE: results/ only. The same break exists for twelve sha-cited files under data/,
tools/ and docs/ (126 citations; all twelve stored LF: six cited by their CRLF disk bytes, which an LF checkout
breaks, and six cited by their LF bytes, which a checkout on this box converts to CRLF; none carries a `-text`
attribute; a clone made on this box fails three committed tests, `test_frozen_instrument_sha_is_pinned_and_true_on_disk`
and the `test_committed_*_payload_reproduces_its_verdict` tests of the OQ-18 rider diagnostic and positive
control): forward-ledger row EVID-1, its own lane.
**Mistake it prevents:** reading a clean `git status` as "bytes equal the commit"; re-saving or "normalising" line
endings under `results/`; counting gitignored `results/smoke/` payloads as evidence (a first version of the test
did, and failed on a fresh clone); reading "fixed" as covering data/ and tools/.
**Proof you hit it:** `git ls-files --eol results/ | grep -c "i/lf *w/crlf"` (the columns are padded; a
single-space pattern prints 0 either way) must print 0 and `python -m pytest -q tests/test_evidence_bytes.py` must
pass. Remedy split when it is red: a file test 1 names that nothing cites may be committed (churn); a cited file is
restored with `git checkout -- <file>` or re-cited by the registered landing that regenerated it, never by editing
the citation.

**Update 2026-10-03 (EVID-1 closed):** the same remedy now covers the fifteen sha-cited files outside `results/`: the
twelve of the ledger row plus `tools/run_prefetch_bigram.py`, `tools/run_prefetch_strat.py` and
`tools/run_prefetch_r2.py` (their citers normalise CRLF to LF, but their raw-bytes self-attestation on a rerun needs
the same pin). Each has a `<path> -text` line in `.gitattributes` and was stored as it is on disk by
`git add --renormalize` run in this worktree: six blobs changed from LF to CRLF by line endings only (the four
`data/prompts*.jsonl` files and the two frozen instruments `tools/run_fullfree_coarse_amended.py` and
`tools/run_oq18_rider_diag.py`, whose attested bytes ARE the CRLF bytes), nine unchanged, no disk byte changed (18 of
18 on-disk sha256 of the frozen closure and the cited files identical before and after). Measured in scratch clones of
41359bd before the fix, 186 citations of the fifteen in all: a `core.autocrlf=false` clone reproduced none of the 99
citations of the six CRLF-cited files while twelve citation-bearing test files all passed (test_evidence_bytes,
test_fullfree_coarse, test_fullfree_coarse_amended, test_fullfree_twin, test_harness_doc_claims, test_oq18_rider_diag,
test_oq18_rider_poscontrol, test_harvest and the four prefetch landing tests; no committed test covers those chains),
and a `core.autocrlf=true` clone reproduced none of the 87 raw-bytes citations of the nine LF-stored files and failed
exactly the three tests named above; after the fix both kinds of clone reproduce 186 of 186 and pass the same twelve
files (104 passed / 2 skipped in the rehearsal clones, before check 4 existed). Two traps measured on the way: a fresh
`core.autocrlf=true` clone writes EVERY text file CRLF, so renormalising there stores the nine LF-cited files wrong
(the fix runs only where the disk bytes are the cited bytes, this worktree); and here `git status` stayed clean after
the fifteen attribute lines were added (the stat cache again) until `git add --renormalize` re-read the six. A third,
found by the critic: an EXISTING `core.autocrlf=true` checkout that pulls this fix keeps its CRLF copies of the nine
LF-stored files (a new attribute line does not re-smudge an unchanged blob), `git status` stays clean, only 99 of 186
citations reproduce, and renormalising there stages the stale bytes as the nine's new blobs (check 4 then reads them
as an unreproducible chain); the remedy is to restore the index bytes to disk
(`python tools/landing_text.py eol --fix-lf` on the ten LF-pinned files, `tests/test_prefetch_r2.py` included, whose
stale copy check 4 cannot see; measured in a clone left in that state: 186 of 186 afterwards).
`tests/test_evidence_bytes.py` check 4 now derives the cited set from the full-sha256 citations and requires the
`-text` attribute in both the worktree's and the index's .gitattributes (this repository commits with
`git commit -- <paths>`, which takes the worktree copy), a citation of the DISK bytes themselves (a citation of
another line-ending form is reported as a stale checkout when the index still holds the cited bytes, with the eol
remedy, and as an unreproducible chain otherwise), index-blob equality with those bytes, and citation counts no lower
than HEAD's; red on this tree and both unfixed clones before the fix, green after, and seven negative controls in the
fixed clone (an attribute line removed, a byte appended to a cited file, a CRLF-twin citation planted, a CRLF-cited
data file re-saved as LF, an LF-cited instrument re-saved as CRLF, that stale state renormalised, and the pre-fix LF
blob staged under the CRLF disk copy of a data file) fire five of its six messages, each in the state it describes
(the planted twin and the renormalised stale state share one, the two re-saves another; the staged LF blob is the only
way to reach the renormalise remedy); the sixth, an untracked HAND_PINNED path, was added as a post-GO edit on
2026-10-04 and fired in the fixed clone only in the critic's re-runs after that GO, not among the seven. So "fixed"
now covers every file under `data/`, `tools/` and `docs/` that a tracked text file cites by a full sha256; a 12-hex
pin in prose is outside check 4's reach (docs/BLUEPRINT.md's R2 freeze record pins `tests/test_prefetch_r2.py` by its
raw LF bytes, so that file is pinned `-text` by hand and listed in check 4's HAND_PINNED, which holds it to the
attribute; GO-time shas quoted in round notes were measured on this box and are not chains). The pin works from this
commit forward only: a checkout of an earlier commit, a payload's recorded freeze commit included, still writes the
six by its own autocrlf, so read the record at this commit or later. The SCOPE sentence and the last mistake above are
history. Proof: `python -m pytest -q tests/test_evidence_bytes.py` (4 passed) and
`git ls-files --eol -- data/prompts.jsonl` reading `i/crlf w/crlf attr/-text`.

## Registered state files are gitignored by default

**Footgun:** `.gitignore:12` ignores `results/real/*.state.jsonl`; each registered run's state file is un-ignored
by its own `!results/real/<out>.json.state.jsonl` line (49 such lines = the 49 tracked state files after the R2 landing, 2026-10-03, counted over `results/real/`; 47 after the stratified-read landing, 2026-10-02; 45 after the free-bigram landing, 2026-10-01; 43 before). The payload
`.json` is not ignored, so `git add results/real/` or a glance at `git status` picks up the payload and silently
drops the state file, which is the recompute surface behind `--conclude-from`. Raw harvest `.npz` arrays and
`*.byproduct/` are ignored on purpose (bound by sha256 in committed metas); state files are the opposite case.
**Mistake it prevents:** landing a payload whose state file never reaches git.
**Proof you hit it:** `git check-ignore -v results/real/<new>.json.state.jsonl` prints
`.gitignore:12:results/real/*.state.jsonl`; once the negation line exists it prints nothing and exits 1.

## `-dirty` counts tracked files only: commit before a registered run

**Footgun:** instruments record `git_commit` as HEAD plus `-dirty` when any TRACKED file is modified
(`git status --porcelain --untracked-files=no`, `tools/run_fullfree_coarse.py:779-787`), and landing tests pin the
attestation: `tests/test_prefetch_landing.py:60` asserts the freeze commit and `git_status_tracked == []`. So an
uncommitted edit to any tracked file before a registered run, a docs tweak included (the edits that produced
this file would do it), stains the attestation; an untracked file does not, which is how the OQ-19 draft files sat untracked beside registered runs from
2026-09-07 until they were committed as an unfrozen draft on 2026-10-01; now that they are tracked, an
uncommitted edit to them stains an attestation like any other tracked file.
**Mistake it prevents:** launching a registered run with the instrument or a tracked doc uncommitted ("I will
commit after"), or assuming untracked files are checked.
**Proof you hit it:** `git status --porcelain --untracked-files=no` must print nothing before launch.
**Dated note 2026-10-16:** "tracked files only" is the rule of 12 of the 16 `tools/run_*.py` copies of the git
helper (measured at HEAD); 4 count untracked files too (`tools/run_error_predictor.py`, `tools/run_k3_arms.py`, `tools/run_posthoc_topic.py`, `tools/run_probes.py`; `probes_s1` fba1fb3-dirty
and `posthoc_topic_s1` 1a54fb7-dirty carry that meaning), as do the adapter `hf_specdec.py`, the harvesters and the
trainers (20 plain `git status --porcelain` call sites against 13 with `--untracked-files=no` under src/, tools/
and experiments/, the harness's tools/cc excluded), so a payload's `-dirty` has two meanings in this record; read the
instrument's own helper before interpreting a stamp.

## plan_guard denies source and evidence writes until a plan is open

**Footgun:** on this tree with no plan open (`cc/execution_plan.json` missing), `plan_guard._is_exempt` (checked by
calling it) denies Write/Edit/NotebookEdit on the gated paths. The one maintained list of gated and exempt
paths is CLAUDE.md's Harness section, witnessed by `tests/test_harness_doc_claims.py` (this entry used to carry
a second copy; a third lived nowhere else). A plan is open only while `cc/execution_plan.json` has
`status: in_progress` with at least one step: `python tools/cc/execution_plan.py create --task "..." --steps
"a|b"` opens one, and marking the last step passed sets `complete`, which closes the window again. The hook's
matcher is `Write|Edit|NotebookEdit` (`.claude/settings.json`), so Bash is not plan-gated; that is a gap, not a
licence (evidence under `results/` is still written only by its generating tool).
**Mistake it prevents:** assuming an earlier plan is still open, or routing an edit through a shell to dodge the
gate.
**Proof you hit it:** a denied write reads "No active execution plan (missing). Mutation requires
status='in_progress'..." (`tools/cc/hooks/_denial_reasons.py:532`; the prescribed route is `/implement-task`);
`python tools/cc/execution_plan.py status` shows the state.

## Work outside git is lost: session scratchpads and HANDOFF.md

**Footgun:** operator-supplied, 2026-10-01: session scratchpad directories are temporary and are lost between
sessions; the OQ-19 registration draft `scratchpad/oq19/patch_docs_oq19.py` (HANDOFF.md around line 207 calls it
"READY FOR FREEZE" since 09-06) was lost that way. Checked: no copy in tracked files, in the repo, or under the
claude temp tree. HANDOFF.md is itself gitignored (`.gitignore:81`, not tracked), 32 of its lines name
`scratchpad/...` paths (OQ-9, OQ-18, OQ-19 landing scripts), and registered text cites it, so a clone has neither.
**Mistake it prevents:** parking a draft, patch script or critic recompute in a scratchpad (or only in HANDOFF.md)
and expecting the next session to find it. Anything meant to survive must live in the repo.
**Proof you hit it:** `git grep -n patch_docs_oq19` prints nothing while `grep -n patch_docs_oq19 HANDOFF.md`
finds the pointer.
**Update 2026-10-01 (later session):** the draft was recoverable after all. The repo moved from `Desktop\sideband`
to `Desktop\Research\sideband`, so every earlier transcript and scratchpad lives under the old project slug
(`~/.claude/projects/c--Users-Michael-Desktop-sideband/` and the matching `Temp\claude\` folder); the earlier
"no copy under the claude temp tree" check searched only the new slug. Replaying the 2026-09-07 transcript's
Write/Edit calls for `scratchpad/oq19/*` (each tool_use line appears twice in the JSONL; dedupe by id) rebuilt
`blueprint_oq19.md` at 471 lines, the count the 09-14 session's own note recorded (that note and the rebuilt file
are both outside this tree, in the assistant's memory and the session scratchpad). The footgun stands: a scratchpad is Temp, and the rebuilt copy is in Temp again
until it is placed in the repo.
**Update 2026-10-01 (resolved):** the rebuilt draft and the three instrument files are committed as an
UNFROZEN draft (`docs/OQ19_ORACLE_CEILING_DRAFT.md`, DRAFT banners on the files); the Temp copy is no longer
the only one. The footgun stands for the next scratchpad.

## A session that commits and dies before `/handoff` leaves the harness continuity one session stale

**Footgun:** found 2026-10-01 (fifth session). The fourth session committed its work at 16:29 and ended before
`/handoff` ran (the session's cache went stale before the operator returned). `/handoff` is the only writer of
`cc/GOAL.md`, of the `ESPALIER_MEMORY.md` Session Log row and of the handoff leg of `cc/_working_summary.md`; the
summary's automatic rewrite fires only at compaction, and that session never compacted. So the next SessionStart
banner carried the THIRD session's GOAL snapshot (written 15:32) beside the FOURTH session's blueprint reasoning
(its critic verdicts and its pinned ledger decision), with nothing marking the two vintages. The banner labels
GOAL a snapshot, which is correct, but a reader trusting it would have believed the ledger work was still owed.
**Mistake it prevents:** treating the banner's "Still owed" and "Where we are" as current after a session that
did not hand off, and relying on `/handoff` alone to carry a session's state. What carried it this time was the
pre-harness belt and braces: the hand-written `HANDOFF.md` pointer (gitignored; written one minute after the
commit) and the assistant's own memory. After a run-heavy session with scratchpad-only drafts the loss would not
be small (see "Work outside git is lost" above).
**Proof you hit it:** `stat -c %Y cc/GOAL.md` prints a smaller number than `git log -1 --format=%ct HEAD` (the
goal snapshot predates the last commit). `python tools/cc/cognitive_blueprint.py chain` then shows a blueprint
newer than the snapshot with `reasoning>0`: that is the session that died.
**Practice:** run `/handoff` right after any landing commit when the session might not survive (a rate limit, a
long idle); it costs one memory row and a push, and the next session can run it again. A retroactive `/handoff`
from the next session works (done 2026-10-01; one Session Log row covers both sessions) but it writes from a
reconstruction, not from the dead session's context.

## Three footguns from the first generated landing (2026-10-02)

**Footgun:** found landing the stratified coverage read, whose status line, OUTCOME and pointers were generated from the
payloads by a script and applied by exact anchors. (1) `git checkout -- <file>` on this box (`core.autocrlf=true`)
re-materialises an LF-convention file (FINDINGS.md, README.md, CLAUDE.md, docs/CONVENTIONS.md, this file, pyproject.toml)
as CRLF; the index is unaffected, the per-file convention is not. (2) `textwrap` splits a phrase across a line break, so an
exact-string replacement that worked on the generator's output fails on the wrapped paragraph in the file. (3) A phrase
that a frozen registered text also carries ("where the free tables are blind" sits in the twin's 2026-10-01 OUTCOME and
status line) is edited by a global replace — registered text changed without a dated erratum.
**Mistake it prevents:** fixing generated text by patching the file (the generator and the record drift; the second
landing round found three sentence blockers, fixed by reverting the files, fixing the generator and re-applying);
leaving a revert's CRLF behind; and replacing a phrase file-wide when only your own region may change.
**Proof you hit it:** `file FINDINGS.md` reads "CRLF line terminators" after a `git checkout --` of it;
`git grep -c "free tables are blind" HEAD -- FINDINGS.md docs/BLUEPRINT.md` prints 1 and 1, and those counts must not move
at a landing; a replacement script exiting "0 occurrences" on a phrase you can see in the file is the wrap.
**Practice:** generate every landing number from the payloads (804 numbers checked by the critic across two rounds on
2026-10-02, 0 misquotes — every blocker was a sentence); apply by anchors with the file's own line ending; restore LF
after any revert; match wrapped phrases whitespace-tolerantly or re-wrap the paragraph; confine a shared phrase's
replacement to the region you wrote.
**Update 2026-10-03:** three more from the R2 landing, folded here from the held reflect candidate of that session:
(4) a paragraph-insertion rule keyed on a line that ends with a closing parenthesis splices the new paragraph into the
middle of a bullet whose closing parenthesis is not its last line (docs/WHY_THIS_DIES.md's K-6 STATUS on the R2
landing's first application; the landing critic caught it before the commit, so no committed file witnesses the
splice) — the rule is the blank line, never a character; (5) a grep for a phrase that textwrap has split across lines
misses it, so a check that "returns nothing" on wrapped prose proves nothing — collapse whitespace first; (6) quoting
a banned phrase to describe the defect it names trips the same grep on the describing text — describe, never quote.
Since 2026-10-03 `tools/landing_text.py` carries the mechanics (docs/TASK_RECIPES.md, "Landing texts"): `Doc` reads
and writes each file in its own line ending and refuses a mismatch against `expect` (footgun 1; pass `expect="lf"` on
every LF file, since a detected ending would follow the residue), `flex_replace_once` matches across a wrap (2, 5),
`region` confines a replacement and re-looks its bounds up on every call (3), `insert_after_paragraph` is the
blank-line rule and refuses a tight list of bullets, numbered items or table rows (4), `check` collapses whitespace
and case before it greps the diff's added lines (5, 6), and `eol --fix-lf` is the restore after a revert;
`tests/test_landing_text.py` pins each of these.

## A generator that types a reading word next to payload numbers repeats the error the record warns about

**Footgun:** found 2026-10-03 landing R2. The landing text was generated from the payloads, but one fragment of the
generator carried a hand-typed pair of reading words ("NOT-SHOWN / NOT-SHOWN") beside the two harvests' numbers. The
payloads read the pooled Q1 gate (`conclusion/labels/gate_eq_r2_all_reading`) NOT-SHOWN in
`results/real/prefetch_r2_s3.json` and SIGNAL in `results/real/prefetch_r2_s3_r.json` (both read 2026-10-03), so
the typed pair was wrong until the generator derived every reading from the payloads. A number check passes this class
(the numbers were right, the word beside them was not): the same blind spot as "a right number in the wrong cell" in
ESPALIER_MEMORY.md (2026-10-02 session row).
**Mistake it prevents:** typing a label or reading word in a landing template for a primary / replication pair.
**Proof you hit it:** in the landing generator (session scratch, not committed) `grep -n "(SIGNAL / SIGNAL\|(NOT-SHOWN /
NOT-SHOWN"` must print nothing: no literal reading word may sit beside a paired fragment.
**Update 2026-10-03:** `tools/landing_text.py` makes the derivation the default: `Pair.rdp(key)` returns the rule's
word on each side and emits the two-word form only where the sides differ, recording that pair so `check` flags its
absence from the applied text; the rule itself is the instrument's (`run_prefetch_readouts._reading`), passed in,
never re-implemented in the kit. `tests/test_landing_text.py` pins this case on the committed R2 payloads: the pooled
Q1 reading comes out NOT-SHOWN on the primary and SIGNAL on the replication, and that pair sits in F-26's third status
line.

## The Stop gate re-fires while background subagents are still running

**Footgun:** found 2026-10-03. Gates 2 and 3 of `tools/cc/hooks/stop_gate.py` read the relief records
`.espalier-state/docs_refreshed` and `.espalier-state/code_reviewed`; `subagent_stop` is their only writer (comment at
`stop_gate.py:69`), and it writes when the reviewer or docs subagent finishes. A turn that ends while those subagents
still run therefore meets the gate again on every attempt (lane-observed on the R2 landing, repeatedly; not re-measured
here). What held the turn open without re-triggering, per the lane: a Monitor waiting on `.espalier-state/code_reviewed`
instead of ending the turn.
**Mistake it prevents:** ending the turn to "wait" for a background reviewer, or writing the relief files by hand (the
hook owns them; defeating the gate that way is an inference, not tried).
**Proof you hit it:** the gate blocks while `ls -l .espalier-state/code_reviewed .espalier-state/docs_refreshed` shows
a record older than the subagent dispatch; it relieves once the subagent's record is written.

## Two espalier engines on one box (global pinned to the deploy commit 2026-10-01)

**Footgun:** `espalier init` was run by engine 0.8.0b2 (commit 2cb371b) from the dev clone's venv while the global
`python -m espalier` was 0.8.0b1, and the managed command bodies (`/smoke`, `/preflight`, `/integrity`) call
`python -m espalier`, i.e. the global one: it falsely reported build-plan drift and, had `fingerprint` or `upgrade`
been run through it, would have re-rendered the reports with the older renderer. On 2026-10-01 the global was
pinned to the deploy commit (`python -m pip install --upgrade
"git+https://github.com/Mike-Byrne-AI/espalier-harness.git@2cb371b2eb9937c22f53c4e719d94c1412ee7d9d"`), so both
report `espalier 0.8.0b2` and `doctor` reads pass through the pinned one. A `fingerprint` run through the venv
engine rendered a different hook list into `cc/LIVE_SURFACE.md` and made the pinned `doctor` warn (observed
2026-10-01), so generate `reports/` only with the pinned engine. The venv remains an editable install of the
clone at its lane HEAD (7 commits past the deploy commit on 2026-10-01, counted in that clone, outside this tree;
the deployed hooks still byte-match it, `selfcheck --contracts` check C-2). Eleven other harness deployments on
this box (a Desktop search, outside this tree) share the global engine and will see an upgrade offer from their
`doctor`.
**Mistake it prevents:** running `fingerprint`, `upgrade` or `init` through an engine that does not match the
seeds' first-line version marker; attributing an engine-backed result to the wrong engine.
**Proof you hit it:** `python -m espalier --version` and the clone venv's `-m espalier --version` disagree, or
`python -m espalier doctor .` reports `build_plan_changed: true` while the venv engine reports false.

## Managed harness files regenerate on re-init: the critic lane lives in three of them

**Footgun:** `.claude/commands/preflight.md`, `implement-task.md` and `implement-pack.md` carry
the `espalier:managed` marker comment on line 1 ("regenerated by `espalier init`; edit at your
own risk") and are listed in
`cc/PACK_MANIFEST.txt` as espalier-owned. On 2026-10-01 this repository added its own lane to
their reviewer steps (dispatch `sideband-critic` — recompute mode on `results/` or
`FINDINGS.md`, diff mode otherwise — when a diff touches
`results/`, `data/`, `experiments/`, `src/sideband/`, a `tools/*.py` outside `tools/cc/`, `tests/test_*_landing.py`, `FINDINGS.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md`, `docs/BLUEPRINT.md`, `docs/WHY_THIS_DIES.md`, `docs/REPORT.md`, `docs/FINDINGS_INDEX.md`, `docs/OQ*_*.md` or `README.md`) and a
`python tools/lint_findings.py` line to preflight step 1. `espalier init`,
`espalier upgrade --execute` and `espalier clean-generated --execute` rewrite or delete managed
files, so a re-init drops the lane; `tests/test_critic_lane.py` is what notices (the suite
must be green before any commit), while the `/critic` skill
(`.claude/skills/critic/SKILL.md`) and the agent file (`.claude/agents/sideband-critic.md`) are
unmanaged and survive. The agent's frontmatter also pins `model: opus`: an agent file without a
`model:` line inherits the parent session's model, and the operator's standing rule (2026-10-01)
is that no subagent runs on Fable without permission.
**Mistake it prevents:** re-initialising or upgrading the harness and assuming the critic still
gates findings; copying the `espalier:managed` marker line into the unmanaged skill or agent
file (`clean-generated` deletes any file carrying the marker and treats a file without it as
the user's whatever inventory lists it — `cleanup.py` in both installed engine versions);
dropping the `model:` line; running the three `.claude/workflows/*.js` scripts or `/reflect`,
whose `general-purpose` dispatches pass no model and inherit the parent session's, without
asking first.
**Proof you hit it:** `grep -c sideband-critic .claude/commands/preflight.md
.claude/commands/implement-task.md .claude/commands/implement-pack.md` prints a non-zero count
for each (3, 1 and 2 on 2026-10-01) and `python -m pytest -o pythonpath=src
tests/test_critic_lane.py -q` passes; after a re-init the count is 0 and the test is red —
re-apply the lane from the adoption commit (`git log --grep "adopt the sideband critic"`,
then `git show` its three command-body hunks); the decision row in ESPALIER_MEMORY.md
("Harness Decisions", 2026-10-01) holds only the surface list, not the lane text.

## `lint_findings.py` checks that cited paths exist and are tracked; it cannot see what it cannot parse

**Footgun:** since 2026-10-01 `tools/lint_findings.py` requires every cited path on a `- source:` line to exist AND
be tracked by git (`git ls-files`, i.e. the index: a staged file counts; separators normalised; a directory passes
when at least one tracked path sits beneath it, so a half-tracked harvest directory passes). It resolves the forms
FINDINGS.md actually uses: tokens starting with `results/`, `experiments/`, `tests/`, `docs/`, `src/`, `data/` or
`tools/`, brace shorthand (`prefetch_s3{,_r}.json`), wrapping parentheses, backticks, quotes or angle brackets, a
markdown link's target, a bare file name after a cited path (`results/real/x.json, x.json.state.jsonl`) resolved
against that path's directory then the repo root, and every `- source:` line of an entry. On 2026-10-01 that is
296 paths including all 48 state-file citations on source lines (27 of them were checked before). That closes
the hole where a registered run's state file, git-ignored until its own negation line lands (entry "Registered
state files are gitignored by default"), could be cited as evidence that never reached the repository. Without
git on PATH the lint falls back to existence and says "existence only" on its OK line; under CI it fails instead.
A token whose letter case differs from the tracked path is named as a case mismatch (a case-insensitive
filesystem lets it exist). An intent-to-add entry (`git add -N`) does not count as tracked. Still unchecked: a
bare name with a suffix outside its list, a citation in prose outside a `- source:` line (five state files are
cited that way in F-20 and F-25, all tracked on 2026-10-01), anything under a heading other than `## F-...`, and
free text (allowed on purpose).
**Mistake it prevents:** trusting `lint OK` as proof that every cited file is committed; citing a state file in a
form the lint cannot resolve and expecting it to notice; taking "committed" literally (the index is the oracle).
**Proof you hit it:** `lint_findings.lint_text("## F-99 - t\n- regime: r\n- source: results/real/prefetch_s3.json,
prefetch_s3.json.state.jsonl\n", Path("."), tracked={"results/real/prefetch_s3.json"})` returns the "not
committed evidence" error for the bare state file; `tools/run_nope.py` returns "does not exist" (both run
2026-10-01).

## The must-read files are too big to read whole

**Footgun:** CLAUDE.md says to read FINDINGS.md, DECISIONS.md and OPEN_QUESTIONS.md first, but FINDINGS.md is
213,953 bytes in 282 lines (longest line 12,940 bytes), OPEN_QUESTIONS.md 58,790 bytes, and docs/BLUEPRINT.md
412,467 bytes in 6,224 lines. Read the maps first: docs/FINDINGS_INDEX.md and docs/BLUEPRINT_INDEX.md (the block
title is the stable pointer, found by `grep -n`; its line numbers drift after dated insertions), then read by
range (`grep -n '^## F-' FINDINGS.md`).
**Mistake it prevents:** a whole-file read that floods or truncates the context; a line limit does not help
when the lines are 12 KB.
**Proof you hit it:** `wc -c FINDINGS.md docs/BLUEPRINT.md`.

## A registered GPU run's own untracked outputs stamp every later run `-dirty` (2026-10-09)

**Footgun:** `tools/run_k3_arms.py:382` stamps its meta with `git status --porcelain` WITHOUT
`--untracked-files=no` (the convention in "`-dirty` counts tracked files only" above is the opposite; the same bare
form sits in `src/sideband/real/bucketize_vocab.py:103`, `harvest_freq.py:122` and `hf_specdec.py:1050`). So the first
registered run's own untracked outputs make every later run in the same checkout read `-dirty`, which is how every
F-19 / F-21 meta does. Remedy chosen for OQ-20 (pre-run, not yet frozen): launch registered GPU jobs from a clean
clone of the launch commit (`git clone`, then `git checkout --detach <sha>`) with `--out` as an absolute path into
the working tree.
**Mistake it prevents:** reading `-dirty` on a meta as a tracked-file edit, or launching several registered runs
from the working tree and expecting a clean stamp on the second.
**Proof you hit it:** `grep -n "git status" tools/run_k3_arms.py` shows line 382 with no `--untracked-files=no`.

## A resumed `run_k3_arms.py` run keeps `resume: false` in its meta (2026-10-09)

**Footgun:** a resumed run keeps the ORIGINAL meta, so its `resume` argument stays False; it adds `resumed: true`
and a second entry in `run_ids` (`tools/run_k3_arms.py:415-417`). Reading `resume` reports every resumed run as
not resumed.
**Mistake it prevents:** attesting "ran uninterrupted" from `args.resume`.
**Proof you hit it:** `results/real/sanity_k512_bf16.meta.json` reads `"resume": false, "resumed": true`.

## Citing an instrument by on-disk sha256 reds `test_evidence_bytes.py` on an autocrlf checkout (2026-10-09)

**Footgun:** a registration that cites a file by its on-disk sha256 while the file is not pinned `-text`: on this box
(`core.autocrlf=true`) the disk copy is CRLF and the index blob LF, so the cited sha is the CRLF form and check 4 of
`tests/test_evidence_bytes.py` reds with the path under "lack the -text attribute". Adding `-text` afterwards does
not rescue the citation (the stored bytes change, the cited digest does not follow). Remedies: cite the git blob id
(`git rev-parse HEAD:<path>`, 40 hex; the test scans 64-hex only), or pin `-text` BEFORE citing, as the EVID-1 rule
in docs/TASK_RECIPES.md asks.
**Mistake it prevents:** a registration whose sha citation fails on a fresh clone.
**Proof you hit it:** the test's failure message lists the path under "lack the -text attribute".

## `;` after a failed proof lets the plan mark advance; chain with `&&` (2026-10-09)

**Footgun:** `<proof> ; python tools/cc/execution_plan.py mark N passed` marked a step passed after its proof
failed, and the step had to be re-marked running. Same family as the heredoc lesson in ESPALIER_MEMORY.md (a
failed first command does not stop the next one under `;`).
**Mistake it prevents:** a plan that records a step passed on a red proof.
**Proof you hit it:** `python tools/cc/execution_plan.py status` shows the step passed while the proof's exit code
was non-zero; write `<proof> && python tools/cc/execution_plan.py mark N passed`.

## The CP-RMRF speed bump fires on `rm -rf` of a scratch directory outside the repo (2026-10-09)

**Footgun:** `rm -rf <scratch dir>` trips CP-RMRF even when the directory is outside the repo, and the bump blocks
the whole Bash call (re-issue the identical command, as with CP-DISCARD).
**Mistake it prevents:** deleting a scratch clone to start a snapshot over. A `test ! -e <dir> && cp -r <src> <dir>`
snapshot avoids both the bump and the delete (it refuses if the target exists).
**Proof you hit it:** the Bash call is blocked with the CP-RMRF notice before anything runs.

## A fresh git repository built from exported files dropped a tracked file (2026-10-12)

**Footgun:** `.gitignore` carries the line `HANDOFF.md`. `git init` on this box writes `core.ignorecase true` into a new
repository's config, and under that setting the line also matches `.claude/commands/handoff.md`, so `git add -A` in the
fresh export repository skipped the file. The private repository sets `core.ignorecase` nowhere (git's default is then
false), matches case-sensitively, and has always tracked the file: `git check-ignore --no-index -v
.claude/commands/handoff.md` exits 1 there and 0 only with `-c core.ignorecase=true`. The export tool
wrote 804 files and the new repository tracked 803. Fix in `tools/export_public_cut.py`: `git add -A -f` (the tree [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
holds only what the tool wrote) plus a tracked-count equality check after the commit.
**Mistake it prevents:** a public repository silently missing a file the record cites.
**Proof you hit it:** `git -C <fresh repo> status --porcelain --ignored | grep '^!!'` names a file the source
repository tracks.

## A tool that withholds passages by exact anchor cannot ship in its own export (2026-10-12)

**Footgun:** `tools/export_public_cut.py` carries the withheld passages verbatim as its anchors, so shipping it would [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
ship them. It and `tests/test_export_public_cut.py` are on the withhold list for that reason (plan section 12); the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
named follow-up is a data/mechanism split, with the anchors in a withheld spec file.
**Mistake it prevents:** removing the tool from the withhold list to make the public repository self-contained.
**Proof you hit it:** a `grep -c` of any token of the tool's PRIVATE_NAMES list over tools/export_public_cut.py prints a [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
positive count in the private tree, and the export's private-name scan, which skips no file, would list the tool if it
were exported; `tests/test_export_public_cut.py` asserts the tool and its test are absent from the export. [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]

## `mv` of a Desktop folder fails with "Device or resource busy" (2026-10-12)

**Footgun:** a handle from another project's process pins the folder. Moving the folder's CONTENTS child by child
works and leaves an empty husk; the tool's foreign-entry check counts files only, because git commits no empty
directory, so the husk is harmless.
**Mistake it prevents:** retrying the folder `mv` or killing an unrelated process.
**Proof you hit it:** `mv <folder> <new>` prints "Device or resource busy" while `mv` of each child succeeds.

## The `[pending:` placeholder class vs its instances (2026-10-12)

**Footgun:** the marker has a class form (its name quoted in backticks, as CHANGELOG.md and ESPALIER_MEMORY.md do, or the
form with three dots inside the brackets) and an instance form (the prefix followed by the pending item's text,
whether or not the whole token sits in backticks). A scan on the bare prefix fires on the record talking about the
marker; a scan that exempts anything preceded by a backtick misses a real instance written in backticks, and the
export's own fills wrap the repository-URL token that way: measured 2026-10-13, seven instances hidden, 14 counted
where 21 were there. The tool exempts only a backtick right AFTER the colon (the quoted class name) and the three-dot
form; the commit log, where a committed message (c7f8999) quotes the class with its dots lost, sits outside the
pending and placeholder scans.
**Mistake it prevents:** a NO-GO verdict caused by prose that names the marker, and a GO that hides an instance in
backticks.
**Proof you hit it:** a backticked instance of the repository-URL token in an exported document is missing from the
verdict's pending list while the bare one in CITATION.cff is present.

## A test that exports `HEAD` cannot see a lane's uncommitted sources (2026-10-12)

**Footgun:** anchors, allowlist entries and `docs/public_cut/` sources that exist only in the worktree are invisible to [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
an export of `HEAD`. `tests/test_export_public_cut.py` exports a snapshot commit of the worktree (held on the scratch ref [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
`refs/tmp/export-snapshot` while the tests run, deleted at teardown) built
through a temporary index (`GIT_INDEX_FILE=<tmp>` with `read-tree HEAD`, `add -A`, `write-tree`,
`commit-tree -p HEAD`), the same temporary-index recipe ESPALIER_MEMORY.md's 2026-10-12 row records for a shared
worktree.
**Mistake it prevents:** a green real-tree test that tested the previous commit.
**Proof you hit it:** the real-tree test reports `allowlist-stale` hits for entries whose lines exist only in the worktree.

## A tracked-file edit during the full suite trips the frozen instruments' tree guard (2026-10-13)

**Footgun:** the registered instruments (`tools/run_prefetch_horizon.py` and the modules it imports) hash HEAD and the
tracked status when a run starts and refuse to write when either differs at the end. A `git checkout --` of a record
file, or a regenerate of one, while `pytest -q` is running makes the shift-rule guard test of
`tests/test_prefetch_horizon.py` fail with "the tree changed during the run (HEAD or the tracked status): refusing to
write", and the same test passes alone.
**Mistake it prevents:** reading that failure as a defect of the diff, or landing on a suite that ran over a moving tree.
**Proof you hit it:** one failure in `tests/test_prefetch_horizon.py` whose message names the tree, and a `git` or
regenerate command of yours timestamped inside the run (measured 2026-10-13: 1 failed and 719 passed with a revert
at 08:11 and 08:16 inside a run from 08:04 to 08:30; 720 passed on the untouched tree).

## EVID-1's `-text` pin for a withheld file: refused, oracle-breaking or name-hiding (2026-10-13)

**Footgun:** `tests/test_evidence_bytes.py` check 4 asks for a `-text` line in `.gitattributes` for every tracked file
outside results/ whose sha256 another tracked text file cites. The export tool's proof receipts
(`docs/public_cut/proofs/*.json`, from the tool revision that records `tool_sha256` and `allowlist_sha256`) cite the [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
tool's and the allowlist's digests, and both files are withheld from the public cut. Three ways to write the line, none
clean: a literal line naming either file puts a withheld name in `.gitattributes`, a format that takes no mention
marker, and `mark_mentions` refuses such a line at export (read from the tool's code: `.gitattributes` is outside its
COMMENT_SUFFIXES and PROSE_SUFFIXES); a `*` glob line that avoids the name passes the marker but puts the withheld
paths it matches into the tool's frozen set, which the real-tree test's oracle skips for `*` lines, so
`tests/test_export_public_cut.py` fails instead; a `?` or bracket glob passes both only because `frozen_set` and that [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
oracle read it as a literal while git honours it, so it hides the name from the mention guard rather than satisfying
it (and `frozen_set`'s blindness to `?` and `[]` globs is a gap of its own). The digests are checkout-independent
anyway: the tool folds CRLF to LF before hashing itself (`tool_digest()`), and the allowlist's digest is the pinned
commit's blob when the export ran without `--worktree-sources` (a worktree-sources export hashes the worktree copy).
**Mistake it prevents:** adding the line the test's message prescribes and breaking the export; hiding the name with a
`?` glob; or editing a receipt to drop the digests.
**Proof you hit it:** the full suite names `docs/public_cut/tone_allowlist.txt` and `tools/export_public_cut.py` as [withheld: docs/public_cut/, tools/export_public_cut.py not in this repository; see WITHHELD.md]
unpinned sha-cited files right after a receipt of the current tool is added under `docs/public_cut/proofs/` [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
(measured 2026-10-13: 1 failed, 719 passed, 5 skipped on the commit B tree before the amendment).
**Practice:** the test's `FOLDED_CITERS` exemption (2026-10-13) holds a file cited only by the receipts, by its
LF-folded sha256, to that fold against its index blob instead of the attribute, the route that relies on none of the
three. The HEAD-count check still applies while an edit to the tool or the allowlist is uncommitted; once committed,
the new digest has no citation at HEAD and the check passes without a new receipt, so a receipt describes the tool at
its export's source commit, not the tree's head. The lasting fix on the export side, a tool change that drops withheld
paths' attribute lines at export, is an eighth gap beside plan 12.5's seven; `frozen_set`'s `?` and `[]` blindness a
ninth.
**Update 2026-10-14 (call PC-4 of the 2026-10-14 public-cut decision batch, which docs/PUBLIC_CUT_PLAN.md section 13 [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
records once lane 2 lands; the receipt lock is gone):** the index-blob fold above is superseded, and the lock it left was check 4's HEAD-count, not the fold: an unstaged edit never changes the
index blob, but it leaves the file's new bytes cited nowhere where HEAD's were cited by the receipt, so the suite went
red until a receipt citing the new digest landed with the edit (both edit controls below failed on that assertion).
Now `tests/test_evidence_bytes.py` leaves the receipts out of check 4's citing set, at HEAD and now, and a fifth check
binds each receipt at the commit the receipt itself names: every tracked `.json` under `docs/public_cut/proofs/` must, [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
when HEAD holds it, equal HEAD's copy once CRLF is folded (a receipt is never edited); parse; name a 40-hex
`source_commit` that is an ancestor of HEAD (a dangling snapshot commit passes `cat-file -e` and fails this); and
carry, under every key that names a sha256, the digest of the file the key names at that commit, as stored or
LF-folded (`tool_sha256` the tool, `allowlist_sha256` the allowlist); no receipt tracked at HEAD may be missing from
the tree or from disk (PC-4 chose the binding at the source commit; the lane's two reviews added the never-edited
clause, the ancestor test and the key-and-path binding). A digest that names bytes no commit holds (an uncommitted
tool's, or the allowlist digest of a `--worktree-sources` export, which on this checkout is taken over CRLF worktree
bytes) is refused, with the remedy in its message: commit the sources, export from that commit, prove again; a receipt
with no digest under a sha256 key, such as the 2026-10-12 worktree-sources receipt, binds nothing and passes, and a
string under such a key that is not 64 lowercase hex is refused. The worktree and the index are not consulted for a
receipt-cited file, so an uncommitted edit to the tool or the allowlist no longer reds the suite. What the call gave
up: a committed edit to the tool or the allowlist no longer needs a receipt beside it, so the newest receipt may
describe an older tool, and nothing makes the next export's receipt follow. A second, non-receipt citer of the tool
or the allowlist puts the file back into check 4 with the `-text` remedy the tool refuses, so a record never quotes a
receipt's full digest. Measured in a scratch clone of b924585 with the new test copied in: a line appended to the
tool, and separately a comment appended to the allowlist, each uncommitted, left the new test green where HEAD's test
went red on its HEAD-count assertion; a tampered digest, a dangling commit, a commit of forty zeros, an edited verdict,
a deletion with `git rm` and a deletion on disk alone each went red on the new check, and a staged new receipt carrying
a 64-hex string in a stage tail stayed green while one carrying the empty blob's digest as `tool_sha256` went red (the
controls are listed in CHANGELOG.md's gates-lane entry). **Proof you hit the new check:** the failure message starts
"proof receipts that do not resolve at their own source commit" (or "proof receipts tracked at HEAD are gone from the
tree"); the remedy is in the message.
**Dated update 2026-10-15 (lane 2 of the public-cut batch, plan 13):** the eighth and ninth gaps are closed. A
`.gitattributes` line that NAMES a withheld file is dropped at export and listed in WITHHELD.md (a glob that merely
matches a withheld path stays, because it pins exported files too), and `frozen_set` takes the `text` attribute's
final state from `git check-attr` itself, run over the tree's attribute files in a scratch repository with the
system and global attribute files disabled (three reviews found a Python reader getting a new form wrong each
time, so there is no reader now; `tests/test_export_public_cut.py` pins the plumbing against an independent [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
`git check-attr` call per .gitattributes content). The
real-tree test's own oracle still reads literal `-text` lines only, so a glob pin for a sha-cited file still needs
that oracle extended by hand; the literal line is the clean route now, and the receipts need none (PC-4).
Dated 2026-10-17: the need is not limited to sha-cited files. The oracle asserts equality with the tool's
`frozen_set`, so ANY glob `-text` line needs it; the recovered critic folder's `docs/audits/critic-recovered/** -text`,
the second glob line after `results/** -text`, went in with the folder added to the oracle's prefix tuple
(`test_real_tree_frozen_files_are_byte_identical_and_anchors_matched`).

## A bit-exact gate crosses a BLAS thread-count boundary under numpy 2.4.6 (measured 2026-10-14)

**Footgun:** `tools/run_noise_floor.py`, a frozen instrument, runs `os.environ.setdefault(_var, "2")` for
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` at import (a value already set wins), and four
module-level imports pull it in during pytest's collection: `tests/test_noise_floor.py:21`,
`tests/test_noise_floor_landing.py:20`, and `tools/run_seed_replay.py:107` through `tests/test_seed_replay.py:31` and
`tests/test_seed_replay_landing.py:22`. By
then numpy's OpenBLAS is loaded in the pytest process at the box's logical-processor count (24 here, and numpy's OpenBLAS kept it
after the variables were set; `tests/test_balanced_groups.py`
imports numpy at module level and sorts first), so it keeps 24 threads while a child interpreter that inherits the
environment runs 2, as does a BLAS loaded later in-process such as scipy's (`threadpoolctl.threadpool_info()`, read
after the in-process freeze refused, showed `openblas 24` beside `openblas 2`, and `openblas 2` alone in the child the
instrumented test then spawned).
Under the OpenBLAS numpy 2.4.6 bundles (0.3.31.188.0, Haswell kernel on this box) the OQ-15 stage-I `delta_noise` on
the synthetic fixture differs between the two thread counts by 2.5e-15 (`0.007444130210472721` at 2 threads, the value
the subprocess committed; `0.0074441302104752485` at 24, the value the in-process recompute produced), which is the
whole of the binding-gate refusal plan 12.7 recorded; under numpy 2.3.5 (OpenBLAS 0.3.30) the two thread counts give
identical bits, `0.007444130210476211`, a third value, so the numpy wheel and the OpenBLAS build it bundles move the
bits as well. The same test passing alone is consistent with this (a single-test session imports no instrument before
the freeze), inferred, not read: no thread reading exists for that run. Three other in-process recompute families
(the reader-lens, noise-floor and seed-replay landing tests) passed under 2.4.6 on this box in the failure-mode
reviewer's scratch runs, one at 1 BLAS thread and one at 4, whose logs record counts (41 and 26 passed), not the test
sets or command lines, so the pairing rests on that reviewer's report; the prefetch landing family, which pins its
exact recompute to the instrument's own numpy, passed in one run under 2.3.5 there; the remaining synthetic exact
recomputes are unmeasured, as is the ubuntu runner's kernel until the CI rehearsal (call PC-8).
**Mistake it prevents:** reading the refusal as noise, as a numpy bug, or as a reason for a gate tolerance; asserting a
bit-exact match between a long-lived process and a fresh one; expecting a public bit-exact recompute to survive a
thread-count or wheel change under numpy 2.4.6 (the committed Stage-I summary the freeze binds to,
results/real/oq15_stage1.json, its meta and the frozen heads' meta results/real/oq15_head_weights.meta.json record
neither a numpy version nor a thread cap; docs/REPRODUCE.md section 4 carries the dated note).
**Proof you hit it:** `OPENBLAS_NUM_THREADS=2` and `=24` runs of `tools/train_outcome_head.py` on the same synthetic root
under numpy 2.4.6 disagree in `delta_noise` at the 15th decimal and agree under 2.3.5; inside a full pytest run
`threadpool_info()` shows two thread counts.
**Practice (call PC-5, 2026-10-14):** `tests/test_outcome_head.py` runs the stage-C freeze recompute in a fresh
interpreter, which inherits the same environment as the stage-I subprocess, so both sides see one thread count; the
gate stays bit-exact and no numpy pin is needed. A registered run whose field must be recomputed bit-exactly elsewhere
records in its payload's provenance the runtime thread count and kernel from `threadpoolctl.threadpool_info()` (the
`blas_info()` of `tools/run_prefetch_strat.py` records the environment variables and the build-time BLAS, which here
would have read 2 for a 24-thread computation), the thread-cap variables in force, and the numpy version with the
OpenBLAS build `np.show_runtime()` reports, and is rerun under the same numpy wheel and thread caps (the CPU kernel was
never varied here: every measurement read Haswell); the landing recipe in docs/TASK_RECIPES.md carries the line
(tests/test_prefetch_landing.py pins its exact recompute to the instrument's numpy version for a different reason, the
Generator stream). An unmeasured option: a conftest hook that removes the three variables after collection when they
were unset at session start.

## The pre-push seat-belt admits a `file:////` spelling of the private remote on POSIX (measured 2026-10-15)

**Footgun:** `tools/export_public_cut.py normalise_remote` and its shell twin `HOOK_NORM_SH` strip the scheme and fold [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
case, backslashes, ports and `.git`, but do not collapse a doubled leading slash: `file:////tmp/x/private origin.git`
normalises to `//tmp/x/private origin` while the forbidden entry is `/tmp/x/private origin`, so the hook admits the push and
git, which reads `//tmp/x` as `/tmp/x`, completes it. Found by lane A's Linux proof: the export fixture test's fourth
spelling, built as `"file:///" + <absolute path>`, is a four-slash URL on POSIX and pushed with exit 0 (round-2 log,
2026-10-15); on Windows the same expression builds `file:///C:/...`, which the normaliser folds correctly, so the gap
never showed here. The function's own gap list (ssh aliases, another host for a service, a trailing-dot host, the scp
absolute form, IPv6 with a port) does not name it, nor doubled inner slashes, dot segments or percent-encoding, which git
also resolves. A fix moves the tool's digest (its proof receipts bind it), so it is a lane of its own (a lane C
candidate); lane A built the test's URL with one leading slash and left the tool alone.
**Mistake it prevents:** reading "refuses in any spelling" in the export test as a boundary claim; it covers the spellings
listed, and the seat-belt is self-protection against an accidental push, not a defence against a deliberate one.
**Proof you hit it:** `python -c "import sys; sys.path.insert(0, 'tools'); import export_public_cut as ep; [withheld: export_public_cut not in this repository; see WITHHELD.md]
print(ep.normalise_remote('file:////tmp/x/private origin.git'))"` prints `//tmp/x/private origin`.

**Fixed 2026-10-16 (lane C of the image audit):** `normalise_remote` and `HOOK_NORM_SH` fold a doubled leading slash
right after the scheme strip (`^/{2,}` to `/`; sed `s#^///*#/#`), the parity test runs both sides over the four-slash
spellings, the pairs test pins the folded forms, and the fixture test pushes the four-slash spelling on POSIX again.
The proof command now prints `/tmp/x/private origin`. The tool's digest moved with the edit; under the PC-4 form of
`tests/test_evidence_bytes.py` (check 5) no receipt is needed beside it. Still not folded: doubled inner slashes, dot
segments, percent-encoding and the gaps the docstring lists.

## A full pytest run at default BLAS threads thrashes under the box's other load (measured 2026-10-16)

**Footgun:** numpy's OpenBLAS inside the pytest process keeps the box's logical-processor count (24 here; the thread-count
entry above) and its worker threads spin-wait, so a full `pytest -q` started while other sessions loaded the box (91-96%
busy) burned 48,000 CPU-seconds for 39% of the suite in 62 minutes, read as 305 CPU-s per 20 s of wall on the pytest
process while the dots stood still in tests/test_prefetch_r2.py; it was stopped. The same run with `OMP_NUM_THREADS=2`,
`OPENBLAS_NUM_THREADS=2` and `MKL_NUM_THREADS=2` set in the parent shell before pytest (the value the registered
instruments `setdefault` at import, so the faithful setting for their recompute gates) finished in 27:41 under the same
load, 726 passed / 5 skipped, the result the untouched-tree runs give at default threads.
**Mistake it prevents:** reading a silent hour as a hang and killing a healthy run; reading it as "the suite got slower"
and opening a performance lane; starting a full run at default threads while another session is working.
**Proof you hit it:** `powershell "(Get-Process -Id <pytest pid>).CPU"` read twice 20 s apart grows by far more than 20 s
while the progress line does not move, and the box's load is above 90%.

## A dated insertion above BLUEPRINT's blocks shifts every line citation into it (2026-10-16)

**Footgun:** docs/BLUEPRINT_INDEX.md's Line column and docs/METHOD.md's 26 "line N" citations point into
docs/BLUEPRINT.md by number, and the index itself says the numbers "stay valid until a dated insertion above them".
Lane B's front-matter note at line 3 plus nine notes above most blocks was that insertion: the index went from 32 of
47 rows correct at HEAD (it was already drifting) to 0 of 47, and METHOD's citations from about 19 correct to about 5,
found by the failure-mode reviewer, not by any test. The fix regenerated the index's Line column by block title in
file order and re-mapped METHOD's numbers from HEAD's line text to the new line; `tests/test_record_claims.py` now
pins every index row's title to its stated line.
**Mistake it prevents:** landing a dated note above a block and leaving the two derived aids pointing at unrelated
text, which a public reader following the reading-order index meets first.
**Proof you hit it:** `python -m pytest tests/test_record_claims.py -q` fails on
`test_blueprint_index_rows_sit_on_their_stated_lines`; regenerate by title (the lane's script pattern: walk the file
once, match each row's title after the previous match) and re-map METHOD by HEAD line text.

## Typed counts and typed comparatives in a lane about stale counts (2026-10-16)

**Footgun:** lane B's first draft, whose subject was stale counts, typed six of its own: "fourteen files" (twelve),
"six of the eight" helper copies (12 tracked-only and 4 untracked-counting in `tools/run_*.py`, 20 against 13 call
sites tree-wide), "two path kinds" (three), "the bonus token the verifier emits on every block" (only when a whole
block is accepted, `src/sideband/specdec.py`), "at most four emitted tokens" (five drafted, a stop at position 1
against an extension to six) and "S3 L2's largest upper" read off Mt rows instead of D rows. The generator's re-find
check passed every one of them because it tested whether the quoted string occurs in the JSON, not which row it came
from; the critic's recompute caught them all. A sibling trap in the same lane: anchoring a wrapped note by its first
sentence misses, because `textwrap` broke the sentence; anchor by the note's end marker instead. And a superlative
("the nearest committed bound to the floor") taken from one refuter's slice was wrong lane-wide: the critic found
F-28's RN at L1 replication upper +0.004951 against the audit's +0.0029.
**Mistake it prevents:** writing a count, a denominator, a comparative or a superlative into the record from memory or
from a reviewer's prose instead of deriving it in the generator from the measured quantity, with the command beside
it (docs/LESSONS.md entry 7).
**Proof you hit it:** the critic's recompute table shows a lane number beside its own with a nonzero discrepancy; the
cheap pre-check is to grep every typed numeral in the diff's `+` lines against the generator's measured values before
dispatching the reviewers.

## Check 6 of the evidence-bytes test reds on every new digest citation until the pins file is regenerated (2026-10-16)

**Footgun:** tests/evidence_pins.json records every cited sha256 that resolves to a tracked file. A landing that cites
a new digest (a payload's provenance, a test pin, a doc quoting one) reds check 6 of tests/test_evidence_bytes.py with
a message naming `python tools/evidence_pins.py --write`; a landing that regenerates a cited file reds it with an
`unresolved` row, and `--write` refuses that case unless each digest is named with `--accept`, so a hand-edit cannot
be re-baselined by habit. The pins file is itself a citer for checks 2 to 4 (it quotes every digest), so after a
legitimate regeneration check 3 reads one citation short until the file is rewritten. docs/TASK_RECIPES.md carries
the step beside the EVID-1 `-text` rule.
**Mistake it prevents:** rewriting the pins over changed evidence bytes; reading check 6's red as a defect in the test.
**Proof you hit it:** `python tools/evidence_pins.py` prints a nonzero `new`, `unresolved`, `uncited` or `moved` count.

## A handoff's date stamp is not today's date: date a registration from the box (2026-10-16)

**Footgun:** cc/GOAL.md (gitignored, `.gitignore:120`; rewritten by `/handoff`) opened the S1 reader re-test session
stamped `_Updated: 2026-10-17` while the box clock and the prompt hook's "Today's date" line read 2026-10-16. The
file's own mtime is 2026-10-16 06:57 -0400 and the three commits it logs (5d1598c, ff0aa4b, f692032) were made 06:54
to 06:58 -0400 on the 16th, still the 16th in UTC, so the stamp is not a timezone reading (probable, not verified:
it carried the overnight session's own sense of the date). The lane copied the stamp into its registration block,
the F-24 dated note, the CHANGELOG section, the `.gitattributes` comment, the rider folder's name and its scripts'
`pinned_on` strings, so the rider outputs, written on the 16th, carried a date later than their own file times. The
critic blocked it ("in a record whose first open doubt is registration order, evidence must not post-date its own
file times"); the fix re-dated the stamps, renamed the folder to `docs/audits/2026-10-16-f24-support/` and
regenerated its outputs. The same stamp is in a committed row: ESPALIER_MEMORY.md's thirty-third session row reads
2026-10-17, and f692032 committed it at 06:58 -0400 on the 16th.
**Mistake it prevents:** dating a registration, a pin, a folder or a finding note from a handoff or memory stamp. In
this record the order of registration and evidence is itself a claim, so a future-dated stamp is a defect, not a
typo.
**Proof you hit it:** take the date from `date +%F` and the hook's "Today's date" line, and compare it with
`git log -1 --format=%cd` (a stamp later than both is wrong); then, in Git Bash,
`git diff HEAD 2>/dev/null | grep -n "^+.*$(date -d tomorrow +%F)"` lists every added line carrying tomorrow's date,
each a future-dated stamp unless the line is about the stamp. Run it after a re-date too: on 2026-10-16 the first
re-date missed the instrument's own docstring (`tools/run_reader_s1.py:3`, the one stamp inside a file the word
payload will hash), which the critic's confirmation round caught; after that fix the command printed two lines (before this entry and its CONVENTIONS and memory rows added three more), both
in docs/BLUEPRINT.md and both about the stamp.

## A withhold-whole key's basename becomes a withheld name tree-wide, and a frozen file takes no marker (2026-10-17)

**Footgun:** `tools/export_public_cut.py` derives the withheld-name patterns from the `withhold_whole` keys: the path, [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
the basename and an underscored stem. Withholding the recovered critic folder's copy of `docs/REPORT.md` (plan 14.2
item 3) would have made every `REPORT.md` in the tree a withheld name, and the folder's `MANIFEST_WITHHELD.json`
the same for `MANIFEST_WITHHELD`; a key stays out of the patterns only through a `mention_exempt` entry. The lane
met the second half too: a file the export freezes (`-text`, emitted byte for byte) cannot carry the
`[withheld: ...]` marker, so any withheld name inside it is a `withheld-name` blocker, and a JSON field named
`public_cut` in the folder's frozen manifest was one (the bare `public_cut` is derived from the `docs/public_cut/` [withheld: docs/public_cut/, public_cut not in this repository; see WITHHELD.md]
key). Fourteen frozen recovered files needed residue entries (twelve quote the record's own pointer to
`docs/IDEAS.md` or `docs/FUTURE_IDEAS.md`, one is a landing diff whose hunk of the idea file the record holds [withheld: docs/FUTURE_IDEAS.md, docs/IDEAS.md not in this repository; see WITHHELD.md]
elsewhere, one holds a git status line naming the withheld export test; a fifteenth, a diff hunk with lines found
in no exported file, is withheld instead), and the manifests were split so that no digest of a withheld file
sits in a public one. Measured on 2026-10-17 by the tool's own `unmarked_names` over the folder before the landing
and by the real-tree scan test, which also found that an EMPTY withheld file registered the empty digest as a
withheld digest and flagged the OQ-20 driver log's zero-line pip freeze (fixed in the tool the same day).
**Mistake it prevents:** adding a `withhold_whole` key whose basename is a common word of the record without a
`mention_exempt` entry; pinning a folder `-text` without first scanning it for withheld names, private names and
placeholders; naming a field or a constant after a withheld folder; reading a `withheld-digest` hit on the empty
digest as a leak (since the fix an empty withheld file registers nothing; the folder withholds seven, six under
`2026-10-15-9dfaf64d/critic_ga1/` and `2026-10-13-b10c3ea1/critic1/err.txt`, by MANIFEST_WITHHELD.json's `bytes`);
exempting a folder key from mentions (a folder key derives only its full path, so nothing needs the exemption and
it would hide a real mention); keeping a recovered file whose lines exist in no exported file on the strength of
a residue reason written for another file.
**Proof you hit it:** `tests/test_export_public_cut.py::test_real_tree_scan_has_only_the_expected_hits` lists [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
`withheld-name` hits in a frozen file or `withheld-digest` hits on the empty digest; or
`python -c "import sys; sys.path.insert(0, 'tools'); import export_public_cut as ep; print(ep.SIDEBAND.mention_re().pattern)"` [withheld: export_public_cut not in this repository; see WITHHELD.md]
shows the basename in the pattern.

## An Edit anchored on a line inside a test function grafts that function's tail onto the inserted test (2026-10-18)

**Footgun:** the prove tests in `tests/test_export_public_cut.py` run several phases in one function, and a phase [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
can end on a line that reads like a function's last. In
`test_fixture_prove_reaches_a_verdict_and_stamps_only_an_exact_passed`, `mode["skip"] = False` is followed by
`calls.clear()` and the stamped run with its receipt checks. Plan 15.9's lane inserted its four new tests with an
Edit whose old text ended at that line, so Python read the old test's remaining indented lines as the body of the
last inserted test: the old test lost its stamped-run assertions and the new one inherited them. The targeted run
caught it as a failure in the new test at the old test's assertion (15.9's account; the tail was moved back before
review). Nothing else signals it: the file parses, the collection count rises by the number of tests inserted, and
the truncated old test still passes (inference: had the tail passed in its new home, no run would have flagged
the loss).
**Mistake it prevents:** choosing an insertion point by a line's content instead of by the previous function's
last line; reading a clean collection and a green old test as proof that the new tests sit between functions.
**Proof you hit it:** compare each test's span before and after the edit,
`python -c "import ast; t=ast.parse(open('tests/test_export_public_cut.py',encoding='utf-8').read()); [print(f.name, f.lineno, f.end_lineno) for f in t.body if isinstance(f, ast.FunctionDef)]"`, [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
against the same over `git show HEAD:tests/test_export_public_cut.py`: an old test that shrank by more than the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
lines deliberately removed has lost its tail (the prove test above spans 56 lines at 57867dc, 65 after the
lane's added assertions and 73 after its hardening batch of 2026-10-19). Insert a new test immediately before the next top-level `def` line instead.

## `.espalier-state/` is one folder per checkout, shared by every session open in it (2026-10-19)

**Footgun:** the hooks keep their per-session state in `.espalier-state/` at the checkout root (`STATE_DIR` in
`tools/cc/hooks/_hook_utils.py`; gitignored): `write_count`, `tool_call_count`, `last_tool`, `session_started` and the
relief records `docs_refreshed` and `code_reviewed`. `session_start.py` rewrites `session_started` and, on a fresh
start (not a compact or resume), clears the counters. So two Claude Code sessions open on the same checkout share one
counter set: the later start zeroes the earlier session's counts, and every source-file Write or Edit (or MCP write call)
either session makes (reflect_trigger.py's `_is_source_file`: a path inside the checkout with a source-code extension such as `.py`,
outside tests/, .claude/, cc/, reports/ and, on an adopter tree, tools/cc/ and espalier/; a `.md` or a tests/ file never
counts) counts toward both sessions' Stop gates (`stop_gate.py` gates 2 and 3 block at `write_count >= 10` with no
relief record).
Observed 2026-10-18 (plan 15.9): the landing session's writes blocked the Stop of a parallel session that was reserving
the Zenodo DOI and wrote nothing to the repository.
**Mistake it prevents:** reading a Stop block in a session that made no repository write as a hook defect; trusting
either session's write count while two sessions share a checkout; writing the relief files by hand to get past it (the
hook owns them, as "The Stop gate re-fires while background subagents are still running" above says; the one
hand-written record both gates honour is the operator form, `agent` "operator" with a note of at least 20 characters,
a recorded judgement).
**Proof you hit it:** in a session that has made no source-file Write or Edit, `cat .espalier-state/write_count` prints a count
above zero, and `ls -l .espalier-state` shows `session_started` newer than this session's own start. There is no
per-session state folder; keeping one session per checkout during a landing is the mitigation (inference from the
mechanism, not measured).

## Bit-exact recompute gates hold on the registered box and failed off it: the first CI run refused three, and a synthetic zero moved (2026-10-19)

**Footgun:** three landing tests reproduce registered lens payloads byte for byte (the instrument's rider gate compares
`json.dumps` of the recomputed rider with the stored one, before labelling), and one synthetic prefetch fixture
asserted a share the instrument leaves None where the twin's fallback margin is exactly zero, an assertion a negative
margin failed (narrowed since). Every full run on this box, the export's proof venv on it (numpy 2.4.6, 2 threads) and,
by the lane's account, lane A's Linux container on it passed them, so the suite looked
portable. The public cut's first CI run (ubuntu-24.04, Python 3.12, numpy 2.5.4, scipy 1.18.1, scipy-openblas
0.3.34.106.0, 2 CPUs) refused the three lens-rider reproductions and read the twin's margin NEGATIVE -0.0011 (share
-416.67 against a bound of 0.5). Four Docker containers on this CPU passed all four: python:3.12 with the runner's
versions and, by the lane's account, no thread cap (its command line unlogged; inferred 24 threads); numpy 2.3.5 (the payloads') with scipy 1.17.1; the runner's versions
with the same OpenBLAS build at 2 threads on 2 pinned CPUs (Haswell kernels by threadpoolctl); and ubuntu:24.04 with
its apt Python 3.12.3 and glibc 2.39 under the same versions, build and threads. Not matched: the runner's CPython
build, its virtualisation, the full-suite context, and its CPU, which its log does not name. The runner's CPU and the
kernel OpenBLAS selects for it is the leading candidate; which operation moves is not measured.
**Mistake it prevents:** reading a runner refusal as a corrupted payload or a numpy regression; pinning numpy or a
thread count for a difference neither made on this CPU (a numpy pin also changes the bundled OpenBLAS build, measured on this box's Windows wheel; whether
either would move the runner's bits is unmeasured); loosening a gate that lives in a sha-attested instrument (the
attestation would break first). The honest forms are a named skip under `CI` with the measurement in its reason and a
REQUIRE override for the three gates, and the one synthetic assertion narrowed to a positive margin with a dated
amendment for the pinned test file (tests/README.md, "Fail, not skip", 2026-10-19); the proof on the registered box
keeps running the gates, and the release export's proof receipt, kept in the private record, is the witness that it
did (its pytest count expected at the first export's 724 passed, 35 skipped).
**Proof you hit it:** the CI log reads `SystemExit: lens_s3.json: the rider at L3_olmoe_balanced_v1 does not
recompute from the shuffled rows` while the same test passes on this box in a container: the ubuntu:24.04 run's
full command line is the second line of exp4_ubuntu2404_2threads.log, kept in the private record (`docker run --rm
--cpuset-cpus=0,1 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e MKL_NUM_THREADS=2 -v <export>:/export:ro -w /w
ubuntu:24.04 bash -c '...'`, the body installing git and python3, cloning /export, making a venv, installing
`.[dev,analysis]` and threadpoolctl, printing the versions and thread pools, then pytest on the four files' selected
tests: 13 passed in 32.08 s).

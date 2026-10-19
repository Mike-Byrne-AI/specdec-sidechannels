# TP-1 — Test-suite speed: measure, tier, parallelise, cache

## Status

- Kind: PACK
- Version target: none (test infrastructure and lane practice; no release label moves)
- Change type: cleanup (test runtime and lane wall-clock), with one dev-dependency
  addition and one conditional public-CI line
- Authored: 2026-10-15, from the measurements of the gates lane (lane 1 of the
  2026-10-14 public-cut decision batch; CHANGELOG.md, the gates-lane entry, uncommitted
  at authoring time)
- Drives through: `/implement-pack` (the plan gate covers pyproject.toml and the
  tests; task-packs/ is exempt)

## Motivation

The suite runs serially on a box with 24 logical processors, and the lanes that
land on it re-run it several times per landing. Measured on 2026-10-14/15 in the
gates lane (session logs, each the output of the command named; re-derive by
timing the command):

| What ran | Command | Measured |
|---|---|---|
| Full suite, serial, alone | `python -m pytest -q -p no:cacheprovider` | 1,800.15 s (721 passed, 5 skipped) |
| Full suite at preflight, alone | the same | 2,560.69 s |
| Full suite with two control sets running beside it | the same | 3,909.32 s |
| The five files that snapshot the worktree or read the documents | `python -m pytest tests/test_critic_lane.py tests/test_evidence_bytes.py tests/test_export_public_cut.py tests/test_tools_and_real.py tests/test_harness_doc_claims.py -q -p no:cacheprovider` | 327 to 451 s across six runs [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md] |
| The evidence and outcome-head files | `python -m pytest tests/test_evidence_bytes.py tests/test_outcome_head.py -q -p no:cacheprovider` | 37 to 39 s |
| tests/test_evidence_bytes.py alone | its file | 20 to 38 s, about forty-five runs in one lane |
| Fifteen control runs of that file in a scratch clone | `d4_controls_v2.sh` (session scratch) | 337 s |
| Two numpy 2.4.6 validation clones, run concurrently | the receipt's pytest command | about 4 h each; the 2.3.5 clone of the previous session, alone, 3,582 s |

The gates lane ran the full suite four times and the five-file set six times,
mostly to re-prove documentation edits. docs/SHARP_EDGES.md ("The full suite is
slow; run the targeted file first") recorded about 7 minutes at 583 collected tests
on 2026-10-01; `python -m pytest --collect-only -q -p no:cacheprovider | tail -1`
prints the current count (726 on 2026-10-15), and the growth since then is the
landing recomputes, the export tests and the evidence gate.

Structural facts (verified on the tree on 2026-10-15): pytest-xdist is not
installed (`python -c "import importlib.util as u; print(u.find_spec('xdist') is not None)"`
prints False); `[tool.pytest.ini_options]` in pyproject.toml declares `testpaths`
and `pythonpath` and no markers; the only marks in `tests/` are `parametrize` and
`skipif`; there is no `tests/conftest.py` (dated note 2026-10-15: there is one since lane A, a session fixture); the real-tree export in
tests/test_export_public_cut.py happens once per module (`tests/test_export_public_cut.py::real` [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
is module-scoped), so "export once per module" is already the case and that
file's time lies elsewhere, which Task 0 decides.

## Scope (in)

1. **Task 0 — measure, and try to kill the pack.** One serial `--durations=0`
   run on a clean tree; one scratch-venv parallel feasibility run, twice; the
   refuting results below end the pack or drop a lever.
2. **A quick tier by markers (1-A).** A `slow` marker registered in
   `pyproject.toml` and applied to the tests Task 0 ranks above a threshold it sets;
   `python -m pytest -m "not slow" -q` becomes the lane-proof recipe in
   docs/TASK_RECIPES.md, the full suite stays the landing proof at `/preflight`
   (its managed body already runs the whole suite).
3. **A parallel full run (2-A, 2-B).** pytest-xdist added to the `dev` extra of
   `pyproject.toml`;
   `python -m pytest -q -n auto --dist loadfile` as the full-suite recipe on this
   box, with any test Task 0 shows racing isolated in an `xdist_group` or marked
   serial; the thread-cap question measured, not assumed.
4. **Cached reads in `tests/test_evidence_bytes.py` (3-A).** The five checks share
   one read of the tracked files and one HEAD batch instead of five.
5. **`tests/test_export_public_cut.py` (4-A).** Whatever Task 0 shows: the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
   prescription is deferred to the measurement (see Implementation).
6. **The public workflow line (5-A), conditional.** `docs/public_cut/ci.yml`'s [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
   pytest line gains the parallel flags only if 2-B passed and the dev extra
   carries xdist; measured at the CI rehearsal (public-cut call PC-8), never
   before.
7. **Lane practice (6-A), documentation only.** `docs/TASK_RECIPES.md`: the quick
   tier for lane proofs; validation clones one at a time; after a critic GO,
   advisory edits earn the tracer and the five snapshot files, not another read;
   a one-line checklist for proof sentences (name the form the run was on and its
   log). `docs/SHARP_EDGES.md` and `CHANGELOG.md`: a dated update of the suite-time
   entry with Task 0's numbers, and the pack's entry.
8. **Red team (7-A)** on the marker and parallel changes, by the
   failure-mode reviewer.

## Scope (out)

- **Any change to a registered recompute** (fewer bootstrap draws, a smaller
  state file, a tolerance): those tests are the evidence (`results/*.state.jsonl`
  reproduce the labels; CLAUDE.md D-3, D-9). A `slow` mark may skip one in the
  quick tier; nothing may make one cheaper. Reason: the record's labels are
  recomputed from them.
- **The frozen instruments** (pyproject.toml `extend-exclude`, the sixteen
  `tools/run_*.py` and their imports) and `tools/export_public_cut.py` (lane 2 [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  of the decision batch owns it). Reason: byte-attested; lane ownership.
- **The managed command bodies** (`.claude/commands/*.md` with the line-1 marker):
  the quick-tier recipe is written into docs/TASK_RECIPES.md, which survives
  `espalier upgrade`; the bodies do not. Reason: regenerated on re-init.
- **The instruments' thread-cap `setdefault`** in `tools/run_noise_floor.py`
  (frozen) and the unmeasured conftest hook named in the thread-count entry.
  Reason: frozen; unmeasured.
- **The private workflow** (`.github/workflows/ci.yml`): Actions are off at the
  private remote by the push policy. Reason: it never runs.
- **GPU-marked tests** under `src/sideband/real/`: skipped in CI and here by
  their guards. Reason: not in the measured time.

## Task 0 — Verify

Two oracles, each with a refuting result and an exit. Both run on a clean tree
(`git status --porcelain` empty, or the lane's own seven files only) and nothing
else running on the box: the measured inflation from a concurrent run is the
whole reason this pack exists, so a measurement taken beside another run is not
one.

**0-A Where the time goes (serial).**

```bash
python -m pytest -q -p no:cacheprovider --durations=0 > durations_serial.log 2>&1; echo "EXIT: $?" >> durations_serial.log
python - <<'EOF'
import re
rows = []
for line in open("durations_serial.log", encoding="utf-8", errors="replace"):
    m = re.match(r"\s*([\d.]+)s\s+(call|setup|teardown)\s+(\S+)", line)
    if m:
        rows.append((float(m.group(1)), m.group(3)))
rows.sort(reverse=True)
total = sum(s for s, _ in rows)
top = rows[:30]
print("tests with a duration line:", len(rows), "sum", round(total, 1), "s")
print("top 30 sum", round(sum(s for s, _ in top), 1), "s =", round(100 * sum(s for s, _ in top) / total, 1), "% of the sum")
by_file = {}
for s, name in rows:
    by_file[name.split("::")[0]] = by_file.get(name.split("::")[0], 0) + s
for f, s in sorted(by_file.items(), key=lambda kv: -kv[1])[:12]:
    print(f"{s:8.1f} s  {f}")
EOF
```

- **Decides:** which tests and files carry the time, and whether the time is
  concentrated. The threshold for `slow` is set from this output (the smallest
  per-test duration such that the marked set carries at least half the sum).
- **Refuting result for the quick tier (sub-task 1):** the thirty slowest tests
  carry under 30 % of the sum. Then no marker set makes a quick tier that is
  minutes rather than tens of minutes; sub-task 1 is dropped and the pack
  continues with the parallel run alone.
- **Refuting result for the cache (sub-task 3):** tests/test_evidence_bytes.py's
  five tests sum to under 10 s in this run (the lane's 20 to 38 s were measured
  beside other runs, which this run is not). Then sub-task 3 is dropped.
- **Refuting result for 4-A:** tests/test_export_public_cut.py's sum is under [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  60 s, or its time sits in the module-scoped real export rather than the
  per-test demo repositories. Then 4-A has no prescription and is dropped, or
  becomes a `slow` mark on the real-tree trio under sub-task 1.

**0-B Parallel feasibility (scratch venv; nothing installed in the tree).**

```bash
# a scratch clone of the same commit and a scratch venv; the tree's own venv is not touched
git clone -q <this repo> <scratch>/clone && cd <scratch>/clone
python -m venv <scratch>/venv && <scratch>/venv/Scripts/python.exe -m pip install -q -e ".[dev,analysis]" pytest-xdist
<scratch>/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider > serial_scratch.log 2>&1; echo "EXIT: $?" >> serial_scratch.log
<scratch>/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -n auto --dist loadfile > par1.log 2>&1; echo "EXIT: $?" >> par1.log
<scratch>/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -n auto --dist loadfile > par2.log 2>&1; echo "EXIT: $?" >> par2.log
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 <scratch>/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -n auto --dist loadfile > par3_threads1.log 2>&1; echo "EXIT: $?" >> par3_threads1.log
tail -n 2 serial_scratch.log par1.log par2.log par3_threads1.log
```

- **Decides:** whether the suite passes under `loadfile` distribution twice with
  the serial run's pass and skip counts, how much wall-clock it saves, and
  whether capping BLAS threads to one per worker (the oversubscription fix, 24
  workers each at 24 OpenBLAS threads otherwise) changes any outcome under the
  box's numpy.
- **Refuting results:** a test red under `-n auto` in either parallel run that is
  green serially, whose cause is not a shared resource `loadfile` or an
  `xdist_group` can isolate (the one known shared resource is the ref
  `refs/tmp/export-snapshot`, confined to one file, which `loadfile` already
  keeps on one worker; the tree guard in tests/test_prefetch_horizon.py hashes
  HEAD and the tracked status, which no test changes) → **stop and re-raise**
  with the failing test and its message. A parallel wall-clock not under half
  the serial wall-clock → sub-tasks 2 and 5 are dropped; the pack continues
  with sub-tasks 1 and 3. A difference in any test's outcome between `par1` and
  `par3_threads1` → the thread cap is not adopted and the thread-count entry of
  docs/SHARP_EDGES.md gains the measurement; the parallel recipe runs uncapped.
- **Exit when both oracles refute every lever:** the pack is scrapped with the
  two logs attached to its Landing stanza; no edit is made.

**0-C Baseline the controls of the evidence test** (needed by 3-A's oracle):
re-run `d4_controls_v2.sh` from the gates lane's scratch against the current
tests/test_evidence_bytes.py, or re-create it from CHANGELOG.md's gates-lane
entry (the fifteen states and their expected exits), and keep its log. If the
scratch is gone, the entry is the specification.

## Relevant memory

Recent pattern, measured in the gates lane: two concurrent runs inflated each
other threefold (4 h against 1.3 h for a numpy 2.4.6 clone validation; 3,909 s
against 1,800 s for the suite beside two control sets), and the lane's reviews
spent more wall-clock than its tests (seven critic reads, about two hours, three
of them on sentences that mislabelled which form a run had proven). Both are
process, not code, and both belong to this pack's 6-A.

| Entry | Where |
|---|---|
| The full suite is slow; run the targeted file first | `docs/SHARP_EDGES.md` |
| A tracked-file edit during the full suite trips the frozen instruments' tree guard (2026-10-13) | `docs/SHARP_EDGES.md` |
| A test that exports `HEAD` cannot see a lane's uncommitted sources (2026-10-12) | `docs/SHARP_EDGES.md` |
| A bit-exact gate crosses a BLAS thread-count boundary under numpy 2.4.6 (measured 2026-10-14) | `docs/SHARP_EDGES.md` (lands with the gates lane) |
| Local green is not CI green: torch is installed here, CI installs only `.[dev]` | `docs/SHARP_EDGES.md` |
| Two espalier engines on one box (global pinned to the deploy commit 2026-10-01) | `docs/SHARP_EDGES.md` |

Resolved at authoring time by `python tools/cc/hooks/_recall.py "tracked-file edit during the full suite tree guard"`,
`... "export snapshot ref worktree test"` and `... "pytest durations slow marker tier"`;
re-run them rather than trusting this list if the pack has been sitting.

## Affected symbols

The `slow` marker is declared under Affected literals, not here: the bare word is
English throughout the tree and the symbol walk would draw every use of it. The
symbol walk's remaining hits outside Scope (in) are homonyms (`tools/landing_text.py`
has its own `_tracked`; a harness summary under `cc/` and this pack quote the test's
helpers by name); an executor accepts them with
`espalier scope-check task-packs/TP-1-test-suite-speed.md --accept-scope-gap "homonyms: tools/landing_text.py::_tracked is a different helper; cc/ summaries and the pack quote the test's helpers"`.

### Removed paths
- (none — nothing is removed; a `slow` mark skips a test in the quick tier and deletes nothing)

### Renamed symbols
- (none)

### Changed semantics
- `tests/test_evidence_bytes.py::_tracked` — one `git ls-files -z` per test → one per
  module, memoised (3-A)
- `tests/test_evidence_bytes.py::_blob_reader` — a cat-file batch per call → a
  module-level cache keyed by (prefix, path), filled once per prefix (3-A)
- `tests/test_evidence_bytes.py::_head_reader` — unchanged signature, served from the
  cache (3-A)

### Added paths/symbols
- `tests/test_evidence_bytes.py::_worktree_bytes` — the one place a tracked file's
  worktree bytes are read, memoised for the module (3-A)

## Affected literals

- `@pytest.mark.slow` — the mark 1-A applies to the tests Task 0 ranks (and
  `pytestmark = pytest.mark.slow` at module level where a whole file qualifies);
  registered in `pyproject.toml`'s `markers`. EXCLUDE: docs/, task-packs/, cc/,
  harvest/
- `"pytest>=8"` — the `dev` extra's pytest pin in pyproject.toml, which 2-A
  extends with `"pytest-xdist>=3"` beside it. EXCLUDE: docs/, CHANGELOG.md,
  task-packs/, harvest/
- `testpaths = ["tests"]` — the `[tool.pytest.ini_options]` block 1-A extends with
  a `markers` list. EXCLUDE: docs/, task-packs/, harvest/
- `- run: pytest -q` — the public workflow's test line in docs/public_cut/ci.yml [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  (5-A, conditional on 2-B). EXCLUDE: .github/workflows/ci.yml, docs/, task-packs/,
  harvest/

## Implementation

Every fix below is a shape, untested at authoring time; each names what refutes it.

**1-A The `slow` marker** *(fix shape, untested; refuted by Task 0-A's
quick-tier result, or if `-m "not slow"` still takes over the budget Task 0 sets)*

```toml target=pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
# rootdir-relative: a clone or worktree tests its own src/, not whichever
# checkout the global editable install points at (docs/SHARP_EDGES.md).
pythonpath = ["src"]
markers = [
    "slow: a test above the per-test threshold Task 0 of TP-1 set; skipped by the lane's quick tier (`-m \"not slow\"`), always run by /preflight",
]
```

The marked set is derived, not listed here: every test whose `--durations=0`
call time exceeds the threshold Task 0-A sets, applied as `@pytest.mark.slow`
on the test function (or `pytestmark = pytest.mark.slow` at module level when a
whole file qualifies, the landing-recompute files being the expected case). The
quick tier is `python -m pytest -m "not slow" -q -p no:cacheprovider`; its
wall-clock is a pass criterion.

**2-A pytest-xdist in the dev extra** *(fix shape, untested; refuted by Task
0-B's parallel result)*

```toml target=pyproject.toml
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-xdist>=3", "ruff>=0.15"]
```

**2-B The parallel recipe** *(fix shape; refuted by any outcome difference
between the two parallel runs of Task 0-B, or between serial and parallel)*:
`python -m pytest -q -p no:cacheprovider -n auto --dist loadfile`, written into
docs/TASK_RECIPES.md's landing recipe as the full-suite form on this box, with
the thread cap only if Task 0-B's `par3_threads1` matched `par1` outcome for
outcome. Any test Task 0-B shows racing gets `@pytest.mark.xdist_group("serial")`
and the recipe adds `--dist loadgroup`; the two known shared resources are
named in Task 0-B and expected not to race under `loadfile`.

**3-A Cached reads in the evidence test** *(fix shape, untested; refuted by
Task 0-A if the five tests' time is in git subprocesses rather than in reading
and hashing, which the per-test durations and a `--durations=0` on the file alone
after the change decide)*

```python target=tests/test_evidence_bytes.py
_WORKTREE: dict[str, bytes] = {}        # worktree bytes of a tracked file, read once per module
_TRACKED: list[str] | None = None       # one `git ls-files -z` per module
_BLOBS: dict[tuple[str, str], bytes] = {}   # (prefix, path) -> blob bytes, one cat-file batch per prefix


def _worktree_bytes(path: str) -> bytes:
    b = _WORKTREE.get(path)
    if b is None:
        b = _WORKTREE[path] = (ROOT / path).read_bytes()
    return b


def _tracked() -> list[str]:
    global _TRACKED
    if _TRACKED is None:
        _TRACKED = _z(_git("ls-files", "-z"))
    return _TRACKED
```

with every `(ROOT / p).read_bytes()` in the five tests replaced by `_worktree_bytes(p)` and
`_blob_reader` consulting `_BLOBS` before batching the paths it lacks. The
controls are the oracle: the fifteen states of Task 0-C must give the same
fifteen exits and the same assertion messages after the change (a cache that
survives a control's edit of the tree would be the refutation: each control
runs pytest afresh, so the module cache is per process, and a control that
edits a file between two tests of one process does not exist).

**4-A The export test file** *(no prescription at authoring time)*: Task 0-A
names where its time goes. If the per-test demo repositories dominate
(`tests/test_export_public_cut.py::make_repo` runs per test through the `demo` [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
fixture), the candidate is a module-scoped base repository cloned per test;
if the real-tree trio dominates, they take the `slow` mark; if the scan does,
nothing in this pack touches it (the tool is lane 2's). The pack records which.

**5-A The public workflow** *(conditional on 2-B; measured only at the PC-8
rehearsal)*:

```yaml target=docs/public_cut/ci.yml [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
      - run: pip install -e ".[dev,analysis]"
      - run: pytest -q -n auto --dist loadfile
      - run: python tools/lint_findings.py
```

Refuted if the rehearsal's run fails where the box's parallel run passed; the
line then reverts to `pytest -q` and the pack's Landing records the runner's
behaviour.

**6-A Lane practice** *(documentation)*: docs/TASK_RECIPES.md's landing recipe
gains four lines (the quick tier as the lane proof and the parallel full suite
as the landing proof; validation clones one at a time; after a critic GO,
advisory edits earn the tracer and the five snapshot files, not another read;
every proof sentence names the form the run was on and its log). docs/SHARP_EDGES.md's
suite-time entry gains a dated update with Task 0-A's numbers and the parallel
wall-clock.

## Pass criteria

- Task 0's two logs exist and are named in the Landing stanza; every lever kept
  is one Task 0 did not refute, and every lever dropped names the refuting line.
- No registered recompute test changes its draws, its inputs, its tolerance or
  its assertions; no test is deleted; no assertion anywhere is weakened. A
  `slow` mark is the only change a marked test receives.
- The serial full suite (`python -m pytest -q -p no:cacheprovider`) passes with
  the pass and skip counts the command prints before the pack, re-derived, not
  restated.
- If 2-B is kept: the parallel full suite passes twice on a clean tree with the
  serial run's pass and skip counts, and its wall-clock is under half the serial
  wall-clock measured in Task 0-A on the same box in the same session.
- If 1-A is kept: `python -m pytest -m "not slow" -q -p no:cacheprovider`
  passes and its wall-clock is under the budget Task 0-A set (stated in the
  Landing stanza with the threshold).
- If 3-A is kept: the fifteen control states of Task 0-C give the same exits
  and assertion messages as the baseline log, and the file's own `--durations=0`
  sum is lower than Task 0-A's by a stated amount.
- `/preflight`'s managed body still runs the whole suite (no edit to it); the
  quick tier appears only in docs/TASK_RECIPES.md.
- docs/public_cut/ci.yml changes only under 5-A's condition, and the export [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
  tests (`python -m pytest tests/test_export_public_cut.py -q -p no:cacheprovider`) [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  pass after it (the workflow is an export source the real-tree scan reads).
- Red team ran (7-A) and its findings are recorded in Landing, "none found"
  included.

## Files touched

- New: `task-packs/TP-1-test-suite-speed.md` (this pack),
  `task-packs/TP-1-test-suite-speed-RUNBOOK.md`.
- Modified: `pyproject.toml` (the `dev` extra; the pytest markers), the test
  files Task 0-A ranks (a `slow` mark each), `tests/test_evidence_bytes.py` (3-A),
  possibly `tests/test_export_public_cut.py` (4-A, measurement-dependent), [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  `docs/TASK_RECIPES.md`, `docs/SHARP_EDGES.md`, `CHANGELOG.md`, and
  `docs/public_cut/ci.yml` only under 5-A's condition. [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
- Deleted: none.
- Unmodified on purpose: the sixteen frozen `tools/run_*.py`, `tools/export_public_cut.py`, [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  `src/`, `results/`, the managed command bodies under `.claude/commands/`,
  `.github/workflows/ci.yml`.

## Sub-task ordering

1. **0-A, 0-B, 0-C** — measure (serial durations; parallel feasibility in a
   scratch venv; the controls baseline). Checkpoint: the three logs exist with
   `EXIT:` lines, and the refuting-result table of this pack is filled in
   (kept / dropped per lever). May end the pack.
2. **1-A** — the marker and the derived `slow` set. Checkpoint:
   `python -m pytest -m "not slow" -q -p no:cacheprovider` green within budget;
   `python -m pytest --co -q -m slow | tail -1` prints the marked count.
3. **3-A** — the cache. Checkpoint: the file's five tests green; the fifteen
   controls match the baseline; `--durations=0` on the file alone, before and
   after.
4. **2-A, 2-B** — xdist in the dev extra; the parallel recipe. Checkpoint: two
   parallel full runs green with the serial counts; wall-clock recorded.
5. **4-A** — the export file, by what Task 0-A showed. Checkpoint: the file
   green; its `--durations=0` sum before and after.
6. **6-A** — the practice lines and the dated sharp-edge update. Checkpoint:
   `python -m pytest tests/test_harness_doc_claims.py tests/test_critic_lane.py -q`
   green; `python tools/landing_text.py check <registry> --added docs/TASK_RECIPES.md docs/SHARP_EDGES.md CHANGELOG.md`
   at 0 findings.
7. **7-A** — red team: the failure-mode reviewer on the marker set and the
   parallel recipe (what a `slow`-skipped lane proof would miss; what a
   `loadfile` worker could share; what the thread cap changes). Findings land as
   one batch; the affected checkpoints re-run.
8. **5-A** — conditional, last, and only the line: measured at the PC-8
   rehearsal, not here.
9. **Land** — `/preflight` (the whole suite, serial or parallel as 2-B decided),
   `/commit`, `/handoff`; the Landing stanza stamped.

## Estimated effort

| Sub-task | Budget |
|---|---|
| 0-A serial durations run | 35 min wall-clock, unattended |
| 0-B parallel feasibility (clone, venv, four runs) | 1 h 30 min wall-clock, unattended |
| 0-C controls baseline | 10 min |
| 1-A marker and derived set | 30 min |
| 3-A cache and its controls | 45 min |
| 2-A, 2-B dev extra and recipe, two parallel runs | 30 min plus the two runs |
| 4-A export file (if prescribed) | 45 min |
| 6-A practice lines, sharp-edge update, changelog | 45 min |
| 7-A red team and its fix batch | 45 min |
| Land (preflight, commit, handoff) | the full suite once, plus 20 min |
| **Total** | about 5 h of which about 3 h is unattended runs |

## Landing

- State: DRAFT
- Commits:
- Suite:
- Earn-the-red: <3-A: a control state edited between tests of one process does not exist, so the red to earn is Task 0-C's fifteen exits reproduced; 1-A: `-m slow` collects a non-empty set and `-m "not slow"` excludes it; 2-B: a deliberately shared tmp path in a scratch test goes red under `-n 2` and green serially, proving the race detector works>
- Red-team: <lanes run, verdicts, what they changed; "none found" is a result>
- Reach: not a class pack; no Reach section claimed
- Date:

## Sharp-edge entry to add (if Task 0 or 0-B finds one)

If 0-B shows a race, its entry goes under docs/SHARP_EDGES.md in the standard
form (footgun, the mistake it prevents, the proof you hit it), naming the test
and the shared resource; the pack's 6-A carries it.

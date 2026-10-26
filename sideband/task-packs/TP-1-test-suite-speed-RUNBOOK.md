# TP-1 RUNBOOK — test-suite speed

Ordered commands for `task-packs/TP-1-test-suite-speed.md`. The blueprint is what a
reader evaluates; this is what a session executes. Every run writes a log with its
command line and exit code before any sentence quotes it. Nothing here runs beside
another pytest on the box.

## Pre-work

```bash
git status --porcelain            # empty, or the lane's own files only
git tag pre-tp1                   # rollback: git reset --hard pre-tp1 (never on a tree with others' uncommitted work)
python -m pytest --collect-only -q -p no:cacheprovider | tail -1   # the current count, for the Landing stanza
```

## Task 0 — measure (may end the pack)

0-A, serial, alone on the box (about 35 min):

```bash
S=<session scratchpad>/tp1 && mkdir -p "$S"
{ echo "CMD: python -m pytest -q -p no:cacheprovider --durations=0"; echo "HEAD: $(git rev-parse HEAD) dirty: $(git status --porcelain | wc -l)"; echo "NUMPY: $(python -c 'import numpy;print(numpy.__version__)')"; echo "WHEN: $(date -u +%FT%TZ)"; } > "$S/durations_serial.log"
python -m pytest -q -p no:cacheprovider --durations=0 >> "$S/durations_serial.log" 2>&1; echo "EXIT: $?" >> "$S/durations_serial.log"
python <the summariser of Task 0-A in the pack> "$S/durations_serial.log"   # top 30, per-file sums, the % of the sum
```

Read the refuting results of the pack's Task 0-A against the summary and record
each lever as kept or dropped in the pack (a dated line under Task 0).

0-B, parallel feasibility in a scratch clone and venv (about 1 h 30 min):

```bash
git clone -q "$(git rev-parse --show-toplevel)" "$S/clone" && python -m venv "$S/venv"
"$S/venv/Scripts/python.exe" -m pip install -q -e "$S/clone[dev,analysis]" pytest-xdist
cd "$S/clone"
for label in serial_scratch par1 par2 par3_threads1; do
  case $label in serial_scratch) FLAGS="";; par3_threads1) FLAGS="-n auto --dist loadfile"; export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1;; *) FLAGS="-n auto --dist loadfile";; esac
  { echo "CMD: python -m pytest -q -p no:cacheprovider $FLAGS"; echo "ENV: OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-unset}"; echo "WHEN: $(date -u +%FT%TZ)"; } > "$S/$label.log"
  "$S/venv/Scripts/python.exe" -m pytest -q -p no:cacheprovider $FLAGS >> "$S/$label.log" 2>&1; echo "EXIT: $?" >> "$S/$label.log"
  unset OPENBLAS_NUM_THREADS OMP_NUM_THREADS MKL_NUM_THREADS
done
tail -n 2 "$S"/serial_scratch.log "$S"/par1.log "$S"/par2.log "$S"/par3_threads1.log
```

Compare pass/skip counts and the FAILED lines across the four logs; apply the
pack's Task 0-B refuting results. A red under `-n auto` that is green serially and
is not a shared-resource race: **stop and re-raise**.

0-C, the controls baseline for 3-A:

```bash
bash <the gates lane's d4_controls_v2.sh, or its re-creation from CHANGELOG.md's gates-lane entry>
grep -c AS-EXPECTED <its controls.log>; grep -c UNEXPECTED <its controls.log> || true
```

## Lane entry

```bash
python tools/cc/execution_plan.py create --task "TP-1 test-suite speed: the levers Task 0 kept" --goal "lane proofs in minutes, the full suite once per landing, parallel where it is race-free" --not-doing "no registered recompute cheapened; frozen instruments, the export tool, managed command bodies and the private workflow untouched" --steps "1-A slow marker|3-A evidence-test cache|2-A/2-B xdist and the parallel recipe|4-A export file by measurement|6-A practice lines and sharp-edge update|7-A red team|5-A public workflow line (conditional)"
python tools/cc/execution_plan.py mark 0 running
```

## 1-A — the marker (checkpoint: quick tier green within budget)

```bash
# pyproject.toml: the markers list (the pack's 1-A fence); then the derived slow set
python - <<'EOF'
# from durations_serial.log: every test whose call time exceeds the threshold Task 0-A set -> its file and name
EOF
# apply @pytest.mark.slow / pytestmark per the derived list (a script file, exact anchors, the file's own line ending)
python -m pytest --co -q -p no:cacheprovider -m slow | tail -1
{ echo "CMD: python -m pytest -m \"not slow\" -q -p no:cacheprovider"; echo "WHEN: $(date -u +%FT%TZ)"; } > "$S/quick_tier.log"
python -m pytest -m "not slow" -q -p no:cacheprovider >> "$S/quick_tier.log" 2>&1; echo "EXIT: $?" >> "$S/quick_tier.log"
python tools/cc/execution_plan.py mark 0 passed
```

## 3-A — the cache (checkpoint: five tests green; controls match; durations before/after)

```bash
python tools/cc/execution_plan.py mark 1 running
python -m pytest tests/test_evidence_bytes.py -q -p no:cacheprovider --durations=0 > "$S/evidence_before.log" 2>&1
# apply the 3-A fence through a script file (CRLF on this checkout)
python -m pytest tests/test_evidence_bytes.py -q -p no:cacheprovider --durations=0 > "$S/evidence_after.log" 2>&1; echo "EXIT: $?" >> "$S/evidence_after.log"
bash <d4_controls_v2.sh>    # the fifteen states against the new file; compare with 0-C's log line by line
python tools/cc/execution_plan.py mark 1 passed
```

## 2-A / 2-B — xdist and the recipe (checkpoint: two parallel full runs green with the serial counts)

```bash
python tools/cc/execution_plan.py mark 2 running
# pyproject.toml dev extra (the pack's 2-A fence); python -m pip install -e ".[dev,analysis]"
# docs/TASK_RECIPES.md: the full-suite recipe line (the pack's 2-B)
for i in 1 2; do { echo "CMD: python -m pytest -q -p no:cacheprovider -n auto --dist loadfile"; echo "WHEN: $(date -u +%FT%TZ)"; } > "$S/par_tree_$i.log"; python -m pytest -q -p no:cacheprovider -n auto --dist loadfile >> "$S/par_tree_$i.log" 2>&1; echo "EXIT: $?" >> "$S/par_tree_$i.log"; done
tail -n 2 "$S"/par_tree_1.log "$S"/par_tree_2.log
python tools/cc/execution_plan.py mark 2 passed
```

## 4-A — the export file (only if Task 0-A prescribed something)

```bash
python tools/cc/execution_plan.py mark 3 running
python -m pytest tests/test_export_public_cut.py -q -p no:cacheprovider --durations=0 > "$S/export_before.log" 2>&1 [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
# the change Task 0-A named, through a script file
python -m pytest tests/test_export_public_cut.py -q -p no:cacheprovider --durations=0 > "$S/export_after.log" 2>&1; echo "EXIT: $?" >> "$S/export_after.log" [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
python tools/cc/execution_plan.py mark 3 passed
```

## 6-A — practice lines, sharp-edge update, changelog (checkpoint: doc tests and the tracer)

```bash
python tools/cc/execution_plan.py mark 4 running
# docs/TASK_RECIPES.md, docs/SHARP_EDGES.md, CHANGELOG.md through script files; a numbers registry from the Task 0 logs
python -m pytest tests/test_harness_doc_claims.py tests/test_critic_lane.py -q -p no:cacheprovider
python tools/landing_text.py check "$S/numbers.json" --added docs/TASK_RECIPES.md docs/SHARP_EDGES.md CHANGELOG.md pyproject.toml
python tools/cc/execution_plan.py mark 4 passed
```

## 7-A — red team (edits frozen until the report is in)

Dispatch the failure-mode reviewer (model named explicitly; never Fable) on the
diff with the pack's three questions: what a `slow`-skipped lane proof would miss;
what two `loadfile` workers could still share; what the thread cap changes. Land
the accepted findings as one batch; re-run the checkpoints of the sub-tasks the
batch touched; record the verdict in the pack's Landing stanza.

## 5-A — the public workflow line (conditional; never measured here)

Only if 2-B is kept: the one-line change in docs/public_cut/ci.yml; then [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
`python -m pytest tests/test_export_public_cut.py -q -p no:cacheprovider` (the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
real-tree scan reads the workflow). Its first run is the PC-8 rehearsal.

## Land

```bash
python tools/cc/execution_plan.py status     # expect: complete
python tools/cc/reflect_protocol.py
```

Then `/preflight` (the whole suite, the form 2-B decided), `/commit` (the pack's
files and the lane's, by name), `/handoff`; stamp the Landing stanza (State,
Commits, Suite from the preflight log, Earn-the-red, Red-team, Date).

Open a work session: validate environment, refresh state, choose a task pack, confirm baseline.

## What to do

Execute these in order, stopping if any hard failure occurs.

**1. Environment check.** Run:

```powershell
python tools/trellis_check_env.py
```

If it fails, stop and report the failing checks.

**2. Godfile freshness.** Run:

```powershell
python tools/trellis_extract_godfile.py --check
```

If stale, regenerate automatically:

```powershell
python tools/trellis_extract_godfile.py
```

Then read `.claude/GODFILE.md` end-to-end.

**3. Git state.** Run:

```powershell
git status
```

List uncommitted changes. Surface anything surprising before proceeding.

**4. Test baseline.** If a `tests/` directory exists, run:

```powershell
python -m pytest -q
```

If tests fail, stop. If no `tests/` directory exists, report `[WARN] tests: no tests/ directory yet` and continue.

**5. List active packs.** List only root-level active packs matching:

```text
task-packs/TP-*.md
```

Do not list files under `task-packs/examples/`, `task-packs/archive/`, `task-packs/completed/`, or `task-packs/done/` as active work.

**6. Read the selected pack.** If exactly one active pack exists, propose starting it. If multiple exist, ask which one. Once the user confirms, read the full pack and summarize only its Goal and sub-task names.

## What not to do

- Do not start a sub-task without explicit user confirmation.
- Do not skip the baseline check.
- Do not synthesize findings or decisions here.
- Do not treat example/archive/completed/done packs as active work.

## Output format

```text
[OK] env: N/M OK
[OK] godfile: fresh
[OK] git: clean
[OK] tests: N passed
[OK] active packs: <list>

Which would you like to work on?
```

Keep it tight. The user wants signal, not narration.

## End of session

When the selected pack is complete, use `/close` to verify, refresh compact state, move completed packs, and produce a handoff.

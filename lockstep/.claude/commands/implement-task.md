Implement one bounded Trellis task using an execution plan and targeted proof.

## Usage

```text
/implement-task <task>         focused mode
/implement-task --multi <task> coordinated multi-phase mode
/implement-task --resume       resume .claude/trellis_plan.json
```

Focused mode is for one localized change. Use `--multi` when the task touches three or more files, multiple subsystems, hooks, installer behavior, or command behavior.

## Focused mode

**1. Restate the task.** Identify expected files, expected tests, rollback path, and whether any stop condition is already visible.

**2. Present a short plan unless the user already explicitly authorized execution.** The plan must name the proof command.

**3. Create a one-step execution plan.** Run:

```powershell
python tools/trellis_plan.py create --task "<task description>" --steps "Focused implementation: <change>; files: <expected files>; proof: <targeted proof>; rollback: <rollback note>"
```

Use `--force` only when replacing an obsolete local plan intentionally.

**4. Implement the change.** Keep edits scoped to the stated files unless new evidence requires a scope update.

**5. Run targeted proof.** Prefer the narrowest meaningful command, for example:

```powershell
python -m pytest -q tests/test_<affected_area>.py
```

If no targeted test exists, add one or run the full suite.

**6. Mark the plan step.** On pass:

```powershell
python tools/trellis_plan.py mark 0 passed
```

On failure:

```powershell
python tools/trellis_plan.py mark 0 failed --note "<literal failure summary>"
```

**7. Record significant reasoning.** If the task produced durable reasoning:

```powershell
python tools/trellis_blueprint.py record --kind decision --description "..."
```

**8. Report changed files, proof, plan status, and next action.**

## Multi-phase mode

**1. Decompose the work.** Each phase must state files, proof, and rollback.

**2. Create a phase plan.** Run:

```powershell
python tools/trellis_plan.py create --task "<task description>" --steps "phase 1|phase 2|phase 3"
```

**3. Execute phase by phase.** For each phase:

```powershell
python tools/trellis_plan.py mark <index> running
```

Make the edits, run targeted proof, then mark `passed` or `failed`.

**4. Integration check.** After all phases pass, run:

```powershell
python -m pytest -q
python tools/trellis_reflect.py --check
```

**5. Record and report.** Record durable blueprint entries and summarize the final plan state.

## Resume

Run:

```powershell
python tools/trellis_plan.py status
python tools/trellis_plan.py next
```

Resume from the first running, pending, or blocked step. Do not restart from memory.

## Stop conditions

Stop and ask before continuing if:

- targeted proof fails,
- full proof fails,
- an acceptance condition cannot be verified,
- the task unexpectedly touches files outside the stated scope,
- a destructive or expensive command would be required,
- references or godfile freshness cannot be repaired,
- a task marker says `STOP`, `OPERATOR REQUIRED`, `DO NOT AUTO-EXECUTE`, or `MANUAL STEP`.

When stopping, report the step, literal failure output, and two or three concrete options.

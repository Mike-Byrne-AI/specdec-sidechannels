Resume a Trellis session from compact local state.

Use this at the beginning of a fresh Claude Code session when the user wants continuity but has not selected a task pack yet. `/pack` remains the stronger start command when active task selection and baseline testing are needed.

## What to do

**1. Start or load the cognitive blueprint.** Run:

```powershell
python tools/trellis_blueprint.py load
python tools/trellis_blueprint.py start
```

If an active blueprint already exists, keep it. Do not reset it unless the user asks.

**2. Check compact state.** Run:

```powershell
python tools/trellis_extract_godfile.py --check
```

If stale, regenerate:

```powershell
python tools/trellis_extract_godfile.py
```

Then read `.claude/GODFILE.md`.

**3. Read project memory only as needed.** Prefer the generated godfile first. Read source files when the work needs detail:

```text
trellis-docs/trellis-findings.md
trellis-docs/trellis-decisions.md
trellis-docs/trellis-runs.md
task-packs/TP-*.md
memory/*/README.md   # only when task-pack authoring, harness maintenance, OSS-release, or continuity context is relevant
```

**4. Check live state.** Run:

```powershell
git status
python tools/trellis_plan.py status
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
```

**5. Report in 6 lines max.** Use this shape:

```text
REPO:    <name>
SURFACE: <healthy | DEGRADED>
LAST:    <latest blueprint continuation or none>
BRANCH:  <branch plus clean/dirty>
STATUS:  <godfile, refs, plan state>
NEXT:    <first safe action>
```

## Stop conditions

Stop and ask before continuing if:

- godfile generation fails,
- reference checking fails,
- an existing execution plan is `failed` or `blocked`,
- git state includes unexpected large/generated files,
- the next action would run an expensive command.

## What not to do

- Do not relitigate previous blueprint decisions unless new evidence appears.
- Do not invent a task pack.
- Do not start implementation. Use `/implement-task` or `/implement-pack` for that.

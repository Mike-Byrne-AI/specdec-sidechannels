End a Trellis session cleanly and leave useful continuity for the next session.

Use `/handoff` when the session produced reasoning that should survive context compaction or when the next session needs a clear entry point. Use `/close` when you also need the full verification closeout checklist.

## What to do

**1. Capture durable reasoning.** Record only decisions, rejected alternatives, discovered patterns, unresolved risks, next-step constraints, pack results, or reflection findings. Do not record noise.

Examples:

```powershell
python tools/trellis_blueprint.py record --kind decision --description "chose X over Y because Z"
python tools/trellis_blueprint.py record --kind alternative_rejected --description "considered X; rejected because Y"
python tools/trellis_blueprint.py record --kind pattern_discovered --description "files in X follow pattern Y"
python tools/trellis_blueprint.py record --kind risk --description "Y remains unverified because Z"
python tools/trellis_blueprint.py record --kind next_step --description "next session should start with X"
```

If no active blueprint exists, start one once:

```powershell
python tools/trellis_blueprint.py start
```

**2. Update durable source files only when justified.** Use:

```text
trellis-docs/trellis-findings.md   empirical observations with evidence
trellis-docs/trellis-decisions.md  durable architecture choices
trellis-docs/trellis-runs.md  experiment or verification runs
memory/  stable Trellis-maintenance patterns only when they are public and reusable
task-packs/   task state and acceptance status
```

Do not duplicate session chatter into durable memory.

**3. Run lightweight continuity checks.** Run:

```powershell
python tools/trellis_refs.py
python tools/trellis_memory_lint.py
python tools/trellis_reflect.py --check
python tools/trellis_extract_godfile.py
python tools/trellis_extract_godfile.py --check
```

If a check fails, include the failure in the handoff summary instead of hiding it.

**4. Finalize the blueprint.** Run:

```powershell
python tools/trellis_blueprint.py finalize
```

This writes `.claude/blueprints/latest.json` for the next `/context-load` session.

**5. Emit the handoff summary.** Use this exact shape:

```text
SESSION SUMMARY
Repo: <name>
Branch: <branch and clean/dirty>
Changed: <files touched>
Proof: <green | red | not run>
Blueprint: <finalized | not finalized, reason>
Memory: <updated | not updated, reason>
Next: <smallest useful next step>
Risks: <remaining blockers or none>
```

## Stop conditions

Stop and ask before finalizing if:

- the user wants to review a decision before it becomes durable memory,
- references fail and you cannot repair them locally,
- reflect finds a cross-file inconsistency you cannot safely fix,
- a task pack says `STOP`, `OPERATOR REQUIRED`, `DO NOT AUTO-EXECUTE`, or `MANUAL STEP`,
- verification is red and the user has not approved a red handoff.

## What not to do

- Do not promote decision confidence silently.
- Do not create findings or decisions from weak observations.
- Do not edit `.claude/GODFILE.md` by hand.
- Do not turn the handoff into a long narrative.

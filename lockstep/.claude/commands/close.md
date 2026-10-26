
Close a Trellis work session: verify the repo, refresh compact state, record handoff notes, and move completed task packs out of the active queue.

## What to do

Execute these in order, stopping on hard failures unless the user explicitly asks for a partial closeout.

**1. Check git state.** Run:

```powershell
git status
```

Summarize changed files. Surface unexpected files before proceeding.

**2. Run targeted verification.** If the session changed a specific file or module, run the narrowest relevant test first. Then run the local reference check:

```powershell
python tools/trellis_refs.py
python tools/trellis_memory_lint.py
```

**3. Run the full local gate.** Run:

```powershell
python tools/trellis_repair_gate.py
```

If this is a project repo with expensive tests, ask the user before running expensive project-specific commands. Do not invent a heavy command.

**4. Refresh compact state.** Run:

```powershell
python tools/trellis_extract_godfile.py
python tools/trellis_extract_godfile.py --check
```

**5. Close the active task pack.** If the active pack's final acceptance is complete, move it to `task-packs/done/` and prepend:

```text
**Status**: COMPLETED YYYY-MM-DD by session <brief>
```

If incomplete, leave it active and add a short `**Status**: BLOCKED <reason>` or `**Status**: IN PROGRESS <next step>` line only if useful.

**6. Record durable memory.** If the work produced a durable empirical observation, append to `trellis-docs/trellis-findings.md`. If it locked in a durable architectural choice, append to `trellis-docs/trellis-decisions.md`. If it produced a reusable Trellis-maintenance pattern, update the relevant `memory/*/README.md`. Do not create memory entries just to look thorough.

**7. Produce or delegate the handoff.** If the session produced durable reasoning, use `/handoff` after this checklist. Keep the closeout compact:

```text
[OK] changed: <files>
[OK] verified: <commands and result>
[OK] godfile: fresh
[OK] refs: pass
[OK] active packs: <remaining count/list>

Handoff:
- Completed: <one line>
- Left open: <one line or none>
- Next: <one concrete step>
```

## What not to do

- Do not move an incomplete pack to `done/`.
- Do not edit `.claude/GODFILE.md` by hand.
- Do not promote decision confidence silently.
- Do not create findings or decisions from weak/session-only observations.
- Do not skip `/handoff` when the next session needs continuity.
- Do not add a long narrative handoff when a short one is enough.

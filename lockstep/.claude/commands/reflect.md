Run the Trellis reflection protocol after meaningful work.

Reflection is a phase change: stop generating, re-read what changed, and look for cross-artifact gaps before claiming the work is complete.

## What to do

**1. Get changed files.** Run:

```powershell
git status
```

If git is unavailable, list the files changed in this session from memory and tool use.

**2. Re-read changed files.** Include any related tests, command docs, task packs, or project memory files.

**3. Run deterministic checks.** Run:

```powershell
python tools/trellis_reflect.py --check
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
python tools/trellis_pack_lint.py
```

**4. Do the cognitive review.** Check:

- changed docs match changed code,
- command docs mention real scripts,
- task packs still reflect actual work,
- internal `memory/` notes remain public, procedural, and non-duplicative,
- terms are stable across files,
- early and late edits have the same quality bar,
- acceptance criteria are actually verified,
- any new finding/decision belongs in durable memory.

**5. Record durable reflection only when useful.** Example:

```powershell
python tools/trellis_blueprint.py record --kind reflection --description "Found X drift between Y and Z; fixed by ..."
```

## Output format

```text
REFLECT
Changed: <files>
Deterministic checks: <pass | fail>
Cross-file issues: <none | list>
Memory updates: <none | list>
Next fixes: <top 1-3>
```

## Stop conditions

Stop before declaring success if:

- deterministic reflection fails,
- a referenced file/script/task/finding/decision is missing,
- docs and code disagree about a command or behavior,
- acceptance criteria cannot be verified,
- fixing the issue would expand scope beyond the user request.

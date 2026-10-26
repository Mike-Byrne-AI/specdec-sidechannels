# Hooks

Structural enforcement layer for conventions documented in `CLAUDE.md`.

Hooks are wired in `.claude/settings.json`, the shared project settings file. Personal overrides belong in `.claude/settings.local.json`, which is ignored by git.

## What each hook does

| Hook | Event | Matcher | Behavior |
|---|---|---|---|
| `track_reads.py` | PreToolUse | Read | Records normalized read paths in `.claude/.session-state/<id>/reads.json`. Always exits 0. |
| `check_context_loaded.py` | PreToolUse | Edit/Write/str_replace | Blocks `src/` edits unless the real project-root `trellis-docs/trellis-findings.md` and `trellis-docs/trellis-decisions.md` were read this session. |
| `check_godfile_fresh.py` | PreToolUse | Edit/Write/str_replace | Blocks `src/` edits if `.claude/GODFILE.md` is missing or stale relative to FINDINGS, DECISIONS, RUNS, or active task packs. |
| `check_confidence_promotion.py` | PreToolUse | Edit/Write/str_replace | Blocks unaudited confidence promotions in root `trellis-docs/trellis-decisions.md`. |
| `flag_finding_citations.py` | PostToolUse | Edit/Write/str_replace | Detects finding IDs in changed source text and reminds the operator to verify. Never blocks. |

## Source truth

Hook modules import shared helpers from the hook file's own project root before honoring any `TRELLIS_PROJECT_ROOT` override. That keeps test/project-root overrides from shadowing the installed helper modules.

`tools/trellis_paths.py` is the shared source/path truth layer. It defines:

- project-root detection,
- active task-pack discovery,
- godfile source discovery,
- path normalization for hook state.

Do not duplicate those rules inside hooks.

## Bypasses

- Godfile bypass: include the literal string `GODFILE-BYPASS` in an Edit/Write/str_replace tool input. Use rarely and visibly.
- Confidence promotion bypass: include `USER-CONFIRMED` in the user request or diff. This is reserved for the user.
- All hooks bypass: temporarily set `disableAllHooks` in local settings or remove the hooks section while debugging. Do not treat this as normal workflow.

## Permission model

These hooks and permissions are not a sandbox. They reduce accidental drift and skipped process steps. They do not stop arbitrary code from doing what the operating system allows.

## Testing hooks manually

Each hook reads JSON from stdin.

PowerShell:

```powershell
'{"tool_name":"Read","tool_input":{"file_path":"trellis-docs/trellis-findings.md"},"session_id":"manual_test","cwd":"."}' | python .claude/hooks/track_reads.py
```

Exit codes:

- `0` = allow
- `2` = block and show stderr to Claude Code

## Performance

Hooks should stay fast. If a hook needs heavy analysis, move the heavy work to an explicit command instead of running it before every edit.

## Reference check

Hooks do not perform full repository reference validation. Run `python tools/trellis_refs.py` or `/close` to check stable references before handoff.

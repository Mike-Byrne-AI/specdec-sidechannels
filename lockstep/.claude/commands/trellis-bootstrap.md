Bootstrap Trellis into the host repo root safely.

Use this after installing Trellis into a host project. The installer leaves host-owned root docs alone; `/trellis-bootstrap` is the explicit permission step that integrates the two root files Claude Code actually needs.

## What to do

**1. Run the bootstrap script.**

```powershell
python tools/trellis_bootstrap.py
```

The script resolves four conditions:

1. Root `CLAUDE.md` exists and contains the Trellis orientation as a fenced block.
2. Root `.gitignore` contains the Trellis ignore snippet without duplicate lines.
3. `.claude/trellis_install_manifest.json` records the expected installed Trellis surface.
4. A cleanup advisory lists legacy Trellis files that are actually present.

**2. Require explicit permission for each mutation.**

When prompted, ask the user before typing `yes`. Do not approve a mutation silently. The only host-owned root files this command may change are:

```text
CLAUDE.md
.gitignore
```

The manifest is Trellis-owned state under `.claude/`.

**3. Verify after bootstrap.**

```powershell
python tools/trellis_repair_gate.py
```

If the gate fails, report the failing command and the smallest next fix.

## Idempotency expectations

A second run should report:

```text
CLAUDE.md already integrated
gitignore already merged
```

and should not rewrite those files.

## Stop conditions

Stop and ask before continuing if:

- the user does not approve a requested mutation,
- the CLAUDE template is missing,
- the gitignore snippet is missing,
- the cleanup advisory includes files the user wants to inspect before proceeding,
- `python tools/trellis_repair_gate.py` fails.

## What not to do

- Do not delete cleanup candidates.
- Do not move host docs.
- Do not overwrite host `CLAUDE.md` outside the Trellis fence.
- Do not create project-specific README, findings, decisions, or run content.
- Do not run implementation work; use `/context-load`, `/pack`, `/implement-task`, or `/implement-pack` after bootstrap.

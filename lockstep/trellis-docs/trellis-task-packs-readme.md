# Task packs

This directory holds work specifications for Claude Code. One pack equals one focused unit of work, usually sized to one session.

## Active pack location

Only root-level files matching this pattern are active work:

```text
task-packs/TP-N_descriptive_snake_case.md
```

Inactive packs live outside the active queue:

```text
task-packs/examples/
task-packs/archive/
task-packs/completed/
task-packs/done/
```

`task-packs/examples/TP-0_example.md` is a worked example. It must never be treated as active work.

## Naming convention

- `N` is the pack number, incremented monotonically.
- Sub-tasks inside a pack are named `Task N-A`, `Task N-B`, etc.
- When the pack number changes, the letter resets to A.

## Pack structure

Every pack should have these sections, in this order:

1. **Goal** — one paragraph stating what the pack achieves and why.
2. **Why this matters** — empirical or methodological motivation. Usually references a finding from `trellis-docs/trellis-findings.md`.
3. **Out of scope** — what the pack will not change.
4. **Files touched** — concrete list of files created/modified.
5. **Risk level** — low, medium, or high with one sentence explaining why.
6. **Dependencies** — prior packs, findings, decisions, or `None`.
7. **Proof gate** — concrete commands for `/implement-pack`.
8. **Sub-tasks** — numbered implementation phases.
9. **Final acceptance** — the contract for declaring the pack complete.
10. **Stop conditions** — cases that require asking before continuing.

See `../trellis-docs/trellis-task-pack-goldprint.md` and `examples/TP-0_goldprint_basic.md` for worked examples. Lint a pack with:

```powershell
python tools/trellis_pack_lint.py task-packs/TP-N_name.md
```

## Lifecycle

1. Pack lives as `task-packs/TP-N_*.md` while active.
2. Leave it in place while work is in progress.
3. When all acceptance criteria pass, move it to `task-packs/done/` or `task-packs/completed/` and prepend:

```text
**Status**: COMPLETED YYYY-MM-DD by session <brief>
```

4. If a pack is partially complete but stalled, add a `**Status**: BLOCKED <reason>` line and leave it in the active root queue.

## Freshness

Active task packs are godfile sources. Adding or changing a root-level active pack makes `.claude/GODFILE.md` stale until regenerated.

Examples, archives, and completed packs do not make the godfile stale.

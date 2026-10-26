# Session-continuity memory

Use this folder for durable lessons about what should survive between Trellis sessions and where that information belongs.

## Current patterns to preserve

- `.claude/GODFILE.md` is generated compact state from findings, decisions, runs, and active task packs. Regenerate it; never edit it by hand.
- `.claude/blueprints/*.json` is short session continuity. Use it for reasoning that should survive compaction but is not ready to become a finding, decision, run row, task pack, or memory note.
- `memory/` is for stable procedural patterns only. Add or change a note when a future maintainer would likely repeat the mistake without it.
- Do not preload every memory topic at session start. Read the topic folder that matches the work, such as task-pack authoring, harness maintenance, OSS release, or continuity.

## Update checklist

When changing Trellis memory, run:

```powershell
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
python tools/trellis_reflect.py --check
```

If a memory note cites an `F<N>`, `D-<N>`, or `TP-<N>` ID, that reference must resolve. If the note is only useful for the current session, record it in the blueprint instead of `memory/`.

## Drift to avoid

- Do not turn memory into a transcript, diary, todo list, cache, or output directory.
- Do not duplicate full command docs or task-pack examples in memory; link to the source file and keep only the durable lesson.
- Do not add topic folders for one-off notes. Fold nearby notes into an existing topic or leave them in the blueprint.

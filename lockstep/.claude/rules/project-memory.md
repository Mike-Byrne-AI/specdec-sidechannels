---
paths:
  - "memory/**/*.md"
  - "trellis-docs/trellis-findings.md"
  - "trellis-docs/trellis-decisions.md"
  - "trellis-docs/trellis-runs.md"
---
# Project-memory rules

- `trellis-docs/trellis-findings.md` is append-only. If a finding is invalidated, add a new finding instead of editing the old one.
- `trellis-docs/trellis-decisions.md` entries require `[imagined]`, `[probable]`, or `[verified]` confidence.
- Claude may propose confidence changes, but the user promotes confidence.
- `trellis-docs/trellis-runs.md` is for compact run comparison, not long narrative analysis.
- `memory/` is Trellis internal procedural memory. Use it only for stable maintainer knowledge, not findings, decisions, runs, task status, raw logs, secrets, private user data, or scratch notes.
- If `memory/.trellis-memory` is missing or is a symlink, treat root `memory/` as host-owned or invalid. Do not add Trellis notes there or assume Trellis reference checks apply to it unless the user explicitly opts in.
- Each `memory/` topic should live in a subfolder with a short `README.md`. Keep topic folders low-cardinality and public-release safe.
- Use stable IDs: `F<N>`, `D-<N>`, and `TP-<N>`.
- Run `python tools/trellis_memory_lint.py` after changing Trellis memory.
- Run `python tools/trellis_refs.py` after changing project memory references.

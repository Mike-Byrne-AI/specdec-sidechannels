---
paths:
  - "src/**/*"
---
# Source work rules

- Read `trellis-docs/trellis-findings.md` and `trellis-docs/trellis-decisions.md` before changing source files.
- Regenerate `.claude/GODFILE.md` if `python tools/trellis_extract_godfile.py --check` reports stale state.
- Keep source changes scoped to the active task pack.
- Add or update tests for behavioral changes.
- Cite empirical assumptions with `F<N>` only when the finding exists in `trellis-docs/trellis-findings.md`.
- If a cited finding might be state-dependent, run `python tools/trellis_verify_finding.py F<N> --checkpoint <path>` before treating the change as done.

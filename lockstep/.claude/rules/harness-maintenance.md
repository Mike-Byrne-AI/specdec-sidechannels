---
paths:
  - ".claude/**/*"
  - "memory/**/*"
  - "tools/trellis_*.py"
  - "tools/trellis_extract_godfile.py"
  - "install_trellis.py"
  - "trellis-docs/**/*"
---
# Harness-maintenance rules

- Keep Trellis small: no dashboards, daemons, databases, remote services, or broad orchestration.
- Hooks and local scripts must be deterministic, dependency-free, and fast.
- Hook imports must come from the hook file's own project root, not an environment-controlled path.
- Installer and bootstrap writes must skip symlinked destination files and parent directories rather than writing through them.
- Console output must be ASCII-only.
- Update `tools/trellis_inventory.py` whenever commands, rules, skills, agents, or hooks change.
- Update tests when changing hook behavior, generated-state behavior, settings, or installer behavior.
- Treat root `memory/` as Trellis-owned internal memory only when a regular, non-symlink `memory/.trellis-memory` exists; preserve the sentinel, installer guard, manifest guard, and lint checks that skip host-owned memory directories.
- Run `python tools/trellis_memory_lint.py` after changing memory docs or memory infrastructure.
- Finish with `python tools/trellis_repair_gate.py` before packaging a snapshot.

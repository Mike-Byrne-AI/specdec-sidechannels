# Harness-maintenance memory

Use this folder for stable maintenance conventions for the Trellis source repo and installed harness surface.

## Current patterns to preserve

- Keep Trellis lightweight: no dashboards, daemons, databases, remote policy services, broad orchestration, or auto-commit flows.
- Prefer small deterministic Python tools with no runtime dependencies beyond the standard library unless the project already requires them.
- Keep source-repository public files source-only. Host installs should not copy root `README.md`, `LICENSE`, CI files, root `CLAUDE.md`, or root `.gitignore`.
- Route root `CLAUDE.md` and `.gitignore` integration through `tools/trellis_bootstrap.py` so the operator chooses the mutation.
- When changing commands, hooks, rules, skills, or agents, update inventory expectations and tests in the same patch.
- When changing installed files, update the install-surface model, installer tests, bootstrap manifest behavior, and documentation together.
- When changing `memory/`, preserve the regular, non-symlink sentinel and run the memory linter so host-owned root memory directories remain untouched.
- Keep shared Claude settings narrow: do not auto-allow broad shell readers, git staging, package installation, or direct root `memory/**` writes.
- Installer and bootstrap changes must not write through symlinked destination files or parent directories.

## Local proof habit

For harness work, run the narrowest relevant tests first, then the local gate:

```powershell
python -m pytest -q
python tools/trellis_memory_lint.py
python tools/trellis_repair_gate.py
```

For release-candidate packaging, also run:

```powershell
python tools/trellis_oss_release_gate.py
```

## Drift signals

Treat these as signs that a change needs reflection before shipping:

- docs describe a command that does not exist,
- command docs and tool behavior disagree,
- installer expected files and bootstrap manifest diverge,
- bootstrap manifest claims files from an unmarked host-owned `memory/` directory,
- shared settings allow a host-owned root write, broad shell reader, git staging, or package install directly,
- examples or completed packs appear as active work,
- generated state is edited by hand.

# OSS-release memory

Use this folder for public-release safety notes that are stable enough to remember across future Trellis revisions.

## Release posture

Trellis should remain explicit about being public preview / experimental alpha until maintainers choose a different policy. Permissions and hooks are workflow guardrails, not a sandbox or security boundary.

## Host-safety rules

- Default install must merge Trellis-owned assets without overwriting host-owned root docs.
- Root `CLAUDE.md` and root `.gitignore` remain opt-in bootstrap mutations.
- Existing Trellis-managed file collisions are skipped by default and backed up before overwrite when `--overwrite-trellis` is used.
- Generic host-owned directories are dangerous to merge into silently. For `memory/`, the installer copies Trellis internal memory only when the directory is absent or already marked with a regular, non-symlink `memory/.trellis-memory`.
- Trellis checks should also respect the sentinel. Unmarked root `memory/` is host-owned and must not be scanned as Trellis memory or recorded as expected install surface. This follows D-3.
- Installed Trellis self-tests live under `.claude/trellis-tests/`, not host root `tests/`.
- Installer and bootstrap writes skip symlinked destination files and symlinked parent directories instead of backing up or overwriting through them.
- Shared settings should not auto-allow broad shell readers, git staging, package installation, or direct root `memory/**` writes; make those local/operator choices.

## Public-content rules

- Assume every committed memory note, task pack example, and documentation page will be read by external users.
- Do not include private project history, internal-only names, secrets, credentials, or raw session transcripts.
- Prefer statements that can survive outside the original team context.
- Keep safety caveats visible but not alarmist: Trellis reduces workflow mistakes; it does not provide isolation.
- Run `python tools/trellis_memory_lint.py` before packaging when memory notes changed.

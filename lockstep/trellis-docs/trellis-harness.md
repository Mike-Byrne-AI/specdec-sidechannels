# Trellis harness

Trellis is lightweight Claude Code scaffolding for research-style projects. It combines bounded task packs, durable memory files, compact generated state, path-scoped rules, reusable skills, focused subagents, a cheap status line, and deterministic local checks.

## Core loop

1. Install Trellis into the host repo with `python install_trellis.py <target>`.
2. Run `/trellis-bootstrap` or `python tools/trellis_bootstrap.py --yes` once to integrate the root `CLAUDE.md` fenced block and merge `.gitignore` with explicit permission.
3. Start sessions with `/context-load` for continuity or `/pack` for task-pack selection.
4. Use `/implement-task` for bounded ad hoc work or `/implement-pack` for one task pack.
5. Track phases with `tools/trellis_plan.py`.
6. Run `/reflect` after meaningful edits.
7. Record findings, decisions, runs, and blueprint entries only when durable.
8. Use `/handoff` for continuity and `/close` for full verification closeout.

## What Trellis provides

- Root orientation through an explicit fenced block in `CLAUDE.md`.
- Source-truth discipline through `trellis-docs/trellis-findings.md`, `trellis-docs/trellis-decisions.md`, and `trellis-docs/trellis-runs.md`.
- Internal procedural memory through root `memory/` topic folders for durable maintainer patterns.
- Bounded work through root-level active `task-packs/TP-*.md`.
- Structural enforcement through hooks in `.claude/hooks/`.
- Small local verification through `tools/trellis_repair_gate.py` and `tools/trellis_oss_release_gate.py`.
- Lightweight work loops through blueprint, plan, pack lint, reflection, and handoff tools.

## What Trellis is not

Trellis is not a sandbox. Trellis is not malware containment, a production deployment guard, a remote policy system, a dashboard, a database, a daemon, or a multi-agent orchestration framework.

Trellis is accident-prevention friction and workflow memory. For hard isolation, use containers, VMs, filesystem permissions, or Claude Code sandboxing.

## Host-safe install model

The installer is safe to run against an existing non-empty project by default. It creates Trellis-owned files and directories, skips existing collisions, and never overwrites a target file unless the operator passes `--overwrite-trellis` or the deprecated compatibility alias `--force`.

Use dry-run first when inspecting a target:

```powershell
python install_trellis.py ../host-project --dry-run
```

Then install:

```powershell
python install_trellis.py ../host-project
```

To intentionally replace an existing Trellis-managed collision after a `.host-backup` file is created:

```powershell
python install_trellis.py ../host-project --overwrite-trellis
```

The installer excludes source-repository files and host-owned root docs, including:

```text
README.md
LICENSE
CONTRIBUTING.md
SECURITY.md
CODE_OF_CONDUCT.md
CHANGELOG.md
pyproject.toml
requirements-dev.txt
.github/
CLAUDE.md
.gitignore
docs/
runs/
```

`memory/` is Trellis-owned internal memory, but it uses a generic root name. To avoid polluting host-owned state, the installer copies `memory/` only when the target has no root `memory/` directory or when it already contains the regular, non-symlink Trellis sentinel `memory/.trellis-memory`. If an unmarked host `memory/` directory exists, Trellis skips its internal memory files rather than merging into it. Memory-aware checks use the same sentinel, so unmarked host memory is skipped by Trellis reference scanning, memory linting, and install-manifest expectations.

The installer also skips any destination file or parent directory that is a symlink, even during `--overwrite-trellis`, so it does not write through host symlinks into paths outside the intended target tree. Bootstrap applies the same rule to `CLAUDE.md`, `.gitignore`, and `.claude/trellis_install_manifest.json` writes.

The only normal host-owned root files Trellis may touch after install are:

```text
CLAUDE.md
.gitignore
```

Those mutations happen through `python tools/trellis_bootstrap.py --yes` and require explicit approval unless the operator chooses noninteractive `--yes`.

## Trellis-owned layout

```text
.claude/                 Claude Code commands, hooks, skills, agents, rules, settings
.claude/trellis-tests/   installed Trellis self-tests in host projects
tools/trellis_*.py       deterministic local Trellis tools
tools/trellis_templates/ bootstrap templates for CLAUDE.md and .gitignore
trellis-docs/            Trellis memory and harness docs
memory/                  Trellis internal procedural memory
task-packs/              active/inactive work specs
tests/                   source-repository Trellis tests only; not installed at host root
```

`tools/trellis_install_surface.py` is the authoritative source for installed files, source-only exclusions, and test relocation. Bootstrap writes `.claude/trellis_install_manifest.json` from that same surface model.

## Canonical commands

```powershell
python tools/trellis_bootstrap.py --yes
python tools/trellis_check_env.py
python tools/trellis_extract_godfile.py
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
python tools/trellis_pack_lint.py
python tools/trellis_reflect.py --check
python tools/trellis_inventory.py --check
python tools/trellis_repair_gate.py
```

Source contributors should also run:

```powershell
python -m compileall -q install_trellis.py tools .claude/hooks
python -m pytest -q
pytest -q
```

Release candidates should run the source checks above first, then the fresh-install release gate:

```powershell
python tools/trellis_oss_release_gate.py
```

The release gate performs non-pytest source preflight checks, installer dry-run, fresh install, bootstrap, install-manifest verification, and the installed repair gate.

## Memory and generated state

- `trellis-docs/trellis-findings.md` contains empirical findings with stable `F<N>` IDs.
- `trellis-docs/trellis-decisions.md` contains durable decisions with stable `D-<N>` IDs and confidence markers.
- `trellis-docs/trellis-runs.md` contains experiment and verification run rows.
- `memory/` contains short procedural notes for durable maintainer patterns such as task-pack authoring, harness maintenance, session continuity, and OSS-release safety. It is public content; do not store secrets, private data, raw transcripts, generated outputs, or scratch notes there.
- `tools/trellis_memory_lint.py` enforces the memory sentinel contract, shallow topic layout, UTF-8 Markdown, small-file limits, and basic secret-pattern checks.
- `.claude/GODFILE.md` is generated compact state. Never edit it by hand.
- Godfile freshness is content-based: `python tools/trellis_extract_godfile.py --check` renders the expected content and compares it to `.claude/GODFILE.md`, rather than trusting mtimes.
- `.claude/.session-state/` stores hook state under derived safe session keys; raw Claude session IDs are not used as path components.

## Task packs

Active packs are only root-level files matching:

```text
task-packs/TP-*.md
```

Examples, archived packs, completed packs, and done packs are inactive. `TP-0` is valid only for examples under `task-packs/examples/`; active root work starts at `TP-1`.

## Reference scanning

`tools/trellis_refs.py` strictly reads Trellis-owned memory docs and task packs as UTF-8. It scans `memory/**/*.md` only when `memory/.trellis-memory` is present. Host source files under `src/` are scanned only when they look like text; binary, generated, or non-UTF-8 source files are skipped rather than crashing the gate.

## Bootstrap idempotency

`CLAUDE.md` uses a fenced Trellis block. Running bootstrap again updates only that block, preserving host content below. `.gitignore` merge is line-deduped. Bootstrap never deletes cleanup candidates; it only reports them.

## Shared permissions

Shared `.claude/settings.json` does not directly allow editing or writing root `CLAUDE.md`, `.gitignore`, or root `memory/**`. It also avoids auto-allowing broad shell readers such as `cat`, `grep`, `rg`, and `find`, git staging, `git show`, or package installation. Bootstrap remains the reviewed path for root file integrations, and memory writes remain reviewed because a host may already own root `memory/`. Operators who want broader local access can opt in through `.claude/settings.local.json`; the example file documents that this is local-only.

Trellis permissions are workflow guardrails and accident-prevention friction. They are not a sandbox, malware containment, or a hard security boundary.

## Setup script portability

Archive extraction can drop executable bits. Prefer portable invocation:

```powershell
bash setup.sh
```

Most Trellis tools discover the project root through Trellis markers rather than assuming the current working directory.

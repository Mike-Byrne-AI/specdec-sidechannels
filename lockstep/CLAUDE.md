<!-- BEGIN TRELLIS BOOTSTRAP -->
# Trellis Claude orientation

This project uses Trellis, a lightweight Claude Code harness for research-style work. Trellis keeps Claude grounded in append-only findings, decisions, run history, bounded task packs, compact generated state, and small deterministic hooks.

If this file conflicts with the user's in-session instructions, the user's current instructions win.

## Fast path

If this is a freshly installed host repo, run `/trellis-bootstrap` first. Then start with `/context-load` for continuity or `/pack` when selecting active task-pack work.

Use `/implement-task` for bounded ad hoc changes, `/implement-pack` for one task pack, `/reflect` before claiming completion, and `/handoff` when reasoning should survive the session. Use `/close` for the full verification closeout.

## Core files

1. `trellis-docs/trellis-findings.md` — append-only empirical findings. Stable IDs: `F<N>`.
2. `trellis-docs/trellis-decisions.md` — architectural decisions with confidence markers. Stable IDs: `D-<N>`.
3. `trellis-docs/trellis-runs.md` — compact table of experiment or measurement runs.
4. `task-packs/` — bounded work specs. Active packs are only root-level `task-packs/TP-*.md`.
5. `memory/` — Trellis internal procedural memory, when present; public maintainer notes only.
6. `.claude/GODFILE.md` — generated compact state. Regenerate with `python tools/trellis_extract_godfile.py`.
7. `.claude/rules/` — path-scoped Trellis instructions that load only when relevant.
8. `trellis-docs/trellis-harness.md` — human-readable explanation of the harness.

## Standard commands

```powershell
python tools/trellis_bootstrap.py --yes
python tools/trellis_check_env.py
python tools/trellis_extract_godfile.py
python tools/trellis_extract_godfile.py --check
python tools/trellis_memory_lint.py
python tools/trellis_refs.py
python tools/trellis_pack_lint.py
python tools/trellis_reflect.py --check
python tools/trellis_inventory.py --check
python tools/trellis_repair_gate.py
# Source checkout only; installed Trellis self-tests live under .claude/trellis-tests/.
python -m pytest -q
```

## Project customization points

Fill these in after installing Trellis into a real project:

- Mission: what question or product goal this repo serves.
- Code map: the important directories and modules.
- Project-specific commands: training, eval, build, sample, package, or release commands.
- Known pitfalls: distilled from real findings.
- Output style: user/project preferences not already covered by Trellis defaults.

## Current mission

Build the determinism layer for neural compression: a bit-exact integer
reference coder, a specified probability grid, model-pinned containers,
and a conformance suite that makes deterministic decode a testable claim.
v0 proves the machinery on humble integer models; TP-1 brings the LLM.
North star: an archive packed today decodes bit-exactly on any machine,
any hardware, any year.

## Code map

```text
src/lockstep/rac.py        integer range coder — the trust base; changing constants is a format break
src/lockstep/cdf.py        CDF + quantizers; quantize_weights is core, quantize_probs is research surface
src/lockstep/models.py     PredictiveModel protocol + adaptive-order1 / static reference models
src/lockstep/codec.py      model-agnostic encode/decode loop
src/lockstep/container.py  .lsa model-pinned container, dual sha256, loud failure taxonomy
src/lockstep/envprobe.py   machine determinism fingerprint (python -m lockstep env)
src/lockstep/drbg.py       specced deterministic bytes for tests/vectors — never random.Random
tests_project/             stdlib unittest suite; pytest-compatible; run before and after every change
conformance/               lsp0 vectors; regenerating them is a format break and needs a decision
specs/                     normative documents — code follows spec, not the reverse
docs/                      research context: taxonomy, prior art, patents, architecture
experiments/               protocols that need operator hardware (GPUs); do not simulate results
tools/lockstep_gen_vectors.py  vector generator; --write only inside a pack that says so
```

## Project commands

```powershell
python -m unittest discover -s tests_project -t . -q   # always available
python -m pytest -q tests_project                       # on machines with pytest
python tools/lockstep_gen_vectors.py                    # print vectors (no write)
python -m lockstep env                                  # machine fingerprint
```

## Project pitfalls

- No floats on the coding path. `quantize_probs` exists for TP-2 research;
  the reference codec must stay integer-only (D-7).
- Coder constants, model parameters, and the quantizer rule are all part
  of decode profile lsp0. "Refactors" that change emitted bits are format
  breaks: they need a task pack, a decision, and regenerated vectors.
- Conformance failures are signal, never test rot. Investigate before
  touching vectors.
- Patent caution around integer-network compression claims: read
  docs/03-patent-and-licensing-notes.md and TP-5 before publishing [withheld: docs/03-patent-and-licensing-notes.md not in this repository; see WITHHELD.md]
  anything that touches that design space.

## Trellis conventions

- Use `tools/trellis_plan.py` for multi-step implementation work.
- Read the active task pack before editing.
- Keep changes scoped to the active pack unless the user explicitly expands scope.
- Run targeted tests after each meaningful change.
- Run `/reflect` or `python tools/trellis_reflect.py --check` after meaningful cross-file edits.
- Run `python tools/trellis_repair_gate.py` before declaring harness work complete. In source checkouts, also run `python -m pytest -q`.
- Record durable empirical observations in `trellis-docs/trellis-findings.md`.
- Record durable architectural choices in `trellis-docs/trellis-decisions.md`.
- Record reusable Trellis-maintenance patterns in `memory/` only when `memory/.trellis-memory` is a regular, non-symlink file and the note is stable, public, and not better represented as findings, decisions, runs, or task packs.
- Run `python tools/trellis_memory_lint.py` after changing Trellis memory.
- Regenerate `.claude/GODFILE.md` after changing findings, decisions, runs, or active task packs.
- Run `python tools/trellis_refs.py` after changing stable references.
- Move completed packs to `task-packs/done/` or `task-packs/completed/` with a status line.
- Record durable reasoning in `tools/trellis_blueprint.py` only when it should survive session compaction.

## Structural enforcement

Hooks in `.claude/hooks/` enforce selected rules:

- `src/` edits require the real project-root `trellis-docs/trellis-findings.md` and `trellis-docs/trellis-decisions.md` to have been read in the current session.
- `src/` edits are blocked when `.claude/GODFILE.md` is missing or content-stale.
- Decision confidence promotion is blocked unless explicitly justified.
- New source text citing `F<N>` triggers a reminder to verify that finding.

If a hook blocks a tool call, read the stderr message and fix the missing precondition.

## Claude Code surfaces

Commands:

- `/trellis-bootstrap` — integrate Trellis into root `CLAUDE.md` and `.gitignore` with explicit permission.
- `/context-load` — resume compact state and blueprint continuity.
- `/pack` — session-opening workflow with task-pack selection.
- `/implement-task` — focused or multi-phase ad hoc implementation.
- `/implement-pack` — single-pack implementation workflow.
- `/reflect` — deterministic and cognitive reflection pass.
- `/handoff` — finalize cognitive blueprint continuity.
- `/close` — full verification closeout workflow.
- `/decision` — interactive decision entry.
- `/glass-castle` — self-audit for unmarked assumptions.

Skills:

- `findings-log`
- `decision-record`
- `task-pack-format`
- `run-analysis`
- `verify-workflow`

Agents:

- `run-analyzer`
- `task-pack-author`
- `finding-investigator`

Rules:

- `.claude/rules/source-work.md`
- `.claude/rules/test-work.md`
- `.claude/rules/task-packs.md`
- `.claude/rules/project-memory.md`
- `.claude/rules/harness-maintenance.md`

## Permission truth

Trellis permissions are workflow guardrails and accident-prevention friction. They are not a sandbox, malware containment, or a hard security boundary. Shared settings keep root `CLAUDE.md` and `.gitignore` behind `tools/trellis_bootstrap.py`, keep root `memory/**` writes behind explicit review paths, and avoid auto-allowing broad shell readers, git staging, or package installation; use local settings for broader operator-specific access. For hard isolation, use OS permissions, containers, VMs, or Claude Code sandboxing.

## What not to do

- Do not run expensive operations without explicit user approval.
- Do not add dependencies casually.
- Do not refactor for aesthetics.
- Do not edit generated `.claude/GODFILE.md` by hand.
- Do not treat example, archived, completed, or done task packs as active work.
- Do not promote decision confidence silently.
- Do not import folder-mode pack chains, auto-commits, release gates, integrity manifests, dashboards, daemons, databases, or broad governance systems.
<!-- END TRELLIS BOOTSTRAP -->

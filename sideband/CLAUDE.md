# CLAUDE.md — repo conventions

Read FINDINGS.md, DECISIONS.md, OPEN_QUESTIONS.md before changing anything;
docs/BLUEPRINT.md is the plan of record.

## Hard rules
- `make test` green before any commit; `make lint` before committing findings.
- Findings go in FINDINGS.md with `- regime:` and `- source:` lines pointing
  at committed evidence (results/, tests/, ...). No regime, no finding (D-4).
- Never re-implement verifier math: import from `sideband.specdec` (D-3).
  If you need a fast path, make the numpy tests pass against it first.
- Steering claims are meaningless without the free_lastp baseline (D-5).
- Compare policies at identical seeds; telemetry reads use the isolated RNG
  stream — do not "simplify" that away (D-6).
- Bucket predictions/gates live in concept space, glue bucket excluded (D-7).
- Analytic per-position acceptance is the headline; empirical by-offset is
  survival-conditioned — label which one you're reporting (D-9).
- `src/sideband/real/` requires a GPU box; nothing in CI may import torch.

## Workflow
- Experiments are deterministic given --seed; results/*.json are committed
  evidence — regenerate with `make experiments`, don't hand-edit.
- Before merging experiment changes or new findings, run the
  `sideband-critic` agent (.claude/agents/) against the diff. Its
  highest-value mode is RECOMPUTING decisions from the raw state files,
  not reading diffs — ask for that explicitly.
- Wall-clock claims are banned: nothing in this repository is a benchmark
  harness, and logged runtimes are provenance, not claims (D-9 and its
  dated note of 2026-10-16). A registered latency measurement (K-5's sidecar
  timing) is a measurement, not a claim. Superseded wording, kept for the
  record: "until the KV-crop fast path exists (the HF adapter recomputes
  prefixes)"; the adapter has cropped KV caches by default since b1dae57
  (2026-08-29).

## Working practices (earned 2026-08-30/31, Phase-2/3/P1 arc)
- Numbers in prose/commit messages ONLY from files just read in that
  session — never from recollection or extrapolation (six miscounts
  caught by the critic across one session).
- Pre-register everything, post-hoc diagnostics included: pin cells,
  readouts, and conclusion labels before running; date amendments and
  make them before any result is read (P1 precedent). Pin a replication's
  gating cell AND its non-firing branches before it runs (F-15 precedent).
- Registered runs' *.state.jsonl checkpoints are committed EVIDENCE (the
  per-prompt cluster counts reproduce the bootstrap); they carry a
  sha-header binding to their harvest, and resume refuses a mismatch.
  Smoke-run state files are scratch (gitignored).
- When probing "does adding feature block B help over A", run the
  equal-dims noise anchor (A + alignment-destroyed B) alongside —
  measured dilution here was −0.0045..+3e-5 per +2048 dims, enough to
  fake a null (F-16 P1 design).
- Registered text with an error gets a dated erratum, never a rewrite.

## Harness (espalier, adopted 2026-10-01 on branch espalier-trial)
- Dated amendment 2026-10-15 (call PC-9 of the 2026-10-14 public-cut batch): the
  working branch is `main` since 2026-10-14, fast-forwarded onto `espalier-trial`
  (c23f214 to b924585) and pushed; `espalier-trial` is a retired historical ref.
  The heading keeps its branch name as written on 2026-10-01.
- Repo changes go through the lane: `/implement-task` (or `--multi`), then
  `/critic`, `/preflight`, `/commit`, `/handoff`. The plan gate blocks
  Write/Edit until an execution plan is in progress under src/, tools/
  (outside tools/cc), experiments/, results/, data/, .github/ and the root
  files README.md, CLAUDE.md, CHANGELOG.md, CONTRIBUTING.md, AGENTS.md,
  Makefile, pyproject.toml, setup.cfg and espalier.toml (a root file is
  gated when its name or extension marks it as code or config, a root .py,
  .json or .yml included); exempt are tests/, docs/, task-packs/, cc/,
  .claude/, memory/, reports/, .espalier-state/, FINDINGS.md, DECISIONS.md,
  OPEN_QUESTIONS.md, HANDOFF.md, ESPALIER_MEMORY.md, CITATION.cff,
  .gitattributes and .gitignore; Bash writes are not gated (a gap, not a
  licence). `tests/test_harness_doc_claims.py` holds this list against the
  hook, and `espalier.toml` keeps the gate everywhere it applies
  (`plan_exempt_prefixes = []`).
- Hooks are per machine: they live in the untracked `.claude/settings.json`,
  so on a fresh checkout run `python -m espalier doctor .` before trusting
  the gate.
- Harness memory and footguns: [ESPALIER_MEMORY.md](ESPALIER_MEMORY.md)
  (harness decisions, session log), [docs/SHARP_EDGES.md](docs/SHARP_EDGES.md)
  (footguns measured on this box; long entries live under
  [docs/sharp-edges/](docs/sharp-edges/README.md)),
  [docs/CONVENTIONS.md](docs/CONVENTIONS.md) (patterns measured on this tree),
  [docs/TASK_RECIPES.md](docs/TASK_RECIPES.md) (the landing recipe). Engine
  reference docs seeded by the harness: [docs/WORKFLOW.md](docs/WORKFLOW.md),
  [docs/INSTALL-CI.md](docs/INSTALL-CI.md),
  [docs/ENV_CATALOG.md](docs/ENV_CATALOG.md).
- Managed bodies (`.claude/commands/*.md` with the line-1 marker,
  `cc/COMMANDS.md`, `cc/LIVE_SURFACE.md`, `cc/PACK_MANIFEST.txt`) regenerate
  on `espalier init` / `upgrade` and would drop the sideband-critic lane;
  `tests/test_critic_lane.py` is the witness. Run engine commands only with an
  engine whose version matches the seeds' first-line marker.
- Never edit `tools/cc/hooks/*` (integrity-manifested) or a frozen
  instrument: a `tools/run_*.py` whose sha is attested in a results/ payload
  (fourteen on 2026-10-17, the S1 word instrument's the fourteenth) or any tools/ module such an instrument imports
  (run_fullfree.py, run_posthoc_topic.py, run_probes.py), seventeen files in all.
  `ruff` excludes those seventeen outright (`force-exclude`) and is otherwise
  pyflakes-only because the house style keeps one-line statements and short
  names; `tests/test_harness_doc_claims.py` derives the seventeen from the
  payloads and their imports.

## Trellis note
This repo follows the Trellis conventions (findings/decisions logs, regime
tags, critic agent, kill-criteria doc) and should drop into the harness
without changes; the lint tool is standalone on purpose.

# Contributing

Read CLAUDE.md (the hard rules), FINDINGS.md, DECISIONS.md and
OPEN_QUESTIONS.md first; docs/BLUEPRINT.md is the plan of record. House
terms used below and not defined inline are in docs/GLOSSARY.md.

## Before every commit

- `python -m pytest -q` must be green (this is `make test`; `make` is not
  required). A sanity subset before the full suite (README.md's quickstart
  calls it a 1-2 minute run on the author's box):
  `python -m pytest -q tests/test_stats.py tests/test_specdec.py`.
- `python tools/lint_findings.py` (`make lint`) must print OK before
  committing anything that touches FINDINGS.md.
- Nothing importable from tests/ or experiments/ may import torch at module
  level (CI installs only `.[dev]`; export note 2026-10-13: the public repository's root workflow installs `.[dev,analysis]`). GPU code lives in src/sideband/real/
  and imports torch lazily; tests that need it carry
  `@pytest.mark.skipif(not _has("torch"), ...)`.

## Adding a finding

A finding is a `## F-<n> - <title>` section in FINDINGS.md. It MUST carry a
`- regime:` line (where the number was measured: synthetic world vs real
models, model pair, seeds, prompt population) and a `- source:` line whose
repo paths exist and are tracked by git (results/, experiments/, tests/, docs/,
src/, data/ and tools/ prefixes are checked by tools/lint_findings.py, brace
shorthand expanded and a bare file name resolved against the last cited
directory; DECISIONS.md D-4; tracked since 2026-10-01). No regime, no
finding. Numbers in the text are copied from files read in the same
session, never from memory. A telemetry-steering claim is meaningless
without the free-information baseline column (D-5: free_lastp, steering
from the target's last verified distribution, which every speculative
decoder already has). Label acceptance numbers as analytic per-position
(the headline, D-9) or empirical by-offset (survival-conditioned).

## Register before you run

Pin the cells, readouts, gating rule and conclusion labels in
docs/BLUEPRINT.md (dated) before a run starts, including the non-firing
branches and any post-hoc diagnostic. Amendments are dated and land before
a result is read. Registered text with an error gets a dated erratum, never
a rewrite. A run whose guard breaches follows the registered void
semantics; its gate metrics stay unread.

## Evidence files

results/*.json and results/real/** are committed evidence: regenerate them
with the tool that wrote them (`python experiments/run_all.py` for the
synthetic e01-e07; the GPU tools under tools/ for results/real/), never
hand-edit them, and never rewrite history the registered documents cite by
commit hash. The registered runs' *.state.jsonl files are evidence too:
they are the recompute surface for the bootstrap CIs, so keep their row
order. `experiments/run_all.py --smoke` writes to results/smoke/ (gitignored).

## Run the critic

Before merging experiment changes or a new finding, run the
`sideband-critic` agent (.claude/agents/sideband-critic.md) against the
diff and ask it explicitly to RECOMPUTE the decision from the committed
state files rather than read the prose; its objections come tagged
BLOCKING or ADVISORY and end with the cheapest experiment that would change
its mind. Compare policies at identical seeds with telemetry on its
isolated RNG stream (D-6), and never re-implement verifier math: import it
from sideband.specdec (D-3).

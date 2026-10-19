# TP-4_cross_device_determinism_harness

**Status**: archived 2026-10-10 (TP-7, F-19): the research is closed; this pack will not be executed.

## Goal
Build the tooling that executes E-001 and E-003 end-to-end: logit capture, cross-device diffing, grid-crossing analysis, and machine-fingerprinted reports.

## Why this matters
The project's central empirical question is "how big is real drift and does our grid absorb it" - answering it by hand once proves nothing durable. A repeatable harness turns every new device, driver, or runtime into a one-command census, and its reports are the evidence base for lsp1's stated drift bound.

## Out of scope
- No fixes to any drift found (TP-2 owns mitigation).
- No serving-stack or batch>1 optimization work; measurement only.
- No purchase or provisioning decisions; runs use whatever devices the operator supplies.

## Files touched
- `tools/lockstep_drift_census.py` - orchestrates capture runs, pairwise diffs, grid-crossing stats, and a JSON+markdown report per device set.
- `src/lockstep/adapters/capture.py` - logit-dump hook on the TP-1 adapter (positions, raw floats, fingerprint digest).
- `experiments/E-001-cross-device-logit-drift.md` - updated with exact commands once the tool exists.
- `tests_project/test_drift_census.py` - unit tests on synthetic logit files (no GPU needed): diff math, bucket stats, report shape.

## Risk level
Low. Pure measurement tooling; touches no format surface and no Tier-0 code.

## Dependencies
- TP-1 adapter with capture hook surface.
- `experiments/E-001-cross-device-logit-drift.md` and `experiments/E-003-batch-invariance.md` protocols.
- Operator hardware for real runs (tool must still be fully testable without it).

## Proof gate
```powershell
python -m unittest tests_project.test_drift_census -v
python -m unittest discover -s tests_project -t . -q
python tools/trellis_pack_lint.py task-packs/TP-4_cross_device_determinism_harness.md
```

## Sub-tasks
1. Capture format: npz/jsonl of per-position logits + envprobe digest + corpus hash; documented in the tool docstring.
2. Diff engine: pairwise max/p99/mean drift, magnitude-bucketed; probability-space conversion; grid-crossing fraction at 2^12..2^16.
3. Report emitter: one markdown table per device pair ready to paste into a run row; JSON alongside for machines.
4. Synthetic-input tests covering: identical inputs (zero drift), seeded drift at known magnitudes, and a crafted case straddling a grid boundary.

## Final acceptance
- On synthetic fixtures, reported drift stats match hand-computed values exactly.
- A dry run over two local capture files (may be CPU-only) produces the full report without manual steps.
- E-001 doc contains the literal commands an operator runs on each device.
- Every command in Proof gate passes.

## Stop conditions
- Stop if the capture hook cannot expose raw logits without patching llama.cpp itself - record the limitation and escalate to a design note first.
- Stop if census math requires dependencies beyond numpy.
- Stop if acceptance cannot be verified without GPU access.

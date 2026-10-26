---
name: run-analysis
description: Use when an experiment or training run has just finished, when the user shares run output (loss curves, eval results, run metadata), or when discussing what a run revealed. Covers what to look at first, how to read measurement noise vs signal, the difference between best and final state, and common interpretation pitfalls.
---

# Run analysis

When a run produces output, focus on these dimensions in order:

## 1. Did the process behave as expected?

Did the run terminate normally? Did the metrics evolve the way you'd expect for the configuration?

Common things to look for in any run:
- Did the primary metric trend in the expected direction?
- Was there a clear transition between "learning" and "stable / plateau / overfit"?
- Did any safety guards fire (early stopping, gradient clipping, NaN detection)?
- Are there gaps in the measurement (missing checkpoints, missing val passes)?

If the process didn't behave normally, investigate before reading metrics.

## 2. Generalization gap (or its analog)

Most projects have a "trained-on" set and a "held-out" set. The difference between performance on each is the generalization signal:

- Small gap: model/system is generalizing
- Large gap: overfit to trained-on data

The threshold for "large" depends on the project's metric scale — calibrate this from prior runs.

## 3. The diagnostic that matters most for your project

<!-- TODO: customize this section -->

Every project has a specific diagnostic that tells you what the system *actually learned*, beyond what the summary metrics say. Examples:

- For an anomaly detector: which inputs trigger highest anomaly scores? Do they match what you'd intuitively call anomalous, or are they confounded by surface features?
- For a classifier: which classes are confused with which? Is the model picking up on the intended signal or a shortcut?
- For an optimizer: at convergence, what does the solution look like? Reasonable, or pathological?

This is the qualitative check that AUROC / accuracy / loss numbers don't surface.

## Cross-run comparison rules

When comparing two runs:

- **Same config, different seed → variance estimate.** Two runs differing by seed give you a noise floor. Effects smaller than the seed-to-seed variance aren't reliable.
- **Different config, same seed → effect estimate.** But you can't distinguish "the change made things better" from "you got lucky on this seed" without ≥3 seeds.
- **Different data → confounded.** Different inputs change everything; isolating the effect of a code change requires holding data constant.

## Statistical noise floor

Small sample sizes produce quantized measurements. AUROC at n=4 can only take a small number of discrete values; the same is true for any rank-based metric. Rules of thumb:

- **n < 10**: don't compare point estimates across configurations. Compare effect sizes (deltas) if you have them.
- **n < 5**: even single-configuration point estimates are barely interpretable. Report them, but don't draw conclusions.
- **Cross-run comparison**: look at multiple metrics together. A single metric moving by a small amount is rarely meaningful.

## Best vs final state

If the project tracks a "best" checkpoint (lowest val loss, highest accuracy at that step), evaluating the best state vs the final state can tell you whether you've overfit. The best state is what you'd actually use; the final state is diagnostic.

If a checkpoint format predates the "best vs final" distinction, the file may not carry the metadata needed to identify which is which. Re-train rather than reverse-engineer.

## Updating the run log

A new run typically requires a new row in `trellis-docs/trellis-runs.md` (if your project uses one). Required:

- All non-`n/a` columns filled
- "Notes" column states (a) what changed since the previous run, (b) the one most important observation

## Updating trellis-docs/trellis-findings.md

A new finding entry is warranted only if the run produced an observation that meets the bar (see `findings-log` skill). NOT every run produces a finding. Most runs are confirmations.

If the run **invalidates** a prior finding, write a NEW finding documenting the invalidation. Never edit the old one.

## Common interpretation pitfalls

- **Reading small-sample metrics as precise.** AUROC at n=4 is a category, not a measurement.
- **Reporting trained-on metrics as headline.** Trained-on performance measures memorization, not generalization.
- **Assuming "below chance" or "anomalous direction" means broken process.** It might mean methodological contamination. Trace the data flow before blaming the model.
- **Ignoring qualitative diagnostics because the headline number was "good enough".** A high metric with terrible qualitative behavior means you have a system that scores well on the specific test you ran. It won't generalize.

## Related skills

- `findings-log` — when a run produces a new finding worth recording
- `verify-workflow` — when you've run a finding verifier and need to interpret the result

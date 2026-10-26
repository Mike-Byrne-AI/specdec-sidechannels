---
name: verify-workflow
description: Use when running tools/trellis_verify_finding.py or interpreting its results. Covers what SUPPORTS / CONTRADICTS / INCONCLUSIVE actually mean, when to add a new verifier, and what to do when a verifier returns CONTRADICTS — including the protocol for writing a new finding that documents the invalidation.
---

# Verify-finding workflow

`tools/trellis_verify_finding.py` is the glass-castle protocol's structural layer: it makes findings testable rather than asserted.

## Verdicts

The script returns one of three verdicts:

- **SUPPORTS**: the finding's claim is observable in the current state with the expected magnitude. This is reaffirmation, not promotion to `[verified]` confidence in trellis-docs/trellis-decisions.md — that requires the user's explicit promotion (see `decision-record` skill).

- **CONTRADICTS**: the finding's claim is NOT observable. Either the system has changed (later work invalidated the finding), the data has changed, or the original finding was wrong.

- **INCONCLUSIVE**: there isn't enough signal to support or contradict. Common causes: sample too small, state doesn't put the finding in scope, the measurement that would test the finding can't be made in the current configuration.

## What to do with each verdict

### SUPPORTS

- Note the result.
- If the finding is currently marked at lower than `[verified]` confidence in trellis-docs/trellis-decisions.md, you may PROPOSE (not perform) a promotion. The user adds `USER-CONFIRMED` or includes the verify_finding citation in the diff.
- Don't celebrate. Supporting evidence is the expected case for a still-valid finding.

### CONTRADICTS

This is the high-stakes verdict. Do the following:

1. **Don't edit the existing finding.** trellis-docs/trellis-findings.md is append-only.

2. **Write a NEW finding documenting the invalidation.** Use the next free F-N number. Reference the contradicted finding by ID.

3. **Surface the contradiction to the user before continuing other work.** A contradicted finding may invalidate decisions made on its basis. Trace which D-N decisions cite this finding as their source.

4. **Don't auto-act on the contradiction.** The user decides what to do next — possibly nothing, possibly a new task pack to reconsider downstream decisions.

### INCONCLUSIVE

- Note the result.
- Read the script's explanation (it should give a specific reason: "run too short", "no eligible sessions", "effect size too small", etc.).
- The action depends on the reason:
  - Insufficient data → generate more
  - Wrong state for the test → run against a different checkpoint or configuration
  - Effect size too small → not enough signal at this scale; verification deferred

INCONCLUSIVE is not failure. It's honest reporting that the available evidence doesn't reach the bar.

## When to add a new verifier

When a new finding is recorded, ideally a programmatic check is added to `tools/trellis_verify_finding.py` for it. Not every finding can be verified programmatically — some are methodological observations that don't reduce to a numeric check. But many can.

The pattern:

1. Read the existing verifiers in `tools/trellis_verify_finding.py` for the convention (the file ships with a template comment if none exist yet).
2. Write a new `verify_FN` function with the signature `(args) -> str` returning one of the Verdict constants.
3. Register it in the `CHECKS` dict at the bottom of the file.
4. Test by running `python tools/trellis_verify_finding.py F-N` against a relevant target.

The function should:
- Print what the finding claims
- Print what was measured (the actual numbers)
- Return a verdict with a one-line summary

## Citing verifications in code

When source code makes a claim that depends on a finding, cite the finding by ID:

```python
# Per F-N, <claim>
# Re-verify with: python tools/trellis_verify_finding.py F-N
```

The `flag_finding_citations.py` hook detects these citations on edits and reminds you to verify.

## Common mistakes

- **Treating SUPPORTS as the same as "verified" confidence.** Confidence promotion is a user action. SUPPORTS is just evidence.
- **Editing a finding in place when CONTRADICTS comes in.** Append-only. New entry.
- **Skipping the "Open question" line in the new (invalidating) finding.** The contradiction itself is often more interesting than the original finding — capture what we still don't know.
- **Running verify_finding without a recent target.** Verification is state-relative. An old verification doesn't apply to a new run.

## Related skills

- `findings-log` — for writing the new finding when CONTRADICTS comes in
- `run-analysis` — for the broader context of what a run revealed

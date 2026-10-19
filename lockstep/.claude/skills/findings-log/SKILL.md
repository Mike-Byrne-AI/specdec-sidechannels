---
name: findings-log
description: Use when reading or writing trellis-docs/trellis-findings.md, or when an empirical observation from a training run is being discussed and needs to be recorded. Covers the append-only convention, finding-number assignment (F1, F2, ...), what counts as a finding vs noise, and the relationship between findings and DECISIONS / RUNS.
---

# Findings log

trellis-docs/trellis-findings.md is the empirical memory of this project. It's what survives across runs, sessions, and even people. Treat additions to it as the most consequential writing in the repo.

## What a finding is

A finding is an **empirical observation about behavior**, supported by run data. It's not:
- A design choice (that's a DECISION)
- A planned experiment (that's a TASK PACK)
- A hypothesis you haven't tested (that's IMAGINED, belongs nowhere yet)

A finding has the form: "When we did X, we observed Y, and Y is unexpected/notable because Z."

If you can't cite a run number or a concrete observation, it's not a finding.

## Numbering

Findings are numbered F1, F2, F3, ... in the order they were first observed. The number is permanent and citable from code, decisions, task packs, and other findings.

To pick the next number:
1. Read trellis-docs/trellis-findings.md
2. Find the highest existing F-N
3. Use F(N+1)

## Append-only

Findings are never edited or deleted. If a later run invalidates a finding, write a NEW finding that documents the invalidation:

> **F7 — F2 no longer holds at scale**
> 
> Run_005 (with the larger dataset) shows the phenomenon documented in F2 does not appear. F2 was correct for the earlier regime but does not generalize. F2 should be considered superseded by F7.

The original F2 entry stays where it was. The audit trail matters.

## Structure of a finding entry

```markdown
### F-N — <title>

**Observation**: <what was measured, in 1-3 sentences>
**Context**: <which run, what config, what split>
**Why it matters**: <the implication — what this rules in or out>
**Status**: <action taken, action queued, or "noted">
**Open question**: <what we still don't know>
```

Status options:
- `acted on` (link to a task pack or code change)
- `queued` (link to a task pack)
- `noted` (no immediate action needed, but recorded for context)

## When to write a new finding

The bar is: would a future session reading trellis-docs/trellis-findings.md make a different decision because of this entry? If yes, write it. If no, it's noise.

Concrete triggers:
- A metric, measurement, or qualitative result that surprises (in either direction)
- A behavior that confirms or contradicts a previous finding
- A methodological gotcha that bit you and would bite future sessions
- An emergent pattern across multiple runs

NOT triggers:
- An expected result that confirmed a hypothesis ("the change worked")
- A bug fix (that's a commit message, possibly a decision)
- A planned experiment outcome that landed where predicted

## Where findings appear elsewhere

- `trellis-docs/trellis-runs.md` table has a "Linked findings" section at the bottom — update it when a finding is first observed in a run and when later runs verify/invalidate it
- `trellis-docs/trellis-decisions.md` D-N entries cite findings as their `Source` when the decision was driven by empirical evidence
- Code comments cite findings with the bare token (`# Per F2, we expect ...`)
- The `flag_finding_citations.py` hook reminds CC to run `trellis_verify_finding.py` whenever a finding ID appears in changed code

## Common mistakes

- Writing a finding as "X works well" — too vague, not citable, not testable. Find the specific observation.
- Editing an old finding to "correct" it — never do this. Add a new one.
- Skipping the "Why it matters" line — without it, the finding is just data. The matters-line is what makes it useful to future sessions.
- Confusing a finding with a decision. If it's a choice you made about how to proceed, that's a DECISION. If it's an observation about the world, that's a FINDING.

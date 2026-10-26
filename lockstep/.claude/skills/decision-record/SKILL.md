---
name: decision-record
description: Use when reading or writing trellis-docs/trellis-decisions.md, when an architectural choice is being made or proposed, or when discussing why the project is shaped a particular way. Covers the D-N numbering, the verified/probable/imagined confidence ladder, when to propose promotions, and the hook-enforced restriction that only the user promotes confidence.
---

# Decision records

trellis-docs/trellis-decisions.md captures architectural choices that affect more than one task pack or sub-task. The point is to prevent relitigation: when a future session asks "should this be different?" the answer (with reasoning) lives in trellis-docs/trellis-decisions.md.

## Numbering

D-N format. Read trellis-docs/trellis-decisions.md, find highest existing N, use N+1. Numbers are permanent — never renumber.

## The confidence ladder

Every decision is tagged `[imagined]`, `[probable]`, or `[verified]`.

- **`[imagined]`**: a design choice that has not yet been built. Most decisions start here. Example: "we will adopt approach X" before the supporting task pack lands.
- **`[probable]`**: built or partially built, but not directly tested. The design exists in the codebase and is internally consistent, but no empirical check has confirmed it does what we think.
- **`[verified]`**: built AND directly validated by either (a) a run number that shows the expected behavior, or (b) a successful `trellis_verify_finding.py` invocation.

## CC must not silently promote

Only the user moves a decision from `[imagined]` → `[probable]` → `[verified]`. CC can propose, not promote.

This is enforced by `check_confidence_promotion.py` hook. Without justification (a `trellis_verify_finding.py` citation, a `verified by run_NNN` phrase, or `USER-CONFIRMED` marker), promotions are blocked.

If you (CC) believe a decision is ready for promotion:

> "D-N was marked `[imagined]`. After the relevant task pack landed and run_NNN showed the expected behavior, I think we have evidence for `[verified]`. Want me to update it?"

The user adds the marker; you don't.

## Structure of a decision entry

```markdown
## D-N — <Short title>                                                    [confidence]

**Context**: <what we were trying to decide>
**Choice**: <what we picked>
**Why**: <the argument that won>
**Alternatives considered**: <other options and why they lost>
**Reversibility**: <cheap / medium / expensive>
**Source**: <link to runs, findings, task packs>
```

The title is 5-10 words. Avoid weasel-words ("Better path pool handling"). Be specific ("Path pool scoped to same-split-other-sessions").

## When to write a new decision

Triggers:
- The user just chose between two options for how something should work
- The user specified a constraint that affects future work ("we'll never add early stopping because we want to see the overfit curve")
- A finding implies a design change (e.g., "F-N implies we need to change approach X")
- A task pack proposes a choice that locks in behavior

NOT triggers:
- A bug fix
- A refactor with no semantic impact
- A code-style preference
- A one-off experimental choice that doesn't constrain anything

## Promotion etiquette

When proposing a promotion:
1. State the current confidence
2. Cite the new evidence (run number, finding, verify_finding result)
3. Propose the target confidence
4. Ask for the user's confirmation

When the user confirms, they add `USER-CONFIRMED` or a `trellis_verify_finding.py` citation to the diff. The hook checks for one of those tokens.

## Common mistakes

- Promoting `[imagined]` → `[probable]` because the code was written. Writing code doesn't verify it — running it does. Use `[probable]` only when the design is operational.
- Treating `[verified]` as final. It's verified at a moment; later runs can invalidate it. If they do, write a NEW finding (not edit the decision) and the user may downgrade confidence.
- Writing decisions about trivia. The bar: does this constrain more than one future task pack? If no, it's not a decision worth recording.
- Skipping "Alternatives considered." This section is what makes the decision relitigation-proof. Without it, future sessions will re-derive the same alternatives and waste time.

## Related skills

- `findings-log` skill — for the empirical observations that often drive decisions
- The `/decision` command — interactive draft entry

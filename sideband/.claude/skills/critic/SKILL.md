---
name: critic
description: Adversarial review of an experiment change, a finding, or a payload by the sideband-critic agent, recompute mode by default — it re-derives the asserted labels and numbers from the committed state files. Use before committing findings, merging experiment changes, or writing up results, and when the user asks to run the critic, recompute a result, or red-team a claim. Distinct from /review (code correctness) and /adversarial (self-inflicted failure modes). Delegates to the sideband-critic agent.
---
# Critic — sideband-critic delegation

The work is performed by the **sideband-critic** agent in its own context
so this conversation's framing does not bias the review. Its checklist and
its two modes are in `.claude/agents/sideband-critic.md`; this skill is
this repository's own (not espalier-managed) and survives a harness re-init.

## Step 1 — Frame the surface and the mode

One mode rule, the same one the gates use: **recompute** when the scope touches
`results/` or `FINDINGS.md` (there is committed evidence to recompute from);
**diff** otherwise (a registration, an instrument or code change that has not run).
The research-record surface the gates fire on (one canonical list, asserted at
every site by `tests/test_critic_lane.py`): `results/`, `data/`, `experiments/`, `src/sideband/`, a `tools/*.py` outside `tools/cc/`, `tests/test_*_landing.py`, `FINDINGS.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md`, `docs/BLUEPRINT.md`, `docs/WHY_THIS_DIES.md`, `docs/REPORT.md`, `docs/FINDINGS_INDEX.md`, `docs/OQ*_*.md` or `README.md`.

- "critic the uncommitted work" — the pre-commit case, and the default when the
  user names nothing → `git diff HEAD` plus every untracked file in
  `git status --short` that belongs to the change.
- "critic the branch" → `git diff main...HEAD`.
- "critic the staged changes" → `git diff --cached`.
- "critic finding F-NN" / "recompute payload X" → the finding's `- source:`
  payloads and their `.state.jsonl` files; recompute.
- "critic the registration" → the BLUEPRINT block and the instrument it
  registers; diff.
- Otherwise: ask which diff, finding or payload, and say which mode the rule gives.

## Step 2 — Delegate to sideband-critic

Dispatch the **sideband-critic** subagent (`subagent_type='sideband-critic'`).
Pass:

- the exact scope from step 1: paths, shas, the finding or question id;
- the mode, and for recompute the pinned numbers the text asserts (labels,
  deltas, counts, CI bounds) so the agent reports a discrepancy, not an
  impression;
- the cadence — pre-registration, pre-run, landing, or write-up — because
  the checklist items that matter differ (leakage and pairing before a run;
  survivorship, regime and recompute at landing).

Freeze edits to the scoped files while the agent is out. When `/preflight`,
`/implement-task` or `/implement-pack` dispatched the critic beside the
code-reviewer and the failure-mode-reviewer, read the critic's report first:
its BLOCKING objections decide whether the other two reports are about a
result worth fixing.

## Step 3 — Surface the verdict

Present the numbered objections as-is, each with its BLOCKING / ADVISORY tag
and its file/line references, the "What would change my mind:" sentence,
and for recompute the maximum discrepancy. Do not re-litigate the calls.
BLOCKING = NO-GO for the gate that dispatched it. "No objection" is reported
in those words; it is not "verified".

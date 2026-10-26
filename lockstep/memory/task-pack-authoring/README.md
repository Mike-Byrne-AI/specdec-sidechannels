# Task-pack authoring memory

Use this folder for durable lessons about writing Trellis task packs. It is not a place to store active task state; active work belongs in root-level `task-packs/TP-*.md`.

## Current patterns to preserve

- One pack should fit roughly one focused implementation session.
- The `Files touched` section is a scope boundary, not a guess. If expected files change, update the pack before execution continues.
- `Proof gate` names concrete commands. Avoid vague proof such as "run tests" without the exact command.
- `Final acceptance` is the completion contract. Every item must be observable.
- `Stop conditions` should protect the operator from scope creep, red proof, broad rewrites, or manual-only steps.
- `TP-0` is reserved for examples under `task-packs/examples/`; active root work starts at the first nonzero pack number.

## Authoring checklist

Before a pack is considered review-ready, check that it has:

1. a narrow goal and explicit out-of-scope boundaries,
2. exact changed paths or path families,
3. low/medium/high risk with a reason,
4. dependencies that cite real files, findings, decisions, or `None`,
5. a proof gate that can be run locally,
6. numbered sub-tasks with a sensible order,
7. final acceptance criteria that can be verified without interpretation,
8. stop conditions that force a pause when the work becomes unsafe or ambiguous.

## Common drift to avoid

- Do not reintroduce the old `Verification` heading; use `Proof gate`.
- Do not make example packs active work.
- Do not hide multi-pack programs inside one oversized pack.
- Do not write packs that require network, credentials, destructive shell commands, or broad host edits unless the user explicitly asked for that scope.
- Do not claim a drafted pack is complete. The user decides when a draft becomes authoritative.

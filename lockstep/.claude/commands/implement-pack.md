Implement one Trellis task pack end to end.

## Usage

```text
/implement-pack task-packs/TP-N_name.md
/implement-pack --resume
```

This Trellis command intentionally supports single-pack mode only. It does not auto-run folders, require commits, update changelogs, or mirror package resources.

## Workflow

**1. Read the exact pack path supplied by the user.** Do not substitute a similarly named file. The pack's Proof gate and Final acceptance sections are the contract.

**2. Lint the pack.** Run:

```powershell
python tools/trellis_pack_lint.py <path-to-pack>
```

If lint fails, stop and report the missing contract pieces.

**3. Audit current state.** Run any pre-state checks listed in the pack. Confirm the repo still matches the assumptions in the pack. If not, stop.

**4. Create an execution plan from the pack sub-tasks.** Run:

```powershell
python tools/trellis_plan.py create --task "<TP-N>: <one-line goal>" --steps "phase 1|phase 2|phase 3"
```

Each phase should map to one sub-task or one proof boundary.

**5. Execute phase by phase.** For each phase:

```powershell
python tools/trellis_plan.py mark <index> running
```

Make the changes, run the phase proof, then mark `passed` or `failed`.

**6. Run final proof.** Run the pack's Proof gate. Then run:

```powershell
python tools/trellis_refs.py
python tools/trellis_memory_lint.py
python tools/trellis_reflect.py --check
python tools/trellis_extract_godfile.py
python tools/trellis_extract_godfile.py --check
```

Run `python -m pytest -q` unless the user explicitly narrowed verification.

**7. Record blueprint outcome.** Run:

```powershell
python tools/trellis_blueprint.py record --kind pack_result --description "<TP-N> shipped: <one-line result>; proof: <commands>"
```

**8. Move completed pack only after acceptance is verified.** Move it to `task-packs/done/` and prepend a short status line if the repo convention calls for it. Leave incomplete packs active.

**9. Report.** Include changed files, proof commands, plan status, completed acceptance criteria, and remaining risks.

## Resume

Run:

```powershell
python tools/trellis_plan.py status
python tools/trellis_plan.py next
```

Re-read the task pack before continuing. Resume from the first running, pending, or blocked step.

## Stop conditions

Stop and ask before continuing if:

- pack lint fails,
- pre-state no longer matches the pack,
- targeted proof fails,
- final proof fails,
- an acceptance criterion cannot be verified,
- changed files leave the pack's Files touched scope,
- the pack contains `STOP`, `OPERATOR REQUIRED`, `DO NOT AUTO-EXECUTE`, or `MANUAL STEP`,
- the work requires destructive, network, or expensive commands not already authorized.

When a stop condition fires, report the pack, phase, literal trigger output, and two or three specific options.

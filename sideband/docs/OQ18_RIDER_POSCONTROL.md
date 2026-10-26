# OQ-18 LEAK-RIDER POSITIVE CONTROL (registered 2026-09-13, before any control cell trained)

Proposed by the pre-commit critic round (recompute mode, 2026-09-13) on
the 2026-09-07 rider amendment (docs/BLUEPRINT.md, OQ-18 block, DATED
AMENDMENT): "the E leg sees every leak the raw leg sees" is an argument
about direction, not a measured effect. This control measures it at one
leak size before any amended cell trains. It reads no OQ-18 label.

## Question

Does the AMENDED leg 2 of the leak rider (docs/OQ18_RIDER_DIAGNOSTIC.md,
"The amended leg": the twin-referenced dependence excess E(fplus_b) -
E(fplus_r) at the off2 / linear / seed-0 shuffled cell FAILS if it
exceeds 0.01 OR is CI95-clear above 0 and >= +0.005) actually FIRE on a
literal non-causal block of the modality the rider guards, and does the
registered raw leg 2 (acc(fplus_b) - acc(fplus) > 0.01) fire on it too?

## Construction (pinned)

- fplus_leak = fplus ++ the same row's slots block (SlotsAnchorBlock,
  the aligned block's own class) read at the shuffled label's OWN
  position li = (a + off - 1 + 17) mod length[row], the exact index
  sideband.probes.labels_for() uses for the shuffled label (label_index
  (a, off) + SHUFFLE_SHIFT, wrapped within the row). The block carries
  the label position's telemetry (the off-1 relation between a position's
  slots and its own token, the strongest in the record). Equal dims with
  fplus_b and fplus_r (the same block class over the same alphabet).
- One linear cell per space, off2, seed 0, shuffled labels, with the
  prediction dump (run_oq18_rider_diag.run_cell_diag, unchanged), on the
  S1 primary harvest: L3_concept_groups_v1 and L2_concept_k512.
- Reference rows: the diagnostic's own seed-0 rows for shuffled (a),
  fplus, fplus_b and fplus_r at each space, REUSED from
  results/real/oq18_rider_diag_s1.json.state.jsonl (same labels, split
  and wrap flags, so the per-prompt label histograms pair exactly; the
  tool refuses a reference row whose test_acc differs from the committed
  payload's cell entry). Nothing is re-trained.
- Statistics: run_oq18_rider_diag.excess_stats (the registered code,
  unchanged) with the leak cell in the aligned arm's seat (key fplus_b;
  the cell's features field says fplus_leak), so the pair "fplus_b-fplus"
  is the registered raw leg 2 applied to the leak and "fplus_b-fplus_r"
  is the amended leg applied to it; cluster bootstrap over the 30 test
  prompts, n_boot 2000, seed 0, selection "all" decides; non-wrapped and
  wrapped selections are reported.

## Readouts (per space, seed 0)

- E(leak) with CI95; the diagnostic's E(fplus_b) and dE_br beside it.
- dE_leak_r = E(leak) - E(fplus_r) with CI95 -> the AMENDED LEG applied.
- raw_leak = acc(leak) - acc(fplus) with CI95 -> the RAW LEG applied
  (band 0.01).
- X_leak = acc(leak) - acc(fplus_r); dE_leak_f = E(leak) - E(fplus).
- Flags: AMENDED-FIRES (the amended leg fails on (leak, fplus_r));
  RAW-FIRES (raw_leak > 0.01).

## Verdict (pinned)

- DOMINANCE-FALSIFIED: at any space RAW-FIRES and not AMENDED-FIRES.
  Consequence: the 2026-09-07 amendment is WITHDRAWN by a dated note
  before any amended cell trains; S1 stays label-less under OQ-18; the
  S3 runs conclude under the frozen instrument as registered (their
  riders passed both legs at both spaces); the user decides the next
  step.
- DOMINANCE-CONFIRMED-HERE: AMENDED-FIRES at both spaces (RAW-FIRES or
  not). The amended runs proceed; the dominance sentence may be called
  measured at the tested leak size, and only there.
- PARTIAL: AMENDED-FIRES at exactly one space and no falsification. The
  amended runs proceed; the dominance sentence stays an argument at the
  space where neither leg fired.
- UNINFORMATIVE: neither leg fires at either space. The amended runs
  proceed; the leak block carries too little to test with; the dominance
  sentence stays an argument.
- INCOMPLETE: a control cell is missing (an --only run); no verdict.

## Honest prediction (pinned before any control cell trained)

AMENDED-FIRES and RAW-FIRES at both spaces (direction: probable — the
slots at li stand in the off-1 relation to the label token, the relation
with the largest margins in the Phase-3 record); dE_leak_r >= +0.01 at
both spaces (magnitude: imagined, not derived from any number in the
record); larger at L3 than at L2 (weakly held). Surprise line, symmetric:
DOMINANCE-FALSIFIED would mean the leak expresses itself at this reader
mainly as a prediction-marginal shift that the E leg discards — exactly
the case the amendment argues cannot be a leak — and the amendment is
withdrawn; UNINFORMATIVE would mean a same-position slots block carries
less than +0.005 in E at a linear reader, which would itself be a fact
about the telemetry worth recording.

## Limits (disclosed)

One positive control at one leak size in one direction: it measures
power on THIS block and cannot show that the E leg sees every leak. It
is post-hoc relative to the diagnostic (proposed after its verdict was
read), registered here before it ran, and its pinned prediction was
written before any control cell trained.

## Evidence

results/real/oq18_rider_poscontrol_s1.json (payload: statistics, flags,
verdict, this document's sha, the diagnostic payload's and state file's
shas, instrument sha, git attestation, harvest npz shas) and
results/real/oq18_rider_poscontrol_s1.json.state.jsonl (the two control
rows with their per-prompt histograms; sha-header bound to the harvest;
negated back into git). This document is committed BEFORE the control
runs and stays byte-identical afterwards; the outcome is recorded as a
dated OUTCOME sentence in the BLUEPRINT amendment bullet and the OQ-18
ledger entry, never here.

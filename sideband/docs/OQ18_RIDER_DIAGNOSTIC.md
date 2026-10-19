# OQ-18 LEAK-RIDER DIAGNOSTIC — registered 2026-09-07, before any diagnostic cell trained; pre-read critic round applied the same day (dated section at the end)

Status: REGISTERED POST-HOC DIAGNOSTIC of a fired kill condition. Written
as an untracked file so that the two in-flight registered S3 runs (lane B)
keep a clean tracked-file attestation; its sha256 is recorded in the
diagnostic payload at run time, and the byte-identical file is committed
with the payload. This is the diagnosis the OQ-18 registration requires
before any amendment ("the whole SOURCE goes label-less until the leak is
diagnosed and a dated amendment made — no partial label is read around a
failed rider", docs/BLUEPRINT.md, OQ-18 block, CELLS / LEAK RIDER).

## What fired (read from the S1 primary state file and the lane-A log)

The registered S1 primary run (tools/run_fullfree_coarse.py at the freeze
15c4e9c, results/real/fullfree_coarse_s1.json.state.jsonl) halted at cell
36/66 on LEAK RIDER leg 2 at L3_concept_groups_v1: shuffled fplus_b
0.5314 > shuffled fplus 0.5182 + 0.01 (excess +0.0132 against the 0.01
band). The three L3 shuffled rows: shuffled (a) 0.5629 = the test majority
rate 0.5629 exactly (best epoch 1); shuffled fplus 0.5182 (best epoch 4,
val 0.5347); shuffled fplus_b 0.5314 (best epoch 18, val 0.5387). All 33 L2
cells had completed (L2 rider: shuffled (a) 0.4108 = majority, fplus
0.3991, fplus_b 0.4014 — both legs passed, leg-2 excess +0.0024). No
payload was written; no D, Mt, Mn_r or label was computed for S1. Per the
registered rule S1's L2 cells are label-less too. The S3 runs (lane B)
are unaffected: their riders passed at both spaces (L2: (a) 0.4199,
fplus 0.4198, fplus_b 0.4197; L3: (a) 0.4211, fplus 0.4008, fplus_b
0.4028), and they continue under the frozen instrument. The shift's
short-row sliver (rows of length 17 or 18, where the shifted label lands
on the aligned or offset-1 label) is EMPTY on the S1 test split: every
test row is at least 36 tokens long, 1604 of 1680 rows are exactly 256,
and 4080 of 61030 test anchors (6.69%) wrap.

Disclosure of what was seen before this registration was pinned: the six
S1 shuffled rows above with their per-prompt cluster counts (six prompts
printed); the individual test accuracies of the 30 trained S1 L2 cells
and of the S3 cells through 56/75 as they scrolled in the lane logs (no
margin, D, Mt or Mn_r was computed from them, and the author attests to
not having subtracted any pair of them — the S1 state file holds the L2
gate-cell accuracies from which D follows by subtraction); the OQ-17 L1
rider values (leg-2 excess +0.0008 / +0.0024 / -0.0005 / -0.0006 on S1 /
S1-r / S3 / S3-r, all near the majority rate); the S1 L3 group sizes
(one mega-group of 455/510); and the wrap fraction of the 17-shift at
offset 2 on the S1 primary harvest (6.7% of anchors, 6.7% of test
anchors, computed as design input). Seen AFTER the pin, from the one-cell
smoke (results/smoke/oq18_rider_diag_smoke.json, gitignored): the
shuffled (a) L3 seed-0 cell reproduced its state row exactly (abs_diff
0.0, epoch 1), predicts the majority class on every test anchor
(q_majority 1.0), E identically 0; the wrapped anchors' shifted-label
majority rate is 0.5336 against 0.5650 on the non-wrapped anchors. Also
in the tree during the runs, invisible to the tracked-only attestation:
three untracked OQ-19 files (src/sideband/real/oracle_replay.py,
tools/run_fullfree_oracle.py, tests/test_fullfree_oracle.py), never
imported by any OQ-18 or diagnostic process.

## Why the fired leg can be wrong about a "leak", stated before measuring

The rider's shuffle is a fixed 17-position circular label shift within
the row (tools/run_probes.py SHUFFLE_SHIFT = 17): the "shuffled" label at
(row, anchor a, offset 2) is the TRUE label at position a + 1 + 17 of the
same row, wrapping to the row's first positions for the last 18 anchors.
Leg 2 asks whether the aligned slots block predicts that 17-ahead label
better than the arm without it. Three mechanisms can raise a raw
shuffled accuracy:

1. PREDICTION-MARGINAL DRIFT. Under mostly-noise labels a linear probe's
   test accuracy is dominated by how much of its prediction mass sits on
   the majority class; both fired arms sit far BELOW the majority rate
   (fplus -0.045, fplus_b -0.032), stopped at different epochs (4 vs 18).
   A difference in drift toward the majority predictor is not
   information about the shifted label. The OQ-17 disclosure already
   noted that a high-dimensional shuffled fplus sits below the floor; at
   the lopsided L3 lens the deficits are three to four times larger
   than at L2.
2. PROMPT-INDEPENDENT POSITION / OCCUPANCY INFORMATION. Slot occupancy
   grows along the row; the wrapped anchors (6.7%) draw their shifted
   label from the row's first positions, whose class mix differs.
   Information of this kind is shared by the equal-dims corrected twin
   (another prompt's row at the same anchor index), so the gate readout
   D = fplus_b - fplus_r is immune to it by construction — but leg 2 as
   registered is dims-asymmetric (fplus_b against fplus) and has no twin.
3. CONTENT TRANSFER. The aligned block predicts the row's own 17-ahead
   label beyond its equal-dims twin and beyond the marginals. This is
   EITHER a pipeline leak (a non-causal block: features at anchor a that
   depend on tokens after a) OR persistent row-level topic information in
   the slots block that hz's linear readout does not expose — and this
   instrument cannot separate the two. Phase-3's rider R2 (docs/
   BLUEPRINT.md, "rider R2") already states that a probe can legitimately
   learn per-prompt label COMPOSITION, which the shift preserves, and
   OQ-18's own licensed SURVIVES sentence is about "coarse future-TOPIC
   information beyond the anchor's own state" — at the S1 L3 lens (56%
   mega-group) topic transfers 17 positions trivially. The registered
   rider treats BOTH as disqualifying: a design collision between the
   rider and the OQ-18 question, disclosed here and NOT rerouted (a
   CONTENT-TRANSFER read leaves S1 label-less exactly as the registered
   text says). Separating the two would take a causal-prefix audit of
   the slots block (re-run the anchor forward on the prefix [0..a] for a
   sample of test anchors and compare the stored slot vectors bitwise);
   that audit is NOT part of this diagnostic and is not authorized here.

Why the twin-referenced dependence excess is the right statistic and is
not weaker than the fired leg where it matters: a raw shuffled accuracy
is chance(q, p) + E, where chance = sum_c q(c) p(c) moves with the
prediction marginal q ALONE (a drifted reader changes it with no
dependence) and E is the dependence beyond the marginals. dE_br = E_b -
E_r is the D-matched control — the same twin, the same reference, read
at the shifted label. A non-causal block shows in dE_br because the twin
lacks it, so the E leg catches every leak the raw leg catches and is
sharper under a drifted reader; what it no longer sees — marginal drift
and twin-shared position information — are non-leaks. What this
instrument therefore IS: a position-specificity test of the aligned
block at the shifted label. What it is NOT: a pipeline-leak test.

## Instrument

tools/run_oq18_rider_diag.py (new, untracked until committed with the
payload), tests/test_oq18_rider_diag.py. It reuses the frozen OQ-18
instrument's data path, label spaces, hz moments (asserted equal to the
committed OQ-17 sha), per-seed derangements and arm factories, and the
Phase-3 trainer with full_eval=True — the prediction dump the K-3 arc
registered, asserted by tests to leave the training trajectory and the
default return values byte-identical. Out path results/real/
oq18_rider_diag_s1.json + .state.jsonl (never a registered OQ-18 out
path; --only smokes go to results/smoke/ only).

## Cells (S1 primary harvest results/real/harvest_shadow; offset 2; linear; SHUFFLED = the registered 17-shift)

- L3_concept_groups_v1: arms (a), fplus, fplus_b, fplus_r x train seeds
  0, 1, 2 — 12 cells. Seed 0 re-trains the three registered rider cells
  in-process (their state rows are the tie) and adds the missing
  equal-dims twin; seeds 1 and 2 ask whether the fire replicates across
  train seeds.
- L2_concept_k512: arms (a), fplus, fplus_b, fplus_r x seed 0 — 4 cells,
  REPORTED context only (the space where leg 2 passed); L2 enters no
  branch. Under B its seed-0 amended-leg value decides whether the S1
  resume is launched (Consequence, item 2), because the amended
  instrument's L2 rider cells are this construction at these seeds.
16 cells; every cell stores, per test prompt and split by the wrap flag
(shifted index >= row length), the anchor count, the correct count, the
prediction histogram and the shifted-label histogram over the space's
classes. Those histograms are the evidence: the payload's statistics
reproduce from the state file.

## Readouts (pinned)

For arm X on a prompt set (per-prompt counts summed over the seeds in
the pool, the house estimand): acc_X = correct / N; q_X(c) = the
prediction marginal; p(c) = the shifted-label marginal (identical across
arms — asserted per prompt and seed); chance_X = sum_c q_X(c) p(c); the
DEPENDENCE EXCESS E_X = acc_X - chance_X (accuracy beyond what the two
marginals explain; exactly 0 for a constant predictor, which is what the
shuffled (a) cell is at both spaces; the numerator of Cohen's kappa, whose
exact null is the pooled label permutation). E can be positive without
anchor-level dependence through per-prompt label composition (q_i and
p_i co-varying across prompts) — legitimate per Phase-3 R2, available to
all three arms through hz, and cancelling in dE_br. Paired differences
between arms use the same prompts. CI95: cluster bootstrap over the 30
test prompts, n_boot 2000, seed 0, percentile, all marginals recomputed
inside each resample (deterministic; own generator). Per-seed points and
CIs reported beside every pooled statistic.

At S1 L3:
- R-a leg2_raw per seed: acc(sh fplus_b) - acc(sh fplus); the registered
  fire REPRODUCES if the seed-0 value exceeds the 0.01 band; whether
  seeds 1 and 2 exceed it is reported (replication across train seeds).
- R-b X_raw = acc(sh fplus_b) - acc(sh fplus_r), per seed and pooled with
  CI (the equal-dims raw comparison leg 2 lacked).
- R-c E_X per arm, pooled with CI, per seed; q_X(majority) per arm.
- R-d dE_bf = E_b - E_f; dE_br = E_b - E_r; dE_fa = E_f - E_a (leg-1
  analog); dE_rf = E_r - E_f; each pooled with CI and per seed.
- R-e wrap split: acc, chance and E per arm on wrapped and non-wrapped
  anchors, with CIs; the shifted-label majority rate on each.
- R-f determinism: |acc(re-trained seed-0 cell) - acc(state row)| for the
  six registered shuffled cells (three per space); REPRODUCED at <= 1e-9,
  which on test_acc means an identical correct COUNT (granularity
  1/61030), not identical predictions.
- R-g best epoch per cell.
At S1 L2: the same statistics for seed 0, reported.

## The amended leg (defined here because branch B and the consequence use it)

At a (fplus_b, fplus_r) shuffled cell pair — seed 0 unless stated — the
AMENDED LEG 2 FAILS if dE_br > 0.01 OR (dE_br's CI95 lower > 0 AND dE_br
>= +0.005); otherwise it passes. The band is the registered rider's; the
second clause is branch A's own definition of content transfer, so the
leg can never pass numbers this document elsewhere calls the transfer
signature.

## Branches (pinned; S1 L3, pooled three-seed statistics; L2 never enters)

Precondition T (tie to the registered fire): the re-trained seed-0
leg2_raw exceeds 0.01. If T fails: INDETERMINATE-NOT-REPRODUCED — the
registered fire did not reproduce in-process; no amendment; S1 stays
label-less; the determinism readout is disclosed. TIE SCOPE: if T holds
but any of the six re-trained registered cells fails the 1e-9 test, the
diagnosis is "of the construction, not of the registered run" and the
verdict says so (tie_scope = construction); with all six reproduced it
is of the registered run.

- A CONTENT-TRANSFER: pooled dE_br CI95 lower > 0 AND pooled dE_br point
  >= +0.005. The aligned block predicts the 17-ahead label beyond its
  own equal-dims twin, beyond the marginals: content transfer — a
  pipeline leak or persistent row-level topic information, not
  separable by this instrument; the registered rider treats both as
  disqualifying. QUALIFIER: A carries "concentrated on wrapped anchors
  (row-end / row-opening recall), not row-level content" unless dE_br on
  the NON-WRAPPED selection is itself CI95-lower > 0 and >= +0.005.
  Consequence: no amendment reads a label; S1 remains label-less under
  OQ-18; S3 concludes as registered (its riders passed); the next step
  is the causal-prefix audit named above and the user's decision —
  neither is authorized by this document. Reportable as "at the L3
  group lens the aligned slots block predicts the label 17 positions
  ahead beyond its equal-dims twin and beyond (a) + TOK + hz"; it
  licenses no existence sentence.
- B AMENDABLE: not A, AND the amended leg PASSES at seed 0, AND pooled
  dE_br <= 0.01. Mechanism sub-reading (reported, no branch weight):
  MARGINAL-DRIFT if dE_bf's CI95 includes 0; TWIN-MATCHED if dE_bf's
  lower > 0 — dependence the twin shares: position / occupancy, or any
  same-marginal sparse block de-compressing the reader's use of hz's
  composition knowledge (E is not compression-invariant);
  DRIFT-DOMINANT if dE_bf's upper < 0 (raw accuracy up, dependence down:
  the purest drift signature). QUALIFIERS carried by B, each pinned:
  POWER — if the seed-0 dE_br CI95 half-width exceeds 0.005, "underpowered
  against a materiality-sized excess"; COMPRESSION — if q_maj(fplus_b) -
  q_maj(fplus_r) > 0.02 at seed 0, "no EXPRESSED dependence at this
  reader: the aligned arm sits closer to the majority predictor than
  its twin by that much" (E <= (1 - q_maj)(1 + p_maj)); TWIN-ANOMALY — a
  CI-clear NEGATIVE pooled dE_br is disclosed like an Mn_r fire; X-RAW —
  X_raw at seed 0 is quoted with the sentence "the registered statistic,
  twin-referenced, would also have passed" if X_raw <= 0.01, else "would
  still have fired" (the amendment is then a change of statistic, not
  only of reference, and rests on the dominance argument above).
- C INDETERMINATE: anything else — the amended leg fails at seed 0
  without A firing on the pooled statistics, or the pooled point sits
  above the band with a CI including 0. No amendment; S1 stays
  label-less; report.

## Consequence under B (pinned now; implemented only after the read)

A DATED AMENDMENT to the OQ-18 registration (docs/BLUEPRINT.md block,
OPEN_QUESTIONS.md OQ-18), written after this diagnostic is read and
COMMITTED before any amended cell trains:
1. Leg 2 of the leak rider becomes the AMENDED LEG defined above,
   computed at the rider cell (off2 / linear / seed 0) from per-prompt
   histograms stored in the state row, with its CI. The registered raw
   leg 2 is REPORTED per harvest as registered_leg2_raw with its pass /
   fail (FIRED at S1 primary L3), beside X_raw and its sentence. Leg 1
   is unchanged. The rider gains a fourth shuffled cell (fplus_r) per
   space; all four shuffled cells are trained with the prediction dump;
   a state row without histograms is RE-TRAINED, never reused (the
   fired run's three L3 and three L2 shuffled rows stay in the S1 state
   file as the record of the fire). The amended leg is a KILL at every
   harvest exactly as the original was.
2. The amended instrument is a NEW FILE (tools/run_fullfree_coarse_
   amended.py, importing the frozen instrument), so that tools/
   run_fullfree_coarse.py stays byte-identical on disk while the frozen
   S3 runs are in flight (their payloads hash the instrument file at
   write time). It applies to ALL FOUR harvests (symmetry; it adds a way
   to not read, never a way to read more). S1 primary RESUMES from its
   state file — its 33 trained L2 cells are reused (trainer, blocks,
   seeds and labels byte-identical; licensed here, resumed_cells
   recorded nonzero for exactly these resumes); the resume is launched
   ONLY IF this diagnostic's L2 seed-0 cells pass the amended leg (they
   are the amended instrument's L2 rider cells), otherwise S1 is
   label-less under the amended rider as well and nothing is resumed.
   S1 replication runs fresh. The S3 primary and replication payloads
   written under the frozen instrument are preserved under
   *.rider_v1.json names and NEVER concluded (no v1 label is read);
   their runs are resumed under the amended instrument to (re)train the
   shuffled cells and re-emit the payload. If the amended leg FAILS at
   an S3 harvest, S3 is label-less and the record says, in these words,
   "a post-hoc kill applied to a completed registered run whose label
   was never read". COMMIT ORDER: the amendment, the amended instrument,
   this document, the diagnostic payload and state file, and the S1
   state file at the sha the diagnostic payload records (the resume
   APPENDS to that file) are committed BEFORE any amended cell trains;
   HEAD therefore advances under the in-flight frozen S3 runs, whose
   payloads then record the later HEAD with a clean tracked tree and the
   frozen instrument's sha — disclosed, not hidden. The .gitignore gains
   the negation for results/real/oq18_rider_diag_s1.json.state.jsonl.
3. Every label read under the amendment, and every F-15 / K-2 STATUS
   line produced under it, carries the sentence, in the repo's precedent
   words: "a post-hoc reroute around a fired kill condition: the leg
   that fired was replaced after the fire by a twin-referenced
   dependence-excess leg whose S1 seed-0 values at both spaces were
   known from the diagnostic payload when the amendment was written; it
   is a fresh test only at the other three harvests" — followed by the
   dominance argument in one sentence, the mechanism read, X_raw at seed
   0 with its sentence, and the POWER line where it applies. What makes
   the amendment legitimate rather than merely disclosed: the E leg
   dominates the raw leg on leaks (it sees every non-causal block the
   raw leg sees, and more under drift), and what it drops are non-leaks.
   OQ-18's honest prediction, gate, labels, readouts and consequence
   rules are otherwise unchanged; the amendment touches the rider only.
Under A or C nothing is resumed; the S3 runs complete and conclude under
the frozen instrument (their riders passed), S1 is INCOMPLETE for OQ-18,
and the user decides the next step.

## Honest prediction (pinned before any diagnostic cell trained)

T holds (the trainer reproduces the state rows to 1e-9 on this box —
probable; the in-flight S3 rider rows match the BLUEPRINT smoke (2) to
four decimals with the same selected epochs, the best cross-process
evidence available). Branch B with mechanism MARGINAL-DRIFT: every E at
S1 L3 within +/-0.005 of zero for fplus, fplus_b and fplus_r; dE_bf's CI
includes 0; dE_br within +/-0.005 with a CI including 0; X_raw at seed 0
within +/-0.01 (the equal-dims twin drifts like the aligned block, not
like fplus — weakly held); leg2_raw at seeds 1 and 2: at least one below
the band (weakly held). Surprise line, symmetric: a CI-clear dE_br >=
+0.005 (branch A) would mean the aligned slots block carries row-level
information beyond the anchor's own state that transfers 17 positions —
reportable, disqualifying for OQ-18 at S1, and licensing no existence
sentence; a TWIN-MATCHED reading would mean leg 2 as registered was
measuring information the gate readout already controls for.
(Dated note, 2026-09-07, pre-read critic round, before any statistic was
computed: the clause "every E ... within +/-0.005 of zero for fplus" is
WITHDRAWN as uninformative — E_f is expected positive through per-prompt
composition knowledge, legitimate per Phase-3 R2; the predictions on
dE_bf, dE_br, X_raw and the branch stand as written.)

## Evidence

results/real/oq18_rider_diag_s1.json (payload: statistics, branch,
qualifiers, registration sha, pre-round registration sha, instrument
sha, git attestation, harvest npz shas, moments sha, derangement shas,
the fired S1 state file's sha) and results/real/oq18_rider_diag_s1.json
.state.jsonl (per-cell rows with the per-prompt histograms; sha-header
bound to the harvest). Committed with this document in the amendment
commit (under B) or with the S3 landing commit (under A / C).

## Pre-read critic round (2026-09-07, sideband-critic; applied after two diagnostic cells had trained and while the third was training, before any statistic was computed)

The document's pre-round sha256 was
1904dd6245e090e8117e4e7d37428004a5c54b3697549e5e283ca4baedb676b8 (the
value the smoke payload and the stopped run's start recorded). The
running diagnostic was STOPPED and RESUMED from its state file so that
the payload records this document's post-round sha: the completed cells
are reused (their training does not depend on this text) and
resumed_cells is recorded nonzero for that reason — licensed here; the
tool's --resume clause names this case. Applied: B1 mechanism 3 renamed
CONTENT TRANSFER with the pipeline-leak / row-topic non-separability
and the design collision stated; the dominance paragraph and the
"position-specificity test, not a pipeline-leak test" sentence added;
branch A renamed CONTENT-TRANSFER. B2 the amended leg made coherent with
A (fails on point > 0.01 OR CI-clear >= +0.005) and B redefined to
require it at seed 0. B3 the reroute wording pinned verbatim for every
derived sentence, the X_raw sentence and the POWER qualifier added, the
dominance argument named as what makes the amendment legitimate. C4
this section (sha mechanics, resume license). C5 tie scope. C6 no v1
label is read; the S3 post-hoc-kill wording; the S1 resume precondition
on the diagnostic's L2 cells; the commit order and the state-file sha;
the .gitignore negation; the new-file amended instrument (so the frozen
instrument's on-disk hash stays true for the in-flight runs). C7 the
wrap qualifier on A and the compression qualifier on B. C8 histogram-
less rows re-trained. N9 the E_f composition note and the withdrawn
prediction clause. N10 C's unreachable example removed; MIXED renamed
DRIFT-DOMINANT; the twin-anomaly disclosure; TWIN-MATCHED reworded. N12
the disclosures (smoke observations, the no-subtraction attestation,
the untracked OQ-19 files, the empty short-row sliver). The L2 leg-2
excess rounded correctly to +0.0024. Not applied: the causal-prefix
audit (named as the next step under A, not authorized here).

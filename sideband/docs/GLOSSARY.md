# Glossary

House terms, prefixes, decisions, kill criteria, open questions, and the
economics bars of the sideband repo, in one place. Written 2026-09-05 at
evidence commit 2e44105 (the STAGE-A FREEZE; HEAD 8542ef5 is one later code-hygiene commit that touches no registered text or result; the F-23 commit on top adds one result file, the OQ-16 dated erratum and the closing finding, and this glossary's dated F-23 clauses) from the registered documents (FINDINGS.md, DECISIONS.md,
OPEN_QUESTIONS.md, docs/WHY_THIS_DIES.md, docs/ECONOMICS.md,
docs/BLUEPRINT.md, docs/PRIOR_ART.md) and the committed result payloads
they cite. Every number below is copied from one of those files and names
its source the first time it appears in an entry; nothing here is a new
measurement. Where the registered text and a later result disagree, the
entry says so rather than reconciling them.

Dated note 2026-10-14 (the public cut's front-doors lane): the A-Z gained a
headed entry for each of these labels of the record (ABSORBED, ADDRESS-BEYOND-
TOKEN, BAR-RESOLVED@210 and RULE-LEAKS@30, EQUAL-DIMS-ONLY, FLOOR-MATERIAL,
H-ABSORBS, K-2-ISOLATED, LEAD-TIME-ABSORBED, NOT-SHOWN, PREFETCH-HEADROOM,
R2-FALLBACK-SURVIVES, SPLIT, SURVIVES-STRONGER, TWIN-ROBUST), each stating its
registered rule, every number and quoted phrase in them copied from
FINDINGS.md, docs/WHY_THIS_DIES.md or the registration in docs/BLUEPRINT.md as
they stood on that date; the K-2 row, the Finding (F-N) entry and the Mega-
group lens entry gained dated clauses through F-28. The entries written on
2026-09-05 are otherwise unchanged.

The project in one sentence: a speculative-decoding drafter is steered from
a *sideband* - a narrow channel carrying only what a weight-serving device
could observe about the target model's forward pass (expert ids, weight-slot
addresses, page ids), never activation values - and the repo asks whether
that channel carries anything the drafter does not already get for free,
and whether it converts into more emitted tokens per verify call.

Status vocabulary used throughout, in the repo's own sense:

| word | meaning here |
|---|---|
| shown | a registered gate or finding says so, with a CI clear of zero on the registered estimand |
| not shown | the registered test ran and did not clear its bar (a null), or the claim was never put to a registered test |
| unpriced | a quantity the repo names but has not measured, or cannot separate under the registered readout; no magnitude is licensed, and for the standing example ("beyond p" after DR-4) the outcome licenses neither a positive block-aligned share nor its absence - "not separable from dilution under the registered readout" (docs/BLUEPRINT.md DR-4 OUTCOME) |
| qualified | shown, but only in a narrower sense than the plain words suggest, and the qualifier is part of the claim |

No wall-clock or speedup claim exists anywhere in this repo (see Tokens/call
and K-5): the currency is emitted tokens per verify call, and, one layer
down, probe accuracy margins.

Repository: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`, folder sideband/. License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).

---

## Prefixes

| prefix | what it names | where it lives |
|---|---|---|
| F-N | a finding (F-0..F-26 at HEAD on 2026-10-01; 27 entries; F-0..F-1 verifier exactness, F-2..F-9 synthetic world, F-10..F-26 real models, of which F-24 / F-25 are the full-free re-tests and F-26 the OQ-9 prefetch datum with a dated status line of 2026-10-01). Each carries `- date:`, `- regime:` and `- source:` lines (F-0..F-18 also `- finding:`, and all of those but F-1 `- caveats:`; F-19..F-22 use labelled VERDICT/disclosure lines instead, F-21/F-22 keeping a `- caveats:` line; F-24..F-26 carry `- finding:` and `- caveats:` lines, F-25 also `- amendment:` and `- post-hoc reading` lines, F-26 a `- post-hoc reading` line and a dated `- status` line); the lint refuses an entry without regime + source (D-4) | FINDINGS.md |
| D-N | a standing decision (D-1..D-11); reversing one needs a dated entry | DECISIONS.md |
| K-N | a kill criterion (K-1..K-7): a pre-registered condition under which the project or a phase dies, with the phase that tests it and the salvage; OUTCOME/STATUS blocks are appended, never rewritten | docs/WHY_THIS_DIES.md |
| OQ-N | an open question (OQ-1..OQ-19 at HEAD on 2026-10-01; OQ-12 has two headers, the resolution and the original statement); status notes are appended as dated parentheticals | OPEN_QUESTIONS.md |
| E1..E12 | the STAGE-E ENGINEERING CLARIFICATIONS of the K-3 Attempt-#1 live instrument (dated 2026-09-02, before any stage-E code); see Stage-E clarifications | docs/BLUEPRINT.md |
| DR-N | a Stage-R POST-GATE DIAGNOSTIC in the OQ-16 arc (DR-1..DR-4 ran; DR-5 is forbidden under the hard stop); all NON-CRITERION | docs/BLUEPRINT.md, F-22 |
| DI-1 | the Stage-I post-gate diagnostic in the OQ-15 arc: the five-seed stale-target control | docs/BLUEPRINT.md, F-20 |
| P1 | the post-hoc topic-state diagnostic (S1: F-16; S3 analog: F-18) | docs/BLUEPRINT.md |
| R1 / R2 / R3 | Phase-3 probe-run riders: harvest fidelity, label shuffle, split hygiene | F-15, F-17 |
| C1..C4 | the OQ-15 Stage-C arms (vanilla, draft-confidence, head_free, head_tel) = runner arms 1, 2, 6, 7 | F-21 |
| arms 1..10 | the K-3 lane's runner arm numbers: 1 vanilla gamma-4; 2 draft-confidence; 3 (a)-probe; 4 (c)-probe telemetry; 5 fixed gamma-6; 6 head_free; 7 head_tel; 8 oracle_h; 9 free_inject; 10 tel_inject | F-19, F-21, docs/BLUEPRINT.md STAGE-A FREEZE |
| M2 / M3 / M4 / M2n / M2noise | the P1 readouts (see that entry) | F-16, F-18 |
| S1 / S2 / S3 | telemetry sources (compute-tier tap / KV pages / MoE router addresses) | D-1, K-2 |
| L1 / L2 / L3 | probe label spaces (concept_k16 / concept_k512 / concept_groups_v1) | F-15 |
| A0 / A1 | the two rungs of the Stage-A GPU ladder | docs/BLUEPRINT.md STAGE-A FREEZE |

## The three layers

The repo keeps three questions apart and never converts between their
units. Conflating them is the named failure mode of the whole arc.

| layer | question | unit | kill criterion | state at evidence commit 2e44105 |
|---|---|---|---|---|
| EXISTENCE | does telemetry carry information about the target's future beyond what the drafter already has for free? | probe top-1 accuracy margin, (c)-(a) | K-2 | shown at S1 (F-15, replicated) and at S3 (F-17, replicated); mechanism not topic-state at the histogram-family level (F-16, F-18; richer prefix families open); S2 never run |
| CONVERSION | does that information become more emitted tokens per verify call at matched drafting budget? | tokens/call delta vs every comparator | K-3 | not shown: K-3 fired at Attempt #1 (F-19); fold-back #1 was a conversion-mode null (F-20, F-21); fold-back #2's actuator stage (Stage A) was frozen and then voided as a telemetry test by the 2026-09-05 erratum (F-23) before any run |
| RECONSTRUCTION | how much of the anchor hidden state h_a (SD^2's steering vector) is linearly recoverable from the address stream? | standardized MSE, R^2, centered cosine | none (OQ-16 partition) | qualified: Stage R PASS (F-22); about a quarter of h_a linearly (DR-1); a free hashed encoding of p's top-32 token ids recovers at least as much (DR-2); telemetry plus that encoding beats the encoding alone (DR-3); "beyond p" unpriced (DR-4); F-23 (2026-09-05): the target is an exact linear function of the anchor's full p, free under D-5, so the lane is closed by dated erratum with no partition branch claimed, mechanism TARGET-FREE |

Probe-margin units (existence) and acceptance units (conversion) are
different layers: docs/ECONOMICS.md section 1 states that no rule in the
repo converts one into the other. Reconstruction (OQ-16) is a third layer
again: F-22 wins at state identity while the same stream lost at
acceptance prediction (F-20) and at conversion (F-21), and the finding says
no shared bug is needed to explain that.

A fourth thing, wall-clock (K-5), is not a layer the repo has measured at
all.

---

## Decisions D-1..D-11 (from DECISIONS.md; all dated 2026-08-28, status adopted)

- **D-1 Telemetry must be input-dependent by architecture.** A dense hashed matmul touches every weight slot on every forward, so its address set says nothing; real telemetry v1 is MoE expert routing, and the dense stand-in is a shadow sketch on an INTACT model. Never corrupt the model to harvest telemetry. Scope note (2026-08-30): read-only taps on a compute tier's own activations are inside the premise; anything that changes what the observed target computes is forbidden; modifying the draft's q is fair game; the observability constraint is read as "almost nothing crosses the wire"; K-2 is evaluated per source.
- **D-2 Causality discipline.** Steering information for a block may only come from positions at or before the last verified position; sidecar labels come from the target's OWN causal continuation; leaky oracles are explicitly named as such (D-2's text names oracle_concept_now; F-14's oracle_nextp and the Stage-A oracle_h are named the same way) and exist only as ceilings.
- **D-3 Single source of truth for verifier math.** src/sideband/specdec.py is the only implementation of accept/reject/residual; the HF adapter converts torch logits to numpy and calls spec_step; anyone re-implementing it "for speed" must first make the numpy tests pass against their implementation.
- **D-4 Findings carry regime + evidence, lint-enforced.** Every FINDINGS entry has `- regime:` and `- source:` lines with existing evidence paths; tools/lint_findings.py enforces it; a finding cited outside its regime is a bug.
- **D-5 The free-information baseline is mandatory.** Any telemetry-steering claim is compared against free_lastp (steering from the target's distribution at the last verified position); without it a result is "dominated-baseline theater"; synthetic world: provably identical (F-6); real models: beating it is the existence question (OQ-1).
- **D-6 Paired comparisons; telemetry on an isolated RNG stream.** Policies are compared at identical seeds so trajectories are paired; a policy that READS telemetry draws from its own generator so reading cannot perturb the shared draft/verify trajectory (this coupling once silently equalized experiment e05's v0 across all K).
- **D-7 Predictions and gate comparisons live in concept space.** The glue/function bucket is excluded from BOTH sides of any bucket argmax used for prediction or disagreement gating; otherwise every position looks like a disagreement and the F-3 tax returns. Real-vocab analog: OQ-4.
- **D-8 Steering mechanism: soft bias + disagreement gate + confidence gate.** Additive log-space bias only (hard masks are the beta-to-infinity pathology measured at -0.18 acceptance in F-3); disagreement gating on by default (F-3); confidence gating on by default (F-5); defaults beta about 3 gated, tau about 0.5 scaled to decoder quality.
- **D-9 Analytic per-position acceptance is the headline metric.** Record E[1 - TV(p, q_steered)] at every DRAFTED position (unconditional, variance-reduced); empirical acceptance-by-offset conditions on SURVIVING to that offset and answers a different question; report both, never conflate. Wall-clock claims additionally need a cache-correct harness; the v1 HF adapter recomputes prefixes and is valid for acceptance only. Dated erratum 2026-10-16: that last clause was false when this entry was written (2026-09-05); the adapter has cropped KV caches by default since b1dae57 (2026-08-29), and the ban's ground is the absence of a benchmark harness (DECISIONS.md D-9, dated note 2026-10-16).
- **D-10 Steering mechanism v2: centered posterior bias + disagreement gate.** Default is steering.posterior_bias: boost each concept bucket by beta*(P(b) - 1/C), glue 0; it dominates argmax+tau at every sideband width and at the oracle level (F-7) because the optimal bias is BIDIRECTIONAL; centering subsumes the confidence-tau gate; the disagreement gate remains mandatory. Supersedes D-8's DEFAULT, not its principles. Dated note 2026-10-16: the decision's default, not the code's: sideband.pipeline.run_simulation keeps steer_mech="argmax" as its parameter default, and e03, e04 and e05 (F-3, F-4, F-5, quoted by F-6) ran argmax (D-10's dated note; pinned by tests/test_record_claims.py).
- **D-11 Ceilings and baselines must be mechanism-matched.** Recovery denominators use an oracle running the SAME mechanism as the policy (the posterior sidecar exceeded 100% recovery against the argmax oracle in F-7 - a statement about the wrong ceiling); corollary: under the posterior mechanism run BOTH free variants, soft (bucket masses of p_last) and SHARPENED (one-hot at argmax p_last).

---

## Kill criteria K-1..K-7 (from docs/WHY_THIS_DIES.md; status verified against FINDINGS.md)

| K | condition (short) | status at HEAD | decided / qualified by |
|---|---|---|---|
| K-1 | rejections are not cross-bucket (< about 25% at every sane k) | did not fire | F-10 (2026-08-29); reopen trigger did not fire either, F-11 |
| K-2 | telemetry adds nothing beyond free information at offsets >= 2 | survived at S1 and at S3 against the 657-summary PROXY (F-15, F-17; the later readouts F-20 / F-22 qualify but do not re-fire it); dated 2026-09-06 (F-24): FIRED at the registered reader of the full free baseline at the pinned L1 cells of both sources (no MATERIAL +0.005 equal-dims margin; the stronger-reader residual is the one named path to overturn); dated 2026-09-14 (F-25, read under the 2026-09-07 rider amendment - a disclosed post-hoc reroute around a fired kill condition, a fresh test only at the other three harvests): L2 FIRED at both sources, S1 L3 and S3 L3 OPEN at the full-free level (NOT-SHOWN / SPLIT); S2 untested; dated 2026-10-05 and 2026-10-09 (F-28, the reader-and-lens re-test at S3): through the balanced lens at the registered reader S3 L3 reads ABSORBED where the lopsided lens read SPLIT; under the stronger readers R-N, R-T and R-L at the S3 gate cells the FINAL word is K-2-ISOLATED - the S3 L1 kill stands at the registered reader, S3 L3 stays OPEN (SPLIT) at the registered reader, the two SURVIVES-STRONGER cells (R-N and R-L at the lopsided L3) are EQUAL-DIMS-ONLY at a lens that never decides a reopen, "one more family of readers, not K-2's universal"; S1 not run; dated 2026-10-17 (F-29, the S1 reader re-test): under the same three readers at the S1 gate cell R-N (hz-rescaled) ABSORBED; R-T (two-tower) ABSORBED; R-L (longer budget) ABSORBED, the S1 word K-2-NOT-OVERTURNED-AT-S1 (under readers R-N, R-T and R-L at S1; one more family of readers, not K-2's universal); the S1 kill of 2026-09-06 stands as a statement about the registered reader | F-15, F-16 (S1); F-17, F-18 (S3); qualifiers F-20, F-22; F-24, F-25 (registered-reader scope); F-28 (the balanced lens and three stronger readers at S3); F-29 (the same three readers at the S1 gate cell) |
| K-3 | probe margins do not convert to acceptance | FIRED at Attempt #1; fold-back #1 conversion-mode null; fold-back #2 Stage R PASS, then closed by dated erratum with Stage A void as a telemetry test | F-19; F-20, F-21; F-22; F-23 |
| K-4 | the sideband is too narrow for the decoder it needs | untested: no finding rules on it | adjacent evidence only: F-5 (synthetic shape), docs/ECONOMICS.md section 3 widths |
| K-5 | wall-clock eats the win | untested: nothing in the repo measures wall-clock | D-9 caveat; every real finding carries a "no wall-clock claims" line |
| K-6 | the premise's economics do not exist | untested / open; reframed per lane by docs/ECONOMICS.md section 4 (dated 2026-09-15 and 2026-10-01, F-26 and its twin: still UNTESTED; the first datum is a next-forward expert-set hit-rate count on the OLMoE harvests, not bytes, latency or a boundary argument; 2026-10-04, the horizon read: still UNTESTED, its lead-time datum in forwards — LEAD-TIME-ABSORBED on both harvests, the address stream over the strongest free arm R2 built horizon 2 +0.0178 [+0.0138, +0.0223] / +0.0153 [+0.0113, +0.0203]; horizon 3 +0.0173 [+0.0129, +0.0223] / +0.0135 [+0.0093, +0.0187]; horizon 4 +0.0149 [+0.0105, +0.0198] / +0.0104 [+0.0062, +0.0154] (primary / replication; every one of the six label readings NOT-SHOWN by the rule)) | no finding addresses the boundary argument; the section 6 skeleton is left as registered and a dated section 6a (2026-09-05) fills it; K-6 STATUS lines of 2026-09-15, 2026-10-01, 2026-10-02, 2026-10-03 and 2026-10-04 in docs/WHY_THIS_DIES.md |
| K-7 | the glue-bucket tax cannot be neutralized in real vocab space | not fired as written; the gate-health diagnostic FIRED and was re-routed to OQ-12 | F-11 (identification works); F-12 (gate open 93.6-94.0%); F-13, F-14 (granularity, not glue) |

Detail, with the numbers the status rests on:

- **K-1.** Pre-registered rule: KILL iff the prompt-cluster-bootstrap CI upper bound on cross-bucket RESIDUAL MASS is < 0.25 at EVERY k in {256, 512, 1024}; any CI intersecting [0.15, 0.35] requires a bf16 confirmation first (docs/WHY_THIS_DIES.md). Outcome (F-10): residual mass 0.778 [0.769, 0.787] at k=256, 0.812 [0.804, 0.820] at k=512, 0.863 [0.856, 0.870] at k=1024 over 11,287 rejections; no CI in the caution band; the 20-prompt bf16 arm agrees at 0.787 [0.764, 0.809]. The K-7-registered REOPEN trigger (concept-level CI upper < 0.25) also did not fire: F-11 concept-to-concept 0.565 [0.554, 0.575] / 0.610 [0.600, 0.621] / 0.674 [0.664, 0.684] token-level by k, 0.607 [0.597, 0.617] mass-level at k=512.
- **K-2.** Per-source verdict (D-1 scope note). S1 (F-15): the pinned L1/off2/linear replication triple re-fired at +0.0141 [+0.0081, +0.0203], all eight off2/off3 triples re-fired, offset 4 not established (horizon 2-3 tokens); F-16 rejects the topic-state explanation at the histogram level. S3 (F-17): pinned L1_olmoe_k16/off2/linear +0.0147 [+0.0113, +0.0182] primary, +0.0173 [+0.0133, +0.0221] replication, the same 7 of 12 triples firing both runs; F-18 rejects topic-state at S3 too, with one real topic component at L3 about 1/10 of the tap's margin there. S2 (KV pages) never ran; docs/ECONOMICS.md section 5 settles it as off the K-3 critical path. Qualifiers from later arcs: F-20 finds no DEMONSTRATED block-aligned acceptance-relevant margin above free (a different target from K-2's registered future-concept probes); F-22 has telemetry CI-clear slightly below FREETOK at reconstruction (DR-2, -0.004792 [-0.007192, -0.002600]) but UNION above FREETOK (DR-3, +0.065180 [+0.062411, +0.067705]) and states it "does not re-fire K-2". Dated 2026-10-01: at the registered reader of the FULL free baseline K-2 FIRED at the pinned L1 cells of both sources (F-24; the 2026-09-06 STATUS) and at L2 of both (F-25; the 2026-09-14 STATUS, read under the rider amendment); S1 L3 and S3 L3 are OPEN at the full-free level (NOT-SHOWN / SPLIT); the survived verdicts above stand against the 657-summary PROXY.
- **K-3.** Kill text (docs/ECONOMICS.md section 5): delta over free_lastp indistinguishable from zero -> fold back; the fold-back count was widened on 2026-09-02 (FOLD-BACK COUNT AMENDMENT, docs/BLUEPRINT.md) to a pinned two-lane sequence, OQ-15 then OQ-16, with a cross-lane skip and a hard stop after #2. Attempt #1 (F-19): telemetry arm 4 vs vanilla +0.006860 CI95 [-0.015024, +0.025572] tokens/call against the +0.062 bar; vs the (a)-probe arm +0.006974 [-0.014909, +0.025690]; vs draft-confidence +0.048863 [-0.007393, +0.104327] with the budget guard breached (arm-4 drafted-per-emitted 1.317033 vs allowed 1.285681); every leg fails both statistical criteria. Fold-back #1, OQ-15: Stage I (F-20) gate PASS mechanically at delta_noise +0.000763 [+0.000308, +0.001215] but pinned label ARTIFACT-DOMINANT under the five-seed stale-target control, and delta_free -0.00286 [-0.00322, -0.00252] CI-clear negative; Stage C (F-21) head_tel vs vanilla +0.002664 [-0.044719, +0.046727], vs head_free -0.081846 [-0.132484, -0.035567] -> CONVERSION-MODE NULL. Fold-back #2, OQ-16: Stage R (F-22) PASS at delta_noise +0.176469 [+0.130414, +0.251518] and delta_free +0.204984 [+0.153698, +0.288162], magnitudes inflated about 25% by a standardization pathology; DR-1 deployable margin +0.250784 [+0.239316, +0.261616]; DR-2 TOKEN-IDENTITY-NOT-EXCLUDED; DR-3 TELEMETRY-BEYOND-P; DR-4 COMPARATOR-TOOTHLESS. Stage A (SD^2-style injection) is AUTHORIZED, USER-GATED, frozen in docs/BLUEPRINT.md (STAGE-A FREEZE, 2026-09-05) and has NO GPU run at HEAD: results/real holds only oq16_stage_r* payloads. One registered stage remains before the hard stop.
- **K-4.** Adjacent evidence only. F-5 (synthetic): decoder holdout accuracy 0.16 (K=8) .. 1.00 (K=1024) slots, and gating turns harmful narrow decoders harmless - the SHAPE is the transferable claim. docs/ECONOMICS.md section 3 prices the real widths: S3 768/513 bits per token (id-list naive / set-coded), S1 1152/676, against SD^2's 65,536 bits per verified position (about 85-128x narrower at S3, about 57-97x at S1). OQ-5 (sidecar latency) and OQ-14(i) (which layers carry the signal) are unrun.
- **K-5.** The kill doc itself notes "NOTHING in v0.1.0 measures wall-clock"; CLAUDE.md bans wall-clock claims until a KV-crop fast path exists; docs/ECONOMICS.md section 6 leaves "sidecar latency measured? KV-crop fast path built?" unfilled; Lane A's K-5 residual (time the linear-probe sidecar inside a draft loop) has not been done. Dated note 2026-10-16: the KV-crop path exists (the adapter's default since b1dae57, 2026-08-29; see the KV cache entry's erratum); the ban now rests on the absence of a benchmark harness, and the sidecar timing is still not done.
- **K-6.** docs/ECONOMICS.md section 4 reframes it per lane: Lane A (software telemetry in MoE serving) has no device to justify but owns that the constraint is self-imposed in-lane; Lane B (hardware) needs BOTH (a) a K-3 win at the +0.044-acceptance operational bar AND (b) a named, defended deployment where the hidden-state vector cannot cross - "currently unanswered". (a) is unmet at HEAD; no finding addresses (b).
- **K-7.** Pre-registered glue rule: top-100 target-only frequency tokens, glue = shortest bucket prefix reaching 80% cover; gate-health diagnostic: open rate above about 0.8 is a warning. F-11: glue is concentrated and identifiable (2/2/4 buckets at k=256/512/1024 covering 82.3%/80.1%/80.0% of top-100 frequency mass); every alternative glue set keeps the concept-level CI lower bound >= 0.485. But F-12: the disagreement gate is open 93.6-94.0% of drafted positions in every gated arm, the confirmatory arm is -0.0098 [-0.0155, -0.0039], and the pre-registered 90%-cover re-test moved the open rate only 0.9393 -> 0.9361 - a GRANULARITY failure, not under-excluded glue. F-13: coarsening restores selectivity (open rate 0.55-0.56 at C=15) but all six arms land BROKEN; F-14: the coarse-k oracle ceiling is <= +0.0069 with a truth-gate rate of 15.9%. The kill doc's OUTCOME: "Either way it is not K-7's: glue identification and the gate's selectivity are both demonstrated fixable."

---

## Open questions OQ-1..OQ-19 (from OPEN_QUESTIONS.md; the OQ-17..OQ-19 rows and the OQ-9 status were added 2026-10-01; the OQ-7 status word dated 2026-10-15)

| OQ | question (short) | status in OPEN_QUESTIONS.md | answered / advanced by |
|---|---|---|---|
| OQ-1 | does real telemetry carry anything beyond the last verified p? (the existence question) | header reads "ANSWERED YES at source S1 (F-15, 2026-08-31); S2/S3 open", and the body's "what remains open" item (i) still calls S2/S3 untested - both predate F-17 (2026-09-01), which answered S3; neither sentence was updated in the committed entry (its last dated update is the F-16 note) | F-15, F-16 (S1); F-17, F-18 (S3); S2 unrun |
| OQ-2 | real cross-bucket rejection fraction | ANSWERED (F-10, 2026-08-29): 0.778/0.812/0.863 at k=256/512/1024 | F-10; glue share by F-11 |
| OQ-3 | real bucket-level persistence | no status line; measured in substance: p_same_bucket 0.02706469973283773 and mean run length 1.0149421233206144 at k=512 (results/real/bucket_persistence_k512.json, cited in F-12); 1.07-1.14 across coarse k (F-13) | F-12, F-13 (entry not updated) |
| OQ-4 | glue-bucket identification in real k-means space | ANSWERED (F-11, 2026-08-30); the problem moved to gate granularity (OQ-12) | F-11 |
| OQ-5 | hardware sideband width and sidecar latency budget | OPEN; width priced (docs/ECONOMICS.md section 3); latency never timed | - |
| OQ-6 | what fraction of SD^2's gain survives the observability constraint? | no status header; partially answered: h_a reference probe UNDEFINED at offsets >= 2 at S1 (F-15) and CI-crossing at off2 / CI-negative at off3-4 at S3 (F-17); reconstruction level (F-22): about a quarter of h_a linearly, and a free encoding of p's top-32 ids recovers at least as much; acceptance-level fraction unmeasured (Stage A unrun) | F-15, F-17, F-22 |
| OQ-7 | verified archives: the spec-decode trace as a codec | TRANSFERRED to amber/ (dated note 2026-10-15, call PC-6 of the 2026-10-14 public-cut batch; OPEN until then); constraint from F-9 (synthetic): total break-even hint budget 0.162 bits/token, dense hints lose 20:1; prior-art pass (LLMZip, ts_zip) required and not done; dated note 2026-10-11: the deterministic decode runtime it requires was never built (lockstep F-19; on one box an fp32 replay pin was enough) and the byproduct economics it leans on were never measured (the only pack rate in lockstep's record, F-17, is a separately run draft pass, 460x short of break-even); see the OQ-7 dated note in OPEN_QUESTIONS.md; the prior-art pass named here: see the OQ-7 cell's dated note of 2026-10-11 in docs/PRIOR_ART.md | - |
| OQ-8 | KV-page telemetry (source S2) | OPEN, never run; Lane-B breadth, not on the K-3 critical path (docs/ECONOMICS.md) | - |
| OQ-9 | bidirectional sidecar (steer + prefetch) | the STEER half PARKED by the 2026-09-14 note (no actuator in the record converts); the PREFETCH half ran as stage 1 on the OLMoE harvests (registered 2026-09-14, landed 2026-09-15 as F-26: PREFETCH-HEADROOM, NON-CRITERION, a K-6 datum) and as its free-bigram twin (2026-10-01: SURVIVES at that encoding, with a coverage caveat); the stratified covered-vs-fallback test read ran on 2026-10-02 (FALLBACK-LOCATED / PT-SURVIVES on both harvests, both gates straddling the floor: the caveat indicated, not settled; next rung R2, a free baseline whose encoding handles unseen and sparse keys); R2 ran on 2026-10-03 (R2-FALLBACK-SURVIVES / H-ABSORBS on both harvests: the unseen-key margin survives a generalising free encoding, +0.0732 [+0.0623, +0.0834] / +0.0662 [+0.0559, +0.0773], the located margin NOT shown to be table sparsity at this encoding, the pooled Q1 reading +0.0493 [+0.0425, +0.0577] / +0.0506 [+0.0433, +0.0594] straddles the floor on both, NOT-SHOWN / SIGNAL by the rule; with the stored final-norm state in the free arm no material margin (at or above +0.05) of the address block over the equal-dims free block, nor of the address stream over the free bigram plus the hidden block, is shown (both readings CI-positive below the floor), +0.0111 [+0.0078, +0.0150] / +0.0106 [+0.0068, +0.0153] equal-dims and +0.0172 [+0.0139, +0.0210] / +0.0162 [+0.0126, +0.0206] union, beside the strike, as pinned: D_add^H on the unseen-key positions +0.0399 [+0.0279, +0.0514] / +0.0286 [+0.0195, +0.0386] (NOT-SHOWN; the primary's CI95 containing the floor); stage 2's address-beyond-free motivation struck; the free-baseline ladder closed); stage 2 (a real draft partner for OLMoE) is an option without its address-beyond-free motivation, not a plan; the horizon read ran on 2026-10-04 (LEAD-TIME-ABSORBED on both harvests at horizons 2, 3, 4 against the hidden state plus the smoothed bigram: the PREFETCH half CLOSES at this reader by the pinned condition (beside it, as pinned: the primary's unseen-key CI95 contains the floor on 5 of the six fallback label cells, the replication's on none; the unseen-key readings in F-26's fourth dated status line); stage 2 only under a motivation this record does not supply) | F-26 and its dated status lines |
| OQ-10 | draft blindspot atlas and adaptive gamma | OPEN as a whole; pieces: OQ-14(ii)/(iii) readouts; K-3 arm 2 ran as the SpecDec++-class comparator in F-19 and F-21 | partial |
| OQ-11 | streaming / anytime steering during the target's forward | OPEN; only a synthetic p01 probe exists | - |
| OQ-12 | gate/steer granularity (coarse gating space) | ANSWERED NEGATIVE (F-13, 2026-08-30): coarsening fixes the gate (open rate 0.55/0.67/0.80 at C=15/31/62 vs 0.94 at C=510) but not the mechanism (best k16 soft -0.0029 [-0.0088, +0.0029]); attribution rider F-14 STRADDLE (+0.0014 [-0.0043, +0.0069]) with the oracle ceiling bounded <= +0.0069; the fine-k oracle cell is the untested residue. Two headers: the resolution and the original statement | F-13, F-14 |
| OQ-13 | S3 margin composition (floors, lenses, where the signal lives) | OPEN; registered post-replication secondary analyses, NON-CRITERION; floor-reduction menu UNRUN (F-17 caveat) | - |
| OQ-14 | extraction ceiling and usable signal | (ii) error-predictor ANSWERED at S1 (2026-09-02): test precision@0.20 = 0.7919 (a) / 0.8356 (c) over base rates 0.6059/0.6223, both arms select L1/off2; (iii) calibration ANSWERED at S1: test ECE 0.0082 (a) / 0.0408 (c), both under the 0.05 bar; (i) per-layer ensemble and (iv) boosting OPEN | results/real/error_predictor_s1.json; consumed by F-19 |
| OQ-15 | outcome-supervised readout (fold-back #1 of K-3) | CLOSED - CONVERSION-MODE NULL: Stage I (F-20, 2026-09-03) gate PASS mechanically but ARTIFACT-DOMINANT; Stage C (F-21, 2026-09-04) head_tel ties vanilla and loses CI-clear to head_free; hands off to OQ-16 | F-20, F-21 |
| OQ-16 | vector reconstruction telemetry -> h_a, consumed by SD^2's draft-side injection (fold-back #2) | Stage R PASS (F-22, 2026-09-04); DR-1 DEPLOYABLE-MARGIN CONFIRMED; DR-2 TOKEN-IDENTITY-NOT-EXCLUDED; DR-3 TELEMETRY-BEYOND-P (+0.065 [+0.062, +0.068], 37.5% of the free margin); DR-4 (2026-09-05) COMPARATOR-TOOTHLESS (-0.003 [-0.005, -0.001]; "beyond p" UNPRICED); STAGE-A FREEZE landed 2026-09-05 (arms vanilla / oracle_h / free_inject=FREETOK / tel_inject=UNION; ladder A0 then A1; seed 4, seed 5 reserved); GPU untouched; lane hard-stops after Stage A; DR-5 forbidden unless the user authorizes an exception "in those words" | F-22; Stage A pending; CLOSED 2026-09-05 by dated erratum (F-23): TARGET-FREE, no partition branch claimed (limbo clause honored); the lane has ended |
| OQ-17 | does the existence margin survive the FULL free baseline ((a) ++ hashed token ids ++ z-scored h_a) at the registered reader? | CLOSED as a question (F-24, 2026-09-06): ABSORBED at both sources at the pinned L1 cells (every gate D CI95 upper below +0.005); corrected twin TWIN-ROBUST at both; the pinned prediction failed on both sources; what remains open is the owner's: a registered re-test with the corrected twin and/or a stronger reader | F-24 |
| OQ-18 | does the COARSE-LABEL (L2 / L3) existence margin survive the full free baseline? | CLOSED as a question (F-25, 2026-09-14) under the 2026-09-07 leak-rider amendment - a post-hoc reroute around a fired kill condition, a fresh test only at the other three harvests (the registered rider fired at S1 L3; the amended leg's positive control read DOMINANCE-CONFIRMED-HERE): S1 L2 ABSORBED, S1 L3 NOT-SHOWN, S3 L2 ABSORBED, S3 L3 SPLIT (fired on the replication harvest only; inflated by up to the twin's own cost, not read as half a survival); the 2026-09-14 outcome says the plan of record (2026-09-06) proceeds to OQ-19, now the unfrozen draft of the row below | F-25 |
| OQ-19 | oracle-intermediate CEILING: do the TRUE tap-layer activations carry future-concept information beyond the full free baseline at all? | UNFROZEN DRAFT, UNDECIDED (dated note 2026-10-01): the registration block drafted 2026-09-06/07 and rebuilt verbatim from that session's transcript as docs/OQ19_ORACLE_CEILING_DRAFT.md, the instrument files carrying DRAFT banners and a run refusal; nothing has run; the 2026-09-14 review recommended skipping it or shrinking it to a pilot; dated note 2026-10-11: SKIPPED by the operator's decision, the draft and the run refusal unchanged | - |

---

## Economics bars (from docs/ECONOMICS.md, registered skeleton + pinned bars, 2026-09-01)

Written after F-18 and before any K-3 actuator run; makes no wall-clock
claim; its section 6 verdict skeleton is left as registered, with a dated section 6a (2026-09-05) filled by its own rule ("to be
filled by K-3, not edited before it").

Measured inputs the bars stand on (section 2, each with its committed source):

| quantity | value | source (as the memo cites it) |
|---|---|---|
| vanilla acceptance, Llama pair, gamma=4 | 0.763 | F-10 (audit_k512) |
| tokens per target call | 3.11 | BLUEPRINT origin frame (measured on the pair) |
| concept-level steerable share of rejections | 0.56-0.67 by k | F-11 |
| free-information steering delta, best arm | +0.0025, CI through zero | F-12 |
| free-information confirmatory arm | -0.0098 [-0.0155, -0.0039] | F-12 |
| old-actuator oracle ceiling at coarse k | <= +0.0069 (point +0.0014) | F-14 |
| concept-bucket persistence, k=512 | 0.027, run length 1.015 | F-12 (bucket_persistence) |
| probe margin, S1 (finding's stated range) | +0.008..+0.044 | F-15 |
| probe margin, S3 (finding's stated range) | +0.006..+0.073 | F-17 |
| acceptance <-> tokens/call coupling | about 6.2 tokens/call per unit acceptance | F-12 dose arm (sharp beta4: -0.0237 acceptance, -0.146 tokens/call) |
| SD^2 upper baseline | +35% accepted tokens, +22% throughput | docs/PRIOR_ART.md; its dated correction (2026-09-04) says these are cross-pair maxima, not the Llama pair's numbers |

The coupling sentence, verbatim from section 2: "Coupling caveat: 6.2 is a
linearization from ONE dose point on the harm side of one arm; treating it
as symmetric and linear is an approximation, labeled as such wherever used
below." Section 5 adds that its use for scheduling arms is out-of-regime
(it was measured at fixed gamma=4 on a q-modifying arm); the Stage-A freeze
notes that Stage A, a fixed-gamma q-modifying actuator, is the one place
the coupling is in regime.

The bars (section 5; prohibited from amendment after any K-3 result is read):

| bar | value | what it gates |
|---|---|---|
| K-3 WIN (acceptance form) | minimum paired delta over ALL THREE comparators (vanilla, free-soft, free-sharpened): CI95 lower > 0, point >= +0.010 acceptance, analytic estimand concordant | the original K-3 gate |
| K-3 WIN (tokens/call form, dated pre-result amendment 2026-09-01) | for EVERY comparator: CI95 lower > 0 AND point >= +0.062 tokens/call AT MATCHED DRAFTING BUDGET AND the pairwise budget guard (arm's verdict drafted-per-emitted <= comparator's + 0.01); analytic concordance demoted to reported-not-gating | K-3 Attempt #1 (F-19), OQ-15 Stage C (F-21), Stage A (unchanged) |
| Lane A materiality | the WIN bar itself; +0.010 acceptance is about +0.062 tokens/call, about +2.0% on the 3.11 base; verdict language at exactly the bar is "real, free, modest" | software telemetry in MoE serving |
| Lane B operational bar | point acceptance delta >= +0.044 (about +0.27 tokens/call, 8.8% of the 3.11 base by section 5, "+8.7%" by section 3's arithmetic); like-for-like on SD^2's accepted-tokens base it is about 37% of SD^2's gain, so harder than its "25% of SD^2" label; plus a named, defended boundary where the hidden-state vector cannot cross | the hardware device story |

Anchors the memo gives for +0.010: it exceeds the dead actuator's
perfect-forecast ceiling (F-14 CI upper +0.0069 at coarse k) and is about
2x the harness's typical CI half-width (about 0.005-0.006 across
F-12/F-13/F-14). Empirical basis for the budget guard: the phase0b vanilla
accepted-length distribution P(k=0..4) = 0.2509/0.1751/0.1341/0.0953/0.3445
over 17,220 blocks, mean emitted per block 3.107; the information-free skew
residual was measured at +0.0103 tokens/call, 17% of the bar.

Where the bars stand against evidence: F-19 measured +0.006860 tokens/call
(the F-19 title rounds it to +0.007 against +0.062); F-21 measured
+0.002664; neither the Lane A nor the Lane B bar has been met; Stage A is
the last registered attempt.

---

## A-Z

### A

**A0 / A1 (Stage-A ladder).** The two user-launched rungs of the OQ-16 actuator stage (docs/BLUEPRINT.md STAGE-A FREEZE, 2026-09-05). A0 = export the reconstructions, train the oracle_h adapter, run V then O on the verdict population at seed 4; O-vs-V must clear the E6 bar (CI95 lower > 0 AND point >= +0.062 tokens/call AND the pairwise budget guard) or the outcome is ACTUATOR-CEILING NULL and the lane ends. A1 (only after A0 clears, and only by the user's decision with DR-4's COMPARATOR-TOOTHLESS label in view) = train free_inject and tel_inject, run F then T; F-vs-V is the FREE-ACTUATOR readout (its own label, outside the K-3 kill text), and the telemetry verdict is WIN iff T-vs-V AND T-vs-F each clear the bar, licensed only as telemetry converting "beyond FREETOK, the strongest free encoding tested ... at the actuator", never as "beyond p". No rung has run at HEAD. (F-23, 2026-09-05: arms 9 and 10 struck pre-GPU because their target is free information; arm 8 is the deployable free-actuator arm under any future registration; the A0/A1 ladder no longer exists as a telemetry test.)

**ABSORBED.** The strong-null label of the full-free re-tests (F-24, F-25, F-28), one of the mechanical labels per (source, label space) read from both harvests of a source: the gate D = acc(fplus_b) - acc(fplus_n) (F-25 and F-28: acc(fplus_r), the corrected twin) at the off2 gate cell (the registered reader mlp256 in F-24, F-25 and F-28's lens stage; each stronger reader in F-28's reader stages) fires on neither harvest under the Phase-3 triple rule (CI95 lower > 0, all three seeds positive, point >= +0.005) AND every D row's CI95 upper is below +0.005 on both harvests (F-24's registered rule; its siblings READER-INVALID / SURVIVES-FULL-FREE / SPLIT / NOT-SHOWN / INCOMPLETE). It carries two scopes, the registered reader at the registered budget and the +0.005 materiality floor: the licensed sentence is "no MATERIAL (+0.005) equal-dims margin at the registered reader", never "no margin" (F-24: Mt, telemetry's own margin over the full free baseline, is CI-clear at about +0.003 on three of the four harvests), and it is "the registered strong-null form (every D upper below +0.005 on both harvests), not a demonstration that the equal-dims margin is zero" (F-24 caveats). Landed: S1 and S3 at the pinned L1 offset-2 cell (F-24: S1 D +0.0002 [-0.0012, +0.0015] / +0.0012 [-0.0003, +0.0028], S3 D +0.0003 [-0.0013, +0.0020] / +0.0001 [-0.0019, +0.0021], primary / replication, "Mt beside it +0.003 or less"); S1 L2 and S3 L2 (F-25); S3 L3 through the balanced lens at the registered reader (F-28: D +0.0019 [+0.0006, +0.0032] / +0.0004 [-0.0011, +0.0018]); and, resting on one gate D row per harvest, the stronger-reader cells at S3 (F-28) at L1 under R-N, R-T and R-L, at the balanced L3 under R-T and R-L, and at the lopsided L3 under R-T. Horizon form OFF3-ABSORBED / OFF4-ABSORBED. The record issues no all-space sentence: L3 is OPEN at both sources at the registered reader. See Materiality floor (+0.005), Equal-dims noise anchor, NOT-SHOWN, SPLIT, TWIN-ROBUST, K-2-ISOLATED, Kill criteria K-2.

**Acceptance probability, per-position (1 - TV(p, q)).** Under the Leviathan rejection scheme the probability that a drafted token is accepted equals one minus the total-variation distance between the target's p and the (possibly steered) draft's q at that position. It is the quantity steering tries to raise, the D-9 headline estimand when averaged over drafted positions, and OQ-15's regression target. See Analytic acceptance.

**Actuator.** The mechanism that turns a signal into acceptance: bucket-bias steering (D-8/D-10; dead as built on real models at every tested k, F-12/F-13/F-14; the fine-k oracle cell is unrun), adaptive block scheduling on probes (K-3 Attempt #1, F-19), the outcome-head scheduler (OQ-15, F-21), and SD^2-style hidden-state injection (OQ-16 Stage A, frozen, unrun). "Existence != actuator" is the recurring caveat; see Ceiling vs existence vs headroom vs actuator.

**ACTUATOR-CEILING NULL.** The Stage-A A0 outcome if oracle_h (the TRUE h_a injected) fails to beat vanilla by the E6 bar: "not even the TRUE anchor state converts through this frozen-drafter rank-512 actuator at this training budget on this box" (docs/BLUEPRINT.md STAGE-A FREEZE). A sub-label of the OQ-16 partition's ACTUATOR NULL; carries the actuator caveat verbatim (a null of THIS actuator, not of SD^2's). (F-23, 2026-09-05: arms 9 and 10 struck pre-GPU because their target is free information; arm 8 is the deployable free-actuator arm under any future registration; the A0/A1 ladder no longer exists as a telemetry test.)

**ADDRESS-BEYOND-TOKEN.** F-26's prefetch reading on the OLMoE S3 harvests: HISTORY_TOK minus FREE_TOK at horizon j = 1, in hit rate at residency budget B = 16 of the 64 experts per gate; SIGNAL iff the paired CI95 lower > 0 and the point >= +0.05 (the pinned floor), NEGATIVE iff the CI95 upper < 0, else NOT-SHOWN; "the sideband sentence follows ADDRESS-BEYOND-TOKEN alone". Landed SIGNAL +0.1032 [+0.0926, +0.1146] / +0.1072 [+0.0952, +0.1206] (primary / replication), below the +0.05 floor at B = 32 (+0.0405 / +0.0434). Its scope, carried on every text of that landing: the free arm is a ONE-TOKEN table and the equally free previous token is not in it; the free-bigram twin (F-26's status line of 2026-10-01) read D_eq +0.0609 [+0.0514, +0.0712] / +0.0659 [+0.0547, +0.0788] over an equal-dims free bigram block ("SURVIVES at THIS ENCODING", docs/WHY_THIS_DIES.md K-6 STATUS 2026-10-01), the free previous token accounting for 0.4104 / 0.3858 of the re-measured margin; the later rungs carry their own labels, see R2-FALLBACK-SURVIVES, H-ABSORBS and LEAD-TIME-ABSORBED. NON-CRITERION, a K-6 datum; nothing in F-26 reads it "as support for the sideband premise". See PREFETCH-HEADROOM, Kill criteria K-6.

**Alignment-destroyed.** A feature block taken from a different block of the same prompt (slots of anchor (a+17) mod row-length, F-16), so per-prompt statistics survive but the block-aligned signal is gone. The construction behind the equal-dims noise anchor; UNIONNOISE = NOISE ++ TOK is the union arm's anchor (F-22 DR-3). See Equal-dims noise anchor.

**Analytic acceptance (D-9 headline).** E[1 - TV(p_j, q_j)] recorded at every DRAFTED position: unconditional, variance-reduced, exogenous to accept/reject outcomes. For scheduling arms it is REPORTED, not gating, because arms draft different position mixes (docs/ECONOMICS.md section 5 amendment 1; F-19, F-21 report it that way: seed-1 pooled vanilla 0.734390 vs telemetry 0.734971 in F-19). At fixed gamma with q-modifying arms (Stage A) the freeze pins it as reported per arm and per offset without the composition caveat.

**Analytic vs empirical vs probe units.** Three layers the findings never convert between: probe top-1 accuracy margins (K-2), per-position analytic acceptance and tokens per call (K-3), and wall-clock (K-5, unmeasured). See The three layers.

**Anchor-state identity (F-23).** The 2026-09-05 dated erratum's fact: h_a, the verifier's final-norm output at the anchor, is the lm_head input, and Llama-3.1-8B-Instruct's lm_head is an untied, bias-free linear map of full column rank (128256 x 4096), so the anchor's logits determine h_a exactly and the full next-token distribution p determines it up to floating-point error (results/real/oq16_ha_identity.json: full-logit inverse relative error 2.5e-8 median; top-4097 log-prob recovery per-row R^2 +1.0000; top-32 R^2 +0.014 on 48 pinned rows). Consequence: every reconstruction of h_a from telemetry or from a hashed p is a lossy copy of free information (D-5); see TARGET-FREE, RECONSTRUCTION-CEILING NULL, Free actuator.

**Anchor.** The block-start position whose forward produced the telemetry and the free summaries. Harvest: anchor a holds telemetry captured during the forward that produced p_a. Live (K-3 arc): the position that produced the emitted residual-or-bonus token, index = base + accepted count, conditioned on accepted content only; the first block's anchor is the prompt's last token from the prefill forward, and block-1 consults are disabled (E12(i)).

**Argmax mechanism (argmax+tau).** D-8's original default: boost only the single argmax-predicted concept bucket, gated on confidence tau. Dominated by posterior_bias at every width and at the oracle level (F-7); superseded as the default by D-10.

**ARTIFACT-DOMINANT / ARTIFACT-NOT-EXCLUDED.** DI-1's pinned labels: primary stale point >= 0.5 x the live margin -> ARTIFACT-DOMINANT; the replicate below that -> ARTIFACT-NOT-EXCLUDED; disagreement carries ARTIFACT-DOMINANT. F-20 landed ARTIFACT-DOMINANT (primary stale +0.000643 [-0.000076, +0.001357], about 84% of the live +0.000763). NON-CRITERION: the label cannot reclassify the partition branch. See Stale-target control.

**Attempt #1 (K-3).** The registered Phase-4 arc that first tested conversion: adaptive block scheduling on frozen S1 probes, five arms, thresholds frozen on 30 val prompts, verdict on data/prompts_k3_verdict.jsonl (210 prompts). Result NOT WIN (F-19): telemetry vs vanilla +0.006860 [-0.015024, +0.025572] tokens/call against the +0.062 bar. Its byproduct logs are OQ-15's and OQ-16's training data. See K-3 arms 1-5, P-stage, Void semantics.

### B

**B_ref.** The reference drafting budget: vanilla gamma-4's drafted-per-emitted measured on the VAL prompts, frozen at first read before any verdict run; each adaptive arm tunes subject to val dpe <= B_ref. OQ-15 Stage C: 1.3255813953488371 from oq15c_val_arm1 (F-21).

**BAR-RESOLVED@210 / RULE-LEAKS@30 (F-27 readings).** The seed-noise floor's two readings beside its label, each mechanical (docs/BLUEPRINT.md, "SEED-NOISE FLOOR READOUTS REGISTRATION"): BAR-RESOLVED@210 iff the n = 210 cross-seed null CI95 half-width is below 0.062 (the +0.062 WIN bar exceeds one CI half-width at the verdict size), else BAR-UNRESOLVED@210; RULE-LEAKS@30 iff g_one at n = 30, the share of 1,000 prompt subsets in which a single comparator leg of the F-19 WIN rule passes by seed noise alone, exceeds 0.01, else RULE-TIGHT@30 ("1% is a reporting threshold with NO consequence: the rate itself is the datum and is quoted with its SE whatever the word"). Landed on both populations (K3 / OQ15): BAR-RESOLVED@210 with half-widths 0.0385 / 0.0398 tokens per verify call; RULE-LEAKS@30 with g_one 0.0235 / 0.0375 (SE 0.0033 / 0.0042; "the guarded rate is the same number by algebra"). NON-CRITERION: "no verdict moves". See FLOOR-MATERIAL, Win bar (+0.062 tokens/call), Replication (pinned triple).

**Beta.** Steering strength, the magnitude of the additive log-space bias. Best about 3-4 gated in the synthetic world (F-3); harm is dose-monotone in beta on real models (F-12 sharp: +0.0009 / -0.0040 / -0.0098 / -0.0237 at beta 1/2/3/4).

**Binding gate.** See Sha header / binding gate.

**Block.** One draft-then-verify round: gamma drafted tokens, one target verify forward, emitted = accepted + 1 (the bonus or residual token). See Gamma, Bonus token.

**Block-aligned information vs prompt-level statistics.** The distinction the stale-target control draws: information tied to THIS block's anchor (what steering needs) versus information about the prompt overall (which a shifted twin also carries). F-22: NOISE-vs-FREE +0.02852 [+0.02319, +0.03542] is prompt-level slot statistics (about 14% of the free margin), not block-aligned.

**Block-start alignment.** The load-bearing harvest convention (sideband.harvest.label_index): the label at offset j is the bucket of token x_{a+j-1}; offset 1 is the token sampled from p_a itself; K-2 reads offsets >= 2. It guarantees the free probe (a) is not handicapped by under-logging.

**Bonus token / residual token.** The one token the verifier always emits after a block: sampled from the residual distribution on a rejection, or from the target's distribution at position gamma+1 when every draft is accepted. Hence emitted-per-call = accepted + 1 always (docs/ECONOMICS.md section 5), which is why raw tokens/call is buyable by drafting more; see Information-free extend channel.

**Break-even hint budget.** F-9 (synthetic, OQ-7): the total bits per token an archive hint channel may spend before it costs more than the corrections it saves - 0.162 bits/token in that regime; a dense per-position fresh-concept hint loses 20:1 (net -3.18 bits/token); free-causal steering saves 0.100 bits/token at zero cost. The SHAPE (dense hints dominated, free steering a pure win) is the transferable constraint. Dated note 2026-10-11: 'free steering a pure win' has no real-model support as built: the real-pair free-information steering baseline is zero (F-12; the confirmatory arm's pooled acceptance delta -0.0098 [-0.0155, -0.0039], an empirical pooled acceptance-rate delta, not bits, with the D-9 analytic estimand agreeing in sign and size; F-12's own caveat bounds the mechanism at that granularity, not free information's ceiling, F-13 closed the coarse-granularity half the same way, dead at every tested granularity, and F-14 bounded the oracle ceiling at k=16 at +0.0014 [-0.0043, +0.0069], an acceptance CI, not bits, STRADDLE with the fine-k oracle cell left open; no real-text bit ledger ran), and amber's archive is draft-coded on both sides (a separate pass: encode with the draft's teacher-forced logits, decode with the draft alone), a regime with no verifier-side steering to save bits; what remains is the shape's other half, dense per-position hints dominated, a synthetic constraint untested on real models; see the F-9 row of docs/REPORT.md section 4.1.

**Bucket / bucketization.** A partition of the vocabulary. Synthetic: ground-truth concept blocks. Real: k-means over the target's lm_head rows (PCA-128, seed 0) at k in {256, 512, 1024} for the audit (F-10) and {16, 32, 64} for coarse gating (F-13, fresh runs, not coarsenings). "Cross-bucket" is bucket-level, not certified concept-level, until glue is excluded (F-11).

**Byproduct logs.** E8: per K-3-arc run, a gitignored directory <out>.byproduct/ with one npz per prompt holding per-block arrays (anchor position, slots, h_a, bucket masses at several k, entropy, argmax, top-32 ids and probs, gamma used, stop/extend, accepted count, consult signals) and per-drafted-position arrays (proposed token, accepted flag, analytic 1 - TV). Logged READ-ONLY (no extra forwards, no RNG; the D-6 containment property); per-file sha256s land in the run SUMMARY sidecar (E12(iii) erratum). These logs are OQ-15's and OQ-16's training data, collected "for free" by the dated 2026-09-02 byproduct amendment; the raws are gitignored, so their loss before Stage R completes is VOID-BY-DATA-LOSS (OQ-16 limbo dispositions).

### C

**C1..C4 (OQ-15 Stage-C arms).** C1 vanilla (runner arm 1); C2 draft-confidence (arm 2, the SpecDec++-class incumbent retuned on fresh val); C3 head_free = the outcome-head policy on FREE features, 657 dims (arm 6, the matched-actuator free baseline); C4 head_tel = the same policy on FREE+TEL, 2705 dims (arm 7, the bet). Head policy: STOP at consult j in {1, 2} iff S_j = prod a_hat_1..j < tau_stop[j]; EXTEND to gamma 6 iff S_4 * a_hat_5 >= tau_ext (F-21). Seed-3 verdict: C4-vs-C1 +0.002664 [-0.044719, +0.046727], C4-vs-C2 -0.050425 [-0.109388, +0.005772], C4-vs-C3 -0.081846 [-0.132484, -0.035567].

**Ceiling vs existence vs headroom vs actuator.** Four layers the findings keep apart. HEADROOM = the share of rejections a mechanism could address (F-10 bucket-level 0.78-0.86; F-11 concept-level 0.56-0.67). EXISTENCE = information beyond free (K-2; F-15, F-17). CEILING = what a perfect forecast converts through a given mechanism (F-14: <= +0.0069 acceptance through bucket bias at coarse k). ACTUATOR = the mechanism that converts a signal to acceptance (K-3). A number in one layer never stands in for another.

**Chat template, pinned date.** K-1 amendment (docs/WHY_THIS_DIES.md): Instruct models are decoded with the chat template applied and a fixed date_string, recorded as chat_template_used in every run meta, because raw-completion decoding of an Instruct pair is a regime nobody deploys.

**CI-clear / CI-positive / CI-negative.** A CI95 entirely above zero (clear or positive) or entirely below zero (negative). "CI-positive-immaterial" = above zero but the point is below the +0.005 materiality floor (F-17's L1/off3 profile). See Straddle.

**Committed evidence (results/*.json).** Result files are regenerated by tools, never hand-edited (CLAUDE.md). Synthetic results/ regenerate bit-exact via `make experiments`; real results/real/ payloads are verified by RE-RUN because CUDA/bitsandbytes kernels are not bitwise deterministic (K-1 rider), the pass rule being "point estimate inside the original run's cluster-bootstrap 95% CI". Registered runs' state files are committed evidence too; see State files.

**Composition confound.** Why analytic acceptance is reported-not-gating for scheduling arms: an arm that stops aggressively drafts an easier mix of positions and posts higher per-drafted-position acceptance without producing more tokens per call. F-21 shows it in one line: head_tel has the top analytic acceptance (0.7416298732067561) while drafting the fewest tokens (68,392 vs 69,936-70,765) and losing on tokens/call.

**Compute-tier tap vs address stream.** D-1's bright line. A compute tier possesses a layer's activations locally, so READ-ONLY taps on them (S1 shadow sketches) are inside the observability premise; a passive weight store observed through its ADDRESSES (S3 routing, S2 pages) is the original hardware story. Taps that read are allowed; gates that change what the target computes are forbidden; the draft's q is fair game. K-2 is judged per source because of this split.

**Concept bucket / concept space / concept-level.** Non-glue buckets. "Concept-level" share = rejections whose proposed and emitted tokens lie in DIFFERENT non-glue buckets (F-11: 0.565/0.610/0.674 at k=256/512/1024). Not certified semantic concepts - k-means cells with the glue cells removed. Predictions and gate comparisons live here (D-7).

**Concept-HMM v0 (synthetic world).** The Phase-1 testbed: a hidden-Markov concept process emitting bucketed tokens, a corrupted draft (draft_alpha), concept persistence rho, a function-word rate lambda_function, and hardened telemetry parameters. F-2..F-9 live there (F-0/F-1 are verifier-exactness results independent of any world); F-6 proves it cannot show telemetry beating free information, so every existence claim had to move to real models.

**Confidence gate / tau.** D-8: steer only when the decoder's confidence exceeds tau (about 0.5); it converts harmful weak decoders into harmless ones (F-5: at the three narrowest widths of the sweep, K = 8/16/32 slots per experiments/e05_sidecar_recovery.py, recovery goes from -152%/-88%/-22% ungated to -1%/+2%/+8% gated). Subsumed by centering under D-10 (a uniform posterior is an exact no-op).

**Constrained maximization / frontier search.** The registered tuning rule for adaptive arms: maximize val tokens/call subject to val drafted-per-emitted <= B_ref over a pinned quantile grid, tie-break toward lower budget - never unconstrained tokens/call maximization (docs/ECONOMICS.md section 5 amendment 1). F-19: 97 evals across arms; F-21: 128 evals.

**Consult / STOP / EXTEND.** The K-3 and OQ-15 scheduler's per-block decisions. A CONSULT reads a signal at drafted position j in {1, 2}; STOP truncates the block's drafting at j; EXTEND (one decision after the base gamma-4 drafting, E4) extends the same block to gamma 6 before the single verify forward. Mutually exclusive; disabled on block 1 (E12(i)).

**Containment rider (E10).** The empirical READ-ONLY check that instruments do not perturb the trajectory: vanilla arm, 10 val prompts, seed 100, three runs (instruments ON, OFF, OFF rerun). If OFF vs OFF-rerun is bit-identical the bar is BIT-IDENTITY of ON vs OFF; else a bounded mean-acceptance delta. OQ-15 Stage C passed on the strictest bit-identity branch (F-21, oq15c_containment_rider.json).

**Contamination.** The test-in-train prompt-overlap audit of a harvest (results/real/harvest_audit*.json): 0.8% at S1 (OPEN_QUESTIONS.md OQ-1); 0.52%/0.64% (distinct/occurrence) on the S3 primary harvest and 0.37%/0.47% on its replication (F-17).

**Coupling (about 6.2 tokens/call per unit acceptance).** docs/ECONOMICS.md section 2: a linearization from ONE dose point on the harm side of one arm (F-12 sharp beta4: -0.0237 acceptance, -0.146 tokens/call), labeled an approximation wherever used, and out-of-regime for scheduling arms. It is how +0.010 acceptance becomes the +0.062 tokens/call bar. See Economics bars.

**Critic (sideband-critic) / recompute.** The .claude/agents/ review agent run against every experiment diff before merge (CLAUDE.md). Its highest-value mode is RECOMPUTING decisions from the raw state files with a fresh implementation; bit-exact matches are recorded in findings (F-15, F-17, F-18, F-20, F-22). A "critic attack round" is the adversarial pass a surprising branch gets (F-22, invoking rule 7).

**Cross-fit h_hat (Stage-A export).** In the Stage-A freeze, the reconstructed vector used to TRAIN an injection adapter comes from five-fold cross-fitting per population (position mod 5): every prompt's h_hat comes from a ridge fit that never saw it, on 168 of 210 prompts; a full refit on all 210 yields the verdict-time weights; every fit at the arm's DR-4 VAL-chosen lambda with DR-1's support clip (docs/BLUEPRINT.md STAGE-A FREEZE). The export is binding-gated on reproducing results/real/oq16_stage_r_dr4.json bit-exactly. Not run at HEAD.

**Cross-lane skip condition.** From the FOLD-BACK COUNT AMENDMENT (2026-09-02): if OQ-15 nulls at the information ceiling, OQ-16 is SKIPPED and the lane stops, because both lanes read the same stream. An argument-level "bridge", explicitly not a theorem: the BRIDGE LOOPHOLE clause records that prediction bounds are not intervention bounds. OQ-15 nulled in conversion mode, so the skip did not fire.

### D

**D2/D3 (K-3 diagnostic stage).** The Attempt-#1 stage on the committed S1 harvest that produced the OQ-14(ii) error-predictor and OQ-14(iii) calibration readouts (results/real/error_predictor_s1.json: test precision@0.20 = 0.7919 (a) / 0.8356 (c) over base rates 0.6059/0.6223; test ECE 0.0082 (a) / 0.0408 (c)) and thereby picked the live probes' label space (L1/off2) and confidence signal (the raw posterior).

**data/prompts.jsonl (210).** The committed short-prompt set (one unique topic per prompt so bootstrap clusters are independent) used from Phase 0a through Phase 3; it includes the 150 probe-training prompts, which is why every actuator verdict uses a fresh committed population. See Verdict population.

**Dated amendment / dated erratum.** House rule: registered text is never rewritten; a correction is appended with a date (examples: F-16's 3266 -> 3265 dims erratum; E12(iii) "meta" -> "summary"; DR-4's "dense-valued" -> sparse TOK_B). A dated PRE-RESULT amendment may change a registration; amending a bar after its result is read is prohibited (docs/ECONOMICS.md section 5).

**Decision (D-N).** A standing decision in DECISIONS.md (D-1..D-11); see the Decisions section above.

**Defined comparison (E2).** A probe-vs-draft class comparison counts only when BOTH classes are concept classes (neither is the merged glue class); an undefined comparison fires neither STOP nor EXTEND. Because glue is the majority label at anchors, defined comparisons are a minority of consults and realized trigger rates sit below the nominal quantile levels (F-19 disclosures).

**delta_noise / delta_free.** The OQ-15 and OQ-16 gate deltas on pooled TEST MSE: delta_noise = MSE(NOISE) - MSE(TEL) (existence above dilution); delta_free = MSE(FREE) - MSE(TEL) (deployability above free). Positive means telemetry is better. F-20: +0.000763 [+0.000308, +0.001215] and -0.00286 [-0.00322, -0.00252]. F-22 registered run: +0.176469 [+0.130414, +0.251518] and +0.204984 [+0.153698, +0.288162]; under DR-1's clip +0.161692 [+0.153035, +0.170259] and +0.169079 [+0.160250, +0.177775] (results/real/oq16_stage_r.json, oq16_stage_r_dr.json).

**DI-1.** The Stage-I stale-target control; see Stale-target control.

**Dilution.** The accuracy or MSE cost of adding uninformative dimensions to a linear model at fixed data. It can fake a null when TEL is compared with FREE at unequal dims, which is why the equal-dims noise anchor exists. Measured -0.0045..+3.3e-5 per +2048 dims at S1 (F-16 M2noise), -0.0108..+0.0015 at S3 (F-18), and about 0.026 gross per +2048 dims in the OQ-16 ridge (F-22 DR-3), about 5x F-16's scale.

**Direction proxy.** The OQ-16 registration's downstream readout (does the reconstructed vector's direction correlate with the true one's), pinned REPORTED-only, not gating, as one of the three design decisions put to the user before registration (docs/BLUEPRINT.md OQ-16 ARC REGISTRATION). Reported as the centered-cosine medians in F-22.

**Dirty flag (git_commit -dirty).** Meta provenance flag: the working tree had uncommitted files when the run started. Repeatedly disclosed in findings as "untracked results/scratch only, operator-attested" or "the dirt IS the instrument + registration that ran" (F-15, F-17, F-18, F-20, F-22).

**Disagreement gate.** Apply steering only where the draft's own top CONCEPT bucket differs from the predicted bucket, glue excluded on both sides (D-7, D-8). Load-bearing in the synthetic world (F-3: gated stale oracle +0.0195 at beta=3 vs an ungated peak of +0.010); on real k=512 it is open 93.6-94.0% of positions and hence useless (F-12); coarsening restores selectivity without rescuing the mechanism (F-13).

**DR-1..DR-5 (Stage-R post-gate diagnostics).** Registered after the Stage-R gate was read and before running, with pinned labels; NON-CRITERION (docs/BLUEPRINT.md; F-22). DR-1 = the feature-support clip and the deployable margin vs the trivial predictor (label DEPLOYABLE-MARGIN CONFIRMED, +0.250784 [+0.239316, +0.261616]). DR-2 = the equal-dims FREETOK arm (TOKEN-IDENTITY-NOT-EXCLUDED, tel_vs_freetok -0.004792 [-0.007192, -0.002600]). DR-3 = UNION vs FREETOK (TELEMETRY-BEYOND-P, +0.065180 [+0.062411, +0.067705]; dated 2026-09-04, registered in commit 2ec789f). DR-4 = FREETOK2, the better-token-encoding comparator (COMPARATOR-TOOTHLESS, freetok2_vs_freetok -0.003085 [-0.004984, -0.001280]; dated 2026-09-05, registered in c2181b1, "the lane's LAST reconstruction-level diagnostic"). DR-5 = the anchored TOK_B twin, FORBIDDEN under the fold-back-#2 hard stop unless the user authorizes an exception "in those words" (OPEN_QUESTIONS.md OQ-16).

**DR labels (TELEMETRY-BEYOND-P, TOKEN-IDENTITY-NOT-EXCLUDED, DEPLOYABLE-MARGIN CONFIRMED, COMPARATOR-TOOTHLESS).** The pinned outcomes of DR-3, DR-2, DR-1 and DR-4 respectively (results/real/oq16_stage_r_dr4.json diagnostic_labels). Together they license "telemetry adds beyond FREETOK's hashed encoding of p at reconstruction" and refuse "beyond p", which stays unpriced.

**draft_alpha / rho.** Synthetic-world knobs: draft_alpha = draft quality (0.5 weak .. 0.9 strong; F-2 cross-bucket fractions 89.3% / 83.1% / 76.1%); rho = concept persistence (run length 2.5 at rho=0.6, 33 at rho=0.97; F-4).

**Drafted-per-emitted (dpe).** E6: drafted tokens divided by emitted tokens - the drafting BUDGET an arm spends per token it produces. Vanilla gamma-4 about 1.32 (F-19 seed-1 vanilla 1.324316; F-21 seed-3 vanilla 1.3296655675930287). The quantity budget matching and the pairwise guard are defined on. With gamma fixed, dpe = 4 / tokens-per-call exactly (Stage-A freeze).

### E

**E1..E12 (Stage-E engineering clarifications).** Twelve pins in docs/BLUEPRINT.md (dated 2026-09-02, before any stage-E code) closing the degrees of freedom of the K-3 live instrument: (E1) live probes = the four committed Phase-3 cells L1_concept_k16 | off{2,3} | {a,c} | linear at train seed 0, binding-gated export; (E2) agreement/disagreement semantics in concept space (see Defined comparison); (E3) arm-2 signal mapping signal_j = q_j(x_j); (E4) extend mechanics (one decision per block after the base drafting); (E5) threshold materialization from quantile grids over consulting blocks; (E6) gate arithmetic (tokens/call = emitted per verify call, prefill excluded; the joint-bootstrap ratio delta); (E7) feature fidelity to the harvest dtypes; (E8) byproduct format; (E9) live-tap fidelity rider + tolerance mapping; (E10) containment rider; (E11) instrument change scope (defaults OFF, byte-identical default path); (E12) dated amendment: block-1 consult exclusion, temperature binding, the E8 erratum (shas in the summary, not the meta), E9 errata. "Stage E" = the engineering stage of the K-3 arc (live ShadowTap in hf_specdec, probe export, scheduler hook).

**Empirical acceptance-by-offset (survival-conditioned).** The fraction of drafts accepted at offset j among blocks that SURVIVED to offset j (F-10 at k=512: 0.815/0.818/0.809/0.807 for offsets 1-4, n = 4321/3015/2310/1641). It answers a different question from the analytic estimand and must be labeled as such (D-9).

**Equal-dims noise anchor / noise twin / NOISE / (atn).** The control that prices dilution: the same base features plus a telemetry block whose ALIGNMENT is destroyed, so dims match the tested arm exactly (F-16: (atn) = (a)+(t)+shifted slots, 3265 dims = (abt)). Mandatory alongside any "does adding block B help" test (CLAUDE.md working practices). In OQ-15/OQ-16 the NOISE arm is F-16's shift applied to the slot block (2705 dims, equal to TEL). Its limitation, F-20's lesson: it prices dilution but not the zero-information draw distribution under same-anchor redundancy; pair it with the multi-seed stale-target control.

**EQUAL-DIMS-ONLY.** The licence qualifier of a SURVIVES statement in the full-free re-tests, pinned in the OQ-18 registration's LICENSED SENTENCES (docs/BLUEPRINT.md): a SURVIVES statement quotes Mt AND Mn_r beside D and names the reader; the licence is FULL only if BOTH Mt's and Mn_r's CI95 uppers are >= 0 at the gate cell on both harvests, since by the paired identity D = Mt - Mn_r a gate fire on a harvest where the corrected twin is CI-clear harmful is bought by the twin's cost; a fire with Mn_r's upper < 0 is written "at equal dims (D), inflated by up to |Mn_r| by the twin's own cost" and a fire with Mt's upper < 0 is written "at equal dims (D); at this budget adding it did not raise accuracy (Mt)" (the payload's survives_license and license_reason say which). F-28 applies the same rule to SURVIVES-STRONGER (FULL only if Mt's and Mn_r's CI95 uppers are >= 0 on both, else EQUAL-DIMS-ONLY with the reason). Its two cells, both at the lopsided L3 (primary / replication): R-N (hz-rescaled), reason "Mt CI95 upper < 0 on a harvest" and "two costs" (F-28; docs/WHY_THIS_DIES.md K-2 STATUS 2026-10-09) with Mt -0.0041 [-0.0063, -0.0018] / -0.0015 [-0.0055, +0.0029] and Mn_r -0.0121 [-0.0141, -0.0100] / -0.0144 [-0.0173, -0.0116] (K-2 STATUS 2026-10-05), D +0.0080 [+0.0062, +0.0097] / +0.0130 [+0.0095, +0.0169]; and R-L (longer budget), "inflated by the twin's own cost" with Mt +0.0023 [+0.0008, +0.0038] / +0.0031 [+0.000336, +0.0058] and Mn_r -0.0028 [-0.0043, -0.0011] / -0.0023 [-0.0045, -0.000098] (K-2 STATUS 2026-10-09), D +0.005107 [+0.0034, +0.0069] / +0.005410 [+0.0034, +0.0078]. F-25's S3 L3 SPLIT fire has the Mn_r shape. See SURVIVES-STRONGER, SPLIT, Dilution.

**Existence.** The first of the three layers; see The three layers and K-2.

**Extend-signal breakdown.** F-21 finding duty (i): the offset-5 heads that gate every EXTEND land WORSE than the trivial train-mean baseline on TEST (free 0.05469985821808974 / tel 0.05974761296262184 vs trivial 0.052217), so the registered actuator was mostly steering on noise wherever it extended; the measured null prices the actuator WITH that channel, and a stop-only variant was never registered.

### F

**Feature sets (a), (b), (c), (h), (t), (at), (abt), (atn).** Phase-3 probe inputs (F-15, F-16). (a) = ALL logged free summaries of p_a (657 dims at S1: bucket masses in four k-spaces, entropy, top-32 probs); (b) = telemetry only (slot multi-hot: 2048 at S1, 1024 at S3); (c) = both; (h) = the anchor hidden state h_a (4096 dims at S1, 2048 at S3; the OQ-6 denominator); (t) = 560 prefix-topic dims; (at), (abt) = concatenations; (atn) = (a)+(t)+alignment-destroyed slots, dims equal to (abt). The K-2 estimand is (c)-(a).

**Finding (F-N).** An entry in FINDINGS.md; see Prefixes. At HEAD there are 24 (F-0..F-23) and tools/lint_findings.py passes on all of them (dated 2026-10-01: 27, F-0..F-26; the lint line reads "27 findings, all carry regime + tracked evidence"; dated 2026-10-14: 29, F-0..F-28, the lint line reading "29 findings, all carry regime + tracked evidence").

**Firing conditions (K-2 probe rule).** A triple FIRES iff (c)-(a) has CI95 lower > 0 AND all three train seeds are positive AND the point is >= +0.005 (the materiality floor) (F-15). Original S1 grid: 10 of 12 offset>=2 triples fired; S3 primary: 7 of 12, reproduced cell-for-cell on replication (F-17).

**FLOOR-MATERIAL.** F-27's label per population (docs/BLUEPRINT.md, "SEED-NOISE FLOOR READOUTS REGISTRATION"): FLOOR-MATERIAL iff f_one at n = 30 is at or above 0.02, the pinned one-sided kill threshold, else FLOOR-WEAK; f_one is the share of 1,000 prompt subsets in which a +0.062 point win appears by a same-policy seed change alone. Landed FLOOR-MATERIAL on both populations: 0.1060 (SE 0.0065) on K3, the label population, and 0.1320 (SE 0.0070) on OQ15, the replication, neither within two SEs of its threshold; the stage word NOTE-STANDS iff FLOOR-MATERIAL on K3 (NOTE-COLLAPSES iff FLOOR-WEAK on K3), landed NOTE-STANDS. A cross-seed, same-policy, single-comparator null on the four committed vanilla gamma-4 verdict runs; the same-seed null the record's gate legs faced is not measured. NON-CRITERION. See BAR-RESOLVED@210 / RULE-LEAKS@30, Win bar (+0.062 tokens/call).

**Fold-back / fold-back #1 / fold-back #2.** What K-3's kill text prescribes after a null: try a mechanistically different actuator, once. The FOLD-BACK COUNT AMENDMENT (docs/BLUEPRINT.md, 2026-09-02, made content-blind while the seed-1 rerun was in flight) widened "once" to a pinned two-lane sequence: #1 = OQ-15 (outcome-supervised head), #2 = OQ-16 (vector reconstruction -> SD^2 injection), run only if #1 nulls in conversion mode; hard stop after #2 or the skip; no third mechanism. Both ran: #1 nulled in conversion mode (F-21); #2 passed Stage R (F-22) and sits at its user-gated actuator stage.

**Free information / free features / FREE.** Everything a speculative decoder already has at the last verified position: the target's distribution p_a and its summaries (bucket masses, entropy, top-32 ids and probs) and, in live scheduling stages, the draft's own confidence q_sig. D-5 makes it the mandatory baseline. In OQ-15/OQ-16, FREE = the 657-dim scheduler.probe_input core (results/real/oq16_stage_r.json feature_dims). F-12 measured free-information bucket-bias STEERING at zero on real models (best arm +0.0025 [-0.0028, +0.0079]); F-15/F-17 measured free-information PREDICTION as collapsing to the majority floor by offset 3 at S1 and already at offset 2 at S3.

**free_lastp.** The D-5 baseline policy: steer the draft from the target's last verified distribution p_last via its bucket masses. Two D-11 variants: SOFT (bucket masses of p_last) and SHARPENED / free_lastp_sharp (one-hot at argmax p_last; an hf_specdec --bucket-source value). Synthetic: identical to the stale oracle (F-6). Real: null-to-negative (F-12).

**Free actuator / FREE-ACTUATOR WIN / NULL.** After F-23, the only live question the Stage-A instrument can still answer: does injecting the verifier's OWN anchor state h_a (computable from p; arm 8, code name oracle_h) into the frozen drafter convert to tokens per call on this box? It sits outside the K-3 kill text and outside the OQ-16 lane's telemetry claim; it runs only under its own dated registration (V vs O, seed 4, the frozen +0.062 bar and budget guard), and a WIN is an SD^2 configuration result (frozen drafter, rank-512 adapter, single-position final-norm read, gamma 4, NF4 verifier), never a sideband result. Unregistered and unrun at this commit.

**FREETOK.** DR-2's equal-dims, deployment-free comparator: FREE ++ a 2048-dim multi-hot of the anchor's top-32 next-token ids hashed mod 2048 (about 62 ids per bin, identity partly lost; 2705 dims). It reconstructs h_a CI-clear slightly BETTER than TEL (tel_vs_freetok -0.004792 [-0.007192, -0.002600]; FREETOK R^2 +0.258 vs TEL +0.253 under the clip) and reaches freetok_vs_free +0.173871 [+0.164704, +0.182838] (F-22; results/real/oq16_stage_r_dr.json). It is the mandatory Stage-A free comparator (free_inject, arm 9), reaffirmed after DR-4.

**FREETOK2.** See TOK_A / TOK_B / FREETOK2.

### G

**Gamma (block length).** The number of draft tokens proposed per verify call. Default 4 (blocks of up to 5 emitted tokens including the bonus token). gamma-6 is the always-extend control (K-3 arm 5: seed-1 tokens/call 3.428206 at dpe 1.750186 vs vanilla 3.020427 at 1.324316, F-19 - raw tokens/call bought information-free).

**Gate-open rate.** The fraction of steerable positions at which the disagreement gate fires. K-7's diagnostic bar: above about 0.8 means the gate is not doing its job. Measured 0.94 at C=510 (F-12) and 0.55-0.56 / 0.67 / 0.80-0.81 at C=15/31/62 (F-13).

**Glue bucket.** Function-token buckets (", the, ., a, and, of, to, 's", markdown markers, pronouns per F-11). Identified by the K-7 rule: rank tokens by frequency in TARGET-ONLY generations, take the top 100, glue = the shortest bucket prefix (by frequency-mass share) reaching 80% cover (sideband.glue.identify_glue_buckets). Real: 2/2/4 buckets at k=256/512/1024 (F-11); at k=512 the glue buckets are {59, 403} (F-12); glue tokens are 41% of generated text (F-11). Excluded from both sides of any prediction or gate argmax (D-7).

**Glue tax / function-word tax / F-3 tax.** The self-cancellation of ungated bucket boosting: wrong-concept positions gain, already-right positions pay because boosting a bucket steals mass from glue tokens. Synthetic: acceptance collapses to 0.4376 at beta=6, -0.18 (F-3). Real: the always-gate control lands at -0.0168 [-0.0232, -0.0104] vs gated -0.0098 (F-12).

**Granularity trap.** F-14's summary of the bucket-bias actuator: fine k has headroom (0.61 concept-cross at k=512) but a useless gate and stale forecasts; coarse k has a working gate but true concept disagreement collapses to about 16% and the ceiling is <= +0.0069. The fine-k oracle cell (perfect forecast x the 0.61 headroom) is the untested remainder.

**Grid-edge.** See Ridge / lambda / grid-edge duty.

### H

**h_a.** The anchor hidden state at the position that produced p_a: the model.norm output, 4096 dims, float16 on disk, at S1 (F-22); the S3 harvest's hidden reference feature (h) is 2048-dim (F-17), its capture point not stated in the finding. It is the SD^2 steering vector's position, OQ-6's denominator, and OQ-16's reconstruction target. Observability-violating - never a deployable source; injected only as the D-2-named oracle_h ceiling.

**H-ABSORBS.** R2's hidden-state (Q2) label in the OQ-9 prefetch rungs (docs/BLUEPRINT.md, the R2 registration; F-26's status lines of 2026-10-03 and 2026-10-04): H-SURVIVES iff D_eq^H and D_add^H both read SIGNAL, H-COMPLEMENTARY iff only D_add^H does, H-ABSORBS iff neither does, H-INCONSISTENT iff only D_eq^H does; a NEGATIVE reading is "not SIGNAL" and is said in those words. With the forward's stored final-norm state (clipped, z-scored and reduced to 1024 principal directions on train) in the free arm beside the smoothed token tables, neither reading is SIGNAL at horizon 1 (primary / replication): D_eq^H (history_bigram_r2 - free_h, 3073 against 3073 dims) +0.0111 [+0.0078, +0.0150] / +0.0106 [+0.0068, +0.0153] and D_add^H (history_all_h - free_h) +0.0172 [+0.0139, +0.0210] / +0.0162 [+0.0126, +0.0206], both CI-positive below the +0.05 floor, so in the frozen wording "no material margin (at or above +0.05) of the address block over the equal-dims free block, nor of the address stream over the free bigram plus the hidden block, is shown" and "STAGE 2's ADDRESS-BEYOND-FREE MOTIVATION IS STRUCK" (docs/WHY_THIS_DIES.md K-6 STATUS 2026-10-03; beside the strike, as pinned, D_add^H on the unseen-key positions +0.0399 [+0.0279, +0.0514] / +0.0286 [+0.0195, +0.0386], NOT-SHOWN with the primary's CI95 containing the floor). In the registration's own words "absorbs" names the label, not a mechanism. The horizon read extends the reading to horizons 2, 3 and 4 (see LEAD-TIME-ABSORBED); the hidden state in the free arm is the alternative K-6 names (ship a vector), and the datum "points toward the alternative, not the premise" (K-6 STATUS 2026-10-04). See ADDRESS-BEYOND-TOKEN, R2-FALLBACK-SURVIVES, Kill criteria K-6.

**HANDOFF.md.** An untracked, gitignored session-state file, not committed evidence; its most recent note records the session state; no Stage-A GPU run exists. Nothing in FINDINGS.md rests on it.

**Hard stop.** After fold-back #2 (or the skip) no third mechanism exists or may be registered (FOLD-BACK COUNT AMENDMENT). Within OQ-16, every branch of the partition ends the lane (the hard-stop clause) except a Stage-R PASS, which authorizes exactly one user-gated actuator stage, after which the lane ends regardless of outcome (docs/BLUEPRINT.md OQ-16 ARC REGISTRATION, paraphrased); DR-5 is forbidden without an explicit user exception.

**Hardened telemetry.** Synthetic telemetry-noise parameters (support_gain=0.5, support_noise=0.5, background_noise=0.25, top_n=16) used in e05/e06/e07 (F-5, F-7, F-9) so that sidecar decoding is non-trivial.

**Harvest.** The Phase-2 protocol: run the TARGET alone (no draft) on the 210 prompts across generation seeds, logging per anchor the telemetry, the free summaries of p_a, h_a and the generated tokens, block-start aligned, with a volume bar of >= 1M (anchor, offset) pairs for a full harvest. S1: harvest_shadow (seeds 0..7, 1,693,036 pairs) + harvest_shadow_r (seeds 8..11, 849,536 pairs, half volume by registered design) (F-15); S3: harvest_moe (1,647,264 pairs) + harvest_moe_r (827,324) (F-17). Raw npz files are gitignored; metas and summaries are committed and sha-bound.

**Horizon.** How many tokens ahead telemetry demonstrably carries information: 2-3 at S1 (F-15; offset 4 not established); at S3 offset 2 in L1, 3 in L2, 4 in L3 (F-17).

### I

**Information-ceiling null vs conversion-mode null.** OQ-15's two null branches (FOLD-BACK COUNT AMENDMENT decidability pin; OQ-15 arc registration). Information-ceiling: the telemetry head fails to beat the matched free head on held-out outcome prediction, so the stream carries no acceptance-relevant information above free and OQ-16 is skipped. Conversion-mode: Stage I passed but the derived policy fails its bar; hands off to OQ-16. Unclassifiable outcomes default to information-ceiling null. F-21 landed CONVERSION-MODE NULL because Stage I passed mechanically despite its ARTIFACT-DOMINANT label.

**Information-free extend channel / gamma inflation.** Raw tokens/call rises with gamma regardless of information (emitted = accepted + 1), so any always-extend arm clears a raw tokens/call bar; docs/ECONOMICS.md section 5 amendment 1 introduced the matched-budget frame and the pairwise guard to block it, and F-19's gamma-6 control confirmed the arithmetic (about +0.41 tokens/call, seed-1 pooled 3.428206 vs vanilla 3.020427, for +0.43 dpe).

**Invariance leg.** F-22's requirement that the extended Stage-R tool with all diagnostic modes OFF reproduces the registered numbers: it held on every gate-bearing field, with the REPORTED trivial MSE differing by one ULP (0.9900697257801255 vs 0.9900697257801256) for a summation-order reason explained per the pin (results/real/oq16_stage_r_inv.json).

**Isolated RNG stream.** D-6: a policy that reads telemetry draws from its own generator so reading cannot perturb the shared draft/verify trajectory. The READ-ONLY / containment property of byproduct logging (E8, E10) is its live form.

### K

**K-2-ISOLATED.** The registered K-2 word at S3 over STAGE READERS and STAGE READERS-LONG of F-28's reader-and-lens re-test (docs/BLUEPRINT.md, "READER-AND-LENS RE-TEST AT S3 REGISTRATION"): K-2-ISOLATED iff some valid (reader, space) cell reads SURVIVES-STRONGER but the REOPENED condition fails (not reopen-grade, or at the lopsided lens, or S1 not reopen-grade, or S1 not yet run), where a cell is reopen-grade iff SURVIVES-STRONGER with the FULL licence AND Mt firing the Phase-3 triple rule on both harvests; its siblings: K-2-NOT-OVERTURNED-AT-S3 (every valid (reader, space) cell reads ABSORBED or NOT-SHOWN), K-2-UNSETTLED (some valid cell reads SPLIT and none SURVIVES-STRONGER), K-2-INCOMPLETE (no valid cell exists) and K-2-REOPENED-AT a (reader, space) cell (the reopen branch); the lopsided lens never decides a reopen. Landed FINAL on 2026-10-09 (docs/WHY_THIS_DIES.md K-2 STATUS, superseding the interim word of 2026-10-05): under R-N (hz-rescaled), R-T (two-tower) and R-L (longer budget) at the S3 gate cells the SURVIVES-STRONGER cells are R-N and R-L at the lopsided L3, both EQUAL-DIMS-ONLY, at a lens "which never decides a reopen"; "no reopen-grade cell anywhere"; the S3 L1 kill of 2026-09-06 stands as a statement about the registered reader; S3 L3 stays OPEN at the registered reader (F-25's SPLIT); S1 not run (final); "one more family of readers, not K-2's universal". See Kill criteria K-2, SURVIVES-STRONGER, Mega-group lens.

**K-2-NOT-OVERTURNED-AT-S1.** The registered S1 word of F-29's S1 reader
re-test (docs/BLUEPRINT.md, "S1 READER RE-TEST REGISTRATION", 2026-10-16),
issued by tools/run_reader_s1.py over the valid readers at the S1 gate cell
from the frozen per-reader labels: K-2-INCOMPLETE-AT-S1 iff no valid reader;
K-2-REOPENED-AT-S1 iff some valid reader is reopen-grade (SURVIVES-STRONGER
with the FULL licence and Mt firing the triple rule on both harvests), per
source, PROVISIONAL until a reader-matched rider passes; K-2-ISOLATED-AT-S1
iff some valid reader reads SURVIVES-STRONGER without reopen grade;
K-2-UNSETTLED-AT-S1 iff some valid reader reads SPLIT and none
SURVIVES-STRONGER; K-2-NOT-OVERTURNED-AT-S1 iff every valid reader reads
ABSORBED or NOT-SHOWN (narrowed where ABSORBED, not where NOT-SHOWN);
precedence in that order. Landed 2026-10-17: R-N (hz-rescaled) ABSORBED; R-T
(two-tower) ABSORBED; R-L (longer budget) ABSORBED; K-2-NOT-OVERTURNED-AT-S1
(under readers R-N, R-T and R-L at S1; one more family of readers, not K-2's
universal); the S1 kill of 2026-09-06 stands as a statement about the
registered reader; the S3 word K-2-ISOLATED (final) does not move. See
K-2-ISOLATED, SURVIVES-STRONGER, Kill criteria K-2.

**K-3 arms 1-5.** Attempt #1's arms (F-19): 1 vanilla gamma-4; 2 draft-confidence stop/extend (the incumbent-style comparator; selected stop q0.25 / extend q0.5); 3 the (a)-probe free-signal scheduler (q0.95 / q0.05, degenerate tuning); 4 the (c)-probe telemetry scheduler (the bet; q0.4 / q0.05, re-frozen q0.35 / q0.05 under the void); 5 fixed gamma-6 (information-free control, never in the gate minimum).

**Kill criterion (K-N).** A pre-registered death condition in docs/WHY_THIS_DIES.md; see the Kill criteria section above.

**KV cache / --no-kv-cache rider / KV-crop fast path.** Real runs use per-prompt KV caches; a pre-registered cached-vs-uncached A/B must pass bidirectionally (six containments) before cached numbers are cited (K-1 rider; F-10, F-12, F-14). The HF adapter recomputes prefixes rather than cropping the cache, so it is acceptance-valid only; wall-clock claims are banned until a KV-crop fast path exists (D-9, CLAUDE.md). Dated erratum 2026-10-16: the two clauses before this one were false when written (2026-09-05): the adapter crops the cache (DynamicCache.crop to the verified prefix after every block in src/sideband/real/hf_specdec.py, the default since b1dae57, 2026-08-29; --no-kv-cache selects the exact-recompute reference), so "KV-crop fast path" names the path that exists; acceptance-valid only, and the wall-clock ban, stand on the absence of a benchmark harness (DECISIONS.md D-9, dated note 2026-10-16).

### L

**Label spaces L1 / L2 / L3.** Probe target spaces (F-15): L1 = concept_k16 (16 k-means buckets, merged glue class included); L2 = concept_k512 (510 concepts + a merged glue class); L3 = concept_groups_v1 (transition-coherent groupings of the k512 buckets, fit on the train split only; a lopsided "mega-group lens"). OLMoE variants carry the suffix _olmoe (F-17).

**Lane A / Lane B.** docs/ECONOMICS.md section 4's deployment lanes. Lane A = software telemetry in MoE serving: the router's top-k indices are computed anyway, no device; value = a two-orders-of-magnitude cheaper input than SD^2 plus the unclaimed index-only research cell; bar = the K-3 WIN bar; verdict language "real, free, modest". Lane B = the hardware memory-side device in fetch-on-demand regimes (MoE offload, KV-page offload, CXL tiers, multi-tenant or confidential boundaries); needs point acceptance delta >= +0.044 AND a defended boundary where SD^2's vector cannot cross. Neither bar is met at HEAD.

**LEAD-TIME-ABSORBED.** The horizon read's stage label (docs/BLUEPRINT.md, "OQ-9 STAGE-1 HORIZON READ REGISTRATION"; F-26's status line of 2026-10-04; K-6's lead-time datum): LEAD-TIME-ABSORBED iff H-ABSORBS at every horizon j in {2, 3, 4}; LEAD-TIME-SURVIVES@j iff H-SURVIVES at some j, j the smallest such horizon; LEAD-TIME-COMPLEMENTARY@j iff no H-SURVIVES and H-COMPLEMENTARY at some j; LEAD-TIME-INCONSISTENT otherwise; the primary harvest's label is the label, the replication computed identically and reported as agrees / disagrees. Landed LEAD-TIME-ABSORBED on the primary (H-ABSORBS at horizons 2, 3 and 4; horizon 1 reproduces R2's H-ABSORBS cell), the replication agreeing on the stage label and on every per-horizon label, with no floor straddle, no reader guard and no free_h grid edge at any label horizon on either harvest, so the pinned cross-harvest closure condition held. The address stream over the strongest free arm R2 built, in hit rate (primary / replication): horizon 2 +0.0178 [+0.0138, +0.0223] / +0.0153 [+0.0113, +0.0203]; horizon 3 +0.0173 [+0.0129, +0.0223] / +0.0135 [+0.0093, +0.0187]; horizon 4 +0.0149 [+0.0105, +0.0198] / +0.0104 [+0.0062, +0.0154]; every one of the six label readings NOT-SHOWN by the rule. In the record's words "OQ-9's prefetch half closes at this reader"; K-6 stays UNTESTED. See H-ABSORBS, Kill criteria K-6.

**Leviathan rejection scheme / spec_step.** The standard speculative-decoding verifier: accept draft token x with probability min(1, p(x)/q(x)); on rejection sample from the residual normalize(max(p - q, 0)). Implemented once in src/sideband/specdec.py (D-3); exact by construction (F-0, enumeration at atol 1e-12; F-1, worst deviation 2.2e-16). Steering is a pure speed knob: output quality is not on the table.

**Live-tap fidelity rider (E9) / tolerance mapping.** Compares live-captured slots, mass, entropy and argmax at sampled anchors against a fresh teacher-forced recompute, with constants derived mechanically from a calibration run: SLOT_OVERLAP_MIN = 20, MASS_LINF_MAX = 0.11094206571578979, ENTROPY_ABS_MAX = 0.3908865451812744, ARGMAX_GAP = MASS_LINF_MAX (docs/BLUEPRINT.md STAGE-E TOLERANCE AMENDMENT). A FAIL quarantines the live instrument.

**Llama pair.** Llama-3.1-8B-Instruct target (NF4) + Llama-3.2-1B-Instruct draft (bf16), one shared tokenizer, gamma 4, temperature 1.0, chat template with a pinned date - the regime of every real steering and actuator finding (F-10 onward). Also SD^2's own pair (docs/PRIOR_ART.md), though at k=8, unquantized and batched there.

### M

**M2 / M3 / M4 / M2n / M2noise.** The P1 readouts (F-16, F-18). M2 = (abt)-(at): the telemetry margin over free+topic. M3 = (at)-(a): what topic adds to free. M4 = (c)-(at). M2n = (abt)-(atn): the telemetry margin against the equal-dims alignment-destroyed twin. M2noise = (atn)-(at): the pure dilution cost of the added dims. S1 primary L1/off2: M2 +0.0177 [+0.0119, +0.0232]; S3 primary cell: M2 +0.012958 [+0.008783, +0.016809].

**Majority floor.** The accuracy of always predicting the most common label - the baseline a probe must lift off. At S3 the floor IS the glue bucket (L1 0.5803 primary, F-17); S1 floors 0.591/0.413 (OPEN_QUESTIONS.md OQ-1, harvest_audit.json). Free information sits ON the floor by offset 3 at S1 and already at offset 2 at S3.

**Matched drafting budget.** The K-3 gate frame (docs/ECONOMICS.md section 5 amendment 1): compare tokens/call only between arms spending the same drafting budget, because raw tokens/call is buyable information-free by drafting more. Implemented as constrained maximization on val plus the pairwise budget guard at verdict.

**Materiality floor (+0.005).** The registered minimum probe-margin point estimate for a triple to count (F-15 firing conditions). Cells CI-positive below it are "CI-positive-immaterial".

**Mechanism-matched.** D-11: a ceiling or baseline must run the same mechanism as the policy it prices. Every later "free arm" is a matched-mechanism arm (Phase 0b soft + sharp, K-3 arm 3, OQ-15 head_free, Stage-A free_inject = FREETOK), and the K-3 WIN gate takes the minimum over comparators for this reason.

**Mega-group lens.** The caveat that L3 (concept_groups_v1) is lopsided: two groups cover about 455 of 510 concepts at S1 (F-15) and about 461 of 510 at S3 (F-17, leading sizes 193 and 268), so L3's larger margins read through a coarse lens. OQ-13's balanced-lens item is the unrun robustness check. Dated 2026-10-14: the balanced lens ran as F-28 (2026-10-05) at S3 only, L3_olmoe_balanced_v1, in F-28's regime line "16 groups of 31 or 32 concepts; cap 32 against the lopsided lens's 268"; through it S3 L3 reads ABSORBED at the registered reader where the lopsided lens read SPLIT (F-25); S1 L3's mega-group never got a balanced read.

### N

**n_steerable.** The number of drafted positions at which a gated policy could fire, the denominator of the gate-open rate (F-14: 69,192 for the oracle arm); the free arm's count excludes each prompt's first block, the oracle's includes it (F-14 comparability footnote).

**NF4.** 4-bit NormalFloat quantization (bitsandbytes; --load-4bit, double-quant, bf16 compute): the primary real-model regime for the 8B target on the 12 GB RTX 3080 Ti. A 20-prompt bf16 confirmation arm exists for K-1 (F-10: mass 0.787 [0.764, 0.809], with a quantization shift on mass of +0.031 [+0.003, +0.060]). At S3 the routers and lm_head are excluded from quantization (F-17).

**NON-CRITERION.** A registered diagnostic that reports and prices but cannot change a verdict or partition branch (P1, DI-1, DR-1..DR-4, OQ-13 items). The registrations say so in those words.

**NOT WIN / WIN / NULL.** Gate outcome labels. WIN requires every leg to hold (all-hold form); NOT WIN is the mechanical result when any leg fails; NULL is the partition classification attached to a NOT WIN (e.g. CONVERSION-MODE NULL, F-21).

**NOT-SHOWN.** A conclusion label in two registered families, distinct from the status word "not shown" in the table at the top. (i) In the full-free re-tests (F-24, F-25, F-28): the label at a (source, space) when the gate fired on neither harvest and some D row's CI95 upper is at or above +0.005, "Neither survived nor fired" (docs/WHY_THIS_DIES.md K-2 STATUS 2026-09-14). S1 L3 at the registered reader (F-25; primary / replication): the gate D +0.0010 [-0.0006, +0.0026] / +0.0012 [-0.0015, +0.0040] fires on neither harvest and the linear off2 D row -0.0028 [-0.0052, -0.0005] / +0.0029 [-0.0007, +0.0063] has its replication upper at or above the floor; R-N (hz-rescaled) at the balanced L3 (F-28, one gate D row per harvest): D +0.0040 [+0.0025, +0.005385] / +0.0045 [+0.0027, +0.0061], the upper at or above the floor on both. (ii) In the prefetch readouts (F-26 and its rungs): a reading that is neither SIGNAL (paired CI95 lower > 0 and point >= +0.05) nor NEGATIVE (CI95 upper < 0), so a CI-positive reading below the +0.05 floor reads NOT-SHOWN and is written "no material margin ... is shown". See ABSORBED, SPLIT, ADDRESS-BEYOND-TOKEN.

### O

**Observability constraint.** The premise that only addresses (widened by D-1's scope note to "almost nothing") cross the wire - no activation values, no logits. SD^2 is the comparator that violates it by shipping a full hidden vector per verified position. Lane A owns that the constraint is self-imposed in software; Lane B needs a real boundary (K-6).

**Offset.** Distance ahead of the anchor, 1..gamma. Offset 1 is the anchor's own sampled token (free-saturated: adding telemetry HURTS there, every (c)-(a) CI-negative at offset 1 on both S1 runs, the internal leak control in F-15). Offsets 2-3 are the demonstrated S1 horizon.

**OLMoE.** allenai/OLMoE-1B-7B-0125-Instruct: the S3 source model, 16 MoE gates each routing top-8-of-64 experts; harvested target-only, routers and lm_head excluded from quantization (F-17). No draft partner is verified for it.

**Open question (OQ-N).** An entry in OPEN_QUESTIONS.md; see the Open questions section above.

**Operational bar (+0.044 acceptance).** The Lane-B bar (docs/ECONOMICS.md section 5): point acceptance delta >= +0.044, about +0.27 tokens/call via the coupling, 8.8% of the 3.11 base; like-for-like on SD^2's accepted-tokens base about 37% of SD^2's gain, harder than its "25% of SD^2" motivating label. The memo flags the coincidence that +0.044 is numerically the top of S1's probe-margin range: the units differ, nothing follows.

**Oracle (stale / fresh / oracle_nextp / oracle_h / oracle_concept_now).** D-2-named non-causal CEILINGS. Stale oracle = the true concept at block start, held; fresh oracle = the true concept at each position (synthetic, F-3/F-4); oracle_nextp (F-14) = the target's own fresh p_j concept posterior per drafted position; oracle_h (Stage A, arm 8) = the TRUE h_a injected into the drafter (the actuator ceiling). They bound what any predictor could achieve through a mechanism; never deployable.

**Outcome head / a_hat.** OQ-15's closed-form ridge regressor predicting per-position analytic acceptance from anchor features; a_hat_j is its prediction at offset j. Offsets 1-4 come from Stage I, offset 5 was trained at freeze time on the arm-5 byproducts (F-21). The offset-5 heads landed worse than the trivial baseline; see Extend-signal breakdown.

### P

**P(k=0..4) accepted-length distribution.** From the committed phase0b vanilla records: 0.2509/0.1751/0.1341/0.0953/0.3445 over 17,220 blocks, E[emitted per call] 3.1071 (docs/ECONOMICS.md section 5; F-19 CONTROL ARITHMETIC) - the evidence that the information-free extend channel is real. Its geometric-tail extension over-predicted the measured gamma-6 tokens/call by +0.185 (F-19), disclosed as geometric-tail optimism.

**P1 / P1-analog.** The registered post-hoc diagnostic testing whether a probe margin is merely prefix TOPIC STATE: feature set (t) = 560 decoder-free dims of concept histograms over already-generated tokens; readouts M2/M3/M4/M2n/M2noise; pinned labels P1-SURVIVES vs P1-DEFLATES. Ran at S1 (F-16) and, as the S3 P1-analog, at S3 (F-18); SURVIVES both times at the histogram-family level, with the prompt-token residual and richer prefix families explicitly left open.

**P-stage.** The Phase-4 PRECONDITION run of K-3 Attempt #1: arms 1-3 on the verdict population at the verdict seed, evaluated BEFORE the telemetry arm; had the free-signal arm (3) beaten vanilla the arc would have folded back early. F-19: arm3-vs-arm1 +0.000451 [-0.001952, +0.003220], NO FOLD-BACK.

**p_a / p_last / last-p.** The target's next-token distribution at the anchor (last verified position). Offset-1 labels are by construction the token sampled from it; its summaries are the free feature set (a).

**Paired / identical seeds.** D-6: arms run on the same prompts with the same per-prompt RNG streams so deltas are within-prompt differences. Cross-version bit-exact reproduction (F-8: e03 vanilla 0.6194399309459379 bit-exact after the pipeline rewrite) confirms pairing survives code changes.

**Pairwise budget guard.** The verdict-time tolerance: the tested arm's verdict-population dpe must be <= each comparator's dpe + 0.01 (epsilon pinned; the information-free skew residual measured at +0.0103 tokens/call, 17% of the bar; docs/ECONOMICS.md section 5). Breached twice by MECHANISM in F-19 (val->verdict budget inflation of the probe arm's extend channel: arm-4 dpe 1.313115 vs allowed 1.284202 at seed 0, 1.317033 vs 1.285681 at seed 1); breached once in F-21 by a SELECTION-TIME gap (0.00544107351372447 over the allowance at seed 2), cleared at seed 3. With gamma fixed (Stage A) the guard is mechanical.

**Persistence.** See Staleness / persistence / run length / hold rule.

**Phases 0a / 0b / 0c / 1 / 2 / 3 / 4 / 5.** docs/BLUEPRINT.md's plan: 0a the real cross-bucket audit (K-1; F-10, F-11); 0b the free-information steering baseline (F-12); 0c coarse gating / OQ-12 plus the attribution rider (F-13, F-14); 1 the synthetic testbed (F-2..F-9, with F-0/F-1 the verifier-exactness floor); 2 the real telemetry harvest; 3 the existence test / K-2 (F-15..F-18); 4 steered speculative decoding end to end / K-3 (F-19..F-22 and Stage A); 5 the hardware-premise memo (docs/ECONOMICS.md skeleton).

**posterior_bias (centered posterior mechanism).** D-10's default: bias concept bucket b by beta*(P(b) - 1/C), glue 0 (sideband.steering.posterior_bias). Bidirectional: boosts the predicted bucket and demotes other topical buckets. "soft" = bucket-mass posterior; "sharp" = one-hot posterior. The mechanism actually run on real models in Phase 0b/0c (F-12, F-13, F-14).

**PREFETCH-HEADROOM.** F-26's stage label on the primary OLMoE S3 harvest (docs/BLUEPRINT.md, "OQ-9 STAGE-1 PREFETCH READOUTS REGISTRATION"): PREFETCH-HEADROOM if not CACHE-SUFFICIENT and HISTORY or INTRA-FORWARD reads SIGNAL; PREFETCH-NOT-SHOWN if not CACHE-SUFFICIENT and neither does; INCOMPLETE if any registered arm or label cell is missing on the primary harvest; CACHE-SUFFICIENT iff RECENCY_16 at j = 1 is at or above 0.90. Scope, in the registration's words: "HISTORY and PREFETCH-HEADROOM are scoped to address-only readers against the cache policy and license nothing about the address stream being needed once tokens[t] is in the reader". Landed, the seed replication agreeing on every label (primary / replication): CACHE-SUFFICIENT did not fire, RECENCY_16 0.5197 [0.5144, 0.5258] / 0.5155 [0.5092, 0.5223] and RECENCY_32 0.7755 [0.7713, 0.7799] / 0.7750 [0.7701, 0.7802]; HISTORY SIGNAL +0.2867 [+0.2784, +0.2939] / +0.2901 [+0.2808, +0.2978]; INTRA-FORWARD SIGNAL +0.4861 [+0.4710, +0.5009] / +0.4816 [+0.4663, +0.4975]; the arms at B = 16, j = 1: recency 0.5197 / 0.5155, free_tok 0.8111 / 0.8036, history 0.8064 / 0.8056, history_tok 0.9143 / 0.9108. A hit-rate count at linear readers on a harvest: "no bytes, latency, wall-clock or boundary is priced"; NON-CRITERION, a K-6 datum; the label "does not depend on" the ADDRESS-BEYOND-TOKEN margin and stands through the later rungs. See ADDRESS-BEYOND-TOKEN, Kill criteria K-6.

**Prefill.** The one-per-prompt target forward that primes the KV cache and produces the first block's anchor read at the prompt's last position; present in every arm; excluded uniformly from the verify-call count (E6).

**Probe.** A small classifier (linear or mlp256) trained on anchor features to predict the target's bucket at offset j (src/sideband/probes.py; tools/run_probes.py). "Probe margin" = accuracy(c) - accuracy(a) in top-1 accuracy units - NOT acceptance units (docs/ECONOMICS.md section 1).

**Prompt-cluster bootstrap.** The house CI: resample PROMPTS (clusters) with replacement, recompute the pooled statistic, take the percentile CI95; n_boot 2000, seed 0 by default in sideband.stats (cluster_bootstrap_ci, paired_cluster_delta_ci; 20000 in tools/analyze_phase0b.py per F-12). Never the independence CI. paired_ratio_delta_ci resamples both arms jointly for ratio-of-totals deltas (tokens/call, standardized MSE).

### Q

**q_sig / draft confidence.** signal_j = q_j(x_j), the draft's probability of its own sampled token at drafted position j (E3). K-3 arm 2 stops on LOW q (the SpecDec++ feature class, the incumbent comparator); in OQ-15 it sits inside the FREE feature set; it does not exist at the anchor, so OQ-16's features exclude it (F-22 regime).

**Quarantine.** Leaving result columns unread until a registered condition is evaluated - gate metrics under a guard breach (budget columns only consulted; F-19, F-21), or a control's labels before its pins are applied. A discipline against post-hoc tuning; F-21 records holding comparators unread "beyond the letter".

### R

**R1 / R2 / R3 riders.** Phase-3 probe-run riders (F-15, F-17): R1 = harvest fidelity (stored telemetry vs a fresh recompute at sampled anchors, calibrated tolerances); R2 = label-shuffle control (the probe must collapse to floor under shuffled labels); R3 = split hygiene. A rider PASS is a precondition, not a result.

**R2-FALLBACK-SURVIVES.** The coverage (Q1) label of the generalising-free-baseline rung R2 (docs/BLUEPRINT.md, "OQ-9 STAGE-1 GENERALISING FREE BASELINE REGISTRATION (R2)"; F-26's status line of 2026-10-03): R2-FALLBACK-SURVIVES iff D_eq^R2 on the FALLBACK positions reads SIGNAL; R2-POOLED-ONLY iff it does not on FALLBACK but does on ALL; R2-ABSORBED iff neither; a NEGATIVE reading is "not SIGNAL". On the unseen-key positions (0.0987 / 0.1418 of the test positions, primary / replication) the address block's margin over a generalising free encoding (the twin's count tables with the model's own routers replayed on the token's normalised input embedding as the Dirichlet prior of each key's row, k = 128 selected on val) reads SIGNAL, +0.0732 [+0.0623, +0.0834] / +0.0662 [+0.0559, +0.0773], so "the located margin is NOT shown to be table sparsity at this encoding and the coverage caveat stands as a scoped limitation, not a retraction, at this reader (B = 16, j = 1)". Its companion label H-ABSORBS answers the hidden-state question the other way. See ADDRESS-BEYOND-TOKEN, H-ABSORBS.

**Re-freeze.** Re-selecting an adaptive arm's thresholds on val evidence only after a void, toward lower budget (K-3: stop q0.4 -> q0.35; OQ-15 Stage C: new cap = the comparator's own selected val budget 1.2858072916666667, giving a unique cell stop q0.15 / extend q0.75). Output files carry selection_label VOID_REFREEZE (F-19, F-21).

**RECONSTRUCTION-CEILING NULL (OQ-16 partition branch, NOT claimed).** The OQ-16 partition's conservative branch ("Stage-R leg 1 fails") and its catch-all target. F-23 does not claim it: the measured leg-1 pass contradicts the branch's definition, and the registered limbo clause forbids re-labeling a never-run Stage A as a null. F-23's disposition is instead the partition's own VOID precedent - no branch claimed, a dated note, the lane stops in practice under the fold-back hard stop - under the name CLOSED BY DATED ERRATUM, mechanism TARGET-FREE. STAGE-R PASS stands as the mechanical outcome of its gate. (The first draft of F-23 claimed the catch-all; the critic round removed it before the commit.)

**Reconstruction.** The third of the three layers; see The three layers and Stage R / Stage A.

**Recovery.** Synthetic metric: (policy gain) / (mechanism-matched oracle gain). F-5 and F-7 report it per sideband width K; a recovery above 100% against the wrong ceiling is the cautionary case behind D-11.

**Regime (regime tag).** The exact conditions a number was measured under - models, quantization, gamma, temperature, prompts, seeds, bucket space, cache path - stated on every finding's `- regime:` line (D-4). Synthetic regime = "concept-HMM v0"; real regime = "REAL MODELS (Phase ...)" with the pair named. A finding cited outside its regime is a bug.

**Registration / pre-registration / pinned.** Writing cells, readouts, bars, comparators and conclusion labels into docs/BLUEPRINT.md, dated, BEFORE the governed result exists - post-hoc diagnostics included (CLAUDE.md working practices). "Pinned" = fixed at registration. Amending a bar after its result is read is prohibited; dated pre-result amendments are allowed.

**Replication (pinned triple).** A fresh-seed rerun of the harvest+probe grid whose decision was PINNED to one cell before it ran (S1: L1/off2/linear, pinned after the original grid; S3: L1_olmoe_k16/off2/linear, pinned before the primary grid existed) - the insurance against the about 26% family-wise multiplicity of 12 uncorrected triples (F-15, F-17). "Re-fired" = all three firing conditions held again.

**Reserved seed.** A seed pinned at registration for the single void-rerun: K-3 seed 1; OQ-15 Stage C seed 3; Stage A seed 4 for the verdict with seed 5 reserved (docs/BLUEPRINT.md STAGE-A FREEZE).

**Residual distribution / cross-bucket residual mass.** The distribution sampled on a rejection. Cross-bucket residual mass (the F-8 default estimand) = the mean residual mass lying outside the proposed token's bucket - the analytic version of "fraction of rejections that cross a bucket boundary" and K-1's estimand (F-10: 0.778/0.812/0.863 by k).

**Ridge / lambda / grid-edge duty.** OQ-15 and OQ-16 heads are closed-form ridge regressions with lambda the only degree of freedom, selected on VAL. "Grid-edge" = the chosen value sat at the edge of its grid. F-19 has no ridge lambda; its grid-edge events are on the threshold QUANTILE grid (arm 3's all-e0 frontier with a "grid-edge winner"; arm 4's extend threshold at the q0.05 grid edge). Ridge lambda 10.0 at the top of the grid in F-20 (all 24 chosen lambdas) and F-21 (all ten exported heads); 1e5 in F-22's registered run over the widened grid 1e-2..1e5 (the "fourth consecutive event", counting F-19's quantile-grid edge, F-20, F-21, then its own), meaning the free arm was capped short of its optimum and delta_free overstated the free margin by roughly 0.10; DR-1's clip gave the lane's first interior selections (1e4 for free/tel/freetok; noise still at the edge).

**Rule 7 ("fast earns scrutiny").** A working rule of the project's operator (cited by number in F-22; not a repo file): a breakthrough-feeling result is the cue to slow down and check harder. Invoked by name in F-22 when the surprising Stage-R PASS landed, triggering the critic attack round that found the standardization pathology.

**RULE-LEAKS@30.** See BAR-RESOLVED@210 / RULE-LEAKS@30 (F-27 readings).

### S

**Same-anchor redundancy channel.** F-20's named mechanism: TEL's slot dims are partly linearly redundant with the anchor's own 657 free dims, while the noise twin's shifted slots are only prompt-level redundant - a variance-cost asymmetry that can manufacture small positive TEL-vs-NOISE margins without information. The five-seed spread found draw variance of the live margin's own magnitude (sd about 0.0005) rather than a confirmed systematic mean.

**Sampled fraction.** The empirical consistency check for K-1: the fraction of actual rejections whose emitted token lies in a different bucket than the proposed token. It agrees with the mass estimator within 0.003 at every k on real models (F-10), replicating F-8's synthetic concordance.

**SD^2.** "Steering Pretrained Drafters during Speculative Decoding" (arXiv 2511.09844 as recorded in docs/PRIOR_ART.md, which says to re-verify arXiv ids before citing externally): a steering vector from the verifier's hidden state at the last verified position is added to the drafter's MLP hidden states. The project's upper baseline, the OQ-6 denominator, and the actuator template for OQ-16 Stage A. PRIOR_ART's dated correction (2026-09-04): the headline "+35% / +22%" figures are cross-pair maxima ("up to 35% under standard sampling and 22% under greedy"), so the original entry's "+22% throughput" reading is superseded; for the Llama pair at k=8 (blocks of 9, batched, unquantized) block efficiency goes 4.44 -> 4.79 under sampling and 4.51 -> 5.04 under greedy; the drafter is fully fine-tuned, and frozen-drafter steering is their weaker ablation - which is why the Stage-A freeze owns its frozen-drafter, rank-512 deviation and runs an oracle-ceiling rung first.

**Selection-time gap vs val->verdict inflation.** The two guard-breach mechanisms seen so far: F-19's arms inflated their budget from val to verdict (the probe arm's extend channel); F-21's arms selected different distances below the common cap on val (arm 7 0.0136 below, arm 6 0.0398 below; frontier-grid discreteness), knowable at freeze time from the committed selection budgets. Lesson carried: check pairwise SELECTED val budgets against epsilon at freeze.

**Sha header / binding gate.** State files and exports carry sha256s of their inputs (harvest npz, thresholds, head weights, prompts) and the tools refuse on a mismatch; resume refuses a mismatched state header (CLAUDE.md). BINDING-GATED EXPORT = retraining for export must reproduce the committed state cell bit-exact (test_acc, per-cluster counts, val_acc_best, best_epoch; E1) or the export refuses; the Stage-A export binds to results/real/oq16_stage_r_dr4.json the same way.

**Shadow tap / shadow telemetry / ShadowTap.** The S1 instrument: hooks on an INTACT target model that sketch which top-N weight columns would be most important at a layer (real/shadow_telemetry.py; the live ShadowTap inside hf_specdec for the K-3 arc). "Shadow" because it simulates an observer without corrupting the model (D-1).

**Shrinkage / winner's curse.** The drop from a val-tuned advantage (a maximum over many search evaluations on 30 prompts) to the fresh-prompt verdict: the telemetry arm's +0.060 over vanilla on the tuning prompts shrank to +0.007 in F-19. The F-19 caveat says the mechanism applies to every tuned arm symmetrically.

**Sideband.** The narrow observability channel from the weight-serving side to the drafter - the project's name and premise. Width priced in bits per token in docs/ECONOMICS.md section 3: S3 768/513, S1 1152/676, against SD^2's 65,536 bits per verified position.

**Sidecar / decoder.** The small model that reads the sideband and emits a steering posterior or a schedule decision. It must fit inside the draft loop's latency budget (K-5, OQ-5), which has never been timed.

**Slots.** The per-layer set of telemetry addresses at an anchor (int16, sorted-unique, -1-padded): top-32-of-512 weight slots per tapped layer at S1 (layers {7, 15, 23, 31}), top-8-of-64 expert ids per gate at S3. Fed to probes as a multi-hot vector (2048 dims at S1, 1024 at S3).

**Source line.** A finding's `- source:` line: committed evidence paths (results/, experiments/, tests/, docs/, src/); tools/lint_findings.py checks that the paths exist (D-4).

**SpecDec++.** Adaptive block length via a trained acceptance-prediction head on draft-side features - the incumbent free-signal comparator class that K-3 arm 2 and OQ-15's C2 stand in for, and the feature class OQ-15 constraint (c) names as mandatory baseline (docs/PRIOR_ART.md, OPEN_QUESTIONS.md OQ-15).

**SPLIT.** The full-free label when the gate fires on exactly one of a source's two harvests (F-24's rule; the twin diagnostic's TWIN-SPLIT is the analogue). Landed once: S3 L3 at the lopsided group lens (F-25; primary / replication): D +0.0041 [+0.0026, +0.0055] / +0.0053 [+0.0019, +0.0091] (fired on the replication harvest only), Mt +0.0010 [-0.0012, +0.0030] / -0.0014 [-0.0041, +0.0016] and Mn_r -0.0031 [-0.0053, -0.0010] / -0.0067 [-0.0090, -0.0042] beside it. F-25's post-hoc reading (written after the labels were read; "NOT a registered readout"), quoting the registration's pinned words for a fire with Mn_r's upper below zero, reads the fire as "at equal dims (D), inflated by up to |Mn_r| by the twin's own cost", and the record's own gloss is that the SPLIT "is not read as half a survival". S3 L3 stays OPEN at the registered reader, and through the balanced lens the same cell reads ABSORBED (F-28). See ABSORBED, EQUAL-DIMS-ONLY, Mega-group lens.

**Stage A arms V / O / F / T (arms 1 / 8 / 9 / 10).** The STAGE-A FREEZE (docs/BLUEPRINT.md, 2026-09-05): V = arm 1 vanilla (no hooks); O = arm 8 oracle_h (the TRUE h_a injected, the D-2-named ceiling); F = arm 9 free_inject (h_hat from the frozen FREETOK ridge, R^2 +0.258); T = arm 10 tel_inject (h_hat from the frozen UNION ridge, R^2 +0.324). Injection = an SD^2-style delta added to the drafter's MLP up-projection output at every layer via forward hooks; adapter = LayerNorm(4096) -> U (4096 x 512) -> V_l (512 x 8192) per layer, all 16 layers, V zero-initialised; the drafter stays FROZEN (an owned deviation from SD^2). Every arm at seed 4 on data/prompts_oq16_verdict.jsonl (210 prompts, 3 families x 70 topics, mechanical paraphrase refusal against the four committed sets); seed 5 reserved. None has run. (F-23, 2026-09-05: arms 9 and 10 struck pre-GPU because their target is free information; arm 8 is the deployable free-actuator arm under any future registration; the A0/A1 ladder no longer exists as a telemetry test.)

**Stage I / Stage C (OQ-15).** Stage I = INFORMATION (CPU, on the arm-1 byproduct logs, 17,673 + 17,581 blocks x 4 offsets, 28,616 TEST positions in 42 clusters): does the TEL head beat its noise twin at predicting analytic acceptance? Stage C = CONVERSION (GPU, fresh committed populations, unchanged bars): does the head policy convert to tokens/call at matched budget? Terminal partition {WIN, information-ceiling null, conversion-mode null}. Outcomes: F-20 (Stage I PASS mechanically, ARTIFACT-DOMINANT) and F-21 (CONVERSION-MODE NULL).

**Stage R / Stage A (OQ-16).** Stage R = RECONSTRUCTION (CPU-only, on the four vanilla verdict byproduct runs, 70,529 blocks, 84 TEST clusters across two populations): a two-leg gate, TEL-vs-NOISE (with a GATING five-seed stale-target control: CI lower > 0 AND point > stale mean + 3 sd AND point > stale max) AND TEL-vs-FREE (CI lower > 0). Stage A = ACTUATOR (GPU): SD^2-style injection of the reconstructed vector. Partition: RECONSTRUCTION-CEILING NULL (leg 1 fails) / RECONSTRUCTION-DILUTION NULL (leg 1 holds, leg 2 fails) / STAGE-R PASS -> user-gated Stage A / ACTUATOR NULL or WIN; limbo dispositions: a Stage A never run leaves the lane OPEN, never a null; raws lost = VOID-BY-DATA-LOSS. F-22: STAGE-R PASS; Stage A frozen, unrun. (F-23, 2026-09-05: arms 9 and 10 struck pre-GPU because their target is free information; arm 8 is the deployable free-actuator arm under any future registration; the A0/A1 ladder no longer exists as a telemetry test.)

**Stale-target control (DI-1; five-seed).** Replace every (run, prompt)'s targets with a seeded permutation of its own block rows so NO block-aligned information exists for any arm, re-select lambda inside the control, and re-measure the TEL-vs-NOISE margin; if the live margin is within the spread of such zero-information draws, existence is unsupported. F-20 (non-criterion): five seeds spread -0.00071..+0.00064 around a live +0.00076 -> ARTIFACT-DOMINANT (live rank 1 of 6, one-sided p about 0.17). F-22 (gating, baked into leg 1): live +0.176469 vs stale points +0.000343 / +0.000849 / -0.000698 / -0.004252 / +0.000294, 3-sd bar +0.005508, cleared by about 32x. Lesson (F-20): a single stale draw misleads either way - use multi-seed.

**Staleness / persistence / run length / hold rule.** F-4 (synthetic): a block-held bucket prediction pays only when the expected concept run length comfortably exceeds gamma (rho=0.6, run length 2.5, was net-harmful at every offset even for a perfect decoder). Real persistence at k=512: p_same_bucket 0.02706469973283773, mean run length 1.0149421233206144, p90 = 1 (results/real/bucket_persistence_k512.json, F-12); 1.07-1.14 at coarse k (F-13) - the hold rule fails everywhere tested, whatever the predictor.

**Standardization pathology.** F-22's critic finding: Standardizer.from_moments (src/sideband/outcome_head.py) floors only exactly-zero sd, rare mass512 buckets carry TRAIN sd down to about 1e-7, and two out-of-support oq15 TEST prompts (orig 140, 37) produced standardized inputs of 26,662 and 14,082, making every trained arm 4-8x worse than the mean predictor on those clusters and inflating the registered deltas by about 25% (the unregistered drop-two diagnostic gives delta_noise +0.1327 vs the registered +0.176469). Stage I had been shielded by predict_clipped's [0, 1] clip; the unbounded h_a target removed the shield. Fixed for diagnostics by the DR-1 support clip. Dated note 2026-10-16: the live Stage-C heads (F-21) had no support clip either; the audit's replay puts the exposure at 41 / 41 changed decisions of 17,185 / 17,616 consulted, about 0.24% / 0.23%, no label moved (F-21's dated note).

**Standardized MSE / R^2 / centered cosine.** OQ-16 readouts on per-coordinate z-scored h_a (TRAIN moments): pooled TEST standardized MSE per arm; R^2 = 1 - MSE / MSE(trivial); the median centered cosine between reconstructed and true vectors in standardized space (raw-space injection differs by the 1/sd reweighting - a pinned distinction). Under DR-1's clip: TEL R^2 +0.253, cosine median 0.502; FREETOK +0.258; UNION +0.324, cosine median 0.579; trivial MSE 0.9901 (F-22; results/real/oq16_stage_r_dr3.json r2).

**State files (*.state.jsonl, *.meta.json, *.summary.json, *.stats.jsonl).** The evidence quartet. state.jsonl = per-cell checkpoints (per-prompt cluster counts that reproduce the bootstrap; a sha header binding to the harvest; resume refuses a mismatch) - committed evidence for registered runs, scratch for smokes (CLAUDE.md). meta.json = run provenance (args, git commit, shas, load regime). summary.json = pooled results per run or arm. stats.jsonl = per-prompt rows for verdict runs.

**Steer flags (hf_specdec).** The real adapter's arm descriptors (src/sideband/real/hf_specdec.py): --steer {none, bucket}; --bucket-source {free_lastp, free_lastp_sharp, oracle_nextp}; --steer-gate {disagree, always} (default disagree, F-3); --steer-mech {argmax, posterior} (default posterior, D-10); --beta (default 0.0).

**Straddle.** A CI95 that includes zero. Registered rule: straddles read as FAIL for gates (OQ-16 partition: "straddles read as FAIL"); F-14's registered verdict STRADDLE (+0.0014 [-0.0043, +0.0069]) means attribution between forecast quality and the actuator stays open.

**Support clip (DR-1).** Per feature, per arm, clip VAL/TEST raw values to the TRAIN [min, max] before standardization - an OUT-OF-SUPPORT guard, not an sd floor (only 425 of the 6,212 cells above 20 sd on the full TEL design lie outside TRAIN support; the clip changes 446 TEST cells). It removed the standardization pathology and is a mandatory Stage-A freeze element for every live feature (F-22).

**SURVIVES-STRONGER.** F-28's label for a stronger-reader gate cell at S3 whose triple rule fires on both harvests (the registration pinned the word before any cell trained; licence FULL only if Mt's and Mn_r's CI95 uppers are >= 0 on both harvests, else EQUAL-DIMS-ONLY with the reason). Two cells carry it, both at the lopsided L3 lens and both EQUAL-DIMS-ONLY (primary / replication): R-N (hz-rescaled), D +0.0080 [+0.0062, +0.0097] / +0.0130 [+0.0095, +0.0169], and R-L (longer budget), D +0.005107 [+0.0034, +0.0069] / +0.005410 [+0.0034, +0.0078]; the lopsided lens "never decides a reopen", so the K-2 word is K-2-ISOLATED, not a reopen. See EQUAL-DIMS-ONLY, K-2-ISOLATED.

### T

**tapcal / rotcheck (run-name suffixes).** Result-file naming in the K-3 lane; neither name is expanded in the findings. *_tapcal runs are read here as the live-tap calibration runs of E9 (F-20 lists "val/tapcal runs" as TRAIN-only rows for Stage I); *_rotcheck payloads are the DI-1 stale-target control runs of F-20 (results/real/oq15_stage1_rotcheck.json, _r, _s2.._s4). The rotcheck payloads print the gate schema's branch strings mechanically and carry no lane-state meaning (F-20 schema residue).

**TEL.** The OQ-15/OQ-16 feature arm: FREE (657) ++ slot multi-hot (2048) = 2705 dims via scheduler.probe_input (results/real/oq16_stage_r.json feature_dims). Under DR-1's clip its h_a reconstruction reaches R^2 +0.253 and tel_vs_trivial +0.250784 [+0.239316, +0.261616]; it sits CI-clear slightly below FREETOK (DR-2).

**Telemetry.** The sideband signal: what a memory or compute device could observe about the target model's forward without seeing values - expert ids, weight-slot addresses, page ids. Contrasted with FREE information (what the decoder has anyway) and with SD^2's hidden-state vector (what the observability constraint forbids).

**Telemetry sources S1 / S2 / S3.** S1 = the value-aware COMPUTE-TIER tap: shadow taps at Llama-3.1-8B layers {7, 15, 23, 31}, top-32-of-512 weight-slot occupancy per layer (hash-sketched addresses at the down_proj inputs), from the anchor forward (F-15, F-22). S2 = KV-page telemetry (top-k attended page ids; OQ-8; NEVER RUN). S3 = the pure ADDRESS STREAM: the OLMoE router's own top-8-of-64 expert ids at each of 16 MoE gates, no logits, no values (F-17). K-2's verdict is per source (D-1 scope note); every K-3 lane arc so far ran on S1.

**Terminal-outcome partition.** The exhaustive, pre-registered set of ways an arc can end, with statistical criteria per branch and a default branch for unclassifiable outcomes (information-ceiling null for OQ-15; reconstruction-ceiling null for OQ-16). Straddles read as FAIL. Required by the FOLD-BACK COUNT AMENDMENT's decidability pin so that no outcome is labeled after the fact.

**Three layers.** See The three layers box at the top.

**TARGET-FREE.** The mechanism name F-23 attaches to OQ-16's closure: the registered reconstruction target was itself free information under D-5, so "beyond p" is priced at that target (nothing is) and no further comparator (DR-5) is needed. The one reconstruction target at which telemetry could carry non-free information is the verifier's state at FUTURE anchors (OQ-16's anticipatory variant, never run, not authorized).

**TOK_A / TOK_B / FREETOK2.** DR-4 (F-22): TOK_A = FREETOK's hashed top-32 id multi-hot; TOK_B = a salted second hash of the same ids valued by top_p (value-paired, sparse with heavy-tailed values per the dated erratum); FREETOK2 = FREE ++ TOK_A ++ TOK_B at UNION's 4753 dims. Result COMPARATOR-TOOTHLESS: FREETOK2 is CI-clear worse than FREETOK (-0.003085 [-0.004984, -0.001280]), so "beyond p" stays unpriced; the readout is UNANCHORED (no destroyed-TOK_B twin, which would be the forbidden DR-5). union_vs_freetok2 +0.068265 [+0.065783, +0.070556] is REPORTED, not labelling.

**Tokens/call (t/c).** The E6 estimand: emitted tokens per VERIFY call = total emitted / n_blocks, pooled over a population, the per-prompt prefill excluded. The K-3 gate quantity. Vanilla gamma-4 about 3.11 on the Llama pair (docs/ECONOMICS.md; F-19 seed-1 vanilla 3.020427; F-21 seed-3 vanilla 3.00827523663776). Gameable by gamma inflation unless budget-matched; not a wall-clock measure.

**Top-1 accuracy margin / (c)-(a).** The K-2 unit: the difference in held-out top-1 label accuracy between the both-features probe and the free-only probe, per-prompt paired successes summed over train seeds, one prompt-cluster bootstrap over the 30 test prompts (F-15). Not an acceptance number.

**Train / val / test split (150/30/30; 126/42/42).** Prompt-level (cluster-level) splits so test prompts are unseen. Phase-3 probes: 150/30/30 of the 210 prompts, pinned (F-15). OQ-15/OQ-16 heads: 126/42/42 per population via default_rng(15) (F-20, F-22).

**Trellis.** The conventions this repo follows (findings and decisions logs, regime tags, a critic agent, a kill-criteria doc) so that it drops into that harness without changes; the lint tool is standalone on purpose (CLAUDE.md).

**Triple / cell.** A probe grid cell = (label space, offset, capacity). 156 registered cells per grid plus 6 R2 shuffle cells; the 12 offset>=2 triples are the K-2 decision set; capacities linear and mlp256; train seeds {0, 1, 2} (F-15, F-17).

**Trivial predictor / train-mean baseline / tel_vs_trivial.** Predict the TRAIN-mean target everywhere (the lambda-to-infinity ridge). tel_vs_trivial = MSE(trivial) - MSE(TEL) is the honest deployable margin: registered run +0.10701 [-0.06983, +0.22088] (not CI-clear, because of the pathology prompts); under DR-1's clip +0.250784 [+0.239316, +0.261616] with both populations agreeing (F-22).

**Truth-gate rate.** The gate-open rate when the prediction is the target's own fresh concept profile (the oracle): 15.9% at C=15 (F-14, n = 69,192) - the draft already agrees with the target about 84% of the time at coarse granularity, so little disagreement remains to steer.

**TWIN-ROBUST.** The reading of F-24's post-hoc twin-inertness diagnostic (registered before its cells ran; NON-CRITERION: "it cannot change a registered label — it pins which qualifier the consequence text carries"): TWIN-ROBUST iff D_r's CI95 upper is below +0.005 on both harvests ("the registered null does not depend on the shift twin"), where D_r = acc(fplus_b) - acc(fplus_r) and fplus_r is the corrected twin (the same-generation-index row of a different prompt, label-inert by construction); its siblings TWIN-MASKED (clean fires only) / TWIN-SPLIT / TWIN-DEPENDENT / TWIN-INCOMPLETE, plus a T reading, T = acc(fplus_n) - acc(fplus_r). Landed TWIN-ROBUST at both sources (primary / replication): D_r +0.0002 [-0.0009, +0.0014] / +0.0013 [-0.0002, +0.0028] at S1 and +0.0000 [-0.0014, +0.0014] / +0.0008 [-0.0014, +0.0029] at S3, with T about zero everywhere (TWIN-INFORMATION-NOT-SHOWN). The corrected twin itself gains CI-clear over the base on three of the four harvests (Mn_r +0.0032 [+0.0016, +0.0050] / +0.0020 [+0.0002, +0.0037] at S1, +0.0033 [+0.0015, +0.0050] / +0.0005 [-0.0012, +0.0022] at S3), so the label-consumption mechanism is WITHDRAWN at S1 on both harvests and at S3 on the primary, where "a same-marginal sparse block of these dims yields about Mt at this reader — the strongest form of the null", while on the S3 replication it is "neither withdrawn nor supported (Mn_r and T straddle zero)" (docs/WHY_THIS_DIES.md K-2 STATUS 2026-09-06). Its own pinned prediction (S1 TWIN-DEPENDENT) "FAILED in every part". See ABSORBED, Equal-dims noise anchor.

### U

**UNION.** DR-3's arm: TEL ++ TOK (4753 dims), telemetry plus p's hashed top-32 support. It beats FREETOK by +0.065180 [+0.062411, +0.067705] (both populations CI-clear: k3 +0.0639, oq15 +0.0665) and its anchor UNIONNOISE by +0.078089 [+0.075624, +0.080368]; R^2 +0.324 vs FREETOK's +0.258; the increment is 37.5% of the free margin, above the pinned "would surprise" line of a quarter (F-22; results/real/oq16_stage_r_dr3.json). Mirror: union_vs_tel +0.069971 [+0.067058, +0.072830] - p adds on top of telemetry about what telemetry adds on top of p. The Stage-A tel_inject arm (arm 10).

**UNIONNOISE.** NOISE ++ TOK: the equal-dims alignment-destroyed anchor for UNION (4753 dims; R^2 +0.245). MSE(UNIONNOISE) - MSE(FREETOK) = +0.013 is dilution net of the shifted block's prompt-level gain (F-22 DR-3).

### V

**Val population / val prompts.** Two senses. (i) Actuator tuning: 30 prompts on which thresholds are frozen (K-3: data/prompts.jsonl with idx % 7 == 5; OQ-15 Stage C: data/prompts_oq15_val.jsonl, 30 lines). (ii) Probe or head training: the val split of the prompt-level 150/30/30 or 126/42/42 partition, used only for lambda or epoch selection.

**Verdict population.** The fresh committed prompt set an actuator is judged on, authored and committed BEFORE any diagnostic output is read (docs/ECONOMICS.md section 5 amendment 2): data/prompts_k3_verdict.jsonl (K-3), data/prompts_oq15_verdict.jsonl (OQ-15 Stage C), data/prompts_oq16_verdict.jsonl (Stage A), 210 prompts each. Distinct from data/prompts.jsonl, which contains the 150 probe-training prompts. The Stage-A freeze notes the +0.062 bar is resolvable at 210 prompts (seed-vs-seed CI95 half-widths about 0.039) but not at 84.

**Verified archives (OQ-7).** A proposed track: store a spec-decode trace (accept bits plus corrections entropy-coded under the draft) so text decompresses with the draft alone, with the rejection rate as attestation of the decoder. Requires a deterministic decode runtime; constrained by F-9's break-even hint budget; prior-art pass not done. Dated note 2026-10-11: that runtime was never built (lockstep F-19); for amber's archives on one box an fp32 replay pin was enough (docs/DECODE_CONTRACTS.md); the byproduct economics were never measured (the only pack rate in lockstep's record, F-17, is a separately run draft pass). Dated note 2026-10-11 (second, attestation): 'the rejection rate as attestation of the decoder' was never built. amber's attestation design is L0, a header pin of the draft, plus L1, the target's recompute of the divergence set, and L1 is measured on the synthetic world only (amber F-2: an honest archive attests exactly, 2346 of 2346 recomputed divergences equal the recorded corrections, and a single forged token fails L1; L0 is blind to order-preserving drift of the draft); amber's errata row E12 (its F-14) records that no L1 path exists for its real archives, whose L0 header pin does exist. In those real archives a drifted decoder is detected, not located, by the content digest at the end of a draft-only decode (amber's src/amber/real/archive.py); the first-desync rates in docs/DECODE_CONTRACTS.md section 4 were measured in that instrument's experiment mode against the original tokens. 'Prior-art pass not done' above: see the OQ-7 cell's dated note of 2026-10-11 in docs/PRIOR_ART.md. Dated note 2026-10-15: status TRANSFERRED to amber/ (the operator's call PC-6 of 2026-10-14; the OQ-7 dated note of 2026-10-15 in OPEN_QUESTIONS.md); F-9's constraint stands as sideband's own, and no amber result is claimed here.

**Verify call / target call.** One forward of the target model over a block. tokens/call counts emitted tokens per verify call; the per-prompt PREFILL forward is excluded uniformly (E6).

**Void semantics / void-rerun.** What happens when the pairwise budget guard breaches at verdict: gate metrics are QUARANTINED unread (budget columns only consulted), ONE re-freeze retunes toward lower budget, the stage reruns at the reserved seed; a second breach FAILS that leg. Executed in F-19 (seed 0 voided -> seed 1, re-breach on the arm-2 leg as the honest prediction forecast) and F-21 (seed 2 voided -> seed 3, guard cleared every leg). A voided run's numbers are disclosed afterwards but never gate.

### W

**Win bar (+0.062 tokens/call).** The K-3 WIN point-estimate bar for scheduling and injection arms: +0.010 acceptance x the about-6.2 coupling on the 3.11 base, about +2.0% (docs/ECONOMICS.md sections 3 and 5). Requires, for EVERY comparator, CI95 lower > 0 AND point >= +0.062 AND the pairwise budget guard. Unchanged across K-3 Attempt #1 (F-19: +0.006860 measured), OQ-15 Stage C (F-21: +0.002664) and the Stage-A freeze.

**Would-surprise line / honest prediction.** The registration practice of pinning, before a run, what outcome the author expects and what magnitude would surprise, and recording the outcome FOR or AGAINST it. F-19's re-breach prediction was confirmed; F-21's guard-clears-and-null-strengthens prediction was confirmed; F-22's dilution-null expectation was REFUTED, DR-2 and DR-3 both landed on the surprising side, and DR-4's teeth prediction failed on sign.

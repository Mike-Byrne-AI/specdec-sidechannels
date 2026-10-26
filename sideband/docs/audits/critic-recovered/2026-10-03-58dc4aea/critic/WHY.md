# Why This Dies

The honest list. Each kill condition names the phase that tests it and what
we salvage if it fires. If none of these can kill the project, the project
isn't being tested.

## K-1 — Rejections aren't cross-bucket (Phase 0a)
If < ~25% of real rejections cross bucket boundaries at every sane k, concept
steering has no room regardless of decoder quality. Synthetic says 76–89%
(F-2) but that world was built to have topical structure.
Salvage: the audit tooling and the negative number itself.

OUTCOME (2026-08-29): did not fire. Mass CI lower bounds 0.769/0.804/0.856
at k=256/512/1024 — no CI near the threshold or the caution band; decision
insensitive to NF4-vs-bf16. Evidence and regime: F-10. The rule below is
retained verbatim as the record of what was pre-registered.

Decision rule (pre-registered 2026-08-29, before any real-model number
exists; the local card forces an NF4-quantized target, so the rule is fixed
now rather than after seeing how quantization moves the number):
- Estimand: cross-bucket RESIDUAL MASS (the F-8 default), with the sampled
  fraction reported alongside as the consistency check. The decision reads
  the prompt-cluster bootstrap 95% CI (sideband.stats), not the
  independence CI.
- Primary evidence regime: NF4 target (Llama-3.1-8B-Instruct, nf4 +
  double-quant, bf16 compute) + bf16 draft (Llama-3.2-1B-Instruct),
  gamma=4, temperature 1.0, >= 200 mixed prompts; k in {256, 512, 1024}.
  Amended 2026-08-29 (same day, still before any real number exists): chat
  template APPLIED with a pinned date_string (chat_template_used: true in
  run meta) — raw-completion decoding of an Instruct pair is a regime
  nobody deploys; prompt set = data/prompts.jsonl (committed, one unique
  topic per prompt so the bootstrap's prompt-clusters are independent;
  short prompts — the audit probes short-prefix behavior).
- KILL fires iff the cluster-bootstrap CI upper bound < 0.25 at EVERY k.
- Near-threshold band: if at any k the CI intersects [0.15, 0.35], no
  verdict (kill or survive) is issued from NF4 evidence alone — a
  bf16-target confirmation on a prompt subset (CPU offload; acceptance-only
  per D-9) is required first. The NF4-vs-bf16 paired delta on ~20 prompts
  is part of the sanity pass regardless (pairing is at PROMPT granularity
  via per-prompt RNG streams; within-prompt trajectories diverge at the
  first differing acceptance, which is expected and fine).
- Verification note (rider, 2026-08-29): CUDA/bnb kernels are not bitwise
  deterministic, so audit artifacts are verified by RE-RUN, never by
  byte-diff — unlike the synthetic results/, which regenerate bit-exact.
  Sharp criterion, fixed now: a verification re-run PASSES iff its point
  estimate falls inside the original run's cluster-bootstrap 95% CI (mere
  CI overlap is too lenient and is not the rule). Recorded in every run's
  .meta.json.
- KV-path rider (pre-registered 2026-08-29, before any cached audit number
  exists): the audit runs with per-prompt KV caches. Before its numbers are
  cited, re-run the identical invocation with --no-kv-cache on >= 20
  prompts at the same seed. PASSES iff each arm's mean-acceptance point
  estimate lies inside the other arm's prompt-cluster bootstrap 95% CI, and
  the same bidirectionally for cross-bucket residual mass. FAIL quarantines
  all cached results pending diagnosis. Compared arms of ANY later
  experiment must agree on the cache path (metas must match on
  no_kv_cache) — never confound path with policy.

## K-2 — Telemetry adds nothing beyond free information (Phase 3, OQ-1)
The load-bearing risk. If probes on (last-p + telemetry) never beat last-p
alone at offsets >= 2, the address stream is a lossy copy of information the
decoder already has, and the HARDWARE story is dead. F-6 proves the synthetic
world cannot rescue this — only real models can.
Salvage: fold to "free-information steering" (Phase 0b results), which is a
publishable systems trick with zero hardware premise; plus the negative
result on address-stream information content.
Scope note (2026-08-30, registered before Phase 3 exists; see D-1 scope
note): sources span pure ADDRESS streams (MoE routing) and value-aware
COMPUTE-TIER taps (shadow sketches). K-2's verdict is per source. If only
tap sources survive, the address-stream hardware story is dead as written
here, and what lives is the narrower compute-tier sideband story — a
re-scoping, not a rescue: the Phase-5 memo must then price the tap uplink
against SD^2's ship-a-vector alternative, with no address-observation
premise left to lean on. Also note F-12's outcome already removed the
free-information-steering salvage line above (the free baseline is null);
K-2's remaining salvage is the negative result alone.
STATUS (2026-08-31, F-15): S1 (compute-tier tap) SURVIVED K-2 — grid
verdict EXISTENCE, CONFIRMED by the registered seeds-8..11 replication
(pinned L1/off2/linear triple re-fired; all eight off2/off3 triples
re-fired; off4 not established — horizon is 2–3 tokens). Survived means
exactly what the scope note says and no more: the value-aware
compute-tier tap carries CI-positive future-concept information beyond
the strongest free baseline. The ADDRESS-STREAM story (S2 KV pages, S3
MoE routing) is still fully untested by this and remains where K-2 can
kill the hardware premise as originally written. The kill front now
moves to K-3: F-14 measured the existing actuator's oracle ceiling at
~zero at coarse k, so these probe margins currently have NO
demonstrated path to acceptance — existence without an actuator is a
sideband with nothing to steer.

STATUS (2026-09-05, appended; the 2026-08-31 block above is history):
S3 (pure MoE-router ADDRESS stream, OLMoE) also SURVIVED K-2 — F-17
(2026-09-01): CI-positive future-concept information beyond the
strongest free baseline at offset 2 in every label space (pinned cell
+0.0147 [+0.0113, +0.0182], replication +0.0173 [+0.0133, +0.0221]),
extending to offsets 3-4 under coarse-graining; F-18 showed it is not
prefix-topic state at the histogram level. So the "address-stream story
still fully untested" sentence above is superseded for S3; S2 (KV
pages) was never run and remains untested. K-2's verdict at the PROBE
level is therefore "survived at S1 and S3". At the RECONSTRUCTION level
(OQ-16, F-22) the picture is K-2's own sentence: the anchor state h_a
that the S1 stream reconstructs at R^2 ~0.25 is, by the dated OQ-16
erratum of 2026-09-05 (docs/BLUEPRINT.md), an exact linear function of
the verifier's full next-token distribution at the same position -
information D-5 already defines as free - so that reconstruction is "a
lossy copy of information the decoder already has". The existence
results (F-15/F-17) are about FUTURE-position concepts, which the
anchor's p does not determine, and are not touched at the linear level
(the erratum's OQ-6 h-probe re-reading: a linear probe on h_a is a
linear probe on the full logit vector and adds nothing over (a) at the
pinned cells); a nonlinear-in-p free baseline was never run.
Salvage line as it stands: the negative results and the method.

STATUS (2026-09-06, appended; F-24, OQ-17 FULL-FREE EXISTENCE RE-TEST):
S1: K-2 FIRED at the probe level AT THE REGISTERED READER at the pinned cells L1 offsets 2-3, in K-2's own sentence (the stream is a lossy copy of information the decoder already has), with two scopes — the registered reader (one to three AdamW passes at the registered budget) and the +0.005 materiality floor (no MATERIAL equal-dims margin: D +0.0002 [-0.0012, +0.0015] / +0.0012 [-0.0003, +0.0028], every D upper below +0.005; Mt +0.0034 [+0.0021, +0.0048] / +0.0033 [+0.0012, +0.0052] beside it). The stronger-reader residual is named exactly as it would have been under SURVIVES; one reader cannot establish K-2's universal "never beat". The registered twin was non-inert; the null reproduces at the corrected twin (TWIN-ROBUST: D_r +0.0002 [-0.0009, +0.0014] primary (seeds +0.0013 / -0.0016 / +0.0008), +0.0013 [-0.0002, +0.0028] replication (seeds +0.0029 / +0.0009 / -0.0001); Mn_r +0.0032 [+0.0016, +0.0050] / +0.0020 [+0.0002, +0.0037]; T +0.0000 [-0.0012, +0.0013] / +0.0000 [-0.0016, +0.0019] (TWIN-INFORMATION-NOT-SHOWN)). On the primary and replication the corrected twin itself gains CI-clear over the base while T's CI includes zero, so the label-consumption mechanism is WITHDRAWN for both harvests: the shift twin's gain is matched by a prompt-independent block, which under the pinned reading means a same-marginal sparse block of these dims yields about Mt at this reader — the strongest form of the null, under which Mt stops being evidence of telemetry information (the registered reading of one construction, not a measurement of every block); D_r remains the matched comparison.
S3: K-2 FIRED at the probe level AT THE REGISTERED READER at the pinned cells L1 offset 2, in K-2's own sentence (the stream is a lossy copy of information the decoder already has), with two scopes — the registered reader (one to three AdamW passes at the registered budget) and the +0.005 materiality floor (no MATERIAL equal-dims margin: D +0.0003 [-0.0013, +0.0020] / +0.0001 [-0.0019, +0.0021], every D upper below +0.005; Mt +0.0033 [+0.0013, +0.0054] / +0.0013 [-0.0008, +0.0035] beside it). The stronger-reader residual is named exactly as it would have been under SURVIVES; one reader cannot establish K-2's universal "never beat". The registered twin was non-inert; the null reproduces at the corrected twin (TWIN-ROBUST: D_r +0.0000 [-0.0014, +0.0014] primary (seeds +0.0010 / +0.0001 / -0.0009), +0.0008 [-0.0014, +0.0029] replication (seeds +0.0019 / +0.0009 / -0.0006); Mn_r +0.0033 [+0.0015, +0.0050] / +0.0005 [-0.0012, +0.0022]; T -0.0003 [-0.0021, +0.0015] / +0.0007 [-0.0005, +0.0018] (TWIN-INFORMATION-NOT-SHOWN)). On the primary the corrected twin itself gains CI-clear over the base while T's CI includes zero, so the label-consumption mechanism is WITHDRAWN for that harvest: the shift twin's gain is matched by a prompt-independent block, which under the pinned reading means a same-marginal sparse block of these dims yields about Mt at this reader — the strongest form of the null, under which Mt stops being evidence of telemetry information (the registered reading of one construction, not a measurement of every block); D_r remains the matched comparison. On the replication the mechanism is neither withdrawn nor supported (Mn_r and T straddle zero).
BOTH SOURCES: the existence layer is NOT SHOWN anywhere at the registered reader (ABSORBED at S1 and S3, twin-robust at both); the salvage line of 2026-09-05 — the negative results and the method — is all that stands. The stronger-reader residual remains the one named path to overturn.

STATUS (2026-09-14, appended; F-25, OQ-18 COARSE-LABEL FULL-FREE RE-TEST at L2 / L3):
[read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] S1 L2: K-2 FIRED at the probe level AT THE REGISTERED READER at the L2 cells (offsets 2-3), in K-2's own sentence (the stream is a lossy copy of information the decoder already has), with two scopes — the registered reader and the +0.005 materiality floor (no MATERIAL equal-dims margin: D +0.0011 [-0.0001, +0.0023] / +0.0006 [-0.0007, +0.0020], every D upper below +0.005; Mt +0.0015 [-0.0007, +0.0038] / +0.0022 [+0.0001, +0.0041] beside it). The L1 kill (F-24) extends to L2; the stronger-reader residual is named exactly as it would have been under SURVIVES.
[read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] S1 L3: OPEN at the full-free level at the registered reader — NOT-SHOWN (the gate fired on neither harvest and some D upper is at or above +0.005: D +0.0010 [-0.0006, +0.0026] / +0.0012 [-0.0015, +0.0040]; Mt +0.0013 [-0.0010, +0.0037] / +0.0028 [-0.0001, +0.0059]) at the L3 group lens (S1: one mega-group of 455/510 concepts including all 165 zero-degree concepts, the next group 10). Neither survived nor fired.
[read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] S3 L2: K-2 FIRED at the probe level AT THE REGISTERED READER at the L2 cells (offsets 2-3), in K-2's own sentence (the stream is a lossy copy of information the decoder already has), with two scopes — the registered reader and the +0.005 materiality floor (no MATERIAL equal-dims margin: D +0.0018 [+0.0008, +0.0030] / +0.0003 [-0.0009, +0.0013], every D upper below +0.005; Mt +0.0021 [+0.0007, +0.0034] / +0.0018 [-0.0000, +0.0036] beside it). The L1 kill (F-24) extends to L2; the stronger-reader residual is named exactly as it would have been under SURVIVES. acc(fplus, mlp256) - floor per seed +0.0329 / +0.0333 / +0.0340 (primary), +0.0265 / +0.0294 / +0.0305 (replication).
[read under the 2026-09-07 rider amendment after the registered rider fired at S1 L3 (raw leg 2 +0.0132 against the 0.01 band); diagnostic branch AMENDABLE, mechanism TWIN-MATCHED; a post-hoc reroute around a fired kill condition: the leg that fired was replaced after the fire by a twin-referenced dependence-excess leg whose S1 seed-0 values at both spaces were known from the diagnostic payload when the amendment was written; it is a fresh test only at the other three harvests; the E leg sees every non-causal block the raw leg sees (the twin lacks it) and is sharper under a drifted reader; what it drops (prediction-marginal drift and twin-shared position information) are non-leaks; S1 diagnostic X_raw at seed 0 +0.0006, the registered statistic, twin-referenced, would also have passed] S3 L3: OPEN at the full-free level — SPLIT (fired on the replication harvest only; D +0.0041 [+0.0026, +0.0055] / +0.0053 [+0.0019, +0.0091]; Mt +0.0010 [-0.0012, +0.0030] / -0.0014 [-0.0041, +0.0016]) at the L3 group lens (S3: two mega-groups of 268 and 193 = 461/510 including all 20 zero-degree concepts).
NOT all four pairs read ABSORBED; the per-(source, space) lines above carry the record; no all-space sentence issues.

## K-3 — Probe margins don't convert to acceptance (Phase 4)
Information that exists but arrives too noisy, too coarse, or too stale to
move 1 - TV(p, q'). F-4 is the mechanism: if real bucket persistence is short
relative to gamma, held predictions age out (rho=0.6 was net-harmful at every
offset even for a PERFECT decoder).
Salvage: per-offset gating rules and the staleness map.
(Dated note 2026-09-02: the fold-back sequence after an Attempt-#1 null is
the FOLD-BACK COUNT AMENDMENT in docs/BLUEPRINT.md — OQ-15 then OQ-16,
pinned order, cross-lane skip, hard stop, no third. The count's registration
homes are that block and docs/ECONOMICS.md §5; this section never carried a
count — noted to repair the "per K-3's kill text" citation chain.)

STATUS (2026-09-05, appended): K-3 FIRED at Attempt #1 - F-19
(2026-09-03): adaptive block scheduling on the frozen S1 probes posted
+0.006860 CI95 [-0.015024, +0.025572] tokens per verify call against
vanilla (bar: CI lower > 0 AND point >= +0.062), the pairwise budget
guard breached twice by mechanism. Fold-back #1 (OQ-15, outcome-
supervised telemetry head): CONVERSION-MODE NULL - F-21 (2026-09-04):
+0.002664 [-0.044719, +0.046727] vs vanilla and -0.081846 [-0.132484,
-0.035567] vs the free-features head at matched budget. Fold-back #2
(OQ-16, reconstruction -> SD^2-style injection): Stage R PASSED its
registered gate (F-22) and the actuator stage was frozen pre-GPU
(2026-09-05), but the dated OQ-16 erratum of the same day closes the
telemetry actuator test before any GPU spend: the reconstruction target
is free information under D-5 (see K-2 STATUS above), so the telemetry
injection arms are dominated by construction. What remains of Stage A
is the free-actuator question - whether an SD^2-style injection of the
verifier's own anchor state (computable from p) converts on this box -
which sits OUTSIDE this kill text (no sideband premise) and needs its
own registration. The hard stop after fold-back #2 holds: no third
mechanism. Salvage as written (per-offset gating rules, staleness map)
was exhausted by F-19's mechanism analysis.

## K-4 — The sideband is too narrow for the decoder it needs (Phase 5, F-5)
Ungated, a sub-80%-accuracy decoder is worse than nothing; gated, it's
harmless but also useless. If real telemetry needs thousands of distinguishable
slots or multi-layer taps to decode, the "cheap sideband" premise inverts.
Salvage: the width-vs-recovery curve as a hardware design constraint.

## K-5 — Wall-clock eats the win
Acceptance gains are real but the sidecar + gating latency inside the draft
loop, or the KV-crop engineering, costs more than the accepted tokens buy.
Note: NOTHING in v0.1.0 measures wall-clock (D-9 caveat; the HF adapter
recomputes prefixes). Do not let an acceptance win masquerade as a speedup.

## K-6 — The premise's economics don't exist
The device this helps (weight-serving memory with a sideband) only makes
sense in MoE/offload regimes (D-1 killed dense-resident). If those regimes
are better served by just shipping hidden states (SD^2 costs one vector per
verified position), the observability constraint is self-imposed, not
imposed. The Phase-5 memo must argue the constraint is real somewhere —
e.g. CXL-attached memory, multi-tenant isolation, or licensing boundaries —
or concede.

STATUS (2026-09-05, appended to K-4, K-5, K-6 together): UNTESTED. No
finding rules on any of the three. K-4: the S1/S3 widths (docs/
ECONOMICS.md section 3) were priced on paper only; no decoder-width
sweep ran on real telemetry. K-5: wall-clock is banned repo-wide until
the KV-crop fast path exists (D-9); sidecar latency was never timed;
no throughput sentence exists anywhere in this repo. K-6: the premise's
economics were never reached - both conversion attempts nulled below
the Lane-A bar, so the Lane-B boundary question was never posed with a
positive number in hand.

STATUS (2026-09-15, appended; F-26, OQ-9 STAGE 1): K-6 stays UNTESTED.
The first prefetch datum now exists - on the OLMoE S3 harvests a 16-of-64
resident set chosen by a linear reader from the routing history plus the
free bonus token covers 0.9143 / 0.9108 (primary / replication) of the
next forward's expert sets against 0.5197 / 0.5155 for a recency cache
and 0.8111 / 0.8036 for a one-token table alone (F-26) - but it is a
hit-rate COUNT on a harvest, not bytes, latency or a boundary argument;
the address stream's margin over that one-token free arm is +0.10 at
B = 16 and below the +0.05 floor at B = 32, part of it is plausibly free
token-history information (the free-bigram twin is unrun), and prior art
occupies the cells. No finding rules on K-6.

STATUS (2026-10-01, appended; the free-bigram twin of F-26): K-6 stays UNTESTED.
With the equally free previous token in the baseline at equal dims the
address block's margin reads +0.0609 / +0.0659 (SIGNAL /
SIGNAL) and the address stream over the free bigram +0.0661 /
+0.0705 (SIGNAL / SIGNAL) at B = 16 — label SURVIVES at THIS
ENCODING, below the floor at B = 32; the free previous token accounts for
0.4104 / 0.3858 of the +0.10 margin over the one-token table, and the
material part of what survives sits on positions whose token key the train
tables never saw (covered-position D_eq +0.0454 / +0.0472 on val in an
unregistered diagnostic, below the floor), so nothing here reads the address
stream as context or as support for the sideband premise. Still a hit-rate
COUNT on a harvest: no bytes, latency or boundary; prior art occupies the
cells. No finding rules on K-6.

STATUS (2026-10-02, appended; the stratified coverage read of the twin's
margin): K-6 stays UNTESTED. 2026-10-02, STRATIFIED COVERAGE READ of the
twin's margin, both runs from the clean freeze commit fea2431; label
FALLBACK-LOCATED / PT-SURVIVES on both harvests, REPRODUCE EXACT, both
gates straddling the floor: on the covered positions (0.9013 / 0.8582)
D_eq +0.0463 / +0.0481, CI-positive below the floor with the floor
inside the CI; on the unseen-key positions (0.0987 / 0.1418) +0.1940 /
+0.1741 (SIGNAL); with p_t's stored summaries in both arms D_eq^PT
+0.0532 / +0.0565 and D_add^PT +0.0583 / +0.0609 (SIGNAL, the equal-dims
CI containing the floor); the caveat is neither retired nor confirmed at
this power — its location is indicated, not settled; the sparse covered
keys (one to four train occurrences) read at or above the floor while
the well-covered keys do not; next rung R2, a free baseline whose
encoding handles unseen and sparse keys; see F-26's second dated status
line and the block's OUTCOME. Still a hit-rate COUNT on a harvest: no
bytes, latency or boundary; prior art occupies the cells. No finding
rules on K-6.

STATUS (2026-10-03, appended; the generalising free baseline, R2): K-6 stays
UNTESTED. 2026-10-03, GENERALISING FREE BASELINE (R2), both runs from the
clean freeze commit 2fe5926; label R2-FALLBACK-SURVIVES / H-ABSORBS on both
harvests, REPRODUCE EXACT, no straddle on the unseen-key gate or either Q2
reading, k = 128 interior: against replay-prior smoothed tables the address
block still adds +0.0732 [+0.0623, +0.0834] / +0.0662 [+0.0559, +0.0773] on
the unseen-key positions (SIGNAL) while the encoding recovers +0.1971
[+0.1697, +0.2266] / +0.1822 [+0.1557, +0.2167] of hit rate there — the
located margin is NOT shown to be table sparsity at this encoding; the
pooled Q1 reading +0.0493 [+0.0425, +0.0577] / +0.0506 [+0.0433, +0.0594]
reads NOT-SHOWN / SIGNAL by the rule with the CI95 straddling the floor on
both — the one label-bearing reading on which the harvests differ, said in
words; with the forward's stored final-norm state in the free arm the
address block adds +0.0111 [+0.0078, +0.0150] / +0.0106 [+0.0068, +0.0153]
and the address stream +0.0172 [+0.0139, +0.0210] / +0.0162 [+0.0126,
+0.0206], both NOT-SHOWN — no material margin (at or above +0.05) of the
address block over the equal-dims free block, nor of the address stream over
the free bigram plus the hidden block, is shown (both readings CI-positive
below the floor) at this reader, and STAGE 2's ADDRESS-BEYOND-FREE
MOTIVATION IS STRUCK by the pinned condition (beside the strike, as pinned:
D_add^H on the unseen-key positions +0.0399 [+0.0279, +0.0514] / +0.0286
[+0.0195, +0.0386] (NOT-SHOWN; the primary's CI95 containing the floor);
PREFETCH-HEADROOM stands; K-6 stays UNTESTED). The free-baseline ladder
under F-26 is closed as pre-committed; no further rung on this margin. See
F-26's third dated status line and the block's OUTCOME. Still a hit-rate
COUNT on a harvest: no bytes, latency or boundary; prior art occupies the
cells. No finding rules on K-6.

## K-7 — Glue-bucket tax can't be neutralized in real vocab space
D-7's exclusion worked because the synthetic function bucket is labeled. If
real k-means glue buckets can't be identified well enough (OQ-4), the gate
misfires and reinstates the self-cancellation of F-3.
Salvage: frequency-based exclusion heuristics and the audit-by-k tooling.

Glue rule + F-10 reopen trigger (pre-registered 2026-08-29, before any glue
set or concept-level number exists):
- Identification rule (sideband.glue.identify_glue_buckets): rank tokens by
  frequency in TARGET-ONLY sampled generations (real/harvest_freq.py: NF4
  target, data/prompts.jsonl, seed 0, temperature 1.0, max_new 256, chat
  template with the pinned date) — deliberately independent of the draft and
  of any steering outcome. Take the top 100 tokens; glue = the shortest
  prefix of buckets, ordered by their share of those tokens' frequency mass,
  reaching 80% cumulative cover. Ties break to lower ids (deterministic).
  Report alongside, never in place of: the 70%/90%-cover sets (sensitivity),
  the >= 5-of-top-100 count-rule set (OQ-4's original wording), and a
  concentration flag when glue exceeds k/8 buckets (frequency mass NOT being
  concentrated is itself the K-7 warning sign).
- Estimands after exclusion (tools/analyze_glue.py): (a) token-level
  concept_cross_fraction on the COMMITTED Phase 0a records at every k —
  fraction of rejections whose emitted token lies in a CONCEPT bucket
  different from the proposed token's bucket; (b) mass-level
  residual_mass_concept_other at k=512 from the Phase 0b vanilla re-run
  (whose records carry the residual_mass_glue decomposition). Both read
  prompt-cluster bootstrap CIs (seed 0), as K-1 did.
- REOPEN trigger: F-10's "K-1 does not fire" verdict is REOPENED iff the
  token-level CI upper bound < 0.25 at EVERY k, or the mass-level CI upper
  bound < 0.25 at k=512. Reopening mandates a full concept-level re-audit
  before any Phase >= 0b claim circulates. Any CI intersecting [0.15, 0.35]:
  flag and require the bf16 confirmation before a verdict, as in K-1.
- Gate-health diagnostic (Phase 0b, not a kill): report the disagreement
  gate's open rate per arm. A rate approaching always-on (>~0.8) with the
  80%-cover glue set says the exclusion is not doing its job — test the
  90%-cover set before concluding anything; persistent near-always-open
  gating plus no positive beta is the F-3 signature that makes K-7 live.

OUTCOME (2026-08-30): the REOPEN TRIGGER did not fire — concept-level share
0.565/0.610/0.674 by k token-level, 0.607 mass-level at k=512, every CI
lower bound >2x the bar (F-11). Glue identification itself works (2-4
concentrated function-token buckets). But the GATE-HEALTH DIAGNOSTIC FIRED:
gate open 93.6-94.0% in every gated Phase 0b arm, and the free baseline is
zero-to-negative with the F-3 ordering reproduced (always < gated <
vanilla; F-12). Diagnosis: not a glue-identification failure but a
GRANULARITY failure — argmax disagreement is uninformative over C=510
concept buckets (the synthetic gate had C=12). The pre-registered 90%-cover
re-test WAS RUN before concluding (phase0b_sharp_b3_cover90: tripling the
glue set, 2 -> 6 buckets / 80% -> 91% frequency-mass cover, moved the gate
open rate 0.9393 -> 0.9361 and left the delta <= 0: -0.0051 [-0.0108,
+0.0007], analytic -0.0078 [-0.0125, -0.0032]) — so the open rate is not
driven by under-excluded glue. Independent corroboration: consecutive
concept-bucket persistence at k=512 is 0.027, mean run length 1.015
(results/real/bucket_persistence_k512.json) — a block-held fine-bucket
prediction fails F-4's hold rule regardless of predictor. K-7 as written
(glue can't be identified) is answered NO; its underlying concern (the
gate misfires in real vocab space and reinstates the F-3 tax) is LIVE via
granularity, tracked as OQ-12 with a pre-registration-first test plan.
OQ-12 resolution (2026-08-30, F-13): the gate-misfire half is FIXABLE —
coarsening restores gate SELECTIVITY (open rate 0.55 at C=15) — but the
mechanism stays net-harmful at every tested granularity. Whether the
residual kill is forecast quality (K-2/K-3 territory — F-4 staleness is
K-3's named mechanism) or the actuator itself is overdetermined at coarse
k; the registered oracle-ceiling arm (BLUEPRINT Phase 0c attribution
rider) was the decider. It RAN (F-14) and returned the registered
STRADDLE — attribution stays open — while bounding the coarse-k oracle
ceiling at <= +0.0069 and measuring the truth-gate rate at 15.9% (little
concept disagreement left to steer at C=15). Either way it is not K-7's:
glue identification and the gate's selectivity are both demonstrated
fixable.

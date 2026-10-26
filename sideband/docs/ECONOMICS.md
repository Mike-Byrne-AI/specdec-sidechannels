# K-5/K-6 Economics Memo — the bar K-3 must clear

Status: REGISTERED SKELETON + PINNED BARS, written 2026-09-01, AFTER
F-18 landed and BEFORE any K-3 actuator experiment exists or runs.
This is NOT the Phase-5 exit artifact (that requires K-3's result to
fill the verdict skeleton at the bottom) and it makes NO wall-clock
claims (D-9/K-5: nothing in this repo measures wall-clock; the HF
adapter recomputes prefixes and is acceptance-valid only). Its job is
to pre-register what "K-3 succeeded" and "this matters" mean — in
numbers, from measured inputs, before any K-3 result can tempt us to
define success after the fact.
DATED ERRATUM 2026-10-16: "the HF adapter recomputes prefixes" above was
false when this header was written (2026-09-01): the adapter has cropped KV
caches by default since b1dae57 (2026-08-29). The no-claims sentence stands
on the absence of a benchmark harness (DECISIONS.md D-9, dated note 2026-10-16).

## 1. The claim chain, and where it stands

The project's main argument decomposes into three links. Only the
first is established.

1. EXISTENCE (K-2): telemetry carries future-concept information
   beyond the strongest free baseline. ANSWERED YES at two sources,
   replicated, and priced against the topic-state alternative:
   S1 compute-tier tap +0.008..+0.044 (F-15, F-16), S3 pure address
   stream +0.006..+0.073 (F-17, F-18; each range is the finding's
   own stated span). Probe top-1 accuracy margins; horizon 2-3
   tokens at S1, offset 2 everywhere plus 3-4 under coarse-graining
   at S3. S2 (KV pages) unrun.
2. CONVERSION (K-3): margins become acceptance. OPEN, with a
   graveyard: free-information bucket-bias steering is dead at every
   tested granularity (F-12, F-13), and that actuator's oracle
   ceiling at coarse k is measured at <= +0.0069 acceptance (F-14) —
   perfect forecasts had nowhere to act through it. Any K-3 attempt
   needs a DIFFERENT actuator (the registered OQ-14(ii)
   error-predictor / selective-prediction lane is the ranked
   candidate; SpecDec++ is the adaptive-gamma prior-art relative).
3. ECONOMICS (K-5/K-6): the win is worth its cost somewhere real.
   OPEN; this memo pins what "worth it" means, per deployment lane.

Direction vs magnitude, stated once for the whole memo: probe-margin
units (concept-bucket top-1 accuracy) and acceptance units are
DIFFERENT LAYERS. No number in link 1 converts to link 2 by any rule
we possess; that conversion is exactly what K-3 measures.

## 2. Measured inputs (each with its committed source)

| Quantity | Value | Source |
|---|---|---|
| Vanilla acceptance, Llama pair, gamma=4 | 0.763 | F-10 (audit_k512) |
| Tokens per target call (amortization budget) | 3.11 | BLUEPRINT origin frame (measured on the pair) |
| Concept-level steerable share of rejections | 0.56-0.67 by k | F-11 |
| Free-information steering delta (best arm) | +0.0025, CI through zero | F-12 (phase0b) |
| Free-information confirmatory arm | -0.0098 [-0.0155,-0.0039] | F-12 |
| Old-actuator oracle ceiling, coarse k | <= +0.0069 (point +0.0014) | F-14 (phase0c oracle) |
| Concept-bucket persistence (k=512) | 0.027, run length 1.015 | F-12 (bucket_persistence) |
| Probe margin, S1 (finding's stated range; gate cell +0.0141 repl.) | +0.008..+0.044 | F-15 |
| Probe margin, S3 (finding's stated range; gate cell +0.0147→+0.0173) | +0.006..+0.073 | F-17 |
| Topic-state share of the S3 L3 margin | ~1/10 at off2 (~1/5 like-for-like at off3) | F-18 (M3 vs M2) |
| Acceptance <-> tokens/call coupling | ~6.2 tokens/call per unit acceptance | F-12 dose arm (sharp beta4: -0.0237 acc, -0.146 tok/call) |
| SD^2 upper baseline (full hidden states, same pair) | +35% accepted tokens, +22% throughput | PRIOR_ART (arXiv 2511.09844) |
| Break-even hint budget (synthetic, shape only) | ~0.16 bits/token; dense hints lose 20:1 | F-9 |
| Narrow-sideband safety (synthetic, shape only) | gating makes weak decoders harmless | F-5 |

Coupling caveat: 6.2 is a linearization from ONE dose point on the
harm side of one arm; treating it as symmetric and linear is an
approximation, labeled as such wherever used below.

## 3. Derived quantities (arithmetic on the inputs above, computed 2026-09-01)

Sideband width, bits per token (id-list naive / set-coded):
- S3 (16 gates x top-8-of-64): 768 / 513
- S1 (4 layers x top-32-of-512): 1152 / 676
- SD^2 comparator (one 4096-dim bf16 hidden vector per verified
  position): 65,536 bits — the observability ratio is ~85-128x (S3)
  and ~57-97x (S1). The channel we steer from is two orders of
  magnitude narrower than the one SD^2 needs.

Acceptance deltas read through the measured coupling (~6.2), on the
3.11 tokens/call baseline:
- +0.010 acceptance ~ +0.062 tokens/call ~ +2.0%
- +0.044 acceptance ~ +0.27 tokens/call ~ +8.7% ~ "25% of SD^2's
  gain" (that label mixes bases — see the disclosure in section 5;
  like-for-like it is ~37%)

Flagged coincidence, so it cannot be quietly exploited later: 25% of
SD^2's accepted-token gain corresponds to ~+0.044 acceptance, which
is numerically the top of S1's PROBE-MARGIN range. The units differ
(section 1); nothing follows from the coincidence.

## 4. Two deployment lanes (K-6 answered per lane, not globally)

LANE A — software telemetry in MoE serving (no hardware premise).
At S3 the telemetry is the router's own top-k indices, which every
MoE serving stack computes anyway; reading them is a software hook,
not a device. K-6's DEVICE-economics question does not arise here —
there is no device to justify — but its deeper objection stands
in-lane and must be owned: in the same serving stack SD^2's
hidden-state vector is ALSO just software, so the observability
constraint is self-imposed in Lane A, and a stronger-signal
alternative exists in-lane. Lane A's honest value is therefore NOT a
deployment argument against SD^2; it is (a) a two-orders-of-
magnitude cheaper input (section 3) and (b) the research cell
PRIOR_ART records as unclaimed — steering from indices only, no
values, no logits — which stays unclaimed even in software. K-5
reduces to "does a linear-probe sidecar fit the draft loop"
(unmeasured; small by construction, but that is a hypothesis until
timed). The honest cost: this lane abandons the memory-device story;
it is the systems-trick salvage, upgraded from "free-information
steering" (which F-12 killed) to "index-stream steering" (which
F-17/F-18 says carries real, non-derivable signal).

LANE B — the hardware memory-side device (the original premise).
Lives only in fetch-on-demand regimes: MoE expert offload, KV-page
offload (S2's premise, already deployed in serving stacks), CXL/
disaggregated memory tiers (SpecPIM/HPIM show the substrate as a
compute story; the memory-side INFORMATION channel remains
unclaimed), multi-tenant or confidential serving where values may not
cross a boundary but addresses inevitably do (the side-channel
literature — access patterns leak token-level information — proves
that stream is readable AT the boundary; we are its cooperative
dual). SD^2's standing rebuttal: if you can touch the host and ship
one vector per verified position, do that instead. So Lane B's
premise is real ONLY where that vector cannot or may not cross:
K-6's yes/no is the question "does such a boundary exist in a
deployment anyone runs," and this memo does not answer it — it
records that Lane B additionally needs the answer to be yes, plus a
materially larger win than Lane A (a device must pay for itself).
Lane B covers BOTH device variants D-1 distinguishes: the passive
address-observed weight store (S3-flavored; the S3 width row prices
it) and the compute-tier tap whose uplink D-1's scope note obliges
this memo to price (S1-flavored; the S1 width row is that price).
Two registered items would improve Lane B's economics if they land:
OQ-9 (one sideband serving steer + prefetch amortizes the wire
twice) and OQ-14(i) (if the signal concentrates in few layers, the
sideband narrows further); OQ-13(i) feeds actuator granularity, a
K-3 input rather than a wire-count one.

## 5. THE PINNED BARS (the registration payload of this memo)

Registered 2026-09-01, before any K-3 actuator experiment exists.
These numbers are judgment calls anchored on measured quantities, not
derivations from a cost model — the pinning itself is the point (the
same honesty label as F-13's 0.5 gate bar). Amending them after any
K-3 result is read is prohibited; a dated pre-result amendment is
allowed as always.

K-3 KILL (unchanged, already registered in WHY_THIS_DIES/Phase 4):
delta over free_lastp indistinguishable from zero -> fold back once;
repeat -> stop.
(DATED CROSS-NOTE 2026-09-02: the fold-back COUNT in the sentence
above is widened to a structured two by the FOLD-BACK COUNT
AMENDMENT in docs/BLUEPRINT.md — pinned order OQ-15 then OQ-16,
cross-lane skip condition, hard stop, no third. Why this section's
lock does not bite: the lock protects the BARS the verdict is
measured against; the fold-back count is post-null SEQUENCING
touching no bar, guard, or epsilon — and the widening is pre-result
with respect to the gate the fold-back triggers on (the seed-1
verdict, unevaluated and unread at amendment time). The kill still
fires in its own words; only what follows a null is restructured.)

K-3 WIN, pinned now: paired acceptance deltas on the 210 committed
prompts at identical seeds (D-6), computed against ALL THREE
comparators — vanilla and both D-11 free arms (soft and sharpened).
The GATING delta is the MINIMUM of the three (the actuator must beat
the strongest comparator), and that minimum must satisfy (i) CI95
lower bound > 0, (ii) point >= +0.010 acceptance, (iii) the analytic
(D-9) estimand concordant in sign. Anchors for +0.010: it exceeds
the dead actuator's PERFECT-FORECAST ceiling at its tested cell
(F-14 CI-upper +0.0069 at coarse k; the fine-k oracle cell is the
registered open remainder) — a new actuator clearing it has done
something bucket-bias could not at any cell where bucket-bias was
measured, even with an oracle — and it is ~2x this harness's typical
CI half-width (~0.005-0.006 across F-12/F-13/F-14), so a WIN cannot
be a noise-edge artifact. These bars do NOT unblock Phase 4 by
themselves: the registered condition stands separately — Phase 4 is
attempted only with an actuator whose FREE-INFORMATION arm is
non-negative (F-12/F-13's condition, a precondition the
minimum-delta rule does not imply and does not replace).

ECONOMIC MATERIALITY, pinned readings of a WIN:
- Lane A (software): the WIN bar itself is the materiality bar.
  +0.010 acceptance ~ +2% tokens/call (measured coupling, section 3)
  — modest, but the input is free and the sidecar is a linear probe;
  the pinned verdict language at exactly the bar is "real, free,
  modest" — no stronger adjective. K-5 residual: the sidecar must be
  TIMED inside a draft loop before any deployment claim (not a
  wall-clock speedup claim; a latency measurement, allowed and
  required).
- Lane B (hardware): requires BOTH (a) a K-3 WIN reaching the
  OPERATIONAL BAR, which is authoritative: point acceptance delta
  >= +0.044 (~ +0.27 tokens/call via the ~6.2 coupling) — AND (b) a
  named, defended deployment where the hidden-state vector cannot
  cross (K-6's boundary argument, currently unanswered). BASE
  DISCLOSURE on the "25% of SD^2" label that motivated (a): +0.27
  tokens/call is 8.8% of the 3.11 tokens/call base (bonus token
  included), and 25% = 8.8/35 divides that by SD^2's accepted-tokens
  percentage, whose base (~2.11, bonus excluded) is smaller —
  like-for-like on the accepted-tokens base, +0.27 tokens/call is
  ~37% of SD^2's gain, so the pinned bar is HARDER than its "25%"
  label. The acceptance number +0.044 gates; the percentage is
  motivation only. Below (a), or absent (b), Lane B CONCEDES to SD^2
  per K-6's own text, and what survives is Lane A plus the negative
  result.

S2's role, settled by this memo: NOT on the K-3 critical path. S2 is
Lane-B breadth (the KV-offload boundary is the most commonly deployed
fetch-on-demand regime today); run it if and when Lane B's condition
(b) is being argued seriously, or as existence breadth on its own
merits. K-3 proceeds on S1/S3 evidence alone.

DATED PRE-RESULT AMENDMENTS (2026-09-01, made at K-3 Attempt #1
registration, BEFORE any diagnostic or run of that arc exists;
revised across the critic's registration-gate rounds, all
pre-result; full text in the BLUEPRINT Phase-4 arc registration):
(1) ESTIMAND AND GATE FRAME — for schedule-class actuators,
per-drafted-position acceptance is gameable by truncation AND raw
tokens/target-call is gameable by gamma inflation (emitted-per-call
= accepted + 1 always, monotone nondecreasing in gamma — an
information-free always-extend arm clears any raw tokens/call bar;
critic-verified against specdec.py). The gate is therefore TOKENS
PER TARGET CALL AT MATCHED DRAFTING BUDGET: each adaptive arm
tunes on val prompts by CONSTRAINED MAXIMIZATION (maximize val
tokens/call subject to val drafted-per-emitted <= the vanilla
gamma=4 reference budget EXACTLY — the design's one tolerance is
the verdict-time guard below; over a pinned quantile grid,
tie-break toward lower realized budget — never UNCONSTRAINED
tokens/call maximization), and the win requires, for EVERY
comparator, CI95 lower > 0 AND point >= +0.062 AND the PAIRWISE
budget guard: arm 4's verdict-population drafted-per-emitted <=
that comparator's + 0.01 (pinned; the information-free skew
residual is the MEASURED +0.0103 tokens/call, 17% of the bar;
drift-proof because both sides move with the verdict
population). Guard-breach void semantics (quarantine, one
re-freeze retuning toward lower budget, reserved-seed rerun) are
pinned in the BLUEPRINT block. Empirical basis from the committed
phase0b vanilla records: accepted-length distribution
P(k=0..4) = 0.2509/0.1751/0.1341/0.0953/0.3445 over 17,220
blocks, mean emitted/block 3.107 — the information-free extend
channel is real, so the guard is required. Minimum paired delta
CI95 lower > 0, point >= +0.062, unchanged in size. OWNED DEVIATION:
memo gate condition (iii) (analytic concordance) is demoted to
reported-not-gating for scheduling arms — the analytic estimand is
composition-confounded when arms draft different position mixes.
OWNED APPROXIMATION: the ~6.2 coupling was measured at fixed
gamma=4 on a q-modifying arm; its use here is out-of-regime, per
this memo's own labeling rule. (2) POPULATION — the verdict
population is a NEW committed prompt set, authored and committed
BEFORE any D2/D3 diagnostic output is read (the memo's 210 include
the 150 probe-training prompts, a leak for actuator evaluation);
probe-test prompts reported alongside, probe-train prompts
excluded from the gate; thresholds frozen on probe-val prompts
only. The +0.010-acceptance-equivalent bar size, the
minimum-of-comparators rule, and the Lane-B operational bar are
UNCHANGED.

## 6. Verdict skeleton (to be filled by K-3, not edited before it)

- K-3 result: ______ (delta, CI, arms, actuator; its own registration)
- Lane A verdict: WIN bar met? ______ -> "real, free, modest" or fold
- Lane B verdict: (a) point delta >= +0.044 acceptance (the pinned
  operational bar)? ______ (b) boundary defended? ______ -> premise
  lives / concedes
- K-5 residual at verdict time: sidecar latency measured? KV-crop
  fast path built? (both required before any wall-clock sentence)
  (dated note 2026-10-16: the KV-crop path exists since b1dae57, 2026-08-29;
  what wall-clock requires is a benchmark harness, never built; sidecar
  latency unmeasured)

## 6a. Verdict (filled 2026-09-05 by the skeleton's own rule - K-3 has
fired and both fold-backs have outcomes; the skeleton above is left as
registered)

- K-3 result: FIRED at Attempt #1 (F-19, 2026-09-03): telemetry arm 4
  vs vanilla +0.006860 CI95 [-0.015024, +0.025572] tokens per verify
  call (bar +0.062, CI lower > 0), pairwise budget guard breached
  twice by mechanism; actuator = adaptive block scheduling on frozen
  S1 probes; registration = the K-3 Attempt #1 arc block in
  docs/BLUEPRINT.md. Fold-back #1 (OQ-15, F-21): +0.002664
  [-0.044719, +0.046727] vs vanilla, -0.081846 [-0.132484, -0.035567]
  vs the free-features head. Fold-back #2 (OQ-16, F-22): Stage R
  PASS at the reconstruction level; the telemetry actuator stage
  closed pre-GPU by the dated erratum of 2026-09-05 (the target is
  free information under D-5).
- Lane A verdict: WIN bar NOT met by any telemetry arm at any
  attempt -> no "real, free, modest" sentence is licensed. The only
  CI-clear conversion leg in the registered record is the telemetry
  head LOSING to the free-features head (-0.081846 [-0.132484,
  -0.035567], F-21); head_free's own margin over vanilla is a
  descriptive tokens/call line in F-21 with no registered CI.
- Lane B verdict: (a) never reached - no telemetry arm cleared Lane A;
  (b) boundary defended? not posed. The premise concedes at Lane A.
- K-5 residual at verdict time: sidecar latency NOT measured; KV-crop
  fast path NOT built; no wall-clock sentence exists (D-9 holds).
  DATED ERRATUM 2026-10-16: "KV-crop fast path NOT built" was false when
  written (2026-09-05): the adapter's default path has cropped KV caches
  since b1dae57 (2026-08-29). What was never built is a benchmark harness;
  sidecar latency stays unmeasured, so K-5 stays UNTESTED (DECISIONS.md D-9, dated note 2026-10-16).
- Rounding note (release audit): section 2's "+0.27 tokens/call ~
  +8.7%" and section 4's "8.8%" are the same quantity at two roundings
  (0.27/3.11 = 8.68%; 0.044 x 6.2 / 3.11 = 8.77%); the base 3.11 is
  the data/prompts.jsonl population's vanilla, and each verdict
  population has its own (3.020 K-3, 3.008 OQ-15C).
- SD^2 baseline erratum pointer: the "+35% accepted tokens, +22%
  throughput, same pair" row in section 2 is corrected by docs/
  PRIOR_ART.md's dated correction (2026-09-04): those are cross-pair
  maxima; this pair's Table-1 block efficiency is 4.44 -> 4.79
  (sampling) at k = 8, unquantized, batch 12 - a cross-gamma prior,
  not a bar.

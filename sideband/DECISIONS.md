# Decisions

Standing decisions with their rationale. Reversing one requires a dated entry
explaining what changed. Findings referencing a decision cite it as D-N.

## D-1 — Telemetry must be input-dependent by architecture
- date: 2026-08-28, status: adopted
- A dense hashed matmul touches every slot every forward: its access set is
  input-INDEPENDENT and "top-N weighted" telemetry needs activation values a
  memory controller cannot see. The original Phase-1 plan (HashedNet injection
  into a dense MLP) is therefore dead as a telemetry source. Real telemetry
  v1 = MoE expert routing (input-dependent by architecture, zero simulation);
  dense stand-in = shadow sketches of would-be top-N column importances on an
  INTACT model (real/shadow_telemetry.py). Never corrupt the model to harvest
  telemetry (random-codebook injection destroys the labels too).
- Scope note (2026-08-30, after discussion of the origin architecture): this
  kill applies to a PASSIVE weight store observed through its ADDRESSES. It
  says nothing against a COMPUTE tier (the original "SRAM computes the
  hashed layers" architecture): a device that computes a layer possesses
  that layer's activations locally, and READ-ONLY taps on them — internal
  classifiers feeding a sidecar, with only a few bits crossing the uplink —
  are fully within the observability premise. shadow_telemetry is exactly
  that observer, simulated on an intact model; its priority rises under the
  compute-tier reading. The bright line stands: taps that read are allowed;
  gates that change what the OBSERVED/TARGET model computes are forbidden
  (the draft's q is exactly what steering modifies — that side is fair
  game; this is the decision's second lesson). We NOW READ the
  observability constraint as "almost nothing crosses the wire" rather
  than "addresses only" — a deliberate premise widening, dated here: the
  repo's original one-liner is address-stream-worded, and K-2's kill
  clause is too. Consequence, to settle in K-2's terms BEFORE Phase 3
  reads out: K-2 is evaluated per source, and a taps-only survival means
  the address-stream hardware story is dead while the compute-tier
  sideband story lives — the Phase-5 memo must then price the tap uplink,
  not the address observation (scope note added to K-2).

## D-2 — Causality discipline
- date: 2026-08-28, status: adopted, enforced by construction
- Steering information for a block may only come from positions <= the last
  verified position. Sidecar labels come from the target's OWN causal
  continuation, never teacher-forced corpus text. The pipeline passes causal
  state to policies by construction; leaky oracles are explicitly named as
  such (oracle_concept_now) and exist only as ceilings.

## D-3 — Single source of truth for verifier math
- date: 2026-08-28, status: adopted
- src/sideband/specdec.py is the only implementation of accept/reject/residual.
  The HF adapter converts torch logits to numpy and calls spec_step. Anyone
  re-implementing the verifier "for speed" must first make the numpy tests
  pass against their implementation.

## D-4 — Findings carry regime + evidence, lint-enforced
- date: 2026-08-28, status: adopted (ported from determinism-layer postmortem)
- Every FINDINGS entry must have `- regime:` and `- source:` lines with
  existing evidence paths. tools/lint_findings.py enforces it; CI runs it.
  A finding cited outside its regime is a bug, and the cheap fix is making it
  impossible for a finding to circulate without its regime stapled on.

## D-5 — The free-information baseline is mandatory
- date: 2026-08-28, status: adopted
- Any telemetry-steering claim must be compared against free_lastp: steering
  from the target's distribution at the last verified position, which every
  speculative decoder computes anyway. A telemetry result without this
  comparison is dominated-baseline theater. In the synthetic world the two are
  provably identical (F-6); on real models beating it is the existence
  question (OQ-1).

## D-6 — Paired comparisons; telemetry on an isolated RNG stream
- date: 2026-08-28, status: adopted
- Policies are compared at identical seeds so trajectories are paired.
  Telemetry draws from its own generator: a policy that READS telemetry must
  not perturb the shared draft/verify trajectory (this coupling silently
  equalized e05 v0 across all K).

## D-7 — Predictions and gate comparisons live in concept space
- date: 2026-08-28, status: adopted
- The glue/function bucket is excluded from BOTH sides of any bucket argmax
  used for prediction or disagreement gating. Rationale: at realistic
  function-word rates a flattened draft's raw bucket-mass argmax is the
  function bucket everywhere, which makes every position look like a
  disagreement and reinstates the tax (F-3 caveats). Real-vocab analog:
  identify and exclude high-frequency glue buckets (OQ-4).

## D-8 — Steering mechanism: soft bias + disagreement gate + confidence gate
- date: 2026-08-28, status: adopted
- Additive log-space bias only (hard masks are the beta->inf pathology,
  measured at -0.18 acceptance in F-3). Disagreement gating on by default
  (F-3). Confidence gating on by default (F-5: converts harmful low-quality
  decoders into harmless ones). Defaults: beta ~= 3 gated, tau ~= 0.5 scaled
  to decoder quality.

## D-9 — Analytic per-position acceptance is the headline metric
- date: 2026-08-28, status: adopted
- We record E[1 - TV(p, q_steered)] at every DRAFTED position (unconditional,
  variance-reduced, exogenous to accept/reject outcomes in this world).
  Empirical acceptance-by-offset conditions on SURVIVING to that offset and
  answers a different question. Report both; never conflate them. Wall-clock
  claims additionally require a cache-correct harness (the v1 HF adapter
  recomputes prefixes and is valid for acceptance only).
- Dated note 2026-10-16 (image audit 2026-10-15, section B item 1; the
  report is docs/audits/2026-10-15-image-audit/README.md): "the v1 HF
  adapter recomputes prefixes" was true in the initial commit 21b9010
  (2026-08-29, 00:29 UTC) and false from b1dae57 later that day (11:02
  UTC), which made per-prompt KV caches cropped to the verified prefix
  after every block the default path of src/sideband/real/hf_specdec.py
  (use_kv_cache=True; --no-kv-cache selects the exact-recompute reference
  that the K-1 rider A/B compares the cached path against). Every
  committed GPU result postdates that commit; 23 of the 26 committed run
  metas that record the flag read no_kv_cache false (107 metas are tracked;
  tools/run_k3_arms.py passes use_kv_cache=True without logging it). The wall-clock ban stands on its own
  ground, not on the recompute: nothing in this repository is a benchmark
  harness (one shared consumer GPU, the decode runs at batch 1, uncontrolled timings, bf16
  kernel tiling that makes trajectories diverge at the bit level, no
  batching or kernel control), so a cached run is expected to be faster
  (unmeasured) without any timing being a measurement of the system. The per-prompt and per-run
  seconds that the run metas and 59 stats.jsonl files log are instrument
  provenance, not wall-clock claims. Fifteen statements in twelve files
  repeated the stale mechanism (thirteen with docs/METHOD.md's quotation
  of the critic's rule); each carries a dated note or erratum of 2026-10-16
  pointing here, except the export front door, corrected in place.

## D-10 — Steering mechanism v2: centered posterior bias + disagreement gate
- date: 2026-08-28, status: adopted; supersedes D-8's argmax+tau DEFAULT (D-8's principles — soft bias, no hard masks, gates — stand)
- The default mechanism is steering.posterior_bias: boost each concept bucket
  by beta*(P(b)-1/C), glue tokens 0. Rationale (F-7): it dominates argmax+tau
  at every sideband width tested and at the oracle level, because the optimal
  bias is BIDIRECTIONAL — boost the predicted bucket AND demote the other
  topical buckets while sparing glue. Centering subsumes the confidence-tau
  gate (uniform posterior = exact no-op). The DISAGREEMENT gate remains
  mandatory: ungated, a confident posterior applies near-full-strength bias
  at already-right positions and reinstates the F-3 tax (reproduce with
  steer_gate="always"). hf_specdec defaults to --steer-mech posterior.
- Dated note 2026-10-16 (image audit 2026-10-15, section B item 5): "the
  default mechanism" is this decision's default, not the code's:
  sideband.pipeline.run_simulation keeps steer_mech="argmax" as its
  parameter default while the module docstring calls posterior the "v2
  default", and e03, e04 and e05 (F-3, F-4, F-5) pass no steer_mech, so
  they ran argmax; their regime lines carry a dated clause, as does F-6,
  which quotes e03's numbers. e06 passes both mechanisms explicitly, e07
  and the real adapter pass posterior. Numbers unaffected.

## D-11 — Ceilings and baselines must be mechanism-matched
- date: 2026-08-28, status: adopted
- Recovery denominators use the oracle running the SAME mechanism as the
  policy: the posterior sidecar exceeds 100% recovery against the argmax
  oracle (F-7), which is a statement about the old ceiling, not about magic.
  Corollary for D-5 free baselines under the posterior mechanism: run BOTH
  free variants — soft (bucket masses of p_last) and SHARPENED (one-hot at
  argmax p_last) — since posterior SHAPE now matters and the soft variant
  alone quietly lowers the bar. In the synthetic world the sharpened variant
  coincides with the stale oracle, so F-6 stands unchanged.

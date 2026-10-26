# The seed-to-seed noise floor of tokens per verify call (a methods note)

Written 2026-10-04 from the committed payloads results/real/noise_floor_k3.json and results/real/noise_floor_oq15.json
(F-27 in FINDINGS.md; registered in docs/BLUEPRINT.md as "SEED-NOISE FLOOR READOUTS REGISTRATION" before any readout
ran; both runs from the clean tree at 906edfd). Every measured number here is copied from those payloads; the entry wins on any
disagreement. Status words: this is a METHODS DATUM, NON-CRITERION for every finding and kill status in the record.

## The question

Every conversion verdict in this repository carries a confidence interval
across prompt clusters at ONE sampling seed, and the materiality bar (+0.062
tokens per verify call) with the F-19 WIN rule (CI95 lower above zero AND
point at or above the bar AND a pairwise drafting-budget guard, for every
comparator) was priced against those intervals. This note asks how much a
change of the sampling seed alone, under the SAME policy and on the SAME
prompts, moves the pooled tokens/call estimand as a function of the number
of prompts; how reliable one seed's per-prompt tokens/call is as a measure
of the prompt; and how often seed noise alone clears the bar and a single
comparator leg of the WIN rule at the sizes the record has used (30 val
prompts, 42 clusters, 84, 126, 210 verdict prompts).

## The data

Four committed vanilla (gamma 4, no stop / extend) runs of the
Llama-3.1-8B-Instruct NF4 target with the Llama-3.2-1B-Instruct bf16 draft
at temperature 1.0 and 256 new tokens, read from the per-prompt rows of
their summaries: population K3 (data/prompts_k3_verdict.jsonl, 210 prompts
in three templated families of 70) at seeds 0 and 1, and population OQ15
(data/prompts_oq15_verdict.jsonl, likewise) at seeds 2 and 3. K3 is the
label population (F-19's seed pair); OQ15 the replication on different
prompts and seeds. Two of the four runs belong to verdict sets that were
voided for their TEST arms' budget guards (K3 seed 0, OQ15 seed 2); the
vanilla measurements themselves were never voided. No model forward, no GPU,
no new seed: the whole readout is a CPU recompute on committed evidence.

## The estimand and the null

Tokens/call on a prompt set is the pooled ratio sum(emitted) / sum(verify
calls); the NULL DELTA is the lower seed's tokens/call minus the higher's on
the same prompts; its CI95 is the joint prompt-cluster bootstrap of
sideband.stats.paired_ratio_delta_ci (2,000 draws, seed 0), the recipe F-19
and F-21 used for their gate legs. Between fixed-gamma vanilla runs every
prompt drafts exactly 4 tokens per block, so the budget guard cannot bind
and the guarded rates equal the unguarded ones by algebra; the guard is
reported as an identity check. WHICH NULL THIS IS: a cross-seed,
same-policy, single-comparator null. The record's gate legs compare arms at
the same seed and require every comparator's leg to hold; a no-effect policy
at the same seed is bit-identical to its comparator until its first
divergent decision, so the same-seed null's noise lies between zero and the
cross-seed noise measured here for a policy whose per-prompt variance does
not exceed vanilla's. This note therefore prices what is plausibly an upper
bound on the noise the record's legs faced; the same-seed null itself is not
measured.

## Readouts (K3 / OQ15)

RELIABILITY. The Pearson correlation of per-prompt tokens/call across the
two seeds is 0.4232 [0.3073, 0.5193] / 0.4172 [0.2990, 0.5224]
(prompt-bootstrap CI95; half-widths 0.1060 / 0.1117). Within families it is
0.2944 / 0.3368 (instruct 0.3400 / 0.3579, story 0.1470 / 0.2213, summarize
0.3283 / 0.3817): a single seed's per-prompt tokens/call is a weak measure
of the prompt. The sd of the 420 prompt-run values is 0.2671 / 0.2824; the
mean absolute seed-to-seed difference per prompt is 0.2262 / 0.2381.

VARIANCE. Nested sums of squares over the 420 prompt-run values, reported
two ways. As SS shares (ML normalisation; with two seeds per prompt the seed
term carries HALF the seed variance, so it is a share, not a component):
seed-within-prompt 0.2894 / 0.2920, prompt-within-family 0.5169 / 0.5663,
family 0.1937 / 0.1417 (SS_total / 420 = 0.07133 / 0.07975). As balanced
method-of-moments components (df 210 / 207 / 2): seed 0.04128 / 0.04658,
prompt 0.01676 / 0.02253, family 0.02020 / 0.01630, all non-negative, shares
0.5276 / 0.5453 / 0.2142 / 0.2638 / 0.2581 / 0.1908: about half of a
prompt-run's variance is trajectory noise at a fixed prompt. The family term
has two degrees of freedom and is a fixed effect of three named families
(pooled means instruct 3.1472 / 3.1023, story 2.8818 / 2.8901, summarize
3.1112 / 3.1268).

HALF-WIDTH VS n. The median CI95 half-width of the null delta over 1,000
subsets of n prompts: n = 30 0.0982 / 0.1032, 42 0.0844 / 0.0887, 84 0.0603
/ 0.0632, 126 0.0493 / 0.0520, 210 0.0385 / 0.0398 (the full set, one draw;
delta +0.011597 [-0.027295, +0.049782] / +0.017473 [-0.024110, +0.055481]).
The +0.062 bar exceeds the median half-width at 210 prompts
(BAR-RESOLVED@210) and from n = 126 on both populations (0.0493 / 0.0520),
at n = 84 on K3 only (0.0603 / 0.0632), and sits inside it at 42 or fewer; a
half-width below the bar says where the bar is resolvable as one interval,
not what power a comparison has.

NULL EXCEEDANCE OF THE BAR. The one-sided rate f_one at which a +0.062 point
win appears by seed noise alone for a tested arm against a same-policy
comparator (half the two-sided rate; seed labels are exchangeable under the
null), with its Monte Carlo SE: n = 30 0.1060 / 0.1320 (0.0065 / 0.0070), 42
0.0605 / 0.0860 (0.0052 / 0.0060), 84 0.0090 / 0.0230 (0.0021 / 0.0033), 126
0.0005 / 0.0005 (0.0005 / 0.0005), 210 0.0000 / 0.0000 (one draw, below the
bar). At n = 30 the two orientations split 0.1510 / 0.2060 against 0.0610 /
0.0580. SINGLE-LEG FALSE POSITIVES of the F-19 rule (CI95 lower above zero
AND point at or above the bar), g_one: n = 30 0.0235 / 0.0375 (0.0033 /
0.0042), 42 0.0185 / 0.0250 (0.0030 / 0.0034), 84 0.0075 / 0.0190 (0.0019 /
0.0030), 126 0.0005 / 0.0005 (0.0005 / 0.0005), 210 0.0000 / 0.0000; the
guarded rate is the same number at every n (RULE-LEAKS@30: above the 1%
reporting threshold at n = 30). THE F-19 PERCENTILE: F-19's val-selected
advantage of +0.059725 on 30 val prompts sits at the 0.8840 / 0.8590
percentile of the pooled n = 30 null draws (0.1160 / 0.1410 at or above it)
— a description of a single cross-seed draw: that selection was a max over
32 search evals, same-seed, different-policy, on a different prompt set,
none of which is modeled.

THE SUBSAMPLING CAVEAT AND THE SWAP COMPANION. Every primary rate is the
SUBSAMPLING distribution of one realised seed pair (overlapping draws
without replacement from 210 prompts, centred on the realised full-set
delta, the variance of delta shrunk by 1 - n / 210 = 0.857 / 0.800 / 0.600 /
0.400 at n = 30 / 42 / 84 / 126), so the n = 84 and n = 126 rates are lower
bounds on an independent experiment's rate; the null is cross-seed,
same-policy and single-comparator, while the record's gate legs are
same-seed and all-comparator, and that same-seed null is not measured. The
swap companion (a random per-prompt exchange of the two seeds' rows, centred
at zero, every draw using the subset's full information) reads f_one^sw n =
30 0.1115 / 0.1285, 42 0.0790 / 0.0920, 84 0.0240 / 0.0275, 126 0.0055 /
0.0080, 210 0.0010 / 0.0005 (1,000 draws of the full set) with median
half-widths 0.0981 / 0.1032 / 0.0845 / 0.0882 / 0.0601 / 0.0632 / 0.0495 /
0.0518 / 0.0384 / 0.0401: it agrees with the primary at n = 30 and sits
above it at n = 84 and 126, as the shrinkage predicts. It bears on no label.

## Labels

FLOOR-MATERIAL on K3 (f_one at n = 30 0.1060 against the 2% threshold IDEAS [withheld: IDEAS not in this repository; see WITHHELD.md]
rank 1 pinned) and on OQ15 (0.1320); stage NOTE-STANDS; BAR-RESOLVED@210 and
RULE-LEAKS@30 on both; neither label within two SEs of its threshold. The
pinned sentence: "at this pair and regime a same-policy seed change moves
pooled tokens/call by a CI95 half-width of 0.0385 / 0.0398 at 210 prompts
and 0.0982 / 0.1032 at 30; one seed's per-prompt tokens/call correlates
0.4232 [0.3073, 0.5193] / 0.4172 [0.2990, 0.5224] with the other seed's
(0.2944 / 0.3368 within families); at n = 30 a +0.062 point win appears by
seed noise alone in 0.1060 / 0.1320 of subsets (SE 0.0065 / 0.0070) and a
single comparator leg of the F-19 WIN rule passes in 0.0235 / 0.0375 (SE
0.0033 / 0.0042; the guarded rate is the same number by algebra); the +0.062
bar is resolved at 210 prompts (BAR-RESOLVED@210 on both populations); a
cross-seed single-comparator null, plausibly an upper bound on the same-seed
noise the record's legs faced (argued from the shared prefix for a policy
whose per-prompt variance does not exceed vanilla's; not measured);
NON-CRITERION; no verdict moves".

## What this is, and is not

ACCEPTANCE-LEVEL: tokens per verify call under the HF adapter, which
recomputes prefixes and is acceptance-valid only. Published
speculative-decoding claims report wall-clock speedups, whose run-to-run
noise adds kernel, scheduling and batching variance on top of the trajectory
noise measured here; this floor is therefore a LOWER bound on the noise
those claims carry, and no wall-clock sentence follows from it (D-9). One
Llama-8B/1B NF4 pair, temperature 1.0, 256 tokens, templated prompt
families; two seeds per prompt is the floor for a reliability estimate. The
record's verdict arms' own cross-seed variance stays unmeasured (one
registered seed each), and the same-seed null the gate legs faced is not
measured.
Dated erratum 2026-10-16: "which recomputes prefixes" above was false when
written (2026-10-05); the adapter has cropped KV caches by default since
b1dae57 (2026-08-29). ACCEPTANCE-LEVEL and "no wall-clock sentence follows"
stand on the absence of a benchmark harness (DECISIONS.md D-9, dated note 2026-10-16).
Dated note 2026-10-16 (coverage): the percentile cluster bootstrap behind every
CI95 here (paired_ratio_delta_ci) shares its recipe with paired_cluster_delta_ci,
measured to under-cover at small cluster counts, 0.897 / 0.939 / 0.948 at 10 /
30 / 60 clusters for a nominal 0.95 on an F-24-shaped simulation (the ratio form
itself was not measured)
(docs/audits/2026-10-15-image-audit/coverage_out.json); the shortfall shrinks
with the cluster count and was not measured at 210.

Dated note 2026-10-10 (OQ-20, F-27's STAGE REPLAY line): one further seed
per vs-vanilla leg and per mechanism-matched free leg was run — each
verdict's two legs replayed at seed 6 under their frozen policies read
MUTUAL-COVERAGE / REPRODUCES on both populations (SPREAD-COVERED,
FREE-SPREAD-COVERED; K3 +0.010340 [-0.009288, +0.030521] vs vanilla and
+0.010109 [-0.009724, +0.030422] vs the free arm, OQ15 -0.018029 [-0.065168,
+0.028495] and -0.053623 [-0.107526, -0.002448], every guard held, no bar
cleared); on K3 the two stage words are not two confirmations (the free leg
is nearly the vs-vanilla leg, |R5 - R1| = 0.000231), and on OQ15 the
cross-seed differences' CI95 half-widths (0.0666 / 0.0707) exceed the +0.062
bar, so a bar-sized move is not resolved there; the cross-seed variance
stays unestimated; the draft_conf legs and the same-seed null stay
unmeasured.

## Using the paired-ratio package

src/sideband/stats.py holds the estimators, numpy only.
paired_ratio_delta_ci(num_a, den_a, num_b, den_b, n_boot, seed) returns
(delta, lo, hi) for sum(num_a)/sum(den_a) - sum(num_b)/sum(den_b) under a
JOINT prompt-cluster bootstrap: one index draw is applied to both arms'
per-prompt (numerator, denominator) pairs, so pairing at identical seeds is
preserved while each arm keeps its own denominators — for tokens/call, num =
emitted tokens and den = verify calls per prompt.
paired_cluster_delta_ci(successes_a, successes_b, trials, ...) is the same
recipe for two fractions on shared trials (the probe margins).
tools/e6_gate.py applies the first to the record's gate legs with the WIN
rule and the pairwise budget guard (the tested arm's drafted-per-emitted at
most the comparator's plus 0.01); tools/run_noise_floor.py applies it to the
seed pairs here. What this note's numbers say about sample size, for this
pair and regime: the +0.062 bar exceeds the median CI95 half-width of a
same-policy seed-pair delta from 126 prompts on both populations (0.0493 /
0.0520) and at 210 (0.0385 / 0.0398), at 84 on K3 only (0.0603 / 0.0632),
and sits inside it at 42 or fewer (0.0844 / 0.0887 at 42, 0.0982 / 0.1032 at
30); at 30 prompts a single cross-seed draw clears +0.062 in 0.1060 / 0.1320
of subsets (about one in 9 on K3 and one in 8 on OQ15; the scope above: the
subsampling of one realised pair, the same-seed null and a selection over
many evals not measured). A half-width below the bar is a resolution
statement, not a power statement.

## Prior art

Miller 2024's clustered / paired template for evaluation error bars is the
method's parent, applied here to a ratio estimand with per-arm denominators.
The pinned search before this note was written (three extended web searches;
the queries and results are recorded in the registration block's OUTCOME in
docs/BLUEPRINT.md) found no paper or benchmark reporting seed-to-seed or
run-to-run variance of tokens/call or accepted length for speculative
decoding with confidence intervals or sample-size guidance. The nearest
neighbours: MoE-Spec (arXiv 2602.16052) reports five-seed error bars on
quality metrics; the rigmark issue (github.com/alexellis/rigmark, issue 1)
reports run-to-run wall-clock tokens-per-second variance with a power
calculation for a benchmarking tool; SPEED-Bench
(huggingface.co/blog/nvidia/speed-bench, re-read at the source) names no
seeds, reports acceptance length and acceptance rate as point values, and
prints a standard deviation only on end-to-end request time, a wall-clock
quantity; Spec-Bench reports a mean of three.

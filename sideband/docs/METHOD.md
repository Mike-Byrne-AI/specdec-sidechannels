# Method: how research is run in this repo

For someone who wants to reuse how this repository does research, not its
results. Results live in FINDINGS.md; the plan of record is docs/BLUEPRINT.md;
decisions are DECISIONS.md; open questions (OQ-N) are OPEN_QUESTIONS.md; kill
criteria (K-N) are docs/WHY_THIS_DIES.md. House
terms are defined on first use and collected in docs/GLOSSARY.md. Line
numbers refer to docs/BLUEPRINT.md at HEAD 8542ef5 (2026-09-05; the file is
byte-unchanged since 2e44105) and will drift; block labels will not. Status
language is the repo's own: **shown** (a registered gate or finding says so,
with a CI clear of zero on the registered estimand), **not shown** (the
registered test ran and did not clear its bar, or the claim was never put to
a registered test), **unpriced** (named but not measured, or not separable
under the registered readout; no magnitude is licensed), **qualified** (shown
only in a narrower sense than the plain words suggest, the qualifier being
part of the claim) - the docs/GLOSSARY.md definitions. Three layers are never conflated:
**existence** (information beyond free signals; F-15, F-17), **conversion**
(more tokens per verify call at matched budget; two registered attempts,
F-19 and F-21, both nulls) and **reconstruction** (rebuilding the anchor
hidden state h_a, the last verified position's final-norm output; F-22,
"beyond p" unpriced after DR-4, then priced by identity in F-23: h_a is an
exact linear function of the anchor's full p, free under D-5, so the lane
closed before the frozen Stage A actuator test ran). The only throughput
currency is tokens per verify call; no wall-clock or speedup claim exists.

## 1. The loop

Every experiment runs the same five steps, and each step leaves a dated
block in docs/BLUEPRINT.md that is appended to, never rewritten.

| Step | Block type in docs/BLUEPRINT.md | What it pins | Examples at HEAD (line numbers re-measured 2026-10-16 after lane B's dated insertions; the block title is the stable pointer) |
|---|---|---|---|
| Register | `ARC REGISTRATION` (earlier phases: a `Phase N` protocol heading, "pre-registered <date>") | question, estimand, data by path and sha, gate statistic and CI recipe, controls, reserved seeds, an exhaustive TERMINAL-OUTCOME PARTITION, VOID SEMANTICS, a HONEST EXPECTATION, PRE-REGISTRATION DATA CONTACT | K-3 line 1279 (2026-09-01), OQ-15 line 2194 (2026-09-03), OQ-16 line 2872 (2026-09-04) |
| Freeze | `FREEZE` / dated `AMENDMENT` (the "deferred constants" pattern) | constants that cannot exist at registration (thresholds, tolerances, exported weights), landed by a dated amendment before the run they govern; amending a gating pin after a readout is prohibited | STAGE-C FREEZE line 2564 (2026-09-03), STAGE-A FREEZE line 3604 (2026-09-05), BUDGET-DILUTION AMENDMENT line 794 (2026-08-31), FOLD-BACK COUNT AMENDMENT line 1588 (2026-09-02) |
| Run and recompute | (no block; the run writes `<out>.meta.json` before starting, `<out>.state.jsonl` while running, `<out>` on completion) | the critic recomputes the decision from the state file with a fresh implementation before any finding text is written | see section 3 |
| Record | `OUTCOME` (plus `VOID EXECUTION` when a budget guard breached) | numbers by file path, the mechanical label, the critic round's result, the outcome recorded FOR or AGAINST the pinned expectation | STAGE-R OUTCOME line 3067, DR-4 OUTCOME line 3493; VOID EXECUTION line 2062 (2026-09-02), STAGE-C VOID EXECUTION line 2715 (2026-09-03) |
| Correct | `DATED ERRATUM` | the wrong sentence, the right value, the registered text left as written | DIMS ERRATUM line 842 (2026-08-31), lines 2004 (2026-09-02), 2109 (2026-09-03), 3355 (2026-09-04), 3558 (2026-09-05) |

The finding enters FINDINGS.md as one `## F-N` entry with mandatory
`- regime:` and `- source:` lines (D-4), enforced by tools/lint_findings.py
("OK (27 findings, all carry regime + tracked evidence)" on this tree, 2026-10-01). Kill criteria
K-1..K-7 carry decision rules written before the data; when one fires (K-3
at F-19) the fold-back count applies and a HARD STOP follows (line 1632).

## 2. The rules and the incidents that earned them

Sources: CLAUDE.md "Working practices" (committed f3d05d4, 2026-08-31) and
the dated blocks in docs/BLUEPRINT.md; each incident was checked there.

| Rule | Incident that earned it |
|---|---|
| Numbers in prose or commit messages come only from files read in that session | "six miscounts caught by the critic across one session" (CLAUDE.md, f3d05d4, 2026-08-31) |
| Pre-register post-hoc diagnostics too: pin cells, readouts and labels before running | the P1 prefix-topic control's equal-dims arm and DEFLATES gate were amended on critic review before any result was read (BUDGET-DILUTION AMENDMENT, 2026-08-31, line 794); reused for DI-1 and DR-1..DR-4 |
| Pin a replication's gating cell and its non-firing branches before it runs | S1 pinned L1/off2/linear after seeing which 10 triples fired (REPLICATION REGISTRATION, 2026-08-31, line 667); S3 pinned its replication "before the primary grid exists" (line 1035) |
| Registered `*.state.jsonl` files are committed evidence with a sha header; resume refuses a mismatch | a stale checkpoint "could otherwise silently masquerade as a fresh replication" (STATE-FILE INTEGRITY, critic round 2026-08-31, line 707; commit 86136c8: "state file is now committed evidence, not gitignored scratch") |
| The free baseline must be the strongest available, including token identity | the critic caught an 18-dim free baseline as handicapped and it became 657 dims (commit c344e15, 2026-08-30); DR-2: a hashed top-32 token-identity arm reconstructs h_a CI-clear better than telemetry, tel_vs_freetok -0.004792 [-0.007192, -0.002600] (F-22, 2026-09-04); F-23 (2026-09-05): for a RECONSTRUCTION target the strongest free baseline is D-5's full p itself, which determined OQ-16's target exactly - build the free arm from the definition, not from the summaries a pipeline already has |
| Run the equal-dims alignment-destroyed anchor beside any "adding block B helps" claim | measured dilution -0.0045..+3.3e-5 per +2048 dims was enough to fake a null on a dims-asymmetric readout (F-16, 2026-08-31) |
| Pair a small CI-positive margin with a multi-seed stale-target control, gating not advisory | F-20 (2026-09-03): one stale draw read as artifact, seed 3 alone would have read clean, five seeds spanned -0.000713..+0.000643 against a live +0.000763; OQ-16 baked five stale seeds into its gate |
| Registered text with an error gets a dated erratum, never a rewrite | DIMS ERRATUM: registered 3266/1218 dims, committed alphabets give 3265/1217 (line 842, 2026-08-31); five more errata through 2026-09-05 |
| Pin an honest prediction before every run | VOID EXECUTION 2026-09-02 pinned that the seed-1 "rerun likely breaches the arm-2 leg again" (line 2123; confirmed at seed 1, F-19); Stage R pinned a dilution null (refuted, F-22); DR-4 pinned teeth at +0.02..+0.05 and landed -0.003085 (DR-4 OUTCOME) |
| Void semantics pinned at registration: quarantine gate metrics unread, one re-freeze toward lower budget, rerun on the reserved seed, a second breach fails the leg | pinned because "a guard breach is otherwise a decision made with verdict numbers on screen" (K-3 registration, line 1392, 2026-09-01); executed at F-19 (seed 0 to 1) and F-21 (seed 2 to 3) |
| Quarantine beyond the letter and disclose every exposure | STAGE-C VOID EXECUTION (2026-09-03): comparator tokens/call held unread too; a 12-line stdout tail showing arm 6's summary was disclosed |
| Compare at matched drafting budget with a pairwise guard; raw tokens/call is gameable | critic rounds on the K-3 registration killed "raw tokens/call gameable by gamma inflation" (commit 1c14db4, 2026-09-01); the gamma-6 control measured it: 3.428206 vs vanilla 3.020427 tokens/call (F-19) |
| Check pairwise selected val budgets against epsilon at freeze time | F-21 (2026-09-04): a selection-time gap, val budgets 1.3119926682377585 vs 1.2858072916666667 (2.6x epsilon), was "knowable at freeze time from the committed selection budgets and not noticed"; now a Stage-A freeze duty |
| A `-dirty` meta must say what the dirt was, backed by a clean-worktree rerun where possible | F-10 (2026-08-29): audit metas `-dirty`, verified bit-exact against the clean-tree segment on 20 prompts; DR-4 (2026-09-05): clean-worktree rerun at c2181b1 byte-identical on the summary and all 3612 state rows |
| Verdict populations are fresh committed prompt sets, authored before any output that could select them, with a mechanical paraphrase refusal | Amendment #2: the memo's 210 prompts "include the 150 prompts whose generations trained the probes" (line 1412); Stage-A freeze: "83 of the first draft's topics were paraphrases" (commit 2e44105) |
| Every arc pins an exhaustive terminal-outcome partition; unclassifiable defaults to the conservative branch; a never-run stage is LIMBO, never a null | FOLD-BACK COUNT AMENDMENT decidability pin (2026-09-02); LIMBO DISPOSITIONS at lines 2275 and 2918 |
| Non-criterion diagnostics may price a label's meaning but never reclassify it | F-20: DI-1 returned ARTIFACT-DOMINANT and the mechanical PASS stood; F-22: DR-1..DR-4 could not touch STAGE-R PASS |
| Before registering a reconstruction or prediction target, ask whether the free information determines it in closed form; run an adversarial pass over the gathered data BEFORE a GPU stage, not after | F-23 (2026-09-05): h_a follows from the anchor's logits through the lm_head (full-logit inverse relative error 2.5e-8); found by a creative-lens contrarian pass after the actuator had been frozen and critic-gated twice |
| Grid-edge lambda selections are a disclosure duty; the lambda family must contain the trivial predictor; live features get a support clip | four consecutive grid-edge events (F-19, F-20, Stage-C freeze, Stage R); standardized inputs of 26,662 and 14,082 on two out-of-support prompts (F-22) |
| Verify load regimes by module inspection, not flags | the bitsandbytes skip-list spelling "mlp.gate" silently quantized the routers (commit 3eb5efd, 2026-08-31) |

## 3. The critic agent

The critic is the review agent in .claude/agents/sideband-critic.md, run
before any finding or experiment change is committed. Its checklist, quoted
by heading: 1 Leakage; 2 Dominated baseline ("A telemetry win without that
column is theater"); 3 Regime abuse; 4 Survivorship; 5 Gate hygiene; 6
Pairing; 7 Wall-clock honesty ("Reject any tokens/sec claim until the
KV-crop path exists", the rule's form before 2026-10-16: the path exists
since b1dae57 and the rule now rests on the absence of a benchmark harness,
DECISIONS.md D-9's dated note); 8 Function-word tax; 9 Kill-criteria dodging ("If a
kill condition fired and the plan reroutes around it, say so in exactly
those words"). Output: objections tagged BLOCKING or ADVISORY, then "What
would change my mind:" and the cheapest experiment that would.

Its highest-value mode is **recomputing the decision from the committed
state file with a fresh implementation**: rebuild the pooled statistic and
its cluster bootstrap from the checkpointed per-cluster rows and compare to
the committed summary bit-for-bit. Worked example, F-22 DR-3 (run here):

```python
# results/real/oq16_stage_r_dr3.json.state.jsonl; line 1 = header {"header": true, "tool": "train_recon",
#   "registration": "OQ-16 FOLD-BACK #2 (BLUEPRINT 2026-09-04)", "git_commit": "2ec789f-dirty", "runs": [...],
#   "summary_sha256": {run: sha}, "stale_seeds": [0,1,2,3,4], ...}; lines 2..3109 = 3108 rows, one per
#   (arm, variant, test cluster), count = rows x 4096 coordinates, e.g.
# {"arm": "free", "variant": "live", "pop": "k3", "orig_prompt_idx": 1, "sse": 533153.6650571913, "count": 720896.0}
import json, sys, numpy as np; sys.path.insert(0, "src")
from sideband.stats import paired_ratio_delta_ci
from sideband.recon import dr3_label
lines = [l for l in open("results/real/oq16_stage_r_dr3.json.state.jsonl") if l.strip()]
rows = [json.loads(l) for l in lines[1:]]
sse = {}
for r in rows:
    sse.setdefault((r["arm"], r["variant"]), []).append(r["sse"])
cnt = np.array([r["count"] for r in rows if (r["arm"], r["variant"]) == ("free", "live")])
d = lambda a, b: paired_ratio_delta_ci(np.array(sse[(a, "live")]), cnt,
                                       np.array(sse[(b, "live")]), cnt, n_boot=2000, seed=0)
uf, un = d("freetok", "union"), d("unionnoise", "union")
print(uf, un, dr3_label(uf, un))
```

Output: `(0.0651797160379991, 0.06241090578182812, 0.06770480986506906)`,
`(0.078089425878617, 0.07562422378541674, 0.08036844527770323)`,
`TELEMETRY-BEYOND-P`, identical to `reported_deltas.union_vs_freetok.pooled`
and `union_vs_unionnoise.pooled` in results/real/oq16_stage_r_dr3.json.
`paired_ratio_delta_ci(num_a, den_a, num_b, den_b, n_boot=2000, seed=0,
alpha=0.05)` (src/sideband/stats.py) returns `(delta, lo, hi)` for
`sum(num_a)/sum(den_a) - sum(num_b)/sum(den_b)` under a joint cluster
bootstrap: one index draw applied to both arms, so identical-seed pairing
(D-6) survives. Both cluster bootstraps are percentile intervals; the paired
one was measured to under-cover at the record's cluster counts, 0.897 /
0.939 / 0.948 at 10 / 30 / 60 clusters for a nominal 0.95 on an F-24-shaped
paired simulation (docs/audits/2026-10-15-image-audit/coverage_out.json, dated
2026-10-16; cluster_bootstrap_ci shares the recipe and was not measured). The
nearest label-deciding bound to the +0.005 floor is F-28's RN at L1
replication gate D upper +0.004951 (results/real/readers_s3_r.json), which a
t-for-z correction carries to +0.005026: under that correction the RN at L1 cell
would read NOT-SHOWN instead of ABSORBED (F-28's dated note of 2026-10-16);
the registered estimator is the percentile bootstrap, every label stands as
registered, and the final S3 word K-2-ISOLATED does not change. The snippet assumes every (arm, variant) writes clusters in
the same order; a stricter recompute keys on `(pop, orig_prompt_idx)`. The
same recipe recomputes F-19/F-21 from `per_prompt_stats` (`n_emitted`,
`n_blocks`) in the verdict summaries and F-15/F-17 from `_clusters` in the
probe state files via `paired_cluster_delta_ci`. Commit messages typically record two or more rounds (2e44105 "Two critic
rounds"; 44b08fa three: gate recompute, DI-1 recompute, fix verification;
1e12957 "Critic round 4"); a surprising result gets an
attack round (F-22's standardization pathology was found only there).

## 4. Evidence conventions

- `results/**` summaries are committed evidence (371 tracked files, `git
  ls-files results`), regenerated by tooling and never hand-edited.
- Every run writes `<out>.meta.json` **before** it starts ("meta BEFORE the
  run, state jsonl as the recompute surface, summary as completion marker",
  tools/train_recon.py). The meta records `git_commit` and the input shas its
  tool binds (`npz_sha256`, `prompts_sha256`, `thresholds_sha256`,
  `summary_sha256`); tools that dump `vars(args)` (tools/run_probes.py,
  tools/run_posthoc_topic.py, tools/k3_threshold_search.py,
  tools/run_error_predictor.py, tools/run_k3_arms.py and the GPU
  harvest/specdec modules) filter it through
  `sideband.provenance.redact_args`; tools/train_recon.py and
  tools/train_outcome_head.py record named fields and no args dict.
- `<out>.state.jsonl` line 1 binds the state to its inputs (`{"kind":
  "state_header", "harvest_npz_sha256": {...}}` for probe runs,
  tools/run_probes.py; `{"header": true, "summary_sha256": {...}}` for the
  CPU heads); for probe runs `parse_state` (tools/run_probes.py) refuses to
  resume on a mismatch. .gitignore
  ignores `results/real/*.state.jsonl` and negates the registered runs back
  in (27 `!` lines); smoke state files are scratch (`experiments/run_all.py
  --smoke` writes to the gitignored results/smoke/).
- Large raws are gitignored and bound by sha256 maps in committed files: the
  24 harvest npz shards through their shard metas' `npz_sha256`; the
  per-prompt byproduct directories through `summary.byproduct_sha256` (210
  entries in results/real/k3_verdict_s1_arm4.summary.json), refused on any
  mismatch by `sideband.outcome_head.verify_byproduct`. A stranger can check
  the shas are quoted consistently; only the box with the raws can check
  them against bytes. Registered output paths refuse override and sizing
  knobs (the "registered-outs guard" in tools/train_recon.py,
  tools/train_outcome_head.py, tools/run_probes.py).
- `git_commit` carries `-dirty` whenever `git status --porcelain` is non-empty
  at run time (hf_specdec.py and every tool). Untracked results accrue
  mid-chain, so most real-model metas are `-dirty` (k3_verdict_s1_arm4.meta.json
  binds `92fa9cb...-dirty`); the convention is attestation: say what the dirt
  was and, where possible, rerun clean (DR-4: byte-identical at c2181b1).

## 5. Controls the repo relies on

| Control | What it prices | Where it mattered |
|---|---|---|
| Free-information baseline (D-5): `free_lastp`, then the full 657-dim free summary `(a)`, then FREETOK (free ++ hashed top-32 token ids) | whether telemetry adds anything the decoder does not already have | F-12: no free steering arm beats vanilla acceptance 0.7628, best +0.0025 [-0.0028, +0.0079]; F-15: pinned telemetry-over-free margin +0.0141 [+0.0081, +0.0203]; F-22 DR-2: tel_vs_freetok -0.004792 [-0.007192, -0.002600] |
| Equal-dims alignment-destroyed anchor (`(atn)`, NOISE, UNIONNOISE) | dilution from adding dims | F-16: M2noise -0.0045..+3.3e-5 per +2048 dims; F-22 DR-3: gross dilution about 0.026 per +2048 dims (BLUEPRINT DR-3 OUTCOME) |
| Multi-seed stale-target control (targets permuted within prompt-run) | the zero-information draw spread of small margins | F-20: live +0.000763 [+0.000308, +0.001215] vs stale primary +0.000643 [-0.000076, +0.001357], label ARTIFACT-DOMINANT; F-22 gate: 3-sd bar +0.005508 vs live +0.176469 [+0.130414, +0.251518] |
| Matched drafting budget + pairwise budget guard (epsilon 0.01 on drafted-per-emitted, F-19) | tokens/call bought by drafting more | F-19: gamma-6 control 3.428206 vs vanilla 3.020427 tokens/call; guard breached twice (drafted-per-emitted, dpe, 1.317033 vs allowed 1.285681 at seed 1) |
| Void semantics | decisions made with verdict numbers on screen | F-19: seed 0 voided, seed 1 re-breached, leg failed; F-21: seed-2 breach 0.00544107351372447 (about 0.54x epsilon), seed 3 cleared every leg |
| Honest prediction pinned before the run | outcomes presented as surprising after the fact | F-19 "likely re-breach" confirmed; F-22 dilution null refuted; DR-4 failed on sign |
| Named oracle ceilings (D-2) | what a perfect signal converts through the mechanism | F-14: oracle_nextp at k=16 +0.0014 [-0.0043, +0.0069]; Stage A rung A0 (oracle_h vs vanilla) must clear before the telemetry rung runs |
| Offset-1 internal leak control | index-shift leaks a label shuffle cannot see | F-15: adding telemetry at free-saturated offset 1 hurts, (c)-(a) -0.0049..-0.0699 |
| Pinned-triple replication with owned multiplicity | winner's curse over 12 uncorrected triples (about 26% family-wise, F-15) | F-15 re-fired +0.0141 [+0.0081, +0.0203]; F-17 re-fired +0.0173 [+0.0133, +0.0221] |

## 6. What the method caught

Counts from `git log` (70 commits at HEAD 8542ef5, 69 at 2e44105, 2026-08-29
to 2026-09-05, one author; the 8542ef5 message contains none of the grep terms,
so every count below holds at both): 50 messages mention the critic (`git log -i --grep=critic`), 17 in
the subject; 33 record a BLOCKING objection or "blocker"; 30 mention a
recomputation, 28 say "bit-exact"; 6 mention an erratum. These count
mentions, not corrections (zero-blocker "critic-gated" registrations are
among the 50). Five corrections, quoted (em-dashes rendered as hyphens):

1. b1dae57 (2026-08-29): "2 BLOCKING, both fixed - (1) the original tests
   ran at acceptance 1.0 so every crop was a no-op and an off-by-one crop
   mutant survived; ... (2) the '~4-5x' prose was wrong as arithmetic and
   banned as wall-clock".
2. c344e15 (2026-08-30): "the critic caught the per-space 18-dim (a) as a
   handicapped free baseline, the exact hole Phase 2 closed at the logging
   level".
3. 3eb5efd (2026-08-31): "CRITIC BLOCKER 1: the bnb skip-list spelling
   "mlp.gate" silently quantized the routers (found on-box and by the critic
   independently; matching is leaf-name/dotted-prefix)".
4. 1e12957 (2026-08-31): "my "M2n larger everywhere" sub-claim REFUTED (3/12
   cells invert by <= 1e-4 where dilution ~ 0) and the finding wording
   carries the corrected form".
5. 2ec789f (2026-09-04): "a STANDARDIZATION PATHOLOGY (rare mass512 buckets
   with TRAIN sd ~1e-7; standardized inputs up to 26,662 on two out-of-support
   oq15 test prompts) inflates the registered deltas ~25% and leaves the
   honest TEL-vs-trivial margin CI-straddling (+0.107 [-0.070, +0.221])".

Two more: the arm-2 threshold-search erratum came from recomputing the
committed state file (a logged eval at val tokens/call 3.124012 beat the
selected 3.096891; line 2004), and F-20's DI-1 control was "critic-proposed"
(commit 44b08fa).

Dated addition 2026-10-11 (harvested from the parked sibling lockstep at
54d83f4b5e1e; not a sideband incident): a slip of the kind this repository's
rules target, from a repository that lacked them. lockstep F-14 (committed
2026-08-29) turned a measured draft-scoring rate of 9,233 positions/s into "~5
MB/s" of decoded text, then concluded that the archive economics were "no
longer two orders of magnitude off". At the 4.7277 bytes/token in its own
cited input the product is 43,651 B/s, or 0.0437 MB/s: 114.5x below the
printed figure and 460x short of lockstep's own 20.1 MB/s break-even (its
F-8). F-14's text shows no bytes-per-token figure, so how the 114.5x arose is
not recorded. It stood 41 days, until a cross-repository multi-agent review on
2026-10-09; lockstep F-17 is the append-only erratum, from amber's
pre-registered recompute (errata row E10). The rule in section 2's table,
numbers in prose only from files read in that session, is this repository's
guard against that kind of slip. The same log has the opposite case: lockstep
F-7 discarded two synthetic probes because their results agreed with no theory
(a jitter grid aligned with the logit grid; a trial loop that resampled
perturbation signs but not base logits).

## 7. Costs and limits of the method

- Time. Registrations run to hundreds of lines and are critic-gated before
  commit (docs/BLUEPRINT.md is 3870 lines; the K-3 registration took "three
  critic rounds, all pre-result", 1c14db4). Registered planning numbers: a
  threshold search "worst case <= 114 evals/arm, ~11.0 h" (36600cb); the
  forbidden DR-5 "~5 CPU-min on top of a 31-min run" (DR-4 OUTCOME). The suite
  (357 tests collected by `pytest --collect-only` on a clean checkout of
  8542ef5; 362 on the tree that adds tests/test_e6_gate.py and tests/test_ha_identity.py) was not re-timed.
- The `-dirty` stamps. Nearly every real-model meta is `-dirty` because the
  evidence chain dirties the tree. The flag is honest but weak: it rests on
  operator attestation except where a clean-worktree rerun exists (F-10,
  DR-4). In-session orderings (registration before run) are likewise
  attested, not provable from committed bytes; F-22's regime line says so.
- Session-local agents. The critic's reports are not committed; only their
  dispositions survive in commit messages and BLUEPRINT notes. A reader can
  reproduce the recomputations but not audit the rounds.
- Single operator, same model family. One git author; the critic is a
  subagent of the assistant that wrote the code. It found the cases above; the F-21
  selection-time gap passed the critic-gated Stage-C freeze (9e8fa4a)
  unremarked - "knowable at freeze time from the committed selection budgets
  and not noticed" (F-21).
- Power and scope. 210-prompt verdict populations with 42 or 84 test
  clusters; the +0.062 tokens/call bar (docs/ECONOMICS.md) is "resolvable at
  210 prompts, not at the 84 held-out TEST prompts" (STAGE-A FREEZE power
  note, CI95 half-widths about 0.039 at n=210). One model pair (Llama-3.1-8B-Instruct target,
  Llama-3.2-1B-Instruct draft) for every conversion and reconstruction result,
  plus allenai/OLMoE-1B-7B-0125-Instruct alone for the S3 existence probes
  (F-17, F-18); one GPU; NF4.

## 8. How to reuse it in another repo

The minimal kit is three files and one habit.

1. **FINDINGS lint.** Copy tools/lint_findings.py (stdlib only): it
   fails unless every `## F-*` entry has a `- regime:` line and a `- source:`
   line whose repo paths exist and are tracked by git. Wire it to `make lint` and CI.
2. **The critic prompt.** Copy .claude/agents/sideband-critic.md and rewrite
   the nine items for your domain, keeping the shape (named leak channels,
   the dominated baseline, regime abuse, survivorship, pairing, the banned
   claim class, kill-criteria dodging), the BLOCKING / ADVISORY tags and the
   closing "What would change my mind:". Ask it explicitly to recompute from
   state files, and make your tools write per-cluster state rows so it can.
3. **The registration block template** (the OQ-15 and OQ-16 blocks at lines
   2131 and 2809, reduced; the VOID SEMANTICS, DEFERRED CONSTANTS and
   PRE-REGISTRATION DATA CONTACT headings are OQ-15's at 2381, 2385 and 2139,
   which OQ-16 carries inside its STAGE A and DISCLOSURES bullets at
   2980-2994):

```text
<ARC> ARC REGISTRATION (dated YYYY-MM-DD, pinned BEFORE any computation runs)
AUTHORIZATION: the outcome or decision that authorizes this arc.
PRE-REGISTRATION DATA CONTACT: what was seen before writing this; why it cannot tune a pin.
QUESTION: one sentence naming the estimand.
DATA: committed inputs by path + sha; split rule; populations; RESERVED seeds.
GATE: statistic; CI recipe (n_boot, seed); materiality floor; controls (free baseline,
  equal-dims anchor, multi-seed stale-target); budget guard + epsilon.
TERMINAL-OUTCOME PARTITION (exhaustive): WIN / NULL-A / NULL-B; unclassifiable -> the
  conservative branch; LIMBO dispositions (never-run, data loss) may never become a null.
VOID SEMANTICS: quarantine gate metrics unread; one re-freeze toward lower budget; rerun on
  the reserved seed; a second breach fails the leg.
HONEST EXPECTATION: the expected branch and the magnitude that would surprise.
ARTIFACTS: exact command lines; meta / state / summary paths; registered-outs guard.
DEFERRED CONSTANTS: what lands by dated FREEZE amendment before the run.
--- appended later, never rewritten ---
OUTCOME (dated): numbers by path; critic result; recorded FOR/AGAINST the expectation.
DATED ERRATUM (dated): the wrong sentence, the right value; registered text left as written.
```

The habit is the loop in section 1: nothing is read before it is
registered, nothing is rewritten after it is read, and every decision is
recomputed from a file someone else can open.

License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).
Repository: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`, folder sideband/.

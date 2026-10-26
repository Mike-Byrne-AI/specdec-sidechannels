# Critic recompute report (ERRATA_PLAN step 4)

Verbatim return value of the critic agent (an independent general-purpose
agent on claude-opus, dispatched 2026-10-10 from the amber session with the
sideband-critic recompute checklist adapted to amber; scripts beside this
file). Payload reviewed: results/errata_recompute.json at 04cbfe9, written
at 20dd31d. Agent output is evidence of the review, not a finding.

---

**Errata recompute critic report (amber, payload 04cbfe9, written at 20dd31d)**

I recomputed every row with my own code, reading the shards, JSON, dumps and HTML directly. I used amber's loaders only to cross-check my raw reads, and wrote my own simulator for P2b. Every payload value reproduces exactly, so the maximum discrepancy is 0. Two problems are with the rules, not the numbers: the E9 rule checks F-10's figures at the wrong theta, and the E13 rule was changed after the pages had been read.

Provenance checks out. All 30 `provenance.inputs` blob ids equal git at 20dd31d, and all 27 protocol sources also equal 6672db4. `script_blob`, the tree, `script_sha256_lf` and `lib_sha256_lf` match. The payload has 0 CR bytes and is identical to the HEAD blob. Both `results/errata_web` sha256 values match, and a live re-fetch of both arXiv pages today is byte-identical. `clean_tracked_tree` is self-reported and can't be checked after the fact.

**1. Per-row table**

row | payload status | my status | max discrepancy | note
- E1 | CORRECTED | CORRECTED | 0 | `encode_meta.model.id` is Llama-3.2-1B, the P1 draft; `encode_stage` calls `load_model(a.draft)`.
- E2 | CORRECTED | CORRECTED | 0 | 186 rows hit the cap and 14 end at EOS 128001, with no overlap and no mid-sequence EOS. Min 21, 0 empty, 48,958 total. My raw shard read equals `load_generated`.
- E3 | CORRECTED | CORRECTED | 0 | 125/200 rows looped, 29,739 tokens (60.7%). My periodicity code agrees with `loop_fraction` on all 200 rows. All 39 grid points give at least 35 rows and 8,960 tokens, so the status holds across the grid. Repeat share is 34,648/48,358.
- E4 | CORRECTED | CORRECTED | 0 | The instrument check passes only with the float32 mean; a float64 mean misses by 1.24e-8. The looped/non-looped sign split holds at 39/39 grid points. The per-archive direction does not hold (objection 4).
- E5 | CORRECTED | CORRECTED | 0 | Weighted rate is 24.995. "32.8" is the unweighted mean of shard rates. The run is bimodal: shards 0-5 ran at about 11.5 tok/s, shards 7-24 at about 40.6 (median 40.57).
- E6 | CORRECTED | CORRECTED | 0 | Aggregate is 990.77, exactly the JSON value. The clean rate is 3,436 / 3,521 / 4,008 at f = 0.1 / 0.25 / 0.5, all at least 1.5 x aggregate (1,486).
- E7 | CONFIRMED | CONFIRMED | 0 | 7.280526, exactly `results/p4_real_archive.json`. Identical with cleanup on or off and with a raw `tokenizers` decode. Variant (b) is 6.745; the special-token literals total 3,610 B.
- E8a | CORRECTED | CORRECTED | 0 | At theta 0 there is 1 A-desync (gap 1.335e-5); at every theta >= 0.142 there are 0. I reproduced this JSON row from the pinned dumps with my own simulator.
- E8b | CONFIRMED | CONFIRMED | 0 | 224 rows, 0 failures, and `n_decoded` equals gen_len on every row. 48,958 + 5,852 = 54,810.
- E8c | CORRECTED | CORRECTED | 0 | Exactly one desync: sequence 57, offset 467, position 29,594. Encoder rank 4, decoder rank 5, encoder top-1/top-2 gap 0.37500763. Manifest 30/30 OK.
- E9 | CORRECTED | CORRECTED under the pinned rule; CONFIRMED in the claim's own regime | 0 (704 per-rank entries plus buckets) | All 11 printed figures match the theta=0.465/m=2 row exactly, and no other row. At theta 0, rank 2 is 6.00% (bf16) and 0.72% (fp16).
- E10 | CONFIRMED | CONFIRMED | 0 | Weighted rate 9,233.04. 4.72766 bytes/token, which I also reproduced by decoding the text myself.
- E11 | CORRECTED | CORRECTED | 0 | The hf JSON path accepts length 2^24 and refuses 2^24+1. v3 and v4 start work both with the sentinel and with the real `payload_to_symbols` plus a counting stepper. The L=3 control starts work on all three paths.
- E12 | CORRECTED | CORRECTED | 0 | (a) empty set, (b) 0, (c) 0. A wider grep finds no attestation path for real archives (objection 11).
- E13 | CORRECTED | UNRECOMPUTABLE under the pinned rule; CORRECTED under the amended rule | 0 | The 2601.10678 abstract introduces PMATIC (Adler, Tang). 2601.17684 (Hu, Tang) has no PMATIC anywhere on the page.
- E14 | CONFIRMED | CONFIRMED | 0 | No `results/p7`, no `results/p7_longhorizon.json`, 0 tracked files.

**2. Objections**

1. **BLOCKING (E9): the status comes from checking the claim at the wrong theta.** F-10 item (3) is the theta=0.465, m=2 table, both in `results/p2b.log` lines 3-4 and in the JSON.
   - These counts occur only in that row: fp16 C-desyncs 840 of 16,611 (5.1%), bf16 4,283 (25.8%), set-coded 1,548 (9.3%), and bf16_b1 to bf16_b8 3,819 (22.9%; ranks 2 and 3 at 2.06% and 7.53%).
   - At that row every pinned figure rounds correctly: bf16 2.70 / 9.34 / 15.34 / 25.61 / 59.8, fp16 0.37 / 1.54 / 3.66 / 14.4, and the headline's 3% and 9-26%.
   - F-10 item (4)'s 1/1070, 1/170, 1/212 and 1/60 also reproduce only from theta=0.465 rates.
   - The headline itself ("the escape ... is not enough") is about the escape-on setting.
   - The protocol's E9 rule ("the theta == 0.0 row") checks the claim at the wrong theta. The payload applied that rule correctly, but `rows.E9.note` is null even though the author saw the match (amendment "E9 (second dry run)").
   - Commit 04cbfe9 says the errata text is generated from the payload, so as it stands it would publish a false correction ("2.7% -> 6.0%").
   - Fix: keep the pinned status, record it as a protocol defect (as the repo did for F-8's band dead zone), and word the erratum as "θ=0.465/m=2 not stated; at the shipped θ=0 the figures are 6.0% and 0.7%".

2. **BLOCKING (E13 amendment): changed after the pages were read, and it flips the status.**
   - Under the pinned `citation_title` rule neither title contains PMATIC, so the row is UNRECOMPUTABLE; I reproduce that.
   - The rule was rewritten to `citation_abstract` after the pages had been read, which yields CORRECTED.
   - That breaks the protocol's own rule ("Amendments ... written before any result is read").
   - It also makes the log's opening claim false: "none of these change a decision that depends on a value".
   - The dry-run outputs weren't saved, so none of the log's value-independence claims can be audited.
   - The substance is verified: the 2601.10678 abstract matches PRIOR_ART.md:10's description almost word for word.
   - Fix: record UNRECOMPUTABLE under the pinned rule alongside a clearly labelled post-hoc CORRECTED, and correct the log sentence.

3. **ADVISORY (E4 and E7 amendments).**
   - The E4 amendment also flipped UNRECOMPUTABLE to CORRECTED after a value was seen (the 1.24e-8 float64 miss, which I reproduce). It is defensible: "-mean(log2q)" on the float32 array, read literally, is the float32 mean, which equals the JSON exactly. But the log should say it flipped the check, and a 1e-9 tolerance against a float32-rounded stored value was mis-specified.
   - The E7 amendment also flipped a status (UNRECOMPUTABLE to CONFIRMED), but it was triggered by the environment, and same-files is verified: `tokenizer.json` sha256 79e3e522..., and a raw `tokenizers` decode is byte-identical.

4. **ADVISORY (E4): the per-archive direction isn't robust.**
   - `strata.nonlooped.rel_perarchive` is +0.0717 at the pinned loop rule, but across the 39 grid points it ranges from -0.048 to +0.078, positive at 18/39.
   - The status survives because the sign split holds at 39/39, but no erratum should state a per-archive direction.
   - `prediction.rel_perarchive_nonlooped` = [-0.10, -0.07] uses the opposite sign to the defined quantity, so mechanical scoring would mark it a miss.

5. **ADVISORY (E8a): say "at θ=0".**
   - In the F-10 headline's own regime (theta >= 0.142), cuda_fp32_b1 has 0 desyncs.
   - The correction does bite for README.md:34 (the shipped θ=0 contract has 1 desync) and for OQ-2:14 ("order is exactly stable to rank 64"). OQ-2:14 is false at every theta: cpu_fp32 and cuda_fp32_b1 differ in top-64 order at 379/49,056 positions (411 for b8), all near-ties with gap <= 1.5e-4.
   - That also undercuts F-10's verdict ("exactly order-stable ... at every measured depth"), which is not a protocol row.

6. **ADVISORY (E8c): the gap label could mislead.**
   - `events[0].enc_gap` = 0.375 is the top-1/top-2 gap. The swapped pair (ranks 4 and 5) was separated by 2.96e-5, so reporting a "0.375 gap" would describe a wide-gap flip that never happened.
   - The escape doesn't cure this desync: it persists at theta 0.142 and 0.465 with m=2 (as C), and at 0.465 and 0.93 with m=4 (as T).

7. **ADVISORY (missing source): the protocol never lists `results/p4_real_archive.json`, F-11's cited source.**
   - Its values equal the recompute exactly: 7.280526165284529, 990.7656264617082, and 5,852 content tokens for cpu_fp32.
   - F-11:80's "24/24 (5,900 positions)" should read 5,852. The E8b prediction of 54,858 was built on the rounded figure.

8. **ADVISORY (E5, E6 wording).**
   - E5: neither 32.8 nor 25.0 is the steady rate; report the median 40.6 alongside.
   - E6: the f=0.25 rule also flags row 52 (21 tokens in 21.6 ms, which is fixed per-call overhead) and row 1 (0.37 s). f=0.1 isolates exactly the 15 periodic stalls of about 2.2-3.6 s, every 14-15 rows, inside the timed `score()` call. Calling them "not the instrument" is unverified without a rerun.

9. **ADVISORY (E7, D-6 fairness).** Every per-archive zstd baseline carries the 17-byte "<|begin_of_text|>" literal, and 14 also carry "<|end_of_text|>". Stripping them takes 7.28 to 6.75 (-7.3%); the erratum should state both.

10. **ADVISORY (E11 wording).** F-4 was accurate for the JSON format it described. The binary v3/v4 formats were added later with no ceiling at all, and their varint fields admit lengths up to 2^35-1 (the v3 parser accepted 2^34). The erratum should say "not carried to v3/v4", not "F-4 was false".

11. **ADVISORY (E12).** The grep in (b) covers only the listed files. A grep over all of `src/`, `experiments/`, `tools/` and `tests/` finds `attest_with_target` only in `codec.py`, `a02_attestation.py` (synthetic), `tests/test_amber.py` and the errata script. Record the wider grep in the payload.

12. **ADVISORY (E13 payload).** The stored abstract is cut at 400 characters, before the PMATIC mention, so the payload doesn't show its own evidence. 2601.17684 is relevant prior art in its own right, so the fix should re-ID the citation, not delete it.

13. **ADVISORY (proposal, probable; same defect outside the rows).**
    - F-10 item (4) and P4_PROTOCOL's predictions used theta=0.465 rates, but F-11 decoded at theta=0.
    - Theta=0 rates, including A-desyncs, predict 1/77 for bf16 and 1/502 for fp16; F-11 measured 1/65 and 1/670.
    - So F-11's caveat ("target-generated corrections are slightly MORE fragile") reverses for fp16 once the regimes match.
    - This is a candidate E15: about 20 lines of numpy over committed data.

14. **ADVISORY (E14).** The protocol's `ran` check doesn't look at `results/p7_longhorizon.json`, the script's second output. I checked: it is absent, so the status is unchanged.

**3.** What would change my mind: a row of `results/p2b_escape_robustness.json` other than theta=0.465/m=2 that reproduces F-10's 840/16,611 and 4,283 C counts would sink objection 1 (I checked all seven rows and none does), and a timestamped record showing the E13 abstract rule was written before the first dry run printed E13 would downgrade objection 2 to ADVISORY.

My scripts are in the session scratchpad `critic/` directory: `c_p1.py`, `c_e7.py`, `c_p2.py`, `c_misc.py`, `c_order.py`, `c_e4grid.py`, `c_f10p4.py` (copied beside this report).

RECOMPUTE DISCREPANCY: 0
BLOCKING: 2

---

## Second pass (after 12e4867 / 3e91148 / d0eae27), verbatim

The two original BLOCKING objections are fixed. The revision adds one new BLOCKING: the E8a text claims the resolved token is exactly stable across fp32 arms, and that sentence would land in README and OPEN_QUESTIONS. Every new payload field reproduces exactly, the old values are unchanged, all 16 statuses are unchanged, and provenance checks out at 12e4867.

1. **E9: OK.** `rows.E9.status_in_claim_regime` is CONFIRMED and `claim_regime_rows` is ['0.465/2']. My own `checks_by_theta_m` agrees on all 7 theta/m rows x 11 figures, and 8 of 11 match at theta 0. `tables_claim_regime` matches mine exactly. The bullet says the theta is unstated and that at the shipped theta 0 rank 2 is 6.0% (bf16) and 0.7% (fp16). It does not say "2.7% -> 6.0%". `rows.E9.note` and the new log entry record the pinned verdict as a protocol defect. ADVISORY: the F-14 title still counts E9 among "12 of 16 ... corrected". ADVISORY: "the other depths are unchanged" should read "the other printed depths"; top-1 is not unchanged (159 A-desyncs at theta 0, 0 at 0.465/2). ADVISORY: the fp32_b1 "top-1 0.00%" rounds away the 1/25,306 desync; print the count.
2. **E13: OK.** `status_under_pinned_rule` is UNRECOMPUTABLE and `amended_by` is set, both in the payload and in the F-14 bracket. The log's false sentence is corrected, and it says the change was motivated by the pages. The stored abstracts are now complete and equal the saved pages byte for byte. `results/errata_dryruns/dry1.json` makes the pre-amendment statuses auditable: written at 18:53:10 EDT on a clean tree at head 73575a8, six minutes after the pre-registration commit; it shows E4, E7 and E13 as UNRECOMPUTABLE with notes "instrument mismatch", "OfflineModeIsEnabled" and "neither title contains PMATIC". `dry2.json` (18:57:05, dirty tree, as expected) shows the amended statuses. ADVISORY: the bracket says "decided by the E13 amendment" but not that the amendment was written after reading the pages; only the log says so.
3. **Generated text: one BLOCKING objection.** BLOCKING (E8a bullet; inserted after README.md:47 and OPEN_QUESTIONS.md:14): the sentence "'exactly order-stable' holds for the resolved token, not for the order" is false and contradicts my recompute. At theta 0, cpu_fp32 -> cuda_fp32_b1 has 1 resolved-token desync. cuda_fp32_b8 has 1 under every theta/m. Same objection: `rows.E8a.status_in_claim_regime` is CONFIRMED, which holds only for the F-10 headline in the escape-on setting; it is wrong for README:34 (the shipped theta 0 contract) and for OQ-2:14, an order claim that is false at every theta (379 order differences). The same missing qualifier appears in E8c. Fix: give the field per claim site; qualify both sentences with "only at batch 1 with the escape on (theta >= 0.142)". Otherwise every numeral traces to the payload. The E4 bullet states no per-archive direction. The E8c bullet reports the pair gap. ADVISORY: "at most 2.2e-03" is literally false (2.24e-03) and does not show the near-ties; cite the encoder gap at the first differing slot instead: at most 1.48e-04 for b1 and 5.72e-05 for b8. ADVISORY: the DECISIONS.md insertion "after line 100" splits D-8's sentence; it should go after line 101. ADVISORY: the F-14 title "0 unrecomputable" should mention that three rows were decided only by amendments.
4. **New fields: OK, zero discrepancy.** E4 grid: all 39 settings exact; range -0.048420 to +0.078337, positive at 18, sign split holds at 39. E8c persistence: 1 desync at all 7 theta/m. E8a by theta/m: 1 at theta 0, then 0. Order differences: 379 for b1 and 411 for b8; the adjacent-gap statistic reproduces exactly. Of the 2,971 payload values present in both versions, only 5 changed, all intended. ADVISORY: the E8b CONFIRMED status now sits on a claim string that includes "(5,900 positions)", which the rule never scored.
5. **Appended log entry: one item still false**, the one in item 3: "E8a gets the same field: F-10's body states theta >= 0.142 for its zero" takes the regime from F-10's body, not from the claim sites. The rest is accurate.

Check scripts: `v2_check.py`, `v2_numerals.py` (scratchpad `critic/`).

RECOMPUTE DISCREPANCY: 0
BLOCKING: 1

---

## Third pass (after 070430b / 4492ec0 / 31ee98b), verbatim

The remaining BLOCKING objection is fixed, and I found no new ones. The 4492ec0 payload's provenance checks out at 070430b and all 16 statuses are unchanged. Since 3e91148, only the intended fields changed. The errata tests pass (14) and the tree stayed clean.

1. **Per-site statuses and the E8a/E8c sentences: OK.** `rows.E8a.status_by_claim_site` matches my recompute: F-10 headline CONFIRMED (escape on, cuda_fp32_b1 has 0 desyncs at all six theta > 0 rows); README.md:34 CORRECTED (1 A-desync at the shipped theta 0); OPEN_QUESTIONS.md:14 CORRECTED (the order differs at 379 positions whatever the theta). E8a's "stable is the resolved token, and only at batch 1 with the escape on" is true on this data. E8c's "only at batch 1 with the escape on ... and for batch 8 at no theta" is true: cuda_fp32_b8 has 1 desync in all 7 theta/m rows, which I verified. ADVISORY: `rows.E8a.note` still says "the headline, README and OQ-2 read as the shipped theta 0". That clause contradicts the headline's per-site CONFIRMED. It is not printed in the generated text.
2. **Near-tie measure: OK.** I computed it independently with your definition (the encoder gap between the encoder's token and the decoder's token at the first differing slot). b1: 1.478195e-04. b8: 5.722046e-05. Both are exact matches, and the competing token is never outside the encoder top-256. At every one of the 379 and 411 positions the competitor is the adjacent token, so these equal my first-slot gaps. ADVISORY: "near-tie" has no threshold. At 2 of the 379 b1 positions the gap exceeds 8.6e-05, the fp32 pair drift budget used by p2b's XB-3 check. So the top-1-calibrated fp32 tau understates drift deeper in the ranking. This is worth one clause; it doesn't make "near-tie" false at logit scale.
3. **Numerals: OK.** Every numeral traces to a payload value or a quoted claim string. My tracer flagged only "0.0422", which is -0.0422 with the sign stripped by the tracer, from `delta_concat_looped` (-0.04216). The E9 counts (159, 25 and 1 of 25,306) equal the p2b JSON. 1.48e-04 is the new field rounded. The DECISIONS.md note now goes after line 101, the end of the bullet. The F-14 title qualifier and the dates on the amendment labels are present.
4. **Third log entry: OK.** Nothing in it is false.

RECOMPUTE DISCREPANCY: 0
BLOCKING: 0

## Second batch (rows E15, E16): first pass (after 861c553; a new opus agent), verbatim

**Critic report, second batch (E15, E16). Payload: results/errata_recompute_2.json, HEAD blob 1551084f34ab1d8e28567e42df8ed350d472f364, written at b35e126, committed at 861c553. Reviewed while HEAD moved to a00c50c (the text-generator commit, out of scope); the payload blob is unchanged at a00c50c.**

I recomputed both rows with my own code, reading the raw npz shards, dumps and JSON directly. I used amber's `load_rank` only to cross-check my raw P1 read, and it agrees. Every payload value reproduces exactly: 399 leaves in E15 and 283 in E16, including the informational arms and the events lists, with a maximum discrepancy of 0. The statuses also follow from the pinned rules as written. The problems are with the rules, in the same way the first batch's E9 was wrong:
- E15's CORRECTED is decided by the A-desync term. The protocol moves that term across a change of draft model it never records, while the claim it corrects is about corrections, and corrections are more fragile than predicted on both arms.
- E16's CORRECTED is decided at slot 43, by one context counted twice. Its claim sites are all top-1 claims, and at slot 0 there is no exceedance on any arm.

Every number below was computed by my scripts unless marked (read).

**Provenance (task A): checks out.**
- All 38 `provenance.inputs` ids equal `git rev-parse b35e126:<path>`.
- All 20 rows of the protocol's second-batch source table equal git at 509ad90 (tree ee34f6f), and none of those sources moved between 509ad90 and b35e126.
- The payload has 0 CR bytes and is byte-identical to its HEAD blob 1551084f.
- `script_blob`, the tree, `script_sha256_lf` (81fbc002…) and `lib_sha256_lf` (bb2ad77d…) match the committed files.
- I checked all 86 manifest entries for the dumps E16 reads (corpus plus six arms, 14 files each) by sha256, not just three: all match, and every file read is listed.

**1. Per-row table**

row | payload status | my status | max discrepancy | note
---|---|---|---|---
E15 | CORRECTED; `status_in_claim_regime` CONFIRMED | CORRECTED under the pinned rule (reproduced). As a correction of the claim's own quantity it is not supported (objection 1). Claim regime: CONFIRMED. | 0 (399 leaves) | Regime check: A 45,611, C 3,339, T 0, X 8 = 48,958 = `content_tokens`. Instrument checks: N1 = 48,958; divergence identical; shard rates 168/10,937 and 57/38,219 equal the JSON exactly. All-class theta-0 prediction (h4): 1/76.61 (bf16), 1/501.0 (fp16), against measured 1/65.10 and 1/670.51. fail_exact is 91.86% and 37.23%, against 84% and 28.5%. In the claim regime (h1): 1/170.05 and 1/1070.23; set-coded 1/370.08 and 1/2916.06; Poisson fail 76.29% and 20.45%.
E16 | CORRECTED; `status_by_arm` b1 CORRECTED, b8 CONFIRMED | CORRECTED under the pinned depth rule (reproduced). At the claim sites' own scope it is CONFIRMED on every arm (objection 2). | 0 (283 leaves) | b1: 379 order differences, 2 above 8.6e-05, both g = 1.478195e-04 at slot 43; they are one context (objection 3). b8: 411 order differences, max g 5.722046e-05, 0 above 9.727e-05 and 0 above 8.6e-05, so the b8 budget choice does not matter. n_absent is 0 on every arm; n_nonadjacent is 0 on both fp32 arms.

**2. Rule checks (task C)**
- **E15.** `reversals` (bf16 fail rate; fp16 rate and fail rate) follows from the values, so CORRECTED follows. 170.05 rounds to 170 and 1070.23 to 1070, so `status_in_claim_regime` is CONFIRMED. The pinned weightings, classes, Lbar = 244.79 and fail_exact definitions are applied as written.
- **E16.** `count_above_budget` follows from the values: 2 for b1 gives CORRECTED, 0 for b8 gives CONFIRMED.
- **Predictions.** They match REPORT.md: first pass item 13 (1/77, 1/502; measured 1/65, 1/670), item 5 (379, 411), and third pass item 2 (1.478195e-04, 5.722046e-05, "2 of the 379").
- **Dry run.** All 714 leaves of dry_b2.json equal the final payload except the two `seconds` fields, and the statuses are identical. But see objection 8: dry_b2 is not the pre-amendment run.

**3. Objections**

1. **BLOCKING (E15): the pinned rule scores F-11:85's claim about *corrections* on an all-class quantity. The reversal comes from the A term, which is carried across a draft-model change the protocol does not record.**
   - **Regime.** P2b's rates come from Llama-3.2-1B-Instruct (snapshot 9213176726f5), on mix_docs50_wiki50 text, with decoders run as one full teacher-forced forward per 512-token window (read: p2b JSON `model`, dump meta.json). P4 is Llama-3.2-1B base (4e20de36) on target-generated text, with incremental-KV decoders (read: p4_real_archive.json). The protocol and the payload `note` record only the encoder device.
   - **Per class, observed vs expected.** I compared observed first desyncs with the expected count summed over the positions actually decoded (the compensator, which is unbiased under the hazard model whatever the competing risk does), using the theta-0 per-rank rates as pinned.
     - bf16: A 28 vs 63.8 (0.44x); C 140 vs 81.6 (1.72x).
     - fp16: A 9 vs 35.2 (0.26x); C 48 vs 38.6 (1.24x).
     - Approximate Poisson z: A −4.5 and −4.4; C +6.5 and +1.5.
   - **Why A is over-predicted: the gap distribution.**
     - At rank-1 positions, the share with top-1/top-2 gap below 0.4654 is 9.04% in the P2 dumps and 4.16% in the P4 archives. Below 0.0662 it is 1.36% vs 0.53%.
     - Post hoc (my choice, not pre-registered): I conditioned P2b's A rate on that gap, reproducing its 159/25,306 and 25/25,306 A desyncs exactly first. It then predicts 30.0–33.3 A first desyncs for bf16 (observed 28) and 11.2–15.0 for fp16 (observed 9). The spread covers five binnings.
     - With that A rate and everything else as pinned, the theta-0 prediction is 1/103–1/105 and 73.9–74.7% for bf16, and 1/682–1/725 and 25.9–27.4% for fp16.
     - The measured values exceed it on all four comparisons in all five binnings, so the pinned rule would return CONFIRMED. The fp16 margins are within one binomial sd (about 3.1 points).
   - **Consequence.** The predecessor's 1/77 and 1/502 reproduce, but its inference ("F-11's caveat reverses for fp16") does not survive splitting by class. F-11's direction holds for corrections in both arms. Its attribution to *target-generated* content is not identified, since model, content and kernel path all differ.
   - **Fix (E9 precedent).**
     - Keep the pinned verdict as the record of a protocol defect.
     - Add the per-class observed/expected values and the full regime line: model, snapshot, kernel path, corpus.
     - The erratum must not say the direction reverses. A suitable wording: "the 76%/20% omitted A desyncs at theta 0. P2b's rank-only A rate overshoots on these archives (91.9%/37.2%), because it over-predicts A desyncs 2.3x/3.9x on the base draft. The C excess persists (1.72x/1.24x)."

2. **BLOCKING (E16): the rule scores top-1 claim sites at depth.**
   - Each `where` site is a top-1 statement:
     - FINDINGS.md:76: "every A-desync at theta=0…".
     - FINDINGS.md:55: F-7's "every flip is a near-tie", which refers to its top-1 flip rates.
     - OPEN_QUESTIONS.md:16: "1-2% at bf16 with every flip a near-tie".
   - At slot 0, the count above budget is 0 on all five arms:
     - b1: 1 flip, g = 1.335e-05.
     - b8: no flips.
     - fp16: 208 flips, max g 0.0239 against 0.0662.
     - bf16_b1: 983 flips, max 0.2630 against 0.4654.
     - bf16_b8: 834 flips, max 0.2708 against 0.452.
   - The only sentence the depth result contradicts is the errata's own: OPEN_QUESTIONS.md:15, the E8a erratum ("every one a near-tie (… 1.48e-04)").
   - Fix: add a `status_at_claim_scope` field (CONFIRMED, with the slot-0 numbers per arm), and attach the CORRECTED only to F-14/E8a's depth sentence.

3. **ADVISORY (E16): the 2 b1 events are one context.** Positions 45480 and 47524 are sequences 89 and 93 at offset 1, and both sequences begin with tokens [128000, 520]: the same input on both arms. The 379 order differences contain 378 distinct contexts.
   - At that context: j = 43, k = 44; the encoder values are 10.472665 and 10.472517. The decoder raised token k by 4.17e-04 (about 10x tau) and lowered token j by 3.3e-05, a pair drift of 4.50e-04.
   - All 96 windows share the offset-0 context [BOS], and there are only 77 distinct two-token prefixes. So the 49,056 positions are not independent contexts in any P2/P2b count. The effect here is small.

4. **ADVISORY (E16): the budget is a quantile, not a bound, and tau is calibrated on the top 64, not on top-1.**
   - The census tau is the 0.999 quantile of aligned |Δ| over reference top-64 ∩ arm top-64 at all 49,152 positions (`p2_rank_census.py --topk 64`). I reproduce 4.291534e-05 (b1) and 4.863739e-05 (b8) exactly, and fp16/bf16 within 2e-8. Over the full 256 width it would be 3.81e-05 and 4.48e-05. The protocol's source line should state the top-64 truncation.
   - The predecessor's third-pass mechanism ("a top-1-calibrated tau understates drift deeper") is wrong. For b1 the per-slot q0.999 of |Δ| falls with depth: 5.9e-05 at slot 0, 4.8e-05 at slots 1–7, 4.4e-05 at 8–15, 4.0e-05 at 16–63, 3.6e-05 at 64–255.
   - Exceeding the budget is expected without any pipeline bug: 328 of 3,090,528 adjacent top-64 pairs drift by more than 8.6e-05 (b1); for b8, 254 exceed 9.73e-05.
   - g = 1.48e-04 is 1/83 of the encoder's 1st-percentile top-2 gap (0.01234, payload field, reproduced). The erratum should say "one context at 1.7x the fp32 pair budget, a tail drift". It should not say "wide-gap flip" or "not a near-tie".

5. **ADVISORY (E15): the rate comparison is not like-for-like.** `desyncs_per_token` is a first-desync hazard over the decoded prefixes, but it is compared with a whole-archive average.
   - The compensator gives all-class observed/expected of 1.16 (bf16: 168 vs 145.4) and 0.77 (fp16: 57 vs 73.9). These have the same directions as the payload's 1.18 and 0.75, so no status moves.
   - The ratio-of-expectations estimator gives bf16 0.01554 predicted vs 0.01536 measured, which flips the direction. So the amendment's "two metrics disagree for bf16" depends on the estimator and should cite the compensator.
   - `class_shares_theta0` compares shares of *all* desyncs (predicted) with shares of *first* desyncs (measured). The like-for-like predicted A shares are 43.9% and 47.7%, against measured 16.7% and 15.8%.

6. **ADVISORY (E15 rule design).**
   - The binary comparisons on 200 archives carry no noise allowance.
   - There is no `status_by_claim_site` field. The four `where` sites get different verdicts: F-10:72, F-10:76 and BLUEPRINT:57 reproduce in their own regime, while F-11:85 is what the primary rule scores. The first batch's E8a precedent applies.

7. **ADVISORY (predictions).**
   - E15's `prediction` mixes the critic's four values with the protocol's own four, with no labels.
   - The critic's 1/502 is the h1 value (502.34); the payload's headline field is h4 (501.0).
   - E16's "the competing token is always adjacent" has no prediction field. The value matches: n_nonadjacent is 0.

8. **ADVISORY (audit trail).**
   - dry_b2.json is not the dry run that preceded the amendment's informational field. It already carries `encoder_top2_gap_quantiles`, and its script and lib sha256_lf equal the final payload's.
   - It was written at 22:03:29 (written_unix 1791684209), 18 s before b35e126, the commit that contains the "after the dry run" entry. The run whose values were seen first is not preserved.
   - "Written before any code existed" is self-reported. Git shows only that the protocol commit (21:57:01) precedes the code commit by 6 min 46 s.

RECOMPUTE DISCREPANCY 0, BLOCKING 2

**What would change my mind**
- **Objection 1 drops to ADVISORY** on any of these:
  - the owner states that F-11:85 asserts all-class archive fragility, not corrections;
  - a base-model (Llama-3.2-1B, 4e20de36) A-desync measurement shows a rank-only A rate near 0.63% (bf16) and 0.099% (fp16) on P4-like text, contradicting the gap-conditioned estimate;
  - the C excess (140 vs 81.6; 48 vs 38.6) disappears under a C model that conditions on local rank spacing. I could not test this, because the P4 symbol files carry only the top-1/top-2 gap.
- **Objection 2 drops to ADVISORY** if the generated text attaches E16's CORRECTED only to F-14/E8a's depth sentence (OPEN_QUESTIONS.md:15) and states that the top-1 claims at FINDINGS.md:55, FINDINGS.md:76 and OPEN_QUESTIONS.md:16 stand.

Scripts (standalone, torch blocked, no imports from errata_lib or errata_recompute), all in results/errata_critic/:
- c2_prov.py: provenance checks.
- c2_e15.py: E15 recompute, compensator, matched predictions.
- c2_e16.py: E16 recompute, slot-0 scope, duplicate contexts, tau population, gap-conditioned A rate.
- c2_e15_gapsens.py: binning sensitivity.

Each script writes its output to a matching `.out.json` file, with LF line endings.

## Second batch: second pass (after 553ffb4), verbatim

**Critic report, second batch, second pass (E15, E16). Payload: results/errata_recompute_2.json, HEAD blob 0887fd91b920fea55a9c91ca934cf913f9ab87ac, written at 9c325c4, committed at 553ffb4 (HEAD at review). Text: `experiments/errata_text.py --payload results/errata_recompute_2.json --finding F-15 --dry-run`, run read-only at 553ffb4.**

I recomputed every value of the regenerated rows with new standalone scripts (`c2b_*`), including all the post-critic fields. Every value reproduces exactly: 450 value leaves in E15 and 376 in E16, plus 9 status leaves per row, with a maximum discrepancy of 0. Every status field follows from the values and from the 2026-10-11 UTC amendment as written. Both earlier BLOCKING objections are fixed in the payload and in the text.

One new BLOCKING objection is in the generated F-15 caveats line: it states that all of F-7's printed "2tau" thresholds are 4 tau, and one of them is not. The "finding:" line's sentence that my recompute "reproduced every value" is true after this pass.

Every number below was computed by my scripts unless marked (read).

**Provenance (task A): checks out.**
- All 38 `provenance.inputs` ids equal `git rev-parse 9c325c4:<path>`.
- The tree and `script_blob` (6c813e8) match. `script_sha256_lf` (d9b75f38…) and `lib_sha256_lf` (ec28d59b…) match the committed files at 9c325c4 and at HEAD.
- The payload has 0 CR bytes and equals its HEAD blob.
- All 20 rows of the second-batch source table still equal git at 509ad90. The only source that moved by 9c325c4 is results/errata_critic/REPORT.md, through append-only additions; the prediction text is unchanged.
- ERRATA_PROTOCOL.md is append-only across 509ad90, cfb9595, b35e126 and 9c325c4: each version is a byte prefix of the next.
- dry_b2_pre.json: head cfb9595, written 22:01:57 local, no `encoder_top2_gap_quantiles`, statuses CORRECTED/CORRECTED. Its 684 leaves shared with the new payload are equal apart from notes, claim text and `seconds`.
- Old payload (861c553) against new: 686 shared leaves, and only the notes, E16's claim string and `seconds` differ. 28 leaves were removed (`class_shares_theta0` and the two renamed prediction keys) and 189 added. No number changed.
- The errata tests pass (30). The tracked tree stayed clean apart from my new files.

**1. Per-row table**

row | payload status | my status | max discrepancy | note
---|---|---|---|---
E15 | CORRECTED; claim regime CONFIRMED; by class A CORRECTED, C CONFIRMED, all CORRECTED; all 4 claim sites CONFIRMED | identical on every field | 0 (450 value + 9 status leaves) | Compensator (theta-0 rates, h4, decoded positions):<br>• bf16: A 28 vs 63.82 (z −4.48); C 140 vs 81.56 (z +6.47); all 168 vs 145.38 (z +1.88).<br>• fp16: A 9 vs 35.25 (z −4.42); C 48 vs 38.63 (z +1.51); all 57 vs 73.88 (z −1.96).<br>Predicted first-desync A share: 43.9% and 47.7%.<br>`gap_shares` (rank-1 positions below the bf16 budget 0.4654): 9.04% of 25,306 (P2) vs 4.16% of 45,611 (P4). Below the fp16 budget 0.0662: 1.36% vs 0.53%. I verified 16 dump files.<br>h1 flat fields: 76.72 and 502.34.<br>`sides`: the P2b snapshot equals the cpu_fp32 dump meta.json.<br>`prediction_sources` agrees with REPORT.md item 13 and the protocol (checked by hand). |
E16 | CORRECTED; by arm b1 CORRECTED, b8 CONFIRMED; at claim scope both CONFIRMED; F-14 sentence sites CORRECTED, 3 top-1 sites CONFIRMED | identical on every field. The top-1 sites are also CONFIRMED from all five arms' slot-0 counts (see objection 5). | 0 (376 value + 9 status leaves) | Distinct contexts (above budget in brackets): b1 378 (1), b8 411 (0), fp16 47,967 (3), bf16_b1 48,933 (4), bf16_b8 48,933 (6).<br>b1 event: dj −3.34e-05, dk +4.168e-04, pair drift +4.501e-04.<br>`drift` q0.999 by slot bucket {0, 1–7, 8–15, 16–63}:<br>• b1: 5.91e-05, 4.77e-05, 4.39e-05, 4.01e-05; 328 of 3,090,528 adjacent pairs above budget; 0 absent.<br>• b8: 6.29e-05, 5.34e-05, 4.96e-05, 4.67e-05; 254 of 3,090,528; 0 absent.<br>`tau_definition`: topk_used 64 (read: census JSON); quantile 0.999 (read: the `calibrate_tau_topk` default). I verified all 86 dump files. |

**2. Text checks**
- **Placement.** I built every insertion in memory with the generator's own planner; nothing was written. The anchors are correct:
  - FINDINGS.md: after 55 (F-7), 78 (F-10) and 86 (F-11). After 125, F-14's erratum line comes first and the F-15 block second.
  - docs/BLUEPRINT.md: after 70, the end of the Phase 2 paragraph.
  - OPEN_QUESTIONS.md: after 16, one note covering lines 15–16.
  - README.md: after 50, and the status note after 16.
- **Numerals.** Every numeral in all nine insertions traces to a payload value at its printed rounding, or to a line or range label. The "245" in "1 - exp(-245/N)" is Lbar 244.79 rounded, which I checked by hand.
- **E15 bullet.** It does not say F-11's direction reverses. It says that 3 of 4 comparisons reverse under the pinned all-class rule, then gives the by-class result and that F-11's direction holds for corrections.
- **E16 bullet.** It attaches CORRECTED only to F-14's E8a sentence and says the top-1 claims stand. It says "tail drift" and "not a top-1 calibration".
- **Brackets.** They match the status fields.
- **"Finding:" line.** "Reproduced every value" is true after this pass. The only leaves I copied instead of deriving are three text labels (`measured.definition`, `prediction_sources`, `tau_definition.note`); the last two I checked by hand.

**3. Objections**

1. **BLOCKING (F-15 caveats line: one false sentence).** "F-5's and F-7's printed "2tau" thresholds are four times the census tau" is false for F-7's fp16 label. F-7 prints 0.066, which is 2 × 0.0331 = 0.0662, i.e. 2 tau (read: results/p2_llama32_rank_census.json).
   - The other labels are 4 tau:
     - F-5's four: 0.142, 0.93, 5.0 and 12.3, which are 4 × 0.0355, 0.2325, 1.2506 and 3.0752 (read: results/p2_rank_census.json).
     - F-7's bf16 0.93 and int8 6.6, which are 4 × 0.2327 and 4 × 1.649.
   - The protocol's own observation states the exception; the generator dropped it. F-15 is append-only once landed, so this has to be fixed before it lands.
   - Suggested wording: "F-5's four and F-7's bf16 and int8 printed '2tau' thresholds are four times the census tau (F-7's fp16 0.066 is 2 tau)".
   - Aside for the later row: the code settles the question the protocol left open. `census_row` passes `tau=2*tau`, and `_census_core` counts `flip_gaps > tau`, so the census's `flips_beyond` counts are at 2 tau and only the printed labels are 4 tau.

2. **ADVISORY (E16 text: "a tail drift, not a wide-gap flip").** Delete "not a wide-gap flip" and keep "a tail drift (one context; 328 of 3,090,528 adjacent pairs drift past the budget), not evidence of a pipeline bug".
   - The record defines a wide-gap flip as a gap above the 2(tau_enc + tau_dec) pair budget: FINDINGS.md:76 and BLUEPRINT.md:65.
   - Under the depth reading that E16's CORRECTED relies on, this order difference exceeds that budget, so under that reading it is one.
   - Under the top-1 reading the phrase is vacuous. Either way it does not help.

3. **ADVISORY (E16 text: "near-ties at logit scale, every one" next to CORRECTED for F-14's "every one a near-tie").**
   - F-14's sentence printed its own maximum gap, 1.48e-04, and this text endorses it at logit scale. The correction is that a threshold has now been supplied.
   - Suggested wording: "F-14's sentence holds at logit scale; at the record's fp32 pair budget, one context (twice in the corpus) exceeds it".

4. **ADVISORY (F-15 title and the README status note).**
   - "2 of 2 claims corrected, 0 confirmed" counts pinned statuses. The payload's own claim-site fields say E15 stands at 4 of 4 sites, and E16's only correction is of F-14's own sentence.
   - The README note ("2 of 2 corrected") carries no qualifier at all.
   - The same convention was used for F-14's E9 and was accepted as advisory, but here it contradicts `status_by_claim_site` for a whole row.
   - The title's "F-10's '1/170' … compare across escape regimes" is also off: F-10's figure reproduces in its own regime, and it is F-11's comparison that crosses regimes.

5. **ADVISORY (E16 top-1 claim sites take only cuda_fp32_b1's slot-0 status).**
   - F-7:55, OPEN_QUESTIONS.md:16 and F-10:76 item (1) are claims about fp16 and bf16 flips too.
   - All five arms' slot-0 counts above budget are 0: b1 0/1, b8 0/0, fp16 0/208, bf16_b1 0/983, bf16_b8 0/834. So CONFIRMED stands.
   - Derive the status from all arms, and replace "0 of 1 exceed the budget on this arm, so the top-1 claims stand" with those five counts.

6. **ADVISORY (E15 text).**
   - "That regime is the escape on and C desyncs only" can be read as saying only C desyncs occur at 0.465/2. That row has 88 (bf16) and 16 (fp16) T desyncs (read). Better: "the prediction counts C desyncs only".
   - "The all-class reversal is the rank-1 term" holds for the fail rates too, but the payload carries no number for that. My first pass does (c2_e15.out.json): with C hazards only at theta 0, the expected fails are 131.6 (65.8%) against 84% for bf16, and 42.5 (21.3%) against 28.5% for fp16.

7. **ADVISORY (F-15 regime and source lines).**
   - The cited protocol blob (b15ba24f9d5d) is the file at 9c325c4, which includes the post-critic entry. The pre-registration is cfb9595, blob 09aba6888a01.
   - "With one post-dry-run entry adding an informational field" omits the post-critic entry. That entry added every by-class, claim-scope and claim-site status shown in the brackets; only the caveats line mentions it.
   - The source line lists dry_b2.json but not dry_b2_pre.json, the run the "after the dry run" entry now refers to.
   - The post-critic log entry does not record that `class_shares_theta0` was dropped, although the earlier entry promised the erratum would print class shares.

8. **ADVISORY (predictions line).**
   - "Predictions scored (the critic's values …)" labels all eight E15 predictions as the critic's, but `prediction_sources` marks four as the protocol's own.
   - "fp16_measured_one_in miss" scores the critic's quotation of F-11's printed "1/670" against 670.51, which rounds to 671. The critic made no prediction there.

9. **ADVISORY (labels and dry-run display).**
   - FINDINGS F-7 and F-10, and the BLUEPRINT note, carry "erratum" lines although every claim site they point for is CONFIRMED. A neutral pointer would fit better.
   - The dry run prints insertions sorted by text, so it shows F-14's erratum line after the F-15 block. The write order is correct; I verified it in memory.

RECOMPUTE DISCREPANCY 0, BLOCKING 1

**What would change my mind**
- **Objection 1** would drop if a census source existed in which F-7's 0.066 is 4 × tau. results/p2_llama32_rank_census.json gives fp16 tau = 0.0331.
- **Objection 2** would rise to BLOCKING if the owner holds that E16's depth order differences are "flips" in XB-3's sense. That is the reading E16's CORRECTED uses, and under it the sentence is false.
- **The "reproduced every value" verdict** would change if the three copied text labels are meant to be values that must be derived independently.

Scripts, all in results/errata_critic/. Each writes its output to a matching `.out.json` with LF line endings:
- c2b_prov.py: provenance.
- c2b_e15.py: E15 recompute, all fields and statuses.
- c2b_e16.py: E16 recompute, all fields and statuses, plus slot 0 on every arm.
- c2b_text.py: placement and numeral trace, in memory.

## Second batch: third pass (after 3cec4df, reviewed at 8515734), verbatim

**Critic report, second batch, third pass (E15, E16). Payload: results/errata_recompute_2.json, HEAD blob 09f389ad24ccfcae4d2397a89fa2df2821df15c4, written at 05c3305, committed at 3cec4df. HEAD at review: 8515734 (tests-only corrective). Text: `experiments/errata_text.py --payload results/errata_recompute_2.json --finding F-15 --dry-run`, run read-only at 8515734.**

I recomputed every value of the regenerated rows with new standalone scripts (`c2c_*`), including the fields added after the second pass. All values reproduce exactly: 467 value leaves in E15 and 379 in E16, plus 9 and 12 status leaves, with a maximum discrepancy of 0. Every status field follows from the values and from the 2026-10-11 UTC "after the critic's second pass" entry. The second-pass BLOCKING (the caveats sentence on the "2tau" labels) is fixed, and so is every advisory the coordinator listed.

I found nothing false in the nine insertions. One new sentence in the E15 bullet sets a C-hazards-only failure prediction beside the all-class measured failure rates. That overstates the size of the correction excess on the failure metric (objection 1), and my own second-pass wording invited it. The "finding:" line's sentence that my recompute "reproduced every value" is true after this pass.

Every number below was computed by my scripts unless marked (read).

**Provenance (task A): checks out.**
- All 38 `provenance.inputs` ids equal `git rev-parse 05c3305:<path>`.
- The tree (5853654) and `script_blob` (461118c) match. `script_sha256_lf` (62ea01c7…) and `lib_sha256_lf` (ec28d59b…) match the committed files at 05c3305 and at HEAD. The corrective commit touches only tests/test_errata_text.py.
- The payload has 0 CR bytes and equals its HEAD blob.
- All 20 rows of the second-batch source table still equal git at 509ad90. REPORT.md moved only by append-only additions.
- ERRATA_PROTOCOL.md at 9c325c4 is a byte prefix of the version at 05c3305. The regime line's blob, 2ea030ea35ae, is the protocol at 05c3305 (verified).
- Payload at 553ffb4 against 3cec4df:
  - 868 shared leaves; only the two `seconds` fields differ.
  - 7 leaves removed: the two F-11 quotations from `prediction` and their `prediction_sources`, plus the three renamed top-1 claim-site keys.
  - 28 leaves added, all of them the fields the amendment lists.
- The errata tests pass at HEAD (32). The tracked tree stayed clean apart from my new files.

**1. Per-row table**

row | payload status | my status | max discrepancy | note
---|---|---|---|---
E15 | CORRECTED; claim regime CONFIRMED; by class A CORRECTED, C CONFIRMED, all CORRECTED; all 4 claim sites CONFIRMED | identical on every field | 0 (467 value + 9 status leaves) | New `fail_exact` (theta 0, h4):<br>• C hazards only: 65.81% (131.62 expected fails) bf16; 21.27% (42.55) fp16.<br>• A hazards only: 74.84% (149.67) bf16; 20.10% (40.19) fp16.<br>`f11_printed_one_in`: 65 against 65.10, which rounds to it. 670 against 670.51, which does not: F-11's "1 per 670" is a truncation, and the text does not use the figure.<br>`pinned_rule_sites` = [FINDINGS.md:85].<br>`prediction_sources`: 6 keys; the two `all_theta0_one_in_h1` keys are the critic's (REPORT.md first pass item 13) and the other four are the protocol's (checked by hand). |
E16 | CORRECTED; by arm b1 CORRECTED, b8 CONFIRMED; claim scope CONFIRMED on all 5 arms; F-14 sentence sites CORRECTED; 3 top-1 sites CONFIRMED | identical on every field | 0 (379 value + 12 status leaves) | Slot-0 counts above budget: b1 0/1, b8 0/0, fp16 0/208, bf16_b1 0/983, bf16_b8 0/834. So the top-1 sites are CONFIRMED under the amendment's every-arm rule.<br>`pinned_rule_sites` = FINDINGS.md:114, OPEN_QUESTIONS.md:15, README.md:50.<br>All 86 dump files re-verified by sha256. |

**2. Text checks**
- **Placement.** I built every insertion in memory with the generator's planner; nothing was written. The dry run now prints insertions in write order.
  - FINDINGS.md: a note after 55 (F-7), a note after 78 (F-10) and an erratum after 86 (F-11). After 125, the F-14 erratum line comes first and the F-15 block second.
  - docs/BLUEPRINT.md: a note after 70, the end of the Phase 2 paragraph.
  - OPEN_QUESTIONS.md: an erratum after 16, covering lines 15–16.
  - README.md: an erratum after 50, and the status note after 16.
- **Labels.** The erratum and note labels follow the amendment's rule. F-11 is "erratum" because FINDINGS.md:85 is the site the pinned rule scores.
- **Numerals.** Every numeral traces to a payload value at its printed rounding, or to a line label, range label or commit id. "245" is Lbar 244.79 rounded. I checked these by hand:
  - "7 of 8 claim sites": E15's four claim-site keys all stand, and three of E16's four do.
  - "65.8% and 21.3%": the C-hazards-only `fail_exact` values.
  - The five slot-0 counts.
- **Required content.**
  - The E15 bullet does not say the direction reverses, and it says "the prediction counts C desyncs only".
  - The E16 bullet attaches CORRECTED only to F-14's sentence and says that sentence holds at logit scale. It calls the one context "a tail drift, not evidence of a pipeline bug", no longer says "not a wide-gap flip", and prints all five arms' slot-0 counts.
  - The caveats sentence on the "2tau" labels is now true. F-5's four labels and F-7's bf16 and int8 labels are 4 tau; F-7's fp16 0.066 is 2 tau (read: both census JSONs). The census's beyond-2tau counts were taken at 2 tau (from the code).
  - The title and README note count rows under pinned rules and claim sites at their own scope, and the title attributes the cross-regime comparison to F-11.
  - The regime line names the protocol entries behind the cited blob, and the source line lists dry_b2_pre.json.
- **"Finding:" line.** "Reproduced every value" is true. The only leaves I took from the payload instead of deriving are text labels (`measured.definition`, `tau_definition.note`, `prediction_sources`); I checked the last by hand.

**3. Objections**

1. **ADVISORY (E15 bullet: the C-hazards-only failure comparison is not like-for-like).** The bullet reads: "with correction hazards alone the theta-0 whole-archive failure prediction is 65.8% and 21.3% against the measured 84.0% and 28.5%, so the correction excess holds on both metrics".
   - The measured 84.0% and 28.5% include the archives whose first desync was rank-1 (28 and 9 of 200). A C-only prediction should be compared with C-caused failures: 140/200 = 70.0% and 48/200 = 24.0%.
   - Against 65.8% and 21.3%, the excess is 4.2 and 2.7 points, about 1.25 and 0.94 binomial sd. The printed pair shows 18.2 and 7.2 points.
   - Under the full rank-only theta-0 model, the expected C-caused first-desync rates are 58.2% and 20.3%. The measured C-caused rates exceed both predictions, so the direction holds, but on the failure metric it is within noise on both arms.
   - Not false, but it overstates the magnitude in an append-only finding. Suggested wording: "C-caused failures are 70.0% and 24.0% (140 and 48 of 200) against 65.8% and 21.3% with correction hazards alone: the same direction, within about one binomial sd".
   - I own the origin. My second-pass objection 6 put "65.8% against 84%" side by side to support a different statement (that without the A term no comparison reverses, which is valid), and the generator reused the pair for a magnitude claim.

2. **ADVISORY (caveats line: the label rule as stated).** "Labelled erratum where a site there is corrected and note where it stands" does not match F-11. Its site, FINDINGS.md:85, stands at its own scope (it is one of the title's 7 standing sites), yet it carries "erratum". The amendment's rule includes "or is a pinned rule's site". The caveat should say so.

3. **ADVISORY (predictions line).** The line says "each labelled by its source", but E16's seven predictions carry no label (all are the critic's) and E16 has no `prediction_sources` field.

4. **ADVISORY (house rule).** 05c3305 and 3cec4df were committed with two tests failing; 8515734 says so. That breaks CLAUDE.md's "make test green before commits". The payload is unaffected: the corrective commit changes only test expectations, the code that wrote the payload is unchanged at HEAD, and 32 tests now pass.

5. **ADVISORY (carried over, unverifiable).** "Before any code for them ran" is self-reported. The earliest E15/E16 run on record, dry_b2_pre.json, was written at 22:01:57 on a dirty tree at cfb9595, 4 min 56 s after the protocol commit. Git cannot show more than that ordering.

RECOMPUTE DISCREPANCY 0, BLOCKING 0

**What would change my mind**
- **Objection 1 would become BLOCKING** if the owner reads "the correction excess holds on both metrics" as a claim about magnitude rather than direction. On the like-for-like comparison (z +1.25 and +0.94), a magnitude claim on the failure metric is not supported.
- **The verdict of nothing false** would change if a census source gave tau values other than results/p2_rank_census.json and results/p2_llama32_rank_census.json, since the corrected caveat rests on them. It would also change if "claim site" is meant per location rather than per status key. Then E16 has six locations, the F-14 sentence alone accounts for three, and "7 of 8" would need restating.
- **The "reproduced every value" verdict** would change if the text labels I copied count as values that must be derived independently.

Scripts, all in results/errata_critic/. Each writes its output to a matching `.out.json` with LF line endings:
- c2c_prov.py: provenance.
- c2c_e15.py: E15 recompute, all fields and statuses, plus the C-caused failure audit.
- c2c_e16.py: E16 recompute, all fields and statuses, slot 0 on every arm.
- c2c_text.py: placement and numeral trace, in memory.

## Second batch: fourth (narrow) pass (after 980597b), verbatim

**Critic report, second batch, fourth (narrow) pass. Payload: results/errata_recompute_2.json, HEAD blob 5ff5b67e6d24b7e89a94a99a2871e1bb97c0319d, written at 8211329, committed at 980597b (HEAD at review). Text: `experiments/errata_text.py --payload results/errata_recompute_2.json --finding F-15 --dry-run`, run read-only at 980597b.**

All three items check out. Nothing in the nine insertions is false. Every number below was computed by results/errata_critic/c2d_check.py unless marked (read).

1. **The E15 failure-metric sentence: OK.** In the E15 bullet and in the BLUEPRINT note it reads: "on the failure metric, C-caused failures are 70.0% and 24.0% (140 and 48 of 200) against 65.8% and 21.3% with correction hazards alone: the same direction, by 1.2 and 0.9 binomial sd of the predicted rate, within noise."
   - I recomputed it from the raw sources, not from the payload. The counts are C first desyncs over archives (read: p4_real_archive.json) and match the compensator's observed C: 140 and 48 of 200.
   - p is the theta-0, C-hazards-only, whole-archive failure prediction from the P2b theta-0 row and the 200 P4 symbol streams: 0.658086 and 0.212745, equal to the payload's `c_only_theta0_h4` exactly.
   - k = (O/n − p)/√(p(1−p)/n) = 1.2496 and 0.9418, printed as 1.2 and 0.9. "Within noise" holds because both are below 2.
   - The old "holds on both metrics" sentence is gone.

2. **Labels and wording: OK.**
   - **Predictions line.** Every E16 prediction now carries "(critic)", and E15's labels are unchanged.
   - **Caveats line.** It states the full rule: "erratum where a site there is corrected or is the site a pinned rule scores, and note where every site there stands". That matches the pointer labels: note under F-7, F-10 and BLUEPRINT; erratum under F-11, F-14, OPEN_QUESTIONS.md and README.md:50.
   - **Title and README note.** Both say "7 of 8 claim-site statuses standing at their own scope".
   - **Regime line.** It says the pre-registration was "committed before the first code for them (the history shows that order; the order of writing is self-reported)". That is true: cfb9595 contains only the protocol and precedes b35e126, the first code commit. The cited blob, 861afe70f1c6, is the protocol at 8211329.
   - **Scope of the change.** A word-level diff against the third-pass dry run shows changes only in the title, the regime line, the E15 failure sentence (FINDINGS.md and BLUEPRINT), the predictions line, the caveats label rule and the README note.

3. **Provenance and unchanged values: OK.**
   - All 38 `provenance.inputs` ids equal git at 8211329.
   - The tree, `script_blob`, `script_sha256_lf` and `lib_sha256_lf` match.
   - The payload has 0 CR bytes and equals its HEAD blob.
   - The protocol at 05c3305 is a byte prefix of the version at 8211329, so the log stays append-only.
   - Against 3cec4df: 896 shared leaves, and only the two `seconds` fields differ. Nothing was removed. The 7 added leaves are all `E16/value/prediction_sources`. So the second-to-fourth-pass recomputes still cover every value, and the "finding:" line's "reproduced every value" stays true.
   - The errata tests pass (32), and the tracked tree is clean apart from my new files.

**ADVISORY (E16 `prediction_sources`).** The label says "first pass items 5 and 13; third pass item 2", but item 13 is the E15 proposal.
- E16's values come from first pass item 5 (379 and 411), second pass item 4 and third pass item 2 (the 2 above 8.6e-05, the 1.478195e-04 and 5.722046e-05 maxima, and the adjacent competitor).
- `b8_count_above_budget` = 0 was the protocol's own inference from the critic's b8 maximum; the critic never stated it.
- This sits in the payload label and the protocol entry only; the nine insertions print "(critic)", which is fair in substance.

RECOMPUTE DISCREPANCY 0, BLOCKING 0

Nothing in the nine insertions is false. Script: results/errata_critic/c2d_check.py, which writes its output to c2d_check.out.json with LF line endings.

## Third batch (rows E17, E18, E19): first pass (after 5b5664f, reviewed at 1ac19bf), verbatim

**Critic report, third batch (E17, E18, E19). Payload: results/errata_recompute_3.json, HEAD blob 79fa0e9edeb36fca6f05b521c46d156b82e5dce2, written at a90c107, committed at 5b5664f. HEAD at review: 1ac19bf. Text: `experiments/errata_text.py --payload results/errata_recompute_3.json --finding F-16 --dry-run`, run read-only at 1ac19bf.**

I recomputed every value of the three rows with standalone scripts (`c3_*`), reading the raw shards, dumps, census JSONs and P1/P5/P6 files directly. For E18 I retrained every dictionary. Every value reproduces exactly: 113 leaves in E17, 126 in E18 and 192 in E19, with a maximum discrepancy of 0. Every status field follows from its values under the entry's rules.

Two problems are with what the rows and text say, not with the numbers:
- E17's text says only the labels are wrong. The 4-tau labels also produced F-5's and F-7's escape-cost figures, which are wrong by the same factor of threshold.
- E19's status was decided by a rule written after its primary values were known. They are my own second-batch post-hoc values, reproduced to every digit, and the F-16 text presents them as a pre-registered confirmation with six prediction hits.

Every number below was computed by my scripts unless marked (read).

**Provenance (task A): checks out.**
- All 49 `provenance.inputs` ids equal git at a90c107.
- All 29 rows of the third-batch source table equal git at 168efb0. None moved by a90c107, and all are in `inputs`.
- The three sideband harvest files match their pinned sha256 prefixes: spot6.py 16287b93720382ed, spot7.py 7193399480e8650f, zdict_sess.py 9f6b55072b409215.
- The payload has 0 CR bytes and equals its HEAD blob. The tree, script blob and LF-normalised script/lib sha256 match.
- ERRATA_PROTOCOL.md is append-only from 168efb0 to a90c107 to HEAD, and 04dbf23 (00:15:12) touches only the protocol.
- dry_b3.json: head 04dbf23, dirty tree, written 00:20:13, with the final script and lib (sha256 equal). Its 487 leaves equal the payload's apart from three `seconds` fields, and the statuses are identical.
- 727338d and 1ac19bf touch only experiments/errata_text.py. The errata tests pass (36).

**1. Per-row table**

row | payload status | my status | max discrepancy | note
---|---|---|---|---
E17 | CORRECTED; status_by_count CONFIRMED; F-5 and F-7 sites CORRECTED | identical | 0 (113 leaves) | I parsed the seven labels and beyond-counts from FINDINGS.md:40 and :54 at 168efb0, not typed: 6 are 4 tau and 1 is 2 tau. All counts equal the census's `flips_beyond_tau`. Each row's `tau` field is 2 tau. Code semantics confirmed in the source: `census_row` passes 2 tau, and `_census_core` counts `flip_gaps > tau`. See objection 1. |
E18 | CORRECTED; per archive CORRECTED, k=16 sessions CORRECTED, both concatenated sites CONFIRMED | identical | 0 (126 leaves) | My decode (`tokenizers`, special tokens kept) reproduces P5's all-row 7.280526165284529 and 3.9372523387393277 exactly, so the text is P5's.<br>Dictionary training is deterministic on this box: two trainings are byte-identical, and sha256 and dict_id equal the payload's. The 65536 and 262144 requests both return the same 22,323-byte dictionary.<br>Effects: 0.345 per archive, 0.194 at k=16, 0.254 at k=8, 0.045 concatenated, 0.043 generated text concatenated. The crossover formula on all rows gives 263.22, the printed 263. |
E19 | CONFIRMED; status_e15_rule_gap_conditioned CONFIRMED; both claim sites CONFIRMED | identical | 0 (192 leaves) | The dumps' A desyncs are 159 and 25, equal to P2b's theta-0 row. Primary E_A 33.282 / 15.028 (z −0.92 / −1.55). Grid z: −0.40 to −1.33 for bf16, −0.53 to −1.79 for fp16. See objections 2 and 5. |

**2. Checks of rules, predictions and text (tasks C and E)**
- **E17 predictions (n_labels_4tau 6, n_labels_2tau 1, counts match).** These are values seen before the entry, and the entry says so.
- **E18 predictions.** All seven of the harvest's predictions reproduce exactly under its own definitions:
  - Its spot6.py/spot7.py decode the same token ids with `tokenizers`' default `skip_special_tokens=True`, which gives 6.251 with no dictionary, then 4.737, 4.446 and 4.408 with the 4 KB, 16 KB and 64 KB dictionaries (the 64 KB one is 22,330 bytes).
  - spot7.py's repeat share divides by len(g), which selects 23 rows and gives 5.253 and 10.330.
  - So the six "misses" come from definitions, not from a computational disagreement.
  - The coordinator's premise is wrong in one detail: the predictions came from spot6.py/spot7.py, not from zdict.py's prompt-string text.
  - The F-16 attribution of 6.775 to the special-token literals is correct: the held-out rows carry 100 begin and 5 end literals, 1,775 bytes in all. "Which a dictionary absorbs" is also correct: with the 16 KB dictionary, text with the literals compresses to 4.4387 and text without them to 4.4458.
- **E19 predictions.** They are read programmatically from my results/errata_critic/c2_e15_gapsens.out.json (`p2_quantile20`) and equal the primary values by construction (objection 2).
- **Placement.** Every insertion lands at a paragraph or bullet end:
  - FINDINGS.md: after 41, 56, 64, 80, 96, 103 and 139, with the F-15 note line written before the F-16 block.
  - DECISIONS.md: after 44 (the end of D-6) and after 132 (between D-11's bullets).
  - docs/BLUEPRINT.md: after 54 and after 86.
  - OPEN_QUESTIONS.md: after 32.
  - README.md: after 17 and after 50.
- **Labels.** These follow the generator's implemented rule. The caveats' statement of the rule does not match one of them (objection 9).
- **Numerals.** Every numeral in the nine insertions traces to a payload value at its printed rounding, or to a date, row range, key name or commit id. I hand-checked the E17 taus, the E18 rates, effects and multiples, and the E19 E_A, z, one_in and failure rates.

**3. Objections**

1. **BLOCKING (E17: "only the labels are wrong" is false; the 4-tau labels reached the escape-cost claims).**
   - F-5 (FINDINGS.md:40) prices the escape at "6.7% of positions at 0.142 (fp16's 2tau) … 32.6% at 0.93 (bf16's 2tau)" (read).
   - F-7 (FINDINGS.md:54) says "the escape-symbol cost for a bf16 decoder is ~39% of positions on this model, for fp16 ~8%" (read). OPEN_QUESTIONS.md:16 repeats "~8% … fp16, ~39% for bf16" (read), and that site is not in E17's `where`.
   - From the cpu_fp32 dump, I reproduce F-7's near-tie masses at the printed thresholds: 8.25%, 23.24% and 39.11%. At the census's actual 2 tau they are 4.13% for fp16 (0.0662) and 23.25% for bf16 (0.4654).
   - F-5's own figure at 0.465, which is TinyLlama's 2 tau for bf16 (0.4649), is 19.0% (read), not 32.6%.
   - The record's later practice used theta 0.465 for bf16 and removed every A desync there (F-10), so 2 tau is the threshold that was needed.
   - The F-16 sentence "so the claims 'every flip within 2 tau' stand and only the labels are wrong" and the row note "label defect only" understate the correction. So does "a label defect, not a count defect", which the second-batch amendment adopted from my second-pass aside. That aside said "only the printed labels are 4 tau" and I did not check the cost claims then.
   - Fix: say that the labels, and the escape-cost figures quoted at those labels, are wrong; print the 2-tau costs; add OPEN_QUESTIONS.md:16. The status (CORRECTED) is unchanged.

2. **BLOCKING (E19: the status was decided by a rule pinned after its primary values were known; F-16 presents it as a pre-registered confirmation).**
   - The primary binning (20 equal-count bins, edges at quantiles 0.05–0.95) is exactly my second-batch post-hoc `p2_quantile20`. My E_A, one_in and fail values equal the payload's to every digit: 33.281990521326975 and 15.027646129541841; 103.21404535498503; 0.7466950835701788 and 0.2743004142463592.
   - That file was committed at 93ea7de (2026-10-10 22:42:31), 1 h 33 min before the pre-registration 04dbf23. O_A (28 and 9) was in results/p4_real_archive.json, so the deciding z was computable before the rule was written.
   - The payload's E19 `prediction` dict is computed by reading that file, so the six "hits (critic)" hold by construction.
   - The F-16 regime line says all three rows were "pre-registered" and names only E17's ratios as seen before the entry.
   - This is the predecessor's E13 case: a rule written after its result was read decides a status.
   - Fix (the E13 remedy): label E19's status as decided by a rule written after its primary values were seen, so it is a recorded post-hoc analysis. Do not score the six E19 predictions, or mark them identical by construction. Say in the regime line that E19's primary values had been seen.
   - The six other binnings were not seen before. Their z range (above) is the row's only out-of-sample evidence, and the text should say so.

3. **ADVISORY (three FINDINGS line pins are off by one).** At 168efb0 the following are each finding's "- source:" line:
   - FINDINGS.md:76: F-10 item (4) is on 77.
   - FINDINGS.md:94: F-12's "7.28 per archive" is on 95.
   - FINDINGS.md:101: F-13's "3.4x at k=16" is on 102.

   They appear in `where`, the claim-site keys, `pinned_rule_sites` and the F-16 brackets. Pointer placement is by finding block, so no line lands in the wrong place, but F-16 is append-only. Fix before landing. (The predecessor graded a placement error as advisory; I follow that.)

4. **ADVISORY (E18 predictions line).**
   - The generator labels any source not containing "critic" as "(protocol)", so the harvest's seven predictions print as "(protocol)", against `prediction_sources`.
   - The six "misses" should say they reproduce exactly under the harvest's own text and repeat-share definitions (item 2 above).

5. **ADVISORY (E19 wording: "the dumps' rank-1 rate transfers").** "Consistent with transfer at this sample size" is what the data support.
   - O/E is 0.84 (95% Poisson interval 0.56–1.22) for bf16 and 0.60 (0.27–1.14) for fp16. The test cannot exclude an archive rank-1 rate 44% or 73% below the dumps'.
   - `status_e15_rule_gap_conditioned` holds at 6 of 7 binnings. At quantile10, fp16's rate comparison reverses (one_in 668.2 against a measured 670.5). At the primary binning, fp16's margins are about 2% (681.7 against 670.5; 27.4% against 28.5%).

6. **ADVISORY (E19 claim-site scope).** "FINDINGS.md:76 (F-10 item (4): the rank-1 term, gap-conditioned) CONFIRMED" scores a term the site does not contain: item (4) is C-only, with the escape on.
   - The record's transfer claim is F-10's caveat at FINDINGS.md:78: "the per-rank rates are what transfer, the mix is not" (read).
   - E15 showed that claim fails for the rank-1 term (0.44x and 0.26x), and E19 qualifies it. The F-10 pointer is labelled "note", as if everything there stands.

7. **ADVISORY (E18 sites).** F-11 (FINDINGS.md:86) prints the same strawman comparator, "against zstd-19 … 7.28 per archive" (read). At the per-archive scale it would be CORRECTED, but it is not in `where`, so F-11 gets no pointer. DECISIONS.md:105 ("~3.3 bits/token on 245-token archives, comparable to zstd") is also unlisted.

8. **ADVISORY (E18: part of the effect is the literals).**
   - The 34% per-archive effect includes the dictionary absorbing the special-token literals.
   - Without them, with the dictionary trained on the same text, the effects are 0.289 per archive, 0.180 at k=16, 0.234 at k=8 and 0.039 concatenated. Every status is unchanged at the 0.10 threshold.
   - Printing both figures would keep P5's literal-carrying comparator from inflating the headline.
   - The families are interleaved (34/33/33 in training, 33/34/33 held out) and the topics are disjoint, so the note "the other half of the same prompt families" is accurate. The shared prompt templates favour zstd, as the note says.

9. **ADVISORY (caveats line: the label rule as stated).** The caveats line says "erratum … where a site there … is the site a pinned rule scores". FINDINGS.md:76 is E19's pinned site, yet F-10 is labelled "note". The implemented rule also requires the row's pinned status to be CORRECTED, and the caveat should say so.

10. **ADVISORY (E17 code, latent).** `n_labels = n4 + n2`. A label at any other multiple would drop out of the count, and the status test `n4 == 0 and n2 == n_labels` could then pass as CONFIRMED. It is not triggered here (all 7 labels are 2 or 4). Count the printed labels instead.

RECOMPUTE DISCREPANCY 0, BLOCKING 2

**What would change my mind**
- **Objection 1** would drop if the escape threshold were 4 tau rather than 2 tau. Against that: P2b's budgets are 2 tau, and theta 0.465 (2 tau) removed every bf16 A desync (F-10).
- **Objection 1** would also drop if the owner reads F-7's "~39% / ~8%" as costs at the printed thresholds rather than at each dtype's 2 tau. But F-7 attaches them to the decoders, not to the thresholds.
- **Objection 2** would drop to advisory with a record showing the E19 primary binning and rule were fixed before 93ea7de's values were read. It would also drop if the F-16 text labels E19 as post hoc and stops scoring its predictions.

Scripts, all in results/errata_critic/, each writing a matching `.out.json` with LF line endings:
- c3_prov.py: provenance.
- c3_e17.py: E17 recompute.
- c3_e17_cost.py: near-tie masses at 2 tau and 4 tau.
- c3_e18.py: E18 recompute, the harvest-definition reproduction, effects without the literals.
- c3_e19.py: E19 recompute, intervals, grid robustness, equality with p2_quantile20.
- c3_text.py: placement and numeral trace, in memory.

## Third batch: second pass (after d1a9f9d), verbatim

**Critic report, third batch, second pass (E17, E18, E19). Payload: results/errata_recompute_3.json, HEAD blob bacc8f641313710dab1d15231ed8801efbe75def, written at 2c5e06a, committed at d1a9f9d (HEAD at review). Text: `experiments/errata_text.py --payload results/errata_recompute_3.json --finding F-16 --dry-run`, run read-only at d1a9f9d.**

Both first-pass BLOCKING objections are fixed, and so are all eight advisories.

Every value of the regenerated rows reproduces with new standalone scripts (`c3b_*`): 178 leaves in E17, 165 in E18 and 215 in E19, plus every status field. The only differences are floating-point. The largest is 4.4e-16 on an E19 interval endpoint, because I use bisection on the Poisson CDF where the payload uses scipy's chi2. The other is 6.2e-17 on one E18 effect, from a different order of arithmetic. Every status follows from the values and the entries.

The instrument amendment is of the E4/E7 kind, not worse. One sentence in the F-16 caveats line is false: it says the masses are over the kept positions, contradicting the amendment and the payload.

Every number below was computed by my scripts unless marked (read).

**Provenance: checks out.**
- All 50 `provenance.inputs` ids equal git at 2c5e06a, including the new results/p2_tinyllama_dumps.sha256.
- The 29-row source table still equals git at 168efb0, and the three harvest files match their pinned sha256 prefixes.
- The payload has 0 CR bytes and equals its HEAD blob. The tree, script blob and LF-normalised script/lib sha256 match.
- ERRATA_PROTOCOL.md is append-only from 168efb0 through a90c107 and 2c5e06a to HEAD. The regime line's blob, d4473abb3121, is the protocol at 2c5e06a.
- The new TinyLlama manifest equals the 144 results/p2 entries of the original results/p2_dumps.sha256 (committed at 6672db4, before any errata run), digest for digest. So those dumps were pinned before any value was seen.
- First payload (5b5664f) against this one: 458 shared leaves. Only claim and note text, `seconds` fields and the corrected line pins differ; no numeric value changed.
- dry_b3b.json: head d350243, dirty tree, written 00:48:35, with a script that differs from the final one. In it the F-7 and OPEN_QUESTIONS.md:16 cost sites are UNRECOMPUTABLE, as the after-dry-run entry says.
- The errata tests pass (37).

**1. Per-row table**

row | payload status | my status | max discrepancy | note
---|---|---|---|---
E17 | CORRECTED; beyond-counts CONFIRMED; all 5 claim-site statuses CORRECTED; under the original tolerance, the F-7 and OPEN_QUESTIONS.md:16 cost sites are UNRECOMPUTABLE | identical, including status_under_pinned_tolerance | 0 (178 leaves) | Near-tie masses over all 49,152 census positions:<br>• Llama: 8.2520 / 23.2422 / 39.1093% at the printed thresholds; at 2 tau, fp16 4.1300% (0.0662) and bf16 23.2524% (0.4654). These reproduce my first-pass 8.25 / 23.24 / 39.11 and 4.13 / 23.25 exactly.<br>• TinyLlama (results/p2, computed independently): 6.6711 / 19.0328 / 32.6314%; at 2 tau, fp16 3.4098% (0.0711) and bf16 19.0287% (0.4649).<br>Over the kept positions, the Llama mass at 0.465 is 23.2530%. The printed figures were checked against the claim text at 168efb0. |
E18 | CORRECTED; 5 per-archive or session sites CORRECTED, 2 concatenated sites CONFIRMED | identical | 6.2e-17 (165 leaves; floating-point, on effects_without_literals/concat) | The text still reproduces P5's 7.280526165284529 exactly. The harvest-definition dictionaries train deterministically too, and their sha256 and dict_id match. Harvest definitions: 6.251, 4.737, 4.446, 4.408 (22,330 B); 23 rows, 5.253 and 10.330. Effects without the literals: 0.289 per archive, 0.180 at k=16, 0.234 at k=8, 0.039 concatenated. |
E19 | CONFIRMED (post hoc); out of sample CONFIRMED; E15 rule under gap conditioning CONFIRMED; FINDINGS.md:78 CORRECTED; FINDINGS.md:136 CONFIRMED | identical | 4.4e-16 (215 leaves; interval endpoint, bisection against scipy chi2) | O/E 0.841 (0.559–1.216) and 0.599 (0.274–1.137). Margins +58.5% and +9.3 points for bf16; +1.7% and +1.1 points for fp16. E15's rule holds at 7/7 binnings for bf16 and 6/7 for fp16. Out of sample, the largest \|z\| is 1.79. `primary_equals_critic` is true. |

**2. The instrument amendment (E17): the E4/E7 kind, not worse.**
- The entry pinned the masses over the kept positions (49,056, E8c's mask). F-7's printed masses were taken by the census over all 49,152 positions (read: F-7's regime line and the census JSON `positions`). The original pin was therefore an instrument defect unrelated to the claim, like E4's float32 mean.
- The tolerance change does nothing. "Within 0.05 points" and "rounds to the printed one-decimal value" are the same width.
- The population is what decides the check. The kept-position 23.2530 fails both versions, and the all-position 23.2422 passes both.
- No verdict depends on it. The 2-tau masses round to the same figures over either population (Llama 4 / 23 against the printed 8 / 39; TinyLlama 3.4 / 19.0 against 6.7 / 32.6), so every cost site is CORRECTED either way. Only the instrument gate moves, from UNRECOMPUTABLE to decided.
- The amendment was written after the dry run showed the failure, and the payload records `status_under_pinned_tolerance`. That is the E4/E7/E13 remedy.
- One wording slip: the post-critic entry says the cost comparison is "rounded as printed (whole percent)", but F-5's figures are printed to one decimal. The code uses each figure's printed precision, which is right.

**3. Text checks**
- **Placement and labels.** All placements land at paragraph or bullet ends:
  - FINDINGS.md: after 41, 56, 64, 80, 89, 96, 103 and 139.
  - OPEN_QUESTIONS.md: after 16 and 32.
  - DECISIONS.md: after 44, after 107 (the end of the bullet holding DECISIONS.md:105) and after 132.
  - README.md: after 17 and 50.
  - docs/BLUEPRINT.md: after 54 and 86.

  The labels follow the rule the caveats now state, which is the implemented one: erratum under F-5, F-7, F-10, F-11, F-12, F-13, OPEN_QUESTIONS.md and DECISIONS.md; note under F-8, F-15 and BLUEPRINT.
- **Numerals.** Every numeral traces to a payload value at its printed rounding, or to a date, row range, key name or commit id. "44%" and "73%" are one minus the interval lows.
- **Required content.**
  - The E17 bullet says the labels and the escape-cost figures quoted at them are wrong, prints the 2-tau costs, and includes OPEN_QUESTIONS.md:16.
  - The E19 bullet says "consistent with transfer at this sample size", prints the intervals and margins, names the primary binning as my post-hoc one, and is not scored.
  - The regime line says E17's ratios and E19's primary values had been seen.
  - The predictions line labels the harvest's values "(harvest)".
- **"Finding:" line.** "Reproduced every value" is true at this pass, up to floating point.

**4. Objections**

1. **BLOCKING (F-16 caveats line: a false sentence).** "Its escape costs are near-tie masses over all kept positions of each model's dumps" contradicts both the after-dry-run entry and the payload. `mass_pct`, the figure printed and scored, is over all census positions (49,152); the kept-position masses (49,056) are a separate field. F-16 is append-only. Fix: "over all census positions (49,152) of each model's dumps".

2. **ADVISORY (E18 prediction scoring: the pinned scoring was dropped, not kept beside).**
   - The post-critic entry says the harvest's predictions are scored under its own definitions "beside the pinned ones".
   - The payload removed the pinned keys (zstd_arch_none, _4096, _16384, _65536, rep_below_half_*) from `prediction`. The predictions line now reads 7 of 7 hits.
   - Under the scoring pre-registered in the third-batch entry it was 1 hit and 6 misses, all six from definitions. The bullet explains the definitions, but the scoring record no longer shows the misses. Restore the pinned keys beside the harvest_def ones.

3. **ADVISORY (source line).** It lists dry_b3.json but not dry_b3b.json, the run the after-dry-run entry refers to.

4. **ADVISORY (E19 site FINDINGS.md:78).** Its CORRECTED rests on E15's rank-only compensator z (−4.48, −4.42). That field was itself added after the second batch's values were seen, and this site's rule was written after those values were in the record. The row's `post_hoc` field covers only the row status. The z values are far from the threshold, so the verdict is not fragile, but the bracket should say where it comes from.

RECOMPUTE DISCREPANCY 4.4e-16 (floating-point only), BLOCKING 1

**What would change my mind**
- **Objection 1** would drop if `mass_pct` were over the kept positions. It is not: the payload's own `positions` is 49,152, and my all-position masses equal `mass_pct` exactly.
- **The E4/E7 classification of the amendment** would change if any cost-site verdict differed between the two populations. None does, and that is computed for both models.
- **Objection 2** would drop if the owner holds that the third-batch entry's E18 "Prediction" was meant as the harvest's own quantities rather than the entry's pinned ones. The entry's wording ("held-out per archive, amber v3 4.181, zstd-19 6.251") names the pinned quantity.

Scripts, all in results/errata_critic/, each writing a matching `.out.json` with LF line endings:
- c3b_prov.py: provenance, plus the first payload and dry_b3b against this one.
- c3b_e17.py: E17 with escape costs for both models, both populations, both tolerances, and the manifest equality.
- c3b_e18.py: E18 with harvest definitions, effects without literals, and determinism.
- c3b_e19.py: E19 with intervals, margins, out-of-sample status and the F-10 site.
- c3b_text.py: placement and numeral trace, in memory.

## Third batch: third (narrow) pass (after 70b6dcc), verbatim

**Critic report, third batch, third (narrow) pass. Payload: results/errata_recompute_3.json, HEAD blob 80356a9e44523fe4c9eb10ce83cfa5e28c549211, written at f492e68, committed at 70b6dcc (HEAD at review). Text: `experiments/errata_text.py --payload results/errata_recompute_3.json --finding F-16 --dry-run`, run read-only at 70b6dcc.**

All four items check out. Nothing in the nine insertions is false. Every number below was computed by results/errata_critic/c3c_check.py unless marked (read).

1. **Provenance and unchanged values: OK.**
   - All 50 `provenance.inputs` ids equal git at f492e68.
   - The tree, script blob, `script_sha256_lf` and `lib_sha256_lf` match.
   - The payload has 0 CR bytes and equals its HEAD blob.
   - ERRATA_PROTOCOL.md at 2c5e06a is a byte prefix of the version at f492e68.
   - Against bacc8f64: 623 shared leaves, and only the three `seconds` fields differ. The changes are exactly the ones described:
     - six restored E18 prediction keys and their six source labels;
     - E19's FINDINGS.md:78 key string, replaced by the longer one. Its status is still CORRECTED.

     No other value or status changed, so the second-pass recompute (discrepancy 4.4e-16, floating point only) still covers every value.
   - The errata tests pass (37).

2. **Predictions line: OK.** It now shows both scorings, every E18 entry labelled "(harvest)":
   - Under the harvest's own definitions, 6 hits.
   - Under the pinned definitions, 6 misses: rep_below_half_amber_v3_arch, rep_below_half_zstd_arch_16384, zstd_arch_16384, zstd_arch_4096, zstd_arch_65536 and zstd_arch_none.
   - amber_v3_arch is a hit under both.
   - The restored values equal the third-batch entry's printed predictions (read from the protocol text). Each hit and miss checks out at the prediction's own precision. For example, 6.251 against the pinned 6.775 is a miss, and against the harvest-definition 6.251 a hit.

3. **Caveats sentence, source line and E19 bracket: OK.**
   - **Caveats.** It now reads "its escape costs are near-tie masses over all census positions of each model's dumps, as the census counted them". That is true: `mass_pct` is over 49,152 positions, and no insertion still says "kept positions".
   - **Source line.** It lists results/errata_dryruns/dry_b3b.json and results/p2_tinyllama_dumps.sha256.
   - **E19 bracket.** It says FINDINGS.md:78's CORRECTED rests "on E15's rank-only compensator z, a field added after the second batch's values were seen".
   - **Regime line.** It now names commit f492e68, tree a800d10 and protocol blob 4dd72905bc99, all verified against git.
   - **Scope of the change.** A word-level diff against the second-pass dry run shows changes in only those places: the regime line, the source line, the E19 bracket, the predictions line and the caveats sentence.

4. **Anything false in the F-16 block: no.**

RECOMPUTE DISCREPANCY 0, BLOCKING 0

There is nothing open that would change my mind on this pass. A status or value differing from bacc8f64 outside the prediction dict and the one key string would have; none does.

Script: results/errata_critic/c3c_check.py, which writes its output to c3c_check.out.json with LF line endings.

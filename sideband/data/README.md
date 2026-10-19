# data/ - committed prompt sets

Five committed prompt sets, rows `{prompt, family, topic}`, three families
(instruct / story / summarize). Every real-model number in the repo is
measured on one of them; the regime line of each finding names which.
Counts below are line counts of the committed files (870 lines in total).

| File | Rows | Generator | Used by |
|---|---|---|---|
| prompts.jsonl | 210 (70 / 70 / 70, 210 unique topics) | data/make_prompts.py | Phase 0 audits and steering (F-10..F-14); the S1/S3 harvests and the existence probes, split 150 / 30 / 30 prompt clusters by `sideband.harvest.split_of_prompt` (F-15..F-18) |
| prompts_k3_verdict.jsonl | 210 | none committed: authored and committed in 2db51aa (2026-09-01, "K-3 verdict prompt set committed BEFORE any D2/D3 output exists") as the only file in that commit; later generators use it only as a collision reference | K-3 Attempt #1 verdict runs at seeds 0 (voided) and 1 (F-19); the four vanilla byproduct runs that F-22 and F-23 consume include k3_verdict_arm1 and k3_verdict_s1_arm1 |
| prompts_oq15_val.jsonl | 30 (10 / 10 / 10) | data/make_prompts_oq15.py | OQ-15 Stage C threshold selection (oq15c_search_arm*, oq15c_val_arm1) |
| prompts_oq15_verdict.jsonl | 210 | data/make_prompts_oq15.py | OQ-15 Stage C verdict runs at seeds 2 (voided) and 3 (F-21); oq15c_verdict_arm1 and oq15c_verdict_s3_arm1 are the other two F-22 / F-23 byproduct runs |
| prompts_oq16_verdict.jsonl | 210 | data/make_prompts_oq16.py (mechanical refusal of any topic sharing two or more content words with, or contained in, the four committed sets) | Stage A verdict population (docs/BLUEPRINT.md STAGE-A FREEZE). No run exists: Stage A never ran (F-23) |

Rules that apply to every set (docs/ECONOMICS.md section 5, amendment 2):
a verdict population is authored and committed BEFORE any output that
could select it is read; the prompts are short and factual; generations
cap at 256 tokens. The K-3 set's authoring script was never committed,
which is disclosed here and in docs/DATA.md rather than reconstructed.

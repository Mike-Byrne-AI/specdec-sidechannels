# Runs

Tabular log of experiments / training runs / measurement campaigns. One row per run. Cross-reference `trellis-docs/trellis-findings.md` for narrative; this file is for at-a-glance comparison.

<!-- TODO: customize columns for your project's metrics. The starter columns below are placeholders. -->

## Columns

- **Run** — directory name in `outputs/`
- **Config** — key parameters; `default` if no overrides
- **Primary metric** — e.g., best val loss, final accuracy, validation AUROC
- **Notes** — what changed from previous run; one most important observation

## Runs

| Run | Config | Primary metric | Notes |
|---|---|---|---|
| run_001 | oss-preview-gate | passed locally | Source tests, source repair gate, and fresh-install release gate passed for the OSS preview revision. |
| run_002 | lockstep v0.1.0 lsp0 reference; CPython 3.12.3 Linux x86_64; stdlib only | 30/30 unittests; 6/6 vectors; ratios 1.87x prose / 3.63x repetitive / 0.93x random | First project run. Built integer coder+CDF+models+codec+container+CLI+envprobe; froze vectors_v0.json; measured drift-sponge boundary data (F-2) and throughput baseline ~32 KiB/s (F-1). |
| run_003 | review pass on v0.1.0; container hardening + cost model | 42/42 unittests; all Trellis gates green | Adversarial review: hardened manifest parser (F-3, D-11, +test_manifest), added cost model (F-4), review/ideas + why-this-dies docs, lockstep-critic agent, TP-6. Cost model flags the business case as the top risk. |
| run_004 | cross-finding synthesis; no new experiments (analysis only, TOTAL_MAX patched in-probe) | 4 new findings (F-5..F-8), 3 decisions, 2 OQs closed, TP-1/TP-2 blocked | Emergent pass: F-5 coder ceiling forbids LLM vocabs (2^16 vs 128k; constant conservative, verified to 2^30); F-6 drift sponge doesn't scale (no grid both absorbs and preserves ratio); F-7 logit-space+top-k restores sparse corrections, law rate~k*eps/delta measured 0.67% vs 0.64% predicted; F-8 pack = 92% of TCO, needs 100-500x, wins only as free byproduct. Added profile advisor + E-006. |
| run_005 | unified lsp0 v0.2.0; CPython 3.13.5 Linux x86_64; source + clean wheel | 82/82 product tests + 39 subtests; 6/6 vectors; 115/115 runnable Trellis tests; repair gate passed | Unified the synthesis superset without changing lsp0 bytes; enforced complete model pins (F-9), hardened parser/types/resources and atomic streaming I/O, added packaging and deterministic fuzzing, and invalidated the inherited all-green maintenance claim (F-10). |
| run_006 | first sibling-dependency use (amber); Windows 11 Pro 10.0.26200, CPython MSVC build; editable install of the v0.2.0 snapshot; no source changes | 82/82 product tests; 6/6 vectors reproduced (`lockstep self-check`); envprobe 2d2a2e0c… | Repo re-created from lockstep-ultimate-repo.zip (sha256 41677661…) under git; F-11 records the first independent-OS vector reproduction; D-15 records the amber dependency and the shared E-006 census. |
| run_007 | E-006 first evidence via amber Phase 2: TinyLlama-1.1B top-64 logits, CPU fp32 vs 3080 Ti fp32/bf16/fp16/int8/nf4, 49,152 positions | fp32 eps p50 3e-6 / max 1.3e-4; crossing 2.6% / 21.9% / 90.8% at delta 1e-2/1e-3/1e-4 (k=64); bf16/fp16 100% | Measured, not projected: D-13's delta=1e-3 default is not sparse on this pair; law k*eps/delta confirmed; rank order exactly stable at fp32 (amber F-5). See F-12. |
| run_008 | E-006 second datapoint via amber Phase 2: Llama-3.2-1B-Instruct (V=128256) top-64 logits, CPU fp32 vs 3080 Ti arms, 49,152 positions | fp32 eps p50 7e-6 / max 4.5e-4; crossing 5.0% / 40.8% / 99.4% at delta 1e-2/1e-3/1e-4 (k=64); bf16/fp16 100% | Same shape as run_007 on the target vocabulary regime; law holds (45% predicted vs 41%); delta=1e-2 is the first two-point candidate profile constant. See F-13. |
| run_009 | amber Phase 1 via this repo's cost lens: Llama-3.2-3B greedy generation + 1B draft replay, 48,958 tokens, 3080 Ti bf16 | gen 32.8 tok/s; draft replay 9,233 tok/s; archive 0.474 bits/token vs zstd 3.62 | First measured pack-side throughput for the byproduct regime; F-8's placeholder was 10-20x too pessimistic on pack speed and 12x on ratio for this content. See F-14. |
| run_010 | amber P3/P2b via this repo: rac coder on the P1 stream (49k target-generated tokens) + cross-arm order-stability at depth on run_008 dumps (top-256, 49,056 positions) | rac1 0.417 vs gamma 0.421 bits/token (held-out); fp32->fp32 0 desyncs to rank 64; fp16 5.1% / bf16 23-26% of rank-2..64 corrections mis-resolve; top-1 escapes remove all A-desyncs at 2tau | First production use of rac; rank stability has a depth axis that top-1 censuses miss; the determinism ask for rank codecs is an fp32 dtype pin. See F-15. |
| run_011 | amber P4: real hf archives, Llama-3.2-1B fp32 teacher-forced encode, draft-only incremental KV decode under cuda fp32/bf16/fp16 + cpu fp32 (200 archives, 48,958 tokens) | fp32 200/200 + 24/24 byte-exact; bf16 84% archive failure; fp16 28.5%; payload 0.44 bits/token, header 551 B/archive | The fp32 dtype pin is the whole determinism ask for rank archives, measured end-to-end across device and kernel path. See F-16. |

## Reading the table

<!-- TODO: project-specific heuristics. Examples: -->
<!-- - Best metric << final metric = overfit; use best for downstream eval. -->
<!-- - Metric near baseline = system can't yet detect the signal we want. -->

## When adding a row

After each run, append a row. Required:
- All non-`n/a` columns filled
- "Notes" column states what changed since the previous run AND the one most important observation

## Linked findings

| Finding | First observed in | Verified in |
|---|---|---|
| F-1 | run_002 | run_006 (independent OS/interpreter reproduces all 6 vectors; F-11) |
| F-2 | run_002 | (pending E-001 on real logits) |
| F-3 | run_003 | run_003 (fix verified in-suite) |
| F-4 | run_003 | run_004 (re-priced against D-10; superseded by F-8) |
| F-5 | run_004 | (coder ceiling verified in-probe to 2^30) |
| F-6 | run_004 | run_007 (bf16/fp16 cross a grid at 100% of positions; F-12) |
| F-7 | run_004 | run_007 (law matches measured eps on real logits at delta 1e-2/1e-3; F-12) |
| F-8 | run_004 | run_009 (pack throughput measured on one consumer GPU; F-14; OQ-13 conversation still pending) |
| F-9 | run_005 | run_005 (three forged fields rejected in-suite) |
| F-10 | run_005 | run_005 (source, maintenance, repair, fuzz, and clean-wheel gates) |
| F-11 | run_006 | run_006 (self-check on Windows/CPython) |
| F-12 | run_007 | (one CPU/GPU pair; cross-architecture pending) |
| F-13 | run_008 | (second model, same box; cross-architecture pending) |
| F-14 | run_009 | (one GPU, batch-1 generation; batched pack term pending) |
| F-15 | run_010 | run_011 (per-rank predictions landed in band on real archives; F-16); qualified by F-20: that comparison crossed escape regimes, and the rank-only top-1 rate did not transfer |
| F-16 | run_011 | run_011b (amber F-12: 200/200 fp32-exact again with prompt segments decoded — real-text C ranks to 64 and 27% raw-X — at 72 tok/s) |

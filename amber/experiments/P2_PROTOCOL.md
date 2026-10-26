# P2 — Rank-stability census protocol (pre-registration)

Frozen 2026-08-29 before any capture. Provenance: lockstep E-006 (drift census
shape, burstiness stop condition), cross-research XB-3 (calibrated tolerance,
near-tie attribution, batch invariance, discrete invariants never toleranced),
tokenizer-lab F31→F33 (pipeline nondeterminism masquerading as kernel
nondeterminism). Nothing below may be changed after the first shard is written;
if it must be, that is a new protocol file with a new date.

## Question
On this hardware, how often does the draft's token ORDER (top-1, top-k set,
top-k order) differ between numeric arms — and is every difference a near-tie?
Amber's codec needs order stability of the draft (D-5, F-2), nothing stronger.

## Setup
- Model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (Llama architecture, 22 layers,
  vocab 32000; HF snapshot hash recorded). Intended: `meta-llama/Llama-3.2-1B-Instruct`
  — the box's HF account is not authorized for the gated Llama-3.2 repos as of
  2026-08-29 (weights never downloaded). Phase 2 asks a HARDWARE question about
  a Llama-architecture ~1B draft, so TinyLlama answers it in-regime; the finding
  will carry the model in its regime tag and be re-run on 3.2-1B when access
  lands (same command, `--model`). Phase 1 needs the tokenizer-matched pair
  (3.1-8B target is cached; 3.2-1B draft is not) — access request is the
  blocker there, not compute.
- Corpus: 96 non-overlapping windows × 512 tokens (BOS + 511) from
  `tokenizer-lab/data/mix_docs50_wiki50.txt`, seeded selection, sha256 pinned in
  `results/p2/corpus.json`. 49,152 positions. NO padding anywhere.
- Dump: top-256 (value, index) per position, fp32 after upcast; census at k=64.
- The int8 arm uses bitsandbytes LLM.int8; nf4 uses double-quant nf4 with fp16 compute.
- Arms (reference first): `cpu_fp32`; `cpu_fp32_rep` (run-to-run);
  `cuda_fp32_b1`; `cuda_bf16_b1`; `cuda_bf16_b1_rep`; `cuda_bf16_b8`;
  `cuda_fp16_b1`; `cuda_int8_b1`; `cuda_nf4_b1`.
- Throughput per shard is recorded; it is a measurement, not a projection.

## Metrics (all from `amber.rankcensus.rank_census_topk`)
- top-1 flip rate; top-k SET and ORDER flip rates for k ∈ {1, 2, 8, 64}.
- τ per ARM = 99.9th percentile of that arm's own aligned |Δlogit| vs the
  reference. Threshold 2τ. `flips_beyond_2tau` counts top-1 flips whose
  reference gap exceeds 2τ — flips the arm's observed perturbation cannot
  explain. (Amended 2026-08-29 before any real capture: the smoke run showed
  run-to-run and batch repeats bit-identical on this box, so a repeat-derived
  τ is 0 and degenerate.)
- Determinism checks, each expected BIT-IDENTICAL (max |Δ| = 0, zero order
  flips at k=64): `cpu_fp32` vs `cpu_fp32_rep`; `cuda_bf16_b1` vs
  `cuda_bf16_b1_rep`; `cuda_bf16_b1` vs `cuda_bf16_b8` (batch invariance).
  Any nonzero top-1 flip in a determinism check ⇒ band (c).
- Burstiness: dispersion index of per-sequence flip counts; longest flip run.
- Batch invariance: `cuda_bf16_b1` vs `cuda_bf16_b8`, same τ.
- Spread: metrics per sequence-half.

## Bands (complementary; no dead zone)
- Deciding arms: `cuda_fp32_b1`, `cuda_bf16_b1`, `cuda_fp16_b1`.
- **(a) contract near-free**: every deciding arm has top-1 flip rate
  < 1e-3 AND `flips_beyond_2tau == 0`. → D-5's ask of lockstep is cheap; K-3
  retreats; proceed to Phase 1 with the rank codec unchanged.
- **(b) near-tie escape needed**: some arm ≥ 1e-3 but every flip within 2τ.
  → the codec gets a near-tie escape symbol (gap-below-threshold positions are
  coded explicitly). Format change; decide BEFORE Phase 1 freezes rates.
- **(c) pipeline bug first**: any `flips_beyond_2tau > 0`. → do not interpret
  drift; find the bug (alignment, tokenizer, dtype of the upcast, RNG coupling)
  and re-run. A wide-gap flip is never "hardware".
- Any determinism check with a top-1 flip → band (c) regardless of the above.
- Dispersion index > 3 on any arm → recorded as its own finding: bursty drift
  means a run-length correction format, not a tuning problem.
- int8/nf4 arms are expected to sit in (b) (quantization is a real
  perturbation, [probable]); they are reported but do NOT decide the band —
  the band is about the bf16/fp16/fp32 arms the archive-compatible decoder
  would actually run. If int8/nf4 land in (a), that is a bonus finding.

## Stop conditions
- Any arm's dump has non-finite values → capture refuses to write; investigate.
- Corpus sha mismatch between arms → census refuses to run.
- τ cannot be calibrated (repeat arm missing) → report without band.

## Commands
```
python -m amber.real.capture corpus --text ../tokenizer-lab/data/mix_docs50_wiki50.txt
python -m amber.real.capture run --arm cpu_fp32 --arm cpu_fp32_rep
python -m amber.real.capture run --arm cuda_bf16_b1 --arm cuda_bf16_b1_rep --arm cuda_bf16_b8 --arm cuda_fp16_b1 --arm cuda_fp32_b1
python -m amber.real.capture run --arm cuda_int8_b1 --arm cuda_nf4_b1
python -m amber.real.capture status
python experiments/p2_rank_census.py
```
Every `run` is resumable: rerun the same command after an interruption.

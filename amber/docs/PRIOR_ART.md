# Prior Art Map (seeded from the sideband v0.2.1 dive; re-verify before citing)

- **LLM arithmetic-coding lineage** — LLMZip, llama-zip, nncp/ts_zip,
  "Language Modeling is Compression". Rate-optimal with the model; requires
  the SAME model at decode. Amber's regime-B baseline (D-6) and the thing
  regime A's asymmetry is defined against.
- [withheld: a patent entry: its number and the claim reading (plan 10.3; 15.1 call 2); see WITHHELD.md]
  > Dated note (2026-10-18): the claim reading in the entry above was withdrawn on
  > sideband's prior-art map (sideband docs/PRIOR_ART.md, its dated note of
  > 2026-10-11 under the v0.2.1 section: a textual reading of the claims, not legal
  > advice). K-1 stands as structure; the entry's wording stands as written, with
  > this note beside it.
- **PMATIC** (arXiv 2601.17684) — formalizes prediction mismatch in
  model-driven compression; tolerates bounded drift. The
  tolerate-vs-eliminate alternative to lockstep; also the reason the
  arithmetic-coder upgrade is gated (BLUEPRINT).
> Erratum (2026-10-10; F-14 row E13): E13: PMATIC is arXiv 2601.10678, "Synchronizing Probabilities in Model-Driven Lossless Compression" (Adler, Aviv; Tang, Jennifer; page sha256 a1ee3e4a2e0e); the cited id is arXiv 2601.17684, "A Model-Driven Lossless Compression Algorithm Resistant to Mismatch" (Hu, Cordelia; Tang, Jennifer; page sha256 b227437a106e), a different paper that is relevant prior art in its own right (re-identify the citation, do not remove it); pages saved under results/errata_web/.
- **Speculative KV coding** (Doubleword) — predictor-model-driven arithmetic
  coder, explicit spec-decode analogy, SYMMETRIC (predictor both sides), on
  KV caches not token streams. Nearest technical neighbor.
- **Speculative decoding** (Leviathan/Chen) — the verifier math amber's
  sampling-mode (OQ-3) inherits via sideband's tested core.
- **sideband F-9 / e07** — the hint-rate budget (~0.16 bits/token in that
  regime; dense hints lose 20:1) that constrains OQ-4.

## v0.2 additions (lockstep import, 2026-08-29)
- **Lockstep PA-3 — hybrid-neural archival feasibility** (arXiv 2603.25526)
  — names nondeterministic hardware + compute cost as the two blockers;
  proposes logit quantization for bit-exact reproducibility ("GPU butterfly
  effect", ~1e-7 drift). Lockstep F-6/F-7 arrived at the same logit-space
  top-k design by elimination; amber's rank codec needs strictly less
  (order, not grid position).
- **Lockstep PA-7 — reproducible learning-based compression** (arXiv
  2410.09872) — cross-GPU decode failure (A100-encoded stream failing on
  H100); safeguard bitstream. Amber's corrections ARE a safeguard stream
  against the target, so the rank-flip census (OQ-2) is where its size vs
  the draft's own drift gets measured.
- **Lockstep PA-10 — batch-invariant kernels** (Thinking Machines, 2025) —
  determinism purchasable at ~60% throughput cost. The price K-3 compares
  against.
- [withheld: two patent entries (integer-network entropy models): numbers and the counsel gate (plan 10.3; 15.1 call 2); see WITHHELD.md]

## 2026-10-18 additions (the cold read of that date; each entry fetched and read on 2026-10-18)
- **LLMZip** (arXiv 2306.04050; Valmeekam et al., 2023), named in the lineage
  line above without its method: by the paper's own section titles its encoding
  schemes are compressing the ranks with zlib, token-by-token compression, and
  arithmetic coding, so amber's rank code sits inside a published lineage rather
  than beside it.
- **LLM-based source code compression via thresholded symbol ranking** (arXiv
  2607.24192; Nardone and Ferragina, 2026): for source code, LLM-predicted symbol
  ranks limited to a small top-T window with out-of-window symbols stored
  separately, reported to beat earlier LLM-based methods on ratio and throughput
  and zstd and bzip2 on ratio; the nearest published relative of amber's
  max_rank 64 with its X class, on a different corpus.
- **Numerical sources of nondeterminism in LLM inference** (arXiv 2506.09501;
  Yuan et al., 2025): under bf16 greedy decoding, GPU count, GPU type or batch
  size shift a reasoning model's accuracy by up to 9%; proposes LayerCast (16-bit
  weights, FP32 compute). A published measurement of bf16 greedy nondeterminism
  across GPU type, count and batch, beside the cross-dtype rates F-10 and F-11
  measure.
- **Lossless compression of LLM-generated text** (arXiv 2505.06297; Mao et al.,
  2025): an LLM's own outputs are highly predictable to it, over 20x compression
  against about 3x for Gzip. **Haiku to Opus in Just 10 bits** (arXiv 2604.02343;
  Rinberg et al., 2026): compressing LLM-generated text with domain-adapted
  adapters, and a small model querying a stronger one. Both are the setting F-8
  measures, model-generated text coded under a model; neither was cited before.
- **ts_zip (Bellard)**, in the lineage line above for ratio only: its page states
  "The model is evaluated in a deterministic and reproducible way. Hence the
  result does not depend on the exact GPU or CPU model nor on the number of
  configured threads." and "The model is quantized to 8 bits per parameter and
  evaluated using BF16 floating point numbers." (bellard.org/ts_zip, fetched
  2026-10-18). Bears on a same-dtype bf16 contract, which F-11 did not measure (its
  two dated notes of the same day: F-11's rates are cross-dtype, fp32-encoded
  archives decoded at bf16 or fp16), and on the determinism price K-3 compares
  against.

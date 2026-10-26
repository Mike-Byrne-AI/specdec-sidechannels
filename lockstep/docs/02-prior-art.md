# Prior art and adjacent work

Read this before designing anything; cite entries by tag (PA-n) in
decisions and packs. Links were live as of 2026-07; re-verify before
external use.

## LLM-as-compressor

- **PA-1 llama-zip** (github.com/AlexBuz/llama-zip) — OSS utility using a
  user-supplied LLM as the probability model for an arithmetic coder;
  sliding window for arbitrary length; binary via UTF-8 private-use
  escape. Strong ratios on text. No determinism story — the gap we fill.
- **PA-2 Llamazip** (arXiv:2511.17589) — LLaMA3-based lossless text
  compression storing only mispredicted tokens; explicitly positions the
  speed-for-ratio trade as archival; doubles as training-set membership
  probe (interesting side-capability for provenance).
- **PA-3 Hybrid-neural archival feasibility** (arXiv:2603.25526) — names
  the two blockers: nondeterministic hardware and compute cost; proposes
  logit quantization into a discrete probability space for bit-exact
  reproducibility; visualizes the "GPU butterfly effect" (parallel vs
  serial kernels drifting ~1e-7 and diverging the coder). Closest to our
  thesis; validates it independently.
- **PA-4 NNCP / ts_zip (Bellard)** — practical demonstrations that
  NN/LLM probability models + arithmetic coding win on ratio at severe
  speed cost. Long-standing existence proofs.
  - Dated note (2026-10-18): ts_zip also ships the determinism this record
    treated as unsolved (docs/01 item 2, docs/04 item 1, F-16). Its page states:
    "The model is evaluated in a deterministic and reproducible way. Hence the
    result does not depend on the exact GPU or CPU model nor on the number of
    configured threads." and "The model is quantized to 8 bits per parameter
    and evaluated using BF16 floating point numbers." (bellard.org/ts_zip,
    fetched 2026-10-18; its stated speed is "up to 1 MB/s on a RTX 4090").
    PA-4 above cites it for ratio only. The claim bears on F-16's bf16
    sentence (see F-16's dated note) and on the premise that bf16 model
    evaluation cannot be made reproducible across hardware; how ts_zip
    achieves it is not described on that page and was not examined here.
- **PA-5 "Language Modeling Is Compression"** (arXiv:2309.10668) — the
  conceptual frame: LLMs are general-purpose compressors; scaling laws
  viewed through compression.
- **PA-6 Hutter Prize / CMIX / PAQ family** — the ratio frontier for
  text and the culture of exact reproducibility budgets (time/memory
  limits) we should emulate in conformance.

## Determinism and reproducible inference

- **PA-7 Reproducible learning-based compression** (arXiv:2410.09872) —
  documents cross-GPU decode failure (stream encoded on A100 failing on
  H100); proposes quantizing critical-module outputs plus a *safeguard
  bitstream* so a decoder within an error bound reproduces exact values.
  Blueprint for our TP-2 side-stream.
- **PA-8 Quantized decoder for learned image compression**
  (arXiv:2312.11209) — decoder-only integer quantization achieves
  bit-exact output; ~0.5% rate loss at 16-bit weights/activations, ~7.9%
  at 8-bit. Cost-of-determinism datapoint.
- **PA-9 Integer networks for data compression** (Ballé et al., ICLR
  2019) — the original "make the entropy-model network integer so
  encoder and decoder agree" result. Foundational; also see PA-13.
- **PA-10 Batch-invariant kernels** (Thinking Machines, 2025 writeups) —
  temp=0 LLMs are nondeterministic under batching; batch-invariant
  norm/matmul/attention kernels achieve exact repeatability at roughly
  60% throughput cost. Determinism is purchasable; price is real.

[withheld: the section of adjacent market signals, entries PA-11 and PA-12 (the operator's call 3 of 2026-10-18, plan 15.6); see WITHHELD.md]

## Patents flagged (details in 03-patent-and-licensing-notes.md) [withheld: 03-patent-and-licensing-notes.md not in this repository; see WITHHELD.md]

- **PA-13** [withheld: two patent numbers and their claim reading (plan 10.3; 15.1 call 2's shape, 15.6); see WITHHELD.md] Directly adjacent
  to the "make the net integer" strategy. Design-space consequence:
  prefer the safeguard-stream architecture (PA-7) and treat
  integer-network entropy models as requiring counsel review (TP-5).

[withheld: the closing paragraph on what no listed work ships (the operator's call 3 of 2026-10-18, plan 15.6); see WITHHELD.md]

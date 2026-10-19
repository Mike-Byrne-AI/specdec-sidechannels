# Nondeterminism taxonomy

Every cross-machine decode failure has a cause in one of these classes.
The design column says which Lockstep mechanism neutralizes it. Keep
this table current; it is the project's threat model.

| # | Class | Mechanism | Example | Lockstep answer |
|---|-------|-----------|---------|-----------------|
| N1 | FP reduction order | Floating-point addition is non-associative; parallel reductions change grouping | Same matmul, different logits across GPU archs (~1e-7 drift reported in the literature) | No floats in the trust base (D-7); for lsp1, quantized logits + safeguard stream (TP-2) |
| N2 | Batch variance | Kernel strategy changes with batch size, changing reduction order | temp=0 LLM APIs returning different outputs under load; batch-invariant kernels fix it at ~60% throughput cost | Decode profile pins batch=1 semantics; adapter must be batch-invariant or integer |
| N3 | Kernel/library selection | cuDNN autotune, cuBLAS heuristics, framework version pick different kernels run-to-run or install-to-install | "Same code, same GPU, different build" mismatches | Profile pins runtime identity; envprobe diffs machines; conformance gates every runtime |
| N4 | Transcendental libm drift | exp/log/tanh differ by ulps across libm implementations and ISAs | softmax on CPU A ≠ softmax on CPU B | envprobe captures exact float bits of canary calls; lsp1 specifies integer/fixed-point softmax or table-based exp |
| N5 | Quantization ambiguity | "int8 model" underspecifies rounding modes, accumulators, dequant order | Two int8 runtimes, two outputs | Decode profile specifies the arithmetic, not the intent; vectors enforce it |
| N6 | Tokenizer drift | Normalization, merges, special-token handling differ across versions | Same text, different token ids → different model states | Container pins tokenizer hash; v0 sidesteps via raw-byte alphabet |
| N7 | Sampling/state leakage | RNG, KV-cache reuse, context-window policy differences | "Deterministic" decode that depends on server state | Profile defines exact context policy; reference models are pure functions of history |
| N8 | Software entropy over years | Deps rot, formats drift, hardware dies | The 20-year archive problem | Stdlib-only reference impl; spec-first format; model pinned by content hash, stored alongside archives |

## Design consequences

1. **Two trust tiers.** The v0 trust base (coder, integer quantizer,
   container) must be immune to N1–N5 *by construction* — hence
   integer-only. The lsp1 model surface is where N1–N7 live; it gets the
   grid, the safeguard stream, and conformance instead of hope.
2. **The grid is a drift sponge, not a guarantee.** Quantizing
   probabilities to a 2^15 grid absorbs drift below ~half a grid step
   (measured: F-2). Drift above it must be caught (payload/original
   hashes) and corrected (safeguard stream, TP-2) — never silently
   tolerated. Dated note (2026-10-18): the measured boundary is far below
   half a step; F-21 (an erratum to F-2) gives the figures.
3. **Loud failure taxonomy.** container.py distinguishes "stream
   damaged" from "decoder desynced". N-class debugging starts from that
   split plus an envprobe diff.

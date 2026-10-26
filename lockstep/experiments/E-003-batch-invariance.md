# E-003 — Batch-invariance audit

## Question
Which candidate runtimes give identical logits for identical positions
regardless of batch size / concurrent load?

## Why
N2 in the taxonomy. PA-10 showed serving-stack nondeterminism at temp=0
and fixed it with batch-invariant kernels at ~60% throughput cost.
Archival decode can simply pin batch=1 — but we must PROVE batch=1 is
actually invariant on each runtime we bless, and measure what
invariance costs if a user wants throughput.

## Procedure
1. For each runtime (llama.cpp CPU, llama.cpp CUDA, candidate
   batch-invariant kernel stack): run the E-001 corpus at batch sizes
   {1, 2, 8, mixed-load} × 5 repeats.
2. Hash the logit stream per position; count positions with any
   variation across repeats/batches.
3. Throughput table alongside.

## Outputs
Per-runtime verdict: {invariant at batch=1, invariant always, variant};
tokens/sec at each setting. Feeds the lsp1 "blessed runtimes" list.

## Stop conditions
Stop if NO runtime is invariant even at batch=1 on GPU — lsp1 decode
becomes CPU-only until that changes (would confirm D-10's bet).

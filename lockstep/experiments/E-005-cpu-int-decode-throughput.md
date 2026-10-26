# E-005 — CPU integer decode throughput ceiling

## Question
How fast can a ported (C/Rust) Tier-0 coder + int8 model surface decode
on commodity CPUs, verified against the same conformance vectors?

## Why
D-10 bets on CPU-first decode for archives (sidesteps N1–N3 entirely).
The bet dies if realistic throughput can't reach ~single-digit MB/s per
core for lsp1-class models — restore-time SLAs exist.

## Procedure
1. Port rac.py to C (or Rust) mechanically; MUST pass vectors_v0.json
   before any optimization.
2. Micro-bench coder alone (uniform + adaptive-order1) per core.
3. With TP-1 adapter: measure end-to-end decode tokens/sec on int8
   CPU inference (llama.cpp), 1/4/8 threads; project archive restore
   time for 1GB and 100GB corpora.

## Outputs
Throughput table + restore-time projection; Finding stating whether
CPU-first survives contact with the numbers.

## Stop conditions
Stop (and rethink product posture, OQ-8/9) if projected 100GB restore
exceeds 24h on an 8-core box at the chosen model size.

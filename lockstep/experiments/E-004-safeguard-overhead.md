# E-004 — Safeguard-stream overhead vs drift rate

## Question
Given measured drift (E-001) and chosen grid (E-002), what does the
PA-7-style correction side-stream cost in bytes, and does it restore
bit-exact decode across every device pair?

## Procedure
1. Implement TP-2's encoder mode that emits correction records for
   positions whose probability sits within a guard band of a cell edge.
2. Sweep guard-band width; measure side-stream size as % of payload and
   end-to-end cross-device decode success over the E-001 device set.
3. Adversarial pass: inject synthetic drift at 2×, 10× measured p99 and
   confirm graceful behavior (loud desync, never silent corruption).

## Outputs
Curve: guard band → (overhead %, success rate). Target: 100% success at
<2% overhead. Finding + lsp2 profile draft numbers.

## Stop conditions
Stop if 100% success needs >10% overhead — architecture review (per-
block checkpoints, OQ-7 alternative) before more tuning.

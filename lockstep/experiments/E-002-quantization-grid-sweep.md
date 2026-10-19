# E-002 — Grid resolution sweep

## Question
Compression-ratio cost of coarser probability grids (2^12..2^16) vs
their drift absorption, on real text through the lsp1 adapter.

## Why
The grid is the primary drift sponge (F-2 shows the mechanism on
synthetic distributions). Coarser grid = more absorption + more ratio
loss. Find the knee.

## Procedure
1. Fix corpus (enwik-style 1MB slice + code + logs; hashes recorded).
2. For total in {2^12, 2^13, 2^14, 2^15, 2^16}: encode via adapter with
   quantize_probs at that total; record ratio and, using E-001's logit
   dumps, the fraction of positions where cross-device drift would have
   crossed a cell boundary.
3. Plot ratio-vs-absorption; pick lsp1 default; record decision.

## Outputs
Run rows + a Finding naming the chosen grid with both numbers attached.

## Stop conditions
Stop if ratio loss at the smallest drift-safe grid exceeds 15% vs
float baseline — that resurrects the integer-softmax path (OQ-4) and
needs a design session, not a bigger sweep.

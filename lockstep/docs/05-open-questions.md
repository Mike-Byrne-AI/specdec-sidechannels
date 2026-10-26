# Open questions

Living list. Promote an answer to a Finding (empirical) or a Decision
(architectural) when it firms up; strike it here with a pointer.

## Format & spec

- OQ-1 Chunking: fixed-size blocks with per-chunk coder reset (enables
  seek + parallel decode + bounded desync blast radius) vs single
  stream (best ratio). Likely both, profile-flagged. → TP-3.
- OQ-2 Should the container optionally *embed* the model (self-contained
  archive) vs pin-by-hash only? Embedding trades size for the 20-year
  problem (N8). Licensing interacts (patent doc §3).
- OQ-3 Multi-file archives: tar-then-pack vs native file table. Lean
  tar-then-pack for v0 simplicity.

## lsp1 (LLM profile)

- ~~OQ-4 Where exactly to place the grid: logits vs probabilities?~~
  **CLOSED by F-6/F-7 (D-13): it must be logit space with top-k.** No
  probability-space grid both absorbs drift and preserves ratio at LLM
  vocabulary — the windows do not overlap. Answered by elimination, not
  preference.
- OQ-5 Context policy: fixed window with documented truncation vs
  sliding with overlap (PA-1 style). Sliding reintroduces state — must
  be specified to the token.
- OQ-6 Tokenizer: byte-level fallback keeps the alphabet honest (N6);
  what ratio do we sacrifice vs full tokenizer pinning?
- OQ-7 Safeguard record design: position-indexed corrections vs
  per-block checkpoint hashes with re-sync protocol. Overhead vs
  recovery power. → E-004.

## Product & positioning

- OQ-8 What corpus size / access pattern makes LLM archival beat
  zstd -19 on TCO, including GPU-hours to pack? Need a real cost model
  with measured throughputs, not vibes.
- OQ-9 [withheld: a question on the first users of a commercial offering (the operator's call 3 of 2026-10-18, plan 15.6); see WITHHELD.md]
- OQ-10 [withheld: a question on what an open specification leaves to a commercial runtime (the operator's call 3 of 2026-10-18, plan 15.6); see WITHHELD.md]
- ~~OQ-11 Manifest overhead / compact binary header?~~ **CLOSED by
  F-4+F-8 (EF-5): no.** The economics exclude the small-input regime
  entirely, so the ~457 B floor never binds. Revisit only if chunking
  (TP-3) makes per-chunk metadata a material fraction.
- OQ-12 Does real LLM logit drift sit at PA-3's ~1e-7, and is it
  independent across positions or correlated? F-7's law and every lsp1
  constant are keyed to that number; correlation makes corrections
  bursty rather than Poisson. → E-006, the highest-value measurement
  left in the project.
- OQ-13 Is there a real population running full-corpus inference AND
  retaining that corpus long enough for archival economics to matter
  (D-14's byproduct bet)? If not, the cost thesis is dead in every
  regime and only the attestation framing survives. Cheapest experiment
  in the project: a conversation.
- OQ-14 Does lsp1 want CODE_BITS=64? F-5 leaves only ~3 bits of headroom
  at CODE_BITS=32 once PROB_BITS_MAX reaches ~27. What does 64-bit cost
  a future C/Rust port?

## Risks we are consciously carrying

- Pure-Python throughput makes big-corpus experiments annoying before
  the C port (mitigate: small corpora, honest extrapolation).
- Patent posture rests on a non-lawyer's reading until TP-5 closes.
- Working name may collide (D-6) — do not print stickers yet.

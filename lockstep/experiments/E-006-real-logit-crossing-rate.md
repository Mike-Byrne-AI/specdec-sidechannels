# E-006 — Real-logit boundary-crossing rate (the number lsp1 rests on)

## Question
On real hardware and a real model, what fraction of tokens have at least one
top-k logit cross a quantization boundary under cross-device drift — and does
it follow F-7's law, rate ~ k * eps / delta?

## Why
F-6 killed the probability-space grid; F-7's logit-space design replaces it,
and every lsp1 constant (delta, k, safeguard sizing, D-13) is keyed to a drift
magnitude taken from PA-3's paper (~1e-7), not from our hardware. This is now
the highest-value measurement in the project: it sizes the side-stream, sets
the profile, and either validates or destroys D-13. It supersedes E-001's
framing, whose stop threshold was computed against a 2^15 probability grid that
F-5 proves lsp1 can never use.

## Setup
- Model: one small open-weight gguf (1–3B, Q8_0), weights sha256 recorded.
- Devices: >=2 distinct (ideally CPU + two GPU architectures).
- Corpus: teacher-forced token sequences from a recorded DRBG seed, >=50k
  positions, so both devices evaluate identical inputs.
- Record `python -m lockstep env` digest per device.

## Procedure
1. Dump raw per-position logits on each device (capture hook, TP-4).
2. Pairwise: compute per-logit drift distribution (max/p99/mean), restricted
   to the top-k survivors — the tail is irrelevant under D-13.
3. For delta in {1e-2, 1e-3, 1e-4} and k in {32, 64, 256}: count positions
   where the quantized top-k tuple set differs between devices. That count IS
   the correction rate the safeguard stream must carry.
4. Compare measured rate to k*eps/delta using the measured eps. Report the
   ratio; a large discrepancy means drift is correlated, not independent.
5. Check burstiness: are crossings Poisson-scattered or clustered by position?
   Clustering changes side-stream framing (run-length vs position-delta).

## Outputs
- Table: (device pair, delta, k) -> correction rate, measured vs predicted.
- The chosen lsp1 (delta, k) with both numbers attached; feeds D-13 and TP-2.
- Finding recording measured drift magnitude and whether F-7's law holds.

## Stop conditions
- Stop if measured drift exceeds ~1e-5: at that magnitude no delta keeps
  corrections sparse without destroying ratio, and D-13 needs a rethink
  (integer softmax over the top-k, or CPU-only packing).
- Stop if crossings are strongly correlated across positions — record it as a
  finding first; bursty corrections are a different wire format, not a tuning
  problem.
- Do NOT tune delta to make the number look good. The rate is the measurement.

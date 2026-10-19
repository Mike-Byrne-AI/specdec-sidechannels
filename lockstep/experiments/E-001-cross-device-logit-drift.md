# E-001 — Cross-device logit drift census

## Question
For a pinned quantized model (llama.cpp, fixed build, fixed weights
hash), how large is per-token logit drift across devices, and where
does it sit relative to the lsp grid step?

## Why
Everything in TP-2 sizes itself off this number. PA-3/PA-7 report ~1e-7
class drift for parallel-vs-serial kernels; we need OUR distribution on
OUR candidate runtime, not the literature's.

## Setup
- Model: one small open-weight model (e.g. a 1–3B Q8_0 gguf), weights
  sha256 recorded.
- Runtime: llama.cpp pinned commit, built with default flags per
  platform; record build info + `python -m lockstep env` digest.
- Devices: minimum three of {desktop dGPU, laptop iGPU, CPU-only,
  cloud A-class, cloud H-class}.
- Corpus: 32 prompts x 512 tokens, teacher-forced from
  drbg-derived text (seed recorded) so every device evaluates
  identical token sequences.

## Procedure
1. On each device, dump raw float logits per position (llama.cpp
   `--logits-all` style path or adapter hook) to disk.
2. Pairwise diff across devices: max/mean abs drift per position, per
   layer-temperature (logit magnitude buckets).
3. Convert to probability-space drift post-softmax; histogram against
   the lsp grid step (~3.05e-5 at 2^15 with 128-symbol slices; compute
   for the real vocab size).

## Outputs
- `outputs/e001/<device>/logits.npz` + fingerprint json per device.
- Table: device-pair × {max, p99, mean} drift.
- Finding: "grid at 2^k absorbs {yes/no/fraction} of observed drift."

## Stop conditions
- Stop and record if any device pair shows drift ABOVE half a grid step
  at 2^15 for >0.1% of positions — that changes TP-2's design (safeguard
  stream stops being optional).

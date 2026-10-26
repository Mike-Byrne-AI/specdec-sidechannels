# P7 — Long-horizon archives + TRUE multi-turn sessions — pre-registration

Frozen 2026-08-30 before any long-horizon or multi-turn token was generated.
Withdrawn (2026-10-10; F-14 row E14): no stage of the P7 pre-registration ran (results/p7 on disk: false; tracked files: 0) and none will; the pre-registration stands as frozen text, withdrawn.
Provenance: F-8 (divergence front-loaded 15% -> 1.8% over a 256-token
horizon; its caveat: the cap truncates the curve exactly where it is
cheapest), F-12/D-10 (rate law 917/L + 0.455 extrapolated from L=245),
F-13/D-11 (shared-context coding loses on independently-generated turns;
the sign test on TRUE multi-turn data was explicitly deferred to this run),
D-6 (four-baseline tables), D-8 (fp32 contract, gamma, max_rank 64).

## Questions
A. What does the payload rate do at L in {2k, 4k, 8k}? F-8 measured
   divergence falling with position; F-12's law extrapolates the L=245
   payload rate flat. If divergence keeps falling, the law is an upper
   envelope at long L. Known hazard, pre-registered: greedy base models
   drift into repetition loops at long horizons; looped text has near-zero
   divergence (flattering to amber) AND near-zero zstd cost (flattering to
   the baseline). The degenerate regime must be detected and labelled, not
   averaged in silently.
B. On sessions where the target GENERATED each turn conditioned on full
   session history, does shared-context coding (ctx_mode 1) beat
   reset-per-turn (ctx_mode 0)? F-13's mechanism story predicts the sign
   flips because the history is now information the target actually used.
   This is the falsifiable half of F-13's caveat.

## Setup
Target meta-llama/Llama-3.2-3B (base) greedy, bf16, batch 1, KV cache —
same content definition as P1 (bf16 run-to-run is bit-identical on this
stack, F-5/F-7). Draft Llama-3.2-1B base; ALL encode scoring and decode
replay at cuda fp32 (D-8). gamma coder, max_rank 64, topk 128. Prompts:
sideband's set, same file as P1.

Part A: rows 0-15 max_new 2048; rows 16-27 max_new 4096; rows 28-31
max_new 8192 (row-fixed group assignment, families mixed by construction).
v3 single archives, prompt segment draft-coded (D-10). Early EOS is kept
and reported: groups are reported at REALIZED mean length, and every
band below applies at realized-L.
Part A rows reuse P1 prompt texts; by greedy determinism the first ~256
generated tokens should reproduce P1's content. Expected, not contamination.

Part B: rows 0-95 as 12 sessions of k=8. Turn 1 = BOS + prompt; turn i>1
appends prompt_i (no BOS) to the full session so far; the TARGET generates
each turn with max_new 256 seeing everything before it. The same content is
then encoded twice: ctx_mode 1 (draft scores with full history — matched to
generation) and ctx_mode 0 (draft scores each turn from its own first token
— now the handicapped mode). Honest bias note, pre-registered: the k prompts
in a session are UNRELATED instructions, so history cannot help predict
prompt text much (F-13 measured 0.85x there); the content sign test is the
real question, the prompt term is expected near-flat.

## Metrics
- A: per group — realized lengths, file bits/gen-token with breakdown
  (fixed+frame / prompt / content), content bits by 1024-position bucket
  (standalone-coded accounting, labelled), divergence by bucket, D-6 table
  (own rate, AC-under-draft with matched conditioning via -sum log2 q,
  zstd-19 per archive and concatenated per group, raw), measured-vs-law
  ratio, repetition diagnostics (tail loop period/fraction, distinct-4gram).
- B: per mode — file bits/gen-token; per-turn-index prompt/content/
  divergence; the turns-2..8 content ratio m1/m0; D-6 table per mode.
- Decode: byte-exactness and tok/s for all Part A archives (32) and all
  Part B sessions in both modes (12+12).

## Pre-registered bands
- A1 content payload (whole-archive accounting), bits/gen-token:
  L2048 in [0.08, 0.35]; L4096 in [0.05, 0.32]; L8192 in [0.03, 0.30];
  non-increasing across groups (slack +0.02).
- A2 measured total / rate-law prediction (917/realized-mean-L + 0.455):
  in [0.35, 1.00] for every group. >1 means F-12's extrapolation was
  flattering; record it as a miss of the law, not of the format.
- A3 content bits/token in position buckets >= 1024: in [0.01, 0.25].
- A4 decode 32/32 byte-exact at cuda fp32 (8k-token incremental KV replay
  is new surface: any failure is investigated as a format/replay bug FIRST,
  contract question second).
- A5 labelling rule: group median loop_fraction > 0.5 => the group is
  labelled DEGENERATE and excluded from headline rate claims; if L8192 is
  degenerate, the text-continuation corpus becomes the REQUIRED replication
  before any deep-curve claim is cited.
- A6 directional, probable (not banded): amber total < zstd-19 per-archive
  at every group on rows with loop_fraction < 0.3.
- B1 THE sign test: content bits/token over turns 2..8, m1/m0 in
  [0.40, 0.95]. Ratio >= 1.0 FALSIFIES F-13's caveat hypothesis — first-
  class finding either way. A PASS does not auto-overturn D-11's reset
  default: desync containment still argues for reset; a PASS converts the
  default into an explicit rate-vs-robustness tradeoff.
- B2 mode-0 divergence turn 8 / turn 1 in [1.3, 6.0] (draft can't see
  history the target used).
- B3 mode-1 divergence turn 8 / turn 1 in [0.6, 1.6] (matched conditioning
  => roughly flat).
- B4 mode-1 prompt bits/token turns 2..8 vs turn 1 in [0.6, 1.0]
  (unrelated prompts; biased against a saving — noted above).
- B5 file-level total m1/m0 at k=8 in [0.55, 0.98].
- B6 decode 12/12 (m1) and 12/12 (m0) byte-exact at cuda fp32.

## Stop conditions / hygiene
- Symbol self-check (payload_to_symbols == symbols) on every archive and
  session before it is written; non-finite logits refuse to encode.
- Every stage resumable at row/session granularity (atomic writes); the
  longest atomic unit is one 8192-token generation (~5-10 min).
- Any decode desync halts further decodes of that part pending
  investigation (bug first, per A4/B6).

## GPU budget (estimate, not a band)
generate ~75-105 min (Part A long pole) + encode ~10 min + decode ~40 min
=> ~2-2.5 h total on the 3080 Ti, interruptible throughout.

## Commands
```
python experiments/p7_longhorizon.py generate
python experiments/p7_longhorizon.py encode
python experiments/p7_longhorizon.py decode
python experiments/p7_longhorizon.py report
```

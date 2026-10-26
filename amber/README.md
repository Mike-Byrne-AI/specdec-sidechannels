# amber

When a large language model generates text, a smaller "draft" model of the
same family usually agrees with it on most tokens. amber asked whether an
archive of the large model's text can be stored as the draft's rank
corrections, the position-by-position fixes the draft needs to regenerate the
text, and decoded by the draft alone, byte for byte. This repository is the
record of that test on one model pair and one machine, with the three dated
errata batches that corrected it, published as it stood when the work was
parked. Nothing here is maintained or offered as a tool.

**The answer, as corrected.** The draft codes both ends: it encodes from its
own teacher-forced logits over the target's text and decodes alone, and the
target only generates the text (F-14 row E1, which corrected the first line of
the record below). On meta-llama/Llama-3.2-3B as the target and
meta-llama/Llama-3.2-1B as the draft, over 48,958 generated tokens, greedy
divergence is 6.78% and amber v0 codes the text at 0.4738 bits per token,
against 0.4723 for arithmetic coding under the draft and 3.618 for zstd-19 on
the same text (F-8). That tie with arithmetic coding is a mixture: 125 of 200
rows end in an exact periodic tail covering 60.7% of the generated tokens, and
on the rows without loops amber reads 0.8929 against 0.8094 bits per token
for arithmetic coding under the same draft (F-14 rows E3 and E4). Against
zstd with a 16 KB dictionary trained on the other half of the same prompt
families, amber's per-archive advantage is 1.06x (F-16 row E18). What holds is
narrower and exact: under an fp32 decode contract, 200 of 200 archives decode
byte-exactly on the GPU and 24 of 24 on the CPU, while bf16 decoders fail 84%
of archives and fp16 decoders 28.5% (F-11). Real archives carry no attestation
(F-14 row E12).

**Dated note (2026-10-18): the headline figures per stratum.** Split by E3's loop
rule, greedy divergence on the 75 rows without loops is 13.40% (3.28% on the 125
looped rows; 6.78% is the mixture), and zstd-19 on the text of those 75 rows alone
is 7.492 bits per token, so amber's multiple over zstd-19 there is 8.39x against the
headline 7.64x (results/diagnostics_2026-10-18/p1_stratified.json, from the script
beside it, which reproduces every all-rows figure of F-8 and the E3 and E4 rows
before reporting). The absolute rates in the sentence above are therefore about half
of what the non-looped text shows, while the multiple over concatenated zstd-19 with
no dictionary survives the split (the dictionary comparison of row E18 is the
sentence above's 1.06x).

**How it was run, and by whom.** Each real-model experiment (P1 to P7) has a
protocol in experiments/ stating its arms, its bands and its kill tests; the
synthetic experiments a01 to a03 and the hardening sweep (F-1 to F-4) have
none, and the kill criteria of docs/WHY_THIS_DIES.md entered the history
with the first two findings. What the history shows: the P1 protocol entered
git about three hours before its result; the P2 protocol in a commit that
carried only a 64-position smoke payload, thirteen minutes before the commit
that carried its full payload, while the capture's own file timestamps put
the start of that run seconds after the protocol commit; the errata protocol
twelve minutes before its first payload; the P3 to P6 protocols in the same
commit as their results, so for those four the registration-before-run rests
on the author's word (measured 2026-10-17 and 2026-10-18 from `git log` on
each protocol and payload and, for P2, the untracked capture files' write
times); P7 was withdrawn before it ran. Findings carry their regime and their evidence paths, and
registered text with an error gets a dated erratum, never a rewrite. The errata pass (F-14 to F-16, rows E1 to E19) recomputed claims a
read-only review of 2026-10-09 had disputed, under rules pinned in
experiments/ERRATA_PROTOCOL.md before each recompute ran, except where the
record says otherwise (F-14 decided rows E4, E7 and E13 through logged
amendments written after its first dry run; F-16 decided two of E17's claim
sites after a revised dry run and labels E19 post hoc), and a
second AI agent
of the same model family as the assistant, run as its subagent, recomputed the
payload before the errata landed (results/errata_critic/REPORT.md). One human
researcher set the question, the kill criteria and every decision, and
arbitrated; an AI coding assistant (Claude Code) built the instruments, ran the
experiments and drafted the record under that direction.

**Terms, one line each.**
- target, draft: the large model that generated the text, and the small model that codes it.
- rank correction: at each position, the draft's rank of the token the target chose, counted from 1; rank 1 is the draft's own first choice, so a correction is any position of rank 2 or more (src/amber/codec.py).
- fp32 contract: the decoder replays the draft in float32 (D-9); bf16 and fp16 replay desynchronises.
- F-n, D-n, OQ-n, K-n: entries of FINDINGS.md, DECISIONS.md, OPEN_QUESTIONS.md and docs/WHY_THIS_DIES.md.
- E-n: a row of the errata pass, recomputed from committed evidence under a rule pinned before the recompute, or under a logged amendment where F-14 and F-16 say so.
- regime: the model pair, dtype, corpus and machine a finding holds for; every finding states one.

**Where to look.** FINDINGS.md, newest last, with every evidence path;
results/ for the committed evidence (the P1 shards under results/p1/
reproduce F-8's divergence and arithmetic-coding rate exactly, as a reader
of the assistant's own model family did on 2026-10-17, while F-14 rows E2 and
E5 corrected two of F-8's other figures from the same shards:
docs/audits/2026-10-17-image-audit/README.md); experiments/ for the
pre-registrations and the scripts; src/amber/ for the codec, the binary
formats and the real-model layer; tests/ for the roundtrip, corruption and
contract batteries.

**Install.** amber imports sideband's tested primitives and lockstep's
integer range coder (D-1, D-7) and installs them from sibling checkouts: in
the public repository they are the sibling folders `../sideband` and
`../lockstep`; on the author's box they were `../../Research/sideband` and
`../lockstep-ultimate-repo`. Then `pip install -e ".[dev]"`, `pytest -q` and
`python tools/lint_findings.py`; the suite needs no model and no GPU.

**Third-party content.** results/errata_web/ holds two saved arXiv abstract
pages, kept as the digest-bound evidence of F-14 row E13; they are arXiv's and
the papers' authors' content and are not covered by this repository's
licence. The P1 shards and the P4 to P6 archives under results/ are outputs
of the Llama 3.2 checkpoints named above; the repository root's NOTICE and
licence copies describe that use.

---

## The record as it stood on 2026-10-11

The text below this line is the front door as the record left it, kept with
its errata in place; the paragraph above replaces its first line.

**Verified archives: compress with the target model, decode with the draft
alone — byte-exact, self-describing, attesting.**
> Erratum (2026-10-10; F-14 rows E1, E12): E1: the real-archive encoder loads meta-llama/Llama-3.2-1B (the draft; the target is meta-llama/Llama-3.2-3B): archive.py opens "Real-model amber archives (header kind "hf"): encode with the draft's teacher-forced logits, decode with the draft alone, replayed incrementally." and encode_stage calls load_model(a.draft). The draft codes both ends; the target only generates. E12: no L1 path exists for real archives: attest_with_target replays the synthetic world and the hf header carries 0 of the synthetic-world keys it reads; it mentions the payload on 0 lines; attestation appears on 0 lines of the real-archive code and the P4-P6 experiments, and across all of src/, experiments/, tools/ and tests/ only in experiments/a02_attestation.py, experiments/errata_recompute.py, experiments/errata_text.py, experiments/p1_divergence.py, src/amber/codec.py, tests/test_amber.py. F-2's synthetic L1 stands as stated.

The fusion of two sibling projects: sideband (speculative-decoding harness)
supplies the tested primitives and the ledger methodology; determinism-layer
(lockstep) supplies the replay contract — narrowed by F-2 to RANK STABILITY,
not bitwise determinism. The economic premise is determinism-layer's own
surviving regime: packing as a free byproduct of inference already running,
which serve-time spec decoding provides literally.

## Status (v0.2.0)

> Erratum pass (2026-10-10): F-14 corrects 12 of 16 checked claims from a pre-registered recompute (experiments/ERRATA_PROTOCOL.md, results/errata_recompute.json); the lines below stand as written, with dated erratum notes where a figure changed.
> Second errata batch (2026-10-11): F-15 adds rows E15, E16 from a second pre-registered recompute (experiments/ERRATA_PROTOCOL.md amendment log, results/errata_recompute_2.json): 2 of 2 rows corrected under their pinned rules, 7 of 8 claim-site statuses standing at their own scope; the lines below stand as written.
> Third errata batch (2026-10-11): F-16 adds rows E17, E18, E19 from a third pre-registered recompute (experiments/ERRATA_PROTOCOL.md amendment log, results/errata_recompute_3.json): 2 of 3 rows corrected under their pinned rules, 3 of 14 claim-site statuses standing at their own scope; the zstd figures below carry no dictionary, and F-16 gives the dictionary comparator; the lines stand as written.
Working v0 codec on the sideband synthetic world: byte-exact roundtrip,
loud typed corruption failure, L0/L1 attestation, and the measured rate
curve (F-1) — beats the AC-under-draft bound at alpha >= 0.7, 12.5x raw at
alpha 0.97, with the honest caveat that content-level coders win this
degenerate world (D-6 exists because of it). v0.2 adds lockstep as a sibling
dependency (D-7), a hardened sealed header after the mutation sweep caught
silent length corruption (F-4), and the rank-stability census instrument
validated on synthetic drift (F-3). Phase 2 has RUN on two drafts (F-5/F-6 TinyLlama-1.1B,
F-7 Llama-3.2-1B-Instruct; one 3080 Ti): fp32 cross-device rank order is
exactly stable (0-1 flips/49k), fp16 flips 0.1-0.4%, bf16 1-2% of top-1s, all
near-ties; the same dumps show a 1e-3 logit grid crossing at 22-41% of
positions even at fp32 — rank contracts are far cheaper than grid contracts.
Phase 1 has RUN (F-8, Llama-3.2-3B -> 1B, 49k target-generated tokens):
6.8% greedy divergence, amber v0 at 0.474 bits/token — 7.6x below zstd-19 and
tied with AC-under-draft (0.472). K-2 does not fire. Format v2 (F-9/F-10,
D-8): a lockstep.rac coder with value-free contexts gains only 1% (and loses
40% on short archives — gamma stays default); the near-tie escape removes
top-1 desyncs as designed but bf16 decoders still mis-resolve 3-26% of
shallow-rank corrections, so the decoder contract is fp32-class draft replay
(0 desyncs / 49k positions, 3.65x the bf16 time). Payload digest added.
Real archives exist (F-11, D-9): encode with the 1B draft in fp32, decode
draft-only with incremental KV replay — 200/200 byte-exact on GPU, 24/24 on
CPU; bf16 / fp16 decoders fail 84% / 28.5% of archives, as F-10 predicted.
The v3 binary format (F-12, D-10) makes an archive a 130 B mean file:
4.26 bits/generated token at L=245 (97 B fixed pins+digests, prompt coded
with the draft at 11.3 bits/token, content 0.45), 200/200 fp32-exact with
the prompt segment decoded; rate = 917/L + 0.455 bits/token, beating
zstd-19-concatenated beyond L~263. Session archives (F-13, D-11) amortise
the floor: 1.65 bits/gen-token at 8 turns, 1.45 at 16 (3.4x under zstd-19
per session), reset-per-turn by default — shared-context coding measurably
LOSES on independently-generated turns and desyncs stay turn-confined.
Next: long-horizon + true multi-turn generation, hints (OQ-4),
seeded-sampling archives (OQ-3).
> Erratum (2026-10-11; F-16 row E18): E18: on the held-out half (P1 rows 100-199, 24780 generated tokens; dictionaries trained on rows 0-99), per archive on the full text: zstd-19 6.775 bits per generated token without a dictionary (the text carries the special-token literals E7 found, which a dictionary absorbs), 4.834 with a 4096 B dictionary (requested 4 KB), 4.439 with a 16384 B dictionary (requested 16 KB), 4.481 with a 22323 B dictionary (requested 64 KB), 4.481 with a 22323 B dictionary (requested 256 KB); amber v3 4.181 (1.050 without its 97 B fixed header). The 16 KB dictionary lowers the comparator by 34%; amber's per-archive advantage is 1.62x without it and 1.06x with it (9.728 for zstd once the dictionary's own bytes are spread over these archives). Sessions in reset mode whose rows are all held out: k=16 (5 sessions): amber v4 1.37, zstd-19 4.35 without and 3.51 with the 16 KB dictionary (multiples 3.2x and 2.6x; effect 19%); k=8 (12 sessions): amber v4 1.58, zstd-19 4.97 without and 3.70 with the 16 KB dictionary (multiples 3.1x and 2.3x; effect 25%). Concatenated full text: 3.81 without and 3.64 with the dictionary (effect 5%); by F-12's rate law the crossover moves from L 273 to 288. Content, concatenated generated text: amber v0 0.4213 against zstd-19 3.470 without and 3.322 with a dictionary trained on generated text (effect 4%): 8.2x and 7.9x. On the 22 held-out rows whose repeat-4-gram share is below one half: amber v3 5.10 against dictionary zstd 10.26 (14.38 without). Under the harvest's own definitions (special tokens skipped; repeat share over the row length) the same quantities are 6.251 and 4.446 per archive and, on 23 rows, 5.253 against 10.330, which is what its predictions were; without the literals the effects are 29% per archive, 18% and 23% for the sessions and 4% concatenated, every status unchanged. D-6's zstd rows were strawmen at the per-archive scale, strawmen at the session scale and fair at the concatenated scale; the dictionaries were trained on the other half of the same prompt families, which favours zstd.
> Erratum (2026-10-10; F-14 row E8a): E8a: at theta 0 (the shipped default) cpu_fp32 -> cuda_fp32_b1 has 1 desync in 49056 positions (class A, gap 1.34e-05); 0 at theta in {0.142, 0.465, 0.93}, as F-10's body states, so the headline's zero is the escape-on count and the shipped contract has one. As an ORDER claim (OQ-2) it is false at every theta: the top-64 order differs from cpu_fp32 at 379 positions, every one a near-tie (the largest encoder gap between the two tokens competing for the first differing slot is 1.48e-04); what is stable is the resolved token, and only at batch 1 with the escape on.
> Erratum (2026-10-11; F-15 row E16): E16: the top-64 order of cuda_fp32_b1 differs from cpu_fp32 at 379 of 49056 positions (378 distinct contexts); the encoder gap between the two tokens competing for the first differing slot (always the adjacent token) has median 6.7e-06 and max 1.48e-04 against an encoder top-2 gap of median 1.35 (p01 0.012), so F-14's "every one a near-tie" holds at logit scale; at the record's fp32 pair budget 2(tau_enc + tau_dec) = 8.6e-05, which that sentence did not state, 2 positions exceed it, 1 distinct context (sequence 89 offset 1, slot 43, gap 1.48e-04 (1.7x the budget), pair drift 4.50e-04; sequence 93 offset 1, slot 43, gap 1.48e-04 (1.7x the budget), pair drift 4.50e-04): a tail drift, not evidence of a pipeline bug, since tau is the 0.999 quantile of the aligned top-64 deltas (not a top-1 calibration), that quantile falls with depth on this arm (slot 0: 5.9e-05, slots 1-7: 4.8e-05, slots 8-15: 4.4e-05, slots 16-63: 4.0e-05), and 328 of 3090528 adjacent top-64 pairs drift by more than the budget. By first differing slot: slot 0: 1; slot 1: 2; slots 2-7: 11; slots 8-15: 13; slots 16-63: 352 (2 above). At slot 0, the scope of every claim site (F-7's and OQ-2's top-1 flips, F-10's A desyncs), the counts above budget are cuda_bf16_b1 0 of 983; cuda_bf16_b8 0 of 834; cuda_fp16_b1 0 of 208; cuda_fp32_b1 0 of 1; cuda_fp32_b8 0 of 0: the top-1 claims stand. At batch 8 (411 positions, 411 contexts, max 5.72e-05) 0 exceed that arm's 2 tau of 9.73e-05 (a census-derived proxy; P2b has no batch-8 budget) and 254 of 3090528 adjacent pairs drift by more than it. The other decoders at depth, informational: cuda_bf16_b1: order differs at 49056 of 49056 (48933 contexts), 4 above its budget 4.65e-01; cuda_bf16_b8: order differs at 49056 of 49056 (48933 contexts), 7 above its budget 4.52e-01; cuda_fp16_b1: order differs at 48090 of 49056 (47967 contexts), 4 above its budget 6.62e-02.

## Quickstart

    pip install -e ../sideband -e ../lockstep-ultimate-repo   # sibling deps (D-1)
    pip install -e ".[dev]"
    make test && make lint && make experiments

## Layout

    src/amber/bits.py     exact bit I/O + Elias-gamma (the default payload coder)
    src/amber/rac_codec.py  v2 rac1 coder over lockstep.rac: {A,C,T,X} grammar, tie escape (D-8)
    src/amber/codec.py    encode/decode/attest — the synthetic-world format (sealed header + payload digest)
    src/amber/real/archive.py  hf-kind archives: model pin, content digest; teacher-forced encode, KV-replay decode
    src/amber/binformat.py  v3/v4 binary framing: varints, 97 B fixed cost, draft-coded prompts, k-turn sessions (D-10/D-11)
    src/amber/rankcensus.py  rank-flip census instrument for Phase 2 (OQ-2)
    experiments/          a01-a03 synthetic; p1/p2/p3/p2b real-model ledgers + frozen protocols
    results/              committed evidence cited by FINDINGS.md
    docs/                 BLUEPRINT (phases + kills), PRIOR_ART, WHY_THIS_DIES
    FINDINGS / DECISIONS / OPEN_QUESTIONS   the logs (lint-enforced)

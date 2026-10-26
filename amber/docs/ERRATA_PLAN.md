# ERRATA_PLAN — correcting amber's record before the trio write-up

Status: PLAN, written 2026-10-10 from a sideband session on the operator's
direction. DONE 2026-10-10: steps 0-6 landed (amber 0f6d2f0, then
lockstep TP-7 at 54d83f4); the critic ran from amber as an explicit-opus agent
(results/errata_critic/REPORT.md), not from sideband; E11 is record-only and the
critic's proposed E15 is deferred, by the operator's decision. Nothing in this file is a finding. Every value marked "harvest"
below is agent output from an unverified review: it is a prediction to be
recomputed, never a citation.

## Why

- amber is parked (v0.4.0, 2026-08-30) and stays private. Public material
  about amber, sideband and lockstep will be built separately, from verified
  numbers only.
- A read-only multi-agent review on 2026-10-09 (the "harvest") found claims
  in amber's record that are wrong or overstated. Some are numbers a write-up
  would cite: the F-8 rates, the F-10 desync count, the depth table.
- This plan corrects amber's own record with dated, append-only errata. Each
  number is recomputed from evidence committed in this repo, the recompute is
  pre-registered before it runs, and a critic re-derives the payload before
  the errata land. The write-up then cites amber at the landing commit.

## Inputs

- Pinned state: amber HEAD `8662535`, clean tree on 2026-10-10.
- The harvest, at `C:\Users\Michael\Desktop\Research\sideband\harvest\amber-lockstep-review-2026-10-09\`
  (untracked, gitignored in sideband). Its `README.md` is the index.
  `scratchpad/digest/wf2_final.json`, key `catchup.doc_corrections`, holds
  73 proposed corrections to this repo's files, and `scratchpad/verify/*/`
  holds the verifiers' scripts. Use them as leads: re-derive, never copy a
  number across.

## Scope

In scope: the claims in the table below. These are the claims a write-up
could cite, plus the record's own headline errors.

Not carried: the product-positioning rewrites the harvest proposed (the
BLUEPRINT economics and phases, the WHY_THIS_DIES status lines, the patent
and FTO readings, the OQ-3 / OQ-4 priced states, the D-6 dictionary-zstd
amendment, the CLAUDE.md rule additions, the pyproject extras) and its 14
protocol fixes. One line in the errata finding records that they exist and
were not adopted: the thesis is parked, and those documents describe a
product no reader will see.

## Claims to check

Line numbers are at `8662535`.

| ID | Claim | Where | Harvest's value (a prediction) | How it is checked |
|---|---|---|---|---|
| E1 | "compress with the target model, decode with the draft" | README.md:3, docs/BLUEPRINT.md:3 | the draft codes both ends; the target only generates | code reading at the pinned sha: which model the archive encoder runs (src/amber/real/archive.py); quote the lines |
| E2 | F-8: "193/200 prompts hit the 256 cap" | FINDINGS.md:57 | 186/200; the other 14 end at EOS 128001 | count rows with 256 generated tokens in the results/p1/generate shards |
| E3 | F-8 caveat: continuations "are fluent" | FINDINGS.md:60 | 125/200 rows end in an exact periodic tail covering at least half the row (window 128, max period 64), 106 to 138 across definitions; 70.8% of generated tokens repeat an earlier 4-gram | amber's own `loop_fraction` (src/amber/real/longhorizon.py) at one pinned setting, plus a pinned sensitivity grid; the repeated-4-gram share |
| E4 | F-8: amber v0 0.4738 ties AC-under-draft 0.4723 bits/token | FINDINGS.md:59 | a mixture: concatenated, non-looped rows +0.0835 and looped rows -0.0422; per archive, amber trails AC-under-draft by 7-10% on non-looped rows | stratify by E3's pinned loop flag; amber v0 and AC-under-draft bits, per archive and concatenated, with amber's own rate functions (D-1) |
| E5 | F-8: target generation 32.8 tok/s | FINDINGS.md:59 | 32.8 is the unweighted mean of per-shard rates; token-weighted 25.0; about 40.6 steady (bimodal shards) | per-shard seconds and new_tokens in results/p1/generate/meta.json: unweighted mean, token-weighted rate, median; no "steady" figure unless its rule is pinned first |
| E6 | F-11 regime: encode 991 pos/s | FINDINGS.md:78 | 15 rows with stalls of about 2.2-3.6 s inside the timed score() account for 36.3 of the 49.4 s; about 4.2k pos/s clean | per-row score_seconds in results/p4/encode_meta.json; the stall rule pinned before the read |
| E7 | F-11: zstd-19 per archive 7.28 bits/token (OPEN_QUESTIONS carries "7.3") | FINDINGS.md:80 | the per-archive text includes the decoded `<\|begin_of_text\|>` literal (17 B per archive) and 14 `<\|end_of_text\|>` literals; 6.75 without them | re-decode the P4 texts with the pinned tokenizer (its tokenizer.json sha256 recorded); compress with and without the special-token literals |
| E8 | F-10: "0 desyncs / 49k positions / all ranks to 64" at fp32 (also README.md:34, OPEN_QUESTIONS.md:14; DECISIONS.md:100 says "0 desyncs / 55k") | FINDINGS.md:69 | at theta = 0, the shipped default (D-8), one desync cpu_fp32 to cuda_fp32_b1, i.e. 1/49,056 per arm; plus a rank-4/5 swap for a cuda_fp32_b8 decoder that P2b never ran; about 2e-5 per position (2/98,112) | the committed results/p2b_escape_robustness.json for the P2b arms; the b8 event needs the gitignored dumps in results/p2_llama32 (pinned by a sha256 manifest): recompute it, or mark it UNRECOMPUTABLE in this pass |
| E9 | The depth table: the write-up's headline, an erratum only if it disagrees with F-10's text ("3% of rank-2 and 9-26% of rank-3..8") | FINDINGS.md:69 | bf16 0.63% top-1, 6.0% rank 2, 59.8% ranks 17-64; fp32 1/49,056 per arm (Llama-3.2-1B-Instruct, CPU fp32 reference vs the 3080 Ti, theta = 0) | per arm and per depth from results/p2b_escape_robustness.json, under a pinned definition (encoder arm, decoder arm, theta, denominator); reconcile with F-10's printed numbers |
| E10 | Inputs lockstep's F-14 used: draft scoring 9,233 positions/s and 4.7277 B/token (F-8 prints 9.2k and 4.73) | FINDINGS.md:57, :59 | as printed | results/p1_divergence.json; exposed in the payload for lockstep's TP-7, not an amber erratum by itself |
| E11 | F-4: a declared-length ceiling (default 2^24) is checked before any replay | FINDINGS.md:31 | the binary formats v3 and v4 (src/amber/real/binformat.py) lost the ceiling | at the pinned sha, craft a v3 and a v4 archive that declare a huge length; record whether decode refuses before replay |
| E12 | F-2's L1 attestation read onto real archives | FINDINGS.md (F-2), README, BLUEPRINT | `attest_with_target` (src/amber/codec.py:370-386) compares the correction COUNT and caller-supplied tokens and never reads the payload; real archives have no L1 | code reading at the pinned sha; F-2's synthetic regime line itself stands |
| E13 | PMATIC is arXiv 2601.17684 | docs/PRIOR_ART.md:10 | 2601.10678 (Adler and Tang, v1 2026-01-15); 2601.17684 is a different paper | save both arXiv abstract pages with their sha256 and read the titles and authors |
| E14 | The P7 pre-registration stands frozen | experiments/P7_PROTOCOL.md (HEAD commit 8662535) | withdraw it: no GPU stage ran and none will | a dated withdrawal line; no number |

## Steps

### 0. Environment (no repo change)

- Both editable installs point at moved paths: `pip show amber` reports
  `<path outside the repository, scrubbed at export>` and `pip show lockstep-archive` reports
  `<path outside the repository, scrubbed at export>` (2026-10-10), so neither
  package imports. Reinstall both with `--no-deps`:
  ```
  python -m pip install -e <path outside the repository, scrubbed at export> --no-deps
  python -m pip install -e <path outside the repository, scrubbed at export> --no-deps
  ```
  `--no-deps` matters. amber declares `sideband>=0.2.0`, and a resolver run
  could replace sideband's editable install, which must keep resolving to
  `C:\Users\Michael\Desktop\Research\sideband\src\sideband\__init__.py`.
- Verify:
  `python -c "import amber, lockstep, sideband; print(amber.__file__, lockstep.__file__, sideband.__file__)"`.
- Baseline before any change: `python -m pytest -q` and
  `python tools/lint_findings.py` (no `make` on this box). Record the counts.
- Git identity: this repo's local `user.name` is `amber`. Set the identity
  the operator wants credited before the first commit (the operator decides).

### 1. Evidence commit, before any recompute

- Line endings first. `core.autocrlf` is true on this box, and 20 of the 24
  tracked results files are LF in the index and CRLF on disk
  (`git ls-files --eol results`, 2026-10-10). Add `.gitattributes` with
  `results/** -text` and renormalise in the same commit. Cite results files
  by git blob id (`git rev-parse HEAD:<path>`), not by on-disk sha256.
  sideband's docs/TASK_RECIPES.md (the EVID-1 entry) and docs/SHARP_EDGES.md
  hold the recipe measured on this box.
- Commit the small gitignored raws the recomputes read, through negation
  rules in .gitignore: results/p1 (2.1 MB), results/p4 (3.2 MB), results/p5
  (2.1 MB), results/p6 (0.9 MB) (`du`, 2026-10-10). They hold
  Llama-3.2-generated token ids: private-repo evidence, never for public
  release.
  Dated note (2026-10-18): the last sentence of this bullet is superseded by
  the owner's call of 2026-10-18 on the public cut: the four folders ship in
  the public repository, under its root notice for Llama-derived material, as
  sideband's own model-output files ship. They are the evidence behind F-8
  and F-11 to F-13, and every errata row loads P1. The sentence stands as
  written; this note records the decision.
- The large dumps (results/p2 and results/p2_llama32) stay local. Commit a
  sha256 manifest of them instead.
- The stale `../sideband` path in the pyproject comment can be fixed in this
  commit (optional).
- Proof: tests and lint as at baseline, `git status` clean, and
  `git ls-files --eol results` shows `-text`.

### 2. Pre-registration: experiments/ERRATA_PROTOCOL.md, committed before any recompute runs

For each row E1 to E14, pin:
- the claim text and its location;
- the quantity and its exact definition. Where a definition needs a choice
  (the loop rule, the stall rule, the depth denominators), pin the choice
  and its sensitivity grid;
- the source paths with their blob ids;
- the function used: amber's own code wherever the claim is about amber's
  instrument (D-1);
- the decision rule: CONFIRMED when the recomputed value equals the printed
  claim at its printed precision, CORRECTED when it does not, UNRECOMPUTABLE
  when a named source is missing;
- the harvest's value, as a prediction scored after the run.

Amendments are dated and made before any result is read.

### 3. Recompute: experiments/errata_recompute.py writes results/errata_recompute.json

- CPU only, and nothing imports torch. The tokenizer is loaded lazily, for
  E7 only, and its tokenizer.json sha256 is recorded.
- Payload provenance: the script's sha256, git HEAD, a clean-tree flag and
  every input's blob id. The script refuses to run on a dirty tracked tree.
- One stable key per row (`rows.E2.value`, `rows.E2.status`, and so on), so
  the write-up's claims manifest can address each value by repo, commit,
  file and key.
- E13's arXiv pages are saved under results/errata_web/ with their sha256.

### 4. Critic recompute

Dispatch the critic from a sideband session: the harness and the
sideband-critic agent live there, and amber has neither. Use recompute
mode, point it at experiments/ERRATA_PROTOCOL.md and
results/errata_recompute.json, and set the model explicitly (opus; never
Fable, by operator rule). A BLOCKING objection stops the landing.

### 5. Errata text, generated from the payload

- A new finding, F-14 "2026-10 errata pass", with `- regime:` and
  `- source:` lines (the lint rule) and one bullet per row: the claim, the
  recomputed value and the status.
- Under each affected finding (F-2, F-4, F-8, F-10, F-11), one dated line:
  "- erratum (date): see F-14, row En". Append-only: the original text is
  never rewritten.
- Dated pointer notes at the other locations: README.md:3 and :34,
  docs/BLUEPRINT.md:3, DECISIONS.md:100 (D-8), OPEN_QUESTIONS.md:14 and the
  "7.3" line, docs/PRIOR_ART.md:10, a withdrawal line in
  experiments/P7_PROTOCOL.md, and the README status header.
- Every numeral and status word comes from the payload through a
  generator; none is typed by hand. Markdown table cells carry no unescaped
  pipes.
- E11: if the ceiling is confirmed missing, record that. Fixing binformat
  is a separate change the operator approves: under this repo's rules it
  needs a roundtrip test and a corruption test.

### 6. Land

- Tests and lint green. One commit for amber only, separate from any
  sideband or lockstep commit (this repo's CLAUDE.md). Local only, never
  pushed; the repo stays private.
- Then lockstep's TP-7 runs against the landed payload. It cites rows E5,
  E6, E8 and E10 at this commit.

## Done when

- results/errata_recompute.json exists at a clean landing commit, with a
  status for every row E1 to E14.
- F-14 and the dated notes are in, generated from the payload; lint is
  green and the tests are at baseline.
- The critic raises no blocking objection, and its recompute discrepancy is 0.

## Not doing

- No GPU runs, no new experiments, no P7, and no cross-architecture decode
  (deferred by the operator until the write-up exists).
- No product, economics or patent rewrites.
- No publication from this repo, and no push.

## Order across the trio

amber (this plan), then lockstep's TP-7, then sideband's own lines on the
same claims (through sideband's lane), then the write-up.

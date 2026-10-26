# Ecosystem map — sibling projects and borrowable tools

Surveyed 2026-08-28/29 on the Windows box (RTX 3080 Ti). Paths are absolute to
this machine. Sibling repos evolve independently of this survey: **verify a
path and skim the file before importing anything.** Nothing here is a finding;
findings live in FINDINGS.md with regime tags.

[withheld: the probe-estate salvage survey: four private repositories' report numbers and file paths (plan section 3); see WITHHELD.md]

## Sibling projects (who depends on whom)

(Section rewritten 2026-09-05 for release: the original carried absolute
paths into the author's private working copies; the paths and personal
folder names are removed and the rest is kept. None of these projects is
published with this repo - read each entry as "what the sibling exports",
not as a location. The header note above about absolute paths no longer
applies to this section.)

- **amber** - the verified-archives track (OQ-7 / T-A) spun out as its own
  repo the same evening as sideband v0.2.1. Declares `sideband>=0.2.0` as a
  pip dependency (installed editable from a sideband checkout) and imports
  `sideband.specdec` and `sideband.synthetic.World` verbatim. Its own
  ledger (amber F-2 / D-5) narrows the determinism dependency from bitwise
  determinism to **rank stability** of draft replay. OQ-7 build work
  happens THERE; sideband's e07 ledger and specdec primitives are its
  inputs. Key files inside amber: `src/amber/{codec,bits}.py`,
  `experiments/{a01_rate_vs_draft_quality,a02_attestation}.py`.
  Dated note 2026-10-11: two corrections to this entry. amber imports only
  `sideband.synthetic` (World and WorldConfig: its src/amber/codec.py line
  44, three experiments and three test files); no amber module imports
  `sideband.specdec` (grep over its src/, experiments/ and tests/ on
  2026-10-11); no amber real-model experiment imports sideband directly, but
  src/amber/real/archive.py line 31 imports amber.codec, whose line 44 loads
  `sideband.synthetic` at module level, so the experiments that import
  amber.real.archive, P4 to P7 and the errata recompute, load sideband too
  (checked by importing amber.real.archive on 2026-10-11: sideband,
  sideband.dists, sideband.sketch and sideband.synthetic appear in
  sys.modules), and the 210-prompt set is read as data by
  src/amber/real/divergence.py line 42; so of 'sideband's e07 ledger and
  specdec primitives are its inputs' above, what amber takes from sideband
  is the synthetic world behind e07 and the prompt file, never
  `sideband.specdec`. Its key files are now `src/amber/real/archive.py` (a
  separate pass: encode with the draft's teacher-forced logits, decode with
  the draft alone), `src/amber/binformat.py` and `src/amber/rac_codec.py`,
  with experiments P1 to P6 (P7 pre-registered, never run, withdrawn by
  amber's F-14 row E14) and the 2026-10 errata instruments; amber calls
  itself parked (its docs/ERRATA_PLAN.md), its record last moved at amber
  69b437c (tag errata-batch-3-landed; findings F-1 to F-16), and its
  measurements are cited from here through docs/DECODE_CONTRACTS.md's
  Sources table. The OQ-7 build work it took on ended with the draft on both
  sides (docs/PRIOR_ART.md, the OQ-7 cell's dated note, correction (c)).
  Dated note 2026-10-11 (second, public cut): amber and lockstep are the
  commercial branches of this research, both private repositories;
  amber's record last moved at 69b437c and lockstep is parked at cdfe0b3
  (its entry below).

- **lockstep** (the "determinism-layer" cited by D-4 / OQ-7 / amber) -
  exists only as archived repository snapshots, never unpacked into a live
  working tree. Inside: a range coder (`src/lockstep/rac.py`), CDF
  quantization, a DRBG, conformance vectors, `tools/lockstep_costmodel.py`,
  and the "packing must be a free byproduct of inference" economics finding
  (lockstep F-8) that BLUEPRINT's T-A leans on. Caveat: the LLM-backed
  profile (`lsp1`) is designed but NOT implemented - only the byte-model
  `lsp0` exists.
  Dated note 2026-10-11: the first sentence is superseded. lockstep became a
  live git repository, closed its research on 2026-10-10 (its F-17 to F-19)
  and is parked after this harvest. Its economics do not support T-A: the only
  pack rate in lockstep's record (F-17, measured by amber) is a separately run
  bf16 draft-scoring pass at 0.0437 MB/s, 460x short of F-8's break-even; the
  byproduct regime T-A leans on was never measured; and F-19 records that lsp1
  was never built. Harvested here: docs/DECODE_CONTRACTS.md (the
  value-contract half, beside amber's order-contract measurements) and a dated
  addition to docs/METHOD.md section 6. lockstep's F-12 to F-16 and F-18
  restate amber's measurements, and amber's later errata batches correct three
  of those restatements (lockstep F-20); cite amber's payloads through
  DECODE_CONTRACTS.md's Sources table, never the restatements. lockstep's own
  primary claims are F-1 to F-11, F-17's arithmetic and F-19.
  Dated note 2026-10-11 (second, written on parking, from the lockstep
  session): the standalone-merit verdict. lockstep had the problem right, the
  prescription wrong, and economics that made the prescription moot. Problem
  right: on amber's P4 archives a bf16 decoder fails 84.0% and fp16 28.5%
  (DECODE_CONTRACTS.md), so cross-dtype decode of an LLM-coded stream is a
  measured hazard, not a theoretical one. Prescription wrong: lockstep's value
  contract (a probability or logit grid plus a safeguard side-stream) crosses
  grid boundaries at 22% and 41% of positions on its two models even fp32 to
  fp32 at delta 1e-3 (lockstep F-12 and F-13, restating amber), so the
  "sparse" correction stream is not sparse; the contract that holds is amber's
  order contract under an fp32 pin (1 desync in 49,056 positions at the
  shipped theta 0, 0 with the escape on; lockstep F-18), which needs a dtype
  and kernel pin, not a runtime. Economics moot: packing is 92% of lockstep's
  own total-cost model (F-8), and the only pack rate in its record, a
  separately run bf16 draft-scoring pass measured by amber, is 0.0437 MB/s,
  460x short of that model's break-even (F-17). The vision document's claim
  that the blocker was "not ratio, speed, or cost trends" is the sentence the
  record refutes. Never tested, and the only two things that could have
  changed the verdict: the byproduct-user conversation (lockstep D-14 /
  OQ-13) and the attestation framing (its Blueprint E); neither is lockstep
  work, and no external implementor of its spec ever appeared, the retreat
  condition its own docs/08 set for the ecosystem risk. What stands:
  `src/lockstep/rac.py` as amber's production coder (lockstep F-15, 1% over
  Elias-gamma with value-free contexts; dated 2026-10-18: amber keeps
  Elias-gamma as its default coder and rac as its long-stream option, amber's
  DECISIONS.md D-8, and the real archives amber decoded record gamma as
  their coder, rac having been measured in P3's rate comparison, amber F-9;
  lockstep's audit report of 2026-10-18 item B4), the lsp0 vectors reproduced on a
  second OS and interpreter (F-11), and the method record (docs/METHOD.md
  section 6). lockstep stays installable as amber's frozen dependency and is
  not developed further. Its three parked blueprints that never depended on
  the dead thesis (decode receipts, recipe-pinned derived data, the unbuilt
  citation half of regime tags) are carried into docs/FUTURE_IDEAS.md. [withheld: docs/FUTURE_IDEAS.md not in this repository; see WITHHELD.md]
  Dated note 2026-10-11 (third, public cut): lockstep and amber are the
  commercial branches of this research, both private repositories;
  lockstep is parked at cdfe0b3 and amber's record last moved at 69b437c
  (its entry above).

- **Espalier-Lite** - the harness formerly named **Trellis** (CLAUDE.md's
  "Trellis note" refers to this). Full kit: `install_esplite.py`,
  `task-packs/`, `tools/`, `.claude/` with GODFILE/agents/hooks/skills; its
  HARNESS.md is the written spec these conventions came from. Sideband has
  the logs + critic agent but not the harness pieces (runs/RUNS.md,
  task-packs/, godfile tools, hooks) - "drops into the harness without
  changes" means layout compatibility, not that the harness is installed.

- **Espalier** (full) - main development happens on a different machine;
  any local copy is many commits behind, so borrow patterns, not
  implementations. Useful regardless: `espalier/fan_out_findings.py`
  (multi-agent review schema with adversarial refutation) and
  `espalier/finding_ledger.py` (append-only run-boundaried finding ledger)
  - if `sideband-critic` ever fans out.

- [withheld: a private repository's entry (plan section 3); see WITHHELD.md]

[withheld: a private repository's vocab-basket mechanism (plan section 3); see WITHHELD.md]

[withheld: the borrow list: file paths into private repositories (plan section 3); see WITHHELD.md]

## Environment facts (this box, verified 2026-08-28/29)

- RTX 3080 Ti 12GB; system Python 3.11.9; torch 2.6.0+cu124 CUDA-verified;
  transformers 4.57.3; accelerate 1.12.0; bitsandbytes 0.49.1; ~219GB free.
- HF cache complete: Llama-3.1-8B-Instruct (4/4 shards — the Phase-0a
  target), Llama-3.1-8B base. Incomplete/stub: Meta-Llama-3.1-8B-Instruct
  alias (1/4 shards), Llama-3.2-3B (config only, no weights).
- **Llama-3.2 access is gated OFF for this account as of 2026-08-29** (403 on
  1B-Instruct and 3B; the 3.1 license was accepted, 3.2 is a separate gate).
  Action: accept the 3.2 license on huggingface.co, then
  `hf download meta-llama/Llama-3.2-1B-Instruct` (~2.5GB).
- No `make` on this box: `make test|lint|experiments` =
  `python -m pytest -q` | `python tools/lint_findings.py` |
  `python experiments/run_all.py` from the repo root.
- Full synthetic suite ≈ 10–15 min here (16k-position sim ≈ 1.1s); e01 and
  e07 regenerate bit-exact vs committed results on numpy 2.3.5.
- Footgun: `run_all.py --smoke` overwrites committed `results/*.json` in the
  working tree (CI-safe, locally needs a `git restore` after).

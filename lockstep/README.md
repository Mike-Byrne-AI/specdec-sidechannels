# Lockstep

When a language model drives an arithmetic coder, the model's probabilities are the code: the
decoder has to reproduce exactly the numbers the encoder used, and floating-point arithmetic
does not promise that across machines, drivers or batch sizes. lockstep asked whether a
pure-integer coder, with a decode profile that pins every model parameter, could make such
archives decode bit-exactly on any machine, and whether that would pay for itself on archives.
Its original one-sentence version, from a planning document the public folder withholds:
"Information can be stored as computation — but only if the computation is *exactly*
repeatable, so Lockstep builds the layer that makes neural decode bit-exact on any machine,
forever, and everything else follows." The research was closed on 2026-10-10 (F-19) and parked
on 2026-10-11 (F-20); this repository is its record as it stood then, with the audit of
2026-10-18 beside it. Nothing here is maintained or offered as a tool.

**The answer, as the record and its audit leave it.** What was built holds: lsp0, a
pure-integer 32-bit arithmetic coder over a byte alphabet with two reference models, a
container that pins the coder's constants and every model parameter, and six conformance
vectors that reproduce byte-exactly on a second operating system and CPython build (F-11: one
Windows box, from a tree unpacked from an archive) and from three encoders the audit's agents
wrote without importing lockstep (two of them by agents who had read the reference code),
under the reading of specs/decode-profile-v0.md the reference
code follows (one renormalisation loop and the conventional initial state, which the
specification leaves unstated); read as three successive loops it reproduces 1 of the 6
(audit report, item D3). What it was for was never built: the
model-backed profile lsp1 (F-19). Under the coder's 16-bit probability total, the three
vocabularies of 128,256 tokens and more that the record tried cannot build a probability
table at all, and a 32,768-token one fits with half its probability mass in the floor (F-5,
an analysis of run_004 with no new hardware). The measurements made through amber show why
the proposed design would not have held beyond that. Between a CPU and a GPU both in fp32, a
1e-3 logit grid over the top 64
tokens is crossed at 21.9% of positions for TinyLlama-1.1B and 40.8% for Llama-3.2-1B, and at
every position under bf16 or fp16 (F-12, F-13: one RTX 3080 Ti against one CPU, 49,152
teacher-forced positions each); a 1e-2 grid is crossed at 2.6% and 5.0%, a setting the record
never priced. What holds for amber's archives is narrower: an fp32 replay pin under which 200
of 200 archives decode byte-exactly on the GPU and 24 of 24 on the CPU (F-16), with F-18's
qualifiers: the resolved token is stable at batch 1 with the escape on, the full top-64 order
differs at 379 of 49,056 positions, and a batch-8 decoder desyncs once. Those are amber's
measurements, and amber's payloads are primary (F-20). On cost, the cost model's first run had
LLM archiving lose to zstd -19 in every scenario (F-4); with its placeholder inputs, packing is
92% of total cost (F-8); the pack rate measured at batch 1, 0.0437 MB/s, is 460x short of the model's
break-even (F-17, which also corrects F-14's units slip of 114.5x). The audit found that
break-even built from placeholder prices and ratios, so the gap runs from 55x to 988x across
the record's own alternative inputs, and that with any decode rate the record measured in place
of the cost model's 2 MB/s decode placeholder, LLM archiving costs more than zstd -19 even with
packing free: the verdict that the standalone thesis loses survives, and F-8's 92% and its
free-packing branch do not (audit report, item B3). lockstep's range coder `lockstep.rac` is
amber's long-stream option; amber's default coder is Elias-gamma (amber's DECISIONS.md, D-8).

**How it was run, and by whom.** The code, the specs and F-1 to F-10 entered this history as
one imported archive on 2026-08-29, its first commit; ASSESSMENT.md records how three earlier
revisions were merged into it outside this history, and runs run_001 to run_005 were logged
there, so their measurements rest on the record's word (several of their probes were never
committed: audit report, items B2 and B12). From F-11 on, every commit names an AI coding assistant
(Claude) as co-author. F-12 to F-16 and F-18
restate measurements amber made. Findings are append-only: F-17 is a dated erratum, F-18 and
F-20 are dated status entries. The experiments E-001 to E-006 are protocols, and only E-006's
measurements were taken, through amber. Every decision, D-1 to D-15, carries the tag
[imagined], which the legend defines as "design choice not yet built", the built and tested
ones included (audit report, item B6). The agent harness the record was kept with ships beside
it (.claude/, tools/trellis_*.py, memory/ and the harness pages of trellis-docs/); its reference
checker reads finding IDs written F<N> and this record writes F-N, so its `refs` step checks
none of the twenty findings (audit report, item C2).

**Who made the code before the import, stated by the owner (2026-10-18).** The paragraph above
left the authorship of the three revisions ASSESSMENT.md merges to the owner. The owner's words,
recorded verbatim in sideband's plan of record (its section 15.8): "Everything lockstep was made by
me and AI assistance." Read as covering those three revisions as well as every commit of this history.

**Dated notes (2026-10-18): sentences below that no longer stand.**
- "the repository stays private" (the first banner), TP-7's "stays private" and F-19's
  "Anything public about this work is built elsewhere": this folder is published in the public
  repository the root README names.
- The Licensing paragraph ("No project license has been selected"; "should not be presented as
  licensed OSS") and the harness decision D-1's "This revision uses the MIT license": the
  public repository's root licence, MIT, covers this folder.
- The parking banner's "the contract that holds is an fp32 pin on token order": F-18 says what
  holds is the resolved token at batch 1 with the escape on, not the order.
- "lockstep.rac is now amber's production coder" (F-15's title; F-19's Why it matters says
  the same, and the run_010 row calls it rac's "First production use"): amber keeps Elias-gamma
  as its default.
- The Research direction section's next steps: the research is closed (F-19).
- VALIDATION.md, ASSESSMENT.md, CHANGELOG.md and F-10 describe this folder's own CI workflow,
  which the public repository does not ship; its root workflow runs the five commands of the
  Validation section from this folder.
- The "six conformance vectors" and "three encoders" sentences above, read as evidence for
  the whole decode profile: no vector drives the adaptive model's row total past its rescale
  limit (peak 3,712 against 32,768 over the five adaptive-model vectors;
  docs/audits/2026-10-18-image-audit/vector_coverage.py, its output pinned in its header), so
  neither the vectors nor the three encoders exercised the rescale clause, and a coder with
  that clause removed reproduces the five adaptive-model vectors' payload digests (the uniform
  sixth has no such clause). The sentences stand for what the vectors cover (added 2026-10-18).
- The parking banner's "bf16 decoders fail 84%": a rate for bf16 decoders reading archives
  encoded at fp32 (amber's P4 protocol), so a cross-dtype figure; it says nothing about a
  bf16-at-both-ends contract, which ts_zip's page states its model achieves deterministically
  across GPU and CPU models (F-16's two dated notes; docs/02 PA-4's dated note; added
  2026-10-18 and reworded the same day after the critic's recompute).

**Terms, one line each.**
- lsp0, lsp1: the byte-model decode profile that exists, and the model-backed profile proposed and never built.
- value contract: decode reproduces the model's numbers to a grid, with a safeguard stream for drift past it; order contract: decode reproduces only the token ranking (amber's).
- F-n, D-n, OQ-n, E-n, TP-n, run_n: entries of trellis-docs/trellis-findings.md, trellis-docs/trellis-decisions.md, docs/05-open-questions.md, experiments/, task-packs/ and trellis-docs/trellis-runs.md.
- [verified], [probable], [imagined]: the decisions' epistemic tags (the legend in trellis-docs/trellis-decisions.md).
- TCO: total cost of ownership in tools/lockstep_costmodel.py, which prints its lsp1 ratio and speed inputs as placeholders; its prices carry no source.

**Where to look.** trellis-docs/trellis-findings.md, newest last; specs/ for the normative
profile, container and conformance documents; src/lockstep/ for the coder and the container;
tests_project/ for the 82 tests of the code (.claude/trellis-tests/ holds the harness's own
119, of which 4 skip where their preconditions do not hold); tools/lockstep_costmodel.py and tools/lockstep_profile_advisor.py for the instruments
behind F-4 to F-8; docs/audits/2026-10-18-image-audit/README.md for the audit.

**Install and check.** Python 3.10 or newer and no dependencies: `python -m pip install -e .`
from this folder (amber installs it from the sibling folder `../lockstep`), then the five
commands of the Validation section below. The two vector files must be checked out with LF line
endings, which .gitattributes pins since 2026-10-18; before it, a Windows clone made with
core.autocrlf=true failed `self-check` and 3 of the 82 tests (audit report, item A1). The
generator's half is open: `tools/lockstep_gen_vectors.py --check` compares text, not bytes, and
`--write` writes the platform's line endings, which the attribute now lets into a commit (item
C1).

---

## The record as it stood on 2026-10-11

The text below this line is the front door as the record left it, unchanged; the paragraphs
above replace its first lines, and their dated notes say which of its sentences no longer stand.

> **Archived 2026-10-10.** This research is closed and the repository stays private: see `trellis-docs/trellis-findings.md` F-17 (the erratum to F-14's economics), F-18 (the status of F-15 and F-16 after amber's errata pass) and F-19 (the closing finding). Nothing below is maintained.
>
> **Parked 2026-10-11.** F-20 points at amber's later errata batches, which correct three sentences this log restated from amber, and records the harvest into sideband, where `docs/DECODE_CONTRACTS.md` carries this repository's grid-crossing result beside amber's rank-order measurements.
>
> **Parking follow-up 2026-10-11.** Standalone-merit verdict, recorded in sideband 8e3949b (`docs/ECOSYSTEM.md`, lockstep entry, second dated note): the problem was right (bf16 decoders fail 84% of amber's archives, F-16), the prescription wrong (the grid plus safeguard value contract crosses at 22% to 41% of positions even at fp32, F-12/F-13; the contract that holds is an fp32 pin on token order, F-18), and the economics moot (F-8, F-17). The three parked blueprints in `docs/07-review-and-ideas.md` that never depended on the thesis (D recipe-pinned derived data, E decode receipts, F regime tags) are carried into sideband's `docs/FUTURE_IDEAS.md`. This repository stays installable as amber's frozen coder dependency; nothing else changes. [withheld: docs/07-review-and-ideas.md not in this repository; see WITHHELD.md]

**A deterministic arithmetic-coding reference runtime and model-pinned archive format.**

Status: **pre-alpha research software**. The `lsp0` byte-model profile is implemented,
conformance-pinned, installable, and hardened for untrusted containers. The proposed
LLM-backed `lsp1` profile is **not implemented**; the repository’s own synthesis shows
that its original probability-grid design does not scale to modern vocabularies.

See [ASSESSMENT.md](ASSESSMENT.md) for the comparison of the starter, reviewed, and
synthesis repositories and the exact merge decisions behind this version. The exact
local release gate is recorded in [VALIDATION.md](VALIDATION.md).

## What exists today

Lockstep currently provides:

1. A pure-integer 32-bit arithmetic coder with bit-exact `lsp0` vectors.
2. A fully specified byte alphabet and two deterministic reference models:
   `adaptive-order1` and `uniform`.
3. A `.lsa` container that pins coder constants **and every required model parameter**.
4. Typed failure categories for malformed manifests, unsupported profiles, payload
   damage, decoder desynchronisation, and resource-policy limits.
5. Streaming file pack/unpack/verify paths with payload-first integrity checks and
   atomic destination replacement.
6. Packaged conformance vectors and an environment fingerprint for cross-machine runs.
7. Research tooling for profile feasibility and total-cost modelling.

It does **not** yet provide chunking, random access, multi-file framing, encryption,
model embedding, a native high-performance decoder, or an LLM adapter.

## Install

Python 3.10 or newer is required.

```bash
python -m pip install -e .
```

The runtime has no third-party dependencies. Install the optional test dependency with:

```bash
python -m pip install -e '.[test]'
```

## Quickstart

```bash
lockstep pack README.md readme.lsa
lockstep info readme.lsa
lockstep verify readme.lsa
lockstep unpack readme.lsa readme.out

lockstep models
lockstep env
lockstep self-check
```

The CLI applies a 1 GiB input/output/payload policy by default. Packing stops if
either the source or the coded payload crosses its limit. Limits accept byte
counts or binary suffixes such as `512MiB` and `2GiB`:

```bash
lockstep pack input.bin archive.lsa --max-input-size 4GiB --max-payload-size 8GiB
lockstep unpack archive.lsa output.bin --max-output-size 4GiB
lockstep verify archive.lsa --max-output-size 4GiB --max-payload-size 8GiB
```

Reader and file-API defaults are 8 GiB and can be lowered per call. Treat these as
operational policy, not proof that decoding an allowed size is cheap.

## Python API

```python
from lockstep import pack, unpack

blob = pack(b"deterministic decode, forever")
assert unpack(blob) == b"deterministic decode, forever"
```

For large files, use `pack_file`, `unpack_file`, and `verify_file`; these avoid loading
the entire archive or decoded output into memory.

## Security and format behavior

A reader validates framing and schema before decoding, rejects duplicate JSON keys,
enforces manifest/payload/output limits, checks the payload digest before model work,
and checks the decoded digest before publishing output. File extraction writes to a
private temporary file, rehashes the bounded payload during decode to detect source
mutation, and atomically replaces the destination only after all checks pass.

The embedded SHA-256 values detect accidental corruption; they do **not** authenticate
a maliciously rewritten archive because an attacker can replace both content and
digest. Use an external signature/authenticated-encryption layer when provenance
matters.

The format is still pre-alpha. Do not treat it as a sandbox, do not decode untrusted
archives without explicit limits, and do not rely on it as the only copy of valuable
data.

## Validation

Run the product suite, conformance mirror check, hidden harness suite, and repair gate:

```bash
python -m pytest -q tests_project
python tools/lockstep_gen_vectors.py --check
python -m lockstep self-check
python -m pytest -q .claude/trellis-tests
python tools/trellis_repair_gate.py
```

At unification time this repository passes:

- 82 product tests plus 39 pytest subtests;
- all 6 packaged `lsp0` conformance cases with unchanged payload hashes;
- 115 Trellis harness tests, with 4 layout/platform skips;
- the full Trellis repair gate.

## Repository map

```text
src/lockstep/     installable reference implementation and packaged vectors
tests_project/    product, adversarial, streaming, fuzz, and conformance tests
conformance/      source-visible mirror of the normative lsp0 vectors
specs/            normative profile, container, and conformance documents
docs/             vision, threat model, prior art, review, failure analysis, synthesis
experiments/      E-001..E-006 operator protocols
task-packs/       planned lsp1, chunking, hardware, legal, and fuzzing work
tools/            vector, profile, cost, and Trellis maintenance utilities
trellis-docs/     findings, decisions, and run history
```

## Research direction

The current evidence points away from a global probability-space grid for LLM
vocabularies. The leading `lsp1` direction is logit-space quantisation over a small
top-k set plus a sparse safeguard stream, but that design still requires real
cross-device measurements, profile constants, model/tokenizer content pinning, and an
economic use case where inference cost is already being paid.

The highest-value next work is E-006 on real hardware and customer validation of the
“compression as a byproduct of an existing inference pass” thesis—not adding claims to
the format before those results exist.

## Licensing

No project license has been selected in the supplied repositories. The patent and model
licensing review remains TP-5. Choose and add an explicit license before external
publication or redistribution; this repository should not be presented as licensed OSS
until that decision is made.

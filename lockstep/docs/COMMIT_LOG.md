# Commit log of the private lockstep repository

18 commits, newest first, up to a84bef4968dcd7effc1a619ae9fa1d36c8629c68, the commit this folder is exported from. The public repository has a fresh history, so the hashes the record cites (trellis-docs/trellis-findings.md, README.md, task-packs/done/TP-7_errata_and_archive.md, task-packs/done/TP-8_harvest_and_park.md) resolve here and nowhere else in the public tree; the review rounds each landing records are in these messages. Absolute paths outside the repository are scrubbed; paths into the author's own sideband checkouts stay (the export's own-checkout rule). 0 messages name a private repository or match the deny list: each keeps its subject with the match replaced and has its body replaced by a `[withheld: ...]` line. A line naming a file this export withholds carries the same marker the rest of the folder uses.

## a84bef4 2026-10-18 record: dated notes at F-8, the synthesis page's cost section and D-14 pointing to the audit's item B3 (the owner's call of 2026-10-18)

````text
The owner's call on the commercial register of the kept pages (sideband's plan of record, section 15.9): the words ship as written, and the figures they rest on get the correction where they sit. Three dated notes, each append-only: under F-8's Open question (trellis-docs/trellis-findings.md), at the end of EF-4 on the synthesis page (docs/09), and under D-14's Source line (trellis-docs/trellis-decisions.md). Each says the figures rest on the cost model's placeholder inputs, the 2 MB/s decode rate among them, and points to docs/audits/2026-10-18-image-audit/README.md item B3 in its own words: with any decode rate the record measured in that placeholder's place, lsp1 costs more than zstd -19 even with packing free, so the free-packing branch does not survive measured inputs; the verdict that the standalone thesis loses survives every input set the audit's refuters tried, and the reason given for it, the 92% share, does not. Amended before any push after the critic's recompute of the same evening, which found the first wording ahead of B3 on the share and short of it on the qualifier. Nothing is withheld or removed (11 inserted lines, 0 removed, against the parent). Validation in a copy of the final tree: tests_project 82 passed in 10.12s; lockstep_gen_vectors.py --check OK: 2 vector copies match generated lsp0 data; self-check: all 6 vectors reproduced; profile lsp0 OK; trellis-tests 115 passed, 4 skipped in 7.92s; the repair gate [OK] Trellis repair gate passed; every exit 0.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 4b6bcc1 2026-10-18 record: second dated note under F-16 (the bf16 rate is cross-dtype); the coverage script gains a probe self-test; five-of-six wording; the taxonomy note moved to its bullet's end

````text
After the critic's recompute of 2026-10-18 (sideband's plan of record, section 15.8, review): the F-16 dated note of the same day said the bf16 and fp16 rates were "not of the numeric formats"; amber's P4 archives were encoded at fp32 and decoded at bf16 or fp16, so the rates are cross-dtype figures, and a second dated note withdraws the phrase (append-only; the first note stands as written). README's dated-notes bullet on the 84% figure is reworded to the same scope. The "all six payload digests" wording in README, VALIDATION.md and the coverage script's docstring becomes "the five adaptive-model vectors' digests; the uniform sixth has no such clause". docs/audits/2026-10-18-image-audit/vector_coverage.py gains a self-test that feeds the probe a synthetic row crossing the rescale limit and asserts the probe sees the rescale, so its pinned "no rescale fired" rests on a probe that can detect one; its pinned EXPECTED is unchanged. The dated note in the taxonomy page's item 2 moves to the end of its bullet so the registered sentence it interrupted reads whole. Validation in a copy of the final tree: tests_project, gen_vectors --check, self-check 6/6, trellis-tests, repair gate, all exit 0.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2e20b0f 2026-10-18 record: F-21 erratum to F-2, vector-coverage note, ts_zip determinism note, F-16 scope note; MIT licence; owner's provenance line; __all__

````text
Dated notes from the cold read of 2026-10-18 (five unanchored reviewers; recorded in sideband's plan of record, section 15.8):
- trellis-findings F-21: erratum to F-2 quoting the audit report's item B1 figures; dated pointers beside the taxonomy page's item 2 and the architecture page's item 1.
- docs/audits/2026-10-18-image-audit/vector_coverage.py: no conformance vector reaches the adaptive model's rescale limit (peak 3,712 of 32,768); a coder without the clause reproduces all six digests; output pinned in its header; dated notes in VALIDATION.md and the README's dated-notes list.
- prior-art page, PA-4: ts_zip's deterministic BF16 evaluation quoted from its page (fetched 2026-10-18); F-16 gains a dated note scoping the bf16 failure rate to amber's PyTorch stack at its settings.
- LICENSE (MIT) and PEP 639 licence fields in pyproject (setuptools floor 77; a wheel built from the tracked tree carries licenses/LICENSE and License-Expression: MIT); audit item A2.
- README first screen: the owner's provenance sentence, verbatim.
- src/lockstep/__init__.py: __all__ naming the 34 re-exports; conformance.py: one unused import removed. ruff --select F on src: 35 hits to 0.
Validation in a copy of the checkout: tests_project, gen_vectors --check, self-check 6/6, trellis-tests, repair gate, all exit 0.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 145e33a 2026-10-18 Audit report corrected after the critic's fourth round (2026-10-18)

````text
docs/audits/2026-10-18-image-audit/README.md: the sentence on malformed manifests says no
untyped exception arose on any tried, 3,000 random mutations included (14 of which the reader
accepted), and that one malformed form, a null writer, is accepted where the container
specification says reject (the audit's S2-C-5; it said every malformed manifest raised a typed
error); item B4 cites the P4, P5 and P6 payloads, decoded by draft replay, and records that
sideband's ecosystem page now carries a dated note; the opening and closing paragraphs name this
fourth commit.

No finding, decision, protocol, test, tool or vector changed. Not pushed: Actions are enabled
on the remote.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 3590af9 2026-10-18 Audit report and front door corrected after the critic's second round (2026-10-18)

````text
docs/audits/2026-10-18-image-audit/README.md: item B4 scopes its archive clause to the real
archives amber decoded (the P4 and P5 payloads record gamma), since amber's F-9 measured rac in
P3's rate comparison (it said every archive amber measured was coded with gamma); item A1's
line-ending sentence holds under core.autocrlf true or input; section B's heading says none of
its candidates is landed in the findings log; the opening and closing paragraphs name this
third commit.

README.md's first screen: two of the three encoders were written by agents who had read the
reference code.

No finding, decision, protocol, test, tool or vector changed. Not pushed: Actions are enabled
on the remote.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## cafdd56 2026-10-18 Front door and audit report corrected after the critic's first round (2026-10-18)

````text
README.md's first screen: the cost model prints its lsp1 ratio and speed inputs as
placeholders and its prices carry no source (it said every price was labelled); the three
encoders the audit's agents wrote reproduce the six vectors under the reading of the decode
profile the reference code follows, and a reading of its renormalisation sentence as three
loops reproduces 1 of the 6 (it said they were written from the specification alone); F-5 is
an analysis of run_004 and covers the three vocabularies of 128,256 tokens and more, a
32,768-token one fitting with half its mass in the floor (it was filed under the amber
measurements); the pack rate is the one measured at batch 1; the harness holds 119 tests, 4 of
which skip; the roles sentence states only what git attests; the generator's line-ending half
(the report's item C1) is stated as open.

docs/audits/2026-10-18-image-audit/README.md: the same encoder sentence, with the agents of
slice S1 having read rac.py; item A1 names the generator's half as open; items A3 and A4 cite
the banners by name, not by line; item B6's closed decisions are the refuter's reading; item
D3 gives the three-loop reading's 1 of 6; the closing paragraph names this second commit and
the dated notes the first screen carries.

No finding, decision, protocol, test, tool or vector changed. Not pushed: Actions are enabled
on the remote.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## aa10639 2026-10-18 Front door for publication (2026-10-18): first screen, audit report, vector line endings

````text
README.md opens with a plain-language first screen (the question, the original one-sentence
version, the answer as the record and its audit leave it with every figure beside its finding,
who ran it and how, dated notes on the sentences the public release and F-18 supersede, one
line per term, where to look, install and check) above the front door as it stood on
2026-10-11, which is kept beneath unchanged.

docs/audits/2026-10-18-image-audit/README.md is the curated report of a read-only image audit
(nineteen agents: ten slice finders, one record reader, two reader walkthroughs, six
default-refuted refuters; 165 findings as found, 131 confirmed, 31 downgraded, 1 upgraded, 2
refuted, 8 added; 171 survivors, 25 high, ten distinct defects). Its section B lists the
candidates for dated errata; none is landed here.

.gitattributes marks the two copies of the lsp0 conformance vectors -text: their sha256 pin is
of LF bytes, and a clone made with core.autocrlf=true failed self-check and 3 of the 82 tests
(the report's item A1).

No finding, decision, protocol, test, tool or vector changed. Not pushed: Actions are enabled
on the remote.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## cdfe0b3 2026-10-11 Parking follow-up: standalone-merit verdict and Blueprints D/E/F carried into sideband 8e3949b; README banner line [withheld: Blueprints D/E/F not in this repository; see WITHHELD.md]

````text
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 23be2bc 2026-10-11 TP-8: F-20 (amber's errata batches 2-3 correct three restated sentences); harvest into sideband e74cbd7; parked

````text
F-20 points at amber 69b437c (tag errata-batch-3-landed): row E19 corrects
F-15's "per-rank rates transfer"; row E15 shows F-16's prediction
comparison crossed escape regimes, its sign depending on the predictor;
row E16 qualifies F-18's "every one a near-tie". It records the harvest
into sideband e74cbd7 (docs/DECODE_CONTRACTS.md, dated notes, METHOD
section 6 addition) and amends F-19's "no further findings": F-20 is the
last entry. runs.md F-15 row and README banner updated; TP-8 done.

Gates: 82 tests OK; GODFILE fresh; refs, pack-lint, reflect clean.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

## 54d83f4 2026-10-10 TP-7: F-17 (erratum to F-14), F-18 (status of F-15/F-16), F-19 (closing); README archived banner; TP-1..TP-6 archived

````text
Append-only findings sourced from amber's errata payload at its landing
commit 0f6d2f0 (results/errata_recompute.json, blob 551a1ccd; amber F-14),
generated by a scratchpad script so no number was typed: every figure in
F-17 and F-18 is a payload value or arithmetic shown in the text.

- F-17: F-14's own inputs (row E10: 9,233 positions/s token-weighted at
  4.7277 bytes/token) multiply to 0.0437 MB/s, not "~5 MB/s": 114.5x lower
  than F-14 stated, 11.5x below F-4's 0.5 MB/s placeholder (F-14 attributed
  it to F-8) and 460x short of F-8's 20.1 MB/s break-even. F-14's
  "no longer two orders of magnitude off" is withdrawn. Row E5: the
  32.8 tok/s target rate was an unweighted shard mean; token-weighted 25.0.
  Rows E3/E4 qualify the repeated "0.47 bits/token" (loop-degenerate corpus;
  the AC tie is a mixture).
- F-18: F-15's "0 desyncs / 49k" is the escape-on count (1 at the shipped
  theta 0; 1 at batch 8 at every theta, a rank-4/5 near-tie); its per-rank
  table is amber F-10's theta 0.465 / m 2 row, unstated there; F-16's
  "0 desyncs / 55k" stands (0 over 54,810); "991 pos/s" is a stall-dominated
  aggregate (3,521 pos/s excluding 17 stalled rows).
- F-19: `git grep -n -i lsp1 2d7d079 -- src` returns 0 lines; the research
  is closed, pointing at F-17, F-18 and amber's errata pass.
- README: dated archived banner. TP-1..TP-6 moved to task-packs/archive/
  with a status line (operator confirmed); TP-7 to task-packs/done/ with its
  status line. GODFILE regenerated (gitignored by design).

Proof gate at baseline (2d7d079): unittest 82 OK, refs OK, pack-lint OK,
reflect OK; godfile --check reported STALE because the untracked TP-7 was
not rendered (pre-existing, as the pack's stop rule asks to report). Proof
gate after: all five pass. Local only; the repo stays private.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
````

## 2d7d079 2026-08-30 F-16 verification: amber P5 re-confirms the fp32 pin with decoded prompt segments (deep-rank symbols on real text), 200/200 byte-exact

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## dec0b3e 2026-08-30 run_011 / F-16: fp32 replay contract verified end-to-end on real amber archives (200/200 GPU, 24/24 CPU byte-exact across device and kernel path; bf16 84% / fp16 28.5% archive failure); F-15 verification column updated

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## dd6a1c0 2026-08-30 run_010 / F-15: rank-order stability has a depth axis (amber P2b: fp32->fp32 0 desyncs to rank 64; bf16 23-26% of rank-2..64 corrections mis-resolve; top-1 escapes remove A-desyncs at 2tau); rac's first production use gains 1% over gamma with value-free contexts; open: parametrise AdaptiveByteModel alphabet

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f9e9c9c 2026-08-29 run_009 / F-14: first measured pack-side throughputs via amber Phase 1 (3B gen 33 tok/s, 1B draft replay 9.2k tok/s) and 0.47 bits/token archive rate; F-8 verification column updated

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## cb8bebf 2026-08-29 run_008 / F-13: second E-006 datapoint (Llama-3.2-1B-Instruct, V=128k) — fp32 eps p50 7e-6, delta=1e-3 crosses at 41% (law 45%), delta=1e-2 at 5%; rank order stable to 1 flip/49k

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## 7c5b0a4 2026-08-29 run_007 / F-12: first E-006 evidence via amber Phase 2 — fp32 cross-device eps ~3e-6 median, k*eps/delta law holds, delta=1e-3 grid crosses at 22% of positions (bf16/fp16 100%); rank order exactly stable at fp32; F-6/F-7 verification column updated

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## f1f733a 2026-08-29 run_006: F-11 independent-OS vector reproduction (Windows/CPython), D-15 amber sibling dependency + shared E-006 census; GODFILE regenerated

````text
Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
````

## dcbb088 2026-08-29 lockstep v0.2.0: import of lockstep-ultimate-repo.zip (sha256 4167766182777681d225d0c5c552341be31db8f027b11edb0707d5a6a8d6e409) as amber's sibling determinism-layer dependency

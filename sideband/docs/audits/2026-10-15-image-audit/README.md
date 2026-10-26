# Pre-publication image audit of sideband, 2026-10-15

Status note 2026-10-16 (lane B of the public-cut plan): this file is the audit's curated report, committed as
the evidence behind the dated notes and errata that lane B landed on 2026-10-16; docs/LESSONS.md lists them
and the rule each one taught. The report reads as it was written on 2026-10-15, with three edits: the corpus
pointer below names the author's private scratch instead of "this folder"; one path class in section A is
spelled out in words; and one sentence in section B item 7 names the two BLUEPRINT sites by position instead
of by the quoted phrases, so that the export's tone sweep does not match the report itself. The reviewer
walkthroughs and the finder and refuter files stay in that private scratch and are not shipped. The recompute
scripts whose numbers entered the record sit beside this file (see "Files beside this report" at the end);
each was made tree-relative and rerun from the committed tree on 2026-10-16 with its expected figures pinned
in its header before the rerun, and asserts those pins on every run. Lane A (c41f9f1, 2026-10-16) closed section A's test fixes; its last bullet, the Linux run with Actions on,
is still owed. Lane B closed section B items 1 to 7 except the verification of recalled prior-art
identifiers, which needs sources outside the tree and is its own lane. Sections C and D are lanes C and D of
the same plan and had not run when this note was written; each closing lane appends a dated line here.
Where a figure in the report differs from the JSON beside it or from the record's dated note, those win:
B1's "13 files" counts docs/METHOD.md's quotation of the critic's rule, which the lane gave a dated pointer
(twelve files carried the sentence itself); B3's "|z| up to 12,653" is the finder's offset-1 maximum,
while replay_c1.json and F-21's note carry the decision-path maxima 17,531 / 122,318, and the offset-5
figure 28,137 was not re-derived; B4's "nearest committed bound" was wrong: the nearest label-deciding
bound is F-28's RN at L1 replication gate upper +0.004951 (F-28's dated note); B5's "26-37% too high"
reads 16% / 26% on the committed ledger rerun (e07_ledger_out.json). Every file:line reference in the
report is at commit 4c6b043 and has moved since (the lane's own insertions among the causes); the block
titles and the file names are the stable pointers.
Lane C (2026-10-16; its commit hash is in the handoff's memory row) closed section C: S5b-C-1 (the lint reads
a wrapped source bullet whole; nine more cited paths are checked, 323 against 314, counted by the lint's own
parser over FINDINGS.md; the pathless-source half, a `- source:` with no path passing by design while D-4 and
METHOD.md say a path is required, is left open, and no entry is pathless today), S6b-C-1 (check 6 of
tests/test_evidence_bytes.py with tests/evidence_pins.json and tools/evidence_pins.py: 152 cited digests
resolving to 153 tracked files on 2026-10-16, compared with a fresh scan rather than with HEAD; paths are
compared and the line-ending form only recorded), S7a-C-1 (tests/test_fullfree_landing.py: the landed labels
through the instrument's conclude() over the payload rows, the provenance, and the fullfree instrument's digest
attested to its blob at the freeze commit; the state-to-payload leg is held by the twin recompute and by
check 6), S7a-C-6 (the twin, diagnostic and control verdicts pinned as landed), S6b-C-4 (a Stage-I positive
control on the sign and on the MSE identity; the null control is on magnitude at a cell picked from the ten
tried, nine of which pass its bar; the bootstrap's undercoverage is the probable cause of a null root reading
CI-clear, not one measured here), S6a-C-3 (the D-6 telemetry-stream test), S6a-C-9 (the one-hot run_block
index test), S6a-C-5 (the selection key called from the tool), S6a-C-2 (the tautology pinned to twenty
consecutive seed-24 draws and the draw after them), S6b-C-2 (the sharp-variant cached-vs-uncached asserts
restored; four of the five tests of that class, which need torch and ran a tiny model here, pass), S5b-K-6
(both lens builders pinned by digest; the balanced builder's other imports, sideband.glue and
sideband.harvest, are not pinned), S8-C-7 (experiments/_util.py smoke_results(), called first by every
script's main(smoke=True) and by the runner; e06's partial files follow it), S5a-C-3 (weights_only on
tools/run_k3_arms.py, whose blob the OQ-20 registration's environment capture records as c6304e3 and which
this change moves; the --inject-adapter path never ran, so no payload depends on it). Left open: S8-C-1
(data/make_prompts.py's Linux rerun and the oq16 verdict prompts' missing -text line; the evidence-bytes
checks catch the rewrite). The two lane-A hand-offs landed in the same lane (the file://// fold in
tools/export_public_cut.py and its hook pipeline, which moves the tool's digest; the tie-break test calling [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
the tool's key), and CITATION.cff's abstract carries its dated forward pointer with K-2's scope. No frozen
tool, payload, state file or registered text changed; no label moved.

Lever 3 (2026-10-17; its commit hash is in the handoff's memory row) answered the researcher walkthrough's second
doubt in part: docs/audits/critic-recovered/ holds a recovered selection of the reviewer's recompute scripts and
round reports of the harness era (308 of the 2026-10-16 archive's 309 files, the archive's rule having taken only
the top-level files of four suffixes inside critic-named folders; home paths scrubbed, every byte pinned by two
manifests; the rounds of the five public-cut lanes withheld from the public cut with the tool they review; its
[README](../critic-recovered/README.md) says what the folder is and is not, and what the rule left behind). The
outside half, a rerun of the committed audit scripts by a non-Anthropic model or a human colleague, stays the
operator's action.

Lane D (2026-10-17; its commit hash is in the handoff's memory row) dispositioned section D's two named items and the
first-screen item both walkthroughs put first. README.md now opens with a plain-language question, answer and
roles paragraph (the human, the assistant, the critic as a second AI agent of the same model family, run as the
assistant's subagent) and a one-line-per-term list before
its first label, the 2026-10-14 front door kept beneath; the public cut's root README gets the same opening, its
two repeated sentences removed and F-29 carried into its existence row and kill-criteria paragraph, where the S1
reader re-test's landing had not reached (its text still read "S1 not run"), and CITATION.cff's dated note gains
the same clause; tests/README.md says what each kind of test file checks, which fail rather than skip on missing
evidence, which six files a freeze record pins, and how to run part of the suite, and docs/CONVENTIONS.md "Tests"
gains a dated pointer to it with two moved facts. Left for a patch after v1.0.0,
as this section allowed: the git-provenance helper, the spec_decode_prompt split, the harvester mains and
calibration scripts, the critic-round comments and amendment-log docstrings, the frozen-instrument notes and
the two stale status lines in never-run modules; the conftest exists since lane A and `pythonpath` stays
`["src"]` (the tools/ imports stay explicit sys.path inserts, which tests/README.md documents). No frozen tool,
payload, state file or registered text changed; no label moved.

Read-only. Tree untouched at 4c6b043. Corpus: the author's private scratch (findings/, verdicts/ with their recompute scripts, walkthroughs/, survivors.md, survivors.json), not shipped.

## How it was run

- 12 slices of sideband's own research code (129 files, 47,165 lines; Espalier's engine assets excluded), each read by two Opus reviewers in different modes (correctness; craft), plus one tone read of docs/BLUEPRINT.md (13,867 lines, all sections) and two reader walkthroughs of the staging export (a researcher with 30 minutes; a hiring manager with 5).
- Every code/test finding was then handed to an adversarial refuter per slice, default-refuted, who re-derived every quantitative claim and checked the record for prior disclosure. The BLUEPRINT tone findings had no refuter (reviewer judgement only).
- Tally: 375 findings; 347 judged; 45 refuted, 136 downgraded, 164 confirmed, 2 upgraded; 28 added by refuters as missed. Survivors: 4 high, 41 medium, 282 low.
- Zero committed labels overturned. Every recompute any reviewer attempted matched: F-24's ten D rows and ten Mt rows from state files (0.0), F-20's delta_noise bit-exact from its state file, the stage-C freeze, the phase-0 tools, the lens builders (exact arrays), 873 of 875 numerals in the F-26 block, and the researcher walkthrough's independent-numpy reproduction of F-19, F-22 and all four F-24 gate intervals.

Status tags below: VERIFIED = checked by the orchestrator's own read; REFUTER = confirmed by a refuter with a recompute; TONE = reviewer judgement, unrefuted.

## The answer to "what signals does the repo give a stranger"

Three signals, in the order a stranger meets them:

1. **Density and private dialect** (minutes). The README's first screen is a block of undefined house labels; BLUEPRINT never defines who "the assistant", "the critic", "the user" and "the operator" are; docstrings open with registration IDs. Both walkthrough readers hit this first. Cheapest high-leverage fix: a plain-English first screen in README.md and a dated front-matter note in BLUEPRINT defining the roles.
2. **Copy-forward structure** (ten minutes). Instruments were built by copying the previous one: 20 to 80 percent verbatim between frozen rungs, 36 copies of a git helper, a 479-line adapter function, no conftest in tests. Every craft reviewer saw it. The frozen 16 cannot change; the editable code can.
3. **Guards weaker than their names** (an adversarial reader's probe). The findings lint, the evidence-bytes test, the F-24 payload test, the Stage-I tests and the landing-test pattern each enforce less than the record says. All fixable test-side.

What they would respect: the recruiter forwarded, on the kill criteria, the free baseline with its scrambled twin and the F-23 self-retraction; the researcher reproduced numbers with code of their own and would cite the work with its scope. "AI-generated" tells were judged present but not dominant in the code; the strongest AI tell is the prose (registration excerpts, critic-round IDs, session bookkeeping in registrations).

## A. Must fix before the private push (CI will be red)

- S7b-C-1 tests/test_prefetch_landing.py:59 — two stage-1 payloads store harvest_dir with backslashes; Path().name on Linux returns the whole string. F-26 headline landing test red. Fix in the test (PureWindowsPath or split on both separators). REFUTER, high.
- S7a-C-2 tests/test_reader_lens_landing.py:105 (+ readers, readers_long) — payloads store Windows-absolute paths read back through the FROZEN run_reader_lens.py:1050-1051,1067. Three F-28 landing tests red. Fix is test- or CI-side (a Windows runner for landing tests, or the test passes a path-normalised copy of the payload to the frozen function). REFUTER, high.
- S7a-C-3 tests/test_fullfree_coarse_amended.py:261 — rider_v1_preserved.path is a Windows path; F-25 S3 pair red. Test-side fix. REFUTER, high.
- S7a-C-4 / S7a-K-2 tests/test_reader_lens.py:26 — module-level torch importorskip removes all 26 tests on CI; 21 need no torch. REFUTER, medium.
- S6a-C-6 tests/test_probes.py:449 — pure-numpy checks (incl. the SeedSequence drift pin) hidden in torch-gated classes. REFUTER, medium.
- S7b-C-2 (disclosed, low after refutation) — the numpy==2.3.5 exact-recompute gate always takes the fallback on CI; the fallback still recomputes labels and checks parent CIs to 1e-12. Known; no action beyond awareness.
- Run the suite once on a Linux runner (the private remote with Actions on) before the pinned export; the plan already budgets this.

## B. Record-level: dated notes and errata (the critic-recompute lane)

1. **KV-crop vs "recomputes prefixes".** VERIFIED. hf_specdec.py:260 `use_kv_cache=True` default, crop at :649-661, docstring :3-12; commit b1dae57 (2026-08-29) before any GPU result; 23 of 26 committed metas `no_kv_cache: false`. The record says the adapter recomputes prefixes in 15 statements across 13 files (README:178, DECISIONS D-9:99, CLAUDE.md:27, GLOSSARY:102/422, REPORT:313, BLUEPRINT:2100, ECONOMICS:8/287 ["KV-crop fast path NOT built", dated 2026-09-05], RELEASE_NOTES:45, NOISE_FLOOR:145, WHY_THIS_DIES:241/256, ROOT_README:120, the critic agent), while CHANGELOG:1281, METHOD:189, REPORT:55 record the cached path. The ban stands; its stated mechanism is stale. Dated notes where true-when-written (D-9, CLAUDE.md, WHY_THIS_DIES:241, BLUEPRINT:2100, critic agent); dated errata where false-when-written (README, GLOSSARY, REPORT, RELEASE_NOTES, ECONOMICS, NOISE_FLOOR, WHY_THIS_DIES:256); fix ROOT_README:118-120 before export, and its "No wall-clock number exists anywhere" is literally false (59 stats.jsonl files log per-prompt seconds; DATA.md quotes runtimes) → reword to "no wall-clock claim or benchmark; instrument runtimes are provenance". The approved speedup-clause edit folds in here.
2. **Intervals omit probe-training variance** (S3-C-1, tools/run_probes.py:345-357). REFUTER, medium. Bootstrap resamples 30 test prompts after summing over 3 training seeds. 72 rows rebuilt to 1e-12; three estimators (normal-combination H, method-of-moments M, two-way bootstrap P). All F-24 D uppers (≤ +0.0047), TWIN-ROBUST, S3 L2 ABSORBED, S3 L3 SPLIT stand under all three. F-25 S1 L2 deciding row upper +0.0039 → H +0.0055 / M +0.00498 / P +0.0064; S1 Mn_r loses CI-clear under H and M; F-24's S3 linear "CI-positive" qualifier loses CI-clear. Three seeds = 2 df, size unmeasurable. BLUEPRINT.md:480 ("the train seed only shuffles AdamW batch order") is false: probes.py:238 seeds initial weights. Consequence: dated notes on F-25 (S1 L2) and F-24 (iii); erratum on BLUEPRINT:480; no re-run. Probable mechanism (unverified): 25 of 120 twin seed pairs read at different best-val epochs.
3. **Live Stage-C heads ran without a support clip** (S5a-C-1, train_outcome_head.py:552). REFUTER, medium. Every logged decision replayed exactly (17,185/17,185 and 17,616/17,616); |z| up to 12,653 / 122,318; a support clip would change 41 decisions per arm (0.24% / 0.23%) in both directions; seed-2 41/30, seed-6 42/47; rough bound ~0.01 tokens/call; C4-vs-C3 −0.0818 [−0.1325, −0.0356], no label moves. The "shielded" sentence (FINDINGS:252, BLUEPRINT:3053, GLOSSARY:582) refers to the output clip; live exposure stated nowhere. Dated note on F-21 with counts; pointers from F-22 (iii) and F-27's replay line; note that offset-5 heads reach |z| 28,137.
4. **Percentile cluster bootstrap under-covers at the record's cluster counts** (S1-C-2, stats.py:11). REFUTER, medium. Three independent simulations: 0.939 ± 0.0038 (4,000 reps), 0.934/0.942, 0.922 at 30 clusters; ~0.90 at 10; textbook 0.936. Known small-sample property, not a bug; docstring's "conservative end" is loose; undisclosed. Nearest committed bound: F-24 S3 primary linear off2 D upper +0.0029 → ~+0.0030 corrected; no label moves; one descriptive CI-POSITIVE-IMMATERIAL tag would drop to ~0. Docstring fix + one disclosure sentence (NOISE_FLOOR or METHOD).
5. **Synthetic-phase sentences** (S8). REFUTER, medium. F-4 "net harmful at every offset": offset 1 is seed noise (10 seeds, mean +0.0005, SE 0.0010; offsets 2-6 negative on all ten). F-9 break-even budget omits the bonus token: 26-37% too high; direction holds. e03-e05 ran argmax silently while D-10/pipeline docstring say posterior default. Dated errata on F-4 and F-9; regime strings note.
6. **Stale counts and claims.** VERIFIED where marked. RELEASE_NOTES 3.1 and README:389 say 30 results files carry the operator's name; 80 at HEAD (89 tree-wide) [REFUTER]. RELEASE_NOTES:173 and SHARP_EDGES:79-80 say --smoke no longer overwrites evidence; per-script --smoke still does (reproduced in a clone) [REFUTER]. FINDINGS.md:63 F-26 summary row stops at 2026-10-01 [REFUTER]. results/real/fidelity_calibration.json says "batch-16" for a batch-10 run [REFUTER]. README.md:271-272 Quickstart "609 tests (2026-10-04)" vs :327 "711 tests (2026-10-10)", lint "expected 27" vs 29 today [VERIFIED]. SHARP_EDGES:270 "-dirty counts tracked only" is not universal (two frozen tools count untracked) [REFUTER].
7. **BLUEPRINT tone** (TONE, unrefuted; 7 high, 13 medium, 25 trust passages). Highest leverage: a dated front-matter note defining the roles (assistant = AI co-author; critic/reviewers = LLM agents; user/operator/owner = the author) and stating that lowercase quoted strings are verbatim authorisations and harness references are process provenance (BP-T-7, -12, -20). Dated forward pointers under the two bold early "CONFIRMED" existence outcomes (BP-T-1 line 1088, BP-T-8 line 665) and the premise (BP-T-9 line 26) naming F-24/F-25/F-28. Dated erratum at 529 (R1 entropy tolerance supported by the rerun it passed; BP-T-2). Operator re-decides PC-2 for the pointer at 5494 to the withheld idea list's verdict (BP-T-5) and the v0.2.0 tracks section at 13843 (BP-T-6), or dated notes. Verify or mark every recalled prior-art id (BP-T-14; PRIOR_ART.md:4 already says "re-verify before citing"). P1 header "before any diagnostic probe ran" needs the erratum beside it (BP-T-11).

## C. Guards weaker than their names (test-side fixes)

- S5b-C-1 tools/lint_findings.py:166 — lint reads only the first physical line of a wrapped `- source:` bullet; 9 of F-28's 11 paths unchecked; renaming three to nonexistent files still prints OK. All 320 cited paths exist today. REFUTER, high. Also pathless sources pass by design (documented) but D-4 and METHOD.md say paths are required.
- S6b-C-1 tests/test_evidence_bytes.py:297 — HEAD-relative: a committed hand-edit passes all five checks; the title reads as absolute. 781 of 978 sha256 values resolve; an absolute "cited sha names a tracked blob" check is feasible. REFUTER, medium.
- S7a-C-1 tests/test_fullfree.py:341 — F-24's payload test accepts any label; no F-24 landing test; run_fullfree.py's sha attested nowhere (only the twin payloads bind it). REFUTER, medium.
- S7a-C-6 — twin / OQ-18 diag / poscontrol verdicts unpinned (TWIN-ROBUST, DOMINANCE-CONFIRMED-HERE appear in no test). REFUTER, medium.
- S6b-C-4 tests/test_outcome_head.py:258 — Stage-I tests have no positive control; a sign flip of delta() passes all 15. REFUTER, medium.
- S6a-C-3 — D-6 telemetry-RNG isolation has no test anywhere; a shared-stream mutant passes. REFUTER, medium.
- S6a-C-9 / MISSED-15 — run_block index mutants pass; the only kill is the lucky-seed ordering test (S6a-C-1, 12 of 20 seeds). Land a real run_block index test before touching C-1. REFUTER, medium.
- S6a-C-5 / K-1 tests/test_probes.py:513 — test re-types the tool's selection lambda; extract and call it. REFUTER, medium.
- S6a-C-2 tests/test_specdec.py:144 — tautology (both calls identical). REFUTER, medium.
- S6b-C-2 / K-1 tests/test_tools_and_real.py:584,631 — "cached matches reference" lost its asserts via 910522b and 7d46466; restoring them passes at HEAD. GPU-only. REFUTER, medium.
- S5b-K-6 / MISSED-13 — tools/build_balanced_groups.py is sha-pinned in BLUEPRINT (d6fda8997c65) but imports its math from unpinned build_concept_groups.py; nothing guards the pinned file's content. Pin both. REFUTER, medium.
- S8-C-7 / S8-K-1 — per-script --smoke overwrites committed evidence (reproduced). REFUTER, medium.
- S8-C-1 data/make_prompts.py:140 — Linux rerun rewrites the sha-cited prompts.jsonl (not silent: evidence-bytes check 4 and git status catch it); prompts_oq16_verdict.jsonl has no -text line and is LF in index / CRLF on disk. REFUTER, medium.
- S5a-C-3 — torch.load without weights_only on a user-supplied adapter (arms never ran). REFUTER, low; one-line fix.

## D. Craft (editable files; optional before v1.0.0)

- One git-provenance helper in sideband.provenance (36 copies, 4 semantics); one "-dirty" rule.
- spec_decode_prompt (479 lines, 18 params) — any split must keep the names frozen run_k3_arms.py imports and behaviour byte-identical.
- Harvester mains share 149 lines; two fidelity riders; two calibration scripts (138 lines); summarize_harvest re-implements verified_seed_files.
- tests: a conftest with shared fixtures and `pythonpath = ["src", "tools"]`; a tests/README.md explaining instrument vs landing tests, fail-not-skip, and which test files are byte-frozen (the single most leverage per line, per two reviewers).
- Comments that cite critic rounds ("the critic's A15") → state the rule; docstrings that are amendment logs (test_evidence_bytes.py:1, _run_freeze) → contract first, history after.
- Frozen instruments: note-only (stale docstrings "alignment-destroyed", "pure dilution", "shares init"; conclude-from printout cut at 6,000 chars before the K-2 key; usage line missing --lens).
- Stage-A tools and two never-run GPU modules carry stale status lines (steer_inject.py:1, oracle_replay.py:1).

## Walkthroughs

- Recruiter (5 min): FORWARD. Reason: builds the control that can kill its own result and publishes the kill. Red flags: README first screen (33 lines of undefined labels), two near-duplicate phrases, "adversarial reviewer" revealed as an agent only at line 169, CLAUDE.md ceremony, missing folders (the known layout state).
- Researcher (30 min): reproduced F-22, F-19 and all four F-24 gate intervals with independent numpy; sha chains hold. Biggest doubts: registration-order is operator-attested only; the reviewer is the same AI and its reports are uncommitted; S1 kill rests on a weak reader (stronger readers ran at S3 only); three F-24 support numbers have no committed artifact; data deposit pending. Got lost in: the first screen, superseded "existence is shown" summaries left in place (REPORT opening, sideband/CITATION.cff), stale Quickstart counts, a 27,414-character FINDINGS line.

## Recommended program (ordered)

1. Lane A, CI portability: the six Linux-red tests, the importorskip, the torch-gated numpy checks; then one Linux run on the private remote. Small. Precedes the pinned export.
2. Lane B, record errata batch, critic-recompute gated: items B1-B7 above (KV-crop wording in 13 files incl. ROOT_README and the speedup clause; seed-variance notes + BLUEPRINT:480; F-21 note; bootstrap disclosure; F-4/F-9 errata; stale counts; BLUEPRINT front-matter roles note and forward pointers; prior-art id verification). Medium.
3. Lane C, guards: lint wrapped bullets; evidence-bytes absolute check; F-24 landing test + instrument sha; twin/diag pins; Stage-I positive control; D-6 test; run_block index test; pin build_concept_groups.py; smoke-flag root fix; weights_only. Medium.
4. Lane D, craft and the README first screen + tests/README.md. The first-screen rewrite is cheap and is what both walkthrough readers hit first; the rest can follow v1.0.0 as a patch.
5. Operator calls: PC-2 re-decision on BP-T-5 and BP-T-6; the registration-order sentence in the README; whether to redact home paths in BLUEPRINT's registered commands (BP-T-19) or keep with the 3.1 disclosure (then fix its count).

## Files beside this report

Committed 2026-10-16. Every script resolves the repository root from its own location, writes its output next
to itself as LF JSON, and was rerun from the committed tree before the commit; the header of each pins the
figures the audit reported before the rerun, and docs/LESSONS.md quotes only figures that the rerun reproduced.

- `seed_var.py`, `seed_var_out.json`: section B item 2. Rebuilds 72 label-bearing rows of F-24, the corrected
  twin and F-25 from the committed state files (reproducing each payload interval to 1e-12) and reports three
  seed-inclusive approximations beside each. CPU, numpy only, a few seconds.
- `coverage.py`, `coverage_out.json`: section B item 4. Monte Carlo coverage of
  `sideband.stats.paired_cluster_delta_ci` on an F-24-shaped data-generating process at 10, 30 and 60
  clusters. CPU, numpy only, about ten seconds.
- `f4_seeds.py`, `f4_seeds_out.json`: section B item 5, F-4. e04's protocol over seeds 200 to 209 at rho 0.6,
  0.75 and 0.9 (the seed-200 run reproduces the committed e04 payload). CPU, about two minutes.
- `e07_ledger.py`, `e07_ledger_out.json`: section B item 5, F-9. e07's three arms at seeds 500 and 501 with the
  bonus token and the accept/reject indicator priced beside the committed correction bits. CPU, about ten
  seconds.
- `replay_c1.py`, `replay_c1.json`, `replay_c1_seed6.py`, `replay_c1_seed6.json`: section B item 3. Replays the
  live Stage-C head decisions of the F-21 verdict arms (seed 3 and the voided seed 2) and the OQ-20 seed-6
  arms, checks the replay against the logged decisions, and counts the decisions a TRAIN-support clip would
  change. These two scripts read the per-prompt byproduct arrays under `results/real/*.jsonl.byproduct/`,
  which are gitignored (docs/DATA.md), so they run only on a box that holds the raws and refuse with a
  message otherwise; under a minute each where they run; the JSON outputs are committed as data.

Every script asserts the figures pinned in its header and exits non-zero without writing on any mismatch,
so a rerun that passes rewrites its output byte for byte; each output records the numpy version it ran
under (the pins were set under numpy 2.3.5; numpy's Generator streams are not promised stable across
releases, so a mismatch under another numpy is a version note, not a finding, until rerun under 2.3.5).

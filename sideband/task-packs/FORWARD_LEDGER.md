<!-- espalier:seed-version v0.8.0b2 sha256:0aad1442fe3d87163f0cd42a9c0ef0bc3a2fa142e089cc3eb5d09df9029287ed -->
# Forward Ledger

_This repository's forward-work tracker: what is still wrong or still to do, grouped
into classes by the unit of work that fixes it, each live row carrying a probe that
re-derives its claim or a declared reason why none can. `espalier init` seeded it and
filed the onboarding rows below; every row after those is yours. Edit it through the
verbs in `tools/cc/`, never by hand -- they keep the counts, the index and the probes
in step, and refuse a write that would leave them disagreeing:_

- `python tools/cc/ledger_row.py class C4 --title "..." --population HYGIENE --audience MAINTAINER` opens a class;
- `python tools/cc/ledger_row.py file <ID> --section C4 --anchor <site> --text-file <row.md> --severity minor --subject <file> --probe-cmd "..." --open-value <value>` files a row, and drives its probe first (`--after <ID>` places it after an existing row; `--why-not "<reason>"` replaces the probe for a row nothing on disk can measure);
- `python tools/cc/ledger_row.py strike <ID> --text-file <closing.md>` closes a row, keeping its prior text;
- `python tools/cc/check_ledger_probes.py` re-derives every probed row (`/preflight` runs it);
- `python tools/cc/generate_ledger_regions.py --check` confirms every count below is derived from the rows.

Each writing verb holds a lock file beside the ledger while it works, so run them one at a
time: a second one refuses rather than racing the first.

**No completeness gate ships yet.** Nothing fails a build when a live row carries
neither a probe nor a declared reason for having none; filing through `ledger_row.py`
is what keeps every row honest, because it requires one or the other.

**Live: 1** — 0 logic bugs · 1 hygiene · 0 operator actions.
**0** reach an adopter.

## §2 — Open fixes, by unit of work (1 LIVE issues in 1 classes + 0 standalone)

**The three populations are counted apart, never as one number** -- a defect in the
code, a document or registry out of step, and a thing only a person can do are three
different kinds of "not done yet".

| population | live | what it means |
|---|---|---|
| LOGIC_BUG | 0 | code behaves wrongly |
| HYGIENE | 1 | docs / comments / registries / test scaffolding |
| OPERATOR_ACTION | 0 | no code fix exists: a person has to do it |

| audience | live |
|---|---|
| **ADOPTER** — a person who uses what this repository ships | **0** |
| MAINTAINER — you, and whoever works on this repository with you | 1 |
| OPERATOR — whoever runs what this repository ships | 0 |

### Class index

| § | class | members | population | audience | effort |
|---|---|---|---|---|---|
| [§C1](#c1--initialise-finish-what-init-started) | Initialise: finish what init started | 2 (**0 live**, 2 closed) | OPERATOR_ACTION | MAINTAINER | — |
| [§C2](#c2--test-confirm-the-harness-runs-this-repositorys-own-checks) | Test: confirm the harness runs this repository's own checks | 2 (**0 live**, 2 closed) | OPERATOR_ACTION | MAINTAINER | — |
| [§C3](#c3--adapt-fit-the-harness-to-this-repository) | Adapt: fit the harness to this repository | 3 (**0 live**, 3 closed) | OPERATOR_ACTION | MAINTAINER | — |
| [§C4](#c4--evidence-sha-cited-files-outside-results-must-reproduce-on-a-fresh-clone) | Evidence: sha-cited files outside results/ must reproduce on a fresh clone | 1 (**0 live**, 1 closed) | LOGIC_BUG | ADOPTER | — |
| [§C5](#c5--hygiene-imports-marked-rather-than-removed) | Hygiene: imports marked rather than removed | 1 | HYGIENE | MAINTAINER | — |

### §C1 — Initialise: finish what init started

**Members (2)** — derived, never typed

| id | site | what | sev |
|---|---|---|---|
| ~~`ONB-1`~~ | cc/GOAL.md (unless goal_snapshot = false) | ✅ **CLOSED 2026-10-01 — set 2026-10-01: cc/GOAL.md carries the operator-approved goal (keep the record honest and reproducible from a fresh clone; take whatever runs next through the pre-registered, critic-gated lane; the thesis question is closed negative at the registered reader and is not re-opened without a stronger reader). Per-machine file; the probe reads False.** PRIOR TEXT: **Set the goal** (on each machine: `cc/GOAL.md` is not committed). It still carries its skeleton's placeholder, so every session opens without knowing what this repository is working toward. Write the goal there (each `/handoff` keeps the rest of it current), or opt out with `goal_snapshot = false` near the top of espalier.toml -- above any `[table]` -- and delete the file. | minor |
| ~~`ONB-2`~~ | the hooks, armed on each machine | ✅ **CLOSED 2026-10-01 — confirmed 2026-10-01 on this machine: `python -m espalier doctor .` through the PATH engine reads status pass with no warnings, after the global engine was pinned to the deploy commit 2cb371b (0.8.0b2) and the fingerprint re-baselined with the matching engine; `integrity verify` ok, `audit` pass, `selfcheck --contracts` pass. Every hook has live or dry-run evidence this session (session_start banner, task_router cold-open, write_guard and plan_guard denies, post_write_check advisory records, subagent_start, subagent_stop, context_reinject_failure, reflect_trigger, stop_gate); post_compact is the one not yet exercised.** PRIOR TEXT: **Confirm the hooks fire** (on each machine you work from). `init` wired them into `.claude/settings.json`, which is not committed; `python -m espalier doctor .` is what says they are armed here. Run it, fix what it names, and strike this row once it reads clean on the machines you use. | minor |

### §C2 — Test: confirm the harness runs this repository's own checks

**Members (2)** — derived, never typed

| id | site | what | sev |
|---|---|---|---|
| ~~`ONB-3`~~ | the test command the gates run | ✅ **CLOSED 2026-10-01 — confirmed on this machine 2026-10-01, in this worktree (not a fresh clone) and before this lane added its own tests: the fingerprint's first test_command `pytest -q` from the repo root (the command /preflight step 2 and the opt-in stop gate run) = 460 passed / 5 skipped of 465 collected in 7:57, and `python -m pytest -o pythonpath=src` = 460 / 5 in 6:54; both counts include the 13 tests and 2 skips of the untracked tests/test_fullfree_oracle.py; the final tree of this lane collects 488 (475 tracked + those 13). `make test` (the second test_command) is dead here: make is not installed. The editable install was re-pointed at this checkout the same day (operator-approved `python -m pip install -e .[dev]`) and pyproject now sets pytest `pythonpath = ["src"]`, so a single test file imports the package in any checkout; before that the suite imported it only through tracked tools that put src/ on sys.path during collection (docs/SHARP_EDGES.md, first entry).** PRIOR TEXT: **Confirm the gates can run this repository's tests** (on each machine). `/preflight` runs the first test runner it finds installed (pytest, npm, cargo, go test); the stop gate's opt-in test gate runs `test_commands` from `reports/repo_fingerprint.json`, or the command in `ESPALIER_STOP_GATE_TEST_CMD` when that is set in the environment Claude Code starts in. If neither finds your tests, set the variable, or add the tests the fingerprint looks for and re-run `python -m espalier fingerprint .`. | minor |
| ~~`ONB-4`~~ | a first /preflight run | ✅ **CLOSED 2026-10-01 — run 2026-10-01 on this tree before its two commits, every step this repository's own: step 1 `ruff check .` under the repo's pyflakes-only config (exit 0) and `python tools/lint_findings.py` (OK, 27 findings, 296 cited paths resolved); step 2 `pytest -q` = 483 passed / 5 skipped of 488 collected in 3:59 (13 of the collected tests from the untracked tests/test_fullfree_oracle.py); step 3 `espalier audit` pass (0 errors, 0 warnings) and `integrity verify` ok (26 files); step 4 release gate skipped (adopter repo); step 5 `reflect-deep` exit 0 with 0 gaps and 0 orphans; step 6 the three review lanes on the diff: sideband-critic in recompute mode (round 1 NO-GO with 4 blocking, round 2 NO-GO with 1 blocking, round 3 NO-GO with 2 blocking, both one-line fixes landed as a third batch and re-proved in an autocrlf=false clone), code-reviewer REQUEST CHANGES minor (0 block, 3 warn, 7 nit) and failure-mode-reviewer REQUEST CHANGES (0 regression, 5 gap, 5 rough-edge), every accepted finding landed as three fix batches and re-proved; step 7 pin check skipped (adopter repo); step 8 ledger probes (two still-open rows filed by this run, EVID-1 and LINT-1; this row NO_ORACLE); verdict GO.** PRIOR TEXT: **Run `/preflight` once** and check that it ran this repository's own checks -- its lint, its tests -- and not only the harness's. Strike this row with what it ran. | minor |

### §C3 — Adapt: fit the harness to this repository

**Members (3)** — derived, never typed

| id | site | what | sev |
|---|---|---|---|
| ~~`ONB-5`~~ | reports/harness_config.json (profiles) | ✅ **CLOSED 2026-10-01 — decided 2026-10-01: python_library + docs_heavy stand. Consumers traced in the engine: profiles are labels recorded in the build plan, the blueprint and the handoff and printed by status; agents come from choose_agents(fingerprint) and permissions from the separate settings profile, so another label changes nothing functional, and a re-init to apply one would drop the critic lane.** PRIOR TEXT: **Confirm the repository category.** `init` chose the profiles in `reports/harness_config.json` from presence heuristics and name matches, so a folder of scripts can read as a library. If they are wrong, set `preferred_profiles` or `suppress_profiles` near the top of espalier.toml -- above any `[table]` -- and re-run `python -m espalier init .`. | minor |
| ~~`ONB-6`~~ | espalier.toml (plan_exempt_prefixes) | ✅ **CLOSED 2026-10-01 — decided 2026-10-01: espalier.toml sets plan_exempt_prefixes = [], keeping the gate on src/, tools/ (outside tools/cc), experiments/, results/, data/ and the root config files (coverage measured by plan_guard dry runs); an unplanned edit there is what the lane exists to prevent. The probe reads False.** PRIOR TEXT: **Decide which source folders need a plan.** The plan gate blocks an edit to a source file outside the harness's own folders until an execution plan is active. Name the folders where that is friction, not protection, with `plan_exempt_prefixes = ["src/"]` near the top of espalier.toml -- above any `[table]`, or it is read as part of that table -- or set it to `[]` to keep the gate everywhere. | minor |
| ~~`ONB-7`~~ | docs/CONVENTIONS.md + docs/SHARP_EDGES.md | ✅ **CLOSED 2026-10-01 — both files rewritten from measurements on this tree by /analyze (repo-analyst + docs-maintainer) and committed 2026-10-01 as 918cc9c (docs(harness): ground conventions and sharp edges on this tree); the probe reads False: neither file matches its seed sha.** PRIOR TEXT: **Replace the conventions and footguns stubs.** `docs/CONVENTIONS.md` and `docs/SHARP_EDGES.md` are still the stubs `init` seeded, and the agents read them as this repository's patterns and footguns. Write what is true here into each; any edit closes its half of this row. | minor |

### §C4 — Evidence: sha-cited files outside results/ must reproduce on a fresh clone

**Members (1)** — derived, never typed

| id | site | what | sev |
|---|---|---|---|
| ~~`EVID-1`~~ | .gitattributes (data/, tools/run_*.py, docs/OQ18_RIDER_*.md) | ✅ **CLOSED 2026-10-03 — in its own lane with the operator's say (2026-10-03, "got it, approved", given after the blob change to two frozen instruments was spelled out): `.gitattributes` pins fifteen sha-cited files outside results/ with `-text` (the twelve of this row plus the three instruments landed since, `tools/run_prefetch_bigram.py`, `tools/run_prefetch_strat.py`, `tools/run_prefetch_r2.py`, whose citers normalise line endings but whose raw-bytes self-attestation on a rerun needs the same pin; plus `tests/test_prefetch_r2.py`, pinned by a 12-hex raw-LF-bytes freeze record in docs/BLUEPRINT.md, outside the test's 64-hex scan and listed by hand in its HAND_PINNED), and `git add --renormalize` run in this worktree stored each as it is on disk: six blobs changed from LF to CRLF by line endings only (the four `data/prompts*.jsonl` files and the two frozen instruments `tools/run_fullfree_coarse_amended.py` and `tools/run_oq18_rider_diag.py`, whose attested bytes ARE the CRLF bytes), the rest unchanged; no disk byte changed (18 of 18 on-disk sha256 of the frozen closure and the cited files identical before and after). Measured in scratch clones of HEAD 41359bd before the fix, 186 citations of the fifteen in all: a core.autocrlf=false clone reproduced none of the 99 citations of the six CRLF-cited files while every one of twelve citation-bearing test files passed (no committed test covers those chains); a core.autocrlf=true clone reproduced none of the 87 raw-bytes citations of the nine LF-stored files (the row's 27 grown by the three prefetch landings; the prefetch chain's LF-normalising readers still pass) and failed exactly the three tests this row names. After the rehearsed fix, both kinds of clone reproduce 186 of 186 and pass the same twelve files (104 passed / 2 skipped, before check 4 existed). Enforcement: `tests/test_evidence_bytes.py` check 4 derives the cited set from the full-sha256 citations and requires the `-text` attribute in both the worktree's and the index's .gitattributes, a citation of the DISK bytes themselves (another line-ending form is reported as a stale checkout when the index still holds the cited bytes, with the eol remedy, and as an unreproducible chain otherwise), index-blob equality with those bytes, and citation counts no lower than HEAD's; red on this tree and both unfixed clones before the fix, green after; seven negative controls in the fixed clone (an attribute line removed, a byte appended to a cited file, a CRLF-twin citation planted, a CRLF-cited data file re-saved as LF, an LF-cited instrument re-saved as CRLF, that stale state renormalised, and the pre-fix LF blob staged under the CRLF disk copy of a data file) fire all five of its messages, each in the state it describes. An existing core.autocrlf=true checkout that pulls the fix keeps CRLF copies of the ten LF-pinned files with `git status` clean; `python tools/landing_text.py eol --fix-lf` on them is the remedy (measured in a clone left in that state: 186 of 186 afterwards). The probe prints False now.** PRIOR TEXT: **Sha-cited files outside results/ do not reproduce on a fresh clone.** Twelve tracked files under data/, tools/ and docs/ are cited by the sha256 of their bytes on this disk (126 citations in payload provenance, instrument pins and tests) and none carries the `-text` attribute, so autocrlf decides their bytes per checkout. All twelve are stored LF. Six are cited by their CRLF disk bytes (`data/prompts.jsonl` 64 citations, `data/prompts_k3_verdict.jsonl` 10, `data/prompts_oq15_verdict.jsonl` 8, `data/prompts_oq15_val.jsonl` 7, `tools/run_fullfree_coarse_amended.py` 8, `tools/run_oq18_rider_diag.py` 2), so an LF checkout (Linux, CI, autocrlf=false) breaks 99 chains; six are cited by their LF bytes (`tools/run_fullfree_coarse.py` 10, `docs/OQ18_RIDER_DIAGNOSTIC.md` 6, `tools/run_prefetch_readouts.py` 5, `tools/run_fullfree_twin.py` 4, `docs/OQ18_RIDER_POSCONTROL.md` 1, `tools/run_oq18_rider_poscontrol.py` 1), so a checkout on this box writes CRLF and breaks 27, and a clone made here fails three committed tests: `tests/test_fullfree_coarse_amended.py::test_frozen_instrument_sha_is_pinned_and_true_on_disk`, `tests/test_oq18_rider_diag.py::test_committed_diagnostic_payload_reproduces_its_verdict` and `tests/test_oq18_rider_poscontrol.py::test_committed_control_payload_reproduces_its_verdict`. No git configuration reproduces all twelve. Remedy candidate (its own lane, with the critic in recompute mode and the operator's say, because two of the six CRLF-cited files are frozen instruments): a `-text` attribute for the twelve plus `git add --renormalize` for the six cited by CRLF bytes, then `tests/test_evidence_bytes.py` extended to derive its targets from the citations instead of the `results/` prefix. The probe stays open until the attribute is set AND the six CRLF-cited files are stored as they are on disk; setting the attribute alone would make every checkout write LF and break the 99. Found by the failure-mode reviewer on 2026-10-01 and re-derived by the lane and the critic. | major |

### §C5 — Hygiene: imports marked rather than removed

**Members (1)** — derived, never typed

| id | site | what | sev |
|---|---|---|---|
| `LINT-1` | src/sideband/synthetic.py, tests/test_fullfree.py, tests/test_tools_and_real.py (noqa: F401) | **Five unused imports are kept behind `# noqa: F401` instead of being removed.** `ruff check --isolated --ignore-noqa --select F401` over `src/sideband/synthetic.py`, `tests/test_fullfree.py` and `tests/test_tools_and_real.py` reports five sites: three marked in the 2026-10-01 setup lane (`field` in synthetic.py, `SlotsAnchorBlock` in test_fullfree.py, an `import torch` in the Phase 0b production test) and two that carried a marker before it (an `import torch` and `sideband.real.shadow_telemetry` used as availability probes in test_tools_and_real.py, where ruff suggests `importlib.util.find_spec`). `ruff check .` reads clean because of the markers. The operator scoped the setup lane to configuration and deferred the removals. Close by removing the three debt imports and converting the two probes to `importlib.util.find_spec` in one small lane (targeted proofs: tests/test_synthetic_sidecar.py, tests/test_fullfree.py, tests/test_tools_and_real.py; then `ruff check .`); the probe strikes when the count reaches zero. | nit |

## §6 — Dropped / do-not-rediscover

**A finding a review has already declined, with the reason it stays declined.** The
review workflows read this section before they report, so a row here stops the same
finding being paid for twice; deleting one invites the re-find it prevents.

| id | what | why it stays declined |
|---|---|---|

## Appendix B — id index

| id | § | site |
|---|---|---|
| ~~`ONB-1`~~ | §C1 | cc/GOAL.md (unless goal_snapshot = false) |
| ~~`ONB-2`~~ | §C1 | the hooks, armed on each machine |
| ~~`ONB-3`~~ | §C2 | the test command the gates run |
| ~~`ONB-4`~~ | §C2 | a first /preflight run |
| ~~`ONB-5`~~ | §C3 | reports/harness_config.json (profiles) |
| ~~`ONB-6`~~ | §C3 | espalier.toml (plan_exempt_prefixes) |
| ~~`ONB-7`~~ | §C3 | docs/CONVENTIONS.md + docs/SHARP_EDGES.md |
| ~~`EVID-1`~~ | §C4 | .gitattributes (data/, tools/run_*.py, docs/OQ18_RIDER_*.md) |
| `LINT-1` | §C5 | src/sideband/synthetic.py, tests/test_fullfree.py, tests/test_tools_and_real.py (noqa: F401) |

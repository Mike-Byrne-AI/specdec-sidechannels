<!-- espalier:seed-version v0.8.0b2 sha256:b1fcb2c668a59c2e615855f61efaf8f431e00fd7f924dc5eeb5c43889316b041 -->
# Conventions

What this repo does, measured with `ast`, `grep` and `git` on 2026-10-01 at HEAD f1aabe4 (branch
`espalier-trial`; update 2026-10-15: the working branch is `main` since 2026-10-14, call PC-9 of the
public-cut decision batch, and `espalier-trial` is a retired ref, the one these counts were measured on).
Counts are of the working tree, which includes three untracked OQ-19 files
(`src/sideband/real/oracle_replay.py`, `tests/test_fullfree_oracle.py`, `tools/run_fullfree_oracle.py`);
re-measure before leaning on a number. Update 2026-10-01 (later): the three OQ-19 files are committed since 0a29d83 as an unfrozen draft, and the
free-bigram twin added `tools/run_prefetch_bigram.py`, `tests/test_prefetch_bigram.py` and
`tests/test_prefetch_bigram_landing.py`; counts that a line below does not re-date predate both. The new tool
has the documented shape (BLUEPRINT citation and date, a `NON-CRITERION` tag, a usage example, a smoke
command "refused under results/", `from __future__`, argparse, a main guard, a `src/` prepend).

The research discipline is not restated here. It lives in CLAUDE.md (hard rules, working practices),
DECISIONS.md (D-3 verifier math, D-4 regime/source lines, D-5 free baseline, D-6 paired seeds and the
isolated telemetry RNG, D-7 concept space, D-9 headline metric) and CONTRIBUTING.md (pre-commit gates,
"Register before you run", evidence files). This file covers what those do not: layout, naming,
instrument style, refusals, test shape, and the evidence/commit pattern.

## Layout and import direction

- **Directories.** `src/sideband/` numpy core; `src/sideband/real/` GPU adapters; `tools/` a flat directory of
  CLI scripts; `experiments/` synthetic-world runs; `tests/`; `results/` committed evidence. `tools/`,
  `tests/` and `experiments/` have no `__init__.py`; there is no `conftest.py` (dated note 2026-10-15: `tests/conftest.py`
  exists since lane A of the image audit, one session fixture `phase3_data_root` for the reader-lens landing tests).
- **Import direction** (AST over every module in `src/sideband`): core imports core only (the leaf is
  `dists.py`); `real/*` imports core and `real/*`; nothing under `src/` imports `tools/`, `experiments/` or
  `tests/`; `experiments/` does not import `tools/`. Verifier math lives only in `specdec.py` (D-3).
- **torch/transformers/scipy/sklearn are imported lazily, inside functions.** There is no module-level import of
  any of them in `src/`, `tools/`, `experiments/` or `tests/`, and `pytest --collect-only` leaves `torch` and
  `transformers` out of `sys.modules` even though both are installed here. `src/sideband/real/__init__.py:14
  require_real_deps()` turns a missing GPU extra into `ImportError("sideband.real needs the GPU extras: ...")`;
  `tests/test_tools_and_real.py:440 test_real_modules_import_lazily` pins four `real/` modules. Lazy imports
  also occur outside `real/`: `src/sideband/probes.py:230` (trainer), `src/sideband/glue.py:243`
  (`--tokenizer` path), 12 tools (inside `main()` or helpers); `tools/run_prefetch_readouts.py` declares itself
  numpy-only. scipy/sklearn appear only in `tools/build_concept_groups.py` (the `analysis` extra in
  `pyproject.toml`; `real` holds torch/transformers; CI installs `.[dev]` only; export note 2026-10-13: the public repository's root workflow installs `.[dev,analysis]`).
- **Instruments chain by bare module name.** Later instruments import earlier ones from `tools/`: `run_probes`
  <- `run_posthoc_topic` <- `run_fullfree` <- `run_fullfree_twin` <- `run_fullfree_coarse` <-
  `run_fullfree_coarse_amended`, with `run_oq18_rider_*` importing the same chain
  (`tools/run_fullfree_coarse_amended.py:51-75`). Since 2026-10-01 two more: the unfrozen OQ-19 draft `run_fullfree_oracle` imports the first five links
  (`tools/run_fullfree_oracle.py:117-127`), and a separate chain `run_prefetch_readouts` <- `run_prefetch_bigram`
  (`tools/run_prefetch_bigram.py:132`), where the child refuses at import unless the parent's LF-normalised sha matches
  (`:138-150`). Older arcs (K-3, OQ-15, OQ-16) put machinery in a core module
  (`scheduler.py`, `outcome_head.py`, `recon.py`) with a driver in `tools/`. No tracked module was added
  under `src/` between 2026-09-05 (`provenance.py`) and 2026-10-01, when the unfrozen OQ-19 draft committed
  `src/sideband/real/oracle_replay.py` (imported by its driver, `tools/run_fullfree_oracle.py:115`); the OQ-17,
  OQ-18 and OQ-9 instruments (2026-09-06 on, the free-bigram twin included) are single `tools/run_*.py` files.

## Naming

- **Code.** Modules lowercase snake_case, one topic each; private helpers `_prefixed`; classes CamelCase;
  constants UPPER_CASE (`MATERIALITY`, `N_BOOT`, `GATE_OFFSET`). No custom exception classes.
- **Tool scripts.** `run_<name>.py` (16 on 2026-10-04 by `ls tools/run_*.py`; 15 on 2026-10-03; 13 since `run_prefetch_bigram.py`, 2026-10-01) for registered runners and diagnostics, `train_*` (3), `calibrate_*` (2), `analyze_*` (2), and
  one-offs named for what they recompute (`e6_gate.py`, `ha_identity_check.py`); `landing_text.py` (2026-10-03)
  is a library tool, imported by bare name from each landing's scratch generator and applier
  (docs/TASK_RECIPES.md, "Landing texts").
- **Experiments.** `experiments/eNN_<name>.py` exposing `main(smoke: bool = False)`, writing
  `results/eNN_<name>.json` through `experiments/_util.py:14 save_json`; idea-tier probes are
  `experiments/probes/pNN_*.py`.
- **Tests.** `tests/test_<topic>.py`; an instrument's tests are `tests/test_<tool stem without run_>.py`
  (`tools/run_fullfree_twin.py` -> `tests/test_fullfree_twin.py`). In all 12 instrument/test pairs checked, both
  files were added in the same commit (the registration commit; the free-bigram pair too, d55e62f). A finding's landing test is
  `tests/test_<name>_landing.py` (two: `test_prefetch_landing.py`, which skips when its payloads are absent, and
  `test_prefetch_bigram_landing.py`, 2026-10-01, which fails instead, `tests/test_prefetch_bigram_landing.py:53-54`).
- **Payloads** (`results/real/`). `<family>_<source>[_r][_twin].json`; source tag `s1` = S1 shadow weight-slot
  harvest (`harvest_shadow/`), `s3` = S3 OLMoE router harvest (`harvest_moe/`); `_r` = the seed-replication
  harvest. A run's checkpoint is `<out>.state.jsonl` (full payload name plus the suffix). Meta files are
  `<stem>.meta.json` for newer tools (`prefetch_s3.meta.json`) and `<out>.meta.json` for the OQ-15/OQ-16
  family (`oq16_stage_r.json.meta.json`): both spellings exist. `*.rider_v1.json` is a frozen instrument's
  payload kept beside its amended successor (`fullfree_coarse_s3.rider_v1.json`).
- **Cell ids** are `"<space>|off<k>|<arm>|<capacity>|s<seed>[|SHUFFLED]"`, built only by
  `tools/run_probes.py:214 cell_id`. **Conclusion labels** are UPPER-KEBAB strings held in `LABEL_*` constants
  (`tools/run_fullfree.py:116-121`: `ABSORBED`, `NOT-SHOWN`, `SURVIVES-FULL-FREE`, ...).

## Instrument scripts (`tools/run_*.py` and kin)

- **Header docstring.** 22 of 31 tool docstrings cite `docs/BLUEPRINT.md` (22 also carry a date) and 26
  carry a `python tools/<name>.py ...` usage example. Shape (`tools/run_prefetch_readouts.py:1-52`,
  `tools/run_fullfree.py:1-70`): line 1 names the tool and OQ id; "Registered YYYY-MM-DD in docs/BLUEPRINT.md"
  plus the block title; a criterion tag, `CRITERION-BEARING` or `NON-CRITERION` (8 docstrings, 6 of them `NON-CRITERION`); "numpy only - nothing
  in this file imports torch" where true; the registered arms, cells, readouts and labels as prose; Usage; the
  smoke command marked "refused under results/". Five tools carry no registration (`analyze_glue`,
  `audit_harvest`, `bucket_persistence`, `lint_findings`, `verify_phase0a`): recompute/audit utilities.
  Dated note 2026-10-16: measured again by an ast read of each module docstring over 41 top-level tools, 17
  cite the path `docs/BLUEPRINT.md` (15 of them with a date) and 31 name BLUEPRINT in any form; the usage-example
  and boilerplate counts above were not re-measured.
- **Boilerplate.** `from __future__ import annotations` first (31/31); argparse (29/31); `main()` behind
  `if __name__ == "__main__"` (31/31); 29 tools prepend `src/` themselves
  (`sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))`, the following imports tagged
  `# noqa: E402`) so they run on a bare checkout. Exceptions: `lint_findings.py` (standalone on purpose, per
  CLAUDE.md), `bucket_persistence.py` (imports nothing from sideband) and, since 2026-10-03, `landing_text.py`
  (standalone like the linter; the instrument's reading rule is passed in; the 2026-10-01 counts in this bullet
  predate it).
  `export_public_cut.py` (2026-10-12) follows the same rule: stdlib only, no sideband import, git through [withheld: export_public_cut.py not in this repository; see WITHHELD.md]
  subprocess.
- **Pinned constants** sit at module top in UPPER_CASE and the CLI defaults equal the registered grid; the tool's
  test file pins both (`tests/test_fullfree.py:310 test_parser_defaults_are_the_s1_instrument`).
- **Payload shape.** Top-level `"registered"` (registration title and date; 13 tools write it) and a
  `provenance` dict: `git_commit` (HEAD sha, suffixed `-dirty` when a TRACKED file is modified, via
  `git status --porcelain --untracked-files=no`, `tools/run_fullfree_coarse.py:779-787`), input shas, the tool's
  own `instrument_sha256` (raw bytes of `__file__`, newer tools), `args` through
  `sideband.provenance.redact_args(vars(args))`, numpy and python versions. The `redact_args` rule is enforced by
  a source-grep test over `tools/*.py` and `src/sideband/real/*.py`
  (`tests/test_tools_and_real.py:929 test_every_meta_args_writer_redacts`).
- **Recompute surface.** Label-bearing readouts come from `--conclude-from` (one payload path in
  `run_prefetch_readouts.py`; `PRIMARY REPLICATION` in `run_fullfree{,_coarse,_oracle,_twin}.py`), which
  recomputes from the state file and exits on a mismatch (`RECOMPUTE MISMATCH`,
  `tools/run_prefetch_readouts.py:944`).

## Errors and refusals

- **Core (numpy) modules** raise `ValueError` for argument or shape misuse (67 raises outside `real/`) and
  `SystemExit` for data-integrity refusals on loaded evidence (15: sha mismatches, split integrity, NaN and
  shape guards, one overwrite guard; e.g. `src/sideband/harvest.py:85`, "npz sha mismatch - refusing unbound
  harvest data").
- **Tools and `real/`** refuse with `raise SystemExit("<what is wrong> ... refusing ...")` (375 in `tools/`,
  98 in `real/`, against 2 `ValueError` in `tools/`); messages name the cause and the remedy ("delete it or use
  a different --out"). No custom exception classes; no bare `except:` (0); `except Exception` (29 sites, 3 tagged
  `# noqa: BLE001`); the ones inspected are best-effort probes (the `_git()` helpers return "unknown") or
  fail-closed gates (`src/sideband/real/_preflight.py:91`; `tools/run_fullfree_coarse_amended.py:229` turns a
  git failure into a refusal).
  Dated note 2026-10-18 (plan 15.9): `tools/export_public_cut.py` is the exception and has been since its first [withheld: tools/export_public_cut.py not in this repository; see WITHHELD.md]
  commit (3e7b744: 47 `raise RuntimeError`, 0 `raise SystemExit`; 74 at 57867dc, 93 with plan 15.9's sibling
  proof stages and 96 after its hardening batch of 2026-10-19): its `main()` turns any `Exception` into exit 3, distinct from a NO-GO's 2, and prints a traceback
  for anything but a `RuntimeError`. `except Exception` does not catch `SystemExit`, so a refusal added to that tool
  in the `SystemExit` form above would bypass the handler and exit 1.
- **Existing outputs.** 8 tools take `--overwrite` and refuse without it ("<out> exists; pass --overwrite to
  redo"); 7 tools carry a `FRESH-STATE PIN` (a registered run refuses to start if `<out>.state.jsonl` exists
  unless `--resume`, which only continues a crash); 5 tools take `--resume`.
- **State-file binding.** `tools/run_probes.py:276 parse_state` refuses a headerless, corrupt or sha-mismatched
  state file ("refusing to resume; delete it or use a different --out") and drops a torn final line. The header
  row has three spellings by family: `{"kind": "state_header"}` (28 of the 47 tracked state files on 2026-10-02: the
  run_probes family, `k3_threshold_search`), `{"header": true, "tool": ...}` (12: `train_outcome_head`,
  `train_recon`), `{"state_header": true}` (10 of the 51 tracked state files on 2026-10-04, the families then 28 / 12 / 10 plus the one pre-header file below: `run_prefetch_readouts` and, since 2026-10-01, `run_prefetch_bigram`, since 2026-10-02 `run_prefetch_strat`, since 2026-10-03 `run_prefetch_r2`, since 2026-10-04 `run_prefetch_horizon`; one-shot writes with no resume; the 28 / 12 / 6 split is the 2026-10-02 count and predates the two R2 and the two horizon-read state files, whose first line is `{"state_header": true, ...}`);
  `probes_s1.json.state.jsonl` (pre-header era) has none. Read a state file with its own tool's parser. Dated
  2026-10-05: the two `run_noise_floor` state files carry `{"header": true}` WITHOUT a `"tool"` key (the second
  spelling's family, now 14 files; `run_noise_floor.conclude_from` reads them), so over the 53 tracked state files at
  HEAD the spellings count 28 / 14 / 10 plus the one pre-header file.
- **Registered-run guards.** Smoke options (`--only-seeds`, `--smoke-split-val`, a non-registered lambda grid)
  may not write under `results/` (`tools/run_prefetch_readouts.py:865-868`); `experiments/run_all.py --smoke`
  writes to `results/smoke/`; `tools/run_fullfree_coarse_amended.py:195 assert_frozen_instrument` and `:220
  committed_guard` refuse a changed frozen instrument or a dirty tracked tree. `tools/run_prefetch_bigram.py:141
  assert_frozen_instrument` guards its parent the same way, LF-normalised and at import. A committed but
  unregistered instrument refuses every run: `tools/run_fullfree_oracle.py:169 DRAFT_UNFROZEN = True`, checked in
  `main()` at `:768`, flips only in a freeze commit (`docs/OQ19_ORACLE_CEILING_DRAFT.md`, owed item 5); one
  instance (OQ-19, 2026-10-01), listed as a guard, not a convention. GPU runs go through
  `src/sideband/real/_preflight.py:56 preflight(...)`, which fails closed on free VRAM, GPU utilization, disk
  and a pending reboot.

## Tests

- **Dated note 2026-10-17 (lane D of the image audit).** [tests/README.md](../tests/README.md) is the reader-facing
  description of the suite (the kinds of test file, fail-vs-skip as measured, the six freeze-pinned test files, how
  to run); this section keeps the measured conventions. Two facts below have moved: `pyproject.toml` has also set
  `pythonpath = ["src"]` since ab12cbd (2026-10-01), and `tests/test_reader_s1.py` now inserts `tests/` on
  `sys.path` itself (its line 20 at this HEAD), so the import-mode remark about it no longer applies and its cited
  lines are :23 and :107.
- **Config.** `pyproject.toml` sets `testpaths = ["tests"]` and nothing else: no registered markers (only
  builtin `skipif`/`parametrize`), no `conftest.py`, one `@pytest.fixture` in the suite
  (`tests/test_outcome_head.py:236 synth_root`). Dated note 2026-10-15: `tests/conftest.py` exists (lane A, the session
  fixture `phase3_data_root`), and the fixture count above was already stale when written: four before it
  (`tests/test_export_public_cut.py:216`, `:222`, `:1050` and `tests/test_outcome_head.py:236`), five now. Dated note 2026-10-18: [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  seven by `grep -c "@pytest.fixture" tests/*.py` in the private tree (3 in the public folder, which withholds the
  export tool's test file; tests/conftest.py 1, tests/test_export_public_cut.py 4, among them [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  the module-scoped `real_amber` of plan 15.5, which skips when the amber checkout is absent unless
  `SIDEBAND_REQUIRE_AMBER=1`, tests/test_outcome_head.py 2; six at HEAD before that lane, so "five now" above was
  already stale). Dated note 2026-10-18, later: eight by the same command (tests/test_export_public_cut.py 5, the [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  lockstep survey's `real_lockstep` of plan 15.7 among them, which skips when a sibling checkout is absent unless
  either `SIDEBAND_REQUIRE_AMBER=1` or `SIDEBAND_REQUIRE_LOCKSTEP=1`). Data is built inline from `np.random.default_rng(seed)`
  (51 uses) and `tmp_path` (256).
- **Two shapes, split by date of first commit.** Class-per-unit, `class Test<Unit>` with `test_*` methods
  (`TestExactness`, `TestProposalCoupling`, ... in `tests/test_specdec.py`), in the 11 files first added
  2026-08-29..2026-09-02. Flat `def test_*` functions in the 18 files added since (12 first committed
  2026-09-03..2026-09-15; 6 on 2026-10-01: the harness witnesses `test_critic_lane.py`, `test_evidence_bytes.py`
  and `test_harness_doc_claims.py`, then `test_fullfree_oracle.py`, `test_prefetch_bigram.py` and
  `test_prefetch_bigram_landing.py`), one per registered instrument or
  landing. New instrument tests follow the flat shape.
- **Instrument test files** open with a docstring that names the instrument or the question and then `the
  CI-safe layer`, in one of three forms — `tools/<name>.py (OQ-NN ...)`, `tests/<name>.py (OQ-NN ...)` or
  `OQ-NN ... (tools/<name>.py)` (3 / 2 / 2 of 7 sampled on 2026-10-01) — and say "No torch"
  (`tests/test_fullfree.py:1-9`; 16 of 24 test docstrings declare CI-safety or no torch). One file imports
  another test module's fixtures (`tests/test_prefetch_bigram.py` puts `tests/` on `sys.path` and imports
  `test_prefetch_readouts`; a single instance, 2026-10-01, not a convention).
  Dated note 2026-10-16: no longer a single instance. Five test files in the index import another test module
  (`git ls-files 'tests/*.py' | xargs grep -lE "from test_|import test_" | wc -l`; four at HEAD f692032 plus the
  staged `tests/test_reader_s1.py`), seven import statements in all. The four prefetch-family files
  (`test_prefetch_bigram`, `test_prefetch_strat`, `test_prefetch_r2`, `test_prefetch_horizon`) put `tests/` on
  `sys.path` themselves and write `import test_<parent> as <alias>  # noqa: E402  (its fixtures)`;
  `tests/test_reader_s1.py:22` writes `from test_reader_lens import NPZ, NPZ_R, NULL_D, _payload, _readouts`
  (plus a function-level `import test_reader_lens_readers_long_landing` at `:106`) and inserts only `tools/`,
  relying on pytest's default `prepend` import mode to put `tests/` (no `__init__.py`) on `sys.path`: it
  collects 10 tests by default and fails collection under `--import-mode=importlib` (`ModuleNotFoundError: No
  module named 'test_reader_lens'`, 2026-10-16).
  Recurring contents: equal-dims factories in the same block order, the grid equals the registered one, label
  logic is mechanical, `--conclude-from` exercised (7 files), a parser-defaults test (7 files), and a
  `test_committed_*` test that reproduces the conclusion from the committed payloads and skips when they are
  absent (8 files at f1aabe4; `tests/test_prefetch_bigram_landing.py:50`, 2026-10-01, fails instead, by design, `:53`).
- **Assertions.** Refusals use `pytest.raises(SystemExit, match=...)` (145 of 217 `pytest.raises`); core
  preconditions `pytest.raises(ValueError)` (67); numerics `np.testing.assert_*` (113). Five files drive tools
  through `subprocess`.
- **Skips are of two kinds.** (1) torch/transformers: a per-file copy of `_has(mod)` plus
  `@pytest.mark.skipif(not _has("torch"), ...)` (`test_harvest.py:19`, `test_probes.py:18`,
  `test_tools_and_real.py:14`). (2) committed evidence: `pytest.skip("... payloads not present")` or
  `skipif(not path.exists())`. The 5 skips at this HEAD, run with `-rs` on 2026-10-01 (re-run after the free-bigram landing over the three skipping files: 76 passed, 5 skipped, the same five) and matching the 5 reported
  in commit c23f214: 2 x `tests/test_fullfree_coarse.py:418` (OQ-18 payloads are amended), 2 x
  `tests/test_fullfree_oracle.py:557` (OQ-19 draft payloads not present; the file is tracked since 2026-10-01), 1 x
  `tests/test_tools_and_real.py:443` (torch is installed, so the no-torch guard is not exercised; in a torch-less
  environment that test runs and the torch-guarded ones skip instead).
- **A hand-kept copy is held to its source by a witness test** (dated 2026-10-17; five instances, read from each
  test): CLAUDE.md's gated and exempt paths against `plan_guard._is_exempt`
  (`tests/test_harness_doc_claims.py::test_plan_gate_scope_matches_claude_md`); pyproject's `extend-exclude` tool
  entries against the payload-attested instruments plus their imports
  (`::test_ruff_excludes_exactly_the_frozen_instrument_closure`); the critic lane's surface list at every site
  that names it (`tests/test_critic_lane.py::test_canonical_surface_named_at_every_site`); `tools/evidence_pins.py`'s
  scope constants against the evidence-bytes test's own
  (`tests/test_evidence_bytes.py::test_pins_tool_scope_matches_this_file`, `RECOVERED_PREFIXES` added 2026-10-17);
  and the export spec's recovered-folder withhold keys and reasons against the folder's MANIFEST.json
  (`tests/test_export_public_cut.py::test_helpers`, 2026-10-17). The copy stays in the file its consumer reads [withheld: tests/test_export_public_cut.py not in this repository; see WITHHELD.md]
  (CLAUDE.md, pyproject.toml, the gate bodies, the tool, the spec) and the test names the drift. The stronger form,
  deleting the copy and asking the source (the export's `frozen_set` runs `git check-attr` itself since lane 2 of
  the public-cut batch, 2026-10-15), has one instance, so it is not yet a convention by this file's rule.
- **Count.** 609 collected on 2026-10-04 after the horizon read's landing (36 test files; tests/test_prefetch_horizon.py and tests/test_prefetch_horizon_landing.py added since); 583 collected on 2026-10-03 with tests/test_landing_text.py (34 test files; 560 / 33 after the R2 landing); 533 collected on 2026-10-02 after the stratified read's landing (31 test files); 513 on 2026-10-01
  after the code-review follow-up (509 after the free-bigram landing), all in tracked files (506 at d55e62f in a
  scratch clone; 488 = 475 + 13 untracked OQ-19 tests before 0a29d83; 458 = 445 + 13 at 918cc9c).
  Test functions are un-annotated (3 of 464).

## Code style

- `from __future__ import annotations` in 16 of 17 core files, 14 of 14 `real/`, 31 of 31 tools; return
  annotations on 144 of 145 public functions in the core, 64 of 88 in `real/`, 255 of 324 in `tools/`; PEP 604/585
  syntax (`list[str]`, `str | None`; `requires-python >= 3.10`).
- Randomness only through `np.random.default_rng(seed)` Generators (core: `sideband.dists.rng` / `spawn`); zero
  uses of the global `np.random.*` API in `src/`, `tools/` and `experiments/`.
- Linting (since 2026-10-01): `ruff` (in the `dev` extra) is configured in `pyproject.toml` to pyflakes rules only
  (`select = ["F"]`); `tools/cc` and the seventeen frozen-instrument files (nine until the free-bigram twin landed on
  2026-10-01, ten until the stratified coverage read landed on 2026-10-02, eleven until R2 landed on 2026-10-03,
  twelve until the horizon read landed on 2026-10-04, thirteen until the seed-noise floor readouts landed later that
  day, fourteen until the reader-and-lens re-test's lens stage landed on 2026-10-05, fifteen until the seed replay landed on 2026-10-10, sixteen until the S1 reader re-test landed on 2026-10-17) are excluded outright with `force-exclude = true` (`tests/test_harness_doc_claims.py` derives the
  list from the payload attestations plus their imports), and three remaining unused imports carry a line-level
  `# noqa: F401`. The house style keeps
  one-line statements and short math names, so the default rule set stays off. No formatter. `/preflight` step 1
  runs `ruff check .`; CI (`.github/workflows/ci.yml`) runs `pytest -q`, `python tools/lint_findings.py` and
  `python experiments/run_all.py --smoke`, not ruff. `# noqa: E402` marks post-bootstrap imports.
  Dated note 2026-10-17: `extend-exclude` carries a third kind of entry, the glob `docs/audits/critic-recovered/20*`
  (the session folders of the recovered critic folder: the reviewer's scratch scripts, copied as a record, never
  linted or edited; the folder's own `recover.py` and `gen_readme.py` beside them are linted);
  `tests/test_harness_doc_claims.py` compares only the `tools/*.py` entries with the frozen closure, so the glob
  entry leaves that test's equality and the seventeen above unchanged.

## Evidence and commits

- **Evidence files.** Committed under `results/`; `.gitattributes` sets `results/** -text` (byte-exact);
  `results/smoke/` is ignored; harvest `.npz` arrays and `*.byproduct/` are ignored and bound by sha256 in
  committed meta/summary files; state files are ignored by default (`.gitignore:12`) and un-ignored one by
  one (45 `!` lines = 45 tracked state files after the free-bigram landing, 2026-10-01; 47 state-file negations =
  47 tracked state files after the stratified read's landing, 2026-10-02, the file's 50 `!` lines including three
  for task-packs/; 53 negations and 53 tracked state files at HEAD on 2026-10-05 after the seed-noise floor landing (the working tree's `.gitignore` carries eight more negations for an uncommitted registration, not counted); 51 and 51 on 2026-10-04 after the horizon read's landing, 49 and 49 on 2026-10-03 after the R2 landing, counted over `results/real/` only). Line endings: writers open
  files in text mode without `newline=` (`experiments/_util.py:18`, `save_json` through `write_text`), so the
  platform that writes decides; `tools/run_prefetch_bigram.py:532 _write_lf` (2026-10-01) is the one writer that
  fixes LF (`newline="\n"`), 1 of 34 files with a text-mode write under `tools/`, `src/` and `experiments/` (a grep
  count). One instance, so not a convention yet; cc/GOAL.md lists the rest as owed. Update 2026-10-03:
  `tools/landing_text.py` also writes LF (its generated texts and `numbers.json`, `newline="\n"`) and rewrites a
  record file in that file's own line ending (`Doc`), so the one-writer count predates it; a library, not an
  evidence writer.
  Update 2026-10-03 (EVID-1): fifteen sha-cited files outside `results/` (the four `data/prompts*.jsonl`, the two
  OQ-18 registration docs under `docs/`, the nine attested instruments under `tools/`) carry `<path> -text` lines too
  and are stored as they are on disk, six of them CRLF; a new sha-cited file gets its line in its freeze commit (a
  registered run from a clone made between the freeze and the landing needs it), enforced from the landing on by
  `tests/test_evidence_bytes.py` check 4, which derives the set from the full-sha256 citations in tracked text files,
  the payloads' provenance first of all (so nothing mechanical holds the line between freeze and landing); a 12-hex
  pin in prose gets its line by hand and an entry in the test's HAND_PINNED: `tests/test_prefetch_r2.py`, the R2
  freeze record's. Dated 2026-10-04: the HAND_PINNED entry belongs in the FREEZE commit, next to the `-text` line,
  whenever the freeze record pins the test file by 12-hex sha (the horizon read, `tests/test_prefetch_horizon.py`).
  Dated 2026-10-17: two prefixes are left out of citer scans. The export's proof receipts (`FOLDED_CITERS`) are out
  of check 4 and of tools/evidence_pins.py (check 5 binds them); the recovered critic folder (`RECOVERED_PREFIXES`,
  `docs/audits/critic-recovered/`) is out of checks 2 to 4 and 6, so a digest quoted inside it needs no `-text`
  line and no pins-file row (its scripts quote digests in whichever form the reviewer hashed, its manifests the
  folder's own). Files under both stay citation TARGETS. The tool keeps the same two tuples and
  `tests/test_evidence_bytes.py::test_pins_tool_scope_matches_this_file` holds them equal.
- **Registered-experiment arc, minimal form: two commits** (c4c4511 then c23f214; the subject
  style described here is superseded for new commits by the Decision below). (1) "registration + instrument (pre-run;
  critic-gated)": a `docs/BLUEPRINT.md` block, `tools/run_*.py`, `tests/test_*.py`, a dated note in
  `OPEN_QUESTIONS.md`, `.gitignore` negations. (2) "F-NN: ... landed": `results/real/` payload, state and meta
  files, the `FINDINGS.md` entry, dated notes in `OPEN_QUESTIONS.md` and `docs/`, a landing test. Longer arcs add
  commits: runs landed before the finding text (OQ-17: 1d1a7f8, 675a8f6, 0b82e98), dated amendments, void notices
  ("K-3 VOID: ..."); idea-tier docs use "FUTURE_IDEAS: ...". [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]
- **Git log on `main`** (81 commits, 2026-08-29..2026-09-15, one author `sideband <sideband@local>`):
  - Subjects are long and identifier-led: median 102 characters, 7 of 81 at most 72, 24 over 150, longest 1041.
    They start with the register id (15 `F-NN:`, 22 `OQ-NN`, 11 `K-N`, 5 `FUTURE_IDEAS:`, then `Phase N`, `S3`) [withheld: FUTURE_IDEAS not in this repository; see WITHHELD.md]
    and carry process facts in parentheses, e.g. "(pre-run; critic-gated)". No subject on `main` contains a
    sha; shas appear in bodies (20 of 81).
  - No conventional-commit prefixes, with one exception: `83c9bd5 docs: ECOSYSTEM.md - ...`.
  - 76 of 81 have a body (median 27 non-empty lines with all 81 counted, longest 69): prose paragraphs, or bullets of the form
    `- path: what changed` (27 bodies have `- ` bullets). Many close with the suite and lint line (39 bodies carry
    an `N passed` count, e.g. "Suite 450 passed / 5 skipped; lint OK (26 findings)") and, when untracked files
    were left out, an explicit "not part of this commit" note (c4c4511, fa6537e).
  - 76 of 81 end with a `Co-Authored-By: Claude <model> <noreply@anthropic.com>` trailer; the model name varies
    by session (Claude Fable 5 x59, Claude Fable 5.1 x17; HEAD f1aabe4 on this branch says Claude Opus 5.5). The 5
    without a body or trailer: 21b9010, bcaa84e, c93b427 (the v0.x release commits), d8cb7a0, f3d05d4.

- Landing texts are GENERATED from the committed payloads (since 2026-10-02, the stratified coverage read): a
  session script reads both payloads and emits the finding's status line, the block's OUTCOME and every pointer, and
  a second script applies them by exact anchors with each file's line ending preserved; a fix batch reverts the
  files, fixes the generator and re-applies, never patches the output (docs/SHARP_EDGES.md, "Three footguns from
  the first generated landing"). The scripts are session scratch, not committed (since 2026-10-03 they import the committed
  `tools/landing_text.py` for the mechanics); the record is the applied text. Since 2026-10-03 the generator also
  derives every READING word from the payloads: a typed reading beside a paired fragment is the same error class
  (docs/SHARP_EDGES.md, "A generator that types a reading word ...").
- Straddle wording and the said-in-words list belong in the registration block, before the first critic round
  (a lesson adopted 2026-10-02 from the stratified coverage read's lane; no lane has used it yet, so not a
  convention by this file's own rule): every label-bearing readout gets its floor-straddle sentence variants and
  the list of reported cells that must be said in words at landing, written before the design round rather than in
  answer to it. In that lane the straddle sentences arrived as the design round's fourth blocker and several
  said-in-words items as design and confirmation advisories (the PRE-FREEZE ROUND records of the amendment block in
  docs/BLUEPRINT.md); across its six critic rounds (three before the freeze, one recompute, a landing round and its
  confirmation) no blocker was a number: most were sentences (a claim beyond a gate, an unmarked edit to a pinned
  prediction, a misstatement of what the record stores) and two changed the design (the Q2 gate's shape; the
  stage-2 strike rule under a straddle). The landing generator quotes the pinned sentences verbatim, so those are
  words the critic has already read; the generated prose around them is new, and that is where the landing round's
  three blockers were.
- The critic's "what would change my mind" check is run when it is cheap: a standing practice (DR-1, DR-3 and
  DR-4, registered 2026-09-04 as the critic's "what would change my mind" diagnostics, docs/BLUEPRINT.md;
  clean-worktree reruns go back to F-10, docs/METHOD.md), recorded here on 2026-10-02 after the stratified
  coverage read: its recompute round named a clean-clone rerun of the replication as the check that would move its
  verdict; the rerun took 93.3 s of elapsed time against the registered run's 91.9 s and reproduced the committed
  state file byte for
  byte (sha 87f6705bc5f2 on both; the amendment block's OUTCOME in docs/BLUEPRINT.md). A check the critic names and
  the lane can afford is run and its result recorded in the OUTCOME, not argued about.
- The critic's GO is scoped to file shas, and every edit after it is named (R2's freeze, 2026-10-03; one lane, so a
  lesson and not yet a convention by this file's rule): the freeze commit's body lists the first twelve hex of each
  hashed file (`docs/BLUEPRINT.md`, `tools/run_prefetch_r2.py`, `tests/test_prefetch_r2.py`, `OPEN_QUESTIONS.md`,
  `.gitignore`) and says they are recorded in the body "so the block's hash stands"; the block's pre-freeze round
  carries a "POST-GO EDITS, in three batches, every one named" passage (found by that phrase in
  docs/BLUEPRINT.md; the first batch is a one-line docstring correction). Even a docstring line is an edit to a
  hashed file. Open reading: the Decision below says no shas in a message; this body carries file digests and
  "OQ-9", and this file does not settle whether those count.
- **Registrations are generated, and a new CPU readout imports only frozen instruments** (OQ-20, 2026-10-09; one
  lane, so a lesson and not yet a convention by this file's rule). The registration block is emitted by a scratch
  generator (`reg_oq20.py`, not committed) that derives every quoted number from committed files (payloads, metas,
  `tools/e6_gate.py`, git blob ids, `git log`), the landing-generator pattern extended to registrations
  (docs/TASK_RECIPES.md, "Landing texts"). `tools/run_seed_replay.py` imports only the frozen
  `tools/run_noise_floor.py` so that `tools/e6_gate.py`, which it merely reuses, stays out of the frozen
  closure; `tests/test_seed_replay.py` pins the equality of its leg to `e6_gate.pair` instead.
- **Audit folders, two output forms** (`docs/audits/<date>-<slug>/`; dated 2026-10-16; two folders, one of each
  form, so a record of what is and not yet a convention by this file's rule). All nine scripts in the index
  (`git ls-files 'docs/audits/*.py' | wc -l`; the f24 folder's three staged, not committed) resolve the
  repository root from their own location, pin in the header the figures the record states before the rerun,
  write their output beside themselves as LF JSON (`write_bytes` of `json.dumps(...) + "\n"`) and record the
  numpy version in it. They differ on a failed pin. WRITE ONLY ON PASS: the six scripts of
  `docs/audits/2026-10-15-image-audit/` exit 1 before the write, so a passing rerun rewrites its output byte
  for byte and a failing one leaves the committed output as it was (that README, "Files beside this report",
  last paragraph). ALWAYS WRITE: the three scripts of `docs/audits/2026-10-16-f24-support/` write every value,
  each pin's verdict and `all_pins_hold`, then exit 1 if a pin failed, so a figure that does not reproduce is
  on the record beside the figure it fails; a missing-shards refusal exits non-zero with no output (that
  README, "Convention"). Each README states its form.
  Dated note 2026-10-17: `docs/audits/critic-recovered/` is neither form. It holds a selection of the reviewer's
  recovered scratch of 2026-10-01 to 2026-10-16 (308 files under 16 session folders), copied by `recover.py` beside
  it and pinned by its two manifests, its README written by `gen_readme.py` from them; no recovered script runs as
  copied or is re-run by a test (its README), and the folder is pinned `-text` by one glob line, its session folders
  left out of ruff, all of it out of the evidence-bytes citer scans and of the export's tone sweep, and frozen in
  the public cut (one folder, a record of what is). The count command above prints 224 at the lane's index, 215 of
  them under that folder (213 recovered scripts, `recover.py` and `gen_readme.py`); the nine are the two audit
  folders' scripts, and the f24 folder's three were committed in 46a812f, the commit that carried this bullet.
  `python -I docs/audits/critic-recovered/recover.py --source <the 2026-10-16 archive> --date 2026-10-17 --check`
  rebuilds the folder in memory and compares it with the disk, writing nothing (exit 0, "would change 0 of 310
  files", 2026-10-17); `python -I docs/audits/critic-recovered/gen_readme.py --check` does the same for the README.

### Decision (2026-10-01): commit messages follow the harness convention

From the first commit after the harness deploy commit on this branch, commit messages follow the
harness's `/commit` guidance (`.claude/commands/commit.md`, "Step 3"): `<type>(<scope>):
<description>` with a subject of at most 72 characters, imperative, no trailing period; a body
saying what changed, why, and how it was proved, wrapped at 72 columns; the `Co-Authored-By`
trailer last. The strict reading applies: no register ids (`F-NN`, `OQ-NN`, `K-N`, `D-N`), no
task-pack or ledger ids, and no shas anywhere in the message. Traceability runs the other way,
through the record. A commit cannot cite its own sha and no record text cites one yet, so the
route that works is content search: `git log -S'## F-NN' -- FINDINGS.md` for a finding (run
2026-10-01, it returns the landing commit of F-26) and `git log -S'<block title>' --
docs/BLUEPRINT.md` for a registration; a later dated note in the record may add the sha.
Types are commit.md's seven (feat, fix, refactor, test, docs, chore, style). The scope is the
area, never a question or finding id: `harness`, `instrument`, `evidence`, `record`, `core`,
`real`, `experiments`, `tests`, `docs`. A `git revert` keeps its generated subject; the sha it
carries is the one allowed, said aloud. The history before this decision keeps its identifier-led
subjects, and `git log --grep` still finds those.

Facts that still hold: nothing in this tree enforces either format (the 72-character and
identifier checks in commit.md are scoped to the Espalier-Harness source tree); `/commit`
generates the message and the operator approves it. Recorded in ESPALIER_MEMORY.md
("Harness Decisions", 2026-10-01).

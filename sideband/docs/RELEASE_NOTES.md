# Release notes - sideband v0.3.0 (pending)

Dated 2026-09-05. Written against HEAD 8542ef5, the release-hygiene
commit on top of 2e44105 whose contents are listed under [0.3.0] in
CHANGELOG.md. Every number below
was copied from the named repo file as read on that date; counts marked
"this session" were measured with git/python on the author's working tree
on that date. Nothing here is a finding.

License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12); section 5 is the checklist as it stood on 2026-09-05.
Repository URL: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`, folder sideband/ (filled at export).

## 1. What this release is

v0.3.0 is the first public cut of the repository: the code, evidence and
documents at commit 2e44105 plus the release-hygiene commit 8542ef5 (version bump, a
torch-free redaction guard, torch skip guards, a scratch directory for
smoke runs, and the documents written in this pass), and the F-23 commit
on top of it: one added evidence file (results/real/oq16_ha_identity.json),
the dated OQ-16 erratum, the closing finding, and two CPU recompute tools
(tools/e6_gate.py, tools/ha_identity_check.py) with tests. Three version labels appear in the history (v0.1.0, v0.2.0,
v0.2.1, all 2026-08-29) but no git tag exists yet.

Status language, borrowed from the repo's own documents and used
consistently here: **shown** (a registered gate passed and replicated),
**not shown** (a registered gate failed), **unpriced** (a question whose
registered comparator did not deliver a measurement), **qualified** (a
pass whose registered meaning is narrowed by a registered diagnostic).
Three layers are never conflated:

- **existence** - does the telemetry carry information beyond the free
  baseline (DECISIONS.md D-5: *free_lastp*, steering from the target's
  distribution at the last verified position, which every speculative
  decoder already has);
- **conversion** - do such margins become more emitted tokens per verify
  call at a matched drafting budget (the K-3 estimand; docs/ECONOMICS.md
  section 5 pins the win bar at +0.062 tokens per call);
- **reconstruction** - how much of the target's anchor hidden state h_a
  (the verifier's final-norm output at the anchor: the last verified row,
  whose forward produced the next-token distribution p_a; docs/GLOSSARY.md,
  "Anchor") a linear map recovers from the telemetry (OQ-16 Stage R).

No wall-clock or speedup number exists anywhere in the repo (D-9;
docs/ECONOMICS.md header: "nothing in this repo measures wall-clock; the HF
adapter recomputes prefixes and is acceptance-valid only"). Tokens per
verify call is the currency.
Dated erratum 2026-10-16: the quoted ECONOMICS clause was false when written;
the adapter has cropped KV caches by default since b1dae57 (2026-08-29). And
"no wall-clock number exists" is too strong: 59 stats.jsonl files and the run
metas log per-prompt and per-run seconds as provenance (docs/DATA.md quotes
them). What stands: no wall-clock or speedup CLAIM or benchmark exists
(DECISIONS.md D-9, dated note 2026-10-16).

Other house terms used below: *telemetry* is the hardware-observable
stream (S1 = compute-tier weight-slot occupancy on the Llama target,
value-aware; S3 = OLMoE router expert ids, addresses only; S2 = KV pages,
unrun); a *regime* is the world, model pair, seeds and prompt population a
number was measured in (every finding carries one, lint-enforced, D-4); a
*registered run* is one whose cells, readouts and conclusion labels were
pinned in docs/BLUEPRINT.md before it ran; a *state file* (`*.state.jsonl`)
is the per-cluster checkpoint a registered run writes, committed as
evidence because the bootstrap CIs recompute from it; the *critic* is the
reviewer agent in .claude/agents/sideband-critic.md; *void semantics* are
the registered rule for a run whose budget guard breaches (gate metrics
stay unread, one rerun at a fresh seed); a *dated erratum* is the only way
registered text is corrected (never a rewrite). FREETOK is a
deployment-free feature block (the anchor's top-32 next-token ids hashed
into 2048 bins, appended to the free features) and UNION is telemetry
plus that block (FINDINGS.md F-22). The full term list is
docs/GLOSSARY.md.

## 2. Where the science stands

| Layer | Status | Headline number (source) |
|---|---|---|
| Existence at S1 (value-aware compute-tier tap, Llama-3.1-8B-Instruct NF4) | shown, replicated on fresh seeds; not topic-state at the histogram level (F-16) | pinned replication cell L1_concept_k16/off2/linear +0.0141 [+0.0081, +0.0203] top-1 accuracy over the free baseline (F-15; results/real/probes_s1_replication.json) |
| Existence at S3 (pure address stream, OLMoE router expert ids) | shown, replicated; the only address-only positive | +0.0147 [+0.0113, +0.0182] primary and +0.0173 [+0.0133, +0.0221] replication at the pinned cell; up to +0.0721 [+0.0652, +0.0792] at the coarse L3 lens (F-17; results/real/probes_s3.json, probes_s3_replication.json) |
| Existence at S2 (KV pages) | unrun | none (docs/ECONOMICS.md line 25) |
| Conversion, attempt 1: K-3 adaptive block scheduling on frozen probes | not shown (null) | telemetry vs vanilla +0.006860 [-0.015024, +0.025572] tokens per call against the +0.062 bar (F-19; results/real/k3_verdict_s1_arm*.summary.json) |
| Conversion, attempt 2: OQ-15 outcome-supervised head | not shown (conversion-mode null) | head_tel vs vanilla +0.002664 [-0.044719, +0.046727]; head_tel vs head_free -0.081846 [-0.132484, -0.035567], CI-clear negative (F-21; results/real/oq15c_verdict_s3_arm*.summary.json); at the prediction level the telemetry head already lost to the free head, delta_free -0.00286 [-0.00322, -0.00252] (F-20) |
| Earlier actuator: free-information bucket-bias steering | dead at every tested granularity | oracle ceiling at coarse k +0.0014 [-0.0043, +0.0069] acceptance (F-14) |
| Reconstruction (OQ-16 Stage R) | qualified pass, then closed by the dated erratum F-23 (the target is free information; no partition branch claimed) | registered gate: delta_free +0.204984 [+0.153698, +0.288162], delta_noise +0.176469 [+0.130414, +0.251518] (F-22; results/real/oq16_stage_r.json); under the DR-1 support clip the telemetry ridge reaches R^2 +0.253 of h_a; DR-2: FREETOK reconstructs slightly better, tel_vs_freetok -0.004792 [-0.007192, -0.002600]; DR-3: UNION beats FREETOK +0.065180 [+0.062411, +0.067705]; DR-4: the comparator meant to price "beyond p" is CI-clear worse than FREETOK, freetok2_vs_freetok -0.003085 [-0.004984, -0.001280], label COMPARATOR-TOOTHLESS, so "beyond p" was unpriced (F-22 addenda; results/real/oq16_stage_r_dr.json, _dr3.json, _dr4.json); F-23 (2026-09-05): h_a follows exactly from the anchor's full p (full-logit inverse relative error 2.5e-8 median; top-4097 log-probs per-row R^2 +1.0000; top-32 R^2 +0.014; results/real/oq16_ha_identity.json), so the reconstruction is a lossy copy of free information |
| Actuation (OQ-16 Stage A, SD^2-style injection; SD^2 is the hidden-state drafter-steering paper mapped in docs/PRIOR_ART.md) | frozen pre-GPU, then void as a telemetry test by the dated erratum (F-23); the oracle arm survives only as an unregistered free-actuator question outside the lane; the lane has ended | none (docs/BLUEPRINT.md, STAGE-A FREEZE at line 3531 and the OQ-16 DATED ERRATUM + LANE CLOSURE block after it) |

Net: two replicated existence positives, two conversion nulls, one
reconstruction pass whose target proved to be free information (lane
closed by erratum), no actuator run. The kill
criteria K-5 (wall-clock) and K-6 (device economics) in
docs/WHY_THIS_DIES.md are unmeasured.

## 3. Provenance and privacy notes

### 3.1 Absolute operator paths in 30 committed result files

Dated note 2026-10-16 (image audit 2026-10-15, section B item 6): the count
was true on 2026-09-05 and is stale. At HEAD on 2026-10-16, 80 tracked files
under results/real/ and 87 tree-wide carry the author's absolute paths (git
grep -l -E 'Users[\\/]+<name>'; a bare-name search finds 89, adding the author
entry of docs/public_cut/identity.json and an OQ-19 slug), the later [withheld: docs/public_cut/ not in this repository; see WITHHELD.md]
instruments (prefetch, lens, readers) adding keys under args, label_space and
companion_files_filled. Three recorded path kinds ARE read back: the Phase-3
companion paths as basenames by the frozen tools/run_reader_lens.py, the
amendment's rider_v1_preserved.path by tests/test_fullfree_coarse_amended.py,
and a relative backslash harvest_dir in a prefetch payload by
tests/test_prefetch_landing.py, which is why six tests (three, two and one)
were red on a Linux clone until lane A (c41f9f1) handled them test-side;
"inert" below holds for the run metas' key values. The 12 registered command lines of
docs/BLUEPRINT.md's OQ-20 block (and its C:\tmp\oq20_clone) carry the same
checkout path and are kept under this disclosure by the operator's call of
2026-10-16 (dated note there).

30 files under results/real/ record the author's absolute invocation
paths (a Windows home directory containing a first name) as provenance:
176 JSON string values in total, under the keys buckets16, buckets32,
buckets64, buckets512, glue16 and probe_weights (27 files each) and
val_run (14 values across 11 files). They are the K-3 and OQ-15 Stage-C run metas
(k3_*.meta.json, oq15c_*.meta.json), the threshold-search payloads
(k3_threshold_search_arm{2,3,4}.json, oq15c_search_arm{2,6,7}.json) and the
thresholds files k3_thresholds_arm{2,3,4}.json. Counts verified by parsing
every results/real JSON this session.

They are inert: no tool reads those keys back (grep of src/ and tools/ for
the key names this session: no dereference), so a public clone runs
without the paths existing. They are unedited by house rule (results/ is
committed evidence and is never hand-edited, CLAUDE.md), and editing would
break the provenance chain: 9 of the 30 files have their sha256 quoted by
other committed files (verified this session: each threshold-search
payload's sha appears in its thresholds file and in the verdict metas of
both seeds; each k3_thresholds_arm{2,3}.json sha appears in both seeds'
verdict metas and k3_thresholds_arm4.json's in the seed-0 meta (the seed-1
meta binds k3_thresholds_arm4_v2.json)). A history rewrite is likewise out: 31 short
commit hashes cited in FINDINGS.md, DECISIONS.md, OPEN_QUESTIONS.md and
docs/BLUEPRINT.md resolve to real commits (checked this session) and would
be orphaned. The exposure is a first name in a path, not a secret. The
only clean way to remove it would be to re-run those arms on the GPU box
with relative paths and commit new evidence with dated errata; that is an
owner decision and is not recommended by this pass. A forward fix
(store repo-relative paths in future metas) is not implemented here.

### 3.2 docs/ECOSYSTEM.md

The "Sibling projects" section was rewritten on 2026-09-05 to remove
absolute paths and personal folder names; the useful content (which
sibling exports what) is kept, and a dated note in the section says so.
The rest of the file is unchanged and still describes the author's GPU
box (its "Environment facts" section, including Hub access gating on
2026-08-29) and, at line 65, names a personal folder in the salvage
survey; the file's own header still says paths are absolute to the
author's machine. Those parts are a tool map, not registered text, and
can be trimmed by the owner at will.

### 3.3 HANDOFF.md is unpublished by design

HANDOFF.md is the operator-local session log (82,283 bytes on disk this
session). It is untracked and now explicitly gitignored (.gitignore line
61), so `git add -A` cannot ship it. Registered text cites it: FINDINGS.md
once and docs/BLUEPRINT.md six times (grep this session), in the pattern
where a run meta's "-dirty" stamp is attested to come from that untracked
file alone (F-22: "meta bd71358-dirty from the untracked HANDOFF only").
Those citations stay as written; registered text is corrected by dated
errata, never rewritten. A public reader will therefore see references to
a file that is not in the repo, and this note is the explanation.

### 3.4 "-dirty" git stamps and what attests them

80 of the 85 `*.meta.json` files under results/real (counted this session)
record `git_commit` as `<sha>-dirty`, and so do the state-file headers
(for example results/real/oq16_stage_r.json.state.jsonl line 1:
`"git_commit": "bd71358-dirty"`). The stamp is mechanical: `git status
--porcelain` counts the untracked results and scratch files that accrue
while a chain of runs is in flight. What attests that the tracked code was
identical to the named commit is operator statement inside the registered
text, not committed bytes:

- F-15: "both runs' -dirty = untracked results/scratch only,
  operator-attested; tracked src/tests clean".
- F-17: "all -dirty = untracked-only, operator-attested".
- F-21: "every meta binds git_commit '-dirty' mechanically (untracked
  results accrue mid-chain; porcelain counts them - instrument artifact,
  code identical to the named commits)".
- F-22: the registered run's dirt is attributed to the untracked HANDOFF
  alone; the DR-4 addendum records "a clean-worktree byte-identical
  re-run".
- F-20: "a full deterministic rerun of the tool from the sha-verified raws
  reproduced summary and state BYTE-IDENTICAL".

What a stranger can verify without trusting the attestation: the sha256
chain between committed files (harvest metas -> state-file headers ->
payload provenance -> probe-weight meta -> run metas -> summaries; the
mechanisms are named in section 6) and the CPU recomputes in section 7,
which reproduce the registered CIs bit-exactly from the committed state
files. What cannot be verified from committed bytes: the content of the
working tree at run time. Treat "-dirty" as operator-attested, which is
how the findings themselves label it.

### 3.5 Smoke runs no longer overwrite evidence

`experiments/run_all.py --smoke` (the CI step in .github/workflows/ci.yml)
used to write smoke-sized payloads into the same results/*.json files as
the registered full runs, so a local smoke run dirtied committed evidence
(docs/ECOSYSTEM.md line 233 recorded the footgun). It now writes to
results/smoke/, which is gitignored (.gitignore line 63). The full run
(`python experiments/run_all.py`, `make experiments`) still rewrites
results/e0*.json and results/summary.json deliberately; the committed
results/summary.json notes that on the author's box the full run
"outlived the session wall clock" and records no per-run seconds.
Dated note 2026-10-16: the heading holds for run_all.py only. Each experiment
script's own --smoke flag (python experiments/e04_staleness_decay.py --smoke)
still writes its smoke-sized payload over the committed results/ file, as the
image audit reproduced in a clone; the evidence-bytes test and git status
catch it, and the root fix is lane C's.
Dated note 2026-10-16, later: lane C landed the root fix. main(smoke=True) of every script
calls experiments/_util.py smoke_results() first, so a script run on its own, run_all.py and
a programmatic call all write under results/smoke/; e06's partial files follow the same
directory. save_json writes LF on every OS since the same lane: results/e01_verifier_exactness.json
and results/e07_hint_rate.json are stored CRLF today and change line ending when next
regenerated (the evidence-bytes checks report it; none of the seven payloads is sha-cited).
tests/test_experiments_smoke.py runs one script from a scratch copy and checks that the
committed path is untouched and the smoke file is LF.

### 3.6 Redaction guard

`redact_args` (drops any argument whose name equals, or ends in `_` plus,
one of token / secret / password / api_key / apikey before `vars(args)`
lands in a meta; `tokenizer_revision` survives, `hf_token` does not)
moved from src/sideband/real/hf_specdec.py to the torch-free
src/sideband/provenance.py and is re-exported from its old location. Four
tools that wrote `vars(args)` unredacted (tools/k3_threshold_search.py,
tools/run_error_predictor.py, tools/run_posthoc_topic.py,
tools/run_probes.py) now route through it, and
tests/test_tools_and_real.py::test_every_meta_args_writer_redacts fails if
any file under tools/ or src/sideband/real/ writes `vars(args)` without
it. No credential value exists in any tracked file: a grep of results/
for keys ending in token / secret / password / api_key finds only the data
key `bucket_of_token` in the buckets files (this session). Committed metas
are unchanged; the guard is forward-looking.

### 3.7 torch skip guards

tests/test_probes.py::TestD2D3Instrument (4 tests) and
::TestStageEInstrument (2 tests) call `train_probe`, whose lazy `import
torch` (src/sideband/probes.py) made them fail with ModuleNotFoundError on
a `pip install -e ".[dev]"` clone, contradicting the CI contract (only
`.[dev]` is installed, Python 3.12; export note 2026-10-13: the public repository's root workflow installs `.[dev,analysis]`). Both classes now carry the same
`@pytest.mark.skipif(not _has("torch"), reason="needs torch")` guard as
TestTrainProbe. `python -m pytest --collect-only -q` collects 357 tests on
the tracked tree at 8542ef5 (measured in a clean worktree; 362 on a working
tree that also holds the untracked tests/test_e6_gate.py and
tests/test_ha_identity.py; this session).

### 3.8 Author identity and AI-assisted authorship

All 70 commits are authored and committed as `sideband <sideband@local>`
(git log this session): GitHub will not link them to an account. 65 of the
70 commit messages carry a `Co-Authored-By: Claude ... <noreply@anthropic.com>`
trailer, a public disclosure of AI-assisted authorship. Neither can be
changed without the history rewrite that 3.1 rules out.

## 4. Known limitations

1. No LICENSE file; pyproject.toml has no license, authors or urls fields;
   no git tag; the repository URL was not chosen when this was written (the export fills it: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`).
2. The 30 path-bearing result files of 3.1 ship as-is (dated note 2026-10-16: 80 at HEAD; see 3.1).
3. The full test suite is long; the sanity subset is
   `python -m pytest -q tests/test_stats.py tests/test_specdec.py`. Skips
   are torch- / `[real]`-extras- / evidence-gated. The exact run time was
   not measured in this pass.
4. The full synthetic experiment suite is long (the committed
   results/summary.json note; experiments/run_all.py's docstring says
   about 10-15 minutes and the smoke variant about 1-2 minutes, both
   author-box estimates).
5. GPU evidence cannot be regenerated from a clone: the raw arrays are
   gitignored (section 6) and every real-model run needs a CUDA box with
   the gated Llama checkpoints. The intended public verification surface
   is the committed state files (section 7).
6. numpy is unpinned (`numpy>=1.26`); the run metas and
   docs/ECOSYSTEM.md line 232 record numpy 2.3.5, and the section 7
   recompute reproduced the committed CI bit-exactly under numpy 2.3.5
   this session. A future numpy could change percentile arithmetic;
   re-run section 7 after upgrading.
7. State-file row order is load-bearing for the CIs: `paired_ratio_delta_ci`
   (src/sideband/stats.py) draws bootstrap indices positionally, so
   sorting a state file changes the CI (not the point estimate). Do not
   reorder them.
8. The SD^2 "+35% accepted tokens" figure still stands unqualified in
   registered and ledger text (docs/BLUEPRINT.md lines 23 and 560,
   OPEN_QUESTIONS.md line 81, docs/ECONOMICS.md line 57). docs/PRIOR_ART.md
   carries the dated correction (2026-09-04, lines 27-52): +35% / +22% are
   the paper's headline maxima across model pairs, and for this pair at
   k = 8 the paper reports block efficiency 4.44 -> 4.79 under sampling.
   README.md (its "Prior art positioning" section) already uses the corrected wording. Dated erratum
   lines under the four registered sentences were not added in this pass.
9. Stage A never ran. The 2026-09-05 dated erratum (FINDINGS.md F-23)
   struck its telemetry arms pre-GPU because their target is free
   information under D-5; the oracle arm is a free-actuator question
   outside the lane and needs its own registration; the lane has ended
   and the fold-back hard stop holds (docs/BLUEPRINT.md OQ-16 DATED
   ERRATUM + LANE CLOSURE).
10. Regime scope of every real-model number: one model pair, one GPU and
    kernel stack (RTX 3080 Ti, NF4 target), 210-prompt verdict populations
    (F-21 caveats). No shared-benchmark number exists.
11. CI pins Python 3.12 while the author's box runs 3.11.9
    (docs/ECOSYSTEM.md line 219); requires-python is >=3.10. The workflow
    has not been observed passing from inside this repo (no evidence
    in-tree); check after the first push.
    Dated note 2026-10-19: observed on the first push to the release
    repository (the three-folder workflow of the public cut), the repository
    then still private: amber and lockstep passed;
    the sideband job read 4 failed, 716 passed, 39 skipped, the four holding
    on the author's machine and failing on that runner (tests/README.md,
    "Fail, not skip"); three skip under CI by name and one assertion is narrowed since
    the second source commit (CHANGELOG, 2026-10-19).
12. bitsandbytes is required for NF4 loading but is not declared in
    pyproject.toml (docs/THIRD_PARTY.md).
13. Reported by the release read-through, not reproduced here: on Windows
    a faulthandler "access violation" banner can print during
    tests/test_outcome_head.py's subprocess test while the test passes.

## 5. Release checklist for the owner

1. Choose the license for the code and decide whether data, results and
   documents share it or take a separate one; add LICENSE (and a second
   file if split) at the root; state the split in README.md.
2. Set `[project]` license, authors and urls in pyproject.toml; replace
   every repository-URL placeholder (README.md, docs/METHOD.md, this file; filled at export).
3. Work the owner checks in docs/THIRD_PARTY.md: the Llama community
   licenses versus the shipped token-id arrays and vocabulary strings, the
   OLMoE model card, and the SD^2 repository's terms on reimplementation.
4. Decide on the 30 path-bearing files (3.1; 80 at HEAD, dated note 2026-10-16): keep as-is (recommended) or
   re-run on the GPU box with dated errata.
5. Run `python -m pytest -q` and `python tools/lint_findings.py`; commit
   the release documents of this pass on top of 8542ef5 (the hygiene code
   is already committed there).
6. `git tag -a v0.3.0` on that commit (annotated).
7. Optional: `git gc` before the first push.
8. First push; open the Actions tab and confirm the ci workflow
   (checkout, Python 3.12, `pip install -e ".[dev]"` [export note 2026-10-13: `.[dev,analysis]` in the public root workflow], `pytest -q`,
   `python tools/lint_findings.py`, `python experiments/run_all.py --smoke`)
   passes; if it does not, the failure is a release blocker.
   Dated note 2026-10-19: it did not, on the first run; the rule applied: no
   flip until the named skips and the narrowed assertion landed, the owner's
   word on that narrowing of the gate was recorded, and a second run passed
   (CHANGELOG, 2026-10-19, and the private record).
   Dated note 2026-10-19, later: the owner's word on the one-sentence
   approach below was read by 16:43 on the box clock (the private plan
   records it verbatim); the rule above holds for the word on the narrowed
   assertion, asked again at 17:10. A third source commit adds one sentence
   to the root README and tests/README.md telling a reader on another
   machine to set `CI=1` to skip the three named gates; the same rule
   applies to it: no flip until that commit's export is proved and its CI
   run passes.
9. Optional: add dated erratum lines under the four "+35%" sentences of
   limitation 8, pointing at docs/PRIOR_ART.md lines 27-52.

## 6. What is not in this repo

Tracked at 8542ef5: 471 files, 102,135,609 bytes of committed blobs
(`git ls-tree -r -l HEAD`, this session), of which results/ is 371 files
and 100,553,663 bytes; 27 tracked files
exceed 1 MB, the largest being results/real/phase0c_k64_sharp_b3.jsonl
at 3,206,390 bytes. No file approaches GitHub's limits and Git LFS is
not used; .gitattributes sets results/** -text (no line-ending conversion)
so the sha256 bindings hold.

Not tracked (gitignored; sizes measured on the author's disk this
session):

| Item | Files | Bytes | Where its sha256 is committed |
|---|---|---|---|
| results/real/harvest_shadow/*.npz (S1 primary, seeds 0-7) | 8 | 4,257,831,088 (8 x 532,228,886) | `npz_sha256` in results/real/harvest_shadow/shadow_s*.meta.json and in harvest_shadow_summary.json; `state_header.harvest_npz_sha256` on line 1 of the probe and post-hoc state files; `provenance.harvest_npz_sha256` in the probe payloads and k3_probe_weights.meta.json (.gitignore lines 3-8) |
| results/real/harvest_shadow_r/*.npz (S1 replication, seeds 8-11) | 4 | 2,128,915,544 | same pattern, harvest_shadow_r |
| results/real/harvest_moe/*.npz (S3 primary) | 8 | 2,496,223,408 (8 x 312,027,926) | same pattern, harvest_moe |
| results/real/harvest_moe_r/*.npz (S3 replication) | 4 | 1,248,111,704 | same pattern, harvest_moe_r |
| results/real/k3_*.jsonl.byproduct/*.npz (K-3 per-prompt raw arrays: anchors, slots, h_a, analytic acceptance) | 2,160 | 1,797,516,744 | `byproduct_sha256` per file in each run's committed `*.summary.json`; `sideband.outcome_head.verify_byproduct` refuses missing, extra or mismatched files (.gitignore line 29) |
| results/real/oq15c_*.jsonl.byproduct/*.npz (OQ-15 Stage C raws) | 1,710 | 1,441,201,336 | same |
| Total gitignored under results/ | 3,894 | 13,369,799,824 (about 13.4 GB) | |
| Stage-A artifacts: results/real/oq16_recon_weights.npz, oq16_recon_hhat/, oq16_inject_*.pt | 0 | 0 | declared in .gitignore lines 56-58 but never produced; their binding file results/real/oq16_stage_a_export.json does not exist either (ls this session) |
| HANDOFF.md | 1 | 82,283 | not bound; operator log (3.3) |

The CPU tools that read the raws (tools/train_outcome_head.py,
tools/train_recon.py, tools/summarize_harvest.py, tools/audit_harvest.py)
therefore cannot be re-run from a clone; the OQ-15/OQ-16 tools record the
sha256 of every run summary they read in their `*.meta.json` and in line
1 of their state files.

## 7. Recompute one headline number without a GPU

The committed state files are the recompute surface. This reproduces
F-22's registered delta_free (leg 2 of the Stage-R gate) from
results/real/oq16_stage_r.json.state.jsonl with the repo's own estimator;
it ran in under a second this session under numpy 2.3.5 and matched the
committed value bit-for-bit. Keep the file order (limitation 7).

```
python - <<'EOF'
import json, sys, numpy as np
sys.path.insert(0, 'src')
from sideband.stats import paired_ratio_delta_ci
rows = [json.loads(l) for l in open('results/real/oq16_stage_r.json.state.jsonl') if l.strip()][1:]
A = lambda a: [r for r in rows if r['arm'] == a and r['variant'] == 'live']
f, t = A('free'), A('tel')
print(paired_ratio_delta_ci([r['sse'] for r in f], [r['count'] for r in f],
                            [r['sse'] for r in t], [r['count'] for r in t], n_boot=2000, seed=0))
print(json.load(open('results/real/oq16_stage_r.json'))['delta_free']['live'])
EOF
```

Expected, both lines: 0.204983722587619, 0.15369761574819202,
0.28816195871219474 over 84 clusters (FINDINGS.md F-22 prints it as
+0.204984 [+0.153698, +0.288162]). The same pattern recomputes F-19 and
F-21 from the `per_prompt_stats` of the committed `*.summary.json` files,
F-20 from oq15_stage1.json.state.jsonl, and the F-15/F-17 existence
margins from the `_clusters` counts in probes_*.json.state.jsonl; the
critic's own recomputes of those are recorded in the findings.

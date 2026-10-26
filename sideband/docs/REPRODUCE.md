# Reproducing sideband

License: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).
Repository: `https://github.com/Mike-Byrne-AI/specdec-sidechannels`, folder sideband/. Everything below was executed on 2026-09-05 against
HEAD 8542ef5 (2e44105, the Stage-A freeze, plus the release-hygiene commit:
version 0.3.0, torch skip guards, `--smoke` writing to results/smoke/; it
touches no registered text or result).

Three tiers of "reproduce" exist here and are kept apart:

1. The CPU test suite and the synthetic experiments (anyone, minutes).
2. Recomputing a registered number from a committed *state file* - the
   per-cluster rows a tool writes next to its summary json, negated back into
   git as evidence - with the repo's own bootstrap estimator (anyone, seconds).
3. The GPU runs and everything that reads the gitignored raw arrays (the GPU
   box only; section 3).

House terms used below: *tokens per verify call* (t/c) is the throughput
currency - emitted tokens per target forward, prefill excluded; no wall-clock
or speedup number exists anywhere in this repo (DECISIONS.md D-9).
*dpe* = drafted tokens per emitted token, the drafting budget. *CI95* = a
prompt-cluster bootstrap 95% interval, `n_boot=2000, seed=0`, from
`sideband.stats`. A *delta* is always "comparator minus arm" or "arm minus
comparator" exactly as the finding names it. docs/GLOSSARY.md (same docs pass)
collects the rest.

## 1. Fresh-clone quickstart (CPU only, no `make` required)

The Makefile targets are the three raw commands below; `make` is absent on
Windows by default. Python >= 3.10 (pyproject.toml); tested here with 3.11.9,
CI (.github/workflows/ci.yml) uses 3.12.

```
git clone https://github.com/Mike-Byrne-AI/specdec-sidechannels specdec-sidechannels && cd specdec-sidechannels/sideband
python -m venv .venv
# Linux/macOS: source .venv/bin/activate      Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"          # numpy>=1.26 + pytest>=8 only; no torch
python -m pytest -q tests/test_specdec.py tests/test_stats.py   # sanity subset
python -m pytest -q                        # full suite
python tools/lint_findings.py              # findings lint
python experiments/run_all.py --smoke      # CI variant -> results/smoke/ (gitignored)
```

| Step | Expected output | Measured |
|---|---|---|
| install | last line `Successfully installed ... sideband-0.3.0` | about 46 s in the 2026-09-04 fresh clone (scratch record, then 0.2.0) |
| sanity subset | `56 passed` | `56 passed in 11.78s` (this box) |
| full suite, torch + CUDA present | `356 passed, 1 skipped` for the tracked tree at 8542ef5 (the skip: "torch installed; guard path not exercised here", tests/test_tools_and_real.py); `359 passed, 1 skipped` with tests/test_e6_gate.py (3 tests) present; `361 passed, 1 skipped in 475.33s` (this box, 2026-09-05) with tests/test_ha_identity.py (2 tests) as well | `356 passed, 1 skipped in 165.40s (0:02:45)`; re-measured with test_e6_gate.py present `359 passed, 1 skipped in 220.84s (0:03:40)` (this box, RTX 3080 Ti, torch 2.6.0+cu124) |
| full suite, torch-less `.[dev]` venv | 475 collected in tracked files on 2026-10-01 (362 before this session's additions; 357 at 8542ef5, plus tests/test_e6_gate.py and tests/test_ha_identity.py); expected `332 passed, 25 skipped` after the skip-guard fix (inferred, NOT re-measured) | pre-fix scratch record 2026-09-04: `3 failed, 331 passed, 22 skipped in 1416.78s (0:23:36)`, all 3 failures `ModuleNotFoundError: torch` at src/sideband/probes.py:230 |
| lint | `lint_findings: OK (27 findings, all carry regime + tracked evidence)` (2026-10-01; before the tracked check the line ended in "+ evidence") | as expected |
| `--smoke` | 7 lines `=== e0N_... (smoke) ===`, each followed by `[saved] .../results/smoke/e0N_....json`, then `[saved] .../results/smoke/summary.json`; `git status results/` stays clean | 14.15 s wall here; per-run seconds in results/smoke/summary.json 0.5 / 0.46 / 3.39 / 1.13 / 4.54 / 3.35 / 0.58; 63 s in the fresh clone |

Wall-time caveat: the same suite took 2.75 min here and 23.6 min in the
fresh torch-less venv on the same Windows 11 machine; the gap is not
diagnosed (different numpy builds, 2.3.5 here vs 2.4.6 there, are one
candidate). Budget 25 minutes for a torch-less run until someone measures it
again. The 22 to 25 skips are the `[real]`-extras and evidence-gated tests.

Do NOT run `python experiments/run_all.py` without `--smoke` casually: it
rewrites the committed results/e0*.json and results/summary.json evidence
(its docstring says so and estimates 10-15 min CPU; the committed
results/summary.json note records that the v0.2.0 assembly "outlived the
session wall clock" and stores `seconds: null` for every run). Not measured
here.

Dated note 2026-10-19: on a machine other than the author's, the full suite
may refuse three `--conclude-from` reproductions (the lens instrument's
byte-for-byte rider gate); on GitHub's ubuntu runner they did on the first
CI run, with one synthetic prefetch assertion since narrowed, and the three
skip there under the variable CI by name (tests/README.md, "Fail, not skip").

## 2. Recompute a registered number from committed state

Every registered CPU-side result is rebuilt from its `*.state.jsonl` (line 1
is a header binding the inputs by sha256; the remaining lines are one row per
cluster or cell) with the library estimator. Run each snippet from the repo
root; on Windows save it to a file and run `python file.py`. Expected: the
finding's number, bit-exact where the source prints full precision, else to
the printed precision. All eight were run in this session; outputs are pasted
verbatim after each snippet. Arm names in the OQ-16 files (F-22; docs/GLOSSARY.md):
`free` = the 657 logged free summaries of p_a; `tel` = free plus the 2048-dim
slot multi-hot (2705); `noise` = tel with the slot block alignment-destroyed;
`trivial` = the TRAIN-mean predictor; `freetok` = free plus p's hashed top-32
token ids (2705, the token-identity arm); `union` = tel plus that token block
(4753); `unionnoise` = union's alignment-destroyed twin; `freetok2` = freetok
plus a second salted hash valued by top_p (4753). Variant `live` = the real
alignment, `'0'..'4'` = the five stale (target-permuted) control seeds;
"clip" = DR-1's TRAIN-support clip of test features.

### F-19 (K-3 attempt #1) - from `results/real/k3_verdict_s1_arm*.summary.json`

```python
import json, sys, numpy as np; sys.path.insert(0, 'src')
from sideband.stats import paired_ratio_delta_ci
def arr(stem):
    pp = sorted(json.load(open(f'results/real/{stem}.summary.json'))['per_prompt_stats'], key=lambda d: d['prompt_idx'])
    return (np.array([p['n_emitted'] for p in pp], float), np.array([p['n_blocks'] for p in pp], float))
e4, b4 = arr('k3_verdict_s1_arm4')
for c in (1, 3, 2):
    ec, bc = arr(f'k3_verdict_s1_arm{c}')
    print('arm4 vs arm%d' % c, paired_ratio_delta_ci(e4, b4, ec, bc, n_boot=2000, seed=0))
```
Printed: `arm4 vs arm1 (0.00686049817456702, -0.015024412465135483, 0.025571504613919983)`,
`arm4 vs arm3 (0.0069736651524432425, -0.014909166422008346, 0.025690067473614957)`,
`arm4 vs arm2 (0.048862651981209204, -0.007392537919904296, 0.10432746614425849)`.
FINDINGS.md F-19 prints +0.006860 [-0.015024, +0.025572] / +0.006974 [-0.014909, +0.025690] / +0.048863 [-0.007393, +0.104327]: match at the printed 6 dp. The seed-1 pooled t/c and dpe (vanilla 3.020427 / 1.324316 ... gamma-6 3.428206 / 1.750186) also reproduce from `sum(n_emitted)/sum(n_blocks)` and `sum(n_drafted)/sum(n_emitted)`.

### F-21 (OQ-15 Stage C) - from `results/real/oq15c_verdict_s3_arm*.summary.json`

Same `arr` helper with `n_drafted` added; `e7, b7 = arr('oq15c_verdict_s3_arm7')` versus comparators 1, 2, 6. Printed:
`arm7 vs arm1 (0.002663841113839105, -0.044719376618043205, 0.04672687273931539)`,
`arm7 vs arm2 (-0.05042494709029022, -0.1093876711189656, 0.00577161510178088)`,
`arm7 vs arm6 (-0.0818462053757365, -0.13248438490194608, -0.035567418925565815)`;
`arm7 t/c 3.010939077751599 dpe 1.2742347176420175`; comparator t/c 3.00827523663776 / 3.061364024841889 / 3.0927852831273355. F-21 prints +0.002664 [-0.044719, +0.046727] / -0.050425 [-0.109388, +0.005772] / -0.081846 [-0.132484, -0.035567] (match at 6 dp) and the t/c and dpe values at full precision (bit-exact).

### F-22 Stage R (registered run) - from `results/real/oq16_stage_r.json.state.jsonl`

```python
import json, sys, numpy as np; sys.path.insert(0, 'src')
from sideband.stats import paired_ratio_delta_ci
from sideband.recon import stage_r_gate
rows = [json.loads(l) for l in open('results/real/oq16_stage_r.json.state.jsonl') if l.strip()][1:]  # line 1 = header; KEEP FILE ORDER
sse = {}
for r in rows: sse.setdefault((r['arm'], r['variant']), []).append(r['sse'])
cnt = np.array([r['count'] for r in rows if (r['arm'], r['variant']) == ('free', 'live')])
d = lambda a, b, v='live': paired_ratio_delta_ci(np.array(sse[(a, v)]), cnt, np.array(sse[(b, v)]), cnt, n_boot=2000, seed=0)
dn = {v: d('noise', 'tel', v) for v in ('live', '0', '1', '2', '3', '4')}
print('delta_noise', dn['live']); print('delta_free', d('free', 'tel'))
print(stage_r_gate(dn['live'], d('free', 'tel'), [dn[s][0] for s in '01234'])['label'])
for fs in ('free', 'tel', 'noise'): print(fs, np.sum(sse[(fs, 'live')]) / cnt.sum())
```
Printed: 84 clusters, 59,183,104 positions; `delta_noise (0.1764686955579684, 0.13041446942258753, 0.2515175260511939)`; `delta_free (0.204983722587619, 0.15369761574819202, 0.28816195871219474)`; `STAGE-R PASS`; test MSE free 1.0880404988549714 / tel 0.8830567762673525 / noise 1.0595254718253209. All bit-exact against results/real/oq16_stage_r.json (`delta_noise.live`, `delta_free.live`, `gate`, `test_mse`), and F-22 prints +0.176469 [+0.130414, +0.251518] / +0.204984 [+0.153698, +0.288162]. The gate's stale statistics (mean -0.0006930177080524569, sd 0.0020671401789247503, bar 0.005508402828721794) reproduce too. Not recomputable from this file: `trivial_baseline_test_mse` (the registered run wrote no trivial rows).

### F-22 DR-1 / DR-2 - `results/real/oq16_stage_r_dr.json.state.jsonl`

Same loader; the trivial arm has one row set reused for every variant, so `key = lambda a, v: (a, 'live') if a == 'trivial' else (a, v)`, plus per-population masks `pop == 'k3'` / `'oq15'` from the rows and `from sideband.recon import dr1_label, dr2_label`. Printed: `tel_vs_trivial pooled (0.2507840175698831, 0.2393163049799146, 0.2616155335932516)`, k3 (0.24835485489665077, ...), oq15 (0.25316622864106975, ...); `tel_vs_freetok (-0.0047917229020996155, -0.007191593773222577, -0.002600197462770046)`; `freetok_vs_free (0.1738710818638295, 0.164703902477286, 0.1828384291478207)`; `freetok_vs_trivial (0.2555757404719827, ...)`; clip-mode `delta_noise (0.1616921379032632, ...)`, `delta_free (0.16907935896172988, ...)`; labels `DEPLOYABLE-MARGIN CONFIRMED | TOKEN-IDENTITY-NOT-EXCLUDED`. All bit-exact against the summary's `reported_deltas` and `diagnostic_labels`. F-22 prints +0.250784 [+0.239316, +0.261616] and -0.004792 [-0.007192, -0.002600].

### F-22 DR-3 - `results/real/oq16_stage_r_dr3.json.state.jsonl`

```python
from sideband.recon import dr3_label            # loader as above, live variant only
uf, un, ut = d('freetok', 'union'), d('unionnoise', 'union'), d('tel', 'union')
print(uf); print(un); print(ut); print(dr3_label(uf, un))
```
Printed: `(0.0651797160379991, 0.06241090578182812, 0.06770480986506906)`, `(0.078089425878617, 0.07562422378541674, 0.08036844527770323)`, `(0.06997143894009872, 0.06705794066510505, 0.07283045403743675)`, `TELEMETRY-BEYOND-P` (the pinned label name only: after DR-4 "beyond p" is unpriced and DR-3's statement stands qualified - F-22 dated addendum, docs/BLUEPRINT.md DR-4 OUTCOME); per population union_vs_freetok k3 0.06386941060792573 / oq15 0.06646469548237832. Bit-exact against the summary; F-22 prints +0.065180 [+0.062411, +0.067705].

### F-22 DR-4 - `results/real/oq16_stage_r_dr4.json.state.jsonl`

`from sideband.recon import dr4_label; f2f, uf2 = d('freetok', 'freetok2'), d('freetok2', 'union'); print(f2f, uf2, d('free', 'freetok2'), d('freetok2', 'tel'), dr4_label(uf2, f2f))`. Printed: `freetok2_vs_freetok (-0.003084904666688648, -0.00498416470003459, -0.0012800606079713726)`; `union_vs_freetok2 (0.06826462070468775, 0.06578270350142151, 0.07055601138524556)`; `freetok2_vs_free (0.17078617719714084, ...)`; `tel_vs_freetok2 (-0.0017068182354109673, -0.004334366593361788, 0.0006279950674516682)`; `COMPARATOR-TOOTHLESS`. Bit-exact; F-22 prints -0.003085 [-0.004984, -0.001280] and +0.068265 [+0.065783, +0.070556].

### F-19 / F-21 by tool - `python tools/e6_gate.py`

Recomputes every registered tokens-per-call delta, its CI, the +0.062 bar and the pairwise budget guard from the committed `*.summary.json` per-prompt rows (n_boot 2000, seed 0), for every verdict population whose files exist; `--population k3_s1` or `oq15c_s3` selects one; `--json <path>` writes the readouts (never under results/). tests/test_e6_gate.py pins the F-19 and F-21 numbers bit-exact. Output on this tree:

```
[k3_s1] F-19 (K-3 Attempt #1, seed 1)  bar +0.062 tokens/call, guard +0.01
  arm  1 vanilla gamma-4          t/c 3.020427  drafted/emitted 1.324316  n=210
  arm  2 draft_conf               t/c 2.978424  drafted/emitted 1.275681  n=210
  arm  3 probe (a) free           t/c 3.020313  drafted/emitted 1.324403  n=210
  arm  4 probe (c) telemetry      t/c 3.027287  drafted/emitted 1.317033  n=210
  arm  5 fixed gamma-6 control    t/c 3.428206  drafted/emitted 1.750186  n=210
  arm4_vs_arm1   delta +0.006860 [-0.015024, +0.025572]  guard margin +0.0173  -> fails
  arm4_vs_arm3   delta +0.006974 [-0.014909, +0.025690]  guard margin +0.0174  -> fails
  arm4_vs_arm2   delta +0.048863 [-0.007393, +0.104327]  guard margin -0.0314  -> fails
  WIN (all-hold): False

[oq15c_s3] F-21 (OQ-15 Stage C, seed 3)  bar +0.062 tokens/call, guard +0.01
  arm  1 C1 vanilla gamma-4       t/c 3.008275  drafted/emitted 1.329666  n=210
  arm  2 C2 draft_conf            t/c 3.061364  drafted/emitted 1.317048  n=210
  arm  6 C3 head_free             t/c 3.092785  drafted/emitted 1.299950  n=210
  arm  7 C4 head_tel              t/c 3.010939  drafted/emitted 1.274235  n=210
  arm7_vs_arm1   delta +0.002664 [-0.044719, +0.046727]  guard margin +0.0654  -> fails
  arm7_vs_arm2   delta -0.050425 [-0.109388, +0.005772]  guard margin +0.0528  -> fails
  arm7_vs_arm6   delta -0.081846 [-0.132484, -0.035567]  guard margin +0.0357  -> fails
  WIN (all-hold): False
[oq16a_s4] summaries not present - skipped (STAGE-A FREEZE ladder as frozen (F-22 registration); STRUCK by F-23 except arm 8 vs arm 1, live only under a future FREE-ACTUATOR registration)
```

### F-23 (OQ-16 erratum) - `results/real/oq16_ha_identity.json`

Not CPU-reproducible from committed files alone: `python tools/ha_identity_check.py --out <path>` needs the cached Llama-3.1-8B-Instruct checkpoint (the lm_head shard read through safetensors) and the gitignored byproduct npz files, and refuses on any sha mismatch against the four committed summaries. What a stranger can check without them: `python -m pytest -q tests/test_ha_identity.py` (the closed-form recovery is exact on a synthetic unembedding once k >= d + 1 rows are used, and the committed JSON carries the pinned row count and the identity-level numbers), and the JSON's `lm_head.shard_sha256` plus `provenance[*].sha256`, which bind the run to the checkpoint shard and the twelve npz files.

### F-20 (OQ-15 Stage I) - `results/real/oq15_stage1.json.state.jsonl`

```python
import json, sys, numpy as np; sys.path.insert(0, 'src')
from sideband.stats import paired_cluster_delta_ci
rows = [json.loads(l) for l in open('results/real/oq15_stage1.json.state.jsonl') if l.strip()]
hdr, rows = rows[0], rows[1:]
test = set(hdr['split']['test']); cl = {}
for r in rows:
    if r['prompt'] not in test or r['run'] not in hdr['gate_runs']: continue
    c = cl.setdefault(r['prompt'], {})
    for k, v in r.items():
        if isinstance(v, dict) and 'se' in v and not k.endswith('_bin'):
            for key in (k, k.split('_off')[0]):
                a = c.setdefault(key, [0.0, 0]); a[0] += v['se']; a[1] += v['n']
pids = sorted(cl)
d = lambda a, b: paired_cluster_delta_ci(np.array([cl[p][a][0] for p in pids]), np.array([cl[p][b][0] for p in pids]), np.array([cl[p][a][1] for p in pids], float), n_boot=2000, seed=0)
print('delta_noise', d('noise', 'tel')); print('delta_free', d('free', 'tel'))
```
Printed: 42 test clusters, 28,616 positions; `delta_noise (0.0007634988041307618, 0.0003079085032585709, 0.0012145948244439294)`; `delta_free (-0.0028591513187409645, -0.003220433681267988, -0.0025181782143188086)`; per offset off1 (0.0008693897120093675, ...) ... off4 (0.0010543139258839724, -0.0001072870897008869, 0.002161438856061373). Bit-exact against results/real/oq15_stage1.json; F-20 prints +0.000763 [+0.000308, +0.001215] and -0.00286 [-0.00322, -0.00252].

### F-15 / F-17 (Phase-3 existence cells) - `results/real/probes_s1.json.state.jsonl` etc.

```python
import json, sys, numpy as np; sys.path.insert(0, 'src')
from sideband.stats import paired_cluster_delta_ci
stem, space, off = 'probes_s1', 'L1_concept_k16', 2      # probes_s3 uses L1_olmoe_k16
cells = [json.loads(l) for l in open(f'results/real/{stem}.json.state.jsonl') if l.strip()]
by = {c['cell']: c for c in cells if 'cell' in c and not c.get('shuffled')}
sc = sa = n = None
for s in (0, 1, 2):
    c = by[f'{space}|off{off}|c|linear|s{s}']; a = by[f'{space}|off{off}|a|linear|s{s}']
    ps = [p for p in c['_clusters'] if p in a['_clusters']]        # FILE ORDER of the cluster keys, not sorted()
    cs = np.array([c['_clusters'][p][0] for p in ps]); as_ = np.array([a['_clusters'][p][0] for p in ps]); cn = np.array([c['_clusters'][p][1] for p in ps], float)
    sc = cs if sc is None else sc + cs; sa = as_ if sa is None else sa + as_; n = cn if n is None else n + cn
print(paired_cluster_delta_ci(sc, sa, n, n_boot=2000, seed=0))
```
Printed (30 clusters each): probes_s1 `(0.01633622808454858, 0.010824298224328132, 0.021624845790476962)`; probes_s1_replication `(0.014135751580104425, 0.008102460176745908, 0.02025057417088149)`; probes_s3 `(0.014688506229875402, 0.011259628578453312, 0.018209439258365042)`; probes_s3_replication `(0.01729838036400067, 0.013340960232357603, 0.02206313827066782)`. Bit-exact against each payload's `margins` row (and `decision.existence_triples`); F-15 prints +0.0141 [+0.0081, +0.0203] for the replication cell, F-17 prints +0.0147 [+0.0113, +0.0182] and +0.0173 [+0.0133, +0.0221].

| Finding | Recompute surface | Result |
|---|---|---|
| F-19, F-21 | four + four `*.summary.json` per_prompt_stats | match at printed 6 dp; t/c and dpe bit-exact |
| F-22 Stage R, DR-1/2, DR-3, DR-4 | five `oq16_stage_r*.json.state.jsonl` | bit-exact on every delta, CI, MSE and label |
| F-20 | `oq15_stage1.json.state.jsonl` | bit-exact |
| F-15, F-17 | four `probes_*.json.state.jsonl` | bit-exact in file order; see section 4 for what sorting the clusters does |

## 3. What cannot be reproduced without the GPU box or the gitignored raws

- Every GPU run itself: Phase 0a/0b/0c `hf_specdec` runs (audit_k*, sanity_k*, phase0b_*, phase0c_*), the K-3 / OQ-15C arm runs (`tools/run_k3_arms.py`: all summaries, stats, gen, metas and the raw byproducts), containment riders, tap calibration/rider, harvest fidelity riders, and any Stage-A arm (frozen pre-GPU at HEAD, unrun).
- The harvest raws: 24 gitignored npz, 10,131,081,744 bytes (harvest_shadow 8 x 532,228,886 B, harvest_shadow_r 4 x the same, harvest_moe 8 x 312,027,926 B, harvest_moe_r 4 x the same) and everything that reads them: harvest_*_summary.json, harvest_audit*.json, fidelity_calibration*.json, the Phase-3 probe cell accuracies (torch, CUDA) and `tools/export_probe_weights.py`'s self-check. A stranger can verify that the shas are consistently QUOTED across metas, summaries, state headers and weight metas, not that they match bytes.
- The block-level raws: 2,160 k3 byproduct npz (1,797,516,744 B, 12 dirs) and 1,710 oq15c byproduct npz (1,441,201,336 B, 9 dirs), gitignored under results/real/*.byproduct/. Needed for every oq15_* / oq16_* field that is not a per-cluster SSE row: ridge fits, val_mse tables, chosen lambdas, per-head MSEs, binary sidebars, cosines, per-coordinate R2, the stale permutations, the FREETOK / UNION / FREETOK2 feature constructions, the threshold-search evals, and the `oq15_head_weights.npz` refit. CPU-only in principle, not from committed files.
- The registered `trivial_baseline_test_mse` 0.9900697257801255 in oq16_stage_r.json (no trivial rows in that state file); the extended runs' value 0.9900697257801256 recomputes from oq16_stage_r_inv.json.state.jsonl, and a Python `sum()` over the same rows gives ...259 - the documented accumulation-order ULP (unit in the last place, one float64 rounding step).
- The `-dirty` git_commit stamps in every meta and the registration-before-run orderings: operator-attested, not resolvable from committed bytes.

On this box all 3,894 raw files (13,369,799,824 bytes) are present and every sha spot-checked matched (the four run summaries in the oq16 state header, p000/p209 of k3_verdict_arm1, shadow_s0.npz, both weight npz, data/prompts_k3_verdict.jsonl).

## 4. Determinism notes

- Synthetic experiments are deterministic given `--seed`; each results json embeds `_written_unix` (experiments/_util.py), so a byte diff after regeneration always differs - compare with that key dropped. The results/summary.json claim that v0.1 numbers reproduced bit-exact was not re-verified here.
- Policies are compared at identical seeds and telemetry reads use an isolated RNG stream (DECISIONS.md D-6): a policy that reads telemetry must not perturb the shared draft/verify trajectory. Do not "simplify" that away when re-implementing a comparison.
- State-row order is part of the evidence. The point estimate is order-invariant; the bootstrap CI is not, because the index draw is positional. Measured on the F-15 cell above: file-order clusters give [0.010824298224328132, 0.021624845790476962] (the committed CI), while `sorted()` on the string keys ('104' < '13' < '6') gives [0.010915861964508585, 0.022134074632186914] with the identical point 0.01633622808454858. Never sort or dedupe a state file before bootstrapping.
- Accumulation order matters at the ULP level: `np.sum(sse)/np.sum(count)` reproduces the committed test MSEs bit-exactly; Python `sum()` lands 3 ULP off on the tel arm (0.8830567762673528 vs 0.8830567762673525). The bootstrap deltas are unaffected because the estimator does its own sums.
- numpy is unpinned (`numpy>=1.26`). The metas record numpy 2.3.5; the recomputes here ran on 2.3.5 and the fresh-clone pass reported bit-exact agreement on 2.4.6 (scratch record, not a repo file). A future numpy could move the percentile arithmetic.
- CUDA paths are not bit-deterministic by their own admission: results/real/gen_freq.json carries "CUDA sampling is not bitwise deterministic; consumers pin this file by sha256", probes_s1.json provenance says "CUDA probe training uses atomics". The CPU tools are: F-20 and F-22 record byte-identical reruns of train_outcome_head.py and train_recon.py from the sha-verified raws.
- Dated note 2026-10-14: the byte-identical reruns above hold under one numpy wheel and one BLAS thread count. On the synthetic fixture of tests/test_outcome_head.py, train_outcome_head.py's `delta_noise` moved at the 15th decimal between numpy 2.3.5 and 2.4.6 and, under 2.4.6, between OPENBLAS_NUM_THREADS=2 and 24 (docs/SHARP_EDGES.md, "A bit-exact gate crosses a BLAS thread-count boundary under numpy 2.4.6"). The committed Stage-I summary results/real/oq15_stage1.json, its meta and results/real/oq15_head_weights.meta.json record neither a numpy version nor a thread cap, so a bit-exact rerun of the stage-C freeze from the deposited raws is assured only when the numpy wheel and the BLAS thread count match the original run's, which the record does not name (on this box, under numpy 2.4.6, numpy's OpenBLAS, loaded with no thread-cap variable set, read 24, the logical-processor count, and kept it after the thread-cap variables were set later in the same process) (the CPU kernel was not varied: every measurement read Haswell); the real-data sensitivity is unmeasured. The percentile bullet above stands.
- Dated note 2026-10-19: a second machine was tried once, GitHub's ubuntu runner on the release repository's first CI run, the repository then still private (its CPU and kernel are not in its log): three lens-rider reproductions (tests/test_reader_lens_landing.py and its two readers siblings) refused and one synthetic prefetch margin read NEGATIVE where this box reads zero, while four Linux containers on this box's CPU, the last of them matching the runner's numpy, scipy, OpenBLAS build, thread count and distribution, passed all four (tests/README.md, "Fail, not skip"; docs/SHARP_EDGES.md, the 2026-10-19 entry). The runner's CPU is the leading candidate; which operation moves is not measured.

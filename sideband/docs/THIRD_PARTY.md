# Third-party models, libraries and prior art

Status: release-hygiene document, dated 2026-09-05, written against HEAD
8542ef5 (2e44105 plus the v0.3.0 release-hygiene commit 8542ef5). Nothing here is a
finding (findings live in FINDINGS.md with regime tags). House terms not
defined inline (NF4, harvest, probe, anchor, h_a, ridge, K-3, OQ-16) are
in docs/GLOSSARY.md. License names
below are the names the publishers use; this file does not summarize any
license's terms, and the owner must read each license text before the
first push.

License of this repository: MIT (LICENSE at the root of the specdec-sidechannels repository; chosen 2026-10-12).

## Models

No model weights are shipped, and nothing under tests/ or experiments/
loads a model. The three checkpoints below are pulled from the Hugging
Face Hub by the GPU-only adapters in src/sideband/real/ and by the GPU
tools under tools/ (torch is imported lazily; CI never imports it).

Dated note 2026-10-13: two files of trained probe weights ship under
results/real/, k3_probe_weights.npz (8 arrays, the K-3 stage-E export bound
to the S1 Llama harvests) and oq15_head_weights.npz (30 arrays, the OQ-15
Stage-C heads), derived from the harvested activations and tracked since
2026-09-02 and 2026-09-03; "no model weights" above means no checkpoint
weights of the three models. Whether such a probe is "an AI model" under the
Llama licences' naming clause for models trained on Llama outputs is the
owner's reading; not legal advice. Found by the public cut's critic on
2026-10-13.

Two house terms used in the table: a *telemetry source* is the
hardware-observable stream the project reads (S1 = the compute-tier
weight-slot occupancy tapped on the Llama target, which is value-aware;
S3 = the MoE router's chosen expert ids, addresses only; S2 = KV pages,
unrun, docs/ECONOMICS.md line 25). The *target* is the verifier model of
the speculative-decoding pair and the *draft* is the small proposer.

| Model id as pinned in the code | Role here | Pinned in | License name as stated by the publisher |
|---|---|---|---|
| meta-llama/Llama-3.1-8B-Instruct | target (verifier) of the pair, loaded 4-bit NF4 through bitsandbytes for every registered real-model run (one committed sanity run, results/real/sanity_k512_bf16.meta.json, records target_load bf16; the NF4 path is the --load-4bit branch of src/sideband/real/hf_specdec.py); also the S1 harvest model | src/sideband/real/fidelity_rider.py:92, src/sideband/real/shadow_telemetry.py:332, tools/calibrate_fidelity.py:57, tools/k3_containment_rider.py:63, tools/run_k3_arms.py:165 | Llama 3.1 Community License |
| meta-llama/Llama-3.2-1B-Instruct | draft of the pair (bf16) | tools/k3_containment_rider.py:64, tools/run_k3_arms.py (the --draft default), src/sideband/real/hf_specdec.py:31 (docstring example) | Llama 3.2 Community License |
| allenai/OLMoE-1B-7B-0125-Instruct | the S3 source: the mixture-of-experts model whose router expert ids are the pure address-stream telemetry of F-17/F-18 | src/sideband/real/moe_telemetry.py:197, src/sideband/real/fidelity_rider_moe.py:77, tools/calibrate_fidelity_moe.py:54; recorded as "model" in results/real/harvest_moe/*.meta.json and results/real/fidelity_calibration_olmoe.json | see the model card (the repo records no license name for this checkpoint); dated note 2026-10-11: Apache 2.0, the name the model card states (its front matter `license: apache-2.0` and its "License and use" section) at snapshot b89a7c4, the revision in the local Hub cache and the one the Hub API returned on 2026-10-11 |

Dated note 2026-10-12: no committed harvest meta records a checkpoint
revision. The 24 metas under results/real/harvest_shadow, harvest_shadow_r,
harvest_moe and harvest_moe_r record the model id, the harvester's git
commit and the array sha256 (`model`, `git_commit`, `npz_sha256`), and none
carries a revision or snapshot field. The record pins snapshots elsewhere:
b89a7c4 as the replay source of the OQ-9 prefetch readouts over the same
S3 harvests (`replay_source.snapshot` in results/real/prefetch_r2_s3.meta.json,
prefetch_r2_s3_r.meta.json, prefetch_horizon_s3.meta.json and
prefetch_horizon_s3_r.meta.json, each with `replay_source_matches_pinned`
true), and the Llama-3.1 target snapshot 0e9e39f2 in
results/real/oq16_ha_identity.json. The harvests' own metas carry no such
field, so the harvested revisions are not pinned; they are inferred, and
the basis of the inference is that the local Hub cache holds one snapshot
of each checkpoint (OLMoE b89a7c4, its cache directory dated 2026-08-30 to
2026-08-31, no later than the S3 metas' entry into git, 2026-08-31 primary
and 2026-09-01 replication; Llama-3.1-8B-Instruct 0e9e39f2, dated
2026-01-14, before the S1 metas' entry of 2026-08-30 primary and 2026-08-31
replication). The OLMoE licence name above was read from that snapshot,
b89a7c4.

Access note: docs/ECOSYSTEM.md (lines 224-227) records that the Llama 3.1
and Llama 3.2 checkpoints sit behind separate Hub gates; each license must
be accepted on huggingface.co before `hf download` succeeds.
Dated note 2026-10-11: the line range above is stale; the gate note is the
ECOSYSTEM bullet that opens "Llama-3.2 access is gated OFF for this
account".

## What of the models' outputs is in this repository

| Artifact | Count | Content | Not present |
|---|---|---|---|
| results/real/*.gen.jsonl | 22 files (git ls-files, this session) | integer token-id arrays (`generated_ids`) emitted by the Llama pair under speculative decoding, plus prompt indices and lengths; one row per prompt of a committed run | no decoded text anywhere in the tree |
| results/real/glue_*.json | 10 files; 9 carry 50 `text` fields each, 450 in total, and glue_phase0a_analysis.json carries none (counted this session) | single tokenizer-vocabulary strings: the frequency-derived glue (function-word) token lists; a *glue bucket* is a vocabulary cluster dominated by such tokens and is excluded from every steering gate (DECISIONS.md D-7) | no generated text |
| results/real/buckets_k*.json, buckets_olmoe_k*.json | label spaces | one k-means cluster id per vocabulary token, derived from the rows of each model's unembedding (lm_head) matrix | no weights |
| results/real/harvest_*/*.meta.json, *.summary.json, probes_*.json, oq15_*.json, oq16_*.json and the rest of results/real/ | aggregate statistics, probe accuracies, per-cluster error sums | derived numbers from forward passes | the raw arrays they summarize (hidden states, slot sets, top-32 distributions) are gitignored; see docs/RELEASE_NOTES.md, "What is not in this repo" |

Whether any redistribution or attribution condition in the Llama
community licenses reaches generated token-id arrays and vocabulary
strings has not been determined in this repo; nothing here has read or
summarized those licenses. This is an owner check before the first push.
The gen.jsonl files cannot be removed without breaking sha256 bindings
recorded in the run metas.

## Prompts and datasets

No third-party dataset is used. Every committed prompt set
(data/prompts.jsonl, prompts_k3_verdict.jsonl, prompts_oq15_val.jsonl,
prompts_oq15_verdict.jsonl, prompts_oq16_verdict.jsonl) is produced by a
committed deterministic generator (data/make_prompts.py,
data/make_prompts_oq15.py, data/make_prompts_oq16.py); a grep of data/*.py
for load_dataset / sharegpt / alpaca / huggingface returns nothing (this
session).

## Libraries

Constraints are those in pyproject.toml (v0.3.0). License names for these
packages are not recorded in this repo; the owner should confirm them from
the installed package metadata (`pip show <pkg>`) at release time rather
than from this table.

| Package | Constraint | Extra | Used for |
|---|---|---|---|
| numpy | >=1.26 | core | everything CPU-side: the verifier (src/sideband/specdec.py), the synthetic world, the bootstrap CIs (src/sideband/stats.py), the ridge heads and the reconstruction |
| pytest | >=8 | dev | the test suite (357 tests collected on the tracked tree at 8542ef5 this session, in a clean worktree) |
| scipy | >=1.11 | analysis | tools/build_concept_groups.py:66-68 only (sparse graph, connected components) |
| scikit-learn | >=1.3 | analysis | tools/build_concept_groups.py:67-69 only (SpectralClustering, AgglomerativeClustering) |
| torch | >=2.3 | real | GPU adapters under src/sideband/real/; probe training via the lazy import in src/sideband/probes.py |
| transformers | >=4.44 | real | model loading and BitsAndBytesConfig (src/sideband/real/hf_specdec.py:956-958) |
| bitsandbytes | not declared in pyproject.toml | (needed with `real`) | NF4 4-bit quantization of the target; its version is recorded into every run meta (src/sideband/real/hf_specdec.py:1120-1133) |
| accelerate | not declared; not imported by repo code (grep this session) | (recorded on the GPU box only) | device placement inside transformers, if at all - unverified |

Versions recorded on the author's GPU box (docs/ECOSYSTEM.md lines 219-220
and 232): Python 3.11.9, torch 2.6.0+cu124, transformers 4.57.3,
accelerate 1.12.0, bitsandbytes 0.49.1, numpy 2.3.5. CI
(.github/workflows/ci.yml) installs only `.[dev]` on Python 3.12. [export note 2026-10-13: the public repository's root workflow installs `.[dev,analysis]`; the private workflow this sentence describes is not exported]

## Prior art reimplemented, not vendored

A grep of src/, tools/, experiments/, tests/ and data/ for "vendored",
"copied from", "adapted from", "ported from", "SD-square" and "ETH-DISCO"
finds no hits beyond two docstring phrases reading "imported from" that
match "ported from" as a substring (src/sideband/real/__init__.py line 4,
tools/lint_findings.py line 4; neither refers to third-party code); no
third-party source file is included.

- **Speculative sampling (Leviathan et al. 2023 / Chen et al. 2023).**
  The exact rejection scheme is implemented in src/sideband/specdec.py;
  docs/PRIOR_ART.md (lines 64-66) records that losslessness is theirs and
  that F-0/F-1 only refuse to take it on faith. D-3 makes that file the
  single source of verifier math.
- **SD^2, "Steering Pretrained Drafters during Speculative Decoding"**
  (recorded in docs/PRIOR_ART.md line 20 as arXiv 2511.09844, AAAI 2026,
  with the public code repository named there; PRIOR_ART.md line 4 says
  to re-verify arXiv ids before citing externally, and this file inherits
  that caveat). The OQ-16 Stage-A actuator in
  src/sideband/real/steer_inject.py is a reimplementation of SD^2's
  "merged" MLP up-projection injection from a reading of the paper and the
  public code on 2026-09-04 (module docstring, lines 5-12). Disclosed
  deviations, from that docstring and docs/PRIOR_ART.md lines 27-52: a
  rank-r factorization (LayerNorm -> U -> per-layer V, r = ADAPTER_RANK =
  512, zero-initialized) instead of SD^2's single full-rank
  zero-initialized linear map; a frozen drafter where SD^2 fully fine-tunes
  it; a single anchor-position vector (the true h_a for the oracle arm, a
  CPU ridge reconstruction for the deployable arms) instead of SD^2's
  three-layer g_t. Stage A never ran: no adapter, export, or GPU run
  exists; its telemetry arms were struck pre-GPU by the dated OQ-16 erratum
  (FINDINGS.md F-23), and the oracle arm survives only as an unregistered
  free-actuator question. Whether the SD^2 repository's license places
  conditions on independent reimplementations is an owner check; it was
  not read here.
- **Everything else** (HashSketch, the synthetic concept-HMM world, the
  bucket-bias and posterior-bias mechanisms, the K-3 scheduler, the
  outcome heads, the reconstruction ridge) is original to this repo.
  docs/PRIOR_ART.md maps the surrounding literature (EAGLE-3, FlexDraft,
  SpecDec++, SP-MoE, the side-channel papers) as positioning, not as code.

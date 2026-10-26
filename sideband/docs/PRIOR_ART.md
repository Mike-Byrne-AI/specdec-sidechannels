# Prior Art Map

Format per entry: what it claims / what it leaves open / regime + relevance.
Compiled 2026-08; re-verify arXiv ids before citing externally.

## Where this project sits

The occupied cells: steering drafters with verifier **hidden states** (SD^2),
multi-layer target **features** as draft input (EAGLE-3), **bonus-token**
calibration (FlexDraft), and draft-predicts-target-experts for **prefetching**
(SP-MoE — the reverse direction of ours). The side-channel literature proves
access patterns leak token-level information. The unclaimed cell this repo
targets: **address-stream-only observability steering a draft** — no
activation values, no logits leaving the device. Our ceiling is SD^2's number;
our contribution is what survives the observability constraint (OQ-6).

## Speculative decoding + steering

- **SD^2 — "Steering Pretrained Drafters during Speculative Decoding"**
  (arXiv 2511.09844, AAAI 2026; code: github.com/ETH-DISCO/SD-square).
  Claims: a steering vector from verifier hidden states at the last verified
  position, added to the drafter's MLP hidden states, yields +35% accepted
  tokens / +22% throughput on Llama-3.1-8B + Llama-3.2-1B.
  Leaves open: any observability constraint — it reads full hidden states.
  Regime/relevance: our exact model pairing; our **upper baseline** and the
  denominator of OQ-6.
  DATED CORRECTION (2026-09-04, from the arXiv HTML full text and the
  public code, read for the OQ-16 Stage-A freeze): the "+35% / +22%" are
  the paper's headline MAXIMA across model pairs ("up to 35% under
  standard sampling and 22% under greedy"), not the Llama-3.1-8B +
  Llama-3.2-1B numbers. Table 1 for our pair — REGIME: draft length
  k = 8 (blocks of 9), batched decoding (batch 12), <= 128 output
  tokens, mean of three seeds at T = 1, UltraChat held-out validation
  as the reported column, unquantized models (no 4-bit anywhere in the
  paper; training in bf16) — block efficiency tau (accepted+1 per
  block) pretrained 4.44 -> distilled 4.58 -> SD^2 4.79 under sampling
  (T=1; speedup 1.07), and 4.51 -> 4.89 -> 5.04 under greedy (speedup
  1.11) — i.e. +0.35 / +0.53 tokens per block over the pretrained
  drafter AT k = 8. Our lane runs gamma = 4 (blocks of 5, ceiling 5 <
  their 9), NF4 target, batch 1, 256 tokens: the reachable fraction of
  a k = 8 gain at k = 4 is unmeasured, so their number is a cross-gamma
  prior, not a bar for ours. Mechanism, from the code (src/models/llama.py,
  src/model.py, main.py): g_t = W_hml[h_t, m_t, l_t] from verifier
  layers 3, L/2, L-2 at the last verified position (W_hml initialized
  as a sum of identities, then LayerNorm); a zero-initialized linear
  map from g_t to one d_ff-dim bias PER drafter layer ("merged": added
  to the up-projection output before the SiLU gate product, every
  layer); refreshed after every verify; loss KL (code default TVD) to
  the verifier on verifier-generated synthetic text with random block
  offsets; the drafter is FULLY fine-tuned alongside ("critical to the
  performance improvement", their Fig. 6 ablation, frozen-drafter
  steering is weaker); 1xA100-80GB, 6 epochs UltraChat + 1 ShareGPT.

- **EAGLE-3** (Li et al.). Claims: draft consumes multi-layer target features;
  3.0–6.5× speedups. Leaves open: requires training a bespoke draft head with
  full feature access. Relevance: the far ceiling of "target-informed
  drafting"; not observability-constrained.

- **FlexDraft** (arXiv 2605.20022). Claims: bonus-token-guided calibration of
  the draft. Relevance: closest *free-information* relative — reinforces D-5
  (any telemetry claim must beat what the bonus token / last verified p
  already gives).

- **Leviathan et al. 2023 / Chen et al. 2023** — the exact rejection scheme
  this repo implements verbatim (specdec.py); losslessness is theirs, our
  tests just refuse to take it on faith.

- **Medusa / Kangaroo / LayerSkip / Token Recycling** — self-drafting and
  head-based families. Relevance: alternative draft sources; orthogonal to
  the steering question, useful later as stronger baselines.

## MoE routing as signal

- **SP-MoE** (arXiv 2510.10302). Claims: the *draft* predicts the *target's*
  expert routing to prefetch experts. Leaves open: the reverse direction —
  using the target's realized routing to inform the draft. Relevance: proves
  routing is predictable across the pair; we invert the arrow.

- **MoE-Spec** (arXiv 2602.16052), **ELDR** (arXiv 2607.00466): MoE-specific
  speculative decoding / expert-locality results. Relevance: regime detail
  for Phase 2's OLMoE/Mixtral harvesting.

## The signal exists (side-channel literature)

- **"I Know What You Said"** (arXiv 2505.06738, USENIX Security 2025):
  embedding-cache access patterns leak token values.
- **"Spill The Beans"** (arXiv 2505.00817): cache side channels recover
  80–90% of API keys / ~40% of English text from LLM serving.
- **Confidential-computing survey** (arXiv 2605.03213): flags speculative-
  decoding access-pattern analysis as unstudied.
  Relevance: these prove the address stream carries token-level information —
  as an *attack*. We are the constructive dual: same channel, cooperating
  endpoint. They also mean the hardware premise has a security review in its
  future; note it in Phase 5.

## Sparsity, memory architectures, prefetching

- **HashedNets** (Chen et al. 2015): the hashing trick for weights — the
  origin of the original (dead) Phase 1; D-1 explains why it can't be the
  telemetry source (access set is input-independent when dense).
- **Deja Vu / PowerInfer**: contextual activation sparsity — the regime where
  a dense model's *effective* access set becomes input-dependent; the shadow
  telemetry adapter is their observational cousin.
- **Lample et al. PKM / Meta Memory Layers**: product-key memory — a native
  key-addressed regime where the address stream is the computation; the best
  long-term home for this idea if MoE routing pans out.
- **Hashemi et al.** (learned memory-access prediction): ML on address
  streams for prefetching — evidence the stream is learnable at hardware
  timescales, which is what the sidecar needs.

## What would falsify the novelty claim

A paper steering a draft from access patterns / routing indices *without*
values crossing the boundary. Closest misses as of compilation: SP-MoE
(wrong direction), SD^2 (full hidden states). Re-search before any writeup:
"speculative decoding" x {routing, access pattern, side channel, prefetch}.

## v0.2.0 additions (emergent-track relatives)

- **TriForce** — hierarchical speculative decoding using the target's own
  sparse/retrieved KV as its draft. Leaves open: the observability-
  constrained version — page IDS only, no values, consumed by a SEPARATE
  draft. Relevance: nearest relative of OQ-8; also evidence KV locality
  carries draftable signal.
- **SpecDec++** — adaptive candidate (block) length via a trained
  acceptance-prediction head on draft-side features. Leaves open: telemetry
  features and a failure taxonomy (which rejections are which). Relevance:
  OQ-10's adaptive-gamma relative; cite when building it.
- **LLMZip / ts_zip lineage** — LLM + arithmetic coding for lossless text
  compression (rate-optimal with the pricing model). Leaves open (to
  verify, not assume): draft-only decompression with byte-exact replay,
  the hint-rate tradeoff, and rejection-rate-as-attestation. Relevance:
  OQ-7 must position against this lineage before any novelty claim.
  Dated note 2026-10-11: the first 'leaves open' item does not hold for the
  format, rank coding with one model on both ends; see correction (d) in the
  OQ-7 cell's dated note below (LLMZip's own v1 coded token ranks with zlib,
  and the rank cell has stayed occupied since). Byte-exact replay is a
  separate question.

## v0.2.1 additions (prior-art deep dive, 2026-08-28)

- **PEARL** (ICLR 2025, arXiv 2408.11850) — pre-verify/post-verify run draft
  and target in parallel with adaptive draft length ("mutual waiting
  problem"). Leaves open: the concurrent draft receives NO signal from the
  in-flight verification. Relevance: the schedule half of OQ-11 exists,
  blind. **AMUSD** — asynchronous multi-device decoupling of draft/verify.
- **FlexDraft** (updated reading) — names parallel drafting's core problem:
  uncertainty in the bonus token and accepted length while drafting
  concurrently. Relevance: OQ-11's streamed anytime posterior is partial
  information about exactly this unknown.
- **ConFu** (arXiv 2603.08899) — "contemplate tokens"/soft prompts make the
  target expose intermediate-reasoning signals as continuous embeddings that
  guide the draft. Leaves open: observability (values cross the boundary)
  and an unmodified target. Relevance: closest anticipatory-signal work;
  ideal comparator for measuring the observability tax (OQ-6/OQ-11).
- **DREAM** — target intermediate-layer features as TRAINING supervision for
  multimodal drafts (not runtime streaming). **Draft&Verify / LayerSkip
  lineage** — early layers as the draft, shared device. Independent evidence
  that early/mid-forward state is draft-informative; a refusal-probe line
  (arXiv 2605.28553) shows linear decodability from intermediate activations
  well before the final layer.
- **SpecPIM** — speculative decoding mapped onto processing-in-memory via
  architecture/dataflow co-exploration. **HPIM** (arXiv 2509.12993) —
  SRAM-PIM + HBM-PIM running in parallel for memory-bound LLM decode.
  Relevance: the hardware substrate of the original intuition exists as a
  COMPUTE story; the information-channel use of the memory side remains
  unclaimed. **SpecMamba** — FPGA spec-decode co-design lineage.
- **SD² limitations (their own)** — requires verifier hidden-state access;
  hidden-state intervention can derail generation. Relevance: names our
  constraint as their limitation; q-only steering is lossless by
  construction (F-0).
- **OQ-7 cell**: a granted patent (US 12,547,833) covers LLM+arithmetic-
  coding text compression REQUIRING the same LLM on both sides — the
  symmetric version is claimed; freedom-to-operate diligence needed.
  **PMATIC** (arXiv 2601.17684) formalizes prediction-mismatch in
  model-driven compression and tolerates bounded mismatch — validates the
  determinism dependency and is the tolerate-vs-eliminate alternative.
  **Speculative KV coding** (Doubleword) — predictor-model-driven arithmetic
  coder for KV caches, explicit spec-decode analogy, but SYMMETRIC (predictor
  on both sides) and on activations. The asymmetric token-stream bundle
  (target-encode, draft-only-decode, hint-rate tradeoff, attestation)
  remains unclaimed as of this pass.
  Dated note 2026-10-11 (four corrections from the 2026-10-09 review of the
  siblings amber and lockstep, each re-verified on 2026-10-11; the write-up
  cites this note, not the sentences above). (a) US 12,547,833 B2 (Dell
  Products L.P.; filed 2023-12-27, granted 2026-02-10; 19 claims) does not
  REQUIRE the same LLM on both sides. Its independent claims 1, 6 and 11
  each recite a rolling-window LLM next-token probability mass function, the
  replacement of the last token by a higher-probability predicted token, and
  that PMF fed to an arithmetic coding scheme; the loss is recited by claim
  1 ('incurs a loss in compression') and by dependent claims 9 and 12 under
  claims 6 and 11, and dependent claim 19 names the lossless case, the
  predicted token equal to the last token; decompression appears only in
  dependent claims 5, 10, 14, 16 and 17, none of which names the LLM; the
  same-LLM decoder sits in the description, not the claims (read from the
  review's transcription of the USPTO grant PDF and from the Google Patents
  claim listing; a textual reading, not legal advice). 'The symmetric
  version is claimed' is withdrawn: every independent claim requires the
  replacement step, and whether a coder without one falls inside them is a
  question this record does not answer. (b) PMATIC is arXiv 2601.10678,
  'Synchronizing Probabilities in Model-Driven Lossless Compression' (Adler
  and Tang, v1 2026-01-15); arXiv 2601.17684 is 'A Model-Driven Lossless
  Compression Algorithm Resistant to Mismatch' (Hu and Tang, v1 2026-01-25),
  a different mismatch-tolerant coder that is relevant in its own right
  (both abstract pages fetched 2026-10-11; amber made the same correction as
  its F-14 row E13). (c) 'The asymmetric token-stream bundle ... remains
  unclaimed' does not hold as a bundle: coding LLM output with a model other
  than its generator is published (Rinberg, Carrell, Henniger, Carlini and
  Warr, arXiv 2604.02343, v1 2026-02-09, in the paper's own setup 'Opus as
  the generator and Mistral-7B-Instruct as the compressor'); compression of
  LLM-generated text via next-token prediction is published (Mao, Pirk and
  Xue, arXiv 2505.06297, v1 2025-05-07, title-level); and verifying
  generated tokens by recompute against a trusted reference is published
  (DiFR, Karvonen et al., arXiv 2511.20621, v1 2025-11-25; abstract page
  fetched 2026-10-11 and saved beside the review's texts). What the review's
  search did not find, a search-scope statement and not a novelty claim, is
  narrower than the bundle: a trace captured as a byproduct of serving-time
  speculative decoding, with its hint channel. Neither was built: amber's
  archive (its src/amber/real/archive.py) is a separate pass that encodes
  with the draft's teacher-forced logits and decodes with the draft alone,
  so both sides are the draft. (d) 'Leaves open (to verify, not assume):
  draft-only decompression with byte-exact replay' in the LLMZip / ts_zip
  entry above does not hold for the format, rank coding with one model on
  both ends: LLMZip's own v1 (arXiv 2306.04050, v1 2023-06-06) already codes
  the sequence of token ranks with zlib, its 'LLaMA+zlib' scheme (read from
  the paper's full text), and rank-based LLM compression continues through
  Nardone and Ferragina (arXiv 2607.24192, v1 2026-07-27, thresholded symbol
  ranking; abstract page fetched 2026-10-11 and saved beside the review's
  texts); the review names Llamazip, AlphaZip, FineZip and LLMc in the same
  cell (agent output, not re-verified here). Byte-exact replay is the
  separate question, answered for amber's archives on one box by an fp32 pin
  (docs/DECODE_CONTRACTS.md). amber's rank codec therefore sits in an
  occupied cell; what its record contributes is measurements, the
  order-stability census by rank depth and the cross-dtype decode-failure
  rates (docs/DECODE_CONTRACTS.md, whose 'What carries over' section also
  names exllamav3's model_diff as prior art for the by-depth readout, agent
  output), not the format. Sources: the arXiv abstract pages fetched on
  2026-10-11 and, where stated, the full texts the review downloaded on
  2026-10-09; the Dell claims from two independent renderings of the grant.

## 2026-10-18 additions (the cold read of that date; each entry fetched and read on 2026-10-18)

Added after the cold read recorded in docs/PUBLIC_CUT_PLAN.md 15.8: directly [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
relevant work the map did not name, each with the line it bears on.

- **Softmax bottleneck.** Finlayson, Ren and Swayamdipta, "Logits of
  API-Protected LLMs Leak Proprietary Information" (arXiv 2403.09539, 2024):
  the softmax bottleneck confines a model's outputs to a linear subspace of
  dimension equal to the hidden size. Carlini et al., "Stealing Part of a
  Production Language Model" (arXiv 2403.06634, 2024): recovers the embedding
  projection layer up to symmetries from API access. Bears on F-23: the
  final-norm state is the lm_head input, so with the lm_head matrix of full
  column rank it follows from the full logits the verifier holds; neither paper
  claims state recovery. docs/IDEAS.md line 247 concedes the order of events: [withheld: docs/IDEAS.md not in this repository; see WITHHELD.md]
  "textbook prior art (Finlayson 2024, Carlini 2024) that nobody in the lane
  applied".
- **MoE routing tracks token identity.** Xue et al., "OpenMoE" (arXiv
  2402.01739, 2024): routing decisions depend mainly on token IDs with little
  regard to context ("Context-Independent Specialization"), set early in
  pre-training. Muennighoff et al., "OLMoE" (arXiv 2409.02060, 2024), the paper
  of the base model behind S3's checkpoint (its section 5.4 analyses
  OLMoE-1B-7B; S3 used OLMoE-1B-7B-0125-Instruct): vocabulary specialization of
  the experts, later layers specializing on predicted output token IDs. Bears on
  F-24 at S3: a free baseline without token ids leaves out what routing follows
  there; consistent with the absorption measured, not a prediction of it (F-24's
  dated note of 2026-10-18).
- **Future-token information in hidden states.** Pal et al., "Future Lens"
  (arXiv 2311.04897, 2023): a single hidden state at some GPT-J-6B layers
  approximates the model's predictions for subsequent tokens with over 48%
  accuracy. Wu, Morris and Levine, "Do language models plan ahead for future
  tokens?" (arXiv 2404.00859, 2024): hidden states carry information to later
  steps; pre-caching versus breadcrumbs. Bears on K-2's steelman: hidden states
  carry information about later tokens, so the existence question was not closed
  in advance.
- **Probing practice.** Xu et al., "A Theory of Usable Information Under
  Computational Constraints" (arXiv 2002.10689, 2020): predictive V-information.
  Pimentel et al., "Information-Theoretic Probing for Linguistic Structure"
  (arXiv 2004.03061, 2020): use the highest-performing probe available. Hewitt
  and Liang, "Designing and Interpreting Probes with Control Tasks" (arXiv
  1909.03368, 2019): control tasks and selectivity. Bears on the reader every
  K-2 label is scoped to: the record's readers were untuned and scored on top-1
  accuracy, and at F-15 and F-17 read raw inputs (F-24 onward z-scores h_a);
  these name the standard a stronger reader meets.
- **Routing as signal.** Li and Zhou, "Your Mixture-of-Experts LLM Is Secretly
  an Embedding Model For Free" (arXiv 2410.10814, 2024): router weights serve as
  an embedding model without finetuning. Yona et al., "Stealing User Prompts
  from Mixture of Experts" (arXiv 2410.22884, 2024): Expert-Choice-Routing tie
  handling leaks a batch-mate's prompt. Bears on the MoE routing section above:
  two published forms of "the signal exists" and of its leak.
- **Evaluation default.** Xia et al., "Unlocking Efficiency in Large Language
  Model Inference: A Comprehensive Survey of Speculative Decoding" (arXiv
  2401.07851, 2024), whose repository is Spec-Bench, "a comprehensive benchmark
  designed for assessing Speculative Decoding methods across diverse scenarios".
  Bears on the population: the record's prompt sets are templated prompts in
  three families (data/prompts.jsonl, data/make_prompts.py), not a benchmark
  slice such as Spec-Bench's, and a reviewer would ask for one.

Sources: the arXiv abstract pages fetched on 2026-10-18 (OLMoE's section 5.4
and the Spec-Bench page read the same day); the fetch log is in the lane's
scratch, and the sentence each entry supports is the one quoted here, nothing
beyond it.

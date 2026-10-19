# TP-1_llamacpp_adapter

**Status**: archived 2026-10-10 (TP-7, F-19): the research is closed; this pack will not be executed.

> **BLOCKED by F-5.** The coder's TOTAL_MAX=2^16 cannot represent LLM
> vocabularies: Llama-3/Qwen/Gemma raise CoderError outright, and 32k vocabs
> lose ~33% ratio to floor mass. Land D-12 (lsp1 profile constants) before
> starting this pack. Sub-task 2's `quantize_probs at 2^15` is void — the grid
> moves to logit space per D-13/F-7.


## Goal
Implement a llama.cpp-backed PredictiveModel so real LLM probabilities drive the existing coder, with round-trip proven on one machine.

## Why this matters
Everything above the model interface is already model-agnostic and conformance-tested; the adapter is the bridge from "reference machinery" to "the actual product thesis" (LLM-grade ratios inside a deterministic container). Without it, lsp1, E-001..E-005, and TP-2 are all blocked.

## Out of scope
- No cross-device determinism claims (that is TP-4 / E-001).
- No logit quantization or safeguard stream (that is TP-2).
- No changes to Tier-0 files (`src/lockstep/rac.py`, `src/lockstep/container.py`) or to conformance vectors.
- No model weights committed to the repo.

## Files touched
- `src/lockstep/adapters/llamacpp.py` - new adapter implementing next_cdf/update via llama-cpp-python teacher forcing; byte-fallback tokenizer policy per OQ-6.
- `src/lockstep/adapters/__init__.py` - adapter registry, optional-import guarded.
- `tests_project/test_adapter_llamacpp.py` - round-trip on small corpora; skipped automatically when llama-cpp-python or the model file is absent.
- `docs/06-adapter-notes.md` - observed ratios, context policy chosen, and every nondeterminism observed en route.

## Risk level
Medium. Third-party runtime with float internals touches the model surface; risk is contained because Tier-0 stays frozen and container hashes make any desync loud.

## Dependencies
- `docs/04-architecture.md` two-tier trust model.
- `specs/decode-profile-v0.md` model-interface obligations.
- Operator-provided gguf model file and llama-cpp-python install (record versions and weights sha256 in the run row).

## Proof gate
```powershell
python -m unittest tests_project.test_adapter_llamacpp -v
python -m unittest discover -s tests_project -t . -q
python tools/trellis_refs.py
```

## Sub-tasks
1. Adapter skeleton: load model, teacher-forced eval loop, expose per-position probabilities over the byte alphabet via the OQ-6 byte-fallback policy; document context window policy to the token.
2. CDF path: probabilities -> `quantize_probs` at 2^15 -> Cdf; identical calls on encode and decode; unit test that encode-side and decode-side CDFs match position-by-position on one machine.
3. Round-trip: 3 corpora (prose, code, drbg-random) x 2 sizes; record ratios vs adaptive-order1 baseline in trellis-docs/trellis-runs.md; write finding if ratio > 3x on prose.
4. Failure drill: force a mismatched model file and confirm the container failure taxonomy reports desync, not damage.

## Final acceptance
- Round-trip is bit-exact on the dev machine for all six corpus cases.
- Adapter tests skip cleanly (not fail) when the runtime or weights are absent.
- A run row exists with weights hash, llama.cpp version, ratios, and env fingerprint digest.
- Every command in Proof gate passes.

## Stop conditions
- Stop if round-trip fails intermittently on a single machine - that is an N2/N3 finding to record first, not a bug to paper over.
- Stop if the adapter needs changes to Tier-0 files or vectors.
- Stop if acceptance cannot be verified with the operator's hardware.

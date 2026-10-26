# TP-2_logit_quantization_and_safeguard

**Status**: archived 2026-10-10 (TP-7, F-19): the research is closed; this pack will not be executed.

> **BLOCKED by F-6.** The probability-space grid cannot both absorb drift and
> preserve ratio at LLM vocabulary — corrections would fire on ~100% of tokens
> and this pack's 10% overhead stop condition trips immediately. Re-scope onto
> D-13 (logit-space grid + top-k, correction rate ~ k*eps/delta per F-7) and
> size delta/k from E-006 before implementing.


## Goal
Make lsp1 decode survive bounded cross-device drift: pin the grid placement (OQ-4) and implement the PA-7-style safeguard side-stream with measured overhead.

## Why this matters
This pack is the determinism thesis itself. The grid absorbs sub-half-step drift (F-2) but E-001-class drift near cell edges will eventually desync a decoder; the safeguard stream converts "usually decodes" into "decodes, guaranteed within a stated drift bound" — the property no shipping system offers.

## Out of scope
- No integer-network entropy model implementation (patent-gated; see docs/03-patent-and-licensing-notes.md and TP-5). [withheld: docs/03-patent-and-licensing-notes.md not in this repository; see WITHHELD.md]
- No multi-device measurement campaigns (E-001/E-004 execute separately; this pack builds what they measure).
- No changes to lsp0 semantics or vectors; new behavior lands as profile draft lsp2.

## Files touched
- `src/lockstep/guard.py` - guard-band detection on encode, correction-record emit, decode-side application.
- `src/lockstep/container.py` - optional `safeguard` manifest block + side-stream framing (additive, version-gated).
- `specs/decode-profile-v1-draft.md` - grid placement decision, guard-band rule, record wire format.
- `tests_project/test_guard.py` - synthetic-drift injection: perturbed decoder + safeguard = bit-exact; without = loud desync.

## Risk level
High. Touches container framing and defines the format's central guarantee; mitigated by version-gating, synthetic-drift tests, and E-004 before any spec freeze.

## Dependencies
- TP-1 adapter (real probability source).
- F-2 grid-absorption finding and `quantize_probs` rule in `specs/decode-profile-v0.md`.
- PA-3 and PA-7 designs in `docs/02-prior-art.md`.

## Proof gate
```powershell
python -m unittest tests_project.test_guard -v
python -m unittest discover -s tests_project -t . -q
python tools/trellis_pack_lint.py task-packs/TP-2_logit_quantization_and_safeguard.md
```

## Sub-tasks
1. Decide and record grid placement (logits vs post-softmax) as a decision citing OQ-4 and PA-3; implement the chosen rule behind one function with an exactness note per class N4.
2. Guard-band detector: flag positions whose quantized cell sits within delta of a boundary; delta parameterized for the E-002/E-004 sweeps.
3. Correction records: wire format (position-delta varint, cell id), side-stream framing in the container, decode-side application before coding each flagged symbol.
4. Synthetic drift harness: decoder-side probability perturbation at configurable epsilon; tests prove bit-exact recovery inside the bound and loud desync beyond it.

## Final acceptance
- With safeguard on, synthetic drift up to the stated bound yields bit-exact decode on 100% of 200 seeded cases; beyond the bound, failure is the taxonomy's desync error.
- Overhead is reported (bytes of side-stream / bytes of payload) for three delta values on one real corpus.
- lsp0 vectors still pass untouched.
- Every command in Proof gate passes.

## Stop conditions
- Stop if safeguard overhead exceeds 10% at any delta that achieves 100% recovery - architecture review per E-004 stop rule.
- Stop if the design drifts toward integer-network entropy models before TP-5 closes.
- Stop if lsp0 conformance breaks at any point.

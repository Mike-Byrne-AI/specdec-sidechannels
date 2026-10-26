# TP-6_fuzzing_and_bomb_guards

**Status**: archived 2026-10-10 (TP-7, F-19): the research is closed; this pack will not be executed.

## Goal
Maintain standing adversarial protection for the container parser and complete the decoded-bytes policy needed by a future multi-chunk format.

## Unified v0.2 baseline

The deterministic stdlib mutation suite is now committed and runs 768 cases in the
default product gate; structured regression tests cover duplicate keys, numeric/parser
edge cases, forged profile pins, framing mismatches, and destination safety. For the
current single-stream format, the exact declared output size is validated against the
caller policy before decode and the decoder emits exactly that many bytes. The remaining
work is the independent cumulative `max_decoded_bytes` counter required when TP-3 adds
multiple chunks or any framing where aggregate output is not represented by one trusted
size field. An optional broader property/fuzzer harness also remains useful.

## Why this matters
F-3 found real untrusted-input defects (leaked exceptions, silent negative size, a size-declared decompression bomb) by hand; strict validation (D-11) closed them. The unified mutation suite now keeps those classes under continuous pressure. Archives are still read from untrusted sources, so future chunked framing needs a second, aggregate output-side bomb guard where many individually valid chunks could describe excessive cumulative output.

## Out of scope
- No model or adapter work.
- No new container fields beyond an optional decoded-bytes limit parameter.
- No third-party fuzzing dependency in the committed test path (keep Tier-0 stdlib-only; an optional atheris/hypothesis harness may live behind a guarded import).

## Files touched
- `tests_project/test_fuzz_container.py` - extend the existing deterministic stdlib mutation smoke test with structured per-field type-confusion generation.
- `src/lockstep/container.py` - add an aggregate `max_decoded_bytes` budget when chunked framing makes it distinct from the existing exact single-stream output-size policy.
- `specs/lockstep-container-v0.md` - document the output-side guard alongside the declared-size ceiling.
- `tests_project/test_manifest.py` - extend with the output-side budget cases.

## Risk level
Low. Additive guards and tests; the happy path and existing vectors are untouched.

## Dependencies
- F-3 finding and D-11 strict-validation decision.
- `src/lockstep/manifest.py` validator.
- TP-3 chunk format (for where cumulative output guarding matters most; this pack can land the single-stream guard first).

## Proof gate
```powershell
python -m unittest tests_project.test_fuzz_container tests_project.test_manifest -v
python -m unittest discover -s tests_project -t . -q
python tools/trellis_pack_lint.py task-packs/TP-6_fuzzing_and_bomb_guards.md
```

## Sub-tasks
1. **Baseline complete:** deterministic seeded mutation harness covers truncation, bit flips, insertions, random framing, and length corruption; extend with field-swap and generated type-confusion matrices.
2. Structured type-confusion generator: for each manifest field, substitute each wrong JSON type and assert typed rejection.
3. Streaming output guard: thread max_decoded_bytes through the decode loop; abort the instant produced bytes would exceed it; typed error; test with a container whose declared size is small but (in a future chunked world) whose cumulative output is large.
4. **Baseline complete:** current guard/spec/tests are documented in F-9/F-10; append a new finding for the chunked cumulative guard and any newly surfaced defect.

## Final acceptance
- The fuzz harness runs a fixed seed budget with zero leaked builtin exceptions and is fast enough for CI (< a few seconds).
- The streaming guard aborts over-budget decode with a typed error, proven by test.
- All existing vectors and tests still pass.
- Every command in Proof gate passes.

## Stop conditions
- Stop and record a finding if the fuzzer surfaces any input that escapes as a non-container exception.
- Stop if the output guard would require changing lsp0 coder semantics.
- Stop if fuzz runtime blows the CI budget - reduce the seed set and file a note rather than weaken assertions.

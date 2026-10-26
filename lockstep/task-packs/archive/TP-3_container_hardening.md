# TP-3_container_hardening

**Status**: archived 2026-10-10 (TP-7, F-19): the research is closed; this pack will not be executed.

## Goal
Take the container from demo-grade to archive-grade: chunking with per-chunk reset, streaming IO, a multi-file convention, and spec/vector coverage for all of it.

## Why this matters
Archives are the wedge use case (docs/00-vision.md), and archives are big. The unified v0.2 baseline now streams a single lsp0 payload in bounded memory, but it still cannot seek, parallelize, or localize a desynchronization blast radius. Finishing chunking is what makes E-005 restore-time projections and any pilot conversation honest. [withheld: docs/00-vision.md not in this repository; see WITHHELD.md]

## Unified v0.2 baseline

The unchunked portion of sub-task 2 is complete: `pack_file`, `unpack_file`, and
`verify_file` stream, enforce source/payload/output policies, verify before publishing,
and use atomic destination replacement. The remaining task is genuinely format-level:
chunk metadata, per-chunk resets and hashes, selective decode, corruption localization,
and a multi-file convention. This task pack stays open for those additions.

## Out of scope
- No compression-model changes and no adapter work.
- No encryption or signing (compose externally; revisit post-TP-5).
- No backward-incompatible edits to existing lsp0 vector cases (new cases may be added).

## Files touched
- `src/lockstep/container.py` - extend the existing streaming file APIs with a chunk table, per-chunk coder reset, and per-chunk SHA-256.
- `specs/lockstep-container-v0.md` - chunking extension section resolving OQ-1, multi-file (tar-then-pack) convention resolving OQ-3.
- `tests_project/test_container.py` - chunked round-trip, mid-archive corruption isolates to one chunk, seek-decode of a single chunk, large-file streaming smoke.
- `tools/lockstep_gen_vectors.py` - additive chunked-mode vector cases.
- `conformance/vectors_v0.json` - regenerated with additions only.

## Risk level
Medium. Format surgery on the trust base, but purely additive: unchunked v0 streams remain valid and their vectors remain frozen.

## Dependencies
- `specs/lockstep-container-v0.md` reader algorithm and failure taxonomy.
- OQ-1 and OQ-3 in `docs/05-open-questions.md`.
- D-9 vector governance.

## Proof gate
```powershell
python -m unittest tests_project.test_container tests_project.test_conformance -v
python -m unittest discover -s tests_project -t . -q
python tools/trellis_pack_lint.py task-packs/TP-3_container_hardening.md
```

## Sub-tasks
1. Manifest chunk table (offset, coded size, raw size, sha256 per chunk) + writer producing fixed-raw-size chunks with fresh model+coder per chunk; record the chunk-size ratio cost on one corpus.
2. **Partly complete:** bounded-memory pack/unpack/verify APIs are landed; add the chunk-specific corruption test proving one flipped byte damages exactly one chunk and names it.
3. Seek: decode chunk k without touching others; test.
4. Multi-file convention: document tar-then-pack with a worked example; add a cookbook snippet to README.
5. Vector additions for chunked mode; decision row recording the default chunk size with its measured trade-off.

## Final acceptance
- 1GB-scale streaming pack/unpack runs in bounded memory on the operator machine (documented peak RSS).
- Single-byte corruption is localized and reported with chunk index; other chunks decode.
- All prior vectors byte-identical; new chunked vectors added and passing.
- Every command in Proof gate passes.

## Stop conditions
- Stop if chunk-reset ratio cost exceeds 10% at the default size - resize or rethink before freezing.
- Stop if any existing vector changes.
- Stop if memory bounds cannot be met without touching Tier-0 coder internals.

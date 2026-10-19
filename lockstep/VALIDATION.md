# Local release validation — v0.2.0

Validation date: 2026-07-22.

Environment used for the completed local gate:

- CPython 3.13.5, GCC 14.2.0;
- Linux x86_64, kernel 6.12.13;
- runtime dependencies: Python standard library only;
- test runner available in the analysis environment: pytest 9.0.2.

## Completed gates

| Gate | Result |
|---|---|
| `python -m pytest -q tests_project` | 82 passed, 39 subtests passed |
| `python -m unittest discover -s tests_project -t . -q` | 82 passed |
| `python tools/lockstep_gen_vectors.py --check` | generated data and both vector copies match |
| `python -m lockstep self-check` | 6/6 lsp0 vectors reproduced |
| `python -m pytest -q .claude/trellis-tests` | 115 passed, 4 precondition skips |
| `python tools/trellis_repair_gate.py` | passed |
| `python -m compileall -q src tests_project tools` | passed |
| committed deterministic mutation suite | 768 cases, no leaked builtin exception |
| additional deterministic malformed-container sweep | 10,000 cases, no leaked builtin exception |
| clean wheel install outside source tree | console command, packaged vectors, resource digest, and API round-trip passed |

The six conformance payload hashes are unchanged from the supplied repositories. The
source-visible and installed vector resource is byte-pinned as:

```text
c452e20b01344a9d4b1e0c0f42b17da97572de7ac52746a3c9ef6e91934b4861
```

The built wheel used for this release check is:

```text
lockstep_archive-0.2.0-py3-none-any.whl
SHA-256 a9ab85e4b4742f70960f56d11cef87bed7dc24dcc21300cb40b003ad81732561
```

The source-tree self-check fingerprint was
`9c661e9a34b2edcf310196bf1c7ed3abbae38cffcc152a5305151dd271fc4318`; the clean
virtual-environment fingerprint was
`7b8a87ec8daf4a3ccdbb41ed224ede59c8dbad5f3f5b573f34b30db31632fc71`.
The fingerprint intentionally includes environment identity, so these digests need not
match; both environments reproduced the same six profile payloads.

## Scope of the claim

These are local Linux/CPython 3.13.5 results. The repository includes a hosted CI
workflow for Python 3.10–3.13 and a clean-wheel smoke test, but that hosted matrix was
not executed in this analysis environment. The validation establishes the hardened
`lsp0` reference and packaging path; it does not establish an unimplemented `lsp1`,
cross-device neural-model determinism, production throughput, encryption, chunking, or
license clearance.

Dated note (2026-10-18): the six vectors do not exercise the adaptive model's rescale
clause. Replayed through the model, the largest row total any context reaches is 3,712
against the limit of 32,768, no rescale fires, and a coder with the clause disabled
reproduces the five adaptive-model vectors' payload digests, the uniform sixth having no
such clause (docs/audits/2026-10-18-image-audit/vector_coverage.py, output pinned in its
header). The byte-exact reproductions above, and the three encoders
the audit's agents wrote without importing lockstep, therefore attest the profile up to
that clause and not beyond it. A vector long enough to cross the limit is owed before the
clause can be called conformance-tested.

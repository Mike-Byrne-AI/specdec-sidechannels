# Repository assessment and unification record

## Executive finding

The three inputs are sequential revisions of one codebase, not competing
implementations. The synthesis repository is a superset of the reviewed repository,
which is a superset of the starter. No unique starter implementation needed to be
rescued from an abandoned branch, so the correct merge strategy was:

1. use synthesis as the content baseline;
2. preserve the proven `lsp0` bitstream exactly;
3. repair inconsistencies and security gaps found by adversarial review;
4. make the reference runtime installable and file-safe;
5. leave unproven `lsp1` work explicitly unresolved.

## Input comparison

| Repository | Files | Product tests | What it contributes | Main limitation |
|---|---:|---:|---|---|
| Starter | 145 | 30 | Integer coder, CDFs, byte models, v0 container, vectors, initial specs and research plan | Ad-hoc manifest access, no bomb policy, no package metadata |
| Reviewed | 152 | 42 | Strict manifest module, output-size ceiling, review/failure docs, cost model, critic agent, 12 regression tests | Model parameters still not enforced; hidden Trellis inventory broken |
| Synthesis | 155 | 42 | Everything reviewed adds, plus profile advisor, E-006, and the emergent scale/economics synthesis | Runtime code is unchanged from reviewed; packaging and file safety still absent |

The original visible suites all passed: 30/30 for starter and 42/42 for reviewed and
synthesis. The reviewed and synthesis hidden Trellis suite did not fully pass: the new
`lockstep-critic` agent increased the real inventory to four while the expected count
remained three. The supplied archive SHA-256 values are:

- starter: `6476837cb40bbe05249f1f42b0363c67be8ef4425db56b084206102a01c9236a`;
- reviewed: `0ee7e61d591c610a7e54d88a4af7f506abb1f8bae27ae63f3b0b3a40635b33a0`;
- synthesis: `5326448711126e81a4790ae5e195bf0cb96b1124eff17165de9e4b4bfacfe4f2`.

## What was retained

- The arithmetic coder algorithm and all profile constants.
- The adaptive and uniform model state transitions.
- The exact conformance vector inputs and payload hashes.
- The reviewed manifest choke point and caller-controlled output ceiling.
- All critical review, failure-mode, cost-model, profile-advisor, and E-006 material.
- The Trellis workflow and repository memory.

## Defects found beyond the supplied review

### Critical format-contract gap

`profile.model` was documented as pinning every parameter, but the reader only used the
model name. Archives forged with `alphabet=999`, `increment=999`, or
`rescale_limit=257` were accepted and decoded successfully because those fields were
ignored. This version requires every expected parameter with exact JSON type and value
before decoding.

### Parser ambiguity and exception leakage

Duplicate JSON keys were accepted according to Python’s “last key wins” behavior, which
can disagree across implementations. A JSON integer longer than Python’s configured
digit limit leaked raw `ValueError`; exponent overflow could create a non-finite float
even without a `NaN` token; and unpaired Unicode surrogates were accepted. These are now
typed manifest failures under explicit numeric and manifest-size policies.

### Trust-base type coercion

The integer-only guarantee was not enforced at API boundaries. CDFs and coder intervals
could accept floats or `bool` values because Python comparisons and arithmetic allowed
them. These inputs are now rejected as `CoderError` before state mutation. CDF objects
and the public profile/registry tables are now immutable so accidental mutation cannot
change the declared contract independently of coder behavior.

### Operational scaling mismatch

The manifest allowed outputs up to 8 GiB while `pack_file` and `unpack_file` loaded whole
files and outputs into memory. The standalone in-memory manifest reader also failed to
compare declared and physical payload lengths. File APIs now stream, cap coded-payload
growth, verify the payload before decode, rehash the bounded second pass to detect source
mutation, hash output during decode, and atomically publish only verified output. This
does not add chunking or random access; it makes the existing single-stream format
operationally honest.

### Packaging gap

The README suggested editable installation despite having no `pyproject.toml` or setup
metadata, and `self-check` depended on vectors adjacent to a source checkout. The
unified version installs normally, exposes a console script, and includes byte-identical
vectors as package data while maintaining a checked source-visible mirror and a hard
vector-resource digest pin.

## Unified-version validation

- 82/82 product tests pass, plus 39 pytest subtests.
- 115/115 runnable Trellis tests pass; 4 tests skip because their source-layout or
  platform preconditions do not apply.
- All six `lsp0` payload sizes and SHA-256 hashes remain unchanged.
- Streaming and in-memory encoders are tested byte-for-byte equivalent.
- `pack_file` and `pack` are tested to create identical containers.
- The default suite includes a deterministic 768-case mutation fuzzer; an additional
  10,000 malformed-container sweep leaked no builtin exception.
- Corrupt, concurrently mutated, or desynchronised archives are tested not to overwrite
  an existing output.
- A wheel installs into a clean virtual environment, runs `lockstep self-check` outside
  the source tree, finds its packaged vectors, and completes an API round-trip.
- The full Trellis repair gate passes.

These validation results were executed locally on CPython 3.13.5, Linux x86_64. The
repository defines a Python 3.10–3.13 hosted CI matrix, but that hosted matrix was not
executed inside this analysis environment.

## What remains unresolved

This is the strongest coherent **lsp0 reference** from the supplied material, not the
finished product thesis.

- `lsp1` has no adapter, model/tokenizer content pinning, safeguard stream, or normative
  profile constants.
- E-006 still needs real CPU/GPU logit-crossing measurements.
- Chunking, seekability, multi-file archives, and encryption are absent.
- The Python adaptive model is a correctness reference, not a production-throughput
  runtime.
- The economic case depends on packing being amortised by inference already performed
  for another purpose; that has not been validated with users.
- Patent, model-license, repository-license, and trademark decisions remain open.

The next “ultimate” milestone should therefore be evidence-driven: execute E-006,
select lsp1 constants from measured regimes, and validate the byproduct use case before
building a larger format surface.

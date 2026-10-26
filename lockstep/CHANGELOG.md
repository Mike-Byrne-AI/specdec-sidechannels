# Changelog

## 0.2.0 — Unified hardened reference

### Added

- Installable `pyproject.toml` package and `lockstep` console command.
- Packaged conformance vectors that work outside a source checkout.
- Streaming codec and file container APIs.
- Atomic file extraction and streaming verification.
- Typed integrity, desynchronisation, unsupported-profile, and resource-limit errors.
- Adversarial tests for parser ambiguity, model-profile forgery, resource limits,
  strict integer inputs, stream equivalence, source mutation, and destination safety.
- A deterministic 768-case container mutation smoke fuzzer in the default suite.
- A hard SHA-256 pin for the packaged conformance-vector bytes.
- CI workflow covering Python 3.10–3.13, product tests, vectors, self-check, Trellis
  tests, the repair gate, and a clean-wheel smoke test.

### Fixed

- Enforced `alphabet`, `increment`, and `rescale_limit` instead of silently ignoring
  forged model-profile pins.
- Rejected duplicate JSON keys, unpaired Unicode surrogates, non-finite numeric
  values, oversized manifests, and huge numeric literals without leaking builtin
  parser exceptions.
- Rejected floats and `bool` values at the integer coder/CDF trust boundary.
- Rejected non-finite probability inputs with typed errors.
- Enforced payload-length equality in the standalone manifest reader.
- Added a coded-payload growth ceiling to streaming pack and second-pass source
  mutation detection to streaming verify/unpack.
- Made CDF objects and public model-profile/registry tables immutable.
- Fixed the Trellis inventory expectation after adding the fourth agent.
- Generalised the Trellis pytest-discovery test for host repositories using
  `tests_project/`.

### Compatibility

- `lsp0` coder constants, model behavior, and all six payload hashes are unchanged.
- Existing in-memory `pack`, `unpack`, `encode_bytes`, and `decode_bytes` APIs remain.
- Writer version advanced from 0.1.0 to 0.2.0; readers do not branch on writer version.

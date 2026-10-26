# Conformance methodology v0

## Normative vector copies

`conformance/vectors_v0.json` is the source-visible normative vector set. An
installed distribution also carries an exact byte-for-byte mirror at
`lockstep/data/vectors_v0.json` so `lockstep self-check` does not depend on a
source checkout.

The two copies MUST remain byte-identical. Their current bytes are pinned in
`lockstep.conformance.VECTORS_V0_SHA256`, so an installed self-check also rejects
vector-resource drift. The reference command
`python tools/lockstep_gen_vectors.py --check` verifies generated payloads, the
source/package mirror, and that digest pin; `--write` is an explicit maintenance
operation, not an automatic test repair.

## What a vector pins

Each case specifies a reproducible input, model name, `payload_size`,
`payload_sha256`, and `original_sha256`. Input generators are:

- a UTF-8 literal;
- a repeated byte ramp `00..ff`;
- the deterministic generator in `src/lockstep/drbg.py`, where
  `block_i = SHA-256(seed_utf8 || uint64_be(i))`, concatenated and truncated to
  the requested length.

Payload hashes, rather than whole-container hashes, are pinned. Writer-version
changes can therefore leave vectors valid while every profile-emitted bit stays
frozen.

## Claiming conformance

1. Run the vector suite on the target runtime, not only a development checkout:
   `python -m lockstep self-check` or
   `python -m pytest -q tests_project/test_conformance.py`.
2. Record the environment fingerprint printed by `python -m lockstep env`.
   A useful claim is the pair `(vectors pass, fingerprint digest)`.
3. For a distribution claim, install the built package into a clean environment
   and run `lockstep self-check` from outside the repository.
4. Cross-machine claims follow `experiments/E-001-cross-device-logit-drift.md`:
   run the same immutable vectors on each machine and compare exact hashes.

A local pass demonstrates reference-runtime consistency. It does not by itself
establish an unimplemented LLM-backed profile or cross-device neural-model
determinism.

## Governance

- Vectors are append-preferred. Adding cases is permitted when existing cases
  remain unchanged.
- Changing or removing an existing case is a format break requiring a task
  pack, a recorded decision, and a versioned vector/profile change.
- A conformance failure is never resolved by regenerating vectors first.
  Diagnose the container failure category and environment difference, then
  decide whether code, specification, or a new profile version must change.
- The vector mirror inside the package is generated from the normative file;
  disagreement between the copies is a packaging/release failure.

## Roadmap

A future `lsp1` vector format is expected to add model-content and tokenizer
hashes, canary-logit digests at pinned positions, safeguard-stream records, and
cross-device evidence. Those fields are roadmap items, not current guarantees.

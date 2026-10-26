# Lockstep container v0 (`.lsa`) — normative

Status: draft. Reference implementation: `src/lockstep/container.py` and
`src/lockstep/manifest.py`. On conflict, this specification wins and the
implementation is defective.

## Layout

| offset | size | field |
|---|---:|---|
| 0 | 4 | magic `LSA0` (`4c 53 41 30`) |
| 4 | 4 | manifest length `M`, unsigned 32-bit big-endian |
| 8 | `M` | manifest JSON, UTF-8 |
| `8+M` | rest | arithmetic-coded payload |

A conforming **v0 writer MUST emit canonical JSON**: object keys sorted
lexicographically at every level; separators `,` and `:` with no whitespace;
UTF-8; no byte-order mark or trailing newline; and no non-finite numeric
constants.

A reader MUST parse JSON unambiguously and MUST reject malformed UTF-8,
duplicate object keys, unpaired Unicode surrogates, non-finite numeric values,
and numeric literals too large for its documented parser policy. A reader MAY
accept otherwise valid noncanonical JSON. Canonical reserialization is therefore
not a prerequisite for reading an archive and is not an integrity mechanism;
the payload and original digests are.

## Manifest schema (v0)

```json
{
  "format": "lockstep-container",
  "format_version": 0,
  "profile": {
    "id": "lsp0",
    "coder": {"code_bits": 32, "prob_bits_max": 16},
    "model": {"model": "<registry name>", "...": "all pinned parameters"}
  },
  "original": {"size": 0, "sha256": "<64 lowercase hex chars>"},
  "payload":  {"size": 0, "sha256": "<64 lowercase hex chars>"},
  "writer":   {"tool": "lockstep", "version": "<version string>"}
}
```

Rules:

- `writer` is optional and informational. When present it MUST be an object
  containing string fields `writer.tool` and `writer.version`. Readers MUST
  NOT branch on writer identity or version.
- Unknown manifest keys MUST be ignored by readers for forward compatibility.
  A v0 writer MUST NOT emit unknown keys.
- `profile.model` MUST contain every parameter needed to reconstruct the model
  exactly. Decode-time defaults do not exist.
- Values are compared by exact JSON type as well as value. In particular,
  `true` and `false` are not integers.

The model profiles defined by `lsp0` are exact:

```json
{"alphabet":256,"increment":24,"model":"adaptive-order1","rescale_limit":32768}
```

```json
{"alphabet":256,"model":"uniform"}
```

A reader supporting either model MUST reject missing, altered, or differently
typed values in these pinned fields as unsupported. Extra model keys are
ignored for forward compatibility but cannot override the pinned fields.

## Reader algorithm (normative order)

1. Verify magic and enforce a reader-supplied manifest-length ceiling before
   allocating or parsing the manifest.
2. Parse unambiguous JSON and validate the schema strictly, including
   reader-supplied ceilings for both `original.size` and `payload.size`.
3. Compare the physical payload length to `payload.size`, then verify
   `payload.sha256`, before any decode-model work. Failure is **damage**.
4. Instantiate the exact pinned model. An unknown profile, unknown model, or
   incompatible pinned parameter is **unsupported**, not damage.
5. Decode exactly `original.size` symbols. No EOF symbol is present.
6. Verify `original.sha256`. Failure is **desynchronisation**, distinct from
   storage/transit damage.
7. A file extractor MUST NOT publish partially decoded output. It SHOULD write
   to a private temporary file in the destination directory and atomically
   replace the destination only after step 6 succeeds. The reference reader
   bounds the second-pass decoder to the validated payload length, rehashes that
   pass, and rejects source-file mutation before publication.

A verifier performs the same steps but may discard decoded bytes.

## Strict manifest validation (normative)

A conforming reader MUST reject a manifest that violates any of the following:

- the root is a JSON object;
- `format` is exactly `"lockstep-container"`;
- `format_version` is integer `0`;
- `profile` is an object with `id` exactly `"lsp0"`;
- `profile.coder` is an object with integer `code_bits == 32` and integer
  `prob_bits_max == 16`;
- `profile.model` is an object with a string `model` registry name and all
  exact fields pinned above for that model;
- `original` and `payload` are objects;
- `original.size` and `payload.size` are non-negative integers;
- `original.size` does not exceed the caller's `max_original_size` policy;
- `payload.size` and the physical payload length do not exceed the caller's
  `max_payload_size` policy;
- `original.sha256` and `payload.sha256` match
  `/\A[0-9a-f]{64}\Z/`;
- `writer`, when present, contains string `tool` and `version` fields.

Schema rejection MUST be a typed container failure, never a leaked language
exception such as `KeyError`, `TypeError`, `AttributeError`, a JSON parser
integer-limit exception, or a recursion exception.

## Failure taxonomy

The reference hierarchy is normative in meaning, not in Python class names:

- **malformed manifest/framing** — `ManifestError` or `ContainerError`;
- **unsupported exact profile/model** — `UnsupportedProfileError`;
- **caller resource policy exceeded** — `ResourceLimitError` (a
  manifest-declared limit may also be a manifest error);
- **payload size or digest failure** — `IntegrityError`;
- **decoder failure or decoded digest mismatch** — `DesyncError`.

Callers MUST be able to distinguish at least unsupported, damage,
desynchronisation, and resource-policy failures without matching error text.

## Resource policy

The format's 32-bit manifest-length field permits values far larger than a safe
reader should accept. Every reader MUST expose finite local limits for manifest
bytes, declared decoded bytes, and payload bytes, and MUST apply them before the
corresponding allocation or work. Limits are operational policy, not a claim
that every accepted archive is computationally cheap.

The reference runtime defaults to 1 MiB for manifests and 8 GiB for original
and payload sizes at the library boundary; its CLI lowers the latter two to
1 GiB. Its parser additionally caps integer literals at 128 digits and
floating-point literals at 256 characters. The file packer applies the same
caller-controlled payload ceiling while producing coded bytes, so expansion
cannot consume unbounded temporary storage. These values are implementation
policy, not wire-format constants.

## Deliberate v0 limits

`lsp0` has one stream, no chunk table or seeking, one payload, no file table,
model selection by registry name rather than content hash, and no encryption.
Encryption or authentication may be composed outside the format. The embedded
SHA-256 values detect accidental damage but do not authenticate a maliciously
rewritten archive because an attacker can replace both data and digest. A future
profile must use a new profile identifier and conformance vectors rather than
silently changing these semantics.

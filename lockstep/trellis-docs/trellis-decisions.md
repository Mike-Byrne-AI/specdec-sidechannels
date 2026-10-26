# Decisions

Architectural choices and their rationale. Each entry locks in something that affects more than one task pack or sub-task. The point: prevent relitigation.

## Format

```markdown
## D-N — Short title                                                    [confidence]

**Context**: what we were trying to decide.
**Choice**: what we picked.
**Why**: the argument that won.
**Alternatives considered**: other options and why they lost.
**Reversibility**: cheap / medium / expensive.
**Source**: links to runs, findings, task packs.
```

## Confidence markers

- `[verified]` — validated by running code or empirical evidence
- `[probable]` — well-argued and consistent with available evidence, not directly tested
- `[imagined]` — design choice not yet built. Most decisions start here.

**CC must not silently promote confidence.** Only the user moves `[imagined]` → `[probable]` → `[verified]`. CC may propose; the user confirms. The `check_confidence_promotion.py` hook enforces this.

## How to add a decision

When making a non-trivial design choice during a task pack:

1. Read the existing trellis-docs/trellis-decisions.md to find the highest D-N
2. Default confidence to `[imagined]`
3. Cite the source (task pack, finding, or run number)
4. Don't promote confidence of existing decisions — user-only

## Decisions

## D-1 - Public preview license and status [imagined]

**Context**: The harness needs a public OSS surface before release.
**Choice**: This revision uses the MIT license and labels the project as public preview / experimental alpha until a maintainer chooses a different release policy.
**Why**: Users need explicit license and stability boundaries before trying the harness in real repositories.
**Alternatives considered**: Leaving the license unspecified was rejected because that is not usable OSS. Claiming production stability was rejected because the harness remains preview-grade.
**Reversibility**: Medium; a maintainer can change license/status before publication, but should do so before external adoption.
**Source**: task pack 4 public OSS surface.

## D-2 - Installed self-tests live under `.claude/trellis-tests/` [imagined]

**Context**: Installing Trellis tests into host root `tests/` can collide with project tests and fixtures.
**Choice**: Source tests remain in root `tests/`, while installed host projects receive Trellis self-tests under `.claude/trellis-tests/`.
**Why**: This keeps Trellis-owned validation available without taking over host test layout.
**Alternatives considered**: Root `tests/` installation was rejected as too invasive for public users. Omitting installed tests was rejected because it weakens repair-gate confidence.
**Reversibility**: Medium; paths can migrate with installer and manifest changes.
**Source**: task pack 5 installed harness self-test isolation.

## D-3 - Sentinel-gated internal memory [imagined]

**Context**: Root `memory/` is a useful Trellis procedural-memory name, but many host projects may already use that directory for their own state.
**Choice**: Trellis treats `memory/` as internal memory only when `memory/.trellis-memory` exists as a regular, non-symlink file. Installer, manifest, reference scanning, reflection, and memory linting all share that sentinel contract.
**Why**: A single guard avoids silently merging, scanning, or claiming host-owned memory while still allowing Trellis-maintained memory in source and fresh installs.
**Alternatives considered**: Always using root `memory/` was rejected as too collision-prone. Moving Trellis memory under `.claude/` was rejected for now because root-level procedural notes are easier for maintainers to find and can remain safe with a sentinel and lint gate.
**Reversibility**: Medium; the directory could migrate, but installed hosts and docs would need a compatibility path.
**Source**: memory infrastructure refinement.

## D-4 - Host-safe shared permissions [imagined]

**Context**: Shared Claude Code settings ship into host repositories, so permissive defaults can turn a lightweight harness into surprising ambient authority.
**Choice**: Shared settings keep root integrations behind bootstrap, keep root `memory/**` writes behind explicit review, and do not auto-allow broad shell readers, git staging/show, or package installation. Operators can still opt in locally with uncommitted settings.
**Why**: The harness should reduce accidental host mutations and data exposure without pretending to be a sandbox. Local opt-in keeps advanced workflows possible while making public defaults conservative.
**Alternatives considered**: Broad shared readers and git staging were rejected because they make OSS installs feel more invasive than necessary. Fully denying host source edits was rejected because Trellis is a coding workflow harness, not a read-only documentation tool.
**Reversibility**: Cheap; shared settings can be loosened or tightened in a future release, but changes should remain documented and tested.
**Source**: memory infrastructure final quality pass.

## D-5 - Symlink-safe Trellis writes [imagined]

**Context**: Host projects may use symlinks under Trellis-managed destination prefixes or at bootstrap write paths. Backing up, overwriting, or generating through those links could mutate files outside the intended target tree.
**Choice**: The installer skips symlinked destination files and symlinked parent directories, including during `--overwrite-trellis`, and bootstrap skips symlinked `CLAUDE.md`, `.gitignore`, and manifest write paths. Both report the skipped path.
**Why**: Skipping is safer than following a link or trying to infer ownership across filesystem boundaries. A user can remove or replace the symlink explicitly when they want Trellis to manage that path.
**Alternatives considered**: Following symlinks was rejected as a host-safety footgun. Deleting symlinks was rejected because the installer should not perform destructive cleanup.
**Reversibility**: Medium; future install modes could add an explicit symlink policy flag, but the default should stay conservative.
**Source**: memory infrastructure final quality pass.

## D-6 - Working name "Lockstep" is provisional [imagined]

**Context**: The repo needs a name before a trademark/collision check has happened.
**Choice**: Use "Lockstep" (containers `.lsa`, profiles `lspN`) as a working name, explicitly provisional until TP-5-adjacent naming diligence.
**Why**: The word states the thesis (encoder and decoder marching in exact step) and short profile ids fall out of it naturally.
**Alternatives considered**: "Amber" (preservation connotation, weaker on determinism), descriptive "determinism-layer" (accurate, unbrandable). Both lost on thesis-fit.
**Reversibility**: Cheap now (rename + vector profile ids), expensive after anything ships.
**Source**: task pack scoping session; docs/05-open-questions.md risk list.

## D-7 - The reference path is float-free end to end [imagined]

**Context**: Floating point is the root cause of classes N1–N5 in docs/01-nondeterminism-taxonomy.md.
**Choice**: Tier-0 (coder, weight quantizer, container) uses integer arithmetic only; `quantize_probs` (float in) exists solely as a research surface for the lsp1 adapter and is banned from the lsp0 coding path.
**Why**: Bit-exactness by construction beats bit-exactness by testing; the reference implementation is the arbiter other runtimes are checked against, so it must be immune to the failure class it adjudicates.
**Alternatives considered**: Carefully-specified float path (rejected: N4 libm drift is outside our control); fixed-point floats via software emulation (rejected for v0: complexity without ratio benefit at this tier).
**Reversibility**: Expensive; this is the trust base's identity.
**Source**: F-1, F-2, docs/01 taxonomy, PA-8/PA-9 in docs/02-prior-art.md.

## D-8 - Safeguard side-stream is the primary lsp1 drift strategy; integer-network entropy models are counsel-gated [imagined]

**Context**: Two viable architectures make LLM decode deterministic: make the network's entropy math integer (PA-9 lineage) or quantize outputs to a grid and correct residual drift with a safeguard stream (PA-7 lineage). [withheld: the sentence naming two patents near the first architecture (15.1 call 2's shape, 15.6); see WITHHELD.md]
**Choice**: Build lsp1 on grid + safeguard stream (TP-2); treat integer-network entropy models as an alternative that requires TP-5 counsel clearance before any implementation.
**Why**: The safeguard design matches published third-party work with its own lineage, degrades gracefully (overhead scales with measured drift), and keeps the patent question from blocking all progress.
**Alternatives considered**: Integer-network-first (rejected pending freedom-to-operate); grid-only with no safeguard (rejected: F-2 shows a hard absorption boundary, and E-001 may find real drift beyond it).
**Reversibility**: Medium; the model surface is behind one interface, but a published lsp1 spec freezes the choice.
**Source**: docs/03-patent-and-licensing-notes.md, PA-7/PA-13, F-2, TP-2, TP-5. [withheld: docs/03-patent-and-licensing-notes.md not in this repository; see WITHHELD.md]

## D-9 - Container v0 shape and vector governance [imagined]

**Context**: The format needs an integrity story and a rule for when its promises may change.
**Choice**: `.lsa` = magic + canonical-JSON manifest + payload; dual sha256 (original + payload) with a normative failure taxonomy distinguishing damage from desync; conformance pins payload hashes (not container hashes); vectors are append-preferred and any change/removal is a format break requiring a pack + decision.
**Why**: Canonical JSON keeps manifests diffable and hashable; the dual-hash taxonomy turns the nightmare case (silent desync) into a named, testable error; payload-level pinning survives writer-version bumps.
**Alternatives considered**: Binary TLV manifest (rejected v0: opacity before an audience exists); container-hash pinning (rejected: couples vectors to writer metadata).
**Reversibility**: Medium; additive extensions are planned (TP-3), breaking changes are governed.
**Source**: specs/lockstep-container-v0.md, specs/conformance-v0.md, F-1.

## D-10 - CPU-first decode posture for archives [imagined]

**Context**: GPU inference is where nondeterminism classes N1–N3 concentrate, but archives are decoded rarely and tolerantly of latency.
**Choice**: Design lsp1 so the blessed decode path is CPU integer inference first; GPU decode is an optimization admitted only after passing the same conformance vectors and E-003 invariance audit.
**Why**: It removes the hardest nondeterminism classes from the guarantee's critical path and matches the archival access pattern (rare reads, long horizons).
**Alternatives considered**: GPU-first (rejected: stakes the guarantee on the least stable layer); CPU-only forever (rejected: E-005 may show GPU decode is needed for restore-time SLAs at scale).
**Reversibility**: Cheap until lsp1 freezes; the profile just names blessed runtimes.
**Source**: docs/01 taxonomy N1–N3, PA-10, E-003/E-005 protocols.

## D-11 - Strict manifest validation is the single untrusted-input choke point [imagined]

**Context**: F-3 showed the container manifest parser leaked builtin exceptions, silently accepted a negative original.size, and let an attacker-chosen size trigger a decompression bomb.
**Choice**: All container reads pass through manifest.validate_manifest, which enforces the exact v0 schema and types (rejecting bool-as-int), demands 64-char lowercase-hex digests, verifies pinned coder constants and model name, and enforces a caller-tunable max_original_size ceiling (default 8 GiB) BEFORE any decode loop. It raises ManifestError (a ContainerError subclass) and never a bare builtin. The old in-body model check is retired in favor of schema-time rejection.
**Why**: Untrusted-input surfaces need one hardened front door, not scattered dict indexing. Bounding declared output size before decoding is the only place a bomb can be stopped cheaply. Subclassing ContainerError keeps every existing except-site working.
**Alternatives considered**: Per-field try/except at each use site (rejected: leaky and unauditable); a third-party schema library (rejected: Tier-0 must stay stdlib-only per the 20-year/N8 posture); bounding memory at the OS level only (rejected: too coarse, gives a bad error).
**Reversibility**: Cheap; validation is additive and the schema is versioned with the format.
**Source**: F-3, specs/lockstep-container-v0.md reader algorithm, docs/01 taxonomy (loud-failure principle).

## D-12 - lsp1 gets its own coder constants; lsp0 stays frozen [imagined]

**Context**: F-5 proved TOTAL_MAX=2^16 forbids modern LLM vocabularies outright and destroys the ones that nominally fit, while also proving the constant is conservative (coder verified correct to 2^30 at CODE_BITS=32).
**Choice**: Do not mutate lsp0. Define lsp1 as a separate decode profile carrying its own constants (PROB_BITS_MAX raised to at least ~27, CODE_BITS=64 under evaluation for headroom), with its own vector set. lsp0 and its frozen vectors remain valid for the byte-alphabet reference path.
**Why**: D-9 governance makes vector changes a format break; a new profile is additive rather than breaking, and the two profiles serve genuinely different regimes (byte alphabet vs LLM vocabulary). Keeping lsp0 frozen preserves the reference implementation's role as arbiter.
**Alternatives considered**: Raising TOTAL_MAX in place (rejected: breaks lsp0 vectors for no benefit to the byte path); keeping 2^16 and shrinking vocab via aggressive top-k alone (rejected: F-5's floor-mass arithmetic still bites at any k above a few hundred, and it hides the real constraint).
**Reversibility**: Cheap now, expensive once any third party holds a vector file — which is precisely why it lands before TP-1 rather than after.
**Source**: F-5, D-9, specs/decode-profile-v0.md, TP-1.

## D-13 - The lsp1 grid lives in logit space with top-k truncation, not probability space [imagined]

**Context**: F-6 showed no probability-space grid both absorbs drift and preserves ratio at LLM vocabulary; F-7 showed logit-space quantization plus top-k restores sparse corrections at a measured rate matching k*eps/delta.
**Choice**: lsp1 quantizes logits on a coarse grid (delta ~1e-3 pending E-006), truncates to top-k (k ~64 pending E-006) with a lumped escape symbol, and performs softmax/apportionment in exact integer arithmetic over the k+1 survivors. The safeguard side-stream (D-8) carries corrections only for the rare boundary crossings this leaves.
**Why**: It collapses the drift surface from V to k, which is the only structural way out of F-6's squeeze; it converges with PA-3's published proposal; and it makes the side-stream sparse enough for D-8's economics to hold. It also answers OQ-4 by elimination rather than preference.
**Alternatives considered**: Probability-space grid (rejected: F-6 proves the windows do not overlap); safeguard-everything with no grid (rejected: equivalent to transmitting the model's decisions); integer-network entropy model (still counsel-gated per D-8/TP-5).
**Reversibility**: Medium; this shapes the lsp1 profile and the safeguard wire format, but nothing is frozen until E-006 lands.
**Source**: F-6, F-7, PA-3, PA-7, OQ-4 (now closed), D-8.

## D-14 - Position Lockstep as a byproduct of inference already being run, pending validation [imagined]

**Context**: F-8 showed packing is 92% of TCO and needs a 100–500x throughput miracle to break even as a standalone compressor, but that lsp1 wins by 23% when pack cost is zero.
**Choice**: Treat "the corpus owner is already computing these logits for another reason (RAG ingestion, embedding, indexing, curation, moderation)" as the project's working positioning, and validate it with a prospective user BEFORE further format work. Do not promote this beyond [imagined] on argument alone; it is a market claim and needs market evidence.
**Why**: It is the only regime the cost model admits, and it is falsifiable cheaply — a conversation, not a quarter of engineering. Naming it explicitly also prevents the failure mode where the team keeps optimizing the 8% because the 92% is uncomfortable.
**Alternatives considered**: Standalone archival compressor (rejected by F-8's arithmetic); attestation/restorability framing where value is not cost (docs/07 Blueprint E — retained as the live alternative if this fails); provenance spin-off (Blueprint D — parked). [withheld: Blueprint D, Blueprint E, docs/07 not in this repository; see WITHHELD.md]
**Reversibility**: Cheap; positioning is words until code follows it.
**Source**: F-8, F-4, docs/07-review-and-ideas.md, docs/08-why-this-dies.md killers #1 and #3. [withheld: docs/07-review-and-ideas.md not in this repository; see WITHHELD.md]
**Dated note (2026-10-18)**: this decision's Context rests on F-8's placeholder-input figures. The audit of 2026-10-18 (docs/audits/2026-10-18-image-audit/README.md, item B3) found that with any decode rate the record measured, lsp1 costs more than zstd -19 even with packing free, so the free-packing branch this positioning rests on does not survive measured inputs; the verdict that the standalone thesis loses survives every input set the audit's refuters tried, and the reason given for it does not. The decision stands as written, its confidence tag unchanged.

## D-15 - Lockstep is consumed by amber as a sibling editable dependency; amber's rank-stability census is E-006's cousin [imagined]

**Context**: The amber project (verified archives: compress with a target LLM, decode with the draft alone, byte-exact, attesting) needs a determinism contract for draft replay and an integer coder for its arithmetic-coding upgrade. Lockstep has both in lsp0 form but no LLM adapter (TP-1/TP-2 blocked on E-006).
**Choice**: Amber depends on this repo as `lockstep-archive` via editable sibling install (`pip install -e ../lockstep-ultimate-repo`), importing `rac`, `manifest`/`errors` patterns, `drbg`, and `envprobe`; it does not copy source. Amber's Phase 2 (rank-flip census across dtype/quantization/batch on one box, CPU as the second "device") is treated as the first execution of E-006's protocol with a weaker success criterion: amber's rank codec needs only ORDER stability of the draft's top-k, not grid-boundary stability (amber F-2). Results flow back here as E-006 evidence; lockstep does not fork its own census until amber's has run.
**Why**: F-8/D-14 say this thesis survives only where packing is a byproduct of inference already running; serve-time speculative decoding is that regime literally, and amber is the codec that makes the trace a file format. Sharing one census avoids two repos measuring the same drift on the same 3080 Ti.
**Alternatives considered**: Copying rac.py into amber (rejected: silent drift between copies, the failure D-9's vector governance exists to prevent); making amber a subpackage here (rejected: different regime, different findings namespace, different kill criteria).
**Reversibility**: Cheap; a dependency line and a protocol-sharing agreement.
**Source**: amber F-2/D-5 (rank stability narrowing), F-8, D-13/D-14, E-006, TP-4; amber repo `Desktop/amber` (DECISIONS D-7).

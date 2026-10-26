# Pre-publication image audit of amber, 2026-10-17

Read-only. The tree was untouched at 69b437c throughout; this report and the front-door
revision beside it are the commits after it (three: the first on 2026-10-17, two corrections
on 2026-10-18 after a critic's rounds). The audit's working files (the finders'
and refuters' JSON, their scratch scripts, the two reader walkthroughs) stay in the author's
private scratch and are not shipped; the counts below were printed by a tally script over
those files on 2026-10-17 and the recomputed figures are the refuters' own, each reproduced
from the committed files at 69b437c with code of their own.

## How it was run

- 62 tracked files outside results/, 11,501 lines (`git ls-files | grep -v ^results/ | xargs wc -l`),
  in five slices: the core codec and formats (src/amber/bits.py, codec.py, rac_codec.py,
  binformat.py, rankcensus.py); the real-model layer (src/amber/real/); the eleven
  experiment scripts with their seven protocols; the errata machinery (errata_recompute.py,
  errata_lib.py, errata_text.py, ERRATA_PROTOCOL.md, docs/ERRATA_PLAN.md, the payloads and
  the critic report); the tests, tools and project wiring.
- Each slice was read by two Opus finders (a correctness lens; a craft lens), the record
  documents by one more (FINDINGS, DECISIONS, OPEN_QUESTIONS, BLUEPRINT, PRIOR_ART,
  WHY_THIS_DIES, README, CLAUDE.md, the protocols), and a staging export of the public
  layout by two readers in role: a research scientist with thirty minutes and a hiring
  manager with five. Every finding then went to a default-refuted Opus refuter for its slice
  (six refuters), who reproduced each claim with their own code, searched the record for
  prior disclosure, and added what the finders missed. Nineteen agents in all; the
  orchestrating assistant wrote the briefs and this report and ran none of the recomputes
  itself except the protocol-freeze check below.
- Tally: 141 findings as found (17 high, 73 medium, 51 low); 101 confirmed, 38 downgraded,
  2 upgraded, 0 refuted; 11 added by the refuters. Survivors: 152, of which 7 high, 62 medium,
  83 low. That no finding was refuted outright is itself a datum: the finders quoted lines
  and ran code, and the refuters' work went into severities, prior disclosure and the
  finders' own wording (several titles carried a wrong number or a reversed conclusion, noted
  below where it matters).
- Limits. Finders, refuters and the assistant are agents of one model family; the human
  arbitrated the report, not the individual verdicts. Nothing here was recomputed by a
  person. Severity: high = a reader would be misled, a label's words are wrong or CI would be
  red; medium = a real defect or a stale sentence with no label at stake; low = craft.

## The answer to "what does the repository tell a stranger"

Both readers hit the same thing first: the tagline on line 1 of README.md ("compress with the
target model, decode with the draft alone, byte-exact, self-describing, attesting") is
withdrawn by the erratum blockquote on line 5 (the draft codes both ends; real archives
carry no attestation), and 64.6% of the README's words sat in erratum blockquotes (1,031 of
1,596, the refuter's count). The researcher would cite the record narrowly, as a one-machine
measurement of decoder-side numeric drift (the fp32 contract: 200 of 200 archives decode on
the GPU and 24 of 24 on the CPU; bf16 fails 84% and fp16 28.5%), would reuse the P1 rank
shards, the P4 archives, the census instrument and the errata method, and would dismiss the
headline rate as a general result because 60.7% of the generated tokens sit in exact loops.
They checked eight numbers from F-8, F-11, F-14 and F-16 against the committed payloads and
shards; all eight matched. The hiring manager would forward the candidate on the strength of
tests/test_hardening.py with F-4 (a seeded mutation sweep that found a silent-corruption bug
and pinned the fix), the kill criteria and the pre-registered correction pass, and would
spend the call on communication, because the first screen buried all of it.

What they would respect, merged from every reader's list and checked by the refuters:
the P1 shards reproduce F-8's divergence and arithmetic-coding rate exactly (0.067834 and
0.472296) and its unprinted secondary figures (max rank 759, mean rank 4.013), while two of
F-8's other printed figures were corrected from the same shards by rows E2 and E5; every A-class desync in F-11 is a near-tie by recompute (28 of 28 bf16, 9 of 9 fp16
under 2 tau); the errata payloads regenerate from the HEAD instrument with 0 differing values
and a second agent's recompute matched them to 0 across its passes; header sealing refuses
all 400 seeded byte mutations and all 689 single-bit header flips with a typed error; the
tie-escape tests show both where the escape works and where it does not; the capture is
atomic and resumable with provenance pinned in every committed archive; the format core
imports without torch; the suite runs in about 2.5 seconds with no model and no GPU and
nothing skips silently; negative results are stated plainly (the coder upgrade gains 1% and
loses 40% on short archives; shared-context sessions lose; the zstd baselines are called
strawmen at the per-archive scale by the record itself).

## A. Before the public push

1. **One test needs scipy, which amber never declared** (S4-C-1, S5-C-1; high). With scipy
   hidden from the import system the suite reads 1 failed, 159 passed, and the one failure
   is tests/test_errata_recompute.py's Garwood-interval test reaching experiments/errata_lib.py.
   The refuter rebuilt the public layout in a Linux container with the root README's own
   install line and got the same 1 failed, 159 passed. Fixed in this commit: pyproject.toml's
   dev extra declares scipy. Also undeclared and not fixed here: zstandard, transformers,
   torch, bitsandbytes and huggingface_hub, which the experiments and the errata recompute
   import; the suite does not need them.
2. **The quickstart's first command fails in the public layout** (S5-C-7; medium): README.md's
   install line names the author's sibling checkout folder, which the public repository
   calls lockstep/. Fixed in this commit by the install paragraph of the new first screen;
   the original line stays in the kept section below it.
3. **The tagline and the package description still state the withdrawn claim** (S4-K-3,
   R-11; medium). Fixed in this commit: the first screen opens on the corrected statement and
   pyproject.toml's description no longer says "compress with the target" or "attesting";
   the original tagline stays as the first line of the kept record, under its erratum.
4. **docs/ERRATA_PLAN.md step 1 (2026-10-10) calls the token-id folders results/p1, p4, p5
   and p6 "private-repo evidence, never for public release"** (S4-C-4, S4-K-4; medium). They
   are the inputs of F-8 and F-11 to F-13 and of every errata row (main() loads P1 before any
   row). The public cut's export flags that sentence as an operator decision: ship the four
   folders under the repository root's Llama notice, as sideband's own model-output files
   ship, with a dated note here, or withhold them and the evidence with them. Not decided in
   this commit.
5. **Private history.** Of the 119 input entries the three errata payloads pin (20 of them
   tree ids, the rest blob ids), at 69b437c 94 resolve at the tree and 25 only in history (21
   record files the errata landings themselves changed, 4 the batch-1 and batch-2
   instrument versions); at the front-door commits 91 and 28, the three more being
   pyproject.toml, which all three payloads pin and the first front-door commit edited. Of
   the 75 rows of the protocol's source tables (60 blob ids and 15 tree ids), 59 match
   current files and 16 are history-only at 69b437c, 58 and 17 at the front-door commits;
   37 commit ids are cited across the
   protocol, the critic report, the plan and
   FINDINGS.md; the errata's 100 file:line claim-site addresses resolve only at the private
   commits they name, and at HEAD several already point at other lines. A fresh-history
   export keeps none of that order; the public cut answers with the folder's scrubbed commit
   log and a restricted bundle of the private histories (sideband's plan, 14.2 item 4 and
   15.1 call 4). On the author's machine the HEAD instrument regenerates all 20 non-network
   rows of the three payloads with 0 differing leaves. From the public folder the recompute is
   partial by construction: five rows (E8c, E15, E16, E17, E19) read logit dumps that were
   never tracked; the export's patent withhold moves the bytes of docs/PRIOR_ART.md, which
   two entries pin (src/amber/rankcensus.py, also pinned, ships byte-identical: item 7); and in
   a subfolder layout the provenance lookups record None (item 6).
6. **In a subfolder layout the errata provenance records every input as None** (S5-C-5;
   medium): experiments/errata_lib.py and errata_text.py look files up as `HEAD:<path>`,
   which git resolves from the enclosing repository's root; the refuter reproduced 50 of 50
   inputs as None in a scratch monorepo with the tree still reporting clean. The committed
   payloads were written in the private layout and are unaffected; a rerun from the public
   tree would not be. `HEAD:./<path>` works. Not changed here (errata_lib.py is an input the
   protocol pins by digest).
7. **Absolute home-directory paths sit in committed evidence** (MISSED-S2-2; low): the
   critic's recompute scripts under results/errata_critic/, four payload JSON files and two
   logs. Frozen bytes; the export discloses each as residue and flags the seven scripts whose
   path's parent folder is a word of its deny list for the operator. For the same reason the
   private sibling repository's name in src/amber/rankcensus.py's docstring stays as name-only
   residue rather than taking a marker: two errata payloads pin that file's blob.

## B. Record-level: candidates for dated errata, none landed here

The record's rule is a dated erratum beside the sentence, never a rewrite; each item below
names the sentence and the recompute. No finding's status word (a PASS or FAIL, a CORRECTED
or CONFIRMED) changed under any of them. What moves are sentences, scopes and printed
figures: three pre-registered P3 band readings read differently from the committed payload,
bands (i) and (ii), which the record reports as held, as missed, and band (iii), which the
record reports as not fired, as fired on two pairs under the pre-registered rule (items 3
and 15), and F-12's byte breakdown (item 6).

1. **F-13's "confines a desync to its turn"** (S2-C-1; high; also D-11 and finding (4)). The
   draft context does restart each turn (turns 2 to 4 decode exactly on their own after a
   perturbed turn 1), but the shipped decoder raises one error for the whole session and
   returns nothing, and the v4 format carries one digest per session, so no decoder could
   check a turn. The cited test (tests/test_sessions.py) passes identically on a shared-mode
   archive. Fix: scope the word to the draft context.
2. **F-13 (3)'s "~4.1k-token KV contexts"** (S3-C-2; high). The k=8 sessions actually decoded
   average 2,066 tokens (longest 2,164); 4.1k is the length of the k=16 sessions, which were
   never decoded. The fp32 contract is shown to about 2.2k tokens.
3. **F-10's "top-1 desyncs -> 0", D-8's and the README's "removes top-1 desyncs as
   designed" (DECISIONS.md:82-83, README.md:35-36) and the P3 protocol's "band (i) held for
   A/T"** (S3-C-1; high). The P2b payload has T desyncs: 9 and 8 for fp16 at theta 0.142,
   115 and 200 for bf16 at theta 0.93 (m=2 and m=4 of one bf16 pair); positions where the
   encoder's top-1 was correct still desync, coded as T. No errata row covers it.
4. **F-2's "L1 = target divergence-set equality" and E12's "stands as stated"** (S1-C-8;
   high, upgraded by the refuter). `attest_with_target` compares the correction count and
   the tokens it is given, never the payload or positions: a resealed payload swap with the
   same count passes the fingerprint pin, the payload digest and L1, then decodes silently to
   different tokens at 98 of 400 positions. F-2's measured numbers stand; F-4's caveat
   already disclaims forgery resistance.
5. **D-8, K-3's status line and BLUEPRINT Phase 2 still say fp32 order is free across
   CPU, GPU and batch at every depth** (R-1; high), with no pointer to E8a (one desync at the
   shipped theta 0; the order claim "false at every theta") or E8c (one batch-8 fp32 desync at
   every theta). The errata were attached only to the sites the protocol listed.
6. **F-12's byte breakdown** (S1-C-7, S1-K-1, S5-K-2, MISSED-S1-1; medium). The 200 committed
   v3 archives carry 98 B (27) or 99 B (173) of framing, mean 98.865, against the 97 B
   `fixed_overhead_bytes` returns and F-12 prints; 3.17 + 0.57 + 0.45 sums to 4.19 (4.1995)
   against the measured 4.2605, the rate-law constant moves from 917 to about 932 bits and the
   zstd crossover from L 263 to about 267.5. E18 reprints the 97 B figure at eight sites
   ("1.050 without its 97 B fixed header" reads 0.989 with the real headers; "L 273 to 288"
   reads 278 to 293); its statuses do not change. 97 B is the true floor, so D-10 stands.
7. **The "3.65x the bf16 replay time" cost of the fp32 contract** (S3-C-4, S3-K-2, R-3,
   MISSED-S2-1; medium; seven sites, D-8, F-9, OQ-2, README.md:38 and K-3 among them). It is
   the ratio of unweighted per-shard means of teacher-forced capture rates, the averaging E5
   corrected elsewhere; token-weighted it is 5.17x and by median shard 4.74x, and it was never
   a replay measurement. F-11's replay ran fp32 at 26.3 tok/s against bf16 at 17.4, with the
   record's own caveat that the harness is dominated by Python overhead.
8. **F-1's "flat ~1.3-1.4 bits/token" overhead is a ratio (1.32x to 1.36x); in bits per token
   it runs 0.20 to 2.33** (S3-C-3, R-5; medium), and the reading spread to P1_PROTOCOL.md,
   BLUEPRINT.md and F-9's caveat.
9. **F-7's throughputs** (S2-C-5, R-4; medium): 1.5k and 17k match no average in the result
   file; weighted by positions the batch-1 fp32 GPU run is 1,422 pos/s and bf16 batch-8 4,875.
   F-5's figures move by at most 7% and stand.
10. **The Phase-1 headline at four front sites** (R-2; medium: README, OQ-1, BLUEPRINT and
    the K-2 status line) quotes 0.474 bits per token, 7.6x zstd and the tie with arithmetic
    coding without the E3/E4 mixture (on the 75 rows without loops amber reads 0.893 against
    0.809). The finder's reading that the P7 loop rule would call the corpus degenerate did
    not hold: at the rule's own window of 512 the median loop fraction is 0.0; the 0.859
    appears only at E3's window of 128.
11. **README.md:41 ("as F-10 predicted") and BLUEPRINT.md:77-78** restate the cross-regime
    comparison E15 corrected, with no note (S4-C-6; medium).
12. **P6's pre-registered pooled readouts over turns 2+ are never printed; F-13 quotes single
    turns** (S3-C-6; medium). The content band (1.288x) sits inside its [0.8, 1.3] range and is
    never scored, and shared mode codes each later turn's start token as a prompt symbol while
    reset mode does not (undisclosed). The finder's "no saving" headline was reversed by the
    refuter: counted alike, shared mode saves on prompts at 6 of 7 turns (0.887x pooled), and
    F-13's "barely appears" stands. Adopt no wording from the finder.
13. **F-8's "strongly front-loaded" divergence curve is mostly loop tails** (S3-C-8; medium):
    looped rows fall from 11.8% to 0.01%, non-looped rows from 20.9% to 5.5%.
14. **The archive-level rate tables of F-11 to F-13 carry no arithmetic-coding-under-draft
    row and no own-bound row** (S3-C-9; medium), which D-6 requires; E18 later supplied the
    dictionary comparator.
15. **The P2b pipeline-bug check used a pair budget looser than the pre-registered
    2 tau_decoder rule, by 2x to about 5,400x across the pairs (8x and about 5,400x on the
    two pairs where the pre-registered rule fires band (iii) and the looser one does not)**
    (S3-C-5; medium); F-10 names the rule it used.
16. **F-6's only evidence, and F-7's grid-crossing half, is a payload whose producing code
    was never committed** (MISSED-R-2; medium); the rates reproduce from the local dumps by the
    rule in the payload's regime string, and D-8's ban on value contexts cites them.
17. **Protocol freeze provenance** (S3-K-1, MISSED-R-1; medium). Git shows the P1 protocol
    entering history about three hours before its payload, the P2 protocol in a commit that
    carried only a 64-position smoke payload, thirteen minutes before the commit that carried
    its full payload (the untracked capture files' write times put the start of that run
    seconds after the protocol commit), and the errata protocol twelve minutes before its
    first payload; the P3 to P6 protocols
    entered in the same commit as their results (the payload files were written one to three
    minutes before that commit). The protocols' "Frozen ... before" lines are self-attested
    for those four.
18. **Stale status lines** (R-7, R-14, S1-C-10, S1-K-6, S2-C-3, S3-K-4, S5-K-5, OPEN_QUESTIONS.md:14;
    medium): nothing a stranger opens first said the work is parked (this commit's first screen
    does); README and BLUEPRINT end in "Next:" lines naming the withdrawn P7; the Status
    heading says v0.2.0 against pyproject's 0.4.0; D-10 has no pointer to E11; F-4's "the
    payload still carries no digest" and bits.py's "future upgrade" predate D-8; the
    "offline-first" loader docstring predates the E7 amendment that found it false for Llama-3
    tokenizers; p7_longhorizon.py and the Makefile's p7 target do not say P7 was withdrawn.
19. **The pre-publication gate** (R-9; medium): BLUEPRINT's "Gate before anything public"
    (counsel plus a fresh prior-art search) has no recorded outcome. The owner's call: passed,
    waived, or moot by parking, in a dated line.
20. **The premise stated as fact** (R-6; medium): BLUEPRINT's "IS that regime ... zero marginal
    pack cost" was never measured; README calls it a premise and OQ-5 and K-4 leave it open.
21. **F-14's "not carried" reason, that no reader will see the planning documents** (R-8;
    medium), is voided by publication; the public cut withholds the patent passages (R-10) and
    keeps the rest as the record.

## C. Guards weaker than their names

- The forged-field battery of tests/test_hardening.py forges without resealing, so 10 of its
  29 cases are refused by the header digest before the check they name runs; deleting any of
  the five field validators (coder, tie_margin, tie_topm, cfg fields, max_rank) leaves the
  suite green at 160 of 160, and with the tie_topm check gone a resealed forgery leaks a bare
  IndexError (S1-C-4, S1-K-3, S5-K-3). The fix is to recompute only header_sha in the
  helper; calling reseal() would itself raise on the malformed-cfg cases.
- The "every failure is a ValueError" contract leaks TypeError, AttributeError, MemoryError
  and IndexError on resealed headers (S1-C-1, S1-C-3, S1-K-2, S2-C-7): tie_topm is bounded by
  1024 and not by the vocabulary or the stepper's top-K; cfg and the declared length are
  unbounded at the parser (E11 records the lost ceiling; the new fact is the bare MemoryError
  at the 2^35-1 maximum); length 0 passes validation and crashes encode and decode (S1-C-2);
  encode never validates the header it writes (S1-C-5).
- Nothing binds the payload numbers to the landed errata text: a changed payload number in
  memory passes, and the payload-to-text test's xfail branch is permanently armed for F-14
  and F-15 (S4-C-2, S5-C-2). Today the landed blocks match the generator line for line.
- The session containment test does not tell reset from shared mode (S5-K-4, item B1).
- Capture resume binds shards by shape and key names only: a rebuilt corpus or --force keeps
  the old shards and restamps meta.json with the new corpus hash, so a mixed arm passes the
  census script's own corpus check (S2-C-2, S2-K-3). Committed evidence is unaffected (200
  unique rows per stage).
- Reruns overwrite committed evidence in place: every experiment script rewrites its payload
  with a fresh timestamp, `make experiments` rewrites three committed results (with CRLF
  bytes on Windows, which `results/** -text` then keeps), and a non-dry errata run refetches
  the arXiv pages into results/errata_web/ and rewrites the batch-1 payload (S3-C-10, S5-C-4,
  S4-C-3). The pages were fetched three times and committed once; arXiv served identical
  bytes each time.
- The findings lint reads only the first physical `- source:` line and flags a path:line
  token even when the file exists; nothing slips through today (94 of 94 source tokens
  tracked) (S5-C-3). It reads FINDINGS.md in the platform's default encoding (MISSED-S5-1).
- The fp32 rule and the model pin are checked after the fact by the content hash; the dtype
  is a literal the caller types, no experiment passes expected_fingerprint, and TF32 and
  matmul precision are neither set nor recorded (S2-C-4).

## D. Craft

- The rank formula is written five times; the one tested copy is called only by tests and
  the three torch copies produced every committed rank (S2-K-1). p4 and p5 share 42 identical
  lines, 31 lines recur in three or more of p4 to p7, zstd-19 counting is written six times
  (S3-K-7); the archive parser repeats codec.py's checks with vaguer messages (S2-K-4).
- The generator inserts erratum notes with no blank line before body text, so the README's
  Status section renders as one blockquote of 7,978 characters holding 6 note lines and 33
  original lines, and 13 original lines of OPEN_QUESTIONS.md sit inside quotes (S4-K-1); the
  README notes other than E16's do not quote the wording they correct (S4-K-2).
- The hf payload's escape code is documented as 0 and written as 64 (S2-K-2); `RankCensus.tau`
  holds 2 tau (E17 corrected the labels; the name stays, in a file the protocol pins).
- 9 of the Makefile's 14 targets cannot run from a fresh clone; the quickstart's sibling paths
  are the author's; `lockstep-archive` is not on PyPI (S5-K-8, S5-K-7).
- Private CI never ran the suite: 3 of 6 remote runs failed at the sibling checkout and 3
  never started; tools/lint_findings.py's docstring says CI runs it on every push (S5-K-1).
- Session bookkeeping and cross-repository ids in docstrings; 143 lines of experiment code
  join statements with `;`; 8 ruff F-rule errors across six scripts; no `--help` text and
  four CLI shapes (S3-K-8, S3-K-10, S3-K-12).

## What this commit changes, and does not

Changed: README.md gains a plain-language first screen above the record as it stood on
2026-10-11, which is kept beneath with its errata in place; pyproject.toml's description
states the corrected claim and its dev extra declares scipy; this report. Not changed: any
finding, decision, protocol, payload or result; any sentence in section B, which are dated
errata for amber's own lane to land after a recompute; the test weaknesses of section C.

# F-24 support-number artifacts (2026-10-16)

Lever 2 of docs/PUBLIC_CUT_PLAN.md section 14.2, the rider of the S1 READER RE-TEST REGISTRATION [withheld: docs/PUBLIC_CUT_PLAN.md not in this repository; see WITHHELD.md]
(docs/BLUEPRINT.md, 2026-10-16). FINDINGS.md F-24 quotes three support figures with the words "no committed
artifact records it": the cross-seed collapse of the twin payloads' per-cluster correlations with a
same-subtrahend control (F-24 (iii)), a position-only predictor's gain over the floor (F-24 (iii)) and
the per-anchor input norms of the full-free arm's blocks (F-24 (iv)). The image audit's researcher
walkthrough (docs/audits/2026-10-15-image-audit/README.md) named them as a doubt. The three scripts here
are those artifacts. They train nothing and cannot move a label; F-24's three clauses stay as written and
its dated note of 2026-10-16 points here.

## Convention

Each script resolves the repository root from its own location, pins in its header the figure F-24
states BEFORE the rerun (the pins are F-24's figures; the constructions are the script's and are named),
and writes its output next to itself as LF JSON with every value and each pin's verdict. Unlike the
2026-10-15 audit folder's scripts, which write only when every pin holds, these ALWAYS write and exit
non-zero on a failed pin: a figure that does not reproduce is the rider's result, and it belongs on the
record beside the figure it fails, not in a missing file. A missing-shards refusal also exits non-zero,
with its own message and no output written. Every output records the numpy version it ran under (2.3.5
here; the bootstrap in `position_only.py` draws from numpy's Generator, whose streams are not promised
stable across releases).

## Files

- `corr_control.py`, `corr_control_out.json`: F-24 (iii), the correlations. Reads the four committed twin
  state files and the full-free state files they paired against, bound by the sha256 each twin payload
  recorded for them (numpy only, a second). A: reproduces the twin payloads' pooled per-cluster
  correlations (Mt against Mn_r, Mt against Mn) to 0.0 on all four harvests. B: the cross-seed
  correlation, Mt from train seed i against Mn_r from seed j != i, the six ordered pairs and their mean.
  C: the same-subtrahend control under this file's reading, Mt from seed i against acc(fplus_j) -
  acc(fplus_i), j != i (a delta sharing Mt's subtrahend whose minuend is another seed's full-free probe,
  no slots block). D, descriptions: pooled Mn against Mn_r; cross-seed Mt against the shift twin's Mn;
  the pooled RAW accuracies of fplus_b against fplus_r and fplus_n.
- `position_only.py`, `position_only_out.json`: F-24 (iii), the position channel. On both PRIMARY
  harvests at the gate cell (offset 2, the L1 space), the per-anchor-index majority predictor fitted on
  TRAIN anchors against the constant TRAIN-majority predictor on TEST anchors, through the registered
  anchor table, label spaces and split; the gain as the Phase-3 paired cluster estimand; a binned (eight
  indices) variant beside it. Reads the gitignored harvest shards (docs/DATA.md), so it refuses elsewhere.
- `input_norms.py`, `input_norms_out.json`: F-24 (iv), the input norms. On the S1 PRIMARY at the gate
  cell, the fplus_b arm's blocks built through the frozen classes the registered cells used (the six (a)
  blocks, TokAnchorBlock, HiddenZBlock with the TRAIN moments asserted equal to fullfree_s1.json's,
  SlotsAnchorBlock), the per-anchor L2 of each block over every TEST anchor, and the per-anchor hot
  counts of the two multi-hot blocks. Loads the primary's hidden array (about 3.5 GB); refuses without
  the shards.

## Results (2026-10-16, every pin held)

| Figure | F-24's words | Pin | Read |
|---|---|---|---|
| A reproduction, all four harvests | the recorded "+0.58..+0.76" (see below) | max abs diff <= 1e-9 | 0.0 on each (S3 primary pooled Mt vs Mn_r 0.7554, Mt vs Mn 0.6470) |
| B cross-seed, S3 primary | "collapse to about +0.1" | mean in [0.00, 0.20] | +0.1127 (pairs -0.189..+0.511; within-seed mean +0.7837) |
| C same-subtrahend control, S3 primary | "+0.49" | mean in [0.39, 0.59] | +0.4815 (pairs +0.220..+0.638) |
| Position-only gain, S1 and S3 primaries | "gains nothing over the floor" | <= +0.002 | 0.0 exactly on both; floors 0.591381 / 0.580311 reproduced to 1e-12 |
| hz per-anchor L2 median, S1 primary | "about 65" | in [55, 75] | 65.21 (p10 57.27, p90 68.93, max 72.36) |
| slots per-anchor L2 max, S1 primary | "at most about 11" | <= 11.4 | 11.3137 (= sqrt(128); median 11.14) |
| TOK per-anchor L2 median, S1 primary | "about 6" | in [5, 7] | 5.66 (max 5.6569 = sqrt(32)) |

Said in words:

- F-24's "+0.58..+0.76" covers the two S1 harvests and the S3 primary; the S3 replication's recorded
  pooled values are +0.4062 (Mt vs Mn_r) and +0.4500 (Mt vs Mn), as the twin OUTCOME in docs/BLUEPRINT.md
  lists them, and A reproduces all four pairs to 0.0. A dated correction; F-24's sentence stays as written.
- The cross-seed collapse holds on the S3 primary as F-24 states it, and on the other three harvests as
  descriptions: cross-seed means +0.0871 (S1 primary), -0.0326 (S1 replication), -0.0883 (S3 replication),
  against within-seed means +0.7026 / +0.7109 / +0.5020. On the S3 primary three readings of the same
  per-cluster deltas sit side by side: sharing neither the subtrahend nor the train seed (cross-seed B)
  gives +0.1127; sharing only the subtrahend (the control C) gives +0.4815; sharing the
  subtrahend and the train seed (within-seed Mt against Mn_r) gives +0.7837. Correlations do not add, so
  no share is attributed to either part; the three readings are what the artifact is made of. The
  raw-accuracy correlation of fplus_b against fplus_r (+0.9965 pooled, no shared subtrahend) says only
  that both arms are the same probe plus a block.
- The record does not say how the critic built its "same-subtrahend control". Construction C (pinned
  here before the rerun) reads +0.4815 on the S3 primary, +0.48 at two decimals against F-24's +0.49:
  approximated, not reproduced to the last digit. The second reading D, pooled Mn against Mn_r, reads
  +0.4671 there; D is not a same-subtrahend-only control (fplus_n and fplus_r share the train seed and the
  6801 free dims as well as the subtrahend), so it stays a description. From this folder on, C is the
  committed definition.
- The position channel carries nothing a majority-beating predictor can use at this cell: on both
  primaries every one of the 255 anchor indices has train anchors and the per-index majority is the global
  majority at every one of them (no index predicts a non-majority class), so the position-only predictor
  IS the floor and its gain is 0.0, not merely negligible. One predictor; a reader keyed on position
  jointly with the blocks is not what this measures.
- The norm dominance of F-24 (iv) is as stated: the standardised hz block's median per-anchor L2 is 5.9
  times the slots block's and 11.5 times TOK's (29 times the (a) summaries' 2.23). The hot counts behind
  the two sparse blocks' norms: TOK is 32-hot (its construction maximum) for 82.1% of the test anchors
  (median 32, min 28, where hashed ids collide); the slots block is 128-hot for 1.6% of them (median 124,
  p10 122, p90 126, min 115), so its typical norm is sqrt(124) and its maximum sqrt(128). The shortfall is
  the harvest's own padding, not repeated ids: over the 61,030 test anchors the stored slot rows hold
  237,337 entries of -1 (3.89 per anchor, 128 - 3.89 = 124.11, the mean hot count) and no slot id repeats
  within a layer (0 counted), as `input_norms_out.json` records.

Rerun: `python docs/audits/2026-10-16-f24-support/<script>.py` from any directory; the two harvest-reading
scripts need the shards on disk.

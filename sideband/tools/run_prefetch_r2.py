#!/usr/bin/env python
"""tools/run_prefetch_r2.py — OQ-9 STAGE-1 POST-HOC DIAGNOSTIC: the GENERALISING FREE
BASELINE (R2) for the free-bigram twin's margin (F-26's 2026-10-02 status line), with the
forward's stored final-norm state as a second question.

Registered 2026-10-02 as a dated AMENDMENT to the stratified coverage read block in
docs/BLUEPRINT.md ("OQ-9 STAGE-1 GENERALISING FREE BASELINE REGISTRATION (R2)"), written
before any readout of it ran on either S3 harvest. NON-CRITERION for every finding's
mechanical label; it executes ONE pinned consequence, a dated STATUS line under F-26 (the
third). CPU only; numpy only — nothing in this file imports torch, transformers or
safetensors, so its tests run in CI; the checkpoint's safetensors files are parsed by
their 8-byte length prefix and JSON header.

WHY. The stratified read located the material part of the twin's surviving margin on the
positions with at least one unseen key, where a free count table reads the marginal, and
reported that the margin falls with the key's train coverage: an undertrained free table
and address information beyond the tokens are unseparated there. Two questions, read on
the same positions:
  Q1 (SPARSITY)  with the free tables replaced by an encoding that generalises across keys
                 — the model's own routers REPLAYED on the token's normalised input
                 embedding as the Dirichlet prior of a smoothed count table — how much of
                 the twin's free arm's deficit is recovered (SHRINKAGE, the headline), and
                 does the address block still beat the equal-dims free block on the
                 unseen-key positions, and pooled?
  Q2 (HIDDEN)    with the forward's final-norm state h_a (the harvest's 'hidden'; F-24's
                 free block, F-23's carrier of p) in the free arm at the address block's
                 width, does the address block still beat the equal-dims free block, and
                 does the address stream still add over the union?

THE FROZEN INSTRUMENTS. tools/run_prefetch_strat.py (sha 39a6cd587492..., attested by
both committed stratified payloads) is imported by bare module name and NEVER edited;
this file refuses to run unless its LF-normalised bytes still hash to that sha. Its own
import-time assertions cover the twin (10599fa98c27...) and the stage-1 parent
(8529532d4d78...). Its Strat class is reused for the twin's tables, the leave-one-prompt-
out reads, the bigram positions, the twin's design, the six coverage strata and the val
selection rule; the twin's Gram is accumulated here by the twin's own statement on the
same chunks and the twin's nine arms are solved at the twin's SELECTED lambdas read from
the committed stratified payload (which carries the twin's), so those arms ARE the twin's
readers and their stratified rows are the stratified read's rows (REPRODUCE).

INDEX CONVENTION (the frozen one): forward t has INPUT tokens[t-1], OUTPUT p_t, routing
S[t] and final-norm state hidden[t]; tokens[t] is sampled from p_t. At anchor t the
decoder holds S[t], tokens[t], tokens[t-1] and hidden[t]; the target is S[t+1], the
routing of the forward tokens[t] feeds. REPLAY(x) at gate l estimates gate l of the
forward x FEEDS: REPLAY(tokens[t]) is aligned with the target, REPLAY(tokens[t-1]) with
S[t] (one forward before the target).

THE REPLAY ENCODING. REPLAY(x) in [0, 1]^1024: per gate l the softmax over the 64 experts
of W_l . RMSNorm_l(e_x), e_x row x of the input embedding, RMSNorm_l(v) = v / sqrt(mean
(v^2) + eps) times layer l's post-attention norm weight, W_l the layer's router. Model
weights only; defined for every token id. The source is the cached checkpoint snapshot
pinned below; the sha256 over exactly the tensors the replay reads (name, dtype, shape and
BF16 bytes, in a fixed order) is REPLAY_SOURCE_SHA256, and a registered run refuses any
other source. A fixture source (an .npz with embed / gates / norms / eps) serves the tests
and is refused under results/.

THE SMOOTHING FAMILY. SMOOTH_k(x)[g, e] = (c + k r) / (n + k) with c the twin's train
count (leave-one-prompt-out at train rows), n the row's count sum at the gate (8 per
train occurrence), r = REPLAY(x) at the gate, k in COUNT units. k = 0: the table where
n > 0, the replay where n = 0 (BACKOFF); k = inf: the replay everywhere. One k for both
tables, selected jointly with lambda for the free arm on the pooled VAL positions (strict
>, ties keep the smaller k then the smaller lambda; grid-edge flagged). K_GRID
{0, 2, 8, 32, 128, 512, inf}.

THE HIDDEN BLOCK. H(t) in R^1024: hidden[t] (2048 float16 -> float64) clipped per
channel to the TRAIN support, z-scored with TRAIN moments (a zero sd replaced by 1), then
projected on the 1024 leading principal directions of the TRAIN covariance (eigh in
float64, eigenvalues descending, each direction's sign fixed so its largest-magnitude
coordinate is positive). Train support, moments and directions never see a val or test
row.

DESIGN. The twin's Gram [S[t] (1024) ++ TABLE_CUR(tokens[t]) ++ TABLE_PREV(tokens[t-1]) ++
TABLE_CUR(tokens[t-1]) ++ bias] (4097; the twin's statement on the twin's chunks), plus
the blocks the new arms need, accumulated on the same chunks: H with H, S and the bias;
for every k, SMOOTH_k(tokens[t]) ++ SMOOTH_k(tokens[t-1]) with itself, S, H and the bias;
every block with the targets. An arm's Gram is assembled from those blocks.
ARMS (dims; k* the selected k):
  the twin's nine at the twin's lambdas (REPRODUCE): history 1025, free_tok 1025,
    history_tok 2049, free_bigram_b/_a 2049, history_bigram_b/_a 3073, free_all 3073,
    history_all 4097 (FREE_BIGRAM / HISTORY_BIGRAM = the twin's selected encoding)
  free_r2            SMOOTH_k*(tokens[t]) ++ SMOOTH_k*(tokens[t-1])         (2049)
  history_tok_r2     S[t] ++ SMOOTH_k*(tokens[t])                            (2049)
  history_bigram_r2  S[t] ++ free_r2's blocks                                (3073)
  free_backoff       free_r2 at k = 0;  free_replay  free_r2 at k = inf      (2049)
  replay_cur         REPLAY(tokens[t])                                       (1025)
  replay_zerofit     the top-B of REPLAY(tokens[t]) itself, no fit
  h_only             H(t)                                                    (1025)
  free_h             free_r2's blocks ++ H(t)                                (3073)
  history_all_h      S[t] ++ free_h's blocks                                 (4097)
Readers: closed-form ridge in float64, bias regularised alike; lambda per arm on val
(frozen grid); resident set and hit rate as the frozen instruments count them.

READOUTS at B = 16 (8 and 32 reported), paired per prompt within a scope (six strata,
three unions), cluster bootstrap over the 30 test prompts (n_boot 2000, seed 0):
  PRECONDITION REPRODUCE  every (arm, budget, gate, prompt, stratum) row of the committed
                          stratified state file over the twin's nine arms equals this
                          read's row, hits AND needed (EXACT; hits-only mismatches on at
                          most 0.1% of those rows within +-1 hit NEAR, said in words;
                          else INVALID, void); IDENTITY: the twin's D_eq on ALL, COVERED
                          and FALLBACK, CI included, equals the stratified payload's cells
  Q1 HEADLINE  SHR^s     = free_r2 - FREE_BIGRAM on FALLBACK / COVERED / ALL;
               SHARE     = SHR^FB / D_eq^FB (point ratio)
  Q1 GATE      D_eq^R2   = history_tok_r2 - free_r2 on FALLBACK and on ALL
  Q1 UNION     D_add^R2  = history_bigram_r2 - free_r2 (reported)
  Q2 GATE      D_eq^H    = history_bigram_r2 - free_h on ALL (3073 against 3073)
  Q2 UNION     D_add^H   = history_all_h - free_h on ALL; anchor = history_all_h -
                           history_bigram_r2 (= D_add^H - D_eq^H)
  reported: the family's ends against the table, the selected k against each end, the
  replay alone against the one-token table, history_tok_r2 - history_tok, h_only against
  free_tok and history_tok, free_h - free_r2, every delta per scope and budget, REPLAY
  AGREEMENT per split and gate (top-8 of REPLAY(tokens[t-1]) against S[t]; of
  REPLAY(tokens[t]) against S[t+1]; no fit).
Readings by the frozen rule: SIGNAL iff CI95 lower > 0 and point >= +0.05; NEGATIVE iff
CI95 upper < 0; else NOT-SHOWN. A CI95 containing the floor is a FLOOR STRADDLE; a
straddle on the Q1 gate on FALLBACK, or on either Q2 reading, selects the pinned "not
settled at this power" sentence; a straddle on the Q1 gate on ALL is said in words.
READER GUARD (critic design round): where free_h - free_r2 on ALL or the dilution anchor on
ALL reads NEGATIVE, adding H degraded a reader; the Q2 label stays mechanical but its
branch sentence is replaced by the guard's and nothing is struck. ABSORBED QUALIFIERS: the
sparsity clause needs SHRINKAGE on FALLBACK to read SIGNAL (else a no-gain clause); it is
replaced where k* is the pure-replay end; a NEGATIVE history_tok_r2 - history_tok on ALL
or FALLBACK adds the handicap clause. H-INCONSISTENT's cause is "reader" (the anchor's
CI95 upper < 0), "floor straddle" (a Q2 CI95 contains the floor) or "neither". The tool's
sentences are number-free templates; the STATUS line at landing quotes the BLUEPRINT's
pinned words with the numbers beside them.
LABELS (mechanical; the PRIMARY harvest's label is the label):
  REPRODUCE-INVALID | INCOMPLETE                              (void: numbers only)
  Q1: R2-FALLBACK-SURVIVES  D_eq^R2 on FALLBACK SIGNAL
      R2-POOLED-ONLY        not, and D_eq^R2 on ALL SIGNAL
      R2-ABSORBED           neither SIGNAL
  Q2: H-SURVIVES   D_eq^H SIGNAL and D_add^H SIGNAL;  H-COMPLEMENTARY  only D_add^H;
      H-ABSORBS    neither;  H-INCONSISTENT  only D_eq^H ("reader" iff the anchor's CI95
      upper < 0, "floor straddle" iff a Q2 CI95 contains the floor, else "neither")
  label = "Q1 / Q2", e.g. "R2-FALLBACK-SURVIVES / H-ABSORBS".
--conclude-from recomputes every table, CI, delta, the REPRODUCE and identity checks
against the committed stratified payload and state file (re-read, re-hashed, every header
field compared), the selected k and every lambda from the payload's own val tables, and
every label from the state file, and refuses a payload whose stored numbers differ. It
needs no checkpoint: the state rows carry the hits. Evidence files are written with LF
newlines on every platform.

Usage:
  python tools/run_prefetch_r2.py --harvest results/real/harvest_moe \
      --out results/real/prefetch_r2_s3.json
  python tools/run_prefetch_r2.py --harvest results/real/harvest_moe_r \
      --out results/real/prefetch_r2_s3_r.json
  python tools/run_prefetch_r2.py --conclude-from results/real/prefetch_r2_s3.json
Smoke (disclosed in the registration; refused under results/; no stratified payload read):
  python tools/run_prefetch_r2.py --harvest results/real/harvest_moe_r \
      --only-seeds 8 --smoke-split-val --strat none --out <scratch>/r2_smoke.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import struct
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import run_prefetch_readouts as pr  # noqa: E402  (the FROZEN stage-1 instrument)
import run_prefetch_bigram as rb  # noqa: E402  (the FROZEN twin)
import run_prefetch_strat as rs  # noqa: E402  (the FROZEN stratified read; asserts its parents at import)
from sideband.probes import load_label_space  # noqa: E402
from sideband.provenance import redact_args  # noqa: E402

# the stratified tool's LF-normalised sha256 (= tests/test_prefetch_strat_landing.py INSTRUMENT_SHA256,
# = both committed stratified payloads' provenance.instrument_sha256)
STRAT_INSTRUMENT_SHA256 = "39a6cd587492e13d66da47ce75df0ec17ffe2ab57c3ee0ae760f4c574e110e0c"


def assert_frozen_strat(path: Path | None = None) -> str:
    """Refuse unless the stratified tool on disk still hashes (CRLF -> LF) to the attested sha."""
    p = Path(path) if path is not None else Path(rs.__file__)
    sha = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != STRAT_INSTRUMENT_SHA256:
        raise SystemExit(f"{p}: sha {sha[:12]} is not the frozen stratified tool {STRAT_INSTRUMENT_SHA256[:12]} — refusing")
    return sha


assert_frozen_strat()
rs.assert_frozen_twin()
rb.assert_frozen_instrument()

REGISTERED = ("OQ-9 STAGE-1 GENERALISING FREE BASELINE REGISTRATION (R2) "
              "(docs/BLUEPRINT.md, 2026-10-02 amendment; post-hoc diagnostic; NON-CRITERION)")
E, L, K, D = rs.E, rs.L, rs.K, rs.D
BUDGETS, LAMBDAS = rs.BUDGETS, rs.LAMBDAS
LABEL_BUDGET, MATERIAL, N_BOOT, BOOT_SEED, CHUNK = rs.LABEL_BUDGET, rs.MATERIAL, rs.N_BOOT, rs.BOOT_SEED, rs.CHUNK
HORIZON = rs.HORIZON
STRATA, UNIONS, SCOPES = rs.STRATA, rs.UNIONS, rs.SCOPES
SPLITS = pr.SPLITS
D_X = rb.D_X                             # 4097: the twin's design, bias at 4096
BIAS_COL = D_X - 1
K_GRID = (0.0, 2.0, 8.0, 32.0, 128.0, 512.0, float("inf"))
K_TAG = {0.0: "0", 2.0: "2", 8.0: "8", 32.0: "32", 128.0: "128", 512.0: "512", float("inf"): "inf"}
REPRODUCE_NEAR_SHARE, REPRODUCE_NEAR_HITS = rs.REPRODUCE_NEAR_SHARE, rs.REPRODUCE_NEAR_HITS
IDENTITY_TOL = 1e-12
IDENTITY_SCOPES = ("all", "covered", "fallback")

# the replay source: the cached checkpoint snapshot and the sha over exactly the tensors the replay reads
MODEL_ID = "allenai/OLMoE-1B-7B-0125-Instruct"
SNAPSHOT = "b89a7c4bc24fb9e55ce2543c9458ce0ca5c4650e"
REPLAY_SOURCE_SHA256 = "d8e5770a2d88a8bee02518b3f95a88fed122f9a7ce66ba3183d16fdf39936e63"
TOKEN_PROBE = (0, 1, 2, 3, 128, 1024, 8192, 32768)   # the replay vectors whose shas the meta records

ARMS_TWIN = rb.ARMS_REQUIRED
ARMS_R2 = ("free_r2", "history_tok_r2", "history_bigram_r2", "free_backoff", "free_replay", "replay_cur",
           "replay_zerofit", "h_only", "free_h", "history_all_h")
ARMS_REQUIRED = ARMS_TWIN + ARMS_R2
ARMS_RIDGE_R2 = tuple(a for a in ARMS_R2 if a != "replay_zerofit")
# block lists (bias last); "cur" / "prev" are the smoothed blocks at the arm's k (ARM_K: None = the selected k)
ARM_BLOCKS_R2 = {
    "free_r2": ("cur", "prev", "bias"),
    "history_tok_r2": ("hist", "cur", "bias"),
    "history_bigram_r2": ("hist", "cur", "prev", "bias"),
    "free_backoff": ("cur", "prev", "bias"),
    "free_replay": ("cur", "prev", "bias"),
    "replay_cur": ("cur", "bias"),
    "h_only": ("h", "bias"),
    "free_h": ("cur", "prev", "h", "bias"),
    "history_all_h": ("hist", "cur", "prev", "h", "bias"),
}
ARM_K = {"free_backoff": 0.0, "free_replay": float("inf"), "replay_cur": float("inf")}
BLOCK_SIZE = {"hist": D, "cur": D, "prev": D, "h": D, "bias": 1}
STRAT_OF_HARVEST = {"harvest_moe": "prefetch_strat_s3.json", "harvest_moe_r": "prefetch_strat_s3_r.json"}
OUT_OF_HARVEST = {"harvest_moe": "prefetch_r2_s3.json", "harvest_moe_r": "prefetch_r2_s3_r.json"}


def k_tag(k: float) -> str:
    return K_TAG.get(float(k), "inf" if np.isinf(k) else repr(float(k)))


def k_of_tag(tag: str) -> float:
    return float("inf") if tag == "inf" else float(tag)


def arm_dims(arm: str, encoding: str) -> int:
    if arm in rb.ARM_BLOCKS:
        return rb.arm_dims(arm)
    if arm == "replay_zerofit":
        return 0
    return int(sum(BLOCK_SIZE[b] for b in ARM_BLOCKS_R2[arm]))


# ---------------------------------------------------------------------------
# The replay source (numpy-only safetensors parse) and the replay table
# ---------------------------------------------------------------------------

def _read_header(path: Path):
    with open(path, "rb") as fh:
        n = struct.unpack("<Q", fh.read(8))[0]
        return json.loads(fh.read(n)), 8 + n


def _read_tensor(path: Path, name: str, hdr: dict, base: int):
    e = hdr[name]
    dt, shape = e["dtype"], e["shape"]
    a, b = e["data_offsets"]
    with open(path, "rb") as fh:
        fh.seek(base + a)
        buf = fh.read(b - a)
    if dt == "BF16":
        arr = (np.frombuffer(buf, dtype=np.uint16).astype(np.uint32) << 16).view(np.float32)
    elif dt == "F16":
        arr = np.frombuffer(buf, dtype=np.float16).astype(np.float32)
    elif dt == "F32":
        arr = np.frombuffer(buf, dtype=np.float32).copy()
    else:
        raise SystemExit(f"{name}: unsupported safetensors dtype {dt}")
    return arr.reshape(shape), dt, shape, buf


def hf_snapshot_dir() -> Path:
    cache = os.environ.get("HF_HUB_CACHE")
    if not cache:
        home = os.environ.get("HF_HOME")
        cache = str(Path(home) / "hub") if home else str(Path.home() / ".cache" / "huggingface" / "hub")
    return Path(cache) / ("models--" + MODEL_ID.replace("/", "--")) / "snapshots" / SNAPSHOT


def load_replay_source(spec: str) -> dict:
    """'hf' -> the pinned cached snapshot (embed float32 (V, Hd), gates float64 (L, E, Hd), norms float64
    (L, Hd), eps, the source sha over the tensors read); a path -> an .npz fixture (embed, gates, norms,
    eps; sha = the file's sha256)."""
    if spec == "hf":
        snap = hf_snapshot_dir()
        if not snap.exists():
            raise SystemExit(f"the pinned checkpoint snapshot is not in the Hugging Face cache: {snap}")
        cfg = json.loads((snap / "config.json").read_text(encoding="utf-8"))
        wmap = json.loads((snap / "model.safetensors.index.json").read_text(encoding="utf-8"))["weight_map"]
        n_layers = int(cfg["num_hidden_layers"])
        names = ["model.embed_tokens.weight"] + [n for l in range(n_layers) for n in
                                                 (f"model.layers.{l}.mlp.gate.weight",
                                                  f"model.layers.{l}.post_attention_layernorm.weight")]
        headers: dict = {}
        h = hashlib.sha256()
        tensors: dict = {}
        for name in names:
            f = wmap[name]
            if f not in headers:
                headers[f] = _read_header(snap / f)
            hdr, base = headers[f]
            arr, dt, shape, buf = _read_tensor(snap / f, name, hdr, base)
            h.update(name.encode()); h.update(dt.encode()); h.update(json.dumps(shape).encode()); h.update(buf)
            tensors[name] = arr
        gates = np.stack([tensors[f"model.layers.{l}.mlp.gate.weight"] for l in range(n_layers)]).astype(np.float64)
        norms = np.stack([tensors[f"model.layers.{l}.post_attention_layernorm.weight"] for l in range(n_layers)]).astype(np.float64)
        blobs = sorted({os.path.basename(os.readlink(snap / f)) if os.path.islink(snap / f) else f
                        for f in set(wmap.values())})
        return {"kind": "hf", "model": MODEL_ID, "snapshot": SNAPSHOT, "blobs": blobs,
                "config": {k: cfg.get(k) for k in ("hidden_size", "num_hidden_layers", "num_experts",
                                                   "num_experts_per_tok", "vocab_size", "rms_norm_eps", "norm_topk_prob")},
                "tensor_order": names, "sha256": h.hexdigest(),
                "embed": tensors["model.embed_tokens.weight"], "gates": gates, "norms": norms,
                "eps": float(cfg.get("rms_norm_eps", 1e-5))}
    path = Path(spec)
    if not path.exists():
        raise SystemExit(f"replay source {path} not found")
    z = np.load(path)
    for key in ("embed", "gates", "norms", "eps"):
        if key not in z.files:
            raise SystemExit(f"replay fixture {path} lacks '{key}'")
    return {"kind": "fixture", "path": rs._rel(path), "sha256": pr._sha(path),
            "embed": z["embed"].astype(np.float32), "gates": z["gates"].astype(np.float64),
            "norms": z["norms"].astype(np.float64), "eps": float(z["eps"])}


def _check_source_shapes(src: dict) -> None:
    gates, norms, embed = src["gates"], src["norms"], src["embed"]
    if gates.ndim != 3 or gates.shape[:2] != (L, E):
        raise SystemExit(f"replay gates shape {gates.shape} is not ({L}, {E}, hidden)")
    hd = gates.shape[2]
    if norms.shape != (L, hd) or embed.ndim != 2 or embed.shape[1] != hd:
        raise SystemExit("replay source shapes disagree (gates / norms / embed)")


def replay_table(src: dict, vocab: int, chunk: int = 4096) -> np.ndarray:
    """(vocab, 1024) float64: REPLAY(x) for every token id below vocab."""
    _check_source_shapes(src)
    embed, gates, norms, eps = src["embed"], src["gates"], src["norms"], src["eps"]
    if embed.shape[0] < vocab:
        raise SystemExit(f"replay source covers {embed.shape[0]} token ids, the harvest needs {vocab}")
    out = np.empty((vocab, D), dtype=np.float64)
    for s in range(0, vocab, chunk):
        x = embed[s:min(s + chunk, vocab)].astype(np.float64)              # (c, hd); the last chunk ends at vocab
        for l in range(L):
            v = x * (1.0 / np.sqrt((x * x).mean(axis=1, keepdims=True) + eps)) * norms[l]
            z = v @ gates[l].T                                               # (c, E)
            z = z - z.max(axis=1, keepdims=True)
            p = np.exp(z)
            out[s:s + chunk, l * E:(l + 1) * E] = p / p.sum(axis=1, keepdims=True)
    return out


def replay_probe(table: np.ndarray) -> dict:
    """sha256 of each probe token's replay vector bytes (ids beyond the table are skipped)."""
    return {str(t): hashlib.sha256(np.ascontiguousarray(table[t]).tobytes()).hexdigest()
            for t in TOKEN_PROBE if t < table.shape[0]}


def smooth(c: np.ndarray, n: np.ndarray, r: np.ndarray, k: float) -> np.ndarray:
    """(c + k r) / (n + k) per gate; k = 0 is the table where n > 0 and the replay where n = 0; k = inf the replay."""
    if np.isinf(k):
        return r
    if k == 0:
        return np.where(n > 0, c / np.maximum(n, 1.0), r)
    return (c + k * r) / (n + k)


# ---------------------------------------------------------------------------
# The harvests' hidden array (not loaded by the frozen S3Data)
# ---------------------------------------------------------------------------

def load_hidden(data: pr.S3Data) -> np.ndarray:
    """(rows, T, Dh) float16 in S3Data's row order (shards in meta order, the smoke's val-row filter applied)."""
    parts, orig_prompt = [], []
    # the shards are re-verified against the committed metas' shas (the frozen loader's own check, run again)
    verified = {m["npz_file"]: p for m, p in pr.verified_seed_files(data.dir)}
    for m in data.metas:
        if m["npz_file"] not in verified:
            raise SystemExit(f"{m['npz_file']} is not among the verified shards of {data.dir}")
        z = np.load(verified[m["npz_file"]])
        if "hidden" not in z.files:
            raise SystemExit(f"{m['npz_file']} has no 'hidden' array")
        h = z["hidden"]
        if h.ndim != 3:
            raise SystemExit(f"{m['npz_file']}: hidden has shape {h.shape}, expected (rows, T, D)")
        if h.shape[1] < data.T:
            pad = np.zeros((h.shape[0], data.T - h.shape[1], h.shape[2]), dtype=h.dtype)
            h = np.concatenate([h, pad], axis=1)
        parts.append(h.astype(np.float16, copy=False))
        orig_prompt.append(z["prompt_idx"].astype(np.int64))
    hidden = np.concatenate(parts)
    if data.smoke:
        keep = np.array([pr.split_of_prompt(int(p)) == "val" for p in np.concatenate(orig_prompt)])
        hidden = hidden[keep]
    if hidden.shape[0] != data.n_rows or hidden.shape[1] != data.T:
        raise SystemExit(f"hidden rows {hidden.shape[:2]} do not match the harvest's ({data.n_rows}, {data.T})")
    if hidden.shape[2] < D:
        raise SystemExit(f"hidden width {hidden.shape[2]} is below the address block's {D}: no equal-dims H block")
    return hidden


# ---------------------------------------------------------------------------
# The computation (a Strat subclass: tables, lopo reads, positions, design, strata reused)
# ---------------------------------------------------------------------------

class R2(rs.Strat):
    """Fits the twin's tables and Gram (the twin's own statements) plus the hidden and smoothed
    blocks; evaluates the twin's arms and the R2 arms on the bigram positions of a split, split
    into the six coverage strata."""

    def __init__(self, data: pr.S3Data, label_of_token: np.ndarray, n_classes: int, hidden: np.ndarray,
                 replay: np.ndarray, strat: dict | None = None, lambdas=LAMBDAS, k_grid=K_GRID, chunk: int = CHUNK):
        super().__init__(data, label_of_token, n_classes, twin=None, lambdas=lambdas, chunk=chunk)
        self.strat = strat
        if strat is not None:
            self.encoding_selected = strat["encoding"]
            for arm in ARMS_TWIN:
                self.lambda_selected[arm] = float(strat["lambda_selected"][arm])
                self.grid_edge[arm] = None
        self.lambda_source = {a: ("strat" if strat is not None else "val") for a in ARMS_TWIN}
        self.lambda_source.update({a: "val" for a in ARMS_RIDGE_R2})
        self.lambda_source["replay_zerofit"] = None
        self.lambda_selected["replay_zerofit"] = None
        self.grid_edge["replay_zerofit"] = None
        if replay.shape != (self.vocab, D) and replay.shape[0] < self.vocab:
            raise SystemExit(f"replay table covers {replay.shape[0]} ids, the harvest needs {self.vocab}")
        if replay.shape[1] != D:
            raise SystemExit(f"replay table width {replay.shape[1]} is not {D}")
        self.replay = replay
        self.hidden = hidden
        self.k_grid = tuple(float(k) for k in k_grid)
        if list(self.k_grid) != sorted(self.k_grid) or len(set(self.k_grid)) != len(self.k_grid):
            raise SystemExit("the k grid must be strictly increasing (ties keep the smaller k)")
        if self.k_grid[0] != 0.0 or not np.isinf(self.k_grid[-1]):
            raise SystemExit("the k grid must run from 0 (the backoff end) to inf (the pure replay)")
        self.k_selected: float | None = None
        self.k_grid_edge: bool | None = None
        self.k_val_table: dict = {}

    # ----- the hidden block ------------------------------------------------------
    def fit_hidden(self, rows, anchors) -> None:
        """Train support, moments and the 1024 leading principal directions, two chunked passes."""
        Dh = int(self.hidden.shape[2])
        n = 0
        s = np.zeros(Dh); mn = np.full(Dh, np.inf); mx = np.full(Dh, -np.inf)
        for st in range(0, rows.shape[0], self.chunk):
            h = self.hidden[rows[st:st + self.chunk], anchors[st:st + self.chunk]].astype(np.float64)
            if not np.all(np.isfinite(h)):
                raise SystemExit("a non-finite hidden value at a train bigram position: the H block cannot be fit")
            n += h.shape[0]; s += h.sum(axis=0)
            mn = np.minimum(mn, h.min(axis=0)); mx = np.maximum(mx, h.max(axis=0))
        if n == 0:
            raise SystemExit("no train bigram positions for the hidden moments")
        mu = s / n
        cov = np.zeros((Dh, Dh))
        for st in range(0, rows.shape[0], self.chunk):
            h = self.hidden[rows[st:st + self.chunk], anchors[st:st + self.chunk]].astype(np.float64) - mu
            cov += h.T @ h
        cov /= n
        var = np.diag(cov).copy()
        sd = np.sqrt(np.maximum(var, 0.0))
        sd = np.where(sd > 0, sd, 1.0)
        covz = cov / np.outer(sd, sd)
        w, V = np.linalg.eigh(covz)
        order = np.argsort(-w, kind="stable")
        w, V = w[order], V[:, order]
        V = V[:, :D].copy()
        for j in range(D):
            i = int(np.argmax(np.abs(V[:, j])))
            if V[i, j] < 0:
                V[:, j] *= -1.0
        wpos = np.maximum(w, 0.0)
        self.h_mu, self.h_sd, self.h_min, self.h_max, self.h_V = mu, sd, mn, mx, V
        self.h_n = int(n)
        self.h_kept_share = float(wpos[:D].sum() / wpos.sum()) if wpos.sum() > 0 else None
        self.h_eigen_top = [float(x) for x in w[:8]]
        self.h_eigen_last = float(w[D - 1])
        self.h_eigen_next = float(w[D]) if w.shape[0] > D else None      # the gap at the cut: a near tie makes H BLAS-dependent

    def h_block(self, rows, anchors) -> np.ndarray:
        h = self.hidden[rows, anchors].astype(np.float64)
        if not np.all(np.isfinite(h)):
            raise SystemExit("a non-finite hidden value at a bigram position: the H arms would be corrupt")
        z = (np.clip(h, self.h_min, self.h_max) - self.h_mu) / self.h_sd
        return z @ self.h_V

    # ----- the smoothed blocks ---------------------------------------------------
    def _lopo_counts(self, table, pair_keys, pair_counts, tok, prompt):
        """(counts (N, L, E) float64, sums (N, L, 1)): the twin's table at tok, every contribution of the
        row's own prompt removed at train rows (the twin's leave-one-prompt-out, counts instead of freqs)."""
        tok = np.asarray(tok, dtype=np.int64)
        c = table[tok].astype(np.float64)
        if prompt is not None:
            pk = np.asarray(prompt, dtype=np.int64) * self.vocab + tok
            idx = np.searchsorted(pair_keys, pk)
            idx_c = np.minimum(idx, pair_keys.shape[0] - 1)
            if not np.all(pair_keys[idx_c] == pk):
                raise SystemExit("internal: a train row's (prompt, key) pair is missing from the pair table")
            c -= pair_counts[idx_c].astype(np.float64)
            if c.min() < 0:
                raise SystemExit("internal: leave-one-prompt-out removed a contribution the table never counted")
        return c, c.sum(axis=2, keepdims=True)

    def smooth_blocks(self, rows, anchors, ks, lopo: bool = False) -> dict:
        """{k: (N, 2048) [SMOOTH_k(tokens[t]) ++ SMOOTH_k(tokens[t-1])]} for the given ks."""
        d = self.d
        prompt = d.prompt_idx[rows] if lopo else None
        tok, tokp = d.tokens[rows, anchors], d.tokens[rows, anchors - 1]
        cc, nc = self._lopo_counts(self.token_table, self.pair_keys, self.pair_counts, tok, prompt)
        cp, np_ = self._lopo_counts(self.prev_table, self.prev_pair_keys, self.prev_pair_counts, tokp, prompt)
        rc = self.replay[tok].reshape(tok.shape[0], L, E)
        rp = self.replay[tokp].reshape(tok.shape[0], L, E)
        out = {}
        for k in ks:
            out[k] = np.hstack([smooth(cc, nc, rc, k).reshape(tok.shape[0], D),
                                smooth(cp, np_, rp, k).reshape(tok.shape[0], D)])
        return out

    # ----- fit -------------------------------------------------------------------
    def fit(self) -> None:
        self.fit_tables()
        d = self.d
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks["train"])
        self.fit_hidden(rows, anchors)
        G = np.zeros((D_X, D_X)); C = np.zeros((D_X, D))
        Ghh = np.zeros((D, D)); Ghs = np.zeros((D, D)); Ghb = np.zeros(D); Ch = np.zeros((D, D))
        Gkk = {k: np.zeros((2 * D, 2 * D)) for k in self.k_grid}
        Gks = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        Gkh = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        Gkb = {k: np.zeros(2 * D) for k in self.k_grid}
        Ck = {k: np.zeros((2 * D, D)) for k in self.k_grid}
        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            X, Y = self.design(r, a, lopo=True)              # the twin's statement, the twin's chunks
            G += X.T @ X
            C += X.T @ Y
            S = X[:, :D]
            Hb = self.h_block(r, a)
            Ghh += Hb.T @ Hb; Ghs += Hb.T @ S; Ghb += Hb.sum(axis=0); Ch += Hb.T @ Y
            for k, Sk in self.smooth_blocks(r, a, self.k_grid, lopo=True).items():
                Gkk[k] += Sk.T @ Sk; Gks[k] += Sk.T @ S; Gkh[k] += Sk.T @ Hb; Gkb[k] += Sk.sum(axis=0); Ck[k] += Sk.T @ Y
        self.G, self.C = G, C                                 # the twin's Gram
        self.Ghh, self.Ghs, self.Ghb, self.Ch = Ghh, Ghs, Ghb, Ch
        self.Gkk, self.Gks, self.Gkh, self.Gkb, self.Ck = Gkk, Gks, Gkh, Gkb, Ck
        self.W = {}
        for arm in ARMS_TWIN:
            F = rb.arm_cols(arm)
            Gs, Cs = G[np.ix_(F, F)], C[F]
            lams = self.lambdas if self.strat is None else (self.lambda_selected[arm],)
            for lam in lams:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)
        # the free arm at every (k, lambda); h_only; the fixed-k arms
        self.Wk = {}
        for k in self.k_grid:
            Gs, Cs = self.arm_gram("free_r2", k)
            for lam in self.lambdas:
                self.Wk[("free_r2", k, lam)] = pr.ridge_solve(Gs, Cs, lam)
        for arm in ("h_only", "replay_cur"):
            Gs, Cs = self.arm_gram(arm, ARM_K.get(arm))
            for lam in self.lambdas:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)
        for arm in ("free_backoff", "free_replay"):
            for lam in self.lambdas:
                self.W[(arm, lam)] = self.Wk[("free_r2", ARM_K[arm], lam)]

    def _pair(self, a: str, b: str, k: float | None) -> np.ndarray:
        """The (size_a, size_b) Gram block of ordered blocks a, b (k the smoothed blocks' k)."""
        if a == "bias" and b != "bias":
            return self._pair(b, a, k).T
        if a == "hist":
            if b == "hist":
                return self.G[:D, :D]
            if b == "cur":
                return self.Gks[k][:D].T
            if b == "prev":
                return self.Gks[k][D:].T
            if b == "h":
                return self.Ghs.T
            return self.G[:D, BIAS_COL][:, None]
        if a == "cur":
            if b == "hist":
                return self.Gks[k][:D]
            if b == "cur":
                return self.Gkk[k][:D, :D]
            if b == "prev":
                return self.Gkk[k][:D, D:]
            if b == "h":
                return self.Gkh[k][:D]
            return self.Gkb[k][:D][:, None]
        if a == "prev":
            if b == "hist":
                return self.Gks[k][D:]
            if b == "cur":
                return self.Gkk[k][D:, :D]
            if b == "prev":
                return self.Gkk[k][D:, D:]
            if b == "h":
                return self.Gkh[k][D:]
            return self.Gkb[k][D:][:, None]
        if a == "h":
            if b == "hist":
                return self.Ghs
            if b == "cur":
                return self.Gkh[k][:D].T
            if b == "prev":
                return self.Gkh[k][D:].T
            if b == "h":
                return self.Ghh
            return self.Ghb[:, None]
        return self.G[BIAS_COL:BIAS_COL + 1, BIAS_COL:BIAS_COL + 1]            # bias, bias

    def _target(self, a: str, k: float | None) -> np.ndarray:
        if a == "hist":
            return self.C[:D]
        if a == "cur":
            return self.Ck[k][:D]
        if a == "prev":
            return self.Ck[k][D:]
        if a == "h":
            return self.Ch
        return self.C[BIAS_COL:BIAS_COL + 1]

    def arm_gram(self, arm: str, k: float | None):
        blocks = ARM_BLOCKS_R2[arm]
        Gs = np.block([[self._pair(a, b, k) for b in blocks] for a in blocks])
        Cs = np.vstack([self._target(a, k) for a in blocks])
        return Gs, Cs

    def fit_k(self, k: float) -> None:
        """The arms that use the selected k, at every lambda."""
        for arm in ("history_tok_r2", "history_bigram_r2", "free_h", "history_all_h"):
            Gs, Cs = self.arm_gram(arm, k)
            for lam in self.lambdas:
                self.W[(arm, lam)] = pr.ridge_solve(Gs, Cs, lam)
        for lam in self.lambdas:
            self.W[("free_r2", lam)] = self.Wk[("free_r2", k, lam)]

    # ----- evaluate --------------------------------------------------------------
    def _blocks(self, r, a, X, ks: tuple) -> dict:
        out = {"hist": X[:, :D], "bias": X[:, BIAS_COL:BIAS_COL + 1], "h": self.h_block(r, a)}
        for k, Sk in self.smooth_blocks(r, a, ks).items():
            out[("cur", k)] = Sk[:, :D]
            out[("prev", k)] = Sk[:, D:]
        return out

    def _arm_design(self, arm: str, blocks: dict, k: float) -> np.ndarray:
        cols = []
        for b in ARM_BLOCKS_R2[arm]:
            cols.append(blocks[(b, k)] if b in ("cur", "prev") else blocks[b])
        return np.hstack(cols)

    def evaluate_free_grid(self, split: str) -> dict:
        """out[(k, lam, B, stratum)] = (hits, needed) for free_r2 at every (k, lambda) of the grids."""
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks[split])
        maxB = max(self.budgets)
        out: dict = {}

        def acc(key, h, n):
            if key in out:
                out[key][0][...] += h; out[key][1][...] += n
            else:
                out[key] = (h.copy(), n.copy())

        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            pp = d.prompt_idx[r]
            Y = self.mh(r, a + HORIZON)
            yy = Y.reshape(r.shape[0], L, E)
            masks = {kk: m for kk, m in self.strata_masks(r, a).items() if m.any()}
            n_full = np.full((r.shape[0], L), K, np.int64)
            bias = np.ones((r.shape[0], 1))
            for k, Sk in self.smooth_blocks(r, a, self.k_grid).items():
                Xa = np.hstack([Sk, bias])
                for lam in self.lambdas:
                    sc = (Xa @ self.Wk[("free_r2", k, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(sc, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        for stratum, m in masks.items():
                            acc((k, lam, B, stratum), pr.per_prompt(h[m], pp[m], pids), pr.per_prompt(n_full[m], pp[m], pids))
        return out

    def select_k(self, grid: dict) -> None:
        """(k, lambda) for free_r2 on the pooled val positions at the label budget: strict >, grid order
        (k outer, lambda inner), so ties keep the smaller k then the smaller lambda; both edges flagged."""
        best, best_k, best_lam, table = -np.inf, None, None, {}
        for k in self.k_grid:
            table[k_tag(k)] = {}
            for lam in self.lambdas:
                h = sum(grid[(k, lam, LABEL_BUDGET, s)][0].sum() for s in STRATA if (k, lam, LABEL_BUDGET, s) in grid)
                n = sum(grid[(k, lam, LABEL_BUDGET, s)][1].sum() for s in STRATA if (k, lam, LABEL_BUDGET, s) in grid)
                v = float(h / n) if n > 0 else float("nan")
                table[k_tag(k)][str(lam)] = v
                if v > best:
                    best, best_k, best_lam = v, k, lam
        self.k_val_table = table
        if best_k is None:
            raise SystemExit("select_k: no (k, lambda) pair has a val hit rate (every cell NaN)")
        self.k_selected = best_k
        self.k_grid_edge = bool(best_k in (self.k_grid[0], self.k_grid[-1]))
        self.lambda_selected["free_r2"] = best_lam
        self.grid_edge["free_r2"] = bool(best_lam in (self.lambdas[0], self.lambdas[-1]))
        self.val_table["free_r2"] = table[k_tag(best_k)]

    def evaluate(self, split: str, encoding: str | None = None, arms=ARMS_REQUIRED, lambdas_of_arm: dict | None = None) -> dict:
        """out[(arm, B, lam, stratum)] = (hits (P, L), needed (P, L)) over the bigram positions of the
        split in that stratum; every lambda unless lambdas_of_arm. The twin's arms are read exactly as
        the stratified tool reads them (the same column slices of the same design)."""
        d = self.d
        pids = self.prompt_ids[split]
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks[split])
        self.n_positions[f"bigram/{split}"] = int(rows.shape[0])
        maxB = max(self.budgets)
        need_r2 = any(a_ in ARMS_R2 for a_ in arms)
        ks_set = set()
        for a_ in arms:
            if a_ in ARMS_RIDGE_R2:
                kk = ARM_K.get(a_, self.k_selected)
                if kk is None:
                    raise SystemExit("evaluate: the selected k is not set (select_k first)")
                ks_set.add(kk)
        ks = tuple(sorted(ks_set, key=lambda x: (bool(np.isinf(x)), x)))
        out: dict = {}

        def acc(key, h, n):
            if key in out:
                out[key][0][...] += h; out[key][1][...] += n
            else:
                out[key] = (h.copy(), n.copy())

        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            pp = d.prompt_idx[r]
            X, Y = self.design(r, a)
            yy = Y.reshape(r.shape[0], L, E)
            masks = {kk: m for kk, m in self.strata_masks(r, a).items() if m.any()}
            n_full = np.full((r.shape[0], L), K, np.int64)
            blocks = self._blocks(r, a, X, ks) if need_r2 else None
            for arm in arms:
                if arm == "replay_zerofit":
                    sc = self.replay[d.tokens[r, a]].reshape(r.shape[0], L, E)
                    lams = (None,)
                elif arm in ARMS_TWIN:
                    sc = None
                    lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                    Xa = X[:, rb.arm_cols(arm)]
                else:
                    sc = None
                    lams = self.lambdas if lambdas_of_arm is None else (lambdas_of_arm[arm],)
                    Xa = self._arm_design(arm, blocks, ARM_K.get(arm, self.k_selected))
                for lam in lams:
                    scores = sc if sc is not None else (Xa @ self.W[(arm, lam)]).reshape(r.shape[0], L, E)
                    order = pr.topb_order(scores, maxB)
                    for B in self.budgets:
                        h = np.take_along_axis(yy, order[:, :, :B], axis=2).sum(axis=2)
                        for stratum, m in masks.items():
                            acc((arm, B, lam, stratum), pr.per_prompt(h[m], pp[m], pids), pr.per_prompt(n_full[m], pp[m], pids))
        return out

    def replay_agreement(self, split: str) -> dict:
        """Per gate: the mean overlap over 8 of the top-8 of REPLAY(tokens[t-1]) with S[t], and of
        REPLAY(tokens[t]) with S[t+1], over the split's bigram positions (no fit, no readout target)."""
        d = self.d
        rows, anchors = pr.restrict(*rb.bigram_positions(d.lengths, d.T), self.masks[split])
        hp = np.zeros(L); hc = np.zeros(L); n = 0
        for s in range(0, rows.shape[0], self.chunk):
            r, a = rows[s:s + self.chunk], anchors[s:s + self.chunk]
            rp = self.replay[d.tokens[r, a - 1]].reshape(r.shape[0], L, E)
            rc = self.replay[d.tokens[r, a]].reshape(r.shape[0], L, E)
            st = self.mh(r, a).reshape(r.shape[0], L, E)
            st1 = self.mh(r, a + HORIZON).reshape(r.shape[0], L, E)
            hp += np.take_along_axis(st, pr.topb_order(rp, K), axis=2).sum(axis=(0, 2))
            hc += np.take_along_axis(st1, pr.topb_order(rc, K), axis=2).sum(axis=(0, 2))
            n += r.shape[0]
        if n == 0:
            return {"n": 0}
        return {"n": int(n), "prev_vs_S_t": {"per_gate": [float(x) for x in hp / (n * K)], "pooled": float(hp.sum() / (n * K * L))},
                "cur_vs_S_t1": {"per_gate": [float(x) for x in hc / (n * K)], "pooled": float(hc.sum() / (n * K * L))}}


# ---------------------------------------------------------------------------
# Conclusion (mechanical; --conclude-from recomputes it from the state file)
# ---------------------------------------------------------------------------

def _index_strat(rows: list[dict]) -> dict:
    return {(r["arm"], int(r["budget"]), int(r["gate"]), int(r["prompt_idx"]), r["stratum"]): (int(r["hits"]), int(r["needed"]))
            for r in rows if r["arm"] in ARMS_TWIN}


def reproduce_check(rows: list[dict], strat_rows: list[dict]) -> dict:
    """The REPRODUCE precondition: this read's rows for the twin's nine arms against the committed
    stratified rows for the same arms, per stratum, hits AND needed, to the integer."""
    mine, theirs = _index_strat(rows), _index_strat(strat_rows)
    missing = sorted(k for k in theirs if k not in mine)
    extra = sorted(k for k in mine if k not in theirs)
    needed_mm, hits_mm, max_gap = 0, 0, 0
    for k, (h, n) in theirs.items():
        if k not in mine:
            continue
        hm, nm = mine[k]
        if nm != n:
            needed_mm += 1
        elif hm != h:
            hits_mm += 1
            max_gap = max(max_gap, abs(hm - h))
    n_rows = len(theirs)
    exact = not missing and not extra and needed_mm == 0 and hits_mm == 0
    near = (not exact and not missing and not extra and needed_mm == 0
            and hits_mm <= int(REPRODUCE_NEAR_SHARE * n_rows) and max_gap <= REPRODUCE_NEAR_HITS)
    status = "EXACT" if exact else "NEAR" if near else "INVALID"
    return {"n_strat_rows": n_rows, "n_compared": n_rows - len(missing), "missing_in_r2": len(missing),
            "extra_in_r2": len(extra), "needed_mismatch_rows": needed_mm, "hits_mismatch_rows": hits_mm,
            "max_abs_hits_gap": int(max_gap), "near_share_cap": REPRODUCE_NEAR_SHARE, "near_hits_cap": REPRODUCE_NEAR_HITS,
            "status": status, "ok": bool(status != "INVALID")}


_AT = f"at this reader (B = {LABEL_BUDGET}, j = {HORIZON})"
_NM = f"no material margin (at or above +{MATERIAL})"
_FB = "the unseen-key positions"
_ENC = ("a free encoding that is never at the marginal (the model's own routers replayed on the token "
        "embedding as the prior of the smoothed count tables)")
_H = "the forward's final-norm state at the address block's width in the free arm"
SENTENCES_Q1 = {
    ("R2-FALLBACK-SURVIVES", False): (f"against {_ENC}, the address block still adds a material margin over the equal-dims "
                                      f"free block on {_FB}: the located margin is not shown to be table sparsity at this "
                                      f"encoding and the coverage caveat stands as a scoped limitation, not a retraction, {_AT}"),
    ("R2-FALLBACK-SURVIVES", True): (f"the address block's equal-dims margin over the generalising free block on {_FB} reads "
                                     f"SIGNAL by the rule with a CI95 that straddles the +{MATERIAL} floor: not settled at "
                                     f"this power, {_AT}"),
    ("R2-POOLED-ONLY", False): (f"{_NM} of the address block over the equal-dims generalising free block is shown on {_FB} "
                                f"while the pooled margin is material: the margin the stratified read located on the unseen "
                                f"keys is not shown to survive this encoding, {{COVERED}}, {_AT}"),
    ("R2-POOLED-ONLY", True): (f"{_NM} of the address block over the equal-dims generalising free block is shown on {_FB} by "
                               f"the rule, with a CI95 that straddles the +{MATERIAL} floor, while the pooled margin is "
                               f"material: not settled at this power, {_AT}"),
    ("R2-ABSORBED", False): (f"{_NM} of the address block over the equal-dims generalising free block is shown on {_FB} nor "
                             f"pooled: the margin the stratified read located was not shown to survive {_ENC}{{TAIL}}, {_AT}"),
    ("R2-ABSORBED", True): (f"neither Q1 reading is SIGNAL by the rule while the unseen-key CI95 straddles the +{MATERIAL} "
                            f"floor: not settled at this power, {_AT}"),
}
_STR = f"at least one CI95 straddles the +{MATERIAL} floor"
SENTENCES_Q2 = {
    ("H-SURVIVES", False): (f"with {_H}, the address block adds a material margin over the equal-dims free block and the "
                            f"address stream adds a material margin over the free bigram plus the hidden block: the "
                            f"address margin survives the strongest free arm this registration builds (the p_t summaries "
                            f"and the full h_a not included), with H at 1024 of 2048 dimensions, {_AT}"),
    ("H-SURVIVES", True): (f"with {_H}, both Q2 readings are SIGNAL by the rule while {_STR}: not settled at this power, "
                           f"{_AT}"),
    ("H-COMPLEMENTARY", False): (f"with {_H}, {_NM} of the address block over the equal-dims free block is shown, while the "
                                 f"address stream adds a material margin over the free bigram plus the hidden block, {_AT}"),
    ("H-COMPLEMENTARY", True): (f"with {_H}, the union reading is SIGNAL and the equal-dims reading is not, by the rule, "
                                f"while {_STR}: not settled at this power, {_AT}"),
    ("H-ABSORBS", False): (f"with {_H}, {_NM} of the address block over the equal-dims free block is shown and none of the "
                           f"address stream over the free bigram plus the hidden block: at this reader the forward's own "
                           f"final-norm state plus two tokens' smoothed routing profiles show no material address margin "
                           f"(NON-CRITERION; K-2 is untouched), {_AT}"),
    ("H-ABSORBS", True): (f"with {_H}, neither Q2 reading is SIGNAL by the rule while {_STR}: not settled at this power, "
                          f"{_AT}"),
    ("H-INCONSISTENT", False): (f"with {_H}, the equal-dims comparison reads a material margin while the union reader does "
                                f"not; no sentence on the margin is written, {_AT}"),
    ("H-INCONSISTENT", True): (f"with {_H}, the equal-dims comparison reads a material margin while the union reader does "
                               f"not, and {_STR}; no sentence on the margin is written, {_AT}"),
}
_ALL_STRADDLE = f"; the pooled Q1 reading's CI95 straddles the +{MATERIAL} floor"
_ALL_NEGATIVE = "; the pooled Q1 reading is NEGATIVE"
_NEG_FB = f"the address block reads below the equal-dims generalising free block on {_FB} (NEGATIVE); "
_NEG_H_EQ = "the address block reads below the equal-dims free block with the hidden block (NEGATIVE); "
_NEG_H_ADD = "the address stream reads below the free bigram plus the hidden block (NEGATIVE); "
# the ABSORBED sentence's tail: the sparsity clause, replaced where k sits at the pure-replay end (the encoding replaced
# the tables for every key) and extended where the shared k handicaps the address partner (critic design round, B3)
_TAIL_SPARSITY = (", consistent with table sparsity, and the coverage caveat is resolved in the free baseline's favour at "
                  "this encoding")
_TAIL_NO_GAIN = ("; the encoding did not recover a material share of the unseen-key deficit (SHRINKAGE on fallback not "
                 "SIGNAL), so the absorption is not attributed to table sparsity")
_TAIL_REPLAY_END = ("; with k at the pure-replay end of the grid the encoding replaced the tables for every key, seen or "
                    "not, so the absorption is not attributable to the sparse keys and the coverage caveat is neither "
                    "resolved nor retired by it")
_TAIL_HANDICAP = ("; the shared k handicaps the address partner (history_tok_r2 reads below history_tok, NEGATIVE, on "
                  "{SCOPE}), so part of the absorption is that handicap, and the twin's own address arm against the "
                  "generalising free block (history_tok - free_r2, reported per scope) is read beside it")
_COVERED_SIGNAL = "and what survives sits on the covered positions"
_COVERED_NOT = "while the unseen-key reading is not SIGNAL at this power"
# the Q2 reader guard: adding H degraded a reader (critic design round, B1); the label stays, the claim does not
_READER_GUARD = (f"with {_H}, {{WHICH}} {{VERB}} NEGATIVE: the hidden block degrades a reader at this train size; the Q2 "
                 f"label is mechanical and is quoted, but no Q2 branch claim is written and nothing is struck, {_AT}")
SENTENCE_VOID = {
    "REPRODUCE-INVALID": ("this read's rows do not reproduce the committed stratified read's rows for the twin's arms (or "
                          "the twin's D_eq is not the stratified payload's); the run is void and its deltas are numbers, "
                          "not readings"),
    "INCOMPLETE": None,
}
DELTA_PAIRS = (("address_beyond_token", "history_tok", "free_tok"),
               ("gate_eq", "history_tok", "FREE"),
               ("address_beyond_bigram", "HIST", "FREE"),
               ("bigram_gain", "FREE", "free_tok"),
               ("shrinkage", "free_r2", "FREE"),
               ("gate_eq_r2", "history_tok_r2", "free_r2"),
               ("gate_eq_r2_twinarm", "history_tok", "free_r2"),
               ("d_add_r2", "history_bigram_r2", "free_r2"),
               ("backoff-free_bigram", "free_backoff", "FREE"),
               ("replay-free_bigram", "free_replay", "FREE"),
               ("free_r2-free_backoff", "free_r2", "free_backoff"),
               ("free_r2-free_replay", "free_r2", "free_replay"),
               ("replay_cur-free_tok", "replay_cur", "free_tok"),
               ("replay_zerofit-free_tok", "replay_zerofit", "free_tok"),
               ("history_tok_r2-history_tok", "history_tok_r2", "history_tok"),
               ("h_only-free_tok", "h_only", "free_tok"),
               ("h_only-history_tok", "h_only", "history_tok"),
               ("free_h-free_r2", "free_h", "free_r2"),
               ("d_eq_h", "history_bigram_r2", "free_h"),
               ("d_add_h", "history_all_h", "free_h"),
               ("history_all_h-history_bigram_r2", "history_all_h", "history_bigram_r2"))
LABEL_CELLS = (f"gate_eq_r2|B={LABEL_BUDGET}|fallback", f"gate_eq_r2|B={LABEL_BUDGET}|all",
               f"d_eq_h|B={LABEL_BUDGET}|all", f"d_add_h|B={LABEL_BUDGET}|all")
HEADLINE_CELLS = (f"shrinkage|B={LABEL_BUDGET}|fallback", f"shrinkage|B={LABEL_BUDGET}|covered",
                  f"shrinkage|B={LABEL_BUDGET}|all", f"gate_eq|B={LABEL_BUDGET}|fallback")
READING_FIELDS = ("gate_eq_r2_fallback_reading", "gate_eq_r2_all_reading", "d_eq_h_all_reading", "d_add_h_all_reading",
                  "shrinkage_readings", "gate_eq_r2_readings", "d_eq_h_readings", "fallback_negative", "h_negative",
                  "h_inconsistent_cause", "gate_eq_r2_covered_reading", "free_h_gain_reading", "h_anchor_reading",
                  "address_handicap_reading", "address_handicap_fallback_reading", "d_add_h_fallback_reading",
                  "address_handicap_scopes", "q2_reader_guard", "address_handicap", "all_negative", "said_in_words")


def _straddle(dl: dict) -> bool:
    return bool(dl["lo"] <= MATERIAL <= dl["hi"])


def conclude(rows: list[dict], encoding: str, k_selected: float, strat_rows: list[dict] | None,
             strat_cells: dict | None = None, n_boot: int = N_BOOT, seed: int = BOOT_SEED, budgets=BUDGETS) -> dict:
    if encoding not in rb.ENCODINGS:
        raise SystemExit(f"unknown encoding {encoding!r}")
    rows = rs.sort_rows(rows)
    prompts = sorted({int(r["prompt_idx"]) for r in rows})
    groups = rs._group(rows)
    free, hist = rb.free_arm_of(encoding), rb.history_arm_of(encoding)
    names = {"FREE": free, "HIST": hist}
    tables: dict = {}
    for (arm, B, scope), gates in groups.items():
        entry = {"arm": arm, "budget": B, "scope": scope,
                 "dims": arm_dims(arm, encoding) if arm in ARMS_REQUIRED else None, "per_gate": {}}
        for g in sorted(gates):
            h, n = pr._arrays(gates[g], prompts)
            entry["per_gate"][str(g)] = pr._point_ci(h, n, n_boot, seed)
        H, N = pr._pooled(gates, prompts)
        entry["all"] = pr._point_ci(H, N, n_boot, seed)
        tables[f"{arm}|B={B}|{scope}"] = entry

    def pooled_of(arm, B, scope):
        gates = groups.get((names.get(arm, arm), B, scope))
        return None if gates is None else pr._pooled(gates, prompts)

    for B in budgets:
        for scope in SCOPES:
            ref = pooled_of("history_tok", B, scope)
            if ref is None:
                continue
            for arm in ARMS_REQUIRED:
                pa = pooled_of(arm, B, scope)
                if pa is not None and not np.array_equal(pa[1], ref[1]):
                    raise SystemExit(f"pairing violated: {arm} and history_tok have different per-prompt trials at B={B} in {scope}")

    def delta_of(a, b, B, scope):
        pa, pb = pooled_of(a, B, scope), pooled_of(b, B, scope)
        if pa is None or pb is None:
            return None
        if not np.array_equal(pa[1], pb[1]):
            raise SystemExit(f"pairing violated: {a} and {b} have different per-prompt trials at B={B} in {scope}")
        return pr._delta(pa[0], pb[0], pa[1], n_boot, seed)

    deltas: dict = {}
    for B in budgets:
        for scope in SCOPES:
            for name, a, b in DELTA_PAIRS:
                dl = delta_of(a, b, B, scope)
                if dl is not None:
                    deltas[f"{name}|B={B}|{scope}"] = dl

    scopes: dict = {}
    ref_all = pooled_of("history_tok", LABEL_BUDGET, "all")
    for scope in SCOPES:
        pa = pooled_of("history_tok", LABEL_BUDGET, scope)
        if pa is None:
            scopes[scope] = {"positions": 0, "share": 0.0, "prompts_with_positions": 0}
            continue
        scopes[scope] = {"positions": int(round(float(pa[1].sum()) / (L * K))),
                         "share": float(pa[1].sum() / ref_all[1].sum()) if ref_all is not None and ref_all[1].sum() > 0 else None,
                         "prompts_with_positions": int((pa[1] > 0).sum())}

    present = {r["arm"] for r in rows}
    missing = [a for a in ARMS_REQUIRED if a not in present]
    missing_cells = [c for c in LABEL_CELLS + HEADLINE_CELLS if c not in deltas]
    labels: dict = {"encoding": encoding, "free_bigram_arm": free, "history_bigram_arm": hist, "k_selected": k_tag(k_selected),
                    "missing_arms": missing, "missing_label_cells": missing_cells, "scopes": scopes}
    rep = None if strat_rows is None else reproduce_check(rows, strat_rows)
    labels["reproduce"] = rep
    # the identity check: the twin's D_eq on the three scopes repeats the stratified payload's cells
    if strat_cells is not None:
        ok = True
        for scope in IDENTITY_SCOPES:
            mine, theirs = deltas.get(f"gate_eq|B={LABEL_BUDGET}|{scope}"), strat_cells.get(scope)
            if mine is None or theirs is None:
                ok = False
                continue
            ok = ok and all(abs(float(mine[kk]) - float(theirs[kk])) <= IDENTITY_TOL for kk in ("delta", "lo", "hi"))
        labels["gate_eq_matches_strat"] = bool(ok)
    else:
        labels["gate_eq_matches_strat"] = None
    if rep is None:
        labels["reproduce_status"], labels["reproduce_ok"] = None, None
    else:
        status = rep["status"]
        if status != "INVALID" and labels["gate_eq_matches_strat"] is False:
            status = "INVALID"
        labels["reproduce_status"], labels["reproduce_ok"] = status, bool(status != "INVALID")
    if missing or missing_cells:
        labels.update({"label": "INCOMPLETE", "void": True, "q1": None, "q2": None, "sentence": None})
        return {"tables": tables, "deltas": deltas, "labels": labels}
    fb, al, eqh, addh = (deltas[c] for c in LABEL_CELLS)
    shr_fb, shr_cov, shr_all, twin_fb = (deltas[c] for c in HEADLINE_CELLS)
    anchor = deltas.get(f"history_all_h-history_bigram_r2|B={LABEL_BUDGET}|all")
    labels.update({"gate_eq_r2_fallback": fb, "gate_eq_r2_all": al, "d_eq_h_all": eqh, "d_add_h_all": addh,
                   "shrinkage_fallback": shr_fb, "shrinkage_covered": shr_cov, "shrinkage_all": shr_all,
                   "twin_gate_eq_fallback": twin_fb, "h_dilution_anchor": anchor,
                   "shrinkage_share_of_fallback_margin": (float(shr_fb["delta"] / twin_fb["delta"]) if twin_fb["delta"] != 0 else None)})
    labels["gate_eq_r2_fallback_reading"] = pr._reading(fb)
    labels["gate_eq_r2_all_reading"] = pr._reading(al)
    labels["d_eq_h_all_reading"] = pr._reading(eqh)
    labels["d_add_h_all_reading"] = pr._reading(addh)
    for name, field in (("shrinkage", "shrinkage_readings"), ("gate_eq_r2", "gate_eq_r2_readings"), ("d_eq_h", "d_eq_h_readings")):
        labels[field] = {s: pr._reading(deltas[f"{name}|B={LABEL_BUDGET}|{s}"])
                         for s in SCOPES if f"{name}|B={LABEL_BUDGET}|{s}" in deltas}
    labels["fallback_floor_straddle"] = _straddle(fb)
    labels["all_floor_straddle"] = _straddle(al)
    labels["d_eq_h_floor_straddle"] = _straddle(eqh)
    labels["d_add_h_floor_straddle"] = _straddle(addh)
    labels["q2_floor_straddle"] = bool(labels["d_eq_h_floor_straddle"] or labels["d_add_h_floor_straddle"])
    labels["shrinkage_floor_straddle"] = {s: _straddle(deltas[f"shrinkage|B={LABEL_BUDGET}|{s}"])
                                          for s in ("fallback", "covered", "all") if f"shrinkage|B={LABEL_BUDGET}|{s}" in deltas}
    labels["fallback_negative"] = bool(labels["gate_eq_r2_fallback_reading"] == "NEGATIVE")
    labels["all_negative"] = bool(labels["gate_eq_r2_all_reading"] == "NEGATIVE")
    labels["h_negative"] = bool(labels["d_eq_h_all_reading"] == "NEGATIVE" or labels["d_add_h_all_reading"] == "NEGATIVE")
    # the co-readings the sentences and the said-in-words list depend on (critic design round, B1 / B3 / B5 / A8)
    cov_r2 = deltas.get(f"gate_eq_r2|B={LABEL_BUDGET}|covered")
    hgain = deltas.get(f"free_h-free_r2|B={LABEL_BUDGET}|all")
    handicap = deltas.get(f"history_tok_r2-history_tok|B={LABEL_BUDGET}|all")
    handicap_fb = deltas.get(f"history_tok_r2-history_tok|B={LABEL_BUDGET}|fallback")
    dadd_r2 = deltas.get(f"d_add_r2|B={LABEL_BUDGET}|all")
    dadd_r2_fb = deltas.get(f"d_add_r2|B={LABEL_BUDGET}|fallback")
    dadd_h_fb = deltas.get(f"d_add_h|B={LABEL_BUDGET}|fallback")
    labels.update({"gate_eq_r2_covered": cov_r2, "free_h_gain_all": hgain, "address_handicap_all": handicap,
                   "address_handicap_fallback": handicap_fb, "d_add_r2_all": dadd_r2, "d_add_r2_fallback": dadd_r2_fb,
                   "d_add_h_fallback": dadd_h_fb,
                   "gate_eq_r2_twinarm_all": deltas.get(f"gate_eq_r2_twinarm|B={LABEL_BUDGET}|all"),
                   "gate_eq_r2_twinarm_fallback": deltas.get(f"gate_eq_r2_twinarm|B={LABEL_BUDGET}|fallback")})
    labels["gate_eq_r2_covered_reading"] = None if cov_r2 is None else pr._reading(cov_r2)
    labels["free_h_gain_reading"] = None if hgain is None else pr._reading(hgain)
    labels["h_anchor_reading"] = None if anchor is None else pr._reading(anchor)
    labels["address_handicap_reading"] = None if handicap is None else pr._reading(handicap)
    labels["address_handicap_fallback_reading"] = None if handicap_fb is None else pr._reading(handicap_fb)
    labels["d_add_h_fallback_reading"] = None if dadd_h_fb is None else pr._reading(dadd_h_fb)
    labels["d_add_r2_floor_straddle"] = None if dadd_r2 is None else _straddle(dadd_r2)
    labels["d_add_r2_fallback_floor_straddle"] = None if dadd_r2_fb is None else _straddle(dadd_r2_fb)
    labels["k_at_replay_end"] = bool(np.isinf(k_selected))
    # the handicap is keyed on ALL or on FALLBACK (the gate's scope); the sentence names the scope(s)
    hand_scopes = [s for s, dl in (("all", handicap), ("fallback", handicap_fb)) if dl is not None and dl["hi"] < 0]
    labels["address_handicap"] = bool(hand_scopes)
    labels["address_handicap_scopes"] = hand_scopes
    labels["q2_reader_guard"] = bool((hgain is not None and hgain["hi"] < 0) or (anchor is not None and anchor["hi"] < 0))
    # said in words, mechanised: the B = 8 / 32 readings that disagree with B = 16's on the four label cells; a limit arm
    # above free_r2 on test; h_only above history_tok; replay_zerofit's point (compared at landing with stage 1's RECENCY_16)
    said: dict = {"b8_b32_disagree": [], "limit_arm_above_free_r2": [], "h_only_above_history_tok": None, "replay_zerofit_all_point": None}
    for cell in LABEL_CELLS:
        name, _, scope = cell.split("|")
        for B in budgets:
            if B == LABEL_BUDGET:
                continue
            other = deltas.get(f"{name}|B={B}|{scope}")
            if other is not None and pr._reading(other) != pr._reading(deltas[cell]):
                said["b8_b32_disagree"].append(f"{name}|B={B}|{scope}: {pr._reading(other)}")
    pt = lambda arm: tables.get(f"{arm}|B={LABEL_BUDGET}|all", {}).get("all", {}).get("point")  # noqa: E731
    for arm in ("free_backoff", "free_replay"):
        if pt(arm) is not None and pt("free_r2") is not None and pt(arm) > pt("free_r2"):
            said["limit_arm_above_free_r2"].append(arm)
    if pt("h_only") is not None and pt("history_tok") is not None:
        said["h_only_above_history_tok"] = bool(pt("h_only") > pt("history_tok"))
    said["replay_zerofit_all_point"] = pt("replay_zerofit")
    labels["said_in_words"] = said
    f_sig, a_sig = labels["gate_eq_r2_fallback_reading"] == "SIGNAL", labels["gate_eq_r2_all_reading"] == "SIGNAL"
    q1 = "R2-FALLBACK-SURVIVES" if f_sig else "R2-POOLED-ONLY" if a_sig else "R2-ABSORBED"
    e_sig, u_sig = labels["d_eq_h_all_reading"] == "SIGNAL", labels["d_add_h_all_reading"] == "SIGNAL"
    q2 = ("H-SURVIVES" if (e_sig and u_sig) else "H-COMPLEMENTARY" if (not e_sig and u_sig)
          else "H-ABSORBS" if (not e_sig and not u_sig) else "H-INCONSISTENT")
    labels["h_inconsistent_cause"] = (None if q2 != "H-INCONSISTENT"
                                      else "reader" if (anchor is not None and anchor["hi"] < 0)
                                      else "floor straddle" if labels["q2_floor_straddle"] else "neither")
    labels["q1"], labels["q2"] = q1, q2
    if labels["reproduce_ok"] is False:
        labels["label"] = "REPRODUCE-INVALID"
        labels["void"] = True
        labels["sentence"] = SENTENCE_VOID["REPRODUCE-INVALID"]
        labels["q1"], labels["q2"] = None, None
        for f in READING_FIELDS:
            labels[f] = None
    else:
        labels["label"] = f"{q1} / {q2}"
        labels["void"] = False
        s1 = SENTENCES_Q1[(q1, labels["fallback_floor_straddle"])]
        if (q1, labels["fallback_floor_straddle"]) == ("R2-ABSORBED", False):
            # the sparsity clause needs a material SHRINKAGE on the unseen keys (code review, W1); the pure-replay end
            # replaces it; a handicap on ALL or FALLBACK extends it
            if labels["k_at_replay_end"]:
                tail = _TAIL_REPLAY_END
            elif labels["shrinkage_readings"].get("fallback") == "SIGNAL":
                tail = _TAIL_SPARSITY
            else:
                tail = _TAIL_NO_GAIN
            if labels["address_handicap"]:
                tail = tail + _TAIL_HANDICAP.replace("{SCOPE}", " and ".join(hand_scopes))
            s1 = s1.replace("{TAIL}", tail)
        if (q1, labels["fallback_floor_straddle"]) == ("R2-POOLED-ONLY", False):
            s1 = s1.replace("{COVERED}", _COVERED_SIGNAL if labels["gate_eq_r2_covered_reading"] == "SIGNAL" else _COVERED_NOT)
        if labels["fallback_negative"]:
            s1 = _NEG_FB + s1
        if labels["all_floor_straddle"]:
            s1 = s1 + _ALL_STRADDLE
        if labels["all_negative"]:
            s1 = s1 + _ALL_NEGATIVE
        if labels["q2_reader_guard"]:
            parts = [w for w, flag in (("free_h - free_r2", hgain is not None and hgain["hi"] < 0),
                                       ("the dilution anchor history_all_h - history_bigram_r2", anchor is not None and anchor["hi"] < 0)) if flag]
            s2 = _READER_GUARD.replace("{WHICH}", " and ".join(parts)).replace("{VERB}", "read" if len(parts) > 1 else "reads")
        else:
            s2 = SENTENCES_Q2[(q2, labels["q2_floor_straddle"])]
        # a NEGATIVE Q2 reading keeps its prefix under the guard too, each reading with its own words (code review, B1)
        if labels["d_add_h_all_reading"] == "NEGATIVE":
            s2 = _NEG_H_ADD + s2
        if labels["d_eq_h_all_reading"] == "NEGATIVE":
            s2 = _NEG_H_EQ + s2
        labels["sentence"] = s1 + "; " + s2
    labels["rule"] = (f"readings SIGNAL iff CI95 lower > 0 and delta >= +{MATERIAL}, NEGATIVE iff CI95 upper < 0, else "
                      f"NOT-SHOWN, at B={LABEL_BUDGET}, j={HORIZON}, on the twin's bigram positions split by train-table "
                      f"coverage (six strata; covered / fallback / all); PRECONDITION REPRODUCE: this read's rows for the "
                      f"twin's nine arms equal the committed stratified read's rows per stratum (hits-only mismatches on at "
                      f"most {REPRODUCE_NEAR_SHARE:.1%} of them within +-{REPRODUCE_NEAR_HITS} hit are NEAR; more, any needed "
                      f"mismatch, or a twin D_eq on all / covered / fallback that is not the stratified payload's is INVALID = "
                      f"void, numbers only); the free arm's k and lambda selected jointly on val (strict >, smaller k then "
                      f"smaller lambda on ties); Q1 R2-FALLBACK-SURVIVES iff history_tok_r2 - free_r2 on fallback SIGNAL, "
                      f"R2-POOLED-ONLY iff not and on all SIGNAL, else R2-ABSORBED; Q2 on all positions: H-SURVIVES iff "
                      f"history_bigram_r2 - free_h and history_all_h - free_h both SIGNAL, H-COMPLEMENTARY iff only the "
                      f"union, H-ABSORBS iff neither, H-INCONSISTENT iff only the equal-dims; a CI95 containing +{MATERIAL} "
                      f"is a floor straddle, flagged, and on the fallback gate or either Q2 reading the pinned sentence then "
                      f"claims nothing beyond the rule; READER GUARD: where free_h - free_r2 or history_all_h - "
                      f"history_bigram_r2 on all reads NEGATIVE the Q2 label stays but its branch sentence is replaced and "
                      f"nothing is struck; a NEGATIVE D_eq^H and a NEGATIVE D_add^H each carry their own prefix; the "
                      f"ABSORBED sentence's sparsity clause needs shrinkage on fallback SIGNAL (else a no-gain clause), is "
                      f"replaced where k is the pure-replay end, and is extended where history_tok_r2 - history_tok on all "
                      f"or on fallback reads NEGATIVE; the primary harvest's label is the label; NON-CRITERION, one pinned "
                      f"consequence (a dated STATUS line under F-26)")
    return {"tables": tables, "deltas": deltas, "labels": labels}


# ---------------------------------------------------------------------------
# Provenance, I/O, CLI
# ---------------------------------------------------------------------------

def read_strat(path: Path) -> dict:
    """The committed stratified payload and its state file: the twin's encoding and lambdas it carries
    (taken verbatim), its three D_eq cells (the identity check) and the rows REPRODUCE is checked against."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("registered") != rs.REGISTERED:
        raise SystemExit(f"{path} is not a stratified coverage read payload")
    prov = payload["provenance"]
    if prov.get("instrument_sha256") != STRAT_INSTRUMENT_SHA256:
        raise SystemExit(f"{path} was not written by the frozen stratified tool ({str(prov.get('instrument_sha256'))[:12]})")
    if prov.get("twin") is None or prov.get("encoding_source") != "twin":
        raise SystemExit(f"{path} did not take its encoding and lambdas from a committed twin payload")
    state_path = Path(str(path) + ".state.jsonl")
    if not state_path.exists():
        raise SystemExit(f"stratified state file {state_path} not found")
    header, rows = pr.load_state(state_path)
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit(f"{state_path}: row count differs from the stratified payload's")
    cells = {scope: payload["conclusion"]["deltas"][f"gate_eq|B={LABEL_BUDGET}|{scope}"] for scope in IDENTITY_SCOPES}
    return {"path": rs._rel(path), "sha256": pr._sha(path), "state_path": rs._rel(state_path), "state_sha256": pr._sha(state_path),
            "git_commit": prov["git_commit"], "instrument_sha256": prov["instrument_sha256"],
            "encoding": prov["encoding_selected"],
            "lambda_selected": {k: float(prov["lambda_selected"][k]) for k in ARMS_TWIN},
            "twin_path": prov["twin"]["path"], "twin_sha256": prov["twin"]["sha256"],
            "n_state_rows": int(payload["n_state_rows"]), "harvest_npz_sha256": prov["harvest_npz_sha256"],
            "gate_eq": cells, "_rows": rows}


def strat_reference(harvest_dir: Path, strat_arg: str | None, smoke: bool, out_under_results: bool) -> dict | None:
    if smoke:
        return None
    if strat_arg is not None and strat_arg.lower() == "none":
        if out_under_results:
            raise SystemExit("a registered run must read the committed stratified payload (--strat none is refused under results/)")
        return None
    explicit = strat_arg is not None
    want = STRAT_OF_HARVEST.get(Path(harvest_dir).name)
    if not explicit:
        if want is None:
            if not out_under_results:
                return None
            raise SystemExit(f"no committed stratified payload is known for harvest {Path(harvest_dir).name}; pass --strat")
        path = ROOT / "results" / "real" / want
    else:
        path = Path(strat_arg)
        if out_under_results and path.resolve() != (ROOT / "results" / "real" / (want or "")).resolve():
            raise SystemExit("under results/ the stratified payload must be the registered one for this harvest")
    if not path.exists():
        if not explicit and not out_under_results:
            return None
        raise SystemExit(f"stratified payload {path} not found")
    return read_strat(path)


def _strat_header(strat: dict | None) -> dict | None:
    return None if strat is None else {k: v for k, v in strat.items() if k != "_rows"}


def _source_record(src: dict) -> dict:
    return {k: v for k, v in src.items() if k not in ("embed", "gates", "norms")}


def _select_lambda(table: dict, lambdas) -> float:
    best_lam, best = None, -np.inf
    for lam in lambdas:
        v = table[str(float(lam))]
        if v > best:
            best, best_lam = v, float(lam)
    return best_lam


def _select_k_from_table(table: dict, k_grid, lambdas):
    best, best_k, best_lam = -np.inf, None, None
    for k in k_grid:
        for lam in lambdas:
            v = table[k_tag(k)][str(float(lam))]
            if v > best:
                best, best_k, best_lam = v, k, float(lam)
    return best_k, best_lam


def run(args) -> dict:
    started = time.time()
    strat_sha = assert_frozen_strat()
    twin_sha = rs.assert_frozen_twin()
    parent_sha = rb.assert_frozen_instrument()
    only = [int(s) for s in args.only_seeds.split(",")] if args.only_seeds else None
    smoke = bool(args.smoke_split_val or only is not None)
    out = Path(args.out)
    under = pr._under_results(out)
    if smoke and under:
        raise SystemExit("a smoke (--only-seeds / --smoke-split-val) may not write under results/")
    lambdas = tuple(float(x) for x in args.lambdas.split(",")) if getattr(args, "lambdas", None) else LAMBDAS
    k_grid = tuple(k_of_tag(x) for x in args.k_grid.split(",")) if getattr(args, "k_grid", None) else K_GRID
    if (lambdas != LAMBDAS or k_grid != K_GRID) and under:
        raise SystemExit("a non-registered lambda or k grid may not write under results/")
    if under and args.replay != "hf":
        raise SystemExit("under results/ the replay source must be the pinned checkpoint (--replay hf)")
    state_path = Path(str(out) + ".state.jsonl")
    meta_path = Path(str(out)[:-5] + ".meta.json") if str(out).endswith(".json") else Path(str(out) + ".meta.json")
    if under:
        for p in (out, state_path, meta_path):
            if p.exists():
                raise SystemExit(f"{p} exists: a registered payload is never overwritten (delete it by hand if that is the intent)")
        want = OUT_OF_HARVEST.get(Path(args.harvest).name)
        if want is None or out.resolve() != (ROOT / "results" / "real" / want).resolve():
            raise SystemExit(f"under results/ the out path for harvest {Path(args.harvest).name} must be "
                             f"results/real/{want or '<unknown harvest>'}")
    strat = strat_reference(Path(args.harvest), args.strat, smoke, under)
    if under and strat is not None and strat["encoding"] != "prev_table":
        raise SystemExit("under results/ the stratified payload's twin encoding must be prev_table: the smoothed previous-token "
                         "table is TABLE_PREV, and the SHRINKAGE would otherwise mix encodings")
    src = load_replay_source(args.replay)
    if under and src["sha256"] != REPLAY_SOURCE_SHA256:
        raise SystemExit(f"replay source sha {src['sha256'][:12]} is not the pinned {REPLAY_SOURCE_SHA256[:12]}: refusing under results/")
    if under and (src["eps"] != 1e-5 or src["gates"].shape[0] != L):
        raise SystemExit("under results/ the replay's eps must be 1e-5 and its layer count 16 (config.json is outside the pinned sha)")
    data = pr.S3Data(args.harvest, only_seeds=only, smoke_split_val=args.smoke_split_val)
    if strat is not None and strat["harvest_npz_sha256"] != data.npz_shas:
        raise SystemExit("the stratified payload was read on different harvest shards than this run opens")
    hidden = load_hidden(data)
    label_of_token, n_classes = load_label_space(args.buckets, args.glue)
    vocab = int(data.tokens.max()) + 1
    t_replay = time.time()
    replay = replay_table(src, vocab)
    t_replay = time.time() - t_replay
    r2 = R2(data, label_of_token, n_classes, hidden, replay, strat=strat, lambdas=lambdas, k_grid=k_grid)
    r2.fit()
    if strat is None:
        val_twin = r2.evaluate("val", arms=ARMS_TWIN)         # the twin's own rule, re-run
        r2.select(val_twin, ARMS_TWIN)
    encoding = r2.encoding_selected
    grid = r2.evaluate_free_grid("val")
    r2.select_k(grid)
    r2.fit_k(r2.k_selected)
    arms_val = tuple(a for a in ARMS_RIDGE_R2 if a != "free_r2")
    val_r2 = r2.evaluate("val", arms=arms_val)
    r2.select(val_r2, arms_val)
    test = r2.evaluate("test", arms=ARMS_REQUIRED, lambdas_of_arm=r2.lambda_selected)
    rows = r2.state_rows(test)
    conclusion = conclude(rows, encoding, r2.k_selected, None if strat is None else strat["_rows"],
                          None if strat is None else strat["gate_eq"])
    agreement = {split: r2.replay_agreement(split) for split in SPLITS}
    git_commit, tracked = pr._git()
    prov = {
        "registered": REGISTERED,
        "git_commit": git_commit,
        "git_status_tracked": tracked,
        "instrument_sha256": pr._sha(Path(__file__)),
        "frozen_strat": {"path": "tools/run_prefetch_strat.py", "sha256_lf": strat_sha},
        "frozen_twin": {"path": "tools/run_prefetch_bigram.py", "sha256_lf": twin_sha},
        "frozen_instrument": {"path": "tools/run_prefetch_readouts.py", "sha256_lf": parent_sha},
        "harvest_dir": str(args.harvest),
        "harvest_npz_sha256": data.npz_shas,
        "seeds": data.seeds,
        "smoke": smoke,
        "smoke_split_val": bool(args.smoke_split_val),
        "strat": _strat_header(strat),
        "replay_source": _source_record(src),
        "replay_source_pinned": REPLAY_SOURCE_SHA256,
        "replay_source_matches_pinned": bool(src["sha256"] == REPLAY_SOURCE_SHA256),
        "replay_vocab": int(vocab),
        "replay_probe": replay_probe(replay),
        "replay_seconds": t_replay,
        "replay_agreement": agreement,
        "hidden": {"width": int(hidden.shape[2]), "dtype": str(hidden.dtype), "train_positions": r2.h_n,
                   "kept_variance_share": r2.h_kept_share, "eigen_top8": r2.h_eigen_top, "eigen_1024th": r2.h_eigen_last,
                   "eigen_1025th": r2.h_eigen_next},
        "label_space": {"buckets": str(args.buckets), "buckets_sha256": pr._sha(args.buckets),
                        "glue": str(args.glue), "glue_sha256": pr._sha(args.glue), "n_classes": int(n_classes),
                        "n_tokens": int(label_of_token.shape[0])},
        "constants": {"budgets": list(BUDGETS), "horizon": HORIZON, "lambdas": list(lambdas), "k_grid": [k_tag(k) for k in k_grid],
                      "label_budget": LABEL_BUDGET, "material": MATERIAL, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
                      "chunk": CHUNK, "strata": list(STRATA), "unions": {k: list(v) for k, v in UNIONS.items()},
                      "reproduce_near_share": REPRODUCE_NEAR_SHARE, "reproduce_near_hits": REPRODUCE_NEAR_HITS,
                      "identity_tol": IDENTITY_TOL, "identity_scopes": list(IDENTITY_SCOPES), "token_probe": list(TOKEN_PROBE),
                      "arm_dims": {a: arm_dims(a, encoding) for a in ARMS_REQUIRED},
                      "arm_k": {a: k_tag(ARM_K[a]) for a in ARM_K}},
        "n_positions": r2.n_positions,
        "n_test_prompts": int(r2.prompt_ids["test"].shape[0]),
        "strata_counts": r2.strata_counts(),
        "table_coverage": r2.table_coverage(),
        "encoding_selected": encoding,
        "encoding_source": "strat" if strat is not None else "val",
        "k_selected": k_tag(r2.k_selected),
        "k_grid_edge": r2.k_grid_edge,
        "k_val_table": r2.k_val_table,
        "lambda_selected": {k: (None if v is None else float(v)) for k, v in r2.lambda_selected.items()},
        "lambda_source": r2.lambda_source,
        "lambda_grid_edge": r2.grid_edge,
        "val_table": r2.val_table,
        "blas": rs.blas_info(),
        "args": redact_args(vars(args)),
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "started_unix": started,
        "runtime_s": time.time() - started,
    }
    payload = {"registered": REGISTERED, "provenance": prov, "conclusion": conclusion, "n_state_rows": len(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    header = {"state_header": True, "registered": REGISTERED, "harvest_npz_sha256": data.npz_shas, "smoke": smoke,
              "encoding": encoding, "k_selected": k_tag(r2.k_selected), "lambda_selected": prov["lambda_selected"],
              "strat": _strat_header(strat), "replay_source_sha256": src["sha256"]}
    rs._write_lf(state_path, "".join(json.dumps(x) + "\n" for x in [header] + rows))
    rs._write_lf(out, json.dumps(payload, indent=1))
    rs._write_lf(meta_path, json.dumps(prov, indent=1))
    print_summary(payload)
    return payload


def conclude_from(payload_path: Path) -> dict:
    assert_frozen_strat()
    rs.assert_frozen_twin()
    rb.assert_frozen_instrument()
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    if payload.get("registered") != REGISTERED:
        raise SystemExit("payload is not a generalising free baseline (R2) payload")
    header, rows = pr.load_state(Path(str(payload_path) + ".state.jsonl"))
    prov = payload["provenance"]
    if header["harvest_npz_sha256"] != prov["harvest_npz_sha256"]:
        raise SystemExit("state header harvest shas differ from the payload's")
    if header.get("encoding") != prov["encoding_selected"]:
        raise SystemExit("state header encoding differs from the payload's")
    if header.get("k_selected") != prov["k_selected"]:
        raise SystemExit("state header k differs from the payload's")
    if header.get("lambda_selected") != prov["lambda_selected"]:
        raise SystemExit("state header lambdas differ from the payload's")
    if header.get("strat") != prov["strat"]:
        raise SystemExit("state header stratified reference differs from the payload's")
    if header.get("replay_source_sha256") != prov["replay_source"]["sha256"]:
        raise SystemExit("state header replay source sha differs from the payload's")
    if header.get("registered") != REGISTERED or bool(header.get("smoke")) != bool(prov.get("smoke")):
        raise SystemExit("state header registration or smoke flag differs from the payload's")
    if len(rows) != payload["n_state_rows"]:
        raise SystemExit("state row count differs from the payload's")
    # the selected k and every new arm's lambda are RE-DERIVED from the payload's own val tables, whose keys must be
    # the payload's own grids (a malformed payload is refused, never a crash)
    lambdas = [float(x) for x in prov["constants"]["lambdas"]]
    k_grid = [k_of_tag(x) for x in prov["constants"]["k_grid"]]
    lam_keys = {str(float(x)) for x in lambdas}
    if set(prov["k_val_table"]) != {k_tag(k) for k in k_grid} or any(set(row) != lam_keys for row in prov["k_val_table"].values()):
        raise SystemExit("the payload's k val table does not carry its own k and lambda grids")
    for arm in ARMS_RIDGE_R2:
        if set(prov["val_table"].get(arm, {})) != lam_keys:
            raise SystemExit(f"the payload's val table for {arm} does not carry its own lambda grid")
    k_best, lam_best = _select_k_from_table(prov["k_val_table"], k_grid, lambdas)
    if k_tag(k_best) != prov["k_selected"] or lam_best != float(prov["lambda_selected"]["free_r2"]):
        raise SystemExit("the payload's (k, lambda) for free_r2 is not the pair its val table selects")
    if bool(prov.get("k_grid_edge")) != bool(k_best in (k_grid[0], k_grid[-1])):
        raise SystemExit("the payload's k grid-edge flag is not what its selected k implies")
    if prov["val_table"].get("free_r2") != prov["k_val_table"][k_tag(k_best)]:
        raise SystemExit("the payload's free_r2 val table is not its k table's row at the selected k")
    for arm in ARMS_RIDGE_R2:
        if arm == "free_r2":
            continue
        if _select_lambda(prov["val_table"][arm], lambdas) != float(prov["lambda_selected"][arm]):
            raise SystemExit(f"the payload's lambda for {arm} is not the one its val table selects")
    for arm in ARMS_RIDGE_R2:
        lam = float(prov["lambda_selected"][arm])
        if bool(prov["lambda_grid_edge"].get(arm)) != bool(lam in (lambdas[0], lambdas[-1])):
            raise SystemExit(f"the payload's grid-edge flag for {arm} is not what its lambda implies")
    if pr._under_results(Path(payload_path)):
        # a registered payload: the registered grids, the pinned replay source, a stratified record, no smoke
        if prov.get("smoke") or header.get("strat") is None:
            raise SystemExit("a payload under results/ must be a registered run with a stratified record")
        if [float(x) for x in prov["constants"]["lambdas"]] != list(LAMBDAS) or prov["constants"]["k_grid"] != [k_tag(k) for k in K_GRID]:
            raise SystemExit("a payload under results/ must carry the registered lambda and k grids")
        if prov["replay_source"].get("sha256") != REPLAY_SOURCE_SHA256 or prov["replay_source"].get("kind") != "hf":
            raise SystemExit("a payload under results/ must carry the pinned replay source")
    strat_rows, strat_cells = None, None
    st = header.get("strat")
    if st is not None:
        if st["encoding"] != header["encoding"]:
            raise SystemExit("the state header's encoding is not the stratified payload's")
        for arm in ARMS_TWIN:
            if float(st["lambda_selected"][arm]) != float(header["lambda_selected"][arm]):
                raise SystemExit(f"the state header's lambda for {arm} is not the stratified payload's")
        spath = ROOT / st["path"] if not Path(st["path"]).is_absolute() else Path(st["path"])
        if not spath.exists():
            raise SystemExit(f"the committed stratified payload {st['path']} is not present; REPRODUCE cannot be recomputed")
        fresh = read_strat(spath)
        if fresh["sha256"] != st["sha256"] or fresh["state_sha256"] != st["state_sha256"]:
            raise SystemExit(f"the committed stratified payload {st['path']} is not the one this run read "
                             f"(sha {st['sha256'][:12]} -> {fresh['sha256'][:12]}; state {st['state_sha256'][:12]} -> "
                             f"{fresh['state_sha256'][:12]})")
        if _strat_header(fresh) != st:
            raise SystemExit(f"the committed stratified payload {st['path']} differs from the header's record of it beyond the shas")
        strat_rows, strat_cells = fresh["_rows"], fresh["gate_eq"]
    got = conclude(rows, header["encoding"], k_of_tag(header["k_selected"]), strat_rows, strat_cells)
    if json.dumps(got, sort_keys=True) != json.dumps(payload["conclusion"], sort_keys=True):
        raise SystemExit("RECOMPUTE MISMATCH: the state file does not reproduce the payload's conclusion")
    tag = " (SMOKE — not evidence)" if prov.get("smoke") else ""
    print(f"conclude-from: state file reproduces the payload exactly{tag}")
    print_summary(payload)
    return got


def _fmt(d: dict | None) -> str:
    return "n/a" if d is None else f"{d['delta']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]"


def print_summary(payload: dict) -> None:
    c = payload["conclusion"]; lab = c["labels"]; prov = payload["provenance"]
    print(f"LABEL: {lab.get('label')}   (smoke={prov.get('smoke')}; encoding={lab.get('encoding')} from "
          f"{prov.get('encoding_source')}; k={lab.get('k_selected')} edge={prov.get('k_grid_edge')}; void={lab.get('void')})")
    rep = lab.get("reproduce")
    if rep is None:
        print("  REPRODUCE: not applicable (no stratified payload read)")
    else:
        print(f"  REPRODUCE: {lab.get('reproduce_status')} (rows {rep['status']})  strat rows {rep['n_strat_rows']}  compared "
              f"{rep['n_compared']}  missing {rep['missing_in_r2']}  extra {rep['extra_in_r2']}  needed mismatches "
              f"{rep['needed_mismatch_rows']}  hits mismatches {rep['hits_mismatch_rows']}  max |gap| {rep['max_abs_hits_gap']}  "
              f"identity (twin D_eq = strat's on all/covered/fallback): {lab.get('gate_eq_matches_strat')}")
    if lab.get("label") == "INCOMPLETE":
        print("missing arms:", lab["missing_arms"], "missing label cells:", lab["missing_label_cells"]); return
    for scope in SCOPES:
        s = lab["scopes"].get(scope, {})
        share = s.get("share")
        print(f"  scope {scope:12s} positions {s.get('positions', 0):7d}  share {share if share is None else format(share, '.4f')}  "
              f"prompts {s.get('prompts_with_positions', 0)}")
    sr = lab.get("shrinkage_readings") or {}
    print(f"  HEADLINE shrinkage fallback {str(sr.get('fallback')):10s} {_fmt(lab['shrinkage_fallback'])}  "
          f"share of twin FB margin {lab.get('shrinkage_share_of_fallback_margin')}")
    print(f"           shrinkage covered  {str(sr.get('covered')):10s} {_fmt(lab['shrinkage_covered'])}   all "
          f"{str(sr.get('all')):10s} {_fmt(lab['shrinkage_all'])}")
    print(f"  Q1 {lab.get('q1')}: D_eq^R2 fallback {str(lab.get('gate_eq_r2_fallback_reading')):10s} {_fmt(lab['gate_eq_r2_fallback'])}  "
          f"straddle={lab['fallback_floor_straddle']}  negative={lab['fallback_negative']}")
    print(f"     D_eq^R2 all      {str(lab.get('gate_eq_r2_all_reading')):10s} {_fmt(lab['gate_eq_r2_all'])}  straddle={lab['all_floor_straddle']}")
    print(f"     D_eq^R2 covered  {str(lab.get('gate_eq_r2_covered_reading')):10s} {_fmt(lab.get('gate_eq_r2_covered'))}  "
          f"twin arm vs free_r2 all {_fmt(lab.get('gate_eq_r2_twinarm_all'))}  k at replay end={lab.get('k_at_replay_end')}  "
          f"address handicap={lab.get('address_handicap')} {_fmt(lab.get('address_handicap_all'))}")
    print(f"  Q2 {lab.get('q2')}: D_eq^H all {str(lab.get('d_eq_h_all_reading')):10s} {_fmt(lab['d_eq_h_all'])}  straddle={lab['d_eq_h_floor_straddle']}  "
          f"reader guard={lab.get('q2_reader_guard')} (free_h-free_r2 {_fmt(lab.get('free_h_gain_all'))})")
    print(f"     D_add^H all {str(lab.get('d_add_h_all_reading')):10s} {_fmt(lab['d_add_h_all'])}  straddle={lab['d_add_h_floor_straddle']}  "
          f"(Q2 straddle={lab['q2_floor_straddle']})  anchor {_fmt(lab['h_dilution_anchor'])}  inconsistent cause={lab['h_inconsistent_cause']}")
    print(f"  sentence: {lab['sentence']}")
    print(f"  said in words: {lab.get('said_in_words')}")
    for B in BUDGETS:
        for scope in SCOPES:
            parts = []
            for name, _, _ in DELTA_PAIRS:
                d = c["deltas"].get(f"{name}|B={B}|{scope}")
                if d:
                    parts.append(f"{name} {_fmt(d)}")
            for i in range(0, len(parts), 5):
                print(f"  B={B:2d} {scope:12s} " + " | ".join(parts[i:i + 5]) if i == 0 else f"  {'':17s}" + " | ".join(parts[i:i + 5]))
    for B in BUDGETS:
        for arm in ARMS_REQUIRED:
            t = c["tables"].get(f"{arm}|B={B}|all")
            if t:
                a = t["all"]; print(f"  B={B:2d} {arm:18s} all {a['point']:.4f} [{a['ci_lo']:.4f}, {a['ci_hi']:.4f}]")
    print("  k val table (B=16, pooled val):", prov.get("k_val_table"))
    print("  lambda:", prov.get("lambda_selected"))
    print("  lambda source:", prov.get("lambda_source"))
    print("  grid-edge:", prov.get("lambda_grid_edge"), " k edge:", prov.get("k_grid_edge"))
    ag = prov.get("replay_agreement", {})
    for split in SPLITS:
        a = ag.get(split, {})
        if a.get("n"):
            pg = a["prev_vs_S_t"]["per_gate"]
            print(f"  replay agreement {split:5s}: prev->S[t] pooled {a['prev_vs_S_t']['pooled']:.4f} gate0 {pg[0]:.4f} "
                  f"min {min(pg):.4f} max {max(pg):.4f} | cur->S[t+1] pooled {a['cur_vs_S_t1']['pooled']:.4f}")
    print("  hidden:", prov.get("hidden"))
    print("  strata (test):", prov.get("strata_counts", {}).get("test"))
    print("  replay source:", {k: v for k, v in (prov.get("replay_source") or {}).items() if k in ("kind", "sha256", "snapshot", "path")},
          "matches pinned:", prov.get("replay_source_matches_pinned"))
    print("  blas:", prov.get("blas"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--harvest", default=str(ROOT / "results" / "real" / "harvest_moe"))
    ap.add_argument("--out", default=str(ROOT / "results" / "real" / "prefetch_r2_s3.json"))
    ap.add_argument("--buckets", default=str(pr.BUCKETS16))
    ap.add_argument("--glue", default=str(pr.GLUE16))
    ap.add_argument("--strat", default=None,
                    help="the committed stratified payload whose twin encoding, lambdas and state rows this read takes "
                         "(default: derived from the harvest name; 'none' only outside results/)")
    ap.add_argument("--replay", default="hf",
                    help="'hf' = the pinned cached checkpoint snapshot (required under results/); or a path to an .npz "
                         "fixture (embed, gates, norms, eps) for tests")
    ap.add_argument("--only-seeds", default=None, help="smoke only: comma-separated generation seeds")
    ap.add_argument("--smoke-split-val", action="store_true",
                    help="smoke only: keep the val prompts and re-split them by (prompt_idx // 7) %% 3")
    ap.add_argument("--lambdas", default=None, help="tests/smoke only: comma-separated grid (refused under results/)")
    ap.add_argument("--k-grid", default=None, help="tests/smoke only: comma-separated k grid, 'inf' allowed (refused under results/)")
    ap.add_argument("--conclude-from", default=None, help="recompute a payload's conclusion from its state file")
    args = ap.parse_args(argv)
    if args.conclude_from:
        conclude_from(Path(args.conclude_from))
        return
    run(args)


if __name__ == "__main__":
    main()

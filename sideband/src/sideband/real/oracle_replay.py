"""DRAFT STATUS (2026-10-01): UNFROZEN. Committed as a DRAFT beside
docs/OQ19_ORACLE_CEILING_DRAFT.md. The registration block this docstring
names was never inserted into docs/BLUEPRINT.md, no freeze commit exists and
no replay or registered cell has run; the text below describes the draft as
it stood on 2026-09-07.

OQ-19 ORACLE REPLAY (plan of record item 2, 2026-09-06; registered in
docs/BLUEPRINT.md "OQ-19 ORACLE-INTERMEDIATE CEILING REGISTRATION" before
any replay ran; three pre-run critic rounds applied): REPLAY of a
committed harvest's logged generations through the IDENTICAL batched,
left-padded, KV-cached path the harvester used — the same prompt batches
in the same order, the same padding, the same forward kwargs, the same
library versions and GPU (asserted against the parent metas), AND the
same per-row sampling generators drawing at every step exactly as the
harvester did. Running rows are fed the LOGGED token; finished rows
(beyond their logged length) are fed the DRAWN token, which reproduces the
post-EOS inputs the harvester sampled and then zeroed in storage — this
matters on OLMoE, whose MoE block groups tokens per expert ACROSS the rows
of a batch and whose 4-bit kernels take different paths for one-token and
multi-token expert inputs, so a finished row's input changes the running
rows' numerics (second critic round). At every anchor it captures the
post-attention-norm OUTPUT at the REGISTERED layers — the MLP input on
Llama, the router input on OLMoE: the activation the tapped sketch /
expert selection is a deterministic function of (the first batch of every
seed also asserts, through a pre-hook on the MLP module, that this tensor
IS the MLP's input) — the OQ-19 oracle block, beside a per-position
FIDELITY record: the DRAWN token against the logged token (a one-sample
test of p_a per position; its RATE over valid positions bounds the mean
p-discrepancy; the draws themselves are stored, so the post-EOS feeds are
recorded), the recomputed argmax and the recomputed probabilities of the
logged top-32 ids against the logged ones (deterministic p diagnostics,
reported), the recomputed sketch / expert set against the logged slots
(set OVERLAP per layer; exact equality as a diagnostic), and the
recomputed h_a against the logged hidden (max-abs difference: the
ALIGNMENT certificate — the oracle is captured in the same forward as
h_replay, which must agree with h_logged at the same anchor within the
registered floors). A flipped draw on a valid position does not perturb
the replay (the logged token is still fed) and reads as a p-difference,
not misalignment; misalignment shows as match rates far below the floor
and O(1) h differences on every row.

Why replay, not re-harvest: it keeps the SAME rows, labels, committed cells
and twins as OQ-17 / OQ-18, so the oracle arms pair against the committed
fplus / fplus_b / fplus_r cells on identical prompts and anchors; the
fidelity record replaces the assumption that a fresh forward would
reproduce the logged one.

OUTPUT: <out-dir>/oracle_s{seed}.npz (gitignored raw: oracle (rows, T, L,
d) float16 zeroed beyond each row's length; drawn (rows, T) int32 — the
draw at EVERY step, post-EOS included; token_match, argmax_match (rows, T)
bool; topp_maxabs, h_maxabs, h_absmax_logged (rows, T) float32;
slot_overlap (rows, T, L_tap) float16; slot_match (rows, T, L_tap) bool;
lengths; prompt_idx) plus the committed <out-dir>/oracle_s{seed}.meta.json
binding the PARENT npz sha, the layers, the load regime, the library
versions, the GPU and the fidelity summary (recomputed from the arrays by
every consumer). The side-files live in their OWN directory: sideband.
harvest.verified_seed_files refuses a harvest directory with mixed
prefixes, so nothing is ever written into a harvest directory (the tool
refuses an out-dir holding another prefix's metas, and never rewrites a
committed side-file).

Usage (GPU box):
    python -m sideband.real.oracle_replay --harvest results/real/harvest_shadow \
        --out-dir results/real/oracle_shadow --layers 7,15,23,31
    python -m sideband.real.oracle_replay --harvest results/real/harvest_moe \
        --out-dir results/real/oracle_moe --layers 3,7,11,15
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from ..harvest import verified_seed_files
from . import require_real_deps
from .shadow_telemetry import NormCatch, ShadowTap, _pad_cat, row_generator_seeds

SHADOW_PREFIX = "shadow"
MOE_PREFIX = "moe"
ORACLE_PREFIX = "oracle"
# Registered layers per source (docs/BLUEPRINT.md OQ-19 block): S1 = the
# four tapped down_proj layers; S3 = four of the sixteen router layers,
# evenly spaced, the last MoE block included.
REGISTERED_LAYERS = {SHADOW_PREFIX: (7, 15, 23, 31), MOE_PREFIX: (3, 7, 11, 15)}
ROW_SEED_CONVENTION = "SeedSequence(seed).spawn(n_prompts)[i] % (2**63-1)"
FIDELITY_TOL = 1e-6
FLOAT16_MAX = 65504.0
# arrays with a T axis that carry data only within a row's logged length;
# `drawn` is deliberately NOT here (the post-EOS draws are the record)
_MASKED_2D = ("token_match", "argmax_match", "topp_maxabs", "h_maxabs", "h_absmax_logged")
_MASKED_3D = ("slot_match", "slot_overlap")


def seed_of_npz(name: str) -> int:
    """'shadow_s10.npz' -> 10."""
    return int(Path(name).name.split("_s")[1].split(".")[0])


def chunk_bounds(n_prompts: int, batch_size: int) -> list[tuple[int, int]]:
    """The harvester's batch composition: contiguous prompt slices in prompt
    order, the last one short."""
    if n_prompts <= 0 or batch_size <= 0:
        raise ValueError("n_prompts and batch_size must be positive")
    return [(s, min(s + batch_size, n_prompts)) for s in range(0, n_prompts, batch_size)]


def sets_equal_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(B, L, top) sorted id arrays (-1 padded) -> (B, L) bool exact
    set-equality per (row, layer)."""
    a = np.asarray(a)
    b = np.asarray(b)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} vs {b.shape}")
    return np.all(a == b, axis=-1)


def set_overlap_rows(recomputed: np.ndarray, logged: np.ndarray) -> np.ndarray:
    """(B, L, top) -1-padded id arrays -> (B, L) fraction of the LOGGED set
    found in the recomputed set (1.0 for an empty logged set)."""
    recomputed = np.asarray(recomputed)
    logged = np.asarray(logged)
    if recomputed.shape != logged.shape:
        raise ValueError(f"shape mismatch {recomputed.shape} vs {logged.shape}")
    B, L, _ = logged.shape
    out = np.ones((B, L), np.float32)
    for b in range(B):
        for li in range(L):
            lg = logged[b, li]
            lg = lg[lg >= 0]
            if lg.size == 0:
                continue
            rc = recomputed[b, li]
            rc = rc[rc >= 0]
            out[b, li] = float(np.isin(lg, rc).mean())
    return out


def finalize_replay(arrays: dict, lengths: np.ndarray) -> dict:
    """The harvester's hygiene rule on the replay's outputs: nothing beyond
    a row's logged length is data — the oracle and every fidelity array
    are zeroed / cleared there. `drawn` is kept whole (the post-EOS draws
    are exactly the inputs the harvester fed and are the record of them).
    Inputs are not mutated."""
    lengths = np.asarray(lengths, dtype=np.int64)
    out = {k: np.array(v, copy=True) for k, v in arrays.items()}
    n_rec = out["oracle"].shape[1]
    valid = np.arange(n_rec)[None, :] < lengths[:, None]
    for b in range(out["oracle"].shape[0]):
        out["oracle"][b, int(lengths[b]):] = 0
    for k in _MASKED_2D:
        if k in out:
            out[k] = np.where(valid, out[k], 0).astype(out[k].dtype)
    for k in _MASKED_3D:
        if k in out:
            out[k] = np.where(valid[:, :, None], out[k], 0).astype(out[k].dtype)
    return out


def fidelity_summary(arrays: dict, lengths: np.ndarray, layer_names: list[str]) -> dict:
    """The drawn-token match rate, the deterministic p diagnostics, the
    per-layer mean overlap and exact-match rates, and the h_a difference
    percentiles, over the VALID positions (a < length) only. Recomputed
    from the arrays by every consumer."""
    lengths = np.asarray(lengths, dtype=np.int64)
    slot_match, slot_overlap = arrays["slot_match"], arrays["slot_overlap"]
    if slot_match.shape[2] != len(layer_names):
        raise ValueError(f"{len(layer_names)} layer names for {slot_match.shape[2]} tapped layers")
    T = slot_match.shape[1]
    valid = np.arange(T)[None, :] < lengths[:, None]
    n_valid = int(valid.sum())
    if n_valid == 0:
        raise ValueError("no valid positions")
    per_layer = {}
    for li, name in enumerate(layer_names):
        m = slot_match[:, :, li][valid]
        o = slot_overlap[:, :, li][valid].astype(np.float64)
        per_layer[name] = {"exact_match_rate": float(m.mean()), "mean_overlap": float(o.mean()),
                           "n_positions": int(m.size)}
    hm = arrays["h_maxabs"][valid].astype(np.float64)
    hl = np.maximum(arrays["h_absmax_logged"][valid].astype(np.float64), 1e-12)
    rel = hm / hl
    tp = arrays["topp_maxabs"][valid].astype(np.float64)
    pct = (50, 90, 99, 100)
    return {
        "n_valid_positions": n_valid,
        "token_match_rate": float(arrays["token_match"][valid].mean()),
        "argmax_match_rate": float(arrays["argmax_match"][valid].mean()),
        "topp_maxabs_percentiles": {str(p): float(np.percentile(tp, p)) for p in pct},
        "slot_overlap_mean_min": float(min(v["mean_overlap"] for v in per_layer.values())),
        "slot_exact_match_rate_min": float(min(v["exact_match_rate"] for v in per_layer.values())),
        "slot_per_layer": per_layer,
        "h_maxabs_percentiles": {str(p): float(np.percentile(hm, p)) for p in pct},
        "h_relmax_percentiles": {str(p): float(np.percentile(rel, p)) for p in pct},
        "h_exact_rate": float((hm == 0).mean()),
    }


def _fidelity_close(a: dict, b: dict, tol: float = FIDELITY_TOL) -> bool:
    keys = ("token_match_rate", "argmax_match_rate", "slot_overlap_mean_min", "slot_exact_match_rate_min",
            "h_exact_rate", "n_valid_positions")
    if any(abs(float(a[k]) - float(b[k])) > tol for k in keys):
        return False
    for k in ("h_maxabs_percentiles", "h_relmax_percentiles", "topp_maxabs_percentiles"):
        if any(abs(float(a[k][p]) - float(b[k][p])) > tol * max(1.0, abs(float(b[k][p]))) for p in b[k]):
            return False
    return True


def oracle_meta_check(meta: dict, parent_shas: dict[str, str], layers: tuple[int, ...]) -> None:
    """Refuse an oracle side-file whose meta does not bind the loaded
    harvest's npz sha or was replayed at other layers."""
    pf, ps = meta.get("parent_npz_file"), meta.get("parent_npz_sha256")
    if pf not in parent_shas or parent_shas[pf] != ps:
        raise SystemExit(f"oracle side-file {meta.get('npz_file')} binds parent {pf!r} sha {str(ps)[:12]} "
                         "which is not the loaded harvest's — refusing")
    if tuple(int(x) for x in meta.get("layers", ())) != tuple(layers):
        raise SystemExit(f"oracle side-file {meta.get('npz_file')} was replayed at layers "
                         f"{meta.get('layers')}, not the registered {list(layers)} — refusing")


class OracleData:
    """Concatenated oracle side-files, loaded in the HARVEST'S OWN seed
    order (sideband.harvest.verified_seed_files sorts metas lexicographically,
    so a replication harvest reads s10, s11, s8, s9 — the side-file of each
    parent is opened by the parent's name, never by numeric seed), sha-bound
    to their parents, row-aligned by lengths and prompt_idx at load, and
    with each meta's fidelity summary RECOMPUTED from the arrays and
    asserted equal. The big array is preallocated once as (rows, T, L * d)
    float16 and filled seed by seed (each seed's member is read once; the
    finiteness check runs on the float16 member without a cast)."""

    def __init__(self, oracle_dir: str | Path, harvest, layers: tuple[int, ...]):
        self.dir = Path(oracle_dir)
        self.layers = tuple(int(i) for i in layers)
        self.metas: list[dict] = []
        self.npz_shas: dict[str, str] = {}
        self.meta_shas: dict[str, str] = {}
        tmax = int(harvest.tokens.shape[1])
        n_rows = int(harvest.n_rows)
        self.oracle_flat = None
        self.slot_match = None
        self.slot_overlap = None
        r0 = 0
        for pf, psha in harvest.npz_shas.items():
            seed = seed_of_npz(pf)
            mp = self.dir / f"{ORACLE_PREFIX}_s{seed}.meta.json"
            if not mp.exists():
                raise SystemExit(f"no oracle side-file for parent {pf} (expected {mp.name}) — refusing")
            meta = json.loads(mp.read_text())
            npz_path = self.dir / meta["npz_file"]
            sha = hashlib.sha256(npz_path.read_bytes()).hexdigest()
            if sha != meta["npz_sha256"]:
                raise SystemExit(f"{mp.name}: oracle npz sha mismatch — refusing unbound side-file")
            if meta.get("parent_npz_file") != pf:
                raise SystemExit(f"{mp.name} binds parent {meta.get('parent_npz_file')!r}, expected {pf!r}")
            oracle_meta_check(meta, harvest.npz_shas, self.layers)
            z = np.load(npz_path)
            o = z["oracle"]
            n, t = int(o.shape[0]), int(o.shape[1])
            L, d = int(o.shape[2]), int(o.shape[3])
            if self.oracle_flat is None:
                self.d = d
                self.layer_names = list(meta["layer_names"])
                self.oracle_flat = np.zeros((n_rows, tmax, L * d), np.float16)
                n_tap = int(z["slot_match"].shape[2])
                self.slot_match = np.zeros((n_rows, tmax, n_tap), bool)
                self.slot_overlap = np.zeros((n_rows, tmax, n_tap), np.float16)
            if t > tmax or L != len(self.layers) or d != self.d or r0 + n > n_rows:
                raise SystemExit(f"{npz_path.name}: oracle shape {o.shape} does not fit the harvest / registration")
            lengths = z["lengths"].astype(np.int64)
            if not np.array_equal(lengths, harvest.lengths[r0:r0 + n]) or \
                    not np.array_equal(z["prompt_idx"].astype(np.int64), harvest.prompt_idx[r0:r0 + n]):
                raise SystemExit(f"{npz_path.name}: lengths / prompt_idx differ from the harvest rows it "
                                 "would occupy — row misalignment; refusing")
            if not np.isfinite(o).all():
                raise SystemExit(f"{npz_path.name}: non-finite oracle values — refusing")
            arrays = {k: z[k] for k in ("token_match", "argmax_match", "topp_maxabs", "slot_match", "slot_overlap",
                                        "h_maxabs", "h_absmax_logged")}
            fid = fidelity_summary(arrays, lengths, list(meta["sketch_layer_names"]))
            if not _fidelity_close(fid, meta["fidelity"]):
                raise SystemExit(f"{mp.name}: the meta's fidelity summary does not reproduce from the arrays — refusing")
            self.oracle_flat[r0:r0 + n, :t] = o.reshape(n, t, L * d)
            self.slot_match[r0:r0 + n, :t] = z["slot_match"]
            self.slot_overlap[r0:r0 + n, :t] = z["slot_overlap"]
            # the harvester's hygiene rule, enforced at load as well: nothing
            # beyond a row's length is data, whatever the side-file holds
            for b in range(n):
                ln = int(lengths[b])
                self.oracle_flat[r0 + b, ln:] = 0
                self.slot_match[r0 + b, ln:] = False
                self.slot_overlap[r0 + b, ln:] = 0
            r0 += n
            self.metas.append(meta)
            self.npz_shas[meta["npz_file"]] = sha
            self.meta_shas[mp.name] = hashlib.sha256(mp.read_bytes()).hexdigest()
        if r0 != n_rows:
            raise SystemExit("oracle side-files do not cover every harvest row — refusing")
        fids = [m["fidelity"] for m in self.metas]
        self.token_match_rate_min = min(float(f["token_match_rate"]) for f in fids)
        self.slot_overlap_mean_min = min(float(f["slot_overlap_mean_min"]) for f in fids)
        self.slot_exact_rate_min = min(float(f["slot_exact_match_rate_min"]) for f in fids)
        self.h_relmax_median_max = max(float(f["h_relmax_percentiles"]["50"]) for f in fids)
        self.h_relmax_p99_max = max(float(f["h_relmax_percentiles"]["99"]) for f in fids)

    @property
    def nbytes(self) -> int:
        return int(self.oracle_flat.nbytes)


# ---------------------------------------------------------------------------
# GPU side
# ---------------------------------------------------------------------------

class OracleCatch:
    """Forward hooks on the post-attention norms of the registered layers;
    captures the LAST position's output per row (real for every row under
    LEFT padding), the MLP / router input of that layer."""

    def __init__(self, model, layer_indices: tuple[int, ...]):
        self.layer_indices = tuple(int(i) for i in layer_indices)
        self.latest: dict[int, object] = {}
        self._handles = []
        self.layer_names = []
        layers = getattr(getattr(model, "model", None), "layers", None)
        if layers is None:
            raise SystemExit("expected a *ForCausalLM exposing .model.layers")
        for i in self.layer_indices:
            norm = getattr(layers[i], "post_attention_layernorm", None)
            if norm is None:
                raise SystemExit(f"layer {i} has no post_attention_layernorm")
            self.layer_names.append(f"model.layers.{i}.post_attention_layernorm")
            self._handles.append(norm.register_forward_hook(self._make_hook(i)))

    def _make_hook(self, i: int):
        def hook(_module, _inputs, output):
            self.latest[i] = output[:, -1, :].detach()
        return hook

    def collect(self, n_rows: int) -> np.ndarray:
        out = []
        for i in self.layer_indices:
            if i not in self.latest:
                raise RuntimeError(f"oracle layer {i} did not fire since last collect()")
            x = self.latest[i].float().cpu().numpy()
            if x.shape[0] != n_rows:
                raise RuntimeError(f"layer {i}: captured {x.shape[0]} rows, expected {n_rows}")
            if not np.isfinite(x).all() or np.abs(x).max() > FLOAT16_MAX:
                raise RuntimeError(f"layer {i}: non-finite or float16-overflowing oracle values")
            out.append(x.astype(np.float16))
        self.latest = {}
        return np.stack(out, axis=1)  # (B, L, d)

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


class MLPInputCheck:
    """Forward-PRE hooks on the registered layers' MLP modules: the tensor
    the MLP receives must be the norm output OracleCatch captured — the
    capture point certified in code, not by reading the model source."""

    def __init__(self, model, layer_indices: tuple[int, ...]):
        self.layer_indices = tuple(int(i) for i in layer_indices)
        self.latest: dict[int, object] = {}
        self._handles = []
        layers = model.model.layers
        for i in self.layer_indices:
            mlp = getattr(layers[i], "mlp", None)
            if mlp is None:
                raise SystemExit(f"layer {i} has no mlp module")
            self._handles.append(mlp.register_forward_pre_hook(self._make_hook(i)))

    def _make_hook(self, i: int):
        def hook(_module, inputs):
            x = inputs[0]
            self.latest[i] = (x.reshape(-1, x.shape[-1]) if x.dim() == 2 else x[:, -1, :]).detach()
        return hook

    def compare(self, oracle_batch: np.ndarray, n_rows: int) -> bool:
        """oracle_batch (B, L, d) float16 from OracleCatch.collect at the same
        step; True iff every registered layer's MLP input equals it."""
        ok = True
        for li, i in enumerate(self.layer_indices):
            if i not in self.latest:
                raise RuntimeError(f"mlp input check: layer {i} did not fire")
            x = self.latest[i]
            if x.shape[0] != n_rows:
                x = x.reshape(n_rows, -1, x.shape[-1])[:, -1, :]
            got = x.float().cpu().numpy().astype(np.float16)
            ok = ok and np.array_equal(got, oracle_batch[:, li, :])
        self.latest = {}
        return ok

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


def replay_batch(model, tap, normcatch: NormCatch, oracle: OracleCatch, input_ids, attention_mask,
                 logged: dict, row_seeds: np.ndarray, temperature: float,
                 forward_kwargs: dict | None = None, mlp_check: MLPInputCheck | None = None) -> dict:
    """The harvester's loop, step for step: p = softmax(logits / t); capture
    slots, h_a and the oracle from the forward that produced p; DRAW a token
    per row with that row's own generator (seeded as the harvester seeded
    it, advanced once per row per step, the last step included); record the
    draw, draw == logged on valid positions and the deterministic p
    diagnostics; feed the LOGGED token to running rows and the DRAWN token
    to rows beyond their logged length (the harvester's post-EOS inputs,
    which it sampled and later zeroed in storage). `logged` holds the
    parent arrays for these rows: tokens, lengths, slots, hidden, argmax,
    top_ids, top_p."""
    import torch

    fkw = dict(forward_kwargs or {})
    dev = input_ids.device
    B = int(input_ids.shape[0])
    tokens_logged = logged["tokens"]
    lengths_logged = np.asarray(logged["lengths"], dtype=np.int64)
    n_rec = int(lengths_logged.max())
    if n_rec < 1 or n_rec > tokens_logged.shape[1]:
        raise ValueError("inconsistent logged lengths")
    if len(row_seeds) != B:
        raise ValueError("one sampling seed per row is required")
    t = max(float(temperature), 1e-4)
    gens = []
    for s in row_seeds:
        g = torch.Generator(device=dev)
        g.manual_seed(int(s))
        gens.append(g)
    L = len(oracle.layer_indices)
    n_tap = logged["slots"].shape[2]
    oracle_out = None
    drawn_all = np.zeros((B, n_rec), np.int32)
    token_match = np.zeros((B, n_rec), bool)
    argmax_match = np.zeros((B, n_rec), bool)
    topp_maxabs = np.zeros((B, n_rec), np.float32)
    slot_match = np.zeros((B, n_rec, n_tap), bool)
    slot_overlap = np.zeros((B, n_rec, n_tap), np.float16)
    h_maxabs = np.zeros((B, n_rec), np.float32)
    h_absmax = np.zeros((B, n_rec), np.float32)
    mlp_ok = True
    rows_idx = np.arange(B)

    mask = attention_mask.clone()
    position_ids = (mask.long().cumsum(-1) - 1).clamp(min=0)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=mask, position_ids=position_ids,
                    use_cache=True, **fkw)
        cache = out.past_key_values
        logits = out.logits[:, -1]
        for a in range(n_rec):
            p = torch.softmax(logits.float() / t, dim=-1)
            s_now = tap.collect(B)                       # (B, L_tap, top)
            h_now = normcatch.collect(B)                 # (B, d_h) float16
            o_now = oracle.collect(B)                    # (B, L, d)
            if mlp_check is not None:
                mlp_ok = mlp_check.compare(o_now, B) and mlp_ok
            if oracle_out is None:
                oracle_out = np.zeros((B, n_rec, L, int(o_now.shape[-1])), np.float16)
            oracle_out[:, a] = o_now
            slot_match[:, a] = sets_equal_rows(s_now, logged["slots"][:, a])
            slot_overlap[:, a] = set_overlap_rows(s_now, logged["slots"][:, a]).astype(np.float16)
            diff = np.abs(h_now.astype(np.float32) - logged["hidden"][:, a].astype(np.float32))
            h_maxabs[:, a] = diff.max(-1)
            h_absmax[:, a] = np.abs(logged["hidden"][:, a].astype(np.float32)).max(-1)
            p_np = p.cpu().numpy()
            argmax_match[:, a] = p_np.argmax(-1) == logged["argmax"][:, a].astype(np.int64)
            ids = logged["top_ids"][:, a].astype(np.int64)                 # (B, top_m)
            p_at = p_np[rows_idx[:, None], ids]
            topp_maxabs[:, a] = np.abs(p_at - logged["top_p"][:, a].astype(np.float32)).max(-1)
            drawn = torch.empty(B, dtype=torch.long, device=dev)
            for b in range(B):
                drawn[b] = torch.multinomial(p[b], 1, generator=gens[b])[0]
            drawn_np = drawn.cpu().numpy().astype(np.int64)
            drawn_all[:, a] = drawn_np
            valid_a = a < lengths_logged
            token_match[:, a] = valid_a & (drawn_np == tokens_logged[:, a].astype(np.int64))
            if a == n_rec - 1:
                break
            feed = np.where(valid_a, tokens_logged[:, a].astype(np.int64), drawn_np)
            nxt = torch.as_tensor(feed, device=dev)
            mask = torch.cat([mask, torch.ones(B, 1, dtype=mask.dtype, device=mask.device)], dim=1)
            pos_next = (mask.long().sum(-1) - 1)[:, None]
            out = model(input_ids=nxt[:, None], attention_mask=mask, position_ids=pos_next,
                        past_key_values=cache, use_cache=True, **fkw)
            cache = out.past_key_values
            logits = out.logits[:, -1]
    arrays = finalize_replay({"oracle": oracle_out, "drawn": drawn_all, "token_match": token_match,
                              "argmax_match": argmax_match, "topp_maxabs": topp_maxabs,
                              "slot_match": slot_match, "slot_overlap": slot_overlap,
                              "h_maxabs": h_maxabs, "h_absmax_logged": h_absmax}, lengths_logged)
    arrays["mlp_input_ok"] = bool(mlp_ok)
    return arrays


def _sha_path(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git_tracked(p: Path) -> bool:
    """True when git says the file is tracked — and True on any failure to
    ask (fail CLOSED: a committed side-file is never rewritten by mistake)."""
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", str(p)], capture_output=True, text=True,
                           cwd=str(p.resolve().parent), timeout=10)
        return r.returncode == 0
    except Exception:
        return True


def check_out_dir(out_dir: Path, harvest_dir: Path) -> None:
    """The side-files' directory must be neither the harvest directory nor
    a directory holding another prefix's seed metas (every consumer refuses
    mixed prefixes, so such a write would poison that directory)."""
    if out_dir.resolve() == harvest_dir.resolve():
        raise SystemExit("--out-dir must not be the harvest directory (mixed prefixes are refused by every consumer)")
    if out_dir.exists():
        prefixes = {p.name.split("_s")[0] for p in out_dir.glob("*_s*.meta.json")}
        if prefixes - {ORACLE_PREFIX}:
            raise SystemExit(f"--out-dir {out_dir} holds metas of prefixes {sorted(prefixes)} — refusing to mix")


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    from .hf_specdec import PINNED_DATE, _assert_gpu_resident, _atomic_write_text, redact_args
    from ._preflight import preflight

    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", required=True, help="committed harvest directory (parent)")
    ap.add_argument("--out-dir", required=True, help="oracle side-file directory (NOT the harvest dir)")
    ap.add_argument("--layers", required=True, help="registered decoder-layer indices, comma-separated")
    ap.add_argument("--seeds", default=None, help="subset of the parent seeds (default: all)")
    ap.add_argument("--prompts", default=None, help="override the parent meta's prompts path (sha still checked)")
    ap.add_argument("--overwrite", action="store_true", help="rewrite an UNCOMMITTED side-file")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    args = ap.parse_args()

    harvest_dir = Path(args.harvest)
    out_dir = Path(args.out_dir)
    check_out_dir(out_dir, harvest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_files = verified_seed_files(harvest_dir)
    prefix = seed_files[0][0]["npz_file"].split("_s")[0]
    if prefix not in REGISTERED_LAYERS:
        raise SystemExit(f"harvest prefix {prefix!r} has no registered oracle layers")
    layers = tuple(int(x) for x in args.layers.split(","))
    if layers != REGISTERED_LAYERS[prefix]:
        raise SystemExit(f"--layers {list(layers)} are not the registered {list(REGISTERED_LAYERS[prefix])} for {prefix}")
    ref = seed_files[0][0]
    model_id = ref["model"]
    prompts_path = Path(args.prompts or ref["prompts"])
    if _sha_path(prompts_path) != ref["prompts_sha256"]:
        raise SystemExit("prompts file sha differs from the parent meta's — the batch composition would differ")
    if ref.get("row_seed_convention") != ROW_SEED_CONVENTION:
        raise SystemExit(f"parent row-seed convention {ref.get('row_seed_convention')!r} is not the one "
                         f"row_generator_seeds implements ({ROW_SEED_CONVENTION!r})")
    batch_size = int(ref["batch_size"])
    n_prompts = int(ref["n_prompts"])
    use_chat = bool(ref["chat_template_used"])
    temperature = float(ref.get("temperature", 1.0))
    wanted = None if args.seeds is None else {int(s) for s in args.seeds.split(",")}
    # IDENTICAL PATH is a version claim: assert the libraries and GPU the parent recorded
    for key, have in (("transformers_version", transformers.__version__), ("torch_version", torch.__version__)):
        if ref.get(key) is not None and str(ref[key]) != str(have):
            raise SystemExit(f"{key} {have} differs from the parent meta's {ref[key]} — not the identical path")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    if ref.get("gpu") is not None and gpu_name != ref["gpu"]:
        raise SystemExit(f"GPU {gpu_name!r} differs from the parent meta's {ref['gpu']!r} — not the identical path")
    try:
        import bitsandbytes
        bnb_version = getattr(bitsandbytes, "__version__", None)   # recorded; the parent metas do not carry it
    except Exception:
        bnb_version = None
    n_seeds = len(seed_files) if wanted is None else len([m for m, _ in seed_files if int(m["seed"]) in wanted])
    z0 = np.load(seed_files[0][1])
    T_ref = int(z0["tokens"].shape[1])
    d_hidden = int(z0["hidden"].shape[2])
    del z0
    side_bytes = n_seeds * n_prompts * T_ref * len(layers) * d_hidden * 2
    preflight_report = preflight(disk_path=out_dir.resolve().anchor or ".", force=args.skip_preflight,
                                 min_disk_free_gb=max(10.0, side_bytes / 1e9 + 5.0))

    tok = transformers.AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    if prefix == SHADOW_PREFIX:
        kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
        if ref["load_4bit"]:
            kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
        model = transformers.AutoModelForCausalLM.from_pretrained(model_id, **kwargs).eval()
        load_tag = "nf4-double-quant-bf16compute" if ref["load_4bit"] else "bf16"
        load_verified = None
    else:
        from .moe_telemetry import load_quantized_moe, verify_load_regime
        model, load_tag = load_quantized_moe(transformers, torch, model_id,
                                             bool(ref["load_4bit"]), bool(ref["bf16_routers"]))
        load_verified = verify_load_regime(model, bool(ref["load_4bit"]), bool(ref["bf16_routers"]),
                                           gate_regex=ref["gate_regex"])
    _assert_gpu_resident(model, "model", args.allow_cpu_offload)
    dev = model.device
    attn_impl = getattr(getattr(model, "config", None), "_attn_implementation", None)

    prompts = [json.loads(l)["prompt"] for l in prompts_path.read_text().splitlines() if l.strip()]
    prompts = prompts[:n_prompts]

    def encode_batch(batch: list[str]):
        if use_chat:
            texts = [tok.apply_chat_template([{"role": "user", "content": p}],
                                             add_generation_prompt=True, tokenize=False,
                                             date_string=PINNED_DATE) for p in batch]
            return tok(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        return tok(batch, return_tensors="pt", padding=True)

    norm_module = getattr(getattr(model, "model", None), "norm", None)
    if norm_module is None:
        raise SystemExit("expected a *ForCausalLM exposing .model.norm")
    import inspect
    fkw = {"logits_to_keep": 1} if "logits_to_keep" in inspect.signature(model.forward).parameters else {}

    if prefix == SHADOW_PREFIX:
        keep = {int(x) for x in ref["layers"].split(",")}
        tap = ShadowTap(model, ref["layer_regex"], keep, int(ref["n_slots"]), int(ref["top_n"]),
                        seed=int(ref["sketch_seed"]))
        if tap.layer_names != list(ref["layer_names"]):
            raise SystemExit("re-created ShadowTap does not match the parent meta's layers")
        logged_seeds = ref.get("sketch_layer_seeds")
        if isinstance(logged_seeds, dict) and \
                {n: int(tap.layer_seeds[n]) for n in tap.layer_names} != {k: int(v) for k, v in logged_seeds.items()}:
            raise SystemExit("re-created ShadowTap's sketch seeds differ from the parent meta's")
    else:
        from .moe_telemetry import RouterTap
        tap = RouterTap(model, ref["gate_regex"], int(ref["top_k"]))
        if tap.layer_names != list(ref["layer_names"]):
            raise SystemExit("re-created RouterTap does not match the parent meta's layers")
    normcatch = NormCatch(norm_module)
    oracle = OracleCatch(model, layers)
    print(f"[oracle] {prefix}: layers {list(layers)} -> {oracle.layer_names}; temperature {temperature}", flush=True)

    def _git(cmd):
        r = subprocess.run(["git", *cmd], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    def _git_commit() -> str:
        try:
            dirty = "-dirty" if _git(["status", "--porcelain", "--untracked-files=no"]) else ""
            return (_git(["rev-parse", "HEAD"]) or "unknown") + dirty
        except Exception:
            return "unknown"

    bounds = chunk_bounds(len(prompts), batch_size)
    for meta, npz_path in seed_files:
        seed = int(meta["seed"])
        if wanted is not None and seed not in wanted:
            continue
        out_npz = out_dir / f"{ORACLE_PREFIX}_s{seed}.npz"
        out_meta = out_dir / f"{ORACLE_PREFIX}_s{seed}.meta.json"
        if out_meta.exists() and _git_tracked(out_meta):
            m = json.loads(out_meta.read_text())
            if out_npz.exists() and m.get("npz_sha256") == _sha_path(out_npz) \
                    and m.get("parent_npz_sha256") == meta["npz_sha256"]:
                print(f"[seed {seed}] committed oracle exists (sha verified), skipping", flush=True)
                continue
            raise SystemExit(f"{out_meta} is COMMITTED evidence and its npz is missing or differs — never rewritten")
        if out_npz.exists() and out_meta.exists() and not args.overwrite:
            m = json.loads(out_meta.read_text())
            if m.get("npz_sha256") == _sha_path(out_npz) and m.get("parent_npz_sha256") == meta["npz_sha256"]:
                print(f"[seed {seed}] oracle exists (sha verified), skipping", flush=True)
                continue
            raise SystemExit(f"{out_npz} exists but does not match its meta; delete or --overwrite deliberately")
        z = np.load(npz_path)
        tokens_all, lengths_all = z["tokens"], z["lengths"].astype(np.int64)
        if int(tokens_all.shape[0]) != len(prompts):
            raise SystemExit(f"seed {seed}: {tokens_all.shape[0]} rows for {len(prompts)} prompts")
        row_seeds = row_generator_seeds(seed, len(prompts))
        chunks = []
        t0 = time.time()
        n_valid = 0
        n_tok = 0
        mlp_ok_all = True
        for bi, (s, e) in enumerate(bounds):
            enc = encode_batch(prompts[s:e]).to(dev)
            logged = {k: z[k][s:e] for k in ("tokens", "lengths", "slots", "hidden", "argmax", "top_ids", "top_p")}
            # the first batch of every seed certifies the capture point through the MLP pre-hook
            mlp_check = MLPInputCheck(model, layers) if bi == 0 else None
            res = replay_batch(model, tap, normcatch, oracle, enc["input_ids"], enc["attention_mask"],
                               logged, row_seeds[s:e], temperature, forward_kwargs=fkw, mlp_check=mlp_check)
            if mlp_check is not None:
                mlp_check.close()
                if not res["mlp_input_ok"]:
                    raise SystemExit(f"seed {seed}: the captured norm output is NOT the MLP input on the first batch")
            mlp_ok_all = mlp_ok_all and res["mlp_input_ok"]
            chunks.append(res)
            n_valid += int(lengths_all[s:e].sum())
            n_tok += int(res["token_match"].sum())
            print(f"[seed {seed}] {e}/{len(prompts)} prompts {time.time() - t0:.0f}s "
                  f"drawn-token match {n_tok / max(n_valid, 1):.4f} over {n_valid} positions", flush=True)
        arrays = {
            "oracle": _pad_cat([c["oracle"] for c in chunks], 0),
            "drawn": _pad_cat([c["drawn"] for c in chunks], 0),
            "token_match": _pad_cat([c["token_match"] for c in chunks], False),
            "argmax_match": _pad_cat([c["argmax_match"] for c in chunks], False),
            "topp_maxabs": _pad_cat([c["topp_maxabs"] for c in chunks], 0.0),
            "slot_match": _pad_cat([c["slot_match"] for c in chunks], False),
            "slot_overlap": _pad_cat([c["slot_overlap"] for c in chunks], 0),
            "h_maxabs": _pad_cat([c["h_maxabs"] for c in chunks], 0.0),
            "h_absmax_logged": _pad_cat([c["h_absmax_logged"] for c in chunks], 0.0),
            "lengths": lengths_all.astype(np.int32),
            "prompt_idx": z["prompt_idx"],
        }
        if arrays["oracle"].shape[1] != tokens_all.shape[1]:
            raise SystemExit(f"seed {seed}: replay recorded T {arrays['oracle'].shape[1]} vs parent T {tokens_all.shape[1]}")
        fid = fidelity_summary(arrays, lengths_all, tap.layer_names)
        np.savez(out_npz, **arrays)
        out_meta_d = {
            "kind": "oq19_oracle_replay",
            "npz_file": out_npz.name,
            "npz_sha256": _sha_path(out_npz),
            "parent_dir": str(harvest_dir),
            "parent_npz_file": meta["npz_file"],
            "parent_npz_sha256": meta["npz_sha256"],
            "parent_meta_sha256": _sha_path(harvest_dir / f"{prefix}_s{seed}.meta.json"),
            "seed": seed,
            "model": model_id,
            "target_load": load_tag,
            "load_regime_verified": load_verified,
            "attn_implementation": attn_impl,
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "bitsandbytes_version": bnb_version,
            "parent_versions": {k: ref.get(k) for k in ("torch_version", "transformers_version", "gpu")},
            "layers": list(layers),
            "layer_names": oracle.layer_names,
            "mlp_input_equals_norm_output_first_batch": bool(mlp_ok_all),
            "sketch_layer_names": tap.layer_names,
            "d": int(arrays["oracle"].shape[-1]),
            "n_rows": int(arrays["oracle"].shape[0]),
            "T": int(arrays["oracle"].shape[1]),
            "regime": ("REPLAY of the logged generations through the harvester's batched left-padded KV-cached "
                       "path (same prompt batches, same order, same forward kwargs, transformers / torch / GPU "
                       "asserted equal to the parent meta's, bitsandbytes recorded), the harvester's per-row "
                       "sampling generators re-seeded and drawn at every step; running rows fed the logged "
                       "token, finished rows the drawn token; oracle = post-attention-norm output at the "
                       "registered layers, last position per row (asserted to be the MLP input on the first batch)"),
            "temperature": temperature,
            "row_seed_convention": ref.get("row_seed_convention"),
            "batch_size": batch_size,
            "chat_template_used": use_chat,
            "date_string_pinned": PINNED_DATE if use_chat else None,
            "fidelity": fid,
            "preflight": preflight_report,
            "git_commit": _git_commit(),
            "args": redact_args(vars(args)),
            "runtime_s": round(time.time() - t0, 1),
            "gpu": gpu_name,
        }
        _atomic_write_text(out_meta, json.dumps(out_meta_d, indent=1))
        print(f"[seed {seed}] done: token match {fid['token_match_rate']:.4f}, argmax match "
              f"{fid['argmax_match_rate']:.4f}, overlap mean min {fid['slot_overlap_mean_min']:.4f}, exact min "
              f"{fid['slot_exact_match_rate_min']:.4f}, h relmax p50 {fid['h_relmax_percentiles']['50']:.2e} "
              f"p99 {fid['h_relmax_percentiles']['99']:.2e}, {out_meta_d['runtime_s']}s", flush=True)
    tap.close()
    normcatch.close()
    oracle.close()


if __name__ == "__main__":
    main()

"""OQ-16 STAGE-A actuator (STAGE-A FREEZE, BLUEPRINT 2026-09-04): the
SD^2-style injection of an anchor-state vector into the drafter's MLP
up-projection outputs, plus the training-row assembly for its adapter.

MECHANISM (SD^2 "merged", their public code src/models/llama.py
LlamaBlockMerged + src/model.py PrepLatentDeltas, read 2026-09-04): per
drafter layer l the MLP computes down(act(gate(x)) * (up(x) + delta_l));
delta = adapter(h) with adapter = LayerNorm(h_dim) -> U (h_dim x r) ->
V_l (r x d_ff) per layer, V zero-initialised (a no-op until trained).
SD^2's map is a single full-rank zero-initialised linear (h_dim x
d_ff*n_layers); the rank-r factorisation is this box's memory deviation
(pinned r = ADAPTER_RANK; disclosed at the freeze). The vector h is the
verifier's anchor state: TRUE h_a for the oracle arm (NON-DEPLOYABLE
ceiling — D-2-named "oracle_"), or a frozen CPU ridge reconstruction
h_hat for the deployable arms (sideband.recon.LiveReconstructor over the
STAGE-A export). One delta per block, computed at the anchor (after each
verify; the prefill anchor for block 1), applied to every drafted row of
the block, cleared before the verify forward.

Implemented as forward hooks on `draft.model.layers[l].mlp.up_proj`: the
drafter's weights stay frozen, the verifier and sideband.specdec are
untouched (D-1's bright line — draft-side q modification only).

BLOCK-BOUNDARY CONSISTENCY: on the KV-cached path the first draft feed
of a block is 1 token, or 2 after a full-accept block (the drafter never
saw the gamma-th drafted token), or the whole prompt on the very first
step. Training assigns rows to blocks by guide_block_per_row (row t
belongs to the block that emitted token t+1), so the hook applies the
CURRENT block's delta to the LAST fed row only and the PREVIOUS block's
delta (zero when none) to earlier rows — the same per-row assignment the
adapter was trained under.

torch is imported lazily (house rule: nothing in CI imports torch); the
numpy parts (assemble_prompt, hhat loading) are CPU-tested.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from ..recon import (
    anchor_positions_from_spans,
    block_token_spans,
    guide_block_per_row,
)

ADAPTER_RANK = 512
ADAPTER_LN_EPS = 1e-5
INJECT_ARMS = {"oracle_h": "h", "free_inject": "freetok", "tel_inject": "union"}


# ---------------------------------------------------------------------------
# training-row assembly (numpy; CPU-tested)
# ---------------------------------------------------------------------------

def assemble_prompt(prompt_ids: np.ndarray, gen_row: dict, byp: dict,
                    vectors: np.ndarray) -> dict:
    """One prompt's teacher-forcing rows from the run's sidecars.

    prompt_ids: (prompt_len,) the templated prompt ids (re-encoded; the
      caller binds prompt 0's sha to the run meta); gen_row: the gen.jsonl
      line (prompt_len, generated_ids); byp: the byproduct npz dict
      (accepted, anchor_pos, n_blocks); vectors: (n_blocks, h_dim) the
      per-block injection vectors (h or h_hat).
    Returns ids (L,), guide (L,) block index per input row (-1 = none),
    spans, and asserts the DATA CONTRACT: the recomputed anchor positions
    equal the logged anchor_pos and the emitted-token count matches."""
    prompt_len = int(gen_row["prompt_len"])
    if prompt_ids.shape != (prompt_len,):
        raise ValueError(f"prompt_len {prompt_len} != encoded {prompt_ids.shape}")
    gen_ids = np.asarray(gen_row["generated_ids"], dtype=np.int64)
    acc = np.asarray(byp["accepted"], dtype=np.int64)
    n_blocks = int(byp["n_blocks"])
    if acc.shape != (n_blocks,) or vectors.shape[0] != n_blocks:
        raise ValueError("accepted / vectors do not match n_blocks")
    spans = block_token_spans(prompt_len, acc)
    anchors = anchor_positions_from_spans(prompt_len, spans)
    logged = np.asarray(byp["anchor_pos"], dtype=np.int64)
    if not np.array_equal(anchors, logged):
        raise ValueError("DATA CONTRACT: recomputed anchor positions != logged "
                         f"anchor_pos (first mismatch at block "
                         f"{int(np.argmax(anchors != logged))})")
    n_emitted = int(spans[-1, 1]) - prompt_len + 1 if n_blocks else 0
    if gen_ids.shape[0] != n_emitted:
        raise ValueError(f"DATA CONTRACT: {gen_ids.shape[0]} generated ids != "
                         f"{n_emitted} emitted by the blocks")
    ids = np.concatenate([np.asarray(prompt_ids, dtype=np.int64), gen_ids])
    guide = guide_block_per_row(prompt_len, spans, ids.shape[0])
    return {"ids": ids, "guide": guide, "spans": spans, "anchors": anchors,
            "prompt_len": prompt_len, "n_blocks": n_blocks}


def load_hhat(hhat_dir: Path, export_summary: dict, stem: str, pid: int,
              arm: str) -> np.ndarray:
    """(n_blocks, h_dim) float16 -> float64 cross-fitted h_hat for one
    prompt, sha-verified against the committed export summary."""
    f = Path(hhat_dir) / stem / f"p{pid:03d}.npz"
    want = export_summary["hhat_sha256"].get(f"{stem}/{f.name}")
    if want is None:
        raise SystemExit(f"{f} is not listed in the export summary")
    got = hashlib.sha256(f.read_bytes()).hexdigest()
    if got != want:
        raise SystemExit(f"sha256 mismatch for {f}")
    z = np.load(f)
    return np.asarray(z[arm], dtype=np.float64)


def encode_prompt_ids(tok, prompt: str, use_chat: bool, pinned_date: str):
    """The arm runner's encode_prompt, verbatim (chat template + pinned
    date string) — the trainer must reproduce the runs' prompt ids."""
    if use_chat:
        return tok.apply_chat_template(
            [{"role": "user", "content": prompt}], add_generation_prompt=True,
            return_tensors="pt", date_string=pinned_date)
    return tok(prompt, return_tensors="pt").input_ids


def ids_sha(ids_row) -> str:
    return hashlib.sha256(json.dumps([int(x) for x in ids_row]).encode()).hexdigest()


# ---------------------------------------------------------------------------
# torch side (GPU box)
# ---------------------------------------------------------------------------

def build_adapter(h_dim: int, n_layers: int, d_ff: int, r: int = ADAPTER_RANK):
    """The pinned adapter as a torch Module (lazy import).
    forward(h: (..., h_dim)) -> (n_layers, ..., d_ff), float32."""
    import torch
    import torch.nn as nn

    class InjectAdapter(nn.Module):
        def __init__(self):
            super().__init__()
            self.norm = nn.LayerNorm(h_dim, eps=ADAPTER_LN_EPS)
            self.u = nn.Linear(h_dim, r, bias=False)
            self.v = nn.Parameter(torch.zeros(n_layers, r, d_ff))
            self.h_dim, self.r, self.n_layers, self.d_ff = h_dim, r, n_layers, d_ff

        def forward(self, h):
            g = self.u(self.norm(h.float()))
            return torch.einsum("...r,lrf->l...f", g, self.v)

        def numpy_params(self) -> dict:
            """In sideband.recon.adapter_forward_np's layout (u: h_dim x r)."""
            return {"ln_w": self.norm.weight.detach().float().cpu().numpy(),
                    "ln_b": self.norm.bias.detach().float().cpu().numpy(),
                    "u": self.u.weight.detach().float().cpu().numpy().T,
                    "v": self.v.detach().float().cpu().numpy()}

    return InjectAdapter()


def adapter_self_check(adapter, n: int = 64, seed: int = 0, tol: float = 1e-4) -> float:
    """The torch adapter vs the numpy reference on n random vectors
    (float32 torch vs float64 numpy; tol is a judgment-call bound on
    fp32 accumulation over h_dim x r x d_ff). Returns the max abs dev."""
    import torch
    from ..recon import adapter_forward_np
    p = adapter.numpy_params()
    rng = np.random.default_rng(seed)
    dev = 0.0
    for _ in range(n):
        h = rng.normal(0, 3, adapter.h_dim)
        want = adapter_forward_np(h, p["ln_w"], p["ln_b"], p["u"], p["v"],
                                  eps=ADAPTER_LN_EPS)
        with torch.no_grad():
            got = adapter(torch.tensor(h, dtype=torch.float32,
                                       device=adapter.v.device)).float().cpu().numpy()
        # relative to the OUTPUT magnitude (critic advisory: a bound scaled
        # by the weights alone can trip spuriously on trained adapters)
        scale = max(1.0, float(np.abs(want).max()))
        dev = max(dev, float(np.max(np.abs(got - want))) / scale)
    if dev > tol:
        raise RuntimeError(f"adapter self-check: torch vs numpy relative "
                           f"deviation {dev:.3e} > {tol}")
    return dev


class UpProjInjector:
    """Forward hooks on every drafter layer's mlp.up_proj. With no delta
    set the hooks return the output untouched (bit-identical to the
    unhooked model — the vanilla arm never installs them anyway).

    set_block(cur, prev): cur / prev are (n_layers, d_ff) tensors (prev
    None = zero). Per the block-boundary rule, a fed chunk of T rows gets
    prev (or zero) on rows :-1 and cur on the last row; T > 2 is only
    legal when prev is None (the prompt prefill). set_rows(per_row) sets
    an explicit (n_layers, T, d_ff) schedule (training)."""

    def __init__(self, draft_model):
        layers = draft_model.model.layers
        self.n_layers = len(layers)
        self.cur = None
        self.prev = None
        self.rows = None
        self.n_applied = 0
        self._handles = [layer.mlp.up_proj.register_forward_hook(self._hook(i))
                         for i, layer in enumerate(layers)]

    def _hook(self, i: int):
        def hook(_module, _inputs, out):
            if self.rows is not None:
                d = self.rows[i]
                if out.shape[0] != 1 or out.shape[1] != d.shape[0]:
                    raise RuntimeError("row schedule does not match the fed chunk")
                self.n_applied += 1
                return out + d.to(out.dtype)[None]
            if self.cur is None:
                return out
            T = out.shape[1]
            if T > 2 and self.prev is not None:
                raise RuntimeError("multi-row feed with a previous block set — "
                                   "the cached path never does this")
            add = out.new_zeros(out.shape[1:])            # (T, d_ff)
            add[-1] = self.cur[i].to(out.dtype)
            if self.prev is not None and T == 2:
                add[0] = self.prev[i].to(out.dtype)
            self.n_applied += 1
            return out + add[None]
        return hook

    def set_block(self, cur, prev=None) -> None:
        self.rows = None
        self.cur, self.prev = cur, prev

    def set_rows(self, per_row) -> None:
        self.cur = self.prev = None
        self.rows = per_row

    def clear(self) -> None:
        self.cur = self.prev = self.rows = None

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


class BlockInjector:
    """What spec_decode_prompt's k3.inject carries: turns an AnchorRead
    into the block's delta and drives the UpProjInjector. mode 'h' (the
    oracle arm) injects the read's TRUE h_a; otherwise `recon` is a
    LiveReconstructor over the exported weights for that arm."""

    def __init__(self, injector: UpProjInjector, adapter, mode: str,
                 recon=None, device=None, gamma: int = 4):
        import torch
        self.injector, self.adapter, self.mode, self.recon = injector, adapter, mode, recon
        self.device = device if device is not None else adapter.v.device
        self.prev = None
        self.n_blocks = 0
        self.gamma = int(gamma)          # draft forwards per block (fixed schedule)
        self._applied_at_start = 0
        self._torch = torch
        if mode != "h" and recon is None:
            raise ValueError("reconstruction arms need a LiveReconstructor")

    def vector(self, anchor) -> np.ndarray:
        if self.mode == "h":
            return np.asarray(anchor.h, dtype=np.float64)
        return self.recon.reconstruct(anchor.summaries, anchor.slots)

    def start_block(self, anchor) -> None:
        h = self._torch.tensor(self.vector(anchor), dtype=self._torch.float32,
                               device=self.device)
        with self._torch.no_grad():
            cur = self.adapter(h)                      # (n_layers, d_ff)
        self.injector.set_block(cur, self.prev)
        self.prev = cur
        self.n_blocks += 1
        self._applied_at_start = self.injector.n_applied

    def end_block(self) -> None:
        # every drafted row of the block passed through every layer's hook:
        # gamma draft forwards x n_layers applications, exactly (the fixed
        # schedule makes this an equality, asserted per block)
        applied = self.injector.n_applied - self._applied_at_start
        want = self.injector.n_layers * self.gamma
        if applied != want:
            raise RuntimeError(f"injector applied {applied} hook adds this block, "
                               f"expected {want} (= {self.injector.n_layers} "
                               f"layers x {self.gamma} draft forwards)")
        self.injector.clear()

    def reset(self) -> None:
        self.prev = None
        self.injector.clear()

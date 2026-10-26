"""Phase-3 probe machinery: data layer + trainers for the OQ-1/K-2 grid.

Implements the registered protocol (docs/BLUEPRINT.md Phase 3, 2026-08-30).
Pure-numpy pieces (label building, splits, label maps) are CI-tested; the
torch trainers run on the GPU box.

Conventions enforced here, single-sourced from sideband.harvest:
- block-start alignment: label(anchor a, offset j) = token at a + j - 1;
- pinned prompt split (idx % 7), recomputed from stored prompt_idx at load
  time with an integrity abort (rider R3);
- the LABEL RULE: concept ids 0..C-1 from glue_remap, glue AND unbucketed
  merged into class C (predicting glue is part of the task).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .glue import glue_remap, load_glue
from .harvest import label_index, split_of_prompt, verified_seed_files

SPLITS = ("train", "val", "test")


def merged_label_map(bucket_of_token, glue_bucket_ids) -> tuple[np.ndarray, int]:
    """(label_of_token, n_classes): concepts 0..C-1, glue/unbucketed -> C."""
    steer_map, _mask, C = glue_remap(bucket_of_token, glue_bucket_ids)
    return np.where(steer_map >= 0, steer_map, C).astype(np.int64), C + 1


def load_label_space(buckets_path: str | Path, glue_path: str | Path) -> tuple[np.ndarray, int]:
    """Load a committed (buckets, glue) pair with the sha binding enforced."""
    import hashlib

    data = json.loads(Path(buckets_path).read_text())
    n = int(data["n_tokens"])
    arr = np.full(n, -1, dtype=np.int64)
    for tok, b in data["bucket_of_token"].items():
        arr[int(tok)] = int(b)
    bsha = hashlib.sha256(Path(buckets_path).read_bytes()).hexdigest()
    glue_ids, _meta = load_glue(str(glue_path), expect_buckets_sha256=bsha)
    return merged_label_map(arr, glue_ids)


class HarvestData:
    """Concatenated S1 harvest across seeds. Lazy on the big arrays."""

    def __init__(self, harvest_dir: str | Path):
        self.dir = Path(harvest_dir)
        self._npzs = []
        self.npz_shas: dict[str, str] = {}
        self.metas: list[dict] = []
        tok_chunks, len_chunks, pidx_chunks = [], [], []
        for meta, npz_path in verified_seed_files(self.dir):
            self.npz_shas[meta["npz_file"]] = meta["npz_sha256"]
            self.metas.append(meta)
            z = np.load(npz_path)
            self._npzs.append(z)
            tok_chunks.append(z["tokens"])
            len_chunks.append(z["lengths"].astype(np.int64))
            pidx_chunks.append(z["prompt_idx"].astype(np.int64))
        self.ref_meta = self.metas[0]
        self._tmax = max(t.shape[1] for t in tok_chunks)
        self.tokens = np.concatenate([self._pad(t, 0) for t in tok_chunks])
        self.lengths = np.concatenate(len_chunks)
        self.prompt_idx = np.concatenate(pidx_chunks)
        self.n_rows = self.tokens.shape[0]
        self._cache: dict[str, np.ndarray] = {}

    def _pad(self, a: np.ndarray, fill) -> np.ndarray:
        if a.shape[1] == self._tmax:
            return a
        pad = np.full((a.shape[0], self._tmax - a.shape[1]) + a.shape[2:], fill, dtype=a.dtype)
        return np.concatenate([a, pad], axis=1)

    def array(self, key: str) -> np.ndarray:
        """Concatenated per-anchor array (rows padded to the common T)."""
        if key not in self._cache:
            fill = -1 if key == "slots" else 0
            self._cache[key] = np.concatenate([self._pad(z[key], fill) for z in self._npzs])
        return self._cache[key]

    def row_split(self) -> np.ndarray:
        """Split name per row, from stored prompt_idx (rider R3: recomputed,
        and a prompt may never map to two splits — impossible by construction
        since prompt_idx is the key; asserted anyway per registration)."""
        names = np.array([split_of_prompt(int(i)) for i in self.prompt_idx])
        for pid in np.unique(self.prompt_idx):
            got = set(names[self.prompt_idx == pid])
            if len(got) != 1:
                raise SystemExit(f"R3 split integrity: prompt {pid} in splits {got}")
        return names


def anchor_table(lengths: np.ndarray, offset: int, tmax: int) -> tuple[np.ndarray, np.ndarray]:
    """(row_idx, anchor_idx) for every anchor whose offset-j label exists."""
    rows, anchors = [], []
    for r, n in enumerate(lengths):
        hi = int(n) - (offset - 1)  # anchors 0..hi-1 have label_index < n
        if hi > 0:
            rows.append(np.full(hi, r, dtype=np.int64))
            anchors.append(np.arange(hi, dtype=np.int64))
    return np.concatenate(rows), np.concatenate(anchors)


def labels_for(tokens: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
               offset: int, label_of_token: np.ndarray,
               shuffle_shift: int = 0, lengths: np.ndarray | None = None) -> np.ndarray:
    """Labels at (row, anchor, offset). shuffle_shift != 0 is rider R2: the
    label INDEX is circularly shifted by +shift within each row's valid
    range, destroying alignment while preserving each row's marginals.
    Known sliver: rows of length 1 or exactly `shift` shift to themselves
    ((li+shift) % n == li) and stay truly aligned — harmless under R2's
    RELATIVE band (shuffled-(c) vs shuffled-(a)), recorded here."""
    li = np.array([label_index(int(a), offset) for a in anchors], dtype=np.int64)
    if shuffle_shift:
        if lengths is None:
            raise ValueError("shuffle_shift requires lengths")
        n = lengths[rows]
        li = (li + shuffle_shift) % n
    return label_of_token[tokens[rows, li]]


def slots_multi_hot(slots_rows: np.ndarray, n_slots: int) -> np.ndarray:
    """(N, L, top_n) -1-padded slot ids -> (N, L*n_slots) float32 multi-hot."""
    N, L, _ = slots_rows.shape
    out = np.zeros((N, L * n_slots), dtype=np.float32)
    for li in range(L):
        s = slots_rows[:, li, :]
        rows_rep = np.repeat(np.arange(N), s.shape[1])
        flat = s.ravel()
        keep = flat >= 0
        out[rows_rep[keep], li * n_slots + flat[keep]] = 1.0
    return out


# ---------------------------------------------------------------------------
# Feature blocks: batches are assembled lazily — the dense f32 design matrix
# for a (c)-at-k512 cell would be >4 GB and must never be materialized.
# ---------------------------------------------------------------------------

class DenseBlock:
    """A per-anchor array in its native (storage) dtype; f32 per batch."""

    def __init__(self, arr: np.ndarray):
        self.arr = arr

    @property
    def dim(self) -> int:
        return int(self.arr.shape[1])

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return self.arr[idx].astype(np.float32, copy=False)


class SlotsBlock:
    """Raw (N, L, top_n) -1-padded slot ids; multi-hot built per batch."""

    def __init__(self, slots: np.ndarray, n_slots: int):
        self.slots = slots
        self.n_slots = n_slots

    @property
    def dim(self) -> int:
        return int(self.slots.shape[1]) * self.n_slots

    def batch(self, idx: np.ndarray) -> np.ndarray:
        return slots_multi_hot(self.slots[idx], self.n_slots)


class PrefixTopicBlock:
    """Post-hoc diagnostic P1 (BLUEPRINT 2026-08-31): decoder-free
    prefix-topic features from tokens[row, :anchor] ONLY — strictly before
    the offset-1 token (label_index(a,1) == a), i.e. exactly the anchor
    information set. Per anchor: normalized k512-alphabet concept histogram
    incl. the merged glue class (511 = C+1 for the committed k512 space) +
    k16-alphabet full-prefix histogram (16) + k16 histograms of the last 16
    and last 64 prefix tokens (16+16) + log1p(prefix length) (1) = 560 dims
    for the committed alphabets (dim follows the loaded n512/n16).
    Everything here is computable by a runtime decoder from tokens it has
    already accepted; no telemetry."""

    def __init__(self, tokens: np.ndarray, rows: np.ndarray, anchors: np.ndarray,
                 map512: np.ndarray, n512: int, map16: np.ndarray, n16: int):
        self.tokens, self.rows, self.anchors = tokens, rows, anchors
        self.map512, self.n512 = map512, int(n512)
        self.map16, self.n16 = map16, int(n16)

    @property
    def dim(self) -> int:
        return self.n512 + 3 * self.n16 + 1

    def batch(self, idx: np.ndarray) -> np.ndarray:
        out = np.zeros((len(idx), self.dim), dtype=np.float32)
        for i, j in enumerate(idx):
            r = self.rows[j]
            a = int(self.anchors[j])
            pre = self.tokens[r, :a]
            if a > 0:
                c512 = self.map512[pre]
                c16 = self.map16[pre]
                o = 0
                out[i, o:o + self.n512] = np.bincount(c512, minlength=self.n512) / a
                o += self.n512
                out[i, o:o + self.n16] = np.bincount(c16, minlength=self.n16) / a
                o += self.n16
                for w in (16, 64):
                    win = c16[-w:]
                    out[i, o:o + self.n16] = np.bincount(win, minlength=self.n16) / len(win)
                    o += self.n16
            out[i, -1] = np.log1p(a)
        return out


def train_probe(blocks: list, labels: np.ndarray, split_of_anchor: np.ndarray,
                n_classes: int, capacity: str, seed: int, device: str = "cuda",
                epochs: int = 30, batch_size: int = 4096, lr: float = 3e-3,
                eval_batch: int = 16384, full_eval: bool = False,
                return_weights: bool = False) -> dict:
    """Train one probe cell; returns per-anchor test correctness + summary.

    blocks: list of DenseBlock/SlotsBlock — the feature SET is the caller's
    choice; identical optimizer budget per cell by construction (same
    epochs/batch/lr regardless of the feature set). Model selection: VAL
    accuracy at epoch granularity; TEST read once, after selection.
    """
    import torch

    y = labels.astype(np.int64)
    tr = split_of_anchor == "train"
    va = split_of_anchor == "val"
    te = split_of_anchor == "test"

    g = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    dev = torch.device(device if (device == "cpu" or torch.cuda.is_available()) else "cpu")

    def assemble(idx: np.ndarray) -> "torch.Tensor":
        x = np.concatenate([b.batch(idx) for b in blocks], axis=1)
        return torch.from_numpy(x).to(dev)

    d = sum(b.dim for b in blocks)
    if capacity == "linear":
        model = torch.nn.Linear(d, n_classes)
    elif capacity == "mlp256":
        model = torch.nn.Sequential(torch.nn.Linear(d, 256), torch.nn.ReLU(),
                                    torch.nn.Linear(256, n_classes))
    else:
        raise ValueError(f"unknown capacity {capacity!r}")
    model = model.to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)

    yt = torch.from_numpy(y)
    idx_tr = np.nonzero(tr)[0]

    def acc_on(mask: np.ndarray) -> tuple[float, np.ndarray]:
        idx = np.nonzero(mask)[0]
        correct = np.zeros(len(idx), dtype=bool)
        model.eval()
        with torch.no_grad():
            for s in range(0, len(idx), eval_batch):
                sl = idx[s: s + eval_batch]
                out = model(assemble(sl))
                correct[s: s + len(sl)] = (out.argmax(-1).cpu().numpy() == y[sl])
        return float(correct.mean()), correct

    best_val, best_state, best_epoch = -1.0, None, -1
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(len(idx_tr), generator=g).numpy()
        for s in range(0, len(idx_tr), batch_size):
            sl = idx_tr[perm[s: s + batch_size]]
            xb = assemble(sl)
            yb = yt[sl].to(dev)
            opt.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(model(xb), yb)
            loss.backward()
            opt.step()
        val_acc, _ = acc_on(va)
        if val_acc > best_val:
            best_val = val_acc
            best_epoch = epoch
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    test_acc, test_correct = acc_on(te)
    out = {
        "test_acc": test_acc,
        "val_acc_best": best_val,
        "best_epoch": best_epoch,
        "n_train": int(tr.sum()), "n_val": int(va.sum()), "n_test": int(te.sum()),
        "test_correct": test_correct,  # per-anchor, for the paired cluster bootstrap
    }
    if full_eval:
        # D2/D3 path (K-3 arc registration): per-anchor correctness and
        # softmax confidence on every split, computed AFTER training with
        # no_grad — the training trajectory and the default return values
        # are byte-identical to the full_eval=False path (asserted by
        # tests; the extra evals consume no generator randomness).
        def eval_full(mask: np.ndarray) -> dict:
            idx = np.nonzero(mask)[0]
            correct = np.zeros(len(idx), dtype=bool)
            pred = np.zeros(len(idx), dtype=np.int64)
            prob_max = np.zeros(len(idx), dtype=np.float64)
            model.eval()
            with torch.no_grad():
                for s in range(0, len(idx), eval_batch):
                    sl = idx[s: s + eval_batch]
                    logits = model(assemble(sl))
                    p = torch.softmax(logits.double(), dim=-1)
                    pm, pa = p.max(dim=-1)
                    pa = pa.cpu().numpy()
                    pred[s: s + len(sl)] = pa
                    prob_max[s: s + len(sl)] = pm.cpu().numpy()
                    correct[s: s + len(sl)] = (pa == y[sl])
            return {"idx": idx, "correct": correct, "pred": pred,
                    "prob_max": prob_max}
        out["full"] = {name: eval_full(mask)
                       for name, mask in (("train", tr), ("val", va), ("test", te))}
    if return_weights:
        # Stage-E export path (K-3 arc, clarification E1/E7): the selected
        # epoch's weights as numpy, read AFTER training with no effect on
        # the trajectory or the default return values (full_eval pattern;
        # consumes no generator randomness).
        out["weights"] = {k: v.detach().cpu().numpy().copy()
                          for k, v in model.state_dict().items()}
    return out

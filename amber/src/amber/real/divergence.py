"""Phase 1 (OQ-1): target-generated text, draft-replay divergence — resumable.

Two stages, both shard-atomic (same pattern as amber.real.capture):

1. `generate`: the TARGET (Llama-3.2-3B) continues each prompt greedily,
   batch=1 (no padding, no batching hazards — generation is the one place a
   left-pad bug would silently corrupt the CONTENT itself, so it is not
   risked; ~200 prompts x 256 tokens is minutes on a 3080 Ti with KV cache).
2. `rank`: for each generated sequence, ONE teacher-forced forward of the
   DRAFT (and one of the target, for a self-consistency check) yields per
   generated position: the true token's 1-based rank in the draft's stable
   order, the draft's log2-probability of the true token (AC-under-draft
   bound), the draft top-2 gap (near-tie budget), and whether the target's
   own teacher-forced argmax reproduces the token it generated (must be ~100%;
   a shortfall is a KV-cache-vs-forward kernel mismatch — recorded, not hidden).

Rank is computed on device over the FULL vocabulary (not a top-k dump): rank
= 1 + #{logits > l_true} + #{logits == l_true and index < true}, i.e. the
codec's own stable_order convention. Everything the ledger needs is then
tiny (a few ints per position), so the whole run fits in one npz per shard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import numpy as np

from .capture import (Arm, _load_tokenizer, atomic_savez, atomic_write_json, load_model,
                      provenance, shard_path)

TARGET = "meta-llama/Llama-3.2-3B"
DRAFT = "meta-llama/Llama-3.2-1B"
DEFAULT_OUT = Path("results") / "p1"
PROMPTS = Path("..") / "sideband" / "data" / "prompts.jsonl"


# ----------------------------------------------------------------------------
# pure helpers (tested without torch)
# ----------------------------------------------------------------------------

def stable_rank(logits: np.ndarray, true_tok: np.ndarray) -> np.ndarray:
    """1-based rank of true_tok[t] in row t under (value desc, index asc)."""
    logits = np.asarray(logits); true_tok = np.asarray(true_tok)
    lt = logits[np.arange(logits.shape[0]), true_tok][:, None]
    greater = (logits > lt).sum(axis=1)
    tie_before = ((logits == lt) & (np.arange(logits.shape[1])[None, :] < true_tok[:, None])).sum(axis=1)
    return (1 + greater + tie_before).astype(np.int64)


def shard_ok(path: Path, keys=("ranks",)) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path, allow_pickle=False) as z:
            return all(k in z for k in keys)
    except Exception:  # noqa: BLE001
        return False


def load_prompts(path: Path, n: int) -> list[dict]:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(rows) < n:
        raise ValueError(f"{path} has {len(rows)} prompts; need {n}")
    return rows[:n]


# ----------------------------------------------------------------------------
# stage 1: greedy generation with the target
# ----------------------------------------------------------------------------

def make_generator(model, tok, device: str, max_new: int) -> Callable[[list[int]], list[int]]:
    import torch

    eos = tok.eos_token_id

    @torch.inference_mode()
    def gen(prompt_ids: list[int]) -> list[int]:
        ids = torch.as_tensor([prompt_ids], dtype=torch.long, device=device)
        out = model.generate(ids, max_new_tokens=max_new, do_sample=False, num_beams=1,
                             eos_token_id=eos, pad_token_id=eos, use_cache=True)
        return out[0, len(prompt_ids):].tolist()
    return gen


def run_generate(prompts: list[dict], tok_encode: Callable[[str], list[int]], gen: Callable,
                 out_dir: Path, shard_size: int = 8, meta_extra: dict | None = None, log=print) -> dict:
    gdir = out_dir / "generate"; gdir.mkdir(parents=True, exist_ok=True)
    n = len(prompts); n_shards = (n + shard_size - 1) // shard_size
    meta_path = gdir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({"n_prompts": n, "shard_size": shard_size, **(meta_extra or {})}); meta.setdefault("shards", {})
    for s in range(n_shards):
        sp = shard_path(gdir, s)
        if shard_ok(sp, ("ids", "prompt_len", "row")):
            continue
        rows = list(range(s * shard_size, min(n, (s + 1) * shard_size)))
        t0 = time.perf_counter()
        seqs, plens = [], []
        for r in rows:
            p_ids = tok_encode(prompts[r]["prompt"])
            g_ids = gen(p_ids)
            seqs.append(np.asarray(p_ids + g_ids, dtype=np.int32)); plens.append(len(p_ids))
        L = max(len(x) for x in seqs)
        ids = np.full((len(rows), L), -1, dtype=np.int32)  # -1 = beyond end (ragged)
        for i, x in enumerate(seqs):
            ids[i, :len(x)] = x
        atomic_savez(sp, ids=ids, prompt_len=np.asarray(plens, np.int32), row=np.asarray(rows, np.int32))
        dt = time.perf_counter() - t0
        n_new = int(sum(len(x) for x in seqs) - sum(plens))
        meta["shards"][str(s)] = {"rows": [rows[0], rows[-1]], "seconds": dt, "new_tokens": n_new, "tok_per_s": n_new / dt}
        atomic_write_json(meta_path, meta)
        log(f"[generate] shard {s + 1}/{n_shards} {n_new} new tokens {dt:.1f}s ({n_new / dt:.1f} tok/s)")
    (gdir / "DONE").write_text("{}"); meta["done"] = True; atomic_write_json(meta_path, meta)
    return meta


def load_generated(out_dir: Path) -> list[tuple[int, np.ndarray, int]]:
    gdir = out_dir / "generate"
    meta = json.loads((gdir / "meta.json").read_text())
    if not (gdir / "DONE").exists():
        raise ValueError("generation incomplete")
    n_shards = (meta["n_prompts"] + meta["shard_size"] - 1) // meta["shard_size"]
    out = []
    for s in range(n_shards):
        with np.load(shard_path(gdir, s)) as z:
            for i, r in enumerate(z["row"]):
                ids = z["ids"][i]; ids = ids[ids >= 0]
                out.append((int(r), ids.astype(np.int64), int(z["prompt_len"][i])))
    return out


# ----------------------------------------------------------------------------
# stage 2: teacher-forced rank dumps
# ----------------------------------------------------------------------------

def make_scorer(model, device: str) -> Callable[[np.ndarray, int], dict]:
    """f(ids, prompt_len) -> per generated position: rank, log2q(true), gap,
    argmax-equals-true. Position t's logits predict token t+1; generated
    tokens are ids[prompt_len:], predicted from positions prompt_len-1 ..."""
    import torch

    @torch.inference_mode()
    def score(ids: np.ndarray, prompt_len: int) -> dict:
        x = torch.as_tensor(ids[None, :], dtype=torch.long, device=device)
        logits = model(input_ids=x, use_cache=False).logits[0].float()   # (L, V)
        pred = logits[prompt_len - 1:-1]                                  # predicts ids[prompt_len:]
        true = torch.as_tensor(ids[prompt_len:], dtype=torch.long, device=device)
        lt = pred.gather(1, true[:, None])
        greater = (pred > lt).sum(1)
        idx = torch.arange(pred.shape[1], device=device)[None, :]
        tie_before = ((pred == lt) & (idx < true[:, None])).sum(1)
        rank = 1 + greater + tie_before
        lsm = torch.log_softmax(pred, dim=1)
        logq = lsm.gather(1, true[:, None])[:, 0] / np.log(2.0)
        logqmax = lsm.max(dim=1).values / np.log(2.0)
        top2 = torch.topk(pred, 2, dim=1).values
        gap = top2[:, 0] - top2[:, 1]
        return {"rank": rank.to(torch.int32).cpu().numpy(), "log2q": logq.cpu().numpy().astype(np.float32),
                "log2qmax": logqmax.cpu().numpy().astype(np.float32),
                "gap": gap.cpu().numpy().astype(np.float32),
                "argmax_is_true": (rank == 1).cpu().numpy()}
    return score


def run_rank(seqs: list[tuple[int, np.ndarray, int]], scorer: Callable, out_dir: Path, name: str,
             shard_size: int = 8, meta_extra: dict | None = None, log=print) -> dict:
    rdir = out_dir / name; rdir.mkdir(parents=True, exist_ok=True)
    n = len(seqs); n_shards = (n + shard_size - 1) // shard_size
    meta_path = rdir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({"n_prompts": n, "shard_size": shard_size, **(meta_extra or {})}); meta.setdefault("shards", {})
    for s in range(n_shards):
        sp = shard_path(rdir, s)
        if shard_ok(sp, ("ranks", "log2q", "log2qmax", "gap", "row", "offsets")):
            continue
        t0 = time.perf_counter()
        ranks, log2q, log2qmax, gaps, rows, offsets = [], [], [], [], [], [0]
        for r, ids, plen in seqs[s * shard_size:(s + 1) * shard_size]:
            d = scorer(ids, plen)
            ranks.append(d["rank"]); log2q.append(d["log2q"]); log2qmax.append(d["log2qmax"]); gaps.append(d["gap"]); rows.append(r)
            offsets.append(offsets[-1] + len(d["rank"]))
        atomic_savez(sp, ranks=np.concatenate(ranks), log2q=np.concatenate(log2q), log2qmax=np.concatenate(log2qmax),
                     gap=np.concatenate(gaps), row=np.asarray(rows, np.int32), offsets=np.asarray(offsets, np.int64))
        dt = time.perf_counter() - t0
        meta["shards"][str(s)] = {"seconds": dt, "positions": int(offsets[-1])}
        atomic_write_json(meta_path, meta)
        log(f"[{name}] shard {s + 1}/{n_shards} {offsets[-1]} positions {dt:.1f}s")
    (rdir / "DONE").write_text("{}"); meta["done"] = True; atomic_write_json(meta_path, meta)
    return meta


def load_rank(out_dir: Path, name: str) -> dict:
    rdir = out_dir / name
    meta = json.loads((rdir / "meta.json").read_text())
    if not (rdir / "DONE").exists():
        raise ValueError(f"{name} incomplete")
    n_shards = (meta["n_prompts"] + meta["shard_size"] - 1) // meta["shard_size"]
    per_prompt = []
    for s in range(n_shards):
        with np.load(shard_path(rdir, s)) as z:
            off = z["offsets"]
            for i, r in enumerate(z["row"]):
                sl = slice(int(off[i]), int(off[i + 1]))
                per_prompt.append({"row": int(r), "rank": z["ranks"][sl], "log2q": z["log2q"][sl],
                                   "log2qmax": z["log2qmax"][sl], "gap": z["gap"][sl]})
    return {"meta": meta, "per_prompt": per_prompt}


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--target", default=TARGET); ap.add_argument("--draft", default=DRAFT)
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "fp32"])
    ap.add_argument("--prompts", default=str(PROMPTS)); ap.add_argument("--n-prompts", type=int, default=200)
    ap.add_argument("--max-new", type=int, default=256); ap.add_argument("--shard-size", type=int, default=8)
    ap.add_argument("stage", choices=["generate", "rank", "all"])
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    prompts = load_prompts(Path(a.prompts), a.n_prompts)
    atomic_write_json(out / "prompts.json", {"source": str(a.prompts), "n": a.n_prompts,
                      "sha256": hashlib.sha256(json.dumps(prompts, sort_keys=True).encode()).hexdigest(),
                      "prompts": prompts})
    tok = _load_tokenizer(a.target)
    bos = tok.bos_token_id
    encode = lambda s: [bos] + tok(s, add_special_tokens=False)["input_ids"]  # noqa: E731
    arm = Arm("gen", "cuda", a.dtype, "none", 1)

    if a.stage in ("generate", "all") and not (out / "generate" / "DONE").exists():
        t0 = time.perf_counter(); model = load_model(a.target, arm)
        print(f"[generate] target loaded in {time.perf_counter() - t0:.1f}s")
        run_generate(prompts, encode, make_generator(model, tok, "cuda", a.max_new), out, a.shard_size,
                     meta_extra={"target": a.target, "max_new": a.max_new, "dtype": a.dtype,
                                 "provenance": provenance(a.target, arm)})
        del model
        import torch, gc; gc.collect(); torch.cuda.empty_cache()
    if a.stage in ("rank", "all"):
        seqs = load_generated(out)
        for name, mid in (("draft", a.draft), ("target_selfcheck", a.target)):
            if (out / name / "DONE").exists():
                print(f"[{name}] already DONE"); continue
            t0 = time.perf_counter(); model = load_model(mid, arm)
            print(f"[{name}] {mid} loaded in {time.perf_counter() - t0:.1f}s")
            run_rank(seqs, make_scorer(model, "cuda"), out, name, a.shard_size,
                     meta_extra={"model": mid, "dtype": a.dtype, "provenance": provenance(mid, arm)})
            del model
            import torch, gc; gc.collect(); torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

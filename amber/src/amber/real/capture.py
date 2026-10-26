"""Phase 2 logit capture: teacher-forced top-k logit dumps of the DRAFT under
several numeric "arms" (device x dtype x quantization x batch), resumable.

Design choices, each one a hazard from the sibling repos' ledgers:

* **No padding at all.** Every sequence is exactly `seq_len` tokens (BOS +
  seq_len-1 corpus tokens), so batch composition can never change a row's
  visible prefix — the left-pad offset hazard (cross-research XB-3 / T1) is
  removed by construction rather than tested around. Batch size then changes
  ONLY kernel selection, which is the thing Phase 2 wants to measure.
* **One forward pass per sequence, all positions at once.** Teacher forcing
  gives every position's next-token logits in a single pass; no generation
  loop, no KV cache. Throughput is bounded by the forward, not by Python.
* **Top-k on device, then transfer.** Full logits are (batch, L, 128256)
  fp32 — 2.1 GB at batch 8 — and are never moved to host. We keep k=256
  values+indices per position (the codec needs ORDER of the top few; the
  census needs the top-2 gap and top-k membership).
* **Shard-atomic, resumable.** Each shard of sequences is written with a
  same-directory temp file + os.replace (tokenizer-lab io_utils H-1/H-2
  pattern); a rerun skips shards whose file exists and parses. A DONE marker
  closes the arm. Interrupting at any point loses at most one shard.
* **Offline-first model loading.** `local_files_only=True` first, network only
  if the snapshot is missing — the connection here is unreliable and the
  weights are already cached.
* **Provenance in every meta.json:** lockstep envprobe digest (libm/interp),
  torch/cuda/transformers versions, GPU name, the HF snapshot hash, the corpus
  sha256, per-shard wall time (so throughput is measured, never projected —
  lockstep F-8's lesson).

Usage:
    python -m amber.real.capture corpus  --text ../tokenizer-lab/data/mix_docs50_wiki50.txt
    python -m amber.real.capture run --arm cpu_fp32
    python -m amber.real.capture run --arm cuda_bf16_b1 --arm cuda_bf16_b8 ...
    python -m amber.real.capture status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

# Llama-3.2-1B-Instruct is the intended draft (tokenizer-matched to the cached
# Llama-3.1-8B target) but this box's HF token is NOT authorized for the gated
# Llama-3.2 repos (2026-08-29: "not in the authorized list"). TinyLlama-1.1B
# is a Llama-architecture stand-in for the hardware question Phase 2 asks;
# override with --model once access is granted (protocol records the model).
DEFAULT_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
INTENDED_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
DEFAULT_OUT = Path("results") / "p2"
SEQ_LEN = 512
TOPK = 256


# ----------------------------------------------------------------------------
# atomic I/O (tokenizer-lab io_utils pattern)
# ----------------------------------------------------------------------------

def atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def atomic_write_json(path: Path, obj) -> None:
    atomic_write_bytes(path, json.dumps(obj, indent=2, sort_keys=True).encode("utf-8"))


def atomic_savez(path: Path, **arrays) -> None:
    tmp = path.with_name(path.name + ".tmp.npz")
    np.savez(tmp, **arrays)
    os.replace(tmp, path)


# ----------------------------------------------------------------------------
# arms
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Arm:
    name: str
    device: str          # "cpu" | "cuda"
    dtype: str           # "fp32" | "bf16" | "fp16"
    quant: str           # "none" | "int8" | "nf4"
    batch: int
    repeat: int = 1      # run-to-run repeat index (same config, second load)


ARMS: dict[str, Arm] = {a.name: a for a in [
    Arm("cpu_fp32", "cpu", "fp32", "none", 1),
    Arm("cpu_fp32_rep", "cpu", "fp32", "none", 1, repeat=2),
    Arm("cuda_fp32_b1", "cuda", "fp32", "none", 1),
    Arm("cuda_fp32_b8", "cuda", "fp32", "none", 8),   # added post-census as the band-(c) discriminator
    Arm("cuda_bf16_b1", "cuda", "bf16", "none", 1),
    Arm("cuda_bf16_b1_rep", "cuda", "bf16", "none", 1, repeat=2),
    Arm("cuda_bf16_b8", "cuda", "bf16", "none", 8),
    Arm("cuda_fp16_b1", "cuda", "fp16", "none", 1),
    Arm("cuda_int8_b1", "cuda", "fp16", "int8", 1),
    Arm("cuda_nf4_b1", "cuda", "fp16", "nf4", 1),
]}
REFERENCE_ARM = "cpu_fp32"
DEFAULT_ARM_ORDER = list(ARMS)


# ----------------------------------------------------------------------------
# corpus
# ----------------------------------------------------------------------------

def make_windows(token_ids: np.ndarray, bos: int, seq_len: int, n_seqs: int, seed: int = 0) -> np.ndarray:
    """Non-overlapping windows of seq_len-1 tokens, BOS prepended, chosen by a
    seeded permutation so the sample is spread over the corpus. Deterministic."""
    token_ids = np.asarray(token_ids, dtype=np.int64)
    body = seq_len - 1
    n_windows = len(token_ids) // body
    if n_windows < n_seqs:
        raise ValueError(f"corpus has {n_windows} windows of {body} tokens; need {n_seqs}")
    order = np.random.default_rng(seed).permutation(n_windows)[:n_seqs]
    order.sort()  # keep corpus order for readability; selection is still seeded
    out = np.empty((n_seqs, seq_len), dtype=np.int32)
    for i, w in enumerate(order):
        out[i, 0] = bos
        out[i, 1:] = token_ids[w * body:(w + 1) * body]
    return out


def corpus_sha(tokens: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(tokens, dtype=np.int32).tobytes()).hexdigest()


def build_corpus(text_path: Path, out_dir: Path, model_id: str, seq_len: int, n_seqs: int, seed: int) -> Path:
    from transformers import AutoTokenizer  # lazy
    tok = _load_tokenizer(model_id)
    text = Path(text_path).read_text(encoding="utf-8", errors="replace")
    ids = np.asarray(tok(text, add_special_tokens=False)["input_ids"], dtype=np.int64)
    bos = tok.bos_token_id
    if bos is None:
        raise ValueError("tokenizer has no BOS token; refusing to build a corpus without one")
    tokens = make_windows(ids, bos, seq_len, n_seqs, seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "corpus.npz"
    atomic_savez(path, tokens=tokens)
    meta = {
        "model_id": model_id, "text_path": str(text_path),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "n_tokens_total": int(len(ids)), "seq_len": seq_len, "n_seqs": n_seqs, "seed": seed,
        "corpus_sha256": corpus_sha(tokens), "positions": int(tokens.shape[0] * tokens.shape[1]),
    }
    atomic_write_json(out_dir / "corpus.json", meta)
    return path


def load_corpus(out_dir: Path) -> tuple[np.ndarray, dict]:
    meta = json.loads((out_dir / "corpus.json").read_text())
    tokens = np.load(out_dir / "corpus.npz")["tokens"]
    if corpus_sha(tokens) != meta["corpus_sha256"]:
        raise ValueError("corpus.npz does not match corpus.json sha256 (partial write?)")
    return tokens, meta


# ----------------------------------------------------------------------------
# model loading (one loader, all arms — eot TP-10 rule: no second drifting path)
# ----------------------------------------------------------------------------

def _load_tokenizer(model_id: str):
    from transformers import AutoTokenizer
    try:
        return AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    except Exception:
        return AutoTokenizer.from_pretrained(model_id)


def _snapshot_hash(model_id: str) -> str | None:
    try:
        from transformers.utils.hub import cached_file
        p = Path(cached_file(model_id, "config.json", local_files_only=True))
        return p.parent.name if p.parent.parent.name == "snapshots" else None
    except Exception:
        return None


def load_model(model_id: str, arm: Arm):
    import torch
    from transformers import AutoModelForCausalLM
    dtype = {"fp32": torch.float32, "bf16": torch.bfloat16, "fp16": torch.float16}[arm.dtype]
    kw: dict = {"torch_dtype": dtype}
    if arm.quant != "none":
        if arm.device != "cuda":
            raise ValueError("int8/nf4 arms need CUDA (bitsandbytes)")
        from transformers import BitsAndBytesConfig
        if arm.quant == "int8":
            kw["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        elif arm.quant == "nf4":
            kw["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
        else:
            raise ValueError(f"unknown quant {arm.quant}")
        kw["device_map"] = {"": 0}
    for local in (True, False):
        try:
            model = AutoModelForCausalLM.from_pretrained(model_id, local_files_only=local, **kw)
            break
        except Exception as exc:  # noqa: BLE001
            if local:
                print(f"[capture] local snapshot unavailable ({type(exc).__name__}); trying network", file=sys.stderr)
                continue
            raise
    if arm.quant == "none":
        model = model.to(arm.device)
    model.eval()
    return model


def make_forward(model, device: str, topk: int) -> Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Return f(tokens[b, L]) -> (idx[b, L, k] int32, val[b, L, k] float32).
    Logits are upcast to fp32 before top-k so the dump's precision is the
    same across arms; only the MODEL's arithmetic differs."""
    import torch

    @torch.inference_mode()
    def forward(batch: np.ndarray):
        ids = torch.as_tensor(batch, dtype=torch.long, device=device)
        out = model(input_ids=ids, use_cache=False)
        logits = out.logits.float()
        val, idx = torch.topk(logits, topk, dim=-1, largest=True, sorted=True)
        return idx.to(torch.int32).cpu().numpy(), val.cpu().numpy()
    return forward


# ----------------------------------------------------------------------------
# resumable capture
# ----------------------------------------------------------------------------

def shard_path(arm_dir: Path, i: int) -> Path:
    return arm_dir / f"shard_{i:04d}.npz"


def shard_ok(path: Path, expect_rows: int, k: int) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path) as z:
            return z["idx"].shape[0] == expect_rows and z["idx"].shape[2] == k and z["val"].shape == z["idx"].shape
    except Exception:  # noqa: BLE001 - a corrupt shard is just "not done"
        return False


def iter_batches(rows: Iterable[int], batch: int):
    rows = list(rows)
    for i in range(0, len(rows), batch):
        yield rows[i:i + batch]


def run_arm(arm: Arm, tokens: np.ndarray, out_dir: Path, forward: Callable, topk: int = TOPK,
            shard_size: int = 8, meta_extra: dict | None = None, log=print) -> dict:
    """Capture every sequence for one arm, resuming from existing shards.
    `forward` is injected so tests can run without a model."""
    arm_dir = out_dir / arm.name
    arm_dir.mkdir(parents=True, exist_ok=True)
    n = tokens.shape[0]
    n_shards = (n + shard_size - 1) // shard_size
    meta_path = arm_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({"arm": asdict(arm), "topk": topk, "shard_size": shard_size, "n_seqs": n,
                 "seq_len": int(tokens.shape[1]), "corpus_sha256": corpus_sha(tokens),
                 **(meta_extra or {})})
    meta.setdefault("shards", {})
    done = 0
    for s in range(n_shards):
        rows = list(range(s * shard_size, min(n, (s + 1) * shard_size)))
        sp = shard_path(arm_dir, s)
        if shard_ok(sp, len(rows), topk):
            done += 1
            continue
        t0 = time.perf_counter()
        idx_parts, val_parts = [], []
        for b in iter_batches(rows, arm.batch):
            idx, val = forward(tokens[b])
            idx_parts.append(idx); val_parts.append(val)
        idx = np.concatenate(idx_parts, 0).astype(np.int32)
        val = np.concatenate(val_parts, 0).astype(np.float32)
        if not np.all(np.isfinite(val)):
            raise ValueError(f"non-finite logits in arm {arm.name} shard {s}; refusing to write")
        atomic_savez(sp, idx=idx, val=val, rows=np.asarray(rows, dtype=np.int32))
        dt = time.perf_counter() - t0
        meta["shards"][str(s)] = {"rows": [rows[0], rows[-1]], "seconds": dt,
                                  "positions_per_s": len(rows) * tokens.shape[1] / dt}
        atomic_write_json(meta_path, meta)
        done += 1
        log(f"[{arm.name}] shard {s + 1}/{n_shards} rows {rows[0]}-{rows[-1]} {dt:.1f}s "
            f"({len(rows) * tokens.shape[1] / dt:.0f} pos/s)")
    if done == n_shards:
        (arm_dir / "DONE").write_text(json.dumps({"finished_unix": int(time.time())}))
        meta["done"] = True
        atomic_write_json(meta_path, meta)
    return meta


def load_arm(out_dir: Path, arm_name: str, topk: int | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Concatenate an arm's shards -> (idx[N, k], val[N, k], meta) with N =
    n_seqs * seq_len (row-major over sequences then positions)."""
    arm_dir = out_dir / arm_name
    meta = json.loads((arm_dir / "meta.json").read_text())
    if not (arm_dir / "DONE").exists():
        raise ValueError(f"arm {arm_name} is not complete (no DONE marker)")
    n_shards = (meta["n_seqs"] + meta["shard_size"] - 1) // meta["shard_size"]
    idx_parts, val_parts = [], []
    for s in range(n_shards):
        with np.load(shard_path(arm_dir, s)) as z:
            idx_parts.append(z["idx"]); val_parts.append(z["val"])
    idx = np.concatenate(idx_parts, 0); val = np.concatenate(val_parts, 0)
    k = topk or idx.shape[2]
    return idx[:, :, :k].reshape(-1, k), val[:, :, :k].reshape(-1, k), meta


# ----------------------------------------------------------------------------
# provenance
# ----------------------------------------------------------------------------

def provenance(model_id: str, arm: Arm) -> dict:
    info: dict = {"model_id": model_id, "snapshot": _snapshot_hash(model_id),
                  "platform": platform.platform(), "python": sys.version.split()[0]}
    try:
        from lockstep.envprobe import fingerprint
        info["envprobe_digest"] = fingerprint()["digest"]
    except Exception:  # noqa: BLE001
        info["envprobe_digest"] = None
    try:
        import torch, transformers
        info.update({"torch": torch.__version__, "transformers": transformers.__version__,
                     "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
                     "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                     "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                     "cpu_threads": torch.get_num_threads()})
        if arm.quant != "none":
            import bitsandbytes
            info["bitsandbytes"] = bitsandbytes.__version__
    except Exception as exc:  # noqa: BLE001
        info["torch_error"] = repr(exc)
    return info


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def cmd_corpus(a):
    p = build_corpus(Path(a.text), Path(a.out), a.model, a.seq_len, a.n_seqs, a.seed)
    print(f"[corpus] wrote {p} ({a.n_seqs} x {a.seq_len} tokens)")


def cmd_run(a):
    out = Path(a.out)
    tokens, cmeta = load_corpus(out)
    for name in a.arm:
        arm = ARMS[name]
        if (out / name / "DONE").exists() and not a.force:
            print(f"[{name}] already DONE, skipping"); continue
        if arm.device == "cuda":
            import torch
            if not torch.cuda.is_available():
                print(f"[{name}] CUDA unavailable, skipping"); continue
        t0 = time.perf_counter()
        model = load_model(a.model, arm)
        load_s = time.perf_counter() - t0
        print(f"[{name}] model loaded in {load_s:.1f}s")
        fwd = make_forward(model, arm.device, a.topk)
        run_arm(arm, tokens, out, fwd, topk=a.topk, shard_size=a.shard_size,
                meta_extra={"provenance": provenance(a.model, arm), "model_load_seconds": load_s})
        del model, fwd
        import gc; gc.collect()
        try:
            import torch; torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass


def cmd_status(a):
    out = Path(a.out)
    if not (out / "corpus.json").exists():
        print("no corpus yet"); return
    tokens, cmeta = load_corpus(out)
    print(f"corpus: {tokens.shape} sha {cmeta['corpus_sha256'][:12]}")
    for name in DEFAULT_ARM_ORDER:
        d = out / name
        if not d.exists():
            print(f"  {name:18s} -"); continue
        meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        n_sh = (meta.get("n_seqs", 0) + meta.get("shard_size", 1) - 1) // max(1, meta.get("shard_size", 1))
        done = sum(shard_ok(shard_path(d, s), min(meta.get("shard_size", 0), meta.get("n_seqs", 0) - s * meta.get("shard_size", 0)), meta.get("topk", TOPK)) for s in range(n_sh))
        rate = np.mean([v["positions_per_s"] for v in meta.get("shards", {}).values()]) if meta.get("shards") else float("nan")
        print(f"  {name:18s} {done}/{n_sh} shards {'DONE' if (d / 'DONE').exists() else ''} ~{rate:.0f} pos/s")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("corpus"); c.add_argument("--text", required=True)
    c.add_argument("--seq-len", type=int, default=SEQ_LEN); c.add_argument("--n-seqs", type=int, default=96)
    c.add_argument("--seed", type=int, default=0); c.set_defaults(fn=cmd_corpus)
    r = sub.add_parser("run"); r.add_argument("--arm", action="append", choices=list(ARMS), required=True)
    r.add_argument("--topk", type=int, default=TOPK); r.add_argument("--shard-size", type=int, default=8)
    r.add_argument("--force", action="store_true"); r.set_defaults(fn=cmd_run)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    a.fn(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

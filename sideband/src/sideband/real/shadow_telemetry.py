"""Phase-2 S1 harvester: shadow weight-slot telemetry from an INTACT model.

GPU box. Per DECISIONS D-1 (and its 2026-08-30 compute-tier scope note):
never corrupt the model to harvest telemetry. Hook chosen down_proj layers,
leave the computation untouched, and compute the sketch a hypothetical
activation-sparse fetch-on-demand device WOULD have emitted:

    importance_j = |a_j| * ||W[:, j]||        (input unit j's pull on output)
    telemetry    = sorted unique slots of the top-N units (HashSketch)

The registered protocol lives in docs/BLUEPRINT.md Phase 2 (pre-registered
2026-08-30). Load-bearing conventions:

- BLOCK-START ALIGNMENT (sideband.harvest.label_index): anchor a stores
  telemetry captured DURING the forward that produced p_a, free-information
  summaries of p_a (exact bucket masses in ALL FOUR committed spaces
  k=16/32/64/512, entropy, argmax, top-m ids+probs — Phase-3 label spaces
  are restricted to spaces whose exact p_a masses are logged), and the
  OQ-6 reference feature h_a (the final-norm hidden state that produced
  p_a — the SD^2 comparison feature; observability-violating, never a
  deployable source; NOT an information bound on mid-layer taps at
  offsets >= 2). The label at offset j is token x_{a+j-1}: offset 1 is
  the token sampled from p_a itself; K-2 reads offsets >= 2.
- Generation regime: harvest_freq's regime parameters (target-only
  sampling, NF4, chat template with PINNED_DATE, temperature 1.0, per-row
  EOS-set truncation) — the sampling LAW matches gen_freq but the RNG
  regime does not (per-row generators vs global manual_seed+generate), so
  trajectories differ from gen_freq's at the same seed by design. Batched
  left-padded KV-cached decoding with explicit position ids.
- Per-row sampling generators are seeded from
  np.random.SeedSequence(seed).spawn(n_prompts)[prompt_idx] so batching
  cannot couple rows (D-6 spirit). CUDA sampling is not bitwise
  deterministic across boxes; the committed meta binds each npz by sha256
  (harvest_freq precedent).

Output per seed: <out-dir>/shadow_s{S}.npz (gitignored raw arrays; zeroed /
-1-filled beyond each row's length) + committed shadow_s{S}.meta.json.

Usage (GPU box):
    python -m sideband.real.shadow_telemetry \
        --model meta-llama/Llama-3.1-8B-Instruct --load-4bit \
        --prompts data/prompts.jsonl --n-prompts 210 --max-new 256 \
        --seeds 0,1,2,3,4,5,6,7 \
        --out-dir results/real/harvest_shadow
    (bucket spaces default to the four committed results/real/buckets_k*.json)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import zlib
from pathlib import Path

import numpy as np

from ..harvest import GAMMA_DEFAULT, total_pairs
from ..sketch import HashSketch
from . import require_real_deps


def _linear_col_norms(module):
    """Column norms ||W[:, j]|| as a float32 tensor on the module's device.

    bitsandbytes Linear4bit stores packed uint8 in .weight — norms on the raw
    tensor would be garbage. Dequantize first (the registered protocol says
    norms are taken on DEQUANTIZED weights)."""
    import torch

    W = module.weight
    if W.__class__.__name__ == "Params4bit":
        from bitsandbytes.functional import dequantize_4bit

        with torch.no_grad():
            Wd = dequantize_4bit(W.data, W.quant_state)
        norms = Wd.float().norm(dim=0)
    else:
        norms = W.detach().float().norm(dim=0)
    # Fail-fast on any transposed/wrong-shape dequant: norms must be per
    # INPUT unit (the activation dimension the importance multiplies).
    if int(norms.shape[0]) != int(module.in_features):
        raise RuntimeError(f"column norms shape {tuple(norms.shape)} != in_features {module.in_features}")
    return norms


class ShadowTap:
    """Forward-pre hooks on regex-matched Linear layers.

    Scores importance on-GPU per batch row (last position only — real for
    every row under LEFT padding), takes the top-N units, and maps them
    through the layer's HashSketch slot table. collect() returns the sorted
    unique slot ids per (row, layer), -1-padded to top_n — equivalent to
    HashSketch.slots_for on the same importance vector whenever top-N scores
    are tie-free (exact ties at the rank boundary may resolve differently
    than numpy's index-order rule; measure-zero for real activations, and
    the equivalence test uses tie-free data).
    """

    def __init__(self, model, layer_regex: str, keep_layer_indices, n_slots: int,
                 top_n: int, seed: int = 0):
        import torch

        self.top_n = top_n
        self.n_slots = n_slots
        self.latest: dict = {}
        self._handles = []
        pattern = re.compile(layer_regex)
        matched = [(n, m) for n, m in model.named_modules() if pattern.search(n)]
        if keep_layer_indices is not None:
            matched = [nm for i, nm in enumerate(matched) if i in keep_layer_indices]
        if not matched:
            raise ValueError(f"no modules matched {layer_regex!r} (after --layers filter)")
        self.layer_names = [n for n, _ in matched]
        self.sketches: dict[str, HashSketch] = {}
        self.layer_seeds: dict[str, int] = {}
        self._col_norms = {}
        self._slot_of = {}
        for name, module in matched:
            norms = _linear_col_norms(module)
            d_in = int(norms.shape[0])
            # Stable per-layer seed: crc32, NOT Python hash() (hash() is
            # randomized per process and would silently change the sketch).
            layer_seed = seed + zlib.crc32(name.encode()) % 100_000
            self.layer_seeds[name] = layer_seed
            sk = HashSketch(d_in, n_slots, seed=layer_seed)
            self.sketches[name] = sk
            self._col_norms[name] = norms
            self._slot_of[name] = torch.from_numpy(sk.slot_of_unit).to(norms.device)
            self._handles.append(module.register_forward_pre_hook(self._make_hook(name)))

    def _make_hook(self, name: str):
        import torch

        def hook(_module, inputs):
            a = inputs[0]
            imp = a[:, -1, :].float().abs() * self._col_norms[name]  # (B, d_in)
            k = min(self.top_n, imp.shape[-1])
            top = torch.topk(imp, k=k, dim=-1).indices  # (B, k) unit ids
            self.latest[name] = self._slot_of[name][top]  # (B, k) slot ids

        return hook

    def collect(self, n_rows: int) -> np.ndarray:
        """(n_rows, n_layers, top_n) int16 sorted-unique slot ids, -1 pad.
        Clears captured state; refuses if a tapped layer did not fire."""
        out = np.full((n_rows, len(self.layer_names), self.top_n), -1, dtype=np.int16)
        for li, name in enumerate(self.layer_names):
            if name not in self.latest:
                raise RuntimeError(f"tapped layer {name} did not fire since last collect()")
            raw = self.latest[name].cpu().numpy()
            if raw.shape[0] != n_rows:
                raise RuntimeError(f"{name}: captured {raw.shape[0]} rows, expected {n_rows}")
            for b in range(n_rows):
                u = np.unique(raw[b])
                out[b, li, : len(u)] = u.astype(np.int16)
        self.latest = {}
        return out

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []


class NormCatch:
    """Captures the final-norm output row that produces each anchor's p_a —
    the OQ-6 reference feature (observability-violating; never a deployable
    source; NOT an information bound on mid-layer taps at offsets >= 2)."""

    def __init__(self, norm_module):
        self.latest = None
        self._handle = norm_module.register_forward_hook(self._hook)

    def _hook(self, _module, _inputs, output):
        self.latest = output[:, -1, :].detach()

    def collect(self, n_rows: int) -> np.ndarray:
        if self.latest is None:
            raise RuntimeError("norm hook did not fire since last collect()")
        h = self.latest.float().cpu().numpy().astype(np.float16)
        if h.shape[0] != n_rows:
            raise RuntimeError(f"norm hook captured {h.shape[0]} rows, expected {n_rows}")
        self.latest = None
        return h

    def close(self) -> None:
        self._handle.remove()


def row_generator_seeds(seed: int, n_prompts: int) -> np.ndarray:
    """One 63-bit sampling seed per prompt row, from the repo's spawn
    convention: SeedSequence(seed).spawn(n_prompts)[i]."""
    children = np.random.SeedSequence(seed).spawn(n_prompts)
    return np.array([int(c.generate_state(1, np.uint64)[0] % (2**63 - 1)) for c in children],
                    dtype=np.int64)


def harvest_batch(model, tap: ShadowTap, normcatch: NormCatch, input_ids, attention_mask,
                  row_seeds, eos_set: set[int], max_new: int, temperature: float,
                  bucket_spaces: dict, top_m: int = 32, forward_kwargs: dict | None = None):
    """Batched left-padded KV-cached target-only sampling with per-anchor
    capture under the block-start alignment. Returns dict of numpy arrays
    [B, T, ...] (T = anchors actually recorded) + per-row lengths + the
    per-row EOS `finished` flags.

    bucket_spaces: {name: full-coverage int64 torch tensor (vocab,)} on the
    model device — one exact p_a mass vector is logged per space (key
    "mass{name}"). row_seeds: one sampling seed per row (absolute-prompt
    convention — batching must not change any row's stream)."""
    import torch

    if max_new < 1:
        raise ValueError("max_new must be >= 1")
    fkw = dict(forward_kwargs or {})
    dev = input_ids.device
    B = int(input_ids.shape[0])
    t = max(temperature, 1e-4)
    n_buckets = {name: int(bt.max().item()) + 1 for name, bt in bucket_spaces.items()}
    L = len(tap.layer_names)

    gens = []
    for s in row_seeds:
        g = torch.Generator(device=dev)
        g.manual_seed(int(s))
        gens.append(g)

    tokens = np.zeros((B, max_new), np.int32)
    entropy = np.zeros((B, max_new), np.float32)
    argmax = np.zeros((B, max_new), np.int32)
    top_ids = np.zeros((B, max_new, top_m), np.int32)
    top_p = np.zeros((B, max_new, top_m), np.float16)
    masses = {name: np.zeros((B, max_new, n), np.float16) for name, n in n_buckets.items()}
    slots = np.full((B, max_new, L, tap.top_n), -1, np.int16)
    hidden = None  # allocated on first anchor (hidden size not known here)
    lengths = np.zeros(B, np.int32)
    finished = np.zeros(B, bool)

    mask = attention_mask.clone()
    position_ids = (mask.long().cumsum(-1) - 1).clamp(min=0)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=mask, position_ids=position_ids,
                    use_cache=True, **fkw)
        cache = out.past_key_values
        logits = out.logits[:, -1]
        a = -1
        for a in range(max_new):
            p = torch.softmax(logits.float() / t, dim=-1)  # (B, V)
            slots[:, a] = tap.collect(B)
            h = normcatch.collect(B)
            if hidden is None:
                hidden = np.zeros((B, max_new, h.shape[1]), np.float16)
            hidden[:, a] = h
            entropy[:, a] = (-torch.special.xlogy(p, p).sum(-1)).cpu().numpy()
            argmax[:, a] = p.argmax(-1).cpu().numpy()
            tp = torch.topk(p, k=min(top_m, p.shape[-1]), dim=-1)
            top_ids[:, a, : tp.indices.shape[-1]] = tp.indices.cpu().numpy()
            top_p[:, a, : tp.values.shape[-1]] = tp.values.cpu().numpy().astype(np.float16)
            for name, bt in bucket_spaces.items():
                m = torch.zeros(B, n_buckets[name], device=dev).scatter_add_(1, bt.expand(B, -1), p)
                masses[name][:, a] = m.cpu().numpy().astype(np.float16)

            nxt = torch.empty(B, dtype=torch.long, device=dev)
            for b in range(B):
                nxt[b] = torch.multinomial(p[b], 1, generator=gens[b])[0]
            tokens[:, a] = nxt.cpu().numpy()
            for b in range(B):
                if not finished[b] and int(nxt[b]) in eos_set:
                    finished[b] = True
                    lengths[b] = a + 1  # EOS included, harvest_freq precedent
            if bool(finished.all()) or a == max_new - 1:
                break

            mask = torch.cat([mask, torch.ones(B, 1, dtype=mask.dtype, device=dev)], dim=1)
            pos_next = (mask.long().sum(-1) - 1)[:, None]
            out = model(input_ids=nxt[:, None], attention_mask=mask, position_ids=pos_next,
                        past_key_values=cache, use_cache=True, **fkw)
            cache = out.past_key_values
            logits = out.logits[:, -1]

    n_rec = a + 1
    lengths[~finished] = n_rec
    # Hygiene: nothing beyond a row's length is data — zero it so accidental
    # consumers can't silently read post-EOS garbage (lengths is the law).
    for b in range(B):
        n = int(lengths[b])
        tokens[b, n:] = 0
        entropy[b, n:] = 0.0
        argmax[b, n:] = 0
        top_ids[b, n:] = 0
        top_p[b, n:] = 0
        for name in masses:
            masses[name][b, n:] = 0
        slots[b, n:] = -1
        hidden[b, n:] = 0
    out = {
        "tokens": tokens[:, :n_rec],
        "entropy": entropy[:, :n_rec],
        "argmax": argmax[:, :n_rec],
        "top_ids": top_ids[:, :n_rec],
        "top_p": top_p[:, :n_rec],
        "slots": slots[:, :n_rec],
        "hidden": hidden[:, :n_rec],
        "lengths": lengths,
        "finished": finished,
    }
    for name in masses:
        out[f"mass{name}"] = masses[name][:, :n_rec]
    return out


def _pad_cat(chunks: list[np.ndarray], fill) -> np.ndarray:
    """Concatenate batch chunks along rows, padding dim 1 (anchors) to the max."""
    tmax = max(c.shape[1] for c in chunks)
    out = []
    for c in chunks:
        if c.shape[1] < tmax:
            pad_shape = (c.shape[0], tmax - c.shape[1]) + c.shape[2:]
            c = np.concatenate([c, np.full(pad_shape, fill, dtype=c.dtype)], axis=1)
        out.append(c)
    return np.concatenate(out, axis=0)


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    from .hf_specdec import (PINNED_DATE, _assert_gpu_resident, _atomic_write_text,
                             load_buckets, redact_args)

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--layer-regex", default=r"mlp\.down_proj$")
    ap.add_argument("--layers", default="7,15,23,31",
                    help="comma indices among regex matches (= layer depths)")
    ap.add_argument("--n-slots", type=int, default=512)
    ap.add_argument("--top-n", type=int, default=32)
    ap.add_argument("--sketch-seed", type=int, default=0)
    ap.add_argument("--prompts", required=True, help="jsonl with a 'prompt' field")
    ap.add_argument("--n-prompts", type=int, default=210)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-m", type=int, default=32)
    ap.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--buckets16", default="results/real/buckets_k16.json")
    ap.add_argument("--buckets32", default="results/real/buckets_k32.json")
    ap.add_argument("--buckets64", default="results/real/buckets_k64.json")
    ap.add_argument("--buckets512", default="results/real/buckets_k512.json")
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--no-chat-template", action="store_true")
    ap.add_argument("--out-dir", default="results/real/harvest_shadow")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--allow-cpu-offload", action="store_true")
    args = ap.parse_args()

    from ._preflight import preflight

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preflight_report = preflight(disk_path=out_dir.resolve().anchor or ".",
                                 force=args.skip_preflight)

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    use_chat = (not args.no_chat_template) and tok.chat_template is not None
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    kwargs: dict = {"device_map": "auto", "torch_dtype": torch.bfloat16}
    if args.load_4bit:
        kwargs["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    model = transformers.AutoModelForCausalLM.from_pretrained(args.model, **kwargs).eval()
    _assert_gpu_resident(model, "model", args.allow_cpu_offload)
    dev = model.device
    vocab = int(model.config.vocab_size)

    bucket_paths = {"16": args.buckets16, "32": args.buckets32,
                    "64": args.buckets64, "512": args.buckets512}
    bucket_spaces = {}
    for name, path in bucket_paths.items():
        arr = load_buckets(path, vocab, expect_model=args.model)
        if (arr < 0).any():
            raise SystemExit(f"buckets{name} does not cover the full vocab; mass logging requires full coverage")
        bucket_spaces[name] = torch.from_numpy(arr).to(dev)

    prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    prompts = prompts[: args.n_prompts]

    def encode_batch(batch: list[str]):
        if use_chat:
            texts = [tok.apply_chat_template([{"role": "user", "content": p}],
                                             add_generation_prompt=True, tokenize=False,
                                             date_string=PINNED_DATE) for p in batch]
            return tok(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        return tok(batch, return_tensors="pt", padding=True)

    eos = model.config.eos_token_id
    eos_set = set(eos) if isinstance(eos, (list, tuple)) else {eos}

    norm_module = getattr(getattr(model, "model", None), "norm", None)
    if norm_module is None:
        raise SystemExit("expected a LlamaForCausalLM-shaped model exposing .model.norm")

    import inspect

    fkw = {"logits_to_keep": 1} if "logits_to_keep" in inspect.signature(model.forward).parameters else {}

    tap = ShadowTap(model, args.layer_regex, {int(x) for x in args.layers.split(",")} if args.layers else None,
                    args.n_slots, args.top_n, seed=args.sketch_seed)
    normcatch = NormCatch(norm_module)
    print(f"[tap] layers: {tap.layer_names}", flush=True)

    def _git(cmd):
        import subprocess

        r = subprocess.run(["git", *cmd], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parent, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    def _git_commit() -> str:
        try:
            dirty = "-dirty" if _git(["status", "--porcelain"]) else ""
            return (_git(["rev-parse", "HEAD"]) or "unknown") + dirty
        except Exception:
            return "unknown"

    def _sha(p: str) -> str:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    seeds = [int(s) for s in args.seeds.split(",")]
    grand_pairs = 0
    try:
        for seed in seeds:
            npz_path = out_dir / f"shadow_s{seed}.npz"
            meta_path = out_dir / f"shadow_s{seed}.meta.json"
            if npz_path.exists() and meta_path.exists() and not args.overwrite:
                meta = json.loads(meta_path.read_text())
                if meta.get("npz_sha256") == _sha(str(npz_path)):
                    grand_pairs += int(meta["n_pairs"])
                    print(f"[seed {seed}] exists (sha verified), skipping", flush=True)
                    continue
                raise SystemExit(f"{npz_path} exists but does not match its meta sha; "
                                 "delete or --overwrite deliberately")

            row_seeds = row_generator_seeds(seed, len(prompts))
            chunks: list[dict] = []
            t0 = time.time()
            for s in range(0, len(prompts), args.batch_size):
                batch = prompts[s: s + args.batch_size]
                enc = encode_batch(batch).to(dev)
                res = harvest_batch(model, tap, normcatch, enc["input_ids"], enc["attention_mask"],
                                    row_seeds[s: s + len(batch)], eos_set, args.max_new,
                                    args.temperature, bucket_spaces, top_m=args.top_m,
                                    forward_kwargs=fkw)
                chunks.append(res)
                done = min(s + args.batch_size, len(prompts))
                print(f"[seed {seed}] {done}/{len(prompts)} prompts "
                      f"anchors={sum(int(x) for c in chunks for x in c['lengths'])} "
                      f"{time.time() - t0:.0f}s", flush=True)

            arrays = {
                "tokens": _pad_cat([c["tokens"] for c in chunks], 0),
                "entropy": _pad_cat([c["entropy"] for c in chunks], 0.0),
                "argmax": _pad_cat([c["argmax"] for c in chunks], 0),
                "top_ids": _pad_cat([c["top_ids"] for c in chunks], 0),
                "top_p": _pad_cat([c["top_p"] for c in chunks], 0),
                "slots": _pad_cat([c["slots"] for c in chunks], -1),
                "hidden": _pad_cat([c["hidden"] for c in chunks], 0),
                "lengths": np.concatenate([c["lengths"] for c in chunks]),
                "prompt_idx": np.arange(len(prompts), dtype=np.int32),
            }
            for name in bucket_spaces:
                arrays[f"mass{name}"] = _pad_cat([c[f"mass{name}"] for c in chunks], 0)
            n_finished = int(sum(int(c["finished"].sum()) for c in chunks))
            np.savez(npz_path, **arrays)
            lengths = arrays["lengths"]
            n_pairs = total_pairs(lengths, GAMMA_DEFAULT)
            grand_pairs += n_pairs
            meta = {
                **redact_args(vars(args)),
                "seed": seed,
                "regime": ("target-only sampled generations, NF4, chat template pinned; "
                           "shadow weight-slot taps (Phase 2 S1, registered protocol)"),
                "target_load": "nf4-double-quant-bf16compute" if args.load_4bit else "bf16",
                "chat_template_used": use_chat,
                "date_string_pinned": PINNED_DATE if use_chat else None,
                "alignment": "block-start: label_index(a, j) = a + j - 1 (sideband.harvest)",
                "split_rule": "prompt_idx % 7: {0..4} train, 5 val, 6 test",
                "layer_names": tap.layer_names,
                "sketch_layer_seeds": tap.layer_seeds,
                "row_seed_convention": "SeedSequence(seed).spawn(n_prompts)[i] % (2**63-1)",
                "prompts_sha256": _sha(args.prompts),
                **{f"buckets{name}_sha256": _sha(path) for name, path in bucket_paths.items()},
                "n_prompts_used": len(prompts),
                "n_anchors": int(lengths.sum()),
                "n_pairs": int(n_pairs),
                "gamma": GAMMA_DEFAULT,
                "mean_length": float(lengths.mean()),
                "n_rows_finished_by_eos": n_finished,
                "eos_hit_fraction": float((lengths < args.max_new).mean()),
                "eos_hit_note": ("a row whose token at max_new-1 IS its EOS counts in "
                                 "n_rows_finished_by_eos but not eos_hit_fraction"),
                "runtime_s": round(time.time() - t0, 1),
                "npz_file": npz_path.name,
                "npz_sha256": _sha(str(npz_path)),
                "torch_version": torch.__version__,
                "transformers_version": transformers.__version__,
                "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "preflight": preflight_report,
                "git_commit": _git_commit(),
            }
            _atomic_write_text(meta_path, json.dumps(meta, indent=1, sort_keys=True))
            print(f"[seed {seed}] anchors={meta['n_anchors']} pairs={n_pairs} "
                  f"mean_len={meta['mean_length']:.1f} -> {npz_path}", flush=True)
    finally:
        tap.close()
        normcatch.close()

    print(f"[harvest] total pairs (gamma={GAMMA_DEFAULT}) across seeds run/skipped: {grand_pairs} "
          f"(exit bar 1,000,000: {'MET' if grand_pairs >= 1_000_000 else 'NOT MET - extend seeds'})",
          flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()

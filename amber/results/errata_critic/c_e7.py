"""Critic: independent E7 (and E10 content-bytes cross-check) from raw generate shards."""
import sys
sys.modules["torch"] = None
import os
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
import json, glob, hashlib
from pathlib import Path
import numpy as np
import zstandard

REPO = Path(r"C:\Users\Michael\Desktop\SaaS\amber"); R = REPO / "results"
SNAP = Path(r"C:\Users\Michael\.cache\huggingface\hub\models--meta-llama--Llama-3.2-1B\snapshots\4e20de362430cd3b72f300e6b0f18e50e7166e08")
PAY = json.loads((R / "errata_recompute.json").read_text(encoding="utf-8"))["rows"]
print("tokenizer.json sha256", hashlib.sha256((SNAP / "tokenizer.json").read_bytes()).hexdigest(), "zstandard", zstandard.__version__)

raw = {}
for f in sorted(glob.glob(str(R / "p1/generate/shard_*.npz"))):
    z = np.load(f)
    for i, r in enumerate(z["row"]):
        a = z["ids"][i]; a = a[a >= 0]
        raw[int(r)] = (a.astype(np.int64), int(z["prompt_len"][i]))
rows = list(range(200))
n_tok = sum(len(raw[r][0]) - raw[r][1] for r in rows)

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(str(SNAP), local_files_only=True)
print("tok class", type(tok).__name__, "clean_up default", tok.clean_up_tokenization_spaces)
from tokenizers import Tokenizer
rawtok = Tokenizer.from_file(str(SNAP / "tokenizer.json"))

zc = zstandard.ZstdCompressor(level=19)
def zlen(s): return len(zc.compress(s.encode("utf-8")))
variants = {
    "a_default": lambda ids: tok.decode(ids.tolist()),
    "a_numpy_arg_like_p4": lambda ids: tok.decode(ids),
    "a_cleanup_false": lambda ids: tok.decode(ids.tolist(), clean_up_tokenization_spaces=False),
    "a_rawtokenizers": lambda ids: rawtok.decode(ids.tolist(), skip_special_tokens=False),
    "b_skip": lambda ids: tok.decode(ids.tolist(), skip_special_tokens=True),
    "b_skip_cleanup_false": lambda ids: tok.decode(ids.tolist(), skip_special_tokens=True, clean_up_tokenization_spaces=False),
}
res = {}; texts = {}
for k, fn in variants.items():
    ts = [fn(raw[r][0]) for r in rows]; texts[k] = ts
    b = sum(zlen(t) for t in ts)
    res[k] = {"bytes": b, "bits_per_gen_tok": 8 * b / n_tok}
    print(f"  {k:24s} bytes={b} bits/gen-tok={8*b/n_tok:.6f} -> {8*b/n_tok:.2f}")
print("  default == numpy-arg decode:", texts["a_default"] == texts["a_numpy_arg_like_p4"])
print("  default == rawtokenizers (cleanup off):", texts["a_cleanup_false"] == texts["a_rawtokenizers"])
n_bot = sum("<|begin_of_text|>" in t for t in texts["a_default"]); n_eot = sum("<|end_of_text|>" in t for t in texts["a_default"])
lit = sum(len(a.encode()) - len(b.encode()) for a, b in zip(texts["a_default"], texts["b_skip"]))
n_bot_count = sum(t.count("<|begin_of_text|>") for t in texts["a_default"])
print(f"  n_rows_with_bot={n_bot} (total occurrences {n_bot_count}) n_rows_with_eot={n_eot} literal_bytes={lit}")
# bos at start of every row?
print("  rows starting with 128000:", sum(int(raw[r][0][0]) == 128000 for r in rows), " any other special ids (>=128000) mid-seq:",
      sum(int(((raw[r][0][1:] >= 128000) & (raw[r][0][1:] != 128001)).sum()) for r in rows))
pv = PAY["E7"]["value"]
d = 0
for k, mine in (("a_as_printed", res["a_default"]["bits_per_gen_tok"]), ("b_skip_special", res["b_skip"]["bits_per_gen_tok"]),
                ("bytes_a", res["a_default"]["bytes"]), ("bytes_b", res["b_skip"]["bytes"]), ("literal_bytes", lit),
                ("n_rows_with_bot", n_bot), ("n_rows_with_eot", n_eot), ("n_tok", n_tok)):
    a = abs(float(mine) - float(pv[k])); d = max(d, a); print(f"  {k}: mine={mine!r} payload={pv[k]!r} abs={a:.3e}")
st = "CONFIRMED" if f"{res['a_default']['bits_per_gen_tok']:.2f}" == "7.28" else "CORRECTED"
print("  E7 status", st, "payload", PAY["E7"]["status"], "maxdisc", d)
# p4_real_archive.json at 6672db4 printed value
import subprocess
p4 = json.loads(subprocess.check_output(["git", "-C", str(REPO), "show", "6672db4:results/p4_real_archive.json"]))["report"]
print("  p4_real_archive.json per-archive:", p4["zstd19_full_text_per_archive_bits_per_generated_token"], " gen-text:", p4["zstd19_generated_text_bits_per_token"],
      " concat full:", p4["zstd19_full_text_concatenated_bits_per_generated_token"])
# E10 cross-check: content bytes per token of generated text (p1_divergence: "".join(decode(gen)))
gen_text = "".join(tok.decode(raw[r][0][raw[r][1]:].tolist()) for r in rows)
gen_text_nc = "".join(tok.decode(raw[r][0][raw[r][1]:].tolist(), clean_up_tokenization_spaces=False) for r in rows)
p1 = json.loads((R / "p1_divergence.json").read_text())["row"]
print(f"  E10 content_bytes/token default={len(gen_text.encode())/n_tok!r} json={p1['content_bytes_per_token']!r} cleanup_off={len(gen_text_nc.encode())/n_tok:.6f}")
print(f"  E10 zstd19 gen text default={8*zlen(gen_text)/n_tok!r} json={p1['zstd19_bits_per_token']!r} cleanup_off={8*zlen(gen_text_nc)/n_tok:.6f}")
full = "".join(texts["a_default"]); print(f"  concat full text: {8*zlen(full)/n_tok!r}")
# OPEN_QUESTIONS 7.3 check
print("  rounds to 7.3:", f"{res['a_default']['bits_per_gen_tok']:.1f}")

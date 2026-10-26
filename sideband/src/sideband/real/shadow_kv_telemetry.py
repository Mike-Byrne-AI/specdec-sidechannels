"""Shadow KV-page telemetry: which PAST PAGES the target attends to.

GPU box. The emergent Phase-2 alternate track (OQ-8): KV offloading and paged
attention are deployed reality, so the address stream of the KV tier — top-k
attended page ids per layer per token — is telemetry with a hardware premise
that already exists. Values never cross: pages ids only.

v0 implementation constraint: flash/sdpa kernels don't materialize attention
weights, so this harvester loads the model with attn_implementation="eager"
and output_attentions=True. That is SLOW and memory-hungry — it is a
telemetry harvester, not a serving path. A production tap would read the
paging layer directly (vLLM block tables), which is the honest end state.

Per (position, layer): head-mean attention over past positions from the last
query row -> top-k positions -> unique page ids (pos // page_size).

Output jsonl: {"pos": 41, "layer": 12, "pages": [0, 3, 5], "token": 2211}

Nearest relative: TriForce (the target's own sparse KV as its draft) — this
is the observability-constrained cousin: page IDS only, consumed by a
separate draft. See docs/PRIOR_ART.md.

Usage:
    python -m sideband.real.shadow_kv_telemetry \
        --model meta-llama/Llama-3.1-8B-Instruct \
        --page-size 16 --topk 8 --layers 8,16,24 \
        --prompts data/prompts.jsonl --max-new 128 \
        --out results/real/kv_telemetry.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import require_real_deps


def main() -> None:  # pragma: no cover - GPU box entrypoint
    torch, transformers = require_real_deps()
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--page-size", type=int, default=16)
    ap.add_argument("--topk", type=int, default=8)
    ap.add_argument("--layers", default=None, help="comma layer indices; default all")
    ap.add_argument("--prompts", default=None)
    ap.add_argument("--n-prompts", type=int, default=20)
    ap.add_argument("--max-new", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--out", default="results/real/kv_telemetry.jsonl")
    args = ap.parse_args()

    tok = transformers.AutoTokenizer.from_pretrained(args.model)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto",
        attn_implementation="eager",  # required to materialize attention weights
    ).eval()
    keep = {int(x) for x in args.layers.split(",")} if args.layers else None

    if args.prompts:
        prompts = [json.loads(l)["prompt"] for l in Path(args.prompts).read_text().splitlines() if l.strip()]
    else:
        prompts = ["Summarize the plot of a heist movie.", "Explain how tides work."] * (
            (args.n_prompts // 2) + 1
        )
    prompts = prompts[: args.n_prompts]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f, torch.no_grad():
        for pi, prompt in enumerate(prompts):
            ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
            for step in range(args.max_new):
                outputs = model(ids, output_attentions=True)
                # attentions: tuple(L) of (B, H, S, S); last query row = new token's view
                records = []
                for li, att in enumerate(outputs.attentions):
                    if keep is not None and li not in keep:
                        continue
                    row = att[0].float().mean(dim=0)[-1]  # head-mean, (S,)
                    k = min(args.topk, row.shape[0])
                    top_pos = torch.topk(row, k=k).indices
                    pages = sorted({int(p) // args.page_size for p in top_pos.tolist()})
                    records.append({"pos": step, "layer": li, "pages": pages, "prompt_idx": pi})
                logits = outputs.logits[0, -1].float()
                probs = torch.softmax(logits / max(args.temperature, 1e-4), dim=-1)
                nxt = int(torch.multinomial(probs, 1))
                for r in records:
                    r["token"] = nxt
                    f.write(json.dumps(r) + "\n")
                ids = torch.cat([ids, torch.tensor([[nxt]], device=ids.device)], dim=1)
                if nxt == tok.eos_token_id:
                    break
    print(json.dumps({"out": str(out_path), "page_size": args.page_size}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

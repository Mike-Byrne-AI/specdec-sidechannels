import sys, json, shutil, io, contextlib
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "tools")
import run_seed_replay as sr
R = Path("results/real")
S = Path(sys.argv[1]); S.mkdir(parents=True, exist_ok=True)
for rs, vs, k, seed in sr.REPLAY_SPECS:
    for ext in ("gen.jsonl", "stats.jsonl", "meta.json"):
        shutil.copy(R / f"{vs}.{ext}", S / f"{vs}.{ext}")
    gen = sr._jsonl_rows(R / f"{vs}.gen.jsonl")[:k]; st = sr._jsonl_rows(R / f"{vs}.stats.jsonl")[:k]
    (S / f"{rs}.gen.jsonl").write_text("".join(json.dumps({**g, "run_id": "X"}) + "\n" for g in gen))
    (S / f"{rs}.stats.jsonl").write_text("".join(json.dumps({**r, "run_id": "X", "seconds": 0.1, "peak_vram_gb": 1.0}) + "\n" for r in st))
    m = json.loads((R / f"{vs}.meta.json").read_text(encoding="utf-8")); m.update({"n_prompts": k, "git_commit": "L", "run_id": "X"})
    (S / f"{rs}.meta.json").write_text(json.dumps(m))
buf = io.StringIO()
with contextlib.redirect_stdout(buf): rep = sr.replay_check(S, launch_commit="L")
print("exact replay of committed rows:", rep["all_match"]); print(buf.getvalue())
# perturb one float field in arm-4 prompt 5's stats row by one ulp
p = S / "oq20_replay_k3_s1_arm4.stats.jsonl"; rows = sr._jsonl_rows(p)
import numpy as np
rows[5]["analytic_acc_drafted_sum"] = float(np.nextafter(rows[5]["analytic_acc_drafted_sum"], 1e9))
p.write_text("".join(json.dumps(r) + "\n" for r in rows))
with contextlib.redirect_stdout(io.StringIO()): rep = sr.replay_check(S, launch_commit="L")
print("one-ulp float change ->", rep["all_match"], rep["arms"]["oq20_replay_k3_s1_arm4"]["stats_rows"][5]["differing_fields"])
with contextlib.redirect_stdout(io.StringIO()): rep = sr.replay_check(S)
print("without --launch-commit, launch_commit_clean =", rep["arms"]["oq20_replay_k3_s1_arm1"]["meta"]["launch_commit_clean"])

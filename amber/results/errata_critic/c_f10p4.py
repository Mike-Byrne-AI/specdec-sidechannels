import sys; sys.modules["torch"]=None
import glob, json, numpy as np
from pathlib import Path
R=Path(r"C:\Users\Michael\Desktop\SaaS\amber\results")
rk=np.concatenate([np.load(f)["ranks"] for f in sorted(glob.glob(str(R/"p1/draft/shard_*.npz")))]).astype(int)
N=rk.size; B=json.load(open(R/"p2b_escape_robustness.json"))
def rate(enc,dec,th,m):
    row=[r for r in B["report"][enc]["decoders"][dec] if r["theta"]==th and r["m"]==m][0]
    byr=row["C_desync_by_rank"]
    e=sum((rk==r).sum()*byr[str(r)]["desync"]/byr[str(r)]["n"] for r in range(2,65) if str(r) in byr and byr[str(r)]["n"])
    eA=(rk==1).sum()*row["desyncs"]["A"]/row["symbol_counts"]["A"]
    return N/e if e else None, N/(e+eA) if (e+eA) else None
for enc,dec in (("cpu_fp32","cuda_fp16_b1"),("cpu_fp32","cuda_bf16_b1"),("cuda_bf16_b1","cuda_bf16_b8"),("cpu_fp32","cuda_int8_b1")):
    for th,m in ((0.0,2),(0.142,2),(0.465,2)):
        c,ca=rate(enc,dec,th,m); print(f"{enc}->{dec} th{th}/m{m}: 1 C-desync per {c:.0f} tok; incl A: 1 per {ca:.0f}")

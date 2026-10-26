import sys; sys.modules["torch"]=None
import glob, numpy as np
from pathlib import Path
R=Path(r"C:\Users\Michael\Desktop\SaaS\amber\results")
gen={}
for f in sorted(glob.glob(str(R/"p1/generate/shard_*.npz"))):
    z=np.load(f)
    for i,r in enumerate(z["row"]):
        a=z["ids"][i]; a=a[a>=0]; gen[int(r)]=a[int(z["prompt_len"][i]):].astype(np.int64)
dr={}
for f in sorted(glob.glob(str(R/"p1/draft/shard_*.npz"))):
    z=np.load(f); o=z["offsets"]
    for i,r in enumerate(z["row"]): dr[int(r)]=(z["ranks"][o[i]:o[i+1]].astype(np.int64), z["log2q"][o[i]:o[i+1]].astype(np.float64))
def loop(g,W,P):
    n=len(g)
    if n<W: return 0.0
    t=g[n-W:]
    for p in range(1,P+1):
        if np.array_equal(t[p:],t[:-p]):
            s=W
            while s<n and g[n-s-1]==g[n-s-1+p]: s+=1
            return s/n
    return 0.0
def gb(n): return 2*(int(n).bit_length()-1)+1
def ab(r):
    b=0;gap=0
    for x in r:
        if x==1: gap+=1; continue
        b+=gb(gap+1)+gb(int(x)-1); gap=0
    return b
res=[]
for W in (64,128,192,256):
  for P in (16,32,64,128):
    if P>=W: continue
    for t in (0.25,0.5,0.75):
      fl={r:loop(gen[r],W,P)>=t for r in range(200)}
      out={}
      for nm,fv in (("L",True),("N",False)):
        sel=[r for r in range(200) if fl[r]==fv]
        rk=np.concatenate([dr[r][0] for r in sel]); q=np.concatenate([dr[r][1] for r in sel]); n=rk.size; ac=-q.mean()
        out[nm]=(ab(rk)/n-ac, sum(ab(dr[r][0]) for r in sel)/n/ac-1)
      sign_diff=np.sign(out["L"][0])!=np.sign(out["N"][0]); big=abs(out["N"][1])>0.02
      res.append((W,P,t,sign_diff,big,round(out["L"][0],4),round(out["N"][0],4),round(out["N"][1],4)))
n_corr=sum(1 for x in res if x[3] or x[4]); n_sign=sum(1 for x in res if x[3]); n_big=sum(1 for x in res if x[4])
print("grid points",len(res),"CORRECTED at",n_corr,"sign-differs at",n_sign,"|rel_N|>0.02 at",n_big)
print("rel_perarchive_nonlooped range:",min(x[7] for x in res),max(x[7] for x in res), " positive (amber worse) at", sum(1 for x in res if x[7]>0))
print("delta_concat_nonlooped range:",min(x[6] for x in res),max(x[6] for x in res))
for x in res:
    if not (x[3] and x[4]): print("  ",x)

import subprocess
from pathlib import Path
from collections import Counter
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
def git(*a): return subprocess.run(["git",*a],cwd=ROOT,capture_output=True,check=True).stdout
def style(b):
    lf=b.count(b"\n"); crlf=b.count(b"\r\n")
    if lf==0: return "no-newline"
    if crlf==lf: return "CRLF"
    if crlf==0: return "LF"
    return "MIXED"
tracked=[p for p in git("ls-files","-z","--","results").decode().split("\0") if p]
head=Counter(); idx=Counter(); mixed=[]
for p in tracked:
    h=style(git("cat-file","blob",f"HEAD:{p}")); i=style(git("cat-file","blob",f":{p}"))
    head[h]+=1; idx[i]+=1
    if "MIXED" in (h,i): mixed.append((p,h,i))
print("HEAD blob styles:",dict(head)); print("index blob styles (post-change):",dict(idx)); print("mixed:",mixed[:10])
for p in ["results/e01_verifier_exactness.json","results/e02_crossbucket_audit.json","results/e03_oracle_ceiling.json","results/e04_staleness_decay.json","results/e05_sidecar_recovery.json","results/e06_posterior_mechanism.json","results/e07_hint_rate.json","results/summary.json"]:
    try:
        h=style(git("cat-file","blob",f"HEAD:{p}")); d=style((ROOT/p).read_bytes())
        last=git("log","-1","--format=%h %ad","--date=iso","--",p).decode().strip()
        print(f"{p}: HEAD={h} disk={d} last-commit={last}")
    except Exception as e: print(p, "ERR", e)

import hashlib, json, subprocess, sys, os
from pathlib import Path
ROOT = Path(r"C:\Users\<user>\Desktop\Research\sideband")
SP = Path(r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\64064aa4-b9c8-45b6-9f59-46838015656c\scratchpad")
def git(*a, data=None):
    return subprocess.run(["git", *a], cwd=ROOT, input=data, capture_output=True, check=True).stdout
def sha(b): return hashlib.sha256(b).hexdigest()

# ---------- R1
staged_all = [p for p in git("diff","--cached","--name-only","-z").decode().split("\0") if p]
staged_res = [p for p in git("diff","--cached","--name-only","-z","--","results/").decode().split("\0") if p]
outside = [p for p in staged_all if not p.startswith("results/")]
print("R1 staged total:", len(staged_all), " under results/:", len(staged_res), " outside results/:", outside)
status = git("diff","--cached","--name-status").decode().split("\n")
kinds = {}
for line in status:
    if line.strip():
        kinds[line.split("\t")[0]] = kinds.get(line.split("\t")[0],0)+1
print("R1 staged status kinds:", kinds)
r1 = {"norm_neq":[], "idx_neq_disk":[], "head_has_cr":[], "idx_lone_lf":[], "idx_lone_cr":[], "idx_neq_head_crlf":[], "idx_no_cr":[], "disk_trailing_newline_diff":[]}
per = {}
for p in staged_res:
    head = git("cat-file","blob",f"HEAD:{p}")
    idx = git("cat-file","blob",f":{p}")
    disk = (ROOT/p).read_bytes()
    hn = head.replace(b"\r\n", b"\n"); inn = idx.replace(b"\r\n", b"\n")
    if hn != inn: r1["norm_neq"].append(p)
    if idx != disk: r1["idx_neq_disk"].append(p)
    if b"\r" in head: r1["head_has_cr"].append(p)
    lf = idx.count(b"\n"); crlf = idx.count(b"\r\n"); cr = idx.count(b"\r")
    if lf != crlf: r1["idx_lone_lf"].append((p, lf-crlf))
    if cr != crlf: r1["idx_lone_cr"].append((p, cr-crlf))
    if cr == 0: r1["idx_no_cr"].append(p)
    if idx != head.replace(b"\n", b"\r\n"): r1["idx_neq_head_crlf"].append(p)
    per[p] = {"lf_sha": sha(head), "crlf_sha": sha(idx), "disk_sha": sha(disk), "lines": crlf, "bytes_head": len(head), "bytes_idx": len(idx)}
for k,v in r1.items(): print("R1", k, len(v), v[:5])
json.dump(per, open(SP/"critic"/"staged84.json","w"), indent=1)

# ---------- R2
m = json.load(open(SP/"before_manifest.json"))
man = m["results_disk_sha"]
tracked = [p for p in git("ls-files","-z","--","results").decode().split("\0") if p]
print("R2 tracked results files:", len(tracked), " manifest entries:", len(man), " manifest head:", m["head"])
print("R2 tracked-not-in-manifest:", sorted(set(tracked)-set(man))[:5], len(set(tracked)-set(man)))
print("R2 manifest-not-tracked:", sorted(set(man)-set(tracked))[:5], len(set(man)-set(tracked)))
diff2 = [p for p in tracked if p in man and sha((ROOT/p).read_bytes()) != man[p]]
print("R2 disk sha != manifest:", len(diff2), diff2[:5])
# frozen tools
ft = m["frozen_tools_sha"]
fdiff = [p for p,s in ft.items() if sha((ROOT/p).read_bytes()) != s]
print("R2b frozen_tools entries:", len(ft), " differ now:", len(fdiff), fdiff, sorted(ft))

# ---------- R5
ls = git("ls-tree","-r","-z","HEAD","--","results").decode().split("\0")
headblob = {}
for rec in ls:
    if not rec: continue
    meta, path = rec.split("\t",1)
    headblob[path] = meta.split()[2]
paths = sorted(headblob)
disk = git("hash-object","--no-filters","--stdin-paths", data=("\n".join(paths)+"\n").encode()).decode().split()
d5 = [p for p,d in zip(paths, disk) if d != headblob[p]]
print("R5 HEAD results blobs:", len(headblob), " differ from disk (no-filters):", len(d5))
print("R5 set equal to staged set:", set(d5) == set(staged_res), " sym diff:", sorted(set(d5) ^ set(staged_res))[:5])
# index vs disk for all tracked
lsi = git("ls-files","-s","-z","--","results").decode().split("\0")
idxblob = {}
for rec in lsi:
    if not rec: continue
    meta, path = rec.split("\t",1); idxblob[path] = meta.split()[1]
ip = sorted(idxblob)
disk2 = git("hash-object","--no-filters","--stdin-paths", data=("\n".join(ip)+"\n").encode()).decode().split()
print("R5b index blobs:", len(idxblob), " index != disk:", sum(1 for p,d in zip(ip,disk2) if d != idxblob[p]))
# Untracked/ignored files under results present on disk
allres = [str(Path(dp,f).relative_to(ROOT)).replace("\\","/") for dp,_,fs in os.walk(ROOT/"results") for f in fs]
print("disk files under results/:", len(allres), " untracked-on-disk:", len(set(allres)-set(tracked)))

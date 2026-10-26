import json, hashlib, subprocess, os, datetime
ROOT = "C:/Users/<user>/Desktop/Research/sideband"
CRLF = bytes([13, 10]); LF = bytes([10])
def sh(b): return hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True).stdout
def fsha(p): return sh(open(ROOT + "/" + p, "rb").read())
def lfsha(p): return sh(open(ROOT + "/" + p, "rb").read().replace(CRLF, LF))
inst = "tools/run_prefetch_strat.py"
raw_disk = open(ROOT + "/" + inst, "rb").read()
print("instrument disk raw", sh(raw_disk)[:12], "disk LF", sh(raw_disk.replace(CRLF, LF))[:12], "has CR", bytes([13]) in raw_disk)
blob = git("show", "fea2431:" + inst)
print("instrument git blob @fea2431", sh(blob)[:12], "blob==disk(LF)", blob == raw_disk.replace(CRLF, LF))
for p, want in (("tools/run_prefetch_bigram.py", "10599fa98c27"), ("tools/run_prefetch_readouts.py", "8529532d4d78")):
    print(p, "disk LF", lfsha(p)[:12], "git blob", sh(git("show", "fea2431:" + p))[:12], "want", want)
freeze_ct = int(git("log", "-1", "--format=%ct", "fea2431").strip()); print("freeze commit unix", freeze_ct, datetime.datetime.fromtimestamp(freeze_ct, datetime.timezone.utc))
print("HEAD", git("rev-parse", "HEAD").strip().decode())
print("porcelain tracked:", repr(git("status", "--porcelain", "--untracked-files=no").decode()))
print("diff fea2431 HEAD names:", repr(git("diff", "--name-only", "fea2431", "HEAD").decode()))
for name, twin, hdir in (("prefetch_strat_s3", "prefetch_bigram_s3", "harvest_moe"), ("prefetch_strat_s3_r", "prefetch_bigram_s3_r", "harvest_moe_r")):
    print("=====", name)
    pay = json.load(open(ROOT + "/results/real/" + name + ".json", encoding="utf-8"))
    meta = json.load(open(ROOT + "/results/real/" + name + ".meta.json", encoding="utf-8"))
    prov = pay["provenance"]
    print("meta == payload provenance:", meta == prov)
    print("git_commit", prov["git_commit"], "tracked", prov["git_status_tracked"], "instrument", prov["instrument_sha256"][:12])
    print("frozen", prov["frozen_twin"]["sha256_lf"][:12], prov["frozen_instrument"]["sha256_lf"][:12])
    st = prov["started_unix"]; rt = prov["runtime_s"]
    print("started", datetime.datetime.fromtimestamp(st, datetime.timezone.utc), "after freeze by s:", round(st - freeze_ct, 1), "runtime_s", round(rt, 1),
          "end", datetime.datetime.fromtimestamp(st + rt, datetime.timezone.utc))
    for suf in (".json", ".json.state.jsonl", ".meta.json"):
        p = ROOT + "/results/real/" + name + suf
        mt = os.stat(p).st_mtime
        print("  mtime", suf, datetime.datetime.fromtimestamp(mt, datetime.timezone.utc), "minus start", round(mt - st, 1), "minus end", round(mt - st - rt, 2))
    # shard metas (committed copies)
    mm = {}
    for f in sorted(prov["harvest_npz_sha256"]):
        mp = "results/real/" + hdir + "/" + f.replace(".npz", ".meta.json")
        committed = json.loads(git("show", "fea2431:" + mp))
        disk = json.load(open(ROOT + "/" + mp, encoding="utf-8"))
        mm[f] = (committed["npz_sha256"] == prov["harvest_npz_sha256"][f], disk == committed)
    print("  shard npz sha == committed meta / disk meta == committed:", mm)
    tw = json.load(open(ROOT + "/results/real/" + twin + ".json", encoding="utf-8"))
    tp = tw["provenance"]; rec = prov["twin"]
    print("  twin shards == run shards", tp["harvest_npz_sha256"] == prov["harvest_npz_sha256"])
    print("  twin rec path", rec["path"], "sha ok", rec["sha256"] == fsha(rec["path"]), "state sha ok", rec["state_sha256"] == fsha(rec["state_path"]))
    print("  twin rec git", rec["git_commit"] == tp["git_commit"], "inst", rec["instrument_sha256"] == tp["instrument_sha256"] == "10599fa98c276751f3296ecff6815aae07a701e35d13b5a2fb6ff8170ba7a11a",
          "enc", rec["encoding"] == tp["encoding_selected"], "lams", rec["lambda_selected"] == {k: float(v) for k, v in tp["lambda_selected"].items()},
          "nrows", rec["n_state_rows"] == tw["n_state_rows"], "shards", rec["harvest_npz_sha256"] == tp["harvest_npz_sha256"],
          "gate_eq", rec["gate_eq"] == tw["conclusion"]["deltas"]["gate_eq|B=16"])
    print("  twin files tracked & unchanged since commit:", git("ls-files", rec["path"], rec["state_path"]).decode().split(), repr(git("diff", "--stat", "HEAD", "--", rec["path"], rec["state_path"]).decode()))
    print("  twin file git blob sha == disk:", sh(git("show", "HEAD:" + rec["path"])) == fsha(rec["path"]), sh(git("show", "HEAD:" + rec["state_path"])) == fsha(rec["state_path"]))
    # lambdas
    ls = prov["lambda_selected"]
    print("  twin arms lambdas == twin payload:", all(ls[a] == float(tp["lambda_selected"][a]) for a in tp["lambda_selected"]), "encoding_source", prov["encoding_source"], "encoding", prov["encoding_selected"])
    grid = prov["constants"]["lambdas"]
    for arm, tab in prov["val_table"].items():
        best, bl = -1e9, None
        for lam in grid:
            v = tab[str(float(lam))]
            if v > best:
                best, bl = v, float(lam)
        srt = sorted(((v, float(k)) for k, v in tab.items()), reverse=True)
        print("   ", arm, "rederived", bl, "payload", ls[arm], "edge", bl in (grid[0], grid[-1]), "payload edge", prov["lambda_grid_edge"][arm],
              "best", round(srt[0][0], 6), "second", srt[1], "gap", srt[0][0] - srt[1][0])
    print("  grid", grid, "seeds", prov["seeds"], "n_test_prompts", prov["n_test_prompts"], "blas", prov["blas"], "numpy", prov["numpy_version"])
    ls_ = prov["label_space"]
    print("  label space shas", fsha("results/real/buckets_olmoe_k16.json") == ls_["buckets_sha256"], fsha("results/real/glue_olmoe_k16.json") == ls_["glue_sha256"])
    print("  args", prov["args"])
    print("  n_positions", prov["n_positions"], "twin n_positions", tp.get("n_positions"))
    print("  table_coverage == twin's", prov["table_coverage"] == tp.get("table_coverage"))
    # state header vs payload
    hdr = json.loads(open(ROOT + "/results/real/" + name + ".json.state.jsonl", encoding="utf-8").readline())
    print("  header: shards", hdr["harvest_npz_sha256"] == prov["harvest_npz_sha256"], "enc", hdr["encoding"] == prov["encoding_selected"],
          "lams", hdr["lambda_selected"] == ls, "twin", hdr["twin"] == rec, "smoke", hdr["smoke"])
    # git check-ignore
    for suf in (".json", ".json.state.jsonl", ".meta.json"):
        r = subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", "results/real/" + name + suf])
        print("  check-ignore", suf, "exit", r.returncode)

import sys, json
sys.path.insert(0, "src")
import numpy as np
from collections import defaultdict
from sideband.stats import paired_cluster_delta_ci, cluster_bootstrap_ci
S = sys.argv[1]
pay = json.load(open(S, encoding="utf-8"))
lines = open(S + ".state.jsonl", encoding="utf-8").read().splitlines()
hdr = json.loads(lines[0]); rows = [json.loads(x) for x in lines[1:]]
print("rows", len(rows), "payload n_state_rows", pay["n_state_rows"], "header", {k: hdr[k] for k in ("encoding","horizons","k_of_horizon")})
prompts = sorted({r["prompt_idx"] for r in rows}); P = {p:i for i,p in enumerate(prompts)}
print("prompts", len(prompts))
H = defaultdict(lambda: np.zeros(len(prompts))); N = defaultdict(lambda: np.zeros(len(prompts)))
for r in rows:
    for sc in (r["scope"], "all"):
        k = (r["arm"], r["budget"], r["key"], sc)
        H[k][P[r["prompt_idx"]]] += r["hits"]; N[k][P[r["prompt_idx"]]] += r["needed"]
enc = hdr["encoding"]; FREE = "free_bigram_b" if enc=="prev_table" else "free_bigram_a"; HIST = FREE.replace("free","history")
names = {"FREE":FREE,"HIST":HIST}
pairs = [("abt","history_tok","free_tok"),("gate_eq","history_tok","FREE"),("d_add_bigram","HIST","FREE"),("gate_eq_r2","history_tok_r2","free_r2"),("d_add_r2","history_bigram_r2","free_r2"),("d_eq_h","history_bigram_r2","free_h"),("d_add_h","history_all_h","free_h"),("anchor","history_all_h","history_bigram_r2"),("free_h-free_r2","free_h","free_r2"),("h_only-free_tok","h_only","free_tok"),("h_only-history","h_only","history"),("h_only-history_tok","h_only","history_tok"),("free_r2-FREE","free_r2","FREE"),("history_tok_r2-history_tok","history_tok_r2","history_tok")]
for a in ("history","free_tok","history_tok","FREE","HIST","free_r2","history_tok_r2","history_bigram_r2","h_only","free_h","history_all_h"):
    pairs.append((f"{a}-marginal", a, "marginal"))
D = pay["conclusion"]["deltas"]; T = pay["conclusion"]["tables"]
maxd = 0.0; n = 0; missing = []
for j in hdr["horizons"]:
    for B in (8,16,32):
        for sc in ("covered","fallback","all"):
            for nm,a,b in pairs:
                ka=(names.get(a,a),B,j,sc); kb=(names.get(b,b),B,j,sc)
                if ka not in N or kb not in N: continue
                assert np.array_equal(N[ka], N[kb]), (ka,kb)
                d,lo,hi = paired_cluster_delta_ci(H[ka],H[kb],N[ka],n_boot=2000,seed=0)
                key=f"{nm}|B={B}|j={j}|{sc}"
                if key not in D: missing.append(key); continue
                for x,y in ((d,D[key]["delta"]),(lo,D[key]["lo"]),(hi,D[key]["hi"])):
                    maxd=max(maxd,abs(x-y)); n+=1
# tables pooled points + CI
for (arm,B,j,sc),nn in N.items():
    key=f"{arm}|B={B}|j={j}|{sc}"
    pt = H[(arm,B,j,sc)].sum()/nn.sum(); lo,hi = cluster_bootstrap_ci(H[(arm,B,j,sc)], nn, n_boot=2000, seed=0)
    t=T[key]["all"]
    for x,y in ((pt,t["point"]),(lo,t["ci_lo"]),(hi,t["ci_hi"])):
        maxd=max(maxd,abs(x-y)); n+=1
print("values compared", n, "max abs discrepancy", maxd, "missing in payload", missing[:5], len(missing))
print("payload delta keys not recomputed", len([k for k in D if k not in {f'{nm}|B={B}|j={j}|{sc}' for j in hdr['horizons'] for B in (8,16,32) for sc in ('covered','fallback','all') for nm,_,_ in pairs}]))
# labels
def rd(d,lo,hi): return "SIGNAL" if lo>0 and d>=0.05 else "NEGATIVE" if hi<0 else "NOT-SHOWN"
qs={}
for j in hdr["horizons"]:
    g=lambda nm: D[f"{nm}|B=16|j={j}|all"]
    eq,add,anc,gain=g("d_eq_h"),g("d_add_h"),g("anchor"),g("free_h-free_r2")
    e=rd(eq["delta"],eq["lo"],eq["hi"])=="SIGNAL"; u=rd(add["delta"],add["lo"],add["hi"])=="SIGNAL"
    q="H-SURVIVES" if e and u else "H-COMPLEMENTARY" if u else "H-ABSORBS" if not e else "H-INCONSISTENT"
    guard = gain["hi"]<0 or anc["hi"]<0
    strad = (eq["lo"]<=0.05<=eq["hi"]) or (add["lo"]<=0.05<=add["hi"])
    qs[j]=q
    print("j",j,q,"guard",guard,"straddle",strad, "| payload", pay["conclusion"]["labels"]["horizons"][str(j)]["q"], pay["conclusion"]["labels"]["horizons"][str(j)]["reader_guard"], pay["conclusion"]["labels"]["horizons"][str(j)]["floor_straddle"])
print("payload label", pay["conclusion"]["labels"]["label"])
pv=pay["provenance"]
print("n_positions", pv["n_positions"])
print("runtime_s", pv["runtime_s"], "replay_seconds", pv["replay_seconds"], "elapsed", pv["elapsed_per_horizon_s"])
print("instrument_sha256", pv["instrument_sha256"][:12], "git", pv["git_commit"][:12], "tracked dirty", pv["git_status_tracked"] if not isinstance(pv["git_status_tracked"], list) else len(pv["git_status_tracked"]))
print("hidden", {k:v for k,v in pv["hidden"].items() if k!="eigen_top8"})
for j,s in pv["selection"].items():
    print("sel", j, s["k_selected"], s["k_grid_edge"], {a:s["lambda_selected"][a] for a in ("free_r2","h_only","free_h","history_all_h","marginal") if a in s["lambda_selected"]})
    kt=s["k_val_table"]; best=max((v,k,l) for k,row in kt.items() for l,v in row.items())
    print("   k table best", best, " per-k max:", {k: round(max(row.values()),4) for k,row in kt.items()})

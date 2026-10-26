import json, math, zipfile, glob
R = r"C:\Users\<user>\Desktop\Research\sideband\results\real"
tw = json.load(open(R + r"\prefetch_bigram_s3.json", encoding="utf-8"))["provenance"]
twr = json.load(open(R + r"\prefetch_bigram_s3_r.json", encoding="utf-8"))["provenance"]
print("twin runtimes %.1f / %.1f" % (tw["runtime_s"], twr["runtime_s"]))
ff = json.load(open(R + r"\fullfree_s3.json", encoding="utf-8"))
def find(o, key, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if key in k.lower(): yield path + "/" + k, v
            yield from find(v, key, path + "/" + k)
hs = list(find(ff.get("provenance", ff), "sha"))
print("fullfree_s3 sha-ish fields:", [p for p, _ in hs][:12])
twsh = tw["harvest_npz_sha256"]
print("twin harvest shas type", type(twsh).__name__, (list(twsh.items())[:2] if isinstance(twsh, dict) else twsh[:2]))
blob = json.dumps(ff)
vals = list(twsh.values()) if isinstance(twsh, dict) else twsh
print("twin shard shas found inside fullfree_s3.json:", sum(1 for v in vals if v in blob), "of", len(vals))
z = zipfile.ZipFile(sorted(glob.glob(R + r"\harvest_moe\*.npz"))[0])
print("harvest npz members:", [n for n in z.namelist()])
print("ln(50304) = %.4f" % math.log(50304))
m = json.load(open(r"C:\Users\<user>\AppData\Local\Temp\claude\c--Users-<user>-Desktop-Research-sideband\12e6097a-8666-465a-b5a3-e76024a56cff\scratchpad\strat\smoke\strat_smoke2.meta.json", encoding="utf-8"))
print("label space", m["label_space"]["n_tokens"], "ent scale", m["constants"]["entropy_scale_ln_v"])
st1 = json.load(open(R + r"\prefetch_s3.json", encoding="utf-8"))
b = json.dumps(st1); print("0.5197 in prefetch_s3.json:", "0.5197" in b, "| recency keys:", [k for k in st1["conclusion"]["tables"] if k.startswith("recency")][:4] if "tables" in st1.get("conclusion", {}) else None)

import sys, json, re
sys.path.insert(0, "src")
ROOT = "."
P = json.load(open("results/real/prefetch_strat_s3.json"))
R = json.load(open("results/real/prefetch_strat_s3_r.json"))
TP = json.load(open("results/real/prefetch_bigram_s3.json"))
TR = json.load(open("results/real/prefetch_bigram_s3_r.json"))

def f4(x): return f"{x:+.4f}"
def trip(d): return (f4(d["delta"]), f4(d["lo"]), f4(d["hi"]))
def tripT(d): return (f4(d["point"]), f4(d["ci_lo"]), f4(d["ci_hi"]))

def index(X):
    out = {}
    C = X["conclusion"]
    for k, d in C["deltas"].items():
        out.setdefault(trip(d), []).append("delta:" + k)
    for k, t in C["tables"].items():
        out.setdefault(tripT(t["all"]), []).append("table:" + k)
    return out
IP, IR = index(P), index(R)
def tindex(X):
    out = {}
    C = X["conclusion"]
    for k, d in C.get("deltas", {}).items():
        if isinstance(d, dict) and "delta" in d:
            out.setdefault(trip(d), []).append("twin-delta:" + k)
    return out
ITP, ITR = tindex(TP), tindex(TR)

NUM = r"[+-]\d+\.\d+"
TRI = rf"({NUM}) \[({NUM}), ({NUM})\]"
PAIR = re.compile(rf"{TRI}\s*/\s*{TRI}")
SING = re.compile(TRI)

def check(text, tag):
    n_pairs = 0; bad = []
    used = set()
    for m in PAIR.finditer(text):
        a = m.group(1, 2, 3); b = m.group(4, 5, 6)
        kp = set(IP.get(a, [])) | set("T" + k for k in ITP.get(a, []))
        kr = set(IR.get(b, [])) | set("T" + k for k in ITR.get(b, []))
        common = sorted(kp & kr)
        ctx = text[max(0, m.start() - 90):m.start()].replace("\n", " ")
        n_pairs += 1
        used.add((m.start(), m.end()))
        if not common:
            bad.append((ctx, a, b, sorted(kp)[:4], sorted(kr)[:4]))
            print(f"[{tag}] NO-BIND ...{ctx[-90:]} || {a} / {b} || P:{sorted(kp)[:4]} R:{sorted(kr)[:4]}")
        else:
            print(f"[{tag}] ok ...{ctx[-70:]} || {a[0]}/{b[0]} -> {[c for c in common if 'B=16' in c or 'twin' in c][:6] or common[:6]}")
    # single triples not inside a pair
    for m in SING.finditer(text):
        if any(s <= m.start() < e for s, e in used):
            continue
        a = m.group(1, 2, 3)
        kp = IP.get(a, []) ; kr = IR.get(a, [])
        ctx = text[max(0, m.start() - 90):m.start()].replace("\n", " ")
        print(f"[{tag}] SINGLE ...{ctx[-80:]} || {a} -> P:{kp[:4]} R:{kr[:4]}")
    return n_pairs, bad

if __name__ == "__main__":
    src, tag = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    n, bad = check(text, tag)
    print(tag, "pairs", n, "unbound", len(bad))

"""Critic: independent E1, E11, E12, E13, E14."""
import sys
sys.modules["torch"] = None
import json, re, subprocess, hashlib, html as H, os
from pathlib import Path
import numpy as np

REPO = Path(r"C:\Users\Michael\Desktop\SaaS\amber"); R = REPO / "results"
PAY = json.loads((R / "errata_recompute.json").read_text(encoding="utf-8"))["rows"]
def show(c, p): return subprocess.check_output(["git", "-C", str(REPO), "show", f"{c}:{p}"]).decode("utf-8")
out = {}

# ---------------- E1 ----------------
print("E1")
enc = json.loads(show("6672db4", "results/p4/encode_meta.json")); gm = json.loads(show("6672db4", "results/p1/generate/meta.json"))
p1 = json.loads(show("6672db4", "results/p1_divergence.json"))
arch = show("6672db4", "src/amber/real/archive.py").splitlines()
p4 = show("6672db4", "experiments/p4_real_archive.py")
es = p4[p4.index("def encode_stage"):p4.index("def decode_stage")]
calls = re.findall(r"load_model\(\s*([^,\)]+)", es)
# what is a.draft's default?
dflt = re.findall(r'add_argument\(\s*"--draft"[^)]*default\s*=\s*([^,\)]+)', p4)
draft_const = re.findall(r'^DRAFT\s*=\s*(.+)$', p4, flags=re.M)
mine = {"encode_meta_draft": enc["draft"], "encode_meta_model_id": enc["model"]["id"], "p1_generate_target": gm["target"],
        "p1_divergence_draft": p1["draft"], "p1_divergence_target": p1["target"], "archive_py_line1": arch[0], "archive_py_line2": arch[1],
        "p4_encode_stage_load_model_arg": calls[0] if calls else None}
print("  load_model calls in encode_stage:", calls, " --draft default:", dflt, draft_const)
print("  encode_meta provenance model_id:", enc.get("provenance", {}).get("model_id"), " snapshot:", enc["model"].get("snapshot"))
d1 = 0
for k, v in mine.items():
    eq = v == PAY["E1"]["value"][k]; d1 = max(d1, 0 if eq else 1); print(f"  {k}: {v!r} equal={eq}")
st = "CORRECTED" if (mine["encode_meta_model_id"] == p1["draft"] and mine["encode_meta_model_id"] != p1["target"]) else ("CONFIRMED" if mine["encode_meta_model_id"] == p1["target"] else "UNRECOMPUTABLE")
out["E1"] = (st, d1); print("  status", st, "payload", PAY["E1"]["status"])

# ---------------- E11 ----------------
print("E11")
import amber.real.archive as A
from amber import binformat as BF
from amber.codec import MAGIC, VERSION, header_digest, payload_digest, DEFAULT_MAX_LENGTH
from amber.rac_codec import CoderParams
print("  DEFAULT_MAX_LENGTH", DEFAULT_MAX_LENGTH, "bomb", DEFAULT_MAX_LENGTH + 1)
model = {"id": "errata-test", "snapshot": None, "dtype": "fp32"}; V = 128256
fp_hex = A.hf_fingerprint(model, V)
P = CoderParams(tie_margin=0.0, tie_topm=2, max_rank=64, vocab_bits=(V - 1).bit_length())

def hf_blob(L, prompt=(1,)):
    # own framing: MAGIC | u32 BE header length | sorted-keys JSON | payload (empty)
    h = {"magic": MAGIC, "version": VERSION, "kind": "hf", "model": dict(model), "vocab_size": V, "prompt_ids": list(prompt),
         "length": L, "n_corrections": 0, "payload_bits": 0, "coder": "gamma", "tie_margin": 0.0, "tie_topm": 2, "max_rank": 64,
         "payload_sha": payload_digest(b""), "content_sha": A.content_digest(np.zeros(L if L < 100 else 0, np.int32)), "fingerprint": fp_hex}
    h["header_sha"] = header_digest(h)
    j = json.dumps(h, sort_keys=True).encode()
    return MAGIC.encode() + len(j).to_bytes(4, "big") + j

def v3_blob(L):
    return BF.pack(model_id=model["id"], snapshot=None, dtype="fp32", fingerprint8=bytes.fromhex(fp_hex), vocab_size=V, coder="gamma", p=P,
                   first_token=1, prompt_len=1, length=L, n_corrections=0, payload=b"", content_sha8=b"\x00" * 8)

def v4_blob(L, ctx=None):
    return BF.pack_session(model_id=model["id"], snapshot=None, dtype="fp32", fingerprint8=bytes.fromhex(fp_hex), vocab_size=V, coder="gamma", p=P,
                           ctx_mode=BF.CTX_RESET if ctx is None else ctx, turns=[{"prompt_len": 1, "gen_len": L, "first_token": 1}], n_corrections=0,
                           payload=b"", content_sha8=b"\x00" * 8)

class Stop(Exception): pass
def run_unpatched(dec, blob, limit=3):
    """Real decoder, real payload_to_symbols; stepper counts calls and stops after `limit` -> proves replay began."""
    calls = {"n": 0}
    def mk():
        def step(new_ids):
            calls["n"] += 1
            if calls["n"] >= limit: raise Stop()
            idx = np.arange(128, dtype=np.int64); val = -np.arange(128, dtype=np.float64)
            return idx, val
        return step
    try:
        dec(blob, mk); return ("returned", calls["n"], None)
    except Stop:
        return ("work_started", calls["n"], None)
    except ValueError as e:
        return ("refused", calls["n"], str(e))
    except Exception as e:
        return (type(e).__name__, calls["n"], str(e))

class WS(Exception): pass
def run_patched(dec, blob):
    orig = A.payload_to_symbols
    def boom(*a, **k): raise WS()
    A.payload_to_symbols = boom
    try:
        dec(blob, lambda: boom); return "returned"
    except WS: return "work_started"
    except ValueError as e: return "refused: " + str(e)
    except Exception as e: return type(e).__name__
    finally: A.payload_to_symbols = orig

paths = {"hf_json": (hf_blob, A.decode_archive), "v3": (v3_blob, A.decode_binary_archive), "v4": (v4_blob, A.decode_session_archive)}
res = {}
for name, (mk, dec) in paths.items():
    for L in (3, DEFAULT_MAX_LENGTH, DEFAULT_MAX_LENGTH + 1):
        if name != "hf_json" and L >= DEFAULT_MAX_LENGTH:
            # check the parser accepts it and what length it reports, then a real (unpatched) decode with a counting stepper
            h = (BF.unpack if name == "v3" else BF.unpack_session)(mk(L))[0]
            info = {k: h[k] for k in ("length", "n_symbols") if k in h} if name == "v3" else {"n_symbols": h["n_symbols"], "turns": h["turns"]}
        else:
            info = None
        pt = run_patched(dec, mk(L))
        up = run_unpatched(dec, mk(L)) if L <= DEFAULT_MAX_LENGTH + 1 else None
        res[(name, L)] = (pt, up)
        print(f"  {name} L={L}: patched={pt}  unpatched={up}  {info if info else ''}")
# also v4 ctx shared, and a much larger v3 length (varint allows up to 2^35-1)
print("  v4 shared ctx bomb:", run_patched(A.decode_session_archive, v4_blob(DEFAULT_MAX_LENGTH + 1, BF.CTX_SHARED if hasattr(BF, 'CTX_SHARED') else 1)))
try:
    h = BF.unpack(v3_blob((1 << 34)))[0]; print("  v3 parser accepts length 2^34:", h["length"])
except Exception as e:
    print("  v3 2^34:", type(e).__name__, e)
pb = PAY["E11"]["value"]
mine_b = {"hf_json": res[("hf_json", DEFAULT_MAX_LENGTH + 1)][0].split(":")[0], "v3": res[("v3", DEFAULT_MAX_LENGTH + 1)][0], "v4": res[("v4", DEFAULT_MAX_LENGTH + 1)][0]}
mine_c = {k: res[(k, 3)][0] for k in paths}
d11 = 0
for k in paths:
    d11 = max(d11, 0 if mine_b[k] == pb["bomb"][k]["outcome"] else 1, 0 if mine_c[k] == pb["control"][k]["outcome"] else 1)
print("  mine bomb", mine_b, "control", mine_c, " payload bomb", {k: v["outcome"] for k, v in pb["bomb"].items()})
print("  hf refusal message mine:", res[("hf_json", DEFAULT_MAX_LENGTH + 1)][0], "| payload:", pb["bomb"]["hf_json"]["message"])
ctrl_ok = all(v == "work_started" for v in mine_c.values())
st = ("CONFIRMED" if all(v == "refused" for v in mine_b.values()) else "CORRECTED") if ctrl_ok else "UNRECOMPUTABLE"
out["E11"] = (st, d11); print("  status", st, "payload", PAY["E11"]["status"])
# Synthetic codec path (F-4's original path) for completeness
from amber import codec as C
try:
    C.Archive.from_bytes(b"")
except Exception as e:
    print("  synthetic Archive.from_bytes(b'') ->", type(e).__name__)

# ---------------- E12 ----------------
print("E12")
from amber.codec import attest_with_target
import inspect
src = inspect.getsource(attest_with_target)
pv = PAY["E12"]["value"]
keys = sorted({"cfg", "path_seed", "draft_seed"} & set(A.HF_REQUIRED))
pl = sum(1 for ln in src.splitlines() if "payload" in ln)
listed = ["experiments/p4_real_archive.py", "experiments/p5_binformat.py", "experiments/p6_sessions.py"] + sorted(p.relative_to(REPO).as_posix() for p in (REPO / "src/amber/real").glob("*.py"))
def cnt(paths):
    n = 0; hits = []
    for p in paths:
        for i, ln in enumerate((REPO / p).read_text(encoding="utf-8").splitlines(), 1):
            if "attest" in ln: n += 1; hits.append(f"{p}:{i}")
    return n, hits
n_listed, _ = cnt(listed)
print(f"  (a) keys {keys}  (b) listed-files count {n_listed}  (c) payload lines {pl}")
# wide grep: whole src/, experiments/, tools/, tests/ (tracked at 20dd31d)
files = subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "20dd31d", "src", "experiments", "tools", "tests"]).decode().split()
pyfiles = [f for f in files if f.endswith(".py")]
n_all, hits = cnt(pyfiles)
by_file = {}
for h in hits: by_file.setdefault(h.rsplit(":", 1)[0], 0); by_file[h.rsplit(":", 1)[0]] += 1
print("  wide grep 'attest' (case-sensitive) per file:", by_file)
# case-insensitive & synonyms
syn = re.compile(r"attest|verify_with_target|L1\b|target.*verif", re.I)
wide = {}
for p in pyfiles:
    for i, ln in enumerate((REPO / p).read_text(encoding="utf-8").splitlines(), 1):
        if syn.search(ln): wide.setdefault(p, []).append(i)
print("  wide grep /attest|verify_with_target|L1|target.*verif/i files:", {k: len(v) for k, v in wide.items()})
# who calls attest_with_target?
callers = {p: [i for i, ln in enumerate((REPO / p).read_text(encoding="utf-8").splitlines(), 1) if "attest_with_target" in ln] for p in pyfiles}
print("  attest_with_target references:", {k: v for k, v in callers.items() if v})
d12 = max(0 if keys == pv["synthetic_keys_in_HF_REQUIRED"] else 1, abs(n_listed - pv["attest_lines_in_real_paths"]), abs(pl - pv["payload_lines_in_attest_with_target"]))
print("  files_searched equal:", listed == pv["files_searched"])
st = "CORRECTED" if (not keys and n_listed == 0) else "CONFIRMED"
out["E12"] = (st, d12); print("  status", st, "payload", PAY["E12"]["status"])

# ---------------- E13 ----------------
print("E13")
pe = PAY["E13"]["value"]
def parse(b):
    t = b.decode("utf-8", errors="replace")
    def metas(n): return [H.unescape(m) for m in re.findall(r'<meta\s+name="%s"\s+content="([^"]*)"' % n, t)]
    return {"title": (metas("citation_title") or [None])[0], "authors": metas("citation_author"), "abstract": (metas("citation_abstract") or [None])[0],
            "pmatic": len(re.findall("pmatic", t, re.I)), "arxiv_id": metas("citation_arxiv_id")}
loc = {}
for aid in ("2601.17684", "2601.10678"):
    b = (R / "errata_web" / f"arxiv_{aid}.html").read_bytes()
    sha = hashlib.sha256(b).hexdigest(); m = parse(b); loc[aid] = m
    print(f"  {aid}: sha ok={sha == pe['pages'][aid]['sha256']} title={m['title']!r} authors={m['authors']} pmatic_in_page={m['pmatic']} "
          f"abstract_has_pmatic={bool(m['abstract']) and 'pmatic' in m['abstract'].lower()} arxiv_id_meta={m['arxiv_id']}")
    if m["abstract"]:
        i = m["abstract"].lower().find("pmatic"); print("    abstract excerpt:", m["abstract"][max(0, i - 120):i + 80] if i >= 0 else m["abstract"][-200:])
d13 = 0
for aid in loc:
    d13 = max(d13, 0 if loc[aid]["title"] == pe["pages"][aid]["title"] else 1, 0 if loc[aid]["authors"] == pe["pages"][aid]["authors"] else 1,
              abs(loc[aid]["pmatic"] - pe["pages"][aid]["pmatic_count_in_page"]))
in_t = {a: bool(loc[a]["title"]) and "pmatic" in loc[a]["title"].lower() for a in loc}
in_a = {a: bool(loc[a]["abstract"]) and "pmatic" in loc[a]["abstract"].lower() for a in loc}
st_pinned = "CONFIRMED" if in_t["2601.17684"] else ("CORRECTED" if in_t["2601.10678"] else "UNRECOMPUTABLE")
st_amended = "CONFIRMED" if in_a["2601.17684"] else ("CORRECTED" if in_a["2601.10678"] else "UNRECOMPUTABLE")
print(f"  status under ORIGINAL pinned rule (citation_title): {st_pinned}; under amended rule (citation_abstract): {st_amended}; payload {PAY['E13']['status']}")
# live re-fetch
import urllib.request, time
for aid in ("2601.17684", "2601.10678"):
    try:
        req = urllib.request.Request(f"https://arxiv.org/abs/{aid}", headers={"User-Agent": "amber-errata-critic/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r: b = r.read()
        Path(__file__).with_name(f"refetch_{aid}.html").write_bytes(b)
        m = parse(b)
        print(f"  refetch {aid}: title={m['title']!r} authors={m['authors']} abstract_has_pmatic={bool(m['abstract']) and 'pmatic' in m['abstract'].lower()} "
              f"same_title={m['title']==loc[aid]['title']} same_abstract={m['abstract']==loc[aid]['abstract']} bytes_identical={hashlib.sha256(b).hexdigest()==pe['pages'][aid]['sha256']}")
    except Exception as e:
        print(f"  refetch {aid} failed: {type(e).__name__}: {e}")
out["E13"] = (st_amended, d13)

# ---------------- E14 ----------------
print("E14")
on_disk = (R / "p7").exists()
tracked20 = subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "20dd31d", "results/p7"]).decode().split()
trackedH = subprocess.check_output(["git", "-C", str(REPO), "ls-files", "results/p7"]).decode().split()
p7ish = sorted(p.name for p in R.iterdir() if "p7" in p.name.lower())
p7any = subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "20dd31d"]).decode().split()
p7files = [f for f in p7any if "p7" in f.lower()]
print(f"  results/p7 on disk={on_disk} tracked@20dd31d={len(tracked20)} tracked@HEAD={len(trackedH)}; results entries with 'p7': {p7ish}; tracked files with 'p7': {p7files}")
ran = on_disk or len(trackedH) > 0
d14 = max(0 if ran == PAY["E14"]["value"]["ran"] else 1, 0 if on_disk == PAY["E14"]["value"]["results_p7_on_disk"] else 1, abs(len(trackedH) - PAY["E14"]["value"]["results_p7_tracked_files"]))
out["E14"] = ("CONFIRMED" if not ran else "CORRECTED", d14); print("  status", out["E14"][0], "payload", PAY["E14"]["status"])
print(out)
json.dump({k: list(v) for k, v in out.items()}, open(Path(__file__).with_suffix(".out.json"), "w"), indent=1)

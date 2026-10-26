import subprocess, hashlib, re, sys
from pathlib import Path
C = Path(r"C:/Users/<user>/AppData/Local/Temp/claude/c--Users-<user>-Desktop-Research-sideband/d880d7a7-5b03-4222-a6bf-23f7b5705b02/scratchpad/evid1/clone_fix")
def git(*a): return subprocess.run(["git", *a], cwd=C, capture_output=True, text=True).stdout
def run():
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-o", "pythonpath=src", "tests/test_evidence_bytes.py", "-k", "outside_results"], cwd=C, capture_output=True, text=True).stdout
    m = [l for l in out.splitlines() if l.startswith("E ") and "AssertionError" in l]
    tail = out.strip().splitlines()[-1]
    return (m[0][:150] if m else "-"), tail
status0 = git("status", "--short"); idx0 = git("ls-files", "-s")
TW, VAL, CIT = "tools/run_fullfree_twin.py", "data/prompts_oq15_val.jsonl", "docs/IDEAS.md"
orig = {p: (C / p).read_bytes() for p in (TW, VAL, CIT)}
assert b"\r\n" not in orig[TW] and b"\r\n" in orig[VAL]
def restore():
    for p, b in orig.items(): (C / p).write_bytes(b)
    git("reset", "-q", "--", TW)
try:
    (C / TW).write_bytes(orig[TW] + b"x"); print("2 byte appended:", run()); restore()
    twin = hashlib.sha256(orig[TW].replace(b"\n", b"\r\n")).hexdigest().encode()
    (C / CIT).write_bytes(orig[CIT] + b"\n" + twin + b"\n"); print("3 crlf twin planted:", run()); restore()
    (C / VAL).write_bytes(orig[VAL].replace(b"\r\n", b"\n")); print("4 crlf data re-saved LF:", run()); restore()
    (C / TW).write_bytes(orig[TW].replace(b"\n", b"\r\n")); print("5 lf instrument re-saved CRLF:", run())
    git("add", "--renormalize", "--", TW); print("   staged:", git("ls-files", "-s", TW).split()[1][:12]); print("6 stale renormalised:", run())
finally:
    restore()
print("status same:", git("status", "--short") == status0, "index same:", git("ls-files", "-s") == idx0)
print("after:", run())

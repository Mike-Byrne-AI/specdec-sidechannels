#!/usr/bin/env python3
"""Critic, second batch (E15/E16), task A: provenance of results/errata_recompute_2.json.

Standalone (no imports from experiments/errata_*). Read-only git plumbing only.
Checks: every provenance.inputs blob id == `git rev-parse <head>:<path>`; the
protocol's second-batch source table == git at 509ad90 (and whether each source
moved between 509ad90 and the payload head); the payload file has no CR bytes
and equals its HEAD blob; script/lib LF-normalised sha256 vs the committed files.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = "results/errata_recompute_2.json"


def git(*a, binary=False):
    out = subprocess.check_output(["git", "-C", str(REPO), *a], stderr=subprocess.DEVNULL)
    return out if binary else out.decode().strip()


def rev(commit, path):
    try:
        return git("rev-parse", f"{commit}:{path}")
    except subprocess.CalledProcessError:
        return None


def main():
    res = {}
    raw = (REPO / PAYLOAD).read_bytes()
    d = json.loads(raw)
    pv = d["provenance"]; head = pv["head"]
    res["payload_head"] = head
    res["payload_cr_bytes"] = raw.count(b"\r")
    head_blob = git("show", f"HEAD:{PAYLOAD}", binary=True)
    res["payload_equals_HEAD_blob"] = head_blob == raw
    res["payload_HEAD_blob_id"] = rev("HEAD", PAYLOAD)
    res["payload_in_head_commit"] = rev(head, PAYLOAD)          # expected None: written at b35e126, committed later
    res["tree_matches"] = git("rev-parse", f"{head}^{{tree}}") == pv["tree"]
    # inputs
    bad = {}
    for p, bid in pv["inputs"].items():
        g = rev(head, p)
        if g != bid:
            bad[p] = {"payload": bid, "git": g}
    res["inputs_n"] = len(pv["inputs"]); res["inputs_mismatch"] = bad
    res["script_blob_matches"] = rev(head, "experiments/errata_recompute.py") == pv["script_blob"]
    for key, path in (("script_sha256_lf", "experiments/errata_recompute.py"), ("lib_sha256_lf", "experiments/errata_lib.py")):
        b = git("show", f"{head}:{path}", binary=True)
        res[key + "_matches_committed_at_head"] = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
        b2 = git("show", f"HEAD:{path}", binary=True)
        res[key + "_matches_committed_at_HEAD"] = hashlib.sha256(b2.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
    # protocol second-batch source table (at HEAD's protocol text)
    proto = git("show", "HEAD:experiments/ERRATA_PROTOCOL.md")
    start = proto.index("2026-10-10, second batch (rows E15 and E16)")
    seg = proto[start:proto.index("### E15", start)]
    table = re.findall(r"^\| ([^|]+?) \| ([0-9a-f]{40}) \|", seg, flags=re.M)
    tbad = {}; moved = {}; vs_payload = {}
    for path, bid in table:
        path = path.strip()
        g = rev("509ad90", path)
        if g != bid:
            tbad[path] = {"protocol": bid, "git_509ad90": g}
        gh = rev(head, path)
        if gh != bid:
            moved[path] = {"509ad90": bid, head[:7]: gh}
        if path in pv["inputs"] and pv["inputs"][path] != bid:
            vs_payload[path] = {"protocol": bid, "payload": pv["inputs"][path]}
    res["protocol_table_n"] = len(table); res["protocol_table_mismatch_at_509ad90"] = tbad
    res["protocol_sources_moved_509ad90_to_head"] = moved
    res["protocol_table_paths_missing_from_payload_inputs"] = [p.strip() for p, _ in table if p.strip() not in pv["inputs"]]
    res["protocol_vs_payload_inputs_differ"] = vs_payload
    res["protocol_pinned_tree"] = git("rev-parse", "509ad90^{tree}")
    # git ancestry: 509ad90 -> cfb9595 -> b35e126 -> 861c553
    res["log"] = git("log", "--format=%h %ad %s", "--date=iso", "509ad90^..HEAD").splitlines()
    text = json.dumps(res, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

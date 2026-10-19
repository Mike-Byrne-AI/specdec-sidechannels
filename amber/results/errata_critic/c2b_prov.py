#!/usr/bin/env python3
"""Critic, second batch, SECOND pass, task A: provenance of the regenerated results/errata_recompute_2.json.

Standalone, read-only git plumbing. Checks: every provenance.inputs id == `git rev-parse <head>:<path>`;
tree, script blob, LF-normalised sha256 of script and lib; no CR bytes; payload == HEAD blob; the
second-batch source table still equals git at 509ad90; the protocol blob the F-15 regime line cites;
the two dry runs (pre-amendment and post-field) and the payload write time.
"""
import datetime
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


def ts(u):
    return datetime.datetime.fromtimestamp(u).isoformat()


def main():
    res = {}
    raw = (REPO / PAYLOAD).read_bytes(); d = json.loads(raw); pv = d["provenance"]; head = pv["head"]
    res.update({"HEAD": git("rev-parse", "HEAD"), "payload_head": head, "payload_cr_bytes": raw.count(b"\r"),
                "payload_equals_HEAD_blob": git("show", f"HEAD:{PAYLOAD}", binary=True) == raw, "payload_HEAD_blob_id": rev("HEAD", PAYLOAD),
                "tree_matches": git("rev-parse", f"{head}^{{tree}}") == pv["tree"], "clean_tracked_tree_selfreported": pv["clean_tracked_tree"],
                "payload_written": ts(pv["written_unix"])})
    bad = {p: {"payload": bid, "git": rev(head, p)} for p, bid in pv["inputs"].items() if rev(head, p) != bid}
    res["inputs_n"] = len(pv["inputs"]); res["inputs_mismatch"] = bad
    res["script_blob_matches"] = rev(head, "experiments/errata_recompute.py") == pv["script_blob"]
    for key, path in (("script_sha256_lf", "experiments/errata_recompute.py"), ("lib_sha256_lf", "experiments/errata_lib.py")):
        for c in (head, "HEAD"):
            b = git("show", f"{c}:{path}", binary=True)
            res[f"{key}_matches_at_{c[:7]}"] = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
    proto = git("show", "HEAD:experiments/ERRATA_PROTOCOL.md")
    start = proto.index("2026-10-10, second batch (rows E15 and E16)"); seg = proto[start:proto.index("### E15", start)]
    table = re.findall(r"^\| ([^|]+?) \| ([0-9a-f]{40}) \|", seg, flags=re.M)
    res["protocol_table_n"] = len(table)
    res["protocol_table_mismatch_at_509ad90"] = {p.strip(): bid for p, bid in table if rev("509ad90", p.strip()) != bid}
    res["protocol_sources_moved_509ad90_to_payload_head"] = {p.strip(): rev(head, p.strip()) for p, bid in table if rev(head, p.strip()) != bid}
    res["protocol_blob_at_cfb9595"] = rev("cfb9595", "experiments/ERRATA_PROTOCOL.md")
    res["protocol_blob_at_payload_head"] = rev(head, "experiments/ERRATA_PROTOCOL.md")
    for f in ("results/errata_dryruns/dry_b2_pre.json", "results/errata_dryruns/dry_b2.json"):
        r2 = (REPO / f).read_bytes(); dd = json.loads(r2); p2 = dd["provenance"]
        res[f] = {"cr_bytes": r2.count(b"\r"), "head": p2["head"][:7], "clean": p2["clean_tracked_tree"], "written": ts(p2["written_unix"]),
                  "script_sha256_lf": p2["script_sha256_lf"][:12], "lib_sha256_lf": p2["lib_sha256_lf"][:12],
                  "statuses": {k: v["status"] for k, v in dd["rows"].items()},
                  "has_encoder_top2_gap_quantiles": "encoder_top2_gap_quantiles" in dd["rows"]["E16"]["value"]}
    res["log"] = git("log", "--format=%h %ad %s", "--date=iso", "509ad90^..HEAD").splitlines()
    text = json.dumps(res, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

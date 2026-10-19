#!/usr/bin/env python3
"""Critic, third batch, task A: provenance of results/errata_recompute_3.json, read-only git plumbing.

Checks: provenance.inputs == git at the payload head; the protocol's third-batch source table == git at 168efb0
(and the three sideband harvest files against their pinned sha256 prefixes); the third-batch sources present in
provenance.inputs; LF and HEAD blob; tree, script blob, LF-normalised sha256 of script and lib; protocol append-only
168efb0 -> head -> HEAD; which files each third-batch commit touches; dry_b3.json against the payload.
"""
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = "results/errata_recompute_3.json"
HARVEST = Path(r"C:\Users\Michael\Desktop\Research\sideband\harvest\amber-lockstep-review-2026-10-09")


def git(*a, binary=False):
    out = subprocess.check_output(["git", "-C", str(REPO), *a], stderr=subprocess.DEVNULL)
    return out if binary else out.decode().strip()


def rev(c, p):
    try:
        return git("rev-parse", f"{c}:{p}")
    except subprocess.CalledProcessError:
        return None


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def main():
    res = {}
    raw = (REPO / PAYLOAD).read_bytes(); P = json.loads(raw); pv = P["provenance"]; head = pv["head"]
    res.update({"HEAD": git("rev-parse", "HEAD")[:7], "payload_head": head[:7], "cr_bytes": raw.count(b"\r"),
                "equals_HEAD_blob": git("show", f"HEAD:{PAYLOAD}", binary=True) == raw, "HEAD_blob": rev("HEAD", PAYLOAD),
                "tree_ok": git("rev-parse", f"{head}^{{tree}}") == pv["tree"], "script_blob_ok": rev(head, "experiments/errata_recompute.py") == pv["script_blob"],
                "clean_selfreported": pv["clean_tracked_tree"], "batch": pv.get("batch"), "written": datetime.datetime.fromtimestamp(pv["written_unix"]).isoformat()})
    res["inputs_n"] = len(pv["inputs"]); res["inputs_mismatch"] = {p: b for p, b in pv["inputs"].items() if rev(head, p) != b}
    for key, path in (("script_sha256_lf", "experiments/errata_recompute.py"), ("lib_sha256_lf", "experiments/errata_lib.py")):
        b = git("show", f"{head}:{path}", binary=True); res[key + "_ok"] = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
    proto = git("show", "HEAD:experiments/ERRATA_PROTOCOL.md")
    s = proto.index("2026-10-11 UTC, third batch (rows E17, E18 and E19)"); seg = proto[s:proto.index("### E17", s)]
    table = re.findall(r"^\| ([^|]+?) \| ([0-9a-f]{40}) \|", seg, flags=re.M)
    res["protocol_table_n"] = len(table)
    res["protocol_table_mismatch_at_168efb0"] = {p.strip(): b for p, b in table if rev("168efb0", p.strip()) != b}
    res["protocol_table_moved_168efb0_to_payload_head"] = {p.strip(): rev(head, p.strip()) for p, b in table if rev(head, p.strip()) != b}
    res["protocol_table_missing_from_payload_inputs"] = [p.strip() for p, b in table if p.strip() not in pv["inputs"]]
    hv = re.findall(r"`(scratchpad/[^`]+)` \(untracked agent output\) \| sha256 ([0-9a-f]+) \|", seg)
    res["harvest_files"] = {p: {"pinned": h, "actual_prefix": hashlib.sha256((HARVEST / p).read_bytes()).hexdigest()[:len(h)] if (HARVEST / p).exists() else None}
                            for p, h in hv}
    res["protocol_168efb0_prefix_of_head"] = git("show", f"{head}:experiments/ERRATA_PROTOCOL.md", binary=True).startswith(git("show", "168efb0:experiments/ERRATA_PROTOCOL.md", binary=True))
    res["protocol_head_prefix_of_HEAD"] = git("show", "HEAD:experiments/ERRATA_PROTOCOL.md", binary=True).startswith(git("show", f"{head}:experiments/ERRATA_PROTOCOL.md", binary=True))
    res["commits"] = {c: git("show", "--stat", "--format=%h %ad %s", "--date=iso", c).splitlines() for c in ("04dbf23", "a90c107", "5b5664f", "727338d", "1ac19bf")}
    dry = json.loads((REPO / "results/errata_dryruns/dry_b3.json").read_bytes()); dp = dry["provenance"]
    fd, fp = dict(flatten(dry["rows"])), dict(flatten(P["rows"]))
    res["dry_b3"] = {"head": dp["head"][:7], "clean": dp["clean_tracked_tree"], "written": datetime.datetime.fromtimestamp(dp["written_unix"]).isoformat(),
                     "script_sha256_lf_equal": dp["script_sha256_lf"] == pv["script_sha256_lf"], "lib_sha256_lf_equal": dp["lib_sha256_lf"] == pv["lib_sha256_lf"],
                     "statuses": {k: v["status"] for k, v in dry["rows"].items()}, "shared": len(set(fd) & set(fp)),
                     "changed": [k for k in set(fd) & set(fp) if fd[k] != fp[k]], "only_dry": sorted(set(fd) - set(fp)), "only_payload": sorted(set(fp) - set(fd)),
                     "cr_bytes": (REPO / "results/errata_dryruns/dry_b3.json").read_bytes().count(b"\r")}
    text = json.dumps(res, indent=1) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Critic, third batch, THIRD (narrow) pass: the changes since the second pass, read-only.

1. Provenance of the payload regenerated at 70b6dcc (inputs at its head, LF, equals the HEAD blob, script/lib sha256,
   protocol append-only) and every leaf of rows.* against the payload at d1a9f9d (blob bacc8f64): which changed.
2. The restored E18 pinned prediction keys equal the third-batch entry's printed values, and their hit/miss at the
   prediction's own precision against the pinned payload keys.
3. The generated text (the generator's planner, in memory; nothing written): predictions line, caveats sentence, source
   line, E19 bracket. torch blocked.
"""
import sys

sys.modules["torch"] = None
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

REPO = Path(__file__).resolve().parents[2]; PAYLOAD = "results/errata_recompute_3.json"


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
    out = {}
    raw = (REPO / PAYLOAD).read_bytes(); P = json.loads(raw); pv = P["provenance"]; head = pv["head"]
    out["provenance"] = {"HEAD": git("rev-parse", "HEAD")[:7], "payload_head": head[:7], "cr_bytes": raw.count(b"\r"),
                         "equals_HEAD_blob": git("show", f"HEAD:{PAYLOAD}", binary=True) == raw, "HEAD_blob": rev("HEAD", PAYLOAD),
                         "inputs_n": len(pv["inputs"]), "inputs_mismatch": {p: b for p, b in pv["inputs"].items() if rev(head, p) != b},
                         "tree_ok": git("rev-parse", f"{head}^{{tree}}") == pv["tree"], "script_blob_ok": rev(head, "experiments/errata_recompute.py") == pv["script_blob"],
                         "clean_selfreported": pv["clean_tracked_tree"],
                         "protocol_append_only_2c5e06a_to_head": git("show", f"{head}:experiments/ERRATA_PROTOCOL.md", binary=True).startswith(
                             git("show", "2c5e06a:experiments/ERRATA_PROTOCOL.md", binary=True))}
    for key, path in (("script_sha256_lf", "experiments/errata_recompute.py"), ("lib_sha256_lf", "experiments/errata_lib.py")):
        b = git("show", f"{head}:{path}", binary=True); out["provenance"][key + "_ok"] = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
    old = dict(flatten(json.loads(git("show", f"bacc8f641313710dab1d15231ed8801efbe75def", binary=True))["rows"])); new = dict(flatten(P["rows"]))
    sh = set(old) & set(new)
    out["vs_bacc8f64"] = {"shared": len(sh), "changed": sorted(k for k in sh if old[k] != new[k]), "removed": sorted(set(old) - set(new)), "added": sorted(set(new) - set(old))}
    # restored pinned predictions against the entry's printed values and the pinned payload keys
    e18 = P["rows"]["E18"]; pred = e18["prediction"]; v = e18["value"]
    entry = {"amber_v3_arch": 4.181, "zstd_arch_none": 6.251, "zstd_arch_4096": 4.737, "zstd_arch_16384": 4.446, "zstd_arch_65536": 4.408,
             "rep_below_half_amber_v3_arch": 5.253, "rep_below_half_zstd_arch_16384": 10.330}
    proto = git("show", "HEAD:experiments/ERRATA_PROTOCOL.md")
    out["entry_text_has_values"] = all(s in proto for s in ("amber v3 4.181, zstd-19 6.251", "4.737 (4 KB), 4.446 (16 KB), 4.408 (64 KB)", "amber\n  5.253 against 10.330"))
    score = {}
    for k, pv_ in pred.items():
        nd = len(str(pv_).split(".")[1]) if "." in str(pv_) else 0
        score[k] = {"pred": pv_, "value": v.get(k), "hit": round(v[k], nd) == round(pv_, nd) if k in v else None}
    out["E18_prediction"] = {"restored_equal_entry": all(pred.get(k) == x for k, x in entry.items()), "score": score,
                             "sources": {k: v["prediction_sources"].get(k) for k in pred}}
    # text
    sys.path.insert(0, str(REPO / "experiments"))
    import errata_text as T
    edits = T.plan_edits(P, "F-16")
    blk = [t for _, t in edits["FINDINGS.md"] if t.lstrip().startswith("## F-16")][0].split("\n")
    out["text"] = {"predictions": [ln for ln in blk if ln.startswith("- predictions")][0],
                   "caveats_mass_sentence": re.search(r"its escape costs are[^.;]*", [ln for ln in blk if ln.startswith("- caveats")][0]).group(0),
                   "source": [ln for ln in blk if ln.startswith("- source:")][0],
                   "e19_bracket": re.search(r"  - E19 \[(.*?)\] F-10", "\n".join(blk), flags=re.S).group(1),
                   "kept_positions_mentioned": "kept positions" in "\n".join(t for _, ins in edits.items() for _, t in ins)}
    text = json.dumps(out, indent=1, default=float) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

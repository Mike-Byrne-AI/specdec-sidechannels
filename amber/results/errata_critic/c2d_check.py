#!/usr/bin/env python3
"""Critic, second batch, FOURTH (narrow) pass: the changes since the third pass, read-only.

1. Provenance of the payload regenerated at 980597b (inputs at its head, LF, equals the HEAD blob, script/lib sha256).
2. Every leaf of rows.E15/E16 other than the new E16 value.prediction_sources equals the payload at 3cec4df.
3. The E15 failure-metric sentence's numbers, recomputed from the raw sources independently of the payload:
   C-caused failures = C first desyncs / archives (P4 report first_desync_class_counts), the C-hazards-only
   theta-0 whole-archive failure prediction from the P2b theta-0 row and the P4 symbol streams, and
   k = (O/n - p) / sqrt(p (1 - p) / n).
4. The generated text (the generator's own planner, in memory; nothing written): the sentence, the labels,
   the title/README wording, the regime line, the caveats rule, the predictions line.
torch is blocked.
"""
import sys

sys.modules["torch"] = None
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]; RES = REPO / "results"; R = 64
PAYLOAD = "results/errata_recompute_2.json"


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
                         "inputs_mismatch": {p: b for p, b in pv["inputs"].items() if rev(head, p) != b}, "inputs_n": len(pv["inputs"]),
                         "tree_ok": git("rev-parse", f"{head}^{{tree}}") == pv["tree"], "script_blob_ok": rev(head, "experiments/errata_recompute.py") == pv["script_blob"],
                         "clean_selfreported": pv["clean_tracked_tree"]}
    for key, path in (("script_sha256_lf", "experiments/errata_recompute.py"), ("lib_sha256_lf", "experiments/errata_lib.py")):
        b = git("show", f"{head}:{path}", binary=True)
        out["provenance"][key + "_ok"] = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == pv[key]
    out["provenance"]["protocol_append_only_05c3305_to_head"] = git("show", f"{head}:experiments/ERRATA_PROTOCOL.md", binary=True).startswith(
        git("show", "05c3305:experiments/ERRATA_PROTOCOL.md", binary=True))
    # 2. unchanged from 3cec4df
    old = dict(flatten(json.loads(git("show", f"3cec4df:{PAYLOAD}", binary=True))["rows"])); new = dict(flatten(P["rows"]))
    out["vs_3cec4df"] = {"shared": len([k for k in old if k in new]), "changed": [k for k in old if k in new and old[k] != new[k]],
                         "removed": [k for k in old if k not in new], "added": [k for k in new if k not in old]}
    out["E16_prediction_sources"] = P["rows"]["E16"]["value"]["prediction_sources"]
    # 3. the failure-metric numbers from raw sources
    b = json.loads((RES / "p2b_escape_robustness.json").read_text()); p4 = json.loads((RES / "p4_real_archive.json").read_text())["report"]
    streams = []
    for f in sorted(glob.glob(str(RES / "p4/archives/row_*_symbols.npz"))):
        with np.load(f) as z:
            fl = z["flag"].astype(int); rk = z["rank"].astype(np.int64)
        streams.append(np.where(fl == 3, R + 1, rk))
    calc = {}
    for D, arm in (("cuda_bf16_b1", "cuda_bf16"), ("cuda_fp16_b1", "cuda_fp16")):
        row0 = [r for r in b["report"]["cpu_fp32"]["decoders"][D] if r["theta"] == 0.0][0]
        tab = np.zeros(R + 2)
        for rr, e in row0["C_desync_by_rank"].items():
            tab[int(rr)] = e["desync"] / e["n"]
        p = 1 - float(np.mean([np.prod(1 - tab[np.minimum(s, R + 1)]) for s in streams]))
        m = p4["arms"][arm]; n = m["archives"]; o = sum(v for k, v in m["first_desync_class_counts"].items() if k.startswith("C"))
        calc[D] = {"O": o, "n": n, "rate": o / n, "p": p, "k": (o / n - p) / math.sqrt(p * (1 - p) / n),
                   "payload_p": P["rows"]["E15"]["value"]["arms"][D]["fail_exact"]["c_only_theta0_h4"]["fail_rate"],
                   "payload_O": P["rows"]["E15"]["value"]["arms"][D]["compensator_theta0_h4"]["C"]["observed"]}
        calc[D]["abs_diff_p"] = abs(calc[D]["p"] - calc[D]["payload_p"])
    out["failure_metric"] = calc
    # 4. the text
    sys.path.insert(0, str(REPO / "experiments"))
    import errata_text as T
    edits = T.plan_edits(P, "F-15"); texts = {f: [t for _, t in ins] for f, ins in edits.items()}
    allt = "\n".join(t for ts in texts.values() for t in ts)
    m = re.search(r"on the failure metric, C-caused failures are .*?binomial sd of the predicted rate(, within noise)?\.", allt)
    out["text"] = {"failure_sentence": m.group(0) if m else None,
                   "expected_fragment": (f"{100 * calc['cuda_bf16_b1']['rate']:.1f}% and {100 * calc['cuda_fp16_b1']['rate']:.1f}% "
                                         f"({calc['cuda_bf16_b1']['O']} and {calc['cuda_fp16_b1']['O']} of {calc['cuda_bf16_b1']['n']}) against "
                                         f"{100 * calc['cuda_bf16_b1']['p']:.1f}% and {100 * calc['cuda_fp16_b1']['p']:.1f}% with correction hazards alone: "
                                         f"the same direction, by {calc['cuda_bf16_b1']['k']:.1f} and {calc['cuda_fp16_b1']['k']:.1f} binomial sd"),
                   "old_overstatement_present": "so the correction excess holds on both metrics" in allt,
                   "claim_site_statuses_in_title_and_readme": [("claim-site statuses" in t) for t in texts["README.md"] + [x for x in texts["FINDINGS.md"] if x.lstrip().startswith("## F-15")]],
                   "pointer_labels": {f: [t.split(":")[0][:40] for t in ts if not t.lstrip().startswith("## F-15")] for f, ts in texts.items()}}
    blk = [x for x in texts["FINDINGS.md"] if x.lstrip().startswith("## F-15")][0].split("\n")
    out["text"]["title"] = [ln for ln in blk if ln.startswith("## F-15")][0]
    out["text"]["regime"] = [ln for ln in blk if ln.startswith("- regime:")][0]
    out["text"]["predictions"] = [ln for ln in blk if ln.startswith("- predictions")][0]
    out["text"]["caveats_label_rule"] = re.search(r"labelled erratum[^.]*\.", [ln for ln in blk if ln.startswith("- caveats")][0]).group(0)
    out["text"]["readme_note"] = [t for t in texts["README.md"] if t.startswith("> Second")][0]
    out["text"]["finding_line"] = [ln for ln in blk if ln.startswith("- finding:")][0]
    text = json.dumps(out, indent=1, default=float) + "\n"
    Path(__file__).with_suffix(".out.json").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

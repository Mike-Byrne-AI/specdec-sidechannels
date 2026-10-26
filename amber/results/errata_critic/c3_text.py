#!/usr/bin/env python3
"""Critic, third batch: the generated F-16 text, read-only (payload results/errata_recompute_3.json at 5b5664f).

Uses the generator's own plan (experiments/errata_text.plan_edits / insert_lines, the code that would
write) to build every insertion IN MEMORY (nothing is written), then:
  1. shows where each insertion lands (the text around it in the would-be file), including the order of
     the two insertions that share FINDINGS.md's last line (F-15's note line and the F-16 block);
  2. traces every numeral in every insertion to a payload value (rows.E17 / rows.E18 / rows.E19 / provenance) under
     common renderings, to a quoted claim string, or to structure (line refs, ids); prints the rest.
torch is blocked.
"""
import sys

sys.modules["torch"] = None
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "experiments"))
import errata_text as T  # noqa: E402  (read-only use of the planner)

NUM = re.compile(r"(?<![A-Za-z_\-])[+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?%?")


def flatten(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flatten(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flatten(v, f"{p}[{i}]")
    else:
        yield p, x


def renderings(x):
    out = set()
    try:
        x = float(x)
    except (TypeError, ValueError):
        return out
    for v in (x, 100 * x):
        if v == int(v):
            out.add(str(int(v)))
        for d in range(0, 5):
            out.add(f"{v:.{d}f}")
        for d in range(0, 4):
            out.add(f"{v:.{d}e}")
        for sf in range(1, 7):
            out.add(f"{v:.{sf}g}")
    return out


def main():
    P = json.loads((REPO / "results/errata_recompute_3.json").read_text(encoding="utf-8"))
    edits = T.plan_edits(P, "F-16")
    report = {"placement": {}, "untraced": {}}
    for file, ins in edits.items():
        lines = T.read_lf(REPO / file)[0].split("\n")
        new = T.insert_lines(lines, ins)
        # where each insertion lands
        pl = []
        for i, text in ins:
            k = new.index(text)
            pl.append({"after_line": i + 1, "prev_line": new[k - 1][:90], "first_chars": text.strip()[:70], "next_line": (new[k + 1][:70] if k + 1 < len(new) else None)})
        report["placement"][file] = pl
    # values
    vals = set()
    for key in ("E17", "E18", "E19"):
        for _, v in flatten(P["rows"][key]):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals |= renderings(v)
    for key in ("E17", "E18", "E19"):
        for _, v in flatten(P["rows"][key]):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.add(f"{v:+.1f}")
    struct = set()
    for _, v in flatten(P["rows"]):
        if isinstance(v, str):
            struct |= set(NUM.findall(v))
    for key in ("E17", "E18", "E19"):
        for k in P["rows"][key]:
            if k.startswith("status_by"):
                for kk in P["rows"][key][k]:
                    struct |= set(NUM.findall(kk))
    for _, v in flatten(P["provenance"]):
        struct |= set(NUM.findall(str(v)))
    # claim texts as printed (the payload's claim strings already included); the F-14 sentence quoted
    for file, ins in edits.items():
        unt = []
        for i, text in ins:
            for m in NUM.finditer(text):
                tok = m.group(0)
                bare = tok.rstrip("%").lstrip("+")
                ctx = text[max(0, m.start() - 30): m.end() + 10].replace("\n", " ")
                if tok in vals or bare in vals or tok in struct or bare in struct:
                    continue
                unt.append({"numeral": tok, "context": ctx})
        report["untraced"][file] = unt
    Path(__file__).with_suffix(".out.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()

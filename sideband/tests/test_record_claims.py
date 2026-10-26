"""tests/test_record_claims.py: three record claims that lane B of the 2026-10-15 image audit made
checkable (written 2026-10-16; no torch).

1. docs/BLUEPRINT_INDEX.md's Line column: each row's title sits on its stated line of docs/BLUEPRINT.md.
   The index says its numbers stay valid until a dated insertion above them; lane B inserted a front-matter
   note at the top and regenerated the column by title, and this pin goes red the next time an insertion
   lands without a regeneration.
2. sideband.pipeline.run_simulation keeps steer_mech="argmax" as its parameter default (D-10's dated note of
   2026-10-16: e03, e04 and e05 passed no steer_mech and ran argmax while the decision calls posterior the
   default). A change of the default moves every synthetic rerun; the note is written against this value.
3. src/sideband/real/hf_specdec.py's spec_decode_prompt defaults use_kv_cache=True, read by ast without
   importing the module (it needs torch): the ground of every "crops KV caches by default" sentence the lane
   added, and of the dated note under DECISIONS.md D-9.
"""
from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _lines(rel: str) -> list[str]:
    return (ROOT / rel).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")


def test_blueprint_index_rows_sit_on_their_stated_lines():
    bp = _lines("docs/BLUEPRINT.md")
    rows = [l for l in _lines("docs/BLUEPRINT_INDEX.md") if re.match(r"\| \d+ \| (heading|block) \|", l)]
    assert len(rows) >= 40, "the index table is missing"
    bad = []
    for row in rows:
        n, kind, title = [c.strip() for c in row.strip("|").split("|")[:3]]
        line = bp[int(n) - 1].replace("—", "-").replace("–", "-")
        head = line.lstrip("#").strip() if kind == "heading" else line
        if not head.startswith(title.replace("—", "-")):
            bad.append((n, title[:40], line[:40]))
    assert bad == [], f"index rows whose title is not on the stated line (line, title, found): {bad}"


def test_run_simulation_parameter_default_is_argmax():
    from sideband.pipeline import run_simulation

    assert inspect.signature(run_simulation).parameters["steer_mech"].default == "argmax"


def test_hf_adapter_defaults_to_the_kv_cache_path():
    tree = ast.parse((ROOT / "src/sideband/real/hf_specdec.py").read_bytes().decode("utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "spec_decode_prompt")
    params = fn.args.args + fn.args.kwonlyargs
    defaults = list(fn.args.defaults) + list(fn.args.kw_defaults)
    # positional defaults align to the tail of the positional parameters
    pos = fn.args.args
    pos_defaults = dict(zip([p.arg for p in pos[len(pos) - len(fn.args.defaults):]], fn.args.defaults))
    kw_defaults = {p.arg: d for p, d in zip(fn.args.kwonlyargs, fn.args.kw_defaults)}
    value = pos_defaults.get("use_kv_cache", kw_defaults.get("use_kv_cache"))
    assert value is not None, [p.arg for p in params]
    assert isinstance(value, ast.Constant) and value.value is True, ast.dump(value)
    del defaults

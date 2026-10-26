"""tests/test_harness_doc_claims.py — the hand-written harness facts in CLAUDE.md
and pyproject.toml are witnessed against the code that implements them.

Written 2026-10-01 (failure-mode review of the harness setup lane): CLAUDE.md
copies the plan gate's scope and the frozen-instrument rule by hand, and nothing
mechanical noticed when such a copy drifted. Two witnesses:
  1. the plan gate: the paths CLAUDE.md names as gated are gated and the ones
     it names as exempt are exempt, per `plan_guard._is_exempt` (the hook is
     tracked under tools/cc/hooks/ and imports nothing from the engine);
  2. the frozen instruments: pyproject's ruff `extend-exclude` list equals the
     import closure of the sha-attested instruments (every `tools/*.py` whose
     bytes, in raw, LF or CRLF form, hash to an `instrument` value in a
     committed payload's provenance, plus every tools/ module those import,
     transitively). The three line-ending forms matter: two instruments are
     attested by their CRLF bytes, so an LF checkout (CI) would otherwise miss
     them.
The lists below are the CLAUDE.md sentence spelled out as paths; they are kept
by hand on purpose, so a change to either side shows up here. Nothing here
imports torch, and the TOML is read with a regular expression so the test runs
on Python 3.10 (no tomllib)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "cc" / "hooks"))
import plan_guard  # noqa: E402

# CLAUDE.md, "Harness" section: gated until a plan is in progress ...
GATED = [
    "src/sideband/specdec.py", "tools/run_probes.py", "experiments/run_all.py",
    "results/real/x.json", "data/prompts.jsonl", ".github/workflows/ci.yml",
    "README.md", "CLAUDE.md", "CHANGELOG.md", "CONTRIBUTING.md", "AGENTS.md",
    "Makefile", "pyproject.toml", "setup.cfg", "espalier.toml",
]
# ... and exempt
EXEMPT = [
    "tests/test_x.py", "docs/BLUEPRINT.md", "task-packs/FORWARD_LEDGER.md", "cc/GOAL.md",
    "tools/cc/hooks/plan_guard.py", ".claude/agents/sideband-critic.md", "memory/README.md",
    "reports/repo_fingerprint.json", ".espalier-state/last_tool",
    "FINDINGS.md", "DECISIONS.md", "OPEN_QUESTIONS.md", "HANDOFF.md", "ESPALIER_MEMORY.md",
    "CITATION.cff", ".gitattributes", ".gitignore",
]


def test_plan_gate_scope_matches_claude_md():
    gated_wrong = [p for p in GATED if plan_guard._is_exempt(p, ROOT)]
    exempt_wrong = [p for p in EXEMPT if not plan_guard._is_exempt(p, ROOT)]
    assert gated_wrong == [], f"CLAUDE.md calls these gated; plan_guard exempts them: {gated_wrong}"
    assert exempt_wrong == [], f"CLAUDE.md calls these exempt; plan_guard gates them: {exempt_wrong}"


def _forms(b: bytes) -> set[str]:
    """sha256 of the bytes as they are, LF-normalised, and CRLF-normalised."""
    lf = b.replace(b"\r\n", b"\n")
    return {hashlib.sha256(x).hexdigest() for x in (b, lf, lf.replace(b"\n", b"\r\n"))}


def _attested_instruments() -> set[str]:
    shas: set[str] = set()
    for payload in ROOT.glob("results/**/*.json"):
        try:
            d = json.loads(payload.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        prov = d.get("provenance") if isinstance(d, dict) else None
        if not isinstance(prov, dict):
            continue
        for k, v in prov.items():
            if "instrument" in k and isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v):
                shas.add(v)
    return {tool.stem for tool in ROOT.glob("tools/*.py") if _forms(tool.read_bytes()) & shas}


def _import_closure(stems: set[str]) -> set[str]:
    seen, frontier = set(stems), list(stems)
    while frontier:
        src = (ROOT / "tools" / f"{frontier.pop()}.py").read_text(encoding="utf-8", errors="replace")
        for dep in re.findall(r"^\s*(?:from|import)\s+(\w+)", src, flags=re.M):
            if (ROOT / "tools" / f"{dep}.py").exists() and dep not in seen:
                seen.add(dep)
                frontier.append(dep)
    return seen


def _ruff_exclusions() -> tuple[bool, set[str]]:
    """(force-exclude on?, the tools/*.py entries of extend-exclude) from pyproject.toml."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = text[text.index("[tool.ruff]"):]
    if "\n[tool.ruff.lint]" in section:
        section = section[: section.index("\n[tool.ruff.lint]")]
    force = re.search(r"^force-exclude\s*=\s*true\s*$", section, flags=re.M) is not None
    m = re.search(r"extend-exclude\s*=\s*\[(.*?)\]", section, flags=re.S)
    entries = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    return force, {e for e in entries if e.startswith("tools/") and e.endswith(".py")}


def test_ruff_excludes_exactly_the_frozen_instrument_closure():
    attested = _attested_instruments()
    assert attested, "no sha-attested instrument found under results/"
    frozen = {f"tools/{s}.py" for s in _import_closure(attested)}
    force, excluded = _ruff_exclusions()
    assert force, "force-exclude must be on, or an explicit path bypasses the exclusion"
    assert excluded == frozen, f"ruff extend-exclude {sorted(excluded)} != frozen closure {sorted(frozen)}"

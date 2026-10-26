"""The sideband-critic lane in the espalier harness (adopted 2026-10-01): the
three managed command bodies carry the lane with one mode sentence and one
canonical research-record surface, the unmanaged skill and agent files exist,
every agent file pins a model (operator rule: never Fable without permission),
and preflight runs the findings lint. A harness re-init regenerates the
managed bodies and drops the lane; this test is what notices
(docs/SHARP_EDGES.md, "Managed harness files regenerate on re-init").
No torch."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ROOT / ".claude" / "commands"
AGENTS = ROOT / ".claude" / "agents"
BODIES = [COMMANDS / name for name in ("preflight.md", "implement-task.md", "implement-pack.md")]
SKILL = ROOT / ".claude" / "skills" / "critic" / "SKILL.md"
AGENT = AGENTS / "sideband-critic.md"
SHARP_EDGES = ROOT / "docs" / "SHARP_EDGES.md"
MEMORY = ROOT / "ESPALIER_MEMORY.md"

MODE_SENTENCE = (
    "ALSO dispatch `sideband-critic` (the `/critic` lens): recompute mode when the diff "
    "touches `results/` or `FINDINGS.md`, diff mode otherwise."
)
# The canonical research-record surface. Every site below must name every token.
SURFACE = (
    "`results/`", "`data/`", "`experiments/`", "`src/sideband/`", "`tools/*.py`",
    "`tests/test_*_landing.py`", "`FINDINGS.md`", "`DECISIONS.md`", "`OPEN_QUESTIONS.md`",
    "`docs/BLUEPRINT.md`", "`docs/WHY_THIS_DIES.md`", "`docs/REPORT.md`",
    "`docs/FINDINGS_INDEX.md`", "`docs/OQ*_*.md`", "`README.md`",
)
LIST_SITES = BODIES + [SKILL, SHARP_EDGES, MEMORY]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _frontmatter(path: Path) -> dict[str, str]:
    text = _read(path)
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, f"{path.name}: no frontmatter"
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def test_lane_present_in_every_gate_with_one_mode_sentence():
    for body in BODIES:
        text = _read(body)
        assert "sideband-critic" in text, f"{body.name}: the critic lane is gone (harness re-init?)"
        assert _norm(MODE_SENTENCE) in _norm(text), f"{body.name}: mode sentence drifted"


def test_gates_carry_no_stale_two_reviewer_wording():
    for body in BODIES:
        text = _norm(_read(body))
        assert "both reports" not in text and "from both" not in text, body.name


def test_canonical_surface_named_at_every_site():
    for site in LIST_SITES:
        text = _read(site)
        missing = [token for token in SURFACE if token not in text]
        assert not missing, f"{site.relative_to(ROOT)}: surface tokens missing {missing}"


def test_skill_and_agent_files_exist_and_are_unmanaged():
    assert SKILL.exists() and AGENT.exists()
    for path in (SKILL, AGENT):
        assert "espalier:managed" not in _read(path), f"{path.name} carries the managed marker"
    assert _frontmatter(SKILL)["name"] == "critic"
    assert _frontmatter(AGENT)["name"] == "sideband-critic"


def test_critic_has_no_write_tool():
    tools = _frontmatter(AGENT)["tools"]
    assert "Write" not in [t.strip() for t in tools.split(",")]


def test_every_agent_file_pins_a_non_fable_model():
    files = sorted(AGENTS.glob("*.md"))
    assert files
    for path in files:
        model = _frontmatter(path).get("model")
        assert model, f"{path.name}: no model line (would inherit the parent session's model)"
        assert "fable" not in model.lower(), f"{path.name}: model is Fable"


def test_preflight_runs_the_findings_lint():
    assert "python tools/lint_findings.py" in _read(COMMANDS / "preflight.md")

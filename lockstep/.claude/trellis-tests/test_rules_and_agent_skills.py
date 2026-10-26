from __future__ import annotations

import re


EXPECTED_RULES = {
    "source-work.md",
    "test-work.md",
    "task-packs.md",
    "project-memory.md",
    "harness-maintenance.md",
}

EXPECTED_AGENT_SKILLS = {
    "run-analyzer.md": ["run-analysis", "verify-workflow", "findings-log"],
    "task-pack-author.md": ["task-pack-format", "decision-record"],
    "finding-investigator.md": ["findings-log", "verify-workflow", "run-analysis"],
}


def test_path_scoped_rules_exist_with_paths_frontmatter(repo_root):
    rules_dir = repo_root / ".claude" / "rules"
    found = {p.name for p in rules_dir.glob("*.md")}
    assert EXPECTED_RULES.issubset(found)
    for name in EXPECTED_RULES:
        text = (rules_dir / name).read_text(encoding="utf-8")
        assert text.startswith("---\n"), name
        assert "paths:" in text.split("---", 2)[1], name


def test_agents_preload_relevant_skills(repo_root):
    for filename, skills in EXPECTED_AGENT_SKILLS.items():
        text = (repo_root / ".claude" / "agents" / filename).read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        assert "skills:" in frontmatter, filename
        for skill in skills:
            assert re.search(rf"^\s*- {re.escape(skill)}$", frontmatter, re.MULTILINE), filename


def test_claude_md_references_rules_without_reinlining_everything(repo_root):
    text = (repo_root / "tools" / "trellis_templates" / "CLAUDE.md.template").read_text(encoding="utf-8")
    assert ".claude/rules/" in text
    assert len(text.splitlines()) < 180

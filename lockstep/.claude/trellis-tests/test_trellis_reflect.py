from __future__ import annotations

from tools.trellis_reflect import check_command_tool_refs, check_markdown_links, reflect


def test_reflect_passes_minimal_project(minimal_project):
    assert reflect(minimal_project) == []


def test_broken_trellis_markdown_link_fails(minimal_project):
    (minimal_project / "trellis-docs" / "trellis-harness.md").write_text("[missing](docs/nope.md)\n", encoding="utf-8")
    issues = check_markdown_links(minimal_project)
    assert any(issue.code == "broken-link" for issue in issues)


def test_host_readme_links_are_outside_installed_reflection_scope(minimal_project):
    (minimal_project / "README.md").write_text("[missing](docs/nope.md)\n", encoding="utf-8")
    issues = check_markdown_links(minimal_project)
    assert not any(issue.path == "README.md" for issue in issues)


def test_command_referencing_missing_tool_fails(minimal_project):
    commands = minimal_project / ".claude" / "commands"
    commands.mkdir(parents=True)
    (commands / "bad.md").write_text("```powershell\npython tools/missing.py\n```\n", encoding="utf-8")
    issues = check_command_tool_refs(minimal_project)
    assert any(issue.code == "missing-tool" for issue in issues)


def test_reflect_skips_unmarked_host_memory(minimal_project):
    (minimal_project / "memory").mkdir()
    (minimal_project / "memory" / "host-note.md").write_bytes(b"\xff\xfe[bad](missing.md)")

    assert reflect(minimal_project) == []


def test_reflect_reports_marked_memory_lint_issues(minimal_project):
    (minimal_project / "memory").mkdir()
    (minimal_project / "memory" / ".trellis-memory").write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    (minimal_project / "memory" / "README.md").write_text("# Memory\n", encoding="utf-8")
    (minimal_project / "memory" / "scratch.md").write_text("temporary\n", encoding="utf-8")

    issues = reflect(minimal_project)

    assert any(issue.code == "memory-root-file" and issue.path == "memory/scratch.md" for issue in issues)

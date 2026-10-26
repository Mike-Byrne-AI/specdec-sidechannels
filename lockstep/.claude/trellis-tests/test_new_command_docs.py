from __future__ import annotations

COMMANDS = {
    "trellis-bootstrap.md": ["python tools/trellis_bootstrap.py", "CLAUDE.md already integrated"],
    "context-load.md": ["python tools/trellis_blueprint.py load", "python tools/trellis_extract_godfile.py --check"],
    "handoff.md": ["python tools/trellis_blueprint.py finalize", "SESSION SUMMARY"],
    "implement-task.md": ["python tools/trellis_plan.py create", "Stop conditions"],
    "implement-pack.md": ["python tools/trellis_pack_lint.py", "single-pack mode only"],
    "reflect.md": ["python tools/trellis_reflect.py --check", "REFLECT"],
}


def test_new_commands_exist_and_reference_real_trellis_tools(repo_root):
    commands_dir = repo_root / ".claude" / "commands"
    for filename, expected_snippets in COMMANDS.items():
        text = (commands_dir / filename).read_text(encoding="utf-8")
        for snippet in expected_snippets:
            assert snippet in text, filename

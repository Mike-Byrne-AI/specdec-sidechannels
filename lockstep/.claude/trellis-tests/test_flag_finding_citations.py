from __future__ import annotations

from conftest import run_hook


def payload(project_root, tool_name="Edit", tool_input=None):
    return {
        "tool_name": tool_name,
        "session_id": "s1",
        "cwd": str(project_root),
        "tool_input": tool_input or {},
    }


def test_edit_new_string_triggers(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, tool_input={
        "file_path": "src/main.py",
        "old_string": "x",
        "new_string": "# Per F1, keep this path\n",
    }))
    assert proc.returncode == 0
    assert "F1" in proc.stderr


def test_str_replace_new_str_triggers(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, "str_replace", {
        "path": "src/main.py",
        "old_str": "x",
        "new_str": "# Finding F2 applies\n",
    }))
    assert "F2" in proc.stderr


def test_write_content_triggers(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, "Write", {
        "file_path": "tools/check.py",
        "content": "# Per F3\n",
    }))
    assert "F3" in proc.stderr


def test_nested_edits_trigger_and_deduplicate(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, tool_input={
        "file_path": "src/main.py",
        "edits": [{"new_string": "# F4\n"}, {"new_string": "# F4 again\n"}],
    }))
    assert proc.stderr.count("F4") >= 1
    assert proc.stderr.count("verify_finding.py F4") == 1


def test_f1_score_and_f1000research_do_not_trigger(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, tool_input={
        "file_path": "src/main.py",
        "new_string": "metric = 'F1-score'; journal = 'F1000Research'; other = 'F1_score'\n",
    }))
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_no_finding_exits_cleanly(repo_root, minimal_project):
    proc = run_hook(repo_root, minimal_project, "flag_finding_citations.py", payload(minimal_project, tool_input={
        "file_path": "src/main.py",
        "new_string": "print('no finding')\n",
    }))
    assert proc.returncode == 0
    assert proc.stderr == ""

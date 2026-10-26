from __future__ import annotations

from tools import trellis_repair_gate


def test_repair_gate_command_list_contains_core_checks():
    labels = [label for label, _command in trellis_repair_gate.COMMANDS]
    assert "compile" in labels
    assert "tests" in labels
    assert "env" in labels
    assert "inventory" in labels
    assert "memory-lint" in labels
    assert "refs" in labels
    assert "godfile-generate" in labels
    assert "godfile-check" in labels


def test_repair_gate_disables_external_pytest_plugins_for_test_command(monkeypatch):
    calls = []

    def fake_run(command, cwd, text, env, **kwargs):
        calls.append((command, cwd, text, env, kwargs))

        class Proc:
            returncode = 0
            stdout = ""

        return Proc()

    monkeypatch.setattr(trellis_repair_gate.subprocess, "run", fake_run)
    assert trellis_repair_gate.run_command("tests", ["python", "-m", "pytest", "-q"]) is True
    assert calls[0][3]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert calls[0][4]["timeout"] == 120
    assert calls[0][4]["stdout"] == trellis_repair_gate.subprocess.DEVNULL


def test_repair_gate_selects_installed_self_tests(tmp_path):
    root = tmp_path / "host"
    (root / ".claude" / "trellis-tests").mkdir(parents=True)
    (root / ".claude" / "trellis-tests" / "conftest.py").write_text("", encoding="utf-8")
    (root / "tests").mkdir()
    assert trellis_repair_gate.trellis_test_paths(root) == [".claude/trellis-tests"]
    assert trellis_repair_gate.trellis_test_paths(root, include_host_tests=True) == [".claude/trellis-tests", "tests"]

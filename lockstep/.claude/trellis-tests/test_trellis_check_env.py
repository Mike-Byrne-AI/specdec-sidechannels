from __future__ import annotations

from tools import trellis_check_env


def test_check_env_uses_project_root_from_nested_cwd(repo_root, tmp_path, monkeypatch, capsys):
    nested = tmp_path / "nested" / "dir"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.setenv("TRELLIS_PROJECT_ROOT", str(repo_root))
    assert trellis_check_env.main() == 0
    out = capsys.readouterr().out
    assert f"Project root: {repo_root}" in out
    assert f"Working dir: {nested.resolve()}" in out
    assert "tools/trellis_templates/CLAUDE.md.template: present" in out

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

try:
    import install_trellis
except ModuleNotFoundError:  # Installed projects keep the installer under tools/trellis_install.py.
    from tools import trellis_install as install_trellis

from tools import trellis_bootstrap


def install_target(repo_root: Path, tmp_path: Path) -> Path:
    target = tmp_path / "host"
    assert install_trellis.install(repo_root, target, force=True, dry_run=False) == 0
    return target


def run_bootstrap(project_root: Path, monkeypatch, *args: str) -> int:
    old = os.environ.get("TRELLIS_PROJECT_ROOT")
    monkeypatch.setenv("TRELLIS_PROJECT_ROOT", str(project_root))
    try:
        return trellis_bootstrap.main(list(args))
    finally:
        if old is None:
            monkeypatch.delenv("TRELLIS_PROJECT_ROOT", raising=False)
        else:
            monkeypatch.setenv("TRELLIS_PROJECT_ROOT", old)


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")


def test_bootstrap_fresh_install_generates_root_claude_and_gitignore(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".gitignore").exists()

    assert run_bootstrap(target, monkeypatch, "--yes") == 0

    claude = (target / "CLAUDE.md").read_text(encoding="utf-8")
    template = (target / "tools" / "trellis_templates" / "CLAUDE.md.template").read_text(encoding="utf-8").strip()
    assert trellis_bootstrap.FENCE_START in claude
    assert template in claude
    assert trellis_bootstrap.FENCE_END in claude
    assert ".claude/GODFILE.md" in (target / ".gitignore").read_text(encoding="utf-8")
    assert (target / ".claude" / "trellis_install_manifest.json").exists()


def test_bootstrap_rerun_is_noop_for_claude_and_gitignore(repo_root, tmp_path, monkeypatch, capsys):
    target = install_target(repo_root, tmp_path)
    assert run_bootstrap(target, monkeypatch, "--yes") == 0
    claude_before = (target / "CLAUDE.md").read_text(encoding="utf-8")
    gitignore_before = (target / ".gitignore").read_text(encoding="utf-8")

    assert run_bootstrap(target, monkeypatch, "--yes") == 0
    output = capsys.readouterr().out

    assert "CLAUDE.md already integrated" in output
    assert "gitignore already merged" in output
    assert (target / "CLAUDE.md").read_text(encoding="utf-8") == claude_before
    assert (target / ".gitignore").read_text(encoding="utf-8") == gitignore_before


def test_bootstrap_gitignore_dedupes_existing_lines(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    (target / ".gitignore").write_text(".claude/GODFILE.md\ncustom.log\n", encoding="utf-8")

    assert run_bootstrap(target, monkeypatch, "--yes") == 0
    text = (target / ".gitignore").read_text(encoding="utf-8")
    assert text.count(".claude/GODFILE.md") == 1
    assert "custom.log" in text
    assert ".claude/trellis_plan.json" in text


def test_bootstrap_updates_existing_fence_in_place(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    existing = (
        "host prefix\n"
        f"{trellis_bootstrap.FENCE_START}\nold block\n{trellis_bootstrap.FENCE_END}\n"
        "host body\n"
    )
    (target / "CLAUDE.md").write_text(existing, encoding="utf-8")

    assert run_bootstrap(target, monkeypatch, "--yes") == 0
    text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "old block" not in text
    assert text.startswith("host prefix\n")
    assert text.endswith("host body\n")
    assert "# Trellis Claude orientation" in text


def test_bootstrap_does_not_touch_files_without_explicit_yes(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    answers = iter(["no", "no", "no"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert run_bootstrap(target, monkeypatch) == 0

    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".gitignore").exists()
    assert not (target / ".claude" / "trellis_install_manifest.json").exists()


def test_bootstrap_missing_template_file_errors(repo_root, tmp_path, monkeypatch, capsys):
    target = install_target(repo_root, tmp_path)
    (target / "tools" / "trellis_templates" / "CLAUDE.md.template").unlink()

    assert run_bootstrap(target, monkeypatch, "--yes") == 1
    err = capsys.readouterr().err
    assert "required template missing" in err


def test_bootstrap_manifest_does_not_claim_unmarked_host_memory(repo_root, tmp_path, monkeypatch):
    target = tmp_path / "host"
    (target / "memory").mkdir(parents=True)
    (target / "memory" / "host-note.md").write_text("host memory\n", encoding="utf-8")
    assert install_trellis.install(repo_root, target, force=False, dry_run=False) == 0
    assert not (target / "memory" / ".trellis-memory").exists()

    assert run_bootstrap(target, monkeypatch, "--yes") == 0

    manifest = json.loads((target / ".claude" / "trellis_install_manifest.json").read_text(encoding="utf-8"))
    assert "memory/host-note.md" not in manifest["expected_files"]
    assert not any(rel.startswith("memory/") for rel in manifest["expected_files"])
    assert "memory/host-note.md" not in manifest["missing_files"]


def test_cleanup_advisory_lists_only_present_candidates(repo_root, tmp_path, monkeypatch, capsys):
    target = install_target(repo_root, tmp_path)
    legacy = target / "trellis-docs" / "trellis-claude.md"
    legacy.write_text("old", encoding="utf-8")
    (target / "task-packs" / "done" / "TP-99_old.md").write_text("# TP-99 old\n", encoding="utf-8")

    assert run_bootstrap(target, monkeypatch, "--yes") == 0
    out = capsys.readouterr().out
    assert "trellis-docs/trellis-claude.md" in out
    assert "task-packs/done/TP-99_old.md" in out
    assert "trellis-docs/trellis-readme.md" not in out


def test_bootstrap_does_not_write_through_symlinked_claude(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    outside = tmp_path / "outside-claude.md"
    outside.write_text("host outside content\n", encoding="utf-8")
    _symlink_or_skip(target / "CLAUDE.md", outside)

    assert run_bootstrap(target, monkeypatch, "--yes") == 0

    assert (target / "CLAUDE.md").is_symlink()
    assert outside.read_text(encoding="utf-8") == "host outside content\n"
    assert (target / ".gitignore").exists()


def test_bootstrap_does_not_write_through_symlinked_manifest(repo_root, tmp_path, monkeypatch):
    target = install_target(repo_root, tmp_path)
    outside = tmp_path / "outside-manifest.json"
    outside.write_text('{"host": true}\n', encoding="utf-8")
    _symlink_or_skip(target / ".claude" / "trellis_install_manifest.json", outside)

    assert run_bootstrap(target, monkeypatch, "--yes") == 0

    assert (target / ".claude" / "trellis_install_manifest.json").is_symlink()
    assert outside.read_text(encoding="utf-8") == '{"host": true}\n'
    assert (target / "CLAUDE.md").exists()
    assert (target / ".gitignore").exists()

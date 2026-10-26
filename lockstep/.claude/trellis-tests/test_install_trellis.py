from __future__ import annotations

from pathlib import Path

import pytest

try:
    import install_trellis
except ModuleNotFoundError:  # Installed projects keep the installer under tools/trellis_install.py.
    from tools import trellis_install as install_trellis


def run_installer(repo_root: Path, target: Path, *args: str):
    overwrite = "--overwrite-trellis" in args or "--force" in args
    dry_run = "--dry-run" in args
    return install_trellis.install(repo_root, target, dry_run=dry_run, overwrite_trellis=overwrite)


def source_has_trellis_memory(repo_root: Path) -> bool:
    return (repo_root / "memory" / ".trellis-memory").is_file()


def test_installer_creates_expected_trellis_files_without_host_docs(repo_root, tmp_path):
    target = tmp_path / "new-project"
    result = run_installer(repo_root, target)
    assert result == 0
    assert not (target / "CLAUDE.md").exists()
    assert not (target / "README.md").exists()
    assert not (target / "FINDINGS.md").exists()
    assert not (target / "DECISIONS.md").exists()
    assert not (target / "BLUEPRINT.md").exists()
    assert (target / "tools" / "trellis_templates" / "CLAUDE.md.template").exists()
    assert (target / "tools" / "trellis_templates" / "gitignore.snippet").exists()
    assert (target / ".claude" / "commands" / "trellis-bootstrap.md").exists()
    assert (target / "trellis-docs" / "trellis-findings.md").exists()
    assert (target / "trellis-docs" / "trellis-decisions.md").exists()
    assert (target / ".claude" / "settings.json").exists()
    assert (target / ".claude" / "hooks" / "check_context_loaded.py").exists()
    assert (target / ".claude" / "rules" / "source-work.md").exists()
    if source_has_trellis_memory(repo_root):
        assert (target / "memory" / ".trellis-memory").exists()
        assert (target / "memory" / "README.md").exists()
        assert (target / "memory" / "task-pack-authoring" / "README.md").exists()
        assert (target / "memory" / "session-continuity" / "README.md").exists()
    else:
        assert not (target / "memory" / ".trellis-memory").exists()
    assert (target / "tools" / "trellis_refs.py").exists()
    assert (target / "tools" / "trellis_install.py").exists()
    assert (target / "task-packs" / "examples" / "TP-0_example.md").exists()
    assert not (target / "tests").exists()
    assert (target / ".claude" / "trellis-tests" / "test_install_trellis.py").exists()


def test_installer_preserves_host_documents_by_default(repo_root, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    host_files = {
        "README.md": "host readme",
        "CLAUDE.md": "host claude",
        "FINDINGS.md": "host findings",
        "DECISIONS.md": "host decisions",
        "HARNESS.md": "host harness",
    }
    for rel, text in host_files.items():
        (target / rel).write_text(text, encoding="utf-8")

    result = run_installer(repo_root, target)
    assert result == 0
    for rel, text in host_files.items():
        assert (target / rel).read_text(encoding="utf-8") == text
    assert (target / "trellis-docs" / "trellis-harness.md").exists()
    assert (target / "tools" / "trellis_templates" / "CLAUDE.md.template").exists()


def test_installer_backs_up_trellis_named_collision(repo_root, tmp_path):
    target = tmp_path / "existing"
    collision = target / "trellis-docs" / "trellis-harness.md"
    collision.parent.mkdir(parents=True)
    collision.write_text("host trellis-like file", encoding="utf-8")

    result = run_installer(repo_root, target, "--overwrite-trellis")
    assert result == 0
    assert (target / "trellis-docs" / "trellis-harness.md.host-backup").read_text(encoding="utf-8") == "host trellis-like file"
    assert "host trellis-like file" not in collision.read_text(encoding="utf-8")


def test_non_empty_target_succeeds_by_default_without_overwrite(repo_root, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "existing.txt").write_text("keep", encoding="utf-8")
    result = run_installer(repo_root, target)
    assert result == 0
    assert (target / "existing.txt").read_text(encoding="utf-8") == "keep"
    assert (target / ".claude" / "commands" / "pack.md").exists()
    assert (target / ".claude" / "commands" / "close.md").exists()


def test_existing_host_memory_directory_is_not_polluted(repo_root, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "memory").mkdir()
    (target / "memory" / "host-note.md").write_text("host memory\n", encoding="utf-8")

    result = run_installer(repo_root, target)

    assert result == 0
    assert (target / "memory" / "host-note.md").read_text(encoding="utf-8") == "host memory\n"
    assert not (target / "memory" / ".trellis-memory").exists()
    assert not (target / "memory" / "task-pack-authoring").exists()


def test_existing_trellis_memory_directory_can_receive_updates(repo_root, tmp_path):
    target = tmp_path / "existing"
    (target / "memory").mkdir(parents=True)
    (target / "memory" / ".trellis-memory").write_text("Trellis internal memory sentinel.\n", encoding="utf-8")

    result = run_installer(repo_root, target)

    assert result == 0
    assert (target / "memory" / ".trellis-memory").exists()
    if source_has_trellis_memory(repo_root):
        assert (target / "memory" / "README.md").exists()
        assert (target / "memory" / "task-pack-authoring" / "README.md").exists()


def test_existing_trellis_collision_skipped_by_default(repo_root, tmp_path):
    target = tmp_path / "existing"
    collision = target / "trellis-docs" / "trellis-harness.md"
    collision.parent.mkdir(parents=True)
    collision.write_text("host trellis-like file", encoding="utf-8")

    result = run_installer(repo_root, target)
    assert result == 0
    assert collision.read_text(encoding="utf-8") == "host trellis-like file"
    assert not (target / "trellis-docs" / "trellis-harness.md.host-backup").exists()


def test_installer_ignores_unowned_source_files(repo_root, tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "tools" / "trellis_templates").mkdir(parents=True)
    (source / "tools" / "trellis_templates" / "CLAUDE.md.template").write_text("template", encoding="utf-8")
    (source / ".claude" / "commands").mkdir(parents=True)
    (source / ".claude" / "commands" / "pack.md").write_text("pack", encoding="utf-8")
    (source / "src").mkdir()
    (source / "src" / "host_code.py").write_text("print('host')", encoding="utf-8")
    (source / "random-root.txt").write_text("not trellis", encoding="utf-8")

    result = run_installer(source, target)
    assert result == 0
    assert (target / "tools" / "trellis_templates" / "CLAUDE.md.template").exists()
    assert (target / ".claude" / "commands" / "pack.md").exists()
    assert not (target / "src").exists()
    assert not (target / "random-root.txt").exists()


def test_dry_run_does_not_create_target(repo_root, tmp_path):
    target = tmp_path / "dry-run-target"
    result = run_installer(repo_root, target, "--dry-run")
    assert result == 0
    assert not target.exists()


def test_rejects_target_nested_inside_source(repo_root, tmp_path):
    del tmp_path
    target = repo_root / "tmp-nested-install-target"
    result = run_installer(repo_root, target, "--dry-run")
    assert result != 0


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")


def test_installer_does_not_write_through_symlinked_collision(repo_root, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside host content", encoding="utf-8")
    collision = target / "trellis-docs" / "trellis-harness.md"
    collision.parent.mkdir(parents=True)
    _symlink_or_skip(collision, outside)

    result = run_installer(repo_root, target, "--overwrite-trellis")

    assert result == 0
    assert collision.is_symlink()
    assert outside.read_text(encoding="utf-8") == "outside host content"
    assert not (target / "trellis-docs" / "trellis-harness.md.host-backup").exists()


def test_installer_does_not_write_inside_symlinked_directory(repo_root, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    outside = tmp_path / "outside-tools"
    outside.mkdir()
    _symlink_or_skip(target / "tools", outside)

    result = run_installer(repo_root, target)

    assert result == 0
    assert (target / "tools").is_symlink()
    assert not (outside / "trellis_refs.py").exists()
    assert not (outside / "trellis_templates" / "CLAUDE.md.template").exists()

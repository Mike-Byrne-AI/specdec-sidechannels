from __future__ import annotations

import pytest

from tools.trellis_paths import TrellisPathError, get_project_root, has_trellis_memory, is_source_layout


def test_env_project_root_must_have_trellis_markers(tmp_path, monkeypatch):
    unmarked = tmp_path / "not-trellis"
    unmarked.mkdir()
    monkeypatch.setenv("TRELLIS_PROJECT_ROOT", str(unmarked))

    with pytest.raises(TrellisPathError):
        get_project_root(unmarked)


def test_symlinked_memory_sentinel_is_not_trusted(minimal_project, tmp_path):
    memory = minimal_project / "memory"
    memory.mkdir()
    real_sentinel = tmp_path / "sentinel"
    real_sentinel.write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    try:
        (memory / ".trellis-memory").symlink_to(real_sentinel)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")

    assert not has_trellis_memory(minimal_project)


def _write_source_layout_markers(root):
    for rel in (
        "install_trellis.py",
        "BLUEPRINT.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "requirements-dev.txt",
        "tests/conftest.py",
        "tests/test_public_project_surface.py",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# source marker\n", encoding="utf-8")


def test_source_layout_accepts_complete_source_marker_set(minimal_project):
    _write_source_layout_markers(minimal_project)

    assert is_source_layout(minimal_project)


def test_installed_host_with_root_tests_is_not_source_layout(minimal_project):
    # Installed hosts receive install_trellis.py, and many host projects have
    # their own root tests/conftest.py. That pair alone must not make Trellis
    # self-tests treat the host as the source checkout.
    (minimal_project / "install_trellis.py").write_text("", encoding="utf-8")
    (minimal_project / "tests").mkdir()
    (minimal_project / "tests" / "conftest.py").write_text("", encoding="utf-8")

    assert not is_source_layout(minimal_project)


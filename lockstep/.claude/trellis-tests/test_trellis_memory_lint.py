from __future__ import annotations

import pytest

from tools.trellis_memory_lint import check_memory


def mark_memory(root):
    (root / "memory").mkdir(exist_ok=True)
    (root / "memory" / ".trellis-memory").write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    (root / "memory" / "README.md").write_text("# Trellis internal memory\n", encoding="utf-8")


def test_source_memory_lint_passes(repo_root):
    assert check_memory(repo_root) == []


def test_unmarked_host_memory_is_skipped(minimal_project):
    (minimal_project / "memory").mkdir()
    (minimal_project / "memory" / "scratch.md").write_bytes(b"\xff\xfeD-99")

    assert check_memory(minimal_project) == []


def test_marked_memory_requires_topic_readme(minimal_project):
    mark_memory(minimal_project)
    (minimal_project / "memory" / "bad_topic").mkdir()

    issues = check_memory(minimal_project)

    assert any(issue.code == "topic-name" and issue.path == "memory/bad_topic" for issue in issues)
    assert any(issue.code == "missing-topic-readme" and issue.path == "memory/bad_topic/README.md" for issue in issues)


def test_marked_memory_rejects_root_scratch_files(minimal_project):
    mark_memory(minimal_project)
    (minimal_project / "memory" / "scratch.md").write_text("temporary note\n", encoding="utf-8")

    issues = check_memory(minimal_project)

    assert any(issue.code == "root-file" and issue.path == "memory/scratch.md" for issue in issues)
    assert any(issue.code == "banned-name" and issue.path == "memory/scratch.md" for issue in issues)


def test_marked_memory_rejects_secret_patterns(minimal_project):
    mark_memory(minimal_project)
    topic = minimal_project / "memory" / "harness-maintenance"
    topic.mkdir()
    (topic / "README.md").write_text("# Harness\n\napi_key = 'sk-12345678901234567890'\n", encoding="utf-8")

    issues = check_memory(minimal_project)

    assert any(issue.code == "secret-pattern" and issue.path == "memory/harness-maintenance/README.md" for issue in issues)


def test_marked_memory_rejects_nested_files(minimal_project):
    mark_memory(minimal_project)
    nested = minimal_project / "memory" / "harness-maintenance" / "nested"
    nested.mkdir(parents=True)
    (minimal_project / "memory" / "harness-maintenance" / "README.md").write_text("# Harness\n", encoding="utf-8")
    (nested / "note.md").write_text("too deep\n", encoding="utf-8")

    issues = check_memory(minimal_project)

    assert any(issue.code == "nested-file" and issue.path == "memory/harness-maintenance/nested/note.md" for issue in issues)


def test_marked_memory_rejects_symlinked_sentinel(minimal_project, tmp_path):
    (minimal_project / "memory").mkdir()
    real_sentinel = tmp_path / "sentinel"
    real_sentinel.write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    try:
        (minimal_project / "memory" / ".trellis-memory").symlink_to(real_sentinel)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")

    issues = check_memory(minimal_project)

    assert any(issue.code == "symlink" and issue.path == "memory/.trellis-memory" for issue in issues)

def test_marked_memory_rejects_nested_symlinked_files(minimal_project, tmp_path):
    topic = minimal_project / "memory" / "harness-maintenance"
    topic.mkdir(parents=True)
    (minimal_project / "memory" / ".trellis-memory").write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    (minimal_project / "memory" / "README.md").write_text("# Memory\n", encoding="utf-8")
    (topic / "README.md").write_text("# Harness\n", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    try:
        (topic / "linked.md").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this platform")

    issues = check_memory(minimal_project)

    assert any(issue.code == "symlink" and issue.path == "memory/harness-maintenance/linked.md" for issue in issues)

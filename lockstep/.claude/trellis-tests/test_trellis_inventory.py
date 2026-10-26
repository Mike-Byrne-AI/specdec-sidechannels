from __future__ import annotations

from tools.trellis_inventory import EXPECTED_COUNTS, EXPECTED_SOURCE_MEMORY_TOPICS, collect_inventory, inventory_mismatches
from tools.trellis_paths import has_trellis_memory


def test_inventory_contains_expected_keys(repo_root):
    data = collect_inventory(repo_root)
    for key in ["commands", "skills", "agents", "hooks", "rules", "active_task_packs", "example_task_packs", "done_task_packs", "memory_topics"]:
        assert key in data


def test_inventory_check_counts_match(repo_root):
    data = collect_inventory(repo_root)
    mismatches = {key: (data.get(key), expected) for key, expected in EXPECTED_COUNTS.items() if data.get(key) != expected}
    assert mismatches == {}
    if has_trellis_memory(repo_root):
        assert data["memory_topics"] == EXPECTED_SOURCE_MEMORY_TOPICS
    assert inventory_mismatches(repo_root, data) == []


def test_source_checkout_with_unmarked_memory_reports_inventory_mismatch(minimal_project):
    for rel in (
        "install_trellis.py",
        "BLUEPRINT.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "requirements-dev.txt",
        "tests/conftest.py",
        "tests/test_public_project_surface.py",
    ):
        path = minimal_project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# source marker\n", encoding="utf-8")
    (minimal_project / "memory" / "harness-maintenance").mkdir(parents=True)
    data = collect_inventory(minimal_project)

    mismatches = inventory_mismatches(minimal_project, data)

    assert any("memory/.trellis-memory" in mismatch for mismatch in mismatches)

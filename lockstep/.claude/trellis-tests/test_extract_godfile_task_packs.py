from __future__ import annotations

from tools.trellis_extract_godfile import build_godfile
from tools.trellis_paths import active_task_packs


def test_active_task_pack_discovery_excludes_examples_archives_and_completed(minimal_project):
    root = minimal_project
    (root / "task-packs" / "TP-1_real_work.md").write_text("# real\n", encoding="utf-8")
    (root / "task-packs" / "examples" / "TP-0_example.md").write_text("# example\n", encoding="utf-8")
    (root / "task-packs" / "archive" / "TP-2_old.md").write_text("# old\n", encoding="utf-8")
    (root / "task-packs" / "completed" / "TP-3_done.md").write_text("# done\n", encoding="utf-8")
    (root / "task-packs" / "TP-4_example.md").write_text("# bad top-level example\n", encoding="utf-8")

    assert [p.name for p in active_task_packs(root)] == ["TP-1_real_work.md"]


def test_godfile_lists_only_real_active_task_packs(minimal_project):
    root = minimal_project
    (root / "task-packs" / "TP-1_real_work.md").write_text("# real\n", encoding="utf-8")
    (root / "task-packs" / "examples" / "TP-0_example.md").write_text("# example\n", encoding="utf-8")

    godfile = build_godfile(root)

    assert "TP-1_real_work.md" in godfile
    assert "TP-0_example.md" not in godfile

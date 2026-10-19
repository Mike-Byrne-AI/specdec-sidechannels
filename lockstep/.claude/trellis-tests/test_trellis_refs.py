from __future__ import annotations

from tools.trellis_refs import check_references, collect_decision_ids, collect_finding_ids, collect_task_pack_ids


def test_refs_pass_with_matching_ids(minimal_project):
    (minimal_project / "trellis-docs/trellis-findings.md").write_text(
        "# Findings\n\n### F1 - Real finding\n\nObservation.\n",
        encoding="utf-8",
    )
    (minimal_project / "trellis-docs/trellis-decisions.md").write_text(
        "# Decisions\n\n## D-1 - Use tiny local gates [imagined]\n\n**Source**: F1 and TP-1\n",
        encoding="utf-8",
    )
    (minimal_project / "task-packs" / "TP-1_real.md").write_text(
        "# Task Pack 1\n\nReferences D-1 and F1.\n",
        encoding="utf-8",
    )
    issues = check_references(minimal_project)
    assert issues == []
    assert collect_finding_ids(minimal_project) == {"F1"}
    assert collect_decision_ids(minimal_project) == {"D-1"}
    assert collect_task_pack_ids(minimal_project) == {"TP-1"}


def test_missing_finding_reference_fails(minimal_project):
    (minimal_project / "trellis-docs/trellis-decisions.md").write_text(
        "# Decisions\n\n## D-1 - Decision [imagined]\n\n**Source**: F9\n",
        encoding="utf-8",
    )
    issues = check_references(minimal_project)
    assert any(issue.ref == "F9" and issue.kind == "finding" for issue in issues)


def test_missing_task_pack_reference_fails(minimal_project):
    (minimal_project / "trellis-docs/trellis-findings.md").write_text(
        "# Findings\n\n### F1 - Finding\n\nStatus: acted on by TP-9.\n",
        encoding="utf-8",
    )
    issues = check_references(minimal_project)
    assert any(issue.ref == "TP-9" and issue.kind == "task-pack" for issue in issues)


def test_placeholder_comments_and_code_fences_are_ignored(minimal_project):
    (minimal_project / "trellis-docs/trellis-findings.md").write_text(
        "# Findings\n\n<!-- the first real finding goes here as F1 -->\n\n```markdown\nF2 example only\n```\n",
        encoding="utf-8",
    )
    issues = check_references(minimal_project)
    assert not any(issue.kind == "finding" for issue in issues)


def test_malformed_decision_confidence_fails(minimal_project):
    (minimal_project / "trellis-docs/trellis-decisions.md").write_text(
        "# Decisions\n\n## D-1 - Missing marker\n\nText.\n",
        encoding="utf-8",
    )
    issues = check_references(minimal_project)
    assert any(issue.ref == "D-1" and "confidence" in issue.message for issue in issues)


def test_example_task_packs_do_not_define_real_task_pack_ids(minimal_project):
    (minimal_project / "task-packs" / "examples" / "TP-9_example.md").write_text("# Example\n", encoding="utf-8")
    assert "TP-9" not in collect_task_pack_ids(minimal_project)


def test_binary_and_non_utf8_source_files_are_skipped(minimal_project):
    src = minimal_project / "src"
    (src / "image.bin").write_bytes(b"\x00\xffD-999")
    (src / "bad.py").write_bytes(b"\xff\xfeF999")
    issues = check_references(minimal_project)
    assert not any(issue.path.endswith("image.bin") or issue.path.endswith("bad.py") for issue in issues)


def test_text_source_file_references_are_still_checked(minimal_project):
    (minimal_project / "src" / "main.py").write_text("# cites F99\n", encoding="utf-8")
    issues = check_references(minimal_project)
    assert any(issue.ref == "F99" and issue.kind == "finding" for issue in issues)


def test_memory_markdown_references_are_checked(minimal_project):
    (minimal_project / "memory" / "task-pack-authoring").mkdir(parents=True)
    (minimal_project / "memory" / ".trellis-memory").write_text("Trellis internal memory sentinel.\n", encoding="utf-8")
    (minimal_project / "memory" / "task-pack-authoring" / "README.md").write_text(
        "# Memory\n\nDurable note cites D-99.\n",
        encoding="utf-8",
    )

    issues = check_references(minimal_project)

    assert any(issue.path == "memory/task-pack-authoring/README.md" and issue.ref == "D-99" for issue in issues)


def test_unmarked_host_memory_references_are_ignored(minimal_project):
    (minimal_project / "memory").mkdir()
    (minimal_project / "memory" / "host-note.md").write_text("Host-owned note cites D-99.\n", encoding="utf-8")

    issues = check_references(minimal_project)

    assert not any(issue.path == "memory/host-note.md" for issue in issues)

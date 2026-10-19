from __future__ import annotations

from tools.trellis_blueprint import (
    active_path,
    finalize_blueprint,
    latest_path,
    load_blueprint_state,
    record_blueprint,
    start_blueprint,
)


def test_blueprint_start_record_finalize(minimal_project):
    data = start_blueprint(minimal_project, title="Test session")
    assert data["status"] == "active"
    assert active_path(minimal_project).exists()

    record = record_blueprint(minimal_project, "decision", "chose the small local version")
    assert record["kind"] == "decision"

    finalized = finalize_blueprint(minimal_project)
    assert finalized is not None
    assert finalized["status"] == "finalized"
    assert not active_path(minimal_project).exists()
    assert latest_path(minimal_project).exists()

    state = load_blueprint_state(minimal_project)
    assert state["latest"]["record_count"] == 1
    assert state["latest"]["latest_records"][0]["description"] == "chose the small local version"


def test_record_autostarts_blueprint(minimal_project):
    record_blueprint(minimal_project, "next_step", "run the next proof gate")
    state = load_blueprint_state(minimal_project)
    assert state["active"] is not None
    assert state["active"]["record_count"] == 1


def test_unsupported_blueprint_kind_fails(minimal_project):
    try:
        record_blueprint(minimal_project, "unsupported", "bad")
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("unsupported kind should fail")

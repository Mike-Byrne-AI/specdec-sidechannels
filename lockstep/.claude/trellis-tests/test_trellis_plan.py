from __future__ import annotations

from tools.trellis_plan import create_plan, mark_step, next_step, read_plan, reset_plan


def test_plan_create_mark_complete_reset(minimal_project):
    plan = create_plan(minimal_project, "Do work", "phase one|phase two")
    assert plan["status"] == "in_progress"
    assert len(plan["steps"]) == 2
    assert next_step(plan)["index"] == 0

    plan = mark_step(minimal_project, 0, "running")
    assert plan["steps"][0]["status"] == "running"

    plan = mark_step(minimal_project, 0, "passed")
    assert plan["status"] == "in_progress"

    plan = mark_step(minimal_project, 1, "passed", note="verified")
    assert plan["status"] == "complete"
    assert plan["steps"][1]["notes"][0]["text"] == "verified"

    assert reset_plan(minimal_project) is True
    assert read_plan(minimal_project) is None


def test_plan_rejects_negative_and_out_of_range_indices(minimal_project):
    create_plan(minimal_project, "Do work", "phase one")
    for index in (-1, 99):
        try:
            mark_step(minimal_project, index, "passed")
        except IndexError:
            pass
        else:
            raise AssertionError("invalid index should fail")


def test_plan_prevents_overwriting_in_progress_without_force(minimal_project):
    create_plan(minimal_project, "First", "phase one")
    try:
        create_plan(minimal_project, "Second", "phase two")
    except RuntimeError as exc:
        assert "in-progress" in str(exc)
    else:
        raise AssertionError("expected in-progress guard")

    forced = create_plan(minimal_project, "Second", "phase two", force=True)
    assert forced["task"] == "Second"

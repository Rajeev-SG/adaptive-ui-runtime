"""Durability + status/resume (issue #3/#13)."""
import os

from adaptive_ui_runtime.contracts import (
    Plan,
    RuntimeConfig,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.engine import Engine
from adaptive_ui_runtime.runtime import Runtime
from adaptive_ui_runtime.transports.fake import FakeTransport


def crit():
    return SuccessCriterion(kind="state", description="d", expected="x", rule={"field": "items"})


def test_checkpoint_written_and_status_queryable(tmp_path):
    store = FileRunStore(tmp_path)
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[crit()], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(), store=store)
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    rt = Runtime(RuntimeConfig(), transport="fake", store=store)
    status = rt.status(r.run_id)
    assert status["found"] and status["status"] == "succeeded"


def test_resume_skips_verified_subtasks(tmp_path):
    store = FileRunStore(tmp_path)
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[crit()], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(), store=store)
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    # resuming a fully verified run must not redo state-changing work
    t2 = FakeTransport()
    rt = Runtime(RuntimeConfig(), transport="fake", store=store)
    r2 = rt.resume(r.run_id, TaskRequest(goal="g", success_criteria=[crit()]), transport=t2)
    assert r2.verified
    assert t2.app.items == []  # nothing replayed


def test_dbos_launches():
    from adaptive_ui_runtime.durability import launch_dbos
    env = os.environ.get("AUR_DBOS_TEST", "1")
    if env == "0":
        return
    assert launch_dbos() in (True, False)  # must not raise

"""Engine contract tests (issue #2/#10/#11)."""
from adaptive_ui_runtime.contracts import (
    FailureClass,
    Plan,
    RuntimeConfig,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.engine import Engine
from adaptive_ui_runtime.transports.fake import FakeTransport


def _store(tmp_path):
    return FileRunStore(tmp_path / "state")


def _crit():
    return SuccessCriterion(kind="state", description="items contains x",
                            expected="x", rule={"field": "items"})


def test_happy_path_verified(tmp_path):
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[_crit()],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(), store=_store(tmp_path))
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[_crit()]))
    assert r.verified and r.status == "succeeded"
    assert t.app.items == ["x"]


def test_premature_done_rejected(tmp_path):
    t = FakeTransport()
    # no steps -> structured path proposes DONE immediately, verifier must reject
    st2 = Subtask(id="s2", goal="g", success_criteria=[_crit()],
                  task_class="deterministic_dom", steps=[])
    e = Engine(t, config=RuntimeConfig(), store=_store(tmp_path))
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st2])
    r = e.execute(TaskRequest(goal="g", success_criteria=[_crit()]))
    assert not r.verified
    assert r.failure_class in (str(FailureClass.PREMATURE_DONE),
                               str(FailureClass.VERIFIER_MISMATCH),
                               str(FailureClass.BUDGET_EXCEEDED))


def test_cycle_detection_terminates(tmp_path):
    t = FakeTransport()
    # clicking 'add' never satisfies the criteria -> same action repeats
    # a no-op repeat: search with an empty field never changes material state
    st = Subtask(id="s1", goal="g", success_criteria=[_crit()],
                 task_class="deterministic_dom",
                 steps=[{"kind": "click", "target": "search"}] * 6)
    e = Engine(t, config=RuntimeConfig(), store=_store(tmp_path))
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[_crit()]))
    assert not r.verified
    assert r.metrics["loops"] >= 1
    assert r.metrics["actions"] <= 6


def test_stale_target_recovery(tmp_path):
    t = FakeTransport()
    t.fail_next = "stale"
    st = Subtask(id="s1", goal="g", success_criteria=[_crit()],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(), store=_store(tmp_path))
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[_crit()]))
    assert r.metrics["recoveries"] >= 1
    assert r.verified


def test_budget_is_bounded(tmp_path):
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[_crit()],
                 task_class="deterministic_dom",
                 steps=[{"kind": "click", "target": "search"}] * 50)
    e = Engine(t, config=RuntimeConfig(), store=_store(tmp_path))
    e.manager._fallback_plan = lambda r: Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[_crit()]))
    assert r.metrics["actions"] <= st.budget.max_actions

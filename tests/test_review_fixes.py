"""Regression tests for frontier review #2 findings D1-D4."""

import pytest

from adaptive_ui_runtime.contracts import (
    Plan,
    RuntimeConfig,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.engine import Engine
from adaptive_ui_runtime.transports.fake import FakeTransport


def crit(v="x"):
    return SuccessCriterion(kind="state", description="d", expected=v, rule={"field": "items"})


class FailThenSucceedManager:
    """A manager that fails the first subtask then replans with a passing one."""

    def __init__(self):
        self.override_plan = None
        self.calls = 0
        self.replans = 0

    def plan(self, request, prior=None):
        return self.override_plan

    def replan(self, request, failure_class, detail, prior):
        self.replans += 1
        c = crit("done")
        st = Subtask(id="new-1", goal="g", success_criteria=[c],
                     task_class="deterministic_dom",
                     steps=[{"kind": "type", "target": "field", "value": "done"},
                            {"kind": "click", "target": "search"}])
        return Plan(goal="g", subtasks=[st], rationale="replan")

    def usage(self):
        return {"manager_calls": 0}


def test_d1_replan_with_fresh_ids_reports_success(tmp_path):
    """D1: a replan that fully succeeds must report SUCCEEDED, not FAILED."""
    t = FakeTransport()
    failing = Subtask(id="orig-1", goal="g", success_criteria=[crit("never")],
                      task_class="deterministic_dom",
                      steps=[{"kind": "click", "target": "search"}])  # never satisfies
    failing.budget.max_actions = 2
    e = Engine(t, config=RuntimeConfig(max_escalations=2), store=FileRunStore(tmp_path))
    m = FailThenSucceedManager()
    m.override_plan = Plan(goal="g", subtasks=[failing])
    e.manager = m
    e.config.enable_strong_manager = True
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    assert m.replans >= 1, "replan path was not exercised"
    assert r.verified, (r.failure_class, r.metrics.get("replans"))


def test_d1_dependency_skip_records_status(tmp_path):
    """D1: a subtask whose dependency is not verified is recorded SKIPPED."""
    t = FakeTransport()
    # 'b' depends on 'z', which is not part of the plan -> never verified -> b skipped
    b = Subtask(id="b", goal="g", success_criteria=[crit("done")],
                task_class="deterministic_dom", depends_on=["z"],
                steps=[{"kind": "type", "target": "field", "value": "done"}])
    e = Engine(t, config=RuntimeConfig(enable_strong_manager=False),
               store=FileRunStore(tmp_path))
    e.manager.override_plan = Plan(goal="g", subtasks=[b])
    save_status = {}
    orig = e._save
    e._save = lambda st: (save_status.update(dict(st.subtask_status)), orig(st))
    e.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    assert str(save_status.get("b")) == "skipped"


def test_d3_save_failure_is_surfaced(tmp_path):
    """D3: a store failure must be recorded, not silently swallowed."""
    class BoomStore:
        def save(self, state):
            raise OSError("disk full")
        def load(self, run_id):
            return None

    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[crit("x")],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(durable=False), store=BoomStore())
    e.manager.override_plan = Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit("x")]))
    assert r.metrics.get("state_save_failures", 0) >= 1
    assert any(ev.kind == "state_save_failed" for ev in e.tracer.events)


def test_d2_registry_evicted_after_run(tmp_path):
    """D2: the durable run registry must not retain engines after a run."""
    from adaptive_ui_runtime import durable_exec
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[crit("x")],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(durable=False), store=FileRunStore(tmp_path))
    e.manager.override_plan = Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit("x")]))
    assert r.run_id not in durable_exec.RUN_REGISTRY


def test_d4_mcp_rejects_invalid_mode():
    """D4: MCP must validate mode strings, not bypass the contract layer."""
    from adaptive_ui_runtime import mcp_server
    for bad in ("adaptve", "Strong", ""):
        with pytest.raises(ValueError):
            mcp_server._rt(mode=bad)
    assert mcp_server._rt(mode="no_jev") is not None

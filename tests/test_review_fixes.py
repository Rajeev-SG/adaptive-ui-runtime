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


def test_no_fault_injection_on_production_transport():
    """Review: fault injection must not ship on the production transport."""
    from adaptive_ui_runtime.transports.isolated import (
        FaultInjectingIsolatedTransport,
        IsolatedBrowserTransport,
    )
    assert not hasattr(IsolatedBrowserTransport, "fail_next")
    assert hasattr(FaultInjectingIsolatedTransport, "_sel")


def test_manager_decide_action_normalises_and_bounds():
    """Manager synonyms normalise to the runtime action vocabulary; junk -> None."""
    import os

    from adaptive_ui_runtime.manager import Manager
    m = Manager()
    # no key -> available() False -> None, never a bogus action
    os.environ.pop("OPENROUTER_API_KEY", None)
    assert m.decide_action("g", [], {}) is None


def test_js_rule_plain_string_result_is_compared(tmp_path):
    """A non-JSON string fact is a legitimate JS result, not a parse failure."""
    from adaptive_ui_runtime.contracts import Observation, SuccessCriterion
    from adaptive_ui_runtime.verifier import Verifier
    obs = Observation(snapshot_id="s", state_fingerprint="f",
                      structured_state={"js_rule_ran": True, "js_result": "Email supplier"})
    crit = SuccessCriterion(kind="js_rule", description="d",
                            rule={"js": "x", "expected": "Email supplier"})
    assert Verifier().check([crit], obs).passed


def test_recovery_case_refuses_non_injecting_transport():
    """The recovery case must not silently run as non-recovery on another transport."""
    import importlib.util
    import sys
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "scripts/run_e2e_benchmark.py"
    spec = importlib.util.spec_from_file_location("e2ebench", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e2ebench"] = mod
    spec.loader.exec_module(mod)
    try:
        mod._make_case_transport("fake", "recovery_injected_stale_target")
        raised = False
    except SystemExit:
        raised = True
    assert raised, "recovery case must refuse a non-fault-injecting transport"


def test_run_timeout_is_classified_as_infra():
    """A rep exceeding the wall budget is an infrastructure timeout, not a
    latency data point (guards the 10-minute provider-stall case)."""
    import importlib.util
    import sys
    import time
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "scripts/run_e2e_benchmark.py"
    spec = importlib.util.spec_from_file_location("e2ebench2", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e2ebench2"] = mod
    spec.loader.exec_module(mod)

    class SlowEngine:
        def execute(self, request):
            time.sleep(5)
            return None

    t0 = time.perf_counter()
    raised = False
    try:
        mod._execute_with_timeout(SlowEngine(), object(), 0.3)
    except mod._RunTimeout:
        raised = True
    assert raised and (time.perf_counter() - t0) < 3.0

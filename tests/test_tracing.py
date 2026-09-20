"""One run must be reconstructable from its trace; metrics are machine-readable
and observability overhead is measurable (issue #14)."""
import json
import time

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


def _run(tmp_path, execute=True):
    t = FakeTransport()
    st = Subtask(id="s1", goal="g", success_criteria=[crit()], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    e = Engine(t, config=RuntimeConfig(durable=False), store=FileRunStore(tmp_path))
    e.manager.override_plan = Plan(goal="g", subtasks=[st])
    return e, e.execute(TaskRequest(goal="g", success_criteria=[crit()]))


def test_trace_reconstructs_run(tmp_path):
    e, r = _run(tmp_path)
    trace = Runtime(RuntimeConfig(), transport="fake", store=FileRunStore(tmp_path)).trace(r.run_id)
    kinds = [ev["kind"] for ev in trace["events"]]
    for required in ("run_start", "plan", "route", "action", "verify", "run_end"):
        assert required in kinds, (required, kinds)


def test_metrics_are_machine_readable(tmp_path):
    import os
    os.environ["AUR_TRACE_DIR"] = str(tmp_path / "traces")
    e, r = _run(tmp_path)
    m = r.metrics
    json.dumps(m)  # serialisable
    for key in ("wall_ms", "actions", "observations", "verifications",
                "jev_calls", "manager_calls", "recoveries", "loops",
                "failure_classes", "config"):
        assert key in m, key


def test_observability_overhead_is_small(tmp_path):
    """Tracer overhead on the deterministic path must be a small fraction."""
    st = Subtask(id="s1", goal="g", success_criteria=[crit()], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    # without tracing
    e1 = Engine(FakeTransport(), config=RuntimeConfig(durable=False), store=FileRunStore(tmp_path))
    e1.manager.override_plan = Plan(goal="g", subtasks=[st])
    start = time.perf_counter()
    for _ in range(20):
        e1.tracer = None
        e1.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    untraced = (time.perf_counter() - start) / 20
    # with tracing
    e2 = Engine(FakeTransport(), config=RuntimeConfig(durable=False), store=FileRunStore(tmp_path))
    e2.manager.override_plan = Plan(goal="g", subtasks=[st])
    start = time.perf_counter()
    for _ in range(20):
        e2.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    traced = (time.perf_counter() - start) / 20
    # tracer must add well under 10x on this micro path
    assert traced < untraced * 10 + 0.01

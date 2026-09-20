"""Manager path tests with a mocked strong model (issue #7, addresses review F3)."""


from adaptive_ui_runtime.contracts import (
    Plan,
    RuntimeConfig,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.engine import Engine
from adaptive_ui_runtime.manager import Manager, ManagerPlanOut
from adaptive_ui_runtime.transports.fake import FakeTransport


def crit():
    return SuccessCriterion(kind="state", description="d", expected="x", rule={"field": "items"})


def test_deterministic_fallback_needs_no_call(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    m = Manager()
    plan = m.plan(TaskRequest(goal="g", success_criteria=[crit()]))
    assert len(plan.subtasks) == 1
    assert m.usage()["manager_calls"] == 0


def test_typed_llm_plan_is_validated(monkeypatch):
    monkeypatch.delenv("AUR_DISABLE_MANAGER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    m = Manager()
    captured = {}

    class FakeUsage:
        input_tokens = 10
        output_tokens = 5

    class FakeResult:
        def __init__(self):
            self.usage = FakeUsage()
            self.output = ManagerPlanOut(
                subtasks=[{
                    "id": "s1",
                    "goal": "do a thing",
                    "success_criteria": [{"kind": "state", "description": "d",
                                          "expected": "x", "rule": {"field": "items"}}],
                    "allowed_routes": ["structured_browser", "jev"],
                    "budget": {"max_actions": 3},
                    "task_class": "deterministic_dom",
                }],
                rationale="one step",
            )

    def fake_run_sync(prompt):
        captured["prompt"] = prompt
        return FakeResult()

    class FakeAgent:
        def run_sync(self, prompt):
            return fake_run_sync(prompt)

    m._build_agent = lambda: FakeAgent()
    plan = m.plan(TaskRequest(goal="g", success_criteria=[crit()]))
    assert plan.subtasks[0].task_class == "deterministic_dom"
    assert plan.subtasks[0].budget.max_actions == 3
    usage = m.usage()
    assert usage["manager_calls"] == 1
    assert usage["manager_input_tokens"] == 10
    # context stays manager-side: the prompt is the only place the goal is sent
    assert "goal" in captured["prompt"]


def test_invalid_subtask_is_rejected_not_executed(monkeypatch):
    monkeypatch.delenv("AUR_DISABLE_MANAGER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    m = Manager()

    class FakeResult:
        output = ManagerPlanOut(subtasks=[{"id": "s1", "goal": "x",
                                           "success_criteria": [],
                                           "budget": {"max_actions": -1}}],
                                rationale="bad")

    class FakeAgent:
        def run_sync(self, prompt):
            return FakeResult()

    m._build_agent = lambda: FakeAgent()
    # budget ge=1 -> validation error -> deterministic fallback, no bad action
    plan = m.plan(TaskRequest(goal="g", success_criteria=[crit()]))
    assert plan.subtasks


def test_manager_replan_uses_failure_context(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    m = Manager()
    plan = m.replan(TaskRequest(goal="g", success_criteria=[crit()]),
                    "verifier_mismatch", "detail", ["s1: verified"])
    assert plan.subtasks


def test_engine_uses_override_plan(monkeypatch, tmp_path):
    monkeypatch.delenv("AUR_DISABLE_MANAGER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    st = Subtask(id="s1", goal="g", success_criteria=[crit()],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    t = FakeTransport()
    e = Engine(t, config=RuntimeConfig(), store=FileRunStore(tmp_path))
    e.manager.override_plan = Plan(goal="g", subtasks=[st])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit()]))
    assert r.verified
    assert r.metrics["manager_calls"] == 0  # override avoids a model call

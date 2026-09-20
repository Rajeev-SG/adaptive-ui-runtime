"""Evaluation arms (issue #15)."""
from adaptive_ui_runtime.contracts import Plan, Subtask, SuccessCriterion, TaskRequest
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.evaluation import run_arms


def test_all_arms_produce_metrics(tmp_path):
    crit = SuccessCriterion(kind="state", description="d", expected="x", rule={"field": "items"})
    st = Subtask(id="s1", goal="g", success_criteria=[crit], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    out = run_arms(TaskRequest(goal="g", success_criteria=[crit]),
                   ["adaptive", "strong_only", "no_jev", "no_fara", "deterministic_only"],
                   plan=Plan(goal="g", subtasks=[st]), reps=2,
                   transport_name="fake", store=FileRunStore(tmp_path))
    for mode in ("adaptive", "strong_only", "no_jev", "no_fara", "deterministic_only"):
        arm = out["arms"][mode]
        assert arm["reps"] == 2
        assert "wall_p50_ms" in arm and "wall_p95_ms" in arm
        assert arm["success_rate"] == 1.0

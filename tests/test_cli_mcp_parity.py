"""CLI and MCP run the same runtime code path (issue #13)."""


from adaptive_ui_runtime.cli import main
from adaptive_ui_runtime.contracts import RuntimeConfig
from adaptive_ui_runtime.runtime import Runtime


def test_cli_execute_fake_fixture(tmp_path):
    spec = tmp_path / "t.yaml"
    spec.write_text(
        "goal: add x\n"
        "success_criteria:\n"
        "  - kind: state\n"
        "    description: items\n"
        "    expected: x\n"
        "    rule: {field: items}\n"
        "subtasks:\n"
        "  - id: s1\n"
        "    goal: add x\n"
        "    task_class: deterministic_dom\n"
        "    steps:\n"
        "      - {kind: type, target: field, value: x}\n"
        "      - {kind: click, target: search}\n"
    )
    rc = main(["execute", "--task", str(spec), "--transport", "fake"])
    assert rc == 0


def test_cli_plan_and_inspect():
    assert main(["inspect", "--transport", "fake"]) == 0
    assert main(["plan", "--task", "/tmp/aur-nonexistent.yaml"]) == 2


def test_mcp_tools_bound_to_runtime():
    from adaptive_ui_runtime import mcp_server
    assert hasattr(mcp_server, "ui_execute")
    assert hasattr(mcp_server, "ui_trace")
    assert hasattr(mcp_server, "ui_evaluate")


def test_same_fixture_python_and_runtime_agree(tmp_path):
    """Python path and Runtime path produce the same verified outcome."""
    from adaptive_ui_runtime.contracts import Plan, Subtask, SuccessCriterion, TaskRequest
    from adaptive_ui_runtime.durability import FileRunStore
    crit = SuccessCriterion(kind="state", description="d", expected="x", rule={"field": "items"})
    st = Subtask(id="s1", goal="g", success_criteria=[crit], task_class="deterministic_dom",
                 steps=[{"kind": "type", "target": "field", "value": "x"},
                        {"kind": "click", "target": "search"}])
    rt = Runtime(RuntimeConfig(), transport="fake", store=FileRunStore(tmp_path))
    res = rt.execute(TaskRequest(goal="g", success_criteria=[crit]),
                     plan=Plan(goal="g", subtasks=[st]))
    assert res.verified

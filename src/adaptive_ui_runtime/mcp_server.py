"""MCP server exposing the eight ui.* tools (issue #13).

Uses the official MCP Python SDK. Tools bind directly to Runtime so MCP and CLI
run the same code path.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from .contracts import (
    RuntimeConfig,
    SuccessCriterion,
    TaskRequest,
)
from .runtime import Runtime

mcp = MCPServer("adaptive-ui-runtime")


def _rt(transport: str | None = None, mode: str = "adaptive") -> Runtime:
    return Runtime(RuntimeConfig(mode=mode), transport=transport)


def _criteria(raw: list[dict[str, Any]] | None) -> list[SuccessCriterion]:
    return [SuccessCriterion(**c) for c in (raw or [])]


@mcp.tool()
def ui_execute(goal: str, success_criteria: list[dict[str, Any]] | None = None,
               constraints: dict[str, Any] | None = None,
               start_url: str | None = None, transport: str | None = None,
               mode: str = "adaptive", steps: list[dict[str, Any]] | None = None,
               task_class: str = "deterministic_dom") -> dict[str, Any]:
    """Execute a browser/UI goal and return a verified result plus run_id.

    Supply concrete success_criteria whenever possible. `steps` may give an
    explicit structured plan; otherwise the runtime plans.
    """
    request = TaskRequest(goal=goal, success_criteria=_criteria(success_criteria),
                          constraints=constraints or {}, start_url=start_url)
    plan = None
    if steps:
        from .contracts import Plan, Subtask
        plan = Plan(goal=goal, subtasks=[Subtask(
            id="s1", goal=goal, success_criteria=request.success_criteria,
            task_class=task_class, steps=steps)], rationale="mcp-provided steps")
    result = _rt(transport, mode).execute(request, plan=plan)
    out = result.model_dump(mode="json")
    out["summary_metrics"] = {
        k: result.metrics.get(k) for k in
        ("wall_ms", "actions", "observations", "jev_calls", "fara_calls",
         "showui_calls", "manager_calls", "recoveries", "loops")
    }
    return out


@mcp.tool()
def ui_inspect(transport: str | None = None) -> dict[str, Any]:
    """Read-only observation of the current UI/session state."""
    return _rt(transport).inspect()


@mcp.tool()
def ui_verify(success_criteria: list[dict[str, Any]],
              transport: str | None = None) -> dict[str, Any]:
    """Independently evaluate explicit success criteria; performs no mutation."""
    return _rt(transport).verify(_criteria(success_criteria))


@mcp.tool()
def ui_plan(goal: str, success_criteria: list[dict[str, Any]] | None = None,
            start_url: str | None = None) -> dict[str, Any]:
    """Return the proposed execution strategy without executing it."""
    return _rt().plan(TaskRequest(goal=goal,
                                  success_criteria=_criteria(success_criteria),
                                  start_url=start_url))


@mcp.tool()
def ui_status(run_id: str) -> dict[str, Any]:
    """Return durable run state for a run_id."""
    return _rt().status(run_id)


@mcp.tool()
def ui_resume(run_id: str, goal: str = "", transport: str | None = None) -> dict[str, Any]:
    """Resume a paused/interrupted run from its last checkpoint."""
    rt = _rt(transport)
    if not goal:
        st = rt.status(run_id)
        goal = st.get("goal", "")
    request = TaskRequest(goal=goal, success_criteria=[])
    return rt.resume(run_id, request).model_dump(mode="json")


@mcp.tool()
def ui_trace(run_id: str) -> dict[str, Any]:
    """Return the machine-readable decision/action/recovery trace for a run."""
    return _rt().trace(run_id)


@mcp.tool()
def ui_evaluate(goal: str, modes: list[str] | None = None,
                success_criteria: list[dict[str, Any]] | None = None,
                steps: list[dict[str, Any]] | None = None,
                task_class: str = "deterministic_dom",
                transport: str = "fake", reps: int = 1) -> dict[str, Any]:
    """Run a task under named runtime modes and return a comparison."""
    from .contracts import Plan, Subtask
    request = TaskRequest(goal=goal, success_criteria=_criteria(success_criteria))
    plan = None
    if steps:
        plan = Plan(goal=goal, subtasks=[Subtask(
            id="s1", goal=goal, success_criteria=request.success_criteria,
            task_class=task_class, steps=steps)], rationale="mcp-provided steps")
    return _rt(transport).evaluate(request, modes or ["adaptive"], plan=plan, reps=reps)


@mcp.tool()
def ui_health() -> dict[str, Any]:
    """Health/ping for the MCP server."""
    from . import __version__
    return {"status": "ok", "name": "adaptive-ui-runtime", "version": __version__}


def serve() -> None:
    mcp.run()


if __name__ == "__main__":
    serve()

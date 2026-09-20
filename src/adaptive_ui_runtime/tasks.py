"""Task-spec loading (issue #13/#15).

A task spec is declarative so the same file drives CLI, MCP and evaluation. It
can be YAML/JSON, and may reference a microbench task's own verifier rule.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Budget, Plan, Subtask, SuccessCriterion, TaskRequest


def _load_raw(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    text = p.read_text()
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PyYAML required for YAML task specs") from exc
        return yaml.safe_load(text)
    return json.loads(text)


def build_plan_from_spec(spec: dict[str, Any]) -> tuple[TaskRequest, Plan | None]:
    criteria = [SuccessCriterion(**c) for c in spec.get("success_criteria", [])]
    request = TaskRequest(
        goal=spec["goal"],
        success_criteria=criteria,
        constraints=spec.get("constraints", {}),
        start_url=spec.get("start_url"),
        preferred_transport=spec.get("preferred_transport"),
        budget=Budget(**spec["budget"]) if spec.get("budget") else Budget(),
    )
    raw_subtasks = spec.get("subtasks")
    if not raw_subtasks:
        return request, None
    subtasks = []
    for i, raw in enumerate(raw_subtasks):
        raw = dict(raw)
        raw.setdefault("id", f"s{i + 1}")
        raw["success_criteria"] = [
            SuccessCriterion(**c) if isinstance(c, dict) else c
            for c in raw.get("success_criteria", [])
        ] or criteria
        subtasks.append(Subtask(**raw))
    return request, Plan(goal=request.goal, subtasks=subtasks,
                         rationale="explicit task spec")


def load_task(path: str | Path) -> tuple[TaskRequest, Plan | None, dict[str, Any]]:
    spec = _load_raw(path)
    request, plan = build_plan_from_spec(spec)
    return request, plan, spec

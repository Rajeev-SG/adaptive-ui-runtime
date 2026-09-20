"""Strong long-context manager (issue #7).

Owns decomposition, ambiguity and exception recovery — not the inner click loop.
The manager keeps full task context; bounded workers receive only their subtask.
Uses Pydantic AI for typed outputs so downstream code never reinterprets prose.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from .contracts import Budget, Plan, RouteKind, Subtask, SuccessCriterion, TaskRequest

DEFAULT_MODEL = os.environ.get("AUR_MANAGER_MODEL", "openrouter:z-ai/glm-5.3-flash")

SYSTEM = """You are the planning layer of an adaptive UI runtime.

Decompose the user's goal into the smallest number of bounded subtasks that can
each be independently verified. Rules:

- Each subtask has an explicit, checkable success criterion.
- Prefer structured/deterministic execution; only allow visual routes when the
  target cannot be addressed structurally.
- Never plan a long-horizon stateful or DOM/eval-dependent workflow onto a bare
  visual worker (Fara/ShowUI). Those must be owned by you with structured steps.
- Budgets must be small and explicit.
- Return ONLY the requested JSON structure.

Allowed route values: deterministic, jev, structured_browser, showui, fara,
strong_manager.
"""


class ManagerPlanOut(BaseModel):
    subtasks: list[dict[str, Any]]
    rationale: str = ""


def _manager_available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY")) and not os.environ.get(
        "AUR_DISABLE_MANAGER"
    )


class Manager:
    """Typed planner. Falls back to a deterministic single-subtask plan when no
    strong model is configured, so the deterministic happy path needs no call.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model_name = model or DEFAULT_MODEL
        #: Explicit plan supplied by a caller (CLI/MCP/eval); bypasses planning.
        self.override_plan: Plan | None = None
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.latency_ms = 0.0
        self._agent = None

    def _build_agent(self):
        if self._agent is not None:
            return self._agent
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        )
        model = OpenAIChatModel(
            self.model_name.split(":", 1)[-1], provider=provider
        )
        self._agent = Agent(model, output_type=ManagerPlanOut, system_prompt=SYSTEM)
        return self._agent

    # -- planning ---------------------------------------------------------
    def plan(self, request: TaskRequest, prior: list[str] | None = None) -> Plan:
        if self.override_plan is not None:
            return self.override_plan
        if not _manager_available():
            return self._fallback_plan(request)
        try:
            return self._llm_plan(request, prior or [])
        except Exception as exc:  # schema/transport failure -> deterministic plan
            plan = self._fallback_plan(request)
            plan.rationale = f"manager unavailable ({exc.__class__.__name__}); {plan.rationale}"
            return plan

    def _llm_plan(self, request: TaskRequest, prior: list[str]) -> Plan:
        agent = self._build_agent()
        prompt = json.dumps(
            {
                "goal": request.goal,
                "success_criteria": [c.model_dump() for c in request.success_criteria],
                "constraints": request.constraints,
                "start_url": request.start_url,
                "prior_verified_outcomes": prior,
                "output_schema": {
                    "subtasks": [
                        {
                            "id": "s1",
                            "goal": "short imperative goal",
                            "success_criteria": [
                                {"kind": "dom_value|url|state|file|microbench",
                                 "description": "what must be true",
                                 "expected": "value",
                                 "rule": {"field": "state key"}}
                            ],
                            "allowed_routes": ["structured_browser"],
                            "budget": {"max_actions": 4, "max_wall_seconds": 30},
                            "task_class": "deterministic_dom|search_extract_act|"
                                          "dynamic_ui|form_filter_download|long_workflow|"
                                          "stateful_dom_eval|visual_fallback",
                            "side_effects": True,
                        }
                    ],
                    "rationale": "one sentence",
                },
            },
            indent=2,
        )
        start = time.perf_counter()
        result = agent.run_sync(prompt)
        self.latency_ms += (time.perf_counter() - start) * 1000.0
        self.calls += 1
        usage = getattr(result, "usage", None)
        if usage is not None:
            self.input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
            self.output_tokens += int(getattr(usage, "output_tokens", 0) or 0)
        out: ManagerPlanOut = result.output
        return self._coerce(out, request)

    def _coerce(self, out: ManagerPlanOut, request: TaskRequest) -> Plan:
        subtasks: list[Subtask] = []
        for i, raw in enumerate(out.subtasks):
            try:
                raw = dict(raw)
                raw.setdefault("id", f"s{i + 1}")
                raw.setdefault("success_criteria", [])
                crits = [
                    SuccessCriterion(**c) if isinstance(c, dict) else c
                    for c in raw["success_criteria"]
                ]
                if not crits:
                    crits = request.success_criteria
                raw["success_criteria"] = crits
                routes = [
                    RouteKind(r) for r in raw.get("allowed_routes", []) if r in set(RouteKind)
                ]
                if routes:
                    raw["allowed_routes"] = routes
                else:
                    raw.pop("allowed_routes", None)
                raw.setdefault("budget", Budget())
                subtasks.append(Subtask(**raw))
            except (ValidationError, TypeError) as exc:
                raise ValueError(f"invalid subtask {i}: {exc}") from exc
        if not subtasks:
            raise ValueError("manager returned no subtasks")
        return Plan(goal=request.goal, subtasks=subtasks,
                    rationale=out.rationale, manager_calls=self.calls)

    def _fallback_plan(self, request: TaskRequest) -> Plan:
        return Plan(
            goal=request.goal,
            subtasks=[
                Subtask(
                    id="s1",
                    goal=request.goal,
                    success_criteria=request.success_criteria,
                    budget=request.budget,
                    task_class="deterministic_dom",
                )
            ],
            rationale="deterministic fallback plan (no strong-model call)",
        )

    # -- recovery ---------------------------------------------------------
    def replan(self, request: TaskRequest, failure_class: str,
               detail: str, prior: list[str]) -> Plan:
        augmented = request.model_copy(deep=True)
        augmented.constraints = dict(augmented.constraints)
        augmented.constraints["previous_failure"] = failure_class
        augmented.constraints["previous_detail"] = detail[:500]
        return self.plan(augmented, prior)

    def usage(self) -> dict[str, Any]:
        return {
            "manager_calls": self.calls,
            "manager_input_tokens": self.input_tokens,
            "manager_output_tokens": self.output_tokens,
            "manager_latency_ms": round(self.latency_ms, 1),
        }

"""Core transport-neutral contracts.

Keep these contracts independent from a specific browser backend or model.
Concrete implementations are delivered through the roadmap issues.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RouteKind(StrEnum):
    DETERMINISTIC = "deterministic"
    JEV = "jev"
    STRUCTURED_BROWSER = "structured_browser"
    FARA = "fara"
    STRONG_MANAGER = "strong_manager"


class SuccessCriterion(BaseModel):
    kind: str
    description: str
    expected: Any | None = None


class Budget(BaseModel):
    max_actions: int = Field(default=8, ge=1)
    max_wall_seconds: float = Field(default=60.0, gt=0)
    max_unchanged_state_actions: int = Field(default=1, ge=0)
    max_verification_failures: int = Field(default=1, ge=0)


class TaskRequest(BaseModel):
    goal: str
    success_criteria: list[SuccessCriterion]
    constraints: dict[str, Any] = Field(default_factory=dict)


class Subtask(BaseModel):
    id: str
    goal: str
    preconditions: list[str] = Field(default_factory=list)
    success_criteria: list[SuccessCriterion]
    allowed_routes: list[RouteKind] = Field(default_factory=lambda: list(RouteKind))
    budget: Budget = Field(default_factory=Budget)


class Observation(BaseModel):
    snapshot_id: str
    state_fingerprint: str
    url: str | None = None
    structured_state: dict[str, Any] = Field(default_factory=dict)
    screenshot_ref: str | None = None


class CandidateAction(BaseModel):
    kind: str
    target: str | None = None
    value: Any | None = None


class RouteDecision(BaseModel):
    route: RouteKind
    reason: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class ActionResult(BaseModel):
    ok: bool
    changed_state: bool
    snapshot_id: str | None = None
    latency_ms: float | None = None
    error_class: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    passed: bool
    failure_class: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class RunResult(BaseModel):
    run_id: str
    status: RunStatus
    verified: bool
    result: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)


EvaluationMode = Literal[
    "adaptive",
    "strong_only",
    "no_jev",
    "no_fara",
    "deterministic_only",
]

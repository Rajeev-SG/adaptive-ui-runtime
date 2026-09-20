"""Core transport-neutral contracts.

Keep these contracts independent from a specific browser backend or model.
Concrete implementations are delivered through the roadmap issues.

Everything downstream (transports, workers, router, verifier, recovery, MCP)
shares these types so the agent-facing surface never leaks a backend.
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
    SHOWUI = "showui"
    FARA = "fara"
    STRONG_MANAGER = "strong_manager"


class SubtaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureClass(StrEnum):
    """Classified failure buckets (issue #11). Infrastructure is never merged
    into model quality."""

    STALE_TARGET = "stale_target"
    FOCUS_LOST = "focus_lost"
    OBSTRUCTION = "obstruction"
    DOM_DRIFT = "dom_drift"
    TARGET_UNAVAILABLE = "target_unavailable"
    TRANSPORT_ERROR = "transport_error"
    NAVIGATION_DRIFT = "navigation_drift"
    VISUAL_ONLY_TARGET = "visual_only_target"
    REPEATED_ACTION_LOOP = "repeated_action_loop"
    PREMATURE_DONE = "premature_done"
    VERIFIER_MISMATCH = "verifier_mismatch"
    POLICY_FAILURE = "policy_failure"
    GROUNDING_FAILURE = "grounding_failure"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNEXPECTED_STATE = "unexpected_state"
    VERIFIER_ERROR = "verifier_error"
    TEST_RESET_FAILURE = "test_reset_failure"


class SuccessCriterion(BaseModel):
    kind: str
    description: str
    expected: Any | None = None
    # Optional microbench-style declarative rule payload.
    rule: dict[str, Any] | None = None


class Budget(BaseModel):
    max_actions: int = Field(default=8, ge=1)
    max_wall_seconds: float = Field(default=60.0, gt=0)
    max_unchanged_state_actions: int = Field(default=1, ge=0)
    max_verification_failures: int = Field(default=1, ge=0)


class TaskRequest(BaseModel):
    goal: str
    success_criteria: list[SuccessCriterion]
    constraints: dict[str, Any] = Field(default_factory=dict)
    start_url: str | None = None
    preferred_transport: str | None = None
    budget: Budget = Field(default_factory=Budget)


class Subtask(BaseModel):
    id: str
    goal: str
    preconditions: list[str] = Field(default_factory=list)
    success_criteria: list[SuccessCriterion]
    allowed_routes: list[RouteKind] = Field(default_factory=lambda: list(RouteKind))
    budget: Budget = Field(default_factory=Budget)
    # Routing hints supplied by the manager (issue #7/#12).
    task_class: str | None = None
    side_effects: bool = True
    depends_on: list[str] = Field(default_factory=list)
    recovery_hint: str | None = None
    #: Concrete structured steps for the deterministic/structured route:
    #: [{"kind": "type", "target": "field", "value": "..."}]. When present these
    #: are executed in order with no model inference.
    steps: list[dict[str, Any]] = Field(default_factory=list)


class Plan(BaseModel):
    goal: str
    subtasks: list[Subtask]
    rationale: str = ""
    manager_calls: int = 0


class Target(BaseModel):
    """A structured, transport-neutral addressable element."""

    id: str
    kind: str
    label: str = ""
    role: str = ""
    node: int | None = None
    value: str = ""


class Observation(BaseModel):
    snapshot_id: str
    state_fingerprint: str
    url: str | None = None
    targets: list[Target] = Field(default_factory=list)
    structured_state: dict[str, Any] = Field(default_factory=dict)
    screenshot_ref: str | None = None
    transport: str | None = None


class CandidateAction(BaseModel):
    kind: str
    target: str | None = None
    value: Any | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    # Provenance: which worker proposed this.
    source: str = ""


class RouteDecision(BaseModel):
    route: RouteKind
    reason: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    alternatives: list[str] = Field(default_factory=list)
    escalation: RouteKind | None = None
    budget_actions: int | None = None


class ActionResult(BaseModel):
    ok: bool
    changed_state: bool
    snapshot_id: str | None = None
    latency_ms: float | None = None
    error_class: str | None = None
    detail: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    passed: bool
    failure_class: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    latency_ms: float | None = None
    error: bool = False


class WorkerResult(BaseModel):
    """Factual result from a bounded worker. Never authoritative success."""

    proposed: list[CandidateAction] = Field(default_factory=list)
    done: bool = False
    confidence: float | None = Field(default=None, ge=0, le=1)
    detail: str = ""
    calls: int = 0
    latency_ms: float | None = None


class TraceEvent(BaseModel):
    run_id: str
    seq: int
    kind: str
    at_ms: float
    data: dict[str, Any] = Field(default_factory=dict)


class RunResult(BaseModel):
    run_id: str
    status: RunStatus
    verified: bool
    result: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    failure_class: str | None = None


class RunState(BaseModel):
    """Durable run record (issue #3/#11)."""

    run_id: str
    goal: str
    status: RunStatus = RunStatus.PENDING
    plan: Plan | None = None
    current_subtask: str | None = None
    subtask_status: dict[str, SubtaskStatus] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    failure_class: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)


EvaluationMode = Literal[
    "adaptive",
    "strong_only",
    "no_jev",
    "no_fara",
    "no_showui",
    "deterministic_only",
]


class RuntimeConfig(BaseModel):
    """Explicit, snapshot-able policy configuration (issue #12)."""

    mode: EvaluationMode = "adaptive"
    jev_confidence_threshold: float = Field(default=0.6, ge=0, le=1)
    enable_jev: bool = True
    enable_fara: bool = True
    enable_showui: bool = True
    enable_strong_manager: bool = True
    max_escalations: int = Field(default=3, ge=0)
    shadow_mode: bool = False
    shadow_sample: float = Field(default=0.0, ge=0, le=1)
    transports: list[str] = Field(default_factory=lambda: ["relay", "playwriter", "fake"])
    #: Fara 9B is excluded from v1 routing by measured evidence (local_cua PR #16).
    allow_fara_9b: bool = False

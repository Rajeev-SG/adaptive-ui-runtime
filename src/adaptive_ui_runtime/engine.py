"""Core runtime engine (composes every layer).

Pipeline (epic #1):

    strong manager -> deterministic/structured actions -> Jev fast path
    -> ShowUI/Fara bounded visual -> independent verifier
    -> classified bounded recovery -> manager replan only when required

Every state-changing subtask is verified independently. Actor `DONE` is only a
proposal. No unbounded loops.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .contracts import (
    ActionResult,
    CandidateAction,
    FailureClass,
    Observation,
    Plan,
    RouteDecision,
    RouteKind,
    RunResult,
    RunState,
    RunStatus,
    RuntimeConfig,
    Subtask,
    SubtaskStatus,
    TaskRequest,
)
from .durability import default_store
from .manager import Manager
from .recovery import CycleDetector, RecoveryPolicy
from .router import AdaptiveRouter
from .tracing import Metrics, Tracer
from .transports.base import StaleTargetError, Transport, TransportError
from .verifier import Verifier
from .workers.jev import JevWorker
from .workers.visual import LocalVisualWorker


class Engine:
    """Executes a TaskRequest end to end over a transport."""

    def __init__(
        self,
        transport: Transport,
        config: RuntimeConfig | None = None,
        manager: Manager | None = None,
        store: Any | None = None,
    ) -> None:
        self.transport = transport
        self.config = config or RuntimeConfig()
        self.manager = manager or Manager()
        self.store = store or default_store()
        self.router = AdaptiveRouter(self.config)
        self.verifier = Verifier(transport)
        self.recovery = RecoveryPolicy(max_attempts=max(1, self.config.max_escalations))
        self.cycle = CycleDetector(limit=1)  # same state+action repeated -> loop
        self.jev = JevWorker(threshold=self.config.jev_confidence_threshold)
        self.fara = LocalVisualWorker(kind="fara")
        self.showui = LocalVisualWorker(kind="showui")
        self.tracer: Tracer = Tracer('unstarted')
        self.metrics = Metrics()
        self._last_plan: Plan | None = None

    # -- public API -------------------------------------------------------
    def execute(self, request: TaskRequest, run_id: str | None = None) -> RunResult:
        run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.tracer = Tracer(run_id)
        self.metrics = Metrics()
        state = RunState(run_id=run_id, goal=request.goal, status=RunStatus.RUNNING)
        start = time.perf_counter()
        self.tracer.emit("run_start", goal=request.goal, mode=self.config.mode)

        if request.start_url and self.transport.supports("navigate"):
            self.transport.navigate(request.start_url)
        self.store.save(state)

        plan = self.manager.plan(request)
        # A caller-supplied plan must never be replaced. Only synthesize a
        # deterministic fallback when no plan was provided at all.
        if (self.manager.override_plan is None
                and not self.config.enable_strong_manager
                and plan.manager_calls == 0):
            plan = self.manager._fallback_plan(request)
        self._last_plan = plan
        state.plan = plan
        state.subtask_status = {s.id: SubtaskStatus.PENDING for s in plan.subtasks}
        self.tracer.emit("plan", subtasks=[s.id for s in plan.subtasks],
                         rationale=plan.rationale)
        self.store.save(state)

        verified_outcomes: list[str] = []
        overall_passed = True
        failure_class: str | None = None

        for subtask in plan.subtasks:
            result = self._run_subtask(subtask, request, verified_outcomes)
            state.subtask_status[subtask.id] = (
                SubtaskStatus.VERIFIED if result["passed"] else SubtaskStatus.FAILED
            )
            state.current_subtask = subtask.id
            self.store.save(state)
            if result["passed"]:
                verified_outcomes.append(f"{subtask.id}: verified")
            else:
                overall_passed = False
                failure_class = result.get("failure_class")
                self.tracer.emit("subtask_failed", subtask=subtask.id,
                                 failure_class=failure_class)
                break
        else:
            state.status = RunStatus.SUCCEEDED

        if not overall_passed:
            state.status = RunStatus.FAILED
            state.failure_class = failure_class

        wall_ms = (time.perf_counter() - start) * 1000.0
        state.metrics = self._collect_metrics(wall_ms)
        state.result = {"verified": overall_passed,
                        "outcomes": verified_outcomes}
        self.store.save(state)
        self.tracer.emit("run_end", status=str(state.status),
                         verified=overall_passed, failure_class=failure_class,
                         wall_ms=round(wall_ms, 1))
        self.tracer.flush()

        return RunResult(
            run_id=run_id,
            status=state.status,
            verified=overall_passed,
            result=state.result,
            metrics=state.metrics,
            failure_class=failure_class,
        )

    # -- subtask loop -----------------------------------------------------
    def _run_subtask(self, subtask: Subtask, request: TaskRequest,
                     prior: list[str]) -> dict[str, Any]:
        self.tracer.emit("subtask_start", subtask=subtask.id, goal=subtask.goal,
                         task_class=subtask.task_class)
        budget = subtask.budget
        deadline = time.perf_counter() + budget.max_wall_seconds
        actions = 0
        verify_failures = 0
        escalations = 0
        step_index = 0
        prior_failures: list[str] = []

        while actions < budget.max_actions and time.perf_counter() < deadline:
            _t0 = time.perf_counter()
            obs = self.transport.observe()
            self.metrics.inc("observations")
            self.metrics.time("observe_ms", (time.perf_counter() - _t0) * 1000.0)

            decision = self.router.route(
                subtask, obs, self.transport.name, self.transport.capabilities,
                structured_truth=bool(obs.targets), prior_failures=prior_failures,
                escalations=escalations,
            )
            self.tracer.emit("route", subtask=subtask.id, route=str(decision.route),
                             reason=decision.reason, confidence=decision.confidence)

            if (decision.route in (RouteKind.DETERMINISTIC, RouteKind.STRUCTURED_BROWSER)
                    and subtask.steps and step_index >= len(subtask.steps)):
                proposal = self._proposal([], done=True)  # all steps executed
            elif (decision.route in (RouteKind.DETERMINISTIC, RouteKind.STRUCTURED_BROWSER)
                    and subtask.steps):
                raw = self._resolve_step(subtask.steps[step_index], obs)
                if raw is None:
                    prior_failures.append(FailureClass.UNEXPECTED_STATE)
                    escalations += 1
                    if escalations > self.config.max_escalations:
                        return {"passed": False,
                                "failure_class": FailureClass.UNEXPECTED_STATE}
                    continue
                proposal = self._proposal([CandidateAction(
                    kind=raw.get("kind", "click"), target=raw.get("target"),
                    value=raw.get("value"), confidence=1.0, source="step")])
            else:
                proposal = self._decide(decision, subtask, obs)
            if proposal is None:
                # No cheap route could decide -> manager owns the loop.
                failure = self.recovery.classify("no decision", verifier_failed=False)
                prior_failures.append(str(failure))
                escalations += 1
                self.metrics.inc("fallbacks")
                self.tracer.emit("escalate", subtask=subtask.id, failure_class=str(failure))
                if escalations > self.config.max_escalations:
                    return {"passed": False, "failure_class": str(failure)}
                continue

            if proposal.done:
                vr = self.verifier.check(subtask.success_criteria, obs)
                self.metrics.inc("verifications")
                self.metrics.time("verify_ms", vr.latency_ms or 0.0)
                self.tracer.emit("verify", subtask=subtask.id, passed=vr.passed,
                                 failure_class=vr.failure_class)
                if vr.passed:
                    return {"passed": True}
                # Premature DONE
                self.metrics.fail(FailureClass.PREMATURE_DONE)
                self.metrics.inc("fallbacks")
                prior_failures.append(FailureClass.PREMATURE_DONE)
                escalations += 1
                if escalations > self.config.max_escalations:
                    return {"passed": False, "failure_class": FailureClass.PREMATURE_DONE}
                continue

            for action in proposal.proposed:
                actions += 1
                self.metrics.inc("actions")
                step_executed = None
                if subtask.steps and decision.route in (
                        RouteKind.DETERMINISTIC, RouteKind.STRUCTURED_BROWSER):
                    step_executed = step_index
                    step_index += 1
                result = self._act(action, obs)
                self.metrics.inc("transport_commands")
                # Cycle detection applies to *successful* actions only; a failed
                # action is a repair candidate, not a loop.
                if result.ok:
                    repeated, count = self.cycle.observe(obs, action)
                    if repeated:
                        self.metrics.inc("loops")
                        self.metrics.fail(FailureClass.REPEATED_ACTION_LOOP)
                        self.tracer.emit("cycle_detected", subtask=subtask.id,
                                         action_kind=action.kind,
                                         target=action.target, repeats=count)
                        return {"passed": False,
                                "failure_class": FailureClass.REPEATED_ACTION_LOOP}
                if result.latency_ms:
                    self.metrics.time("action_ms", result.latency_ms)
                self.tracer.emit("action", subtask=subtask.id, action_kind=action.kind,
                                 target=action.target, ok=result.ok,
                                 error_class=result.error_class)

                if not result.ok:
                    if step_executed is not None:
                        step_index = step_executed
                    failure = self.recovery.classify(result.error_class)
                    self.metrics.fail(str(failure))
                    self.tracer.emit("failure", subtask=subtask.id,
                                     failure_class=str(failure))
                    if self.recovery.exhausted(str(failure)):
                        self.metrics.inc("fallbacks")
                        prior_failures.append(str(failure))
                        escalations += 1
                        if escalations > self.config.max_escalations:
                            return {"passed": False, "failure_class": str(failure)}
                        continue
                    outcome = self.recovery.repair(
                        str(failure), self.transport, target=None,
                        retry=lambda tgt, _a=action, _o=obs: self._act(_a, _o),
                    )
                    self.metrics.inc("recoveries")
                    self.tracer.emit("repair", subtask=subtask.id,
                                     capability=outcome.detail,
                                     repaired=outcome.repaired)
                    if not outcome.repaired:
                        prior_failures.append(str(failure))
                        escalations += 1
                        if escalations > self.config.max_escalations:
                            return {"passed": False, "failure_class": str(failure)}
                    continue

                # Verify after every material state-changing action.
                if result.changed_state:
                    obs2 = self.transport.observe()
                    self.metrics.inc("observations")
                    vr = self.verifier.check(subtask.success_criteria, obs2)
                    self.metrics.inc("verifications")
                    self.metrics.time("verify_ms", vr.latency_ms or 0.0)
                    self.tracer.emit("verify", subtask=subtask.id,
                                     passed=vr.passed, failure_class=vr.failure_class)
                    if vr.passed:
                        return {"passed": True}
                    # An intermediate step not yet satisfying the final criterion
                    # is expected; only a real mismatch accrues failures.
                    if not subtask.steps:
                        verify_failures += 1
                        self.metrics.fail(FailureClass.VERIFIER_MISMATCH)
                    if verify_failures > budget.max_verification_failures:
                        prior_failures.append(FailureClass.VERIFIER_MISMATCH)
                        escalations += 1
                        if escalations > self.config.max_escalations:
                            return {"passed": False,
                                    "failure_class": FailureClass.VERIFIER_MISMATCH}

        fc = FailureClass.BUDGET_EXCEEDED
        self.metrics.fail(fc)
        return {"passed": False, "failure_class": fc}

    def _resolve_step(self, raw: dict[str, Any],
                      obs: Observation) -> dict[str, Any] | None:
        """Bind a declarative step's selector-free target to an observed node.

        A step may name a target by id, or use `target_any` (a role/kind) to take
        the first observed match. The worker never emits a selector.
        """
        raw = dict(raw)
        tid = raw.get("target")
        if tid and tid in {t.id for t in obs.targets}:
            return raw
        want = raw.get("target_any") or raw.get("target_kind")
        if want:
            for t in obs.targets:
                if t.kind == want or t.role == want:
                    raw["target"] = t.id
                    return raw
            return None
        if not tid:
            return raw  # target-less action (key/scroll/wait)
        # named target not present
        return None

    # -- decision dispatch ------------------------------------------------
    def _decide(self, decision: RouteDecision, subtask: Subtask,
                obs: Observation) -> Any | None:
        route = decision.route
        if route == RouteKind.DETERMINISTIC:
            return self._deterministic(subtask, obs)
        if route == RouteKind.STRUCTURED_BROWSER:
            return self._structured(subtask, obs)
        if route == RouteKind.JEV and self.config.enable_jev:
            self.metrics.inc("jev_calls")
            result = self.jev.decide(obs, subtask.goal)
            if result.latency_ms:
                self.metrics.time("jev_ms", result.latency_ms)
            if not result.proposed and not result.done:
                self.metrics.inc("fallbacks")
                return None
            return result
        if route == RouteKind.SHOWUI and self.config.enable_showui:
            self.metrics.inc("showui_calls")
            return self.showui.propose(obs, subtask.goal,
                                       subtask.task_class or "visual_grounding")
        if route == RouteKind.FARA and self.config.enable_fara:
            self.metrics.inc("fara_calls")
            return self.fara.propose(obs, subtask.goal,
                                     subtask.task_class or "visual_grounding")
        # strong_manager route with no cheap mechanism -> manager decides
        return self._manager_decision(subtask, obs)

    def _query_goal(self, subtask: Subtask) -> dict[str, Any]:
        return dict(subtask.budget.__dict__)

    @staticmethod
    def _proposal(actions: list[CandidateAction], done: bool = False,
                  confidence: float = 1.0) -> Any:
        return type("Proposal", (), {
            "proposed": actions, "done": done, "confidence": confidence,
            "latency_ms": 0.0, "detail": "structural",
        })()

    def _deterministic(self, subtask: Subtask, obs: Observation) -> Any | None:
        """Known structured action: pick the first target matching the goal."""
        return self._structured(subtask, obs)

    def _typed_value(self, subtask: Subtask, obs: Observation) -> str:
        """The value to type: explicit constraint > state hint > expected value."""
        if "next_value" in obs.structured_state:
            return str(obs.structured_state["next_value"])
        if subtask.task_class == "clear":
            return ""
        for crit in subtask.success_criteria:
            exp = crit.expected
            if isinstance(exp, str) and exp:
                return exp
        return ""

    def _structured(self, subtask: Subtask, obs: Observation) -> Any | None:
        """Resolve a target from the observation without model inference."""
        goal = subtask.goal.lower()
        for t in obs.targets:
            label = (t.label or t.id).lower()
            if t.id.lower() in goal or (label and label in goal):
                kind = {"fill": "type", "click": "click", "button": "click"}.get(
                    t.kind, "click")
                value = None
                if kind == "type":
                    value = self._typed_value(subtask, obs)
                return self._proposal([CandidateAction(
                    kind=kind, target=t.id, value=value,
                    confidence=1.0, source="structured")])
        # state-based deterministic fallback for the fake app
        state = obs.structured_state
        if "clear" in goal and state.get("field"):
            return self._proposal([CandidateAction(
                kind="type", target="field", value="",
                confidence=1.0, source="structured")])
        return None

    def _manager_decision(self, subtask: Subtask, obs: Observation) -> Any | None:
        """Manager-owned structured step: choose the next target deterministically
        from observed state (the DOM/eval channel), not from a visual model."""
        if not self.config.enable_strong_manager:
            return None
        proposal = self._structured(subtask, obs)
        if proposal is not None:
            return proposal
        # Nothing left to do structurally -> propose DONE for the verifier.
        return self._proposal([], done=True)

    # -- action execution -------------------------------------------------
    #: Actions that do not address a specific element.
    TARGETLESS = {"key", "scroll", "wait", "focus"}

    def _act(self, action: CandidateAction, obs: Observation) -> ActionResult:
        if action.kind in self.TARGETLESS:
            try:
                if action.kind == "key":
                    return self.transport.key(str(action.value or "Enter"))
                if action.kind == "scroll":
                    return self.transport.scroll(int(action.value or 1))
                if action.kind == "focus":
                    return self.transport.focus()
                return self.transport.wait(float(action.value or 0.1))
            except TransportError as exc:
                return ActionResult(ok=False, changed_state=False,
                                    error_class=exc.error_class, detail=str(exc))
        target = next((t for t in obs.targets if t.id == action.target), None)
        if target is None:
            return ActionResult(ok=False, changed_state=False,
                                error_class="stale_target",
                                detail=f"target {action.target} not observed")
        try:
            if action.kind in ("click", "press"):
                return self.transport.click(target)
            if action.kind in ("type", "fill", "input"):
                return self.transport.type(target, str(action.value or ""))
            if action.kind == "key":
                return self.transport.key(str(action.value or "Enter"))
            if action.kind == "select":
                return self.transport.select(target, str(action.value or ""))
            if action.kind == "scroll":
                return self.transport.scroll(int(action.value or 1))
            if action.kind == "inspect":
                return ActionResult(ok=True, changed_state=False)
            return ActionResult(ok=False, changed_state=False,
                                error_class="policy_failure",
                                detail=f"unsupported action {action.kind}")
        except StaleTargetError as exc:
            return ActionResult(ok=False, changed_state=False,
                                error_class="stale_target", detail=str(exc))
        except TransportError as exc:
            return ActionResult(ok=False, changed_state=False,
                                error_class=exc.error_class, detail=str(exc))

    # -- metrics ----------------------------------------------------------
    def _collect_metrics(self, wall_ms: float) -> dict[str, Any]:
        metrics = self.metrics.summary()
        metrics["wall_ms"] = round(wall_ms, 1)
        metrics.update(self.manager.usage())
        metrics.update(self.jev.usage())
        metrics.update(self.fara.usage())
        metrics.update(self.showui.usage())
        metrics["config"] = self.config.model_dump()
        metrics["transport"] = self.transport.name
        return metrics


def plan_only(request: TaskRequest, config: RuntimeConfig | None = None) -> dict[str, Any]:
    """ui.plan: return the proposed strategy without executing it."""
    manager = Manager()
    plan = manager.plan(request)
    router = AdaptiveRouter(config or RuntimeConfig())
    routes = []
    for st in plan.subtasks:
        decision = router.route(st, None, "n/a", frozenset(), structured_truth=True)
        routes.append({"subtask": st.id, "route": str(decision.route),
                       "reason": decision.reason})
    return {"goal": plan.goal, "subtasks": [s.model_dump(mode="json")
                                            for s in plan.subtasks],
            "routes": routes, "rationale": plan.rationale}

"""Anti-thrash cycle detection + classified bounded recovery (issue #11).

The bespoke layer here is deliberately small: it *classifies* a failure, chooses
an *existing* repair capability, enforces a budget and re-verifies. It does not
implement browser self-healing itself.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .contracts import ActionResult, FailureClass, Observation, RouteKind


@dataclass
class CycleDetector:
    """Rolling (state_fingerprint, action_kind, target, value) key.

    If materially identical state receives the same ineffective action beyond
    the configured limit, stop the worker and escalate — never spend the
    remaining budget repeating the same guess.
    """

    limit: int = 1
    keys: list[str] = field(default_factory=list)

    def key(self, obs: Observation, action: Any) -> str:
        target = getattr(action, "target", None) or ""
        value = getattr(action, "value", None) or ""
        kind = getattr(action, "kind", "") or ""
        return f"{obs.state_fingerprint}|{kind}|{target}|{value}"

    def observe(self, obs: Observation, action: Any) -> tuple[bool, int]:
        k = self.key(obs, action)
        repeats = self.keys.count(k)
        self.keys.append(k)
        return repeats >= self.limit, repeats + 1

    def reset(self) -> None:
        self.keys.clear()


#: failure class -> (first repair capability, next escalation route)
REPAIR_TABLE: dict[str, tuple[str, RouteKind]] = {
    FailureClass.STALE_TARGET: ("reobserve_rebind", RouteKind.STRUCTURED_BROWSER),
    FailureClass.FOCUS_LOST: ("focus", RouteKind.STRUCTURED_BROWSER),
    FailureClass.OBSTRUCTION: ("dismiss_and_reobserve", RouteKind.STRUCTURED_BROWSER),
    FailureClass.DOM_DRIFT: ("semantic_rebind", RouteKind.STRUCTURED_BROWSER),
    FailureClass.TARGET_UNAVAILABLE: ("visual_ground", RouteKind.SHOWUI),
    FailureClass.VISUAL_ONLY_TARGET: ("visual_ground", RouteKind.FARA),
    FailureClass.TRANSPORT_ERROR: ("switch_transport", RouteKind.STRUCTURED_BROWSER),
    FailureClass.NAVIGATION_DRIFT: ("renavigate", RouteKind.STRUCTURED_BROWSER),
    FailureClass.PREMATURE_DONE: ("reverify_then_alternate", RouteKind.STRONG_MANAGER),
    FailureClass.VERIFIER_MISMATCH: ("reobserve_rebind", RouteKind.STRONG_MANAGER),
    FailureClass.REPEATED_ACTION_LOOP: ("terminate_and_escalate", RouteKind.STRONG_MANAGER),
    FailureClass.UNEXPECTED_STATE: ("manager_replan", RouteKind.STRONG_MANAGER),
    FailureClass.GROUNDING_FAILURE: ("visual_ground", RouteKind.STRONG_MANAGER),
    FailureClass.POLICY_FAILURE: ("alternate_route", RouteKind.STRONG_MANAGER),
    FailureClass.BUDGET_EXCEEDED: ("manager_replan", RouteKind.STRONG_MANAGER),
}


@dataclass
class RepairOutcome:
    repaired: bool
    detail: str
    latency_ms: float
    action: ActionResult | None = None


class RecoveryPolicy:
    """Classify a failure and invoke the best existing repair capability."""

    def __init__(self, max_attempts: int = 2) -> None:
        self.max_attempts = max_attempts
        self.attempts: dict[str, int] = {}
        self.events: list[dict[str, Any]] = []

    def classify(self, error: str | None, verifier_failed: bool = False,
                 repeated: bool = False) -> str:
        if repeated:
            return FailureClass.REPEATED_ACTION_LOOP
        if verifier_failed:
            return FailureClass.VERIFIER_MISMATCH
        if not error:
            return FailureClass.UNEXPECTED_STATE
        e = error.lower()
        if "stale" in e:
            return FailureClass.STALE_TARGET
        if "focus" in e:
            return FailureClass.FOCUS_LOST
        if "modal" in e or "obstruct" in e or "intercept" in e:
            return FailureClass.OBSTRUCTION
        if "drift" in e:
            return FailureClass.DOM_DRIFT
        if "transport" in e or "connection" in e or "closed" in e:
            return FailureClass.TRANSPORT_ERROR
        if "navigation" in e or "url" in e:
            return FailureClass.NAVIGATION_DRIFT
        if "budget" in e:
            return FailureClass.BUDGET_EXCEEDED
        return FailureClass.UNEXPECTED_STATE

    def exhausted(self, failure_class: str) -> bool:
        return self.attempts.get(failure_class, 0) >= self.max_attempts

    def repair(
        self,
        failure_class: str,
        transport: Any,
        target: Any = None,
        retry: Any = None,
    ) -> RepairOutcome:
        start = time.perf_counter()
        self.attempts[failure_class] = self.attempts.get(failure_class, 0) + 1
        capability, escalation = REPAIR_TABLE.get(
            failure_class, ("manager_replan", RouteKind.STRONG_MANAGER)
        )
        action: ActionResult | None = None
        detail = f"capability={capability}"

        # Invoke an *existing* capability where the transport exposes one.
        if capability == "focus" and hasattr(transport, "focus"):
            action = transport.focus()
        elif capability in ("reobserve_rebind", "semantic_rebind", "dismiss_and_reobserve"):
            if capability == "dismiss_and_reobserve" and hasattr(transport, "evaluate"):
                try:
                    transport.evaluate("dismiss_modal")
                except Exception:
                    pass
            if retry is not None and target is not None:
                try:
                    action = retry(target)
                except Exception as exc:
                    detail += f"; retry failed: {exc}"
        elif capability == "renavigate" and hasattr(transport, "navigate"):
            pass  # caller supplies the URL through retry

        latency = (time.perf_counter() - start) * 1000.0
        repaired = bool(action and action.ok)
        event = {
            "failure_class": failure_class,
            "capability": capability,
            "escalation": str(escalation),
            "repaired": repaired,
            "attempt": self.attempts[failure_class],
            "latency_ms": latency,
        }
        self.events.append(event)
        return RepairOutcome(repaired=repaired, detail=detail,
                             latency_ms=latency, action=action)

    def escalation_route(self, failure_class: str) -> RouteKind:
        return REPAIR_TABLE.get(failure_class, ("", RouteKind.STRONG_MANAGER))[1]

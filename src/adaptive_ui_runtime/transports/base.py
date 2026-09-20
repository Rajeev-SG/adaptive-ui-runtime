"""Capability-aware transport protocol (issue #4).

Reused contract provenance: `Rajeev-SG/jev-tests@4e5ed27`
`src/jev_tests/bridge.py` — the safety property preserved here is:

    a worker selects an *observed* semantic/indexed target;
    code revalidates that exact target;
    the transport executes the concrete action.

The model/worker never emits a raw CSS selector, coordinate, JavaScript or shell
command as part of the normal action contract.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Protocol, runtime_checkable

from ..contracts import ActionResult, Observation, Target

#: Capability flags a transport advertises so the router can choose honestly
#: instead of pretending every backend is identical.
CAPABILITIES = (
    "navigate",
    "observe",
    "click",
    "type",
    "key",
    "select",
    "scroll",
    "wait",
    "focus",
    "screenshot",
    "evaluate",
    "download",
)


class TransportError(RuntimeError):
    """Transport/infrastructure failure — never merged into model quality."""

    def __init__(self, message: str, error_class: str = "transport_error") -> None:
        super().__init__(message)
        self.error_class = error_class


class StaleTargetError(TransportError):
    def __init__(self, message: str = "observed target is stale") -> None:
        super().__init__(message, error_class="stale_target")


@runtime_checkable
class Transport(Protocol):
    name: str
    capabilities: frozenset[str]

    def supports(self, capability: str) -> bool: ...
    def navigate(self, url: str) -> ActionResult: ...
    def observe(self) -> Observation: ...
    def click(self, target: Target) -> ActionResult: ...
    def type(self, target: Target, text: str) -> ActionResult: ...
    def key(self, key: str) -> ActionResult: ...
    def select(self, target: Target, value: str) -> ActionResult: ...
    def scroll(self, delta: int) -> ActionResult: ...
    def wait(self, seconds: float) -> ActionResult: ...
    def focus(self) -> ActionResult: ...
    def screenshot(self) -> str | None: ...
    def evaluate(self, expression: str) -> Any: ...
    def close(self) -> None: ...


def fingerprint(payload: dict[str, Any]) -> str:
    """Material-state fingerprint used by observe() and cycle detection."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:32]


def timed(fn, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    value = fn(*args, **kwargs)
    return value, (time.perf_counter() - start) * 1000.0

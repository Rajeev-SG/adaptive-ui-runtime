"""Deterministic in-memory transport + fixture app (issue #2).

Lets the whole `execute -> verify -> result` path be tested with no browser,
and is the same fixture used for the cross-transport parity tests (#5).
"""

from __future__ import annotations

from typing import Any

from ..contracts import ActionResult, Observation, Target
from .base import CAPABILITIES, StaleTargetError, TransportError, fingerprint


class FakeApp:
    """A tiny deterministic app: a text field, a search button, an add button."""

    def __init__(self) -> None:
        self.url = "https://fake.test/"
        self.field = ""
        self.items: list[str] = []
        self.focused = True
        self.modal = False
        self.version = 0

    def state(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "field": self.field,
            "items": list(self.items),
            "modal": self.modal,
        }


class FakeTransport:
    name = "fake"
    capabilities = frozenset(CAPABILITIES)

    def __init__(self, app: FakeApp | None = None) -> None:
        self.app = app or FakeApp()
        self.commands = 0
        self._node_epoch = 0
        self.fail_next: str | None = None

    # -- protocol ---------------------------------------------------------
    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def _bump(self) -> None:
        self.app.version += 1
        self._node_epoch += 1

    def _targets(self) -> list[Target]:
        return [
            Target(id="field", kind="fill", label="Search", role="textbox",
                   node=self._node_epoch * 10 + 1, value=self.app.field),
            Target(id="search", kind="click", label="Search", role="button",
                   node=self._node_epoch * 10 + 2),
            Target(id="add", kind="click", label="Add item", role="button",
                   node=self._node_epoch * 10 + 3),
        ]

    def observe(self) -> Observation:
        self.commands += 1
        return Observation(
            snapshot_id=f"snap-{self.app.version}",
            state_fingerprint=fingerprint(self.app.state()),  # material state only
            url=self.app.url,
            targets=self._targets(),
            structured_state=self.app.state(),
            transport=self.name,
        )

    def _check(self, target: Target) -> None:
        if self.fail_next == "stale":
            self.fail_next = None
            raise StaleTargetError(f"target {target.id} is stale")
        if self.fail_next:
            name, self.fail_next = self.fail_next, None
            raise TransportError(f"injected {name}", error_class=name)
        known = {t.id: t for t in self._targets()}
        if target.id not in known:
            raise StaleTargetError(f"unknown target {target.id}")
        if target.node is not None and known[target.id].node != target.node:
            raise StaleTargetError(
                f"target {target.id} node {target.node} != {known[target.id].node}"
            )

    def navigate(self, url: str) -> ActionResult:
        self.commands += 1
        self.app.url = url
        self._bump()
        return ActionResult(ok=True, changed_state=True)

    def click(self, target: Target) -> ActionResult:
        self.commands += 1
        self._check(target)
        if self.app.modal and target.id != "search":
            return ActionResult(ok=False, changed_state=False,
                                error_class="obstruction", detail="modal open")
        if target.id == "search":
            if self.app.field:
                self.app.items.append(self.app.field)
                self.app.field = ""
        elif target.id == "add":
            self.app.items.append("(empty)")
        self._bump()
        return ActionResult(ok=True, changed_state=True)

    def type(self, target: Target, text: str) -> ActionResult:
        self.commands += 1
        self._check(target)
        self.app.field = text
        self._bump()
        return ActionResult(ok=True, changed_state=True)

    def key(self, key: str) -> ActionResult:
        self.commands += 1
        if key in ("Enter", "Return"):
            if self.app.field:
                self.app.items.append(self.app.field)
                self.app.field = ""
        self._bump()
        return ActionResult(ok=True, changed_state=True)

    def select(self, target: Target, value: str) -> ActionResult:
        self.commands += 1
        self._check(target)
        return ActionResult(ok=True, changed_state=True)

    def scroll(self, delta: int) -> ActionResult:
        self.commands += 1
        return ActionResult(ok=True, changed_state=False)

    def wait(self, seconds: float) -> ActionResult:
        self.commands += 1
        return ActionResult(ok=True, changed_state=False)

    def focus(self) -> ActionResult:
        self.commands += 1
        self.app.focused = True
        return ActionResult(ok=True, changed_state=False)

    def screenshot(self) -> str | None:
        self.commands += 1
        return f"fake://{self.app.version}.png"

    def evaluate(self, expression: str) -> Any:
        self.commands += 1
        if expression == "items":
            return list(self.app.items)
        if expression == "url":
            return self.app.url
        return None

    def close(self) -> None:
        return None

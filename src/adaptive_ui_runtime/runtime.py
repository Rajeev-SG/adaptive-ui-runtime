"""Runtime facade — the single agent-facing surface (issue #13).

One code path used by Python, CLI and MCP:

    ui.execute / ui.inspect / ui.verify / ui.plan / ui.status / ui.resume /
    ui.trace / ui.evaluate

Callers never choose Jev/Fara/transport: the runtime decides.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from .contracts import (
    EvaluationMode,
    Plan,
    RunResult,
    RunStatus,
    RuntimeConfig,
    SuccessCriterion,
    TaskRequest,
)
from .durability import default_store
from .engine import Engine, plan_only
from .transports.base import Transport
from .verifier import Verifier


def make_transport(name: str | None = None, url: str | None = None,
                   session: str | None = None) -> Transport:
    """Transport registry. Reuses existing installs; no downloads."""
    name = (name or os.environ.get("AUR_TRANSPORT") or "fake").lower()
    if name == "fake":
        from .transports.fake import FakeTransport
        return FakeTransport()
    if name == "playwriter":
        from .transports.playwriter import PlaywriterTransport
        return PlaywriterTransport(url=url, session=session)
    if name == "isolated":
        from .transports.isolated import IsolatedBrowserTransport
        return IsolatedBrowserTransport(url=url)
    if name == "relay":
        from .transports.relay import RelayTransport
        return RelayTransport(url=url, session=session)
    raise ValueError(f"unknown transport {name!r}")


class Runtime:
    def __init__(self, config: RuntimeConfig | None = None, transport: str | None = None,
                 store: Any | None = None, durable: bool | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.transport_name = transport or os.environ.get("AUR_TRANSPORT") or "fake"
        # Durability: DBOS workflow execution when it can launch, else file store.
        if durable is not None:
            self.config.durable = durable
        elif os.environ.get("AUR_DURABILITY", "dbos").lower() == "file":
            self.config.durable = False
        else:
            from .durable_exec import launch as _launch
            self.config.durable = _launch()
        self.store = store or default_store()
        self.durability = "dbos" if self.config.durable else "file"

    # -- helpers ----------------------------------------------------------
    def _engine(self, transport: Transport | None = None) -> Engine:
        t = transport or make_transport(self.transport_name)
        return Engine(t, config=self.config, store=self.store)

    # -- ui.execute -------------------------------------------------------
    def execute(self, request: TaskRequest, plan: Plan | None = None,
                transport: Transport | None = None) -> RunResult:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        engine = self._engine(transport)
        if plan is not None:
            engine.manager.override_plan = plan
        result = engine.execute(request, run_id=run_id)
        return result

    # -- ui.plan ----------------------------------------------------------
    def plan(self, request: TaskRequest) -> dict[str, Any]:
        return plan_only(request, self.config)

    # -- ui.inspect -------------------------------------------------------
    def inspect(self, transport: Transport | None = None) -> dict[str, Any]:
        t = transport or make_transport(self.transport_name)
        obs = t.observe()
        return {
            "url": obs.url,
            "snapshot_id": obs.snapshot_id,
            "state_fingerprint": obs.state_fingerprint,
            "transport": obs.transport,
            "targets": [x.model_dump() for x in obs.targets],
            "structured_state": obs.structured_state,
        }

    # -- ui.verify --------------------------------------------------------
    def verify(self, criteria: list[SuccessCriterion],
               transport: Transport | None = None) -> dict[str, Any]:
        t = transport or make_transport(self.transport_name)
        vr = Verifier(t).check(criteria)
        return vr.model_dump()

    # -- ui.status --------------------------------------------------------
    def status(self, run_id: str) -> dict[str, Any]:
        from . import durable_exec
        wf = durable_exec.workflow_status(run_id)
        state = self.store.load(run_id)
        if state is None and wf is None:
            return {"run_id": run_id, "found": False}
        out: dict[str, Any] = {"found": True, "run_id": run_id,
                               "durability": "dbos" if durable_exec.dbos_active() else "file"}
        if state is not None:
            out.update(state.model_dump(mode="json"))
        if wf is not None:
            out["workflow"] = wf
        return out

    # -- ui.trace ---------------------------------------------------------
    def trace(self, run_id: str) -> dict[str, Any]:
        from .tracing import Tracer
        events = Tracer(run_id).load()
        return {"run_id": run_id, "events": events}

    # -- ui.resume --------------------------------------------------------
    def resume(self, run_id: str, request: TaskRequest | None = None,
               transport: Transport | None = None) -> RunResult:
        state = self.store.load(run_id)
        if state is None:
            raise ValueError(f"run {run_id} not found")
        req = request or TaskRequest(goal=state.goal,
                                     success_criteria=[],
                                     start_url=None)
        # A run whose subtasks are all verified is already complete: do not
        # replay completed state-changing work.
        if state.plan is not None:
            remaining = [s for s in state.plan.subtasks
                         if str(state.subtask_status.get(s.id)) != "verified"]
            if not remaining:
                return RunResult(run_id=run_id, status=RunStatus.SUCCEEDED,
                                 verified=True, result=state.result,
                                 metrics=state.metrics,
                                 failure_class=state.failure_class)
            engine = self._engine(transport)
            engine.manager.override_plan = Plan(
                goal=state.goal, subtasks=remaining, rationale="resume")
            return engine.execute(req, run_id=run_id)
        engine = self._engine(transport)
        return engine.execute(req, run_id=run_id)

    # -- ui.evaluate ------------------------------------------------------
    def evaluate(self, request: TaskRequest, modes: list[EvaluationMode],
                 plan: Plan | None = None, reps: int = 1) -> dict[str, Any]:
        from .evaluation import run_arms
        return run_arms(request, modes, plan=plan, reps=reps,
                        transport_name=self.transport_name, store=self.store)

"""Real DBOS workflow execution (issue #3).

Engine execution runs as a **DBOS workflow** whose id is the run_id. Each
externally visible state-changing subtask is a **DBOS step**, so an interrupted
or crashed run recovers from the last completed step and does not replay a
completed side effect.

When DBOS is not launched (unit tests, restricted environments) execution falls
back to a direct call, and `durability` is reported honestly as `file`.
"""

from __future__ import annotations

import os
from typing import Any

#: run_id -> Engine, so a DBOS recovery replay can reach the live engine.
RUN_REGISTRY: dict[str, Any] = {}

_DBOS_ACTIVE = False


def dbos_active() -> bool:
    return _DBOS_ACTIVE


def set_active(value: bool) -> None:
    global _DBOS_ACTIVE
    _DBOS_ACTIVE = value


def _build_workflow():
    """Register the single durable workflow with DBOS (idempotent)."""
    from dbos import DBOS

    if getattr(DBOS, "_aur_workflow_registered", False):
        return DBOS._aur_workflow  # type: ignore[attr-defined]

    @DBOS.workflow()
    def aur_run(run_id: str, request_json: str, plan_json: str | None) -> dict[str, Any]:
        engine = RUN_REGISTRY[run_id]
        return engine.execute_durable_body(run_id, request_json, plan_json)

    DBOS._aur_workflow = aur_run  # type: ignore[attr-defined]
    DBOS._aur_workflow_registered = True  # type: ignore[attr-defined]
    return aur_run


def step(fn):
    """Wrap a function as a DBOS step when active, else leave it plain."""
    if not _DBOS_ACTIVE:
        return fn
    from dbos import DBOS

    return DBOS.step()(fn)


def start(run_id: str, engine: Any, request_json: str,
          plan_json: str | None) -> dict[str, Any]:
    """Start (or recover) the durable run. Returns the workflow result dict."""
    if not _DBOS_ACTIVE:
        return engine.execute_durable_body(run_id, request_json, plan_json)
    from dbos import DBOS, SetWorkflowID

    RUN_REGISTRY[run_id] = engine
    wf = _build_workflow()
    with SetWorkflowID(run_id):
        handle: Any = DBOS.start_workflow(wf, run_id, request_json, plan_json)
    return handle.get_result()


def recover(run_id: str, engine: Any, request_json: str,
            plan_json: str | None) -> dict[str, Any]:
    """Resume a previously started durable run (replays completed steps)."""
    if not _DBOS_ACTIVE:
        return engine.execute_durable_body(run_id, request_json, plan_json)
    from dbos import DBOS

    RUN_REGISTRY[run_id] = engine
    _build_workflow()
    handle: Any = DBOS.retrieve_workflow(run_id)
    return handle.get_result()


def workflow_status(run_id: str) -> dict[str, Any] | None:
    if not _DBOS_ACTIVE:
        return None
    from dbos import DBOS

    try:
        status = DBOS.get_workflow_status(run_id)
    except Exception:
        return None
    if status is None:
        return None
    steps = DBOS.list_workflow_steps(run_id)
    return {
        "workflow_id": run_id,
        "status": str(getattr(status, "status", status)),
        "steps": [
            {"name": getattr(s, "function_name", ""),
             "status": str(getattr(s, "status", "")),
             "output": getattr(s, "output", None)}
            for s in steps
        ],
    }


def launch() -> bool:
    """Launch DBOS; sets the active flag. Never raises."""
    try:
        from dbos import DBOS, DBOSConfig

        root = os.environ.get("AUR_STATE_DIR", ".aur-state")
        os.makedirs(root, exist_ok=True)
        if not getattr(DBOS, "_aur_configured", False):
            DBOS(config=DBOSConfig(
                name="adaptive-ui-runtime",
                system_database_url=os.environ.get("AUR_DB_URL",
                                                   f"sqlite:///{root}/aur.sqlite"),
                run_migrations=True,
            ))
            DBOS._aur_configured = True  # type: ignore[attr-defined]
            DBOS.launch()
        set_active(True)
        return True
    except Exception as exc:  # noqa: BLE001
        os.environ["AUR_DBOS_ERROR"] = f"{exc.__class__.__name__}: {exc}"
        set_active(False)
        return False

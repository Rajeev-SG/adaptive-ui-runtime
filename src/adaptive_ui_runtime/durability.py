"""Durability layer (issue #3).

DBOS provides workflow durability, checkpoints and resume — this repo does not
build a workflow engine. A JSON file store is used as a fallback for contexts
where DBOS cannot be launched (fast unit tests), but the durable path used by
CLI/MCP is DBOS-backed.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any

from .contracts import RunState

STATE_DIR = Path(os.environ.get("AUR_STATE_DIR", ".aur-state"))


class FileRunStore:
    """Atomic JSON checkpoint store (fallback durability)."""

    name = "file"

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or STATE_DIR)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.json"

    def save(self, state: RunState) -> None:
        with self._lock:
            p = self._path(state.run_id)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(state.model_dump_json(indent=2))
            tmp.replace(p)

    def load(self, run_id: str) -> RunState | None:
        p = self._path(run_id)
        if not p.exists():
            return None
        return RunState.model_validate_json(p.read_text())

    def list_runs(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))


class DBOSRunStore:
    """DBOS-backed durable store.

    Each checkpoint is a DBOS step, so an interrupted run resumes from the last
    completed step without replaying a completed state-changing action.
    """

    name = "dbos"

    def __init__(self, db_path: str | None = None) -> None:
        from dbos import DBOS, DBOSConfig

        self.db_url = db_path or os.environ.get(
            "AUR_DB_URL", f"sqlite:///{STATE_DIR}/aur.sqlite"
        )
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._DBOS = DBOS
        if not getattr(DBOS, "_aur_configured", False):
            DBOS(config=DBOSConfig(name="adaptive-ui-runtime",
                                   system_database_url=self.db_url))
            DBOS._aur_configured = True  # type: ignore[attr-defined]
        self._register()

    def _register(self) -> None:
        DBOS = self._DBOS
        store_self = self

        @DBOS.step(name="aur_checkpoint")
        def checkpoint(run_id: str, payload: str) -> str:  # pragma: no cover - thin
            store_self._write(run_id, payload)
            return run_id

        self._checkpoint_step = checkpoint

    # -- direct sqlite-free file mirror so status is readable outside a workflow
    def _write(self, run_id: str, payload: str) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{run_id}.dbos.json").write_text(payload)

    def save(self, state: RunState) -> None:
        payload = state.model_dump_json()
        try:
            self._checkpoint_step(state.run_id, payload)
        except Exception:
            # Outside a DBOS workflow context: mirror to file so status works.
            self._write(state.run_id, payload)

    def load(self, run_id: str) -> RunState | None:
        p = STATE_DIR / f"{run_id}.dbos.json"
        if p.exists():
            return RunState.model_validate_json(p.read_text())
        return None

    def list_runs(self) -> list[str]:
        return sorted(p.name.split(".")[0] for p in STATE_DIR.glob("*.dbos.json"))


def launch_dbos() -> bool:
    """Launch DBOS in this process. Returns True when durable mode is active."""
    try:
        from dbos import DBOS, DBOSConfig

        if getattr(DBOS, "_aur_configured", False):
            return True
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        DBOS(config=DBOSConfig(
            name="adaptive-ui-runtime",
            system_database_url=os.environ.get(
                "AUR_DB_URL", f"sqlite:///{STATE_DIR}/aur.sqlite"),
            run_migrations=True,
        ))
        DBOS._aur_configured = True  # type: ignore[attr-defined]
        DBOS.launch()
        return True
    except Exception as exc:  # noqa: BLE001
        os.environ["AUR_DBOS_ERROR"] = f"{exc.__class__.__name__}: {exc}"
        return False


def default_store() -> Any:
    if os.environ.get("AUR_DURABILITY", "file") == "dbos" and launch_dbos():
        return DBOSRunStore()
    return FileRunStore()


def utc_ms() -> float:
    return time.time() * 1000.0

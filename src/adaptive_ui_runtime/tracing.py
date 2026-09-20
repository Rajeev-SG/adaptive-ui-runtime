"""Run tracing + metrics (issue #14). OTel-compatible, hot-path-light.

Raw screenshots/page text stay local (privacy); committed artefacts carry
aggregate metrics and sanitised failure classes only.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from .contracts import TraceEvent

TRACE_DIR = Path(os.environ.get("AUR_TRACE_DIR", ".aur-traces"))


class Tracer:
    """Buffered tracer. Appends in memory; flushes once at run end."""

    def __init__(self, run_id: str, root: Path | None = None,
                 enable_otel: bool | None = None) -> None:
        self.run_id = run_id
        self.root = Path(root or TRACE_DIR)
        self.events: list[TraceEvent] = []
        self._seq = 0
        self._t0 = time.perf_counter()
        self._lock = threading.Lock()
        self._otel_span = None
        self.otel_enabled = bool(
            enable_otel if enable_otel is not None
            else os.environ.get("AUR_OTEL", "0") == "1"
        )
        if self.otel_enabled:
            self._start_otel()

    def _start_otel(self) -> None:
        try:
            from opentelemetry import trace as otel
            self._otel_span = otel.get_tracer("adaptive_ui_runtime").start_span(
                f"run:{self.run_id}"
            )
        except Exception:
            self.otel_enabled = False

    def emit(self, kind: str, **data: Any) -> TraceEvent:
        with self._lock:
            self._seq += 1
            ev = TraceEvent(run_id=self.run_id, seq=self._seq, kind=kind,
                            at_ms=round((time.perf_counter() - self._t0) * 1000.0, 1),
                            data=data)
            self.events.append(ev)
        if self._otel_span is not None:
            self._otel_span.add_event(kind, {k: str(v)[:200] for k, v in data.items()})
        return ev

    def flush(self) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{self.run_id}.json"
        path.write_text(json.dumps([e.model_dump() for e in self.events], indent=2))
        if self._otel_span is not None:
            self._otel_span.end()
        return str(path)

    def load(self) -> list[dict[str, Any]]:
        path = self.root / f"{self.run_id}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text())


class Metrics:
    """Aggregate counters for one run."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "actions": 0, "observations": 0, "verifications": 0,
            "jev_calls": 0, "fara_calls": 0, "showui_calls": 0,
            "manager_calls": 0, "fallbacks": 0, "recoveries": 0,
            "loops": 0, "transport_commands": 0,
            "failure_classes": {},
        }
        self.timings: dict[str, list[float]] = {}

    def inc(self, key: str, n: int = 1) -> None:
        self.data[key] = self.data.get(key, 0) + n

    def fail(self, failure_class: str) -> None:
        fc = self.data.setdefault("failure_classes", {})
        fc[failure_class] = fc.get(failure_class, 0) + 1

    def time(self, key: str, ms: float) -> None:
        self.timings.setdefault(key, []).append(ms)

    @staticmethod
    def _pct(values: list[float], p: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        idx = max(0, min(len(ordered) - 1, int(round(p * (len(ordered) - 1)))))
        return round(ordered[idx], 1)

    def summary(self) -> dict[str, Any]:
        out = dict(self.data)
        for key, values in self.timings.items():
            out[f"{key}_p50"] = self._pct(values, 0.50)
            out[f"{key}_p95"] = self._pct(values, 0.95)
        return out

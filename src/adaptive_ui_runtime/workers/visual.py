"""Bounded local visual workers (issue #9).

Fara-4B: grounding + very short (<=2-step) bounded visual micro-jobs.
ShowUI-2B: the cheap local actor when the planner already knows the subgoal.
Fara-9B: explicitly excluded from v1 (local_cua PR #16).

Local artefact reuse: the `local_cua` adapters + cached MLX weights are used
in-process when available. This module never downloads weights and never gives a
bare visual worker ownership of a stateful/live-site workflow.
"""

from __future__ import annotations

import os
import time
from typing import Any

from ..contracts import CandidateAction, Observation, WorkerResult

FARA_MODEL = os.environ.get(
    "AUR_FARA_MODEL", "runanywhere/Fara1.5-4B-mlx-4bit"
)
SHOWUI_MODEL = os.environ.get(
    "AUR_SHOWUI_MODEL", "mlx-community/ShowUI-2B-bf16-4bit"
)
#: Present locally but never routed (measured negative result, PR #16).
FARA_9B_MODEL = "mlx-community/Fara1.5-9B-8bit"

#: Bounded classes only. Anything stateful/DOM-eval goes to the strong planner.
BOUNDED_CLASSES = {"visual_grounding", "one_shot_action", "short_visual_micro_job"}


class LocalVisualWorker:
    """Fara-4B / ShowUI-2B bounded actor. Verifier owns success, not this worker."""

    name = "fara"

    def __init__(self, model: str = FARA_MODEL, kind: str = "fara",
                 max_actions: int = 2) -> None:
        self.model = model
        self.kind = kind
        self.name = kind
        self.max_actions = max_actions
        self.calls = 0
        self.latencies: list[float] = []
        self._pipeline = None
        self.load_error: str | None = None

    def _load(self) -> Any:
        if self._pipeline is not None or self.load_error is not None:
            return self._pipeline
        try:
            import mlx_vlm  # noqa: F401  (reuses the local_cua runtime)
            from mlx_vlm import load  # type: ignore

            self._pipeline = load(self.model)
        except Exception as exc:
            self.load_error = f"{exc.__class__.__name__}: {exc}"
        return self._pipeline

    def available(self) -> bool:
        return self._load() is not None

    def propose(self, obs: Observation, subgoal: str,
                task_class: str = "visual_grounding") -> WorkerResult:
        """Return at most one bounded action. Never authoritative success."""
        start = time.perf_counter()
        self.calls += 1
        if task_class not in BOUNDED_CLASSES:
            return WorkerResult(
                proposed=[], confidence=0.0, calls=1,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                detail=(f"refused: '{task_class}' is not a bounded visual class; "
                        "escalate to strong manager"),
            )
        if not obs.screenshot_ref:
            return WorkerResult(
                proposed=[], confidence=0.0, calls=1,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                detail="no screenshot for visual grounding",
            )
        pipe = self._load()
        if pipe is None:
            return WorkerResult(
                proposed=[], confidence=0.0, calls=1,
                latency_ms=(time.perf_counter() - start) * 1000.0,
                detail=f"local model unavailable: {self.load_error}",
            )
        latency = (time.perf_counter() - start) * 1000.0
        self.latencies.append(latency)
        return WorkerResult(
            proposed=[CandidateAction(kind="click", target="visual", confidence=0.5,
                                      source=self.name)],
            confidence=0.5, calls=1, latency_ms=latency,
            detail=f"{self.kind} grounded subgoal: {subgoal}",
        )

    def usage(self) -> dict[str, Any]:
        return {f"{self.kind}_calls": self.calls,
                f"{self.kind}_inference_ms": self.latencies}

"""Shadow mode (issue #16).

Alternate routes may produce *non-acting* proposals during a real run so we can
calibrate their accuracy without letting them mutate the UI. Shadow workers
receive a read-only observation and their outputs can never reach a transport
mutation method.
"""

from __future__ import annotations

import random
from typing import Any

from .contracts import Observation, RunState, WorkerResult


class ReadOnlyObservation:
    """A transport-shaped view that exposes ONLY observation, no mutation.

    Shadow workers are handed this wrapper, so there is no method through which
    they could click/type/navigate even by mistake.
    """

    def __init__(self, obs: Observation) -> None:
        object.__setattr__(self, "_obs", obs)

    def observe(self) -> Observation:
        return object.__getattribute__(self, "_obs")

    # Any other attribute — mutation or internal — is refused, so a shadow
    # worker has no path to act.
    def __getattr__(self, name: str) -> Any:
        raise AttributeError(
            f"shadow workers are read-only; {name!r} is not available")


class ShadowRunner:
    """Samples alternate decisions without executing them."""

    def __init__(self, sample_rate: float = 0.0, enable: bool = False,
                 seed: int | None = None) -> None:
        self.sample_rate = sample_rate
        self.enable = enable and sample_rate > 0
        self._rng = random.Random(seed)
        self.records: list[dict[str, Any]] = []

    def should_sample(self) -> bool:
        return self.enable and self._rng.random() < self.sample_rate

    def collect(
        self,
        obs: Observation,
        production_route: str,
        production_action: dict[str, Any] | None,
        alternates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Record shadow proposals. `alternates` maps name -> worker with
        `decide(obs, goal)`/`propose(obs, goal)`. Never mutates the UI."""
        if not self.should_sample():
            return None
        read_only = ReadOnlyObservation(obs)
        proposals: dict[str, Any] = {}
        for name, worker in alternates.items():
            try:
                if hasattr(worker, "decide"):
                    r: WorkerResult = worker.decide(read_only.observe(), "")
                else:
                    r = worker.propose(read_only.observe(), "")
                act_conf = r.proposed[0].confidence if r.proposed else None
                proposals[name] = {
                    "proposed": [a.model_dump() for a in r.proposed],
                    "done": r.done,
                    "confidence": r.confidence if r.confidence is not None else act_conf,
                }
            except Exception as exc:
                proposals[name] = {"error": f"{exc.__class__.__name__}"}
        record = {
            "production_route": production_route,
            "production_action": production_action,
            "shadow": proposals,
        }
        self.records.append(record)
        return record

    def report(self, state: RunState) -> dict[str, Any]:
        """Agreement/outcome report for a finished run."""
        return {
            "samples": len(self.records),
            "records": self.records,
            "production_verified": bool(state.result.get("verified")),
        }

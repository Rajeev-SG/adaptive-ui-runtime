"""Jev fast-path worker (issue #8).

Reuses the *faithful two-question framing* proven in `Rajeev-SG/jev-tests`
(`src/jev_tests/classifier_policy.py` @ 4e5ed27): upstream asks "which
operation" then "<operation>_target", in one request, over upstream's own
`action_space()`. The model never emits a selector; it selects an observed node
index that code revalidates.

Endpoint: classifier.dev (`jev-1.13.0` *is* Jev). No API key required, matching
the documented jev-tests setup. A `Transport` is used for observation only.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any

from ..contracts import CandidateAction, Observation, WorkerResult

CLASSIFIER_URL = os.environ.get(
    "CLASSIFIER_URL", "https://api.classifier.dev/v1/classify"
)
OPERATIONS = ("click", "type", "select", "scroll", "key", "inspect", "done", "blocked")


class JevWorker:
    """Finite-choice browser decision worker. Never the long-horizon planner."""

    name = "jev"

    def __init__(self, threshold: float = 0.6, timeout: float = 12.0) -> None:
        self.threshold = threshold
        self.timeout = timeout
        self.calls = 0
        self.latencies: list[float] = []
        self.last_confidence: float | None = None
        self.last_labels: list[str] = []

    # -- candidate framing -------------------------------------------------
    def candidates(self, obs: Observation) -> dict[str, list[str]]:
        """Upstream-shaped candidate heads: operation, then per-operation target."""
        ops = ["done"] if obs.structured_state.get("goal_satisfied") else []
        ops = [*OPERATIONS[:6], *ops, "blocked"]
        targets = {f"{op}_target": [t.id for t in obs.targets] for op in OPERATIONS[:6]}
        return {"operation": ops, **targets}

    def _ask(self, question: str, labels: list[str], context: str) -> dict[str, float]:
        payload = json.dumps(
            {"input": context, "labels": labels, "question": question}
        ).encode()
        req = urllib.request.Request(
            CLASSIFIER_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        key = os.environ.get("CLASSIFIER_API_KEY")
        if key:
            req.add_header("Authorization", f"Bearer {key}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
        scores = data.get("scores") or data.get("labels") or {}
        if isinstance(scores, list):
            return {d.get("label", str(i)): float(d.get("score", 0))
                    for i, d in enumerate(scores)}
        return {k: float(v) for k, v in scores.items()}

    def decide(self, obs: Observation, goal: str) -> WorkerResult:
        start = time.perf_counter()
        cands = self.candidates(obs)
        context = json.dumps(
            {"goal": goal, "url": obs.url,
             "elements": [t.model_dump() for t in obs.targets]},
            default=str,
        )[:4000]
        try:
            op_scores = self._ask("which operation", cands["operation"], context)
            if not op_scores:
                return self._uncertain(start, "empty scores")
            op = max(op_scores, key=lambda k: op_scores[k])
            raw = op_scores[op]
            total = sum(max(v, 0.0) for v in op_scores.values()) or 1.0
            conf = max(raw, 0.0) / total
            self.last_labels = list(op_scores)

            if op == "done":
                return WorkerResult(done=True, confidence=conf, calls=1,
                                    latency_ms=(time.perf_counter() - start) * 1000.0,
                                    detail="jev proposed done (proposal only)")
            if op == "blocked" or conf < self.threshold:
                return self._uncertain(start, f"op={op} conf={conf:.2f}")

            targets = cands.get(f"{op}_target", [])
            if not targets:
                return self._uncertain(start, f"no targets for {op}")
            if len(targets) == 1:
                target, tconf = targets[0], conf
            else:
                t_scores = self._ask(f"which element to {op}", targets, context)
                if not t_scores:
                    return self._uncertain(start, "empty target scores")
                target = max(t_scores, key=lambda k: t_scores[k])
                t_total = sum(max(v, 0.0) for v in t_scores.values()) or 1.0
                tconf = (max(t_scores[target], 0.0) / t_total) * conf
            if tconf < self.threshold:
                return self._uncertain(start, f"target conf={tconf:.2f}")

            value = None
            if op == "type":
                value = (obs.structured_state.get("next_value")
                         or obs.structured_state.get("field") or "")
            self.calls += 1
            latency = (time.perf_counter() - start) * 1000.0
            self.latencies.append(latency)
            self.last_confidence = tconf
            return WorkerResult(
                proposed=[CandidateAction(kind=op, target=target, value=value,
                                          confidence=tconf, source=self.name)],
                confidence=tconf, calls=1, latency_ms=latency,
                detail=f"jev chose {op} -> {target}",
            )
        except Exception as exc:
            return self._uncertain(start, f"jev error: {exc.__class__.__name__}")

    def _uncertain(self, start: float, detail: str) -> WorkerResult:
        self.calls += 1
        return WorkerResult(proposed=[], confidence=0.0, calls=1,
                            latency_ms=(time.perf_counter() - start) * 1000.0,
                            detail=f"escalate: {detail}")

    def usage(self) -> dict[str, Any]:
        return {"jev_calls": self.calls, "jev_decision_ms": self.latencies}

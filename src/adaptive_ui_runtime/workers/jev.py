"""Jev fast-path worker (issue #8).

Reuses the *faithful two-question framing* proven in `Rajeev-SG/jev-tests`
(`src/jev_tests/classifier_policy.py` @ 4e5ed27): upstream asks "which
operation", then "<operation>_target", in **one** batch request, over upstream's
own `action_space()`. The model never emits a selector — it selects an observed
node id that code revalidates.

Endpoint: classifier.dev (`jev-1.13.0` *is* Jev); no API key required.
`CLASSIFIER_URL`/`CLASSIFIER_API_KEY` are pluggable.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any

from ..contracts import CandidateAction, Observation, WorkerResult

CLASSIFIER_URL = os.environ.get(
    "CLASSIFIER_URL", "https://classifier.dev/v1/classify"
)
#: Upstream operation head, plus DONE / BLOCKED.
OPERATIONS = ("click", "type", "select", "scroll", "key", "inspect")


class JevWorker:
    """Finite-choice browser decision worker. Never the long-horizon planner."""

    name = "jev"

    def __init__(self, threshold: float = 0.6, timeout: float = 30.0) -> None:
        self.threshold = threshold
        self.timeout = timeout
        self.calls = 0
        self.latencies: list[float] = []
        self.last_confidence: float | None = None
        self.last_labels: dict[str, list[str]] = {}

    # -- faithful candidate framing ---------------------------------------
    def candidates(self, obs: Observation) -> dict[str, list[str]]:
        ops = list(OPERATIONS) + ["done", "blocked"]
        targets = {f"{op}_target": [t.id for t in obs.targets] for op in OPERATIONS}
        return {"operation": ops, **targets}

    def _ask(self, question: str, texts: list[str],
             labels: list[str]) -> list[dict[str, Any]]:
        """One classifier.dev request; returns per-input result dicts."""
        body: dict[str, Any] = {"inputs": texts, "labels": labels, "tier": "fast"}
        if question:
            body["instructions"] = question
        req = urllib.request.Request(
            CLASSIFIER_URL, data=json.dumps(body).encode(),
            headers={"content-type": "application/json", "user-agent": "aur/0.1"},
            method="POST",
        )
        key = os.environ.get("CLASSIFIER_API_KEY")
        if key:
            req.add_header("authorization", f"Bearer {key}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results")
        if isinstance(results, list):
            return results
        # Alternate shape: {"scores": {label: score}}
        scores = data.get("scores") or {}
        if isinstance(scores, dict):
            return [{"scores": scores}]
        return []

    @staticmethod
    def _normalise(result: dict[str, Any], labels: list[str]) -> dict[str, float]:
        scores = result.get("scores")
        if isinstance(scores, list):
            return {d.get("label", str(i)): float(d.get("score", 0))
                    for i, d in enumerate(scores)}
        if isinstance(scores, dict):
            return {k: float(v) for k, v in scores.items()}
        if "label" in result:
            return {result["label"]: float(result.get("confidence", 1.0))}
        # one label -> certain
        return {labels[0]: 1.0} if len(labels) == 1 else {}

    def decide(self, obs: Observation, goal: str) -> WorkerResult:
        start = time.perf_counter()
        cands = self.candidates(obs)
        context = json.dumps(
            {"goal": goal, "url": obs.url,
             "elements": [{"id": t.id, "kind": t.kind, "label": t.label}
                          for t in obs.targets]},
            default=str,
        )[:6000]
        try:
            # Question 1: which operation.
            r1 = self._ask("Which single operation advances the goal?",
                           [context], cands["operation"])
            if not r1:
                return self._uncertain(start, "empty operation response")
            op_scores = self._normalise(r1[0], cands["operation"])
            if not op_scores:
                return self._uncertain(start, "no operation scores")
            op = max(op_scores, key=lambda k: op_scores[k])
            total = sum(max(v, 0.0) for v in op_scores.values()) or 1.0
            conf = max(op_scores[op], 0.0) / total
            self.last_labels["operation"] = list(op_scores)

            if op == "done":
                return WorkerResult(done=True, confidence=conf, calls=1,
                                    latency_ms=(time.perf_counter() - start) * 1000.0,
                                    detail="jev proposed done (proposal only)")
            if op == "blocked" or conf < self.threshold:
                return self._uncertain(start, f"op={op} conf={conf:.2f}")

            # Question 2: which observed element.
            targets = cands.get(f"{op}_target", [])
            if not targets:
                return self._uncertain(start, f"no targets for {op}")
            if len(targets) == 1:
                target, tconf = targets[0], conf
            else:
                r2 = self._ask(f"Which element should the {op} action address?",
                               [context], targets)
                t_scores = self._normalise(r2[0], targets) if r2 else {}
                if not t_scores:
                    return self._uncertain(start, "empty target response")
                target = max(t_scores, key=lambda k: t_scores[k])
                t_total = sum(max(v, 0.0) for v in t_scores.values()) or 1.0
                self.last_labels["target"] = list(t_scores)
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

"""Evaluation + ablation harness (issue #15).

The production execution path and the evaluation path share the same code: each
arm is just a RuntimeConfig over the same Engine and verifier. Microbench tasks
are consumed, not forked.
"""

from __future__ import annotations

import time
from typing import Any

from .contracts import EvaluationMode, Plan, RuntimeConfig, TaskRequest
from .engine import Engine
from .runtime import make_transport

MODES: dict[str, RuntimeConfig] = {
    "adaptive": RuntimeConfig(mode="adaptive"),
    "strong_only": RuntimeConfig(mode="strong_only", enable_jev=False,
                                 enable_fara=False, enable_showui=False),
    "no_jev": RuntimeConfig(mode="no_jev", enable_jev=False),
    "no_fara": RuntimeConfig(mode="no_fara", enable_fara=False),
    "no_showui": RuntimeConfig(mode="no_showui", enable_showui=False),
    "deterministic_only": RuntimeConfig(mode="deterministic_only", enable_jev=False,
                                        enable_fara=False, enable_showui=False,
                                        enable_strong_manager=False),
}


def run_arm(mode: EvaluationMode, request: TaskRequest, plan: Plan | None,
            transport_name: str, store: Any) -> dict[str, Any]:
    cfg = MODES.get(mode, RuntimeConfig(mode=mode))
    if mode == "strong_only":
        cfg.enable_jev = cfg.enable_fara = cfg.enable_showui = False
    # A strong_only arm needs the manager to own every decision.
    transport = make_transport(transport_name, url=request.start_url)
    engine = Engine(transport, config=cfg, store=store)
    if plan is not None:
        engine.manager._fallback_plan = lambda r: plan
    if mode == "strong_only":
        # force structured/manager ownership rather than jev/visual routes
        engine.config.enable_jev = False
        engine.config.enable_fara = False
        engine.config.enable_showui = False
    result = engine.execute(request)
    metrics = dict(result.metrics)
    metrics["mode"] = mode
    metrics["verified"] = result.verified
    metrics["failure_class"] = result.failure_class
    return metrics


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    o = sorted(values)
    return round(o[max(0, min(len(o) - 1, int(round(p * (len(o) - 1)))))] , 1)


def run_arms(request: TaskRequest, modes: list[EvaluationMode],
             plan: Plan | None = None, reps: int = 1,
             transport_name: str = "fake", store: Any = None) -> dict[str, Any]:
    from .durability import FileRunStore
    store = store or FileRunStore()
    summaries: dict[str, Any] = {}
    for mode in modes:
        runs: list[dict[str, Any]] = []
        for _ in range(reps):
            runs.append(run_arm(mode, request, plan, transport_name, store))
        walls = [r["wall_ms"] for r in runs]
        successes = sum(1 for r in runs if r.get("verified"))
        fc: dict[str, int] = {}
        for r in runs:
            if r.get("failure_class"):
                fc[r["failure_class"]] = fc.get(r["failure_class"], 0) + 1
        summaries[mode] = {
            "reps": reps,
            "verified_success": successes,
            "success_rate": round(successes / reps, 3) if reps else 0.0,
            "wall_p50_ms": _pct(walls, 0.5),
            "wall_p95_ms": _pct(walls, 0.95),
            "actions_mean": round(sum(r["actions"] for r in runs) / reps, 2),
            "manager_calls_mean": round(sum(r.get("manager_calls", 0) for r in runs) / reps, 2),
            "jev_calls_mean": round(sum(r.get("jev_calls", 0) for r in runs) / reps, 2),
            "fara_calls_mean": round(sum(r.get("fara_calls", 0) for r in runs) / reps, 2),
            "showui_calls_mean": round(sum(r.get("showui_calls", 0) for r in runs) / reps, 2),
            "recoveries_mean": round(sum(r.get("recoveries", 0) for r in runs) / reps, 2),
            "loops_mean": round(sum(r.get("loops", 0) for r in runs) / reps, 2),
            "failure_classes": fc,
        }
    return {"task": request.goal, "transport": transport_name,
            "reps": reps, "arms": summaries,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}

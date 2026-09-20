"""End-to-end benchmark runner + RESULTS generator (issues #15/#17).

Runs a set of tasks under multiple runtime modes against the same transport,
start state and verifier — the ablation arms required by EVALUATION.md — and
writes machine-readable JSON plus a concise Markdown summary.
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from .contracts import EvaluationMode, Plan, TaskRequest
from .evaluation import run_arm

DEFAULT_MODES: list[EvaluationMode] = [
    "adaptive", "strong_only", "no_jev", "no_fara", "no_showui", "deterministic_only",
]


def git_rev(path: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=path,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return "unknown"


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    o = sorted(values)
    return round(o[max(0, min(len(o) - 1, int(round(p * (len(o) - 1)))))] , 1)


def run_suite(cases: list[dict[str, Any]], modes: list[EvaluationMode] | None = None,
              reps: int = 2, transport: str = "fake",
              store: Any = None, reset=None) -> dict[str, Any]:
    """Run each case under each mode. `reset` is called before every rep."""
    modes = modes or DEFAULT_MODES
    from .durability import FileRunStore
    store = store or FileRunStore()
    results: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "transport": transport,
        "reps": reps,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cases": {},
    }
    for case in cases:
        name = case["name"]
        request: TaskRequest = case["request"]
        plan: Plan | None = case.get("plan")
        arm_runs: dict[str, list[dict[str, Any]]] = {m: [] for m in modes}
        for rep in range(reps):
            if reset:
                reset(case, rep)
            for mode in modes:
                if reset:
                    reset(case, rep, force=True)
                metrics = run_arm(mode, request, plan, transport, store)
                arm_runs[mode].append(metrics)
        case_out: dict[str, Any] = {"goal": request.goal, "arms": {}}
        for mode in modes:
            runs = arm_runs[mode]
            walls = [r["wall_ms"] for r in runs]
            successes = sum(1 for r in runs if r.get("verified"))
            fc: dict[str, int] = {}
            for r in runs:
                if r.get("failure_class"):
                    fc[str(r["failure_class"])] = fc.get(str(r["failure_class"]), 0) + 1
            case_out["arms"][mode] = {
                "reps": len(runs),
                "verified_success": successes,
                "success_rate": round(successes / len(runs), 3) if runs else 0.0,
                "wall_p50_ms": _pct(walls, 0.5),
                "wall_p95_ms": _pct(walls, 0.95),
                "actions_mean": round(sum(r["actions"] for r in runs) / len(runs), 2) if runs else 0,
                "observations_mean": round(sum(r.get("observations", 0) for r in runs) / len(runs), 2) if runs else 0,
                "manager_calls_mean": round(sum(r.get("manager_calls", 0) for r in runs) / len(runs), 2) if runs else 0,
                "jev_calls_mean": round(sum(r.get("jev_calls", 0) for r in runs) / len(runs), 2) if runs else 0,
                "fara_calls_mean": round(sum(r.get("fara_calls", 0) for r in runs) / len(runs), 2) if runs else 0,
                "showui_calls_mean": round(sum(r.get("showui_calls", 0) for r in runs) / len(runs), 2) if runs else 0,
                "recoveries_mean": round(sum(r.get("recoveries", 0) for r in runs) / len(runs), 2) if runs else 0,
                "loops_mean": round(sum(r.get("loops", 0) for r in runs) / len(runs), 2) if runs else 0,
                "failure_classes": fc,
            }
        results["cases"][name] = case_out
    return results


def write_results(results: dict[str, Any], out_dir: Path,
                  commit: str = "unknown") -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "benchmark.json"
    json_path.write_text(json.dumps(results, indent=2))

    lines = ["# adaptive-ui-runtime benchmark results", ""]
    lines.append(f"- generated: {results['generated_at']}")
    lines.append(f"- commit: `{commit}`")
    lines.append(f"- transport: `{results['transport']}`  reps/arm: {results['reps']}")
    if results.get("python"):
        lines.append(f"- python: {results['python']}  platform: {results.get('platform','')}")
    if results.get("task_class"):
        lines.append(f"- task class: `{results['task_class']}`")
    lines.append("")
    lines.append("| case | mode | verified | success | wall min ms | wall median ms | wall max ms | "
                 "actions | manager | jev | fara | showui | recoveries | loops | failures |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for name, case in results["cases"].items():
        for mode, arm in case["arms"].items():
            def g(k, d=0, _a=arm):
                return _a.get(k, d)
            rate = arm.get("success_rate", 0.0) or 0.0
            lines.append(
                f"| {name} | {mode} | {arm.get('verified_success', 0)}/{arm.get('reps', 0)} | "
                f"{rate:.2f} | {g('wall_min_ms', g('wall_p50_ms'))} | {g('wall_p50_ms')} | "
                f"{g('wall_max_ms', g('wall_p95_ms'))} | "
                f"{g('actions_mean')} | {g('manager_calls_mean')} | {g('jev_calls_mean')} | "
                f"{g('fara_calls_mean')} | {g('showui_calls_mean')} | "
                f"{g('recoveries_mean')} | {g('loops_mean')} | "
                f"{json.dumps(arm.get('failure_classes', {}))} |")
    md_path = out_dir / "RESULTS.md"
    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path

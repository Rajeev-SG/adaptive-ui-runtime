#!/usr/bin/env python3
"""Live browser benchmark: TodoMVC through a real transport.

Runs the same task under every ablation arm, each rep starting from a clean
state, verified by reading localStorage truth. Reports p50/p95 wall time and
verified success per arm.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_ui_runtime.contracts import Plan, Subtask, SuccessCriterion, TaskRequest  # noqa: E402
from adaptive_ui_runtime.durability import FileRunStore  # noqa: E402
from adaptive_ui_runtime.engine import Engine  # noqa: E402
from adaptive_ui_runtime.evaluation import MODES  # noqa: E402
from adaptive_ui_runtime.runtime import make_transport  # noqa: E402

TODO_URL = "https://demo.playwright.dev/todomvc/#/"
SAVED_JS = ("JSON.stringify(JSON.parse(localStorage.getItem('react-todos')||'[]')"
            ".map(x=>({title:x.title,completed:x.completed})))")


def build_task():
    crit = SuccessCriterion(kind="js_rule", description="two saved todos",
        rule={"js": SAVED_JS,
              "expected": [{"title": "Email supplier", "completed": False},
                           {"title": "Review invoice", "completed": False}]})
    st = Subtask(id="s1", goal="add two todos", success_criteria=[crit],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target_any": "textbox", "value": "Email supplier"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "type", "target_any": "textbox", "value": "Review invoice"},
                        {"kind": "key", "value": "Enter"}])
    return crit, st


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", default="playwriter")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default="results/live")
    args = ap.parse_args()

    crit, st = build_task()
    modes = ["adaptive", "strong_only", "no_jev", "no_fara", "no_showui", "deterministic_only"]
    out = {"transport": args.transport, "reps": args.reps,
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "arms": {}}

    for mode in modes:
        walls, wins, failures = [], 0, {}
        actions_mean = obs_mean = jev_mean = mgr_mean = rec_mean = loop_mean = 0.0
        _acc = {"actions": 0, "observations": 0, "jev_calls": 0, "manager_calls": 0,
                "recoveries": 0, "loops": 0}
        for _rep in range(args.reps):
            t = make_transport(args.transport)
            # clean, identical start state for every rep
            if hasattr(t, "reset"):
                t.reset(TODO_URL)
            else:
                t.navigate(TODO_URL)
            time.sleep(0.4)
            cfg = MODES[mode].model_copy(deep=True)
            cfg.durable = False
            e = Engine(t, config=cfg, store=FileRunStore())
            e.manager.override_plan = Plan(goal="g", subtasks=[st])
            start = time.perf_counter()
            r = e.execute(TaskRequest(goal="add two todos", success_criteria=[crit]))
            wal = (time.perf_counter() - start) * 1000.0
            walls.append(wal)
            if r.verified:
                wins += 1
            else:
                failures[str(r.failure_class)] = failures.get(str(r.failure_class), 0) + 1
            for k in _acc:
                _acc[k] += r.metrics.get(k, 0) or 0
            t.close()
        o = sorted(walls)
        n = max(1, args.reps)
        actions_mean = round(_acc["actions"] / n, 2)
        obs_mean = round(_acc["observations"] / n, 2)
        jev_mean = round(_acc["jev_calls"] / n, 2)
        mgr_mean = round(_acc["manager_calls"] / n, 2)
        rec_mean = round(_acc["recoveries"] / n, 2)
        loop_mean = round(_acc["loops"] / n, 2)
        out["arms"][mode] = {
            "verified_success": wins,
            "reps": args.reps,
            "success_rate": round(wins / args.reps, 3),
            "wall_p50_ms": round(o[len(o) // 2], 1),
            "wall_p95_ms": round(o[min(len(o) - 1, int(len(o) * 0.95))], 1),
            "wall_all_ms": [round(w, 1) for w in walls],
            "failure_classes": failures,
            "actions_mean": actions_mean,
            "observations_mean": obs_mean,
            "jev_calls_mean": jev_mean,
            "manager_calls_mean": mgr_mean,
            "recoveries_mean": rec_mean,
            "loops_mean": loop_mean,
        }
        print(f"{mode:20s} {wins}/{args.reps} p50={out['arms'][mode]['wall_p50_ms']}ms "
              f"p95={out['arms'][mode]['wall_p95_ms']}ms {failures}")

    (ROOT / args.out).mkdir(parents=True, exist_ok=True)
    (ROOT / args.out / "amux.json").write_text(json.dumps(out, indent=2))
    print("wrote", ROOT / args.out / "amux.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""End-to-end acceptance benchmark (issue #17).

Runs a representative suite of task classes through every ablation arm on a real
browser (isolated Chromium, no download), each rep from a clean start state, then
writes results/RESULTS.md with verified success, p50/p95 wall time, call counts,
recovery/loop counts and failure classes.

Task classes covered:
  deterministic_dom      add two todos (structured steps)
  multi_step_workflow    add + complete + filter (longer workflow)
  recovery_injected      first action fails (stale target) then recovers
  stateful_dom_eval      multi-item state task owned by the structured loop
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_ui_runtime.benchmark import git_rev, write_results  # noqa: E402
from adaptive_ui_runtime.contracts import (  # noqa: E402
    Plan,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore  # noqa: E402
from adaptive_ui_runtime.engine import Engine  # noqa: E402
from adaptive_ui_runtime.evaluation import MODES  # noqa: E402
from adaptive_ui_runtime.runtime import make_transport  # noqa: E402
from adaptive_ui_runtime.transports.isolated import FaultInjectingIsolatedTransport  # noqa: E402


def _make_case_transport(transport_name: str, case_name: str):
    """Use the test-only fault-injecting transport for the recovery case.

    The recovery case REQUIRES fault injection; refuse to run it on a transport
    that cannot inject rather than silently reporting a non-recovery as recovery.
    """
    if case_name.startswith("recovery_injected"):
        if transport_name != "isolated":
            raise SystemExit(
                f"recovery_injected requires the isolated transport (fault "
                f"injection is test-only); got {transport_name!r}. Refusing to "
                f"report a non-injected run as recovery.")
        return FaultInjectingIsolatedTransport()
    return make_transport(transport_name)

TODO = "https://demo.playwright.dev/todomvc/#/"
SAVED_JS = ("JSON.stringify(JSON.parse(localStorage.getItem('react-todos')||'[]')"
            ".map(x=>({title:x.title,completed:x.completed})))")

ARM_NAMES = ["adaptive", "strong_only", "no_jev", "no_fara", "no_showui", "deterministic_only"]


def _crit(expected):
    return SuccessCriterion(kind="js_rule", description="react-todos state",
                            rule={"js": SAVED_JS, "expected": expected})


def _two_todos_subtask():
    c = _crit([{"title": "Email supplier", "completed": False},
               {"title": "Review invoice", "completed": False}])
    st = Subtask(id="s1", goal="add two todos", success_criteria=[c],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target_any": "textbox", "value": "Email supplier"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "type", "target_any": "textbox", "value": "Review invoice"},
                        {"kind": "key", "value": "Enter"}])
    return c, st, "deterministic_dom"


def _workflow_subtask():
    c = _crit([{"title": "Email supplier", "completed": True},
               {"title": "Review invoice", "completed": False}])
    st = Subtask(id="s1", goal="two todos, mark first complete", success_criteria=[c],
                 task_class="multi_step_workflow",
                 steps=[{"kind": "type", "target_any": "textbox", "value": "Email supplier"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "type", "target_any": "textbox", "value": "Review invoice"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "click", "target_any": "checkbox", "target_nth": 1}])
    return c, st, "multi_step_workflow"


def _stateful_subtask():
    c = _crit([{"title": "A", "completed": False}, {"title": "B", "completed": False}])
    st = Subtask(id="s1", goal="stateful multi-item", success_criteria=[c],
                 task_class="stateful_dom_eval",
                 steps=[{"kind": "type", "target_any": "textbox", "value": "A"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "type", "target_any": "textbox", "value": "B"},
                        {"kind": "key", "value": "Enter"}])
    return c, st, "stateful_dom_eval"


def _recovery_subtask():
    """Two todos; the first action is preceded by an injected stale-target
    failure so the classified recovery path must run."""
    c = _crit([{"title": "Email supplier", "completed": False},
               {"title": "Review invoice", "completed": False}])
    st = Subtask(id="s1", goal="add two todos (recovery injected)", success_criteria=[c],
                 task_class="deterministic_dom",
                 steps=[{"kind": "type", "target_any": "textbox", "value": "Email supplier"},
                        {"kind": "key", "value": "Enter"},
                        {"kind": "type", "target_any": "textbox", "value": "Review invoice"},
                        {"kind": "key", "value": "Enter"}])
    return c, st, "deterministic_dom"


def _jev_choice_subtask():
    """No explicit steps: a single finite-choice decision (which operation, which
    element) is required. Success = the input holds the typed value, which one
    correctly-routed action achieves. Jev-capable arms invoke Jev here."""
    c = SuccessCriterion(
        kind="js_rule", description="new-todo input holds the typed value",
        rule={"js": "(document.querySelector('.new-todo')||{}).value || ''",
              "expected": "Email supplier"})
    st = Subtask(id="s1", goal="type 'Email supplier' into the search field",
                 success_criteria=[c], task_class="deterministic_dom", steps=[])
    return c, st, "finite_choice_no_steps"


def _manager_owned_subtask():
    """Under-specified, no explicit steps, but a single bounded action: the
    strong manager (or an escalating cheap route) must choose the action. Success
    is one correct manager decision, so the manager axis is what the arms differ
    on (manager-enabled arms pass; deterministic_only has no manager)."""
    c = SuccessCriterion(
        kind="js_rule", description="new-todo input holds the typed value",
        rule={"js": "(document.querySelector('.new-todo')||{}).value || ''",
              "expected": "manager call"})
    st = Subtask(id="s1", goal="type the text 'manager call' into the todo input",
                 success_criteria=[c], task_class="stateful_dom_eval", steps=[])
    return c, st, "under_specified_single_action"


CASES = [
    ("deterministic_dom_two_todos", _two_todos_subtask),
    ("multi_step_workflow_complete_first", _workflow_subtask),
    ("stateful_dom_eval_structured_owned", _stateful_subtask),
    ("recovery_injected_stale_target", _recovery_subtask),
    ("finite_choice_no_steps", _jev_choice_subtask),
    ("under_specified_stateful", _manager_owned_subtask),
]


def run(transport_name: str, reps: int) -> dict:
    import platform
    out = {"transport": transport_name, "reps": reps,
           "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "commit": git_rev(ROOT),
           "python": platform.python_version(), "platform": platform.platform(),
           "cases": {}}
    for name, builder in CASES:
        crit, st, cls = builder()
        case = {"task_class": cls, "arms": {}}
        for mode in ARM_NAMES:
            walls, wins, fails = [], 0, {}
            acc = {"actions": 0, "observations": 0, "jev_calls": 0, "manager_calls": 0,
                   "fara_calls": 0, "showui_calls": 0, "recoveries": 0, "loops": 0}
            for _rep in range(reps):
                t = _make_case_transport(transport_name, name)
                if hasattr(t, "reset"):
                    t.reset(TODO)
                else:
                    t.navigate(TODO)
                cfg = MODES[mode].model_copy(deep=True)
                cfg.durable = False
                e = Engine(t, config=cfg, store=FileRunStore())
                e.manager.override_plan = Plan(goal="g", subtasks=[st])
                injected = False
                if name.startswith("recovery_injected"):
                    assert isinstance(t, FaultInjectingIsolatedTransport), (
                        "recovery case requires a fault-injecting transport")
                    t.fail_next = "stale"
                    injected = True
                start = time.perf_counter()
                r = e.execute(TaskRequest(goal=st.goal, success_criteria=[crit],
                                          start_url=TODO))
                walls.append((time.perf_counter() - start) * 1000.0)
                if r.verified:
                    wins += 1
                else:
                    fails[str(r.failure_class)] = fails.get(str(r.failure_class), 0) + 1
                for k in acc:
                    acc[k] += r.metrics.get(k, 0) or 0
                if injected:
                    assert r.metrics.get("recoveries", 0) >= 1, (
                        "injected recovery did not fire")
                t.close()
            o = sorted(walls)
            n = max(1, reps)
            case["arms"][mode] = {
                "verified_success": wins, "reps": reps,
                "success_rate": round(wins / reps, 3),
                "wall_min_ms": round(o[0], 1),
                "wall_p50_ms": round(o[len(o) // 2], 1),
                "wall_max_ms": round(o[-1], 1),
                "wall_all_ms": [round(w, 1) for w in walls],
                "actions_mean": round(acc["actions"] / n, 2),
                "observations_mean": round(acc["observations"] / n, 2),
                "jev_calls_mean": round(acc["jev_calls"] / n, 2),
                "fara_calls_mean": round(acc["fara_calls"] / n, 2),
                "showui_calls_mean": round(acc["showui_calls"] / n, 2),
                "manager_calls_mean": round(acc["manager_calls"] / n, 2),
                "recoveries_mean": round(acc["recoveries"] / n, 2),
                "loops_mean": round(acc["loops"] / n, 2),
                "failure_classes": fails,
            }
        out["cases"][name] = case
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", default="isolated")
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()
    res = run(args.transport, args.reps)
    jp, mp = write_results(res, ROOT / "results/e2e", commit=res["commit"])
    print("wrote", jp, mp)
    for name, case in res["cases"].items():
        for mode, arm in case["arms"].items():
            print(f"{name:34s} {mode:20s} {arm['verified_success']}/{arm['reps']} "
                  f"median={arm['wall_p50_ms']}ms min={arm.get('wall_min_ms')} "
                  f"max={arm.get('wall_max_ms')}")

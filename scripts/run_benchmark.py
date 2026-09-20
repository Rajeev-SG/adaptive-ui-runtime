#!/usr/bin/env python3
"""Run the runtime benchmark/ablation suite and write RESULTS.md.

Default suite uses the deterministic fake transport (fast, CI-safe). Pass
--transport playwriter/relay for a live run against a real browser.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_ui_runtime.benchmark import git_rev, run_suite, write_results  # noqa: E402
from adaptive_ui_runtime.contracts import Plan, Subtask, SuccessCriterion, TaskRequest  # noqa: E402


def _crit(value: str) -> SuccessCriterion:
    return SuccessCriterion(kind="state", description=f"items contains {value}",
                            expected=value, rule={"field": "items"})


def build_cases() -> list[dict]:
    cases = []
    # 1. deterministic DOM class: should bypass model inference on every arm
    c1 = _crit("alpha")
    st1 = Subtask(id="s1", goal="type alpha then search", success_criteria=[c1],
                  task_class="deterministic_dom",
                  steps=[{"kind": "type", "target": "field", "value": "alpha"},
                         {"kind": "click", "target": "search"}])
    cases.append({
        "name": "deterministic_dom_two_step",
        "request": TaskRequest(goal="type alpha then search", success_criteria=[c1]),
        "plan": Plan(goal="g", subtasks=[st1], rationale="benchmark"),
    })
    # 2. ambiguous-target safety: two same-role targets must fail closed (F4),
    #    never silently bind an arbitrary element. Adaptive cannot succeed here;
    #    this is a safety invariant, not a success case.
    c2 = _crit("never")
    st2 = Subtask(id="s1", goal="click a button", success_criteria=[c2],
                  task_class="deterministic_dom",
                  steps=[{"kind": "click", "target_any": "button"}])
    cases.append({
        "name": "ambiguous_target_fails_closed",
        "request": TaskRequest(goal="click a button", success_criteria=[c2]),
        "plan": Plan(goal="g", subtasks=[st2], rationale="benchmark"),
    })
    # 3. stateful DOM/eval class: must route to strong-manager-owned loop
    c3 = _crit("gamma")
    st3 = Subtask(id="s1", goal="g", success_criteria=[c3],
                  task_class="stateful_dom_eval",
                  steps=[{"kind": "type", "target": "field", "value": "gamma"},
                         {"kind": "click", "target": "search"}])
    cases.append({
        "name": "stateful_dom_eval_owned_by_manager",
        "request": TaskRequest(goal="g", success_criteria=[c3]),
        "plan": Plan(goal="g", subtasks=[st3], rationale="benchmark"),
    })
    return cases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", default="fake")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    results = run_suite(build_cases(), reps=args.reps, transport=args.transport)
    jp, mp = write_results(results, ROOT / args.out, commit=git_rev(ROOT))
    print(f"wrote {jp} and {mp}")
    for name, case in results["cases"].items():
        for mode, arm in case["arms"].items():
            print(f"{name:34s} {mode:20s} {arm['verified_success']}/{arm['reps']} "
                  f"p50={arm['wall_p50_ms']}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Microbench consumption (issue #15).

Consumes `Rajeev-SG/web-automation-microbench` task specs (registry, reset URL,
instruction, independent verifier) instead of forking the benchmark. The task's
declarative `pass_rule` is evaluated by the runtime verifier — no per-task code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Plan, Subtask, SuccessCriterion, TaskRequest

#: Local microbench checkout (reused, never cloned).
DEFAULT_ROOTS = (
    Path.home() / "Code" / "web-automation-microbench" / "bench-ext" / "corpus" / "tasks",
    Path.home() / "Code" / "local_cua" / "corpus" / "microbench" / "tasks",
)


def find_root(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(p)
        return p
    for root in DEFAULT_ROOTS:
        if root.exists():
            return root
    raise FileNotFoundError("microbench corpus not found locally")


def list_tasks(root: str | Path | None = None) -> list[str]:
    r = find_root(root)
    return sorted(p.stem for p in r.glob("*.json"))


def load_spec(task_id: str, root: str | Path | None = None) -> dict[str, Any]:
    r = find_root(root)
    p = r / f"{task_id}.json"
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text())


def _js_rule(spec: dict[str, Any]) -> dict[str, Any]:
    """Build a js_rule criterion from the task's independent verifier.

    The verifier JS recomputes ground truth from the live DOM and compares it to
    the finding the agent recorded in window.__bench_finding; the spec's own
    `pass_rule` decision is what we check. We embed both so the runtime verifier
    can apply `finding_matches_truth` with no per-task code.
    """
    verification = spec.get("verification") or {}
    verify_js = verification.get("verify_js")
    pass_rule = verification.get("pass_rule") or {}
    # The verify_js in microbench returns {pass: bool, truth: ..., finding: ...}-ish
    # shapes; we ask it for the truth and compare to the recorded finding.
    # verify_js already recomputes the truth and reads window.__bench_finding,
    # returning a JSON string {url, truth, finding}. We reuse it verbatim.
    js = verify_js or "(() => JSON.stringify({truth:{},finding:null}))()"
    return {
        "kind": "js_rule",
        "description": verification.get("description", spec.get("objective", "")),
        "rule": {"js": js, "microbench_pass_rule": pass_rule},
    }


def build(task_id: str, root: str | Path | None = None) -> tuple[TaskRequest, Plan]:
    spec = load_spec(task_id, root)
    criteria = [
        SuccessCriterion(
            kind="js_rule",
            description=(spec.get("verification") or {}).get(
                "description", spec.get("objective", spec.get("instruction", ""))),
            rule=_js_rule(spec)["rule"],
        )
    ]
    request = TaskRequest(
        goal=spec.get("instruction") or spec.get("objective") or task_id,
        success_criteria=criteria,
        start_url=spec.get("url"),
        constraints={"task_id": task_id,
                     "task_class": spec.get("task_class", "live_site_audit")},
    )
    # Microbench task: live-site audit whose truth is DOM/eval-recomputed ->
    # owned by the structured/manager loop, never a bare visual worker.
    subtask = Subtask(
        id="mb",
        goal=request.goal,
        success_criteria=criteria,
        task_class=spec.get("task_class", "live_site_audit"),
        budget=spec.get("budget") and __import__("adaptive_ui_runtime.contracts",
                                                 fromlist=["Budget"]).Budget(**spec["budget"])
        or __import__("adaptive_ui_runtime.contracts", fromlist=["Budget"]).Budget(
            max_actions=14, max_wall_seconds=300),
    )
    return request, Plan(goal=request.goal, subtasks=[subtask],
                         rationale=f"microbench task {task_id}")


def reset_js(spec: dict[str, Any]) -> str | None:
    pre = spec.get("pre_state") or {}
    return pre.get("reset_js")

"""Adaptive router: fastest route consistent with measured correctness (#12).

Rule-based and transparent — no opaque learned meta-router in v1. The router
chooses per subtask/action, never "one model owns the whole workflow".

Evidence boundary (local_cua PR #16): bare Fara fails stateful/live-site
DOM-truth tasks, so those route to a strong-manager-owned structured loop.
There is no Fara-4B -> Fara-9B escalation.
"""

from __future__ import annotations

from .contracts import (
    Observation,
    RouteDecision,
    RouteKind,
    RuntimeConfig,
    Subtask,
)

#: Task classes that require the strong planner's structured DOM/eval channel.
STRONG_OWNED_CLASSES = {
    "stateful_dom_eval",
    "live_site_audit",
    "multi_item_stateful",
    "long_workflow",
    "dynamic_ui",
}
#: Task classes a bounded local visual worker may own.
LOCAL_VISUAL_CLASSES = {"visual_grounding", "one_shot_action", "short_visual_micro_job"}
#: Task classes Jev may decide.
JEV_CLASSES = {"deterministic_dom", "search_extract_act", "form_filter_download"}


class AdaptiveRouter:
    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.decisions: list[RouteDecision] = []

    def _record(self, decision: RouteDecision) -> RouteDecision:
        self.decisions.append(decision)
        return decision

    def route(
        self,
        subtask: Subtask,
        observation: Observation | None,
        transport: str,
        transport_caps: frozenset[str],
        structured_truth: bool = False,
        prior_failures: list[str] | None = None,
        escalations: int = 0,
        forced: RouteKind | None = None,
    ) -> RouteDecision:
        cfg = self.config
        prior = prior_failures or []
        tc = subtask.task_class or ""

        if forced is not None:
            return self._record(RouteDecision(route=forced, reason="forced route",
                                              escalation=None))

        # 0. After an unexpected/ambiguous state, only the manager may decide.
        if "unexpected_state" in prior or "verifier_mismatch" in prior:
            return self._record(RouteDecision(
                route=RouteKind.STRONG_MANAGER,
                reason="ambiguous/failed state requires manager replan",
                alternatives=["structured_browser"],
            ))

        # 1. Deterministic/known structured action, if available.
        if RouteKind.DETERMINISTIC in subtask.allowed_routes and subtask.id in (
            getattr(subtask, "known_recipe_ids", []) or []
        ):
            return self._record(RouteDecision(
                route=RouteKind.DETERMINISTIC, reason="known verified recipe",
                alternatives=["structured_browser"]))

        # 2. Strong-owned stateful / DOM-eval / live-site workflows.
        if tc in STRONG_OWNED_CLASSES:
            return self._record(RouteDecision(
                route=RouteKind.STRONG_MANAGER,
                reason=f"task_class={tc} needs planner-owned DOM/eval loop",
                alternatives=["structured_browser", "showui"],
                escalation=RouteKind.STRONG_MANAGER,
            ))

        # 3. Direct structured browser resolution when the target is unambiguous.
        if observation and structured_truth and "click" in transport_caps:
            if RouteKind.STRUCTURED_BROWSER in subtask.allowed_routes:
                return self._record(RouteDecision(
                    route=RouteKind.STRUCTURED_BROWSER,
                    reason="structured target resolved unambiguously",
                    alternatives=["jev", "deterministic"],
                    escalation=RouteKind.JEV,
                ))

        # 4. Jev for calibrated finite-choice browser decisions.
        if cfg.enable_jev and tc in JEV_CLASSES:
            if RouteKind.JEV in subtask.allowed_routes:
                return self._record(RouteDecision(
                    route=RouteKind.JEV,
                    reason=f"calibrated finite-choice class {tc}",
                    confidence=cfg.jev_confidence_threshold,
                    alternatives=["structured_browser"],
                    escalation=RouteKind.STRONG_MANAGER,
                    budget_actions=subtask.budget.max_actions,
                ))

        # 5. Bounded local visual grounding/action.
        if tc in LOCAL_VISUAL_CLASSES:
            if cfg.enable_showui and RouteKind.SHOWUI in subtask.allowed_routes:
                return self._record(RouteDecision(
                    route=RouteKind.SHOWUI,
                    reason="subgoal known; cheap local actor grounds it",
                    alternatives=["fara", "strong_manager"],
                    escalation=RouteKind.STRONG_MANAGER,
                    budget_actions=min(2, subtask.budget.max_actions),
                ))
            if cfg.enable_fara and RouteKind.FARA in subtask.allowed_routes:
                return self._record(RouteDecision(
                    route=RouteKind.FARA,
                    reason="bounded visual micro-job",
                    alternatives=["strong_manager"],
                    escalation=RouteKind.STRONG_MANAGER,
                    budget_actions=min(2, subtask.budget.max_actions),
                ))

        # 6. Fall back to the strong manager.
        return self._record(RouteDecision(
            route=RouteKind.STRONG_MANAGER,
            reason="no cheaper route is calibrated for this class",
            alternatives=["structured_browser"],
        ))

    def escalate(self, current: RouteDecision, failure_class: str) -> RouteDecision:
        nxt = current.escalation or RouteKind.STRONG_MANAGER
        return self._record(RouteDecision(
            route=nxt,
            reason=f"escalated after {failure_class}",
            alternatives=[str(current.route)],
            escalation=RouteKind.STRONG_MANAGER,
        ))

    def snapshot(self) -> dict:
        return self.config.model_dump()

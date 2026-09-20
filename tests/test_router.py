"""Router tests (issue #12)."""
from adaptive_ui_runtime.contracts import RouteKind, RuntimeConfig, Subtask, SuccessCriterion
from adaptive_ui_runtime.router import AdaptiveRouter


def st(tc):
    return Subtask(id="s", goal="g", success_criteria=[SuccessCriterion(kind="url", description="d")],
                   task_class=tc)


def test_stateful_routes_to_manager():
    r = AdaptiveRouter(RuntimeConfig())
    d = r.route(st("stateful_dom_eval"), None, "relay", frozenset({"click"}))
    assert d.route == RouteKind.STRONG_MANAGER


def test_jev_class_routes_to_jev():
    r = AdaptiveRouter(RuntimeConfig())
    d = r.route(st("deterministic_dom"), None, "relay", frozenset({"click"}))
    assert d.route in (RouteKind.JEV, RouteKind.STRUCTURED_BROWSER)


def test_visual_class_routes_to_showui():
    r = AdaptiveRouter(RuntimeConfig())
    d = r.route(st("visual_grounding"), None, "relay", frozenset({"click"}))
    assert d.route == RouteKind.SHOWUI


def test_fara9b_absent_from_policy():
    cfg = RuntimeConfig()
    assert cfg.allow_fara_9b is False
    r = AdaptiveRouter(cfg)
    for tc in ("stateful_dom_eval", "deterministic_dom", "visual_grounding", "long_workflow"):
        d = r.route(st(tc), None, "relay", frozenset({"click"}))
        assert d.escalation != RouteKind.FARA


def test_unexpected_state_forces_manager():
    r = AdaptiveRouter(RuntimeConfig())
    d = r.route(st("deterministic_dom"), None, "relay", frozenset({"click"}),
                prior_failures=["unexpected_state"])
    assert d.route == RouteKind.STRONG_MANAGER


def test_config_snapshot_emitted():
    r = AdaptiveRouter(RuntimeConfig(mode="no_jev", enable_jev=False))
    snap = r.snapshot()
    assert snap["mode"] == "no_jev" and snap["enable_jev"] is False

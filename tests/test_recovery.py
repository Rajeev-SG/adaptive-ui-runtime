"""Cycle detection + classified recovery (issue #11)."""
from adaptive_ui_runtime.contracts import CandidateAction, Observation, RouteKind
from adaptive_ui_runtime.recovery import CycleDetector, RecoveryPolicy
from adaptive_ui_runtime.transports.fake import FakeTransport


def _obs(fp="same"):
    return Observation(snapshot_id="s", state_fingerprint=fp)


def test_cycle_detector_bounds_repeats():
    c = CycleDetector(limit=1)
    a = CandidateAction(kind="click", target="x")
    assert c.observe(_obs(), a)[0] is False
    assert c.observe(_obs(), a)[0] is True
    assert c.observe(_obs("diff"), a)[0] is False


def test_classification():
    p = RecoveryPolicy()
    assert p.classify("target is stale") == "stale_target"
    assert p.classify("focus lost") == "focus_lost"
    assert p.classify("modal covering") == "obstruction"
    assert p.classify(None, verifier_failed=True) == "verifier_mismatch"
    assert p.classify(None, repeated=True) == "repeated_action_loop"


def test_focus_repair_uses_transport():
    t = FakeTransport()
    t.app.focused = False
    p = RecoveryPolicy()
    out = p.repair("focus_lost", t)
    assert out.repaired and t.app.focused is True


def test_repair_is_bounded():
    p = RecoveryPolicy(max_attempts=2)
    p.repair("unexpected_state", FakeTransport())
    p.repair("unexpected_state", FakeTransport())
    assert p.exhausted("unexpected_state")


def test_escalation_routes_exist():
    p = RecoveryPolicy()
    assert p.escalation_route("transport_error") == RouteKind.STRUCTURED_BROWSER
    assert p.escalation_route("unexpected_state") == RouteKind.STRONG_MANAGER

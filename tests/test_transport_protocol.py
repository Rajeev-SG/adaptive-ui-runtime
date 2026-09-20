"""Transport protocol + capability tests (issue #4/#5)."""
import pytest

from adaptive_ui_runtime.contracts import Target
from adaptive_ui_runtime.transports.base import StaleTargetError, Transport
from adaptive_ui_runtime.transports.fake import FakeTransport


def test_fake_transport_satisfies_protocol():
    t = FakeTransport()
    assert isinstance(t, Transport)


def test_capabilities_are_advertised():
    t = FakeTransport()
    assert t.supports("click") and t.supports("observe")
    assert not t.supports("teleport")


def test_stale_node_fails_closed():
    t = FakeTransport()
    obs = t.observe()
    target = next(x for x in obs.targets if x.id == "field")
    # a node id from a different observation epoch must be rejected
    stale = Target(id="field", kind="fill", node=target.node + 999)
    with pytest.raises(StaleTargetError):
        t.type(stale, "x")


def test_no_selector_leaks_in_contract():
    # CandidateAction.target names an observed node id, never a CSS selector
    t = FakeTransport()
    obs = t.observe()
    for target in obs.targets:
        assert not target.id.startswith((".", "#", "["))


def test_observation_is_transport_neutral():
    t = FakeTransport()
    obs = t.observe()
    assert obs.snapshot_id and obs.state_fingerprint
    assert obs.transport == "fake"

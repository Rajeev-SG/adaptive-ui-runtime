"""Shadow mode must not be able to mutate the transport (issue #16)."""
import pytest

from adaptive_ui_runtime.shadow import ReadOnlyObservation, ShadowRunner
from adaptive_ui_runtime.transports.fake import FakeTransport


def test_read_only_observation_cannot_mutate():
    obs = FakeTransport().observe()
    ro = ReadOnlyObservation(obs)
    assert ro.observe().snapshot_id == obs.snapshot_id
    with pytest.raises(AttributeError):
        ro.click(None)  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        ro.type(None, "x")  # type: ignore[attr-defined]


def test_shadow_produces_records_without_acting():
    t = FakeTransport()
    obs = t.observe()
    before = list(t.app.items)
    runner = ShadowRunner(sample_rate=1.0, enable=True, seed=0)

    class W:
        def decide(self, obs, goal):
            from adaptive_ui_runtime.contracts import CandidateAction, WorkerResult
            return WorkerResult(proposed=[CandidateAction(kind="click", target="search",
                                                          confidence=0.9)], calls=1)

    rec = runner.collect(obs, "structured_browser", {"kind": "type"}, {"jev": W()})
    assert rec and rec["shadow"]["jev"]["confidence"] == 0.9
    assert t.app.items == before  # production state untouched


def test_shadow_disabled_by_default():
    runner = ShadowRunner()
    assert runner.enable is False
    assert runner.collect(FakeTransport().observe(), "x", None, {}) is None

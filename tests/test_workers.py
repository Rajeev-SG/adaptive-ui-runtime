"""Worker contract tests (issue #8/#9)."""
from adaptive_ui_runtime.workers.jev import JevWorker
from adaptive_ui_runtime.workers.visual import FARA_9B_MODEL, LocalVisualWorker


def obs():
    from adaptive_ui_runtime.transports.fake import FakeTransport
    return FakeTransport().observe()


def test_jev_two_question_framing():
    w = JevWorker()
    cands = w.candidates(obs())
    assert "operation" in cands
    # upstream shape: per-operation target heads
    assert "click_target" in cands
    assert "type_target" in cands


def test_jev_targets_are_observed_node_ids():
    w = JevWorker()
    cands = w.candidates(obs())
    assert set(cands["click_target"]) <= {"field", "search", "add"}


def test_fara_refuses_stateful_class():
    w = LocalVisualWorker(kind="fara")
    r = w.propose(obs(), "select UK and apply filters", task_class="stateful_dom_eval")
    assert not r.proposed
    assert "escalate" in r.detail


def test_fara9b_is_not_the_routed_model():
    w = LocalVisualWorker(kind="fara")
    assert w.model != FARA_9B_MODEL


def test_bounded_budget_enforced_by_runtime_not_prompt():
    # max_actions is a runtime field, not prompt text
    w = LocalVisualWorker(kind="fara", max_actions=2)
    assert w.max_actions == 2

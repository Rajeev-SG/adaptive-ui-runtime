"""Microbench consumption + pass-rule parity (issue #15)."""

from adaptive_ui_runtime.contracts import Observation, SuccessCriterion
from adaptive_ui_runtime.microbench import build, list_tasks
from adaptive_ui_runtime.verifier import Verifier


def test_microbench_corpus_is_consumed_not_forked():
    tasks = list_tasks()
    assert "puma-uk-tag-inspection" in tasks
    assert len(tasks) >= 5  # >=5 representative task classes (issue #15)


def test_build_produces_structured_owned_subtask():
    request, plan = build("puma-uk-tag-inspection")
    assert request.start_url
    st = plan.subtasks[0]
    # live-site DOM/eval task -> never routed to a bare visual worker
    assert st.task_class in ("live_site_audit", "web-automation", "stateful_dom_eval")


def _obs(truth, finding):
    return Observation(snapshot_id="s", state_fingerprint="f",
                       structured_state={"js_rule_ran": True,
                                         "js_result": {"truth": truth, "finding": finding}})


def test_pass_rule_parity_pass_and_fail():
    v = Verifier()
    crit = SuccessCriterion(kind="js_rule", description="d", rule={
        "microbench_pass_rule": {
            "kind": "finding_matches_truth",
            "fields": ["gtm", "aw"],
            "presence_fields": ["pinterest"],
            "require_any_of": ["gtm", "aw", "pinterest"],
        }})
    truth = {"gtm": ["GTM-A"], "aw": ["AW-123456"], "pinterest": True}
    assert v.check([crit], _obs(truth, dict(truth))).passed
    wrong = {"gtm": ["GTM-B"], "aw": ["AW-123456"], "pinterest": True}
    assert not v.check([crit], _obs(truth, wrong)).passed


def test_degenerate_measurement_fails_closed():
    v = Verifier()
    crit = SuccessCriterion(kind="js_rule", description="d", rule={
        "microbench_pass_rule": {
            "kind": "finding_matches_truth", "fields": ["gtm"],
            "require_any_of": ["gtm", "aw", "pinterest"]}})
    empty = {"gtm": [], "aw": [], "pinterest": False}
    assert not v.check([crit], _obs(empty, empty)).passed

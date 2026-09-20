"""Verifier tests (issue #10)."""
from adaptive_ui_runtime.contracts import Observation, SuccessCriterion
from adaptive_ui_runtime.verifier import Verifier


def obs(**state):
    return Observation(snapshot_id="s", state_fingerprint="f",
                       url=state.get("url"), structured_state=state)


def test_dom_value_pass_and_fail():
    v = Verifier()
    c = SuccessCriterion(kind="dom_value", description="field", expected="UK",
                         rule={"field": "country"})
    assert v.check([c], obs(country="UK")).passed
    assert not v.check([c], obs(country="US")).passed


def test_premature_done_is_rejected():
    v = Verifier()
    c = SuccessCriterion(kind="dom_value", description="d", expected="x",
                         rule={"field": "k"})
    assert not v.check([c], obs(k="y")).passed


def test_url_only_false_positive_prevented():
    v = Verifier()
    c = SuccessCriterion(kind="url_and_state", description="d",
                         rule={"url": "/step2", "field": "saved", "value": True})
    # correct URL but the required state is absent -> must fail
    assert not v.check([c], obs(url="https://x/step2", saved=False)).passed
    assert v.check([c], obs(url="https://x/step2", saved=True)).passed


def test_file_freshness():
    v = Verifier()
    c = SuccessCriterion(kind="file", description="report", expected="report.xlsx",
                         rule={"min_bytes": 100, "after": 1000})
    ok = obs(downloads=[{"name": "report.xlsx", "bytes": 500, "mtime": 2000}])
    stale = obs(downloads=[{"name": "report.xlsx", "bytes": 500, "mtime": 500}])
    assert v.check([c], ok).passed
    assert not v.check([c], stale).passed


def test_and_or_composition():
    v = Verifier()
    a = SuccessCriterion(kind="dom_value", description="a", expected=1, rule={"field": "a"})
    b = SuccessCriterion(kind="dom_value", description="b", expected=2, rule={"field": "b"})
    assert v.check([a, b], obs(a=1, b=2)).passed
    assert not v.check([a, b], obs(a=1, b=9)).passed
    assert v.check([a, b], obs(a=1, b=9), combine="or").passed


def test_verifier_error_is_distinct_bucket():
    v = Verifier()
    r = v.check([SuccessCriterion(kind="url", description="d")], observation=None)
    assert r.error and not r.passed


def test_js_rule_fails_closed_without_expectation():
    v = Verifier()
    c = SuccessCriterion(kind="js_rule", description="d", rule={"js": "1"})
    # no expectation and no js_result -> fail closed
    assert not v.check([c], obs(js_rule_ran=True, js_result="yes")).passed

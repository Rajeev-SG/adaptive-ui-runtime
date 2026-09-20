"""Independent verifier engine (issue #10).

Success is established by independent evidence, never by an actor's self-report.
An actor `DONE` is only a *proposal* to verify.

Verifier kinds compose with AND/OR. Structured evidence is preferred; a
probabilistic/visual check must expose confidence and is only used where
structured evidence is unavailable.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .contracts import (
    FailureClass,
    Observation,
    SuccessCriterion,
    VerificationResult,
)
from .transports.base import Transport

#: kind -> checker(observation, criterion) -> (passed, evidence)
Checker = Callable[[Observation, SuccessCriterion], tuple[bool, dict[str, Any]]]


def _get(state: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = state
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _check_url(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    want = str(crit.expected or "")
    got = obs.url or ""
    ok = got.rstrip("/").endswith(want.rstrip("/")) if want else bool(got)
    return ok, {"url": got, "expected": want}


def _check_dom_value(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    state = obs.structured_state
    key = crit.rule.get("field") if crit.rule else None
    if key is None:
        key = (crit.rule or {}).get("key")
    if key is None:
        # fall back to matching the description against target labels
        want = crit.expected
        for t in obs.targets:
            if t.label and crit.description.lower() in t.label.lower():
                return t.value == str(want or ""), {"target": t.id, "value": t.value}
        return False, {"reason": "no field/key in criterion"}
    got = _get(state, str(key))
    return got == crit.expected, {"field": key, "value": got, "expected": crit.expected}


def _check_state_contains(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    state = obs.structured_state
    key = (crit.rule or {}).get("field")
    want = crit.expected
    got = _get(state, str(key)) if key else None
    if isinstance(got, list):
        return (want in got), {"field": key, "value": got, "expected": want}
    return got == want, {"field": key, "value": got, "expected": want}


def _check_url_and_more(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    """Guard against a URL-only false positive (issue #10 test).

    Requires the URL match *and* a state field match.
    """
    rule = crit.rule or {}
    want_url = str(rule.get("url", ""))
    url_ok = (obs.url or "").rstrip("/").endswith(want_url.rstrip("/"))
    field = rule.get("field")
    want_value = rule.get("value")
    value = _get(obs.structured_state, str(field)) if field else None
    value_ok = value == want_value
    return url_ok and value_ok, {
        "url": obs.url, "url_ok": url_ok,
        "field": field, "value": value, "value_ok": value_ok,
    }


def _check_file_exists(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    """Downloaded-file existence + freshness, from transport download metadata."""
    rule = crit.rule or {}
    files = obs.structured_state.get("downloads", [])
    name = rule.get("name", crit.expected)
    min_bytes = int(rule.get("min_bytes", 1))
    after = rule.get("after")
    for f in files:
        if name and str(name) not in str(f.get("name", "")):
            continue
        if int(f.get("bytes", 0)) < min_bytes:
            return False, {"file": f, "reason": "too small / stale"}
        if after is not None and float(f.get("mtime", 0)) < float(after):
            return False, {"file": f, "reason": "stale file"}
        return True, {"file": f}
    return False, {"name": name, "reason": "not found", "files": files}


def _check_visual(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    """Probabilistic visual invariant — used only when structured evidence is
    impossible. Never silently replaces structured evidence."""
    rule = crit.rule or {}
    if not obs.screenshot_ref:
        return False, {"reason": "no screenshot available"}
    conf = float(rule.get("confidence", 0.0))
    threshold = float(rule.get("threshold", 0.5))
    return conf >= threshold, {
        "screenshot_ref": obs.screenshot_ref,
        "confidence": conf,
        "threshold": threshold,
        "probabilistic": True,
    }


def _check_microbench(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    """Adapter for a microbench `finding_matches_truth` rule.

    The actor records a finding in page state; truth is recomputed from the live
    DOM by the microbench pass rule. Here we compare the recorded finding against
    the observed truth using the declarative rule (no per-task code).
    """
    rule = crit.rule or {}
    finding = obs.structured_state.get("finding") or {}
    truth = obs.structured_state.get("truth") or {}
    if not truth and rule.get("require_any_of"):
        # fail closed: an empty measurement is an invalid run, not a pass
        return False, {"reason": "degenerate measurement", "truth": truth}
    problems: list[str] = []
    for field in rule.get("list_fields", []):
        f = set(finding.get(field) or [])
        t = set(truth.get(field) or [])
        if f != t:
            problems.append(f"{field}: {sorted(f)} != {sorted(t)}")
    for field in rule.get("exact_fields", []):
        if str(finding.get(field, "")).strip() != str(truth.get(field, "")).strip():
            problems.append(f"{field} mismatch")
    for field in rule.get("presence_fields", []):
        if bool(finding.get(field)) != bool(truth.get(field)):
            problems.append(f"{field} presence mismatch")
    return (not problems), {"problems": problems, "finding": finding, "truth": truth}


def _check_js_rule(obs: Observation, crit: SuccessCriterion) -> tuple[bool, dict[str, Any]]:
    """Structured DOM/app truth recomputed at verify time.

    Fails closed: a js rule with no explicit expectation never passes. Supports
    either an exact `expected` match, or a dict of `expect` field comparisons.
    """
    rule = crit.rule or {}
    if not obs.structured_state.get("js_rule_ran"):
        return False, {"reason": "js rule not evaluated"}
    if "js_error" in obs.structured_state:
        return False, {"reason": "js error", "error": obs.structured_state["js_error"]}
    got = obs.structured_state.get("js_result")
    if got is None:
        return False, {"reason": "empty js result (fail closed)"}

    if isinstance(got, str):
        try:
            import json as _json
            parsed = _json.loads(got)
        except Exception:
            return False, {"reason": "js result not JSON", "got": got[:200]}
    else:
        parsed = got

    # Microbench mode: the task's own declarative pass rule compares the
    # recorded finding against the page-recomputed truth.
    mb = rule.get("microbench_pass_rule")
    if mb and isinstance(parsed, dict) and "truth" in parsed:
        return _apply_microbench_pass_rule(mb, parsed.get("truth") or {},
                                           parsed.get("finding") or {})
    got = parsed

    rule = crit.rule or {}
    expected = rule.get("expected")
    if expected is not None:
        return got == expected, {"got": got, "expected": expected, "mode": "exact"}

    expect = rule.get("expect")
    if isinstance(expect, dict):
        problems = []
        for path, want in expect.items():
            cur = got
            for part in str(path).split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    cur = None
                    break
            if cur != want:
                problems.append(f"{path}: {cur!r} != {want!r}")
        return (not problems), {"problems": problems, "got": got, "mode": "fields"}

    return False, {"reason": "no expectation given (fail closed)", "got": got}


def _apply_microbench_pass_rule(rule: dict[str, Any], truth: dict[str, Any],
                                finding: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Evaluate a microbench `finding_matches_truth` pass rule.

    Mirrors the semantics of microbench's own pass_rule.py: list fields compared
    as exact sets, presence fields as booleans, and `require_any_of` fails closed
    on a degenerate (all-empty) measurement.
    """
    if rule.get("require_any_of"):
        if not any(truth.get(f) for f in rule["require_any_of"]):
            return False, {"reason": "degenerate measurement (require_any_of)",
                           "truth": truth, "finding": finding}
    problems: list[str] = []
    for field in rule.get("fields", []):
        f = sorted(finding.get(field) or [])
        t = sorted(truth.get(field) or [])
        if f != t:
            problems.append(f"{field}: finding {f} != truth {t}")
    for field in rule.get("exact_fields", []):
        if str(finding.get(field, "")).strip() != str(truth.get(field, "")).strip():
            problems.append(f"{field}: mismatch")
    for field in rule.get("presence_fields", []):
        if bool(finding.get(field)) != bool(truth.get(field)):
            problems.append(f"{field}: presence mismatch")
    return (not problems), {"problems": problems, "truth": truth, "finding": finding}


class JSRuleVerifier:
    """Evaluates a JS rule through a transport's structured channel."""

    def __init__(self, transport: Any) -> None:
        self.transport = transport

    def run(self, js: str) -> Any:
        return self.transport.evaluate(js)


CHECKERS: dict[str, Checker] = {
    "js_rule": _check_js_rule,
    "dom_query": _check_js_rule,
    "url": _check_url,
    "dom_value": _check_dom_value,
    "state": _check_state_contains,
    "state_contains": _check_state_contains,
    "url_and_state": _check_url_and_more,
    "file": _check_file_exists,
    "download": _check_file_exists,
    "visual": _check_visual,
    "microbench": _check_microbench,
    "finding_matches_truth": _check_microbench,
}


class Verifier:
    """Composes success criteria over an observation."""

    def __init__(self, transport: Transport | None = None) -> None:
        self.transport = transport
        self.timing_ms: float = 0.0

    def check(
        self,
        criteria: list[SuccessCriterion],
        observation: Observation | None = None,
        combine: str = "and",
    ) -> VerificationResult:
        start = time.perf_counter()
        try:
            obs = observation or (self.transport.observe() if self.transport else None)
        except Exception as exc:  # verifier infrastructure failure bucket
            self.timing_ms = (time.perf_counter() - start) * 1000.0
            return VerificationResult(
                passed=False,
                failure_class=FailureClass.VERIFIER_ERROR,
                error=True,
                evidence={"error": str(exc)},
                latency_ms=self.timing_ms,
            )
        if obs is None:
            self.timing_ms = (time.perf_counter() - start) * 1000.0
            return VerificationResult(
                passed=False,
                failure_class=FailureClass.VERIFIER_ERROR,
                error=True,
                evidence={"error": "no observation"},
                latency_ms=self.timing_ms,
            )

        # Pre-evaluate any JS rules through the transport's structured channel
        # so the observation carries the recomputed DOM/app truth.
        js_rules = [c for c in criteria if c.kind in ("js_rule", "dom_query")
                    and c.rule and c.rule.get("js")]
        if js_rules and self.transport is not None:
            extra: dict[str, Any] = {}
            extra["js_rule_ran"] = True
            for c in js_rules:
                rule = c.rule or {}
                try:
                    extra["js_result"] = self.transport.evaluate(rule["js"])
                except Exception as exc:
                    extra["js_result"] = None
                    extra["js_error"] = str(exc)
            obs = obs.model_copy(update={
                "structured_state": {**obs.structured_state, **extra}})

        results: list[dict[str, Any]] = []
        passes: list[bool] = []
        for crit in criteria:
            checker = CHECKERS.get(crit.kind)
            if checker is None:
                results.append({"kind": crit.kind, "passed": False,
                                "reason": "unknown criterion kind"})
                passes.append(False)
                continue
            try:
                ok, evidence = checker(obs, crit)
            except Exception as exc:
                results.append({"kind": crit.kind, "passed": False,
                                "reason": f"checker error: {exc}", "error": True})
                passes.append(False)
                continue
            results.append({"kind": crit.kind, "passed": ok, "evidence": evidence})
            passes.append(ok)

        passed = all(passes) if combine == "and" else any(passes)
        self.timing_ms = (time.perf_counter() - start) * 1000.0
        return VerificationResult(
            passed=passed,
            failure_class=None if passed else FailureClass.VERIFIER_MISMATCH,
            evidence={"criteria": results, "combine": combine,
                      "snapshot_id": obs.snapshot_id},
            latency_ms=self.timing_ms,
        )

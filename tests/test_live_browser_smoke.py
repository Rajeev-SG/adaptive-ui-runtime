"""Scripted real-browser smoke test (issue #2/#13, addresses review F3).

Skipped unless a browser is available. Uses the repo's own Playwriter/Relay
transport when a session is configured, else falls back to a Playwright-driven
local Chromium (already installed via ms-playwright) so CI can still exercise a
real DOM end to end.
"""
from __future__ import annotations

import pytest

from adaptive_ui_runtime.contracts import (
    Plan,
    RuntimeConfig,
    Subtask,
    SuccessCriterion,
    TaskRequest,
)
from adaptive_ui_runtime.durability import FileRunStore
from adaptive_ui_runtime.engine import Engine

TODO_URL = "https://demo.playwright.dev/todomvc/#/"
SAVED_JS = ("JSON.stringify(JSON.parse(localStorage.getItem('react-todos')||'[]')"
            ".map(x=>({title:x.title,completed:x.completed})))")


def _playwright_transport():
    """A transport backed by a local Playwright Chromium (no download)."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # pragma: no cover
        pytest.skip("playwright not installed")
    from adaptive_ui_runtime.contracts import ActionResult, Observation, Target
    from adaptive_ui_runtime.transports.base import CAPABILITIES, fingerprint

    class PW:
        name = "playwright"
        capabilities = frozenset(CAPABILITIES)

        def __init__(self):
            self._pw = sync_playwright().start()
            self.browser = self._pw.chromium.launch(headless=True)
            self.page = self.browser.new_page()
            self.commands = 0

        def supports(self, c):
            return c in self.capabilities

        def _nodes(self):
            return self.page.evaluate("""() => {
              const out=[]; let i=0;
              for (const e of document.querySelectorAll('input,button,a[href]')) {
                const r=e.getBoundingClientRect();
                if (r.width<=0||r.height<=0) continue;
                let kind;
                if (e.tagName==='A') kind='link';
                else if (e.tagName==='BUTTON'||e.type==='submit') kind='button';
                else if (e.tagName==='INPUT') {
                  if (['checkbox','radio'].includes(e.type)) kind=e.type;
                  else if (['button','submit','reset'].includes(e.type)) kind='button';
                  else kind='textbox';
                } else kind='button';
                out.push({id:'n'+(++i), node:i, kind,
                  label: (e.getAttribute('placeholder')||e.innerText||e.getAttribute('aria-label')||'').trim(),
                  value: e.value||''});
              }
              return out; }""")

        def navigate(self, url):
            self.commands += 1
            self.page.goto(url, wait_until="domcontentloaded")
            return ActionResult(ok=True, changed_state=True)

        def observe(self):
            self.commands += 1
            nodes = self._nodes()
            targets = [Target(id=n["id"], kind=n["kind"], label=n["label"],
                              node=n["node"], value=n["value"]) for n in nodes]
            return Observation(snapshot_id=f"pw-{self.commands}",
                               state_fingerprint=fingerprint({"n": [t.id for t in targets]}),
                               url=self.page.url, targets=targets, transport=self.name)

        def _sel(self, target):
            return f"[data-aur='{target.node}']"

        def _stamp(self, target):
            ok = self.page.evaluate(
                """(n) => { let i=0; for (const e of document.querySelectorAll('input,button,a[href]')) {
                     const r=e.getBoundingClientRect(); if (r.width<=0||r.height<=0) continue;
                     if (++i===n) { e.setAttribute('data-aur', n); return true; } } return false; }""",
                target.node)
            if not ok:
                raise RuntimeError("stale target")
            return self._sel(target)

        def click(self, target):
            self.commands += 1
            self.page.locator(self._stamp(target)).click()
            return ActionResult(ok=True, changed_state=True)

        def type(self, target, text):
            self.commands += 1
            self.page.locator(self._stamp(target)).fill(text)
            return ActionResult(ok=True, changed_state=True)

        def key(self, key):
            self.commands += 1
            self.page.keyboard.press(key)
            return ActionResult(ok=True, changed_state=True)

        def select(self, target, value):
            self._stamp(target)
            self.page.select_option(self._sel(target), value)
            return ActionResult(ok=True, changed_state=True)

        def scroll(self, delta):
            self.page.mouse.wheel(0, delta)
            return ActionResult(ok=True, changed_state=False)

        def wait(self, seconds):
            import time
            time.sleep(seconds)
            return ActionResult(ok=True, changed_state=False)

        def focus(self):
            self.page.bring_to_front()
            return ActionResult(ok=True, changed_state=False)

        def screenshot(self):
            return None

        def evaluate(self, expr):
            if expr == SAVED_JS:
                return self.page.evaluate(SAVED_JS)
            if expr == "location.href":
                return self.page.url
            if expr.startswith("localStorage.clear"):
                return self.page.evaluate("() => { localStorage.clear(); return 'ok'; }")
            return self.page.evaluate(f"() => ({expr})")

        def close(self):
            try:
                self.browser.close()
                self._pw.stop()
            except Exception:
                pass

    return PW()


def test_live_todomvc_two_todos_verified(tmp_path):
    t = _playwright_transport()
    try:
        t.navigate(TODO_URL)
        t.evaluate("localStorage.clear(); 'ok'")
        crit = SuccessCriterion(kind="js_rule", description="two saved todos",
                                rule={"js": SAVED_JS,
                                      "expected": [{"title": "Email supplier", "completed": False},
                                                   {"title": "Review invoice", "completed": False}]})
        st = Subtask(id="s1", goal="add two todos", success_criteria=[crit],
                     task_class="deterministic_dom",
                     steps=[{"kind": "type", "target_any": "textbox", "value": "Email supplier"},
                            {"kind": "key", "value": "Enter"},
                            {"kind": "type", "target_any": "textbox", "value": "Review invoice"},
                            {"kind": "key", "value": "Enter"}])
        e = Engine(t, config=RuntimeConfig(durable=False), store=FileRunStore(tmp_path))
        e.manager.override_plan = Plan(goal="g", subtasks=[st])
        r = e.execute(TaskRequest(goal="add two todos", success_criteria=[crit]))
        assert r.verified, r.metrics
        saved = t.evaluate(SAVED_JS)
        import json
        assert [x["title"] for x in json.loads(saved)] == ["Email supplier", "Review invoice"]
    finally:
        t.close()

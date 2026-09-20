"""Isolated Playwright-Chromium transport (issue #5).

A real browser (existing ms-playwright Chromium — no download) with a clean,
controllable page per run. Complements the existing-session Playwriter/Relay
transports where a reproducible reset matters (benchmarks, CI, ablations).
Same observed-node safety contract as the CLI transports.
"""

from __future__ import annotations

import time
from typing import Any

from ..contracts import ActionResult, Observation, Target
from .base import CAPABILITIES, fingerprint

_NODES_JS = """() => {
  const out=[]; let i=0; const LIMIT=60;
  for (const e of document.querySelectorAll('input,button,a[href],select,textarea,[role="button"]')) {
    if (out.length>=LIMIT) break;
    const r=e.getBoundingClientRect(); if (r.width<=0||r.height<=0) continue;
    let kind;
    if (e.tagName==='A') kind='link';
    else if (e.tagName==='SELECT') kind='combobox';
    else if (e.tagName==='TEXTAREA') kind='textbox';
    else if (e.tagName==='BUTTON'||e.type==='submit') kind='button';
    else if (e.tagName==='INPUT') {
      if (['checkbox','radio'].includes(e.type)) kind=e.type;
      else if (['button','submit','reset'].includes(e.type)) kind='button';
      else kind='textbox';
    } else kind='button';
    out.push({id:'n'+(++i), node:i, kind,
      label:(e.getAttribute('placeholder')||e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,60),
      value:(e.value||'').slice(0,60)});
  }
  return out; }"""

_STAMP_JS = """(n) => {
  let i=0; for (const e of document.querySelectorAll('input,button,a[href],select,textarea,[role="button"]')) {
    if (i>=60) break;
    const r=e.getBoundingClientRect(); if (r.width<=0||r.height<=0) continue;
    if (++i===n) { e.setAttribute('data-aur', String(n)); return true; } }
  return false; }"""


class IsolatedBrowserTransport:
    name = "isolated"
    capabilities = frozenset(CAPABILITIES)

    def __init__(self, headless: bool = True, url: str | None = None) -> None:
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=headless)
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.commands = 0
        #: One-shot fault injection for recovery tests/benchmarks:
        #: "stale" raises a stale-target error on the next action.
        self.fail_next: str | None = None
        if url:
            self.navigate(url)

    def supports(self, cap: str) -> bool:
        return cap in self.capabilities

    # -- reset (clean state per rep) --------------------------------------
    def reset(self, url: str) -> None:
        self.context.clear_cookies()
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            self.page.reload(wait_until="domcontentloaded")
        except Exception:
            self.page.goto(url, wait_until="domcontentloaded")

    def navigate(self, url: str) -> ActionResult:
        self.commands += 1
        self.page.goto(url, wait_until="domcontentloaded")
        return ActionResult(ok=True, changed_state=True)

    def observe(self) -> Observation:
        self.commands += 1
        nodes = self.page.evaluate(_NODES_JS)
        targets = [Target(id=n["id"], kind=n["kind"], label=n["label"],
                          node=n["node"], value=n["value"]) for n in nodes]
        return Observation(snapshot_id=f"iso-{self.commands}",
                           state_fingerprint=fingerprint(
                               {"n": [t.id + t.value for t in targets]}),
                           url=self.page.url, targets=targets, transport=self.name)

    def _inject_failure(self) -> None:
        if self.fail_next:
            kind, self.fail_next = self.fail_next, None
            from .base import StaleTargetError
            if kind == "stale":
                raise StaleTargetError("injected stale target")

    def _sel(self, target: Target) -> str:
        self._inject_failure()
        if not self.page.evaluate(_STAMP_JS, target.node):
            raise RuntimeError("stale or covered target")
        return f"[data-aur='{target.node}']"

    def click(self, target: Target) -> ActionResult:
        self.commands += 1
        loc = self.page.locator(self._sel(target))
        try:
            loc.click(timeout=8000)
        except Exception:
            # Hidden-but-interactive controls (e.g. TodoMVC's opacity:0 toggle)
            # need a forced click; this is transport-native, not a bespoke repair.
            loc.click(timeout=8000, force=True)
        return ActionResult(ok=True, changed_state=True)

    def type(self, target: Target, text: str) -> ActionResult:
        self.commands += 1
        self.page.locator(self._sel(target)).fill(text, timeout=8000)
        return ActionResult(ok=True, changed_state=True)

    def key(self, key: str) -> ActionResult:
        self.commands += 1
        self.page.keyboard.press(key)
        return ActionResult(ok=True, changed_state=True)

    def select(self, target: Target, value: str) -> ActionResult:
        self.page.select_option(self._sel(target), value)
        return ActionResult(ok=True, changed_state=True)

    def scroll(self, delta: int) -> ActionResult:
        self.page.mouse.wheel(0, delta)
        return ActionResult(ok=True, changed_state=False)

    def wait(self, seconds: float) -> ActionResult:
        time.sleep(seconds)
        return ActionResult(ok=True, changed_state=False)

    def focus(self) -> ActionResult:
        self.page.bring_to_front()
        return ActionResult(ok=True, changed_state=False)

    def screenshot(self) -> str | None:
        return None

    def evaluate(self, expression: str) -> Any:
        self.commands += 1
        return self.page.evaluate(f"() => ({expression})")

    def close(self) -> None:
        for fn in (self.browser.close, self._pw.stop):
            try:
                fn()
            except Exception:
                pass

"""Shared CLI-transport base for Playwriter and Browser Relay (issue #5).

Reuses the mechanics proven in `jev-tests` `bridge.py` @4e5ed27:

* a worker selects an *observed* integer node id;
* this code revalidates that exact node and stamps a short-lived code-owned
  attribute;
* the transport executes the action against the generated selector.

The model/worker never supplies a selector, coordinate, JS or shell command.
No silent fallback inside a transport — fallback belongs to the router.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from typing import Any

from ..contracts import ActionResult, Observation, Target
from .base import CAPABILITIES, StaleTargetError, TransportError, fingerprint

#: Satisfaction of the BridgeBrowser contract: observed-node identity is kept in
#: `window.__uiNodes` and cleared on each observe.
OBSERVE_JS = r"""
(() => {
  if (!document.body) return null;
  const state = window.__uiNodes ||= {ids:new WeakMap(), nodes:new Map(), next:1};
  state.nodes.clear();
  const visible = e => !e.closest('[aria-hidden="true"],[inert]') &&
    e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
  const name = e => (e.getAttribute('aria-label') || (e.labels && e.labels[0] && e.labels[0].innerText) ||
    e.value || e.getAttribute('placeholder') || e.getAttribute('title') ||
    (e.innerText || '').slice(0,60) || '').trim();
  const roles=['button','link','checkbox','radio','switch','tab','menuitem','option',
    'combobox','textbox','searchbox','spinbutton'];
  const sel='a[href],button,input,textarea,select,summary,[contenteditable="true"],'+
    roles.map(r=>'[role="'+r+'"]').join(',');
  const role = e => {
    const x=e.getAttribute('role'); if (roles.includes(x)) return x;
    if (e.tagName==='BUTTON') return 'button';
    if (e.tagName==='A') return 'link';
    if (e.tagName==='SELECT') return 'combobox';
    if (e.tagName==='TEXTAREA'||e.isContentEditable) return 'textbox';
    if (e.tagName==='INPUT') {
      if(['checkbox','radio'].includes(e.type)) return e.type;
      if(['button','submit','reset'].includes(e.type)) return 'button';
      if(e.type==='search') return 'searchbox';
      return 'textbox';
    }
    return 'textbox';
  };
  const out=[];
  for (const e of document.querySelectorAll(sel)) {
    if (e.type==='password'||e.type==='file'||e.type==='hidden') continue;
    if (!visible(e) || e.matches(':disabled')) continue;
    const r=e.getBoundingClientRect();
    if (r.width<=0||r.height<=0) continue;
    let id = state.ids.get(e); if(!id){ id=state.next++; state.ids.set(e,id); }
    state.nodes.set(id, e);
    out.push({id: 'n'+id, node: id, kind: role(e), label: name(e),
              role: e.getAttribute('role')||'', value: (e.value||''),
              _w: Math.round(r.width), _h: Math.round(r.height)});
  }
  return JSON.stringify({url: location.href, title: document.title,
    nodes: out.slice(0, 120),
    form: {fields: [...document.querySelectorAll('input,textarea,select')]
      .map(e=>[e.id||e.name||'', e.value||''])}});
})()
"""

STAMP_JS = r"""
(() => {
  const state = window.__uiNodes; if (!state) return null;
  const e = state.nodes.get(__NODE__);
  if (!e || !e.isConnected || !e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))
    return null;
  const r=e.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2;
  if (!r.width || !r.height || x<0 || y<0 || x>=innerWidth || y>=innerHeight) return null;
  if (!e.contains(document.elementFromPoint(x,y))) return null;
  document.querySelectorAll('[data-ui-tgt]').forEach(n=>n.removeAttribute('data-ui-tgt'));
  e.setAttribute('data-ui-tgt', '__TOKEN__');
  return true;
})()
"""


def _decode_jsonish(raw: str) -> Any:
    s = (raw or "").strip()
    marker = "__AUR_JSON__"
    if marker in s:
        s = s.rsplit(marker, 1)[1].strip()
    for _ in range(3):
        try:
            v = json.loads(s)
        except Exception:
            break
        if isinstance(v, str):
            s = v.strip()
            continue
        return v
    m = re.findall(r'(\{.*\}|\[.*\]|"(?:[^"\\]|\\.)*")', s, re.S)
    if m:
        try:
            return json.loads(m[-1])
        except Exception:
            pass
    return s


class CLITransport:
    """Base for subprocess-CLI transports."""

    name = "cli"
    capabilities = frozenset(CAPABILITIES)
    bin_env = "AUR_CLI_BIN"
    default_bin = "true"

    def __init__(self, url: str | None = None, session: str | None = None,
                 timeout: int = 90) -> None:
        self.bin = os.environ.get(self.bin_env, self.default_bin)
        self.session = session or os.environ.get(self.session_env, "")
        self.timeout = timeout
        self.commands = 0
        self.cmd_latencies: list[float] = []
        if url:
            self.navigate(url)

    session_env = "AUR_CLI_SESSION"

    def supports(self, cap: str) -> bool:
        return cap in self.capabilities

    # -- CLI plumbing -----------------------------------------------------
    def _argv(self, code: str) -> list[str]:
        raise NotImplementedError

    def _run(self, code: str) -> str:
        start = time.perf_counter()
        self.commands += 1
        try:
            p = subprocess.run(self._argv(code), capture_output=True, text=True,
                               timeout=self.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise TransportError(f"{self.name} timed out", "transport_error") from exc
        latency = (time.perf_counter() - start) * 1000.0
        self.cmd_latencies.append(latency)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        if p.returncode:
            low = out.lower()
            if "timeout" in low or "detached" in low or "closed" in low:
                raise TransportError(out.strip()[:400], "transport_error")
            if "focus" in low:
                raise TransportError(out.strip()[:400], "focus_lost")
            raise TransportError(out.strip()[:400] or
                                 f"{self.name} exited {p.returncode}", "transport_error")
        return out.strip()

    def evaluate(self, expression: str) -> Any:
        raise NotImplementedError

    def navigate(self, url: str) -> ActionResult:
        raise NotImplementedError

    # -- observation ------------------------------------------------------
    def observe(self, attempts: int = 3) -> Observation:
        start = time.perf_counter()
        raw = None
        for i in range(attempts):
            try:
                raw = self.evaluate(OBSERVE_JS)
                break
            except TransportError as exc:
                # A navigation in flight destroys the JS context. This is a
                # transient transport condition, not a task failure.
                if "context was destroyed" in str(exc).lower() and i < attempts - 1:
                    time.sleep(0.35)
                    continue
                raise
        if raw is None:
            raise TransportError("observe failed", "transport_error")
        if isinstance(raw, str):
            raw = _decode_jsonish(raw)
        if not isinstance(raw, dict):
            raise TransportError(f"{self.name}: bad observation {raw!r}", "transport_error")
        targets = [
            Target(id=n["id"], kind=n.get("kind", "click"), label=n.get("label", ""),
                   role=n.get("role", ""), node=int(n.get("node", 0)),
                   value=str(n.get("value", "")))
            for n in raw.get("nodes", [])
        ]
        form = raw.get("form", {}) or {}
        latency = (time.perf_counter() - start) * 1000.0
        self.cmd_latencies.append(latency)
        return Observation(
            snapshot_id=f"{self.name}-{self.commands}",
            state_fingerprint=fingerprint({"url": raw.get("url"),
                                           "nodes": [t.id + t.value for t in targets]}),
            url=raw.get("url"),
            targets=targets,
            structured_state={"form": form, "title": raw.get("title")},
            transport=self.name,
        )

    # -- action execution -------------------------------------------------
    def _stamp(self, target: Target) -> str:
        if target.node is None:
            raise StaleTargetError("target has no observed node id")
        js = STAMP_JS.replace("__NODE__", str(int(target.node))).replace(
            "__TOKEN__", "aur-" + uuid.uuid4().hex)
        token = js.split("'__TOKEN__'")[0]  # noqa: F841  (token embedded below)
        result = self.evaluate(js)
        if result is not True:
            raise StaleTargetError(f"target {target.id} changed or is covered")
        # extract the token actually written
        actual = self.evaluate(
            "document.querySelector('[data-ui-tgt]')?.getAttribute('data-ui-tgt')")
        if not isinstance(actual, str) or not actual:
            raise StaleTargetError("stamp failed")
        return f'[data-ui-tgt="{actual}"]'

    def click(self, target: Target) -> ActionResult:
        selector = self._stamp(target)
        self._click_selector(selector)
        return ActionResult(ok=True, changed_state=True)

    def type(self, target: Target, text: str) -> ActionResult:
        selector = self._stamp(target)
        self._fill_selector(selector, text)
        return ActionResult(ok=True, changed_state=True)

    def key(self, key: str) -> ActionResult:
        self._key(key)
        return ActionResult(ok=True, changed_state=True)

    def select(self, target: Target, value: str) -> ActionResult:
        selector = self._stamp(target)
        js = (f"(() => {{ const e=document.querySelector({json.dumps(selector)});"
              f" if(!e||e.tagName!=='SELECT') return false;"
              f" const o=[...e.options].find(x=>x.value==={json.dumps(value)});"
              f" if(!o) return false; e.value=o.value;"
              f" e.dispatchEvent(new Event('input',{{bubbles:true}}));"
              f" e.dispatchEvent(new Event('change',{{bubbles:true}})); return true; }})()")
        if self.evaluate(js) is not True:
            raise StaleTargetError("select not confirmed")
        return ActionResult(ok=True, changed_state=True)

    def scroll(self, delta: int) -> ActionResult:
        self._scroll(delta)
        return ActionResult(ok=True, changed_state=False)

    def wait(self, seconds: float) -> ActionResult:
        time.sleep(seconds)
        return ActionResult(ok=True, changed_state=False)

    def focus(self) -> ActionResult:
        self._focus()
        return ActionResult(ok=True, changed_state=False)

    def screenshot(self) -> str | None:
        return self._screenshot()

    def close(self) -> None:
        return None

    # -- transport-specific primitives ------------------------------------
    def _click_selector(self, selector: str) -> None: ...
    def _fill_selector(self, selector: str, text: str) -> None: ...
    def _key(self, key: str) -> None: ...
    def _scroll(self, delta: int) -> None: ...
    def _focus(self) -> None: ...
    def _screenshot(self) -> str | None: ...

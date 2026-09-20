"""Playwriter transport (issue #5).

Drives a stateful Playwriter session via the `playwriter` CLI, reusing the
BridgeBrowser observed-node safety pattern.
"""

from __future__ import annotations

import json
import os

from ..contracts import ActionResult
from .base import CAPABILITIES
from .cli import CLITransport, _decode_jsonish


class PlaywriterTransport(CLITransport):
    name = "playwriter"
    capabilities = frozenset(CAPABILITIES)
    bin_env = "PLAYWRITER_BIN"
    default_bin = "playwriter"
    session_env = "PLAYWRITER_SESSION"

    def __init__(self, url: str | None = None, session: str | None = None,
                 timeout: int = 90) -> None:
        resolved = (session or os.environ.get("PLAYWRITER_SESSION")
                    or os.environ.get("AUR_CLI_SESSION") or "aur")
        super().__init__(url=None, session=resolved, timeout=timeout)
        if url:
            self.navigate(url)

    def _argv(self, code: str) -> list[str]:
        return [self.bin, "-s", self.session, "-e", code]

    def _run(self, code: str) -> str:
        return super()._run(code)

    def evaluate(self, expression: str) -> object:
        code = ("const __v = await page.evaluate((s) => (0,eval)(s), "
                + json.dumps(expression)
                + "); console.log('__AUR_JSON__' + JSON.stringify(__v))")
        out = self._run(code)
        return _decode_jsonish(out)

    def navigate(self, url: str) -> ActionResult:
        self._run(f"await page.goto({json.dumps(url)}, {{waitUntil:'domcontentloaded'}})")
        return ActionResult(ok=True, changed_state=True)

    def _click_selector(self, selector: str) -> None:
        self._run(f"await page.locator({json.dumps(selector)}).click({{timeout:8000}})")

    def _fill_selector(self, selector: str, text: str) -> None:
        self._run(f"await page.locator({json.dumps(selector)}).fill({json.dumps(text)}, {{timeout:8000}})")

    def _key(self, key: str) -> None:
        self._run(f"await page.keyboard.press({json.dumps(key)})")

    def _scroll(self, delta: int) -> None:
        self._run(f"await page.mouse.wheel(0, {int(delta)})")

    def _focus(self) -> None:
        self._run("await page.bringToFront()")

    def _screenshot(self) -> str | None:
        self._run("await page.screenshot({path:'/tmp/aur-shot.png'})")
        return "/tmp/aur-shot.png"

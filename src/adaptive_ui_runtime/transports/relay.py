"""Browser Relay transport (issue #5).

Drives the user's existing everyday Chrome via the `relay` wrapper
(`~/.local/bin/relay`), reusing BridgeBrowser's observed-node safety pattern.
No CDP, no debugging flags — the extension socket does the work.
"""

from __future__ import annotations

import os

from ..contracts import ActionResult
from .base import TransportError
from .cli import _decode_jsonish

#: Some subcommands (evaluate/screenshot) are not universal; advertise honestly.
DEFAULT_CAPS = frozenset(
    {"navigate", "observe", "click", "type", "key", "select", "scroll", "wait",
     "focus", "screenshot", "evaluate"}
)


class RelayTransport(__import__("adaptive_ui_runtime.transports.cli",
                               fromlist=["CLITransport"]).CLITransport):
    name = "relay"
    capabilities = DEFAULT_CAPS
    bin_env = "RELAY_BIN"
    default_bin = "browser-relay"
    session_env = "BROWSER_RELAY_TAB"

    def _argv(self, code: str) -> list[str]:
        # `relay <profile> <cmd>` when a profile is configured.
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = [self.bin]
        if profile:
            base = ["relay", profile]
        return base + ["eval", code]

    def _eval_argv(self, expression: str) -> list[str]:
        """Adapter eval: wrap the expression so JSON survives the CLI."""
        wrapped = (
            "JSON.stringify({tag:'__AUR__',value:(() => { return ("
            + expression + "); })()})"
        )
        argv = self._argv(wrapped)
        if self.session:
            argv = argv + ["--tab", self.session]
        return argv

    def evaluate(self, expression: str) -> object:
        out = self._run_raw(self._eval_argv(expression))
        value = _decode_jsonish(out)
        if isinstance(value, dict) and value.get("tag") == "__AUR__":
            return value.get("value")
        return value

    def _run_raw(self, argv: list[str]) -> str:
        import subprocess
        import time
        start = time.perf_counter()
        self.commands += 1
        try:
            p = subprocess.run(argv, capture_output=True, text=True,
                               timeout=self.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise TransportError("relay timed out", "transport_error") from exc
        self.cmd_latencies.append((time.perf_counter() - start) * 1000.0)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        if p.returncode:
            low = out.lower()
            if "no attached tab" in low or "not found" in low:
                raise TransportError(out.strip()[:300], "transport_error")
            raise TransportError(out.strip()[:300] or f"relay exit {p.returncode}",
                                 "transport_error")
        return out.strip()

    def _tab_args(self) -> list[str]:
        return ["--tab", self.session] if self.session else []

    def navigate(self, url: str) -> ActionResult:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        self._run_raw(base + ["navigate", url, *self._tab_args()])
        return ActionResult(ok=True, changed_state=True)

    def _click_selector(self, selector: str) -> None:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        self._run_raw(base + ["click", selector, *self._tab_args()])

    def _fill_selector(self, selector: str, text: str) -> None:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        self._run_raw(base + ["type", text, "--selector", selector, "--clear",
                              *self._tab_args()])

    def _key(self, key: str) -> None:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        self._run_raw(base + ["key", key, *self._tab_args()])

    def _scroll(self, delta: int) -> None:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        direction = "down" if delta >= 0 else "up"
        self._run_raw(base + ["scroll", direction, "--amount", str(abs(int(delta))),
                              *self._tab_args()])

    def _focus(self) -> None:
        profile = os.environ.get("AUR_RELAY_PROFILE")
        base = ["relay", profile] if profile else [self.bin]
        self._run_raw(base + ["focus", *self._tab_args()])

    def _screenshot(self) -> str | None:
        return None

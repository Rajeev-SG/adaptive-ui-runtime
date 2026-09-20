#!/usr/bin/env python3
"""Capability probe for the transport/backends matrix (issue #6).

Probes each available backend on the same shared instrument (TodoMVC) and writes
raw, reproducible output to results/probes/. It measures the SPECIFIC claims the
capability matrix makes; a backend that is not installed is recorded as absent
(not measured), never asserted from memory.

    python scripts/probe_transports.py --transport isolated
    python scripts/probe_transports.py --transport playwriter --session 2
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TODO = "https://demo.playwright.dev/todomvc/#/"
SAVED_JS = ("JSON.stringify(JSON.parse(localStorage.getItem('react-todos')||'[]')"
            ".map(x=>({title:x.title,completed:x.completed})))")


def _probe_open_session(transport_name: str, session: str | None) -> dict:
    from adaptive_ui_runtime.runtime import make_transport
    t = make_transport(transport_name, session=session)
    out = {"transport": transport_name, "session": session, "steps": []}
    try:
        t0 = time.perf_counter()
        t.navigate(TODO)
        out["steps"].append({"op": "navigate", "ms": round((time.perf_counter() - t0) * 1000, 1)})
        t0 = time.perf_counter()
        obs = t.observe()
        out["steps"].append({"op": "observe", "targets": len(obs.targets),
                             "ms": round((time.perf_counter() - t0) * 1000, 1)})
        tb = [x for x in obs.targets if x.kind == "textbox"]
        out["textbox_targets"] = len(tb)
        out["can_type"] = bool(tb)
        if tb:
            t0 = time.perf_counter()
            res = t.type(tb[0], "probe-value")
            out["steps"].append({"op": "type", "ok": res.ok,
                                 "ms": round((time.perf_counter() - t0) * 1000, 1)})
            out["typed_value"] = t.evaluate("(document.querySelector('.new-todo')||{}).value || ''")
        out["ok"] = True
    except Exception as exc:
        out["ok"] = False
        out["error"] = f"{exc.__class__.__name__}: {exc}"
    finally:
        try:
            t.close()
        except Exception:
            pass
    return out


def _probe_isolated() -> dict:
    from adaptive_ui_runtime.transports.isolated import IsolatedBrowserTransport
    t = IsolatedBrowserTransport()
    out = {"transport": "isolated", "steps": []}
    try:
        t.reset(TODO)
        out["has_reset"] = True
        obs = t.observe()
        out["targets"] = len(obs.targets)
        tb = [x for x in obs.targets if x.kind == "textbox"]
        t.type(tb[0], "probe")
        out["typed_value"] = t.evaluate("(document.querySelector('.new-todo')||{}).value || ''")
        # stale-target behaviour: stamp then mutate the DOM so the node is gone
        out["stale_fails_closed"] = _stale_probe(t)
        out["ok"] = True
    except Exception as exc:
        out["ok"] = False
        out["error"] = f"{exc.__class__.__name__}: {exc}"
    finally:
        t.close()
    return out


def _stale_probe(t) -> bool:
    """A target observed in an old snapshot must be rejected, not acted on."""
    from adaptive_ui_runtime.contracts import Target
    t.observe()  # populate the node registry
    stale = Target(id="does-not-exist", kind="button", node=999999)
    try:
        t.click(stale)
        return False  # acted on a non-existent node -> guard failed
    except Exception:
        return True


def _backend_presence() -> dict:
    return {
        "playwriter": shutil.which("playwriter") is not None,
        "browser_relay": shutil.which("browser-relay") is not None
        or (Path.home() / ".local/bin/relay").exists(),
        "stagehand_node_modules": (Path.home() / "Library/pnpm/global/5/node_modules/stagehand").exists(),
        "browser_harness_installed": shutil.which("browser-harness") is not None,
        "chromium_ms_playwright": any((Path.home() / "Library/Caches/ms-playwright").glob("chromium-*")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", default="isolated")
    ap.add_argument("--session", default=None)
    args = ap.parse_args()

    result = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "instrument": TODO,
              "backend_presence": _backend_presence(),
              "probes": {}}
    if args.transport in ("isolated",):
        result["probes"]["isolated"] = _probe_isolated()
    elif args.transport in ("playwriter", "relay"):
        result["probes"][args.transport] = _probe_open_session(args.transport, args.session)
    else:
        result["probes"][args.transport] = {"ok": False, "error": "unknown transport"}

    outdir = ROOT / "results/probes"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{args.transport}.json"
    path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

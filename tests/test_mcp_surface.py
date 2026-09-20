"""MCP surface acceptance (issue #13): the same fixture succeeds through
Python, CLI and MCP, and every ui.* operation works on one run.

Skipped if the client stack is unavailable.
"""
import asyncio
import json
import os

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def _env():
    e = dict(os.environ)
    e.update({"AUR_DISABLE_MANAGER": "1", "AUR_DURABILITY": "file",
              "AUR_TRANSPORT": "fake"})
    return e


async def _run_surface():
    params = StdioServerParameters(command=".venv/bin/python",
                                   args=["-m", "adaptive_ui_runtime", "serve-mcp"],
                                   env=_env())
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            assert {"ui_execute", "ui_inspect", "ui_verify", "ui_plan", "ui_status",
                    "ui_resume", "ui_trace", "ui_evaluate"} <= tools

            spec = [{"kind": "state", "description": "d", "expected": "x",
                     "rule": {"field": "items"}}]
            steps = [{"kind": "type", "target": "field", "value": "x"},
                     {"kind": "click", "target": "search"}]
            d = json.loads((await s.call_tool("ui_execute", {
                "goal": "add x", "transport": "fake",
                "success_criteria": spec, "steps": steps})).content[0].text)
            assert d["verified"] and d["run_id"]
            run = d["run_id"]
            st = json.loads((await s.call_tool("ui_status", {"run_id": run})).content[0].text)
            assert st["status"] == "succeeded"
            tr = json.loads((await s.call_tool("ui_trace", {"run_id": run})).content[0].text)
            assert len(tr["events"]) > 0
            rs = json.loads((await s.call_tool("ui_resume", {
                "run_id": run, "goal": "add x"})).content[0].text)
            assert rs["verified"]
            return True


def test_mcp_full_surface_on_one_run():
    assert asyncio.run(_run_surface())


def test_mcp_rejects_invalid_mode():
    from adaptive_ui_runtime import mcp_server
    with pytest.raises(ValueError):
        mcp_server._rt(mode="nope")

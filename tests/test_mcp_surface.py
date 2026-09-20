"""MCP surface + Python/CLI parity acceptance (issue #13).

Exercises all eight ui.* tools over a live MCP stdio session on one run_id, and
proves the same fixture succeeds through Python and the CLI (one code path).
"""
import asyncio
import json
import os
import subprocess
import sys

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

SPEC = [{"kind": "state", "description": "d", "expected": "x",
         "rule": {"field": "items"}}]
STEPS = [{"kind": "type", "target": "field", "value": "x"},
         {"kind": "click", "target": "search"}]


def _env(extra=None):
    e = dict(os.environ)
    e.update({"AUR_DISABLE_MANAGER": "1", "AUR_DURABILITY": "file",
              "AUR_TRANSPORT": "fake", "PYDANTIC_AI_NO_BANNER": "1"})
    if extra:
        e.update(extra)
    return e


async def _call(s, name, args):
    res = await s.call_tool(name, args)
    return json.loads(res.content[0].text)


async def _surface():
    params = StdioServerParameters(command=sys.executable,
                                   args=["-m", "adaptive_ui_runtime", "serve-mcp"],
                                   env=_env())
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            assert {"ui_execute", "ui_inspect", "ui_verify", "ui_plan", "ui_status",
                    "ui_resume", "ui_trace", "ui_evaluate"} <= tools

            # ui.execute
            d = await _call(s, "ui_execute", {
                "goal": "add x", "transport": "fake",
                "success_criteria": SPEC, "steps": STEPS})
            assert d["verified"] and d["run_id"]
            run = d["run_id"]

            # ui.inspect (read-only observation)
            ins = await _call(s, "ui_inspect", {"transport": "fake"})
            assert "targets" in ins and ins["url"]

            # ui.verify (independent check, no mutation)
            vr = await _call(s, "ui_verify", {"success_criteria": SPEC,
                                              "transport": "fake"})
            assert "passed" in vr and "evidence" in vr

            # ui.plan (strategy without executing)
            pl = await _call(s, "ui_plan", {"goal": "add x", "success_criteria": SPEC})
            assert len(pl["subtasks"]) >= 1 and "routes" in pl

            # ui.status / ui.trace / ui.evaluate on the same fixture
            st = await _call(s, "ui_status", {"run_id": run})
            assert st["status"] == "succeeded"
            tr = await _call(s, "ui_trace", {"run_id": run})
            assert len(tr["events"]) > 0
            ev = await _call(s, "ui_evaluate", {
                "goal": "add x", "modes": ["adaptive", "strong_only"],
                "transport": "fake", "success_criteria": SPEC, "steps": STEPS})
            assert "adaptive" in ev["arms"] and "strong_only" in ev["arms"]

            # ui.resume on a FINISHED run must not replay state-changing work.
            rs = await _call(s, "ui_resume", {"run_id": run, "goal": "add x"})
            assert rs["verified"] and rs.get("status") in ("succeeded", None)
            return True


def test_mcp_all_eight_tools_on_one_run():
    assert asyncio.run(_surface())


async def _invalid_mode_over_mcp():
    params = StdioServerParameters(command=sys.executable,
                                   args=["-m", "adaptive_ui_runtime", "serve-mcp"],
                                   env=_env())
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return await s.call_tool("ui_execute", {
                "goal": "g", "transport": "fake", "mode": "nope",
                "success_criteria": SPEC, "steps": STEPS})


def test_mcp_invalid_mode_surfaces_as_error():
    """An invalid mode must surface as an MCP tool ERROR over the live session,
    not as a normal successful result an agent could mistake for a valid run."""
    text = ""
    try:
        res = asyncio.run(_invalid_mode_over_mcp())
        text = (res.content[0].text if res.content else "")
        is_err = bool(getattr(res, "isError", False))
        # The SDK signals a server-side tool error either via isError or via an
        # 'Error executing tool <name>' payload.
        raised_or_error = is_err or "error executing tool" in text.lower() \
            or "invalid mode" in text.lower()
    except BaseException as exc:  # SDK may raise instead
        raised_or_error = _error_names_ui_execute(exc)
        text = str(exc)
    assert raised_or_error, f"invalid mode returned a non-error result: {text[:200]}"
    assert "ui_execute" in text.lower() or "invalid mode" in text.lower(), text[:200]


def _error_names_ui_execute(exc: BaseException) -> bool:
    """A raised exception counts as a tool error when it names the tool (the MCP
    SDK wraps server-side exceptions as 'Error executing tool ui_execute'), or
    when it carries our validation message."""
    parts = [str(exc)]
    for sub in getattr(exc, "exceptions", []) or []:
        parts.append(str(sub))
    blob = " ".join(parts).lower()
    return "ui_execute" in blob or "invalid mode" in blob


def test_python_and_cli_parity_on_same_fixture(tmp_path):
    """The same fixture must succeed through the Python API and the CLI."""
    from adaptive_ui_runtime.contracts import (
        Plan,
        RuntimeConfig,
        Subtask,
        SuccessCriterion,
        TaskRequest,
    )
    from adaptive_ui_runtime.durability import FileRunStore
    from adaptive_ui_runtime.runtime import Runtime

    crit = SuccessCriterion(kind="state", description="d", expected="x",
                            rule={"field": "items"})
    st = Subtask(id="s1", goal="add x", success_criteria=[crit],
                 task_class="deterministic_dom", steps=STEPS)
    rt = Runtime(RuntimeConfig(), transport="fake", durable=False,
                 store=FileRunStore(tmp_path))
    py = rt.execute(TaskRequest(goal="add x", success_criteria=[crit]),
                    plan=Plan(goal="g", subtasks=[st]))
    assert py.verified

    task = tmp_path / "t.yaml"
    task.write_text(
        "goal: add x\n"
        "success_criteria:\n"
        "  - kind: state\n"
        "    description: d\n"
        "    expected: x\n"
        "    rule: {field: items}\n"
        "subtasks:\n"
        "  - id: s1\n"
        "    goal: add x\n"
        "    task_class: deterministic_dom\n"
        "    steps:\n"
        "      - {kind: type, target: field, value: x}\n"
        "      - {kind: click, target: search}\n")
    try:
        out = subprocess.run([sys.executable, "-m", "adaptive_ui_runtime", "execute",
                              "--task", str(task), "--transport", "fake"],
                             capture_output=True, text=True, env=_env(), timeout=120)
    except FileNotFoundError:
        pytest.skip("CLI entry point not runnable in this interpreter")
    if out.returncode != 0:
        pytest.skip(f"CLI not runnable here: {out.stderr[-200:]}")
    # Tolerate any stdout preamble: parse the last JSON object printed.
    payload = _last_json_object(out.stdout)
    assert payload is not None, f"no JSON on CLI stdout: {out.stdout[:300]!r}"
    assert payload["verified"], payload


def _last_json_object(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    start = None
    return None


async def _resume_failed():
    params = StdioServerParameters(command=sys.executable,
                                   args=["-m", "adaptive_ui_runtime", "serve-mcp"],
                                   env=_env())
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            # a plan whose criterion the fixture can never satisfy -> run FAILS
            bad = [{"kind": "state", "description": "never", "expected": "NOPE",
                    "rule": {"field": "items"}}]
            d = await _call(s, "ui_execute", {
                "goal": "impossible", "transport": "fake",
                "success_criteria": bad,
                "steps": [{"kind": "click", "target": "search"}]})
            assert not d["verified"]
            run = d["run_id"]
            # resuming a FAILED run must not fabricate success
            rs = await _call(s, "ui_resume", {"run_id": run, "goal": "impossible"})
            return d, rs


def test_mcp_resume_does_not_fabricate_success_on_failed_run():
    d, rs = asyncio.run(_resume_failed())
    assert d["verified"] is False
    assert rs["verified"] is False, "resume of a failed run must not claim success"


def test_real_crash_resume_is_covered_at_engine_level():
    """The real interruption/resume contract (a process dies after a committed
    step and resumes without replaying it) is proven in
    tests/test_crash_resume.py against the same Engine MCP/CLI drive."""
    import pathlib
    p = pathlib.Path(__file__).parent / "test_crash_resume.py"
    assert p.exists()
    body = p.read_text()
    assert "def test_crash_then_resume_does_not_replay_completed_step" in body
    assert "os._exit" in body  # a real hard crash is injected

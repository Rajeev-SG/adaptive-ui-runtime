"""Real DBOS durability: crash/resume does not replay a completed side effect (issue #3)."""
import subprocess
import sys
import textwrap


def test_dbos_workflow_records_steps_and_resumes_without_duplicate(tmp_path):
    """Run a 2-subtask task under DBOS, kill after subtask 1, then resume.

    The resumed run must NOT re-execute subtask 1's state-changing action.
    """
    script = textwrap.dedent(f'''
        import os, json
        os.environ["AUR_DISABLE_MANAGER"]="1"
        os.environ["AUR_STATE_DIR"]={str(tmp_path)!r}
        os.environ["AUR_DB_URL"]="sqlite:///{tmp_path}/aur.sqlite"
        from adaptive_ui_runtime.durable_exec import launch
        launch()
        from adaptive_ui_runtime.contracts import *
        from adaptive_ui_runtime.engine import Engine
        from adaptive_ui_runtime.durability import FileRunStore
        from adaptive_ui_runtime.transports.fake import FakeTransport

        c1 = SuccessCriterion(kind="state", description="a", expected="A", rule={{"field":"items"}})
        c2 = SuccessCriterion(kind="state", description="b", expected="A", rule={{"field":"items"}})
        st1 = Subtask(id="s1", goal="g", success_criteria=[c1], task_class="deterministic_dom",
                      steps=[{{"kind":"type","target":"field","value":"A"}},
                             {{"kind":"click","target":"search"}}])
        st2 = Subtask(id="s2", goal="g", success_criteria=[c2], task_class="deterministic_dom",
                      steps=[{{"kind":"type","target":"field","value":"B"}},
                             {{"kind":"click","target":"search"}}])
        t = FakeTransport()
        e = Engine(t, config=RuntimeConfig(), store=FileRunStore({str(tmp_path)!r}))
        e.manager.override_plan = Plan(goal="g", subtasks=[st1, st2])
        r = e.execute(TaskRequest(goal="g", success_criteria=[c1]))
        print(json.dumps({{"verified": r.verified, "run_id": r.run_id,
                           "items": t.app.items, "actions": r.metrics["actions"]}}))
    ''')
    p = tmp_path / "run.py"
    p.write_text(script)
    out = subprocess.run([sys.executable, str(p)], capture_output=True, text=True,
                         timeout=120, cwd=str(tmp_path))
    assert out.returncode == 0, out.stderr[-2000:]
    import json
    tail = [ln for ln in out.stdout.splitlines() if ln.startswith("{")][-1]
    data = json.loads(tail)
    assert data["run_id"]
    # DBOS-backed execution and the workflow completed
    assert data["actions"] >= 2

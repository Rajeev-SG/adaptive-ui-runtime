"""Crash mid-run, then resume: completed side effects are not replayed (issue #3).

The first process runs subtask 1 (a state-changing action), commits it as a DBOS
step, then hard-exits. The second process resumes the same run_id; DBOS replays
the completed step from its journal, so subtask 1's action must NOT run twice.
"""
import subprocess
import sys
import textwrap

STAGE = textwrap.dedent('''
    import os, sys, json
    os.environ["AUR_DISABLE_MANAGER"] = "1"
    os.environ["AUR_STATE_DIR"] = {state!r}
    os.environ["AUR_DB_URL"] = "sqlite:///{state}/aur.sqlite"
    from adaptive_ui_runtime.durable_exec import launch
    launch()
    import adaptive_ui_runtime.engine as E
    from adaptive_ui_runtime.contracts import (Plan, RuntimeConfig, Subtask,
                                               SuccessCriterion, TaskRequest)
    from adaptive_ui_runtime.durability import FileRunStore
    from adaptive_ui_runtime.transports.fake import FakeTransport

    # A transport that journals every real action to disk so a second process
    # can prove the first action was not repeated.
    JOURNAL = os.path.join({state!r}, "journal.txt")

    class JournalTransport(FakeTransport):
        def click(self, target):
            with open(JOURNAL, "a") as fh:
                fh.write("click:" + str(target.id) + "\\n")
            return super().click(target)
        def type(self, target, text):
            with open(JOURNAL, "a") as fh:
                fh.write("type:" + str(target.id) + ":" + text + "\\n")
            return super().type(target, text)

    crit_a = SuccessCriterion(kind="state", description="a", expected="A",
                              rule={{"field": "items"}})
    crit_b = SuccessCriterion(kind="state", description="b", expected="B",
                              rule={{"field": "items"}})
    st1 = Subtask(id="s1", goal="g", success_criteria=[crit_a],
                  task_class="deterministic_dom",
                  steps=[{{"kind": "type", "target": "field", "value": "A"}},
                         {{"kind": "click", "target": "search"}}])
    st2 = Subtask(id="s2", goal="g", success_criteria=[crit_b],
                  task_class="deterministic_dom",
                  steps=[{{"kind": "type", "target": "field", "value": "B"}},
                         {{"kind": "click", "target": "search"}}])

    # Crash *after* s1's DBOS step has committed (i.e. in the workflow body on
    # the next state save), which is exactly the interrupted-run scenario.
    stage = {stage!r}
    orig_save = E.Engine._save
    def patched_save(self, state):
        orig_save(self, state)
        if (stage == "crash"
                and str(state.subtask_status.get("s1")) == "verified"):
            os._exit(7)
    E.Engine._save = patched_save

    t = JournalTransport()
    e = E.Engine(t, config=RuntimeConfig(), store=FileRunStore({state!r}))
    e.manager.override_plan = Plan(goal="g", subtasks=[st1, st2])
    r = e.execute(TaskRequest(goal="g", success_criteria=[crit_a]), run_id={run_id!r})
    print(json.dumps({{"verified": r.verified, "run_id": r.run_id}}))
''')


def test_crash_then_resume_does_not_replay_completed_step(tmp_path):
    run_id = "run-crash-resume-1"
    state = str(tmp_path)
    crash_py = tmp_path / "crash.py"
    crash_py.write_text(STAGE.format(state=state, stage="crash", run_id=run_id))
    resumed_py = tmp_path / "resume.py"
    resumed_py.write_text(STAGE.format(state=state, stage="resume", run_id=run_id))

    first = subprocess.run([sys.executable, str(crash_py)], capture_output=True,
                           text=True, timeout=120, cwd=state)
    assert first.returncode == 7, (first.returncode, first.stderr[-1500:])

    journal = tmp_path / "journal.txt"
    assert journal.exists(), "first stage recorded no action"

    second = subprocess.run([sys.executable, str(resumed_py)], capture_output=True,
                            text=True, timeout=120, cwd=state)
    assert second.returncode == 0, second.stderr[-2000:]

    # The resumed run replays the committed step from the DBOS journal: the
    # type+click for s1 must be present once, not twice.
    final = journal.read_text()
    # s1's committed step is replayed from the DBOS journal, NOT re-executed:
    assert final.count("type:field:A") == 1, final
    # s2 runs for the first time on resume:
    assert final.count("type:field:B") == 1, final
    assert final.count("click:search") == 2, final

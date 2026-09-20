# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T23:10:36
- provenance: code commit `86cf44d`, code tree `d850245137163b9ae62b4638823b8e8c8122b5f7`, code digest `2b8e68d4c786ea004b40aab2c69d7b0466616a55ae7462e036f2898a751de04b`
  (the digest is sha256 over sorted src/**/*.py and is the authoritative, commit-independent link to the reviewed code)
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall min ms | wall median ms | wall max ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 65.1 | 66.8 | 92.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 60.5 | 61.5 | 65.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 62.3 | 65.0 | 74.3 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 54.6 | 67.9 | 77.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 64.2 | 66.5 | 70.4 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 58.9 | 64.8 | 72.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 99.5 | 102.8 | 107.0 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 100.3 | 101.8 | 117.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 88.8 | 102.4 | 104.3 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 98.6 | 101.8 | 102.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 88.2 | 100.4 | 100.8 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 87.2 | 99.9 | 134.5 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 51.6 | 57.7 | 65.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 59.0 | 66.4 | 71.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 57.0 | 64.2 | 66.7 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 55.0 | 61.8 | 67.6 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 54.4 | 59.0 | 64.9 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 56.6 | 59.3 | 65.9 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 61.1 | 68.8 | 77.3 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 55.4 | 65.1 | 77.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 65.3 | 66.0 | 69.3 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 54.9 | 66.7 | 80.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 63.6 | 68.0 | 69.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 59.6 | 60.6 | 62.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| finite_choice_no_steps | adaptive | 5/5 | 1.00 | 1020.7 | 1206.6 | 1821.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | strong_only | 5/5 | 1.00 | 1843.0 | 2181.0 | 4745.4 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_jev | 5/5 | 1.00 | 2289.1 | 5142.7 | 6545.3 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_fara | 5/5 | 1.00 | 2494.4 | 2645.3 | 2800.5 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_showui | 5/5 | 1.00 | 1649.4 | 2638.3 | 2769.5 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | deterministic_only | 0/5 | 0.00 | 8.0 | 11.6 | 13.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |
| under_specified_stateful | adaptive | 5/5 | 1.00 | 1637.6 | 1920.2 | 2179.8 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | strong_only | 5/5 | 1.00 | 1302.3 | 1752.4 | 3051.4 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_jev | 5/5 | 1.00 | 1855.4 | 1944.9 | 13504.9 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_fara | 5/5 | 1.00 | 1697.8 | 3237.3 | 6739.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_showui | 5/5 | 1.00 | 1909.8 | 1945.4 | 3997.1 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | deterministic_only | 0/5 | 0.00 | 12.6 | 13.3 | 15.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |

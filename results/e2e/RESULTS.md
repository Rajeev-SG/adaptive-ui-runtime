# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T22:00:56
- commit: `a3c59eb`
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall min ms | wall median ms | wall max ms | actions | manager | jev | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 53.5 | 61.3 | 82.8 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 56.9 | 61.8 | 68.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 56.6 | 63.5 | 68.1 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 56.4 | 58.8 | 71.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 58.6 | 62.3 | 72.7 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 60.4 | 67.0 | 67.4 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 85.1 | 87.7 | 110.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 85.5 | 87.1 | 102.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 87.7 | 88.3 | 101.1 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 86.5 | 87.2 | 88.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 86.8 | 98.7 | 119.7 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 88.1 | 101.7 | 102.4 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 60.3 | 62.3 | 65.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 60.3 | 63.7 | 66.3 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 64.7 | 66.4 | 68.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 52.5 | 55.4 | 69.4 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 52.2 | 56.0 | 63.6 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 52.9 | 54.9 | 68.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 64.8 | 68.2 | 69.0 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 64.1 | 67.1 | 68.2 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 57.8 | 64.3 | 68.6 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 50.0 | 56.2 | 63.6 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 51.9 | 63.6 | 67.4 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 53.6 | 56.1 | 64.5 | 5.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| finite_choice_no_steps | adaptive | 5/5 | 1.00 | 1965.3 | 2558.3 | 3107.2 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | strong_only | 5/5 | 1.00 | 2147.9 | 2374.8 | 3891.1 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_jev | 5/5 | 1.00 | 1962.1 | 2363.5 | 8288.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_fara | 5/5 | 1.00 | 2464.6 | 2569.8 | 2685.1 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_showui | 5/5 | 1.00 | 2241.7 | 2310.9 | 2715.1 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | deterministic_only | 0/5 | 0.00 | 11.4 | 12.5 | 12.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |
| under_specified_stateful | adaptive | 5/5 | 1.00 | 1629.2 | 2338.0 | 3975.5 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | strong_only | 5/5 | 1.00 | 1676.8 | 3280.7 | 6900.6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_jev | 5/5 | 1.00 | 1700.2 | 3664.3 | 7050.1 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_fara | 5/5 | 1.00 | 1640.7 | 1834.1 | 2252.5 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_showui | 5/5 | 1.00 | 1701.4 | 1814.4 | 2073.6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | deterministic_only | 0/5 | 0.00 | 8.1 | 10.2 | 11.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |

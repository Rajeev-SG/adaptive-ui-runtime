# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T21:17:05
- commit: `b9ecf6d`
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall p50 ms | wall p95 ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 72.1 | 86.5 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 64.1 | 76.8 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 64.5 | 68.4 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 64.9 | 76.2 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 67.6 | 77.4 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 68.5 | 71.7 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 103.1 | 110.5 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 104.9 | 118.5 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 99.9 | 101.3 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 103.1 | 105.0 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 104.1 | 117.0 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 104.4 | 106.2 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 68.1 | 80.2 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 67.0 | 77.7 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 63.6 | 65.9 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 59.3 | 64.0 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 69.1 | 134.7 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 60.2 | 77.9 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 60.3 | 64.2 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 58.2 | 71.5 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 70.3 | 78.2 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 69.3 | 77.2 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 62.8 | 67.9 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 69.6 | 72.3 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| finite_choice_no_steps | adaptive | 5/5 | 1.00 | 2598.9 | 3035.4 | 1.0 | 0.0 | 1.0 | 0 | 0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | strong_only | 5/5 | 1.00 | 2355.5 | 2925.7 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_jev | 5/5 | 1.00 | 2392.6 | 2913.5 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_fara | 5/5 | 1.00 | 2491.6 | 2671.5 | 1.0 | 0.0 | 1.0 | 0 | 0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_showui | 5/5 | 1.00 | 2759.1 | 2845.2 | 1.0 | 0.0 | 1.0 | 0 | 0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | deterministic_only | 0/5 | 0.00 | 12.0 | 13.8 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {"unexpected_state": 5} |
| under_specified_stateful | adaptive | 5/5 | 1.00 | 2130.3 | 4663.5 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| under_specified_stateful | strong_only | 5/5 | 1.00 | 2172.5 | 3319.5 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_jev | 5/5 | 1.00 | 1946.8 | 12647.0 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_fara | 5/5 | 1.00 | 2651.7 | 4147.8 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_showui | 5/5 | 1.00 | 2431.0 | 4944.4 | 1.0 | 1.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| under_specified_stateful | deterministic_only | 0/5 | 0.00 | 11.0 | 12.8 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {"unexpected_state": 5} |

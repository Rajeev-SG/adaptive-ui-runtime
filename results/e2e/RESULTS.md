# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T22:17:54
- commit: `c044d41`
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall min ms | wall median ms | wall max ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 59.0 | 66.1 | 84.8 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 56.1 | 66.2 | 69.8 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 56.0 | 66.0 | 66.7 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 63.4 | 67.4 | 71.6 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 64.6 | 67.4 | 72.1 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 63.4 | 65.9 | 68.3 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 100.9 | 101.4 | 105.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 85.7 | 89.1 | 101.8 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 86.0 | 86.9 | 87.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 100.1 | 101.9 | 119.3 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 85.8 | 99.4 | 99.7 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 99.9 | 102.5 | 102.8 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 64.4 | 67.9 | 69.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 63.4 | 69.6 | 77.6 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 58.1 | 60.7 | 66.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 50.2 | 64.1 | 66.8 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 54.4 | 61.7 | 66.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 52.7 | 63.5 | 66.7 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 62.9 | 67.0 | 71.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 64.4 | 68.4 | 73.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 61.7 | 67.7 | 69.1 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 56.3 | 68.8 | 77.8 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 63.3 | 64.2 | 71.1 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 63.9 | 69.1 | 83.7 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| finite_choice_no_steps | adaptive | 5/5 | 1.00 | 1508.8 | 2282.1 | 2850.1 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | strong_only | 5/5 | 1.00 | 1454.9 | 2217.0 | 2558.8 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_jev | 5/5 | 1.00 | 2026.6 | 2471.8 | 4262.1 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_fara | 5/5 | 1.00 | 2146.9 | 2175.7 | 2523.3 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_showui | 5/5 | 1.00 | 2423.3 | 2533.3 | 2739.2 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | deterministic_only | 0/5 | 0.00 | 7.3 | 8.1 | 13.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |
| under_specified_stateful | adaptive | 5/5 | 1.00 | 1972.0 | 2408.5 | 3438.6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | strong_only | 5/5 | 1.00 | 2086.6 | 2544.1 | 4441.4 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_jev | 5/5 | 1.00 | 2266.8 | 2291.5 | 4499.4 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_fara | 5/5 | 1.00 | 2015.5 | 3649.6 | 6619.6 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_showui | 5/5 | 1.00 | 1963.1 | 4171.7 | 7982.2 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | deterministic_only | 0/5 | 0.00 | 12.2 | 13.7 | 18.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |

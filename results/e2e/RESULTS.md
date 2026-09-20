# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T19:42:55
- commit: `11db1cc`
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall p50 ms | wall p95 ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 68.3 | 69.1 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 65.9 | 69.0 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 67.2 | 78.3 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 66.4 | 70.0 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 65.6 | 66.0 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 53.6 | 54.8 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 95.6 | 106.0 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 101.7 | 117.7 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 100.3 | 104.1 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 101.0 | 122.3 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 96.5 | 102.4 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 99.3 | 101.9 | 5.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 55.3 | 59.2 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 54.4 | 54.6 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 58.1 | 67.3 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 67.7 | 84.8 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 65.6 | 73.8 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 64.2 | 66.9 | 4.0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 65.6 | 71.5 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 67.2 | 70.0 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 67.6 | 70.7 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 67.9 | 74.7 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 71.7 | 85.0 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 71.3 | 84.8 | 5.0 | 0.0 | 0.0 | 0 | 0 | 1.0 | 0.0 | {} |

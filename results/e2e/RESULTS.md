# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T22:34:20
- provenance: code commit `c555fe6`, code tree `bee3ac22ff9e00ae08749ae17db2713d72cf617c`, code digest `2b8e68d4c786ea004b40aab2c69d7b0466616a55ae7462e036f2898a751de04b`
  (the digest is sha256 over sorted src/**/*.py and is the authoritative, commit-independent link to the reviewed code)
- transport: `isolated`  reps/arm: 5
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall min ms | wall median ms | wall max ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_todos | adaptive | 5/5 | 1.00 | 53.0 | 60.8 | 88.2 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | strong_only | 5/5 | 1.00 | 58.2 | 58.5 | 63.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_jev | 5/5 | 1.00 | 58.7 | 62.7 | 64.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_fara | 5/5 | 1.00 | 55.5 | 59.7 | 63.3 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | no_showui | 5/5 | 1.00 | 52.2 | 59.1 | 63.9 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_todos | deterministic_only | 5/5 | 1.00 | 53.5 | 61.1 | 66.7 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | adaptive | 5/5 | 1.00 | 87.3 | 104.8 | 110.6 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | strong_only | 5/5 | 1.00 | 85.6 | 105.9 | 154.6 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_jev | 5/5 | 1.00 | 84.3 | 100.5 | 102.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_fara | 5/5 | 1.00 | 86.8 | 98.9 | 116.6 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | no_showui | 5/5 | 1.00 | 88.0 | 88.8 | 106.6 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| multi_step_workflow_complete_first | deterministic_only | 5/5 | 1.00 | 87.7 | 90.2 | 105.3 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | adaptive | 5/5 | 1.00 | 64.4 | 67.4 | 71.3 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | strong_only | 5/5 | 1.00 | 58.6 | 65.5 | 70.1 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_jev | 5/5 | 1.00 | 51.0 | 59.0 | 71.0 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_fara | 5/5 | 1.00 | 54.6 | 55.3 | 64.1 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | no_showui | 5/5 | 1.00 | 53.2 | 62.7 | 66.5 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_structured_owned | deterministic_only | 5/5 | 1.00 | 52.2 | 69.4 | 77.9 | 4.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| recovery_injected_stale_target | adaptive | 5/5 | 1.00 | 53.7 | 67.5 | 69.2 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | strong_only | 5/5 | 1.00 | 58.1 | 66.9 | 75.1 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_jev | 5/5 | 1.00 | 65.1 | 67.0 | 89.5 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_fara | 5/5 | 1.00 | 64.7 | 67.5 | 71.6 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | no_showui | 5/5 | 1.00 | 61.3 | 71.1 | 74.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| recovery_injected_stale_target | deterministic_only | 5/5 | 1.00 | 57.9 | 64.5 | 79.9 | 5.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | {} |
| finite_choice_no_steps | adaptive | 5/5 | 1.00 | 2357.2 | 2526.9 | 2651.7 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | strong_only | 5/5 | 1.00 | 2157.2 | 2423.2 | 3379.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_jev | 5/5 | 1.00 | 1320.8 | 2105.3 | 2355.9 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_fara | 5/5 | 1.00 | 1651.9 | 1916.8 | 2459.1 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | no_showui | 5/5 | 1.00 | 2621.8 | 2691.1 | 2835.6 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| finite_choice_no_steps | deterministic_only | 0/5 | 0.00 | 7.2 | 8.5 | 15.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |
| under_specified_stateful | adaptive | 5/5 | 1.00 | 1674.9 | 3411.5 | 3581.8 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | strong_only | 5/5 | 1.00 | 1880.2 | 2017.7 | 3667.2 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_jev | 5/5 | 1.00 | 1886.0 | 2064.1 | 5084.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_fara | 5/5 | 1.00 | 2233.5 | 8002.5 | 603771.2 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | no_showui | 5/5 | 1.00 | 1929.3 | 2253.8 | 2364.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| under_specified_stateful | deterministic_only | 0/5 | 0.00 | 13.3 | 15.3 | 24.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 5} |

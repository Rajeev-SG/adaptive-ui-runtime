# adaptive-ui-runtime benchmark results

- generated: 2026-09-20T18:41:56
- commit: `68d266e`
- transport: `fake`  reps/arm: 3
- python: 3.12.13  platform: macOS-26.5.2-arm64-arm-64bit

| case | mode | verified | success | wall p50 ms | wall p95 ms | actions | manager | jev | fara | showui | recoveries | loops | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deterministic_dom_two_step | adaptive | 3/3 | 1.00 | 0.4 | 0.9 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_step | strong_only | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_step | no_jev | 3/3 | 1.00 | 0.4 | 0.6 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_step | no_fara | 3/3 | 1.00 | 0.4 | 0.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_step | no_showui | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| deterministic_dom_two_step | deterministic_only | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| ambiguous_target_fails_closed | adaptive | 0/3 | 0.00 | 1.1 | 1.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| ambiguous_target_fails_closed | strong_only | 0/3 | 0.00 | 1.2 | 1.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| ambiguous_target_fails_closed | no_jev | 0/3 | 0.00 | 1.1 | 1.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| ambiguous_target_fails_closed | no_fara | 0/3 | 0.00 | 1.1 | 1.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| ambiguous_target_fails_closed | no_showui | 0/3 | 0.00 | 1.5 | 1.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| ambiguous_target_fails_closed | deterministic_only | 0/3 | 0.00 | 0.3 | 0.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {"unexpected_state": 3} |
| stateful_dom_eval_owned_by_manager | adaptive | 3/3 | 1.00 | 0.3 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_owned_by_manager | strong_only | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_owned_by_manager | no_jev | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_owned_by_manager | no_fara | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_owned_by_manager | no_showui | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |
| stateful_dom_eval_owned_by_manager | deterministic_only | 3/3 | 1.00 | 0.4 | 0.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | {} |

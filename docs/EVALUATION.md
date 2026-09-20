# Evaluation contract

Evaluation is part of the runtime, not a separate toy harness.

## Canonical source

Reuse `Rajeev-SG/web-automation-microbench` for task definitions, reset logic and independent verifiers where practical.

Reuse evidence/fixtures from:
- `Rajeev-SG/jev-tests`
- `Rajeev-SG/local_cua`

Do not fork those frameworks unless an upstream gap is demonstrated.

## Primary question

Does the adaptive runtime preserve or improve verified task success while reducing end-to-end wall time versus a strong-model browser-agent baseline?

Cost is reported but is the third-order objective.

## Required arms

For every promoted task class, compare where applicable:

1. `adaptive` — full runtime.
2. `strong_only` — strong manager/planner used for all decisions with the same transport/verifier.
3. `no_jev` — adaptive runtime with Jev disabled.
4. `no_fara` — adaptive runtime with Fara disabled.
5. `deterministic_only` — only for tasks genuinely solvable that way.
6. transport-specific baselines when investigating a transport claim.

The underlying task start/reset and verifier must be identical.

## Required metrics

Primary:
- verified task success rate;
- end-to-end wall time p50/p95.

Secondary:
- action count;
- observation count;
- strong-model calls;
- strong-model input/output tokens;
- Jev calls and decision p50/p95;
- Fara calls and inference p50/p95;
- transport command count;
- verifier latency;
- recovery/fallback count;
- repeated-action cycle count;
- setup/cold-start time separately;
- total inference cost;
- failure classes.

## Failure buckets

At minimum:
- policy/decision failure;
- grounding/target failure;
- transport/infrastructure failure;
- verifier mismatch;
- premature done;
- repeated-action loop;
- budget exceeded;
- unexpected state;
- test/reset failure.

Never merge infrastructure faults into model quality silently.

## Replication

Default:
- 2 reps — smoke/screen;
- 5 reps — plausible candidate;
- 10 reps — close/high-variance decision.

Preserve failures.

## Promotion policy

Correctness is the gate.

A route/component becomes default only if:
1. verified success is acceptable relative to the strong baseline on the target task class;
2. its failure modes are understood and bounded;
3. fallback restores overall runtime success;
4. it improves p50/p95 end-to-end latency or removes strong-model work without regressing wall time.

Do not promote because a component is cheaper alone.

## Jev evaluation

Use the faithful two-question/candidate framing already established in `jev-tests`.

Measure:
- coverage by confidence threshold;
- accuracy on the covered slice;
- held-out threshold validation;
- latency;
- resulting whole-task success and wall time.

A threshold that looks good in-sample is not sufficient.

## Fara evaluation

Consume `local_cua` evidence and Fara 9B issue results.

Evaluate bounded subtask classes:
- named-item navigation;
- filter/select/apply;
- form fill;
- report/download;
- short deterministic sequences;
- ambiguous/stateful sequences as negative/escalation controls.

Measure where delegation ceases to be reliable.

## End-to-end acceptance suite

Include:
- deterministic DOM-heavy task;
- search/extract/act task;
- dynamic UI task;
- form/filter/download task;
- longer workflow with multiple independent subtasks;
- safe logged-in-session task if reproducible;
- at least one visual/awkward task requiring fallback;
- at least one injected recoverable failure (stale target, focus loss or obstruction).

## Shadow mode

Support non-acting alternative decisions on real runs.

Record:
- production action;
- Jev proposal/confidence;
- Fara proposal where practical;
- strong-model proposal where practical;
- agreement/disagreement;
- eventual verifier result.

Shadow decisions must never mutate UI.

Use shadow data to calibrate/promote routes safely.

## Results artefacts

Generate machine-readable JSON plus a concise Markdown summary.

Each summary states:
- exact git commit;
- dependency/model versions;
- machine/environment;
- task set and commit;
- arm configuration;
- rep count;
- success denominator;
- p50/p95 timing;
- strong calls/tokens;
- fallback rate;
- cost;
- failure distribution;
- decision.

Raw sensitive session traces remain local and ignored by git.

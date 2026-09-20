# Product requirements

## Product statement

`adaptive-ui-runtime` is a shared execution runtime that lets agents reliably operate browser and eventually desktop interfaces without exposing them to the implementation complexity of individual automation tools/models.

The runtime chooses the **fastest route that preserves verified correctness**.

## Priorities

Priority order is strict:

1. **Accuracy / verified success**
2. **Speed / end-to-end wall time**
3. **Cost / paid inference avoided**

A cheaper route must not be selected if benchmark evidence shows materially worse verified success.

## Functional requirements

### FR1 — Unified agent interface

Expose one MCP server plus equivalent CLI/Python interfaces.

Required operations:
- `execute`
- `inspect`
- `verify`
- `plan`
- `status`
- `resume`
- `trace`
- `evaluate`

The normal agent path must not require knowledge of Jev, Fara, Playwriter, Browser Relay, Stagehand, Browser Harness or manager model details.

### FR2 — Typed task contract

An executable task/subtask must support:
- goal;
- current/expected state;
- preconditions;
- postconditions/success criteria;
- permitted side effects;
- action/time budget;
- preferred/allowed routes;
- fallback policy;
- privacy/safety constraints;
- idempotency metadata.

### FR3 — Strong long-context manager

A configurable strong model owns:
- initial decomposition;
- long-horizon/global state;
- ambiguous decisions;
- recovery after unexpected states;
- synthesis of final result.

It must be possible to keep the full task context at this layer without resending it to every cheap worker call.

### FR4 — Fast-path routing

The runtime can make cheap/fast decisions without a strong-model turn.

Jev is the initial fast semantic router for finite candidate decisions. Confidence gating must be calibrated from measured traces. Unsupported/low-confidence cases escalate rather than guess.

### FR5 — Deterministic execution first

If a reliable API/DOM/accessibility/known recipe action exists, execute it without model inference.

The router should distinguish:
- deterministic/known;
- structured browser;
- cheap semantic decision;
- visual micro-job;
- strong-model reasoning.

### FR6 — Browser transports

Support interchangeable adapters for:
- Playwriter;
- Browser Relay;
- Stagehand where it adds value;
- Browser Harness where it adds value.

Preserve/port the existing `BridgeBrowser` observed-node contract from `jev-tests` rather than inventing a second incompatible abstraction.

### FR7 — Local visual workers

Integrate Fara as a bounded local worker. Start from the proven Fara 4B artifact and consume the Fara 9B evaluation when available.

The runtime must support a hierarchy such as:
- Fara 4B;
- optional Fara 9B escalation if evidence justifies it;
- ShowUI/TongUI grounding fallback where evidence justifies it;
- strong manager.

Workers may not own an unbounded workflow.

### FR8 — Independent verification

Success is established by independent evidence, not an actor's self-report.

Verifier types should include:
- DOM/property/state;
- URL/navigation;
- file/download existence + metadata;
- API/network state where appropriate;
- accessibility state;
- screenshot/visual invariants only when structured verification is impossible;
- task-specific verifier imported from microbench.

### FR9 — Bounded recovery

Classify and handle at least:
- stale target/node;
- lost browser focus;
- obstruction/modal;
- element moved/DOM drift;
- transport failure;
- page navigation/state drift;
- visual-only target;
- actor repeated same action;
- actor premature DONE;
- verifier mismatch;
- unexpected/ambiguous state.

Each recovery path has a fixed budget. Generic blind retries are forbidden.

### FR10 — Cycle detection

Fingerprint material state and recent actions.

Repeated same-action-on-same-state patterns must:
1. stop the current worker;
2. record the failure class;
3. escalate route or manager;
4. never consume the remaining action budget by repeating the same guess.

### FR11 — Durability and resumability

Runs survive process/interruption failures and can resume from the last safe checkpoint without replaying completed state-changing actions.

Initial implementation should validate DBOS as the durable workflow backbone rather than building workflow durability from scratch.

### FR12 — Observability

Every run gets a stable `run_id`.

Trace:
- plan/decomposition;
- route decisions + confidence;
- snapshots/state fingerprints;
- actions;
- verifier results;
- repair/escalation events;
- timings;
- model/tool usage;
- failure classes.

OpenTelemetry-compatible output is preferred.

### FR13 — Evaluation and shadow mode

The production execution path and evaluation path share the same code.

Required evaluation modes:
- adaptive/full runtime;
- strong-only;
- deterministic-only where possible;
- no-Jev;
- no-Fara;
- selected transport baselines.

Shadow mode may obtain alternate decisions without executing them, allowing safe measurement on real tasks.

### FR14 — Reusable recipes

A verified successful execution may be distilled into a reusable semantic recipe.

Recipes:
- prefer stable semantic locators over raw coordinates;
- carry success checks;
- fail closed on drift;
- can rebind via structured observation;
- only update after the repaired execution verifies successfully.

Do not build a large recipe system before the core adaptive runtime is proven.

### FR15 — Browser first, extensible to desktop

v1 is browser-first because the existing evidence/tools are strongest there.

The protocols must not hard-code browser-only semantics so a later native desktop/accessibility transport can use the same task, route, verifier and recovery contracts.

## Non-functional requirements

### NFR1 — Accuracy

No route is promoted into default execution solely on speed/cost. It must meet the acceptance threshold defined against the strong baseline on representative tasks.

### NFR2 — Latency

Minimise:
- strong-model turns;
- repeated screenshots/observations;
- serial inference where safe;
- model reload/cold starts;
- redundant tool hops.

Keep useful local models resident where practical.

### NFR3 — Cost

Record cost, but optimise it only after correctness and latency. Local inference should replace paid calls when it does not materially worsen success or latency.

### NFR4 — Fail closed

When state is uncertain, stop/escalate rather than executing an unsafe guessed action.

### NFR5 — Pluggability

Models/transports/verifiers are replaceable without changing the agent-facing API.

### NFR6 — Reproducibility

Benchmark summaries must include exact versions/revisions, model artifacts, settings, task commit, repetitions, verifier and environment.

## v1 acceptance

The runtime must complete an agreed representative microbench subset through the MCP/CLI surface.

Acceptance requires:
- no unbounded action loops;
- independent verification on every scored task;
- durable status/resume demonstrated;
- adaptive + baseline + ablation results generated from the same harness;
- adaptive verified success is not materially below the strong-only baseline;
- adaptive path demonstrates a material wall-time improvement on at least the task classes claimed as fast-path wins;
- full trace explains every fallback/recovery.

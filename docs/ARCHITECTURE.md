# Architecture

## System boundary

This repo owns **orchestration, routing, verification composition, recovery policy, durable workflow configuration and agent exposure**.

It does **not** own the underlying models, browser engines, generic workflow engine, generic self-healing framework, benchmark framework or observability backend.

The design goal is to compose existing capabilities with the smallest possible amount of glue.

```text
                       Agent
                         |
                  MCP / CLI / Python
                         |
              +----------v-----------+
              | Runtime API / DBOS   |
              | durable Run + Steps  |
              +----------+-----------+
                         |
              +----------v-----------+
              | Strong Manager       |
              | long context / plan  |
              +----------+-----------+
                         |
              +----------v-----------+
              | Adaptive Router      |
              +---+---------+--------+
                  |         |
        deterministic       +--------------------+
                  |                              |
                  v                              v
         Browser/recipe                    Cheap workers
            execution                    Jev / Fara / ...
                  |                              |
                  +--------------+---------------+
                                 v
                         Browser abstraction
                 Playwriter / Relay / Stagehand /
                         Browser Harness
                                 |
                                 v
                         Independent verifier
                                 |
                +----------------+----------------+
                |                                 |
              pass                         classified failure
                |                                 |
          next subtask              existing repair capability
                                                  |
                                      alternate route / manager
```

## Composition rule

Every architectural layer must answer: **what existing component already provides this?**

Expected composition:

| Need | Preferred source |
|---|---|
| Durable workflows/checkpoints/resume | DBOS |
| Typed manager/model interface | Pydantic AI |
| MCP transport/protocol | MCP SDK |
| Jev semantics + browser bridge | existing `jev-tests` implementation |
| Local Fara adapters/artifacts | existing `local_cua` implementation/cache |
| Browser execution | Playwriter / Browser Relay |
| DOM/browser self-healing | Stagehand where it proves useful |
| low-level CDP escape hatch/helpers | Browser Harness where it proves useful |
| task/reset/verifier corpus | `web-automation-microbench` |
| traces/export | OpenTelemetry-compatible stack |

The runtime should normally add **adapters and policy**, not replace these systems.

## Local-first implementation

Before acquiring an external asset, consult `docs/ASSET_INVENTORY.md`.

Local development should prefer:
- existing repo clones/worktrees;
- existing model caches;
- existing installed browser runtimes;
- already-running local services;
- already-installed packages where version-compatible.

The inventory also records the canonical remote source/version so clean installs stay reproducible.

## Why this split

The strong model is good at:
- global context;
- decomposition;
- ambiguity;
- exception reasoning.

It is a poor choice for every routine inner-loop action because repeated full-context turns add latency and cost.

Jev is useful where the decision can be reduced to a small candidate set. Fara 4B is useful for grounding and very short bounded visual work; ShowUI 2B is the preferred cheap actor candidate when the next subgoal is already known. `local_cua` PR #16 shows that bare Fara should not own stateful/live-site DOM-eval workflows, and that Fara 9B is not a useful v1 escalation tier. Structured transports and the strong planner own those richer state channels.

The verifier, not the actor, determines progress.

## Core domain objects

### Run

A durable user/agent request.

Key fields:
- `run_id`
- goal
- constraints
- plan
- current task/subtask
- status
- budgets
- checkpoints
- final result

### Subtask

A bounded unit of work:
- goal
- preconditions
- postconditions
- action budget
- timeout
- allowed routes
- side effects
- verifier
- fallback policy

### Observation

Transport-neutral representation of material state:
- URL/window/app identity;
- structured elements where available;
- optional accessibility tree;
- optional screenshot;
- state fingerprint;
- timestamp/version.

### CandidateAction

A finite, typed action proposed by deterministic logic, Jev, Fara or manager.

### ActionResult

The transport's factual result:
- command status;
- changed state/snapshot id;
- timing;
- errors.

### VerificationResult

Independent check:
- `passed`
- evidence
- failure class
- confidence only where verification itself is probabilistic.

### RouteDecision

Records:
- selected route;
- reason;
- confidence;
- alternatives considered;
- escalation threshold;
- budget impact.

## Routing policy

The initial policy should be simple and measurable:

```text
if verified deterministic action/recipe exists:
    execute deterministically
elif structured browser executor can resolve the action unambiguously:
    use Playwriter/Relay/Stagehand
elif finite browser decision and Jev is calibrated for this class:
    use Jev
elif known subgoal only needs local visual grounding/action:
    use ShowUI-2B or Fara-4B
else:
    use/re-enter the strong manager

# For stateful, multi-item or DOM/eval-dependent workflows,
# the strong manager may own the outer loop from the start
# and delegate individual actions to the faster tiers above.
# Never escalate Fara-4B -> Fara-9B in v1.
```

After every mutation: verify.

Never implement an opaque learned meta-router until the rule-based policy has benchmark evidence.

## Worker budgets

A worker invocation must specify:
- max actions;
- max wall time;
- max unchanged-state actions;
- max verifier failures;
- escalation route.

Defaults should be conservative.

Example:

```text
Fara goal: click/open the visually identified country control
max_actions: 2
unchanged_state_limit: 1
verification: target control opened or expected value changed
fallback: ShowUI/structured transport -> manager

# The manager/structured layer, not bare Fara, owns a stateful
# "select UK and apply filters across a live report" workflow.
```

## Cycle detection

Maintain a rolling key such as:

```text
(state_fingerprint, normalized_action, normalized_target)
```

If an action repeats against an unchanged material state, do not let the model burn the remainder of its budget. Escalate immediately.

## Browser abstraction

Reuse the contract/provenance from `jev-tests` `BridgeBrowser`.

The common transport should expose capabilities, not pretend every backend is identical:

- navigate
- observe
- resolve structured targets
- click
- type
- key
- select
- scroll
- wait
- screenshot
- evaluate only where explicitly permitted
- focus
- download metadata
- current URL/state

Adapters advertise capability flags. Routing may use them.

## Durability

Validate DBOS first.

Durable boundaries should include:
- plan creation;
- each externally visible state-changing subtask;
- verifier result;
- manager recovery;
- final result.

Do not checkpoint after every trivial pure helper if it adds latency with no recovery value.

Do not build a replacement workflow engine if DBOS meets these requirements.

## Pydantic AI

Use typed manager inputs/outputs and structured recovery decisions. The manager should return validated plans/subtasks rather than prose that downstream code must reinterpret.

Do not put Pydantic AI in the hot path for actions that do not need the strong manager.

## Self-healing

"Self-healing" means **orchestrating the best existing repair capability**, not writing a new browser-healing framework.

Prefer, in order where applicable:
- transport-native target rebinding/focus/stale-node handling;
- Stagehand semantic observe/replay/healing;
- Browser Harness/CDP helper paths;
- visual grounding/Fara;
- strong-manager replan.

The bespoke recovery layer should remain small: failure classification, budget enforcement, route selection and verification.

Initial repair table:

| Failure | First repair | Next escalation |
|---|---|---|
| stale node | transport/Stagehand re-observe/rebind | alternate structured transport |
| focus lost | existing transport/browser focus operation | transport fallback |
| obstruction | existing semantic/DOM dismiss + re-observe | manager |
| DOM drift | existing semantic rebind | visual worker |
| structured target unavailable | visual grounder/Fara | manager |
| transport error | switch transport if safe | manager |
| premature DONE | verifier rejects | alternate worker/manager |
| repeated action | terminate worker | alternate route |
| unexpected state | no blind retry | manager replan |

If a mature included dependency already performs a repair safely, call it; do not duplicate its heuristics in this repo.

## Strong manager context

The manager Run can retain:
- original goal;
- full decomposition;
- prior verified outcomes;
- compact traces/failure summaries;
- relevant long-context artefacts.

Cheap workers receive only the bounded subtask + minimum state required. This is how we use long context without paying its latency on every interaction.

## Extension to desktop

Keep:
- `Observation`
- `CandidateAction`
- `VerificationResult`
- `RouteDecision`
- worker budgets

generic enough for a future native desktop/accessibility transport.

Do not compromise browser v1 to prematurely solve every desktop edge case.

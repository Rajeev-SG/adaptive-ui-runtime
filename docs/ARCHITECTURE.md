# Architecture

## System boundary

This repo owns **orchestration, routing, verification, recovery, durable state and agent exposure**.

It does not own the underlying models/browser engines.

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
          next subtask              deterministic bounded repair
                                                  |
                                      alternate route / manager
```

## Why this split

The strong model is good at:
- global context;
- decomposition;
- ambiguity;
- exception reasoning.

It is a poor choice for every routine inner-loop action because repeated full-context turns add latency and cost.

Jev is useful where the decision can be reduced to a small candidate set. Fara is useful when a bounded section is visual/awkward and can be delegated locally. Structured transports are preferable when they can act deterministically.

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
elif finite structured browser decision and Jev is calibrated for this class:
    use Jev
elif structured browser executor can directly resolve the action:
    use Playwriter/Relay/Stagehand
elif bounded visual micro-job:
    use Fara
else:
    call strong manager
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
Fara goal: select UK, apply filter
max_actions: 4
unchanged_state_limit: 1
verification: selected_country == "UK" && filter_applied
fallback: structured transport -> manager
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

## Pydantic AI

Use typed manager inputs/outputs and structured recovery decisions. The manager should return validated plans/subtasks rather than prose that downstream code must reinterpret.

Do not put Pydantic AI in the hot path for actions that do not need the strong manager.

## Self-healing

"Self-healing" means classified recovery, not retries.

Initial repair table:

| Failure | First repair | Next escalation |
|---|---|---|
| stale node | re-observe/rebind | alternate structured transport |
| focus lost | focus target tab/window | transport fallback |
| obstruction | dismiss known obstruction / re-observe | manager |
| DOM drift | semantic rebind | visual worker |
| structured target unavailable | visual grounder/Fara | manager |
| transport error | switch transport if safe | manager |
| premature DONE | verifier rejects | alternate worker/manager |
| repeated action | terminate worker | alternate route |
| unexpected state | no blind retry | manager replan |

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

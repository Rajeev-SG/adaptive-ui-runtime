# AGENTS.md

This repository is intended to be delivered by coding agents. Follow these rules.

## Mission

Build and prove an **accuracy-first, low-latency adaptive UI runtime**. Correctness comes before speed; speed comes before cost.

Do not optimise for elegance at the expense of measured end-to-end task success.

## Reuse policy

Before writing a subsystem, inspect mature existing tools and the related repos:

- `Rajeev-SG/jev-tests`
- `Rajeev-SG/local_cua`
- `Rajeev-SG/web-automation-microbench`

Prefer upstream packages/adapters over copied or bespoke framework code.

In particular, do not independently reimplement:
- durable workflow execution if DBOS satisfies the requirement;
- browser self-healing already provided by Stagehand/Browser Harness;
- the existing Jev `BridgeBrowser` abstraction;
- benchmark task/reset/verifier logic already present in `web-automation-microbench`.

If a proposed dependency does not satisfy the requirement, record the concrete gap before building replacement code.

## Architecture rules

1. The agent-facing API is runtime-level (`ui.execute`, etc.), never raw Jev/Fara clicks.
2. Browser transports implement a common protocol.
3. Worker/model implementations are plugins behind the router.
4. Verification is independent of the actor.
5. Every mutable subtask has:
   - preconditions;
   - postconditions;
   - action/time budget;
   - fallback/escalation policy.
6. Same-state/same-action cycles terminate immediately and escalate.
7. Retries must be classified and bounded; no generic "try again" loops.
8. Strong-model replanning occurs only when deterministic recovery/cheap routes are exhausted or the state is genuinely ambiguous.
9. Every decision/action must be traceable enough to reproduce benchmark metrics.
10. Secrets, cookies, page content and private session data must not be committed.

## Testing rules

- Preserve failed runs.
- Use independent verifiers.
- Separate policy/model failures from transport/infrastructure failures.
- Compare against the same initial state and verifier.
- Run 2 reps to screen, 5 for plausible candidates, 10 only for close/high-variance cases unless the benchmark issue specifies otherwise.
- Never improve benchmark numbers by silently removing hard tasks.
- Any compatibility workaround is a separately labelled condition.
- Unit tests are insufficient for acceptance: live end-to-end browser tests are required.

## Performance rules

Instrument the hot path before optimising it.

Always capture:
- wall time;
- planning/decision latency;
- action latency;
- verifier latency;
- retries/recoveries;
- strong-model calls/tokens/cost;
- Jev/Fara calls;
- transport commands;
- success/failure.

Do not add an abstraction to the hot path without measuring its overhead.

## Delivery discipline

Work from GitHub issues. Keep issue state/comments current as evidence lands.

For each issue:
1. reproduce/inspect the relevant existing evidence;
2. implement the smallest coherent slice;
3. test it;
4. run the acceptance scenario;
5. commit generated benchmark summaries but not sensitive raw traces;
6. update docs/results;
7. close only with evidence.

If an issue's assumptions are disproven, update the issue/docs rather than forcing the original design.

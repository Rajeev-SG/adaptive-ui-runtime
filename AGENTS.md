# AGENTS.md

This repository is intended to be delivered by coding agents. Follow these rules.

## Mission

Build and prove an **accuracy-first, low-latency adaptive UI runtime**. Correctness comes before speed; speed comes before cost.

Do not optimise for elegance at the expense of measured end-to-end task success.

## STOP: reuse-first gate

**This project is primarily an integration/composition project, not a framework-building project.**

Before you write code, install a package, clone a repository, download a model, install a browser, or build a self-healing mechanism:

1. **Inspect what already exists on disk.**
   - existing clones/worktrees of the related repos;
   - installed binaries/services;
   - Python/Node environments and package caches;
   - Hugging Face/model caches;
   - Playwright/Chromium/browser installations;
   - existing Jev/Fara artefacts and benchmark outputs.
2. **Inspect the related project repos before reimplementing anything.**
   - `Rajeev-SG/jev-tests`
   - `Rajeev-SG/local_cua`
   - `Rajeev-SG/web-automation-microbench`
3. **Inspect mature upstream OSS before building a subsystem.**
4. **Reuse the existing implementation in place, adapt it, or depend on it.**
5. Only build bespoke functionality when there is a concrete gap that cannot be satisfied by the above.

**Do not redownload/reclone/reinstall something merely because it is easier than locating the existing copy.**

During Phase 0, maintain `docs/ASSET_INVENTORY.md` with the actual local path/version/commit/cache location of reusable assets. Prefer those local assets for development and testing. Keep reproducible remote provenance/pins for clean installs.

Read [Reuse-first implementation policy](docs/REUSE_FIRST.md) before implementation work.

## Bespoke-code budget

The custom code in this repo should be mostly **thin glue**:

- typed domain contracts;
- adapters around existing transports/workers;
- routing policy;
- verifier composition;
- bounded recovery orchestration;
- MCP/CLI exposure;
- metrics/evaluation glue.

The following are **not** acceptable bespoke projects unless an issue records a measured, concrete upstream gap first:

- workflow/durability engine;
- browser automation engine;
- browser self-healing framework;
- DOM/accessibility parser if an included tool already provides it;
- Jev implementation;
- Fara/model inference runtime;
- browser benchmark/task framework;
- observability stack;
- generic MCP framework;
- model download/cache manager.

A change that introduces a substantial new subsystem must include a short **reuse decision** in the PR/issue:

```text
Need:
Existing local asset checked:
Existing project code checked:
Upstream OSS checked:
Why reuse/adaptation is insufficient:
Smallest bespoke surface required:
```

If that section cannot be filled in convincingly, do not build the subsystem.

## Reuse hierarchy

Use this order:

1. **Already-running / already-downloaded local asset**
2. **Existing code in the three related repos**
3. **Already-installed mature package/tool**
4. **Pinned upstream OSS package/repository**
5. **Thin adapter/wrapper**
6. **Bespoke implementation as last resort**

For local development, avoid duplicate copies. For reproducibility, record exact upstream version/commit/model artefact without forcing a fresh download when the same artefact is already cached locally.

## Specific reuse expectations

Do not independently reimplement:

- durable workflow execution if DBOS satisfies the requirement;
- typed model orchestration already supplied by Pydantic AI;
- MCP protocol/server plumbing already supplied by the MCP SDK;
- browser self-healing already provided by Stagehand/Browser Harness or the selected transport;
- the Jev `BridgeBrowser` abstraction and faithful action framing already proven in `jev-tests`;
- Fara adapters/model artefacts already proven/downloaded through `local_cua`;
- benchmark task/reset/verifier logic already present in `web-automation-microbench`;
- tracing/export machinery already supplied by OpenTelemetry-compatible libraries.

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

## Self-healing rule

The runtime should **orchestrate existing self-healing capabilities**, not grow its own competing browser-healing framework.

Prefer:
- transport-native semantic rebinding;
- Stagehand observe/replay/self-healing where useful;
- Browser Harness/CDP helpers where useful;
- existing focus/stale-node handling in Playwriter/Browser Relay;
- visual fallback through Fara/grounders.

Our bespoke recovery layer should mainly:
1. classify the failure;
2. choose the already-existing repair capability;
3. enforce retry/action budgets;
4. verify the repair;
5. escalate if it fails.

## Testing rules

- Preserve failed runs.
- Use independent verifiers.
- Separate policy/model failures from transport/infrastructure failures.
- Compare against the same initial state and verifier.
- Run 2 reps to screen, 5 for plausible candidates, 10 only for close/high-variance cases unless the benchmark issue specifies otherwise.
- Never improve benchmark numbers by silently removing hard tasks.
- Any compatibility workaround is a separately labelled condition.
- Unit tests are insufficient for acceptance: live end-to-end browser tests are required.
- Prefer existing downloaded models/browsers and existing test fixtures; do not create redundant copies.

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
1. **run the reuse-first preflight and update the asset inventory if anything relevant changed;**
2. reproduce/inspect the relevant existing evidence;
3. implement the smallest coherent integration slice;
4. test it;
5. run the acceptance scenario;
6. commit generated benchmark summaries but not sensitive raw traces;
7. update docs/results;
8. close only with evidence.

If an issue's assumptions are disproven, update the issue/docs rather than forcing the original design.

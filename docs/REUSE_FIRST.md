# Reuse-first implementation policy

## Purpose

Ship the runtime quickly by composing what already exists.

This repo should contain the **smallest possible amount of bespoke implementation** necessary to connect proven components into one accurate, fast runtime.

The default assumption is:

> If we think we need to build something substantial, first prove that it does not already exist locally, in the related repos, or in mature OSS.

## Mandatory search order

For every subsystem or capability:

### 1. Check local disk first

Look for:
- an existing clone/worktree;
- a running local service;
- an installed binary;
- a compatible Python/Node package;
- model weights in local caches;
- an existing browser/Playwright/Chromium installation;
- existing benchmark fixtures/results.

Do not clone, install or download again until this check is complete.

### 2. Check related repos

Inspect:

- `Rajeev-SG/jev-tests`
- `Rajeev-SG/local_cua`
- `Rajeev-SG/web-automation-microbench`

Reuse existing code, scripts, fixtures, model adapters and measurements wherever sensible.

### 3. Check mature OSS

Use upstream projects for generic infrastructure.

Preferred initial sources:

| Capability | Reuse target |
|---|---|
| Durable workflows, checkpoints, resume | DBOS |
| Typed model/manager orchestration | Pydantic AI |
| MCP protocol/server | official MCP SDK |
| Browser execution in current user session | Playwriter / Browser Relay |
| Browser semantic healing / observe / replay | Stagehand if validated |
| Low-level browser/CDP escape hatch | Browser Harness if validated |
| Fast finite-choice routing | Jev implementation already proven in `jev-tests` |
| Local visual CUA | Fara adapters/artifacts already proven in `local_cua` |
| Benchmark tasks/reset/verifiers | `web-automation-microbench` |
| Traces/export | OpenTelemetry-compatible tooling |

### 4. Prefer a thin adapter

If an existing component is 80–95% of what we need, write the smallest adapter around it.

Do not fork or replace it just to obtain a cleaner internal API.

### 5. Bespoke implementation is the last resort

Before adding a substantial subsystem, record:

```text
Need:
Local assets checked:
Related project code checked:
Upstream OSS checked:
Concrete gap:
Why a thin adapter is insufficient:
Smallest bespoke surface:
```

That record belongs in the issue/PR.

## What bespoke code is expected

Reasonable custom code:

- shared Pydantic contracts;
- capability adapters;
- routing rules;
- threshold configuration;
- verifier composition;
- cycle detection;
- failure classification;
- bounded recovery orchestration;
- MCP/CLI product surface;
- benchmark/metrics glue.

These pieces are specific to how the runtime composes existing systems.

## What should not become bespoke

Do not build another:

- workflow engine;
- task queue;
- persistence/checkpoint engine;
- browser driver;
- browser DOM engine;
- general browser self-healing framework;
- model server if an existing runtime works;
- Jev clone;
- Fara inference implementation;
- MCP protocol stack;
- generic tracing backend;
- benchmark corpus/framework.

## Self-healing policy

Most self-healing should come from existing software.

The runtime's responsibility is primarily:

```text
failure
 -> classify
 -> invoke best existing repair capability
 -> verify
 -> escalate if necessary
```

Examples:

- stale element -> transport/Stagehand re-observe or rebind;
- focus issue -> existing focus primitive;
- unusual CDP/browser behaviour -> Browser Harness helper;
- structured target unavailable -> Fara/visual worker;
- genuinely new/ambiguous state -> strong manager.

Avoid growing a parallel collection of page-specific heuristics in this repo.

## Local asset reuse

### Models

Before model download, inspect existing caches and the assets already used by `local_cua`.

If the exact compatible artifact is already present, use it.

Do not create a second copy solely to place it inside this repo.

### Browsers

Reuse installed/working browser runtimes and sessions where compatible.

Do not automatically trigger a Playwright/Chromium download if a compatible existing installation satisfies the test.

### Repositories

Prefer an existing local clone/worktree.

Do not create duplicate clones for cross-repo inspection.

When code needs to be consumed reproducibly, prefer:
- normal package dependency;
- pinned git dependency;
- small vendored adapter only when licensing/packaging makes that necessary.

Avoid wholesale source copying.

### Packages

Use the existing environment/cache where compatible, but pin supported versions in project metadata so a clean machine remains reproducible.

## Development vs reproducibility

"Do not redownload" does not mean "depend on one undocumented laptop path".

For each reused asset record both:

1. **local resolution** — where/how the current machine finds it;
2. **canonical provenance** — upstream repo/package/model id + exact version/commit/revision.

That gives fast local development and reproducible clean installs.

## Completion criterion

A v1 implementation should look small compared with the systems it composes.

If the repo starts accumulating large implementations of browser mechanics, workflow durability, model serving or self-healing heuristics, stop and perform another reuse audit.

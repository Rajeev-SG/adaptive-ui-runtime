# Agent integration

## Principle

Agents use **one runtime-level tool**, not a bag of low-level browser/model tools.

The runtime decides whether the work is executed by a deterministic route, Jev, Playwriter, Browser Relay, Fara, another grounder or the strong manager.

## MCP surface

Target tool family:

### `ui.execute`

Input:
- goal;
- success criteria;
- constraints;
- optional preferred session/browser;
- optional timeout/budget.

Output:
- run_id;
- verified status;
- result/evidence;
- summary metrics.

### `ui.inspect`

Read-only observation of current UI/session state.

### `ui.verify`

Evaluate explicit success criteria without performing mutation.

### `ui.plan`

Produce the typed plan/routing strategy without executing it.

### `ui.status`

Return durable run/subtask state and current route.

### `ui.resume`

Resume a paused/interrupted run from its checkpoint.

### `ui.trace`

Return compact machine-readable execution trace and failure/recovery events.

### `ui.evaluate`

Run a named benchmark/task under one or more runtime modes and return/emit comparison artefacts.

## CLI

The CLI must exercise the same runtime code path as MCP.

Examples:

```bash
aur execute --goal "Download the August report" --success success.yaml
aur status <run-id>
aur trace <run-id>
aur evaluate benchmark.yaml
aur serve-mcp
```

The final binary/package name may change; do not fork separate logic for the CLI.

## Coding-agent policy

Recommended shared instruction:

> For browser/UI work, use adaptive-ui-runtime's `ui.execute` rather than manually implementing a screenshot/reason/click loop. Supply concrete success criteria whenever possible. Use `ui.trace` only when debugging a failed runtime execution.

## Why not expose raw workers by default?

If agents can directly call `fara.click`, `jev.choose`, `browser_relay.click`, etc., they recreate the same thrashy orchestration this project is intended to remove.

Raw worker commands may exist behind a debug/developer namespace but should not be part of the normal agent toolset.

## Evaluation from agents

Agents should be able to ask the runtime:

```text
ui.evaluate(
  task = "...",
  modes = ["adaptive", "strong_only", "no_jev", "no_fara"]
)
```

and receive:
- verified success;
- wall time;
- calls/tokens;
- route/fallback trace;
- cost;
- comparison summary.

This makes the product self-evaluating and lets coding agents prove whether a change improved runtime behaviour before merging it.

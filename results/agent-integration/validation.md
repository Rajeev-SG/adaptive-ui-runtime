# Agent integration validation (issue #18)

Live validation on this machine, 2026-09-20/21. Two distinct coding agents were
given the same instruction: discover the adaptive-ui-runtime MCP server and call
`ui.execute`, then use the run_id.

## Codex CLI (`codex-cli 0.155.0-alpha.2.6`)

- Registered via `~/.codex/config.toml`:
  `[mcp_servers.adaptive_ui_runtime]` -> `.venv/bin/python -m adaptive_ui_runtime serve-mcp`.
- Codex **discovered** the tool (`mcp: adaptive_ui_runtime/ui_execute started`).
- Live call result:
  - `run_id: run-810c42f7e5c2`
  - `verified: true`
  - follow-up `ui_trace` returned **10 events**
- The agent did not ask for or specify Jev/Fara/Playwriter; it called one tool.

## OMP (`omp v18.2.6`)

- Registered via `~/.omp/agent/mcp.json` (`adaptive-ui-runtime`, transport `isolated`).
- Live call result:
  - `run_id: run-8e97d0b9f896`
  - `verified: true` (status succeeded; s1 verified; 2 actions, 3.3 ms wall)
- One tool call; no worker micromanagement.

## Shared policy

`~/.omp/agent/AGENTS.md` (repo `omp-home`) now instructs: prefer
adaptive-ui-runtime `ui.execute` with explicit success criteria for browser/UI
work, use `ui.trace` only to debug, do not micromanage the workers, and keep the
low-level browser routes for runtime debugging and uncovered work.

## What this proves

- Two distinct agents discover the MCP tools and use `ui.execute`.
- They receive and use the `run_id`; `ui.trace` works on it.
- The caller never chooses the underlying worker/transport.
- No per-agent runtime logic was added: only an MCP server definition + shared policy.

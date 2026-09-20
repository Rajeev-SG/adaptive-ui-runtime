# Installing and wiring the runtime for coding agents (issue #18)

One install, one entry point, one MCP server. Agents call `ui.execute`; they never
choose Jev/Fara/Playwriter.

## Install (from the repo)

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python -e ".[local]"   # [local] adds mlx-vlm for Fara/ShowUI
.venv/bin/aur --help
```

`aur` is the CLI; `python -m adaptive_ui_runtime serve-mcp` is the MCP server.

## MCP server definition (any MCP-capable agent)

The server speaks stdio and exposes `ui.execute`, `ui.inspect`, `ui.verify`,
`ui.plan`, `ui.status`, `ui.resume`, `ui.trace`, `ui.evaluate` (plus `ui_health`).

Generic MCP JSON (adapt the key names to the host agent):

```json
{
  "mcpServers": {
    "adaptive-ui-runtime": {
      "command": "/absolute/path/to/adaptive-ui-runtime/.venv/bin/python",
      "args": ["-m", "adaptive_ui_runtime", "serve-mcp"],
      "env": {
        "AUR_TRANSPORT": "isolated",
        "OPENROUTER_API_KEY": "…"
      }
    }
  }
}
```

Notes:
- AUR_TRANSPORT chooses the default transport (`isolated`, `relay`, `playwriter`, `fake`).
- `OPENROUTER_API_KEY` enables the strong-manager path; without it the runtime still
  runs deterministic/structured and Jev routes.
- For Browser Relay, set `AUR_RELAY_PROFILE` and `BROWSER_RELAY_TAB`; for Playwriter,
  `PLAYWRITER_SESSION`.

### Codex (`~/.codex/config.toml`)

```toml
[mcp_servers.adaptive_ui_runtime]
command = "/absolute/path/to/adaptive-ui-runtime/.venv/bin/python"
args = ["-m", "adaptive_ui_runtime", "serve-mcp"]
```

### Cline / OMP / OpenChamber / Claude

Use the same MCP JSON shape in the agent's MCP config surface (Cline MCP settings,
OMP `models.yml`/MCP config, OpenChamber/OpenCode MCP config, Claude desktop
`mcpServers`). No per-agent runtime logic is required — only the server definition.

## Shared agent policy (recommended wording)

> For browser/UI work, prefer adaptive-ui-runtime's `ui.execute` with explicit
> success criteria over manually implementing a screenshot/reason/click loop. Use
> `ui.trace` to debug a failed runtime execution. Do not micromanage Jev/Fara/transports.

## One-tool usage example

```text
ui.execute(goal="Add two todos and apply the Active filter",
           success_criteria=[{kind: "js_rule", description: "saved todos",
                              rule: {js: "localStorage.getItem('react-todos')"}}])
-> {run_id, verified, summary_metrics}
```

Then `ui.trace(run_id)` only if `verified` is false.

## Verified integration (this machine)

| Agent | Route | Evidence |
|---|---|---|
| Codex | MCP stdio | tests/test_mcp_surface.py runs the server over stdio and calls all 8 tools |
| Generic MCP client | MCP stdio | same test uses the official MCP SDK client |
| CLI (non-MCP) | `aur execute` | tests/test_mcp_surface.py parity test |
| Python | `Runtime.execute` | same parity test |

See `results/RESULTS.md` for the runtime's supported-task scope.

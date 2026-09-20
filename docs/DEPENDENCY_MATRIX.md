# Dependency / compatibility matrix (issue #2)

Verified 2026-09-20 on macOS (Apple Silicon M5 Pro), Python 3.12.13, `uv 0.10.11`.

## Architecture dependencies

| Dependency | Version pinned | Local status | Decision | Notes |
|---|---|---|---|---|
| `pydantic` | 2.13.5 | installed (repo venv) | use | contracts + validation |
| `pydantic-ai-slim` | 2.46.0 | installed (repo venv) | use | typed manager outputs |
| `dbos` | 3.0.0 | installed (repo venv) | use | durability; SQLite sys DB for dev/test |
| `mcp` | 2.2.0 | installed (repo venv) | use | **API change**: `FastMCP` → `MCPServer` |
| `opentelemetry-api` | 1.44.0 | installed (repo venv) | use | trace export (opt-in) |
| `opentelemetry-sdk` | 1.44.0 | installed (repo venv) | use | trace export (opt-in) |
| `PyYAML` | 6.x | installed (repo venv) | use | task-spec loading |
| `mlx-vlm` | 0.7.1 | present in `local_cua` venv | reuse (optional extra) | Fara-4B / ShowUI-2B local workers |
| `pytest` / `pytest-asyncio` | 9.1.1 / 1.4.0 | installed (repo venv) | use | tests |
| `ruff` / `mypy` | 0.16.8 / 2.3.1 | installed (repo venv) | use | lint / types |

## External tool dependencies (reused in place, not installed)

| Tool | Local status | Decision |
|---|---|---|
| `playwriter` 0.5.0 | installed (`~/Library/pnpm/playwriter`); sessions live | reuse as transport |
| Browser Relay + `relay` wrapper | installed (`~/.local/bin/relay`); 4 profiles healthy | reuse as transport |
| Playwright Chromium | `~/Library/Caches/ms-playwright/chromium-1243` | reuse for isolated reps |
| `uv` 0.10.11 | `/opt/homebrew/bin/uv` | use for env + CI |

## Model artefacts (reused from cache; no download)

| Artefact | Local path | Version | Decision |
|---|---|---|---|
| Fara-4B | HF cache `models--runanywhere--Fara1.5-4B-mlx-4bit` (7.4 GB) | rev `9e3987b4...` | bounded local worker |
| ShowUI-2B | HF cache `models--mlx-community--ShowUI-2B-bf16-4bit` (4.1 GB) | cached | preferred local actor |
| Fara-9B | HF cache (partial) | — | **excluded from v1** (PR #16) |

## Known incompatibilities / workarounds

- **MCP SDK 2.x** renamed `FastMCP` to `MCPServer` (`mcp.server.mcpserver`).
  Server code targets the 2.x API and pins `mcp>=1.9` as the floor.
- **DBOS** runs on SQLite for dev/test; PostgreSQL recommended for production
  durability. Launch is best-effort: the file store is the fallback when DBOS
  cannot start (e.g. restricted environments), and never raises.
- **`TYPESAFE_API_KEY`** is absent on this machine; Jev runs through
  classifier.dev (`jev-1.13.0` *is* Jev), matching the documented `jev-tests`
  setup. No key required.

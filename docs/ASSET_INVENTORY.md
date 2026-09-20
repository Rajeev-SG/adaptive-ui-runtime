# Local / OSS asset inventory

This file is a **required Phase 0 artefact**.

Its purpose is to prevent duplicate clones, model downloads, browser installs and reimplementation.

Before installing/downloading anything, locate the existing asset and fill in the relevant row.

Do not commit secrets, private page/session content or credentials.

## Inventory

| Capability | Preferred asset/source | Local path / resolution | Version / commit / model revision | Ready? | Action |
|---|---|---|---|---|---|
| Jev fast-path implementation | `Rajeev-SG/jev-tests` | TBD by Phase 0 | TBD | TBD | reuse existing |
| BridgeBrowser | `Rajeev-SG/jev-tests` | TBD | TBD | TBD | reuse/port thinly |
| Jev model/API client | existing Jev/classifier.dev setup | TBD | TBD | TBD | reuse existing credentials/config |
| Fara 4B artifact | asset used by `local_cua` | TBD/cache | exact artifact from results | TBD | **do not redownload if cached** |
| Fara 9B artifact | `local_cua#15` result/cache | TBD/cache | TBD | TBD | use only if benchmark justifies |
| ShowUI/TongUI artifacts | assets used by `local_cua` | TBD/cache | TBD | TBD | optional only |
| local CUA adapters | `Rajeev-SG/local_cua` | TBD | TBD | TBD | reuse |
| benchmark task corpus | `Rajeev-SG/web-automation-microbench` | TBD | TBD | TBD | consume, do not fork |
| Playwriter | existing local install/setup | TBD | TBD | TBD | reuse |
| Browser Relay | existing local install/setup | TBD | TBD | TBD | reuse |
| Browser/Chromium runtime | existing working install | TBD | TBD | TBD | reuse if compatible |
| DBOS | upstream package | env/cache TBD | TBD | TBD | validate, do not recreate |
| Pydantic AI | upstream package | env/cache TBD | TBD | TBD | validate |
| MCP SDK | upstream package | env/cache TBD | TBD | TBD | use |
| Stagehand | upstream OSS / existing test install if present | TBD | TBD | TBD | evaluate only |
| Browser Harness | upstream OSS / existing install if present | TBD | TBD | TBD | evaluate only |
| OpenTelemetry | upstream packages | env/cache TBD | TBD | TBD | reuse |
| Python environment tooling | existing `uv` etc. | TBD | TBD | TBD | reuse |
| Node runtime/package manager if needed | existing local runtime | TBD | TBD | TBD | reuse |

## Local discovery notes

Phase 0 should inspect, rather than blindly modify:

- nearby project directories/worktrees;
- active Python environments;
- `uv`/pip caches;
- Node package/cache state where needed;
- Hugging Face/model caches;
- Playwright/browser caches/installations;
- existing MCP configs;
- existing Playwriter/Browser Relay setup;
- existing running local model/browser services.

## Rules

- **Do not move or duplicate large model artefacts into this repo.**
- **Do not clone a repo already available locally.**
- **Do not reinstall a browser if a compatible existing runtime works.**
- **Do not vendor an OSS project wholesale.**
- **Do not replace a mature subsystem with bespoke code because integration feels inconvenient.**
- Record exact remote provenance even when development resolves to a local path/cache.

## Phase 0 completion

This inventory is considered complete for v1 when every foundational runtime dependency has:
- a local resolution or explicit "not present";
- a canonical upstream source;
- an exact version/revision where relevant;
- a reuse/install decision.

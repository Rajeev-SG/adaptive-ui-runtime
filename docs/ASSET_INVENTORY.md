# Local / OSS asset inventory (Phase 0A — issue #21)

This is the required Phase 0 artefact for the reuse-first preflight (#21).

It records, for every foundational runtime dependency, the **local resolution**
(where this machine finds it), the **canonical provenance** (exact upstream
version/commit/revision for clean installs) and the **reuse decision**.

Do not commit secrets, private page/session content or credentials. Key names are
recorded; no key values are stored here.

Discovery date: 2026-09-20. Host: Apple Silicon MacBook Pro (M5 Pro, 48 GB).

## Summary

- All three related repos are already cloned locally and are current enough to
  consume. **No duplicate clones were created** for discovery.
- Fara-4B and ShowUI-2B model weights are **already fully cached**. Fara-9B is
  partially cached and is **excluded from v1** — it is located for provenance
  only and will not be downloaded further or integrated.
- Playwriter and Browser Relay are installed and healthy; a Playwright Chromium
  is present. **No browser download is required.**
- DBOS / Pydantic AI / MCP SDK / OpenTelemetry are **not yet installed in this
  repo's environment**; they are mature OSS and will be pinned as dependencies in
  #2/#3 rather than reimplemented.
- The only deliberate acquisition this project performs is the runtime's own
  Python environment for `adaptive-ui-runtime`. No foundational model, browser or
  repo asset needs a fresh download.

## Related-repo inventory

| Asset | Local path | Version / commit | Canonical provenance | Decision |
|---|---|---|---|---|
| `adaptive-ui-runtime` (this repo) | `~/Code/adaptive-ui-runtime` | `82ee658` | `github.com/Rajeev-SG/adaptive-ui-runtime` | working copy |
| `jev-tests` | `~/Code/jev-tests` | `4e5ed27` | `github.com/Rajeev-SG/jev-tests` | reuse |
| `local_cua` | `~/Code/local_cua` | `576dd2a` (PR #16 merged) | `github.com/Rajeev-SG/local_cua` | reuse |
| `web-automation-microbench` | `~/Code/web-automation-microbench` | `a82c414` | `github.com/Rajeev-SG/web-automation-microbench` | consume, do not fork |

Additional worktrees exist under `~/.codex-worktrees/` (e.g.
`jev-tests-gh-122-...`, `jev-tests-feat`); they are other sessions' checkouts and
are not used here. No extra clone was made.

## Main inventory

| Capability | Preferred asset/source | Local path / resolution | Version / commit / revision | Ready? | Action |
|---|---|---|---|---|---|
| Jev fast-path implementation | `Rajeev-SG/jev-tests` | `~/Code/jev-tests/src/jev_tests/classifier_policy.py` | jev-tests `4e5ed27`; upstream `jev-ultrafast` pinned in `pyproject.toml` | yes | reuse (thin adapter) |
| Jev model/API client endpoint | classifier.dev (`jev-1.13.0` is Jev) | used by `classifier_policy.py` | `jev-1.13.0` | yes | reuse; **no key required** (free tier) |
| BridgeBrowser | `Rajeev-SG/jev-tests` | `~/Code/jev-tests/src/jev_tests/bridge.py` | jev-tests `4e5ed27` | yes | reuse/port thinly (issue #4) |
| BridgeBrowser transports | Playwriter + Browser Relay via subprocess | same file (`BrowserRelayTransport`, Playwriter transport) | jev-tests `4e5ed27` | yes | reuse |
| Fara 4B artifact | asset used by `local_cua` | `~/.cache/huggingface/hub/models--runanywhere--Fara1.5-4B-mlx-4bit` (7.4 GB, complete) | `runanywhere/Fara1.5-4B-mlx-4bit` rev `9e3987b4c0175...` | yes | **cached — do not redownload** |
| Fara 9B artifact | PR #16 provenance only | `~/.cache/huggingface/hub/models--mlx-community--Fara1.5-9B-8bit` (partial, 983 MB, has `.incomplete` blobs) | `mlx-community/Fara1.5-9B-8bit` | located only | **do NOT download/integrate** (v1 exclusion) |
| ShowUI 2B artifact | asset used by `local_cua` | `~/.cache/huggingface/hub/models--mlx-community--ShowUI-2B-bf16-4bit` (4.1 GB, complete) | `mlx-community/ShowUI-2B-bf16-4bit` | yes | **cached — do not redownload** |
| ShowUI bf16 (alt) | `local_cua` screening | `~/.cache/huggingface/hub/models--prince-canuma--ShowUI-2B-bf16` | `prince-canuma/ShowUI-2B-bf16` | yes | use only if needed |
| UGround-V1-2B | `local_cua` screening (optional) | `~/.cache/huggingface/hub/models--mlx-community--UGround-V1-2B-bf16` | `mlx-community/UGround-V1-2B-bf16` | yes | optional grounder |
| TongUI-3B | `local_cua` screening (optional) | `~/.cache/huggingface/hub/models--Bofeee5675--TongUI-3B` | `Bofeee5675/TongUI-3B` | yes | optional; not preferred |
| local CUA adapters (Fara) | `Rajeev-SG/local_cua` | `~/Code/local_cua/harness/adapters/fara.py` | local_cua `576dd2a` | yes | reuse/adapt thinly |
| local CUA adapters (ShowUI) | `Rajeev-SG/local_cua` | `~/Code/local_cua/harness/adapters/showui.py` | local_cua `576dd2a` | yes | reuse/adapt thinly |
| local CUA executor | `Rajeev-SG/local_cua` | `~/Code/local_cua/harness/browser.py` | local_cua `576dd2a` | yes | reuse for isolated local-work tests |
| benchmark task corpus | `Rajeev-SG/web-automation-microbench` | `~/Code/web-automation-microbench/bench-ext/corpus/tasks` (11 tasks) | microbench `a82c414`; `SOURCE.json` sha256-pinned | yes | **consume, do not fork** |
| benchmark verifiers / pass rule | `Rajeev-SG/web-automation-microbench` | `bench-ext/pass_rule.py`, `bench-ext/benchlib.py` (`VERIFY_JS`) | microbench `a82c414` | yes | consume |
| benchmark Chrome launcher | `Rajeev-SG/web-automation-microbench` | `bench-ext/cft_chrome.py` | microbench `a82c414` | yes | reuse for isolated reps |
| Playwriter | existing local install | `~/Library/pnpm/playwriter` | installed 2026-09 | yes | reuse |
| Browser Relay | existing local install + `relay` wrapper | `~/.local/bin/relay`; profiles default/omnicom/singulyr/chanel | relay health `ok` (2026-09-20) | yes | reuse via `relay` |
| Browser runtime (Chromium) | existing Playwright install | `~/Library/Caches/ms-playwright/chromium-1243` (+1208/1234) | ms-playwright 1243 | yes | **reuse — no browser download** |
| Python env tooling | `uv` | `/opt/homebrew/bin/uv` | 2026-09 | yes | reuse |
| Node / package managers | `node`, `pnpm`, `npm` | `/opt/homebrew/bin/{node,pnpm,npm}` | 2026-09 | yes | reuse if Stagehand evaluated |
| DBOS | upstream package | not installed in this repo env yet | pin in #3 (validate) | no | **install pinned, do not build** |
| Pydantic AI | upstream package | not installed in this repo env yet | pin in #3 (validate) | no | **install pinned, do not build** |
| MCP SDK | upstream package | not installed in this repo env yet | pin in #13 | no | **install pinned, do not build** |
| OpenTelemetry | upstream packages | not installed in this repo env yet | pin in #14 | no | **install pinned, do not build** |
| Stagehand | upstream OSS (node) | not present locally | evaluate in #6 | no | evaluate only |
| Browser Harness | upstream OSS | not present locally | evaluate in #6 | no | evaluate only |

## Credentials (names only — no values stored)

| Need | Resolution | Notes |
|---|---|---|
| Strong manager (OpenRouter) | macOS keychain `codex-openrouter` / `default`; `.env.example:OPENROUTER_API_KEY` | present |
| Jev / classifier.dev | classifier.dev free tier, **no key** (`classifier_policy.py`) | usable without a key |
| DBOS `DATABASE_URL` | SQLite by default for v1 | configure in #3 |
| Playwriter / Browser Relay sessions | existing Chrome profiles via `relay` | configured |

Note: `TYPESAFE_API_KEY` is not present on this machine. The faithful Jev framing
runs through classifier.dev (`jev-1.13.0` *is* Jev), matching the documented
`jev-tests` setup. This measures Jev's decisions, not TypeSafe's latency.

## Existing measured evidence to consume (do not rediscover)

- `jev-tests` `4e5ed27` — live TodoMVC fast path: **Jev 9/10 vs GLM 5/10** across
  Playwriter/Browser Relay; Jev decision p50 ≈ 1.2–1.4 s vs GLM ≈ 2.5–2.6 s;
  Jev+Playwriter median 16.1 s vs GLM 27.1 s (≈40% lower). One Jev Playwriter run
  looped on an already-satisfied action (failure class: repeated action).
  Source: `~/Code/jev-tests/results/browser-fastpath/README.md`.
- `local_cua` `576dd2a` (PR #16) — Fara 4B and 9B both **8/8 grounding**, both
  **T1 2/2, T2 2/2, T3 0/2**, both **0/6** on the DOM/eval-dependent real-work set;
  9B costs 1.8–3.5× latency and 1.6–2.3× memory for the same outcome. Stage-3
  median wall 65 s (4B) vs 228 s (9B). Baseline strong agents pass 3–4/6 on the
  same tasks because they own a DOM/eval loop. Source:
  `~/Code/local_cua/RESULTS.md` §5.3–5.5.
- `web-automation-microbench` `a82c414` — canonical task/reset/verifier corpus and
  the TodoMVC golden verifier in `bench-ext/benchlib.py:VERIFY_JS`.

## Bespoke-code audit

Expected bespoke surface for this runtime (thin glue only):

| Bespoke piece | Why it cannot be reused |
|---|---|
| Domain contracts (`contracts.py`) | integration-specific task/route/observation shapes |
| Thin transport adapters over BridgeBrowser/relay/playwriter | normalise the existing transports behind one protocol |
| Router / policy + explicit budgets | routing thresholds are runtime-specific policy |
| Verifier composition (DOM/URL/file/api/microbench) | composition, not new verification engines |
| Cycle detection + failure classification | small policy layer over existing repair capabilities |
| Bounded recovery orchestration | chooses among existing repairs; does not implement them |
| MCP/CLI surface | thin binding of MCP SDK + CLI to the same code path |
| Evaluation/metrics glue | consumes microbench + OTel; no new benchmark framework |

**Explicitly not bespoke:** workflow engine (DBOS), browser engine/self-healing
(Playwriter/Browser Relay/Stagehand/Browser Harness), Jev (existing), Fara/ShowUI
inference (existing `local_cua` adapters + mlx-vlm), benchmark framework
(microbench), MCP protocol (SDK), tracing backend (OpenTelemetry), model
download/cache manager. No issue has yet recorded a concrete gap justifying any of
these.

## Unavoidable new downloads / installs

| Item | Why unavoidable | Phase |
|---|---|---|
| `adaptive-ui-runtime` Python env (pydantic, DBOS, pydantic-ai, mcp, otel, pytest, ruff, mypy, mlx-vlm, playwright) | this repo's own runnable environment; none of it is a duplicate of a cached model/browser asset | #2–#3 |

No model weights, browser binaries, or related-repo clones need to be downloaded.

## Acceptance (#21)

- [x] `docs/ASSET_INVENTORY.md` completed
- [x] all three related repos located and reusable assets identified
- [x] existing model cache/artifacts identified (Fara-4B, ShowUI-2B complete; Fara-9B located, excluded)
- [x] existing browser/tool installations identified (relay, playwriter, Chromium 1243)
- [x] canonical OSS provenance/versions recorded
- [x] no unnecessary clone/download/install performed
- [x] bespoke scope is demonstrably thin
- [x] unavoidable new downloads/installations explicitly listed before execution

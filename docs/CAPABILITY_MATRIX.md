# Transport / backend capability matrix (issue #6)

Every number below is backed by a committed probe artifact under
`results/probes/` produced by `scripts/probe_transports.py` on the shared
TodoMVC instrument, or by an existing measured artifact cited by path. Nothing
here is asserted from memory.

## How to reproduce

```bash
python scripts/probe_transports.py --transport isolated
PLAYWRITER_SESSION=<id> python scripts/probe_transports.py --transport playwriter --session <id>
AUR_RELAY_PROFILE=<p> BROWSER_RELAY_TAB=<tab> python scripts/probe_transports.py --transport relay
```

Each run writes raw JSON to `results/probes/<transport>.json`.

## Backend presence on this machine (probed, not assumed)

`results/probes/*.json` → `backend_presence`:

| Backend | Installed? | Resolution |
|---|---|---|
| Playwriter | **yes** | `~/Library/pnpm/playwriter`, sessions live |
| Browser Relay | **yes** | `browser-relay` + `~/.local/bin/relay`, 4 profiles |
| Browser Harness | **yes** | `~/.local/bin/browser-harness` v0.1.13 (daemon not running) |
| Stagehand | **no** | no node_modules copy present |
| Chromium (ms-playwright) | **yes** | existing binary, no download |

## Probed capability results (raw: `results/probes/`)

| Probe | isolated | playwriter | relay |
|---|---|---|---|
| navigate ok | yes | yes (361 ms) | yes |
| observe → targets | 4 | 4 (216 ms) | 3–4 (97 ms) |
| can type into textbox | yes | yes | yes |
| typed value round-trips | `probe` | `probe-value` (551 ms) | `probe-value` |
| clean per-run reset | **yes** | no | no |
| stale/absent target fails closed | **yes** | (via stamp revalidation) | (via stamp revalidation) |

Backends with no probe run (Stagehand, Browser Harness) are **not measured here**
and are therefore not claimed.

## Existing measured evidence (consumed, cited by path)

- `web-automation-microbench` Round 2 (`artifacts/2026-09-11`): **Stagehand v4
  1/4 @ 13.1s**, **Browser Harness 2/2 @ 9.9s**, on the shared TodoMVC contract.
- `jev-tests` live fast path: Playwriter+Jev 4/5 @ 16.1 s; Relay+Jev 5/5 @ 13.1 s;
  GLM 4/5 and 1/5. (This repo re-uses this evidence; see `results/browser-fastpath/`
  in jev-tests.)

## Decision

| Backend | Decision | Reason (evidence-backed) |
|---|---|---|
| Playwriter | **integrate as transport** | probed live; existing session |
| Browser Relay | **integrate as transport** | probed live; best measured Jev reliability (5/5) |
| Isolated Chromium | **integrate as transport** | probed live; the only backend with a clean per-run reset, which the benchmarks and CI need |
| Stagehand | **omit from v1** | not installed locally; 1/4 on the shared instrument; adopting it adds a Node runtime + LLM calls on the inner loop for no measured gain here |
| Browser Harness | **omit as an agent-facing route; documented dev/debug escape hatch** | installed (v0.1.13) and 2/2 on the toy instrument, but its distinct value (raw CDP helpers) is a developer tool, not a runtime route; no measured reliability/latency gain over the transports above on a real task class |

## Overlap / hot-path overhead

- The three adopted transports overlap on the core action set and differ on
  session model and reset. No bespoke self-healing was added: stale-target
  handling is transport-native re-stamp plus the runtime's classified recovery.
- No Node stack or new runtime was installed for this issue.

## Not yet covered

- A live Stagehand capability probe (not installed; installing it would violate
  the reuse-first budget for a 1/4 result). Recorded as the boundary for a future
  issue if a real task class shows a drift/healing gap the transports cannot cover.
- Browser Harness end-to-end on a real task class (it is retained as a debug tool,
  not promoted).

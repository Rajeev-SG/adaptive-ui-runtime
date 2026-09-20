# Transport / backend capability matrix (issue #6)

Decision for v1, based on existing local installations and the already-recorded
`web-automation-microbench` results. No new backend is installed to satisfy this
issue — the evidence is consumed.

## Measured evidence (existing, not re-run)

- `web-automation-microbench` Round 2 (`artifacts/2026-09-11`): **Stagehand v4
  1/4 @ 13.1s** on the shared TodoMVC instrument; **Browser Harness 2/2 @ 9.9s**.
- `web-automation-microbench` Round 6/7: thin, one-command-per-step CLIs
  (browser-relay 4.3s, BrowserSkill 4.1s, browser-cli 6.2s) beat own-loop agents
  on speed; vision-first agents were most reliable on messy JS sites but slower.
- `jev-tests` live fast path: Playwriter + Jev 4/5 @ 16.1s, Relay + Jev 5/5 @
  13.1s; GLM baselines 4/5 and 1/5 respectively.

## Matrix

| Capability | Playwriter | Browser Relay | Isolated Chromium | Stagehand | Browser Harness | Runtime owner |
|---|---|---|---|---|---|---|
| navigate/observe/click/type/key/select/scroll | yes | yes | yes | yes | yes | transport adapter |
| existing logged-in session | **yes** | **yes** | no | via CDP | via CDP | Playwriter/Relay |
| clean per-run reset | no | no | **yes** | yes | yes | isolated transport |
| capability flags advertised | yes | yes | yes | n/a | n/a | Transport protocol |
| stale-target fail-closed | yes | yes | yes | partial | n/a | transport + recovery |
| semantic observe/resolve + replay | no | no | no | **yes** | no | Stagehand (if adopted) |
| DOM drift / self-healing | no | no | no | **yes** | partial | Stagehand (if adopted) |
| iframe/shadow-DOM handling | no | no | no | **yes** | partial | Stagehand (if adopted) |
| raw CDP escape hatch | no | no | no | partial | **yes** | dev/debug only |
| measured TodoMVC result | 4/5 (Jev) | 5/5 (Jev) | currently 3/3 (ablation) | **1/4** | 2/2 | — |

## Decision

| Backend | Decision | Reason |
|---|---|---|
| Playwriter | **integrate as transport** | existing session, proven fast path, already required |
| Browser Relay | **integrate as transport** | existing session, best measured Jev reliability (5/5) |
| Isolated Chromium | **integrate as transport** | reproducible clean state for benchmarks/CI, no download |
| Stagehand | **omit from v1** | 1/4 on the shared instrument; no installed copy; its observe/replay/self-healing adds a JS runtime + LLM calls we would have to pay on the inner loop. Revisit only if a task class shows a concrete drift/healing gap the transports cannot cover. |
| Browser Harness | **omit from v1; keep as a documented dev/debug escape hatch** | its unique value (raw CDP helpers) is a developer tool, not an agent-facing route; the microbench 2/2 is on the toy instrument only. |

## Overlap and hot-path overhead

- Playwriter/Relay/Isolated overlap on the core action set; they differ on
  session model (existing vs clean) and transport cost. No bespoke self-healing
  code was added: stale-target handling is transport-native re-stamp + the
  runtime's classified recovery, matching the AGENTS.md self-healing rule.
- No hot-path dependency was added by this issue (nothing installed).

## Not yet covered

- A live Stagehand/Browser Harness capability probe. Deferred deliberately: the
  evidence above already answers the v1 question, and installing a Node stack to
  re-confirm a 1/4 result would violate the reuse-first budget. Recorded as the
  boundary for a future issue.

# Task: adaptive-ui-runtime microbench adapter + screening benchmark

Paste this whole file as the first message of a NEW Codex task (project: `Code`
= /Users/rajeev/Code). Self-contained — no prior thread context needed.

## Goal
Produce a real, same-instrument comparison of adaptive-ui-runtime against the
existing microbench contenders (browser-relay, raw-playwright, BrowserSkill, ...).

## Paths
- Runtime: /Users/rajeev/Code/adaptive-ui-runtime (.venv; CLI `.venv/bin/aur`;
  MCP `.venv/bin/python -m adaptive_ui_runtime serve-mcp`)
- Microbench: /Users/rajeev/Code/web-automation-microbench (harness = bench-ext)
- Chrome for Testing:
  /Users/rajeev/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing
- OpenRouter key: `security find-generic-password -s codex-openrouter -a default -w`

## Read first
1. `bench-ext/benchlib.py` — adapter contract near `run_cli`/`run_rep`
   (name, doc, start()->(handle,obs) pre-timed, act(handle,code)->(obs,elapsed)
   in-loop, verify(handle) post-timed, screenshot, teardown).
2. `bench-ext/runners/browser-use-pi.py` and `skyvern.py` — the **own-loop**
   contender pattern: timed as ONE agent run per rep, NOT one command per step
   (microbench fairness rule). The runtime is an own-loop contender; follow this.
3. `bench-ext/runners/browser-relay.py` — the thin-CLI baseline you're compared to.
4. `bench-ext/cft_chrome.py` — CFT launcher.
   `bench-ext/corpus/report.py` + `docs/benchmark-spec.md` — run-JSON shape + aggregation.

## Verified facts (don't re-derive)
- The runtime's browser attaches to an externally launched Chrome over CDP:
  `playwright.chromium.connect_over_cdp("http://127.0.0.1:<port>")` works against
  cft_chrome Chrome. So the microbench launches Chrome, the runtime drives it,
  and the microbench verifies independently afterwards.
- The runtime exposes `ui.execute` (MCP / CLI / Python `Runtime.execute`). Task
  specs are YAML/JSON and can carry explicit structured `steps`.
- Independent verification must stay the microbench's: read final state via CDP
  with the task's own `verify_js` + `pass_rule`; never trust the runtime's
  `verified` flag. Report BOTH (`runtime_verified` vs `independent_pass`) so any
  disagreement is visible.
- The runtime makes an OpenRouter strong-manager call ONLY on classes needing a
  decision; deterministic/structured classes make 0 model calls. Record
  `manager_calls` and `jev_calls` per rep.

## Deliverable
1. `bench-ext/runners/adaptive-ui-runtime.py` — committed adapter, own-loop
   pattern, one runtime call per rep, untimed CDP verification, standard run JSON.
2. A note (e.g. `bench-ext/runners/ADAPTIVE_UI_RUNTIME.md`) documenting the runtime
   version/commit pin, model config, and explicit comparability caveats (manager
   calls go to OpenRouter; no window-resume semantics like the CLIs; wall time
   includes manager decision latency on decision classes).
3. 2-rep screening on default `todomvc`, then 2 reps on 2-3 real harvested tasks
   (`bench-ext/corpus/tasks/`). Preserve failures; do not skip hard tasks.
4. Results summary vs existing contenders' medians for the SAME task, standard
   columns: pass (independent), median wall, tokens, cost, failure classes.

## Rules
- Reuse-first: import benchlib/verifier; do not fork. No browser downloads,
  no re-cloning repos.
- Do not modify the microbench core harness (`benchlib.py`, `pass_rule.py`,
  `tasks`) — runner only. If a core change seems needed, stop and report.
- Commit in the microbench repo on a focused branch, open a PR, follow that
  repo's CI; do not merge with outstanding review findings.
- Do NOT add the runtime to any agent's default tool set or policy — it is
  deliberately non-default (see ~/.omp/agent/AGENTS.md marker
  `aur-status: available-not-default`).

## Report back
The runtime's measured row vs browser-relay/raw-playwright on the same
instrument, whether independent verification agreed with the runtime's own
verdict, and the explicit limitations. If it loses, say so plainly with numbers.

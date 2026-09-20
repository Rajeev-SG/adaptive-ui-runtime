# Reuse decisions for bespoke surfaces

Per AGENTS.md, any substantial subsystem records why existing software is
insufficient. Every entry below is *thin glue*, not a subsystem replacement.

## Transport adapters (Playwriter / Browser Relay / isolated Chromium)

```text
Need:                    interchangeable browser execution behind one contract
Existing local asset:    BridgeBrowser + transports in jev-tests@4e5ed27; relay/playwriter installed
Existing project code:   jev_tests.bridge (observed-node stamping, stale handling)
Upstream OSS checked:    Playwright (used directly for the isolated transport)
Why reuse/adaptation is insufficient: the transports differ per backend, but no existing package
                         exposes our capability-aware protocol over both CLIs
Smallest bespoke surface: ~1 adapter per transport over the existing CLI/Playwright calls
```

## DBOS durability

```text
Need:                    durable runs, resume without replaying committed side effects
Upstream OSS used:       DBOS 3.0 workflows + steps (no bespoke engine)
Bespoke surface:         registration of one workflow + one module-level step, and eviction
```

## Jev fast path

```text
Need:                    finite-choice browser decisions
Existing project code:   jev-tests classifier_policy.py (faithful two-question framing)
Upstream service used:   classifier.dev (no bespoke model)
Bespoke surface:         HTTP client + threshold gating (no Jev reimplementation)
```

## Local visual workers

```text
Need:                    bounded local grounding/acting
Existing project code:   local_cua adapters (fara.py, showui.py) + cached MLX artefacts
Upstream OSS used:       mlx-vlm
Bespoke surface:         bounded-worker wrapper that refuses non-bounded task classes
```

## Verifier / recovery / router / cycle detector

```text
Need:                    independent verification, classified bounded recovery, routing policy
Upstream OSS checked:    none provides task-level verification composition or this routing policy
Bespoke surface:         small policy modules (verifier.py, recovery.py, router.py) — no browser
                         self-healing framework, no benchmark framework
```

## Benchmark / evaluation

```text
Need:                    ablations over the same execution path
Existing project asset:  web-automation-microbench corpus + pass_rule (consumed, not forked)
Bespoke surface:         run_suite/write_results glue that calls the production Engine
```

## Deliberately NOT built

Workflow engine, browser engine, self-healing framework, Jev clone, model runtime,
MCP protocol stack, tracing backend, benchmark corpus — each is provided by DBOS,
Playwright/Playwriter/relay, Stagehand-if-adopted, jev-tests, mlx-vlm, the MCP SDK,
OpenTelemetry, and web-automation-microbench respectively.

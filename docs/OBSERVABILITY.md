# Tracing, metrics and observability (issue #14)

## Trace model

Every run has a stable `run_id`. Events are appended in memory by `Tracer` and
flushed once to `.aur-traces/<run_id>.json` at run end (not the hot path). Each
event carries `run_id`, monotonic `seq`, `kind`, `at_ms` and a small `data` dict.

Event kinds: `run_start`, `plan`, `subtask_start`, `route`, `route_cascade`,
`action`, `failure`, `repair`, `verify`, `cycle_detected`, `escalate`,
`manager_replan`, `subtask_skipped`, `state_save_failed`, `run_end`.

One run is reconstructable from its trace: plan -> route decisions -> actions ->
verifier results -> recoveries -> final status.

## Metrics (machine-readable, in `RunResult.metrics` and `RunState.metrics`)

`wall_ms`, `actions`, `observations`, `verifications`, `transport_commands`,
`jev_calls`, `fara_calls`, `showui_calls`, `manager_calls`, `replans`, `fallbacks`,
`recoveries`, `loops`, `state_save_failures`, `failure_classes`,
`observe_ms`/`action_ms`/`verify_ms`/`jev_ms` p50/p95, manager call/token counts,
local-worker inference p50, the config snapshot, and the transport name.

## OpenTelemetry-compatible export

Set `AUR_OTEL=1` to open a span per run (`Tracer._start_otel`) and mirror each
event as a span event via the OpenTelemetry API. Export is opt-in so the hot path
stays free of network work; the SDK exporter is configured by the operator's
standard OTel environment, not by this repo (no bespoke tracing backend).

## Overhead

`tests/test_tracing.py::test_observability_overhead_is_small` bounds tracer
overhead on the deterministic path. The tracer buffers in memory and writes once
at flush; events are never written per-action to disk in the hot path.

## Privacy

Raw screenshots and page text stay local (`.aur-traces/` and `.aur-state/` are
gitignored). Committed benchmark artefacts carry aggregate metrics and classified
failure names only — no session content, cookies or private page data.

## Why each fallback occurred

Each `route_cascade`, `repair`, `escalate`, `cycle_detected`, `manager_replan`
and `subtask_skipped` event records the reason, so a reviewer can attribute any
fallback to a route, a failure class, or a budget decision.

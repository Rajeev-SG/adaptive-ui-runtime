# adaptive-ui-runtime

A fast, accuracy-first execution runtime for browser and UI automation.

The runtime gives coding/agent systems **one interface** for UI work while dynamically choosing the fastest reliable execution path underneath: deterministic browser actions, Jev, Playwriter, Browser Relay, local Fara, visual grounding, or a strong long-context model.

## Objective

Optimise lexicographically for:

1. **Correctness / verified task success**
2. **End-to-end wall-clock latency**
3. **Cost**

The runtime must never trade a material loss in verified success for cheaper inference.

## Core idea

```text
Agent (Codex / Cline / OMP / OpenChamber / Claude)
                    |
                MCP / CLI
                    |
          adaptive-ui-runtime
                    |
     +--------------+--------------+
     |              |              |
 deterministic     Jev         bounded Fara
 structured path  fast path    visual worker
     |              |              |
     +--------- browser transports-+
          Playwriter / Browser Relay
          Stagehand / Browser Harness
                    |
             independent verifier
                    |
          success -> return result
          failure -> bounded repair
                  -> strong-model replan
```

The strong model owns long-horizon planning and genuinely ambiguous recovery. It should **not** sit in the inner click-by-click loop when a faster reliable mechanism can advance the workflow.

## Non-negotiable principles

- **Fail closed.** "DONE" from an acting model is never proof of success.
- **Independent verification.** Every state-changing subtask has explicit postconditions checked outside the actor.
- **Bounded workers.** Jev/Fara/other workers get action/time budgets; repeated guessing is forbidden.
- **No thrashing.** Detect identical state/action cycles and escalate immediately.
- **Structured before visual.** API/DOM/accessibility/deterministic execution is preferred when reliable.
- **Route by evidence.** Promotion thresholds come from measured task success, not model reputation.
- **Strong-model context is preserved.** The manager can hold full task/history context while delegating bounded UI work.
- **One agent-facing product surface.** Agents call the runtime, not individual Jev/Fara/browser tools.
- **Reuse, do not reinvent.** Existing mature OSS and the proven code in `local_cua`, `jev-tests`, and `web-automation-microbench` should be reused before bespoke code is written.

## Agent-facing surface

Target MCP/CLI operations:

- `ui.execute` — execute a goal with success criteria and constraints.
- `ui.inspect` — inspect current UI/state without mutation.
- `ui.verify` — independently evaluate success criteria.
- `ui.plan` — return the proposed execution strategy without executing it.
- `ui.status` — current durable run state.
- `ui.resume` — resume a checkpointed run.
- `ui.trace` — machine-readable decision/action/recovery trace.
- `ui.evaluate` — controlled runtime ablations and benchmark execution.

Normal agents should usually use only `ui.execute`.

## Runtime layers

```text
Agent surface      MCP + CLI
Control plane      typed plans / state / budgets / policy
Durability         DBOS (subject to implementation validation)
Manager            strong long-context model via Pydantic AI
Fast routing       Jev / classifier.dev-compatible path
Visual workers     Fara 4B, optional 9B escalation, ShowUI/TongUI where justified
Browser layer      existing BridgeBrowser contract
Transports         Playwriter, Browser Relay, Stagehand, Browser Harness
Verification       DOM/state/file/url/API/screenshot invariants
Recovery           deterministic repair -> route escalation -> manager replan
Telemetry          OpenTelemetry-compatible traces + benchmark metrics
```

See:
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Evaluation contract](docs/EVALUATION.md)
- [Agent integration](docs/AGENT_INTEGRATION.md)
- [Implementation rules](AGENTS.md)

## Existing evidence to reuse

Do not rerun foundational work merely to rediscover it.

- `Rajeev-SG/jev-tests`: Jev browser routing / live fast-path results and `BridgeBrowser`.
- `Rajeev-SG/local_cua`: local Fara / ShowUI / TongUI / UGround screening and the Fara 9B delegation-frontier work.
- `Rajeev-SG/web-automation-microbench`: canonical real-work task/reset/verifier corpus.

These repos are evidence and reusable inputs. This repo owns the **integrated runtime**.

## Definition of done for v1

A coding agent can install/configure the runtime, expose it over MCP and CLI, and run the same real tasks through:

- adaptive runtime,
- strong-model-only baseline,
- no-Jev ablation,
- no-Fara ablation,
- deterministic-only where applicable.

The report must demonstrate, on held-out/repeated tasks:

- verified success rate,
- p50/p95 wall time,
- p50/p95 decision latency,
- strong-model calls/tokens,
- local/cloud inference calls,
- cost,
- recovery/fallback frequency,
- repeated-action-loop count,
- failure classes.

The v1 runtime is accepted only if it is **at least as accurate as the strong baseline within the benchmark evidence and materially faster on the task classes it claims to accelerate**.

The detailed delivery roadmap lives in GitHub Issues.

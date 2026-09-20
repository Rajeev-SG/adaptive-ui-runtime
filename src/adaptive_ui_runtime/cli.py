"""CLI — same runtime code path as MCP (issue #13)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .contracts import RuntimeConfig
from .runtime import Runtime
from .tasks import load_task


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(
            "adaptive-ui-runtime (aur)\n\n"
            "Commands:\n"
            "  execute --task task.yaml [--transport relay|playwriter|fake]\n"
            "  plan --task task.yaml\n"
            "  inspect [--transport ...]\n"
            "  verify --task task.yaml\n"
            "  status <run_id>\n"
            "  resume <run_id> --task task.yaml\n"
            "  trace <run_id>\n"
            "  evaluate --task task.yaml --modes adaptive,strong_only,... [--reps N]\n"
            "  serve-mcp\n"
        )
        return 0

    cmd, rest = argv[0], argv[1:]
    opts = _parse(rest)
    transport = opts.get("transport") or None
    try:
        return _dispatch(cmd, opts, transport)
    except FileNotFoundError as exc:
        print(json.dumps({"error": f"file not found: {exc.filename}"}), file=sys.stderr)
        return 2
    except KeyError as exc:
        print(json.dumps({"error": f"missing required option {exc}"}), file=sys.stderr)
        return 2


def _dispatch(cmd: str, opts: dict, transport: str | None) -> int:

    if cmd == "serve-mcp":
        from .mcp_server import serve
        serve()
        return 0

    if cmd == "execute":
        request, plan, _ = load_task(opts["task"])
        rt = Runtime(RuntimeConfig(mode=opts.get("mode", "adaptive")),
                     transport=transport)
        result = rt.execute(request, plan=plan)
        _print(result.model_dump(mode="json"))
        return 0 if result.verified else 1

    if cmd == "plan":
        request, _, _ = load_task(opts["task"])
        _print(Runtime(transport=transport).plan(request))
        return 0

    if cmd == "inspect":
        _print(Runtime(transport=transport).inspect())
        return 0

    if cmd == "verify":
        request, _, _ = load_task(opts["task"])
        _print(Runtime(transport=transport).verify(request.success_criteria))
        return 0

    if cmd == "status":
        _print(Runtime(transport=transport).status(opts["_pos"][0]))
        return 0

    if cmd == "resume":
        request, plan, _ = load_task(opts["task"])
        _print(Runtime(transport=transport).resume(opts["_pos"][0], request).model_dump(mode="json"))
        return 0

    if cmd == "trace":
        _print(Runtime(transport=transport).trace(opts["_pos"][0]))
        return 0

    if cmd == "evaluate":
        request, plan, _ = load_task(opts["task"])
        modes = [m.strip() for m in opts.get("modes", "adaptive").split(",")]
        out = Runtime(transport=transport or "fake").evaluate(
            request, modes, plan=plan, reps=int(opts.get("reps", 1)))
        print(json.dumps(out, indent=2, default=str))
        outdir = Path(opts.get("out", "results"))
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "eval-summary.json").write_text(json.dumps(out, indent=2))
        return 0

    print(f"unknown command {cmd!r}", file=sys.stderr)
    return 2


def _parse(args: list[str]) -> dict:
    out: dict = {"_pos": []}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            key = a[2:]
            if "=" in key:
                key, val = key.split("=", 1)
                out[key] = val
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                out[key] = args[i + 1]
                i += 1
            else:
                out[key] = True
        else:
            out["_pos"].append(a)
        i += 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())

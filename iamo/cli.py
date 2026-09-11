from __future__ import annotations
import argparse
import json
from .core import IAMO
from .memory import RuntimePaths

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="iamo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("pulse")
    sub.add_parser("status")
    serve = sub.add_parser("serve")
    serve.add_argument("--interval", type=float, default=300.0)
    outcome = sub.add_parser("outcome")
    outcome.add_argument("kind", choices=["social", "iamox", "generic"])
    outcome.add_argument("reward", type=float)
    outcome.add_argument("--signal", type=float, default=1.0)
    outcome.add_argument("--safety", type=float, default=1.0)
    outcome.add_argument("--latency-ms", type=float, default=0.0)
    sub.add_parser("improve")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = IAMO(RuntimePaths.default())
    if args.command == "pulse":
        print(json.dumps(app.heartbeat(), ensure_ascii=False, indent=2))
    elif args.command == "status":
        print(json.dumps(app.state(), ensure_ascii=False, indent=2))
    elif args.command == "serve":
        app.serve(args.interval)
    elif args.command == "outcome":
        app.improver.record_outcome(
            kind=args.kind, reward=args.reward, signal=args.signal,
            safety=args.safety, latency_ms=args.latency_ms,
        )
        print("outcome recorded")
    elif args.command == "improve":
        result = app.improver.improve()
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0

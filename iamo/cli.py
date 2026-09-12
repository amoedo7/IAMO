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
    socialize = sub.add_parser("socialize")
    socialize.add_argument("--budget", type=int, default=3)
    sub.add_parser("grow")
    sub.add_parser("synergies")
    sub.add_parser("synergy-auto")
    result = sub.add_parser("synergy-result")
    result.add_argument("synergy_id")
    result.add_argument("outcome", choices=["success", "fail"])
    result.add_argument("--note", default="")
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
    elif args.command == "socialize":
        result = {
            "observe": app.social.heartbeat(app.improver.policy()["social_read_limit"]),
            "socialize": app.social_life.tick(max(0, args.budget)),
            "relationships": app.friendships.summary(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "grow":
        result = {
            "harvest": app.growth.harvest(3),
            "code_draft": app.code_lab.draft_once(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "synergies":
        print(json.dumps({
            "discover": app.synergy.discover(),
            "summary": app.synergy.summary(),
        }, ensure_ascii=False, indent=2))
    elif args.command == "synergy-auto":
        print(json.dumps(app.synergy.queue_best(), ensure_ascii=False, indent=2))
    elif args.command == "synergy-result":
        print(json.dumps(
            app.synergy.record_result(
                args.synergy_id,
                args.outcome == "success",
                args.note,
            ),
            ensure_ascii=False,
            indent=2,
        ))
    return 0

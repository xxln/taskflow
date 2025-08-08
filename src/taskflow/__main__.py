from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="taskflow",
        description="Taskflow unified entrypoint",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser(
        "cli",
        help="Run CLI (standard or enhanced via bin/task-flow script)",
    )
    sub.add_parser("api", help="Run FastAPI server")

    args, passthrough = parser.parse_known_args()

    if args.cmd == "cli":
        from .cli import main as cli_main
        # Delegate to existing CLI with passthrough args
        sys.argv = ["taskflow-cli", *passthrough]
        cli_main()
        return

    if args.cmd == "api":
        from .server import main as api_main
        api_main()
        return

    # Default help
    parser.print_help()


if __name__ == "__main__":
    main()

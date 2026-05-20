"""Small CLI entrypoint for local Cloud Chamber tooling."""

from __future__ import annotations

import argparse

from cloud_chamber import __version__

ENGINE_NOTE = (
    "CM1 is the high-fidelity simulation engine; Cloud Chamber is the local "
    "experiment builder, run manager, and visualizer."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloud-chamber")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("doctor",),
        help="Run a lightweight local tooling command.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print(ENGINE_NOTE)
        print("No CM1 runtime is required for normal scaffold checks.")
        return 0

    parser.print_help()
    return 0

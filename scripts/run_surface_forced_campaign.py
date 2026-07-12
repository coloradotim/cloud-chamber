#!/usr/bin/env python3
"""Plan, package, queue, ingest, and report a surface-forced sounding campaign."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
BACKEND_VENV_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"

if sys.version_info < (3, 12):
    if BACKEND_VENV_PYTHON.exists() and Path(sys.executable) != BACKEND_VENV_PYTHON:
        os.execv(
            str(BACKEND_VENV_PYTHON),
            [str(BACKEND_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        )
    raise SystemExit("run_surface_forced_campaign.py requires Python 3.12 or newer.")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.surface_forced_campaign import (  # noqa: E402
    CampaignError,
    ingest_campaign,
    package_campaign,
    plan_campaign,
    queue_campaign,
    report_campaign,
    status_campaign,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    selected = set(args.matrix_id) if args.matrix_id else None
    runtime_home = Path(args.runtime_home).expanduser() if args.runtime_home else None
    if not any(
        (args.plan, args.package, args.queue, args.status, args.ingest, args.report)
    ):
        args.plan = True
    try:
        if args.plan:
            plan = plan_campaign(
                Path(args.matrix),
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(plan.model_dump_json(indent=2))
        if args.package:
            result = package_campaign(
                Path(args.matrix),
                runtime_home=runtime_home,
                selected_matrix_ids=selected,
                resume=args.resume,
                force_rerun=args.force_rerun,
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(result.model_dump_json(indent=2))
        if args.queue:
            result = queue_campaign(
                Path(args.matrix),
                runtime_home=runtime_home,
                selected_matrix_ids=selected,
                resume=True,
                include_optional=args.include_optional,
                override_phase_gate=args.override_phase_gate,
                override_reason=args.override_reason,
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(result.model_dump_json(indent=2))
        if args.status:
            result = status_campaign(
                Path(args.matrix),
                runtime_home=runtime_home,
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(result.model_dump_json(indent=2))
        if args.ingest:
            result = ingest_campaign(
                Path(args.matrix),
                runtime_home=runtime_home,
                selected_matrix_ids=selected,
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(result.model_dump_json(indent=2))
        if args.report:
            artifacts = report_campaign(
                Path(args.matrix),
                runtime_home=runtime_home,
                report_path=Path(args.report_path).expanduser()
                if args.report_path
                else None,
                summary_json_path=(
                    Path(args.summary_json_path).expanduser()
                    if args.summary_json_path
                    else None
                ),
                allow_absolute_local_paths=args.allow_absolute_local_paths,
            )
            print(json.dumps(artifacts.model_dump(mode="json"), indent=2))
    except CampaignError as exc:
        print(f"surface-forced-campaign: {exc}", file=sys.stderr)
        return 2

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a checked-in surface-forced observed-sounding campaign matrix."
    )
    parser.add_argument(
        "--matrix", required=True, help="Campaign matrix YAML/JSON path."
    )
    parser.add_argument(
        "--runtime-home",
        help="Cloud Chamber runtime home. Defaults to settings/CLOUD_CHAMBER_RUNTIME_HOME.",
    )
    parser.add_argument(
        "--matrix-id",
        action="append",
        default=[],
        help="Limit package/queue/ingest operations to one matrix_id. Repeatable.",
    )
    parser.add_argument(
        "--allow-absolute-local-paths",
        action="store_true",
        help=(
            "Allow absolute local IGRA source paths for local-only matrices. Do not commit "
            "matrices containing machine-private paths."
        ),
    )
    parser.add_argument(
        "--plan", action="store_true", help="Validate and print planned runs."
    )
    parser.add_argument(
        "--package", action="store_true", help="Create dry-run packages."
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Create packages if needed and queue selected runs locally or on LAN.",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Include optional matrix rows when queueing without explicit --matrix-id.",
    )
    parser.add_argument(
        "--override-phase-gate",
        action="store_true",
        help="Allow queueing post-Phase-1 rows before the automatic phase gate passes.",
    )
    parser.add_argument(
        "--override-reason",
        help="Reason persisted when --override-phase-gate is used.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Summarize campaign state from manifests, queue state, and runtime files.",
    )
    parser.add_argument(
        "--ingest", action="store_true", help="Ingest completed run outputs."
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write markdown and JSON campaign summary artifacts.",
    )
    parser.add_argument(
        "--report-path",
        help="Override markdown report path. Defaults to the matrix commit_report_path.",
    )
    parser.add_argument(
        "--summary-json-path",
        help="Override JSON summary path. Defaults to runtime campaigns/<id>/campaign-summary.json.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing campaign packages with the same stable resume identity.",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Overwrite an existing generated package for selected rows.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())

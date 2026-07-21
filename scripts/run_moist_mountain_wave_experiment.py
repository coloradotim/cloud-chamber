#!/usr/bin/env python3
"""Package, explicitly execute, and evaluate issue #407's one authorized process."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
BACKEND_VENV_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"

if (
    BACKEND_VENV_PYTHON.exists()
    and Path(sys.executable).resolve() != BACKEND_VENV_PYTHON.resolve()
):
    os.execv(
        str(BACKEND_VENV_PYTHON),
        [str(BACKEND_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
    )
if sys.version_info < (3, 12):  # noqa: UP036
    raise SystemExit(
        "run_moist_mountain_wave_experiment.py requires Python 3.12 or newer."
    )

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError  # noqa: E402
from cloud_chamber.moist_mountain_wave_case import (  # noqa: E402
    MoistMountainWaveCaseError,
    evaluate_moist_mountain_wave_run,
    generate_moist_mountain_wave_package,
    load_moist_mountain_wave_package,
    preflight_package_for_execution,
    write_moist_mountain_wave_evidence,
)
from cloud_chamber.mountain_wave_case import MountainWaveCaseError  # noqa: E402
from cloud_chamber.run_manifest import LifecycleState  # noqa: E402
from cloud_chamber.settings import load_settings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    runtime_home = Path(args.runtime_home).expanduser() if args.runtime_home else None
    settings = load_settings(home=runtime_home)
    run_id = args.run_id or _default_run_id()

    try:
        package_dir = settings.runtime_home.expanduser() / "runs" / run_id
        if args.execute and package_dir.exists():
            package = load_moist_mountain_wave_package(settings=settings, run_id=run_id)
        else:
            package = generate_moist_mountain_wave_package(
                settings=settings, run_id=run_id
            )
        preflight = preflight_package_for_execution(settings=settings, package=package)
        if not preflight.passed:
            raise MoistMountainWaveCaseError(
                "Hard execution preflight did not fully pass."
            )
        if not args.execute:
            print(
                json.dumps(
                    {
                        "status": "source_locked_package_and_hard_preflight_complete_not_executed",
                        "run_id": run_id,
                        "manifest_path": str(package.manifest_path),
                        "case_manifest_path": str(package.case_manifest_path),
                        "execution_preflight": str(
                            package.package_dir / "execution_preflight.json"
                        ),
                        "execution_requires_explicit_flag": "--execute",
                    },
                    indent=2,
                )
            )
            return 0

        manager = LocalRunManager(settings=settings)
        status = manager.launch(package.manifest_path)
        try:
            while status.lifecycle_state in {
                LifecycleState.QUEUED,
                LifecycleState.RUNNING,
            }:
                time.sleep(args.poll_seconds)
                status = manager.status(package.manifest_path)
        except KeyboardInterrupt:
            manager.cancel()
            raise

        if status.lifecycle_state != LifecycleState.COMPLETED or status.exit_code != 0:
            print(
                json.dumps(
                    {
                        "status": "single_authorized_process_failed_no_retry_permitted",
                        "run_id": run_id,
                        "lifecycle_state": status.lifecycle_state.value,
                        "exit_code": status.exit_code,
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        evidence = evaluate_moist_mountain_wave_run(settings=settings, package=package)
        evidence_path = package.package_dir / "moist_mountain_wave_evidence.json"
        write_moist_mountain_wave_evidence(evidence_path, evidence)
        print(
            json.dumps(
                {
                    "status": "single_authorized_process_completed_and_evaluated",
                    "run_id": run_id,
                    "manifest_path": str(package.manifest_path),
                    "evidence_path": str(evidence_path),
                    "wall_clock_seconds": evidence.runtime_integrity[
                        "wall_clock_seconds"
                    ],
                    "peak_ql_kg_kg": evidence.cloud_and_wave["peak_cloud_frame"][
                        "maximum_ql_kg_kg"
                    ],
                    "predeclared_checks": evidence.predeclared_checks,
                    "smoke_tuning_retry_or_second_process": False,
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "moist-mountain-wave: authorized process canceled; no retry is permitted",
            file=sys.stderr,
        )
        return 130
    except (
        MoistMountainWaveCaseError,
        MountainWaveCaseError,
        LocalRunManagerError,
    ) as exc:
        print(f"moist-mountain-wave: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the exact source-locked moist mountain-wave package. Execution is "
            "opt-in and limited to one complete 4000-second CM1 process."
        )
    )
    parser.add_argument("--run-id", help="Runtime-local technical run identifier.")
    parser.add_argument(
        "--runtime-home",
        help="Cloud Chamber runtime home. Defaults to configured local settings.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="After repeated hard preflight passes, start the one authorized CM1 process.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help="Status polling interval while the authorized process is active.",
    )
    return parser


def _default_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"moist-mountain-wave-toy-1972-{timestamp}"


if __name__ == "__main__":
    raise SystemExit(main())

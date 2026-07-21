#!/usr/bin/env python3
"""Package, explicitly execute, and evaluate the one authorized Gate B run."""

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

if BACKEND_VENV_PYTHON.exists() and Path(sys.executable).resolve() != BACKEND_VENV_PYTHON.resolve():
    os.execv(
        str(BACKEND_VENV_PYTHON),
        [str(BACKEND_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
    )
if sys.version_info < (3, 12):  # noqa: UP036 - cover environments without a repository venv.
    raise SystemExit("run_dry_mountain_wave_benchmark.py requires Python 3.12 or newer.")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError  # noqa: E402
from cloud_chamber.mountain_wave_case import (  # noqa: E402
    MountainWaveCaseError,
    evaluate_mountain_wave_run,
    generate_mountain_wave_package,
    load_mountain_wave_package,
    preflight_package_for_execution,
    write_mountain_wave_run_evidence,
)
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
            package = load_mountain_wave_package(settings=settings, run_id=run_id)
        else:
            package = generate_mountain_wave_package(settings=settings, run_id=run_id)
        if not args.execute:
            print(
                json.dumps(
                    {
                        "status": "package_and_preflight_complete_not_executed",
                        "run_id": run_id,
                        "manifest_path": str(package.manifest_path),
                        "case_manifest_path": str(package.case_manifest_path),
                        "namelist_audit_path": str(package.namelist_audit_path),
                        "storage_estimate_path": str(package.storage_estimate_path),
                        "execution_requires_explicit_flag": "--execute",
                    },
                    indent=2,
                )
            )
            return 0

        preflight = preflight_package_for_execution(settings=settings, package=package)
        if not preflight.passed:
            raise MountainWaveCaseError("Execution preflight did not pass every check.")

        manager = LocalRunManager(settings=settings)
        status = manager.launch(package.manifest_path)
        try:
            while status.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
                time.sleep(args.poll_seconds)
                status = manager.status(package.manifest_path)
        except KeyboardInterrupt:
            manager.cancel()
            raise

        if status.lifecycle_state != LifecycleState.COMPLETED or status.exit_code != 0:
            print(
                json.dumps(
                    {
                        "status": "single_authorized_run_failed_no_rerun_permitted",
                        "run_id": run_id,
                        "lifecycle_state": status.lifecycle_state.value,
                        "exit_code": status.exit_code,
                        "manifest_path": str(package.manifest_path),
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        evidence = evaluate_mountain_wave_run(settings=settings, package=package)
        evidence_path = package.package_dir / "mountain_wave_run_evidence.json"
        write_mountain_wave_run_evidence(evidence_path, evidence)
        report_path = package.package_dir / "dry_run_report.json"
        report_path.write_text(
            json.dumps(
                {
                    "status": "completed_and_native_output_evaluated",
                    "case_id": evidence.case_id,
                    "run_id": evidence.run_id,
                    "implementation_commit": evidence.implementation_commit,
                    "evidence_path": str(evidence_path),
                    "lifecycle": evidence.lifecycle,
                    "model_output_count": evidence.output_inventory["actual_model_output_count"],
                    "model_netcdf_bytes": evidence.output_inventory["total_model_netcdf_bytes"],
                    "active_top_m": evidence.terrain_and_coordinates[
                        "active_top_from_final_nominal_zf_m"
                    ],
                    "netcdf_scalar_ztop_m": evidence.terrain_and_coordinates[
                        "netcdf_scalar_ztop_m"
                    ],
                    "runtime_integrity": evidence.runtime_integrity,
                    "run_recipe": None,
                    "recipe_id": None,
                    "cloud_world_id": None,
                },
                indent=2,
                default=str,
            )
            + "\n"
        )
        print(
            json.dumps(
                {
                    "status": "single_authorized_run_completed_and_evaluated",
                    "run_id": run_id,
                    "manifest_path": str(package.manifest_path),
                    "evidence_path": str(evidence_path),
                    "model_output_count": evidence.output_inventory["actual_model_output_count"],
                    "model_netcdf_bytes": evidence.output_inventory["total_model_netcdf_bytes"],
                    "wall_clock_seconds": evidence.runtime_integrity["wall_clock_seconds"],
                    "floating_point_flags": evidence.runtime_integrity["floating_point_flags"],
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "dry-mountain-wave: the authorized process was canceled; no rerun is permitted",
            file=sys.stderr,
        )
        return 130
    except (MountainWaveCaseError, LocalRunManagerError) as exc:
        print(f"dry-mountain-wave: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the exact official CM1 r21.1 dry mountain-wave package. "
            "Execution is opt-in and limited to one complete 2160-second process."
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
        help="After all repeated preflight checks pass, start the one authorized CM1 process.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=1.0,
        help="Status polling interval while the authorized process is active.",
    )
    return parser


def _default_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"dry-mountain-wave-official-{timestamp}"


if __name__ == "__main__":
    raise SystemExit(main())

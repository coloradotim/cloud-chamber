#!/usr/bin/env python3
"""Package, preflight, and explicitly execute issue #416's one authorized process."""

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
        "run_quarter_circle_supercell_benchmark.py requires Python 3.12 or newer."
    )

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.run_manifest import LifecycleState  # noqa: E402
from cloud_chamber.settings import load_settings  # noqa: E402
from cloud_chamber.supercell_benchmark import (  # noqa: E402
    SupercellBenchmarkError,
    evaluate_supercell_run,
    generate_supercell_package,
    load_supercell_package,
    preflight_supercell_package,
    write_supercell_evidence,
    write_supercell_run_report,
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    runtime_home = Path(args.runtime_home).expanduser() if args.runtime_home else None
    settings = load_settings(home=runtime_home)
    run_id = args.run_id or _default_run_id()
    try:
        if args.evaluate_existing:
            if args.run_id is None:
                raise SupercellBenchmarkError(
                    "Existing-output evaluation requires the exact existing --run-id."
                )
            package = load_supercell_package(settings=settings, run_id=run_id)
            evidence = evaluate_supercell_run(settings=settings, package=package)
            evidence_path = package.package_dir / "supercell_gate_b_evidence.json"
            write_supercell_evidence(evidence_path, evidence)
            report_path = (
                REPO_ROOT
                / "docs/research/storms/canonical-deep-convection-run-report.md"
            )
            write_supercell_run_report(report_path, evidence)
            print(
                json.dumps(
                    {
                        "status": "preserved_output_evaluated_and_reported_no_process_started",
                        "run_id": run_id,
                        "implementation_commit": package.implementation_commit,
                        "evaluation_commit": evidence.evaluation_commit,
                        "evidence_path": str(evidence_path),
                        "report_path": str(report_path),
                        "wall_clock_seconds": evidence.runtime_integrity[
                            "wall_clock_seconds"
                        ],
                        "retained_bytes": evidence.runtime_integrity["artifact_bytes"][
                            "total"
                        ],
                        "final_disposition": evidence.final_disposition,
                        "process_started": False,
                    },
                    indent=2,
                )
            )
            return 0
        if args.preflight or args.execute:
            if args.run_id is None:
                raise SupercellBenchmarkError(
                    "Preflight and execution require the exact existing --run-id."
                )
            package = load_supercell_package(settings=settings, run_id=run_id)
            preflight = preflight_supercell_package(settings=settings, package=package)
            if not preflight.passed:
                raise SupercellBenchmarkError(
                    "Hard launch preflight did not fully pass."
                )
            if args.preflight:
                print(
                    json.dumps(
                        {
                            "status": "hard_launch_preflight_complete_not_executed",
                            "run_id": run_id,
                            "implementation_commit": package.implementation_commit,
                            "checks": preflight.checks,
                            "available_free_bytes": preflight.storage.available_free_bytes,
                            "process_started": False,
                        },
                        indent=2,
                    )
                )
                return 0
        else:
            package = generate_supercell_package(settings=settings, run_id=run_id)
            print(
                json.dumps(
                    {
                        "status": "source_locked_package_complete_not_executed",
                        "run_id": run_id,
                        "manifest_path": str(package.manifest_path),
                        "case_manifest_path": str(package.case_manifest_path),
                        "next_command": (
                            "scripts/run_quarter_circle_supercell_benchmark.py "
                            f"--run-id {run_id} --preflight"
                        ),
                        "execution_requires_explicit_flag": "--execute",
                    },
                    indent=2,
                )
            )
            return 0

        from cloud_chamber.local_run_manager import (
            LocalRunManager,
            LocalRunManagerError,
        )

        manager = LocalRunManager(settings=settings)
        try:
            status = manager.launch(package.manifest_path)
        except LocalRunManagerError as exc:
            raise SupercellBenchmarkError(str(exc)) from exc
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

        evidence = evaluate_supercell_run(settings=settings, package=package)
        evidence_path = package.package_dir / "supercell_gate_b_evidence.json"
        write_supercell_evidence(evidence_path, evidence)
        report_path = (
            REPO_ROOT / "docs/research/storms/canonical-deep-convection-run-report.md"
        )
        write_supercell_run_report(report_path, evidence)
        print(
            json.dumps(
                {
                    "status": "single_authorized_process_completed_evaluated_and_reported",
                    "run_id": run_id,
                    "implementation_commit": package.implementation_commit,
                    "evidence_path": str(evidence_path),
                    "report_path": str(report_path),
                    "wall_clock_seconds": evidence.runtime_integrity[
                        "wall_clock_seconds"
                    ],
                    "retained_bytes": evidence.runtime_integrity["artifact_bytes"][
                        "total"
                    ],
                    "final_disposition": evidence.final_disposition,
                    "smoke_retry_rerun_or_tuning": False,
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "supercell-gate-b: process canceled; no retry or rerun is permitted",
            file=sys.stderr,
        )
        return 130
    except SupercellBenchmarkError as exc:
        print(f"supercell-gate-b: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Package the exact stock CM1 r21.1 quarter-circle supercell benchmark. "
            "Preflight and the one full process are separate opt-in modes."
        )
    )
    parser.add_argument("--run-id", help="Runtime-local technical run identifier.")
    parser.add_argument(
        "--runtime-home",
        help="Cloud Chamber runtime home. Defaults to configured local settings.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Rehash and hard-preflight an existing package without starting CM1.",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Re-run hard preflight, then start the one authorized 7,200-second process.",
    )
    mode.add_argument(
        "--evaluate-existing",
        action="store_true",
        help="Evaluate and report an existing completed run without starting CM1.",
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
    return f"quarter-circle-supercell-official-{timestamp}"


if __name__ == "__main__":
    raise SystemExit(main())

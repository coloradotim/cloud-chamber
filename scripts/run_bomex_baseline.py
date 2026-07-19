#!/usr/bin/env python3
"""Package, execute, ingest, and evaluate one canonical BOMEX baseline run."""

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

if sys.version_info < (3, 12):
    if BACKEND_VENV_PYTHON.exists() and Path(sys.executable) != BACKEND_VENV_PYTHON:
        os.execv(
            str(BACKEND_VENV_PYTHON),
            [str(BACKEND_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        )
    raise SystemExit("run_bomex_baseline.py requires Python 3.12 or newer.")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.bomex_case import (  # noqa: E402
    BomexCaseError,
    BomexVariant,
    build_bomex_run_evidence,
    generate_bomex_package,
    write_bomex_run_evidence,
)
from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError  # noqa: E402
from cloud_chamber.result_ingest import ResultIngestError, ingest_completed_run  # noqa: E402
from cloud_chamber.run_manifest import LifecycleState  # noqa: E402
from cloud_chamber.settings import load_settings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    variant = BomexVariant(args.variant)
    runtime_home = Path(args.runtime_home).expanduser() if args.runtime_home else None
    settings = load_settings(home=runtime_home)
    run_id = args.run_id or _default_run_id(variant)

    try:
        package = generate_bomex_package(
            settings=settings,
            variant=variant,
            run_id=run_id,
            allow_overwrite=args.allow_overwrite,
        )
        if args.package_only:
            print(
                json.dumps(
                    {
                        "status": "packaged",
                        "run_id": run_id,
                        "variant": variant.value,
                        "manifest_path": str(package.manifest_path),
                        "case_manifest_path": str(package.case_manifest_path),
                    },
                    indent=2,
                )
            )
            return 0

        manager = LocalRunManager(settings=settings)
        started = time.monotonic()
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
        wall_clock_seconds = time.monotonic() - started
        if status.lifecycle_state != LifecycleState.COMPLETED or status.exit_code != 0:
            print(
                json.dumps(
                    {
                        "status": "run_failed",
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

        result = ingest_completed_run(package.manifest_path)
        evidence = build_bomex_run_evidence(
            result, wall_clock_seconds=wall_clock_seconds
        )
        evidence_path = package.package_dir / "bomex_run_evidence.json"
        write_bomex_run_evidence(evidence_path, evidence)
        print(
            json.dumps(
                {
                    "status": "completed_ingested_and_evaluated",
                    "run_id": run_id,
                    "result_id": result.result_id,
                    "variant": variant.value,
                    "manifest_path": str(package.manifest_path),
                    "result_metadata_path": str(
                        package.package_dir / "result_metadata.json"
                    ),
                    "evidence_path": str(evidence_path),
                    "runtime_integrity_state": evidence.runtime_integrity_state,
                    "missing_required_fields": evidence.missing_required_fields,
                    "wall_clock_seconds": wall_clock_seconds,
                    "netcdf_output_bytes": evidence.netcdf_output_bytes,
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("bomex-baseline: canceled", file=sys.stderr)
        return 130
    except (BomexCaseError, LocalRunManagerError, ResultIngestError) as exc:
        print(f"bomex-baseline: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one deterministic canonical BOMEX smoke or six-hour case."
    )
    parser.add_argument(
        "--variant", required=True, choices=[variant.value for variant in BomexVariant]
    )
    parser.add_argument("--run-id", help="Runtime-local run identifier.")
    parser.add_argument(
        "--runtime-home",
        help="Cloud Chamber runtime home. Defaults to settings/CLOUD_CHAMBER_RUNTIME_HOME.",
    )
    parser.add_argument(
        "--package-only",
        action="store_true",
        help="Generate and verify the package without launching CM1.",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Replace an existing package with the same run id before execution.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help="Status polling interval while CM1 is active.",
    )
    return parser


def _default_run_id(variant: BomexVariant) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{variant.value}-{variant.duration_seconds}s-{timestamp}-{os.getpid()}"


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Package or serially execute issue #420's four final presentation runs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
BACKEND_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"
if (
    BACKEND_PYTHON.exists()
    and Path(sys.executable).resolve() != BACKEND_PYTHON.resolve()
):
    os.execv(str(BACKEND_PYTHON), [str(BACKEND_PYTHON), __file__, *sys.argv[1:]])
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.local_run_manager import LocalRunManager  # noqa: E402
from cloud_chamber.presentation_runs import (  # noqa: E402
    MINIMUM_POST_RUN_FREE_BYTES,
    PRESENTATION_RUN_SPECS,
    PresentationRunError,
    aggregate_estimated_bytes,
    generate_presentation_package,
    load_presentation_package,
    validate_completed_presentation_run,
    verify_presentation_package,
)
from cloud_chamber.run_manifest import LifecycleState  # noqa: E402
from cloud_chamber.settings import load_settings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--package", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--runtime-home")
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    args = parser.parse_args(argv)
    settings = load_settings(
        home=Path(args.runtime_home).expanduser() if args.runtime_home else None
    )
    try:
        if args.package:
            estimate = aggregate_estimated_bytes(settings)
            available = shutil.disk_usage(settings.runtime_home.expanduser()).free
            if available < estimate + MINIMUM_POST_RUN_FREE_BYTES:
                raise PresentationRunError(
                    f"Aggregate storage preflight failed: {available} < "
                    f"{estimate + MINIMUM_POST_RUN_FREE_BYTES}."
                )
            packages = [
                generate_presentation_package(settings=settings, spec=spec)
                for spec in PRESENTATION_RUN_SPECS
            ]
            print(
                json.dumps(
                    {
                        "status": "four_packages_ready_no_cm1_started",
                        "estimated_retained_bytes": estimate,
                        "available_free_bytes": available,
                        "runs": [
                            package.model_dump(mode="json") for package in packages
                        ],
                    },
                    indent=2,
                )
            )
            return 0

        completed = []
        for spec in PRESENTATION_RUN_SPECS:
            package = load_presentation_package(settings=settings, spec=spec)
            verify_presentation_package(
                settings=settings, spec=spec, require_clean_head=True
            )
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
            if (
                status.lifecycle_state != LifecycleState.COMPLETED
                or status.exit_code != 0
            ):
                raise PresentationRunError(
                    f"Final run failed; sequence stopped without retry: {spec.run_id} "
                    f"({status.lifecycle_state.value}, {status.exit_code})."
                )
            evidence = validate_completed_presentation_run(settings=settings, spec=spec)
            completed.append(evidence.model_dump(mode="json"))
            print(
                json.dumps(
                    {
                        "status": "presentation_run_completed",
                        "run_id": spec.run_id,
                        "runtime_seconds": evidence.runtime_seconds,
                        "history_count": evidence.history_count,
                        "retained_run_bytes": evidence.retained_run_bytes,
                    }
                ),
                flush=True,
            )
        print(
            json.dumps(
                {"status": "four_final_runs_completed", "runs": completed}, indent=2
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "Presentation run sequence canceled; no retry is authorized.",
            file=sys.stderr,
        )
        return 130
    except Exception as exc:
        print(f"presentation-runs: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

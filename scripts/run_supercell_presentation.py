#!/usr/bin/env python3
"""Package, preflight, execute, or validate issue #421's bounded CM1 processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
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
from cloud_chamber.run_manifest import LifecycleState, load_run_manifest  # noqa: E402
from cloud_chamber.settings import load_settings  # noqa: E402
from cloud_chamber.supercell_presentation import (  # noqa: E402
    SupercellPresentationError,
    generate_presentation_package,
    load_presentation_package,
    spec_for_kind,
    validate_completed_presentation_run,
    verify_presentation_package,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--package", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--validate", action="store_true")
    parser.add_argument("--kind", choices=("characterization", "final"), required=True)
    parser.add_argument("--runtime-home")
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    args = parser.parse_args(argv)
    settings = load_settings(
        home=Path(args.runtime_home).expanduser() if args.runtime_home else None
    )
    spec = spec_for_kind(args.kind)
    try:
        if args.package:
            package = generate_presentation_package(settings=settings, spec=spec)
            print(
                json.dumps(
                    {
                        "status": "presentation_package_ready_no_process_started",
                        "kind": spec.kind,
                        "run_id": spec.run_id,
                        "manifest_path": str(package.manifest_path),
                        "process_started": False,
                    },
                    indent=2,
                )
            )
            return 0
        package = load_presentation_package(settings=settings, spec=spec)
        if args.preflight:
            preflight = verify_presentation_package(
                settings=settings,
                package=package,
                require_clean_head=True,
            )
            print(
                json.dumps(
                    {
                        "status": "hard_preflight_complete_no_process_started",
                        "kind": spec.kind,
                        "run_id": spec.run_id,
                        "checks": preflight.checks,
                        "storage": preflight.storage.model_dump(mode="json"),
                        "process_started": False,
                    },
                    indent=2,
                )
            )
            return 0
        if args.validate:
            evidence = validate_completed_presentation_run(
                settings=settings,
                package=package,
                peak_rss_bytes=_recorded_peak_rss(package.package_dir),
            )
            print(json.dumps(evidence.model_dump(mode="json"), indent=2))
            return 0

        preflight = verify_presentation_package(
            settings=settings,
            package=package,
            require_clean_head=True,
        )
        if not preflight.passed:
            raise SupercellPresentationError("Hard launch preflight did not pass.")
        manager = LocalRunManager(settings=settings)
        status = manager.launch(package.manifest_path)
        peak_rss_bytes = 0
        try:
            while status.lifecycle_state in {
                LifecycleState.QUEUED,
                LifecycleState.RUNNING,
            }:
                manifest = load_run_manifest(package.manifest_path)
                if manifest.execution.process_id is not None:
                    peak_rss_bytes = max(
                        peak_rss_bytes,
                        _rss_bytes(manifest.execution.process_id),
                    )
                time.sleep(args.poll_seconds)
                status = manager.status(package.manifest_path)
        except KeyboardInterrupt:
            manager.cancel()
            raise
        _write_resource_monitor(package.package_dir, peak_rss_bytes)
        if status.lifecycle_state != LifecycleState.COMPLETED or status.exit_code != 0:
            print(
                json.dumps(
                    {
                        "status": "authorized_process_failed_no_retry_permitted",
                        "kind": spec.kind,
                        "run_id": spec.run_id,
                        "lifecycle_state": status.lifecycle_state.value,
                        "exit_code": status.exit_code,
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2
        evidence = validate_completed_presentation_run(
            settings=settings,
            package=package,
            peak_rss_bytes=peak_rss_bytes or None,
        )
        print(
            json.dumps(
                {
                    "status": "authorized_process_completed_and_validated",
                    "kind": spec.kind,
                    "run_id": spec.run_id,
                    "runtime_seconds": evidence.runtime_seconds,
                    "peak_rss_bytes": evidence.peak_rss_bytes,
                    "history_count": evidence.history_count,
                    "numbered_history_bytes": evidence.numbered_history_bytes,
                    "retained_run_bytes": evidence.retained_run_bytes,
                    "retry_or_tuning_process_started": False,
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "Supercell presentation process canceled; no retry is authorized.",
            file=sys.stderr,
        )
        return 130
    except Exception as exc:
        print(f"supercell-presentation: {exc}", file=sys.stderr)
        return 2


def _rss_bytes(process_id: int) -> int:
    completed = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(process_id)],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return int(completed.stdout.strip()) * 1024
    except ValueError:
        return 0


def _write_resource_monitor(package_dir: Path, peak_rss_bytes: int) -> None:
    (package_dir / "resource_monitor.json").write_text(
        json.dumps({"peak_rss_bytes": peak_rss_bytes}, indent=2) + "\n"
    )


def _recorded_peak_rss(package_dir: Path) -> int | None:
    path = package_dir / "resource_monitor.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text()).get("peak_rss_bytes")
    return int(value) if isinstance(value, int) and value > 0 else None


if __name__ == "__main__":
    raise SystemExit(main())

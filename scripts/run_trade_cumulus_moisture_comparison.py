#!/usr/bin/env python3
"""Run the one approved matched Trade Cumulus moisture comparison."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
if sys.version_info < (3, 12):
    raise SystemExit(
        "run_trade_cumulus_moisture_comparison.py requires Python 3.12 or newer."
    )

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cloud_chamber.bomex_case import (  # noqa: E402
    BomexCaseError,
    collect_cm1_provenance,
    verified_clean_git_commit,
)
from cloud_chamber.local_run_manager import (  # noqa: E402
    LocalRunManager,
    LocalRunManagerError,
)
from cloud_chamber.result_ingest import (  # noqa: E402
    ResultIngestError,
    ResultMetadata,
    get_result_metadata,
    ingest_completed_run,
)
from cloud_chamber.run_manifest import LifecycleState  # noqa: E402
from cloud_chamber.settings import CloudChamberSettings, load_settings  # noqa: E402
from cloud_chamber.trade_cumulus_moisture_comparison import (  # noqa: E402
    MINIMUM_FREE_BYTES,
    STAGE4_RESULT_ID,
    PackageComparisonProof,
    TradeCumulusMatchedPackage,
    TradeCumulusMoistureComparisonError,
    TradeCumulusMoistureState,
    TradeCumulusPairedEvidence,
    TradeCumulusRunEvidence,
    TradeCumulusRunLength,
    build_joint_lens_preparation,
    build_paired_evidence,
    build_trade_cumulus_run_evidence,
    compare_matched_packages,
    compare_stage4_baseline,
    generate_trade_cumulus_matched_package,
    verify_smoke_full_equivalence,
    write_paired_evidence,
    write_trade_cumulus_run_evidence,
)


@dataclass(frozen=True)
class _CompletedRun:
    result: ResultMetadata
    evidence: TradeCumulusRunEvidence
    evidence_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    runtime_home = Path(args.runtime_home).expanduser() if args.runtime_home else None
    settings = load_settings(home=runtime_home)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        implementation_commit = verified_clean_git_commit()
        provenance = collect_cm1_provenance(settings)
        preserved = _verify_preserved_stage4_result(settings)
        initial_free_bytes = _free_bytes(settings)
        if initial_free_bytes < MINIMUM_FREE_BYTES:
            raise TradeCumulusMoistureComparisonError(
                f"Preflight requires at least {MINIMUM_FREE_BYTES} free bytes; "
                f"found {initial_free_bytes}."
            )
        packages = _generate_all_packages(
            settings=settings,
            timestamp=timestamp,
            implementation_commit=implementation_commit,
        )
        proofs = _verify_all_packages(packages)
        _verify_execution_commit(implementation_commit)

        baseline_smoke = _run_one(
            settings,
            packages[(TradeCumulusRunLength.SMOKE, TradeCumulusMoistureState.BASELINE)],
            poll_seconds=args.poll_seconds,
            implementation_commit=implementation_commit,
        )
        variant_smoke = _run_one(
            settings,
            packages[
                (TradeCumulusRunLength.SMOKE, TradeCumulusMoistureState.MORE_MOISTURE)
            ],
            poll_seconds=args.poll_seconds,
            implementation_commit=implementation_commit,
        )
        estimated_full_pair_bytes = _estimated_full_pair_bytes(
            baseline_smoke.evidence.output_bytes,
            variant_smoke.evidence.output_bytes,
        )
        required_with_headroom = math.ceil(estimated_full_pair_bytes * 1.25)
        available_after_smokes = _free_bytes(settings)
        if available_after_smokes < required_with_headroom:
            raise TradeCumulusMoistureComparisonError(
                "Full-pair storage gate failed: "
                f"estimated {estimated_full_pair_bytes} bytes plus 25% headroom requires "
                f"{required_with_headroom}, found {available_after_smokes}."
            )

        baseline_full = _run_one(
            settings,
            packages[(TradeCumulusRunLength.FULL, TradeCumulusMoistureState.BASELINE)],
            poll_seconds=args.poll_seconds,
            implementation_commit=implementation_commit,
        )
        stage4 = compare_stage4_baseline(preserved, baseline_full.result)
        stage4_path = (
            baseline_full.evidence_path.parent / "stage4_consistency_evidence.json"
        )
        stage4_path.write_text(stage4.model_dump_json(indent=2) + "\n")
        if not stage4.passed:
            raise TradeCumulusMoistureComparisonError(
                "The new 120-second baseline failed the Stage 4 common-time consistency gate: "
                + (
                    stage4.first_failure.model_dump_json()
                    if stage4.first_failure
                    else "unknown"
                )
            )

        variant_full = _run_one(
            settings,
            packages[
                (TradeCumulusRunLength.FULL, TradeCumulusMoistureState.MORE_MOISTURE)
            ],
            poll_seconds=args.poll_seconds,
            implementation_commit=implementation_commit,
        )
        lens = build_joint_lens_preparation(
            settings, baseline_full.result, variant_full.result
        )
        paired = build_paired_evidence(
            baseline_full.evidence,
            variant_full.evidence,
            implementation_commit=implementation_commit,
            matched_package_proof=proofs[-1],
            stage4_consistency=stage4,
            lens_preparation=lens,
            estimated_full_pair_bytes=estimated_full_pair_bytes,
        )
        comparison_dir = (
            settings.runtime_home.expanduser()
            / "comparisons"
            / (f"trade-cumulus-moisture-{timestamp}")
        )
        evidence_path = comparison_dir / "comparison_evidence.json"
        paired = paired.model_copy(
            update={"runtime_local_evidence_path": str(evidence_path)}
        )
        write_paired_evidence(evidence_path, paired)
        print(
            json.dumps(
                _success_summary(
                    paired=paired,
                    evidence_path=evidence_path,
                    packages=packages,
                    proofs=proofs,
                    smoke_runs=(baseline_smoke, variant_smoke),
                    full_runs=(baseline_full, variant_full),
                    initial_free_bytes=initial_free_bytes,
                    available_after_smokes=available_after_smokes,
                    required_with_headroom=required_with_headroom,
                    cm1_release=provenance.release,
                    cm1_executable_sha256=provenance.executable_sha256,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("trade-cumulus-moisture-comparison: canceled", file=sys.stderr)
        return 130
    except (
        BomexCaseError,
        LocalRunManagerError,
        ResultIngestError,
        TradeCumulusMoistureComparisonError,
        OSError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {"status": "controlled_gate_failure", "error": str(exc)},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the exact baseline and More Moisture Trade Cumulus smoke/full sequence."
        )
    )
    parser.add_argument(
        "--runtime-home",
        help="Cloud Chamber runtime home. Defaults to configured settings.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help="Status polling interval while each sequential CM1 run is active.",
    )
    return parser


def _generate_all_packages(
    *,
    settings: CloudChamberSettings,
    timestamp: str,
    implementation_commit: str,
) -> dict[
    tuple[TradeCumulusRunLength, TradeCumulusMoistureState], TradeCumulusMatchedPackage
]:
    packages: dict[
        tuple[TradeCumulusRunLength, TradeCumulusMoistureState],
        TradeCumulusMatchedPackage,
    ] = {}
    for run_length in (TradeCumulusRunLength.SMOKE, TradeCumulusRunLength.FULL):
        for state in (
            TradeCumulusMoistureState.BASELINE,
            TradeCumulusMoistureState.MORE_MOISTURE,
        ):
            run_id = f"trade-cumulus-5b-{run_length.value}-{state.value}-{timestamp}"
            packages[(run_length, state)] = generate_trade_cumulus_matched_package(
                settings=settings,
                control_state=state,
                run_length=run_length,
                run_id=run_id,
                app_commit=implementation_commit,
            )
    return packages


def _verify_all_packages(
    packages: dict[
        tuple[TradeCumulusRunLength, TradeCumulusMoistureState],
        TradeCumulusMatchedPackage,
    ],
) -> list[PackageComparisonProof]:
    proofs: list[PackageComparisonProof] = []
    for run_length in (TradeCumulusRunLength.SMOKE, TradeCumulusRunLength.FULL):
        proofs.append(
            compare_matched_packages(
                packages[(run_length, TradeCumulusMoistureState.BASELINE)],
                packages[(run_length, TradeCumulusMoistureState.MORE_MOISTURE)],
            )
        )
    for state in (
        TradeCumulusMoistureState.BASELINE,
        TradeCumulusMoistureState.MORE_MOISTURE,
    ):
        verify_smoke_full_equivalence(
            packages[(TradeCumulusRunLength.SMOKE, state)],
            packages[(TradeCumulusRunLength.FULL, state)],
        )
    return proofs


def _run_one(
    settings: CloudChamberSettings,
    package: TradeCumulusMatchedPackage,
    *,
    poll_seconds: float,
    implementation_commit: str,
) -> _CompletedRun:
    _verify_execution_commit(implementation_commit)
    manager = LocalRunManager(settings=settings)
    started = time.monotonic()
    status = manager.launch(package.manifest_path)
    try:
        while status.lifecycle_state in {LifecycleState.QUEUED, LifecycleState.RUNNING}:
            time.sleep(poll_seconds)
            status = manager.status(package.manifest_path)
    except KeyboardInterrupt:
        manager.cancel()
        raise
    wall_clock_seconds = time.monotonic() - started
    if status.lifecycle_state != LifecycleState.COMPLETED or status.exit_code != 0:
        raise TradeCumulusMoistureComparisonError(
            f"Run {package.run_id} failed with lifecycle {status.lifecycle_state.value} "
            f"and exit code {status.exit_code}."
        )
    result = ingest_completed_run(package.manifest_path)
    evidence = build_trade_cumulus_run_evidence(
        result, package, wall_clock_seconds=wall_clock_seconds
    )
    evidence_path = package.package_dir / "trade_cumulus_moisture_run_evidence.json"
    write_trade_cumulus_run_evidence(evidence_path, evidence)
    if not evidence.gate.valid:
        raise TradeCumulusMoistureComparisonError(
            f"Run {package.run_id} failed its evidence gate: {evidence.gate.failures}"
        )
    return _CompletedRun(result=result, evidence=evidence, evidence_path=evidence_path)


def _verify_execution_commit(expected_commit: str) -> None:
    actual_commit = verified_clean_git_commit()
    if actual_commit != expected_commit:
        raise TradeCumulusMoistureComparisonError(
            f"Execution commit changed from {expected_commit} to {actual_commit}."
        )


def _verify_preserved_stage4_result(settings: CloudChamberSettings) -> ResultMetadata:
    xarray = __import__("xarray")
    result = get_result_metadata(settings, STAGE4_RESULT_ID)
    if len(result.model_output_paths) != 73:
        raise TradeCumulusMoistureComparisonError(
            f"Preserved Stage 4 result has {len(result.model_output_paths)} model paths, expected 73."
        )
    for configured_path in result.model_output_paths:
        path = Path(configured_path)
        if not path.is_file():
            raise TradeCumulusMoistureComparisonError(
                f"Preserved Stage 4 model output is unavailable: {path}"
            )
        with xarray.open_dataset(path, decode_times=False) as dataset:
            missing = [
                field
                for field in ("ql", "qv", "th", "w", "cwp")
                if field not in dataset
            ]
            if missing:
                raise TradeCumulusMoistureComparisonError(
                    f"Preserved Stage 4 output {path} lacks required fields: {missing}"
                )
    return result


def _estimated_full_pair_bytes(
    baseline_smoke_bytes: int, variant_smoke_bytes: int
) -> int:
    smoke_frames = (
        TradeCumulusRunLength.SMOKE.expected_model_output_count
        + TradeCumulusRunLength.SMOKE.expected_diagnostic_output_count
    )
    full_frames = (
        TradeCumulusRunLength.FULL.expected_model_output_count
        + TradeCumulusRunLength.FULL.expected_diagnostic_output_count
    )
    return math.ceil(
        (baseline_smoke_bytes + variant_smoke_bytes) * full_frames / smoke_frames
    )


def _free_bytes(settings: CloudChamberSettings) -> int:
    settings.runtime_home.expanduser().mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(settings.runtime_home.expanduser()).free


def _success_summary(
    *,
    paired: TradeCumulusPairedEvidence,
    evidence_path: Path,
    packages: dict[
        tuple[TradeCumulusRunLength, TradeCumulusMoistureState],
        TradeCumulusMatchedPackage,
    ],
    proofs: list[PackageComparisonProof],
    smoke_runs: tuple[_CompletedRun, _CompletedRun],
    full_runs: tuple[_CompletedRun, _CompletedRun],
    initial_free_bytes: int,
    available_after_smokes: int,
    required_with_headroom: int,
    cm1_release: str,
    cm1_executable_sha256: str,
) -> dict[str, Any]:
    completed = [*smoke_runs, *full_runs]
    return {
        "status": "completed_ingested_and_evaluated",
        "evidence_state": paired.evidence_state,
        "implementation_commit": paired.implementation_commit,
        "comparison_evidence_path": str(evidence_path),
        "run_ids": [item.evidence.run_id for item in completed],
        "result_ids": [item.evidence.result_id for item in completed],
        "run_evidence_paths": [str(item.evidence_path) for item in completed],
        "package_manifest_paths": [
            str(package.manifest_path) for package in packages.values()
        ],
        "package_proofs": [proof.model_dump(mode="json") for proof in proofs],
        "run_gates": {
            item.evidence.run_id: item.evidence.gate.model_dump(mode="json")
            for item in completed
        },
        "stage4_consistency": paired.stage4_consistency.model_dump(mode="json"),
        "lens_preparation": paired.lens_preparation.model_dump(mode="json"),
        "runtime_seconds": {
            item.evidence.run_id: item.evidence.wall_clock_seconds for item in completed
        },
        "output_bytes": {
            item.evidence.run_id: item.evidence.output_bytes for item in completed
        },
        "storage": {
            "initial_free_bytes": initial_free_bytes,
            "available_after_smokes": available_after_smokes,
            "estimated_full_pair_bytes": paired.estimated_full_pair_bytes,
            "required_with_25_percent_headroom_bytes": required_with_headroom,
            "actual_full_pair_bytes": paired.actual_full_pair_bytes,
        },
        "cm1_release": cm1_release,
        "cm1_executable_sha256": cm1_executable_sha256,
    }


if __name__ == "__main__":
    raise SystemExit(main())

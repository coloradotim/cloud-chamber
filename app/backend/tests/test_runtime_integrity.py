from pathlib import Path

import xarray as xr

from cloud_chamber.result_diagnostics import (
    FieldFrameQualityRecord,
    FieldFrameQualitySummary,
    FieldQuality,
)
from cloud_chamber.runtime_integrity import assess_runtime_integrity


def test_runtime_integrity_trusts_clean_normal_completion(tmp_path: Path) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")

    integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=[],
        stdout_log=stdout,
    )

    assert integrity.state == "trusted"
    assert integrity.reason == "runtime_integrity_checks_passed"
    assert integrity.normal_completion_reported is True


def test_runtime_integrity_caveats_underflow_only_without_failing(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")

    integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=[
            "CM1 stderr reported floating-point exception flags: IEEE_UNDERFLOW_FLAG"
        ],
        stdout_log=stdout,
    )

    assert integrity.state == "caveated"
    assert integrity.fatal_warning_flags == []
    assert "runtime_integrity_caveated_underflow_only" in integrity.caveats


def test_runtime_integrity_fails_invalid_or_overflow_warning(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")

    integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=[
            "CM1 stderr reported floating-point exception flags: "
            "IEEE_INVALID_FLAG IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG"
        ],
        stdout_log=stdout,
    )

    assert integrity.state == "failed"
    assert integrity.fatal_warning_flags == ["IEEE_INVALID_FLAG", "IEEE_OVERFLOW_FLAG"]
    assert "runtime_integrity_failed_fatal_floating_point_flags" in integrity.caveats
    assert "runtime_warning_flag:IEEE_INVALID_FLAG" in integrity.evidence


def test_runtime_integrity_fails_cm1_stats_sentinel_collapse(
    tmp_path: Path,
) -> None:
    stats_path = tmp_path / "cm1out_stats.nc"
    dataset = xr.Dataset(
        data_vars={
            "cflmax": ("mtime", [0.8, 0.7, 0.0]),
            "umax": ("mtime", [20.0, 22.0, -1.0e31]),
        },
        coords={"mtime": [0.0, 21420.0, 21480.0]},
    )
    dataset.to_netcdf(stats_path, engine="scipy")

    integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=[],
        stats_netcdf_paths=[stats_path],
    )

    assert integrity.state == "failed"
    assert integrity.stats_sentinel_collapse_detected is True
    assert integrity.stats_sentinel_times_seconds == [21480.0]
    assert "runtime_integrity_failed_cm1_stats_sentinel_collapse" in integrity.caveats
    assert any("umax:frame_2:time_21480" in item for item in integrity.evidence)


def test_runtime_integrity_fails_terminal_multi_field_non_finite_output() -> None:
    terminal_frame = FieldFrameQualitySummary(
        frame_times_seconds=[0.0, 21600.0],
        affected_frames=[
            FieldFrameQualityRecord(
                frame_index=1,
                time_seconds=21600.0,
                position="terminal",
                finite_count=0,
                non_finite_count=16,
                total_count=16,
                entirely_non_finite=True,
            )
        ],
        affected_frame_indices=[1],
        affected_frame_times_seconds=[21600.0],
        terminal_frame_affected=True,
        affected_frame_count=1,
        entirely_non_finite_frame_count=1,
        finite_frame_count=1,
        total_frame_count=2,
        finite_point_fraction=0.5,
        last_finite_frame_time_seconds=0.0,
    )
    field_quality = {
        field: FieldQuality(
            field=field,
            source_field=source,
            quality_state="untrusted",
            reason=f"{field}_terminal_output_frame_entirely_non_finite",
            finite_count=16,
            non_finite_count=16,
            total_count=32,
            finite_fraction=0.5,
            frame_quality=terminal_frame,
            caveats=[f"{field}_terminal_output_frame_entirely_non_finite"],
        )
        for field, source in {"qc": "qc", "qv": "qv", "surface_rain": "rain"}.items()
    }

    integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=[],
        field_quality=field_quality,
    )

    assert integrity.state == "failed"
    assert integrity.terminal_non_finite_fields == ["qc", "qv", "surface_rain"]
    assert "runtime_integrity_failed_terminal_output_frame_entirely_non_finite" in (
        integrity.caveats
    )

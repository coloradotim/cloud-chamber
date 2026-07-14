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
        lifecycle_state="completed",
        exit_code=0,
        runtime_warnings=[],
        stdout_log=stdout,
    )

    assert integrity.state == "trusted"
    assert integrity.reason == "runtime_integrity_checks_passed"
    assert integrity.normal_completion_reported is True


def test_runtime_integrity_is_not_assessed_before_terminal_lifecycle() -> None:
    for lifecycle_state in ("packaged", "queued", "running"):
        integrity = assess_runtime_integrity(lifecycle_state=lifecycle_state)

        assert integrity.state == "not_assessed"
        assert integrity.assessed is False
        assert integrity.reason == "runtime_integrity_not_assessed_until_terminal_lifecycle_state"


def test_runtime_integrity_is_not_assessed_without_completion_evidence() -> None:
    integrity = assess_runtime_integrity(lifecycle_state="completed")

    assert integrity.state == "not_assessed"
    assert integrity.assessed is False
    assert integrity.reason == "runtime_integrity_not_assessed_missing_completion_evidence"


def test_runtime_integrity_caveats_underflow_only_without_failing(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")

    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
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
        lifecycle_state="completed",
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
        lifecycle_state="completed",
        exit_code=0,
        runtime_warnings=[],
        stats_netcdf_paths=[stats_path],
    )

    assert integrity.state == "failed"
    assert integrity.stats_sentinel_collapse_detected is True
    assert integrity.stats_sentinel_times_seconds == [21480.0]
    assert "runtime_integrity_failed_cm1_stats_sentinel_collapse" in integrity.caveats
    assert any("umax:frame_2:time_21480" in item for item in integrity.evidence)


def test_runtime_integrity_caveats_one_terminal_optional_field() -> None:
    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        field_quality=_terminal_field_quality(["dbz"]),
    )

    assert integrity.state == "caveated"
    assert integrity.terminal_non_finite_fields == ["dbz"]
    assert "runtime_integrity_caveated_terminal_output_frame_entirely_non_finite" in (
        integrity.caveats
    )


def test_runtime_integrity_caveats_one_terminal_core_field() -> None:
    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        field_quality=_terminal_field_quality(["qc"]),
    )

    assert integrity.state == "caveated"
    assert integrity.terminal_non_finite_fields == ["qc"]


def test_runtime_integrity_caveats_terminal_fields_within_one_category() -> None:
    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        field_quality=_terminal_field_quality(["qc", "qr", "qi"]),
    )

    assert integrity.state == "caveated"
    assert integrity.terminal_non_finite_fields == ["qc", "qi", "qr"]


def test_runtime_integrity_fails_terminal_multi_category_non_finite_output() -> None:
    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        field_quality=_terminal_field_quality(["qc", "w", "hfx"]),
    )

    assert integrity.state == "failed"
    assert integrity.terminal_non_finite_fields == ["hfx", "qc", "w"]
    assert "runtime_integrity_failed_terminal_output_frame_entirely_non_finite" in (
        integrity.caveats
    )


def test_runtime_integrity_fails_surface_forced_002_terminal_pattern() -> None:
    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        runtime_warnings=[
            "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG "
            "IEEE_DIVIDE_BY_ZERO IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG"
        ],
        field_quality=_terminal_field_quality(["hfx", "qc", "qfx", "qr", "surface_rain", "w"]),
    )

    assert integrity.state == "failed"
    assert integrity.terminal_non_finite_fields == [
        "hfx",
        "qc",
        "qfx",
        "qr",
        "surface_rain",
        "w",
    ]
    assert "runtime_integrity_failed_fatal_floating_point_flags" in integrity.caveats
    assert "runtime_integrity_failed_terminal_output_frame_entirely_non_finite" in (
        integrity.caveats
    )


def test_runtime_integrity_caveats_benign_stats_nan_without_failing(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")
    stats_path = tmp_path / "cm1out_stats.nc"
    xr.Dataset(
        data_vars={"cflmax": ("mtime", [0.8, float("nan"), 0.7])},
        coords={"mtime": [0.0, 60.0, 120.0]},
    ).to_netcdf(stats_path, engine="scipy")

    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        stdout_log=stdout,
        stats_netcdf_paths=[stats_path],
    )

    assert integrity.state == "caveated"
    assert integrity.stats_sentinel_collapse_detected is False
    assert "runtime_integrity_caveated_cm1_stats_ambiguous_non_finite" in integrity.caveats


def test_runtime_integrity_ignores_unrelated_all_nan_stats_variable(
    tmp_path: Path,
) -> None:
    stdout = tmp_path / "stdout.log"
    stdout.write_text("Program terminated normally\n")
    stats_path = tmp_path / "cm1out_stats.nc"
    xr.Dataset(
        data_vars={"optional_missing_stat": ("mtime", [float("nan"), float("nan")])},
        coords={"mtime": [0.0, 60.0]},
    ).to_netcdf(stats_path, engine="scipy")

    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        stdout_log=stdout,
        stats_netcdf_paths=[stats_path],
    )

    assert integrity.state == "trusted"
    assert integrity.stats_sentinel_collapse_detected is False


def test_runtime_integrity_fails_late_stats_infinity(tmp_path: Path) -> None:
    stats_path = tmp_path / "cm1out_stats.nc"
    xr.Dataset(
        data_vars={"kmhmax": ("mtime", [1.0, 2.0, float("inf")])},
        coords={"mtime": [0.0, 21420.0, 21480.0]},
    ).to_netcdf(stats_path, engine="scipy")

    integrity = assess_runtime_integrity(
        lifecycle_state="completed",
        exit_code=0,
        stats_netcdf_paths=[stats_path],
    )

    assert integrity.state == "failed"
    assert integrity.stats_sentinel_times_seconds == [21480.0]


def _terminal_field_quality(fields: list[str]) -> dict[str, FieldQuality]:
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
    source_fields = {
        "surface_rain": "rain",
    }
    return {
        field: FieldQuality(
            field=field,
            source_field=source_fields.get(field, field),
            quality_state="untrusted",
            reason=f"{field}_terminal_output_frame_entirely_non_finite",
            finite_count=16,
            non_finite_count=16,
            total_count=32,
            finite_fraction=0.5,
            frame_quality=terminal_frame,
            caveats=[f"{field}_terminal_output_frame_entirely_non_finite"],
        )
        for field in fields
    }

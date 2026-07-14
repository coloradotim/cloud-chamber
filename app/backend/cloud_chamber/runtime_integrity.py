"""Runtime-integrity assessment for CM1 runs.

This layer is deliberately separate from lifecycle state. A CM1 process can
exit normally while the scientific output is no longer trustworthy.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterable, Mapping, Sequence
from math import isfinite
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.result_diagnostics import FieldQuality

RuntimeIntegrityState = Literal["trusted", "caveated", "failed", "not_assessed"]

FLOATING_POINT_WARNING_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
    "IEEE_UNDERFLOW_FLAG",
)
FATAL_FLOATING_POINT_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
)
SENTINEL_ABS_THRESHOLD = 1.0e20
TERMINAL_LIFECYCLE_STATES = {"completed", "ingested", "saved"}
CM1_STATS_INTEGRITY_VARIABLES = {
    "cfl",
    "cflmax",
    "khhmax",
    "khvmax",
    "kmhmax",
    "kmvmax",
    "maxqc",
    "maxqg",
    "maxqi",
    "maxqr",
    "maxqs",
    "maxqv",
    "minqc",
    "minqg",
    "minqi",
    "minqr",
    "minqs",
    "minqv",
    "umax",
    "umin",
    "vmax",
    "vmin",
    "wmax",
    "wmin",
}
TERMINAL_FIELD_CATEGORIES = {
    "dynamics": {"u", "v", "w", "uinterp", "vinterp", "winterp", "u10", "v10"},
    "thermodynamics": {"prs", "pressure", "q2", "qv", "t", "t2", "temperature", "th", "theta"},
    "hydrometeors": {"dbz", "qc", "qg", "qi", "qr", "qs"},
    "surface": {"hfx", "prate", "qfx", "rain", "surface_rain"},
}


class RuntimeIntegrity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessed: bool = False
    state: RuntimeIntegrityState = "not_assessed"
    reason: str = "runtime_integrity_not_assessed"
    summary: str = "Runtime integrity was not assessed for this result."
    exit_code: int | None = None
    normal_completion_reported: bool | None = None
    warning_flags: list[str] = Field(default_factory=list)
    fatal_warning_flags: list[str] = Field(default_factory=list)
    stats_sentinel_collapse_detected: bool = False
    stats_sentinel_times_seconds: list[float | None] = Field(default_factory=list)
    terminal_non_finite_fields: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


def assess_runtime_integrity(
    *,
    lifecycle_state: str | None = None,
    exit_code: int | None = None,
    runtime_warnings: Sequence[str] = (),
    stdout_log: Path | None = None,
    stats_netcdf_paths: Sequence[Path] = (),
    field_quality: Mapping[str, FieldQuality] | None = None,
) -> RuntimeIntegrity:
    """Assess whether a completed CM1 runtime produced trustworthy output."""

    normal_completion_reported = _stdout_reports_normal_completion(stdout_log)
    warning_flags = _floating_point_flags(runtime_warnings)
    fatal_flags = [flag for flag in warning_flags if flag in FATAL_FLOATING_POINT_FLAGS]
    stats_collapse = _stats_sentinel_collapse(stats_netcdf_paths)
    terminal_fields = _terminal_non_finite_fields(field_quality)
    partial_terminal_fields = _partial_terminal_non_finite_fields(field_quality)
    caveats: list[str] = []
    evidence: list[str] = []

    if exit_code is not None:
        evidence.append(f"exit_code:{exit_code}")
    if normal_completion_reported is True:
        evidence.append("stdout:program_terminated_normally")
    elif normal_completion_reported is False:
        evidence.append("stdout:normal_completion_marker_absent")
    for flag in warning_flags:
        evidence.append(f"runtime_warning_flag:{flag}")
    if stats_collapse.detected:
        evidence.extend(stats_collapse.evidence)
    if stats_collapse.ambiguous_evidence:
        evidence.extend(stats_collapse.ambiguous_evidence)
    for field in terminal_fields:
        evidence.append(f"terminal_output_frame_entirely_non_finite:{field}")
    for field in partial_terminal_fields:
        evidence.append(f"terminal_output_frame_partially_non_finite:{field}")

    if lifecycle_state is not None and lifecycle_state not in TERMINAL_LIFECYCLE_STATES:
        return _not_assessed(
            reason="runtime_integrity_not_assessed_until_terminal_lifecycle_state",
            summary=(
                "Runtime integrity is not assessed until a CM1 run reaches a terminal "
                "completed state."
            ),
            lifecycle_state=lifecycle_state,
            exit_code=exit_code,
            normal_completion_reported=normal_completion_reported,
            warning_flags=warning_flags,
            fatal_flags=fatal_flags,
            evidence=evidence,
        )

    if exit_code is not None and exit_code != 0:
        caveats.append("runtime_integrity_failed_nonzero_exit_code")
    if fatal_flags:
        caveats.append("runtime_integrity_failed_fatal_floating_point_flags")
    if stats_collapse.detected:
        caveats.append("runtime_integrity_failed_cm1_stats_sentinel_collapse")
    terminal_policy = _terminal_non_finite_policy(terminal_fields)
    if terminal_policy == "failed":
        caveats.append("runtime_integrity_failed_terminal_output_frame_entirely_non_finite")
    elif terminal_policy == "caveated":
        caveats.append("runtime_integrity_caveated_terminal_output_frame_entirely_non_finite")
    if partial_terminal_fields:
        caveats.append("runtime_integrity_caveated_terminal_non_finite_values")
    if stats_collapse.ambiguous_evidence and not stats_collapse.detected:
        caveats.append("runtime_integrity_caveated_cm1_stats_ambiguous_non_finite")
    if warning_flags == ["IEEE_UNDERFLOW_FLAG"]:
        caveats.append("runtime_integrity_caveated_underflow_only")

    failed = any(caveat.startswith("runtime_integrity_failed") for caveat in caveats)
    if failed:
        return RuntimeIntegrity(
            assessed=True,
            state="failed",
            reason="runtime_integrity_failure_evidence_present",
            summary=(
                "CM1 process completion is not enough to trust this result; runtime-integrity "
                "checks found fatal floating-point, stats-collapse, or terminal output evidence."
            ),
            exit_code=exit_code,
            normal_completion_reported=normal_completion_reported,
            warning_flags=warning_flags,
            fatal_warning_flags=fatal_flags,
            stats_sentinel_collapse_detected=stats_collapse.detected,
            stats_sentinel_times_seconds=stats_collapse.times_seconds,
            terminal_non_finite_fields=terminal_fields,
            caveats=_dedupe(caveats),
            evidence=_dedupe(evidence),
        )

    if not _has_minimum_assessment_evidence(
        exit_code=exit_code,
        normal_completion_reported=normal_completion_reported,
        warning_flags=warning_flags,
        stats_paths=stats_netcdf_paths,
    ):
        return _not_assessed(
            reason="runtime_integrity_not_assessed_missing_completion_evidence",
            summary=(
                "Runtime integrity was not assessed because completion evidence, runtime "
                "warnings, and CM1 stats evidence are unavailable."
            ),
            lifecycle_state=lifecycle_state,
            exit_code=exit_code,
            normal_completion_reported=normal_completion_reported,
            warning_flags=warning_flags,
            fatal_flags=fatal_flags,
            evidence=evidence,
        )

    if caveats:
        return RuntimeIntegrity(
            assessed=True,
            state="caveated",
            reason="runtime_integrity_caveated_evidence_present",
            summary=(
                "CM1 completed without fatal runtime-integrity evidence, but the run carries "
                "runtime caveats that should remain visible."
            ),
            exit_code=exit_code,
            normal_completion_reported=normal_completion_reported,
            warning_flags=warning_flags,
            fatal_warning_flags=fatal_flags,
            stats_sentinel_collapse_detected=stats_collapse.detected,
            stats_sentinel_times_seconds=stats_collapse.times_seconds,
            terminal_non_finite_fields=terminal_fields,
            caveats=_dedupe(caveats),
            evidence=_dedupe(evidence),
        )

    return RuntimeIntegrity(
        assessed=True,
        state="trusted",
        reason="runtime_integrity_checks_passed",
        summary="Runtime-integrity checks found no fatal or caveated runtime evidence.",
        exit_code=exit_code,
        normal_completion_reported=normal_completion_reported,
        warning_flags=warning_flags,
        fatal_warning_flags=[],
        stats_sentinel_collapse_detected=False,
        stats_sentinel_times_seconds=[],
        terminal_non_finite_fields=[],
        caveats=[],
        evidence=_dedupe(evidence),
    )


class _StatsCollapse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected: bool = False
    times_seconds: list[float | None] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    ambiguous_evidence: list[str] = Field(default_factory=list)


def _not_assessed(
    *,
    reason: str,
    summary: str,
    lifecycle_state: str | None,
    exit_code: int | None,
    normal_completion_reported: bool | None,
    warning_flags: list[str],
    fatal_flags: list[str],
    evidence: list[str],
) -> RuntimeIntegrity:
    if lifecycle_state is not None:
        evidence = [*evidence, f"lifecycle_state:{lifecycle_state}"]
    return RuntimeIntegrity(
        assessed=False,
        state="not_assessed",
        reason=reason,
        summary=summary,
        exit_code=exit_code,
        normal_completion_reported=normal_completion_reported,
        warning_flags=warning_flags,
        fatal_warning_flags=fatal_flags,
        caveats=[],
        evidence=_dedupe(evidence),
    )


def _has_minimum_assessment_evidence(
    *,
    exit_code: int | None,
    normal_completion_reported: bool | None,
    warning_flags: list[str],
    stats_paths: Sequence[Path],
) -> bool:
    return (
        exit_code is not None
        or normal_completion_reported is True
        or bool(warning_flags)
        or bool(stats_paths)
    )


def _terminal_non_finite_policy(fields: Sequence[str]) -> RuntimeIntegrityState:
    if not fields:
        return "trusted"
    categories = {
        category
        for field in fields
        for category, category_fields in TERMINAL_FIELD_CATEGORIES.items()
        if field in category_fields
    }
    if len(fields) >= 2 and len(categories) >= 2:
        return "failed"
    return "caveated"


def _floating_point_flags(warnings: Iterable[str]) -> list[str]:
    joined = "\n".join(warnings)
    return [flag for flag in FLOATING_POINT_WARNING_FLAGS if flag in joined]


def _stdout_reports_normal_completion(stdout_log: Path | None) -> bool | None:
    if stdout_log is None:
        return None
    try:
        if not stdout_log.exists():
            return None
        return "Program terminated normally" in stdout_log.read_text(errors="replace")
    except OSError:
        return None


def _terminal_non_finite_fields(
    field_quality: Mapping[str, FieldQuality] | None,
) -> list[str]:
    fields: list[str] = []
    for field, quality in (field_quality or {}).items():
        frame_quality = quality.frame_quality
        if frame_quality is None:
            continue
        if any(
            frame.position in {"terminal", "single"} and frame.entirely_non_finite
            for frame in frame_quality.affected_frames
        ):
            fields.append(field)
    return sorted(fields)


def _partial_terminal_non_finite_fields(
    field_quality: Mapping[str, FieldQuality] | None,
) -> list[str]:
    fields: list[str] = []
    for field, quality in (field_quality or {}).items():
        frame_quality = quality.frame_quality
        if frame_quality is None:
            continue
        if any(
            frame.position in {"terminal", "single"} and not frame.entirely_non_finite
            for frame in frame_quality.affected_frames
        ):
            fields.append(field)
    return sorted(fields)


def _stats_sentinel_collapse(paths: Sequence[Path]) -> _StatsCollapse:
    times: list[float | None] = []
    evidence: list[str] = []
    ambiguous_evidence: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            dataset = _open_dataset(path)
        except Exception:
            continue
        try:
            collapse = _stats_sentinel_collapse_for_dataset(dataset)
            times.extend(collapse.times_seconds)
            evidence.extend(
                f"cm1_stats_sentinel_collapse:{path.name}:{item}" for item in collapse.evidence
            )
            ambiguous_evidence.extend(
                f"cm1_stats_ambiguous_non_finite:{path.name}:{item}"
                for item in collapse.ambiguous_evidence
            )
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()
    return _StatsCollapse(
        detected=bool(evidence),
        times_seconds=_dedupe_optional_float(times),
        evidence=_dedupe(evidence),
        ambiguous_evidence=_dedupe(ambiguous_evidence),
    )


def _open_dataset(path: Path) -> Any:
    xarray = importlib.import_module("xarray")
    return xarray.open_dataset(path)


def _stats_sentinel_collapse_for_dataset(dataset: Any) -> _StatsCollapse:
    time_name = _stats_time_name(dataset)
    time_values = _stats_time_values(dataset, time_name)
    detected_times: list[float | None] = []
    evidence: list[str] = []
    ambiguous_evidence: list[str] = []
    for variable_name, data_array in dataset.data_vars.items():
        normalized_name = variable_name.lower()
        values = getattr(data_array, "values", None)
        if values is None:
            continue
        try:
            array = _as_numpy_array(values)
        except Exception:
            continue
        if array.size == 0 or normalized_name not in CM1_STATS_INTEGRITY_VARIABLES:
            continue
        frame_axis = _time_axis(data_array, time_name)
        if frame_axis is None:
            if _contains_collapse_sentinel(array, prior_frames=None):
                detected_times.append(None)
                evidence.append(f"{variable_name}:time_unavailable")
            elif _contains_ambiguous_non_finite(array):
                ambiguous_evidence.append(f"{variable_name}:time_unavailable")
            continue
        frame_count = int(array.shape[frame_axis])
        for frame_index in range(frame_count):
            frame = _take_frame(array, frame_axis, frame_index)
            prior_frames = (
                _take_frame_range(array, frame_axis, frame_index) if frame_index > 0 else None
            )
            if _contains_collapse_sentinel(frame, prior_frames=prior_frames):
                time_seconds = time_values[frame_index] if frame_index < len(time_values) else None
                detected_times.append(time_seconds)
                evidence.append(
                    f"{variable_name}:frame_{frame_index}:time_{_time_label(time_seconds)}"
                )
            elif _contains_ambiguous_non_finite(frame):
                time_seconds = time_values[frame_index] if frame_index < len(time_values) else None
                ambiguous_evidence.append(
                    f"{variable_name}:frame_{frame_index}:time_{_time_label(time_seconds)}"
                )
    return _StatsCollapse(
        detected=bool(evidence),
        times_seconds=_dedupe_optional_float(detected_times),
        evidence=_dedupe(evidence),
        ambiguous_evidence=_dedupe(ambiguous_evidence),
    )


def _as_numpy_array(values: Any) -> Any:
    numpy = importlib.import_module("numpy")
    return numpy.asarray(values)


def _stats_time_name(dataset: Any) -> str | None:
    for candidate in ("time", "mtime", "t"):
        if candidate in getattr(dataset, "sizes", {}):
            return candidate
    return None


def _stats_time_values(dataset: Any, time_name: str | None) -> list[float | None]:
    if time_name is None:
        return []
    if time_name not in dataset.coords:
        return [float(index) for index in range(int(dataset.sizes[time_name]))]
    values = dataset.coords[time_name].values.reshape(-1).tolist()
    return [_float_or_none(value) for value in values]


def _time_axis(data_array: Any, time_name: str | None) -> int | None:
    if time_name is None:
        return None
    try:
        return list(data_array.dims).index(time_name)
    except ValueError:
        return None


def _take_frame(array: Any, axis: int, index: int) -> Any:
    numpy = importlib.import_module("numpy")
    return numpy.take(array, index, axis=axis)


def _take_frame_range(array: Any, axis: int, stop: int) -> Any:
    return array.take(indices=range(stop), axis=axis)


def _contains_collapse_sentinel(array: Any, *, prior_frames: Any | None) -> bool:
    numpy = importlib.import_module("numpy")
    try:
        numeric = numpy.asarray(array, dtype=float)
    except (TypeError, ValueError):
        return False
    if numeric.size == 0:
        return False
    has_infinity = bool(numpy.isinf(numeric).any())
    finite_values = numeric[numpy.isfinite(numeric)]
    has_extreme = bool(
        finite_values.size and numpy.nanmax(numpy.abs(finite_values)) >= SENTINEL_ABS_THRESHOLD
    )
    if not has_infinity and not has_extreme:
        return False
    if prior_frames is None:
        return True
    return _has_prior_finite_evolution(prior_frames)


def _contains_ambiguous_non_finite(array: Any) -> bool:
    numpy = importlib.import_module("numpy")
    try:
        numeric = numpy.asarray(array, dtype=float)
    except (TypeError, ValueError):
        return False
    if numeric.size == 0:
        return False
    return bool(numpy.isnan(numeric).any())


def _has_prior_finite_evolution(array: Any) -> bool:
    numpy = importlib.import_module("numpy")
    try:
        numeric = numpy.asarray(array, dtype=float)
    except (TypeError, ValueError):
        return False
    finite_values = numeric[numpy.isfinite(numeric)]
    if finite_values.size == 0:
        return False
    max_abs = float(numpy.nanmax(numpy.abs(finite_values)))
    return isfinite(max_abs) and max_abs < SENTINEL_ABS_THRESHOLD


def _float_or_none(value: Any) -> float | None:
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    return as_float if isfinite(as_float) else None


def _time_label(value: float | None) -> str:
    if value is None:
        return "unavailable"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}"


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _dedupe_optional_float(values: Iterable[float | None]) -> list[float | None]:
    seen: set[str] = set()
    deduped: list[float | None] = []
    for value in values:
        key = "none" if value is None else repr(float(value))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped

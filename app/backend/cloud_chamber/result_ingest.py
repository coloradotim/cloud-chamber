"""NetCDF result ingest metadata for completed CM1 runs."""

from __future__ import annotations

import importlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.output_products import (
    FieldDefaultTime,
    InterestingTimeRecord,
    ScienceSummary,
    build_interesting_time_product,
    build_output_product_manifest_for_result,
    default_output_product_manifest_path,
    write_output_product_manifest,
)
from cloud_chamber.result_diagnostics import (
    CloudDiagnostics,
    ProcessDiagnostics,
    RainDiagnostics,
    ResultDiagnostics,
    TimeDiagnostics,
    TimeValue,
    VerticalVelocityDiagnostics,
    compute_baseline_diagnostics,
    compute_process_diagnostics,
)
from cloud_chamber.run_manifest import LifecycleState, ProductState, RunManifest, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

RESULT_METADATA_FILENAME = "result_metadata.json"
MODEL_OUTPUT_PATTERN = re.compile(r"^cm1out_\d+\.nc(?:4)?$")
STATS_OUTPUT_NAMES = {"cm1out_stats.nc", "cm1out_stats.nc4"}


class ResultIngestError(RuntimeError):
    """Raised when a completed run cannot be ingested into result metadata."""


class FieldMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dimensions: list[str]
    shape: list[int]
    units: str | None = None


class ResultMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    scenario_name: str | None = None
    physical_question: str
    controls: dict[str, str | float | bool]
    run_size_preset: str
    source_lifecycle_state: str
    source_product_state: str
    source_model: str
    input_source: str = "generated_reference"
    input_source_label: str = "Generated reference"
    observed_sounding: dict[str, Any] | None = None
    package_family: str | None = None
    package_display_name: str | None = None
    trigger_type: str | None = None
    trigger_parameters: dict[str, Any] | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    package_caveats: list[str] = Field(default_factory=list)
    manual_validation_status: str | None = None
    result_state: str = "ingested_result_metadata"
    raw_cm1_artifacts: list[str] = Field(default_factory=list)
    netcdf_paths: list[str] = Field(default_factory=list)
    model_output_paths: list[str] = Field(default_factory=list)
    stats_netcdf_paths: list[str] = Field(default_factory=list)
    skipped_netcdf_paths: list[str] = Field(default_factory=list)
    model_output_file_count: int = 0
    processed_artifacts: list[str] = Field(default_factory=list)
    visualization_ready_artifacts: list[str] = Field(default_factory=list)
    dimensions: dict[str, int] = Field(default_factory=dict)
    coordinates: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    fields_detected: list[FieldMetadata] = Field(default_factory=list)
    time_coordinate: str | None = None
    time_steps: int | None = None
    first_output_time_seconds: float | None = None
    last_output_time_seconds: float | None = None
    time_coordinate_source: str | None = None
    time_coordinate_fallback_used: bool = False
    grid_shape: list[int] | None = None
    warnings: list[str] = Field(default_factory=list)
    diagnostics_summary: str | None = None
    diagnostics: ResultDiagnostics | None = None
    process_diagnostics: ProcessDiagnostics | None = None
    interesting_times: list[InterestingTimeRecord] = Field(default_factory=list)
    default_time_by_field: dict[str, FieldDefaultTime] = Field(default_factory=dict)
    science_summary: ScienceSummary | None = None
    interesting_time_caveats: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


def ingest_completed_run(manifest_path: Path) -> ResultMetadata:
    """Create result metadata for a completed run with NetCDF output."""
    manifest = load_run_manifest(manifest_path.expanduser())
    if manifest.lifecycle_state != LifecycleState.COMPLETED:
        raise ResultIngestError(
            "Only completed CM1 runs can be ingested into result metadata; "
            f"found {manifest.lifecycle_state.value}."
        )
    if manifest.provenance.product_state != ProductState.COMPLETED_CM1_RESULT:
        raise ResultIngestError(
            "Only completed CM1 result manifests can be ingested; "
            f"found {manifest.provenance.product_state.value}."
        )
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser()
    netcdf_paths = _netcdf_paths(manifest, run_dir)
    if not netcdf_paths:
        raise ResultIngestError(
            "No NetCDF output artifacts found for ingest. Raw CM1 .dat/.ctl artifacts "
            "may be cataloged on the run manifest, but they are not NetCDF ingest input."
        )

    classified = _classify_netcdf_paths(netcdf_paths)
    if not classified.model_output_paths:
        raise ResultIngestError(
            "No CM1 model-field NetCDF output files found for ingest. "
            "Stats NetCDF files are not enough for field diagnostics."
        )
    result = _result_from_model_output_files(manifest, netcdf_paths, classified)

    result_path = run_dir / RESULT_METADATA_FILENAME
    product_manifest_path = default_output_product_manifest_path(run_dir)
    result = result.model_copy(
        update={"processed_artifacts": [*result.processed_artifacts, str(product_manifest_path)]}
    )
    product_manifest = build_output_product_manifest_for_result(
        result,
        result_metadata_path=result_path,
        run_manifest_path=manifest_path.expanduser(),
        product_root=product_manifest_path.parent,
    )
    interesting_time_product = build_interesting_time_product(
        result_id=result.result_id,
        diagnostics=result.diagnostics,
        output_manifest=product_manifest,
        variables=result.variables,
    )
    product_manifest = product_manifest.model_copy(
        update={"interesting_time_product": interesting_time_product}
    )
    result = result.model_copy(
        update={
            "interesting_times": interesting_time_product.available_interesting_times,
            "default_time_by_field": interesting_time_product.default_time_by_field,
            "science_summary": interesting_time_product.science_summary,
            "interesting_time_caveats": interesting_time_product.caveats,
        }
    )
    result_path.write_text(result.to_json_text())
    write_output_product_manifest(product_manifest_path, product_manifest)
    return result


def _result_from_model_output_files(
    manifest: RunManifest,
    netcdf_paths: list[Path],
    classified: _ClassifiedNetcdfPaths,
) -> ResultMetadata:
    if len(classified.model_output_paths) == 1:
        dataset, skipped_single, contributing_single, close_datasets = _open_model_output_sequence(
            classified.model_output_paths
        )
        try:
            return _result_from_dataset(
                manifest,
                netcdf_paths,
                classified,
                skipped_single,
                contributing_single,
                dataset,
            )
        finally:
            for close_dataset in close_datasets:
                close = getattr(close_dataset, "close", None)
                if callable(close):
                    close()

    skipped_paths: list[str] = []
    contributing_paths: list[Path] = []
    diagnostics_parts: list[ResultDiagnostics] = []
    sequence_time_values: list[float | None] = []
    metadata_snapshot: _DatasetMetadataSnapshot | None = None

    for file_index, path in enumerate(classified.model_output_paths):
        try:
            dataset = _open_dataset(path)
        except ResultIngestError as exc:
            skipped_paths.append(f"{path}: {exc}")
            continue

        try:
            normalized = _normalize_time_dimension(dataset, file_index)
            if metadata_snapshot is None:
                metadata_snapshot = _metadata_snapshot(normalized)
            contributing_paths.append(path)
            diagnostics_parts.append(compute_baseline_diagnostics(normalized, []))
            sequence_time_values.extend(_time_values(normalized))
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()

    if metadata_snapshot is None or not contributing_paths:
        skipped_detail = "; ".join(skipped_paths) if skipped_paths else "no files could be opened"
        raise ResultIngestError(
            f"No CM1 model-field NetCDF output files could be opened: {skipped_detail}"
        )

    warnings = list(manifest.outputs.runtime_warnings)
    warnings.extend(f"skipped_netcdf_output:{path}" for path in skipped_paths)
    missing_expected = [
        field
        for field in ("qc", "w")
        if field not in metadata_snapshot.variables and field not in metadata_snapshot.coordinates
    ]
    if missing_expected:
        warnings.append(
            "Expected fields missing from NetCDF metadata: " + ", ".join(missing_expected)
        )

    diagnostics = _merge_diagnostics(diagnostics_parts, warnings)
    process_diagnostics = compute_process_diagnostics(
        diagnostics,
        scenario_id=manifest.scenario.id,
        controls=manifest.controls,
        variables=metadata_snapshot.variables,
    )
    dimensions = dict(metadata_snapshot.dimensions)
    if metadata_snapshot.time_coordinate is not None:
        dimensions[metadata_snapshot.time_coordinate] = len(sequence_time_values)
    now = datetime.now(UTC)
    return ResultMetadata(
        result_id=f"result-{manifest.run_id}",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        scenario_name=None,
        physical_question=manifest.physical_question,
        controls=manifest.controls,
        run_size_preset=manifest.run_size_preset,
        source_lifecycle_state=manifest.lifecycle_state.value,
        source_product_state=manifest.provenance.product_state.value,
        source_model=manifest.provenance.source_model,
        input_source=_input_source(manifest),
        input_source_label=_input_source_label(manifest),
        observed_sounding=manifest.observed_sounding,
        package_family=manifest.package_family,
        package_display_name=manifest.package_display_name,
        trigger_type=manifest.trigger_type,
        trigger_parameters=manifest.trigger_parameters,
        expected_outputs=manifest.expected_outputs,
        package_caveats=manifest.package_caveats,
        manual_validation_status=manifest.manual_validation_status,
        raw_cm1_artifacts=manifest.outputs.raw_cm1_artifacts,
        netcdf_paths=[str(path) for path in netcdf_paths],
        model_output_paths=[str(path) for path in contributing_paths],
        stats_netcdf_paths=[str(path) for path in classified.stats_netcdf_paths],
        skipped_netcdf_paths=skipped_paths,
        model_output_file_count=len(contributing_paths),
        processed_artifacts=manifest.outputs.processed_artifacts,
        dimensions=dimensions,
        coordinates=metadata_snapshot.coordinates,
        variables=metadata_snapshot.variables,
        fields_detected=metadata_snapshot.fields,
        time_coordinate=metadata_snapshot.time_coordinate,
        time_steps=len(sequence_time_values) or None,
        first_output_time_seconds=_first_time_value(sequence_time_values),
        last_output_time_seconds=_last_time_value(sequence_time_values),
        time_coordinate_source=diagnostics.time.source,
        time_coordinate_fallback_used=diagnostics.time.fallback_used,
        grid_shape=_grid_shape(dimensions),
        warnings=warnings,
        diagnostics_summary=_diagnostics_summary(diagnostics),
        diagnostics=diagnostics,
        process_diagnostics=process_diagnostics,
        created_at=now,
        updated_at=now,
    )


def list_result_metadata(settings: CloudChamberSettings) -> list[ResultMetadata]:
    """List result metadata files under the configured runtime home."""
    results_dir = settings.runtime_home.expanduser() / "runs"
    if not results_dir.exists():
        return []
    results: list[ResultMetadata] = []
    for path in sorted(results_dir.glob(f"*/{RESULT_METADATA_FILENAME}")):
        try:
            results.append(result_metadata_from_json(path.read_text()))
        except (OSError, ValueError):
            continue
    return results


def get_result_metadata(settings: CloudChamberSettings, result_id: str) -> ResultMetadata:
    for result in list_result_metadata(settings):
        if result.result_id == result_id:
            return result
    raise ResultIngestError(f"Result metadata not found: {result_id}")


def result_metadata_from_json(text: str) -> ResultMetadata:
    return ResultMetadata.model_validate(json.loads(text))


def _netcdf_paths(manifest: RunManifest, run_dir: Path) -> list[Path]:
    configured = [Path(path).expanduser() for path in manifest.outputs.netcdf_paths]
    existing = [path for path in configured if path.exists()]
    if existing:
        return sorted(existing)
    patterns = ("*.nc", "*.nc4", "*.cdf", "*.netcdf")
    discovered: list[Path] = []
    for pattern in patterns:
        discovered.extend(run_dir.glob(pattern))
    return sorted(set(discovered))


class _ClassifiedNetcdfPaths(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_output_paths: list[Path]
    stats_netcdf_paths: list[Path]
    other_netcdf_paths: list[Path]


class _DatasetMetadataSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dimensions: dict[str, int]
    coordinates: list[str]
    variables: list[str]
    fields: list[FieldMetadata]
    time_coordinate: str | None


def _classify_netcdf_paths(paths: list[Path]) -> _ClassifiedNetcdfPaths:
    model_output_paths: list[Path] = []
    stats_netcdf_paths: list[Path] = []
    other_netcdf_paths: list[Path] = []
    for path in sorted(paths, key=_netcdf_sort_key):
        name = path.name
        if MODEL_OUTPUT_PATTERN.match(name):
            model_output_paths.append(path)
        elif name in STATS_OUTPUT_NAMES:
            stats_netcdf_paths.append(path)
        else:
            other_netcdf_paths.append(path)
    return _ClassifiedNetcdfPaths(
        model_output_paths=model_output_paths,
        stats_netcdf_paths=stats_netcdf_paths,
        other_netcdf_paths=other_netcdf_paths,
    )


def _netcdf_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"cm1out_(\d+)", path.name)
    if match:
        return int(match.group(1)), path.name
    return 10**9, path.name


def _open_dataset(path: Path) -> Any:
    try:
        xarray = importlib.import_module("xarray")
        return xarray.open_dataset(path)
    except Exception as exc:
        raise ResultIngestError(f"Could not open NetCDF output {path}: {exc}") from exc


def _open_model_output_sequence(paths: list[Path]) -> tuple[Any, list[str], list[Path], list[Any]]:
    opened: list[Any] = []
    contributing_paths: list[Path] = []
    normalized: list[Any] = []
    skipped: list[str] = []
    for index, path in enumerate(paths):
        try:
            dataset = _open_dataset(path)
        except ResultIngestError as exc:
            skipped.append(f"{path}: {exc}")
            continue
        opened.append(dataset)
        contributing_paths.append(path)
        normalized.append(_normalize_time_dimension(dataset, index))

    if not normalized:
        skipped_detail = "; ".join(skipped) if skipped else "no files could be opened"
        raise ResultIngestError(
            f"No CM1 model-field NetCDF output files could be opened: {skipped_detail}"
        )
    if len(normalized) == 1:
        return normalized[0], skipped, contributing_paths, opened

    xarray = importlib.import_module("xarray")
    try:
        return xarray.concat(normalized, dim="time"), skipped, contributing_paths, opened
    except Exception as exc:
        raise ResultIngestError(f"Could not combine model-output NetCDF files: {exc}") from exc


def _normalize_time_dimension(dataset: Any, file_index: int) -> Any:
    if "time" not in dataset.dims:
        return dataset.expand_dims(time=[float(file_index)])
    if "time" not in dataset.coords:
        size = int(dataset.sizes["time"])
        return dataset.assign_coords(time=[float(file_index + offset) for offset in range(size)])
    return dataset


def _metadata_snapshot(dataset: Any) -> _DatasetMetadataSnapshot:
    dimensions = {str(name): int(size) for name, size in dataset.sizes.items()}
    coordinates = _ordered_coordinate_names([str(name) for name in dataset.coords])
    variables = [str(name) for name in dataset.data_vars]
    fields = [
        FieldMetadata(
            name=str(name),
            dimensions=[str(dimension) for dimension in data_array.dims],
            shape=[int(size) for size in data_array.shape],
            units=_attribute_as_string(data_array.attrs.get("units")),
        )
        for name, data_array in dataset.data_vars.items()
    ]
    return _DatasetMetadataSnapshot(
        dimensions=dimensions,
        coordinates=coordinates,
        variables=variables,
        fields=fields,
        time_coordinate=_first_present(("time", "mtime", "t"), coordinates),
    )


def _time_values(dataset: Any) -> list[float | None]:
    time_coordinate = _first_present(("time", "mtime", "t"), list(dataset.sizes))
    if time_coordinate is None:
        return [None]
    if time_coordinate not in dataset.coords:
        return [float(index) for index in range(int(dataset.sizes[time_coordinate]))]
    return [
        _to_float_or_none(value)
        for value in dataset.coords[time_coordinate].values.reshape(-1).tolist()
    ]


def _first_time_value(values: list[float | None]) -> float | None:
    return values[0] if values else None


def _last_time_value(values: list[float | None]) -> float | None:
    return values[-1] if values else None


def _merge_diagnostics(
    diagnostics_parts: list[ResultDiagnostics],
    inherited_caveats: list[str],
) -> ResultDiagnostics:
    time = _merge_time_diagnostics(diagnostics_parts)
    cloud = _merge_cloud_diagnostics([diagnostics.cloud for diagnostics in diagnostics_parts])
    vertical = _merge_vertical_velocity_diagnostics(
        [diagnostics.vertical_velocity for diagnostics in diagnostics_parts]
    )
    rain = _merge_rain_diagnostics([diagnostics.rain for diagnostics in diagnostics_parts])
    caveats = _dedupe_strings(
        [
            *inherited_caveats,
            *(caveat for diagnostics in diagnostics_parts for caveat in diagnostics.caveats),
        ]
    )
    return ResultDiagnostics(
        cloud=cloud,
        vertical_velocity=vertical,
        rain=rain,
        time=time,
        caveats=caveats,
    )


def _merge_time_diagnostics(diagnostics_parts: list[ResultDiagnostics]) -> TimeDiagnostics:
    if not diagnostics_parts:
        return TimeDiagnostics(source="unavailable", fallback_used=True)
    sources = {diagnostics.time.source for diagnostics in diagnostics_parts}
    coordinate_names = {
        diagnostics.time.coordinate_name
        for diagnostics in diagnostics_parts
        if diagnostics.time.coordinate_name is not None
    }
    fallback_used = any(diagnostics.time.fallback_used for diagnostics in diagnostics_parts)
    return TimeDiagnostics(
        source=next(iter(sources)) if len(sources) == 1 else "mixed_time_sources",
        fallback_used=fallback_used or len(sources) > 1,
        coordinate_name=next(iter(coordinate_names)) if len(coordinate_names) == 1 else None,
    )


def _merge_cloud_diagnostics(parts: list[CloudDiagnostics]) -> CloudDiagnostics:
    available_parts = [part for part in parts if part.available]
    if not available_parts:
        return CloudDiagnostics(available=False)
    first_cloud_time = _first_non_none([part.first_cloud_time_seconds for part in available_parts])
    max_qc_time = _max_time_value(
        [
            TimeValue(time_seconds=part.time_of_max_qc_seconds, value=part.max_qc_kg_kg)
            for part in available_parts
        ]
    )
    return CloudDiagnostics(
        formed=any(part.formed for part in available_parts),
        first_cloud_time_seconds=first_cloud_time,
        cloud_base_m=_min_optional([part.cloud_base_m for part in available_parts]),
        cloud_top_m=_max_optional([part.cloud_top_m for part in available_parts]),
        cloud_base_time_series=[
            point for part in available_parts for point in part.cloud_base_time_series
        ],
        cloud_top_time_series=[
            point for part in available_parts for point in part.cloud_top_time_series
        ],
        max_qc_kg_kg=max_qc_time.value,
        time_of_max_qc_seconds=max_qc_time.time_seconds,
        max_qc_height_time_series=[
            point for part in available_parts for point in part.max_qc_height_time_series
        ],
        qc_max_time_series=[point for part in available_parts for point in part.qc_max_time_series],
        cloud_fraction_time_series=[
            point for part in available_parts for point in part.cloud_fraction_time_series
        ],
        cloud_present_time_steps=[
            time for part in available_parts for time in part.cloud_present_time_steps
        ],
        available=all(part.available for part in parts),
    )


def _merge_vertical_velocity_diagnostics(
    parts: list[VerticalVelocityDiagnostics],
) -> VerticalVelocityDiagnostics:
    available_parts = [part for part in parts if part.available]
    if not available_parts:
        units = next((part.units for part in parts if part.units is not None), None)
        return VerticalVelocityDiagnostics(available=False, units=units)
    max_w_time = _max_time_value(
        [
            TimeValue(time_seconds=part.time_of_max_w_seconds, value=part.max_w_m_s)
            for part in available_parts
        ]
    )
    min_w_time = _min_time_value(
        [
            TimeValue(time_seconds=part.time_of_min_w_seconds, value=part.min_w_m_s)
            for part in available_parts
        ]
    )
    return VerticalVelocityDiagnostics(
        max_w_m_s=max_w_time.value,
        time_of_max_w_seconds=max_w_time.time_seconds,
        min_w_m_s=min_w_time.value,
        time_of_min_w_seconds=min_w_time.time_seconds,
        max_w_height_time_series=[
            point for part in available_parts for point in part.max_w_height_time_series
        ],
        w_max_time_series=[point for part in available_parts for point in part.w_max_time_series],
        w_min_time_series=[point for part in available_parts for point in part.w_min_time_series],
        units=next((part.units for part in available_parts if part.units is not None), None),
        available=all(part.available for part in parts),
    )


def _merge_rain_diagnostics(parts: list[RainDiagnostics]) -> RainDiagnostics:
    present_parts = [part for part in parts if part.available]
    if not present_parts:
        return RainDiagnostics(
            available=False, field_absent=all(part.field_absent for part in parts)
        )
    first_rain_time = _first_non_none([part.first_rain_time_seconds for part in present_parts])
    max_qr_time = _max_time_value(
        [
            TimeValue(time_seconds=part.time_of_max_qr_seconds, value=part.max_qr_kg_kg)
            for part in present_parts
        ]
    )
    present = any(part.present for part in present_parts)
    return RainDiagnostics(
        present=present,
        first_rain_time_seconds=first_rain_time,
        max_qr_kg_kg=max_qr_time.value,
        time_of_max_qr_seconds=max_qr_time.time_seconds,
        qr_max_time_series=[point for part in present_parts for point in part.qr_max_time_series],
        user_message="Rain detected." if present else "No rain detected.",
        available=all(part.available for part in parts),
        field_absent=all(part.field_absent for part in parts),
    )


def _first_non_none(values: list[float | None]) -> float | None:
    return next((value for value in values if value is not None), None)


def _min_optional(values: list[float | None]) -> float | None:
    finite_values = [value for value in values if value is not None]
    return min(finite_values) if finite_values else None


def _max_optional(values: list[float | None]) -> float | None:
    finite_values = [value for value in values if value is not None]
    return max(finite_values) if finite_values else None


def _max_time_value(values: list[TimeValue]) -> TimeValue:
    candidates = [value for value in values if value.value is not None]
    if not candidates:
        return TimeValue(time_seconds=None, value=None)
    return max(
        candidates, key=lambda value: value.value if value.value is not None else float("-inf")
    )


def _min_time_value(values: list[TimeValue]) -> TimeValue:
    candidates = [value for value in values if value.value is not None]
    if not candidates:
        return TimeValue(time_seconds=None, value=None)
    return min(
        candidates, key=lambda value: value.value if value.value is not None else float("inf")
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _result_from_dataset(
    manifest: RunManifest,
    netcdf_paths: list[Path],
    classified: _ClassifiedNetcdfPaths,
    skipped_paths: list[str],
    contributing_paths: list[Path],
    dataset: Any,
) -> ResultMetadata:
    now = datetime.now(UTC)
    dimensions = {str(name): int(size) for name, size in dataset.sizes.items()}
    coordinates = _ordered_coordinate_names([str(name) for name in dataset.coords])
    variables = [str(name) for name in dataset.data_vars]
    fields = [
        FieldMetadata(
            name=str(name),
            dimensions=[str(dimension) for dimension in data_array.dims],
            shape=[int(size) for size in data_array.shape],
            units=_attribute_as_string(data_array.attrs.get("units")),
        )
        for name, data_array in dataset.data_vars.items()
    ]
    time_coordinate = _first_present(("time", "mtime", "t"), coordinates)
    time_steps = dimensions.get(time_coordinate) if time_coordinate else None
    grid_shape = _grid_shape(dimensions)
    warnings = list(manifest.outputs.runtime_warnings)
    warnings.extend(f"skipped_netcdf_output:{path}" for path in skipped_paths)
    missing_expected = [
        field for field in ("qc", "w") if field not in variables and field not in coordinates
    ]
    if missing_expected:
        warnings.append(
            "Expected fields missing from NetCDF metadata: " + ", ".join(missing_expected)
        )
    diagnostics = compute_baseline_diagnostics(dataset, warnings)
    process_diagnostics = compute_process_diagnostics(
        diagnostics,
        scenario_id=manifest.scenario.id,
        controls=manifest.controls,
        variables=variables,
    )

    return ResultMetadata(
        result_id=f"result-{manifest.run_id}",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        scenario_name=None,
        physical_question=manifest.physical_question,
        controls=manifest.controls,
        run_size_preset=manifest.run_size_preset,
        source_lifecycle_state=manifest.lifecycle_state.value,
        source_product_state=manifest.provenance.product_state.value,
        source_model=manifest.provenance.source_model,
        input_source=_input_source(manifest),
        input_source_label=_input_source_label(manifest),
        observed_sounding=manifest.observed_sounding,
        package_family=manifest.package_family,
        package_display_name=manifest.package_display_name,
        trigger_type=manifest.trigger_type,
        trigger_parameters=manifest.trigger_parameters,
        expected_outputs=manifest.expected_outputs,
        package_caveats=manifest.package_caveats,
        manual_validation_status=manifest.manual_validation_status,
        raw_cm1_artifacts=manifest.outputs.raw_cm1_artifacts,
        netcdf_paths=[str(path) for path in netcdf_paths],
        model_output_paths=[str(path) for path in contributing_paths],
        stats_netcdf_paths=[str(path) for path in classified.stats_netcdf_paths],
        skipped_netcdf_paths=skipped_paths,
        model_output_file_count=len(contributing_paths),
        processed_artifacts=manifest.outputs.processed_artifacts,
        dimensions=dimensions,
        coordinates=coordinates,
        variables=variables,
        fields_detected=fields,
        time_coordinate=time_coordinate,
        time_steps=time_steps,
        first_output_time_seconds=_time_bound(dataset, time_coordinate, first=True),
        last_output_time_seconds=_time_bound(dataset, time_coordinate, first=False),
        time_coordinate_source=diagnostics.time.source,
        time_coordinate_fallback_used=diagnostics.time.fallback_used,
        grid_shape=grid_shape,
        warnings=warnings,
        diagnostics_summary=_diagnostics_summary(diagnostics),
        diagnostics=diagnostics,
        process_diagnostics=process_diagnostics,
        created_at=now,
        updated_at=now,
    )


def _attribute_as_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _first_present(candidates: tuple[str, ...], names: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _ordered_coordinate_names(names: list[str]) -> list[str]:
    preferred = [
        name for name in ("time", "mtime", "t", "z", "zh", "y", "yh", "x", "xh") if name in names
    ]
    remaining = sorted(name for name in names if name not in preferred)
    return preferred + remaining


def _grid_shape(dimensions: dict[str, int]) -> list[int] | None:
    preferred = [name for name in ("z", "zh", "y", "yh", "x", "xh") if name in dimensions]
    if preferred:
        return [dimensions[name] for name in preferred]
    spatial = [
        size for name, size in dimensions.items() if name.lower() not in {"time", "mtime", "t"}
    ]
    return spatial or None


def _time_bound(dataset: Any, time_coordinate: str | None, *, first: bool) -> float | None:
    if time_coordinate is None or time_coordinate not in dataset.coords:
        return None
    values = dataset.coords[time_coordinate].values.reshape(-1).tolist()
    if not values:
        return None
    value = values[0] if first else values[-1]
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_float_or_none(value: object) -> float | None:
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return None


def _input_source(manifest: RunManifest) -> str:
    return "observed_sounding" if manifest.observed_sounding else "generated_reference"


def _input_source_label(manifest: RunManifest) -> str:
    observed = manifest.observed_sounding
    if not observed:
        return "Generated reference"
    station_id = observed.get("station_id")
    station_name = observed.get("station_name")
    if station_id and station_name:
        return f"Observed sounding: {station_id} · {station_name}"
    if station_id:
        return f"Observed sounding: {station_id}"
    return "Observed sounding"


def _diagnostics_summary(diagnostics: ResultDiagnostics) -> str:
    cloud_status = "cloud formed" if diagnostics.cloud.formed else "no cloud formed"
    rain_status = "rain detected" if diagnostics.rain.present else "no rain detected"
    return f"{cloud_status}; {rain_status}"

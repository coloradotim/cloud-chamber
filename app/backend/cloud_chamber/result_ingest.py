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
    FieldQuality,
    ProcessDiagnostics,
    RainDiagnostics,
    ReflectivityDiagnostics,
    ResultDiagnostics,
    SurfaceFluxDiagnostics,
    SurfaceFluxFieldDiagnostics,
    SurfaceRainDiagnostics,
    TimeDiagnostics,
    TimeValue,
    VerticalVelocityDiagnostics,
    compute_baseline_diagnostics,
    compute_process_diagnostics,
)
from cloud_chamber.run_manifest import LifecycleState, ProductState, RunManifest, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

RESULT_METADATA_FILENAME = "result_metadata.json"
REQUIRED_OUTPUT_FIELD_ALIASES: dict[str, set[str]] = {
    "qfx": {"qfx", "lhfx"},
    "lhfx": {"qfx", "lhfx"},
}
MODEL_OUTPUT_PATTERN = re.compile(r"^cm1out_\d+\.nc(?:4)?$")
STATS_OUTPUT_NAMES = {"cm1out_stats.nc", "cm1out_stats.nc4"}
DEEP_CONVECTION_STORY_IDS = {
    "severe_thunderstorm_environment",
    "supercell_environment",
    "high_cape_pulse_storm",
    "dry_microburst_inverted_v",
    "squall_line_cold_pool_candidate",
    "elevated_convection",
}
DEEP_CONVECTION_STORY_LABELS = {
    "severe_thunderstorm_environment": "Severe thunderstorm environment",
    "supercell_environment": "Supercell-like environment",
    "high_cape_pulse_storm": "High-CAPE pulse storm",
    "dry_microburst_inverted_v": "Dry microburst / inverted-V",
    "squall_line_cold_pool_candidate": "Squall-line / cold-pool candidate",
    "elevated_convection": "Elevated convection",
}


class ResultIngestError(RuntimeError):
    """Raised when a completed run cannot be ingested into result metadata."""


class FieldMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dimensions: list[str]
    shape: list[int]
    units: str | None = None


class CandidateHypothesisComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screened_as: str | None = None
    ran_as: str
    cm1_outcome: str
    match_status: str
    match_status_label: str
    evidence: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class ResultMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    scenario_id: str
    scenario_name: str | None = None
    physical_question: str
    controls: dict[str, str | float | bool]
    run_configuration: dict[str, Any]
    source_lifecycle_state: str
    source_product_state: str
    source_model: str
    input_source: str = "generated_reference"
    input_source_label: str = "Generated reference"
    observed_sounding: dict[str, Any] | None = None
    run_recipe: str | None = None
    run_recipe_display_name: str | None = None
    recipe_id: str | None = None
    recipe_display_name: str | None = None
    assumption_set_id: str | None = None
    assumption_mode: str | None = None
    recipe_assumptions: dict[str, Any] = Field(default_factory=dict)
    required_output_fields: list[str] = Field(default_factory=list)
    missing_required_output_fields: list[str] = Field(default_factory=list)
    recipe_caveats: list[str] = Field(default_factory=list)
    trigger_type: str | None = None
    trigger_parameters: dict[str, Any] | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    run_caveats: list[str] = Field(default_factory=list)
    manual_validation_status: str | None = None
    candidate_screening: dict[str, Any] | None = None
    pre_run_validation_report: dict[str, Any] | None = None
    candidate_hypothesis_comparison: CandidateHypothesisComparison | None = None
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
        run_recipe=result.run_recipe,
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
    result = result.model_copy(
        update={"candidate_hypothesis_comparison": _candidate_hypothesis_comparison(result)}
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
    missing_required_output_fields = _missing_required_output_fields(
        manifest,
        metadata_snapshot.variables,
        metadata_snapshot.coordinates,
    )
    if missing_required_output_fields:
        warnings.append(
            "Recipe required output fields missing from NetCDF metadata: "
            + ", ".join(missing_required_output_fields)
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
        run_configuration=manifest.run_configuration,
        source_lifecycle_state=manifest.lifecycle_state.value,
        source_product_state=manifest.provenance.product_state.value,
        source_model=manifest.provenance.source_model,
        input_source=_input_source(manifest),
        input_source_label=_input_source_label(manifest),
        observed_sounding=manifest.observed_sounding,
        run_recipe=manifest.run_recipe,
        run_recipe_display_name=manifest.run_recipe_display_name,
        recipe_id=manifest.recipe_id,
        recipe_display_name=manifest.recipe_display_name,
        assumption_set_id=manifest.assumption_set_id,
        assumption_mode=manifest.assumption_mode,
        recipe_assumptions=manifest.recipe_assumptions,
        required_output_fields=manifest.required_output_fields,
        missing_required_output_fields=missing_required_output_fields,
        recipe_caveats=manifest.recipe_caveats,
        trigger_type=manifest.trigger_type,
        trigger_parameters=manifest.trigger_parameters,
        expected_outputs=manifest.expected_outputs,
        run_caveats=manifest.run_caveats,
        manual_validation_status=manifest.manual_validation_status,
        candidate_screening=manifest.candidate_screening,
        pre_run_validation_report=manifest.pre_run_validation_report,
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
    surface_rain = _merge_surface_rain_diagnostics(
        [diagnostics.surface_rain for diagnostics in diagnostics_parts]
    )
    reflectivity = _merge_reflectivity_diagnostics(
        [diagnostics.reflectivity for diagnostics in diagnostics_parts]
    )
    surface_fluxes = _merge_surface_flux_diagnostics(
        [diagnostics.surface_fluxes for diagnostics in diagnostics_parts]
    )
    field_quality = _merge_field_quality_maps(diagnostics_parts)
    field_quality_assessed = any(
        diagnostics.field_quality_assessed for diagnostics in diagnostics_parts
    )
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
        surface_rain=surface_rain,
        reflectivity=reflectivity,
        surface_fluxes=surface_fluxes,
        time=time,
        field_quality_assessed=field_quality_assessed,
        field_quality=field_quality,
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
        available=True,
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
        available=True,
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
        user_message=("Rain water aloft detected." if present else "No rain water aloft detected."),
        available=True,
        field_absent=all(part.field_absent for part in parts),
    )


def _merge_surface_rain_diagnostics(parts: list[SurfaceRainDiagnostics]) -> SurfaceRainDiagnostics:
    present_parts = [part for part in parts if part.available]
    if not present_parts:
        return SurfaceRainDiagnostics(
            available=False,
            field_absent=all(part.field_absent for part in parts),
            units=next((part.units for part in parts if part.units is not None), None),
        )
    max_surface_rain_time = _max_time_value(
        [
            TimeValue(
                time_seconds=part.time_of_max_surface_rain_seconds,
                value=part.max_surface_rain,
            )
            for part in present_parts
        ]
    )
    present = any(part.present for part in present_parts)
    return SurfaceRainDiagnostics(
        present=present,
        max_surface_rain=max_surface_rain_time.value,
        time_of_max_surface_rain_seconds=max_surface_rain_time.time_seconds,
        surface_rain_max_time_series=[
            point for part in present_parts for point in part.surface_rain_max_time_series
        ],
        units=next((part.units for part in present_parts if part.units is not None), None),
        user_message=(
            "Surface rain reached the ground." if present else "No surface rain reached the ground."
        ),
        available=True,
        field_absent=all(part.field_absent for part in parts),
    )


def _merge_reflectivity_diagnostics(
    parts: list[ReflectivityDiagnostics],
) -> ReflectivityDiagnostics:
    present_parts = [part for part in parts if part.available]
    if not present_parts:
        return ReflectivityDiagnostics(
            available=False,
            field_absent=all(part.field_absent for part in parts),
            units=next((part.units for part in parts if part.units is not None), None),
        )
    max_dbz_time = _max_time_value(
        [
            TimeValue(time_seconds=part.time_of_max_dbz_seconds, value=part.max_dbz)
            for part in present_parts
        ]
    )
    return ReflectivityDiagnostics(
        max_dbz=max_dbz_time.value,
        time_of_max_dbz_seconds=max_dbz_time.time_seconds,
        dbz_max_time_series=[point for part in present_parts for point in part.dbz_max_time_series],
        units=next((part.units for part in present_parts if part.units is not None), None),
        user_message=(
            "Reflectivity field available."
            if max_dbz_time.value is not None
            else "Reflectivity unavailable."
        ),
        available=True,
        field_absent=all(part.field_absent for part in parts),
    )


def _merge_surface_flux_diagnostics(
    parts: list[SurfaceFluxDiagnostics],
) -> SurfaceFluxDiagnostics:
    return SurfaceFluxDiagnostics(
        hfx=_merge_surface_flux_field_diagnostics("hfx", [part.hfx for part in parts]),
        qfx=_merge_surface_flux_field_diagnostics("qfx", [part.qfx for part in parts]),
    )


def _merge_surface_flux_field_diagnostics(
    source_field: str,
    parts: list[SurfaceFluxFieldDiagnostics],
) -> SurfaceFluxFieldDiagnostics:
    if not parts:
        return SurfaceFluxFieldDiagnostics(source_field=source_field)
    available_parts = [part for part in parts if part.available]
    finite_count = sum(part.finite_count for part in parts)
    non_finite_count = sum(part.non_finite_count for part in parts)
    total_count = sum(part.total_count for part in parts)
    units = next((part.units for part in parts if part.units is not None), None)
    caveats = _dedupe_strings([caveat for part in parts for caveat in part.caveats])
    if not available_parts:
        return SurfaceFluxFieldDiagnostics(
            source_field=source_field,
            available=False,
            field_absent=all(part.field_absent for part in parts),
            units=units,
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            caveats=caveats,
        )

    weighted_total = sum(
        (part.mean_value or 0.0) * part.finite_count
        for part in available_parts
        if part.mean_value is not None
    )
    return SurfaceFluxFieldDiagnostics(
        source_field=source_field,
        available=True,
        field_absent=False,
        min_value=_min_optional([part.min_value for part in available_parts]),
        max_value=_max_optional([part.max_value for part in available_parts]),
        mean_value=weighted_total / finite_count if finite_count > 0 else None,
        units=units,
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
        caveats=caveats,
    )


FIELD_QUALITY_MERGE_ORDER = ("qc", "w", "qr", "surface_rain", "dbz", "hfx", "qfx")
FIELD_QUALITY_COMPARISON_ORDER = ("qc", "w", "qr", "surface_rain", "dbz")


def _merge_field_quality_maps(
    diagnostics_parts: list[ResultDiagnostics],
) -> dict[str, FieldQuality]:
    field_names = [
        field
        for field in FIELD_QUALITY_MERGE_ORDER
        if any(field in diagnostics.field_quality for diagnostics in diagnostics_parts)
    ]
    return {
        field: _merge_field_quality(
            field,
            [
                diagnostics.field_quality[field]
                for diagnostics in diagnostics_parts
                if field in diagnostics.field_quality
            ],
        )
        for field in field_names
    }


def _merge_field_quality(field: str, qualities: list[FieldQuality]) -> FieldQuality:
    source_field = next((quality.source_field for quality in qualities), field)
    finite_count = sum(quality.finite_count for quality in qualities)
    non_finite_count = sum(quality.non_finite_count for quality in qualities)
    total_count = sum(quality.total_count for quality in qualities)
    caveats = _dedupe_strings([caveat for quality in qualities for caveat in quality.caveats])
    reason = next(
        (
            quality.reason
            for quality in qualities
            if quality.quality_state != "trusted" and quality.reason is not None
        ),
        None,
    )

    if total_count == 0 and finite_count == 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="unavailable",
            reason=reason,
            caveats=caveats,
        )
    if finite_count == 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="untrusted",
            reason=reason,
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            caveats=caveats,
        )
    if non_finite_count > 0 or any(
        quality.quality_state in {"caveated", "untrusted", "unavailable"} for quality in qualities
    ):
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="caveated",
            reason=reason,
            finite_count=finite_count,
            non_finite_count=non_finite_count,
            total_count=total_count,
            caveats=caveats,
        )
    return FieldQuality(
        field=field,
        source_field=source_field,
        quality_state="trusted",
        finite_count=finite_count,
        non_finite_count=non_finite_count,
        total_count=total_count,
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
    missing_required_output_fields = _missing_required_output_fields(
        manifest,
        variables,
        coordinates,
    )
    if missing_required_output_fields:
        warnings.append(
            "Recipe required output fields missing from NetCDF metadata: "
            + ", ".join(missing_required_output_fields)
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
        run_configuration=manifest.run_configuration,
        source_lifecycle_state=manifest.lifecycle_state.value,
        source_product_state=manifest.provenance.product_state.value,
        source_model=manifest.provenance.source_model,
        input_source=_input_source(manifest),
        input_source_label=_input_source_label(manifest),
        observed_sounding=manifest.observed_sounding,
        run_recipe=manifest.run_recipe,
        run_recipe_display_name=manifest.run_recipe_display_name,
        recipe_id=manifest.recipe_id,
        recipe_display_name=manifest.recipe_display_name,
        assumption_set_id=manifest.assumption_set_id,
        assumption_mode=manifest.assumption_mode,
        recipe_assumptions=manifest.recipe_assumptions,
        required_output_fields=manifest.required_output_fields,
        missing_required_output_fields=missing_required_output_fields,
        recipe_caveats=manifest.recipe_caveats,
        trigger_type=manifest.trigger_type,
        trigger_parameters=manifest.trigger_parameters,
        expected_outputs=manifest.expected_outputs,
        run_caveats=manifest.run_caveats,
        manual_validation_status=manifest.manual_validation_status,
        candidate_screening=manifest.candidate_screening,
        pre_run_validation_report=manifest.pre_run_validation_report,
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


def _missing_required_output_fields(
    manifest: RunManifest,
    variables: list[str],
    coordinates: list[str],
) -> list[str]:
    available = set(variables) | set(coordinates)
    return [
        field
        for field in manifest.required_output_fields
        if not (REQUIRED_OUTPUT_FIELD_ALIASES.get(field, {field}) & available)
    ]


def _candidate_hypothesis_comparison(
    result: ResultMetadata,
) -> CandidateHypothesisComparison | None:
    screening = result.candidate_screening
    if not screening:
        return None

    primary_story = _screening_string(screening.get("primary_story"))
    screened_as = _candidate_story_label(primary_story)
    ran_as = (
        result.recipe_display_name
        or result.run_recipe_display_name
        or _display_run_recipe(result.run_recipe)
    )
    if result.scenario_name and ran_as == "CM1 run":
        ran_as = result.scenario_name

    science_summary = result.science_summary
    diagnostics = result.diagnostics
    if science_summary is None or diagnostics is None:
        return CandidateHypothesisComparison(
            screened_as=screened_as,
            ran_as=ran_as,
            cm1_outcome="Inconclusive because result diagnostics are unavailable.",
            match_status="inconclusive",
            match_status_label="Inconclusive",
            caveats=[
                "candidate_screening_is_a_pre_run_hypothesis",
                "result_diagnostics_unavailable",
            ],
        )

    evidence = _candidate_outcome_evidence(science_summary)
    field_quality_caveats = _field_quality_comparison_caveats(diagnostics)
    caveats = [
        "candidate_screening_is_a_pre_run_hypothesis",
        "candidate_match_uses_simple_v1_deep_convection_rules",
        *field_quality_caveats,
    ]
    if primary_story not in DEEP_CONVECTION_STORY_IDS:
        return CandidateHypothesisComparison(
            screened_as=screened_as,
            ran_as=ran_as,
            cm1_outcome=science_summary.cm1_outcome
            or "CM1 outcome was ingested, but no deep-convection comparison is available.",
            match_status="not_comparable",
            match_status_label="Not comparable",
            evidence=evidence,
            caveats=_dedupe_strings(
                [*caveats, "candidate_story_not_in_deep_convection_v1_rule_set"]
            ),
        )
    if not diagnostics.cloud.available or not diagnostics.vertical_velocity.available:
        return CandidateHypothesisComparison(
            screened_as=screened_as,
            ran_as=ran_as,
            cm1_outcome=science_summary.cm1_outcome
            or "Inconclusive because required cloud or updraft fields are missing.",
            match_status="inconclusive",
            match_status_label="Inconclusive",
            evidence=evidence,
            caveats=_dedupe_strings([*caveats, "missing_qc_or_w_fields"]),
        )

    deep_cloud = science_summary.deep_cloud_formed is True
    strong_updraft = science_summary.strong_updraft_formed is True
    rain_water_aloft_detected = diagnostics.rain.available and diagnostics.rain.present
    missing_comparison_fields = [
        field
        for field in result.missing_required_output_fields
        if field in {"qc", "w", "qr", "rain", "dbz", "hfx", "qfx", "lhfx"}
    ]
    if (
        deep_cloud
        and strong_updraft
        and rain_water_aloft_detected
        and not missing_comparison_fields
    ):
        match_status = "supported"
    elif deep_cloud or strong_updraft or rain_water_aloft_detected:
        match_status = "partially_supported"
    else:
        match_status = "inconclusive"

    if not diagnostics.rain.available:
        caveats.append("rain_water_aloft_field_missing_or_unavailable")
    if missing_comparison_fields:
        caveats.append(
            "required_output_fields_missing_for_deep_candidate_comparison:"
            + ",".join(missing_comparison_fields)
        )
    if match_status == "inconclusive":
        caveats.append("no_storm_under_selected_surface_forcing_is_not_failed_potential")

    return CandidateHypothesisComparison(
        screened_as=screened_as,
        ran_as=ran_as,
        cm1_outcome=science_summary.cm1_outcome
        or _deep_candidate_cm1_outcome(science_summary, diagnostics),
        match_status=match_status,
        match_status_label=_match_status_label(match_status),
        evidence=evidence,
        caveats=_dedupe_strings(caveats),
    )


def _candidate_outcome_evidence(science_summary: ScienceSummary) -> list[str]:
    evidence: list[str] = []
    if science_summary.deep_cloud_formed is not None:
        evidence.append(
            "deep cloud formed" if science_summary.deep_cloud_formed else "no deep cloud detected"
        )
    if science_summary.highest_cloud_top_m is not None:
        evidence.append(f"cloud top {_format_metric(science_summary.highest_cloud_top_m, 'm')}")
    if science_summary.max_updraft_w_m_s is not None:
        evidence.append(f"max updraft {_format_metric(science_summary.max_updraft_w_m_s, 'm/s')}")
    if science_summary.rain_onset_time_seconds is not None:
        evidence.append(
            f"rain-water-aloft onset {_format_seconds(science_summary.rain_onset_time_seconds)}"
        )
    elif science_summary.max_qr_kg_kg is not None:
        evidence.append(
            f"max rain water aloft {_format_scientific(science_summary.max_qr_kg_kg)} kg/kg"
        )
    if science_summary.time_of_first_deep_convection_seconds is not None:
        evidence.append(
            "first deep convection "
            f"{_format_seconds(science_summary.time_of_first_deep_convection_seconds)}"
        )
    return evidence


def _field_quality_comparison_caveats(diagnostics: ResultDiagnostics) -> list[str]:
    if not diagnostics.field_quality_assessed:
        return ["field_quality_not_assessed"]
    caveats: list[str] = []
    for field in FIELD_QUALITY_COMPARISON_ORDER:
        quality = diagnostics.field_quality.get(field)
        if quality is None or quality.quality_state == "trusted":
            continue
        caveat = f"field_quality_{quality.quality_state}:{field}"
        if quality.reason:
            caveat = f"{caveat}:{quality.reason}"
        if quality.total_count > 0:
            caveat = (
                f"{caveat}:finite={quality.finite_count}:"
                f"non_finite={quality.non_finite_count}:total={quality.total_count}"
            )
        caveats.append(caveat)
    return caveats


def _screening_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _candidate_story_label(story: str | None) -> str | None:
    if story is None:
        return None
    return DEEP_CONVECTION_STORY_LABELS.get(story, story.replace("_", " ").title())


def _display_run_recipe(run_recipe: str | None) -> str:
    if run_recipe == "observed_surface_forced_evolution":
        return "Observed Surface-Forced Evolution"
    return "CM1 run"


def _deep_candidate_cm1_outcome(
    science_summary: ScienceSummary,
    diagnostics: ResultDiagnostics,
) -> str:
    deep_cloud = science_summary.deep_cloud_formed is True
    strong_updraft = science_summary.strong_updraft_formed is True
    rain_water_aloft = diagnostics.rain.available and diagnostics.rain.present
    surface_rain = diagnostics.surface_rain.available and diagnostics.surface_rain.present is True
    if deep_cloud and strong_updraft and rain_water_aloft and surface_rain:
        return "Deep convection formed with strong updraft, rain water aloft, and surface rain."
    if deep_cloud and strong_updraft and rain_water_aloft:
        return "Deep convection formed with strong updraft and rain water aloft."
    if deep_cloud and strong_updraft:
        return "Deep convection formed with strong updraft."
    if deep_cloud or strong_updraft or rain_water_aloft:
        return (
            "Some deep-candidate evidence appeared, but the full deep-convection signature did not."
        )
    return (
        "Deep convection did not occur under this run configuration by current "
        "cloud-top and updraft thresholds; this does not disprove the sounding's "
        "deep-convection potential."
    )


def _match_status_label(match_status: str) -> str:
    return {
        "supported": "Supported",
        "partially_supported": "Partially supported",
        "inconclusive": "Inconclusive",
        "not_comparable": "Not comparable",
    }.get(match_status, match_status.replace("_", " ").title())


def _format_metric(value: float, units: str) -> str:
    return f"{value:g} {units}"


def _format_seconds(value: float) -> str:
    return f"{value:g} s"


def _format_scientific(value: float) -> str:
    return f"{value:.3e}"


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
    cloud_status = (
        "cloud formed"
        if diagnostics.cloud.available and diagnostics.cloud.formed
        else "no cloud formed"
        if diagnostics.cloud.available
        else "cloud unavailable"
    )
    rain_water_status = (
        "rain water aloft detected"
        if diagnostics.rain.available and diagnostics.rain.present
        else "no rain water aloft detected"
        if diagnostics.rain.available
        else "rain water aloft unavailable"
    )
    if diagnostics.surface_rain.available:
        surface_status = (
            "surface rain reached ground"
            if diagnostics.surface_rain.present
            else "no surface rain reached ground"
        )
    else:
        surface_status = "surface rain unavailable"
    if diagnostics.reflectivity.available:
        reflectivity_status = "reflectivity available"
    else:
        reflectivity_status = "reflectivity unavailable"
    return f"{cloud_status}; {rain_water_status}; {surface_status}; {reflectivity_status}"

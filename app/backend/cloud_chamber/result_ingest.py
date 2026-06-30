"""NetCDF result ingest metadata for completed CM1 runs."""

from __future__ import annotations

import importlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.output_products import (
    build_output_product_manifest_for_result,
    default_output_product_manifest_path,
    write_output_product_manifest,
)
from cloud_chamber.result_diagnostics import (
    ProcessDiagnostics,
    ResultDiagnostics,
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
    dataset, skipped_paths, contributing_paths, close_datasets = _open_model_output_sequence(
        classified.model_output_paths
    )
    try:
        result = _result_from_dataset(
            manifest,
            netcdf_paths,
            classified,
            skipped_paths,
            contributing_paths,
            dataset,
        )
    finally:
        for close_dataset in close_datasets:
            close = getattr(close_dataset, "close", None)
            if callable(close):
                close()

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
    result_path.write_text(result.to_json_text())
    write_output_product_manifest(product_manifest_path, product_manifest)
    return result


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


def _diagnostics_summary(diagnostics: ResultDiagnostics) -> str:
    cloud_status = "cloud formed" if diagnostics.cloud.formed else "no cloud formed"
    rain_status = "rain detected" if diagnostics.rain.present else "no rain detected"
    return f"{cloud_status}; {rain_status}"

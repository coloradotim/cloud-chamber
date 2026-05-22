"""NetCDF result ingest metadata for completed CM1 runs."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.run_manifest import LifecycleState, ProductState, RunManifest, load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

RESULT_METADATA_FILENAME = "result_metadata.json"


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
    processed_artifacts: list[str] = Field(default_factory=list)
    visualization_ready_artifacts: list[str] = Field(default_factory=list)
    dimensions: dict[str, int] = Field(default_factory=dict)
    coordinates: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    fields_detected: list[FieldMetadata] = Field(default_factory=list)
    time_coordinate: str | None = None
    time_steps: int | None = None
    grid_shape: list[int] | None = None
    warnings: list[str] = Field(default_factory=list)
    diagnostics_summary: str | None = None
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

    dataset = _open_dataset(netcdf_paths[0])
    try:
        result = _result_from_dataset(manifest, netcdf_paths, dataset)
    finally:
        close = getattr(dataset, "close", None)
        if callable(close):
            close()

    result_path = run_dir / RESULT_METADATA_FILENAME
    result_path.write_text(result.to_json_text())
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


def _open_dataset(path: Path) -> Any:
    try:
        xarray = importlib.import_module("xarray")
        return xarray.open_dataset(path)
    except Exception as exc:
        raise ResultIngestError(f"Could not open NetCDF output {path}: {exc}") from exc


def _result_from_dataset(
    manifest: RunManifest,
    netcdf_paths: list[Path],
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
    missing_expected = [
        field for field in ("qc", "w") if field not in variables and field not in coordinates
    ]
    if missing_expected:
        warnings.append(
            "Expected fields missing from NetCDF metadata: " + ", ".join(missing_expected)
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
        processed_artifacts=manifest.outputs.processed_artifacts,
        dimensions=dimensions,
        coordinates=coordinates,
        variables=variables,
        fields_detected=fields,
        time_coordinate=time_coordinate,
        time_steps=time_steps,
        grid_shape=grid_shape,
        warnings=warnings,
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

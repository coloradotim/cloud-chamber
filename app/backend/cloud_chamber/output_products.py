"""Runtime-local output product manifest contracts.

The output product manifest indexes CM1 output without making the browser infer
file/time relationships or parse raw NetCDF. It is a small, rebuildable runtime
artifact that points back to CM1-owned source files.
"""

from __future__ import annotations

import importlib
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.result_diagnostics import ResultDiagnostics, TimeValue

OUTPUT_PRODUCT_MANIFEST_VERSION = 1
DERIVED_PRODUCTS_DIRNAME = "derived-products"
OUTPUT_PRODUCT_MANIFEST_FILENAME = "output_product_manifest.json"

MODEL_OUTPUT_PATTERN = re.compile(r"^cm1out_\d+\.nc(?:4)?$")
STATS_OUTPUT_NAMES = {"cm1out_stats.nc", "cm1out_stats.nc4"}
TIME_COORDINATE_CANDIDATES = ("time", "mtime", "t")

SourceFileKind = Literal["model_output_netcdf", "stats_netcdf", "raw_cm1_artifact"]
TimeSource = Literal["netcdf_time_coordinate", "inferred_filename_order"]
InterestingTimeSupportState = Literal[
    "supported",
    "fallback",
    "unavailable",
    "unsupported_missing_fields",
    "unsupported_missing_diagnostic",
]

DEEP_CLOUD_TOP_THRESHOLD_M = 8000.0
STRONG_UPDRAFT_THRESHOLD_M_S = 10.0


class OutputProductManifestError(RuntimeError):
    """Raised when an output product manifest cannot be built or resolved."""


class OutputTimeIndexEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_index: int
    time_seconds: float | None = None
    source_time_value: float | str | None = None
    source_file: str
    source_file_kind: SourceFileKind
    local_time_index: int
    time_source: TimeSource
    time_caveats: list[str] = Field(default_factory=list)


class SourceRawOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_output_files: list[str] = Field(default_factory=list)
    stats_files: list[str] = Field(default_factory=list)
    raw_cm1_artifacts: list[str] = Field(default_factory=list)


class OutputProductCache(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_root: str
    cache_key: str | None = None
    invalidated: bool = False


class OutputProductProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_model: str = "CM1"
    processing_method: str = "backend_output_product_manifest_time_index"
    provenance_label: str = (
        "CM1 output product manifest; backend-resolved file/time mapping; "
        "raw NetCDF stays local and backend-owned"
    )


class InterestingTimeProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_model: str = "CM1"
    processing_method: str = "backend_output_product_interesting_times"
    provenance_label: str = (
        "CM1-derived interesting-time product; backend diagnostics plus output "
        "manifest time-index mapping; raw NetCDF stays backend-owned"
    )


class InterestingTimeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    time_index: int | None = None
    time_seconds: float | None = None
    source_time_value: float | str | None = None
    source_field: str | None = None
    source_diagnostic: str | None = None
    value: float | bool | None = None
    units: str | None = None
    support_state: InterestingTimeSupportState
    provenance: InterestingTimeProvenance = Field(default_factory=InterestingTimeProvenance)
    caveats: list[str] = Field(default_factory=list)
    fallback_reason: str | None = None


class FieldDefaultTime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    time_index: int | None = None
    time_seconds: float | None = None
    source_interesting_time_key: str
    support_state: InterestingTimeSupportState
    fallback_reason: str | None = None
    caveats: list[str] = Field(default_factory=list)


class ScienceDiagnosticAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    support_state: InterestingTimeSupportState
    source_field: str | None = None
    value: float | bool | None = None
    units: str | None = None
    caveats: list[str] = Field(default_factory=list)


class ScienceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud_formed: bool | None = None
    deep_cloud_formed: bool | None = None
    deep_cloud_threshold_m: float = DEEP_CLOUD_TOP_THRESHOLD_M
    strong_updraft_formed: bool | None = None
    strong_updraft_threshold_m_s: float = STRONG_UPDRAFT_THRESHOLD_M_S
    first_cloud_time_seconds: float | None = None
    first_cloud_time_label: str | None = None
    time_of_first_deep_convection_seconds: float | None = None
    max_qc_kg_kg: float | None = None
    max_qc_time_seconds: float | None = None
    max_updraft_w_m_s: float | None = None
    max_updraft_time_seconds: float | None = None
    min_downdraft_w_m_s: float | None = None
    min_downdraft_time_seconds: float | None = None
    highest_cloud_top_m: float | None = None
    rain_onset_time_seconds: float | None = None
    max_qr_kg_kg: float | None = None
    max_rain_or_surface_precip: float | None = None
    max_dbz_or_reflectivity_proxy: float | None = None
    cold_pool_proxy: float | None = None
    near_surface_theta_perturbation_proxy: float | None = None
    updraft_depth_proxy_m: float | None = None
    latest_output_time_seconds: float | None = None
    default_explore_time_index: int | None = None
    default_explore_time_seconds: float | None = None
    cm1_outcome: str | None = None
    diagnostic_availability: list[ScienceDiagnosticAvailability] = Field(default_factory=list)
    interesting_time_caveats: list[str] = Field(default_factory=list)
    interesting_time_support_state: str = "unavailable"


class InterestingTimeProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    available_interesting_times: list[InterestingTimeRecord]
    default_time_by_field: dict[str, FieldDefaultTime] = Field(default_factory=dict)
    science_summary: ScienceSummary
    caveats: list[str] = Field(default_factory=list)
    provenance: InterestingTimeProvenance = Field(default_factory=InterestingTimeProvenance)


class OutputProductManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: int = OUTPUT_PRODUCT_MANIFEST_VERSION
    product_manifest_id: str
    result_id: str
    run_id: str
    scenario_id: str | None = None
    source_model: str = "CM1"
    source_result_metadata_path: str | None = None
    source_run_manifest_path: str | None = None
    source_raw_outputs: SourceRawOutputs
    time_index: list[OutputTimeIndexEntry]
    interesting_time_product: InterestingTimeProduct | None = None
    cache: OutputProductCache
    provenance: OutputProductProvenance = Field(default_factory=OutputProductProvenance)
    caveats: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2) + "\n"


class ClassifiedOutputPaths(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_output_paths: list[Path]
    stats_netcdf_paths: list[Path]
    other_paths: list[Path]


class ResolvedTimeIndex(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_index: int
    time_seconds: float | None = None
    source_file: str
    source_file_kind: SourceFileKind
    local_time_index: int
    time_source: TimeSource
    time_caveats: list[str] = Field(default_factory=list)


def default_output_product_root(run_dir: Path) -> Path:
    """Return the runtime-local derived product root for a run directory."""
    return run_dir / DERIVED_PRODUCTS_DIRNAME


def default_output_product_manifest_path(run_dir: Path) -> Path:
    """Return the runtime-local output product manifest path for a run."""
    return default_output_product_root(run_dir) / OUTPUT_PRODUCT_MANIFEST_FILENAME


def output_product_manifest_from_json(text: str) -> OutputProductManifest:
    """Parse an output product manifest JSON string."""
    return OutputProductManifest.model_validate(json.loads(text))


def write_output_product_manifest(path: Path, manifest: OutputProductManifest) -> None:
    """Write an output product manifest, creating the runtime product directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.to_json_text())


def classify_output_paths(paths: list[Path]) -> ClassifiedOutputPaths:
    """Classify CM1 output paths without treating stats files as model fields."""
    model_output_paths: list[Path] = []
    stats_netcdf_paths: list[Path] = []
    other_paths: list[Path] = []
    for path in sorted(paths, key=_output_sort_key):
        if MODEL_OUTPUT_PATTERN.match(path.name):
            model_output_paths.append(path)
        elif path.name in STATS_OUTPUT_NAMES:
            stats_netcdf_paths.append(path)
        else:
            other_paths.append(path)
    return ClassifiedOutputPaths(
        model_output_paths=model_output_paths,
        stats_netcdf_paths=stats_netcdf_paths,
        other_paths=other_paths,
    )


def build_output_product_manifest_for_result(
    result_metadata: Any,
    *,
    result_metadata_path: Path | None = None,
    run_manifest_path: Path | None = None,
    product_root: Path | None = None,
) -> OutputProductManifest:
    """Build an output product manifest from an existing result metadata object."""
    model_output_paths = [Path(path).expanduser() for path in result_metadata.model_output_paths]
    stats_paths = [Path(path).expanduser() for path in result_metadata.stats_netcdf_paths]
    raw_paths = [Path(path).expanduser() for path in result_metadata.raw_cm1_artifacts]
    if product_root is None:
        inferred_run_dir = (
            result_metadata_path.parent
            if result_metadata_path is not None
            else _common_parent(model_output_paths + stats_paths + raw_paths)
        )
        product_root = default_output_product_root(inferred_run_dir)
    return build_output_product_manifest(
        result_id=str(result_metadata.result_id),
        run_id=str(result_metadata.run_id),
        scenario_id=getattr(result_metadata, "scenario_id", None),
        source_model=str(getattr(result_metadata, "source_model", "CM1")),
        model_output_paths=model_output_paths,
        stats_netcdf_paths=stats_paths,
        raw_cm1_artifacts=raw_paths,
        source_result_metadata_path=result_metadata_path,
        source_run_manifest_path=run_manifest_path,
        product_root=product_root,
        inherited_caveats=[
            *[str(warning) for warning in getattr(result_metadata, "warnings", [])],
            *[
                f"skipped_netcdf_output:{path}"
                for path in getattr(result_metadata, "skipped_netcdf_paths", [])
            ],
        ],
    )


def build_output_product_manifest(
    *,
    result_id: str,
    run_id: str,
    model_output_paths: list[Path],
    stats_netcdf_paths: list[Path] | None = None,
    raw_cm1_artifacts: list[Path] | None = None,
    scenario_id: str | None = None,
    source_model: str = "CM1",
    source_result_metadata_path: Path | None = None,
    source_run_manifest_path: Path | None = None,
    product_root: Path,
    inherited_caveats: list[str] | None = None,
) -> OutputProductManifest:
    """Build an output product manifest and global time index.

    Each model-output file is opened independently to inspect only time
    coordinates. The files are never concatenated here.
    """
    stats_netcdf_paths = stats_netcdf_paths or []
    raw_cm1_artifacts = raw_cm1_artifacts or []
    now = datetime.now(UTC)
    time_entries, time_caveats = build_time_index(model_output_paths)
    caveats = _dedupe([*(inherited_caveats or []), *time_caveats])
    if not time_entries:
        raise OutputProductManifestError("No model-output timesteps could be indexed.")
    return OutputProductManifest(
        product_manifest_id=f"output-products-{result_id}",
        result_id=result_id,
        run_id=run_id,
        scenario_id=scenario_id,
        source_model=source_model,
        source_result_metadata_path=str(source_result_metadata_path)
        if source_result_metadata_path
        else None,
        source_run_manifest_path=str(source_run_manifest_path)
        if source_run_manifest_path
        else None,
        source_raw_outputs=SourceRawOutputs(
            model_output_files=[
                str(path) for path in sorted(model_output_paths, key=_output_sort_key)
            ],
            stats_files=[str(path) for path in sorted(stats_netcdf_paths, key=_output_sort_key)],
            raw_cm1_artifacts=[
                str(path) for path in sorted(raw_cm1_artifacts, key=_output_sort_key)
            ],
        ),
        time_index=time_entries,
        cache=OutputProductCache(
            product_root=str(product_root),
            cache_key=_cache_key(model_output_paths, stats_netcdf_paths, raw_cm1_artifacts),
        ),
        provenance=OutputProductProvenance(source_model=source_model),
        caveats=caveats,
        created_at=now,
        updated_at=now,
    )


def build_time_index(
    model_output_paths: list[Path],
) -> tuple[list[OutputTimeIndexEntry], list[str]]:
    """Build a global time index from model-output NetCDF files."""
    entries: list[OutputTimeIndexEntry] = []
    caveats: list[str] = []
    original_numeric_times: list[float | None] = []
    sorted_paths = sorted(model_output_paths, key=_output_sort_key)
    for file_order, path in enumerate(sorted_paths):
        if path.name in STATS_OUTPUT_NAMES:
            caveats.append(f"stats_file_excluded_from_model_time_index:{path}")
            continue
        if not MODEL_OUTPUT_PATTERN.match(path.name):
            caveats.append(f"non_model_netcdf_excluded_from_time_index:{path}")
            continue
        if not path.exists():
            caveats.append(f"missing_model_output_file:{path}")
            continue
        try:
            file_entries = _time_entries_for_file(path, file_order)
        except OutputProductManifestError as exc:
            caveats.append(f"skipped_model_output_file:{path}:{exc}")
            continue
        entries.extend(file_entries)
        original_numeric_times.extend(entry.time_seconds for entry in file_entries)

    if not entries:
        return [], _dedupe([*caveats, "no_model_output_files_indexed"])

    all_direct_numeric = all(
        entry.time_source == "netcdf_time_coordinate" and entry.time_seconds is not None
        for entry in entries
    )
    if all_direct_numeric:
        entries = sorted(
            entries,
            key=lambda entry: (
                float(entry.time_seconds) if entry.time_seconds is not None else math.inf,
                entry.source_file,
                entry.local_time_index,
            ),
        )
    else:
        caveats.append("global_time_index_preserves_filename_order_due_to_inferred_times")

    caveats.extend(_time_order_caveats(original_numeric_times, entries))
    entries = _flag_duplicate_entry_times(entries)
    return [
        entry.model_copy(update={"time_index": time_index})
        for time_index, entry in enumerate(entries)
    ], _dedupe(caveats)


def resolve_time_index(manifest: OutputProductManifest, time_index: int) -> ResolvedTimeIndex:
    """Resolve a global time index to the source file and local file index."""
    if time_index < 0:
        raise OutputProductManifestError("time_index must be non-negative.")
    for entry in manifest.time_index:
        if entry.time_index == time_index:
            return ResolvedTimeIndex(
                time_index=entry.time_index,
                time_seconds=entry.time_seconds,
                source_file=entry.source_file,
                source_file_kind=entry.source_file_kind,
                local_time_index=entry.local_time_index,
                time_source=entry.time_source,
                time_caveats=entry.time_caveats,
            )
    raise OutputProductManifestError(f"time_index is not available: {time_index}")


def build_interesting_time_product(
    *,
    result_id: str,
    diagnostics: ResultDiagnostics | None,
    output_manifest: OutputProductManifest,
    variables: list[str],
    package_family: str | None = None,
) -> InterestingTimeProduct:
    """Build small science time landmarks from diagnostics and manifest time mapping."""
    records = _interesting_time_records(
        diagnostics=diagnostics,
        output_manifest=output_manifest,
        variables=set(variables),
        package_family=package_family,
    )
    defaults = _field_defaults(records)
    summary = _science_summary(
        diagnostics,
        output_manifest,
        records,
        defaults,
        variables=set(variables),
        package_family=package_family,
    )
    caveats = _dedupe(
        [
            *(output_manifest.caveats or []),
            *(diagnostics.caveats if diagnostics else []),
            *(caveat for record in records for caveat in record.caveats),
            *(caveat for default in defaults.values() for caveat in default.caveats),
        ]
    )
    return InterestingTimeProduct(
        result_id=result_id,
        available_interesting_times=records,
        default_time_by_field=defaults,
        science_summary=summary.model_copy(update={"interesting_time_caveats": caveats}),
        caveats=caveats,
    )


def _interesting_time_records(
    *,
    diagnostics: ResultDiagnostics | None,
    output_manifest: OutputProductManifest,
    variables: set[str],
    package_family: str | None,
) -> list[InterestingTimeRecord]:
    latest = _latest_time_record(output_manifest)
    if diagnostics is None:
        return [
            _unavailable_record(
                key="first_cloud",
                label="First cloud",
                source_field="qc",
                source_diagnostic="diagnostics.cloud.first_cloud_time_seconds",
                support_state="unsupported_missing_diagnostic",
                caveat="diagnostics_unavailable",
            ),
            latest,
            _field_default_record(latest, fallback_reason="diagnostics_unavailable"),
        ]

    cloud = diagnostics.cloud
    vertical = diagnostics.vertical_velocity
    rain = diagnostics.rain
    records = [
        _event_record(
            key="first_cloud",
            label="First cloud",
            time_seconds=cloud.first_cloud_time_seconds
            if cloud.available and cloud.formed
            else None,
            source_field="qc",
            source_diagnostic="diagnostics.cloud.first_cloud_time_seconds",
            value=cloud.formed if cloud.available else None,
            units=None,
            output_manifest=output_manifest,
            unavailable_caveat="no_cloud_formed" if cloud.available else "missing_qc_field",
            support_state="unavailable" if cloud.available else "unsupported_missing_fields",
        ),
        _event_record(
            key="max_qc",
            label="Max cloud water",
            time_seconds=cloud.time_of_max_qc_seconds
            if cloud.available and _positive(cloud.max_qc_kg_kg)
            else None,
            source_field="qc",
            source_diagnostic="diagnostics.cloud.max_qc_kg_kg",
            value=cloud.max_qc_kg_kg if cloud.available else None,
            units="kg/kg",
            output_manifest=output_manifest,
            unavailable_caveat="no_positive_cloud_water_detected"
            if cloud.available
            else "missing_qc_field",
            support_state="unavailable" if cloud.available else "unsupported_missing_fields",
        ),
        _series_max_record(
            key="highest_cloud_top",
            label="Highest cloud top",
            series=cloud.cloud_top_time_series if cloud.available else [],
            source_field="qc+qr+qi+qs+qg when available",
            source_diagnostic="diagnostics.cloud.cloud_top_time_series",
            units="m",
            output_manifest=output_manifest,
            unavailable_caveat="no_cloud_top_detected" if cloud.available else "missing_qc_field",
            support_state="unavailable" if cloud.available else "unsupported_missing_fields",
        ),
        _event_record(
            key="first_deep_convection",
            label="First deep convection",
            time_seconds=_first_deep_convection_time(diagnostics) if cloud.available else None,
            source_field="qc+qr+qi+qs+qg when available",
            source_diagnostic="diagnostics.cloud.cloud_top_time_series",
            value=_deep_cloud_formed(diagnostics) if cloud.available else None,
            units=None,
            output_manifest=output_manifest,
            unavailable_caveat="no_deep_cloud_detected" if cloud.available else "missing_qc_field",
            support_state="unavailable" if cloud.available else "unsupported_missing_fields",
        )
        if package_family == "deep_convection_trial"
        else None,
        _event_record(
            key="max_updraft_w",
            label="Max updraft",
            time_seconds=vertical.time_of_max_w_seconds if vertical.available else None,
            source_field="w",
            source_diagnostic="diagnostics.vertical_velocity.max_w_m_s",
            value=vertical.max_w_m_s if vertical.available else None,
            units=vertical.units or "m/s",
            output_manifest=output_manifest,
            unavailable_caveat="missing_w_field",
            support_state="unsupported_missing_fields",
        ),
        _event_record(
            key="min_downdraft_w",
            label="Min downdraft",
            time_seconds=vertical.time_of_min_w_seconds if vertical.available else None,
            source_field="w",
            source_diagnostic="diagnostics.vertical_velocity.min_w_m_s",
            value=vertical.min_w_m_s if vertical.available else None,
            units=vertical.units or "m/s",
            output_manifest=output_manifest,
            unavailable_caveat="missing_w_field",
            support_state="unsupported_missing_fields",
        ),
        _event_record(
            key="rain_onset",
            label="Rain-water onset",
            time_seconds=rain.first_rain_time_seconds if rain.available and rain.present else None,
            source_field="qr",
            source_diagnostic="diagnostics.rain.first_rain_time_seconds",
            value=rain.present if rain.available else None,
            units=None,
            output_manifest=output_manifest,
            unavailable_caveat="no_rain_water_aloft_detected"
            if rain.available
            else (
                "missing_qr_field"
                if rain.field_absent
                else "rain_water_aloft_diagnostics_unavailable"
            ),
            support_state="unavailable" if rain.available else "unsupported_missing_fields",
        ),
        _event_record(
            key="max_qr",
            label="Max rain water aloft",
            time_seconds=rain.time_of_max_qr_seconds
            if rain.available and _positive(rain.max_qr_kg_kg)
            else None,
            source_field="qr",
            source_diagnostic="diagnostics.rain.max_qr_kg_kg",
            value=rain.max_qr_kg_kg if rain.available else None,
            units="kg/kg",
            output_manifest=output_manifest,
            unavailable_caveat="no_rain_water_aloft_detected"
            if rain.available
            else (
                "missing_qr_field"
                if rain.field_absent
                else "rain_water_aloft_diagnostics_unavailable"
            ),
            support_state="unavailable" if rain.available else "unsupported_missing_fields",
        ),
        _series_max_record(
            key="max_dbz",
            label="Max reflectivity",
            series=diagnostics.reflectivity.dbz_max_time_series
            if diagnostics.reflectivity.available
            else [],
            source_field="dbz",
            source_diagnostic="diagnostics.reflectivity.max_dbz",
            units=diagnostics.reflectivity.units or "dBZ",
            output_manifest=output_manifest,
            unavailable_caveat="no_reflectivity_values_detected"
            if diagnostics.reflectivity.available
            else (
                "missing_dbz_field"
                if diagnostics.reflectivity.field_absent
                else "reflectivity_diagnostics_unavailable"
            ),
            support_state="unavailable"
            if diagnostics.reflectivity.available
            else "unsupported_missing_fields",
        ),
        _series_max_record(
            key="max_surface_rain",
            label="Max surface rain",
            series=diagnostics.surface_rain.surface_rain_max_time_series
            if diagnostics.surface_rain.available and diagnostics.surface_rain.present
            else [],
            source_field="rain",
            source_diagnostic="diagnostics.surface_rain.max_surface_rain",
            units=diagnostics.surface_rain.units or "unknown",
            output_manifest=output_manifest,
            unavailable_caveat="no_surface_rain_detected"
            if diagnostics.surface_rain.available
            else (
                "missing_rain_field"
                if diagnostics.surface_rain.field_absent
                else "surface_rain_diagnostics_unavailable"
            ),
            support_state="unavailable"
            if diagnostics.surface_rain.available
            else "unsupported_missing_fields",
        ),
        latest,
    ]
    compact_records = [record for record in records if record is not None]
    compact_records.append(
        _field_default_record(
            _default_source_record(compact_records, package_family=package_family),
            fallback_reason=None,
        )
    )
    return compact_records


def _event_record(
    *,
    key: str,
    label: str,
    time_seconds: float | None,
    source_field: str,
    source_diagnostic: str,
    value: float | bool | None,
    units: str | None,
    output_manifest: OutputProductManifest,
    unavailable_caveat: str,
    support_state: InterestingTimeSupportState,
) -> InterestingTimeRecord:
    if time_seconds is None:
        return _unavailable_record(
            key=key,
            label=label,
            source_field=source_field,
            source_diagnostic=source_diagnostic,
            support_state=support_state,
            caveat=unavailable_caveat,
            value=value,
            units=units,
        )
    resolved, caveats = _resolve_time_seconds(output_manifest, time_seconds)
    if resolved is None:
        return _unavailable_record(
            key=key,
            label=label,
            source_field=source_field,
            source_diagnostic=source_diagnostic,
            support_state="unavailable",
            caveat=f"time_not_found_in_output_manifest:{time_seconds:g}",
            value=value,
            units=units,
        )
    return InterestingTimeRecord(
        key=key,
        label=label,
        time_index=resolved.time_index,
        time_seconds=resolved.time_seconds,
        source_time_value=resolved.source_time_value,
        source_field=source_field,
        source_diagnostic=source_diagnostic,
        value=value,
        units=units,
        support_state="supported",
        caveats=_dedupe([*resolved.time_caveats, *caveats]),
    )


def _series_max_record(
    *,
    key: str,
    label: str,
    series: list[TimeValue],
    source_field: str,
    source_diagnostic: str,
    units: str,
    output_manifest: OutputProductManifest,
    unavailable_caveat: str,
    support_state: InterestingTimeSupportState,
) -> InterestingTimeRecord:
    candidates = [point for point in series if point.value is not None]
    if not candidates:
        return _unavailable_record(
            key=key,
            label=label,
            source_field=source_field,
            source_diagnostic=source_diagnostic,
            support_state=support_state,
            caveat=unavailable_caveat,
            units=units,
        )
    highest = max(
        candidates, key=lambda point: point.value if point.value is not None else -math.inf
    )
    return _event_record(
        key=key,
        label=label,
        time_seconds=highest.time_seconds,
        source_field=source_field,
        source_diagnostic=source_diagnostic,
        value=highest.value,
        units=units,
        output_manifest=output_manifest,
        unavailable_caveat=unavailable_caveat,
        support_state=support_state,
    )


def _latest_time_record(output_manifest: OutputProductManifest) -> InterestingTimeRecord:
    if not output_manifest.time_index:
        return _unavailable_record(
            key="latest_output",
            label="Latest output",
            source_diagnostic="output_manifest.time_index",
            support_state="unavailable",
            caveat="time_index_unavailable",
        )
    latest = output_manifest.time_index[-1]
    return InterestingTimeRecord(
        key="latest_output",
        label="Latest output",
        time_index=latest.time_index,
        time_seconds=latest.time_seconds,
        source_time_value=latest.source_time_value,
        source_diagnostic="output_manifest.time_index",
        support_state="supported",
        caveats=list(latest.time_caveats),
    )


def _field_default_record(
    source_record: InterestingTimeRecord,
    *,
    fallback_reason: str | None,
) -> InterestingTimeRecord:
    fallback = fallback_reason or (
        None if source_record.support_state == "supported" else "no_supported_science_landmark"
    )
    return InterestingTimeRecord(
        key="field_default_time",
        label="Default Explore time",
        time_index=source_record.time_index,
        time_seconds=source_record.time_seconds,
        source_time_value=source_record.source_time_value,
        source_field=source_record.source_field,
        source_diagnostic=source_record.source_diagnostic,
        value=source_record.value,
        units=source_record.units,
        support_state="supported" if fallback is None else "fallback",
        caveats=list(source_record.caveats),
        fallback_reason=fallback,
    )


def _unsupported_field_record(
    *,
    key: str,
    label: str,
    source_field: str,
    source_diagnostic: str,
    field_present: bool,
) -> InterestingTimeRecord:
    return _unavailable_record(
        key=key,
        label=label,
        source_field=source_field,
        source_diagnostic=source_diagnostic,
        support_state="unsupported_missing_diagnostic"
        if field_present
        else "unsupported_missing_fields",
        caveat=(
            f"{source_field}_interesting_time_diagnostic_not_implemented"
            if field_present
            else f"missing_{source_field}_field"
        ),
    )


def _unavailable_record(
    *,
    key: str,
    label: str,
    source_field: str | None = None,
    source_diagnostic: str | None = None,
    support_state: InterestingTimeSupportState,
    caveat: str,
    value: float | bool | None = None,
    units: str | None = None,
) -> InterestingTimeRecord:
    return InterestingTimeRecord(
        key=key,
        label=label,
        source_field=source_field,
        source_diagnostic=source_diagnostic,
        value=value,
        units=units,
        support_state=support_state,
        caveats=[caveat],
    )


def _field_defaults(
    records: list[InterestingTimeRecord],
) -> dict[str, FieldDefaultTime]:
    by_key = {record.key: record for record in records}
    latest = by_key.get("latest_output")
    defaults: dict[str, FieldDefaultTime] = {}
    choices = {
        "qc": ("max_qc", "first_cloud"),
        "w": ("max_updraft_w",),
        "qr": ("rain_onset", "max_qr"),
        "dbz": ("max_dbz",),
        "rain": ("max_surface_rain",),
    }
    for field, keys in choices.items():
        source = next(
            (
                by_key[key]
                for key in keys
                if by_key.get(key) and by_key[key].support_state == "supported"
            ),
            None,
        )
        fallback_reason = None
        if source is None:
            source = latest
            fallback_reason = f"no_supported_{field}_interesting_time"
        if source is None:
            continue
        defaults[field] = FieldDefaultTime(
            field=field,
            time_index=source.time_index,
            time_seconds=source.time_seconds,
            source_interesting_time_key=source.key,
            support_state="supported" if fallback_reason is None else "fallback",
            fallback_reason=fallback_reason,
            caveats=list(source.caveats),
        )
    return defaults


def _science_summary(
    diagnostics: ResultDiagnostics | None,
    output_manifest: OutputProductManifest,
    records: list[InterestingTimeRecord],
    defaults: dict[str, FieldDefaultTime],
    *,
    variables: set[str],
    package_family: str | None,
) -> ScienceSummary:
    record_by_key = {record.key: record for record in records}
    default_record = record_by_key.get("field_default_time")
    latest = record_by_key.get("latest_output")
    qc_default = defaults.get("qc")
    is_deep_convection = package_family == "deep_convection_trial"
    if diagnostics is None:
        return ScienceSummary(
            latest_output_time_seconds=latest.time_seconds if latest else None,
            default_explore_time_index=default_record.time_index if default_record else None,
            default_explore_time_seconds=default_record.time_seconds if default_record else None,
            interesting_time_support_state="fallback",
            diagnostic_availability=_diagnostic_availability(variables),
        )
    supported_science_keys = {
        "first_cloud",
        "max_qc",
        "highest_cloud_top",
        "max_updraft_w",
        "min_downdraft_w",
        "rain_onset",
        "max_qr",
        "max_dbz",
        "max_surface_rain",
    }
    supported_count = sum(
        1
        for record in records
        if record.key in supported_science_keys and record.support_state == "supported"
    )
    support_state = "supported" if supported_count > 0 else "fallback"
    highest_cloud_top = _record_value(record_by_key.get("highest_cloud_top"))
    first_deep_convection = _record_time(record_by_key.get("first_deep_convection"))
    deep_cloud_formed = _deep_cloud_formed(diagnostics)
    strong_updraft_formed = _strong_updraft_formed(diagnostics)
    default_source = default_record if is_deep_convection else qc_default or default_record
    return ScienceSummary(
        cloud_formed=diagnostics.cloud.formed if diagnostics.cloud.available else None,
        deep_cloud_formed=deep_cloud_formed,
        strong_updraft_formed=strong_updraft_formed,
        first_cloud_time_seconds=diagnostics.cloud.first_cloud_time_seconds,
        first_cloud_time_label=_format_time_label(diagnostics.cloud.first_cloud_time_seconds),
        time_of_first_deep_convection_seconds=first_deep_convection,
        max_qc_kg_kg=diagnostics.cloud.max_qc_kg_kg if diagnostics.cloud.available else None,
        max_qc_time_seconds=diagnostics.cloud.time_of_max_qc_seconds
        if record_by_key.get("max_qc", None)
        and record_by_key["max_qc"].support_state == "supported"
        else None,
        max_updraft_w_m_s=diagnostics.vertical_velocity.max_w_m_s
        if diagnostics.vertical_velocity.available
        else None,
        max_updraft_time_seconds=diagnostics.vertical_velocity.time_of_max_w_seconds,
        min_downdraft_w_m_s=diagnostics.vertical_velocity.min_w_m_s
        if diagnostics.vertical_velocity.available
        else None,
        min_downdraft_time_seconds=diagnostics.vertical_velocity.time_of_min_w_seconds,
        highest_cloud_top_m=highest_cloud_top,
        rain_onset_time_seconds=diagnostics.rain.first_rain_time_seconds,
        max_qr_kg_kg=diagnostics.rain.max_qr_kg_kg if diagnostics.rain.available else None,
        max_rain_or_surface_precip=diagnostics.surface_rain.max_surface_rain
        if diagnostics.surface_rain.available
        else None,
        max_dbz_or_reflectivity_proxy=diagnostics.reflectivity.max_dbz
        if diagnostics.reflectivity.available
        else None,
        latest_output_time_seconds=latest.time_seconds
        if latest
        else _latest_manifest_time(output_manifest),
        default_explore_time_index=default_source.time_index if default_source else None,
        default_explore_time_seconds=default_source.time_seconds if default_source else None,
        cm1_outcome=_cm1_outcome(diagnostics) if is_deep_convection else None,
        diagnostic_availability=_diagnostic_availability(variables, diagnostics),
        interesting_time_support_state=support_state,
    )


def _default_source_record(
    records: list[InterestingTimeRecord],
    *,
    package_family: str | None,
) -> InterestingTimeRecord:
    by_key = {record.key: record for record in records}
    preferred_keys = (
        ("first_deep_convection", "max_updraft_w", "rain_onset", "max_qc")
        if package_family == "deep_convection_trial"
        else ("first_cloud", "max_qc", "max_updraft_w")
    )
    for key in preferred_keys:
        record = by_key.get(key)
        if record and record.support_state == "supported":
            return record
    return by_key["latest_output"]


def _resolve_time_seconds(
    manifest: OutputProductManifest, time_seconds: float
) -> tuple[OutputTimeIndexEntry | None, list[str]]:
    if not manifest.time_index:
        return None, ["time_index_unavailable"]
    direct = [entry for entry in manifest.time_index if entry.time_seconds == time_seconds]
    if direct:
        caveats: list[str] = []
        if len(direct) > 1:
            caveats.append(f"duplicate_interesting_time_seconds:{time_seconds:g}")
        return direct[0], caveats
    nearest = min(
        (entry for entry in manifest.time_index if entry.time_seconds is not None),
        key=lambda entry: abs((entry.time_seconds or 0.0) - time_seconds),
        default=None,
    )
    if nearest is None:
        return None, ["time_index_has_no_numeric_times"]
    if abs((nearest.time_seconds or 0.0) - time_seconds) <= 1e-6:
        return nearest, []
    return None, [f"time_not_found_in_output_manifest:{time_seconds:g}"]


def _latest_manifest_time(manifest: OutputProductManifest) -> float | None:
    if not manifest.time_index:
        return None
    return manifest.time_index[-1].time_seconds


def _record_value(record: InterestingTimeRecord | None) -> float | None:
    if record is None or record.support_state != "supported":
        return None
    return float(record.value) if isinstance(record.value, (int, float)) else None


def _record_time(record: InterestingTimeRecord | None) -> float | None:
    if record is None or record.support_state != "supported":
        return None
    return record.time_seconds


def _first_deep_convection_time(diagnostics: ResultDiagnostics) -> float | None:
    for point in diagnostics.cloud.cloud_top_time_series:
        if point.value is not None and point.value >= DEEP_CLOUD_TOP_THRESHOLD_M:
            return point.time_seconds
    return None


def _deep_cloud_formed(diagnostics: ResultDiagnostics) -> bool | None:
    if not diagnostics.cloud.available:
        return None
    return any(
        point.value is not None and point.value >= DEEP_CLOUD_TOP_THRESHOLD_M
        for point in diagnostics.cloud.cloud_top_time_series
    )


def _strong_updraft_formed(diagnostics: ResultDiagnostics) -> bool | None:
    if not diagnostics.vertical_velocity.available:
        return None
    return (
        diagnostics.vertical_velocity.max_w_m_s is not None
        and diagnostics.vertical_velocity.max_w_m_s >= STRONG_UPDRAFT_THRESHOLD_M_S
    )


def _cm1_outcome(diagnostics: ResultDiagnostics) -> str:
    deep_cloud = _deep_cloud_formed(diagnostics)
    strong_updraft = _strong_updraft_formed(diagnostics)
    if deep_cloud is None or strong_updraft is None:
        return (
            "Unable to evaluate deep convection because required cloud or updraft fields "
            "are missing."
        )
    if deep_cloud and strong_updraft:
        rain_water_aloft = diagnostics.rain.available and diagnostics.rain.present
        surface_rain = diagnostics.surface_rain.available and diagnostics.surface_rain.present
        if rain_water_aloft and surface_rain:
            return (
                "Deep convection formed with strong updraft, rain water aloft, "
                "and surface rain reached the ground."
            )
        if rain_water_aloft:
            return "Deep convection formed with strong updraft and rain water aloft."
        if surface_rain:
            return (
                "Deep convection formed with strong updraft and surface rain reached the ground; "
                "rain-water-aloft evidence is absent or unavailable."
            )
        return (
            "Deep convection formed with strong updraft; "
            "rain-water-aloft evidence is absent or unavailable."
        )
    if deep_cloud:
        return "Deep cloud formed, but the updraft-strength threshold was not met."
    if strong_updraft:
        return "Strong updraft formed, but deep cloud did not reach the threshold."
    return "Trigger failed to produce deep convection by current cloud-top and updraft thresholds."


def _diagnostic_availability(
    variables: set[str], diagnostics: ResultDiagnostics | None = None
) -> list[ScienceDiagnosticAvailability]:
    reflectivity_supported = bool(diagnostics and diagnostics.reflectivity.available)
    surface_rain_supported = bool(diagnostics and diagnostics.surface_rain.available)
    return [
        _availability_record(
            key="max_dbz_or_reflectivity_proxy",
            label="Max reflectivity",
            source_field="dbz",
            field_present="dbz" in variables,
            implemented=reflectivity_supported,
        ),
        _availability_record(
            key="max_rain_or_surface_precip",
            label="Max surface rain",
            source_field="rain",
            field_present="rain" in variables,
            implemented=surface_rain_supported,
        ),
        _availability_record(
            key="updraft_depth_proxy",
            label="Updraft depth proxy",
            source_field="w",
            field_present="w" in variables,
            implemented=False,
        ),
        _availability_record(
            key="cold_pool_proxy",
            label="Cold-pool proxy",
            source_field="th",
            field_present=bool({"th", "theta", "theta_v"} & variables),
            implemented=False,
        ),
        _availability_record(
            key="near_surface_theta_perturbation_proxy",
            label="Near-surface theta perturbation",
            source_field="th",
            field_present=bool({"th", "theta", "theta_v"} & variables),
            implemented=False,
        ),
    ]


def _availability_record(
    *,
    key: str,
    label: str,
    source_field: str,
    field_present: bool,
    implemented: bool,
) -> ScienceDiagnosticAvailability:
    if implemented:
        return ScienceDiagnosticAvailability(
            key=key,
            label=label,
            source_field=source_field,
            support_state="supported",
        )
    caveat = (
        f"{key}_diagnostic_not_implemented" if field_present else f"missing_{source_field}_field"
    )
    return ScienceDiagnosticAvailability(
        key=key,
        label=label,
        source_field=source_field,
        support_state="unsupported_missing_diagnostic"
        if field_present
        else "unsupported_missing_fields",
        caveats=[caveat],
    )


def _positive(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and value > 0.0


def _format_time_label(time_seconds: float | None) -> str | None:
    if time_seconds is None:
        return None
    return f"{time_seconds:g} s"


def _time_entries_for_file(path: Path, file_order: int) -> list[OutputTimeIndexEntry]:
    xarray = importlib.import_module("xarray")
    try:
        dataset = xarray.open_dataset(path)
    except Exception as exc:
        raise OutputProductManifestError(f"could_not_open_netcdf:{exc}") from exc
    try:
        return _time_entries_from_dataset(dataset, path, file_order)
    finally:
        close = getattr(dataset, "close", None)
        if callable(close):
            close()


def _time_entries_from_dataset(
    dataset: Any, path: Path, file_order: int
) -> list[OutputTimeIndexEntry]:
    time_coordinate = _first_present(
        TIME_COORDINATE_CANDIDATES, [str(name) for name in dataset.coords]
    )
    if time_coordinate is not None:
        values = _coordinate_values(dataset, time_coordinate)
        return [
            OutputTimeIndexEntry(
                time_index=-1,
                time_seconds=_float_or_none(value),
                source_time_value=_source_time_value(value),
                source_file=str(path),
                source_file_kind="model_output_netcdf",
                local_time_index=local_index,
                time_source="netcdf_time_coordinate",
                time_caveats=_direct_time_caveats(value),
            )
            for local_index, value in enumerate(values)
        ]

    time_dimension = _first_present(
        TIME_COORDINATE_CANDIDATES, [str(name) for name in dataset.sizes]
    )
    time_size = int(dataset.sizes[time_dimension]) if time_dimension is not None else 1
    return [
        OutputTimeIndexEntry(
            time_index=-1,
            time_seconds=float(file_order + local_index),
            source_time_value=float(file_order + local_index),
            source_file=str(path),
            source_file_kind="model_output_netcdf",
            local_time_index=local_index,
            time_source="inferred_filename_order",
            time_caveats=[
                "time_coordinate_missing",
                "time_inferred_from_filename_order",
            ],
        )
        for local_index in range(time_size)
    ]


def _coordinate_values(dataset: Any, coordinate: str) -> list[Any]:
    values = dataset.coords[coordinate].values
    reshaped = values.reshape(-1)
    return list(reshaped.tolist())


def _direct_time_caveats(value: Any) -> list[str]:
    if _float_or_none(value) is None:
        return ["time_coordinate_not_numeric_seconds"]
    return []


def _time_order_caveats(
    original_numeric_times: list[float | None],
    entries: list[OutputTimeIndexEntry],
) -> list[str]:
    caveats: list[str] = []
    direct_numeric = [time for time in original_numeric_times if time is not None]
    if len(direct_numeric) >= 2 and any(
        later < earlier for earlier, later in zip(direct_numeric, direct_numeric[1:], strict=False)
    ):
        caveats.append("non_monotonic_time_coordinates_detected")
    seen: set[float] = set()
    duplicates: set[float] = set()
    for entry in entries:
        if entry.time_seconds is None:
            continue
        if entry.time_seconds in seen:
            duplicates.add(entry.time_seconds)
        seen.add(entry.time_seconds)
    for value in sorted(duplicates):
        caveats.append(f"duplicate_time_coordinate_detected:{value:g}")
    if any(entry.time_source == "inferred_filename_order" for entry in entries):
        caveats.append("inferred_time_indices_present")
    return caveats


def _flag_duplicate_entry_times(
    entries: list[OutputTimeIndexEntry],
) -> list[OutputTimeIndexEntry]:
    counts: dict[float, int] = {}
    for entry in entries:
        if entry.time_seconds is None:
            continue
        counts[entry.time_seconds] = counts.get(entry.time_seconds, 0) + 1
    flagged: list[OutputTimeIndexEntry] = []
    for entry in entries:
        if entry.time_seconds is None or counts.get(entry.time_seconds, 0) <= 1:
            flagged.append(entry)
            continue
        flagged.append(
            entry.model_copy(
                update={"time_caveats": _dedupe([*entry.time_caveats, "duplicate_time_coordinate"])}
            )
        )
    return flagged


def _first_present(candidates: tuple[str, ...], names: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _source_time_value(value: Any) -> float | str | None:
    numeric = _float_or_none(value)
    if numeric is not None:
        return numeric
    if value is None:
        return None
    return str(value)


def _cache_key(*path_groups: list[Path]) -> str:
    parts: list[str] = []
    for paths in path_groups:
        for path in sorted(paths, key=_output_sort_key):
            try:
                stat = path.stat()
            except OSError:
                parts.append(f"{path}:missing")
                continue
            parts.append(f"{path}:{stat.st_size}:{stat.st_mtime_ns}")
    return "|".join(parts)


def _output_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"cm1out_(\d+)", path.name)
    if match:
        return int(match.group(1)), path.name
    return 10**9, path.name


def _common_parent(paths: list[Path]) -> Path:
    if not paths:
        return Path(".")
    return paths[0].parent


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped

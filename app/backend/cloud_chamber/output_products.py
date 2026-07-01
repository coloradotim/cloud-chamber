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

OUTPUT_PRODUCT_MANIFEST_VERSION = 1
DERIVED_PRODUCTS_DIRNAME = "derived-products"
OUTPUT_PRODUCT_MANIFEST_FILENAME = "output_product_manifest.json"

MODEL_OUTPUT_PATTERN = re.compile(r"^cm1out_\d+\.nc(?:4)?$")
STATS_OUTPUT_NAMES = {"cm1out_stats.nc", "cm1out_stats.nc4"}
TIME_COORDINATE_CANDIDATES = ("time", "mtime", "t")

SourceFileKind = Literal["model_output_netcdf", "stats_netcdf", "raw_cm1_artifact"]
TimeSource = Literal["netcdf_time_coordinate", "inferred_filename_order"]


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

"""Terrain-aware browser payload for the preserved Gate B mountain-wave run."""

from __future__ import annotations

import math
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.mountain_wave_case import (
    EXPECTED_OUTPUT_TIMES_SECONDS,
    PRESERVED_GATE_B_EVALUATION_INPUT_SHA256,
    PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
    PRESERVED_GATE_B_RUN_ID,
    MountainWaveCaseError,
    accepted_model_output_paths,
    load_completed_mountain_wave_package_for_evaluation,
    normalize_length_to_m,
    normalize_time_to_seconds,
    parse_namelist_assignments,
    reconstruct_physical_heights,
    resolve_active_top_evidence,
    verify_evaluation_input_identity,
)
from cloud_chamber.settings import CloudChamberSettings

MountainWaveTerrainField = Literal["w", "theta_perturbation"]


class MountainWaveTerrainVisualizationError(RuntimeError):
    """Raised when the bounded terrain-aware payload cannot be represented honestly."""


class TerrainFieldMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: MountainWaveTerrainField
    display_name: str
    units: str
    native_dimensions: list[str]
    vertical_grid: Literal["physical_full_levels", "physical_scalar_levels"]
    derivation: str


class TerrainGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_center_m: list[float]
    x_edge_m: list[float]
    terrain_m: list[float]
    scalar_height_m: list[list[float]]
    full_height_m: list[list[float]]
    nominal_scalar_height_m: list[float]
    nominal_full_height_m: list[float]
    active_top_m: float
    singleton_y_m: float
    horizontal_units: str = "m"
    vertical_units: str = "m"


class TerrainActiveTopEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transform_top_source: str
    final_nominal_zf_m: float
    runtime_ztop_m: float
    configured_nz: int
    configured_dz_m: float
    nz_times_dz_m: float
    all_sources_agree: bool
    inactive_namelist_ztop_m: float


class TerrainVerticalReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    physical_model_height: str = "terrain-following geometric height above model datum"
    local_agl: str = "physical model height minus native terrain height at the same x cell"
    nominal_coordinate: str = "terrain coordinate used by CM1; not physical altitude over terrain"
    model_height_is_msl: bool = False


class TerrainScale(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixed_across_all_times: bool = True
    minimum: float
    maximum: float
    selected_time_minimum: float
    selected_time_maximum: float
    palette: str = "blue_white_red_diverging"


class TerrainProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_history_file: str
    reference_history_file: str | None = None
    source_kind: str = "native_cm1_numbered_history"
    topology: str = "native_2d_x_z_singleton_y"
    horizontal_collocation: str = "none"
    interpolation: str = "none"
    display_binning: str
    physical_height_source: str
    full_height_source: str
    masked_below_terrain: bool = True


class TerrainIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    implementation_commit: str
    verification_mode: str
    verified_file_count: int
    verified_before_and_after_extraction: bool


class TerrainPerformance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_ms: float
    serialization_ms: float = 0.0
    serialized_payload_bytes: int = 0


class MountainWaveTerrainFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "mountain_wave_terrain_research_v1"
    run_id: str
    case_label: str = "CM1 r21.1 dry mountain-wave benchmark"
    time_index: int
    time_seconds: int
    times_seconds: list[int]
    dimensionality: str = "2-D x-z cross-section"
    singleton_y: bool = True
    dry_case: bool = True
    field: TerrainFieldMetadata
    values: list[list[float]]
    geometry: TerrainGeometry
    active_top_evidence: TerrainActiveTopEvidence
    vertical_references: TerrainVerticalReferences = Field(
        default_factory=TerrainVerticalReferences
    )
    scale: TerrainScale
    provenance: TerrainProvenance
    identity: TerrainIdentity
    performance: TerrainPerformance
    caveats: list[str] = Field(
        default_factory=lambda: [
            "This dry two-dimensional benchmark does not simulate moisture or cloud formation.",
            (
                "The singleton y dimension is native CM1 output, not an extruded "
                "three-dimensional field."
            ),
        ]
    )


def terrain_frame_from_native_outputs(
    *,
    output_paths: list[Path],
    namelist_path: Path,
    field: MountainWaveTerrainField,
    time_index: int,
    run_id: str = PRESERVED_GATE_B_RUN_ID,
    implementation_commit: str = PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
    expected_times_seconds: tuple[int, ...] = EXPECTED_OUTPUT_TIMES_SECONDS,
    identity_verified: bool = False,
    verified_file_count: int = 0,
) -> MountainWaveTerrainFrame:
    """Extract one native-topology frame while validating every history's geometry."""
    started = perf_counter()
    paths = accepted_model_output_paths(output_paths)
    if len(paths) != len(expected_times_seconds):
        raise MountainWaveTerrainVisualizationError(
            f"Expected {len(expected_times_seconds)} numbered histories; found {len(paths)}."
        )
    if not 0 <= time_index < len(paths):
        raise MountainWaveTerrainVisualizationError(
            f"Time index {time_index} is outside 0..{len(paths) - 1}."
        )

    assignments = parse_namelist_assignments(namelist_path.read_text())
    configured_nz = _namelist_int(assignments, "nz")
    configured_dz_m = _namelist_float(assignments, "dz")
    if _namelist_int(assignments, "ny") != 1:
        raise MountainWaveTerrainVisualizationError(
            "The bounded terrain viewer requires the native singleton y dimension."
        )
    if _namelist_int(assignments, "stretch_z") != 0:
        raise MountainWaveTerrainVisualizationError(
            "This bounded validator supports only the preserved unstretched vertical setup."
        )

    times: list[int] = []
    frames: list[np.ndarray[Any, np.dtype[np.float64]]] = []
    reference_theta: np.ndarray[Any, np.dtype[np.float64]] | None = None
    expected_geometry: tuple[np.ndarray[Any, np.dtype[np.float64]], ...] | None = None
    selected_geometry: tuple[np.ndarray[Any, np.dtype[np.float64]], ...] | None = None
    selected_y_m = 0.0
    selected_active_top = None

    for path_index, path in enumerate(paths):
        try:
            with xr.open_dataset(path, decode_times=False) as dataset:
                _require_native_semantics(dataset)
                time_seconds = _single_time_seconds(dataset)
                rounded_time = int(round(time_seconds))
                if not math.isclose(time_seconds, rounded_time, rel_tol=0.0, abs_tol=0.01):
                    raise MountainWaveTerrainVisualizationError(
                        "Native history time is not an integral second."
                    )
                times.append(rounded_time)

                x_center_m = _length_coordinate(dataset, "xh")
                x_edge_m = _length_coordinate(dataset, "xf")
                y_center_m = _length_coordinate(dataset, "yh")
                nominal_scalar_m = _length_coordinate(dataset, "zh")
                nominal_full_m = _length_coordinate(dataset, "zf")
                if y_center_m.size != 1 or int(dataset.sizes.get("yh", 0)) != 1:
                    raise MountainWaveTerrainVisualizationError(
                        "Native output is not a singleton-y two-dimensional cross-section."
                    )
                if x_edge_m.size != x_center_m.size + 1:
                    raise MountainWaveTerrainVisualizationError(
                        "Native x edges do not bound the scalar x centers."
                    )
                terrain_m = _field_2d(dataset, "zs", ("yh", "xh"))[0]
                scalar_height_m = _field_3d(dataset, "zhval", ("zh", "yh", "xh"))[:, 0, :]
                active_top = resolve_active_top_evidence(
                    nominal_full_m,
                    "m",
                    dataset["ztop"].values,
                    str(dataset["ztop"].attrs.get("units", "")),
                    configured_nz=configured_nz,
                    configured_dz_m=configured_dz_m,
                )
                full_height_m = reconstruct_physical_heights(
                    terrain_m[None, :],
                    nominal_full_m,
                    active_top_m=active_top.final_nominal_zf_m,
                )[:, 0, :]
                reconstructed_scalar_m = reconstruct_physical_heights(
                    terrain_m[None, :],
                    nominal_scalar_m,
                    active_top_m=active_top.final_nominal_zf_m,
                )[:, 0, :]
                if scalar_height_m.shape != reconstructed_scalar_m.shape or not np.allclose(
                    scalar_height_m, reconstructed_scalar_m, rtol=0.0, atol=0.02
                ):
                    raise MountainWaveTerrainVisualizationError(
                        "Native physical scalar heights disagree with CM1 "
                        "terrain-following semantics."
                    )
                _require_geometry_invariants(
                    terrain_m=terrain_m,
                    scalar_height_m=scalar_height_m,
                    full_height_m=full_height_m,
                    active_top_m=active_top.final_nominal_zf_m,
                )

                geometry = (
                    x_center_m,
                    x_edge_m,
                    terrain_m,
                    scalar_height_m,
                    full_height_m,
                    nominal_scalar_m,
                    nominal_full_m,
                )
                if expected_geometry is None:
                    expected_geometry = tuple(item.copy() for item in geometry)
                else:
                    _require_same_geometry(expected_geometry, geometry)

                if field == "w":
                    _require_units(dataset, "w", {"m/s", "m s-1", "m s^-1"})
                    values = _field_3d(dataset, "w", ("zf", "yh", "xh"))[:, 0, :]
                else:
                    _require_units(dataset, "th", {"k", "kelvin"})
                    theta = _field_3d(dataset, "th", ("zh", "yh", "xh"))[:, 0, :]
                    if reference_theta is None:
                        reference_theta = theta.copy()
                    values = theta - reference_theta
                if not np.isfinite(values).all():
                    raise MountainWaveTerrainVisualizationError(
                        f"Field {field} contains non-finite values."
                    )
                frames.append(values)
                if path_index == time_index:
                    selected_geometry = geometry
                    selected_y_m = float(y_center_m[0])
                    selected_active_top = active_top
        except MountainWaveTerrainVisualizationError:
            raise
        except MountainWaveCaseError as exc:
            raise MountainWaveTerrainVisualizationError(str(exc)) from exc
        except (OSError, ValueError, KeyError) as exc:
            raise MountainWaveTerrainVisualizationError(
                f"Native history {path.name} could not be decoded with required terrain semantics."
            ) from exc

    if times != list(expected_times_seconds):
        raise MountainWaveTerrainVisualizationError(
            f"Native history times differ from the required exact sequence: {times}."
        )
    if selected_geometry is None or selected_active_top is None:
        raise MountainWaveTerrainVisualizationError("Selected terrain geometry was not extracted.")

    global_max_abs = max(float(np.max(np.abs(values))) for values in frames)
    if global_max_abs == 0.0:
        global_max_abs = 1.0
    selected = frames[time_index]
    (
        x_center_m,
        x_edge_m,
        terrain_m,
        scalar_height_m,
        full_height_m,
        nominal_scalar_m,
        nominal_full_m,
    ) = selected_geometry
    metadata = _field_metadata(field)
    response = MountainWaveTerrainFrame(
        run_id=run_id,
        time_index=time_index,
        time_seconds=times[time_index],
        times_seconds=times,
        field=metadata,
        values=selected.tolist(),
        geometry=TerrainGeometry(
            x_center_m=x_center_m.tolist(),
            x_edge_m=x_edge_m.tolist(),
            terrain_m=terrain_m.tolist(),
            scalar_height_m=scalar_height_m.tolist(),
            full_height_m=full_height_m.tolist(),
            nominal_scalar_height_m=nominal_scalar_m.tolist(),
            nominal_full_height_m=nominal_full_m.tolist(),
            active_top_m=float(full_height_m[-1, 0]),
            singleton_y_m=selected_y_m,
        ),
        active_top_evidence=TerrainActiveTopEvidence(
            transform_top_source=selected_active_top.transform_top_source,
            final_nominal_zf_m=selected_active_top.final_nominal_zf_m,
            runtime_ztop_m=selected_active_top.runtime_ztop_m,
            configured_nz=selected_active_top.configured_nz,
            configured_dz_m=selected_active_top.configured_dz_m,
            nz_times_dz_m=selected_active_top.nz_times_dz_m,
            all_sources_agree=selected_active_top.all_active_top_sources_agree,
            inactive_namelist_ztop_m=selected_active_top.inactive_namelist_ztop_m,
        ),
        scale=TerrainScale(
            minimum=-global_max_abs,
            maximum=global_max_abs,
            selected_time_minimum=float(np.min(selected)),
            selected_time_maximum=float(np.max(selected)),
        ),
        provenance=TerrainProvenance(
            source_history_file=paths[time_index].name,
            reference_history_file=paths[0].name if field == "theta_perturbation" else None,
            display_binning=(
                "Native full-level samples painted between physical vertical midpoints and "
                "adjacent center-height midpoints at interior x edges, clamped to terrain and "
                "active top; native field values are not interpolated."
                if field == "w"
                else (
                    "Native scalar samples painted between physical full-level bounds and "
                    "adjacent center-height midpoints at interior x edges; native field values "
                    "are not interpolated."
                )
            ),
            physical_height_source=(
                "native zhval verified against CM1 terrain-following reconstruction"
            ),
            full_height_source=(
                "reconstructed from native zs, nominal zf, and independently agreed active top"
            ),
        ),
        identity=TerrainIdentity(
            implementation_commit=implementation_commit,
            verification_mode="pinned_sha256_before_and_after_extraction",
            verified_file_count=verified_file_count,
            verified_before_and_after_extraction=identity_verified,
        ),
        performance=TerrainPerformance(extraction_ms=(perf_counter() - started) * 1_000.0),
    )
    return _measure_serialization(response)


def preserved_mountain_wave_terrain_frame(
    settings: CloudChamberSettings,
    *,
    field: MountainWaveTerrainField,
    time_index: int,
) -> MountainWaveTerrainFrame:
    """Return one frame only after before-and-after verification of the preserved run."""
    try:
        package = load_completed_mountain_wave_package_for_evaluation(
            settings=settings,
            run_id=PRESERVED_GATE_B_RUN_ID,
            expected_implementation_commit=PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
        )
        before = verify_evaluation_input_identity(
            package,
            expected_run_id=PRESERVED_GATE_B_RUN_ID,
            expected_implementation_commit=PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
            expected_file_sha256=PRESERVED_GATE_B_EVALUATION_INPUT_SHA256,
        )
        response = terrain_frame_from_native_outputs(
            output_paths=list(package.package_dir.glob("cm1out_*.nc*")),
            namelist_path=package.package_dir / "namelist.input",
            field=field,
            time_index=time_index,
            identity_verified=True,
            verified_file_count=len(before["file_sha256"]),
        )
        after = verify_evaluation_input_identity(
            package,
            expected_run_id=PRESERVED_GATE_B_RUN_ID,
            expected_implementation_commit=PRESERVED_GATE_B_IMPLEMENTATION_COMMIT,
            expected_file_sha256=PRESERVED_GATE_B_EVALUATION_INPUT_SHA256,
        )
        if before["file_sha256"] != after["file_sha256"]:
            raise MountainWaveTerrainVisualizationError(
                "Preserved evaluation inputs changed during terrain extraction."
            )
        return response
    except MountainWaveTerrainVisualizationError:
        raise
    except MountainWaveCaseError as exc:
        raise MountainWaveTerrainVisualizationError(str(exc)) from exc
    except OSError as exc:
        raise MountainWaveTerrainVisualizationError(
            "The preserved mountain-wave result is not available for local terrain validation."
        ) from exc


def local_agl_m(*, model_height_m: float, terrain_height_m: float) -> float:
    agl = model_height_m - terrain_height_m
    if agl < -0.01:
        raise MountainWaveTerrainVisualizationError(
            "A point below local terrain has no visible AGL."
        )
    return max(0.0, agl)


def _field_metadata(field: MountainWaveTerrainField) -> TerrainFieldMetadata:
    if field == "w":
        return TerrainFieldMetadata(
            key=field,
            display_name="Vertical velocity",
            units="m/s",
            native_dimensions=["zf", "yh", "xh"],
            vertical_grid="physical_full_levels",
            derivation="native CM1 w; no interpolation or collocation",
        )
    return TerrainFieldMetadata(
        key=field,
        display_name="Potential-temperature perturbation",
        units="K",
        native_dimensions=["zh", "yh", "xh"],
        vertical_grid="physical_scalar_levels",
        derivation="native CM1 th minus the same native scalar cell at t=0 s",
    )


def _measure_serialization(response: MountainWaveTerrainFrame) -> MountainWaveTerrainFrame:
    started = perf_counter()
    response.model_dump_json()
    elapsed_ms = (perf_counter() - started) * 1_000.0
    measured = response.model_copy(
        update={
            "performance": response.performance.model_copy(
                update={
                    "serialization_ms": elapsed_ms,
                    "serialized_payload_bytes": 0,
                }
            )
        }
    )
    for _attempt in range(4):
        payload_bytes = len(measured.model_dump_json().encode("utf-8"))
        if payload_bytes == measured.performance.serialized_payload_bytes:
            break
        measured = measured.model_copy(
            update={
                "performance": measured.performance.model_copy(
                    update={"serialized_payload_bytes": payload_bytes}
                )
            }
        )
    return measured


def _namelist_float(assignments: dict[str, str], name: str) -> float:
    try:
        return float(assignments[name].lower().replace("d", "e"))
    except (KeyError, ValueError) as exc:
        raise MountainWaveTerrainVisualizationError(
            f"Namelist lacks a numeric {name} assignment."
        ) from exc


def _namelist_int(assignments: dict[str, str], name: str) -> int:
    value = _namelist_float(assignments, name)
    if not value.is_integer():
        raise MountainWaveTerrainVisualizationError(f"Namelist {name} must be integral.")
    return int(value)


def _single_time_seconds(dataset: xr.Dataset) -> float:
    if "time" not in dataset:
        raise MountainWaveTerrainVisualizationError("Native output lacks the time coordinate.")
    values = normalize_time_to_seconds(
        dataset["time"].values,
        str(dataset["time"].attrs.get("units", "")),
    ).reshape(-1)
    if values.size != 1:
        raise MountainWaveTerrainVisualizationError(
            "Each numbered native history must contain exactly one time."
        )
    return float(values[0])


def _length_coordinate(dataset: xr.Dataset, name: str) -> np.ndarray[Any, np.dtype[np.float64]]:
    if name not in dataset:
        raise MountainWaveTerrainVisualizationError(f"Native output lacks coordinate {name}.")
    values = normalize_length_to_m(
        dataset[name].values,
        str(dataset[name].attrs.get("units", "")),
    )
    if values.ndim != 1 or values.size < 1 or not np.isfinite(values).all():
        raise MountainWaveTerrainVisualizationError(f"Coordinate {name} is not finite and 1-D.")
    if values.size > 1 and not np.all(np.diff(values) > 0.0):
        raise MountainWaveTerrainVisualizationError(
            f"Coordinate {name} is not strictly increasing."
        )
    return values


def _field_2d(
    dataset: xr.Dataset, name: str, dimensions: tuple[str, str]
) -> np.ndarray[Any, np.dtype[np.float64]]:
    return _field_array(dataset, name, dimensions)


def _field_3d(
    dataset: xr.Dataset, name: str, dimensions: tuple[str, str, str]
) -> np.ndarray[Any, np.dtype[np.float64]]:
    return _field_array(dataset, name, dimensions)


def _field_array(
    dataset: xr.Dataset, name: str, dimensions: tuple[str, ...]
) -> np.ndarray[Any, np.dtype[np.float64]]:
    if name not in dataset:
        raise MountainWaveTerrainVisualizationError(f"Native output lacks required field {name}.")
    item = dataset[name]
    if "time" in item.dims:
        if item.sizes["time"] != 1:
            raise MountainWaveTerrainVisualizationError(
                f"Field {name} has more than one time in a numbered history."
            )
        item = item.isel(time=0)
    for dimension in list(item.dims):
        if dimension not in dimensions:
            if item.sizes[dimension] != 1:
                raise MountainWaveTerrainVisualizationError(
                    f"Field {name} has unsupported dimension {dimension}."
                )
            item = item.isel({dimension: 0})
    if set(item.dims) != set(dimensions):
        raise MountainWaveTerrainVisualizationError(
            f"Field {name} dimensions are {item.dims}; expected {dimensions}."
        )
    values = np.asarray(item.transpose(*dimensions).values, dtype=np.float64)
    if not np.isfinite(values).all():
        raise MountainWaveTerrainVisualizationError(f"Field {name} contains non-finite values.")
    return values


def _require_native_semantics(dataset: xr.Dataset) -> None:
    for name in ("time", "xh", "xf", "yh", "zh", "zf", "zs", "zhval", "th", "w", "ztop"):
        if name not in dataset:
            raise MountainWaveTerrainVisualizationError(
                f"Native output lacks required terrain semantic {name}."
            )
    _require_units(dataset, "zs", {"m", "meter", "meters"})
    _require_units(dataset, "zhval", {"m", "meter", "meters"})


def _require_units(dataset: xr.Dataset, name: str, accepted: set[str]) -> None:
    actual = str(dataset[name].attrs.get("units", "")).strip().lower()
    normalized = actual.replace(" ", "")
    if normalized not in {unit.replace(" ", "") for unit in accepted}:
        raise MountainWaveTerrainVisualizationError(
            f"Required field {name} has unsupported units {actual!r}."
        )


def _require_geometry_invariants(
    *,
    terrain_m: np.ndarray[Any, np.dtype[np.float64]],
    scalar_height_m: np.ndarray[Any, np.dtype[np.float64]],
    full_height_m: np.ndarray[Any, np.dtype[np.float64]],
    active_top_m: float,
) -> None:
    if float(np.ptp(terrain_m)) <= 0.0:
        raise MountainWaveTerrainVisualizationError(
            "The preserved terrain-aware validation requires curved, non-flat terrain."
        )
    if scalar_height_m.shape[1] != terrain_m.size or full_height_m.shape[1] != terrain_m.size:
        raise MountainWaveTerrainVisualizationError("Physical height meshes do not match x cells.")
    if not np.all(np.diff(scalar_height_m, axis=0) > 0.0) or not np.all(
        np.diff(full_height_m, axis=0) > 0.0
    ):
        raise MountainWaveTerrainVisualizationError("Physical model columns are not monotonic.")
    if np.any(scalar_height_m < terrain_m[None, :] - 0.01) or np.any(
        full_height_m < terrain_m[None, :] - 0.01
    ):
        raise MountainWaveTerrainVisualizationError("Physical grid contains heights below terrain.")
    if not np.allclose(full_height_m[0], terrain_m, rtol=0.0, atol=0.01):
        raise MountainWaveTerrainVisualizationError(
            "Full-level bottom does not equal local terrain."
        )
    if not np.allclose(full_height_m[-1], active_top_m, rtol=0.0, atol=0.01):
        raise MountainWaveTerrainVisualizationError("Full-level top is not constant at active top.")


def _require_same_geometry(
    expected: tuple[np.ndarray[Any, np.dtype[np.float64]], ...],
    actual: tuple[np.ndarray[Any, np.dtype[np.float64]], ...],
) -> None:
    for expected_values, actual_values in zip(expected, actual, strict=True):
        if expected_values.shape != actual_values.shape or not np.allclose(
            expected_values, actual_values, rtol=0.0, atol=0.01
        ):
            raise MountainWaveTerrainVisualizationError(
                "Terrain-aware coordinates change between native histories."
            )

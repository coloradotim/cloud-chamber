"""Bounded Gate C examination payloads for the retained supercell benchmark."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import numpy as np
import xarray as xr
from pydantic import BaseModel, Field

from cloud_chamber.settings import CloudChamberSettings

PRESERVED_RUN_ID = "quarter-circle-supercell-official-20260722T142521Z"
PRESERVED_CASE_ID = "cm1_r21_1_quarter_circle_supercell_official_v0"
EXPECTED_TIMES_SECONDS = tuple(range(0, 7_201, 900))
HISTORY_FILENAMES = tuple(f"cm1out_{index:06d}.nc" for index in range(1, 10))
PRESENTATION_RUN_ID = "quarter-circle-supercell-presentation-v1-20260723"
PRESENTATION_CASE_ID = "cm1_r21_1_quarter_circle_supercell_presentation_v1"
PRESENTATION_TIMES_SECONDS = tuple(range(0, 10_801, 120))
PRESENTATION_HISTORY_FILENAMES = tuple(f"cm1out_{index:06d}.nc" for index in range(1, 92))
PRESENTATION_EVIDENCE_FILENAME = "supercell_presentation_evidence.json"
PRESENTATION_DEFAULT_TIME_SECONDS = 4_440
DEFAULT_PRESENTATION_TIME_INDEX = PRESENTATION_TIMES_SECONDS.index(
    PRESENTATION_DEFAULT_TIME_SECONDS
)
HYDROMETEORS = ("qc", "qr", "qi", "qs", "qg")
PRESENTATION_REQUIRED_FIELDS = {
    "th",
    "prs",
    "qv",
    "qc",
    "qr",
    "qi",
    "qs",
    "qg",
    "nci",
    "ncs",
    "ncr",
    "ncg",
    "dbz",
    "uinterp",
    "vinterp",
    "winterp",
    "xvort",
    "yvort",
    "zvort",
    "rain",
    "prate",
    "uh",
    "cref",
}
LensId = Literal["rotating_updraft", "cloud_precipitation", "low_level_interactions"]
ViewportId = Literal["storm", "full"]
FramePurpose = Literal["research", "product"]
STORM_VIEW_BOUNDS_KM = {
    "x_min": -40.0,
    "x_max": 40.0,
    "y_min": -45.0,
    "y_max": 35.0,
}
GATE_C_STORM_VIEW_BOUNDS_KM = {
    "x_min": -35.5,
    "x_max": 24.5,
    "y_min": -33.5,
    "y_max": 26.5,
}


@dataclass(frozen=True)
class _RunContract:
    run_id: str
    case_id: str
    expected_times_seconds: tuple[int, ...]
    history_filenames: tuple[str, ...]
    evidence_filename: str | None
    unavailable_label: str


GATE_C_RUN = _RunContract(
    run_id=PRESERVED_RUN_ID,
    case_id=PRESERVED_CASE_ID,
    expected_times_seconds=EXPECTED_TIMES_SECONDS,
    history_filenames=HISTORY_FILENAMES,
    evidence_filename=None,
    unavailable_label="accepted Gate B retained output",
)
PRESENTATION_RUN = _RunContract(
    run_id=PRESENTATION_RUN_ID,
    case_id=PRESENTATION_CASE_ID,
    expected_times_seconds=PRESENTATION_TIMES_SECONDS,
    history_filenames=PRESENTATION_HISTORY_FILENAMES,
    evidence_filename=PRESENTATION_EVIDENCE_FILENAME,
    unavailable_label="accepted presentation output",
)

W_COLORS = (
    "#4b0082",
    "#0057d9",
    "#00c9d8",
    "#ffffff",
    "#00d63b",
    "#8fe000",
    "#ffe000",
    "#ff9800",
    "#ff3b00",
    "#c40000",
)


class StormExaminationError(RuntimeError):
    """Raised when the preserved Gate C evidence cannot be loaded honestly."""


class ScaleMetadata(BaseModel):
    scale_id: str
    display_name: str
    units: str
    scale_type: Literal["fixed_discrete", "fixed_continuous", "categorical"]
    minimum: float
    maximum: float
    breakpoints: list[float] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    fixed_across_time: bool = True


class FieldLayer(BaseModel):
    key: str
    display_name: str
    units: str
    evidence_kind: Literal["native", "derived"]
    source_fields: list[str]
    derivation: str | None = None
    values: list[list[float | None]]
    selected_frame_minimum: float
    selected_frame_maximum: float
    scale: ScaleMetadata


class CategoryDefinition(BaseModel):
    code: int
    key: str
    label: str
    color: str


class CategoryLayer(BaseModel):
    key: str
    display_name: str
    evidence_kind: Literal["derived"] = "derived"
    source_fields: list[str]
    derivation: str
    values: list[list[int]]
    magnitude: FieldLayer
    categories: list[CategoryDefinition]


class WindVector(BaseModel):
    x_km: float
    y_km: float
    u_m_s: float
    v_m_s: float
    magnitude_m_s: float


class PointMarker(BaseModel):
    x_index: int
    y_index: int
    z_index: int
    x_km: float
    y_km: float
    z_km: float
    w_m_s: float


class VolumeLayer(BaseModel):
    key: str
    display_name: str
    units: str
    evidence_kind: Literal["native", "derived"]
    source_fields: list[str]
    derivation: str | None = None
    rendering: Literal["neutral_cloud", "signed_scalar", "scalar", "categorical"]
    points: list[tuple[float, float, float, float, int]]
    source_count: int
    returned_count: int
    threshold_label: str
    default_visible: bool
    default_opacity: float
    default_point_size: float
    scale: ScaleMetadata | None = None
    categories: list[CategoryDefinition] = Field(default_factory=list)


class VolumeWindVector(BaseModel):
    x_km: float
    y_km: float
    z_km: float
    u_m_s: float
    v_m_s: float
    magnitude_m_s: float


class StormVolumeScene(BaseModel):
    coordinate_extents_km: dict[str, dict[str, float]]
    coordinate_sizes: dict[str, int]
    coordinate_indices: dict[str, list[int]]
    coordinate_values_km: dict[str, list[float]]
    layers: list[VolumeLayer]
    wind_vectors: list[VolumeWindVector] = Field(default_factory=list)
    wind_reference_m_s: float
    point_budget: int
    source_history_file: str


class PlanView(BaseModel):
    title: str
    subtitle: str
    x_indices: list[int]
    y_indices: list[int]
    x_km: list[float]
    y_km: list[float]
    level_index: int
    level_km: float
    selection_z_indices: list[list[int]] | None = None
    primary: FieldLayer
    overlays: dict[str, FieldLayer]
    categories: CategoryLayer | None = None
    wind_vectors: list[WindVector] = Field(default_factory=list)


class VerticalSection(BaseModel):
    orientation: Literal["xz", "yz"]
    title: str
    horizontal_dimension: Literal["x", "y"]
    horizontal_indices: list[int]
    horizontal_km: list[float]
    z_km: list[float]
    cross_section_coordinate_km: float
    primary: FieldLayer
    overlays: dict[str, FieldLayer]
    categories: CategoryLayer | None = None


class SelectedPointEvidence(BaseModel):
    x_index: int
    y_index: int
    z_index: int
    x_km: float
    y_km: float
    z_km: float
    model_time_seconds: float
    coordinate_frame: str
    values: dict[str, float]
    units: dict[str, str]
    evidence_kind: dict[str, Literal["native", "derived"]]
    states: list[str]
    distance_to_primary_updraft_km: float


class TimelineCheckpoint(BaseModel):
    time_seconds: int
    label: str
    phase: str
    phase_kind: Literal["visible_checkpoint", "bounded_inference"]


class StormExaminationFrame(BaseModel):
    schema_version: Literal["storm_examination_gate_c_v1", "supercells_explore_v1"] = (
        "storm_examination_gate_c_v1"
    )
    authority_state: Literal[
        "issue_418_gate_c_research_not_product", "supercells_product_world"
    ] = "issue_418_gate_c_research_not_product"
    world_id: Literal["supercells"] | None = None
    simulation_id: Literal["supercells_quarter_circle_reference"] | None = None
    run_id: str
    case_id: str
    simulation_label: str
    lens_id: LensId
    lens_name: str
    lens_question: str
    what_to_notice_now: str
    what_to_notice_by_view: dict[str, str] | None = None
    time_index: int
    time_seconds: float
    times_seconds: list[float]
    mature_checkpoint_indices: list[int]
    timeline_checkpoints: list[TimelineCheckpoint]
    viewport: ViewportId
    viewport_bounds_km: dict[str, float]
    primary_updraft: PointMarker
    selected_point: SelectedPointEvidence
    plan: PlanView
    xz_section: VerticalSection
    yz_section: VerticalSection
    scene: StormVolumeScene | None = None
    caveats: list[str]
    provenance: dict[str, str]
    extraction_milliseconds: float


def preserved_storm_examination_frame(
    settings: CloudChamberSettings,
    *,
    lens: LensId = "rotating_updraft",
    time_index: int = 5,
    viewport: ViewportId = "storm",
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
) -> StormExaminationFrame:
    """Return the accepted Gate C research surface through the shared extractor."""
    return _storm_frame(
        settings,
        lens=lens,
        time_index=time_index,
        viewport=viewport,
        x_index=x_index,
        y_index=y_index,
        z_index=z_index,
        purpose="research",
    )


def supercells_explore_frame(
    settings: CloudChamberSettings,
    *,
    lens: LensId = "rotating_updraft",
    time_index: int = DEFAULT_PRESENTATION_TIME_INDEX,
    viewport: ViewportId = "storm",
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
) -> StormExaminationFrame:
    """Return the production Supercells frame from the accepted Gate C science path."""
    return _storm_frame(
        settings,
        lens=lens,
        time_index=time_index,
        viewport=viewport,
        x_index=x_index,
        y_index=y_index,
        z_index=z_index,
        purpose="product",
    )


def storm_examination_inventory(
    settings: CloudChamberSettings,
) -> tuple[tuple[Path, float], ...]:
    """Return the cached, identity-validated production history inventory."""
    run_dir = settings.runtime_home.expanduser() / "runs" / PRESENTATION_RUN_ID
    return _validated_inventory(run_dir, PRESENTATION_RUN)


def _storm_frame(
    settings: CloudChamberSettings,
    *,
    lens: LensId,
    time_index: int,
    viewport: ViewportId,
    x_index: int | None,
    y_index: int | None,
    z_index: int | None,
    purpose: FramePurpose,
) -> StormExaminationFrame:
    """Extract coordinated, bounded views from one retained native history."""
    started = time.perf_counter()
    contract = PRESENTATION_RUN if purpose == "product" else GATE_C_RUN
    run_dir = settings.runtime_home.expanduser() / "runs" / contract.run_id
    inventory = _validated_inventory(run_dir, contract)
    checked_time_index = _checked_index(time_index, len(inventory), "time_index")
    history_path, time_seconds = inventory[checked_time_index]

    with xr.open_dataset(history_path, decode_times=False) as dataset:
        _validate_selected_history(dataset, time_seconds)
        x_km = _coordinate(dataset, "xh")
        y_km = _coordinate(dataset, "yh")
        z_km = _coordinate(dataset, "zh")
        fields = {
            name: _field(dataset, name)
            for name in (
                "winterp",
                "zvort",
                "uh",
                "dbz",
                "rain",
                "qc",
                "qr",
                "qi",
                "qs",
                "qg",
                "uinterp",
                "vinterp",
            )
        }

    bounds = _viewport_bounds(viewport, x_km, y_km, purpose)
    native_x_indices = _coordinate_indices(x_km, bounds["x_min"], bounds["x_max"])
    native_y_indices = _coordinate_indices(y_km, bounds["y_min"], bounds["y_max"])
    if purpose == "product" and viewport == "storm":
        focused_w = fields["winterp"][:, native_y_indices, :][:, :, native_x_indices]
        focused_primary = np.unravel_index(np.nanargmax(focused_w), focused_w.shape)
        primary_index = (
            int(focused_primary[0]),
            int(native_y_indices[focused_primary[1]]),
            int(native_x_indices[focused_primary[2]]),
        )
    else:
        full_primary = np.unravel_index(
            np.nanargmax(fields["winterp"]),
            fields["winterp"].shape,
        )
        primary_index = (
            int(full_primary[0]),
            int(full_primary[1]),
            int(full_primary[2]),
        )
    primary_z, primary_y, primary_x = primary_index
    default_level = _default_level_index(lens, z_km, primary_z)
    selected_x = _checked_index(x_index if x_index is not None else primary_x, len(x_km), "x_index")
    selected_y = _checked_index(y_index if y_index is not None else primary_y, len(y_km), "y_index")
    selected_z = _checked_index(
        z_index if z_index is not None else default_level, len(z_km), "z_index"
    )

    primary = PointMarker(
        x_index=primary_x,
        y_index=primary_y,
        z_index=primary_z,
        x_km=float(x_km[primary_x]),
        y_km=float(y_km[primary_y]),
        z_km=float(z_km[primary_z]),
        w_m_s=float(fields["winterp"][primary_index]),
    )
    x_indices = native_x_indices
    y_indices = native_y_indices
    if purpose == "product" and viewport == "full":
        x_indices = x_indices[::2]
        y_indices = y_indices[::2]
    plan = _plan_view(lens, fields, x_km, y_km, z_km, selected_z, x_indices, y_indices)
    xz_section = _vertical_section(
        lens,
        "xz",
        fields,
        x_km,
        y_km,
        z_km,
        selected_x,
        selected_y,
        x_indices,
        y_indices,
    )
    yz_section = _vertical_section(
        lens,
        "yz",
        fields,
        x_km,
        y_km,
        z_km,
        selected_x,
        selected_y,
        x_indices,
        y_indices,
    )
    selected = _selected_point(
        fields,
        x_km,
        y_km,
        z_km,
        selected_x,
        selected_y,
        selected_z,
        time_seconds,
        primary,
    )
    lens_name, lens_question = _lens_identity(lens)
    what_to_notice_by_view = _what_to_notice_by_view(
        lens, time_seconds, plan, xz_section, yz_section
    )
    default_notice_view = "xz" if lens == "cloud_precipitation" else "plan"
    scene = (
        _volume_scene(
            lens,
            fields,
            x_km,
            y_km,
            z_km,
            x_indices,
            y_indices,
            native_x_indices,
            native_y_indices,
            selected_z,
            history_path.name,
            viewport,
        )
        if purpose == "product"
        else None
    )
    return StormExaminationFrame(
        schema_version=(
            "supercells_explore_v1" if purpose == "product" else "storm_examination_gate_c_v1"
        ),
        authority_state=(
            "supercells_product_world"
            if purpose == "product"
            else "issue_418_gate_c_research_not_product"
        ),
        world_id="supercells" if purpose == "product" else None,
        simulation_id="supercells_quarter_circle_reference" if purpose == "product" else None,
        run_id=contract.run_id,
        case_id=contract.case_id,
        simulation_label=(
            "Quarter-Circle Supercell presentation simulation"
            if purpose == "product"
            else "Official CM1 r21.1 quarter-circle benchmark"
        ),
        lens_id=lens,
        lens_name=lens_name,
        lens_question=lens_question,
        what_to_notice_now=what_to_notice_by_view[default_notice_view],
        what_to_notice_by_view=what_to_notice_by_view,
        time_index=checked_time_index,
        time_seconds=time_seconds,
        times_seconds=[value for _path, value in inventory],
        mature_checkpoint_indices=_mature_checkpoint_indices(inventory),
        timeline_checkpoints=_timeline_checkpoints(inventory),
        viewport=viewport,
        viewport_bounds_km=bounds,
        primary_updraft=primary,
        selected_point=selected,
        plan=plan,
        xz_section=xz_section,
        yz_section=yz_section,
        scene=scene,
        caveats=[
            (
                "Saved histories are 2 minutes apart; continuity between frames remains "
                "inferred, not observed continuously."
                if purpose == "product"
                else "Saved histories are 15 minutes apart; continuity between frames is "
                "inferred, not observed continuously."
            ),
            "Coordinates are in the translating model frame; ground-relative horizontal wind "
            "adds (12.5, 3.0) m/s.",
            "Secondary rotating and convective structures are present after 60 minutes; "
            "no split lineage is assigned.",
            *(
                [
                    "Storm region is a fixed inspection window; use Full domain to inspect "
                    "later outer-domain structures."
                ]
                if purpose == "product"
                else []
            ),
            "The 15-20 km Rayleigh layer overlaps upper storm structure; this view does not "
            "diagnose its causal effect.",
            "Low-level fields can show motion and precipitation relationships but do not by "
            "themselves establish a cold pool.",
        ],
        provenance={
            "source_history_file": history_path.name,
            "source_kind": (
                "presentation_native_cm1_history"
                if purpose == "product"
                else "retained_native_cm1_history"
            ),
            "browser_payload": (
                "bounded 3-D layers, selected plan, and two native-grid vertical sections"
                if purpose == "product"
                else "selected plan and two native-grid vertical sections only"
            ),
            "interpolation": "none",
            "full_domain_level_of_detail": (
                "every_other_native_x_y_cell"
                if purpose == "product" and viewport == "full"
                else "all_native_x_y_cells_in_viewport"
            ),
            "coordinate_frame": "translating_model_coordinates",
            "primary_selection": (
                "strongest_updraft_within_fixed_storm_view"
                if purpose == "product" and viewport == "storm"
                else "strongest_updraft_within_full_domain"
            ),
            "product_boundary": (
                "Supercells production Explore"
                if purpose == "product"
                else "bounded Gate C research; not a Cloud World or final Lens implementation"
            ),
        },
        extraction_milliseconds=round((time.perf_counter() - started) * 1_000, 3),
    )


def _validated_inventory(
    run_dir: Path,
    contract: _RunContract,
) -> tuple[tuple[Path, float], ...]:
    fingerprint = _run_fingerprint(run_dir, contract)
    return _cached_inventory(str(run_dir), fingerprint, contract)


def _run_fingerprint(
    run_dir: Path,
    contract: _RunContract,
) -> tuple[tuple[str, int, int], ...]:
    paths = [run_dir / "run_manifest.json", run_dir / "case_manifest.json"]
    paths.extend(run_dir / name for name in contract.history_filenames)
    if contract.evidence_filename is not None:
        paths.append(run_dir / contract.evidence_filename)
    try:
        return tuple((path.name, path.stat().st_size, path.stat().st_mtime_ns) for path in paths)
    except OSError as exc:
        raise StormExaminationError(f"The {contract.unavailable_label} is unavailable.") from exc


@lru_cache(maxsize=4)
def _cached_inventory(
    run_dir_text: str,
    _fingerprint: tuple[tuple[str, int, int], ...],
    contract: _RunContract,
) -> tuple[tuple[Path, float], ...]:
    run_dir = Path(run_dir_text)
    try:
        manifest = json.loads((run_dir / "run_manifest.json").read_text())
        case_manifest = json.loads((run_dir / "case_manifest.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise StormExaminationError(
            "The retained benchmark identity could not be verified."
        ) from exc
    if manifest.get("run_id") != contract.run_id or manifest.get("lifecycle_state") != "completed":
        raise StormExaminationError("The selected Simulation is not an accepted completed run.")
    if case_manifest.get("case_id") != contract.case_id:
        raise StormExaminationError("The selected Simulation case identity does not match.")
    evidence_inventory: dict[str, tuple[int, int]] | None = None
    if contract.evidence_filename is not None:
        evidence_inventory = _presentation_evidence_inventory(
            run_dir / contract.evidence_filename,
            contract,
            case_manifest,
        )

    inventory: list[tuple[Path, float]] = []
    for expected_time, filename in zip(
        contract.expected_times_seconds,
        contract.history_filenames,
        strict=True,
    ):
        path = run_dir / filename
        if evidence_inventory is not None:
            expected_inventory_item = evidence_inventory.get(filename)
            try:
                actual_size = path.stat().st_size
            except OSError as exc:
                raise StormExaminationError(
                    "A required presentation history is unavailable."
                ) from exc
            if expected_inventory_item is None or (
                actual_size != expected_inventory_item[1]
                or expected_inventory_item[0] != expected_time
            ):
                raise StormExaminationError(
                    "The presentation history inventory changed after validation."
                )
            inventory.append((path, float(expected_time)))
            continue
        try:
            with xr.open_dataset(path, decode_times=False) as dataset:
                actual_time = float(np.asarray(dataset["time"].values).reshape(-1)[0])
        except (OSError, KeyError, ValueError) as exc:
            raise StormExaminationError("A required retained history is unreadable.") from exc
        if not np.isclose(actual_time, expected_time):
            raise StormExaminationError(
                "The retained history timeline does not match its contract."
            )
        inventory.append((path, actual_time))
    return tuple(inventory)


def _presentation_evidence_inventory(
    evidence_path: Path,
    contract: _RunContract,
    case_manifest: dict[str, Any],
) -> dict[str, tuple[int, int]]:
    try:
        evidence = json.loads(evidence_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise StormExaminationError("The presentation validation evidence is unreadable.") from exc
    if (
        evidence.get("evidence_version") != "supercell_presentation_run_evidence_v1"
        or evidence.get("kind") != "final"
        or evidence.get("run_id") != contract.run_id
        or evidence.get("case_id") != contract.case_id
        or evidence.get("source_run_id") != PRESERVED_RUN_ID
        or evidence.get("implementation_commit") != case_manifest.get("implementation_commit")
        or evidence.get("grid")
        != {
            "dx_m": 500.0,
            "dy_m": 500.0,
            "dz_m": 20_000.0 / 60.0,
            "nx": 240,
            "ny": 240,
            "nz": 60,
        }
        or evidence.get("duration_seconds") != 10_800
        or evidence.get("output_cadence_seconds") != 120
        or set(evidence.get("required_fields", [])) != PRESENTATION_REQUIRED_FIELDS
        or evidence.get("normal_completion") is not True
        or evidence.get("times_seconds") != list(contract.expected_times_seconds)
        or evidence.get("history_count") != len(contract.history_filenames)
    ):
        raise StormExaminationError("The presentation validation evidence is not accepted.")
    items = evidence.get("history_inventory")
    if not isinstance(items, list) or len(items) != len(contract.history_filenames):
        raise StormExaminationError("The presentation history evidence is incomplete.")
    inventory: dict[str, tuple[int, int]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise StormExaminationError("The presentation history evidence is invalid.")
        filename = item.get("filename")
        time_seconds = item.get("time_seconds")
        size_bytes = item.get("bytes")
        if (
            not isinstance(filename, str)
            or not isinstance(time_seconds, int)
            or not isinstance(size_bytes, int)
            or size_bytes <= 0
        ):
            raise StormExaminationError("The presentation history evidence is invalid.")
        inventory[filename] = (time_seconds, size_bytes)
    if set(inventory) != set(contract.history_filenames):
        raise StormExaminationError("The presentation history evidence names changed.")
    return inventory


def _validate_selected_history(dataset: xr.Dataset, expected_time: float) -> None:
    required = {
        "xh",
        "yh",
        "zh",
        "time",
        "winterp",
        "zvort",
        "uh",
        "dbz",
        "rain",
        "qc",
        "qr",
        "qi",
        "qs",
        "qg",
        "uinterp",
        "vinterp",
    }
    missing = sorted(required.difference(dataset.variables))
    if missing:
        raise StormExaminationError("The selected history lacks required Gate C evidence.")
    actual_time = float(np.asarray(dataset["time"].values).reshape(-1)[0])
    if not np.isclose(actual_time, expected_time):
        raise StormExaminationError("The selected history time changed after inventory validation.")


def _coordinate(dataset: xr.Dataset, name: str) -> np.ndarray[Any, np.dtype[np.float64]]:
    values = np.asarray(dataset[name].values, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise StormExaminationError(f"The retained {name} coordinate is invalid.")
    return values


def _field(dataset: xr.Dataset, name: str) -> np.ndarray[Any, np.dtype[np.float64]]:
    item = dataset[name]
    values = np.asarray(item.values, dtype=np.float64)
    if item.dims and item.dims[0] == "time":
        values = values[0]
    if not np.all(np.isfinite(values)):
        raise StormExaminationError(f"The retained {name} field contains non-finite values.")
    return values


def _default_level_index(
    lens: LensId, z_km: np.ndarray[Any, np.dtype[np.float64]], primary: int
) -> int:
    if lens == "rotating_updraft":
        return int(np.argmin(np.abs(z_km - 3.25)))
    if lens == "low_level_interactions":
        return int(np.argmin(np.abs(z_km - 1.25)))
    return primary


def _plan_view(
    lens: LensId,
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: np.ndarray[Any, np.dtype[np.float64]],
    level_index: int,
    x_indices: np.ndarray[Any, np.dtype[np.int64]],
    y_indices: np.ndarray[Any, np.dtype[np.int64]],
) -> PlanView:
    view_fields = {
        name: values[:, y_indices, :][:, :, x_indices]
        if values.ndim == 3
        else values[y_indices, :][:, x_indices]
        for name, values in fields.items()
    }
    view_x_km = x_km[x_indices]
    view_y_km = y_km[y_indices]
    composite_dbz = np.max(view_fields["dbz"], axis=0)
    rain_mm = view_fields["rain"] * 10.0
    overlays = {
        "composite_reflectivity": _layer(
            "composite_reflectivity",
            "Column-maximum reflectivity",
            "dBZ",
            "derived",
            ["dbz"],
            composite_dbz,
            _reflectivity_scale(),
            "maximum native dbz over all scalar z levels at each x/y cell",
        ),
        "accumulated_surface_rain": _layer(
            "accumulated_surface_rain",
            "Accumulated surface rain",
            "mm",
            "derived",
            ["rain"],
            rain_mm,
            _rain_scale(),
            "native accumulated rain in cm multiplied by 10 to display liquid-water depth in mm",
        ),
    }
    if lens == "rotating_updraft":
        total = _total_condensate_g_kg(view_fields)
        primary = _layer(
            "winterp",
            "Vertical velocity",
            "m/s",
            "native",
            ["winterp"],
            view_fields["winterp"][level_index],
            _midlevel_w_scale(),
        )
        overlays["vertical_vorticity"] = _layer(
            "zvort",
            "Vertical vorticity",
            "s^-1",
            "native",
            ["zvort"],
            view_fields["zvort"][level_index],
            _vorticity_scale(),
        )
        overlays["updraft_helicity"] = _layer(
            "uh",
            "2-5 km AGL updraft helicity",
            "m^2/s^2",
            "native",
            ["uh"],
            view_fields["uh"],
            _uh_scale(),
        )
        overlays["total_condensate"] = _layer(
            "total_condensate",
            "Total condensate",
            "g/kg",
            "derived",
            list(HYDROMETEORS),
            total[level_index],
            _condensate_scale(),
            "1000 * (qc + qr + qi + qs + qg)",
        )
        title = "Updraft and rotation"
        subtitle = "Signed vertical velocity with cyclonic vorticity and 2-5 km AGL UH"
        categories = None
        selection_z_indices = None
        vectors: list[WindVector] = []
    elif lens == "cloud_precipitation":
        total = _total_condensate_g_kg(view_fields)
        column_max = np.max(total, axis=0)
        strongest_level = np.argmax(total, axis=0)
        primary = _layer(
            "column_max_total_condensate",
            "Column-maximum total condensate",
            "g/kg",
            "derived",
            list(HYDROMETEORS),
            column_max,
            _condensate_scale(),
            "1000 * max_z(qc + qr + qi + qs + qg)",
        )
        categories = _column_hydrometeor_categories(view_fields, column_max, strongest_level)
        aligned_vertical_velocity = np.take_along_axis(
            view_fields["winterp"], strongest_level[np.newaxis, :, :], axis=0
        )[0]
        overlays["vertical_velocity"] = _layer(
            "vertical_velocity_at_condensate_maximum",
            "Vertical velocity at strongest condensate level",
            "m/s",
            "derived",
            ["winterp", *HYDROMETEORS],
            aligned_vertical_velocity,
            _midlevel_w_scale(),
            (
                "native winterp sampled at each x/y cell's level of maximum "
                "1000 * (qc + qr + qi + qs + qg)"
            ),
        )
        title = "Cloud and precipitation structure"
        subtitle = "Column-derived category and motion at each cell's strongest condensate level"
        selection_z_indices = [[int(value) for value in row] for row in strongest_level.tolist()]
        vectors = []
    else:
        primary = _layer(
            "winterp",
            "Low-level vertical velocity",
            "m/s",
            "native",
            ["winterp"],
            view_fields["winterp"][level_index],
            _low_level_w_scale(),
        )
        title = "Low-level motion and rain footprint"
        level_km = float(z_km[level_index])
        subtitle = (
            f"{level_km:.2f} km current motion, precipitation, model-relative flow, "
            "and historical rain accumulation"
        )
        selection_z_indices = None
        categories = None
        vectors = _wind_vectors(view_fields, view_x_km, view_y_km, level_index)
        precipitating = 1_000.0 * (
            view_fields["qr"][level_index]
            + view_fields["qs"][level_index]
            + view_fields["qg"][level_index]
        )
        overlays["low_level_precipitating_condensate"] = _layer(
            "low_level_precipitating_condensate",
            "Current precipitating condensate",
            "g/kg",
            "derived",
            ["qr", "qs", "qg"],
            precipitating,
            _condensate_scale(),
            f"1000 * (qr + qs + qg) at the displayed {level_km:.2f} km level",
        )
    return PlanView(
        title=title,
        subtitle=subtitle,
        x_indices=[int(value) for value in x_indices],
        y_indices=[int(value) for value in y_indices],
        x_km=_float_list(view_x_km),
        y_km=_float_list(view_y_km),
        level_index=level_index,
        level_km=float(z_km[level_index]),
        selection_z_indices=selection_z_indices,
        primary=primary,
        overlays=overlays,
        categories=categories,
        wind_vectors=vectors,
    )


def _vertical_section(
    lens: LensId,
    orientation: Literal["xz", "yz"],
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: np.ndarray[Any, np.dtype[np.float64]],
    x_index: int,
    y_index: int,
    x_indices: np.ndarray[Any, np.dtype[np.int64]],
    y_indices: np.ndarray[Any, np.dtype[np.int64]],
) -> VerticalSection:
    if orientation == "xz":
        horizontal_indices = x_indices
        horizontal = x_km[horizontal_indices]
        cross = float(y_km[y_index])
        dimension: Literal["x", "y"] = "x"
        title = f"x-z section at y = {cross:.1f} km"
        w_section = fields["winterp"][:, y_index, horizontal_indices]
        condensate = _total_condensate_g_kg(fields)[:, y_index, horizontal_indices]
        reflectivity = fields["dbz"][:, y_index, horizontal_indices]
        vorticity = fields["zvort"][:, y_index, horizontal_indices]
        precipitating = 1_000.0 * (
            fields["qr"][:, y_index, horizontal_indices]
            + fields["qs"][:, y_index, horizontal_indices]
            + fields["qg"][:, y_index, horizontal_indices]
        )
    else:
        horizontal_indices = y_indices
        horizontal = y_km[horizontal_indices]
        cross = float(x_km[x_index])
        dimension = "y"
        title = f"y-z section at x = {cross:.1f} km"
        w_section = fields["winterp"][:, horizontal_indices, x_index]
        condensate = _total_condensate_g_kg(fields)[:, horizontal_indices, x_index]
        reflectivity = fields["dbz"][:, horizontal_indices, x_index]
        vorticity = fields["zvort"][:, horizontal_indices, x_index]
        precipitating = 1_000.0 * (
            fields["qr"][:, horizontal_indices, x_index]
            + fields["qs"][:, horizontal_indices, x_index]
            + fields["qg"][:, horizontal_indices, x_index]
        )
    overlays = {
        "total_condensate": _layer(
            "total_condensate",
            "Total condensate",
            "g/kg",
            "derived",
            list(HYDROMETEORS),
            condensate,
            _condensate_scale(),
            "1000 * (qc + qr + qi + qs + qg)",
        ),
        "precipitating_condensate": _layer(
            "precipitating_condensate",
            "Rain, snow, and hail-treated large ice",
            "g/kg",
            "derived",
            ["qr", "qs", "qg"],
            precipitating,
            _condensate_scale(),
            "1000 * (qr + qs + qg)",
        ),
        "reflectivity": _layer(
            "dbz",
            "Reflectivity",
            "dBZ",
            "native",
            ["dbz"],
            reflectivity,
            _reflectivity_scale(),
        ),
        "vertical_velocity": _layer(
            "winterp",
            "Vertical velocity",
            "m/s",
            "native",
            ["winterp"],
            w_section,
            _section_w_scale(),
        ),
        "vertical_vorticity": _layer(
            "zvort",
            "Vertical vorticity",
            "s^-1",
            "native",
            ["zvort"],
            vorticity,
            _vorticity_scale(),
        ),
    }
    if lens == "cloud_precipitation":
        primary = overlays["total_condensate"]
        categories = _section_hydrometeor_categories(
            fields, orientation, x_index, y_index, horizontal_indices
        )
    else:
        primary = overlays["vertical_velocity"]
        categories = None
    return VerticalSection(
        orientation=orientation,
        title=title,
        horizontal_dimension=dimension,
        horizontal_indices=[int(value) for value in horizontal_indices],
        horizontal_km=_float_list(horizontal),
        z_km=_float_list(z_km),
        cross_section_coordinate_km=cross,
        primary=primary,
        overlays=overlays,
        categories=categories,
    )


def _selected_point(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: np.ndarray[Any, np.dtype[np.float64]],
    x_index: int,
    y_index: int,
    z_index: int,
    time_seconds: float,
    primary: PointMarker,
) -> SelectedPointEvidence:
    index = (z_index, y_index, x_index)
    values = {
        "vertical_velocity": float(fields["winterp"][index]),
        "vertical_vorticity": float(fields["zvort"][index]),
        "reflectivity": float(fields["dbz"][index]),
        "cloud_liquid": float(fields["qc"][index] * 1_000.0),
        "rain_water": float(fields["qr"][index] * 1_000.0),
        "cloud_ice": float(fields["qi"][index] * 1_000.0),
        "snow": float(fields["qs"][index] * 1_000.0),
        "hail_treated_large_ice": float(fields["qg"][index] * 1_000.0),
        "total_condensate": float(
            sum(float(fields[name][index]) for name in HYDROMETEORS) * 1_000.0
        ),
        "accumulated_surface_rain": float(fields["rain"][y_index, x_index] * 10.0),
        "model_relative_u": float(fields["uinterp"][index]),
        "model_relative_v": float(fields["vinterp"][index]),
        "updraft_helicity": float(fields["uh"][y_index, x_index]),
    }
    w = values["vertical_velocity"]
    condensate = values["total_condensate"]
    states = ["Rising" if w >= 1.0 else "Descending" if w <= -1.0 else "Near neutral"]
    states.append("Condensate present" if condensate >= 0.05 else "Little condensate")
    states.append(
        "Rain footprint" if values["accumulated_surface_rain"] >= 0.1 else "No accumulated rain"
    )
    distance = float(
        np.hypot(float(x_km[x_index]) - primary.x_km, float(y_km[y_index]) - primary.y_km)
    )
    native_keys = {
        "vertical_velocity",
        "vertical_vorticity",
        "reflectivity",
        "cloud_liquid",
        "rain_water",
        "cloud_ice",
        "snow",
        "hail_treated_large_ice",
        "model_relative_u",
        "model_relative_v",
        "updraft_helicity",
    }
    units = {
        "vertical_velocity": "m/s",
        "vertical_vorticity": "s^-1",
        "reflectivity": "dBZ",
        "cloud_liquid": "g/kg",
        "rain_water": "g/kg",
        "cloud_ice": "g/kg",
        "snow": "g/kg",
        "hail_treated_large_ice": "g/kg",
        "total_condensate": "g/kg",
        "accumulated_surface_rain": "mm",
        "model_relative_u": "m/s",
        "model_relative_v": "m/s",
        "updraft_helicity": "m^2/s^2",
    }
    return SelectedPointEvidence(
        x_index=x_index,
        y_index=y_index,
        z_index=z_index,
        x_km=float(x_km[x_index]),
        y_km=float(y_km[y_index]),
        z_km=float(z_km[z_index]),
        model_time_seconds=time_seconds,
        coordinate_frame="translating model frame; native model-relative winds",
        values=values,
        units=units,
        evidence_kind={key: "native" if key in native_keys else "derived" for key in values},
        states=states,
        distance_to_primary_updraft_km=distance,
    )


def _layer(
    key: str,
    display_name: str,
    units: str,
    evidence_kind: Literal["native", "derived"],
    source_fields: list[str],
    values: np.ndarray[Any, np.dtype[np.float64]],
    scale: ScaleMetadata,
    derivation: str | None = None,
) -> FieldLayer:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise StormExaminationError(f"The {key} view has no finite values.")
    return FieldLayer(
        key=key,
        display_name=display_name,
        units=units,
        evidence_kind=evidence_kind,
        source_fields=source_fields,
        derivation=derivation,
        values=_matrix(values),
        selected_frame_minimum=float(np.min(finite)),
        selected_frame_maximum=float(np.max(finite)),
        scale=scale,
    )


def _total_condensate_g_kg(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
) -> np.ndarray[Any, np.dtype[np.float64]]:
    total = np.zeros_like(fields["qc"], dtype=np.float64)
    for name in HYDROMETEORS:
        total += fields[name]
    return total * 1_000.0


def _column_hydrometeor_categories(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    column_max: np.ndarray[Any, np.dtype[np.float64]],
    strongest_level: np.ndarray[Any, np.dtype[np.int64]],
) -> CategoryLayer:
    masses = np.stack([fields[name] for name in HYDROMETEORS], axis=0)
    categories = np.zeros(column_max.shape, dtype=np.int64)
    for y_index in range(column_max.shape[0]):
        for x_index in range(column_max.shape[1]):
            if column_max[y_index, x_index] < 0.05:
                continue
            level = int(strongest_level[y_index, x_index])
            categories[y_index, x_index] = int(np.argmax(masses[:, level, y_index, x_index])) + 1
    magnitude = _layer(
        "column_max_total_condensate",
        "Column-maximum total condensate",
        "g/kg",
        "derived",
        list(HYDROMETEORS),
        column_max,
        _condensate_scale(),
        "1000 * max_z(qc + qr + qi + qs + qg)",
    )
    return _category_layer(categories, magnitude, "dominant species at max total-condensate level")


def _section_hydrometeor_categories(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    orientation: Literal["xz", "yz"],
    x_index: int,
    y_index: int,
    horizontal_indices: np.ndarray[Any, np.dtype[np.int64]],
) -> CategoryLayer:
    masses = np.stack([fields[name] for name in HYDROMETEORS], axis=0)
    if orientation == "xz":
        section_masses = masses[:, :, y_index, horizontal_indices]
    else:
        section_masses = masses[:, :, horizontal_indices, x_index]
    total = np.sum(section_masses, axis=0) * 1_000.0
    categories = np.argmax(section_masses, axis=0).astype(np.int64) + 1
    categories[total < 0.05] = 0
    magnitude = _layer(
        "total_condensate",
        "Total condensate",
        "g/kg",
        "derived",
        list(HYDROMETEORS),
        total,
        _condensate_scale(),
        "1000 * (qc + qr + qi + qs + qg)",
    )
    return _category_layer(categories, magnitude, "largest native hydrometeor mass mixing ratio")


def _category_layer(
    values: np.ndarray[Any, np.dtype[np.int64]], magnitude: FieldLayer, method: str
) -> CategoryLayer:
    return CategoryLayer(
        key="dominant_hydrometeor",
        display_name="Dominant hydrometeor category",
        source_fields=list(HYDROMETEORS),
        derivation=(
            f"{method}; categories appear only where total condensate is at least 0.05 g/kg"
        ),
        values=[[int(value) for value in row] for row in values.tolist()],
        magnitude=magnitude,
        categories=_hydrometeor_category_definitions(),
    )


def _hydrometeor_category_definitions() -> list[CategoryDefinition]:
    return [
        CategoryDefinition(
            code=0, key="clear", label="Below condensate threshold", color="#ffffff"
        ),
        CategoryDefinition(code=1, key="qc", label="Cloud liquid", color="#62c6d7"),
        CategoryDefinition(code=2, key="qr", label="Rain", color="#2a78b8"),
        CategoryDefinition(code=3, key="qi", label="Cloud ice", color="#cab6e8"),
        CategoryDefinition(code=4, key="qs", label="Snow", color="#8b9fd8"),
        CategoryDefinition(code=5, key="qg", label="Hail-treated large ice", color="#e38a36"),
    ]


def _wind_vectors(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    level_index: int,
) -> list[WindVector]:
    stride = 8
    vectors: list[WindVector] = []
    for y_index in range(0, len(y_km), stride):
        for x_index in range(0, len(x_km), stride):
            u = float(fields["uinterp"][level_index, y_index, x_index])
            v = float(fields["vinterp"][level_index, y_index, x_index])
            vectors.append(
                WindVector(
                    x_km=float(x_km[x_index]),
                    y_km=float(y_km[y_index]),
                    u_m_s=u,
                    v_m_s=v,
                    magnitude_m_s=float(np.hypot(u, v)),
                )
            )
    return vectors


def _volume_scene(
    lens: LensId,
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: np.ndarray[Any, np.dtype[np.float64]],
    x_indices: np.ndarray[Any, np.dtype[np.int64]],
    y_indices: np.ndarray[Any, np.dtype[np.int64]],
    navigation_x_indices: np.ndarray[Any, np.dtype[np.int64]],
    navigation_y_indices: np.ndarray[Any, np.dtype[np.int64]],
    level_index: int,
    history_filename: str,
    viewport: ViewportId,
) -> StormVolumeScene:
    view = {
        name: values[:, y_indices, :][:, :, x_indices]
        if values.ndim == 3
        else values[y_indices, :][:, x_indices]
        for name, values in fields.items()
    }
    view_x = x_km[x_indices]
    view_y = y_km[y_indices]
    total = _total_condensate_g_kg(view)
    precipitating = 1_000.0 * (view["qr"] + view["qs"] + view["qg"])
    budget_scale = 1.0 if viewport == "storm" else 0.62
    low_level_volume = z_km[:, np.newaxis, np.newaxis] <= 5.25
    scene_z_max = 5.25 if lens == "low_level_interactions" else float(np.max(z_km))
    scene_z_indices = np.flatnonzero(z_km <= scene_z_max)

    cloud = _volume_layer(
        key="storm_cloud_body",
        display_name="Storm cloud body",
        units="g/kg",
        evidence_kind="derived",
        source_fields=list(HYDROMETEORS),
        derivation="1000 * (qc + qr + qi + qs + qg)",
        rendering="neutral_cloud",
        values=total,
        mask=(total >= 0.05) & (low_level_volume if lens == "low_level_interactions" else True),
        x_km=view_x,
        y_km=view_y,
        z_km=z_km,
        point_budget=round(12_000 * budget_scale),
        threshold_label="Total condensate at or above 0.05 g/kg",
        default_visible=lens == "rotating_updraft",
        default_opacity=0.22,
        default_point_size=4.5,
        scale=_condensate_scale(),
    )
    layers: list[VolumeLayer] = [cloud]
    wind_vectors: list[VolumeWindVector] = []

    if lens == "rotating_updraft":
        layers.extend(
            [
                _volume_layer(
                    key="rising_core",
                    display_name="Rising core",
                    units="m/s",
                    evidence_kind="native",
                    source_fields=["winterp"],
                    derivation=None,
                    rendering="signed_scalar",
                    values=view["winterp"],
                    mask=view["winterp"] >= 5.0,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(6_000 * budget_scale),
                    threshold_label="Rising motion at or above 5 m/s",
                    default_visible=True,
                    default_opacity=0.88,
                    default_point_size=6.8,
                    scale=_midlevel_w_scale(),
                ),
                _volume_layer(
                    key="strong_descent",
                    display_name="Strong descent",
                    units="m/s",
                    evidence_kind="native",
                    source_fields=["winterp"],
                    derivation=None,
                    rendering="signed_scalar",
                    values=view["winterp"],
                    mask=view["winterp"] <= -5.0,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(3_000 * budget_scale),
                    threshold_label="Descending motion at or below -5 m/s",
                    default_visible=False,
                    default_opacity=0.58,
                    default_point_size=5.0,
                    scale=_midlevel_w_scale(),
                ),
                _volume_layer(
                    key="cyclonic_rotation",
                    display_name="Cyclonic vertical vorticity",
                    units="s^-1",
                    evidence_kind="native",
                    source_fields=["zvort"],
                    derivation=None,
                    rendering="scalar",
                    values=view["zvort"],
                    mask=(view["zvort"] >= 0.01) & (view["winterp"] >= 2.0),
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(3_500 * budget_scale),
                    threshold_label="Cyclonic vorticity at or above 0.01 s^-1 in rising air",
                    default_visible=True,
                    default_opacity=0.92,
                    default_point_size=4.2,
                    scale=_vorticity_scale(),
                ),
                _surface_volume_layer(
                    key="updraft_helicity",
                    display_name="2-5 km AGL updraft helicity",
                    units="m^2/s^2",
                    evidence_kind="native",
                    source_fields=["uh"],
                    derivation=None,
                    rendering="scalar",
                    values=view["uh"],
                    mask=view["uh"] >= 300.0,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=float(z_km[0]),
                    point_budget=round(3_000 * budget_scale),
                    threshold_label="Cyclonic 2-5 km AGL UH at or above 300 m^2/s^2",
                    default_visible=True,
                    default_opacity=0.78,
                    default_point_size=5.2,
                    scale=_uh_scale(),
                ),
                _volume_layer(
                    key="reflectivity",
                    display_name="Reflectivity",
                    units="dBZ",
                    evidence_kind="native",
                    source_fields=["dbz"],
                    derivation=None,
                    rendering="scalar",
                    values=view["dbz"],
                    mask=(view["dbz"] >= 20.0) & low_level_volume,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(5_000 * budget_scale),
                    threshold_label="Reflectivity at or above 20 dBZ",
                    default_visible=False,
                    default_opacity=0.58,
                    default_point_size=5.0,
                    scale=_reflectivity_scale(),
                ),
            ]
        )
    elif lens == "cloud_precipitation":
        masses = np.stack([view[name] for name in HYDROMETEORS], axis=0)
        categories = np.argmax(masses, axis=0).astype(np.int64) + 1
        dominant_mass = np.max(masses, axis=0) * 1_000.0
        category_thresholds = np.asarray([0.0, 0.10, 0.20, 0.10, 0.30, 2.00])
        category_mask = dominant_mass >= category_thresholds[categories]
        categories[~category_mask] = 0
        layers.extend(
            [
                _volume_layer(
                    key="hydrometeor_categories",
                    display_name="Dominant hydrometeor",
                    units="g/kg",
                    evidence_kind="derived",
                    source_fields=list(HYDROMETEORS),
                    derivation="largest native hydrometeor mass mixing ratio per cloudy cell",
                    rendering="categorical",
                    values=total,
                    mask=category_mask,
                    categories=categories,
                    category_definitions=_hydrometeor_category_definitions(),
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(10_000 * budget_scale),
                    threshold_label=(
                        "Native dominant-species thresholds: qc/qi 0.10, qr 0.20, "
                        "qs 0.30, qg 2.00 g/kg"
                    ),
                    default_visible=True,
                    default_opacity=0.42,
                    default_point_size=4.2,
                    scale=_condensate_scale(),
                ),
                _volume_layer(
                    key="vertical_motion",
                    display_name="Strong vertical motion",
                    units="m/s",
                    evidence_kind="native",
                    source_fields=["winterp"],
                    derivation=None,
                    rendering="signed_scalar",
                    values=view["winterp"],
                    mask=np.abs(view["winterp"]) >= 8.0,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(5_000 * budget_scale),
                    threshold_label="Absolute vertical velocity at or above 8 m/s",
                    default_visible=False,
                    default_opacity=0.6,
                    default_point_size=5.5,
                    scale=_section_w_scale(),
                ),
                _volume_layer(
                    key="reflectivity",
                    display_name="Reflectivity",
                    units="dBZ",
                    evidence_kind="native",
                    source_fields=["dbz"],
                    derivation=None,
                    rendering="scalar",
                    values=view["dbz"],
                    mask=view["dbz"] >= 25.0,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(5_000 * budget_scale),
                    threshold_label="Reflectivity at or above 25 dBZ",
                    default_visible=False,
                    default_opacity=0.55,
                    default_point_size=5.0,
                    scale=_reflectivity_scale(),
                ),
            ]
        )
    else:
        layers.extend(
            [
                _surface_volume_layer(
                    key="low_level_vertical_motion",
                    display_name="Low-level vertical motion",
                    units="m/s",
                    evidence_kind="native",
                    source_fields=["winterp"],
                    derivation=None,
                    rendering="signed_scalar",
                    values=view["winterp"][level_index],
                    mask=np.ones_like(view["winterp"][level_index], dtype=np.bool_),
                    x_km=view_x,
                    y_km=view_y,
                    z_km=float(z_km[level_index]),
                    point_budget=round(8_000 * budget_scale),
                    threshold_label=f"Native plane at z = {float(z_km[level_index]):.2f} km",
                    default_visible=True,
                    default_opacity=0.72,
                    default_point_size=5.0,
                    scale=_low_level_w_scale(),
                ),
                _surface_volume_layer(
                    key="accumulated_surface_rain",
                    display_name="Accumulated surface rain",
                    units="mm",
                    evidence_kind="derived",
                    source_fields=["rain"],
                    derivation="native accumulated rain in cm multiplied by 10",
                    rendering="scalar",
                    values=view["rain"] * 10.0,
                    mask=view["rain"] >= 0.01,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=float(z_km[0]),
                    point_budget=round(5_000 * budget_scale),
                    threshold_label="Accumulated rain at or above 0.1 mm",
                    default_visible=True,
                    default_opacity=0.72,
                    default_point_size=5.5,
                    scale=_rain_scale(),
                ),
                _volume_layer(
                    key="precipitating_condensate",
                    display_name="Low-level precipitating condensate",
                    units="g/kg",
                    evidence_kind="derived",
                    source_fields=["qr", "qs", "qg"],
                    derivation="1000 * (qr + qs + qg)",
                    rendering="scalar",
                    values=precipitating,
                    mask=(precipitating >= 0.25) & (z_km[:, np.newaxis, np.newaxis] <= 3.25),
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(6_000 * budget_scale),
                    threshold_label=(
                        "Rain, snow, and hail-treated large ice at or above 0.25 g/kg "
                        "through 3.25 km"
                    ),
                    default_visible=True,
                    default_opacity=0.24,
                    default_point_size=3.2,
                    scale=_precipitating_condensate_scale(),
                ),
                _volume_layer(
                    key="reflectivity",
                    display_name="Reflectivity",
                    units="dBZ",
                    evidence_kind="native",
                    source_fields=["dbz"],
                    derivation=None,
                    rendering="scalar",
                    values=view["dbz"],
                    mask=(view["dbz"] >= 20.0) & low_level_volume,
                    x_km=view_x,
                    y_km=view_y,
                    z_km=z_km,
                    point_budget=round(5_000 * budget_scale),
                    threshold_label="Reflectivity at or above 20 dBZ",
                    default_visible=False,
                    default_opacity=0.52,
                    default_point_size=5.0,
                    scale=_reflectivity_scale(),
                ),
            ]
        )
        wind_vectors = _volume_wind_vectors(
            view,
            view_x,
            view_y,
            float(z_km[level_index]),
            level_index,
            10 if viewport == "storm" else 5,
        )

    return StormVolumeScene(
        coordinate_extents_km={
            "x": {"min": float(np.min(view_x)), "max": float(np.max(view_x))},
            "y": {"min": float(np.min(view_y)), "max": float(np.max(view_y))},
            "z": {"min": float(np.min(z_km)), "max": scene_z_max},
        },
        coordinate_sizes={
            "x": len(x_km),
            "y": len(y_km),
            "z": len(scene_z_indices),
        },
        coordinate_indices={
            "x": [int(value) for value in navigation_x_indices],
            "y": [int(value) for value in navigation_y_indices],
            "z": [int(value) for value in scene_z_indices],
        },
        coordinate_values_km={
            "x": _float_list(x_km[navigation_x_indices]),
            "y": _float_list(y_km[navigation_y_indices]),
            "z": _float_list(z_km[scene_z_indices]),
        },
        layers=layers,
        wind_vectors=wind_vectors,
        wind_reference_m_s=25.0,
        point_budget=sum(layer.returned_count for layer in layers),
        source_history_file=history_filename,
    )


def _volume_layer(
    *,
    key: str,
    display_name: str,
    units: str,
    evidence_kind: Literal["native", "derived"],
    source_fields: list[str],
    derivation: str | None,
    rendering: Literal["neutral_cloud", "signed_scalar", "scalar", "categorical"],
    values: np.ndarray[Any, np.dtype[np.float64]],
    mask: np.ndarray[Any, np.dtype[np.bool_]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: np.ndarray[Any, np.dtype[np.float64]],
    point_budget: int,
    threshold_label: str,
    default_visible: bool,
    default_opacity: float,
    default_point_size: float,
    scale: ScaleMetadata | None,
    categories: np.ndarray[Any, np.dtype[np.int64]] | None = None,
    category_definitions: list[CategoryDefinition] | None = None,
) -> VolumeLayer:
    locations = np.argwhere(mask & np.isfinite(values))
    source_count = len(locations)
    if source_count > point_budget:
        stride = max(1, int(np.ceil(source_count / point_budget)))
        locations = locations[::stride][:point_budget]
    points = [
        (
            round(float(x_km[x_index]), 5),
            round(float(y_km[y_index]), 5),
            round(float(z_km[z_index]), 5),
            round(float(values[z_index, y_index, x_index]), 6),
            int(categories[z_index, y_index, x_index]) if categories is not None else 0,
        )
        for z_index, y_index, x_index in locations
    ]
    return VolumeLayer(
        key=key,
        display_name=display_name,
        units=units,
        evidence_kind=evidence_kind,
        source_fields=source_fields,
        derivation=derivation,
        rendering=rendering,
        points=points,
        source_count=source_count,
        returned_count=len(points),
        threshold_label=threshold_label,
        default_visible=default_visible,
        default_opacity=default_opacity,
        default_point_size=default_point_size,
        scale=scale,
        categories=category_definitions or [],
    )


def _surface_volume_layer(
    *,
    values: np.ndarray[Any, np.dtype[np.float64]],
    mask: np.ndarray[Any, np.dtype[np.bool_]],
    z_km: float,
    **kwargs: Any,
) -> VolumeLayer:
    return _volume_layer(
        values=values[np.newaxis, :, :],
        mask=mask[np.newaxis, :, :],
        z_km=np.asarray([z_km], dtype=np.float64),
        **kwargs,
    )


def _volume_wind_vectors(
    fields: dict[str, np.ndarray[Any, np.dtype[np.float64]]],
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    z_km: float,
    level_index: int,
    stride: int,
) -> list[VolumeWindVector]:
    vectors: list[VolumeWindVector] = []
    for y_index in range(0, len(y_km), stride):
        for x_index in range(0, len(x_km), stride):
            u = float(fields["uinterp"][level_index, y_index, x_index])
            v = float(fields["vinterp"][level_index, y_index, x_index])
            vectors.append(
                VolumeWindVector(
                    x_km=float(x_km[x_index]),
                    y_km=float(y_km[y_index]),
                    z_km=z_km,
                    u_m_s=u,
                    v_m_s=v,
                    magnitude_m_s=float(np.hypot(u, v)),
                )
            )
    return vectors


def _viewport_bounds(
    viewport: ViewportId,
    x_km: np.ndarray[Any, np.dtype[np.float64]],
    y_km: np.ndarray[Any, np.dtype[np.float64]],
    purpose: FramePurpose,
) -> dict[str, float]:
    x_min, x_max = float(np.min(x_km) - 0.5), float(np.max(x_km) + 0.5)
    y_min, y_max = float(np.min(y_km) - 0.5), float(np.max(y_km) + 0.5)
    if viewport == "full":
        return {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}
    requested = STORM_VIEW_BOUNDS_KM if purpose == "product" else GATE_C_STORM_VIEW_BOUNDS_KM
    return {
        "x_min": max(x_min, requested["x_min"]),
        "x_max": min(x_max, requested["x_max"]),
        "y_min": max(y_min, requested["y_min"]),
        "y_max": min(y_max, requested["y_max"]),
    }


def _what_to_notice_by_view(
    lens: LensId,
    time_seconds: float,
    plan: PlanView,
    xz_section: VerticalSection,
    yz_section: VerticalSection,
) -> dict[str, str]:
    minutes = round(time_seconds / 60)
    if lens == "rotating_updraft":
        w = np.asarray(plan.primary.values, dtype=np.float64)
        vorticity = np.asarray(plan.overlays["vertical_vorticity"].values, dtype=np.float64)
        overlap = int(np.count_nonzero((w >= 5.0) & (vorticity >= 0.01)))
        uh_max = plan.overlays["updraft_helicity"].selected_frame_maximum
        return {
            "plan": (
                f"At {minutes} min, {overlap} cells on the {plan.level_km:.2f} km slice combine "
                f"rising motion of at least 5 m/s with cyclonic vorticity of at least "
                f"0.01 s^-1; 2-5 km AGL UH peaks at {uh_max:.0f} m^2/s^2."
            ),
            "xz": _rotating_section_notice(minutes, xz_section),
            "yz": _rotating_section_notice(minutes, yz_section),
        }
    if lens == "cloud_precipitation":
        categories = plan.categories
        if categories is None:
            plan_notice = f"At {minutes} min, the column-derived cloud view is unavailable."
        else:
            common = _most_common_category(categories)
            plan_notice = (
                f"At {minutes} min, the column-derived x-y view most often assigns "
                f"{common.lower()} where condensate is present; column-maximum total "
                f"condensate reaches {plan.primary.selected_frame_maximum:.2f} g/kg. "
                "Selecting a cell inspects the native level responsible for that category."
            )
        return {
            "plan": plan_notice,
            "xz": _cloud_section_notice(minutes, xz_section),
            "yz": _cloud_section_notice(minutes, yz_section),
        }
    w_min = plan.primary.selected_frame_minimum
    w_max = plan.primary.selected_frame_maximum
    rain_max = plan.overlays["accumulated_surface_rain"].selected_frame_maximum
    precip_max = plan.overlays["low_level_precipitating_condensate"].selected_frame_maximum
    return {
        "plan": (
            f"At {minutes} min, current {plan.level_km:.2f} km motion spans "
            f"{w_min:+.1f} to "
            f"{w_max:+.1f} m/s and precipitating condensate reaches "
            f"{precip_max:.2f} g/kg; the historical rain footprint peaks at "
            f"{rain_max:.1f} mm."
        ),
        "xz": _low_level_section_notice(minutes, xz_section),
        "yz": _low_level_section_notice(minutes, yz_section),
    }


def _most_common_category(categories: CategoryLayer) -> str:
    codes = np.asarray(categories.values, dtype=np.int64)
    present = codes[codes > 0]
    definitions = {item.code: item.label for item in categories.categories}
    if present.size == 0:
        return "No hydrometeor"
    return definitions[int(np.bincount(present).argmax())]


def _rotating_section_notice(minutes: int, section: VerticalSection) -> str:
    w = np.asarray(section.primary.values, dtype=np.float64)
    vorticity = np.asarray(section.overlays["vertical_vorticity"].values, dtype=np.float64)
    overlap = int(np.count_nonzero((w >= 5.0) & (vorticity >= 0.01)))
    return (
        f"At {minutes} min, this {section.orientation} section intersects {overlap} cells "
        f"with both rising motion of at least 5 m/s and cyclonic vorticity of at least "
        f"0.01 s^-1; vertical velocity spans "
        f"{section.primary.selected_frame_minimum:+.1f} to "
        f"{section.primary.selected_frame_maximum:+.1f} m/s."
    )


def _cloud_section_notice(minutes: int, section: VerticalSection) -> str:
    categories = section.categories
    if categories is None:
        return f"At {minutes} min, this {section.orientation} cloud section is unavailable."
    common = _most_common_category(categories)
    total_max = section.primary.selected_frame_maximum
    precip_max = section.overlays["precipitating_condensate"].selected_frame_maximum
    coordinate = "y" if section.orientation == "xz" else "x"
    return (
        f"At {minutes} min, this {section.orientation} section through {coordinate} = "
        f"{section.cross_section_coordinate_km:.1f} km most often shows {common.lower()} "
        f"where condensate is present; total condensate reaches {total_max:.2f} g/kg "
        f"and precipitating condensate reaches {precip_max:.2f} g/kg."
    )


def _low_level_section_notice(minutes: int, section: VerticalSection) -> str:
    precip_max = section.overlays["precipitating_condensate"].selected_frame_maximum
    coordinate = "y" if section.orientation == "xz" else "x"
    return (
        f"At {minutes} min, this {section.orientation} section through {coordinate} = "
        f"{section.cross_section_coordinate_km:.1f} km shows vertical motion from "
        f"{section.primary.selected_frame_minimum:+.1f} to "
        f"{section.primary.selected_frame_maximum:+.1f} m/s; current precipitating "
        f"condensate reaches {precip_max:.2f} g/kg."
    )


def _lens_identity(lens: LensId) -> tuple[str, str]:
    if lens == "rotating_updraft":
        return (
            "Rotating Updraft",
            "Where is the storm rising and rotating as one organized structure?",
        )
    if lens == "cloud_precipitation":
        return (
            "Cloud and Precipitation",
            "How are liquid, ice, and precipitation arranged through the storm?",
        )
    return (
        "Low-Level Interactions",
        "How do low-level ascent, descent, rain, and horizontal flow meet beneath the storm?",
    )


def _timeline_checkpoints(
    inventory: tuple[tuple[Path, float], ...],
) -> list[TimelineCheckpoint]:
    gate_c_checkpoints = (
        (2_700, "Established deep rotating storm"),
        (3_600, "Mature storm with secondary convection"),
        (4_440, "Dominant core and growing secondary cells"),
        (5_400, "Multiple active convective structures"),
        (6_240, "Expanding storm field"),
        (7_200, "Strong southern core in a broad storm field"),
    )
    presentation_extension = (
        (8_400, "Persistent southern convection"),
        (9_600, "Renewed intense rotation"),
        (10_800, "Active structures across the full domain"),
    )
    requested = (
        (*gate_c_checkpoints, *presentation_extension)
        if inventory[-1][1] > 7_200
        else gate_c_checkpoints
    )
    available = [int(round(value)) for _path, value in inventory]
    checkpoints: list[TimelineCheckpoint] = []
    used: set[int] = set()
    for source_time, phase in requested:
        selected = min(available, key=lambda value: abs(value - source_time))
        if selected in used:
            continue
        used.add(selected)
        checkpoints.append(
            TimelineCheckpoint(
                time_seconds=selected,
                label=f"{selected // 60} min",
                phase=phase,
                phase_kind="visible_checkpoint",
            )
        )
    return checkpoints


def _mature_checkpoint_indices(
    inventory: tuple[tuple[Path, float], ...],
) -> list[int]:
    checkpoint_times = {checkpoint.time_seconds for checkpoint in _timeline_checkpoints(inventory)}
    return [
        index
        for index, (_path, value) in enumerate(inventory)
        if int(round(value)) in checkpoint_times
    ]


def _matrix(values: np.ndarray[Any, np.dtype[np.float64]]) -> list[list[float | None]]:
    return [
        [round(float(value), 6) if np.isfinite(value) else None for value in row]
        for row in values.tolist()
    ]


def _float_list(values: np.ndarray[Any, np.dtype[np.float64]]) -> list[float]:
    return [round(float(value), 6) for value in values]


def _checked_index(value: int, size: int, name: str) -> int:
    if value < 0 or value >= size:
        raise StormExaminationError(f"{name} is outside the retained native grid.")
    return value


def _coordinate_indices(
    values: np.ndarray[Any, np.dtype[np.float64]], minimum: float, maximum: float
) -> np.ndarray[Any, np.dtype[np.int64]]:
    indices = np.flatnonzero((values >= minimum) & (values <= maximum)).astype(np.int64)
    if indices.size == 0:
        raise StormExaminationError("The requested viewport contains no native grid cells.")
    return indices


def _midlevel_w_scale() -> ScaleMetadata:
    return _w_scale(
        "supercell_midlevel_vertical_velocity_v1", 30.0, [-20, -8, -2, 2, 5, 10, 15, 20, 25]
    )


def _low_level_w_scale() -> ScaleMetadata:
    return _w_scale(
        "supercell_low_level_vertical_velocity_v1", 15.0, [-10, -5, -1, 1, 3, 5, 8, 11, 13]
    )


def _section_w_scale() -> ScaleMetadata:
    return _w_scale(
        "supercell_full_depth_vertical_velocity_v1", 65.0, [-45, -20, -3, 3, 10, 20, 35, 50, 60]
    )


def _w_scale(scale_id: str, maximum: float, breakpoints: list[float]) -> ScaleMetadata:
    return ScaleMetadata(
        scale_id=scale_id,
        display_name="Vertical velocity",
        units="m/s",
        scale_type="fixed_discrete",
        minimum=-maximum,
        maximum=maximum,
        breakpoints=breakpoints,
        colors=list(W_COLORS),
    )


def _reflectivity_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_reflectivity_v2",
        display_name="Reflectivity",
        units="dBZ",
        scale_type="fixed_continuous",
        minimum=-10,
        maximum=75,
        breakpoints=[20, 40, 60],
        colors=["#d8e5eb", "#8ac7b8", "#f1c453", "#d65332"],
    )


def _rain_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_accumulated_rain_v2",
        display_name="Accumulated surface rain",
        units="mm",
        scale_type="fixed_continuous",
        minimum=0,
        maximum=120,
        breakpoints=[1, 10, 30, 60],
        colors=["#ffffff", "#c7e1ee", "#6daed1", "#236b9e", "#0b3557"],
    )


def _condensate_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_total_condensate_v2",
        display_name="Total condensate",
        units="g/kg",
        scale_type="fixed_continuous",
        minimum=0,
        maximum=20,
        breakpoints=[0.05, 0.5, 2, 8],
        colors=["#ffffff", "#d9eef2", "#86cbd7", "#3a91ae", "#15506f"],
    )


def _precipitating_condensate_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_low_level_precipitating_condensate_v1",
        display_name="Low-level precipitating condensate",
        units="g/kg",
        scale_type="fixed_continuous",
        minimum=0,
        maximum=10,
        breakpoints=[0.25, 1, 3, 6],
        colors=["#f4ecdc", "#dfc18b", "#bd8446", "#8a5526", "#583516"],
    )


def _vorticity_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_vertical_vorticity_v1",
        display_name="Cyclonic vertical vorticity",
        units="s^-1",
        scale_type="fixed_continuous",
        minimum=0,
        maximum=0.035,
        breakpoints=[0.01, 0.02, 0.03],
        colors=["#d8c4e2", "#9c5bad", "#632b73", "#32113d"],
    )


def _uh_scale() -> ScaleMetadata:
    return ScaleMetadata(
        scale_id="supercell_updraft_helicity_v2",
        display_name="2-5 km AGL updraft helicity",
        units="m^2/s^2",
        scale_type="fixed_continuous",
        minimum=0,
        maximum=2_000,
        breakpoints=[300, 800, 1_400],
        colors=["#ffffff", "#f6b27d", "#d9583f", "#7f1d1d"],
    )

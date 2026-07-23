"""FastAPI application skeleton for local Cloud Chamber services."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cloud_chamber.cli import ENGINE_NOTE
from cloud_chamber.cloud_worlds import (
    CloudWorldSummary,
    TradeCumulusWorldDetail,
    list_cloud_world_summaries,
    trade_cumulus_simulation_exists,
    trade_cumulus_world_detail,
)
from cloud_chamber.dry_run_package import (
    DryRunPackageError,
    generate_dry_run_package,
    read_dry_run_report,
)
from cloud_chamber.igra_catalog import (
    IGRACatalogError,
    cache_station_zip_from_catalog,
    read_igra_cache_manifest,
    read_igra_recent_catalog,
    refresh_recent_catalog,
)
from cloud_chamber.lan_worker import (
    LanWorkerApiError,
    cleanup_lan_worker_run,
    collect_lan_worker_run,
    lan_worker_config_status,
    lan_worker_run_status,
    start_lan_worker_run,
)
from cloud_chamber.local_run_manager import LocalRunManager, LocalRunManagerError, RunStatus
from cloud_chamber.local_run_queue import LocalRunQueueError, LocalRunQueueManager
from cloud_chamber.mountain_wave_terrain_visualization import (
    MountainWaveTerrainField,
    MountainWaveTerrainVisualizationError,
    mountain_waves_frame_from_native_outputs,
    preserved_mountain_wave_terrain_frame,
)
from cloud_chamber.mountain_waves_variations import (
    MountainWavesVariationError,
    MountainWavesVariationPackage,
    MountainWavesVariationPreview,
    MountainWavesVariationRequest,
    MountainWavesVariationTemplate,
    create_mountain_waves_variation,
    mountain_waves_variation_template,
    preflight_mountain_waves_variation,
    preview_mountain_waves_variation,
)
from cloud_chamber.mountain_waves_world import (
    MountainWavesWorldDetail,
    MountainWavesWorldSummary,
    mountain_waves_run_manifest,
    mountain_waves_simulation,
    mountain_waves_world_detail,
)
from cloud_chamber.observed_sounding import ObservedSoundingError, parse_igra_station_text
from cloud_chamber.result_cards import (
    ResultCardUpdate,
    get_result_card,
    list_result_cards,
    save_result_card,
    update_result_card,
)
from cloud_chamber.result_ingest import (
    ResultIngestError,
    ingest_completed_run,
)
from cloud_chamber.run_manifest import RunManifestError, load_run_manifest
from cloud_chamber.run_progress import run_progress_from_manifest
from cloud_chamber.runtime_integrity import assess_runtime_integrity
from cloud_chamber.runtime_storage import (
    RuntimeStorageError,
    delete_ingested_result,
    delete_runtime_run,
    runtime_storage_inventory,
)
from cloud_chamber.scenario_catalog import (
    load_scenario_template,
    load_scenario_templates,
    scenario_summary,
)
from cloud_chamber.selected_region_diagnostics import (
    RegionType,
    SelectedRegionError,
    SelectedRegionRequest,
    selected_region_diagnostics,
)
from cloud_chamber.settings import CloudChamberSettings, load_settings
from cloud_chamber.simulation_notes import (
    SimulationNoteError,
    SimulationNoteResponse,
    SimulationNoteUpdate,
    load_simulation_note,
    save_simulation_note,
)
from cloud_chamber.sounding_candidates import (
    CandidateHistoryScope,
    CandidateReadinessFilter,
    CandidateSortDirection,
    CandidateSortKey,
    CandidateStoryFamilyFilter,
    CandidateStoryFilter,
    CandidateSupportFilter,
    SaveCandidateRequest,
    TargetStoryId,
    UpdateSavedCandidateRequest,
    analyze_cached_soundings,
    delete_saved_candidate,
    list_saved_candidates,
    list_screening_inputs,
    save_candidate,
    screen_cached_soundings,
    update_saved_candidate,
)
from cloud_chamber.storm_examination import (
    DEFAULT_PRESENTATION_TIME_INDEX,
    StormExaminationError,
    preserved_storm_examination_frame,
    supercells_explore_frame,
)
from cloud_chamber.storm_examination import (
    LensId as StormExaminationLensId,
)
from cloud_chamber.storm_examination import (
    ViewportId as StormExaminationViewportId,
)
from cloud_chamber.supercells_world import (
    REFERENCE_SIMULATION_ID as SUPERCELLS_REFERENCE_SIMULATION_ID,
)
from cloud_chamber.supercells_world import (
    SupercellsWorldDetail,
    SupercellsWorldSummary,
    supercells_world_detail,
)
from cloud_chamber.trade_cumulus_comparison_story import (
    TradeCumulusComparisonStoryConflict,
    TradeCumulusComparisonStoryNotFound,
    trade_cumulus_moisture_comparison_story,
)
from cloud_chamber.trade_cumulus_updraft_lens import (
    LensOrientation,
    TradeCumulusUpdraftLensError,
    WindMode,
    trade_cumulus_updraft_lens_defaults,
    trade_cumulus_updraft_lens_frame,
)
from cloud_chamber.visualization_data import (
    ProfileAggregationMethod,
    TimeHeightAggregationMethod,
    TimeSeriesAggregationMethod,
    VisualizationDataError,
    VisualizationOrientation,
    field_catalog,
    field_slice,
    output_product_catalog,
    point_cloud,
    time_height_product,
    time_series_product,
    vertical_profile,
    view_defaults,
)

app = FastAPI(
    title="Cloud Chamber Backend",
    summary="Local backend API for Cloud Chamber CM1 experiment workflows.",
    version="0.1.0",
)

_local_run_manager: LocalRunManager | None = None
_local_run_queue: LocalRunQueueManager | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response that does not require CM1."""
    return {
        "status": "ok",
        "product": "Cloud Chamber",
        "engine_note": ENGINE_NOTE,
    }


class DryRunRequest(BaseModel):
    scenario_id: str = "baseline-shallow-cumulus"
    controls: dict[str, str | float | bool] = Field(default_factory=dict)
    run_configuration: dict[str, object] | None = None
    run_recipe: str | None = None
    observed_sounding: dict[str, object] | None = None
    candidate_screening: dict[str, object] | None = None
    user_name: str | None = None
    user_tags: list[str] = Field(default_factory=list)
    user_notes: str | None = None


class ObservedSoundingParseRequest(BaseModel):
    uploaded_filename: str
    text: str
    selected_time_utc: str | None = None


class LaunchRunRequest(BaseModel):
    manifest_path: str


class DeleteRunRequest(BaseModel):
    run_id: str
    dry_run: bool = True
    confirm: bool = False
    force_saved: bool = False


class DeleteResultRequest(BaseModel):
    confirm: bool = False


class IngestResultRequest(BaseModel):
    manifest_path: str


class LanWorkerRunRequest(BaseModel):
    manifest_path: str


class IGRACacheRequest(BaseModel):
    station_id: str
    filename: str | None = None


class IGRABatchCacheRequest(BaseModel):
    station_id: str | None = None
    station_ids: list[str] = Field(default_factory=list)
    limit: int = 10


class SoundingCandidateScreenRequest(BaseModel):
    station_id: str | None = None
    station_ids: list[str] = Field(default_factory=list)
    history_scope: CandidateHistoryScope = "latest_per_station"
    latest_per_station: int | None = 5
    limit: int = 50
    target_story: TargetStoryId | None = None


class SoundingCandidateAnalysisRequest(BaseModel):
    station_id: str | None = None
    station_ids: list[str] = Field(default_factory=list)
    history_scope: CandidateHistoryScope = "all_cached"
    latest_per_station: int | None = None
    limit: int = 50
    story_filter: CandidateStoryFilter = "all"
    story_family: CandidateStoryFamilyFilter = "all"
    support: CandidateSupportFilter = "all"
    readiness: CandidateReadinessFilter = "all"
    station_search: str = ""
    sort_by: CandidateSortKey = "best_match"
    sort_direction: CandidateSortDirection | None = None


@app.get("/api/scenarios")
def list_scenarios() -> dict[str, object]:
    scenarios = [scenario_summary(scenario) for scenario in load_scenario_templates()]
    return {
        "golden_path_scenario_id": "baseline-shallow-cumulus",
        "scenarios": scenarios,
    }


@app.post("/api/dry-run-package")
def create_dry_run_package(request: DryRunRequest) -> dict[str, Any]:
    scenario = load_scenario_template(request.scenario_id)
    settings = load_settings()
    try:
        result = generate_dry_run_package(
            scenario_data=scenario.model_dump(mode="json"),
            runtime_home=settings.runtime_home,
            run_id=f"dry-run-{uuid4().hex[:12]}",
            controls=request.controls,
            run_configuration=request.run_configuration,
            run_recipe=request.run_recipe,
            observed_sounding=request.observed_sounding,
            candidate_screening=request.candidate_screening,
            user_name=request.user_name,
            user_tags=request.user_tags,
            user_notes=request.user_notes,
        )
    except DryRunPackageError as exc:
        if exc.pre_run_validation_report is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(exc),
                    "pre_run_validation_report": exc.pre_run_validation_report,
                },
            ) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    report = read_dry_run_report(result.report_path)
    return {
        "package_dir": str(result.package_dir),
        "manifest_path": str(result.manifest_path),
        "report_path": str(result.report_path),
        "generated_files": [str(path) for path in result.generated_files],
        "report": report,
    }


@app.post("/api/observed-soundings/parse")
def parse_observed_sounding(request: ObservedSoundingParseRequest) -> dict[str, object]:
    try:
        selected_time = (
            datetime.fromisoformat(request.selected_time_utc.replace("Z", "+00:00"))
            if request.selected_time_utc
            else None
        )
        result = parse_igra_station_text(
            request.text,
            uploaded_filename=request.uploaded_filename,
            selected_time_utc=selected_time,
        )
    except ObservedSoundingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/igra/recent/catalog")
def get_igra_recent_catalog() -> dict[str, object]:
    catalog = read_igra_recent_catalog(load_settings())
    return {"catalog": catalog.model_dump(mode="json") if catalog else None}


@app.post("/api/igra/recent/refresh-catalog")
def refresh_igra_recent_catalog() -> dict[str, object]:
    try:
        catalog = refresh_recent_catalog(load_settings())
    except IGRACatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return catalog.model_dump(mode="json")


@app.get("/api/igra/recent/cache")
def get_igra_recent_cache() -> dict[str, object]:
    manifest = read_igra_cache_manifest(load_settings())
    return manifest.model_dump(mode="json")


@app.post("/api/igra/recent/cache")
def cache_igra_recent_file(request: IGRACacheRequest) -> dict[str, object]:
    try:
        entry = cache_station_zip_from_catalog(
            load_settings(),
            station_id=request.station_id,
            filename=request.filename,
        )
    except IGRACatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return entry.model_dump(mode="json")


@app.post("/api/igra/recent/cache-batch")
def cache_igra_recent_files(request: IGRABatchCacheRequest) -> dict[str, object]:
    if request.limit < 1 and not request.station_ids:
        raise HTTPException(status_code=400, detail="limit must be at least 1")
    settings = load_settings()
    catalog = read_igra_recent_catalog(settings)
    if catalog is None:
        raise HTTPException(
            status_code=400,
            detail="Refresh IGRA recent catalog before caching station files.",
        )
    selected_station_ids = [
        station.strip()
        for station in ([request.station_id] if request.station_id else []) + request.station_ids
        if station and station.strip()
    ]
    selected_station_set = set(selected_station_ids)
    uncached = [
        reference
        for reference in catalog.zip_references
        if reference.cached_status == "not_cached"
        and (not selected_station_set or reference.station_id in selected_station_set)
    ]
    if selected_station_set:
        station_order = {station: index for index, station in enumerate(selected_station_ids)}
        selected = sorted(
            uncached,
            key=lambda reference: (
                station_order.get(reference.station_id, len(station_order)),
                reference.filename,
            ),
        )
    else:
        selected = uncached[: request.limit]
    cached_entries: list[dict[str, object]] = []
    failed: list[dict[str, str]] = []
    for reference in selected:
        try:
            entry = cache_station_zip_from_catalog(
                settings,
                station_id=reference.station_id,
                filename=reference.filename,
            )
            cached_entries.append(entry.model_dump(mode="json"))
        except IGRACatalogError as exc:
            failed.append(
                {
                    "station_id": reference.station_id,
                    "filename": reference.filename,
                    "error": str(exc),
                }
            )
    return {
        "requested_limit": request.limit,
        "requested_station_ids": selected_station_ids,
        "selected_count": len(selected),
        "cached_entries": cached_entries,
        "failed": failed,
        "remaining_uncached_count": max(0, len(uncached) - len(cached_entries)),
    }


@app.get("/api/sounding-candidates/screening-inputs")
def get_sounding_candidate_screening_inputs() -> dict[str, object]:
    inputs = list_screening_inputs(load_settings())
    return {"inputs": [item.model_dump(mode="json") for item in inputs]}


@app.post("/api/sounding-candidates/screen")
def screen_sounding_candidates(request: SoundingCandidateScreenRequest) -> dict[str, object]:
    try:
        result = screen_cached_soundings(
            load_settings(),
            station_id=request.station_id,
            station_ids=request.station_ids,
            history_scope=request.history_scope,
            latest_per_station=request.latest_per_station,
            limit=request.limit,
            target_story=request.target_story,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/sounding-candidates/analyze")
def analyze_sounding_candidates(request: SoundingCandidateAnalysisRequest) -> dict[str, object]:
    try:
        result = analyze_cached_soundings(
            load_settings(),
            station_id=request.station_id,
            station_ids=request.station_ids,
            history_scope=request.history_scope,
            latest_per_station=request.latest_per_station,
            limit=request.limit,
            story_filter=request.story_filter,
            story_family=request.story_family,
            support=request.support,
            readiness=request.readiness,
            station_search=request.station_search,
            sort_by=request.sort_by,
            sort_direction=request.sort_direction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/sounding-candidates/saved")
def get_saved_sounding_candidates() -> dict[str, object]:
    try:
        saved = list_saved_candidates(load_settings())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"saved_candidates": [candidate.model_dump(mode="json") for candidate in saved]}


@app.post("/api/sounding-candidates/saved")
def create_saved_sounding_candidate(request: SaveCandidateRequest) -> dict[str, object]:
    try:
        saved = save_candidate(load_settings(), request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return saved.model_dump(mode="json")


@app.patch("/api/sounding-candidates/saved/{saved_candidate_id}")
def update_saved_sounding_candidate(
    saved_candidate_id: str, request: UpdateSavedCandidateRequest
) -> dict[str, object]:
    try:
        saved = update_saved_candidate(load_settings(), saved_candidate_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved sounding candidate not found")
    return saved.model_dump(mode="json")


@app.delete("/api/sounding-candidates/saved/{saved_candidate_id}")
def remove_saved_sounding_candidate(saved_candidate_id: str) -> dict[str, object]:
    try:
        deleted = delete_saved_candidate(load_settings(), saved_candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"saved_candidate_id": saved_candidate_id, "deleted": deleted}


@app.post("/api/runs/launch")
def launch_run(request: LaunchRunRequest) -> dict[str, object]:
    try:
        status = _get_local_run_manager().launch(Path(request.manifest_path).expanduser())
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.post("/api/runs/queue")
def enqueue_run(request: LaunchRunRequest) -> dict[str, object]:
    try:
        state = _get_local_run_queue().enqueue(Path(request.manifest_path).expanduser())
    except LocalRunQueueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return state.model_dump(mode="json")


@app.get("/api/runs/queue")
def run_queue_status() -> dict[str, object]:
    try:
        state = _get_local_run_queue().refresh()
    except LocalRunQueueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return state.model_dump(mode="json")


@app.get("/api/runs/status")
def run_status(manifest_path: str) -> dict[str, object]:
    try:
        status = _get_local_run_manager().status(Path(manifest_path).expanduser())
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.post("/api/runs/cancel")
def cancel_run() -> dict[str, object]:
    try:
        status = _get_local_run_manager().cancel()
    except LocalRunManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _run_status_payload(status)


@app.get("/api/lan-worker/config")
def get_lan_worker_config() -> dict[str, object]:
    return lan_worker_config_status()


@app.post("/api/lan-worker/start")
def start_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return start_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/lan-worker/status")
def get_lan_worker_status(manifest_path: str) -> dict[str, object]:
    try:
        return lan_worker_run_status(load_settings(), Path(manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lan-worker/collect")
def collect_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return collect_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lan-worker/cleanup")
def cleanup_lan_worker(request: LanWorkerRunRequest) -> dict[str, object]:
    try:
        return cleanup_lan_worker_run(load_settings(), Path(request.manifest_path).expanduser())
    except LanWorkerApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/storage/inventory")
def storage_inventory() -> dict[str, object]:
    inventory = runtime_storage_inventory(load_settings())
    return inventory.model_dump(mode="json")


@app.get(
    "/api/worlds",
    response_model=list[CloudWorldSummary | MountainWavesWorldSummary | SupercellsWorldSummary],
)
def list_worlds() -> list[CloudWorldSummary | MountainWavesWorldSummary | SupercellsWorldSummary]:
    try:
        return list_cloud_world_summaries(load_settings())
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=500, detail="Cloud World inventory is unavailable."
        ) from exc


@app.get("/api/worlds/trade-cumulus", response_model=TradeCumulusWorldDetail)
def get_trade_cumulus_world() -> TradeCumulusWorldDetail:
    try:
        return trade_cumulus_world_detail(load_settings())
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=500, detail="Trade Cumulus World data is unavailable."
        ) from exc


@app.get("/api/worlds/mountain-waves", response_model=MountainWavesWorldDetail)
def get_mountain_waves_world() -> MountainWavesWorldDetail:
    try:
        return mountain_waves_world_detail(load_settings())
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=500, detail="Mountain Waves World data is unavailable."
        ) from exc


@app.get("/api/worlds/supercells", response_model=SupercellsWorldDetail)
def get_supercells_world() -> SupercellsWorldDetail:
    return supercells_world_detail(load_settings())


@app.get(
    "/api/worlds/{world_id}/simulations/{simulation_id}/note",
    response_model=SimulationNoteResponse,
)
def get_simulation_note(world_id: str, simulation_id: str) -> SimulationNoteResponse:
    settings = load_settings()
    canonical_world_id = _canonical_note_world_id(world_id)
    if not _simulation_note_target_exists(
        canonical_world_id,
        simulation_id,
        settings=settings,
    ):
        raise HTTPException(status_code=404, detail="Cloud World Simulation not found.")
    try:
        note = load_simulation_note(
            settings,
            world_id=canonical_world_id,
            simulation_id=simulation_id,
        )
    except SimulationNoteError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SimulationNoteResponse(note=note)


@app.put(
    "/api/worlds/{world_id}/simulations/{simulation_id}/note",
    response_model=SimulationNoteResponse,
)
def put_simulation_note(
    world_id: str,
    simulation_id: str,
    request: SimulationNoteUpdate,
) -> SimulationNoteResponse:
    settings = load_settings()
    canonical_world_id = _canonical_note_world_id(world_id)
    if not _simulation_note_target_exists(
        canonical_world_id,
        simulation_id,
        settings=settings,
    ):
        raise HTTPException(status_code=404, detail="Cloud World Simulation not found.")
    try:
        note = save_simulation_note(
            settings,
            world_id=canonical_world_id,
            simulation_id=simulation_id,
            text=request.text,
        )
    except SimulationNoteError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SimulationNoteResponse(note=note)


@app.get(
    "/api/worlds/mountain-waves/variation-template",
    response_model=MountainWavesVariationTemplate,
)
def get_mountain_waves_variation_template(
    parent_simulation_id: str,
) -> MountainWavesVariationTemplate:
    try:
        return mountain_waves_variation_template(load_settings(), parent_simulation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (OSError, MountainWavesVariationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/api/worlds/mountain-waves/variations/preview",
    response_model=MountainWavesVariationPreview,
)
def preview_mountain_waves_variation_request(
    request: MountainWavesVariationRequest,
) -> MountainWavesVariationPreview:
    try:
        return preview_mountain_waves_variation(load_settings(), request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (OSError, MountainWavesVariationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/api/worlds/mountain-waves/variations",
    response_model=MountainWavesVariationPackage,
)
def package_mountain_waves_variation(
    request: MountainWavesVariationRequest,
) -> MountainWavesVariationPackage:
    try:
        return create_mountain_waves_variation(load_settings(), request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (OSError, MountainWavesVariationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/worlds/mountain-waves/variations/preflight")
def preflight_mountain_waves_variation_request(request: LaunchRunRequest) -> dict[str, Any]:
    try:
        return preflight_mountain_waves_variation(Path(request.manifest_path).expanduser())
    except (OSError, ValueError, MountainWavesVariationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/worlds/mountain-waves/simulations/{simulation_id}/frame")
def get_mountain_waves_simulation_frame(
    simulation_id: str,
    field: MountainWaveTerrainField = "w",
    time_index: int = 0,
) -> dict[str, Any]:
    try:
        record, manifest, _manifest_path = mountain_waves_run_manifest(
            load_settings(), simulation_id
        )
        if not record.inspectable:
            raise MountainWaveTerrainVisualizationError(
                f"Simulation {simulation_id} does not have inspectable completed output."
            )
        response = mountain_waves_frame_from_native_outputs(
            output_paths=[Path(value).expanduser() for value in manifest.outputs.netcdf_paths],
            namelist_path=Path(manifest.generated_inputs.namelist_input or "").expanduser(),
            field=field,
            time_index=time_index,
            run_id=manifest.run_id,
            case_label=record.display_name,
            implementation_commit=manifest.app.commit or "unknown",
            dry_case=not record.moist_fields_available,
            caveats=[*record.caveats, *record.warnings],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (OSError, MountainWaveTerrainVisualizationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return response.model_dump(mode="json")


@app.post("/api/storage/delete-run")
def delete_run(request: DeleteRunRequest) -> dict[str, object]:
    try:
        result = delete_runtime_run(
            load_settings(),
            run_id=request.run_id,
            dry_run=request.dry_run,
            confirm=request.confirm,
            force_saved=request.force_saved,
        )
    except RuntimeStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/ingest")
def ingest_result(request: IngestResultRequest) -> dict[str, object]:
    try:
        result = ingest_completed_run(Path(request.manifest_path).expanduser())
    except ResultIngestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results")
def list_results() -> dict[str, object]:
    return {
        "results": [card.model_dump(mode="json") for card in list_result_cards(load_settings())]
    }


@app.get("/api/comparisons/trade-cumulus-moisture-v1")
def get_trade_cumulus_moisture_comparison_story() -> dict[str, object]:
    try:
        story = trade_cumulus_moisture_comparison_story(load_settings())
    except TradeCumulusComparisonStoryNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TradeCumulusComparisonStoryConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return story.model_dump(mode="json")


@app.get("/api/results/{result_id}")
def get_result(result_id: str) -> dict[str, object]:
    try:
        result = get_result_card(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/{result_id}/delete-preview")
def preview_result_delete(result_id: str) -> dict[str, object]:
    try:
        result = delete_ingested_result(
            load_settings(),
            result_id=result_id,
            dry_run=True,
            confirm=False,
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/{result_id}/delete")
def delete_result(result_id: str, request: DeleteResultRequest) -> dict[str, object]:
    try:
        result = delete_ingested_result(
            load_settings(),
            result_id=result_id,
            dry_run=False,
            confirm=request.confirm,
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.patch("/api/results/{result_id}")
def patch_result(result_id: str, request: ResultCardUpdate) -> dict[str, object]:
    try:
        result = update_result_card(load_settings(), result_id, request)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/results/{result_id}/save")
def save_result(result_id: str) -> dict[str, object]:
    try:
        result = save_result_card(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/fields")
def get_visualization_fields(result_id: str) -> dict[str, object]:
    try:
        result = field_catalog(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/defaults")
def get_visualization_defaults(result_id: str, time_index: int | None = None) -> dict[str, object]:
    try:
        result = view_defaults(load_settings(), result_id, time_index=time_index)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/slice")
def get_visualization_slice(
    result_id: str,
    field: str,
    time_index: int = 0,
    orientation: str = "horizontal",
    level_index: int = 0,
    encoding: str = "json",
) -> dict[str, object]:
    if orientation not in {"horizontal", "vertical_x", "vertical_y"}:
        raise HTTPException(status_code=400, detail=f"Unsupported orientation: {orientation}")
    if encoding != "json":
        raise HTTPException(status_code=400, detail="Only encoding=json is supported.")
    checked_orientation = cast(VisualizationOrientation, orientation)
    try:
        result = field_slice(
            load_settings(),
            result_id,
            field=field,
            time_index=time_index,
            orientation=checked_orientation,
            level_index=level_index,
            encoding="json",
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/point-cloud")
def get_visualization_point_cloud(
    result_id: str,
    field: str = "qc",
    time_index: int = 0,
    threshold: float = 1e-6,
    max_points: int = 50_000,
    encoding: str = "json",
) -> dict[str, object]:
    if encoding != "json":
        raise HTTPException(status_code=400, detail="Only encoding=json is supported.")
    try:
        result = point_cloud(
            load_settings(),
            result_id,
            field=field,
            time_index=time_index,
            threshold=threshold,
            max_points=max_points,
            encoding="json",
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/visualization/trade-cumulus-updraft-lens/defaults")
def get_trade_cumulus_updraft_lens_defaults(result_id: str) -> dict[str, object]:
    try:
        result = trade_cumulus_updraft_lens_defaults(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TradeCumulusUpdraftLensError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/research/mountain-wave-terrain")
def get_mountain_wave_terrain_frame(
    field: MountainWaveTerrainField = "w",
    time_index: int = 0,
) -> dict[str, object]:
    try:
        result = preserved_mountain_wave_terrain_frame(
            load_settings(),
            field=field,
            time_index=time_index,
        )
    except MountainWaveTerrainVisualizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/worlds/supercells/simulations/{simulation_id}/frame")
def get_supercells_simulation_frame(
    simulation_id: str,
    lens: StormExaminationLensId = "rotating_updraft",
    time_index: int = DEFAULT_PRESENTATION_TIME_INDEX,
    viewport: StormExaminationViewportId = "storm",
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
) -> dict[str, object]:
    if simulation_id != SUPERCELLS_REFERENCE_SIMULATION_ID:
        raise HTTPException(status_code=404, detail="Supercell Simulation not found.")
    try:
        frame = supercells_explore_frame(
            load_settings(),
            lens=lens,
            time_index=time_index,
            viewport=viewport,
            x_index=x_index,
            y_index=y_index,
            z_index=z_index,
        )
    except StormExaminationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return frame.model_dump(mode="json")


@app.get("/api/research/storm-examination")
def get_storm_examination_frame(
    lens: StormExaminationLensId = "rotating_updraft",
    time_index: int = 5,
    viewport: StormExaminationViewportId = "storm",
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
) -> dict[str, object]:
    try:
        result = preserved_storm_examination_frame(
            load_settings(),
            lens=lens,
            time_index=time_index,
            viewport=viewport,
            x_index=x_index,
            y_index=y_index,
            z_index=z_index,
        )
    except StormExaminationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


def _canonical_note_world_id(world_id: str) -> str:
    aliases = {
        "trade-cumulus": "trade_cumulus",
        "trade_cumulus": "trade_cumulus",
        "mountain-waves": "mountain_waves",
        "mountain_waves": "mountain_waves",
        "supercells": "supercells",
    }
    canonical = aliases.get(world_id)
    if canonical is None:
        raise HTTPException(status_code=404, detail="Cloud World not found.")
    return canonical


def _simulation_note_target_exists(
    world_id: str,
    simulation_id: str,
    *,
    settings: CloudChamberSettings,
) -> bool:
    if world_id == "trade_cumulus":
        return trade_cumulus_simulation_exists(settings, simulation_id)
    if world_id == "mountain_waves":
        return mountain_waves_simulation(settings, simulation_id) is not None
    if world_id == "supercells":
        return simulation_id == SUPERCELLS_REFERENCE_SIMULATION_ID
    return False


@app.get("/api/results/{result_id}/visualization/trade-cumulus-updraft-lens/frame")
def get_trade_cumulus_updraft_lens_frame(
    result_id: str,
    time_index: int,
    plane_index: int,
    orientation: str = "vertical_x",
    wind_mode: str = "perturbation",
) -> dict[str, object]:
    if orientation not in {"horizontal", "vertical_x", "vertical_y"}:
        raise HTTPException(status_code=400, detail=f"Unsupported orientation: {orientation}")
    if wind_mode not in {"perturbation", "total"}:
        raise HTTPException(status_code=400, detail=f"Unsupported wind_mode: {wind_mode}")
    try:
        result = trade_cumulus_updraft_lens_frame(
            load_settings(),
            result_id,
            time_index=time_index,
            orientation=cast(LensOrientation, orientation),
            plane_index=plane_index,
            wind_mode=cast(WindMode, wind_mode),
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TradeCumulusUpdraftLensError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/output-products")
def get_output_product_catalog(result_id: str) -> dict[str, object]:
    try:
        result = output_product_catalog(load_settings(), result_id)
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/output-products/profile")
def get_output_product_profile(
    result_id: str,
    field: str,
    time_index: int = 0,
    aggregation_method: str = "domain_mean",
    x_index: int | None = None,
    y_index: int | None = None,
) -> dict[str, object]:
    if aggregation_method not in {"domain_mean", "domain_min", "domain_max", "selected_column"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported profile aggregation_method: {aggregation_method}",
        )
    try:
        result = vertical_profile(
            load_settings(),
            result_id,
            field=field,
            time_index=time_index,
            aggregation_method=cast(ProfileAggregationMethod, aggregation_method),
            x_index=x_index,
            y_index=y_index,
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/output-products/time-height")
def get_output_product_time_height(
    result_id: str,
    field: str,
    aggregation_method: str = "domain_mean",
    threshold: float | None = None,
) -> dict[str, object]:
    if aggregation_method not in {"cloud_fraction", "domain_mean", "domain_min", "domain_max"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported time-height aggregation_method: {aggregation_method}",
        )
    try:
        result = time_height_product(
            load_settings(),
            result_id,
            field=field,
            aggregation_method=cast(TimeHeightAggregationMethod, aggregation_method),
            threshold=threshold,
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/output-products/time-series")
def get_output_product_time_series(
    result_id: str,
    field: str,
    aggregation_method: str = "domain_max",
    threshold: float | None = None,
) -> dict[str, object]:
    if aggregation_method not in {"cloud_fraction", "domain_mean", "domain_min", "domain_max"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported time-series aggregation_method: {aggregation_method}",
        )
    try:
        result = time_series_product(
            load_settings(),
            result_id,
            field=field,
            aggregation_method=cast(TimeSeriesAggregationMethod, aggregation_method),
            threshold=threshold,
        )
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VisualizationDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/results/{result_id}/diagnostics/selected-region")
def get_selected_region_diagnostics(
    result_id: str,
    region_type: str,
    x_index: int | None = None,
    y_index: int | None = None,
    z_index: int | None = None,
    x_start: int | None = None,
    x_end: int | None = None,
    y_start: int | None = None,
    y_end: int | None = None,
    z_start: int | None = None,
    z_end: int | None = None,
    neighborhood: int = 0,
) -> dict[str, object]:
    if region_type not in {"point", "column", "box"}:
        raise HTTPException(status_code=400, detail=f"Unsupported region_type: {region_type}")
    checked_region_type = cast(RegionType, region_type)
    try:
        request = SelectedRegionRequest(
            region_type=checked_region_type,
            x_index=x_index,
            y_index=y_index,
            z_index=z_index,
            x_start=x_start,
            x_end=x_end,
            y_start=y_start,
            y_end=y_end,
            z_start=z_start,
            z_end=z_end,
            neighborhood=neighborhood,
        )
        result = selected_region_diagnostics(load_settings(), result_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ResultIngestError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SelectedRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


def _get_local_run_manager() -> LocalRunManager:
    global _local_run_manager
    if _local_run_manager is None:
        _local_run_manager = LocalRunManager(settings=load_settings())
    return _local_run_manager


def _get_local_run_queue() -> LocalRunQueueManager:
    global _local_run_queue
    if _local_run_queue is None:
        _local_run_queue = LocalRunQueueManager(
            settings=load_settings(),
            run_manager=_get_local_run_manager(),
        )
    return _local_run_queue


def _run_status_payload(status: RunStatus) -> dict[str, object]:
    try:
        manifest = load_run_manifest(status.manifest_path)
    except (OSError, RunManifestError):
        return {
            "run_id": status.run_id,
            "lifecycle_state": status.lifecycle_state.value,
            "product_state": None,
            "validation_status": None,
            "manifest_path": str(status.manifest_path),
            "command": list(status.command),
            "stdout_log": str(status.stdout_log),
            "stderr_log": str(status.stderr_log),
            "stdout_tail": _tail_text(status.stdout_log),
            "stderr_tail": _tail_text(status.stderr_log),
            "exit_code": status.exit_code,
            "started_at": None,
            "finished_at": None,
            "output_summary": {
                "raw_cm1_artifacts": 0,
                "netcdf_paths": 0,
                "processed_artifacts": 0,
            },
            "runtime_warnings": [],
            "runtime_integrity": None,
            "progress": None,
            "user": None,
            "observed_sounding": None,
            "candidate_screening": None,
            "run_recipe": None,
            "run_recipe_display_name": None,
            "recipe_id": None,
            "recipe_display_name": None,
            "assumption_set_id": None,
            "assumption_mode": None,
            "required_output_fields": [],
            "missing_required_output_fields": [],
            "input_source": None,
            "run_configuration": None,
            "pre_run_validation_report": None,
        }
    runtime_integrity = assess_runtime_integrity(
        lifecycle_state=manifest.lifecycle_state.value,
        exit_code=manifest.execution.exit_code,
        runtime_warnings=manifest.outputs.runtime_warnings,
        stdout_log=status.stdout_log if str(status.stdout_log) else None,
    )
    return {
        "run_id": status.run_id,
        "lifecycle_state": status.lifecycle_state.value,
        "product_state": manifest.provenance.product_state.value,
        "validation_status": manifest.validation_status.value,
        "manifest_path": str(status.manifest_path),
        "command": list(status.command),
        "stdout_log": str(status.stdout_log),
        "stderr_log": str(status.stderr_log),
        "stdout_tail": _tail_text(status.stdout_log),
        "stderr_tail": _tail_text(status.stderr_log),
        "exit_code": status.exit_code,
        "started_at": manifest.execution.started_at.isoformat()
        if manifest.execution.started_at
        else None,
        "finished_at": manifest.execution.finished_at.isoformat()
        if manifest.execution.finished_at
        else None,
        "output_summary": {
            "raw_cm1_artifacts": len(manifest.outputs.raw_cm1_artifacts),
            "netcdf_paths": len(manifest.outputs.netcdf_paths),
            "processed_artifacts": len(manifest.outputs.processed_artifacts),
        },
        "runtime_warnings": manifest.outputs.runtime_warnings,
        "runtime_integrity": runtime_integrity.model_dump(mode="json"),
        "progress": run_progress_from_manifest(manifest),
        "user": manifest.user.model_dump(mode="json"),
        "observed_sounding": manifest.observed_sounding,
        "candidate_screening": manifest.candidate_screening,
        "run_recipe": manifest.run_recipe,
        "run_recipe_display_name": manifest.run_recipe_display_name,
        "recipe_id": manifest.recipe_id,
        "recipe_display_name": manifest.recipe_display_name,
        "assumption_set_id": manifest.assumption_set_id,
        "assumption_mode": manifest.assumption_mode,
        "required_output_fields": manifest.required_output_fields,
        "missing_required_output_fields": manifest.missing_required_output_fields,
        "input_source": manifest.input_source,
        "run_configuration": manifest.run_configuration,
        "pre_run_validation_report": manifest.pre_run_validation_report,
    }


def _tail_text(path: Path, *, max_lines: int = 12) -> str | None:
    if not str(path):
        return None
    try:
        if not path.exists():
            return None
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return None
    return "\n".join(lines[-max_lines:]) if lines else ""

"""Result card / experiment notebook API models.

Result cards are a product-facing view over ingested result metadata. They keep
the completed CM1 result, ingested metadata, and notebook entry states distinct
while allowing user-editable name, tags, and notes to live beside the generated
run output under the local runtime home. Older cards may still include
saved/protected compatibility fields.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cloud_chamber.output_products import FieldDefaultTime, InterestingTimeRecord, ScienceSummary
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    CandidateHypothesisComparison,
    ResultIngestError,
    ResultMetadata,
    result_metadata_from_json,
)
from cloud_chamber.run_manifest import load_run_manifest
from cloud_chamber.settings import CloudChamberSettings

RESULT_CARD_FILENAME = "result_card.json"


class OutputFileSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    netcdf_count: int = 0
    model_output_count: int = 0
    stats_netcdf_count: int = 0
    raw_cm1_artifact_count: int = 0
    processed_artifact_count: int = 0
    visualization_ready_artifact_count: int = 0
    total_output_count: int = 0
    model_output_file_count: int = 0
    time_steps: int | None = None
    first_output_time_seconds: float | None = None
    last_output_time_seconds: float | None = None


class ResultCardState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    saved: bool = False
    protected: bool = False
    updated_at: datetime | None = None


class ResultCardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    saved: bool | None = None
    protected: bool | None = None


class ResultCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    run_id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    saved: bool = False
    protected: bool = False
    scenario_id: str
    scenario_name: str | None = None
    run_configuration: dict[str, object]
    physical_question: str
    controls: dict[str, str | float | bool] = Field(default_factory=dict)
    status: str
    source_lifecycle_state: str
    source_product_state: str
    source_model: str
    input_source: str = "generated_reference"
    input_source_label: str = "Generated reference"
    observed_sounding: dict[str, object] | None = None
    package_family: str | None = None
    package_display_name: str | None = None
    trigger_type: str | None = None
    trigger_parameters: dict[str, object] | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    package_caveats: list[str] = Field(default_factory=list)
    manual_validation_status: str | None = None
    candidate_screening: dict[str, object] | None = None
    pre_run_validation_report: dict[str, Any] | None = None
    candidate_hypothesis_comparison: CandidateHypothesisComparison | None = None
    provenance_labels: list[str] = Field(default_factory=list)
    diagnostics_summary: str | None = None
    thermal_fate_label: str | None = None
    thermal_fate_confidence: str | None = None
    main_limiting_factor: str | None = None
    first_cloud_time_seconds: float | None = None
    max_qc_kg_kg: float | None = None
    time_of_max_qc_seconds: float | None = None
    max_w_m_s: float | None = None
    time_of_max_w_seconds: float | None = None
    min_w_m_s: float | None = None
    time_of_min_w_seconds: float | None = None
    rain_present: bool | None = None
    first_rain_time_seconds: float | None = None
    surface_rain_present: bool | None = None
    max_surface_rain: float | None = None
    surface_rain_units: str | None = None
    max_dbz: float | None = None
    reflectivity_available: bool | None = None
    interesting_times: list[InterestingTimeRecord] = Field(default_factory=list)
    default_time_by_field: dict[str, FieldDefaultTime] = Field(default_factory=dict)
    science_summary: ScienceSummary | None = None
    interesting_time_caveats: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    output_file_summary: OutputFileSummary
    created_at: datetime
    completed_at: datetime | None = None
    ingested_at: datetime
    updated_at: datetime


def list_result_cards(settings: CloudChamberSettings) -> list[ResultCard]:
    """List result cards under the configured runtime home."""
    runs_dir = settings.runtime_home.expanduser() / "runs"
    if not runs_dir.exists():
        return []
    cards: list[ResultCard] = []
    for metadata_path in sorted(runs_dir.glob(f"*/{RESULT_METADATA_FILENAME}")):
        try:
            cards.append(_card_from_metadata_path(metadata_path))
        except (OSError, ValueError, ResultIngestError):
            continue
    return cards


def get_result_card(settings: CloudChamberSettings, result_id: str) -> ResultCard:
    for card in list_result_cards(settings):
        if card.result_id == result_id:
            return card
    raise ResultIngestError(f"Result card not found: {result_id}")


def update_result_card(
    settings: CloudChamberSettings,
    result_id: str,
    update: ResultCardUpdate,
) -> ResultCard:
    metadata_path = _metadata_path_for_result(settings, result_id)
    state_path = metadata_path.parent / RESULT_CARD_FILENAME
    state = _read_card_state(state_path)
    update_data = update.model_dump(exclude_unset=True)
    if "protected" in update_data and update_data["protected"] is True:
        update_data["saved"] = True
    state = state.model_copy(update={**update_data, "updated_at": datetime.now(UTC)})
    _write_card_state(state_path, state)
    return _card_from_metadata_path(metadata_path)


def save_result_card(settings: CloudChamberSettings, result_id: str) -> ResultCard:
    return update_result_card(
        settings,
        result_id,
        ResultCardUpdate(saved=True, protected=True),
    )


def _metadata_path_for_result(settings: CloudChamberSettings, result_id: str) -> Path:
    runs_dir = settings.runtime_home.expanduser() / "runs"
    for metadata_path in sorted(runs_dir.glob(f"*/{RESULT_METADATA_FILENAME}")):
        try:
            metadata = result_metadata_from_json(metadata_path.read_text())
        except (OSError, ValueError):
            continue
        if metadata.result_id == result_id:
            return metadata_path
    raise ResultIngestError(f"Result card not found: {result_id}")


def _card_from_metadata_path(metadata_path: Path) -> ResultCard:
    metadata = result_metadata_from_json(metadata_path.read_text())
    state = _read_card_state(metadata_path.parent / RESULT_CARD_FILENAME)
    completed_at = _completed_at(metadata_path.parent / "run_manifest.json")
    return _card_from_metadata(metadata, state, completed_at)


def _card_from_metadata(
    metadata: ResultMetadata,
    state: ResultCardState,
    completed_at: datetime | None,
) -> ResultCard:
    diagnostics = metadata.diagnostics
    process_diagnostics = metadata.process_diagnostics
    interpretation = process_diagnostics.interpretation_support if process_diagnostics else None
    cloud = diagnostics.cloud if diagnostics else None
    vertical_velocity = diagnostics.vertical_velocity if diagnostics else None
    rain = diagnostics.rain if diagnostics else None
    surface_rain = diagnostics.surface_rain if diagnostics else None
    reflectivity = diagnostics.reflectivity if diagnostics else None
    name = state.name or _default_result_card_name(metadata)
    scenario_name = _display_scenario_name(metadata)
    caveats = list(metadata.warnings)
    if diagnostics:
        caveats.extend(diagnostics.caveats)
    return ResultCard(
        result_id=metadata.result_id,
        run_id=metadata.run_id,
        name=name,
        tags=state.tags,
        notes=state.notes,
        saved=state.saved,
        protected=state.protected or state.saved,
        scenario_id=metadata.scenario_id,
        scenario_name=scenario_name,
        run_configuration=metadata.run_configuration,
        physical_question=metadata.physical_question,
        controls=metadata.controls,
        status=metadata.result_state if not state.saved else "saved_result_notebook_entry",
        source_lifecycle_state=metadata.source_lifecycle_state,
        source_product_state=metadata.source_product_state,
        source_model=metadata.source_model,
        input_source=metadata.input_source,
        input_source_label=metadata.input_source_label,
        observed_sounding=metadata.observed_sounding,
        package_family=metadata.package_family,
        package_display_name=metadata.package_display_name,
        trigger_type=metadata.trigger_type,
        trigger_parameters=metadata.trigger_parameters,
        expected_outputs=metadata.expected_outputs,
        package_caveats=metadata.package_caveats,
        manual_validation_status=metadata.manual_validation_status,
        candidate_screening=metadata.candidate_screening,
        pre_run_validation_report=metadata.pre_run_validation_report,
        candidate_hypothesis_comparison=metadata.candidate_hypothesis_comparison,
        provenance_labels=[
            f"source_model:{metadata.source_model}",
            f"source_product_state:{metadata.source_product_state}",
            f"result_state:{metadata.result_state}",
            *([f"package_family:{metadata.package_family}"] if metadata.package_family else []),
        ],
        diagnostics_summary=metadata.diagnostics_summary,
        thermal_fate_label=interpretation.thermal_fate_label if interpretation else None,
        thermal_fate_confidence=interpretation.confidence if interpretation else None,
        main_limiting_factor=interpretation.main_limiting_factor if interpretation else None,
        first_cloud_time_seconds=cloud.first_cloud_time_seconds if cloud else None,
        max_qc_kg_kg=cloud.max_qc_kg_kg if cloud else None,
        time_of_max_qc_seconds=cloud.time_of_max_qc_seconds if cloud else None,
        max_w_m_s=vertical_velocity.max_w_m_s if vertical_velocity else None,
        time_of_max_w_seconds=vertical_velocity.time_of_max_w_seconds
        if vertical_velocity
        else None,
        min_w_m_s=vertical_velocity.min_w_m_s if vertical_velocity else None,
        time_of_min_w_seconds=vertical_velocity.time_of_min_w_seconds
        if vertical_velocity
        else None,
        rain_present=rain.present if rain else None,
        first_rain_time_seconds=rain.first_rain_time_seconds if rain else None,
        surface_rain_present=surface_rain.present if surface_rain else None,
        max_surface_rain=surface_rain.max_surface_rain if surface_rain else None,
        surface_rain_units=surface_rain.units if surface_rain else None,
        max_dbz=reflectivity.max_dbz if reflectivity else None,
        reflectivity_available=reflectivity.available if reflectivity else None,
        interesting_times=metadata.interesting_times,
        default_time_by_field=metadata.default_time_by_field,
        science_summary=metadata.science_summary,
        interesting_time_caveats=metadata.interesting_time_caveats,
        caveats=_dedupe(caveats),
        output_file_summary=_output_file_summary(metadata),
        created_at=metadata.created_at,
        completed_at=completed_at,
        ingested_at=metadata.created_at,
        updated_at=state.updated_at or metadata.updated_at,
    )


def _default_result_card_name(metadata: ResultMetadata) -> str:
    if metadata.package_family == "deep_convection_trial":
        station_name = _observed_sounding_value(metadata.observed_sounding, "station_name")
        station_id = _observed_sounding_value(metadata.observed_sounding, "station_id")
        if station_name:
            return f"Deep Convection Trial — {station_name}"
        if station_id:
            return f"Deep Convection Trial — {station_id}"
        return "Deep Convection Trial"
    if metadata.input_source == "observed_sounding":
        station_name = _observed_sounding_value(metadata.observed_sounding, "station_name")
        station_id = _observed_sounding_value(metadata.observed_sounding, "station_id")
        if station_name:
            return f"Uploaded Sounding — {station_name}"
        if station_id:
            return f"Uploaded Sounding — {station_id}"
        return "Uploaded Sounding"
    return metadata.scenario_name or metadata.scenario_id


def _display_scenario_name(metadata: ResultMetadata) -> str | None:
    if metadata.package_family == "deep_convection_trial" and metadata.package_display_name:
        return metadata.package_display_name
    if metadata.input_source == "observed_sounding":
        return "Uploaded Sounding"
    return metadata.scenario_name


def _observed_sounding_value(observed_sounding: dict[str, object] | None, key: str) -> str | None:
    if not observed_sounding:
        return None
    value = observed_sounding.get(key)
    return value if isinstance(value, str) and value else None


def _output_file_summary(metadata: ResultMetadata) -> OutputFileSummary:
    total = (
        len(metadata.netcdf_paths)
        + len(metadata.raw_cm1_artifacts)
        + len(metadata.processed_artifacts)
        + len(metadata.visualization_ready_artifacts)
    )
    return OutputFileSummary(
        netcdf_count=len(metadata.netcdf_paths),
        model_output_count=len(metadata.model_output_paths),
        stats_netcdf_count=len(metadata.stats_netcdf_paths),
        raw_cm1_artifact_count=len(metadata.raw_cm1_artifacts),
        processed_artifact_count=len(metadata.processed_artifacts),
        visualization_ready_artifact_count=len(metadata.visualization_ready_artifacts),
        total_output_count=total,
        model_output_file_count=metadata.model_output_file_count,
        time_steps=metadata.time_steps,
        first_output_time_seconds=metadata.first_output_time_seconds,
        last_output_time_seconds=metadata.last_output_time_seconds,
    )


def _completed_at(manifest_path: Path) -> datetime | None:
    if not manifest_path.exists():
        return None
    try:
        return load_run_manifest(manifest_path).execution.finished_at
    except (OSError, ValueError):
        return None


def _read_card_state(path: Path) -> ResultCardState:
    if not path.exists():
        return ResultCardState()
    loaded = json.loads(path.read_text())
    return ResultCardState.model_validate(loaded)


def _write_card_state(path: Path, state: ResultCardState) -> None:
    path.write_text(state.model_dump_json(indent=2) + "\n")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))

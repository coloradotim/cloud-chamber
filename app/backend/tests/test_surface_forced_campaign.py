from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.output_products import ScienceSummary
from cloud_chamber.result_diagnostics import (
    CloudDiagnostics,
    FieldFrameQualityRecord,
    FieldFrameQualitySummary,
    FieldQuality,
    LowLevelResponseDiagnostics,
    LowLevelResponseFieldDiagnostics,
    RainDiagnostics,
    ReflectivityDiagnostics,
    ResultDiagnostics,
    SurfaceFluxDiagnostics,
    SurfaceFluxFieldDiagnostics,
    SurfaceRainDiagnostics,
    TimeDiagnostics,
    TimeValue,
    VerticalVelocityDiagnostics,
)
from cloud_chamber.result_ingest import RESULT_METADATA_FILENAME, FieldMetadata, ResultMetadata
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.runtime_integrity import assess_runtime_integrity
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.surface_forced_campaign import (
    CampaignError,
    build_campaign_plan,
    ingest_campaign,
    package_campaign,
    plan_campaign,
    queue_campaign,
    report_campaign,
    status_campaign,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def write_matrix(
    tmp_path: Path,
    *,
    queue_target: str = "local",
    include_followups: bool = False,
    include_comparison: bool = False,
) -> Path:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "valley.txt").write_text(IGRA_FIXTURE)
    matrix: dict[str, Any] = {
        "schema_version": "surface_forced_campaign_matrix_v1",
        "campaign": {
            "campaign_id": "surface_forced_test",
            "title": "Surface forced test",
            "objective": "Verify campaign runner plumbing.",
            "protocol": "docs/research/surface-forced-sounding-verification-protocol.md",
            "commit_report_path": str(tmp_path / "reports" / "surface_forced_test.md"),
        },
        "execution": {"queue_target": queue_target, "resume_existing": True},
        "selection_sets": [
            {
                "selection_id": "control_sounding",
                "role": "forcing_path_smoke_check",
                "source": {
                    "type": "uploaded_or_local_igra",
                    "local_text_path": "fixtures/valley.txt",
                    "selected_valid_time_utc": "2025-01-02T00:00:00Z",
                },
                "selection_notes": "Tiny test IGRA fixture.",
                "candidate_screening": {
                    "candidate_id": "fixture-candidate",
                    "primary_story": "humid_rainy_candidate",
                    "primary_story_label": "Humid / rainy candidate",
                    "story_family": "lower_atmosphere",
                    "rank_score": 72.0,
                    "evidence": [{"label": "low-level moisture", "value": "high"}],
                    "caveats": ["fixture_screening"],
                },
            }
        ],
        "run_defaults": {
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "surface_heat_flux_k_m_s": 8.0e-3,
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "queue_target": queue_target,
            "tags": ["campaign-test"],
            "notes": "Campaign default note.",
        },
        "forcing_sets": [
            {
                "forcing_id": "stronger_flux",
                "surface_heat_flux_k_m_s": 4.0e-2,
                "surface_moisture_flux_g_g_m_s": 1.0e-4,
            }
        ],
        "comparison_types": [
            {
                "comparison_type": "forcing_sensitivity_same_duration",
                "varied_fields": ["surface_heat_flux_k_m_s"],
                "required_equal_fields": ["duration"],
                "required_available_fields": ["hfx", "qfx", "qv", "qc", "w"],
                "required_diagnostic_support": ["surface_fluxes", "low_level_response"],
            }
        ],
        "runs": [
            {
                "matrix_id": "phase1_control_high_flux",
                "phase": "forcing_path_smoke_check",
                "selection_id": "control_sounding",
                "forcing_id": "stronger_flux",
                "comparison_role": "phase1_control",
            }
        ],
        "required_summary_fields": {"metadata": ["campaign_id"], "evidence": ["hfx_present"]},
    }
    if include_followups:
        matrix["runs"].extend(
            [
                {
                    "matrix_id": "phase2_followup",
                    "phase": "easy_sounding_response_check",
                    "selection_id": "control_sounding",
                    "forcing_id": "stronger_flux",
                },
                {
                    "matrix_id": "phase2_optional_120km",
                    "phase": "easy_sounding_response_check",
                    "optional": True,
                    "selection_id": "control_sounding",
                    "forcing_id": "stronger_flux",
                    "domain_size": "regional_120km",
                },
            ]
        )
    if include_comparison:
        matrix["runs"].append(
            {
                "matrix_id": "phase1_experiment_high_flux",
                "phase": "forcing_path_smoke_check",
                "selection_id": "control_sounding",
                "forcing_id": "stronger_flux",
                "surface_heat_flux_k_m_s": 5.0e-2,
                "comparison": {
                    "type": "forcing_sensitivity_same_duration",
                    "control_matrix_id": "phase1_control_high_flux",
                },
            }
        )
    matrix_path = tmp_path / "campaign.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))
    return matrix_path


def write_phase1_surface_flux_matrix(tmp_path: Path) -> Path:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["comparison_types"] = [
        {
            "comparison_type": "heat_flux_sensitivity",
            "varied_fields": ["surface_heat_flux_k_m_s", "cm1_cnst_shflx"],
            "required_equal_fields": [
                "selection_id",
                "surface_moisture_flux_g_g_m_s",
                "duration",
                "domain_size",
                "horizontal_cell_count",
                "output_cadence",
                "required_output_fields",
            ],
            "required_available_fields": ["hfx", "qfx"],
            "required_diagnostic_support": ["surface_fluxes"],
        },
        {
            "comparison_type": "moisture_flux_sensitivity",
            "varied_fields": ["surface_moisture_flux_g_g_m_s", "cm1_cnst_lhflx"],
            "required_equal_fields": [
                "selection_id",
                "surface_heat_flux_k_m_s",
                "duration",
                "domain_size",
                "horizontal_cell_count",
                "output_cadence",
                "required_output_fields",
            ],
            "required_available_fields": ["hfx", "qfx"],
            "required_diagnostic_support": ["surface_fluxes"],
        },
        {
            "comparison_type": "combined_flux_sensitivity",
            "varied_fields": [
                "surface_heat_flux_k_m_s",
                "surface_moisture_flux_g_g_m_s",
                "cm1_cnst_shflx",
                "cm1_cnst_lhflx",
            ],
            "required_equal_fields": [
                "selection_id",
                "duration",
                "domain_size",
                "horizontal_cell_count",
                "output_cadence",
                "required_output_fields",
            ],
            "required_available_fields": ["hfx", "qfx"],
            "required_diagnostic_support": ["surface_fluxes"],
        },
    ]
    matrix["phase1_required_comparison_types"] = [
        "heat_flux_sensitivity",
        "moisture_flux_sensitivity",
        "combined_flux_sensitivity",
    ]
    matrix["runs"] = [
        {
            "matrix_id": "phase1_control_default_flux",
            "phase": "forcing_path_smoke_check",
            "selection_id": "control_sounding",
            "comparison_role": "phase1_control",
        },
        {
            "matrix_id": "phase1_control_high_sensible",
            "phase": "forcing_path_smoke_check",
            "selection_id": "control_sounding",
            "surface_heat_flux_k_m_s": 4.0e-2,
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "comparison": {
                "type": "heat_flux_sensitivity",
                "control_matrix_id": "phase1_control_default_flux",
            },
            "comparison_role": "heat_flux_sensitivity",
        },
        {
            "matrix_id": "phase1_control_high_moisture",
            "phase": "forcing_path_smoke_check",
            "selection_id": "control_sounding",
            "surface_heat_flux_k_m_s": 8.0e-3,
            "surface_moisture_flux_g_g_m_s": 1.0e-4,
            "comparison": {
                "type": "moisture_flux_sensitivity",
                "control_matrix_id": "phase1_control_default_flux",
            },
            "comparison_role": "moisture_flux_sensitivity",
        },
        {
            "matrix_id": "phase1_control_high_both",
            "phase": "forcing_path_smoke_check",
            "selection_id": "control_sounding",
            "surface_heat_flux_k_m_s": 4.0e-2,
            "surface_moisture_flux_g_g_m_s": 1.0e-4,
            "comparison": {
                "type": "combined_flux_sensitivity",
                "control_matrix_id": "phase1_control_default_flux",
            },
            "comparison_role": "combined_flux_sensitivity",
        },
    ]
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))
    return matrix_path


def test_campaign_plan_validates_matrix_and_resolves_cm1_values(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    plan = build_campaign_plan(yaml.safe_load(matrix_path.read_text()), matrix_path=matrix_path)

    assert plan.campaign_id == "surface_forced_test"
    assert plan.run_count == 1
    run = plan.runs[0]
    assert run.matrix_id == "phase1_control_high_flux"
    assert run.queue_target == "local"
    assert run.run_configuration["surface_heat_flux_k_m_s"] == 4.0e-2
    assert run.run_configuration["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert run.surface_flux_cm1_values["cnst_shflx"] == 4.0e-2
    assert run.surface_flux_cm1_values["cnst_lhflx"] == 1.0e-4
    assert run.cm1_values["nx"] == 128
    assert run.cm1_values["domain_x_km"] == 12.8
    assert "campaign:surface_forced_test" in run.tags
    assert run.stable_resume_identity


def test_campaign_plan_preserves_explicit_timestep_target(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["run_defaults"]["time_step_seconds"] = 1.0
    matrix["comparison_types"][0]["required_equal_fields"].append("time_step_seconds")
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))

    plan = build_campaign_plan(yaml.safe_load(matrix_path.read_text()), matrix_path=matrix_path)
    run = plan.runs[0]

    assert run.run_configuration["time_step_seconds"] == 1.0
    assert run.cm1_values["time_step_seconds"] == 1.0
    assert run.resolved_run_configuration["cm1_values"]["time_step_seconds"] == 1.0
    assert "dtl_1p000e00s" in run.resolved_run_configuration["configuration_id"]


def test_campaign_plans_checked_in_example_matrix() -> None:
    plan = plan_campaign(
        REPO_ROOT / "docs/research/templates/surface-forced-campaign-matrix.example.yaml"
    )

    assert plan.campaign_id == "surface_forced_smoke_001"
    assert plan.run_count == 10
    assert plan.execution["max_concurrent_runs"] == 1
    assert "forcing_sensitivity_same_duration" in plan.comparison_types
    assert plan.phase1_required_comparison_types == [
        "heat_flux_sensitivity",
        "moisture_flux_sensitivity",
        "combined_flux_sensitivity",
    ]
    assert any(run.optional for run in plan.runs)
    assert plan.required_summary_fields["evidence"]


def test_campaign_plan_blocks_machine_private_absolute_igra_paths(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["selection_sets"][0]["source"]["local_text_path"] = str(tmp_path / "valley.txt")

    try:
        build_campaign_plan(matrix, matrix_path=matrix_path)
    except CampaignError as exc:
        assert "absolute" in str(exc)
    else:
        raise AssertionError("absolute local path should be blocked by default")


def test_campaign_plan_rejects_unknown_required_summary_field(tmp_path: Path) -> None:
    matrix_path = write_matrix(tmp_path)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["required_summary_fields"]["evidence"].append("not_a_real_summary_field")

    with pytest.raises(CampaignError, match="Unsupported required_summary_fields"):
        build_campaign_plan(matrix, matrix_path=matrix_path)


def test_campaign_package_creates_observed_surface_forced_package_and_resumes(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)

    first = package_campaign(matrix_path, settings=settings, resume=True)
    second = package_campaign(matrix_path, settings=settings, resume=True)

    assert first.runs[0].status == "packaged"
    assert second.runs[0].message == "Resumed existing package."
    assert len(list((settings.runtime_home / "runs").iterdir())) == 1
    manifest = load_run_manifest(Path(first.runs[0].manifest_path or ""))
    assert manifest.run_recipe == "observed_surface_forced_evolution"
    assert manifest.observed_sounding is not None
    assert manifest.observed_sounding["station_id"] == "USM00072558"
    assert manifest.candidate_screening is not None
    assert manifest.candidate_screening["primary_story"] == "humid_rainy_candidate"
    assert manifest.run_configuration["surface_heat_flux_k_m_s"] == 4.0e-2
    assert manifest.run_configuration["surface_moisture_flux_g_g_m_s"] == 1.0e-4
    assert "campaign:surface_forced_test" in manifest.user.tags
    assert "Campaign default note." in (manifest.user.notes or "")


def test_campaign_queue_uses_existing_local_queue_path(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    enqueued: list[Path] = []

    class FakeQueue:
        def enqueue(self, manifest_path: Path) -> SimpleNamespace:
            enqueued.append(manifest_path)
            entry = SimpleNamespace(
                manifest_path=str(manifest_path),
                state="queued",
                message="Queued by fake local queue.",
                error=None,
                result_id=None,
            )
            return SimpleNamespace(entries=[entry])

    def fake_queue_factory(_settings: CloudChamberSettings) -> Any:
        return FakeQueue()

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=fake_queue_factory,
    )

    assert result.runs[0].status == "queued"
    assert result.runs[0].run_status == "queued"
    assert result.runs[0].message == "Queued by fake local queue."
    assert enqueued == [Path(result.runs[0].manifest_path or "")]


def test_campaign_queue_rejects_unknown_matrix_id(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)

    with pytest.raises(CampaignError, match="Unknown matrix_id"):
        queue_campaign(
            matrix_path,
            settings=settings,
            selected_matrix_ids={"missing-row"},
        )


def test_campaign_queue_blocks_followups_and_excludes_optional_by_default(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_followups=True)
    enqueued: list[str] = []

    class FakeQueue:
        def enqueue(self, manifest_path: Path) -> SimpleNamespace:
            enqueued.append(manifest_path.name)
            entry = SimpleNamespace(
                manifest_path=str(manifest_path),
                state="queued",
                message="Queued by fake local queue.",
                error=None,
                result_id=None,
            )
            return SimpleNamespace(entries=[entry])

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=lambda _settings: FakeQueue(),
    )
    runs = {run.matrix_id: run for run in result.runs}

    assert len(enqueued) == 1
    assert runs["phase1_control_high_flux"].status == "queued"
    assert runs["phase2_followup"].status == "blocked"
    assert runs["phase2_optional_120km"].status == "planned"

    override = queue_campaign(
        matrix_path,
        settings=settings,
        selected_matrix_ids={"phase2_followup"},
        override_phase_gate=True,
        override_reason="manual smoke evidence reviewed",
        local_queue_factory=lambda _settings: FakeQueue(),
    )
    followup = next(run for run in override.runs if run.matrix_id == "phase2_followup")
    assert followup.status == "queued"
    assert followup.gate_override is not None
    assert followup.gate_override["reason"] == "manual smoke evidence reviewed"


@pytest.mark.parametrize(
    ("lifecycle", "product_state", "expected_status"),
    [
        (
            LifecycleState.QUEUED,
            ProductState.QUEUED_RUNNING_CM1_PROCESS,
            "queued",
        ),
        (
            LifecycleState.RUNNING,
            ProductState.QUEUED_RUNNING_CM1_PROCESS,
            "running",
        ),
        (
            LifecycleState.COMPLETED,
            ProductState.COMPLETED_CM1_RESULT,
            "completed_not_ingested",
        ),
        (
            LifecycleState.INGESTED,
            ProductState.INGESTED_RESULT_METADATA,
            "ingested",
        ),
        (
            LifecycleState.FAILED,
            ProductState.FAILED_CANCELED_CM1_RUN,
            "run_failed",
        ),
        (
            LifecycleState.CANCELED,
            ProductState.FAILED_CANCELED_CM1_RUN,
            "run_canceled",
        ),
    ],
)
def test_campaign_queue_is_idempotent_for_existing_lifecycle_states(
    tmp_path: Path,
    lifecycle: LifecycleState,
    product_state: ProductState,
    expected_status: str,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _set_manifest_lifecycle(manifest_path, lifecycle, product_state)
    if lifecycle == LifecycleState.RUNNING:
        manifest = load_run_manifest(manifest_path)
        write_run_manifest(
            manifest_path,
            manifest.model_copy(
                update={
                    "execution": manifest.execution.model_copy(update={"process_id": os.getpid()})
                }
            ),
        )

    class FailingQueue:
        def enqueue(self, _manifest_path: Path) -> SimpleNamespace:
            raise AssertionError("queue should not be called for existing lifecycle state")

    result = queue_campaign(
        matrix_path,
        settings=settings,
        local_queue_factory=lambda _settings: FailingQueue(),
    )

    assert result.runs[0].status == expected_status
    assert "Skipped queue" in (result.runs[0].message or "")


def test_campaign_status_reconciles_stale_running_manifest_before_queue_state(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.RUNNING,
                "provenance": ProvenanceMetadata(
                    product_state=ProductState.QUEUED_RUNNING_CM1_PROCESS
                ),
                "execution": manifest.execution.model_copy(update={"process_id": 987654321}),
            }
        ),
    )
    queue_path = settings.runtime_home / "run-queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "running",
                        "queued_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        "finished_at": None,
                        "result_id": None,
                        "message": "Stale queue entry still claims running.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "run_failed"
    manifest = load_run_manifest(manifest_path)
    assert manifest.lifecycle_state == LifecycleState.FAILED
    assert (
        "Tracked CM1 process 987654321 is no longer running"
        in (manifest.outputs.runtime_warnings[0])
    )


def test_campaign_status_reports_queued_entry_for_packaged_manifest(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    queue_path = settings.runtime_home / "run-queue.json"
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "queued",
                        "queued_at": now,
                        "updated_at": now,
                        "started_at": None,
                        "finished_at": None,
                        "result_id": None,
                        "message": "Queued behind another local run.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "queued"
    assert status.runs[0].run_status == "queued"
    assert status.runs[0].message == "Queued behind another local run."


def test_campaign_status_prefers_ingested_result_over_stale_queue_message(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(manifest_path)
    queue_path = settings.runtime_home / "run-queue.json"
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "entries": [
                    {
                        "run_id": packaged.runs[0].run_id,
                        "manifest_path": str(manifest_path),
                        "state": "running",
                        "queued_at": now,
                        "updated_at": now,
                        "started_at": now,
                        "finished_at": None,
                        "result_id": None,
                        "message": "CM1 is running; waiting for terminal status.",
                        "error": None,
                        "cleanup_status": None,
                    }
                ],
            }
        )
        + "\n"
    )

    status = status_campaign(matrix_path, settings=settings)

    assert status.runs[0].status == "ingested"
    assert status.runs[0].message == "Completed CM1 output ingested."


def test_campaign_lan_queue_status_collect_and_ingest_flow(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from cloud_chamber import surface_forced_campaign

    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, queue_target="lan")
    started: list[Path] = []

    def fake_start(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        started.append(manifest_path)
        return {"state": "running", "message": "LAN worker started"}

    def fake_running(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        return {"state": "running", "message": "LAN worker still running"}

    def fake_complete(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        return {"state": "ready_for_local_ingest", "message": "LAN output is ready"}

    def fake_collect(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        netcdf_path = manifest_path.parent / "cm1out_000001.nc"
        netcdf_path.write_text("fake netcdf placeholder")
        _set_manifest_lifecycle(
            manifest_path,
            LifecycleState.COMPLETED,
            ProductState.COMPLETED_CM1_RESULT,
            netcdf_path=netcdf_path,
        )
        return {"state": "ready_for_local_ingest", "message": "LAN output collected"}

    queued = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=fake_start,
        lan_status=fake_running,
    )
    assert queued.runs[0].status == "running"
    assert len(started) == 1

    def duplicate_start(_settings: CloudChamberSettings, _manifest_path: Path) -> dict[str, object]:
        raise AssertionError("LAN start should not run twice")

    repeated = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=duplicate_start,
        lan_status=fake_running,
    )
    assert repeated.runs[0].status == "running"
    assert len(started) == 1

    running = status_campaign(matrix_path, settings=settings, lan_status=fake_running)
    assert running.runs[0].status == "running"

    not_ready = ingest_campaign(matrix_path, settings=settings, lan_status=fake_running)
    assert not_ready.runs[0].status == "running"
    assert not_ready.runs[0].ingest_status == "not_started"

    complete = status_campaign(matrix_path, settings=settings, lan_status=fake_complete)
    assert complete.runs[0].status == "completed_not_ingested"

    monkeypatch.setattr(
        surface_forced_campaign,
        "ingest_completed_run",
        lambda _manifest_path: SimpleNamespace(result_id="result-lan-campaign"),
    )
    ingested = ingest_campaign(
        matrix_path,
        settings=settings,
        lan_status=fake_complete,
        lan_collect=fake_collect,
    )

    assert ingested.runs[0].status == "ingested"
    assert ingested.runs[0].result_id == "result-lan-campaign"


def test_campaign_lan_queue_enforces_max_concurrent_runs(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, queue_target="lan", include_comparison=True)
    started: list[Path] = []

    def fake_start(_settings: CloudChamberSettings, manifest_path: Path) -> dict[str, object]:
        started.append(manifest_path)
        return {"state": "running", "message": "LAN worker started"}

    result = queue_campaign(
        matrix_path,
        settings=settings,
        lan_start=fake_start,
    )
    runs = {run.matrix_id: run for run in result.runs}

    assert len(started) == 1
    assert runs["phase1_control_high_flux"].status == "running"
    assert runs["phase1_experiment_high_flux"].status == "blocked"
    assert "max_concurrent_runs=1" in (runs["phase1_experiment_high_flux"].message or "")


def test_campaign_report_summarizes_ingested_result_without_fabricating_bl_response(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(manifest_path)

    report_path = tmp_path / "report.md"
    summary_path = tmp_path / "summary.json"
    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=report_path,
        summary_json_path=summary_path,
    )

    summary = artifacts.summary
    assert Path(artifacts.markdown_path) == report_path
    assert Path(artifacts.summary_json_path) == summary_path
    assert summary["status_counts"] == {"ingested": 1}
    assert summary["phase_gate_state"] == "surface_flux_response_inconclusive_missing_evidence"
    assert summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_missing_evidence"
    )
    run = summary["runs"][0]
    assert run["hfx_present"] is True
    assert run["hfx_units"] == "K m/s"
    assert run["hfx_min"] == 2.0
    assert run["hfx_max"] == 2.0
    assert run["hfx_mean"] == 2.0
    assert run["hfx_finite_count"] == 8
    assert run["hfx_non_finite_count"] == 0
    assert run["hfx_total_count"] == 8
    assert run["qfx_present"] is True
    assert run["surface_moisture_flux_output_field"] == "qfx"
    assert run["qfx_units"] == "kg/m^2/s"
    assert run["qfx_min"] == 2.0e-5
    assert run["qfx_max"] == 2.0e-5
    assert run["qfx_mean"] == 2.0e-5
    assert run["qfx_finite_count"] == 8
    assert run["qfx_non_finite_count"] == 0
    assert run["qfx_total_count"] == 8
    assert run["lhfx_present"] is True
    assert run["diagnostic_support"]["surface_fluxes"] == "available"
    assert run["low_level_qv_response"] == (
        "unavailable:qv_low_level_response_unavailable_in_fixture"
    )
    assert run["low_level_qv_response_method"] == (
        "unavailable:qv_low_level_response_unavailable_in_fixture"
    )
    assert "low_level_qv_response" in summary["unavailable_diagnostics"]
    assert "max w 2.5" in report_path.read_text()


def test_campaign_report_verifies_matched_phase1_surface_flux_response(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.5e-5),
            "phase1_control_high_moisture": (2.2, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == "surface_flux_response_verified"
    assert artifacts.summary["phase_gate_state"] == (
        "forcing_wiring_verified_but_response_not_verified"
    )
    evaluations = artifacts.summary["surface_flux_response"]["evaluations"]
    assert {evaluation["status"] for evaluation in evaluations} == {
        "surface_flux_response_verified"
    }
    heat = next(
        evaluation
        for evaluation in evaluations
        if evaluation["comparison_type"] == "heat_flux_sensitivity"
    )
    assert heat["expectations"] == [
        {
            "field": "hfx",
            "selected_control_field": "surface_heat_flux_k_m_s",
            "expected": "increase",
            "observed": "increase",
            "required": True,
            "status": "verified",
            "control_selected": 0.008,
            "experiment_selected": 0.04,
            "control_mean": 2.0,
            "experiment_mean": 4.0,
            "units": "K m/s",
        },
        {
            "field": "qfx",
            "selected_control_field": "surface_moisture_flux_g_g_m_s",
            "expected": "comparable",
            "observed": "increase",
            "required": False,
            "status": "informational",
            "control_selected": 5.2e-05,
            "experiment_selected": 5.2e-05,
            "control_mean": 2.0e-05,
            "experiment_mean": 2.5e-05,
            "units": "kg/m^2/s",
        },
    ]
    moisture = next(
        evaluation
        for evaluation in evaluations
        if evaluation["comparison_type"] == "moisture_flux_sensitivity"
    )
    assert moisture["expectations"][0]["required"] is False
    assert moisture["expectations"][0]["status"] == "informational"
    assert moisture["expectations"][1]["required"] is True
    assert moisture["expectations"][1]["status"] == "verified"
    report = Path(artifacts.markdown_path).read_text()
    assert "Surface flux response: `surface_flux_response_verified`" in report
    assert "qfx: informational; expected `comparable`, observed `increase`" in report
    assert "`phase1_control_high_sensible` vs `phase1_control_default_flux`" in report


def test_campaign_report_verifies_matched_phase1_low_level_response(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.5e-5),
            "phase1_control_high_moisture": (2.2, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        low_level_deltas={
            "phase1_control_default_flux": (0.001, 1.0),
            "phase1_control_high_sensible": (0.0012, 3.0),
            "phase1_control_high_moisture": (0.004, 1.1),
            "phase1_control_high_both": (0.004, 3.2),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == "surface_flux_response_verified"
    assert artifacts.summary["low_level_response"]["state"] == "low_level_response_verified"
    assert artifacts.summary["phase_gate_state"] == "forcing_path_verified_for_campaign"
    run = next(
        row
        for row in artifacts.summary["runs"]
        if row["matrix_id"] == "phase1_control_high_moisture"
    )
    assert run["low_level_qv_response"] == pytest.approx(0.004)
    assert run["low_level_qv_early_response_delta"] == pytest.approx(0.004)
    assert run["low_level_qv_response_method"] == (
        "0_1km_thickness_weighted_domain_mean_early_30_90min"
    )
    assert run["low_level_qv_full_run_delta"] == pytest.approx(0.004)
    assert run["low_level_theta_or_temperature_response"] == pytest.approx(1.1)
    assert run["low_level_theta_or_temperature_early_response_delta"] == pytest.approx(1.1)

    moisture = next(
        evaluation
        for evaluation in artifacts.summary["low_level_response"]["evaluations"]
        if evaluation["comparison_type"] == "moisture_flux_sensitivity"
    )
    assert moisture["expectations"][0]["required"] is False
    assert moisture["expectations"][1]["required"] is True
    assert moisture["expectations"][1]["field"] == "low_level_qv_early_response_delta"
    assert moisture["expectations"][1]["status"] == "verified"
    report = Path(artifacts.markdown_path).read_text()
    assert "## Low-Level Response" in report
    assert (
        "low_level_qv_early_response_delta: required; expected `increase`, observed `increase`"
    ) in report


def test_campaign_gate_uses_early_response_not_full_run_delta(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.5e-5),
            "phase1_control_high_moisture": (2.2, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        low_level_deltas={
            "phase1_control_default_flux": (0.001, 1.0),
            "phase1_control_high_sensible": (0.0012, 3.0),
            "phase1_control_high_moisture": (0.004, 1.1),
            "phase1_control_high_both": (0.004, 3.2),
        },
        low_level_full_run_deltas={
            "phase1_control_default_flux": (0.003, 3.0),
            "phase1_control_high_sensible": (0.001, 2.0),
            "phase1_control_high_moisture": (0.002, 1.0),
            "phase1_control_high_both": (0.002, 2.0),
        },
    )

    assert artifacts.summary["low_level_response"]["state"] == "low_level_response_verified"
    assert artifacts.summary["phase_gate_state"] == "forcing_path_verified_for_campaign"
    high_moisture = next(
        row
        for row in artifacts.summary["runs"]
        if row["matrix_id"] == "phase1_control_high_moisture"
    )
    assert high_moisture["low_level_qv_early_response_delta"] == pytest.approx(0.004)
    assert high_moisture["low_level_qv_full_run_delta"] == pytest.approx(0.002)


def test_campaign_gate_blocks_when_early_response_missing_even_with_full_run_delta(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.5e-5),
            "phase1_control_high_moisture": (2.2, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        low_level_full_run_deltas={
            "phase1_control_default_flux": (0.001, 1.0),
            "phase1_control_high_sensible": (0.0012, 3.0),
            "phase1_control_high_moisture": (0.004, 1.1),
            "phase1_control_high_both": (0.004, 3.2),
        },
    )

    assert artifacts.summary["low_level_response"]["state"] == (
        "low_level_response_inconclusive_missing_evidence"
    )
    assert artifacts.summary["phase_gate_state"] == (
        "forcing_wiring_verified_but_response_not_verified"
    )
    high_moisture = next(
        row
        for row in artifacts.summary["runs"]
        if row["matrix_id"] == "phase1_control_high_moisture"
    )
    assert high_moisture["low_level_qv_early_response_available"] is False
    assert high_moisture["low_level_qv_full_run_response_available"] is True
    assert high_moisture["low_level_qv_early_response_delta"] == (
        "unavailable:low_level_early_response_unavailable"
    )
    assert high_moisture["low_level_qv_full_run_delta"] == pytest.approx(0.004)


def test_campaign_gate_blocks_caveated_early_response_below_finite_threshold(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.5e-5),
            "phase1_control_high_moisture": (2.2, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        low_level_deltas={
            "phase1_control_default_flux": (0.001, 1.0),
            "phase1_control_high_sensible": (0.0012, 3.0),
            "phase1_control_high_moisture": (0.004, 1.1),
            "phase1_control_high_both": (0.004, 3.2),
        },
        low_level_qv_early_end_counts={
            "phase1_control_high_moisture": (7, 8),
        },
    )

    assert artifacts.summary["low_level_response"]["state"] == (
        "low_level_response_inconclusive_missing_evidence"
    )
    moisture = next(
        evaluation
        for evaluation in artifacts.summary["low_level_response"]["evaluations"]
        if evaluation["comparison_type"] == "moisture_flux_sensitivity"
    )
    assert any(
        "experiment:low_level_qv_early_response_delta_finite_fraction_below_threshold" in item
        for item in moisture["unavailable_evidence"]
    )
    high_moisture = next(
        row
        for row in artifacts.summary["runs"]
        if row["matrix_id"] == "phase1_control_high_moisture"
    )
    assert high_moisture["low_level_qv_early_response_quality_state"] == (
        "caveated_below_minimum_finite_fraction"
    )


def test_campaign_report_blocks_phase_gate_when_low_level_response_not_verified(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        low_level_deltas={
            "phase1_control_default_flux": (0.001, 1.0),
            "phase1_control_high_sensible": (0.001, 3.0),
            "phase1_control_high_moisture": (0.001, 1.0),
            "phase1_control_high_both": (0.004, 3.2),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == "surface_flux_response_verified"
    assert artifacts.summary["low_level_response"]["state"] == "low_level_response_not_verified"
    assert artifacts.summary["phase_gate_state"] == (
        "forcing_wiring_verified_but_response_not_verified"
    )
    moisture = next(
        evaluation
        for evaluation in artifacts.summary["low_level_response"]["evaluations"]
        if evaluation["comparison_type"] == "moisture_flux_sensitivity"
    )
    assert moisture["expectations"][1]["expected"] == "increase"
    assert moisture["expectations"][1]["observed"] == "comparable"
    assert moisture["expectations"][1]["status"] == "not_verified"


def test_campaign_report_requires_complete_phase1_surface_flux_response_matrix(
    tmp_path: Path,
) -> None:
    def mutate(matrix: dict[str, Any]) -> None:
        matrix["runs"] = [
            run
            for run in matrix["runs"]
            if run["matrix_id"] in {"phase1_control_default_flux", "phase1_control_high_sensible"}
        ]

    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
        },
        mutate_matrix=mutate,
    )

    response = artifacts.summary["surface_flux_response"]
    assert response["state"] == "surface_flux_response_inconclusive_missing_evidence"
    assert response["missing_required_comparison_types"] == [
        "moisture_flux_sensitivity",
        "combined_flux_sensitivity",
    ]
    assert response["unavailable_evidence"] == [
        "missing_phase1_required_comparison_type:moisture_flux_sensitivity",
        "missing_phase1_required_comparison_type:combined_flux_sensitivity",
    ]
    assert artifacts.summary["phase_gate_state"] == (
        "surface_flux_response_inconclusive_missing_evidence"
    )


def test_campaign_report_rejects_unchanged_emitted_flux_response(
    tmp_path: Path,
) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (2.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 2.0e-5),
            "phase1_control_high_both": (2.0, 2.0e-5),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_not_verified"
    )
    assert artifacts.summary["phase_gate_state"] == "surface_flux_response_not_verified"
    expectations = artifacts.summary["surface_flux_response"]["evaluations"][0]["expectations"]
    assert expectations[0]["expected"] == "increase"
    assert expectations[0]["observed"] == "comparable"
    assert expectations[0]["status"] == "not_verified"


def test_campaign_report_rejects_reversed_emitted_flux_response(tmp_path: Path) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (1.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 1.0e-5),
            "phase1_control_high_both": (1.0, 1.0e-5),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_not_verified"
    )
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert heat["expectations"][0]["expected"] == "increase"
    assert heat["expectations"][0]["observed"] == "decrease"


def test_campaign_report_requires_trusted_surface_flux_stats(tmp_path: Path) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        non_finite_counts={"phase1_control_high_sensible": (1, 0)},
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_missing_evidence"
    )
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert "experiment:hfx_stats_not_trusted_non_finite" in heat["unavailable_evidence"]


def test_campaign_report_blocks_initial_surface_flux_frame_contamination_without_policy(
    tmp_path: Path,
) -> None:
    initial_frame = _fake_frame_quality(
        frame_index=0,
        time_seconds=0.0,
        position="initial",
    )
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        non_finite_counts={"phase1_control_default_flux": (8, 8)},
        frame_quality_overrides={
            "phase1_control_default_flux": (initial_frame, initial_frame),
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_missing_evidence"
    )
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert "control:hfx_initial_output_frame_entirely_non_finite" in heat["unavailable_evidence"]
    assert "control:qfx_initial_output_frame_entirely_non_finite" in heat["unavailable_evidence"]
    control = next(
        run
        for run in artifacts.summary["runs"]
        if run["matrix_id"] == "phase1_control_default_flux"
    )
    assert control["hfx_frame_quality"]["initial_frame_affected"] is True
    assert control["hfx_frame_quality"]["terminal_frame_affected"] is False


def test_campaign_report_blocks_terminal_surface_flux_frame_contamination(
    tmp_path: Path,
) -> None:
    terminal_frame = _fake_frame_quality(
        frame_index=24,
        time_seconds=21600.0,
        position="terminal",
        total_frame_count=25,
        finite_frame_count=24,
    )
    terminal_field_overrides = {
        "qc": _fake_field_quality("qc", "qc", non_finite_count=8, frame_quality=terminal_frame),
        "qr": _fake_field_quality("qr", "qr", non_finite_count=8, frame_quality=terminal_frame),
        "surface_rain": _fake_field_quality(
            "surface_rain", "rain", non_finite_count=8, frame_quality=terminal_frame
        ),
    }
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        non_finite_counts={"phase1_control_default_flux": (8, 8)},
        frame_quality_overrides={
            "phase1_control_default_flux": (terminal_frame, terminal_frame),
        },
        field_quality_overrides_by_run={
            "phase1_control_default_flux": terminal_field_overrides,
        },
        warnings_by_run={
            "phase1_control_default_flux": [
                "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG "
                "IEEE_DIVIDE_BY_ZERO IEEE_OVERFLOW_FLAG IEEE_UNDERFLOW_FLAG"
            ]
        },
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_missing_evidence"
    )
    assert artifacts.summary["phase_gate_state"] == "runtime_integrity_failed"
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert "control:hfx_terminal_output_frame_entirely_non_finite" in heat["unavailable_evidence"]
    assert "control:qfx_terminal_output_frame_entirely_non_finite" in heat["unavailable_evidence"]
    control = next(
        run
        for run in artifacts.summary["runs"]
        if run["matrix_id"] == "phase1_control_default_flux"
    )
    assert control["terminal_output_contamination"] is True
    assert control["terminal_output_contamination_fields"] == [
        "hfx",
        "qc",
        "qfx",
        "qr",
        "surface_rain",
    ]
    assert control["diagnostic_trust"]["qc"] == "untrusted_terminal_non_finite_frame"
    assert control["runtime_integrity_state"] == "failed"
    assert (
        "runtime_integrity_failed_fatal_floating_point_flags"
        in (control["runtime_integrity_caveats"])
    )
    assert (
        "runtime_integrity_failed_terminal_output_frame_entirely_non_finite"
        in (control["runtime_integrity_caveats"])
    )
    report = Path(artifacts.markdown_path).read_text()
    assert "Terminal field contamination" in report
    assert "Runtime floating-point warnings" in report
    assert "Runtime integrity: `failed`" in report
    assert "normal CM1 process exit does not make the resulting science output trusted" in report
    assert "runtime_integrity_failed_terminal_output_frame_entirely_non_finite" in report
    assert "control:hfx_terminal_output_frame_entirely_non_finite" in report
    assert "21600 s" in report
    assert "Cloud-top summaries use the coherent cloud-object top" in report
    assert "hfx_field_entirely_non_finite" not in report


def test_campaign_report_rejects_mismatched_surface_flux_units(tmp_path: Path) -> None:
    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        unit_overrides={"phase1_control_high_sensible": ("W m-2", "kg/m^2/s")},
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_noncomparable"
    )
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert "hfx:noncomparable_units:K m/s:vs:W m-2" in heat["unavailable_evidence"]


def test_campaign_report_rejects_structurally_noncomparable_surface_flux_runs(
    tmp_path: Path,
) -> None:
    def mutate(matrix: dict[str, Any]) -> None:
        for run in matrix["runs"]:
            if run["matrix_id"] == "phase1_control_high_sensible":
                run["domain_size"] = "local_6km"

    artifacts = _report_phase1_surface_flux_matrix(
        tmp_path,
        flux_means={
            "phase1_control_default_flux": (2.0, 2.0e-5),
            "phase1_control_high_sensible": (4.0, 2.0e-5),
            "phase1_control_high_moisture": (2.0, 4.0e-5),
            "phase1_control_high_both": (4.0, 4.0e-5),
        },
        mutate_matrix=mutate,
    )

    assert artifacts.summary["surface_flux_response"]["state"] == (
        "surface_flux_response_inconclusive_noncomparable"
    )
    heat = artifacts.summary["surface_flux_response"]["evaluations"][0]
    assert {"field": "domain_size", "control": "wide_12km", "experiment": "local_6km"} in (
        heat["equality_gate_failures"]
    )


def test_campaign_report_marks_non_finite_outcomes_as_untrusted(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    _write_fake_result_metadata(
        manifest_path,
        surface_rain_present=True,
        run_caveats=[
            "non_finite_values_detected_in_qc",
            "qc_field_entirely_non_finite",
            "non_finite_values_detected_in_w",
            "non_finite_values_detected_in_qr",
            "qr_field_entirely_non_finite",
            "non_finite_values_detected_in_surface_rain",
            "surface_rain_field_entirely_non_finite",
        ],
    )

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    run = artifacts.summary["runs"][0]
    assert run["diagnostic_trust"]["qc"] == "untrusted_entirely_non_finite"
    assert run["diagnostic_trust"]["w"] == "caveated_non_finite_values_detected"
    assert run["diagnostic_trust"]["qr"] == "untrusted_entirely_non_finite"
    assert run["diagnostic_trust"]["surface_rain"] == "untrusted_entirely_non_finite"
    assert run["surface_rain_present"] == (
        "unavailable:untrusted_surface_rain_field_entirely_non_finite"
    )
    assert "surface_rain_field_entirely_non_finite" in run["diagnostic_quality_warnings"]

    report = Path(artifacts.markdown_path).read_text()
    assert "surface rain unavailable (untrusted)" in report
    assert "max w 2.5 (caveated)" in report
    assert "Diagnostic trust: `qc untrusted" in report
    assert "Field-quality warnings: `" in report
    assert "surface rain `True`" not in report


def test_campaign_report_treats_stale_lhfx_requirement_as_qfx_alias(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(update={"required_output_fields": ["hfx", "lhfx", "qv", "qc", "w"]}),
    )
    _write_fake_result_metadata(
        manifest_path,
        missing_required_output_fields=["lhfx"],
        warnings=["Recipe required output fields missing from NetCDF metadata: lhfx"],
    )

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    run = artifacts.summary["runs"][0]
    assert run["required_output_fields"] == ["hfx", "qfx", "qv", "qc", "w"]
    assert run["missing_output_fields"] == []
    assert run["warnings"] == []
    assert "missing_output_field:qfx" not in artifacts.summary["unavailable_diagnostics"]
    assert "missing_output_field:lhfx" not in artifacts.summary["unavailable_diagnostics"]
    report = Path(artifacts.markdown_path).read_text()
    assert "lhfx" not in report
    assert "Required/missing fields: `hfx, qfx, qv, qc, w` / `none`" in report


def test_campaign_report_normalizes_stale_lhfx_comparison_evidence(
    tmp_path: Path,
) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_comparison=True)
    matrix = yaml.safe_load(matrix_path.read_text())
    matrix["comparison_types"][0]["required_available_fields"] = ["hfx", "lhfx"]
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    assert artifacts.summary["runs"][0]["diagnostic_trust"] == {
        "qc": "unavailable_until_result_ingested",
        "w": "unavailable_until_result_ingested",
        "qr": "unavailable_until_result_ingested",
        "surface_rain": "unavailable_until_result_ingested",
        "dbz": "unavailable_until_result_ingested",
    }
    unavailable_evidence = artifacts.summary["comparisons"][0]["unavailable_evidence"]
    assert "control:missing_required_field:qfx" in unavailable_evidence
    assert "control:missing_required_field:lhfx" not in unavailable_evidence
    assert (
        "missing_output_field:unavailable:until_result_ingested"
        not in artifacts.summary["unavailable_diagnostics"]
    )
    report = Path(artifacts.markdown_path).read_text()
    assert "missing_required_field:qfx" in report
    assert "missing_required_field:lhfx" not in report


def test_campaign_report_evaluates_comparison_contract(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path, include_comparison=True)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    for state_run in packaged.runs:
        _write_fake_result_metadata(Path(state_run.manifest_path or ""))

    artifacts = report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )

    comparisons = artifacts.summary["comparisons"]
    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison["comparison_type"] == "forcing_sensitivity_same_duration"
    assert comparison["control_matrix_id"] == "phase1_control_high_flux"
    assert comparison["experiment_matrix_id"] == "phase1_experiment_high_flux"
    assert comparison["status"] == "inconclusive_missing_evidence"
    assert comparison["equality_gate_failures"] == []
    assert "control:diagnostic_unavailable:low_level_response" in comparison["unavailable_evidence"]
    assert {
        "field": "surface_heat_flux_k_m_s",
        "control": 0.04,
        "experiment": 0.05,
    } in comparison["supported_differences"]
    assert "## Matched Comparisons" in Path(artifacts.markdown_path).read_text()


def test_campaign_ingest_updates_state_with_existing_completed_output(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from cloud_chamber import surface_forced_campaign

    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    manifest_path = Path(packaged.runs[0].manifest_path or "")
    manifest = load_run_manifest(manifest_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    netcdf_path.write_text("fake netcdf placeholder")
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
            }
        ),
    )

    monkeypatch.setattr(
        surface_forced_campaign,
        "ingest_completed_run",
        lambda _manifest_path: SimpleNamespace(result_id="result-surface-forced-test"),
    )

    result = surface_forced_campaign.ingest_campaign(matrix_path, settings=settings)

    assert result.runs[0].status == "ingested"
    assert result.runs[0].ingest_status == "ingested"
    assert result.runs[0].result_id == "result-surface-forced-test"


def _report_phase1_surface_flux_matrix(
    tmp_path: Path,
    *,
    flux_means: dict[str, tuple[float, float]],
    low_level_deltas: dict[str, tuple[float, float]] | None = None,
    low_level_full_run_deltas: dict[str, tuple[float, float]] | None = None,
    low_level_qv_early_end_counts: dict[str, tuple[int, int]] | None = None,
    non_finite_counts: dict[str, tuple[int, int]] | None = None,
    frame_quality_overrides: dict[
        str, tuple[FieldFrameQualitySummary | None, FieldFrameQualitySummary | None]
    ]
    | None = None,
    field_quality_overrides_by_run: dict[str, dict[str, FieldQuality]] | None = None,
    warnings_by_run: dict[str, list[str]] | None = None,
    unit_overrides: dict[str, tuple[str, str]] | None = None,
    mutate_matrix: Any | None = None,
) -> Any:
    settings = fake_settings(tmp_path)
    matrix_path = write_phase1_surface_flux_matrix(tmp_path)
    if mutate_matrix is not None:
        matrix = yaml.safe_load(matrix_path.read_text())
        mutate_matrix(matrix)
        matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False))
    packaged = package_campaign(matrix_path, settings=settings, resume=True)
    for state_run in packaged.runs:
        hfx_mean, qfx_mean = flux_means[state_run.matrix_id]
        hfx_non_finite, qfx_non_finite = (non_finite_counts or {}).get(
            state_run.matrix_id,
            (0, 0),
        )
        hfx_units, qfx_units = (unit_overrides or {}).get(
            state_run.matrix_id,
            ("K m/s", "kg/m^2/s"),
        )
        hfx_frame_quality, qfx_frame_quality = (frame_quality_overrides or {}).get(
            state_run.matrix_id,
            (None, None),
        )
        qv_early_end_finite, qv_early_end_total = (low_level_qv_early_end_counts or {}).get(
            state_run.matrix_id, (8, 8)
        )
        _write_fake_result_metadata(
            Path(state_run.manifest_path or ""),
            hfx_mean=hfx_mean,
            qfx_mean=qfx_mean,
            low_level_qv_delta=(
                low_level_deltas[state_run.matrix_id][0] if low_level_deltas is not None else None
            ),
            low_level_theta_delta=(
                low_level_deltas[state_run.matrix_id][1] if low_level_deltas is not None else None
            ),
            low_level_qv_full_run_delta=(
                low_level_full_run_deltas[state_run.matrix_id][0]
                if low_level_full_run_deltas is not None
                else None
            ),
            low_level_qv_early_end_finite_count=qv_early_end_finite,
            low_level_qv_early_end_total_count=qv_early_end_total,
            low_level_theta_full_run_delta=(
                low_level_full_run_deltas[state_run.matrix_id][1]
                if low_level_full_run_deltas is not None
                else None
            ),
            hfx_units=hfx_units,
            qfx_units=qfx_units,
            hfx_non_finite_count=hfx_non_finite,
            qfx_non_finite_count=qfx_non_finite,
            hfx_frame_quality=hfx_frame_quality,
            qfx_frame_quality=qfx_frame_quality,
            field_quality_overrides=(field_quality_overrides_by_run or {}).get(state_run.matrix_id),
            warnings=(warnings_by_run or {}).get(state_run.matrix_id),
        )

    return report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=tmp_path / "summary.json",
    )


def _set_manifest_lifecycle(
    manifest_path: Path,
    lifecycle: LifecycleState,
    product_state: ProductState,
    *,
    netcdf_path: Path | None = None,
) -> None:
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": lifecycle,
                "provenance": ProvenanceMetadata(product_state=product_state),
                "outputs": OutputMetadata(
                    netcdf_paths=[str(netcdf_path)] if netcdf_path is not None else []
                ),
            }
        ),
    )


def _fake_low_level_response_field(
    *,
    source_field: str,
    delta: float | None,
    full_run_delta: float | None = None,
    units: str,
    early_end_finite_count: int = 8,
    early_end_total_count: int = 8,
) -> LowLevelResponseFieldDiagnostics:
    if delta is None and full_run_delta is None:
        return LowLevelResponseFieldDiagnostics(
            source_field=source_field,
            available=False,
            early_response_available=False,
            full_run_response_available=False,
            field_absent=False,
            units=units,
            caveats=[f"{source_field}_low_level_response_unavailable_in_fixture"],
        )
    first_mean = 0.010 if source_field == "qv" else 300.0
    full_delta = delta if full_run_delta is None else full_run_delta
    early_mean = first_mean + delta if delta is not None else None
    final_mean = first_mean + full_delta if full_delta is not None else None
    early_available = delta is not None
    full_available = full_run_delta is not None or (delta is not None and full_delta is not None)
    return LowLevelResponseFieldDiagnostics(
        source_field=source_field,
        available=early_available,
        early_response_available=early_available,
        full_run_response_available=full_available,
        field_absent=False,
        layer_bottom_m=0.0,
        layer_top_m=1000.0,
        vertical_coordinate_name="z",
        vertical_coordinate_units="m",
        vertical_coordinate_method="0_1km_thickness_weighted_domain_mean_early_30_90min",
        time_dimension="time",
        first_time_index=0,
        final_time_index=2,
        first_time_seconds=0.0,
        final_time_seconds=21600.0,
        first_mean_value=first_mean,
        final_mean_value=final_mean,
        delta_value=delta,
        early_response_start_time_index=0 if early_available else None,
        early_response_end_time_index=1 if early_available else None,
        early_response_start_time_seconds=0.0 if early_available else None,
        early_response_end_time_seconds=3600.0 if early_available else None,
        early_response_start_mean_value=first_mean if early_available else None,
        early_response_end_mean_value=early_mean if early_available else None,
        early_response_delta=delta,
        early_response_start_finite_count=8 if early_available else 0,
        early_response_start_non_finite_count=0,
        early_response_start_total_count=8 if early_available else 0,
        early_response_end_finite_count=early_end_finite_count if early_available else 0,
        early_response_end_non_finite_count=(
            max(early_end_total_count - early_end_finite_count, 0) if early_available else 0
        ),
        early_response_end_total_count=early_end_total_count if early_available else 0,
        full_run_delta=full_delta if full_available else None,
        units=units,
        first_finite_count=8,
        first_non_finite_count=0,
        first_total_count=8,
        final_finite_count=8,
        final_non_finite_count=0,
        final_total_count=8,
    )


def _fake_frame_quality(
    *,
    frame_index: int = 2,
    time_seconds: float = 21600.0,
    position: str = "terminal",
    finite_count: int = 0,
    non_finite_count: int = 8,
    total_count: int = 8,
    total_frame_count: int = 3,
    finite_frame_count: int = 2,
) -> FieldFrameQualitySummary:
    frame_times_seconds: list[float | None]
    if total_frame_count <= 1:
        frame_times_seconds = [time_seconds]
    else:
        frame_times_seconds = [
            21600.0 * index / (total_frame_count - 1) for index in range(total_frame_count)
        ]
        frame_times_seconds[frame_index] = time_seconds
    return FieldFrameQualitySummary(
        affected_frames=[
            FieldFrameQualityRecord(
                frame_index=frame_index,
                time_seconds=time_seconds,
                position=position,  # type: ignore[arg-type]
                finite_count=finite_count,
                non_finite_count=non_finite_count,
                total_count=total_count,
                entirely_non_finite=finite_count == 0,
            )
        ],
        frame_times_seconds=frame_times_seconds,
        affected_frame_indices=[frame_index],
        affected_frame_times_seconds=[time_seconds],
        initial_frame_affected=position == "initial",
        terminal_frame_affected=position == "terminal",
        affected_frame_count=1,
        entirely_non_finite_frame_count=1 if finite_count == 0 else 0,
        partially_non_finite_frame_count=0 if finite_count == 0 else 1,
        finite_frame_count=finite_frame_count,
        total_frame_count=total_frame_count,
        finite_point_fraction=finite_frame_count / total_frame_count,
        chronology_available=True,
        chronology_caveats=[],
        first_finite_frame_time_seconds=0.0,
        last_finite_frame_time_seconds=3600.0 if position == "terminal" else time_seconds,
    )


def _fake_flux_caveats(
    field: str,
    non_finite_count: int,
    frame_quality: FieldFrameQualitySummary | None,
) -> list[str]:
    caveats: list[str] = []
    if non_finite_count > 0:
        caveats.append(f"non_finite_values_detected_in_{field}")
    if frame_quality is not None and frame_quality.terminal_frame_affected:
        caveats.append(f"{field}_terminal_output_frame_entirely_non_finite")
    elif frame_quality is not None and frame_quality.initial_frame_affected:
        caveats.append(f"{field}_initial_output_frame_entirely_non_finite")
    elif frame_quality is not None and frame_quality.entirely_non_finite_frame_count > 0:
        caveats.append(f"{field}_intermediate_output_frame_entirely_non_finite")
    return caveats


def _fake_field_quality_map(
    *,
    hfx_non_finite_count: int,
    qfx_non_finite_count: int,
    hfx_frame_quality: FieldFrameQualitySummary | None,
    qfx_frame_quality: FieldFrameQualitySummary | None,
) -> dict[str, FieldQuality]:
    fields = {
        "qc": "qc",
        "w": "w",
        "qr": "qr",
        "surface_rain": "rain",
        "dbz": "dbz",
        "hfx": "hfx",
        "qfx": "qfx",
    }
    qualities = {
        field: FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="trusted",
            finite_count=8,
            non_finite_count=0,
            total_count=8,
            finite_fraction=1.0,
        )
        for field, source_field in fields.items()
    }
    qualities["hfx"] = _fake_field_quality(
        "hfx",
        "hfx",
        non_finite_count=hfx_non_finite_count,
        frame_quality=hfx_frame_quality,
    )
    qualities["qfx"] = _fake_field_quality(
        "qfx",
        "qfx",
        non_finite_count=qfx_non_finite_count,
        frame_quality=qfx_frame_quality,
    )
    return qualities


def _fake_field_quality_from_caveats(caveats: list[str]) -> dict[str, FieldQuality]:
    fields = {
        "qc": ("qc", "non_finite_values_detected_in_qc", "qc_field_entirely_non_finite"),
        "w": ("w", "non_finite_values_detected_in_w", "w_field_entirely_non_finite"),
        "qr": ("qr", "non_finite_values_detected_in_qr", "qr_field_entirely_non_finite"),
        "surface_rain": (
            "rain",
            "non_finite_values_detected_in_surface_rain",
            "surface_rain_field_entirely_non_finite",
        ),
        "dbz": ("dbz", "non_finite_values_detected_in_dbz", "dbz_field_entirely_non_finite"),
    }
    overrides: dict[str, FieldQuality] = {}
    caveat_set = set(caveats)
    for field, (source_field, partial, entire) in fields.items():
        if entire in caveat_set:
            overrides[field] = FieldQuality(
                field=field,
                source_field=source_field,
                quality_state="untrusted",
                reason=entire,
                finite_count=0,
                non_finite_count=8,
                total_count=8,
                finite_fraction=0.0,
                caveats=[partial, entire],
            )
        elif partial in caveat_set:
            overrides[field] = FieldQuality(
                field=field,
                source_field=source_field,
                quality_state="caveated",
                reason=partial,
                finite_count=7,
                non_finite_count=1,
                total_count=8,
                finite_fraction=7 / 8,
                caveats=[partial],
            )
    return overrides


def _fake_field_quality(
    field: str,
    source_field: str,
    *,
    non_finite_count: int,
    frame_quality: FieldFrameQualitySummary | None,
) -> FieldQuality:
    if non_finite_count <= 0:
        return FieldQuality(
            field=field,
            source_field=source_field,
            quality_state="trusted",
            finite_count=8,
            non_finite_count=0,
            total_count=8,
            finite_fraction=1.0,
            frame_quality=frame_quality,
        )
    if frame_quality is not None and frame_quality.terminal_frame_affected:
        reason = f"{field}_terminal_output_frame_entirely_non_finite"
        quality_state = "untrusted"
    elif frame_quality is not None and frame_quality.initial_frame_affected:
        reason = f"{field}_initial_output_frame_entirely_non_finite"
        quality_state = "caveated"
    elif frame_quality is not None and frame_quality.entirely_non_finite_frame_count > 0:
        reason = f"{field}_intermediate_output_frame_entirely_non_finite"
        quality_state = "caveated"
    else:
        reason = f"non_finite_values_detected_in_{field}"
        quality_state = "caveated"
    return FieldQuality(
        field=field,
        source_field=source_field,
        quality_state=quality_state,  # type: ignore[arg-type]
        reason=reason,
        finite_count=8,
        non_finite_count=non_finite_count,
        total_count=8 + non_finite_count,
        finite_fraction=8 / (8 + non_finite_count),
        frame_quality=frame_quality,
        caveats=_fake_flux_caveats(field, non_finite_count, frame_quality),
    )


def _write_fake_result_metadata(
    manifest_path: Path,
    *,
    missing_required_output_fields: list[str] | None = None,
    warnings: list[str] | None = None,
    run_caveats: list[str] | None = None,
    interesting_time_caveats: list[str] | None = None,
    surface_rain_present: bool = False,
    hfx_mean: float = 2.0,
    qfx_mean: float = 2.0e-5,
    hfx_units: str = "K m/s",
    qfx_units: str = "kg/m^2/s",
    hfx_non_finite_count: int = 0,
    qfx_non_finite_count: int = 0,
    hfx_frame_quality: FieldFrameQualitySummary | None = None,
    qfx_frame_quality: FieldFrameQualitySummary | None = None,
    field_quality_overrides: dict[str, FieldQuality] | None = None,
    low_level_qv_delta: float | None = None,
    low_level_theta_delta: float | None = None,
    low_level_qv_full_run_delta: float | None = None,
    low_level_theta_full_run_delta: float | None = None,
    low_level_qv_early_end_finite_count: int = 8,
    low_level_qv_early_end_total_count: int = 8,
) -> None:
    manifest = load_run_manifest(manifest_path)
    now = datetime.now(UTC)
    field_quality = _fake_field_quality_map(
        hfx_non_finite_count=hfx_non_finite_count,
        qfx_non_finite_count=qfx_non_finite_count,
        hfx_frame_quality=hfx_frame_quality,
        qfx_frame_quality=qfx_frame_quality,
    )
    field_quality.update(_fake_field_quality_from_caveats(run_caveats or []))
    field_quality.update(field_quality_overrides or {})
    runtime_integrity = assess_runtime_integrity(
        exit_code=0,
        runtime_warnings=warnings or [],
        field_quality=field_quality,
    )
    result = ResultMetadata(
        result_id=f"result-{manifest.run_id}",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        physical_question=manifest.physical_question,
        controls=manifest.controls,
        run_configuration=manifest.run_configuration,
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        input_source=manifest.input_source or "observed_sounding",
        input_source_label="Observed sounding",
        observed_sounding=manifest.observed_sounding,
        run_recipe=manifest.run_recipe,
        run_recipe_display_name=manifest.run_recipe_display_name,
        recipe_id=manifest.recipe_id,
        recipe_display_name=manifest.recipe_display_name,
        assumption_set_id=manifest.assumption_set_id,
        assumption_mode=manifest.assumption_mode,
        recipe_assumptions=manifest.recipe_assumptions,
        required_output_fields=manifest.required_output_fields,
        missing_required_output_fields=missing_required_output_fields or [],
        candidate_screening=manifest.candidate_screening,
        variables=["qc", "w", "qr", "rain", "dbz", "hfx", "qfx", "qv", "th"],
        fields_detected=[
            FieldMetadata(
                name="hfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units=hfx_units
            ),
            FieldMetadata(
                name="qfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units=qfx_units
            ),
            FieldMetadata(
                name="qv", dimensions=["time", "z", "y", "x"], shape=[2, 2, 2, 2], units="kg/kg"
            ),
            FieldMetadata(
                name="th", dimensions=["time", "z", "y", "x"], shape=[2, 2, 2, 2], units="K"
            ),
        ],
        diagnostics=ResultDiagnostics(
            cloud=CloudDiagnostics(
                formed=True,
                first_cloud_time_seconds=900.0,
                cloud_top_m=1800.0,
                cloud_top_time_series=[
                    TimeValue(time_seconds=900.0, value=900.0),
                    TimeValue(time_seconds=1800.0, value=1800.0),
                ],
                max_qc_kg_kg=2.0e-5,
                time_of_max_qc_seconds=1800.0,
            ),
            vertical_velocity=VerticalVelocityDiagnostics(
                max_w_m_s=2.5,
                time_of_max_w_seconds=1800.0,
                max_w_height_time_series=[
                    TimeValue(time_seconds=1800.0, value=2400.0),
                ],
                units="m/s",
            ),
            rain=RainDiagnostics(
                present=True,
                first_rain_time_seconds=2700.0,
                max_qr_kg_kg=1.0e-6,
                available=True,
            ),
            surface_rain=SurfaceRainDiagnostics(
                present=surface_rain_present,
                max_surface_rain=1.25 if surface_rain_present else 0.0,
                units="mm",
                available=True,
                field_absent=False,
            ),
            reflectivity=ReflectivityDiagnostics(
                max_dbz=32.0,
                units="dBZ",
                available=True,
                field_absent=False,
            ),
            surface_fluxes=SurfaceFluxDiagnostics(
                hfx=SurfaceFluxFieldDiagnostics(
                    source_field="hfx",
                    available=True,
                    field_absent=False,
                    min_value=hfx_mean,
                    max_value=hfx_mean,
                    mean_value=hfx_mean,
                    units=hfx_units,
                    finite_count=8,
                    non_finite_count=hfx_non_finite_count,
                    total_count=8 + hfx_non_finite_count,
                    finite_fraction=8 / (8 + hfx_non_finite_count)
                    if (8 + hfx_non_finite_count) > 0
                    else None,
                    frame_quality=hfx_frame_quality,
                    caveats=_fake_flux_caveats("hfx", hfx_non_finite_count, hfx_frame_quality),
                ),
                qfx=SurfaceFluxFieldDiagnostics(
                    source_field="qfx",
                    available=True,
                    field_absent=False,
                    min_value=qfx_mean,
                    max_value=qfx_mean,
                    mean_value=qfx_mean,
                    units=qfx_units,
                    finite_count=8,
                    non_finite_count=qfx_non_finite_count,
                    total_count=8 + qfx_non_finite_count,
                    finite_fraction=8 / (8 + qfx_non_finite_count)
                    if (8 + qfx_non_finite_count) > 0
                    else None,
                    frame_quality=qfx_frame_quality,
                    caveats=_fake_flux_caveats("qfx", qfx_non_finite_count, qfx_frame_quality),
                ),
            ),
            low_level_response=LowLevelResponseDiagnostics(
                qv=_fake_low_level_response_field(
                    source_field="qv",
                    delta=low_level_qv_delta,
                    full_run_delta=low_level_qv_full_run_delta,
                    units="kg/kg",
                    early_end_finite_count=low_level_qv_early_end_finite_count,
                    early_end_total_count=low_level_qv_early_end_total_count,
                ),
                theta_or_temperature=_fake_low_level_response_field(
                    source_field="th",
                    delta=low_level_theta_delta,
                    full_run_delta=low_level_theta_full_run_delta,
                    units="K",
                ),
            ),
            time=TimeDiagnostics(source="time", fallback_used=False, coordinate_name="time"),
            field_quality_assessed=True,
            field_quality=field_quality,
        ),
        run_caveats=run_caveats or [],
        runtime_integrity=runtime_integrity,
        science_summary=ScienceSummary(
            cloud_formed=True,
            deep_cloud_formed=False,
            strong_updraft_formed=False,
            first_cloud_time_seconds=900.0,
            first_cloud_time_label="900 s",
            time_of_first_deep_convection_seconds=None,
            max_qc_kg_kg=2.0e-5,
            max_qc_time_seconds=1800.0,
            max_updraft_w_m_s=2.5,
            max_updraft_time_seconds=1800.0,
            highest_cloud_top_m=1800.0,
            rain_onset_time_seconds=2700.0,
            max_qr_kg_kg=1.0e-6,
            max_rain_or_surface_precip=0.0,
            max_dbz_or_reflectivity_proxy=32.0,
            latest_output_time_seconds=3600.0,
            default_explore_time_index=1,
            default_explore_time_seconds=1800.0,
            interesting_time_support_state="supported",
        ),
        warnings=warnings or [],
        interesting_time_caveats=interesting_time_caveats or [],
        created_at=now,
        updated_at=now,
    )
    (manifest_path.parent / RESULT_METADATA_FILENAME).write_text(result.to_json_text())


def test_campaign_summary_json_is_plain_json(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    matrix_path = write_matrix(tmp_path)
    package_campaign(matrix_path, settings=settings, resume=True)
    summary_path = tmp_path / "summary.json"

    report_campaign(
        matrix_path,
        settings=settings,
        report_path=tmp_path / "report.md",
        summary_json_path=summary_path,
    )

    loaded = json.loads(summary_path.read_text())
    assert loaded["campaign_id"] == "surface_forced_test"

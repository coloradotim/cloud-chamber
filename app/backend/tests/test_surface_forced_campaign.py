from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml  # type: ignore[import-untyped]
from igra_fixtures import IGRA_FIXTURE

from cloud_chamber.result_diagnostics import (
    CloudDiagnostics,
    RainDiagnostics,
    ReflectivityDiagnostics,
    ResultDiagnostics,
    SurfaceRainDiagnostics,
    TimeDiagnostics,
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
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.surface_forced_campaign import (
    CampaignError,
    build_campaign_plan,
    package_campaign,
    queue_campaign,
    report_campaign,
)


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def write_matrix(tmp_path: Path, *, queue_target: str = "local") -> Path:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "valley.txt").write_text(IGRA_FIXTURE)
    matrix = {
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
                "required_available_fields": ["hfx", "lhfx", "qv", "qc", "w"],
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
    matrix_path = tmp_path / "campaign.yaml"
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
    assert summary["phase_gate_state"] == "forcing_wiring_verified_but_response_not_verified"
    run = summary["runs"][0]
    assert run["hfx_present"] is True
    assert run["lhfx_present"] is True
    assert run["low_level_qv_response"] == "unavailable"
    assert run["low_level_qv_response_method"] == "low_level_response_diagnostic_not_implemented"
    assert "low_level_qv_response" in summary["unavailable_diagnostics"]
    assert "max w `2.5`" in report_path.read_text()


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


def _write_fake_result_metadata(manifest_path: Path) -> None:
    manifest = load_run_manifest(manifest_path)
    now = datetime.now(UTC)
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
        missing_required_output_fields=[],
        candidate_screening=manifest.candidate_screening,
        variables=["qc", "w", "qr", "rain", "dbz", "hfx", "lhfx"],
        fields_detected=[
            FieldMetadata(
                name="hfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units="K m/s"
            ),
            FieldMetadata(
                name="lhfx", dimensions=["time", "y", "x"], shape=[2, 2, 2], units="g/g m/s"
            ),
        ],
        diagnostics=ResultDiagnostics(
            cloud=CloudDiagnostics(
                formed=True,
                first_cloud_time_seconds=900.0,
                cloud_top_m=1800.0,
                max_qc_kg_kg=2.0e-5,
                time_of_max_qc_seconds=1800.0,
            ),
            vertical_velocity=VerticalVelocityDiagnostics(
                max_w_m_s=2.5,
                time_of_max_w_seconds=1800.0,
                units="m/s",
            ),
            rain=RainDiagnostics(
                present=True,
                first_rain_time_seconds=2700.0,
                max_qr_kg_kg=1.0e-6,
                available=True,
            ),
            surface_rain=SurfaceRainDiagnostics(
                present=False,
                max_surface_rain=0.0,
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
            time=TimeDiagnostics(source="time", fallback_used=False, coordinate_name="time"),
        ),
        warnings=[],
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

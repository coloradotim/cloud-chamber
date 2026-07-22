from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cloud_chamber.mountain_waves_world import (
    DRY_CASE_ID,
    DRY_RUN_ID,
    DRY_SIMULATION_ID,
    MOIST_CASE_ID,
    MOIST_RUN_ID,
    MOIST_SIMULATION_ID,
    mountain_waves_world_detail,
)
from cloud_chamber.run_manifest import (
    AppMetadata,
    GeneratedInputs,
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    RunManifest,
    RuntimePaths,
    ScenarioReference,
    UserMetadata,
    ValidationStatus,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings


def test_world_installs_distinct_dry_and_moist_references(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)

    world = mountain_waves_world_detail(settings)

    assert world.world_id == "mountain_waves"
    assert world.display_name == "Mountain Waves"
    assert world.availability_state == "available"
    assert [simulation.simulation_id for simulation in world.simulations] == [
        DRY_SIMULATION_ID,
        MOIST_SIMULATION_ID,
    ]
    assert all(simulation.inspectable for simulation in world.simulations)
    assert all(simulation.can_create_variation for simulation in world.simulations)
    assert world.simulations[0].moist is False
    assert world.simulations[1].moist is True
    assert any("not a controlled pair" in caveat for caveat in world.caveats)


def test_missing_reference_is_honest_without_disabling_lab(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)

    world = mountain_waves_world_detail(settings)

    assert world.availability_state == "partial"
    assert world.simulations[0].state == "unavailable"
    assert world.simulations[0].inspectable is False
    assert world.simulations[1].inspectable is True
    assert world.default_parent_simulation_id == MOIST_SIMULATION_ID
    assert world.lab_summary.total_variation_count == 0


def test_variation_history_and_completed_simulation_survive_reload(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    _write_run(
        settings,
        run_id="mw-smoother-wave-20260721T230000Z-abcd",
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "mountain_waves_smoother_wave_abcd1234",
            "simulation_display_name": "Smoother Wave",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "parent_run_id": MOIST_RUN_ID,
            "reference_simulation_id": MOIST_SIMULATION_ID,
            "mountain_waves_configuration": _configuration(),
            "configuration_difference": {
                "terrain": [
                    {"label": "Ridge height", "before": 2000.0, "after": 1500.0, "units": "m"}
                ]
            },
            "warnings": ["Multiple physical groups change together."],
        },
    )

    first = mountain_waves_world_detail(settings)
    second = mountain_waves_world_detail(settings)

    for world in (first, second):
        variation = next(
            item
            for item in world.simulations
            if item.simulation_id == "mountain_waves_smoother_wave_abcd1234"
        )
        assert variation.state == "available"
        assert variation.parent_simulation_id == MOIST_SIMULATION_ID
        assert variation.can_create_variation is True
        assert world.history[0].simulation_id == variation.simulation_id
        assert world.lab_summary.completed_simulation_count == 1


def _settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path / "CloudChamber",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def _write_run(
    settings: CloudChamberSettings,
    *,
    run_id: str,
    case_id: str,
    run_configuration: dict[str, Any] | None = None,
) -> Path:
    run_dir = settings.runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF fixture")
    namelist = run_dir / "namelist.input"
    sounding = run_dir / "input_sounding"
    namelist.write_text(" &param0\n nx = 3,\n /\n")
    sounding.write_text("1000.0 288.0 0.0\n0.0 288.0 0.0 10.0 0.0\n")
    now = datetime(2026, 7, 21, tzinfo=UTC)
    manifest_path = run_dir / "run_manifest.json"
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=case_id, schema_version="test-v1"),
        controls={},
        run_configuration=run_configuration or {},
        physical_question="What happened over the ridge?",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist),
            input_sounding=str(sounding),
        ),
        runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home)),
        app=AppMetadata(app_version="test", commit="test-commit"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.NEEDS_REVIEW,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        outputs=OutputMetadata(netcdf_paths=[str(output)]),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name=run_id),
    )
    write_run_manifest(manifest_path, manifest)
    return manifest_path


def _configuration() -> dict[str, Any]:
    return {
        "terrain": {"height_m": 1500.0, "half_width_m": 10000.0, "center_m": 500.0},
        "sounding": [
            {
                "height_m": 0.0,
                "pressure_pa": 100000.0,
                "theta_k": 288.0,
                "qv_g_kg": 4.0,
                "u_m_s": 12.0,
                "v_m_s": 0.0,
            },
            {
                "height_m": 12500.0,
                "pressure_pa": 20000.0,
                "theta_k": 340.0,
                "qv_g_kg": 0.5,
                "u_m_s": 20.0,
                "v_m_s": 0.0,
            },
            {
                "height_m": 25200.0,
                "pressure_pa": 3000.0,
                "theta_k": 440.0,
                "qv_g_kg": 0.0,
                "u_m_s": 25.0,
                "v_m_s": 0.0,
            },
        ],
        "duration_seconds": 4000,
        "output_cadence_seconds": 200,
    }

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.mountain_waves_world import (
    _BUILT_INS,
    DRY_CASE_ID,
    DRY_RUN_ID,
    DRY_SIMULATION_ID,
    MOIST_CASE_ID,
    MOIST_RUN_ID,
    MOIST_SIMULATION_ID,
    _built_in_inspectability,
    mountain_waves_world_detail,
)
from cloud_chamber.run_manifest import (
    AppMetadata,
    ExecutionMetadata,
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


@pytest.fixture(autouse=True)
def _trust_test_built_in_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_world._built_in_inspectability",
        lambda _settings, _spec, _manifest: (True, "Test artifact accepted."),
    )


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
    assert world.simulations[0].can_create_variation is False
    assert world.simulations[1].can_create_variation is True
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


@pytest.mark.parametrize("corruption", ["missing_history", "missing_field", "wrong_time"])
def test_completed_variation_with_invalid_native_output_stays_noninspectable(
    tmp_path: Path, corruption: str
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    manifest_path = _write_run(
        settings,
        run_id=f"mw-invalid-{corruption}",
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": f"mountain_waves_invalid_{corruption}",
            "simulation_display_name": "Invalid output",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "parent_run_id": MOIST_RUN_ID,
            "mountain_waves_configuration": _configuration(),
            "configuration_difference": {"terrain": [{"label": "Ridge height"}]},
        },
    )
    run_dir = manifest_path.parent
    if corruption == "missing_history":
        (run_dir / "cm1out_000003.nc").unlink()
    else:
        path = run_dir / "cm1out_000002.nc"
        with xr.open_dataset(path, decode_times=False) as source:
            dataset = source.load()
        if corruption == "missing_field":
            dataset = dataset.drop_vars("uinterp")
        else:
            dataset["time"] = xr.DataArray([201], dims=("time",), attrs={"units": "seconds"})
        dataset.to_netcdf(path, mode="w")

    world = mountain_waves_world_detail(settings)
    attempt = next(item for item in world.history if item.run_id == f"mw-invalid-{corruption}")

    assert attempt.inspectable is False
    assert attempt.state == "conflict"
    assert attempt not in world.simulations
    assert "failed native-data validation" in attempt.state_message


def test_contradictory_built_in_artifact_is_not_promoted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    manifest_path = _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    from cloud_chamber.run_manifest import load_run_manifest

    manifest = load_run_manifest(manifest_path)
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_world.load_completed_mountain_wave_package_for_evaluation",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("hash contradiction")),
    )

    inspectable, message = _built_in_inspectability(settings, _BUILT_INS[0], manifest)

    assert inspectable is False
    assert "hash contradiction" in message


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
    namelist = run_dir / "namelist.input"
    sounding = run_dir / "input_sounding"
    is_variation = case_id == "mountain_waves_exploratory_variation_v1"
    if is_variation:
        outputs = _write_native_histories(run_dir)
        namelist = run_dir / "namelist.input"
    else:
        output = run_dir / "cm1out_000001.nc"
        output.write_bytes(b"built-in identity fixture")
        outputs = [output]
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
        execution=ExecutionMetadata(started_at=now, finished_at=now, exit_code=0),
        outputs=OutputMetadata(netcdf_paths=[str(output) for output in outputs]),
        required_output_fields=(
            ["prs", "ql", "qv", "th", "uinterp", "w", "winterp", "zhval", "zs"]
            if is_variation
            else []
        ),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name=run_id),
    )
    write_run_manifest(manifest_path, manifest)
    return manifest_path


def _write_native_histories(run_dir: Path) -> list[Path]:
    (run_dir / "namelist.input").write_text(
        """ &param0
 nx = 3,
 ny = 1,
 nz = 2,
 dx = 1000.0,
 dy = 1000.0,
 dz = 10000.0,
 timax = 400.0,
 tapfrq = 200.0,
 stretch_z = 0,
 ztop = 19000.0,
 /
"""
    )
    terrain = np.asarray([0.0, 400.0, 100.0])
    nominal_scalar = np.asarray([5_000.0, 15_000.0])
    scalar_height = (
        terrain[None, :] + nominal_scalar[:, None] * (20_000.0 - terrain[None, :]) / 20_000.0
    )
    outputs: list[Path] = []
    for index, time_seconds in enumerate((0, 200, 400), start=1):
        scalar_shape = (1, 2, 1, 3)
        scalar_w = np.full(scalar_shape, 0.1 * index)
        dataset = xr.Dataset(
            data_vars={
                "zs": (("time", "yh", "xh"), terrain.reshape(1, 1, 3), {"units": "m"}),
                "zhval": (
                    ("time", "zh", "yh", "xh"),
                    scalar_height.reshape(scalar_shape),
                    {"units": "m"},
                ),
                "th": (("time", "zh", "yh", "xh"), np.full(scalar_shape, 290.0), {"units": "K"}),
                "prs": (
                    ("time", "zh", "yh", "xh"),
                    np.full(scalar_shape, 70_000.0),
                    {"units": "Pa"},
                ),
                "qv": (
                    ("time", "zh", "yh", "xh"),
                    np.full(scalar_shape, 0.004),
                    {"units": "kg/kg"},
                ),
                "ql": (("time", "zh", "yh", "xh"), np.zeros(scalar_shape), {"units": "kg/kg"}),
                "uinterp": (
                    ("time", "zh", "yh", "xh"),
                    np.full(scalar_shape, 15.0),
                    {"units": "m/s"},
                ),
                "winterp": (("time", "zh", "yh", "xh"), scalar_w, {"units": "m/s"}),
                "w": (("time", "zf", "yh", "xh"), np.full((1, 3, 1, 3), 0.1), {"units": "m/s"}),
                "ztop": (("one",), [20_000.0], {"units": "m"}),
            },
            coords={
                "time": ("time", [time_seconds], {"units": "seconds"}),
                "xh": ("xh", [-1.0, 0.0, 1.0], {"units": "km"}),
                "xf": ("xf", [-1.5, -0.5, 0.5, 1.5], {"units": "km"}),
                "yh": ("yh", [0.0], {"units": "km"}),
                "yf": ("yf", [-0.5, 0.5], {"units": "km"}),
                "zh": ("zh", [5.0, 15.0], {"units": "km"}),
                "zf": ("zf", [0.0, 10.0, 20.0], {"units": "km"}),
                "one": ("one", [1]),
            },
        )
        path = run_dir / f"cm1out_{index:06d}.nc"
        dataset.to_netcdf(path)
        outputs.append(path)
    return outputs


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

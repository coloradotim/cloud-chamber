from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.mountain_wave_terrain_visualization import (
    validate_mountain_waves_native_outputs,
)
from cloud_chamber.mountain_waves_world import (
    _BUILT_INS,
    DRY_CASE_ID,
    DRY_RUN_ID,
    DRY_SIMULATION_ID,
    MOIST_CASE_ID,
    MOIST_RUN_ID,
    MOIST_SIMULATION_ID,
    _built_in_inspectability,
    mountain_waves_run_manifest,
    mountain_waves_world_detail,
)
from cloud_chamber.presentation_runs import spec_by_key
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
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.variation_envelope import (
    VariationAttempt,
    VariationDifference,
    VariationEnvelope,
    immutable_layer,
)


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
    assert "bounded equivalence" in (world.simulations[0].parent_eligibility_reason or "")
    assert world.simulations[0].recipe_id == "dry_ridge_mechanics"
    assert world.simulations[1].can_create_variation is True
    assert world.simulations[1].recipe_id == "boulder_moist_wave"
    assert world.simulations[0].moist is False
    assert world.simulations[1].moist is True
    assert any("not a controlled pair" in caveat for caveat in world.caveats)


def test_built_ins_resolve_the_exact_presentation_run_contracts() -> None:
    for built_in in _BUILT_INS:
        presentation = spec_by_key(built_in.presentation_key)
        assert presentation.run_id == built_in.run_id
        assert presentation.case_id == built_in.case_id
        assert presentation.moist_terrain == built_in.moist


def test_missing_reference_is_honest_without_disabling_lab(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)

    world = mountain_waves_world_detail(settings)

    assert world.availability_state == "partial"
    assert world.simulations[0].state == "unavailable"
    assert world.simulations[0].inspectable is False
    assert world.simulations[1].inspectable is True
    assert world.default_parent_simulation_id == MOIST_SIMULATION_ID
    assert world.lab_summary.total_variation_count == 1
    assert world.history[0].legacy_contract is True
    assert world.history[0].simulation_id == "mountain_waves_broader-boulder-ridge_f8f714fb"


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
        assert variation.can_create_variation is False
        assert variation.legacy_contract is True
        assert "Legacy-contract" in (variation.parent_eligibility_reason or "")
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
        "cloud_chamber.mountain_waves_world._verify_presentation_built_in",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("hash contradiction")),
    )

    inspectable, message = _built_in_inspectability(settings, _BUILT_INS[0], manifest)

    assert inspectable is False
    assert "hash contradiction" in message


def test_world_polling_reuses_validation_until_artifact_fingerprint_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    manifest_path = _write_run(
        settings,
        run_id="mw-cached-validation",
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "mountain_waves_cached_validation",
            "simulation_display_name": "Cached validation",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "parent_run_id": MOIST_RUN_ID,
            "mountain_waves_configuration": _configuration(),
        },
    )
    original = validate_mountain_waves_native_outputs
    calls = 0

    def counted_validation(**kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_world.validate_mountain_waves_native_outputs",
        counted_validation,
    )

    mountain_waves_world_detail(settings)
    mountain_waves_world_detail(settings)
    assert calls == 1

    output = manifest_path.parent / "cm1out_000002.nc"
    os.utime(output, None)
    mountain_waves_world_detail(settings)
    assert calls == 2


def test_completed_variation_rechecks_generated_input_hashes_before_promotion(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    manifest_path = _write_run(
        settings,
        run_id="mw-tampered-input",
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "mountain_waves_tampered_input",
            "simulation_display_name": "Tampered input",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "parent_run_id": MOIST_RUN_ID,
            "mountain_waves_configuration": _configuration(),
        },
    )
    manifest = load_run_manifest(manifest_path)
    namelist = Path(manifest.generated_inputs.namelist_input or "")
    digest = hashlib.sha256(namelist.read_bytes()).hexdigest()
    configuration = {
        **manifest.run_configuration,
        "generated_input_sha256": {namelist.name: digest},
    }
    write_run_manifest(
        manifest_path,
        manifest.model_copy(update={"run_configuration": configuration}),
    )
    namelist.write_text(namelist.read_text() + "\n! changed after packaging\n")

    world = mountain_waves_world_detail(settings)
    attempt = next(item for item in world.history if item.run_id == "mw-tampered-input")

    assert attempt.inspectable is False
    assert "changed after packaging" in attempt.state_message


def test_direct_simulation_resolution_does_not_reconstruct_the_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    _write_run(
        settings,
        run_id="mw-direct-resolution",
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration={
            "cloud_world_id": "mountain_waves",
            "simulation_id": "mountain_waves_direct_resolution",
            "simulation_display_name": "Direct resolution",
            "parent_simulation_id": MOIST_SIMULATION_ID,
            "parent_run_id": MOIST_RUN_ID,
            "mountain_waves_configuration": _configuration(),
        },
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_world.mountain_waves_world_detail",
        lambda _settings: (_ for _ in ()).throw(AssertionError("whole World rebuilt")),
    )

    record, manifest, _manifest_path = mountain_waves_run_manifest(
        settings, "mountain_waves_direct_resolution"
    )

    assert record.inspectable is True
    assert manifest.run_id == "mw-direct-resolution"


def test_attempts_with_one_simulation_identity_collapse_to_one_world_record(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    simulation_id = "mountain_waves_same_design"
    first_run = "mw-same-design-a"
    second_run = "mw-same-design-b"
    _write_run(
        settings,
        run_id=first_run,
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration=_variation_configuration(
            simulation_id=simulation_id,
            run_id=first_run,
        ),
    )
    _write_run(
        settings,
        run_id=second_run,
        case_id="mountain_waves_exploratory_variation_v1",
        run_configuration=_variation_configuration(
            simulation_id=simulation_id,
            run_id=second_run,
        ),
    )

    world = mountain_waves_world_detail(settings)

    records = [item for item in world.simulations if item.simulation_id == simulation_id]
    assert len(records) == 1
    assert records[0].run_id == first_run
    assert world.lab_summary.completed_simulation_count == 1
    promoted = load_run_manifest(settings.runtime_home / "runs" / first_run / "run_manifest.json")
    envelope = VariationEnvelope.model_validate(promoted.run_configuration["variation_envelope"])
    assert [attempt.run_id for attempt in envelope.attempts] == [first_run, second_run]
    assert [attempt.run_id for attempt in envelope.attempts if attempt.accepted_backing] == [
        first_run
    ]


def test_conflicting_accepted_attempts_fail_closed(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID)
    _write_run(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID)
    simulation_id = "mountain_waves_conflicted_design"
    for suffix in ("a", "b"):
        run_id = f"mw-conflicted-design-{suffix}"
        _write_run(
            settings,
            run_id=run_id,
            case_id="mountain_waves_exploratory_variation_v1",
            run_configuration=_variation_configuration(
                simulation_id=simulation_id,
                run_id=run_id,
                accepted_backing=True,
            ),
        )

    world = mountain_waves_world_detail(settings)

    conflict = next(item for item in world.history if item.simulation_id == simulation_id)
    assert conflict.state == "conflict"
    assert conflict.inspectable is False
    assert "Multiple attempts claim accepted backing" in conflict.state_message
    assert all(item.simulation_id != simulation_id for item in world.simulations)
    with pytest.raises(ValueError, match="backing is conflicted"):
        mountain_waves_run_manifest(settings, simulation_id)


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


def _variation_configuration(
    *,
    simulation_id: str,
    run_id: str,
    accepted_backing: bool = False,
) -> dict[str, Any]:
    scientific_design = {
        "world_id": "mountain_waves",
        "recipe_id": "boulder_moist_wave",
        "recipe_contract_version": "1",
        "controls": {
            "recipe_id": "boulder_moist_wave",
            "boulder_moist": {
                "ridge_height_m": 2_000.0,
                "ridge_half_width_m": 11_000.0,
                "low_level_wind_m_s": 14.1,
                "wind_offset_m_s": 0.0,
                "shear_through_10km_m_s": 23.8,
                "lower_layer_rh_percent": 66.0,
                "midlevel_rh_percent": 34.5,
                "dry_air_counterpart": False,
                "lower_stability_factor": 1.0,
                "midlevel_stability_factor": 1.0,
                "upper_stability_factor": 1.0,
            },
        },
    }
    numerical = {"grid": "fixture"}
    observation = {
        "duration_seconds": 400.0,
        "output_cadence_seconds": 200.0,
    }
    envelope = VariationEnvelope(
        world_id="mountain_waves",
        recipe_id="boulder_moist_wave",
        recipe_contract_version="1",
        simulation_id=simulation_id,
        parent_simulation_id=MOIST_SIMULATION_ID,
        reference_simulation_id=MOIST_SIMULATION_ID,
        display_name="Same design",
        scientific_design=immutable_layer(scientific_design),
        numerical_realization=immutable_layer(numerical),
        observation_plan=immutable_layer(observation),
        world_payload={
            "controls": scientific_design["controls"],
            "terrain": {"height_m": 2_000.0, "half_width_m": 11_000.0},
            "diagnostics": {
                "periodic_wrap_time_seconds": 10_000.0,
                "damping_base_m": 20_000.0,
                "model_top_m": 30_000.0,
            },
        },
        differences=[
            VariationDifference(
                category="terrain",
                path="controls.ridge_half_width_m",
                label="Ridge half-width",
                before=10_000.0,
                after=11_000.0,
                units="m",
            )
        ],
        relationship_classification="controlled_physical_variation",
        run_profile_id="mountain_waves_boulder_quick_v1",
        run_profile_contract={},
        cost_estimate={},
        package_identity_sha256=f"package-{run_id}",
        attempts=[
            VariationAttempt(
                attempt_id=run_id,
                run_id=run_id,
                relationship="initial",
                package_identity_sha256=f"package-{run_id}",
                accepted_backing=accepted_backing,
            )
        ],
        availability_state="packaged",
    )
    configuration = _configuration()
    return {
        "cloud_world_id": "mountain_waves",
        "simulation_id": simulation_id,
        "simulation_display_name": "Same design",
        "parent_simulation_id": MOIST_SIMULATION_ID,
        "parent_run_id": MOIST_RUN_ID,
        "reference_simulation_id": MOIST_SIMULATION_ID,
        "variation_envelope": envelope.model_dump(mode="json"),
        "mountain_waves_configuration": configuration,
        "duration_seconds": 400.0,
        "output_cadence_seconds": 200.0,
        "domain": {
            "nx": 3,
            "ny": 1,
            "nz": 2,
            "dx_m": 1_000.0,
            "dy_m": 1_000.0,
            "dz_m": 10_000.0,
            "active_top_m": 20_000.0,
        },
        "terrain": configuration["terrain"],
    }

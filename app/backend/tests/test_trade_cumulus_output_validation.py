from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.bomex_case import CM1_SOURCE_MANIFEST_SHA256, CRITICAL_SOURCE_HASHES
from cloud_chamber.cm1_source_customization import (
    CUSTOM_EXECUTABLE_FILENAME,
)
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.run_cost import ExactNumericalDomain
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
)
from cloud_chamber.trade_cumulus_forcing import (
    TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
    TRADE_CUMULUS_FORCING_SCHEMA_VERSION,
    TRADE_CUMULUS_FORCING_TARGET,
)
from cloud_chamber.trade_cumulus_forcing_diagnostics import (
    expected_forcing_profiles,
    forcing_diagnostic_contract,
)
from cloud_chamber.trade_cumulus_output_validation import (
    TradeCumulusOutputValidationError,
    clear_trade_cumulus_output_validation_cache,
    validate_trade_cumulus_variation_outputs,
)
from cloud_chamber.trade_cumulus_recipes import default_controls
from cloud_chamber.variation_envelope import (
    VariationAttempt,
    VariationEnvelope,
    canonical_payload_sha256,
    immutable_layer,
)

_CANONICAL_EXECUTABLE_BYTES = b"approved canonical executable"
_CANONICAL_EXECUTABLE_SHA256 = hashlib.sha256(_CANONICAL_EXECUTABLE_BYTES).hexdigest()


@pytest.fixture(autouse=True)
def _clear_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_trade_cumulus_output_validation_cache()
    monkeypatch.setattr(
        "cloud_chamber.trade_cumulus_attempt_provenance.CM1_EXECUTABLE_SHA256",
        _CANONICAL_EXECUTABLE_SHA256,
    )


def test_valid_output_is_cached_and_cloud_free_response_is_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, metadata = _artifacts(tmp_path)
    original = xr.open_dataset
    calls = 0

    def counted(*args: Any, **kwargs: Any) -> xr.Dataset:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "cloud_chamber.trade_cumulus_output_validation.xr.open_dataset",
        counted,
    )

    first = validate_trade_cumulus_variation_outputs(manifest, metadata)
    second = validate_trade_cumulus_variation_outputs(manifest, metadata)

    assert first == second
    assert first["history_count"] == 3
    assert first["cloud_response_required"] is False
    assert first["resolved_fields"]["w"] == "w"
    assert first["forcing_diagnostics"]["file_count"] == 3
    assert calls == 6


@pytest.mark.parametrize(
    ("corruption", "message"),
    [
        ("missing_w", "Required native field w is absent"),
        ("wrong_ql_units", "unsupported units"),
        ("nonfinite_w", "contains nonfinite values"),
        ("wrong_grid", "reviewed grid"),
        ("wrong_spacing", "reviewed spacing"),
        ("wrong_extent", "reviewed domain bounds"),
        ("wrong_top", "reviewed model top"),
        ("wrong_start", "exact reviewed timeline"),
        ("wrong_time", "exact reviewed timeline"),
        ("wrong_end", "exact reviewed timeline"),
        ("escaped_output", "escapes the accepted attempt directory"),
        ("wrong_surface_flux", "does not match the reviewed target"),
        ("wrong_provenance", "approved source manifest"),
        ("missing_diagnostic", "forcing diagnostic histories"),
        ("wrong_diagnostic_time", "exact retained cadence"),
        ("missing_diagnostic_field", "Required forcing diagnostic field"),
        ("wrong_diagnostic_units", "unsupported units"),
        ("wrong_diagnostic_profile", "reviewed forcing profile"),
        ("wrong_canonical_command", "approved configured executable"),
        ("tampered_canonical_executable", "executable identity"),
        ("wrong_launch_executable_hash", "executable identity"),
    ],
)
def test_invalid_native_output_fails_closed(
    tmp_path: Path,
    corruption: str,
    message: str,
) -> None:
    manifest, metadata = _artifacts(tmp_path, corruption=corruption)

    with pytest.raises(TradeCumulusOutputValidationError, match=message):
        validate_trade_cumulus_variation_outputs(manifest, metadata)


def test_generated_input_tampering_fails_before_output_promotion(tmp_path: Path) -> None:
    manifest, metadata = _artifacts(tmp_path)
    Path(manifest.generated_inputs.input_sounding or "").write_text("changed\n")

    with pytest.raises(TradeCumulusOutputValidationError, match="changed after"):
        validate_trade_cumulus_variation_outputs(manifest, metadata)


def test_forcing_modified_output_binds_package_build_executable_and_readback(
    tmp_path: Path,
) -> None:
    manifest, metadata = _artifacts(tmp_path, forcing_customization=True)

    report = validate_trade_cumulus_variation_outputs(manifest, metadata)

    provenance = report["attempt_provenance"]
    assert provenance["customization_kind"] == TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND
    assert provenance["executable_kind"] == "isolated_forcing_customization"
    assert provenance["forcing_readback"] == {
        "vertical_motion_m_s": 0.01,
        "temperature_tendency_k_day": 3.0,
        "total_water_tendency_g_kg_day": -4.0,
    }


@pytest.mark.parametrize(
    ("corruption", "message"),
    [
        ("wrong_applied_forcing", "does not match the reviewed forcing targets"),
        ("wrong_execution_command", "did not use the applied custom executable"),
        ("tampered_custom_executable", "hash does not match"),
    ],
)
def test_forcing_modified_output_fails_closed_on_unbound_execution(
    tmp_path: Path,
    corruption: str,
    message: str,
) -> None:
    manifest, metadata = _artifacts(tmp_path, forcing_customization=True)
    status = dict(manifest.cm1_source_customization_status or {})
    if corruption == "wrong_applied_forcing":
        status["forcing"] = {
            **dict(status["forcing"]),
            "temperature_tendency_k_day": 2.0,
        }
        manifest.cm1_source_customization_status = status
    elif corruption == "wrong_execution_command":
        manifest.execution.command = ["/approved/canonical/cm1.exe"]
    else:
        Path(str(status["custom_executable"])).write_bytes(b"tampered executable")

    with pytest.raises(TradeCumulusOutputValidationError, match=message):
        validate_trade_cumulus_variation_outputs(manifest, metadata)


def _artifacts(
    tmp_path: Path,
    *,
    corruption: str | None = None,
    forcing_customization: bool = False,
) -> tuple[RunManifest, ResultMetadata]:
    run_dir = tmp_path / "runs" / "trade-output-validation"
    run_dir.mkdir(parents=True)
    namelist = run_dir / "namelist.input"
    sounding = run_dir / "input_sounding"
    checklist = run_dir / "runtime_file_checklist.json"
    namelist.write_text("isnd = 7,\n")
    sounding.write_text("1015.0 298.7 17.0\n0.0 298.7 17.0 -8.75 0.0\n")
    checklist.write_text("{}\n")
    controls = default_controls()
    customization_path: Path | None = None
    customization_status: dict[str, Any] | None = None
    execution_command: list[str] = []
    execution_sha256: str | None = None
    runtime_run_dir = tmp_path / "cm1-run"
    runtime_run_dir.mkdir()
    canonical_executable = runtime_run_dir / "cm1.exe"
    canonical_executable.write_bytes(_CANONICAL_EXECUTABLE_BYTES)
    execution_command = [str(canonical_executable)]
    execution_sha256 = _CANONICAL_EXECUTABLE_SHA256
    if forcing_customization:
        controls = controls.model_copy(
            update={
                "large_scale_vertical_motion_m_s": 0.01,
                "temperature_tendency_k_day": 3.0,
                "total_water_tendency_g_kg_day": -4.0,
            }
        )
        forcing = {
            "vertical_motion_m_s": 0.01,
            "temperature_tendency_k_day": 3.0,
            "total_water_tendency_g_kg_day": -4.0,
        }
        customization_path = run_dir / "trade_cumulus_forcing_customization.json"
        customization_path.write_text(
            json.dumps(
                {
                    "schema_version": TRADE_CUMULUS_FORCING_SCHEMA_VERSION,
                    "customization_kind": TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
                    "target": str(TRADE_CUMULUS_FORCING_TARGET),
                    "original_source_sha256": CRITICAL_SOURCE_HASHES[
                        str(TRADE_CUMULUS_FORCING_TARGET)
                    ],
                    "patched_source_sha256": "d" * 64,
                    "forcing": forcing,
                }
            )
        )
        build_root = tmp_path / "cm1_source_builds" / "fixture-build"
        build_root.mkdir(parents=True)
        executable = run_dir / CUSTOM_EXECUTABLE_FILENAME
        executable.write_bytes(b"custom executable")
        executable_sha256 = hashlib.sha256(executable.read_bytes()).hexdigest()
        execution_command = [str(executable)]
        execution_sha256 = executable_sha256
        customization_status = {
            "schema_version": "cm1_source_customization_status_v1",
            "customization_kind": TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND,
            "run_id": "trade-output-validation",
            "customization_manifest": str(customization_path),
            "original_target_sha256": CRITICAL_SOURCE_HASHES[str(TRADE_CUMULUS_FORCING_TARGET)],
            "patched_target_sha256": "d" * 64,
            "patched_files": [str(TRADE_CUMULUS_FORCING_TARGET)],
            "source_restored_after_build": "not_modified_isolated_build_tree",
            "build_command": ["make"],
            "build_root": str(build_root),
            "custom_executable": str(executable),
            "custom_executable_sha256": executable_sha256,
            "forcing": forcing,
            "no_silent_forcing_fallback": True,
        }
    generated_paths = [namelist, sounding, checklist]
    if customization_path is not None:
        generated_paths.append(customization_path)
    generated_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in generated_paths
    }

    paths: list[Path] = []
    diagnostic_paths: list[Path] = []
    times = [0.0, 60.0, 120.0]
    if corruption == "wrong_start":
        times[0] = 1.0
    elif corruption == "wrong_time":
        times[1] = 61.0
    elif corruption == "wrong_end":
        times[2] = 121.0
    for index, time_seconds in enumerate(times, start=1):
        path = (
            tmp_path / f"escaped_cm1out_{index:06d}.nc"
            if corruption == "escaped_output" and index == 2
            else run_dir / f"cm1out_{index:06d}.nc"
        )
        _write_history(
            path,
            time_seconds=time_seconds,
            missing_w=corruption == "missing_w" and index == 2,
            wrong_ql_units=corruption == "wrong_ql_units" and index == 2,
            nonfinite_w=corruption == "nonfinite_w" and index == 2,
            wrong_grid=corruption == "wrong_grid" and index == 2,
            wrong_spacing=corruption == "wrong_spacing" and index == 2,
            wrong_extent=corruption == "wrong_extent" and index == 2,
            wrong_top=corruption == "wrong_top" and index == 2,
            wrong_surface_flux=corruption == "wrong_surface_flux" and index == 2,
        )
        paths.append(path)

    diagnostic_times = [0.0, 60.0, 120.0]
    if corruption == "wrong_diagnostic_time":
        diagnostic_times[1] = 61.0
    for index, time_seconds in enumerate(diagnostic_times, start=1):
        if corruption == "missing_diagnostic" and index == 2:
            continue
        path = run_dir / f"cm1out_diag_{index:06d}.nc"
        _write_forcing_diagnostic(
            path,
            time_seconds=time_seconds,
            controls=controls,
            missing_field=corruption == "missing_diagnostic_field" and index == 2,
            wrong_units=corruption == "wrong_diagnostic_units" and index == 2,
            wrong_profile=corruption == "wrong_diagnostic_profile" and index == 2,
        )
        diagnostic_paths.append(path)

    scientific = {
        "controls": controls.model_dump(mode="json"),
        "fixed_assumptions": {"physics": "nonprecipitating"},
    }
    numerical = {
        "domain": "200 m × 200 m × 200 m",
        "grid": "2 × 2 × 2",
        "spacing": "100 × 100 × 100 m",
        "timestep_strategy": "target 1 s",
        "physics_source": "test fixture",
        "exact_domain": {
            "nx": 2,
            "ny": 2,
            "nz": 2,
            "dx_m": 100.0,
            "dy_m": 100.0,
            "dz_m": 100.0,
            "x_extent_m": 200.0,
            "y_extent_m": 200.0,
            "model_top_m": 200.0,
            "x_min_m": -100.0,
            "x_max_m": 100.0,
            "y_min_m": -100.0,
            "y_max_m": 100.0,
            "timestep_seconds": 1.0,
        },
    }
    exact_numerical = ExactNumericalDomain.model_validate(numerical["exact_domain"])
    forcing_diagnostics = forcing_diagnostic_contract(
        duration_seconds=120,
        numerical=exact_numerical,
    )
    identity = canonical_payload_sha256(
        {"scientific_design": scientific, "numerical_realization": numerical}
    )
    simulation_id = f"trade_cumulus_output_fixture_{identity[:8]}"
    envelope = VariationEnvelope(
        world_id="trade_cumulus",
        recipe_id="canonical_bomex_trade_cumulus",
        recipe_contract_version="1",
        simulation_id=simulation_id,
        parent_simulation_id="trade_cumulus_canonical_bomex",
        reference_simulation_id="trade_cumulus_canonical_bomex",
        display_name="Output validation fixture",
        scientific_design=immutable_layer(scientific),
        numerical_realization=immutable_layer(numerical),
        observation_plan=immutable_layer(
            {
                "duration_seconds": 120,
                "output_cadence_seconds": 60,
                "expected_history_count": 3,
                "retained_field_inventory": [
                    "ql",
                    "qv",
                    "th",
                    "prs",
                    "rho",
                    "u",
                    "v",
                    "w",
                    "tke",
                    "kmh",
                    "khh",
                    "cwp",
                    "hfx",
                    "qfx",
                    "rain",
                ],
            }
        ),
        world_payload={
            "controls": controls.model_dump(mode="json"),
            "forcing_diagnostic_contract": forcing_diagnostics,
        },
        differences=[],
        relationship_classification="replicate_realization",
        run_profile_id="fixture",
        run_profile_contract={},
        cost_estimate={},
        package_identity_sha256=identity,
        attempts=[
            VariationAttempt(
                attempt_id="trade-output-validation",
                run_id="trade-output-validation",
                relationship="initial",
                package_identity_sha256=identity,
            )
        ],
    )
    now = datetime(2026, 7, 28, tzinfo=UTC)
    manifest_path = run_dir / "run_manifest.json"
    manifest = RunManifest(
        run_id="trade-output-validation",
        scenario=ScenarioReference(
            id="trade_cumulus_recipe_variation_v1",
            schema_version="trade_cumulus_variation_v1",
        ),
        controls={},
        run_configuration={
            "cloud_world_id": "trade_cumulus",
            "simulation_id": simulation_id,
            "variation_envelope": envelope.model_dump(mode="json"),
            "generated_input_sha256": generated_hashes,
            "cm1_provenance": {
                "source_manifest_sha256": (
                    "0" * 64 if corruption == "wrong_provenance" else CM1_SOURCE_MANIFEST_SHA256
                ),
                "executable_sha256": _CANONICAL_EXECUTABLE_SHA256,
            },
            "forcing_diagnostic_contract": forcing_diagnostics,
            "cm1_source_customization_kind": (
                TRADE_CUMULUS_FORCING_CUSTOMIZATION_KIND if forcing_customization else None
            ),
        },
        physical_question="Can retained output support Explore?",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist),
            input_sounding=str(sounding),
            cm1_source_customization=(
                str(customization_path) if customization_path is not None else None
            ),
            runtime_file_checklist=[str(checklist)],
        ),
        runtime_paths=RuntimePaths(
            runtime_home=str(tmp_path),
            cm1_run_dir=str(runtime_run_dir),
        ),
        app=AppMetadata(app_version="test", commit="test"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.NEEDS_REVIEW,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        execution=ExecutionMetadata(
            command=execution_command,
            executable_sha256=execution_sha256,
            started_at=now,
            finished_at=now,
            exit_code=0,
        ),
        outputs=OutputMetadata(netcdf_paths=[str(path) for path in [*paths, *diagnostic_paths]]),
        required_output_fields=[
            "ql",
            "qv",
            "th",
            "prs",
            "rho",
            "u",
            "v",
            "w",
            "tke",
            "kmh",
            "khh",
            "cwp",
            "hfx",
            "qfx",
            "rain",
        ],
        created_at=now,
        updated_at=now,
        user=UserMetadata(name="Output validation fixture"),
        cm1_source_customization_status=customization_status,
        expected_outputs=[
            "native_numbered_cm1_model_netcdf",
            "cm1_domain_diagnostic_netcdf",
        ],
    )
    if corruption == "wrong_canonical_command":
        manifest.execution.command = [str(run_dir / "other-cm1.exe")]
    elif corruption == "tampered_canonical_executable":
        canonical_executable.write_bytes(b"tampered")
    elif corruption == "wrong_launch_executable_hash":
        manifest.execution.executable_sha256 = "f" * 64
    metadata = ResultMetadata(
        result_id="result-trade-output-validation",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        physical_question=manifest.physical_question,
        controls={},
        run_configuration=manifest.run_configuration,
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        required_output_fields=manifest.required_output_fields,
        model_output_paths=[str(path) for path in paths],
        netcdf_paths=[str(path) for path in [*paths, *diagnostic_paths]],
        model_output_file_count=3,
        time_steps=3,
        first_output_time_seconds=0.0,
        last_output_time_seconds=120.0,
        created_at=now,
        updated_at=now,
    )
    return manifest, metadata


def _write_history(
    path: Path,
    *,
    time_seconds: float,
    missing_w: bool,
    wrong_ql_units: bool,
    nonfinite_w: bool,
    wrong_grid: bool,
    wrong_spacing: bool,
    wrong_extent: bool,
    wrong_top: bool,
    wrong_surface_flux: bool,
) -> None:
    x_count = 3 if wrong_grid else 2
    shape = (1, 2, 2, x_count)
    scalar = np.ones(shape, dtype=np.float32)
    cloud = np.zeros(shape, dtype=np.float32)
    vertical = scalar.copy()
    if nonfinite_w:
        vertical[0, 0, 0, 0] = np.nan
    data_vars: dict[str, Any] = {
        "ql": (("time", "zh", "yh", "xh"), cloud),
        "qv": (("time", "zh", "yh", "xh"), scalar * 0.01),
        "th": (("time", "zh", "yh", "xh"), scalar * 300),
        "prs": (("time", "zh", "yh", "xh"), scalar * 90_000),
        "rho": (("time", "zh", "yh", "xh"), scalar * 1.2),
        "u": (("time", "zh", "yh", "xh"), scalar * -7),
        "v": (("time", "zh", "yh", "xh"), scalar * 1),
        "tke": (("time", "zh", "yh", "xh"), scalar),
        "kmh": (("time", "zh", "yh", "xh"), scalar),
        "khh": (("time", "zh", "yh", "xh"), scalar),
        "cwp": (("time", "yh", "xh"), np.ones((1, 2, x_count), dtype=np.float32)),
        "hfx": (
            ("time", "yh", "xh"),
            np.full(
                (1, 2, x_count),
                1.2 * 1_004.0 * (0.009 if wrong_surface_flux else 0.008),
                dtype=np.float32,
            ),
        ),
        "qfx": (
            ("time", "yh", "xh"),
            np.full((1, 2, x_count), 1.2 * 0.052 / 1_000.0, dtype=np.float32),
        ),
        "rain": (("time", "yh", "xh"), np.zeros((1, 2, x_count), dtype=np.float32)),
    }
    if not missing_w:
        data_vars["w"] = (("time", "zh", "yh", "xh"), vertical)
    dataset = xr.Dataset(
        data_vars,
        coords={
            "time": ("time", [time_seconds], {"units": "seconds"}),
            "zh": (
                "zh",
                [0.1, 0.2] if wrong_top else [0.05, 0.15],
                {"units": "km"},
            ),
            "yh": ("yh", [-0.05, 0.05], {"units": "km"}),
            "xh": (
                "xh",
                (
                    [-0.1, 0.0, 0.1]
                    if wrong_grid
                    else [-0.06, 0.06]
                    if wrong_spacing
                    else [0.05, 0.15]
                    if wrong_extent
                    else [-0.05, 0.05]
                ),
                {"units": "km"},
            ),
        },
    )
    for field in ("ql", "qv"):
        dataset[field].attrs["units"] = "kg kg-1"
    dataset["ql"].attrs["units"] = "g kg-1" if wrong_ql_units else "kg kg-1"
    dataset["th"].attrs["units"] = "K"
    dataset["prs"].attrs["units"] = "Pa"
    dataset["rho"].attrs["units"] = "kg m-3"
    dataset["hfx"].attrs["units"] = "W m-2"
    dataset["qfx"].attrs["units"] = "kg m-2 s-1"
    for field in ("u", "v"):
        dataset[field].attrs["units"] = "m s-1"
    if "w" in dataset:
        dataset["w"].attrs["units"] = "m s-1"
    dataset.to_netcdf(path)


def _write_forcing_diagnostic(
    path: Path,
    *,
    time_seconds: float,
    controls: Any,
    missing_field: bool,
    wrong_units: bool,
    wrong_profile: bool,
) -> None:
    zh_m = np.asarray([50.0, 150.0])
    zf_m = np.asarray([0.0, 100.0, 200.0])
    profiles = expected_forcing_profiles(controls, zh_m=zh_m, zf_m=zf_m)
    if wrong_profile:
        profiles["wprof"] = profiles["wprof"].copy()
        profiles["wprof"][1] += 0.01
    data_vars: dict[str, Any] = {
        "wprof": (
            ("time", "zf", "yh", "xh"),
            profiles["wprof"].reshape(1, 3, 1, 1).astype(np.float32),
        ),
        "ptb_frc": (
            ("time", "zh", "yh", "xh"),
            profiles["ptb_frc"].reshape(1, 2, 1, 1).astype(np.float32),
        ),
        "qvb_frc": (
            ("time", "zh", "yh", "xh"),
            profiles["qvb_frc"].reshape(1, 2, 1, 1).astype(np.float32),
        ),
    }
    if missing_field:
        data_vars.pop("qvb_frc")
    dataset = xr.Dataset(
        data_vars,
        coords={
            "time": ("time", [time_seconds], {"units": "seconds"}),
            "zh": ("zh", zh_m, {"units": "m"}),
            "zf": ("zf", zf_m, {"units": "m"}),
            "yh": ("yh", [0.0], {"units": "degree_north"}),
            "xh": ("xh", [0.0], {"units": "degree_east"}),
        },
    )
    dataset["wprof"].attrs["units"] = "cm/s" if wrong_units else "m/s"
    dataset["ptb_frc"].attrs["units"] = "K/s"
    if "qvb_frc" in dataset:
        dataset["qvb_frc"].attrs["units"] = "g/g/s"
    dataset.to_netcdf(path)

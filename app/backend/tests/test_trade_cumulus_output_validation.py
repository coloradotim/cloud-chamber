from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.result_ingest import ResultMetadata
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


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_trade_cumulus_output_validation_cache()


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
    assert calls == 3


@pytest.mark.parametrize(
    ("corruption", "message"),
    [
        ("missing_w", "Required native field w is absent"),
        ("wrong_ql_units", "unsupported units"),
        ("nonfinite_w", "contains nonfinite values"),
        ("wrong_time", "reviewed output cadence"),
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


def _artifacts(
    tmp_path: Path,
    *,
    corruption: str | None = None,
) -> tuple[RunManifest, ResultMetadata]:
    run_dir = tmp_path / "runs" / "trade-output-validation"
    run_dir.mkdir(parents=True)
    namelist = run_dir / "namelist.input"
    sounding = run_dir / "input_sounding"
    checklist = run_dir / "runtime_file_checklist.json"
    namelist.write_text("isnd = 7,\n")
    sounding.write_text("1015.0 298.7 17.0\n0.0 298.7 17.0 -8.75 0.0\n")
    checklist.write_text("{}\n")
    generated_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (namelist, sounding, checklist)
    }

    paths: list[Path] = []
    for index, time_seconds in enumerate((0.0, 60.0, 120.0), start=1):
        path = run_dir / f"cm1out_{index:06d}.nc"
        _write_history(
            path,
            time_seconds=(90.0 if corruption == "wrong_time" and index == 2 else time_seconds),
            missing_w=corruption == "missing_w" and index == 2,
            wrong_ql_units=corruption == "wrong_ql_units" and index == 2,
            nonfinite_w=corruption == "nonfinite_w" and index == 2,
        )
        paths.append(path)

    scientific = {
        "controls": default_controls().model_dump(mode="json"),
        "fixed_assumptions": {"physics": "nonprecipitating"},
    }
    numerical = {"grid": "fixture"}
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
        world_payload={"controls": default_controls().model_dump(mode="json")},
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
                "source_manifest_sha256": "a" * 64,
                "executable_sha256": "b" * 64,
            },
        },
        physical_question="Can retained output support Explore?",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist),
            input_sounding=str(sounding),
            runtime_file_checklist=[str(checklist)],
        ),
        runtime_paths=RuntimePaths(runtime_home=str(tmp_path)),
        app=AppMetadata(app_version="test", commit="test"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.NEEDS_REVIEW,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        execution=ExecutionMetadata(started_at=now, finished_at=now, exit_code=0),
        outputs=OutputMetadata(netcdf_paths=[str(path) for path in paths]),
        required_output_fields=[
            "ql",
            "qv",
            "th",
            "prs",
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
    )
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
        netcdf_paths=[str(path) for path in paths],
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
) -> None:
    shape = (1, 2, 2, 2)
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
        "u": (("time", "zh", "yh", "xh"), scalar * -7),
        "v": (("time", "zh", "yh", "xh"), scalar * 1),
        "tke": (("time", "zh", "yh", "xh"), scalar),
        "kmh": (("time", "zh", "yh", "xh"), scalar),
        "khh": (("time", "zh", "yh", "xh"), scalar),
        "cwp": (("time", "yh", "xh"), np.ones((1, 2, 2), dtype=np.float32)),
        "hfx": (("time", "yh", "xh"), np.ones((1, 2, 2), dtype=np.float32)),
        "qfx": (("time", "yh", "xh"), np.ones((1, 2, 2), dtype=np.float32)),
        "rain": (("time", "yh", "xh"), np.zeros((1, 2, 2), dtype=np.float32)),
    }
    if not missing_w:
        data_vars["w"] = (("time", "zh", "yh", "xh"), vertical)
    dataset = xr.Dataset(
        data_vars,
        coords={
            "time": ("time", [time_seconds], {"units": "seconds"}),
            "zh": ("zh", [0.1, 0.2], {"units": "km"}),
            "yh": ("yh", [-0.1, 0.1], {"units": "km"}),
            "xh": ("xh", [-0.1, 0.1], {"units": "km"}),
        },
    )
    for field in ("ql", "qv"):
        dataset[field].attrs["units"] = "kg kg-1"
    dataset["ql"].attrs["units"] = "g kg-1" if wrong_ql_units else "kg kg-1"
    dataset["th"].attrs["units"] = "K"
    dataset["prs"].attrs["units"] = "Pa"
    for field in ("u", "v"):
        dataset[field].attrs["units"] = "m s-1"
    if "w" in dataset:
        dataset["w"].attrs["units"] = "m s-1"
    dataset.to_netcdf(path)

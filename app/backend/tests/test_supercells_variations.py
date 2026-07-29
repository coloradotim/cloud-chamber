from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.run_cost import profile_by_id
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
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    NATIVE_FIELD_CONTRACT,
    PRESENTATION_CASE_ID,
    PRESENTATION_RUN_ID,
    QUARTER_CIRCLE_SIMULATION_ID,
    STRAIGHT_LINE_PRESENTATION_CASE_ID,
    STRAIGHT_LINE_PRESENTATION_RUN_ID,
    STRAIGHT_LINE_SIMULATION_ID,
    StormExaminationError,
    _validate_generated_history_contract,
    storm_examination_variation_inventory,
)
from cloud_chamber.supercell_benchmark import (
    CM1_EXECUTABLE_SHA256,
    CM1_SOURCE_MANIFEST_SHA256,
)
from cloud_chamber.supercells_attempt_provenance import (
    SupercellsAttemptProvenanceError,
    validate_supercells_attempt_provenance,
)
from cloud_chamber.supercells_recipes import SupercellsControls, default_controls
from cloud_chamber.supercells_source_customization import (
    render_supercells_source,
)
from cloud_chamber.supercells_variations import (
    VARIATION_CASE_ID,
    SupercellsVariationPackage,
    SupercellsVariationRequest,
    create_supercells_variation,
    preflight_supercells_variation,
    preview_supercells_variation,
    supercells_variation_template,
)
from cloud_chamber.supercells_world import (
    SupercellSimulationRecord,
    _builtin_simulation_contract,
    _intended_simulation_sha256,
    supercells_world_detail,
)
from cloud_chamber.variation_envelope import grouped_differences
from cloud_chamber.world_compare import world_compare_descriptor


@pytest.fixture(autouse=True)
def _accepted_builtin_parent_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_inventory",
        lambda _settings, _simulation_id: tuple(
            (tmp_path / f"cm1out_{index + 1:06d}.nc", float(index * 120)) for index in range(91)
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world._builtin_parent_eligibility",
        lambda _settings, _simulation_id, _run_id: (
            True,
            "Accepted retained presentation evidence.",
        ),
    )


def test_templates_inherit_both_accepted_real_parents_and_all_profiles(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)

    quarter = supercells_variation_template(settings, QUARTER_CIRCLE_SIMULATION_ID)
    straight = supercells_variation_template(settings, STRAIGHT_LINE_SIMULATION_ID)

    assert quarter.can_create_variation is True
    assert straight.can_create_variation is True
    assert quarter.controls.hodograph_family == "quarter_circle"
    assert straight.controls.hodograph_family == "straight"
    assert quarter.default_run_profile_id == "supercells_presentation_v1"
    assert {item.profile.role for item in quarter.run_profiles} == {
        "Quick",
        "Standard",
        "Presentation",
        "Extended",
    }
    assert all(
        item.profile.recipe_id == "idealized_isolated_supercell" for item in quarter.run_profiles
    )


def test_preview_reports_reference_parent_requested_and_achieved_values(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    controls = default_controls().model_copy(
        update={
            "shear_0_2_km_m_s": 20.0,
            "surface_based_cape_j_kg": 4_000.0,
            "thermal_perturbation_amplitude_k": -1.0,
        }
    )
    preview = preview_supercells_variation(
        settings,
        _request(controls=controls, profile_id="supercells_standard_v1"),
    )

    assert preview.blocking_errors == []
    assert preview.reference_controls["shear_0_2_km_m_s"] == pytest.approx(
        default_controls().shear_0_2_km_m_s
    )
    assert preview.parent_controls == preview.reference_controls
    assert preview.requested_controls["surface_based_cape_j_kg"] == 4_000.0
    assert preview.achieved_controls["surface_based_cape_j_kg"] == pytest.approx(
        4_000.0,
        abs=0.5,
    )
    assert preview.relationship_classification == "mixed_variation"
    assert preview.sounding[-1]["height_m"] > 20_000.0
    assert preview.initiation["amplitude_k"] == -1.0
    assert any("cold perturbation" in item.lower() for item in preview.warnings)


def test_unchanged_specification_and_uncharacterized_extended_profile_block(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)

    unchanged = preview_supercells_variation(
        settings,
        _request(
            controls=default_controls(),
            profile_id="supercells_presentation_v1",
        ),
    )
    extended = preview_supercells_variation(
        settings,
        _request(
            controls=default_controls().model_copy(
                update={"thermal_perturbation_amplitude_k": 2.0}
            ),
            profile_id="supercells_extended_v1",
        ),
    )

    assert unchanged.blocking_errors == [
        "Change at least one scientific control or run profile before packaging."
    ]
    assert any("uncharacterized" in item for item in extended.blocking_errors)


def test_observation_only_change_packages_as_an_alternate_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    presentation = profile_by_id("supercells_presentation_v1")
    observation_only = presentation.model_copy(
        update={
            "profile_id": "supercells_observation_only_test",
            "observation_plan": presentation.observation_plan.model_copy(
                update={
                    "output_cadence_seconds": 60,
                    "expected_history_count": 181,
                }
            ),
        }
    )
    original_profile_by_id = profile_by_id
    monkeypatch.setattr(
        "cloud_chamber.supercells_variations.profile_by_id",
        lambda profile_id: (
            observation_only
            if profile_id == observation_only.profile_id
            else original_profile_by_id(profile_id)
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.profile_by_id",
        lambda profile_id: (
            observation_only
            if profile_id == observation_only.profile_id
            else original_profile_by_id(profile_id)
        ),
    )
    request = _request(
        controls=default_controls(),
        profile_id=observation_only.profile_id,
    )

    preview = preview_supercells_variation(settings, request)
    package = create_supercells_variation(settings, request)
    manifest = load_run_manifest(Path(package.manifest_path))

    assert preview.relationship_classification == "observation_only_attempt"
    assert preview.blocking_errors == []
    assert package.simulation_id == QUARTER_CIRCLE_SIMULATION_ID
    assert package.envelope.parent_simulation_id == QUARTER_CIRCLE_SIMULATION_ID
    assert package.envelope.display_name == "Quarter-Circle Supercell"
    assert package.envelope.attempts[-1].relationship == "alternate_observation_attempt"
    assert manifest.run_configuration["attempt_relationship"] == ("alternate_observation_attempt")
    assert manifest.run_configuration["simulation_id"] == QUARTER_CIRCLE_SIMULATION_ID


def test_package_persists_exact_profiles_source_readback_and_launch_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    controls = default_controls().model_copy(update={"thermal_perturbation_amplitude_k": 2.0})
    request = _request(
        controls=controls,
        profile_id="supercells_presentation_v1",
    )

    first = create_supercells_variation(settings, request)
    second = create_supercells_variation(settings, request)
    manifest = load_run_manifest(Path(first.manifest_path))

    assert first.simulation_id == second.simulation_id
    assert first.run_id != second.run_id
    assert first.envelope.package_identity_sha256 == second.envelope.package_identity_sha256
    assert first.envelope.relationship_classification == ("controlled_initiation_sensitivity")
    assert first.preflight["passed"] is True
    assert first.preflight["checks"]["sounding_extends_above_model_top"] is True
    assert preflight_supercells_variation(Path(first.manifest_path))["passed"] is True
    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.recipe_id == "idealized_isolated_supercell"
    assert manifest.run_configuration["cm1_source_customization_kind"] == (
        "supercells_environment_and_thermal_v1"
    )
    assert manifest.run_configuration["launch_review_snapshot_id"]
    assert manifest.run_configuration["launch_specification"]["profile_id"] == (
        "supercells_presentation_v1"
    )
    assert {"winterp", "uh", "cref", "rain"} <= set(manifest.required_output_fields)
    run_dir = Path(first.package_dir)
    assert not list(run_dir.glob("cm1out*"))
    case_manifest = (run_dir / "case_manifest.json").read_text()
    assert '"variation_envelope":' not in case_manifest
    assert '"variation_envelope_authority":' in case_manifest
    sounding_rows = (run_dir / "input_sounding").read_text().splitlines()
    assert float(sounding_rows[1].split()[0]) == 0.0
    assert float(sounding_rows[-1].split()[0]) > 20_000.0
    one_km = next(row for row in sounding_rows[1:] if float(row.split()[0]) == 1_000.0).split()
    assert tuple(float(value) for value in one_km[1:3]) == pytest.approx(
        (301.9252711278505, 14.0),
        rel=0.0,
        abs=1.0e-9,
    )


def test_completed_attempt_binds_isolated_build_and_executable_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    package = create_supercells_variation(
        settings,
        _request(
            controls=default_controls().model_copy(
                update={"thermal_perturbation_amplitude_k": 2.0}
            ),
            profile_id="supercells_quick_v1",
        ),
    )
    manifest = _apply_fake_custom_build(package, settings)

    report = validate_supercells_attempt_provenance(manifest)

    assert report["source_build_isolated"] is True
    assert report["executable_kind"] == "isolated_supercells_customization"

    manifest.execution.command = [str(Path(package.package_dir) / "other-cm1.exe")]
    with pytest.raises(
        SupercellsAttemptProvenanceError,
        match="did not use",
    ):
        validate_supercells_attempt_provenance(manifest)


@pytest.mark.parametrize(
    "mutated_asset",
    ["input_sounding", "customization", "build_source", "executable"],
)
def test_completed_attempt_revalidates_provenance_before_cached_inventory(
    mutated_asset: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    package = create_supercells_variation(
        settings,
        _request(
            controls=default_controls().model_copy(
                update={"thermal_perturbation_amplitude_k": 2.0}
            ),
            profile_id="supercells_quick_v1",
        ),
    )
    manifest = _apply_fake_custom_build(package, settings)
    _mark_package_completed_for_world_wiring(package)
    inventory = tuple(
        (
            Path(package.package_dir) / f"cm1out_{index + 1:06d}.nc",
            float(index * 300),
        )
        for index in range(25)
    )
    for path, _time_seconds in inventory:
        path.write_bytes(b"cached-history-fixture")
    monkeypatch.setattr(
        "cloud_chamber.storm_examination._cached_inventory",
        lambda _run_dir, _fingerprint, _contract: inventory,
    )

    assert (
        storm_examination_variation_inventory(
            settings,
            Path(package.manifest_path),
        )
        == inventory
    )

    status = manifest.cm1_source_customization_status
    assert isinstance(status, dict)
    paths = {
        "input_sounding": Path(manifest.generated_inputs.input_sounding or ""),
        "customization": Path(manifest.generated_inputs.cm1_source_customization or ""),
        "build_source": Path(status["build_root"]) / "src" / "init3d.F",
        "executable": Path(status["custom_executable"]),
    }
    paths[mutated_asset].write_bytes(b"mutated-after-validation")
    with pytest.raises(StormExaminationError, match="provenance is invalid"):
        storm_examination_variation_inventory(
            settings,
            Path(package.manifest_path),
        )


def test_attempt_grouping_hash_covers_simulation_identity_not_attempt_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    package = create_supercells_variation(
        settings,
        _request(
            controls=default_controls().model_copy(
                update={"thermal_perturbation_amplitude_k": 2.0}
            ),
            profile_id="supercells_quick_v1",
        ),
    )
    altered_question = package.envelope.model_copy(
        update={"question": "A materially different intended scientific question."}
    )
    altered_science = package.envelope.model_copy(
        update={
            "scientific_design": package.envelope.scientific_design.model_copy(
                update={
                    "payload": {
                        **package.envelope.scientific_design.payload,
                        "generators": {
                            **package.envelope.scientific_design.payload["generators"],
                            "initiation": "different_generator",
                        },
                    }
                }
            )
        }
    )

    assert _intended_simulation_sha256(package.envelope) == (
        _intended_simulation_sha256(altered_question)
    )
    assert _intended_simulation_sha256(package.envelope) != (
        _intended_simulation_sha256(altered_science)
    )


def test_non_direct_compare_uses_real_generated_semantic_layers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    request = _request(
        controls=default_controls().model_copy(
            update={
                "hodograph_family": "straight",
                "thermal_perturbation_amplitude_k": 2.0,
            }
        ),
        profile_id="supercells_presentation_v1",
    ).model_copy(update={"parent_simulation_id": STRAIGHT_LINE_SIMULATION_ID})
    package = create_supercells_variation(settings, request)
    (
        scientific,
        numerical,
        observation,
        world_payload,
        differences,
        profile,
    ) = _builtin_simulation_contract(QUARTER_CIRCLE_SIMULATION_ID)
    reference = SupercellSimulationRecord(
        simulation_id=QUARTER_CIRCLE_SIMULATION_ID,
        display_name="Quarter-Circle Supercell",
        role="reference",
        run_id=PRESENTATION_RUN_ID,
        case_id=PRESENTATION_CASE_ID,
        technical_state="available",
        technical_state_message="Available",
        explore_available=True,
        saved_output_count=91,
        model_start_seconds=0,
        model_end_seconds=10_800,
        history_cadence_seconds=120,
        parent_eligibility_reason="Accepted.",
        scientific_design=scientific,
        numerical_realization=numerical,
        observation_plan=observation,
        world_payload=world_payload,
        differences=differences,
        run_profile_contract=profile,
    )
    envelope = package.envelope
    child = SupercellSimulationRecord(
        simulation_id=envelope.simulation_id,
        display_name=envelope.display_name,
        role="variation",
        run_id=package.run_id,
        case_id=VARIATION_CASE_ID,
        parent_simulation_id=STRAIGHT_LINE_SIMULATION_ID,
        technical_state="available",
        technical_state_message="Available",
        explore_available=True,
        saved_output_count=91,
        model_start_seconds=0,
        model_end_seconds=10_800,
        history_cadence_seconds=120,
        parent_eligibility_reason="Accepted.",
        scientific_design=envelope.scientific_design.payload,
        numerical_realization=envelope.numerical_realization.payload,
        observation_plan=envelope.observation_plan.payload,
        world_payload=envelope.world_payload,
        differences=grouped_differences(envelope.differences),
        run_profile_contract=envelope.run_profile_contract,
    )
    monkeypatch.setattr(
        "cloud_chamber.world_compare.supercells_world_detail",
        lambda _settings: SimpleNamespace(
            display_name="Supercells",
            simulations=[reference, child],
            reference_simulation=reference,
        ),
    )

    descriptor = world_compare_descriptor(
        settings,
        world_slug="supercells",
        left_simulation_id=reference.simulation_id,
        right_simulation_id=child.simulation_id,
    )

    paths = {difference.path for difference in descriptor.material_differences}
    assert "scientific_design.controls.hodograph_family" in paths
    assert "scientific_design.controls.thermal_perturbation_amplitude_k" in paths
    assert not any("achieved_controls" in path for path in paths)
    assert not any("generators" in path for path in paths)
    assert not any("fixed_assumptions" in path for path in paths)


def test_impossible_thermal_clearance_blocks_before_writing_a_package(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    controls = default_controls().model_copy(
        update={
            "thermal_horizontal_radius_km": 40.0,
            "thermal_center_x_km": 60.0,
        }
    )
    request = _request(controls=controls, profile_id="supercells_quick_v1")
    preview = preview_supercells_variation(settings, request)

    assert any("horizontal domain" in item for item in preview.blocking_errors)
    with pytest.raises(Exception, match="horizontal domain"):
        create_supercells_variation(settings, request)
    assert not any((settings.runtime_home / "runs").glob("sc-*"))


def test_completed_weak_variation_becomes_available_in_all_three_lenses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_builtin_parents(settings)
    _trust_packaging(monkeypatch, settings)
    package = create_supercells_variation(
        settings,
        _request(
            controls=default_controls().model_copy(update={"surface_based_cape_j_kg": 0.0}),
            profile_id="supercells_quick_v1",
        ),
    )
    _mark_package_completed_for_world_wiring(package)
    assert settings.cm1_root is not None
    source_hash = hashlib.sha256((settings.cm1_root / "src" / "init3d.F").read_bytes()).hexdigest()
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.PINNED_INIT3D_F_SHA256",
        source_hash,
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_variation_inventory",
        lambda _settings, _path: tuple(
            (Path(package.package_dir) / f"cm1out_{index + 1:06d}.nc", float(index * 300))
            for index in range(25)
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_variation_interactions",
        lambda _settings, _path: SimpleNamespace(
            classification="clear",
            blocking_classification="clear",
            useful_window_end_seconds=7_200,
            lateral_boundary_first_time_seconds=None,
            damping_layer_first_time_seconds=None,
            blocking_lateral_boundary_first_time_seconds=None,
            blocking_damping_layer_first_time_seconds=None,
        ),
    )

    detail = supercells_world_detail(settings)

    child = next(
        simulation
        for simulation in detail.simulations
        if simulation.simulation_id == package.simulation_id
    )
    assert child.technical_state == "available"
    assert child.explore_available is True
    assert child.saved_output_count == 25
    assert child.can_create_variation is True
    assert "reconstructible" in child.parent_eligibility_reason


def test_generated_output_rejects_readable_but_wrong_native_grid(
    tmp_path: Path,
) -> None:
    exact_domain = profile_by_id("supercells_quick_v1").numerical_realization.exact_domain
    assert exact_domain is not None
    dataset = _native_dataset(
        time_seconds=0,
        xh=np.asarray([-1.0, 1.0], dtype=np.float32),
        yh=np.asarray([-1.0, 1.0], dtype=np.float32),
        zh=np.asarray([0.25, 1.25], dtype=np.float32),
    )
    with pytest.raises(StormExaminationError, match="exact native grid"):
        _validate_generated_history_contract(dataset, 0.0, exact_domain)


def test_generated_output_accepts_the_selected_profile_exact_native_grid() -> None:
    exact_domain = profile_by_id("supercells_quick_v1").numerical_realization.exact_domain
    assert exact_domain is not None
    dataset = _native_dataset(
        time_seconds=0,
        xh=np.linspace(
            exact_domain.x_min_m + exact_domain.dx_m / 2,
            exact_domain.x_max_m - exact_domain.dx_m / 2,
            exact_domain.nx,
            dtype=np.float32,
        )
        / 1_000,
        yh=np.linspace(
            exact_domain.y_min_m + exact_domain.dy_m / 2,
            exact_domain.y_max_m - exact_domain.dy_m / 2,
            exact_domain.ny,
            dtype=np.float32,
        )
        / 1_000,
        zh=np.linspace(
            exact_domain.dz_m / 2,
            exact_domain.model_top_m - exact_domain.dz_m / 2,
            exact_domain.nz,
            dtype=np.float32,
        )
        / 1_000,
    )

    _validate_generated_history_contract(dataset, 0.0, exact_domain)


def _request(*, controls: SupercellsControls, profile_id: str) -> SupercellsVariationRequest:
    return SupercellsVariationRequest(
        parent_simulation_id=QUARTER_CIRCLE_SIMULATION_ID,
        simulation_name="Direct Supercells Experiment",
        user_question="How does the storm respond?",
        run_profile_id=profile_id,
        controls=controls,
    )


def _mark_package_completed_for_world_wiring(
    package: SupercellsVariationPackage,
) -> None:
    manifest_path = Path(package.manifest_path)
    manifest = load_run_manifest(manifest_path)
    manifest.lifecycle_state = LifecycleState.COMPLETED
    manifest.provenance.product_state = ProductState.COMPLETED_CM1_RESULT
    manifest.execution.exit_code = 0
    manifest.execution.started_at = manifest.created_at
    manifest.execution.finished_at = manifest.updated_at
    manifest.updated_at = datetime.now(UTC)
    write_run_manifest(manifest_path, manifest)


def _native_dataset(
    *,
    time_seconds: int,
    xh: np.ndarray,
    yh: np.ndarray,
    zh: np.ndarray,
) -> xr.Dataset:
    shape_3d = (1, len(zh), len(yh), len(xh))
    shape_2d = (1, len(yh), len(xh))
    data_vars = {
        name: (
            dims,
            np.broadcast_to(
                np.zeros((1, 1, 1, 1) if "zh" in dims else (1, 1, 1), dtype=np.float32),
                shape_3d if "zh" in dims else shape_2d,
            ),
            {"units": units},
        )
        for name, (dims, units) in NATIVE_FIELD_CONTRACT.items()
    }
    return xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": (
                "time",
                np.asarray([time_seconds], dtype=np.float32),
                {"units": "seconds"},
            ),
            "xh": ("xh", xh, {"units": "km"}),
            "yh": ("yh", yh, {"units": "km"}),
            "zh": ("zh", zh, {"units": "km"}),
        },
    )


def _apply_fake_custom_build(
    package: SupercellsVariationPackage,
    settings: CloudChamberSettings,
) -> RunManifest:
    manifest_path = Path(package.manifest_path)
    manifest = load_run_manifest(manifest_path)
    run_dir = manifest_path.parent
    customization_path = Path(manifest.generated_inputs.cm1_source_customization or "")
    customization = json.loads(customization_path.read_text())
    build_root = settings.runtime_home / "cm1_source_builds" / manifest.run_id
    built_source = build_root / "src" / "init3d.F"
    built_source.parent.mkdir(parents=True)
    assert settings.cm1_root is not None
    built_source.write_text(
        render_supercells_source(
            (settings.cm1_root / "src" / "init3d.F").read_text(),
            customization["initiation"],
        )
    )
    executable = run_dir / "cm1_cloud_chamber_custom.exe"
    executable.write_bytes(b"custom-supercells-executable")
    executable_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    manifest.cm1_source_customization_status = {
        "schema_version": "cm1_source_customization_status_v1",
        "customization_kind": "supercells_environment_and_thermal_v1",
        "run_id": manifest.run_id,
        "build_root": str(build_root),
        "customization_manifest": str(customization_path),
        "original_target_sha256": customization["original_source_sha256"],
        "patched_target_sha256": customization["patched_source_sha256"],
        "patched_files": ["src/init3d.F"],
        "source_restored_after_build": "not_modified_isolated_build_tree",
        "build_command": ["make"],
        "custom_executable": str(executable),
        "custom_executable_sha256": executable_hash,
        "wind_profile_sha256": customization["wind_profile_sha256"],
        "thermodynamic_profile_sha256": customization["thermodynamic_profile_sha256"],
        "initiation": customization["initiation"],
        "no_silent_profile_or_thermal_fallback": True,
    }
    manifest.execution.command = [str(executable)]
    manifest.execution.executable_sha256 = executable_hash
    write_run_manifest(manifest_path, manifest)
    return load_run_manifest(manifest_path)


def _settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1r21.1"
    cm1_run_dir = cm1_root / "run"
    source = _init3d_source()
    (cm1_root / "src").mkdir(parents=True)
    (cm1_root / "src" / "init3d.F").write_text(source)
    cm1_run_dir.mkdir(parents=True)
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def _write_builtin_parents(settings: CloudChamberSettings) -> None:
    _write_parent(
        settings,
        run_id=PRESENTATION_RUN_ID,
        case_id=PRESENTATION_CASE_ID,
    )
    _write_parent(
        settings,
        run_id=STRAIGHT_LINE_PRESENTATION_RUN_ID,
        case_id=STRAIGHT_LINE_PRESENTATION_CASE_ID,
    )


def _write_parent(
    settings: CloudChamberSettings,
    *,
    run_id: str,
    case_id: str,
) -> None:
    run_dir = settings.runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    namelist = run_dir / "namelist.input"
    namelist.write_text(_parent_namelist())
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF fixture")
    manifest_path = run_dir / "run_manifest.json"
    now = datetime(2026, 7, 28, tzinfo=UTC)
    write_run_manifest(
        manifest_path,
        RunManifest(
            run_id=run_id,
            scenario=ScenarioReference(id=case_id, schema_version="test-v1"),
            controls={},
            run_configuration={},
            physical_question="How does the idealized storm evolve?",
            expected_diagnostics=[],
            generated_inputs=GeneratedInputs(
                run_directory=str(run_dir),
                manifest_path=str(manifest_path),
                namelist_input=str(namelist),
            ),
            runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home)),
            app=AppMetadata(app_version="test", commit="parent-commit"),
            lifecycle_state=LifecycleState.COMPLETED,
            validation_status=ValidationStatus.NEEDS_REVIEW,
            provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
            outputs=OutputMetadata(netcdf_paths=[str(output)]),
            created_at=now,
            updated_at=now,
            user=UserMetadata(name=run_id),
        ),
    )


def _trust_packaging(
    monkeypatch: pytest.MonkeyPatch,
    settings: CloudChamberSettings,
) -> None:
    assert settings.cm1_root is not None
    source = (settings.cm1_root / "src" / "init3d.F").read_text()
    monkeypatch.setattr(
        "cloud_chamber.supercells_source_customization.PINNED_INIT3D_F_SHA256",
        hashlib.sha256(source.encode()).hexdigest(),
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_attempt_provenance.PINNED_INIT3D_F_SHA256",
        hashlib.sha256(source.encode()).hexdigest(),
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_variations.verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_variations.collect_cm1_provenance",
        lambda _settings: SimpleNamespace(
            report_record=lambda: {
                "source_manifest_sha256": CM1_SOURCE_MANIFEST_SHA256,
                "executable_sha256": CM1_EXECUTABLE_SHA256,
            }
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=100 * 1024**3),
    )


def _init3d_source() -> str:
    return """      IF(iinit.eq.1)THEN

        ric     =  centerx  ! center of bubble in x-direction (m)
        rjc     =  centery  ! center of bubble in y-direction (m)
        zc      =   1400.0  ! height of center of bubble above ground (m)
        bhrad   =  10000.0  ! horizontal radius of bubble (m)
        bvrad   =   1400.0  ! vertical radius of bubble (m)
        bptpert =      1.0  ! max potential temp perturbation (K)
"""


def _parent_namelist() -> str:
    values = {
        "nx": "240",
        "ny": "240",
        "nz": "60",
        "dx": "500.0",
        "dy": "500.0",
        "dz": "333.3333333333",
        "dtl": "3.0",
        "timax": "10800.0",
        "tapfrq": "120.0",
        "iinit": "1",
        "isnd": "5",
        "iwnd": "2",
        "imoist": "1",
        "ptype": "5",
        "stretch_z": "0",
        "ztop": "18000.0",
        "zd": "15000.0",
        "umove": "12.5",
        "vmove": "3.0",
        "output_format": "2",
        "output_filetype": "2",
        "output_rain": "1",
        "output_th": "1",
        "output_prs": "1",
        "output_qv": "1",
        "output_q": "1",
        "output_dbz": "1",
        "output_uinterp": "1",
        "output_vinterp": "1",
        "output_winterp": "1",
        "output_vort": "1",
        "output_uh": "1",
    }
    return (
        " &param0\n" + "".join(f" {name} = {value},\n" for name, value in values.items()) + " /\n"
    )

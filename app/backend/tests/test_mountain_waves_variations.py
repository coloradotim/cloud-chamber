from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from cloud_chamber.mountain_waves_recipes import (
    BOULDER_RECIPE_ID,
    DRY_RECIPE_ID,
    BoulderMoistControls,
    DryRidgeControls,
    MountainWavesRecipeControls,
    RecipeId,
    normalize_recipe_controls,
)
from cloud_chamber.mountain_waves_variations import (
    MountainWavesVariationRequest,
    create_mountain_waves_variation,
    mountain_waves_variation_template,
    preflight_mountain_waves_variation,
    preview_mountain_waves_variation,
)
from cloud_chamber.mountain_waves_world import (
    DRY_CASE_ID,
    DRY_RUN_ID,
    DRY_SIMULATION_ID,
    MOIST_CASE_ID,
    MOIST_RUN_ID,
    MOIST_SIMULATION_ID,
)
from cloud_chamber.run_cost import LaunchBudgetError, validate_manifest_launch_budget
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


@pytest.fixture(autouse=True)
def _trust_test_built_in_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_world._built_in_inspectability",
        lambda _settings, _spec, _manifest: (True, "Test artifact accepted."),
    )


def test_templates_expose_two_distinct_recipes_and_approved_profiles(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID, moist=False)
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, moist=True)

    dry = mountain_waves_variation_template(settings, DRY_SIMULATION_ID)
    moist = mountain_waves_variation_template(settings, MOIST_SIMULATION_ID)

    assert dry.can_create_variation is False
    assert "bounded equivalence" in (dry.unavailable_reason or "")
    assert dry.recipe_id == DRY_RECIPE_ID
    assert dry.controls.dry_ridge == DryRidgeControls()
    assert {item.profile.role for item in dry.run_profiles} == {
        "Quick",
        "Standard",
        "Presentation",
        "Extended",
    }
    assert dry.default_run_profile_id == "mountain_waves_dry_presentation_v1"
    assert moist.recipe_id == BOULDER_RECIPE_ID
    assert moist.controls.boulder_moist == BoulderMoistControls()
    assert moist.default_run_profile_id == "mountain_waves_boulder_presentation_v1"
    assert all(item.profile.recipe_id == BOULDER_RECIPE_ID for item in moist.run_profiles)


def test_dry_preview_uses_recipe_controls_and_generated_timing(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID, moist=False)
    controls = DryRidgeControls(
        ridge_height_m=600,
        ridge_half_width_m=2_000,
        cross_ridge_wind_m_s=12,
        dry_stability_n_s=0.012,
        wind_shear_through_10km_m_s=-8,
    )
    preview = preview_mountain_waves_variation(
        settings,
        _request(
            parent=DRY_SIMULATION_ID,
            recipe_id=DRY_RECIPE_ID,
            profile_id="mountain_waves_dry_standard_v1",
            controls=MountainWavesRecipeControls(recipe_id=DRY_RECIPE_ID, dry_ridge=controls),
        ),
    )

    assert preview.blocking_errors == [
        "Dry Ridge remains inspectable but cannot parent a variation until "
        "source-defined analytic inheritance or bounded equivalence is approved."
    ]
    assert preview.relationship_classification == "mixed_variation"
    assert {item["label"] for item in preview.differences["terrain"]} == {
        "Ridge height",
        "Ridge half-width",
    }
    assert preview.diagnostics["cells_per_half_width"] == pytest.approx(20)
    assert preview.observation_plan["duration_seconds"] >= 2_160
    assert preview.observation_plan["output_cadence_seconds"] == 60
    assert preview.cost_estimate.profile.numerical_realization.grid.endswith("× 1 × 180")
    assert len(preview.terrain_profile) == 121
    assert preview.moisture_profile[0]["value"] == 0
    assert preview.relative_humidity_profile[0]["value"] == 0
    assert preview.theta_profile[0]["value"] == pytest.approx(288)


def test_dry_slope_and_uncharacterized_profile_block_without_sanitizing_science(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID, moist=False)
    controls = DryRidgeControls(ridge_height_m=2_500, ridge_half_width_m=500)
    preview = preview_mountain_waves_variation(
        settings,
        _request(
            parent=DRY_SIMULATION_ID,
            recipe_id=DRY_RECIPE_ID,
            profile_id="mountain_waves_dry_extended_v1",
            controls=MountainWavesRecipeControls(recipe_id=DRY_RECIPE_ID, dry_ridge=controls),
        ),
    )

    assert any("maximum terrain slope" in item for item in preview.blocking_errors)
    assert any("uncharacterized" in item for item in preview.blocking_errors)


def test_boulder_preview_applies_absolute_reference_transforms(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, moist=True)
    controls = BoulderMoistControls(
        ridge_half_width_m=11_000,
        low_level_wind_m_s=20.0,
        shear_through_10km_m_s=30.0,
        lower_layer_rh_percent=80.0,
        midlevel_rh_percent=50.0,
        lower_stability_factor=1.1,
    )
    request = _request(
        parent=MOIST_SIMULATION_ID,
        recipe_id=BOULDER_RECIPE_ID,
        profile_id="mountain_waves_boulder_standard_v1",
        controls=MountainWavesRecipeControls(recipe_id=BOULDER_RECIPE_ID, boulder_moist=controls),
    )

    first = preview_mountain_waves_variation(settings, request)
    second = preview_mountain_waves_variation(settings, request)

    assert first.blocking_errors == []
    assert first.wind_profile == second.wind_profile
    assert first.moisture_profile == second.moisture_profile
    assert first.relative_humidity_profile == second.relative_humidity_profile
    assert first.theta_profile == second.theta_profile
    assert first.differences["terrain"][0]["after"] == 11_000
    assert first.differences["moisture"][0]["label"] == "0–4 km mean RH"
    assert first.relationship_classification == "mixed_variation"
    assert first.cost_estimate.profile.estimate_basis == "scaled_from_measured"
    assert all(item["value"] >= 0 for item in first.moisture_profile)
    assert all(0 <= item["value"] <= 100 for item in first.relative_humidity_profile)
    assert _profile_layer_mean(first.wind_profile, 0.0, 4_000.0) == pytest.approx(20.0)
    assert _profile_value_at(first.wind_profile, 10_000.0) - _profile_value_at(
        first.wind_profile, 0.0
    ) == pytest.approx(30.0)
    assert _profile_layer_mean(first.relative_humidity_profile, 0.0, 4_000.0) == pytest.approx(
        80.0, abs=0.02
    )
    assert _profile_layer_mean(first.relative_humidity_profile, 4_000.0, 10_000.0) == pytest.approx(
        50.0, abs=0.02
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("low_level_wind_m_s", -0.1),
        ("low_level_wind_m_s", 50.1),
        ("wind_offset_m_s", -20.1),
        ("wind_offset_m_s", 20.1),
        ("shear_through_10km_m_s", -30.1),
        ("shear_through_10km_m_s", 50.1),
        ("lower_layer_rh_percent", -0.1),
        ("lower_layer_rh_percent", 100.1),
        ("midlevel_rh_percent", -0.1),
        ("midlevel_rh_percent", 100.1),
    ],
)
def test_boulder_actual_value_controls_enforce_approved_bounds(field: str, value: float) -> None:
    payload = BoulderMoistControls().model_dump(mode="json")
    payload[field] = value

    with pytest.raises(ValueError):
        BoulderMoistControls.model_validate(payload)


def test_inactive_controls_normalize_out_of_effective_scientific_design() -> None:
    dry_reference = MountainWavesRecipeControls(
        recipe_id=DRY_RECIPE_ID,
        dry_ridge=DryRidgeControls(),
    )
    dry = MountainWavesRecipeControls(
        recipe_id=DRY_RECIPE_ID,
        dry_ridge=DryRidgeControls(
            layered_stability=False,
            lower_stability_n_s=0.02,
            upper_stability_n_s=0.005,
            stability_transition_height_m=12_000,
        ),
    )
    normalized_dry = normalize_recipe_controls(dry, recipe_reference=dry_reference)
    assert normalized_dry == dry_reference

    moist_reference = MountainWavesRecipeControls(
        recipe_id=BOULDER_RECIPE_ID,
        boulder_moist=BoulderMoistControls(dry_air_counterpart=True),
    )
    moist = MountainWavesRecipeControls(
        recipe_id=BOULDER_RECIPE_ID,
        boulder_moist=BoulderMoistControls(
            dry_air_counterpart=True,
            lower_layer_rh_percent=5.0,
            midlevel_rh_percent=95.0,
        ),
    )
    normalized_moist = normalize_recipe_controls(
        moist,
        recipe_reference=MountainWavesRecipeControls(
            recipe_id=BOULDER_RECIPE_ID,
            boulder_moist=BoulderMoistControls(),
        ),
    )
    assert normalized_moist.boulder_moist is not None
    assert normalized_moist.boulder_moist.lower_layer_rh_percent == 66.0
    assert normalized_moist.boulder_moist.midlevel_rh_percent == 34.5
    assert normalized_moist.boulder_moist.dry_air_counterpart is True
    assert moist_reference.boulder_moist is not None


def test_boulder_vertical_domain_and_critical_level_fail_closed(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, moist=True)
    high_wind = preview_mountain_waves_variation(
        settings,
        _request(
            parent=MOIST_SIMULATION_ID,
            recipe_id=BOULDER_RECIPE_ID,
            profile_id="mountain_waves_boulder_standard_v1",
            controls=MountainWavesRecipeControls(
                recipe_id=BOULDER_RECIPE_ID,
                boulder_moist=BoulderMoistControls(
                    low_level_wind_m_s=50.0,
                    shear_through_10km_m_s=50.0,
                ),
            ),
        ),
    )
    critical_level = preview_mountain_waves_variation(
        settings,
        _request(
            parent=MOIST_SIMULATION_ID,
            recipe_id=BOULDER_RECIPE_ID,
            profile_id="mountain_waves_boulder_standard_v1",
            controls=MountainWavesRecipeControls(
                recipe_id=BOULDER_RECIPE_ID,
                boulder_moist=BoulderMoistControls(
                    low_level_wind_m_s=0.0,
                    wind_offset_m_s=-20.0,
                    shear_through_10km_m_s=50.0,
                ),
            ),
        ),
    )

    assert any(
        "exceeds the 25.0 km source-backed sounding" in error for error in high_wind.blocking_errors
    )
    assert any(
        "critical level falls inside the active terrain-forced wave region" in error
        for error in critical_level.blocking_errors
    )
    assert high_wind.diagnostics["damping_base_m"] < high_wind.diagnostics["model_top_m"]


def test_boulder_inherited_critical_structure_warns_without_blocking(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(
        settings,
        run_id=MOIST_RUN_ID,
        case_id=MOIST_CASE_ID,
        moist=True,
        upper_wind_m_s=-5.0,
    )

    preview = preview_mountain_waves_variation(
        settings,
        _request(
            parent=MOIST_SIMULATION_ID,
            recipe_id=BOULDER_RECIPE_ID,
            profile_id="mountain_waves_boulder_standard_v1",
            controls=MountainWavesRecipeControls(
                recipe_id=BOULDER_RECIPE_ID,
                boulder_moist=BoulderMoistControls(
                    ridge_height_m=2_500.0,
                    ridge_half_width_m=11_000.0,
                    lower_layer_rh_percent=80.0,
                    lower_stability_factor=1.1,
                ),
            ),
        ),
    )

    assert not any("critical level falls" in error for error in preview.blocking_errors)
    assert any(
        "retained Boulder source atmosphere contains a critical level" in warning
        for warning in preview.warnings
    )


def test_package_persists_stable_simulation_identity_separate_attempts_and_launch_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, moist=True)
    request = _request(
        parent=MOIST_SIMULATION_ID,
        recipe_id=BOULDER_RECIPE_ID,
        profile_id="mountain_waves_boulder_quick_v1",
        controls=MountainWavesRecipeControls(
            recipe_id=BOULDER_RECIPE_ID,
            boulder_moist=BoulderMoistControls(
                ridge_half_width_m=11_000,
                lower_layer_rh_percent=75.0,
                lower_stability_factor=1.1,
            ),
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.collect_cm1_provenance",
        lambda _settings: SimpleNamespace(report_record=lambda: {"release": "21.1"}),
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=100 * 1024**3),
    )

    first = create_mountain_waves_variation(settings, request)
    second = create_mountain_waves_variation(settings, request)
    manifest = load_run_manifest(Path(first.manifest_path))

    assert first.simulation_id == second.simulation_id
    assert first.run_id != second.run_id
    assert first.envelope.package_identity_sha256 == second.envelope.package_identity_sha256
    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.recipe_id == BOULDER_RECIPE_ID
    assert manifest.run_configuration["variation_envelope"]["availability_state"] == "packaged"
    assert manifest.run_configuration["launch_review_snapshot_id"]
    assert manifest.run_configuration["launch_specification"]["profile_id"] == (
        "mountain_waves_boulder_quick_v1"
    )
    assert first.preflight["passed"] is True
    assert preflight_mountain_waves_variation(Path(first.manifest_path))["passed"] is True
    assert "uinterp" in manifest.required_output_fields
    assert not list(Path(first.package_dir).glob("cm1out*"))
    case_manifest = Path(first.package_dir, "case_manifest.json").read_text()
    package_report = Path(first.package_dir, "mountain_waves_variation.json").read_text()
    assert '"variation_envelope":' not in case_manifest
    assert '"variation_envelope":' not in package_report
    assert '"variation_envelope_authority":' in case_manifest
    assert '"variation_envelope_authority":' in package_report
    generated_sounding = manifest.run_configuration["mountain_waves_configuration"]["sounding"]
    generated_pressures = [level["pressure_pa"] for level in generated_sounding]
    assert all(
        upper < lower
        for lower, upper in zip(generated_pressures, generated_pressures[1:], strict=False)
    )

    launch_check = validate_manifest_launch_budget(
        settings,
        manifest=manifest,
        snapshot_id=first.launch_review_snapshot_id,
    )
    assert launch_check is not None
    assert launch_check.check_kind == "launch"
    with pytest.raises(LaunchBudgetError, match="already been consumed"):
        validate_manifest_launch_budget(
            settings,
            manifest=manifest,
            snapshot_id=first.launch_review_snapshot_id,
        )


def test_descendant_differences_are_relative_to_selected_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, moist=True)
    parent_controls = BoulderMoistControls(ridge_half_width_m=11_000)
    parent_request = _request(
        parent=MOIST_SIMULATION_ID,
        recipe_id=BOULDER_RECIPE_ID,
        profile_id="mountain_waves_boulder_quick_v1",
        controls=MountainWavesRecipeControls(
            recipe_id=BOULDER_RECIPE_ID,
            boulder_moist=parent_controls,
        ),
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.collect_cm1_provenance",
        lambda _settings: SimpleNamespace(report_record=lambda: {"release": "21.1"}),
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=100 * 1024**3),
    )
    parent = create_mountain_waves_variation(settings, parent_request)
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations._parent_eligibility",
        lambda *_args: (True, None),
    )

    unchanged = preview_mountain_waves_variation(
        settings,
        parent_request.model_copy(update={"parent_simulation_id": parent.simulation_id}),
    )
    assert unchanged.blocking_errors == [
        "Change at least one effective Recipe control or numerical realization."
    ]

    child_controls = parent_controls.model_copy(update={"ridge_height_m": 2_500.0})
    child_request = parent_request.model_copy(
        update={
            "parent_simulation_id": parent.simulation_id,
            "controls": MountainWavesRecipeControls(
                recipe_id=BOULDER_RECIPE_ID,
                boulder_moist=child_controls,
            ),
        }
    )
    child = preview_mountain_waves_variation(settings, child_request)

    assert child.blocking_errors == []
    terrain_differences = child.differences["terrain"]
    assert terrain_differences == [
        {
            "path": "controls.ridge_height_m",
            "label": "Ridge height",
            "before": 2_000.0,
            "after": 2_500.0,
            "units": "m",
            "material": True,
        }
    ]
    child_package = create_mountain_waves_variation(settings, child_request)
    child_manifest = load_run_manifest(Path(child_package.manifest_path))
    assert child_manifest.run_configuration["configuration_difference"]["terrain"] == (
        terrain_differences
    )
    assert [
        difference.model_dump(mode="json") for difference in child_package.envelope.differences
    ] == [
        {
            "category": "terrain",
            "path": "controls.ridge_height_m",
            "label": "Ridge height",
            "before": 2_000.0,
            "after": 2_500.0,
            "units": "m",
            "material": True,
        }
    ]


def _request(
    *,
    parent: str,
    recipe_id: RecipeId,
    profile_id: str,
    controls: MountainWavesRecipeControls,
) -> MountainWavesVariationRequest:
    return MountainWavesVariationRequest(
        parent_simulation_id=parent,
        simulation_name="Bounded wave experiment",
        user_question="How does the approved control change the wave response?",
        recipe_id=recipe_id,
        run_profile_id=profile_id,
        controls=controls,
    )


def _profile_layer_mean(
    profile: list[dict[str, float]],
    lower_height_m: float,
    upper_height_m: float,
) -> float:
    values = [
        item["value"] for item in profile if lower_height_m <= item["height_m"] < upper_height_m
    ]
    return sum(values) / len(values)


def _profile_value_at(profile: list[dict[str, float]], height_m: float) -> float:
    return next(item["value"] for item in profile if item["height_m"] == height_m)


def _settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1r21.1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True)
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def _write_parent(
    settings: CloudChamberSettings,
    *,
    run_id: str,
    case_id: str,
    moist: bool,
    upper_wind_m_s: float = 28.0,
) -> None:
    run_dir = settings.runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF fixture")
    namelist = run_dir / "namelist.input"
    namelist.write_text(_parent_namelist(dry=not moist))
    sounding = run_dir / "input_sounding"
    sounding.write_text(
        "1000.0000 288.000000 8.000000000\n"
        "0.0 288.0 8.0 12.0 0.0\n"
        "4000.0 305.0 4.0 16.0 0.0\n"
        "10000.0 335.0 0.5 22.0 0.0\n"
        f"25000.0 460.0 0.0 {upper_wind_m_s} 0.0\n"
    )
    (run_dir / "case_manifest.json").write_text("{}\n")
    now = datetime(2026, 7, 21, tzinfo=UTC)
    manifest_path = run_dir / "run_manifest.json"
    domain = {
        "nx": 200 if not moist else 440,
        "ny": 1,
        "nz": 200 if not moist else 250,
        "dx_m": 100.0 if not moist else 500.0,
        "dy_m": 100.0 if not moist else 500.0,
        "dz_m": 100.0,
        "active_top_m": 20_000.0 if not moist else 25_000.0,
    }
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=case_id, schema_version="test-v1"),
        controls={},
        run_configuration={
            "duration_seconds": 2_160 if not moist else 7_200,
            "output_cadence_seconds": 30,
            "domain": domain,
            "terrain": {
                "height_m": 400.0 if not moist else 2_000.0,
                "half_width_m": 1_000.0 if not moist else 10_000.0,
                "center_m": 0.0 if not moist else 250.0,
            },
        },
        physical_question="What happens over the ridge?",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist),
            input_sounding=str(sounding),
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
    )
    write_run_manifest(manifest_path, manifest)


def _parent_namelist(*, dry: bool) -> str:
    values = {
        "nx": "200" if dry else "440",
        "ny": "1",
        "nz": "200" if dry else "250",
        "dx": "100.0" if dry else "500.0",
        "dy": "100.0" if dry else "500.0",
        "dz": "100.0",
        "dtl": "1.0",
        "timax": "2160.0" if dry else "7200.0",
        "tapfrq": "30.0",
        "stretch_z": "0",
        "ztop": "18000.0" if dry else "25000.0",
        "zd": "14000.0",
        "itern": "1" if dry else "4",
        "isnd": "9" if dry else "7",
        "iwnd": "6" if dry else "0",
        "imoist": "0" if dry else "1",
        "output_zs": "1",
        "output_zh": "1",
        "output_th": "1",
        "output_prs": "1",
        "output_qv": "1",
        "output_q": "1",
        "output_uinterp": "1",
        "output_vinterp": "1",
        "output_winterp": "1",
        "output_w": "1",
    }
    return (
        " &param0\n" + "".join(f" {name} = {value},\n" for name, value in values.items()) + " /\n"
    )

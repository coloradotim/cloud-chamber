from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from cloud_chamber.bomex_case import (
    CM1_EXECUTABLE_SHA256,
    CM1_SOURCE_MANIFEST_SHA256,
    CM1Provenance,
)
from cloud_chamber.cloud_worlds import (
    PRESENTATION_BASELINE_RESULT_ID,
    PRESENTATION_BASELINE_RUN_ID,
    PRESENTATION_FIXED_ASSUMPTIONS_SHA256,
    REFERENCE_SIMULATION_ID,
    trade_cumulus_world_detail,
)
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
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_recipes import TradeCumulusControls
from cloud_chamber.trade_cumulus_variations import (
    EXTENDED_CHARACTERIZATION_AUTHORIZATION_ID,
    TradeCumulusExtendedCharacterizationRequest,
    TradeCumulusVariationError,
    TradeCumulusVariationRequest,
    create_trade_cumulus_extended_characterization,
    create_trade_cumulus_variation,
    preflight_trade_cumulus_variation,
    preview_trade_cumulus_variation,
    trade_cumulus_variation_template,
)
from cloud_chamber.variation_envelope import VariationEnvelope


def test_template_inherits_absolute_parent_controls_and_all_profiles(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)

    template = trade_cumulus_variation_template(settings, REFERENCE_SIMULATION_ID)

    assert template.can_create_variation is True
    assert template.controls == TradeCumulusControls()
    assert template.canonical_reference_controls == TradeCumulusControls()
    assert template.default_run_profile_id == "trade_cumulus_presentation_v1"
    assert {estimate.profile.role for estimate in template.run_profiles} == {
        "Quick",
        "Standard",
        "Full-cycle",
        "Presentation",
        "Extended",
    }


def test_preview_uses_parent_relative_differences_and_warns_without_blocking(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    controls = TradeCumulusControls(
        surface_sensible_heat_flux_k_m_s=-0.01,
        surface_moisture_flux_g_kg_m_s=-0.05,
        inversion_strength_k=-2.0,
        free_tropospheric_rh_percent=98.0,
        cloud_layer_shear_m_s=35.0,
        large_scale_vertical_motion_m_s=0.02,
        temperature_tendency_k_day=3.0,
        total_water_tendency_g_kg_day=2.0,
    )

    preview = preview_trade_cumulus_variation(
        settings,
        _request(controls=controls),
    )

    assert preview.blocking_errors == []
    assert preview.relationship_classification == "multi_factor_physical_variation"
    assert preview.canonical_reference_controls["surface_moisture_flux_g_kg_m_s"] == 0.052
    assert preview.parent_controls["surface_moisture_flux_g_kg_m_s"] == 0.052
    assert preview.resolved_controls["surface_moisture_flux_g_kg_m_s"] == -0.05
    assert any("downward" in warning for warning in preview.warnings)
    assert any("reverses the inversion" in warning for warning in preview.warnings)
    assert any("reversed to ascent" in warning for warning in preview.warnings)
    assert len(preview.sounding_profile) > 20
    assert len(preview.forcing_profile) > 20


def test_preview_blocks_unattainable_vertical_domain_without_clipping(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)

    preview = preview_trade_cumulus_variation(
        settings,
        _request(
            controls=TradeCumulusControls(
                inversion_base_m_agl=2_000,
                inversion_thickness_m=1_000,
            )
        ),
    )

    assert any("run profile ends" in error for error in preview.blocking_errors)
    assert preview.diagnostics["inversion_top_m_agl"] == 3_000


def test_normal_extended_profile_remains_blocked(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)

    preview = preview_trade_cumulus_variation(
        settings,
        TradeCumulusVariationRequest(
            parent_simulation_id=REFERENCE_SIMULATION_ID,
            simulation_name="Ordinary Extended request",
            run_profile_id="trade_cumulus_extended_v1",
            controls=TradeCumulusControls(),
        ),
    )

    assert any("uncharacterized" in error for error in preview.blocking_errors)


def test_pm_authorized_extended_reference_characterization_packages_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    _patch_package_environment(tmp_path, monkeypatch)

    package = create_trade_cumulus_extended_characterization(
        settings,
        TradeCumulusExtendedCharacterizationRequest(
            authorization_id=EXTENDED_CHARACTERIZATION_AUTHORIZATION_ID
        ),
    )
    manifest = load_run_manifest(Path(package.manifest_path))
    authorization = manifest.run_configuration["characterization_authorization"]

    assert authorization["issue_number"] == 448
    assert authorization["ordinary_extended_profile_enabled"] is False
    assert manifest.run_configuration["parent_simulation_id"] == REFERENCE_SIMULATION_ID
    assert manifest.run_configuration["launch_specification"]["profile_id"] == (
        "trade_cumulus_extended_v1"
    )
    assert manifest.controls == TradeCumulusControls().model_dump(mode="json")
    assert manifest.manual_validation_status == (
        "pm_authorized_extended_reference_characterization_packaged"
    )
    assert package.preflight["passed"] is True
    assert package.envelope.world_payload["characterization_authorization"] == authorization
    with pytest.raises(TradeCumulusVariationError, match="already been used"):
        create_trade_cumulus_extended_characterization(
            settings,
            TradeCumulusExtendedCharacterizationRequest(
                authorization_id=EXTENDED_CHARACTERIZATION_AUTHORIZATION_ID
            ),
        )


def test_package_persists_exact_inputs_shared_envelope_and_retry_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    _patch_package_environment(tmp_path, monkeypatch)
    request = _request(controls=TradeCumulusControls(surface_moisture_flux_g_kg_m_s=0.09))

    first = create_trade_cumulus_variation(settings, request)
    second = create_trade_cumulus_variation(settings, request)
    manifest = load_run_manifest(Path(first.manifest_path))
    namelist = Path(manifest.generated_inputs.namelist_input or "").read_text()
    sounding = Path(manifest.generated_inputs.input_sounding or "").read_text()

    assert first.simulation_id == second.simulation_id
    assert first.run_id != second.run_id
    assert first.envelope.package_identity_sha256 == second.envelope.package_identity_sha256
    assert first.envelope.relationship_classification == "controlled_physical_variation"
    assert second.envelope.attempts[-1].relationship == "unchanged_retry"
    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.recipe_id == "canonical_bomex_trade_cumulus"
    assert manifest.run_configuration["variation_envelope"]["availability_state"] == "packaged"
    assert manifest.run_configuration["launch_specification"]["profile_id"] == (
        "trade_cumulus_presentation_v1"
    )
    assert manifest.run_configuration["launch_review_snapshot_id"]
    assert "cnst_lhflx = 9.000000000000e-05" in namelist
    assert "isnd = 7" in namelist
    assert len(sounding.splitlines()) > 20
    assert first.preflight["passed"] is True
    assert preflight_trade_cumulus_variation(Path(first.manifest_path))["passed"] is True
    assert not list(Path(first.package_dir).glob("cm1out*"))


def test_package_forcing_customization_records_absolute_signed_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    source_path = _patch_package_environment(tmp_path, monkeypatch)
    controls = TradeCumulusControls(
        surface_moisture_flux_g_kg_m_s=0.09,
        large_scale_vertical_motion_m_s=0.02,
        temperature_tendency_k_day=4.0,
        total_water_tendency_g_kg_day=-6.0,
    )

    package = create_trade_cumulus_variation(settings, _request(controls=controls))
    manifest = load_run_manifest(Path(package.manifest_path))
    artifact = Path(manifest.generated_inputs.cm1_source_customization or "").read_text()

    assert source_path.name == "base.F"
    assert '"vertical_motion_m_s": 0.02' in artifact
    assert '"temperature_tendency_k_day": 4.0' in artifact
    assert '"total_water_tendency_g_kg_day": -6.0' in artifact
    assert manifest.run_configuration["cm1_source_customization_kind"] == (
        "trade_cumulus_forcing_v1"
    )


def test_preflight_rejects_self_consistent_but_wrong_generated_sounding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    _patch_package_environment(tmp_path, monkeypatch)
    package = create_trade_cumulus_variation(
        settings,
        _request(
            controls=TradeCumulusControls(
                sub_inversion_total_water_g_kg=18.0,
            )
        ),
    )
    manifest_path = Path(package.manifest_path)
    manifest = load_run_manifest(manifest_path)
    sounding_path = Path(manifest.generated_inputs.input_sounding or "")
    sounding_path.write_text(sounding_path.read_text() + "\n# tampered after review\n")
    generated_hashes = dict(manifest.run_configuration["generated_input_sha256"])
    generated_hashes["input_sounding"] = hashlib.sha256(sounding_path.read_bytes()).hexdigest()
    manifest.run_configuration["generated_input_sha256"] = generated_hashes
    write_run_manifest(manifest_path, manifest)

    with pytest.raises(
        TradeCumulusVariationError,
        match="sounding_matches_reviewed_contract.*False",
    ):
        preflight_trade_cumulus_variation(manifest_path)


def test_completed_retries_promote_one_backing_and_support_descendant_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    _patch_package_environment(tmp_path, monkeypatch)
    request = _request(controls=TradeCumulusControls(surface_moisture_flux_g_kg_m_s=0.09))
    first = create_trade_cumulus_variation(settings, request)
    second = create_trade_cumulus_variation(settings, request)
    _complete_package(first.manifest_path)
    _complete_package(second.manifest_path)
    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.validate_trade_cumulus_variation_outputs",
        lambda _manifest, _metadata: {"passed": True},
    )
    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.validate_trade_cumulus_attempt_provenance",
        lambda _manifest: {"passed": True},
    )

    world = trade_cumulus_world_detail(settings)
    records = [
        record for record in world.simulations if record.simulation_id == first.simulation_id
    ]

    assert len(records) == 1
    assert records[0].run_id == first.run_id
    assert records[0].attempt_count == 2
    assert records[0].can_create_variation is True
    promoted = load_run_manifest(Path(first.manifest_path))
    envelope = VariationEnvelope.model_validate(promoted.run_configuration["variation_envelope"])
    assert [attempt.run_id for attempt in envelope.attempts] == [
        first.run_id,
        second.run_id,
    ]
    assert [attempt.run_id for attempt in envelope.attempts if attempt.accepted_backing] == [
        first.run_id
    ]
    child = trade_cumulus_variation_template(settings, first.simulation_id)
    assert child.can_create_variation is True
    assert child.controls.surface_moisture_flux_g_kg_m_s == 0.09


def test_cross_parent_attempt_collision_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings)
    _patch_package_environment(tmp_path, monkeypatch)
    request = _request(controls=TradeCumulusControls(surface_moisture_flux_g_kg_m_s=0.09))
    first = create_trade_cumulus_variation(settings, request)
    second = create_trade_cumulus_variation(settings, request)
    second_path = Path(second.manifest_path)
    second_manifest = load_run_manifest(second_path)
    second_envelope = VariationEnvelope.model_validate(
        second_manifest.run_configuration["variation_envelope"]
    ).model_copy(update={"parent_simulation_id": "trade_cumulus_more_moisture"})
    second_manifest.run_configuration["variation_envelope"] = second_envelope.model_dump(
        mode="json"
    )
    second_manifest.run_configuration["parent_simulation_id"] = "trade_cumulus_more_moisture"
    write_run_manifest(second_path, second_manifest)
    _complete_package(first.manifest_path)
    _complete_package(second.manifest_path)
    monkeypatch.setattr(
        "cloud_chamber.cloud_worlds.validate_trade_cumulus_variation_outputs",
        lambda _manifest, _metadata: {"passed": True},
    )

    world = trade_cumulus_world_detail(settings)

    assert all(record.simulation_id != first.simulation_id for record in world.simulations)
    conflict = next(
        record for record in world.lab_history if record.run_id in {first.run_id, second.run_id}
    )
    assert conflict.technical_state == "conflict"
    assert "canonical intended Simulation contract" in conflict.technical_state_message


def _request(*, controls: TradeCumulusControls) -> TradeCumulusVariationRequest:
    return TradeCumulusVariationRequest(
        parent_simulation_id=REFERENCE_SIMULATION_ID,
        simulation_name="Direct target experiment",
        user_question="How do direct atmospheric targets change the cloud field?",
        run_profile_id="trade_cumulus_presentation_v1",
        controls=controls,
    )


def _settings(tmp_path: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=tmp_path / "runtime",
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=tmp_path / "cache",
        log_dir=tmp_path / "logs",
    )


def _write_parent(settings: CloudChamberSettings) -> None:
    run_dir = settings.runtime_home / "runs" / PRESENTATION_BASELINE_RUN_ID
    run_dir.mkdir(parents=True)
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF retained parent fixture")
    namelist = run_dir / "namelist.input"
    sounding = run_dir / "input_sounding"
    namelist.write_text("isnd = 7,\n")
    sounding.write_text("1015.0 298.7 17.0\n0.0 298.7 17.0 -8.75 0.0\n")
    now = datetime(2026, 7, 28, tzinfo=UTC)
    manifest_path = run_dir / "run_manifest.json"
    manifest = RunManifest(
        run_id=PRESENTATION_BASELINE_RUN_ID,
        scenario=ScenarioReference(
            id="bomex_trade_cumulus_baseline_v0",
            schema_version="test-v1",
        ),
        controls={"surface_moisture_flux_g_g_m_s": 5.2e-5},
        run_configuration={
            "case_id": "bomex_trade_cumulus_baseline_v0",
            "product_slice_id": "trade_cumulus_v1",
            "comparison_group_id": "trade_cumulus_moisture_v1",
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "fixed_assumptions_sha256": PRESENTATION_FIXED_ASSUMPTIONS_SHA256,
        },
        physical_question="Canonical BOMEX parent",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist),
            input_sounding=str(sounding),
        ),
        runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home)),
        app=AppMetadata(app_version="test", commit="test"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name="Canonical BOMEX Baseline"),
    )
    write_run_manifest(manifest_path, manifest)
    metadata = ResultMetadata(
        result_id=PRESENTATION_BASELINE_RESULT_ID,
        run_id=PRESENTATION_BASELINE_RUN_ID,
        scenario_id="bomex_trade_cumulus_baseline_v0",
        physical_question="Canonical BOMEX parent",
        controls={
            "control_id": "surface_moisture_supply",
            "control_state": "baseline",
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
        },
        run_configuration={
            "case_id": "bomex_trade_cumulus_baseline_v0",
            "product_slice_id": "trade_cumulus_v1",
            "comparison_group_id": "trade_cumulus_moisture_v1",
            "control_id": "surface_moisture_supply",
            "control_state": "baseline",
            "recipe_candidate_id": "canonical_bomex_baseline",
            "surface_moisture_flux_g_g_m_s": 5.2e-5,
            "fixed_assumptions_sha256": PRESENTATION_FIXED_ASSUMPTIONS_SHA256,
            "cm1_provenance": {
                "source_manifest_sha256": (
                    "fbe2367dfcd6d8c55cac4bd03362d8d49f13f80cebd13b36230c20d71119a84e"
                ),
                "executable_sha256": (
                    "5b7304bb04514ec03cf4d6e604bc0b5df6e8076bd4fb53c4b5cf5ea9184cdfd1"
                ),
            },
        },
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        model_output_paths=[str(output)],
        netcdf_paths=[str(output)],
        model_output_file_count=1,
        created_at=now,
        updated_at=now,
    )
    (run_dir / "result_metadata.json").write_text(metadata.to_json_text())


def _patch_package_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    source_root = tmp_path / "cm1"
    source_path = source_root / "src" / "base.F"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(_forcing_source_fixture())
    reference_namelist = tmp_path / "bomex.input"
    reference_namelist.write_text("fixture\n")
    provenance = CM1Provenance(
        release="r21.1",
        official_tag_commit="tag",
        official_source_tag="r21.1",
        source_tree_path=str(source_root),
        run_directory_path=str(tmp_path / "cm1-run"),
        executable_path=str(tmp_path / "cm1.exe"),
        executable_sha256=CM1_EXECUTABLE_SHA256,
        readme_namelist_path=str(reference_namelist),
        readme_namelist_sha256="b" * 64,
        source_manifest_method="test",
        source_manifest_sha256=CM1_SOURCE_MANIFEST_SHA256,
        critical_source_sha256={"src/base.F": "d" * 64},
        bundled_bomex_namelist_path=str(reference_namelist),
        bundled_bomex_namelist_sha256="e" * 64,
        bundled_bomex_readme_path=str(reference_namelist),
        bundled_bomex_readme_sha256="f" * 64,
    )
    monkeypatch.setattr(
        "cloud_chamber.trade_cumulus_variations.verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(
        "cloud_chamber.trade_cumulus_variations.collect_cm1_provenance",
        lambda _settings: provenance,
    )

    def render_namelist(
        _reference: str,
        controls: TradeCumulusControls,
        profile_id: str,
    ) -> str:
        extended = profile_id == "trade_cumulus_extended_v1"
        return (
            f"nx = {128 if extended else 96},\n"
            f"ny = {128 if extended else 96},\n"
            f"nz = {75 if extended else 100},\n"
            f"dx = {100 if extended else 66.66666667},\n"
            f"dy = {100 if extended else 66.66666667},\n"
            f"dz = {40 if extended else 30},\n"
            f"dtl = {3 if extended else 2},\n"
            "timax = 14400,\n"
            f"tapfrq = {120 if extended else 60},\n"
            "dodomaindiag = .true.,\n"
            "diagfrq = 60,\n"
            "isnd = 7,\n"
            "iwnd = 0,\n"
            f"cnst_shflx = {controls.surface_sensible_heat_flux_k_m_s:.12e},\n"
            f"cnst_lhflx = {controls.surface_moisture_flux_g_kg_m_s / 1000:.12e},\n"
        )

    monkeypatch.setattr(
        "cloud_chamber.trade_cumulus_variations._render_namelist",
        render_namelist,
    )
    monkeypatch.setattr(
        "cloud_chamber.run_cost.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=100 * 1024**3),
    )
    return source_path


def _complete_package(manifest_path_value: str) -> None:
    manifest_path = Path(manifest_path_value)
    manifest = load_run_manifest(manifest_path)
    run_dir = manifest_path.parent
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF completed variation fixture")
    now = datetime.now(UTC)
    manifest = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "validation_status": ValidationStatus.NEEDS_REVIEW,
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
            "execution": ExecutionMetadata(
                started_at=now,
                finished_at=now,
                exit_code=0,
            ),
            "outputs": OutputMetadata(netcdf_paths=[str(output)]),
            "updated_at": now,
        }
    )
    write_run_manifest(manifest_path, manifest)
    metadata = ResultMetadata(
        result_id=f"result-{manifest.run_id}",
        run_id=manifest.run_id,
        scenario_id=manifest.scenario.id,
        physical_question=manifest.physical_question,
        controls=manifest.controls,
        run_configuration=manifest.run_configuration,
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        required_output_fields=manifest.required_output_fields,
        model_output_paths=[str(output)],
        netcdf_paths=[str(output)],
        model_output_file_count=1,
        created_at=manifest.created_at,
        updated_at=now,
    )
    (run_dir / "result_metadata.json").write_text(metadata.to_json_text())


def _forcing_source_fixture() -> str:
    return """\
    IF( testcase .eq. 3 )THEN
      ! shallow Cu case  (Siebesma et al, 2003, JAS)
      wmin  =  -0.0065
      radsfc = -2.0/( 3600.0 * 24.0 )
      qvsfc  = -1.2e-8
      qvfrc(k) = -1.2e-8
    ENDIF
    IF( testcase .eq. 4 )THEN
    ENDIF
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from cloud_chamber.mountain_waves_variations import (
    MountainWavesConfiguration,
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
    mountain_waves_run_manifest,
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


def test_dry_reference_is_inspectable_but_not_an_editable_parent(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_parent(settings, run_id=DRY_RUN_ID, case_id=DRY_CASE_ID, configuration=None)

    template = mountain_waves_variation_template(settings, DRY_SIMULATION_ID)

    assert template.can_create_variation is False
    assert "source-defined" in (template.unavailable_reason or "")
    assert template.configuration.terrain.height_m == pytest.approx(400.0)


def test_preview_groups_multiple_exact_changes_and_keeps_science_warnings_nonblocking(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    parent = _configuration()
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, configuration=parent)
    intended = parent.model_copy(deep=True)
    intended.terrain.height_m = 3_800.0
    intended.terrain.half_width_m = 6_000.0
    intended.sounding[0].u_m_s = -5.0
    intended.sounding[1].u_m_s = 20.0
    intended.sounding[0].qv_g_kg = 18.0
    intended.sounding[1].theta_k = 280.0
    intended.duration_seconds = 1_200
    intended.output_cadence_seconds = 600
    request = MountainWavesVariationRequest(
        parent_simulation_id=MOIST_SIMULATION_ID,
        simulation_name="Rotor cloud attempt",
        user_question="Can a compact ridge make a sharper lee cloud?",
        configuration=intended,
    )

    preview = preview_mountain_waves_variation(settings, request)

    assert preview.blocking_errors == []
    assert all(
        preview.differences[group]
        for group in (
            "terrain",
            "wind",
            "moisture",
            "stability/thermodynamics",
            "numerics/time",
            "output",
        )
    )
    assert any("reverses direction" in warning for warning in preview.warnings)
    assert any("statically unstable" in warning for warning in preview.warnings)
    assert any("Multiple physical groups" in warning for warning in preview.warnings)
    assert len(preview.terrain_profile) == 121
    assert len(preview.derived_stability_n2_s2) == len(intended.sounding) - 1


def test_malformed_configuration_blocks_without_turning_warnings_into_gates(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    parent = _configuration()
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, configuration=parent)
    intended = parent.model_copy(deep=True)
    intended.terrain.height_m = 0.0
    intended.duration_seconds = 1_001
    intended.output_cadence_seconds = 200

    preview = preview_mountain_waves_variation(
        settings,
        MountainWavesVariationRequest(
            parent_simulation_id=MOIST_SIMULATION_ID,
            simulation_name="Malformed",
            configuration=intended,
        ),
    )

    assert any("Ridge height" in error for error in preview.blocking_errors)
    assert any("divide" in error for error in preview.blocking_errors)


def test_unchanged_and_noninherited_coordinates_are_blocked(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    parent = _configuration()
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, configuration=parent)

    unchanged = preview_mountain_waves_variation(
        settings,
        MountainWavesVariationRequest(
            parent_simulation_id=MOIST_SIMULATION_ID,
            simulation_name="No-op",
            configuration=parent,
        ),
    )
    assert any("Change at least one" in error for error in unchanged.blocking_errors)

    changed = parent.model_copy(deep=True)
    changed.terrain.height_m = 1_900.0
    changed.terrain.center_m = 200_000.0
    changed.sounding[1].height_m += 1.0
    changed.sounding[1].pressure_pa += 1.0
    preview = preview_mountain_waves_variation(
        settings,
        MountainWavesVariationRequest(
            parent_simulation_id=MOIST_SIMULATION_ID,
            simulation_name="Invalid inherited coordinates",
            configuration=changed,
        ),
    )
    assert any("Ridge center" in error for error in preview.blocking_errors)
    assert any("heights and pressures" in error for error in preview.blocking_errors)


def test_each_preview_edit_resolves_its_parent_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    parent = _configuration()
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, configuration=parent)
    intended = parent.model_copy(deep=True)
    intended.terrain.height_m += 100.0
    request = MountainWavesVariationRequest(
        parent_simulation_id=MOIST_SIMULATION_ID,
        simulation_name="Preview edits",
        configuration=intended,
    )
    original = mountain_waves_run_manifest
    calls = 0

    def counted_resolver(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.mountain_waves_run_manifest",
        counted_resolver,
    )

    preview_mountain_waves_variation(settings, request)
    preview_mountain_waves_variation(settings, request)

    assert calls == 2


def test_package_persists_identity_lineage_inputs_and_clean_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    parent = _configuration()
    _write_parent(settings, run_id=MOIST_RUN_ID, case_id=MOIST_CASE_ID, configuration=parent)
    intended = parent.model_copy(deep=True)
    intended.terrain.height_m = 1_600.0
    intended.sounding[0].qv_g_kg *= 1.1
    request = MountainWavesVariationRequest(
        parent_simulation_id=MOIST_SIMULATION_ID,
        simulation_name="Smooth Lenticular Attempt",
        user_question="Will a lower ridge make a smoother cap cloud?",
        configuration=intended,
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(
        "cloud_chamber.mountain_waves_variations.collect_cm1_provenance",
        lambda _settings: SimpleNamespace(report_record=lambda: {"release": "21.1"}),
    )

    package = create_mountain_waves_variation(settings, request)
    manifest_path = Path(package.manifest_path)
    manifest = load_run_manifest(manifest_path)
    preflight = preflight_mountain_waves_variation(manifest_path)

    assert package.simulation_id.startswith("mountain_waves_smooth-lenticular-attempt_")
    assert package.run_id.startswith("mw-smooth-lenticular-attempt-")
    assert package.preflight["passed"] is True
    assert preflight["passed"] is True
    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.run_configuration["cloud_world_id"] == "mountain_waves"
    assert manifest.run_configuration["parent_simulation_id"] == MOIST_SIMULATION_ID
    assert manifest.run_configuration["reference_simulation_id"] == MOIST_SIMULATION_ID
    assert manifest.run_configuration["user_question"] == request.user_question
    assert manifest.run_configuration["mountain_waves_configuration"] == intended.model_dump(
        mode="json"
    )
    assert "uinterp" in manifest.required_output_fields
    assert manifest.run_configuration["configuration_difference"]["terrain"]
    assert manifest.generated_inputs.input_sounding is not None
    assert Path(manifest.generated_inputs.input_sounding).read_text().startswith("1000.0000")
    terrain_path = Path(package.package_dir) / "perts.dat"
    assert terrain_path.stat().st_size == 220 * 4


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
    configuration: MountainWavesConfiguration | None,
) -> None:
    run_dir = settings.runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF fixture")
    namelist = run_dir / "namelist.input"
    namelist.write_text(_parent_namelist(dry=configuration is None))
    sounding = run_dir / "input_sounding"
    sounding.write_text("1000.0000 288.000000 0.000000000\n0.0 288.0 0.0 10.0 0.0\n")
    now = datetime(2026, 7, 21, tzinfo=UTC)
    manifest_path = run_dir / "run_manifest.json"
    domain = {
        "nx": 100 if configuration is None else 220,
        "ny": 1,
        "nz": 100 if configuration is None else 125,
        "dx_m": 200.0 if configuration is None else 1000.0,
        "dy_m": 200.0 if configuration is None else 1000.0,
        "dz_m": 200.0,
        ("active_model_top_m" if configuration is None else "active_top_m"): (
            20_000.0 if configuration is None else 25_000.0
        ),
    }
    run_configuration: dict[str, Any] = {
        "duration_seconds": 2_160 if configuration is None else 4_000,
        "output_cadence_seconds": 216 if configuration is None else 200,
        "domain": domain,
        "terrain": {
            "height_m": 400.0 if configuration is None else 2_000.0,
            "half_width_m": 1_000.0 if configuration is None else 10_000.0,
            "center_m": 100.0 if configuration is None else 500.0,
        },
    }
    if configuration is not None:
        run_configuration["mountain_waves_configuration"] = configuration.model_dump(mode="json")
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=case_id, schema_version="test-v1"),
        controls={},
        run_configuration=run_configuration,
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


def _configuration() -> MountainWavesConfiguration:
    return MountainWavesConfiguration.model_validate(
        {
            "terrain": {"height_m": 2000.0, "half_width_m": 10000.0, "center_m": 500.0},
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
    )


def _parent_namelist(*, dry: bool) -> str:
    values = {
        "nx": "100" if dry else "220",
        "ny": "1",
        "nz": "100" if dry else "125",
        "dx": "200.0" if dry else "1000.0",
        "dy": "200.0" if dry else "1000.0",
        "dz": "200.0",
        "timax": "2160.0" if dry else "4000.0",
        "tapfrq": "216.0" if dry else "200.0",
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

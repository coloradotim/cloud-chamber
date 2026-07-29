import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

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
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import StormExaminationError
from cloud_chamber.supercell_presentation import (
    BASE_PRESENTATION_ASSIGNMENTS,
    LOCKED_SCIENCE_ASSIGNMENTS,
    PRESENTATION_PROFILE_ID,
)
from cloud_chamber.supercells_world import (
    REFERENCE_SIMULATION_ID,
    STRAIGHT_LINE_SIMULATION_ID,
    _validate_builtin_source_identity,
    supercells_world_detail,
)


def _settings(runtime_home: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


@pytest.fixture(autouse=True)
def _accepted_builtin_parent_eligibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.supercells_world._builtin_parent_eligibility",
        lambda _settings, _simulation_id, _run_id: (
            True,
            "Accepted retained presentation evidence.",
        ),
    )


def test_world_exposes_stable_identity_and_data_driven_timeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_inventory",
        lambda _settings, _simulation_id: tuple(
            (tmp_path / f"cm1out_{index + 1:06d}.nc", float(index * 120)) for index in range(91)
        ),
    )

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.world_id == "supercells"
    assert detail.display_name == "Supercells"
    assert len(detail.simulations) == 2
    simulation = detail.reference_simulation
    assert simulation.simulation_id == "supercells_quarter_circle_reference"
    assert simulation.display_name == "Quarter-Circle Supercell"
    assert simulation.run_id == "quarter-circle-supercell-presentation-v1-20260723"
    assert simulation.case_id == "cm1_r21_1_quarter_circle_supercell_presentation_v1"
    assert simulation.explore_available is True
    assert simulation.saved_output_count == 91
    assert simulation.model_end_seconds == 10_800
    assert simulation.history_cadence_seconds == 120
    assert simulation.default_explore_time_index == 37
    assert detail.capabilities.lab is False
    variation = detail.simulations[1]
    assert variation.simulation_id == "supercells_straight_line_hodograph"
    assert variation.display_name == "Straight-Line Hodograph Supercell"
    assert variation.role == "variation"
    assert variation.parent_simulation_id == simulation.simulation_id
    assert detail.capabilities.compare is True
    assert detail.summary().simulation_count == 2


def test_world_inventory_does_not_deeply_revalidate_parent_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.storm_examination_inventory",
        lambda _settings, _simulation_id: ((tmp_path / "cm1out_000001.nc", 0.0),),
    )
    deep_calls = 0

    def deep_validation(
        _settings: CloudChamberSettings,
        _simulation_id: str,
        _run_id: str,
    ) -> tuple[bool, str]:
        nonlocal deep_calls
        deep_calls += 1
        return True, "Validated."

    monkeypatch.setattr(
        "cloud_chamber.supercells_world._builtin_parent_eligibility",
        deep_validation,
    )

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.capabilities.create_variation is True
    assert deep_calls == 0


def test_world_remains_usable_when_retained_output_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(_settings: CloudChamberSettings, _simulation_id: str) -> None:
        raise StormExaminationError("The accepted Gate B retained output is unavailable.")

    monkeypatch.setattr("cloud_chamber.supercells_world.storm_examination_inventory", unavailable)

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.availability_state == "unavailable"
    assert detail.reference_simulation.technical_state == "missing"
    assert detail.reference_simulation.explore_available is False
    assert detail.simulations[0].simulation_id == "supercells_quarter_circle_reference"
    assert detail.simulations[1].simulation_id == "supercells_straight_line_hodograph"
    assert detail.summary().simulation_count == 0


def test_world_exposes_one_run_without_inventing_a_compare_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def inventory(
        _settings: CloudChamberSettings, simulation_id: str
    ) -> tuple[tuple[Path, float], ...]:
        if simulation_id == "supercells_straight_line_hodograph":
            raise StormExaminationError(
                "The controlled straight-line presentation output is unavailable."
            )
        return tuple(
            (tmp_path / f"cm1out_{index + 1:06d}.nc", float(index * 120)) for index in range(91)
        )

    monkeypatch.setattr("cloud_chamber.supercells_world.storm_examination_inventory", inventory)

    detail = supercells_world_detail(_settings(tmp_path))

    assert detail.availability_state == "partial"
    assert detail.reference_simulation.explore_available is True
    assert detail.simulations[1].explore_available is False
    assert detail.capabilities.compare is False
    assert detail.summary().simulation_count == 1


def test_builtin_quarter_circle_parent_revalidates_complete_case_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _builtin_identity_fixture(
        tmp_path,
        monkeypatch,
        simulation_id=REFERENCE_SIMULATION_ID,
    )

    _validate_builtin_source_identity(**fixture)

    namelist_path = fixture["manifest_path"].parent / "namelist.input"
    namelist_path.write_text(namelist_path.read_text().replace("isnd = 5", "isnd = 6"))
    with pytest.raises(ValueError, match="namelist differs"):
        _validate_builtin_source_identity(**fixture)


def test_builtin_straight_line_parent_revalidates_patch_build_and_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _builtin_identity_fixture(
        tmp_path,
        monkeypatch,
        simulation_id=STRAIGHT_LINE_SIMULATION_ID,
    )

    _validate_builtin_source_identity(**fixture)

    status = fixture["manifest"].cm1_source_customization_status
    assert isinstance(status, dict)
    built_source = (
        Path(fixture["settings"].runtime_home)
        / "cm1_source_builds"
        / (Path(status["build_root"]).name)
        / "src"
        / "base.F"
    )
    built_source.write_bytes(b"mutated")
    with pytest.raises(ValueError, match="isolated build source"):
        _validate_builtin_source_identity(**fixture)


def _builtin_identity_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    simulation_id: str,
) -> dict[str, Any]:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1r21.1"
    run_directory = cm1_root / "run"
    source_root = cm1_root
    source_path = source_root / "src" / "base.F"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("pinned-base-source")
    run_directory.mkdir(parents=True)
    canonical_executable = run_directory / "cm1.exe"
    canonical_executable.write_bytes(b"canonical-cm1")
    canonical_hash = hashlib.sha256(canonical_executable.read_bytes()).hexdigest()
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    critical_sources = {"src/base.F": source_hash}
    provenance_record = {
        "source_manifest_sha256": "test-source-manifest",
        "critical_source_sha256": critical_sources,
        "executable_sha256": canonical_hash,
    }
    provenance = SimpleNamespace(
        source_root=source_root,
        run_directory=run_directory,
        executable_path=canonical_executable,
        report_record=lambda: provenance_record,
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.collect_cm1_provenance",
        lambda _settings: provenance,
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.CM1_SOURCE_MANIFEST_SHA256",
        "test-source-manifest",
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.CRITICAL_SOURCE_SHA256",
        critical_sources,
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.CM1_EXECUTABLE_SHA256",
        canonical_hash,
    )
    monkeypatch.setattr(
        "cloud_chamber.supercells_world.PINNED_BASE_F_SHA256",
        source_hash,
    )

    settings = CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=run_directory,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )
    run_id = "quarter-parent" if simulation_id == REFERENCE_SIMULATION_ID else "straight-parent"
    case_id = f"{run_id}-case"
    run_dir = runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    assignments = {
        **BASE_PRESENTATION_ASSIGNMENTS,
        **LOCKED_SCIENCE_ASSIGNMENTS,
        "timax": "10800.0",
        "tapfrq": "120.0",
    }
    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        assignments["iwnd"] = "12"
    (run_dir / "namelist.input").write_text(
        " &param0\n"
        + "".join(f" {name} = {value},\n" for name, value in assignments.items())
        + " /\n"
    )
    output = run_dir / "cm1out_000001.nc"
    output.write_bytes(b"CDF")
    now = datetime(2026, 7, 29, tzinfo=UTC)
    manifest = RunManifest(
        run_id=run_id,
        scenario=ScenarioReference(id=case_id, schema_version="test-v1"),
        controls={},
        run_configuration={
            "simulation_id": simulation_id,
            "source_lock": provenance_record,
            "source_run": {"run_id": "source-run"},
            "gate_a_source_lock": {"sha256": "gate-a"},
        },
        physical_question="How does the storm evolve?",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(run_dir),
            manifest_path=str(run_dir / "run_manifest.json"),
            namelist_input=str(run_dir / "namelist.input"),
        ),
        runtime_paths=RuntimePaths(runtime_home=str(runtime_home)),
        app=AppMetadata(app_version="test", commit="test-commit"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.NEEDS_REVIEW,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        outputs=OutputMetadata(netcdf_paths=[str(output)]),
        created_at=now,
        updated_at=now,
        user=UserMetadata(name=run_id),
    )
    manifest.execution.exit_code = 0
    manifest.execution.command = [str(canonical_executable)]
    manifest.execution.executable_sha256 = canonical_hash
    hodograph = "quarter_circle"

    if simulation_id == STRAIGHT_LINE_SIMULATION_ID:
        hodograph = "straight_line"
        patched_source = b"patched-straight-line-source"
        patched_hash = hashlib.sha256(patched_source).hexdigest()
        artifact = {
            "original_source_sha256": source_hash,
            "patched_source_sha256": patched_hash,
            "wind_profile": {"family": "straight"},
        }
        monkeypatch.setattr(
            "cloud_chamber.supercells_world.straight_line_hodograph_artifact",
            lambda _source: artifact,
        )
        customization_path = run_dir / "straight_line_hodograph_customization.json"
        customization_path.write_text(json.dumps(artifact))
        build_root = runtime_home / "cm1_source_builds" / "straight-build"
        built_source = build_root / "src" / "base.F"
        built_source.parent.mkdir(parents=True)
        built_source.write_bytes(patched_source)
        custom_executable = run_dir / "cm1_cloud_chamber_custom.exe"
        custom_executable.write_bytes(b"straight-cm1")
        custom_hash = hashlib.sha256(custom_executable.read_bytes()).hexdigest()
        status = {
            "schema_version": "cm1_source_customization_status_v1",
            "customization_kind": "straight_line_hodograph_v1",
            "run_id": run_id,
            "build_root": f"/relocated/cm1_source_builds/{build_root.name}",
            "customization_manifest": f"/relocated/runs/{run_id}/{customization_path.name}",
            "original_target_sha256": source_hash,
            "patched_target_sha256": patched_hash,
            "patched_files": ["src/base.F"],
            "source_restored_after_build": "not_modified_isolated_build_tree",
            "build_command": ["make"],
            "custom_executable": f"/relocated/runs/{run_id}/{custom_executable.name}",
            "custom_executable_sha256": custom_hash,
            "hodograph_profile": artifact["wind_profile"],
            "no_silent_hodograph_fallback": True,
        }
        (run_dir / "cm1_source_customization_applied.json").write_text(json.dumps(status))
        manifest.generated_inputs.cm1_source_customization = (
            f"/relocated/runs/{run_id}/{customization_path.name}"
        )
        manifest.cm1_source_customization_status = status
        manifest.execution.command = [f"/relocated/runs/{run_id}/{custom_executable.name}"]
        manifest.execution.executable_sha256 = custom_hash

    verified_generated_inputs: dict[str, str] = {}
    (run_dir / "case_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "case_id": case_id,
                "simulation_id": simulation_id,
                "profile_id": PRESENTATION_PROFILE_ID,
                "hodograph": hodograph,
                "cm1_provenance": provenance_record,
                "generated_input_sha256": verified_generated_inputs,
                "source_run": manifest.run_configuration["source_run"],
                "gate_a_source_lock": manifest.run_configuration["gate_a_source_lock"],
            }
        )
    )
    return {
        "settings": settings,
        "simulation_id": simulation_id,
        "manifest": manifest,
        "manifest_path": run_dir / "run_manifest.json",
        "verified_generated_inputs": verified_generated_inputs,
    }

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import supercell_presentation
from cloud_chamber.run_manifest import (
    AppMetadata,
    ExecutionMetadata,
    GeneratedInputs,
    LifecycleState,
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
from cloud_chamber.supercell_benchmark import CM1Provenance
from cloud_chamber.supercell_presentation import (
    CHARACTERIZATION_SPEC,
    MINIMUM_POST_RUN_FREE_BYTES,
    PRESENTATION_SPEC,
    PresentationStorageEstimate,
    estimate_storage,
    generate_presentation_package,
    render_presentation_namelist,
    verify_presentation_package,
)


def _official_namelist() -> str:
    assignments = {
        **supercell_presentation.EXPECTED_OFFICIAL_ASSIGNMENTS,
        **supercell_presentation.LOCKED_SCIENCE_ASSIGNMENTS,
    }
    return (
        " &param0\n"
        + "".join(f" {name} = {value},\n" for name, value in assignments.items())
        + " /\n"
    )


def _settings(tmp_path: Path) -> CloudChamberSettings:
    cm1_root = tmp_path / "cm1"
    run_dir = cm1_root / "run"
    run_dir.mkdir(parents=True)
    return CloudChamberSettings(
        runtime_home=tmp_path / "runtime",
        cm1_root=cm1_root,
        cm1_run_dir=run_dir,
        cache_dir=tmp_path / "runtime/cache",
        log_dir=tmp_path / "runtime/logs",
    )


def _provenance(tmp_path: Path) -> CM1Provenance:
    root = tmp_path / "cm1"
    run_dir = root / "run"
    namelist = root / "official-namelist.input"
    namelist.write_text(_official_namelist())
    executable = run_dir / "cm1.exe"
    executable.write_text("fake executable\n")
    return CM1Provenance(
        release="21.1",
        official_commit="official",
        source_root=root,
        run_directory=run_dir,
        executable_path=executable,
        supercell_namelist_path=namelist,
        source_manifest_sha256="a" * 64,
        executable_sha256="b" * 64,
        readme_namelist_sha256="c" * 64,
        supercell_namelist_sha256="d" * 64,
        supercell_readme_sha256="e" * 64,
        critical_source_sha256={"src/base.F": "f" * 64},
        netcdf_link_evidence=["libnetcdf.dylib"],
    )


def _write_accepted_source(settings: CloudChamberSettings) -> None:
    source_dir = settings.runtime_home / "runs" / supercell_presentation.SOURCE_RUN_ID
    source_dir.mkdir(parents=True)
    manifest_path = source_dir / "run_manifest.json"
    now = datetime.now(UTC)
    manifest = RunManifest(
        run_id=supercell_presentation.SOURCE_RUN_ID,
        scenario=ScenarioReference(
            id=supercell_presentation.SOURCE_CASE_ID,
            schema_version="supercell_gate_b_v1",
        ),
        controls={},
        run_configuration={},
        physical_question="source",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(source_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(source_dir / "namelist.input"),
        ),
        runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home)),
        app=AppMetadata(app_version="test", commit="source"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        created_at=now,
        updated_at=now,
        execution=ExecutionMetadata(exit_code=0),
        user=UserMetadata(name="source"),
    )
    write_run_manifest(manifest_path, manifest)
    (source_dir / supercell_presentation.SOURCE_EVIDENCE_FILENAME).write_text(
        json.dumps(
            {
                "run_id": supercell_presentation.SOURCE_RUN_ID,
                "case_id": supercell_presentation.SOURCE_CASE_ID,
                "final_disposition": "advance_to_storm_examination_validation",
                "manual_structural_review": {
                    "judgment": "supports_coherent_persistent_rotating_supercell"
                },
            }
        )
    )


def test_final_contract_materially_improves_space_time_and_duration() -> None:
    assert PRESENTATION_SPEC.scalar_cells == 6 * 120 * 120 * 40
    assert PRESENTATION_SPEC.integration_steps == 3 * (7200 // 6)
    assert PRESENTATION_SPEC.duration_seconds == 10_800
    assert PRESENTATION_SPEC.output_cadence_seconds == 120
    assert len(PRESENTATION_SPEC.expected_times_seconds) == 91
    assert CHARACTERIZATION_SPEC.changed_assignments["nx"] == "240"
    assert CHARACTERIZATION_SPEC.changed_assignments["timax"] == "300.0"


def test_namelist_changes_only_declared_presentation_assignments() -> None:
    official = _official_namelist()

    rendered, differences = render_presentation_namelist(official, PRESENTATION_SPEC)

    names = {item.name for item in differences}
    assert names == set(PRESENTATION_SPEC.changed_assignments)
    assert {item.reason for item in differences} == {
        "output_transport",
        "presentation_grid",
        "presentation_timing",
        "bounded_output_inventory",
    }
    assert " output_w = 0," in rendered
    assert " output_winterp = 1," in rendered
    assert " output_q = 1," in rendered
    assert " output_uh = 1," in rendered
    assert " timax = 10800.0," in rendered


def test_storage_floor_uses_no_compression_credit(tmp_path: Path) -> None:
    storage = estimate_storage(PRESENTATION_SPEC, tmp_path)
    expected_history_bytes = (
        len(supercell_presentation.REQUIRED_3D_FIELDS) * 240 * 240 * 60
        + len(supercell_presentation.REQUIRED_2D_FIELDS) * 240 * 240
    ) * 4

    assert storage.expected_history_count == 91
    assert storage.uncompressed_numeric_history_floor_bytes == expected_history_bytes * 91
    assert storage.compression_credit_bytes == 0
    assert storage.required_free_bytes == (
        storage.uncompressed_numeric_history_floor_bytes + MINIMUM_POST_RUN_FREE_BYTES
    )


def test_package_and_preflight_are_nonexecuting_and_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _write_accepted_source(settings)
    provenance = _provenance(tmp_path)
    monkeypatch.setattr(
        supercell_presentation,
        "verified_clean_git_commit",
        lambda: "implementation",
    )
    monkeypatch.setattr(supercell_presentation, "active_cm1_processes", lambda: [])
    monkeypatch.setattr(
        supercell_presentation,
        "verify_gate_a_source_lock",
        lambda: {"logical_path": "gate-a.md", "sha256": "source-lock"},
    )
    monkeypatch.setattr(
        supercell_presentation,
        "collect_cm1_provenance",
        lambda _settings: provenance,
    )
    monkeypatch.setattr(
        supercell_presentation,
        "estimate_storage",
        lambda _spec, _path: PresentationStorageEstimate(
            expected_history_count=2,
            scalar_grid=[240, 240, 60],
            scalar_3d_array_count=19,
            scalar_2d_array_count=4,
            uncompressed_numeric_history_floor_bytes=1,
            required_free_bytes=1,
            available_free_bytes=10,
            passed=True,
        ),
    )

    package = generate_presentation_package(
        settings=settings,
        spec=CHARACTERIZATION_SPEC,
    )
    preflight = verify_presentation_package(
        settings=settings,
        package=package,
        require_clean_head=True,
    )

    assert preflight.passed is True
    assert all(preflight.checks.values())
    assert not list(package.package_dir.glob("cm1out_*.nc"))
    assert json.loads(package.case_manifest_path.read_text())["execution_authorization"] == {
        "duration_seconds": 300,
        "process_count": 1,
        "retry_allowed": False,
        "tuning_matrix_allowed": False,
    }


def test_completed_validation_rejects_non_finite_required_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = CHARACTERIZATION_SPEC
    settings = _settings(tmp_path)
    package_dir = settings.runtime_home / "runs" / spec.run_id
    package_dir.mkdir(parents=True)
    now = datetime.now(UTC)
    manifest_path = package_dir / "run_manifest.json"
    namelist_path = package_dir / "namelist.input"
    namelist_path.write_text(" &param0\n /\n")
    generated_hash = supercell_presentation.sha256_file(namelist_path)
    manifest = RunManifest(
        run_id=spec.run_id,
        scenario=ScenarioReference(id=spec.case_id, schema_version="test"),
        controls={},
        run_configuration={"generated_input_sha256": {"namelist.input": generated_hash}},
        physical_question="test",
        expected_diagnostics=[],
        generated_inputs=GeneratedInputs(
            run_directory=str(package_dir),
            manifest_path=str(manifest_path),
            namelist_input=str(namelist_path),
        ),
        runtime_paths=RuntimePaths(runtime_home=str(settings.runtime_home)),
        app=AppMetadata(app_version="test", commit="implementation"),
        lifecycle_state=LifecycleState.COMPLETED,
        validation_status=ValidationStatus.VALID,
        provenance=ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        created_at=now,
        updated_at=now,
        execution=ExecutionMetadata(
            exit_code=0,
            started_at=now,
            finished_at=now,
            stdout_log=str(package_dir / "stdout.log"),
            stderr_log=str(package_dir / "stderr.log"),
        ),
        user=UserMetadata(name="test"),
    )
    write_run_manifest(manifest_path, manifest)
    (package_dir / "stdout.log").write_text("Program terminated normally\n")
    (package_dir / "stderr.log").write_text("")
    xr.Dataset({"time": ("time", np.array([0.0], dtype=np.float32))}).to_netcdf(
        package_dir / "cm1out_stats.nc"
    )
    for index, time_seconds in enumerate(spec.expected_times_seconds, start=1):
        values = np.array([[[[np.nan if index == 2 else 1.0]]]], dtype=np.float32)
        xr.Dataset(
            {
                "time": ("time", np.array([time_seconds], dtype=np.float32), {"units": "seconds"}),
                "winterp": (("time", "zh", "yh", "xh"), values, {"units": "m/s"}),
                "rain": (
                    ("time", "yh", "xh"),
                    np.zeros((1, 1, 1), dtype=np.float32),
                    {"units": "cm"},
                ),
            },
            coords={
                "xh": np.array([0.0]),
                "yh": np.array([0.0]),
                "zh": np.array([0.0]),
            },
        ).to_netcdf(package_dir / f"cm1out_{index:06d}.nc")
    package = supercell_presentation.SupercellPresentationPackage(
        spec=spec,
        package_dir=package_dir,
        manifest_path=manifest_path,
        case_manifest_path=package_dir / "case_manifest.json",
        storage_estimate_path=package_dir / "storage_estimate.json",
        implementation_commit="implementation",
    )
    monkeypatch.setattr(supercell_presentation, "REQUIRED_3D_FIELDS", ("winterp",))
    monkeypatch.setattr(supercell_presentation, "REQUIRED_2D_FIELDS", ("rain",))
    monkeypatch.setattr(
        supercell_presentation,
        "REQUIRED_OUTPUT_FIELDS",
        ("winterp", "rain"),
    )
    monkeypatch.setattr(supercell_presentation, "_validate_grid", lambda _dataset: None)
    monkeypatch.setattr(supercell_presentation, "_validate_units", lambda _dataset: None)
    monkeypatch.setattr(
        supercell_presentation,
        "collect_cm1_provenance",
        lambda _settings: None,
    )

    with pytest.raises(
        supercell_presentation.SupercellPresentationError,
        match="non-finite",
    ):
        supercell_presentation.validate_completed_presentation_run(
            settings=settings,
            package=package,
        )

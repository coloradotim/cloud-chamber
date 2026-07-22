from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import supercell_benchmark
from cloud_chamber.run_manifest import (
    ExecutionMetadata,
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.supercell_benchmark import (
    CASE_ID,
    EXPECTED_OUTPUT_TIMES_SECONDS,
    MINIMUM_FREE_BYTES,
    CM1Provenance,
    SupercellBenchmarkError,
    audit_supercell_namelist,
    evaluate_supercell_run,
    generate_supercell_package,
    preflight_supercell_package,
    render_supercell_namelist,
    render_supercell_run_report,
)


def _official_namelist() -> str:
    assignments = dict(supercell_benchmark.LOCKED_NAMELIST_VALUES)
    assignments.update({"output_format": "1", "output_filetype": "1"})
    return (
        " &test\n"
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
        official_commit=supercell_benchmark.CM1_OFFICIAL_COMMIT,
        source_root=root,
        run_directory=run_dir,
        executable_path=executable,
        supercell_namelist_path=namelist,
        source_manifest_sha256=supercell_benchmark.CM1_SOURCE_MANIFEST_SHA256,
        executable_sha256=supercell_benchmark.CM1_EXECUTABLE_SHA256,
        readme_namelist_sha256=supercell_benchmark.CM1_README_NAMELIST_SHA256,
        supercell_namelist_sha256=supercell_benchmark.CM1_SUPERCELL_NAMELIST_SHA256,
        supercell_readme_sha256=supercell_benchmark.CM1_SUPERCELL_README_SHA256,
        critical_source_sha256=dict(supercell_benchmark.CRITICAL_SOURCE_SHA256),
        netcdf_link_evidence=["libnetcdff.dylib"],
    )


def _patch_preconditions(
    monkeypatch: pytest.MonkeyPatch,
    provenance: CM1Provenance,
) -> None:
    monkeypatch.setattr(supercell_benchmark, "verified_clean_git_commit", lambda: "abc123")
    monkeypatch.setattr(
        supercell_benchmark,
        "verify_gate_a_source_lock",
        lambda: {"logical_path": "gate-a.md", "sha256": "source-lock"},
    )
    monkeypatch.setattr(supercell_benchmark, "collect_cm1_provenance", lambda _settings: provenance)
    monkeypatch.setattr(supercell_benchmark, "active_cm1_processes", lambda: [])
    monkeypatch.setattr(supercell_benchmark, "prior_supercell_executions", lambda *_args: [])


def test_namelist_has_exact_two_transport_changes() -> None:
    official = _official_namelist()

    generated = render_supercell_namelist(official)
    audit = audit_supercell_namelist(official, generated)

    assert [item.name for item in audit.differences] == ["output_format", "output_filetype"]
    assert audit.byte_equivalent_after_restoring_approved_values is True
    assert audit.locked_assignments["output_interp"] == "0"


def test_namelist_rejects_any_scientific_change() -> None:
    official = _official_namelist()
    generated = render_supercell_namelist(official).replace(" iinit = 1,", " iinit = 3,")

    with pytest.raises(SupercellBenchmarkError, match="Unapproved namelist difference iinit"):
        audit_supercell_namelist(official, generated)


def test_coordinate_spacing_accepts_float32_kilometer_precision_only() -> None:
    observed_x_m = (
        np.asarray(
            [-59.500003814697266, -58.5, -57.5, -56.500003814697266],
            dtype=np.float64,
        )
        * 1000.0
    )
    materially_wrong_x_m = observed_x_m.copy()
    materially_wrong_x_m[2] += 0.1

    assert supercell_benchmark._coordinate_spacing_matches(observed_x_m, 1000.0)
    assert not supercell_benchmark._coordinate_spacing_matches(
        materially_wrong_x_m,
        1000.0,
    )


def test_package_and_explicit_preflight_are_nonexecuting_and_input_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    provenance = _provenance(tmp_path)
    _patch_preconditions(monkeypatch, provenance)

    package = generate_supercell_package(settings=settings, run_id="supercell-fixture")
    preflight = preflight_supercell_package(settings=settings, package=package)
    manifest = load_run_manifest(package.manifest_path)
    checklist = json.loads((package.package_dir / "runtime_file_checklist.json").read_text())

    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.execution.process_id is None
    assert manifest.scenario.id == CASE_ID
    assert manifest.generated_inputs.input_sounding is None
    assert not (package.package_dir / "input_sounding").exists()
    assert checklist["consumed_files"] == []
    assert checklist["required_files"] == []
    assert preflight.passed is True
    assert preflight.storage.required_free_bytes == MINIMUM_FREE_BYTES
    assert all(preflight.checks.values())


def _tiny_grid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(supercell_benchmark, "NX", 4)
    monkeypatch.setattr(supercell_benchmark, "NY", 3)
    monkeypatch.setattr(supercell_benchmark, "NZ", 4)
    monkeypatch.setattr(supercell_benchmark, "ACTIVE_TOP_M", 2000.0)
    monkeypatch.setattr(supercell_benchmark, "RAYLEIGH_ONSET_M", 1500.0)


def _write_tiny_histories(
    package_dir: Path,
    *,
    nonfinite_frame: int | None = None,
) -> list[Path]:
    nx, ny, nz = 4, 3, 4
    xh = np.arange(nx, dtype=np.float32) - 1.5
    xf = np.arange(nx + 1, dtype=np.float32) - 2.0
    yh = np.arange(ny, dtype=np.float32) - 1.0
    yf = np.arange(ny + 1, dtype=np.float32) - 1.5
    zh = np.arange(nz, dtype=np.float32) * 0.5 + 0.25
    zf = np.arange(nz + 1, dtype=np.float32) * 0.5
    paths: list[Path] = []
    for number, time_seconds in enumerate(EXPECTED_OUTPUT_TIMES_SECONDS, start=1):
        scalar = np.zeros((1, nz, ny, nx), dtype=np.float32)
        w_scalar = scalar.copy()
        w_scalar[:, 2, 1, 2] = 20.0 if time_seconds >= 2700 else float(time_seconds / 900)
        if nonfinite_frame == number:
            w_scalar[:, 0, 0, 0] = np.nan
        hydrometeor = np.where(w_scalar > 5.0, 1.0e-3, 0.0).astype(np.float32)
        dbz = np.where(w_scalar > 5.0, 45.0, -10.0).astype(np.float32)
        w_native = np.zeros((1, nz + 1, ny, nx), dtype=np.float32)
        w_native[:, 2, 1, 2] = np.max(w_scalar)
        surface = np.zeros((1, ny, nx), dtype=np.float32)
        if time_seconds >= 2700:
            surface[:, 1, 2] = 1.0
        uh = surface * 100.0
        data_vars: dict[str, tuple[tuple[str, ...], np.ndarray, dict[str, str]]] = {
            "th": (("time", "zh", "yh", "xh"), 300.0 + scalar, {"units": "K"}),
            "prs": (("time", "zh", "yh", "xh"), 90000.0 + scalar, {"units": "Pa"}),
            "qv": (("time", "zh", "yh", "xh"), 0.012 + scalar, {"units": "kg/kg"}),
            "dbz": (("time", "zh", "yh", "xh"), dbz, {"units": "dBZ"}),
            "uinterp": (("time", "zh", "yh", "xh"), scalar, {"units": "m/s"}),
            "vinterp": (("time", "zh", "yh", "xh"), scalar, {"units": "m/s"}),
            "winterp": (("time", "zh", "yh", "xh"), w_scalar, {"units": "m/s"}),
            "xvort": (("time", "zh", "yh", "xh"), scalar, {"units": "1/s"}),
            "yvort": (("time", "zh", "yh", "xh"), scalar, {"units": "1/s"}),
            "zvort": (
                ("time", "zh", "yh", "xh"),
                np.where(w_scalar > 5.0, 0.01, 0.0).astype(np.float32),
                {"units": "1/s"},
            ),
            "u": (
                ("time", "zh", "yh", "xf"),
                np.zeros((1, nz, ny, nx + 1), dtype=np.float32),
                {"units": "m/s"},
            ),
            "v": (
                ("time", "zh", "yf", "xh"),
                np.zeros((1, nz, ny + 1, nx), dtype=np.float32),
                {"units": "m/s"},
            ),
            "w": (("time", "zf", "yh", "xh"), w_native, {"units": "m/s"}),
            "uh": (("time", "yh", "xh"), uh, {"units": "m2/s2"}),
            "rain": (("time", "yh", "xh"), surface, {"units": "kg/m2"}),
        }
        for name in ("qc", "qr", "qi", "qs", "qg"):
            data_vars[name] = (
                ("time", "zh", "yh", "xh"),
                hydrometeor,
                {"units": "kg/kg"},
            )
        for name in ("nci", "ncs", "ncr", "ncg"):
            data_vars[name] = (
                ("time", "zh", "yh", "xh"),
                np.where(hydrometeor > 0.0, 1000.0, 0.0).astype(np.float32),
                {"units": "#/kg"},
            )
        for name in ("tke", "kmh", "kmv", "khh", "khv"):
            data_vars[name] = (
                ("time", "zf", "yh", "xh"),
                np.zeros_like(w_native),
                {"units": "m2/s2" if name == "tke" else "m2/s"},
            )
        for name in supercell_benchmark.SURFACE_FIELDS:
            if name not in data_vars:
                data_vars[name] = (
                    ("time", "yh", "xh"),
                    surface,
                    {"units": "native"},
                )
        dataset = xr.Dataset(
            data_vars=data_vars,
            coords={
                "time": ("time", [float(time_seconds)], {"units": "s"}),
                "xh": ("xh", xh, {"units": "km"}),
                "xf": ("xf", xf, {"units": "km"}),
                "yh": ("yh", yh, {"units": "km"}),
                "yf": ("yf", yf, {"units": "km"}),
                "zh": ("zh", zh, {"units": "km"}),
                "zf": ("zf", zf, {"units": "km"}),
            },
            attrs={"case": "tiny supercell fixture", "umove": "12.5", "vmove": "3.0"},
        )
        path = package_dir / f"cm1out_{number:06d}.nc"
        dataset.to_netcdf(path)
        dataset.close()
        paths.append(path)
    return paths


def _write_stats(package_dir: Path) -> Path:
    times = np.arange(0.0, 7200.0 + 60.0, 60.0)
    dataset = xr.Dataset(
        data_vars={
            "cflmax": (("time",), np.linspace(0.1, 0.8, times.size)),
            "tmass": (("time",), np.ones(times.size)),
        },
        coords={"time": (("time",), times, {"units": "s"})},
    )
    path = package_dir / "cm1out_stats.nc"
    dataset.to_netcdf(path)
    dataset.close()
    return path


def _mark_completed(
    package: supercell_benchmark.SupercellPackageResult, outputs: list[Path]
) -> None:
    log_dir = package.package_dir / "logs"
    log_dir.mkdir()
    stdout = log_dir / "stdout.log"
    stderr = log_dir / "stderr.log"
    stdout.write_text("Program terminated normally\n")
    stderr.write_text("")
    manifest = load_run_manifest(package.manifest_path)
    started = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
    completed = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "execution": ExecutionMetadata(
                command=["cm1.exe"],
                process_id=123,
                started_at=started,
                finished_at=started.replace(minute=20),
                exit_code=0,
                stdout_log=str(stdout),
                stderr_log=str(stderr),
            ),
            "outputs": OutputMetadata(netcdf_paths=[str(path) for path in outputs]),
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        }
    )
    write_run_manifest(package.manifest_path, completed)


def test_evaluator_reads_every_tiny_native_field_and_renders_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    provenance = _provenance(tmp_path)
    _patch_preconditions(monkeypatch, provenance)
    package = generate_supercell_package(settings=settings, run_id="native-fixture")
    _tiny_grid(monkeypatch)
    outputs = _write_tiny_histories(package.package_dir)
    outputs.append(_write_stats(package.package_dir))
    _mark_completed(package, outputs)

    evidence = evaluate_supercell_run(settings=settings, package=package)
    report = render_supercell_run_report(evidence)

    assert evidence.output_inventory["history_times_seconds"] == list(EXPECTED_OUTPUT_TIMES_SECONDS)
    assert evidence.implementation_commit == "abc123"
    assert evidence.evaluation_commit == "abc123"
    assert evidence.integrity_checks["all_required_fields_finite"] is True
    assert evidence.rotation_and_organization["sustained_organized_rotation"] is True
    boundary_times = [
        item["time_seconds"]
        for item in evidence.boundaries_translation_and_damping[
            "primary_updraft_boundary_distances_by_time"
        ]
    ]
    assert boundary_times == [float(value) for value in EXPECTED_OUTPUT_TIMES_SECONDS[1:]]
    assert evidence.evolution["hydrometeor_species_with_material_evolution"] == [
        "qc",
        "qr",
        "qi",
        "qs",
        "qg",
    ]
    assert "## 21. Final disposition" in report
    assert evidence.final_disposition in report


def test_evaluator_rejects_nonfinite_required_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    provenance = _provenance(tmp_path)
    _patch_preconditions(monkeypatch, provenance)
    package = generate_supercell_package(settings=settings, run_id="nonfinite-fixture")
    _tiny_grid(monkeypatch)
    outputs = _write_tiny_histories(package.package_dir, nonfinite_frame=4)
    outputs.append(_write_stats(package.package_dir))
    _mark_completed(package, outputs)

    with pytest.raises(SupercellBenchmarkError, match="non-finite"):
        evaluate_supercell_run(settings=settings, package=package)

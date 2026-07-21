from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import moist_mountain_wave_case
from cloud_chamber.moist_mountain_wave_case import (
    ACTIVE_TOP_M,
    EXPECTED_OUTPUT_TIMES_SECONDS,
    MATERIAL_PEAK_KG_KG,
    NX,
    NY,
    MoistMountainWavePackageResult,
    analytic_terrain_m,
    audit_input_sounding,
    audit_moist_namelist,
    evaluate_moist_mountain_wave_run,
    expected_output_times,
    generate_moist_mountain_wave_package,
    preflight_package_for_execution,
    render_input_sounding,
    render_moist_namelist,
    sounding_records,
    terrain_x_m,
    write_terrain_file,
)
from cloud_chamber.mountain_wave_case import (
    CM1Provenance,
    parse_namelist_assignments,
    reconstruct_physical_heights,
    sha256_file,
)
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


def reference_namelist_text() -> str:
    values = dict(moist_mountain_wave_case.LOCKED_NAMELIST_VALUES)
    values.update(
        {
            "nx": "100",
            "nz": "100",
            "dx": "200.0",
            "dy": "200.0",
            "timax": "2160.0",
            "tapfrq": "216.0",
            "cm1setup": "0",
            "apmasscon": "1",
            "imoist": "0",
            "sgsmodel": "1",
            "tconfig": "1",
            "irdamp": "1",
            "ptype": "5",
            "icor": "1",
            "lspgrad": "1",
            "wbc": "2",
            "ebc": "2",
            "isnd": "9",
            "iwnd": "6",
            "itern": "1",
            "fcor": "0.00010",
            "v_t": "7.0",
            "ztop": "18000.0",
            "output_format": "1",
            "output_filetype": "1",
            "output_interp": "1",
            "output_rain": "1",
            "output_dbz": "1",
        }
    )
    values["unlisted_control"] = "17"
    return (
        "\n &param0\n"
        + "".join(f" {name:<20} = {value},\n" for name, value in values.items())
        + " /\n"
    )


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1r21.1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True, exist_ok=True)
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=cm1_root,
        cm1_run_dir=cm1_run_dir,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def fake_provenance(tmp_path: Path) -> CM1Provenance:
    settings = fake_settings(tmp_path)
    assert settings.cm1_root is not None
    assert settings.cm1_run_dir is not None
    official = settings.cm1_root / "run/config_files/nh_mountain_waves/namelist.input"
    official.parent.mkdir(parents=True, exist_ok=True)
    official.write_text(reference_namelist_text())
    executable = settings.cm1_run_dir / "cm1.exe"
    executable.write_text("fake netcdf executable")
    return CM1Provenance(
        release="21.1",
        official_tag_commit="test-tag-commit",
        official_source_tag="test-source-tag",
        source_tree_path=settings.cm1_root,
        run_directory_path=settings.cm1_run_dir,
        executable_path=executable,
        executable_sha256="executable-hash",
        source_manifest_method="test source manifest",
        source_manifest_sha256="source-manifest-hash",
        readme_namelist_sha256="namelist-readme-hash",
        readme_terrain_sha256="terrain-readme-hash",
        mountain_wave_namelist_path=official,
        mountain_wave_namelist_sha256=sha256_file(official),
        critical_source_sha256={"src/init_terrain.F": "terrain-source-hash"},
        netcdf_link_evidence=["libnetcdf"],
    )


def patch_package_preconditions(monkeypatch: pytest.MonkeyPatch, provenance: CM1Provenance) -> None:
    monkeypatch.setattr(
        moist_mountain_wave_case,
        "collect_cm1_provenance",
        lambda _settings: provenance,
    )
    monkeypatch.setattr(
        moist_mountain_wave_case,
        "verified_clean_git_commit",
        lambda: "implementation-commit",
    )
    monkeypatch.setattr(moist_mountain_wave_case, "active_cm1_processes", lambda: [])
    monkeypatch.setattr(
        moist_mountain_wave_case,
        "verify_source_lock",
        lambda: {
            "relative_path": moist_mountain_wave_case.SOURCE_LOCK_RELATIVE_PATH.as_posix(),
            "sha256": moist_mountain_wave_case.SOURCE_LOCK_SHA256,
        },
    )


def test_sounding_is_exactly_derived_and_initially_unsaturated() -> None:
    text = render_input_sounding()
    audit = audit_input_sounding(text)
    records = sounding_records()

    assert len(text.splitlines()) == len(records) == 38
    assert audit["profile_row_count"] == 37
    assert audit["final_model_height_m"] == 25_846.0
    assert audit["maximum_source_relative_humidity_percent"] == 95.0
    assert audit["checks"]["missing_rh_rows_map_to_zero_qv"] is True
    assert records[0]["pressure_pa"] == 85_000
    assert records[0]["theta_k"] == pytest.approx(285.5125, abs=1.0e-4)
    assert records[0]["qv_g_kg"] == pytest.approx(1.767594, abs=1.0e-6)
    assert records[0]["u_m_s"] == pytest.approx(-4.2858, abs=1.0e-4)


def test_terrain_binary_is_exact_single_float32_record(tmp_path: Path) -> None:
    path = tmp_path / "perts.dat"
    audit = write_terrain_file(path)
    values = np.fromfile(path, dtype="<f4").reshape((NY, NX))

    assert path.stat().st_size == 4 * NX * NY
    assert values.shape == (1, 220)
    assert audit["crest_x_m"] == 500.0
    assert audit["crest_height_m"] == 2_000.0
    assert audit["maximum_analytic_slope"] == pytest.approx(0.1299038106)
    assert all(audit["checks"].values())


def test_namelist_preserves_unlisted_assignments_and_locks_complete_case() -> None:
    official = reference_namelist_text()
    generated = render_moist_namelist(official)
    audit = audit_moist_namelist(official, generated)

    assert expected_output_times(generated) == EXPECTED_OUTPUT_TIMES_SECONDS
    assert "unlisted_control" not in {difference["name"] for difference in audit["differences"]}
    assert parse_namelist_assignments(generated)["unlisted_control"] == "17"
    assert audit["all_unlisted_assignments_preserved"] is True

    altered = generated.replace(" unlisted_control", " changed_unlisted_control")
    with pytest.raises(
        moist_mountain_wave_case.MoistMountainWaveCaseError,
        match="assignment set",
    ):
        audit_moist_namelist(official, altered)


def test_package_and_repeated_hard_preflight_are_nonexecuting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = fake_settings(tmp_path)
    provenance = fake_provenance(tmp_path)
    patch_package_preconditions(monkeypatch, provenance)

    package = generate_moist_mountain_wave_package(settings=settings, run_id="moist-wave-fixture")
    preflight = preflight_package_for_execution(settings=settings, package=package)
    manifest = load_run_manifest(package.manifest_path)
    case_manifest = json.loads(package.case_manifest_path.read_text())
    checklist = json.loads((package.package_dir / "runtime_file_checklist.json").read_text())

    assert manifest.lifecycle_state == LifecycleState.PACKAGED
    assert manifest.execution.process_id is None
    assert manifest.run_recipe is None
    assert manifest.recipe_id is None
    assert case_manifest["cloud_world_id"] is None
    assert checklist["consumed_files"] == ["input_sounding", "perts.dat"]
    assert checklist["required_files"] == []
    assert preflight.passed is True
    assert all(preflight.checks.values())
    assert {path.name for path in package.generated_files} == {
        "run_manifest.json",
        "case_manifest.json",
        "namelist.input",
        "input_sounding",
        "perts.dat",
        "runtime_file_checklist.json",
        "source_namelist_diff.json",
        "source_namelist_diff.txt",
        "storage_estimate.json",
        "moist_run_report.json",
    }


def test_evaluator_detects_clear_coherent_material_gravity_wave_cloud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = fake_settings(tmp_path)
    provenance = fake_provenance(tmp_path)
    patch_package_preconditions(monkeypatch, provenance)
    package = generate_moist_mountain_wave_package(
        settings=settings, run_id="moist-wave-native-fixture"
    )
    output_paths = _write_synthetic_native_outputs(package.package_dir)
    _mark_package_completed(package, output_paths)

    evidence = evaluate_moist_mountain_wave_run(settings=settings, package=package)

    assert evidence.output_inventory["actual_times_seconds"] == list(EXPECTED_OUTPUT_TIMES_SECONDS)
    assert evidence.initial_and_upstream["initial_maximum_ql_kg_kg"] == 0.0
    assert evidence.initial_and_upstream["upstream_maximum_ql_kg_kg_all_times"] == 0.0
    assert evidence.cloud_and_wave["peak_cloud_frame"]["maximum_ql_kg_kg"] >= (MATERIAL_PEAK_KG_KG)
    assert evidence.cloud_and_wave["persistent_windows_seconds"]
    assert evidence.cloud_and_wave["descent_evaporation_frames_seconds"]
    assert evidence.geometry["physical_height_transform_maximum_abs_error_m"] == pytest.approx(0.0)
    assert all(evidence.predeclared_checks.values())
    assert json.loads(evidence.to_json_text())["case_id"] == moist_mountain_wave_case.CASE_ID


def _write_synthetic_native_outputs(package_dir: Path) -> list[Path]:
    xh_m = terrain_x_m()
    xf_m = np.arange(-110_000.0, 111_000.0, 1_000.0)
    yh_m = np.array([0.0])
    yf_m = np.array([-500.0, 500.0])
    zh_m = np.array([1_000.0, 3_000.0, 10_000.0, 24_000.0])
    zf_m = np.array([0.0, 2_000.0, 5_000.0, 15_000.0, 25_000.0])
    terrain = analytic_terrain_m(xh_m)[None, :]
    zh_physical = reconstruct_physical_heights(terrain, zh_m, active_top_m=ACTIVE_TOP_M)
    pressure = 85_000.0 * np.exp(-zh_physical / 8_000.0)
    temperature = np.full_like(pressure, 280.0)
    theta = temperature / (pressure / 100_000.0) ** (287.04 / 1004.0)
    qsat = moist_mountain_wave_case._saturation_mixing_ratio_kg_kg(temperature, pressure)
    cloud_x = np.flatnonzero((xh_m >= -2_500.0) & (xh_m <= 1_500.0))[:3]
    outputs: list[Path] = []

    for number, time_seconds in enumerate(EXPECTED_OUTPUT_TIMES_SECONDS, start=1):
        ql = np.zeros((4, 1, NX), dtype=np.float64)
        qv = 0.8 * qsat
        w = np.zeros((5, 1, NX), dtype=np.float64)
        if 2 <= number <= 8:
            for z_index in range(3):
                ql[z_index, 0, cloud_x] = 3.0e-4
                qv[z_index, 0, cloud_x] = qsat[z_index, 0, cloud_x]
                w[z_index, 0, cloud_x] = 1.0
                w[z_index + 1, 0, cloud_x] = 1.0
            descent_x = cloud_x[-1] + 1
            w[0:3, 0, descent_x] = -1.0
        dataset = xr.Dataset(
            data_vars={
                "zs": (("time", "yh", "xh"), terrain[None], {"units": "m"}),
                "zhval": (
                    ("time", "zh", "yh", "xh"),
                    zh_physical[None],
                    {"units": "m"},
                ),
                "th": (
                    ("time", "zh", "yh", "xh"),
                    theta[None],
                    {"units": "K"},
                ),
                "prs": (
                    ("time", "zh", "yh", "xh"),
                    pressure[None],
                    {"units": "Pa"},
                ),
                "qv": (
                    ("time", "zh", "yh", "xh"),
                    qv[None],
                    {"units": "kg/kg"},
                ),
                "ql": (
                    ("time", "zh", "yh", "xh"),
                    ql[None],
                    {"units": "kg/kg"},
                ),
                "u": (
                    ("time", "zh", "yh", "xf"),
                    np.full((1, 4, 1, NX + 1), 10.0),
                    {"units": "m/s"},
                ),
                "v": (
                    ("time", "zh", "yf", "xh"),
                    np.zeros((1, 4, 2, NX)),
                    {"units": "m/s"},
                ),
                "w": (
                    ("time", "zf", "yh", "xh"),
                    w[None],
                    {"units": "m/s"},
                ),
            },
            coords={
                "time": ("time", [float(time_seconds)], {"units": "s"}),
                "xh": ("xh", xh_m / 1000.0, {"units": "km"}),
                "xf": ("xf", xf_m / 1000.0, {"units": "km"}),
                "yh": ("yh", yh_m / 1000.0, {"units": "km"}),
                "yf": ("yf", yf_m / 1000.0, {"units": "km"}),
                "zh": ("zh", zh_m / 1000.0, {"units": "km"}),
                "zf": ("zf", zf_m / 1000.0, {"units": "km"}),
            },
        )
        path = package_dir / f"cm1out_{number:06d}.nc"
        dataset.to_netcdf(path)
        dataset.close()
        outputs.append(path)
    return outputs


def _mark_package_completed(
    package: MoistMountainWavePackageResult, output_paths: list[Path]
) -> None:
    stdout = package.package_dir / "stdout.log"
    stderr = package.package_dir / "stderr.log"
    stdout.write_text("Program terminated normally\n")
    stderr.write_text("")
    started = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
    finished = datetime(2026, 7, 21, 12, 2, tzinfo=UTC)
    manifest = load_run_manifest(package.manifest_path)
    completed = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "execution": ExecutionMetadata(
                command=["cm1.exe"],
                process_id=123,
                started_at=started,
                finished_at=finished,
                exit_code=0,
                stdout_log=str(stdout),
                stderr_log=str(stderr),
            ),
            "outputs": OutputMetadata(netcdf_paths=[str(path) for path in output_paths]),
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        }
    )
    write_run_manifest(package.manifest_path, completed)

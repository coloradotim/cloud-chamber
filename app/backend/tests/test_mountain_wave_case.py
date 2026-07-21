import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import mountain_wave_case
from cloud_chamber.mountain_wave_case import (
    ACTIVE_TOP_M,
    EXPECTED_OUTPUT_TIMES_SECONDS,
    CM1Provenance,
    MountainWavePackageResult,
    accepted_model_output_paths,
    analytic_itern1_terrain,
    audit_namelist,
    central_boundary_metrics,
    estimate_storage,
    evaluate_mountain_wave_run,
    expected_output_times,
    generate_mountain_wave_package,
    load_mountain_wave_package,
    lower_boundary_tangency_metrics,
    normalize_length_to_m,
    normalize_time_to_seconds,
    reconstruct_physical_heights,
    render_mountain_wave_namelist,
    resolve_active_top_m,
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
    values = {
        "nx": "100",
        "ny": "1",
        "nz": "100",
        "dx": "200.0",
        "dy": "200.0",
        "dz": "200.0",
        "dtl": "2.000",
        "timax": "2160.0",
        "tapfrq": "216.0",
        "terrain_flag": ".true.",
        "itern": "1",
        "isnd": "9",
        "iwnd": "6",
        "imoist": "0",
        "output_format": "1",
        "output_filetype": "1",
        "output_interp": "1",
        "ibalance": "0",
        "axisymm": "0",
        "imove": "0",
        "alphobc": "60.0",
        "nudgeobc": "0",
        "roflux": "0",
        "xhd": "100000.0",
        "hrdamp": "0",
        "ztop": "18000.0",
    }
    return (
        "\n &param0\n"
        + "".join(f" {name:<18} = {value},\n" for name, value in values.items())
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
        official_tag_commit=mountain_wave_case.CM1_TAG_COMMIT,
        official_source_tag=mountain_wave_case.CM1_SOURCE_TAG,
        source_tree_path=settings.cm1_root,
        run_directory_path=settings.cm1_run_dir,
        executable_path=executable,
        executable_sha256="exe-hash",
        source_manifest_method="test manifest",
        source_manifest_sha256="source-hash",
        readme_namelist_sha256="readme-hash",
        readme_terrain_sha256="terrain-readme-hash",
        mountain_wave_namelist_path=official,
        mountain_wave_namelist_sha256=mountain_wave_case.sha256_file(official),
        critical_source_sha256={"src/init_terrain.F": "terrain-source-hash"},
        netcdf_link_evidence=["libnetcdf"],
    )


def test_render_preserves_complete_official_namelist_with_exact_three_differences() -> None:
    official = reference_namelist_text()
    generated = render_mountain_wave_namelist(official)
    audit = audit_namelist(official, generated)

    assert [difference.name for difference in audit.differences] == [
        "output_format",
        "output_filetype",
        "output_interp",
    ]
    assert audit.byte_equivalent_after_restoring_approved_values is True
    assert audit.unchanged_inactive_values == mountain_wave_case.INACTIVE_AUDIT_VALUES
    assert audit.assignment_count == audit.unchanged_assignment_count + 3


def test_namelist_audit_rejects_any_additional_change() -> None:
    official = reference_namelist_text()
    generated = (
        render_mountain_wave_namelist(official)
        .replace(" timax", " timax")
        .replace("2160.0,", "1200.0,", 1)
    )

    with pytest.raises(mountain_wave_case.MountainWaveCaseError, match="Unapproved"):
        audit_namelist(official, generated)


def test_expected_times_and_storage_estimate_derive_from_generated_settings(
    tmp_path: Path,
) -> None:
    generated = render_mountain_wave_namelist(reference_namelist_text())
    estimate = estimate_storage(generated, tmp_path)

    assert expected_output_times(generated) == EXPECTED_OUTPUT_TIMES_SECONDS
    assert estimate.expected_history_count == 11
    assert estimate.precision_bytes == 4
    assert estimate.raw_history_bytes > 0
    assert estimate.estimated_total_bytes > estimate.raw_history_bytes
    assert estimate.required_free_bytes == 2 * estimate.estimated_total_bytes
    assert estimate.passed is True


def test_package_contains_only_bounded_inputs_and_labels_non_consumed_sounding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    provenance = fake_provenance(tmp_path)
    monkeypatch.setattr(mountain_wave_case, "collect_cm1_provenance", lambda _settings: provenance)
    monkeypatch.setattr(
        mountain_wave_case, "verified_clean_git_commit", lambda: "implementation-commit"
    )
    monkeypatch.setattr(mountain_wave_case, "active_cm1_processes", lambda: [])

    package = generate_mountain_wave_package(settings=settings, run_id="mountain-wave-test")
    manifest = load_run_manifest(package.manifest_path)
    case_manifest = json.loads(package.case_manifest_path.read_text())
    checklist = json.loads((package.package_dir / "runtime_file_checklist.json").read_text())

    assert set(path.name for path in package.generated_files) == {
        "run_manifest.json",
        "case_manifest.json",
        "namelist.input",
        "input_sounding",
        "dry_run_report.json",
        "runtime_file_checklist.json",
        "official_namelist_diff.json",
        "official_namelist_diff.txt",
        "storage_estimate.json",
    }
    assert manifest.app.commit == "implementation-commit"
    assert manifest.scenario.id == mountain_wave_case.CASE_ID
    assert manifest.run_recipe is None
    assert manifest.recipe_id is None
    assert case_manifest["cloud_world_id"] is None
    assert case_manifest["input_sounding_status"] == mountain_wave_case.NON_CONSUMED_SOUNDING_LABEL
    assert checklist["required_files"] == []
    assert "LANDUSE.TBL" in checklist["explicitly_not_staged"]
    assert "perts.dat" in checklist["explicitly_not_staged"]
    assert (
        "cloud chamber input_sounding notes"
        not in (package.package_dir / "input_sounding").read_text()
    )

    loaded = load_mountain_wave_package(settings=settings, run_id="mountain-wave-test")
    assert loaded.package_dir == package.package_dir
    assert loaded.implementation_commit == "implementation-commit"


def test_package_refuses_dirty_worktree_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)

    def dirty_git_output(*args: str) -> str:
        if args == ("rev-parse", "HEAD"):
            return "implementation-commit"
        if args == ("status", "--porcelain=v1", "--untracked-files=all"):
            return " M app/backend/cloud_chamber/mountain_wave_case.py"
        raise AssertionError(args)

    monkeypatch.setattr(mountain_wave_case, "_git_output", dirty_git_output)

    with pytest.raises(mountain_wave_case.MountainWaveCaseError, match="clean Git worktree"):
        generate_mountain_wave_package(settings=settings, run_id="dirty-package")
    assert not (settings.runtime_home / "runs/dirty-package").exists()


def test_collect_provenance_fails_on_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    assert settings.cm1_root is not None
    assert settings.cm1_run_dir is not None
    files = {
        settings.cm1_run_dir / "cm1.exe": b"wrong executable",
        settings.cm1_root / "README.namelist": b"readme",
        settings.cm1_root / "README.terrain": b"terrain",
        settings.cm1_root / "run/config_files/nh_mountain_waves/namelist.input": b"namelist",
    }
    for relative in mountain_wave_case.CRITICAL_SOURCE_HASHES:
        files[settings.cm1_root / relative] = relative.encode()
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(
        mountain_wave_case, "source_manifest_sha256", lambda _root: "wrong-source-manifest"
    )
    monkeypatch.setattr(mountain_wave_case, "_netcdf_link_evidence", lambda _path: ["netcdf"])

    with pytest.raises(mountain_wave_case.MountainWaveCaseError, match="provenance"):
        mountain_wave_case.collect_cm1_provenance(settings)


def test_filename_acceptance_excludes_stats_and_interpolated_output(tmp_path: Path) -> None:
    paths = [
        tmp_path / "cm1out_000002.nc",
        tmp_path / "cm1out_stats.nc",
        tmp_path / "cm1out_000001_i.nc",
        tmp_path / "cm1out_000001.nc",
        tmp_path / "cm1out_000003.nc4",
    ]

    assert [path.name for path in accepted_model_output_paths(paths)] == [
        "cm1out_000001.nc",
        "cm1out_000002.nc",
        "cm1out_000003.nc4",
    ]


def test_actual_units_are_normalized_or_rejected() -> None:
    assert normalize_length_to_m([0.0, 1.0], "km").tolist() == [0.0, 1_000.0]
    assert normalize_length_to_m([0.0, 100.0], "m").tolist() == [0.0, 100.0]
    assert normalize_time_to_seconds([0.0, 1.0], "minutes").tolist() == [0.0, 60.0]
    with pytest.raises(mountain_wave_case.MountainWaveCaseError, match="length units"):
        normalize_length_to_m([1.0], "furlong")


def test_terrain_and_physical_height_reconstruction_rejects_inert_ztop() -> None:
    x_m = np.array([-900.0, 100.0, 1_100.0])
    terrain = analytic_itern1_terrain(x_m)[None, :]
    nominal = np.array([100.0, 10_000.0, 19_900.0])
    physical = reconstruct_physical_heights(terrain, nominal, active_top_m=ACTIVE_TOP_M)
    active_top, netcdf_top, rejected = resolve_active_top_m([0.0, 10.0, 20.0], "km", [18.0], "km")

    assert terrain[0, 1] == pytest.approx(400.0)
    assert np.all(np.diff(physical, axis=0) > 0.0)
    assert active_top == 20_000.0
    assert netcdf_top == 18_000.0
    assert rejected is True


def test_lower_boundary_residual_collocates_staggered_velocity() -> None:
    x_m = np.array([-1_000.0, 0.0, 1_000.0, 2_000.0])
    y_m = np.array([0.0])
    terrain = analytic_itern1_terrain(x_m)[None, :]
    u_faces = np.full((1, x_m.size + 1), 10.0)
    v_faces = np.zeros((y_m.size + 1, x_m.size))
    slope = np.gradient(terrain, x_m, axis=-1, edge_order=2)
    w = 10.0 * slope

    metrics = lower_boundary_tangency_metrics(
        x_m=x_m,
        y_m=y_m,
        zs_m=terrain,
        u_bottom=u_faces,
        v_bottom=v_faces,
        w_bottom=w,
    )

    assert metrics["residual_rms_m_s"] == pytest.approx(0.0, abs=1.0e-12)
    assert metrics["predicted_observed_correlation"] == pytest.approx(1.0)


def test_central_boundary_metrics_separate_rayleigh_and_lateral_zones() -> None:
    x_m = np.linspace(-10_000.0, 10_000.0, 10)
    z_m = np.array([1_000.0, 15_000.0])[:, None, None]
    heights = np.broadcast_to(z_m, (2, 1, 10))
    values = np.ones_like(heights)
    values[0, :, :2] = 3.0
    values[0, :, -2:] = 3.0
    values[1] = 2.0

    metrics = central_boundary_metrics(values, x_m, heights)

    assert metrics["central_below_rayleigh_rms"] == pytest.approx(1.0)
    assert metrics["boundary_below_rayleigh_rms"] == pytest.approx(3.0)
    assert metrics["rayleigh_layer_rms"] == pytest.approx(2.0)


def test_evaluator_records_native_inventory_coordinates_and_serializable_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    provenance = fake_provenance(tmp_path)
    monkeypatch.setattr(mountain_wave_case, "collect_cm1_provenance", lambda _settings: provenance)
    monkeypatch.setattr(
        mountain_wave_case, "verified_clean_git_commit", lambda: "implementation-commit"
    )
    monkeypatch.setattr(mountain_wave_case, "active_cm1_processes", lambda: [])
    package = generate_mountain_wave_package(settings=settings, run_id="synthetic-evaluation")
    output_paths = _write_synthetic_native_outputs(package.package_dir)
    _mark_package_completed(package, output_paths)

    evidence = evaluate_mountain_wave_run(settings=settings, package=package)
    serialized = json.loads(evidence.to_json_text())

    assert evidence.output_inventory["actual_model_output_count"] == 11
    assert evidence.output_inventory["actual_times_seconds"] == list(EXPECTED_OUTPUT_TIMES_SECONDS)
    assert evidence.output_inventory["variable_inventory"]["u"]["staggering"] == ("u_staggered_x")
    assert evidence.output_inventory["variable_inventory"]["w"]["staggering"] == ("w_staggered_z")
    assert evidence.terrain_and_coordinates["inert_netcdf_ztop_rejected"] is True
    assert evidence.terrain_and_coordinates["active_top_from_final_nominal_zf_m"] == 20_000.0
    assert evidence.lower_boundary["maximum_abs_residual_m_s"] == pytest.approx(0.0, abs=1.0e-12)
    assert evidence.runtime_integrity["normal_termination_marker_present"] is True
    assert evidence.runtime_integrity["stats_evidence"]["status"] == ("stats_netcdf_inspected")
    assert "cflmax" in evidence.runtime_integrity["stats_evidence"]["selected_fields"]
    assert serialized["case_id"] == mountain_wave_case.CASE_ID
    assert serialized["implementation_commit"] == "implementation-commit"


def _write_synthetic_native_outputs(package_dir: Path) -> list[Path]:
    xh_m = np.array([-900.0, 100.0, 1_100.0, 2_100.0])
    xf_m = np.array([-1_400.0, -400.0, 600.0, 1_600.0, 2_600.0])
    yh_m = np.array([0.0])
    yf_m = np.array([-100.0, 100.0])
    zh_m = np.array([1_000.0, 10_000.0])
    zf_m = np.array([0.0, 10_000.0, 20_000.0])
    terrain = analytic_itern1_terrain(xh_m)[None, :]
    zh_physical = reconstruct_physical_heights(terrain, zh_m, active_top_m=ACTIVE_TOP_M)
    zf_physical = reconstruct_physical_heights(terrain, zf_m, active_top_m=ACTIVE_TOP_M)
    base_theta = 288.0 * np.exp(1.0e-4 * zh_physical / 9.81)
    pressure = 100_000.0 * np.exp(-zh_physical / 8_000.0)
    slope = np.gradient(terrain, xh_m, axis=-1, edge_order=2)
    outputs: list[Path] = []

    for number, time_seconds in enumerate(EXPECTED_OUTPUT_TIMES_SECONDS, start=1):
        phase = time_seconds / EXPECTED_OUTPUT_TIMES_SECONDS[-1]
        th = base_theta + phase * np.sin(xh_m[None, None, :] / 1_000.0) * 0.5
        u = np.full((2, 1, 5), 10.0)
        v = np.zeros((2, 2, 4))
        w = np.zeros((3, 1, 4))
        w[0, :, :] = 10.0 * slope
        w[1, 0, :] = phase * np.sin(xh_m / 800.0)
        w[2, 0, :] = phase * np.cos(xh_m / 1_200.0) * 0.1
        dataset = xr.Dataset(
            data_vars={
                "ztop": (("one",), np.array([18.0]), {"units": "km"}),
                "zs": (("time", "yh", "xh"), terrain[None, :, :], {"units": "m"}),
                "zhval": (
                    ("time", "zh", "yh", "xh"),
                    zh_physical[None, :, :, :],
                    {"units": "m"},
                ),
                "th": (
                    ("time", "zh", "yh", "xh"),
                    th[None, :, :, :],
                    {"units": "K"},
                ),
                "prs": (
                    ("time", "zh", "yh", "xh"),
                    pressure[None, :, :, :],
                    {"units": "Pa"},
                ),
                "u": (
                    ("time", "zh", "yh", "xf"),
                    u[None, :, :, :],
                    {"units": "m/s"},
                ),
                "v": (
                    ("time", "zh", "yf", "xh"),
                    v[None, :, :, :],
                    {"units": "m/s"},
                ),
                "w": (
                    ("time", "zf", "yh", "xh"),
                    w[None, :, :, :],
                    {"units": "m/s"},
                ),
            },
            coords={
                "one": [0],
                "time": ("time", [float(time_seconds)], {"units": "seconds"}),
                "xh": ("xh", xh_m / 1_000.0, {"units": "km"}),
                "xf": ("xf", xf_m / 1_000.0, {"units": "km"}),
                "yh": ("yh", yh_m / 1_000.0, {"units": "km"}),
                "yf": ("yf", yf_m / 1_000.0, {"units": "km"}),
                "zh": ("zh", zh_m / 1_000.0, {"units": "km"}),
                "zf": ("zf", zf_m / 1_000.0, {"units": "km"}),
            },
            attrs={"CM1 version": "cm1r21.1", "imoist": 0, "terrain_flag": 1},
        )
        path = package_dir / f"cm1out_{number:06d}.nc"
        dataset.to_netcdf(path)
        outputs.append(path)

    # Keep this assignment live so the test explicitly verifies the full-level construction.
    np.testing.assert_allclose(zf_physical[0], terrain)
    xr.Dataset(
        data_vars={
            "cflmax": ("time", np.linspace(0.1, 0.5, len(EXPECTED_OUTPUT_TIMES_SECONDS))),
            "tmass": ("time", np.linspace(1.0, 1.001, len(EXPECTED_OUTPUT_TIMES_SECONDS))),
        },
        coords={
            "time": (
                "time",
                np.asarray(EXPECTED_OUTPUT_TIMES_SECONDS, dtype=float),
                {"units": "seconds"},
            )
        },
    ).to_netcdf(package_dir / "cm1out_stats.nc")
    return outputs


def _mark_package_completed(
    package: MountainWavePackageResult,
    output_paths: list[Path],
) -> None:
    logs = package.package_dir / "logs"
    logs.mkdir()
    stdout = logs / "stdout.log"
    stderr = logs / "stderr.log"
    stdout.write_text("Program terminated normally\n")
    stderr.write_text("")
    started = datetime.now(UTC)
    manifest = load_run_manifest(package.manifest_path)
    completed = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
            "execution": ExecutionMetadata(
                command=["configured/cm1.exe"],
                started_at=started,
                finished_at=started + timedelta(seconds=3),
                exit_code=0,
                stdout_log=str(stdout),
                stderr_log=str(stderr),
            ),
            "outputs": OutputMetadata(netcdf_paths=[str(path) for path in output_paths]),
            "updated_at": started + timedelta(seconds=3),
        }
    )
    write_run_manifest(package.manifest_path, completed)

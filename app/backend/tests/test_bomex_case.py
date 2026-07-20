import json
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import bomex_case
from cloud_chamber.bomex_case import (
    REQUIRED_OUTPUT_SWITCHES,
    BomexVariant,
    CM1Provenance,
    generate_bomex_package,
    normalized_science_namelist,
    render_bomex_namelist,
    render_profile_audit,
    sha256_text,
)
from cloud_chamber.run_manifest import load_run_manifest
from cloud_chamber.settings import CloudChamberSettings


def reference_namelist_text() -> str:
    names = sorted(
        {
            *bomex_case._COMMON_NAMELIST_OVERRIDES,
            *REQUIRED_OUTPUT_SWITCHES,
            "timax",
        }
    )
    return "&bomex_test\n" + "".join(f"  {name} = -999,\n" for name in names) + "/\n"


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
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


def fake_provenance(tmp_path: Path) -> CM1Provenance:
    reference_path = tmp_path / "cm1r21.1" / "run" / "namelist.input.reference"
    reference_path.write_text(reference_namelist_text())
    return CM1Provenance(
        release="21.1",
        official_tag_commit=bomex_case.CM1_TAG_COMMIT,
        official_source_tag=bomex_case.CM1_SOURCE_TAG,
        source_tree_path=str(tmp_path / "cm1r21.1"),
        run_directory_path=str(tmp_path / "cm1r21.1" / "run"),
        executable_path=str(tmp_path / "cm1r21.1" / "run" / "cm1.exe"),
        executable_sha256="executable-hash",
        readme_namelist_path=str(tmp_path / "cm1r21.1" / "README.namelist"),
        readme_namelist_sha256="readme-hash",
        source_manifest_method="test manifest",
        source_manifest_sha256="source-hash",
        critical_source_sha256={"src/base.F": "base-hash"},
        bundled_bomex_namelist_path=str(reference_path),
        bundled_bomex_namelist_sha256="reference-hash",
        bundled_bomex_readme_path=str(tmp_path / "cm1r21.1" / "README"),
        bundled_bomex_readme_sha256="case-readme-hash",
    )


def assignment(text: str, name: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith(f"{name} ="):
            return line.split("=", 1)[1].split(",", 1)[0].strip()
    raise AssertionError(f"missing assignment: {name}")


def test_rendered_namelist_uses_exact_bomex_science_and_output_settings() -> None:
    rendered = render_bomex_namelist(reference_namelist_text(), BomexVariant.FULL)

    assert assignment(rendered, "timax") == "21600.0"
    assert assignment(rendered, "testcase") == "3"
    assert assignment(rendered, "isnd") == "19"
    assert assignment(rendered, "iwnd") == "9"
    assert assignment(rendered, "iinit") == "0"
    assert assignment(rendered, "irandp") == "1"
    assert assignment(rendered, "ptype") == "6"
    assert assignment(rendered, "v_t") == "0.0"
    assert assignment(rendered, "tapfrq") == "300.0"
    assert assignment(rendered, "diagfrq") == "60.0"
    assert assignment(rendered, "output_dbz") == "0"
    for name, value in REQUIRED_OUTPUT_SWITCHES.items():
        assert assignment(rendered, name) == value


def test_smoke_and_full_namelists_differ_only_in_duration() -> None:
    reference = reference_namelist_text()
    smoke = render_bomex_namelist(reference, BomexVariant.SMOKE)
    full = render_bomex_namelist(reference, BomexVariant.FULL)

    assert smoke != full
    assert assignment(smoke, "timax") == "600.0"
    assert normalized_science_namelist(smoke) == normalized_science_namelist(full)
    assert sha256_text(normalized_science_namelist(smoke)) == sha256_text(
        normalized_science_namelist(full)
    )


def test_profile_audit_is_deterministic_and_contains_canonical_knots() -> None:
    first = render_profile_audit()
    second = render_profile_audit()

    assert first == second
    assert "     0.0000   298.7000   17.000000    -8.7500" in first
    assert "   520.0000   298.7000   16.300000" in first
    assert "  1480.0000   302.4000   10.700000" in first
    assert "  3000.0000   311.8500    3.000000    -4.6100" in first


def test_package_records_hashes_provenance_and_no_recipe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = fake_settings(tmp_path)
    provenance = fake_provenance(tmp_path)
    monkeypatch.setattr(bomex_case, "collect_cm1_provenance", lambda _settings: provenance)
    monkeypatch.setattr(bomex_case, "verified_clean_git_commit", lambda: "commit-test")

    smoke = generate_bomex_package(
        settings=settings,
        variant=BomexVariant.SMOKE,
        run_id="bomex-smoke-test",
    )
    full = generate_bomex_package(
        settings=settings,
        variant=BomexVariant.FULL,
        run_id="bomex-full-test",
    )

    smoke_manifest = load_run_manifest(smoke.manifest_path)
    full_manifest = load_run_manifest(full.manifest_path)
    smoke_config = smoke_manifest.run_configuration
    full_config = full_manifest.run_configuration
    assert smoke_manifest.run_recipe is None
    assert smoke_manifest.app.commit == "commit-test"
    assert smoke_manifest.observed_sounding is None
    assert smoke_manifest.trigger_type is None
    assert smoke_config["case_id"] == bomex_case.CASE_ID
    assert smoke_config["mapping_version"] == bomex_case.MAPPING_VERSION
    assert smoke_config["science_settings_sha256"] == full_config["science_settings_sha256"]
    assert smoke_config["duration_seconds"] == 600
    assert full_config["duration_seconds"] == 21_600
    assert smoke_config["generated_forcing_input_sha256"] == {}
    generated_hashes = smoke_config["generated_input_sha256"]
    assert isinstance(generated_hashes, dict)
    assert set(generated_hashes) == {
        "case_manifest.json",
        "input_sounding",
        "namelist.input",
        "runtime_file_checklist.json",
    }
    assert smoke_config["cm1_provenance"] == provenance.model_dump(mode="json")
    case_manifest = json.loads(smoke.case_manifest_path.read_text())
    assert case_manifest["authority_state"] == "stage4_candidate_evidence_not_product_recipe"
    assert case_manifest["cm1_translation"]["ptype"] == 6
    assert case_manifest["cm1_translation"]["v_t_m_s"] == 0.0
    assert case_manifest["unsupported_components"] == []


def test_model_frame_evidence_uses_cwp_and_converts_km_heights(tmp_path: Path) -> None:
    path = tmp_path / "cm1out_000001.nc"
    liquid = np.zeros((1, 2, 2, 2), dtype=float)
    liquid[0, 0, 0, 0] = 2.0e-6
    xr.Dataset(
        data_vars={
            "ql": (("time", "zh", "yh", "xh"), liquid),
            "cwp": (("time", "yh", "xh"), np.full((1, 2, 2), 0.25)),
            "lwp": (("time", "yh", "xh"), np.zeros((1, 2, 2))),
        },
        coords={
            "time": ("time", [300.0]),
            "zh": ("zh", [0.02, 0.06], {"units": "km"}),
            "yh": ("yh", [0.0, 0.1]),
            "xh": ("xh", [0.0, 0.1]),
        },
    ).to_netcdf(path)

    metrics, _cloud_profiles, _non_finite, _profiles, heights = bomex_case._model_frame_evidence(
        [path]
    )

    assert metrics[0]["mean_lwp"] == pytest.approx(0.25)
    assert metrics[0]["max_lwp"] == pytest.approx(0.25)
    assert heights == pytest.approx([20.0, 60.0])


def test_package_refuses_dirty_worktree_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = fake_settings(tmp_path)

    def dirty_git_output(*args: str) -> str:
        if args == ("rev-parse", "HEAD"):
            return "clean-commit"
        if args == ("status", "--porcelain=v1", "--untracked-files=all"):
            return " M app/backend/cloud_chamber/bomex_case.py"
        raise AssertionError(args)

    monkeypatch.setattr(bomex_case, "_git_output", dirty_git_output)

    with pytest.raises(bomex_case.BomexCaseError, match="requires a clean Git worktree"):
        generate_bomex_package(
            settings=settings,
            variant=BomexVariant.SMOKE,
            run_id="dirty-bomex-package",
        )

    assert not (settings.runtime_home / "runs" / "dirty-bomex-package").exists()


def test_final_three_hour_cloud_fraction_peak_uses_time_mean_profile(tmp_path: Path) -> None:
    first_path = tmp_path / "cm1out_000001.nc"
    second_path = tmp_path / "cm1out_000002.nc"
    first_liquid = np.zeros((1, 2, 2, 2), dtype=float)
    first_liquid[0, 0, :, :] = 2.0e-6
    second_liquid = np.zeros((1, 2, 2, 2), dtype=float)
    second_liquid[0, 1, 0, :] = 2.0e-6

    for path, time_seconds, liquid in (
        (first_path, 10_800.0, first_liquid),
        (second_path, 11_100.0, second_liquid),
    ):
        xr.Dataset(
            data_vars={"ql": (("time", "zh", "yh", "xh"), liquid)},
            coords={
                "time": ("time", [time_seconds]),
                "zh": ("zh", [20.0, 60.0], {"units": "m"}),
                "yh": ("yh", [0.0, 100.0]),
                "xh": ("xh", [0.0, 100.0]),
            },
        ).to_netcdf(path)

    metrics, cloud_profiles, _non_finite, _profiles, heights = bomex_case._model_frame_evidence(
        [first_path, second_path]
    )
    peak_percent, peak_height_m = bomex_case._final_three_hour_cloud_fraction_peak(
        cloud_profiles, heights
    )

    assert [metric["peak_cloud_fraction_percent"] for metric in metrics] == pytest.approx(
        [100.0, 50.0]
    )
    assert peak_percent == pytest.approx(50.0)
    assert peak_height_m == pytest.approx(20.0)

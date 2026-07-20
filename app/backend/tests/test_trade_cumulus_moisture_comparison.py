from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

import cloud_chamber.trade_cumulus_moisture_comparison as comparison
from cloud_chamber import bomex_case
from cloud_chamber.bomex_case import CM1Provenance
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.run_manifest import load_run_manifest
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.trade_cumulus_moisture_comparison import (
    COMPARISON_GROUP_ID,
    OUTPUT_CADENCE_SECONDS,
    PERCENT_DELTA_MINIMUM_DENOMINATOR,
    PackageComparisonProof,
    RunGateEvidence,
    ScalarRunMetric,
    TimedValue,
    TradeCumulusMatchedPackage,
    TradeCumulusMoistureComparisonError,
    TradeCumulusMoistureState,
    TradeCumulusRunEvidence,
    TradeCumulusRunLength,
    VerticalProfile,
    compare_matched_packages,
    compare_stage4_baseline,
    generate_trade_cumulus_matched_package,
    namelist_difference_names,
    normalized_trade_cumulus_fixed_assumptions_namelist,
    normalized_trade_cumulus_science_namelist,
    pair_exact_time_series,
    pair_scalar_metric,
    render_trade_cumulus_matched_namelist,
    thickness_weighted_layer_mean,
    verify_smoke_full_equivalence,
)
from cloud_chamber.trade_cumulus_updraft_lens import rounded_percentile_reference


def _reference_namelist_text() -> str:
    names = sorted(
        {
            *bomex_case._COMMON_NAMELIST_OVERRIDES,
            *bomex_case.REQUIRED_OUTPUT_SWITCHES,
            "cnst_lhflx",
            "timax",
        }
    )
    return "&bomex_test\n" + "".join(f"  {name} = -999,\n" for name in names) + "/\n"


def _assignment(text: str, name: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith(f"{name} ="):
            return line.split("=", 1)[1].split(",", 1)[0].strip()
    raise AssertionError(f"missing assignment: {name}")


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


def _provenance(tmp_path: Path) -> CM1Provenance:
    reference_path = tmp_path / "cm1r21.1" / "run" / "namelist.input.reference"
    reference_path.write_text(_reference_namelist_text())
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


def _install_package_mocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CloudChamberSettings:
    settings = _settings(tmp_path)
    provenance = _provenance(tmp_path)
    monkeypatch.setattr(bomex_case, "collect_cm1_provenance", lambda _settings: provenance)
    monkeypatch.setattr(bomex_case, "verified_clean_git_commit", lambda: "commit-test")
    monkeypatch.setattr(comparison, "verified_clean_git_commit", lambda: "commit-test")
    return settings


def test_exact_states_lengths_cadences_and_counts() -> None:
    assert TradeCumulusMoistureState.BASELINE.surface_moisture_flux_g_g_m_s == 5.2e-5
    assert TradeCumulusMoistureState.MORE_MOISTURE.surface_moisture_flux_g_g_m_s == 7.8e-5
    assert OUTPUT_CADENCE_SECONDS == 120
    assert TradeCumulusRunLength.SMOKE.duration_seconds == 600
    assert TradeCumulusRunLength.SMOKE.expected_model_output_count == 6
    assert TradeCumulusRunLength.SMOKE.expected_diagnostic_output_count == 11
    assert TradeCumulusRunLength.FULL.duration_seconds == 21_600
    assert TradeCumulusRunLength.FULL.expected_model_output_count == 181
    assert TradeCumulusRunLength.FULL.expected_diagnostic_output_count == 361


def test_rendered_pair_diff_and_normalized_hash_contract() -> None:
    reference = _reference_namelist_text()
    baseline_smoke = render_trade_cumulus_matched_namelist(
        reference, TradeCumulusMoistureState.BASELINE, TradeCumulusRunLength.SMOKE
    )
    baseline_full = render_trade_cumulus_matched_namelist(
        reference, TradeCumulusMoistureState.BASELINE, TradeCumulusRunLength.FULL
    )
    variant_full = render_trade_cumulus_matched_namelist(
        reference, TradeCumulusMoistureState.MORE_MOISTURE, TradeCumulusRunLength.FULL
    )

    assert _assignment(baseline_smoke, "timax") == "600.0"
    assert _assignment(baseline_full, "tapfrq") == "120.0"
    assert _assignment(baseline_full, "diagfrq") == "60.0"
    assert _assignment(baseline_full, "cnst_lhflx") == "5.2e-5"
    assert _assignment(variant_full, "cnst_lhflx") == "7.8e-5"
    assert namelist_difference_names(baseline_smoke, baseline_full) == ["timax"]
    assert namelist_difference_names(baseline_full, variant_full) == ["cnst_lhflx"]
    assert normalized_trade_cumulus_science_namelist(baseline_smoke) == (
        normalized_trade_cumulus_science_namelist(baseline_full)
    )
    assert normalized_trade_cumulus_science_namelist(baseline_full) != (
        normalized_trade_cumulus_science_namelist(variant_full)
    )
    assert normalized_trade_cumulus_fixed_assumptions_namelist(baseline_full) == (
        normalized_trade_cumulus_fixed_assumptions_namelist(variant_full)
    )


def test_packages_record_exact_identifiers_hashes_and_null_recipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _install_package_mocks(tmp_path, monkeypatch)
    packages: dict[tuple[TradeCumulusMoistureState, TradeCumulusRunLength], Any] = {}
    for state in TradeCumulusMoistureState:
        for run_length in TradeCumulusRunLength:
            packages[(state, run_length)] = generate_trade_cumulus_matched_package(
                settings=settings,
                control_state=state,
                run_length=run_length,
                run_id=f"{run_length.value}-{state.value}",
                app_commit="commit-test",
            )

    baseline_smoke = packages[(TradeCumulusMoistureState.BASELINE, TradeCumulusRunLength.SMOKE)]
    variant_smoke = packages[(TradeCumulusMoistureState.MORE_MOISTURE, TradeCumulusRunLength.SMOKE)]
    baseline_full = packages[(TradeCumulusMoistureState.BASELINE, TradeCumulusRunLength.FULL)]
    variant_full = packages[(TradeCumulusMoistureState.MORE_MOISTURE, TradeCumulusRunLength.FULL)]
    proof = compare_matched_packages(baseline_smoke, variant_smoke)
    assert proof.valid is True
    compare_matched_packages(baseline_full, variant_full)
    verify_smoke_full_equivalence(baseline_smoke, baseline_full)
    verify_smoke_full_equivalence(variant_smoke, variant_full)
    assert baseline_full.fixed_assumptions_sha256 == variant_full.fixed_assumptions_sha256
    assert baseline_full.science_settings_sha256 != variant_full.science_settings_sha256

    manifest = load_run_manifest(variant_full.manifest_path)
    assert manifest.scenario.id == bomex_case.CASE_ID
    assert manifest.run_recipe is None
    assert manifest.app.commit == "commit-test"
    assert manifest.run_configuration["product_slice_id"] == "trade_cumulus_v1"
    assert manifest.run_configuration["comparison_group_id"] == COMPARISON_GROUP_ID
    assert manifest.run_configuration["recipe_candidate_id"] == "canonical_bomex_baseline"
    assert manifest.run_configuration["control_id"] == "surface_moisture_supply"
    assert manifest.run_configuration["control_state"] == "more_moisture"
    assert manifest.run_configuration["expected_model_output_count"] == 181
    assert manifest.run_configuration["expected_diagnostic_output_count"] == 361
    changed = manifest.run_configuration["changed_assumptions"]
    assert set(changed) == {
        "control_id",
        "control_state",
        "surface_moisture_flux_g_g_m_s",
    }


def test_package_refuses_dirty_or_mismatched_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)

    def dirty() -> str:
        raise bomex_case.BomexCaseError("requires a clean Git worktree")

    monkeypatch.setattr(comparison, "verified_clean_git_commit", dirty)
    with pytest.raises(TradeCumulusMoistureComparisonError, match="clean Git worktree"):
        generate_trade_cumulus_matched_package(
            settings=settings,
            control_state=TradeCumulusMoistureState.BASELINE,
            run_length=TradeCumulusRunLength.SMOKE,
            run_id="dirty",
        )
    assert not (settings.runtime_home / "runs" / "dirty").exists()


def test_thickness_weighted_mean_is_not_arithmetic_mean() -> None:
    profile = np.asarray([0.0, 10.0, 20.0])
    heights = np.asarray([50.0, 200.0, 800.0])
    weighted = thickness_weighted_layer_mean(profile, heights)
    assert weighted == pytest.approx(13.75)
    assert weighted != pytest.approx(float(np.mean(profile)))


def test_time_mean_profile_peak_is_not_instantaneous_peak() -> None:
    profile = comparison._mean_optional_profiles([[100.0, 0.0], [0.0, 80.0], [0.0, 80.0]])
    peak, height = comparison._profile_peak(profile, [100.0, 500.0])
    assert profile == pytest.approx([100.0 / 3.0, 160.0 / 3.0])
    assert (peak, height) == pytest.approx((160.0 / 3.0, 500.0))


def test_cloud_conditioned_w_excludes_clear_raw_extrema() -> None:
    w = np.asarray([[[1.0, -20.0], [3.0, 40.0]]])
    cloud = np.asarray([[[True, False], [True, False]]])
    assert comparison._cloud_conditioned_profile(w, cloud) == pytest.approx([2.0])
    assert float(np.max(w)) == 40.0


def test_exact_time_pairing_rejects_interpolation() -> None:
    baseline = [TimedValue(time_seconds=0.0, value=1.0), TimedValue(time_seconds=120.0, value=2.0)]
    variant = [TimedValue(time_seconds=0.0, value=2.0), TimedValue(time_seconds=180.0, value=4.0)]
    with pytest.raises(TradeCumulusMoistureComparisonError, match="interpolation is forbidden"):
        pair_exact_time_series(baseline, variant)


def test_percent_delta_is_unavailable_for_zero_and_near_zero_baselines() -> None:
    for value in (0.0, PERCENT_DELTA_MINIMUM_DENOMINATOR):
        paired = pair_scalar_metric(
            ScalarRunMetric(value=value, units="m/s", method="same", window="same"),
            ScalarRunMetric(value=1.0, units="m/s", method="same", window="same"),
        )
        assert paired.percent_delta is None
        assert paired.percent_delta_unavailable_reason == "baseline_denominator_zero_or_near_zero"


def _stage4_dataset(delta: float = 0.0) -> xr.Dataset:
    times = np.arange(0.0, 21_601.0, 600.0)
    shape = (times.size, 2, 2, 2)
    ql = np.full(shape, 2e-6)
    qv = np.full(shape, 0.01)
    qv[1, 0, 0, 0] += delta
    th = np.full(shape, 300.0)
    w = np.ones((times.size, 3, 2, 2))
    cwp = np.full((times.size, 2, 2), 0.1)
    return xr.Dataset(
        {
            "ql": (("time", "zh", "yh", "xh"), ql),
            "qv": (("time", "zh", "yh", "xh"), qv),
            "th": (("time", "zh", "yh", "xh"), th),
            "w": (("time", "zf", "yh", "xh"), w),
            "cwp": (("time", "yh", "xh"), cwp),
        },
        coords={
            "time": ("time", times, {"units": "s"}),
            "zh": ("zh", [0.1, 0.3], {"units": "km"}),
            "zf": ("zf", [0.0, 0.2, 0.4], {"units": "km"}),
            "yh": ("yh", [0.0, 0.1], {"units": "km"}),
            "xh": ("xh", [0.0, 0.1], {"units": "km"}),
        },
    )


def _result(path: Path, result_id: str) -> ResultMetadata:
    now = datetime(2026, 7, 20, tzinfo=UTC)
    return ResultMetadata(
        result_id=result_id,
        run_id=result_id.removeprefix("result-"),
        scenario_id=bomex_case.CASE_ID,
        physical_question="comparison",
        controls={},
        run_configuration={"case_id": bomex_case.CASE_ID},
        source_lifecycle_state="completed",
        source_product_state="completed_cm1_result",
        source_model="CM1",
        model_output_paths=[str(path)],
        model_output_file_count=37,
        time_steps=37,
        first_output_time_seconds=0.0,
        last_output_time_seconds=21_600.0,
        created_at=now,
        updated_at=now,
    )


def test_stage4_consistency_checker_passes_and_reports_maxima(tmp_path: Path) -> None:
    preserved_path = tmp_path / "preserved.nc"
    candidate_path = tmp_path / "candidate.nc"
    _stage4_dataset().to_netcdf(preserved_path)
    _stage4_dataset(delta=1e-12).to_netcdf(candidate_path)
    evidence = compare_stage4_baseline(
        _result(preserved_path, "result-stage4"),
        _result(candidate_path, "result-new"),
    )
    assert evidence.passed is True
    assert evidence.first_failure is None
    assert evidence.field_differences[1].maximum_absolute_difference == pytest.approx(1e-12)


def test_stage4_consistency_checker_records_first_failure(tmp_path: Path) -> None:
    preserved_path = tmp_path / "preserved.nc"
    candidate_path = tmp_path / "candidate.nc"
    _stage4_dataset().to_netcdf(preserved_path)
    _stage4_dataset(delta=1e-5).to_netcdf(candidate_path)
    evidence = compare_stage4_baseline(
        _result(preserved_path, "result-stage4"),
        _result(candidate_path, "result-new"),
    )
    assert evidence.passed is False
    assert evidence.first_failure is not None
    assert evidence.first_failure.time_seconds == 600.0
    assert evidence.first_failure.field == "qv"
    assert evidence.first_failure.index == [0, 0, 0]


def test_joint_reference_uses_values_from_either_member() -> None:
    baseline = np.asarray([0.2, 0.3])
    variant = np.asarray([1.01, 1.02])
    joint = rounded_percentile_reference([baseline, variant], 99, 0.5)
    assert joint == 1.1


def _minimal_run_evidence() -> TradeCumulusRunEvidence:
    gate = RunGateEvidence(
        valid=True,
        lifecycle_state="completed",
        product_state="completed_cm1_result",
        exit_code=0,
        normal_completion_reported=True,
        runtime_integrity_state="trusted",
        runtime_integrity_reason="passed",
        runtime_integrity_caveats=[],
        model_output_count=6,
        expected_model_output_count=6,
        diagnostic_output_count=11,
        expected_diagnostic_output_count=11,
        missing_required_fields=[],
        required_field_non_finite_counts={},
        intended_surface_moisture_flux_g_g_m_s=5.2e-5,
        emitted_surface_moisture_flux_min_g_g_m_s=5.2e-5,
        emitted_surface_moisture_flux_max_g_g_m_s=5.2e-5,
    )
    return TradeCumulusRunEvidence(
        control_state="baseline",
        run_length="smoke",
        run_id="run",
        result_id="result-run",
        app_commit="commit",
        surface_moisture_flux_g_g_m_s=5.2e-5,
        duration_seconds=600,
        output_bytes=123,
        gate=gate,
        scalar_metrics={
            "metric": ScalarRunMetric(value=1.0, units="1", method="deterministic", window="all")
        },
        time_series={"series": [TimedValue(time_seconds=0.0, value=1.0)]},
        vertical_profiles={
            "profile": VerticalProfile(
                height_m=[100.0],
                values=[1.0],
                units="1",
                method="deterministic",
                window="all",
            )
        },
        final_domain_mean_profiles={},
        forcing_diagnostics={},
        forcing_and_transport_fields_available=[],
        available_fields=[],
    )


def test_run_evidence_serialization_is_deterministic() -> None:
    evidence = _minimal_run_evidence()
    assert evidence.to_json_text() == evidence.model_copy(deep=True).to_json_text()
    assert evidence.to_json_text().endswith("\n")


def test_package_comparison_proof_forbids_extra_difference(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "namelist.input").write_text("a = 1,\ncnst_lhflx = 5.2e-5,\n")
    (right / "namelist.input").write_text("a = 2,\ncnst_lhflx = 7.8e-5,\n")
    baseline = TradeCumulusMatchedPackage(
        run_id="baseline",
        control_state=TradeCumulusMoistureState.BASELINE,
        run_length=TradeCumulusRunLength.FULL,
        package_dir=left,
        manifest_path=left / "manifest",
        case_manifest_path=left / "case",
        namelist_path=left / "namelist.input",
        science_settings_sha256="baseline-science",
        fixed_assumptions_sha256="fixed",
        app_commit="commit",
    )
    variant = TradeCumulusMatchedPackage(
        run_id="variant",
        control_state=TradeCumulusMoistureState.MORE_MOISTURE,
        run_length=TradeCumulusRunLength.FULL,
        package_dir=right,
        manifest_path=right / "manifest",
        case_manifest_path=right / "case",
        namelist_path=right / "namelist.input",
        science_settings_sha256="variant-science",
        fixed_assumptions_sha256="fixed",
        app_commit="commit",
    )
    with pytest.raises(TradeCumulusMoistureComparisonError, match="proof failed"):
        compare_matched_packages(baseline, variant)


def test_package_proof_model_serializes_stably() -> None:
    proof = PackageComparisonProof(
        run_length="smoke",
        baseline_run_id="baseline",
        more_moisture_run_id="variant",
        differing_namelist_assignments=["cnst_lhflx"],
        fixed_assumptions_sha256="fixed",
        baseline_science_settings_sha256="one",
        more_moisture_science_settings_sha256="two",
        valid=True,
    )
    assert proof.model_dump_json() == proof.model_copy().model_dump_json()

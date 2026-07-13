import json
from pathlib import Path
from typing import Any

import pytest
import xarray as xr

from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.output_products import (
    default_output_product_manifest_path,
    output_product_manifest_from_json,
)
from cloud_chamber.result_ingest import (
    RESULT_METADATA_FILENAME,
    ResultIngestError,
    get_result_metadata,
    ingest_completed_run,
    list_result_metadata,
    result_metadata_from_json,
)
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_TEMPLATE = REPO_ROOT / "scenarios/lower-atmosphere/baseline-shallow-cumulus.json"


def fake_settings(tmp_path: Path) -> CloudChamberSettings:
    runtime_home = tmp_path / "CloudChamber"
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=tmp_path / "cm1r21.1",
        cm1_run_dir=tmp_path / "cm1r21.1" / "run",
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def create_manifest(tmp_path: Path, run_id: str = "run-ingest") -> Path:
    result = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=tmp_path / "CloudChamber",
        run_id=run_id,
    )
    return result.manifest_path


def complete_manifest(
    manifest_path: Path,
    outputs: OutputMetadata,
) -> None:
    manifest = load_run_manifest(manifest_path)
    updated = manifest.model_copy(
        update={
            "lifecycle_state": LifecycleState.COMPLETED,
            "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
            "outputs": outputs,
        }
    )
    write_run_manifest(manifest_path, updated)


def write_tiny_netcdf(
    path: Path,
    *,
    include_qc: bool = True,
    include_w: bool = True,
) -> None:
    data_vars: dict[str, Any] = {}
    if include_qc:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            [[[[0.0, 0.1], [0.2, 0.3]], [[0.4, 0.5], [0.6, 0.7]]]],
            {"units": "kg/kg"},
        )
    if include_w:
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            [[[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]]],
            {"units": "m/s"},
        )
    dataset = xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": [0.0],
            "z": [125.0, 250.0],
            "y": [0.0, 200.0],
            "x": [0.0, 200.0],
        },
    )
    dataset.to_netcdf(path, engine="scipy")


def write_model_netcdf(
    path: Path,
    *,
    times: list[float],
    qc_values: list[float],
    w_values: list[float],
    qr_values: list[float] | None = None,
    rain_values: list[float] | None = None,
    dbz_values: list[float] | None = None,
    hfx_values: list[float] | None = None,
    qfx_values: list[float] | None = None,
    qv_values: list[float] | None = None,
    th_values: list[float] | None = None,
    z_values: list[float] | None = None,
    include_qc: bool = True,
    include_w: bool = True,
) -> None:
    z_values = z_values or [500.0, 1500.0]
    data_vars: dict[str, Any] = {}
    if include_qc:
        data_vars["qc"] = (
            ("time", "z", "y", "x"),
            [
                [[[qc_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for qc_value in qc_values
            ],
            {"units": "kg/kg"},
        )
    if include_w:
        data_vars["w"] = (
            ("time", "z", "y", "x"),
            [
                [[[w_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for w_value in w_values
            ],
            {"units": "m/s"},
        )
    if qr_values is not None:
        data_vars["qr"] = (
            ("time", "z", "y", "x"),
            [
                [[[qr_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for qr_value in qr_values
            ],
            {"units": "kg/kg"},
        )
    if rain_values is not None:
        data_vars["rain"] = (
            ("time", "y", "x"),
            [[[rain_value for _x in range(4)] for _y in range(3)] for rain_value in rain_values],
            {"units": "mm"},
        )
    if dbz_values is not None:
        data_vars["dbz"] = (
            ("time", "z", "y", "x"),
            [
                [[[dbz_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for dbz_value in dbz_values
            ],
            {"units": "dBZ"},
        )
    if hfx_values is not None:
        data_vars["hfx"] = (
            ("time", "y", "x"),
            [[[hfx_value for _x in range(4)] for _y in range(3)] for hfx_value in hfx_values],
            {"units": "K m/s"},
        )
    if qfx_values is not None:
        data_vars["qfx"] = (
            ("time", "y", "x"),
            [[[qfx_value for _x in range(4)] for _y in range(3)] for qfx_value in qfx_values],
            {"units": "kg/m^2/s"},
        )
    if qv_values is not None:
        data_vars["qv"] = (
            ("time", "z", "y", "x"),
            [
                [[[qv_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for qv_value in qv_values
            ],
            {"units": "kg/kg"},
        )
    if th_values is not None:
        data_vars["th"] = (
            ("time", "z", "y", "x"),
            [
                [[[th_value for _x in range(4)] for _y in range(3)] for _z in z_values]
                for th_value in th_values
            ],
            {"units": "K"},
        )
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": times,
            "z": z_values,
            "y": [0.0, 200.0, 400.0],
            "x": [0.0, 200.0, 400.0, 600.0],
        },
    ).to_netcdf(path, engine="scipy")


def write_stats_netcdf(path: Path) -> None:
    xr.Dataset(
        data_vars={"mass": (("time",), [1.0], {"units": "kg"})},
        coords={"time": [0.0]},
    ).to_netcdf(path, engine="scipy")


def test_ingests_valid_tiny_netcdf_metadata(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    raw_path = run_dir / "cm1out_000001_s.dat"
    write_tiny_netcdf(netcdf_path)
    raw_path.write_text("raw CM1 artifact")
    complete_manifest(
        manifest_path,
        OutputMetadata(
            raw_cm1_artifacts=[str(raw_path)],
            netcdf_paths=[str(netcdf_path)],
            runtime_warnings=[
                "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG"
            ],
        ),
    )

    result = ingest_completed_run(manifest_path)

    assert result.result_id == "result-run-ingest"
    assert result.run_id == "run-ingest"
    assert result.scenario_id == "baseline-shallow-cumulus"
    assert result.physical_question
    assert result.run_configuration["duration"] == "short_6h"
    assert result.run_configuration["cm1_values"]["expected_output_frames"] == 25
    assert result.pre_run_validation_report is not None
    assert result.pre_run_validation_report["run_shape_validation"]["estimated_frames"] == 25
    assert result.source_lifecycle_state == "completed"
    assert result.source_product_state == "completed_cm1_result"
    assert result.source_model == "CM1"
    assert result.netcdf_paths == [str(netcdf_path)]
    assert result.raw_cm1_artifacts == [str(raw_path)]
    product_manifest_path = default_output_product_manifest_path(run_dir)
    assert result.processed_artifacts == [str(product_manifest_path)]
    assert result.visualization_ready_artifacts == []
    assert result.dimensions == {"time": 1, "z": 2, "y": 2, "x": 2}
    assert result.coordinates == ["time", "z", "y", "x"]
    assert result.variables == ["qc", "w"]
    assert result.recipe_id == "generated_reference_lower_atmosphere_v1"
    assert result.required_output_fields == ["qv", "qc", "w", "qr", "rain", "dbz", "hfx", "qfx"]
    assert result.missing_required_output_fields == ["qv", "qr", "rain", "dbz", "hfx", "qfx"]
    assert result.time_coordinate == "time"
    assert result.time_steps == 1
    assert result.grid_shape == [2, 2, 2]
    assert [(field.name, field.units) for field in result.fields_detected] == [
        ("qc", "kg/kg"),
        ("w", "m/s"),
    ]
    assert result.diagnostics_summary == (
        "no cloud formed; rain water aloft unavailable; surface rain unavailable; "
        "reflectivity unavailable"
    )
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is False
    assert result.diagnostics.rain.field_absent is True
    assert result.diagnostics.surface_fluxes.hfx.available is False
    assert result.diagnostics.surface_fluxes.hfx.field_absent is True
    assert result.diagnostics.surface_fluxes.qfx.available is False
    assert result.diagnostics.surface_fluxes.qfx.field_absent is True
    assert result.diagnostics.field_quality_assessed is True
    assert result.diagnostics.field_quality["qc"].quality_state == "trusted"
    assert result.diagnostics.field_quality["w"].quality_state == "trusted"
    assert result.diagnostics.field_quality["qr"].quality_state == "unavailable"
    assert result.diagnostics.field_quality["hfx"].quality_state == "unavailable"
    assert result.diagnostics.field_quality["qfx"].quality_state == "unavailable"
    assert result.process_diagnostics is not None
    assert (
        result.process_diagnostics.interpretation_support.thermal_fate_label
        == "Thermal without cloud"
    )
    assert result.process_diagnostics.interpretation_support.confidence == "supported"
    assert result.process_diagnostics.deep_breakthrough.status == "unsupported_missing_fields"
    assert result.warnings == [
        "CM1 stderr reported floating-point exception flags: IEEE_INVALID_FLAG",
        "Recipe required output fields missing from NetCDF metadata: qv, qr, rain, dbz, hfx, qfx",
    ]
    assert (run_dir / RESULT_METADATA_FILENAME).exists()
    assert product_manifest_path.exists()
    product_manifest = output_product_manifest_from_json(product_manifest_path.read_text())
    assert product_manifest.result_id == result.result_id
    assert product_manifest.run_id == result.run_id
    assert product_manifest.source_result_metadata_path == str(run_dir / RESULT_METADATA_FILENAME)
    assert product_manifest.source_run_manifest_path == str(manifest_path)
    assert [entry.time_index for entry in product_manifest.time_index] == [0]
    assert product_manifest.time_index[0].source_file == str(netcdf_path)
    assert product_manifest.time_index[0].local_time_index == 0


def test_result_metadata_serializes_and_lists_from_runtime_home(tmp_path: Path) -> None:
    settings = fake_settings(tmp_path)
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    result = ingest_completed_run(manifest_path)
    round_tripped = result_metadata_from_json(result.to_json_text())
    listed = list_result_metadata(settings)
    found = get_result_metadata(settings, result.result_id)

    assert round_tripped == result
    assert listed == [result]
    assert found == result


def test_ingests_multifile_model_output_sequence_and_excludes_stats(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-multifile")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    stats = run_dir / "cm1out_stats.nc"
    write_model_netcdf(
        first,
        times=[300.0],
        qc_values=[0.0],
        w_values=[-5.0],
        hfx_values=[1.0],
        qfx_values=[1.0e-5],
        qv_values=[0.010],
        th_values=[300.0],
    )
    write_model_netcdf(
        second,
        times=[3900.0],
        qc_values=[2e-6],
        w_values=[7.0],
        hfx_values=[3.0],
        qfx_values=[3.0e-5],
        qv_values=[0.016],
        th_values=[304.0],
    )
    write_stats_netcdf(stats)
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(second), str(stats), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_paths == [str(first), str(second)]
    assert result.stats_netcdf_paths == [str(stats)]
    assert result.model_output_file_count == 2
    assert result.time_steps == 2
    assert result.first_output_time_seconds == 300.0
    assert result.last_output_time_seconds == 3900.0
    assert result.time_coordinate_source == "netcdf_time_coordinate"
    assert result.time_coordinate_fallback_used is False
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.cloud.first_cloud_time_seconds == 3900.0
    assert len(result.diagnostics.cloud.qc_max_time_series) == 2
    assert result.diagnostics.cloud.max_qc_kg_kg == 2e-6
    assert result.diagnostics.cloud.time_of_max_qc_seconds == 3900.0
    assert result.diagnostics.vertical_velocity.min_w_m_s == -5.0
    assert result.diagnostics.vertical_velocity.max_w_m_s == 7.0
    assert result.diagnostics.surface_fluxes.hfx.available is True
    assert result.diagnostics.surface_fluxes.hfx.units == "K m/s"
    assert result.diagnostics.surface_fluxes.hfx.min_value == pytest.approx(1.0)
    assert result.diagnostics.surface_fluxes.hfx.max_value == pytest.approx(3.0)
    assert result.diagnostics.surface_fluxes.hfx.mean_value == pytest.approx(2.0)
    assert result.diagnostics.surface_fluxes.hfx.finite_count == 24
    assert result.diagnostics.surface_fluxes.hfx.total_count == 24
    assert result.diagnostics.surface_fluxes.qfx.available is True
    assert result.diagnostics.surface_fluxes.qfx.units == "kg/m^2/s"
    assert result.diagnostics.surface_fluxes.qfx.min_value == pytest.approx(1.0e-5)
    assert result.diagnostics.surface_fluxes.qfx.max_value == pytest.approx(3.0e-5)
    assert result.diagnostics.surface_fluxes.qfx.mean_value == pytest.approx(2.0e-5)
    assert result.diagnostics.surface_fluxes.qfx.finite_count == 24
    assert result.diagnostics.surface_fluxes.qfx.total_count == 24
    assert result.diagnostics.field_quality["hfx"].quality_state == "trusted"
    assert result.diagnostics.field_quality["qfx"].quality_state == "trusted"
    assert result.diagnostics.low_level_response.qv.available is True
    assert result.diagnostics.low_level_response.qv.first_time_seconds == 300.0
    assert result.diagnostics.low_level_response.qv.final_time_seconds == 3900.0
    assert result.diagnostics.low_level_response.qv.early_response_end_time_seconds == 3900.0
    assert result.diagnostics.low_level_response.qv.delta_value == pytest.approx(0.006)
    assert result.diagnostics.low_level_response.qv.early_response_available is True
    assert result.diagnostics.low_level_response.qv.full_run_response_available is False
    assert result.diagnostics.low_level_response.qv.full_run_delta is None
    assert result.diagnostics.low_level_response.theta_or_temperature.available is True
    assert result.diagnostics.low_level_response.theta_or_temperature.delta_value == pytest.approx(
        4.0
    )
    assert (
        "qv_low_level_response_requires_at_least_two_time_steps" not in result.diagnostics.caveats
    )
    interesting = {record.key: record for record in result.interesting_times}
    assert interesting["first_cloud"].support_state == "supported"
    assert interesting["first_cloud"].time_index == 1
    assert interesting["first_cloud"].time_seconds == 3900.0
    assert interesting["max_qc"].support_state == "supported"
    assert interesting["max_qc"].time_index == 1
    assert interesting["max_updraft_w"].time_index == 1
    assert interesting["min_downdraft_w"].time_index == 0
    assert interesting["rain_onset"].support_state == "unsupported_missing_fields"
    assert interesting["max_dbz"].support_state == "unsupported_missing_fields"
    assert interesting["latest_output"].time_index == 1
    assert interesting["field_default_time"].time_index == 1
    assert result.default_time_by_field["qc"].time_index == 1
    assert result.default_time_by_field["w"].time_index == 1
    assert result.default_time_by_field["qr"].support_state == "fallback"
    assert result.science_summary is not None
    assert result.science_summary.first_cloud_time_seconds == 3900.0
    assert result.science_summary.max_qc_kg_kg == 2e-6
    assert result.science_summary.max_qc_time_seconds == 3900.0
    assert result.science_summary.max_updraft_w_m_s == 7.0
    assert result.science_summary.min_downdraft_w_m_s == -5.0
    assert result.science_summary.latest_output_time_seconds == 3900.0
    assert result.science_summary.low_level_response.qv.delta_value == pytest.approx(0.006)
    availability = {item.key: item for item in result.science_summary.diagnostic_availability}
    assert availability["low_level_qv_response"].support_state == "supported"
    assert availability["low_level_qv_response"].value == pytest.approx(0.006)


def test_ingest_keeps_rain_water_surface_rain_and_reflectivity_distinct(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-precip-fields")
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    write_model_netcdf(
        netcdf_path,
        times=[0.0, 600.0],
        qc_values=[0.0, 2e-6],
        w_values=[1.0, 4.0],
        qr_values=[2e-7, 4e-7],
        rain_values=[0.0, 3.5],
        dbz_values=[-5.0, 28.0],
    )
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    result = ingest_completed_run(manifest_path)

    assert result.diagnostics is not None
    assert result.diagnostics.rain.present is True
    assert result.diagnostics.rain.max_qr_kg_kg == 4e-7
    assert result.diagnostics.surface_rain.present is True
    assert result.diagnostics.surface_rain.max_surface_rain == 3.5
    assert result.diagnostics.surface_rain.units == "mm"
    assert result.diagnostics.reflectivity.available is True
    assert result.diagnostics.reflectivity.max_dbz == 28.0
    assert result.diagnostics.reflectivity.units == "dBZ"
    assert result.science_summary is not None
    assert result.science_summary.max_qr_kg_kg == 4e-7
    assert result.science_summary.max_rain_or_surface_precip == 3.5
    assert result.science_summary.max_dbz_or_reflectivity_proxy == 28.0
    assert result.default_time_by_field["rain"].source_interesting_time_key == "max_surface_rain"
    assert result.default_time_by_field["dbz"].source_interesting_time_key == "max_dbz"
    assert result.science_summary.default_explore_time_index == 1
    assert result.science_summary.interesting_time_support_state == "supported"
    product_manifest = output_product_manifest_from_json(
        default_output_product_manifest_path(run_dir).read_text()
    )
    assert product_manifest.interesting_time_product is not None
    assert product_manifest.interesting_time_product.science_summary == result.science_summary


def test_ingest_marks_sequence_diagnostics_available_when_later_file_has_fields(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-fields-arrive-later")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    write_model_netcdf(
        first,
        times=[0.0],
        qc_values=[0.0],
        w_values=[0.0],
    )
    write_model_netcdf(
        second,
        times=[900.0],
        qc_values=[2e-6],
        w_values=[3.0],
        qr_values=[4e-7],
        rain_values=[1.5],
        dbz_values=[24.0],
    )
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(first), str(second)]))

    result = ingest_completed_run(manifest_path)

    assert result.diagnostics is not None
    assert result.diagnostics.cloud.available is True
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.rain.available is True
    assert result.diagnostics.rain.present is True
    assert result.diagnostics.rain.field_absent is False
    assert result.diagnostics.surface_rain.available is True
    assert result.diagnostics.surface_rain.present is True
    assert result.diagnostics.surface_rain.field_absent is False
    assert result.diagnostics.reflectivity.available is True
    assert result.diagnostics.reflectivity.max_dbz == 24.0
    assert result.diagnostics.reflectivity.field_absent is False


def test_ingests_deep_convection_candidate_outcome_comparison(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-deep-convection-result")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    candidate_screening = {
        "candidate_id": "USM00072357-2025052000-supercell",
        "primary_story": "supercell_environment",
        "rank_score": 93.0,
        "confidence": "supported",
    }
    write_model_netcdf(
        first,
        times=[300.0],
        qc_values=[0.0],
        w_values=[2.0],
        qr_values=[0.0],
        z_values=[500.0, 1500.0, 9500.0],
    )
    write_model_netcdf(
        second,
        times=[900.0],
        qc_values=[2e-6],
        w_values=[15.0],
        qr_values=[4e-7],
        z_values=[500.0, 1500.0, 9500.0],
    )
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(first), str(second)]),
    )
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "candidate_screening": candidate_screening,
                "run_recipe": "observed_surface_forced_evolution",
                "run_recipe_display_name": "Observed Surface-Forced Evolution",
                "recipe_id": "observed_surface_forced_evolution_v0",
                "recipe_display_name": "Observed Surface-Forced Evolution v0",
                "assumption_set_id": "observed_surface_forced_evolution_v0_assumptions",
                "assumption_mode": "observed_surface_forced_evolution",
                "recipe_assumptions": {
                    "trigger": {"mode": "none"},
                    "surface_fluxes": {
                        "mode": "constant_uniform",
                        "sensible_heat_flux_k_m_s": 8.0e-3,
                        "moisture_flux_g_g_m_s": 5.2e-5,
                    },
                    "radiation": {"mode": "disabled"},
                },
                "required_output_fields": ["qc", "w", "qr", "rain", "dbz"],
                "input_source": "observed_sounding",
                "expected_outputs": ["qc", "qr", "w", "rain", "dbz"],
                "manual_validation_status": "observed_surface_forced_evolution_v0_metadata_only",
            }
        ),
    )

    result = ingest_completed_run(manifest_path)

    assert result.candidate_screening == candidate_screening
    assert result.science_summary is not None
    assert result.science_summary.deep_cloud_formed is True
    assert result.science_summary.strong_updraft_formed is True
    assert result.science_summary.time_of_first_deep_convection_seconds == 900.0
    assert result.science_summary.default_explore_time_seconds == 900.0
    assert result.candidate_hypothesis_comparison is not None
    assert result.candidate_hypothesis_comparison.screened_as == "Supercell-like environment"
    assert result.candidate_hypothesis_comparison.ran_as == "Observed Surface-Forced Evolution v0"
    assert result.candidate_hypothesis_comparison.match_status == "partially_supported"
    assert result.candidate_hypothesis_comparison.cm1_outcome == (
        "Deep convection formed with strong updraft and rain water aloft."
    )
    assert any(
        caveat.startswith("required_output_fields_missing_for_deep_candidate_comparison")
        for caveat in result.candidate_hypothesis_comparison.caveats
    )
    assert "max updraft 15 m/s" in result.candidate_hypothesis_comparison.evidence
    assert "rain-water-aloft onset 900 s" in result.candidate_hypothesis_comparison.evidence
    availability = {item.key: item for item in result.science_summary.diagnostic_availability}
    assert availability["max_dbz_or_reflectivity_proxy"].support_state == (
        "unsupported_missing_fields"
    )


def test_deep_candidate_comparison_uses_observed_surface_forced_outcome(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-observed-quicklook-candidate")
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    candidate_screening = {
        "candidate_id": "USM00072357-2025052000-supercell",
        "primary_story": "supercell_environment",
        "rank_score": 93.0,
    }
    write_model_netcdf(
        netcdf_path,
        times=[300.0],
        qc_values=[0.0],
        w_values=[1.0],
        qr_values=[0.0],
    )
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "candidate_screening": candidate_screening,
                "run_recipe": "observed_surface_forced_evolution",
                "run_recipe_display_name": "Observed Surface-Forced Evolution",
                "recipe_id": "observed_surface_forced_evolution_v0",
                "recipe_display_name": "Observed Surface-Forced Evolution v0",
                "assumption_set_id": "observed_surface_forced_evolution_v0_assumptions",
                "assumption_mode": "observed_surface_forced_evolution",
                "recipe_assumptions": {
                    "trigger": {"mode": "none"},
                    "radiation": {"mode": "disabled"},
                    "large_scale_forcing": {"mode": "none"},
                },
                "required_output_fields": ["qv", "qc", "w", "qr", "rain", "dbz"],
                "recipe_caveats": ["No artificial atmospheric trigger is applied."],
                "input_source": "observed_sounding",
            }
        ),
    )

    result = ingest_completed_run(manifest_path)

    assert result.science_summary is not None
    assert result.science_summary.cm1_outcome is None
    assert result.recipe_id == "observed_surface_forced_evolution_v0"
    assert result.recipe_display_name == "Observed Surface-Forced Evolution v0"
    assert result.assumption_set_id == "observed_surface_forced_evolution_v0_assumptions"
    assert result.assumption_mode == "observed_surface_forced_evolution"
    assert result.recipe_assumptions["trigger"]["mode"] == "none"
    assert result.required_output_fields == ["qv", "qc", "w", "qr", "rain", "dbz"]
    assert result.missing_required_output_fields == ["qv", "rain", "dbz"]
    assert "Recipe required output fields missing from NetCDF metadata: qv, rain, dbz" in (
        result.warnings
    )
    assert result.candidate_hypothesis_comparison is not None
    assert result.candidate_hypothesis_comparison.match_status == "inconclusive"
    assert result.candidate_hypothesis_comparison.cm1_outcome == (
        "Deep convection did not occur under this run configuration by current "
        "cloud-top and updraft thresholds; this does not disprove the sounding's "
        "deep-convection potential."
    )
    assert "trigger" not in result.candidate_hypothesis_comparison.cm1_outcome.lower()
    assert "failed" not in result.candidate_hypothesis_comparison.cm1_outcome.lower()
    assert "comparison_requires_triggered_deep_potential_run" not in (
        result.candidate_hypothesis_comparison.caveats
    )
    assert "no_storm_under_selected_surface_forcing_is_not_failed_potential" in (
        result.candidate_hypothesis_comparison.caveats
    )


def test_deep_candidate_comparison_caveats_untrusted_rain_water_field(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-untrusted-rain-water")
    run_dir = manifest_path.parent
    netcdf_path = run_dir / "cm1out_000001.nc"
    write_model_netcdf(
        netcdf_path,
        times=[900.0],
        qc_values=[2e-5],
        w_values=[15.0],
        qr_values=[float("nan")],
        z_values=[500.0, 10500.0],
    )
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))
    manifest = load_run_manifest(manifest_path)
    write_run_manifest(
        manifest_path,
        manifest.model_copy(
            update={
                "candidate_screening": {
                    "candidate_id": "USM00072357-2025052000-supercell",
                    "primary_story": "supercell_environment",
                    "rank_score": 93.0,
                },
                "run_recipe": "observed_surface_forced_evolution",
                "recipe_display_name": "Observed Surface-Forced Evolution v0",
                "required_output_fields": ["qc", "w", "qr"],
                "input_source": "observed_sounding",
            }
        ),
    )

    result = ingest_completed_run(manifest_path)

    assert result.diagnostics is not None
    assert result.diagnostics.field_quality["qr"].quality_state == "untrusted"
    comparison = result.candidate_hypothesis_comparison
    assert comparison is not None
    assert comparison.match_status == "partially_supported"
    assert not any("rain-water-aloft onset" in item for item in comparison.evidence)
    assert any(
        caveat.startswith("field_quality_untrusted:qr:qr_field_entirely_non_finite")
        for caveat in comparison.caveats
    )


def test_no_cloud_result_keeps_interesting_times_honest(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-no-cloud-interesting-times")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[0.0], qc_values=[0.0], w_values=[1.0])
    write_model_netcdf(second, times=[900.0], qc_values=[0.0], w_values=[2.0])
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(first), str(second)]))

    result = ingest_completed_run(manifest_path)

    interesting = {record.key: record for record in result.interesting_times}
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is False
    assert interesting["first_cloud"].support_state == "unavailable"
    assert interesting["first_cloud"].time_index is None
    assert interesting["first_cloud"].caveats == ["no_cloud_formed"]
    assert interesting["max_qc"].support_state == "unavailable"
    assert interesting["max_qc"].time_index is None
    assert interesting["max_qc"].caveats == ["no_positive_cloud_water_detected"]
    assert interesting["max_updraft_w"].support_state == "supported"
    assert interesting["max_updraft_w"].time_index == 1
    assert interesting["latest_output"].time_index == 1
    assert result.default_time_by_field["qc"].support_state == "fallback"
    assert result.default_time_by_field["qc"].source_interesting_time_key == "latest_output"
    assert result.default_time_by_field["w"].support_state == "supported"
    assert result.science_summary is not None
    assert result.science_summary.first_cloud_time_seconds is None
    assert result.science_summary.max_qc_kg_kg == 0.0
    assert result.science_summary.max_qc_time_seconds is None
    assert result.science_summary.default_explore_time_index == 1
    assert "no_cloud_formed" in result.interesting_time_caveats


def test_multifile_ingest_does_not_concatenate_full_sequence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-no-concat")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[300.0], qc_values=[0.0], w_values=[1.0])
    write_model_netcdf(second, times=[600.0], qc_values=[2e-6], w_values=[7.0])
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(first), str(second)]),
    )

    def fail_concat(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("multi-file ingest should not concatenate full NetCDF sequence")

    monkeypatch.setattr(xr, "concat", fail_concat)

    result = ingest_completed_run(manifest_path)

    assert result.time_steps == 2
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.cloud.time_of_max_qc_seconds == 600.0


def test_ingests_multifile_with_multiple_timesteps_per_file(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-multistep")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    second = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[0.0, 300.0], qc_values=[0.0, 0.0], w_values=[-1.0, 2.0])
    write_model_netcdf(
        second,
        times=[600.0, 900.0],
        qc_values=[0.0, 4e-6],
        w_values=[3.0, 4.0],
    )
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(second), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_file_count == 2
    assert result.time_steps == 4
    assert result.first_output_time_seconds == 0.0
    assert result.last_output_time_seconds == 900.0
    assert result.diagnostics is not None
    assert len(result.diagnostics.cloud.qc_max_time_series) == 4
    assert result.diagnostics.cloud.formed is True
    assert result.diagnostics.cloud.first_cloud_time_seconds == 900.0
    assert result.diagnostics.vertical_velocity.time_of_max_w_seconds == 900.0


def test_ingest_records_corrupt_model_file_caveat_and_uses_remaining_outputs(
    tmp_path: Path,
) -> None:
    manifest_path = create_manifest(tmp_path, run_id="run-corrupt")
    run_dir = manifest_path.parent
    first = run_dir / "cm1out_000001.nc"
    corrupt = run_dir / "cm1out_000002.nc"
    write_model_netcdf(first, times=[300.0], qc_values=[0.0], w_values=[1.0])
    corrupt.write_text("not netcdf")
    complete_manifest(
        manifest_path,
        OutputMetadata(netcdf_paths=[str(corrupt), str(first)]),
    )

    result = ingest_completed_run(manifest_path)

    assert result.model_output_paths == [str(first)]
    assert result.model_output_file_count == 1
    assert len(result.skipped_netcdf_paths) == 1
    assert str(corrupt) in result.skipped_netcdf_paths[0]
    assert any("skipped_netcdf_output" in warning for warning in result.warnings)


def test_ingest_fails_when_only_stats_netcdf_exists(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    stats = manifest_path.parent / "cm1out_stats.nc"
    write_stats_netcdf(stats)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(stats)]))

    with pytest.raises(ResultIngestError, match="No CM1 model-field NetCDF output files"):
        ingest_completed_run(manifest_path)


def test_missing_netcdf_output_fails_gracefully(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    raw_path = manifest_path.parent / "cm1out_000001_s.dat"
    raw_path.write_text("raw CM1 artifact")
    complete_manifest(
        manifest_path,
        OutputMetadata(raw_cm1_artifacts=[str(raw_path)]),
    )

    with pytest.raises(ResultIngestError, match="No NetCDF output artifacts"):
        ingest_completed_run(manifest_path)


def test_packaged_manifest_is_not_ingested(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path)

    with pytest.raises(ResultIngestError, match="Only completed CM1 runs"):
        ingest_completed_run(manifest_path)


def test_malformed_netcdf_fails_gracefully(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    netcdf_path.write_text("not a netcdf file")
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    with pytest.raises(ResultIngestError, match="Could not open NetCDF output"):
        ingest_completed_run(manifest_path)


def test_missing_expected_fields_are_warnings_not_claimed_diagnostics(tmp_path: Path) -> None:
    manifest_path = create_manifest(tmp_path)
    netcdf_path = manifest_path.parent / "cm1out_000001.nc"
    write_tiny_netcdf(netcdf_path, include_qc=False, include_w=True)
    complete_manifest(manifest_path, OutputMetadata(netcdf_paths=[str(netcdf_path)]))

    result = ingest_completed_run(manifest_path)

    assert result.variables == ["w"]
    assert result.diagnostics_summary == (
        "cloud unavailable; rain water aloft unavailable; surface rain unavailable; "
        "reflectivity unavailable"
    )
    assert result.diagnostics is not None
    assert result.diagnostics.cloud.available is False
    assert result.diagnostics.field_quality["qc"].quality_state == "unavailable"
    assert result.diagnostics.field_quality["w"].quality_state == "trusted"
    assert result.warnings == [
        "Expected fields missing from NetCDF metadata: qc",
        (
            "Recipe required output fields missing from NetCDF metadata: "
            "qv, qc, qr, rain, dbz, hfx, qfx"
        ),
    ]

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr
from fastapi.testclient import TestClient

from cloud_chamber.app import app
from cloud_chamber.dry_run_package import generate_dry_run_package
from cloud_chamber.result_ingest import ingest_completed_run
from cloud_chamber.run_manifest import (
    LifecycleState,
    OutputMetadata,
    ProductState,
    ProvenanceMetadata,
    load_run_manifest,
    write_run_manifest,
)
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.visualization_data import (
    VisualizationDataError,
    field_catalog,
    field_slice,
    output_product_catalog,
    point_cloud,
    time_height_product,
    time_series_product,
    vertical_profile,
    view_defaults,
)

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


def create_visualization_result(
    tmp_path: Path,
    *,
    include_qc: bool = True,
    include_w: bool = True,
    include_u: bool = True,
    include_v: bool = True,
    include_qr: bool = False,
    include_qv: bool = True,
    include_dbz: bool = True,
    run_id: str = "run-visualization",
    package_updates: dict[str, object] | None = None,
) -> tuple[CloudChamberSettings, str, Path]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id=run_id,
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    write_visualization_netcdf(
        netcdf_path,
        include_qc=include_qc,
        include_w=include_w,
        include_u=include_u,
        include_v=include_v,
        include_qr=include_qr,
        include_qv=include_qv,
        include_dbz=include_dbz,
    )
    manifest = load_run_manifest(package.manifest_path)
    update_payload = {
        "lifecycle_state": LifecycleState.COMPLETED,
        "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
        "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
    }
    update_payload.update(package_updates or {})
    write_run_manifest(package.manifest_path, manifest.model_copy(update=update_payload))
    result = ingest_completed_run(package.manifest_path)
    return settings, result.result_id, package.package_dir


def create_multifile_visualization_result(
    tmp_path: Path,
    *,
    file_count: int = 3,
    run_id: str = "run-multifile-visualization",
) -> tuple[CloudChamberSettings, str, Path]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id=run_id,
    )
    paths: list[Path] = []
    for index in range(file_count):
        path = package.package_dir / f"cm1out_{index + 1:06d}.nc"
        write_single_time_visualization_netcdf(
            path,
            time_seconds=float(index * 600),
            qc_value=(index + 1) * 1e-5,
            w_value=float(index + 1),
        )
        paths.append(path)
    manifest = load_run_manifest(package.manifest_path)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(path) for path in paths]),
            }
        ),
    )
    result = ingest_completed_run(package.manifest_path)
    return settings, result.result_id, package.package_dir


def create_realistic_field_catalog_result(
    tmp_path: Path,
) -> tuple[CloudChamberSettings, str, Path]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id="run-realistic-field-catalog",
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    write_realistic_field_catalog_netcdf(netcdf_path)
    manifest = load_run_manifest(package.manifest_path)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
                "expected_outputs": [
                    "qc",
                    "w",
                    "u",
                    "v",
                    "qv",
                    "prs",
                    "hfx",
                    "qfx",
                    "swten",
                    "lwp",
                    "CAPE",
                    "CIN",
                    "LCL",
                    "LFC",
                    "dbz",
                ],
            }
        ),
    )
    result = ingest_completed_run(package.manifest_path)
    return settings, result.result_id, package.package_dir


def write_visualization_netcdf(
    path: Path,
    *,
    include_qc: bool,
    include_w: bool,
    include_u: bool,
    include_v: bool,
    include_qr: bool,
    include_qv: bool,
    include_dbz: bool,
) -> None:
    data_vars: dict[str, Any] = {}
    if include_qc:
        qc = np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) * 1e-6
        qc[0, 0, 0, 0] = np.nan
        qc[1, 1, 2, 3] = np.inf
        data_vars["qc"] = (
            ("time", "zh", "yh", "xh"),
            qc,
            {"units": "kg/kg"},
        )
    if include_w:
        w = np.arange(2 * 3 * 3 * 4, dtype=float).reshape(2, 3, 3, 4)
        data_vars["w"] = (
            ("time", "zf", "yh", "xh"),
            w,
            {"units": "m/s"},
        )
    if include_u:
        u = 5.0 + np.arange(2 * 2 * 3 * 5, dtype=float).reshape(2, 2, 3, 5) * 0.1
        data_vars["u"] = (
            ("time", "zh", "yh", "xf"),
            u,
            {"units": "m/s"},
        )
    if include_v:
        v = -2.0 + np.arange(2 * 2 * 4 * 4, dtype=float).reshape(2, 2, 4, 4) * 0.2
        data_vars["v"] = (
            ("time", "zh", "yf", "xh"),
            v,
            {"units": "m/s"},
        )
    if include_qr:
        qr = np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) * 1e-7
        data_vars["qr"] = (
            ("time", "zh", "yh", "xh"),
            qr,
            {"units": "kg/kg"},
        )
    data_vars["theta"] = (
        ("time", "zh", "yh", "xh"),
        300.0 + np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) * 0.1,
        {"units": "K"},
    )
    data_vars["temperature"] = (
        ("time", "zh", "yh", "xh"),
        285.0 + np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) * 0.2,
        {"units": "K"},
    )
    if include_qv:
        qv = 0.010 + np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) * 1e-5
        data_vars["qv"] = (
            ("time", "zh", "yh", "xh"),
            qv,
            {"units": "kg/kg"},
        )
    if include_dbz:
        dbz = np.arange(2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4) - 10.0
        data_vars["dbz"] = (
            ("time", "zh", "yh", "xh"),
            dbz,
            {"units": "dBZ"},
        )
    rain = np.arange(2 * 3 * 4, dtype=float).reshape(2, 3, 4) * 0.25
    data_vars["rain"] = (
        ("time", "yh", "xh"),
        rain,
        {"units": "mm"},
    )
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": ("time", [0.0, 900.0], {"units": "s"}),
            "zh": ("zh", [0.4, 0.8], {"units": "km"}),
            "zf": ("zf", [0.0, 0.4, 0.8], {"units": "km"}),
            "yh": ("yh", [0.0, 1.0, 2.0], {"units": "km"}),
            "yf": ("yf", [-0.5, 0.5, 1.5, 2.5], {"units": "km"}),
            "xh": ("xh", [0.0, 1.0, 2.0, 3.0], {"units": "km"}),
            "xf": ("xf", [-0.5, 0.5, 1.5, 2.5, 3.5], {"units": "km"}),
        },
    ).to_netcdf(path, engine="scipy")


def write_realistic_field_catalog_netcdf(path: Path) -> None:
    volume_shape = (2, 2, 3, 4)
    surface_shape = (2, 3, 4)
    volume = np.arange(np.prod(volume_shape), dtype=float).reshape(volume_shape)
    surface = np.arange(np.prod(surface_shape), dtype=float).reshape(surface_shape)
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "zh", "yh", "xh"),
                volume * 1e-6,
                {"units": "kg/kg"},
            ),
            "w": (
                ("time", "zf", "yh", "xh"),
                np.arange(2 * 3 * 3 * 4, dtype=float).reshape(2, 3, 3, 4),
                {"units": "m/s"},
            ),
            "u": (
                ("time", "zh", "yh", "xf"),
                5.0 + np.arange(2 * 2 * 3 * 5, dtype=float).reshape(2, 2, 3, 5) * 0.1,
                {"units": "m/s"},
            ),
            "v": (
                ("time", "zh", "yf", "xh"),
                -2.0 + np.arange(2 * 2 * 4 * 4, dtype=float).reshape(2, 2, 4, 4) * 0.2,
                {"units": "m/s"},
            ),
            "qv": (
                ("time", "zh", "yh", "xh"),
                0.010 + volume * 1e-5,
                {"units": "kg/kg"},
            ),
            "prs": (
                ("time", "zh", "yh", "xh"),
                90000.0 - volume * 10.0,
                {"units": "Pa"},
            ),
            "hfx": (
                ("time", "yh", "xh"),
                surface,
                {"units": "W m-2"},
            ),
            "qfx": (
                ("time", "yh", "xh"),
                surface * 1e-7,
                {"units": "kg/m^2/s"},
            ),
            "psfc": (
                ("time", "yh", "xh"),
                95000.0 + surface,
                {"units": "Pa"},
            ),
            "swten": (
                ("time", "zh", "yh", "xh"),
                volume * 1e-4,
                {"units": "K/s"},
            ),
            "lwp": (
                ("time", "yh", "xh"),
                surface * 1e-3,
                {"units": "kg m-2"},
            ),
            "CAPE": (
                ("time", "yh", "xh"),
                surface * 10.0,
                {"units": "J/kg"},
            ),
            "CIN": (
                ("time", "yh", "xh"),
                -surface,
                {"units": "J/kg"},
            ),
            "LCL": (
                ("time", "yh", "xh"),
                800.0 + surface,
                {"units": "m"},
            ),
            "LFC": (
                ("time", "yh", "xh"),
                1500.0 + surface,
                {"units": "m"},
            ),
        },
        coords={
            "time": ("time", [0.0, 900.0], {"units": "s"}),
            "zh": ("zh", [0.4, 0.8], {"units": "km"}),
            "zf": ("zf", [0.0, 0.4, 0.8], {"units": "km"}),
            "yh": ("yh", [0.0, 1.0, 2.0], {"units": "km"}),
            "yf": ("yf", [-0.5, 0.5, 1.5, 2.5], {"units": "km"}),
            "xh": ("xh", [0.0, 1.0, 2.0, 3.0], {"units": "km"}),
            "xf": ("xf", [-0.5, 0.5, 1.5, 2.5, 3.5], {"units": "km"}),
        },
    ).to_netcdf(path, engine="scipy")


def write_single_time_visualization_netcdf(
    path: Path,
    *,
    time_seconds: float,
    qc_value: float,
    w_value: float,
) -> None:
    xr.Dataset(
        data_vars={
            "qc": (
                ("time", "zh", "yh", "xh"),
                np.full((1, 2, 3, 4), qc_value, dtype=float),
                {"units": "kg/kg"},
            ),
            "w": (
                ("time", "zf", "yh", "xh"),
                np.full((1, 3, 3, 4), w_value, dtype=float),
                {"units": "m/s"},
            ),
        },
        coords={
            "time": ("time", [time_seconds], {"units": "s"}),
            "zh": ("zh", [0.4, 0.8], {"units": "km"}),
            "zf": ("zf", [0.0, 0.4, 0.8], {"units": "km"}),
            "yh": ("yh", [0.0, 1.0, 2.0], {"units": "km"}),
            "xh": ("xh", [0.0, 1.0, 2.0, 3.0], {"units": "km"}),
        },
    ).to_netcdf(path, engine="scipy")


def test_field_catalog_includes_qc_and_w_with_provenance(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    catalog = field_catalog(settings, result_id)

    fields = {field.raw_field_name: field for field in catalog.available_fields}
    assert set(fields) >= {"qc", "w"}
    assert fields["qc"].canonical_field_name == "cloud_water"
    assert fields["qc"].native_grid == "zh/yh/xh"
    assert fields["qc"].coordinate_names.vertical == "zh"
    assert fields["qc"].time_coordinate_values == [0.0, 900.0]
    assert fields["w"].canonical_field_name == "vertical_velocity"
    assert fields["w"].native_grid == "zf/yh/xh"
    assert fields["w"].coordinate_names.vertical == "zf"
    assert fields["u"].canonical_field_name == "east_west_wind"
    assert fields["u"].native_grid == "zh/yh/xf"
    assert fields["u"].coordinate_names.x == "xf"
    assert "native_staggered_wind_component" in fields["u"].caveats
    assert fields["v"].canonical_field_name == "north_south_wind"
    assert fields["v"].native_grid == "zh/yf/xh"
    assert fields["v"].coordinate_names.y == "yf"
    assert "native_staggered_wind_component" in fields["v"].caveats
    assert fields["theta"].canonical_field_name == "potential_temperature"
    assert fields["theta"].units == "K"
    assert fields["temperature"].canonical_field_name == "temperature"
    assert fields["temperature"].units == "K"
    assert fields["qv"].canonical_field_name == "water_vapor"
    assert fields["dbz"].canonical_field_name == "reflectivity"
    assert fields["rain"].canonical_field_name == "accumulated_surface_rain"
    assert fields["rain"].native_grid == "surface/yh/xh"
    assert catalog.provenance.source_model == "CM1"
    assert "native-grid view" in catalog.provenance.provenance_label


def test_field_catalog_uses_ingested_metadata_without_reopening_netcdf(tmp_path: Path) -> None:
    settings, result_id, run_dir = create_visualization_result(tmp_path)
    for path in run_dir.glob("cm1out_*.nc"):
        path.unlink()

    catalog = field_catalog(settings, result_id)

    fields = {field.raw_field_name: field for field in catalog.available_fields}
    assert set(fields) >= {"qc", "w"}
    assert fields["qc"].shape == [2, 2, 3, 4]
    assert fields["qc"].time_coordinate_values == [0.0, 900.0]
    assert catalog.provenance.processing_method == "ingested_result_metadata_field_catalog"


def test_field_catalog_handles_missing_qc_and_missing_w(tmp_path: Path) -> None:
    settings_qc_missing, result_id_qc_missing, _run_dir = create_visualization_result(
        tmp_path / "qc-missing",
        include_qc=False,
        include_w=True,
        run_id="run-qc-missing",
    )
    settings_w_missing, result_id_w_missing, _run_dir = create_visualization_result(
        tmp_path / "w-missing",
        include_qc=True,
        include_w=False,
        run_id="run-w-missing",
    )

    qc_missing = field_catalog(settings_qc_missing, result_id_qc_missing)
    w_missing = field_catalog(settings_w_missing, result_id_w_missing)

    assert "qc" not in {field.raw_field_name for field in qc_missing.available_fields}
    assert "missing_visualization_field:qc" in qc_missing.caveats
    assert "w" not in {field.raw_field_name for field in w_missing.available_fields}
    assert "missing_visualization_field:w" in w_missing.caveats


def test_field_catalog_classifies_realistic_output_fields_conservatively(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_realistic_field_catalog_result(tmp_path)

    catalog = field_catalog(settings, result_id)

    fields = {field.raw_field_name: field for field in catalog.available_fields}
    assert set(fields) >= {
        "qv",
        "prs",
        "hfx",
        "qfx",
        "psfc",
        "swten",
        "lwp",
        "CAPE",
        "CIN",
        "LCL",
        "LFC",
    }

    assert fields["qv"].field_family == "thermodynamic"
    assert fields["qv"].native_grid_class == "volume_3d"
    assert fields["qv"].capabilities.slice is True
    assert fields["qv"].capabilities.point_cloud is True
    assert fields["qv"].capabilities.selected_column is True
    assert fields["qv"].capabilities.profile_candidate is True
    assert fields["qv"].capabilities.time_height_candidate is True
    assert fields["qv"].capabilities.render_ready_candidate is True

    assert fields["prs"].canonical_field_name == "pressure"
    assert fields["prs"].capabilities.slice is True
    assert fields["prs"].capabilities.point_cloud is False
    assert fields["prs"].capabilities.profile_candidate is True
    assert fields["prs"].capabilities.time_height_candidate is True
    assert "pressure_field_slice_profile_first" in fields["prs"].caveats

    assert fields["hfx"].field_family == "surface_flux"
    assert fields["hfx"].native_grid_class == "surface_2d"
    assert fields["hfx"].native_grid == "surface/yh/xh"
    assert fields["hfx"].capabilities.slice is True
    assert fields["hfx"].capabilities.point_cloud is False
    assert fields["hfx"].capabilities.selected_point is True
    assert fields["hfx"].capabilities.selected_column is False
    assert fields["hfx"].capabilities.profile_candidate is False
    assert fields["hfx"].capabilities.time_height_candidate is False
    assert "surface_flux_field_not_cloud_outcome" in fields["hfx"].caveats

    assert fields["swten"].field_family == "radiation"
    assert fields["swten"].capabilities.slice is True
    assert fields["swten"].capabilities.point_cloud is False
    assert "radiation_field_cataloged_when_present" in fields["swten"].caveats

    assert fields["lwp"].field_family == "column_integrated_water"
    assert fields["lwp"].native_grid_class == "surface_2d"
    assert fields["lwp"].capabilities.profile_candidate is False
    assert "column_integrated_field_no_vertical_profile" in fields["lwp"].caveats

    assert fields["CAPE"].canonical_field_name == "cape"
    assert fields["CAPE"].display_name == "CAPE"
    assert fields["CAPE"].native_grid_class == "surface_2d"
    assert fields["CAPE"].capabilities.point_cloud is False
    assert "parcel_diagnostic_field_catalog_only" in fields["CAPE"].caveats
    assert fields["CAPE"].frontend_consumer_guidance


def test_field_catalog_reports_expected_known_fields_unavailable(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_realistic_field_catalog_result(tmp_path)

    catalog = field_catalog(settings, result_id)

    unavailable = {field.raw_field_name: field for field in catalog.unavailable_fields}
    assert "dbz" in unavailable
    assert unavailable["dbz"].canonical_field_name == "reflectivity"
    assert unavailable["dbz"].expected_by_run is True
    assert unavailable["dbz"].reason == "expected_known_field_missing_from_result_metadata"
    assert "field_not_present_in_ingested_netcdf_metadata" in unavailable["dbz"].caveats
    assert "expected_field_unavailable:dbz" in catalog.caveats


def test_pressure_slice_is_available_but_pressure_point_cloud_is_blocked(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_realistic_field_catalog_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="prs",
        time_index=0,
        orientation="horizontal",
        level_index=0,
    )

    assert sliced.field.raw_field_name == "prs"
    assert sliced.field.canonical_field_name == "pressure"
    assert sliced.field.capabilities.slice is True
    assert sliced.field.capabilities.point_cloud is False
    assert sliced.stats.max == pytest.approx(90000.0)
    with pytest.raises(VisualizationDataError, match="not 3-D point-cloud"):
        point_cloud(
            settings,
            result_id,
            field="prs",
            time_index=0,
            threshold=0,
            max_points=50_000,
        )


def test_output_product_catalog_advertises_bounded_products_and_unavailable_diagnostics(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_realistic_field_catalog_result(tmp_path)

    catalog = output_product_catalog(settings, result_id)

    profile_keys = {product.product_key for product in catalog.available_profile_products}
    time_height_keys = {product.product_key for product in catalog.available_time_height_products}
    time_series_keys = {product.product_key for product in catalog.available_time_series_products}
    unavailable = {product.product_key: product for product in catalog.unavailable_products}

    assert "profile:qv" in profile_keys
    assert "profile:prs" in profile_keys
    assert "profile:u" in profile_keys
    assert "profile:v" in profile_keys
    assert "time_height:qv" in time_height_keys
    assert "time_height:swten" in time_height_keys
    assert "time_height:u" in time_height_keys
    assert "time_height:v" in time_height_keys
    assert "time_series:hfx" in time_series_keys
    assert "time_series:qfx" in time_series_keys
    assert "time_series:u" in time_series_keys
    assert "time_series:v" in time_series_keys
    assert unavailable["boundary_layer_depth_time_series"].status == "unavailable"
    assert unavailable["boundary_layer_depth_time_series"].reason == (
        "future_diagnostic_method_not_validated"
    )
    assert unavailable["unavailable:dbz"].reason == (
        "expected_known_field_missing_from_result_metadata"
    )
    assert unavailable["unavailable:dbz"].field_quality is not None
    assert unavailable["unavailable:dbz"].field_quality.assessed is True
    assert unavailable["unavailable:dbz"].field_quality.quality_state == "unavailable"
    assert unavailable["near_surface_wind_time_series:u"].reason == (
        "near_surface_wind_diagnostic_not_implemented"
    )
    assert (
        "wind_component_not_wind_gust_outflow_or_rotation_diagnostic"
        in unavailable["near_surface_wind_time_series:v"].caveats
    )
    assert "browser_does_not_parse_raw_netcdf" in catalog.caveats


def test_vertical_profile_domain_mean_preserves_units_coordinates_and_time_index(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    profile = vertical_profile(
        settings,
        result_id,
        field="qv",
        time_index=0,
        aggregation_method="domain_mean",
    )

    assert profile.field.canonical_field_name == "water_vapor"
    assert profile.field.units == "kg/kg"
    assert profile.vertical_dimension == "zh"
    assert profile.vertical_units == "km"
    assert profile.vertical_coordinate_values == [0.4, 0.8]
    assert profile.selection.time_index == 0
    assert profile.selection.local_time_index == 0
    assert profile.selection.source_file is not None
    assert profile.values == pytest.approx([0.010055, 0.010175])
    assert profile.finite_counts == [12, 12]
    assert profile.non_finite_counts == [0, 0]
    assert profile.aggregation_method == "domain_mean"
    assert profile.field_quality is not None
    assert profile.field_quality.assessed is False
    assert profile.field_quality.reason == "field_quality_not_tracked_for_field"
    assert "native_grid_profile_no_interpolation" in profile.caveats


def test_selected_column_profile_preserves_xy_selection_and_values(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    profile = vertical_profile(
        settings,
        result_id,
        field="qc",
        time_index=0,
        aggregation_method="selected_column",
        x_index=3,
        y_index=2,
    )

    assert profile.selection.x_index == 3
    assert profile.selection.y_index == 2
    assert profile.selection.x_coordinate_value == 3.0
    assert profile.selection.y_coordinate_value == 2.0
    assert profile.values == pytest.approx([1.1e-5, 2.3e-5])
    assert profile.finite_counts == [1, 1]
    assert profile.non_finite_counts == [0, 0]
    assert "selected_column_requires_native_x_y_indices" in profile.caveats


def test_wind_component_profiles_preserve_native_staggered_grid_and_caveats(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    u_profile = vertical_profile(
        settings,
        result_id,
        field="u",
        time_index=0,
        aggregation_method="domain_mean",
    )
    v_profile = vertical_profile(
        settings,
        result_id,
        field="v",
        time_index=0,
        aggregation_method="selected_column",
        x_index=3,
        y_index=3,
    )

    assert u_profile.field.canonical_field_name == "east_west_wind"
    assert u_profile.field.field_family == "wind"
    assert u_profile.field.units == "m/s"
    assert u_profile.field.native_grid == "zh/yh/xf"
    assert u_profile.values == pytest.approx([5.7, 7.2])
    assert u_profile.finite_counts == [15, 15]
    assert "native_staggered_wind_component" in u_profile.caveats
    assert "no_vector_interpolation" in u_profile.caveats
    assert "wind_component_not_wind_gust_outflow_or_rotation_diagnostic" in u_profile.caveats

    assert v_profile.field.canonical_field_name == "north_south_wind"
    assert v_profile.field.native_grid == "zh/yf/xh"
    assert v_profile.selection.x_coordinate_value == 3.0
    assert v_profile.selection.y_coordinate_value == 2.5
    assert v_profile.values == pytest.approx([1.0, 4.2])
    assert "v_native_y_staggered_grid" in v_profile.caveats
    assert "wind_component_not_wind_gust_outflow_or_rotation_diagnostic" in v_profile.caveats


def test_time_height_products_compute_cloud_fraction_and_w_extrema(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    cloud_fraction = time_height_product(
        settings,
        result_id,
        field="qc",
        aggregation_method="cloud_fraction",
    )
    max_w = time_height_product(
        settings,
        result_id,
        field="w",
        aggregation_method="domain_max",
    )

    assert cloud_fraction.selection.threshold == pytest.approx(1e-6)
    assert cloud_fraction.shape == [2, 2]
    assert cloud_fraction.time_axis.time_indices == [0, 1]
    assert cloud_fraction.time_axis.time_seconds == [0.0, 900.0]
    assert cloud_fraction.vertical_coordinate_values == [0.4, 0.8]
    assert cloud_fraction.values[0] == pytest.approx([1.0, 1.0])
    assert cloud_fraction.values[1] == pytest.approx([1.0, 1.0])
    assert cloud_fraction.finite_counts == [[11, 12], [12, 11]]
    assert cloud_fraction.non_finite_counts == [[1, 0], [0, 1]]
    assert cloud_fraction.field_quality is not None
    assert cloud_fraction.field_quality.assessed is True
    assert cloud_fraction.field_quality.quality_state == "caveated"
    assert cloud_fraction.field_quality.finite_count == 46
    assert cloud_fraction.field_quality.non_finite_count == 2
    assert "non_finite_values_detected_in_qc" in cloud_fraction.field_quality.quality_caveats
    assert "cloud_fraction_threshold_kg_kg:1e-06" in cloud_fraction.caveats

    assert max_w.field.canonical_field_name == "vertical_velocity"
    assert max_w.vertical_dimension == "zf"
    assert max_w.vertical_coordinate_values == [0.0, 0.4, 0.8]
    assert max_w.values[0] == pytest.approx([11.0, 23.0, 35.0])
    assert max_w.values[1] == pytest.approx([47.0, 59.0, 71.0])
    assert max_w.finite_counts == [[12, 12, 12], [12, 12, 12]]
    assert "native_grid_time_height_no_interpolation" in max_w.caveats


def test_wind_component_time_height_products_work_without_vector_claims(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    u = time_height_product(
        settings,
        result_id,
        field="u",
        aggregation_method="domain_mean",
    )
    v = time_height_product(
        settings,
        result_id,
        field="v",
        aggregation_method="domain_max",
    )

    assert u.field.canonical_field_name == "east_west_wind"
    assert u.vertical_dimension == "zh"
    assert u.values[0] == pytest.approx([5.7, 7.2])
    assert u.values[1] == pytest.approx([8.7, 10.2])
    assert u.finite_counts == [[15, 15], [15, 15]]
    assert "u_native_x_staggered_grid" in u.caveats
    assert "wind_component_not_wind_gust_outflow_or_rotation_diagnostic" in u.caveats

    assert v.field.canonical_field_name == "north_south_wind"
    assert v.values[0] == pytest.approx([1.0, 4.2])
    assert v.values[1] == pytest.approx([7.4, 10.600000000000001])
    assert v.finite_counts == [[16, 16], [16, 16]]
    assert "v_native_y_staggered_grid" in v.caveats
    assert "no_vector_interpolation" in v.caveats


def test_time_height_supports_qv_and_temperature_domain_mean(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    qv = time_height_product(
        settings,
        result_id,
        field="qv",
        aggregation_method="domain_mean",
    )
    temperature = time_height_product(
        settings,
        result_id,
        field="temperature",
        aggregation_method="domain_mean",
    )

    assert qv.values[0] == pytest.approx([0.010055, 0.010175])
    assert qv.values[1] == pytest.approx([0.010295, 0.010415])
    assert temperature.field.canonical_field_name == "temperature"
    assert temperature.values[0] == pytest.approx([286.1, 288.5])
    assert temperature.values[1] == pytest.approx([290.9, 293.3])


def test_time_series_products_cover_surface_rain_reflectivity_and_fluxes(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path / "core")
    flux_settings, flux_result_id, _run_dir = create_realistic_field_catalog_result(
        tmp_path / "flux"
    )

    surface_rain = time_series_product(
        settings,
        result_id,
        field="rain",
        aggregation_method="domain_max",
    )
    reflectivity = time_series_product(
        settings,
        result_id,
        field="dbz",
        aggregation_method="domain_max",
    )
    surface_flux = time_series_product(
        flux_settings,
        flux_result_id,
        field="hfx",
        aggregation_method="domain_mean",
    )

    assert surface_rain.field.canonical_field_name == "accumulated_surface_rain"
    assert surface_rain.units == "mm"
    assert surface_rain.values == pytest.approx([2.75, 5.75])
    assert surface_rain.finite_counts == [12, 12]
    assert surface_rain.field_quality is not None
    assert surface_rain.field_quality.assessed is True
    assert surface_rain.field_quality.source_field == "rain"
    assert surface_rain.field_quality.quality_state == "trusted"
    assert reflectivity.field.canonical_field_name == "reflectivity"
    assert reflectivity.values == pytest.approx([13.0, 37.0])
    assert reflectivity.field_quality is not None
    assert reflectivity.field_quality.assessed is True
    assert reflectivity.field_quality.quality_state == "trusted"
    assert surface_flux.field.canonical_field_name == "surface_sensible_heat_flux"
    assert surface_flux.values == pytest.approx([5.5, 17.5])
    assert surface_flux.field_quality is not None
    assert surface_flux.field_quality.assessed is True
    assert surface_flux.field_quality.source_field == "hfx"
    assert surface_flux.field_quality.quality_state == "trusted"
    assert surface_flux.field_quality.finite_count == 24
    assert surface_flux.field_quality.non_finite_count == 0
    assert "native_grid_time_series_no_interpolation" in surface_flux.caveats


def test_output_products_report_missing_fields_without_late_rendering_failure(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_realistic_field_catalog_result(tmp_path)

    catalog = output_product_catalog(settings, result_id)
    unavailable = {product.product_key: product for product in catalog.unavailable_products}

    assert "unavailable:dbz" in unavailable
    with pytest.raises(VisualizationDataError, match="missing from this result"):
        time_series_product(
            settings,
            result_id,
            field="dbz",
            aggregation_method="domain_max",
        )


def test_multifile_slice_reads_requested_output_time_without_combining_all_files(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_multifile_visualization_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="qc",
        time_index=2,
        orientation="horizontal",
        level_index=1,
    )

    assert sliced.selection.time_index == 2
    assert sliced.selection.time_seconds == 1200.0
    assert sliced.values[0][0] == pytest.approx(3e-5)


def test_multifile_point_cloud_reads_requested_output_time_without_combining_all_files(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_multifile_visualization_result(tmp_path)

    cloud = point_cloud(
        settings,
        result_id,
        field="qc",
        time_index=2,
        threshold=2e-5,
        max_points=100,
    )

    assert cloud.selection.time_index == 2
    assert cloud.selection.time_seconds == 1200.0
    assert cloud.stats.source_count == 24
    assert cloud.stats.min_value == pytest.approx(3e-5)
    assert cloud.stats.max_value == pytest.approx(3e-5)


def test_metadata_defaults_use_multifile_interesting_time_for_large_results(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_multifile_visualization_result(
        tmp_path,
        file_count=10,
    )

    defaults = view_defaults(settings, result_id)

    assert defaults.provenance.processing_method == "ingested_result_metadata_view_defaults"
    assert defaults.fields["qc"].time_index == 9
    assert defaults.fields["qc"].time_seconds == 5400.0
    assert defaults.fields["qc"].horizontal_level_index == 0


def test_horizontal_qc_slice_uses_json_values_and_counts_non_finite(
    tmp_path: Path,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="qc",
        time_index=0,
        orientation="horizontal",
        level_index=0,
    )

    assert sliced.field.raw_field_name == "qc"
    assert sliced.selection.orientation == "horizontal"
    assert sliced.selection.selected_dimension == "zh"
    assert sliced.selection.level_units == "km"
    assert sliced.selection.level_coordinate_value == 0.4
    assert sliced.selection.level_meters == 400.0
    assert sliced.shape == [3, 4]
    assert sliced.dimension_order == ["yh", "xh"]
    assert sliced.data_encoding == "json"
    assert sliced.values[0][0] is None
    assert sliced.stats.non_finite_count == 1
    assert sliced.stats.finite_count == 11
    assert sliced.stats.max == 1.1e-05
    assert "native_grid_view_no_interpolation" in sliced.caveats


def test_vertical_qc_slices_have_stable_shape_and_order(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    vertical_x = field_slice(
        settings,
        result_id,
        field="qc",
        time_index=0,
        orientation="vertical_x",
        level_index=1,
    )
    vertical_y = field_slice(
        settings,
        result_id,
        field="qc",
        time_index=0,
        orientation="vertical_y",
        level_index=2,
    )

    assert vertical_x.selection.selected_dimension == "yh"
    assert vertical_x.shape == [2, 4]
    assert vertical_x.dimension_order == ["zh", "xh"]
    assert vertical_y.selection.selected_dimension == "xh"
    assert vertical_y.shape == [2, 3]
    assert vertical_y.dimension_order == ["zh", "yh"]


def test_temperature_slice_is_available_when_direct_temperature_exists(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="temperature",
        time_index=0,
        orientation="horizontal",
        level_index=1,
    )

    assert sliced.field.raw_field_name == "temperature"
    assert sliced.field.canonical_field_name == "temperature"
    assert sliced.field.units == "K"
    assert sliced.selection.selected_dimension == "zh"
    assert sliced.dimension_order == ["yh", "xh"]
    assert sliced.stats.min == 287.4
    assert sliced.stats.max == 289.6


def test_surface_rain_slice_is_horizontal_floor_map(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="rain",
        time_index=1,
        orientation="horizontal",
        level_index=0,
    )

    assert sliced.field.raw_field_name == "rain"
    assert sliced.field.native_grid == "surface/yh/xh"
    assert sliced.selection.selected_dimension == "surface"
    assert sliced.selection.level_coordinate_value == 0.0
    assert sliced.selection.level_units == "km"
    assert sliced.dimension_order == ["yh", "xh"]
    assert sliced.shape == [3, 4]
    assert sliced.stats.max == 5.75
    assert "surface_field_rendered_on_domain_floor" in sliced.caveats


def test_surface_rain_rejects_vertical_slice_orientation(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    with pytest.raises(VisualizationDataError, match="surface field.*horizontal slices"):
        field_slice(
            settings,
            result_id,
            field="rain",
            time_index=0,
            orientation="vertical_x",
            level_index=0,
        )


def test_w_slice_uses_native_zf_grid(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    sliced = field_slice(
        settings,
        result_id,
        field="w",
        time_index=1,
        orientation="horizontal",
        level_index=2,
    )

    assert sliced.field.raw_field_name == "w"
    assert sliced.field.native_grid == "zf/yh/xh"
    assert sliced.selection.selected_dimension == "zf"
    assert sliced.selection.time_seconds == 900.0
    assert sliced.selection.level_coordinate_value == 0.8
    assert sliced.selection.level_meters == 800.0
    assert sliced.shape == [3, 4]
    assert sliced.stats.min == 60.0
    assert sliced.stats.max == 71.0


def test_point_cloud_returns_qc_points_above_threshold(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    cloud = point_cloud(
        settings,
        result_id,
        field="qc",
        time_index=0,
        threshold=1e-6,
        max_points=50_000,
    )

    assert cloud.field.raw_field_name == "qc"
    assert cloud.field.canonical_field_name == "cloud_water"
    assert cloud.selection.threshold == 1e-6
    assert cloud.selection.time_seconds == 0.0
    assert cloud.point_order == ["x", "y", "z", "value"]
    assert cloud.coordinate_units == {"xh": "km", "yh": "km", "zh": "km"}
    assert cloud.coordinate_extents["xh"].min == 0.0
    assert cloud.coordinate_extents["xh"].max == 3.0
    assert cloud.coordinate_extents["yh"].min == 0.0
    assert cloud.coordinate_extents["yh"].max == 2.0
    assert cloud.coordinate_extents["zh"].min == 0.4
    assert cloud.coordinate_extents["zh"].max == 0.8
    assert cloud.stats.source_count == 23
    assert cloud.stats.returned_count == 23
    assert cloud.stats.field_finite_count == 23
    assert cloud.stats.field_non_finite_count == 1
    assert cloud.stats.field_min_value == 1e-6
    assert cloud.stats.field_max_value == 2.3e-05
    assert cloud.stats.downsampled is False
    assert cloud.stats.min_value == 1e-6
    assert cloud.stats.max_value == 2.3e-05
    assert cloud.stats.active_z_min == 0.4
    assert cloud.stats.active_z_max == 0.8
    assert cloud.stats.max_value_location == {"x": 3.0, "y": 2.0, "z": 0.8, "value": 2.3e-05}
    assert cloud.points[0] == [1.0, 0.0, 0.4, 1e-6]
    assert cloud.provenance.processing_method == "backend_xarray_native_grid_threshold"
    assert cloud.provenance.rendering_method == "thresholded_point_cloud"
    assert "native_grid_thresholded_point_cloud" in cloud.caveats


def test_point_cloud_returns_qr_points_when_rain_water_is_available(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path, include_qr=True)

    rain = point_cloud(
        settings,
        result_id,
        field="qr",
        time_index=0,
        threshold=5e-7,
        max_points=50_000,
    )

    assert rain.field.raw_field_name == "qr"
    assert rain.field.canonical_field_name == "rain_water"
    assert rain.selection.threshold == 5e-7
    assert rain.stats.source_count == 19
    assert rain.stats.returned_count == 19
    assert rain.stats.min_value == 5e-7
    assert rain.stats.max_value == 2.3e-06
    assert rain.provenance.provenance_label.startswith("CM1-derived rain water aloft point cloud")
    assert "visualizer_interpretation_of_cm1_qr" in rain.caveats


def test_point_cloud_rejects_potential_temperature_for_now(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    with pytest.raises(VisualizationDataError, match="2-D slices but not 3-D point-cloud"):
        point_cloud(
            settings,
            result_id,
            field="theta",
            time_index=0,
            threshold=0,
            max_points=50_000,
        )


@pytest.mark.parametrize(
    ("field_name", "canonical_name", "threshold", "expected_count"),
    [
        ("qv", "water_vapor", 0.0, 24),
        ("dbz", "reflectivity", 0.0, 14),
        ("rain", "accumulated_surface_rain", 0.0, 12),
    ],
)
def test_point_cloud_returns_additional_scalar_fields(
    tmp_path: Path,
    field_name: str,
    canonical_name: str,
    threshold: float,
    expected_count: int,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    scalar = point_cloud(
        settings,
        result_id,
        field=field_name,
        time_index=0,
        threshold=threshold,
        max_points=50_000,
    )

    assert scalar.field.raw_field_name == field_name
    assert scalar.field.canonical_field_name == canonical_name
    assert scalar.stats.source_count == expected_count
    assert scalar.stats.returned_count == expected_count
    assert scalar.stats.field_finite_count > 0
    assert scalar.stats.field_max_value is not None
    assert f"visualizer_interpretation_of_cm1_{field_name}" in scalar.caveats
    if field_name == "dbz":
        assert scalar.stats.field_min_value == -10.0
        assert scalar.stats.field_max_value == 13.0
    if field_name == "rain":
        assert scalar.stats.active_z_min == 0.0
        assert scalar.stats.active_z_max == 0.0
        assert "surface_field_rendered_on_domain_floor" in scalar.caveats


def test_view_defaults_choose_native_grid_max_locations(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    defaults = view_defaults(settings, result_id)

    assert defaults.preferred_field == "qc"
    assert defaults.fields["qc"].source == "max_qc_native_grid_location"
    assert defaults.fields["qc"].time_index == 1
    assert defaults.fields["qc"].time_seconds == 900.0
    assert defaults.fields["qc"].horizontal_level_index == 1
    assert defaults.fields["qc"].vertical_x_index == 2
    assert defaults.fields["qc"].vertical_y_index == 2
    assert defaults.fields["qc"].max_value == 4.6e-05
    assert defaults.fields["w"].source == "max_w_native_grid_location"
    assert defaults.fields["w"].time_index == 1
    assert defaults.fields["w"].horizontal_level_index == 2
    assert defaults.fields["w"].vertical_x_index == 2
    assert defaults.fields["w"].vertical_y_index == 3
    assert defaults.fields["theta"].source == "max_theta_native_grid_location"
    assert defaults.fields["theta"].horizontal_level_index == 1
    assert defaults.fields["temperature"].source == "max_temperature_native_grid_location"
    assert defaults.fields["qv"].source == "max_qv_native_grid_location"
    assert defaults.fields["dbz"].source == "max_dbz_native_grid_location"
    assert defaults.fields["rain"].source == "domain_center_missing_required_dimensions"
    assert "default_locations_are_native_grid_indices" in defaults.caveats
    assert defaults.provenance.processing_method == "backend_xarray_interesting_view_defaults"


def test_deep_convection_view_defaults_prefer_updraft_field(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(
        tmp_path,
        run_id="run-deep-visualization",
        package_updates={
            "run_recipe": "observed_surface_forced_evolution",
            "run_recipe_display_name": "Observed Surface-Forced Evolution",
            "candidate_screening": {
                "primary_story": "supercell_environment",
                "active_story": "supercell_environment",
                "story_scores": [
                    {"story": "supercell_environment", "support": "supported"},
                ],
            },
        },
    )

    defaults = view_defaults(settings, result_id)

    assert defaults.preferred_field == "w"
    assert defaults.fields["w"].source == "max_w_native_grid_location"
    assert defaults.fields["qc"].source == "max_qc_native_grid_location"


def test_view_defaults_can_choose_selected_time_max_locations(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    defaults = view_defaults(settings, result_id, time_index=0)

    assert defaults.fields["qc"].source == "selected_time_max_qc_native_grid_location"
    assert defaults.fields["qc"].time_index == 0
    assert defaults.fields["qc"].time_seconds == 0.0
    assert defaults.fields["qc"].selected_time_index == 0
    assert defaults.fields["qc"].selected_time_seconds == 0.0
    assert defaults.fields["qc"].horizontal_level_index == 1
    assert defaults.fields["qc"].vertical_x_index == 2
    assert defaults.fields["qc"].vertical_y_index == 3
    assert defaults.fields["qc"].max_value == 2.3e-05
    assert defaults.fields["w"].source == "selected_time_max_w_native_grid_location"
    assert defaults.fields["w"].time_index == 0
    assert defaults.fields["w"].horizontal_level_index == 2
    assert defaults.fields["w"].vertical_x_index == 2
    assert defaults.fields["w"].vertical_y_index == 3
    assert defaults.fields["w"].max_value == 35.0
    assert "default_locations_are_selected_time_native_grid_indices" in defaults.caveats


def test_point_cloud_reports_no_points_above_threshold(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    cloud = point_cloud(
        settings,
        result_id,
        field="qc",
        time_index=0,
        threshold=1.0,
        max_points=50_000,
    )

    assert cloud.points == []
    assert cloud.stats.source_count == 0
    assert cloud.stats.returned_count == 0
    assert cloud.stats.field_finite_count == 23
    assert cloud.stats.field_max_value == 2.3e-05
    assert cloud.stats.min_value is None
    assert cloud.stats.max_value is None


def test_point_cloud_missing_field_reports_clear_error(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(
        tmp_path,
        include_qc=False,
        include_w=True,
    )

    with pytest.raises(VisualizationDataError, match="Field is not available.*qc"):
        point_cloud(
            settings,
            result_id,
            field="qc",
            time_index=0,
            threshold=1e-6,
            max_points=50_000,
        )


def test_point_cloud_rejects_signed_flow_fields_for_now(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    with pytest.raises(VisualizationDataError, match="signed-flow 3-D rendering"):
        point_cloud(
            settings,
            result_id,
            field="w",
            time_index=0,
            threshold=0,
            max_points=50_000,
        )


@pytest.mark.parametrize(
    ("time_index", "threshold", "max_points", "message"),
    [
        (8, 1e-6, 50_000, "time_index"),
        (0, -1.0, 50_000, "threshold"),
        (0, float("nan"), 50_000, "threshold"),
        (0, 1e-6, 0, "max_points"),
    ],
)
def test_point_cloud_validates_query_values(
    tmp_path: Path,
    time_index: int,
    threshold: float,
    max_points: int,
    message: str,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    with pytest.raises(VisualizationDataError, match=message):
        point_cloud(
            settings,
            result_id,
            field="qc",
            time_index=time_index,
            threshold=threshold,
            max_points=max_points,
        )


def test_point_cloud_uses_deterministic_stride_downsampling(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)

    cloud = point_cloud(
        settings,
        result_id,
        field="qc",
        time_index=0,
        threshold=1e-6,
        max_points=5,
    )

    assert cloud.stats.source_count == 23
    assert cloud.stats.returned_count == 5
    assert cloud.stats.downsampled is True
    assert cloud.stats.downsample_stride == 5
    assert [point[3] for point in cloud.points] == [1e-6, 6e-6, 1.1e-05, 1.6e-05, 2.1e-05]
    assert "deterministic_stride_downsampling_applied" in cloud.caveats


def test_point_cloud_endpoint_returns_payload_and_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))
    client = TestClient(app)

    ok = client.get(
        f"/api/results/{result_id}/visualization/point-cloud",
        params={"field": "qc", "time_index": 0, "threshold": 1e-6, "max_points": 5},
    )
    bad = client.get(
        f"/api/results/{result_id}/visualization/point-cloud",
        params={"field": "w", "time_index": 0, "threshold": 1e-6, "max_points": 5},
    )

    assert ok.status_code == 200
    assert ok.json()["stats"]["downsampled"] is True
    assert ok.json()["provenance"]["rendering_method"] == "thresholded_point_cloud"
    assert bad.status_code == 400
    assert "signed-flow 3-D rendering" in bad.json()["detail"]


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            {"field": "bad", "time_index": 0, "orientation": "horizontal", "level_index": 0},
            "Unsupported",
        ),
        (
            {"field": "qc", "time_index": 8, "orientation": "horizontal", "level_index": 0},
            "time_index",
        ),
        (
            {"field": "qc", "time_index": 0, "orientation": "horizontal", "level_index": 8},
            "level_index",
        ),
    ],
)
def test_slice_endpoint_reports_clear_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    query: dict[str, str | int],
    message: str,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))

    response = TestClient(app).get(
        f"/api/results/{result_id}/visualization/slice",
        params=query,
    )

    assert response.status_code == 400
    assert message in response.json()["detail"]


def test_visualization_api_returns_field_catalog_and_slice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))
    client = TestClient(app)

    catalog = client.get(f"/api/results/{result_id}/visualization/fields")
    defaults = client.get(
        f"/api/results/{result_id}/visualization/defaults",
        params={"time_index": 0},
    )
    sliced = client.get(
        f"/api/results/{result_id}/visualization/slice",
        params={
            "field": "qc",
            "time_index": 0,
            "orientation": "horizontal",
            "level_index": 0,
            "encoding": "json",
        },
    )

    assert catalog.status_code == 200
    assert catalog.json()["available_fields"][0]["provenance"]["source_model"] == "CM1"
    assert defaults.status_code == 200
    assert defaults.json()["fields"]["qc"]["source"] == "selected_time_max_qc_native_grid_location"
    assert defaults.json()["fields"]["w"]["source"] == "selected_time_max_w_native_grid_location"
    assert sliced.status_code == 200
    payload = sliced.json()
    assert payload["field"]["canonical_field_name"] == "cloud_water"
    assert payload["shape"] == [3, 4]
    assert payload["dimension_order"] == ["yh", "xh"]
    assert payload["stats"]["finite_count"] == 11
    assert payload["stats"]["non_finite_count"] == 1


def test_output_product_api_returns_profile_time_height_and_time_series(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, result_id, _run_dir = create_visualization_result(tmp_path)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))
    client = TestClient(app)

    catalog = client.get(f"/api/results/{result_id}/output-products")
    profile = client.get(
        f"/api/results/{result_id}/output-products/profile",
        params={"field": "qv", "time_index": 0, "aggregation_method": "domain_mean"},
    )
    time_height = client.get(
        f"/api/results/{result_id}/output-products/time-height",
        params={"field": "w", "aggregation_method": "domain_max"},
    )
    time_series = client.get(
        f"/api/results/{result_id}/output-products/time-series",
        params={"field": "rain", "aggregation_method": "domain_max"},
    )
    bad_profile = client.get(
        f"/api/results/{result_id}/output-products/profile",
        params={"field": "rain", "time_index": 0, "aggregation_method": "domain_mean"},
    )

    assert catalog.status_code == 200
    assert any(
        product["product_key"] == "profile:qv"
        for product in catalog.json()["available_profile_products"]
    )
    assert catalog.json()["unavailable_products"][0]["product_key"] == (
        "boundary_layer_depth_time_series"
    )
    assert profile.status_code == 200
    assert profile.json()["values"] == pytest.approx([0.010055, 0.010175])
    assert profile.json()["field_quality"]["assessed"] is False
    assert profile.json()["field_quality"]["reason"] == "field_quality_not_tracked_for_field"
    assert time_height.status_code == 200
    assert time_height.json()["shape"] == [2, 3]
    assert time_height.json()["values"][0] == pytest.approx([11.0, 23.0, 35.0])
    assert time_height.json()["values"][1] == pytest.approx([47.0, 59.0, 71.0])
    assert time_height.json()["field_quality"]["assessed"] is True
    assert time_height.json()["field_quality"]["quality_state"] == "trusted"
    assert time_series.status_code == 200
    assert time_series.json()["values"] == pytest.approx([2.75, 5.75])
    assert time_series.json()["field_quality"]["assessed"] is True
    assert time_series.json()["field_quality"]["quality_state"] == "trusted"
    assert bad_profile.status_code == 400
    assert "not profile-capable" in bad_profile.json()["detail"]

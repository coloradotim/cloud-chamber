import json
from pathlib import Path

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
    point_cloud,
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
    run_id: str = "run-visualization",
) -> tuple[CloudChamberSettings, str, Path]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id=run_id,
        run_size_preset="quick_look",
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    write_visualization_netcdf(netcdf_path, include_qc=include_qc, include_w=include_w)
    manifest = load_run_manifest(package.manifest_path)
    write_run_manifest(
        package.manifest_path,
        manifest.model_copy(
            update={
                "lifecycle_state": LifecycleState.COMPLETED,
                "provenance": ProvenanceMetadata(product_state=ProductState.COMPLETED_CM1_RESULT),
                "outputs": OutputMetadata(netcdf_paths=[str(netcdf_path)]),
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
) -> None:
    data_vars = {}
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
    data_vars["theta"] = (
        ("time", "zh", "yh", "xh"),
        np.zeros((2, 2, 3, 4), dtype=float),
        {"units": "K"},
    )
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": ("time", [0.0, 900.0], {"units": "s"}),
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
    assert catalog.provenance.source_model == "CM1"
    assert "native-grid view" in catalog.provenance.provenance_label


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
    assert cloud.stats.source_count == 23
    assert cloud.stats.returned_count == 23
    assert cloud.stats.downsampled is False
    assert cloud.stats.min_value == 1e-6
    assert cloud.stats.max_value == 2.3e-05
    assert cloud.points[0] == [1.0, 0.0, 0.4, 1e-6]
    assert cloud.provenance.processing_method == "backend_xarray_native_grid_threshold"
    assert cloud.provenance.rendering_method == "thresholded_point_cloud"
    assert "native_grid_thresholded_point_cloud" in cloud.caveats


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
    assert cloud.stats.min_value is None
    assert cloud.stats.max_value is None


def test_point_cloud_missing_qc_reports_clear_error(tmp_path: Path) -> None:
    settings, result_id, _run_dir = create_visualization_result(
        tmp_path,
        include_qc=False,
        include_w=True,
    )

    with pytest.raises(VisualizationDataError, match="qc is not available"):
        point_cloud(
            settings,
            result_id,
            field="qc",
            time_index=0,
            threshold=1e-6,
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
    assert "Only field=qc" in bad.json()["detail"]


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
    assert sliced.status_code == 200
    payload = sliced.json()
    assert payload["field"]["canonical_field_name"] == "cloud_water"
    assert payload["shape"] == [3, 4]
    assert payload["dimension_order"] == ["yh", "xh"]
    assert payload["stats"]["finite_count"] == 11
    assert payload["stats"]["non_finite_count"] == 1

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
from cloud_chamber.selected_region_diagnostics import (
    SelectedRegionError,
    SelectedRegionRequest,
    selected_region_diagnostics,
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


def create_region_result(
    tmp_path: Path,
    *,
    include_qc: bool = True,
    include_w: bool = True,
    include_qr: bool = True,
    run_id: str = "run-region",
) -> tuple[CloudChamberSettings, str]:
    settings = fake_settings(tmp_path)
    package = generate_dry_run_package(
        scenario_data=json.loads(BASELINE_TEMPLATE.read_text()),
        runtime_home=settings.runtime_home,
        run_id=run_id,
    )
    netcdf_path = package.package_dir / "cm1out_000001.nc"
    write_region_netcdf(
        netcdf_path,
        include_qc=include_qc,
        include_w=include_w,
        include_qr=include_qr,
    )
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
    return settings, result.result_id


def write_region_netcdf(
    path: Path,
    *,
    include_qc: bool,
    include_w: bool,
    include_qr: bool,
) -> None:
    data_vars = {}
    if include_qc:
        qc = np.zeros((3, 3, 3, 4), dtype=float)
        qc[1, 1, 1, 2] = 2e-6
        qc[2, 2, 1, 2] = 5e-6
        qc[2, 1, 0, 0] = np.inf
        data_vars["qc"] = (("time", "zh", "yh", "xh"), qc, {"units": "kg/kg"})
    if include_w:
        w = np.zeros((3, 3, 3, 4), dtype=float)
        w[0, 1, 1, 2] = 0.4
        w[1, 1, 1, 2] = 1.8
        w[2, 2, 1, 2] = 2.4
        w[2, 0, 0, 0] = -0.7
        data_vars["w"] = (("time", "zf", "yh", "xh"), w, {"units": "m/s"})
    if include_qr:
        qr = np.zeros((3, 3, 3, 4), dtype=float)
        qr[2, 1, 1, 2] = 2e-7
        data_vars["qr"] = (("time", "zh", "yh", "xh"), qr, {"units": "kg/kg"})
    xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": ("time", [0.0, 900.0, 1800.0], {"units": "s"}),
            "zh": ("zh", [0.4, 0.8, 1.2], {"units": "km"}),
            "zf": ("zf", [0.0, 0.8, 1.6], {"units": "km"}),
            "yh": ("yh", [0.0, 1.0, 2.0], {"units": "km"}),
            "xh": ("xh", [0.0, 1.0, 2.0, 3.0], {"units": "km"}),
        },
    ).to_netcdf(path, engine="scipy")


def test_point_region_reports_local_cloud_updraft_rain_and_comparison(tmp_path: Path) -> None:
    settings, result_id = create_region_result(tmp_path)

    payload = selected_region_diagnostics(
        settings,
        result_id,
        SelectedRegionRequest(region_type="point", x_index=2, y_index=1, z_index=1),
    )

    assert payload.region.region_type == "point"
    assert payload.region.cell_count == 1
    assert payload.region.x is not None
    assert payload.region.x.start_coordinate == 2.0
    assert payload.diagnostics.local_max_w_m_s == 1.8
    assert payload.diagnostics.local_min_w_m_s == 0.0
    assert payload.diagnostics.local_max_qc_kg_kg == 2e-6
    assert payload.diagnostics.first_local_cloud_time_seconds == 900.0
    assert payload.diagnostics.local_cloud_fraction_time_series[1].value == 1.0
    assert payload.diagnostics.local_rain_present is True
    assert payload.diagnostics.first_local_rain_time_seconds == 1800.0
    assert payload.comparison_to_domain.local_max_w_fraction_of_domain == pytest.approx(0.75)
    assert payload.interpretation.thermal_fate_label in {
        "Brief / diluted cloud",
        "Fair-weather cumulus",
    }
    assert payload.provenance.processing_method == "backend_xarray_selected_region_diagnostics"
    assert "native_grid_region_summary_no_interpolation" in payload.caveats


def test_column_region_uses_vertical_extent_and_detects_growth(tmp_path: Path) -> None:
    settings, result_id = create_region_result(tmp_path)

    payload = selected_region_diagnostics(
        settings,
        result_id,
        SelectedRegionRequest(region_type="column", x_index=2, y_index=1),
    )

    assert payload.region.vertical is not None
    assert payload.region.vertical.start_index == 0
    assert payload.region.vertical.end_index == 2
    assert payload.diagnostics.local_max_w_m_s == 2.4
    assert payload.diagnostics.local_max_qc_kg_kg == 5e-6
    assert payload.diagnostics.local_cloud_top_time_series[-1].value == 1200.0
    assert payload.diagnostics.local_max_w_height_time_series[-1].value == 1600.0
    assert payload.interpretation.thermal_fate_label == "Growing cumulus"


def test_box_region_summarizes_bounded_area(tmp_path: Path) -> None:
    settings, result_id = create_region_result(tmp_path)

    payload = selected_region_diagnostics(
        settings,
        result_id,
        SelectedRegionRequest(
            region_type="box",
            x_start=1,
            x_end=2,
            y_start=1,
            y_end=1,
            z_start=1,
            z_end=2,
        ),
    )

    assert payload.region.cell_count == 4
    assert payload.region.x is not None
    assert payload.region.x.end_coordinate == 2.0
    assert len(payload.diagnostics.local_qc_max_time_series) == 3
    assert payload.diagnostics.local_qc_max_time_series[-1].value == 5e-6


def test_thermal_without_cloud_selected_region(tmp_path: Path) -> None:
    settings, result_id = create_region_result(tmp_path)

    payload = selected_region_diagnostics(
        settings,
        result_id,
        SelectedRegionRequest(region_type="column", x_index=0, y_index=0),
    )

    assert payload.diagnostics.first_local_cloud_time_seconds is None
    assert payload.diagnostics.local_max_w_m_s == 0.0
    assert payload.diagnostics.local_min_w_m_s == -0.7
    assert payload.interpretation.thermal_fate_label == "No meaningful thermal"


def test_missing_fields_return_caveats_without_crashing(tmp_path: Path) -> None:
    settings, result_id = create_region_result(
        tmp_path,
        include_qc=False,
        include_w=True,
        include_qr=False,
    )

    payload = selected_region_diagnostics(
        settings,
        result_id,
        SelectedRegionRequest(region_type="column", x_index=2, y_index=1),
    )

    assert payload.diagnostics.available is False
    assert payload.diagnostics.local_max_w_m_s == 2.4
    assert payload.interpretation.confidence == "unsupported_missing_fields"
    assert "missing_qc_field" in payload.caveats


def test_out_of_bounds_region_is_rejected(tmp_path: Path) -> None:
    settings, result_id = create_region_result(tmp_path)

    with pytest.raises(SelectedRegionError, match="x_index=99"):
        selected_region_diagnostics(
            settings,
            result_id,
            SelectedRegionRequest(region_type="column", x_index=99, y_index=1),
        )


def test_selected_region_api_payload_and_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, result_id = create_region_result(tmp_path)
    monkeypatch.setenv("CLOUD_CHAMBER_RUNTIME_HOME", str(settings.runtime_home))
    client = TestClient(app)

    ok = client.get(
        f"/api/results/{result_id}/diagnostics/selected-region",
        params={"region_type": "column", "x_index": 2, "y_index": 1},
    )
    bad = client.get(
        f"/api/results/{result_id}/diagnostics/selected-region",
        params={"region_type": "column", "x_index": 99, "y_index": 1},
    )

    assert ok.status_code == 200
    assert ok.json()["diagnostics"]["local_max_w_m_s"] == 2.4
    assert ok.json()["provenance"]["provenance_label"].startswith("CM1-derived")
    assert bad.status_code == 400
    assert "x_index=99" in bad.json()["detail"]

import json
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    PRESERVED_CASE_ID,
    PRESERVED_RUN_ID,
    StormExaminationError,
    preserved_storm_examination_frame,
)


def _settings(runtime_home: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def _write_retained_fixture(runtime_home: Path) -> Path:
    run_dir = runtime_home / "runs" / PRESERVED_RUN_ID
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"run_id": PRESERVED_RUN_ID, "lifecycle_state": "completed"})
    )
    (run_dir / "case_manifest.json").write_text(
        json.dumps({"run_id": PRESERVED_RUN_ID, "case_id": PRESERVED_CASE_ID})
    )
    x = np.asarray([-60.0, -30.0, 0.0, 30.0, 60.0], dtype=np.float32)
    y = np.asarray([-60.0, -30.0, 0.0, 30.0, 60.0], dtype=np.float32)
    z = np.asarray([0.25, 1.25, 3.25, 10.25, 15.25], dtype=np.float32)
    shape = (1, len(z), len(y), len(x))
    for number, time_seconds in enumerate(range(0, 7_201, 900), start=1):
        w = np.zeros(shape, dtype=np.float32)
        w[0, 3, 2, 2] = 40 + number
        w[0, 1, 1, 1] = -6
        w[0, 1, 2, 2] = 8
        zvort = np.zeros(shape, dtype=np.float32)
        zvort[0, 2, 2, 2] = 0.015
        dbz = np.full(shape, -10.0, dtype=np.float32)
        dbz[0, :, 1:4, 1:4] = 45
        qc = np.zeros(shape, dtype=np.float32)
        qr = np.zeros(shape, dtype=np.float32)
        qi = np.zeros(shape, dtype=np.float32)
        qs = np.zeros(shape, dtype=np.float32)
        qg = np.zeros(shape, dtype=np.float32)
        qc[0, 3, 2, 2] = 0.002
        qr[0, 1, 1, 1] = 0.003
        qi[0, 4, 2, 2] = 0.001
        qs[0, 3, 3, 3] = 0.0015
        qg[0, 2, 2, 2] = 0.004
        surface = np.zeros((1, len(y), len(x)), dtype=np.float32)
        surface[0, 2, 2] = number
        u = np.full(shape, 12.0, dtype=np.float32)
        v = np.full(shape, -4.0, dtype=np.float32)
        dataset = xr.Dataset(
            data_vars={
                "winterp": (("time", "zh", "yh", "xh"), w, {"units": "m/s"}),
                "zvort": (("time", "zh", "yh", "xh"), zvort, {"units": "1/s"}),
                "dbz": (("time", "zh", "yh", "xh"), dbz, {"units": "dBZ"}),
                "qc": (("time", "zh", "yh", "xh"), qc, {"units": "kg/kg"}),
                "qr": (("time", "zh", "yh", "xh"), qr, {"units": "kg/kg"}),
                "qi": (("time", "zh", "yh", "xh"), qi, {"units": "kg/kg"}),
                "qs": (("time", "zh", "yh", "xh"), qs, {"units": "kg/kg"}),
                "qg": (("time", "zh", "yh", "xh"), qg, {"units": "kg/kg"}),
                "uinterp": (("time", "zh", "yh", "xh"), u, {"units": "m/s"}),
                "vinterp": (("time", "zh", "yh", "xh"), v, {"units": "m/s"}),
                "uh": (("time", "yh", "xh"), surface * 100, {"units": "m2/s2"}),
                "rain": (("time", "yh", "xh"), surface, {"units": "cm"}),
            },
            coords={
                "time": (
                    "time",
                    np.asarray([time_seconds], dtype=np.float32),
                    {"units": "seconds"},
                ),
                "xh": ("xh", x, {"units": "km"}),
                "yh": ("yh", y, {"units": "km"}),
                "zh": ("zh", z, {"units": "km"}),
            },
        )
        dataset.to_netcdf(run_dir / f"cm1out_{number:06d}.nc")
    return run_dir


def test_rotating_updraft_returns_coordinated_native_slices(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path)

    frame = preserved_storm_examination_frame(
        _settings(tmp_path), lens="rotating_updraft", time_index=5, viewport="storm"
    )

    assert frame.run_id == PRESERVED_RUN_ID
    assert frame.time_seconds == 4_500
    assert frame.plan.level_km == pytest.approx(3.25)
    assert frame.plan.primary.key == "winterp"
    assert frame.plan.primary.evidence_kind == "native"
    assert frame.plan.x_indices == [1, 2, 3]
    assert frame.plan.y_indices == [1, 2, 3]
    assert np.asarray(frame.plan.primary.values).shape == (3, 3)
    assert frame.plan.overlays["vertical_vorticity"].units == "s^-1"
    assert frame.xz_section.cross_section_coordinate_km == pytest.approx(0)
    assert frame.yz_section.cross_section_coordinate_km == pytest.approx(0)
    assert frame.xz_section.horizontal_indices == [1, 2, 3]
    assert frame.yz_section.horizontal_indices == [1, 2, 3]
    assert frame.primary_updraft.w_m_s == pytest.approx(46)
    assert all("tmp" not in value for value in frame.provenance.values())


def test_cloud_and_precipitation_labels_derived_hydrometeor_grouping(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path)

    frame = preserved_storm_examination_frame(
        _settings(tmp_path), lens="cloud_precipitation", time_index=8, viewport="full"
    )

    assert frame.plan.categories is not None
    assert frame.plan.x_indices == [0, 1, 2, 3, 4]
    assert frame.plan.y_indices == [0, 1, 2, 3, 4]
    assert frame.plan.categories.evidence_kind == "derived"
    assert frame.plan.categories.source_fields == ["qc", "qr", "qi", "qs", "qg"]
    assert "max total-condensate level" in frame.plan.categories.derivation
    assert frame.plan.primary.units == "g/kg"
    assert frame.xz_section.categories is not None
    assert frame.xz_section.overlays["reflectivity"].evidence_kind == "native"
    assert frame.selected_point.values["total_condensate"] == pytest.approx(2)
    assert frame.selected_point.evidence_kind["total_condensate"] == "derived"


def test_low_level_view_combines_motion_rain_and_model_relative_flow(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path)

    frame = preserved_storm_examination_frame(
        _settings(tmp_path),
        lens="low_level_interactions",
        time_index=5,
        viewport="storm",
        x_index=1,
        y_index=1,
        z_index=1,
    )

    assert frame.plan.level_km == pytest.approx(1.25)
    assert frame.plan.primary.selected_frame_minimum == pytest.approx(-6)
    assert frame.plan.primary.selected_frame_maximum == pytest.approx(8)
    assert frame.plan.wind_vectors[0].u_m_s == pytest.approx(12)
    assert frame.plan.wind_vectors[0].v_m_s == pytest.approx(-4)
    assert frame.plan.overlays["accumulated_surface_rain"].units == "mm"
    assert "multiplied by 10" in (frame.plan.overlays["accumulated_surface_rain"].derivation or "")
    assert frame.selected_point.states[0] == "Descending"
    assert frame.selected_point.coordinate_frame.startswith("translating model frame")


def test_retained_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    run_dir = _write_retained_fixture(tmp_path)
    (run_dir / "case_manifest.json").write_text(json.dumps({"case_id": "not-approved"}))

    with pytest.raises(StormExaminationError, match="case identity"):
        preserved_storm_examination_frame(_settings(tmp_path))

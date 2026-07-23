import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import xarray as xr

from cloud_chamber import storm_examination
from cloud_chamber.settings import CloudChamberSettings
from cloud_chamber.storm_examination import (
    PRESENTATION_CASE_ID,
    PRESENTATION_EVIDENCE_FILENAME,
    PRESENTATION_RUN_ID,
    PRESENTATION_TIMES_SECONDS,
    PRESERVED_CASE_ID,
    PRESERVED_RUN_ID,
    StormExaminationError,
    preserved_storm_examination_frame,
    storm_examination_inventory,
    supercells_explore_frame,
)


def _settings(runtime_home: Path) -> CloudChamberSettings:
    return CloudChamberSettings(
        runtime_home=runtime_home,
        cm1_root=None,
        cm1_run_dir=None,
        cache_dir=runtime_home / "cache",
        log_dir=runtime_home / "logs",
    )


def _write_retained_fixture(
    runtime_home: Path,
    *,
    presentation: bool = False,
) -> Path:
    run_id = PRESENTATION_RUN_ID if presentation else PRESERVED_RUN_ID
    case_id = PRESENTATION_CASE_ID if presentation else PRESERVED_CASE_ID
    times = PRESENTATION_TIMES_SECONDS if presentation else tuple(range(0, 7_201, 900))
    implementation_commit = "presentation-test-commit"
    run_dir = runtime_home / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"run_id": run_id, "lifecycle_state": "completed"})
    )
    (run_dir / "case_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "case_id": case_id,
                "implementation_commit": implementation_commit,
            }
        )
    )
    x = np.asarray([-60.0, -30.0, 0.0, 30.0, 60.0], dtype=np.float32)
    y = np.asarray([-60.0, -30.0, 0.0, 30.0, 60.0], dtype=np.float32)
    z = np.asarray([0.25, 1.25, 3.25, 10.25, 15.25], dtype=np.float32)
    shape = (1, len(z), len(y), len(x))
    history_inventory = []
    for number, time_seconds in enumerate(times, start=1):
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
        u = np.full(shape, 5.0, dtype=np.float32)
        v = np.full(shape, -1.0, dtype=np.float32)
        u[0, 1] = 12.0
        v[0, 1] = -4.0
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
        history_path = run_dir / f"cm1out_{number:06d}.nc"
        dataset.to_netcdf(history_path)
        history_inventory.append(
            {
                "filename": history_path.name,
                "time_seconds": time_seconds,
                "bytes": history_path.stat().st_size,
                "sha256": "fixture-does-not-reverify-content-hash",
            }
        )
    if presentation:
        (run_dir / PRESENTATION_EVIDENCE_FILENAME).write_text(
            json.dumps(
                {
                    "evidence_version": "supercell_presentation_run_evidence_v1",
                    "kind": "final",
                    "run_id": run_id,
                    "case_id": case_id,
                    "source_run_id": PRESERVED_RUN_ID,
                    "implementation_commit": implementation_commit,
                    "grid": {
                        "dx_m": 500.0,
                        "dy_m": 500.0,
                        "dz_m": 20_000.0 / 60.0,
                        "nx": 240,
                        "ny": 240,
                        "nz": 60,
                    },
                    "duration_seconds": 10_800,
                    "output_cadence_seconds": 120,
                    "required_fields": sorted(storm_examination.PRESENTATION_REQUIRED_FIELDS),
                    "normal_completion": True,
                    "times_seconds": list(times),
                    "history_count": len(times),
                    "history_inventory": history_inventory,
                }
            )
        )
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
    assert frame.plan.x_indices == [1, 2]
    assert frame.plan.y_indices == [1, 2]
    assert np.asarray(frame.plan.primary.values).shape == (2, 2)
    assert frame.plan.overlays["vertical_vorticity"].units == "s^-1"
    assert frame.plan.overlays["total_condensate"].units == "g/kg"
    assert frame.xz_section.overlays["vertical_vorticity"].units == "s^-1"
    assert frame.xz_section.cross_section_coordinate_km == pytest.approx(0)
    assert frame.yz_section.cross_section_coordinate_km == pytest.approx(0)
    assert frame.xz_section.horizontal_indices == [1, 2]
    assert frame.yz_section.horizontal_indices == [1, 2]
    assert frame.primary_updraft.w_m_s == pytest.approx(46)
    assert "combine rising motion" in frame.what_to_notice_now
    assert frame.what_to_notice_by_view is not None
    assert "this xz section intersects" in frame.what_to_notice_by_view["xz"]
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
    assert frame.plan.selection_z_indices is not None
    assert frame.plan.selection_z_indices[2][2] == 2
    assert frame.plan.primary.units == "g/kg"
    assert frame.plan.overlays["vertical_velocity"].evidence_kind == "derived"
    assert "sampled at each x/y cell's level" in (
        frame.plan.overlays["vertical_velocity"].derivation or ""
    )
    assert frame.xz_section.categories is not None
    assert frame.xz_section.overlays["reflectivity"].evidence_kind == "native"
    assert frame.selected_point.values["total_condensate"] == pytest.approx(2)
    assert frame.selected_point.evidence_kind["total_condensate"] == "derived"
    assert frame.what_to_notice_by_view is not None
    assert "responsible for that category" in frame.what_to_notice_by_view["plan"]
    assert "this yz section" in frame.what_to_notice_by_view["yz"]


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
    assert frame.what_to_notice_by_view is not None
    assert "historical rain footprint" in frame.what_to_notice_by_view["plan"]
    assert "current precipitating condensate" in frame.what_to_notice_by_view["xz"]


def test_storm_viewport_is_fixed_across_saved_outputs(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path, presentation=True)
    settings = _settings(tmp_path)

    first = supercells_explore_frame(settings, time_index=0, viewport="storm")
    last = supercells_explore_frame(settings, time_index=90, viewport="storm")

    assert first.viewport_bounds_km == last.viewport_bounds_km
    assert first.viewport_bounds_km == {
        "x_min": -40.0,
        "x_max": 40.0,
        "y_min": -45.0,
        "y_max": 35.0,
    }
    assert any("fixed inspection window" in caveat for caveat in first.caveats)


def test_retained_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    run_dir = _write_retained_fixture(tmp_path)
    (run_dir / "case_manifest.json").write_text(json.dumps({"case_id": "not-approved"}))

    with pytest.raises(StormExaminationError, match="case identity"):
        preserved_storm_examination_frame(_settings(tmp_path))


def test_presentation_evidence_mismatch_fails_closed(tmp_path: Path) -> None:
    run_dir = _write_retained_fixture(tmp_path, presentation=True)
    evidence_path = run_dir / PRESENTATION_EVIDENCE_FILENAME
    evidence = json.loads(evidence_path.read_text())
    evidence["history_count"] = 90
    evidence_path.write_text(json.dumps(evidence))

    with pytest.raises(StormExaminationError, match="validation evidence is not accepted"):
        storm_examination_inventory(_settings(tmp_path))


def test_presentation_inventory_uses_promotion_evidence_then_reads_selected_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_retained_fixture(tmp_path, presentation=True)
    original_open_dataset = xr.open_dataset
    opened: list[str] = []

    def counted_open_dataset(filename_or_obj: str | Path, **kwargs: Any) -> xr.Dataset:
        opened.append(Path(filename_or_obj).name)
        return original_open_dataset(filename_or_obj, **kwargs)

    monkeypatch.setattr(
        "cloud_chamber.storm_examination.xr.open_dataset",
        counted_open_dataset,
    )
    inventory = storm_examination_inventory(_settings(tmp_path))

    assert len(inventory) == 91
    assert opened == []

    supercells_explore_frame(
        _settings(tmp_path),
        lens="rotating_updraft",
        time_index=37,
        viewport="storm",
    )

    assert opened == ["cm1out_000038.nc"]


def test_presentation_inventory_cache_invalidates_when_history_is_removed(
    tmp_path: Path,
) -> None:
    run_dir = _write_retained_fixture(tmp_path, presentation=True)
    settings = _settings(tmp_path)

    assert len(storm_examination_inventory(settings)) == 91
    (run_dir / "cm1out_000038.nc").unlink()

    with pytest.raises(StormExaminationError, match="presentation output is unavailable"):
        storm_examination_inventory(settings)


def test_product_frame_adds_bounded_volume_layers_without_changing_science_path(
    tmp_path: Path,
) -> None:
    _write_retained_fixture(tmp_path, presentation=True)

    frame = supercells_explore_frame(
        _settings(tmp_path), lens="rotating_updraft", time_index=5, viewport="storm"
    )

    assert frame.schema_version == "supercells_explore_v1"
    assert frame.authority_state == "supercells_product_world"
    assert frame.world_id == "supercells"
    assert frame.simulation_id == "supercells_quarter_circle_reference"
    assert frame.run_id == PRESENTATION_RUN_ID
    assert frame.case_id == PRESENTATION_CASE_ID
    assert len(frame.times_seconds) == 91
    assert frame.times_seconds[-1] == 10_800
    assert frame.scene is not None
    layers = {layer.key: layer for layer in frame.scene.layers}
    assert layers["storm_cloud_body"].threshold_label.endswith("0.05 g/kg")
    assert layers["rising_core"].scale is not None
    assert layers["rising_core"].scale.scale_id == "supercell_midlevel_vertical_velocity_v1"
    assert layers["rising_core"].default_visible is True
    assert layers["strong_descent"].default_visible is False
    assert layers["cyclonic_rotation"].source_fields == ["zvort"]
    assert layers["cyclonic_rotation"].threshold_label.endswith("0.01 s^-1 in rising air")
    assert layers["updraft_helicity"].default_visible is True
    assert "300 m^2/s^2" in layers["updraft_helicity"].threshold_label
    assert layers["updraft_helicity"].scale is not None
    assert layers["updraft_helicity"].scale.scale_id == "supercell_updraft_helicity_v2"
    assert layers["updraft_helicity"].scale.minimum == 0
    assert layers["updraft_helicity"].scale.maximum == 2_000
    assert layers["reflectivity"].default_visible is False
    assert layers["reflectivity"].scale is not None
    assert layers["reflectivity"].scale.scale_id == "supercell_reflectivity_v2"
    assert layers["reflectivity"].scale.maximum == 75
    assert all(layer.returned_count <= layer.source_count for layer in layers.values())


def test_product_frame_exposes_native_plane_inventory_and_honors_selected_height(
    tmp_path: Path,
) -> None:
    _write_retained_fixture(tmp_path, presentation=True)

    frame = supercells_explore_frame(
        _settings(tmp_path),
        lens="rotating_updraft",
        time_index=5,
        viewport="storm",
        x_index=2,
        y_index=1,
        z_index=4,
    )

    assert frame.plan.level_index == 4
    assert frame.plan.level_km == pytest.approx(15.25)
    assert frame.plan.title == "Updraft and rotation"
    assert frame.what_to_notice_by_view is not None
    assert "15.25 km slice" in frame.what_to_notice_by_view["plan"]
    assert frame.scene is not None
    assert frame.scene.coordinate_indices == {
        "x": [1, 2, 3],
        "y": [1, 2, 3],
        "z": [0, 1, 2, 3, 4],
    }
    assert frame.scene.coordinate_values_km["x"] == pytest.approx([-30, 0, 30])
    assert frame.scene.coordinate_values_km["y"] == pytest.approx([-30, 0, 30])
    assert frame.scene.coordinate_values_km["z"] == pytest.approx([0.25, 1.25, 3.25, 10.25, 15.25])


def test_product_hydrometeor_scene_keeps_exact_large_ice_label(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path, presentation=True)

    frame = supercells_explore_frame(
        _settings(tmp_path), lens="cloud_precipitation", time_index=5, viewport="full"
    )

    assert frame.scene is not None
    assert frame.plan.x_indices == [0, 2, 4]
    assert frame.plan.y_indices == [0, 2, 4]
    assert frame.scene.coordinate_indices["x"] == [0, 1, 2, 3, 4]
    assert frame.scene.coordinate_indices["y"] == [0, 1, 2, 3, 4]
    assert frame.provenance["full_domain_level_of_detail"] == "every_other_native_x_y_cell"
    category_layer = next(
        layer for layer in frame.scene.layers if layer.key == "hydrometeor_categories"
    )
    assert category_layer.default_visible is True
    assert category_layer.categories[-1].label == "Hail-treated large ice"
    assert category_layer.scale is not None
    assert category_layer.scale.scale_id == "supercell_total_condensate_v2"
    assert category_layer.scale.maximum == 20


def test_product_low_level_scene_identifies_model_relative_flow(tmp_path: Path) -> None:
    _write_retained_fixture(tmp_path, presentation=True)

    frame = supercells_explore_frame(
        _settings(tmp_path),
        lens="low_level_interactions",
        time_index=5,
        viewport="storm",
        z_index=2,
    )

    assert frame.scene is not None
    assert frame.scene.wind_vectors
    assert frame.plan.level_km == pytest.approx(3.25)
    assert frame.scene.wind_vectors[0].z_km == pytest.approx(frame.plan.level_km)
    assert frame.scene.coordinate_extents_km["z"]["max"] == pytest.approx(5.25)
    assert frame.scene.coordinate_sizes["z"] == 3
    assert frame.scene.coordinate_indices["z"] == [0, 1, 2]
    assert frame.scene.coordinate_values_km["z"] == pytest.approx([0.25, 1.25, 3.25])
    layers = {layer.key: layer for layer in frame.scene.layers}
    motion = layers["low_level_vertical_motion"]
    precipitation = layers["precipitating_condensate"]
    accumulated_rain = layers["accumulated_surface_rain"]
    assert precipitation.scale is not None
    assert precipitation.scale.scale_id == "supercell_low_level_precipitating_condensate_v1"
    assert accumulated_rain.scale is not None
    assert accumulated_rain.scale.scale_id == "supercell_accumulated_rain_v2"
    assert accumulated_rain.scale.maximum == 120
    assert "through 3.25 km" in precipitation.threshold_label
    assert max(point[2] for point in precipitation.points) <= 3.25
    assert motion.points
    assert all(point[2] == pytest.approx(frame.plan.level_km) for point in motion.points)
    assert max(point[2] for point in layers["reflectivity"].points) <= 5.25
    assert frame.plan.wind_vectors[0].u_m_s == pytest.approx(frame.scene.wind_vectors[0].u_m_s)
    assert frame.plan.wind_vectors[0].v_m_s == pytest.approx(frame.scene.wind_vectors[0].v_m_s)
    assert layers["precipitating_condensate"].default_visible is True
    assert frame.plan.overlays["low_level_precipitating_condensate"].units == "g/kg"
    assert "displayed 3.25 km level" in (
        frame.plan.overlays["low_level_precipitating_condensate"].derivation or ""
    )
    assert frame.what_to_notice_by_view is not None
    assert "current 3.25 km motion" in frame.what_to_notice_by_view["plan"]
    assert frame.selected_point.coordinate_frame.startswith("translating model frame")
    assert "cold pool" in frame.caveats[-1]

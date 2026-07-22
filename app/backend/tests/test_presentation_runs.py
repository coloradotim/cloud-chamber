from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from cloud_chamber.presentation_runs import (
    PRESENTATION_RUN_SPECS,
    render_presentation_namelist,
    spec_by_key,
    write_moist_presentation_terrain,
)


def _namelist() -> str:
    return """&param0
 nx = 64,
 ny = 64,
 nz = 75,
 dx = 100.0,
 dy = 100.0,
 dz = 40.0,
 dtl = 3.0,
 timax = 21600.0,
 tapfrq = 120.0,
/
"""


def test_four_presentation_specs_are_bounded_and_unique() -> None:
    assert len(PRESENTATION_RUN_SPECS) == 4
    assert len({spec.key for spec in PRESENTATION_RUN_SPECS}) == 4
    assert len({spec.run_id for spec in PRESENTATION_RUN_SPECS}) == 4
    assert [spec.world for spec in PRESENTATION_RUN_SPECS].count("trade_cumulus") == 2
    assert [spec.world for spec in PRESENTATION_RUN_SPECS].count("mountain_waves") == 2


def test_trade_presentation_namelist_preserves_domain_and_doubles_cadence() -> None:
    spec = spec_by_key("trade_baseline")
    rendered = render_presentation_namelist(_namelist(), spec)
    assert "nx = 96," in rendered
    assert "ny = 96," in rendered
    assert "nz = 100," in rendered
    assert "tapfrq = 60," in rendered
    assert math.isclose(spec.nx * spec.dx_m, 6400.0)
    assert math.isclose(spec.nz * spec.dz_m, 3000.0)
    assert spec.expected_times_seconds[-1] == 14_400
    assert len(spec.expected_times_seconds) == 241
    assert spec.duration_seconds == 4 * 60 * 60


def test_mountain_contracts_preserve_domain_and_use_thirty_second_histories() -> None:
    dry = spec_by_key("mountain_dry")
    moist = spec_by_key("mountain_moist")
    assert math.isclose(dry.nx * dry.dx_m, 20_000.0)
    assert math.isclose(dry.nz * dry.dz_m, 20_000.0)
    assert dry.expected_times_seconds[-1] == 2_160
    assert len(dry.expected_times_seconds) == 73
    assert math.isclose(moist.nx * moist.dx_m, 220_000.0)
    assert math.isclose(moist.nz * moist.dz_m, 25_000.0)
    assert moist.expected_times_seconds[-1] == 7_200
    assert len(moist.expected_times_seconds) == 241


def test_moist_terrain_matches_finer_native_grid(tmp_path: Path) -> None:
    spec = spec_by_key("mountain_moist")
    path = tmp_path / "perts.dat"
    write_moist_presentation_terrain(path, spec)
    values = np.fromfile(path, dtype="<f4")
    assert values.shape == (spec.nx,)
    assert np.all(np.isfinite(values))
    assert math.isclose(float(np.max(values)), 2000.0, abs_tol=1e-4)
    assert path.stat().st_size == 4 * spec.nx * spec.ny

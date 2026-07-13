"""Run-configuration choices for CM1 run generation.

The product model is intentionally explicit: duration, horizontal cell budget,
domain size, output cadence, and lower-boundary forcing are separate levers. The
backend resolves those choices into CM1-facing values before package creation.
"""

from __future__ import annotations

import math
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

RunMode = Literal["smoke", "science"]


class RunConfigurationCM1Values(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nx: int
    ny: int
    nz: int
    dx_m: float
    dy_m: float
    dz_m: float
    stretch_z: int
    model_top_m: float
    str_bot_m: float
    str_top_m: float
    dz_bot_m: float
    dz_top_m: float
    domain_x_km: float
    domain_y_km: float
    time_step_seconds: float
    runtime_seconds: int
    output_cadence_seconds: int
    restart_cadence_seconds: int
    rayleigh_damping_start_m: int
    expected_output_frames: int
    grid_cell_count: int


class RunConfigurationSurfaceFluxCM1Values(BaseModel):
    model_config = ConfigDict(extra="forbid")

    isfcflx: int
    sfcmodel: int
    oceanmodel: int
    set_flx: int
    cnst_shflx: float
    cnst_shflx_units: str
    cnst_lhflx: float
    cnst_lhflx_units: str
    set_znt: int
    cnst_znt: float
    set_ust: int
    cnst_ust: float


class RunConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    configuration_id: str
    mode: RunMode
    label: str
    duration: str
    duration_seconds: int
    horizontal_cell_count: int
    domain_size: str
    output_cadence: str
    output_cadence_seconds: int
    diagnostic_set: str
    cost_runtime_summary: str
    output_volume_summary: str
    cm1_values: RunConfigurationCM1Values
    initiation_method: str
    initiation_summary: str
    surface_heat_flux_k_m_s: float
    surface_moisture_flux_g_g_m_s: float
    surface_flux_mode: str
    surface_flux_summary: str
    surface_flux_cm1_values: RunConfigurationSurfaceFluxCM1Values
    surface_flux_caveats: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class _DurationChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seconds: int
    mode: RunMode
    label: str


class _HorizontalCellChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cells: int
    label: str


class _DomainChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_km: float
    y_km: float
    nz: int
    dz_m: float
    stretch_z: int
    model_top_m: float
    str_bot_m: float
    str_top_m: float
    dz_bot_m: float
    dz_top_m: float
    label: str


class _VerticalGridChoice(TypedDict):
    nz: int
    dz_m: float
    stretch_z: int
    model_top_m: float
    str_bot_m: float
    str_top_m: float
    dz_bot_m: float
    dz_top_m: float


class _CadenceChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seconds: int
    label: str


DURATION_CHOICES: dict[str, _DurationChoice] = {
    "smoke_1h": _DurationChoice(seconds=3600, mode="smoke", label="Smoke check"),
    "short_6h": _DurationChoice(seconds=21600, mode="science", label="Short evolution"),
    "standard_12h": _DurationChoice(seconds=43200, mode="science", label="Standard evolution"),
    "long_24h": _DurationChoice(seconds=86400, mode="science", label="Long evolution"),
}

HORIZONTAL_CELL_CHOICES: dict[str, _HorizontalCellChoice] = {
    "cells_64": _HorizontalCellChoice(cells=64, label="Scout 64 x 64"),
    "cells_96": _HorizontalCellChoice(cells=96, label="Light 96 x 96"),
    "cells_128": _HorizontalCellChoice(cells=128, label="Standard 128 x 128"),
    "cells_192": _HorizontalCellChoice(cells=192, label="Detailed 192 x 192"),
    "cells_256": _HorizontalCellChoice(cells=256, label="High detail 256 x 256"),
    "cells_384": _HorizontalCellChoice(cells=384, label="Very high detail 384 x 384"),
}

TALL_STRETCHED_VERTICAL_GRID: _VerticalGridChoice = {
    "nz": 100,
    "dz_m": 40.0,
    "stretch_z": 1,
    "model_top_m": 18000.0,
    "str_bot_m": 2000.0,
    "str_top_m": 18000.0,
    "dz_bot_m": 40.0,
    "dz_top_m": 600.0,
}

DOMAIN_CHOICES: dict[str, _DomainChoice] = {
    "local_6km": _DomainChoice(
        x_km=6.4,
        y_km=6.4,
        **TALL_STRETCHED_VERTICAL_GRID,
        label="Local 6 km",
    ),
    "wide_12km": _DomainChoice(
        x_km=12.8,
        y_km=12.8,
        **TALL_STRETCHED_VERTICAL_GRID,
        label="Wide 12 km",
    ),
    "regional_60km": _DomainChoice(
        x_km=60.0,
        y_km=60.0,
        **TALL_STRETCHED_VERTICAL_GRID,
        label="Regional 60 km",
    ),
    "regional_120km": _DomainChoice(
        x_km=120.0,
        y_km=120.0,
        **TALL_STRETCHED_VERTICAL_GRID,
        label="Regional 120 km",
    ),
}

CADENCE_CHOICES: dict[str, _CadenceChoice] = {
    "sparse_60min": _CadenceChoice(seconds=3600, label="Sparse 60 min"),
    "standard_15min": _CadenceChoice(seconds=900, label="Standard 15 min"),
    "detailed_5min": _CadenceChoice(seconds=300, label="Detailed 5 min"),
}

DEFAULT_SURFACE_HEAT_FLUX_K_M_S = 8.0e-3
DEFAULT_SURFACE_MOISTURE_FLUX_G_G_M_S = 5.2e-5
SURFACE_HEAT_FLUX_CONTEXT_RANGE_K_M_S = (0.0, 0.2)
SURFACE_MOISTURE_FLUX_CONTEXT_RANGE_G_G_M_S = (0.0, 2.0e-4)


def default_run_configuration_payload(run_recipe: str | None = None) -> dict[str, str | float]:
    if run_recipe == "observed_surface_forced_evolution":
        return {
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "full",
            "surface_heat_flux_k_m_s": DEFAULT_SURFACE_HEAT_FLUX_K_M_S,
            "surface_moisture_flux_g_g_m_s": DEFAULT_SURFACE_MOISTURE_FLUX_G_G_M_S,
        }
    return {
        "duration": "short_6h",
        "horizontal_cell_count": "cells_64",
        "domain_size": "local_6km",
        "output_cadence": "standard_15min",
        "diagnostic_set": "full",
        "surface_heat_flux_k_m_s": DEFAULT_SURFACE_HEAT_FLUX_K_M_S,
        "surface_moisture_flux_g_g_m_s": DEFAULT_SURFACE_MOISTURE_FLUX_G_G_M_S,
    }


def resolve_run_configuration(
    *,
    run_configuration: dict[str, Any] | RunConfiguration | None = None,
    run_recipe: str | None = None,
) -> RunConfiguration:
    if isinstance(run_configuration, RunConfiguration):
        return run_configuration
    if run_configuration is None:
        payload = default_run_configuration_payload(run_recipe)
    else:
        payload = dict(run_configuration)

    payload = {
        **default_run_configuration_payload(run_recipe),
        **payload,
    }

    initiation_method = "none"

    duration = _choice(DURATION_CHOICES, payload.get("duration"), "duration")
    horizontal_cells = _choice(
        HORIZONTAL_CELL_CHOICES,
        payload.get("horizontal_cell_count"),
        "horizontal_cell_count",
    )
    domain = _choice(DOMAIN_CHOICES, payload.get("domain_size"), "domain_size")
    cadence = _choice(
        CADENCE_CHOICES,
        payload.get("output_cadence"),
        "output_cadence",
    )
    diagnostic_set = "full"
    heat_flux = _float_payload(
        payload,
        "surface_heat_flux_k_m_s",
        "surface heat flux",
    )
    moisture_flux = _float_payload(
        payload,
        "surface_moisture_flux_g_g_m_s",
        "surface moisture flux",
    )
    surface_flux_enabled = True
    surface_flux_mode = "constant_uniform_surface_flux_proxy"
    surface_flux_cm1_values = _surface_flux_cm1_values(
        enabled=surface_flux_enabled,
        heat_flux_k_m_s=heat_flux,
        moisture_flux_g_g_m_s=moisture_flux,
    )
    surface_flux_caveats = _surface_flux_caveats(
        surface_flux_mode,
        heat_flux_k_m_s=heat_flux,
        moisture_flux_g_g_m_s=moisture_flux,
    )

    nx = horizontal_cells.cells
    ny = horizontal_cells.cells
    dx_m = domain.x_km * 1000.0 / nx
    dy_m = domain.y_km * 1000.0 / ny
    restart_seconds = max(cadence.seconds, min(duration.seconds, 10800))
    frames = _expected_output_frames(duration.seconds, cadence.seconds)
    grid_cells = nx * ny * domain.nz
    configuration_id = _configuration_id(
        duration=str(payload["duration"]),
        horizontal_cell_count=str(payload["horizontal_cell_count"]),
        domain_size=str(payload["domain_size"]),
        output_cadence=str(payload["output_cadence"]),
        diagnostic_set=diagnostic_set,
        surface_heat_flux_k_m_s=heat_flux,
        surface_moisture_flux_g_g_m_s=moisture_flux,
        surface_flux_mode=surface_flux_mode,
    )
    caveats = _configuration_caveats(
        mode=duration.mode,
        horizontal_cell_count=horizontal_cells.cells,
        domain_size=str(payload["domain_size"]),
        surface_flux_caveats=surface_flux_caveats,
    )
    return RunConfiguration(
        configuration_id=configuration_id,
        mode=duration.mode,
        label=_configuration_label(
            duration.label,
            domain.label,
            horizontal_cells.label,
            dx_m,
            cadence.label,
        ),
        duration=str(payload["duration"]),
        duration_seconds=duration.seconds,
        horizontal_cell_count=horizontal_cells.cells,
        domain_size=str(payload["domain_size"]),
        output_cadence=str(payload["output_cadence"]),
        output_cadence_seconds=cadence.seconds,
        diagnostic_set=diagnostic_set,
        cost_runtime_summary=_runtime_summary(duration.seconds, grid_cells, cadence.seconds),
        output_volume_summary=_output_summary(frames, grid_cells, diagnostic_set),
        cm1_values=RunConfigurationCM1Values(
            nx=nx,
            ny=ny,
            nz=domain.nz,
            dx_m=dx_m,
            dy_m=dy_m,
            dz_m=domain.dz_m,
            stretch_z=domain.stretch_z,
            model_top_m=domain.model_top_m,
            str_bot_m=domain.str_bot_m,
            str_top_m=domain.str_top_m,
            dz_bot_m=domain.dz_bot_m,
            dz_top_m=domain.dz_top_m,
            domain_x_km=domain.x_km,
            domain_y_km=domain.y_km,
            time_step_seconds=_time_step_seconds(),
            runtime_seconds=duration.seconds,
            output_cadence_seconds=cadence.seconds,
            restart_cadence_seconds=restart_seconds,
            rayleigh_damping_start_m=_rayleigh_damping_start_m(),
            expected_output_frames=frames,
            grid_cell_count=grid_cells,
        ),
        initiation_method=initiation_method,
        initiation_summary=_initiation_summary(initiation_method),
        surface_heat_flux_k_m_s=heat_flux,
        surface_moisture_flux_g_g_m_s=moisture_flux,
        surface_flux_mode=surface_flux_mode,
        surface_flux_summary=_surface_flux_summary(
            surface_flux_mode,
            heat_flux,
            moisture_flux,
        ),
        surface_flux_cm1_values=surface_flux_cm1_values,
        surface_flux_caveats=surface_flux_caveats,
        caveats=caveats,
    )


def _choice[T](choices: dict[str, T], value: object, label: str) -> T:
    if not isinstance(value, str) or value not in choices:
        if label == "domain_size" and isinstance(value, str) and value.startswith("storm_"):
            raise ValueError(
                "Removed domain_size: storm-style domains are not active run-configuration "
                "choices. Use local_6km, wide_12km, regional_60km, or regional_120km."
            )
        raise ValueError(f"Unknown {label}: {value}")
    return choices[value]


def _float_payload(payload: dict[str, Any], key: str, label: str) -> float:
    value = payload.get(key)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"Unknown {label}: {value}") from exc
    elif isinstance(value, int | float):
        parsed = float(value)
    else:
        raise ValueError(f"Unknown {label}: {value}")
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"Invalid {label}: must be a finite non-negative number")
    return parsed


def _configuration_id(
    *,
    duration: str,
    horizontal_cell_count: str,
    domain_size: str,
    output_cadence: str,
    diagnostic_set: str,
    surface_heat_flux_k_m_s: float,
    surface_moisture_flux_g_g_m_s: float,
    surface_flux_mode: str,
) -> str:
    if surface_flux_mode == "disabled":
        return (
            f"{duration}__{horizontal_cell_count}__{domain_size}__{output_cadence}"
            f"__{diagnostic_set}__surface_fluxes_disabled"
        )
    return (
        f"{duration}__{horizontal_cell_count}__{domain_size}__{output_cadence}"
        f"__{diagnostic_set}__shflx_{_flux_id(surface_heat_flux_k_m_s)}"
        f"__qflx_{_flux_id(surface_moisture_flux_g_g_m_s)}"
    )


def _configuration_label(
    duration_label: str,
    domain_label: str,
    horizontal_cells_label: str,
    dx_m: float,
    cadence_label: str,
) -> str:
    return (
        f"{duration_label}; {domain_label}; {horizontal_cells_label}; "
        f"{_format_spacing(dx_m)} dx/dy; {cadence_label}"
    )


def _runtime_summary(duration_seconds: int, grid_cells: int, cadence_seconds: int) -> str:
    return (
        f"{duration_seconds // 3600:g} h model time, {grid_cells:,} cells, "
        f"{cadence_seconds // 60:g} min saved-output cadence"
    )


def _output_summary(frames: int, grid_cells: int, diagnostic_set: str) -> str:
    return f"{frames:,} saved frames, full output fields, {grid_cells:,} cells per frame"


def _configuration_caveats(
    *,
    mode: RunMode,
    horizontal_cell_count: int,
    domain_size: str,
    surface_flux_caveats: list[str],
) -> list[str]:
    caveats: list[str] = list(surface_flux_caveats)
    if mode == "smoke":
        caveats.append("short_smoke_mode_is_for_package_health_not_science_evolution")
    if mode == "science":
        caveats.append("science_run_configuration_minimum_duration_6h")
    if horizontal_cell_count >= 256 or domain_size in {
        "wide_12km",
        "regional_60km",
        "regional_120km",
    }:
        caveats.append("configuration_better_suited_to_larger_compute")
    return caveats


def _initiation_summary(initiation_method: str) -> str:
    return "No artificial initiation"


def _surface_flux_cm1_values(
    *,
    enabled: bool,
    heat_flux_k_m_s: float,
    moisture_flux_g_g_m_s: float,
) -> RunConfigurationSurfaceFluxCM1Values:
    return RunConfigurationSurfaceFluxCM1Values(
        isfcflx=1 if enabled else 0,
        sfcmodel=1 if enabled else 0,
        oceanmodel=1 if enabled else 0,
        set_flx=1 if enabled else 0,
        cnst_shflx=heat_flux_k_m_s if enabled else 0.0,
        cnst_shflx_units="K m/s",
        cnst_lhflx=moisture_flux_g_g_m_s if enabled else 0.0,
        cnst_lhflx_units="g/g m/s",
        set_znt=0,
        cnst_znt=0.0,
        set_ust=1 if enabled else 0,
        cnst_ust=0.28,
    )


def _surface_flux_summary(
    surface_flux_mode: str,
    heat_flux_k_m_s: float,
    moisture_flux_g_g_m_s: float,
) -> str:
    if surface_flux_mode == "disabled":
        return "Surface heat/moisture flux forcing disabled"
    return (
        f"Surface heat flux {_format_scientific(heat_flux_k_m_s)} K m/s; "
        f"surface moisture flux {_format_scientific(moisture_flux_g_g_m_s)} g/g m/s; "
        "constant uniform proxy"
    )


def _surface_flux_caveats(
    surface_flux_mode: str,
    *,
    heat_flux_k_m_s: float,
    moisture_flux_g_g_m_s: float,
) -> list[str]:
    if surface_flux_mode == "disabled":
        return []
    caveats = [
        "surface_flux_proxy_constant_uniform_not_place_time_energy_budget",
        "surface_flux_proxy_not_real_land_surface_or_evaporation_model",
        "surface_flux_proxy_values_need_local_smoke_validation",
    ]
    if not _in_range(heat_flux_k_m_s, SURFACE_HEAT_FLUX_CONTEXT_RANGE_K_M_S):
        caveats.append("surface_heat_flux_outside_daytime_context_range")
    if not _in_range(moisture_flux_g_g_m_s, SURFACE_MOISTURE_FLUX_CONTEXT_RANGE_G_G_M_S):
        caveats.append("surface_moisture_flux_outside_daytime_context_range")
    return caveats


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    low, high = bounds
    return low <= value <= high


def _format_scientific(value: float) -> str:
    return f"{value:.3g}"


def _flux_id(value: float) -> str:
    return f"{value:.3e}".replace("+", "").replace("-", "m").replace(".", "p")


def _time_step_seconds() -> float:
    return 3.0


def _rayleigh_damping_start_m() -> int:
    return 12000


def _expected_output_frames(runtime_seconds: int, output_cadence_seconds: int) -> int:
    if output_cadence_seconds <= 0:
        return 0
    return runtime_seconds // output_cadence_seconds + 1


def _format_spacing(dx_m: float) -> str:
    if dx_m >= 1000.0:
        return f"{dx_m / 1000.0:.2g} km"
    if dx_m >= 100.0:
        return f"{dx_m:.0f} m"
    return f"{dx_m:.1f} m"

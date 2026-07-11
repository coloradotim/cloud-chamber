"""Run-configuration choices for CM1 run generation.

The product model is intentionally explicit: duration, horizontal cell budget,
domain size, output cadence, and diagnostic set are separate levers. The backend
resolves those choices into CM1-facing values before package creation.
"""

from __future__ import annotations

from typing import Any, Literal

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
    model_top_m: float
    domain_x_km: float
    domain_y_km: float
    time_step_seconds: float
    runtime_seconds: int
    output_cadence_seconds: int
    restart_cadence_seconds: int
    rayleigh_damping_start_m: int
    expected_output_frames: int
    grid_cell_count: int


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
    model_top_m: float
    label: str


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

SHALLOW_DOMAIN_CHOICES: dict[str, _DomainChoice] = {
    "local_6km": _DomainChoice(
        x_km=6.4,
        y_km=6.4,
        nz=75,
        dz_m=40.0,
        model_top_m=18000.0,
        label="Local 6 km",
    ),
    "wide_12km": _DomainChoice(
        x_km=12.8,
        y_km=12.8,
        nz=75,
        dz_m=40.0,
        model_top_m=18000.0,
        label="Wide 12 km",
    ),
    "regional_60km": _DomainChoice(
        x_km=60.0,
        y_km=60.0,
        nz=75,
        dz_m=40.0,
        model_top_m=18000.0,
        label="Regional 60 km",
    ),
    "regional_120km": _DomainChoice(
        x_km=120.0,
        y_km=120.0,
        nz=75,
        dz_m=40.0,
        model_top_m=18000.0,
        label="Regional 120 km",
    ),
}

DEEP_DOMAIN_CHOICES: dict[str, _DomainChoice] = {
    "storm_120km": _DomainChoice(
        x_km=120.0,
        y_km=120.0,
        nz=40,
        dz_m=500.0,
        model_top_m=20000.0,
        label="Storm 120 km",
    ),
    "storm_160km": _DomainChoice(
        x_km=160.0,
        y_km=160.0,
        nz=40,
        dz_m=500.0,
        model_top_m=20000.0,
        label="Storm 160 km",
    ),
    "storm_240km": _DomainChoice(
        x_km=240.0,
        y_km=240.0,
        nz=40,
        dz_m=500.0,
        model_top_m=20000.0,
        label="Storm 240 km",
    ),
}

CADENCE_CHOICES: dict[str, _CadenceChoice] = {
    "sparse_60min": _CadenceChoice(seconds=3600, label="Sparse 60 min"),
    "standard_15min": _CadenceChoice(seconds=900, label="Standard 15 min"),
    "detailed_5min": _CadenceChoice(seconds=300, label="Detailed 5 min"),
}

DIAGNOSTIC_SET_CHOICES = {"essential", "process", "full"}


def default_run_configuration_payload(run_recipe: str | None = None) -> dict[str, str]:
    if run_recipe == "triggered_deep_potential":
        return {
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "storm_120km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "full",
        }
    if run_recipe == "untriggered_observed_evolution":
        return {
            "duration": "short_6h",
            "horizontal_cell_count": "cells_128",
            "domain_size": "wide_12km",
            "output_cadence": "standard_15min",
            "diagnostic_set": "process",
        }
    return {
        "duration": "short_6h",
        "horizontal_cell_count": "cells_64",
        "domain_size": "local_6km",
        "output_cadence": "standard_15min",
        "diagnostic_set": "process",
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

    if run_recipe == "triggered_deep_potential":
        if payload.get("domain_size") in SHALLOW_DOMAIN_CHOICES:
            payload["domain_size"] = "storm_120km"
    elif payload.get("domain_size") in DEEP_DOMAIN_CHOICES:
        payload["domain_size"] = "local_6km"

    is_triggered_deep_potential = run_recipe == "triggered_deep_potential"
    duration = _choice(DURATION_CHOICES, payload.get("duration"), "duration")
    horizontal_cells = _choice(
        HORIZONTAL_CELL_CHOICES,
        payload.get("horizontal_cell_count"),
        "horizontal_cell_count",
    )
    domains = DEEP_DOMAIN_CHOICES if is_triggered_deep_potential else SHALLOW_DOMAIN_CHOICES
    domain = _choice(domains, payload.get("domain_size"), "domain_size")
    cadence = _choice(
        CADENCE_CHOICES,
        payload.get("output_cadence"),
        "output_cadence",
    )
    diagnostic_set = str(payload.get("diagnostic_set", "process"))
    if diagnostic_set not in DIAGNOSTIC_SET_CHOICES:
        raise ValueError(f"Unknown diagnostic_set: {diagnostic_set}")

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
    )
    caveats = _configuration_caveats(
        mode=duration.mode,
        run_recipe=run_recipe,
        diagnostic_set=diagnostic_set,
        horizontal_cell_count=horizontal_cells.cells,
        domain_size=str(payload["domain_size"]),
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
            model_top_m=domain.model_top_m,
            domain_x_km=domain.x_km,
            domain_y_km=domain.y_km,
            time_step_seconds=_time_step_seconds(run_recipe),
            runtime_seconds=duration.seconds,
            output_cadence_seconds=cadence.seconds,
            restart_cadence_seconds=restart_seconds,
            rayleigh_damping_start_m=_rayleigh_damping_start_m(run_recipe),
            expected_output_frames=frames,
            grid_cell_count=grid_cells,
        ),
        caveats=caveats,
    )


def _choice[T](choices: dict[str, T], value: object, label: str) -> T:
    if not isinstance(value, str) or value not in choices:
        raise ValueError(f"Unknown {label}: {value}")
    return choices[value]


def _configuration_id(
    *,
    duration: str,
    horizontal_cell_count: str,
    domain_size: str,
    output_cadence: str,
    diagnostic_set: str,
) -> str:
    return f"{duration}__{horizontal_cell_count}__{domain_size}__{output_cadence}__{diagnostic_set}"


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
    return f"{frames:,} saved frames, {diagnostic_set} diagnostics, {grid_cells:,} cells per frame"


def _configuration_caveats(
    *,
    mode: RunMode,
    run_recipe: str | None,
    diagnostic_set: str,
    horizontal_cell_count: int,
    domain_size: str,
) -> list[str]:
    caveats: list[str] = []
    if mode == "smoke":
        caveats.append("short_smoke_mode_is_for_package_health_not_science_evolution")
    if mode == "science":
        caveats.append("science_run_configuration_minimum_duration_6h")
    if run_recipe == "triggered_deep_potential":
        caveats.append("triggered_deep_potential_is_not_normal_evolution")
    if diagnostic_set == "essential":
        caveats.append("essential_diagnostic_set_limits_later_diagnostics")
    if horizontal_cell_count >= 256 or domain_size in {
        "wide_12km",
        "regional_60km",
        "regional_120km",
        "storm_240km",
    }:
        caveats.append("configuration_better_suited_to_larger_compute")
    return caveats


def _time_step_seconds(run_recipe: str | None) -> float:
    return 6.0 if run_recipe == "triggered_deep_potential" else 3.0


def _rayleigh_damping_start_m(run_recipe: str | None) -> int:
    return 15000 if run_recipe == "triggered_deep_potential" else 2500


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

"""Run-configuration choices for CM1 package generation.

The product model is intentionally explicit: duration, grid/detail, domain,
output cadence, and output-field density are separate levers. The backend
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
    duration_preset: str
    duration_seconds: int
    grid_detail_preset: str
    domain_size_preset: str
    output_cadence_preset: str
    output_cadence_seconds: int
    output_field_density_preset: str
    cost_runtime_summary: str
    output_volume_summary: str
    cm1_values: RunConfigurationCM1Values
    caveats: list[str] = Field(default_factory=list)


class _DurationChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seconds: int
    mode: RunMode
    label: str


class _GridChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dx_m: float
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
    "quick_6h": _DurationChoice(seconds=21600, mode="science", label="Quick science"),
    "standard_12h": _DurationChoice(seconds=43200, mode="science", label="Standard science"),
    "long_24h": _DurationChoice(seconds=86400, mode="science", label="Long evolution"),
}

SHALLOW_GRID_CHOICES: dict[str, _GridChoice] = {
    "coarse": _GridChoice(dx_m=200.0, label="Coarse"),
    "standard": _GridChoice(dx_m=100.0, label="Standard"),
    "fine": _GridChoice(dx_m=50.0, label="Fine"),
}

DEEP_GRID_CHOICES: dict[str, _GridChoice] = {
    "coarse": _GridChoice(dx_m=2000.0, label="Coarse"),
    "standard": _GridChoice(dx_m=1000.0, label="Standard"),
    "fine": _GridChoice(dx_m=500.0, label="Fine"),
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

FIELD_DENSITY_CHOICES = {"core", "analysis", "rich"}


def default_run_configuration_payload(package_family: str | None = None) -> dict[str, str]:
    if package_family == "deep_convection_trial":
        return {
            "duration_preset": "quick_6h",
            "grid_detail_preset": "standard",
            "domain_size_preset": "storm_120km",
            "output_cadence_preset": "standard_15min",
            "output_field_density_preset": "rich",
        }
    if package_family == "observed_sounding_quicklook":
        return {
            "duration_preset": "quick_6h",
            "grid_detail_preset": "standard",
            "domain_size_preset": "wide_12km",
            "output_cadence_preset": "standard_15min",
            "output_field_density_preset": "analysis",
        }
    return {
        "duration_preset": "quick_6h",
        "grid_detail_preset": "standard",
        "domain_size_preset": "local_6km",
        "output_cadence_preset": "standard_15min",
        "output_field_density_preset": "analysis",
    }


def resolve_run_configuration(
    *,
    run_configuration: dict[str, Any] | RunConfiguration | None = None,
    package_family: str | None = None,
) -> RunConfiguration:
    if isinstance(run_configuration, RunConfiguration):
        payload = run_configuration.model_dump()
    elif run_configuration is None:
        payload = default_run_configuration_payload(package_family)
    else:
        payload = dict(run_configuration)

    payload = {
        **default_run_configuration_payload(package_family),
        **payload,
    }

    if package_family == "deep_convection_trial":
        if payload.get("domain_size_preset") in SHALLOW_DOMAIN_CHOICES:
            payload["domain_size_preset"] = "storm_120km"
    elif payload.get("domain_size_preset") in DEEP_DOMAIN_CHOICES:
        payload["domain_size_preset"] = "local_6km"

    is_deep_convection = package_family == "deep_convection_trial"
    duration = _choice(DURATION_CHOICES, payload.get("duration_preset"), "duration_preset")
    grid_choices = DEEP_GRID_CHOICES if is_deep_convection else SHALLOW_GRID_CHOICES
    grid = _choice(grid_choices, payload.get("grid_detail_preset"), "grid_detail_preset")
    domains = DEEP_DOMAIN_CHOICES if is_deep_convection else SHALLOW_DOMAIN_CHOICES
    domain = _choice(domains, payload.get("domain_size_preset"), "domain_size_preset")
    cadence = _choice(
        CADENCE_CHOICES,
        payload.get("output_cadence_preset"),
        "output_cadence_preset",
    )
    field_density = str(payload.get("output_field_density_preset", "analysis"))
    if field_density not in FIELD_DENSITY_CHOICES:
        raise ValueError(f"Unknown output_field_density_preset: {field_density}")

    nx = max(1, round(domain.x_km * 1000.0 / grid.dx_m))
    ny = max(1, round(domain.y_km * 1000.0 / grid.dx_m))
    restart_seconds = max(cadence.seconds, min(duration.seconds, 10800))
    frames = _expected_output_frames(duration.seconds, cadence.seconds)
    grid_cells = nx * ny * domain.nz
    configuration_id = _configuration_id(
        duration_preset=str(payload["duration_preset"]),
        grid_detail_preset=str(payload["grid_detail_preset"]),
        domain_size_preset=str(payload["domain_size_preset"]),
        output_cadence_preset=str(payload["output_cadence_preset"]),
        output_field_density_preset=field_density,
    )
    caveats = _configuration_caveats(
        mode=duration.mode,
        package_family=package_family,
        field_density=field_density,
        grid_detail_preset=str(payload["grid_detail_preset"]),
        domain_size_preset=str(payload["domain_size_preset"]),
    )
    return RunConfiguration(
        configuration_id=configuration_id,
        mode=duration.mode,
        label=_configuration_label(duration.label, domain.label, grid.label, cadence.label),
        duration_preset=str(payload["duration_preset"]),
        duration_seconds=duration.seconds,
        grid_detail_preset=str(payload["grid_detail_preset"]),
        domain_size_preset=str(payload["domain_size_preset"]),
        output_cadence_preset=str(payload["output_cadence_preset"]),
        output_cadence_seconds=cadence.seconds,
        output_field_density_preset=field_density,
        cost_runtime_summary=_runtime_summary(duration.seconds, grid_cells, cadence.seconds),
        output_volume_summary=_output_summary(frames, grid_cells, field_density),
        cm1_values=RunConfigurationCM1Values(
            nx=nx,
            ny=ny,
            nz=domain.nz,
            dx_m=grid.dx_m,
            dy_m=grid.dx_m,
            dz_m=domain.dz_m,
            model_top_m=domain.model_top_m,
            domain_x_km=domain.x_km,
            domain_y_km=domain.y_km,
            time_step_seconds=_time_step_seconds(package_family),
            runtime_seconds=duration.seconds,
            output_cadence_seconds=cadence.seconds,
            restart_cadence_seconds=restart_seconds,
            rayleigh_damping_start_m=_rayleigh_damping_start_m(package_family),
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
    duration_preset: str,
    grid_detail_preset: str,
    domain_size_preset: str,
    output_cadence_preset: str,
    output_field_density_preset: str,
) -> str:
    return (
        f"{duration_preset}__{grid_detail_preset}__{domain_size_preset}__"
        f"{output_cadence_preset}__{output_field_density_preset}"
    )


def _configuration_label(
    duration_label: str,
    domain_label: str,
    grid_label: str,
    cadence_label: str,
) -> str:
    return f"{duration_label}; {domain_label}; {grid_label}; {cadence_label}"


def _runtime_summary(duration_seconds: int, grid_cells: int, cadence_seconds: int) -> str:
    return (
        f"{duration_seconds // 3600:g} h model time, {grid_cells:,} cells, "
        f"{cadence_seconds // 60:g} min saved-output cadence"
    )


def _output_summary(frames: int, grid_cells: int, field_density: str) -> str:
    return f"{frames:,} saved frames, {field_density} output fields, {grid_cells:,} cells per frame"


def _configuration_caveats(
    *,
    mode: RunMode,
    package_family: str | None,
    field_density: str,
    grid_detail_preset: str,
    domain_size_preset: str,
) -> list[str]:
    caveats: list[str] = []
    if mode == "smoke":
        caveats.append("short_smoke_mode_is_for_package_health_not_science_evolution")
    if mode == "science":
        caveats.append("science_run_configuration_minimum_duration_6h")
    if package_family == "deep_convection_trial":
        caveats.append("deep_convection_trial_uses_triggered_potential_not_normal_evolution")
    if field_density == "core":
        caveats.append("core_output_density_limits_later_diagnostics")
    if grid_detail_preset == "fine" or domain_size_preset in {"wide_12km", "storm_240km"}:
        caveats.append("configuration_better_suited_to_larger_compute")
    return caveats


def _time_step_seconds(package_family: str | None) -> float:
    return 6.0 if package_family == "deep_convection_trial" else 3.0


def _rayleigh_damping_start_m(package_family: str | None) -> int:
    return 15000 if package_family == "deep_convection_trial" else 2500


def _expected_output_frames(runtime_seconds: int, output_cadence_seconds: int) -> int:
    if output_cadence_seconds <= 0:
        return 0
    return runtime_seconds // output_cadence_seconds + 1

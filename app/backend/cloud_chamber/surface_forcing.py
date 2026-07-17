"""Surface-forcing configuration and provenance helpers."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

UNIFORM_SURFACE_FLUX_MODE = "constant_uniform_surface_flux_proxy"
DIFFERENTIAL_SURFACE_FORCING_MODE = "differential_surface_forcing_patch_v0"
DISABLED_SURFACE_FLUX_MODE = "disabled"
SURFACE_FORCING_PATCH_FILENAME = "cloud_chamber_surface_forcing_patch.dat"
SURFACE_FORCING_PATCH_JSON_FILENAME = "surface_forcing_patch.json"
CM1_SOURCE_CUSTOMIZATION_FILENAME = "cm1_source_customization.json"
DIFFERENTIAL_SURFACE_FORCING_APPLICATION_NOTE = (
    "Differential surface forcing uses CM1 source customization at launch. "
    "Cloud Chamber copies the configured external CM1 tree into an isolated runtime "
    "build tree, patches that copy, rebuilds cm1.exe, writes the patch file into "
    "the run directory, and launches the copied custom executable; it must not "
    "silently fall back to uniform forcing."
)

DEFAULT_PATCH_HEAT_FLUX_PERTURBATION_K_M_S = 4.0e-2
DEFAULT_PATCH_MOISTURE_FLUX_PERTURBATION_G_G_M_S = 5.0e-5
DEFAULT_PATCH_RADIUS_M = 1500.0
DEFAULT_PATCH_TAPER_WIDTH_M = 500.0
DEFAULT_PATCH_RAMP_SECONDS = 1800.0
MIN_PATCH_RADIUS_GRID_CELLS = 3.0


class SurfaceForcingPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "surface_forcing_patch_v0"
    shape: Literal["circle"]
    center_x_m: float
    center_y_m: float
    radius_x_m: float
    radius_y_m: float
    taper_function: Literal["raised_cosine"]
    taper_width_m: float
    ramp_seconds: float
    background_heat_flux_k_m_s: float
    background_moisture_flux_g_g_m_s: float
    heat_flux_perturbation_k_m_s: float
    moisture_flux_perturbation_g_g_m_s: float
    domain_x_m: float
    domain_y_m: float
    dx_m: float
    dy_m: float
    support_status: Literal["requires_cm1_source_customization"] = (
        "requires_cm1_source_customization"
    )
    cm1_application_status: Literal["source_customization_required_at_launch"] = (
        "source_customization_required_at_launch"
    )
    pattern_sha256: str
    caveats: list[str] = Field(default_factory=list)


def surface_forcing_mode_from_payload(payload: dict[str, Any]) -> str:
    raw = payload.get("surface_forcing_mode", payload.get("surface_flux_mode"))
    if raw is None:
        return UNIFORM_SURFACE_FLUX_MODE
    if raw == "uniform":
        return UNIFORM_SURFACE_FLUX_MODE
    if raw in {
        UNIFORM_SURFACE_FLUX_MODE,
        DIFFERENTIAL_SURFACE_FORCING_MODE,
        DISABLED_SURFACE_FLUX_MODE,
    }:
        return str(raw)
    raise ValueError(f"Unknown surface forcing mode: {raw}")


def resolve_surface_forcing_patch(
    *,
    payload: dict[str, Any],
    mode: str,
    background_heat_flux_k_m_s: float,
    background_moisture_flux_g_g_m_s: float,
    domain_x_m: float,
    domain_y_m: float,
    dx_m: float,
    dy_m: float,
    duration_seconds: int,
) -> SurfaceForcingPatch | None:
    if mode != DIFFERENTIAL_SURFACE_FORCING_MODE:
        return None

    shape = _shape_payload(payload)
    radius_x = _radius_payload(payload, "x", shape)
    radius_y = _radius_payload(payload, "y", shape)
    if shape == "circle":
        _validate_circle_radius_payload(payload, radius_x)
    center_x = _float_payload(payload, "surface_patch_center_x_m", "patch center x", default=0.0)
    center_y = _float_payload(payload, "surface_patch_center_y_m", "patch center y", default=0.0)
    taper_width = _float_payload(
        payload,
        "surface_patch_taper_width_m",
        "patch taper width",
        default=DEFAULT_PATCH_TAPER_WIDTH_M,
    )
    ramp_seconds = _float_payload(
        payload,
        "surface_patch_ramp_seconds",
        "patch ramp seconds",
        default=DEFAULT_PATCH_RAMP_SECONDS,
    )
    heat_perturbation = _float_payload(
        payload,
        "surface_patch_heat_flux_perturbation_k_m_s",
        "patch heat-flux perturbation",
        default=DEFAULT_PATCH_HEAT_FLUX_PERTURBATION_K_M_S,
    )
    moisture_perturbation = _float_payload(
        payload,
        "surface_patch_moisture_flux_perturbation_g_g_m_s",
        "patch moisture-flux perturbation",
        default=DEFAULT_PATCH_MOISTURE_FLUX_PERTURBATION_G_G_M_S,
    )

    _validate_patch_geometry(
        center_x_m=center_x,
        center_y_m=center_y,
        radius_x_m=radius_x,
        radius_y_m=radius_y,
        taper_width_m=taper_width,
        domain_x_m=domain_x_m,
        domain_y_m=domain_y_m,
        dx_m=dx_m,
        dy_m=dy_m,
    )
    _validate_patch_forcing(
        heat_perturbation_k_m_s=heat_perturbation,
        moisture_perturbation_g_g_m_s=moisture_perturbation,
        ramp_seconds=ramp_seconds,
        duration_seconds=duration_seconds,
    )

    caveats = [
        "differential_surface_forcing_patch_not_real_land_surface_or_radiation",
        "differential_surface_forcing_patch_requires_cm1_source_customization",
        "differential_surface_forcing_patch_applies_in_sfcphys_flux_path",
        "differential_surface_forcing_v0_supports_circle_patch_only",
        "differential_surface_forcing_patch_requires_emitted_flux_and_convergence_validation",
    ]
    base_payload: dict[str, object] = {
        "schema_version": "surface_forcing_patch_v0",
        "shape": shape,
        "center_x_m": center_x,
        "center_y_m": center_y,
        "radius_x_m": radius_x,
        "radius_y_m": radius_y,
        "taper_function": "raised_cosine",
        "taper_width_m": taper_width,
        "ramp_seconds": ramp_seconds,
        "background_heat_flux_k_m_s": background_heat_flux_k_m_s,
        "background_moisture_flux_g_g_m_s": background_moisture_flux_g_g_m_s,
        "heat_flux_perturbation_k_m_s": heat_perturbation,
        "moisture_flux_perturbation_g_g_m_s": moisture_perturbation,
        "domain_x_m": domain_x_m,
        "domain_y_m": domain_y_m,
        "dx_m": dx_m,
        "dy_m": dy_m,
        "support_status": "requires_cm1_source_customization",
        "cm1_application_status": "source_customization_required_at_launch",
        "caveats": caveats,
    }
    return SurfaceForcingPatch.model_validate(
        {
            **base_payload,
            "pattern_sha256": _sha256_payload(base_payload),
        }
    )


def surface_forcing_patch_artifact(patch: SurfaceForcingPatch) -> dict[str, object]:
    payload = patch.model_dump(mode="json")
    return {
        "schema_version": patch.schema_version,
        "surface_flux_mode": DIFFERENTIAL_SURFACE_FORCING_MODE,
        "cm1_application_status": patch.cm1_application_status,
        "cm1_application_note": DIFFERENTIAL_SURFACE_FORCING_APPLICATION_NOTE,
        "cm1_patch_data_filename": SURFACE_FORCING_PATCH_FILENAME,
        "cm1_source_customization_filename": CM1_SOURCE_CUSTOMIZATION_FILENAME,
        "pattern_sha256": patch.pattern_sha256,
        "pattern": payload,
        "application_notes": [
            "This is a Cloud Chamber declarative lower-boundary forcing pattern.",
            (
                "CM1 namelist.input preserves the background constant-flux values. "
                "The spatial perturbation is applied by Cloud Chamber's local CM1 "
                "source customization before launch."
            ),
            (
                "The generated namelist keeps CM1's normal surface-initialization path. "
                "The prescribed heat/moisture flux patch is applied in sfcphys.F where "
                "CM1 writes thflux/qvflux for set_flx=1."
            ),
        ],
    }


def surface_forcing_patch_data_text(patch: SurfaceForcingPatch) -> str:
    """Render the small runtime file read by the CM1 source customization."""

    values = [
        patch.background_heat_flux_k_m_s,
        patch.background_moisture_flux_g_g_m_s,
        patch.heat_flux_perturbation_k_m_s,
        patch.moisture_flux_perturbation_g_g_m_s,
        patch.center_x_m,
        patch.center_y_m,
        patch.radius_x_m,
        patch.radius_y_m,
        patch.taper_width_m,
        patch.ramp_seconds,
    ]
    return (
        "# Cloud Chamber surface forcing patch v0\n"
        "# bg_h bg_q delta_h delta_q center_x center_y radius_x radius_y taper_width ramp_seconds\n"
        + " ".join(f"{value:.12e}" for value in values)
        + "\n"
    )


def surface_forcing_patch_data_sha256(patch: SurfaceForcingPatch) -> str:
    return hashlib.sha256(surface_forcing_patch_data_text(patch).encode("utf-8")).hexdigest()


def cm1_source_customization_artifact(patch: SurfaceForcingPatch) -> dict[str, object]:
    return {
        "schema_version": "cm1_source_customization_v0",
        "surface_flux_mode": DIFFERENTIAL_SURFACE_FORCING_MODE,
        "surface_patch_sha256": patch.pattern_sha256,
        "runtime_patch_file_sha256": surface_forcing_patch_data_sha256(patch),
        "runtime_patch_file": SURFACE_FORCING_PATCH_FILENAME,
        "required_targets": [
            {
                "relative_path": "src/sfcphys.F",
                "purpose": (
                    "Read the per-run patch file and apply a raised-cosine heat/moisture "
                    "flux perturbation to thflux/qvflux when set_flx=1."
                ),
                "marker": "CLOUD_CHAMBER_SURFACE_FORCING_PATCH_V0_SFCPHYS",
            },
        ],
        "application_policy": {
            "no_silent_uniform_fallback": True,
            "isolated_runtime_build_tree": True,
            "backup_original_source": False,
            "rebuild_cm1_executable": True,
            "copy_custom_executable_to_run_directory": True,
            "cm1_source_committed_to_repo": False,
        },
    }


def surface_forcing_patch_summary(patch: SurfaceForcingPatch) -> str:
    return (
        "Differential warm/moist surface patch; source customization required at launch; "
        f"background H {patch.background_heat_flux_k_m_s:.3g} K m/s, "
        f"M {patch.background_moisture_flux_g_g_m_s:.3g} g/g m/s; "
        f"patch +H {patch.heat_flux_perturbation_k_m_s:.3g} K m/s, "
        f"+M {patch.moisture_flux_perturbation_g_g_m_s:.3g} g/g m/s; "
        f"{patch.radius_x_m:.0f} x {patch.radius_y_m:.0f} m {patch.shape}"
    )


def _shape_payload(payload: dict[str, Any]) -> Literal["circle"]:
    raw = payload.get("surface_patch_shape", "circle")
    if raw == "circle":
        return cast(Literal["circle"], raw)
    if raw == "ellipse":
        raise ValueError(
            "Differential surface forcing v0 supports circle patches only. "
            "Ellipse support needs physical-coordinate taper validation before it is safe."
        )
    raise ValueError(f"Unknown surface patch shape: {raw}")


def _radius_payload(payload: dict[str, Any], axis: Literal["x", "y"], shape: str) -> float:
    if shape == "circle":
        return _float_payload(
            payload,
            "surface_patch_radius_m",
            "patch radius",
            default=DEFAULT_PATCH_RADIUS_M,
        )
    raise ValueError(f"Unknown surface patch shape for radius {axis}: {shape}")


def _validate_circle_radius_payload(payload: dict[str, Any], radius_m: float) -> None:
    for key in ("surface_patch_radius_x_m", "surface_patch_radius_y_m"):
        if key not in payload:
            continue
        axis_radius = _float_payload(payload, key, key, default=radius_m)
        if not math.isclose(axis_radius, radius_m, rel_tol=0.0, abs_tol=1.0e-9):
            raise ValueError(
                "Differential surface forcing v0 supports circle patches only; use "
                "surface_patch_radius_m instead of separate x/y radii."
            )


def _float_payload(
    payload: dict[str, Any],
    key: str,
    label: str,
    *,
    default: float,
) -> float:
    value = payload.get(key, default)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"Unknown {label}: {value}") from exc
    elif isinstance(value, int | float):
        parsed = float(value)
    else:
        raise ValueError(f"Unknown {label}: {value}")
    if not math.isfinite(parsed):
        raise ValueError(f"Invalid {label}: must be finite")
    return parsed


def _validate_patch_geometry(
    *,
    center_x_m: float,
    center_y_m: float,
    radius_x_m: float,
    radius_y_m: float,
    taper_width_m: float,
    domain_x_m: float,
    domain_y_m: float,
    dx_m: float,
    dy_m: float,
) -> None:
    if radius_x_m <= 0 or radius_y_m <= 0:
        raise ValueError("Invalid patch radius: radii must be greater than zero")
    if taper_width_m <= 0:
        raise ValueError("Invalid patch taper width: must be greater than zero")
    if radius_x_m < MIN_PATCH_RADIUS_GRID_CELLS * dx_m:
        raise ValueError("Invalid patch radius x: patch must span at least 3 grid cells")
    if radius_y_m < MIN_PATCH_RADIUS_GRID_CELLS * dy_m:
        raise ValueError("Invalid patch radius y: patch must span at least 3 grid cells")
    if abs(center_x_m) + radius_x_m + taper_width_m > domain_x_m / 2:
        raise ValueError("Invalid patch geometry: x radius plus taper must fit inside domain")
    if abs(center_y_m) + radius_y_m + taper_width_m > domain_y_m / 2:
        raise ValueError("Invalid patch geometry: y radius plus taper must fit inside domain")


def _validate_patch_forcing(
    *,
    heat_perturbation_k_m_s: float,
    moisture_perturbation_g_g_m_s: float,
    ramp_seconds: float,
    duration_seconds: int,
) -> None:
    if heat_perturbation_k_m_s < 0 or moisture_perturbation_g_g_m_s < 0:
        raise ValueError(
            "Invalid patch perturbation: heat and moisture perturbations must be non-negative"
        )
    if heat_perturbation_k_m_s == 0 and moisture_perturbation_g_g_m_s == 0:
        raise ValueError("Invalid patch perturbation: at least one perturbation must be positive")
    if ramp_seconds <= 0:
        raise ValueError("Invalid patch ramp seconds: must be greater than zero")
    if ramp_seconds > duration_seconds:
        raise ValueError("Invalid patch ramp seconds: ramp must not exceed run duration")


def _sha256_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

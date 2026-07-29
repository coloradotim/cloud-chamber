"""Strict retained-output validation for Trade Cumulus Recipe variations."""

from __future__ import annotations

import math
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from cloud_chamber.generated_input_identity import (
    GeneratedInputIdentityError,
    verify_generated_input_identity,
)
from cloud_chamber.result_ingest import ResultMetadata
from cloud_chamber.run_cost import ExactNumericalDomain
from cloud_chamber.run_manifest import LifecycleState, RunManifest
from cloud_chamber.trade_cumulus_attempt_provenance import (
    TradeCumulusAttemptProvenanceError,
    validate_trade_cumulus_attempt_provenance,
)
from cloud_chamber.trade_cumulus_recipes import TradeCumulusControls, normalize_controls
from cloud_chamber.variation_envelope import VariationEnvelope, canonical_payload_sha256


class TradeCumulusOutputValidationError(ValueError):
    """Raised when retained output cannot support an available Simulation."""


_VALIDATION_CACHE: OrderedDict[tuple[object, ...], dict[str, Any]] = OrderedDict()
_MAX_CACHE_ENTRIES = 16
_TIME_TOLERANCE_SECONDS = 1.0e-3
_REQUIRED_UNITS = {
    "ql": ("kg kg-1", "kg/kg", "kg kg^-1"),
    "qv": ("kg kg-1", "kg/kg", "kg kg^-1"),
    "th": ("k",),
    "prs": ("pa",),
    "rho": ("kg m-3", "kg/m3", "kg/m^3", "kg m^-3"),
    "hfx": ("w m-2", "w/m2", "w/m^2", "w m^-2"),
    "qfx": ("kg m-2 s-1", "kg/m2/s", "kg/m^2/s", "kg m^-2 s^-1"),
    "u": ("m s-1", "m/s", "m s^-1"),
    "v": ("m s-1", "m/s", "m s^-1"),
    "w": ("m s-1", "m/s", "m s^-1"),
}
_ALIASES = {
    "u": ("u", "uinterp"),
    "v": ("v", "vinterp"),
    "w": ("w", "winterp"),
}


def validate_trade_cumulus_variation_outputs(
    manifest: RunManifest,
    metadata: ResultMetadata,
) -> dict[str, Any]:
    """Validate one ingested Recipe variation and cache by retained artifact identity."""
    paths = [Path(path).expanduser() for path in metadata.model_output_paths]
    key = (
        manifest.run_id,
        manifest.updated_at.isoformat(),
        metadata.updated_at.isoformat(),
        tuple(_path_fingerprint(path) for path in paths),
        tuple(_generated_input_fingerprints(manifest)),
        canonical_payload_sha256(manifest.cm1_source_customization_status),
    )
    cached = _VALIDATION_CACHE.get(key)
    if cached is not None:
        _VALIDATION_CACHE.move_to_end(key)
        return cached

    report = _validate_uncached(manifest, metadata, paths)
    _VALIDATION_CACHE[key] = report
    _VALIDATION_CACHE.move_to_end(key)
    while len(_VALIDATION_CACHE) > _MAX_CACHE_ENTRIES:
        _VALIDATION_CACHE.popitem(last=False)
    return report


def clear_trade_cumulus_output_validation_cache() -> None:
    """Clear bounded validation state for deterministic tests."""
    _VALIDATION_CACHE.clear()


def _validate_uncached(
    manifest: RunManifest,
    metadata: ResultMetadata,
    paths: list[Path],
) -> dict[str, Any]:
    if manifest.lifecycle_state not in {
        LifecycleState.COMPLETED,
        LifecycleState.INGESTED,
        LifecycleState.SAVED,
    }:
        raise TradeCumulusOutputValidationError(
            "Trade Cumulus availability requires a completed or ingested attempt."
        )
    if manifest.execution.exit_code != 0 or manifest.execution.finished_at is None:
        raise TradeCumulusOutputValidationError(
            "Trade Cumulus availability requires normal CM1 completion."
        )
    try:
        verified_inputs = verify_generated_input_identity(manifest)
    except (OSError, ValueError, GeneratedInputIdentityError) as exc:
        raise TradeCumulusOutputValidationError(
            "Generated inputs changed after the reviewed package was created."
        ) from exc

    envelope = _variation_envelope(manifest)
    numerical = _exact_numerical_domain(envelope)
    controls = _retained_controls(envelope)
    try:
        provenance_report = validate_trade_cumulus_attempt_provenance(manifest)
    except TradeCumulusAttemptProvenanceError as exc:
        raise TradeCumulusOutputValidationError(str(exc)) from exc
    observation = envelope.observation_plan.payload
    expected_duration = observation.get("duration_seconds")
    expected_count = observation.get("expected_history_count")
    expected_cadence = observation.get("output_cadence_seconds")
    expected_fields = observation.get("retained_field_inventory")
    if not isinstance(expected_count, int) or expected_count <= 0:
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks an exact expected history count."
        )
    if not isinstance(expected_cadence, int | float) or expected_cadence <= 0:
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks an exact output cadence."
        )
    if not isinstance(expected_duration, int | float) or expected_duration < 0:
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks an exact modeled duration."
        )
    expected_times = [float(index) * float(expected_cadence) for index in range(expected_count)]
    if (
        not math.isclose(
            expected_times[-1],
            float(expected_duration),
            rel_tol=0.0,
            abs_tol=_TIME_TOLERANCE_SECONDS,
        )
        or len(expected_times) != expected_count
    ):
        raise TradeCumulusOutputValidationError(
            "The reviewed duration, cadence, and history count are inconsistent."
        )
    if not isinstance(expected_fields, list | tuple) or not all(
        isinstance(field, str) for field in expected_fields
    ):
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks a required field inventory."
        )
    if len(paths) != expected_count:
        raise TradeCumulusOutputValidationError(
            f"Expected {expected_count} native histories but found {len(paths)}."
        )
    if metadata.model_output_file_count not in {0, len(paths)}:
        raise TradeCumulusOutputValidationError(
            "Ingested output inventory disagrees with the retained histories."
        )
    if metadata.missing_required_output_fields:
        raise TradeCumulusOutputValidationError(
            "Ingested output is missing required fields: "
            + ", ".join(metadata.missing_required_output_fields)
        )

    times: list[float] = []
    scalar_dimensions: tuple[str, str, str] | None = None
    resolved_fields: dict[str, str] = {}
    run_dir = Path(manifest.generated_inputs.run_directory).expanduser().resolve()
    surface_readbacks: list[dict[str, float]] = []
    for path in paths:
        resolved_path = path.resolve()
        if not resolved_path.is_relative_to(run_dir):
            raise TradeCumulusOutputValidationError(
                f"Required native history escapes the accepted attempt directory: {path.name}."
            )
        if not path.is_file():
            raise TradeCumulusOutputValidationError(
                f"Required native history is unavailable: {path.name}."
            )
        try:
            dataset = xr.open_dataset(path, decode_times=False)
        except (OSError, ValueError) as exc:
            raise TradeCumulusOutputValidationError(
                f"Native history {path.name} is unreadable."
            ) from exc
        try:
            local_times = _time_values(dataset, path)
            times.extend(local_times)
            frame_dimensions = _validate_fields(
                dataset,
                expected_fields=tuple(expected_fields),
                path=path,
                resolved_fields=resolved_fields,
            )
            if scalar_dimensions is None:
                scalar_dimensions = frame_dimensions
            elif scalar_dimensions != frame_dimensions:
                raise TradeCumulusOutputValidationError(
                    "Native histories do not share one scalar-grid dimension order."
                )
            _validate_coordinates(dataset, frame_dimensions, path, numerical)
            surface_readbacks.append(_validate_surface_flux_readback(dataset, path, controls))
        finally:
            dataset.close()

    if len(times) != expected_count:
        raise TradeCumulusOutputValidationError(
            f"Expected {expected_count} modeled times but found {len(times)}."
        )
    if any(not math.isfinite(value) for value in times):
        raise TradeCumulusOutputValidationError("Modeled times must be finite.")
    if any(right <= left for left, right in zip(times, times[1:], strict=False)):
        raise TradeCumulusOutputValidationError(
            "Modeled times must be unique and strictly increasing."
        )
    for actual, expected in zip(times, expected_times, strict=True):
        if not math.isclose(
            actual,
            expected,
            rel_tol=0.0,
            abs_tol=_TIME_TOLERANCE_SECONDS,
        ):
            raise TradeCumulusOutputValidationError(
                "Modeled times do not reproduce the exact reviewed timeline."
            )

    return {
        "passed": True,
        "history_count": len(paths),
        "time_count": len(times),
        "first_time_seconds": times[0],
        "last_time_seconds": times[-1],
        "output_cadence_seconds": float(expected_cadence),
        "resolved_fields": resolved_fields,
        "scalar_dimensions": list(scalar_dimensions or ()),
        "generated_input_hash_count": len(verified_inputs),
        "cloud_response_required": False,
        "numerical_realization": numerical.model_dump(mode="json"),
        "surface_flux_readback": surface_readbacks[-1],
        "attempt_provenance": provenance_report,
    }


def _variation_envelope(manifest: RunManifest) -> VariationEnvelope:
    payload = manifest.run_configuration.get("variation_envelope")
    try:
        envelope = VariationEnvelope.model_validate(payload)
    except ValueError as exc:
        raise TradeCumulusOutputValidationError(
            "The retained shared variation envelope is invalid."
        ) from exc
    if (
        envelope.world_id != "trade_cumulus"
        or envelope.recipe_id != "canonical_bomex_trade_cumulus"
        or envelope.recipe_contract_version != "1"
    ):
        raise TradeCumulusOutputValidationError(
            "The retained output is outside the current Trade Cumulus Recipe contract."
        )
    return envelope


def _validate_fields(
    dataset: xr.Dataset,
    *,
    expected_fields: tuple[str, ...],
    path: Path,
    resolved_fields: dict[str, str],
) -> tuple[str, str, str]:
    ql_name = _field_name(dataset, "ql")
    ql = _without_time(dataset[ql_name])
    dimensions = _scalar_dimensions(ql, path)
    for field in expected_fields:
        name = _field_name(dataset, field)
        data = _without_time(dataset[name])
        if data.ndim < 2:
            raise TradeCumulusOutputValidationError(
                f"Required field {name} in {path.name} has unsupported dimensions."
            )
        values = np.asarray(data.values)
        if not np.issubdtype(values.dtype, np.number):
            raise TradeCumulusOutputValidationError(
                f"Required field {name} in {path.name} is not numeric."
            )
        if not np.all(np.isfinite(values)):
            raise TradeCumulusOutputValidationError(
                f"Required field {name} in {path.name} contains nonfinite values."
            )
        resolved_fields[field] = name
        if field in _REQUIRED_UNITS:
            _validate_units(name, data, path, _REQUIRED_UNITS[field])
    for lens_field in ("ql", "u", "v", "w"):
        name = _field_name(dataset, lens_field)
        data = _without_time(dataset[name])
        values = np.asarray(data.values)
        if not np.all(np.isfinite(values)):
            raise TradeCumulusOutputValidationError(
                f"Updraft Lens field {name} in {path.name} contains nonfinite values."
            )
        if lens_field in _REQUIRED_UNITS:
            _validate_units(name, data, path, _REQUIRED_UNITS[lens_field])
        resolved_fields[lens_field] = name
    return dimensions


def _field_name(dataset: xr.Dataset, field: str) -> str:
    candidates = _ALIASES.get(field, (field,))
    name = next((candidate for candidate in candidates if candidate in dataset.data_vars), None)
    if name is None:
        raise TradeCumulusOutputValidationError(f"Required native field {field} is absent.")
    return name


def _without_time(data: xr.DataArray) -> xr.DataArray:
    time_dimension = next(
        (dimension for dimension in data.dims if str(dimension).lower() in {"time", "t"}),
        None,
    )
    return data.isel({time_dimension: 0}, drop=True) if time_dimension else data


def _scalar_dimensions(data: xr.DataArray, path: Path) -> tuple[str, str, str]:
    if data.ndim != 3:
        raise TradeCumulusOutputValidationError(
            f"Cloud liquid in {path.name} is not a native three-dimensional scalar field."
        )
    names = tuple(str(dimension) for dimension in data.dims)
    z = next((dimension for dimension in names if dimension.lower().startswith("z")), None)
    y = next((dimension for dimension in names if dimension.lower().startswith("y")), None)
    x = next((dimension for dimension in names if dimension.lower().startswith("x")), None)
    if z is None or y is None or x is None or len({z, y, x}) != 3:
        raise TradeCumulusOutputValidationError(
            f"Cloud liquid in {path.name} lacks native x/y/z dimensions."
        )
    return z, y, x


def _validate_coordinates(
    dataset: xr.Dataset,
    dimensions: tuple[str, str, str],
    path: Path,
    numerical: ExactNumericalDomain,
) -> None:
    expected = {
        dimensions[0]: (
            numerical.nz,
            numerical.dz_m,
            numerical.model_top_m,
            0.0,
            numerical.model_top_m,
        ),
        dimensions[1]: (
            numerical.ny,
            numerical.dy_m,
            numerical.y_extent_m,
            numerical.y_min_m,
            numerical.y_max_m,
        ),
        dimensions[2]: (
            numerical.nx,
            numerical.dx_m,
            numerical.x_extent_m,
            numerical.x_min_m,
            numerical.x_max_m,
        ),
    }
    for dimension in dimensions:
        if dimension not in dataset.coords:
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} is absent from {path.name}."
            )
        values = np.asarray(dataset.coords[dimension].values, dtype=float)
        if values.ndim != 1 or not values.size or not np.all(np.isfinite(values)):
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} is invalid."
            )
        if values.size > 1 and not np.all(np.diff(values) > 0):
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} is not strictly increasing."
            )
        units = str(dataset.coords[dimension].attrs.get("units", "")).strip().lower()
        if units not in {"m", "meter", "meters", "km", "kilometer", "kilometers"}:
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} lacks length units."
            )
        values_m = values * 1_000.0 if units.startswith("km") else values
        (
            expected_count,
            expected_spacing_m,
            expected_extent_m,
            expected_lower_edge_m,
            expected_upper_edge_m,
        ) = expected[dimension]
        if values_m.size != expected_count:
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} does not match the reviewed grid."
            )
        if values_m.size > 1 and not np.allclose(
            np.diff(values_m),
            expected_spacing_m,
            rtol=0.0,
            atol=max(1.0e-4, expected_spacing_m * 1.0e-5),
        ):
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} does not match reviewed spacing."
            )
        actual_extent_m = (
            expected_spacing_m
            if values_m.size == 1
            else float(values_m[-1] - values_m[0] + expected_spacing_m)
        )
        if not math.isclose(
            actual_extent_m,
            expected_extent_m,
            rel_tol=0.0,
            abs_tol=max(1.0e-3, expected_spacing_m * 1.0e-4),
        ):
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} does not match reviewed extent."
            )
        lower_edge_m = float(values_m[0] - 0.5 * expected_spacing_m)
        upper_edge_m = float(values_m[-1] + 0.5 * expected_spacing_m)
        if not math.isclose(
            lower_edge_m,
            expected_lower_edge_m,
            rel_tol=0.0,
            abs_tol=max(1.0e-3, expected_spacing_m * 1.0e-4),
        ) or not math.isclose(
            upper_edge_m,
            expected_upper_edge_m,
            rel_tol=0.0,
            abs_tol=max(1.0e-3, expected_spacing_m * 1.0e-4),
        ):
            label = (
                "the reviewed model top" if dimension == dimensions[0] else "reviewed domain bounds"
            )
            raise TradeCumulusOutputValidationError(
                f"Native coordinate {dimension} in {path.name} does not match {label}."
            )


def _exact_numerical_domain(envelope: VariationEnvelope) -> ExactNumericalDomain:
    try:
        return ExactNumericalDomain.model_validate(
            envelope.numerical_realization.payload.get("exact_domain")
        )
    except ValueError as exc:
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks an exact numerical realization."
        ) from exc


def _retained_controls(envelope: VariationEnvelope) -> TradeCumulusControls:
    try:
        return normalize_controls(
            TradeCumulusControls.model_validate(envelope.world_payload.get("controls"))
        )
    except ValueError as exc:
        raise TradeCumulusOutputValidationError(
            "The retained envelope lacks valid absolute Trade Cumulus controls."
        ) from exc


def _validate_surface_flux_readback(
    dataset: xr.Dataset,
    path: Path,
    controls: TradeCumulusControls,
) -> dict[str, float]:
    for field in ("rho", "hfx", "qfx"):
        name = _field_name(dataset, field)
        data = _without_time(dataset[name])
        _validate_units(name, data, path, _REQUIRED_UNITS[field])
    rho = _without_time(dataset[_field_name(dataset, "rho")])
    z_dimension = next(
        (dimension for dimension in rho.dims if str(dimension).lower().startswith("z")),
        None,
    )
    if z_dimension is None:
        raise TradeCumulusOutputValidationError(
            f"Density in {path.name} lacks a native vertical dimension."
        )
    surface_density = np.asarray(rho.isel({z_dimension: 0}).values, dtype=float)
    hfx = np.asarray(_without_time(dataset[_field_name(dataset, "hfx")]).values, dtype=float)
    qfx = np.asarray(_without_time(dataset[_field_name(dataset, "qfx")]).values, dtype=float)
    if (
        surface_density.shape != hfx.shape
        or surface_density.shape != qfx.shape
        or not np.all(np.isfinite(surface_density))
        or np.any(surface_density <= 0.0)
    ):
        raise TradeCumulusOutputValidationError(
            f"Surface-flux diagnostics in {path.name} do not share a valid native grid."
        )
    implied_heat = hfx / (surface_density * 1_004.0)
    implied_moisture = qfx / surface_density * 1_000.0
    if not np.allclose(
        implied_heat,
        controls.surface_sensible_heat_flux_k_m_s,
        rtol=0.02,
        atol=1.0e-7,
    ):
        raise TradeCumulusOutputValidationError(
            f"Retained sensible-heat flux in {path.name} does not match the reviewed target."
        )
    if not np.allclose(
        implied_moisture,
        controls.surface_moisture_flux_g_kg_m_s,
        rtol=0.02,
        atol=1.0e-6,
    ):
        raise TradeCumulusOutputValidationError(
            f"Retained moisture flux in {path.name} does not match the reviewed target."
        )
    return {
        "surface_sensible_heat_flux_k_m_s": float(np.mean(implied_heat)),
        "surface_moisture_flux_g_kg_m_s": float(np.mean(implied_moisture)),
    }


def _validate_units(
    field: str,
    data: xr.DataArray,
    path: Path,
    accepted: tuple[str, ...],
) -> None:
    units = str(data.attrs.get("units", "")).strip().lower()
    normalized = units.replace("**", "^").replace(" ", "")
    normalized_accepted = {
        candidate.replace("**", "^").replace(" ", "").lower() for candidate in accepted
    }
    if normalized not in normalized_accepted:
        raise TradeCumulusOutputValidationError(
            f"Required field {field} in {path.name} has unsupported units {units or 'missing'}."
        )


def _time_values(dataset: xr.Dataset, path: Path) -> list[float]:
    if "time" not in dataset.coords and "time" not in dataset.variables:
        raise TradeCumulusOutputValidationError(f"Native history {path.name} lacks modeled time.")
    raw = np.asarray(dataset["time"].values, dtype=float).reshape(-1)
    if raw.size != 1:
        raise TradeCumulusOutputValidationError(
            f"Native history {path.name} must contain exactly one saved modeled time."
        )
    units = str(dataset["time"].attrs.get("units", "")).strip().lower()
    if units not in {"s", "sec", "secs", "second", "seconds"}:
        raise TradeCumulusOutputValidationError(f"Modeled time in {path.name} lacks seconds units.")
    return [float(raw[0])]


def _path_fingerprint(path: Path) -> tuple[str, int | None, int | None]:
    try:
        stat = path.stat()
    except OSError:
        return str(path), None, None
    return str(path), stat.st_size, stat.st_mtime_ns


def _generated_input_fingerprints(
    manifest: RunManifest,
) -> list[tuple[str, int | None, int | None]]:
    values = [
        manifest.generated_inputs.namelist_input,
        manifest.generated_inputs.input_sounding,
        manifest.generated_inputs.cm1_source_customization,
    ]
    fingerprints = [_path_fingerprint(Path(value).expanduser()) for value in values if value]
    status = manifest.cm1_source_customization_status
    if isinstance(status, dict):
        executable = status.get("custom_executable")
        if isinstance(executable, str) and executable:
            fingerprints.append(_path_fingerprint(Path(executable).expanduser()))
    return fingerprints

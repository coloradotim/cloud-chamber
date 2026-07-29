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
from cloud_chamber.run_manifest import LifecycleState, RunManifest
from cloud_chamber.variation_envelope import VariationEnvelope


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
    observation = envelope.observation_plan.payload
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
    for path in paths:
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
            _validate_coordinates(dataset, frame_dimensions, path)
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
    for left, right in zip(times, times[1:], strict=False):
        if not math.isclose(
            right - left,
            float(expected_cadence),
            rel_tol=0.0,
            abs_tol=_TIME_TOLERANCE_SECONDS,
        ):
            raise TradeCumulusOutputValidationError(
                "Modeled times do not reproduce the reviewed output cadence."
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
) -> None:
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
    return [_path_fingerprint(Path(value).expanduser()) for value in values if value]

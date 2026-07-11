"""CM1 run progress summaries for Build status surfaces."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cloud_chamber.run_manifest import LifecycleState, RunManifest

CM1_MODEL_MINUTE_RE = re.compile(
    r"(?m)^\s*\d+\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s+min\s*$"
)
TAIL_BYTES = 2_000_000
TERMINAL_STATES = {
    LifecycleState.COMPLETED,
    LifecycleState.FAILED,
    LifecycleState.CANCELED,
    LifecycleState.INGESTED,
    LifecycleState.SAVED,
}


def run_progress_from_manifest(
    manifest: RunManifest,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return bounded progress metadata from manifest config and CM1 stdout."""

    checked_at = _utc(now or datetime.now(UTC))
    caveats: list[str] = []
    total_model_time, total_source, total_caveats = _configured_model_time_seconds(manifest)
    caveats.extend(total_caveats)
    model_time, model_source = _latest_model_time_seconds(manifest)

    if (
        manifest.lifecycle_state in {LifecycleState.COMPLETED, LifecycleState.INGESTED}
        and manifest.execution.exit_code == 0
        and total_model_time is not None
    ):
        model_time = total_model_time
        model_source = "completed_run_state"

    elapsed = _elapsed_wall_seconds(manifest, checked_at)
    percent = _percent_complete(model_time, total_model_time)
    remaining = _estimated_remaining_wall_seconds(
        elapsed_wall_seconds=elapsed,
        model_time_seconds=model_time,
        total_model_time_seconds=total_model_time,
        lifecycle_state=manifest.lifecycle_state,
    )
    finish_at = checked_at + timedelta(seconds=remaining) if remaining is not None else None

    return {
        "elapsed_wall_seconds": elapsed,
        "model_time_seconds": model_time,
        "total_model_time_seconds": total_model_time,
        "percent_complete": percent,
        "estimated_remaining_wall_seconds": remaining,
        "estimated_finish_at": _isoformat_z(finish_at) if finish_at else None,
        "last_refreshed_at": _isoformat_z(checked_at),
        "stale": False,
        "model_time_source": model_source,
        "total_model_time_source": total_source,
        "unavailable_reason": _unavailable_reason(manifest, model_time, total_model_time),
        "caveats": caveats,
    }


def _configured_model_time_seconds(
    manifest: RunManifest,
) -> tuple[float | None, str | None, list[str]]:
    namelist_path = manifest.generated_inputs.namelist_input
    if namelist_path:
        value = _namelist_float(Path(namelist_path).expanduser(), "timax")
        if value is not None and math.isfinite(value) and value > 0:
            return value, "namelist.input timax", []

    values = manifest.run_configuration.get("cm1_values", {})
    if not isinstance(values, dict):
        values = {}
    runtime_seconds = values.get("runtime_seconds")
    if runtime_seconds is None:
        runtime_seconds = manifest.run_configuration.get("duration_seconds")
    try:
        configured_seconds = (
            float(runtime_seconds) if isinstance(runtime_seconds, str | int | float) else math.nan
        )
    except (TypeError, ValueError):
        configured_seconds = math.nan
    if not math.isfinite(configured_seconds) or configured_seconds <= 0:
        return (
            None,
            None,
            ["configured_model_time_missing_from_run_configuration"],
        )
    return (
        configured_seconds,
        "run_configuration",
        [],
    )


def _latest_model_time_seconds(manifest: RunManifest) -> tuple[float | None, str | None]:
    stdout_log = manifest.execution.stdout_log
    if not stdout_log:
        return None, None
    latest_minutes = _latest_cm1_model_minutes(Path(stdout_log).expanduser())
    if latest_minutes is None:
        return None, None
    return latest_minutes * 60.0, "stdout model-minute progress"


def _latest_cm1_model_minutes(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        text = _read_tail_text(path)
    except OSError:
        return None
    matches = CM1_MODEL_MINUTE_RE.findall(text)
    if not matches:
        return None
    try:
        latest = float(matches[-1])
    except ValueError:
        return None
    return latest if math.isfinite(latest) and latest >= 0 else None


def _namelist_float(path: Path, name: str) -> float | None:
    if not path.exists():
        return None
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    prefix = name.lower()
    for line in text.splitlines():
        stripped = line.split("!", 1)[0].strip()
        if not stripped.lower().startswith(prefix) or "=" not in stripped:
            continue
        value = stripped.split("=", 1)[1].split(",", 1)[0].strip()
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _elapsed_wall_seconds(manifest: RunManifest, now: datetime) -> float | None:
    if manifest.execution.started_at is None:
        return None
    started_at = _utc(manifest.execution.started_at)
    finished_at = _utc(manifest.execution.finished_at) if manifest.execution.finished_at else None
    end = finished_at if manifest.lifecycle_state in TERMINAL_STATES and finished_at else now
    elapsed = (end - started_at).total_seconds()
    return round(elapsed, 3) if math.isfinite(elapsed) and elapsed >= 0 else None


def _percent_complete(
    model_time_seconds: float | None,
    total_model_time_seconds: float | None,
) -> float | None:
    if (
        model_time_seconds is None
        or total_model_time_seconds is None
        or total_model_time_seconds <= 0
    ):
        return None
    percent = max(0.0, min(100.0, model_time_seconds / total_model_time_seconds * 100.0))
    return round(percent, 1)


def _estimated_remaining_wall_seconds(
    *,
    elapsed_wall_seconds: float | None,
    model_time_seconds: float | None,
    total_model_time_seconds: float | None,
    lifecycle_state: LifecycleState,
) -> float | None:
    if lifecycle_state in TERMINAL_STATES:
        return None
    if (
        elapsed_wall_seconds is None
        or model_time_seconds is None
        or total_model_time_seconds is None
        or model_time_seconds <= 0
        or total_model_time_seconds <= 0
    ):
        return None
    if elapsed_wall_seconds < 60 or model_time_seconds < 60:
        return None
    remaining_model_seconds = total_model_time_seconds - model_time_seconds
    if remaining_model_seconds <= 0:
        return None
    seconds_per_model_second = elapsed_wall_seconds / model_time_seconds
    remaining = remaining_model_seconds * seconds_per_model_second
    return round(remaining, 3) if math.isfinite(remaining) and remaining > 0 else None


def _unavailable_reason(
    manifest: RunManifest,
    model_time_seconds: float | None,
    total_model_time_seconds: float | None,
) -> str | None:
    if manifest.execution.started_at is None:
        return "Run has not started."
    if total_model_time_seconds is None:
        return "Configured model time is unavailable because timax could not be read."
    if model_time_seconds is None:
        return (
            "CM1 model-time progress is unavailable until stdout contains "
            "model-minute progress lines."
        )
    return None


def _read_tail_text(path: Path) -> str:
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > TAIL_BYTES:
            handle.seek(-TAIL_BYTES, 2)
        return handle.read().decode("utf-8", errors="replace")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _isoformat_z(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")

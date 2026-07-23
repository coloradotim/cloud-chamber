#!/usr/bin/env python3
"""Render issue #421's native-grid Gate B/presentation comparison evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "app" / "backend"
BACKEND_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"
if (
    BACKEND_PYTHON.exists()
    and Path(sys.executable).resolve() != BACKEND_PYTHON.resolve()
):
    os.execv(str(BACKEND_PYTHON), [str(BACKEND_PYTHON), __file__, *sys.argv[1:]])

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from PIL import Image  # noqa: E402

GATE_B_RUN_ID = "quarter-circle-supercell-official-20260722T142521Z"
PRESENTATION_RUN_ID = "quarter-circle-supercell-presentation-v1-20260723"
STORM_BOUNDS = (-40.0, 40.0, -45.0, 35.0)
W_BREAKS = (-30, -20, -8, -2, 2, 5, 10, 15, 20, 25, 30)
W_COLORS = (
    "#4b0082",
    "#0057d9",
    "#00c9d8",
    "#ffffff",
    "#00d63b",
    "#8fe000",
    "#ffe000",
    "#ff9800",
    "#ff3b00",
    "#c40000",
)
W_CMAP = ListedColormap(W_COLORS)
W_NORM = BoundaryNorm(W_BREAKS, W_CMAP.N)


@dataclass(frozen=True)
class PlanFrame:
    time_seconds: int
    x_km: np.ndarray
    y_km: np.ndarray
    w_m_s: np.ndarray
    cloud_g_kg: np.ndarray


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-home",
        type=Path,
        default=Path("~/CloudChamber").expanduser(),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    gate_b_dir = args.runtime_home.expanduser() / "runs" / GATE_B_RUN_ID
    presentation_dir = args.runtime_home.expanduser() / "runs" / PRESENTATION_RUN_ID
    _verify_completed_presentation(presentation_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    gate_b = _history_index(gate_b_dir)
    presentation = _history_index(presentation_dir)
    matched_path = args.output_dir / "matched-gate-b-presentation.png"
    later_path = args.output_dir / "presentation-later-evolution.png"
    cadence_path = args.output_dir / "cadence-comparison.gif"

    _render_matched(gate_b, presentation, matched_path)
    _render_later(presentation, later_path)
    _render_cadence(gate_b, presentation, cadence_path)
    diagnostics_path = args.output_dir / "presentation-frame-diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(_diagnostic_series(presentation), indent=2) + "\n"
    )
    summary = {
        "gate_b_run_id": GATE_B_RUN_ID,
        "presentation_run_id": PRESENTATION_RUN_ID,
        "rendering": {
            "field": "native winterp nearest 3.25 km",
            "cloud_boundary": "1000 * (qc + qr + qi + qs + qg) >= 0.05 g/kg",
            "viewport_bounds_km": {
                "x_min": STORM_BOUNDS[0],
                "x_max": STORM_BOUNDS[1],
                "y_min": STORM_BOUNDS[2],
                "y_max": STORM_BOUNDS[3],
            },
            "vertical_velocity_scale_m_s": list(W_BREAKS),
            "interpolation": "none",
        },
        "artifacts": [
            matched_path.name,
            later_path.name,
            cadence_path.name,
            diagnostics_path.name,
        ],
    }
    (args.output_dir / "native-review-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))
    return 0


def _verify_completed_presentation(run_dir: Path) -> None:
    evidence_path = run_dir / "supercell_presentation_evidence.json"
    try:
        evidence = json.loads(evidence_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("Validated presentation evidence is unavailable.") from exc
    if (
        evidence.get("kind") != "final"
        or evidence.get("run_id") != PRESENTATION_RUN_ID
        or evidence.get("normal_completion") is not True
        or evidence.get("history_count") != 91
    ):
        raise SystemExit("Presentation evidence is not accepted for review rendering.")


def _history_index(run_dir: Path) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in sorted(run_dir.glob("cm1out_[0-9]*.nc")):
        with xr.open_dataset(path, decode_times=False) as dataset:
            value = int(round(float(np.asarray(dataset["time"].values).reshape(-1)[0])))
        result[value] = path
    if not result:
        raise SystemExit(f"No numbered native histories found in {run_dir}.")
    return result


def _frame(path: Path) -> PlanFrame:
    with xr.open_dataset(path, decode_times=False) as dataset:
        time_seconds = int(
            round(float(np.asarray(dataset["time"].values).reshape(-1)[0]))
        )
        x = np.asarray(dataset["xh"].values, dtype=np.float64)
        y = np.asarray(dataset["yh"].values, dtype=np.float64)
        z = np.asarray(dataset["zh"].values, dtype=np.float64)
        level = int(np.argmin(np.abs(z - 3.25)))
        w = np.asarray(dataset["winterp"].isel(time=0, zh=level).values)
        cloud = sum(
            np.asarray(dataset[name].isel(time=0, zh=level).values)
            for name in ("qc", "qr", "qi", "qs", "qg")
        )
    mask_x = (x >= STORM_BOUNDS[0]) & (x <= STORM_BOUNDS[1])
    mask_y = (y >= STORM_BOUNDS[2]) & (y <= STORM_BOUNDS[3])
    return PlanFrame(
        time_seconds=time_seconds,
        x_km=x[mask_x],
        y_km=y[mask_y],
        w_m_s=w[np.ix_(mask_y, mask_x)],
        cloud_g_kg=1_000.0 * cloud[np.ix_(mask_y, mask_x)],
    )


def _diagnostic_series(inventory: dict[int, Path]) -> list[dict[str, int | float]]:
    diagnostics: list[dict[str, int | float]] = []
    for time_seconds, path in inventory.items():
        with xr.open_dataset(path, decode_times=False) as dataset:
            x = np.asarray(dataset["xh"].values, dtype=np.float64)
            y = np.asarray(dataset["yh"].values, dtype=np.float64)
            z = np.asarray(dataset["zh"].values, dtype=np.float64)
            w = np.asarray(dataset["winterp"].isel(time=0).values)
            primary = np.unravel_index(int(np.nanargmax(w)), w.shape)
            total = sum(
                np.asarray(dataset[name].isel(time=0).values)
                for name in ("qc", "qr", "qi", "qs", "qg")
            )
            rain_mm = 10.0 * np.asarray(dataset["rain"].isel(time=0).values)
            uh = np.asarray(dataset["uh"].isel(time=0).values)
            dbz = np.asarray(dataset["dbz"].isel(time=0).values)
        z_index, y_index, x_index = (int(value) for value in primary)
        diagnostics.append(
            {
                "time_seconds": time_seconds,
                "w_min_m_s": float(np.nanmin(w)),
                "w_max_m_s": float(np.nanmax(w)),
                "primary_x_km": float(x[x_index]),
                "primary_y_km": float(y[y_index]),
                "primary_z_km": float(z[z_index]),
                "total_condensate_max_g_kg": float(1_000.0 * np.nanmax(total)),
                "cloud_cell_count_ge_0_05_g_kg": int(
                    np.count_nonzero(total >= 0.00005)
                ),
                "reflectivity_max_dbz": float(np.nanmax(dbz)),
                "updraft_helicity_max_m2_s2": float(np.nanmax(uh)),
                "accumulated_rain_max_mm": float(np.nanmax(rain_mm)),
            }
        )
    return diagnostics


def _render_matched(
    gate_b: dict[int, Path],
    presentation: dict[int, Path],
    output: Path,
) -> None:
    source_times = (3_600, 5_400, 7_200)
    figure, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    for column, source_time in enumerate(source_times):
        presentation_time = _nearest_time(presentation, source_time)
        _draw_plan(
            axes[0, column],
            _frame(gate_b[source_time]),
            f"Gate B · {source_time // 60} min · 1 km",
        )
        _draw_plan(
            axes[1, column],
            _frame(presentation[presentation_time]),
            f"Presentation · {presentation_time // 60} min · 0.5 km",
        )
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(norm=W_NORM, cmap=W_CMAP),
        ax=axes,
        orientation="horizontal",
        shrink=0.56,
        pad=0.04,
    )
    colorbar.set_label("Vertical velocity at 3.25 km (m/s)")
    figure.suptitle(
        "Matched native-grid storm structure", fontsize=17, fontweight="bold"
    )
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _render_later(presentation: dict[int, Path], output: Path) -> None:
    times = (7_200, 8_400, 9_600, 10_800)
    figure, axes = plt.subplots(1, 4, figsize=(17, 4.8), constrained_layout=True)
    for axis, time_seconds in zip(axes, times, strict=True):
        _draw_plan(
            axis,
            _frame(presentation[time_seconds]),
            f"{time_seconds // 60} min",
        )
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(norm=W_NORM, cmap=W_CMAP),
        ax=axes,
        orientation="horizontal",
        shrink=0.52,
        pad=0.04,
    )
    colorbar.set_label("Vertical velocity at 3.25 km (m/s)")
    figure.suptitle("Presentation run later evolution", fontsize=17, fontweight="bold")
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _render_cadence(
    gate_b: dict[int, Path],
    presentation: dict[int, Path],
    output: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="supercell-cadence-") as temporary:
        frame_paths: list[Path] = []
        for index, presentation_time in enumerate(range(2_400, 7_201, 120)):
            gate_b_time = _nearest_time(gate_b, presentation_time)
            figure, axes = plt.subplots(1, 2, figsize=(10, 5), constrained_layout=True)
            _draw_plan(
                axes[0],
                _frame(gate_b[gate_b_time]),
                f"Gate B saved frame · {gate_b_time // 60} min",
            )
            _draw_plan(
                axes[1],
                _frame(presentation[presentation_time]),
                f"Presentation · {presentation_time // 60} min",
            )
            figure.suptitle(
                "15-minute source cadence versus 2-minute presentation cadence",
                fontsize=14,
                fontweight="bold",
            )
            frame_path = Path(temporary) / f"{index:03d}.png"
            figure.savefig(frame_path, dpi=105)
            plt.close(figure)
            frame_paths.append(frame_path)
        images = [
            Image.open(path).convert("P", palette=Image.Palette.ADAPTIVE)
            for path in frame_paths
        ]
        images[0].save(
            output,
            save_all=True,
            append_images=images[1:],
            duration=240,
            loop=0,
            optimize=True,
        )
        for image in images:
            image.close()


def _draw_plan(axis: plt.Axes, frame: PlanFrame, title: str) -> None:
    axis.pcolormesh(
        frame.x_km,
        frame.y_km,
        frame.w_m_s,
        cmap=W_CMAP,
        norm=W_NORM,
        shading="nearest",
        rasterized=True,
    )
    if np.nanmax(frame.cloud_g_kg) >= 0.05:
        axis.contour(
            frame.x_km,
            frame.y_km,
            frame.cloud_g_kg,
            levels=[0.05],
            colors=["#111820"],
            linewidths=1.0,
        )
    axis.set_xlim(STORM_BOUNDS[0], STORM_BOUNDS[1])
    axis.set_ylim(STORM_BOUNDS[2], STORM_BOUNDS[3])
    axis.set_aspect("equal", adjustable="box")
    axis.set_title(title)
    axis.set_xlabel("x (km)")
    axis.set_ylabel("y (km)")
    axis.grid(color="#dce6eb", linewidth=0.4)


def _nearest_time(inventory: dict[int, Path], target: int) -> int:
    return min(inventory, key=lambda value: abs(value - target))


if __name__ == "__main__":
    raise SystemExit(main())

/* eslint-disable react-refresh/only-export-components */
import type { MouseEvent as ReactMouseEvent } from "react";

export type UpdraftLensWindMode = "perturbation" | "total";
export type UpdraftLensOrientation = "horizontal" | "vertical_x" | "vertical_y";
export type UpdraftLensDimension = "x" | "y" | "z";

export type UpdraftLensWindVector = {
  x_km: number;
  y_km: number;
  z_km: number;
  u_m_s: number;
  v_m_s: number;
  magnitude_m_s: number;
};

export type UpdraftLensFrame = {
  result_id: string;
  time_index: number;
  time_seconds: number | null;
  orientation: UpdraftLensOrientation;
  plane_dimension: UpdraftLensDimension;
  plane_index: number;
  plane_coordinate: number | null;
  plane_units: string | null;
  dimension_order: UpdraftLensDimension[];
  x_indices: number[];
  x_values_km: number[];
  y_indices: number[];
  y_values_km: number[];
  z_indices: number[];
  z_values_km: number[];
  w_values_m_s: Array<Array<number | null>>;
  cloud_mask: boolean[][];
  cloud_threshold_kg_kg: number;
  w_range_min_m_s: number;
  w_range_max_m_s: number;
  w_range_method: string;
  w_scale_id: string;
  w_scale_owner: string;
  w_scale_type: "fixed_discrete";
  w_scale_units: "m/s";
  w_scale_breakpoints_m_s: number[];
  w_scale_colors: string[];
  w_scale_neutral_interval_m_s: number[];
  w_scale_source: string;
  w_scale_clipping_behavior: string;
  w_finite_count: number;
  w_low_clipped_count: number;
  w_high_clipped_count: number;
  w_low_clipped_fraction: number | null;
  w_high_clipped_fraction: number | null;
  wind_mode: UpdraftLensWindMode;
  wind_target_level_m: number;
  wind_actual_level_m: number;
  wind_level_index: number;
  wind_stride: number;
  wind_reference_m_s: number;
  wind_arrow_domain_fraction: number;
  domain_mean_u_m_s: number;
  domain_mean_v_m_s: number;
  wind_vectors: UpdraftLensWindVector[];
  provenance: {
    source_model: string;
    result_id: string;
    run_id: string;
    scenario_id: string;
    processing_method: string;
    rendering_method: string;
    provenance_label: string;
  };
  caveats: string[];
};

export type UpdraftLensPointSelection = {
  xIndex: number;
  yIndex: number;
  zIndex: number;
};

export type UpdraftLensDefaults = {
  result_id: string;
  case_id: string;
  eligible: boolean;
  primary_field: "w";
  cloud_field: "ql";
  orientation: "vertical_x";
  default_time_index: number;
  default_time_seconds: number | null;
  default_time_method: string;
  default_plane_dimension: "y";
  default_plane_index: number;
  default_plane_coordinate: number | null;
  default_plane_units: string | null;
  default_plane_method: string;
  cloud_threshold_kg_kg: number;
  w_range_min_m_s: number;
  w_range_max_m_s: number;
  w_range_method: string;
  w_scale_id: string;
  w_scale_owner: string;
  w_scale_type: "fixed_discrete";
  w_scale_units: "m/s";
  w_scale_breakpoints_m_s: number[];
  w_scale_colors: string[];
  w_scale_neutral_interval_m_s: number[];
  w_scale_source: string;
  w_scale_clipping_behavior: string;
  wind_target_level_m: number;
  wind_actual_level_m: number;
  wind_level_index: number;
  wind_default_mode: "perturbation";
  wind_stride: number;
  wind_shown_by_default: boolean;
  perturbation_wind_reference_m_s: number;
  total_wind_reference_m_s: number;
  wind_arrow_domain_fraction: number;
  provenance: UpdraftLensFrame["provenance"];
  caveats: string[];
};

type UpdraftLensSliceProps = {
  frame: UpdraftLensFrame;
  showCloudBoundary?: boolean;
  showLegend?: boolean;
  selectedPoint?: UpdraftLensPointSelection | null;
  onSelectPoint?: (selection: UpdraftLensPointSelection) => void;
};

type CellGeometry = {
  x: number;
  y: number;
  width: number;
  height: number;
};

const MISSING_COLOR = "#747b80";
const LEGACY_DOWNDRAFT_COLOR = "#2166ac";
const LEGACY_NEUTRAL_COLOR = "#f7f7f7";
const LEGACY_UPDRAFT_COLOR = "#b2182b";
const SCALE_TITLE = "Vertical velocity (w), m/s";
const INTERVAL_MEANINGS = [
  "strongest or clipped downdraft",
  "downdraft",
  "weak downdraft",
  "near-neutral motion",
  "weak updraft",
  "moderate updraft",
  "active updraft",
  "strong updraft",
  "very strong updraft",
  "exceptional or clipped updraft",
];

export function UpdraftLensSlice({
  frame,
  showCloudBoundary = true,
  showLegend = true,
  selectedPoint = null,
  onSelectPoint,
}: UpdraftLensSliceProps) {
  const rowDimension = frame.dimension_order[0] ?? "z";
  const columnDimension = frame.dimension_order[1] ?? "x";
  const rowValues = updraftLensCoordinateValues(frame, rowDimension);
  const columnValues = updraftLensCoordinateValues(frame, columnDimension);
  const columnEdges = coordinateEdges(columnValues);
  const rowEdges = coordinateEdges(rowValues);
  const columnMin = columnEdges[0] ?? 0;
  const columnMax = columnEdges.at(-1) ?? 1;
  const rowMin = rowEdges[0] ?? 0;
  const rowMax = rowEdges.at(-1) ?? 1;
  const width = Math.max(Number.EPSILON, columnMax - columnMin);
  const height = Math.max(Number.EPSILON, rowMax - rowMin);
  const boundaryPath = showCloudBoundary
    ? updraftLensBoundaryPath(frame.cloud_mask, columnEdges, rowEdges)
    : "";
  const selectedColumnIndex = selectedPoint
    ? updraftLensPointIndex(selectedPoint, columnDimension)
    : undefined;
  const selectedRowIndex = selectedPoint
    ? updraftLensPointIndex(selectedPoint, rowDimension)
    : undefined;
  const selectedColumn =
    selectedPoint &&
    updraftLensPointIndex(selectedPoint, frame.plane_dimension) === frame.plane_index &&
    selectedColumnIndex !== undefined
      ? columnValues[selectedColumnIndex]
      : undefined;
  const selectedRow =
    selectedPoint &&
    updraftLensPointIndex(selectedPoint, frame.plane_dimension) === frame.plane_index &&
    selectedRowIndex !== undefined
      ? rowValues[selectedRowIndex]
      : undefined;

  function handlePointer(event: ReactMouseEvent<SVGSVGElement>) {
    if (!onSelectPoint) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const selection = updraftLensSelectionFromPointer(
      event.clientX - bounds.left,
      event.clientY - bounds.top,
      bounds.width,
      bounds.height,
      columnValues,
      rowValues,
      frame.orientation,
      frame.plane_index,
    );
    if (selection) onSelectPoint(selection);
  }

  return (
    <section
      className={`updraft-lens-slice${showLegend ? "" : " updraft-lens-slice-without-legend"}`}
      aria-label="Updraft Lens slice"
    >
      <div className="updraft-lens-axis updraft-lens-axis-z" aria-hidden="true">
        <span>{formatKilometers(rowMax)}</span>
        <strong>{rowDimension} (km)</strong>
        <span>{formatKilometers(rowMin)}</span>
      </div>
      <div className="updraft-lens-plot-column">
        <svg
          className="updraft-lens-svg"
          role="img"
          aria-label={updraftLensAccessibleSummary(frame)}
          data-domain-aspect={(width / height).toFixed(6)}
          data-orientation={frame.orientation}
          viewBox={`${columnMin} ${rowMin} ${width} ${height}`}
          preserveAspectRatio="none"
          style={{ aspectRatio: `${width} / ${height}` }}
          shapeRendering="crispEdges"
          onClick={handlePointer}
        >
          <g transform={`translate(0 ${rowMin + rowMax}) scale(1 -1)`}>
            {frame.w_values_m_s.map((row, zIndex) =>
              row.map((value, xIndex) => {
                const geometry = updraftLensCellGeometry(columnEdges, rowEdges, xIndex, zIndex);
                return (
                  <rect
                    key={`${zIndex}-${xIndex}`}
                    data-cell={`${zIndex}-${xIndex}`}
                    x={geometry.x}
                    y={geometry.y}
                    width={geometry.width}
                    height={geometry.height}
                    fill={updraftLensDiscreteColor(
                      value,
                      frame.w_scale_breakpoints_m_s,
                      frame.w_scale_colors,
                    )}
                  />
                );
              }),
            )}
            {boundaryPath && (
              <path
                className="updraft-lens-cloud-boundary"
                data-testid="updraft-lens-cloud-boundary"
                d={boundaryPath}
                fill="none"
                vectorEffect="non-scaling-stroke"
              />
            )}
            {selectedColumn !== undefined && selectedRow !== undefined && (
              <circle
                className="updraft-lens-selected-point"
                cx={selectedColumn}
                cy={selectedRow}
                r={Math.min(width, height) * 0.018}
                vectorEffect="non-scaling-stroke"
              />
            )}
          </g>
        </svg>
        <div className="updraft-lens-axis updraft-lens-axis-x" aria-hidden="true">
          <span>{formatKilometers(columnMin)}</span>
          <strong>{columnDimension} (km)</strong>
          <span>{formatKilometers(columnMax)}</span>
        </div>
      </div>
      {showLegend && <UpdraftLensScaleLegend frame={frame} viewLabel="2-D inspector" />}
    </section>
  );
}

export function updraftLensDiscreteColor(
  value: number | null,
  breakpoints: number[],
  colors: string[],
): string {
  if (value === null || !Number.isFinite(value)) return MISSING_COLOR;
  if (colors.length !== breakpoints.length + 1 || colors.length === 0) return MISSING_COLOR;
  let colorIndex = 0;
  while (colorIndex < breakpoints.length && value >= breakpoints[colorIndex]) {
    colorIndex += 1;
  }
  return colors[colorIndex] ?? MISSING_COLOR;
}

// Retained for the Standard-view selected-value swatch; Lens rendering uses the discrete lookup.
export function updraftLensColor(
  value: number | null,
  rangeMinimum: number,
  rangeMaximum: number,
): string {
  if (value === null || !Number.isFinite(value)) return MISSING_COLOR;
  if (value <= 0) {
    const denominator = Math.max(Number.EPSILON, Math.abs(rangeMinimum));
    return interpolateHex(
      LEGACY_DOWNDRAFT_COLOR,
      LEGACY_NEUTRAL_COLOR,
      1 - clamp(Math.abs(value) / denominator),
    );
  }
  const denominator = Math.max(Number.EPSILON, Math.abs(rangeMaximum));
  return interpolateHex(LEGACY_NEUTRAL_COLOR, LEGACY_UPDRAFT_COLOR, clamp(value / denominator));
}

export function UpdraftLensScaleLegend({
  frame,
  viewLabel,
}: {
  frame: UpdraftLensFrame;
  viewLabel: "2-D inspector" | "3-D viewer" | "Explore workspace";
}) {
  const intervals = updraftLensScaleIntervals(frame.w_scale_breakpoints_m_s, frame.w_scale_colors);
  const finiteValues = frame.w_values_m_s
    .flat()
    .filter((value): value is number => value !== null && Number.isFinite(value));
  const sliceMinimum = finiteValues.length > 0 ? Math.min(...finiteValues) : null;
  const sliceMaximum = finiteValues.length > 0 ? Math.max(...finiteValues) : null;
  const viewClass =
    viewLabel === "2-D inspector" ? "2d" : viewLabel === "3-D viewer" ? "3d" : "workspace";
  return (
    <section
      className={`updraft-lens-scale-legend updraft-lens-scale-legend-${viewClass}`}
      aria-label={`${viewLabel} ${SCALE_TITLE}; ${frame.w_scale_id}`}
    >
      <div className="updraft-lens-scale-heading">
        <strong>{SCALE_TITLE}</strong>
      </div>
      <p className="updraft-lens-slice-range updraft-lens-slice-range-maximum">
        Slice maximum {sliceMaximum === null ? "unavailable" : `${sliceMaximum.toFixed(2)} m/s`}.
      </p>
      <ol className="updraft-lens-scale-intervals" aria-label="Exact vertical velocity intervals">
        {[...intervals].reverse().map((interval, reversedIndex) => {
          const index = intervals.length - 1 - reversedIndex;
          return (
            <li
              key={`${interval.label}-${interval.color}`}
              aria-label={`${interval.label} ${frame.w_scale_units}; ${INTERVAL_MEANINGS[index]}; color ${interval.color}`}
            >
              <span
                className="updraft-lens-scale-swatch"
                style={{ backgroundColor: interval.color }}
                aria-hidden="true"
              />
              <span>
                {interval.label} {frame.w_scale_units}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="updraft-lens-slice-range updraft-lens-slice-range-minimum">
        Slice minimum {sliceMinimum === null ? "unavailable" : `${sliceMinimum.toFixed(2)} m/s`}.
      </p>
    </section>
  );
}

export function updraftLensScaleIntervals(
  breakpoints: number[],
  colors: string[],
): Array<{ label: string; color: string }> {
  return colors.map((color, index) => {
    if (index === 0) return { label: `< ${formatVelocity(breakpoints[0])}`, color };
    if (index === colors.length - 1) {
      return { label: `>= ${formatVelocity(breakpoints.at(-1))}`, color };
    }
    return {
      label: `${formatVelocity(breakpoints[index - 1])} to < ${formatVelocity(breakpoints[index])}`,
      color,
    };
  });
}

export function updraftLensCellGeometry(
  xEdges: number[],
  zEdges: number[],
  xIndex: number,
  zIndex: number,
): CellGeometry {
  const x = xEdges[xIndex] ?? 0;
  const y = zEdges[zIndex] ?? 0;
  return {
    x,
    y,
    width: Math.max(0, (xEdges[xIndex + 1] ?? x) - x),
    height: Math.max(0, (zEdges[zIndex + 1] ?? y) - y),
  };
}

export function updraftLensBoundaryPath(
  cloudMask: boolean[][],
  xEdges: number[],
  zEdges: number[],
): string {
  const segments: string[] = [];
  for (let zIndex = 0; zIndex < cloudMask.length; zIndex += 1) {
    for (let xIndex = 0; xIndex < (cloudMask[zIndex]?.length ?? 0); xIndex += 1) {
      if (!cloudMask[zIndex]?.[xIndex]) continue;
      const x0 = xEdges[xIndex] ?? 0;
      const x1 = xEdges[xIndex + 1] ?? x0;
      const z0 = zEdges[zIndex] ?? 0;
      const z1 = zEdges[zIndex + 1] ?? z0;
      if (!cloudMask[zIndex]?.[xIndex - 1]) segments.push(`M ${x0} ${z0} L ${x0} ${z1}`);
      if (!cloudMask[zIndex]?.[xIndex + 1]) segments.push(`M ${x1} ${z0} L ${x1} ${z1}`);
      if (!cloudMask[zIndex - 1]?.[xIndex]) segments.push(`M ${x0} ${z0} L ${x1} ${z0}`);
      if (!cloudMask[zIndex + 1]?.[xIndex]) segments.push(`M ${x0} ${z1} L ${x1} ${z1}`);
    }
  }
  return segments.join(" ");
}

export function updraftLensSelectionFromPointer(
  pointerX: number,
  pointerY: number,
  renderedWidth: number,
  renderedHeight: number,
  columnValues: number[],
  rowValues: number[],
  orientation: UpdraftLensOrientation,
  planeIndex: number,
): UpdraftLensPointSelection | null {
  if (
    renderedWidth <= 0 ||
    renderedHeight <= 0 ||
    columnValues.length === 0 ||
    rowValues.length === 0
  ) {
    return null;
  }
  const columnEdges = coordinateEdges(columnValues);
  const rowEdges = coordinateEdges(rowValues);
  const columnCoordinate =
    (columnEdges[0] ?? 0) +
    clamp(pointerX / renderedWidth) * ((columnEdges.at(-1) ?? 1) - (columnEdges[0] ?? 0));
  const rowCoordinate =
    (rowEdges.at(-1) ?? 1) -
    clamp(pointerY / renderedHeight) * ((rowEdges.at(-1) ?? 1) - (rowEdges[0] ?? 0));
  const columnIndex = nearestIndex(columnValues, columnCoordinate);
  const rowIndex = nearestIndex(rowValues, rowCoordinate);
  if (orientation === "horizontal") {
    return { xIndex: columnIndex, yIndex: rowIndex, zIndex: planeIndex };
  }
  if (orientation === "vertical_x") {
    return { xIndex: columnIndex, yIndex: planeIndex, zIndex: rowIndex };
  }
  return { xIndex: planeIndex, yIndex: columnIndex, zIndex: rowIndex };
}

export function updraftLensCoordinateValues(
  frame: UpdraftLensFrame,
  dimension: UpdraftLensDimension,
): number[] {
  if (dimension === "x") return frame.x_values_km;
  if (dimension === "y") return frame.y_values_km;
  return frame.z_values_km;
}

function updraftLensPointIndex(
  selection: UpdraftLensPointSelection,
  dimension: UpdraftLensDimension,
): number {
  if (dimension === "x") return selection.xIndex;
  if (dimension === "y") return selection.yIndex;
  return selection.zIndex;
}

function coordinateEdges(values: number[]): number[] {
  if (values.length === 0) return [0, 1];
  if (values.length === 1) return [values[0] - 0.5, values[0] + 0.5];
  const edges = [values[0] - (values[1] - values[0]) / 2];
  for (let index = 1; index < values.length; index += 1) {
    edges.push((values[index - 1] + values[index]) / 2);
  }
  edges.push(values.at(-1)! + (values.at(-1)! - values.at(-2)!) / 2);
  return edges;
}

function nearestIndex(values: number[], target: number): number {
  let selected = 0;
  let distance = Number.POSITIVE_INFINITY;
  values.forEach((value, index) => {
    const candidateDistance = Math.abs(value - target);
    if (candidateDistance < distance) {
      selected = index;
      distance = candidateDistance;
    }
  });
  return selected;
}

function interpolateHex(start: string, end: string, amount: number): string {
  const startRgb = hexToRgb(start);
  const endRgb = hexToRgb(end);
  return `#${[0, 1, 2]
    .map((index) =>
      Math.round(startRgb[index] + (endRgb[index] - startRgb[index]) * clamp(amount))
        .toString(16)
        .padStart(2, "0"),
    )
    .join("")}`;
}

function hexToRgb(hex: string): [number, number, number] {
  return [
    Number.parseInt(hex.slice(1, 3), 16),
    Number.parseInt(hex.slice(3, 5), 16),
    Number.parseInt(hex.slice(5, 7), 16),
  ];
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function formatKilometers(value: number): string {
  return `${Number(value.toFixed(2))}`;
}

function formatVelocity(value: number | undefined): string {
  return Number.isFinite(value) ? Number(value).toFixed(1) : "unavailable";
}

function updraftLensAccessibleSummary(frame: UpdraftLensFrame): string {
  const finiteValues = frame.w_values_m_s.flat().filter((value): value is number => value !== null);
  const updraftCells = finiteValues.filter((value) => value > 0).length;
  const downdraftCells = finiteValues.filter((value) => value < 0).length;
  const cloudCells = frame.cloud_mask.flat().filter(Boolean).length;
  return `Updraft Lens ${updraftLensOrientationLabel(frame.orientation)} at ${frame.plane_dimension} index ${frame.plane_index}; ${updraftCells} updraft cells, ${downdraftCells} downdraft cells, and ${cloudCells} cloud cells.`;
}

function updraftLensOrientationLabel(orientation: UpdraftLensOrientation): string {
  if (orientation === "horizontal") return "horizontal x-y slice";
  if (orientation === "vertical_y") return "vertical y-z slice";
  return "vertical x-z slice";
}

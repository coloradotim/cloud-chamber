/* eslint-disable react-refresh/only-export-components */
import type { MouseEvent as ReactMouseEvent } from "react";

export type UpdraftLensWindMode = "perturbation" | "total";

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
  orientation: "vertical_x";
  plane_dimension: "y";
  plane_index: number;
  plane_coordinate: number | null;
  plane_units: string | null;
  x_indices: number[];
  x_values_km: number[];
  z_indices: number[];
  z_values_km: number[];
  w_values_m_s: Array<Array<number | null>>;
  cloud_mask: boolean[][];
  cloud_threshold_kg_kg: number;
  w_range_min_m_s: number;
  w_range_max_m_s: number;
  w_range_method: string;
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
  selectedPoint?: UpdraftLensPointSelection | null;
  onSelectPoint?: (selection: UpdraftLensPointSelection) => void;
};

type CellGeometry = {
  x: number;
  y: number;
  width: number;
  height: number;
};

const DOWNDRAFT_COLOR = "#2166ac";
const NEUTRAL_COLOR = "#f7f7f7";
const UPDRAFT_COLOR = "#b2182b";
const MISSING_COLOR = "#747b80";

export function UpdraftLensSlice({
  frame,
  showCloudBoundary = true,
  selectedPoint = null,
  onSelectPoint,
}: UpdraftLensSliceProps) {
  const xEdges = coordinateEdges(frame.x_values_km);
  const zEdges = coordinateEdges(frame.z_values_km);
  const xMin = xEdges[0] ?? 0;
  const xMax = xEdges.at(-1) ?? 1;
  const zMin = zEdges[0] ?? 0;
  const zMax = zEdges.at(-1) ?? 1;
  const width = Math.max(Number.EPSILON, xMax - xMin);
  const height = Math.max(Number.EPSILON, zMax - zMin);
  const boundaryPath = showCloudBoundary
    ? updraftLensBoundaryPath(frame.cloud_mask, xEdges, zEdges)
    : "";
  const selectedX =
    selectedPoint && selectedPoint.yIndex === frame.plane_index
      ? frame.x_values_km[selectedPoint.xIndex]
      : undefined;
  const selectedZ =
    selectedPoint && selectedPoint.yIndex === frame.plane_index
      ? frame.z_values_km[selectedPoint.zIndex]
      : undefined;

  function handlePointer(event: ReactMouseEvent<SVGSVGElement>) {
    if (!onSelectPoint) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const selection = updraftLensSelectionFromPointer(
      event.clientX - bounds.left,
      event.clientY - bounds.top,
      bounds.width,
      bounds.height,
      frame.x_values_km,
      frame.z_values_km,
      frame.plane_index,
    );
    if (selection) onSelectPoint(selection);
  }

  return (
    <section className="updraft-lens-slice" aria-label="Updraft Lens vertical slice">
      <div className="updraft-lens-axis updraft-lens-axis-z" aria-hidden="true">
        <span>{formatKilometers(zMax)}</span>
        <strong>z (km)</strong>
        <span>{formatKilometers(zMin)}</span>
      </div>
      <div className="updraft-lens-plot-column">
        <svg
          className="updraft-lens-svg"
          role="img"
          aria-label={updraftLensAccessibleSummary(frame)}
          data-domain-aspect={(width / height).toFixed(6)}
          viewBox={`${xMin} ${zMin} ${width} ${height}`}
          preserveAspectRatio="none"
          style={{ aspectRatio: `${width} / ${height}` }}
          shapeRendering="crispEdges"
          onClick={handlePointer}
        >
          <g transform={`translate(0 ${zMin + zMax}) scale(1 -1)`}>
            {frame.w_values_m_s.map((row, zIndex) =>
              row.map((value, xIndex) => {
                const geometry = updraftLensCellGeometry(xEdges, zEdges, xIndex, zIndex);
                return (
                  <rect
                    key={`${zIndex}-${xIndex}`}
                    data-cell={`${zIndex}-${xIndex}`}
                    x={geometry.x}
                    y={geometry.y}
                    width={geometry.width}
                    height={geometry.height}
                    fill={updraftLensColor(value, frame.w_range_min_m_s, frame.w_range_max_m_s)}
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
            {selectedX !== undefined && selectedZ !== undefined && (
              <circle
                className="updraft-lens-selected-point"
                cx={selectedX}
                cy={selectedZ}
                r={Math.min(width, height) * 0.018}
                vectorEffect="non-scaling-stroke"
              />
            )}
          </g>
        </svg>
        <div className="updraft-lens-axis updraft-lens-axis-x" aria-hidden="true">
          <span>{formatKilometers(xMin)}</span>
          <strong>x (km)</strong>
          <span>{formatKilometers(xMax)}</span>
        </div>
        <div className="updraft-lens-legend" aria-label="Vertical velocity color scale">
          <span>{frame.w_range_min_m_s.toFixed(1)}</span>
          <span className="updraft-lens-color-ramp" />
          <span>{frame.w_range_max_m_s.toFixed(1)} m/s</span>
        </div>
      </div>
    </section>
  );
}

export function updraftLensColor(
  value: number | null,
  rangeMinimum: number,
  rangeMaximum: number,
): string {
  if (value === null || !Number.isFinite(value)) return MISSING_COLOR;
  if (value <= 0) {
    const denominator = Math.max(Number.EPSILON, Math.abs(rangeMinimum));
    return interpolateHex(DOWNDRAFT_COLOR, NEUTRAL_COLOR, 1 - clamp(Math.abs(value) / denominator));
  }
  const denominator = Math.max(Number.EPSILON, Math.abs(rangeMaximum));
  return interpolateHex(NEUTRAL_COLOR, UPDRAFT_COLOR, clamp(value / denominator));
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
  xValues: number[],
  zValues: number[],
  yIndex: number,
): UpdraftLensPointSelection | null {
  if (renderedWidth <= 0 || renderedHeight <= 0 || xValues.length === 0 || zValues.length === 0) {
    return null;
  }
  const xEdges = coordinateEdges(xValues);
  const zEdges = coordinateEdges(zValues);
  const xCoordinate =
    (xEdges[0] ?? 0) + clamp(pointerX / renderedWidth) * ((xEdges.at(-1) ?? 1) - (xEdges[0] ?? 0));
  const zCoordinate =
    (zEdges.at(-1) ?? 1) -
    clamp(pointerY / renderedHeight) * ((zEdges.at(-1) ?? 1) - (zEdges[0] ?? 0));
  return {
    xIndex: nearestIndex(xValues, xCoordinate),
    yIndex,
    zIndex: nearestIndex(zValues, zCoordinate),
  };
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

function updraftLensAccessibleSummary(frame: UpdraftLensFrame): string {
  const finiteValues = frame.w_values_m_s.flat().filter((value): value is number => value !== null);
  const updraftCells = finiteValues.filter((value) => value > 0).length;
  const downdraftCells = finiteValues.filter((value) => value < 0).length;
  const cloudCells = frame.cloud_mask.flat().filter(Boolean).length;
  return `Updraft Lens vertical x-z slice at y index ${frame.plane_index}; ${updraftCells} updraft cells, ${downdraftCells} downdraft cells, and ${cloudCells} cloud cells.`;
}

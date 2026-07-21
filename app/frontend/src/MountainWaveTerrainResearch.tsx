/* eslint-disable react-refresh/only-export-components */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";

import "./App.css";
import "./MountainWaveTerrainResearch.css";

export type MountainWaveTerrainField = "w" | "theta_perturbation";

export type MountainWaveTerrainFrame = {
  schema_version: string;
  run_id: string;
  case_label: string;
  time_index: number;
  time_seconds: number;
  times_seconds: number[];
  dimensionality: string;
  singleton_y: boolean;
  dry_case: boolean;
  field: {
    key: MountainWaveTerrainField;
    display_name: string;
    units: string;
    native_dimensions: string[];
    vertical_grid: "physical_full_levels" | "physical_scalar_levels";
    derivation: string;
  };
  values: number[][];
  geometry: {
    x_center_m: number[];
    x_edge_m: number[];
    terrain_m: number[];
    scalar_height_m: number[][];
    full_height_m: number[][];
    nominal_scalar_height_m: number[];
    nominal_full_height_m: number[];
    active_top_m: number;
    singleton_y_m: number;
    horizontal_units: string;
    vertical_units: string;
  };
  active_top_evidence: {
    transform_top_source: string;
    final_nominal_zf_m: number;
    runtime_ztop_m: number;
    configured_nz: number;
    configured_dz_m: number;
    nz_times_dz_m: number;
    all_sources_agree: boolean;
    inactive_namelist_ztop_m: number;
  };
  vertical_references: {
    physical_model_height: string;
    local_agl: string;
    nominal_coordinate: string;
    model_height_is_msl: boolean;
  };
  scale: {
    fixed_across_all_times: boolean;
    minimum: number;
    maximum: number;
    selected_time_minimum: number;
    selected_time_maximum: number;
    palette: string;
  };
  provenance: {
    source_history_file: string;
    reference_history_file: string | null;
    source_kind: string;
    topology: string;
    horizontal_collocation: string;
    interpolation: string;
    display_binning: string;
    physical_height_source: string;
    full_height_source: string;
    masked_below_terrain: boolean;
  };
  identity: {
    implementation_commit: string;
    verification_mode: string;
    verified_file_count: number;
    verified_before_and_after_extraction: boolean;
  };
  performance: {
    extraction_ms: number;
    serialization_ms: number;
    serialized_payload_bytes: number;
  };
  caveats: string[];
};

export type TerrainDisplayCell = {
  row: number;
  column: number;
  value: number;
  nominalHeightM: number;
  corners: Array<{ x: number; z: number }>;
};

export type TerrainReadout = {
  xM: number;
  modelHeightM: number;
  terrainHeightM: number;
  aglM: number;
  value: number;
  nominalHeightM: number;
};

const COLOR_STOPS = ["#173f8a", "#6aaed6", "#f7f7f2", "#ef8a62", "#9d1d20"];

export function MountainWaveTerrainResearch() {
  const [field, setField] = useState<MountainWaveTerrainField>("w");
  const [timeIndex, setTimeIndex] = useState(10);
  const [frame, setFrame] = useState<MountainWaveTerrainFrame | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [requestMs, setRequestMs] = useState<number | null>(null);
  const [readout, setReadout] = useState<TerrainReadout | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const started = performance.now();
    setLoading(true);
    setError(null);
    fetch(`/api/research/mountain-wave-terrain?field=${field}&time_index=${timeIndex}`, {
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
          throw new Error(payload?.detail ?? `Terrain payload failed (${response.status}).`);
        }
        return (await response.json()) as MountainWaveTerrainFrame;
      })
      .then((payload) => {
        setFrame(payload);
        setRequestMs(performance.now() - started);
        setReadout(null);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Terrain payload failed.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [field, retryNonce, timeIndex]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setTimeIndex((current) => (current >= 10 ? 0 : current + 1));
    }, 900);
    return () => window.clearInterval(timer);
  }, [playing]);

  const times = frame?.times_seconds ?? Array.from({ length: 11 }, (_unused, index) => index * 216);
  const moveTime = useCallback((delta: number) => {
    setPlaying(false);
    setTimeIndex((current) => Math.max(0, Math.min(10, current + delta)));
  }, []);

  return (
    <main className="mw-research-shell">
      <header className="mw-research-header">
        <div>
          <p className="mw-research-kicker">Terrain-aware validation</p>
          <h1>Dry mountain-wave cross-section</h1>
          <p className="mw-research-subtitle">
            Native CM1 terrain-following output at y ={" "}
            {formatDistance(frame?.geometry.singleton_y_m ?? 0)}
          </p>
        </div>
        <div className="mw-research-header-facts" aria-label="Research surface status">
          <strong>Preserved Gate B result</strong>
          <span>Dry 2-D x-z cross-section · singleton y</span>
        </div>
      </header>

      {error ? (
        <section className="mw-research-error" role="alert">
          <strong>Terrain view unavailable</strong>
          <span>{error}</span>
          <button type="button" onClick={() => setRetryNonce((current) => current + 1)}>
            Retry
          </button>
        </section>
      ) : (
        <div className="mw-research-workspace" aria-busy={loading}>
          <section className="mw-plot-panel" aria-label="Terrain-following field view">
            <div className="mw-plot-heading">
              <div>
                <span>{frame?.field.display_name ?? "Vertical velocity"}</span>
                <strong>{formatModelTime(frame?.time_seconds ?? times[timeIndex] ?? 0)}</strong>
              </div>
              <p>{loading ? "Loading native history…" : "Physical height · native x-z topology"}</p>
            </div>
            {frame ? (
              <TerrainCanvas frame={frame} onReadout={setReadout} />
            ) : (
              <div className="mw-plot-loading">Loading verified terrain geometry…</div>
            )}
            {frame && <TerrainLegend frame={frame} />}
          </section>

          <aside className="mw-control-rail" aria-label="Terrain view controls">
            <section className="mw-control-section">
              <h2>Field</h2>
              <div className="mw-segmented-control" aria-label="Field selection">
                <button type="button" aria-pressed={field === "w"} onClick={() => setField("w")}>
                  Vertical velocity
                </button>
                <button
                  type="button"
                  aria-pressed={field === "theta_perturbation"}
                  onClick={() => setField("theta_perturbation")}
                >
                  θ perturbation
                </button>
              </div>
              <p className="mw-field-note">{frame?.field.derivation ?? "Native CM1 field."}</p>
            </section>

            <section className="mw-control-section">
              <div className="mw-control-heading">
                <h2>Model time</h2>
                <strong>{formatModelTime(times[timeIndex] ?? 0)}</strong>
              </div>
              <div className="mw-time-commands">
                <button
                  type="button"
                  className="mw-icon-button"
                  aria-label="Previous output"
                  title="Previous output"
                  disabled={timeIndex === 0}
                  onClick={() => moveTime(-1)}
                >
                  ‹
                </button>
                <button
                  type="button"
                  className="mw-icon-button mw-play-button"
                  aria-label={playing ? "Pause" : "Play"}
                  title={playing ? "Pause" : "Play"}
                  onClick={() => setPlaying((current) => !current)}
                >
                  <span aria-hidden="true" className={playing ? "mw-pause-icon" : "mw-play-icon"} />
                </button>
                <button
                  type="button"
                  className="mw-icon-button"
                  aria-label="Next output"
                  title="Next output"
                  disabled={timeIndex === times.length - 1}
                  onClick={() => moveTime(1)}
                >
                  ›
                </button>
              </div>
              <input
                className="mw-time-slider"
                type="range"
                min={0}
                max={times.length - 1}
                value={timeIndex}
                aria-label="Saved output time"
                onChange={(event) => {
                  setPlaying(false);
                  setTimeIndex(Number(event.currentTarget.value));
                }}
              />
              <div className="mw-time-range" aria-hidden="true">
                <span>0:00</span>
                <span>36:00</span>
              </div>
            </section>

            <section className="mw-readout-section" aria-live="polite">
              <h2>Pointer</h2>
              {readout ? (
                <dl className="mw-readout-grid">
                  <div>
                    <dt>x</dt>
                    <dd>{formatDistance(readout.xM)}</dd>
                  </div>
                  <div>
                    <dt>Model height</dt>
                    <dd>{formatDistance(readout.modelHeightM)}</dd>
                  </div>
                  <div>
                    <dt>Local AGL</dt>
                    <dd>{formatDistance(readout.aglM)}</dd>
                  </div>
                  <div>
                    <dt>{frame?.field.display_name}</dt>
                    <dd>
                      {readout.value.toFixed(3)} {frame?.field.units}
                    </dd>
                  </div>
                  <div className="mw-readout-wide">
                    <dt>Native level</dt>
                    <dd>{formatDistance(readout.nominalHeightM)} nominal</dd>
                  </div>
                </dl>
              ) : (
                <p>Move across the cross-section to inspect x, physical height, and local AGL.</p>
              )}
            </section>

            <section className="mw-native-facts">
              <h2>Native geometry</h2>
              <dl>
                <div>
                  <dt>Grid</dt>
                  <dd>
                    {frame ? `${frame.geometry.x_center_m.length} × ${frame.values.length}` : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Active top</dt>
                  <dd>{frame ? formatDistance(frame.geometry.active_top_m) : "—"}</dd>
                </div>
                <div>
                  <dt>Placement</dt>
                  <dd>
                    {frame?.field.vertical_grid === "physical_full_levels"
                      ? "Full levels"
                      : "Scalar levels"}
                  </dd>
                </div>
                <div>
                  <dt>Interpolation</dt>
                  <dd>None on field values</dd>
                </div>
              </dl>
            </section>
          </aside>
        </div>
      )}

      {frame && (
        <footer className="mw-research-footer">
          <div>
            <strong>Scope</strong>
            <p>{frame.caveats.join(" ")}</p>
          </div>
          <details>
            <summary>Payload and provenance</summary>
            <dl>
              <div>
                <dt>Run</dt>
                <dd>{frame.run_id}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{frame.provenance.source_history_file}</dd>
              </div>
              <div>
                <dt>Display binning</dt>
                <dd>{frame.provenance.display_binning}</dd>
              </div>
              <div>
                <dt>Identity</dt>
                <dd>
                  {frame.identity.verified_before_and_after_extraction
                    ? `${frame.identity.verified_file_count} pinned files verified before and after extraction`
                    : "Synthetic or unverified payload"}
                </dd>
              </div>
              <div>
                <dt>Backend extraction</dt>
                <dd>{frame.performance.extraction_ms.toFixed(1)} ms</dd>
              </div>
              <div>
                <dt>Payload</dt>
                <dd>{formatBytes(frame.performance.serialized_payload_bytes)}</dd>
              </div>
              <div>
                <dt>Request to browser state</dt>
                <dd>{requestMs === null ? "—" : `${requestMs.toFixed(1)} ms`}</dd>
              </div>
            </dl>
          </details>
        </footer>
      )}
    </main>
  );
}

function TerrainCanvas({
  frame,
  onReadout,
}: {
  frame: MountainWaveTerrainFrame;
  onReadout: (readout: TerrainReadout | null) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cells = useMemo(() => buildTerrainDisplayCells(frame), [frame]);
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawTerrainFrame(canvas, frame, cells);
  }, [cells, frame]);

  useEffect(() => {
    draw();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(() => draw());
    observer?.observe(canvas);
    window.addEventListener("resize", draw);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", draw);
    };
  }, [draw]);

  function handlePointer(event: ReactMouseEvent<HTMLCanvasElement>) {
    const canvas = event.currentTarget;
    const bounds = canvas.getBoundingClientRect();
    const plot = plotBounds(bounds.width || 900, bounds.height || 700);
    const xMin = frame.geometry.x_edge_m[0] ?? 0;
    const xMax = frame.geometry.x_edge_m.at(-1) ?? 1;
    const zMax = frame.geometry.active_top_m;
    const x = xMin + ((event.clientX - bounds.left - plot.left) / plot.width) * (xMax - xMin);
    const z = zMax - ((event.clientY - bounds.top - plot.top) / plot.height) * zMax;
    const cell = cells.find((candidate) => pointInPolygon(x, z, candidate.corners));
    if (!cell) {
      onReadout(null);
      return;
    }
    onReadout(terrainReadoutForCell(frame, cell));
  }

  return (
    <canvas
      ref={canvasRef}
      className="mw-terrain-canvas"
      role="img"
      aria-label={`${frame.field.display_name} over native curved terrain at ${formatModelTime(
        frame.time_seconds,
      )}`}
      onMouseMove={handlePointer}
      onMouseLeave={() => onReadout(null)}
    />
  );
}

function TerrainLegend({ frame }: { frame: MountainWaveTerrainFrame }) {
  const stops = Array.from({ length: 9 }, (_unused, index) => {
    const fraction = index / 8;
    return frame.scale.maximum - fraction * (frame.scale.maximum - frame.scale.minimum);
  });
  return (
    <aside className="mw-color-legend" aria-label={`${frame.field.display_name} color scale`}>
      <strong>
        {frame.field.key === "w" ? "w" : "θ′"} ({frame.field.units})
      </strong>
      <span>{formatValue(frame.scale.maximum)}</span>
      <div className="mw-color-ramp" aria-hidden="true" />
      <div className="mw-color-ticks" aria-hidden="true">
        {stops.map((value) => (
          <span key={value}>{formatValue(value)}</span>
        ))}
      </div>
      <span>{formatValue(frame.scale.minimum)}</span>
      <p>
        This frame {formatValue(frame.scale.selected_time_minimum)} to{" "}
        {formatValue(frame.scale.selected_time_maximum)}
      </p>
    </aside>
  );
}

export function buildTerrainDisplayCells(frame: MountainWaveTerrainFrame): TerrainDisplayCell[] {
  const cells: TerrainDisplayCell[] = [];
  const full = frame.geometry.full_height_m;
  const isFull = frame.field.vertical_grid === "physical_full_levels";
  const verticalCount = frame.values.length;
  for (let row = 0; row < verticalCount; row += 1) {
    const lowerAtCenters = isFull
      ? row === 0
        ? frame.geometry.terrain_m
        : averageRows(full[row - 1], full[row])
      : full[row];
    const upperAtCenters = isFull
      ? row === verticalCount - 1
        ? full[full.length - 1]
        : averageRows(full[row], full[row + 1])
      : full[row + 1];
    const lowerAtEdges = centerValuesToEdges(lowerAtCenters);
    const upperAtEdges = centerValuesToEdges(upperAtCenters);
    for (let column = 0; column < frame.geometry.x_center_m.length; column += 1) {
      const value = frame.values[row]?.[column];
      if (!Number.isFinite(value)) continue;
      const x0 = frame.geometry.x_edge_m[column];
      const x1 = frame.geometry.x_edge_m[column + 1];
      if (x0 === undefined || x1 === undefined) continue;
      cells.push({
        row,
        column,
        value,
        nominalHeightM: isFull
          ? (frame.geometry.nominal_full_height_m[row] ?? 0)
          : (frame.geometry.nominal_scalar_height_m[row] ?? 0),
        corners: [
          { x: x0, z: lowerAtEdges[column] ?? 0 },
          { x: x1, z: lowerAtEdges[column + 1] ?? 0 },
          { x: x1, z: upperAtEdges[column + 1] ?? 0 },
          { x: x0, z: upperAtEdges[column] ?? 0 },
        ],
      });
    }
  }
  return cells;
}

export function terrainReadoutForCell(
  frame: MountainWaveTerrainFrame,
  cell: TerrainDisplayCell,
): TerrainReadout {
  const terrainHeightM = frame.geometry.terrain_m[cell.column] ?? 0;
  const modelHeightM =
    frame.field.vertical_grid === "physical_full_levels"
      ? (frame.geometry.full_height_m[cell.row]?.[cell.column] ?? terrainHeightM)
      : (frame.geometry.scalar_height_m[cell.row]?.[cell.column] ?? terrainHeightM);
  return {
    xM: frame.geometry.x_center_m[cell.column] ?? 0,
    modelHeightM,
    terrainHeightM,
    aglM: Math.max(0, modelHeightM - terrainHeightM),
    value: cell.value,
    nominalHeightM: cell.nominalHeightM,
  };
}

function drawTerrainFrame(
  canvas: HTMLCanvasElement,
  frame: MountainWaveTerrainFrame,
  cells: TerrainDisplayCell[],
) {
  const cssWidth = canvas.clientWidth || 900;
  const cssHeight = canvas.clientHeight || 700;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.round(cssWidth * pixelRatio);
  canvas.height = Math.round(cssHeight * pixelRatio);
  const context = canvas.getContext("2d");
  if (!context) return;
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.clearRect(0, 0, cssWidth, cssHeight);
  context.fillStyle = "#f8fbfc";
  context.fillRect(0, 0, cssWidth, cssHeight);

  const bounds = plotBounds(cssWidth, cssHeight);
  const xMin = frame.geometry.x_edge_m[0] ?? 0;
  const xMax = frame.geometry.x_edge_m.at(-1) ?? 1;
  const zMax = frame.geometry.active_top_m;
  const toX = (value: number) => bounds.left + ((value - xMin) / (xMax - xMin)) * bounds.width;
  const toY = (value: number) => bounds.top + bounds.height - (value / zMax) * bounds.height;

  context.strokeStyle = "#dbe6eb";
  context.lineWidth = 1;
  context.font = "600 12px Inter, system-ui, sans-serif";
  context.textAlign = "right";
  context.textBaseline = "middle";
  for (let zM = 0; zM <= zMax; zM += 5_000) {
    const y = toY(zM);
    context.beginPath();
    context.moveTo(bounds.left, y);
    context.lineTo(bounds.left + bounds.width, y);
    context.stroke();
    context.fillStyle = "#5f7180";
    context.fillText(`${zM / 1_000}`, bounds.left - 12, y);
  }

  for (const cell of cells) {
    context.beginPath();
    cell.corners.forEach((corner, index) => {
      if (index === 0) context.moveTo(toX(corner.x), toY(corner.z));
      else context.lineTo(toX(corner.x), toY(corner.z));
    });
    context.closePath();
    context.fillStyle = terrainFieldColor(cell.value, frame.scale.minimum, frame.scale.maximum);
    context.fill();
  }

  const terrainEdges = centerValuesToEdges(frame.geometry.terrain_m);
  context.beginPath();
  context.moveTo(toX(xMin), toY(0));
  context.lineTo(toX(xMin), toY(terrainEdges[0] ?? 0));
  terrainEdges.forEach((height, index) =>
    context.lineTo(toX(frame.geometry.x_edge_m[index] ?? xMin), toY(height)),
  );
  context.lineTo(toX(xMax), toY(0));
  context.closePath();
  context.fillStyle = "#3f474b";
  context.fill();
  context.beginPath();
  terrainEdges.forEach((height, index) => {
    const x = toX(frame.geometry.x_edge_m[index] ?? xMin);
    const y = toY(height);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.strokeStyle = "#12191d";
  context.lineWidth = 2;
  context.stroke();

  context.strokeStyle = "#536773";
  context.lineWidth = 1.5;
  context.strokeRect(bounds.left, bounds.top, bounds.width, bounds.height);
  context.fillStyle = "#172b3a";
  context.font = "700 13px Inter, system-ui, sans-serif";
  context.textBaseline = "top";
  context.textAlign = "left";
  context.fillText(`${formatDistance(xMin)}`, bounds.left, bounds.top + bounds.height + 12);
  context.textAlign = "right";
  context.fillText(
    `${formatDistance(xMax)}`,
    bounds.left + bounds.width,
    bounds.top + bounds.height + 12,
  );
  context.textAlign = "center";
  context.fillText("x (km)", bounds.left + bounds.width / 2, bounds.top + bounds.height + 38);
  context.save();
  context.translate(18, bounds.top + bounds.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("Physical height (km)", 0, 0);
  context.restore();
}

function plotBounds(width: number, height: number) {
  return { left: 74, top: 22, width: Math.max(1, width - 96), height: Math.max(1, height - 86) };
}

function averageRows(first: number[] | undefined, second: number[] | undefined): number[] {
  if (!first || !second || first.length !== second.length) return [];
  return first.map((value, index) => (value + (second[index] ?? value)) / 2);
}

export function centerValuesToEdges(values: number[]): number[] {
  if (values.length === 0) return [];
  if (values.length === 1) return [values[0], values[0]];
  const edges = [values[0]];
  for (let index = 1; index < values.length; index += 1) {
    edges.push(((values[index - 1] ?? 0) + (values[index] ?? 0)) / 2);
  }
  edges.push(values.at(-1) ?? 0);
  return edges;
}

export function pointInPolygon(x: number, z: number, corners: Array<{ x: number; z: number }>) {
  let inside = false;
  for (let index = 0, previous = corners.length - 1; index < corners.length; previous = index++) {
    const currentCorner = corners[index];
    const previousCorner = corners[previous];
    if (!currentCorner || !previousCorner) continue;
    const intersects =
      currentCorner.z > z !== previousCorner.z > z &&
      x <
        ((previousCorner.x - currentCorner.x) * (z - currentCorner.z)) /
          (previousCorner.z - currentCorner.z) +
          currentCorner.x;
    if (intersects) inside = !inside;
  }
  return inside;
}

export function terrainFieldColor(value: number, minimum: number, maximum: number): string {
  const span = Math.max(Number.EPSILON, maximum - minimum);
  const normalized = Math.max(0, Math.min(1, (value - minimum) / span));
  const scaled = normalized * (COLOR_STOPS.length - 1);
  const lowerIndex = Math.min(COLOR_STOPS.length - 2, Math.floor(scaled));
  const fraction = scaled - lowerIndex;
  return interpolateHex(
    COLOR_STOPS[lowerIndex] ?? "#ffffff",
    COLOR_STOPS[lowerIndex + 1] ?? "#ffffff",
    fraction,
  );
}

function interpolateHex(first: string, second: string, fraction: number): string {
  const firstValue = Number.parseInt(first.slice(1), 16);
  const secondValue = Number.parseInt(second.slice(1), 16);
  const channels = [16, 8, 0].map((shift) => {
    const start = (firstValue >> shift) & 255;
    const end = (secondValue >> shift) & 255;
    return Math.round(start + (end - start) * fraction);
  });
  return `#${channels.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

function formatModelTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}:${remainder.toString().padStart(2, "0")} (${seconds.toLocaleString()} s)`;
}

function formatDistance(meters: number): string {
  if (Math.abs(meters) < 1_000) return `${meters.toFixed(0)} m`;
  return `${(meters / 1_000).toFixed(2)} km`;
}

function formatValue(value: number): string {
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
}

function formatBytes(bytes: number): string {
  return bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KiB` : `${bytes} B`;
}

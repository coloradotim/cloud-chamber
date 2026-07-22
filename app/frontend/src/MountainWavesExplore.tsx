import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";

import { ExploreInspector, IntegratedExploreWorkspace } from "./IntegratedExploreWorkspace";
import type { MountainWavesSimulation } from "./MountainWavesWorld";
import { scalarPointPixelSize } from "./True3DViewer.utils";

type MountainWaveField =
  | "w"
  | "theta_perturbation"
  | "cloud_liquid"
  | "relative_humidity"
  | "cloud_over_wave";
type ViewMode = "field" | "structure" | "cloud";
type GeometryMode = "expanded" | "physical";
type ViewportMode = "focus" | "full";

type FieldMetadata = {
  key: MountainWaveField;
  display_name: string;
  units: string;
  derivation: string;
};

type TerrainGeometry = {
  x_center_m: number[];
  x_edge_m: number[];
  terrain_m: number[];
  scalar_height_m: number[][];
  full_height_m: number[][];
  nominal_scalar_height_m: number[];
  nominal_full_height_m: number[];
  active_top_m: number;
  singleton_y_m: number;
};

type TerrainScale = {
  fixed_across_all_times: boolean;
  minimum: number;
  maximum: number;
  selected_time_minimum: number;
  selected_time_maximum: number;
  palette: string;
  scale_id: string;
  scale_type: "fixed_across_time_discrete";
  units: string;
  breakpoints: number[];
  colors: string[];
};

type PointerContext = {
  horizontal_wind_m_s: number[][];
  vertical_velocity_m_s: number[][];
  potential_temperature_k: number[][];
  theta_perturbation_k: number[][];
  cloud_liquid_g_kg: number[][] | null;
  relative_humidity_percent: number[][] | null;
};

type ViewportBounds = {
  x_minimum_m: number;
  x_maximum_m: number;
  z_minimum_m: number;
  z_maximum_m: number;
};

type ViewportMetadata = {
  default_mode: ViewportMode;
  focus_available: boolean;
  focus: ViewportBounds;
  full: ViewportBounds;
};

type LensMetadata = {
  horizontal_wind_scale_id: string;
  horizontal_wind_reference_m_s: number;
  vertical_velocity_neutral_threshold_m_s: number;
  potential_temperature_contour_scale_id: string;
  potential_temperature_contour_interval_k: number;
  potential_temperature_contour_values_k: number[];
};

type CloudOverlay = {
  values: number[][];
  threshold: number;
  maximum: number;
};

type MountainWaveFrame = {
  schema_version: "mountain_waves_explore_v1";
  run_id: string;
  case_label: string;
  time_index: number;
  time_seconds: number;
  times_seconds: number[];
  dry_case: boolean;
  field: FieldMetadata;
  values: number[][];
  field_options: MountainWaveField[];
  overlay: CloudOverlay | null;
  pointer_context: PointerContext;
  viewport: ViewportMetadata;
  lens: LensMetadata;
  geometry: TerrainGeometry;
  scale: TerrainScale;
  caveats: string[];
  provenance: {
    source_history_file: string;
    topology: string;
    interpolation: string;
    display_binning: string;
    physical_height_source: string;
  };
  active_top_evidence: {
    transform_top_source: string;
    all_sources_agree: boolean;
    inactive_namelist_ztop_m: number;
  };
};

type NativeCloudCellPoint = {
  xM: number;
  zM: number;
  valueGKg: number;
};

function nativeCloudCellPoints(
  frame: Pick<MountainWaveFrame, "overlay" | "geometry">,
): NativeCloudCellPoint[] {
  const overlay = frame.overlay;
  if (!overlay) return [];
  const points: NativeCloudCellPoint[] = [];
  overlay.values.forEach((row, zIndex) => {
    row.forEach((valueGKg, xIndex) => {
      const xM = frame.geometry.x_center_m[xIndex];
      const zM = frame.geometry.scalar_height_m[zIndex]?.[xIndex];
      if (
        !Number.isFinite(valueGKg) ||
        valueGKg < overlay.threshold ||
        !Number.isFinite(xM) ||
        !Number.isFinite(zM)
      ) {
        return;
      }
      points.push({ xM, zM, valueGKg });
    });
  });
  return points;
}

function cloudPointOpacity(
  valueGKg: number,
  thresholdGKg: number,
  maximumGKg: number,
  globalOpacity: number,
): number {
  const global = clamp(globalOpacity, 0, 1);
  const range = Math.max(maximumGKg - thresholdGKg, thresholdGKg, Number.EPSILON);
  const intensity = clamp((valueGKg - thresholdGKg) / range, 0, 1);
  const localOpacity = 0.3 + Math.sqrt(intensity) * 0.7;
  return global * localOpacity;
}

function cloudPointColor(valueGKg: number, thresholdGKg: number, maximumGKg: number): string {
  const range = Math.max(maximumGKg - thresholdGKg, thresholdGKg, Number.EPSILON);
  const intensity = clamp((valueGKg - thresholdGKg) / range, 0, 1);
  const red = Math.round((0.24 + intensity * 0.55) * 255);
  const green = Math.round((0.66 + intensity * 0.3) * 255);
  const blue = Math.round((0.78 + intensity * 0.18) * 255);
  return `rgb(${red}, ${green}, ${blue})`;
}

function clamp(value: number, minimum: number, maximum: number): number {
  if (!Number.isFinite(value)) return minimum;
  return Math.min(maximum, Math.max(minimum, value));
}

// Focused tests exercise the same native-cell primitives used by the canvas renderer.
// eslint-disable-next-line react-refresh/only-export-components
export const mountainWavesCloudPointRendering = {
  cloudPointColor,
  cloudPointOpacity,
  nativeCloudCellPoints,
};

type PointSelection = {
  xIndex: number;
  zIndex: number;
};

type PlotTransform = {
  left: number;
  top: number;
  width: number;
  height: number;
  xMinimum: number;
  xMaximum: number;
  zMinimum: number;
  zMaximum: number;
};

const FIELD_LABELS: Record<Exclude<MountainWaveField, "cloud_over_wave">, string> = {
  w: "Vertical velocity",
  cloud_liquid: "Cloud liquid water",
  relative_humidity: "Relative humidity",
  theta_perturbation: "Potential-temperature perturbation",
};

export function MountainWavesExplore({
  simulation,
  onBack,
}: {
  simulation: MountainWavesSimulation;
  onBack: () => void;
}) {
  const [viewMode, setViewMode] = useState<ViewMode>(
    simulation.moist_fields_available ? "cloud" : "structure",
  );
  const [field, setField] = useState<Exclude<MountainWaveField, "cloud_over_wave">>("w");
  const [geometryMode, setGeometryMode] = useState<GeometryMode>("expanded");
  const [viewportMode, setViewportMode] = useState<ViewportMode | null>(null);
  const [timeIndex, setTimeIndex] = useState<number | null>(null);
  const [frame, setFrame] = useState<MountainWaveFrame | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [selectedPoint, setSelectedPoint] = useState<PointSelection | null>(null);
  const [cloudPoints, setCloudPoints] = useState(true);
  const [cloudBoundary, setCloudBoundary] = useState(true);
  const [saturationContour, setSaturationContour] = useState(true);
  const [horizontalWind, setHorizontalWind] = useState(true);
  const [structurePotentialTemperatureContours, setStructurePotentialTemperatureContours] =
    useState(true);
  const [cloudPotentialTemperatureContours, setCloudPotentialTemperatureContours] = useState(false);
  const [cloudOpacity, setCloudOpacity] = useState(0.68);
  const [cloudPointSize, setCloudPointSize] = useState(11);
  const [maximized, setMaximized] = useState(false);
  const requestSequence = useRef(0);

  const requestedField: MountainWaveField =
    viewMode === "cloud" ? "cloud_over_wave" : viewMode === "structure" ? "w" : field;
  const potentialTemperatureContours =
    viewMode === "cloud"
      ? cloudPotentialTemperatureContours
      : structurePotentialTemperatureContours;

  const loadFrame = useCallback(async () => {
    const requestId = requestSequence.current + 1;
    requestSequence.current = requestId;
    setLoading(true);
    setError(null);
    try {
      const search = new URLSearchParams({
        field: requestedField,
        time_index: String(timeIndex ?? -1),
      });
      const response = await fetch(
        `/api/worlds/mountain-waves/simulations/${simulation.simulation_id}/frame?${search}`,
      );
      if (!response.ok) {
        throw new Error(await responseMessage(response, "This saved output could not be loaded."));
      }
      const payload = validateFrame(await response.json());
      if (requestId !== requestSequence.current) return;
      setFrame(payload);
      setViewportMode((current) => current ?? payload.viewport.default_mode);
      setSelectedPoint(null);
      if (timeIndex !== null && timeIndex >= payload.times_seconds.length) {
        setTimeIndex(payload.times_seconds.length - 1);
      }
    } catch (caught) {
      if (requestId !== requestSequence.current) return;
      setError(caught instanceof Error ? caught.message : "This saved output could not be loaded.");
      setPlaying(false);
    } finally {
      if (requestId === requestSequence.current) setLoading(false);
    }
  }, [requestedField, simulation.simulation_id, timeIndex]);

  useEffect(() => {
    void loadFrame();
    return () => {
      requestSequence.current += 1;
    };
  }, [loadFrame]);

  useEffect(() => {
    const requestedTimeIndex = timeIndex ?? frame?.time_index ?? null;
    const displayedFrameReady =
      frame !== null && !loading && requestedTimeIndex === frame.time_index;
    if (!playing || !frame || !displayedFrameReady) return;
    const delay = Math.max(120, 900 / playbackSpeed);
    const timer = window.setTimeout(() => {
      setTimeIndex((current) => {
        const activeIndex = current ?? frame.time_index;
        if (activeIndex >= frame.times_seconds.length - 1) {
          setPlaying(false);
          return activeIndex;
        }
        return activeIndex + 1;
      });
    }, delay);
    return () => window.clearTimeout(timer);
  }, [frame, loading, playbackSpeed, playing, timeIndex]);

  useEffect(() => {
    if (viewMode === "cloud" && !simulation.moist_fields_available) setViewMode("structure");
  }, [simulation.moist_fields_available, viewMode]);

  useEffect(() => {
    setViewportMode(null);
  }, [simulation.simulation_id]);

  const fieldOptions = useMemo(
    () =>
      (frame?.field_options ?? []).filter(
        (option): option is Exclude<MountainWaveField, "cloud_over_wave"> =>
          ["w", "cloud_liquid", "relative_humidity", "theta_perturbation"].includes(option),
      ),
    [frame?.field_options],
  );
  const selectedEvidence = selectedPoint && frame ? pointEvidence(frame, selectedPoint) : null;

  return (
    <IntegratedExploreWorkspace
      worldName="Mountain Waves"
      simulationName={simulation.display_name}
      onBack={onBack}
    >
      <section
        className={`visualizer-shell mountain-waves-explore-shell${
          maximized ? " mountain-waves-explore-shell-maximized" : ""
        }`}
      >
        <section className="mountain-waves-scientific-view" aria-label="Mountain Waves x-z view">
          <header className="instrument-header mountain-waves-instrument-header">
            <div>
              <h2>
                {viewMode === "cloud"
                  ? "Wave Cloud Lens"
                  : viewMode === "structure"
                    ? "Wave Structure Lens"
                    : FIELD_LABELS[field]}
              </h2>
              <p>
                Native x-z cross-section · {formatTime(frame?.time_seconds ?? 0)} ·{" "}
                {viewportMode === "focus" ? "Focus region" : "Full domain"} ·{" "}
                {geometryMode === "expanded" ? "Expanded height" : "True physical scale"}
              </p>
            </div>
            <div className="instrument-actions">
              <div className="instrument-view-toggle" aria-label="View">
                <button
                  type="button"
                  className={viewMode === "field" ? "active-control" : ""}
                  onClick={() => setViewMode("field")}
                >
                  Field
                </button>
                <button
                  type="button"
                  className={viewMode === "structure" ? "active-control" : ""}
                  onClick={() => setViewMode("structure")}
                >
                  Wave Structure Lens
                </button>
                {simulation.moist_fields_available && (
                  <button
                    type="button"
                    className={viewMode === "cloud" ? "active-control" : ""}
                    onClick={() => setViewMode("cloud")}
                  >
                    Wave Cloud Lens
                  </button>
                )}
              </div>
              <button
                type="button"
                className="viewer-maximize-button"
                aria-label={
                  maximized ? "Restore Mountain Waves view" : "Maximize Mountain Waves view"
                }
                title={maximized ? "Restore view" : "Maximize view"}
                onClick={() => setMaximized((current) => !current)}
              >
                <span aria-hidden="true">{maximized ? "┘" : "⛶"}</span>
              </button>
            </div>
          </header>

          <div className="mountain-waves-science-body">
            {error ? (
              <section className="layer-local-error mountain-waves-local-error">
                <h3>Saved output unavailable</h3>
                <p role="alert">{error}</p>
                <button type="button" onClick={() => void loadFrame()}>
                  Retry frame
                </button>
              </section>
            ) : frame ? (
              <>
                <TerrainPlot
                  frame={frame}
                  geometryMode={geometryMode}
                  viewportMode={viewportMode ?? frame.viewport.default_mode}
                  viewMode={viewMode}
                  cloudPoints={cloudPoints}
                  cloudBoundary={cloudBoundary}
                  cloudOpacity={cloudOpacity}
                  cloudPointSize={cloudPointSize}
                  saturationContour={saturationContour}
                  horizontalWind={horizontalWind}
                  potentialTemperatureContours={potentialTemperatureContours}
                  selectedPoint={selectedPoint}
                  onSelectPoint={setSelectedPoint}
                />
                <MountainWavesLegend
                  frame={frame}
                  viewMode={viewMode}
                  cloudPoints={cloudPoints}
                  horizontalWind={horizontalWind}
                  potentialTemperatureContours={potentialTemperatureContours}
                />
              </>
            ) : (
              <div className="mountain-waves-plot-loading" role="status">
                Loading saved output...
              </div>
            )}
            {loading && frame && (
              <div className="mountain-waves-frame-loading" role="status">
                Loading frame...
              </div>
            )}
          </div>
        </section>

        <section className="mountain-waves-control-strip" aria-label="Visualization controls">
          {frame?.viewport.focus_available && (
            <fieldset className="mountain-waves-viewport-control">
              <legend>Viewport</legend>
              <div className="segmented-buttons">
                <button
                  type="button"
                  className={viewportMode === "focus" ? "active-control" : ""}
                  onClick={() => setViewportMode("focus")}
                >
                  Focus region
                </button>
                <button
                  type="button"
                  className={viewportMode === "full" ? "active-control" : ""}
                  onClick={() => setViewportMode("full")}
                >
                  Full domain
                </button>
              </div>
            </fieldset>
          )}

          <fieldset className="mountain-waves-geometry-control">
            <legend>Geometry</legend>
            <div className="segmented-buttons">
              <button
                type="button"
                className={geometryMode === "expanded" ? "active-control" : ""}
                onClick={() => setGeometryMode("expanded")}
              >
                Expanded height
              </button>
              <button
                type="button"
                className={geometryMode === "physical" ? "active-control" : ""}
                onClick={() => setGeometryMode("physical")}
              >
                True physical scale
              </button>
            </div>
          </fieldset>

          {viewMode === "field" && (
            <fieldset className="mountain-waves-field-control">
              <legend>Field</legend>
              <label>
                <select
                  aria-label="Field"
                  value={field}
                  onChange={(event) => setField(event.target.value as typeof field)}
                >
                  {fieldOptions.map((option) => (
                    <option key={option} value={option}>
                      {FIELD_LABELS[option]}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>
          )}

          {viewMode !== "field" && (
            <fieldset className="mountain-waves-overlay-controls">
              <legend>Overlays</legend>
              <label>
                <input
                  type="checkbox"
                  checked={horizontalWind}
                  onChange={(event) => setHorizontalWind(event.target.checked)}
                />
                Horizontal wind
              </label>
              {viewMode === "cloud" && (
                <>
                  <label>
                    <input
                      type="checkbox"
                      checked={cloudPoints}
                      onChange={(event) => setCloudPoints(event.target.checked)}
                    />
                    Cloud points
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={cloudBoundary}
                      onChange={(event) => setCloudBoundary(event.target.checked)}
                    />
                    Cloud boundary
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={saturationContour}
                      onChange={(event) => setSaturationContour(event.target.checked)}
                    />
                    RH = 100%
                  </label>
                </>
              )}
              <label>
                <input
                  type="checkbox"
                  checked={potentialTemperatureContours}
                  onChange={(event) => {
                    if (viewMode === "cloud") {
                      setCloudPotentialTemperatureContours(event.target.checked);
                    } else {
                      setStructurePotentialTemperatureContours(event.target.checked);
                    }
                  }}
                />
                Potential temperature
              </label>
              {viewMode === "cloud" && cloudPoints && (
                <div className="mountain-waves-cloud-rendering-controls">
                  <label htmlFor="mountain-waves-cloud-opacity">
                    Cloud opacity
                    <input
                      id="mountain-waves-cloud-opacity"
                      aria-label="Cloud opacity"
                      type="range"
                      min={0.1}
                      max={1}
                      step={0.01}
                      value={cloudOpacity}
                      onChange={(event) => setCloudOpacity(Number(event.target.value))}
                    />
                    <output htmlFor="mountain-waves-cloud-opacity">{cloudOpacity}</output>
                  </label>
                  <label htmlFor="mountain-waves-cloud-point-size">
                    Cloud point size
                    <input
                      id="mountain-waves-cloud-point-size"
                      aria-label="Cloud point size"
                      type="range"
                      min={3}
                      max={18}
                      value={cloudPointSize}
                      onChange={(event) => setCloudPointSize(Number(event.target.value))}
                    />
                    <output htmlFor="mountain-waves-cloud-point-size">{cloudPointSize}px</output>
                  </label>
                </div>
              )}
            </fieldset>
          )}
        </section>

        <TimelineControls
          timeIndex={timeIndex ?? frame?.time_index ?? 0}
          times={frame?.times_seconds ?? []}
          playing={playing}
          playbackSpeed={playbackSpeed}
          onTimeIndex={setTimeIndex}
          onPlaying={setPlaying}
          onPlaybackSpeed={setPlaybackSpeed}
        />

        <ExploreInspector
          sections={{
            explain: (
              <MountainWavesContext
                simulation={simulation}
                frame={frame}
                viewMode={viewMode}
                geometryMode={geometryMode}
                viewportMode={viewportMode ?? frame?.viewport.default_mode ?? "full"}
                selectedEvidence={selectedEvidence}
                onClearSelection={() => setSelectedPoint(null)}
              />
            ),
            notes: (
              <section className="mountain-waves-notebook">
                <h3>Experiment question</h3>
                <p>
                  {simulation.user_question ||
                    "No question was recorded for this Simulation. New questions can be attached when creating a Variation in the Lab."}
                </p>
              </section>
            ),
            details: <MountainWavesDetails simulation={simulation} frame={frame} />,
          }}
        />
      </section>
    </IntegratedExploreWorkspace>
  );
}

function TerrainPlot({
  frame,
  geometryMode,
  viewportMode,
  viewMode,
  cloudPoints,
  cloudBoundary,
  cloudOpacity,
  cloudPointSize,
  saturationContour,
  horizontalWind,
  potentialTemperatureContours,
  selectedPoint,
  onSelectPoint,
}: {
  frame: MountainWaveFrame;
  geometryMode: GeometryMode;
  viewportMode: ViewportMode;
  viewMode: ViewMode;
  cloudPoints: boolean;
  cloudBoundary: boolean;
  cloudOpacity: number;
  cloudPointSize: number;
  saturationContour: boolean;
  horizontalWind: boolean;
  potentialTemperatureContours: boolean;
  selectedPoint: PointSelection | null;
  onSelectPoint: (point: PointSelection | null) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const transformRef = useRef<PlotTransform | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const render = () => {
      transformRef.current = drawTerrainFrame(canvas, frame, {
        geometryMode,
        viewportMode,
        viewMode,
        cloudPoints,
        cloudBoundary,
        cloudOpacity,
        cloudPointSize,
        saturationContour,
        horizontalWind,
        potentialTemperatureContours,
        selectedPoint,
      });
    };
    render();
    const observer = new ResizeObserver(render);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [
    cloudBoundary,
    cloudOpacity,
    cloudPoints,
    cloudPointSize,
    frame,
    geometryMode,
    horizontalWind,
    potentialTemperatureContours,
    saturationContour,
    selectedPoint,
    viewportMode,
    viewMode,
  ]);

  function selectPoint(event: ReactMouseEvent<HTMLCanvasElement>) {
    const transform = transformRef.current;
    const canvas = canvasRef.current;
    if (!transform || !canvas) return;
    const rect = canvas.getBoundingClientRect();
    const xPixel = event.clientX - rect.left;
    const yPixel = event.clientY - rect.top;
    if (
      xPixel < transform.left ||
      xPixel > transform.left + transform.width ||
      yPixel < transform.top ||
      yPixel > transform.top + transform.height
    ) {
      onSelectPoint(null);
      return;
    }
    const xModel =
      transform.xMinimum +
      ((xPixel - transform.left) / transform.width) * (transform.xMaximum - transform.xMinimum);
    const xIndex = nearestIndex(frame.geometry.x_center_m, xModel);
    const zModel =
      transform.zMinimum +
      (transform.zMaximum - transform.zMinimum) * (1 - (yPixel - transform.top) / transform.height);
    const heights = frame.geometry.scalar_height_m.map((row) => row[xIndex]);
    const zIndex = nearestIndex(heights, zModel);
    onSelectPoint({ xIndex, zIndex });
  }

  const viewport = frame.viewport[viewportMode];
  const xMinimum = viewport.x_minimum_m / 1_000;
  const xMaximum = viewport.x_maximum_m / 1_000;
  const zMaximum = viewport.z_maximum_m / 1_000;
  return (
    <div className="mountain-waves-plot-column">
      <div className="mountain-waves-y-axis-label">z (km)</div>
      <span className="mountain-waves-y-axis-maximum">{formatAxis(zMaximum)}</span>
      <span className="mountain-waves-y-axis-minimum">0</span>
      <div className="mountain-waves-canvas-wrap">
        <canvas
          ref={canvasRef}
          aria-label={`${frame.field.display_name} terrain-following x-z view`}
          onClick={selectPoint}
        />
      </div>
      <div className="mountain-waves-x-axis">
        <span>{formatAxis(xMinimum)}</span>
        <strong>x (km)</strong>
        <span>{formatAxis(xMaximum)}</span>
      </div>
      <p className="mountain-waves-geometry-note">
        {viewportMode === "focus" ? "Focus region · " : "Full domain · "}
        {geometryMode === "expanded"
          ? "expanded height; terrain angles are not literal."
          : "equal x/z physical scale."}
      </p>
    </div>
  );
}

function MountainWavesLegend({
  frame,
  viewMode,
  cloudPoints,
  horizontalWind,
  potentialTemperatureContours,
}: {
  frame: MountainWaveFrame;
  viewMode: ViewMode;
  cloudPoints: boolean;
  horizontalWind: boolean;
  potentialTemperatureContours: boolean;
}) {
  const title =
    viewMode !== "field" || frame.field.key === "w"
      ? "w (m/s)"
      : `${frame.field.display_name} (${frame.field.units})`;
  const intervals = scaleIntervals(frame.scale);
  return (
    <aside className="mountain-waves-legend" aria-label={`${title} legend`}>
      <strong>{title}</strong>
      <p>Frame max {formatSigned(frame.scale.selected_time_maximum)}</p>
      <ol>
        {intervals.map((interval) => (
          <li key={`${interval.color}-${interval.label}`}>
            <span style={{ backgroundColor: interval.color }} />
            <b>{interval.label}</b>
          </li>
        ))}
      </ol>
      <p>Frame min {formatSigned(frame.scale.selected_time_minimum)}</p>
      <small>Fixed across this Simulation</small>
      {viewMode === "cloud" && cloudPoints && frame.overlay && (
        <div className="mountain-waves-cloud-key">
          <span className="mountain-waves-cloud-point-key" aria-hidden="true" />
          <span>
            Cloudy native cell · ql ≥ {formatCloudThreshold(frame.overlay.threshold)} g/kg
            <small>Point opacity increases with ql.</small>
          </span>
        </div>
      )}
      {viewMode !== "field" && (horizontalWind || potentialTemperatureContours) && (
        <div className="mountain-waves-lens-keys">
          {horizontalWind && (
            <>
              <span className="mountain-waves-wind-key" aria-hidden="true">
                →
              </span>
              <span>u reference {formatNumber(frame.lens.horizontal_wind_reference_m_s)} m/s</span>
            </>
          )}
          {potentialTemperatureContours && (
            <>
              <span className="mountain-waves-theta-key" aria-hidden="true" />
              <span>
                θ every {formatNumber(frame.lens.potential_temperature_contour_interval_k)} K
              </span>
            </>
          )}
        </div>
      )}
    </aside>
  );
}

function TimelineControls({
  timeIndex,
  times,
  playing,
  playbackSpeed,
  onTimeIndex,
  onPlaying,
  onPlaybackSpeed,
}: {
  timeIndex: number;
  times: number[];
  playing: boolean;
  playbackSpeed: number;
  onTimeIndex: (value: number) => void;
  onPlaying: (value: boolean) => void;
  onPlaybackSpeed: (value: number) => void;
}) {
  const disabled = times.length === 0;
  return (
    <fieldset className="explore-control-card explore-control-card-time mountain-waves-timeline">
      <legend>Time</legend>
      <div className="frame-step-controls">
        <button
          type="button"
          aria-label="Previous saved output"
          title="Previous saved output"
          disabled={disabled || timeIndex === 0}
          onClick={() => onTimeIndex(Math.max(0, timeIndex - 1))}
        >
          <span aria-hidden="true">‹</span>
        </button>
        <button
          type="button"
          aria-label="Next saved output"
          title="Next saved output"
          disabled={disabled || timeIndex >= times.length - 1}
          onClick={() => onTimeIndex(Math.min(times.length - 1, timeIndex + 1))}
        >
          <span aria-hidden="true">›</span>
        </button>
      </div>
      <div className="timelapse-controls">
        <button
          type="button"
          aria-label={playing ? "Pause" : "Play"}
          title={playing ? "Pause" : "Play"}
          disabled={disabled}
          onClick={() => onPlaying(!playing)}
        >
          {playing ? (
            <span className="timelapse-icon timelapse-icon-pause" aria-hidden="true">
              <span />
              <span />
            </span>
          ) : (
            <span className="timelapse-icon timelapse-icon-play" aria-hidden="true">
              <span />
            </span>
          )}
        </button>
      </div>
      <label htmlFor="mountain-waves-time-scrubber">
        <span className="timeline-label">Saved output</span>
        <input
          id="mountain-waves-time-scrubber"
          type="range"
          min="0"
          max={Math.max(0, times.length - 1)}
          value={timeIndex}
          disabled={disabled}
          onChange={(event) => onTimeIndex(Number(event.target.value))}
        />
        <span className="slice-position-label">
          {formatTime(times[timeIndex] ?? 0)}
          <small>
            frame {disabled ? 0 : timeIndex + 1} of {times.length}
          </small>
        </span>
      </label>
      <label>
        Speed
        <select
          value={playbackSpeed}
          onChange={(event) => onPlaybackSpeed(Number(event.target.value))}
        >
          <option value="0.5">0.5x</option>
          <option value="1">1x</option>
          <option value="2">2x</option>
          <option value="4">4x</option>
        </select>
      </label>
    </fieldset>
  );
}

function MountainWavesContext({
  simulation,
  frame,
  viewMode,
  geometryMode,
  viewportMode,
  selectedEvidence,
  onClearSelection,
}: {
  simulation: MountainWavesSimulation;
  frame: MountainWaveFrame | null;
  viewMode: ViewMode;
  geometryMode: GeometryMode;
  viewportMode: ViewportMode;
  selectedEvidence: ReturnType<typeof pointEvidence> | null;
  onClearSelection: () => void;
}) {
  if (selectedEvidence) {
    return (
      <section className="selected-region-inspector mountain-waves-point-context">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Selected point</p>
            <h3>Native cell evidence</h3>
          </div>
          <button type="button" className="secondary-button" onClick={onClearSelection}>
            Clear selection
          </button>
        </div>
        <div className="mountain-waves-state-row">
          <span className="state-chip">{selectedEvidence.motionState}</span>
          {selectedEvidence.cloudState && (
            <span className="state-chip">{selectedEvidence.cloudState}</span>
          )}
          {selectedEvidence.saturationState && (
            <span className="state-chip">{selectedEvidence.saturationState}</span>
          )}
        </div>
        <dl className="context-metrics">
          <Metric label="x" value={`${formatNumber(selectedEvidence.xM / 1_000)} km`} />
          <Metric label="Model height" value={`${formatNumber(selectedEvidence.modelHeightM)} m`} />
          <Metric label="Local AGL" value={`${formatNumber(selectedEvidence.aglM)} m`} />
          <Metric label="Model time" value={formatTime(selectedEvidence.timeSeconds)} />
          <Metric label="Horizontal wind" value={`${formatSigned(selectedEvidence.u)} m/s`} />
          <Metric label="Vertical velocity" value={`${formatSigned(selectedEvidence.w)} m/s`} />
          {selectedEvidence.ql !== null && (
            <Metric
              label="Cloud liquid water"
              value={`${formatNumber(selectedEvidence.ql, 4)} g/kg`}
            />
          )}
          {selectedEvidence.rh !== null && (
            <Metric label="Relative humidity" value={`${formatNumber(selectedEvidence.rh, 1)}%`} />
          )}
          <Metric
            label="Potential temperature"
            value={`${formatNumber(selectedEvidence.theta, 1)} K`}
          />
          <Metric
            label="Potential-temperature perturbation"
            value={`${formatSigned(selectedEvidence.thetaPerturbation)} K`}
          />
        </dl>
      </section>
    );
  }

  return (
    <section className="mountain-waves-context-summary">
      <p className="eyebrow">
        {viewMode === "cloud"
          ? "Wave Cloud Lens"
          : viewMode === "structure"
            ? "Wave Structure Lens"
            : "Field"}
      </p>
      <h3>
        {viewMode === "cloud"
          ? "Where does cloud sit within rising and descending wave motion?"
          : viewMode === "structure"
            ? "How is terrain displacing the atmosphere into a gravity wave?"
            : frame?.field.display_name}
      </h3>
      <p>
        {viewMode === "cloud"
          ? "Vertical velocity remains primary. Native-cell cloud points and the black boundary locate cloud liquid water; the RH = 100% contour and horizontal wind show the moist wave environment. Potential-temperature contours can be added for wave structure."
          : viewMode === "structure"
            ? "Vertical velocity remains primary while horizontal wind and total potential-temperature contours reveal the terrain-forced wave."
            : `The selected Field is shown directly on its fixed Simulation scale${frame ? ` in ${frame.field.units}` : ""}.`}
      </p>
      <dl className="context-metrics">
        <Metric label="Simulation" value={simulation.display_name} />
        <Metric label="Atmosphere" value={simulation.moist ? "Moist" : "Dry"} />
        <Metric
          label="Geometry"
          value={geometryMode === "expanded" ? "Expanded height" : "True physical scale"}
        />
        <Metric
          label="Viewport"
          value={viewportMode === "focus" ? "Focus region" : "Full domain"}
        />
        <Metric label="Model time" value={formatTime(frame?.time_seconds ?? 0)} />
        <Metric
          label="Relevant caveat"
          value={
            geometryMode === "expanded"
              ? "Displayed terrain angles are vertically exaggerated for inspection."
              : viewMode === "cloud"
                ? "Cloud state is instantaneous; no formation or erosion process is inferred at a point."
                : simulation.moist
                  ? "Point labels describe the saved instant; they do not infer process direction."
                  : simulation.moist_fields_available
                    ? "The configured atmosphere is dry; retained moisture fields remain available for inspection."
                    : "This dry Simulation contains no water-vapor or cloud fields."
          }
        />
      </dl>
      <p className="context-selection-prompt">
        Select a point in the cross-section for native values.
      </p>
    </section>
  );
}

function MountainWavesDetails({
  simulation,
  frame,
}: {
  simulation: MountainWavesSimulation;
  frame: MountainWaveFrame | null;
}) {
  return (
    <section>
      <h3>Simulation details</h3>
      <dl className="metric-grid">
        <Metric label="Simulation ID" value={simulation.simulation_id} />
        <Metric label="Run ID" value={simulation.run_id} />
        <Metric label="Role" value={simulation.role === "built_in" ? "Built-in" : "Variation"} />
        <Metric label="Native topology" value="2-D x-z; singleton y" />
        <Metric
          label="Saved outputs"
          value={String(frame?.times_seconds.length ?? "Unavailable")}
        />
        <Metric label="Scale" value={frame?.scale.scale_id ?? "Unavailable"} />
      </dl>
      {frame && (
        <details className="technical-details">
          <summary>Visualization provenance</summary>
          <p>{frame.provenance.display_binning}</p>
          <p>{frame.provenance.physical_height_source}</p>
          <code>{frame.provenance.source_history_file}</code>
        </details>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function drawTerrainFrame(
  canvas: HTMLCanvasElement,
  frame: MountainWaveFrame,
  options: {
    geometryMode: GeometryMode;
    viewportMode: ViewportMode;
    viewMode: ViewMode;
    cloudPoints: boolean;
    cloudBoundary: boolean;
    cloudOpacity: number;
    cloudPointSize: number;
    saturationContour: boolean;
    horizontalWind: boolean;
    potentialTemperatureContours: boolean;
    selectedPoint: PointSelection | null;
  },
): PlotTransform | null {
  const context = canvas.getContext("2d");
  if (!context) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, rect.width, rect.height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, rect.width, rect.height);

  const xEdges = frame.geometry.x_edge_m;
  const viewport = frame.viewport[options.viewportMode];
  const xMinimum = viewport.x_minimum_m;
  const xMaximum = viewport.x_maximum_m;
  const zMinimum = viewport.z_minimum_m;
  const zMaximum = viewport.z_maximum_m;
  const domainWidth = xMaximum - xMinimum;
  const domainHeight = zMaximum - zMinimum;
  let plotWidth = rect.width;
  let plotHeight = rect.height;
  let left = 0;
  let top = 0;
  if (options.geometryMode === "physical") {
    const pixelsPerMeter = Math.min(rect.width / domainWidth, rect.height / domainHeight);
    plotWidth = domainWidth * pixelsPerMeter;
    plotHeight = domainHeight * pixelsPerMeter;
    left = (rect.width - plotWidth) / 2;
    top = (rect.height - plotHeight) / 2;
  }
  const transform: PlotTransform = {
    left,
    top,
    width: plotWidth,
    height: plotHeight,
    xMinimum,
    xMaximum,
    zMinimum,
    zMaximum,
  };
  const xPixel = (value: number) => left + ((value - xMinimum) / domainWidth) * plotWidth;
  const zPixel = (value: number) =>
    top + plotHeight - ((value - zMinimum) / domainHeight) * plotHeight;
  const rows = frame.values.length;
  const columns = frame.values[0]?.length ?? 0;

  context.save();
  context.beginPath();
  context.rect(left, top, plotWidth, plotHeight);
  context.clip();
  for (let zIndex = 0; zIndex < rows; zIndex += 1) {
    for (let xIndex = 0; xIndex < columns; xIndex += 1) {
      const lower = frame.geometry.full_height_m[zIndex]?.[xIndex] ?? 0;
      const upper = frame.geometry.full_height_m[zIndex + 1]?.[xIndex] ?? zMaximum;
      const x0 = xPixel(xEdges[xIndex]);
      const x1 = xPixel(xEdges[xIndex + 1]);
      const y0 = zPixel(upper);
      const y1 = zPixel(lower);
      context.fillStyle = scaleColor(frame.values[zIndex][xIndex], frame.scale);
      context.fillRect(x0, y0, Math.max(1, x1 - x0 + 0.5), Math.max(1, y1 - y0 + 0.5));
    }
  }

  const overlay = frame.overlay;
  if (options.viewMode === "cloud" && overlay && options.cloudPoints) {
    const pointSize = scalarPointPixelSize(options.cloudPointSize);
    nativeCloudCellPoints(frame).forEach((point) => {
      context.beginPath();
      context.arc(xPixel(point.xM), zPixel(point.zM), pointSize / 2, 0, Math.PI * 2);
      context.fillStyle = cloudPointColor(point.valueGKg, overlay.threshold, overlay.maximum);
      context.globalAlpha = cloudPointOpacity(
        point.valueGKg,
        overlay.threshold,
        overlay.maximum,
        options.cloudOpacity,
      );
      context.fill();
    });
    context.globalAlpha = 1;
  }
  if (options.viewMode === "cloud" && overlay && options.cloudBoundary) {
    drawMaskBoundary(
      context,
      frame,
      overlay.values,
      (value) => value >= overlay.threshold,
      xPixel,
      zPixel,
      {
        color: "#111820",
        width: 1.5,
      },
    );
  }
  if (
    options.viewMode === "cloud" &&
    options.saturationContour &&
    frame.pointer_context.relative_humidity_percent
  ) {
    drawMaskBoundary(
      context,
      frame,
      frame.pointer_context.relative_humidity_percent,
      (value) => value >= 100,
      xPixel,
      zPixel,
      { color: "#08718d", width: 1.35, dash: [5, 4] },
    );
  }
  if (options.viewMode !== "field" && options.potentialTemperatureContours) {
    drawPotentialTemperatureContours(
      context,
      frame,
      frame.pointer_context.potential_temperature_k,
      xPixel,
      zPixel,
    );
  }
  if (options.viewMode !== "field" && options.horizontalWind) {
    drawHorizontalWind(context, frame, xPixel, zPixel, viewport);
  }

  drawTerrainSilhouette(context, frame, xPixel, zPixel, left, zPixel(zMinimum));
  context.strokeStyle = "#405363";
  context.lineWidth = 1;
  context.strokeRect(
    left + 0.5,
    top + 0.5,
    Math.max(0, plotWidth - 1),
    Math.max(0, plotHeight - 1),
  );

  if (options.selectedPoint) {
    const { xIndex, zIndex } = options.selectedPoint;
    const x = xPixel(frame.geometry.x_center_m[xIndex]);
    const z = zPixel(frame.geometry.scalar_height_m[zIndex][xIndex]);
    context.beginPath();
    context.arc(x, z, 5, 0, Math.PI * 2);
    context.fillStyle = "#ffffff";
    context.fill();
    context.lineWidth = 2;
    context.strokeStyle = "#111820";
    context.stroke();
  }
  context.restore();
  return transform;
}

function drawMaskBoundary(
  context: CanvasRenderingContext2D,
  frame: MountainWaveFrame,
  values: number[][],
  active: (value: number) => boolean,
  xPixel: (value: number) => number,
  zPixel: (value: number) => number,
  style: { color: string; width: number; dash?: number[] },
) {
  const rows = values.length;
  const columns = values[0]?.length ?? 0;
  context.save();
  context.strokeStyle = style.color;
  context.lineWidth = style.width;
  context.setLineDash(style.dash ?? []);
  context.beginPath();
  for (let zIndex = 0; zIndex < rows; zIndex += 1) {
    for (let xIndex = 0; xIndex < columns; xIndex += 1) {
      if (!active(values[zIndex][xIndex])) continue;
      const x0 = xPixel(frame.geometry.x_edge_m[xIndex]);
      const x1 = xPixel(frame.geometry.x_edge_m[xIndex + 1]);
      const y0 = zPixel(frame.geometry.full_height_m[zIndex]?.[xIndex] ?? 0);
      const y1 = zPixel(
        frame.geometry.full_height_m[zIndex + 1]?.[xIndex] ?? frame.geometry.active_top_m,
      );
      if (xIndex === 0 || !active(values[zIndex][xIndex - 1])) {
        context.moveTo(x0, y0);
        context.lineTo(x0, y1);
      }
      if (xIndex === columns - 1 || !active(values[zIndex][xIndex + 1])) {
        context.moveTo(x1, y0);
        context.lineTo(x1, y1);
      }
      if (zIndex === 0 || !active(values[zIndex - 1][xIndex])) {
        context.moveTo(x0, y0);
        context.lineTo(x1, y0);
      }
      if (zIndex === rows - 1 || !active(values[zIndex + 1][xIndex])) {
        context.moveTo(x0, y1);
        context.lineTo(x1, y1);
      }
    }
  }
  context.stroke();
  context.restore();
}

function drawPotentialTemperatureContours(
  context: CanvasRenderingContext2D,
  frame: MountainWaveFrame,
  values: number[][],
  xPixel: (value: number) => number,
  zPixel: (value: number) => number,
) {
  frame.lens.potential_temperature_contour_values_k.forEach((level) => {
    drawMaskBoundary(context, frame, values, (value) => value >= level, xPixel, zPixel, {
      color: "rgba(57, 70, 78, 0.46)",
      width: 0.7,
    });
  });
}

function drawHorizontalWind(
  context: CanvasRenderingContext2D,
  frame: MountainWaveFrame,
  xPixel: (value: number) => number,
  zPixel: (value: number) => number,
  viewport: ViewportBounds,
) {
  const values = frame.pointer_context.horizontal_wind_m_s;
  const rows = values.length;
  const columns = values[0]?.length ?? 0;
  const visibleColumns = frame.geometry.x_center_m.filter(
    (value) => value >= viewport.x_minimum_m && value <= viewport.x_maximum_m,
  ).length;
  const xStep = Math.max(1, Math.floor(visibleColumns / 13));
  const zStep = Math.max(1, Math.floor(rows / 8));
  const reference = Math.max(0.001, frame.lens.horizontal_wind_reference_m_s);

  context.save();
  context.strokeStyle = "rgba(31, 49, 59, 0.82)";
  context.fillStyle = "rgba(31, 49, 59, 0.82)";
  context.lineWidth = 1.15;
  for (let zIndex = 0; zIndex < rows; zIndex += zStep) {
    for (let xIndex = 0; xIndex < columns; xIndex += xStep) {
      const x = frame.geometry.x_center_m[xIndex];
      const z = frame.geometry.scalar_height_m[zIndex]?.[xIndex];
      if (
        z === undefined ||
        x < viewport.x_minimum_m ||
        x > viewport.x_maximum_m ||
        z < viewport.z_minimum_m ||
        z > viewport.z_maximum_m
      ) {
        continue;
      }
      const wind = values[zIndex][xIndex];
      if (!Number.isFinite(wind) || Math.abs(wind) < reference * 0.02) continue;
      const direction = wind >= 0 ? 1 : -1;
      const length = Math.max(5, Math.min(32, (Math.abs(wind) / reference) * 32));
      const startX = xPixel(x) - (direction * length) / 2;
      const endX = xPixel(x) + (direction * length) / 2;
      const y = zPixel(z);
      context.beginPath();
      context.moveTo(startX, y);
      context.lineTo(endX, y);
      context.stroke();
      context.beginPath();
      context.moveTo(endX, y);
      context.lineTo(endX - direction * 4.5, y - 2.8);
      context.lineTo(endX - direction * 4.5, y + 2.8);
      context.closePath();
      context.fill();
    }
  }
  context.restore();
}

function drawTerrainSilhouette(
  context: CanvasRenderingContext2D,
  frame: MountainWaveFrame,
  xPixel: (value: number) => number,
  zPixel: (value: number) => number,
  left: number,
  bottom: number,
) {
  context.beginPath();
  context.moveTo(left, bottom);
  frame.geometry.x_center_m.forEach((x, index) => {
    context.lineTo(xPixel(x), zPixel(frame.geometry.terrain_m[index]));
  });
  context.lineTo(xPixel(frame.geometry.x_edge_m.at(-1)!), bottom);
  context.closePath();
  context.fillStyle = "#26343d";
  context.fill();
}

function scaleColor(value: number, scale: TerrainScale): string {
  const index = scale.breakpoints.findIndex((breakpoint) => value < breakpoint);
  return scale.colors[index === -1 ? scale.colors.length - 1 : index] ?? "#ffffff";
}

function scaleIntervals(scale: TerrainScale): Array<{ color: string; label: string }> {
  const lowToHigh = scale.colors.map((color, index) => {
    if (index === 0) return { color, label: `< ${formatSigned(scale.breakpoints[0])}` };
    if (index === scale.colors.length - 1) {
      return { color, label: `≥ ${formatSigned(scale.breakpoints.at(-1)!)}` };
    }
    return {
      color,
      label: `${formatSigned(scale.breakpoints[index - 1])} to < ${formatSigned(scale.breakpoints[index])}`,
    };
  });
  return lowToHigh.reverse();
}

function pointEvidence(frame: MountainWaveFrame, point: PointSelection) {
  const { xIndex, zIndex } = point;
  const u = frame.pointer_context.horizontal_wind_m_s[zIndex][xIndex];
  const w = frame.pointer_context.vertical_velocity_m_s[zIndex][xIndex];
  const theta = frame.pointer_context.potential_temperature_k[zIndex][xIndex];
  const ql = frame.pointer_context.cloud_liquid_g_kg?.[zIndex]?.[xIndex] ?? null;
  const rh = frame.pointer_context.relative_humidity_percent?.[zIndex]?.[xIndex] ?? null;
  const thetaPerturbation = frame.pointer_context.theta_perturbation_k[zIndex][xIndex];
  const modelHeightM = frame.geometry.scalar_height_m[zIndex][xIndex];
  const terrainM = frame.geometry.terrain_m[xIndex];
  const neutralThreshold = frame.lens.vertical_velocity_neutral_threshold_m_s;
  return {
    xM: frame.geometry.x_center_m[xIndex],
    modelHeightM,
    aglM: modelHeightM - terrainM,
    timeSeconds: frame.time_seconds,
    u,
    w,
    theta,
    ql,
    rh,
    thetaPerturbation,
    motionState: Math.abs(w) <= neutralThreshold ? "Near neutral" : w > 0 ? "Rising" : "Descending",
    cloudState: ql === null ? null : ql >= (frame.overlay?.threshold ?? 0.001) ? "Cloudy" : "Clear",
    saturationState: rh === null ? null : rh >= 100 ? "Saturated" : "Unsaturated",
  };
}

function nearestIndex(values: number[], target: number): number {
  let selected = 0;
  let distance = Number.POSITIVE_INFINITY;
  values.forEach((value, index) => {
    const nextDistance = Math.abs(value - target);
    if (nextDistance < distance) {
      selected = index;
      distance = nextDistance;
    }
  });
  return selected;
}

function validateFrame(value: unknown): MountainWaveFrame {
  if (
    typeof value !== "object" ||
    value === null ||
    !("schema_version" in value) ||
    value.schema_version !== "mountain_waves_explore_v1"
  ) {
    throw new Error("Mountain Waves frame response does not match the required contract.");
  }
  return value as MountainWaveFrame;
}

function formatTime(seconds: number): string {
  return `${new Intl.NumberFormat("en-US").format(seconds)} s`;
}

function formatAxis(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

function formatNumber(value: number, maximumFractionDigits = 2): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(value);
}

function formatCloudThreshold(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 }).format(value);
}

function formatSigned(value: number): string {
  const formatted = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
  return value > 0 ? `+${formatted}` : formatted;
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}

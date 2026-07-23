/* eslint-disable react-refresh/only-export-components */
import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties, MouseEvent as ReactMouseEvent } from "react";

import "./App.css";
import "./StormExaminationResearch.css";
import {
  ExploreInspector,
  ExploreSecondarySections,
  IntegratedExploreWorkspace,
} from "./IntegratedExploreWorkspace";

export type LensId = "rotating_updraft" | "cloud_precipitation" | "low_level_interactions";
export type ViewportId = "storm" | "full";
export type SectionOrientation = "xz" | "yz";

export type ScaleMetadata = {
  scale_id: string;
  display_name: string;
  units: string;
  scale_type: "fixed_discrete" | "fixed_continuous" | "categorical";
  minimum: number;
  maximum: number;
  breakpoints: number[];
  colors: string[];
  fixed_across_time: boolean;
};

export type FieldLayer = {
  key: string;
  display_name: string;
  units: string;
  evidence_kind: "native" | "derived";
  source_fields: string[];
  derivation: string | null;
  values: Array<Array<number | null>>;
  selected_frame_minimum: number;
  selected_frame_maximum: number;
  scale: ScaleMetadata;
};

export type CategoryDefinition = {
  code: number;
  key: string;
  label: string;
  color: string;
};

export type CategoryLayer = {
  key: string;
  display_name: string;
  evidence_kind: "derived";
  source_fields: string[];
  derivation: string;
  values: number[][];
  magnitude: FieldLayer;
  categories: CategoryDefinition[];
};

export type WindVector = {
  x_km: number;
  y_km: number;
  u_m_s: number;
  v_m_s: number;
  magnitude_m_s: number;
};

export type PlanView = {
  title: string;
  subtitle: string;
  x_indices: number[];
  y_indices: number[];
  x_km: number[];
  y_km: number[];
  level_index: number;
  level_km: number;
  selection_z_indices: number[][] | null;
  primary: FieldLayer;
  overlays: Record<string, FieldLayer>;
  categories: CategoryLayer | null;
  wind_vectors: WindVector[];
};

export type VerticalSection = {
  orientation: SectionOrientation;
  title: string;
  horizontal_dimension: "x" | "y";
  horizontal_indices: number[];
  horizontal_km: number[];
  z_km: number[];
  cross_section_coordinate_km: number;
  primary: FieldLayer;
  overlays: Record<string, FieldLayer>;
  categories: CategoryLayer | null;
};

export type SelectedPoint = {
  x_index: number;
  y_index: number;
  z_index: number;
  x_km: number;
  y_km: number;
  z_km: number;
  model_time_seconds: number;
  coordinate_frame: string;
  values: Record<string, number>;
  units: Record<string, string>;
  evidence_kind: Record<string, "native" | "derived">;
  states: string[];
  distance_to_primary_updraft_km: number;
};

export type VolumeLayer = {
  key: string;
  display_name: string;
  units: string;
  evidence_kind: "native" | "derived";
  source_fields: string[];
  derivation: string | null;
  rendering: "neutral_cloud" | "signed_scalar" | "scalar" | "categorical";
  points: Array<[number, number, number, number, number]>;
  source_count: number;
  returned_count: number;
  threshold_label: string;
  default_visible: boolean;
  default_opacity: number;
  default_point_size: number;
  scale: ScaleMetadata | null;
  categories: CategoryDefinition[];
};

export type StormVolumeScene = {
  coordinate_extents_km: Record<"x" | "y" | "z", { min: number; max: number }>;
  coordinate_sizes: Record<"x" | "y" | "z", number>;
  coordinate_indices: Record<"x" | "y" | "z", number[]>;
  coordinate_values_km: Record<"x" | "y" | "z", number[]>;
  layers: VolumeLayer[];
  wind_vectors: Array<{
    x_km: number;
    y_km: number;
    z_km: number;
    u_m_s: number;
    v_m_s: number;
    magnitude_m_s: number;
  }>;
  wind_reference_m_s: number;
  point_budget: number;
  source_history_file: string;
};

export type StormExaminationFrame = {
  schema_version: "storm_examination_gate_c_v1" | "supercells_explore_v1";
  authority_state: "issue_418_gate_c_research_not_product" | "supercells_product_world";
  world_id: "supercells" | null;
  simulation_id: "supercells_quarter_circle_reference" | null;
  run_id: string;
  case_id: string;
  simulation_label: string;
  lens_id: LensId;
  lens_name: string;
  lens_question: string;
  what_to_notice_now: string;
  what_to_notice_by_view?: Partial<Record<"plan" | "xz" | "yz", string>> | null;
  time_index: number;
  time_seconds: number;
  times_seconds: number[];
  mature_checkpoint_indices: number[];
  timeline_checkpoints: Array<{
    time_seconds: number;
    label: string;
    phase: string;
    phase_kind: "visible_checkpoint" | "bounded_inference";
  }>;
  viewport: ViewportId;
  viewport_bounds_km: Record<"x_min" | "x_max" | "y_min" | "y_max", number>;
  primary_updraft: {
    x_index: number;
    y_index: number;
    z_index: number;
    x_km: number;
    y_km: number;
    z_km: number;
    w_m_s: number;
  };
  selected_point: SelectedPoint;
  plan: PlanView;
  xz_section: VerticalSection;
  yz_section: VerticalSection;
  scene: StormVolumeScene | null;
  caveats: string[];
  provenance: Record<string, string>;
  extraction_milliseconds: number;
};

export type Selection = { xIndex: number; yIndex: number; zIndex: number };
export type OverlayState = {
  rotation: boolean;
  updraftHelicity: boolean;
  reflectivity: boolean;
  condensate: boolean;
  rain: boolean;
  wind: boolean;
  precipitatingCondensate: boolean;
  verticalMotion: boolean;
};

type PlotGeometry = {
  left: number;
  top: number;
  width: number;
  height: number;
  xMinimum: number;
  xMaximum: number;
  yMinimum: number;
  yMaximum: number;
};

const LENSES: Array<{ id: LensId; label: string }> = [
  { id: "rotating_updraft", label: "Rotating Updraft" },
  { id: "cloud_precipitation", label: "Cloud and Precipitation" },
  { id: "low_level_interactions", label: "Low-Level Interactions" },
];

const INITIAL_OVERLAYS: OverlayState = {
  rotation: true,
  updraftHelicity: true,
  reflectivity: true,
  condensate: true,
  rain: true,
  wind: true,
  precipitatingCondensate: true,
  verticalMotion: true,
};

const HYDROMETEOR_SHORT: Record<string, string> = {
  qc: "Cloud liquid",
  qr: "Rain",
  qi: "Cloud ice",
  qs: "Snow",
  qg: "Hail-treated large ice",
};

export function StormExaminationResearch() {
  const [lens, setLens] = useState<LensId>("rotating_updraft");
  const [viewport, setViewport] = useState<ViewportId>("storm");
  const [timeIndex, setTimeIndex] = useState(5);
  const [frame, setFrame] = useState<StormExaminationFrame | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [followPrimary, setFollowPrimary] = useState(true);
  const [overlays, setOverlays] = useState(INITIAL_OVERLAYS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [maximized, setMaximized] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);

  const loadFrame = useCallback(
    async (signal: AbortSignal) => {
      setLoading(true);
      setError(null);
      const search = new URLSearchParams({
        lens,
        viewport,
        time_index: String(timeIndex),
      });
      if (!followPrimary && selection) {
        search.set("x_index", String(selection.xIndex));
        search.set("y_index", String(selection.yIndex));
        search.set("z_index", String(selection.zIndex));
      }
      try {
        const response = await fetch(`/api/research/storm-examination?${search}`, { signal });
        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
          throw new Error(payload?.detail ?? `Storm evidence failed (${response.status}).`);
        }
        setFrame((await response.json()) as StormExaminationFrame);
      } catch (reason: unknown) {
        if (!signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Storm evidence failed.");
        }
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    },
    [followPrimary, lens, selection, timeIndex, viewport],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadFrame(controller.signal);
    return () => controller.abort();
  }, [loadFrame, retryNonce]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setTimeIndex((current) => (current >= 8 ? 3 : current + 1));
    }, 1_200 / playbackSpeed);
    return () => window.clearInterval(timer);
  }, [playbackSpeed, playing]);

  const selectPoint = useCallback((next: Selection) => {
    setPlaying(false);
    setFollowPrimary(false);
    setSelection(next);
  }, []);

  function chooseLens(next: LensId) {
    setPlaying(false);
    setLens(next);
    setFollowPrimary(true);
    setSelection(null);
  }

  const checkpoint = frame?.timeline_checkpoints.find(
    (item) => item.time_seconds === frame.time_seconds,
  );

  return (
    <main className="app-shell app-shell-explore storm-research-page">
      <header className="topbar storm-research-topbar">
        <div className="brand-mark">
          <h1>Cloud Chamber</h1>
        </div>
        <span>Gate C research surface</span>
      </header>
      <IntegratedExploreWorkspace
        worldName="Storm examination"
        simulationName="Quarter-Circle Supercell Benchmark"
      >
        <section
          className={`storm-explore-shell${maximized ? " storm-explore-shell-maximized" : ""}`}
        >
          <section className="storm-scientific-workspace" aria-label="Storm examination views">
            <header className="instrument-header storm-instrument-header">
              <div>
                <h2>{frame?.lens_name ?? LENSES.find((item) => item.id === lens)?.label}</h2>
                <p>
                  Coordinated native-grid evidence · {formatTime(frame?.time_seconds ?? 0)} ·{" "}
                  {viewport === "storm" ? "Storm region" : "Full domain"}
                </p>
              </div>
              <div className="instrument-actions">
                <div className="instrument-view-toggle storm-lens-toggle" aria-label="Lens">
                  {LENSES.map((item) => (
                    <button
                      type="button"
                      key={item.id}
                      className={lens === item.id ? "active-control" : ""}
                      aria-pressed={lens === item.id}
                      onClick={() => chooseLens(item.id)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="viewer-maximize-button"
                  aria-label={
                    maximized ? "Restore coordinated views" : "Maximize coordinated views"
                  }
                  title={maximized ? "Restore views" : "Maximize views"}
                  onClick={() => setMaximized((current) => !current)}
                >
                  <span className="storm-maximize-icon" aria-hidden="true" />
                </button>
              </div>
            </header>

            {error ? (
              <section className="layer-local-error storm-local-error">
                <h3>Retained storm evidence unavailable</h3>
                <p role="alert">{error}</p>
                <button type="button" onClick={() => setRetryNonce((current) => current + 1)}>
                  Retry
                </button>
              </section>
            ) : frame ? (
              <div className="storm-view-grid">
                <StormPlanPlot frame={frame} overlays={overlays} onSelect={selectPoint} />
                <div className="storm-section-stack">
                  <StormSectionPlot
                    section={frame.xz_section}
                    frame={frame}
                    overlays={overlays}
                    onSelect={selectPoint}
                  />
                  <StormSectionPlot
                    section={frame.yz_section}
                    frame={frame}
                    overlays={overlays}
                    onSelect={selectPoint}
                  />
                </div>
                <StormLegend frame={frame} overlays={overlays} />
              </div>
            ) : (
              <div className="storm-loading" role="status">
                Loading retained storm evidence...
              </div>
            )}
            {loading && frame && <div className="storm-frame-loading">Loading frame...</div>}
          </section>

          <StormControls
            lens={lens}
            viewport={viewport}
            overlays={overlays}
            followPrimary={followPrimary}
            onViewport={setViewport}
            onOverlays={setOverlays}
            onFollowPrimary={() => {
              setFollowPrimary(true);
              setSelection(null);
            }}
          />

          <StormTimeline
            timeIndex={timeIndex}
            times={frame?.times_seconds ?? []}
            matureIndices={frame?.mature_checkpoint_indices ?? [3, 4, 5, 6, 7, 8]}
            playing={playing}
            playbackSpeed={playbackSpeed}
            checkpoint={checkpoint?.phase}
            onTimeIndex={(next) => {
              setPlaying(false);
              setTimeIndex(next);
            }}
            onPlaying={setPlaying}
            onPlaybackSpeed={setPlaybackSpeed}
          />

          <ExploreInspector>
            <StormContext frame={frame} lens={lens} viewport={viewport} />
          </ExploreInspector>
          <ExploreSecondarySections
            label="Research support"
            sections={{
              science: (
                <section>
                  <h3>Gate C examination</h3>
                  <p>
                    This bounded surface evaluates whether one retained storm result supports a
                    legible Storms World. It is not a product route or a final Lens contract.
                  </p>
                </section>
              ),
              notes: (
                <section>
                  <h3>Simulation notes</h3>
                  <p>Durable notes are available from the Supercells World Explore route.</p>
                </section>
              ),
              details: <StormDetails frame={frame} />,
            }}
          />
        </section>
      </IntegratedExploreWorkspace>
    </main>
  );
}

function StormControls({
  lens,
  viewport,
  overlays,
  followPrimary,
  onViewport,
  onOverlays,
  onFollowPrimary,
}: {
  lens: LensId;
  viewport: ViewportId;
  overlays: OverlayState;
  followPrimary: boolean;
  onViewport: (value: ViewportId) => void;
  onOverlays: (value: OverlayState) => void;
  onFollowPrimary: () => void;
}) {
  const applicable =
    lens === "rotating_updraft"
      ? [
          ["rotation", "Rotation"],
          ["updraftHelicity", "2-5 km UH"],
          ["reflectivity", "Reflectivity"],
          ["condensate", "Condensate boundary"],
        ]
      : lens === "cloud_precipitation"
        ? [
            ["reflectivity", "Reflectivity"],
            ["verticalMotion", "Vertical-motion contours"],
          ]
        : [
            ["rain", "Accumulated rain"],
            ["reflectivity", "Reflectivity"],
            ["wind", "Model-relative flow"],
            ["precipitatingCondensate", "Precipitating condensate"],
          ];
  return (
    <section className="storm-control-strip" aria-label="Visualization controls">
      <fieldset>
        <legend>Viewport</legend>
        <div className="segmented-buttons">
          <button
            type="button"
            className={viewport === "storm" ? "active-control" : ""}
            onClick={() => onViewport("storm")}
          >
            Storm region
          </button>
          <button
            type="button"
            className={viewport === "full" ? "active-control" : ""}
            onClick={() => onViewport("full")}
          >
            Full domain
          </button>
        </div>
      </fieldset>
      <fieldset className="storm-overlay-controls">
        <legend>Evidence</legend>
        {applicable.map(([key, label]) => (
          <label key={key}>
            <input
              type="checkbox"
              checked={overlays[key as keyof OverlayState]}
              onChange={(event) => onOverlays({ ...overlays, [key]: event.currentTarget.checked })}
            />
            {label}
          </label>
        ))}
      </fieldset>
      <fieldset>
        <legend>Sections</legend>
        <button type="button" disabled={followPrimary} onClick={onFollowPrimary}>
          {followPrimary ? "Following strongest updraft" : "Return to strongest updraft"}
        </button>
      </fieldset>
    </section>
  );
}

function StormTimeline({
  timeIndex,
  times,
  matureIndices,
  playing,
  playbackSpeed,
  checkpoint,
  onTimeIndex,
  onPlaying,
  onPlaybackSpeed,
}: {
  timeIndex: number;
  times: number[];
  matureIndices: number[];
  playing: boolean;
  playbackSpeed: number;
  checkpoint?: string;
  onTimeIndex: (value: number) => void;
  onPlaying: (value: boolean) => void;
  onPlaybackSpeed: (value: number) => void;
}) {
  const disabled = times.length === 0;
  return (
    <fieldset className="explore-control-card explore-control-card-time storm-timeline">
      <legend>Time</legend>
      <div className="frame-step-controls">
        <button
          type="button"
          aria-label="Previous saved output"
          title="Previous saved output"
          disabled={disabled || timeIndex <= 3}
          onClick={() => onTimeIndex(Math.max(3, timeIndex - 1))}
        >
          <span aria-hidden="true">&lsaquo;</span>
        </button>
        <button
          type="button"
          aria-label="Next saved output"
          title="Next saved output"
          disabled={disabled || timeIndex >= times.length - 1}
          onClick={() => onTimeIndex(Math.min(times.length - 1, timeIndex + 1))}
        >
          <span aria-hidden="true">&rsaquo;</span>
        </button>
      </div>
      <button
        type="button"
        className="storm-play-button"
        aria-label={playing ? "Pause" : "Play"}
        title={playing ? "Pause" : "Play"}
        disabled={disabled}
        onClick={() => onPlaying(!playing)}
      >
        <span aria-hidden="true">{playing ? "Pause" : "Play"}</span>
      </button>
      <label htmlFor="storm-time-scrubber">
        <span>Saved output</span>
        <input
          id="storm-time-scrubber"
          type="range"
          min={matureIndices[0] ?? 3}
          max={matureIndices.at(-1) ?? 8}
          value={timeIndex}
          disabled={disabled}
          onChange={(event) => onTimeIndex(Number(event.currentTarget.value))}
        />
        <span className="storm-timeline-readout">
          <strong>{formatTime(times[timeIndex] ?? timeIndex * 900)}</strong>
          <small>{checkpoint ?? "Mature storm checkpoint"}</small>
        </span>
      </label>
      <label className="storm-speed-control">
        <span className="sr-only">Playback speed</span>
        <select
          aria-label="Playback speed"
          value={playbackSpeed}
          onChange={(event) => onPlaybackSpeed(Number(event.currentTarget.value))}
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={2}>2x</option>
        </select>
      </label>
    </fieldset>
  );
}

export function StormPlanPlot({
  frame,
  overlays,
  onSelect,
  showSelection = true,
}: {
  frame: StormExaminationFrame;
  overlays: OverlayState;
  onSelect: (value: Selection) => void;
  showSelection?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const geometryRef = useRef<PlotGeometry | null>(null);
  const plotStyle = dataAspectStyle(
    frame.viewport_bounds_km.x_min,
    frame.viewport_bounds_km.x_max,
    frame.viewport_bounds_km.y_min,
    frame.viewport_bounds_km.y_max,
  );
  useCanvasRender(canvasRef, () => {
    const canvas = canvasRef.current;
    if (canvas) geometryRef.current = drawPlan(canvas, frame, overlays, showSelection);
  }, [frame, overlays, showSelection]);

  function select(event: ReactMouseEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const geometry =
      geometryRef.current ??
      (canvas ? plotGeometry(canvas, 43, 12, 12, 34, frame.viewport_bounds_km) : null);
    const model = pointerToModel(event, canvas, geometry);
    if (!model) return;
    const localXIndex = nearestIndex(frame.plan.x_km, model.x);
    const localYIndex = nearestIndex(frame.plan.y_km, model.y);
    onSelect({
      xIndex: frame.plan.x_indices[localXIndex],
      yIndex: frame.plan.y_indices[localYIndex],
      zIndex:
        frame.plan.selection_z_indices?.[localYIndex]?.[localXIndex] ?? frame.plan.level_index,
    });
  }

  return (
    <figure className="storm-plot storm-plan-plot" style={plotStyle}>
      <figcaption>
        <div>
          <strong>{frame.plan.title}</strong>
          <span>{frame.plan.subtitle}</span>
        </div>
        <span>
          {frame.lens_id === "cloud_precipitation"
            ? "column maximum"
            : `z = ${frame.plan.level_km.toFixed(2)} km`}
        </span>
      </figcaption>
      <canvas ref={canvasRef} onClick={select} aria-label={`${frame.plan.title} plan view`} />
      <div className="storm-axis-label storm-plan-x-axis">x (km)</div>
      <div className="storm-axis-label storm-plan-y-axis">y (km)</div>
    </figure>
  );
}

export function StormSectionPlot({
  section,
  frame,
  overlays,
  onSelect,
  showSelection = true,
}: {
  section: VerticalSection;
  frame: StormExaminationFrame;
  overlays: OverlayState;
  onSelect: (value: Selection) => void;
  showSelection?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const geometryRef = useRef<PlotGeometry | null>(null);
  const horizontalMinimum = section.horizontal_km[0];
  const horizontalMaximum = section.horizontal_km.at(-1) ?? horizontalMinimum;
  const verticalMinimum = section.z_km[0] - 0.25;
  const verticalMaximum = (section.z_km.at(-1) ?? 20) + 0.25;
  const plotStyle = dataAspectStyle(
    horizontalMinimum,
    horizontalMaximum,
    verticalMinimum,
    verticalMaximum,
  );
  useCanvasRender(canvasRef, () => {
    const canvas = canvasRef.current;
    if (canvas) {
      geometryRef.current = drawSection(canvas, section, frame, overlays, showSelection);
    }
  }, [frame, overlays, section, showSelection]);

  function select(event: ReactMouseEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const geometry =
      geometryRef.current ??
      (canvas
        ? plotGeometry(canvas, 43, 10, 12, 30, {
            x_min: section.horizontal_km[0],
            x_max: section.horizontal_km.at(-1) ?? section.horizontal_km[0],
            y_min: section.z_km[0] - 0.25,
            y_max: (section.z_km.at(-1) ?? 20) + 0.25,
          })
        : null);
    const model = pointerToModel(event, canvas, geometry);
    if (!model) return;
    const horizontalIndex =
      section.horizontal_indices[nearestIndex(section.horizontal_km, model.x)];
    const zIndex = nearestIndex(section.z_km, model.y);
    const selected = frame.selected_point;
    onSelect({
      xIndex: section.orientation === "xz" ? horizontalIndex : selected.x_index,
      yIndex: section.orientation === "yz" ? horizontalIndex : selected.y_index,
      zIndex,
    });
  }

  return (
    <figure className="storm-plot storm-section-plot" style={plotStyle}>
      <figcaption>
        <strong>{section.title}</strong>
        <span>{section.primary.display_name}</span>
      </figcaption>
      <canvas ref={canvasRef} onClick={select} aria-label={section.title} />
      <div className="storm-axis-label storm-section-x-axis">
        {section.horizontal_dimension} (km)
      </div>
      <div className="storm-axis-label storm-section-z-axis">z (km)</div>
    </figure>
  );
}

export function StormLegend({
  frame,
  overlays,
  evidenceView = "plan",
}: {
  frame: StormExaminationFrame;
  overlays?: OverlayState;
  evidenceView?: "plan" | "xz" | "yz";
}) {
  const evidence =
    evidenceView === "plan"
      ? frame.plan
      : evidenceView === "xz"
        ? frame.xz_section
        : frame.yz_section;
  if (evidence.categories) {
    return (
      <aside className="storm-legend storm-category-legend" aria-label="Hydrometeor legend">
        <div className="storm-legend-heading">
          <strong>Dominant hydrometeor</strong>
          <small>
            {evidenceView === "plan"
              ? "column-derived at each cell's condensate maximum"
              : "at each native section cell"}
          </small>
        </div>
        <ol className="storm-legend-scale">
          {evidence.categories.categories
            .filter((category) => category.code > 0)
            .map((category) => (
              <li key={category.code}>
                <span style={{ backgroundColor: category.color }} />
                <b>{HYDROMETEOR_SHORT[category.key] ?? category.label}</b>
              </li>
            ))}
        </ol>
        <div className="storm-legend-range">
          <span>
            Mass {formatValue(evidence.primary.selected_frame_minimum)} to{" "}
            {formatValue(evidence.primary.selected_frame_maximum)} g/kg
          </span>
        </div>
        <small className="storm-legend-note">
          Derived category; native species retained in Context.
        </small>
        <OverlayKey
          lens={frame.lens_id}
          overlays={overlays}
          evidenceView={evidenceView}
          planLevelKm={frame.plan.level_km}
        />
      </aside>
    );
  }
  const scale = evidence.primary.scale;
  return (
    <aside className="storm-legend" aria-label={`${scale.display_name} legend`}>
      <div className="storm-legend-heading">
        <strong>w (m/s)</strong>
        <small>Fixed across all retained times</small>
      </div>
      <ol className="storm-legend-scale">
        {scale.colors
          .map((color, index) => ({ color, label: compactScaleIntervalLabel(scale, index) }))
          .reverse()
          .map((item) => (
            <li key={`${item.color}-${item.label}`}>
              <span style={{ backgroundColor: item.color }} />
              <b>{item.label}</b>
            </li>
          ))}
      </ol>
      <div className="storm-legend-range">
        <span>Frame max {formatSigned(evidence.primary.selected_frame_maximum)}</span>
        <span>Frame min {formatSigned(evidence.primary.selected_frame_minimum)}</span>
      </div>
      <OverlayKey
        lens={frame.lens_id}
        overlays={overlays}
        evidenceView={evidenceView}
        planLevelKm={frame.plan.level_km}
      />
    </aside>
  );
}

function OverlayKey({
  lens,
  overlays,
  evidenceView,
  planLevelKm,
}: {
  lens: LensId;
  overlays?: OverlayState;
  evidenceView: "plan" | "xz" | "yz";
  planLevelKm: number;
}) {
  const items: Array<[string, string]> = [];
  if (lens === "rotating_updraft") {
    if (overlays?.condensate) items.push(["teal", "Cloud boundary >= 0.05 g/kg"]);
    if (overlays?.rotation) items.push(["purple", "Cyclonic vorticity >= 0.01 s^-1"]);
    if (evidenceView === "plan" && overlays?.updraftHelicity) {
      items.push(["black", "UH >= 300 m^2/s^2"]);
    }
    if (overlays?.reflectivity) items.push(["brown", "Reflectivity >= 35 dBZ"]);
  } else if (lens === "cloud_precipitation") {
    if (overlays?.verticalMotion) items.push(["signed", "w >= +5 red / w <= -5 blue"]);
    if (overlays?.reflectivity) items.push(["black", "Reflectivity >= 35 dBZ"]);
  } else {
    if (evidenceView === "plan" && overlays?.rain) {
      items.push(["navy", "Accumulated rain (history) >= 2 mm"]);
    }
    if (overlays?.precipitatingCondensate) {
      items.push(["brown", "Current precipitating condensate >= 0.1 g/kg"]);
    }
    if (overlays?.reflectivity) items.push(["brown", "Reflectivity >= 35 dBZ"]);
    if (evidenceView === "plan" && overlays?.wind) {
      items.push(["arrow", `Model-relative flow at z = ${planLevelKm.toFixed(2)} km`]);
    }
  }
  if (!items.length) return null;
  return (
    <div className="storm-overlay-key">
      {items.map(([kind, label]) => (
        <div key={label}>
          <span className={`storm-key-symbol storm-key-${kind}`} aria-hidden="true" />
          <small>{label}</small>
        </div>
      ))}
    </div>
  );
}

function StormContext({
  frame,
  lens,
  viewport,
}: {
  frame: StormExaminationFrame | null;
  lens: LensId;
  viewport: ViewportId;
}) {
  if (!frame) return <p>Loading retained storm evidence...</p>;
  const point = frame.selected_point;
  const focusKeys =
    lens === "rotating_updraft"
      ? ["vertical_velocity", "vertical_vorticity", "updraft_helicity", "reflectivity"]
      : lens === "cloud_precipitation"
        ? [
            "total_condensate",
            "cloud_liquid",
            "rain_water",
            "cloud_ice",
            "snow",
            "hail_treated_large_ice",
            "reflectivity",
          ]
        : [
            "vertical_velocity",
            "accumulated_surface_rain",
            "reflectivity",
            "rain_water",
            "model_relative_u",
            "model_relative_v",
          ];
  return (
    <div className="storm-context">
      <p className="eyebrow">{frame.lens_name} Lens</p>
      <h3>{frame.lens_question}</h3>
      <div className="storm-state-row">
        {point.states.map((state) => (
          <span className="state-chip" key={state}>
            {state}
          </span>
        ))}
      </div>
      <dl className="metric-grid storm-coordinate-grid">
        <div>
          <dt>x</dt>
          <dd>{point.x_km.toFixed(1)} km</dd>
        </div>
        <div>
          <dt>y</dt>
          <dd>{point.y_km.toFixed(1)} km</dd>
        </div>
        <div>
          <dt>z</dt>
          <dd>{point.z_km.toFixed(2)} km</dd>
        </div>
        <div>
          <dt>Model time</dt>
          <dd>{formatTime(point.model_time_seconds)}</dd>
        </div>
      </dl>
      <h4>Evidence at selected native cell</h4>
      <dl className="storm-evidence-list">
        {focusKeys.map((key) => (
          <div key={key}>
            <dt>{evidenceLabel(key)}</dt>
            <dd>
              <strong>
                {formatValue(point.values[key])} {point.units[key]}
              </strong>
              <small>{point.evidence_kind[key]}</small>
            </dd>
          </div>
        ))}
      </dl>
      <p className="context-selection-prompt">
        Click any view to coordinate the plan and both sections. Current viewport:{" "}
        {viewport === "storm" ? "storm region" : "full domain"}.
      </p>
      <p className="storm-context-caveat">
        {frame.caveats[lens === "low_level_interactions" ? 4 : 0]}
      </p>
    </div>
  );
}

function StormDetails({ frame }: { frame: StormExaminationFrame | null }) {
  return (
    <section className="storm-details">
      <h3>Evidence and constraints</h3>
      {frame ? (
        <>
          <dl className="metric-grid">
            <div>
              <dt>Source</dt>
              <dd>{frame.provenance.source_history_file}</dd>
            </div>
            <div>
              <dt>Extraction</dt>
              <dd>{frame.extraction_milliseconds.toFixed(0)} ms</dd>
            </div>
            <div>
              <dt>Coordinate frame</dt>
              <dd>Translating model frame</dd>
            </div>
            <div>
              <dt>Interpolation</dt>
              <dd>None</dd>
            </div>
          </dl>
          <ul>
            {frame.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </>
      ) : (
        <p>Loading provenance...</p>
      )}
    </section>
  );
}

function useCanvasRender(
  ref: React.RefObject<HTMLCanvasElement | null>,
  render: () => void,
  dependencies: ReadonlyArray<unknown>,
) {
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    render();
    const observer = new ResizeObserver(render);
    observer.observe(canvas);
    return () => observer.disconnect();
    // The caller supplies the complete render dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
}

function drawPlan(
  canvas: HTMLCanvasElement,
  frame: StormExaminationFrame,
  overlays: OverlayState,
  showSelection = true,
): PlotGeometry {
  const context = prepareCanvas(canvas);
  const geometry = plotGeometry(canvas, 43, 12, 12, 34, frame.viewport_bounds_km);
  drawGrid(context, geometry);
  if (frame.lens_id === "cloud_precipitation" && frame.plan.categories) {
    drawCategories(context, geometry, frame.plan.categories);
  } else {
    drawRaster(context, geometry, frame.plan.primary);
  }
  if (frame.lens_id === "rotating_updraft") {
    const totalCondensate = frame.plan.overlays.total_condensate;
    if (overlays.condensate && totalCondensate) {
      drawThresholdOutline(context, geometry, totalCondensate, 0.05, "#2f7280", 1.15);
    }
    if (overlays.rotation) {
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.vertical_vorticity,
        0.01,
        "#632b73",
        1.6,
      );
    }
    if (overlays.updraftHelicity) {
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.updraft_helicity,
        300,
        "#161b22",
        1.5,
      );
    }
    if (overlays.reflectivity) {
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.composite_reflectivity,
        35,
        "#7b572a",
        1.1,
      );
    }
  } else if (frame.lens_id === "cloud_precipitation") {
    if (overlays.verticalMotion) {
      drawSignedOutlines(context, geometry, frame.plan.overlays.vertical_velocity, 5);
    }
    if (overlays.reflectivity) {
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.composite_reflectivity,
        35,
        "#111820",
        1.25,
      );
    }
  } else {
    const currentPrecipitation = frame.plan.overlays.low_level_precipitating_condensate;
    if (overlays.precipitatingCondensate && currentPrecipitation) {
      drawTransparentRaster(context, geometry, currentPrecipitation, "#7b572a", 0.2);
      drawThresholdOutline(context, geometry, currentPrecipitation, 0.1, "#7b572a", 1.5);
    }
    if (overlays.rain) {
      drawTransparentRaster(
        context,
        geometry,
        frame.plan.overlays.accumulated_surface_rain,
        "#214f9a",
        0.38,
      );
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.accumulated_surface_rain,
        2,
        "#214f9a",
        1.7,
      );
    }
    if (overlays.reflectivity) {
      drawThresholdOutline(
        context,
        geometry,
        frame.plan.overlays.composite_reflectivity,
        35,
        "#111820",
        1.3,
      );
    }
    if (overlays.wind) drawWindVectors(context, geometry, frame.plan.wind_vectors);
  }
  if (showSelection) {
    drawPlanCrosshairs(context, geometry, frame.selected_point);
    drawSelectedMarker(context, geometry, frame.selected_point.x_km, frame.selected_point.y_km);
  }
  return geometry;
}

function drawSection(
  canvas: HTMLCanvasElement,
  section: VerticalSection,
  frame: StormExaminationFrame,
  overlays: OverlayState,
  showSelection = true,
): PlotGeometry {
  const context = prepareCanvas(canvas);
  const xMinimum = section.horizontal_km[0];
  const xMaximum = section.horizontal_km.at(-1) ?? xMinimum;
  const geometry = plotGeometry(canvas, 43, 10, 12, 30, {
    x_min: xMinimum,
    x_max: xMaximum,
    y_min: section.z_km[0] - 0.25,
    y_max: (section.z_km.at(-1) ?? 20) + 0.25,
  });
  drawGrid(context, geometry);
  if (frame.lens_id === "cloud_precipitation" && section.categories) {
    drawCategories(context, geometry, section.categories);
    if (overlays.verticalMotion) {
      drawSignedOutlines(context, geometry, section.overlays.vertical_velocity, 5);
    }
  } else {
    drawRaster(context, geometry, section.primary);
    const verticalVorticity = section.overlays.vertical_vorticity;
    if (overlays.rotation && frame.lens_id === "rotating_updraft" && verticalVorticity) {
      drawThresholdOutline(context, geometry, verticalVorticity, 0.01, "#632b73", 1.8);
    }
    if (overlays.condensate && frame.lens_id === "rotating_updraft") {
      drawThresholdOutline(
        context,
        geometry,
        section.overlays.total_condensate,
        0.05,
        "#2f7280",
        1.3,
      );
    }
    if (overlays.precipitatingCondensate && frame.lens_id === "low_level_interactions") {
      drawThresholdOutline(
        context,
        geometry,
        section.overlays.precipitating_condensate,
        0.1,
        "#7b572a",
        1.4,
      );
    }
    if (overlays.reflectivity) {
      drawThresholdOutline(context, geometry, section.overlays.reflectivity, 35, "#7b572a", 1.05);
    }
  }
  if (showSelection) {
    const horizontal =
      section.orientation === "xz" ? frame.selected_point.x_km : frame.selected_point.y_km;
    drawSelectedMarker(context, geometry, horizontal, frame.selected_point.z_km);
  }
  return geometry;
}

function prepareCanvas(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const rect = canvas.getBoundingClientRect();
  const ratio = Math.max(1, window.devicePixelRatio || 1);
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  if (canvas.width !== width * ratio || canvas.height !== height * ratio) {
    canvas.width = width * ratio;
    canvas.height = height * ratio;
  }
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas is unavailable.");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  return context;
}

function plotGeometry(
  canvas: HTMLCanvasElement,
  left: number,
  top: number,
  right: number,
  bottom: number,
  bounds: Record<"x_min" | "x_max" | "y_min" | "y_max", number>,
): PlotGeometry {
  const rect = canvas.getBoundingClientRect();
  const availableWidth = Math.max(20, rect.width - left - right);
  const availableHeight = Math.max(20, rect.height - top - bottom);
  const modelWidth = Math.max(Number.EPSILON, bounds.x_max - bounds.x_min);
  const modelHeight = Math.max(Number.EPSILON, bounds.y_max - bounds.y_min);
  const modelAspect = modelWidth / modelHeight;
  let width = availableWidth;
  let height = width / modelAspect;
  let fittedLeft = left;
  let fittedTop = top;
  if (height > availableHeight) {
    height = availableHeight;
    width = height * modelAspect;
    fittedLeft += (availableWidth - width) / 2;
  } else {
    fittedTop += (availableHeight - height) / 2;
  }
  return {
    left: fittedLeft,
    top: fittedTop,
    width,
    height,
    xMinimum: bounds.x_min,
    xMaximum: bounds.x_max,
    yMinimum: bounds.y_min,
    yMaximum: bounds.y_max,
  };
}

function dataAspectStyle(
  horizontalMinimum: number,
  horizontalMaximum: number,
  verticalMinimum: number,
  verticalMaximum: number,
): CSSProperties {
  const horizontalSpan = Math.max(Number.EPSILON, horizontalMaximum - horizontalMinimum);
  const verticalSpan = Math.max(Number.EPSILON, verticalMaximum - verticalMinimum);
  return { "--storm-data-aspect": horizontalSpan / verticalSpan } as CSSProperties;
}

function drawGrid(context: CanvasRenderingContext2D, geometry: PlotGeometry) {
  context.save();
  context.strokeStyle = "#dbe6ec";
  context.fillStyle = "#5b6f7e";
  context.font = "600 10px system-ui";
  context.lineWidth = 1;
  for (let index = 0; index <= 4; index += 1) {
    const x = geometry.left + (geometry.width * index) / 4;
    const y = geometry.top + (geometry.height * index) / 4;
    context.beginPath();
    context.moveTo(x, geometry.top);
    context.lineTo(x, geometry.top + geometry.height);
    context.moveTo(geometry.left, y);
    context.lineTo(geometry.left + geometry.width, y);
    context.stroke();
  }
  context.strokeStyle = "#4b5f6c";
  context.strokeRect(geometry.left, geometry.top, geometry.width, geometry.height);
  context.fillText(
    formatAxis(geometry.xMinimum),
    geometry.left,
    geometry.top + geometry.height + 17,
  );
  const xMax = formatAxis(geometry.xMaximum);
  context.fillText(
    xMax,
    geometry.left + geometry.width - context.measureText(xMax).width,
    geometry.top + geometry.height + 17,
  );
  context.fillText(formatAxis(geometry.yMaximum), 5, geometry.top + 7);
  context.fillText(formatAxis(geometry.yMinimum), 5, geometry.top + geometry.height);
  context.restore();
}

function drawRaster(context: CanvasRenderingContext2D, geometry: PlotGeometry, layer: FieldLayer) {
  drawMatrix(context, geometry, layer.values, (value) => scaleColor(value, layer.scale));
}

function drawTransparentRaster(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  layer: FieldLayer,
  color: string,
  maximumOpacity: number,
) {
  context.save();
  drawMatrix(context, geometry, layer.values, (value) => {
    const normalized = clamp(
      (value - layer.scale.minimum) / (layer.scale.maximum - layer.scale.minimum),
      0,
      1,
    );
    return withAlpha(color, normalized * maximumOpacity);
  });
  context.restore();
}

function drawCategories(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  layer: CategoryLayer,
) {
  const colors = new Map(layer.categories.map((item) => [item.code, item.color]));
  const maximum = Math.max(layer.magnitude.scale.maximum, 0.001);
  drawMatrix(context, geometry, layer.values, (value, row, column) => {
    if (!value) return "rgba(255,255,255,0)";
    const mass = layer.magnitude.values[row]?.[column] ?? 0;
    const opacity = 0.18 + 0.78 * Math.sqrt(clamp(Number(mass) / maximum, 0, 1));
    return withAlpha(colors.get(value) ?? "#ffffff", opacity);
  });
}

function drawMatrix(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  values: Array<Array<number | null>>,
  color: (value: number, row: number, column: number) => string,
) {
  const rowCount = values.length;
  const columnCount = values[0]?.length ?? 0;
  if (!rowCount || !columnCount) return;
  const cellWidth = geometry.width / columnCount;
  const cellHeight = geometry.height / rowCount;
  values.forEach((row, rowIndex) => {
    row.forEach((rawValue, columnIndex) => {
      if (rawValue === null || !Number.isFinite(rawValue)) return;
      context.fillStyle = color(rawValue, rowIndex, columnIndex);
      context.fillRect(
        geometry.left + columnIndex * cellWidth,
        geometry.top + (rowCount - rowIndex - 1) * cellHeight,
        cellWidth + 0.5,
        cellHeight + 0.5,
      );
    });
  });
}

function drawThresholdOutline(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  layer: FieldLayer,
  threshold: number,
  color: string,
  lineWidth: number,
) {
  const values = layer.values;
  const rows = values.length;
  const columns = values[0]?.length ?? 0;
  if (!rows || !columns) return;
  const cellWidth = geometry.width / columns;
  const cellHeight = geometry.height / rows;
  context.save();
  context.strokeStyle = color;
  context.lineWidth = lineWidth;
  context.beginPath();
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const value = values[row]?.[column];
      if (value === null || value < threshold) continue;
      const left = geometry.left + column * cellWidth;
      const top = geometry.top + (rows - row - 1) * cellHeight;
      if (row === 0 || Number(values[row - 1]?.[column]) < threshold) {
        context.moveTo(left, top + cellHeight);
        context.lineTo(left + cellWidth, top + cellHeight);
      }
      if (row === rows - 1 || Number(values[row + 1]?.[column]) < threshold) {
        context.moveTo(left, top);
        context.lineTo(left + cellWidth, top);
      }
      if (column === 0 || Number(values[row]?.[column - 1]) < threshold) {
        context.moveTo(left, top);
        context.lineTo(left, top + cellHeight);
      }
      if (column === columns - 1 || Number(values[row]?.[column + 1]) < threshold) {
        context.moveTo(left + cellWidth, top);
        context.lineTo(left + cellWidth, top + cellHeight);
      }
    }
  }
  context.stroke();
  context.restore();
}

function drawSignedOutlines(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  layer: FieldLayer,
  threshold: number,
) {
  const negative: FieldLayer = {
    ...layer,
    values: layer.values.map((row) => row.map((value) => (value === null ? null : -value))),
  };
  drawThresholdOutline(context, geometry, layer, threshold, "rgba(255,255,255,0.94)", 4.2);
  drawThresholdOutline(context, geometry, negative, threshold, "rgba(255,255,255,0.94)", 4.2);
  drawThresholdOutline(context, geometry, layer, threshold, "#c72b22", 2.2);
  drawThresholdOutline(context, geometry, negative, threshold, "#1559b0", 2.2);
}

function drawWindVectors(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  vectors: WindVector[],
) {
  context.save();
  context.strokeStyle = "rgba(25, 42, 52, 0.78)";
  context.fillStyle = "rgba(25, 42, 52, 0.78)";
  context.lineWidth = 1;
  vectors.forEach((vector) => {
    if (!inside(geometry, vector.x_km, vector.y_km)) return;
    const start = modelToPixel(geometry, vector.x_km, vector.y_km);
    const scale = 12 / 50;
    const dx = vector.u_m_s * scale;
    const dy = -vector.v_m_s * scale;
    const endX = start.x + dx;
    const endY = start.y + dy;
    context.beginPath();
    context.moveTo(start.x, start.y);
    context.lineTo(endX, endY);
    context.stroke();
    const angle = Math.atan2(dy, dx);
    context.beginPath();
    context.moveTo(endX, endY);
    context.lineTo(endX - 4 * Math.cos(angle - 0.55), endY - 4 * Math.sin(angle - 0.55));
    context.lineTo(endX - 4 * Math.cos(angle + 0.55), endY - 4 * Math.sin(angle + 0.55));
    context.closePath();
    context.fill();
  });
  context.restore();
}

function drawPlanCrosshairs(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  point: SelectedPoint,
) {
  const pixel = modelToPixel(geometry, point.x_km, point.y_km);
  context.save();
  context.strokeStyle = "rgba(21, 47, 62, 0.55)";
  context.setLineDash([4, 4]);
  context.beginPath();
  context.moveTo(pixel.x, geometry.top);
  context.lineTo(pixel.x, geometry.top + geometry.height);
  context.moveTo(geometry.left, pixel.y);
  context.lineTo(geometry.left + geometry.width, pixel.y);
  context.stroke();
  context.restore();
}

function drawSelectedMarker(
  context: CanvasRenderingContext2D,
  geometry: PlotGeometry,
  x: number,
  y: number,
) {
  if (!inside(geometry, x, y)) return;
  const pixel = modelToPixel(geometry, x, y);
  context.save();
  context.fillStyle = "#ffffff";
  context.strokeStyle = "#101c24";
  context.lineWidth = 1.5;
  context.beginPath();
  context.arc(pixel.x, pixel.y, 4.5, 0, Math.PI * 2);
  context.fill();
  context.stroke();
  context.restore();
}

function pointerToModel(
  event: ReactMouseEvent<HTMLCanvasElement>,
  canvas: HTMLCanvasElement | null,
  geometry: PlotGeometry | null,
): { x: number; y: number } | null {
  if (!canvas || !geometry) return null;
  const rect = canvas.getBoundingClientRect();
  const nativeOffsetX = event.nativeEvent.offsetX;
  const nativeOffsetY = event.nativeEvent.offsetY;
  const pixelX = nativeOffsetX || event.clientX - rect.left;
  const pixelY = nativeOffsetY || event.clientY - rect.top;
  if (
    pixelX < geometry.left ||
    pixelX > geometry.left + geometry.width ||
    pixelY < geometry.top ||
    pixelY > geometry.top + geometry.height
  )
    return null;
  return {
    x:
      geometry.xMinimum +
      ((pixelX - geometry.left) / geometry.width) * (geometry.xMaximum - geometry.xMinimum),
    y:
      geometry.yMaximum -
      ((pixelY - geometry.top) / geometry.height) * (geometry.yMaximum - geometry.yMinimum),
  };
}

function modelToPixel(geometry: PlotGeometry, x: number, y: number) {
  return {
    x:
      geometry.left +
      ((x - geometry.xMinimum) / (geometry.xMaximum - geometry.xMinimum)) * geometry.width,
    y:
      geometry.top +
      ((geometry.yMaximum - y) / (geometry.yMaximum - geometry.yMinimum)) * geometry.height,
  };
}

function inside(geometry: PlotGeometry, x: number, y: number) {
  return (
    x >= geometry.xMinimum &&
    x <= geometry.xMaximum &&
    y >= geometry.yMinimum &&
    y <= geometry.yMaximum
  );
}

function scaleColor(value: number, scale: ScaleMetadata): string {
  if (!scale.colors.length) return "#ffffff";
  if (scale.scale_type === "fixed_discrete" && scale.breakpoints.length) {
    const index = scale.breakpoints.findIndex((breakpoint) => value < breakpoint);
    return scale.colors[index < 0 ? scale.colors.length - 1 : index] ?? scale.colors.at(-1)!;
  }
  const normalized = clamp((value - scale.minimum) / (scale.maximum - scale.minimum), 0, 1);
  return scale.colors[Math.round(normalized * (scale.colors.length - 1))] ?? scale.colors[0];
}

function compactScaleIntervalLabel(scale: ScaleMetadata, index: number): string {
  const lower = index === 0 ? null : scale.breakpoints[index - 1];
  const upper = scale.breakpoints[index] ?? null;
  if (lower === null) return `<${formatCompactLegendValue(upper ?? scale.minimum)}`;
  if (upper === null) return `>=${formatCompactLegendValue(lower)}`;
  return `${formatCompactLegendValue(lower)}–${formatCompactLegendValue(upper)}`;
}

function scaleIntervalLabel(scale: ScaleMetadata, index: number): string {
  const lower = index === 0 ? null : scale.breakpoints[index - 1];
  const upper = scale.breakpoints[index] ?? null;
  if (lower === null) return `< ${formatValue(upper ?? scale.minimum)}`;
  if (upper === null) return `>= ${formatValue(lower)}`;
  return `${formatValue(lower)} to < ${formatValue(upper)}`;
}

function formatCompactLegendValue(value: number): string {
  return Number.isInteger(value) ? value.toFixed(0) : formatValue(value);
}

function withAlpha(hex: string, alpha: number): string {
  const normalized = hex.replace("#", "");
  const value = Number.parseInt(normalized, 16);
  const red = (value >> 16) & 255;
  const green = (value >> 8) & 255;
  const blue = value & 255;
  return `rgba(${red}, ${green}, ${blue}, ${clamp(alpha, 0, 1)})`;
}

function nearestIndex(values: number[], target: number): number {
  let nearest = 0;
  let distance = Number.POSITIVE_INFINITY;
  values.forEach((value, index) => {
    const candidate = Math.abs(value - target);
    if (candidate < distance) {
      nearest = index;
      distance = candidate;
    }
  });
  return nearest;
}

function evidenceLabel(key: string): string {
  if (key === "model_relative_u") return "Model-relative u";
  if (key === "model_relative_v") return "Model-relative v";
  if (key === "hail_treated_large_ice") return "Hail-treated large ice";
  return key.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function formatTime(seconds: number): string {
  return `${Math.round(seconds / 60)} min`;
}

function formatValue(value: number | undefined): string {
  if (value === undefined || !Number.isFinite(value)) return "Unavailable";
  const magnitude = Math.abs(value);
  if (magnitude > 0 && magnitude < 0.01) return value.toExponential(2);
  if (magnitude >= 100) return value.toFixed(0);
  return value.toFixed(2);
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${formatValue(value)}`;
}

function formatAxis(value: number): string {
  return Math.abs(value) >= 10 ? value.toFixed(0) : value.toFixed(1);
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

export const stormExaminationRendering = {
  nearestIndex,
  scaleColor,
  scaleIntervalLabel,
};

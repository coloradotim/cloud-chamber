import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ExploreInspector, IntegratedExploreWorkspace } from "./IntegratedExploreWorkspace";
import type { SupercellSimulation } from "./SupercellsWorld";
import {
  type LensId,
  type OverlayState,
  type Selection,
  type StormExaminationFrame,
  StormLegend,
  StormPlanPlot,
  StormSectionPlot,
  type ViewportId,
} from "./StormExaminationResearch";
import { type StormScenePayload, type StormScenePoint, True3DViewer } from "./True3DViewer";

import "./StormExaminationResearch.css";
import "./SupercellsExplore.css";

type EvidenceView = "plan" | "xz" | "yz";
type FocusedViewer = "scene" | "evidence" | null;

const LENSES: Array<{ id: LensId; label: string }> = [
  { id: "rotating_updraft", label: "Rotating Updraft" },
  { id: "cloud_precipitation", label: "Cloud and Precipitation" },
  { id: "low_level_interactions", label: "Low-Level Interactions" },
];

const HYDROMETEOR_CODES = [
  { code: 1, label: "Cloud liquid" },
  { code: 2, label: "Rain" },
  { code: 3, label: "Cloud ice" },
  { code: 4, label: "Snow" },
  { code: 5, label: "Hail-treated large ice" },
];

export function SupercellsExplore({
  simulation,
  onBack,
}: {
  simulation: SupercellSimulation;
  onBack: () => void;
}) {
  const [lens, setLens] = useState<LensId>("rotating_updraft");
  const [viewport, setViewport] = useState<ViewportId>("storm");
  const [timeIndex, setTimeIndex] = useState(5);
  const [frame, setFrame] = useState<StormExaminationFrame | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [evidenceView, setEvidenceView] = useState<EvidenceView>("plan");
  const [focusedViewer, setFocusedViewer] = useState<FocusedViewer>(null);
  const [contextCollapsed, setContextCollapsed] = useState(false);
  const [overlays, setOverlays] = useState<OverlayState>(() => overlayDefaults("rotating_updraft"));
  const [visibleLayerKeys, setVisibleLayerKeys] = useState<string[]>([]);
  const [categoryCodes, setCategoryCodes] = useState<number[]>(
    HYDROMETEOR_CODES.map((item) => item.code),
  );
  const [sceneOpacity, setSceneOpacity] = useState(1);
  const [scenePointSize, setScenePointSize] = useState(1);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const frameCache = useRef(new Map<string, StormExaminationFrame>());
  const defaultsLens = useRef<LensId | null>(null);
  const contextBeforeEvidenceFocus = useRef(false);

  const requestKey = frameRequestKey(lens, viewport, timeIndex, selection);
  const loadFrame = useCallback(
    async (signal: AbortSignal) => {
      const cached = frameCache.current.get(requestKey);
      if (cached) {
        setFrame(cached);
        setError(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const payload = await fetchSupercellFrame(
          simulation.simulation_id,
          lens,
          viewport,
          timeIndex,
          selection,
          signal,
        );
        frameCache.current.set(requestKey, payload);
        trimCache(frameCache.current, 8);
        setFrame(payload);
        void prefetchAdjacentFrames(
          frameCache.current,
          simulation.simulation_id,
          payload,
          lens,
          viewport,
        );
      } catch (caught) {
        if (!signal.aborted) {
          setError(caught instanceof Error ? caught.message : "Supercell frame unavailable.");
        }
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    },
    [lens, requestKey, selection, simulation.simulation_id, timeIndex, viewport],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadFrame(controller.signal);
    return () => controller.abort();
  }, [loadFrame, retryNonce]);

  useEffect(() => {
    if (!frame?.scene || frame.lens_id !== lens || defaultsLens.current === lens) return;
    defaultsLens.current = lens;
    setVisibleLayerKeys(
      frame.scene.layers.filter((layer) => layer.default_visible).map((layer) => layer.key),
    );
    setOverlays(overlayDefaults(lens));
    setCategoryCodes(HYDROMETEOR_CODES.map((item) => item.code));
  }, [frame, lens]);

  useEffect(() => {
    if (!playing || loading || !frame) return;
    const timer = window.setTimeout(() => {
      setTimeIndex((current) => (current >= frame.times_seconds.length - 1 ? 0 : current + 1));
    }, 1_350 / playbackSpeed);
    return () => window.clearTimeout(timer);
  }, [frame, loading, playbackSpeed, playing]);

  const scene = useMemo(
    () => filterHydrometeorCategories(frame?.scene ?? null, categoryCodes),
    [categoryCodes, frame?.scene],
  );
  const activeSlice = useMemo(
    () => (frame ? evidenceSlice(frame, evidenceView) : null),
    [evidenceView, frame],
  );
  const activeSliceLabel = frame ? evidenceLabel(frame, evidenceView) : "Evidence unavailable";
  const checkpoint = frame?.timeline_checkpoints.find(
    (item) => item.time_seconds === frame.time_seconds,
  );
  const windVectors = frame?.scene?.wind_vectors ?? [];

  function chooseLens(next: LensId) {
    setPlaying(false);
    setLens(next);
    defaultsLens.current = null;
  }

  function selectPoint(next: Selection) {
    setPlaying(false);
    setSelection(next);
  }

  function selectScenePoint(point: StormScenePoint) {
    if (!frame) return;
    selectPoint({
      xIndex: nearestCoordinateIndex(point[0], frame.plan.x_km, frame.plan.x_indices),
      yIndex: nearestCoordinateIndex(point[1], frame.plan.y_km, frame.plan.y_indices),
      zIndex: nearestCoordinateIndex(point[2], frame.xz_section.z_km),
    });
  }

  function toggleLayer(key: string, visible: boolean) {
    setVisibleLayerKeys((current) =>
      visible ? [...new Set([...current, key])] : current.filter((item) => item !== key),
    );
  }

  function toggleEvidenceFocus() {
    if (focusedViewer === "evidence") {
      setFocusedViewer(null);
      setContextCollapsed(contextBeforeEvidenceFocus.current);
      return;
    }
    contextBeforeEvidenceFocus.current = contextCollapsed;
    setContextCollapsed(true);
    setFocusedViewer("evidence");
  }

  return (
    <IntegratedExploreWorkspace
      worldName="Supercells"
      simulationName={simulation.display_name}
      backLabel="Back to Supercells"
      onBack={onBack}
    >
      <section
        className={`supercells-explore-shell${
          focusedViewer ? ` supercells-explore-focused-${focusedViewer}` : ""
        }`}
        aria-label="Supercells integrated Explore workspace"
      >
        <div
          className={`supercells-workbench${
            contextCollapsed ? " supercells-context-collapsed" : ""
          }`}
        >
          <section className="supercells-scene" aria-label="3-D storm scene">
            <div className="supercells-lens-switcher" aria-label="Supercell Lens">
              {LENSES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={lens === item.id ? "active-control" : ""}
                  aria-pressed={lens === item.id}
                  onClick={() => chooseLens(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            {frame?.scene ? (
              <True3DViewer
                resultName={simulation.display_name}
                pointCloud={null}
                fieldLabel={frame.lens_name}
                valueChannelLabel="Native and explicitly derived Supercell layers."
                activeSlice={activeSlice}
                activeSliceLabel={activeSliceLabel}
                showSlicePlane={evidenceView !== "plan"}
                selectedRegion={
                  frame && selection
                    ? {
                        xIndex: frame.selected_point.x_index,
                        yIndex: frame.selected_point.y_index,
                        zIndex: frame.selected_point.z_index,
                      }
                    : null
                }
                coordinateSizes={frame.scene.coordinate_sizes}
                selectedTimeLabel={formatTime(frame.time_seconds)}
                sceneTimeLabel={formatTime(frame.time_seconds)}
                thresholdLabel="Lens-owned fixed thresholds"
                opacity={1}
                pointSize={1}
                status={loading ? "Loading frame" : "Scene synchronized"}
                provenanceLabel="Retained native CM1 history; deterministic bounded selection."
                noCloudMessage="No visible storm layers at this saved output."
                windVectors={windVectors}
                showWindVectors={lens === "low_level_interactions" && overlays.wind}
                windMode="total"
                windReferenceMps={frame.scene.wind_reference_m_s}
                windArrowDomainFraction={0.055}
                compactWorkspace
                maximized={focusedViewer === "scene"}
                onToggleMaximize={() =>
                  setFocusedViewer((current) => (current === "scene" ? null : "scene"))
                }
                stormScene={scene}
                visibleStormLayerKeys={visibleLayerKeys}
                stormOpacity={sceneOpacity}
                stormPointSize={scenePointSize}
                compactAxisLabels
                selectedPointCoordinates={
                  selection && frame
                    ? {
                        x: frame.selected_point.x_km,
                        y: frame.selected_point.y_km,
                        z: frame.selected_point.z_km,
                      }
                    : null
                }
                onSelectStormPoint={selectScenePoint}
                compactDisplayControls={
                  <StormDisplayControls
                    frame={frame}
                    visibleLayerKeys={visibleLayerKeys}
                    opacity={sceneOpacity}
                    pointSize={scenePointSize}
                    categoryCodes={categoryCodes}
                    onLayer={toggleLayer}
                    onOpacity={setSceneOpacity}
                    onPointSize={setScenePointSize}
                    onCategoryCodes={setCategoryCodes}
                  />
                }
              />
            ) : (
              <LocalFailure
                title="3-D storm scene unavailable"
                message={error ?? "The selected frame did not provide a bounded 3-D scene."}
                onRetry={() => setRetryNonce((current) => current + 1)}
              />
            )}
            {loading && frame && <div className="supercells-frame-loading">Loading frame...</div>}
          </section>

          <section className="supercells-evidence" aria-label="Coordinated storm evidence">
            <header className="instrument-header">
              <div>
                <h2>{evidenceTitle(evidenceView)}</h2>
                <p>{activeSliceLabel}</p>
              </div>
              <div className="instrument-actions">
                <div className="instrument-view-toggle" aria-label="Slice orientation">
                  {(["plan", "xz", "yz"] as EvidenceView[]).map((view) => (
                    <button
                      key={view}
                      type="button"
                      className={evidenceView === view ? "active-control" : ""}
                      aria-pressed={evidenceView === view}
                      onClick={() => setEvidenceView(view)}
                    >
                      {sliceControlLabel(view)}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="viewer-maximize-button"
                  aria-label={
                    focusedViewer === "evidence" ? "Restore evidence" : "Maximize evidence"
                  }
                  title={focusedViewer === "evidence" ? "Restore evidence" : "Maximize evidence"}
                  onClick={toggleEvidenceFocus}
                >
                  <span aria-hidden="true">⛶</span>
                </button>
                <button
                  type="button"
                  className="supercells-context-toggle"
                  aria-expanded={!contextCollapsed}
                  aria-controls={contextCollapsed ? undefined : "supercells-context-inspector"}
                  aria-label={contextCollapsed ? "Open Context" : "Collapse Context"}
                  title={contextCollapsed ? "Open Context" : "Collapse Context"}
                  onClick={() => setContextCollapsed((current) => !current)}
                >
                  <span className="supercells-context-toggle-icon" aria-hidden="true">
                    <span className="supercells-context-toggle-frame">
                      <span className="supercells-context-toggle-panel">
                        {contextCollapsed ? "\u2039" : "\u203a"}
                      </span>
                    </span>
                  </span>
                </button>
              </div>
            </header>
            {frame ? (
              <div className="supercells-evidence-body">
                <div className="supercells-active-plot">
                  {evidenceView === "plan" ? (
                    <StormPlanPlot frame={frame} overlays={overlays} onSelect={selectPoint} />
                  ) : (
                    <StormSectionPlot
                      section={evidenceView === "xz" ? frame.xz_section : frame.yz_section}
                      frame={frame}
                      overlays={overlays}
                      onSelect={selectPoint}
                    />
                  )}
                </div>
                <StormLegend frame={frame} overlays={overlays} />
              </div>
            ) : (
              <LocalFailure
                title="Storm evidence unavailable"
                message={error ?? "The selected plan or section could not be loaded."}
                onRetry={() => setRetryNonce((current) => current + 1)}
              />
            )}
          </section>

          <ExploreInspector
            id="supercells-context-inspector"
            collapsed={contextCollapsed}
            onCollapsedChange={setContextCollapsed}
            showCollapseControl={false}
            sections={{
              explain: <SupercellExplanation frame={frame} lens={lens} viewport={viewport} />,
              science: <SupercellScience frame={frame} selected={selection !== null} />,
              notes: <SupercellNotes />,
              details: <SupercellDetails frame={frame} simulation={simulation} />,
            }}
          />
        </div>

        <StormExploreControls
          lens={lens}
          viewport={viewport}
          evidenceView={evidenceView}
          overlays={overlays}
          visibleLayerKeys={visibleLayerKeys}
          onViewport={(next) => {
            setPlaying(false);
            setViewport(next);
          }}
          onEvidenceView={setEvidenceView}
          onOverlays={setOverlays}
          onLayer={toggleLayer}
        />

        <SupercellTimeline
          frame={frame}
          timeIndex={timeIndex}
          playing={playing}
          playbackSpeed={playbackSpeed}
          loading={loading}
          checkpoint={checkpoint?.phase ?? null}
          onTimeIndex={(next) => {
            setPlaying(false);
            setTimeIndex(next);
          }}
          onPlaying={setPlaying}
          onPlaybackSpeed={setPlaybackSpeed}
        />
      </section>
    </IntegratedExploreWorkspace>
  );
}

function StormDisplayControls({
  frame,
  visibleLayerKeys,
  opacity,
  pointSize,
  categoryCodes,
  onLayer,
  onOpacity,
  onPointSize,
  onCategoryCodes,
}: {
  frame: StormExaminationFrame;
  visibleLayerKeys: string[];
  opacity: number;
  pointSize: number;
  categoryCodes: number[];
  onLayer: (key: string, visible: boolean) => void;
  onOpacity: (value: number) => void;
  onPointSize: (value: number) => void;
  onCategoryCodes: (values: number[]) => void;
}) {
  return (
    <section className="supercells-display-controls" aria-label="3-D storm display controls">
      <div className="supercells-layer-list">
        {frame.scene?.layers.map((layer) => (
          <label key={layer.key}>
            <input
              type="checkbox"
              checked={visibleLayerKeys.includes(layer.key)}
              onChange={(event) => onLayer(layer.key, event.currentTarget.checked)}
            />
            {layer.display_name}
          </label>
        ))}
      </div>
      {frame.lens_id === "cloud_precipitation" && (
        <fieldset className="supercells-category-filters">
          <legend>Hydrometeors</legend>
          {HYDROMETEOR_CODES.map((category) => (
            <label key={category.code}>
              <input
                type="checkbox"
                checked={categoryCodes.includes(category.code)}
                onChange={(event) =>
                  onCategoryCodes(
                    event.currentTarget.checked
                      ? [...categoryCodes, category.code]
                      : categoryCodes.filter((code) => code !== category.code),
                  )
                }
              />
              {category.label}
            </label>
          ))}
        </fieldset>
      )}
      <div className="supercells-render-sliders">
        <label>
          Opacity
          <input
            type="range"
            min={0.25}
            max={1.25}
            step={0.05}
            value={opacity}
            onChange={(event) => onOpacity(Number(event.currentTarget.value))}
          />
          <span>{opacity.toFixed(2)}x</span>
        </label>
        <label>
          Point size
          <input
            type="range"
            min={0.5}
            max={1.8}
            step={0.1}
            value={pointSize}
            onChange={(event) => onPointSize(Number(event.currentTarget.value))}
          />
          <span>{pointSize.toFixed(1)}x</span>
        </label>
      </div>
    </section>
  );
}

function StormExploreControls({
  lens,
  viewport,
  evidenceView,
  overlays,
  visibleLayerKeys,
  onViewport,
  onEvidenceView,
  onOverlays,
  onLayer,
}: {
  lens: LensId;
  viewport: ViewportId;
  evidenceView: EvidenceView;
  overlays: OverlayState;
  visibleLayerKeys: string[];
  onViewport: (value: ViewportId) => void;
  onEvidenceView: (value: EvidenceView) => void;
  onOverlays: (value: OverlayState) => void;
  onLayer: (key: string, visible: boolean) => void;
}) {
  const controls = overlayControls(lens);
  function update(control: OverlayControl, checked: boolean) {
    onOverlays({ ...overlays, [control.overlayKey]: checked });
    if (control.layerKey) onLayer(control.layerKey, checked);
  }
  return (
    <section className="supercells-control-deck" aria-label="Supercell visualization controls">
      <fieldset>
        <legend>Viewport</legend>
        <div className="segmented-buttons">
          <button
            type="button"
            className={viewport === "storm" ? "active-control" : ""}
            aria-pressed={viewport === "storm"}
            onClick={() => onViewport("storm")}
          >
            Storm region
          </button>
          <button
            type="button"
            className={viewport === "full" ? "active-control" : ""}
            aria-pressed={viewport === "full"}
            onClick={() => onViewport("full")}
          >
            Full domain
          </button>
        </div>
      </fieldset>
      <fieldset>
        <legend>Slice</legend>
        <div className="segmented-buttons">
          {(["plan", "xz", "yz"] as EvidenceView[]).map((view) => (
            <button
              key={view}
              type="button"
              className={evidenceView === view ? "active-control" : ""}
              aria-pressed={evidenceView === view}
              onClick={() => onEvidenceView(view)}
            >
              {sliceControlLabel(view)}
            </button>
          ))}
        </div>
      </fieldset>
      <fieldset className="supercells-overlay-controls">
        <legend>Overlays</legend>
        {controls.map((control) => (
          <label key={control.label}>
            <input
              type="checkbox"
              checked={
                control.layerKey
                  ? visibleLayerKeys.includes(control.layerKey)
                  : overlays[control.overlayKey]
              }
              onChange={(event) => update(control, event.currentTarget.checked)}
            />
            {control.label}
          </label>
        ))}
      </fieldset>
    </section>
  );
}

type OverlayControl = {
  label: string;
  overlayKey: keyof OverlayState;
  layerKey?: string;
};

function overlayControls(lens: LensId): OverlayControl[] {
  if (lens === "rotating_updraft") {
    return [
      { label: "Cloud body", overlayKey: "condensate", layerKey: "storm_cloud_body" },
      { label: "Vertical motion", overlayKey: "verticalMotion", layerKey: "vertical_motion" },
      { label: "Rotation", overlayKey: "rotation", layerKey: "cyclonic_rotation" },
      { label: "2-5 km UH", overlayKey: "updraftHelicity", layerKey: "updraft_helicity" },
      { label: "Reflectivity", overlayKey: "reflectivity", layerKey: "reflectivity" },
    ];
  }
  if (lens === "cloud_precipitation") {
    return [
      { label: "Hydrometeors", overlayKey: "condensate", layerKey: "hydrometeor_categories" },
      { label: "Reflectivity", overlayKey: "reflectivity", layerKey: "reflectivity" },
      { label: "Vertical motion", overlayKey: "verticalMotion" },
    ];
  }
  return [
    { label: "Cloud body", overlayKey: "condensate", layerKey: "storm_cloud_body" },
    {
      label: "Low-level motion",
      overlayKey: "verticalMotion",
      layerKey: "low_level_vertical_motion",
    },
    { label: "Accumulated rain", overlayKey: "rain", layerKey: "accumulated_surface_rain" },
    { label: "Model-relative flow", overlayKey: "wind" },
    { label: "Reflectivity", overlayKey: "reflectivity", layerKey: "reflectivity" },
    {
      label: "Precipitating condensate",
      overlayKey: "precipitatingCondensate",
      layerKey: "precipitating_condensate",
    },
  ];
}

function SupercellTimeline({
  frame,
  timeIndex,
  playing,
  playbackSpeed,
  loading,
  checkpoint,
  onTimeIndex,
  onPlaying,
  onPlaybackSpeed,
}: {
  frame: StormExaminationFrame | null;
  timeIndex: number;
  playing: boolean;
  playbackSpeed: number;
  loading: boolean;
  checkpoint: string | null;
  onTimeIndex: (value: number) => void;
  onPlaying: (value: boolean) => void;
  onPlaybackSpeed: (value: number) => void;
}) {
  const times = frame?.times_seconds ?? [];
  const disabled = times.length === 0;
  return (
    <fieldset className="supercells-timeline" aria-label="Saved-output timeline">
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
      <button
        type="button"
        className="supercells-play-button"
        aria-label={playing ? "Pause" : "Play"}
        title={playing ? "Pause" : "Play"}
        disabled={disabled}
        onClick={() => onPlaying(!playing)}
      >
        <span
          className={`timelapse-icon timelapse-icon-${playing ? "pause" : "play"}`}
          aria-hidden="true"
        >
          {playing ? (
            <>
              <span />
              <span />
            </>
          ) : (
            <span />
          )}
        </span>
      </button>
      <label className="supercells-time-scrubber">
        <span>Saved output</span>
        <input
          aria-label="Saved output time"
          type="range"
          min={0}
          max={Math.max(0, times.length - 1)}
          value={timeIndex}
          disabled={disabled}
          onChange={(event) => onTimeIndex(Number(event.currentTarget.value))}
        />
        <span className="supercells-time-readout">
          <strong>{formatTime(times[timeIndex] ?? 0)}</strong>
          <small>
            frame {Math.min(timeIndex + 1, Math.max(1, times.length))} of{" "}
            {Math.max(1, times.length)}
            {checkpoint ? ` · ${checkpoint}` : ""}
          </small>
        </span>
      </label>
      <label className="supercells-speed-control">
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
      {loading && <span className="supercells-timeline-status">Loading saved output...</span>}
    </fieldset>
  );
}

function SupercellExplanation({
  frame,
  lens,
  viewport,
}: {
  frame: StormExaminationFrame | null;
  lens: LensId;
  viewport: ViewportId;
}) {
  const question =
    frame?.lens_question ?? LENSES.find((item) => item.id === lens)?.label ?? "Storm evidence";
  return (
    <section className="supercells-context-panel">
      <p className="eyebrow">{frame?.lens_name ?? "Supercell Lens"}</p>
      <h3>{question}</h3>
      <p>{lensExplanation(lens)}</p>
      <dl className="metric-grid">
        <Metric label="Simulation" value="Quarter-Circle Supercell" />
        <Metric label="Viewport" value={viewport === "storm" ? "Storm region" : "Full domain"} />
        <Metric label="Model time" value={formatTime(frame?.time_seconds ?? 0)} />
        <Metric
          label="Frame"
          value={frame ? `${frame.time_index + 1} of ${frame.times_seconds.length}` : "Loading"}
        />
      </dl>
      <p className="context-callout">
        Select a cell in the plan or section to inspect native-grid evidence.
      </p>
    </section>
  );
}

function SupercellScience({
  frame,
  selected,
}: {
  frame: StormExaminationFrame | null;
  selected: boolean;
}) {
  if (!frame) return <p>Scientific evidence is loading.</p>;
  const point = frame.selected_point;
  return (
    <section className="supercells-context-panel">
      <p className="eyebrow">{selected ? "Selected point" : "Strongest-updraft reference"}</p>
      <h3>
        x {point.x_km.toFixed(1)}, y {point.y_km.toFixed(1)}, z {point.z_km.toFixed(2)} km
      </h3>
      <div className="supercells-state-row">
        {point.states.map((state) => (
          <span key={state}>{state}</span>
        ))}
      </div>
      <dl className="metric-grid">
        {scienceKeys(frame.lens_id).map((key) => (
          <Metric
            key={key}
            label={scienceLabel(key)}
            value={`${formatScientific(point.values[key])} ${point.units[key] ?? ""}`.trim()}
          />
        ))}
        <Metric
          label="Distance to strongest updraft"
          value={`${point.distance_to_primary_updraft_km.toFixed(1)} km`}
        />
      </dl>
      <p className="context-coordinate-frame">{point.coordinate_frame}</p>
    </section>
  );
}

function SupercellNotes() {
  return (
    <section className="supercells-context-panel">
      <h3>Simulation notes</h3>
      <p>No note is recorded for this built-in Simulation.</p>
    </section>
  );
}

function SupercellDetails({
  frame,
  simulation,
}: {
  frame: StormExaminationFrame | null;
  simulation: SupercellSimulation;
}) {
  return (
    <section className="supercells-context-panel">
      <h3>Simulation details</h3>
      <dl className="metric-grid">
        <Metric label="World ID" value="supercells" />
        <Metric label="Simulation ID" value={simulation.simulation_id} />
        <Metric label="Run ID" value={simulation.run_id} />
        <Metric label="Case ID" value={simulation.case_id} />
        <Metric label="History" value={frame?.provenance.source_history_file ?? "Loading"} />
        <Metric label="Coordinates" value="Translating model frame" />
      </dl>
      {frame && (
        <details>
          <summary>Fields, scales, and thresholds</summary>
          <ul className="supercells-detail-list">
            {frame.scene?.layers.map((layer) => (
              <li key={layer.key}>
                <strong>{layer.display_name}</strong>
                <span>
                  {layer.evidence_kind} · {layer.source_fields.join(", ")} · {layer.threshold_label}
                </span>
                {layer.scale && <code>{layer.scale.scale_id}</code>}
              </li>
            ))}
          </ul>
        </details>
      )}
      <details>
        <summary>Relevant limitations</summary>
        <ul>
          {frame?.caveats.map((caveat) => <li key={caveat}>{caveat}</li>) ?? <li>Loading.</li>}
        </ul>
      </details>
    </section>
  );
}

function LocalFailure({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <section className="layer-local-error supercells-local-error">
      <h3>{title}</h3>
      <p role="alert">{message}</p>
      <button type="button" onClick={onRetry}>
        Retry
      </button>
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

function overlayDefaults(lens: LensId): OverlayState {
  return {
    rotation: lens === "rotating_updraft",
    updraftHelicity: lens === "rotating_updraft",
    reflectivity: false,
    condensate: true,
    rain: lens === "low_level_interactions",
    wind: lens === "low_level_interactions",
    precipitatingCondensate: false,
    verticalMotion: true,
  };
}

function filterHydrometeorCategories(
  scene: StormExaminationFrame["scene"],
  categoryCodes: number[],
): StormScenePayload | null {
  if (!scene) return null;
  return {
    coordinate_extents_km: scene.coordinate_extents_km,
    layers: scene.layers.map((layer) =>
      layer.key === "hydrometeor_categories"
        ? { ...layer, points: layer.points.filter((point) => categoryCodes.includes(point[4])) }
        : layer,
    ),
  };
}

function nearestCoordinateIndex(
  value: number,
  coordinates: number[],
  sourceIndices?: number[],
): number {
  let nearest = 0;
  let distance = Number.POSITIVE_INFINITY;
  coordinates.forEach((coordinate, index) => {
    const nextDistance = Math.abs(coordinate - value);
    if (nextDistance < distance) {
      distance = nextDistance;
      nearest = index;
    }
  });
  return sourceIndices?.[nearest] ?? nearest;
}

function evidenceSlice(frame: StormExaminationFrame, view: EvidenceView) {
  const field = {
    raw_field_name: frame.plan.primary.key,
    display_name: frame.plan.primary.display_name,
    units: frame.plan.primary.units,
  };
  if (view === "plan") {
    return {
      field,
      selection: {
        orientation: "horizontal" as const,
        selected_dimension: "zh",
        selected_index: frame.plan.level_index,
        selected_coordinate_value: frame.plan.level_km,
        level_coordinate_value: frame.plan.level_km,
        level_units: "km",
        level_meters: frame.plan.level_km * 1_000,
      },
    };
  }
  const section = view === "xz" ? frame.xz_section : frame.yz_section;
  return {
    field,
    selection: {
      orientation: view === "xz" ? ("vertical_x" as const) : ("vertical_y" as const),
      selected_dimension: view === "xz" ? "yh" : "xh",
      selected_index: view === "xz" ? frame.selected_point.y_index : frame.selected_point.x_index,
      selected_coordinate_value: section.cross_section_coordinate_km,
      level_coordinate_value: null,
      level_units: "km",
      level_meters: null,
    },
  };
}

function evidenceLabel(frame: StormExaminationFrame, view: EvidenceView): string {
  if (view === "plan") {
    return `${frame.plan.title} · z = ${frame.plan.level_km.toFixed(2)} km`;
  }
  return view === "xz" ? frame.xz_section.title : frame.yz_section.title;
}

function evidenceTitle(view: EvidenceView): string {
  return `${sliceControlLabel(view)} slice`;
}

function sliceControlLabel(view: EvidenceView): string {
  if (view === "plan") return "Horizontal x-y";
  return view === "xz" ? "Vertical x-z" : "Vertical y-z";
}

function lensExplanation(lens: LensId): string {
  if (lens === "rotating_updraft") {
    return "Signed vertical motion reveals ascent and descent; cyclonic vorticity and 2–5 km updraft helicity show where rising and rotating structure overlap.";
  }
  if (lens === "cloud_precipitation") {
    return "Native cloud liquid, rain, cloud ice, snow, and hail-treated large ice are grouped by the dominant mass species while the inspector retains every value.";
  }
  return "Low-level vertical motion, accumulated rain, and model-relative horizontal flow show how ascent, descent, and precipitation meet beneath the storm without diagnosing a cold pool.";
}

function scienceKeys(lens: LensId): string[] {
  if (lens === "rotating_updraft") {
    return [
      "vertical_velocity",
      "vertical_vorticity",
      "updraft_helicity",
      "reflectivity",
      "total_condensate",
    ];
  }
  if (lens === "cloud_precipitation") {
    return [
      "cloud_liquid",
      "rain_water",
      "cloud_ice",
      "snow",
      "hail_treated_large_ice",
      "total_condensate",
      "reflectivity",
    ];
  }
  return [
    "vertical_velocity",
    "accumulated_surface_rain",
    "model_relative_u",
    "model_relative_v",
    "reflectivity",
    "total_condensate",
  ];
}

function scienceLabel(key: string): string {
  return (
    {
      vertical_velocity: "Vertical velocity",
      vertical_vorticity: "Vertical vorticity",
      updraft_helicity: "2–5 km AGL UH",
      reflectivity: "Reflectivity",
      cloud_liquid: "Cloud liquid",
      rain_water: "Rain water",
      cloud_ice: "Cloud ice",
      snow: "Snow",
      hail_treated_large_ice: "Hail-treated large ice",
      total_condensate: "Total condensate",
      accumulated_surface_rain: "Accumulated surface rain",
      model_relative_u: "Model-relative u",
      model_relative_v: "Model-relative v",
    }[key] ?? key
  );
}

function formatScientific(value: number | undefined): string {
  if (value === undefined || !Number.isFinite(value)) return "Unavailable";
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  if (Math.abs(value) >= 0.1) return value.toFixed(2);
  return value.toExponential(2);
}

function formatTime(seconds: number): string {
  const minutes = Math.round(seconds / 60);
  return `${minutes} min · ${seconds.toLocaleString()} s`;
}

function frameRequestKey(
  lens: LensId,
  viewport: ViewportId,
  timeIndex: number,
  selection: Selection | null,
): string {
  return `${lens}:${viewport}:${timeIndex}:${selection ? `${selection.xIndex},${selection.yIndex},${selection.zIndex}` : "primary"}`;
}

async function fetchSupercellFrame(
  simulationId: string,
  lens: LensId,
  viewport: ViewportId,
  timeIndex: number,
  selection: Selection | null,
  signal?: AbortSignal,
): Promise<StormExaminationFrame> {
  const search = new URLSearchParams({ lens, viewport, time_index: String(timeIndex) });
  if (selection) {
    search.set("x_index", String(selection.xIndex));
    search.set("y_index", String(selection.yIndex));
    search.set("z_index", String(selection.zIndex));
  }
  const response = await fetch(
    `/api/worlds/supercells/simulations/${simulationId}/frame?${search}`,
    { signal },
  );
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Supercell frame failed (${response.status}).`);
  }
  const payload = (await response.json()) as StormExaminationFrame;
  if (
    payload.schema_version !== "supercells_explore_v1" ||
    payload.world_id !== "supercells" ||
    payload.simulation_id !== "supercells_quarter_circle_reference"
  ) {
    throw new Error("Supercell frame response does not match the production World contract.");
  }
  return payload;
}

async function prefetchAdjacentFrames(
  cache: Map<string, StormExaminationFrame>,
  simulationId: string,
  frame: StormExaminationFrame,
  lens: LensId,
  viewport: ViewportId,
) {
  const candidates = [frame.time_index - 1, frame.time_index + 1].filter(
    (index) => index >= 0 && index < frame.times_seconds.length,
  );
  for (const index of candidates) {
    const key = frameRequestKey(lens, viewport, index, null);
    if (cache.has(key)) continue;
    try {
      cache.set(key, await fetchSupercellFrame(simulationId, lens, viewport, index, null));
      trimCache(cache, 8);
    } catch {
      // Adjacent prefetch is optional; the requested frame remains authoritative.
    }
  }
}

function trimCache(cache: Map<string, StormExaminationFrame>, maximum: number) {
  while (cache.size > maximum) {
    const first = cache.keys().next().value as string | undefined;
    if (first === undefined) return;
    cache.delete(first);
  }
}

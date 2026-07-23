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
import {
  type CameraPreset,
  type StormScenePayload,
  type StormScenePoint,
  True3DViewer,
} from "./True3DViewer";

import "./StormExaminationResearch.css";
import "./SupercellsExplore.css";

type EvidenceView = "plan" | "xz" | "yz";
type FocusedViewer = "scene" | "evidence" | null;
type LensPresentation = {
  viewport: ViewportId;
  evidenceView: EvidenceView;
  overlays: OverlayState;
  visibleLayerKeys: string[] | null;
  categoryCodes: number[];
  cameraPreset: CameraPreset;
  sceneOpacity: number;
  scenePointSize: number;
  selection: Selection | null;
};

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
  const [timeIndex, setTimeIndex] = useState(simulation.default_explore_time_index);
  const [frame, setFrame] = useState<StormExaminationFrame | null>(null);
  const [presentations, setPresentations] = useState<Record<LensId, LensPresentation>>(
    lensPresentationDefaults,
  );
  const presentation = presentations[lens];
  const {
    viewport,
    evidenceView,
    overlays,
    categoryCodes,
    cameraPreset,
    sceneOpacity,
    scenePointSize,
    selection,
  } = presentation;
  const visibleLayerKeys = presentation.visibleLayerKeys ?? [];
  const [focusedViewer, setFocusedViewer] = useState<FocusedViewer>(null);
  const [contextCollapsed, setContextCollapsed] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const frameCache = useRef(new Map<string, StormExaminationFrame>());
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
    if (
      !frame?.scene ||
      frame.lens_id !== lens ||
      presentations[lens].visibleLayerKeys !== null
    )
      return;
    const layerKeys = frame.scene.layers
      .filter((layer) => layer.default_visible)
      .map((layer) => layer.key);
    if (lens === "low_level_interactions") layerKeys.push("model_relative_wind");
    setPresentations((current) => ({
      ...current,
      [lens]: { ...current[lens], visibleLayerKeys: layerKeys },
    }));
  }, [frame, lens, presentations]);

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
    setFrame(null);
    setLens(next);
  }

  function selectPoint(next: Selection) {
    setPlaying(false);
    updatePresentation({ selection: next });
  }

  function updatePresentation(patch: Partial<LensPresentation>) {
    setPresentations((current) => ({
      ...current,
      [lens]: { ...current[lens], ...patch },
    }));
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
    updatePresentation({
      visibleLayerKeys: visible
        ? [...new Set([...visibleLayerKeys, key])]
        : visibleLayerKeys.filter((item) => item !== key),
    });
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
                showWindVectors={visibleLayerKeys.includes("model_relative_wind")}
                windMode="total"
                windReferenceMps={frame.scene.wind_reference_m_s}
                windArrowDomainFraction={0.055}
                compactWorkspace
                compactDisplayLabel="3-D layers"
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
                cameraPreset={cameraPreset}
                onCameraPresetChange={(next) => updatePresentation({ cameraPreset: next })}
                compactDisplayControls={
                  <StormDisplayControls
                    frame={frame}
                    visibleLayerKeys={visibleLayerKeys}
                    opacity={sceneOpacity}
                    pointSize={scenePointSize}
                    categoryCodes={categoryCodes}
                    onLayer={toggleLayer}
                    onOpacity={(next) => updatePresentation({ sceneOpacity: next })}
                    onPointSize={(next) => updatePresentation({ scenePointSize: next })}
                    onCategoryCodes={(next) => updatePresentation({ categoryCodes: next })}
                  />
                }
              />
            ) : loading ? (
              <div className="supercells-loading-surface" role="status">
                Loading 3-D Lens...
              </div>
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
                <h2>{evidenceTitle(frame, evidenceView)}</h2>
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
                      onClick={() => updatePresentation({ evidenceView: view })}
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
                <StormLegend frame={frame} overlays={overlays} evidenceView={evidenceView} />
              </div>
            ) : loading ? (
              <div className="supercells-loading-surface" role="status">
                Loading coordinated evidence...
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
              explain: (
                <SupercellExplanation
                  frame={frame}
                  lens={lens}
                  viewport={viewport}
                  evidenceView={evidenceView}
                />
              ),
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
          onViewport={(next) => {
            setPlaying(false);
            updatePresentation({ viewport: next });
          }}
          onEvidenceView={(next) => updatePresentation({ evidenceView: next })}
          onOverlays={(next) => updatePresentation({ overlays: next })}
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
      <strong className="supercells-display-heading">3-D layers</strong>
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
        {Boolean(frame.scene?.wind_vectors.length) && (
          <label>
            <input
              type="checkbox"
              checked={visibleLayerKeys.includes("model_relative_wind")}
              onChange={(event) =>
                onLayer("model_relative_wind", event.currentTarget.checked)
              }
            />
            Model-relative wind at 1.25 km
          </label>
        )}
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
  onViewport,
  onEvidenceView,
  onOverlays,
}: {
  lens: LensId;
  viewport: ViewportId;
  evidenceView: EvidenceView;
  overlays: OverlayState;
  onViewport: (value: ViewportId) => void;
  onEvidenceView: (value: EvidenceView) => void;
  onOverlays: (value: OverlayState) => void;
}) {
  const controls = overlayControls(lens, evidenceView);
  function update(control: OverlayControl, checked: boolean) {
    onOverlays({ ...overlays, [control.overlayKey]: checked });
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
        <legend>2-D evidence</legend>
        {controls.map((control) => (
          <label key={control.label}>
            <input
              type="checkbox"
              checked={overlays[control.overlayKey]}
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
};

function overlayControls(lens: LensId, evidenceView: EvidenceView): OverlayControl[] {
  if (lens === "rotating_updraft") {
    const controls: OverlayControl[] = [
      { label: "Cloud boundary", overlayKey: "condensate" },
      { label: "Rotation contour", overlayKey: "rotation" },
      { label: "Reflectivity contour", overlayKey: "reflectivity" },
    ];
    if (evidenceView === "plan") {
      controls.splice(2, 0, { label: "2-5 km UH footprint", overlayKey: "updraftHelicity" });
    }
    return controls;
  }
  if (lens === "cloud_precipitation") {
    return [
      { label: "Vertical-motion contours", overlayKey: "verticalMotion" },
      { label: "Reflectivity contour", overlayKey: "reflectivity" },
    ];
  }
  const controls: OverlayControl[] = [
    { label: "Current precipitation", overlayKey: "precipitatingCondensate" },
    { label: "Reflectivity contour", overlayKey: "reflectivity" },
  ];
  if (evidenceView === "plan") {
    controls.unshift(
      { label: "Accumulated rain (history)", overlayKey: "rain" },
      { label: "Flow arrows at 1.25 km", overlayKey: "wind" },
    );
  }
  return controls;
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
  evidenceView,
}: {
  frame: StormExaminationFrame | null;
  lens: LensId;
  viewport: ViewportId;
  evidenceView: EvidenceView;
}) {
  const question =
    frame?.lens_question ?? LENSES.find((item) => item.id === lens)?.label ?? "Storm evidence";
  return (
    <section className="supercells-context-panel">
      <p className="eyebrow">{frame?.lens_name ?? "Supercell Lens"}</p>
      <h3>{question}</h3>
      <p>{lensExplanation(lens, evidenceView)}</p>
      {frame && (
        <div className="supercells-notice-now">
          <strong>What to notice now</strong>
          <p>{frame.what_to_notice_by_view?.[evidenceView] ?? frame.what_to_notice_now}</p>
        </div>
      )}
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
      <p className="eyebrow">
        {selected ? "Selected point" : "Strongest-updraft column at slice level"}
      </p>
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
          label="Horizontal distance to strongest-updraft column"
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
    condensate: lens === "rotating_updraft",
    rain: lens === "low_level_interactions",
    wind: lens === "low_level_interactions",
    precipitatingCondensate: lens === "low_level_interactions",
    verticalMotion: true,
  };
}

function lensPresentationDefaults(): Record<LensId, LensPresentation> {
  const categoryCodes = HYDROMETEOR_CODES.map((item) => item.code);
  return {
    rotating_updraft: {
      viewport: "storm",
      evidenceView: "plan",
      overlays: overlayDefaults("rotating_updraft"),
      visibleLayerKeys: null,
      categoryCodes,
      cameraPreset: "look_along_y",
      sceneOpacity: 1,
      scenePointSize: 1,
      selection: null,
    },
    cloud_precipitation: {
      viewport: "storm",
      evidenceView: "xz",
      overlays: overlayDefaults("cloud_precipitation"),
      visibleLayerKeys: null,
      categoryCodes,
      cameraPreset: "look_along_y",
      sceneOpacity: 0.9,
      scenePointSize: 0.9,
      selection: null,
    },
    low_level_interactions: {
      viewport: "storm",
      evidenceView: "plan",
      overlays: overlayDefaults("low_level_interactions"),
      visibleLayerKeys: null,
      categoryCodes,
      cameraPreset: "low_level",
      sceneOpacity: 1,
      scenePointSize: 1,
      selection: null,
    },
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
  if (view === "plan") {
    const field = {
      raw_field_name: frame.plan.primary.key,
      display_name: frame.plan.primary.display_name,
      units: frame.plan.primary.units,
    };
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
    field: {
      raw_field_name: section.primary.key,
      display_name: section.primary.display_name,
      units: section.primary.units,
    },
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
    if (frame.plan.selection_z_indices) {
      return `${frame.plan.title} · column-derived at each cell's condensate maximum`;
    }
    return `${frame.plan.title} · z = ${frame.plan.level_km.toFixed(2)} km`;
  }
  return view === "xz" ? frame.xz_section.title : frame.yz_section.title;
}

function evidenceTitle(
  frame: StormExaminationFrame | null,
  view: EvidenceView,
): string {
  if (view === "plan" && frame?.plan.selection_z_indices) {
    return "Column-derived x-y view";
  }
  return `${sliceControlLabel(view)} slice`;
}

function sliceControlLabel(view: EvidenceView): string {
  if (view === "plan") return "Horizontal x-y";
  return view === "xz" ? "Vertical x-z" : "Vertical y-z";
}

function lensExplanation(lens: LensId, evidenceView: EvidenceView): string {
  if (lens === "rotating_updraft") {
    return evidenceView === "plan"
      ? "The 3.25 km x-y slice pairs signed vertical motion with cyclonic vorticity and the 2–5 km updraft-helicity footprint, showing where ascent and rotation organize together."
      : "This native vertical section pairs signed vertical motion with cyclonic-vorticity contours, showing whether the rotating rising core remains vertically connected.";
  }
  if (lens === "cloud_precipitation") {
    return evidenceView === "plan"
      ? "This column-derived x-y view assigns each cell the hydrometeor that dominates at its strongest-condensate level and samples vertical motion at that same level. Selecting a cell inspects the responsible native level in Context."
      : "This storm-core native section shows the dominant hydrometeor at each cell. Vertical-motion contours remain subordinate, and every native species value remains available in Context.";
  }
  return evidenceView === "plan"
    ? "The fixed 3-D lower-troposphere view and 1.25 km x-y slice coordinate current motion, precipitating condensate, and model-relative flow with the historical accumulated-rain footprint without diagnosing a cold pool."
    : "The 3-D view remains fixed on the lowest 5.25 km, while this native vertical section shows full-depth current ascent, descent, and precipitating condensate; accumulated surface rain remains a separate historical plan-view quantity.";
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
  const candidates = [frame.time_index + 1, frame.time_index - 1].filter(
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

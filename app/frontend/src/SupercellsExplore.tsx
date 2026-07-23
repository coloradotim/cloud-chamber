import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ExploreContextContent,
  ExploreInspector,
  ExploreSelectedEvidence,
  ExploreSecondarySections,
  IntegratedExploreWorkspace,
} from "./IntegratedExploreWorkspace";
import { NativeSlicePositionControl } from "./NativeSlicePositionControl";
import { SimulationNotes } from "./SimulationNotes";
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
  type CameraTransform,
  type CameraPreset,
  type StormScenePayload,
  type StormScenePoint,
  True3DViewer,
} from "./True3DViewer";

import "./StormExaminationResearch.css";
import "./SupercellsExplore.css";

type EvidenceView = "plan" | "xz" | "yz";
type FocusedViewer = "scene" | "evidence" | null;
type SliceAxis = "x" | "y" | "z";
type SlicePositionState = {
  axis: SliceAxis;
  coordinatesKm: number[];
  nativeIndices: number[];
  positionIndex: number;
};
type LensPresentation = {
  viewport: ViewportId;
  evidenceView: EvidenceView;
  overlays: OverlayState;
  visibleLayerKeys: string[] | null;
  categoryCodes: number[];
  cameraPreset: CameraPreset;
  cameraTransform: CameraTransform | null;
  sceneOpacity: number;
  scenePointSize: number;
  selection: Selection | null;
  selectedEvidenceVisible: boolean;
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
  const [presentations, setPresentations] =
    useState<Record<LensId, LensPresentation>>(lensPresentationDefaults);
  const presentation = presentations[lens];
  const {
    viewport,
    evidenceView,
    overlays,
    categoryCodes,
    cameraPreset,
    cameraTransform,
    sceneOpacity,
    scenePointSize,
    selection,
    selectedEvidenceVisible,
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
          selection,
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
    if (!frame?.scene || frame.lens_id !== lens || presentations[lens].visibleLayerKeys !== null)
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
  const slicePosition = useMemo(
    () => (frame ? slicePositionState(frame, evidenceView, selection) : null),
    [evidenceView, frame, selection],
  );
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
    updatePresentation({ selection: next, selectedEvidenceVisible: true });
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

  function setSlicePosition(positionIndex: number) {
    if (!frame || !slicePosition) return;
    const nativeIndex = slicePosition.nativeIndices[positionIndex];
    if (nativeIndex === undefined) return;
    const next = selection
      ? { ...selection }
      : {
          xIndex: frame.selected_point.x_index,
          yIndex: frame.selected_point.y_index,
          zIndex: frame.selected_point.z_index,
        };
    if (slicePosition.axis === "x") next.xIndex = nativeIndex;
    if (slicePosition.axis === "y") next.yIndex = nativeIndex;
    if (slicePosition.axis === "z") next.zIndex = nativeIndex;
    selectPoint(next);
  }

  function resetSlicePosition() {
    setPlaying(false);
    updatePresentation({ selection: null, selectedEvidenceVisible: false });
  }

  function clearSelectedEvidence() {
    setPlaying(false);
    updatePresentation({ selectedEvidenceVisible: false });
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
                showSlicePlane={evidenceView !== "plan" || frame.plan.selection_z_indices === null}
                selectedRegion={
                  frame && selection && selectedEvidenceVisible
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
                windOverlayLabel={`Model-relative wind at z = ${frame.plan.level_km.toFixed(2)} km`}
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
                  selection && selectedEvidenceVisible && frame
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
                cameraTransform={cameraTransform}
                onCameraTransformChange={(next) => updatePresentation({ cameraTransform: next })}
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
                    <StormPlanPlot
                      frame={frame}
                      overlays={overlays}
                      onSelect={selectPoint}
                      showSelection={selection === null || selectedEvidenceVisible}
                    />
                  ) : (
                    <StormSectionPlot
                      section={evidenceView === "xz" ? frame.xz_section : frame.yz_section}
                      frame={frame}
                      overlays={overlays}
                      onSelect={selectPoint}
                      showSelection={selection === null || selectedEvidenceVisible}
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
          >
            <SupercellExplanation
              frame={frame}
              lens={lens}
              viewport={viewport}
              evidenceView={evidenceView}
              selected={selection !== null && selectedEvidenceVisible}
              onClearSelection={clearSelectedEvidence}
            />
          </ExploreInspector>
        </div>

        <StormExploreControls
          lens={lens}
          viewport={viewport}
          evidenceView={evidenceView}
          planLevelKm={frame?.plan.level_km ?? null}
          overlays={overlays}
          onViewport={(next) => {
            setPlaying(false);
            updatePresentation({ viewport: next });
          }}
          onEvidenceView={(next) => updatePresentation({ evidenceView: next })}
          slicePosition={slicePosition}
          onSlicePosition={setSlicePosition}
          onResetSlicePosition={resetSlicePosition}
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

        <ExploreSecondarySections
          sections={{
            science: <SupercellScience frame={frame} lens={lens} />,
            notes: (
              <SimulationNotes
                worldId="supercells"
                simulationId={simulation.simulation_id}
                simulationName={simulation.display_name}
              />
            ),
            details: <SupercellDetails frame={frame} simulation={simulation} />,
          }}
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
              onChange={(event) => onLayer("model_relative_wind", event.currentTarget.checked)}
            />
            Model-relative wind at z = {frame.plan.level_km.toFixed(2)} km
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
  planLevelKm,
  overlays,
  slicePosition,
  onViewport,
  onEvidenceView,
  onSlicePosition,
  onResetSlicePosition,
  onOverlays,
}: {
  lens: LensId;
  viewport: ViewportId;
  evidenceView: EvidenceView;
  planLevelKm: number | null;
  overlays: OverlayState;
  slicePosition: SlicePositionState | null;
  onViewport: (value: ViewportId) => void;
  onEvidenceView: (value: EvidenceView) => void;
  onSlicePosition: (positionIndex: number) => void;
  onResetSlicePosition: () => void;
  onOverlays: (value: OverlayState) => void;
}) {
  const controls = overlayControls(lens, evidenceView, planLevelKm);
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
      <SupercellSlicePositionControl
        view={evidenceView}
        position={slicePosition}
        onPosition={onSlicePosition}
        onReset={onResetSlicePosition}
      />
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

function SupercellSlicePositionControl({
  view,
  position,
  onPosition,
  onReset,
}: {
  view: EvidenceView;
  position: SlicePositionState | null;
  onPosition: (positionIndex: number) => void;
  onReset: () => void;
}) {
  if (!position) {
    return (
      <fieldset className="supercells-slice-position">
        <legend>Position</legend>
        <p>Column-derived across z; choose a vertical slice to position a native plane.</p>
      </fieldset>
    );
  }
  const coordinate = position.coordinatesKm[position.positionIndex] ?? 0;
  const nativeIndex = position.nativeIndices[position.positionIndex] ?? 0;
  const label = `${sliceControlLabel(view)} ${position.axis} position`;
  const plane =
    view === "plan"
      ? ("horizontal" as const)
      : view === "xz"
        ? ("vertical_x" as const)
        : ("vertical_y" as const);
  return (
    <fieldset className="supercells-slice-position">
      <legend>Position</legend>
      <NativeSlicePositionControl
        id={`supercells-${view}-position`}
        ariaLabel={label}
        plane={plane}
        positionIndex={position.positionIndex}
        positionCount={position.coordinatesKm.length}
        positionLabel={`${position.axis} ${formatCoordinateKm(coordinate)}`}
        indexLabel={`native index ${nativeIndex}`}
        onPositionChange={onPosition}
        onReset={onReset}
        resetLabel="Return slice to curated position"
        compact
      />
    </fieldset>
  );
}

type OverlayControl = {
  label: string;
  overlayKey: keyof OverlayState;
};

function overlayControls(
  lens: LensId,
  evidenceView: EvidenceView,
  planLevelKm: number | null,
): OverlayControl[] {
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
    const flowLevel =
      typeof planLevelKm === "number" && Number.isFinite(planLevelKm)
        ? ` at z = ${planLevelKm.toFixed(2)} km`
        : "";
    controls.unshift(
      { label: "Accumulated rain (history)", overlayKey: "rain" },
      { label: `Flow arrows${flowLevel}`, overlayKey: "wind" },
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
  selected,
  onClearSelection,
}: {
  frame: StormExaminationFrame | null;
  lens: LensId;
  viewport: ViewportId;
  evidenceView: EvidenceView;
  selected: boolean;
  onClearSelection: () => void;
}) {
  const question =
    frame?.lens_question ?? LENSES.find((item) => item.id === lens)?.label ?? "Storm evidence";
  const point = frame?.selected_point;
  const selectedEvidence =
    selected && point ? (
      <ExploreSelectedEvidence
        eyebrow="Selected cell"
        title="Native-grid evidence"
        states={point.states}
        metrics={[
          { label: "x", value: `${point.x_km.toFixed(1)} km` },
          { label: "y", value: `${point.y_km.toFixed(1)} km` },
          { label: "z", value: `${point.z_km.toFixed(2)} km` },
          { label: "Model time", value: formatTime(point.model_time_seconds) },
          ...scienceKeys(frame.lens_id).map((key) => ({
            label: scienceLabel(key),
            value: `${formatScientific(point.values[key])} ${point.units[key] ?? ""}`.trim(),
          })),
        ]}
        onClear={onClearSelection}
        className="supercells-selected-context"
      />
    ) : undefined;
  return (
    <ExploreContextContent
      identity={frame?.lens_name ?? "Supercell Lens"}
      question={question}
      explanation={<p>{lensExplanation(lens, evidenceView, frame?.plan.level_km)}</p>}
      selectedEvidence={selectedEvidence}
      whatToNotice={
        frame ? (
          <p>{frame.what_to_notice_by_view?.[evidenceView] ?? frame.what_to_notice_now}</p>
        ) : undefined
      }
      orientation={[
        { label: "Simulation", value: "Quarter-Circle Supercell" },
        { label: "View", value: sliceControlLabel(evidenceView) },
        { label: "Viewport", value: viewport === "storm" ? "Storm region" : "Full domain" },
        { label: "Model time", value: formatTime(frame?.time_seconds ?? 0) },
        {
          label: "Relevant caveat",
          value:
            frame?.caveats[lens === "low_level_interactions" ? 4 : 0] ??
            "Retained storm evidence is loading.",
        },
      ]}
      selectionPrompt={
        selected ? undefined : "Select a cell in the plan or section for native-grid evidence."
      }
    />
  );
}

function SupercellScience({ frame, lens }: { frame: StormExaminationFrame | null; lens: LensId }) {
  const primary = frame?.plan.primary;
  return (
    <section className="explore-science-section">
      <p className="eyebrow">Science</p>
      <h3>{frame?.lens_name ?? LENSES.find((item) => item.id === lens)?.label}</h3>
      <p>{supercellScienceExplanation(lens)}</p>
      <dl className="metric-grid compact-metric-grid">
        <Metric
          label="Fixed primary scale"
          value={
            primary
              ? `${formatScientific(primary.scale.minimum)} to ${formatScientific(
                  primary.scale.maximum,
                )} ${primary.scale.units}`
              : "Loading"
          }
        />
        <Metric
          label="Current plan range"
          value={
            primary
              ? `${formatScientific(primary.selected_frame_minimum)} to ${formatScientific(
                  primary.selected_frame_maximum,
                )} ${primary.units}`
              : "Loading"
          }
        />
        <Metric
          label="Coordinate frame"
          value={frame?.selected_point.coordinate_frame ?? "Translating model frame"}
        />
        <Metric
          label="Sampling"
          value="Retained native cells; overlays identify explicitly derived quantities"
        />
      </dl>
      {frame && (
        <details>
          <summary>Scientific limitations</summary>
          <ul>
            {frame.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function supercellScienceExplanation(lens: LensId): string {
  if (lens === "rotating_updraft") {
    return "Compare the signed updraft with cyclonic vorticity and the 2-5 km updraft-helicity footprint. Their overlap shows where sustained ascent and rotation are organized together; no single overlay is treated as the storm by itself.";
  }
  if (lens === "cloud_precipitation") {
    return "Dominant hydrometeor identity shows which retained condensate species has the largest local mass. Use it with the vertical-motion field and precipitation evidence to distinguish cloud structure from falling or accumulated water.";
  }
  return "Read low-level ascent and descent together with the rain footprint and model-relative flow. The view tests how outflow, inflow, precipitation, and near-surface vertical motion occupy the same storm-relative region without inferring a process from one cell.";
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
      cameraTransform: null,
      sceneOpacity: 1,
      scenePointSize: 1,
      selection: null,
      selectedEvidenceVisible: false,
    },
    cloud_precipitation: {
      viewport: "storm",
      evidenceView: "xz",
      overlays: overlayDefaults("cloud_precipitation"),
      visibleLayerKeys: null,
      categoryCodes,
      cameraPreset: "look_along_y",
      cameraTransform: null,
      sceneOpacity: 0.9,
      scenePointSize: 0.9,
      selection: null,
      selectedEvidenceVisible: false,
    },
    low_level_interactions: {
      viewport: "storm",
      evidenceView: "plan",
      overlays: overlayDefaults("low_level_interactions"),
      visibleLayerKeys: null,
      categoryCodes,
      cameraPreset: "low_level",
      cameraTransform: null,
      sceneOpacity: 1,
      scenePointSize: 1,
      selection: null,
      selectedEvidenceVisible: false,
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

function slicePositionState(
  frame: StormExaminationFrame,
  view: EvidenceView,
  selection: Selection | null,
): SlicePositionState | null {
  if (view === "plan" && frame.plan.selection_z_indices) return null;
  const axis: SliceAxis = view === "plan" ? "z" : view === "xz" ? "y" : "x";
  const coordinatesKm = frame.scene?.coordinate_values_km[axis] ?? [];
  const nativeIndices = frame.scene?.coordinate_indices[axis] ?? [];
  if (coordinatesKm.length === 0 || coordinatesKm.length !== nativeIndices.length) return null;
  const selectedNativeIndex =
    axis === "x"
      ? (selection?.xIndex ?? frame.selected_point.x_index)
      : axis === "y"
        ? (selection?.yIndex ?? frame.selected_point.y_index)
        : (selection?.zIndex ?? frame.plan.level_index);
  const exactPosition = nativeIndices.indexOf(selectedNativeIndex);
  const positionIndex =
    exactPosition >= 0
      ? exactPosition
      : nativeIndices.reduce(
          (nearest, candidate, index) =>
            Math.abs(candidate - selectedNativeIndex) <
            Math.abs(nativeIndices[nearest] - selectedNativeIndex)
              ? index
              : nearest,
          0,
        );
  return { axis, coordinatesKm, nativeIndices, positionIndex };
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

function evidenceTitle(frame: StormExaminationFrame | null, view: EvidenceView): string {
  if (view === "plan" && frame?.plan.selection_z_indices) {
    return "Column-derived x-y view";
  }
  return `${sliceControlLabel(view)} slice`;
}

function sliceControlLabel(view: EvidenceView): string {
  if (view === "plan") return "Horizontal x-y";
  return view === "xz" ? "Vertical x-z" : "Vertical y-z";
}

function lensExplanation(lens: LensId, evidenceView: EvidenceView, planLevelKm?: number): string {
  const level =
    typeof planLevelKm === "number" && Number.isFinite(planLevelKm)
      ? `z = ${planLevelKm.toFixed(2)} km`
      : "the selected native altitude";
  if (lens === "rotating_updraft") {
    return evidenceView === "plan"
      ? `The x-y slice at ${level} pairs signed vertical motion with cyclonic vorticity and the 2–5 km updraft-helicity footprint, showing where ascent and rotation organize together.`
      : "This native vertical section pairs signed vertical motion with cyclonic-vorticity contours, showing whether the rotating rising core remains vertically connected.";
  }
  if (lens === "cloud_precipitation") {
    return evidenceView === "plan"
      ? "This column-derived x-y view assigns each cell the hydrometeor that dominates at its strongest-condensate level and samples vertical motion at that same level. Selecting a cell inspects the responsible native level in Context."
      : "This storm-core native section shows the dominant hydrometeor at each cell. Vertical-motion contours remain subordinate, and every native species value remains available in Context.";
  }
  return evidenceView === "plan"
    ? `The fixed 3-D lower-troposphere view and x-y slice at ${level} coordinate current motion, precipitating condensate, and model-relative flow with the historical accumulated-rain footprint without diagnosing a cold pool.`
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

function formatCoordinateKm(value: number): string {
  const precision = Math.abs(value) >= 10 ? 1 : 2;
  return `${value.toFixed(precision)} km`;
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
  selection: Selection | null,
) {
  const candidates = [frame.time_index + 1, frame.time_index - 1].filter(
    (index) => index >= 0 && index < frame.times_seconds.length,
  );
  for (const index of candidates) {
    const key = frameRequestKey(lens, viewport, index, selection);
    if (cache.has(key)) continue;
    try {
      cache.set(key, await fetchSupercellFrame(simulationId, lens, viewport, index, selection));
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

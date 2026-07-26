import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  type ExplorePoint,
  type ExploreWorldState,
  type MountainWavesExploreState,
  type SupercellsExploreState,
  type TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import {
  type MountainWaveFrame,
  MountainWavesLegend,
  MountainWavesTerrainPlot,
  type MountainWavesViewMode,
} from "./MountainWavesExplore";
import { NativeSlicePositionControl } from "./NativeSlicePositionControl";
import { type StormScenePayload, type StormScenePoint, True3DViewer } from "./True3DViewer";
import {
  type OverlayState,
  type Selection,
  type StormExaminationFrame,
  StormLegend,
  StormPlanPlot,
  StormSectionPlot,
} from "./StormExaminationResearch";
import {
  type UpdraftLensFrame,
  type UpdraftLensPointSelection,
  UpdraftLensSlice,
} from "./UpdraftLensSlice";
import { timeIndexForSeconds } from "./WorldCompare.logic";
import {
  isMountainState,
  isSupercellsState,
  isTradeState,
  type ComparePerformanceSample,
  type CompareSide,
  type CompareSimulationDescriptor,
} from "./WorldCompare.types";

type SideVisualProps = {
  side: CompareSide;
  simulation: CompareSimulationDescriptor;
  state: ExploreWorldState;
  onStateChange: (state: ExploreWorldState) => void;
  onFrameState: (side: CompareSide, state: "loading" | "ready" | "error") => void;
  onPerformance: (sample: ComparePerformanceSample) => void;
  commonMountainScale?: TerrainScale | null;
  onMountainScale?: (side: CompareSide, scale: TerrainScale | null) => void;
  onEvidence?: (side: CompareSide, evidence: CompareSelectedEvidence | null) => void;
};

export type TerrainScale = MountainWaveFrame["scale"];
export type CompareSelectedEvidence = {
  title: string;
  states: string[];
  metrics: Array<{ label: string; value: string; numericValue?: number; units?: string }>;
};

export function WorldCompareSideVisual(props: SideVisualProps) {
  if (props.simulation.world_id === "trade_cumulus" && isTradeState(props.state)) {
    return <TradeCumulusCompareVisual {...props} state={props.state} />;
  }
  if (props.simulation.world_id === "mountain_waves" && isMountainState(props.state)) {
    return <MountainWavesCompareVisual {...props} state={props.state} />;
  }
  if (props.simulation.world_id === "supercells" && isSupercellsState(props.state)) {
    return <SupercellsCompareVisual {...props} state={props.state} />;
  }
  return (
    <section className="compare-side-error" role="alert">
      <h4>View unavailable</h4>
      <p>This World adapter cannot render the selected transient state.</p>
    </section>
  );
}

function TradeCumulusCompareVisual({
  side,
  simulation,
  state,
  onStateChange,
  onFrameState,
  onPerformance,
  onEvidence,
}: Omit<SideVisualProps, "state"> & { state: TradeCumulusExploreState }) {
  const timeIndex = timeIndexForSeconds(simulation, state.model_time_seconds);
  const lensUrl =
    state.view_id === "updraft_lens" && simulation.result_id
      ? `/api/results/${simulation.result_id}/visualization/trade-cumulus-updraft-lens/frame?${new URLSearchParams(
          {
            time_index: String(timeIndex),
            orientation: state.active_slice_plane,
            plane_index: String(state.slice_native_index),
            wind_mode: state.wind_mode,
          },
        )}`
      : null;
  const cloudUrl =
    state.view_id === "field" && simulation.result_id
      ? `/api/results/${simulation.result_id}/visualization/point-cloud?${new URLSearchParams({
          field: state.scene_field_id,
          time_index: String(timeIndex),
          threshold: String(state.threshold_native),
          max_points: "18000",
          encoding: "json",
        })}`
      : null;
  const lens = useBoundedJson<UpdraftLensFrame>(side, lensUrl, onFrameState, onPerformance);
  const cloud = useBoundedJson<TradePointCloud>(side, cloudUrl, onFrameState, onPerformance);
  const frame = lens.data;
  const planeValues = useMemo(
    () => (frame ? coordinateValues(frame, frame.plane_dimension) : []),
    [frame],
  );
  const planeIndex = frame
    ? Math.max(
        0,
        planeValues.findIndex((value) => value === frame.plane_coordinate),
      )
    : state.slice_native_index;
  const selectedLensEvidence = useMemo(
    () => (frame ? tradeSelectedEvidence(frame, state.selected_point) : null),
    [frame, state.selected_point],
  );

  useEffect(() => {
    onEvidence?.(side, selectedLensEvidence);
  }, [onEvidence, selectedLensEvidence, side]);

  const updatePlanePosition = useCallback(
    (positionIndex: number) => {
      const coordinate = planeValues[positionIndex];
      if (!Number.isFinite(coordinate)) return;
      onStateChange({
        ...state,
        slice_native_index: nativePlaneIndex(frame, positionIndex),
        slice_coordinate_km: coordinate,
      });
    },
    [frame, onStateChange, planeValues, state],
  );

  if (state.view_id === "field") {
    return (
      <section className="compare-scientific-view compare-trade-field">
        <True3DViewer
          resultName={simulation.display_name}
          pointCloud={cloud.data}
          fieldLabel="Cloud water"
          valueChannelLabel="ql (kg/kg)"
          activeSlice={null}
          activeSliceLabel="No linked slice in Field mode"
          showSlicePlane={false}
          selectedRegion={null}
          coordinateSizes={{
            x: simulation.grid.nx,
            y: simulation.grid.ny,
            z: simulation.grid.nz,
          }}
          selectedTimeLabel={formatSeconds(state.model_time_seconds)}
          sceneTimeLabel={formatSeconds(cloud.data?.selection.time_seconds ?? null)}
          thresholdLabel={`${formatNumber(state.threshold_native * 1_000)} g/kg`}
          opacity={state.layer_opacity}
          pointSize={state.point_size_px}
          status={
            cloud.error
              ? "Cloud field unavailable"
              : cloud.loading
                ? "Loading cloud field"
                : "Cloud field ready"
          }
          provenanceLabel={cloud.data?.provenance.provenance_label ?? "Native CM1 scalar cells"}
          noCloudMessage="No cloud cells meet the selected threshold."
          compactWorkspace
          compactAxisLabels
          cameraPreset={state.camera_preset}
          cameraTransform={state.camera_transform}
          onCameraPresetChange={(cameraPreset) =>
            onStateChange({ ...state, camera_preset: cameraPreset })
          }
          onCameraTransformChange={(cameraTransform) =>
            onStateChange({ ...state, camera_transform: cameraTransform })
          }
        />
        <CompareLoadState loading={cloud.loading} error={cloud.error} onRetry={cloud.retry} />
      </section>
    );
  }

  return (
    <section className="compare-scientific-view compare-trade-lens">
      {frame && (
        <>
          <UpdraftLensSlice
            frame={frame}
            showCloudBoundary={state.show_cloud_boundary}
            selectedPoint={tradeSelection(frame, state.selected_point)}
            onSelectPoint={(selection) =>
              onStateChange({
                ...state,
                selected_point: tradePhysicalPoint(frame, selection),
              })
            }
          />
          <div className="compare-plane-controls">
            <div
              className="segmented-control"
              aria-label={`${simulation.display_name} slice plane`}
            >
              {(
                [
                  ["horizontal", "Horizontal x-y"],
                  ["vertical_x", "Vertical x-z"],
                  ["vertical_y", "Vertical y-z"],
                ] as const
              ).map(([orientation, label]) => (
                <button
                  type="button"
                  key={orientation}
                  className={state.active_slice_plane === orientation ? "active-control" : ""}
                  onClick={() => {
                    const dimension =
                      orientation === "horizontal" ? "z" : orientation === "vertical_x" ? "y" : "x";
                    const coordinates = coordinateValues(frame, dimension);
                    const mapped = nearestValueIndex(coordinates, state.slice_coordinate_km);
                    onStateChange({
                      ...state,
                      active_slice_plane: orientation,
                      slice_native_index: nativePlaneIndexForDimension(frame, dimension, mapped),
                      slice_coordinate_km: coordinates[mapped] ?? 0,
                    });
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <NativeSlicePositionControl
              id={`compare-${side}-trade-plane`}
              ariaLabel={`${simulation.display_name} slice position`}
              plane={state.active_slice_plane}
              positionIndex={Math.max(0, planeIndex)}
              positionCount={planeValues.length}
              positionLabel={planePositionLabel(frame)}
              indexLabel={`native index ${frame.plane_index}`}
              onPositionChange={updatePlanePosition}
              compact
            />
          </div>
        </>
      )}
      <CompareLoadState loading={lens.loading} error={lens.error} onRetry={lens.retry} />
    </section>
  );
}

function MountainWavesCompareVisual({
  side,
  simulation,
  state,
  onStateChange,
  onFrameState,
  onPerformance,
  commonMountainScale,
  onMountainScale,
  onEvidence,
}: Omit<SideVisualProps, "state"> & { state: MountainWavesExploreState }) {
  const field =
    state.view_id === "wave_structure"
      ? "w"
      : state.view_id === "wave_cloud"
        ? "cloud_over_wave"
        : state.field_id;
  const timeIndex = timeIndexForSeconds(simulation, state.model_time_seconds);
  const url = `/api/worlds/mountain-waves/simulations/${
    simulation.simulation_id
  }/compare-frame?${new URLSearchParams({
    field,
    time_index: String(timeIndex),
  })}`;
  const response = useBoundedJson<MountainCompareFrame>(side, url, onFrameState, onPerformance);
  const sourceFrame = useMemo(
    () => (response.data ? expandMountainCompareFrame(response.data) : null),
    [response.data],
  );
  const frame = useMemo(
    () =>
      sourceFrame && commonMountainScale
        ? {
            ...sourceFrame,
            scale: {
              ...commonMountainScale,
              selected_time_minimum: sourceFrame.scale.selected_time_minimum,
              selected_time_maximum: sourceFrame.scale.selected_time_maximum,
            },
          }
        : sourceFrame,
    [commonMountainScale, sourceFrame],
  );

  useEffect(() => {
    onMountainScale?.(side, sourceFrame?.scale ?? null);
  }, [onMountainScale, side, sourceFrame?.scale]);

  const selectedPoint = useMemo(
    () => (frame ? nearestMountainSelection(frame, state.selected_point) : null),
    [frame, state.selected_point],
  );
  const selectedMountainEvidence = useMemo(
    () => (frame ? mountainSelectedEvidence(frame, selectedPoint) : null),
    [frame, selectedPoint],
  );
  const viewMode: MountainWavesViewMode =
    state.view_id === "wave_cloud"
      ? "cloud"
      : state.view_id === "wave_structure"
        ? "structure"
        : "field";

  useEffect(() => {
    onEvidence?.(side, selectedMountainEvidence);
  }, [onEvidence, selectedMountainEvidence, side]);

  return (
    <section className="compare-scientific-view compare-mountain-view">
      {frame && (
        <div className="compare-mountain-plot">
          <MountainWavesTerrainPlot
            frame={frame}
            geometryMode={state.geometry_id}
            viewportMode={state.viewport_id}
            viewMode={viewMode}
            cloudPoints={state.overlays.cloud_points}
            cloudBoundary={state.overlays.cloud_boundary}
            cloudOpacity={state.cloud_opacity}
            cloudPointSize={state.cloud_point_size_px}
            saturationContour={state.overlays.saturation_contour}
            horizontalWind={state.overlays.horizontal_wind}
            potentialTemperatureContours={state.overlays.potential_temperature_contours}
            selectedPoint={selectedPoint}
            onSelectPoint={(point) =>
              onStateChange({
                ...state,
                selected_point: point ? mountainPhysicalPoint(frame, point) : null,
              })
            }
          />
          <MountainWavesLegend
            frame={frame}
            viewMode={viewMode}
            cloudPoints={state.overlays.cloud_points}
            horizontalWind={state.overlays.horizontal_wind}
            potentialTemperatureContours={state.overlays.potential_temperature_contours}
            fixedScaleLabel={
              commonMountainScale ? "Fixed across both Simulations" : "Fixed across this Simulation"
            }
          />
        </div>
      )}
      <CompareLoadState
        loading={response.loading}
        error={response.error}
        onRetry={response.retry}
      />
    </section>
  );
}

function SupercellsCompareVisual({
  side,
  simulation,
  state,
  onStateChange,
  onFrameState,
  onPerformance,
  onEvidence,
}: Omit<SideVisualProps, "state"> & { state: SupercellsExploreState }) {
  const [surface, setSurface] = useState<"scene" | "evidence">("evidence");
  const timeIndex = timeIndexForSeconds(simulation, state.model_time_seconds);
  const indices = supercellRequestIndices(simulation, state);
  const search = new URLSearchParams({
    lens: state.lens_id,
    viewport: state.viewport_id,
    time_index: String(timeIndex),
  });
  if (indices.x !== null) search.set("x_index", String(indices.x));
  if (indices.y !== null) search.set("y_index", String(indices.y));
  if (indices.z !== null) search.set("z_index", String(indices.z));
  const url = `/api/worlds/supercells/simulations/${simulation.simulation_id}/frame?${search}`;
  const response = useBoundedJson<StormExaminationFrame>(side, url, onFrameState, onPerformance);
  const frame = response.data;
  const overlays = supercellOverlayState(state);
  const scene = useMemo(
    () => filterSupercellScene(frame?.scene ?? null, state.hydrometeor_category_codes),
    [frame?.scene, state.hydrometeor_category_codes],
  );
  const evidence = useMemo(
    () => (frame && state.selected_point ? supercellSelectedEvidence(frame) : null),
    [frame, state.selected_point],
  );

  useEffect(() => {
    onEvidence?.(side, evidence);
  }, [evidence, onEvidence, side]);

  function select(selection: Selection) {
    if (!frame) return;
    const point = supercellPhysicalPoint(frame, selection);
    onStateChange({
      ...state,
      selected_point: point,
      selected_evidence_visible: true,
      plane_coordinate_km:
        state.evidence_view === "plan"
          ? point.z_km
          : state.evidence_view === "xz"
            ? (point.y_km ?? state.plane_coordinate_km)
            : point.x_km,
    });
  }

  function selectScenePoint(point: StormScenePoint) {
    onStateChange({
      ...state,
      selected_point: { x_km: point[0], y_km: point[1], z_km: point[2] },
      selected_evidence_visible: true,
    });
  }

  function showEvidence(view: SupercellsExploreState["evidence_view"]) {
    const selected = state.selected_point;
    const coordinate =
      view === "plan"
        ? (selected?.z_km ?? frame?.plan.level_km ?? state.plane_coordinate_km)
        : view === "xz"
          ? (selected?.y_km ?? 0)
          : (selected?.x_km ?? 0);
    onStateChange({
      ...state,
      evidence_view: view,
      plane_coordinate_km: coordinate,
    });
    setSurface("evidence");
  }

  return (
    <section className="compare-scientific-view compare-supercell-view">
      <nav
        className="compare-supercell-surface-tabs segmented-control"
        aria-label={`${simulation.display_name} scientific surface`}
      >
        <button
          type="button"
          className={surface === "scene" ? "active-control" : ""}
          onClick={() => setSurface("scene")}
        >
          3-D
        </button>
        {(
          [
            ["plan", "Horizontal x-y"],
            ["xz", "Vertical x-z"],
            ["yz", "Vertical y-z"],
          ] as const
        ).map(([view, label]) => (
          <button
            type="button"
            key={view}
            className={
              surface === "evidence" && state.evidence_view === view ? "active-control" : ""
            }
            onClick={() => showEvidence(view)}
          >
            {label}
          </button>
        ))}
      </nav>

      {frame && surface === "scene" && frame.scene ? (
        <div className="compare-supercell-scene">
          <True3DViewer
            resultName={simulation.display_name}
            pointCloud={null}
            fieldLabel={frame.lens_name}
            valueChannelLabel="Native and explicitly derived Supercell layers."
            activeSlice={supercellEvidenceSlice(frame, state.evidence_view)}
            activeSliceLabel={supercellEvidenceLabel(frame, state.evidence_view)}
            showSlicePlane={
              state.evidence_view !== "plan" || frame.plan.selection_z_indices === null
            }
            selectedRegion={
              state.selected_point
                ? {
                    xIndex: frame.selected_point.x_index,
                    yIndex: frame.selected_point.y_index,
                    zIndex: frame.selected_point.z_index,
                  }
                : null
            }
            coordinateSizes={frame.scene.coordinate_sizes}
            selectedTimeLabel={formatSeconds(frame.time_seconds)}
            sceneTimeLabel={formatSeconds(frame.time_seconds)}
            thresholdLabel="Lens-owned fixed thresholds"
            opacity={1}
            pointSize={1}
            status={response.loading ? "Loading frame" : "Scene synchronized"}
            provenanceLabel="Retained native CM1 history; deterministic bounded selection."
            noCloudMessage="No visible storm layers at this saved output."
            windVectors={frame.scene.wind_vectors}
            showWindVectors={state.overlays.wind}
            windMode="total"
            windReferenceMps={frame.scene.wind_reference_m_s}
            windOverlayLabel={`Model-relative wind at z = ${frame.plan.level_km.toFixed(2)} km`}
            windArrowDomainFraction={0.055}
            compactWorkspace
            compactDisplayLabel="3-D layers"
            compactDisplayControlsOpen={state.display_controls_open}
            onCompactDisplayControlsOpenChange={(display_controls_open) =>
              onStateChange({ ...state, display_controls_open })
            }
            stormScene={scene}
            visibleStormLayerKeys={state.visible_layer_ids}
            stormOpacity={state.scene_opacity}
            stormPointSize={state.scene_point_size}
            compactAxisLabels
            selectedPointCoordinates={
              state.selected_point
                ? {
                    x: frame.selected_point.x_km,
                    y: frame.selected_point.y_km,
                    z: frame.selected_point.z_km,
                  }
                : null
            }
            onSelectStormPoint={selectScenePoint}
            cameraPreset={state.camera_preset}
            onCameraPresetChange={(camera_preset) => onStateChange({ ...state, camera_preset })}
            cameraTransform={state.camera_transform}
            onCameraTransformChange={(camera_transform) =>
              onStateChange({ ...state, camera_transform })
            }
            compactDisplayControls={
              <CompareStormLayerControls
                frame={frame}
                state={state}
                onStateChange={onStateChange}
              />
            }
          />
        </div>
      ) : frame && surface === "evidence" ? (
        <div className="compare-supercell-evidence">
          <div className="compare-supercell-plot">
            {state.evidence_view === "plan" ? (
              <StormPlanPlot frame={frame} overlays={overlays} onSelect={select} />
            ) : (
              <StormSectionPlot
                frame={frame}
                section={state.evidence_view === "xz" ? frame.xz_section : frame.yz_section}
                overlays={overlays}
                onSelect={select}
              />
            )}
          </div>
          <StormLegend frame={frame} overlays={overlays} evidenceView={state.evidence_view} />
        </div>
      ) : null}
      <CompareLoadState
        loading={response.loading}
        error={response.error}
        onRetry={response.retry}
      />
    </section>
  );
}

function CompareStormLayerControls({
  frame,
  state,
  onStateChange,
}: {
  frame: StormExaminationFrame;
  state: SupercellsExploreState;
  onStateChange: (state: ExploreWorldState) => void;
}) {
  return (
    <section className="compare-storm-layer-controls" aria-label="3-D storm layers">
      {frame.scene?.layers.map((layer) => (
        <label key={layer.key}>
          <input
            type="checkbox"
            checked={state.visible_layer_ids.includes(layer.key)}
            onChange={(event) =>
              onStateChange({
                ...state,
                visible_layer_ids: event.currentTarget.checked
                  ? [...state.visible_layer_ids, layer.key]
                  : state.visible_layer_ids.filter((key) => key !== layer.key),
              })
            }
          />
          {layer.display_name}
        </label>
      ))}
      {Boolean(frame.scene?.wind_vectors.length) && (
        <label>
          <input
            type="checkbox"
            checked={state.overlays.wind}
            onChange={(event) =>
              onStateChange({
                ...state,
                overlays: { ...state.overlays, wind: event.currentTarget.checked },
              })
            }
          />
          Model-relative wind
        </label>
      )}
    </section>
  );
}

function supercellRequestIndices(
  simulation: CompareSimulationDescriptor,
  state: SupercellsExploreState,
): { x: number | null; y: number | null; z: number | null } {
  const selected = state.selected_point;
  const indices = {
    x: selected
      ? coordinateIndex(selected.x_km, simulation.grid.x_extent_km, simulation.grid.nx)
      : null,
    y:
      selected?.y_km !== null && selected?.y_km !== undefined
        ? coordinateIndex(
            selected.y_km,
            simulation.grid.y_extent_km ?? simulation.grid.x_extent_km,
            simulation.grid.ny,
          )
        : null,
    z: selected
      ? coordinateIndex(selected.z_km, simulation.grid.z_extent_km, simulation.grid.nz)
      : null,
  };
  if (state.evidence_view === "plan") {
    indices.z = coordinateIndex(
      state.plane_coordinate_km,
      simulation.grid.z_extent_km,
      simulation.grid.nz,
    );
  } else if (state.evidence_view === "xz") {
    indices.y = coordinateIndex(
      state.plane_coordinate_km,
      simulation.grid.y_extent_km ?? simulation.grid.x_extent_km,
      simulation.grid.ny,
    );
  } else {
    indices.x = coordinateIndex(
      state.plane_coordinate_km,
      simulation.grid.x_extent_km,
      simulation.grid.nx,
    );
  }
  return indices;
}

function coordinateIndex(coordinate: number, extent: [number, number], count: number): number {
  const spacing = (extent[1] - extent[0]) / count;
  return Math.max(
    0,
    Math.min(count - 1, Math.round((coordinate - extent[0] - spacing / 2) / spacing)),
  );
}

function supercellOverlayState(state: SupercellsExploreState): OverlayState {
  return {
    rotation: state.overlays.rotation,
    updraftHelicity: state.overlays.updraft_helicity,
    reflectivity: state.overlays.reflectivity,
    condensate: state.overlays.condensate,
    rain: state.overlays.rain,
    wind: state.overlays.wind,
    precipitatingCondensate: state.overlays.precipitating_condensate,
    verticalMotion: state.overlays.vertical_motion,
  };
}

function filterSupercellScene(
  source: StormExaminationFrame["scene"],
  categoryCodes: number[],
): StormScenePayload | null {
  if (!source) return null;
  return {
    coordinate_extents_km: source.coordinate_extents_km,
    layers: source.layers.map((layer) =>
      layer.key === "hydrometeor_categories"
        ? {
            ...layer,
            points: layer.points.filter((point) => categoryCodes.includes(point[4])),
          }
        : layer,
    ),
  };
}

function supercellPhysicalPoint(frame: StormExaminationFrame, selection: Selection): ExplorePoint {
  return {
    x_km: supercellCoordinate(frame, "x", selection.xIndex),
    y_km: supercellCoordinate(frame, "y", selection.yIndex),
    z_km: supercellCoordinate(frame, "z", selection.zIndex),
  };
}

function supercellCoordinate(
  frame: StormExaminationFrame,
  axis: "x" | "y" | "z",
  nativeIndex: number,
): number {
  const indices = frame.scene?.coordinate_indices[axis] ?? [];
  const values = frame.scene?.coordinate_values_km[axis] ?? [];
  const position = indices.indexOf(nativeIndex);
  if (position >= 0 && Number.isFinite(values[position])) return values[position];
  if (axis === "x") {
    const planPosition = frame.plan.x_indices.indexOf(nativeIndex);
    return frame.plan.x_km[planPosition] ?? frame.selected_point.x_km;
  }
  if (axis === "y") {
    const planPosition = frame.plan.y_indices.indexOf(nativeIndex);
    return frame.plan.y_km[planPosition] ?? frame.selected_point.y_km;
  }
  return frame.xz_section.z_km[nativeIndex] ?? frame.selected_point.z_km;
}

function supercellSelectedEvidence(frame: StormExaminationFrame): CompareSelectedEvidence {
  const point = frame.selected_point;
  const keys =
    frame.lens_id === "rotating_updraft"
      ? [
          ["vertical_velocity", "Vertical velocity"],
          ["vertical_vorticity", "Vertical vorticity"],
          ["updraft_helicity", "2-5 km AGL updraft helicity"],
          ["total_condensate", "Total condensate"],
          ["reflectivity", "Reflectivity"],
        ]
      : frame.lens_id === "cloud_precipitation"
        ? [
            ["vertical_velocity", "Vertical velocity"],
            ["total_condensate", "Total condensate"],
            ["cloud_liquid", "Cloud liquid"],
            ["rain_water", "Rain water"],
            ["cloud_ice", "Cloud ice"],
            ["snow", "Snow"],
            ["hail_treated_large_ice", "Hail-treated large ice"],
            ["reflectivity", "Reflectivity"],
          ]
        : [
            ["vertical_velocity", "Vertical velocity"],
            ["total_condensate", "Total condensate"],
            ["accumulated_surface_rain", "Accumulated rain"],
            ["model_relative_u", "Model-relative u"],
            ["model_relative_v", "Model-relative v"],
            ["reflectivity", "Reflectivity"],
          ];
  return {
    title: `Native cell at x ${point.x_km.toFixed(1)}, y ${point.y_km.toFixed(
      1,
    )}, z ${point.z_km.toFixed(2)} km`,
    states: point.states,
    metrics: [
      {
        label: "Model time",
        value: formatSeconds(point.model_time_seconds),
        numericValue: point.model_time_seconds,
        units: "s",
      },
      ...keys.map(([key, label]) => {
        const value = point.values[key];
        const units = point.units[key] ?? "";
        return {
          label,
          value: `${formatNumber(value)}${units ? ` ${units}` : ""}`,
          numericValue: value,
          units,
        };
      }),
    ],
  };
}

function supercellEvidenceSlice(
  frame: StormExaminationFrame,
  view: SupercellsExploreState["evidence_view"],
) {
  if (view === "plan") {
    return {
      field: {
        raw_field_name: frame.plan.primary.key,
        display_name: frame.plan.primary.display_name,
        units: frame.plan.primary.units,
      },
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

function supercellEvidenceLabel(
  frame: StormExaminationFrame,
  view: SupercellsExploreState["evidence_view"],
): string {
  if (view === "plan") {
    return frame.plan.selection_z_indices
      ? `${frame.plan.title} · column-derived at each cell's condensate maximum`
      : `${frame.plan.title} · z = ${frame.plan.level_km.toFixed(2)} km`;
  }
  return view === "xz" ? frame.xz_section.title : frame.yz_section.title;
}

function CompareLoadState({
  loading,
  error,
  onRetry,
}: {
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  if (error) {
    return (
      <section className="compare-side-error" role="alert">
        <h4>This side could not load</h4>
        <p>{error}</p>
        <button type="button" onClick={onRetry}>
          Retry this side
        </button>
      </section>
    );
  }
  if (loading) {
    return (
      <div className="compare-side-loading" role="status">
        Loading saved output...
      </div>
    );
  }
  return null;
}

function useBoundedJson<T>(
  side: CompareSide,
  url: string | null,
  onFrameState: SideVisualProps["onFrameState"],
  onPerformance: SideVisualProps["onPerformance"],
) {
  const cache = useRef(new Map<string, { data: T; bytes: number }>());
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(url));
  const [retryNonce, setRetryNonce] = useState(0);

  useEffect(() => {
    if (!url) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const cached = cache.current.get(url);
    if (cached) {
      cache.current.delete(url);
      cache.current.set(url, cached);
      setData(cached.data);
      setError(null);
      setLoading(false);
      onFrameState(side, "ready");
      onPerformance({
        side,
        key: url,
        request_ms: 0,
        payload_bytes: cached.bytes,
        cache_hit: true,
      });
      return;
    }
    const controller = new AbortController();
    const started = window.performance.now();
    setLoading(true);
    setError(null);
    onFrameState(side, "loading");
    void fetch(url, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(await responseMessage(response, "Saved output could not be loaded."));
        }
        const text = await response.text();
        if (controller.signal.aborted) return;
        const parsed = JSON.parse(text) as T;
        cache.current.set(url, { data: parsed, bytes: text.length });
        while (cache.current.size > 6) {
          const oldest = cache.current.keys().next().value;
          if (typeof oldest !== "string") break;
          cache.current.delete(oldest);
        }
        setData(parsed);
        setError(null);
        onFrameState(side, "ready");
        onPerformance({
          side,
          key: url,
          request_ms: window.performance.now() - started,
          payload_bytes: text.length,
          cache_hit: false,
        });
      })
      .catch((caught: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(caught instanceof Error ? caught.message : "Saved output could not be loaded.");
        onFrameState(side, "error");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [onFrameState, onPerformance, retryNonce, side, url]);

  return {
    data,
    error,
    loading,
    retry: () => setRetryNonce((value) => value + 1),
  };
}

type TradePointCloud = {
  field: {
    raw_field_name: string;
    display_name: string;
    units: string | null;
  };
  selection: {
    field: string;
    time_index: number;
    time_seconds: number | null;
    threshold: number;
    max_points: number;
  };
  coordinate_units: Record<string, string | null>;
  coordinate_extents: Record<string, { min: number; max: number; units: string | null }>;
  points: Array<[number, number, number, number]>;
  stats: {
    source_count: number;
    returned_count: number;
    field_min_value: number | null;
    field_max_value: number | null;
    field_mean_value: number | null;
    field_finite_count: number;
    field_non_finite_count: number;
    min_value: number | null;
    max_value: number | null;
    active_z_min: number | null;
    active_z_max: number | null;
    downsampled: boolean;
    downsample_stride: number;
  };
  provenance: {
    source_model: string;
    run_id: string;
    result_id?: string;
    scenario_id: string;
    processing_method: string;
    rendering_method: string;
    provenance_label: string;
  };
  caveats: string[];
};

type TerrainField = MountainWaveFrame["field"];
type TerrainViewport = MountainWaveFrame["viewport"];
type TerrainLens = MountainWaveFrame["lens"];

type MountainCompareFrame = {
  schema_version: "mountain_waves_compare_v1";
  run_id: string;
  case_label: string;
  time_index: number;
  time_seconds: number;
  times_seconds: number[];
  dry_case: boolean;
  field: TerrainField;
  field_options: MountainWaveFrame["field_options"];
  values: number[][];
  native_x_indices: number[];
  native_z_indices: number[];
  x_center_km: number[];
  terrain_km: number[];
  scalar_height_km: number[][];
  pointer_context: {
    horizontal_wind_m_s: number[][];
    vertical_velocity_m_s: number[][];
    potential_temperature_k: number[][];
    theta_perturbation_k: number[][];
    cloud_liquid_g_kg: number[][] | null;
    relative_humidity_percent: number[][] | null;
  };
  cloud_overlay: {
    values: number[][];
    threshold_g_kg: number;
    maximum_g_kg: number;
  } | null;
  viewport: TerrainViewport;
  lens: TerrainLens;
  scale: TerrainScale;
  source_shape: [number, number];
  display_shape: [number, number];
  performance: {
    extraction_ms: number;
    serialization_ms: number;
    serialized_payload_bytes: number;
  };
  caveats: string[];
};

function expandMountainCompareFrame(compact: MountainCompareFrame): MountainWaveFrame {
  const xCentersM = compact.x_center_km.map((value) => value * 1_000);
  const terrainM = compact.terrain_km.map((value) => value * 1_000);
  const scalarHeightM = compact.scalar_height_km.map((row) => row.map((value) => value * 1_000));
  const xEdgesM = coordinateEdges(xCentersM);
  const fullHeightM = fullLevelHeights(scalarHeightM, terrainM);
  return {
    schema_version: "mountain_waves_explore_v1",
    run_id: compact.run_id,
    case_label: compact.case_label,
    time_index: compact.time_index,
    time_seconds: compact.time_seconds,
    times_seconds: compact.times_seconds,
    dry_case: compact.dry_case,
    field: compact.field,
    values: compact.values,
    field_options: compact.field_options,
    overlay: compact.cloud_overlay
      ? {
          values: compact.cloud_overlay.values,
          threshold: compact.cloud_overlay.threshold_g_kg,
          maximum: compact.cloud_overlay.maximum_g_kg,
        }
      : null,
    pointer_context: compact.pointer_context,
    viewport: compact.viewport,
    lens: compact.lens,
    geometry: {
      x_center_m: xCentersM,
      x_edge_m: xEdgesM,
      terrain_m: terrainM,
      scalar_height_m: scalarHeightM,
      full_height_m: fullHeightM,
      nominal_scalar_height_m: scalarHeightM.map((row) => row[0] ?? 0),
      nominal_full_height_m: fullHeightM.map((row) => row[0] ?? 0),
      active_top_m: compact.viewport.full.z_maximum_m,
      singleton_y_m: 0,
    },
    scale: compact.scale,
    caveats: compact.caveats,
    provenance: {
      source_history_file: "retained native history",
      topology: "native_2d_x_z_singleton_y",
      interpolation: "none",
      display_binning: "ordered native-cell display subset",
      physical_height_source: "native terrain-following scalar height",
    },
    active_top_evidence: {
      transform_top_source: "Compare descriptor",
      all_sources_agree: true,
      inactive_namelist_ztop_m: compact.viewport.full.z_maximum_m,
    },
  };
}

function fullLevelHeights(scalar: number[][], terrain: number[]): number[][] {
  if (!scalar.length) return [terrain];
  const columns = scalar[0]?.length ?? 0;
  const rows: number[][] = [terrain.slice()];
  for (let z = 1; z < scalar.length; z += 1) {
    rows.push(Array.from({ length: columns }, (_, x) => (scalar[z - 1][x] + scalar[z][x]) / 2));
  }
  rows.push(
    Array.from({ length: columns }, (_, x) => {
      const last = scalar.at(-1)?.[x] ?? terrain[x] ?? 0;
      const previous = scalar.at(-2)?.[x] ?? terrain[x] ?? 0;
      return last + Math.max(1, (last - previous) / 2);
    }),
  );
  return rows;
}

function coordinateEdges(values: number[]): number[] {
  if (!values.length) return [0, 1];
  if (values.length === 1) return [values[0] - 0.5, values[0] + 0.5];
  const edges = [values[0] - (values[1] - values[0]) / 2];
  for (let index = 1; index < values.length; index += 1) {
    edges.push((values[index - 1] + values[index]) / 2);
  }
  edges.push(values.at(-1)! + (values.at(-1)! - values.at(-2)!) / 2);
  return edges;
}

function coordinateValues(frame: UpdraftLensFrame, dimension: string): number[] {
  if (dimension === "x") return frame.x_values_km;
  if (dimension === "y") return frame.y_values_km;
  return frame.z_values_km;
}

function nativePlaneIndex(frame: UpdraftLensFrame | null, positionIndex: number): number {
  if (!frame) return positionIndex;
  return nativePlaneIndexForDimension(frame, frame.plane_dimension, positionIndex);
}

function nativePlaneIndexForDimension(
  frame: UpdraftLensFrame,
  dimension: string,
  positionIndex: number,
): number {
  const indices =
    dimension === "x" ? frame.x_indices : dimension === "y" ? frame.y_indices : frame.z_indices;
  return indices[positionIndex] ?? positionIndex;
}

function planePositionLabel(frame: UpdraftLensFrame): string {
  const axis = frame.plane_dimension;
  return `${axis} = ${formatNumber(frame.plane_coordinate)} ${frame.plane_units ?? "km"}`;
}

function tradeSelection(
  frame: UpdraftLensFrame,
  point: ExplorePoint | null,
): UpdraftLensPointSelection | null {
  if (!point) return null;
  return {
    xIndex: nearestValueIndex(frame.x_values_km, point.x_km),
    yIndex: nearestValueIndex(frame.y_values_km, point.y_km ?? 0),
    zIndex: nearestValueIndex(frame.z_values_km, point.z_km),
  };
}

function tradePhysicalPoint(
  frame: UpdraftLensFrame,
  selection: UpdraftLensPointSelection,
): ExplorePoint {
  return {
    x_km: frame.x_values_km[selection.xIndex] ?? 0,
    y_km: frame.y_values_km[selection.yIndex] ?? null,
    z_km: frame.z_values_km[selection.zIndex] ?? 0,
  };
}

function tradeSelectedEvidence(
  frame: UpdraftLensFrame,
  point: ExplorePoint | null,
): CompareSelectedEvidence | null {
  const selection = tradeSelection(frame, point);
  if (!selection || !point) return null;
  const rowIndex = lensDimensionIndex(selection, frame.dimension_order[0]);
  const columnIndex = lensDimensionIndex(selection, frame.dimension_order[1]);
  const verticalVelocity = frame.w_values_m_s[rowIndex]?.[columnIndex] ?? null;
  const cloudy = frame.cloud_mask[rowIndex]?.[columnIndex] ?? false;
  return {
    title: `x ${formatNumber(point.x_km)} · ${
      point.y_km === null ? "" : `y ${formatNumber(point.y_km)} · `
    }z ${formatNumber(point.z_km)} km`,
    states: [motionState(verticalVelocity), cloudy ? "Cloudy" : "Clear"],
    metrics: [
      {
        label: "Model time",
        value: formatSeconds(frame.time_seconds),
        numericValue: frame.time_seconds ?? undefined,
        units: "s",
      },
      {
        label: "Vertical velocity",
        value: `${formatNumber(verticalVelocity)} m/s`,
        numericValue: verticalVelocity ?? undefined,
        units: "m/s",
      },
      {
        label: "Cloud threshold",
        value: `${cloudy ? "At or above" : "Below"} ${formatNumber(
          frame.cloud_threshold_kg_kg * 1_000,
        )} g/kg`,
      },
    ],
  };
}

function mountainSelectedEvidence(
  frame: MountainWaveFrame,
  point: { xIndex: number; zIndex: number } | null,
): CompareSelectedEvidence | null {
  if (!point) return null;
  const xKm = (frame.geometry.x_center_m[point.xIndex] ?? 0) / 1_000;
  const zKm = (frame.geometry.scalar_height_m[point.zIndex]?.[point.xIndex] ?? 0) / 1_000;
  const verticalVelocity =
    frame.pointer_context.vertical_velocity_m_s[point.zIndex]?.[point.xIndex] ?? null;
  const thetaPerturbation =
    frame.pointer_context.theta_perturbation_k[point.zIndex]?.[point.xIndex] ?? null;
  const cloud = frame.pointer_context.cloud_liquid_g_kg?.[point.zIndex]?.[point.xIndex] ?? null;
  const relativeHumidity =
    frame.pointer_context.relative_humidity_percent?.[point.zIndex]?.[point.xIndex] ?? null;
  const states = [motionState(verticalVelocity)];
  if (cloud !== null) states.push(cloud >= 0.001 ? "Cloudy" : "Clear");
  if (relativeHumidity !== null) states.push(relativeHumidity >= 100 ? "Saturated" : "Unsaturated");
  return {
    title: `x ${formatNumber(xKm)} km · z ${formatNumber(zKm)} km`,
    states,
    metrics: [
      {
        label: "Model time",
        value: formatSeconds(frame.time_seconds),
        numericValue: frame.time_seconds,
        units: "s",
      },
      {
        label: "Vertical velocity",
        value: `${formatNumber(verticalVelocity)} m/s`,
        numericValue: verticalVelocity ?? undefined,
        units: "m/s",
      },
      {
        label: "Potential-temperature perturbation",
        value: `${formatNumber(thetaPerturbation)} K`,
        numericValue: thetaPerturbation ?? undefined,
        units: "K",
      },
      ...(cloud === null
        ? []
        : [
            {
              label: "Cloud liquid water",
              value: `${formatNumber(cloud)} g/kg`,
              numericValue: cloud,
              units: "g/kg",
            },
          ]),
      ...(relativeHumidity === null
        ? []
        : [
            {
              label: "Relative humidity",
              value: `${formatNumber(relativeHumidity)}%`,
              numericValue: relativeHumidity,
              units: "%",
            },
          ]),
    ],
  };
}

function lensDimensionIndex(
  selection: UpdraftLensPointSelection,
  dimension: string | undefined,
): number {
  if (dimension === "x") return selection.xIndex;
  if (dimension === "y") return selection.yIndex;
  return selection.zIndex;
}

function motionState(value: number | null): string {
  if (value === null) return "Motion unavailable";
  if (value > 0.1) return "Rising";
  if (value < -0.1) return "Descending";
  return "Near neutral";
}

function nearestMountainSelection(
  frame: MountainWaveFrame,
  point: ExplorePoint | null,
): { xIndex: number; zIndex: number } | null {
  if (!point) return null;
  const xIndex = nearestValueIndex(
    frame.geometry.x_center_m.map((value) => value / 1_000),
    point.x_km,
  );
  return {
    xIndex,
    zIndex: nearestValueIndex(
      frame.geometry.scalar_height_m.map((row) => (row[xIndex] ?? 0) / 1_000),
      point.z_km,
    ),
  };
}

function mountainPhysicalPoint(
  frame: MountainWaveFrame,
  point: { xIndex: number; zIndex: number },
): ExplorePoint {
  return {
    x_km: (frame.geometry.x_center_m[point.xIndex] ?? 0) / 1_000,
    y_km: null,
    z_km: (frame.geometry.scalar_height_m[point.zIndex]?.[point.xIndex] ?? 0) / 1_000,
  };
}

function nearestValueIndex(values: number[], target: number): number {
  let selected = 0;
  let distance = Number.POSITIVE_INFINITY;
  values.forEach((value, index) => {
    const candidate = Math.abs(value - target);
    if (candidate < distance) {
      selected = index;
      distance = candidate;
    }
  });
  return selected;
}

function formatSeconds(value: number | null): string {
  return value === null ? "Time unavailable" : `${Math.round(value).toLocaleString()} s`;
}

function formatNumber(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "unavailable";
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  if (Math.abs(value) > 0 && Math.abs(value) < 0.001) return value.toExponential(2);
  if (Math.abs(value) > 0 && Math.abs(value) < 0.01) return value.toFixed(3);
  return value.toFixed(2);
}

async function responseMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : fallback;
  } catch {
    return fallback;
  }
}

export function CompareControlGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="compare-control-group">
      <span>{label}</span>
      {children}
    </div>
  );
}

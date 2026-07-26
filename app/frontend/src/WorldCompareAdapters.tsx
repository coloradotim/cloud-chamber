import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  type ExplorePoint,
  type ExploreWorldState,
  type MountainWavesExploreState,
  type TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import {
  type MountainWaveFrame,
  MountainWavesLegend,
  MountainWavesTerrainPlot,
  type MountainWavesViewMode,
} from "./MountainWavesExplore";
import { NativeSlicePositionControl } from "./NativeSlicePositionControl";
import { True3DViewer } from "./True3DViewer";
import {
  type UpdraftLensFrame,
  type UpdraftLensPointSelection,
  UpdraftLensSlice,
} from "./UpdraftLensSlice";
import { timeIndexForSeconds } from "./WorldCompare.logic";
import {
  isMountainState,
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
    ? Math.max(0, planeValues.findIndex((value) => value === frame.plane_coordinate))
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
          status={cloud.error ? "Cloud field unavailable" : cloud.loading ? "Loading cloud field" : "Cloud field ready"}
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
            <div className="segmented-control" aria-label={`${simulation.display_name} slice plane`}>
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
  const response = useBoundedJson<MountainCompareFrame>(
    side,
    url,
    onFrameState,
    onPerformance,
  );
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
              commonMountainScale
                ? "Fixed across both Simulations"
                : "Fixed across this Simulation"
            }
          />
        </div>
      )}
      <CompareLoadState loading={response.loading} error={response.error} onRetry={response.retry} />
    </section>
  );
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
  const scalarHeightM = compact.scalar_height_km.map((row) =>
    row.map((value) => value * 1_000),
  );
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
    rows.push(
      Array.from({ length: columns }, (_, x) => (scalar[z - 1][x] + scalar[z][x]) / 2),
    );
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
  const cloud =
    frame.pointer_context.cloud_liquid_g_kg?.[point.zIndex]?.[point.xIndex] ?? null;
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

export function CompareControlGroup({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="compare-control-group">
      <span>{label}</span>
      {children}
    </div>
  );
}

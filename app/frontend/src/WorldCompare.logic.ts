import type { CameraPreset, CameraTransform } from "./True3DViewer";
import { SUPERCELLS_CURATED_VIEWS } from "./exploreCuratedDefaults";
import type {
  ExplorePoint,
  ExploreWorldState,
  MountainWavesExploreState,
  SupercellsExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import {
  isMountainState,
  isSupercellsState,
  isTradeState,
  type CompareMappingResult,
  type CompareSimulationDescriptor,
  type CompareWorldId,
  type WorldCompareAdapter,
  type WorldCompareDescriptor,
} from "./WorldCompare.types";

const TRADE_VIEW_LABELS = {
  updraft_lens: "Updraft Lens",
  field: "Cloud field",
} as const;

const MOUNTAIN_VIEW_LABELS = {
  wave_structure: "Wave Structure Lens",
  wave_cloud: "Wave Cloud Lens",
  field: "Field",
} as const;

const SUPERCELLS_VIEW_LABELS = {
  rotating_updraft: "Rotating Updraft",
  cloud_precipitation: "Cloud and Precipitation",
  low_level_interactions: "Low-Level Interactions",
} as const;

export const WORLD_COMPARE_ADAPTERS: Record<CompareWorldId, WorldCompareAdapter> = {
  trade_cumulus: {
    worldId: "trade_cumulus",
    viewLabel: "View",
    viewOptions: (simulation) =>
      simulation.available_view_ids.map((id) => ({
        id,
        label: TRADE_VIEW_LABELS[id as keyof typeof TRADE_VIEW_LABELS] ?? id,
      })),
    viewId: (state) => (isTradeState(state) ? state.view_id : ""),
    setView: (state, viewId) => {
      if (!isTradeState(state) || (viewId !== "field" && viewId !== "updraft_lens")) return state;
      return viewId === "updraft_lens"
        ? {
            ...state,
            view_id: "updraft_lens",
            scene_field_id: "ql",
            slice_field_id: "w",
            fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
            show_cloud_boundary: true,
            show_horizontal_wind: true,
          }
        : {
            ...state,
            view_id: "field",
            scene_field_id: "ql",
            slice_field_id: "ql",
            fixed_scale_id: null,
          };
    },
    fieldId: (state) => (isTradeState(state) ? state.slice_field_id : null),
    setField: (state, fieldId) =>
      isTradeState(state) ? { ...state, scene_field_id: fieldId, slice_field_id: fieldId } : state,
    modelTime: (state) => state.model_time_seconds,
    setModelTime: (state, seconds) => ({ ...state, model_time_seconds: seconds }),
    selectedPoint: (state) => state.selected_point,
    setSelectedPoint: (state, point) => ({ ...state, selected_point: point }),
    cameraPreset: (state) => (isTradeState(state) ? state.camera_preset : null),
    setCamera: (state, preset, transform) =>
      isTradeState(state)
        ? { ...state, camera_preset: preset, camera_transform: transform }
        : state,
    cameraTransform: (state) => (isTradeState(state) ? state.camera_transform : null),
  },
  mountain_waves: {
    worldId: "mountain_waves",
    viewLabel: "View",
    viewOptions: (simulation) =>
      simulation.available_view_ids.map((id) => ({
        id,
        label: MOUNTAIN_VIEW_LABELS[id as keyof typeof MOUNTAIN_VIEW_LABELS] ?? id,
      })),
    viewId: (state) => (isMountainState(state) ? state.view_id : ""),
    setView: (state, viewId) => {
      if (
        !isMountainState(state) ||
        (viewId !== "field" && viewId !== "wave_structure" && viewId !== "wave_cloud")
      ) {
        return state;
      }
      if (viewId === "wave_cloud") {
        return {
          ...state,
          view_id: "wave_cloud",
          field_id: "w",
          fixed_scale_id: "mountain_waves_vertical_velocity_v1",
          overlays: {
            cloud_points: true,
            cloud_boundary: true,
            saturation_contour: true,
            horizontal_wind: true,
            potential_temperature_contours: false,
          },
        };
      }
      if (viewId === "wave_structure") {
        return {
          ...state,
          view_id: "wave_structure",
          field_id: "w",
          fixed_scale_id: "mountain_waves_vertical_velocity_v1",
          overlays: {
            cloud_points: false,
            cloud_boundary: false,
            saturation_contour: false,
            horizontal_wind: true,
            potential_temperature_contours: true,
          },
        };
      }
      return {
        ...state,
        view_id: "field",
        overlays: {
          cloud_points: false,
          cloud_boundary: false,
          saturation_contour: false,
          horizontal_wind: false,
          potential_temperature_contours: false,
        },
      };
    },
    fieldId: (state) => (isMountainState(state) ? state.field_id : null),
    setField: (state, fieldId) => {
      if (
        !isMountainState(state) ||
        !["w", "theta_perturbation", "cloud_liquid", "relative_humidity"].includes(fieldId)
      ) {
        return state;
      }
      return {
        ...state,
        field_id: fieldId as typeof state.field_id,
        fixed_scale_id: mountainScaleId(fieldId),
      };
    },
    modelTime: (state) => state.model_time_seconds,
    setModelTime: (state, seconds) => ({ ...state, model_time_seconds: seconds }),
    selectedPoint: (state) => state.selected_point,
    setSelectedPoint: (state, point) => ({ ...state, selected_point: point }),
    cameraPreset: () => null,
    setCamera: (state) => state,
    cameraTransform: () => null,
  },
  supercells: {
    worldId: "supercells",
    viewLabel: "Lens",
    viewOptions: (simulation) =>
      simulation.available_view_ids.map((id) => ({
        id,
        label: SUPERCELLS_VIEW_LABELS[id as keyof typeof SUPERCELLS_VIEW_LABELS] ?? id,
      })),
    viewId: (state) => (isSupercellsState(state) ? state.lens_id : ""),
    setView: (state, viewId) => {
      if (
        !isSupercellsState(state) ||
        !["rotating_updraft", "cloud_precipitation", "low_level_interactions"].includes(viewId)
      ) {
        return state;
      }
      const lensId = viewId as typeof state.lens_id;
      const curated = SUPERCELLS_CURATED_VIEWS[lensId];
      return {
        ...state,
        lens_id: lensId,
        evidence_view: curated.evidenceOrientation,
        plane_coordinate_km: curated.plane.coordinateKm,
        visible_layer_ids: [...curated.visibleLayerIds],
        fixed_scale_ids: [...curated.fixedScaleIds],
        overlays: {
          rotation: curated.overlays.rotation,
          updraft_helicity: curated.overlays.updraftHelicity,
          reflectivity: curated.overlays.reflectivity,
          condensate: curated.overlays.condensate,
          rain: curated.overlays.rain,
          wind: curated.overlays.wind,
          precipitating_condensate: curated.overlays.precipitatingCondensate,
          vertical_motion: curated.overlays.verticalMotion,
        },
        hydrometeor_category_codes: [...curated.hydrometeorCategoryCodes],
        camera_preset: curated.cameraPreset,
        camera_transform: curated.cameraTransform,
        scene_opacity: curated.sceneOpacity,
        scene_point_size: curated.scenePointSize,
        selected_point: null,
        selected_evidence_visible: false,
      };
    },
    fieldId: () => null,
    setField: (state) => state,
    modelTime: (state) => state.model_time_seconds,
    setModelTime: (state, seconds) => ({ ...state, model_time_seconds: seconds }),
    selectedPoint: (state) => state.selected_point,
    setSelectedPoint: (state, point) =>
      isSupercellsState(state) ? setSupercellSelectedPoint(state, point) : state,
    cameraPreset: (state) => (isSupercellsState(state) ? state.camera_preset : null),
    setCamera: (state, preset, transform) =>
      isSupercellsState(state)
        ? { ...state, camera_preset: preset, camera_transform: transform }
        : state,
    cameraTransform: (state) => (isSupercellsState(state) ? state.camera_transform : null),
  },
};

export function setSupercellSelectedPoint(
  state: SupercellsExploreState,
  point: ExplorePoint | null,
): SupercellsExploreState {
  return {
    ...state,
    selected_point: point,
    selected_evidence_visible: point !== null,
    plane_coordinate_km:
      point === null
        ? state.plane_coordinate_km
        : state.evidence_view === "plan"
          ? point.z_km
          : state.evidence_view === "xz"
            ? (point.y_km ?? state.plane_coordinate_km)
            : point.x_km,
  };
}

export function nearestCompareTime(
  descriptor: CompareSimulationDescriptor,
  requestedSeconds: number,
  toleranceSeconds: number,
): CompareMappingResult<number> | null {
  const values = descriptor.time.times_seconds;
  if (!values.length || !Number.isFinite(requestedSeconds)) return null;
  let closest = values[0];
  let distance = Math.abs(closest - requestedSeconds);
  values.forEach((value) => {
    const candidateDistance = Math.abs(value - requestedSeconds);
    if (candidateDistance < distance) {
      closest = value;
      distance = candidateDistance;
    }
  });
  if (distance > toleranceSeconds + Number.EPSILON) return null;
  const exact = distance <= Number.EPSILON;
  return {
    value: closest,
    exact,
    message: exact
      ? null
      : `Requested ${formatSeconds(requestedSeconds)}; showing nearest saved output at ${formatSeconds(closest)}.`,
  };
}

export type SavedStateRestoration = {
  state: ExploreWorldState;
  status: "healthy" | "partially_restorable" | "unavailable";
  messages: string[];
};

export function reconcileSavedCompareState(
  savedState: ExploreWorldState,
  simulation: CompareSimulationDescriptor,
  timeToleranceSeconds: number,
): SavedStateRestoration {
  if (savedState.world_id !== simulation.world_id) {
    return {
      state: simulation.initial_state,
      status: "unavailable",
      messages: ["The saved state belongs to a different Cloud World."],
    };
  }
  const messages: string[] = [];
  let state = structuredClone(savedState);
  const nearest = nearestCompareTime(
    simulation,
    savedState.model_time_seconds,
    timeToleranceSeconds,
  );
  if (nearest) {
    state = { ...state, model_time_seconds: nearest.value };
    if (!nearest.exact && nearest.message) messages.push(nearest.message);
  } else {
    const values = simulation.time.times_seconds;
    if (!values.length) {
      return {
        state: simulation.initial_state,
        status: "unavailable",
        messages: ["The Simulation has no retained modeled times."],
      };
    }
    const closest = values.reduce((best, value) =>
      Math.abs(value - savedState.model_time_seconds) <
      Math.abs(best - savedState.model_time_seconds)
        ? value
        : best,
    );
    state = { ...state, model_time_seconds: closest };
    messages.push(`Saved modeled time is no longer retained; showing ${formatSeconds(closest)}.`);
  }

  const adapter = WORLD_COMPARE_ADAPTERS[simulation.world_id];
  if (!simulation.available_view_ids.includes(adapter.viewId(state))) {
    state = {
      ...simulation.initial_state,
      model_time_seconds: state.model_time_seconds,
    } as ExploreWorldState;
    messages.push("The saved view is unavailable; the current default view is shown.");
  }

  const fieldId = adapter.fieldId(state);
  if (fieldId && !simulation.available_field_ids.includes(fieldId)) {
    state = adapter.setField(state, simulation.available_field_ids[0] ?? fieldId);
    messages.push("The saved field is unavailable; a compatible field is shown.");
  }

  if (isTradeState(state)) {
    state = reconcileTradeState(state, simulation, messages);
  } else if (isMountainState(state)) {
    state = reconcileMountainState(state, simulation, messages);
  } else if (isSupercellsState(state)) {
    state = reconcileSupercellsState(state, simulation, messages);
  }

  const cameraTransform = adapter.cameraTransform(state);
  const cameraPreset = adapter.cameraPreset(state);
  if (
    cameraTransform &&
    cameraPreset &&
    (simulation.camera_mapping !== "normalized_3d" ||
      !cameraTargetWithinGrid(cameraTransform.target, simulation))
  ) {
    state = adapter.setCamera(state, cameraPreset, null);
    messages.push("The saved camera target is outside the current domain and was reset.");
  }

  const selection = state.selected_point;
  if (selection && !pointWithinGrid(selection, simulation)) {
    state = adapter.setSelectedPoint(state, null);
    messages.push("The saved selected point is outside the current domain and was cleared.");
  }
  return {
    state,
    status: messages.length ? "partially_restorable" : "healthy",
    messages,
  };
}

function cameraTargetWithinGrid(
  target: CameraTransform["target"],
  simulation: CompareSimulationDescriptor,
): boolean {
  return (
    within(target[0], simulation.grid.x_extent_km) &&
    within(target[2], simulation.grid.z_extent_km) &&
    (simulation.grid.y_extent_km === null || within(target[1], simulation.grid.y_extent_km))
  );
}

function reconcileTradeState(
  state: TradeCumulusExploreState,
  simulation: CompareSimulationDescriptor,
  messages: string[],
): TradeCumulusExploreState {
  let next = state;
  if (next.fixed_scale_id && !simulation.fixed_scale_ids.includes(next.fixed_scale_id)) {
    next = { ...next, fixed_scale_id: null };
    messages.push("The saved fixed scale is unavailable; the current field scale is used.");
  }
  const extent =
    next.active_slice_plane === "horizontal"
      ? simulation.grid.z_extent_km
      : next.active_slice_plane === "vertical_x"
        ? simulation.grid.y_extent_km
        : simulation.grid.x_extent_km;
  const count =
    next.active_slice_plane === "horizontal"
      ? simulation.grid.nz
      : next.active_slice_plane === "vertical_x"
        ? simulation.grid.ny
        : simulation.grid.nx;
  if (extent) {
    const coordinate = clamp(next.slice_coordinate_km, extent[0], extent[1]);
    const nativeIndex = coordinateIndex(coordinate, extent, count);
    if (coordinate !== next.slice_coordinate_km || nativeIndex !== next.slice_native_index) {
      next = {
        ...next,
        slice_coordinate_km: coordinate,
        slice_native_index: nativeIndex,
      };
      messages.push("The saved slice was mapped to the current physical domain.");
    }
  }
  return next;
}

function reconcileMountainState(
  state: MountainWavesExploreState,
  simulation: CompareSimulationDescriptor,
  messages: string[],
): MountainWavesExploreState {
  if (simulation.fixed_scale_ids.includes(state.fixed_scale_id)) return state;
  const fallback =
    simulation.fixed_scale_ids.find((scale) => scale.includes(state.field_id)) ??
    simulation.fixed_scale_ids[0] ??
    state.fixed_scale_id;
  messages.push("The saved fixed scale is unavailable; the current compatible scale is used.");
  return { ...state, fixed_scale_id: fallback };
}

function reconcileSupercellsState(
  state: SupercellsExploreState,
  simulation: CompareSimulationDescriptor,
  messages: string[],
): SupercellsExploreState {
  const fixedScaleIds = state.fixed_scale_ids.filter((scale) =>
    simulation.fixed_scale_ids.includes(scale),
  );
  let next =
    fixedScaleIds.length === state.fixed_scale_ids.length
      ? state
      : { ...state, fixed_scale_ids: fixedScaleIds };
  if (fixedScaleIds.length !== state.fixed_scale_ids.length) {
    messages.push("Unavailable fixed scales were removed from the restored Lens.");
  }
  const extent =
    next.evidence_view === "plan"
      ? simulation.grid.z_extent_km
      : next.evidence_view === "xz"
        ? simulation.grid.y_extent_km
        : simulation.grid.x_extent_km;
  if (extent) {
    const coordinate = clamp(next.plane_coordinate_km, extent[0], extent[1]);
    if (coordinate !== next.plane_coordinate_km) {
      next = { ...next, plane_coordinate_km: coordinate };
      messages.push("The saved evidence plane was clamped to the current physical domain.");
    }
  }
  return next;
}

function pointWithinGrid(point: ExplorePoint, simulation: CompareSimulationDescriptor): boolean {
  return (
    within(point.x_km, simulation.grid.x_extent_km) &&
    within(point.z_km, simulation.grid.z_extent_km) &&
    (simulation.grid.y_extent_km === null ||
      point.y_km === null ||
      within(point.y_km, simulation.grid.y_extent_km))
  );
}

function within(value: number, extent: [number, number]): boolean {
  return value >= extent[0] && value <= extent[1];
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function coordinateIndex(coordinate: number, extent: [number, number], count: number): number {
  if (count <= 1 || extent[1] === extent[0]) return 0;
  return Math.round(((coordinate - extent[0]) / (extent[1] - extent[0])) * (count - 1));
}

export function timeIndexForSeconds(
  descriptor: CompareSimulationDescriptor,
  seconds: number,
): number {
  const exactIndex = descriptor.time.times_seconds.indexOf(seconds);
  if (exactIndex >= 0) return exactIndex;
  const nearest = nearestCompareTime(descriptor, seconds, Number.POSITIVE_INFINITY);
  return nearest ? descriptor.time.times_seconds.indexOf(nearest.value) : 0;
}

export function mapCamera(
  preset: CameraPreset,
  transform: CameraTransform | null,
  source: CompareSimulationDescriptor,
  target: CompareSimulationDescriptor,
): { preset: CameraPreset; transform: CameraTransform | null; message: string | null } | null {
  if (source.camera_mapping !== "normalized_3d" || target.camera_mapping !== "normalized_3d") {
    return null;
  }
  if (!transform) return { preset, transform: null, message: null };
  const normalized = normalizeCameraTransform(transform, source.grid);
  return {
    preset,
    transform: denormalizeCameraTransform(normalized, target.grid),
    message: "Camera mapped by normalized domain position; physical coordinates differ.",
  };
}

export function validateWorldCompareDescriptor(value: unknown): WorldCompareDescriptor {
  if (
    !isRecord(value) ||
    value.schema_version !== "world_compare_v1" ||
    !Array.isArray(value.simulations) ||
    typeof value.world_id !== "string"
  ) {
    throw new Error("World Compare metadata does not match the required contract.");
  }
  return value as WorldCompareDescriptor;
}

export function worldSlug(worldId: CompareWorldId): string {
  return worldId.replaceAll("_", "-");
}

function mountainScaleId(fieldId: string): string {
  const values: Record<string, string> = {
    w: "mountain_waves_vertical_velocity_v1",
    theta_perturbation: "mountain_waves_theta_perturbation_v1",
    cloud_liquid: "mountain_waves_cloud_liquid_v1",
    relative_humidity: "mountain_waves_relative_humidity_v1",
  };
  return values[fieldId] ?? "mountain_waves_vertical_velocity_v1";
}

function normalizeCameraTransform(
  transform: CameraTransform,
  grid: CompareSimulationDescriptor["grid"],
): CameraTransform {
  return {
    position: normalizePoint(transform.position, grid),
    target: normalizePoint(transform.target, grid),
    up: transform.up,
  };
}

function denormalizeCameraTransform(
  transform: CameraTransform,
  grid: CompareSimulationDescriptor["grid"],
): CameraTransform {
  return {
    position: denormalizePoint(transform.position, grid),
    target: denormalizePoint(transform.target, grid),
    up: transform.up,
  };
}

function normalizePoint(
  point: [number, number, number],
  grid: CompareSimulationDescriptor["grid"],
): [number, number, number] {
  return [
    normalizeAxis(point[0], grid.x_extent_km),
    normalizeAxis(point[1], grid.z_extent_km),
    normalizeAxis(point[2], grid.y_extent_km ?? grid.x_extent_km),
  ];
}

function denormalizePoint(
  point: [number, number, number],
  grid: CompareSimulationDescriptor["grid"],
): [number, number, number] {
  return [
    denormalizeAxis(point[0], grid.x_extent_km),
    denormalizeAxis(point[1], grid.z_extent_km),
    denormalizeAxis(point[2], grid.y_extent_km ?? grid.x_extent_km),
  ];
}

function normalizeAxis(value: number, extent: [number, number]): number {
  const span = extent[1] - extent[0];
  return span ? (value - extent[0]) / span : 0.5;
}

function denormalizeAxis(value: number, extent: [number, number]): number {
  return extent[0] + value * (extent[1] - extent[0]);
}

function formatSeconds(value: number): string {
  return `${Math.round(value).toLocaleString()} s`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

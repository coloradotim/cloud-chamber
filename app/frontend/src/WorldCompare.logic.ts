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
  type CompareLinkModes,
  type CompareSide,
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

export type SavedPairRestoration = {
  states: Record<CompareSide, ExploreWorldState>;
  links: CompareLinkModes;
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
    const initialView = adapter.viewId(simulation.initial_state);
    const fallbackView = simulation.available_view_ids.includes(initialView)
      ? initialView
      : simulation.available_view_ids[0];
    if (!fallbackView) {
      return {
        state,
        status: "unavailable",
        messages: [...messages, "The Simulation has no compatible Field or Lens."],
      };
    }
    state = restoreUnavailableView(state, adapter.setView(state, fallbackView));
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

function restoreUnavailableView(
  saved: ExploreWorldState,
  fallback: ExploreWorldState,
): ExploreWorldState {
  if (!isSupercellsState(saved) || !isSupercellsState(fallback)) return fallback;
  return {
    ...fallback,
    viewport_id: saved.viewport_id,
    evidence_view: saved.evidence_view,
    plane_coordinate_km: saved.plane_coordinate_km,
    camera_preset: saved.camera_preset,
    camera_transform: saved.camera_transform,
    scene_opacity: saved.scene_opacity,
    scene_point_size: saved.scene_point_size,
    selected_point: saved.selected_point,
    selected_evidence_visible: saved.selected_evidence_visible,
    playback_speed: saved.playback_speed,
    display_controls_open: saved.display_controls_open,
    context_collapsed: saved.context_collapsed,
    secondary_section: saved.secondary_section,
  };
}

export function reconcileSavedComparePair(
  savedStates: Record<CompareSide, ExploreWorldState>,
  savedLinks: CompareLinkModes,
  descriptor: WorldCompareDescriptor,
): SavedPairRestoration {
  const compatibility = descriptor.compatibility;
  const leftSimulation = selectedSimulation(descriptor, descriptor.selected_left_simulation_id);
  const rightSimulation = selectedSimulation(descriptor, descriptor.selected_right_simulation_id);
  if (!compatibility || !leftSimulation || !rightSimulation) {
    throw new Error("The Saved Comparison pair is not available for live inspection.");
  }
  const left = reconcileSavedCompareState(
    savedStates.left,
    leftSimulation,
    compatibility.time_tolerance_seconds,
  );
  const right = reconcileSavedCompareState(
    savedStates.right,
    rightSimulation,
    compatibility.time_tolerance_seconds,
  );
  const messages = [
    ...left.messages.map((message) => `${leftSimulation.display_name}: ${message}`),
    ...right.messages.map((message) => `${rightSimulation.display_name}: ${message}`),
  ];
  const links: CompareLinkModes = {
    time: savedLinks.time && compatibility.nearest_time_link_available,
    view: savedLinks.view && compatibility.shared_view_ids.length > 0,
    plane: savedLinks.plane && compatibility.physical_plane_link_available,
    camera: savedLinks.camera && compatibility.camera_link_available,
    selection: savedLinks.selection && compatibility.selection_link_available,
  };
  (Object.keys(savedLinks) as Array<keyof CompareLinkModes>).forEach((key) => {
    if (savedLinks[key] && !links[key]) {
      messages.push(`${linkLabel(key)} linkage is no longer available and was turned off.`);
    }
  });
  let states = { left: left.state, right: right.state };
  (Object.keys(links) as Array<keyof CompareLinkModes>).forEach((key) => {
    if (!links[key]) return;
    const synchronized = synchronizeCompareLink(
      descriptor,
      key,
      "left",
      states.left,
      states.right,
      true,
    );
    if (!synchronized.applied) {
      links[key] = false;
      messages.push(
        `${linkLabel(key)} linkage could not be restored coherently and was turned off.`,
      );
      messages.push(...synchronized.notices);
      return;
    }
    states = { left: states.left, right: synchronized.state };
    messages.push(...synchronized.notices);
  });
  const uniqueMessages = [...new Set(messages)];
  const unavailable = left.status === "unavailable" || right.status === "unavailable";
  const partial =
    uniqueMessages.length > 0 ||
    left.status === "partially_restorable" ||
    right.status === "partially_restorable";
  return {
    states,
    links,
    status: unavailable ? "unavailable" : partial ? "partially_restorable" : "healthy",
    messages: uniqueMessages,
  };
}

export function synchronizeCompareState(
  descriptor: WorldCompareDescriptor,
  sourceSide: CompareSide,
  source: ExploreWorldState,
  target: ExploreWorldState,
  links: CompareLinkModes,
): { state: ExploreWorldState; notices: string[] } {
  let next = target;
  const notices: string[] = [];
  (Object.keys(links) as Array<keyof CompareLinkModes>).forEach((key) => {
    if (!links[key]) return;
    const synchronized = synchronizeCompareLink(descriptor, key, sourceSide, source, next);
    next = synchronized.state;
    notices.push(...synchronized.notices);
  });
  return { state: next, notices: [...new Set(notices)] };
}

function synchronizeCompareLink(
  descriptor: WorldCompareDescriptor,
  key: keyof CompareLinkModes,
  sourceSide: CompareSide,
  source: ExploreWorldState,
  target: ExploreWorldState,
  restoring = false,
): { state: ExploreWorldState; notices: string[]; applied: boolean } {
  const adapter = WORLD_COMPARE_ADAPTERS[descriptor.world_id];
  const targetSimulation = selectedSimulation(
    descriptor,
    sourceSide === "left"
      ? descriptor.selected_right_simulation_id
      : descriptor.selected_left_simulation_id,
  );
  const sourceSimulation = selectedSimulation(
    descriptor,
    sourceSide === "left"
      ? descriptor.selected_left_simulation_id
      : descriptor.selected_right_simulation_id,
  );
  if (!targetSimulation || !sourceSimulation || source.world_id !== target.world_id) {
    return { state: target, notices: [], applied: false };
  }
  if (key === "time") {
    const mapped = nearestCompareTime(
      targetSimulation,
      adapter.modelTime(source),
      descriptor.compatibility?.time_tolerance_seconds ?? 0,
    );
    if (!mapped) {
      return {
        state: target,
        notices: [
          `${targetSimulation.display_name}: no saved output is within the approved time tolerance.`,
        ],
        applied: false,
      };
    }
    return {
      state: adapter.setModelTime(target, mapped.value),
      notices: mapped.message ? [`${targetSimulation.display_name}: ${mapped.message}`] : [],
      applied: true,
    };
  }
  if (key === "view") {
    const sourceView = adapter.viewId(source);
    if (!descriptor.compatibility?.shared_view_ids.includes(sourceView)) {
      return { state: target, notices: [], applied: false };
    }
    let next = adapter.setView(target, sourceView);
    const sourceField = adapter.fieldId(source);
    if (sourceField) {
      if (!descriptor.compatibility.shared_field_ids.includes(sourceField)) {
        return { state: target, notices: [], applied: false };
      }
      next = adapter.setField(next, sourceField);
    }
    return { state: next, notices: [], applied: true };
  }
  if (key === "plane") {
    if (!descriptor.compatibility?.physical_plane_link_available) {
      return { state: target, notices: [], applied: false };
    }
    const mapped = synchronizePlane(source, target, targetSimulation);
    return { state: mapped ?? target, notices: [], applied: mapped !== null };
  }
  if (key === "camera") {
    if (!descriptor.compatibility?.camera_link_available) {
      return { state: target, notices: [], applied: false };
    }
    const preset = adapter.cameraPreset(source);
    if (!preset) return { state: target, notices: [], applied: false };
    const mapped = mapCamera(
      preset,
      adapter.cameraTransform(source),
      sourceSimulation,
      targetSimulation,
    );
    if (!mapped) return { state: target, notices: [], applied: false };
    return {
      state: adapter.setCamera(target, mapped.preset, mapped.transform),
      notices: mapped.message ? [mapped.message] : [],
      applied: true,
    };
  }
  if (!descriptor.compatibility?.selection_link_available) {
    return { state: target, notices: [], applied: false };
  }
  const sourcePoint = adapter.selectedPoint(source);
  const targetPoint = adapter.selectedPoint(target);
  if (restoring && sourcePoint === null && targetPoint !== null) {
    return { state: target, notices: [], applied: false };
  }
  if (sourcePoint && !pointWithinGrid(sourcePoint, targetSimulation)) {
    return { state: target, notices: [], applied: false };
  }
  return {
    state: adapter.setSelectedPoint(target, sourcePoint),
    notices: [],
    applied: true,
  };
}

function synchronizePlane(
  source: ExploreWorldState,
  target: ExploreWorldState,
  targetSimulation: CompareSimulationDescriptor,
): ExploreWorldState | null {
  if (isTradeState(source) && isTradeState(target)) {
    if (!targetSimulation.plane_orientations.includes(source.active_slice_plane)) return null;
    const { extent, count } = tradePlaneGrid(source.active_slice_plane, targetSimulation);
    if (!extent) return null;
    const mapped = nearestNativePlane(source.slice_coordinate_km, extent, count);
    return {
      ...target,
      active_slice_plane: source.active_slice_plane,
      slice_coordinate_km: mapped.coordinate,
      slice_native_index: mapped.index,
    };
  }
  if (isSupercellsState(source) && isSupercellsState(target)) {
    const orientation =
      source.evidence_view === "plan"
        ? "horizontal"
        : source.evidence_view === "xz"
          ? "vertical_x"
          : "vertical_y";
    if (!targetSimulation.plane_orientations.includes(orientation)) return null;
    const { extent, count } = supercellsPlaneGrid(source.evidence_view, targetSimulation);
    if (!extent) return null;
    return {
      ...target,
      evidence_view: source.evidence_view,
      plane_coordinate_km: nearestNativePlane(source.plane_coordinate_km, extent, count).coordinate,
    };
  }
  return null;
}

function tradePlaneGrid(
  orientation: TradeCumulusExploreState["active_slice_plane"],
  simulation: CompareSimulationDescriptor,
): { extent: [number, number] | null; count: number } {
  if (orientation === "horizontal") {
    return { extent: simulation.grid.z_extent_km, count: simulation.grid.nz };
  }
  if (orientation === "vertical_x") {
    return { extent: simulation.grid.y_extent_km, count: simulation.grid.ny };
  }
  return { extent: simulation.grid.x_extent_km, count: simulation.grid.nx };
}

function supercellsPlaneGrid(
  view: SupercellsExploreState["evidence_view"],
  simulation: CompareSimulationDescriptor,
): { extent: [number, number] | null; count: number } {
  if (view === "plan") {
    return { extent: simulation.grid.z_extent_km, count: simulation.grid.nz };
  }
  if (view === "xz") {
    return { extent: simulation.grid.y_extent_km, count: simulation.grid.ny };
  }
  return { extent: simulation.grid.x_extent_km, count: simulation.grid.nx };
}

function selectedSimulation(
  descriptor: WorldCompareDescriptor,
  simulationId: string | null,
): CompareSimulationDescriptor | null {
  return (
    descriptor.simulations.find((simulation) => simulation.simulation_id === simulationId) ?? null
  );
}

function linkLabel(key: keyof CompareLinkModes): string {
  const labels: Record<keyof CompareLinkModes, string> = {
    time: "Time",
    view: "Field / Lens",
    plane: "Slice plane",
    camera: "Camera",
    selection: "Selection",
  };
  return labels[key];
}

function cameraTargetWithinGrid(
  target: CameraTransform["target"],
  simulation: CompareSimulationDescriptor,
): boolean {
  return (
    within(target[0], simulation.grid.x_extent_km) &&
    within(target[1], simulation.grid.z_extent_km) &&
    (simulation.grid.y_extent_km === null || within(target[2], simulation.grid.y_extent_km))
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
    const mapped = nearestNativePlane(next.slice_coordinate_km, extent, count);
    const coordinate = mapped.coordinate;
    const nativeIndex = mapped.index;
    if (coordinate !== next.slice_coordinate_km || nativeIndex !== next.slice_native_index) {
      const materiallyChanged =
        Math.abs(coordinate - next.slice_coordinate_km) > 1e-6 ||
        nativeIndex !== next.slice_native_index;
      next = {
        ...next,
        slice_coordinate_km: coordinate,
        slice_native_index: nativeIndex,
      };
      if (materiallyChanged) {
        messages.push("The saved slice was mapped to the current physical domain.");
      }
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
    const count =
      next.evidence_view === "plan"
        ? simulation.grid.nz
        : next.evidence_view === "xz"
          ? simulation.grid.ny
          : simulation.grid.nx;
    const coordinate = nearestNativePlane(next.plane_coordinate_km, extent, count).coordinate;
    if (coordinate !== next.plane_coordinate_km) {
      const materiallyChanged = Math.abs(coordinate - next.plane_coordinate_km) > 1e-6;
      next = { ...next, plane_coordinate_km: coordinate };
      if (materiallyChanged) {
        messages.push("The saved evidence plane was mapped to the nearest current native plane.");
      }
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

export function nativePlaneCoordinates(extent: [number, number], count: number): number[] {
  if (count <= 0) return [];
  if (count === 1 || extent[1] === extent[0]) return [(extent[0] + extent[1]) / 2];
  const spacing = (extent[1] - extent[0]) / count;
  return Array.from({ length: count }, (_, index) => extent[0] + (index + 0.5) * spacing);
}

function nearestNativePlane(
  coordinate: number,
  extent: [number, number],
  count: number,
): { coordinate: number; index: number } {
  const values = nativePlaneCoordinates(extent, count);
  if (!values.length) return { coordinate, index: 0 };
  const index = values.reduce(
    (nearest, value, candidate) =>
      Math.abs(value - coordinate) < Math.abs(values[nearest] - coordinate) ? candidate : nearest,
    0,
  );
  return { coordinate: values[index], index };
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

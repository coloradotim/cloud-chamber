import type { ExploreSecondarySection } from "./IntegratedExploreWorkspace";
import type { CameraPreset, CameraTransform } from "./True3DViewer";

export type CuratedDefaultResolutionStatus =
  | "applied"
  | "partially_incompatible"
  | "technical_fallback";

export type CuratedDefaultResolution<T> = {
  status: CuratedDefaultResolutionStatus;
  value: T | null;
  message: string;
  incompatibilities: string[];
};

export type CuratedCommonState = {
  modeledTimeSeconds: number;
  playbackSpeed: number;
  contextCollapsed: boolean;
  secondarySection: ExploreSecondarySection;
  selection: null;
};

export type CuratedPhysicalPlane = {
  orientation: "horizontal" | "vertical_x" | "vertical_y";
  coordinateKm: number;
};

export type TradeCumulusCuratedView = CuratedCommonState & {
  worldId: "trade_cumulus";
  simulationId: "trade_cumulus_canonical_bomex" | "trade_cumulus_more_moisture";
  viewId: "field" | "updraft_lens";
  fieldId: "ql" | "w";
  cloudFieldId: "ql";
  fixedScaleId: "trade_cumulus_updraft_velocity_v1" | null;
  plane: CuratedPhysicalPlane;
  cameraPreset: CameraPreset;
  cameraTransform: CameraTransform | null;
  displayControlsOpen: false;
  cloudThresholdKgKg: number;
  cloudOpacity: number;
  cloudPointSizePx: number;
  lensOpacity: number;
  showSlicePlane: boolean;
  showCloudBoundary: boolean;
  showHorizontalWind: boolean;
  windMode: "perturbation";
};

export type MountainWavesFieldId =
  | "w"
  | "cloud_liquid"
  | "relative_humidity"
  | "theta_perturbation";

export type MountainWavesCuratedView = CuratedCommonState & {
  worldId: "mountain_waves";
  simulationId: "mountain_waves_dry_ridge" | "mountain_waves_boulder_moist_reference";
  viewId: "field" | "wave_structure" | "wave_cloud";
  fieldId: MountainWavesFieldId;
  fixedScaleId:
    | "mountain_waves_vertical_velocity_v1"
    | "mountain_waves_cloud_liquid_v1"
    | "mountain_waves_relative_humidity_v1"
    | "mountain_waves_theta_perturbation_v1";
  geometry: "expanded";
  viewport: "focus" | "full";
  plotFraming: "fit_viewport";
  overlays: {
    horizontalWind: boolean;
    cloudPoints: boolean;
    cloudBoundary: boolean;
    saturationContour: boolean;
    potentialTemperatureContours: boolean;
  };
  cloudOpacity: number;
  cloudPointSizePx: number;
};

export type SupercellsLensId =
  | "rotating_updraft"
  | "cloud_precipitation"
  | "low_level_interactions";

export type SupercellsOverlayState = {
  rotation: boolean;
  updraftHelicity: boolean;
  reflectivity: boolean;
  condensate: boolean;
  rain: boolean;
  wind: boolean;
  precipitatingCondensate: boolean;
  verticalMotion: boolean;
};

export type SupercellsCuratedView = CuratedCommonState & {
  worldId: "supercells";
  simulationId: "supercells_quarter_circle_reference";
  viewId: SupercellsLensId;
  viewport: "storm";
  evidenceOrientation: "plan" | "xz" | "yz";
  plane: CuratedPhysicalPlane;
  cameraPreset: CameraPreset;
  cameraTransform: CameraTransform | null;
  displayControlsOpen: false;
  visibleLayerIds: string[];
  fixedScaleIds: string[];
  overlays: SupercellsOverlayState;
  hydrometeorCategoryCodes: readonly number[];
  sceneOpacity: number;
  scenePointSize: number;
  selectedEvidenceVisible: false;
};

export type WorldCuratedView =
  | TradeCumulusCuratedView
  | MountainWavesCuratedView
  | SupercellsCuratedView;

export type CuratedDefaultCapabilities = {
  availableViewIds?: string[];
  availableFieldIds?: string[];
  availableScaleIds?: string[];
  availableLayerIds?: string[];
  timesSeconds: number[];
  planeCoordinatesKm?: number[];
  planeNativeIndices?: number[];
};

export type ResolvedCuratedView<T extends WorldCuratedView> = {
  definition: T;
  timeIndex: number;
  planePositionIndex: number | null;
  planeNativeIndex: number | null;
};

const COMMON_STATE = {
  playbackSpeed: 1,
  contextCollapsed: false,
  secondarySection: "science",
  selection: null,
} as const;

const TRADE_CUMULUS_PRESENTATIONS = {
  trade_cumulus_canonical_bomex: {
    modeledTimeSeconds: 12_060,
    planeCoordinateKm: 2.366666555404663,
  },
  trade_cumulus_more_moisture: {
    modeledTimeSeconds: 13_920,
    planeCoordinateKm: 1.6333333253860474,
  },
} as const;

export const TRADE_CUMULUS_INITIAL_VIEW = "updraft_lens" as const;

export function tradeCumulusCuratedView(
  simulationId: string | null | undefined,
  viewId: TradeCumulusCuratedView["viewId"],
): TradeCumulusCuratedView | null {
  if (
    simulationId !== "trade_cumulus_canonical_bomex" &&
    simulationId !== "trade_cumulus_more_moisture"
  ) {
    return null;
  }
  const presentation = TRADE_CUMULUS_PRESENTATIONS[simulationId];
  return {
    ...COMMON_STATE,
    worldId: "trade_cumulus",
    simulationId,
    viewId,
    fieldId: viewId === "field" ? "ql" : "w",
    cloudFieldId: "ql",
    fixedScaleId: viewId === "updraft_lens" ? "trade_cumulus_updraft_velocity_v1" : null,
    modeledTimeSeconds: presentation.modeledTimeSeconds,
    plane: {
      orientation: "vertical_x",
      coordinateKm: presentation.planeCoordinateKm,
    },
    cameraPreset: "overview",
    cameraTransform: null,
    displayControlsOpen: false,
    cloudThresholdKgKg: 1e-6,
    cloudOpacity: 0.68,
    cloudPointSizePx: 11,
    lensOpacity: 0.9,
    showSlicePlane: true,
    showCloudBoundary: true,
    showHorizontalWind: true,
    windMode: "perturbation",
  };
}

const MOUNTAIN_WAVES_TIME_SECONDS = {
  mountain_waves_dry_ridge: 2_160,
  mountain_waves_boulder_moist_reference: 7_200,
} as const;

const MOUNTAIN_WAVES_SCALE_IDS: Record<
  MountainWavesFieldId,
  MountainWavesCuratedView["fixedScaleId"]
> = {
  w: "mountain_waves_vertical_velocity_v1",
  cloud_liquid: "mountain_waves_cloud_liquid_v1",
  relative_humidity: "mountain_waves_relative_humidity_v1",
  theta_perturbation: "mountain_waves_theta_perturbation_v1",
};

export function mountainWavesInitialView(
  simulationId: string,
): MountainWavesCuratedView["viewId"] | null {
  if (simulationId === "mountain_waves_dry_ridge") return "wave_structure";
  if (simulationId === "mountain_waves_boulder_moist_reference") return "wave_cloud";
  return null;
}

export function mountainWavesCuratedView(
  simulationId: string,
  viewId: MountainWavesCuratedView["viewId"],
  fieldId: MountainWavesFieldId = "w",
): MountainWavesCuratedView | null {
  if (
    simulationId !== "mountain_waves_dry_ridge" &&
    simulationId !== "mountain_waves_boulder_moist_reference"
  ) {
    return null;
  }
  if (simulationId === "mountain_waves_dry_ridge" && viewId === "wave_cloud") return null;
  const activeField = viewId === "field" ? fieldId : "w";
  return {
    ...COMMON_STATE,
    worldId: "mountain_waves",
    simulationId,
    viewId,
    fieldId: activeField,
    fixedScaleId: MOUNTAIN_WAVES_SCALE_IDS[activeField],
    modeledTimeSeconds: MOUNTAIN_WAVES_TIME_SECONDS[simulationId],
    geometry: "expanded",
    viewport: simulationId === "mountain_waves_dry_ridge" ? "full" : "focus",
    plotFraming: "fit_viewport",
    overlays: {
      horizontalWind: viewId !== "field",
      cloudPoints: viewId === "wave_cloud",
      cloudBoundary: viewId === "wave_cloud",
      saturationContour: viewId === "wave_cloud",
      potentialTemperatureContours: viewId === "wave_structure",
    },
    cloudOpacity: 0.68,
    cloudPointSizePx: 11,
  };
}

export const SUPERCELLS_INITIAL_LENS = "rotating_updraft" as const;

const SUPERCELLS_COMMON = {
  ...COMMON_STATE,
  worldId: "supercells",
  simulationId: "supercells_quarter_circle_reference",
  modeledTimeSeconds: 4_440,
  viewport: "storm",
  cameraTransform: null,
  displayControlsOpen: false,
  hydrometeorCategoryCodes: [1, 2, 3, 4, 5],
  selectedEvidenceVisible: false,
} as const;

export const SUPERCELLS_CURATED_VIEWS: Record<SupercellsLensId, SupercellsCuratedView> = {
  rotating_updraft: {
    ...SUPERCELLS_COMMON,
    viewId: "rotating_updraft",
    evidenceOrientation: "plan",
    plane: { orientation: "horizontal", coordinateKm: 3.1666669845581055 },
    cameraPreset: "look_along_y",
    visibleLayerIds: ["storm_cloud_body", "rising_core", "cyclonic_rotation", "updraft_helicity"],
    fixedScaleIds: ["supercell_midlevel_vertical_velocity_v1"],
    overlays: {
      rotation: true,
      updraftHelicity: true,
      reflectivity: false,
      condensate: true,
      rain: false,
      wind: false,
      precipitatingCondensate: false,
      verticalMotion: true,
    },
    sceneOpacity: 1,
    scenePointSize: 1,
  },
  cloud_precipitation: {
    ...SUPERCELLS_COMMON,
    viewId: "cloud_precipitation",
    evidenceOrientation: "xz",
    plane: { orientation: "vertical_x", coordinateKm: 0.75 },
    cameraPreset: "look_along_y",
    visibleLayerIds: ["hydrometeor_categories"],
    fixedScaleIds: ["supercell_total_condensate_v2"],
    overlays: {
      rotation: false,
      updraftHelicity: false,
      reflectivity: false,
      condensate: false,
      rain: false,
      wind: false,
      precipitatingCondensate: false,
      verticalMotion: true,
    },
    sceneOpacity: 0.9,
    scenePointSize: 0.9,
  },
  low_level_interactions: {
    ...SUPERCELLS_COMMON,
    viewId: "low_level_interactions",
    evidenceOrientation: "plan",
    plane: { orientation: "horizontal", coordinateKm: 1.1666667461395264 },
    cameraPreset: "low_level",
    visibleLayerIds: [
      "low_level_vertical_motion",
      "accumulated_surface_rain",
      "precipitating_condensate",
      "model_relative_wind",
    ],
    fixedScaleIds: ["supercell_low_level_vertical_velocity_v1"],
    overlays: {
      rotation: false,
      updraftHelicity: false,
      reflectivity: false,
      condensate: false,
      rain: true,
      wind: true,
      precipitatingCondensate: true,
      verticalMotion: true,
    },
    sceneOpacity: 1,
    scenePointSize: 1,
  },
};

export function supercellsCuratedView(
  simulationId: string,
  lensId: SupercellsLensId,
): SupercellsCuratedView | null {
  if (simulationId !== "supercells_quarter_circle_reference") return null;
  return SUPERCELLS_CURATED_VIEWS[lensId];
}

export function resolveCuratedView<T extends WorldCuratedView>(
  definition: T | null,
  capabilities: CuratedDefaultCapabilities,
): CuratedDefaultResolution<ResolvedCuratedView<T>> {
  if (!definition) {
    return technicalFallback(
      "No authored curated view is available for this Simulation. Current compatible controls remain in use.",
      ["stable Simulation identity has no authored default"],
    );
  }

  const blockers: string[] = [];
  const partial: string[] = [];
  const viewId = curatedViewId(definition);
  validateAvailable(capabilities.availableViewIds, viewId, "view", blockers);
  if ("fieldId" in definition) {
    validateAvailable(capabilities.availableFieldIds, definition.fieldId, "field", blockers);
  }
  const scaleIds =
    "fixedScaleIds" in definition
      ? definition.fixedScaleIds
      : definition.fixedScaleId
        ? [definition.fixedScaleId]
        : [];
  scaleIds.forEach((scaleId) =>
    validateAvailable(capabilities.availableScaleIds, scaleId, "scale", blockers),
  );
  if ("visibleLayerIds" in definition) {
    definition.visibleLayerIds.forEach((layerId) =>
      validateAvailable(capabilities.availableLayerIds, layerId, "layer", blockers),
    );
  }
  if (blockers.length > 0) {
    return technicalFallback(
      `The authored ${curatedViewLabel(definition)} view is incompatible with the available output. Current compatible controls remain in use.`,
      blockers,
    );
  }

  const resolvedTime = nearestIndex(capabilities.timesSeconds, definition.modeledTimeSeconds);
  if (resolvedTime === null) {
    return technicalFallback(
      `The authored ${curatedViewLabel(definition)} time cannot be resolved because this output has no saved times.`,
      ["saved output time coordinates are unavailable"],
    );
  }
  if (!nearlyEqual(resolvedTime.value, definition.modeledTimeSeconds)) {
    partial.push(
      `authored time ${formatNumber(definition.modeledTimeSeconds)} s resolved to nearest saved output ${formatNumber(resolvedTime.value)} s`,
    );
  }

  let planePositionIndex: number | null = null;
  let planeNativeIndex: number | null = null;
  if ("plane" in definition) {
    const resolvedPlane = nearestIndex(
      capabilities.planeCoordinatesKm ?? [],
      definition.plane.coordinateKm,
    );
    if (resolvedPlane === null) {
      return technicalFallback(
        `The authored ${curatedViewLabel(definition)} plane cannot be resolved from this output.`,
        ["native plane coordinates are unavailable"],
      );
    }
    planePositionIndex = resolvedPlane.index;
    planeNativeIndex =
      capabilities.planeNativeIndices?.[resolvedPlane.index] ?? resolvedPlane.index;
    if (!nearlyEqual(resolvedPlane.value, definition.plane.coordinateKm)) {
      partial.push(
        `authored plane ${formatNumber(definition.plane.coordinateKm)} km resolved to nearest native plane ${formatNumber(resolvedPlane.value)} km`,
      );
    }
  }

  const value = {
    definition,
    timeIndex: resolvedTime.index,
    planePositionIndex,
    planeNativeIndex,
  };
  if (partial.length > 0) {
    return {
      status: "partially_incompatible",
      value,
      message: `Curated ${curatedViewLabel(definition)} view restored with the nearest compatible saved coordinates.`,
      incompatibilities: partial,
    };
  }
  return {
    status: "applied",
    value,
    message: `Curated ${curatedViewLabel(definition)} view restored.`,
    incompatibilities: [],
  };
}

export function curatedResolutionExplanation(result: CuratedDefaultResolution<unknown>): string {
  if (result.incompatibilities.length === 0) return result.message;
  return `${result.message} ${result.incompatibilities.join("; ")}.`;
}

function technicalFallback<T>(
  message: string,
  incompatibilities: string[],
): CuratedDefaultResolution<T> {
  return {
    status: "technical_fallback",
    value: null,
    message,
    incompatibilities,
  };
}

function curatedViewId(definition: WorldCuratedView): string {
  return definition.viewId;
}

function curatedViewLabel(definition: WorldCuratedView): string {
  switch (definition.viewId) {
    case "updraft_lens":
      return "Updraft Lens";
    case "wave_structure":
      return "Wave Structure Lens";
    case "wave_cloud":
      return "Wave Cloud Lens";
    case "rotating_updraft":
      return "Rotating Updraft";
    case "cloud_precipitation":
      return "Cloud and Precipitation";
    case "low_level_interactions":
      return "Low-Level Interactions";
    default:
      return "Field";
  }
}

function validateAvailable(
  available: string[] | undefined,
  expected: string,
  label: string,
  blockers: string[],
) {
  if (available && !available.includes(expected))
    blockers.push(`${label} ${expected} is unavailable`);
}

function nearestIndex(values: number[], target: number) {
  if (values.length === 0) return null;
  let index = 0;
  let distance = Math.abs(values[0] - target);
  for (let candidate = 1; candidate < values.length; candidate += 1) {
    const candidateDistance = Math.abs(values[candidate] - target);
    if (candidateDistance < distance) {
      index = candidate;
      distance = candidateDistance;
    }
  }
  return { index, value: values[index] };
}

function nearlyEqual(left: number, right: number): boolean {
  return Math.abs(left - right) <= Math.max(1e-6, Math.abs(right) * 1e-6);
}

function formatNumber(value: number): string {
  return Number.isInteger(value)
    ? String(value)
    : value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

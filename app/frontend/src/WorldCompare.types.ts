import type {
  ExplorePoint,
  ExploreWorldState,
  MountainWavesExploreState,
  SupercellsExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import type { CameraPreset, CameraTransform } from "./True3DViewer";

export type CompareWorldId = ExploreWorldState["world_id"];
export type CompareWorldSlug = "trade-cumulus" | "mountain-waves" | "supercells";

export type CompareDifference = {
  path: string;
  label: string;
  category: "atmospheric" | "numerical" | "output" | "operational" | "metadata";
  left_value: unknown;
  right_value: unknown;
  left_known: boolean;
  right_known: boolean;
  units: string | null;
  material: boolean;
};

export type CompareGridDescriptor = {
  topology: "native_3d" | "native_2d_xz";
  nx: number;
  ny: number;
  nz: number;
  dx_m: number;
  dy_m: number;
  dz_m: number;
  x_extent_km: [number, number];
  y_extent_km: [number, number] | null;
  z_extent_km: [number, number];
};

export type CompareTimeDescriptor = {
  times_seconds: number[];
  start_seconds: number;
  end_seconds: number;
  cadence_seconds: number;
  saved_output_count: number;
  interpolation_allowed: false;
};

export type CompareSimulationDescriptor = {
  simulation_id: string;
  display_name: string;
  world_id: CompareWorldId;
  role: string;
  run_id: string;
  result_id: string | null;
  case_id: string;
  parent_simulation_id: string | null;
  reference_simulation_id: string | null;
  lineage_state: string;
  availability_state: string;
  availability_message: string;
  inspectable: boolean;
  grid: CompareGridDescriptor;
  time: CompareTimeDescriptor;
  available_field_ids: string[];
  available_view_ids: string[];
  fixed_scale_ids: string[];
  plane_orientations: Array<"horizontal" | "vertical_x" | "vertical_y">;
  camera_mapping: "normalized_3d" | "native_2d_xz";
  initial_state: ExploreWorldState;
  caveats: string[];
};

export type CompareCompatibility = {
  same_world: boolean;
  both_inspectable: boolean;
  relationship: string;
  controlled_pair: boolean;
  controlled_pair_message: string;
  shared_field_ids: string[];
  shared_view_ids: string[];
  shared_fixed_scale_ids: string[];
  exact_time_link_available: boolean;
  nearest_time_link_available: boolean;
  time_tolerance_seconds: number;
  physical_plane_link_available: boolean;
  camera_link_available: boolean;
  selection_link_available: boolean;
  blockers: string[];
};

export type WorldCompareDescriptor = {
  schema_version: "world_compare_v1";
  world_id: CompareWorldId;
  display_name: string;
  simulations: CompareSimulationDescriptor[];
  default_left_simulation_id: string | null;
  default_right_simulation_id: string | null;
  selected_left_simulation_id: string | null;
  selected_right_simulation_id: string | null;
  material_differences: CompareDifference[];
  compatibility: CompareCompatibility | null;
  no_second_simulation_message: string | null;
  persistence: "transient_only";
};

export type CompareLinkModes = {
  time: boolean;
  view: boolean;
  plane: boolean;
  camera: boolean;
  selection: boolean;
};

export type CompareSide = "left" | "right";

export type CompareMappingResult<T> = {
  value: T;
  exact: boolean;
  message: string | null;
};

export type ComparePerformanceSample = {
  side: CompareSide;
  key: string;
  request_ms: number;
  payload_bytes: number;
  cache_hit: boolean;
};

export type ComparePerformanceSummary = {
  first_useful_dual_view_ms: number | null;
  cache_entries: Record<CompareSide, number>;
  estimated_cached_payload_bytes: Record<CompareSide, number>;
  samples: ComparePerformanceSample[];
};

export type WorldCompareAdapter = {
  worldId: CompareWorldId;
  viewLabel: string;
  viewOptions: (simulation: CompareSimulationDescriptor) => Array<{ id: string; label: string }>;
  viewId: (state: ExploreWorldState) => string;
  setView: (state: ExploreWorldState, viewId: string) => ExploreWorldState;
  fieldId: (state: ExploreWorldState) => string | null;
  setField: (state: ExploreWorldState, fieldId: string) => ExploreWorldState;
  modelTime: (state: ExploreWorldState) => number;
  setModelTime: (state: ExploreWorldState, seconds: number) => ExploreWorldState;
  selectedPoint: (state: ExploreWorldState) => ExplorePoint | null;
  setSelectedPoint: (state: ExploreWorldState, point: ExplorePoint | null) => ExploreWorldState;
  cameraPreset: (state: ExploreWorldState) => CameraPreset | null;
  setCamera: (
    state: ExploreWorldState,
    preset: CameraPreset,
    transform: CameraTransform | null,
  ) => ExploreWorldState;
  cameraTransform: (state: ExploreWorldState) => CameraTransform | null;
};

export function isTradeState(state: ExploreWorldState): state is TradeCumulusExploreState {
  return state.world_id === "trade_cumulus";
}

export function isMountainState(state: ExploreWorldState): state is MountainWavesExploreState {
  return state.world_id === "mountain_waves";
}

export function isSupercellsState(state: ExploreWorldState): state is SupercellsExploreState {
  return state.world_id === "supercells";
}

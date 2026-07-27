import { describe, expect, it } from "vitest";

import type {
  MountainWavesExploreState,
  SupercellsExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import {
  mapCamera,
  nativePlaneCoordinates,
  nearestCompareTime,
  reconcileSavedComparePair,
  reconcileSavedCompareState,
  timeIndexForSeconds,
  validateWorldCompareDescriptor,
  WORLD_COMPARE_ADAPTERS,
} from "./WorldCompare.logic";
import type { CompareSimulationDescriptor, WorldCompareDescriptor } from "./WorldCompare.types";

const commonState = {
  state_version: 1 as const,
  context_collapsed: true,
  secondary_section: "notes" as const,
  selected_point: null,
};

const tradeState: TradeCumulusExploreState = {
  ...commonState,
  world_id: "trade_cumulus",
  model_time_seconds: 120,
  view_id: "field",
  scene_field_id: "ql",
  slice_field_id: "ql",
  fixed_scale_id: null,
  active_slice_plane: "vertical_x",
  slice_coordinate_km: 0.9666666666666668,
  slice_native_index: 62,
  horizontal_slice_coordinate_km: 1,
  threshold_native: 1e-6,
  layer_opacity: 0.68,
  point_size_px: 11,
  lens_opacity: 0.9,
  show_slice_plane: true,
  show_cloud_boundary: false,
  show_horizontal_wind: false,
  wind_mode: "perturbation",
  camera_preset: "overview",
  camera_transform: null,
  playback_speed: 1,
  display_controls_open: false,
};

const mountainState: MountainWavesExploreState = {
  ...commonState,
  world_id: "mountain_waves",
  model_time_seconds: 200,
  view_id: "wave_structure",
  field_id: "w",
  fixed_scale_id: "mountain_waves_vertical_velocity_v1",
  viewport_id: "focus",
  geometry_id: "expanded",
  overlays: {
    cloud_points: false,
    cloud_boundary: false,
    saturation_contour: false,
    horizontal_wind: true,
    potential_temperature_contours: true,
  },
  cloud_opacity: 0.68,
  cloud_point_size_px: 11,
  playback_speed: 1,
};

const supercellsState: SupercellsExploreState = {
  ...commonState,
  world_id: "supercells",
  model_time_seconds: 7_500,
  lens_id: "rotating_updraft",
  viewport_id: "storm",
  evidence_view: "xz",
  plane_coordinate_km: -8.25,
  visible_layer_ids: ["vertical_motion"],
  fixed_scale_ids: ["supercells_vertical_velocity_v1"],
  overlays: {
    rotation: true,
    updraft_helicity: true,
    reflectivity: false,
    condensate: true,
    rain: false,
    wind: false,
    precipitating_condensate: false,
    vertical_motion: true,
  },
  hydrometeor_category_codes: [1, 2, 3, 4, 5],
  camera_preset: "overview",
  camera_transform: null,
  scene_opacity: 0.82,
  scene_point_size: 1.2,
  selected_evidence_visible: false,
  playback_speed: 1,
  display_controls_open: true,
};

function simulation(
  updates: Partial<CompareSimulationDescriptor> = {},
): CompareSimulationDescriptor {
  return {
    simulation_id: "left",
    display_name: "Left",
    world_id: "trade_cumulus",
    role: "reference",
    run_id: "left-run",
    result_id: "left-result",
    case_id: "case",
    parent_simulation_id: null,
    reference_simulation_id: null,
    lineage_state: "known",
    availability_state: "available",
    availability_message: "Available",
    inspectable: true,
    grid: {
      topology: "native_3d",
      nx: 96,
      ny: 96,
      nz: 100,
      dx_m: 66.67,
      dy_m: 66.67,
      dz_m: 30,
      x_extent_km: [-3.2, 3.2],
      y_extent_km: [-3.2, 3.2],
      z_extent_km: [0, 3],
    },
    time: {
      times_seconds: [0, 60, 120, 180],
      start_seconds: 0,
      end_seconds: 180,
      cadence_seconds: 60,
      saved_output_count: 4,
      interpolation_allowed: false,
    },
    available_field_ids: ["ql", "w"],
    available_view_ids: ["field", "updraft_lens"],
    fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
    plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
    camera_mapping: "normalized_3d",
    initial_state: tradeState,
    caveats: [],
    ...updates,
  };
}

describe("World Compare adapter logic", () => {
  it("uses exact modeled seconds and labels bounded nearest-output mappings", () => {
    const descriptor = simulation();

    expect(nearestCompareTime(descriptor, 120, 90)).toEqual({
      value: 120,
      exact: true,
      message: null,
    });
    expect(nearestCompareTime(descriptor, 95, 30)).toEqual({
      value: 120,
      exact: false,
      message: "Requested 95 s; showing nearest saved output at 120 s.",
    });
    expect(nearestCompareTime(descriptor, 95, 20)).toBeNull();
    expect(timeIndexForSeconds(descriptor, 95)).toBe(2);
  });

  it("maps 3-D camera coordinates by normalized domain position", () => {
    const source = simulation();
    const target = simulation({
      simulation_id: "right",
      grid: {
        topology: "native_3d",
        nx: 240,
        ny: 240,
        nz: 60,
        dx_m: 500,
        dy_m: 500,
        dz_m: 333.33,
        x_extent_km: [-60, 60],
        y_extent_km: [-60, 60],
        z_extent_km: [0, 20],
      },
    });

    expect(
      mapCamera(
        "overview",
        {
          position: [3.2, 3, 3.2],
          target: [0, 1.5, 0],
          up: [0, 1, 0],
        },
        source,
        target,
      ),
    ).toEqual({
      preset: "overview",
      transform: {
        position: [60, 20, 60],
        target: [0, 10, 0],
        up: [0, 1, 0],
      },
      message: "Camera mapped by normalized domain position; physical coordinates differ.",
    });
    expect(
      mapCamera(
        "overview",
        null,
        source,
        simulation({
          camera_mapping: "native_2d_xz",
          grid: { ...source.grid, topology: "native_2d_xz", y_extent_km: null },
        }),
      ),
    ).toBeNull();
  });

  it("reuses each World's established view semantics", () => {
    const tradeLens = WORLD_COMPARE_ADAPTERS.trade_cumulus.setView(tradeState, "updraft_lens");
    expect(tradeLens).toMatchObject({
      view_id: "updraft_lens",
      slice_field_id: "w",
      fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
      show_cloud_boundary: true,
      show_horizontal_wind: true,
    });

    const cloudLens = WORLD_COMPARE_ADAPTERS.mountain_waves.setView(mountainState, "wave_cloud");
    expect(cloudLens).toMatchObject({
      view_id: "wave_cloud",
      field_id: "w",
      overlays: {
        cloud_points: true,
        cloud_boundary: true,
        saturation_contour: true,
        horizontal_wind: true,
        potential_temperature_contours: false,
      },
    });
    expect(
      WORLD_COMPARE_ADAPTERS.mountain_waves.setField(cloudLens, "relative_humidity"),
    ).toMatchObject({
      field_id: "relative_humidity",
      fixed_scale_id: "mountain_waves_relative_humidity_v1",
    });
  });

  it("restores saved time, physical plane, and selection against current metadata", () => {
    const restored = reconcileSavedCompareState(
      {
        ...tradeState,
        model_time_seconds: 95,
        slice_coordinate_km: 20,
        slice_native_index: 999,
        fixed_scale_id: "retired_scale",
        camera_transform: {
          position: [5, 5, 5],
          target: [99, 0, 1],
          up: [0, 1, 0],
        },
        selected_point: { x_km: 99, y_km: 0, z_km: 1 },
      },
      simulation(),
      30,
    );

    expect(restored.status).toBe("partially_restorable");
    expect(restored.state.model_time_seconds).toBe(120);
    expect(restored.state.selected_point).toBeNull();
    expect((restored.state as TradeCumulusExploreState).fixed_scale_id).toBeNull();
    expect((restored.state as TradeCumulusExploreState).camera_transform).toBeNull();
    expect(restored.state).toMatchObject({
      slice_coordinate_km: 3.166666666666666,
      slice_native_index: 95,
    });
    expect(restored.messages).toEqual(
      expect.arrayContaining([
        expect.stringContaining("nearest saved output"),
        expect.stringContaining("current physical domain"),
        expect.stringContaining("fixed scale"),
        expect.stringContaining("camera target"),
        expect.stringContaining("selected point"),
      ]),
    );

    const viewFallback = reconcileSavedCompareState(
      {
        ...tradeState,
        view_id: "updraft_lens",
        slice_field_id: "w",
      },
      simulation({ available_view_ids: ["field"] }),
      30,
    );
    expect(viewFallback.status).toBe("partially_restorable");
    expect(viewFallback.state).toMatchObject({
      view_id: "field",
      layer_opacity: tradeState.layer_opacity,
      point_size_px: tradeState.point_size_px,
      playback_speed: tradeState.playback_speed,
    });
    expect(viewFallback.messages).toContain(
      "The saved view is unavailable; the current default view is shown.",
    );
  });

  it("uses x-z-y camera axes when validating asymmetric domains", () => {
    const valid = reconcileSavedCompareState(
      {
        ...tradeState,
        camera_transform: {
          position: [4, 4, 4],
          target: [0, 2.5, 3],
          up: [0, 1, 0],
        },
      },
      simulation(),
      30,
    );
    expect((valid.state as TradeCumulusExploreState).camera_transform).not.toBeNull();

    const invalid = reconcileSavedCompareState(
      {
        ...tradeState,
        camera_transform: {
          position: [4, 4, 4],
          target: [0, 3.1, 0],
          up: [0, 1, 0],
        },
      },
      simulation(),
      30,
    );
    expect((invalid.state as TradeCumulusExploreState).camera_transform).toBeNull();
    expect(invalid.messages).toContain(
      "The saved camera target is outside the current domain and was reset.",
    );
  });

  it("restores only links that remain coherent with current pair capabilities", () => {
    const left = simulation({ simulation_id: "left" });
    const right = simulation({
      simulation_id: "right",
      display_name: "Right",
      time: {
        times_seconds: [0, 100, 200],
        start_seconds: 0,
        end_seconds: 200,
        cadence_seconds: 100,
        saved_output_count: 3,
        interpolation_allowed: false,
      },
    });
    const descriptor: WorldCompareDescriptor = {
      schema_version: "world_compare_v1",
      world_id: "trade_cumulus",
      display_name: "Trade Cumulus",
      simulations: [left, right],
      default_left_simulation_id: "left",
      default_right_simulation_id: "right",
      selected_left_simulation_id: "left",
      selected_right_simulation_id: "right",
      material_differences: [],
      compatibility: {
        same_world: true,
        both_inspectable: true,
        relationship: "Test pair",
        controlled_pair: true,
        controlled_pair_message: "Controlled.",
        shared_field_ids: ["ql", "w"],
        shared_view_ids: ["field", "updraft_lens"],
        shared_fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
        exact_time_link_available: false,
        nearest_time_link_available: true,
        time_tolerance_seconds: 30,
        physical_plane_link_available: false,
        camera_link_available: false,
        selection_link_available: true,
        blockers: [],
      },
      no_second_simulation_message: null,
      persistence: "transient_only",
    };
    const restored = reconcileSavedComparePair(
      {
        left: { ...tradeState, model_time_seconds: 120 },
        right: { ...tradeState, model_time_seconds: 120 },
      },
      { time: true, view: true, plane: true, camera: true, selection: false },
      descriptor,
    );

    expect(restored.links).toEqual({
      time: true,
      view: true,
      plane: false,
      camera: false,
      selection: false,
    });
    expect(restored.states.right.model_time_seconds).toBe(100);
    expect(restored.messages).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Slice plane linkage is no longer available"),
        expect.stringContaining("Camera linkage is no longer available"),
        expect.stringContaining("nearest saved output"),
      ]),
    );
  });

  it("turns off ambiguous one-sided saved selection without erasing either side", () => {
    const left = simulation({ simulation_id: "left" });
    const right = simulation({ simulation_id: "right", display_name: "Right" });
    const descriptor: WorldCompareDescriptor = {
      schema_version: "world_compare_v1",
      world_id: "trade_cumulus",
      display_name: "Trade Cumulus",
      simulations: [left, right],
      default_left_simulation_id: "left",
      default_right_simulation_id: "right",
      selected_left_simulation_id: "left",
      selected_right_simulation_id: "right",
      material_differences: [],
      compatibility: {
        same_world: true,
        both_inspectable: true,
        relationship: "Test pair",
        controlled_pair: true,
        controlled_pair_message: "Controlled.",
        shared_field_ids: ["ql", "w"],
        shared_view_ids: ["field", "updraft_lens"],
        shared_fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
        exact_time_link_available: true,
        nearest_time_link_available: true,
        time_tolerance_seconds: 30,
        physical_plane_link_available: true,
        camera_link_available: true,
        selection_link_available: true,
        blockers: [],
      },
      no_second_simulation_message: null,
      persistence: "transient_only",
    };
    const rightPoint = { x_km: 1, y_km: 1, z_km: 1 };
    const restored = reconcileSavedComparePair(
      {
        left: { ...tradeState, selected_point: null },
        right: { ...tradeState, selected_point: rightPoint },
      },
      { time: false, view: false, plane: false, camera: false, selection: true },
      descriptor,
    );

    expect(restored.links.selection).toBe(false);
    expect(restored.states.left.selected_point).toBeNull();
    expect(restored.states.right.selected_point).toEqual(rightPoint);
    expect(restored.messages).toContain(
      "Selection linkage could not be restored coherently and was turned off.",
    );
  });

  it("falls back a retired Lens without discarding compatible side state", () => {
    const left = simulation({ simulation_id: "left" });
    const right = simulation({
      simulation_id: "right",
      display_name: "Right",
      available_view_ids: ["field"],
    });
    const descriptor: WorldCompareDescriptor = {
      schema_version: "world_compare_v1",
      world_id: "trade_cumulus",
      display_name: "Trade Cumulus",
      simulations: [left, right],
      default_left_simulation_id: "left",
      default_right_simulation_id: "right",
      selected_left_simulation_id: "left",
      selected_right_simulation_id: "right",
      material_differences: [],
      compatibility: {
        same_world: true,
        both_inspectable: true,
        relationship: "Test pair",
        controlled_pair: true,
        controlled_pair_message: "Controlled.",
        shared_field_ids: ["ql"],
        shared_view_ids: ["field"],
        shared_fixed_scale_ids: [],
        exact_time_link_available: true,
        nearest_time_link_available: true,
        time_tolerance_seconds: 30,
        physical_plane_link_available: true,
        camera_link_available: true,
        selection_link_available: true,
        blockers: [],
      },
      no_second_simulation_message: null,
      persistence: "transient_only",
    };
    const savedLensState: TradeCumulusExploreState = {
      ...tradeState,
      view_id: "updraft_lens",
      slice_field_id: "w",
      layer_opacity: 0.42,
      point_size_px: 7,
    };
    const restored = reconcileSavedComparePair(
      { left: savedLensState, right: savedLensState },
      { time: false, view: true, plane: false, camera: false, selection: false },
      descriptor,
    );

    expect(restored.links.view).toBe(false);
    expect((restored.states.left as TradeCumulusExploreState).view_id).toBe("updraft_lens");
    expect(restored.states.right).toMatchObject({
      view_id: "field",
      layer_opacity: 0.42,
      point_size_px: 7,
    });
    expect(restored.messages).toEqual(
      expect.arrayContaining([
        expect.stringContaining("saved view is unavailable"),
        expect.stringContaining("Field / Lens linkage could not be restored"),
      ]),
    );
  });

  it("maps plane coordinates to actual current cell centers", () => {
    const coordinates = nativePlaneCoordinates([-3.2, 3.2], 96);
    expect(coordinates).toHaveLength(96);
    expect(coordinates[0]).toBeCloseTo(-3.1666666667);
    expect(coordinates[95]).toBeCloseTo(3.1666666667);
  });

  it("restores exact saved state through each World adapter", () => {
    const mountainSimulation = simulation({
      simulation_id: "mountain",
      world_id: "mountain_waves",
      grid: {
        topology: "native_2d_xz",
        nx: 440,
        ny: 1,
        nz: 250,
        dx_m: 500,
        dy_m: 500,
        dz_m: 100,
        x_extent_km: [-110, 110],
        y_extent_km: null,
        z_extent_km: [0, 25],
      },
      time: {
        times_seconds: [0, 100, 200, 300],
        start_seconds: 0,
        end_seconds: 300,
        cadence_seconds: 100,
        saved_output_count: 4,
        interpolation_allowed: false,
      },
      available_field_ids: ["w", "theta_perturbation", "cloud_liquid", "relative_humidity"],
      available_view_ids: ["field", "wave_structure", "wave_cloud"],
      fixed_scale_ids: ["mountain_waves_vertical_velocity_v1"],
      plane_orientations: ["vertical_x"],
      camera_mapping: "native_2d_xz",
      initial_state: mountainState,
    });
    const supercellsSimulation = simulation({
      simulation_id: "supercell",
      world_id: "supercells",
      grid: {
        topology: "native_3d",
        nx: 240,
        ny: 240,
        nz: 60,
        dx_m: 500,
        dy_m: 500,
        dz_m: 333.33,
        x_extent_km: [-60, 60],
        y_extent_km: [-60, 60],
        z_extent_km: [0, 20],
      },
      time: {
        times_seconds: [0, 7_500, 7_620],
        start_seconds: 0,
        end_seconds: 7_620,
        cadence_seconds: 120,
        saved_output_count: 3,
        interpolation_allowed: false,
      },
      available_field_ids: ["w", "qc", "qr"],
      available_view_ids: ["rotating_updraft", "cloud_precipitation", "low_level_interactions"],
      fixed_scale_ids: ["supercells_vertical_velocity_v1"],
      plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
      camera_mapping: "normalized_3d",
      initial_state: supercellsState,
    });

    expect(reconcileSavedCompareState(tradeState, simulation(), 30)).toEqual({
      state: tradeState,
      status: "healthy",
      messages: [],
    });
    expect(reconcileSavedCompareState(mountainState, mountainSimulation, 50)).toEqual({
      state: mountainState,
      status: "healthy",
      messages: [],
    });
    expect(reconcileSavedCompareState(supercellsState, supercellsSimulation, 60)).toEqual({
      state: supercellsState,
      status: "healthy",
      messages: [],
    });
    expect(
      reconcileSavedCompareState(
        { ...supercellsState, plane_coordinate_km: -8.2500003 },
        supercellsSimulation,
        60,
      ),
    ).toEqual({
      state: supercellsState,
      status: "healthy",
      messages: [],
    });
  });

  it("rejects malformed descriptor envelopes", () => {
    expect(() => validateWorldCompareDescriptor({})).toThrow(
      "World Compare metadata does not match the required contract.",
    );
    expect(
      validateWorldCompareDescriptor({
        schema_version: "world_compare_v1",
        world_id: "supercells",
        simulations: [],
      }),
    ).toMatchObject({ world_id: "supercells" });
  });
});

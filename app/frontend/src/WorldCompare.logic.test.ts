import { describe, expect, it } from "vitest";

import type {
  MountainWavesExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import {
  mapCamera,
  nearestCompareTime,
  timeIndexForSeconds,
  validateWorldCompareDescriptor,
  WORLD_COMPARE_ADAPTERS,
} from "./WorldCompare.logic";
import type { CompareSimulationDescriptor } from "./WorldCompare.types";

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
  slice_coordinate_km: 1,
  slice_native_index: 50,
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
    available_field_ids: ["ql"],
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
    const tradeLens = WORLD_COMPARE_ADAPTERS.trade_cumulus.setView(
      tradeState,
      "updraft_lens",
    );
    expect(tradeLens).toMatchObject({
      view_id: "updraft_lens",
      slice_field_id: "w",
      fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
      show_cloud_boundary: true,
      show_horizontal_wind: true,
    });

    const cloudLens = WORLD_COMPARE_ADAPTERS.mountain_waves.setView(
      mountainState,
      "wave_cloud",
    );
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

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MountainWavesExplore, mountainWavesCloudPointRendering } from "./MountainWavesExplore";
import type { MountainWavesSimulation } from "./MountainWavesWorld";

const { cloudPointColor, cloudPointOpacity, nativeCloudCellPoints } =
  mountainWavesCloudPointRendering;

const simulation: MountainWavesSimulation = {
  simulation_id: "mountain_waves_boulder_moist_reference",
  display_name: "Boulder Windstorm",
  role: "built_in",
  world_id: "mountain_waves",
  run_id: "moist-run",
  case_id: "moist-case",
  parent_simulation_id: null,
  parent_run_id: null,
  reference_simulation_id: "mountain_waves_boulder_moist_reference",
  user_question: "Where does cloud form in the wave?",
  state: "available",
  state_message: "Available",
  inspectable: true,
  can_create_variation: true,
  moist: true,
  moist_fields_available: true,
  purpose: "Moist wave reference",
  configuration: null,
  differences: {},
  warnings: [],
  caveats: ["Cloud state is instantaneous."],
  manifest_path: "/runs/moist/manifest.json",
  created_at: null,
  started_at: null,
  completed_at: null,
};

const drySimulation: MountainWavesSimulation = {
  ...simulation,
  simulation_id: "mountain_waves_dry_ridge",
  display_name: "Dry Ridge — Wave Mechanics",
  run_id: "dry-run",
  case_id: "dry-case",
  reference_simulation_id: "mountain_waves_boulder_moist_reference",
  moist: false,
  moist_fields_available: false,
  purpose: "Dry wave structure",
};

const frame = {
  schema_version: "mountain_waves_explore_v1",
  run_id: "moist-run",
  case_label: "Boulder Windstorm",
  time_index: 0,
  time_seconds: 0,
  times_seconds: [0, 180],
  dry_case: false,
  field: {
    key: "cloud_over_wave",
    display_name: "Vertical velocity",
    units: "m/s",
    derivation: "native",
  },
  values: [
    [-0.4, 0.3],
    [-0.1, 0.7],
  ],
  field_options: [
    "cloud_over_wave",
    "w",
    "cloud_liquid",
    "relative_humidity",
    "theta_perturbation",
  ],
  overlay: {
    values: [
      [0, 0.01],
      [0, 0.02],
    ],
    threshold: 0.001,
    maximum: 0.02,
  },
  pointer_context: {
    horizontal_wind_m_s: [
      [12, 15],
      [18, 21],
    ],
    vertical_velocity_m_s: [
      [-0.4, 0.3],
      [-0.1, 0.7],
    ],
    potential_temperature_k: [
      [290, 291],
      [300, 301],
    ],
    theta_perturbation_k: [
      [-0.2, 0.2],
      [-0.1, 0.3],
    ],
    cloud_liquid_g_kg: [
      [0, 0.01],
      [0, 0.02],
    ],
    relative_humidity_percent: [
      [80, 101],
      [90, 105],
    ],
  },
  viewport: {
    default_mode: "focus",
    focus_available: true,
    focus: {
      x_minimum_m: -1000,
      x_maximum_m: 1000,
      z_minimum_m: 0,
      z_maximum_m: 1500,
    },
    full: {
      x_minimum_m: -1000,
      x_maximum_m: 1000,
      z_minimum_m: 0,
      z_maximum_m: 2000,
    },
  },
  lens: {
    horizontal_wind_scale_id: "mountain_waves_horizontal_wind_v1",
    horizontal_wind_reference_m_s: 25,
    vertical_velocity_neutral_threshold_m_s: 0.1,
    potential_temperature_contour_scale_id:
      "mountain_waves_total_potential_temperature_contours_v1",
    potential_temperature_contour_interval_k: 10,
    potential_temperature_contour_values_k: [290, 300],
  },
  geometry: {
    x_center_m: [-500, 500],
    x_edge_m: [-1000, 0, 1000],
    terrain_m: [0, 300],
    scalar_height_m: [
      [500, 725],
      [1500, 1575],
    ],
    full_height_m: [
      [0, 300],
      [1000, 1150],
      [2000, 2000],
    ],
    nominal_scalar_height_m: [500, 1500],
    nominal_full_height_m: [0, 1000, 2000],
    active_top_m: 2000,
    singleton_y_m: 0,
  },
  scale: {
    fixed_across_all_times: true,
    minimum: -1,
    maximum: 1,
    selected_time_minimum: -0.4,
    selected_time_maximum: 0.7,
    palette: "blue_white_red_diverging",
    scale_id: "mountain_waves_vertical_velocity_v1",
    scale_type: "fixed_across_time_discrete",
    units: "m/s",
    breakpoints: [-0.8, -0.5, -0.1, 0.1, 0.3, 0.5, 0.7, 0.85, 0.95],
    colors: [
      "#4b0082",
      "#0057d9",
      "#00c9d8",
      "#ffffff",
      "#00d63b",
      "#8fe000",
      "#ffe000",
      "#ff9800",
      "#ff3b00",
      "#c40000",
    ],
  },
  caveats: ["Cloud state is instantaneous."],
  provenance: {
    source_history_file: "cm1out_000001.nc",
    topology: "native_2d_x_z_singleton_y",
    interpolation: "none",
    display_binning: "Native scalar samples painted between physical full-level bounds.",
    physical_height_source: "native zhval",
  },
  active_top_evidence: {
    transform_top_source: "final_nominal_zf",
    all_sources_agree: true,
    inactive_namelist_ztop_m: 2000,
  },
};

describe("MountainWavesExplore", () => {
  const originalGetContext = HTMLCanvasElement.prototype.getContext;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ok(frame)));
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      configurable: true,
      value: vi.fn(() => null),
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      configurable: true,
      value: originalGetContext,
    });
  });

  it("opens a moist Simulation in the Wave Cloud Lens with the shared scale and timeline", async () => {
    render(<MountainWavesExplore simulation={simulation} onBack={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: "Wave Cloud Lens" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("field=cloud_over_wave&time_index=-1"),
    );
    expect(screen.getByLabelText("w (m/s) legend")).toHaveTextContent(
      "Fixed across this Simulation",
    );
    expect(screen.getByLabelText("w (m/s) legend")).toHaveTextContent("u reference 25 m/s");
    expect(screen.getByLabelText("w (m/s) legend")).toHaveTextContent("ql ≥ 0.001 g/kg");
    expect(screen.getByLabelText("w (m/s) legend")).toHaveTextContent(
      "Point opacity increases with ql",
    );
    expect(screen.getByRole("button", { name: "Focus region" })).toHaveClass("active-control");
    expect(screen.getByRole("slider", { name: /Saved output/ })).toHaveAttribute("max", "1");
    expect(screen.getByText(/Select a point in the cross-section/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Wave Cloud Lens" })).toHaveLength(1);
  });

  it("switches to direct Field inspection and preserves the geometry choice", async () => {
    render(<MountainWavesExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Wave Cloud Lens" });
    fireEvent.click(screen.getByRole("button", { name: "Field" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w&time_index=-1")),
    );
    expect(screen.getAllByRole("heading", { name: "Vertical velocity" })).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "True physical scale" }));
    expect(screen.getByText(/equal x\/z physical scale/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Full domain" }));
    expect(screen.getByText(/Full domain · equal x\/z physical scale/)).toBeInTheDocument();
  });

  it("offers both Lens presets while keeping cloud-only overlays in the moist Lens", async () => {
    render(<MountainWavesExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Wave Cloud Lens" });

    expect(screen.getByRole("checkbox", { name: "Horizontal wind" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Cloud points" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Cloud boundary" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "RH = 100%" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Potential temperature" })).not.toBeChecked();
    expect(screen.queryByRole("checkbox", { name: "Cloud fill" })).not.toBeInTheDocument();
    expect(screen.getByRole("slider", { name: "Cloud opacity" })).toHaveValue("0.68");
    expect(screen.getByRole("slider", { name: "Cloud point size" })).toHaveValue("11");

    fireEvent.change(screen.getByRole("slider", { name: "Cloud opacity" }), {
      target: { value: "0.35" },
    });
    fireEvent.change(screen.getByRole("slider", { name: "Cloud point size" }), {
      target: { value: "7" },
    });
    expect(screen.getByRole("slider", { name: "Cloud opacity" })).toHaveValue("0.35");
    expect(screen.getByRole("slider", { name: "Cloud point size" })).toHaveValue("7");
    expect(screen.getByText("7px")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("checkbox", { name: "Cloud points" }));
    expect(screen.queryByRole("slider", { name: "Cloud opacity" })).not.toBeInTheDocument();
    expect(screen.queryByRole("slider", { name: "Cloud point size" })).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Cloud boundary" })).toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: "Wave Structure Lens" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w&time_index=-1")),
    );
    expect(screen.queryByRole("checkbox", { name: "Cloud points" })).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: "RH = 100%" })).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Potential temperature" })).toBeChecked();
    expect(screen.getByRole("heading", { name: "Wave Structure Lens" })).toBeInTheDocument();
  });

  it("opens a dry Simulation in the Wave Structure Lens without moist-only controls", async () => {
    vi.mocked(fetch).mockResolvedValue(
      ok({
        ...frame,
        dry_case: true,
        field: { ...frame.field, key: "w" },
        field_options: ["w", "theta_perturbation"],
        overlay: null,
        pointer_context: {
          ...frame.pointer_context,
          cloud_liquid_g_kg: null,
          relative_humidity_percent: null,
        },
        viewport: {
          default_mode: "full",
          focus_available: false,
          focus: frame.viewport.full,
          full: frame.viewport.full,
        },
      }),
    );

    render(<MountainWavesExplore simulation={drySimulation} onBack={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: "Wave Structure Lens" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("field=w&time_index=-1"));
    expect(screen.queryByRole("button", { name: "Wave Cloud Lens" })).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: "Cloud boundary" })).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Horizontal wind" })).toBeChecked();
  });

  it("ignores a stale frame response after a rapid Field change", async () => {
    render(<MountainWavesExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Wave Cloud Lens" });

    let resolveW: ((response: Response) => void) | undefined;
    let resolveCloud: ((response: Response) => void) | undefined;
    vi.mocked(fetch).mockImplementation((input) => {
      const url = String(input);
      if (url.includes("field=cloud_liquid")) {
        return new Promise((resolve) => {
          resolveCloud = resolve;
        });
      }
      return new Promise((resolve) => {
        resolveW = resolve;
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "Field" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Field" }), {
      target: { value: "cloud_liquid" },
    });
    resolveCloud?.(
      ok({
        ...frame,
        field: {
          ...frame.field,
          key: "cloud_liquid",
          display_name: "Cloud liquid water",
          units: "g/kg",
        },
        overlay: null,
      }),
    );
    expect(await screen.findByRole("heading", { name: "Cloud liquid water" })).toBeInTheDocument();

    resolveW?.(ok({ ...frame, field: { ...frame.field, key: "w" }, overlay: null }));
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    expect(screen.getAllByRole("heading", { name: "Cloud liquid water" })).toHaveLength(2);
  });
});

describe("Mountain Waves cloud-point rendering", () => {
  it("uses one native scalar-cell center for every value meeting the cloud threshold", () => {
    const points = nativeCloudCellPoints({
      overlay: {
        threshold: 0.001,
        maximum: 0.02,
        values: [
          [0.001, 0.0009],
          [Number.NaN, 0.02],
        ],
      },
      geometry: frame.geometry,
    });

    expect(points).toEqual([
      { xM: -500, zM: 500, valueGKg: 0.001 },
      { xM: 500, zM: 1575, valueGKg: 0.02 },
    ]);
  });

  it("keeps a visible opacity floor and increases opacity and color intensity with ql", () => {
    const thresholdOpacity = cloudPointOpacity(0.001, 0.001, 0.02, 0.68);
    const middleOpacity = cloudPointOpacity(0.01, 0.001, 0.02, 0.68);
    const maximumOpacity = cloudPointOpacity(0.02, 0.001, 0.02, 0.68);

    expect(thresholdOpacity).toBeCloseTo(0.204);
    expect(middleOpacity).toBeGreaterThan(thresholdOpacity);
    expect(maximumOpacity).toBeCloseTo(0.68);
    expect(cloudPointColor(0.001, 0.001, 0.02)).toBe("rgb(61, 168, 199)");
    expect(cloudPointColor(0.02, 0.001, 0.02)).toBe("rgb(201, 245, 245)");
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

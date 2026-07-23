import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  StormExaminationResearch,
  stormExaminationRendering,
  type StormExaminationFrame,
} from "./StormExaminationResearch";

const wScale = {
  scale_id: "storm_midlevel_w_v1",
  display_name: "Vertical velocity",
  units: "m/s",
  scale_type: "fixed_discrete" as const,
  minimum: -30,
  maximum: 30,
  breakpoints: [-24, -18, -12, -6, 6, 12, 18, 24, 27],
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
  fixed_across_time: true,
};

function layer(key = "winterp", displayName = "Vertical velocity") {
  return {
    key,
    display_name: displayName,
    units: "m/s",
    evidence_kind: "native" as const,
    source_fields: [key],
    derivation: null,
    values: [
      [-4, 3],
      [0, 12],
    ],
    selected_frame_minimum: -4,
    selected_frame_maximum: 12,
    scale: wScale,
  };
}

const frame: StormExaminationFrame = {
  schema_version: "storm_examination_gate_c_v1",
  authority_state: "issue_418_gate_c_research_not_product",
  world_id: null,
  simulation_id: null,
  run_id: "quarter-circle-supercell-official-20260722T142521Z",
  case_id: "cm1_r21_1_quarter_circle_supercell_official_v0",
  simulation_label: "Official CM1 r21.1 quarter-circle benchmark",
  lens_id: "rotating_updraft",
  lens_name: "Rotating Updraft",
  lens_question: "Where is the storm rising and rotating as one organized structure?",
  what_to_notice_now: "The rotating core is organized at this saved output.",
  time_index: 5,
  time_seconds: 4500,
  times_seconds: [0, 900, 1800, 2700, 3600, 4500, 5400, 6300, 7200],
  mature_checkpoint_indices: [3, 4, 5, 6, 7, 8],
  timeline_checkpoints: [
    {
      time_seconds: 4500,
      label: "75 min",
      phase: "Dominant primary with secondary structure",
      phase_kind: "visible_checkpoint",
    },
  ],
  viewport: "storm",
  viewport_bounds_km: { x_min: -30, x_max: 30, y_min: -30, y_max: 30 },
  primary_updraft: {
    x_index: 1,
    y_index: 1,
    z_index: 1,
    x_km: 10,
    y_km: 10,
    z_km: 3.25,
    w_m_s: 48,
  },
  selected_point: {
    x_index: 1,
    y_index: 1,
    z_index: 1,
    x_km: 10,
    y_km: 10,
    z_km: 3.25,
    model_time_seconds: 4500,
    coordinate_frame: "translating model frame; native model-relative winds",
    values: {
      vertical_velocity: 12,
      vertical_vorticity: 0.03,
      reflectivity: 52,
      cloud_liquid: 1.2,
      rain_water: 2.1,
      cloud_ice: 0.4,
      snow: 0.8,
      hail_treated_large_ice: 1.5,
      total_condensate: 6,
      accumulated_surface_rain: 22,
      model_relative_u: 14,
      model_relative_v: 7,
      updraft_helicity: 510,
    },
    units: {
      vertical_velocity: "m/s",
      vertical_vorticity: "s^-1",
      reflectivity: "dBZ",
      cloud_liquid: "g/kg",
      rain_water: "g/kg",
      cloud_ice: "g/kg",
      snow: "g/kg",
      hail_treated_large_ice: "g/kg",
      total_condensate: "g/kg",
      accumulated_surface_rain: "mm",
      model_relative_u: "m/s",
      model_relative_v: "m/s",
      updraft_helicity: "m^2/s^2",
    },
    evidence_kind: {
      vertical_velocity: "native",
      vertical_vorticity: "native",
      reflectivity: "native",
      cloud_liquid: "native",
      rain_water: "native",
      cloud_ice: "native",
      snow: "native",
      hail_treated_large_ice: "native",
      total_condensate: "derived",
      accumulated_surface_rain: "derived",
      model_relative_u: "native",
      model_relative_v: "native",
      updraft_helicity: "native",
    },
    states: ["Rising", "Condensate present", "Rain footprint"],
    distance_to_primary_updraft_km: 0,
  },
  plan: {
    title: "Midlevel updraft and rotation",
    subtitle: "Signed vertical velocity with rotation",
    x_indices: [0, 1],
    y_indices: [0, 1],
    x_km: [-10, 10],
    y_km: [-10, 10],
    level_index: 1,
    level_km: 3.25,
    selection_z_indices: null,
    primary: layer(),
    overlays: {
      vertical_vorticity: layer("zvort", "Vertical vorticity"),
      updraft_helicity: layer("uh", "Updraft helicity"),
      vertical_velocity: layer("winterp", "Vertical velocity"),
      composite_reflectivity: layer("dbz", "Reflectivity"),
      accumulated_surface_rain: layer("rain", "Rain"),
      total_condensate: layer("total_condensate", "Total condensate"),
      low_level_precipitating_condensate: layer(
        "precipitating_condensate",
        "Current precipitating condensate",
      ),
    },
    categories: null,
    wind_vectors: [{ x_km: 0, y_km: 0, u_m_s: 12, v_m_s: 5, magnitude_m_s: 13 }],
  },
  xz_section: {
    orientation: "xz",
    title: "x-z section at y = 10.0 km",
    horizontal_dimension: "x",
    horizontal_indices: [0, 1],
    horizontal_km: [-10, 10],
    z_km: [0.25, 3.25],
    cross_section_coordinate_km: 10,
    primary: layer(),
    overlays: {
      vertical_vorticity: layer("zvort", "Vertical vorticity"),
      total_condensate: layer("total_condensate", "Total condensate"),
      precipitating_condensate: layer("precipitating_condensate", "Precipitating condensate"),
      reflectivity: layer("dbz", "Reflectivity"),
      vertical_velocity: layer(),
    },
    categories: null,
  },
  yz_section: {
    orientation: "yz",
    title: "y-z section at x = 10.0 km",
    horizontal_dimension: "y",
    horizontal_indices: [0, 1],
    horizontal_km: [-10, 10],
    z_km: [0.25, 3.25],
    cross_section_coordinate_km: 10,
    primary: layer(),
    overlays: {
      vertical_vorticity: layer("zvort", "Vertical vorticity"),
      total_condensate: layer("total_condensate", "Total condensate"),
      precipitating_condensate: layer("precipitating_condensate", "Precipitating condensate"),
      reflectivity: layer("dbz", "Reflectivity"),
      vertical_velocity: layer(),
    },
    categories: null,
  },
  scene: null,
  caveats: [
    "Saved histories are 15 minutes apart.",
    "Coordinates are in the translating model frame.",
    "Secondary structures are present.",
    "The Rayleigh layer overlaps upper storm structure.",
    "Low-level fields do not by themselves establish a cold pool.",
  ],
  provenance: {
    source_history_file: "cm1out_000006.nc",
    interpolation: "none",
  },
  extraction_milliseconds: 115,
};

function responseFor(url: string): StormExaminationFrame {
  const search = new URL(url, "http://localhost").searchParams;
  const lens = (search.get("lens") ?? "rotating_updraft") as StormExaminationFrame["lens_id"];
  const names = {
    rotating_updraft: "Rotating Updraft",
    cloud_precipitation: "Cloud and Precipitation",
    low_level_interactions: "Low-Level Interactions",
  };
  return {
    ...frame,
    lens_id: lens,
    lens_name: names[lens],
    lens_question:
      lens === "low_level_interactions"
        ? "How do low-level ascent, descent, rain, and horizontal flow meet beneath the storm?"
        : frame.lens_question,
  };
}

describe("StormExaminationResearch", () => {
  const originalGetContext = HTMLCanvasElement.prototype.getContext;
  const originalBounds = HTMLCanvasElement.prototype.getBoundingClientRect;

  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((url: string) =>
          Promise.resolve({ ok: true, json: () => Promise.resolve(responseFor(url)) }),
        ),
    );
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
    Object.defineProperty(HTMLCanvasElement.prototype, "getBoundingClientRect", {
      configurable: true,
      value: () => ({ width: 500, height: 300, left: 0, top: 0, right: 500, bottom: 300 }),
    });
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      configurable: true,
      value: () => ({
        setTransform: vi.fn(),
        clearRect: vi.fn(),
        fillRect: vi.fn(),
        strokeRect: vi.fn(),
        fillText: vi.fn(),
        measureText: () => ({ width: 20 }),
        save: vi.fn(),
        restore: vi.fn(),
        beginPath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        stroke: vi.fn(),
        fill: vi.fn(),
        closePath: vi.fn(),
        arc: vi.fn(),
        setLineDash: vi.fn(),
      }),
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
    Object.defineProperty(HTMLCanvasElement.prototype, "getBoundingClientRect", {
      configurable: true,
      value: originalBounds,
    });
  });

  it("opens the mature result in the Rotating Updraft Lens with fixed-scale evidence", async () => {
    render(<StormExaminationResearch />);

    expect(await screen.findByRole("heading", { name: "Rotating Updraft" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("lens=rotating_updraft&viewport=storm&time_index=5"),
      expect.anything(),
    );
    expect(screen.getByLabelText("Vertical velocity legend")).toHaveTextContent(
      "Fixed across all retained times",
    );
    expect(screen.getByText("Dominant primary with secondary structure")).toBeInTheDocument();
    expect(screen.getByText("Rising")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Rotating Updraft" })).toHaveLength(1);
  });

  it("switches among all three candidate Lenses and exposes their bounded controls", async () => {
    render(<StormExaminationResearch />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    fireEvent.click(screen.getByRole("button", { name: "Cloud and Precipitation" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("lens=cloud_precipitation"),
        expect.anything(),
      ),
    );
    expect(screen.getByRole("checkbox", { name: "Vertical-motion contours" })).toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: "Low-Level Interactions" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("lens=low_level_interactions"),
        expect.anything(),
      ),
    );
    expect(screen.getByRole("checkbox", { name: "Accumulated rain" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Model-relative flow" })).toBeChecked();
    expect(screen.getAllByText(/do not by themselves establish a cold pool/i)).toHaveLength(2);
  });

  it("coordinates a clicked plan point and supports the shared mature timeline", async () => {
    render(<StormExaminationResearch />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    fireEvent.click(screen.getByLabelText("Midlevel updraft and rotation plan view"), {
      clientX: 250,
      clientY: 150,
      offsetX: 250,
      offsetY: 150,
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("x_index="), expect.anything()),
    );
    expect(screen.getByRole("button", { name: "Return to strongest updraft" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Next saved output" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("time_index=6"),
        expect.anything(),
      ),
    );
  });

  it("fails locally when retained evidence is unavailable and retries without leaving the page", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      json: () =>
        Promise.resolve({ detail: "The accepted Gate B retained output is unavailable." }),
    } as Response);

    render(<StormExaminationResearch />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The accepted Gate B retained output is unavailable.",
    );
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByRole("heading", { name: "Rotating Updraft" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});

describe("stormExaminationRendering", () => {
  it("preserves the signed fixed-scale colors and nearest native index", () => {
    expect(stormExaminationRendering.scaleColor(-30, wScale)).toBe("#4b0082");
    expect(stormExaminationRendering.scaleColor(30, wScale)).toBe("#c40000");
    expect(stormExaminationRendering.nearestIndex([-2, 0, 2], 0.7)).toBe(1);
  });
});

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SupercellsExplore } from "./SupercellsExplore";
import type {
  FieldLayer,
  LensId,
  StormExaminationFrame,
  VolumeLayer,
} from "./StormExaminationResearch";
import type { SupercellSimulation } from "./SupercellsWorld";

vi.mock("./True3DViewer", () => ({
  True3DViewer: ({
    fieldLabel,
    activeSliceLabel,
    maximized,
    onToggleMaximize,
    onSelectStormPoint,
    compactDisplayControls,
    cameraPreset,
    cameraTransform,
    onCameraTransformChange,
    windOverlayLabel,
  }: {
    fieldLabel: string;
    activeSliceLabel: string;
    maximized: boolean;
    onToggleMaximize: () => void;
    onSelectStormPoint: (point: [number, number, number, number, number]) => void;
    compactDisplayControls: ReactNode;
    cameraPreset: string;
    cameraTransform: {
      position: [number, number, number];
      target: [number, number, number];
      up: [number, number, number];
    } | null;
    onCameraTransformChange: (transform: {
      position: [number, number, number];
      target: [number, number, number];
      up: [number, number, number];
    }) => void;
    windOverlayLabel?: string;
  }) => (
    <section aria-label="Mock 3-D storm scene">
      <h2>{fieldLabel}</h2>
      <p>{activeSliceLabel}</p>
      <p>Camera: {cameraPreset}</p>
      <p>Camera position: {cameraTransform?.position.join(",") ?? "default"}</p>
      {windOverlayLabel && <p>{windOverlayLabel}</p>}
      <button
        type="button"
        onClick={() =>
          onCameraTransformChange({
            position: [4, 5, 6],
            target: [1, 2, 3],
            up: [0, 1, 0],
          })
        }
      >
        Move mock camera
      </button>
      <button type="button" onClick={() => onSelectStormPoint([9.1, 19.1, 3.1, 12, 0])}>
        Select 3-D point
      </button>
      <button type="button" onClick={onToggleMaximize}>
        {maximized ? "Restore scene" : "Maximize scene"}
      </button>
      {compactDisplayControls}
    </section>
  ),
}));

const simulation: SupercellSimulation = {
  simulation_id: "supercells_quarter_circle_reference",
  display_name: "Quarter-Circle Supercell",
  role: "reference",
  world_id: "supercells",
  run_id: "quarter-circle-supercell-presentation-v1-20260723",
  case_id: "cm1_r21_1_quarter_circle_supercell_presentation_v1",
  technical_state: "available",
  technical_state_message: "Available",
  explore_available: true,
  saved_output_count: 91,
  model_start_seconds: 0,
  model_end_seconds: 10_800,
  history_cadence_seconds: 120,
  default_explore_time_index: 37,
  lineage_state: "known",
};

const wScale = {
  scale_id: "supercells_vertical_velocity_v1",
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

function field(key = "winterp", displayName = "Vertical velocity"): FieldLayer {
  return {
    key,
    display_name: displayName,
    units: key === "dbz" ? "dBZ" : "m/s",
    evidence_kind: "native",
    source_fields: [key],
    derivation: null,
    values: [
      [-5, 3, 8],
      [0, 12, -2],
      [2, 7, -8],
    ],
    selected_frame_minimum: -8,
    selected_frame_maximum: 12,
    scale: wScale,
  };
}

function sceneLayers(lens: LensId): VolumeLayer[] {
  const base = {
    units: "m/s",
    evidence_kind: "native" as const,
    source_fields: ["winterp"],
    derivation: null,
    points: [
      [-10, -10, 1, -8, 0],
      [0, 0, 4, 18, 0],
      [10, 20, 8, 8, 0],
    ] as Array<[number, number, number, number, number]>,
    source_count: 3,
    returned_count: 3,
    threshold_label: "Fixed retained-run scale",
    default_opacity: 0.8,
    default_point_size: 1,
    scale: wScale,
    categories: [],
  };
  if (lens === "cloud_precipitation") {
    return [
      {
        ...base,
        key: "hydrometeor_categories",
        display_name: "Dominant hydrometeor",
        units: "g/kg",
        source_fields: ["qc", "qr", "qi", "qs", "qg"],
        rendering: "categorical",
        points: [
          [-10, -10, 1, 0.4, 1],
          [0, 0, 4, 1.2, 2],
          [10, 20, 8, 2.1, 5],
        ],
        default_visible: true,
        scale: null,
        categories: [
          { code: 1, key: "qc", label: "Cloud liquid", color: "#d6f0f7" },
          { code: 2, key: "qr", label: "Rain", color: "#2f7fb5" },
          { code: 5, key: "qg", label: "Hail-treated large ice", color: "#7c4d8f" },
        ],
      },
    ];
  }
  if (lens === "low_level_interactions") {
    return [
      {
        ...base,
        key: "storm_cloud_body",
        display_name: "Storm cloud body",
        rendering: "neutral_cloud",
        default_visible: false,
        scale: null,
      },
      {
        ...base,
        key: "low_level_vertical_motion",
        display_name: "Low-level vertical motion",
        rendering: "signed_scalar",
        default_visible: true,
      },
      {
        ...base,
        key: "accumulated_surface_rain",
        display_name: "Accumulated rain",
        units: "mm",
        rendering: "scalar",
        default_visible: true,
      },
      {
        ...base,
        key: "precipitating_condensate",
        display_name: "Low-level precipitating condensate",
        units: "g/kg",
        rendering: "scalar",
        default_visible: true,
      },
    ];
  }
  return [
    {
      ...base,
      key: "storm_cloud_body",
      display_name: "Storm cloud body",
      rendering: "neutral_cloud",
      default_visible: true,
      scale: null,
    },
    {
      ...base,
      key: "rising_core",
      display_name: "Rising core",
      rendering: "signed_scalar",
      default_visible: true,
    },
    {
      ...base,
      key: "strong_descent",
      display_name: "Strong descent",
      rendering: "signed_scalar",
      default_visible: false,
    },
    {
      ...base,
      key: "cyclonic_rotation",
      display_name: "Cyclonic rotation",
      rendering: "scalar",
      default_visible: true,
    },
    {
      ...base,
      key: "updraft_helicity",
      display_name: "2-5 km updraft helicity",
      rendering: "scalar",
      default_visible: true,
    },
  ];
}

function frameFor(url: string): StormExaminationFrame {
  const search = new URL(url, "http://localhost").searchParams;
  const lens = (search.get("lens") ?? "rotating_updraft") as LensId;
  const viewport = search.get("viewport") === "full" ? "full" : "storm";
  const timeIndex = Number(search.get("time_index") ?? 37);
  const times = Array.from({ length: 91 }, (_value, index) => index * 120);
  const xIndex = Number(search.get("x_index") ?? 1);
  const yIndex = Number(search.get("y_index") ?? 1);
  const zIndex = Number(search.get("z_index") ?? 1);
  const xCoordinates = [-10, 0, 10];
  const yCoordinates = [-10, 10, 20];
  const zCoordinates = [0.5, 3, 8];
  const names = {
    rotating_updraft: "Rotating Updraft",
    cloud_precipitation: "Cloud and Precipitation",
    low_level_interactions: "Low-Level Interactions",
  };
  return {
    schema_version: "supercells_explore_v1",
    authority_state: "supercells_product_world",
    world_id: "supercells",
    simulation_id: "supercells_quarter_circle_reference",
    run_id: simulation.run_id,
    case_id: simulation.case_id,
    simulation_label: simulation.display_name,
    lens_id: lens,
    lens_name: names[lens],
    lens_question:
      lens === "rotating_updraft"
        ? "Where is the storm rising and rotating as one organized structure?"
        : lens === "cloud_precipitation"
          ? "How are cloud and precipitation organized through the storm?"
          : "How do ascent, descent, rain, and horizontal flow meet beneath the storm?",
    what_to_notice_now: "This saved output contains coordinated frame-specific evidence.",
    what_to_notice_by_view: {
      plan: "Plan evidence at this saved output.",
      xz: "X-z evidence at this saved output.",
      yz: "Y-z evidence at this saved output.",
    },
    time_index: timeIndex,
    time_seconds: times[timeIndex],
    times_seconds: times,
    mature_checkpoint_indices: [22, 30, 37, 45, 52, 60],
    timeline_checkpoints: [
      {
        time_seconds: 4_440,
        label: "74 min",
        phase: "Organized mature storm",
        phase_kind: "visible_checkpoint",
      },
    ],
    viewport,
    viewport_bounds_km:
      viewport === "storm"
        ? { x_min: -30, x_max: 30, y_min: -30, y_max: 30 }
        : { x_min: -60, x_max: 60, y_min: -60, y_max: 60 },
    primary_updraft: {
      x_index: 1,
      y_index: 1,
      z_index: 1,
      x_km: 0,
      y_km: 10,
      z_km: 3,
      w_m_s: 48,
    },
    selected_point: {
      x_index: xIndex,
      y_index: yIndex,
      z_index: zIndex,
      x_km: xCoordinates[xIndex] ?? 0,
      y_km: yCoordinates[yIndex] ?? 10,
      z_km: zCoordinates[zIndex] ?? 3,
      model_time_seconds: times[timeIndex],
      coordinate_frame: "translating model frame; native model-relative winds",
      values: {
        vertical_velocity: 12,
        vertical_vorticity: 0.03,
        updraft_helicity: 510,
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
      },
      units: {
        vertical_velocity: "m/s",
        vertical_vorticity: "s^-1",
        updraft_helicity: "m^2/s^2",
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
      },
      evidence_kind: {
        vertical_velocity: "native",
        vertical_vorticity: "native",
        updraft_helicity: "native",
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
      },
      states: ["Rising", "Rotating", "Condensate present"],
      distance_to_primary_updraft_km: 0,
    },
    plan: {
      title: lens === "cloud_precipitation" ? "Hydrometeor plan" : "Updraft and rotation",
      subtitle: "Native-grid plan evidence",
      x_indices: [0, 1, 2],
      y_indices: [0, 1, 2],
      x_km: xCoordinates,
      y_km: yCoordinates,
      level_index: zIndex,
      level_km: zCoordinates[zIndex] ?? 3,
      selection_z_indices:
        lens === "cloud_precipitation"
          ? [
              [0, 2, 2],
              [1, 2, 1],
              [0, 1, 2],
            ]
          : null,
      primary: field(),
      overlays: {
        vertical_vorticity: field("zvort", "Vertical vorticity"),
        updraft_helicity: field("uh", "Updraft helicity"),
        vertical_velocity: field("winterp", "Vertical velocity"),
        composite_reflectivity: field("dbz", "Reflectivity"),
        accumulated_surface_rain: field("rain", "Accumulated rain"),
        total_condensate: field("total_condensate", "Total condensate"),
        low_level_precipitating_condensate: field(
          "precipitating_condensate",
          "Current precipitating condensate",
        ),
      },
      categories: null,
      wind_vectors: [{ x_km: 0, y_km: 10, u_m_s: 12, v_m_s: 5, magnitude_m_s: 13 }],
    },
    xz_section: section("xz", "x", yCoordinates[yIndex] ?? 10),
    yz_section: section("yz", "y", xCoordinates[xIndex] ?? 0),
    scene: {
      coordinate_extents_km: {
        x: { min: viewport === "storm" ? -30 : -60, max: viewport === "storm" ? 30 : 60 },
        y: { min: viewport === "storm" ? -30 : -60, max: viewport === "storm" ? 30 : 60 },
        z: { min: 0.25, max: lens === "low_level_interactions" ? 5.25 : 19.75 },
      },
      coordinate_sizes: { x: 120, y: 120, z: 40 },
      coordinate_indices: { x: [0, 1, 2], y: [0, 1, 2], z: [0, 1, 2] },
      coordinate_values_km: {
        x: xCoordinates,
        y: yCoordinates,
        z: zCoordinates,
      },
      layers: sceneLayers(lens),
      wind_vectors:
        lens === "low_level_interactions"
          ? [
              {
                x_km: 0,
                y_km: 10,
                z_km: zCoordinates[zIndex] ?? 3,
                u_m_s: 12,
                v_m_s: 5,
                magnitude_m_s: 13,
              },
            ]
          : [],
      wind_reference_m_s: 25,
      point_budget: 20_000,
      source_history_file: `cm1out_${String(timeIndex + 1).padStart(6, "0")}.nc`,
    },
    caveats: ["Saved histories are 2 minutes apart."],
    provenance: { source_history_file: `cm1out_${String(timeIndex + 1).padStart(6, "0")}.nc` },
    extraction_milliseconds: 120,
  };
}

function section(orientation: "xz" | "yz", horizontal: "x" | "y", coordinate: number) {
  return {
    orientation,
    title: `${orientation} section at ${orientation === "xz" ? "y" : "x"} = ${coordinate.toFixed(1)} km`,
    horizontal_dimension: horizontal,
    horizontal_indices: [0, 1, 2],
    horizontal_km: [-10, 0, 10],
    z_km: [0.5, 3, 8],
    cross_section_coordinate_km: coordinate,
    primary: field(),
    overlays: {
      total_condensate: field("total_condensate", "Total condensate"),
      precipitating_condensate: field("precipitating_condensate", "Precipitating condensate"),
      reflectivity: field("dbz", "Reflectivity"),
      vertical_velocity: field(),
      vertical_vorticity: field("zvort", "Vertical vorticity"),
    },
    categories: null,
  };
}

describe("SupercellsExplore", () => {
  const originalGetContext = HTMLCanvasElement.prototype.getContext;
  const originalBounds = HTMLCanvasElement.prototype.getBoundingClientRect;

  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => Promise.resolve(ok(frameFor(String(input))))),
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
      value: () => canvasContext(),
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

  it("opens at the mature Rotating Updraft frame with the complete retained timeline", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);

    expect(await screen.findByRole("heading", { name: "Rotating Updraft" })).toBeVisible();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("lens=rotating_updraft&viewport=storm&time_index=37"),
      expect.anything(),
    );
    expect(screen.getByLabelText("Saved output time")).toHaveAttribute("max", "90");
    expect(screen.getByText("frame 38 of 91 · Organized mature storm")).toBeVisible();
    expect(screen.getByRole("button", { name: "Rotating Updraft" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByLabelText("Mock 3-D storm scene")).toHaveTextContent("Camera: look_along_y");
  });

  it("moves each evidence orientation through native planes and keeps a user plane across time", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    const horizontalPosition = screen.getByLabelText("Horizontal x-y z position");
    expect(horizontalPosition).toHaveValue("1");
    expect(screen.getByText("z 3.00 km")).toBeVisible();
    expect(screen.getByText("native index 1")).toBeVisible();

    fireEvent.change(horizontalPosition, { target: { value: "0" } });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=1&y_index=1&z_index=0/),
        expect.anything(),
      ),
    );
    expect(screen.getByLabelText("Horizontal x-y z position")).toHaveValue("0");
    expect(await screen.findByText("z 0.50 km")).toBeVisible();
    expect(screen.getByText("native index 0")).toBeVisible();

    fireEvent.change(screen.getByLabelText("Horizontal x-y z position"), {
      target: { value: "2" },
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=1&y_index=1&z_index=2/),
        expect.anything(),
      ),
    );
    expect(await screen.findByText("z 8.00 km")).toBeVisible();
    expect(screen.getByText("native index 2")).toBeVisible();

    const orientation = within(screen.getByLabelText("Slice orientation"));
    fireEvent.click(orientation.getByRole("button", { name: "Vertical x-z" }));
    expect(screen.getByLabelText("Vertical x-z y position")).toHaveValue("1");
    fireEvent.change(screen.getByLabelText("Vertical x-z y position"), {
      target: { value: "0" },
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=1&y_index=0&z_index=2/),
        expect.anything(),
      ),
    );
    expect(await screen.findByText("y -10.0 km")).toBeVisible();
    expect(screen.getByText("native index 0")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Next saved output" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/time_index=38&x_index=1&y_index=0&z_index=2/),
        expect.anything(),
      ),
    );
    expect(screen.getByLabelText("Vertical x-z y position")).toHaveValue("0");

    fireEvent.click(orientation.getByRole("button", { name: "Vertical y-z" }));
    fireEvent.change(screen.getByLabelText("Vertical y-z x position"), {
      target: { value: "2" },
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=2&y_index=0&z_index=2/),
        expect.anything(),
      ),
    );
    expect(await screen.findByText("x 10.0 km")).toBeVisible();
    expect(screen.getByText("native index 2")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Return slice to curated position" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/lens=rotating_updraft&viewport=storm&time_index=38$/),
        expect.anything(),
      ),
    );
  });

  it("keeps rapid cross-axis slice changes in one local native selection", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    vi.mocked(fetch).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (/x_index=1&y_index=1&z_index=2/.test(url)) {
        return new Promise<Response>(() => {});
      }
      return Promise.resolve(ok(frameFor(url)));
    });

    fireEvent.change(screen.getByLabelText("Horizontal x-y z position"), {
      target: { value: "2" },
    });
    fireEvent.click(
      within(screen.getByLabelText("Slice orientation")).getByRole("button", {
        name: "Vertical x-z",
      }),
    );
    fireEvent.change(screen.getByLabelText("Vertical x-z y position"), {
      target: { value: "0" },
    });

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=1&y_index=0&z_index=2/),
        expect.anything(),
      ),
    );
  });

  it("uses the selected Low-Level altitude in 2-D and 3-D labels", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    fireEvent.click(screen.getByRole("button", { name: "Low-Level Interactions" }));
    await screen.findByRole("heading", { name: "Low-Level Interactions" });
    fireEvent.change(screen.getByLabelText("Horizontal x-y z position"), {
      target: { value: "2" },
    });

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/lens=low_level_interactions.*z_index=2/),
        expect.anything(),
      ),
    );
    expect(
      await screen.findAllByText("Model-relative wind at z = 8.00 km"),
    ).not.toHaveLength(0);
    expect(screen.getByText(/x-y slice at z = 8.00 km coordinate current motion/)).toBeVisible();
    expect(screen.getByText("Model-relative flow at z = 8.00 km")).toBeVisible();
  });

  it("keeps a user-framed camera transform per Lens across ordinary workspace changes", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    expect(screen.getByText("Camera position: default")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Move mock camera" }));
    expect(screen.getByText("Camera position: 4,5,6")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Maximize scene" }));
    expect(screen.getByText("Camera position: 4,5,6")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Restore scene" }));
    fireEvent.click(screen.getByRole("button", { name: "Next saved output" }));
    expect(screen.getByText("Camera position: 4,5,6")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Cloud and Precipitation" }));
    await screen.findByRole("heading", { name: "Cloud and Precipitation" });
    expect(screen.getByText("Camera position: default")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Rotating Updraft" }));
    await screen.findByRole("heading", { name: "Rotating Updraft" });
    expect(screen.getByText("Camera position: 4,5,6")).toBeVisible();
  });

  it("keeps lens defaults, viewport, evidence orientation, and native selection synchronized", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    fireEvent.click(screen.getByRole("button", { name: "Cloud and Precipitation" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("lens=cloud_precipitation&viewport=storm&time_index=37"),
        expect.anything(),
      ),
    );
    expect(await screen.findByRole("heading", { name: "Cloud and Precipitation" })).toBeVisible();
    await waitFor(() => expect(screen.getByLabelText("Dominant hydrometeor")).toBeChecked());
    expect(screen.getByLabelText("Vertical-motion contours")).toBeChecked();
    expect(screen.getByText("X-z evidence at this saved output.")).toBeVisible();
    expect(
      screen.getByText(/This storm-core native section shows the dominant hydrometeor/),
    ).toBeVisible();

    const orientation = within(screen.getByLabelText("Slice orientation"));
    expect(orientation.getByRole("button", { name: "Vertical x-z" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect((await screen.findAllByText("xz section at y = 10.0 km")).length).toBeGreaterThan(1);
    expect(screen.getByLabelText("Mock 3-D storm scene")).toHaveTextContent(
      "xz section at y = 10.0 km",
    );
    fireEvent.click(orientation.getByRole("button", { name: "Horizontal x-y" }));
    fireEvent.click(screen.getByLabelText("Hydrometeor plan plan view"), {
      clientX: 250,
      clientY: 150,
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=1&y_index=0&z_index=2/),
        expect.anything(),
      ),
    );
    fireEvent.click(orientation.getByRole("button", { name: "Vertical y-z" }));
    expect((await screen.findAllByText("yz section at x = 0.0 km")).length).toBeGreaterThan(1);
    expect(screen.getByText("Y-z evidence at this saved output.")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Rotating Updraft" }));
    await screen.findByRole("heading", { name: "Rotating Updraft" });
    fireEvent.click(screen.getByRole("button", { name: "Cloud and Precipitation" }));
    await screen.findByRole("heading", { name: "Cloud and Precipitation" });
    expect(
      within(screen.getByLabelText("Slice orientation")).getByRole("button", {
        name: "Vertical y-z",
      }),
    ).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "Full domain" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("lens=cloud_precipitation&viewport=full&time_index=37"),
        expect.anything(),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Select 3-D point" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=2&y_index=2&z_index=1/),
        expect.anything(),
      ),
    );
    expect(screen.getByLabelText("Vertical y-z x position")).toHaveValue("2");
    fireEvent.click(orientation.getByRole("button", { name: "Vertical x-z" }));
    expect(screen.getByLabelText("Vertical x-z y position")).toHaveValue("2");
    fireEvent.change(screen.getByLabelText("Vertical x-z y position"), {
      target: { value: "1" },
    });
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/x_index=2&y_index=1&z_index=1/),
        expect.anything(),
      ),
    );
    expect(screen.getByLabelText("Mock 3-D storm scene")).toHaveTextContent(
      "xz section at y = 10.0 km",
    );
    fireEvent.click(screen.getByRole("tab", { name: "Science" }));
    expect(await screen.findByText("Selected point")).toBeVisible();
    expect(screen.getByRole("heading", { name: "x 10.0, y 10.0, z 3.00 km" })).toBeVisible();
  });

  it("preserves the lens and time while maximizing and restoring either scientific view", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    fireEvent.change(screen.getByLabelText("Saved output time"), { target: { value: "90" } });
    expect(await screen.findByText("180 min · 10,800 s")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Maximize scene" }));
    expect(screen.getByLabelText("Supercells integrated Explore workspace")).toHaveClass(
      "supercells-explore-focused-scene",
    );
    expect(screen.getByRole("button", { name: "Restore scene" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Restore scene" }));

    fireEvent.click(screen.getByRole("button", { name: "Maximize evidence" }));
    expect(screen.getByLabelText("Supercells integrated Explore workspace")).toHaveClass(
      "supercells-explore-focused-evidence",
    );
    expect(screen.getByRole("button", { name: "Open Context" })).toBeVisible();
    expect(screen.queryByLabelText("Explore inspector")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open Context" }));
    expect(screen.getByLabelText("Explore inspector")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Restore evidence" }));

    expect(screen.getByRole("button", { name: "Rotating Updraft" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByLabelText("Saved output time")).toHaveValue("90");
  });

  it("offers the shared Explain, Science, Notes, and Details inspector grammar", async () => {
    render(<SupercellsExplore simulation={simulation} onBack={vi.fn()} />);
    await screen.findByRole("heading", { name: "Rotating Updraft" });

    const inspector = screen.getByLabelText("Explore inspector");
    for (const name of ["Explain", "Science", "Notes", "Details"]) {
      expect(within(inspector).getByRole("tab", { name })).toBeVisible();
    }
    fireEvent.click(within(inspector).getByRole("tab", { name: "Notes" }));
    expect(screen.getByRole("heading", { name: "Simulation notes" })).toBeVisible();
    fireEvent.click(within(inspector).getByRole("tab", { name: "Details" }));
    expect(screen.getByRole("heading", { name: "Simulation details" })).toBeVisible();
  });
});

function canvasContext() {
  return {
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
  };
}

function ok(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

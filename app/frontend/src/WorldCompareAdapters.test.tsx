import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { SupercellsExploreState, TradeCumulusExploreState } from "./ExploreStatePersistence";
import type { CompareSimulationDescriptor } from "./WorldCompare.types";
import { WorldCompareSideVisual } from "./WorldCompareAdapters";

vi.mock("./True3DViewer", () => ({
  True3DViewer: ({
    pointCloud,
    stormScene,
    status,
    compactDisplayControls,
  }: {
    pointCloud: { frame_marker?: string } | null;
    stormScene?: { layers: Array<{ key: string }> } | null;
    status: string;
    compactDisplayControls?: ReactNode;
  }) => (
    <section aria-label="mock 3-D field">
      <span>{status}</span>
      <span>
        {pointCloud?.frame_marker ??
          (stormScene ? `storm scene ${stormScene.layers.length}` : "no frame")}
      </span>
      {compactDisplayControls}
    </section>
  ),
}));

vi.mock("./StormExaminationResearch", () => ({
  StormPlanPlot: ({
    frame,
    onSelect,
  }: {
    frame: { plan: { title: string }; selected_point: Record<string, number> };
    onSelect: (selection: { xIndex: number; yIndex: number; zIndex: number }) => void;
  }) => (
    <button
      type="button"
      aria-label="mock Supercell plan"
      onClick={() => onSelect({ xIndex: 1, yIndex: 1, zIndex: 1 })}
    >
      {frame.plan.title}
    </button>
  ),
  StormSectionPlot: ({ section }: { section: { title: string } }) => (
    <div aria-label="mock Supercell section">{section.title}</div>
  ),
  StormLegend: ({ frame }: { frame: { lens_name: string } }) => (
    <div aria-label="mock Supercell legend">{frame.lens_name} legend</div>
  ),
}));

const commonState = {
  state_version: 1 as const,
  context_collapsed: true,
  secondary_section: "notes" as const,
  selected_point: null,
};

function state(modelTimeSeconds: number): TradeCumulusExploreState {
  return {
    ...commonState,
    world_id: "trade_cumulus",
    model_time_seconds: modelTimeSeconds,
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
}

const simulation: CompareSimulationDescriptor = {
  simulation_id: "baseline",
  display_name: "Canonical BOMEX Baseline",
  world_id: "trade_cumulus",
  role: "reference",
  run_id: "baseline-run",
  result_id: "baseline-result",
  case_id: "bomex",
  parent_simulation_id: null,
  reference_simulation_id: "baseline",
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
    times_seconds: [0, 60, 120],
    start_seconds: 0,
    end_seconds: 120,
    cadence_seconds: 60,
    saved_output_count: 3,
    interpolation_allowed: false,
  },
  available_field_ids: ["ql"],
  available_view_ids: ["field", "updraft_lens"],
  fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
  plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
  camera_mapping: "normalized_3d",
  initial_state: state(0),
  caveats: [],
};

const supercellState: SupercellsExploreState = {
  ...commonState,
  world_id: "supercells",
  model_time_seconds: 120,
  lens_id: "rotating_updraft",
  viewport_id: "storm",
  evidence_view: "plan",
  plane_coordinate_km: 3.1666669845581055,
  visible_layer_ids: ["storm_cloud_body", "rising_core"],
  fixed_scale_ids: ["supercell_midlevel_vertical_velocity_v1"],
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
  camera_preset: "look_along_y",
  camera_transform: null,
  scene_opacity: 1,
  scene_point_size: 1,
  selected_evidence_visible: false,
  playback_speed: 1,
  display_controls_open: false,
};

const supercellSimulation: CompareSimulationDescriptor = {
  ...simulation,
  simulation_id: "supercells_straight_line_hodograph",
  display_name: "Straight-Line Hodograph Supercell",
  world_id: "supercells",
  role: "variation",
  run_id: "straight-line-supercell-presentation-v1-20260726",
  result_id: null,
  case_id: "cm1_r21_1_straight_line_supercell_presentation_v1",
  parent_simulation_id: "supercells_quarter_circle_reference",
  reference_simulation_id: "supercells_quarter_circle_reference",
  grid: {
    topology: "native_3d",
    nx: 240,
    ny: 240,
    nz: 60,
    dx_m: 500,
    dy_m: 500,
    dz_m: 333.3333333,
    x_extent_km: [-60, 60],
    y_extent_km: [-60, 60],
    z_extent_km: [0, 20],
  },
  time: {
    times_seconds: [0, 120, 240],
    start_seconds: 0,
    end_seconds: 240,
    cadence_seconds: 120,
    saved_output_count: 3,
    interpolation_allowed: false,
  },
  available_field_ids: ["winterp", "total_condensate"],
  available_view_ids: ["rotating_updraft", "cloud_precipitation", "low_level_interactions"],
  fixed_scale_ids: [
    "supercell_midlevel_vertical_velocity_v1",
    "supercell_total_condensate_v2",
    "supercell_low_level_vertical_velocity_v1",
  ],
  plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
  camera_mapping: "normalized_3d",
  initial_state: supercellState,
};

function payload(marker: string, seconds: number) {
  return {
    frame_marker: marker,
    selection: { time_seconds: seconds },
    provenance: { provenance_label: "Native CM1 scalar cells" },
  };
}

function supercellPayload() {
  const primary = {
    key: "winterp",
    display_name: "Vertical velocity",
    units: "m/s",
    evidence_kind: "native",
    source_fields: ["winterp"],
    derivation: null,
    values: [
      [-2, 3],
      [1, 8],
    ],
    selected_frame_minimum: -2,
    selected_frame_maximum: 8,
    scale: {
      scale_id: "supercell_midlevel_vertical_velocity_v1",
      display_name: "Vertical velocity",
      units: "m/s",
      scale_type: "fixed_discrete",
      minimum: -30,
      maximum: 30,
      breakpoints: [-20, -10, -2, 2, 10, 20],
      colors: ["#4b0082", "#0057d9", "#00c9d8", "#ffffff", "#00d63b", "#ff9800", "#c40000"],
      fixed_across_time: true,
    },
  };
  const section = (orientation: "xz" | "yz") => ({
    orientation,
    title: `${orientation} native section`,
    horizontal_dimension: orientation === "xz" ? "x" : "y",
    horizontal_indices: [0, 1],
    horizontal_km: [-0.25, 0.25],
    z_km: [0.1667, 0.5],
    cross_section_coordinate_km: 0.25,
    primary,
    overlays: {},
    categories: null,
  });
  return {
    schema_version: "supercells_explore_v1",
    authority_state: "supercells_product_world",
    world_id: "supercells",
    simulation_id: "supercells_straight_line_hodograph",
    run_id: supercellSimulation.run_id,
    case_id: supercellSimulation.case_id,
    simulation_label: supercellSimulation.display_name,
    lens_id: "rotating_updraft",
    lens_name: "Rotating Updraft",
    lens_question: "Where is the storm rising and rotating as one organized structure?",
    what_to_notice_now: "Compare coordinates and local evidence without assigning storm lineage.",
    time_index: 1,
    time_seconds: 120,
    times_seconds: [0, 120, 240],
    mature_checkpoint_indices: [1],
    timeline_checkpoints: [],
    viewport: "storm",
    viewport_bounds_km: { x_min: -40, x_max: 40, y_min: -45, y_max: 35 },
    primary_updraft: {
      x_index: 1,
      y_index: 1,
      z_index: 1,
      x_km: 0.25,
      y_km: 0.25,
      z_km: 0.5,
      w_m_s: 8,
    },
    selected_point: {
      x_index: 1,
      y_index: 1,
      z_index: 1,
      x_km: 0.25,
      y_km: 0.25,
      z_km: 0.5,
      model_time_seconds: 120,
      coordinate_frame: "translating model frame",
      values: {
        vertical_velocity: 8,
        vertical_vorticity: 0.02,
        updraft_helicity: 450,
        total_condensate: 2,
        reflectivity: 48,
      },
      units: {
        vertical_velocity: "m/s",
        vertical_vorticity: "s^-1",
        updraft_helicity: "m^2/s^2",
        total_condensate: "g/kg",
        reflectivity: "dBZ",
      },
      evidence_kind: {},
      states: ["Rising", "Condensate present"],
      distance_to_primary_updraft_km: 0,
    },
    plan: {
      title: "Updraft and rotation",
      subtitle: "Native-grid plan evidence",
      x_indices: [0, 1],
      y_indices: [0, 1],
      x_km: [-0.25, 0.25],
      y_km: [-0.25, 0.25],
      level_index: 1,
      level_km: 0.5,
      selection_z_indices: null,
      primary,
      overlays: {},
      categories: null,
      wind_vectors: [],
    },
    xz_section: section("xz"),
    yz_section: section("yz"),
    scene: {
      coordinate_extents_km: {
        x: { min: -40, max: 40 },
        y: { min: -45, max: 35 },
        z: { min: 0.1667, max: 19.8333 },
      },
      coordinate_sizes: { x: 160, y: 160, z: 60 },
      coordinate_indices: { x: [0, 1], y: [0, 1], z: [0, 1] },
      coordinate_values_km: {
        x: [-0.25, 0.25],
        y: [-0.25, 0.25],
        z: [0.1667, 0.5],
      },
      layers: [
        {
          key: "storm_cloud_body",
          display_name: "Storm cloud body",
          units: "g/kg",
          evidence_kind: "derived",
          source_fields: ["qc", "qr", "qi", "qs", "qg"],
          derivation: "total condensate",
          rendering: "neutral_cloud",
          points: [[0.25, 0.25, 0.5, 2, 0]],
          source_count: 1,
          returned_count: 1,
          threshold_label: "0.05 g/kg",
          default_visible: true,
          default_opacity: 0.22,
          default_point_size: 4.5,
          scale: null,
          categories: [],
        },
      ],
      wind_vectors: [],
      wind_reference_m_s: 25,
      point_budget: 20_000,
      source_history_file: "cm1out_000002.nc",
    },
    caveats: [],
    provenance: {},
    extraction_milliseconds: 12,
  };
}

function deferredResponse() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

function renderSide(exploreState: TradeCumulusExploreState) {
  const onFrameState = vi.fn();
  const onPerformance = vi.fn();
  const result = render(
    <WorldCompareSideVisual
      side="left"
      simulation={simulation}
      state={exploreState}
      onStateChange={vi.fn()}
      onFrameState={onFrameState}
      onPerformance={onPerformance}
    />,
  );
  return { ...result, onFrameState, onPerformance };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("WorldCompareSideVisual request lifecycle", () => {
  it("loads the real Supercells frame contract and exposes 3-D plus physical sections", async () => {
    const onStateChange = vi.fn();
    const onEvidence = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(supercellPayload()), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(
      <WorldCompareSideVisual
        side="right"
        simulation={supercellSimulation}
        state={supercellState}
        onStateChange={onStateChange}
        onFrameState={vi.fn()}
        onPerformance={vi.fn()}
        onEvidence={onEvidence}
      />,
    );

    expect(await screen.findByLabelText("mock Supercell plan")).toHaveTextContent(
      "Updraft and rotation",
    );
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/worlds/supercells/simulations/supercells_straight_line_hodograph/frame?",
    );
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "lens=rotating_updraft&viewport=storm&time_index=1",
    );
    fireEvent.click(screen.getByRole("button", { name: "3-D" }));
    expect(screen.getByText("storm scene 1")).toBeVisible();
    expect(screen.getByRole("checkbox", { name: "Storm cloud body" })).toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: "Vertical x-z" }));
    expect(onStateChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        evidence_view: "xz",
        plane_coordinate_km: 0,
      }),
    );
    expect(onEvidence).toHaveBeenCalledWith("right", null);
  });

  it("retries a failed side without replacing its adapter", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response("temporary failure", { status: 503 }))
        .mockResolvedValueOnce(
          new Response(JSON.stringify(payload("recovered frame", 0)), { status: 200 }),
        ),
    );
    const { onFrameState } = renderSide(state(0));

    fireEvent.click(await screen.findByRole("button", { name: "Retry this side" }));

    expect(await screen.findByText("recovered frame")).toBeVisible();
    expect(onFrameState).toHaveBeenCalledWith("left", "error");
    expect(onFrameState).toHaveBeenLastCalledWith("left", "ready");
  });

  it("aborts and ignores a stale response when the requested time changes", async () => {
    const stale = deferredResponse();
    let firstSignal: AbortSignal | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).includes("time_index=0")) {
          firstSignal = init?.signal ?? undefined;
          return stale.promise;
        }
        return Promise.resolve(
          new Response(JSON.stringify(payload("current frame", 60)), { status: 200 }),
        );
      }),
    );
    const rendered = renderSide(state(0));

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(60)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );

    expect(await screen.findByText("current frame")).toBeVisible();
    expect(firstSignal?.aborted).toBe(true);
    await act(async () => {
      stale.resolve(new Response(JSON.stringify(payload("stale frame", 0)), { status: 200 }));
      await stale.promise;
    });
    await waitFor(() => expect(screen.queryByText("stale frame")).not.toBeInTheDocument());
    expect(screen.getByText("current frame")).toBeVisible();
  });

  it("reuses a bounded side cache when returning to a prior saved output", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const isFirst = String(input).includes("time_index=0");
      return Promise.resolve(
        new Response(
          JSON.stringify(payload(isFirst ? "first frame" : "second frame", isFirst ? 0 : 60)),
          { status: 200 },
        ),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const rendered = renderSide(state(0));
    expect(await screen.findByText("first frame")).toBeVisible();

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(60)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );
    expect(await screen.findByText("second frame")).toBeVisible();

    rendered.rerender(
      <WorldCompareSideVisual
        side="left"
        simulation={simulation}
        state={state(0)}
        onStateChange={vi.fn()}
        onFrameState={rendered.onFrameState}
        onPerformance={rendered.onPerformance}
      />,
    );
    expect(await screen.findByText("first frame")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(rendered.onPerformance).toHaveBeenLastCalledWith(
      expect.objectContaining({ cache_hit: true, side: "left" }),
    );
  });
});

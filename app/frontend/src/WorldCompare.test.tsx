import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  ExploreWorldState,
  MountainWavesExploreState,
  SupercellsExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import { WorldCompare } from "./WorldCompare";
import type { CompareSimulationDescriptor, WorldCompareDescriptor } from "./WorldCompare.types";

vi.mock("./WorldCompareAdapters", async (importOriginal) => {
  const original = await importOriginal<typeof import("./WorldCompareAdapters")>();
  return {
    ...original,
    WorldCompareSideVisual: (props: {
      side: "left" | "right";
      simulation: CompareSimulationDescriptor;
      state: ExploreWorldState;
      onStateChange: (state: ExploreWorldState) => void;
      onFrameState: (side: "left" | "right", state: "ready" | "error") => void;
      onPerformance: (sample: {
        side: "left" | "right";
        key: string;
        request_ms: number;
        payload_bytes: number;
        cache_hit: boolean;
      }) => void;
      onEvidence: (
        side: "left" | "right",
        evidence: {
          title: string;
          states: string[];
          metrics: Array<{
            label: string;
            value: string;
            numericValue?: number;
            units?: string;
          }>;
        } | null,
      ) => void;
    }) => {
      const failed = props.simulation.simulation_id.endsWith("-failed");
      const { onFrameState, onPerformance, side } = props;
      useEffect(() => {
        onFrameState(side, failed ? "error" : "ready");
        if (!failed) {
          onPerformance({
            side,
            key: `${props.simulation.simulation_id}-${props.state.model_time_seconds}`,
            request_ms: 12,
            payload_bytes: 1024,
            cache_hit: false,
          });
        }
      }, [
        failed,
        onFrameState,
        onPerformance,
        props.simulation.simulation_id,
        props.state.model_time_seconds,
        side,
      ]);
      if (failed) {
        return (
          <section role="alert" aria-label={`${props.simulation.display_name} frame failure`}>
            This side failed without removing its partner.
            <button type="button">Retry failed side</button>
          </section>
        );
      }
      const supercellsState = props.state.world_id === "supercells" ? props.state : null;
      return (
        <section aria-label={`${props.simulation.display_name} test frame`}>
          Native frame at {props.state.model_time_seconds} s ·{" "}
          {supercellsState
            ? supercellsState.lens_id
            : "view_id" in props.state
              ? props.state.view_id
              : "field"}
          {supercellsState && (
            <span>
              {" "}
              · {supercellsState.evidence_view} at {supercellsState.plane_coordinate_km} km · camera{" "}
              {supercellsState.camera_transform?.position.join(",") ??
                supercellsState.camera_preset}{" "}
              · selected {supercellsState.selected_point?.x_km ?? "none"}
            </span>
          )}
          <button
            type="button"
            onClick={() => {
              props.onStateChange({
                ...props.state,
                selected_point: { x_km: 1, y_km: 2, z_km: 0.5 },
              });
              props.onEvidence(props.side, {
                title: `${props.simulation.display_name} selected point`,
                states: ["Rising", "Cloudy"],
                metrics: [
                  { label: "Vertical velocity", value: "2.0 m/s", numericValue: 2, units: "m/s" },
                ],
              });
            }}
          >
            Select {props.simulation.display_name} point
          </button>
          {supercellsState && (
            <>
              <button
                type="button"
                onClick={() =>
                  props.onStateChange({
                    ...supercellsState,
                    evidence_view: "xz",
                    plane_coordinate_km: -10,
                  })
                }
              >
                Move {props.simulation.display_name} section
              </button>
              <button
                type="button"
                onClick={() =>
                  props.onStateChange({
                    ...supercellsState,
                    camera_preset: "look_along_x",
                    camera_transform: {
                      position: [10, 12, 14],
                      target: [1, 2, 3],
                      up: [0, 1, 0],
                    },
                  })
                }
              >
                Move {props.simulation.display_name} camera
              </button>
            </>
          )}
        </section>
      );
    },
  };
});

const commonState = {
  state_version: 1 as const,
  context_collapsed: true,
  secondary_section: "notes" as const,
  selected_point: null,
};

function tradeState(modelTimeSeconds: number): TradeCumulusExploreState {
  return {
    ...commonState,
    world_id: "trade_cumulus",
    model_time_seconds: modelTimeSeconds,
    view_id: "updraft_lens",
    scene_field_id: "ql",
    slice_field_id: "w",
    fixed_scale_id: "trade_cumulus_updraft_velocity_v1",
    active_slice_plane: "vertical_x",
    slice_coordinate_km: 1,
    slice_native_index: 50,
    horizontal_slice_coordinate_km: 1,
    threshold_native: 1e-6,
    layer_opacity: 0.68,
    point_size_px: 11,
    lens_opacity: 0.9,
    show_slice_plane: true,
    show_cloud_boundary: true,
    show_horizontal_wind: true,
    wind_mode: "perturbation",
    camera_preset: "overview",
    camera_transform: null,
    playback_speed: 1,
    display_controls_open: false,
  };
}

function tradeSimulation(
  simulationId: string,
  displayName: string,
  timeSeconds: number,
): CompareSimulationDescriptor {
  return {
    simulation_id: simulationId,
    display_name: displayName,
    world_id: "trade_cumulus",
    role: simulationId === "baseline" ? "reference" : "variation",
    run_id: `${simulationId}-run`,
    result_id: `${simulationId}-result`,
    case_id: "bomex",
    parent_simulation_id: simulationId === "baseline" ? null : "baseline",
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
    initial_state: tradeState(timeSeconds),
    caveats: [],
  };
}

function tradeDescriptor(rightId = "moisture"): WorldCompareDescriptor {
  const left = tradeSimulation("baseline", "Canonical BOMEX Baseline", 0);
  const right = tradeSimulation(rightId, "More Moisture", 120);
  return {
    schema_version: "world_compare_v1",
    world_id: "trade_cumulus",
    display_name: "Trade Cumulus",
    simulations: [left, right],
    default_left_simulation_id: left.simulation_id,
    default_right_simulation_id: right.simulation_id,
    selected_left_simulation_id: left.simulation_id,
    selected_right_simulation_id: right.simulation_id,
    material_differences: [
      {
        path: "surface_moisture_flux",
        label: "Surface moisture supply",
        category: "atmospheric",
        left_value: 0.052,
        right_value: 0.078,
        left_known: true,
        right_known: true,
        units: "g/kg m/s",
        material: true,
      },
    ],
    compatibility: {
      same_world: true,
      both_inspectable: true,
      relationship: "More Moisture is a child of Canonical BOMEX Baseline.",
      controlled_pair: true,
      controlled_pair_message: "Only surface moisture supply changed.",
      shared_field_ids: ["ql"],
      shared_view_ids: ["field", "updraft_lens"],
      shared_fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
      exact_time_link_available: true,
      nearest_time_link_available: true,
      time_tolerance_seconds: 90,
      physical_plane_link_available: true,
      camera_link_available: true,
      selection_link_available: true,
      blockers: [],
    },
    no_second_simulation_message: null,
    persistence: "transient_only",
  };
}

function mountainState(
  viewId: MountainWavesExploreState["view_id"],
  modelTimeSeconds: number,
): MountainWavesExploreState {
  return {
    ...commonState,
    world_id: "mountain_waves",
    model_time_seconds: modelTimeSeconds,
    view_id: viewId,
    field_id: "w",
    fixed_scale_id: "mountain_waves_vertical_velocity_v1",
    viewport_id: "focus",
    geometry_id: "expanded",
    overlays: {
      cloud_points: viewId === "wave_cloud",
      cloud_boundary: viewId === "wave_cloud",
      saturation_contour: viewId === "wave_cloud",
      horizontal_wind: true,
      potential_temperature_contours: viewId === "wave_structure",
    },
    cloud_opacity: 0.68,
    cloud_point_size_px: 11,
    playback_speed: 1,
  };
}

function mountainSimulation(
  simulationId: string,
  displayName: string,
  moist: boolean,
): CompareSimulationDescriptor {
  return {
    simulation_id: simulationId,
    display_name: displayName,
    world_id: "mountain_waves",
    role: "built_in",
    run_id: `${simulationId}-run`,
    result_id: null,
    case_id: `${simulationId}-case`,
    parent_simulation_id: null,
    reference_simulation_id: moist ? simulationId : null,
    lineage_state: moist ? "known" : "independent_built_in",
    availability_state: "available",
    availability_message: "Available",
    inspectable: true,
    grid: {
      topology: "native_2d_xz",
      nx: moist ? 440 : 200,
      ny: 1,
      nz: moist ? 250 : 200,
      dx_m: moist ? 500 : 100,
      dy_m: moist ? 500 : 100,
      dz_m: 100,
      x_extent_km: moist ? [-110, 110] : [-10, 10],
      y_extent_km: null,
      z_extent_km: moist ? [0, 25] : [0, 20],
    },
    time: {
      times_seconds: [0, 30, 60],
      start_seconds: 0,
      end_seconds: 60,
      cadence_seconds: 30,
      saved_output_count: 3,
      interpolation_allowed: false,
    },
    available_field_ids: moist
      ? ["w", "theta_perturbation", "cloud_liquid", "relative_humidity"]
      : ["w", "theta_perturbation"],
    available_view_ids: moist
      ? ["field", "wave_structure", "wave_cloud"]
      : ["field", "wave_structure"],
    fixed_scale_ids: ["mountain_waves_vertical_velocity_v1"],
    plane_orientations: [],
    camera_mapping: "native_2d_xz",
    initial_state: mountainState(moist ? "wave_cloud" : "wave_structure", 60),
    caveats: [],
  };
}

function mountainDescriptor(): WorldCompareDescriptor {
  const dry = mountainSimulation("mountain_waves_dry_ridge", "Dry Ridge — Wave Mechanics", false);
  const moist = mountainSimulation(
    "mountain_waves_boulder_moist_reference",
    "Boulder Windstorm — Moist Reference",
    true,
  );
  return {
    schema_version: "world_compare_v1",
    world_id: "mountain_waves",
    display_name: "Mountain Waves",
    simulations: [dry, moist],
    default_left_simulation_id: dry.simulation_id,
    default_right_simulation_id: moist.simulation_id,
    selected_left_simulation_id: dry.simulation_id,
    selected_right_simulation_id: moist.simulation_id,
    material_differences: [],
    compatibility: {
      same_world: true,
      both_inspectable: true,
      relationship:
        "Both are retained built-in Mountain Waves Simulations; no controlled experimental relationship is declared.",
      controlled_pair: false,
      controlled_pair_message: "This is a structural comparison.",
      shared_field_ids: ["theta_perturbation", "w"],
      shared_view_ids: ["field", "wave_structure"],
      shared_fixed_scale_ids: ["mountain_waves_vertical_velocity_v1"],
      exact_time_link_available: true,
      nearest_time_link_available: true,
      time_tolerance_seconds: 45,
      physical_plane_link_available: false,
      camera_link_available: false,
      selection_link_available: true,
      blockers: [],
    },
    no_second_simulation_message: null,
    persistence: "transient_only",
  };
}

function supercellsState(
  lensId: SupercellsExploreState["lens_id"],
  modelTimeSeconds: number,
): SupercellsExploreState {
  return {
    ...commonState,
    world_id: "supercells",
    model_time_seconds: modelTimeSeconds,
    lens_id: lensId,
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
    camera_preset: "overview",
    camera_transform: null,
    scene_opacity: 1,
    scene_point_size: 1,
    selected_evidence_visible: false,
    playback_speed: 1,
    display_controls_open: false,
  };
}

function supercellsSimulation(
  simulationId: string,
  displayName: string,
  modelTimeSeconds: number,
): CompareSimulationDescriptor {
  const reference = simulationId === "supercells_quarter_circle_reference";
  return {
    simulation_id: simulationId,
    display_name: displayName,
    world_id: "supercells",
    role: reference ? "reference" : "variation",
    run_id: `${simulationId}-run`,
    result_id: `${simulationId}-result`,
    case_id: reference
      ? "cm1_r21_1_quarter_circle_supercell_presentation_v1"
      : "cm1_r21_1_straight_line_supercell_presentation_v1",
    parent_simulation_id: reference ? null : "supercells_quarter_circle_reference",
    reference_simulation_id: "supercells_quarter_circle_reference",
    lineage_state: "known",
    availability_state: "available",
    availability_message: "Available",
    inspectable: true,
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
    initial_state: supercellsState("rotating_updraft", modelTimeSeconds),
    caveats: [],
  };
}

function supercellsFixtureDescriptor(): WorldCompareDescriptor {
  const left = supercellsSimulation(
    "supercells_quarter_circle_reference",
    "Quarter-Circle Supercell",
    0,
  );
  const right = supercellsSimulation(
    "supercells_straight_line_hodograph",
    "Straight-Line Hodograph Supercell",
    240,
  );
  return {
    schema_version: "world_compare_v1",
    world_id: "supercells",
    display_name: "Supercells",
    simulations: [left, right],
    default_left_simulation_id: left.simulation_id,
    default_right_simulation_id: right.simulation_id,
    selected_left_simulation_id: left.simulation_id,
    selected_right_simulation_id: right.simulation_id,
    material_differences: [],
    compatibility: {
      same_world: true,
      both_inspectable: true,
      relationship: "Straight-Line Hodograph Supercell is a child of Quarter-Circle Supercell.",
      controlled_pair: true,
      controlled_pair_message: "Only hodograph curvature changed in this controlled pair.",
      shared_field_ids: [],
      shared_view_ids: ["cloud_precipitation", "low_level_interactions", "rotating_updraft"],
      shared_fixed_scale_ids: ["supercells_vertical_velocity_v1"],
      exact_time_link_available: true,
      nearest_time_link_available: true,
      time_tolerance_seconds: 180,
      physical_plane_link_available: true,
      camera_link_available: true,
      selection_link_available: true,
      blockers: [],
    },
    no_second_simulation_message: null,
    persistence: "transient_only",
  };
}

describe("WorldCompare", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(new Response(JSON.stringify(tradeDescriptor()), { status: 200 })),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reviews lineage and exact material differences before loading frames", async () => {
    render(<WorldCompare worldSlug="trade-cumulus" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);

    expect(
      await screen.findByRole("heading", {
        name: "Review the two Simulations before loading frames",
      }),
    ).toBeVisible();
    expect(screen.getByText("More Moisture is a child of Canonical BOMEX Baseline.")).toBeVisible();
    expect(screen.getByText("0.0520 g/kg m/s")).toBeVisible();
    expect(screen.getByText("0.0780 g/kg m/s")).toBeVisible();
    expect(screen.queryByLabelText(/test frame/)).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("supports aligned and independent state plus per-side selected evidence", async () => {
    render(<WorldCompare worldSlug="trade-cumulus" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    expect(await screen.findByLabelText("Canonical BOMEX Baseline test frame")).toBeVisible();
    expect(screen.getByLabelText("More Moisture test frame")).toHaveTextContent("120 s");
    fireEvent.click(screen.getByRole("button", { name: "Aligned" }));
    await waitFor(() =>
      expect(screen.getByLabelText("More Moisture test frame")).toHaveTextContent("0 s"),
    );
    expect(screen.getByLabelText("Time")).toBeChecked();
    expect(screen.getByLabelText("Field / Lens")).toBeChecked();

    fireEvent.click(
      within(screen.getByLabelText("Canonical BOMEX Baseline test frame")).getByRole("button"),
    );
    expect(await screen.findByLabelText("Context")).toBeVisible();
    expect(screen.getByText("Canonical BOMEX Baseline selected point")).toBeVisible();
    expect(screen.getByText("2.0 m/s")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Independent" }));
    expect(screen.getByLabelText("Time")).not.toBeChecked();
    expect(screen.getByLabelText("Field / Lens")).not.toBeChecked();
  });

  it("keeps one side usable when the other adapter fails", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(tradeDescriptor("moisture-failed")), { status: 200 }),
    );
    render(<WorldCompare worldSlug="trade-cumulus" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    expect(await screen.findByLabelText("Canonical BOMEX Baseline test frame")).toBeVisible();
    expect(screen.getByLabelText("More Moisture frame failure")).toBeVisible();
    expect(screen.getByRole("button", { name: "Retry failed side" })).toBeVisible();
  });

  it("exposes Wave Cloud point controls only while cloud points are enabled", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(mountainDescriptor()), { status: 200 }),
    );
    render(<WorldCompare worldSlug="mountain-waves" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    const rightSide = await screen.findByRole("article", {
      name: "Boulder Windstorm — Moist Reference comparison side",
    });
    expect(within(rightSide).getByLabelText("Cloud points")).toBeChecked();
    expect(within(rightSide).getByLabelText("Cloud boundary")).toBeChecked();
    expect(within(rightSide).getByLabelText("RH = 100%")).toBeChecked();
    expect(
      within(rightSide).getByLabelText("Boulder Windstorm — Moist Reference cloud opacity"),
    ).toHaveValue("0.68");
    expect(
      within(rightSide).getByLabelText("Boulder Windstorm — Moist Reference cloud point size"),
    ).toHaveValue("11");

    fireEvent.click(within(rightSide).getByLabelText("Cloud points"));
    expect(
      within(rightSide).queryByLabelText("Boulder Windstorm — Moist Reference cloud opacity"),
    ).not.toBeInTheDocument();
    expect(
      within(rightSide).queryByLabelText("Boulder Windstorm — Moist Reference cloud point size"),
    ).not.toBeInTheDocument();
  });

  it("coordinates the controlled Supercells pair through the shared shell", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(supercellsFixtureDescriptor()), { status: 200 }),
    );
    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    expect(await screen.findByLabelText("Quarter-Circle Supercell test frame")).toHaveTextContent(
      "0 s",
    );
    expect(screen.getByLabelText("Straight-Line Hodograph Supercell test frame")).toHaveTextContent(
      "240 s",
    );
    fireEvent.click(screen.getByRole("button", { name: "Aligned" }));
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("0 s"),
    );
    expect(screen.getByRole("checkbox", { name: /^Time$/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /^Field \/ Lens$/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /^Camera$/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /^Slice plane$/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /^Selection$/ })).toBeChecked();

    const leftSide = screen.getByRole("article", {
      name: "Quarter-Circle Supercell comparison side",
    });
    fireEvent.click(
      within(leftSide).getByRole("button", { name: "Move Quarter-Circle Supercell section" }),
    );
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("xz at -10 km"),
    );
    fireEvent.click(
      within(leftSide).getByRole("button", { name: "Move Quarter-Circle Supercell camera" }),
    );
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("camera 10,12,14"),
    );
    fireEvent.click(
      within(leftSide).getByRole("button", { name: "Select Quarter-Circle Supercell point" }),
    );
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("selected 1"),
    );
    fireEvent.click(within(leftSide).getByRole("button", { name: "Cloud and Precipitation" }));
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("cloud_precipitation"),
    );

    fireEvent.click(screen.getByText("Compare technical details", { exact: true }));
    expect(screen.getByText(/right: 12 ms, 1.0 KB/)).toBeVisible();
    expect(screen.getByText("transient only")).toBeVisible();
  });

  it("shows an honest no-second-Simulation state for Supercells", async () => {
    const reference = tradeSimulation(
      "supercells_quarter_circle_reference",
      "Quarter-Circle Supercell",
      0,
    );
    reference.world_id = "supercells";
    reference.initial_state = {
      ...commonState,
      world_id: "supercells",
      model_time_seconds: 0,
      lens_id: "rotating_updraft",
      viewport_id: "storm",
      evidence_view: "plan",
      plane_coordinate_km: 3,
      visible_layer_ids: [],
      fixed_scale_ids: [],
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
      scene_opacity: 1,
      scene_point_size: 1,
      selected_evidence_visible: false,
      playback_speed: 1,
      display_controls_open: false,
    };
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          schema_version: "world_compare_v1",
          world_id: "supercells",
          display_name: "Supercells",
          simulations: [reference],
          default_left_simulation_id: reference.simulation_id,
          default_right_simulation_id: null,
          selected_left_simulation_id: reference.simulation_id,
          selected_right_simulation_id: null,
          material_differences: [],
          compatibility: null,
          no_second_simulation_message:
            "Supercells currently has one retained Simulation; it is not cloned.",
          persistence: "transient_only",
        }),
        { status: 200 },
      ),
    );

    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);

    expect(await screen.findByLabelText("No second Simulation")).toBeVisible();
    expect(screen.getByText(/it is not cloned/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Open dual view" })).not.toBeInTheDocument();
  });
});

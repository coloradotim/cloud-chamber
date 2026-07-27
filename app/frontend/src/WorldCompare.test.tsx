import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useEffect, useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  ExploreWorldState,
  MountainWavesExploreState,
  SupercellsExploreState,
  TradeCumulusExploreState,
} from "./ExploreStatePersistence";
import type { SavedComparisonEntry } from "./SavedComparisons";
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
      onFrameState: (side: "left" | "right", state: "loading" | "ready" | "error") => void;
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
      presentation: "scene" | "evidence";
      onPresentationChange: (side: "left" | "right", presentation: "scene" | "evidence") => void;
    }) => {
      const failed = props.simulation.simulation_id.endsWith("-failed");
      const startsPending = props.simulation.simulation_id.endsWith("-pending");
      const [pending, setPending] = useState(startsPending);
      const { onFrameState, onPerformance, side } = props;
      useEffect(() => {
        onFrameState(side, failed ? "error" : pending ? "loading" : "ready");
        if (!failed && !pending) {
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
        pending,
        props.simulation.simulation_id,
        props.state.model_time_seconds,
        side,
      ]);
      if (pending) {
        return (
          <section aria-label={`${props.simulation.display_name} pending frame`}>
            Waiting for a coherent frame.
            <button type="button" onClick={() => setPending(false)}>
              Finish {props.simulation.display_name} frame
            </button>
          </section>
        );
      }
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
              · selected{" "}
              {supercellsState.selected_point
                ? `${supercellsState.selected_point.x_km},${supercellsState.selected_point.y_km},${supercellsState.selected_point.z_km}`
                : "none"}{" "}
              · evidence {supercellsState.selected_evidence_visible ? "visible" : "hidden"}
            </span>
          )}
          <button
            type="button"
            onClick={() => {
              const selectedPoint = { x_km: 1, y_km: 2, z_km: 0.5 };
              props.onStateChange({
                ...props.state,
                selected_point: selectedPoint,
                ...(supercellsState
                  ? {
                      selected_evidence_visible: true,
                      plane_coordinate_km:
                        supercellsState.evidence_view === "plan"
                          ? selectedPoint.z_km
                          : supercellsState.evidence_view === "xz"
                            ? selectedPoint.y_km
                            : selectedPoint.x_km,
                    }
                  : {}),
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
                  props.onPresentationChange(
                    props.side,
                    props.presentation === "scene" ? "evidence" : "scene",
                  )
                }
              >
                Show {props.simulation.display_name}{" "}
                {props.presentation === "scene" ? "evidence" : "scene"}
              </button>
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
                    evidence_view: "yz",
                    plane_coordinate_km: -12,
                  })
                }
              >
                Use {props.simulation.display_name} y-z section
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
    available_field_ids: ["ql", "w"],
    available_view_ids: ["field", "updraft_lens"],
    fixed_scale_ids: ["trade_cumulus_updraft_velocity_v1"],
    plane_orientations: ["horizontal", "vertical_x", "vertical_y"],
    camera_mapping: "normalized_3d",
    initial_state: tradeState(timeSeconds),
    caveats: [],
  };
}

function tradeDescriptor(
  rightId = "moisture",
  leftId = "baseline",
  leftDisplayName = "Canonical BOMEX Baseline",
  rightDisplayName = "More Moisture",
): WorldCompareDescriptor {
  const left = tradeSimulation(leftId, leftDisplayName, 0);
  const right = tradeSimulation(rightId, rightDisplayName, 120);
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
      shared_field_ids: ["ql", "w"],
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
    persistence: "saved_comparisons",
  };
}

function savedTradeEntry({
  leftAvailable = true,
  rightAvailable = true,
  rightSimulationId = "moisture",
  relationship,
}: {
  leftAvailable?: boolean;
  rightAvailable?: boolean;
  rightSimulationId?: string;
  relationship?: string;
} = {}): SavedComparisonEntry {
  const descriptor = tradeDescriptor();
  return {
    record: {
      saved_comparison_id: "a".repeat(32),
      title: "Moisture response",
      scientific_question: "How does added moisture change cloud growth?",
      created_at: "2026-07-27T12:00:00Z",
      updated_at: "2026-07-27T12:00:00Z",
      restoration_status: "healthy",
      restoration_message: null,
      captured_pair: {
        left_display_name: "Canonical BOMEX Baseline",
        right_display_name: "More Moisture",
        relationship: relationship ?? descriptor.compatibility!.relationship,
        controlled_pair: descriptor.compatibility!.controlled_pair,
        controlled_pair_message: descriptor.compatibility!.controlled_pair_message,
        material_differences: descriptor.material_differences,
      },
      workspace: {
        schema_version: 1,
        world_id: "trade_cumulus",
        left_simulation_id: "baseline",
        right_simulation_id: rightSimulationId,
        left_state: tradeState(60),
        right_state: tradeState(120),
        links: { time: false, view: true, plane: true, camera: false, selection: false },
        context_collapsed: false,
        supercells_presentation: null,
      },
    },
    dependencies: [
      {
        side: "left",
        simulation_id: "baseline",
        display_name: "Canonical BOMEX Baseline",
        available: leftAvailable,
      },
      {
        side: "right",
        simulation_id: rightSimulationId,
        display_name: "More Moisture",
        available: rightAvailable,
      },
    ],
    effective_restoration_status: leftAvailable && rightAvailable ? "healthy" : "unavailable",
    effective_restoration_message:
      leftAvailable && rightAvailable ? null : "A retained Simulation is missing.",
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
    persistence: "saved_comparisons",
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
    persistence: "saved_comparisons",
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
    expect(screen.getByText("saved comparisons")).toBeVisible();
  });

  it("moves a Supercells section without creating selected evidence", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(supercellsFixtureDescriptor()), { status: 200 }),
    );
    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    const leftSide = await screen.findByRole("article", {
      name: "Quarter-Circle Supercell comparison side",
    });
    fireEvent.change(within(leftSide).getByLabelText("Quarter-Circle Supercell slice position"), {
      target: { value: "10" },
    });

    expect(screen.getByLabelText("Quarter-Circle Supercell test frame")).toHaveTextContent(
      "selected none · evidence hidden",
    );
    expect(screen.queryByLabelText("Selected native-grid evidence")).not.toBeInTheDocument();
  });

  it("keeps linked Supercells selection coherent while plane linking is independent", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(supercellsFixtureDescriptor()), { status: 200 }),
    );
    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));

    const leftSide = await screen.findByRole("article", {
      name: "Quarter-Circle Supercell comparison side",
    });
    const rightSide = screen.getByRole("article", {
      name: "Straight-Line Hodograph Supercell comparison side",
    });
    const selectionLink = screen.getByRole("checkbox", { name: /^Selection$/ });
    const planeLink = screen.getByRole("checkbox", { name: /^Slice plane$/ });
    fireEvent.click(selectionLink);
    expect(selectionLink).toBeChecked();
    expect(planeLink).not.toBeChecked();

    fireEvent.click(
      within(rightSide).getByRole("button", {
        name: "Use Straight-Line Hodograph Supercell y-z section",
      }),
    );
    await waitFor(() =>
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("yz at -12 km"),
    );

    fireEvent.click(
      within(leftSide).getByRole("button", { name: "Select Quarter-Circle Supercell point" }),
    );
    await waitFor(() => {
      expect(screen.getByLabelText("Quarter-Circle Supercell test frame")).toHaveTextContent(
        "selected 1,2,0.5 · evidence visible",
      );
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("yz at 1 km");
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("selected 1,2,0.5 · evidence visible");
    });
    expect(planeLink).not.toBeChecked();

    fireEvent.click(
      within(screen.getByLabelText("Selected native-grid evidence")).getByRole("button", {
        name: "Clear",
      }),
    );
    await waitFor(() => {
      expect(screen.getByLabelText("Quarter-Circle Supercell test frame")).toHaveTextContent(
        "selected none · evidence hidden",
      );
      expect(
        screen.getByLabelText("Straight-Line Hodograph Supercell test frame"),
      ).toHaveTextContent("selected none · evidence hidden");
    });
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
          persistence: "saved_comparisons",
        }),
        { status: 200 },
      ),
    );

    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);

    expect(await screen.findByLabelText("No second Simulation")).toBeVisible();
    expect(screen.getByText(/it is not cloned/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Open dual view" })).not.toBeInTheDocument();
  });

  it("reopens a Saved Comparison directly from its immutable workspace", async () => {
    const descriptor = tradeDescriptor();
    const savedEntry = savedTradeEntry();
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }));

    render(
      <WorldCompare
        worldSlug="trade-cumulus"
        savedComparisonId={savedEntry.record.saved_comparison_id}
        onBack={vi.fn()}
        onOpenSimulation={vi.fn()}
      />,
    );

    expect(await screen.findByText("Saved Comparison: Moisture response")).toBeVisible();
    expect(screen.queryByText(/Review the two Simulations/)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Canonical BOMEX Baseline test frame")).toHaveTextContent("60 s");
    expect(screen.getByLabelText("More Moisture test frame")).toHaveTextContent("120 s");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Save as new comparison" })).toBeEnabled(),
    );
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/worlds/trade-cumulus/saved-comparisons/${savedEntry.record.saved_comparison_id}`,
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });

  it("records restoration only after both saved sides reach coherent frames", async () => {
    const descriptor = tradeDescriptor("moisture-pending");
    const savedEntry = savedTradeEntry({ rightSimulationId: "moisture-pending" });
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }));

    render(
      <WorldCompare
        worldSlug="trade-cumulus"
        savedComparisonId={savedEntry.record.saved_comparison_id}
        onBack={vi.fn()}
        onOpenSimulation={vi.fn()}
      />,
    );

    expect(await screen.findByLabelText("More Moisture pending frame")).toBeVisible();
    expect(fetch).toHaveBeenCalledTimes(2);
    fireEvent.click(screen.getByRole("button", { name: "Finish More Moisture frame" }));
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/worlds/trade-cumulus/saved-comparisons/${savedEntry.record.saved_comparison_id}`,
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });

  it("keeps an opened comparison usable when restoration metadata cannot be persisted", async () => {
    const descriptor = tradeDescriptor();
    const savedEntry = savedTradeEntry();
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "write failed" }), { status: 500 }),
      );

    render(
      <WorldCompare
        worldSlug="trade-cumulus"
        savedComparisonId={savedEntry.record.saved_comparison_id}
        onBack={vi.fn()}
        onOpenSimulation={vi.fn()}
      />,
    );

    expect(await screen.findByLabelText("Canonical BOMEX Baseline test frame")).toBeVisible();
    expect(
      await screen.findByText(
        "The comparison opened, but its restoration status could not be recorded.",
      ),
    ).toBeVisible();
    expect(screen.getByLabelText("More Moisture test frame")).toBeVisible();
  });

  it("reports captured pair metadata drift without rewriting saved history", async () => {
    const descriptor = tradeDescriptor();
    const savedEntry = savedTradeEntry({ relationship: "Captured historical relationship." });
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(savedEntry), { status: 200 }));

    render(
      <WorldCompare
        worldSlug="trade-cumulus"
        savedComparisonId={savedEntry.record.saved_comparison_id}
        onBack={vi.fn()}
        onOpenSimulation={vi.fn()}
      />,
    );

    expect(
      await screen.findByText(
        "Current pair metadata differs from the captured summary; the saved summary remains unchanged.",
      ),
    ).toBeVisible();
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/worlds/trade-cumulus/saved-comparisons/${savedEntry.record.saved_comparison_id}`,
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
    expect(savedEntry.record.captured_pair.relationship).toBe("Captured historical relationship.");
  });

  it.each([
    {
      name: "missing left",
      entry: savedTradeEntry({ leftAvailable: false }),
      descriptor: tradeDescriptor(
        "moisture",
        "current-left",
        "Current left replacement",
        "More Moisture",
      ),
      choices: { left: "current-left", right: null },
    },
    {
      name: "missing right",
      entry: savedTradeEntry({ rightAvailable: false }),
      descriptor: tradeDescriptor(
        "current-right",
        "baseline",
        "Canonical BOMEX Baseline",
        "Current right replacement",
      ),
      choices: { left: null, right: "current-right" },
    },
    {
      name: "both missing",
      entry: savedTradeEntry({ leftAvailable: false, rightAvailable: false }),
      descriptor: tradeDescriptor(
        "current-right",
        "current-left",
        "Current left replacement",
        "Current right replacement",
      ),
      choices: { left: "current-left", right: "current-right" },
    },
  ])(
    "requires deliberate same-World replacement for $name without mutating the source",
    async ({ entry, descriptor, choices }) => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(new Response(JSON.stringify(entry), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }));

      render(
        <WorldCompare
          worldSlug="trade-cumulus"
          savedComparisonId={entry.record.saved_comparison_id}
          onBack={vi.fn()}
          onOpenSimulation={vi.fn()}
        />,
      );

      expect(await screen.findByText("Saved Comparison unavailable")).toBeVisible();
      expect(screen.getByText(/How does added moisture change cloud growth/)).toBeVisible();
      expect(screen.getByText(/Captured relationship/)).toBeVisible();
      const openReplacement = screen.getByRole("button", {
        name: "Open transient replacement pair",
      });
      expect(openReplacement).toBeDisabled();
      if (choices.left) {
        fireEvent.change(screen.getByLabelText("Replacement left"), {
          target: { value: choices.left },
        });
      }
      if (choices.right) {
        fireEvent.change(screen.getByLabelText("Replacement right"), {
          target: { value: choices.right },
        });
      }
      expect(openReplacement).toBeEnabled();
      fireEvent.click(openReplacement);

      expect(await screen.findByText("Transient replacement pair")).toBeVisible();
      expect(screen.getByText(/original remains unchanged/)).toBeVisible();
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "Save as new comparison" })).toBeEnabled(),
      );
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
      expect(vi.mocked(fetch).mock.calls.some(([, init]) => init?.method === "PATCH")).toBe(false);
      expect(entry.record.workspace.left_simulation_id).toBe("baseline");
      expect(entry.record.workspace.right_simulation_id).toBe("moisture");
    },
  );

  it("captures link, Context, Explore, and Supercells surface state exactly", async () => {
    const descriptor = supercellsFixtureDescriptor();
    const created = {
      ...savedTradeEntry(),
      record: {
        ...savedTradeEntry().record,
        saved_comparison_id: "b".repeat(32),
        title: "Rotating updraft surfaces",
      },
    };
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(descriptor), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(created), { status: 201 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(created), { status: 200 }));
    render(<WorldCompare worldSlug="supercells" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));
    fireEvent.click(await screen.findByRole("button", { name: "Aligned" }));
    fireEvent.click(screen.getByRole("button", { name: "Show Quarter-Circle Supercell scene" }));
    fireEvent.click(screen.getByRole("button", { name: "Show Context" }));
    fireEvent.click(screen.getByRole("button", { name: "Save comparison" }));
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Rotating updraft surfaces" },
    });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Save comparison" }),
    );

    await waitFor(() =>
      expect(
        vi
          .mocked(fetch)
          .mock.calls.some(
            ([url, init]) =>
              url === "/api/worlds/supercells/saved-comparisons" && init?.method === "POST",
          ),
      ).toBe(true),
    );
    const createCall = vi
      .mocked(fetch)
      .mock.calls.find(
        ([url, init]) =>
          url === "/api/worlds/supercells/saved-comparisons" && init?.method === "POST",
      );
    const body = JSON.parse(String(createCall?.[1]?.body)) as {
      workspace: {
        world_id: string;
        left_state: ExploreWorldState;
        right_state: ExploreWorldState;
        links: Record<string, boolean>;
        context_collapsed: boolean;
        supercells_presentation: { left: string; right: string };
      };
    };
    expect(body.workspace).toMatchObject({
      world_id: "supercells",
      links: { time: true, view: true, plane: true, camera: true, selection: true },
      context_collapsed: false,
      supercells_presentation: { left: "scene", right: "evidence" },
    });
    expect(body.workspace.left_state).toMatchObject({
      world_id: "supercells",
      lens_id: "rotating_updraft",
    });
    expect(body.workspace.right_state).toMatchObject({
      world_id: "supercells",
      lens_id: "rotating_updraft",
    });
  });

  it("disables saving while comparison playback is running", async () => {
    render(<WorldCompare worldSlug="trade-cumulus" onBack={vi.fn()} onOpenSimulation={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Open dual view" }));
    fireEvent.click(await screen.findByRole("button", { name: "Play Canonical BOMEX Baseline" }));
    expect(screen.getByRole("button", { name: "Save comparison" })).toBeDisabled();
  });
});

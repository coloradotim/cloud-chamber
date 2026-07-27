import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { type SupercellsWorldDetail, SupercellsWorld } from "./SupercellsWorld";

const world: SupercellsWorldDetail = {
  world_id: "supercells",
  display_name: "Supercells",
  short_description: "Inspect an evolving idealized rotating storm.",
  availability_state: "available",
  availability_message:
    "Quarter-Circle and Straight-Line Hodograph Supercells are available for Explore and Compare.",
  reference_simulation: {
    simulation_id: "supercells_quarter_circle_reference",
    display_name: "Quarter-Circle Supercell",
    role: "reference",
    world_id: "supercells",
    run_id: "quarter-circle-supercell-presentation-v1-20260723",
    case_id: "cm1_r21_1_quarter_circle_supercell_presentation_v1",
    parent_simulation_id: null,
    reference_simulation_id: "supercells_quarter_circle_reference",
    technical_state: "available",
    technical_state_message: "Ninety-one retained histories are available.",
    explore_available: true,
    saved_output_count: 91,
    model_start_seconds: 0,
    model_end_seconds: 10_800,
    history_cadence_seconds: 120,
    default_explore_time_index: 37,
    lineage_state: "known",
  },
  simulations: [],
  capabilities: {
    reference_explore: true,
    lab: false,
    compare: true,
    saved_views: false,
    saved_comparisons: true,
  },
  caveats: ["This idealized benchmark is not a forecast or a reconstruction of a real storm."],
};
const straightLineSimulation: SupercellsWorldDetail["simulations"][number] = {
  ...world.reference_simulation,
  simulation_id: "supercells_straight_line_hodograph",
  display_name: "Straight-Line Hodograph Supercell",
  role: "variation",
  run_id: "straight-line-supercell-presentation-v1-20260726",
  case_id: "cm1_r21_1_straight_line_supercell_presentation_v1",
  parent_simulation_id: "supercells_quarter_circle_reference",
};
world.simulations = [world.reference_simulation, straightLineSimulation];

describe("SupercellsWorld", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("exposes the real controlled pair for Explore and Compare", async () => {
    vi.mocked(fetch).mockResolvedValue(ok(world));
    const onExplore = vi.fn();
    const onCompare = vi.fn();
    const onBack = vi.fn();
    render(
      <SupercellsWorld
        onBackToWorlds={onBack}
        onExploreSimulation={onExplore}
        onCompare={onCompare}
        onOpenSavedComparison={vi.fn()}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Supercells" })).toBeInTheDocument();
    const navigation = screen.getByRole("navigation", { name: "Supercells sections" });
    expect(within(navigation).getByRole("button", { name: "Overview" })).toBeVisible();
    expect(within(navigation).getByRole("button", { name: "Simulations" })).toBeVisible();
    expect(within(navigation).getByRole("button", { name: "Saved Comparisons" })).toBeVisible();
    expect(within(navigation).queryByRole("button", { name: /Lab|Compare$/ })).toBeNull();
    expect(
      screen.getByRole("heading", { name: "Straight-Line Hodograph Supercell" }),
    ).toBeVisible();

    fireEvent.click(screen.getAllByRole("button", { name: "Explore" })[0]);
    expect(onExplore).toHaveBeenCalledWith(world.reference_simulation);
    fireEvent.click(screen.getAllByRole("button", { name: "Compare" })[1]);
    expect(onCompare).toHaveBeenCalledWith(straightLineSimulation);

    fireEvent.click(
      within(screen.getByRole("navigation", { name: "Breadcrumb" })).getByRole("button"),
    );
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("fails closed when the retained reference output is unavailable", async () => {
    const unavailable: SupercellsWorldDetail = {
      ...world,
      availability_state: "unavailable",
      availability_message: "The retained Supercell output is missing.",
      capabilities: { ...world.capabilities, reference_explore: false, compare: false },
      reference_simulation: {
        ...world.reference_simulation,
        technical_state: "missing",
        technical_state_message: "The retained run directory could not be found.",
        explore_available: false,
        saved_output_count: 0,
        model_start_seconds: null,
        model_end_seconds: null,
        history_cadence_seconds: null,
      },
      simulations: [],
    };
    unavailable.simulations = [
      unavailable.reference_simulation,
      {
        ...straightLineSimulation,
        technical_state: "missing",
        technical_state_message: "The retained run directory could not be found.",
        explore_available: false,
        saved_output_count: 0,
        model_start_seconds: null,
        model_end_seconds: null,
        history_cadence_seconds: null,
      },
    ];
    vi.mocked(fetch).mockResolvedValue(ok(unavailable));
    render(
      <SupercellsWorld
        onBackToWorlds={vi.fn()}
        onExploreSimulation={vi.fn()}
        onOpenSavedComparison={vi.fn()}
      />,
    );

    expect(await screen.findByText("The retained run directory could not be found.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Explore" })).toBeDisabled();
    expect(screen.getByText("The retained Supercell output is missing.")).toBeVisible();
  });

  it("keeps an endpoint failure local and retryable", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Output inventory failed." }), { status: 503 }),
      )
      .mockResolvedValueOnce(ok(world));
    render(
      <SupercellsWorld
        onBackToWorlds={vi.fn()}
        onExploreSimulation={vi.fn()}
        onOpenSavedComparison={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Output inventory failed.");
    fireEvent.click(screen.getByRole("button", { name: "Retry Supercells" }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Quarter-Circle Supercell" })).toBeVisible(),
    );
  });
});

function ok(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

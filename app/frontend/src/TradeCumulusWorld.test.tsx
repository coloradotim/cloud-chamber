import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  type SimulationRecord,
  TradeCumulusWorld,
  type TradeCumulusWorldDetail,
} from "./TradeCumulusWorld";

const baselineId = "result-trade-cumulus-5b-full-baseline-20260720T162342Z";
const moreId = "result-trade-cumulus-5b-full-more_moisture-20260720T162342Z";

const baseline: SimulationRecord = simulation({
  simulation_id: "trade_cumulus_canonical_bomex",
  display_name: "Canonical BOMEX Baseline",
  role: "reference",
  result_id: baselineId,
  run_id: "trade-cumulus-5b-full-baseline-20260720T162342Z",
  parent_simulation_id: null,
  reference_simulation_id: "trade_cumulus_canonical_bomex",
  lineage_state: "known",
});

const moreMoisture: SimulationRecord = simulation({
  simulation_id: "trade_cumulus_more_moisture",
  display_name: "More Moisture",
  role: "variation",
  result_id: moreId,
  run_id: "trade-cumulus-5b-full-more_moisture-20260720T162342Z",
  parent_simulation_id: "trade_cumulus_canonical_bomex",
  reference_simulation_id: "trade_cumulus_canonical_bomex",
  lineage_state: "known",
  compare_suggestions: [
    {
      comparison_id: "trade_cumulus_moisture_v1",
      display_name: "More Moisture versus Baseline",
      target_simulation_id: "trade_cumulus_canonical_bomex",
    },
  ],
  configuration_difference_from_reference: [
    {
      path: "run_configuration.surface_moisture_flux_g_g_m_s",
      label: "Surface moisture supply",
      category: "atmospheric",
      left_value: 0.000052,
      right_value: 0.000078,
      units: "g/g m/s",
      material: true,
    },
  ],
});

const labHistory = simulation({
  simulation_id: null,
  display_name: "Unretained Trade Cumulus result",
  role: "lab_history",
  result_id: "result-unlineaged",
  run_id: "run-unlineaged",
  parent_simulation_id: null,
  reference_simulation_id: null,
  lineage_state: "unlineaged",
  compare_suggestions: [],
  configuration_difference_from_reference: null,
});

const world: TradeCumulusWorldDetail = {
  world_id: "trade_cumulus",
  display_name: "Trade Cumulus",
  status: "mvp_candidate",
  short_description: "Investigate shallow maritime cumulus and surface moisture supply.",
  availability_state: "available",
  availability_message: "Reference, variation, and featured comparison are available.",
  reference_simulation: baseline,
  simulations: [baseline, moreMoisture],
  lab_history: [labHistory],
  featured_comparison: {
    comparison_id: "trade_cumulus_moisture_v1",
    display_name: "More Moisture versus Baseline",
    baseline_simulation_id: "trade_cumulus_canonical_bomex",
    more_moisture_simulation_id: "trade_cumulus_more_moisture",
    availability_state: "available",
    availability_message: "Featured comparison is available.",
    open_available: true,
  },
  lab_summary: {
    active_run_count: 0,
    completed_uninspected_run_count: 2,
    lab_history_count: 1,
    summary: "2 completed runs await inspection",
  },
  capabilities: {
    reference_explore: true,
    featured_comparison: true,
    lab: true,
    saved_views: false,
    ordinary_compare: false,
  },
  caveats: [],
};

describe("TradeCumulusWorld", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ok(world)));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the five approved sections and stable simulation names", async () => {
    renderWorld();
    expect(await screen.findByRole("heading", { name: "Trade Cumulus" })).toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Trade Cumulus sections" });
    for (const name of ["Overview", "Simulations", "Saved Views", "Comparisons", "Lab"]) {
      expect(within(nav).getByRole("button", { name })).toBeInTheDocument();
    }
    expect(screen.getAllByRole("heading", { name: "Canonical BOMEX Baseline" })).not.toHaveLength(
      0,
    );
    expect(screen.getByRole("heading", { name: "More Moisture" })).toBeInTheDocument();
    expect(screen.queryByText("result-unlineaged")).not.toBeInTheDocument();
  });

  it("opens stable Explore and featured Comparison actions", async () => {
    const onExplore = vi.fn();
    const onCompare = vi.fn();
    renderWorld({ onExploreSimulation: onExplore, onOpenFeaturedComparison: onCompare });
    await screen.findByRole("heading", { name: "Trade Cumulus" });

    fireEvent.click(
      within(screen.getByLabelText("Canonical BOMEX Baseline Simulation")).getByRole("button", {
        name: "Explore",
      }),
    );
    expect(onExplore).toHaveBeenCalledWith(baseline);
    fireEvent.click(screen.getByRole("button", { name: "Open Comparison" }));
    expect(onCompare).toHaveBeenCalledOnce();
  });

  it("keeps Saved Views honest and unlineaged results in Lab history", async () => {
    renderWorld();
    await screen.findByRole("heading", { name: "Trade Cumulus" });
    fireEvent.click(screen.getByRole("button", { name: "Saved Views" }));
    expect(
      screen.getByText("Saved Views are not implemented in this increment."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Lab" }));
    expect(screen.getByText("Build workspace retained")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Results" }));
    expect(screen.getByText("Results workspace retained")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Lab history (1)"));
    expect(screen.getByText("result-unlineaged")).toBeInTheDocument();
  });

  it("shows a missing reference and disables reference Explore", async () => {
    vi.mocked(fetch).mockResolvedValue(
      ok({
        ...world,
        availability_state: "partial",
        availability_message: "Canonical BOMEX Baseline is missing.",
        reference_simulation: {
          ...baseline,
          technical_state: "missing",
          technical_state_message: "Canonical BOMEX Baseline is missing.",
          technical_trust_state: "unavailable",
          explore_available: false,
        },
      }),
    );
    renderWorld();
    const card = await screen.findByLabelText("Canonical BOMEX Baseline Simulation");
    expect(within(card).getByText("Missing")).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Explore" })).toBeDisabled();
  });

  it("keeps runtime integrity secondary and displays moisture flux in g/kg m/s", async () => {
    renderWorld();
    const card = await screen.findByLabelText("More Moisture Simulation");

    expect(card).toHaveTextContent("0.05200 g/kg m/s to 0.07800 g/kg m/s");
    expect(within(card).getByText("Caveated output")).not.toBeVisible();
    fireEvent.click(within(card).getByText("Details"));
    expect(within(card).getByText("Runtime integrity")).toBeInTheDocument();
    expect(within(card).getByText("Caveated output")).toBeVisible();
  });

  it("shows retry and retained Lab content when World detail fails", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(error(500, "Trade Cumulus detail unavailable."))
      .mockResolvedValueOnce(ok(world));
    renderWorld();
    expect(await screen.findByRole("alert")).toHaveTextContent("Trade Cumulus detail unavailable.");
    expect(screen.getByText("Build workspace retained")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry Trade Cumulus" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: "Trade Cumulus" })).toBeInTheDocument();
  });
});

function renderWorld(
  overrides: Partial<{
    onExploreSimulation: (simulation: SimulationRecord) => void;
    onOpenFeaturedComparison: () => void;
  }> = {},
) {
  return render(
    <TradeCumulusWorld
      onBackToWorlds={vi.fn()}
      onExploreSimulation={overrides.onExploreSimulation ?? vi.fn()}
      onOpenFeaturedComparison={overrides.onOpenFeaturedComparison ?? vi.fn()}
      buildContent={<div>Build workspace retained</div>}
      resultsContent={<div>Results workspace retained</div>}
      initialLabSection="build"
    />,
  );
}

function simulation(overrides: Partial<SimulationRecord>): SimulationRecord {
  return {
    simulation_id: "simulation",
    display_name: "Simulation",
    role: "variation",
    world_id: "trade_cumulus",
    product_slice_id: "trade_cumulus_v1",
    case_id: "bomex_trade_cumulus_baseline_v0",
    result_id: "result",
    run_id: "run",
    source_recipe_id: null,
    parent_simulation_id: null,
    reference_simulation_id: "trade_cumulus_canonical_bomex",
    technical_state: "available",
    technical_state_message: "Completed output is available.",
    technical_trust_state: "caveated",
    explore_available: true,
    compare_suggestions: [],
    configuration_difference_from_reference: [],
    lineage_state: "valid",
    created_at: null,
    completed_at: null,
    ...overrides,
  };
}

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

function error(status: number, detail: string): Response {
  return { ok: false, status, json: async () => ({ detail }) } as Response;
}

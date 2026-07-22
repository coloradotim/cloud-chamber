import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MountainWavesWorld, type MountainWavesWorldDetail } from "./MountainWavesWorld";

const world: MountainWavesWorldDetail = {
  world_id: "mountain_waves",
  display_name: "Mountain Waves",
  short_description: "Investigate terrain-forced waves and the clouds they organize.",
  availability_state: "available",
  availability_message: "Dry Ridge and Boulder Windstorm are available.",
  default_parent_simulation_id: "mountain_waves_boulder_moist_reference",
  simulations: [
    {
      simulation_id: "mountain_waves_dry_ridge",
      display_name: "Dry Ridge",
      role: "built_in",
      world_id: "mountain_waves",
      run_id: "dry-run",
      case_id: "dry-case",
      parent_simulation_id: null,
      parent_run_id: null,
      reference_simulation_id: "mountain_waves_boulder_moist_reference",
      user_question: null,
      state: "available",
      state_message: "Completed output is inspectable.",
      inspectable: true,
      can_create_variation: true,
      moist: false,
      purpose: "A dry terrain-wave reference.",
      configuration: null,
      differences: {},
      warnings: [],
      caveats: ["This dry Simulation contains no moisture fields."],
      manifest_path: "/runs/dry/manifest.json",
      created_at: null,
      started_at: null,
      completed_at: null,
    },
    {
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
      state_message: "Completed output is inspectable.",
      inspectable: true,
      can_create_variation: true,
      moist: true,
      purpose: "A moist terrain-wave reference.",
      configuration: null,
      differences: {},
      warnings: [],
      caveats: ["Cloud state is instantaneous."],
      manifest_path: "/runs/moist/manifest.json",
      created_at: null,
      started_at: null,
      completed_at: null,
    },
  ],
  activity: [],
  history: [],
  lab_summary: {
    active_run_count: 0,
    packaged_run_count: 0,
    completed_simulation_count: 2,
    failed_run_count: 0,
    total_variation_count: 0,
  },
  caveats: ["Mountain Waves output is native 2-D x-z."],
};

describe("MountainWavesWorld", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/api/worlds/mountain-waves") return ok(world);
        if (url.includes("variation-template")) {
          return ok({
            parent_simulation_id: world.default_parent_simulation_id,
            parent_run_id: "moist-run",
            parent_display_name: "Boulder Windstorm",
            parent_configuration_source: "retained_exact_sounding",
            reference_simulation_id: world.default_parent_simulation_id,
            configuration: {
              terrain: { height_m: 1_000, half_width_m: 10_000, center_m: 0 },
              sounding: [
                {
                  height_m: 0,
                  pressure_pa: 100_000,
                  theta_k: 288,
                  qv_g_kg: 5,
                  u_m_s: 10,
                  v_m_s: 0,
                },
                {
                  height_m: 1_000,
                  pressure_pa: 90_000,
                  theta_k: 292,
                  qv_g_kg: 4,
                  u_m_s: 12,
                  v_m_s: 0,
                },
                {
                  height_m: 2_000,
                  pressure_pa: 80_000,
                  theta_k: 296,
                  qv_g_kg: 3,
                  u_m_s: 14,
                  v_m_s: 0,
                },
              ],
              duration_seconds: 3_600,
              output_cadence_seconds: 180,
            },
            can_create_variation: true,
            unavailable_reason: null,
          });
        }
        if (url.endsWith("/variations/preview")) {
          return ok({
            differences: {
              terrain: [],
              wind: [],
              moisture: [],
              "stability/thermodynamics": [],
              "numerics/time": [],
              output: [],
            },
            warnings: [],
            blocking_errors: [],
            derived_stability_n2_s2: [0.0001, 0.0001],
            terrain_profile: [],
          });
        }
        throw new Error(`Unexpected fetch ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("presents the retained references and opens either Simulation", async () => {
    const onExplore = vi.fn();
    render(<MountainWavesWorld onBackToWorlds={vi.fn()} onExploreSimulation={onExplore} />);

    expect(await screen.findByRole("heading", { name: "Mountain Waves" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dry Ridge" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Boulder Windstorm" })).toBeInTheDocument();
    const exploreButtons = screen.getAllByRole("button", { name: "Explore" });
    fireEvent.click(exploreButtons[1]);
    expect(onExplore).toHaveBeenCalledWith(world.simulations[1]);
  });

  it("opens the shared Lab on the selected parent", async () => {
    render(<MountainWavesWorld onBackToWorlds={vi.fn()} onExploreSimulation={vi.fn()} />);
    await screen.findByRole("heading", { name: "Boulder Windstorm" });
    const createButtons = screen.getAllByRole("button", { name: "Create variation" });
    fireEvent.click(createButtons[0]);
    expect(await screen.findByRole("heading", { name: /Change the terrain/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Variation" })).toHaveClass("active-control");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/worlds/mountain-waves/variation-template?"),
    );
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

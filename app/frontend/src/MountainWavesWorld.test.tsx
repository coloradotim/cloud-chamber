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
      moist_fields_available: false,
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
      moist_fields_available: true,
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
          const dry = url.includes("mountain_waves_dry_ridge");
          const recipePrefix = dry ? "mountain_waves_dry" : "mountain_waves_boulder";
          return ok({
            parent_simulation_id: dry
              ? "mountain_waves_dry_ridge"
              : world.default_parent_simulation_id,
            parent_run_id: dry ? "dry-run" : "moist-run",
            parent_display_name: dry ? "Dry Ridge" : "Boulder Windstorm",
            parent_configuration_source: "Hash-locked approved Recipe reference",
            reference_simulation_id: dry
              ? "mountain_waves_dry_ridge"
              : world.default_parent_simulation_id,
            recipe_id: dry ? "dry_ridge_mechanics" : "boulder_moist_wave",
            recipe_name: dry ? "Dry Ridge Mechanics" : "Boulder Moist Wave",
            recipe_contract_version: "1",
            controls: {
              recipe_id: dry ? "dry_ridge_mechanics" : "boulder_moist_wave",
              dry_ridge: dry
                ? {
                    ridge_height_m: 400,
                    ridge_half_width_m: 1_000,
                    cross_ridge_wind_m_s: 10,
                    dry_stability_n_s: 0.01,
                    wind_shear_through_10km_m_s: 0,
                    layered_stability: false,
                    lower_stability_n_s: 0.01,
                    upper_stability_n_s: 0.01,
                    stability_transition_height_m: 6_000,
                    stability_transition_width_m: 1_000,
                  }
                : null,
              boulder_moist: dry
                ? null
                : {
                    ridge_height_m: 2_000,
                    ridge_half_width_m: 10_000,
                    low_level_wind_m_s: 14.1,
                    shear_through_10km_m_s: 23.8,
                    lower_layer_rh_percent: 66,
                    midlevel_rh_percent: 34.5,
                    dry_air_counterpart: false,
                    lower_stability_factor: 1,
                    midlevel_stability_factor: 1,
                    upper_stability_factor: 1,
                  },
            },
            run_profiles: [
              {
                profile: {
                  profile_id: `${recipePrefix}_standard_v1`,
                  profile_name: "Standard — Working run",
                  role: "Standard",
                  recipe_id: dry ? "dry_ridge_mechanics" : "boulder_moist_wave",
                  numerical_realization: {
                    domain: "Generated from exact controls",
                    grid: "400 × 1 × 200",
                    spacing: "250 m × 250 m × 100 m",
                    timestep_strategy: "CM1 adaptive timestep",
                    physics_source: "Recipe contract version 1",
                  },
                  observation_plan: {
                    duration_seconds: 3_600,
                    output_cadence_seconds: 60,
                    expected_history_count: 61,
                    retained_field_inventory: ["w", "th", "uinterp"],
                  },
                  expected_runtime_min_seconds: 60,
                  expected_runtime_max_seconds: 120,
                  expected_size_min_bytes: 104_857_600,
                  expected_size_max_bytes: 209_715_200,
                  estimate_basis: "scaled_from_measured",
                  confidence: "moderate",
                  scientific_limitations: [],
                },
                current_free_space_bytes: 107_374_182_400,
                projected_free_space_bytes: 106_300_440_576,
                required_free_space_bytes: 524_288_000,
                disposition: "passes",
                disposition_reason: "Current free space satisfies the resolved profile.",
              },
            ],
            default_run_profile_id: `${recipePrefix}_standard_v1`,
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
    render(
      <MountainWavesWorld
        onBackToWorlds={vi.fn()}
        onExploreSimulation={onExplore}
        onOpenSavedComparison={vi.fn()}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Mountain Waves" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dry Ridge" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Boulder Windstorm" })).toBeInTheDocument();
    expect(screen.getByText("Start a related Simulation")).toBeInTheDocument();
    expect(screen.queryByText("Start an experiment")).not.toBeInTheDocument();
    const exploreButtons = screen.getAllByRole("button", { name: "Explore" });
    fireEvent.click(exploreButtons[1]);
    expect(onExplore).toHaveBeenCalledWith(world.simulations[1]);
  });

  it("opens Create Variation on the selected parent", async () => {
    render(
      <MountainWavesWorld
        onBackToWorlds={vi.fn()}
        onExploreSimulation={vi.fn()}
        onOpenSavedComparison={vi.fn()}
      />,
    );
    await screen.findByRole("heading", { name: "Boulder Windstorm" });
    const createButtons = screen.getAllByRole("button", { name: "Create variation" });
    fireEvent.click(createButtons[1]);
    expect(
      await screen.findByRole("heading", { name: "Atmosphere and terrain" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Boulder Moist Wave")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Variation" })).toHaveClass("active-control");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/worlds/mountain-waves/variation-template?"),
    );
  });
});

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MountainWavesVariationEditor } from "./MountainWavesVariationEditor";
import type {
  MountainWavesSimulation,
  MountainWavesWorldDetail,
} from "./MountainWavesWorld";

const moistControls = {
  recipe_id: "boulder_moist_wave",
  dry_ridge: null,
  boulder_moist: {
    ridge_height_m: 2_000,
    ridge_half_width_m: 10_000,
    flow_strength_factor: 1,
    wind_offset_m_s: 0,
    shear_strength_factor: 1,
    lower_rh_deficit_factor: 1,
    midlevel_rh_deficit_factor: 1,
    dry_air_counterpart: false,
    lower_stability_factor: 1,
    midlevel_stability_factor: 1,
    upper_stability_factor: 1,
  },
};

const dryControls = {
  recipe_id: "dry_ridge_mechanics",
  dry_ridge: {
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
  },
  boulder_moist: null,
};

const world = {
  world_id: "mountain_waves",
  display_name: "Mountain Waves",
  short_description: "Mountain waves",
  availability_state: "available",
  availability_message: "Available",
  default_parent_simulation_id: "mountain_waves_boulder_moist_reference",
  simulations: [
    simulation({
      simulationId: "mountain_waves_boulder_moist_reference",
      displayName: "Boulder Windstorm",
      runId: "moist-parent-run",
      moist: true,
    }),
    simulation({
      simulationId: "mountain_waves_dry_ridge_reference",
      displayName: "Dry Ridge",
      runId: "dry-parent-run",
      moist: false,
    }),
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
  caveats: [],
} satisfies MountainWavesWorldDetail;

describe("MountainWavesVariationEditor", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("variation-template")) {
          const dry = url.includes("mountain_waves_dry_ridge_reference");
          return ok(
            template({
              parentSimulationId: dry
                ? "mountain_waves_dry_ridge_reference"
                : "mountain_waves_boulder_moist_reference",
              parentRunId: dry ? "dry-parent-run" : "moist-parent-run",
              parentDisplayName: dry ? "Dry Ridge" : "Boulder Windstorm",
              recipeId: dry ? "dry_ridge_mechanics" : "boulder_moist_wave",
              recipeName: dry ? "Dry Ridge Mechanics" : "Boulder Moist Wave",
              controls: dry ? dryControls : moistControls,
            }),
          );
        }
        if (url.endsWith("/variations/preview")) {
          const body = JSON.parse(String(init?.body));
          const dry = body.recipe_id === "dry_ridge_mechanics";
          const ridgeHeight = dry
            ? body.controls.dry_ridge.ridge_height_m
            : body.controls.boulder_moist.ridge_height_m;
          const referenceHeight = dry ? 400 : 2_000;
          return ok(preview(body.recipe_id, ridgeHeight, referenceHeight, body.run_profile_id));
        }
        if (url.endsWith("/variations")) {
          return ok({
            simulation_id: "mountain_waves_broader_ridge_1234",
            run_id: "run-variation",
            manifest_path: "/runs/variation/manifest.json",
            package_dir: "/runs/variation",
            launch_review_snapshot_id: "launch-review-123",
            warnings: [],
          });
        }
        if (url === "/api/runs/queue") return ok({ state: "queued" });
        throw new Error(`Unexpected fetch ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("previews exact Recipe changes and keeps packaging separate from queueing", async () => {
    const onCreated = vi.fn();
    render(
      <MountainWavesVariationEditor
        world={world}
        initialParentSimulationId={world.default_parent_simulation_id}
        onCreated={onCreated}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Atmosphere and terrain" })).toBeInTheDocument();
    expect(screen.getByText("Boulder Moist Wave")).toBeInTheDocument();
    await screen.findByText("0 material changes");
    expect(
      await screen.findByRole("heading", { name: "Resolved scientific profiles" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Cross-ridge wind")).toBeInTheDocument();
    expect(screen.getByText("Relative humidity")).toBeInTheDocument();
    expect(screen.getByText("Water vapor")).toBeInTheDocument();
    expect(screen.getByText("Potential temperature")).toBeInTheDocument();
    expect(screen.getByText("Static stability")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Ridge height"), { target: { value: "2200" } });
    expect(await screen.findByText("1 material changes")).toBeInTheDocument();
    expect(screen.getAllByText("Ridge height")).toHaveLength(2);

    fireEvent.change(screen.getByLabelText("Variation name"), {
      target: { value: "Taller Boulder ridge" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Package variation" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Package variation" }));

    expect(await screen.findByText("Packaged, not queued")).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalledWith("/api/runs/queue", expect.anything());

    fireEvent.click(screen.getByRole("button", { name: "Queue CM1 run" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/queue",
      expect.objectContaining({
        body: JSON.stringify({ manifest_path: "/runs/variation/manifest.json" }),
      }),
    );
  });

  it("switches to the dry Recipe and its bounded controls with the parent", async () => {
    render(
      <MountainWavesVariationEditor
        world={world}
        initialParentSimulationId={world.default_parent_simulation_id}
        onCreated={vi.fn()}
      />,
    );

    const parent = await screen.findByLabelText("Parent Simulation");
    fireEvent.change(parent, { target: { value: "mountain_waves_dry_ridge_reference" } });

    expect(await screen.findByText("Dry Ridge Mechanics")).toBeInTheDocument();
    expect(screen.getByLabelText("Cross-ridge wind")).toBeInTheDocument();
    expect(screen.getByLabelText("Dry stability N")).toBeInTheDocument();
    expect(screen.queryByLabelText("Lower RH deficit")).not.toBeInTheDocument();
  });

  it("shows run-profile differences as product language rather than contract ids", async () => {
    render(
      <MountainWavesVariationEditor
        world={world}
        initialParentSimulationId={world.default_parent_simulation_id}
        onCreated={vi.fn()}
      />,
    );

    await screen.findByText("0 material changes");
    fireEvent.click(screen.getByRole("radio", { name: /Presentation/ }));

    expect(await screen.findByText("1 material changes")).toBeInTheDocument();
    expect(screen.getByText("Standard profile → Presentation profile")).toBeInTheDocument();
    expect(screen.queryByText(/mountain waves boulder presentation v1/i)).not.toBeInTheDocument();
  });
});

function simulation({
  simulationId,
  displayName,
  runId,
  moist,
}: {
  simulationId: string;
  displayName: string;
  runId: string;
  moist: boolean;
}): MountainWavesSimulation {
  return {
    simulation_id: simulationId,
    display_name: displayName,
    role: "built_in" as const,
    world_id: "mountain_waves",
    run_id: runId,
    case_id: `${simulationId}-case`,
    parent_simulation_id: null,
    parent_run_id: null,
    reference_simulation_id: simulationId,
    user_question: null,
    state: "available" as const,
    state_message: "Available",
    inspectable: true,
    can_create_variation: true,
    moist,
    moist_fields_available: moist,
    purpose: "Reference",
    configuration: null,
    differences: {},
    warnings: [],
    caveats: [],
    manifest_path: `/runs/${runId}/run_manifest.json`,
    created_at: null,
    started_at: null,
    completed_at: null,
  };
}

function template({
  parentSimulationId,
  parentRunId,
  parentDisplayName,
  recipeId,
  recipeName,
  controls,
}: {
  parentSimulationId: string;
  parentRunId: string;
  parentDisplayName: string;
  recipeId: string;
  recipeName: string;
  controls: typeof moistControls | typeof dryControls;
}) {
  const prefix = recipeId === "dry_ridge_mechanics" ? "mountain_waves_dry" : "mountain_waves_boulder";
  return {
    parent_simulation_id: parentSimulationId,
    parent_run_id: parentRunId,
    parent_display_name: parentDisplayName,
    parent_configuration_source: "Hash-locked approved Recipe reference",
    reference_simulation_id: parentSimulationId,
    recipe_id: recipeId,
    recipe_name: recipeName,
    recipe_contract_version: "1",
    controls,
    run_profiles: [
      costEstimate(`${prefix}_quick_v1`, "Quick", "Quick — Characterization"),
      costEstimate(`${prefix}_standard_v1`, "Standard", "Standard — Working run"),
      costEstimate(`${prefix}_presentation_v1`, "Presentation", "Presentation — Review"),
      costEstimate(`${prefix}_extended_v1`, "Extended", "Extended — Uncharacterized", true),
    ],
    default_run_profile_id: `${prefix}_standard_v1`,
    can_create_variation: true,
    unavailable_reason: null,
  };
}

function costEstimate(profileId: string, role: string, profileName: string, blocked = false) {
  return {
    profile: {
      profile_id: profileId,
      profile_name: profileName,
      role,
      recipe_id: profileId.includes("_dry_") ? "dry_ridge_mechanics" : "boulder_moist_wave",
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
      expected_runtime_min_seconds: blocked ? null : 60,
      expected_runtime_max_seconds: blocked ? null : 120,
      expected_size_min_bytes: blocked ? null : 100 * 1024 ** 2,
      expected_size_max_bytes: blocked ? null : 200 * 1024 ** 2,
      estimate_basis: blocked ? "uncharacterized" : "scaled_from_measured",
      confidence: blocked ? "none" : "moderate",
      scientific_limitations: [],
    },
    current_free_space_bytes: 100 * 1024 ** 3,
    projected_free_space_bytes: blocked ? null : 99 * 1024 ** 3,
    required_free_space_bytes: blocked ? null : 500 * 1024 ** 2,
    disposition: blocked ? "blocked" : "passes",
    disposition_reason: blocked
      ? "Extended has not been characterized."
      : "Current free space satisfies the resolved profile.",
  };
}

function preview(
  recipeId: string,
  ridgeHeight: number,
  referenceHeight: number,
  runProfileId: string,
) {
  const changed = ridgeHeight !== referenceHeight;
  const terrainDifferences = changed
    ? [{ label: "Ridge height", before: referenceHeight, after: ridgeHeight, units: "m" }]
    : [];
  const prefix = recipeId === "dry_ridge_mechanics" ? "mountain_waves_dry" : "mountain_waves_boulder";
  const profileChanged = runProfileId !== `${prefix}_standard_v1`;
  const numericalDifferences = profileChanged
    ? [
        {
          label: "Run profile",
          before: `${prefix}_standard_v1`,
          after: runProfileId,
          units: null,
        },
      ]
    : [];
  return {
    recipe_id: recipeId,
    recipe_name: recipeId === "dry_ridge_mechanics" ? "Dry Ridge Mechanics" : "Boulder Moist Wave",
    differences: {
      terrain: terrainDifferences,
      wind: [],
      moisture: [],
      "stability/thermodynamics": [],
      "forcing/initiation": [],
      "numerical realization": numericalDifferences,
      "observation plan": [],
    },
    relationship_classification: changed
      ? profileChanged
        ? "mixed_variation"
        : "controlled_physical_variation"
      : profileChanged
        ? "numerical_sensitivity"
        : null,
    warnings: [],
    blocking_errors: [],
    diagnostics: {
      maximum_terrain_slope: 0.18,
      cells_per_half_width: 40,
      nondimensional_mountain_height: 1.2,
      nonhydrostatic_width_parameter: 10,
      critical_levels_m: [],
      terrain_resolution: "well resolved",
      upstream_clearance_km: 40,
      downstream_clearance_km: 60,
      advective_time_seconds: 3_600,
      periodic_wrap_time_seconds: 10_800,
      model_top_m: 25_000,
      damping_base_m: 20_000,
      labels: ["Nonlinear wave response", "No critical level"],
    },
    terrain_profile: [
      { x_m: -10_000, height_m: 0 },
      { x_m: 0, height_m: ridgeHeight },
      { x_m: 10_000, height_m: 0 },
    ],
    wind_profile: [{ height_m: 0, value: 12 }],
    moisture_profile: [{ height_m: 0, value: recipeId === "dry_ridge_mechanics" ? 0 : 8 }],
    relative_humidity_profile: [
      { height_m: 0, value: recipeId === "dry_ridge_mechanics" ? 0 : 72 },
    ],
    theta_profile: [{ height_m: 0, value: 288 }],
    stability_profile: [{ height_m: 0, n2_s2: 0.0001 }],
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
    cost_estimate: costEstimate(
      runProfileId,
      profileChanged ? "Presentation" : "Standard",
      profileChanged ? "Presentation — Review" : "Standard — Working run",
    ),
  };
}

function ok(payload: unknown): Response {
  return { ok: true, json: async () => payload } as Response;
}

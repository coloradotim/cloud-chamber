import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SupercellsVariationEditor } from "./SupercellsVariationEditor";
import type { SupercellsWorldDetail } from "./SupercellsWorld";

const referenceControls = {
  hodograph_family: "quarter_circle",
  shear_0_6_km_m_s: 32,
  shear_0_2_km_m_s: 14,
  turning_depth_km_agl: 3,
  shear_6_12_km_m_s: 8,
  upper_shear_direction_relative_deg: 0,
  mean_wind_0_6_km_speed_m_s: 12.5,
  mean_wind_0_6_km_direction_deg: 15,
  surface_based_cape_j_kg: 2_500,
  buoyancy_distribution: "reference",
  lcl_height_m_agl: 1_000,
  midlevel_rh_percent: 50,
  cin_j_kg: 25,
  thermal_perturbation_amplitude_k: 1,
  thermal_horizontal_radius_km: 10,
  thermal_vertical_radius_km: 1.4,
  thermal_center_height_km_agl: 1.4,
  thermal_center_x_km: 0,
  thermal_center_y_km: 0,
};

const referenceSimulation = simulation({
  simulationId: "supercells_quarter_circle_reference",
  displayName: "Quarter-Circle Supercell",
  role: "reference",
  runId: "quarter-run",
});
const straightSimulation = simulation({
  simulationId: "supercells_straight_line_hodograph",
  displayName: "Straight-Line Hodograph Supercell",
  role: "variation",
  runId: "straight-run",
});
const world: SupercellsWorldDetail = {
  world_id: "supercells",
  display_name: "Supercells",
  short_description: "Idealized deep convection",
  availability_state: "available",
  availability_message: "Two retained Simulations are available.",
  reference_simulation: referenceSimulation,
  simulations: [referenceSimulation, straightSimulation],
  capabilities: {
    reference_explore: true,
    lab: false,
    compare: true,
    saved_views: false,
    saved_comparisons: true,
    create_variation: true,
  },
  caveats: [],
};

describe("SupercellsVariationEditor", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("variation-template")) {
          const straight = url.includes("supercells_straight_line_hodograph");
          return ok(template(straight));
        }
        if (url.endsWith("/variations/preview")) {
          const body = JSON.parse(String(init?.body));
          return ok(preview(body));
        }
        if (url.endsWith("/variations")) {
          return ok({
            simulation_id: "supercells_direct_environment_abcd1234",
            run_id: "supercells-variation-run",
            manifest_path: "/runs/supercells-variation-run/run_manifest.json",
            package_dir: "/runs/supercells-variation-run",
            launch_review_snapshot_id: "launch-review-supercells",
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

  it("uses direct physical controls and backend-derived scientific previews", async () => {
    render(
      <SupercellsVariationEditor
        world={world}
        initialParentSimulationId={referenceSimulation.simulation_id}
        onCreated={vi.fn()}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Environment and initiation" }),
    ).toBeVisible();
    expect(screen.getByLabelText("0–6 km shear value")).toHaveValue(32);
    expect(screen.getByLabelText("Surface-based CAPE value")).toHaveValue(2_500);
    expect(screen.getByLabelText("Thermal perturbation value")).toHaveValue(1);
    expect(screen.queryByText(/multiplier|concentration fraction/i)).not.toBeInTheDocument();
    expect(await screen.findByRole("img", { name: "Resolved hodograph" })).toBeVisible();
    expect(screen.getByRole("img", { name: "Resolved parcel buoyancy profile" })).toBeVisible();
    expect(screen.getByRole("img", { name: "Resolved thermal cross-section" })).toBeVisible();

    fireEvent.change(screen.getByLabelText("0–6 km shear value"), {
      target: { value: "60" },
    });
    expect(await screen.findByText("1 material change")).toBeVisible();
    const review = screen.getByLabelText("Variation review");
    expect(within(review).getAllByText("60.0 m/s", { exact: false })).toHaveLength(2);
    expect(within(review).getByText("Controlled physical variation")).toBeVisible();
  });

  it("packages separately from queueing and preserves the exact request", async () => {
    const onCreated = vi.fn();
    render(
      <SupercellsVariationEditor
        world={world}
        initialParentSimulationId={referenceSimulation.simulation_id}
        onCreated={onCreated}
      />,
    );
    await screen.findByText("0 material changes");
    fireEvent.change(screen.getByLabelText("0–2 km shear value"), {
      target: { value: "22" },
    });
    fireEvent.change(screen.getByLabelText("Variation name"), {
      target: { value: "Stronger low-level shear" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Package variation" })).toBeEnabled(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Package variation" }));

    expect(
      await screen.findByText("Stronger low-level shear is packaged. It has not been queued."),
    ).toBeVisible();
    expect(onCreated).not.toHaveBeenCalled();
    expect(fetch).toHaveBeenCalledWith(
      "/api/worlds/supercells/variations",
      expect.objectContaining({
        body: expect.stringContaining('"shear_0_2_km_m_s":22'),
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Queue CM1 run" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(fetch).toHaveBeenCalledWith(
      "/api/runs/queue",
      expect.objectContaining({
        body: JSON.stringify({
          manifest_path: "/runs/supercells-variation-run/run_manifest.json",
        }),
      }),
    );
  });

  it("switches parent values without compounding and blocks impossible geometry", async () => {
    render(
      <SupercellsVariationEditor
        world={world}
        initialParentSimulationId={referenceSimulation.simulation_id}
        onCreated={vi.fn()}
      />,
    );
    const parent = await screen.findByLabelText("Parent Simulation");
    fireEvent.change(parent, {
      target: { value: straightSimulation.simulation_id },
    });

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Straight" })).toHaveAttribute(
        "aria-pressed",
        "true",
      ),
    );
    fireEvent.change(screen.getByLabelText("Horizontal radius value"), {
      target: { value: "40" },
    });
    expect(
      await screen.findByText(/thermal does not fit inside the selected domain/i),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Package variation" })).toBeDisabled();
  });
});

function simulation({
  simulationId,
  displayName,
  role,
  runId,
}: {
  simulationId: string;
  displayName: string;
  role: "reference" | "variation";
  runId: string;
}): SupercellsWorldDetail["simulations"][number] {
  return {
    simulation_id: simulationId,
    display_name: displayName,
    role,
    world_id: "supercells",
    run_id: runId,
    case_id: `${runId}-case`,
    parent_simulation_id: role === "reference" ? null : "supercells_quarter_circle_reference",
    reference_simulation_id: "supercells_quarter_circle_reference",
    technical_state: "available",
    technical_state_message: "Available",
    explore_available: true,
    saved_output_count: 91,
    model_start_seconds: 0,
    model_end_seconds: 10_800,
    history_cadence_seconds: 120,
    default_explore_time_index: 37,
    lineage_state: "known",
    recipe_contract_version: "1",
    relationship_classification: role === "reference" ? null : "controlled_physical_variation",
    run_profile_id: "supercells_presentation_v1",
    can_create_variation: true,
    parent_eligibility_reason: "Accepted retained output.",
  };
}

function template(straight: boolean) {
  const controls = {
    ...referenceControls,
    hodograph_family: straight ? "straight" : "quarter_circle",
  };
  return {
    parent_simulation_id: straight
      ? "supercells_straight_line_hodograph"
      : "supercells_quarter_circle_reference",
    parent_run_id: straight ? "straight-run" : "quarter-run",
    parent_display_name: straight
      ? "Straight-Line Hodograph Supercell"
      : "Quarter-Circle Supercell",
    parent_configuration_source: "Accepted retained presentation evidence",
    reference_simulation_id: "supercells_quarter_circle_reference",
    recipe_id: "idealized_isolated_supercell",
    recipe_name: "Idealized Isolated Supercell",
    recipe_contract_version: "1",
    controls,
    reference_controls: referenceControls,
    run_profiles: [
      costEstimate("supercells_quick_v1", "Quick"),
      costEstimate("supercells_standard_v1", "Standard"),
    ],
    default_run_profile_id: "supercells_standard_v1",
    can_create_variation: true,
    unavailable_reason: null,
  };
}

function preview(body: { controls: typeof referenceControls; run_profile_id: string }) {
  const differences =
    body.controls.shear_0_6_km_m_s === referenceControls.shear_0_6_km_m_s &&
    body.controls.shear_0_2_km_m_s === referenceControls.shear_0_2_km_m_s
      ? []
      : [
          {
            path:
              body.controls.shear_0_6_km_m_s !== referenceControls.shear_0_6_km_m_s
                ? "controls.shear_0_6_km_m_s"
                : "controls.shear_0_2_km_m_s",
            label:
              body.controls.shear_0_6_km_m_s !== referenceControls.shear_0_6_km_m_s
                ? "0–6 km shear"
                : "0–2 km shear",
            before:
              body.controls.shear_0_6_km_m_s !== referenceControls.shear_0_6_km_m_s
                ? referenceControls.shear_0_6_km_m_s
                : referenceControls.shear_0_2_km_m_s,
            after:
              body.controls.shear_0_6_km_m_s !== referenceControls.shear_0_6_km_m_s
                ? body.controls.shear_0_6_km_m_s
                : body.controls.shear_0_2_km_m_s,
            units: "m/s",
          },
        ];
  const blocked = body.controls.thermal_horizontal_radius_km >= 40;
  return {
    reference_controls: referenceControls,
    parent_controls: referenceControls,
    requested_controls: body.controls,
    achieved_controls: body.controls,
    differences: {
      wind: differences,
      thermodynamics: [],
      initiation: [],
      numerical: [],
      observation: [],
    },
    relationship_classification: differences.length ? "controlled_physical_variation" : null,
    warnings: [],
    blocking_errors: blocked
      ? ["The thermal does not fit inside the selected domain clearance."]
      : [],
    diagnostics: {
      achieved_cape_j_kg: body.controls.surface_based_cape_j_kg,
      achieved_cin_j_kg: body.controls.cin_j_kg,
      achieved_lcl_height_m_agl: body.controls.lcl_height_m_agl,
      achieved_midlevel_rh_percent: body.controls.midlevel_rh_percent,
      freezing_level_m_agl: 4_200,
      hydrostatic_residual_pa: 0,
      shear_0_1_km_m_s: body.controls.shear_0_2_km_m_s / 2,
      shear_0_2_km_m_s: body.controls.shear_0_2_km_m_s,
      shear_0_3_km_m_s: 24,
      shear_0_6_km_m_s: body.controls.shear_0_6_km_m_s,
      shear_6_12_km_m_s: body.controls.shear_6_12_km_m_s,
      mean_wind_0_6_km_speed_m_s: body.controls.mean_wind_0_6_km_speed_m_s,
      mean_wind_0_6_km_direction_deg: body.controls.mean_wind_0_6_km_direction_deg,
      storm_relative_helicity_0_1_km_m2_s2: 95,
      storm_relative_helicity_0_3_km_m2_s2: 240,
      model_translation_u_m_s: 12,
      model_translation_v_m_s: 3,
      minimum_boundary_clearance_km: 35,
      minimum_vertical_clearance_km: 10,
      labels: [],
    },
    sounding: [
      sounding(0, -0.02),
      sounding(1_000, 0.08),
      sounding(6_000, 0.03),
      sounding(12_000, -0.01),
    ],
    hodograph: [
      { height_m: 0, u_m_s: -4, v_m_s: -6 },
      { height_m: 2_000, u_m_s: 5, v_m_s: 4 },
      { height_m: 6_000, u_m_s: 24, v_m_s: 9 },
      { height_m: 12_000, u_m_s: 30, v_m_s: 14 },
    ],
    initiation: {
      amplitude_k: body.controls.thermal_perturbation_amplitude_k,
      horizontal_radius_m: body.controls.thermal_horizontal_radius_km * 1_000,
      vertical_radius_m: body.controls.thermal_vertical_radius_km * 1_000,
      center_height_m_agl: body.controls.thermal_center_height_km_agl * 1_000,
      center_x_m: body.controls.thermal_center_x_km * 1_000,
      center_y_m: body.controls.thermal_center_y_km * 1_000,
    },
    numerical_realization: costEstimate(body.run_profile_id, "Standard").profile
      .numerical_realization,
    observation_plan: costEstimate(body.run_profile_id, "Standard").profile.observation_plan,
    useful_window_end_seconds: 10_800,
    cost_estimate: costEstimate(body.run_profile_id, "Standard"),
  };
}

function sounding(height_m: number, parcel_buoyancy_m_s2: number) {
  return {
    height_m,
    pressure_pa: 100_000 - height_m * 10,
    theta_k: 300 + height_m / 1_000,
    temperature_k: 295 - height_m / 1_000,
    qv_g_kg: Math.max(0.5, 14 - height_m / 1_000),
    relative_humidity_percent: 50,
    parcel_temperature_k: 296 - height_m / 1_000,
    parcel_buoyancy_m_s2,
    u_m_s: 0,
    v_m_s: 0,
  };
}

function costEstimate(profileId: string, role: string) {
  return {
    profile: {
      profile_id: profileId,
      profile_name: `${role} — Three-hour storm experiment`,
      role,
      recipe_id: "idealized_isolated_supercell",
      numerical_realization: {
        domain: "120 km × 120 km × 20 km",
        grid: "160 × 160 × 50",
        spacing: "750 × 750 × 400 m",
        timestep_strategy: "target 4.5 s",
        physics_source: "CM1 r21.1",
        exact_domain: {
          nx: 160,
          ny: 160,
          nz: 50,
          dx_m: 750,
          dy_m: 750,
          dz_m: 400,
          x_min_m: -60_000,
          x_max_m: 60_000,
          y_min_m: -60_000,
          y_max_m: 60_000,
          model_top_m: 20_000,
          timestep_seconds: 4.5,
        },
      },
      observation_plan: {
        duration_seconds: 10_800,
        output_cadence_seconds: 180,
        expected_history_count: 61,
        retained_field_inventory: ["winterp", "zvort", "uh", "dbz", "rain"],
      },
      expected_runtime_min_seconds: 2_700,
      expected_runtime_max_seconds: 4_500,
      expected_size_min_bytes: 2_000_000_000,
      expected_size_max_bytes: 3_000_000_000,
      estimate_basis: "scaled_from_measured",
      confidence: "provisional",
      scientific_limitations: ["Low-level detail is coarsely represented."],
    },
    current_free_space_bytes: 100_000_000_000,
    projected_free_space_bytes: 97_000_000_000,
    required_free_space_bytes: 5_000_000_000,
    disposition: "passes",
    disposition_reason: "Storage gate passes.",
  };
}

function ok(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

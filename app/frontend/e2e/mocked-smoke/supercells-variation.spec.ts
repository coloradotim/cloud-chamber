import { expect, test, type Page, type Route } from "@playwright/test";

import { collectConsoleProblems, gotoApp } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

const referenceControls = {
  hodograph_family: "quarter_circle",
  shear_0_6_km_m_s: 31.78049716414141,
  shear_0_2_km_m_s: 9.899494936611665,
  turning_depth_km_agl: 2,
  shear_6_12_km_m_s: 8,
  upper_shear_direction_relative_deg: 0,
  mean_wind_0_6_km_speed_m_s: 14.84893644992435,
  mean_wind_0_6_km_direction_deg: 24.47588900324574,
  surface_based_cape_j_kg: 2_200,
  buoyancy_distribution: "reference",
  lcl_height_m_agl: 1_000,
  midlevel_rh_percent: 45,
  cin_j_kg: 25,
  thermal_perturbation_amplitude_k: 1,
  thermal_horizontal_radius_km: 10,
  thermal_vertical_radius_km: 1.4,
  thermal_center_height_km_agl: 1.4,
  thermal_center_x_km: 0,
  thermal_center_y_km: 0,
};

const reference = simulation(
  "supercells_quarter_circle_reference",
  "Quarter-Circle Supercell",
  "reference",
  "quarter-circle-presentation",
);
const straight = simulation(
  "supercells_straight_line_hodograph",
  "Straight-Line Hodograph Supercell",
  "variation",
  "straight-line-presentation",
);
const descendant = simulation(
  "supercells_direct_environment_abcd1234",
  "Broader Supercell Experiment",
  "variation",
  "supercells-direct-environment-run",
);

test.describe("mocked smoke: Supercells variation contract", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockCloudChamberApis(page);
    await mockSupercellsVariationPath(page);
  });

  test("reviews direct controls, classifications, blockers, lifecycle, and descendant reuse", async ({
    page,
  }) => {
    const consoleProblems = collectConsoleProblems(page);
    await gotoCreateVariation(page);

    await expect(page.getByRole("button", { name: "Quarter Circle" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel("0–6 km shear value", { exact: true })).toHaveValue("31.78");
    await expect(page.getByLabel("Surface-based CAPE value")).toHaveValue("2200");
    await expect(page.getByRole("img", { name: "Resolved hodograph" })).toBeVisible();
    await expect(page.getByRole("img", { name: "Resolved parcel buoyancy profile" })).toBeVisible();
    await expect(page.getByRole("img", { name: "Resolved thermal cross-section" })).toBeVisible();

    await page.getByRole("button", { name: "Straight" }).click();
    await expect(page.getByText("Controlled physical variation")).toBeVisible();
    await page.getByLabel("Surface-based CAPE value").fill("4200");
    await expect(page.getByText("Multi-factor physical variation")).toBeVisible();

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByLabel("Thermal perturbation value").fill("-1");
    await expect(page.getByText("Controlled initiation sensitivity")).toBeVisible();
    await page.getByRole("radio", { name: /Standard/ }).check();
    await expect(page.getByText("Mixed physical and numerical variation")).toBeVisible();

    await page.getByLabel("Surface-based CAPE value").fill("8000");
    await page.getByLabel("LCL height value").fill("4000");
    await expect(page.getByRole("alert")).toContainText(
      "cannot jointly resolve 8,000 J/kg CAPE with a 4,000 m LCL",
    );
    await expect(page.getByRole("button", { name: "Package variation" })).toBeDisabled();

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByText("Horizontal placement", { exact: true }).click();
    await page.getByLabel("Horizontal radius value").fill("40");
    await page.getByLabel("Center x value").fill("60");
    await expect(page.getByRole("alert")).toContainText(
      "does not fit inside the generated horizontal domain",
    );

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByRole("radio", { name: /Extended/ }).check();
    await expect(page.getByRole("alert")).toContainText("Projected free space would fall below");
    await expect(page.getByRole("button", { name: "Package variation" })).toBeDisabled();

    await page.getByRole("button", { name: "Restore parent" }).click();
    await page.getByLabel("Variation name").fill("Broader Supercell Experiment");
    await page.getByLabel("0–6 km shear value", { exact: true }).fill("45");
    await expect(page.getByText("Controlled physical variation")).toBeVisible();
    await page.getByRole("button", { name: "Package variation" }).click();
    await expect(page.getByText("Packaged, not queued")).toBeVisible();
    await expect(page.getByRole("button", { name: "Queue CM1 run" })).toBeVisible();
    await page.getByRole("button", { name: "Queue CM1 run" }).click();

    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
    const lifecycle = page.locator("article", { hasText: "Broader Supercell Experiment" });
    await expect(lifecycle).toBeVisible();
    await lifecycle.getByText("Technical details").click();
    await expect(lifecycle.getByRole("region", { name: "Technical attempts" })).toContainText(
      "Failed",
    );
    await expect(lifecycle.getByRole("region", { name: "Technical attempts" })).toContainText(
      "Completed",
    );

    await page.getByRole("button", { name: "Simulations" }).click();
    const available = page.locator("article", { hasText: "Broader Supercell Experiment" });
    await expect(available.getByRole("button", { name: "Explore" })).toBeEnabled();
    await expect(available.getByRole("button", { name: "Compare" })).toBeEnabled();
    await expect(available.getByRole("button", { name: "Create variation" })).toBeEnabled();
    await available.getByRole("button", { name: "Create variation" }).click();
    await expect(page.getByLabel("Parent Simulation")).toHaveValue(descendant.simulation_id);

    expect(consoleProblems).toEqual([]);
  });

  test("keeps the complete editor coherent in the narrower desktop acceptance size", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1024, height: 856 });
    await gotoCreateVariation(page);

    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(1024);
    await expect(page.getByRole("button", { name: "Straight" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Quarter Circle" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Half Circle" })).toBeVisible();
    await expect(page.getByLabel("Variation review")).toBeVisible();
    await page.getByText("Upper-level wind", { exact: true }).click();
    await expect(page.getByLabel("6–12 km shear value")).toBeVisible();
    await expect(page.getByLabel("Direction relative to 0–6 km shear value")).toBeVisible();
    await expect(page.getByRole("img", { name: "Resolved hodograph" })).toBeVisible();
  });
});

async function gotoCreateVariation(page: Page) {
  await gotoApp(page);
  await page.getByRole("button", { name: "Enter Supercells" }).click();
  await page
    .getByRole("navigation", { name: "Supercells sections" })
    .getByRole("button", { name: "Create Variation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Design a related Supercells Simulation" }),
  ).toBeVisible();
}

async function mockSupercellsVariationPath(page: Page) {
  let completed = false;

  await page.unroute("**/api/worlds");
  await page.route("**/api/worlds", (route) =>
    json(route, [
      {
        world_id: "supercells",
        display_name: "Supercells",
        short_description: "Inspect and vary idealized rotating storms.",
        reference_simulation_id: reference.simulation_id,
        reference_available: true,
        simulation_count: completed ? 3 : 2,
        saved_view_count: 0,
        saved_comparison_count: 1,
        featured_comparison_count: 0,
        active_run_count: 0,
        completed_uninspected_run_count: 0,
        availability_state: "available",
        availability_message: "Available",
      },
    ]),
  );
  await page.route("**/api/worlds/supercells", (route) => json(route, worldPayload(completed)));
  await page.route("**/api/worlds/supercells/variation-template**", (route) => {
    const parentId = new URL(route.request().url()).searchParams.get("parent_simulation_id");
    const parent =
      parentId === straight.simulation_id
        ? straight
        : parentId === descendant.simulation_id
          ? descendant
          : reference;
    return json(route, variationTemplate(parent));
  });
  await page.route("**/api/worlds/supercells/variations/preview", async (route) => {
    const request = route.request().postDataJSON() as VariationRequest;
    return json(route, variationPreview(request));
  });
  await page.route("**/api/worlds/supercells/variations", (route) =>
    json(route, {
      simulation_id: descendant.simulation_id,
      run_id: descendant.run_id,
      manifest_path: "/mock/supercells-direct/run_manifest.json",
      package_dir: "/mock/supercells-direct",
      launch_review_snapshot_id: "mock-supercells-launch-review",
    }),
  );
  await page.unroute("**/api/runs/queue");
  await page.route("**/api/runs/queue", (route) => {
    if (route.request().method() === "POST") completed = true;
    return json(route, { entries: [], active_run_id: null, queued_count: 0 });
  });
  await page.unroute("**/api/lifecycle");
  await page.route("**/api/lifecycle", (route) =>
    json(route, {
      schema_version: "1",
      generated_at: "2026-07-29T14:00:00Z",
      records: completed ? [lifecycleRecord()] : [],
      warnings: [],
    }),
  );
}

function worldPayload(includeDescendant: boolean) {
  return {
    world_id: "supercells",
    display_name: "Supercells",
    short_description: "A deep rotating thunderstorm laboratory.",
    availability_state: "available",
    availability_message: "The retained Supercells Simulations are available.",
    reference_simulation: reference,
    simulations: [reference, straight, ...(includeDescendant ? [descendant] : [])],
    capabilities: {
      reference_explore: true,
      lab: false,
      compare: true,
      saved_views: false,
      saved_comparisons: true,
      create_variation: true,
    },
    caveats: ["Idealized experiments are not forecasts."],
  };
}

function simulation(
  simulationId: string,
  displayName: string,
  role: "reference" | "variation",
  runId: string,
) {
  return {
    simulation_id: simulationId,
    display_name: displayName,
    role,
    world_id: "supercells",
    run_id: runId,
    case_id: `${runId}-case`,
    parent_simulation_id: role === "reference" ? null : reference?.simulation_id,
    reference_simulation_id: "supercells_quarter_circle_reference",
    technical_state: "available",
    technical_state_message: "Exact retained output is available.",
    explore_available: true,
    saved_output_count: 91,
    model_start_seconds: 0,
    model_end_seconds: 10_800,
    history_cadence_seconds: 120,
    default_explore_time_index: 62,
    lineage_state: "known",
    recipe_contract_version: "1",
    relationship_classification: role === "reference" ? null : "controlled_physical_variation",
    run_profile_id: "supercells_presentation_v1",
    can_create_variation: true,
    parent_eligibility_reason: "Exact Recipe and retained-output evidence is reconstructible.",
  };
}

function variationTemplate(parent: ReturnType<typeof simulation>) {
  return {
    parent_simulation_id: parent.simulation_id,
    parent_run_id: parent.run_id,
    parent_display_name: parent.display_name,
    parent_configuration_source: "Accepted retained presentation evidence",
    reference_simulation_id: reference.simulation_id,
    recipe_id: "idealized_isolated_supercell",
    recipe_name: "Idealized Isolated Supercell",
    recipe_contract_version: "1",
    controls: {
      ...referenceControls,
      hodograph_family:
        parent.simulation_id === straight.simulation_id ? "straight" : "quarter_circle",
    },
    reference_controls: referenceControls,
    run_profiles: [
      runCost("supercells_quick_v1", "Quick", "Two-hour storm response", "passes"),
      runCost("supercells_standard_v1", "Standard", "Three-hour supercell experiment", "passes"),
      runCost("supercells_presentation_v1", "Presentation", "Detailed three-hour storm", "passes"),
      runCost("supercells_extended_v1", "Extended", "Four-hour longevity", "blocked"),
    ],
    default_run_profile_id: "supercells_presentation_v1",
    can_create_variation: true,
    unavailable_reason: null,
  };
}

type VariationRequest = {
  run_profile_id: string;
  controls: typeof referenceControls;
};

function variationPreview(request: VariationRequest) {
  const controls = request.controls;
  const differences = {
    wind: differenceList([
      difference(
        "controls.hodograph_family",
        "Hodograph family",
        referenceControls.hodograph_family,
        controls.hodograph_family,
        null,
      ),
      difference(
        "controls.shear_0_6_km_m_s",
        "0-6 km vector shear",
        referenceControls.shear_0_6_km_m_s,
        controls.shear_0_6_km_m_s,
        "m s^-1",
      ),
    ]),
    thermodynamics: differenceList([
      difference(
        "controls.surface_based_cape_j_kg",
        "Surface-based CAPE",
        referenceControls.surface_based_cape_j_kg,
        controls.surface_based_cape_j_kg,
        "J kg^-1",
      ),
      difference(
        "controls.lcl_height_m_agl",
        "LCL height",
        referenceControls.lcl_height_m_agl,
        controls.lcl_height_m_agl,
        "m AGL",
      ),
    ]),
    initiation: differenceList([
      difference(
        "controls.thermal_perturbation_amplitude_k",
        "Thermal perturbation",
        referenceControls.thermal_perturbation_amplitude_k,
        controls.thermal_perturbation_amplitude_k,
        "K",
      ),
      difference(
        "controls.thermal_horizontal_radius_km",
        "Thermal horizontal radius",
        referenceControls.thermal_horizontal_radius_km,
        controls.thermal_horizontal_radius_km,
        "km",
      ),
      difference(
        "controls.thermal_center_x_km",
        "Thermal center x",
        referenceControls.thermal_center_x_km,
        controls.thermal_center_x_km,
        "km",
      ),
    ]),
    numerical:
      request.run_profile_id === "supercells_presentation_v1"
        ? []
        : [
            {
              path: "numerical.run_profile_id",
              label: "Run profile",
              before: "supercells_presentation_v1",
              after: request.run_profile_id,
              units: null,
            },
          ],
    observation: [],
  };
  const physicalCount =
    differences.wind.length + differences.thermodynamics.length + differences.initiation.length;
  const initiationOnly =
    differences.initiation.length > 0 &&
    differences.wind.length === 0 &&
    differences.thermodynamics.length === 0;
  const numerical = differences.numerical.length > 0;
  const cost = runCost(
    request.run_profile_id,
    request.run_profile_id.includes("extended")
      ? "Extended"
      : request.run_profile_id.includes("standard")
        ? "Standard"
        : request.run_profile_id.includes("quick")
          ? "Quick"
          : "Presentation",
    "Selected Supercells profile",
    request.run_profile_id.includes("extended") ? "blocked" : "passes",
  );
  const blockingErrors = [];
  if (physicalCount === 0 && !numerical) {
    blockingErrors.push("Change at least one scientific control or run profile before packaging.");
  }
  if (controls.surface_based_cape_j_kg === 8_000 && controls.lcl_height_m_agl === 4_000) {
    blockingErrors.push(
      "The profile solver cannot jointly resolve 8,000 J/kg CAPE with a 4,000 m LCL inside this coherent profile family.",
    );
  }
  if (Math.abs(controls.thermal_center_x_km) + controls.thermal_horizontal_radius_km > 59) {
    blockingErrors.push(
      "The requested thermal does not fit inside the generated horizontal domain with the required 1 km grid clearance.",
    );
  }
  if (cost.disposition === "blocked") {
    blockingErrors.push(cost.disposition_reason);
  }
  const relationship =
    physicalCount === 0
      ? numerical
        ? "numerical_sensitivity"
        : null
      : numerical
        ? "mixed_variation"
        : initiationOnly
          ? "controlled_initiation_sensitivity"
          : physicalCount === 1
            ? "controlled_physical_variation"
            : "multi_factor_physical_variation";
  return {
    reference_controls: referenceControls,
    parent_controls: referenceControls,
    requested_controls: controls,
    achieved_controls: controls,
    differences,
    relationship_classification: relationship,
    warnings:
      controls.hodograph_family === "half_circle"
        ? ["Half Circle requires bounded runtime characterization before ordinary launch."]
        : [],
    blocking_errors: blockingErrors,
    diagnostics: {
      achieved_cape_j_kg: controls.surface_based_cape_j_kg,
      achieved_cin_j_kg: controls.cin_j_kg,
      achieved_lcl_height_m_agl: controls.lcl_height_m_agl,
      achieved_midlevel_rh_percent: controls.midlevel_rh_percent,
      freezing_level_m_agl: 4_200,
      hydrostatic_residual_pa: 0,
      shear_0_1_km_m_s: controls.shear_0_2_km_m_s / 2,
      shear_0_2_km_m_s: controls.shear_0_2_km_m_s,
      shear_0_3_km_m_s: 18,
      shear_0_6_km_m_s: controls.shear_0_6_km_m_s,
      shear_6_12_km_m_s: controls.shear_6_12_km_m_s,
      mean_wind_0_6_km_speed_m_s: controls.mean_wind_0_6_km_speed_m_s,
      mean_wind_0_6_km_direction_deg: controls.mean_wind_0_6_km_direction_deg,
      storm_relative_helicity_0_1_km_m2_s2: -40,
      storm_relative_helicity_0_3_km_m2_s2: -94,
      model_translation_u_m_s: 13.5,
      model_translation_v_m_s: 6.2,
      minimum_boundary_clearance_km: 50,
      minimum_vertical_clearance_km: 17.2,
      labels: [
        controls.hodograph_family.replaceAll("_", " "),
        "Deep instability",
        "Warm perturbation",
      ],
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
      amplitude_k: controls.thermal_perturbation_amplitude_k,
      horizontal_radius_m: controls.thermal_horizontal_radius_km * 1_000,
      vertical_radius_m: controls.thermal_vertical_radius_km * 1_000,
      center_height_m_agl: controls.thermal_center_height_km_agl * 1_000,
      center_x_m: controls.thermal_center_x_km * 1_000,
      center_y_m: controls.thermal_center_y_km * 1_000,
    },
    numerical_realization: cost.profile.numerical_realization,
    observation_plan: cost.profile.observation_plan,
    cost_estimate: cost,
  };
}

function difference(
  path: string,
  label: string,
  before: number | string,
  after: number | string,
  units: string | null,
) {
  if (before === after) return null;
  return { path, label, before, after, units };
}

function differenceList<T>(values: Array<T | null>): T[] {
  return values.filter((value): value is T => value !== null);
}

function runCost(
  profileId: string,
  role: string,
  profileName: string,
  disposition: "passes" | "blocked",
) {
  const extended = disposition === "blocked";
  const exactDomain = profileId.includes("quick")
    ? { nx: 120, ny: 120, nz: 40, dx_m: 1_000, dy_m: 1_000, dz_m: 500 }
    : profileId.includes("presentation")
      ? { nx: 240, ny: 240, nz: 60, dx_m: 500, dy_m: 500, dz_m: 333.333 }
      : { nx: 160, ny: 160, nz: 50, dx_m: 750, dy_m: 750, dz_m: 400 };
  return {
    profile: {
      profile_id: profileId,
      profile_name: `${role} — ${profileName}`,
      role,
      recipe_id: "idealized_isolated_supercell",
      numerical_realization: {
        domain: "120 km × 120 km × 20 km",
        grid: `${exactDomain.nx} × ${exactDomain.ny} × ${exactDomain.nz}`,
        spacing: `${exactDomain.dx_m} × ${exactDomain.dy_m} × ${Math.round(exactDomain.dz_m)} m`,
        timestep_strategy: "explicit approved timestep",
        physics_source: "CM1 r21.1",
        exact_domain: {
          ...exactDomain,
          x_min_m: -60_000,
          x_max_m: 60_000,
          y_min_m: -60_000,
          y_max_m: 60_000,
          model_top_m: 20_000,
          timestep_seconds: 3,
        },
      },
      observation_plan: {
        duration_seconds: extended ? 14_400 : 10_800,
        output_cadence_seconds: 180,
        expected_history_count: extended ? 81 : 61,
        retained_field_inventory: ["w", "zvort", "uh", "dbz", "rain"],
      },
      expected_runtime_min_seconds: 2_700,
      expected_runtime_max_seconds: 4_500,
      expected_size_min_bytes: 2_000_000_000,
      expected_size_max_bytes: 3_000_000_000,
      estimate_basis: extended ? "uncharacterized" : "scaled_from_measured",
      confidence: extended ? "Characterization required." : "Provisional.",
      scientific_limitations: ["Low-level detail depends on selected resolution."],
    },
    current_free_space_bytes: 100_000_000_000,
    projected_free_space_bytes: extended ? 1_000_000_000 : 97_000_000_000,
    required_free_space_bytes: 5_000_000_000,
    disposition,
    disposition_reason: extended
      ? "Projected free space would fall below the required 2.0 GB post-run reserve."
      : "The high retained-size estimate fits while preserving the required safety margin.",
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

function lifecycleRecord() {
  const attempt = (attemptId: string, state: "failed" | "completed", acceptedBacking: boolean) => ({
    attempt_id: attemptId,
    run_id: attemptId,
    relationship: acceptedBacking ? "later_backing_candidate" : "initial",
    accepted_backing: acceptedBacking,
    manifest_path: `/mock/${attemptId}/run_manifest.json`,
    lifecycle_state: state,
    queue_state: null,
    product_state: state === "completed" ? "completed_cm1_result" : "configured_experiment",
    validation_status: state === "completed" ? "valid" : "failed",
    result_id: state === "completed" ? "result-supercells-direct" : null,
    output_artifact_count: state === "completed" ? 61 : 0,
    size_bytes: state === "completed" ? 2_500_000_000 : 2_048,
    retained_state: "retained",
    created_at: "2026-07-29T14:00:00Z",
    started_at: "2026-07-29T14:01:00Z",
    finished_at: "2026-07-29T15:00:00Z",
    updated_at: "2026-07-29T15:00:00Z",
    message: state === "failed" ? "The first attempt failed before valid output." : null,
    failure_reason: state === "failed" ? "CM1 exited nonzero." : null,
  });
  return {
    record_id: `simulation:supercells:${descendant.simulation_id}`,
    record_kind: "simulation",
    owner_id: "supercells",
    owner_label: "Supercells",
    simulation_id: descendant.simulation_id,
    experiment_id: null,
    world_id: "supercells",
    recipe_id: "idealized_isolated_supercell",
    recipe_version: "1",
    parent_simulation_id: reference.simulation_id,
    reference_simulation_id: reference.simulation_id,
    display_name: descendant.display_name,
    question: "How does stronger deep-layer shear change storm organization?",
    role: "variation",
    case_id: descendant.case_id,
    differences: [
      {
        category: "wind",
        label: "0-6 km vector shear",
        before: 31.8,
        after: 45,
        units: "m/s",
        material: true,
      },
    ],
    attempts: [
      attempt("supercells-direct-failed", "failed", false),
      attempt(descendant.run_id, "completed", true),
    ],
    facts: {
      scientific_work: "present",
      package: "present",
      attempt: "present",
      queue: "not_applicable",
      process: "passed",
      expected_output: "present",
      technical_integrity: "passed",
      ingest: "present",
      world_inspectability: "passed",
      simulation_availability: "present",
      parent_eligibility: "eligible",
      retained_assets: "present",
    },
    trust_state: "trusted",
    caveats: [],
    tags: [],
    notes: null,
    lifecycle_label: "Available",
    lifecycle_detail: "The later successful attempt is inspectable in Supercells.",
    activity_group: "recently_completed",
    in_activity: true,
    created_at: "2026-07-29T14:00:00Z",
    updated_at: "2026-07-29T15:00:00Z",
    size_bytes: 2_500_000_000,
    dependencies: [],
    actions: [
      {
        kind: "explore",
        label: "Explore",
        world_id: "supercells",
        simulation_id: descendant.simulation_id,
        run_id: descendant.run_id,
      },
      {
        kind: "compare",
        label: "Compare",
        world_id: "supercells",
        simulation_id: descendant.simulation_id,
        run_id: descendant.run_id,
      },
    ],
  };
}

function json(route: Route, payload: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });
}

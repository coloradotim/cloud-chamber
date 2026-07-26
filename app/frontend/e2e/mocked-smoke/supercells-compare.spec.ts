import { expect, test, type Page } from "@playwright/test";

import { mockCloudChamberApis } from "../fixtures";
import { gotoApp } from "../helpers";

const REFERENCE_ID = "supercells_quarter_circle_reference";
const VARIATION_ID = "supercells_straight_line_hodograph";
const TIMES = Array.from({ length: 91 }, (_, index) => index * 120);
const W_SCALE = {
  scale_id: "supercell_midlevel_vertical_velocity_v1",
  display_name: "Vertical velocity",
  units: "m/s",
  scale_type: "fixed_discrete",
  minimum: -30,
  maximum: 30,
  breakpoints: [-20, -10, -2, 2, 10, 20],
  colors: ["#4b0082", "#0057d9", "#00c9d8", "#ffffff", "#00d63b", "#ff9800", "#c40000"],
  fixed_across_time: true,
};
const CONDENSATE_SCALE = {
  scale_id: "supercell_total_condensate_v2",
  display_name: "Total condensate",
  units: "g/kg",
  scale_type: "fixed_continuous",
  minimum: 0,
  maximum: 15,
  breakpoints: [],
  colors: ["#ffffff", "#8bd8e7", "#3575b8"],
  fixed_across_time: true,
};
const HYDROMETEORS = [
  { code: 0, key: "clear", label: "Clear", color: "#ffffff" },
  { code: 1, key: "cloud_liquid", label: "Cloud liquid", color: "#72d7df" },
  { code: 2, key: "rain", label: "Rain", color: "#1987bd" },
  { code: 3, key: "cloud_ice", label: "Cloud ice", color: "#c5b8ec" },
  { code: 4, key: "snow", label: "Snow", color: "#8586c6" },
  { code: 5, key: "hail_treated_large_ice", label: "Hail-treated large ice", color: "#e49a4c" },
];
type FrameCategories = null | {
  key: string;
  display_name: string;
  evidence_kind: string;
  source_fields: string[];
  derivation: string;
  values: number[][];
  magnitude: ReturnType<typeof field>;
  categories: typeof HYDROMETEORS;
};

test.describe("mocked smoke: real Supercells Compare adapter", () => {
  test("coordinates all three Lenses and physical sections at both desktop review sizes", async ({
    page,
  }) => {
    test.setTimeout(60_000);
    const browserErrors: string[] = [];
    page.on("pageerror", (error) => {
      browserErrors.push(error.message);
      console.error(error.message);
    });
    page.on("console", (message) => {
      if (message.type() !== "error") return;
      browserErrors.push(message.text());
      console.error(message.text());
    });
    await page.setViewportSize({ width: 1728, height: 1117 });
    await mockCloudChamberApis(page);
    await mockSupercellsPair(page);
    await gotoApp(page);

    await page.getByRole("button", { name: "Enter Supercells" }).click();
    const variation = page
      .locator("article")
      .filter({ hasText: "Straight-Line Hodograph Supercell" });
    await variation.getByRole("button", { name: "Compare" }).click();
    await expect(
      page.getByRole("heading", { name: "Review the two Simulations before loading frames" }),
    ).toBeVisible();
    await expect(page.getByRole("cell", { name: "Hodograph geometry" })).toBeVisible();
    await page.getByRole("button", { name: "Open dual view" }).click();

    await expect(page.getByLabel("Supercells Compare")).toBeVisible();
    await page.getByRole("button", { name: "Aligned" }).click();
    await expect(page.getByLabel("Vertical velocity legend")).toHaveCount(2);
    await expect(page.getByLabel("Quarter-Circle Supercell saved output time")).toBeVisible();
    await page.screenshot({
      path: "test-results/supercells-compare-preview-1728x1117.png",
      fullPage: true,
    });

    const left = page.getByLabel("Quarter-Circle Supercell comparison side");
    await left.getByRole("button", { name: "Cloud and Precipitation" }).click();
    await expect(page.getByLabel("Hydrometeor legend")).toHaveCount(2);
    await left.getByRole("button", { name: "Low-Level Interactions" }).click();
    await expect(page.getByLabel("Vertical velocity legend")).toHaveCount(2);
    await left.getByRole("button", { name: "Vertical x-z" }).click();
    await expect(page.getByLabel("xz native section")).toHaveCount(2);

    await page.setViewportSize({ width: 1024, height: 856 });
    await expect(page.getByLabel("Supercells Compare")).toBeVisible();
    await page.screenshot({
      path: "test-results/supercells-compare-preview-1024x856.png",
      fullPage: true,
    });
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(1);
    expect(browserErrors).toEqual([]);
  });
});

async function mockSupercellsPair(page: Page) {
  await page.unroute("**/api/worlds");
  await page.route("**/api/worlds", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          world_id: "supercells",
          display_name: "Supercells",
          status: "available",
          short_description:
            "A deep rotating thunderstorm for seeing organized ascent and precipitation.",
          reference_simulation_id: REFERENCE_ID,
          reference_available: true,
          simulation_count: 2,
          saved_view_count: 0,
          saved_comparison_count: 0,
          featured_comparison_count: 0,
          active_run_count: 0,
          completed_uninspected_run_count: 0,
          availability_state: "available",
          availability_message: "Two retained Simulations are available.",
        },
      ]),
    }),
  );
  await page.route("**/api/worlds/supercells", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(worldPayload()),
    }),
  );
  await page.route("**/api/worlds/supercells/compare**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(compareDescriptor()),
    }),
  );
  await page.route("**/api/worlds/supercells/simulations/*/frame**", (route) => {
    const url = new URL(route.request().url());
    const simulationId = url.pathname.includes(VARIATION_ID) ? VARIATION_ID : REFERENCE_ID;
    const lens = url.searchParams.get("lens") ?? "rotating_updraft";
    const timeIndex = Number(url.searchParams.get("time_index") ?? 37);
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(framePayload(simulationId, lens, timeIndex)),
    });
  });
}

function worldPayload() {
  const reference = worldSimulation(REFERENCE_ID, "Quarter-Circle Supercell", "reference");
  const variation = worldSimulation(VARIATION_ID, "Straight-Line Hodograph Supercell", "variation");
  return {
    world_id: "supercells",
    display_name: "Supercells",
    short_description:
      "A deep rotating thunderstorm for seeing organized ascent, rotation, hydrometeors, precipitation, and low-level flow evolve together.",
    availability_state: "available",
    availability_message: "Two retained Simulations are available for Explore and Compare.",
    reference_simulation: reference,
    simulations: [reference, variation],
    capabilities: {
      reference_explore: true,
      lab: false,
      compare: true,
      saved_views: false,
    },
    caveats: [
      "Coordinates and local evidence are comparable; storm-object lineage is not inferred.",
    ],
  };
}

function worldSimulation(
  simulationId: string,
  displayName: string,
  role: "reference" | "variation",
) {
  const reference = role === "reference";
  return {
    simulation_id: simulationId,
    display_name: displayName,
    role,
    world_id: "supercells",
    run_id: reference
      ? "quarter-circle-supercell-presentation-v1-20260723"
      : "straight-line-supercell-presentation-v1-20260726",
    case_id: reference
      ? "cm1_r21_1_quarter_circle_supercell_presentation_v1"
      : "cm1_r21_1_straight_line_supercell_presentation_v1",
    parent_simulation_id: reference ? null : REFERENCE_ID,
    reference_simulation_id: REFERENCE_ID,
    technical_state: "available",
    technical_state_message: "Ninety-one retained histories are available.",
    explore_available: true,
    saved_output_count: 91,
    model_start_seconds: 0,
    model_end_seconds: 10_800,
    history_cadence_seconds: 120,
    default_explore_time_index: 37,
    lineage_state: "known",
  };
}

function compareDescriptor() {
  const reference = compareSimulation(REFERENCE_ID, "Quarter-Circle Supercell", "reference");
  const variation = compareSimulation(
    VARIATION_ID,
    "Straight-Line Hodograph Supercell",
    "variation",
  );
  return {
    schema_version: "world_compare_v1",
    world_id: "supercells",
    display_name: "Supercells",
    simulations: [reference, variation],
    default_left_simulation_id: REFERENCE_ID,
    default_right_simulation_id: VARIATION_ID,
    selected_left_simulation_id: REFERENCE_ID,
    selected_right_simulation_id: VARIATION_ID,
    material_differences: [
      {
        path: "atmosphere.hodograph",
        label: "Hodograph geometry",
        category: "atmospheric",
        left_value: "quarter circle",
        right_value: "straight line",
        left_known: true,
        right_known: true,
        units: null,
        material: true,
      },
    ],
    compatibility: {
      same_world: true,
      both_inspectable: true,
      relationship:
        "Straight-Line Hodograph Supercell is a controlled variation of Quarter-Circle Supercell.",
      controlled_pair: true,
      controlled_pair_message:
        "Hodograph geometry changed; thermodynamics and the numerical experiment are matched.",
      shared_field_ids: ["winterp", "total_condensate"],
      shared_view_ids: ["rotating_updraft", "cloud_precipitation", "low_level_interactions"],
      shared_fixed_scale_ids: [
        "supercell_midlevel_vertical_velocity_v1",
        "supercell_total_condensate_v2",
        "supercell_low_level_vertical_velocity_v1",
      ],
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

function compareSimulation(
  simulationId: string,
  displayName: string,
  role: "reference" | "variation",
) {
  const record = worldSimulation(simulationId, displayName, role);
  return {
    simulation_id: simulationId,
    display_name: displayName,
    world_id: "supercells",
    role,
    run_id: record.run_id,
    result_id: null,
    case_id: record.case_id,
    parent_simulation_id: record.parent_simulation_id,
    reference_simulation_id: REFERENCE_ID,
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
      times_seconds: TIMES,
      start_seconds: 0,
      end_seconds: 10_800,
      cadence_seconds: 120,
      saved_output_count: 91,
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
    initial_state: {
      state_version: 1,
      world_id: "supercells",
      model_time_seconds: 4_440,
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
      camera_preset: "overview",
      camera_transform: null,
      scene_opacity: 1,
      scene_point_size: 1,
      selected_evidence_visible: false,
      context_collapsed: true,
      secondary_section: "notes",
      selected_point: null,
      playback_speed: 1,
      display_controls_open: false,
    },
    caveats: ["Storm-object lineage is not inferred between the two Simulations."],
  };
}

function framePayload(simulationId: string, lens: string, timeIndex: number) {
  const variation = simulationId === VARIATION_ID;
  const cloudLens = lens === "cloud_precipitation";
  const lowLevelLens = lens === "low_level_interactions";
  const x = coordinates(32, -38, 22);
  const y = coordinates(32, -28, 32);
  const z = coordinates(24, 0.1667, 19.8333);
  const planValues = matrix(y.length, x.length, (row, column) =>
    stormValue(x[column], y[row], variation, lowLevelLens),
  );
  const sectionValues = matrix(z.length, x.length, (row, column) =>
    sectionValue(x[column], z[row], variation),
  );
  const primary = field(
    cloudLens ? "total_condensate" : "winterp",
    cloudLens ? "Total condensate" : "Vertical velocity",
    cloudLens ? "g/kg" : "m/s",
    cloudLens ? planValues.map((row) => row.map((value) => Math.max(0, value / 2))) : planValues,
    cloudLens ? CONDENSATE_SCALE : W_SCALE,
  );
  const sectionPrimary = field(
    cloudLens ? "total_condensate" : "winterp",
    cloudLens ? "Total condensate" : "Vertical velocity",
    cloudLens ? "g/kg" : "m/s",
    cloudLens
      ? sectionValues.map((row) => row.map((value) => Math.max(0, value / 2)))
      : sectionValues,
    cloudLens ? CONDENSATE_SCALE : W_SCALE,
  );
  const planOverlays = {
    total_condensate: overlayField(
      "total_condensate",
      "Total condensate",
      "g/kg",
      planValues.map((row) => row.map((value) => Math.max(0, value / 4))),
      CONDENSATE_SCALE,
    ),
    vertical_vorticity: overlayField(
      "vertical_vorticity",
      "Vertical vorticity",
      "s^-1",
      planValues.map((row) => row.map((value) => Math.max(0, value / 900))),
      W_SCALE,
    ),
    updraft_helicity: overlayField(
      "updraft_helicity",
      "Updraft helicity",
      "m^2/s^2",
      planValues.map((row) => row.map((value) => Math.max(0, value * 24))),
      W_SCALE,
    ),
    composite_reflectivity: overlayField(
      "composite_reflectivity",
      "Composite reflectivity",
      "dBZ",
      planValues.map((row) => row.map((value) => Math.max(0, value * 3))),
      W_SCALE,
    ),
    vertical_velocity: overlayField(
      "vertical_velocity",
      "Vertical velocity",
      "m/s",
      planValues,
      W_SCALE,
    ),
    accumulated_surface_rain: overlayField(
      "accumulated_surface_rain",
      "Accumulated surface rain",
      "mm",
      planValues.map((row) => row.map((value) => Math.max(0, value / 2))),
      CONDENSATE_SCALE,
    ),
    low_level_precipitating_condensate: overlayField(
      "low_level_precipitating_condensate",
      "Low-level precipitating condensate",
      "g/kg",
      planValues.map((row) => row.map((value) => Math.max(0, value / 8))),
      CONDENSATE_SCALE,
    ),
  };
  const sectionOverlays = {
    vertical_velocity: overlayField(
      "vertical_velocity",
      "Vertical velocity",
      "m/s",
      sectionValues,
      W_SCALE,
    ),
    vertical_vorticity: overlayField(
      "vertical_vorticity",
      "Vertical vorticity",
      "s^-1",
      sectionValues.map((row) => row.map((value) => Math.max(0, value / 900))),
      W_SCALE,
    ),
    total_condensate: overlayField(
      "total_condensate",
      "Total condensate",
      "g/kg",
      sectionValues.map((row) => row.map((value) => Math.max(0, value / 4))),
      CONDENSATE_SCALE,
    ),
    precipitating_condensate: overlayField(
      "precipitating_condensate",
      "Precipitating condensate",
      "g/kg",
      sectionValues.map((row) => row.map((value) => Math.max(0, value / 8))),
      CONDENSATE_SCALE,
    ),
    reflectivity: overlayField(
      "reflectivity",
      "Reflectivity",
      "dBZ",
      sectionValues.map((row) => row.map((value) => Math.max(0, value * 3))),
      W_SCALE,
    ),
  };
  const categories = cloudLens
    ? {
        key: "dominant_hydrometeor",
        display_name: "Dominant hydrometeor",
        evidence_kind: "derived",
        source_fields: ["qc", "qr", "qi", "qs", "qg"],
        derivation: "largest native condensate mixing ratio",
        values: primary.values.map((row) =>
          row.map((value) => (value > 7 ? 5 : value > 4 ? 4 : value > 2 ? 2 : value > 0.2 ? 1 : 0)),
        ),
        magnitude: primary,
        categories: HYDROMETEORS,
      }
    : null;
  const selected = {
    x_index: 120,
    y_index: 120,
    z_index: lowLevelLens ? 3 : 10,
    x_km: 0.25,
    y_km: 0.25,
    z_km: lowLevelLens ? 1.1667 : 3.5,
    model_time_seconds: TIMES[timeIndex],
    coordinate_frame: "translating model frame",
    values: {
      vertical_velocity: variation ? 9.4 : 14.8,
      vertical_vorticity: variation ? 0.008 : 0.024,
      updraft_helicity: variation ? 190 : 430,
      total_condensate: cloudLens ? 8.2 : 3.7,
      reflectivity: 51,
      accumulated_rain: lowLevelLens ? 13.2 : 4.1,
    },
    units: {
      vertical_velocity: "m/s",
      vertical_vorticity: "s^-1",
      updraft_helicity: "m^2/s^2",
      total_condensate: "g/kg",
      reflectivity: "dBZ",
      accumulated_rain: "mm",
    },
    evidence_kind: {},
    states: variation ? ["Rising", "Condensate present"] : ["Rising", "Rotating"],
    distance_to_primary_updraft_km: 0,
  };
  return {
    schema_version: "supercells_explore_v1",
    authority_state: "supercells_product_world",
    world_id: "supercells",
    simulation_id: simulationId,
    run_id:
      simulationId === REFERENCE_ID
        ? "quarter-circle-supercell-presentation-v1-20260723"
        : "straight-line-supercell-presentation-v1-20260726",
    case_id:
      simulationId === REFERENCE_ID
        ? "cm1_r21_1_quarter_circle_supercell_presentation_v1"
        : "cm1_r21_1_straight_line_supercell_presentation_v1",
    simulation_label:
      simulationId === REFERENCE_ID
        ? "Quarter-Circle Supercell"
        : "Straight-Line Hodograph Supercell",
    lens_id: lens,
    lens_name: cloudLens
      ? "Cloud and Precipitation"
      : lowLevelLens
        ? "Low-Level Interactions"
        : "Rotating Updraft",
    lens_question: cloudLens
      ? "How are cloud and precipitation organized?"
      : lowLevelLens
        ? "How do near-surface ascent, descent, and rain interact?"
        : "Where is the storm rising and rotating as one organized structure?",
    what_to_notice_now: "Compare coordinates and local evidence without assigning feature lineage.",
    time_index: timeIndex,
    time_seconds: TIMES[timeIndex],
    times_seconds: TIMES,
    mature_checkpoint_indices: [25, 37, 50, 75, 90],
    timeline_checkpoints: [],
    viewport: "storm",
    viewport_bounds_km: { x_min: -38, x_max: 22, y_min: -28, y_max: 32 },
    primary_updraft: {
      x_index: selected.x_index,
      y_index: selected.y_index,
      z_index: selected.z_index,
      x_km: selected.x_km,
      y_km: selected.y_km,
      z_km: selected.z_km,
      w_m_s: selected.values.vertical_velocity,
    },
    selected_point: selected,
    plan: {
      title: cloudLens
        ? "Cloud and precipitation structure"
        : lowLevelLens
          ? "Low-level motion and rain footprint"
          : "Midlevel updraft and rotation",
      subtitle: "Native-grid evidence in the translating model frame",
      x_indices: x.map((_, index) => index * 7),
      y_indices: y.map((_, index) => index * 7),
      x_km: x,
      y_km: y,
      level_index: selected.z_index,
      level_km: selected.z_km,
      selection_z_indices: cloudLens ? matrix(y.length, x.length, () => 10) : null,
      primary,
      overlays: planOverlays,
      categories,
      wind_vectors: [],
    },
    xz_section: section("xz", x, z, sectionPrimary, sectionOverlays, categories, selected.y_km),
    yz_section: section("yz", y, z, sectionPrimary, sectionOverlays, categories, selected.x_km),
    scene: {
      coordinate_extents_km: {
        x: { min: -38, max: 22 },
        y: { min: -28, max: 32 },
        z: { min: 0.1667, max: 19.8333 },
      },
      coordinate_sizes: { x: 120, y: 120, z: 60 },
      coordinate_indices: {
        x: x.map((_, index) => index),
        y: y.map((_, index) => index),
        z: z.map((_, index) => index),
      },
      coordinate_values_km: { x, y, z },
      layers: [
        {
          key: "storm_cloud_body",
          display_name: "Storm cloud body",
          units: "g/kg",
          evidence_kind: "derived",
          source_fields: ["qc", "qr", "qi", "qs", "qg"],
          derivation: "total condensate",
          rendering: "neutral_cloud",
          points: scenePoints(variation),
          source_count: 256,
          returned_count: 256,
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
      source_history_file: `cm1out_${String(timeIndex + 1).padStart(6, "0")}.nc`,
    },
    caveats: ["Storm-object lineage is not inferred between Simulations."],
    provenance: { source: "mocked native-grid acceptance fixture" },
    extraction_milliseconds: variation ? 16 : 14,
  };
}

function section(
  orientation: "xz" | "yz",
  horizontal: number[],
  z: number[],
  primary: ReturnType<typeof field>,
  overlays: Record<string, ReturnType<typeof field>>,
  categories: FrameCategories,
  coordinate: number,
) {
  return {
    orientation,
    title: `${orientation} native section`,
    horizontal_dimension: orientation === "xz" ? "x" : "y",
    horizontal_indices: horizontal.map((_, index) => index * 7),
    horizontal_km: horizontal,
    z_km: z,
    cross_section_coordinate_km: coordinate,
    primary,
    overlays,
    categories,
  };
}

function field(
  key: string,
  displayName: string,
  units: string,
  values: number[][],
  scale: typeof W_SCALE | typeof CONDENSATE_SCALE,
) {
  const flattened = values.flat();
  return {
    key,
    display_name: displayName,
    units,
    evidence_kind: "native",
    source_fields: [key],
    derivation: null,
    values,
    selected_frame_minimum: Math.min(...flattened),
    selected_frame_maximum: Math.max(...flattened),
    scale,
  };
}

function overlayField(
  key: string,
  displayName: string,
  units: string,
  values: number[][],
  scale: typeof W_SCALE | typeof CONDENSATE_SCALE,
) {
  return {
    ...field(key, displayName, units, values, scale),
    evidence_kind: "derived",
    derivation: "mocked deterministic overlay",
  };
}

function matrix(rows: number, columns: number, value: (row: number, column: number) => number) {
  return Array.from({ length: rows }, (_, row) =>
    Array.from({ length: columns }, (_, column) => value(row, column)),
  );
}

function coordinates(count: number, minimum: number, maximum: number) {
  return Array.from(
    { length: count },
    (_, index) => minimum + (index / Math.max(1, count - 1)) * (maximum - minimum),
  );
}

function stormValue(x: number, y: number, variation: boolean, lowLevel: boolean) {
  const centerX = variation ? -5 : -11;
  const centerY = variation ? 4 : 8;
  const updraft = 24 * gaussian(x, y, centerX, centerY, 7, 9);
  const descent = -13 * gaussian(x, y, centerX + 9, centerY - 4, 9, 11);
  const secondary = variation ? 10 * gaussian(x, y, 7, -7, 7, 8) : 0;
  return (lowLevel ? 0.55 : 1) * (updraft + descent + secondary);
}

function sectionValue(horizontal: number, z: number, variation: boolean) {
  const center = variation ? -5 : -11;
  const primary = 25 * gaussian(horizontal, z, center, 6.5, 7, 4);
  const descent = -12 * gaussian(horizontal, z, center + 10, 5.5, 8, 5);
  return primary + descent;
}

function gaussian(
  x: number,
  y: number,
  centerX: number,
  centerY: number,
  spreadX: number,
  spreadY: number,
) {
  return Math.exp(
    -(
      ((x - centerX) * (x - centerX)) / (2 * spreadX * spreadX) +
      ((y - centerY) * (y - centerY)) / (2 * spreadY * spreadY)
    ),
  );
}

function scenePoints(variation: boolean): Array<[number, number, number, number, number]> {
  return Array.from({ length: 256 }, (_, index) => {
    const angle = (index / 32) * Math.PI * 2;
    const ring = 3 + (index % 8);
    return [
      (variation ? -5 : -11) + Math.cos(angle) * ring,
      (variation ? 4 : 8) + Math.sin(angle) * ring,
      1 + (index % 18) * 0.65,
      0.2 + (index % 12) * 0.15,
      0,
    ];
  });
}

async function horizontalOverflow(page: Page) {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

import { expect, test, type Page, type Route } from "@playwright/test";

import { collectConsoleProblems, gotoApp } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

const simulation = {
  simulation_id: "supercells_quarter_circle_reference",
  display_name: "Quarter-Circle Supercell",
  role: "reference",
  world_id: "supercells",
  run_id: "quarter-circle-supercell-official-20260722T142521Z",
  case_id: "cm1_r21_1_quarter_circle_supercell_official_v0",
  technical_state: "available",
  technical_state_message: "Nine retained histories are available.",
  explore_available: true,
  saved_output_count: 9,
  model_start_seconds: 0,
  model_end_seconds: 7_200,
  history_cadence_seconds: 900,
  lineage_state: "known",
};

const wScale = {
  scale_id: "supercells_vertical_velocity_v1",
  display_name: "Vertical velocity",
  units: "m/s",
  scale_type: "fixed_discrete",
  minimum: -30,
  maximum: 30,
  breakpoints: [-24, -18, -12, -6, 6, 12, 18, 24, 27],
  colors: [
    "#4b0082",
    "#0057d9",
    "#00c9d8",
    "#ffffff",
    "#00d63b",
    "#8fe000",
    "#ffe000",
    "#ff9800",
    "#ff3b00",
    "#c40000",
  ],
  fixed_across_time: true,
};

test.describe("mocked smoke: Supercells product path", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1728, height: 1000 });
    await mockCloudChamberApis(page);
    await mockSupercellsProductPath(page);
  });

  test("coordinates all three Lenses, evidence, Context, timeline, and maximize state", async ({
    page,
  }) => {
    const consoleProblems = collectConsoleProblems(page);
    await gotoSupercellsExplore(page);

    await expect(page.getByRole("button", { name: "Rotating Updraft" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel("True 3-D scalar field viewer")).toBeVisible();
    await expect(page.getByLabel("Midlevel storm structure plan view")).toBeVisible();
    await expect(page.getByText("frame 6 of 9 · Organized mature storm")).toBeVisible();
    const sceneBox = await page.getByLabel("3-D storm scene").boundingBox();
    const evidenceBox = await page.getByLabel("Coordinated storm evidence").boundingBox();
    const contextBox = await page.getByLabel("Explore inspector").boundingBox();
    expect(sceneBox?.width ?? 0).toBeLessThan((evidenceBox?.width ?? 1) * 1.7);
    expect(evidenceBox?.width ?? 0).toBeGreaterThan(500);
    expect(contextBox?.width ?? 0).toBeGreaterThanOrEqual(288);
    const planBox = await page.getByLabel("Midlevel storm structure plan view").boundingBox();
    expect((planBox?.width ?? 0) / (planBox?.height ?? 1)).toBeCloseTo(1, 1);

    await expect(page.getByLabel("Camera view")).toHaveValue("look_along_y");
    await page.getByLabel("Camera view").selectOption("top_down_xy");
    await page.getByRole("button", { name: "Cloud and Precipitation" }).click();
    await expect(page.getByRole("button", { name: "Cloud and Precipitation" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page
        .getByLabel("Slice orientation")
        .getByRole("button", { name: "Vertical x-z" }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByLabel("Camera view")).toHaveValue("look_along_y");
    await page.locator(".true3d-display-control > summary").click();
    await expect(page.getByLabel("Dominant hydrometeor")).toBeChecked();
    await expect(page.getByText("Hail-treated large ice").first()).toBeVisible();

    await page.getByRole("button", { name: "Low-Level Interactions" }).click();
    await expect(page.getByRole("button", { name: "Low-Level Interactions" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel("Flow arrows at 1.25 km")).toBeChecked();
    await expect(page.getByLabel("Accumulated rain (history)").first()).toBeChecked();
    await expect(page.getByLabel("Current precipitation")).toBeChecked();

    await page.getByRole("button", { name: "Rotating Updraft" }).click();
    await expect(page.getByLabel("Camera view")).toHaveValue("top_down_xy");
    await page.getByRole("button", { name: "Low-Level Interactions" }).click();

    await page
      .getByLabel("Slice orientation")
      .getByRole("button", { name: "Vertical x-z" })
      .click();
    await expect(page.getByLabel("Accumulated rain (history)")).toHaveCount(0);
    await expect(page.getByLabel("Flow arrows at 1.25 km")).toHaveCount(0);
    await expect(page.getByLabel("Current precipitation")).toBeChecked();
    await expect(page.getByText("Slice: xz section at y = 10.0 km")).toBeVisible();
    await expect(page.getByLabel("xz section at y = 10.0 km")).toBeVisible();
    const sectionBox = await page.getByLabel("xz section at y = 10.0 km").boundingBox();
    const sectionAspect = await page.locator(".storm-section-plot").evaluate((element) =>
      Number(getComputedStyle(element).getPropertyValue("--storm-data-aspect")),
    );
    expect((sectionBox?.width ?? 0) / (sectionBox?.height ?? 1)).toBeCloseTo(sectionAspect, 1);

    await page.getByLabel("xz section at y = 10.0 km").click({ position: { x: 180, y: 120 } });
    await page.getByRole("tab", { name: "Science" }).click();
    await expect(page.getByText("Selected point")).toBeVisible();

    await page.getByRole("button", { name: "Next saved output" }).click();
    await expect(page.getByText("90 min · 5,400 s")).toBeVisible();
    await page.getByLabel("Playback speed").selectOption("2");
    await expect(page.getByLabel("Playback speed")).toHaveValue("2");

    const evidenceBefore = await page.getByLabel("Coordinated storm evidence").boundingBox();
    await page.getByRole("button", { name: "Maximize evidence" }).click();
    const evidenceMaximized = await page.getByLabel("Coordinated storm evidence").boundingBox();
    expect(evidenceMaximized?.width ?? 0).toBeGreaterThan((evidenceBefore?.width ?? 0) * 2);
    await expect(page.getByRole("button", { name: "Open Context" })).toBeVisible();
    await expect(page.getByLabel("Explore inspector")).toHaveCount(0);
    const maximizedSectionBox = await page.getByLabel("xz section at y = 10.0 km").boundingBox();
    expect(
      (maximizedSectionBox?.width ?? 0) / (maximizedSectionBox?.height ?? 1),
    ).toBeCloseTo(sectionAspect, 1);
    await page.getByRole("button", { name: "Open Context" }).click();
    await expect(page.getByLabel("Explore inspector")).toBeVisible();
    await page.getByRole("button", { name: "Restore evidence" }).click();

    await page.getByRole("button", { name: "Collapse Context" }).click();
    await expect(page.getByLabel("Explore inspector")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Open Context" })).toBeVisible();
    await page.getByRole("button", { name: "Open Context" }).click();

    await page.getByRole("button", { name: "Maximize 3-D viewer" }).click();
    await expect(page.getByRole("button", { name: "Restore 3-D viewer" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Low-Level Interactions" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await page.getByRole("button", { name: "Restore 3-D viewer" }).click();

    expect(consoleProblems).toEqual([]);
  });

  test("keeps the coordinated 2-D evidence usable when WebGL is unavailable", async ({ page }) => {
    await page.addInitScript(() => {
      const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (contextId, options) {
        if (String(contextId).includes("webgl")) return null;
        return original.call(this, contextId, options as CanvasRenderingContext2DSettings);
      } as typeof HTMLCanvasElement.prototype.getContext;
    });

    await gotoSupercellsExplore(page);
    await expect(page.getByText(/Three\.js renderer unavailable/)).toBeVisible();
    await expect(page.getByLabel("Midlevel storm structure plan view")).toBeVisible();
    await expect(page.getByRole("tab", { name: "Explain" })).toBeVisible();
    await expect(page.getByLabel("Saved output time")).toBeEnabled();
  });

  test("keeps both scientific viewers useful in a 1024px desktop half-window", async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 856 });
    await gotoSupercellsExplore(page);

    const sceneFrame = await page.locator(".supercells-scene .true3d-scene-frame").boundingBox();
    const evidence = await page.getByLabel("Coordinated storm evidence").boundingBox();
    const documentWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const documentHeight = await page.evaluate(() => document.documentElement.scrollHeight);

    expect(sceneFrame?.height ?? 0).toBeGreaterThanOrEqual(398);
    expect(evidence?.height ?? 0).toBeGreaterThanOrEqual(398);
    expect(documentWidth).toBe(1024);
    expect(documentHeight).toBeLessThanOrEqual(856);
    await expect(page.getByRole("heading", { name: "Horizontal x-y slice" })).toBeVisible();
    const compactPlan = await page.getByLabel("Midlevel storm structure plan view").boundingBox();
    expect((compactPlan?.width ?? 0) / (compactPlan?.height ?? 1)).toBeCloseTo(1, 1);
    await expect(page.getByRole("button", { name: "Maximize evidence" })).toBeInViewport();
    await expect(page.getByRole("button", { name: "Previous saved output" })).toBeInViewport();
    await expect(page.getByRole("button", { name: "Next saved output" })).toBeInViewport();
    await expect(page.getByRole("button", { name: "Play" })).toBeInViewport();
  });
});

async function gotoSupercellsExplore(page: Page) {
  await gotoApp(page);
  await page.getByRole("button", { name: "Enter Supercells" }).click();
  await expect(page.getByRole("heading", { name: "Supercells" })).toBeVisible();
  await page.getByRole("button", { name: "Explore" }).click();
  await expect(page.getByRole("heading", { name: "Quarter-Circle Supercell" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Rotating Updraft" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
}

async function mockSupercellsProductPath(page: Page) {
  await page.unroute("**/api/worlds");
  await page.route("**/api/worlds", (route) =>
    json(route, [
      {
        world_id: "supercells",
        display_name: "Supercells",
        short_description: "Inspect a retained idealized rotating storm.",
        reference_simulation_id: simulation.simulation_id,
        reference_available: true,
        simulation_count: 1,
        saved_view_count: 0,
        saved_comparison_count: 0,
        featured_comparison_count: 0,
        active_run_count: 0,
        completed_uninspected_run_count: 0,
        availability_state: "available",
        availability_message: "Available",
      },
    ]),
  );
  await page.route("**/api/worlds/supercells", (route) =>
    json(route, {
      world_id: "supercells",
      display_name: "Supercells",
      short_description: "Inspect a retained idealized rotating storm.",
      availability_state: "available",
      availability_message: "The Quarter-Circle Supercell is available.",
      reference_simulation: simulation,
      simulations: [simulation],
      capabilities: {
        reference_explore: true,
        lab: false,
        compare: false,
        saved_views: false,
      },
      caveats: ["This idealized benchmark is not a forecast."],
    }),
  );
  await page.route("**/api/worlds/supercells/simulations/*/frame**", (route) =>
    json(route, supercellsFrame(route.request().url())),
  );
}

function supercellsFrame(url: string) {
  const search = new URL(url).searchParams;
  const lens = search.get("lens") ?? "rotating_updraft";
  const viewport = search.get("viewport") === "full" ? "full" : "storm";
  const timeIndex = Number(search.get("time_index") ?? 5);
  const times = [0, 900, 1_800, 2_700, 3_600, 4_500, 5_400, 6_300, 7_200];
  const xIndex = Number(search.get("x_index") ?? 1);
  const yIndex = Number(search.get("y_index") ?? 1);
  const zIndex = Number(search.get("z_index") ?? 1);
  const x = [-10, 0, 10];
  const y = [-10, 10, 20];
  const z = [0.5, 3, 8];
  const names = {
    rotating_updraft: "Rotating Updraft",
    cloud_precipitation: "Cloud and Precipitation",
    low_level_interactions: "Low-Level Interactions",
  } as const;
  const typedLens = lens as keyof typeof names;
  return {
    schema_version: "supercells_explore_v1",
    authority_state: "supercells_product_world",
    world_id: "supercells",
    simulation_id: simulation.simulation_id,
    run_id: simulation.run_id,
    case_id: simulation.case_id,
    simulation_label: simulation.display_name,
    lens_id: typedLens,
    lens_name: names[typedLens],
    lens_question:
      typedLens === "rotating_updraft"
        ? "Where is the storm rising and rotating as one organized structure?"
        : typedLens === "cloud_precipitation"
          ? "How are cloud and precipitation organized through the storm?"
          : "How do ascent, descent, rain, and horizontal flow meet beneath the storm?",
    what_to_notice_now: "This saved output contains coordinated frame-specific evidence.",
    what_to_notice_by_view: {
      plan: "Plan evidence at this saved output.",
      xz: "X-z evidence at this saved output.",
      yz: "Y-z evidence at this saved output.",
    },
    time_index: timeIndex,
    time_seconds: times[timeIndex],
    times_seconds: times,
    mature_checkpoint_indices: [3, 4, 5, 6, 7, 8],
    timeline_checkpoints: [
      {
        time_seconds: 4_500,
        label: "75 min",
        phase: "Organized mature storm",
        phase_kind: "visible_checkpoint",
      },
    ],
    viewport,
    viewport_bounds_km:
      viewport === "storm"
        ? { x_min: -30, x_max: 30, y_min: -30, y_max: 30 }
        : { x_min: -60, x_max: 60, y_min: -60, y_max: 60 },
    primary_updraft: {
      x_index: 1,
      y_index: 1,
      z_index: 1,
      x_km: 0,
      y_km: 10,
      z_km: 3,
      w_m_s: 48,
    },
    selected_point: selectedPoint(xIndex, yIndex, zIndex, x, y, z, times[timeIndex]),
    plan: plan(typedLens, x, y),
    xz_section: section("xz", "x", y[yIndex] ?? 10),
    yz_section: section("yz", "y", x[xIndex] ?? 0),
    scene: scene(typedLens, viewport),
    caveats: ["Saved histories are 15 minutes apart."],
    provenance: { source_history_file: `cm1out_${String(timeIndex + 1).padStart(6, "0")}.nc` },
    extraction_milliseconds: 80,
  };
}

function selectedPoint(
  xIndex: number,
  yIndex: number,
  zIndex: number,
  x: number[],
  y: number[],
  z: number[],
  time: number,
) {
  const values = {
    vertical_velocity: 12,
    vertical_vorticity: 0.03,
    updraft_helicity: 510,
    reflectivity: 52,
    cloud_liquid: 1.2,
    rain_water: 2.1,
    cloud_ice: 0.4,
    snow: 0.8,
    hail_treated_large_ice: 1.5,
    total_condensate: 6,
    accumulated_surface_rain: 22,
    model_relative_u: 14,
    model_relative_v: 7,
  };
  return {
    x_index: xIndex,
    y_index: yIndex,
    z_index: zIndex,
    x_km: x[xIndex] ?? 0,
    y_km: y[yIndex] ?? 10,
    z_km: z[zIndex] ?? 3,
    model_time_seconds: time,
    coordinate_frame: "translating model frame; native model-relative winds",
    values,
    units: Object.fromEntries(
      Object.keys(values).map((key) => [
        key,
        key.includes("velocity") || key.startsWith("model_relative")
          ? "m/s"
          : key === "vertical_vorticity"
            ? "s^-1"
            : key === "updraft_helicity"
              ? "m^2/s^2"
              : key === "reflectivity"
                ? "dBZ"
                : key === "accumulated_surface_rain"
                  ? "mm"
                  : "g/kg",
      ]),
    ),
    evidence_kind: Object.fromEntries(Object.keys(values).map((key) => [key, "native"])),
    states: ["Rising", "Rotating", "Condensate present"],
    distance_to_primary_updraft_km: 0,
  };
}

function field(key = "winterp", displayName = "Vertical velocity") {
  return {
    key,
    display_name: displayName,
    units: key === "dbz" ? "dBZ" : "m/s",
    evidence_kind: "native",
    source_fields: [key],
    derivation: null,
    values: [
      [-8, -3, 2],
      [-2, 12, 18],
      [1, 7, -5],
    ],
    selected_frame_minimum: -8,
    selected_frame_maximum: 18,
    scale: wScale,
  };
}

function plan(lens: string, x: number[], y: number[]) {
  return {
    title: lens === "cloud_precipitation" ? "Hydrometeor plan" : "Midlevel storm structure",
    subtitle: "Native-grid plan evidence",
    x_indices: [0, 1, 2],
    y_indices: [0, 1, 2],
    x_km: x,
    y_km: y,
    level_index: 1,
    level_km: 3,
    selection_z_indices:
      lens === "cloud_precipitation"
        ? [
            [0, 1, 2],
            [1, 2, 1],
            [0, 1, 2],
          ]
        : null,
    primary: field(),
    overlays: {
      vertical_vorticity: field("zvort", "Vertical vorticity"),
      updraft_helicity: field("uh", "Updraft helicity"),
      vertical_velocity: field("winterp", "Vertical velocity"),
      composite_reflectivity: field("dbz", "Reflectivity"),
      accumulated_surface_rain: field("rain", "Accumulated rain"),
      total_condensate: field("total_condensate", "Total condensate"),
      low_level_precipitating_condensate: field(
        "precipitating_condensate",
        "Current precipitating condensate",
      ),
    },
    categories: null,
    wind_vectors: [{ x_km: 0, y_km: 10, u_m_s: 12, v_m_s: 5, magnitude_m_s: 13 }],
  };
}

function section(orientation: "xz" | "yz", horizontal: "x" | "y", coordinate: number) {
  return {
    orientation,
    title: `${orientation} section at ${orientation === "xz" ? "y" : "x"} = ${coordinate.toFixed(1)} km`,
    horizontal_dimension: horizontal,
    horizontal_indices: [0, 1, 2],
    horizontal_km: [-10, 0, 10],
    z_km: [0.5, 3, 8],
    cross_section_coordinate_km: coordinate,
    primary: field(),
    overlays: {
      vertical_vorticity: field("zvort", "Vertical vorticity"),
      total_condensate: field("total_condensate", "Total condensate"),
      precipitating_condensate: field("precipitating_condensate", "Precipitating condensate"),
      reflectivity: field("dbz", "Reflectivity"),
      vertical_velocity: field(),
    },
    categories: null,
  };
}

function scene(lens: string, viewport: string) {
  const extent = viewport === "storm" ? 30 : 60;
  const points = Array.from({ length: 75 }, (_, index) => {
    const angle = (index / 75) * Math.PI * 2;
    const radius = 4 + (index % 8);
    return [
      Math.cos(angle) * radius,
      10 + Math.sin(angle) * radius,
      0.5 + (index % 18) * 0.6,
      -22 + (index % 10) * 5,
      1 + (index % 5),
    ];
  });
  const layer = (
    key: string,
    displayName: string,
    rendering: string,
    visible: boolean,
    scale: typeof wScale | null = wScale,
  ) => ({
    key,
    display_name: displayName,
    units: rendering === "categorical" ? "g/kg" : "m/s",
    evidence_kind: "native",
    source_fields: ["winterp"],
    derivation: null,
    rendering,
    points,
    source_count: points.length,
    returned_count: points.length,
    threshold_label: "Fixed retained-run threshold",
    default_visible: visible,
    default_opacity: 0.8,
    default_point_size: 1,
    scale,
    categories:
      rendering === "categorical"
        ? [
            { code: 1, key: "qc", label: "Cloud liquid", color: "#d6f0f7" },
            { code: 2, key: "qr", label: "Rain", color: "#2f7fb5" },
            { code: 3, key: "qi", label: "Cloud ice", color: "#c9c5ef" },
            { code: 4, key: "qs", label: "Snow", color: "#71b7d4" },
            { code: 5, key: "qg", label: "Hail-treated large ice", color: "#7c4d8f" },
          ]
        : [],
  });
  const layers =
    lens === "cloud_precipitation"
      ? [
          layer("hydrometeor_categories", "Dominant hydrometeor", "categorical", true, null),
        ]
      : lens === "low_level_interactions"
        ? [
            layer("storm_cloud_body", "Storm cloud body", "neutral_cloud", false, null),
            layer(
              "precipitating_condensate",
              "Low-level precipitating condensate",
              "scalar",
              true,
            ),
            layer("low_level_vertical_motion", "Low-level vertical motion", "signed_scalar", true),
            layer("accumulated_surface_rain", "Accumulated rain", "scalar", true),
          ]
        : [
            layer("storm_cloud_body", "Storm cloud body", "neutral_cloud", true, null),
            layer("rising_core", "Rising core", "signed_scalar", true),
            layer("strong_descent", "Strong descent", "signed_scalar", false),
            layer("cyclonic_rotation", "Cyclonic rotation", "scalar", true),
            layer("updraft_helicity", "2-5 km updraft helicity", "scalar", true),
          ];
  return {
    coordinate_extents_km: {
      x: { min: -extent, max: extent },
      y: { min: -extent, max: extent },
      z: { min: 0.25, max: lens === "low_level_interactions" ? 5.25 : 19.75 },
    },
    coordinate_sizes: { x: 120, y: 120, z: 40 },
    layers,
    wind_vectors: [{ x_km: 0, y_km: 10, z_km: 1.25, u_m_s: 12, v_m_s: 5, magnitude_m_s: 13 }],
    wind_reference_m_s: 25,
    point_budget: 20_000,
    source_history_file: "cm1out_000006.nc",
  };
}

function json(route: Route, payload: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });
}

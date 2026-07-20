import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, openRunMonitor } from "../helpers";
import { mockCloudChamberApis, results } from "../fixtures";

const comparisonBaselineId = "result-trade-cumulus-5b-full-baseline-20260720T162342Z";
const comparisonMoreMoistureId = "result-trade-cumulus-5b-full-more_moisture-20260720T162342Z";

const comparisonBaselineResult = {
  ...results[0],
  result_id: comparisonBaselineId,
  run_id: "trade-cumulus-5b-full-baseline-20260720T162342Z",
  name: "Canonical BOMEX Baseline",
  scenario_id: "bomex_trade_cumulus_baseline_v0",
  scenario_name: "Trade Cumulus",
  run_configuration: {
    ...results[0].run_configuration,
    case_id: "bomex_trade_cumulus_baseline_v0",
  },
};

const comparisonMoreMoistureResult = {
  ...comparisonBaselineResult,
  result_id: comparisonMoreMoistureId,
  run_id: "trade-cumulus-5b-full-more_moisture-20260720T162342Z",
  name: "More Moisture",
};

const comparisonStory = {
  comparison_id: "trade_cumulus_moisture_v1",
  comparison_group_id: "trade_cumulus_moisture_v1",
  product_slice_id: "trade_cumulus_v1",
  case_id: "bomex_trade_cumulus_baseline_v0",
  title: "Trade Cumulus: Baseline and More Moisture",
  question: "How does stronger surface moisture supply change the trade-cumulus field?",
  illustrative_view_note:
    "Illustrative views: selected to help show the response measured across the full simulations. Times and locations may differ, and these are not corresponding individual clouds.",
  baseline: {
    result_id: comparisonBaselineId,
    run_id: comparisonBaselineResult.run_id,
    display_name: "Canonical BOMEX Baseline",
    control_state: "baseline",
    control_label: "Surface moisture supply",
    control_value: 5.2e-5,
    control_units: "g/g m/s",
    control_display: "5.2 × 10⁻⁵ g/g m/s",
    curated_view: {
      time_index: 152,
      time_seconds: 18_240,
      orientation: "vertical_x",
      plane_dimension: "y",
      plane_index: 5,
      plane_coordinate: -2.6500000953674316,
      plane_units: "km",
      camera_preset: "overview",
      cloud_field: "ql",
      cloud_threshold_kg_kg: 1e-6,
      lens_id: "updraft",
      scale_id: "trade_cumulus_updraft_velocity_v1",
      wind_mode: "perturbation",
      show_wind: true,
      show_cloud_boundary: true,
      opacity: 0.68,
      point_size: 11,
      caption:
        "This illustrative Baseline view shows one concentrated active cloud reaching about 2 km, with a strong rising core bordered by sinking air.",
    },
  },
  more_moisture: {
    result_id: comparisonMoreMoistureId,
    run_id: comparisonMoreMoistureResult.run_id,
    display_name: "More Moisture",
    control_state: "more_moisture",
    control_label: "Surface moisture supply",
    control_value: 7.8e-5,
    control_units: "g/g m/s",
    control_display: "7.8 × 10⁻⁵ g/g m/s",
    curated_view: {
      time_index: 169,
      time_seconds: 20_280,
      orientation: "vertical_x",
      plane_dimension: "y",
      plane_index: 51,
      plane_coordinate: 1.9500000476837158,
      plane_units: "km",
      camera_preset: "overview",
      cloud_field: "ql",
      cloud_threshold_kg_kg: 1e-6,
      lens_id: "updraft",
      scale_id: "trade_cumulus_updraft_velocity_v1",
      wind_mode: "perturbation",
      show_wind: true,
      show_cloud_boundary: true,
      opacity: 0.68,
      point_size: 11,
      caption:
        "This illustrative More Moisture view shows several active clouds across the slice, with rising cores distributed through a broader cloud-filled region reaching just above 2 km.",
    },
  },
  changed_condition: {
    label: "Surface moisture supply",
    baseline_display: "5.2 × 10⁻⁵ g/g m/s",
    more_moisture_display: "7.8 × 10⁻⁵ g/g m/s",
    change_display: "+50%",
  },
  material_responses: [
    {
      metric_id: "mean_cloud_cover_final_three_hours",
      label: "Mean cloud cover, final three hours",
      baseline_value: 10.596239697802197,
      more_moisture_value: 12.710873111263735,
      absolute_delta: 2.1146334134615383,
      percent_delta: 19.956451286206196,
      units: "%",
      method: "time mean of horizontal columns containing ql >= 1e-6 kg/kg",
      window: "time >= 10800 s",
      baseline_display: "10.596%",
      more_moisture_display: "12.711%",
      change_display: "+2.115 percentage points",
    },
    {
      metric_id: "mean_cloud_water_path_final_three_hours",
      label: "Mean cloud-water path, final three hours",
      baseline_value: 0.006351999299305916,
      more_moisture_value: 0.009071426778155891,
      absolute_delta: 0.0027194274788499753,
      percent_delta: 42.81215017053178,
      units: "kg/m^2",
      method: "time mean of horizontal domain-mean cwp",
      window: "time >= 10800 s",
      baseline_display: "0.006352 kg/m²",
      more_moisture_display: "0.009071 kg/m²",
      change_display: "+42.812%",
    },
    {
      metric_id: "mean_coherent_cloud_top_final_three_hours",
      label: "Mean coherent cloud top, final three hours",
      baseline_value: 1668.3517340775375,
      more_moisture_value: 1805.0550379595913,
      absolute_delta: 136.7033038820539,
      percent_delta: 8.193913854600911,
      units: "m",
      method: "mean supported coherent cloud-object top",
      window: "time >= 10800 s",
      baseline_display: "1,668 m",
      more_moisture_display: "1,805 m",
      change_display: "+137 m",
    },
  ],
  small_or_mixed_responses: [
    {
      title: "Initial cloud-liquid onset was unchanged.",
      body: "Both simulations first reached the cloud-liquid threshold at 1,080 s.",
    },
    {
      title: "The cloud-fraction peak stayed at the same height.",
      body: "Both final-three-hour profiles peaked near 620 m.",
    },
    {
      title: "The fraction of cloudy air rising changed very little.",
      body: "It was 90.379% in Baseline and 90.451% in More Moisture.",
    },
    {
      title: "The response varied through time.",
      body: "More Moisture was not cloudier or wetter than Baseline at every individual saved frame.",
    },
  ],
  held_fixed_by_design: {
    lead: "Only surface moisture supply changed.",
    groups: [
      {
        title: "Initial atmosphere",
        body: "Thermodynamic, moisture, and wind profiles, including the deterministic perturbation.",
      },
      {
        title: "Forcing",
        body: "Sensible heat supply, friction velocity, large-scale forcing, geostrophic wind, and Coriolis treatment.",
      },
      {
        title: "Model setup",
        body: "Moist physics, turbulence, boundaries, domain, grid, and timestep strategy.",
      },
      {
        title: "Execution and outputs",
        body: "Duration, output cadence, requested fields, CM1 source and executable, and the Cloud Chamber implementation commit.",
      },
    ],
  },
  explanation_paragraphs: [
    "More surface moisture produced a cloudier, wetter, somewhat deeper trade-cumulus field.",
    "Only the lower-boundary moisture supply changed. Over the final three hours, More Moisture covered more of the domain with cloud, held about 43 percent more mean cloud-water path, and produced coherent clouds averaging 137 meters taller.",
    "It did not create a completely different circulation regime. Initial cloud-liquid onset and the height of the cloud-fraction maximum were unchanged, and about 90 percent of cloudy cells were rising in both simulations.",
    "The illustrative Lens views are selected to help show the measured response. They show different times and locations and are not one-to-one matches of individual clouds. More Moisture was also not cloudier at every saved frame, so the result is a change in the evolving cloud field rather than a rule that every moment must look larger.",
  ],
  evidence_summary: {
    analysis_window: "time >= 10800 s",
    analysis_start_seconds: 10_800,
    analysis_end_seconds: 21_600,
    output_cadence_seconds: 120,
    paired_saved_frame_count: 181,
  },
  provenance: {
    evidence_state: "matched_runs_valid",
    evidence_version: "trade_cumulus_moisture_comparison_evidence_v1",
    implementation_commit: "49da1defc9914d3cc903ed9589c1312ddd843726",
    fixed_assumptions_sha256: "71d746b110fb1310ebb6dafbef4cfa4bd44c379fc6964ed1787deaf45e422535",
    baseline_run_id: comparisonBaselineResult.run_id,
    baseline_result_id: comparisonBaselineId,
    more_moisture_run_id: comparisonMoreMoistureResult.run_id,
    more_moisture_result_id: comparisonMoreMoistureId,
    scale_id: "trade_cumulus_updraft_velocity_v1",
    comparison_source: "runtime_matched_pair_evidence",
  },
  caveats: [
    "one_deterministic_les_realization_per_control_state",
    "illustrative_views_are_not_direct_frame_matches",
    "individual_clouds_are_not_paired_one_to_one",
    "candidate_product_slice_not_supported_status",
  ],
};

const comparisonUpdraftScale = {
  w_range_min_m_s: -1,
  w_range_max_m_s: 5,
  w_range_method: "fixed_trade_cumulus_updraft_velocity_v1",
  w_scale_id: "trade_cumulus_updraft_velocity_v1",
  w_scale_owner: "trade_cumulus",
  w_scale_type: "fixed_discrete",
  w_scale_units: "m/s",
  w_scale_breakpoints_m_s: [-1, -0.5, -0.1, 0.1, 0.5, 1, 2, 3, 5],
  w_scale_colors: [
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
  w_scale_neutral_interval_m_s: [-0.1, 0.1],
  w_scale_source: "pm_approved_issue_379_from_stage5b2_matched_pair",
  w_scale_clipping_behavior:
    "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped",
};

type ComparisonMember = typeof comparisonStory.baseline;

function comparisonPointCloud(member: ComparisonMember) {
  const offset = member.control_state === "baseline" ? 0 : 0.45;
  const points: Array<[number, number, number, number]> = [
    [-1.8 + offset, -0.8, 0.5, 0.00035],
    [-1.2 + offset, -0.4, 0.9, 0.0008],
    [-0.5 + offset, 0.1, 1.35, 0.0012],
    [0.3 + offset, 0.6, 1.8, 0.00095],
    [1.4 + offset, 1.1, 1.15, 0.0005],
  ];
  return {
    result_id: member.result_id,
    run_id: member.run_id,
    scenario_id: "bomex_trade_cumulus_baseline_v0",
    field: { raw_field_name: "ql", display_name: "Cloud water", units: "kg/kg" },
    selection: {
      field: "ql",
      time_index: member.curated_view.time_index,
      time_seconds: member.curated_view.time_seconds,
      threshold: 1e-6,
      max_points: 50_000,
    },
    coordinate_units: { xh: "km", yh: "km", zh: "km" },
    coordinate_extents: {
      xh: { min: -3.2, max: 3.2, units: "km" },
      yh: { min: -3.2, max: 3.2, units: "km" },
      zh: { min: 0, max: 3, units: "km" },
    },
    points,
    stats: {
      source_count: points.length,
      returned_count: points.length,
      field_min_value: 0,
      field_max_value: 0.0012,
      field_mean_value: 0.00076,
      field_finite_count: points.length,
      field_non_finite_count: 0,
      min_value: 0.00035,
      max_value: 0.0012,
      active_z_min: 0.5,
      active_z_max: 1.8,
      downsampled: false,
      downsample_stride: 1,
    },
    provenance: {
      source_model: "CM1",
      result_id: member.result_id,
      run_id: member.run_id,
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      processing_method: "backend_xarray_native_grid_threshold",
      rendering_method: "thresholded_point_cloud",
      provenance_label: "CM1-derived cloud water point cloud",
    },
    caveats: [],
  };
}

function comparisonLensFrame(member: ComparisonMember) {
  const values =
    member.control_state === "baseline"
      ? [
          [-0.6, -0.2, 0.3, 0.6],
          [-0.3, 0.1, 0.9, 1.4],
          [-0.1, 0.4, 1.8, 2.5],
          [0, 0.2, 0.8, 0.4],
        ]
      : [
          [-0.5, -0.1, 0.4, 0.8],
          [-0.2, 0.5, 1.5, 2.2],
          [0.1, 0.9, 2.8, 4.1],
          [0.2, 0.6, 1.7, 0.7],
        ];
  return {
    result_id: member.result_id,
    time_index: member.curated_view.time_index,
    time_seconds: member.curated_view.time_seconds,
    orientation: "vertical_x",
    plane_dimension: "y",
    plane_index: member.curated_view.plane_index,
    plane_coordinate: member.curated_view.plane_coordinate,
    plane_units: "km",
    dimension_order: ["z", "x"],
    x_indices: [0, 1, 2, 3],
    x_values_km: [-3.2, -1.1, 1.1, 3.2],
    y_indices: [0, 1],
    y_values_km: [-3.2, 3.2],
    z_indices: [0, 1, 2, 3],
    z_values_km: [0, 1, 2, 3],
    w_values_m_s: values,
    cloud_mask: [
      [false, true, true, false],
      [true, true, true, false],
      [false, true, true, true],
      [false, false, true, false],
    ],
    cloud_threshold_kg_kg: 1e-6,
    ...comparisonUpdraftScale,
    w_finite_count: 16,
    w_low_clipped_count: 0,
    w_high_clipped_count: 0,
    w_low_clipped_fraction: 0,
    w_high_clipped_fraction: 0,
    wind_mode: "perturbation",
    wind_target_level_m: 600,
    wind_actual_level_m: 580,
    wind_level_index: 14,
    wind_stride: 8,
    wind_reference_m_s: 0.9,
    wind_arrow_domain_fraction: 0.08,
    domain_mean_u_m_s: 0,
    domain_mean_v_m_s: 0,
    wind_vectors: [
      { x_km: -2, y_km: 0, z_km: 0.58, u_m_s: 0.4, v_m_s: 0.2, magnitude_m_s: 0.45 },
      { x_km: 0, y_km: 0, z_km: 0.58, u_m_s: -0.3, v_m_s: 0.4, magnitude_m_s: 0.5 },
      { x_km: 2, y_km: 0, z_km: 0.58, u_m_s: 0.2, v_m_s: -0.4, magnitude_m_s: 0.45 },
    ],
    provenance: {
      source_model: "CM1",
      result_id: member.result_id,
      run_id: member.run_id,
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      processing_method: "trade_cumulus_updraft_lens_frame",
      rendering_method: "native_grid_slice",
      provenance_label: "CM1-derived Updraft Lens frame",
    },
    caveats: [],
  };
}

async function mockTradeCumulusComparison(page: Parameters<typeof mockCloudChamberApis>[0]) {
  await page.route("**/api/results", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [comparisonBaselineResult, comparisonMoreMoistureResult, results[0]],
      }),
    }),
  );
  await page.route("**/api/comparisons/trade-cumulus-moisture-v1", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparisonStory),
    }),
  );
  await page.route("**/api/results/*/visualization/point-cloud**", (route) => {
    const url = route.request().url();
    const member = url.includes(comparisonMoreMoistureId)
      ? comparisonStory.more_moisture
      : comparisonStory.baseline;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparisonPointCloud(member)),
    });
  });
  await page.route("**/api/results/*/visualization/trade-cumulus-updraft-lens/frame**", (route) => {
    const member = route.request().url().includes(comparisonMoreMoistureId)
      ? comparisonStory.more_moisture
      : comparisonStory.baseline;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparisonLensFrame(member)),
    });
  });
}

test.describe("mocked smoke: Build, Results, Explore path", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
    await page.route("**/api/comparisons/trade-cumulus-moisture-v1", (route) =>
      route.fulfill({ status: 404, contentType: "application/json", body: "{}" }),
    );
    await gotoApp(page);
  });

  test("Build exposes the Golden Path scenario and creates a safe dry-run package", async ({
    page,
  }) => {
    await gotoBuild(page);

    await expect(page.locator("select").first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Observed Soundings" })).toBeVisible();
    await page.getByLabel("Experiment", { exact: true }).selectOption("baseline-shallow-cumulus");
    await expect(page.getByText(/physical question/i).first()).toBeVisible();
    await expect(page.getByText(/how do low-level moisture/i).first()).toBeVisible();
    await openRunMonitor(page);
    await expect(
      page.getByRole("heading", { name: "Packages and runs needing action" }),
    ).toBeVisible();
    await expect(
      page.getByTestId("package-review-panel").getByText("Not packaged yet").first(),
    ).toBeVisible();
    await expect(page.getByText("Build pipeline")).toBeVisible();
    await expect(page.getByText("Local experiment loop")).not.toBeVisible();
    await expect(page.getByText("Ready to ingest")).toBeVisible();
    await expect(page.getByRole("button", { name: "Preview cleanup" }).first()).toBeVisible();
    await page.getByLabel("Low-level humidity").selectOption("more_humid");
    await expect(page.getByText(/Selected: More humid/i)).toBeVisible();

    await page.getByTestId("create-package-btn").scrollIntoViewIfNeeded();
    await page.getByTestId("create-package-btn").click();

    await expect(page.getByTestId("package-review-panel")).toBeVisible();
    await expect(page.getByText("Package ready").first()).toBeVisible();
    await expect(page.getByText("Latest generated package")).toBeVisible();
    await expect(page.getByRole("button", { name: "Create another package" })).toBeVisible();
    await expect(page.getByText("/tmp/cloud-chamber-e2e/run/run_manifest.json")).toBeVisible();
    await expect(page.getByText("Expected output directory").locator("..")).toContainText(
      "/tmp/cloud-chamber-e2e/run",
    );
    await expect(page.getByText(/not a completed CM1 result/i).first()).toBeVisible();
    await expect(page.getByTestId("launch-cm1-btn")).toBeEnabled();

    await page.getByTestId("launch-cm1-btn").click();
    await expect(
      page.getByLabel("Local serial run queue").getByText("Auto-ingested", { exact: true }),
    ).toBeVisible();
    await expect(page.getByTestId("ingest-results-btn")).toHaveCount(0);

    await page
      .getByLabel("Ingested result actions")
      .getByRole("button", { name: "Open in Results" })
      .click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
  });

  test("Build can review an observed IGRA sounding before package creation", async ({ page }) => {
    await gotoBuild(page);

    await page
      .getByLabel("Experiment", { exact: true })
      .selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Observed Soundings" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Find interesting soundings" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Cached recommendations" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByLabel("IGRA station sounding-data file")).not.toBeVisible();
    await page.getByRole("tab", { name: "Upload IGRA station text" }).click();
    await expect(page.getByLabel("IGRA station sounding-data file")).toBeVisible();
    await expect(page.getByLabel("Low-level humidity")).not.toBeVisible();
    await expect(page.getByLabel("Use uploaded sounding")).not.toBeVisible();

    await page.getByLabel("IGRA station sounding-data file").setInputFiles({
      name: "USM00072558-data.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("#USM00072558 2025 01 02 00"),
    });

    await expect(page.getByText("Observed sounding validated for package review")).toBeVisible();
    await expect(page.getByText("Valley, Nebraska (USM00072558)").first()).toBeVisible();
    await expect(page.locator("#observed-sounding-time")).toHaveValue("2025-01-02T00:00:00Z");
    const observedReview = page.getByLabel("Observed sounding review");
    await observedReview.getByText("Uploaded-sounding review").click();
    await expect(observedReview.getByText("USM00072558 · Valley, Nebraska")).toBeVisible();
    await expect(
      observedReview.getByText(/CM1 z=0 is station surface at 351.5 m MSL/i),
    ).toBeVisible();
    await expect(observedReview.getByText(/generated CM1 namelist uses isnd=7/i)).toBeVisible();

    await observedReview.getByText("Observed-sounding caveats").click();
    await expect(
      observedReview.getByText("Station elevation joined from igra station fixture"),
    ).toBeVisible();

    await page.getByRole("button", { name: "Add to run plan" }).click();
    await expect(
      page.getByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeVisible();
    await expect(page.getByLabel("Run plan").getByLabel("Surface heat flux").first()).toHaveValue(
      "8.0e-3",
    );
    await expect(
      page.getByLabel("Run plan").getByLabel("Surface moisture flux").first(),
    ).toHaveValue("5.2e-5");

    await page.getByRole("button", { name: "Create packages and queue selected runs" }).click();
    await expect(page.getByText("Queued for local serial CM1 run.")).toBeVisible();
    await expect(page.getByText("1 queued locally")).toBeVisible();
  });

  test("Build can screen, save, and use observed sounding candidates", async ({ page }) => {
    await gotoBuild(page);

    await page
      .getByLabel("Experiment", { exact: true })
      .selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Find interesting soundings" })).toBeVisible();
    await expect(page.getByText("Cached soundings ready to search")).toBeVisible();
    await expect(page.getByLabel("Prepare and search local soundings")).toContainText(
      "Selected soundings",
    );
    await expect(page.getByLabel("Station picker")).toContainText("All cached stations");
    await expect(page.getByLabel("Local sounding data")).toContainText("2 cached soundings");
    await expect(page.getByLabel("Advanced sounding candidate controls")).not.toBeVisible();

    await page.getByText("Advanced filters", { exact: true }).click();
    await page.getByRole("button", { name: "Refresh catalog" }).click();
    await expect(page.getByText("IGRA station catalog refreshed")).toBeVisible();
    await expect(page.getByLabel("Local sounding data")).toContainText("2 cached soundings");
    await page.getByLabel("Local sounding data").locator("summary").click();
    await expect(page.getByText("Parsed soundings")).toBeVisible();

    const candidateControls = page.getByLabel("Advanced sounding candidate controls");
    const storySelect = candidateControls.getByRole("combobox").first();
    await storySelect.selectOption("shallow_cumulus_candidate");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();

    await expect(page.getByText("Cached sounding analysis loaded")).toBeVisible();
    const valleyCard = page.getByLabel("Sounding candidate Valley, Nebraska (USM00072558)");
    await expect(valleyCard).toBeVisible();
    await expect(valleyCard).toContainText("Cloud-forming shallow cumulus");
    await expect(valleyCard).toContainText("Package-ready");
    await expect(valleyCard).toContainText("Why it surfaced");
    await expect(valleyCard).toContainText("Good for a surface-forced run");
    const candidateDetails = page.getByLabel("Candidate details");
    await expect(candidateDetails).toContainText("Why this is interesting");
    await expect(candidateDetails).toContainText("Run guidance");
    await expect(candidateDetails).toContainText("Run fit");
    await expect(candidateDetails).toContainText("Top limits");
    await expect(candidateDetails).not.toContainText("Scores rank sounding ingredients only");
    await expect(
      candidateDetails.getByText("All evidence").locator("xpath=.."),
    ).not.toHaveAttribute("open");

    await storySelect.selectOption("needs_review");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();
    const blockedCard = page.getByLabel("Sounding candidate Norman, Oklahoma (USM00072357)");
    await expect(blockedCard).toBeVisible();
    await expect(blockedCard).toContainText("Blocked");
    await expect(blockedCard.getByRole("button", { name: "Configure run" })).toBeDisabled();

    await storySelect.selectOption("all");
    await page.getByRole("button", { name: "Apply advanced filters" }).click();
    const refreshedValleyCard = page.getByLabel(
      "Sounding candidate Valley, Nebraska (USM00072558)",
    );
    await refreshedValleyCard.click();
    await expect(page.getByRole("textbox", { name: "Tags" })).toHaveCount(0);
    await page
      .getByLabel("Candidate details")
      .getByRole("button", { name: "Save candidate" })
      .click();
    await page.getByRole("textbox", { name: "Tags" }).fill("smoke");
    await page.getByLabel("Save candidate notes").getByRole("button", { name: "Save" }).click();
    await expect(page.getByText("Sounding candidate saved")).toBeVisible();
    await page.getByRole("tab", { name: /Saved candidates/ }).click();
    const savedCard = page.getByLabel("Saved sounding candidate Valley, Nebraska (USM00072558)");
    await expect(savedCard).toBeVisible();

    await savedCard.getByRole("button", { name: "Configure run" }).click();
    await expect(page.getByLabel("Selected sounding run setup")).toBeVisible();
    const selectedSetupOrderIsCorrect = await page.evaluate(() => {
      const saved = document.querySelector(
        '[aria-label="Saved sounding candidate Valley, Nebraska (USM00072558)"]',
      );
      const setup = document.querySelector('[aria-label="Selected sounding run setup"]');
      const runPlan = document.querySelector('[aria-label="Run plan"]');
      return Boolean(
        saved &&
        setup &&
        runPlan &&
        saved.compareDocumentPosition(setup) & Node.DOCUMENT_POSITION_FOLLOWING &&
        setup.compareDocumentPosition(runPlan) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(selectedSetupOrderIsCorrect).toBe(true);
    await page.getByRole("button", { name: "Add to run plan" }).click();
    await expect(
      page.getByText("Valley, Nebraska (USM00072558) added to the run plan"),
    ).toBeVisible();
    await expect(page.getByLabel("Run plan").getByLabel("Surface heat flux").first()).toHaveValue(
      "8.0e-3",
    );
    await expect(
      page.getByLabel("Run plan").getByLabel("Surface moisture flux").first(),
    ).toHaveValue("5.2e-5");
    await page.getByRole("button", { name: "Duplicate variant" }).click();
    await expect(page.getByText("Run-plan variant duplicated")).toBeVisible();

    await page.getByRole("button", { name: "Create packages and queue selected runs" }).click();
    await expect(page.getByText("2 queued locally")).toBeVisible();
    await expect(page.getByText("Queued for local serial CM1 run.").first()).toBeVisible();
  });

  test("Results notebook renders with mocked data", async ({ page }) => {
    await gotoResults(page);

    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    const resultsList = page.getByLabel("Results list");
    await expect(resultsList).toBeVisible();
    await expect(page.getByText("Baseline Shallow Cumulus — Quick Look").first()).toBeVisible();
    await expect(
      resultsList.getByText(/Cloud water formed in the validated reference baseline/i),
    ).toBeVisible();
    await expect(resultsList.getByText("Cloud formed").first()).toBeVisible();
    await expect(resultsList.getByText("Rain water aloft detected").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Open in Explore" }).first()).toBeVisible();
    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByText("Technical details").click();
    await expect(resultDetail.getByText("Run ID")).toBeVisible();
    await expect(resultDetail.getByText("Product state")).toBeVisible();
    await expect(
      resultDetail.getByRole("button", { name: "Preview delete result and local run data" }),
    ).toBeVisible();
    await expect(resultDetail.getByText("Local data")).toBeVisible();
    await expect(page.getByRole("tab", { name: "Compare" })).toHaveCount(0);
    await expect(page.getByRole("tab", { name: "Storage" })).toHaveCount(0);
  });

  test("Results opens the complete curated Trade Cumulus comparison story", async ({ page }) => {
    const browserErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(`console: ${message.text()}`);
    });
    page.on("pageerror", (error) => browserErrors.push(`page: ${error.message}`));
    page.on("requestfailed", (request) => {
      const failure = request.failure()?.errorText ?? "unknown failure";
      if (request.url().includes("/api/") && !failure.includes("ERR_ABORTED")) {
        browserErrors.push(`request: ${request.method()} ${request.url()} (${failure})`);
      }
    });

    await mockTradeCumulusComparison(page);
    await page.reload();
    await gotoResults(page);
    browserErrors.length = 0;

    await page.getByRole("button", { name: "Canonical BOMEX Baseline" }).click();
    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByRole("button", { name: "Compare Baseline and More Moisture" }).click();

    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toBeVisible();
    await expect(page.getByText(comparisonStory.question)).toBeVisible();
    await expect(page.getByLabel("Changed condition")).toContainText("+50%");
    await expect(page.getByText(comparisonStory.illustrative_view_note)).toBeVisible();

    const simulations = page.locator("article.comparison-simulation");
    await expect(simulations).toHaveCount(2);
    await expect(simulations.nth(0)).toContainText("18,240 s · 05:04:00");
    await expect(simulations.nth(0)).toContainText("Vertical x-z slice at y = -2.65 km");
    await expect(simulations.nth(1)).toContainText("20,280 s · 05:38:00");
    await expect(simulations.nth(1)).toContainText("Vertical x-z slice at y = 1.95 km");
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toHaveCount(2);
    await expect(page.getByTestId("updraft-lens-cloud-boundary")).toHaveCount(2);
    await expect(page.getByLabel(/3-D viewer Vertical velocity \(w\), m\/s/)).toHaveCount(2);
    await expect(page.getByLabel(/2-D inspector Vertical velocity \(w\), m\/s/)).toHaveCount(2);
    await expect(page.getByRole("heading", { name: "What responded materially" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "What changed little or varied" }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "What stayed fixed" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "What this comparison suggests" }),
    ).toBeVisible();

    const canvases = page.locator("canvas.true3d-canvas");
    await expect(canvases).toHaveCount(2);
    for (let index = 0; index < 2; index += 1) {
      await expect(canvases.nth(index)).toBeVisible();
      const dimensions = await canvases.nth(index).evaluate((canvas: HTMLCanvasElement) => ({
        displayWidth: canvas.clientWidth,
        displayHeight: canvas.clientHeight,
        renderWidth: canvas.width,
        renderHeight: canvas.height,
      }));
      expect(dimensions.displayWidth).toBeGreaterThan(100);
      expect(dimensions.displayHeight).toBeGreaterThan(100);
      expect(dimensions.renderWidth).toBeGreaterThan(100);
      expect(dimensions.renderHeight).toBeGreaterThan(100);
      const renderedPixels = await canvases.nth(index).screenshot();
      expect(renderedPixels.byteLength).toBeGreaterThan(5_000);
    }

    const baselineControls = simulations.nth(0).getByLabel("3-D camera controls");
    const moreMoistureControls = simulations.nth(1).getByLabel("3-D camera controls");
    await baselineControls.getByRole("button", { name: "Look along x" }).click();
    await expect(baselineControls).toContainText("Camera looking along the x axis");
    await expect(moreMoistureControls).toContainText("Camera ready");

    await page.setViewportSize({ width: 390, height: 844 });
    await expect(simulations.nth(0)).toBeVisible();
    await expect(simulations.nth(1)).toBeVisible();
    const mobileLayout = await simulations.evaluateAll((cards) => {
      const first = cards[0].getBoundingClientRect();
      const second = cards[1].getBoundingClientRect();
      return {
        stacked: second.top >= first.bottom,
        fitsViewport: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      };
    });
    expect(mobileLayout).toEqual({ stacked: true, fitsViewport: true });

    await page.setViewportSize({ width: 1440, height: 1000 });
    await simulations.nth(1).getByRole("button", { name: "Open More Moisture in Explore" }).click();
    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toHaveCount(0);
    await expect(page.getByLabel("Explore viewer controls")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("More Moisture").first()).toBeVisible();

    await page
      .getByRole("navigation", { name: "Cloud Chamber workspace" })
      .getByRole("button", { name: "Results" })
      .click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    await page.getByRole("button", { name: "More Moisture", exact: true }).click();
    await page
      .getByLabel("Result detail")
      .getByRole("button", { name: "Compare Baseline and More Moisture" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Trade Cumulus: Baseline and More Moisture" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Back to Results" }).click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    expect(browserErrors).toEqual([]);
  });

  test("Results filters and sorts by science metadata", async ({ page }) => {
    await gotoResults(page);

    const filterBar = page.getByLabel("Filter and sort results");
    const resultsList = page.getByLabel("Results list");

    await expect(filterBar).toBeVisible();
    await expect(resultsList.getByText(/first cloud 1,800 s/i).first()).toBeVisible();

    await filterBar.getByLabel("Search").fill("Valley");
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toBeVisible();
    await expect(
      resultsList.getByText("Observed sounding: USM00072558 · Valley, Nebraska"),
    ).toBeVisible();
    await expect(resultsList.getByText("Baseline Shallow Cumulus — Quick Look")).toHaveCount(0);

    await filterBar.getByLabel("Search").fill("");
    await filterBar.getByLabel("Scenario").selectOption("input_source:observed_sounding");
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toBeVisible();
    await expect(resultsList.getByText("Baseline Shallow Cumulus — Quick Look")).toHaveCount(0);

    await filterBar.getByLabel("Scenario").selectOption("all");
    await filterBar.getByLabel("Cloud outcome").selectOption("no");
    await expect(resultsList.getByText("Dry Failed Cumulus — Quick Look")).toBeVisible();
    await expect(resultsList.getByText("Uploaded Sounding — Valley, Nebraska")).toHaveCount(0);

    await filterBar.getByLabel("Cloud outcome").selectOption("all");
    await filterBar.getByLabel("Sort results").selectOption("max_updraft");
    await expect(resultsList.locator(".experiment-card").first()).toContainText(
      "Uploaded Sounding — Valley, Nebraska",
    );
  });

  test("Results deletes ingested results and Build keeps non-ingested cleanup", async ({
    page,
  }) => {
    await gotoResults(page);

    const resultDetail = page.getByLabel("Result detail");
    await resultDetail
      .getByRole("button", { name: "Preview delete result and local run data" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Delete result and local run data preview" }),
    ).toBeVisible();
    await expect(
      page.getByText(/result will disappear from Results, Explore, and local inventory/),
    ).toBeVisible();
    await expect(page.getByText("Result metadata and notebook edits")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Delete result and local run data", exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Delete result and local run data", exact: true })
      .click();
    await expect(
      page.getByRole("status").filter({ hasText: /Result and local run data deleted/ }),
    ).toBeVisible();
    await expect(
      page.getByLabel("Results list").getByText("Baseline Shallow Cumulus — Quick Look"),
    ).toHaveCount(0);

    await gotoBuild(page);
    await openRunMonitor(page);
    const pipelineRuns = page.getByLabel("Local packages and runs");
    const ingestReadyRun = pipelineRuns.locator("article", { hasText: "dry-run-disposable" });
    await expect(ingestReadyRun.getByText("Ready to ingest")).toBeVisible();
    await expect(ingestReadyRun.getByRole("button", { name: "Preview cleanup" })).toBeEnabled();
    await ingestReadyRun.getByRole("button", { name: "Preview cleanup" }).click();
    await expect(
      page.getByRole("heading", { name: "Delete local package/run data preview" }),
    ).toBeVisible();
    await expect(page.getByText(/does not touch Results entries/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Confirm delete local run data" })).toBeVisible();

    await ingestReadyRun.getByRole("button", { name: "Ingest output" }).click();
    await expect(page.getByText("Ingested result metadata")).toBeVisible();

    const runningRun = pipelineRuns.locator("article", { hasText: "dry-run-running" });
    await expect(runningRun.getByText("Running", { exact: true })).toBeVisible();
    await expect(runningRun.getByRole("button", { name: "Preview cleanup" })).toBeDisabled();

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();
    await expect(page.getByText(/what happened in this result/i).first()).toBeVisible();
  });

  test("Results notebook remains card-first on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await gotoResults(page);

    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    const resultsList = page.getByLabel("Results list");
    await expect(resultsList).toBeVisible();
    await expect(page.getByText("Baseline Shallow Cumulus — Quick Look").first()).toBeVisible();
    await expect(
      resultsList.getByText(/Cloud water formed in the validated reference baseline/i),
    ).toBeVisible();
    await expect(page.getByLabel("Result detail")).toBeVisible();
    await expect(page.getByRole("button", { name: "Open in Explore" }).first()).toBeVisible();
  });

  test("Unified Explore renders cloud context, slice inspector, and explanation", async ({
    page,
  }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/what happened in this result/i).first()).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByLabel("Explore viewer controls")).toBeVisible();
    await expect(page.getByLabel("True 3-D scalar field viewer")).toBeVisible({
      timeout: 12_000,
    });
    await expect(
      page.getByLabel(
        "Interactive Three.js scene showing a CM1 scalar field, domain bounds, slice plane, and selected point",
      ),
    ).toBeVisible();
    await expect(page.getByLabel("3-D camera controls")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Inspect the current slice" })).toBeVisible();
    await expect(page.getByText(/Horizontal layer at z = /i).first()).toBeVisible();
    await expect(page.getByLabel("Slice position")).toBeVisible();
    await expect(page.getByRole("button", { name: /move down/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /move up/i })).toBeVisible();
    const heatmap = page.getByRole("img", { name: /heatmap/i });
    await expect(heatmap).toBeVisible();
    await expect(page.getByTestId("slice-cloud-boundary")).toBeVisible();
    const heatmapLayout = await heatmap.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      const grid = element.querySelector<HTMLElement>(".slice-heatmap-grid");
      const row = element.querySelector<HTMLElement>(".heatmap-row");
      return {
        declaredAspect: Number(element.getAttribute("data-domain-aspect")),
        renderedAspect: bounds.width / bounds.height,
        gridGap: grid ? getComputedStyle(grid).gap : null,
        rowGap: row ? getComputedStyle(row).gap : null,
        padding: getComputedStyle(element).padding,
      };
    });
    expect(Math.abs(heatmapLayout.declaredAspect - heatmapLayout.renderedAspect)).toBeLessThan(
      0.03,
    );
    expect(heatmapLayout.gridGap).toBe("0px");
    expect(heatmapLayout.rowGap).toBe("0px");
    expect(heatmapLayout.padding).toBe("0px");
    const fieldControlsPrecedeHeatmap = await heatmap.evaluate((element) => {
      const fieldControl = document.querySelector("#explore-slice-field");
      return Boolean(
        fieldControl &&
        fieldControl.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(fieldControlsPrecedeHeatmap).toBe(true);
    await page
      .getByRole("button", { name: /inspect .*row 2, column 2/i })
      .first()
      .click();
    await expect(page.getByText(/what happened here/i).first()).toBeVisible();
    await expect(page.getByText(/selected-point diagnostics loaded/i)).toBeVisible();
    await expect(page.getByText(/cloud water appeared locally/i)).toBeVisible();
    await expect(page.getByText(/local max w/i)).toBeVisible();
    await page.getByText("Technical slice details").first().click();
    await expect(page.getByText(/finite values/i).first()).toBeVisible();
    await expect(page.getByText(/\[\[[\d.,\s]+\]\]/)).not.toBeVisible();

    await expect(page.getByText("Cloud formed in this result")).toBeVisible();
    await expect(page.getByText("Cloud formed here")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /reset camera/i })).toBeVisible();
    await expect(page.getByText(/selected point: x/i)).toBeVisible();
  });

  test("Trade Cumulus activates the Updraft Lens with bounded process controls", async ({
    page,
  }) => {
    const catalog = await page.evaluate(async () =>
      fetch("/api/results/result-baseline/visualization/fields").then((response) =>
        response.json(),
      ),
    );
    const tradeResult = {
      ...results[0],
      name: "Trade Cumulus",
      scenario_id: "bomex_trade_cumulus_baseline_v0",
      scenario_name: "Trade Cumulus",
      run_configuration: {
        ...results[0].run_configuration,
        case_id: "bomex_trade_cumulus_baseline_v0",
      },
    };
    catalog.scenario_id = "bomex_trade_cumulus_baseline_v0";
    catalog.available_fields[0] = {
      ...catalog.available_fields[0],
      raw_field: "ql",
      raw_field_name: "ql",
      display_name: "Cloud liquid",
    };
    const updraftScale = {
      w_range_min_m_s: -1.0,
      w_range_max_m_s: 5.0,
      w_range_method: "fixed_trade_cumulus_updraft_velocity_v1",
      w_scale_id: "trade_cumulus_updraft_velocity_v1",
      w_scale_owner: "trade_cumulus",
      w_scale_type: "fixed_discrete",
      w_scale_units: "m/s",
      w_scale_breakpoints_m_s: [-1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0],
      w_scale_colors: [
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
      w_scale_neutral_interval_m_s: [-0.1, 0.1],
      w_scale_source: "pm_approved_issue_379_from_stage5b2_matched_pair",
      w_scale_clipping_behavior:
        "values_below_-1.0_and_at_or_above_5.0_use_endpoint_colors_and_are_reported_as_clipped",
    };

    await page.route("**/api/results", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ results: [tradeResult] }),
      }),
    );
    await page.route("**/api/results/result-baseline/visualization/fields", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(catalog),
      }),
    );
    await page.route(
      "**/api/results/result-baseline/visualization/trade-cumulus-updraft-lens/defaults",
      (route) =>
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            result_id: "result-baseline",
            case_id: "bomex_trade_cumulus_baseline_v0",
            eligible: true,
            primary_field: "w",
            cloud_field: "ql",
            orientation: "vertical_x",
            default_time_index: 1,
            default_time_seconds: 1800,
            default_time_method: "max_finite_domain_mean_cwp_at_or_after_10800_seconds",
            default_plane_dimension: "y",
            default_plane_index: 2,
            default_plane_coordinate: 0.05,
            default_plane_units: "km",
            default_plane_method: "greatest_coherent_positive_w_times_ql_score",
            cloud_threshold_kg_kg: 1e-6,
            ...updraftScale,
            wind_target_level_m: 600,
            wind_actual_level_m: 580,
            wind_level_index: 1,
            wind_default_mode: "perturbation",
            wind_stride: 8,
            wind_shown_by_default: true,
            perturbation_wind_reference_m_s: 0.9,
            total_wind_reference_m_s: 8.8,
            wind_arrow_domain_fraction: 0.08,
            provenance: catalog.provenance,
            caveats: [],
          }),
        }),
    );
    await page.route(
      "**/api/results/result-baseline/visualization/trade-cumulus-updraft-lens/frame**",
      (route) => {
        const url = new URL(route.request().url());
        const windMode = url.searchParams.get("wind_mode") === "total" ? "total" : "perturbation";
        const orientation =
          url.searchParams.get("orientation") === "horizontal"
            ? "horizontal"
            : url.searchParams.get("orientation") === "vertical_y"
              ? "vertical_y"
              : "vertical_x";
        const planeIndex = Number(url.searchParams.get("plane_index") ?? 2);
        const timeIndex = Number(url.searchParams.get("time_index") ?? 1);
        const planeDimension =
          orientation === "horizontal" ? "z" : orientation === "vertical_y" ? "x" : "y";
        const dimensionOrder =
          orientation === "horizontal"
            ? ["y", "x"]
            : orientation === "vertical_y"
              ? ["z", "y"]
              : ["z", "x"];
        const wValues =
          orientation === "horizontal"
            ? [
                [-1.2, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, 5.2],
                [0, 0.1, 0.4, 0.2],
              ]
            : [
                [-1.2, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, 5.2],
                [0, 0.1, 0.4, 0.2],
              ];
        const finiteW = wValues.flat().filter((value): value is number => Number.isFinite(value));
        const lowClippedCount = finiteW.filter((value) => value < -1.0).length;
        const highClippedCount = finiteW.filter((value) => value >= 5.0).length;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            result_id: "result-baseline",
            time_index: timeIndex,
            time_seconds: [0, 1800, 3600][timeIndex] ?? 1800,
            orientation,
            plane_dimension: planeDimension,
            plane_index: planeIndex,
            plane_coordinate: [-0.15, -0.05, 0.05, 0.15][planeIndex] ?? 0.05,
            plane_units: "km",
            dimension_order: dimensionOrder,
            x_indices: [0, 1, 2, 3],
            x_values_km: [-0.15, -0.05, 0.05, 0.15],
            y_indices: [0, 1, 2, 3],
            y_values_km: [-0.15, -0.05, 0.05, 0.15],
            z_indices: [0, 1, 2, 3],
            z_values_km: [0.1, 0.3, 0.5, 0.7],
            w_values_m_s: wValues,
            cloud_mask: [
              [false, false, false, false],
              [false, true, true, false],
              [true, true, true, false],
              [false, true, false, false],
            ],
            cloud_threshold_kg_kg: 1e-6,
            ...updraftScale,
            w_finite_count: finiteW.length,
            w_low_clipped_count: lowClippedCount,
            w_high_clipped_count: highClippedCount,
            w_low_clipped_fraction: lowClippedCount / finiteW.length,
            w_high_clipped_fraction: highClippedCount / finiteW.length,
            wind_mode: windMode,
            wind_target_level_m: 600,
            wind_actual_level_m: 580,
            wind_level_index: 1,
            wind_stride: 8,
            wind_reference_m_s: windMode === "total" ? 8.8 : 0.9,
            wind_arrow_domain_fraction: 0.08,
            domain_mean_u_m_s: -8,
            domain_mean_v_m_s: 0,
            wind_vectors: [
              {
                x_km: 0,
                y_km: 0,
                z_km: 0.58,
                u_m_s: windMode === "total" ? -7.5 : 0.5,
                v_m_s: 0.2,
                magnitude_m_s: windMode === "total" ? 7.5 : 0.54,
              },
            ],
            provenance: catalog.provenance,
            caveats: [],
          }),
        });
      },
    );

    await page.reload();
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    const ordinaryTimeValue = await page.getByRole("combobox", { name: "Time" }).inputValue();
    const viewMode = page.getByLabel("Explore view mode");
    await expect(viewMode).toBeVisible();
    const lensToggle = viewMode.getByRole("button", { name: "Updraft Lens" });
    await expect(lensToggle).toBeEnabled();
    await lensToggle.click();
    await expect(page.getByRole("heading", { name: "Updraft Lens" })).toBeVisible();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toBeVisible();
    await expect(page.getByLabel("Cloud boundary")).toBeChecked();
    await expect(page.getByRole("checkbox", { name: "Horizontal wind" })).toBeChecked();
    await expect(page.getByRole("button", { name: "Local departures" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel("Horizontal wind overlay legend")).toContainText(
      "0.9 m/s reference",
    );
    const inspectorLegend = page.getByLabel(/2-D inspector Vertical velocity \(w\), m\/s/);
    const viewerLegend = page.getByLabel(/3-D viewer Vertical velocity \(w\), m\/s/);
    await expect(inspectorLegend).toContainText("Vertical velocity (w), m/s");
    await expect(viewerLegend).toContainText("-0.1 to < 0.1");
    await expect(page.locator(".updraft-lens-scale-swatch")).toHaveCount(20);
    await expect(page.getByText("Slice maximum 5.20 m/s.")).toHaveCount(2);
    await expect(page.getByText("Slice minimum -1.20 m/s.")).toHaveCount(2);
    await expect(page.getByText(/Clipped in this slice/)).toHaveCount(0);
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("2");
    await expect(page.getByRole("button", { name: "Vertical x-z" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page.getByText("Updraft Lens slice: Vertical x-z slice at y = 0.05 km", { exact: true }),
    ).toBeVisible();
    await expect(page.getByLabel("Slice field")).toHaveCount(0);
    const scalarField = page.getByLabel("3-D scalar field", { exact: true });
    await expect(scalarField).toBeVisible();
    await scalarField.selectOption("qv");
    await expect(scalarField).toHaveValue("qv");
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("2");
    await expect(page.getByRole("img", { name: /y index 2/ })).toBeVisible();
    await page.getByLabel("Layer opacity").fill("0.45");
    await page.getByLabel("Point size").fill("14");
    await expect(page.getByLabel("Layer opacity")).toHaveValue("0.45");
    await expect(page.getByLabel("Point size")).toHaveValue("14");
    const sliceAspect = await page.locator(".updraft-lens-svg").evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return {
        declared: Number(element.getAttribute("data-domain-aspect")),
        rendered: bounds.width / bounds.height,
      };
    });
    expect(Math.abs(sliceAspect.declared - sliceAspect.rendered)).toBeLessThan(0.03);

    await page.getByRole("button", { name: "Horizontal x-y" }).click();
    await expect(
      page.getByRole("img", { name: /Updraft Lens horizontal x-y slice/ }),
    ).toBeVisible();
    await expect(page.getByText(/Updraft Lens slice: Horizontal x-y layer at z =/)).toBeVisible();
    await page.getByRole("button", { name: "Vertical y-z" }).click();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical y-z slice/ })).toBeVisible();
    await expect(page.getByText(/Updraft Lens slice: Vertical y-z slice at x =/)).toBeVisible();
    await page.getByRole("button", { name: "Vertical x-z" }).click();
    await expect(page.getByRole("img", { name: /Updraft Lens vertical x-z slice/ })).toBeVisible();

    await page.getByLabel("Updraft Lens slice position").fill("3");
    await expect(page.getByLabel("Updraft Lens slice position")).toHaveValue("3");
    await expect(page.getByRole("img", { name: /y index 3/ })).toBeVisible();
    await expect(
      page.getByText("Updraft Lens slice: Vertical x-z slice at y = 0.15 km", { exact: true }),
    ).toBeVisible();
    await page.getByRole("combobox", { name: "Time" }).selectOption({ label: "3,600 s" });
    await expect(
      page.getByText("Vertical x-z slice at y = 0.15 km · w · 3,600 s", { exact: true }),
    ).toBeVisible();
    await expect(inspectorLegend).toContainText("Vertical velocity (w), m/s");
    await expect(inspectorLegend).toContainText(">= 5.0");

    await page.getByRole("button", { name: "Total wind" }).click();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toContainText(
      "8.8 m/s reference",
    );
    await page.getByLabel("Cloud boundary").uncheck();
    await expect(page.getByTestId("updraft-lens-cloud-boundary")).toHaveCount(0);
    await page.getByRole("checkbox", { name: "Horizontal wind" }).uncheck();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await viewMode.getByRole("button", { name: "Standard" }).click();
    await expect(page.getByRole("heading", { name: "Inspect the current slice" })).toBeVisible();
    await expect(page.getByLabel("Slice field")).toBeVisible();
    await expect(page.getByRole("combobox", { name: "Time" })).toHaveValue(ordinaryTimeValue);
  });

  test("Unified Explore plays through saved output times", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByLabel("Explore viewer controls")).toBeVisible();
    await expect(page.getByLabel("Timelapse playback controls")).toBeVisible();
    const playbackButton = page.getByLabel("Timelapse playback controls").getByRole("button");
    await expect(playbackButton).toHaveText("Play time");
    await expect(page.getByLabel("Playback speed")).toHaveValue("1");
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();

    await page.locator("#explore-time").selectOption("1");
    await page.getByLabel("Playback speed").selectOption("0.5");
    await playbackButton.click();

    await expect(playbackButton).toHaveText("Pause time");
    await expect(playbackButton).toHaveAttribute("aria-pressed", "true");
    await expect(
      page.getByText("Pause playback to select a cell and explain this time step."),
    ).toBeVisible();
    await expect(
      page.getByText(
        /Animating 3-D scene at .*; slice and evidence remain at .* until playback is paused\./,
      ),
    ).toBeVisible();
    await expect(page.locator("#explore-time")).toHaveValue("2", { timeout: 4_000 });
    await expect(playbackButton).toHaveText("Play time", { timeout: 4_000 });
    await expect(playbackButton).toHaveAttribute("aria-pressed", "false");
    await expect(page.locator("#explore-time")).toHaveValue("0");

    await page.getByRole("button", { name: "Last frame" }).click();
    await expect(page.locator("#explore-time")).toHaveValue("2");
    await playbackButton.click();
    await expect(page.locator("#explore-time")).toHaveValue("0", { timeout: 4_000 });
    await expect(playbackButton).toHaveText("Play time");
    await expect(playbackButton).toHaveAttribute("aria-pressed", "false");
  });

  test("Explore process evidence offers useful modes and moves unsupported modes secondary", async ({
    page,
  }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/what happened in this result/i).first()).toBeVisible({
      timeout: 10_000,
    });
    await page.getByText("Process evidence details").click();

    const processMode = page.getByLabel("Process mode");
    await expect(processMode).toBeVisible();
    await expect(processMode.locator("option", { hasText: "Thermal Fate summary" })).toHaveCount(1);
    await expect(processMode.locator("option", { hasText: "Cloud Water" })).toHaveCount(1);
    await expect(processMode.locator("option", { hasText: "Updrafts" })).toHaveCount(1);
    await expect(processMode.locator("option", { hasText: "Moisture" })).toHaveCount(0);
    await expect(processMode.locator("option", { hasText: "Buoyancy" })).toHaveCount(0);
    await expect(processMode.locator("option", { hasText: "Deep Breakthrough" })).toHaveCount(0);
    await expect(processMode.locator("option", { hasText: "Precipitation Feedback" })).toHaveCount(
      0,
    );

    await page.getByText("Not available for this result").click();
    await expect(page.getByText("Moisture / Saturation", { exact: true })).toBeVisible();
    await expect(page.getByText("Deep Breakthrough", { exact: true })).toBeVisible();
    await expect(page.getByText(/missing required CM1 fields/i)).toBeVisible();
  });

  test("Results to Explore loads cloud-forming qc and w fields", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/slice synced/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#explore-slice-field")).toHaveValue("qc");
    await expect(
      page.locator("#explore-slice-field option", { hasText: "qc - Cloud water" }),
    ).toHaveCount(1);
    await expect(
      page.locator("#explore-slice-field option", {
        hasText: "w - Vertical velocity (slice only)",
      }),
    ).toHaveCount(1);
    await expect(page.getByText(/loading fields/i)).not.toBeVisible();

    await expect(page.getByText(/cloud-water point layer loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.getByText(/cloud-water point layer/i).first()).toBeVisible();
  });

  test("Explore exposes expanded 3-D scalar fields without promoting slice-only fields", async ({
    page,
  }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/cloud-water point layer loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    const threeDField = page.locator("#explore-3d-field");
    await expect(threeDField).toBeVisible();
    await expect(threeDField.locator("option", { hasText: "qc - Cloud water" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "qr - Rain water" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "qv - Water vapor" })).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "dbz - Reflectivity" })).toHaveCount(1);
    await expect(
      threeDField.locator("option", { hasText: "rain - Accumulated surface rain" }),
    ).toHaveCount(1);
    await expect(threeDField.locator("option", { hasText: "temperature" })).toHaveCount(0);
    await expect(threeDField.locator("option", { hasText: "theta" })).toHaveCount(0);
    await expect(threeDField.locator("option", { hasText: "Vertical velocity" })).toHaveCount(0);

    await threeDField.selectOption("qr");
    await expect(page.getByText("Rain-water point layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("qr");

    await threeDField.selectOption("qv");
    await expect(page.getByText("Water-vapor point layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("qv");

    await threeDField.selectOption("dbz");
    await expect(page.getByText("Reflectivity point layer loaded").first()).toBeVisible();
    const threeDLegend = page.getByLabel("3-D field color legend");
    await expect(threeDLegend.getByText("0 dBZ")).toBeVisible();
    await expect(threeDLegend.getByText("60+ dBZ")).toBeVisible();

    await threeDField.selectOption("rain");
    await expect(page.getByText("Surface-rain floor layer loaded").first()).toBeVisible();
    await expect(page.locator("#explore-slice-field")).toHaveValue("rain");
    await expect(page.getByRole("button", { name: "Vertical x-z slice" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Vertical y-z slice" })).toBeDisabled();
  });

  test("Results to Explore treats Dry Failed as no-cloud with updraft inspection", async ({
    page,
  }) => {
    await gotoResults(page);
    await page
      .getByRole("article", { name: "Dry Failed Cumulus — Quick Look experiment" })
      .getByRole("button", { name: "Open in Explore" })
      .click();

    await expect(page.getByText("Dry Failed Cumulus — Quick Look").first()).toBeVisible();
    await expect(page.getByText(/No cloud water formed in this result/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.getByText(/No cloud water formed in this result; vertical velocity is available/i),
    ).toBeVisible();
    await expect(page.getByText("No cloud formed in this result")).toBeVisible();
    await expect(page.getByText("No cloud formed here")).toHaveCount(0);

    await expect(page.getByText(/slice synced/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.locator("#explore-slice-field option", {
        hasText: "w - Vertical velocity (slice only)",
      }),
    ).toHaveCount(1);
  });

  test("Explore field loading failure shows an error and retry instead of a stuck spinner", async ({
    page,
  }) => {
    await page.route("**/api/results/*/visualization/fields", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Visualization fields temporarily failed." }),
      }),
    );

    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByRole("alert")).toContainText("Visualization fields temporarily failed.");
    await expect(page.getByRole("button", { name: "Retry loading fields" })).toBeVisible();
    await expect(page.getByText("Loading fields...", { exact: true })).not.toBeVisible();
  });

  test("Explore mobile puts visualization and explanation before technical controls", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/Horizontal layer at z = /i).first()).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByLabel("Slice position")).toBeVisible();
    const heatmap = page.getByRole("img", { name: /heatmap/i });
    await expect(heatmap).toBeVisible({ timeout: 10_000 });

    const heatmapPrecedesTechnicalDetails = await heatmap.evaluate((element) => {
      const technicalSummary = Array.from(document.querySelectorAll("summary")).find((summary) =>
        summary.textContent?.includes("Technical slice details"),
      );
      return Boolean(
        technicalSummary &&
        element.compareDocumentPosition(technicalSummary) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(heatmapPrecedesTechnicalDetails).toBe(true);

    const scene = page.getByLabel("True 3-D scalar field viewer");
    const explanation = page.getByLabel("Visualization details");
    await expect(scene).toBeVisible({ timeout: 12_000 });
    await expect(explanation).toBeVisible();
    const scenePrecedesExplanation = await scene.evaluate((element) => {
      const details = document.querySelector('[aria-label="Visualization details"]');
      return Boolean(
        details && element.compareDocumentPosition(details) & Node.DOCUMENT_POSITION_FOLLOWING,
      );
    });
    expect(scenePrecedesExplanation).toBe(true);
  });
});

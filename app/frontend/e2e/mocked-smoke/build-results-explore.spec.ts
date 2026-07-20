import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, openRunMonitor } from "../helpers";
import { mockCloudChamberApis, results } from "../fixtures";

test.describe("mocked smoke: Build, Results, Explore path", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
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
    expect(Math.abs(heatmapLayout.declaredAspect - heatmapLayout.renderedAspect)).toBeLessThan(0.03);
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
            w_range_min_m_s: -0.9,
            w_range_max_m_s: 0.9,
            w_range_method: "all_frames_p99_absolute_centered_w",
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
                [-0.9, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, null],
                [0, 0.1, 0.4, 0.2],
              ]
            : [
                [-0.9, -0.4, 0.2, 0.6],
                [-0.5, 0, 0.5, 0.9],
                [-0.2, 0.3, 0.7, null],
                [0, 0.1, 0.4, 0.2],
              ];
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
            w_range_min_m_s: -0.9,
            w_range_max_m_s: 0.9,
            w_range_method: "fixed",
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
    await expect(page.getByLabel("Vertical velocity color scale")).toContainText("0.9 m/s");
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
    await expect(page.getByLabel("Vertical velocity color scale")).toContainText("-0.9");
    await expect(page.getByLabel("Vertical velocity color scale")).toContainText("0.9 m/s");

    await page.getByRole("button", { name: "Total wind" }).click();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toContainText(
      "8.8 m/s reference",
    );
    await page.getByLabel("Cloud boundary").uncheck();
    await expect(page.getByTestId("updraft-lens-cloud-boundary")).toHaveCount(0);
    await page.getByRole("checkbox", { name: "Horizontal wind" }).uncheck();
    await expect(page.getByLabel("Horizontal wind overlay legend")).toHaveCount(0);
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
    await expect(page.getByRole("button", { name: "Play time" })).toBeVisible();
    await expect(page.getByLabel("Playback speed")).toHaveValue("1");
    await expect(page.getByRole("slider", { name: "Saved output time" })).toBeVisible();

    await page.locator("#explore-time").selectOption("1");
    await page.getByLabel("Playback speed").selectOption("2");
    await page.getByRole("button", { name: "Play time" }).click();

    await expect(page.getByRole("button", { name: "Pause time" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page.getByText("Pause playback to select a cell and explain this time step."),
    ).toBeVisible();
    await expect(
      page.getByText(
        /Animating 3-D scene at .*; slice and evidence remain at .* until playback is paused\./,
      ),
    ).toBeVisible();
    await expect(page.locator("#explore-time")).toHaveValue("2", { timeout: 2_000 });

    await page.getByRole("button", { name: "Pause time" }).click();
    await expect(page.getByRole("button", { name: "Play time" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await page.getByRole("button", { name: "Last frame" }).click();
    await expect(page.locator("#explore-time")).toHaveValue("2");
    await page.getByRole("button", { name: "Play time" }).click();
    await expect(page.locator("#explore-time")).toHaveValue("0", { timeout: 2_000 });
    await expect(page.getByRole("button", { name: "Play time" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
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

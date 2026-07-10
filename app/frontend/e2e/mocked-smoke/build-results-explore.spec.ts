import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

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
    await expect(page.getByText(/physical question/i).first()).toBeVisible();
    await expect(page.getByText(/how do low-level moisture/i).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Local run launchpad" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Packages and runs needing action" })).toBeVisible();
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

  test("Build can review an observed IGRA sounding before package creation", async ({
    page,
  }) => {
    await gotoBuild(page);

    await page.getByLabel("Experiment", { exact: true }).selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Upload a Sounding" })).toBeVisible();
    await expect(page.getByText("Observed sounding profile, Surface heating")).toBeVisible();
    await expect(page.getByLabel("Low-level humidity")).not.toBeVisible();
    await expect(page.getByLabel("Surface heating")).toBeEnabled();
    await expect(page.getByLabel("Use uploaded sounding")).not.toBeVisible();

    await page.getByLabel("IGRA station sounding-data file").setInputFiles({
      name: "USM00072558-data.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("#USM00072558 2025 01 02 00"),
    });

    await expect(page.getByText("Observed sounding validated for package review")).toBeVisible();
    await expect(page.getByText("USM00072558 · Valley, Nebraska")).toBeVisible();
    await expect(page.locator("#observed-sounding-time")).toHaveValue("2025-01-02T00:00:00Z");
    await expect(page.getByText(/CM1 z=0 is station surface at 351.5 m MSL/i)).toBeVisible();
    await expect(page.getByText(/generated CM1 namelist uses isnd=7/i)).toBeVisible();

    await page.getByText("Observed-sounding caveats").click();
    await expect(page.getByText("Station elevation joined from igra station fixture")).toBeVisible();

    await page.getByTestId("create-package-btn").scrollIntoViewIfNeeded();
    await page.getByTestId("create-package-btn").click();

    await expect(page.getByText("Package ready").first()).toBeVisible();
    await expect(page.getByText("/tmp/cloud-chamber-e2e/run/run_manifest.json")).toBeVisible();
  });

  test("Build can screen, save, and use observed sounding candidates", async ({ page }) => {
    await gotoBuild(page);

    await page.getByLabel("Experiment", { exact: true }).selectOption("__observed_sounding_upload__");
    await expect(page.getByRole("heading", { name: "Find interesting soundings" })).toBeVisible();
    await expect(page.getByText(/Screening guidance only/i).first()).toBeVisible();
    await expect(page.getByText("IGRA cache not checked yet")).toBeVisible();

    await page.getByRole("button", { name: "Refresh IGRA catalog" }).click();
    await expect(page.getByText("IGRA station catalog refreshed")).toBeVisible();
    await expect(page.getByText("Screenable soundings").locator("..")).toContainText("2 soundings");

    await page.getByRole("button", { name: "Cache station files" }).click();
    await expect(page.getByText("Cached 1 station file")).toBeVisible();

    await page.getByLabel("Story filter").selectOption("shallow_cumulus_candidate");
    await page.getByRole("button", { name: "Analyze cached soundings" }).click();

    await expect(page.getByText("Cached sounding analysis loaded")).toBeVisible();
    const valleyCard = page.getByLabel("Sounding candidate Valley, Nebraska (USM00072558)");
    await expect(valleyCard).toBeVisible();
    await expect(valleyCard).toContainText("Cloud-forming shallow cumulus");
    await expect(valleyCard).toContainText("Package-ready");
    await expect(valleyCard).toContainText("Low-level moisture: 10.2 g/kg");
    await expect(page.getByLabel("Candidate details")).toContainText(
      "Candidate match score is screening guidance only",
    );

    await page.getByLabel("Story filter").selectOption("needs_review");
    await page.getByRole("button", { name: "Analyze cached soundings" }).click();
    const blockedCard = page.getByLabel("Sounding candidate Norman, Oklahoma (USM00072357)");
    await expect(blockedCard).toBeVisible();
    await expect(blockedCard).toContainText("Blocked");
    await expect(blockedCard.getByRole("button", { name: "Use this sounding" })).toBeDisabled();

    await page.getByLabel("Story filter").selectOption("all");
    await page.getByRole("button", { name: "Analyze cached soundings" }).click();
    await valleyCard.getByRole("button", { name: "Save candidate" }).click();
    await expect(page.getByText("Sounding candidate saved")).toBeVisible();
    await expect(
      page.getByLabel("Saved sounding candidate Valley, Nebraska (USM00072558)"),
    ).toBeVisible();

    await valleyCard.getByRole("button", { name: "Use this sounding" }).click();
    await expect(page.getByText("Candidate selected for package review")).toBeVisible();
    await expect(page.getByText("Candidate loaded into observed-sounding package review")).toBeVisible();
    await expect(page.getByText("USM00072558 · Valley, Nebraska")).toBeVisible();
    await expect(page.getByText(/Screened as Cloud-forming shallow cumulus/i)).toBeVisible();

    await page.getByTestId("create-package-btn").scrollIntoViewIfNeeded();
    await page.getByTestId("create-package-btn").click();
    await expect(page.getByText("Package ready").first()).toBeVisible();
  });

  test("Results notebook renders with mocked data", async ({ page }) => {
    await gotoResults(page);

    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    const resultsList = page.getByLabel("Results list");
    await expect(resultsList).toBeVisible();
    await expect(page.getByText("Baseline Shallow Cumulus — Quick Look").first()).toBeVisible();
    await expect(
      resultsList.getByText(/Cloud water formed in the validated quick-look baseline/i),
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
    await expect(resultsList.getByText("Observed sounding: USM00072558 · Valley, Nebraska")).toBeVisible();
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

  test("Results deletes ingested results and Build keeps non-ingested cleanup", async ({ page }) => {
    await gotoResults(page);

    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByRole("button", { name: "Preview delete result and local run data" }).click();
    await expect(page.getByRole("heading", { name: "Delete result and local run data preview" })).toBeVisible();
    await expect(page.getByText(/result will disappear from Results, Explore, and local inventory/)).toBeVisible();
    await expect(page.getByText("Result metadata and notebook edits")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Delete result and local run data", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Delete result and local run data", exact: true }).click();
    await expect(
      page.getByRole("status").filter({ hasText: /Result and local run data deleted/ }),
    ).toBeVisible();
    await expect(page.getByLabel("Results list").getByText("Baseline Shallow Cumulus — Quick Look")).toHaveCount(0);

    await gotoBuild(page);
    const pipelineRuns = page.getByLabel("Local packages and runs");
    const ingestReadyRun = pipelineRuns.locator("article", { hasText: "dry-run-disposable" });
    await expect(ingestReadyRun.getByText("Ready to ingest")).toBeVisible();
    await expect(ingestReadyRun.getByRole("button", { name: "Preview cleanup" })).toBeEnabled();
    await ingestReadyRun.getByRole("button", { name: "Preview cleanup" }).click();
    await expect(page.getByRole("heading", { name: "Delete local package/run data preview" })).toBeVisible();
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
      resultsList.getByText(/Cloud water formed in the validated quick-look baseline/i),
    ).toBeVisible();
    await expect(page.getByLabel("Result detail")).toBeVisible();
    await expect(page.getByRole("button", { name: "Open in Explore" }).first()).toBeVisible();
  });

  test("Unified Explore renders cloud context, slice inspector, and explanation", async ({ page }) => {
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
    const fieldControlsPrecedeHeatmap = await heatmap.evaluate((element) => {
      const fieldControl = document.querySelector("#explore-slice-field");
      return Boolean(
        fieldControl &&
          (fieldControl.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING),
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
      page.getByText(/Animating 3-D scene at .*; slice and evidence remain at .* until playback is paused\./),
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
    await expect(processMode.locator("option", { hasText: "Thermal Fate summary" })).toHaveCount(
      1,
    );
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
    await expect(page.locator("#explore-slice-field option", { hasText: "qc - Cloud water" })).toHaveCount(
      1,
    );
    await expect(
      page.locator("#explore-slice-field option", { hasText: "w - Vertical velocity (slice only)" }),
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
      page.locator("#explore-slice-field option", { hasText: "w - Vertical velocity (slice only)" }),
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

    await expect(page.getByRole("alert")).toContainText(
      "Visualization fields temporarily failed.",
    );
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
          (element.compareDocumentPosition(technicalSummary) & Node.DOCUMENT_POSITION_FOLLOWING),
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

import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, openResultsTab } from "../helpers";
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
    await expect(page.getByRole("heading", { name: "Packages, runs, and results" })).toBeVisible();
    await expect(
      page.getByTestId("package-review-panel").getByText("Not packaged yet").first(),
    ).toBeVisible();
    await expect(page.getByText("Local experiment pipeline")).toBeVisible();
    await expect(page.getByText("Ready to ingest")).toBeVisible();
    await expect(page.getByRole("button", { name: "Open Storage cleanup" })).toBeVisible();
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
    await expect(page.getByText("Completed").first()).toBeVisible();
    await expect(page.getByTestId("ingest-results-btn")).toBeEnabled();

    await page.getByTestId("ingest-results-btn").click();
    await expect(page.getByText("Ingested").first()).toBeVisible();
    await page.getByRole("button", { name: "Open in Results" }).click();
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
  });

  test("Results notebook, Compare, and Storage render with mocked data", async ({ page }) => {
    await gotoResults(page);

    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    const resultsList = page.getByLabel("Results list");
    await expect(resultsList).toBeVisible();
    await expect(page.getByText("Baseline Shallow Cumulus — Quick Look").first()).toBeVisible();
    await expect(
      resultsList.getByText(/Cloud water formed in the validated quick-look baseline/i),
    ).toBeVisible();
    await expect(page.getByText("Cloud formed").first()).toBeVisible();
    await expect(page.getByText("Rain detected").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Open in Explore" }).first()).toBeVisible();
    const resultDetail = page.getByLabel("Result detail");
    await resultDetail.getByText("Technical details").click();
    await expect(resultDetail.getByText("Run ID")).toBeVisible();
    await expect(resultDetail.getByText("Product state")).toBeVisible();

    await openResultsTab(page, /^Compare$/);
    await expect(
      page.getByRole("heading", { name: "Baseline vs Dry Failed Cumulus" }),
    ).toBeVisible();
    await expect(page.getByText("Moisture-limited", { exact: true })).toBeVisible();

    await openResultsTab(page, /^Storage$/);
    await expect(page.getByRole("heading", { name: "Runtime storage cleanup" })).toBeVisible();
    await expect(page.getByText("/tmp/cloud-chamber-e2e").first()).toBeVisible();
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
    await expect(page.getByLabel("Shared Explore controls")).toBeVisible();
    await expect(page.getByLabel("3-D scene container")).toBeVisible({ timeout: 12_000 });
    await expect(page.getByRole("heading", { name: "Inspect the current slice" })).toBeVisible();
    await expect(page.getByText(/Horizontal layer at z = /i).first()).toBeVisible();
    await expect(page.getByLabel("Slice position")).toBeVisible();
    await expect(page.getByRole("button", { name: /move down/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /move up/i })).toBeVisible();
    await expect(page.getByText(/what happened here/i).first()).toBeVisible();
    await expect(page.getByText(/click a slice cell to inspect that point/i).first()).toBeVisible();
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
    await expect(page.getByText(/selected-point diagnostics loaded/i)).toBeVisible();
    await expect(page.getByText(/cloud water appeared locally/i)).toBeVisible();
    await expect(page.getByText(/local max w/i)).toBeVisible();
    await page.getByText("Technical slice details").first().click();
    await expect(page.getByText(/finite values/i).first()).toBeVisible();
    await expect(page.getByText(/\[\[[\d.,\s]+\]\]/)).not.toBeVisible();

    await expect(page.getByText("Cloud formed in this result")).toBeVisible();
    await expect(page.getByText("Cloud formed here")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /reset view/i })).toBeVisible();
    const visualizerControls = page.getByLabel("Shared Explore controls");
    await expect(visualizerControls.getByRole("button", { name: /oblique/i })).toBeVisible();
    await expect(visualizerControls.getByRole("button", { name: /side x-?z/i })).toBeVisible();
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
      page.locator("#explore-slice-field option", { hasText: "w - Vertical velocity" }),
    ).toHaveCount(1);
    await expect(page.getByText(/loading fields/i)).not.toBeVisible();

    await expect(page.getByText(/cloud-water point cloud loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.getByText(/cloud-water point cloud/i).first()).toBeVisible();
  });

  test("Results to Explore treats Dry Failed as no-cloud with updraft inspection", async ({
    page,
  }) => {
    await gotoResults(page);
    await openResultsTab(page, /^Compare$/);
    await page.getByRole("button", { name: "Open Dry Failed in Explore" }).click();

    await expect(page.getByText("Dry Failed Cumulus — Quick Look").first()).toBeVisible();
    await expect(page.getByText(/No cloud water formed in this result/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.getByText(/No cloud water formed in this result; vertical velocity is available/i),
    ).toBeVisible();
    await expect(
      page.getByText(/Use the vertical velocity field \(w\) to inspect the thermals/i),
    ).toBeVisible();
    await expect(page.getByText("No cloud formed in this result")).toBeVisible();
    await expect(page.getByText("No cloud formed here")).toHaveCount(0);

    await expect(page.getByText(/slice synced/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#explore-slice-field")).toHaveValue("w");
    await expect(
      page.locator("#explore-slice-field option", { hasText: "w - Vertical velocity" }),
    ).toHaveCount(1);
  });

  test("Explore field loading failure shows an error and retry instead of a stuck spinner", async ({
    page,
  }) => {
    await page.route("**/api/results/result-baseline/visualization/fields", (route) =>
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
    await expect(page.getByLabel("What happened here panel")).toBeVisible();
    await expect(page.getByLabel("What happened here panel")).toContainText(/what happened here/i);

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

    const scene = page.getByLabel("3-D scene container");
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

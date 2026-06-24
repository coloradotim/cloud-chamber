import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, openExploreTab, openResultsTab } from "../helpers";
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
    await expect(page.getByText(/preview estimate not implemented/i)).toBeVisible();

    await page.getByTestId("create-package-btn").scrollIntoViewIfNeeded();
    await page.getByTestId("create-package-btn").click();

    await expect(page.getByTestId("package-review-panel")).toBeVisible();
    await expect(page.getByText("/tmp/cloud-chamber-e2e/run/run_manifest.json")).toBeVisible();
    await expect(page.getByText("CM1 launched").locator("..")).toContainText("No");
    await expect(page.getByText(/not a completed|dry-run/i).first()).toBeVisible();
    await expect(page.getByTestId("launch-cm1-btn")).toBeEnabled();
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
    await expect(page.getByRole("button", { name: "Open 3-D" }).first()).toBeVisible();
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

  test("Explore 2-D and 3-D views render from the selected result", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByRole("heading", { name: "Inspect and visualize fields" })).toBeVisible();

    await openExploreTab(page, /^2-D Slices$/);
    await expect(page.getByText(/inspect cm1 fields/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/2-d field inspection/i).first()).toBeVisible();
    await expect(page.getByText(/thermal fate overlay/i).first()).toBeVisible();
    await expect(page.getByText(/growing cumulus/i).first()).toBeVisible();
    await expect(page.getByText(/what happened here/i).first()).toBeVisible();
    await page
      .getByRole("button", { name: /inspect vertical x slice row 2, column 2/i })
      .first()
      .click();
    await expect(page.getByText(/selected-region diagnostics loaded/i)).toBeVisible();
    await expect(page.getByText(/cloud water appeared locally/i)).toBeVisible();
    await expect(page.getByText(/local max w/i)).toBeVisible();
    await page.getByRole("button", { name: /clear selection/i }).click();
    await expect(page.getByText(/no region is selected/i)).toBeVisible();
    await expect(page.getByText(/\[\[[\d.,\s]+\]\]/)).not.toBeVisible();

    await openExploreTab(page, /^3-D View$/);
    await expect(page.getByText(/scene shell/i).first()).toBeVisible({ timeout: 12_000 });
    await expect(page.getByText(/oblique overview/i).first()).toBeVisible();
    await expect(page.getByText(/thermal fate overlay/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /reset view/i })).toBeVisible();
  });

  test("Results to Explore loads cloud-forming qc and w fields", async ({ page }) => {
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await openExploreTab(page, /^2-D Slices$/);
    await expect(page.getByText(/slices loaded/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#inspect-field")).toHaveValue("qc");
    await expect(page.locator("#inspect-field option", { hasText: "qc - Cloud water" })).toHaveCount(
      1,
    );
    await expect(
      page.locator("#inspect-field option", { hasText: "w - Vertical velocity" }),
    ).toHaveCount(1);
    await expect(page.getByText(/loading fields/i)).not.toBeVisible();

    await openExploreTab(page, /^3-D View$/);
    await expect(page.getByText(/cloud-water point cloud loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.locator("#scene-field")).toHaveValue("qc");
    await expect(page.getByText(/cloud-water point cloud/i).first()).toBeVisible();
  });

  test("Results to Explore treats Dry Failed as no-cloud with updraft inspection", async ({
    page,
  }) => {
    await gotoResults(page);
    await openResultsTab(page, /^Compare$/);
    await page.getByRole("button", { name: "Open Dry Failed 3-D" }).click();

    await expect(page.getByRole("heading", { name: "Inspect and visualize fields" })).toBeVisible();
    await expect(page.getByText("Dry Failed Cumulus — Quick Look").first()).toBeVisible();
    await expect(page.getByText(/scene shell ready/i).first()).toBeVisible({ timeout: 12_000 });
    await expect(page.locator("#scene-field")).toHaveValue("w");
    await expect(
      page.getByText(/No cloud water formed here; vertical velocity is available/i),
    ).toBeVisible();
    await expect(
      page.getByText(/Use the vertical velocity field \(w\) to inspect the thermals/i),
    ).toBeVisible();

    await openExploreTab(page, /^2-D Slices$/);
    await expect(page.getByText(/slices loaded/i).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("#inspect-field")).toHaveValue("w");
    await expect(
      page.locator("#inspect-field option", { hasText: "w - Vertical velocity" }),
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
    await openExploreTab(page, /^2-D Slices$/);

    await expect(page.getByRole("alert")).toContainText(
      "Visualization fields temporarily failed.",
    );
    await expect(page.getByRole("button", { name: "Retry loading fields" })).toBeVisible();
    await expect(page.getByText("Loading fields...", { exact: true })).not.toBeVisible();
  });
});

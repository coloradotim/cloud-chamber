import { expect, test } from "@playwright/test";

import { collectConsoleProblems, gotoApp } from "../helpers";
import { mockCloudChamberApis, mockMountainWavesProductPath } from "../fixtures";

test.describe("mocked smoke: Mountain Waves product path", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1728, height: 1000 });
    await mockCloudChamberApis(page);
  });

  test("retains a variation from Cloud Worlds through Explore and another parent", async ({
    page,
  }) => {
    await mockMountainWavesProductPath(page);
    const consoleProblems = collectConsoleProblems(page);

    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Mountain Waves" }).click();
    await expect(page.getByRole("heading", { name: "Mountain Waves" })).toBeVisible();

    const reference = page.locator("article", { hasText: "Boulder Windstorm" });
    await reference.getByRole("button", { name: "Explore" }).click();
    await expect(page.getByRole("heading", { name: "Wave Cloud Lens" })).toBeVisible();
    await expect(page.getByLabel("Mountain Waves x-z view")).toBeVisible();
    await page.getByRole("button", { name: "Back to Mountain Waves" }).click();

    await page.getByRole("button", { name: "Lab" }).click();
    await expect(page.getByRole("heading", { name: /Change the terrain/ })).toBeVisible();
    await page.getByLabel("Variation name").fill("Broader Ridge");
    await page.getByLabel("Half-width").fill("11000");
    await expect(page.getByText("1 exact changes")).toBeVisible();
    await page.getByRole("button", { name: "Create and queue" }).click();

    await expect(page.getByText(/Queued · Waiting for the local CM1 runner/)).toBeVisible();
    await page.getByRole("button", { name: "Refresh" }).click();
    await expect(page.getByText(/Running · CM1 is running locally/)).toBeVisible();
    await page.getByRole("button", { name: "Refresh" }).click();
    await expect(page.getByRole("heading", { name: "Lab is idle" })).toBeVisible();

    await page.getByRole("button", { name: "History" }).click();
    const retained = page.locator("article", { hasText: "Broader Ridge" });
    await expect(retained.getByText(/Completed · CM1 completed normally/)).toBeVisible();
    await retained.getByRole("button", { name: "Explore" }).click();
    await expect(page.getByRole("heading", { name: "Wave Cloud Lens" })).toBeVisible();
    await page.getByRole("button", { name: "Back to Mountain Waves" }).click();

    await page.getByRole("button", { name: "Lab" }).click();
    await page.getByRole("button", { name: "History" }).click();
    await page
      .locator("article", { hasText: "Broader Ridge" })
      .getByRole("button", { name: "Create variation" })
      .click();
    await expect(page.getByLabel("Parent Simulation")).toHaveValue(
      "mountain_waves_broader_ridge_abcd1234",
    );
    expect(consoleProblems).toEqual([]);
  });

  test("keeps a package failure inside the Mountain Waves Lab", async ({ page }) => {
    await mockMountainWavesProductPath(page, { failPackage: true });

    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Mountain Waves" }).click();
    await page.getByRole("button", { name: "Lab" }).click();
    await page.getByLabel("Variation name").fill("Rejected Ridge");
    await page.getByLabel("Half-width").fill("11000");
    await page.getByRole("button", { name: "Create and queue" }).click();

    await expect(page.getByRole("alert")).toHaveText("Variation package preflight failed.");
    await expect(page.getByRole("heading", { name: /Change the terrain/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Mountain Waves" })).toBeVisible();
  });
});

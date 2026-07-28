import { expect, test } from "@playwright/test";

import { collectConsoleProblems, gotoApp } from "../helpers";
import { mockCloudChamberApis, mockMountainWavesProductPath } from "../fixtures";

test.describe("mocked smoke: Mountain Waves product path", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1728, height: 1000 });
    await mockCloudChamberApis(page);
  });

  test("retains shared Activity and History after creating a variation", async ({
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

    await page.getByRole("button", { name: "Create Variation", exact: true }).click();
    await expect(page.getByRole("heading", { name: /Change the terrain/ })).toBeVisible();
    await page.getByLabel("Variation name").fill("Broader Ridge");
    await page.getByLabel("Half-width").fill("11000");
    await expect(page.getByText("1 exact change")).toBeVisible();
    await page.getByRole("button", { name: "Create and queue" }).click();

    await expect(page.getByRole("heading", { name: "Current work" })).toBeVisible();
    await expect(page.locator("article", { hasText: "Broader Boulder Ridge" })).toBeVisible();

    await page.getByRole("button", { name: "History" }).click();
    await expect(page.getByRole("heading", { name: "Retained scientific work" })).toBeVisible();
    const retained = page.locator("article", { hasText: "Broader Ridge" });
    await expect(retained.locator(".lifecycle-badge")).toHaveText("Available");
    await retained.getByText("Technical details").click();
    await expect(retained.getByRole("region", { name: "Technical attempts" })).toContainText(
      "Later backing candidate",
    );

    expect(consoleProblems).toEqual([]);
  });

  test("keeps a package failure inside Mountain Waves Create Variation", async ({ page }) => {
    await mockMountainWavesProductPath(page, { failPackage: true });

    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Mountain Waves" }).click();
    await page.getByRole("button", { name: "Create Variation", exact: true }).click();
    await page.getByLabel("Variation name").fill("Rejected Ridge");
    await page.getByLabel("Half-width").fill("11000");
    await page.getByRole("button", { name: "Create and queue" }).click();

    await expect(page.getByRole("alert")).toHaveText("Variation package preflight failed.");
    await expect(page.getByRole("heading", { name: /Change the terrain/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Mountain Waves" })).toBeVisible();
  });
});

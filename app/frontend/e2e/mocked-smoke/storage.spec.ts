import { expect, test } from "@playwright/test";

import { mockCloudChamberApis } from "../fixtures";
import { collectConsoleProblems } from "../helpers";

test.describe("mocked smoke: global Storage", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
  });

  test("opens from global navigation and returns Home", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Storage" }).click();
    await expect(page).toHaveURL(/\/storage$/);
    await expect(page.getByRole("heading", { name: "Storage" })).toBeVisible();

    await page.getByRole("button", { name: "Home" }).click();
    await expect(page).toHaveURL("/");
  });

  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 1024, height: 856 },
  ]) {
    test(`keeps inventory and launch planning usable at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      const consoleProblems = collectConsoleProblems(page);
      await page.setViewportSize(viewport);
      await page.goto("/storage");

      await expect(page.getByRole("heading", { name: "Storage" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Retained locally" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Launch budget" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Retained assets" })).toBeVisible();
      await expect(page.getByText("Usage warning")).toBeVisible();
      await expect(page.getByText("Quarter-Circle Supercell")).toBeVisible();
      await expect(page.getByText("Boulder Windstorm")).toBeVisible();
      await expect(page.getByRole("button", { name: /delete|remove|clean/i })).toHaveCount(0);

      const bodyMetrics = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(bodyMetrics.scrollWidth).toBeLessThanOrEqual(bodyMetrics.clientWidth + 1);

      await page.getByRole("searchbox", { name: "Search" }).fill("Boulder");
      await expect(page.getByText("1 of 3")).toBeVisible();
      await expect(page.getByText("Boulder Windstorm")).toBeVisible();
      await expect(page.getByText("Quarter-Circle Supercell")).toHaveCount(0);

      await page.getByRole("searchbox", { name: "Search" }).fill("");
      await page.getByText("More filters").click();
      await page.getByRole("combobox", { name: "Attempt lifecycle" }).selectOption("canceled");
      await expect(page.getByText("Boulder Windstorm")).toBeVisible();
      await expect(page.getByText("Quarter-Circle Supercell")).toHaveCount(0);
      await page.getByRole("combobox", { name: "Attempt lifecycle" }).selectOption("all");
      await page.getByRole("combobox", { name: "Trust" }).selectOption("trusted");
      await expect(page.getByText("Quarter-Circle Supercell")).toBeVisible();
      await expect(page.getByText("Boulder Windstorm")).toHaveCount(0);
      await page.getByRole("combobox", { name: "Trust" }).selectOption("all");
      await page
        .getByRole("combobox", { name: "World run profile" })
        .selectOption("supercells_extended_v1");
      const launchBudget = page.locator(".storage-budget");
      await expect(
        launchBudget.getByText("Uncharacterized", { exact: true }).first(),
      ).toBeVisible();
      await expect(page.locator(".storage-disposition")).toHaveText("blocked");

      await page.screenshot({
        path: testInfo.outputPath(`storage-${viewport.width}x${viewport.height}.png`),
        fullPage: true,
      });
      expect(consoleProblems).toEqual([]);
    });
  }

  test("records and immediately rechecks a passing launch budget", async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/storage");
    await page.getByRole("button", { name: "Record budget review" }).click();
    await expect(page.getByText(/Planning snapshot 11111111/)).toBeVisible();
    await page.getByRole("button", { name: "Recheck current budget" }).click();
    await expect(page.getByRole("status")).toHaveText(
      "Launch budget passes at immediate prelaunch.",
    );
    await page.screenshot({
      path: testInfo.outputPath("storage-passing-launch-review-1440x900.png"),
      fullPage: true,
    });
  });
});

import { expect, test } from "@playwright/test";

import { collectConsoleProblems, gotoApp, gotoBuild, gotoExplore, gotoResults } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

test.describe("mocked smoke: app shell", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
  });

  test("loads without console errors and exposes Build, Results, Explore", async ({ page }) => {
    const consoleProblems = collectConsoleProblems(page);

    await gotoApp(page);

    await expect(page.getByRole("button", { name: /^Build$/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Results$/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Explore$/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Compare$/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Storage$/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Inspect$/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Visualize$/ })).toHaveCount(0);
    expect(consoleProblems).toEqual([]);
  });

  test("navigates across primary workspaces and subtabs", async ({ page }) => {
    await gotoApp(page);

    await gotoBuild(page);
    await expect(page.getByRole("heading", { name: "Create a CM1 run package" })).toBeVisible();

    await gotoResults(page);
    await expect(page.getByRole("tab", { name: "Notebook" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Compare" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Storage" })).toBeVisible();

    await gotoExplore(page);
    await expect(page.getByRole("tab", { name: "2-D Slices" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "3-D View" })).toBeVisible();
  });
});

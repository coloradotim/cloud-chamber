import { expect, test } from "@playwright/test";

import {
  collectConsoleProblems,
  gotoApp,
  gotoBuild,
  gotoExplore,
  gotoResults,
  openRunMonitor,
} from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

function rgbChannels(value: string) {
  const channels = value.match(/\d+(\.\d+)?/g)?.slice(0, 3).map(Number) ?? [];
  return {
    red: channels[0] ?? 0,
    green: channels[1] ?? 0,
    blue: channels[2] ?? 0,
  };
}

function relativeLuminance({ red, green, blue }: ReturnType<typeof rgbChannels>) {
  const values = [red, green, blue].map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
}

function contrastRatio(
  foreground: ReturnType<typeof rgbChannels>,
  background: ReturnType<typeof rgbChannels>,
) {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

test.describe("mocked smoke: app shell", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
  });

  test("loads without console errors and exposes Build, Results, Explore", async ({ page }) => {
    const consoleProblems = collectConsoleProblems(page);

    await gotoApp(page);

    const topNav = page.getByRole("navigation", { name: "Cloud Chamber workspace" });
    await expect(topNav.getByRole("button", { name: /^Build$/ })).toBeVisible();
    await expect(topNav.getByRole("button", { name: /^Results$/ })).toBeVisible();
    await expect(topNav.getByRole("button", { name: /^Explore$/ })).toBeVisible();
    await expect(topNav.getByRole("button", { name: /^Compare$/ })).toHaveCount(0);
    await expect(topNav.getByRole("button", { name: /^Storage$/ })).toHaveCount(0);
    await expect(topNav.getByRole("button", { name: /^Inspect$/ })).toHaveCount(0);
    await expect(topNav.getByRole("button", { name: /^Visualize$/ })).toHaveCount(0);
    expect(consoleProblems).toEqual([]);
  });

  test("navigates across primary workspaces", async ({ page }) => {
    await gotoApp(page);

    await gotoBuild(page);
    await openRunMonitor(page);

    await gotoResults(page);
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Notebook" })).toHaveCount(0);
    await expect(page.getByRole("tab", { name: "Compare" })).toHaveCount(0);
    await expect(page.getByRole("tab", { name: "Storage" })).toHaveCount(0);

    await gotoExplore(page);
    await expect(page.getByLabel("Explore this result")).toBeVisible();
    await expect(page.getByLabel("Explore viewer controls")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("tab", { name: "2-D Slices" })).toHaveCount(0);
    await expect(page.getByRole("tab", { name: "3-D View" })).toHaveCount(0);
  });

  test("uses atmospheric notebook chrome instead of dark terminal styling", async ({ page }) => {
    await gotoApp(page);

    const shellBackground = rgbChannels(
      await page.locator(".app-shell").evaluate((element) => getComputedStyle(element).backgroundColor),
    );
    const activeWorkspace = page.getByRole("button", { name: /^Results$/ });
    const activeBackground = rgbChannels(
      await activeWorkspace.evaluate((element) => getComputedStyle(element).backgroundColor),
    );
    const activeColor = rgbChannels(
      await activeWorkspace.evaluate((element) => getComputedStyle(element).color),
    );
    const topbarBox = await page.locator(".topbar").boundingBox();

    expect(shellBackground.red).toBeGreaterThan(220);
    expect(shellBackground.green).toBeGreaterThan(225);
    expect(shellBackground.blue).toBeGreaterThan(230);
    expect(activeBackground.blue).toBeGreaterThan(activeBackground.green - 10);
    expect(activeBackground.red).toBeGreaterThan(190);
    expect(activeColor.blue).toBeGreaterThan(activeColor.green - 30);
    expect(contrastRatio(activeColor, activeBackground)).toBeGreaterThan(3);
    expect(topbarBox?.height ?? 999).toBeLessThan(120);
    await expect(page.getByText("Results loaded")).toHaveCount(0);
    await gotoBuild(page);
    await expect(page.getByText("Scenario setup")).toHaveCount(0);
  });

  for (const viewport of [{ width: 1440, height: 900 }]) {
    test(`keeps Build Results Explore reachable at ${viewport.width}x${viewport.height}`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await gotoApp(page);

      for (const name of [/^Build$/, /^Results$/, /^Explore$/]) {
        const button = page.getByRole("button", { name });
        await expect(button).toBeVisible();
        await expect(button).toBeInViewport();
      }

      await gotoBuild(page);
      await openRunMonitor(page);
      await gotoResults(page);
      await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
      await gotoExplore(page);
      await expect(page.getByLabel("Explore this result")).toBeVisible();
      await expect(page.getByRole("heading", { name: "What am I seeing?" }))
        .toBeVisible();
    });
  }
});

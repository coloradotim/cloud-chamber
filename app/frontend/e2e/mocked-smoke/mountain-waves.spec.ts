import { expect, test } from "@playwright/test";

import { collectConsoleProblems, gotoApp } from "../helpers";
import { mockCloudChamberApis, mockMountainWavesProductPath } from "../fixtures";

test.describe("mocked smoke: Mountain Waves product path", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockCloudChamberApis(page);
  });

  test("uses both Recipes and retains Activity and History after queueing", async ({ page }) => {
    await mockMountainWavesProductPath(page);
    const consoleProblems = collectConsoleProblems(page);

    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Mountain Waves" }).click();
    await expect(page.getByRole("heading", { name: "Mountain Waves", exact: true })).toBeVisible();

    const reference = page.locator("article", { hasText: "Boulder Windstorm" });
    await reference.getByRole("button", { name: "Explore" }).click();
    await expect(page.getByRole("heading", { name: "Wave Cloud Lens" })).toBeVisible();
    await expect(page.getByLabel("Mountain Waves x-z view")).toBeVisible();
    await page.getByRole("button", { name: "Back to Mountain Waves" }).click();

    await page.getByRole("button", { name: "Create Variation", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Atmosphere and terrain" })).toBeVisible();
    await expect(page.getByText("Boulder Moist Wave")).toBeVisible();
    await expect(page.getByText("0 material changes")).toBeVisible();

    await page
      .getByLabel("Parent Simulation")
      .selectOption({ value: mountainWavesDrySimulationId });
    await expect(page.getByText("Dry Ridge Mechanics")).toBeVisible();
    await expect(page.getByRole("slider", { name: "Cross-ridge wind" })).toBeVisible();
    await expect(page.getByRole("slider", { name: "Dry stability N" })).toBeVisible();
    await expect(page.getByText("0 material changes")).toBeVisible();

    await page
      .getByLabel("Parent Simulation")
      .selectOption({ value: mountainWavesBoulderSimulationId });
    await expect(page.getByText("Boulder Moist Wave")).toBeVisible();
    await expect(page.getByRole("slider", { name: "0–4 km mean RH" })).toBeVisible();
    await page.getByLabel("Variation name").fill("Broader Ridge");
    await page.getByRole("slider", { name: "Ridge half-width" }).press("ArrowRight");
    await expect(page.getByText("1 material changes")).toBeVisible();
    await page.getByRole("button", { name: "Package variation" }).click();
    await expect(page.getByText("Packaged, not queued")).toBeVisible();
    await expect(page.getByRole("button", { name: "Queue CM1 run" })).toBeVisible();
    await page.getByRole("button", { name: "Queue CM1 run" }).click();

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

    await page.getByRole("button", { name: "Simulations" }).click();
    const availableVariation = page.locator("article", { hasText: "Broader Ridge" });
    await expect(availableVariation).toBeVisible();
    await expect(availableVariation.getByRole("button", { name: "Explore" })).toBeEnabled();
    await expect(availableVariation.getByRole("button", { name: "Compare" })).toBeEnabled();
    await expect(
      availableVariation.getByRole("button", { name: "Create variation" }),
    ).toBeEnabled();

    await availableVariation.getByRole("button", { name: "Explore" }).click();
    await expect(page.getByRole("heading", { name: "Wave Cloud Lens" })).toBeVisible();
    await expect(page.getByLabel("Mountain Waves x-z view")).toBeVisible();
    await page.getByRole("button", { name: "Back to Mountain Waves" }).click();

    await page.getByRole("button", { name: "Simulations" }).click();
    await page
      .locator("article", { hasText: "Broader Ridge" })
      .getByRole("button", { name: "Compare" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Review the two Simulations before loading frames" }),
    ).toBeVisible();
    await expect(page.getByText("Controlled pair")).toBeVisible();
    await expect(
      page.getByText(
        "The shared variation envelope records one material physical change and matched numerical and observation layers.",
      ),
    ).toBeVisible();
    await expect(page.getByRole("cell", { name: "Ridge half-width" })).toBeVisible();
    await page.getByRole("button", { name: "Back to Mountain Waves" }).click();

    await page.getByRole("button", { name: "Simulations" }).click();
    await page
      .locator("article", { hasText: "Broader Ridge" })
      .getByRole("button", { name: "Create variation" })
      .click();
    await expect(page.getByLabel("Parent Simulation")).toHaveValue(
      "mountain_waves_broader_ridge_abcd1234",
    );

    expect(consoleProblems).toEqual([]);
  });

  test("keeps a package failure inside Mountain Waves Create Variation", async ({ page }) => {
    await mockMountainWavesProductPath(page, { failPackage: true });

    await gotoApp(page);
    await page.getByRole("button", { name: "Enter Mountain Waves" }).click();
    await page.getByRole("button", { name: "Create Variation", exact: true }).click();
    await page.getByLabel("Variation name").fill("Rejected Ridge");
    await page.getByRole("slider", { name: "Ridge half-width" }).press("ArrowRight");
    await page.getByRole("button", { name: "Package variation" }).click();

    await expect(page.getByRole("alert")).toHaveText("Variation package preflight failed.");
    await expect(page.getByRole("heading", { name: "Atmosphere and terrain" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Mountain Waves", exact: true })).toBeVisible();
  });
});

const mountainWavesDrySimulationId = "mountain_waves_dry_ridge";
const mountainWavesBoulderSimulationId = "mountain_waves_boulder_moist_reference";

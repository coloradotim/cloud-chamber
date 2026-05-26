import { expect, test, type Locator, type Page } from "@playwright/test";

import { gotoApp, gotoExplore, gotoResults } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

async function expectClickableCenter(page: Page, locator: Locator, label: string) {
  await locator.scrollIntoViewIfNeeded();
  await expect(locator).toBeVisible();
  await expect(locator).toBeInViewport();
  const box = await locator.boundingBox();
  expect(box, `${label} should have a visible bounding box`).not.toBeNull();
  if (!box) return;

  const center = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  const receivesPointer = await locator.evaluate((element, point) => {
    const hit = document.elementFromPoint(point.x, point.y);
    return hit === element || element.contains(hit);
  }, center);
  expect(receivesPointer, `${label} center should not be covered by the visualizer`).toBe(true);
}

async function expectNoOverlap(first: Locator, second: Locator, label: string) {
  const firstBox = await first.boundingBox();
  const secondBox = await second.boundingBox();
  expect(firstBox, `${label} first element should have a bounding box`).not.toBeNull();
  expect(secondBox, `${label} second element should have a bounding box`).not.toBeNull();
  if (!firstBox || !secondBox) return;

  const overlaps =
    firstBox.x < secondBox.x + secondBox.width &&
    firstBox.x + firstBox.width > secondBox.x &&
    firstBox.y < secondBox.y + secondBox.height &&
    firstBox.y + firstBox.height > secondBox.y;
  expect(overlaps, `${label} should not overlap`).toBe(false);
}

async function expectInside(container: Locator, target: Locator, label: string) {
  const containerBox = await container.boundingBox();
  const targetBox = await target.boundingBox();
  expect(containerBox, `${label} container should have a bounding box`).not.toBeNull();
  expect(targetBox, `${label} target should have a bounding box`).not.toBeNull();
  if (!containerBox || !targetBox) return;

  expect(targetBox.x, `${label} should not be clipped on the left`).toBeGreaterThanOrEqual(
    containerBox.x,
  );
  expect(
    targetBox.x + targetBox.width,
    `${label} should not be clipped on the right`,
  ).toBeLessThanOrEqual(containerBox.x + containerBox.width);
}

test.describe("mocked smoke: visualizer occlusion regression", () => {
  test.beforeEach(async ({ page }) => {
    await mockCloudChamberApis(page);
    await gotoApp(page);
    await gotoResults(page);
    await page.getByRole("button", { name: "Open 3-D" }).first().click();
    await gotoExplore(page);
  });

  test("3-D scene does not cover its primary controls", async ({ page }) => {
    await expect(page.getByText(/scene shell/i).first()).toBeVisible({ timeout: 12_000 });
    await expect(page.getByText(/oblique overview/i).first()).toBeVisible();
    await expect(page.getByText(/side x-?z/i).first()).toBeVisible();

    await expectClickableCenter(
      page,
      page.getByRole("button", { name: /reset view/i }),
      "Reset view",
    );
    await expectClickableCenter(
      page,
      page.getByRole("tab", { name: "2-D Slices" }),
      "2-D Slices tab",
    );
    await expectClickableCenter(page, page.getByRole("tab", { name: "3-D View" }), "3-D View tab");
  });

  test("3-D plot labels stay visible and use a non-stretched scale frame", async ({ page }) => {
    const scene = page.getByLabel("3-D scene container");
    const description = page.getByLabel("Projection description");
    const xAxisTicks = page.getByLabel(/x-axis ticks/).locator("span");
    const contextLabel = page.locator(".scene-context-label").first();
    const viewportFrame = page.locator(".viewport-frame").first();

    await expect(scene).toBeVisible();
    await expect(description).toBeVisible();
    await expect(xAxisTicks.last()).toBeVisible();
    await expectNoOverlap(xAxisTicks.last(), description, "Bottom x-axis label and description");
    await expectInside(scene, contextLabel, "Scene context label");

    const plotFrame = await viewportFrame.evaluate((element) => {
      const styles = getComputedStyle(element);
      return {
        width: Number.parseFloat(styles.getPropertyValue("--plot-width")),
        height: Number.parseFloat(styles.getPropertyValue("--plot-height")),
      };
    });

    expect(plotFrame.height).toBeGreaterThan(0);
    expect(plotFrame.width).toBeGreaterThan(0);
    expect(
      plotFrame.height,
      "vertical plot scale should not stretch to match horizontal width",
    ).toBeLessThan(plotFrame.width * 0.7);
  });
});

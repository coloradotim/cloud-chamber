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
    await page.getByRole("button", { name: "Open in Explore" }).first().click();
    await gotoExplore(page);
  });

  test("3-D scene does not cover its primary controls", async ({ page }) => {
    await expect(page.getByText(/what happened in this result/i).first()).toBeVisible({ timeout: 12_000 });
    await expect(page.getByLabel("True 3-D cloud-water viewer")).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.getByLabel("3-D camera controls")).toBeVisible();

    await expectClickableCenter(
      page,
      page.getByRole("button", { name: /reset camera/i }),
      "Reset camera",
    );
    await expectClickableCenter(page, page.getByRole("button", { name: /zoom in/i }), "Zoom in");
    await expectClickableCenter(page, page.getByRole("button", { name: /zoom out/i }), "Zoom out");
    await expectClickableCenter(
      page,
      page.getByLabel("Slice position"),
      "Slice position slider",
    );
    await expectClickableCenter(
      page,
      page.getByRole("button", { name: /vertical x-z slice/i }),
      "Vertical x-z slice control",
    );
    await expect(page.getByRole("heading", { name: "Inspect the current slice" })).toBeVisible();
  });

  test("true 3-D scene labels stay inside the viewer frame", async ({ page }) => {
    const scene = page.getByLabel("True 3-D cloud-water viewer");
    const canvasMount = page.getByLabel(
      "Interactive Three.js scene showing CM1 cloud water, domain bounds, slice plane, and selected point",
    );
    const contextLabel = page.locator(".true3d-scene-label").first();
    const sliceLabel = page.locator(".true3d-slice-label").first();
    const cameraControls = page.getByLabel("3-D camera controls");

    await expect(scene).toBeVisible();
    await expect(canvasMount).toBeVisible();
    await expect(contextLabel).toBeVisible();
    await expect(sliceLabel).toBeVisible();
    await expect(cameraControls).toBeVisible();
    await expectInside(scene, contextLabel, "Scene context label");
    await expectInside(scene, sliceLabel, "Slice plane label");
    await expectNoOverlap(canvasMount, cameraControls, "Canvas mount and camera controls");
  });
});

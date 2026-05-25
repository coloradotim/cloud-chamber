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
});

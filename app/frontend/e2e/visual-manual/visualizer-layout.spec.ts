import { expect, test } from "@playwright/test";

import { gotoApp, gotoResults } from "../helpers";
import { mockCloudChamberApis } from "../fixtures";

test.describe("visual/manual: 3-D workbench layout", () => {
  test("loads the point-cloud scene with qualitative review targets visible", async ({ page }) => {
    test.info().annotations.push({
      type: "manual-review",
      description:
        "Qualitative review: does the 3-D cloud-water view feel physically readable, with slice planes secondary and controls/details reachable?",
    });

    await mockCloudChamberApis(page);
    await gotoApp(page);
    await gotoResults(page);
    await page.getByRole("button", { name: "Open in Explore" }).first().click();

    await expect(page.getByText(/what happened in this result/i).first()).toBeVisible({ timeout: 12_000 });
    await expect(page.getByText(/cloud-water point cloud loaded/i).first()).toBeVisible({
      timeout: 12_000,
    });
    await expect(page.getByText(/cloud-water threshold/i).first()).toBeVisible();
    await expect(page.getByText(/oblique overview/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /side x-?z/i })).toBeVisible();
    await page
      .getByText(/about this visualization/i)
      .first()
      .click();
    await expect(page.getByText(/visualizer interpretation/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /reset view/i })).toBeVisible();
  });
});

import { expect, test } from "@playwright/test";

import { gotoApp, gotoBuild, gotoResults, skipIfBackendUnavailable } from "../helpers";

test.describe("local data: read-only smoke", () => {
  test("Results and Build pipeline load against the local backend when available", async ({ page }) => {
    if (await skipIfBackendUnavailable(page)) {
      test.skip(true, "Local backend unavailable; start scripts/dev.sh for local-data tests.");
    }

    await gotoApp(page);
    await gotoResults(page);
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Storage" })).toHaveCount(0);

    await gotoBuild(page);
    await expect(page.getByRole("heading", { name: "Packages and runs needing action" })).toBeVisible();
  });
});

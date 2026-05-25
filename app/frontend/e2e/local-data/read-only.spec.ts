import { expect, test } from "@playwright/test";

import { gotoApp, gotoResults, openResultsTab, skipIfBackendUnavailable } from "../helpers";

test.describe("local data: read-only smoke", () => {
  test("Results and Storage load against the local backend when available", async ({ page }) => {
    if (await skipIfBackendUnavailable(page)) {
      test.skip(true, "Local backend unavailable; start scripts/dev.sh for local-data tests.");
    }

    await gotoApp(page);
    await gotoResults(page);
    await expect(page.getByRole("heading", { name: "Experiment Notebook" })).toBeVisible();

    await openResultsTab(page, /^Storage$/);
    await expect(page.getByRole("heading", { name: "Runtime storage cleanup" })).toBeVisible();
  });
});

import { expect, type Page } from "@playwright/test";

export const API_GLOB = "**/api/**";

export async function gotoApp(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Cloud Chamber" })).toBeVisible();
}

export async function gotoBuild(page: Page) {
  await page.getByRole("button", { name: /^Build$/ }).click();
}

export async function gotoResults(page: Page) {
  await page.getByRole("button", { name: /^Results$/ }).click();
}

export async function gotoExplore(page: Page) {
  await page.getByRole("button", { name: /^Explore$/ }).click();
}

export async function openRunMonitor(page: Page) {
  const summary = page.locator("summary", { hasText: "Run monitor" });
  await expect(summary).toBeVisible();
  await summary.evaluate((node) => {
    const details = node.closest("details") as HTMLDetailsElement | null;
    if (details) details.open = true;
  });
  await expect(page.getByRole("heading", { name: "Local CM1 queue" })).toBeVisible();
}

export function collectConsoleProblems(page: Page): string[] {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(message.text());
  });
  page.on("pageerror", (error) => problems.push(error.message));
  return problems;
}

export async function skipIfBackendUnavailable(page: Page) {
  const response = await page.request.get("http://127.0.0.1:8000/api/scenarios").catch(() => null);
  if (!response?.ok()) {
    return true;
  }
  return false;
}

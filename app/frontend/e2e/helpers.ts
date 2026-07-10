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

import { test, expect } from "@playwright/test";

test("dashboard shell loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("MRFE Control Room")).toBeVisible();
  await expect(page.getByText("Dashboard")).toBeVisible();
});

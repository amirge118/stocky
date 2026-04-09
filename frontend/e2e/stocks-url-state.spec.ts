import { test, expect } from "@playwright/test"

test("home page loads without stocks list query state", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" })
  await expect(page.getByRole("heading", { name: "Market Pulse" })).toBeVisible()
})

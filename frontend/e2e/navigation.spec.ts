// @ts-check
import { test, expect } from "@playwright/test"

test("home page redirects or loads", async ({ page }) => {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" })
  // Home renders the market snapshot; no crash.
  const status = response?.status() ?? 200
  expect(status).toBeLessThan(500)
})

test("legacy /stocks list redirects to home", async ({ page }) => {
  await page.goto("/stocks", { waitUntil: "domcontentloaded" })
  await expect(page).toHaveURL(/\/$/)
})

test("home page shows market pulse section", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" })
  await expect(page.getByRole("heading", { name: "Market Pulse" })).toBeVisible()
})

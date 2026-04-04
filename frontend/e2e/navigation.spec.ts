// @ts-check
import { test, expect } from "@playwright/test"

test("home page redirects or loads", async ({ page }) => {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" })
  // Home renders the market snapshot; no crash.
  const status = response?.status() ?? 200
  expect(status).toBeLessThan(500)
})

test("stocks page loads", async ({ page }) => {
  await page.goto("/stocks", { waitUntil: "domcontentloaded" })
  await expect(page.locator("h1")).toContainText("Stocks")
})

test("compare page loads with empty state", async ({ page }) => {
  await page.goto("/stocks/compare", { waitUntil: "domcontentloaded" })
  await expect(page.locator("h1")).toContainText("Stock Comparison")
})

test("home page shows market pulse section", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" })
  await expect(page.getByRole("heading", { name: "Market Pulse" })).toBeVisible()
})

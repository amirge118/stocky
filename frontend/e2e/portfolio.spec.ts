// @ts-check
import { test, expect } from "@playwright/test"

const MOCK_SUMMARY = {
  portfolio: {
    positions: [],
    total_value: 0,
    total_cost: 0,
    total_gain_loss: 0,
    total_gain_loss_pct: 0,
    total_day_change: null,
    total_day_change_pct: null,
  },
  sector_breakdown: { sectors: [], total_value: 0 },
}

test("portfolio page loads", async ({ page }) => {
  await page.goto("/portfolio", { waitUntil: "domcontentloaded" })
  // h1 is present in the server-rendered skeleton before any API data loads.
  await expect(page.locator("h1")).toContainText("Portfolio")
})

test("portfolio page shows key sections", async ({ page }) => {
  // Mock the portfolio summary so the test is not backend-dependent.
  await page.route("**/api/v1/portfolio/summary", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_SUMMARY),
    })
  )

  await page.goto("/portfolio", { waitUntil: "domcontentloaded" })

  await expect(page.locator("h1")).toBeVisible()
  // "Add Position" button is visible once the page has hydrated and data loaded.
  await expect(page.getByRole("button", { name: /add position/i })).toBeVisible({ timeout: 10000 })
})

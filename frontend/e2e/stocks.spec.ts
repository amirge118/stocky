import { test, expect } from "@playwright/test"

/**
 * Stock list and compare routes were removed; detail pages under /stocks/[symbol] remain.
 */
test.describe("Stock detail", () => {
  test("loads a ticker page when navigating directly", async ({ page }) => {
    await page.route("**/api/v1/stocks/AAPL*", async (route) => {
      const url = route.request().url()
      if (url.includes("/data")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            symbol: "AAPL",
            name: "Apple Inc.",
            current_price: 150.0,
            previous_close: 145.0,
            change: 5.0,
            change_percent: 3.45,
            volume: 1000000,
            market_cap: 2500000000000,
            currency: "USD",
          }),
        })
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            symbol: "AAPL",
            name: "Apple Inc.",
            exchange: "NASDAQ",
            sector: "Technology",
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
          }),
        })
      }
    })

    await page.goto("/stocks/AAPL", { waitUntil: "domcontentloaded" })
    await expect(page).toHaveURL(/\/stocks\/AAPL/)
    await expect(page.locator("text=Apple Inc.").first()).toBeVisible({ timeout: 15000 })
  })
})

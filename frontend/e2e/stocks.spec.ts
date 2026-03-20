import { test, expect } from "@playwright/test"

test.describe("Stocks Feature", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route("**/api/v1/stocks*", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                id: 1,
                symbol: "AAPL",
                name: "Apple Inc.",
                exchange: "NASDAQ",
                sector: "Technology",
                created_at: "2024-01-01T00:00:00Z",
                updated_at: "2024-01-01T00:00:00Z",
              },
              {
                id: 2,
                symbol: "GOOGL",
                name: "Alphabet Inc.",
                exchange: "NASDAQ",
                sector: "Technology",
                created_at: "2024-01-01T00:00:00Z",
                updated_at: "2024-01-01T00:00:00Z",
              },
            ],
            meta: {
              page: 1,
              limit: 20,
              total: 2,
              total_pages: 1,
            },
          }),
        })
      }
    })
  })

  test("should display stocks list", async ({ page }) => {
    await page.goto("/stocks")

    // Wait for stocks to load
    await expect(page.locator("text=AAPL")).toBeVisible()
    await expect(page.locator("text=Apple Inc.")).toBeVisible()
    await expect(page.locator("text=GOOGL")).toBeVisible()
  })

  test("should navigate to stock detail page when clicking a stock", async ({ page }) => {
    await page.goto("/stocks")

    // Mock stock detail API
    await page.route("**/api/v1/stocks/AAPL*", async (route) => {
      if (route.request().url().includes("/data")) {
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

    // Click on AAPL stock
    await page.click("text=AAPL")

    // Should navigate to detail page
    await expect(page).toHaveURL(/\/stocks\/AAPL/)
    await expect(page.locator("text=Apple Inc.")).toBeVisible()
  })

  test("should display loading state", async ({ page }) => {
    // Hold the API response so the loading spinner stays visible long enough to assert
    await page.route("**/api/v1/stocks*", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3000))
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [], meta: { page: 1, limit: 20, total: 0, total_pages: 0 } }),
      })
    })

    // Fire navigation without awaiting so we can assert the spinner while the API is delayed
    const gotoPromise = page.goto("/stocks")
    await expect(page.locator('[role="status"]')).toBeVisible({ timeout: 5000 })
    await gotoPromise
  })

  test("should display error message on API failure", async ({ page }) => {
    await page.route("**/api/v1/stocks*", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "INTERNAL_ERROR",
            message: "An error occurred",
          },
        }),
      })
    })

    await page.goto("/stocks")

    // Should show error alert (TanStack Query retries once before showing error, allow ~10s)
    await expect(page.locator('[class*="border-destructive"]').first()).toBeVisible({ timeout: 10000 })
  })
})

// @ts-check
import { test, expect } from "@playwright/test"

test("filter params persist in URL", async ({ page }) => {
  // First ensure the stocks page renders
  await page.goto("/stocks", { waitUntil: "domcontentloaded" })
  await expect(page.locator("h1")).toContainText("Stocks")

  // Navigate to the stocks page with query params
  await page.goto("/stocks?q=apple&exchange=NYSE", { waitUntil: "domcontentloaded" })

  // The URL should still contain the filter params after load
  await expect(page).toHaveURL(/q=apple/)
})

test("compare page loads with symbols from URL", async ({ page }) => {
  await page.goto("/stocks/compare?symbols=AAPL,MSFT", { waitUntil: "domcontentloaded" })

  // The h1 should be visible — confirms the page rendered without crashing
  await expect(page.locator("h1")).toContainText("Stock Comparison")

  // The compare input (not the search bar) should be pre-populated from the URL params
  const input = page.getByPlaceholder("e.g. AAPL, MSFT, GOOGL")
  await expect(input).toBeVisible()
  await expect(input).toHaveValue(/AAPL/)
})

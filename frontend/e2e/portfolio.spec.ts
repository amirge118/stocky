// @ts-check
import { test, expect } from "@playwright/test"

test("portfolio page loads", async ({ page }) => {
  await page.goto("/portfolio", { waitUntil: "domcontentloaded" })
  // The portfolio page always renders an h1 with "Portfolio" — present in both
  // the server-rendered skeleton and the hydrated client view.
  await expect(page.locator("h1")).toContainText("Portfolio")
})

test("portfolio page shows key sections", async ({ page }) => {
  await page.goto("/portfolio", { waitUntil: "domcontentloaded" })

  // The page must not show a 500 error — a basic liveness check.
  // We verify the main heading exists (rendered even before API data loads).
  await expect(page.locator("h1")).toBeVisible()

  // The "Add Position" button is always present in both skeleton and live views.
  await expect(page.getByRole("button", { name: /add position/i })).toBeVisible()
})

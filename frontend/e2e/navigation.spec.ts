// @ts-check
import { test, expect } from "@playwright/test"

test("home page redirects or loads", async ({ page }) => {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" })
  // The home page redirects to /portfolio — either the redirect succeeds (200 on final URL)
  // or the initial response is a redirect (3xx). Either way, no crash.
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

test("market pulse page loads", async ({ page }) => {
  await page.goto("/market", { waitUntil: "domcontentloaded" })
  // The market page renders "Market Pulse" as the h1 — check it appears
  // (the API call may fail in test env, but the heading is always rendered)
  await expect(page.locator("h1")).toContainText("Market Pulse")
})

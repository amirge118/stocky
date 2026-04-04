import { test } from "@playwright/test"
import fs from "fs"
import path from "path"

const PAGES = [
  { name: "Home/Portfolio redirect", path: "/" },
  { name: "Stocks", path: "/stocks" },
  { name: "Stock Compare", path: "/stocks/compare" },
  { name: "Portfolio", path: "/portfolio" },
  { name: "Watchlist", path: "/watchlist" },
  { name: "Settings", path: "/settings" },
]

const report: { timestamp: string; errors: object[]; summary: object } = {
  timestamp: new Date().toISOString(),
  errors: [],
  summary: {},
}

for (const { name, path: pagePath } of PAGES) {
  test(`scan: ${name}`, async ({ page }) => {
    const pageErrors: object[] = []

    // Intercept API responses
    page.on("response", (response) => {
      const url = response.url()
      if (url.includes("/api/v1/") && response.status() >= 400) {
        pageErrors.push({
          page: pagePath,
          url,
          status: response.status(),
          method: response.request().method(),
          timestamp: new Date().toISOString(),
        })
      }
    })

    // Intercept failed requests (network errors)
    page.on("requestfailed", (request) => {
      if (request.url().includes("/api/v1/") || request.url().includes(":8000")) {
        pageErrors.push({
          page: pagePath,
          url: request.url(),
          status: "NETWORK_FAIL",
          error: request.failure()?.errorText,
          timestamp: new Date().toISOString(),
        })
      }
    })

    // Capture console errors
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        pageErrors.push({
          page: pagePath,
          type: "console.error",
          text: msg.text(),
          timestamp: new Date().toISOString(),
        })
      }
    })

    await page.goto(pagePath, { waitUntil: "load", timeout: 30000 })
    // Give initial API requests time to fire and respond
    await page.waitForTimeout(3000)
    report.errors.push(...pageErrors)
  })
}

test.afterAll(() => {
  const byPage = report.errors.reduce((acc: Record<string, number>, e: any) => {
    acc[e.page] = (acc[e.page] || 0) + 1
    return acc
  }, {})
  report.summary = { total: report.errors.length, byPage }

  const outPath = path.join(__dirname, "../error-scan-report.json")
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2))
  console.log(`\n=== Error Scan Report ===`)
  console.log(`Total errors: ${report.errors.length}`)
  if (report.errors.length > 0) {
    console.log("Errors by page:", byPage)
    console.log(`Report saved to: ${outPath}`)
  } else {
    console.log("No API errors detected!")
  }
})

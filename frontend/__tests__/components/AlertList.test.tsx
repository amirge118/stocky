import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AlertList } from "@/components/features/alerts/AlertList"
import type { Alert } from "@/types/alerts"

jest.mock("@/lib/api/alerts")

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const mockAlerts: Alert[] = [
  {
    id: 1,
    ticker: "AAPL",
    condition_type: "ABOVE",
    target_price: "200.0000",
    is_active: true,
    last_triggered: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
  },
  {
    id: 2,
    ticker: "MSFT",
    condition_type: "BELOW",
    target_price: "100.0000",
    is_active: false,
    last_triggered: "2026-01-02T12:00:00Z",
    updated_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
]

describe("AlertList", () => {
  it("renders skeleton rows when loading", () => {
    const { container } = render(<AlertList alerts={[]} isLoading={true} />, { wrapper })
    expect(container.querySelectorAll(".animate-pulse").length).toBe(4)
  })

  it("renders empty state when no alerts and not loading", () => {
    render(<AlertList alerts={[]} isLoading={false} />, { wrapper })
    expect(screen.getByText(/No alerts yet/i)).toBeInTheDocument()
  })

  it("renders all alerts when provided", () => {
    render(<AlertList alerts={mockAlerts} isLoading={false} />, { wrapper })
    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("MSFT")).toBeInTheDocument()
  })

  it("renders one row per alert", () => {
    render(<AlertList alerts={mockAlerts} isLoading={false} />, { wrapper })
    // Each AlertRow shows a ticker badge
    expect(screen.getAllByText(/AAPL|MSFT/).length).toBeGreaterThanOrEqual(2)
  })

  it("does not show skeleton when not loading", () => {
    const { container } = render(<AlertList alerts={[]} isLoading={false} />, { wrapper })
    expect(container.querySelectorAll(".animate-pulse").length).toBe(0)
  })
})

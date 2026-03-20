import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AlertRow } from "@/components/features/alerts/AlertRow"
import * as alertsApi from "@/lib/api/alerts"
import type { Alert } from "@/types/alerts"

jest.mock("@/lib/api/alerts")

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const baseAlert: Alert = {
  id: 1,
  ticker: "AAPL",
  condition_type: "ABOVE",
  target_price: "200.0000",
  is_active: true,
  last_triggered: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
}

describe("AlertRow", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders ticker symbol", () => {
    render(<AlertRow alert={baseAlert} />, { wrapper })
    expect(screen.getByText("AAPL")).toBeInTheDocument()
  })

  it("renders ABOVE condition chip", () => {
    render(<AlertRow alert={baseAlert} />, { wrapper })
    expect(screen.getByText("Above")).toBeInTheDocument()
  })

  it("renders BELOW condition chip", () => {
    render(<AlertRow alert={{ ...baseAlert, condition_type: "BELOW" }} />, { wrapper })
    expect(screen.getByText("Below")).toBeInTheDocument()
  })

  it("renders EQUAL condition chip", () => {
    render(<AlertRow alert={{ ...baseAlert, condition_type: "EQUAL" }} />, { wrapper })
    expect(screen.getByText("Equal")).toBeInTheDocument()
  })

  it("renders target price formatted", () => {
    render(<AlertRow alert={baseAlert} />, { wrapper })
    expect(screen.getByText("$200.00")).toBeInTheDocument()
  })

  it("renders 'Never triggered' when last_triggered is null", () => {
    render(<AlertRow alert={baseAlert} />, { wrapper })
    expect(screen.getByText("Never triggered")).toBeInTheDocument()
  })

  it("renders relative time when last_triggered is set", () => {
    const triggered = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2h ago
    render(<AlertRow alert={{ ...baseAlert, last_triggered: triggered }} />, { wrapper })
    expect(screen.getByText(/Triggered/)).toBeInTheDocument()
  })

  it("calls updateAlert when toggle is clicked", async () => {
    ;(alertsApi.updateAlert as jest.Mock).mockResolvedValue({ ...baseAlert, is_active: false })
    render(<AlertRow alert={baseAlert} />, { wrapper })

    const toggle = screen.getByTitle("Deactivate")
    fireEvent.click(toggle)

    await waitFor(() => {
      expect(alertsApi.updateAlert).toHaveBeenCalledWith(1, { is_active: false })
    })
  })

  it("toggle title says Activate when alert is inactive", () => {
    render(<AlertRow alert={{ ...baseAlert, is_active: false }} />, { wrapper })
    expect(screen.getByTitle("Activate")).toBeInTheDocument()
  })

  it("calls deleteAlert when delete button is clicked", async () => {
    ;(alertsApi.deleteAlert as jest.Mock).mockResolvedValue(undefined)
    render(<AlertRow alert={baseAlert} />, { wrapper })

    const deleteBtn = screen.getByTitle("Delete alert")
    fireEvent.click(deleteBtn)

    await waitFor(() => {
      expect(alertsApi.deleteAlert).toHaveBeenCalledWith(1)
    })
  })
})

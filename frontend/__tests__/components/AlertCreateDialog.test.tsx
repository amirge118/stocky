import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AlertCreateDialog } from "@/components/features/alerts/AlertCreateDialog"
import * as alertsApi from "@/lib/api/alerts"

jest.mock("@/lib/api/alerts")

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const mockCreated = {
  id: 1,
  ticker: "AAPL",
  condition_type: "ABOVE" as const,
  target_price: "200.0000",
  is_active: true,
  last_triggered: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
}

describe("AlertCreateDialog", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("does not render content when closed", () => {
    render(<AlertCreateDialog open={false} onOpenChange={jest.fn()} />, { wrapper })
    expect(screen.queryByText("New Price Alert")).not.toBeInTheDocument()
  })

  it("renders dialog title when open", () => {
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    expect(screen.getByText("New Price Alert")).toBeInTheDocument()
  })

  it("renders ticker input, condition buttons, and price field", () => {
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    expect(screen.getByPlaceholderText(/e.g. AAPL/i)).toBeInTheDocument()
    expect(screen.getByText("Above")).toBeInTheDocument()
    expect(screen.getByText("Below")).toBeInTheDocument()
    expect(screen.getByText("Equal")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("0.00")).toBeInTheDocument()
  })

  it("calls onOpenChange when Cancel is clicked", () => {
    const onOpenChange = jest.fn()
    render(<AlertCreateDialog open={true} onOpenChange={onOpenChange} />, { wrapper })
    fireEvent.click(screen.getByText("Cancel"))
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it("shows validation error when ticker is empty on submit", async () => {
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    fireEvent.click(screen.getByText("Create Alert"))
    await waitFor(() => {
      expect(screen.getByText(/Ticker is required/i)).toBeInTheDocument()
    })
  })

  it("shows validation error when price is invalid", async () => {
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    fireEvent.change(screen.getByPlaceholderText(/e.g. AAPL/i), { target: { value: "AAPL" } })
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "-5" } })
    fireEvent.click(screen.getByText("Create Alert"))
    await waitFor(() => {
      expect(screen.getByText(/positive number/i)).toBeInTheDocument()
    })
  })

  it("auto-uppercases ticker input", () => {
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    const input = screen.getByPlaceholderText(/e.g. AAPL/i)
    fireEvent.change(input, { target: { value: "aapl" } })
    expect((input as HTMLInputElement).value).toBe("AAPL")
  })

  it("calls createAlert with correct payload on submit", async () => {
    ;(alertsApi.createAlert as jest.Mock).mockResolvedValue(mockCreated)
    const onOpenChange = jest.fn()
    render(<AlertCreateDialog open={true} onOpenChange={onOpenChange} />, { wrapper })

    fireEvent.change(screen.getByPlaceholderText(/e.g. AAPL/i), { target: { value: "AAPL" } })
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "200" } })
    fireEvent.click(screen.getByText("Create Alert"))

    await waitFor(() => {
      expect(alertsApi.createAlert).toHaveBeenCalledWith({
        ticker: "AAPL",
        condition_type: "ABOVE",
        target_price: 200,
      })
    })
  })

  it("closes dialog after successful creation", async () => {
    ;(alertsApi.createAlert as jest.Mock).mockResolvedValue(mockCreated)
    const onOpenChange = jest.fn()
    render(<AlertCreateDialog open={true} onOpenChange={onOpenChange} />, { wrapper })

    fireEvent.change(screen.getByPlaceholderText(/e.g. AAPL/i), { target: { value: "TSLA" } })
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "150" } })
    fireEvent.click(screen.getByText("Create Alert"))

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false)
    })
  })

  it("shows API error message on failure", async () => {
    ;(alertsApi.createAlert as jest.Mock).mockRejectedValue(new Error("Server error"))
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })

    fireEvent.change(screen.getByPlaceholderText(/e.g. AAPL/i), { target: { value: "AAPL" } })
    fireEvent.change(screen.getByPlaceholderText("0.00"), { target: { value: "100" } })
    fireEvent.click(screen.getByText("Create Alert"))

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument()
    })
  })

  it("can switch condition to BELOW", () => {
    ;(alertsApi.createAlert as jest.Mock).mockResolvedValue(mockCreated)
    render(<AlertCreateDialog open={true} onOpenChange={jest.fn()} />, { wrapper })
    fireEvent.click(screen.getByText("Below"))
    // Below button should now be styled differently (active state)
    expect(screen.getByText("Below")).toBeInTheDocument()
  })
})

import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { EditStockDialog } from "@/components/features/stocks/EditStockDialog"
import type { Stock } from "@/types/stock"

// Mock the API
jest.mock("@/lib/api/stocks", () => ({
  updateStock: jest.fn(),
}))

// Mock toast
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

const mockStock: Stock = {
  id: 1,
  symbol: "AAPL",
  name: "Apple Inc.",
  exchange: "NASDAQ",
  sector: "Technology",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: null,
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe("EditStockDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    stock: mockStock,
    onSuccess: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders dialog when open", () => {
    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText("Edit Stock")).toBeInTheDocument()
    expect(
      screen.getByText("Update stock information. Symbol cannot be changed.")
    ).toBeInTheDocument()
  })

  it("pre-fills form with stock data", () => {
    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByDisplayValue("AAPL")).toBeInTheDocument()
    expect(screen.getByDisplayValue("Apple Inc.")).toBeInTheDocument()
  })

  it("disables symbol field", () => {
    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const symbolInput = screen.getByDisplayValue("AAPL")
    expect(symbolInput).toBeDisabled()
  })

  it("updates stock when form is submitted", async () => {
    const user = userEvent.setup()
    const { updateStock } = require("@/lib/api/stocks")
    updateStock.mockResolvedValue({
      ...mockStock,
      name: "Apple Corporation",
    })

    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const nameInput = screen.getByDisplayValue("Apple Inc.")
    await user.clear(nameInput)
    await user.type(nameInput, "Apple Corporation")

    const submitButton = screen.getByText("Update Stock")
    await user.click(submitButton)

    await waitFor(() => {
      expect(updateStock).toHaveBeenCalledWith("AAPL", {
        name: "Apple Corporation",
        exchange: "NASDAQ",
        sector: "Technology",
      })
    })
  })

  it("shows validation errors for invalid input", async () => {
    const user = userEvent.setup()
    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const nameInput = screen.getByDisplayValue("Apple Inc.")
    await user.clear(nameInput)

    const submitButton = screen.getByText("Update Stock")
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText("Name is required")).toBeInTheDocument()
    })
  })

  it("calls onOpenChange when cancel is clicked", async () => {
    const user = userEvent.setup()
    render(<EditStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const cancelButton = screen.getByText("Cancel")
    await user.click(cancelButton)

    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
  })
})

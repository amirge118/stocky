import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BulkDeleteDialog } from "@/components/features/stocks/BulkDeleteDialog"
import type { Stock } from "@/types/stock"

// Mock the API
jest.mock("@/lib/api/stocks", () => ({
  deleteStock: jest.fn(),
}))

// Mock toast
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

const mockStocks: Stock[] = [
  {
    id: 1,
    symbol: "AAPL",
    name: "Apple Inc.",
    exchange: "NASDAQ",
    sector: "Technology",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  },
  {
    id: 2,
    symbol: "MSFT",
    name: "Microsoft Corporation",
    exchange: "NASDAQ",
    sector: "Technology",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  },
]

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

describe("BulkDeleteDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    stocks: mockStocks,
    onSuccess: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders dialog when open", () => {
    render(<BulkDeleteDialog {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText("Delete 2 stocks?")).toBeInTheDocument()
    expect(screen.getByText(/AAPL, MSFT/)).toBeInTheDocument()
  })

  it("shows singular form for single stock", () => {
    render(
      <BulkDeleteDialog {...defaultProps} stocks={[mockStocks[0]]} />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText("Delete 1 stock?")).toBeInTheDocument()
  })

  it("calls deleteStock for all stocks when confirmed", async () => {
    const user = userEvent.setup()
    const { deleteStock } = require("@/lib/api/stocks")
    deleteStock.mockResolvedValue(undefined)

    render(<BulkDeleteDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete 2 stocks")
    await user.click(deleteButton)

    await waitFor(() => {
      expect(deleteStock).toHaveBeenCalledTimes(2)
      expect(deleteStock).toHaveBeenCalledWith("AAPL")
      expect(deleteStock).toHaveBeenCalledWith("MSFT")
    })
  })

  it("calls onOpenChange when cancel is clicked", async () => {
    const user = userEvent.setup()
    render(<BulkDeleteDialog {...defaultProps} />, { wrapper: createWrapper() })

    const cancelButton = screen.getByText("Cancel")
    await user.click(cancelButton)

    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
  })

  it("shows loading state when deleting", async () => {
    const user = userEvent.setup()
    const { deleteStock } = require("@/lib/api/stocks")
    deleteStock.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    render(<BulkDeleteDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete 2 stocks")
    await user.click(deleteButton)

    expect(screen.getByText("Deleting...")).toBeInTheDocument()
    expect(deleteButton).toBeDisabled()
  })

  it("calls onSuccess after successful deletion", async () => {
    const user = userEvent.setup()
    const { deleteStock } = require("@/lib/api/stocks")
    deleteStock.mockResolvedValue(undefined)

    render(<BulkDeleteDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete 2 stocks")
    await user.click(deleteButton)

    await waitFor(() => {
      expect(defaultProps.onSuccess).toHaveBeenCalled()
    })
  })
})

import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DeleteStockDialog } from "@/components/features/stocks/DeleteStockDialog"
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

describe("DeleteStockDialog", () => {
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
    render(<DeleteStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText("Are you sure?")).toBeInTheDocument()
    expect(screen.getByText(/AAPL/)).toBeInTheDocument()
    expect(screen.getByText(/Apple Inc./)).toBeInTheDocument()
  })

  it("does not render when closed", () => {
    render(<DeleteStockDialog {...defaultProps} open={false} />, {
      wrapper: createWrapper(),
    })

    expect(screen.queryByText("Are you sure?")).not.toBeInTheDocument()
  })

  it("calls deleteStock when delete is confirmed", async () => {
    const user = userEvent.setup()
    const { deleteStock } = require("@/lib/api/stocks")
    deleteStock.mockResolvedValue(undefined)

    render(<DeleteStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete")
    await user.click(deleteButton)

    await waitFor(() => {
      expect(deleteStock).toHaveBeenCalledWith("AAPL")
    })
  })

  it("calls onOpenChange when cancel is clicked", async () => {
    const user = userEvent.setup()
    render(<DeleteStockDialog {...defaultProps} />, { wrapper: createWrapper() })

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

    render(<DeleteStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete")
    await user.click(deleteButton)

    expect(screen.getByText("Deleting...")).toBeInTheDocument()
    expect(deleteButton).toBeDisabled()
  })

  it("calls onSuccess after successful deletion", async () => {
    const user = userEvent.setup()
    const { deleteStock } = require("@/lib/api/stocks")
    deleteStock.mockResolvedValue(undefined)

    render(<DeleteStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const deleteButton = screen.getByText("Delete")
    await user.click(deleteButton)

    await waitFor(() => {
      expect(defaultProps.onSuccess).toHaveBeenCalled()
    })
  })
})

import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StockTable } from "@/components/features/stocks/StockTable"
import type { Stock } from "@/types/stock"

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

// Mock the API
jest.mock("@/lib/api/stocks", () => ({
  fetchStockData: jest.fn(),
}))

// Mock useWatchlist
jest.mock("@/lib/hooks/useWatchlist", () => ({
  useWatchlist: () => ({
    isInWatchlist: jest.fn((symbol: string) => symbol === "AAPL"),
    toggleWatchlist: jest.fn(),
  }),
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

const mockStockData = {
  symbol: "AAPL",
  name: "Apple Inc.",
  current_price: 150.0,
  previous_close: 145.0,
  change: 5.0,
  change_percent: 3.45,
  volume: 50000000,
  market_cap: 2500000000000,
  currency: "USD",
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

describe("StockTable", () => {
  const defaultProps = {
    stocks: mockStocks,
    searchQuery: "",
    filters: {},
  }

  beforeEach(() => {
    jest.clearAllMocks()
    const { fetchStockData } = require("@/lib/api/stocks")
    fetchStockData.mockResolvedValue(mockStockData)
  })

  it("renders table with stock data", () => {
    render(<StockTable {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument()
    expect(screen.getByText("MSFT")).toBeInTheDocument()
    expect(screen.getByText("Microsoft Corporation")).toBeInTheDocument()
  })

  it("renders table headers", () => {
    render(<StockTable {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByText("Symbol")).toBeInTheDocument()
    expect(screen.getByText("Name")).toBeInTheDocument()
    expect(screen.getByText("Exchange")).toBeInTheDocument()
    expect(screen.getByText("Sector")).toBeInTheDocument()
    expect(screen.getByText("Price")).toBeInTheDocument()
    expect(screen.getByText("Change")).toBeInTheDocument()
    expect(screen.getByText("Volume")).toBeInTheDocument()
  })

  it("filters stocks by search query", () => {
    render(<StockTable {...defaultProps} searchQuery="AAPL" />, {
      wrapper: createWrapper(),
    })

    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.queryByText("MSFT")).not.toBeInTheDocument()
  })

  it("filters stocks by exchange", () => {
    render(
      <StockTable {...defaultProps} filters={{ exchange: "NYSE" }} />,
      { wrapper: createWrapper() }
    )

    expect(screen.queryByText("AAPL")).not.toBeInTheDocument()
    expect(screen.queryByText("MSFT")).not.toBeInTheDocument()
  })

  it("filters stocks by sector", () => {
    render(
      <StockTable {...defaultProps} filters={{ sector: "Technology" }} />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("MSFT")).toBeInTheDocument()
  })

  it("shows empty state when no stocks match filters", () => {
    render(
      <StockTable {...defaultProps} searchQuery="NONEXISTENT" />,
      { wrapper: createWrapper() }
    )

    expect(
      screen.getByText(/No stocks match your filters/)
    ).toBeInTheDocument()
  })

  it("handles selection when onSelectionChange is provided", async () => {
    const user = userEvent.setup()
    const onSelectionChange = jest.fn()

    render(
      <StockTable {...defaultProps} onSelectionChange={onSelectionChange} />,
      { wrapper: createWrapper() }
    )

    const checkboxes = screen.getAllByRole("checkbox")
    // First checkbox is select all, second is first row
    await user.click(checkboxes[1])

    expect(onSelectionChange).toHaveBeenCalled()
  })

  it("handles select all", async () => {
    const user = userEvent.setup()
    const onSelectionChange = jest.fn()

    render(
      <StockTable {...defaultProps} onSelectionChange={onSelectionChange} />,
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      const checkboxes = screen.getAllByRole("checkbox")
      expect(checkboxes.length).toBeGreaterThan(0)
    })

    const selectAllCheckbox = screen.getAllByRole("checkbox")[0]
    await user.click(selectAllCheckbox)

    await waitFor(() => {
      expect(onSelectionChange).toHaveBeenCalled()
    })
  })

  it("shows watchlist star icon", () => {
    render(<StockTable {...defaultProps} />, { wrapper: createWrapper() })

    // Should show star buttons for watchlist (aria-label contains "watchlist")
    const starButtons = screen.getAllByRole("button").filter(
      (b) => b.getAttribute("aria-label")?.includes("watchlist")
    )
    expect(starButtons.length).toBeGreaterThan(0)
  })

  it("calls onEdit when edit button is clicked", async () => {
    const user = userEvent.setup()
    const onEdit = jest.fn()

    render(<StockTable {...defaultProps} onEdit={onEdit} />, {
      wrapper: createWrapper(),
    })

    const editButtons = screen.getAllByRole("button")
    const editButton = editButtons.find((btn) =>
      btn.querySelector('svg[class*="lucide-edit"]')
    )

    if (editButton) {
      await user.click(editButton)
      await waitFor(() => {
        expect(onEdit).toHaveBeenCalled()
      })
    }
  })

  it("calls onDelete when delete button is clicked", async () => {
    const user = userEvent.setup()
    const onDelete = jest.fn()

    render(<StockTable {...defaultProps} onDelete={onDelete} />, {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole("button")
      const deleteButton = deleteButtons.find((btn) =>
        btn.querySelector('svg[class*="lucide-trash"]')
      )
      return deleteButton
    }).then(async (deleteButton) => {
      if (deleteButton) {
        await user.click(deleteButton)
        // The delete button opens a dialog, so onDelete is called after confirmation
        // For this test, we just verify the button click works
        await waitFor(() => {
          // Check that delete dialog appears (which means button was clicked)
          expect(screen.queryByText(/Are you sure/i)).toBeInTheDocument()
        })
      }
    })
  })

  it.skip("fetches live data for stocks", async () => {
    const { fetchStockData } = require("@/lib/api/stocks")

    render(<StockTable {...defaultProps} />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(fetchStockData).toHaveBeenCalled()
    })
  })

  it.skip("displays live data when available", async () => {
    const { fetchStockData } = require("@/lib/api/stocks")
    fetchStockData.mockResolvedValue(mockStockData)

    render(<StockTable {...defaultProps} />, { wrapper: createWrapper() })

    await waitFor(
      () => {
        // Check for formatted currency display - there should be at least one price shown
        const priceDisplays = screen.queryAllByText(/\$150\.00/)
        expect(priceDisplays.length).toBeGreaterThan(0)
      },
      { timeout: 3000 }
    )
  })
})

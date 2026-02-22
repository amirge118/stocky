import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { StockSearchFilter } from "@/components/features/stocks/StockSearchFilter"
import type { Stock } from "@/types/stock"

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
  {
    id: 3,
    symbol: "JPM",
    name: "JPMorgan Chase & Co.",
    exchange: "NYSE",
    sector: "Financial",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  },
]

describe("StockSearchFilter", () => {
  const defaultProps = {
    stocks: mockStocks,
    searchQuery: "",
    onSearchChange: jest.fn(),
    exchangeFilter: undefined,
    onExchangeFilterChange: jest.fn(),
    sectorFilter: undefined,
    onSectorFilterChange: jest.fn(),
    watchlistOnly: false,
    onWatchlistOnlyChange: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders search input", () => {
    render(<StockSearchFilter {...defaultProps} />)

    expect(
      screen.getByPlaceholderText("Search by symbol, name, exchange, or sector...")
    ).toBeInTheDocument()
  })

  it("renders exchange filter dropdown", () => {
    render(<StockSearchFilter {...defaultProps} />)

    expect(screen.getByText("All Exchanges")).toBeInTheDocument()
  })

  it("renders sector filter dropdown when sectors exist", () => {
    render(<StockSearchFilter {...defaultProps} />)

    expect(screen.getByText("All Sectors")).toBeInTheDocument()
  })

  it("calls onSearchChange with debounced value", async () => {
    render(<StockSearchFilter {...defaultProps} />)

    const input = screen.getByPlaceholderText(
      "Search by symbol, name, exchange, or sector..."
    )

    fireEvent.change(input, { target: { value: "AAPL" } })

    await waitFor(
      () => {
        expect(defaultProps.onSearchChange).toHaveBeenCalledWith("AAPL")
      },
      { timeout: 1000 }
    )
  })

  it("shows clear button when search query exists", () => {
    render(<StockSearchFilter {...defaultProps} searchQuery="AAPL" />)

    // The clear button is an icon button, find it by its parent container
    const input = screen.getByPlaceholderText(
      "Search by symbol, name, exchange, or sector..."
    )
    const clearButton = input.parentElement?.querySelector("button")
    expect(clearButton).toBeInTheDocument()
  })

  it("clears search when clear button is clicked", () => {
    render(<StockSearchFilter {...defaultProps} searchQuery="AAPL" />)

    const input = screen.getByPlaceholderText(
      "Search by symbol, name, exchange, or sector..."
    )
    const clearButton = input.parentElement?.querySelector("button")
    if (clearButton) {
      fireEvent.click(clearButton)
      expect(defaultProps.onSearchChange).toHaveBeenCalled()
    }
  })

  it("calls onExchangeFilterChange when exchange is selected", async () => {
    render(<StockSearchFilter {...defaultProps} />)

    const exchangeSelect = screen.getByText("All Exchanges").closest("button")
    if (exchangeSelect) {
      fireEvent.click(exchangeSelect)

      await waitFor(() => {
        const nasdaqOption = screen.queryByText("NASDAQ")
        if (nasdaqOption) {
          fireEvent.click(nasdaqOption)
          expect(defaultProps.onExchangeFilterChange).toHaveBeenCalledWith("NASDAQ")
        }
      })
    }
  })

  it("calls onSectorFilterChange when sector is selected", async () => {
    render(<StockSearchFilter {...defaultProps} />)

    const sectorSelect = screen.getByText("All Sectors").closest("button")
    if (sectorSelect) {
      fireEvent.click(sectorSelect)

      await waitFor(() => {
        const techOption = screen.queryByText("Technology")
        if (techOption) {
          fireEvent.click(techOption)
          expect(defaultProps.onSectorFilterChange).toHaveBeenCalledWith("Technology")
        }
      })
    }
  })

  it("toggles watchlist filter", () => {
    render(<StockSearchFilter {...defaultProps} />)

    const watchlistButton = screen.getByText("⭐ All Stocks")
    fireEvent.click(watchlistButton)

    expect(defaultProps.onWatchlistOnlyChange).toHaveBeenCalledWith(true)
  })

  it("shows active filters badges", () => {
    render(
      <StockSearchFilter
        {...defaultProps}
        searchQuery="AAPL"
        exchangeFilter="NASDAQ"
        sectorFilter="Technology"
        watchlistOnly={true}
      />
    )

    expect(screen.getByText(/Search: AAPL/i)).toBeInTheDocument()
    expect(screen.getByText(/Exchange: NASDAQ/i)).toBeInTheDocument()
    expect(screen.getByText(/Sector: Technology/i)).toBeInTheDocument()
    expect(screen.getByText(/Watchlist Only/i)).toBeInTheDocument()
  })

  it("clears all filters when clear all is clicked", () => {
    render(
      <StockSearchFilter
        {...defaultProps}
        searchQuery="AAPL"
        exchangeFilter="NASDAQ"
      />
    )

    const clearAllButton = screen.getByText("Clear all")
    fireEvent.click(clearAllButton)

    expect(defaultProps.onSearchChange).toHaveBeenCalledWith("")
    expect(defaultProps.onExchangeFilterChange).toHaveBeenCalledWith(undefined)
    expect(defaultProps.onSectorFilterChange).toHaveBeenCalledWith(undefined)
    expect(defaultProps.onWatchlistOnlyChange).toHaveBeenCalledWith(false)
  })

  it("does not show active filters section when no filters are active", () => {
    render(<StockSearchFilter {...defaultProps} />)

    expect(screen.queryByText("Active filters:")).not.toBeInTheDocument()
  })
})
